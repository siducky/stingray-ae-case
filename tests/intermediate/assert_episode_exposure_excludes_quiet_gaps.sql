-- An episode is an analytical grouping: its wall-clock span may contain quiet
-- gaps between member storms, and those gaps are never storm exposure.
-- Exposure minutes come only from int_storm_daily_exposure (per member storm),
-- never from the episode span. Checks:
--   1. Per storm, the daily exposure minutes sum back to the storm duration
--      (day-splitting conserves exposure; gaps are never added).
--   2. Per episode, total exposure must not exceed the wall-clock span
--      (only possible if overlapping events double-count, which the warn
--      test assert_no_overlapping_storms_per_site also flags).
-- Warn severity: with genuinely overlapping member storms, cumulative
-- event-minutes can legitimately exceed the span - that is a data shape worth
-- reviewing, not a pipeline defect.
-- Returns offending episodes/storms (test warns if any rows are returned).

{{ config(severity = 'warn') }}

with

episodes as (
    select * from {{ ref('int_storm_episodes') }}
),

storms as (
    select * from {{ ref('stg_stingray__storm_events') }}
),

exposure as (
    select * from {{ ref('int_storm_daily_exposure') }}
),

storm_totals as (
    select
        exposure.storm_id,
        sum(exposure.storm_minutes) as total_exposure_minutes
    from exposure
    group by exposure.storm_id
),

episode_members as (
    select
        episodes.storm_episode_id,
        episodes.site_id,
        episodes.episode_started_at,
        episodes.episode_ended_at,
        episodes.storm_event_count,
        unnest(string_split(episodes.storm_ids, ',')) as storm_id
    from episodes
),

episode_totals as (
    select
        episode_members.storm_episode_id,
        episode_members.episode_started_at,
        episode_members.episode_ended_at,
        episode_members.storm_event_count,
        sum(storm_totals.total_exposure_minutes) as episode_exposure_minutes,
        date_diff(
            'minute',
            episode_members.episode_started_at,
            episode_members.episode_ended_at
        ) as episode_span_minutes
    from episode_members
    inner join storm_totals
        on storm_totals.storm_id = episode_members.storm_id
    group by
        episode_members.storm_episode_id,
        episode_members.episode_started_at,
        episode_members.episode_ended_at,
        episode_members.storm_event_count
),

violations as (
    -- Storm-level conservation: day-splitting must not invent or lose minutes.
    select
        'storm_duration_mismatch' as violation,
        storms.storm_id as entity_id,
        storm_totals.total_exposure_minutes
            <> date_diff('minute', storms.storm_started_at, storms.storm_ended_at)
            as is_violation
    from storms
    inner join storm_totals
        on storm_totals.storm_id = storms.storm_id
    union all
    -- Episode-level: quiet gaps are never exposure; exposure must fit in the
    -- span. For single-event episodes it must equal the span exactly.
    select
        'episode_exposure_exceeds_span' as violation,
        episode_totals.storm_episode_id as entity_id,
        (
            episode_totals.episode_exposure_minutes > episode_totals.episode_span_minutes
            or (
                episode_totals.storm_event_count = 1
                and episode_totals.episode_exposure_minutes <> episode_totals.episode_span_minutes
            )
        ) as is_violation
    from episode_totals
)

select * from violations where violations.is_violation

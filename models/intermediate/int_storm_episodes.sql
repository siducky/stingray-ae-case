-- Grain: one row per storm episode per site.
-- Events merge when the next starts strictly less than
-- var('storm_episode_gap_hours') (default 24) after the running-max end
-- of preceding events at that site; a gap of exactly 24h starts a new
-- episode; different sites never merge. The running max (not LAG) makes
-- overlapping/nested intervals safe.
-- The span is wall-clock and INCLUDES quiet gaps between member storms:
-- never exposure (exposure lives in int_storm_daily_exposure).
-- Bounds are half-open; episode_end_date is the last exposed local date
-- (end - 1 microsecond), so an end exactly at local midnight claims no
-- extra day.

with

storms as (
    select * from {{ ref('stg_stingray__storm_events') }}
),

-- Running maximum of end timestamps over all preceding events at the
-- site (rows between unbounded preceding and 1 preceding), not LAG: the
-- episode end can come from any earlier, longer event.
with_running_end as (
    select
        storms.storm_id,
        storms.site_id,
        storms.storm_started_at,
        storms.storm_ended_at,
        storms.severity,
        max(storms.storm_ended_at) over (
            partition by storms.site_id
            order by storms.storm_started_at, storms.storm_id
            rows between unbounded preceding and 1 preceding
        ) as prev_episode_end_at
    from storms
),

flagged as (
    select
        with_running_end.storm_id,
        with_running_end.site_id,
        with_running_end.storm_started_at,
        with_running_end.storm_ended_at,
        with_running_end.severity,
        with_running_end.prev_episode_end_at,
        (
            with_running_end.prev_episode_end_at is null
            or with_running_end.storm_started_at
                >= with_running_end.prev_episode_end_at + to_hours({{ var('storm_episode_gap_hours', 24) }})
        ) as is_episode_start
    from with_running_end
),

numbered as (
    select
        flagged.storm_id,
        flagged.site_id,
        flagged.storm_started_at,
        flagged.storm_ended_at,
        flagged.severity,
        sum(case when flagged.is_episode_start then 1 else 0 end) over (
            partition by flagged.site_id
            order by flagged.storm_started_at, flagged.storm_id
            rows between unbounded preceding and current row
        ) as episode_number
    from flagged
),

episodes as (
    select
        numbered.site_id,
        numbered.episode_number,
        min(numbered.storm_started_at) as episode_started_at,
        max(numbered.storm_ended_at) as episode_ended_at,
        count(*) as storm_event_count,
        max(
            case numbered.severity
                when 'high' then 3
                when 'moderate' then 2
                when 'low' then 1
            end
        ) as max_severity_rank,
        string_agg(numbered.storm_id, ',' order by numbered.storm_id) as storm_ids
    from numbered
    group by
        numbered.site_id,
        numbered.episode_number
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['episodes.site_id', 'episodes.episode_started_at']) }}
            as storm_episode_id,
        episodes.site_id,
        episodes.episode_started_at,
        episodes.episode_ended_at,
        cast(
            timezone('{{ var("site_timezone", "Europe/Oslo") }}', timezone('UTC', episodes.episode_started_at))
            as date
        ) as episode_start_date,
        -- Last local date containing an instant of the half-open episode
        -- interval: end - 1 microsecond, so an end exactly at local
        -- midnight does not claim that day.
        cast(
            timezone(
                '{{ var("site_timezone", "Europe/Oslo") }}',
                timezone('UTC', episodes.episode_ended_at - interval '1 microsecond')
            ) as date
        ) as episode_end_date,
        episodes.storm_event_count,
        case episodes.max_severity_rank
            when 3 then 'high'
            when 2 then 'moderate'
            when 1 then 'low'
        end as max_severity,
        episodes.storm_ids
    from episodes
)

select * from final

-- One row per storm episode (grouping of closely spaced storm events
-- at one site; see int_storm_episodes).
--
-- Naming caution for consumers: episode_span_minutes / _hours is the
-- WALL-CLOCK span of the episode and deliberately INCLUDES the quiet
-- gaps between member storms. It is never storm exposure - actual
-- exposure minutes per day live in fct_pen_storm_analysis.storm_minutes.
--
-- storm_episode_key equals the intermediate storm_episode_id: that id
-- is already a surrogate over the natural key (site_id +
-- episode_started_at), both of which are retained here as readable
-- attributes. Timestamps are UTC; episode_start_date/episode_end_date
-- are local (Europe/Oslo) calendar dates.

with

episodes as (
    select * from {{ ref('int_storm_episodes') }}
),

final as (
    select
        episodes.storm_episode_id as storm_episode_key,
        {{ dbt_utils.generate_surrogate_key(['episodes.site_id']) }} as site_key,
        episodes.site_id,
        episodes.episode_started_at,
        episodes.episode_ended_at,
        episodes.episode_start_date,
        episodes.episode_end_date,
        date_diff('minute', episodes.episode_started_at, episodes.episode_ended_at)
            as episode_span_minutes,
        round(
            date_diff('minute', episodes.episode_started_at, episodes.episode_ended_at) / 60.0,
            3
        ) as episode_span_hours,
        episodes.storm_event_count,
        episodes.max_severity,
        episodes.storm_ids
    from episodes
)

select * from final

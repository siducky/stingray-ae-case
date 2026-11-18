-- Grain: one row per storm episode (site × episode start).
-- episode_span_* is wall-clock and includes quiet gaps, NOT exposure.
-- Timestamps UTC; start/end dates local. Key = storm_episode_id.

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

-- Grain: one row per site × pen × date. Additive pen-day operational fact.
-- Missing telemetry is null, never zero (has_reported_activity flags it).
-- Additive: node-day counts, expected minutes, shots, detections, uptime.
-- Semi-additive: fish_count snapshot (never sum across dates).
-- Site-day, NOT additive across pens: has_storm, storm_count, storm_minutes,
-- max_storm_severity.
-- Shared core metrics: expected_node_minutes, uptime_pct, reporting_completeness,
-- shots/detections per operating hour, shots per detection.

with

pen_days as (
    select * from {{ ref('int_pen_daily_activity') }}
),

fish_counts as (
    select * from {{ ref('int_pen_daily_fish_count') }}
),

site_storm_days as (
    select * from {{ ref('int_site_daily_storm_summary') }}
),

final as (
    select
        pen_days.pen_day_id,
        cast(strftime(pen_days.activity_date, '%Y%m%d') as integer) as date_key,
        {{ dbt_utils.generate_surrogate_key(['pen_days.site_id']) }} as site_key,
        {{ dbt_utils.generate_surrogate_key(['pen_days.pen_id']) }} as pen_key,
        pen_days.site_id,
        pen_days.pen_id,
        pen_days.activity_date,
        pen_days.day_duration_minutes,
        pen_days.expected_node_days,
        pen_days.reported_node_days,
        pen_days.expected_node_minutes,
        pen_days.has_reported_activity,
        pen_days.reporting_completeness,
        pen_days.laser_shot_count,
        pen_days.lice_detection_count,
        pen_days.uptime_minutes,
        pen_days.uptime_pct,
        pen_days.shots_per_operating_hour,
        pen_days.detections_per_operating_hour,
        pen_days.shots_per_detection,
        pen_days.has_node_set_change,
        pen_days.node_ids,
        fish_counts.fish_count,
        fish_counts.has_fish_count,
        fish_counts.fish_count_log_id,
        fish_counts.fish_count_age_days,
        fish_counts.fish_count_log_comment,
        coalesce(site_storm_days.has_storm, false) as has_storm,
        coalesce(site_storm_days.storm_count, 0) as storm_count,
        coalesce(site_storm_days.total_storm_minutes, 0) as storm_minutes,
        site_storm_days.max_storm_severity
    from pen_days
    left join fish_counts
        on fish_counts.pen_id = pen_days.pen_id
        and fish_counts.activity_date = pen_days.activity_date
    left join site_storm_days
        on site_storm_days.site_id = pen_days.site_id
        and site_storm_days.activity_date = pen_days.activity_date
)

select * from final

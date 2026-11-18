-- Grain: one row per pen × storm episode × date in the before/during/after window.
-- Before/during/after comparisons are aggregated from these rows; no baseline fact.
-- Additive within an episode only: a pen-day can appear in multiple episode windows.
-- Site-day, NOT additive across pens: has_storm, storm_count, storm_minutes,
-- max_storm_severity.
-- Fish counts live in fct_pen_daily_activity (join on pen_id + activity_date).
-- Shared core metrics with fct_pen_daily_activity. Descriptive only.

with

analysis as (
    select * from {{ ref('int_pen_storm_daily_analysis') }}
),

final as (
    select
        analysis.pen_storm_day_id,
        cast(strftime(analysis.activity_date, '%Y%m%d') as integer) as date_key,
        {{ dbt_utils.generate_surrogate_key(['analysis.site_id']) }} as site_key,
        {{ dbt_utils.generate_surrogate_key(['analysis.pen_id']) }} as pen_key,
        analysis.storm_episode_id as storm_episode_key,
        analysis.site_id,
        analysis.pen_id,
        analysis.activity_date,
        analysis.storm_period,
        analysis.days_from_episode_start,
        analysis.day_duration_minutes,
        analysis.expected_node_days,
        analysis.reported_node_days,
        analysis.expected_node_minutes,
        analysis.has_reported_activity,
        analysis.reporting_completeness,
        analysis.laser_shot_count,
        analysis.lice_detection_count,
        analysis.uptime_minutes,
        analysis.uptime_pct,
        analysis.shots_per_operating_hour,
        analysis.detections_per_operating_hour,
        analysis.shots_per_detection,
        analysis.has_storm,
        analysis.storm_count,
        analysis.storm_minutes,
        analysis.max_storm_severity,
        analysis.node_ids,
        analysis.has_node_set_change
    from analysis
)

select * from final

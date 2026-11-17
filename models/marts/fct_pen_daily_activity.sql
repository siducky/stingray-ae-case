-- GRAIN: one row per site, pen and calendar date.
--
-- Daily operational fact: node activity aggregated to pen level, with
-- the selected fish-count snapshot and the site-day storm overlay.
-- Joined 1:1 from int_pen_daily_activity to int_pen_daily_fish_count
-- (pen + date) and int_site_daily_storm_summary (site + date) - no
-- fan-out. The storm overlay makes full-calendar storm context
-- available in the daily fact (site-day values, repeated per pen at the
-- site that day - not additive across pens); episode-relative analysis
-- lives in fct_pen_storm_analysis.
--
-- Usability: natural identifiers (site_id, pen_id, activity_date) are
-- retained next to the surrogate keys, so the table reads without
-- joins. Surrogate keys are generated with the same expressions as
-- the dimensions and verified by relationships tests.
--
-- Measure semantics:
--   - Missing telemetry is NOT zero: measures are null when no node
--     reported; reporting_completeness shows the share of assigned
--     nodes that reported.
--   - fish_count is a snapshot (latest valid entry carried forward
--     under a staleness threshold), null when stale or implausible -
--     never zero.
--   - storm_minutes / storm_count / has_storm come from the complete
--     storm registry, so a site-day without storms is a true zero.

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
        pen_days.expected_node_days,
        pen_days.reported_node_days,
        pen_days.reporting_completeness,
        pen_days.laser_shot_count,
        pen_days.lice_detection_count,
        pen_days.uptime_minutes,
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

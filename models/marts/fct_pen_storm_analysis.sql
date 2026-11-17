-- GRAIN: one row per pen, storm episode and analytical date (the
-- before/during/after window around the episode).
--
-- Daily storm-impact fact: period classification, actual storm exposure
-- and pen activity rates per pen-episode-day, plus the fish-count
-- snapshot as of each date. The pen-episode baseline comparison lives in
-- the separate fct_pen_storm_baseline (pen x episode grain) - join on
-- storm_episode_key + pen_key.
--
-- Measure semantics - READ BEFORE AGGREGATING:
--   - storm_minutes / storm_event_count are site-day exposure repeated
--     for every pen at the site that day: NOT additive across pens.
--   - laser_shot_count / lice_detection_count / uptime_minutes /
--     reporting_completeness duplicate the same pen-day values as
--     fct_pen_daily_activity, restricted to episode windows and keyed
--     additionally by episode. A pen-day can appear in two episodes'
--     windows, so summing THIS fact double-counts - pen-day totals
--     must come from fct_pen_daily_activity.
--   - fish_count is a snapshot (see fct_pen_daily_activity).
--
-- This model describes; it makes no causal claim that storms caused any
-- observed change.

with

analysis as (
    select * from {{ ref('int_pen_storm_daily_analysis') }}
),

fish_counts as (
    select * from {{ ref('int_pen_daily_fish_count') }}
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
        analysis.storm_minutes,
        analysis.storm_event_count,
        analysis.laser_shot_count,
        analysis.lice_detection_count,
        analysis.uptime_minutes,
        analysis.shots_per_operating_hour,
        analysis.detections_per_operating_hour,
        analysis.shots_per_detection,
        analysis.reporting_completeness,
        analysis.node_ids,
        analysis.has_node_set_change,
        fish_counts.fish_count,
        fish_counts.has_fish_count,
        fish_counts.fish_count_log_id,
        fish_counts.fish_count_age_days,
        fish_counts.fish_count_log_comment
    from analysis
    left join fish_counts
        on fish_counts.pen_id = analysis.pen_id
        and fish_counts.activity_date = analysis.activity_date
)

select * from final

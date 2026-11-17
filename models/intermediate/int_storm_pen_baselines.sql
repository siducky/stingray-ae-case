-- Grain: one row per pen and storm episode.
-- Before/during/after comparison. Rates (shots and detections per
-- operating hour, shots per detection) are total / total over the period
-- (never an average of daily rates); null when the denominator is zero
-- or missing. Percentage changes compare the during/after rate with the
-- baseline rate; null when the baseline rate is zero or unavailable.
-- during_days/after_days show how many window days back each figure.
-- has_node_change_in_window flags any node-set change in the window, so
-- comparisons spanning a node move can be discounted. Reporting
-- completeness (mean of daily values) shows reliability. Missing
-- activity is never treated as zero. All rates and percentages are
-- rounded to 3 decimals. Descriptive only - no causal claim.

with

analysis as (
    select * from {{ ref('int_pen_storm_daily_analysis') }}
),

per_pen_episode as (
    select
        analysis.storm_episode_id,
        analysis.site_id,
        analysis.pen_id,
        count(*) filter (where analysis.storm_period = 'before')
            as baseline_days,
        count(*) filter (where analysis.storm_period = 'during')
            as during_days,
        count(*) filter (where analysis.storm_period = 'after')
            as after_days,
        bool_or(analysis.has_node_set_change)
            as has_node_change_in_window,
        round(avg(analysis.reporting_completeness) filter (where analysis.storm_period = 'before'), 3)
            as baseline_reporting_completeness,
        sum(analysis.laser_shot_count) filter (where analysis.storm_period = 'before')
            as baseline_shots,
        sum(analysis.uptime_minutes) filter (where analysis.storm_period = 'before')
            as baseline_uptime_minutes,
        sum(analysis.lice_detection_count) filter (where analysis.storm_period = 'before')
            as baseline_detections,
        round(avg(analysis.reporting_completeness) filter (where analysis.storm_period = 'during'), 3)
            as during_reporting_completeness,
        sum(analysis.laser_shot_count) filter (where analysis.storm_period = 'during')
            as during_shots,
        sum(analysis.uptime_minutes) filter (where analysis.storm_period = 'during')
            as during_uptime_minutes,
        sum(analysis.lice_detection_count) filter (where analysis.storm_period = 'during')
            as during_detections,
        round(avg(analysis.reporting_completeness) filter (where analysis.storm_period = 'after'), 3)
            as after_reporting_completeness,
        sum(analysis.laser_shot_count) filter (where analysis.storm_period = 'after')
            as after_shots,
        sum(analysis.uptime_minutes) filter (where analysis.storm_period = 'after')
            as after_uptime_minutes,
        sum(analysis.lice_detection_count) filter (where analysis.storm_period = 'after')
            as after_detections,
        case
            when sum(analysis.uptime_minutes) filter (where analysis.storm_period = 'before') > 0
                then round(
                    cast(sum(analysis.laser_shot_count) filter (where analysis.storm_period = 'before') as double)
                    / sum(analysis.uptime_minutes) filter (where analysis.storm_period = 'before') * 60, 3
                )
        end as baseline_shots_per_operating_hour,
        case
            when sum(analysis.uptime_minutes) filter (where analysis.storm_period = 'during') > 0
                then round(
                    cast(sum(analysis.laser_shot_count) filter (where analysis.storm_period = 'during') as double)
                    / sum(analysis.uptime_minutes) filter (where analysis.storm_period = 'during') * 60, 3
                )
        end as during_shots_per_operating_hour,
        case
            when sum(analysis.uptime_minutes) filter (where analysis.storm_period = 'after') > 0
                then round(
                    cast(sum(analysis.laser_shot_count) filter (where analysis.storm_period = 'after') as double)
                    / sum(analysis.uptime_minutes) filter (where analysis.storm_period = 'after') * 60, 3
                )
        end as after_shots_per_operating_hour,
        case
            when sum(analysis.uptime_minutes) filter (where analysis.storm_period = 'before') > 0
                then round(
                    cast(sum(analysis.lice_detection_count) filter (where analysis.storm_period = 'before') as double)
                    / sum(analysis.uptime_minutes) filter (where analysis.storm_period = 'before') * 60, 3
                )
        end as baseline_detections_per_operating_hour,
        case
            when sum(analysis.uptime_minutes) filter (where analysis.storm_period = 'during') > 0
                then round(
                    cast(sum(analysis.lice_detection_count) filter (where analysis.storm_period = 'during') as double)
                    / sum(analysis.uptime_minutes) filter (where analysis.storm_period = 'during') * 60, 3
                )
        end as during_detections_per_operating_hour,
        case
            when sum(analysis.uptime_minutes) filter (where analysis.storm_period = 'after') > 0
                then round(
                    cast(sum(analysis.lice_detection_count) filter (where analysis.storm_period = 'after') as double)
                    / sum(analysis.uptime_minutes) filter (where analysis.storm_period = 'after') * 60, 3
                )
        end as after_detections_per_operating_hour,
        case
            when sum(analysis.lice_detection_count) filter (where analysis.storm_period = 'before') > 0
                then round(
                    cast(sum(analysis.laser_shot_count) filter (where analysis.storm_period = 'before') as double)
                    / sum(analysis.lice_detection_count) filter (where analysis.storm_period = 'before'), 3
                )
        end as baseline_shots_per_detection,
        case
            when sum(analysis.lice_detection_count) filter (where analysis.storm_period = 'during') > 0
                then round(
                    cast(sum(analysis.laser_shot_count) filter (where analysis.storm_period = 'during') as double)
                    / sum(analysis.lice_detection_count) filter (where analysis.storm_period = 'during'), 3
                )
        end as during_shots_per_detection,
        case
            when sum(analysis.lice_detection_count) filter (where analysis.storm_period = 'after') > 0
                then round(
                    cast(sum(analysis.laser_shot_count) filter (where analysis.storm_period = 'after') as double)
                    / sum(analysis.lice_detection_count) filter (where analysis.storm_period = 'after'), 3
                )
        end as after_shots_per_detection
    from analysis
    group by
        analysis.storm_episode_id,
        analysis.site_id,
        analysis.pen_id
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['per_pen_episode.storm_episode_id', 'per_pen_episode.pen_id']) }}
            as storm_pen_baseline_id,
        per_pen_episode.storm_episode_id,
        per_pen_episode.site_id,
        per_pen_episode.pen_id,
        per_pen_episode.baseline_days,
        per_pen_episode.during_days,
        per_pen_episode.after_days,
        per_pen_episode.has_node_change_in_window,
        per_pen_episode.baseline_reporting_completeness,
        per_pen_episode.baseline_shots,
        per_pen_episode.baseline_uptime_minutes,
        per_pen_episode.baseline_detections,
        per_pen_episode.baseline_shots_per_operating_hour,
        per_pen_episode.baseline_detections_per_operating_hour,
        per_pen_episode.baseline_shots_per_detection,
        per_pen_episode.during_reporting_completeness,
        per_pen_episode.during_shots,
        per_pen_episode.during_uptime_minutes,
        per_pen_episode.during_detections,
        per_pen_episode.during_shots_per_operating_hour,
        per_pen_episode.during_detections_per_operating_hour,
        per_pen_episode.during_shots_per_detection,
        per_pen_episode.after_reporting_completeness,
        per_pen_episode.after_shots,
        per_pen_episode.after_uptime_minutes,
        per_pen_episode.after_detections,
        per_pen_episode.after_shots_per_operating_hour,
        per_pen_episode.after_detections_per_operating_hour,
        per_pen_episode.after_shots_per_detection
    from per_pen_episode
),

with_pct as (
    select
        final.storm_pen_baseline_id,
        final.storm_episode_id,
        final.site_id,
        final.pen_id,
        final.baseline_days,
        final.during_days,
        final.after_days,
        final.has_node_change_in_window,
        final.baseline_reporting_completeness,
        final.baseline_shots,
        final.baseline_uptime_minutes,
        final.baseline_detections,
        final.baseline_shots_per_operating_hour,
        final.baseline_detections_per_operating_hour,
        final.baseline_shots_per_detection,
        final.during_reporting_completeness,
        final.during_shots,
        final.during_uptime_minutes,
        final.during_detections,
        final.during_shots_per_operating_hour,
        final.during_detections_per_operating_hour,
        final.during_shots_per_detection,
        final.after_reporting_completeness,
        final.after_shots,
        final.after_uptime_minutes,
        final.after_detections,
        final.after_shots_per_operating_hour,
        final.after_detections_per_operating_hour,
        final.after_shots_per_detection,
        case
            when final.baseline_shots_per_operating_hour is not null
                and final.baseline_shots_per_operating_hour <> 0
                and final.during_shots_per_operating_hour is not null
                then round(
                    (final.during_shots_per_operating_hour
                    - final.baseline_shots_per_operating_hour
                ) / final.baseline_shots_per_operating_hour * 100, 3)
        end as during_change_vs_baseline_pct,
        case
            when final.baseline_shots_per_operating_hour is not null
                and final.baseline_shots_per_operating_hour <> 0
                and final.after_shots_per_operating_hour is not null
                then round(
                    (final.after_shots_per_operating_hour
                    - final.baseline_shots_per_operating_hour
                ) / final.baseline_shots_per_operating_hour * 100, 3)
        end as after_change_vs_baseline_pct,
        case
            when final.baseline_detections_per_operating_hour is not null
                and final.baseline_detections_per_operating_hour <> 0
                and final.during_detections_per_operating_hour is not null
                then round(
                    (final.during_detections_per_operating_hour
                    - final.baseline_detections_per_operating_hour
                ) / final.baseline_detections_per_operating_hour * 100, 3)
        end as during_detections_change_vs_baseline_pct,
        case
            when final.baseline_detections_per_operating_hour is not null
                and final.baseline_detections_per_operating_hour <> 0
                and final.after_detections_per_operating_hour is not null
                then round(
                    (final.after_detections_per_operating_hour
                    - final.baseline_detections_per_operating_hour
                ) / final.baseline_detections_per_operating_hour * 100, 3)
        end as after_detections_change_vs_baseline_pct
    from final
)

select * from with_pct

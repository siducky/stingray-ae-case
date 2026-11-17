-- GRAIN: one row per pen and storm episode.
--
-- Pen-episode baseline fact: before/during/after totals, rates and
-- reporting completeness for the storm comparison. Grain-matched partner
-- of fct_pen_storm_analysis - join on storm_episode_key + pen_key to
-- see the comparison next to daily rows (no join fan-out: both are one
-- row per pen-episode on those keys).
--
-- Measure semantics: rates are total / total over the period (never an
-- average of daily rates) and null when the denominator is zero or
-- missing. Completeness is the unweighted mean of daily values. Each
-- row is one pen-episode: never sum across rows. Descriptive only - no
-- causal claim.

with

baselines as (
    select * from {{ ref('int_storm_pen_baselines') }}
),

final as (
    select
        baselines.storm_pen_baseline_id,
        baselines.storm_episode_id as storm_episode_key,
        {{ dbt_utils.generate_surrogate_key(['baselines.site_id']) }} as site_key,
        {{ dbt_utils.generate_surrogate_key(['baselines.pen_id']) }} as pen_key,
        baselines.site_id,
        baselines.pen_id,
        baselines.baseline_days,
        baselines.baseline_reporting_completeness,
        baselines.baseline_shots,
        baselines.baseline_uptime_minutes,
        baselines.baseline_detections,
        baselines.baseline_shots_per_operating_hour,
        baselines.baseline_detections_per_operating_hour,
        baselines.baseline_shots_per_detection,
        baselines.during_days,
        baselines.after_days,
        baselines.has_node_change_in_window,
        baselines.during_reporting_completeness,
        baselines.during_shots,
        baselines.during_uptime_minutes,
        baselines.during_detections,
        baselines.during_shots_per_operating_hour,
        baselines.during_detections_per_operating_hour,
        baselines.during_shots_per_detection,
        baselines.after_reporting_completeness,
        baselines.after_shots,
        baselines.after_uptime_minutes,
        baselines.after_detections,
        baselines.after_shots_per_operating_hour,
        baselines.after_detections_per_operating_hour,
        baselines.after_shots_per_detection,
        baselines.during_change_vs_baseline_pct,
        baselines.after_change_vs_baseline_pct,
        baselines.during_detections_change_vs_baseline_pct,
        baselines.after_detections_change_vs_baseline_pct
    from baselines
)

select * from final

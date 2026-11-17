{#-
    One row per pen and storm episode.

    Aggregates int_pen_storm_daily_analysis into comparable before /
    during / after metrics per pen-episode. Descriptive only - no causal
    claim that storms caused any change.

    Rate definition: total shots / total uptime minutes * 60 over the
    period (NOT an average of daily rates), so high-uptime days weigh
    proportionally. Null when total uptime is zero or missing; percentage
    changes are null when the baseline rate is zero or unavailable, or
    when the compared period has no rate.

    Reporting completeness is the unweighted mean of the daily
    reporting_completeness values in each period, so a comparison can be
    assessed for reliability. Missing activity is never treated as zero:
    pen-days with no node reports contribute null measures, which make the
    period sums null only when EVERY day in the period is missing.
-#}

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
        avg(analysis.reporting_completeness) filter (where analysis.storm_period = 'before')
            as baseline_reporting_completeness,
        sum(analysis.laser_shot_count) filter (where analysis.storm_period = 'before')
            as baseline_shots,
        sum(analysis.uptime_minutes) filter (where analysis.storm_period = 'before')
            as baseline_uptime_minutes,
        avg(analysis.reporting_completeness) filter (where analysis.storm_period = 'during')
            as during_reporting_completeness,
        sum(analysis.laser_shot_count) filter (where analysis.storm_period = 'during')
            as during_shots,
        sum(analysis.uptime_minutes) filter (where analysis.storm_period = 'during')
            as during_uptime_minutes,
        avg(analysis.reporting_completeness) filter (where analysis.storm_period = 'after')
            as after_reporting_completeness,
        sum(analysis.laser_shot_count) filter (where analysis.storm_period = 'after')
            as after_shots,
        sum(analysis.uptime_minutes) filter (where analysis.storm_period = 'after')
            as after_uptime_minutes
    from analysis
    group by
        analysis.storm_episode_id,
        analysis.site_id,
        analysis.pen_id
),

with_rates as (
    select
        per_pen_episode.*,
        case
            when per_pen_episode.baseline_uptime_minutes > 0
                then cast(per_pen_episode.baseline_shots as double)
                    / per_pen_episode.baseline_uptime_minutes * 60
        end as baseline_shots_per_operating_hour,
        case
            when per_pen_episode.during_uptime_minutes > 0
                then cast(per_pen_episode.during_shots as double)
                    / per_pen_episode.during_uptime_minutes * 60
        end as during_shots_per_operating_hour,
        case
            when per_pen_episode.after_uptime_minutes > 0
                then cast(per_pen_episode.after_shots as double)
                    / per_pen_episode.after_uptime_minutes * 60
        end as after_shots_per_operating_hour
    from per_pen_episode
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['with_rates.storm_episode_id', 'with_rates.pen_id']) }}
            as storm_pen_baseline_id,
        with_rates.storm_episode_id,
        with_rates.site_id,
        with_rates.pen_id,
        with_rates.baseline_days,
        with_rates.baseline_reporting_completeness,
        with_rates.baseline_shots,
        with_rates.baseline_uptime_minutes,
        with_rates.baseline_shots_per_operating_hour,
        with_rates.during_reporting_completeness,
        with_rates.during_shots,
        with_rates.during_uptime_minutes,
        with_rates.during_shots_per_operating_hour,
        with_rates.after_reporting_completeness,
        with_rates.after_shots,
        with_rates.after_uptime_minutes,
        with_rates.after_shots_per_operating_hour,
        case
            when with_rates.baseline_shots_per_operating_hour is not null
                and with_rates.baseline_shots_per_operating_hour <> 0
                and with_rates.during_shots_per_operating_hour is not null
                then (
                    with_rates.during_shots_per_operating_hour
                    - with_rates.baseline_shots_per_operating_hour
                ) / with_rates.baseline_shots_per_operating_hour * 100
        end as during_change_vs_baseline_pct,
        case
            when with_rates.baseline_shots_per_operating_hour is not null
                and with_rates.baseline_shots_per_operating_hour <> 0
                and with_rates.after_shots_per_operating_hour is not null
                then (
                    with_rates.after_shots_per_operating_hour
                    - with_rates.baseline_shots_per_operating_hour
                ) / with_rates.baseline_shots_per_operating_hour * 100
        end as after_change_vs_baseline_pct
    from with_rates
)

select * from final

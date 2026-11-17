-- Grain: one row per pen per calendar date, from the pen's first log
-- entry through the reporting period end (same source-driven window as
-- int_node_days_assigned, so the spines line up).
-- Fish counts are snapshots: the latest entry on or before the date
-- wins (tie-break: highest logged_at_local, then highest log_id) and is
-- carried forward only while plausible and younger than
-- var('fish_count_max_age_days'). Otherwise the count is withheld
-- (null, has_fish_count = false) - never silently substituted with an
-- older value or zeroed - while the source log id/ts/age stay for
-- traceability.

{% set fish_count_max_age_days = var('fish_count_max_age_days', 7) %}

with

fish_counts as (
    select * from {{ ref('int_fish_counts_validated') }}
),

activity as (
    select * from {{ ref('stg_stingray__node_daily_activity') }}
),

reporting_period as (
    select
        min(activity.activity_date) as reporting_start_date,
        max(activity.activity_date) as reporting_end_date
    from activity
),

pen_log_bounds as (
    select
        fish_counts.pen_id,
        min(fish_counts.logged_local_date) as first_log_date
    from fish_counts
    group by fish_counts.pen_id
),

pen_days as (
    select
        pen_log_bounds.pen_id,
        cast(days.day as date) as activity_date
    from pen_log_bounds
    cross join reporting_period,
    generate_series(
        greatest(pen_log_bounds.first_log_date, reporting_period.reporting_start_date)::timestamp,
        reporting_period.reporting_end_date::timestamp,
        interval '1 day'
    ) as days(day)
),

-- Latest entry on or before each date, across ALL entries (plausible or
-- not), so an implausible latest entry withholds rather than substitutes.
latest_entry as (
    select
        pen_days.pen_id,
        pen_days.activity_date,
        fish_counts.log_id as fish_count_log_id,
        fish_counts.logged_at_local as fish_count_log_local_ts,
        fish_counts.entered_by as fish_count_entered_by,
        fish_counts.log_comment as fish_count_log_comment,
        fish_counts.fish_count as selected_fish_count,
        fish_counts.logged_local_date as selected_log_date,
        fish_counts.is_fish_count_plausible as selected_is_plausible,
        row_number() over (
            partition by pen_days.pen_id, pen_days.activity_date
            order by fish_counts.logged_at_local desc, fish_counts.log_id desc
        ) as entry_rank
    from pen_days
    left join fish_counts
        on fish_counts.pen_id = pen_days.pen_id
        and fish_counts.logged_local_date <= pen_days.activity_date
),

selected_entry as (
    select
        latest_entry.pen_id,
        latest_entry.activity_date,
        latest_entry.fish_count_log_id,
        latest_entry.fish_count_log_local_ts,
        latest_entry.fish_count_entered_by,
        latest_entry.fish_count_log_comment,
        latest_entry.selected_fish_count,
        latest_entry.selected_is_plausible,
        date_diff(
            'day',
            latest_entry.selected_log_date,
            latest_entry.activity_date
        ) as fish_count_age_days
    from latest_entry
    where latest_entry.entry_rank = 1
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['selected_entry.pen_id', 'selected_entry.activity_date']) }}
            as pen_fish_count_day_id,
        selected_entry.pen_id,
        selected_entry.activity_date,
        -- Withheld unless plausible AND within the staleness threshold.
        case
            when selected_entry.selected_is_plausible
                and selected_entry.fish_count_age_days <= {{ fish_count_max_age_days }}
                then selected_entry.selected_fish_count
        end as fish_count,
        selected_entry.fish_count_log_id,
        selected_entry.fish_count_log_local_ts as fish_count_log_ts,
        selected_entry.fish_count_entered_by,
        selected_entry.fish_count_log_comment,
        selected_entry.fish_count_age_days,
        selected_entry.selected_is_plausible
            and selected_entry.fish_count_age_days <= {{ fish_count_max_age_days }}
            as has_fish_count
    from selected_entry
)

select * from final

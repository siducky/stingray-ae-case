{#-
    One row per pen per calendar date, from the pen's first log entry
    through the end of the reporting period.

    Fish counts are treated as snapshots, not daily measurements: the
    latest entry on or before the date is selected (deterministic rule:
    highest logged_at_local, ties broken by the highest log_id - assumed
    to be the later correction) and carried forward only while it is
    younger than var('fish_count_max_age_days') (default 7).

    Data-quality policy (flags come from int_fish_counts_validated):
      - Beyond the staleness threshold the count is NOT carried forward:
        fish_count becomes null and has_fish_count is false, while the
        source log id/timestamp/age are kept so the reason it is missing
        stays traceable.
      - When the LATEST entry for a date is implausible, an older value is
        NOT silently substituted: the snapshot is withheld (null,
        has_fish_count = false) and the selected log id points at the
        implausible entry, so the gap is visible and traceable. The pen
        stays without a snapshot until a newer valid entry arrives.
      - Plausible same-day duplicates are resolved by the deterministic
        selection rule above.

    The reporting window is the same deterministic, purely source-driven
    one as int_node_days_assigned (min/max activity_date in the source
    data; no CURRENT_DATE dependency, no override mechanism), so the
    snapshot spine lines up with the activity spine downstream.
-#}
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

-- Spine: one row per pen per day from the pen's first log entry to the
-- end of the reporting period. Before the first entry there is no
-- snapshot basis at all, so those dates are not represented.
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
-- not). Plausibility is applied at snapshot time so an implausible latest
-- entry withholds the snapshot instead of silently falling back to an
-- older value. Deterministic tie-break: highest logged_at_local, then
-- highest log_id.
latest_entry as (
    select
        pen_days.pen_id,
        pen_days.activity_date,
        fish_counts.log_id as fish_count_log_id,
        fish_counts.logged_at_local as fish_count_log_local_ts,
        fish_counts.entered_by as fish_count_entered_by,
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
        -- Carry forward only when the selected entry is plausible AND
        -- younger than the staleness threshold; otherwise the count is
        -- withheld (missing, not zero) while the source log stays
        -- traceable through the log columns.
        case
            when selected_entry.selected_is_plausible
                and selected_entry.fish_count_age_days <= {{ fish_count_max_age_days }}
                then selected_entry.selected_fish_count
        end as fish_count,
        selected_entry.fish_count_log_id,
        selected_entry.fish_count_log_local_ts as fish_count_log_ts,
        selected_entry.fish_count_entered_by,
        selected_entry.fish_count_age_days,
        selected_entry.selected_is_plausible
            and selected_entry.fish_count_age_days <= {{ fish_count_max_age_days }}
            as has_fish_count
    from selected_entry
)

select * from final

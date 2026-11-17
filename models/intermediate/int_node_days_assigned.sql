{#-
    One row per assigned node per calendar day in the reporting period.

    The reporting window is deterministic and purely source-driven: the
    observed min/max activity_date in the source data. There is no
    CURRENT_DATE dependency and no override mechanism.
-#}

with

activity as (
    select * from {{ ref('stg_stingray__node_daily_activity') }}
),

assignments as (
    select * from {{ ref('stg_stingray__node_pen_assignments') }}
),

reporting_period as (
    select
        min(activity.activity_date) as reporting_start_date,
        max(activity.activity_date) as reporting_end_date
    from activity
),

-- Daily date spine for every assignment, clipped to the reporting period.
-- valid_until_date is the exclusive bound, so valid_until_date - 1 is the
-- last assigned day. generate_series returns no rows when the clipped
-- range is empty (e.g. an assignment entirely outside the period).
node_days as (
    select
        assignments.assignment_id,
        assignments.node_id,
        assignments.site_id,
        assignments.pen_id,
        cast(days.day as date) as activity_date
    from assignments
    cross join reporting_period,
    generate_series(
        greatest(assignments.valid_from_date, reporting_period.reporting_start_date)::timestamp,
        least(assignments.valid_until_date - 1, reporting_period.reporting_end_date)::timestamp,
        interval '1 day'
    ) as days(day)
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['node_days.node_id', 'node_days.activity_date']) }}
            as node_day_id,
        node_days.assignment_id,
        node_days.node_id,
        node_days.site_id,
        node_days.pen_id,
        node_days.activity_date,
        -- Missing activity stays null: a node without a record is NOT a
        -- zero-activity node (see has_activity_record).
        activity.laser_shot_count,
        activity.lice_detection_count,
        activity.uptime_minutes,
        activity.node_activity_id is not null as has_activity_record
    from node_days
    left join activity
        on activity.node_id = node_days.node_id
        and activity.activity_date = node_days.activity_date
)

select * from final

-- Grain: one row per site, pen and activity date (multi-node pens are
-- valid). Measures sum over reporting nodes only and stay null when no
-- node reported: missing is NOT zero. has_node_set_change compares
-- against the previous AVAILABLE pen-day (window lag), not the previous
-- calendar day.
-- Shared core business metrics are defined here once so both reporting
-- facts expose identical definitions:
--   - expected_node_minutes = expected_node_days * the DST-aware local
--     day length from int_dates.
--   - uptime_pct = uptime_minutes / expected_node_minutes * 100 (null
--     when uptime is missing, 0 when reported uptime is genuinely zero).
--   - daily efficiency rates (shots/detections per operating hour,
--     shots per detection) are rounded to 3 decimals and null when
--     their denominators are zero or missing.
-- Every activity_date is present in int_dates by construction.

with

node_days as (
    select * from {{ ref('int_node_days_assigned') }}
),

dates as (
    select * from {{ ref('int_dates') }}
),

pen_days as (
    select
        node_days.site_id,
        node_days.pen_id,
        node_days.activity_date,
        dates.day_duration_minutes,
        count(*) as expected_node_days,
        count(*) filter (where node_days.has_activity_record) as reported_node_days,
        sum(node_days.laser_shot_count) as laser_shot_count,
        sum(node_days.lice_detection_count) as lice_detection_count,
        sum(node_days.uptime_minutes) as uptime_minutes,
        string_agg(node_days.node_id, ',' order by node_days.node_id) as node_ids
    from node_days
    inner join dates
        on dates.date_day = node_days.activity_date
    group by
        node_days.site_id,
        node_days.pen_id,
        node_days.activity_date,
        dates.day_duration_minutes
),

-- node_ids is sorted, so string equality is set equality.
with_node_set_change as (
    select
        pen_days.site_id,
        pen_days.pen_id,
        pen_days.activity_date,
        pen_days.day_duration_minutes,
        pen_days.expected_node_days,
        pen_days.reported_node_days,
        pen_days.laser_shot_count,
        pen_days.lice_detection_count,
        pen_days.uptime_minutes,
        pen_days.node_ids,
        coalesce(
            pen_days.node_ids
                <> lag(pen_days.node_ids) over (
                    partition by pen_days.site_id, pen_days.pen_id
                    order by pen_days.activity_date
                ),
            false
        ) as has_node_set_change
    from pen_days
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(
            ['with_node_set_change.site_id', 'with_node_set_change.pen_id', 'with_node_set_change.activity_date']
        ) }}
            as pen_day_id,
        with_node_set_change.site_id,
        with_node_set_change.pen_id,
        with_node_set_change.activity_date,
        with_node_set_change.day_duration_minutes,
        with_node_set_change.expected_node_days,
        with_node_set_change.reported_node_days,
        with_node_set_change.expected_node_days * with_node_set_change.day_duration_minutes
            as expected_node_minutes,
        with_node_set_change.reported_node_days > 0 as has_reported_activity,
        round(
            cast(with_node_set_change.reported_node_days as double)
                / with_node_set_change.expected_node_days, 3
        ) as reporting_completeness,
        with_node_set_change.laser_shot_count,
        with_node_set_change.lice_detection_count,
        with_node_set_change.uptime_minutes,
        case
            when with_node_set_change.uptime_minutes is not null
                then round(
                    cast(with_node_set_change.uptime_minutes as double)
                        / (with_node_set_change.expected_node_days * with_node_set_change.day_duration_minutes)
                        * 100, 3
                )
        end as uptime_pct,
        with_node_set_change.node_ids,
        with_node_set_change.has_node_set_change,
        case
            when with_node_set_change.uptime_minutes > 0
                then round(
                    cast(with_node_set_change.laser_shot_count as double)
                        / with_node_set_change.uptime_minutes * 60, 3
                )
        end as shots_per_operating_hour,
        case
            when with_node_set_change.uptime_minutes > 0
                then round(
                    cast(with_node_set_change.lice_detection_count as double)
                        / with_node_set_change.uptime_minutes * 60, 3
                )
        end as detections_per_operating_hour,
        case
            when with_node_set_change.lice_detection_count > 0
                then round(
                    cast(with_node_set_change.laser_shot_count as double)
                        / with_node_set_change.lice_detection_count, 3
                )
        end as shots_per_detection
    from with_node_set_change
)

select * from final

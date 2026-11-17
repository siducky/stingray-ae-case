{#-
    One row per site, pen and activity date.

    Aggregates the assigned node-days. A pen can hold multiple nodes at
    once; expected_node_days counts assigned nodes, reported_node_days
    counts nodes that actually reported. Activity measures are summed
    over reporting nodes only: sum() ignores nulls and returns null when
    every contributing node is missing, so a day with no reports stays
    null rather than becoming zero.

    has_node_set_change compares the node set with the PREVIOUS AVAILABLE
    pen-day (window lag), not necessarily the previous calendar day: if a
    pen has no assigned nodes for a while, the comparison is against the
    last day it did.
-#}

with

node_days as (
    select * from {{ ref('int_node_days_assigned') }}
),

pen_days as (
    select
        node_days.site_id,
        node_days.pen_id,
        node_days.activity_date,
        count(*) as expected_node_days,
        count(*) filter (where node_days.has_activity_record) as reported_node_days,
        sum(node_days.laser_shot_count) as laser_shot_count,
        sum(node_days.lice_detection_count) as lice_detection_count,
        sum(node_days.uptime_minutes) as uptime_minutes,
        string_agg(node_days.node_id, ',' order by node_days.node_id) as node_ids
    from node_days
    group by
        node_days.site_id,
        node_days.pen_id,
        node_days.activity_date
),

-- node_ids is sorted, so string equality is set equality.
with_node_set_change as (
    select
        pen_days.site_id,
        pen_days.pen_id,
        pen_days.activity_date,
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
        with_node_set_change.expected_node_days,
        with_node_set_change.reported_node_days,
        with_node_set_change.laser_shot_count,
        with_node_set_change.lice_detection_count,
        with_node_set_change.uptime_minutes,
        with_node_set_change.node_ids,
        with_node_set_change.has_node_set_change,
        cast(with_node_set_change.reported_node_days as double)
            / with_node_set_change.expected_node_days as reporting_completeness
    from with_node_set_change
)

select * from final

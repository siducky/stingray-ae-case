-- A pen must always belong to the same site across all assignment periods.
-- Returns offending pens (test fails if any rows are returned).

with

assignments as (
    select * from {{ ref('stg_stingray__node_pen_assignments') }}
),

pen_site_counts as (
    select
        assignments.pen_id,
        count(distinct assignments.site_id) as site_count
    from assignments
    group by assignments.pen_id
),

final as (
    select
        pen_site_counts.pen_id,
        pen_site_counts.site_count
    from pen_site_counts
    where pen_site_counts.site_count > 1
)

select * from final

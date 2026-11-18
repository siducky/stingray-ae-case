-- Grain: one row per pen (assignments ∪ farmer logs).
-- site_id/site_key are CURRENT-state only; historical site attribution is per day in the facts.
-- current_node_ids/has_node_changes describe the node history. No Type 2 history.

with

assignments as (
    select * from {{ ref('stg_stingray__node_pen_assignments') }}
),

fish_counts as (
    select * from {{ ref('int_fish_counts_validated') }}
),

pens as (
    select assignments.pen_id from assignments
    union
    select fish_counts.pen_id from fish_counts
),

pen_attributes as (
    select
        assignments.pen_id,
        arg_max(assignments.site_id, assignments.valid_from_date) as site_id,
        string_agg(assignments.node_id, ',' order by assignments.node_id)
            filter (where assignments.is_current_assignment) as current_node_ids,
        count(distinct assignments.node_id) > 1 as has_node_changes,
        min(assignments.valid_from_date) as first_assignment_date,
        bool_or(assignments.is_current_assignment) as is_currently_assigned
    from assignments
    group by assignments.pen_id
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['pens.pen_id']) }} as pen_key,
        pens.pen_id,
        case
            when pen_attributes.site_id is not null
                then {{ dbt_utils.generate_surrogate_key(['pen_attributes.site_id']) }}
        end as site_key,
        pen_attributes.site_id,
        pen_attributes.current_node_ids,
        pen_attributes.has_node_changes,
        pen_attributes.first_assignment_date,
        pen_attributes.is_currently_assigned
    from pens
    left join pen_attributes
        on pen_attributes.pen_id = pens.pen_id
)

select * from final

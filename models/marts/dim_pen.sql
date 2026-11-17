-- Grain: one row per globally unique pen (collected from assignments and
-- farmer logs so every fact foreign key resolves).
--
-- Pen-site caution: site_id / site_key are the pen's CURRENT site (latest
-- assignment) - current-state attributes only. Historical site attribution
-- lives per-day in the fact tables (site_key on every fact row), never
-- flattened onto the pen's whole history. current_node_ids lists the
-- nodes currently assigned to the pen; has_node_changes flags pens that
-- hosted more than one node over their history (e.g. P103: N03 then N05).
--
-- Pens seen only in farmer logs (no assignment) have null site and node
-- attributes. No descriptive pen attributes exist in the source; none
-- are invented. No Type 2 history: the only historically varying pen
-- properties are its site and nodes, both captured per day in the facts.

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

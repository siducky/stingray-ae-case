-- Grain: one row per site (assignments ∪ storms).
-- Only source attribute is site_id; assignment dates are derived. Null dates = storm-only site.

with

assignments as (
    select * from {{ ref('stg_stingray__node_pen_assignments') }}
),

storms as (
    select * from {{ ref('stg_stingray__storm_events') }}
),

sites as (
    select assignments.site_id from assignments
    union
    select storms.site_id from storms
),

assignment_dates as (
    select
        assignments.site_id,
        min(assignments.valid_from_date) as first_assignment_date,
        max(assignments.valid_from_date) as latest_assignment_date
    from assignments
    group by assignments.site_id
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['sites.site_id']) }} as site_key,
        sites.site_id,
        assignment_dates.first_assignment_date,
        assignment_dates.latest_assignment_date
    from sites
    left join assignment_dates
        on assignment_dates.site_id = sites.site_id
)

select * from final

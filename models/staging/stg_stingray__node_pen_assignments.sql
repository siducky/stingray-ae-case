with

source as (
    select * from {{ source('stingray', 'node_pen_assignment') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['trim(source.node_id)', 'cast(source.valid_from as date)']) }}
        as assignment_id,
        trim(source.node_id) as node_id,
        trim(source.site_id) as site_id,
        trim(source.pen_id) as pen_id,
        cast(source.valid_from as date) as valid_from_date,
        -- Blank means "still deployed": normalise '' to null before the DATE cast...
        cast(
            nullif(trim(cast(source.valid_to as varchar)), '') as date
        ) as valid_to_date,
        -- valid_to is inclusive ... so + 1 gives the exclusive bound...
        coalesce(valid_to_date + 1, date '9999-12-31') as valid_until_date,
        valid_to_date is null as is_current_assignment
    from source
)

select * from final

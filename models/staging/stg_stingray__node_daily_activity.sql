with

source as (
    select * from {{ source('stingray', 'node_daily_activity') }}
),

renamed as (
    select
        trim(source.node_id)                    as node_id,
        cast(source.activity_date as date)      as activity_date,
        cast(source.lice_detections as integer) as lice_detection_count,
        cast(source.shots_fired as integer)     as laser_shot_count,
        cast(source.uptime_minutes as integer)  as uptime_minutes
    from source
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['renamed.node_id', 'renamed.activity_date']) }} as node_activity_id,
        renamed.node_id,
        renamed.activity_date,
        renamed.lice_detection_count,
        renamed.laser_shot_count,
        renamed.uptime_minutes
    from renamed
)

select * from final

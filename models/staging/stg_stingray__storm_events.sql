with

source as (
    select * from {{ source('stingray', 'storm_events') }}
),

renamed as (
    select
        trim(source.storm_id) as storm_id,
        trim(source.site_id) as site_id,
        -- Source values are ISO-8601 text with a UTC offset (Z). Casting to timestamptz
        -- applies the offset; timezone('UTC', ...) then returns a naive UTC timestamp.
        timezone('UTC', cast(source.start_ts as timestamptz)) as storm_started_at,
        timezone('UTC', cast(source.end_ts as timestamptz)) as storm_ended_at,
        lower(trim(source.severity)) as severity
    from source
),

final as (
    select
        renamed.storm_id,
        renamed.site_id,
        renamed.storm_started_at,
        renamed.storm_ended_at,
        date_diff('second', renamed.storm_started_at, renamed.storm_ended_at)
            / 3600.0 as storm_duration_hours,
        renamed.severity
    from renamed
)

select * from final

-- Grain: one row per storm event per local calendar date.
-- Half-open [storm_started_at, storm_ended_at) UTC intervals clipped to
-- the DST-aware day boundaries from int_dates (naive-UTC comparison).
-- A day touched only at the exact end boundary gets no row.

with

storms as (
    select * from {{ ref('stg_stingray__storm_events') }}
),

dates as (
    select * from {{ ref('int_dates') }}
),

-- Local calendar dates touched by each storm. A storm ending exactly at
-- local midnight still lists that date here; the zero-minute row is
-- filtered out below (half-open interval [start, end)).
localised as (
    select
        storms.storm_id,
        storms.site_id,
        storms.severity,
        storms.storm_started_at,
        storms.storm_ended_at,
        cast(
            timezone('{{ var("site_timezone", "Europe/Oslo") }}', timezone('UTC', storms.storm_started_at))
            as date
        ) as local_start_date,
        cast(
            timezone('{{ var("site_timezone", "Europe/Oslo") }}', timezone('UTC', storms.storm_ended_at))
            as date
        ) as local_end_date
    from storms
),

storm_days as (
    select
        localised.storm_id,
        localised.site_id,
        localised.severity,
        localised.storm_started_at,
        localised.storm_ended_at,
        cast(days.day as date) as storm_date
    from localised,
    generate_series(
        localised.local_start_date::timestamp,
        localised.local_end_date::timestamp,
        interval '1 day'
    ) as days(day)
),

-- Clip each storm to each local day using the shared DST-aware
-- boundaries from int_dates, expressed as naive UTC.
day_minutes as (
    select
        storm_days.storm_id,
        storm_days.site_id,
        storm_days.severity,
        storm_days.storm_started_at,
        storm_days.storm_ended_at,
        storm_days.storm_date,
        date_diff(
            'minute',
            greatest(storm_days.storm_started_at, dates.day_start_utc),
            least(storm_days.storm_ended_at, dates.day_end_utc)
        ) as storm_minutes
    from storm_days
    inner join dates
        on dates.date_day = storm_days.storm_date
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['day_minutes.storm_id', 'day_minutes.storm_date']) }}
            as storm_day_id,
        day_minutes.storm_id,
        day_minutes.site_id,
        day_minutes.storm_date,
        day_minutes.severity,
        day_minutes.storm_started_at,
        day_minutes.storm_ended_at,
        day_minutes.storm_minutes
    from day_minutes
    -- Half-open intervals: a day the storm only touches at its exact end
    -- boundary contributes zero minutes and is not an exposure day.
    where day_minutes.storm_minutes > 0
)

select * from final

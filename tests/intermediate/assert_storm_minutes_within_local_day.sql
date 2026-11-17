-- Storm minutes must fit inside the local calendar day they are attributed to.
-- Day lengths come from int_dates, which is DST-aware, so shifted days get
-- their true length (23h in spring, 25h in autumn).
-- Returns offending storm-days (test fails if any rows are returned).

with

exposure as (
    select * from {{ ref('int_storm_daily_exposure') }}
),

dates as (
    select * from {{ ref('int_dates') }}
),

with_day_length as (
    select
        exposure.storm_day_id,
        exposure.storm_minutes,
        dates.day_duration_minutes
    from exposure
    inner join dates
        on dates.date_day = exposure.storm_date
)

select
    with_day_length.storm_day_id,
    with_day_length.storm_minutes,
    with_day_length.day_duration_minutes
from with_day_length
where with_day_length.storm_minutes < 0
    or with_day_length.storm_minutes > with_day_length.day_duration_minutes

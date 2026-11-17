-- The int_dates spine must be continuous: one row per calendar day between
-- its first and last date, with no gaps and no duplicates.
-- Returns offending bounds (test fails if any rows are returned).

with

dates as (
    select * from {{ ref('int_dates') }}
),

bounds as (
    select
        min(dates.date_day) as first_date,
        max(dates.date_day) as last_date,
        count(*) as row_count
    from dates
)

select
    bounds.first_date,
    bounds.last_date,
    bounds.row_count,
    date_diff('day', bounds.first_date, bounds.last_date) + 1 as expected_row_count
from bounds
where bounds.row_count <> date_diff('day', bounds.first_date, bounds.last_date) + 1

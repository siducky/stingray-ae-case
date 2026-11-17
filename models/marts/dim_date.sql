-- One row per local calendar date. Power BI / analyst-facing date
-- dimension built on int_dates.
--
-- date_key is a compact sortable integer (YYYYMMDD) - the classic
-- warehouse date key - rather than an md5 surrogate. Calendar
-- attributes are rich enough that consumers never need date functions:
-- group by year_month, week_start_date, weekday_name etc.
--
-- day_duration_minutes and is_dst_transition_day come from the
-- DST-aware int_dates spine, so uptime-style measures can be
-- interpreted correctly on 23h/25h Oslo days.

with

dates as (
    select * from {{ ref('int_dates') }}
),

final as (
    select
        cast(strftime(dates.date_day, '%Y%m%d') as integer) as date_key,
        dates.date_day,
        year(dates.date_day) as year_number,
        quarter(dates.date_day) as quarter_number,
        month(dates.date_day) as month_number,
        strftime(dates.date_day, '%B') as month_name,
        strftime(dates.date_day, '%Y-%m') as year_month,
        weekofyear(dates.date_day) as week_of_year,
        cast(date_trunc('week', dates.date_day) as date) as week_start_date,
        isodow(dates.date_day) as day_of_week,
        strftime(dates.date_day, '%A') as weekday_name,
        isodow(dates.date_day) >= 6 as is_weekend,
        dates.day_duration_minutes,
        dates.day_duration_minutes <> 1440 as is_dst_transition_day
    from dates
)

select * from final

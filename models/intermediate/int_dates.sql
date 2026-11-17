{#-
    One row per local calendar date.

    Central, DST-aware date spine in var('site_timezone') (Europe/Oslo by
    default). Local day boundaries are computed by round-tripping local
    midnight through the timezone, so a 23-hour spring-forward day and a
    25-hour Oslo fall-back day keep their true durations (1380 / 1500
    minutes).

    The range is deterministic and purely source-driven: every
    activity_date plus every local calendar date touched by any storm
    (start or end instant). No CURRENT_DATE dependency - the
    storm-splitting models must never lose a day to a clipped spine.
-#}
{% set site_timezone = var('site_timezone', 'Europe/Oslo') %}

with

activity as (
    select * from {{ ref('stg_stingray__node_daily_activity') }}
),

storms as (
    select * from {{ ref('stg_stingray__storm_events') }}
),

-- Local calendar dates touched by any storm (start or end instant).
-- Conservative by at most one day when a storm ends exactly at local
-- midnight; an unused spine day is harmless.
storm_local_dates as (
    select
        cast(
            timezone('{{ site_timezone }}', timezone('UTC', storms.storm_started_at))
            as date
        ) as date_day
    from storms
    union
    select
        cast(
            timezone('{{ site_timezone }}', timezone('UTC', storms.storm_ended_at))
            as date
        ) as date_day
    from storms
),

all_dates as (
    select activity.activity_date as date_day from activity
    union
    select storm_local_dates.date_day from storm_local_dates
),

bounds as (
    select
        min(all_dates.date_day) as first_date,
        max(all_dates.date_day) as last_date
    from all_dates
),

spine as (
    select
        cast(days.day as date) as date_day
    from bounds,
    generate_series(
        bounds.first_date::timestamp,
        bounds.last_date::timestamp,
        interval '1 day'
    ) as days(day)
),

final as (
    select
        spine.date_day,
        timezone('UTC', timezone('{{ site_timezone }}', spine.date_day::timestamp))
            as day_start_utc,
        timezone('UTC', timezone('{{ site_timezone }}', (spine.date_day + 1)::timestamp))
            as day_end_utc,
        date_diff(
            'minute',
            timezone('UTC', timezone('{{ site_timezone }}', spine.date_day::timestamp)),
            timezone('UTC', timezone('{{ site_timezone }}', (spine.date_day + 1)::timestamp))
        ) as day_duration_minutes
    from spine
)

select * from final

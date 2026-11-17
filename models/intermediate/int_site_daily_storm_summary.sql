-- Grain: one row per site per storm-affected day; joining to pen activity
-- never multiplies rows.
-- total_storm_minutes is CUMULATIVE EVENT-MINUTES: overlapping storms
-- would double-count (warn test guards this).
-- Storm-free days are absent here; downstream left joins coalesce them
-- to zero exposure.

with

storm_days as (
    select * from {{ ref('int_storm_daily_exposure') }}
),

-- severity is ordinal (low < moderate < high): map to a rank, take the
-- max, map back.
severity_ranked as (
    select
        storm_days.site_id,
        storm_days.storm_date as activity_date,
        storm_days.storm_id,
        storm_days.storm_minutes,
        case storm_days.severity
            when 'high' then 3
            when 'moderate' then 2
            when 'low' then 1
        end as severity_rank
    from storm_days
),

site_days as (
    select
        severity_ranked.site_id,
        severity_ranked.activity_date,
        count(distinct severity_ranked.storm_id) as storm_count,
        sum(severity_ranked.storm_minutes) as total_storm_minutes,
        max(severity_ranked.severity_rank) as max_severity_rank
    from severity_ranked
    group by
        severity_ranked.site_id,
        severity_ranked.activity_date
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['site_days.site_id', 'site_days.activity_date']) }}
            as site_day_id,
        site_days.site_id,
        site_days.activity_date,
        site_days.storm_count,
        site_days.total_storm_minutes,
        case site_days.max_severity_rank
            when 3 then 'high'
            when 2 then 'moderate'
            when 1 then 'low'
        end as max_storm_severity,
        true as has_storm
    from site_days
)

select * from final

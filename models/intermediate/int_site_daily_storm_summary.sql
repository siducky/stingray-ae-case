{#-
    One row per site per storm-affected calendar date.

    total_storm_minutes is CUMULATIVE EVENT-MINUTES: minutes are summed per
    storm event, so two overlapping storms at the same site on the same day
    double-count the overlapping wall-clock time. See
    tests/intermediate/assert_no_overlapping_storms_per_site.sql, which
    warns if any overlap ever appears in the data.

    Only days with storm exposure exist here. Days without storms are
    materialised as zero exposure downstream (the final analytical dataset
    left joins this model onto its pen-day spine), which is why has_storm
    is a constant true in this model.
-#}

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

-- total_storm_minutes in int_site_daily_storm_summary is cumulative event-minutes:
-- overlapping storms at the same site would double-count shared wall-clock time.
-- No such overlap exists in the current data; this warn-level test surfaces one
-- if it ever appears, so the metric can be switched to merged-interval exposure.
-- Returns pairs of overlapping storms at the same site (test fails if any rows are returned).

{{ config(severity = 'warn') }}

with

storms as (
    select * from {{ ref('stg_stingray__storm_events') }}
),

overlapping as (
    select
        storm_a.storm_id as storm_id_a,
        storm_b.storm_id as storm_id_b,
        storm_a.site_id
    from storms as storm_a
    inner join storms as storm_b
        on storm_a.site_id = storm_b.site_id
        and storm_a.storm_id < storm_b.storm_id
    -- Half-open intervals overlap when each starts before the other ends.
    where storm_a.storm_started_at < storm_b.storm_ended_at
        and storm_b.storm_started_at < storm_a.storm_ended_at
)

select * from overlapping

-- Grain: one row per pen, storm episode and date in the analytical
-- window: before (storm_baseline_days dates before episode_start_date),
-- during (all episode dates; partially affected days count), after
-- (storm_post_days dates after episode_end_date). Windows are generated
-- arithmetically - they extend beyond the int_dates spine.
-- Pen membership: a pen belongs to an episode only if it had assigned
-- nodes at the episode's site on at least one DURING date, so pens that
-- moved away before the storm (e.g. P202 after N05 left on 2026-10-08)
-- are excluded from the whole window. Within the window the pen still
-- appears only on dates where it had assigned nodes (historical
-- assignments respected). All joins are 1:1 at their grain - no fan-out.
-- storm_minutes/storm_event_count are actual site-day exposure (0 when
-- storm-free), independent of the classification.
-- Rates (shots/detections per operating hour, shots per detection) are
-- null when their denominators are zero or missing.
-- Descriptive only - no causal claim.

with

episodes as (
    select * from {{ ref('int_storm_episodes') }}
),

pen_activity as (
    select * from {{ ref('int_pen_daily_activity') }}
),

site_storm_days as (
    select * from {{ ref('int_site_daily_storm_summary') }}
),

-- One row per episode per local calendar date in the analytical window.
-- Before/during/after ranges are disjoint by construction (before ends at
-- start_date - 1, during covers start_date..end_date, after starts at
-- end_date + 1).
episode_days as (
    select
        episodes.storm_episode_id,
        episodes.site_id,
        episodes.episode_start_date,
        episodes.episode_end_date,
        cast(days.day as date) as activity_date,
        case
            when cast(days.day as date) < episodes.episode_start_date then 'before'
            when cast(days.day as date) > episodes.episode_end_date then 'after'
            else 'during'
        end as storm_period
    from episodes,
    generate_series(
        (episodes.episode_start_date - {{ var('storm_baseline_days', 3) }})::timestamp,
        (episodes.episode_end_date + {{ var('storm_post_days', 3) }})::timestamp,
        interval '1 day'
    ) as days(day)
),

-- Episode membership: pens with assigned nodes at the episode's site on
-- at least one during date.
episode_pens as (
    select distinct
        episode_days.storm_episode_id,
        episode_days.site_id,
        pen_activity.pen_id
    from episode_days
    inner join pen_activity
        on pen_activity.site_id = episode_days.site_id
        and pen_activity.activity_date = episode_days.activity_date
    where episode_days.storm_period = 'during'
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(
            ['episode_days.storm_episode_id', 'episode_pens.pen_id', 'episode_days.activity_date']
        ) }}
            as pen_storm_day_id,
        episode_days.storm_episode_id,
        episode_days.site_id,
        episode_pens.pen_id,
        episode_days.activity_date,
        episode_days.storm_period,
        date_diff(
            'day',
            episode_days.episode_start_date,
            episode_days.activity_date
        ) as days_from_episode_start,
        coalesce(site_storm_days.total_storm_minutes, 0) as storm_minutes,
        coalesce(site_storm_days.storm_count, 0) as storm_event_count,
        pen_activity.laser_shot_count,
        pen_activity.lice_detection_count,
        pen_activity.uptime_minutes,
        pen_activity.shots_per_operating_hour,
        pen_activity.detections_per_operating_hour,
        pen_activity.shots_per_detection,
        pen_activity.reporting_completeness,
        pen_activity.node_ids,
        pen_activity.has_node_set_change
    from episode_days
    inner join episode_pens
        on episode_pens.storm_episode_id = episode_days.storm_episode_id
    -- Pen/site/date spine: only dates where the pen had assigned nodes
    -- at the episode's site (historical assignments respected).
    inner join pen_activity
        on pen_activity.site_id = episode_days.site_id
        and pen_activity.pen_id = episode_pens.pen_id
        and pen_activity.activity_date = episode_days.activity_date
    -- Actual exposure per site-day, independent of the period
    -- classification: a before/after day can carry another episode's
    -- storm minutes, and a during day shows real minutes only.
    left join site_storm_days
        on site_storm_days.site_id = episode_days.site_id
        and site_storm_days.activity_date = episode_days.activity_date
)

select * from final

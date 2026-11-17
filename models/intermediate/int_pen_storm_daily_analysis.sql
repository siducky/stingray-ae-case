{#-
    One row per pen, storm episode and local calendar date within the
    analytical window (before / during / after the episode).

    Window definitions (local calendar dates, configurable):
      - before: the storm_baseline_days (default 3) dates immediately
        preceding episode_start_date;
      - during: all dates from episode_start_date through episode_end_date
        (a partially affected day still counts as during);
      - after: the storm_post_days (default 3) dates immediately following
        episode_end_date.

    Dates are generated arithmetically from the episode bounds rather than
    joined from int_dates on purpose: the before/after windows extend
    beyond the source-derived spine, and joining the spine would silently
    truncate them.

    Grain control - no fan-out:
      - episodes are unique per (storm_episode_id);
      - int_pen_daily_activity is unique per (site_id, pen_id, activity_date)
        and is ALSO the pen/site/date spine: a pen appears on a date only
        when it had assigned nodes at that site on that date (historical
        assignments respected);
      - int_site_daily_storm_summary is unique per (site_id, activity_date).
    So each output row is exactly one pen-day of one episode.

    storm_minutes / storm_event_count come from the site-day storm summary
    (actual exposure), not from the episode span: quiet gaps inside an
    episode contribute nothing. The storm registry is complete, so a
    site-day with no storm row is a true zero, coalesced here to 0.

    shots_per_operating_hour is null when uptime is zero or missing - a
    zero-uptime day never produces an artificial zero rate. This model
    classifies and exposes; it does not attribute causation.
-#}

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

final as (
    select
        {{ dbt_utils.generate_surrogate_key(
            ['episode_days.storm_episode_id', 'pen_activity.pen_id', 'episode_days.activity_date']
        ) }}
            as pen_storm_day_id,
        episode_days.storm_episode_id,
        episode_days.site_id,
        pen_activity.pen_id,
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
        case
            when pen_activity.uptime_minutes > 0
                then cast(pen_activity.laser_shot_count as double)
                    / pen_activity.uptime_minutes * 60
        end as shots_per_operating_hour,
        pen_activity.reporting_completeness
    from episode_days
    -- Pen/site/date spine: only pens with assigned nodes at the episode's
    -- site on that date (historical assignments respected).
    inner join pen_activity
        on pen_activity.site_id = episode_days.site_id
        and pen_activity.activity_date = episode_days.activity_date
    -- Actual exposure per site-day, independent of the period
    -- classification: a before/after day can carry another episode's
    -- storm minutes, and a during day shows real minutes only.
    left join site_storm_days
        on site_storm_days.site_id = episode_days.site_id
        and site_storm_days.activity_date = episode_days.activity_date
)

select * from final

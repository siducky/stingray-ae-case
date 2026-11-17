-- Grain: one row per farmer log entry - validation flags only, nothing
-- removed or corrected.
-- is_fish_count_plausible: fish_count <= var('fish_count_plausible_max').
-- is_duplicate_pen_day: several entries share the pen's local date
-- (legitimate corrections; if an entry is also implausible, implausible
-- wins). Selection is resolved downstream deterministically (latest
-- logged_at_local, then highest log_id).

with

fish_logs as (
    select * from {{ ref('stg_stingray__farmer_pen_logs') }}
),

final as (
    select
        fish_logs.log_id,
        fish_logs.pen_id,
        fish_logs.logged_at,
        fish_logs.logged_at_local,
        fish_logs.logged_local_date,
        fish_logs.fish_count,
        fish_logs.entered_by,
        fish_logs.log_comment,
        fish_logs.fish_count <= {{ var('fish_count_plausible_max', 1000000) }}
            as is_fish_count_plausible,
        count(*) over (
            partition by fish_logs.pen_id, fish_logs.logged_local_date
        ) > 1 as is_duplicate_pen_day
    from fish_logs
)

select * from final

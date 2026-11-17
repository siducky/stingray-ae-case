{#-
    One row per original farmer log entry - validation only, no selection.

    Separates data-quality flagging from the daily snapshot selection in
    int_pen_daily_fish_count. Every source record is preserved; nothing is
    removed or corrected here.

    Flags (a former fish_count_quality_status column was removed as fully
    derivable from these two flags; int_pen_daily_fish_count uses
    is_fish_count_plausible only):
      - is_fish_count_plausible: fish_count <= var('fish_count_plausible_max').
      - is_duplicate_pen_day: more than one entry exists for this pen on
        this local date. Duplicates are quality-relevant but NOT invalid:
        a same-day correction is a legitimate duplicate.

    Precedence when interpreting the flags: an entry that is both
    implausible and a duplicate counts as implausible (implausibility is
    the more severe condition). Duplicate selection is resolved
    deterministically downstream: latest logged_at_local, then highest
    log_id.
-#}

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

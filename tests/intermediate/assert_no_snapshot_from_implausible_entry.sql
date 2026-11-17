-- No daily fish-count snapshot may be built from an implausible source entry,
-- and a pen-date whose latest entry is implausible must NOT silently fall
-- back to an older plausible value: the snapshot stays null while the log id
-- still points at the implausible entry (traceable, not substituted).
-- Returns offending snapshot rows (test fails if any rows are returned).

with

snapshots as (
    select * from {{ ref('int_pen_daily_fish_count') }}
),

validated as (
    select * from {{ ref('int_fish_counts_validated') }}
)

select
    snapshots.pen_fish_count_day_id,
    snapshots.pen_id,
    snapshots.activity_date,
    snapshots.fish_count_log_id
from snapshots
inner join validated
    on validated.log_id = snapshots.fish_count_log_id
where snapshots.has_fish_count
    and not validated.is_fish_count_plausible

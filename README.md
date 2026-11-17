# Stingray Case Study — dbt Analytics Engineering

Local DuckDB warehouse (`data/warehouse/stingray.duckdb`) built with dbt from the raw extracts in
`data/raw/`. Layered staging → intermediate → marts. See `docs/limitations.md` and
`docs/production_portability.md` for scope decisions and porting notes.

Run everything through `uv run` (the project virtualenv is managed by uv).

## Getting started

```bash
# 1. Install the environment (creates .venv from pyproject.toml + uv.lock)
uv sync

# 2. Verify the dbt/DuckDB connection
uv run dbt debug --profiles-dir .

# 3. Build all layers (staging -> intermediate -> marts) and run all tests
uv run dbt build --profiles-dir .
```

### Common commands

```bash
# Build or test a single layer / model
uv run dbt build --select staging --profiles-dir .
uv run dbt build --select intermediate --profiles-dir .
uv run dbt build --select marts --profiles-dir .
uv run dbt run --select int_pen_daily_fish_count --profiles-dir .

# Tests only
uv run dbt test --profiles-dir .

# Generate and serve the docs + lineage graph (http://localhost:8080)
uv run dbt docs generate --profiles-dir .
uv run dbt docs serve --profiles-dir . --port 8080 --no-browser

# Lint / format Python and Marimo notebook files
uv run ruff check --fix . && uv run ruff format .

# Validate notebooks
uv run marimo check notebooks/

# Edit a notebook interactively
uv run marimo edit notebooks/01_data_exploration.py
```

The lineage graph is available in the served docs (left-hand "graph" icon, or the circular-nodes
view) and statically in `target/manifest.json`.

### Configuration overrides

Analytical thresholds are `vars` in `dbt_project.yml` (see the table below) and can be overridden
per run:

```bash
uv run dbt build --select intermediate --profiles-dir . \
  --vars '{fish_count_max_age_days: 14, storm_baseline_days: 5}'
```

**Note:** the warehouse is a single DuckDB file — make sure no other tool (e.g. DBeaver) holds it
open, or `dbt build` fails with a lock error.

## Executive summary (for Kari)

**Question: did laser activity change during the October storms?** Yes — but the data also says
how carefully to read it.

- **S01, high-severity episode (Oct 5–7):** shots per operating hour fell during the storm —
  P101 **−24.0%**, P102 **−48.5%**, P103 **−8.3%** vs each pen's own quiet-weather baseline.
  Detection rate fell similarly (−23.3%, −43.7%, −11.3%), while shots-per-detection stayed flat
  (~1.3): the cameras saw fewer lice per hour, but the laser worked no less efficiently per
  lice found.
- **Uptime, not only behaviour:** P101 and P103 reported **zero uptime** on Oct 6, the peak of
  the storm — the drop is at least partly the system being down, not the system choosing not
  to shoot. Reporting completeness flags exactly these days.
- **Caveat for P103:** its node changed (N03 → N05) on Oct 8, the day *after* the episode —
  `has_node_change_in_window` marks it, and Oct 8 shows completeness 0 (no telemetry on the
  move-day).
- **Fish counts around the storm:** the P101 farmer logged "some mortality after storm"
  (172,400 → 171,100 by Oct 8, −1,300). P202 moved ~40k fish to P201 on Oct 8. P201's Oct 8
  log (1,852,000) is flagged implausible and that pen has no snapshot from Oct 8 onward.
- **S02's two milder episodes (Oct 9–10 moderate, Oct 14 low):** P201 moved −3.3% / +0.2% vs
  baseline — within noise. P202 left the site before the storms (N05 moved on Oct 8) and is
  correctly excluded from those episodes.

**Data reliability:** all S01 comparisons rest on 100% reporting completeness in the baseline
and during periods. Bottom line: the high-severity storm coincided with a large activity
drop that is partly explained by downtime; the milder storms show no clear effect.

## Lineage

```
data/raw (CSV, all_varchar)
│
├─ node_daily_activity.csv ─────► stg_stingray__node_daily_activity ──┬─► int_node_days_assigned ──► int_pen_daily_activity ──┐
├─ node_pen_assignment.csv ─────► stg_stingray__node_pen_assignments ─┘                                                           │
│                                                                                                                                  ▼
│                                                                  int_storm_episodes ◄───────────── stg_stingray__storm_events ◄─ storm_events.csv
│                                                                          │                                                       │
│                                                                          ▼                                                       ▼
│                                          int_pen_storm_daily_analysis ◄────────────────────────────────────────────── int_site_daily_storm_summary
│                                                                          │                                        ▲                ◄─ int_storm_daily_exposure ◄─ int_dates
│                                                                          ▼                                        │
│                                                     int_storm_pen_baselines                                │
│                                                                                                            int_dates ◄──────────┘
└─ farmer_pen_log.csv ──────────► stg_stingray__farmer_pen_logs ──► int_fish_counts_validated ──► int_pen_daily_fish_count
                                                                                      │
                                                                                      ▼
                                              fct_pen_daily_activity ◄── int_pen_daily_activity / int_site_daily_storm_summary

Mart models (7):
  dim_date            ◄─ int_dates
  dim_site            ◄─ stg_stingray__node_pen_assignments + stg_stingray__storm_events
  dim_pen             ◄─ stg_stingray__node_pen_assignments + int_fish_counts_validated
  dim_storm_episode   ◄─ int_storm_episodes
  fct_pen_daily_activity       ◄─ int_pen_daily_activity + int_pen_daily_fish_count + int_site_daily_storm_summary
  fct_pen_storm_analysis       ◄─ int_pen_storm_daily_analysis + int_pen_daily_fish_count
  fct_pen_storm_baseline       ◄─ int_storm_pen_baselines
```

`int_dates` is built from `stg_stingray__node_daily_activity` + `stg_stingray__storm_events` and
provides the shared DST-aware local-day spine. `int_pen_storm_daily_analysis` also uses
`int_pen_daily_activity` as its pen/site/date spine (historical assignments respected).
`stg_stingray__node_daily_activity` is referenced by `int_pen_daily_fish_count` only to define the
deterministic reporting window.

## Mart layer (star schema)

```
                        dim_date
                       1      1 \                        dim_storm_episode
                       |         \                     1 /         |
                       *          *                     /          *
        fct_pen_daily_activity   fct_pen_storm_analysis             fct_pen_storm_baseline
        (site × pen × date)      (pen × episode × date)             (pen × episode)
                       ^          ^         ^          ^                    ^
                    1  |       1  |      1  |       1  |                 1  |
                       |          |         |          |                    |
                    dim_site   dim_pen   dim_site  dim_storm_episode   dim_site / dim_pen
```

All dimension → fact relationships are **one-to-many, single-direction** (dimension filters fact).
No many-to-many, no bidirectional filtering. `dim_date`, `dim_site` and `dim_pen` are conformed
across all facts. The two storm facts are grain-matched partners: `fct_pen_storm_baseline` joins
`fct_pen_storm_analysis` 1:1 on `storm_episode_key + pen_key`.

### Grain and key summary

| Table | Grain | Primary key | Foreign keys |
|---|---|---|---|
| `dim_date` | one row per calendar date | `date_key` (int YYYYMMDD) | — |
| `dim_site` | one row per site | `site_key` | — |
| `dim_pen` | one row per pen | `pen_key` | — |
| `dim_storm_episode` | one row per storm episode | `storm_episode_key` | — |
| `fct_pen_daily_activity` | one row per site × pen × date | `pen_day_id` | `date_key`, `site_key`, `pen_key` |
| `fct_pen_storm_analysis` | one row per pen × episode × analytical date | `pen_storm_day_id` | `date_key`, `site_key`, `pen_key`, `storm_episode_key` |
| `fct_pen_storm_baseline` | one row per pen × episode | `storm_pen_baseline_id` | `site_key`, `pen_key`, `storm_episode_key` |

Natural identifiers (`site_id`, `pen_id`, `activity_date`) are retained in both facts so the
tables read without joins. `dim_pen.current_site_id` is a current-state attribute only —
historical site attribution lives per day in the facts (`has_multiple_sites` flags pens where it
matters). No Type 2 dimensions: the only historically varying property (pen → site) is already
captured per day in the facts.

### Measure additivity rules (read before aggregating)

- `fct_pen_daily_activity` is the **additive pen-day source of truth** for shots, detections,
  uptime and reporting completeness.
- `fct_pen_storm_analysis` covers episode windows only; a pen-day can appear in two episodes'
  windows (one episode's after = the next episode's before), so **summing it double-counts**.
  Its activity measures duplicate the daily fact's values — kept deliberately so storm-impact
  questions are answered from one table.
- `fct_pen_storm_baseline` is one row per pen-episode with before/during/after totals, rates
  (total/total, never averages of daily rates) and completeness — never sum across its rows.
- `storm_minutes` / `storm_event_count` are site-day exposure repeated per pen — not additive
  across pens.
- `fish_count` is a snapshot, not a flow: differences between dates are meaningful, sums are not.
- All rates and percentages are rounded to 3 decimals where computed.

### Query recipes (SQL)

```sql
-- Daily operations overview for a site
select activity_date, pen_id, laser_shot_count, lice_detection_count, uptime_minutes,
       reporting_completeness, fish_count
from fct_pen_daily_activity
where site_id = 'S01'
order by activity_date, pen_id;

-- Storm impact per pen: daily activity next to the baseline comparison
select a.pen_id, a.activity_date, a.storm_period, a.storm_minutes, a.laser_shot_count,
       a.shots_per_operating_hour, b.baseline_shots_per_operating_hour,
       b.baseline_reporting_completeness
from fct_pen_storm_analysis a
join fct_pen_storm_baseline b using (storm_episode_key, pen_key)
join dim_storm_episode using (storm_episode_key)
where dim_storm_episode.max_severity = 'high'
order by a.pen_id, a.activity_date;

-- Data-quality check: pen-days with missing telemetry
select site_id, pen_id, activity_date, expected_node_days, reported_node_days, node_ids
from fct_pen_daily_activity
where reporting_completeness < 1
order by activity_date;

-- Weekly rollup with calendar attributes (no date functions needed)
select d.year_month, d.week_start_date, f.site_id,
       sum(f.laser_shot_count) as shots, sum(f.uptime_minutes) as uptime,
       avg(f.reporting_completeness) as avg_completeness
from fct_pen_daily_activity f
join dim_date d using (date_key)
group by d.year_month, d.week_start_date, f.site_id
order by d.week_start_date;
```

In Power BI: import the seven mart tables, relate each dimension's key to the matching fact key
(one-to-many, single direction), and build measures per fact — pen-day totals from
`fct_pen_daily_activity`, storm comparisons from `fct_pen_storm_baseline`. Both storm facts
analyse at different grains, so relate them to the shared conformed dimensions
(`dim_storm_episode`, `dim_pen`, `dim_site`) rather than to each other: a dimension selection
filters all facts through the conformed keys. Do **not** model a direct fact-to-fact
relationship — the 1:1 composite-key join (`storm_episode_key + pen_key`) between the storm
facts is a SQL convenience, not a Power BI relationship.

## Intermediate models and grains

| Model | Grain | Rows | Purpose |
|---|---|---|---|
| `int_dates` | one row per local calendar date (`date_day`) | 14 | Central DST-aware date spine (UTC day boundaries, true day duration 1380/1440/1500 min). Source-driven range: activity dates ∪ storm-touched local dates. |
| `int_node_days_assigned` | one row per assigned node per calendar day (`node_id` × `activity_date`) | 63 | Attributes each node-day to the site/pen valid **on that date** (temporal assignment), keeps days without telemetry as null measures with `has_activity_record = false`. |
| `int_storm_daily_exposure` | one row per storm event per local calendar day (`storm_id` × `storm_date`) | 6 | Splits half-open storm intervals `[start, end)` into Europe/Oslo days using `int_dates` boundaries. |
| `int_site_daily_storm_summary` | one row per site per storm-affected day (`site_id` × `activity_date`) | 6 | Aggregates storm exposure to site-day so joining to pen activity never multiplies rows. `total_storm_minutes` is **cumulative event-minutes** (see assumptions). |
| `int_pen_daily_activity` | one row per site, pen, day (`site_id` × `pen_id` × `activity_date`) | 63 | Aggregates node-days to pen-days: expected/reported node days, summed measures, node set, node-set-change flag, reporting completeness. |
| `int_fish_counts_validated` | one row per farmer log entry (`log_id`) | 10 | Validation only: `is_fish_count_plausible`, `is_duplicate_pen_day`. Nothing removed or corrected. |
| `int_pen_daily_fish_count` | one row per pen per day from the pen's first log through the reporting period end (`pen_id` × `activity_date`) | 70 | Daily snapshot: latest entry on or before the date (tie-break: highest `log_id`), carried forward only while younger than `fish_count_max_age_days`; implausible latest entries withhold the snapshot instead of silently substituting an older value. |
| `int_storm_episodes` | one row per storm episode per site (`site_id` × `episode_started_at`) | 3 | Groups events at a site whose gap is strictly < `storm_episode_gap_hours` (24); gaps of exactly 24h start a new episode. Running-max gaps-and-islands (overlap/nesting safe). Episode span includes quiet gaps — never exposure. |
| `int_pen_storm_daily_analysis` | one row per pen, episode and local date in the window (`storm_episode_id` × `pen_id` × `activity_date`) | 41 | Before (3 dates) / during (episode dates, partially affected included) / after (3 dates) classification with pen activity, actual site-day storm minutes and rates. Pens included only while assigned at the episode's site. |
| `int_storm_pen_baselines` | one row per pen and episode (`storm_episode_id` × `pen_id`) | 6 | Before/during/after comparison: total shots / total uptime × 60 (never an average of daily rates), reporting completeness, percentage changes (null on zero/unavailable baselines). |

### Reporting window (deterministic, no `CURRENT_DATE`)

`int_node_days_assigned` and `int_pen_daily_fish_count` cover
`min(activity_date) … max(activity_date)` observed in `stg_stingray__node_daily_activity`
(currently 2026-10-01 … 2026-10-14). The window is purely source-driven with no override
mechanism — see `docs/limitations.md` for the consequence.

## Configuration (dbt_project.yml vars)

| Var | Default | Meaning |
|---|---|---|
| `site_timezone` | `Europe/Oslo` | Zone for site-local calendar days (storm day-splitting, episode dates; matches the assumed `activity_date` boundary). |
| `fish_count_plausible_max` | `1000000` | Entries above this are implausible: flagged in `int_fish_counts_validated`, never selected as snapshots (kept in staging). |
| `fish_count_max_age_days` | `7` | Maximum age of a fish-count entry before it is no longer carried forward. |
| `storm_episode_gap_hours` | `24` | Events at a site merge when the gap is strictly below this; a gap of exactly this starts a new episode. |
| `storm_baseline_days` | `3` | Local dates of quiet weather before the episode start date (baseline period). |
| `storm_post_days` | `3` | Local dates after the episode end date (post period). |

`farmer_log_timezone` (staging) remains `Europe/Oslo`.

## Assumptions and trade-offs

1. **Temporal attribution.** A node-day belongs to the assignment whose normalised half-open
   interval `[valid_from_date, valid_until_date)` contains the date. Validated: N05 switches
   S02/P202 → S01/P103 on 2026-10-08, and its missing 2026-10-08 activity is retained as null
   measures (`has_activity_record = false`), not zeros. The only node-set change in the data is
   P103 on 2026-10-08 (N03 → N05).
2. **Missing ≠ zero.** Pen-day sums stay null when every contributing node is missing
   (P103 2026-10-08, P201 2026-10-12 both have `reporting_completeness = 0` and null measures).
   When only some nodes report, the sum covers reporting nodes only — a partial sum, documented
   here because pen-day truth is unknowable from the source.
3. **`total_storm_minutes` is cumulative event-minutes.** Minutes are summed per storm event, so
   two overlapping storms at one site on one day would double-count shared wall-clock time. No
   overlaps exist in the data; `tests/intermediate/assert_no_overlapping_storms_per_site.sql`
   (warn) fires if one ever appears, at which point the metric should become merged-interval
   exposure. Renaming the column was rejected because the brief fixes the column list.
4. **Storm-free days are not in `int_site_daily_storm_summary`.** The model only contains days
   with exposure (`has_storm` is therefore constant true). The final analytical dataset will left
   join it onto the pen-day spine and coalesce to zero exposure / `has_storm = false`.
5. **DST handling.** Local day boundaries are computed in `int_dates` by round-tripping local
   midnight through `var('site_timezone')`, so a 23-hour spring day allows up to 1380 storm
   minutes and a 25-hour Oslo fall-back day up to 1500 (the same ceiling staging allows for
   uptime). All storm-vs-day comparisons happen in naive-UTC space. No storm in the data crosses
   a DST transition. Storms ending exactly at local midnight contribute no row to that day
   (half-open interval) — covered by a unit test.
6. **Fish-count selection rule.** Latest entry on or before the date; ties on identical timestamps
   broken by the highest `log_id` (assumed to be the later correction). Counts are snapshots, not
   daily measurements, and are carried forward only while
   `fish_count_age_days <= fish_count_max_age_days` (7). Stale days keep the source
   `log_id`/timestamp/age (traceable) but withhold the count.
7. **Implausible latest entries are not silently substituted.** When the latest entry for a date is
   above `fish_count_plausible_max`, the snapshot is withheld (null, `has_fish_count = false`) and
   the retained `fish_count_log_id` points at the implausible entry, so the gap is visible and
   traceable. The pen stays without a snapshot until a newer plausible entry arrives. Behaviour
   change vs. the first intermediate iteration (which fell back to the last plausible entry):
   P201 has no fish count from 2026-10-08 onward.
8. **Episode grouping is analytical, not exposure.** `int_storm_episodes` merges events at a site
   when the gap to the running-maximum end is strictly < 24h (exactly 24h splits; different sites
   never merge; overlaps and nesting are safe). The episode span is wall-clock and includes quiet
   gaps; exposure minutes live only in `int_storm_daily_exposure` / `int_site_daily_storm_summary`.
   Episode bounds are half-open: `episode_end_date` is the local date of the last exposed instant, so
   an episode ending exactly at local midnight does not claim that day.
9. **Before/during/after windows are local calendar dates.** Before = 3 dates immediately preceding
   `episode_start_date`; during = all episode dates (a partially affected day counts as during);
   after = 3 dates following `episode_end_date`. A pen appears on a date only when it had assigned
   nodes at the episode's site on that date, so P202 drops out of the S02 episodes after N05 moved
   on 2026-10-08. `days_from_episode_start` is relative to the episode start date. The models
   describe, they never claim storms caused changes.
10. **`storm_minutes` / `storm_event_count` in the analysis model are actual site-day exposure**
    (0 when the site-day had no storm — the storm registry is complete, so absence is a true zero),
    independent of the before/during/after classification: a before/after day can carry another
    episode's minutes.
11. **`int_pen_daily_fish_count` extends the declared input list.** The original brief listed only
    `stg_stingray__farmer_pen_logs`; it now consumes `int_fish_counts_validated` (validation
    separated from selection) and still references `stg_stingray__node_daily_activity` **only** to
    define the deterministic reporting window, so the snapshot spine lines up with the activity
    spine. No activity values are used.
12. **`int_dates` is deliberately not used everywhere.** `int_storm_daily_exposure` reuses it (it
    removes duplicated timezone logic). `int_node_days_assigned`, `int_pen_daily_fish_count` and the
    episode windows keep their own `generate_series` spines: the first two clip to the reporting
    window (which `int_dates` does not know about) and the episode windows extend beyond the
    source-derived spine (before/after periods reach outside the observed data range), so joining
    `int_dates` would silently truncate them.
13. **`has_node_set_change` compares with the previous available pen-day** (window `lag` over
    `activity_date`), not necessarily the previous calendar day — a pen with a gap in assignments
    compares against its last observed day.
14. **Storm/site and pen/site referential checks are warn-level** (inherited from staging): raw
    storms and farmer logs reference sites/pens that exist in assignments, but a warn keeps the
    pipeline running if an extract ever contains an unknown site.

## Data Quality Findings

| Finding | Where | Handling |
|---|---|---|
| N05 has no activity record on 2026-10-08 (its move-day) | `int_node_days_assigned` | Retained as a spine row with null measures and `has_activity_record = false`; P103 2026-10-08 has `reporting_completeness = 0`. |
| N04 has no activity record on 2026-10-12 | `int_node_days_assigned` | Same treatment; P201 2026-10-12 `reporting_completeness = 0`. |
| P201 log 1014 on 2026-10-08 records 1,852,000 fish (10× the next largest count) | `int_fish_counts_validated` → `int_pen_daily_fish_count` | Flagged `implausible` in `int_fish_counts_validated` (`fish_count_plausible_max`), never selected. Because it is the LATEST entry for that pen, no older value is silently substituted: the snapshot is withheld from 2026-10-08 onward with the log id kept for traceability. The entry itself is preserved in staging and flagged by the pre-existing warn test. |
| P102 has two entries on 2026-10-08 (08:16 and a 14:47 "corrected count") | `int_fish_counts_validated` → `int_pen_daily_fish_count` | Both flagged `duplicate` (legitimate correction). Latest entry wins (14:47, log 1013, 164,300); deterministic tie-break (highest timestamp, then highest log_id) covered by a unit test with an exact-timestamp tie. |
| P103 has no farmer log after 2026-10-01 | `int_pen_daily_fish_count` | The 2026-10-01 snapshot is carried to 2026-10-08 (age 7), then withheld as stale from 2026-10-09. |
| S02 storms ST-0042 (ends 2026-10-10 03:00Z) and ST-0043 (starts 2026-10-13 22:30Z) are ~3.8 days apart | `int_storm_episodes` | Gap exceeds `storm_episode_gap_hours` (24), so two separate episodes — never merged. |
| No overlapping storm events per site | `int_site_daily_storm_summary`, `int_storm_episodes` | Verified by warn-level tests; keeps `total_storm_minutes` meaningful as cumulative event-minutes and episode exposure within the span. |
| No overlapping assignment periods per node | staging test `assert_node_has_one_assignment_at_a_time` (gaps allowed) | Inherited guarantee the temporal join relies on; the intermediate grain test (`node_id` × `activity_date` unique) proves no node-day is attributed to multiple assignments. |

## Tests

`uv run dbt build --profiles-dir .` → **316 tests, 315 pass, 1 warn, 0 errors.**
The single warn is the pre-existing staging plausibility check that flags P201's 1,852,000 entry
(deliberate). The intermediate layer contributes 154 tests and the mart layer 102
(data + singular + unit):

- Surrogate keys unique + not null on all ten models; grain uniqueness
  (`node_id`×`activity_date`, `storm_id`×`storm_date`, `site_id`×`activity_date`,
  `site_id`×`pen_id`×`activity_date`, `pen_id`×`activity_date`, `site_id`×`episode_started_at`,
  `storm_episode_id`×`pen_id`×`activity_date`, `storm_episode_id`×`pen_id`, `log_id`, `date_day`).
- `reported_node_days <= expected_node_days`; `reporting_completeness` in [0, 1];
  `storm_minutes` > 0 and within the DST-aware local day length; `node_ids` list length equals
  `expected_node_days`; missing activity is null, never zero; fish count present exactly when
  fresh, never older than the age threshold, and never built from an implausible entry.
- Episode guards: positive ranges, ordered dates, `storm_event_count >= 1`, severity values.
- Analysis guards: window boundaries (before = −N..−1, during ≥ 0, after ≥ 1 from episode start),
  no duplicated pen-day within an episode, zero/missing uptime never yields a rate.
- Baseline guards: rates null exactly when uptime is zero/missing or shots unavailable; percentage
  changes null exactly when the baseline rate is zero/unavailable.
- Foreign keys: `assignment_id`, `storm_id`, `site_id` (warn), `fish_count_log_id`,
  `storm_episode_id`.
- Singular tests: date-spine continuity; storm minutes within the true (DST-aware) local day
  length; episode exposure conservation (day-splitting preserves storm durations; quiet gaps never
  become exposure); no snapshot from an implausible entry; no overlapping storms per site (warn).
- Unit tests: N05 assignment transition with missing move-day telemetry; multi-day storm splitting
  (ST-0041 → 300/1440/420 min) and a midnight-ending storm; storm episodes (23h gap merges,
  exactly-24h gap splits, overlapping and nested intervals merge, different sites never merge);
  fish-count latest-entry, correction, timestamp-tie, implausibility-without-substitution and
  staleness rules; pen-day null preservation and completeness; before/during/after windows with a
  partially affected first day, zero-uptime and missing-activity days; baseline rates, percentage
  changes and null handling (zero baseline uptime, fully missing during period).

## Deliberately not done (awaiting stakeholder review)

- **The before/during/after comparison is descriptive.** `fct_pen_storm_analysis` reports changes
  vs baseline with reporting completeness for reliability assessment; it makes no causal claim and
  does not control for confounders (season, biomass, node set changes).
- **No full-calendar storm fact.** Storm exposure is only exposed inside episode windows
  (`fct_pen_storm_analysis.storm_minutes`); a small `fct_site_daily_storm` fact (site × date) was
  proposed for full-calendar overlay and declined for now.
- **Merged-interval storm exposure** if overlapping storms ever appear (cumulative event-minutes
  today, see assumption 3).
- **Multi-site timezone lookup** — see `docs/limitations.md`.

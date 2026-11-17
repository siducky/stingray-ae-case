# Stingray Case Study — dbt Analytics Engineering

Local DuckDB warehouse (`data/warehouse/stingray.duckdb`) built with dbt from the raw extracts in
`data/raw/`. Layered staging → intermediate → marts. See `docs/limitations.md` and
`docs/production_portability.md` for scope decisions and porting notes.

Run everything through `uv run` (the project virtualenv is managed by uv).

## Repository structure

```
.
├── data/
│   ├── raw/                        # four source CSVs (read-only inputs)
│   └── warehouse/                  # stingray.duckdb, built by dbt (generated)
├── models/
│   ├── staging/                    # sources.yml, 1:1 staging views, tests and docs
│   ├── intermediate/               # business-logic views, YAML and unit tests
│   └── marts/                      # dimensions and facts (tables), tests and docs
├── notebooks/
│   ├── 01_data_exploration.py      # EDA: raw CSVs exposed as DuckDB views
│   ├── stingray_case_presentation.py  # 13-slide case deck (Marimo slides)
│   ├── theme.css                   # deck palette, typography, section backgrounds
│   └── layouts/                    # slides layout, speaker notes, deck settings
├── docs/
│   ├── diagrams/                   # Mermaid sources (.mmd) and rendered SVGs
│   ├── limitations.md              # scope decisions and upgrade paths
│   ├── production_portability.md   # DuckDB → Snowflake/Postgres notes
│   └── stingray_case_presentation.pdf  # rendered deck handout (13 pages)
├── tests/
│   ├── staging/                    # singular tests on staging models
│   └── intermediate/               # singular tests on intermediate models
├── src/stingray_ae_case/           # installable Python package (uv project)
├── dbt_packages/                   # installed dbt packages (generated)
├── target/, logs/                  # dbt artifacts and logs (generated)
├── dbt_project.yml                 # dbt config, vars, materialisations
├── packages.yml                    # dbt package dependencies
├── profiles.yml                    # local DuckDB connection
├── pyproject.toml, uv.lock         # Python environment and dependencies
└── README.md
```

Generated and git-ignored: `.venv/`, `data/warehouse/`, `data/raw/*` (only `.gitkeep` is
tracked), `target/`, `logs/`, `dbt_packages/` and marimo's `__marimo__/` cache.

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

## Presentation notebook (Marimo)

`notebooks/stingray_case_presentation.py` is a 13-slide deck for the case interview:
stakeholder problem → data quality → methodology → dbt architecture → star schema and
SQL → findings → Power BI specification → limitations. It queries the marts read-only,
so every figure in the deck is live from the warehouse.

| File | Purpose |
|---|---|
| `notebooks/stingray_case_presentation.py` | the deck: data-prep cells plus one cell per slide |
| `notebooks/layouts/stingray_case_presentation.slides.json` | slides layout, slide types, speaker notes, deck settings |
| `notebooks/theme.css` | palette/typography, navy section slides, teal progress bar |
| `docs/stingray_case_presentation.pdf` | rendered handout (13 pages, 16:9) |

Paths in the app config are relative to the notebook, so keep `theme.css` and
`layouts/` next to it if you move it. Prerequisite: `uv run dbt build --profiles-dir .`
so `data/warehouse/stingray.duckdb` exists.

### Present

```bash
uv run marimo edit notebooks/stingray_case_presentation.py
```

Open the **app preview** (bottom-right) and pick **Slides** in the layout dropdown — the
saved layout is loaded automatically from `layouts/`. Enter browser fullscreen, then press
`F` for reveal fullscreen.

Keys while presenting: `←`/`→`/`Space` navigate · `S` speaker view (speaker notes) ·
`C` toggle code · `Esc` slide overview · `F` fullscreen.

Read-only app, with no editor UI:

```bash
uv run marimo run notebooks/stingray_case_presentation.py
```

The notebook opens DuckDB with `read_only=True`. Close it before `dbt build` — DuckDB
allows readers or one writer, not both.

### Export

Static, self-contained HTML including outputs, layout, theme and speaker notes:

```bash
uv run marimo export html notebooks/stingray_case_presentation.py -o /tmp/stingray_deck.html
```

`docs/stingray_case_presentation.pdf` is the rendered handout (one slide per page, 16:9).
It is produced from that HTML export with headless Chrome, so the custom theme and charts
match the live deck. Marimo's native slides PDF
(`uv run marimo export pdf notebooks/stingray_case_presentation.py -o deck.pdf --as=slides`)
needs `nbconvert` and Playwright — not project dependencies — and renders through
nbconvert rather than the deck HTML, so the navy section slides lose their CSS.

### Edit and extend

- Data loads/prep are `hide_code` cells; each slide is one cell that returns a `mo.vstack`.
- Slide types, deck settings and speaker notes are edited in the slides config sidebar of
  the app preview and saved back to `layouts/…slides.json`; slide order follows cell order
  (drag slides in the minimap to reorder the underlying cells).
- Adding or removing cells changes the number of layout entries; marimo warns when the
  layout no longer matches the notebook. Re-save the layout from the preview after
  structural edits.
- Validate without opening a browser: `uv run marimo check notebooks/`.

## Diagrams

Versioned Mermaid sources live in `docs/diagrams/`:

- `architecture.mmd` — layered architecture view (raw → staging → intermediate tracks → marts).
- `dag.mmd` — model-to-model DAG generated from `target/manifest.json` (`parent_map`), so it
  always matches what dbt actually resolved.

Render them to SVG (`-b transparent` keeps the background clean for slides and docs). With
`@mermaid-js/mermaid-cli` 12.x the width flag is `--size` (`-w` was removed):

```bash
npx -y @mermaid-js/mermaid-cli@latest -i docs/diagrams/architecture.mmd \
  -o docs/diagrams/architecture.svg -b transparent --size 2400

npx -y @mermaid-js/mermaid-cli@latest -i docs/diagrams/dag.mmd \
  -o docs/diagrams/dag.svg -b transparent --size 3200
```

On Linux hosts that block the Chromium sandbox (e.g. Ubuntu 23.10+ with AppArmor user-namespace
restrictions), add a puppeteer config such as `{"args": ["--no-sandbox"]}` via `-p <config.json>`.

The `.mmd` files are the versioned source of truth; the generated `.svg`/`.png` files are build
outputs. Regenerate `dag.mmd` after changing models (`uv run dbt docs generate --profiles-dir .`
refreshes `target/manifest.json` first).

## Intermediate models and grains

| Model | Grain | Rows | Purpose |
|---|---|---|---|
| `int_dates` | one row per local calendar date (`date_day`) | 14 | Central DST-aware date spine (UTC day boundaries, true day duration 1380/1440/1500 min). Source-driven range: activity dates ∪ storm-touched local dates. |
| `int_node_days_assigned` | one row per assigned node per calendar day (`node_id` × `activity_date`) | 63 | Attributes each node-day to the site/pen valid **on that date** (temporal assignment), keeps days without telemetry as null measures with `has_activity_record = false`. |
| `int_storm_daily_exposure` | one row per storm event per local calendar day (`storm_id` × `storm_date`) | 6 | Splits half-open storm intervals `[start, end)` into Europe/Oslo days using `int_dates` boundaries. |
| `int_site_daily_storm_summary` | one row per site per storm-affected day (`site_id` × `activity_date`) | 6 | Aggregates storm exposure to site-day so joining to pen activity never multiplies rows. `total_storm_minutes` is **cumulative event-minutes** — overlapping storms at one site would double-count shared time; no overlaps exist in the data and a warn test guards it. |
| `int_pen_daily_activity` | one row per site, pen, day (`site_id` × `pen_id` × `activity_date`) | 63 | Aggregates node-days to pen-days: expected/reported node days, summed measures, node set, node-set-change flag, reporting completeness. |
| `int_fish_counts_validated` | one row per farmer log entry (`log_id`) | 10 | Validation only: `is_fish_count_plausible`, `is_duplicate_pen_day`. Nothing removed or corrected. |
| `int_pen_daily_fish_count` | one row per pen per day from the pen's first log through the reporting period end (`pen_id` × `activity_date`) | 70 | Daily snapshot: latest entry on or before the date (tie-break: highest `log_id`), carried forward only while younger than `fish_count_max_age_days`; implausible latest entries withhold the snapshot instead of silently substituting an older value. |
| `int_storm_episodes` | one row per storm episode per site (`site_id` × `episode_started_at`) | 3 | Groups events at a site whose gap is strictly < `storm_episode_gap_hours` (24); gaps of exactly 24h start a new episode. Running-max gaps-and-islands (overlap/nesting safe). Episode span includes quiet gaps — never exposure. |
| `int_pen_storm_daily_analysis` | one row per pen, episode and local date in the window (`storm_episode_id` × `pen_id` × `activity_date`) | 39 | Before (3 dates) / during (episode dates, partially affected included) / after (3 dates) classification with pen activity, actual site-day storm minutes and rates. Pens included only while assigned at the episode's site. |
| `int_storm_pen_baselines` | one row per pen and episode (`storm_episode_id` × `pen_id`) | 5 | Before/during/after comparison: total shots / total uptime × 60 (never an average of daily rates), reporting completeness, percentage changes (null on zero/unavailable baselines). |

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

`uv run dbt build --profiles-dir .` → **347 tests (336 generic/singular + 11 unit), 346 pass, 1 warn, 0 errors.**
The single warn is the pre-existing staging plausibility check that flags P201's 1,852,000 entry
(deliberate). By layer: 48 generic/singular tests on staging, 151 on intermediate, 137 on marts,
plus the 11 unit tests on the temporal and fish-count edge cases.

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
  today).
- **Multi-site timezone lookup** — see `docs/limitations.md`.

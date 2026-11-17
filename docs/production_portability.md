# Portability limitations

**Status: this project is built, tested and supported on DuckDB only.** It has not been run on
Snowflake or Postgres. The notes below record each construct that would break and the equivalent
expression per engine, so a future port is a bounded change rather than a rewrite.

There are deliberately **no adapter-dispatch macros** today — that keeps the model SQL short and
readable. Portability was traded for brevity; see "If you need to port" at the end of this file.

## Non-portable constructs

| # | Where | DuckDB (current) | Postgres | Snowflake |
|---|---|---|---|---|
| 1 | `stg_stingray__storm_events.storm_started_at` / `storm_ended_at` | `timezone('UTC', cast(<col> as timestamptz))` | `cast(<col> as timestamptz) at time zone 'UTC'` | `convert_timezone('UTC', cast(<col> as timestamp_tz))::timestamp_ntz` |
| 2 | `stg_stingray__farmer_pen_logs.logged_at` | `timezone('UTC', timezone('<zone>', cast(log_ts as timestamp)))` | `cast(log_ts as timestamp) at time zone '<zone>' at time zone 'UTC'` | `convert_timezone('<zone>', 'UTC', cast(log_ts as timestamp_ntz))` |
| 3 | `stg_stingray__storm_events.storm_duration_hours` | `date_diff('second', a, b) / 3600.0` | `extract(epoch from (b - a)) / 3600.0` | `datediff('second', a, b) / 3600.0` |
| 4 | `stg_stingray__node_pen_assignments` | Select-list alias reuse: `coalesce(valid_to_date + 1, ...)` references the alias defined earlier in the same `SELECT` | Not allowed — compute `valid_to_date` in a CTE or subquery first | Not allowed — same |
| 5 | `_stingray__sources.yml` | `config.meta.external_location` with `read_csv('data/raw/{name}.csv', header = true, all_varchar = true)` | No equivalent; source must be a table | No equivalent; source must be a real table |
| 6 | `int_dates`, `int_node_days_assigned`, `int_pen_daily_fish_count`, `int_pen_storm_daily_analysis` | `generate_series(ts, ts, interval '1 day')` as a lateral (comma-join) table function | `generate_series` on timestamps works; wrap the lateral reference in explicit `LATERAL` where needed | `GENERATOR` cannot emit dates — use a date spine table or `dbt_utils.date_spine` |
| 7 | Intermediate/mart aggregates | `sum(x) filter (where ...)`, `count(*) filter (where ...)`, `avg(x) filter (where ...)`, `bool_or(x)` | `FILTER (WHERE ...)` is Postgres-native; `bool_or` exists as an aggregate | `SUM(CASE WHEN ... THEN x END)`, `COUNT_IF(...)`, `AVG(CASE WHEN ... THEN x END)`, `BOOLOR_AGG(x)` |
| 8 | `int_pen_daily_activity`, `dim_pen`, `int_fish_counts_validated` | `string_agg(x, ',' order by x)` and `string_agg(...) filter (where ...)` | `string_agg(x, ',' ORDER BY x)` (same name) | `LISTAGG(x, ',') WITHIN GROUP (ORDER BY x)`; conditional via `CASE` inside `LISTAGG` |
| 9 | `int_storm_episodes` | `to_hours(24)` interval arithmetic | `interval '24 hours'` / `make_interval(hours => 24)` | `DATEADD(hour, 24, ts)` or `ts + INTERVAL '24 hours'` |
| 10 | `dim_pen` | `arg_max(site_id, valid_from_date)` | No `arg_max`; use `DISTINCT ON` or a lateral subquery | `MAX_BY(site_id, valid_from_date)` |
| 11 | `dim_date` | `strftime(d, '%Y%m%d')`, `isodow(d)`, `weekofyear(d)`, `strftime(d, '%A')` | `to_char(d, 'YYYYMMDD')`, `extract(isodow from d)`, `extract(week from d)`, `to_char(d, 'Day')` | `TO_CHAR(d, 'YYYYMMDD')`, `DAYOFWEEKISO(d)`, `WEEKISO(d)`, `DAYNAME(d)` |
| 12 | `int_dates`, storm models | `timezone(tz, ts)` / `timezone('UTC', timestamptz)` round-trips | `ts AT TIME ZONE tz` / `ts AT TIME ZONE 'UTC'` | `CONVERT_TIMEZONE(tz, ts)` |

Items 1–3 are one-line function substitutions but have no common syntax: `timezone()` is DuckDB,
`AT TIME ZONE` is Postgres, `CONVERT_TIMEZONE` is Snowflake, and there is no single expression that
parses an offset-bearing string to naive UTC on all three.

Item 4 is why the assignments model cannot be both two CTEs and portable: naming the cast requires a
CTE on the other engines.

## What is portable already

- Casting, `trim`, `nullif`, `coalesce`, `is null`: plain SQL.
- Date arithmetic with integers (`date + 1` returns DATE in DuckDB, Postgres and Snowflake) and the
  `date '9999-12-31'` literal.
- `dbt_utils` tests (`accepted_range`, `unique_combination_of_columns`, `expression_is_true`,
  `mutually_exclusive_ranges`) and `generate_surrogate_key` — the package emits adapter-specific SQL.
- Unit tests with `format: sql` and the singular pen→site test.

## Sources on another engine

Delete the `meta.external_location` key and point the source at a real table
(`RAW.STINGRAY.<table>` on Snowflake). `all_varchar` has no counterpart because staging casts every
column explicitly — the raw-to-typed contract stays the same.

## Timezone data

`var('farmer_log_timezone')` = `Europe/Oslo` assumes `log_ts` is naive local wall time. All three
engines resolve IANA zone names, so the value itself ports; only the function wrapping it changes
(item 2). Multi-zone handling is out of scope — see `docs/limitations.md`.

## If you need to port

1. Add one macro file with three dispatchers (`duckdb__`, `postgres__`, `snowflake__`, plus a
   `default__` that raises): offset-string → UTC, local wall time → UTC, hours between timestamps.
2. Call them from the storm and farmer models; the model SQL then stays adapter-agnostic.
3. Split `stg_stingray__node_pen_assignments` into `typed` → `final` so the cast is named in a CTE.
4. Switch the source config from `external_location` to real tables.

Estimated size: one macro file (~35 lines), one model restructure, two model call-site edits, one
config change. Everything downstream (`fct_`/`dim_` models) is unaffected.

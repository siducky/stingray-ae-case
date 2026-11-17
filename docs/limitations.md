# Limitations and deliberate shortcuts

Scope decisions made for this build, what they cost, and what the next step would be. Ordered by
how much they can affect a result, not by how easy they are to fix.

| # | Limitation | Why it's acceptable now | Next step if it matters |
|---|---|---|---|
| 1 | **One timezone for farmer logs.** `var('farmer_log_timezone')` = `Europe/Oslo` is applied to every row. | All current farmers are in one zone, and `logged_at_local` is preserved, so nothing is lost — only the derived `logged_at` would be wrong if logs arrived from elsewhere. | Add a `site_timezones` lookup (site_id → IANA zone) and convert per row in the intermediate layer: `timezone('UTC', timezone(site_tz, logged_at_local))`. No staging change needed. |
| 2 | **`activity_date` day boundary assumed Europe/Oslo.** The source gives a date, not a timestamp, so the day's UTC start/end is inferred. | The case data is single-zone, so the boundary is consistent. | Make the zone explicit per site and derive `day_start_utc`/`day_end_utc` in the intermediate layer before matching storms. Add a sensitivity check on the ±1 day edge. |
| 3 | **Staging neither deduplicates nor filters.** P102's two logs on 2026-10-08 and P201's 1,852,000 count are kept; the count is flagged by a `warn` test, the double entry is not, because multiple logs per pen-day are legal. | Staging must stay 1:1 with the source; resolution is an analytical decision, not a cleaning one. | Latest-log-wins per pen/day (tested on the deduplicated model) and an outlier flag in the intermediate layer. |
| 4 | **Missing rows are not zero activity.** N05 2026-10-08 and N04 2026-10-12 are absent, not zero; N01/N03 have zero-uptime rows that look similar. | No aggregation happens yet, so nothing is silently mis-summed. | Build a node-day spine in the intermediate layer and left join activity; exclude zero-uptime days from rate denominators. |
| 5 | **DST edge cases are unresolvable from wall-clock input.** A time repeated during the autumn fall-back hour (e.g. 02:00–03:00 on 2026-10-25 in Oslo) maps to one offset only. | All current logs are between 05:52 and 14:47, so none fall in an ambiguous hour. | Capture the offset at entry time (ISO-8601 with `Z`/offset, as `storm_events` already does) and drop the inference. |
| 6 | **The zone is baked into a unit test.** `test_farmer_log_local_time_converted_to_utc_dst_aware` asserts Oslo offsets. | It is the guard that proves the conversion is DST-aware, not a fixed subtraction. | Update the two expected values whenever the configured zone changes; dbt skips the model if the test fails, so a mismatch cannot ship silently. |
| 7 | **No source freshness, contracts or incremental models.** CSVs are read in place with `all_varchar`. | Single local DuckDB file, one writer, full refresh in ~1.5 s. | Freshness/contracts on the source, and incremental materialisation for the fact table once volume justifies it. |
| 8 | **Single environment.** Built and tested on DuckDB only; Snowflake and Postgres are unexercised. | The case runs locally. | See `docs/production_portability.md` for the five non-portable constructs and their per-engine replacements. |

## What I deliberately did not build

A multi-timezone lookup, deduplication and a node-day spine are all *correct*, but with one zone, 10
log rows and 61 activity rows they add joins, seeds and tests without changing a single output value.
Naming the assumption and the migration path demonstrates the same understanding at a fraction of the
complexity — and keeps the effort where the case is judged: the storm-impact analysis.

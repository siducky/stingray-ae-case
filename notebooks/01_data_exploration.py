import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")

with app.setup:
    from pathlib import Path

    import duckdb

    con = duckdb.connect()

    raw_dir = Path("data/raw")
    raw_tables = {
        "farmer_pen_log": raw_dir / "farmer_pen_log.csv",
        "node_daily_activity": raw_dir / "node_daily_activity.csv",
        "node_pen_assignment": raw_dir / "node_pen_assignment.csv",
        "storm_events": raw_dir / "storm_events.csv",
    }

    for table, path in raw_tables.items():
        con.execute(
            f"create or replace view {table} as "
            f"select * from read_csv_auto('{path.as_posix()}', header = true)"
        )


@app.cell(hide_code=True)
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def header(mo):
    mo.md("""
    # Data Exploration

    ### Notebook for exploratory data analysis for the Stingray AE case

    Raw CSVs are exposed as DuckDB views, so you can query them with
    plain SQL in any marimo SQL cell.
    """)


@app.cell
def overview(mo):
    summary = con.sql("show tables").df()
    counts = con.sql(
        " union all ".join(
            f"select '{table}' as table_name, count(*) as row_count from {table}"
            for table in summary["name"]
        )
        + " order by table_name"
    ).df()
    mo.vstack(
        [
            mo.md("## Raw tables loaded"),
            mo.ui.table(counts, selection=None),
        ]
    )


@app.cell(hide_code=True)
def picker(mo):
    table_ui = mo.ui.dropdown(
        options=sorted(raw_tables.keys()),
        value="farmer_pen_log",
        label="View raw table",
    )
    table_ui  # noqa: B018  # trailing expression renders the widget
    return (table_ui,)


@app.cell
def preview(mo, table_ui):
    mo.ui.table(con.sql(f"select * from {table_ui.value}").df(), selection=None)


@app.cell(hide_code=True)
def table_summaries(mo):
    def scalar(query: str):
        return con.sql(query).fetchall()[0][0]

    def fmt_date(value, pattern: str = "%Y-%m-%d") -> str:
        return value.strftime(pattern) if value is not None else "—"

    def row_count(table: str) -> int:
        return scalar(f"select count(*) from {table}")

    def coverage_bounds(
        table: str,
        start_column: str,
        end_column: str,
        *,
        with_time: bool = False,
    ) -> tuple[str, str]:
        start, end = con.sql(
            f"select min({start_column}), max({end_column}) from {table}"
        ).fetchall()[0]
        pattern = "%Y-%m-%d %H:%M" if with_time else "%Y-%m-%d"
        return fmt_date(start, pattern), fmt_date(end, pattern)

    def missing_values(table: str, columns: list[str]) -> str:
        total = row_count(table)
        counts = con.sql(
            f"select {', '.join(f'count(*) - count({column})' for column in columns)} "
            f"from {table}"
        ).fetchall()[0]
        details = [
            f"{column} blank in {count} of {total} rows ({count / total:.0%})"
            for column, count in zip(columns, counts, strict=True)
            if count
        ]
        return "; ".join(details) if details else "none"

    def describe_key(values: tuple) -> str:
        """Render key values as 'P102 on 2026-10-08' instead of 'P102, 2026-10-08'."""
        text = fmt_date(values[0]) if hasattr(values[0], "strftime") else str(values[0])
        for value in values[1:]:
            if hasattr(value, "strftime"):
                text += f" on {fmt_date(value)}"
            else:
                text += f", {value}"
        return text

    def duplicates(
        table: str,
        keys: list[str],
        *,
        detail_column: str | None = None,
    ) -> str:
        key_aliases = [f"key_{index}" for index in range(len(keys))]
        alias_select = ", ".join(
            f"{key} as {alias}" for key, alias in zip(keys, key_aliases, strict=True)
        )
        alias_list = ", ".join(key_aliases)
        grouped = f"""
            select {alias_select}, count(*) as record_count
            from {table}
            group by {", ".join(keys)}
            having count(*) > 1
        """
        groups, extra = con.sql(
            f"select count(*), coalesce(sum(record_count - 1), 0) from ({grouped})"
        ).fetchall()[0]
        if extra == 0:
            return "none"
        *key_values, row_total = con.sql(
            f"select {alias_list}, record_count from ({grouped}) "
            f"order by record_count desc, {alias_list} limit 1"
        ).fetchall()[0]
        message = f"{describe_key(tuple(key_values))} has {row_total} rows"
        if groups > 1:
            message += f" (worst of {groups} duplicate keys)"
        if detail_column:
            where_clause = " and ".join(f"{key} = ?" for key in keys)
            detail_values = con.sql(
                f"select string_agg({detail_column}::varchar, ', ' "
                f"order by {detail_column}) from {table} where {where_clause}",
                params=list(key_values),
            ).fetchall()[0][0]
            message += f" ({detail_column} {detail_values})"
        return message

    def high_outliers(table: str, column: str) -> str:
        q1, q3, median_value = con.sql(
            f"select quantile_cont({column}, 0.25), quantile_cont({column}, 0.75), "
            f"median({column}) from {table}"
        ).fetchall()[0]
        threshold = q3 + 3 * (q3 - q1)
        count = scalar(f"select count(*) from {table} where {column} > {threshold}")
        if count == 0:
            return "none"
        maximum = scalar(f"select max({column}) from {table}")
        plural = "s" if count > 1 else ""
        return (
            f"{count} extreme value{plural}: max {maximum:,.0f} "
            f"vs median {median_value:,.0f}"
        )

    activity_gaps = con.sql(
        """
        select
            node_id,
            date_diff('day', min(activity_date), max(activity_date)) + 1 - count(*)
        from node_daily_activity
        group by node_id
        having date_diff('day', min(activity_date), max(activity_date)) + 1 > count(*)
        order by node_id
        """
    ).fetchall()
    gap_details = "; ".join(
        f"{node_id} misses {missing} day{'s' if missing > 1 else ''}"
        for node_id, missing in activity_gaps
    )

    series_days = scalar(
        "select date_diff('day', min(activity_date), max(activity_date)) + 1 "
        "from node_daily_activity"
    )
    early_stops = con.sql(
        """
        select
            node_id,
            max(activity_date) as last_activity_date,
            date_diff('day', min(activity_date), max(activity_date)) + 1 as span_days
        from node_daily_activity
        group by node_id
        having max(activity_date) < (
            select max(activity_date) from node_daily_activity
        )
        order by node_id
        """
    ).fetchall()
    early_stop_details = "; ".join(
        f"{node_id} stops on {fmt_date(last_date)} ({span_days} of {series_days} days)"
        for node_id, last_date, span_days in early_stops
    )
    missing_dates = (
        "; ".join(part for part in (gap_details, early_stop_details) if part) or "none"
    )

    assignment_start = scalar("select min(valid_from) from node_pen_assignment")
    open_assignments = scalar(
        "select count(*) from node_pen_assignment where valid_to is null"
    )
    assignment_end = (
        "present"
        if open_assignments
        else fmt_date(scalar("select max(valid_to) from node_pen_assignment"))
    )
    assignment_missing = missing_values(
        "node_pen_assignment",
        ["node_id", "site_id", "pen_id", "valid_from", "valid_to"],
    )
    if open_assignments:
        assignment_missing += " — the node is still deployed"

    log_gaps = con.sql(
        """
        select string_agg(previous_log_id + 1 || '–' || (log_id - 1), ', ')
        from (
            select
                log_id,
                lag(log_id) over (order by log_id) as previous_log_id
            from farmer_pen_log
        )
        where log_id - previous_log_id > 1
        """
    ).fetchall()[0][0]
    log_date_count = scalar("select count(distinct log_ts::date) from farmer_pen_log")
    log_dates = con.sql(
        """
        select string_agg(log_date, ', ' order by log_date)
        from (
            select distinct strftime(log_ts, '%Y-%m-%d') as log_date
            from farmer_pen_log
        )
        """
    ).fetchall()[0][0]
    farmer_gaps = f"only {log_date_count} log dates ({log_dates})"
    if log_gaps:
        farmer_gaps += f"; log ids {log_gaps} absent"

    non_positive_counts = scalar(
        "select count(*) from farmer_pen_log where fish_count <= 0"
    )
    farmer_validity = (
        "none — every fish_count is positive"
        if non_positive_counts == 0
        else f"{non_positive_counts} of {row_count('farmer_pen_log')} rows "
        "have fish_count <= 0"
    )

    invalid_uptime = scalar(
        "select count(*) from node_daily_activity "
        "where uptime_minutes not between 0 and 1440"
    )
    negative_counts = scalar(
        "select count(*) from node_daily_activity "
        "where shots_fired < 0 or lice_detections < 0"
    )
    activity_problems = []
    if invalid_uptime:
        activity_problems.append(
            f"{invalid_uptime} rows with uptime outside 0–1440 minutes"
        )
    if negative_counts:
        activity_problems.append(f"{negative_counts} rows with negative counts")
    activity_validity = (
        "; ".join(activity_problems)
        if activity_problems
        else "none — uptime stays within 0–1440 minutes and no counts are negative"
    )

    reversed_assignments = scalar(
        "select count(*) from node_pen_assignment where valid_to < valid_from"
    )
    overlapping_assignments = scalar(
        """
        select count(*)
        from node_pen_assignment as earlier
        inner join node_pen_assignment as later
            on earlier.node_id = later.node_id
            and earlier.valid_from < later.valid_from
            and earlier.valid_from < coalesce(later.valid_to, date '9999-12-31')
            and coalesce(earlier.valid_to, date '9999-12-31') > later.valid_from
        """
    )
    assignment_problems = []
    if reversed_assignments:
        assignment_problems.append(
            f"{reversed_assignments} intervals end before they start"
        )
    if overlapping_assignments:
        assignment_problems.append(
            f"{overlapping_assignments} overlapping intervals for the same node"
        )
    assignment_validity = (
        "; ".join(assignment_problems)
        if assignment_problems
        else "none — no interval ends before it starts and none overlap"
    )

    reversed_storms = scalar(
        "select count(*) from storm_events where end_ts <= start_ts"
    )
    invalid_severities = scalar(
        """
        select count(*) from storm_events
        where severity not in ('low', 'moderate', 'high')
        """
    )
    storm_problems = []
    if reversed_storms:
        storm_problems.append(f"{reversed_storms} storms end before they start")
    if invalid_severities:
        storm_problems.append(
            f"{invalid_severities} severities outside low/moderate/high"
        )
    storm_validity = (
        "; ".join(storm_problems)
        if storm_problems
        else "none — every storm ends after it starts and severity is valid"
    )

    activity_outliers = (
        "; ".join(
            f"{label} — {value}"
            for label, value in (
                ("shots", high_outliers("node_daily_activity", "shots_fired")),
                ("uptime", high_outliers("node_daily_activity", "uptime_minutes")),
            )
            if value != "none"
        )
        or "none"
    )

    log_first, log_last = coverage_bounds(
        "farmer_pen_log", "log_ts", "log_ts", with_time=True
    )
    activity_first, activity_last = coverage_bounds(
        "node_daily_activity", "activity_date", "activity_date"
    )
    storm_first, storm_last = coverage_bounds(
        "storm_events",
        "start_ts at time zone 'utc'",
        "end_ts at time zone 'utc'",
        with_time=True,
    )

    summaries = [
        {
            "table": "farmer_pen_log",
            "rows": row_count("farmer_pen_log"),
            "first_observation_date": log_first,
            "last_observation_date": log_last,
            "unique_entities": (
                f"{scalar('select count(distinct pen_id) from farmer_pen_log')} pens"
            ),
            "missing_values": missing_values(
                "farmer_pen_log", ["fish_count", "entered_by", "comment"]
            ),
            "duplicate_records": duplicates(
                "farmer_pen_log",
                ["pen_id", "log_ts::date"],
                detail_column="log_id",
            ),
            "missing_dates": farmer_gaps,
            "outliers": high_outliers("farmer_pen_log", "fish_count"),
            "validity": farmer_validity,
        },
        {
            "table": "node_daily_activity",
            "rows": row_count("node_daily_activity"),
            "first_observation_date": activity_first,
            "last_observation_date": activity_last,
            "unique_entities": (
                f"{scalar('select count(distinct node_id) from node_daily_activity')} "
                "nodes"
            ),
            "missing_values": missing_values(
                "node_daily_activity",
                ["lice_detections", "shots_fired", "uptime_minutes"],
            ),
            "duplicate_records": duplicates(
                "node_daily_activity", ["node_id", "activity_date"]
            ),
            "missing_dates": missing_dates,
            "outliers": activity_outliers,
            "validity": activity_validity,
        },
        {
            "table": "node_pen_assignment",
            "rows": row_count("node_pen_assignment"),
            "first_observation_date": fmt_date(assignment_start),
            "last_observation_date": assignment_end,
            "unique_entities": (
                f"{scalar('select count(distinct pen_id) from node_pen_assignment')} "
                "pens"
            ),
            "missing_values": assignment_missing,
            "duplicate_records": duplicates(
                "node_pen_assignment", ["node_id", "valid_from"]
            ),
            "missing_dates": "n/a (interval table)",
            "outliers": "none",
            "validity": assignment_validity,
        },
        {
            "table": "storm_events",
            "rows": row_count("storm_events"),
            "first_observation_date": f"{storm_first} UTC",
            "last_observation_date": f"{storm_last} UTC",
            "unique_entities": (
                f"{scalar('select count(distinct site_id) from storm_events')} sites"
            ),
            "missing_values": missing_values(
                "storm_events",
                ["storm_id", "site_id", "start_ts", "end_ts", "severity"],
            ),
            "duplicate_records": duplicates("storm_events", ["storm_id"]),
            "missing_dates": "n/a (event table)",
            "outliers": high_outliers(
                "storm_events", "date_diff('second', start_ts, end_ts) / 3600.0"
            ),
            "validity": storm_validity,
        },
    ]

    grains = {
        "farmer_pen_log": "One row per fish-count log entry",
        "node_daily_activity": "One row per node per day",
        "node_pen_assignment": "One row per node deployment interval",
        "storm_events": "One row per storm event per site",
    }
    by_table = {row["table"]: row for row in summaries}
    farmer_outlier_max = scalar("select max(fish_count) from farmer_pen_log")

    characteristics = [
        {
            "table": row["table"],
            "grain": grains[row["table"]],
            "rows": row["rows"],
            "first_observation_date": row["first_observation_date"],
            "last_observation_date": row["last_observation_date"],
            "unique_entities": row["unique_entities"],
        }
        for row in summaries
    ]

    quality = [
        {
            "Table": row["table"],
            "Missing_values": row["missing_values"],
            "Duplicate_records": row["duplicate_records"],
            "invalid_values": (
                f"{row['validity']}; outlier — {row['outliers']}"
                if row["outliers"] != "none"
                else row["validity"]
            ),
            "temporal_gaps": row["missing_dates"],
        }
        for row in summaries
    ]

    move_rows = con.sql(
        """
        select node_id, pen_id, valid_from
        from node_pen_assignment
        where node_id in (
            select node_id from node_pen_assignment group by node_id having count(*) > 1
        )
        order by node_id, valid_from
        """
    ).fetchall()
    moves: dict[str, list[tuple[str, object]]] = {}
    for node_id, pen_id, valid_from in move_rows:
        moves.setdefault(node_id, []).append((pen_id, valid_from))
    move_details = "; ".join(
        f"{node_id} moved {' → '.join(pen for pen, _ in assignments)} "
        f"on {fmt_date(assignments[-1][1])}"
        for node_id, assignments in moves.items()
    )

    zero_uptime: dict[str, list[str]] = {}
    for node_id, activity_date in con.sql(
        """
        select node_id, activity_date
        from node_daily_activity
        where uptime_minutes = 0
        order by node_id, activity_date
        """
    ).fetchall():
        zero_uptime.setdefault(node_id, []).append(fmt_date(activity_date))
    zero_uptime_text = "; ".join(
        f"{node_id} on {', '.join(days)}" for node_id, days in zero_uptime.items()
    )
    move_note = move_details or "no node ever changed pen"

    longest_storm_id, longest_start, longest_end = con.sql(
        """
        select storm_id, start_ts, end_ts
        from storm_events
        order by date_diff('second', start_ts, end_ts) desc
        limit 1
        """
    ).fetchall()[0]
    fish_median = scalar("select median(fish_count) from farmer_pen_log")
    farmer_blanks = scalar("select count(*) from farmer_pen_log where comment is null")
    farmer_rows = row_count("farmer_pen_log")

    activity_transform = (
        f"The table only has rows where data was logged — {missing_dates}. "
        "Create one row per node per day first, then left join activity, so a "
        "missing day stays blank instead of becoming 0."
    )
    if zero_uptime_text:
        activity_transform += (
            f" Drop zero-uptime days ({zero_uptime_text}) before computing "
            "per-minute rates."
        )

    implications = [
        {
            "table": "farmer_pen_log",
            "joins": (
                "Keep one log per pen per day before joining counts: "
                f"{by_table['farmer_pen_log']['duplicate_records']}. Use the later "
                "log (the 'corrected count'), or P102's count is added twice."
            ),
            "transformations": (
                "log_ts has no timezone while storm_events is stored as +02:00. "
                "Confirm which zone log_ts is in, convert both to UTC, then compare "
                f"times. Leave comment empty where unknown — {farmer_blanks} of "
                f"{farmer_rows} rows have none."
            ),
            "metrics": (
                f"Leave the {farmer_outlier_max:,.0f} count out of averages — it is "
                f"{farmer_outlier_max / fish_median:.0f}x the median of "
                f"{fish_median:,.0f}. Treat log_id as an identifier only, not as a "
                "count of events."
            ),
        },
        {
            "table": "node_daily_activity",
            "joins": (
                "Attach the pen that was active on each day: join on node_id and "
                "activity_date between valid_from and valid_to. Joining on node_id "
                f"alone duplicates every day of a moved node — {move_note}."
            ),
            "transformations": activity_transform,
            "metrics": (
                "Divide shots and detections by the minutes the node was actually up, "
                "not by a flat 1,440, on days with partial uptime. For storms, flag "
                "each node-day as before, during or after the storm at its site."
            ),
        },
        {
            "table": "node_pen_assignment",
            "joins": (
                "This is the lookup from node-days to pens: join on node_id plus a "
                f"date inside valid_from → valid_to. {move_note}, so one node_id "
                "can point at two pens."
            ),
            "transformations": (
                f"valid_to is null in {open_assignments} of "
                f"{row_count('node_pen_assignment')} rows and means 'still active'. "
                "Replace nulls with a far-future date (e.g. 9999-12-31) or "
                "current_date so the date-range join needs no special case."
            ),
            "metrics": (
                "Credit each node-day to the pen active that day; never total a node "
                "across its pens, or those days are counted under both."
            ),
        },
        {
            "table": "storm_events",
            "joins": (
                "Match storms to node-days on site_id plus overlapping time: a day is "
                "'during' a storm when the storm starts before the day ends and ends "
                f"after the day starts. {longest_storm_id} runs "
                f"{fmt_date(longest_start, '%Y-%m-%d %H:%M')} → "
                f"{fmt_date(longest_end, '%Y-%m-%d %H:%M')}, so matching on a single "
                "date would tag only its first day."
            ),
            "transformations": (
                "start_ts and end_ts carry +02:00 offsets, unlike the naive log_ts. "
                "Convert both to UTC before comparing, and derive duration as "
                "end_ts - start_ts."
            ),
            "metrics": (
                f"Only {by_table['storm_events']['rows']} storms across "
                f"{scalar('select count(distinct site_id) from storm_events')} sites — "
                "report before/during/after uptime and shots descriptively rather "
                "than testing for significance."
            ),
        },
    ]

    mo.vstack(
        [
            mo.md("## Table summaries"),
            mo.md("""
            ### Data characteristics

            Row counts, date ranges, unique entities and table grains.
            """),
            mo.ui.table(characteristics, selection=None),
            mo.md("""
            ### Data quality

            Missing values, duplicates, invalid values and temporal gaps.
            Each cell names the offending rows or columns; `none` means the
            check found nothing.
            """),
            mo.ui.table(quality, selection=None),
            mo.md("""
            ### Engineering implications

            How findings influence joins, transformations and metric calculations.
            """),
            mo.ui.table(implications, selection=None),
        ]
    )


@app.cell
def eda_coverage(mo):
    _sql = """
    select
        node_id,
        count(*) as rows,
        min(activity_date) as first_obs_date,
        max(activity_date) as last_obs_date,
        date_diff('day', min(activity_date), max(activity_date)) + 1 as days_active,
        date_diff('day', min(activity_date), max(activity_date)) + 1
            - count(*) as missing_days,
        round(
            100.0 * count(*)
            / (date_diff('day', min(activity_date), max(activity_date)) + 1),
            2
        ) as coverage_pct
    from node_daily_activity
    group by node_id
    order by node_id
    """
    mo.vstack(
        [
            mo.md("## Time-series coverage"),
            mo.ui.table(con.sql(_sql).df(), selection=None),
        ]
    )


@app.cell(hide_code=True)
def eda_by_node(mo):
    _sql = """
    select
        node_id,
        count(*) as days,
        count(*) filter (where uptime_minutes = 0) as days_full_downtime,
        count(*) filter (where uptime_minutes > 0 and uptime_minutes < 1440)
            as days_partial_downtime,
        sum(1440 - uptime_minutes) as total_downtime_minutes,
        round(100.0 * sum(uptime_minutes) / (count(*) * 1440), 2) as pct_uptime,
        round(avg(uptime_minutes), 2) as avg_daily_uptime_minutes,
        round(avg(lice_detections), 2) as lice_mean,
        round(avg(shots_fired), 2) as shots_fired_mean
    from node_daily_activity
    group by node_id
    order by node_id
    """
    mo.vstack(
        [
            mo.md("## Per-node activity stats"),
            mo.ui.table(con.sql(_sql).df(), selection=None),
        ]
    )


@app.cell(hide_code=True)
def eda_findings(mo):
    mo.md("""
    ## Data-quality findings

    - **`farmer_pen_log` log 1014**: `fish_count` = 1,852,000 vs a median of 170,000 — ~11x the typical count, likely a data-entry error. Flag before aggregating.
    - **Missing log IDs**: 1006–1010 are absent (sequence jumps 1005 → 1011). Confirm deleted vs. not exported.
    - **Duplicate pen/date logs**: P102 has two entries on 2026-10-08 (1012 at 08:16, 1013 at 14:47 "corrected count"). Adopt a latest-wins rule.
    - **`comment`**: null in 7 of 10 rows (70%).
    - **`node_daily_activity` coverage**: N03 stops 2026-10-07 (matches its `valid_to`); N04 and N05 each miss one day in their 14-day span.
    - **Zero uptime**: N01 on 2026-10-06; N03 on 2026-10-06 and 2026-10-07 — all inside storm ST-0041 (S01, Oct 5–7).
    - **`node_pen_assignment`**: N05 has two rows (P202 → P103 on 2026-10-08); `valid_to` is null in 4 of 6 rows, meaning "current".
    - **Timezone**: `storm_events` timestamps are UTC; `farmer_pen_log.log_ts` is naive. Confirm the log timezone before joining.
    """)


if __name__ == "__main__":
    app.run()

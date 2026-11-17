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
    return


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
    return


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
    return


@app.cell(hide_code=True)
def table_summaries(mo):
    def scalar(query: str):
        return con.sql(query).fetchall()[0][0]

    def fmt_date(value, pattern: str = "%Y-%m-%d") -> str:
        return value.strftime(pattern) if value is not None else "—"

    def row_count(table: str) -> int:
        return scalar(f"select count(*) from {table}")

    def coverage(
        table: str,
        start_column: str,
        end_column: str,
        *,
        with_time: bool = False,
    ) -> str:
        start, end = con.sql(
            f"select min({start_column}), max({end_column}) from {table}"
        ).fetchall()[0]
        pattern = "%Y-%m-%d %H:%M" if with_time else "%Y-%m-%d"
        return f"{fmt_date(start, pattern)} → {fmt_date(end, pattern)}"

    def missing_values(table: str, columns: list[str]) -> str:
        total = row_count(table)
        counts = con.sql(
            f"select {', '.join(f'count(*) - count({column})' for column in columns)} "
            f"from {table}"
        ).fetchall()[0]
        details = [
            f"{column}: {count} ({count / total:.0%})"
            for column, count in zip(columns, counts, strict=True)
            if count
        ]
        return ", ".join(details) if details else "none"

    def duplicates(table: str, keys: list[str]) -> str:
        key_list = ", ".join(keys)
        groups, extra = con.sql(
            f"""
            select count(*), coalesce(sum(record_count - 1), 0)
            from (
                select {key_list}, count(*) as record_count
                from {table}
                group by {key_list}
                having count(*) > 1
            )
            """
        ).fetchall()[0]
        return f"{extra} extra row(s) across {groups} key(s)" if extra else "none"

    def high_outliers(table: str, column: str) -> str:
        q1, q3 = con.sql(
            f"select quantile_cont({column}, 0.25), quantile_cont({column}, 0.75) "
            f"from {table}"
        ).fetchall()[0]
        threshold = q3 + 3 * (q3 - q1)
        count = scalar(f"select count(*) from {table} where {column} > {threshold}")
        if count == 0:
            return "none"
        maximum = scalar(f"select max({column}) from {table}")
        return f"{count} high (max {maximum:,.0f})"

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
    gap_count = sum(missing for _, missing in activity_gaps)
    gap_details = ", ".join(
        f"{node_id}: {missing}" for node_id, missing in activity_gaps
    )
    missing_dates = f"{gap_count} gap(s) ({gap_details})" if gap_count else "none"

    early_stops = con.sql(
        """
        select node_id, max(activity_date) as last_activity_date
        from node_daily_activity
        group by node_id
        having max(activity_date) < (
            select max(activity_date) from node_daily_activity
        )
        order by node_id
        """
    ).fetchall()
    early_stop_details = ", ".join(
        f"{node_id} ends {fmt_date(last_date)}" for node_id, last_date in early_stops
    )
    if early_stop_details:
        missing_dates += f"; {early_stop_details}"

    assignment_start = scalar("select min(valid_from) from node_pen_assignment")
    open_assignments = scalar(
        "select count(*) from node_pen_assignment where valid_to is null"
    )
    assignment_missing = missing_values(
        "node_pen_assignment",
        ["node_id", "site_id", "pen_id", "valid_from", "valid_to"],
    )
    if open_assignments:
        assignment_missing += " — null valid_to means current"

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
    farmer_validity = (
        f"{scalar('select count(*) from farmer_pen_log where fish_count <= 0')} "
        "non-positive fish_count"
    )
    if log_gaps:
        farmer_validity += f"; log_id gap {log_gaps}"

    invalid_uptime = scalar(
        "select count(*) from node_daily_activity "
        "where uptime_minutes not between 0 and 1440"
    )
    negative_counts = scalar(
        "select count(*) from node_daily_activity "
        "where shots_fired < 0 or lice_detections < 0"
    )
    activity_validity = (
        f"{invalid_uptime} invalid uptime; {negative_counts} negative counts"
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
    assignment_validity = (
        f"{reversed_assignments} reversed intervals; {overlapping_assignments} overlaps"
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
    storm_validity = (
        f"{reversed_storms} reversed intervals; {invalid_severities} invalid severities"
    )

    summaries = [
        {
            "table": "farmer_pen_log",
            "rows": row_count("farmer_pen_log"),
            "date_coverage": coverage(
                "farmer_pen_log", "log_ts", "log_ts", with_time=True
            ),
            "unique_entities": (
                f"{scalar('select count(distinct pen_id) from farmer_pen_log')} pens"
            ),
            "missing_values": missing_values(
                "farmer_pen_log", ["fish_count", "entered_by", "comment"]
            ),
            "duplicate_records": duplicates(
                "farmer_pen_log", ["pen_id", "log_ts::date"]
            ),
            "missing_dates": "n/a (event log)",
            "outliers": high_outliers("farmer_pen_log", "fish_count"),
            "validity": farmer_validity,
        },
        {
            "table": "node_daily_activity",
            "rows": row_count("node_daily_activity"),
            "date_coverage": coverage(
                "node_daily_activity", "activity_date", "activity_date"
            ),
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
            "outliers": (
                f"shots: {high_outliers('node_daily_activity', 'shots_fired')}; "
                f"uptime: {high_outliers('node_daily_activity', 'uptime_minutes')}"
            ),
            "validity": activity_validity,
        },
        {
            "table": "node_pen_assignment",
            "rows": row_count("node_pen_assignment"),
            "date_coverage": (
                f"{fmt_date(assignment_start)} → present "
                f"({open_assignments} open-ended)"
            ),
            "unique_entities": (
                f"{scalar('select count(distinct node_id) from node_pen_assignment')} "
                "nodes"
            ),
            "missing_values": assignment_missing,
            "duplicate_records": duplicates(
                "node_pen_assignment", ["node_id", "valid_from"]
            ),
            "missing_dates": "n/a (interval table)",
            "outliers": "n/a",
            "validity": assignment_validity,
        },
        {
            "table": "storm_events",
            "rows": row_count("storm_events"),
            "date_coverage": coverage(
                "storm_events",
                "start_ts at time zone 'utc'",
                "end_ts at time zone 'utc'",
                with_time=True,
            )
            + " UTC",
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
    outlier_labels = {
        "farmer_pen_log": "fish_count",
        "node_daily_activity": "activity",
        "storm_events": "duration",
    }
    by_table = {row["table"]: row for row in summaries}
    farmer_outlier_max = scalar("select max(fish_count) from farmer_pen_log")

    characteristics = [
        {
            "table": row["table"],
            "grain": grains[row["table"]],
            "rows": row["rows"],
            "date_coverage": row["date_coverage"],
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
                row["validity"]
                if row["outliers"] == "n/a"
                else f"{row['validity']}; "
                f"{outlier_labels[row['table']]} outliers — {row['outliers']}"
            ),
            "temporal_gaps": row["missing_dates"],
        }
        for row in summaries
    ]

    moved_nodes = [
        node_id
        for (node_id,) in con.sql(
            """
            select node_id
            from node_pen_assignment
            group by node_id
            having count(*) > 1
            order by node_id
            """
        ).fetchall()
    ]
    moved_text = ", ".join(moved_nodes) if moved_nodes else "none"

    implications = [
        {
            "table": "farmer_pen_log",
            "joins": (
                "Deduplicate to the latest log per pen/date before joining "
                f"fish counts ({by_table['farmer_pen_log']['duplicate_records']}); "
                "otherwise counts double."
            ),
            "transformations": (
                "Confirm the naive log_ts timezone and convert to UTC before "
                "storm joins; keep comment nullable."
            ),
            "metrics": (
                "Flag/exclude fish_count values above the 3×IQR fence "
                f"(current max {farmer_outlier_max:,.0f}) from averages; "
                "do not use log_id sequence as an event count."
            ),
        },
        {
            "table": "node_daily_activity",
            "joins": (
                "As-of join to node_pen_assignment on activity_date between "
                "valid_from and valid_to (null valid_to = open-ended)."
            ),
            "transformations": (
                "Build a per-node date spine and left join activity so missing "
                "days stay missing, not zero; exclude zero-uptime days from "
                "active-rate denominators."
            ),
            "metrics": (
                "Compute shots/detections per active minute when uptime < 1440; "
                "compare before/during/after storms using interval overlap."
            ),
        },
        {
            "table": "node_pen_assignment",
            "joins": (
                "Use an interval join for node → pen/site; nodes with multiple "
                f"assignments: {moved_text}, so node → pen is not one-to-one."
            ),
            "transformations": (
                "Coalesce null valid_to to an open-ended sentinel "
                "(e.g. date '9999-12-31') or current_date."
            ),
            "metrics": (
                "Attribute node-days to the pen/site active on that date; do not "
                "aggregate a node across multiple pens."
            ),
        },
        {
            "table": "storm_events",
            "joins": (
                "Join to node-days/events on site_id plus interval overlap "
                "(start_ts < window_end and end_ts > window_start), not date "
                "equality."
            ),
            "transformations": (
                "Normalize storm timestamps to UTC and confirm the farmer log "
                "timezone; derive storm_duration_hours as end_ts - start_ts."
            ),
            "metrics": (
                "Use before/during/after flags per node-day; with only "
                f"{by_table['storm_events']['rows']} storms, keep comparisons "
                "descriptive and avoid strong inference."
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
            """),
            mo.ui.table(quality, selection=None),
            mo.md("""
            ### Engineering implications

            How findings influence joins, transformations and metric calculations.
            """),
            mo.ui.table(implications, selection=None),
        ]
    )
    return


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
    return


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
        round(median(lice_detections), 2) as lice_median,
        round(stddev_samp(lice_detections), 2) as lice_std,
        round(avg(shots_fired), 2) as shots_fired_mean,
        median(shots_fired) as shots_fired_median
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
    return


@app.cell(hide_code=True)
def eda_findings(mo):
    mo.md("""
    ## Data-quality findings

    - **`farmer_pen_log` log 1014**: `fish_count` = 1,852,000 vs a median of 171,100 — ~10x peer values, likely a data-entry error. Flag before aggregating.
    - **Missing log IDs**: 1006–1010 are absent (sequence jumps 1005 → 1011). Confirm deleted vs. not exported.
    - **Duplicate pen/date logs**: P102 has two entries on 2026-10-08 (1012 at 08:16, 1013 at 14:47 "corrected count"). Adopt a latest-wins rule.
    - **`comment`**: null in 7 of 10 rows (70%).
    - **`node_daily_activity` coverage**: N03 stops 2026-10-07 (matches its `valid_to`); N04 and N05 each miss one day in their 14-day span.
    - **Zero uptime**: N01 on 2026-10-06; N03 on 2026-10-06 and 2026-10-07 — all inside storm ST-0041 (S01, Oct 5–7).
    - **`node_pen_assignment`**: N05 has two rows (P202 → P103 on 2026-10-08); `valid_to` is null in 4 of 6 rows, meaning "current".
    - **Timezone**: `storm_events` timestamps are UTC; `farmer_pen_log.log_ts` is naive. Confirm the log timezone before joining.
    """)
    return


if __name__ == "__main__":
    app.run()

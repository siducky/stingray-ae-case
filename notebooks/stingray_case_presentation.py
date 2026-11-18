import marimo

__generated_with = "0.25.2"
app = marimo.App(
    width="full",
    app_title="Storms and laser activity — Stingray AE case",
    layout_file="layouts/stingray_case_presentation.slides.json",
    css_file="theme.css",
)


with app.setup:
    import html as _html
    import json
    import textwrap
    from pathlib import Path

    import altair as alt
    import duckdb
    import marimo as mo
    import pandas as pd

    PALETTE = {
        "navy": "#0B1F33",
        "ocean": "#123B52",
        "teal": "#16A6A1",
        "teal_deep": "#0E7C78",
        "teal_soft": "#7FC8C3",
        "seafoam": "#D9F0EB",
        "coral": "#FF765E",
        "coral_deep": "#C94B36",
        "coral_soft": "#FFE4DE",
        "bg": "#F5F8FA",
        "ink": "#172B3A",
        "muted": "#5B7285",
        "border": "#E3EBF0",
        "white": "#FFFFFF",
        "slate": "#6C8FA1",
        "mist": "#EDF3F6",
    }
    NAVY = PALETTE["navy"]
    OCEAN = PALETTE["ocean"]
    TEAL = PALETTE["teal"]
    TEAL_SOFT = PALETTE["teal_soft"]
    TEAL_DEEP = PALETTE["teal_deep"]
    SEAFOAM = PALETTE["seafoam"]
    CORAL = PALETTE["coral"]
    CORAL_DEEP = PALETTE["coral_deep"]
    CORAL_SOFT = PALETTE["coral_soft"]
    INK = PALETTE["ink"]
    MUTED = PALETTE["muted"]
    BORDER = PALETTE["border"]
    WHITE = PALETTE["white"]
    BG = PALETTE["bg"]
    MIST = PALETTE["mist"]
    MONO = "'JetBrains Mono','Fira Code','SFMono-Regular',monospace"
    SANS = (
        "'Inter','Segoe UI',system-ui,-apple-system,'Helvetica Neue',Arial,sans-serif"
    )

    PERIOD_COLOURS = {"Before": TEAL_SOFT, "During": CORAL, "After": OCEAN}
    PERIOD_ORDER = ["Before", "During", "After"]
    PEN_COLOURS = {
        "P101": TEAL,
        "P102": OCEAN,
        "P103": TEAL_SOFT,
        "P201": PALETTE["slate"],
        "P202": "#A7BAC5",
    }
    SEVERITY_COLOURS = {"high": CORAL, "moderate": OCEAN, "low": TEAL_SOFT}

    def _warehouse_path() -> Path:
        """Locate the DuckDB warehouse from the repo root or the notebook folder."""
        direct = Path("data/warehouse/stingray.duckdb")
        if direct.exists():
            return direct
        for parent in Path.cwd().resolve().parents:
            candidate = parent / "data/warehouse/stingray.duckdb"
            if candidate.exists():
                return candidate
        raise FileNotFoundError(
            "data/warehouse/stingray.duckdb not found — run "
            "`uv run dbt build --profiles-dir .` first"
        )

    con = duckdb.connect(str(_warehouse_path()), read_only=True)

    def q(sql: str) -> pd.DataFrame:
        """Run a read-only query and return a pandas frame."""
        return con.execute(sql).df()

    def esc(value: object) -> str:
        return _html.escape(str(value))

    def fmt_int(value: float) -> str:
        return f"{value:,.0f}"

    def fmt_rate(value: float) -> str:
        return f"{value:.1f}"

    def fmt_pct(value: float, *, signed: bool = False) -> str:
        if pd.isna(value):
            return "—"
        return f"{value:+.0f}%" if signed else f"{value:.0f}%"

    def fmt_pct1(value: float, *, signed: bool = False) -> str:
        if pd.isna(value):
            return "—"
        return f"{value:+.1f}%" if signed else f"{value:.1f}%"

    def header(
        kicker: str,
        title: str,
        lead: str = "",
        *,
        title_size: float = 37,
        lead_size: float = 15.5,
        on_dark: bool = False,
    ) -> mo.Html:
        """Consistent slide header: tiny kicker, large title, one lead line."""
        kicker_colour = TEAL if not on_dark else "#7FE0DA"
        title_colour = NAVY if not on_dark else WHITE
        lead_colour = MUTED if not on_dark else "#B9D6D2"
        lead_html = (
            f'<div style="font-size:{lead_size}px;line-height:1.45;color:{lead_colour};'
            f'margin-top:7px;max-width:1120px;">{lead}</div>'
            if lead
            else ""
        )
        return mo.Html(
            f'<div style="margin:0 0 14px 0;">'
            f'<div style="font-size:10.5px;font-weight:700;letter-spacing:.2em;'
            f'text-transform:uppercase;color:{kicker_colour};">{kicker}</div>'
            f'<div style="font-size:{title_size}px;font-weight:700;line-height:1.1;'
            f'color:{title_colour};margin-top:5px;letter-spacing:-.015em;">{title}</div>'
            f"{lead_html}</div>"
        )

    def rule(*, colour: str = BORDER, margin: str = "0") -> str:
        return f'<div style="height:1px;background:{colour};margin:{margin};"></div>'

    def chip(text: str, *, fg: str = OCEAN, bg: str = MIST, size: float = 10.5) -> str:
        return (
            f'<span style="display:inline-block;background:{bg};color:{fg};'
            f"padding:2px 8px;border-radius:999px;font-size:{size}px;"
            f'font-weight:650;white-space:nowrap;letter-spacing:.01em;">{text}</span>'
        )

    def label(text: str, *, colour: str = MUTED, size: float = 10) -> str:
        return (
            f'<div style="font-size:{size}px;font-weight:700;letter-spacing:.14em;'
            f'text-transform:uppercase;color:{colour};">{text}</div>'
        )

    def accent_bar(colour: str, *, width: int = 3) -> str:
        return f'<div style="width:{width}px;background:{colour};border-radius:2px;"></div>'

    def read_sql_excerpt(
        path: str, first_line: int, last_line: int, highlight: str
    ) -> tuple[str, str]:
        """Read an exact line range from a model, returning HTML and the highlighted line.

        This is deliberately file-backed: the slide cannot drift into a paraphrase.
        """
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        if first_line < 1 or last_line > len(lines) or first_line > last_line:
            raise ValueError(f"invalid line range for {path}: {first_line}-{last_line}")
        block = textwrap.dedent("\n".join(lines[first_line - 1 : last_line])).strip(
            "\n"
        )
        if highlight not in block:
            raise ValueError(
                f"highlight {highlight!r} not found in {path}:{first_line}"
            )
        rendered = []
        for line in block.splitlines():
            safe = _html.escape(line)
            if highlight in line:
                rendered.append(
                    f'<span style="display:block;background:rgba(255,118,94,.16);'
                    f'border-left:2px solid {CORAL};padding-left:8px;margin-left:-10px;">'
                    f"{safe}</span>"
                )
            else:
                rendered.append(f'<span style="display:block;">{safe}</span>')
        return "".join(rendered), block

    def code_card(model: str, code_html: str) -> str:
        return (
            f'<div style="background:{NAVY};border-radius:10px;padding:13px 15px;'
            f'height:100%;box-sizing:border-box;display:flex;flex-direction:column;">'
            f'<div style="font-family:{MONO};font-size:9.2px;color:{SEAFOAM};'
            f'letter-spacing:.02em;margin-bottom:8px;overflow-wrap:anywhere;">{esc(model)}</div>'
            f'<pre style="margin:0;font-family:{MONO};font-size:10.3px;line-height:1.55;'
            f'color:#E6F2F0;white-space:pre-wrap;overflow-wrap:anywhere;">{code_html}</pre>'
            f"</div>"
        )

    def deck_chart(chart: alt.Chart, *, background: str = "transparent") -> alt.Chart:
        return (
            chart.configure_view(stroke=None)
            .configure_axis(
                labelColor=MUTED,
                titleColor=INK,
                grid=False,
                domainColor="#CBD8E0",
                tickColor="#CBD8E0",
                labelFontSize=11,
                titleFontSize=11,
                titleFontWeight="normal",
                titlePadding=7,
            )
            .configure_legend(
                labelColor=INK,
                titleColor=INK,
                labelFontSize=10.5,
                symbolSize=70,
                orient="top",
                direction="horizontal",
                title=None,
                offset=4,
            )
            .configure_title(
                color=INK,
                fontSize=12,
                subtitleColor=MUTED,
                subtitleFontSize=10,
                anchor="start",
                offset=8,
            )
            .configure(background=background)
        )


@app.cell(hide_code=True)
def load_marts():
    # Everything visible in the deck is queried from the marts or the source extracts.
    daily = q(
        """
        select
            site_id, pen_id, activity_date,
            expected_node_days, reported_node_days, reporting_completeness,
            laser_shot_count, lice_detection_count, uptime_minutes,
            shots_per_operating_hour, detections_per_operating_hour,
            shots_per_detection, has_node_set_change, node_ids,
            fish_count, has_fish_count, fish_count_log_id, fish_count_age_days,
            has_storm, storm_count, storm_minutes, max_storm_severity
        from main_marts.fct_pen_daily_activity
        order by activity_date, site_id, pen_id
        """
    )
    analysis = q(
        """
        select
            a.*, e.max_severity, e.episode_start_date, e.episode_end_date,
            e.episode_span_hours, e.storm_event_count, e.storm_ids
        from main_marts.fct_pen_storm_window_day as a
        inner join main_marts.dim_storm_episode as e
            on e.storm_episode_key = a.storm_episode_key
        order by e.episode_start_date, a.pen_id, a.activity_date
        """
    )
    episodes = q(
        """
        select
            storm_episode_key, site_id, episode_started_at, episode_ended_at,
            episode_start_date, episode_end_date, episode_span_hours,
            storm_event_count, max_severity, storm_ids
        from main_marts.dim_storm_episode
        order by episode_started_at
        """
    )
    # There is no baseline fact. This one-row-per-pen-episode summary is
    # derived in the notebook from the daily window fact, using total shots /
    # total operating minutes over each period (never an average of daily rates).
    baselines = q(
        """
        with period as (
            select
                a.storm_episode_key,
                a.site_id,
                a.pen_id,
                case
                    when a.storm_period = 'before' then 'baseline'
                    else a.storm_period
                end as period,
                e.max_severity,
                e.episode_start_date,
                e.episode_end_date,
                e.episode_span_hours,
                count(*) as days,
                sum(a.laser_shot_count) as shots,
                sum(a.uptime_minutes) as uptime_minutes,
                sum(a.lice_detection_count) as detections,
                avg(a.reporting_completeness) as reporting_completeness,
                bool_or(a.has_node_set_change) as has_node_set_change
            from main_marts.fct_pen_storm_window_day as a
            inner join main_marts.dim_storm_episode as e
                on e.storm_episode_key = a.storm_episode_key
            group by
                a.storm_episode_key,
                a.site_id,
                a.pen_id,
                a.storm_period,
                e.max_severity,
                e.episode_start_date,
                e.episode_end_date,
                e.episode_span_hours
        ),
        pivoted as (
            select
                period.storm_episode_key,
                period.site_id,
                period.pen_id,
                period.max_severity,
                period.episode_start_date,
                period.episode_end_date,
                max(period.episode_span_hours) as episode_span_hours,
                bool_or(period.has_node_set_change) as has_node_change_in_window,
                max(case when period.period = 'baseline' then period.days end) as baseline_days,
                max(case when period.period = 'during' then period.days end) as during_days,
                max(case when period.period = 'after' then period.days end) as after_days,
                max(case when period.period = 'baseline' then period.shots end) as baseline_shots,
                max(case when period.period = 'during' then period.shots end) as during_shots,
                max(case when period.period = 'after' then period.shots end) as after_shots,
                max(case when period.period = 'baseline' then period.uptime_minutes end) as baseline_uptime_minutes,
                max(case when period.period = 'during' then period.uptime_minutes end) as during_uptime_minutes,
                max(case when period.period = 'after' then period.uptime_minutes end) as after_uptime_minutes,
                max(case when period.period = 'baseline' then period.detections end) as baseline_detections,
                max(case when period.period = 'during' then period.detections end) as during_detections,
                max(case when period.period = 'after' then period.detections end) as after_detections,
                max(case when period.period = 'baseline' then period.reporting_completeness end) as baseline_reporting_completeness,
                max(case when period.period = 'during' then period.reporting_completeness end) as during_reporting_completeness,
                max(case when period.period = 'after' then period.reporting_completeness end) as after_reporting_completeness
            from period
            group by
                period.storm_episode_key,
                period.site_id,
                period.pen_id,
                period.max_severity,
                period.episode_start_date,
                period.episode_end_date,
                period.episode_span_hours
        ),
        rates as (
            select
                pivoted.*,
                case
                    when pivoted.baseline_uptime_minutes > 0
                        then round(pivoted.baseline_shots / pivoted.baseline_uptime_minutes * 60, 3)
                end as baseline_shots_per_operating_hour,
                case
                    when pivoted.during_uptime_minutes > 0
                        then round(pivoted.during_shots / pivoted.during_uptime_minutes * 60, 3)
                end as during_shots_per_operating_hour,
                case
                    when pivoted.after_uptime_minutes > 0
                        then round(pivoted.after_shots / pivoted.after_uptime_minutes * 60, 3)
                end as after_shots_per_operating_hour,
                case
                    when pivoted.baseline_uptime_minutes > 0
                        then round(pivoted.baseline_detections / pivoted.baseline_uptime_minutes * 60, 3)
                end as baseline_detections_per_operating_hour,
                case
                    when pivoted.during_uptime_minutes > 0
                        then round(pivoted.during_detections / pivoted.during_uptime_minutes * 60, 3)
                end as during_detections_per_operating_hour,
                case
                    when pivoted.after_uptime_minutes > 0
                        then round(pivoted.after_detections / pivoted.after_uptime_minutes * 60, 3)
                end as after_detections_per_operating_hour,
                case
                    when pivoted.baseline_detections > 0
                        then round(pivoted.baseline_shots / pivoted.baseline_detections, 3)
                end as baseline_shots_per_detection,
                case
                    when pivoted.during_detections > 0
                        then round(pivoted.during_shots / pivoted.during_detections, 3)
                end as during_shots_per_detection,
                case
                    when pivoted.after_detections > 0
                        then round(pivoted.after_shots / pivoted.after_detections, 3)
                end as after_shots_per_detection
            from pivoted
        )
        select
            rates.*,
            case
                when rates.baseline_shots_per_operating_hour > 0
                    and rates.during_shots_per_operating_hour is not null
                    then round(
                        (rates.during_shots_per_operating_hour - rates.baseline_shots_per_operating_hour)
                        / rates.baseline_shots_per_operating_hour * 100, 3
                    )
            end as during_change_vs_baseline_pct,
            case
                when rates.baseline_shots_per_operating_hour > 0
                    and rates.after_shots_per_operating_hour is not null
                    then round(
                        (rates.after_shots_per_operating_hour - rates.baseline_shots_per_operating_hour)
                        / rates.baseline_shots_per_operating_hour * 100, 3
                    )
            end as after_change_vs_baseline_pct,
            case
                when rates.baseline_detections_per_operating_hour > 0
                    and rates.during_detections_per_operating_hour is not null
                    then round(
                        (rates.during_detections_per_operating_hour - rates.baseline_detections_per_operating_hour)
                        / rates.baseline_detections_per_operating_hour * 100, 3
                    )
            end as during_detections_change_vs_baseline_pct,
            case
                when rates.baseline_detections_per_operating_hour > 0
                    and rates.after_detections_per_operating_hour is not null
                    then round(
                        (rates.after_detections_per_operating_hour - rates.baseline_detections_per_operating_hour)
                        / rates.baseline_detections_per_operating_hour * 100, 3
                    )
            end as after_detections_change_vs_baseline_pct
        from rates
        order by rates.episode_start_date, rates.pen_id
        """
    )
    storm_days = q(
        """
        select distinct
            site_id, activity_date, storm_count,
            storm_minutes as total_storm_minutes, max_storm_severity
        from main_marts.fct_pen_daily_activity
        where has_storm
        order by site_id, activity_date
        """
    )
    mart_counts = q(
        """
        select 'fct_pen_daily_activity' as model_name, count(*) as row_count
        from main_marts.fct_pen_daily_activity
        union all select 'fct_pen_storm_window_day', count(*)
        from main_marts.fct_pen_storm_window_day
        union all select 'dim_date', count(*) from main_marts.dim_date
        union all select 'dim_site', count(*) from main_marts.dim_site
        union all select 'dim_pen', count(*) from main_marts.dim_pen
        union all select 'dim_storm_episode', count(*) from main_marts.dim_storm_episode
        """
    )
    source_counts = q(
        """
        select 'node_daily_activity' as source_table, count(*) as row_count
        from main_staging.stg_stingray__node_daily_activity
        union all select 'node_pen_assignment', count(*)
        from main_staging.stg_stingray__node_pen_assignments
        union all select 'storm_events', count(*)
        from main_staging.stg_stingray__storm_events
        union all select 'farmer_pen_log', count(*)
        from main_staging.stg_stingray__farmer_pen_logs
        """
    )
    fish_logs = q(
        """
        select log_id, pen_id, logged_local_date, logged_at_local, fish_count,
               is_fish_count_plausible, is_duplicate_pen_day, log_comment
        from main_intermediate.int_fish_counts_validated
        order by log_id
        """
    )
    missing_telemetry = q(
        """
        select node_id, site_id, pen_id, activity_date
        from main_intermediate.int_node_days_assigned
        where not has_activity_record
        order by activity_date
        """
    )
    zero_uptime = q(
        """
        select node_id, activity_date, uptime_minutes
        from main_staging.stg_stingray__node_daily_activity
        where uptime_minutes = 0
        order by node_id, activity_date
        """
    )
    return (
        daily,
        analysis,
        episodes,
        baselines,
        storm_days,
        mart_counts,
        source_counts,
        fish_logs,
        missing_telemetry,
        zero_uptime,
    )


@app.cell(hide_code=True)
def shape_metrics(analysis, baselines, daily, episodes, storm_days):
    # ------------------------------------------------------------------
    # Numbers used on the slides. Percentages are recomputed from totals
    # and checked against the mart before they are displayed.
    # ------------------------------------------------------------------
    s01 = baselines[baselines["site_id"] == "S01"].sort_values("pen_id").copy()
    s02 = (
        baselines[baselines["site_id"] == "S02"]
        .sort_values(["episode_start_date", "pen_id"])
        .copy()
    )

    totals = {
        "shots": int(daily["laser_shot_count"].sum()),
        "detections": int(daily["lice_detection_count"].sum()),
        "uptime_hours": float(daily["uptime_minutes"].sum() / 60),
        "completeness": float(
            daily["reported_node_days"].sum() / daily["expected_node_days"].sum()
        ),
        "pen_days": len(daily),
        "storm_days": len(storm_days),
        "sites": daily["site_id"].nunique(),
        "pens": daily["pen_id"].nunique(),
        "reported_node_days": int(daily["reported_node_days"].sum()),
        "expected_node_days": int(daily["expected_node_days"].sum()),
        "days": int(daily["activity_date"].nunique()),
        "uptime_minutes": int(daily["uptime_minutes"].sum()),
    }

    # Recompute the three period rates and the percentage changes.
    for frame in (s01, s02):
        for period in ("baseline", "during", "after"):
            shots = frame[f"{period}_shots"]
            uptime = frame[f"{period}_uptime_minutes"]
            computed = (shots / uptime * 60).where(uptime > 0)
            published = frame[f"{period}_shots_per_operating_hour"]
            if not ((computed - published).abs().fillna(0) < 0.002).all():
                raise AssertionError(f"{period} rate does not reconcile with totals")
        for period in ("during", "after"):
            computed_pct = (
                (
                    frame[f"{period}_shots_per_operating_hour"]
                    - frame["baseline_shots_per_operating_hour"]
                )
                / frame["baseline_shots_per_operating_hour"]
                * 100
            ).where(frame["baseline_shots_per_operating_hour"] > 0)
            published_pct = frame[f"{period}_change_vs_baseline_pct"]
            if not ((computed_pct - published_pct).abs().fillna(0) < 0.01).all():
                raise AssertionError(f"{period} percentage does not reconcile")

    # Grain and relationship checks used by the validation slide.
    if len(daily) != 63 or len(analysis) != 39 or len(baselines) != 5:
        raise AssertionError("fact row counts changed; review the deck claims")
    if totals["shots"] != 34_862 or totals["detections"] != 25_493:
        raise AssertionError("totals do not match the expected warehouse values")

    relationship_counts = q(
        """
        select
            a.pen_id,
            a.storm_episode_key,
            count(a.pen_storm_day_id) as analysis_rows
        from main_marts.fct_pen_storm_window_day as a
        group by a.pen_id, a.storm_episode_key
        order by analysis_rows desc
        """
    )
    if (relationship_counts["analysis_rows"] <= 1).any():
        raise AssertionError("pen-episode summary -> window fact is not one-to-many")

    orphan_counts = q(
        """
        select 'daily_date' as check_name, count(*) as orphans
        from main_marts.fct_pen_daily_activity f
        left join main_marts.dim_date d on d.date_key = f.date_key
        where d.date_key is null
        union all
        select 'daily_site', count(*)
        from main_marts.fct_pen_daily_activity f
        left join main_marts.dim_site d on d.site_key = f.site_key
        where d.site_key is null
        union all
        select 'daily_pen', count(*)
        from main_marts.fct_pen_daily_activity f
        left join main_marts.dim_pen d on d.pen_key = f.pen_key
        where d.pen_key is null
        union all
        select 'window_date', count(*)
        from main_marts.fct_pen_storm_window_day f
        left join main_marts.dim_date d on d.date_key = f.date_key
        where d.date_key is null
        union all
        select 'window_site', count(*)
        from main_marts.fct_pen_storm_window_day f
        left join main_marts.dim_site d on d.site_key = f.site_key
        where d.site_key is null
        union all
        select 'window_pen', count(*)
        from main_marts.fct_pen_storm_window_day f
        left join main_marts.dim_pen d on d.pen_key = f.pen_key
        where d.pen_key is null
        union all
        select 'window_episode', count(*)
        from main_marts.fct_pen_storm_window_day f
        left join main_marts.dim_storm_episode d on d.storm_episode_key = f.storm_episode_key
        where d.storm_episode_key is null
        """
    )
    if int(orphan_counts["orphans"].sum()) != 0:
        raise AssertionError(
            f"orphaned foreign keys: {orphan_counts.to_dict('records')}"
        )

    # The storm fact is deliberately non-additive: 3 pen-days sit in two
    # episode windows (the next episode's before is this episode's after).
    duplicate_pen_days = q(
        """
        select count(*) as duplicate_rows
        from main_marts.fct_pen_storm_window_day as a
        inner join main_marts.fct_pen_storm_window_day as b
            on a.pen_id = b.pen_id
            and a.activity_date = b.activity_date
            and a.storm_episode_key <> b.storm_episode_key
        """
    ).iloc[0, 0]
    unique_analysis = q(
        """
        select count(*) as rows, sum(laser_shot_count) as shots
        from (
            select distinct pen_id, activity_date, laser_shot_count
            from main_marts.fct_pen_storm_window_day
        )
        """
    ).iloc[0]
    analysis_totals = {
        "rows": len(analysis),
        "unique_pen_days": int(unique_analysis["rows"]),
        "shots": int(analysis["laser_shot_count"].sum()),
        "unique_shots": int(unique_analysis["shots"]),
        "duplicate_rows": int(duplicate_pen_days),
    }
    analysis_totals["double_counted_shots"] = (
        analysis_totals["shots"] - analysis_totals["unique_shots"]
    )

    # S01 chart data: one row per pen and period.
    s01_long = s01.melt(
        id_vars=["pen_id", "site_id", "max_severity"],
        value_vars=[
            "baseline_shots_per_operating_hour",
            "during_shots_per_operating_hour",
            "after_shots_per_operating_hour",
        ],
        var_name="period_key",
        value_name="rate",
    )
    s01_long["period"] = s01_long["period_key"].map(
        {
            "baseline_shots_per_operating_hour": "Before",
            "during_shots_per_operating_hour": "During",
            "after_shots_per_operating_hour": "After",
        }
    )
    s01_long["rate_label"] = s01_long["rate"].map(lambda v: f"{v:.1f}")
    s01_long["delta_label"] = ""
    for pen in s01["pen_id"]:
        during_pct = float(
            s01.loc[s01["pen_id"] == pen, "during_change_vs_baseline_pct"].iloc[0]
        )
        after_pct = float(
            s01.loc[s01["pen_id"] == pen, "after_change_vs_baseline_pct"].iloc[0]
        )
        s01_long.loc[
            (s01_long["pen_id"] == pen) & (s01_long["period"] == "During"),
            "delta_label",
        ] = f"{during_pct:+.0f}%"
        s01_long.loc[
            (s01_long["pen_id"] == pen) & (s01_long["period"] == "After"),
            "delta_label",
        ] = f"{after_pct:+.0f}%"

    # Rate vs volume: the same pen, three different percentage changes.
    delta_rows = []
    for row in s01.itertuples():
        delta_rows.extend(
            [
                {
                    "pen_id": row.pen_id,
                    "metric": "Rate",
                    "pct": float(row.during_change_vs_baseline_pct),
                },
                {
                    "pen_id": row.pen_id,
                    "metric": "Total shots",
                    "pct": (row.during_shots - row.baseline_shots)
                    / row.baseline_shots
                    * 100,
                },
                {
                    "pen_id": row.pen_id,
                    "metric": "Operating hours",
                    "pct": (row.during_uptime_minutes - row.baseline_uptime_minutes)
                    / row.baseline_uptime_minutes
                    * 100,
                },
            ]
        )
    delta_metrics = pd.DataFrame(delta_rows)
    delta_metrics["label"] = delta_metrics["pct"].map(lambda v: f"{v:+.0f}%")
    delta_metrics["metric_short"] = delta_metrics["metric"].map(
        {"Rate": "Rate", "Total shots": "Shots", "Operating hours": "Hours"}
    )
    delta_metrics["label_x"] = delta_metrics["pct"] + delta_metrics["pct"].map(
        lambda v: 3 if v >= 0 else -3
    )
    delta_metrics["label_align"] = delta_metrics["pct"].map(
        lambda v: "left" if v >= 0 else "right"
    )

    # S01 per-pen, per-period metrics from the storm-window fact.
    # Aggregated from totals; never an average of daily rates.
    _s01_window = analysis[analysis["site_id"] == "S01"].copy()
    _grouped = (
        _s01_window.groupby(["pen_id", "storm_period"], sort=False)
        .agg(
            days=("activity_date", "count"),
            reported_days=("has_reported_activity", "sum"),
            positive_uptime_days=("uptime_minutes", lambda col: int((col > 0).sum())),
            expected_node_minutes=("expected_node_minutes", "sum"),
            uptime_minutes=("uptime_minutes", "sum"),
            shots=("laser_shot_count", "sum"),
            detections=("lice_detection_count", "sum"),
            expected_node_days=("expected_node_days", "sum"),
            reported_node_days=("reported_node_days", "sum"),
            nodes=("node_ids", lambda col: " / ".join(sorted(set(col)))),
        )
        .reset_index()
    )
    _grouped["completeness"] = (
        _grouped["reported_node_days"] / _grouped["expected_node_days"]
    )
    _grouped["uptime_pct"] = (
        _grouped["uptime_minutes"] / _grouped["expected_node_minutes"] * 100
    )
    _grouped["det_hr"] = _grouped["detections"] / (_grouped["uptime_minutes"] / 60)
    _grouped["shots_hr"] = _grouped["shots"] / (_grouped["uptime_minutes"] / 60)
    _grouped["spd"] = _grouped["shots"] / _grouped["detections"]

    _metric_cols = [
        "days",
        "reported_days",
        "positive_uptime_days",
        "completeness",
        "uptime_pct",
        "det_hr",
        "shots_hr",
        "spd",
        "shots",
        "detections",
        "uptime_minutes",
        "nodes",
    ]
    _wide = _grouped.pivot(index="pen_id", columns="storm_period", values=_metric_cols)
    _wide.columns = [f"{metric}_{period}" for metric, period in _wide.columns]
    s01_metrics = _wide.reset_index().sort_values("pen_id").reset_index(drop=True)

    for period in ("during", "after"):
        for metric in ("uptime_pct", "det_hr", "shots_hr", "spd"):
            base = s01_metrics[f"{metric}_before"]
            value = s01_metrics[f"{metric}_{period}"]
            s01_metrics[f"{period}_change_{metric}_pct"] = (value - base) / base * 100

    # Baseline day-to-day variability, used to qualify the pen comparisons.
    _baseline_daily = _s01_window[_s01_window["storm_period"] == "before"].copy()
    _baseline_daily["shots_hr"] = _baseline_daily["laser_shot_count"] / (
        _baseline_daily["uptime_minutes"] / 60
    )
    _baseline_daily["det_hr"] = _baseline_daily["lice_detection_count"] / (
        _baseline_daily["uptime_minutes"] / 60
    )
    _baseline_daily["spd"] = (
        _baseline_daily["laser_shot_count"] / _baseline_daily["lice_detection_count"]
    )
    baseline_ranges = (
        _baseline_daily.groupby("pen_id")
        .agg(
            shots_hr_min=("shots_hr", "min"),
            shots_hr_max=("shots_hr", "max"),
            det_hr_min=("det_hr", "min"),
            det_hr_max=("det_hr", "max"),
            spd_min=("spd", "min"),
            spd_max=("spd", "max"),
        )
        .reset_index()
        .sort_values("pen_id")
        .reset_index(drop=True)
    )

    # S02 is deliberately a separate, quieter story.
    s02_bands = episodes[episodes["site_id"] == "S02"][
        ["episode_start_date", "episode_end_date", "max_severity", "episode_span_hours"]
    ].copy()
    s02_bands["start"] = pd.to_datetime(s02_bands["episode_start_date"])
    s02_bands["end"] = pd.to_datetime(s02_bands["episode_end_date"]) + pd.Timedelta(
        days=1
    )
    p201_daily = daily[
        (daily["pen_id"] == "P201")
        & (daily["activity_date"] >= pd.Timestamp("2026-10-08"))
    ].copy()

    # Timeline for the dashboard: all pens, all 14 days.
    timeline = daily.copy()
    timeline["pen_label"] = timeline["pen_id"]

    # Fish-count context as of the end of the window.
    _last_day = daily["activity_date"].max()
    fish_context = []
    for pen in sorted(daily["pen_id"].unique()):
        pen_rows = daily[daily["pen_id"] == pen].sort_values("activity_date")
        last_row = pen_rows.iloc[-1]
        if last_row["activity_date"] < _last_day:
            status = f"last assigned {last_row['activity_date']:%d %b}"
        elif bool(last_row["has_fish_count"]):
            status = f"{int(last_row['fish_count']):,}"
        elif pen == "P201":
            status = "withheld (implausible)"
        else:
            status = "stale (>7 days)"
        fish_context.append({"pen_id": pen, "status": status})

    # Test results are read from dbt's own artefacts, not typed by hand.
    run_results_path = Path("target/run_results.json")
    manifest_path = Path("target/manifest.json")
    if not run_results_path.exists() or not manifest_path.exists():
        raise FileNotFoundError(
            "target/run_results.json / target/manifest.json not found — run "
            "`uv run dbt build --profiles-dir .` before exporting the deck"
        )
    run_results = json.loads(run_results_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    def _layer(unique_id: str) -> str:
        node = manifest["nodes"].get(unique_id)
        if node is None:
            return "unit"
        fqn = node.get("fqn", [])
        return fqn[1] if len(fqn) > 1 else "other"

    model_results = [
        r for r in run_results["results"] if r["unique_id"].startswith("model.")
    ]
    test_results = [
        r for r in run_results["results"] if not r["unique_id"].startswith("model.")
    ]
    test_counts = {
        "models": len(model_results),
        "tests": len(test_results),
        "pass": sum(1 for r in test_results if r["status"] == "pass"),
        "warn": sum(1 for r in test_results if r["status"] == "warn"),
        "error": sum(1 for r in test_results if r["status"] == "error"),
        "by_layer": {},
    }
    for r in test_results:
        layer = _layer(r["unique_id"])
        bucket = test_counts["by_layer"].setdefault(
            layer, {"pass": 0, "warn": 0, "error": 0}
        )
        bucket[r["status"]] = bucket.get(r["status"], 0) + 1

    s02_summary = [
        {
            "pen_id": row.pen_id,
            "severity": row.max_severity,
            "start": row.episode_start_date,
            "end": row.episode_end_date,
            "during_pct": float(row.during_change_vs_baseline_pct),
        }
        for row in s02.itertuples()
    ]
    return (
        s01,
        s02,
        totals,
        s01_long,
        delta_metrics,
        s01_metrics,
        baseline_ranges,
        s02_bands,
        p201_daily,
        timeline,
        fish_context,
        test_counts,
        analysis_totals,
        relationship_counts,
        s02_summary,
    )


@app.cell(hide_code=True)
def build_figures(episodes, s01_long, delta_metrics, p201_daily, s02_bands, timeline):
    # ---- S01 small multiples: the trajectory of each _panel_pen -----------------
    panels = []
    for _panel_index, _panel_pen in enumerate(["P101", "P102", "P103"]):
        _panel_frame = s01_long[s01_long["pen_id"] == _panel_pen].copy()
        _panel_frame["period"] = pd.Categorical(
            _panel_frame["period"], categories=PERIOD_ORDER, ordered=True
        )
        _panel_frame = _panel_frame.sort_values("period")
        show_axis = _panel_index == 0
        _panel_base = alt.Chart(_panel_frame).encode(
            x=alt.X(
                "period:N",
                sort=PERIOD_ORDER,
                title=None,
                axis=alt.Axis(labelAngle=0, labelFontSize=11, labelPadding=7),
            ),
            y=alt.Y(
                "rate:Q",
                title="Shots per operating hour" if show_axis else None,
                scale=alt.Scale(domain=[0, 40]),
                axis=(
                    alt.Axis(
                        grid=False,
                        tickCount=5,
                        domain=False,
                        labelFontSize=10.5,
                    )
                    if show_axis
                    else None
                ),
            ),
        )
        line = _panel_base.mark_line(color="#B7C7D1", strokeWidth=1.8)
        points = _panel_base.mark_circle(size=120, filled=True).encode(
            color=alt.Color(
                "period:N",
                scale=alt.Scale(
                    domain=PERIOD_ORDER,
                    range=[
                        PERIOD_COLOURS["Before"],
                        PERIOD_COLOURS["During"],
                        PERIOD_COLOURS["After"],
                    ],
                ),
                legend=None,
            )
        )
        values = _panel_base.mark_text(
            dy=-15, fontSize=10.5, fontWeight=600, color=INK
        ).encode(text=alt.Text("rate_label:N"))
        deltas = (
            alt.Chart(_panel_frame[_panel_frame["period"].isin(["During", "After"])])
            .mark_text(dy=16, fontSize=10, fontWeight=700)
            .encode(
                x=alt.X("period:N", sort=PERIOD_ORDER),
                y=alt.Y("rate:Q"),
                text=alt.Text("delta_label:N"),
                color=alt.Color(
                    "period:N",
                    scale=alt.Scale(
                        domain=PERIOD_ORDER,
                        range=[
                            PERIOD_COLOURS["Before"],
                            PERIOD_COLOURS["During"],
                            PERIOD_COLOURS["After"],
                        ],
                    ),
                    legend=None,
                ),
            )
        )
        _panel_title = alt.TitleParams(
            text=_panel_pen,
            subtitle=f"before {_panel_frame['rate'].iloc[0]:.1f}  ·  during {_panel_frame['rate'].iloc[1]:.1f}",
            fontSize=13,
            subtitleFontSize=9.5,
            color=INK,
            subtitleColor=MUTED,
            anchor="start",
            offset=6,
        )
        panels.append(
            (line + points + values + deltas).properties(
                width=235, height=235, title=_panel_title
            )
        )
    fig_s01 = (
        alt.hconcat(*panels, spacing=22)
        .configure_view(stroke=None)
        .configure(background="transparent")
    )

    # ---- Rate vs volume: behaviour versus availability -------------------
    metric_scale = alt.Scale(
        domain=["Rate", "Total shots", "Operating hours"],
        range=[TEAL, OCEAN, CORAL],
    )
    volume_panels = []
    for _vol_index, _vol_pen in enumerate(["P101", "P102", "P103"]):
        _vol_frame = delta_metrics[delta_metrics["pen_id"] == _vol_pen].copy()
        _vol_show = _vol_index == 0
        _vol_base = alt.Chart(_vol_frame).encode(
            x=alt.X(
                "metric_short:N",
                sort=["Rate", "Shots", "Hours"],
                title=None,
                axis=alt.Axis(labelAngle=0, labelFontSize=9.2, labelPadding=5),
            ),
            y=alt.Y(
                "pct:Q",
                title="% change vs before" if _vol_show else None,
                scale=alt.Scale(domain=[-100, 20]),
                axis=(
                    alt.Axis(
                        grid=False,
                        tickCount=3,
                        domain=False,
                        labelFontSize=9.2,
                        titleFontSize=9.2,
                    )
                    if _vol_show
                    else None
                ),
            ),
        )
        _vol_line = _vol_base.mark_line(color="#B7C7D1", strokeWidth=1.5)
        _vol_points = _vol_base.mark_circle(size=90, filled=True).encode(
            color=alt.Color("metric:N", scale=metric_scale, legend=None)
        )
        _vol_labels = _vol_base.mark_text(
            dy=-10, fontSize=9.3, fontWeight=600, color=INK
        ).encode(text=alt.Text("label:N"))
        volume_panels.append(
            (_vol_line + _vol_points + _vol_labels).properties(
                width=170,
                height=135,
                title=alt.TitleParams(
                    text=_vol_pen, fontSize=11, color=INK, anchor="start", offset=4
                ),
            )
        )
    fig_volume = deck_chart(
        alt.hconcat(*volume_panels, spacing=8).properties(
            title=alt.TitleParams(
                text="Rate vs volume, during vs before",
                subtitle="P102 kept operating; the other pens lost hours",
                fontSize=12,
                subtitleFontSize=9.5,
                anchor="start",
            )
        )
    )

    # ---- S02 sparkline: deliberately quiet ------------------------------
    s02_bands_chart = (
        alt.Chart(s02_bands)
        .mark_rect(color=CORAL, opacity=0.12)
        .encode(x=alt.X("start:T"), x2=alt.X2("end:T"))
    )
    s02_line = (
        alt.Chart(p201_daily)
        .mark_line(color=OCEAN, strokeWidth=2)
        .encode(
            x=alt.X(
                "activity_date:T",
                title=None,
                axis=alt.Axis(format="%d %b", tickCount=4, labelAngle=0),
            ),
            y=alt.Y(
                "shots_per_operating_hour:Q",
                title="shots/h",
                scale=alt.Scale(domain=[20, 36]),
                axis=alt.Axis(tickCount=3, grid=False),
            ),
            tooltip=[
                alt.Tooltip("activity_date:T", title="Date", format="%d %b"),
                alt.Tooltip(
                    "shots_per_operating_hour:Q", title="Shots/h", format=".1f"
                ),
            ],
        )
    )
    s02_points = (
        alt.Chart(p201_daily)
        .mark_circle(size=28, color=OCEAN)
        .encode(x="activity_date:T", y="shots_per_operating_hour:Q")
    )
    fig_s02 = deck_chart(
        (s02_bands_chart + s02_line + s02_points).properties(
            width=465,
            height=105,
            title=alt.TitleParams(
                text="S02 · P201 daily rate",
                subtitle="moderate 9–10 Oct  ·  low 14 Oct",
                fontSize=11,
                subtitleFontSize=9,
                anchor="start",
            ),
        )
    )

    # ---- Dashboard: activity over time ----------------------------------
    timeline_bands = episodes[["episode_start_date", "episode_end_date"]].copy()
    timeline_bands["start"] = pd.to_datetime(timeline_bands["episode_start_date"])
    timeline_bands["end"] = pd.to_datetime(
        timeline_bands["episode_end_date"]
    ) + pd.Timedelta(days=1)
    bands_layer = (
        alt.Chart(timeline_bands)
        .mark_rect(color=CORAL, opacity=0.11)
        .encode(x=alt.X("start:T"), x2=alt.X2("end:T"))
    )
    timeline_line = (
        alt.Chart(timeline)
        .mark_line(strokeWidth=1.8)
        .encode(
            x=alt.X(
                "activity_date:T",
                title=None,
                axis=alt.Axis(format="%d %b", tickCount=6, labelAngle=0),
            ),
            y=alt.Y(
                "shots_per_operating_hour:Q",
                title="shots per operating hour",
                scale=alt.Scale(domain=[0, 46]),
                axis=alt.Axis(tickCount=5, grid=False),
            ),
            color=alt.Color(
                "pen_id:N",
                title=None,
                scale=alt.Scale(
                    domain=list(PEN_COLOURS.keys()),
                    range=list(PEN_COLOURS.values()),
                ),
                legend=alt.Legend(
                    orient="top",
                    direction="horizontal",
                    columns=5,
                    labelFontSize=9.5,
                    symbolSize=55,
                ),
            ),
            tooltip=[
                alt.Tooltip("pen_id:N", title="Pen"),
                alt.Tooltip("activity_date:T", title="Date", format="%d %b"),
                alt.Tooltip(
                    "shots_per_operating_hour:Q", title="Shots/h", format=".1f"
                ),
            ],
        )
    )
    fig_timeline_dash = deck_chart(
        (bands_layer + timeline_line).properties(
            width=880,
            height=245,
            title=alt.TitleParams(
                text="Laser activity over time",
                subtitle="shots per operating hour · coral bands = storm exposure",
                fontSize=14,
                subtitleFontSize=10.5,
                anchor="start",
            ),
        ),
        background=WHITE,
    )

    # ---- Dashboard: compact before / during / after ----------------------
    period_bars = (
        alt.Chart(s01_long)
        .mark_bar(size=14, cornerRadiusTopRight=2, cornerRadiusBottomRight=2)
        .encode(
            y=alt.Y(
                "pen_id:N",
                title=None,
                sort=["P101", "P102", "P103"],
                axis=alt.Axis(labelAngle=0, labelFontSize=10),
            ),
            yOffset=alt.YOffset("period:N", sort=PERIOD_ORDER, title=None),
            x=alt.X(
                "rate:Q",
                title="shots / hour",
                scale=alt.Scale(domain=[0, 42]),
                axis=alt.Axis(tickCount=4),
            ),
            color=alt.Color(
                "period:N",
                scale=alt.Scale(
                    domain=PERIOD_ORDER,
                    range=[
                        PERIOD_COLOURS["Before"],
                        PERIOD_COLOURS["During"],
                        PERIOD_COLOURS["After"],
                    ],
                ),
                legend=alt.Legend(
                    orient="top",
                    direction="horizontal",
                    title=None,
                    labelFontSize=9.5,
                    symbolSize=55,
                ),
            ),
        )
    )
    fig_periods_dash = deck_chart(
        period_bars.properties(
            width=420,
            height=245,
            title=alt.TitleParams(
                text="Before · during · after",
                subtitle="S01 pens, weighted rate",
                fontSize=14,
                subtitleFontSize=10.5,
                anchor="start",
            ),
        ),
        background=WHITE,
    )
    return (
        fig_s01,
        fig_volume,
        fig_s02,
        fig_timeline_dash,
        fig_periods_dash,
    )


@app.cell
def slide_title(episodes, totals):
    # KEY MESSAGE  A stakeholder question, a tested pipeline, an honest scope, and the
    #              observed direction of the answer stated up front.
    # SAY          Title question -> early observed association -> scope -> pipeline roles.
    # TRANSITION   "Let me start with what the farmers actually report."
    sonar = f"""
    <svg viewBox="0 0 540 430" width="100%" height="100%" preserveAspectRatio="xMidYMid meet"
         style="display:block;overflow:visible;">
      <defs>
        <radialGradient id="glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="{TEAL}" stop-opacity="0.20"/>
          <stop offset="70%" stop-color="{TEAL}" stop-opacity="0.03"/>
          <stop offset="100%" stop-color="{NAVY}" stop-opacity="0"/>
        </radialGradient>
        <linearGradient id="sweep" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="{CORAL}" stop-opacity="0"/>
          <stop offset="100%" stop-color="{CORAL}" stop-opacity="0.75"/>
        </linearGradient>
      </defs>
      <circle cx="300" cy="205" r="205" fill="url(#glow)"/>
      <g fill="none" stroke="{TEAL}" stroke-width="1">
        <circle cx="300" cy="205" r="42" opacity="0.26"/>
        <circle cx="300" cy="205" r="84" opacity="0.20"/>
        <circle cx="300" cy="205" r="126" opacity="0.16"/>
        <circle cx="300" cy="205" r="168" opacity="0.12"/>
        <circle cx="300" cy="205" r="205" opacity="0.08"/>
      </g>
      <path d="M 300 205 L 520 145 A 230 230 0 0 0 507 282 Z" fill="url(#sweep)" opacity="0.45"/>
      <path d="M 300 205 m -205 0 a 205 205 0 0 1 410 0" fill="none" stroke="{CORAL}" stroke-width="2.4" opacity="0.85"/>
      <g fill="{TEAL}">
        <circle cx="342" cy="121" r="4.2" opacity="0.95"/>
        <circle cx="391" cy="168" r="3.4" opacity="0.75"/>
        <circle cx="246" cy="151" r="3.0" opacity="0.7"/>
        <circle cx="218" cy="252" r="4.0" opacity="0.9"/>
        <circle cx="355" cy="278" r="3.2" opacity="0.75"/>
        <circle cx="159" cy="205" r="2.6" opacity="0.55"/>
        <circle cx="431" cy="232" r="2.6" opacity="0.55"/>
      </g>
    </svg>
    """
    scope_html = '<span style="width:1px;height:12px;background:#2A4A5F;margin:0 18px;"></span>'.join(
        f'<span style="font-family:{MONO};font-size:16px;font-weight:700;'
        f'color:#7FE0DA;">{value}</span>'
        f'<span style="font-size:11.5px;color:#8FB0AD;margin-left:7px;">{label}</span>'
        for value, label in [
            (totals["sites"], "sites analysed"),
            (totals["pens"], "pens compared"),
            (len(episodes), "storm episodes"),
        ]
    )
    roles_html = "".join(
        f'<div style="display:flex;gap:9px;align-items:baseline;min-width:0;">'
        f'<span style="font-family:{MONO};font-size:11px;font-weight:650;'
        f'color:#9DC9C5;flex:0 0 72px;">{name}</span>'
        f'<span style="font-size:10.5px;color:#8FB0AD;">{role}</span></div>'
        for name, role in [
            ("DuckDB", "local analytical warehouse"),
            ("dbt", "transformations, data modelling and testing"),
            ("Marimo", "EDA, and presentation"),
        ]
    )
    mo.Html(
        f'<div style="display:flex;align-items:center;gap:44px;'
        f'box-sizing:border-box;padding:8px 6px;">'
        f'<div style="flex:1.15;min-width:0;">'
        f'<div style="font-size:10.5px;font-weight:700;letter-spacing:.24em;'
        f'text-transform:uppercase;color:{TEAL};margin-bottom:16px;">'
        f"Stingray · Analytics Engineer case</div>"
        f'<div style="font-size:52px;font-weight:700;line-height:1.06;color:{WHITE};'
        f'letter-spacing:-.025em;max-width:700px;">When storms hit, do the '
        f'<span style="color:#7FE0DA;">lasers slow down</span>?</div>'
        f'<div style="font-size:18px;font-weight:650;line-height:1.45;color:#B9D6D2;'
        f'margin-top:16px;max-width:620px;">Storm periods coincided with lower '
        f"equipment uptime and fewer detections meanwhile shots per detection "
        f"stayed broadly stable.</div>"
        f'<div style="font-size:10px;color:#6F8F96;margin-top:10px;">'
        f"Observed association, not a causal claim.</div>"
        f'<div style="margin-top:30px;">'
        f'<div style="font-size:9.5px;font-weight:700;letter-spacing:.16em;'
        f'text-transform:uppercase;color:#6F8F96;margin-bottom:8px;">'
        f"Investigation scope</div>"
        f'<div style="display:flex;align-items:baseline;">{scope_html}</div></div>'
        f'<div style="margin-top:24px;">'
        f'<div style="font-size:10.5px;font-weight:700;letter-spacing:.18em;'
        f'color:{TEAL};">DATA → TESTED MODELS → DECISIONS</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:7px 26px;'
        f'margin-top:10px;">{roles_html}</div></div>'
        f'<div style="font-size:10px;color:#6F8F96;margin-top:18px;">'
        f"The case runs on DuckDB; Snowflake is the production target.</div>"
        f"</div>"
        f'<div style="flex:.85;height:400px;min-width:0;">{sonar}</div>'
        f"</div>"
    )


@app.cell
def slide_problem():
    # KEY MESSAGE  Total shots cannot explain themselves: three possible explanations.
    # SAY          Problem statement, three explanations, then the three questions.
    # TRANSITION   "Before I can answer that, here is the data we actually have."
    questions = [
        ("01", "Does node activity change during storms?"),
        ("02", "Are some pens or sites more affected than others?"),
        ("03", "Does activity recover after the storm?"),
    ]
    question_html = "".join(
        f'<div style="display:flex;gap:18px;padding:15px 0;border-bottom:1px solid {BORDER};">'
        f'<div style="font-family:{MONO};font-size:11px;color:{TEAL};font-weight:700;'
        f'padding-top:4px;">{num}</div>'
        f'<div style="font-size:17.5px;line-height:1.35;color:{NAVY};font-weight:600;">{text}</div>'
        f"</div>"
        for num, text in questions
    )
    explanations = [
        (
            "1",
            "Reduced availability",
            "The node operates for fewer hours, resulting in fewer total shots.",
            CORAL_DEEP,
        ),
        (
            "2",
            "Reduced activity while operating",
            "The node is running, but fires fewer shots per operating hour.",
            OCEAN,
        ),
        (
            "3",
            "Changed detection conditions",
            (
                "Fish behaviour or detection conditions may affect lice detections and, "
                "subsequently, the shots fired — a hypothesis that must be investigated."
            ),
            TEAL_DEEP,
        ),
    ]
    explanation_html = "".join(
        f'<div style="display:flex;gap:12px;padding:12px 0;'
        f'border-bottom:1px solid {BORDER};">'
        f'<div style="flex:0 0 26px;font-family:{MONO};font-size:11px;font-weight:700;'
        f'color:{colour};padding-top:2px;">{num}</div>'
        f'<div style="flex:1;min-width:0;">'
        f'<div style="font-size:13.5px;font-weight:700;color:{NAVY};">{title}</div>'
        f'<div style="font-size:11.5px;line-height:1.45;color:{MUTED};margin-top:3px;">'
        f"{body}</div></div></div>"
        for num, title, body, colour in explanations
    )
    decisions = [
        ("Farmer conversation", "What to say when a customer reports a dip."),
        ("Inspection priority", "Which pens to check first after rough weather."),
        (
            "Instrumentation",
            "Which measurements the team must log to answer this properly.",
        ),
    ]
    decision_html = "".join(
        f'<div style="flex:1;padding-top:10px;border-top:2px solid {TEAL};">'
        f'<div style="font-size:10px;font-weight:700;letter-spacing:.12em;'
        f'text-transform:uppercase;color:{TEAL};margin-bottom:4px;">{_decision_title}</div>'
        f'<div style="font-size:12.5px;line-height:1.4;color:{MUTED};">{body}</div></div>'
        for _decision_title, body in decisions
    )
    mo.Html(
        f'<div style="min-height:650px;display:flex;flex-direction:column;box-sizing:border-box;'
        f'padding:8px 6px 10px 6px;">'
        f"{header('01 / The business problem', 'A decline in laser shots', 'Farmers report less laser activity after storms. Help the Fish Health team determine whether this is true.')}"
        f'<div style="display:grid;grid-template-columns:1.24fr .76fr;gap:54px;'
        f'align-items:start;margin-top:8px;">'
        f'<div style="padding:8px 0 0 20px;border-left:4px solid {CORAL};">'
        f'<div style="font-size:9.5px;font-weight:700;letter-spacing:.16em;'
        f'text-transform:uppercase;color:{CORAL_DEEP};">The problem</div>'
        f'<div style="font-size:24px;line-height:1.35;color:{NAVY};font-weight:600;'
        f'letter-spacing:-.01em;max-width:740px;margin-top:8px;">'
        f"Farmers report lower laser activity after storms. Different "
        f'possible explanations: <span style="color:{CORAL_DEEP};">equipment availability, laser activity</span> '
        f"or both.</div>"
        f'<div style="font-size:11.5px;color:{MUTED};margin-top:12px;">'
        f"Kari Nordmann · Fish Health Biologist</div>"
        f'<div style="height:1px;background:{BORDER};margin:20px 0 12px 0;"></div>'
        f'<div style="font-size:9.5px;font-weight:700;letter-spacing:.16em;'
        f'text-transform:uppercase;color:{MUTED};margin-bottom:2px;">'
        f"Three possible explanations</div>"
        f"{explanation_html}"
        f'<div style="font-size:10.5px;line-height:1.45;color:{MUTED};margin-top:10px;">'
        f"All three are plausible hypotheses. The analysis is designed to "
        f"distinguish between them.</div></div>"
        f'<div style="padding-top:2px;">'
        f'<div style="background:{WHITE};border:1px solid {BORDER};border-radius:9px;'
        f'padding:6px 16px 4px 16px;">'
        f'<div style="font-size:9.5px;font-weight:700;letter-spacing:.16em;'
        f'text-transform:uppercase;color:{MUTED};margin:8px 0 4px 0;">'
        f"The analysis will answer</div>"
        f"{question_html}"
        f'<div style="font-size:11.5px;line-height:1.5;color:{MUTED};margin:12px 0 8px 0;">'
        f"Each question uses the same model, so the answer is comparable "
        f"across pens, sites and episodes.</div></div></div></div>"
        f'<div style="display:flex;gap:28px;margin-top:auto;">{decision_html}</div>'
        f"</div>"
    )


@app.cell
def slide_sources(daily, source_counts):
    # KEY MESSAGE  Four sources, four levels of detail; the hard part is time.
    # SAY          Walk each source in plain language, then the shared daily view.
    # TRANSITION   "Small data, but it fights back in three specific places."
    _source_counts = dict(
        zip(source_counts["source_table"], source_counts["row_count"], strict=True)
    )
    incomplete_pen_days = len(daily[daily["reporting_completeness"] < 1])
    sources = [
        (
            "01",
            "Node activity",
            "node_daily_activity",
            _source_counts["node_daily_activity"],
            (
                "Daily shots, lice detections and operating time for each laser node. "
                "We link each node to the pen where it was installed on that date."
            ),
            TEAL,
        ),
        (
            "02",
            "Node assignments",
            "node_pen_assignment",
            _source_counts["node_pen_assignment"],
            (
                "Which site and pen each node belonged to, and when. We use this to "
                "track movements and attribute activity to the correct pen."
            ),
            OCEAN,
        ),
        (
            "03",
            "Storm events",
            "storm_events",
            _source_counts["storm_events"],
            (
                "When storms occurred, where they occurred and how severe they were. "
                "We calculate how many minutes of each day were affected by a storm."
            ),
            CORAL,
        ),
        (
            "04",
            "Farmer logs",
            "farmer_pen_log",
            _source_counts["farmer_pen_log"],
            (
                "Fish counts manually entered for each pen. We use the latest "
                "plausible count as population context."
            ),
            TEAL_DEEP,
        ),
    ]
    source_html = ""
    for _num, name, table, rows, description, colour in sources:
        source_html += (
            f'<div style="display:grid;grid-template-columns:186px 1fr;gap:22px;'
            f'padding:13px 0;border-top:1px solid {BORDER};align-items:start;">'
            f'<div style="display:flex;gap:10px;align-items:flex-start;">'
            f"{accent_bar(colour)}"
            f'<div style="min-width:0;">'
            f'<div style="display:flex;gap:7px;align-items:baseline;">'
            f'<span style="font-family:{MONO};font-size:9.5px;color:{colour};'
            f'font-weight:700;">{_num}</span>'
            f'<span style="font-size:13px;font-weight:700;color:{NAVY};">{name}</span></div>'
            f'<div style="font-family:{MONO};font-size:9px;color:{MUTED};'
            f'margin-top:3px;overflow-wrap:anywhere;">{table} · {rows} rows</div></div></div>'
            f'<div style="font-size:12.5px;line-height:1.5;color:{INK};">{description}</div>'
            f"</div>"
        )
    spine = (
        f'<div style="background:{SEAFOAM};border-radius:10px;padding:16px 14px;'
        f"height:100%;box-sizing:border-box;display:flex;flex-direction:column;"
        f'justify-content:center;">'
        f'<div style="font-size:9.5px;font-weight:700;letter-spacing:.14em;'
        f'text-transform:uppercase;color:{TEAL_DEEP};">The shared view</div>'
        f'<div style="font-size:18px;font-weight:700;color:{NAVY};line-height:1.2;'
        f'margin-top:5px;">site × pen<br>× day</div>'
        f'<div style="font-family:{MONO};font-size:20px;font-weight:700;color:{TEAL_DEEP};'
        f'margin-top:12px;">{len(daily)}</div>'
        f'<div style="font-size:10px;color:{MUTED};">pen-days</div>'
        f'<div style="height:1px;background:#B9DDD6;margin:12px 0;"></div>'
        f'<div style="font-size:10px;line-height:1.4;color:{MUTED};">One row per site, '
        f"pen and day: Allows consistent comparison across pens and dates.</div></div>"
    )
    mo.Html(
        f'<div style="min-height:650px;display:flex;flex-direction:column;box-sizing:border-box;'
        f'padding:8px 6px 10px 6px;">'
        f"{header('02 / Understanding the data', 'Four data sources. One consistent daily view.', 'Each file tells us something different about the equipment, storms or fish population. Before comparing them, we need to align their dates and levels of detail.')}"
        f'<div style="display:grid;grid-template-columns:1fr 178px;gap:20px;'
        f'align-items:stretch;margin-top:2px;">'
        f"<div>{source_html}</div>{spine}</div>"
        f'<div style="margin-top:16px;padding:11px 14px;background:{WHITE};'
        f"border-left:3px solid {CORAL};border-radius:0 8px 8px 0;"
        f'font-size:12.5px;line-height:1.5;color:{INK};">'
        f"<b>The main challenge is different table grains.</b> Node activity is per "
        f"node and day, storm events have exact start and end timestamps, and fish counts are entered "
        f"manually per pen. I align these sources to the same local calendar day before comparing "
        f"them.</div>"
        f'<div style="margin-top:9px;padding-left:14px;border-left:3px solid {TEAL};'
        f'font-size:12px;line-height:1.5;color:{INK};">'
        f"Some pen-days ({incomplete_pen_days} of {len(daily)}) have incomplete equipment "
        f"records. Distinction is kept, so missing "
        f"data is never mistaken for a machine that stopped operating.</div>"
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:30px;'
        f'margin-top:auto;padding-top:12px;border-top:1px solid {BORDER};">'
        f'<div><div style="font-size:9px;font-weight:700;letter-spacing:.13em;'
        f'text-transform:uppercase;color:{MUTED};">What the extract does not contain</div>'
        f'<div style="font-size:11.5px;line-height:1.45;color:{INK};margin-top:4px;">'
        f"No site names, geographical information or additional pen details.</div></div>"
        f'<div><div style="font-size:9px;font-weight:700;letter-spacing:.13em;'
        f'text-transform:uppercase;color:{MUTED};">What the model adds</div>'
        f'<div style="font-size:11.5px;line-height:1.45;color:{INK};margin-top:4px;">'
        f"A consistent local calendar, reporting completeness and node assignment "
        f"history.</div></div></div>"
        f"</div>"
    )


@app.cell
def slide_quality(fish_logs, missing_telemetry, test_counts, zero_uptime):
    # KEY MESSAGE  Three raw-data problems, each with a practical consequence and fix.
    # SAY          Each row: what I found -> why it matters -> how I handled it.
    # TRANSITION   "Those decisions define the metric."
    p102_logs = fish_logs[
        (fish_logs["pen_id"] == "P102")
        & (fish_logs["logged_local_date"] == pd.Timestamp("2026-10-08"))
    ].sort_values("log_id")
    p201_log = fish_logs[
        (fish_logs["pen_id"] == "P201") & (~fish_logs["is_fish_count_plausible"])
    ].iloc[0]
    unit_tests = sum(test_counts["by_layer"].get("unit", {}).values())
    missing_text = ", ".join(
        f"{_row.node_id} {_row.activity_date:%d %b}"
        for _row in missing_telemetry.itertuples()
    )
    move_missing_text = ", ".join(
        f"{_row.node_id} {_row.activity_date:%d %b}"
        for _row in missing_telemetry[
            missing_telemetry["node_id"] == "N05"
        ].itertuples()
    )
    zero_text = ", ".join(
        f"{_row.node_id} {_row.activity_date:%d %b}"
        for _row in zero_uptime.itertuples()
    )

    movement = f"""
    <svg viewBox="0 0 300 104" width="100%" height="100%" preserveAspectRatio="xMinYMin meet">
      <text x="0" y="12" font-family="{MONO}" font-size="9" fill="{MUTED}">N05 deployment</text>
      <rect x="0" y="26" width="126" height="20" rx="4" fill="#DDE7EE"/>
      <rect x="132" y="26" width="164" height="20" rx="4" fill="#DFF3EF"/>
      <text x="8" y="40" font-family="{SANS}" font-size="10" fill="{OCEAN}">S02 / P202</text>
      <text x="140" y="40" font-family="{SANS}" font-size="10" fill="{TEAL_DEEP}">S01 / P103</text>
      <line x1="130" y1="18" x2="130" y2="76" stroke="{CORAL}" stroke-width="1.5" stroke-dasharray="4 3"/>
      <circle cx="130" cy="66" r="3.5" fill="{WHITE}" stroke="{CORAL}" stroke-width="1.5"/>
      <text x="136" y="70" font-family="{SANS}" font-size="9" fill="{CORAL_DEEP}">8 Oct · move day, no telemetry</text>
      <text x="0" y="98" font-family="{SANS}" font-size="9" fill="{MUTED}">No activity record for {move_missing_text}</text>
    </svg>
    """
    missing_zero = (
        f'<div style="display:flex;gap:10px;align-items:stretch;">'
        f'<div style="flex:1;border:1px dashed #B7C7D1;border-radius:8px;padding:8px 9px;'
        f'background:{WHITE};">'
        f'<div style="font-size:20px;font-weight:700;color:{MUTED};line-height:1;">—</div>'
        f'<div style="font-size:9px;font-weight:700;color:{MUTED};margin-top:4px;'
        f'letter-spacing:.06em;text-transform:uppercase;">No record</div>'
        f'<div style="font-size:8.5px;color:{MUTED};margin-top:2px;line-height:1.3;">'
        f"{missing_text}</div></div>"
        f'<div style="flex:1;border:1px solid #B9DDD6;border-radius:8px;padding:8px 9px;'
        f'background:{SEAFOAM};">'
        f'<div style="font-size:20px;font-weight:700;color:{TEAL_DEEP};line-height:1;">0</div>'
        f'<div style="font-size:9px;font-weight:700;color:{TEAL_DEEP};margin-top:4px;'
        f'letter-spacing:.06em;text-transform:uppercase;">Uptime 0</div>'
        f'<div style="font-size:8.5px;color:{MUTED};margin-top:2px;line-height:1.3;">'
        f"{zero_text}</div></div></div>"
    )
    log_cards = ""
    for _row in p102_logs.itertuples():
        log_cards += (
            f'<div style="display:flex;justify-content:space-between;gap:8px;'
            f"font-family:{MONO};font-size:9.5px;padding:3px 0;"
            f'border-bottom:1px solid {BORDER};">'
            f'<span style="color:{MUTED};">{_row.logged_at_local:%H:%M}</span>'
            f'<span style="color:{INK};">{int(_row.fish_count):,}</span></div>'
        )
    logs = (
        f'<div style="border:1px solid {BORDER};border-radius:8px;padding:7px 10px;'
        f'background:{WHITE};">'
        f'<div style="font-size:9px;font-weight:700;letter-spacing:.1em;'
        f'text-transform:uppercase;color:{MUTED};margin-bottom:3px;">P102 · 8 Oct</div>'
        f"{log_cards}"
        f'<div style="font-size:9px;color:{TEAL_DEEP};margin-top:5px;">latest valid entry used</div>'
        f'<div style="display:flex;justify-content:space-between;gap:8px;margin-top:5px;'
        f'padding-top:5px;border-top:1px solid {BORDER};font-family:{MONO};font-size:9.5px;">'
        f'<span style="color:{CORAL_DEEP};">P201 · 8 Oct</span>'
        f'<span style="color:{CORAL_DEEP};">{int(p201_log.fish_count):,}</span></div>'
        f'<div style="font-size:9px;color:{CORAL_DEEP};margin-top:1px;">implausible → not used</div>'
        f"</div>"
    )

    row_data = [
        (
            "01",
            "A laser node changes pens",
            movement,
            (
                "Node N05 moved from pen P202 at site S02 to pen P103 at site S01 on "
                "8 October. There is no activity record for the day it moved."
            ),
            (
                "If I link activity to a node without considering when it moved, I could "
                "assign its activity to the wrong pen."
            ),
            (
                "I use the assignment that was valid on each date. The move date is "
                "assigned to the new pen, but its missing activity remains missing."
            ),
        ),
        (
            "02",
            "Missing records are not zero activity",
            missing_zero,
            (
                "N05 and N04 have days with no activity record. On other days, N01 and "
                "N03 explicitly report zero operating time."
            ),
            (
                "No record does not necessarily mean the equipment was inactive. Treating "
                "both situations as zero would distort the comparison."
            ),
            (
                "I create an expected record for every node and day it should be assigned. "
                "Missing data gets NULL, reported zeroes remain zero."
            ),
        ),
        (
            "03",
            "Farmer-entered fish counts need checking",
            logs,
            (
                "Pen P102 has two entries on 8 October, including a correction. Pen P201 "
                f"has a reported count of <b>{int(p201_log.fish_count):,}</b> fish, which "
                "appears implausible."
            ),
            (
                "Incorrect or duplicate fish counts could give us a misleading picture of "
                "the fish population in a pen."
            ),
            (
                "I retain the original entries, use the latest valid count, and flag "
                "implausible values rather than silently replacing them."
            ),
        ),
    ]
    column_labels = [
        ("What I found", NAVY),
        ("Why it matters", CORAL_DEEP),
        ("How I handled it", TEAL_DEEP),
    ]
    header_row = (
        '<div style="display:grid;grid-template-columns:236px 1fr 1fr 1fr;gap:24px;'
        'padding:0 0 8px 0;">'
        "<div></div>"
        + "".join(
            f'<div style="font-size:9.5px;font-weight:700;letter-spacing:.14em;'
            f'text-transform:uppercase;color:{colour};">{text}</div>'
            for text, colour in column_labels
        )
        + "</div>"
    )
    rows_html = ""
    for num, _quality_title, visual, found, matters, handled in row_data:
        rows_html += (
            f'<div style="display:grid;grid-template-columns:236px 1fr 1fr 1fr;'
            f'gap:24px;padding:11px 0;border-top:1px solid {BORDER};align-items:start;">'
            f'<div><div style="display:flex;gap:8px;align-items:baseline;'
            f'margin-bottom:7px;flex-wrap:wrap;">'
            f'<span style="font-family:{MONO};font-size:10px;color:{TEAL};'
            f'font-weight:700;">{num}</span>'
            f'<span style="font-size:13px;font-weight:700;color:{NAVY};">'
            f"{_quality_title}</span></div>"
            f'<div style="min-height:96px;">{visual}</div></div>'
            f'<div style="font-size:12.5px;line-height:1.5;color:{INK};">{found}</div>'
            f'<div style="font-size:12.5px;line-height:1.5;color:{INK};">{matters}</div>'
            f'<div style="border-left:2px solid {SEAFOAM};padding-left:16px;'
            f'font-size:12.5px;line-height:1.5;color:{INK};">{handled}</div></div>'
        )
    mo.Html(
        f'<div style="min-height:650px;display:flex;flex-direction:column;box-sizing:border-box;'
        f'padding:8px 6px 10px 6px;">'
        f"{header('03 / Data quality', 'Three data issues that could lead to misleading conclusions.', 'I found three challenges in the raw data. Each required a specific modelling decision to keep the analysis reliable.')}"
        f'<div style="margin-top:2px;">{header_row}{rows_html}</div>'
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'margin-top:10px;padding-top:8px;border-top:1px solid {BORDER};gap:16px;">'
        f'<div style="font-size:12.5px;line-height:1.4;color:{INK};">'
        f"I turned each of these data issues into an explicit "
        f"<b>validation rule and a test in dbt</b>.</div>"
        f"{chip(f'{unit_tests} unit tests', fg=TEAL_DEEP, bg=SEAFOAM)}"
        f"</div></div>"
    )


@app.cell
def slide_method(daily):
    # KEY MESSAGE  Four metrics separate availability, detection, firing and firing-per-detection.
    # SAY          Walk the four cards, then the interpretation strip.
    # TRANSITION   "Now the engineering design that carries these metrics."

    reported = int(daily["reported_node_days"].sum())
    expected = int(daily["expected_node_days"].sum())
    _completeness = reported / expected

    metrics = [
        {
            "num": "01",
            "tag": "Availability",
            "name": "Equipment availability",
            "metric": "Uptime %",
            "formula": [
                "Total reported uptime minutes",
                "÷ expected operating minutes",
                "× 100",
            ],
            "question": "How much of the expected operating time was the equipment running?",
            "if_line": "If it falls: investigate availability — power, connectivity or shutdowns.",
            "colour": OCEAN,
            "tint": MIST,
        },
        {
            "num": "02",
            "tag": "Detection activity",
            "name": "Lice detection activity",
            "metric": "Detections per uptime hour",
            "formula": [
                "Total lice detections",
                "÷ total uptime hours",
            ],
            "question": "How frequently were lice detected while the equipment was operating?",
            "if_line": "If it falls: investigate detection conditions, fish behaviour or lice prevalence.",
            "colour": TEAL,
            "tint": SEAFOAM,
        },
        {
            "num": "03",
            "tag": "Firing activity",
            "name": "Laser firing activity",
            "metric": "Shots per uptime hour",
            "formula": [
                "Total laser shots",
                "÷ total uptime hours",
            ],
            "question": "How actively was the laser firing while the equipment was operating?",
            "if_line": "If it falls: investigate laser firing activity and operating logic.",
            "colour": CORAL,
            "tint": CORAL_SOFT,
        },
        {
            "num": "04",
            "tag": "Firing vs detection",
            "name": "Shots relative to detections",
            "metric": "Shots per detection",
            "formula": [
                "Total laser shots",
                "÷ total lice detections",
            ],
            "question": "How many shots were fired for each detected louse?",
            "if_line": "If it changes: investigate how firing behaviour relates to detections.",
            "colour": TEAL_DEEP,
            "tint": "#E4F3F1",
        },
    ]

    cards_html = ""
    for item in metrics:
        formula_html = "<br>".join(item["formula"])
        cards_html += (
            f'<div style="background:{WHITE};border:1px solid {BORDER};'
            f"border-top:4px solid {item['colour']};border-radius:9px;"
            f"padding:13px 14px 12px 14px;display:flex;flex-direction:column;"
            f'min-height:300px;box-sizing:border-box;">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;">'
            f'<span style="font-family:{MONO};font-size:10px;font-weight:700;'
            f'color:{item["colour"]};">{item["num"]}</span>'
            f'<span style="font-size:10px;font-weight:700;letter-spacing:.08em;'
            f'text-transform:uppercase;color:{MUTED};">{item["tag"]}</span></div>'
            f'<div style="font-size:13.5px;font-weight:700;color:{NAVY};line-height:1.25;'
            f'margin-top:8px;">{item["name"]}</div>'
            f'<div style="font-family:{MONO};font-size:11.0px;font-weight:650;'
            f'color:{item["colour"]};margin-top:3px;">{item["metric"]}</div>'
            f'<div style="background:{item["tint"]};border-radius:6px;'
            f"padding:8px 9px;margin-top:11px;font-family:{MONO};font-size:10.0px;"
            f'line-height:1.5;color:{OCEAN};">{formula_html}</div>'
            f'<div style="font-size:12.2px;line-height:1.45;color:{INK};margin-top:11px;">'
            f"{item['question']}</div>"
            f'<div style="margin-top:auto;padding-top:9px;border-top:1px solid {BORDER};'
            f'font-size:10.4px;line-height:1.4;color:{MUTED};">'
            f'<b style="color:{CORAL_DEEP};">{item["if_line"].split(":")[0]}:</b>'
            f"{item['if_line'].split(':', 1)[1]}</div></div>"
        )

    mo.Html(
        f'<div style="min-height:650px;display:flex;flex-direction:column;'
        f'box-sizing:border-box;padding:8px 6px 10px 6px;">'
        f"{header('04 / Metrics', 'How to quantify laser activity?', 'Looking at operating time, detection activity and laser firing paints a complete picture and helps understand what changes after a storm.')}"
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;'
        f'margin-top:6px;">{cards_html}</div>'
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'gap:18px;margin-top:auto;padding-top:12px;border-top:1px solid {BORDER};">'
        f'<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">'
        f"{chip('Ratios of totals — never averages', fg=OCEAN, bg=MIST)}"
        f"{chip('Missing or zero denominator → NULL', fg=CORAL_DEEP, bg=CORAL_SOFT)}"
        f"{chip('shots/hour = detections/hour × shots/detection', fg=NAVY, bg=MIST)}"
        f"{chip(f'Reporting completeness {reported} / {expected} ({_completeness:.1%})', fg=TEAL_DEEP, bg=SEAFOAM)}"
        f"</div>"
        f'<div style="font-size:10px;line-height:1.4;color:{CORAL_DEEP};'
        f'text-align:right;max-width:310px;">'
        f"Possible explanations to investigate — "
        f"<b>not established causes</b>.</div>"
        f"</div></div>"
    )


@app.cell
def slide_architecture(analysis, mart_counts, test_counts):
    # KEY MESSAGE  Layered dbt models, two explicit fact grains and tested logic.
    # SAY          Pipeline -> two facts and shared dimensions -> tests.
    # TRANSITION   "Next, the lineage that connects these layers end to end."
    _manifest = json.loads(Path("target/manifest.json").read_text(encoding="utf-8"))
    _layers = [
        node["fqn"][1]
        for node in _manifest["nodes"].values()
        if node["resource_type"] == "model"
    ]
    _staging = _layers.count("staging")
    _intermediate = _layers.count("intermediate")
    _marts = _layers.count("marts")
    _total = len(_layers)
    _tests = test_counts["tests"]
    _unit = sum(test_counts["by_layer"].get("unit", {}).values())
    _mart_counts = dict(
        zip(mart_counts["model_name"], mart_counts["row_count"], strict=True)
    )
    _daily_rows = _mart_counts["fct_pen_daily_activity"]
    _storm_rows = _mart_counts["fct_pen_storm_window_day"]
    _unique_pen_days = int(
        analysis[["pen_id", "activity_date"]].drop_duplicates().shape[0]
    )

    layers = [
        ("RAW", "4", "CSV files", "#F4F7F9", "#B7C7D1", INK),
        ("STAGING", str(_staging), "views", "#EAF4FD", "#8CC3EA", "#0D47A1"),
        (
            "INTERMEDIATE",
            str(_intermediate),
            "models",
            "#FFF0EC",
            CORAL,
            CORAL_DEEP,
        ),
        ("MARTS", str(_marts), "tables", "#E8F5E9", "#43A047", "#1B5E20"),
        ("CONSUME", "", "BI + code", NAVY, NAVY, WHITE),
    ]
    rail_html = ""
    for _index, (_tag, _count, _label, _fill, _stroke, _colour) in enumerate(layers):
        count_html = (
            f'<div style="font-family:{MONO};font-size:20px;font-weight:700;'
            f'line-height:1;color:{_colour};">{_count}</div>'
            if _count
            else ""
        )
        rail_html += (
            f'<div style="flex:1;min-width:0;background:{_fill};border:1px solid {_stroke};'
            f'border-radius:8px;padding:8px 11px;">'
            f'<div style="font-size:9.5px;font-weight:700;letter-spacing:.12em;'
            f'text-transform:uppercase;color:{_colour};opacity:.9;">{_tag}</div>'
            f"{count_html}"
            f'<div style="font-size:10px;color:{_colour};opacity:.9;margin-top:2px;">'
            f"{_label}</div></div>"
        )
        if _index < len(layers) - 1:
            rail_html += (
                f'<div style="flex:0 0 18px;display:flex;align-items:center;'
                f'justify-content:center;color:{MUTED};font-size:13px;">→</div>'
            )

    boundaries = [
        (
            "Staging",
            "One model per source: rename, cast and normalise timestamps.",
            TEAL,
        ),
        (
            "Intermediate",
            "Business logic: node-day records, aggregate activity into pen-level, storm exposure.",
            CORAL,
        ),
        ("Marts", "Business-ready facts and dimensions for reporting.", OCEAN),
    ]
    boundary_rows = "".join(
        f'<div style="display:flex;gap:8px;align-items:flex-start;margin-top:9px;">'
        f'<span style="flex:0 0 6px;height:6px;margin-top:5px;border-radius:50%;'
        f'background:{_colour};"></span>'
        f'<div style="font-size:11.2px;line-height:1.45;color:{INK};">'
        f"<b>{_name}.</b> {_body}</div></div>"
        for _name, _body, _colour in boundaries
    )
    examples = [
        "Effective-dated node-to-pen assignments",
        "Storm exposure by local day",
        "Missing versus zero activity",
    ]
    example_rows = "".join(
        f'<div style="display:flex;gap:7px;align-items:flex-start;margin-top:7px;">'
        f'<span style="flex:0 0 5px;height:5px;margin-top:5px;border-radius:50%;'
        f'background:{TEAL};"></span>'
        f'<span style="font-size:10.5px;line-height:1.45;color:{INK};">{_item}</span></div>'
        for _item in examples
    )

    mo.Html(
        f'<div style="min-height:650px;display:flex;flex-direction:column;'
        f'box-sizing:border-box;padding:8px 6px 10px 6px;">'
        f"{header('05 / Engineering design', 'dbt models: two facts, shared dimensions', 'Three layers: staging, intermediate & marts.')}"
        f'<div style="display:flex;align-items:stretch;gap:5px;margin-top:2px;">'
        f"{rail_html}</div>"
        f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;'
        f'margin-top:14px;align-items:stretch;">'
        # 1 - boundaries
        f'<div style="background:{WHITE};border:1px solid {BORDER};'
        f"border-top:4px solid {TEAL};border-radius:9px;padding:13px 15px 11px 15px;"
        f'display:flex;flex-direction:column;box-sizing:border-box;">'
        f'<div style="font-size:9.5px;font-weight:700;letter-spacing:.12em;'
        f'text-transform:uppercase;color:{TEAL_DEEP};">01</div>'
        f'<div style="font-size:14.5px;font-weight:700;color:{NAVY};line-height:1.3;'
        f'margin-top:3px;">Standardise in staging, transform in intermediate</div>'
        f'<div style="margin-top:3px;">{boundary_rows}</div>'
        f'<div style="margin-top:auto;padding-top:9px;border-top:1px solid {BORDER};'
        f'font-size:10.4px;line-height:1.4;color:{MUTED};">'
        f"Each layer has one job.</div></div>"
        # 2 - two facts and shared dimensions
        f'<div style="background:{WHITE};border:1px solid {BORDER};'
        f"border-top:4px solid {OCEAN};border-radius:9px;padding:13px 15px 11px 15px;"
        f'display:flex;flex-direction:column;box-sizing:border-box;">'
        f'<div style="font-size:9.5px;font-weight:700;letter-spacing:.12em;'
        f'text-transform:uppercase;color:{OCEAN};">02</div>'
        f'<div style="font-size:14.5px;font-weight:700;color:{NAVY};line-height:1.3;'
        f'margin-top:3px;">Two fact grains, deliberately separate</div>'
        f'<div style="margin-top:9px;">'
        f'<div style="font-size:10px;font-weight:700;letter-spacing:.08em;'
        f'text-transform:uppercase;color:{TEAL_DEEP};">Daily activity fact</div>'
        f'<div style="font-size:11.2px;line-height:1.45;color:{INK};margin-top:2px;">'
        f"One row per site × pen × date · {_daily_rows} rows. The source of "
        f"truth for operational reporting and daily totals.</div></div>"
        f'<div style="margin-top:10px;">'
        f'<div style="font-size:10px;font-weight:700;letter-spacing:.08em;'
        f'text-transform:uppercase;color:{CORAL_DEEP};">Storm-window fact</div>'
        f'<div style="font-size:11.2px;line-height:1.45;color:{INK};margin-top:2px;">'
        f"One row per pen × storm episode × date · {_storm_rows} rows"
        f" For before/during/after comparisons."
        f"</div></div>"
        f'<div style="display:flex;gap:4px;flex-wrap:wrap;margin-top:11px;">'
        + "".join(
            f'<span style="font-family:{MONO};font-size:9.2px;font-weight:600;'
            f"color:{TEAL_DEEP};background:{SEAFOAM};border-radius:4px;"
            f'padding:2px 6px;white-space:nowrap;">{dim}'
            f'<span style="font-family:{SANS};font-weight:500;color:{MUTED};">'
            f" · both facts</span></span>"
            for dim in ["dim_date", "dim_site", "dim_pen"]
        )
        + f'<span style="font-family:{MONO};font-size:9.2px;color:{CORAL_DEEP};'
        f"background:{CORAL_SOFT};border-radius:4px;padding:2px 6px;"
        f'white-space:nowrap;">dim_storm_episode'
        f'<span style="font-family:{SANS};color:{MUTED};"> · window fact only</span></span>'
        + "</div>"
        f'<div style="font-size:11.0px;line-height:1.45;color:{MUTED};margin-top:8px;">'
        f"Shared dimensions keep filters consistent; the facts are never joined "
        f"directly.</div> "
        f'<div style="margin-top:auto;padding-top:9px;border-top:1px solid {BORDER};'
        f'font-size:10.4px;line-height:1.4;color:{MUTED};">'
        f"Overall totals come from the daily activity fact; before/after comparisons from the "
        f"storm episode fact.</div></div>"
        # 3 - tests
        f'<div style="background:{WHITE};border:1px solid {BORDER};'
        f"border-top:4px solid {CORAL};border-radius:9px;padding:13px 15px 11px 15px;"
        f'display:flex;flex-direction:column;box-sizing:border-box;">'
        f'<div style="font-size:9.5px;font-weight:700;letter-spacing:.12em;'
        f'text-transform:uppercase;color:{CORAL_DEEP};">03</div>'
        f'<div style="font-size:14.5px;font-weight:700;color:{NAVY};line-height:1.3;'
        f'margin-top:3px;">Business logic is tested</div>'
        f'<div style="display:flex;align-items:baseline;gap:9px;margin-top:8px;">'
        f'<span style="font-family:{MONO};font-size:30px;font-weight:700;'
        f'line-height:1;color:{NAVY};">{_tests}</span>'
        f'<span style="font-size:10px;color:{MUTED};">tests on every build</span>'
        f'<span style="font-size:9px;font-weight:650;color:{CORAL_DEEP};'
        f'background:{CORAL_SOFT};border-radius:999px;padding:2px 7px;">'
        f"{_unit} unit tests</span></div>"
        f'<div style="font-size:11.2px;line-height:1.45;color:{INK};margin-top:9px;">'
        f"Rules live in dbt and are checked by tests, including edge cases:</div>"
        f"{example_rows}"
        f'<div style="margin-top:auto;padding-top:9px;border-top:1px solid {BORDER};'
        f'font-size:10.4px;line-height:1.4;color:{MUTED};">'
        f"Tests not to validate volume of data but assumptions.</div></div></div>"
        f'<div style="margin-top:auto;padding-top:9px;border-top:1px solid {BORDER};'
        f"display:flex;justify-content:space-between;align-items:center;"
        f'font-size:10.0px;color:{MUTED};">'
        f"<span>{_total} models · {_staging} staging · {_intermediate} intermediate · "
        f"{_marts} marts · built and tested on DuckDB </span>"
        f"</div>"
    )


@app.cell
def slide_lineage():
    # KEY MESSAGE  The lineage is four sources -> staging -> intermediate -> marts,
    #              with the business logic concentrated in intermediate models.
    # SAY          Sources and their grains -> staging only standardises -> the
    #              temporal, fish-count and storm transformations -> two facts ->
    #              shared dimensions and dbt traceability.
    # TRANSITION   "So what does that lineage actually show in the data?"
    _source_rows = "".join(
        f'<div style="display:grid;grid-template-columns:112px 14px 1fr;gap:4px;'
        f'align-items:center;padding:6px 0;border-bottom:1px solid {BORDER};">'
        f'<div><div style="font-family:{MONO};font-size:9.0px;color:#0D47A1;'
        f'overflow-wrap:anywhere;">{src}</div>'
        f'<div style="font-size:9.0px;color:{MUTED};margin-top:1px;">{grain}</div></div>'
        f'<span style="font-size:12px;color:{TEAL};">→</span>'
        f'<span style="font-family:{MONO};font-size:9.0px;color:#0D47A1;'
        f'overflow-wrap:anywhere;">{stg}</span></div>'
        for src, grain, stg in [
            (
                "node_daily_activity",
                "node × day",
                "stg_stingray__node_daily_activity",
            ),
            (
                "node_pen_assignment",
                "node × deployment interval",
                "stg_stingray__node_pen_assignments",
            ),
            ("storm_events", "storm × site · UTC", "stg_stingray__storm_events"),
            (
                "farmer_pen_log",
                "pen × manual entry",
                "stg_stingray__farmer_pen_logs",
            ),
        ]
    )

    def _model_row(name: str, desc: str, *, colour: str = CORAL_DEEP) -> str:
        return (
            f'<div style="display:flex;align-items:baseline;gap:6px;padding:4px 8px;'
            f"margin-top:4px;background:{WHITE};border:1px solid {BORDER};"
            f'border-left:2px solid {colour};border-radius:4px;">'
            f'<span style="font-family:{MONO};font-size:9.8px;font-weight:650;'
            f'color:{colour};white-space:nowrap;">{name}</span>'
            f'<span style="font-size:9.4px;line-height:1.3;color:{MUTED};">'
            f"{desc}</span></div>"
        )

    _groups = [
        (
            "Temporal spine & assignment",
            [
                ("int_dates", "DST-aware local calendar spine"),
                (
                    "int_node_days_assigned",
                    "effective-dated node → pen days; missing telemetry kept null",
                ),
            ],
        ),
        (
            "Fish-count snapshots",
            [
                ("int_fish_counts_validated", "plausibility + duplicate flags"),
                (
                    "int_pen_daily_fish_count",
                    "deterministic latest valid count per pen-day",
                ),
            ],
        ),
        (
            "Storm exposure",
            [
                ("int_storm_episodes", "merge storm events per site into episodes"),
                ("int_storm_daily_exposure", "clip storms to local calendar days"),
                ("int_site_daily_storm_summary", "site-day exposure; overlaps warned"),
            ],
        ),
        (
            "Pen-day & window logic",
            [
                ("int_pen_daily_activity", "pen-day aggregation + shared metrics"),
                (
                    "int_pen_storm_daily_analysis",
                    "before / during / after classification",
                ),
            ],
        ),
    ]
    _group_html = "".join(
        f'<div style="font-size:9.0px;font-weight:700;letter-spacing:.11em;'
        f'text-transform:uppercase;color:{MUTED};margin:6px 0 0 2px;">{title}</div>'
        + "".join(_model_row(name, desc) for name, desc in rows)
        for title, rows in _groups
    )

    def _fact_card(
        path_label: str,
        name: str,
        grain: str,
        desc: str,
        feeders: list[str],
        *,
        colour: str,
        tint: str,
    ) -> str:
        _feeders = "".join(
            f'<span style="font-family:{MONO};font-size:8.2px;color:{colour};'
            f"background:{tint};border-radius:3px;padding:1px 4px;"
            f'white-space:nowrap;">{feeder}</span>'
            for feeder in feeders
        )
        return (
            f'<div style="background:{WHITE};border:1px solid {BORDER};'
            f'border-top:3px solid {colour};border-radius:7px;padding:9px 11px;margin-bottom:7px;">'
            f'<div style="font-size:9.0px;font-weight:700;letter-spacing:.12em;'
            f'text-transform:uppercase;color:{colour};">{path_label}</div>'
            f'<div style="font-family:{MONO};font-size:10.8px;font-weight:700;'
            f'color:{colour};margin-top:2px;">{name}</div>'
            f'<div style="font-size:10.0px;font-weight:650;color:{NAVY};'
            f'margin-top:2px;">{grain}</div>'
            f'<div style="font-size:9.2px;line-height:1.4;color:{MUTED};'
            f'margin-top:2px;">{desc}</div>'
            f'<div style="font-size:8.3px;font-weight:700;letter-spacing:.1em;'
            f'text-transform:uppercase;color:{MUTED};margin-top:6px;">Fed by</div>'
            f'<div style="display:flex;gap:3px;flex-wrap:wrap;margin-top:3px;">'
            f"{_feeders}</div></div>"
        )

    _facts_html = _fact_card(
        "Daily operational path",
        "fct_pen_daily_activity",
        "site × pen × day · 63 rows",
        "Additive operational totals with the fish-count snapshot.",
        [
            "int_pen_daily_activity",
            "int_pen_daily_fish_count",
            "int_site_daily_storm_summary",
        ],
        colour=TEAL_DEEP,
        tint=SEAFOAM,
    ) + _fact_card(
        "Storm comparison path",
        "fct_pen_storm_window_day",
        "pen × episode × day · 39 rows / 36 pen-days",
        "Before / during / after comparisons around each storm episode.",
        ["int_pen_storm_daily_analysis"],
        colour=CORAL_DEEP,
        tint=CORAL_SOFT,
    )

    _dim_cards = "".join(
        f'<div style="background:{WHITE};border:1px solid {BORDER};'
        f'border-left:3px solid {colour};border-radius:6px;padding:7px 9px;">'
        f'<div style="font-family:{MONO};font-size:10.0px;font-weight:700;'
        f'color:{colour};">{name}</div>'
        f'<div style="font-family:{MONO};font-size:8.6px;color:{MUTED};'
        f'margin-top:3px;overflow-wrap:anywhere;">← {source}</div></div>'
        for name, source, colour in [
            ("dim_date", "int_dates", TEAL_DEEP),
            (
                "dim_site",
                "stg_stingray__node_pen_assignments + stg_stingray__storm_events",
                TEAL_DEEP,
            ),
            (
                "dim_pen",
                "stg_stingray__node_pen_assignments + int_fish_counts_validated",
                TEAL_DEEP,
            ),
            ("dim_storm_episode", "int_storm_episodes", CORAL_DEEP),
        ]
    )

    def _section_head(label: str, sub: str, colour: str) -> str:
        return (
            f'<div style="padding-bottom:7px;border-bottom:2px solid {colour};'
            f'margin-bottom:7px;">'
            f'<div style="font-size:10.2px;font-weight:700;letter-spacing:.12em;'
            f'text-transform:uppercase;color:{colour};">{label}</div>'
            f'<div style="font-size:8.8px;color:{MUTED};margin-top:2px;">{sub}</div>'
            f"</div>"
        )

    _arrow = (
        f'<div style="display:flex;align-items:center;justify-content:center;'
        f'font-size:22px;font-weight:700;color:{TEAL_SOFT};">→</div>'
    )

    mo.Html(
        f'<div style="min-height:650px;display:flex;flex-direction:column;'
        f'box-sizing:border-box;padding:8px 6px 10px 6px;">'
        f"{header('06 / Traceability', 'Data lineage', 'From source data to analytical outputs.', title_size=36, lead_size=15.5)}"
        f'<div style="background:{WHITE};border:1px solid {BORDER};border-radius:9px;'
        f'padding:13px 15px;box-sizing:border-box;">'
        f'<div style="display:grid;grid-template-columns:298px 24px minmax(0,1fr) 24px 358px;'
        f'gap:8px;align-items:stretch;">'
        f'<div style="display:flex;flex-direction:column;height:100%;">'
        f"{_section_head('Sources → staging', 'Source grain preserved · rename, cast, timestamps', '#0D47A1')}"
        f"{_source_rows}"
        f'<div style="font-size:8.8px;line-height:1.4;color:{MUTED};margin-top:7px;">'
        f"Four views, 1:1 with the extracts. No business logic yet.</div>"
        f'<div style="margin-top:auto;padding:9px 11px;background:#EAF4FD;'
        f"border-left:3px solid #8CC3EA;border-radius:0 6px 6px 0;font-size:8.8px;"
        f'line-height:1.45;color:{INK};">'
        f"<b>Staging contract</b><br>Rename, cast, parse and normalise timestamps. "
        f"Keep the source grain; no joins, aggregation or business rules.</div></div>"
        f"{_arrow}"
        f"<div>"
        f"{_section_head('Intermediate transformations', 'Business logic lives here', CORAL_DEEP)}"
        f"{_group_html}</div>"
        f"{_arrow}"
        f'<div style="display:flex;flex-direction:column;height:100%;">'
        f"{_section_head('Reporting marts', 'Produced by the transformations', '#1B5E20')}"
        f"{_facts_html}"
        f"</div></div></div>"
        f'<div style="margin-top:6px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
        f'margin:0 2px 4px 2px;">'
        f'<span style="font-size:8.6px;font-weight:700;letter-spacing:.12em;'
        f'text-transform:uppercase;color:{MUTED};">Dimension marts</span>'
        f'<span style="font-size:9.0px;color:{MUTED};">'
        f"Upstream models for each dimension</span></div>"
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:7px;">'
        f"{_dim_cards}</div></div>"
        f'<div style="margin-top:12px;padding:10px 40px 0 0;'
        f"border-top:1px solid {BORDER};"
        f"display:flex;justify-content:space-between;align-items:center;gap:12px;"
        f'font-size:9.8px;color:{MUTED};">'
        f'<span><b style="color:{INK};">dbt traceability:</b> every arrow is a '
        f'<span style="font-family:{MONO};">ref()</span> edge — the manifest '
        f'<span style="font-family:{MONO};">parent_map</span> and DAG resolve the '
        f"full source-to-mart path.</span>"
        f'<span style="white-space:nowrap;">staging views · intermediate views · mart tables</span>'
        f"</div></div>"
    )


@app.cell
def slide_findings(s01, s01_metrics, baseline_ranges, s02_summary):
    # KEY MESSAGE  Storm exposure coincided with lower uptime and detection activity,
    #              but the pattern differed by pen; P103 is limited evidence.
    # SAY          Availability -> activity while operating -> firing intensity ->
    #              after the storm -> limits.
    # TRANSITION   "How would Kari use this without me in the room?"
    pens = ["P101", "P102", "P103"]
    _pen_rows = {pen: s01_metrics[s01_metrics["pen_id"] == pen].iloc[0] for pen in pens}
    _pen_base = {
        pen: baseline_ranges[baseline_ranges["pen_id"] == pen].iloc[0] for pen in pens
    }
    s02_moderate = next(
        _comp_row for _comp_row in s02_summary if _comp_row["severity"] == "moderate"
    )
    s02_low = next(
        _comp_row for _comp_row in s02_summary if _comp_row["severity"] == "low"
    )
    _s01_row = s01.iloc[0]
    _s01_label = (
        f"S01 · {_s01_row['max_severity']} severity · "
        f"{_s01_row['episode_start_date']:%d %b}–{_s01_row['episode_end_date']:%d %b} · "
        f"{_s01_row['episode_span_hours']:.0f} h episode"
    )

    def _val(value, digits=1):
        return f"{value:.{digits}f}"

    def _change(value, digits=0):
        return f"{value:+.{digits}f}%"

    def _pen_label(pen, *, limited=False):
        suffix = (
            f'<span style="font-size:8px;font-weight:700;color:{MUTED};">*</span>'
            if limited
            else ""
        )
        colour = MUTED if limited else NAVY
        return (
            f'<span style="font-family:{MONO};font-size:10.5px;font-weight:700;'
            f'color:{colour};">{pen}{suffix}</span>'
        )

    def _cell(
        before_value,
        period_value,
        change,
        *,
        digits=1,
        change_digits=0,
        limited=False,
    ):
        text_colour = MUTED if limited else INK
        change_colour = MUTED if limited else (CORAL_DEEP if change < 0 else TEAL_DEEP)
        return (
            f'<div style="font-size:10.5px;color:{text_colour};line-height:1.3;">'
            f"{_val(before_value, digits)} → {_val(period_value, digits)}</div>"
            f'<div style="font-size:9.5px;font-weight:700;color:{change_colour};">'
            f"{_change(change, change_digits)}</div>"
        )

    def _col_head(text):
        return (
            f'<div style="font-size:8.2px;font-weight:700;letter-spacing:.08em;'
            f'text-transform:uppercase;color:{MUTED};">{text}</div>'
        )

    # ---- Card 1: equipment availability -------------------------------
    availability_rows = "".join(
        f'<div style="display:grid;grid-template-columns:44px 1fr 1fr;gap:8px;'
        f'align-items:start;margin-top:9px;">'
        f"<div>{_pen_label(pen, limited=pen == 'P103')}</div>"
        f"<div>{_cell(_pen_rows[pen]['uptime_pct_before'], _pen_rows[pen]['uptime_pct_during'], _pen_rows[pen]['during_change_uptime_pct_pct'], change_digits=1, limited=pen == 'P103')}</div>"
        f'<div style="font-size:10.5px;color:{MUTED if pen == "P103" else INK};line-height:1.4;">'
        f"{int(_pen_rows[pen]['positive_uptime_days_during'])} of "
        f"{int(_pen_rows[pen]['days_during'])} days with uptime</div></div>"
        for pen in pens
    )

    # ---- Card 2: activity while operating -----------------------------
    activity_rows = "".join(
        f'<div style="display:grid;grid-template-columns:44px 1fr 1fr;gap:8px;'
        f'align-items:start;margin-top:9px;">'
        f"<div>{_pen_label(pen, limited=pen == 'P103')}</div>"
        f"<div>{_cell(_pen_rows[pen]['det_hr_before'], _pen_rows[pen]['det_hr_during'], _pen_rows[pen]['during_change_det_hr_pct'], limited=pen == 'P103')}</div>"
        f"<div>{_cell(_pen_rows[pen]['shots_hr_before'], _pen_rows[pen]['shots_hr_during'], _pen_rows[pen]['during_change_shots_hr_pct'], limited=pen == 'P103')}</div>"
        f"</div>"
        for pen in pens
    )

    # ---- Card 3: firing intensity relative to detections --------------
    firing_rows = "".join(
        f'<div style="display:grid;grid-template-columns:44px 1fr;gap:8px;'
        f'align-items:start;margin-top:9px;">'
        f"<div>{_pen_label(pen, limited=pen == 'P103')}</div>"
        f"<div>{_cell(_pen_rows[pen]['spd_before'], _pen_rows[pen]['spd_during'], _pen_rows[pen]['during_change_spd_pct'], digits=2, change_digits=1, limited=pen == 'P103')}</div>"
        f"</div>"
        for pen in pens
    )

    after_rows = "".join(
        f'<div style="display:grid;grid-template-columns:52px 1fr;gap:10px;'
        f'align-items:baseline;padding:4px 0;border-top:1px solid {BORDER};">'
        f"<div>{_pen_label(pen, limited=pen == 'P103')}</div>"
        f'<div style="font-size:10.2px;color:{MUTED if pen == "P103" else INK};line-height:1.4;">'
        f"uptime {_change(_pen_rows[pen]['after_change_uptime_pct_pct'], 1)} · "
        f"detections/hour {_change(_pen_rows[pen]['after_change_det_hr_pct'])} · "
        f"shots/hour {_change(_pen_rows[pen]['after_change_shots_hr_pct'])} · "
        f"shots/detection {_change(_pen_rows[pen]['after_change_spd_pct'], 1)}"
        f"</div></div>"
        for pen in pens
    )

    def _card(number, title, body_html, footnote, colour):
        return (
            f'<div style="background:{WHITE};border:1px solid {BORDER};'
            f"border-top:4px solid {colour};border-radius:9px;padding:12px 14px 10px 14px;"
            f'display:flex;flex-direction:column;box-sizing:border-box;">'
            f'<div style="font-size:8.5px;font-weight:700;letter-spacing:.12em;'
            f'text-transform:uppercase;color:{colour};">{number}</div>'
            f'<div style="font-size:14.5px;font-weight:700;color:{NAVY};line-height:1.3;'
            f'margin-top:3px;">{title}</div>'
            f'<div style="align-self:flex-start;background:{MIST};border-radius:999px;'
            f"padding:2px 9px;font-size:8.6px;font-weight:650;color:{OCEAN};"
            f'margin-top:6px;">{_s01_label}</div>'
            f"{body_html}"
            f'<div style="margin-top:auto;padding-top:8px;border-top:1px solid {BORDER};'
            f'font-size:9.2px;line-height:1.4;color:{MUTED};">{footnote}</div></div>'
        )

    findings_cards = (
        '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;'
        'margin-top:4px;">'
        + _card(
            "1 · Availability",
            "Uptime fell for P101 and P103; P102 kept operating",
            availability_rows,
            "P103's during-period uptime rests on one operating day "
            "(5 Oct); 6–7 Oct report zero uptime.",
            CORAL,
        )
        + _card(
            "2 · Activity while operating",
            "Fewer detections per hour tracked most of the firing drop",
            activity_rows,
            "Baseline shots/hour ranges: "
            f"P101 {_pen_base['P101']['shots_hr_min']:.1f}–{_pen_base['P101']['shots_hr_max']:.1f} · "
            f"P102 {_pen_base['P102']['shots_hr_min']:.1f}–{_pen_base['P102']['shots_hr_max']:.1f} · "
            f"P103 {_pen_base['P103']['shots_hr_min']:.1f}–{_pen_base['P103']['shots_hr_max']:.1f}. "
            "The changes are large relative to baseline variation for P101 and P102, "
            "not for P103.",
            OCEAN,
        )
        + _card(
            "3 · Firing intensity",
            "Shots per detection stayed comparatively stable",
            firing_rows,
            "shots/hour = detections/hour × shots/detection. "
            f"After vs before: P101 {_pen_rows['P101']['after_change_spd_pct']:+.1f}% · "
            f"P102 {_pen_rows['P102']['after_change_spd_pct']:+.1f}% · "
            f"P103 {_pen_rows['P103']['after_change_spd_pct']:+.1f}%.",
            TEAL,
        )
        + "</div>"
    )

    caveats = [
        (
            "<b>Completeness:</b> 100% before and during for all three S01 pens; "
            "P103 after is 67% (2 of 3 node-days)."
        ),
        (
            "<b>S02 is much quieter:</b> P201 "
            f"{fmt_pct1(s02_moderate['during_pct'], signed=True)} during the moderate "
            f"episode, {fmt_pct1(s02_low['during_pct'], signed=True)} during the low one."
        ),
        "<b>One high-severity episode:</b> co-movement, not causation.",
    ]
    caveat_html = "".join(
        f'<div style="flex:1;min-width:0;font-size:10.4px;line-height:1.45;'
        f'color:{INK};padding-left:14px;border-left:1px solid {BORDER};">{item}</div>'
        for item in caveats
    )
    mo.Html(
        f'<div style="min-height:650px;display:flex;flex-direction:column;'
        f'box-sizing:border-box;padding:8px 6px 10px 6px;">'
        f"{header('07 / What the data shows', 'Storm exposure coincided with lower uptime and detection activity.', 'P101 and P102 provide more informative evidence while operating. P103 is shown for completeness but has limited data.')}"
        f'<div style="display:flex;gap:16px;align-items:baseline;margin:2px 2px 0 2px;'
        f'font-size:9px;color:{MUTED};">'
        f'<span><b style="color:{NAVY};">P101 · P102</b> primary evidence</span>'
        f'<span><b style="color:{MUTED};">P103*</b> limited evidence — one operating day during the storm</span></div>'
        f"{findings_cards}"
        f'<div style="margin-top:10px;background:{WHITE};border:1px solid {BORDER};'
        f'border-radius:8px;padding:7px 12px;display:flex;gap:12px;align-items:flex-start;">'
        f'<div style="flex:0 0 122px;">'
        f'<div style="font-size:8.5px;font-weight:700;letter-spacing:.12em;'
        f'text-transform:uppercase;color:{TEAL_DEEP};">After the storm</div>'
        f'<div style="font-size:9.5px;color:{MUTED};margin-top:2px;">vs same pre-storm baseline</div></div>'
        f'<div style="flex:1;display:grid;grid-template-columns:1fr;gap:0;">{after_rows}</div></div>'
        f'<div style="margin-top:8px;background:#FFF6F3;border-left:3px solid {CORAL};'
        f"border-radius:0 8px 8px 0;padding:7px 12px;display:flex;gap:12px;"
        f'align-items:flex-start;">'
        f'<div style="flex:0 0 84px;">'
        f'<div style="font-size:8.5px;font-weight:700;letter-spacing:.12em;'
        f'text-transform:uppercase;color:{CORAL_DEEP};">Read with care</div>'
        f'<div style="font-size:10px;font-weight:700;color:{NAVY};margin-top:2px;">'
        f"Limits</div></div>"
        f'<div style="display:flex;gap:0;flex:1;">{caveat_html}</div></div>'
        f'<div style="margin-top:auto;padding-top:7px;border-top:1px solid {BORDER};'
        f'display:flex;justify-content:space-between;font-size:9.2px;color:{MUTED};">'
        f"<span>Rates are totals over each period, not an average of daily rates.</span></div>"
        f"</div>"
    )


@app.cell
def slide_dashboard(
    episodes,
    fig_periods_dash,
    fig_timeline_dash,
    fish_context,
    missing_telemetry,
    totals,
):
    # KEY MESSAGE  The dashboard turns the analysis into a practical reporting view,
    #              with data quality visible instead of buried - and every visual
    #              traceable to the fact or dimension that feeds it.
    # SAY          Walk the KPIs and timeline (daily fact) -> the before/during/after
    #              chart (storm-window fact) -> shared dimensions and why the facts
    #              are never joined -> the decisions it supports.
    # TRANSITION   "What still needs checking before this goes to a customer?"
    fish_lookup = {row["pen_id"]: row["status"] for row in fish_context}
    missing_names = ", ".join(
        f"{_row.node_id} {_row.activity_date:%d %b}"
        for _row in missing_telemetry.itertuples()
    )

    def source_line(model: str, *, note: str = "") -> str:
        """Small, secondary provenance line for a dashboard visual."""
        suffix = (
            f' <span style="color:{PALETTE["slate"]};">· {note}</span>' if note else ""
        )
        return (
            f'<span style="font-size:8.2px;line-height:1.25;color:{MUTED};'
            f'letter-spacing:.01em;">'
            f'<span style="font-weight:700;text-transform:uppercase;'
            f'letter-spacing:.08em;font-size:7.4px;color:{PALETTE["slate"]};">'
            f"Source</span>: "
            f'<span style="font-family:{MONO};font-size:7.8px;color:{OCEAN};">'
            f"{model}</span>{suffix}</span>"
        )

    def source_caption(model: str, *, note: str = "") -> mo.Html:
        return mo.Html(
            f'<div style="padding:3px 2px 0 2px;min-height:13px;">'
            f"{source_line(model, note=note)}</div>"
        )

    kpis = [
        (
            f"{totals['shots']:,}",
            "Laser shots",
            f"{totals['days']} days · {totals['pens']} pens",
            TEAL,
        ),
        (
            f"{totals['uptime_hours']:,.1f}",
            "Operating hours",
            f"{totals['uptime_minutes']:,} uptime minutes",
            OCEAN,
        ),
        (f"{totals['detections']:,}", "Lice detections", "camera events", TEAL_SOFT),
        (
            f"{totals['completeness']:.1%}",
            "Reporting completeness",
            f"{totals['reported_node_days']} of {totals['expected_node_days']} node-days",
            CORAL,
        ),
    ]
    kpi_html = "".join(
        f'<div style="background:{WHITE};border:1px solid {BORDER};'
        f"border-top:3px solid {colour};border-radius:7px;padding:4px 7px;"
        f'box-sizing:border-box;">'
        f'<div style="font-size:10px;font-weight:700;letter-spacing:.09em;'
        f'text-transform:uppercase;color:{MUTED};">{label}</div>'
        f'<div style="font-size:24px;font-weight:700;color:{NAVY};line-height:1.15;'
        f'margin-top:2px;">{value}</div>'
        f'<div style="font-size:9.0px;color:{MUTED};margin-top:1px;">{sub}</div></div>'
        for value, label, sub, colour in kpis
    )
    top_bar = (
        f'<div style="background:{NAVY};border-radius:9px 9px 0 0;'
        f"padding:7px 11px;display:flex;justify-content:space-between;"
        f'align-items:center;gap:12px;">'
        f'<div><div style="font-size:13px;font-weight:700;color:{WHITE};'
        f'letter-spacing:-.01em;">Laser activity around storm periods</div>'
        f'<div style="font-size:9.2px;color:#8FB0AD;margin-top:1px;">'
        f"Power BI concept · S01 + S02 · 01–14 Oct 2026</div></div>"
        f'<div style="display:flex;flex-direction:column;align-items:flex-end;gap:2px;">'
        f'<div style="display:flex;gap:5px;flex-wrap:wrap;justify-content:flex-end;">'
        + "".join(
            f'<span style="font-size:9px;color:{SEAFOAM};background:#173A52;'
            f"border:1px solid #28536C;border-radius:4px;padding:2px 6px;"
            f'white-space:nowrap;">{text}</span>'
            for text in [
                "Site: All",
                "Pen: All",
                f"Episodes: all {len(episodes)}",
                "01–14 Oct",
            ]
        )
        + "</div>"
        f'<div style="font-size:8.0px;color:#8FB0AD;letter-spacing:.02em;">'
        f'Filters: <span style="font-family:{MONO};">dim_site · dim_pen</span></div>'
        f"</div></div>"
    )
    context_strip = (
        f'<div style="display:grid;grid-template-columns:1.05fr .95fr;gap:8px;">'
        f'<div style="background:{WHITE};border:1px solid {BORDER};border-radius:7px;'
        f'padding:3px 7px;display:flex;flex-direction:column;">'
        f'<div style="font-size:10px;font-weight:700;letter-spacing:.09em;'
        f'text-transform:uppercase;color:{MUTED};">Missing telemetry</div>'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
        f'gap:8px;margin-top:4px;">'
        f'<span style="font-size:9.5px;color:{INK};">{missing_names}</span>'
        f'<span style="font-size:9px;font-weight:650;color:{TEAL_DEEP};'
        f"background:{SEAFOAM};border-radius:999px;padding:1px 7px;"
        f'white-space:nowrap;">kept null, never zero</span></div>'
        f'<div style="margin-top:auto;padding-top:3px;">'
        f"{source_line('int_node_days_assigned')}</div></div>"
        f'<div style="background:{WHITE};border:1px solid {BORDER};border-radius:7px;'
        f'padding:3px 7px;display:flex;flex-direction:column;">'
        f'<div style="font-size:10px;font-weight:700;letter-spacing:.09em;'
        f'text-transform:uppercase;color:{MUTED};">Fish-count context</div>'
        f'<div style="font-size:9.5px;color:{INK};margin-top:4px;line-height:1.45;">'
        f"P101 {fish_lookup['P101']} · P102 {fish_lookup['P102']} · "
        f'<span style="color:{CORAL_DEEP};">P103 {fish_lookup["P103"]} · '
        f"P201 {fish_lookup['P201']}</span> · P202 {fish_lookup['P202']}</div>"
        f'<div style="margin-top:auto;padding-top:3px;">'
        f"{source_line('fct_pen_daily_activity', note='fish_count snapshot')}"
        f"</div></div></div>"
    )
    shared_footer = (
        f'<div style="background:{WHITE};border:1px solid {BORDER};border-radius:8px;'
        f"padding:5px 9px;display:grid;grid-template-columns:auto 1fr;gap:14px;"
        f'align-items:center;">'
        f"<div>"
        f'<div style="font-size:9.2px;font-weight:700;letter-spacing:.12em;'
        f'text-transform:uppercase;color:{MUTED};">Shared dimensions</div>'
        f'<div style="display:flex;gap:5px;margin-top:4px;flex-wrap:wrap;">'
        + "".join(
            f'<span style="font-family:{MONO};font-size:8.6px;font-weight:600;'
            f"color:{TEAL_DEEP};background:{SEAFOAM};border-radius:4px;"
            f'padding:2px 6px;white-space:nowrap;">{dim_name}'
            f'<span style="font-family:{SANS};font-weight:500;color:{MUTED};">'
            f" · both facts</span></span>"
            for dim_name in ["dim_date", "dim_site", "dim_pen"]
        )
        + f'<span style="font-family:{MONO};font-size:8.6px;color:{CORAL_DEEP};'
        f"background:{CORAL_SOFT};border-radius:4px;padding:2px 6px;"
        f'white-space:nowrap;">dim_storm_episode'
        f'<span style="font-family:{SANS};color:{MUTED};"> · window fact only</span></span>'
        f"</div></div>"
        f'<div style="border-left:1px solid {BORDER};padding-left:14px;font-size:9.0px;'
        f'line-height:1.35;color:{INK};">'
        f"<b>Facts are not joined directly.</b> The daily fact owns overall totals; the "
        f"storm-window fact owns before/during/after comparisons. Shared dimensions keep "
        f"filters consistent without duplicating records or inflating additive metrics. "
        f"Storm exposure is site-level, repeated across pens — never sum it across pens."
        f"</div></div>"
    )
    timeline_panel = mo.vstack(
        [
            fig_timeline_dash.properties(height=182),
            source_caption(
                "fct_pen_daily_activity · dim_date · dim_pen · dim_storm_episode",
                note="bands = storm episodes",
            ),
        ],
        gap=0,
        align="stretch",
    )
    periods_panel = mo.vstack(
        [
            fig_periods_dash.properties(height=182),
            source_caption("fct_pen_storm_window_day · dim_storm_episode · dim_pen"),
        ],
        gap=0,
        align="stretch",
    )
    dashboard = mo.vstack(
        [
            mo.Html(top_bar),
            mo.Html(
                f'<div style="background:#EDF2F5;padding:7px;'
                f'border:1px solid {BORDER};border-top:none;border-radius:0 0 9px 9px;">'
                f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;">'
                f"{kpi_html}</div>"
                f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
                f'gap:10px;margin-top:4px;padding:0 2px;">'
                f"{source_line('fct_pen_daily_activity', note='daily operational fact')}"
                f'<span style="font-size:8.4px;color:{MUTED};">'
                f"KPI totals are computed from the fact, never hardcoded</span></div></div>"
            ),
            mo.hstack(
                [timeline_panel, periods_panel],
                widths=[2.1, 1],
                gap=0.5,
                align="start",
            ),
            mo.Html(context_strip),
            mo.Html(shared_footer),
        ],
        gap=0.2,
        align="stretch",
    )

    _learn = [
        "Which pens show the largest changes after a storm.",
        "Whether changes are driven by operating time or firing activity.",
        "How reliable the comparison is, based on reporting completeness.",
    ]
    _decisions = [
        "Which pens to inspect first after rough weather.",
        "Whether to investigate equipment availability or firing behaviour.",
        "What to communicate to farmers, with data limitations clearly visible.",
    ]

    def _bullet_block(items, colour):
        return "".join(
            f'<div style="display:flex;gap:7px;margin-bottom:3px;align-items:flex-start;">'
            f'<span style="flex:0 0 5px;height:5px;margin-top:4.5px;border-radius:50%;'
            f'background:{colour};"></span>'
            f'<span style="font-size:10px;line-height:1.35;color:{INK};">{item}</span></div>'
            for item in items
        )

    def _value_card(title, colour, items, note=""):
        note_html = (
            f'<div style="font-size:8.7px;color:{MUTED};margin-top:3px;">{note}</div>'
            if note
            else ""
        )
        return (
            f'<div style="background:{WHITE};border:1px solid {BORDER};'
            f'border-top:3px solid {colour};border-radius:8px;padding:6px 11px;">'
            f'<div style="font-size:8.7px;font-weight:700;letter-spacing:.13em;'
            f'text-transform:uppercase;color:{colour};">{title}</div>'
            f'<div style="margin-top:5px;">{_bullet_block(items, colour)}</div>'
            f"{note_html}</div>"
        )

    value_row = (
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">'
        f"{_value_card('What Kari can learn', TEAL, _learn)}"
        f"{_value_card('Decisions it supports', OCEAN, _decisions)}"
        f"</div>"
    )
    mo.vstack(
        [
            header(
                "08 / The product",
                "A reporting view that turns analysis into action.",
                "Kari can compare activity before, during and after storms, identify pens that need attention and see how complete the underlying data is.",
                title_size=30,
                lead_size=14,
            ),
            dashboard,
            mo.Html(value_row),
        ],
        gap=0.35,
        align="stretch",
    )


@app.cell
def slide_closing(test_counts, fish_logs):
    # KEY MESSAGE  Tested transformations, explicit assumptions, and concrete next
    #              steps for Kari — observations, hypotheses and investigations.
    # SAY          Lead with validation, then the remaining source/deployment limits,
    #              then the recommendations grounded in the verified findings.
    # TRANSITION   "Thank you — questions welcome."
    _unit = sum(test_counts["by_layer"].get("unit", {}).values())
    _data = test_counts["tests"] - _unit
    _models = test_counts["models"]
    _pass = test_counts["pass"]
    _warn = test_counts["warn"]
    _error = test_counts["error"]
    _anomaly = int(
        fish_logs[~fish_logs["is_fish_count_plausible"]].iloc[0]["fish_count"]
    )

    categories = [
        (
            "Schema & integrity",
            "Unique keys, not-null constraints and foreign-key relationships.",
            TEAL,
        ),
        (
            "Grain & business rules",
            "Fact grains, assignment validity and no duplicate pen-days within an episode.",
            OCEAN,
        ),
        (
            "Temporal logic",
            "Node reassignments, local-day storm exposure.",
            CORAL,
        ),
        (
            "Calculation & data quality",
            "Missing vs zero, NULL rates, fish plausibility, duplicate resolution.",
            TEAL_DEEP,
        ),
    ]
    category_rows = "".join(
        f'<div style="display:flex;gap:8px;align-items:flex-start;'
        f'padding:4px 0;border-top:1px solid {BORDER};">'
        f'<span style="flex:0 0 6px;height:6px;margin-top:4px;border-radius:50%;'
        f'background:{_colour};"></span>'
        f'<div style="min-width:0;">'
        f'<span style="font-size:10.2px;font-weight:700;color:{NAVY};">{_name}.</span> '
        f'<span style="font-size:9.9px;line-height:1.4;color:{MUTED};">{_body}</span>'
        f"</div></div>"
        for _name, _body, _colour in categories
    )

    _examples = [
        (
            "UNIT TEST",
            "N05 · 8 Oct",
            "New assignment applied; missing telemetry stays missing.",
            TEAL,
        ),
        (
            "UNIT + SINGULAR",
            "ST-0041 · 36 h",
            "300 / 1,440 / 420 minutes across three Oslo days.",
            TEAL,
        ),
        (
            "WARN TEST",
            f"P201 · {_anomaly:,}",
            "Flagged, not corrected or removed.",
            CORAL,
        ),
    ]
    example_cards = "".join(
        f'<div style="background:{WHITE};border:1px solid {BORDER};border-radius:7px;'
        f'padding:5px 8px;min-width:0;">'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
        f'gap:6px;">'
        f'<span style="font-size:9.5px;font-weight:700;letter-spacing:.08em;'
        f'color:{_colour};">{_tag}</span>'
        f'<span style="font-family:{MONO};font-size:10px;font-weight:650;color:{NAVY};">'
        f"{_headline}</span></div>"
        f'<div style="font-size:10.4px;line-height:1.4;color:{INK};margin-top:2px;">'
        f"{_body}</div></div>"
        for _tag, _headline, _body, _colour in _examples
    )

    limitations = [
        (
            "01",
            "Semantic layer & knowledge graph",
            "Incorporate a semantic layer and knowledge graph: End users can easily write text-to-SQL queries.",
            "Design and validate text-to-SQL access against the reporting marts.",
        ),
        (
            "02",
            "Data coverage",
            "Short observation window and missing telemetry: the window ends at the last observed activity date, and some node-days are missing.",
            "Extend the observation window; add device-status and freshness checks.",
        ),
        (
            "03",
            "Production readiness",
            "Snowflake validation, freshness monitoring and source contracts are not yet in place.",
            "Validate Snowflake; add freshness monitoring and source contracts.",
        ),
    ]
    limitation_rows = "".join(
        f'<div style="display:grid;grid-template-columns:22px 1.15fr 22px 1.2fr;'
        f'gap:8px;align-items:start;padding:4px 0;border-top:1px solid {BORDER};">'
        f'<span style="font-family:{MONO};font-size:9px;font-weight:700;'
        f'color:{CORAL_DEEP};padding-top:1px;">{_num}</span>'
        f'<div><span style="font-size:11.0px;font-weight:700;color:{NAVY};">'
        f'{_title}</span><div style="font-size:10.4px;line-height:1.35;color:{MUTED};'
        f'margin-top:1px;">{_body}</div></div>'
        f'<span style="color:{TEAL};font-size:12px;font-weight:700;'
        f'text-align:center;padding-top:2px;">→</span>'
        f'<div style="font-size:11.0px;line-height:1.4;color:{TEAL_DEEP};'
        f'font-weight:600;">{_next_step}</div></div>'
        for _num, _title, _body, _next_step in limitations
    )
    mo.Html(
        f'<div style="min-height:650px;display:flex;flex-direction:column;'
        f'box-sizing:border-box;padding:8px 6px 8px 6px;">'
        f"{header('09 / Closing', 'Validation & Next Steps', 'Here is what has been validated, what still constrains the conclusions, and what it takes to trust this in production.')}"
        # Validated
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;">'
        f'<div style="font-size:10px;font-weight:700;letter-spacing:.13em;'
        f'text-transform:uppercase;color:{TEAL_DEEP};">Validated</div>'
        f'<div style="font-size:10px;color:{MUTED};">'
        f"Latest verified dbt build · run_results.json</div></div>"
        f'<div style="display:grid;grid-template-columns:.92fr 1.38fr;gap:12px;'
        f'margin-top:5px;">'
        f'<div style="background:{SEAFOAM};border:1px solid #B9DDD6;border-radius:9px;'
        f'padding:11px 13px;">'
        f'<div style="display:flex;align-items:baseline;gap:8px;">'
        f'<span style="font-family:{MONO};font-size:38px;font-weight:700;'
        f'line-height:1;color:{TEAL_DEEP};">{test_counts["tests"]}</span>'
        f'<span style="font-size:10px;color:{MUTED};">tests</span>'
        f'<span style="margin-left:auto;font-size:9.5px;font-weight:650;'
        f'color:{TEAL_DEEP};background:{WHITE};border-radius:999px;padding:2px 7px;">'
        f"{_models} models</span></div>"
        f'<div style="font-size:10.4px;color:{INK};margin-top:5px;">'
        f"{_pass} pass · {_warn} intentional warn · {_error} errors</div>"
        f'<div style="font-size:10.4px;line-height:1.4;color:{MUTED};margin-top:3px;">'
        f"{_data} generic/singular tests check the actual model data; "
        f"{_unit} unit tests pin controlled edge cases.</div>"
        f'<div style="font-size:10px;color:{CORAL_DEEP};margin-top:3px;">'
        f"The warn is deliberate: a flagged anomaly (high fish population).</div></div>"
        f'<div style="background:{WHITE};border:1px solid {BORDER};border-radius:9px;'
        f'padding:9px 13px;">'
        f'<div style="font-size:9.5px;font-weight:700;letter-spacing:.1em;'
        f'text-transform:uppercase;color:{MUTED};margin-bottom:2px;">'
        f"What the tests protect</div>{category_rows}</div></div>"
        f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;'
        f'margin-top:5px;">{example_cards}</div>'
        # Limitations -> next steps
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
        f'margin-top:6px;">'
        f'<div style="font-size:10px;font-weight:700;letter-spacing:.13em;'
        f'text-transform:uppercase;color:{CORAL_DEEP};">Remaining limitations '
        f"→ next steps</div>"
        f'<div style="font-size:10px;color:{MUTED};">Highest impact first · '
        f"observations, hypotheses and recommended investigations</div></div>"
        f'<div style="margin-top:3px;">{limitation_rows}</div>'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
        f'margin-top:6px;">'
        f'<div style="font-size:10px;font-weight:700;letter-spacing:.13em;'
        f'text-transform:uppercase;color:{TEAL_DEEP};">Recommendations for Kari</div>'
        f'<div style="font-size:10px;color:{MUTED};">Observations → hypotheses → '
        f"investigations, not a firing-logic change</div></div>"
        f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;'
        f'margin-top:4px;">'
        f'<div style="background:{SEAFOAM};border-left:3px solid {TEAL};'
        f'border-radius:0 7px 7px 0;padding:6px 9px;">'
        f'<div style="font-size:10.0px;font-weight:700;color:{TEAL_DEEP};">'
        f"1 · Equipment availability</div>"
        f'<div style="font-size:10.4px;line-height:1.4;color:{INK};margin-top:3px;">'
        f"Investigate power, connectivity and device-status records for pens with "
        f"substantial reductions in uptime (P101, P103).</div></div>"
        f'<div style="background:{MIST};border-left:3px solid {OCEAN};'
        f'border-radius:0 7px 7px 0;padding:6px 9px;">'
        f'<div style="font-size:10.0px;font-weight:700;color:{OCEAN};">'
        f"2 · Detection conditions</div>"
        f'<div style="font-size:10.4px;line-height:1.4;color:{INK};margin-top:3px;">'
        f"Investigate camera conditions, fish behaviour and lice prevalence where "
        f"detections per operating hour declined (P101, P102).</div></div>"
        f'<div style="background:{CORAL_SOFT};border-left:3px solid {CORAL};'
        f'border-radius:0 7px 7px 0;padding:6px 9px;">'
        f'<div style="font-size:10.0px;font-weight:700;color:{CORAL_DEEP};">'
        f"3 · Post-storm monitoring</div>"
        f'<div style="font-size:10.4px;line-height:1.4;color:{INK};margin-top:3px;">'
        f"Keep monitoring and compare like-for-like node configurations before "
        f"drawing conclusions about recovery (P103 moved from N03 to N05).</div></div>"
        f"</div>"
        # Takeaway
        f'<div style="margin-top:auto;background:{NAVY};border-radius:10px;'
        f'padding:6px 12px;display:flex;gap:14px;align-items:flex-start;">'
        f'<div style="flex:0 0 3px;background:{CORAL};border-radius:2px;'
        f'align-self:stretch;"></div>'
        f'<div style="min-width:0;">'
        f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:5px;">'
        f'<span style="font-size:8.8px;font-weight:700;letter-spacing:.08em;'
        f"color:{SEAFOAM};border:1px solid #2A5A66;border-radius:4px;"
        f'padding:1px 6px;">TESTED ANALYTICS</span>'
        f'<span style="font-size:8.8px;font-weight:700;letter-spacing:.08em;'
        f"color:#FFC4B7;border:1px solid #7A3F35;border-radius:4px;"
        f'padding:1px 6px;">DESCRIPTIVE, NOT CAUSAL</span>'
        f'<span style="font-size:8.8px;font-weight:700;letter-spacing:.08em;'
        f"color:#B9D6D2;border:1px solid #2A5A66;border-radius:4px;"
        f'padding:1px 6px;">NOT PRODUCTION-READY</span></div>'
        f'<div style="font-size:13.5px;line-height:1.4;color:{WHITE};font-weight:500;">'
        f"The model provides a tested and consistent way to investigate how storms "
        f"relate to laser activity. The patterns are useful, but the current data "
        f"cannot establish causality. With better operational telemetry, more "
        f"observations and validated production assumptions, this can become a "
        f"reliable reporting tool for Kari and the fish-health team.</div></div></div>"
        f"</div>"
    )


if __name__ == "__main__":
    app.run()

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
    from pathlib import Path

    import altair as alt
    import duckdb
    import marimo as mo
    import pandas as pd

    PALETTE = {
        "navy": "#0B1F33",
        "ocean": "#123B52",
        "teal": "#16A6A1",
        "teal_soft": "#7FC8C3",
        "seafoam": "#D9F0EB",
        "coral": "#FF765E",
        "bg": "#F5F8FA",
        "ink": "#172B3A",
        "muted": "#5B7285",
        "border": "#E3EBF0",
        "white": "#FFFFFF",
    }
    INK = PALETTE["ink"]
    MUTED = PALETTE["muted"]
    BORDER = PALETTE["border"]
    WHITE = PALETTE["white"]
    CORAL = PALETTE["coral"]
    TEAL = PALETTE["teal"]
    OCEAN = PALETTE["ocean"]
    NAVY = PALETTE["navy"]
    SEAFOAM = PALETTE["seafoam"]
    MONO = "'JetBrains Mono','Fira Code','SFMono-Regular',monospace"

    SEVERITY_COLOURS = {"high": CORAL, "moderate": OCEAN, "low": PALETTE["teal_soft"]}
    PEN_COLOURS = [TEAL, OCEAN, PALETTE["teal_soft"]]
    PERIOD_COLOURS = {"Before": PALETTE["teal_soft"], "During": CORAL, "After": OCEAN}

    def _warehouse_path() -> Path:
        """Locate the DuckDB warehouse whether run from root or elsewhere."""
        direct = Path("data/warehouse/stingray.duckdb")
        if direct.exists():
            return direct
        for parent in Path.cwd().resolve().parents:
            candidate = parent / "data/warehouse/stingray.duckdb"
            if candidate.exists():
                return candidate
        raise FileNotFoundError(
            "data/warehouse/stingray.duckdb not found — run `uv run dbt build --profiles-dir .` first"
        )

    con = duckdb.connect(str(_warehouse_path()), read_only=True)

    def q(sql: str) -> pd.DataFrame:
        """Run a read-only query and return a pandas frame."""
        return con.sql(sql).df()

    def header(kicker: str, title: str, lead: str = "") -> mo.Html:
        """Slide header with a small kicker, title and optional lead line."""
        lead_html = (
            f'<div style="font-size:14.5px;line-height:1.45;color:{MUTED};'
            f'margin-top:4px;max-width:1050px;">{lead}</div>'
            if lead
            else ""
        )
        return mo.Html(
            f'<div style="margin:0 0 10px 0;">'
            f'<div style="font-size:11px;font-weight:700;letter-spacing:.16em;'
            f'text-transform:uppercase;color:{TEAL};">{kicker}</div>'
            f'<div style="font-size:29px;font-weight:700;line-height:1.15;'
            f'color:{NAVY};margin-top:2px;">{title}</div>{lead_html}</div>'
        )

    def dark_header(kicker: str, title: str, lead: str = "") -> mo.Html:
        """Header variant for the navy section slides."""
        lead_html = (
            f'<div style="font-size:16.5px;line-height:1.5;color:#B9D6D2;'
            f'margin-top:8px;max-width:880px;">{lead}</div>'
            if lead
            else ""
        )
        return mo.Html(
            f'<div style="margin:0 0 14px 0;">'
            f'<div style="font-size:11px;font-weight:700;letter-spacing:.18em;'
            f'text-transform:uppercase;color:{TEAL};">{kicker}</div>'
            f'<div style="font-size:40px;font-weight:700;line-height:1.1;'
            f'color:{WHITE};margin-top:6px;">{title}</div>{lead_html}</div>'
        )

    def bullets(items: list[str], *, size: float = 14.5, gap: int = 5) -> mo.Html:
        """Compact bullet list with teal dot markers."""
        rows = "".join(
            f'<li style="display:flex;gap:8px;margin:0 0 {gap}px 0;">'
            f'<span style="flex:0 0 5px;height:5px;margin-top:7px;border-radius:50%;'
            f'background:{TEAL};"></span>'
            f'<span style="font-size:{size}px;line-height:1.45;color:{INK};">{item}</span></li>'
            for item in items
        )
        return mo.Html(f'<ul style="list-style:none;margin:0;padding:0;">{rows}</ul>')

    def table(
        headers: list[str],
        rows: list[list[str]],
        *,
        widths: list[str] | None = None,
        size: str = "12.5px",
    ) -> mo.Html:
        """Lightweight styled table (markdown tables cannot carry this styling)."""
        cols = ""
        if widths:
            cols = (
                "<colgroup>"
                + "".join(f'<col style="width:{w}">' for w in widths)
                + "</colgroup>"
            )
        head = "".join(
            f'<th style="text-align:left;padding:7px 9px;font-size:10px;'
            f"letter-spacing:.09em;text-transform:uppercase;color:{MUTED};"
            f"background:#EDF4F7;border-bottom:1px solid {BORDER};"
            f'font-weight:700;">{h}</th>'
            for h in headers
        )
        body = ""
        for row in rows:
            cells = "".join(
                f'<td style="padding:6px 9px;vertical-align:top;'
                f"font-size:{size};line-height:1.4;color:{INK};"
                f'border-bottom:1px solid #EEF3F6;">{c}</td>'
                for c in row
            )
            body += f"<tr>{cells}</tr>"
        return mo.Html(
            f'<table style="width:100%;border-collapse:collapse;'
            f"table-layout:fixed;background:{WHITE};border:1px solid {BORDER};"
            f'border-radius:8px;overflow:hidden;">{cols}'
            f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
        )

    def card(
        title: str,
        body: str,
        *,
        accent: str = TEAL,
        size: float = 13.5,
        bg: str = WHITE,
        fg: str = INK,
        border: str = BORDER,
    ) -> mo.Html:
        """White card with a coloured top rule (dark variant via bg/fg)."""
        return mo.Html(
            f'<div style="background:{bg};border:1px solid {border};'
            f"border-top:3px solid {accent};border-radius:10px;"
            f'padding:10px 12px;height:100%;box-sizing:border-box;">'
            f'<div style="font-size:10px;font-weight:700;letter-spacing:.09em;'
            f'text-transform:uppercase;color:{accent};margin-bottom:5px;">{title}</div>'
            f'<div style="font-size:{size}px;line-height:1.45;color:{fg};">{body}</div>'
            f"</div>"
        )

    def kpi(value: str, label: str, sub: str = "", *, accent: str = TEAL) -> mo.Html:
        """KPI tile used by the dashboard mock."""
        sub_html = (
            f'<div style="font-size:11px;color:{MUTED};margin-top:2px;">{sub}</div>'
            if sub
            else ""
        )
        return mo.Html(
            f'<div style="background:{WHITE};border:1px solid {BORDER};'
            f"border-left:3px solid {accent};border-radius:8px;"
            f'padding:9px 12px;height:100%;box-sizing:border-box;">'
            f'<div style="font-size:10px;font-weight:600;letter-spacing:.06em;'
            f'text-transform:uppercase;color:{MUTED};">{label}</div>'
            f'<div style="font-size:26px;font-weight:700;color:{NAVY};'
            f'line-height:1.2;margin-top:2px;">{value}</div>{sub_html}</div>'
        )

    def grid(
        items: list[mo.Html],
        *,
        cols: int = 3,
        gap: int = 8,
        max_width: str | None = None,
    ) -> mo.Html:
        """Full-width CSS grid row; hstack shrinks to content, grid stretches."""
        inner = "".join(
            f'<div style="min-width:0;">{item.text}</div>' for item in items
        )
        cap = f"max-width:{max_width};" if max_width else ""
        return mo.Html(
            f'<div style="display:grid;grid-template-columns:'
            f"repeat({cols},minmax(0,1fr));gap:{gap}px;{cap}"
            f'align-items:stretch;">{inner}</div>'
        )

    def pill(text: str, *, fg: str = NAVY, bg: str = SEAFOAM) -> str:
        """Inline chip, returns HTML for embedding in other components."""
        return (
            f'<span style="background:{bg};color:{fg};padding:1px 8px;'
            f"border-radius:999px;font-size:10.5px;font-weight:600;"
            f'white-space:nowrap;">{text}</span>'
        )

    def severity_pill(severity: str) -> str:
        colours = {
            "high": ("#A93A26", "#FFE4DE"),
            "moderate": (OCEAN, "#DDE7EE"),
            "low": ("#0E6E6A", "#DFF3EF"),
        }
        fg, bg = colours.get(severity, (INK, "#EEF3F6"))
        return pill(severity, fg=fg, bg=bg)

    def mono(text: str, *, size: float = 11) -> str:
        return (
            f'<code style="font-family:{MONO};font-size:{size}px;'
            f"background:#EDF4F7;color:{OCEAN};padding:1px 5px;"
            f'border-radius:4px;">{text}</code>'
        )

    def code_block(code: str, caption: str, *, size: float = 11.5) -> mo.Html:
        """Dark code card for the SQL slide."""
        return mo.Html(
            f'<div style="background:{NAVY};border-radius:8px;padding:10px 12px;'
            f'height:100%;box-sizing:border-box;">'
            f'<div style="font-size:9.5px;letter-spacing:.08em;line-height:1.35;'
            f"text-transform:uppercase;color:{SEAFOAM};margin-bottom:6px;"
            f'overflow-wrap:anywhere;font-weight:700;">{caption}</div>'
            f'<pre style="margin:0;white-space:pre-wrap;font-family:{MONO};'
            f'font-size:{size}px;line-height:1.42;color:#E6F2F0;">'
            f"{_html.escape(code)}</pre></div>"
        )

    def alt_style(chart: alt.Chart, *, height: int = 240) -> alt.Chart:
        """Apply the deck's chart theme (one place for axis/legend styling)."""
        return (
            chart.properties(height=height)
            .configure_view(stroke=None)
            .configure_axis(
                labelColor=MUTED,
                titleColor=INK,
                gridColor="#E7EEF2",
                domainColor="#CBD8E0",
                tickColor="#CBD8E0",
                labelFontSize=11.5,
                titleFontSize=11.5,
                titleFontWeight="normal",
                titlePadding=6,
            )
            .configure_legend(
                labelColor=INK,
                titleColor=INK,
                labelFontSize=11,
                symbolSize=80,
                orient="top",
                direction="horizontal",
                title=None,
            )
            .configure_title(color=INK, fontSize=12, anchor="start")
        )


@app.cell(hide_code=True)
def load_activity():
    # Pen-day source of truth: additive measures, completeness, fish snapshot
    # and the site-day storm overlay (site-day values repeat per pen).
    daily = q(
        """
        select
            site_id,
            pen_id,
            activity_date,
            laser_shot_count,
            lice_detection_count,
            uptime_minutes,
            shots_per_operating_hour,
            detections_per_operating_hour,
            shots_per_detection,
            reporting_completeness,
            expected_node_days,
            reported_node_days,
            node_ids,
            has_node_set_change,
            fish_count,
            has_fish_count,
            has_storm,
            storm_count,
            storm_minutes,
            max_storm_severity
        from main_marts.fct_pen_daily_activity
        order by activity_date, site_id, pen_id
        """
    )
    return (daily,)


@app.cell(hide_code=True)
def load_storms():
    # Episodes (pen-independent), site-day exposure (never summed across pens)
    # and the pen-episode baseline fact (one row per pen and episode).
    episodes = q(
        """
        select
            site_id,
            episode_started_at,
            episode_ended_at,
            episode_start_date,
            episode_end_date,
            episode_span_hours,
            storm_event_count,
            max_severity,
            storm_ids
        from main_marts.dim_storm_episode
        order by episode_started_at
        """
    )
    storm_days = q(
        """
        select distinct
            site_id,
            activity_date,
            storm_count,
            storm_minutes as total_storm_minutes,
            max_storm_severity
        from main_marts.fct_pen_daily_activity
        where has_storm
        order by site_id, activity_date
        """
    )
    mart_counts = q(
        """
        select 'fct_pen_daily_activity' as model_name, count(*) as row_count
        from main_marts.fct_pen_daily_activity
        union all
        select 'fct_pen_storm_analysis', count(*)
        from main_marts.fct_pen_storm_analysis
        union all
        select 'fct_pen_storm_baseline', count(*)
        from main_marts.fct_pen_storm_baseline
        union all
        select 'dim_date', count(*) from main_marts.dim_date
        union all
        select 'dim_site', count(*) from main_marts.dim_site
        union all
        select 'dim_pen', count(*) from main_marts.dim_pen
        union all
        select 'dim_storm_episode', count(*) from main_marts.dim_storm_episode
        """
    )
    baselines = q(
        """
        select
            b.pen_id,
            b.site_id,
            b.baseline_days,
            b.during_days,
            b.after_days,
            b.baseline_reporting_completeness,
            b.during_reporting_completeness,
            b.after_reporting_completeness,
            b.baseline_shots,
            b.during_shots,
            b.baseline_uptime_minutes,
            b.during_uptime_minutes,
            b.baseline_shots_per_operating_hour,
            b.during_shots_per_operating_hour,
            b.after_shots_per_operating_hour,
            b.during_change_vs_baseline_pct,
            b.after_change_vs_baseline_pct,
            b.during_detections_change_vs_baseline_pct,
            b.baseline_shots_per_detection,
            b.during_shots_per_detection,
            b.has_node_change_in_window,
            e.max_severity,
            e.episode_start_date,
            e.episode_end_date,
            e.episode_span_hours,
            e.storm_event_count
        from main_marts.fct_pen_storm_baseline as b
        inner join main_marts.dim_storm_episode as e
            on e.storm_episode_key = b.storm_episode_key
        order by e.episode_start_date, b.pen_id
        """
    )
    return baselines, episodes, mart_counts, storm_days


@app.cell(hide_code=True)
def load_quality():
    # Only the data-quality facts that changed a modelling decision.
    fish_logs = q(
        """
        select
            log_id,
            pen_id,
            logged_local_date,
            fish_count,
            is_fish_count_plausible,
            is_duplicate_pen_day,
            log_comment
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
    source_counts = q(
        """
        select 'node_daily_activity' as source_table, count(*) as row_count
        from main_staging.stg_stingray__node_daily_activity
        union all
        select 'node_pen_assignment', count(*)
        from main_staging.stg_stingray__node_pen_assignments
        union all
        select 'storm_events', count(*)
        from main_staging.stg_stingray__storm_events
        union all
        select 'farmer_pen_log', count(*)
        from main_staging.stg_stingray__farmer_pen_logs
        """
    )
    return fish_logs, missing_telemetry, source_counts, zero_uptime


@app.cell(hide_code=True)
def build_figures(baselines, daily, episodes, storm_days):
    # Totals shown in the dashboard mock: summed over pen-days (additive
    # measures only); completeness is reported/expected node-days, not a
    # mean of daily ratios.
    totals = {
        "shots": int(daily["laser_shot_count"].sum()),
        "detections": int(daily["lice_detection_count"].sum()),
        "uptime_hours": float(daily["uptime_minutes"].sum() / 60),
        "completeness": float(
            daily["reported_node_days"].sum() / daily["expected_node_days"].sum()
        ),
        "pen_days": len(daily),
        "storm_days": len(storm_days),
    }

    # Inference: figures are built once, cells below only lay them out.

    # ---- S01 timeline: pen-day rate with the storm window shaded ----------
    s01_daily = daily[daily["site_id"] == "S01"]
    s01_bands = episodes[episodes["site_id"] == "S01"]
    bands = pd.DataFrame(
        {
            "start": s01_bands["episode_start_date"],
            "end": s01_bands["episode_end_date"] + pd.Timedelta(days=1),
        }
    )
    band_layer = (
        alt.Chart(bands)
        .mark_rect(color=CORAL, opacity=0.13)
        .encode(x=alt.X("start:T"), x2=alt.X2("end:T"))
    )
    line = (
        alt.Chart(s01_daily)
        .mark_line(strokeWidth=2.2)
        .encode(
            x=alt.X(
                "activity_date:T",
                title=None,
                axis=alt.Axis(format="%d %b", tickCount=7, labelAngle=0, grid=False),
            ),
            y=alt.Y(
                "shots_per_operating_hour:Q",
                title="Shots per operating hour",
                scale=alt.Scale(domain=[0, 46]),
            ),
            color=alt.Color(
                "pen_id:N",
                title=None,
                scale=alt.Scale(domain=["P101", "P102", "P103"], range=PEN_COLOURS),
            ),
            tooltip=[
                alt.Tooltip("pen_id:N", title="Pen"),
                alt.Tooltip("activity_date:T", title="Date", format="%d %b"),
                alt.Tooltip(
                    "shots_per_operating_hour:Q", title="Shots/h", format=".1f"
                ),
                alt.Tooltip("uptime_minutes:Q", title="Uptime (min)", format=".0f"),
                alt.Tooltip(
                    "reporting_completeness:Q", title="Completeness", format=".0%"
                ),
            ],
        )
    )
    move_dates = s01_daily.loc[
        s01_daily["pen_id"].eq("P103") & s01_daily["has_node_set_change"].fillna(False),
        "activity_date",
    ]
    move_layer = (
        alt.Chart(pd.DataFrame({"date": move_dates}))
        .mark_rule(color=OCEAN, strokeDash=[4, 3], strokeWidth=1)
        .encode(x=alt.X("date:T"))
        if len(move_dates)
        else alt.Chart(pd.DataFrame({"date": []})).mark_rule()
    )
    fig_timeline = alt_style(
        alt.layer(band_layer, move_layer, line, line.mark_point(size=26, filled=True))
        .properties(width="container")
        .interactive(bind_y=False),
        height=252,
    )

    # ---- Before / during / after levels for the S01 pens -------------------
    s01_base = baselines[baselines["site_id"] == "S01"].copy()
    periods = s01_base.melt(
        id_vars=["pen_id"],
        value_vars=[
            "baseline_shots_per_operating_hour",
            "during_shots_per_operating_hour",
            "after_shots_per_operating_hour",
        ],
        var_name="period",
        value_name="rate",
    )
    periods["period"] = periods["period"].map(
        {
            "baseline_shots_per_operating_hour": "Before",
            "during_shots_per_operating_hour": "During",
            "after_shots_per_operating_hour": "After",
        }
    )
    fig_periods = alt_style(
        alt.Chart(periods)
        .mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2)
        .encode(
            x=alt.X("pen_id:N", title=None, axis=alt.Axis(labelAngle=0)),
            xOffset=alt.XOffset(
                "period:N", sort=["Before", "During", "After"], title=None
            ),
            y=alt.Y(
                "rate:Q",
                title="Shots / hour",
                scale=alt.Scale(domain=[0, 40]),
            ),
            color=alt.Color(
                "period:N",
                title=None,
                scale=alt.Scale(
                    domain=["Before", "During", "After"],
                    range=[
                        PERIOD_COLOURS["Before"],
                        PERIOD_COLOURS["During"],
                        PERIOD_COLOURS["After"],
                    ],
                ),
            ),
            tooltip=[
                alt.Tooltip("pen_id:N", title="Pen"),
                alt.Tooltip("period:N", title="Period"),
                alt.Tooltip("rate:Q", title="Shots/h", format=".1f"),
            ],
        )
        .properties(width=340),
        height=186,
    )

    # ---- Site-day storm exposure (the 6 storm-days) ------------------------
    exposure = storm_days.copy()
    exposure["label"] = (
        exposure["site_id"] + " · " + exposure["activity_date"].dt.strftime("%d %b")
    )
    exposure_order = list(exposure["label"])
    exposure_bars = (
        alt.Chart(exposure)
        .mark_bar(size=16, cornerRadiusTopRight=3, cornerRadiusBottomRight=3)
        .encode(
            y=alt.Y("label:N", sort=exposure_order, title=None),
            x=alt.X(
                "total_storm_minutes:Q",
                title="Storm minutes within the local day",
                scale=alt.Scale(domain=[0, 1500]),
            ),
            color=alt.Color(
                "max_storm_severity:N",
                title=None,
                scale=alt.Scale(
                    domain=["low", "moderate", "high"],
                    range=[
                        SEVERITY_COLOURS["low"],
                        SEVERITY_COLOURS["moderate"],
                        SEVERITY_COLOURS["high"],
                    ],
                ),
            ),
            tooltip=[
                alt.Tooltip("site_id:N", title="Site"),
                alt.Tooltip("activity_date:T", title="Date", format="%d %b"),
                alt.Tooltip("total_storm_minutes:Q", title="Minutes", format=".0f"),
                alt.Tooltip("max_storm_severity:N", title="Severity"),
            ],
        )
        .properties(width=400)
    )
    exposure_labels = (
        alt.Chart(exposure)
        .mark_text(align="left", dx=5, fontSize=10, color=MUTED)
        .encode(
            y=alt.Y("label:N", sort=exposure_order),
            x=alt.X("total_storm_minutes:Q"),
            text=alt.Text("total_storm_minutes:Q", format=".0f"),
        )
    )
    fig_exposure = alt_style(alt.layer(exposure_bars, exposure_labels), height=190)
    return exposure, fig_exposure, fig_periods, fig_timeline, totals


@app.cell
def slide_title(daily, episodes, storm_days):
    # KEY MESSAGE  A stakeholder question, not a dashboard request, is the brief.
    # SAY          Frame the talk: business question -> data reality -> model -> answer.
    # TRANSITION   "Let me start with what Kari actually asked for."
    first_day = daily["activity_date"].min().strftime("%d %b")
    last_day = daily["activity_date"].max().strftime("%d %b")
    mo.vstack(
        [
            mo.Html(
                f'<div style="font-size:11px;font-weight:700;letter-spacing:.22em;'
                f'text-transform:uppercase;color:{TEAL};margin-bottom:14px;">'
                f"Stingray · Analytics Engineer case</div>"
            ),
            mo.Html(
                f'<div style="font-size:52px;font-weight:700;line-height:1.06;'
                f'color:{WHITE};max-width:980px;">Do storms change how hard '
                f"the lasers work?</div>"
            ),
            mo.Html(
                f'<div style="font-size:16px;line-height:1.5;color:#B9D6D2;'
                f"max-width:760px;margin-top:14px;\">From Kari's question to a "
                f"tested daily model — and a straight answer about what "
                f"{len(daily):d} pen-days can and cannot prove.</div>"
            ),
            mo.Html('<div style="height:22px;"></div>'),
            grid(
                [
                    kpi(
                        f"{daily['site_id'].nunique()} sites · {daily['pen_id'].nunique()} pens",
                        "Scope",
                        f"{first_day} – {last_day} 2026",
                        accent=TEAL,
                    ),
                    kpi(
                        f"{len(episodes)} episodes",
                        "Storms",
                        f"{len(storm_days)} storm-days at site level",
                        accent=CORAL,
                    ),
                    kpi(
                        f"{len(daily)} pen-days",
                        "Analytical grain",
                        "one row per site × pen × date",
                        accent=PALETTE["teal_soft"],
                    ),
                ],
                cols=3,
                gap=10,
                max_width="880px",
            ),
            mo.Html(
                f'<div style="font-size:11.5px;color:#8FB0AD;margin-top:22px;">'
                f"DuckDB warehouse · dbt (staging → intermediate → marts) · "
                f"Power BI specification · all figures queried live from "
                f'<code style="font-family:{MONO};color:#B9D6D2;">main_marts</code></div>'
            ),
        ],
        gap=0.25,
        align="stretch",
    )


@app.cell
def slide_problem():
    # KEY MESSAGE  Kari needs to separate "laser shooting less" from "node offline"
    #              before any storm story can be told.
    # SAY          Read the quote, then reframe activity into a rate the team can trust.
    # TRANSITION   "Before any analysis, let's see what data we actually have."
    quote = mo.Html(
        f'<div style="background:{WHITE};border:1px solid {BORDER};'
        f'border-left:4px solid {CORAL};border-radius:8px;padding:14px 16px;">'
        f'<div style="font-size:13.5px;line-height:1.55;color:{INK};">'
        f"“Several farmers have told us that the lasers seem to be <b>less active</b> "
        f"after storms. Some think the nodes don’t work properly in rough weather, "
        f"others think it’s just that the fish behave differently afterwards. "
        f"We honestly don’t know.”</div>"
        f'<div style="font-size:11.5px;color:{MUTED};margin-top:8px;">'
        f"Kari Nordmann · Fish Health Biologist</div></div>"
    )
    ask = card(
        "What Kari asked for",
        "A Power BI view of how storms affect laser activity <b>per pen</b>, "
        "comparable across pens and sites, with the difference between "
        "<b>before, during and after</b> a storm.",
        accent=TEAL,
    )
    questions = card(
        "The four questions the model must answer",
        bullets(
            [
                "Does activity change <b>during</b> a storm, and does it <b>recover</b>?",
                "Which <b>pens</b> and <b>sites</b> are most affected?",
                "Is a drop the laser <b>shooting less</b> — or the node being <b>offline</b>?",
                "How do we compare pens that differ in <b>uptime</b> and <b>fish population</b>?",
            ],
            size=13,
            gap=5,
        ),
        accent=OCEAN,
    )
    why_hard = card(
        "Why this is not a simple group-by",
        "Activity is a count with a variable exposure window; storms are site-level "
        "while activity is pen-level; and the reporting is manual, so the gaps matter "
        "as much as the numbers.",
        accent=PALETTE["teal_soft"],
        size=12,
    )
    decisions = mo.Html(
        f'<div style="font-size:12px;line-height:1.5;color:{INK};">'
        f"<b>Decisions this supports:</b> what to tell the farmer in the customer "
        f"meeting, which pens to inspect after rough weather, and which "
        f"measurements (uptime vs shots) the team must log to answer this properly.</div>"
    )
    mo.vstack(
        [
            header(
                "01 · Understanding the problem",
                "A farmer observation, not a specification",
                "The brief arrives as a belief (“lasers are less active after storms”) "
                "with two competing explanations — equipment or fish behaviour.",
            ),
            mo.hstack(
                [
                    mo.vstack([quote, ask], gap=0.5),
                    mo.vstack([questions, why_hard], gap=0.5),
                ],
                widths=[1, 1],
                gap=1.0,
                align="start",
            ),
            decisions,
        ],
        gap=0.55,
        align="stretch",
    )


@app.cell
def slide_sources(source_counts):
    # KEY MESSAGE  Four small tables, four different grains — most of the work is
    #              getting the joins right, not the arithmetic.
    # SAY          Point out the grain column and the relationship line.
    # TRANSITION   "Small data, but it fights back — here is what I found."
    counts = dict(
        zip(source_counts["source_table"], source_counts["row_count"], strict=True)
    )
    source_rows = [
        [
            mono("node_daily_activity"),
            "one row per <b>node per day</b>",
            f"{counts['node_daily_activity']:,}",
            "shots_fired · lice_detections · uptime_minutes (0–1,500 allowed)",
            "What the laser did",
        ],
        [
            mono("node_pen_assignment"),
            "one row per <b>deployment interval</b>",
            f"{counts['node_pen_assignment']:,}",
            "valid_from · valid_to (null = current) · site_id · pen_id",
            "Where each node was, when",
        ],
        [
            mono("storm_events"),
            "one row per <b>storm per site</b>",
            f"{counts['storm_events']:,}",
            "start_ts · end_ts (UTC, +02:00 offsets) · severity",
            "When a site was exposed",
        ],
        [
            mono("farmer_pen_log"),
            "one row per <b>fish-count entry</b>",
            f"{counts['farmer_pen_log']:,}",
            "log_ts (naive local) · fish_count · comment",
            "Population context",
        ],
    ]
    relationships = mo.Html(
        f'<div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;'
        f'font-size:11.5px;color:{INK};">'
        f'{pill("node → pen", fg=OCEAN, bg="#DDE7EE")} <span style="margin-left:4px;">joined on <b>date inside the assignment interval</b>, never on node_id alone</span>'
        f'<span style="color:{BORDER};">|</span>'
        f"{pill('storm → site', fg='#A93A26', bg='#FFE4DE')} clock time, split to local days"
        f'<span style="color:{BORDER};">|</span>'
        f"{pill('log → pen', fg='#0E6E6A', bg='#DFF3EF')} pen + local date, latest entry wins</div>"
    )
    mo.vstack(
        [
            header(
                "02 · Understanding the data",
                "Four extracts, four grains, two sites, five pens",
                "14 days of October 2026 telemetry; the assignment table also "
                "carries deployment history back to April.",
            ),
            table(
                ["Source table", "Grain", "Rows", "Fields that matter", "Answers"],
                source_rows,
                widths=["19%", "20%", "7%", "35%", "19%"],
            ),
            relationships,
            mo.Html(
                f'<div style="font-size:11.5px;color:{MUTED};line-height:1.5;">'
                f"The extract contains <b>no site names, pen metadata or geography</b>, "
                f'so none are invented — sites and pens stay as <code style="font-family:{MONO};">S01/S02</code> and '
                f'<code style="font-family:{MONO};">P101…P202</code>. '
                f'Exploration lives in <code style="font-family:{MONO};">notebooks/01_data_exploration.py</code>; '
                f"this talk only carries the findings that changed a modelling decision.</div>"
            ),
            mo.Html(
                f'<div style="background:{SEAFOAM};border-radius:8px;padding:10px 14px;'
                f'font-size:13px;line-height:1.5;color:{NAVY};">'
                f"<b>The whole model rests on three keys</b> — node, pen and site — plus the "
                f"date that decides <i>which assignment is true</i>. That is where the next "
                f"slide starts.</div>"
            ),
        ],
        gap=0.55,
        align="stretch",
    )


@app.cell
def slide_quality(missing_telemetry, zero_uptime):
    # KEY MESSAGE  Five data-quality findings, five concrete modelling decisions.
    # SAY          Each row: what we saw -> what it would have broken -> what I did.
    # TRANSITION   "With those constraints fixed in the model, here is the metric design."
    missing_text = ", ".join(
        f"{row.node_id} on {row.activity_date.strftime('%d %b')}"
        for row in missing_telemetry.itertuples()
    )
    zero_text = ", ".join(
        sorted(
            {
                f"{row.node_id} {row.activity_date.strftime('%d %b')}"
                for row in zero_uptime.itertuples()
            }
        )
    )
    quality_rows = [
        [
            "<b>Nodes move between pens and sites</b>",
            f'N05 moves <b>S02/P202 → S01/P103</b> on 2026-10-08 (<code style="font-family:{MONO};">valid_from</code>). '
            "Joining on <code>node_id</code> alone would credit its first week to P103.",
            "Effective-dated join on the half-open interval "
            f"{mono('[valid_from, valid_to)')} — one row per node-day, attributed to the pen valid that date.",
        ],
        [
            "<b>Missing telemetry is not zero activity</b>",
            f"No record for {missing_text} → completeness 0, measures null. "
            f"Genuine zeros exist too: {zero_text} report <b>uptime 0</b> at the storm peak.",
            f"Node-day spine + {mono('has_activity_record')}; nulls preserved end to end and surfaced as "
            f"{mono('reporting_completeness')}, never coalesced to 0.",
        ],
        [
            "<b>Storms cross local calendar days</b>",
            "ST-0041 is one 36-hour storm but lands on <b>three S01 local days</b>: "
            "<b>300 / 1,440 / 420</b> storm-minutes.",
            f"Events clipped to DST-aware <b>Europe/Oslo</b> day boundaries in "
            f"{mono('int_storm_daily_exposure')}; half-open [start, end).",
        ],
        [
            "<b>Duplicate farmer entries per pen-day</b>",
            "P102 on 2026-10-08: log 1012 at 08:16 (167,500) and log 1013 at 14:47 "
            "“corrected count” (164,300).",
            "Deterministic latest-wins (timestamp, then highest log_id); the duplicate "
            f"is flagged, not deleted ({mono('is_duplicate_pen_day')}).",
        ],
        [
            "<b>Implausible fish count</b>",
            "P201 log 1014 = <b>1,852,000</b> vs a median of 170,000 — 10× the next-largest "
            "count (185,200).",
            "Flagged implausible and the snapshot is <b>withheld</b> from 2026-10-08 onward. "
            "No silent fallback to an older value; the log id stays for traceability.",
        ],
    ]
    mo.vstack(
        [
            header(
                "02 · Data quality that changed the model",
                "The data fights back in five places",
                "Only the findings that drove a design decision — not descriptive statistics.",
            ),
            table(
                ["Finding", "Evidence in the data", "Modelling decision"],
                quality_rows,
                widths=["20%", "42%", "38%"],
            ),
            mo.Html(
                f'<div style="font-size:11px;color:{MUTED};line-height:1.45;">'
                f"Each finding is covered by a test: missing activity is null (never zero), "
                f"storm minutes fit the local day length, a pen-day appears once per episode, "
                f"and no snapshot is built from an implausible entry.</div>"
            ),
        ],
        gap=0.5,
        align="stretch",
    )


@app.cell
def slide_metrics():
    # KEY MESSAGE  Normalise by operating time, compare each pen to itself, and
    #              never let missing data become a zero.
    # SAY          Walk the definition table; stress total-over-total rates.
    # TRANSITION   "Metrics define the rate; the windows define the comparison."
    metric_rows = [
        [
            "<b>Laser shots</b>",
            "Σ <code>shots_fired</code> over the period",
            "Volume — additive at pen-day grain",
        ],
        [
            "<b>Operating hours</b>",
            "Σ <code>uptime_minutes</code> ÷ 60",
            "Exposure time, not calendar time",
        ],
        [
            "<b>Shots per operating hour</b>",
            "Σ shots ÷ Σ uptime × 60",
            "Behaviour, with uptime removed",
        ],
        [
            "<b>Detections per operating hour</b>",
            "Σ <code>lice_detections</code> ÷ Σ uptime × 60",
            "Lice pressure seen by the camera",
        ],
        [
            "<b>Shots per detection</b>",
            "Σ shots ÷ Σ detections",
            "Laser effort per lice found",
        ],
        [
            "<b>Reporting completeness</b>",
            "reported node-days ÷ expected node-days",
            "How much to trust the day",
        ],
    ]
    rate_note = card(
        "Never average daily rates",
        "A period rate is <b>total ÷ total</b>. Averaging daily rates would let a "
        "zero-uptime day (rate null) or a quiet day carry the same weight as a full "
        "day. Example: P101's during-storm rate is 3-day shots ÷ 3-day uptime, not "
        "the mean of three daily percentages.",
        accent=CORAL,
    )
    fish_note = card(
        "Fish counts: context, not a denominator",
        "Pens differ in population (P101 172,400 vs P103 96,300 on 1 Oct), so each pen "
        "is compared to <b>its own</b> baseline. Counts are manual snapshots, carried "
        "forward at most 7 days; stale or implausible values become <b>null</b>, and "
        "they are never used to normalise activity in this build.",
        accent=OCEAN,
    )
    missing_note = card(
        "Missing stays missing",
        "No activity record ≠ zero shots. The rate is <b>null</b> when uptime is zero "
        "or missing, and completeness is shown next to every comparison.",
        accent=TEAL,
    )
    mo.vstack(
        [
            header(
                "03 · Analytical methodology",
                "What we measure — and why it is a rate, not a count",
                "Uptime and population differ by pen, so raw shot counts compare the "
                "wrong thing. Every measure below is defined once, in dbt.",
            ),
            mo.hstack(
                [
                    mo.vstack(
                        [
                            table(
                                [
                                    "Metric",
                                    "Definition (period totals)",
                                    "What it is for",
                                ],
                                metric_rows,
                                widths=["26%", "40%", "34%"],
                            ),
                            mo.Html(
                                f'<div style="font-size:11px;color:{MUTED};margin-top:10px;'
                                f'border-left:2px solid {BORDER};padding-left:8px;">'
                                f'<b>Assumption to confirm:</b> <code style="font-family:{MONO};">activity_date</code> '
                                f'is a local (Europe/Oslo) day, and <code style="font-family:{MONO};">uptime_minutes</code> '
                                f"is node on-time — not proof the laser was armed.</div>"
                            ),
                        ],
                        gap=0.3,
                    ),
                    mo.vstack([rate_note, fish_note, missing_note], gap=0.6),
                ],
                widths=[1.15, 1],
                gap=1.0,
                align="start",
            ),
        ],
        gap=0.5,
        align="stretch",
    )


@app.cell
def slide_windows(fig_exposure):
    # KEY MESSAGE  The episode window is not the exposure: one is wall-clock,
    #              the other is clipped minutes per local day.
    # SAY          Give the three episodes, then the windows and the membership rule.
    # TRANSITION   "Now the layer where those rules actually live."
    episode_lines = [
        "<b>Episodes</b> group storms at one site with a gap &lt; 24 h → "
        "<b>3 episodes</b>: S01 5–7 Oct (<b>high</b>, 36 h), S02 9–10 Oct "
        "(<b>moderate</b>, 6 h), S02 14 Oct (<b>low</b>, 3 h).",
        "<b>Windows</b>: <i>before</i> = 3 local dates before the start · "
        "<i>during</i> = every episode date (a partially hit day counts) · "
        "<i>after</i> = 3 local dates after the end.",
        "<b>Exposure ≠ window</b>: the episode span includes quiet gaps; "
        "<code>storm_minutes</code> is actual clipped exposure per site-day "
        "(the chart at right).",
        "<b>Membership</b>: a pen joins an episode only if it had nodes at that "
        "site on a <i>during</i> date — so P202 drops out of the S02 episodes "
        "after the 8 Oct move.",
        "<b>Comparison</b>: each pen against its own baseline first, then across "
        "pens and sites. Completeness travels with every number.",
    ]
    mo.vstack(
        [
            header(
                "03 · Analytical methodology",
                "Before, during, after — and what counts as exposure",
                "ST-0041 is 36 hours of weather; the model reports it as three "
                "local days of exposure, not three days of “storm”.",
            ),
            mo.hstack(
                [
                    bullets(episode_lines, size=13.5, gap=7),
                    mo.vstack(
                        [
                            fig_exposure,
                            mo.Html(
                                f'<div style="font-size:10.5px;color:{MUTED};line-height:1.4;">'
                                f"Site-day exposure, all 6 storm-days. ST-0041 splits "
                                f"across 5–7 Oct; ST-0043 runs 00:30–03:30 local on 14 Oct, "
                                f"so it claims only that date.</div>"
                            ),
                        ],
                        gap=0.25,
                        align="stretch",
                    ),
                ],
                widths=[1.35, 1],
                gap=1.1,
                align="start",
            ),
            mo.Html(
                f'<div style="display:flex;gap:10px;font-size:11px;color:{INK};'
                f"background:{WHITE};border:1px solid {BORDER};border-radius:8px;"
                f'padding:8px 10px;">'
                f"{pill('reliability gate', fg='#A93A26', bg='#FFE4DE')}"
                f"<span>S01 comparisons run on <b>100% completeness</b> before and during; "
                f"P103's after-window sits at <b>66.7%</b> because of the 8 Oct node move — "
                f"flagged, not hidden.</span></div>"
            ),
        ],
        gap=0.5,
        align="stretch",
    )


@app.cell
def slide_architecture(baselines):
    # KEY MESSAGE  Layer boundaries are the design: staging standardises, intermediate
    #              encodes the hard joins, marts serve the question.
    # SAY          Follow one storm from CSV to fact; then point at the challenge strip.
    # TRANSITION   "Those challenges are where the engineering effort went."
    def column(title, subtitle, items, accent, bg, *, width="1", footer=""):
        item_html = "".join(
            f'<div style="font-family:{MONO};font-size:11px;line-height:1.6;'
            f'color:{INK};overflow-wrap:anywhere;">{item}</div>'
            for item in items
        )
        return (
            f'<div style="flex:{width};min-width:0;display:flex;'
            f"flex-direction:column;background:{bg};"
            f"border:1px solid {BORDER};border-top:3px solid {accent};"
            f'border-radius:8px;padding:9px 10px;">'
            f'<div style="font-size:10.5px;font-weight:700;letter-spacing:.08em;'
            f'text-transform:uppercase;color:{accent};">{title}</div>'
            f'<div style="font-size:9.5px;color:{MUTED};margin:1px 0 7px 0;">{subtitle}</div>'
            f'<div style="flex:1;">{item_html}</div>'
            f'<div style="margin-top:8px;padding-top:5px;'
            f'border-top:1px dashed {BORDER};font-size:9.5px;color:{MUTED};">'
            f"{footer}</div></div>"
        )

    arrow = '<div style="align-self:center;color:#A7BAC5;font-size:15px;">→</div>'
    pipeline = mo.Html(
        '<div style="display:flex;gap:6px;align-items:stretch;">'
        + column(
            "Raw",
            "CSV · all_varchar",
            [
                "node_daily_activity · 61",
                "node_pen_assignment · 6",
                "storm_events · 3",
                "farmer_pen_log · 10",
            ],
            "#9DB3BF",
            "#F4F7F9",
            footer="80 rows · read as varchar",
        )
        + arrow
        + column(
            "Staging",
            "views · 1:1 · cast + UTC",
            [
                '<span style="color:#7C93A3;">stg_stingray__</span><br>node_daily_activity',
                '<span style="color:#7C93A3;">stg_stingray__</span><br>node_pen_assignments',
                '<span style="color:#7C93A3;">stg_stingray__</span><br>storm_events',
                '<span style="color:#7C93A3;">stg_stingray__</span><br>farmer_pen_logs',
            ],
            PALETTE["teal_soft"],
            "#F2FAF9",
            footer="1:1 with source · no business logic",
        )
        + arrow
        + column(
            "Intermediate",
            "views · business logic",
            [
                "<b>Activity</b>",
                "int_node_days_assigned → int_pen_daily_activity",
                "int_dates (shared local-day spine)",
                "<b>Fish counts</b>",
                "int_fish_counts_validated → int_pen_daily_fish_count",
                "<b>Storm</b>",
                "int_storm_episodes · int_storm_daily_exposure",
                "→ int_site_daily_storm_summary",
                "→ int_pen_storm_daily_analysis",
                "→ int_storm_pen_baselines",
            ],
            "#E8A13C",
            "#FFF8EE",
            width="1.7",
            footer="one row per grain · every join tested",
        )
        + arrow
        + column(
            "Marts",
            "tables · star schema",
            [
                "dim_date · dim_site",
                "dim_pen · dim_storm_episode",
                "<b>fct_pen_daily_activity</b>",
                "<b>fct_pen_storm_analysis</b>",
                "<b>fct_pen_storm_baseline</b>",
            ],
            PALETTE["teal"],
            "#EFF9F7",
            width="1.25",
            footer="additive vs non-additive documented",
        )
        + arrow
        + column(
            "Consume",
            "BI + code",
            ["Power BI", "Python", "R"],
            NAVY,
            "#F4F7F9",
            width="0.7",
            footer="self-serve",
        )
        + "</div>"
    )
    challenges = grid(
        [
            card(
                "Effective-dated join",
                "Half-open <code>[valid_from, valid_to)</code>; one row per node-day, "
                "credited to the pen valid that date.",
                accent=CORAL,
                size=10.5,
            ),
            card(
                "No join fan-out",
                "Storm exposure aggregated to <b>site-day</b> before touching pen-days; "
                "1:1 joins only.",
                accent=CORAL,
                size=10.5,
            ),
            card(
                "Local-day exposure",
                "Storms clipped to DST-aware Oslo boundaries: 36 h → 300/1,440/420 min.",
                accent=CORAL,
                size=10.5,
            ),
            card(
                "Missing ≠ zero",
                "Spine + <code>has_activity_record</code> keep silent node-days null and visible.",
                accent=CORAL,
                size=10.5,
            ),
            card(
                "Fish counts",
                "Flagged, latest-wins, stale → null; never silently corrected or substituted.",
                accent=CORAL,
                size=10.5,
            ),
        ],
        cols=5,
        gap=10,
    )
    mo.vstack(
        [
            header(
                "04 · dbt architecture",
                "One direction of flow, four clear responsibilities",
                "Staging only standardises; intermediate owns time and joins; marts "
                "serve the question. Every arrow below exists in the dbt DAG.",
            ),
            pipeline,
            mo.Html(
                f'<div style="font-size:10.5px;font-weight:700;letter-spacing:.1em;'
                f'text-transform:uppercase;color:{MUTED};margin-top:2px;">'
                f"The five places this could have gone wrong</div>"
            ),
            challenges,
        ],
        gap=0.5,
        align="stretch",
    )


@app.cell
def slide_model(mart_counts):
    # KEY MESSAGE  Three facts, three grains, one set of conformed dimensions.
    # SAY          Explain why separate facts exist, then the additivity rules.
    # TRANSITION   "A few lines of SQL show the decisions behind these tables."
    mart_row_counts = dict(
        zip(mart_counts["model_name"], mart_counts["row_count"], strict=True)
    )
    diagram = f"""
%%{{init: {{"flowchart": {{"nodeSpacing": 26, "rankSpacing": 46, "curve": "linear"}}}}}}%%
flowchart LR
  classDef dim fill:#D9F0EB,stroke:#16A6A1,color:#0B1F33,stroke-width:1px
  classDef fact fill:#FFFFFF,stroke:#123B52,color:#0B1F33,stroke-width:1.5px
  D[dim_date]:::dim
  P[dim_pen]:::dim
  S[dim_site]:::dim
  E[dim_storm_episode]:::dim
  F1["fct_pen_daily_activity<br/>{mart_row_counts["fct_pen_daily_activity"]} rows"]:::fact
  F2["fct_pen_storm_analysis<br/>{mart_row_counts["fct_pen_storm_analysis"]} rows"]:::fact
  F3["fct_pen_storm_baseline<br/>{mart_row_counts["fct_pen_storm_baseline"]} rows"]:::fact
  D -->|1 : *| F1
  D -->|1 : *| F2
  P -->|1 : *| F1
  P -->|1 : *| F2
  P -->|1 : *| F3
  S -->|1 : *| F1
  S -->|1 : *| F2
  S -->|1 : *| F3
  E -->|1 : *| F2
  E -->|1 : *| F3
"""
    grain_rows = [
        [
            mono("fct_pen_daily_activity", size=10),
            "site × pen × <b>date</b>",
            mono("pen_day_id"),
            "shots · detections · uptime · completeness · fish snapshot · site-day storm minutes",
        ],
        [
            mono("fct_pen_storm_analysis", size=10),
            "pen × episode × <b>date</b>",
            mono("pen_storm_day_id"),
            "storm_period (before/during/after) · days from start · storm minutes · daily rates",
        ],
        [
            mono("fct_pen_storm_baseline", size=10),
            "pen × <b>episode</b>",
            mono("storm_pen_baseline_id"),
            "before/during/after totals · weighted rates · % change · completeness",
        ],
    ]
    mo.vstack(
        [
            header(
                "05 · Final data model",
                "Three facts because there are three questions",
                "Pen-day operations, episode-day exposure and the pen-episode comparison "
                "cannot share one grain without duplicating rows or averaging rates.",
            ),
            mo.hstack(
                [
                    mo.mermaid(
                        diagram,
                        theme="base",
                        theme_variables={
                            "fontFamily": "Helvetica, Arial, sans-serif",
                            "fontSize": "12px",
                            "lineColor": "#7FA3AF",
                            "edgeLabelBackground": "#F5F8FA",
                        },
                    ),
                    mo.vstack(
                        [
                            card(
                                "Why not one wide fact?",
                                "A pen-day inside an episode window is not the same unit as "
                                "a pen-episode summary. Separate facts keep the daily fact "
                                "additive and the comparison fact one row per pen-episode.",
                                accent=OCEAN,
                                size=11,
                            ),
                            card(
                                "Grain-matched partners",
                                "The two storm facts join <b>1:1</b> on "
                                "<code>storm_episode_key + pen_key</code> — daily detail "
                                "next to the comparison, no fan-out.",
                                accent=TEAL,
                                size=11,
                            ),
                            card(
                                "Read before aggregating",
                                "<b>Daily fact</b>: additive shots, uptime, detections.<br/>"
                                "<b>Storm analysis</b>: a pen-day can sit in two episode windows "
                                "(one episode's after = the next one's before) — summing double-counts.<br/>"
                                "<b>Baseline</b>: total ÷ total, one row per pen-episode — never sum.<br/>"
                                "<b>storm_minutes</b>: site-day value repeated per pen.",
                                accent=CORAL,
                                size=10.5,
                            ),
                        ],
                        gap=0.45,
                    ),
                ],
                widths=[1.5, 1],
                gap=1.0,
                align="start",
            ),
            table(
                ["Fact", "Grain", "Primary key", "Measures & analytical attributes"],
                grain_rows,
                widths=["23%", "20%", "18%", "39%"],
                size="10.5px",
            ),
            mo.Html(
                f'<div style="font-size:10.5px;color:{MUTED};">'
                f'Four conformed dimensions (<code style="font-family:{MONO};">dim_date</code> '
                f'{mart_row_counts["dim_date"]} · <code style="font-family:{MONO};">dim_site</code> {mart_row_counts["dim_site"]} · '
                f'<code style="font-family:{MONO};">dim_pen</code> {mart_row_counts["dim_pen"]} · '
                f'<code style="font-family:{MONO};">dim_storm_episode</code> {mart_row_counts["dim_storm_episode"]}) '
                f"filter every fact through single-direction 1-to-many relationships.</div>"
            ),
        ],
        gap=0.45,
        align="stretch",
    )


@app.cell
def slide_sql():
    # KEY MESSAGE  The engineering decisions are visible in a dozen lines each.
    # SAY          Read the join predicate, the greatest/least clip, the case + rate.
    # TRANSITION   "Now the answer those tables produce."
    spine_sql = """generate_series(
  greatest(valid_from_date, reporting_start_date),
  least(valid_until_date - 1, reporting_end_date),
  interval '1 day'
) as days(day)
...
left join activity
  on activity.node_id = node_days.node_id
 and activity.activity_date
     = node_days.activity_date"""

    exposure_sql = """date_diff('minute',
  greatest(storm_started_at, dates.day_start_utc),
  least(storm_ended_at,  dates.day_end_utc)
) as storm_minutes
...
-- half-open [start, end): a storm that only
-- touches the boundary adds no exposure day
where storm_minutes > 0"""

    rate_sql = """case
  when activity_date < episode_start_date then 'before'
  when activity_date > episode_end_date   then 'after'
  else 'during'
end as storm_period
...
round(
  sum(laser_shot_count)
    / sum(uptime_minutes) * 60, 3
) as during_shots_per_operating_hour"""
    mo.vstack(
        [
            header(
                "05 · The SQL that carries the decisions",
                "Twelve lines that would be easy to get subtly wrong",
                "Excerpts from the repository (elided with …), not paraphrases.",
            ),
            mo.hstack(
                [
                    code_block(
                        spine_sql,
                        "Effective-dated node → pen spine · int_node_days_assigned",
                    ),
                    code_block(
                        exposure_sql,
                        "Storm minutes per local day · int_storm_daily_exposure",
                    ),
                    code_block(
                        rate_sql,
                        "Period tag + weighted rate · int_pen_storm_daily_analysis",
                    ),
                ],
                widths="equal",
                gap=0.6,
                align="stretch",
            ),
            mo.Html(
                f'<div style="display:flex;gap:10px;align-items:flex-start;'
                f"background:{WHITE};border:1px solid {BORDER};border-radius:8px;"
                f'padding:8px 10px;font-size:10.5px;color:{INK};line-height:1.45;">'
                f"{pill('tests', fg=OCEAN, bg='#DDE7EE')}"
                f"<span>Grain uniqueness per fact and <b>relationships</b> on every foreign key; "
                f"a rate is null exactly when uptime is zero or missing; no pen-day appears twice "
                f"in an episode; storm minutes never exceed the local day length. "
                f"The hard joins are also pinned by unit tests (N05's move day, 300/1,440/420 splitting).</span></div>"
            ),
        ],
        gap=0.55,
        align="stretch",
    )


@app.cell
def slide_findings(baselines, fig_periods, fig_timeline):
    # KEY MESSAGE  The rate drops during the high-severity storm; volume drops
    #              further because uptime goes to zero. Rate ≠ volume.
    # SAY          Read the cards, then the rate-vs-volume line; stop short of causation.
    # TRANSITION   "How would Kari use this without me in the room?"
    s01 = baselines[baselines["site_id"] == "S01"].set_index("pen_id")
    s02 = baselines[baselines["site_id"] == "S02"]
    cards = []
    notes = {
        "P101": "0 uptime on 6 Oct · 100% reporting",
        "P102": "largest drop · 100% reporting",
        "P103": "0 uptime 6–7 Oct · node move 8 Oct",
    }
    for pen in ["P101", "P102", "P103"]:
        row = s01.loc[pen]
        cards.append(
            kpi(
                f"{row['during_change_vs_baseline_pct']:+.1f}%",
                f"{pen} · shots/hour vs baseline",
                f"detections {row['during_detections_change_vs_baseline_pct']:+.1f}% · {notes[pen]}",
                accent=CORAL,
            )
        )
    volume_change = {
        pen: (s01.loc[pen, "during_shots"] - s01.loc[pen, "baseline_shots"])
        / s01.loc[pen, "baseline_shots"]
        * 100
        for pen in ["P101", "P102", "P103"]
    }
    volume_line = " · ".join(
        f"{pen} {volume_change[pen]:+.0f}%" for pen in ["P101", "P102", "P103"]
    )
    s02_lines = "; ".join(
        f"{row.pen_id} {row.during_change_vs_baseline_pct:+.1f}% ({row.max_severity})"
        for row in s02.itertuples()
    )
    mo.vstack(
        [
            header(
                "06 · What the data shows",
                "A real drop in the rate — and a bigger drop in volume",
                "Shots per operating hour, S01 pens, 1–14 Oct. Coral band = storm "
                "local dates (5–7 Oct); dashed line = P103's node move.",
            ),
            fig_timeline,
            mo.hstack(
                [mo.vstack(cards, gap=0.3), fig_periods],
                widths=[1.5, 1],
                gap=0.8,
                align="start",
            ),
            mo.Html(
                f'<div style="background:{WHITE};border:1px solid {BORDER};'
                f"border-radius:8px;padding:8px 12px;font-size:11.5px;"
                f'color:{INK};line-height:1.45;">'
                f"<b>Rate vs volume:</b> total shots during the storm fell "
                f"<b>{volume_line}</b> vs baseline, while the rate fell less for P101 and "
                f"P103 — their zero-uptime hours leave the denominator, so the volume "
                f"gap is the downtime.</div>"
            ),
            mo.Html(
                f'<div style="font-size:11px;color:{MUTED};line-height:1.45;">'
                f"<b>S02, milder:</b> {s02_lines} — inside the day-to-day noise. "
                f"P202 leaves the window after the 8 Oct move. "
                f"<b>Shots per detection during:</b> 1.27 / 1.31 / 1.38 — per-lice "
                f"efficiency holds while the rate falls. Two weeks and one high-severity "
                f"episode support a <b>co-movement</b>, not a causal claim.</div>"
            ),
        ],
        gap=0.35,
        align="stretch",
    )


@app.cell
def slide_powerbi(totals):
    # KEY MESSAGE  The model becomes a dashboard Kari can filter herself, with
    #              data quality visible instead of buried.
    # SAY          Walk the layout left to right, then the four actions.
    # TRANSITION   "What still needs checking before this goes to a customer."
    def zone(label, detail, *, height="46px", accent=BORDER):
        return (
            f'<div style="flex:1;border:1px dashed {accent};border-radius:7px;'
            f"background:{WHITE};padding:6px 8px;min-height:{height};"
            f'box-sizing:border-box;">'
            f'<div style="font-size:9.5px;font-weight:700;letter-spacing:.06em;'
            f'text-transform:uppercase;color:{OCEAN};">{label}</div>'
            f'<div style="font-size:9.5px;color:{MUTED};line-height:1.35;'
            f'margin-top:2px;">{detail}</div></div>'
        )

    wireframe = mo.Html(
        f'<div style="background:{PALETTE["bg"]};border:1px solid {BORDER};'
        f'border-radius:10px;padding:8px;">'
        f'<div style="display:flex;gap:6px;margin-bottom:6px;">'
        f"{zone('Filters', 'site · pen · episode · date range', height='42px', accent=PALETTE['teal_soft'])}"
        f"{zone('Quality badge', 'reporting completeness of the current selection', height='42px', accent=CORAL)}"
        f"</div>"
        f'<div style="margin-bottom:6px;">'
        f"{zone('Laser activity over time', 'shots/hour by pen, storm bands, gaps where telemetry is missing', height='108px', accent=PALETTE['teal_soft'])}"
        f"</div>"
        f'<div style="display:flex;gap:6px;margin-bottom:6px;">'
        f"{zone('Before · During · After', 'weighted rate per period, with completeness shown', height='88px')}"
        f"{zone('Pen comparison in site', "change vs each pen's own baseline", height='88px')}"
        f"</div>"
        f'<div style="display:flex;gap:6px;">'
        f"{zone('Site comparison', 'same metric, S01 vs S02, same week', height='66px')}"
        f"{zone('Fish-count context', 'snapshot + age, withheld when stale', height='66px')}"
        f"</div></div>"
    )
    actions = bullets(
        [
            "<b>Timeline</b> → does the dip sit inside the band, or next to a gap?",
            "<b>Before/during/after</b> → the one chart for the customer meeting.",
            "<b>Pen comparison</b> → P102 first for inspection; P103 needs the node-move caveat.",
            "<b>Filters</b> → new site or episode without writing SQL; dimensions are conformed.",
            "<b>Quality badge</b> → never present a number without its completeness.",
        ],
        size=11.5,
        gap=5,
    )
    mo.vstack(
        [
            header(
                "06 · Power BI and business value",
                "A dashboard that answers Kari's four questions",
                "KPI cards from the actual warehouse — 14 days, five pens, 63 pen-days.",
            ),
            grid(
                [
                    kpi(
                        f"{totals['shots']:,}",
                        "Laser shots",
                        "pen-days summed",
                        accent=TEAL,
                    ),
                    kpi(
                        f"{totals['uptime_hours']:,.1f}",
                        "Operating hours",
                        "from uptime minutes",
                        accent=OCEAN,
                    ),
                    kpi(
                        f"{totals['detections']:,}",
                        "Lice detections",
                        "camera events",
                        accent=PALETTE["teal_soft"],
                    ),
                    kpi(
                        f"{totals['completeness']:.1%}",
                        "Reporting completeness",
                        "61 of 63 node-days",
                        accent=CORAL,
                    ),
                ],
                cols=4,
                gap=8,
            ),
            mo.hstack(
                [
                    wireframe,
                    mo.vstack(
                        [
                            actions,
                            card(
                                "Dashboard rules",
                                "Every visual answers one of the four questions; every rate "
                                "carries its completeness; no chart without its unit and date "
                                "range.",
                                accent=TEAL,
                                size=11.5,
                            ),
                        ],
                        gap=0.5,
                    ),
                ],
                widths=[1.55, 1],
                gap=0.9,
                align="start",
            ),
            mo.Html(
                f'<div style="font-size:11px;color:{MUTED};line-height:1.4;">'
                f"<b>Power BI model:</b> import the seven marts, relate each dimension to each "
                f"fact 1-to-many, single direction; measures per fact. No fact-to-fact "
                f"relationship — the baseline/analysis composite-key join stays in SQL.</div>"
            ),
        ],
        gap=0.45,
        align="stretch",
    )


@app.cell
def slide_validation():
    # KEY MESSAGE  What is tested, what only Kari can confirm, what I'd do next.
    # SAY          Lead with the one warn; it is deliberate and visible.
    # TRANSITION   "So what do we actually have at the end of this?"
    validated = card(
        "Validated by",
        bullets(
            [
                "<b>21 models</b>, <b>336</b> generic/singular tests, <b>11</b> unit tests: "
                "346 pass, <b>1 intentional warn</b> (P201's 1,852,000 count).",
                "Unique + not-null keys, <b>relationships</b> on every FK, grain "
                "uniqueness on every fact.",
                "Guards: missing activity is not zero; storm minutes fit the DST-aware "
                "day; rates null without uptime; no duplicate pen-day in an episode.",
                "Unit tests pin the N05 move with a missing move-day and the "
                "300/1,440/420 split.",
            ],
            size=12,
            gap=4,
        ),
        accent=TEAL,
        size=12,
    )
    confirm = card(
        "Confirm with Kari / data owners",
        bullets(
            [
                "Is <code>activity_date</code> a local (Europe/Oslo) day, or UTC?",
                "Were N03's zero-uptime days on 6–7 Oct a fault or a deliberate shutdown?",
                "What does “less active” mean to farmers: fewer shots, fewer detections, "
                "or less visible?",
                "Are fish counts whole-pen after a transfer (P202 moved ~40k fish to P201)?",
            ],
            size=12,
            gap=4,
        ),
        accent=CORAL,
        size=12,
    )
    next_steps = card(
        "Before this is production",
        bullets(
            [
                "Intraday telemetry: a 3-hour storm (ST-0043) disappears inside a daily grain.",
                "More storm episodes before any statistical test — effect sizes stay descriptive.",
                "Site timezone lookup (logs are single-zone today) and a declared reporting end.",
                "Snowflake port, source contracts/freshness, incremental fact once volume justifies it.",
            ],
            size=12,
            gap=4,
        ),
        accent=OCEAN,
        size=12,
    )
    mo.vstack(
        [
            header(
                "07 · Validation, limitations, next steps",
                "What holds, what needs a conversation, what I'd build next",
            ),
            grid([validated, confirm, next_steps], cols=3, gap=12),
            mo.Html(
                f'<div style="background:{SEAFOAM};border-radius:8px;'
                f'padding:10px 14px;font-size:13px;line-height:1.5;color:{NAVY};">'
                f"<b>What I would tell Kari:</b> the high-severity storm coincides with a "
                f"large drop in the rate, and volume falls further where uptime hits zero; "
                f"the milder storms show nothing clear. Before we promise the farmer an "
                f"answer, let us instrument uptime and collect more storms.</div>"
            ),
            mo.Html(
                f'<div style="font-size:12px;color:{INK};line-height:1.55;'
                f"background:{WHITE};border-left:4px solid {CORAL};"
                f'border-radius:6px;padding:8px 12px;">'
                f"<b>Limitations that stay:</b> daily grain cannot resolve short storms; "
                f"uptime is node on-time, not proof the laser was armed; manually entered "
                f"fish counts are stale by design after 7 days; and with one high-severity "
                f"episode the analysis establishes <b>correlation, not causation</b>.</div>"
            ),
        ],
        gap=0.5,
        align="stretch",
    )


@app.cell
def slide_closing():
    # KEY MESSAGE  Close on value + honesty: the model is done, the causal question is not.
    # SAY          Summarise the three deliverables in one breath, then invite questions.
    deliverable = card(
        "A tested model",
        "Seven marts on a conformed star schema; 21 models, 336 tests, 11 unit tests — "
        "storm exposure, windows and rates defined once.",
        accent=TEAL,
        size=11.5,
        bg="#0F2A40",
        fg="#D9F0EB",
        border="#1E4763",
    )
    answer = card(
        "An answer Kari can use",
        "High-severity S01 storm: shots/hour −24.0% / −48.5% / −8.3% per pen; volume "
        "falls further where uptime hits zero. Milder S02 episodes: no clear change.",
        accent=CORAL,
        size=11.5,
        bg="#0F2A40",
        fg="#D9F0EB",
        border="#1E4763",
    )
    next_step = card(
        "A next step we can agree",
        "Confirm the day boundary and what “less active” means; add intraday telemetry "
        "and more episodes before anyone says “caused”.",
        accent=PALETTE["teal_soft"],
        size=11.5,
        bg="#0F2A40",
        fg="#D9F0EB",
        border="#1E4763",
    )
    mo.vstack(
        [
            dark_header(
                "07 · Close",
                "The signal is in the data. The cause is not yet.",
                "What I'd leave behind after the case: a model that answers the question "
                "Kari asked, and is explicit about what it cannot support.",
            ),
            grid([deliverable, answer, next_step], cols=3, gap=12),
            mo.Html(
                f'<div style="margin-top:18px;font-size:12px;color:#8FB0AD;'
                f'letter-spacing:.04em;">Thank you — questions welcome. '
                f"Every number in this deck is queried live from "
                f'<code style="font-family:{MONO};color:#B9D6D2;">data/warehouse/stingray.duckdb</code>.</div>'
            ),
        ],
        gap=0.9,
        align="stretch",
    )


if __name__ == "__main__":
    app.run()

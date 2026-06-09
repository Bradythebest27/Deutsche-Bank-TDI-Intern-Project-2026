from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.analysis import COVID_END, COVID_START


PLOT_TEMPLATE = "plotly_dark"
ACCENT = "#39d5ff"
SECONDARY = "#a7f3d0"
WARNING = "#f5c542"
STOCK_PALETTE = [
    "#39d5ff",
    "#60a5fa",
    "#fda4af",
    "#fb7185",
    "#86efac",
    "#2dd4bf",
    "#facc15",
    "#c4b5fd",
    "#93c5fd",
]
EVENT_COLOR_MAP = {
    "Ukraine War": "#38bdf8",
    "Middle East": "#f59e0b",
    "Venezuela": "#a78bfa",
    "Iran": "#ef4444",
}
DEFAULT_EVENT_COLOR = "#94a3b8"


def apply_finance_layout(fig: go.Figure, title: str | None = None) -> go.Figure:
    fig.update_layout(
        template=PLOT_TEMPLATE,
        title=title,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(7,12,20,0.92)",
        font={"family": "Inter, Segoe UI, Arial, sans-serif", "color": "#e5edf7"},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        margin={"l": 28, "r": 24, "t": 58, "b": 36},
        hovermode="x unified",
    )
    fig.update_xaxes(gridcolor="rgba(148,163,184,0.14)", zerolinecolor="rgba(148,163,184,0.2)")
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.14)", zerolinecolor="rgba(148,163,184,0.2)")
    return fig


def indexed_return_chart(
    indexed: pd.DataFrame,
    events: pd.DataFrame,
    tickers: list[str],
    include_covid: bool = False,
) -> go.Figure:
    plot_frame = indexed[tickers].reset_index().melt(id_vars="Date", var_name="Ticker", value_name="Index")
    fig = px.line(plot_frame, x="Date", y="Index", color="Ticker", color_discrete_sequence=STOCK_PALETTE)
    fig = apply_finance_layout(fig, "Indexed Total Return Comparison")

    fig.add_vrect(
        x0=COVID_START,
        x1=COVID_END,
        fillcolor="rgba(245, 197, 66, 0.08)" if include_covid else "rgba(245, 197, 66, 0.13)",
        line_width=0,
        annotation_text="COVID shown; excluded from baseline" if include_covid else "COVID omitted from chart data",
        annotation_position="top left",
    )

    finite_values = pd.to_numeric(plot_frame["Index"], errors="coerce").dropna()
    y_min = max(0, finite_values.min() * 0.96) if not finite_values.empty else 0
    y_max = finite_values.max() * 1.03 if not finite_values.empty else 100
    y_points = [y_min + (y_max - y_min) * step / 24 for step in range(25)]
    chart_start = pd.to_datetime(indexed.index.min()) if not indexed.empty else None
    chart_end = pd.to_datetime(indexed.index.max()) if not indexed.empty else None
    _add_event_marker_traces(fig, events, y_points, chart_start, chart_end)

    fig.update_yaxes(title="Indexed value, first available date = 100")
    fig.update_traces(connectgaps=False, selector={"mode": "lines"})
    fig.update_layout(
        hovermode="closest",
        hoverlabel={
            "align": "left",
            "bgcolor": "rgba(15,23,42,0.96)",
            "bordercolor": "rgba(148,163,184,0.55)",
            "font_size": 12,
        },
        legend={
            "orientation": "h",
            "yanchor": "top",
            "y": -0.18,
            "xanchor": "left",
            "x": 0,
            "font": {"size": 11},
            "title": {"text": ""},
        },
        margin={"l": 28, "r": 24, "t": 58, "b": 82},
    )
    return fig


def _add_event_marker_traces(
    fig: go.Figure,
    events: pd.DataFrame | None,
    y_points: list[float],
    chart_start: pd.Timestamp | None,
    chart_end: pd.Timestamp | None,
) -> None:
    if events is None or events.empty or not y_points:
        return

    shown_event_categories: set[str] = set()
    for _, event in events.iterrows():
        event_date = pd.to_datetime(event["date"])
        if chart_start is not None and chart_end is not None and not (chart_start <= event_date <= chart_end):
            continue
        category = str(event.get("category", "Event"))
        event_name = _wrap_hover_text(event.get("event", "Geopolitical event"))
        source = _wrap_hover_text(event.get("source", "Source unavailable"), width=36, max_chars=72)
        color = EVENT_COLOR_MAP.get(category, DEFAULT_EVENT_COLOR)
        showlegend = False
        shown_event_categories.add(category)

        fig.add_trace(
            go.Scatter(
                x=[event_date] * len(y_points),
                y=y_points,
                mode="lines",
                name=f"Event: {category}",
                legendgroup=f"event-{category}",
                showlegend=showlegend,
                line={"color": color, "width": 2.0, "dash": "dot"},
                opacity=0.84,
                customdata=[[event_name, category, source]] * len(y_points),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Category: %{customdata[1]}<br>"
                    "Date: %{x|%b %d, %Y}<br>"
                    "Source: %{customdata[2]}"
                    "<extra></extra>"
                ),
            )
        )


def _wrap_hover_text(value: object, width: int = 34, max_chars: int = 80) -> str:
    text = str(value)
    if len(text) > max_chars:
        text = text[: max_chars - 3].rstrip() + "..."

    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return "<br>".join(lines)


def event_study_chart(event_study: pd.DataFrame) -> go.Figure:
    if event_study.empty:
        fig = go.Figure()
        return apply_finance_layout(fig, "Event Study: No Data Available")

    grouped = (
        event_study.groupby(["Offset", "Ticker"], as_index=False)["Cumulative Abnormal Return"]
        .mean()
        .sort_values("Offset")
    )
    fig = px.line(
        grouped,
        x="Offset",
        y="Cumulative Abnormal Return",
        color="Ticker",
        markers=True,
    )
    fig = apply_finance_layout(fig, "Average Cumulative Abnormal Return Around Events")
    fig.add_vline(x=0, line_width=1, line_dash="dash", line_color=WARNING)
    fig.update_yaxes(tickformat=".1%", title="Cumulative abnormal return")
    fig.update_xaxes(title="Trading days from event")
    return fig


def regime_bar_chart(comparison: pd.DataFrame, tickers: list[str]) -> go.Figure:
    columns = [
        "Ticker",
        "Pre-COVID Annualized Return",
        "Post-2022 Annualized Return",
        "Post-2022 Excess vs Benchmark",
    ]
    plot_frame = comparison[comparison["Ticker"].isin(tickers)][columns].melt(
        id_vars="Ticker",
        var_name="Metric",
        value_name="Value",
    )
    fig = px.bar(plot_frame, x="Ticker", y="Value", color="Metric", barmode="group")
    fig = apply_finance_layout(fig, "Returns Pre vs Post COVID")
    fig.update_layout(legend_title_text="")
    fig.update_yaxes(tickformat=".1%", title="Annualized return")
    return fig


def premium_gauge(score: float) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": " pts"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": ACCENT},
                "bgcolor": "rgba(15,23,42,0.95)",
                "borderwidth": 1,
                "bordercolor": "rgba(148,163,184,0.35)",
                "steps": [
                    {"range": [0, 42], "color": "rgba(16,185,129,0.28)"},
                    {"range": [42, 68], "color": "rgba(245,197,66,0.28)"},
                    {"range": [68, 100], "color": "rgba(239,68,68,0.28)"},
                ],
            },
        )
    )
    fig = apply_finance_layout(fig, "Priced-In Premium Score")
    fig.update_layout(height=260, margin={"l": 16, "r": 16, "t": 44, "b": 12})
    return fig


def budget_spending_chart(budgets: pd.DataFrame, countries: list[str]) -> go.Figure:
    plot_frame = budgets[budgets["Country"].isin(countries)].copy()
    plot_frame["Year Label"] = plot_frame["Year"].astype(str)
    fig = px.line(
        plot_frame,
        x="Year Label",
        y="Defense Spending % GDP",
        color="Country",
        markers=True,
    )
    fig = apply_finance_layout(fig, "NATO Defense Spending as Share of GDP")
    fig.add_hline(y=2.0, line_dash="dash", line_color=WARNING, annotation_text="2% guideline")
    fig.update_yaxes(ticksuffix="%", title="% of GDP")
    fig.update_xaxes(title="")
    return fig


def derivative_chart(
    derivative_timeline: pd.DataFrame,
    tickers: list[str],
    metric: str = "Smoothed Velocity",
    events: pd.DataFrame | None = None,
    include_covid: bool = False,
) -> go.Figure:
    if derivative_timeline.empty:
        fig = go.Figure()
        return apply_finance_layout(fig, "Price Derivative Diagnostics")

    plot_frame = derivative_timeline[derivative_timeline["Ticker"].isin(tickers)].copy()
    fig = px.line(plot_frame, x="Date", y=metric, color="Ticker", color_discrete_sequence=STOCK_PALETTE)
    fig = apply_finance_layout(fig, f"Price Derivative: {metric}")
    fig.add_hline(y=0, line_width=1, line_dash="dot", line_color="rgba(229,237,247,0.42)")

    finite_values = pd.to_numeric(plot_frame[metric], errors="coerce").dropna()
    if not finite_values.empty:
        y_min = finite_values.quantile(0.02)
        y_max = finite_values.quantile(0.98)
        if y_min == y_max:
            y_min, y_max = finite_values.min(), finite_values.max()
        padding = max((y_max - y_min) * 0.12, 0.01)
        y_min -= padding
        y_max += padding
    else:
        y_min, y_max = -0.1, 0.1
    y_points = [y_min + (y_max - y_min) * step / 24 for step in range(25)]
    chart_start = pd.to_datetime(plot_frame["Date"].min()) if not plot_frame.empty else None
    chart_end = pd.to_datetime(plot_frame["Date"].max()) if not plot_frame.empty else None

    fig.add_vrect(
        x0=COVID_START,
        x1=COVID_END,
        fillcolor="rgba(245, 197, 66, 0.08)" if include_covid else "rgba(245, 197, 66, 0.13)",
        line_width=0,
        annotation_text="COVID shown" if include_covid else "COVID omitted",
        annotation_position="top left",
    )
    _add_event_marker_traces(fig, events, y_points, chart_start, chart_end)

    fig.update_traces(connectgaps=False, selector={"mode": "lines"})
    fig.update_yaxes(tickformat=".1%", title=metric)
    fig.update_layout(
        hovermode="closest",
        hoverlabel={
            "align": "left",
            "bgcolor": "rgba(15,23,42,0.96)",
            "bordercolor": "rgba(148,163,184,0.55)",
            "font_size": 12,
        },
        legend={
            "orientation": "h",
            "yanchor": "top",
            "y": -0.18,
            "xanchor": "left",
            "x": 0,
            "font": {"size": 11},
            "title": {"text": ""},
        },
        margin={"l": 28, "r": 24, "t": 58, "b": 82},
    )
    return fig


def priced_in_score_chart(scorecard: pd.DataFrame) -> go.Figure:
    if scorecard.empty:
        fig = go.Figure()
        return apply_finance_layout(fig, "Priced-In Score")

    plot_frame = scorecard.sort_values("Priced-In Score", ascending=True)
    fig = px.bar(
        plot_frame,
        x="Priced-In Score",
        y="Ticker",
        color="Investment Action",
        orientation="h",
        text="Priced-In Score",
        color_discrete_map={
            "Selective Buy Watchlist": "#10b981",
            "Hold / Fairly Priced": "#f5c542",
            "Avoid Chasing": "#ef4444",
        },
    )
    fig = apply_finance_layout(fig, "Composite Priced-In Score")
    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
    fig.update_layout(showlegend=False)
    fig.update_xaxes(range=[0, 100], title="Higher score means more conflict premium is already priced in")
    fig.update_yaxes(title="")
    return fig


def valuation_quality_chart(scorecard: pd.DataFrame) -> go.Figure:
    if scorecard.empty:
        fig = go.Figure()
        return apply_finance_layout(fig, "Valuation vs Quality")

    plot_frame = scorecard.copy()
    fig = px.scatter(
        plot_frame,
        x="Forward P/E",
        y="Backlog to Revenue",
        size="Revenue",
        color="Investment Action",
        hover_name="Ticker",
        hover_data=["EV/EBITDA", "Effective Operating Margin", "Effective Revenue Growth", "Priced-In Score"],
        color_discrete_map={
            "Selective Buy Watchlist": "#10b981",
            "Hold / Fairly Priced": "#f5c542",
            "Avoid Chasing": "#ef4444",
        },
    )
    fig = apply_finance_layout(fig, "Valuation vs Backlog Support")
    fig.update_layout(showlegend=False)
    fig.update_yaxes(title="Backlog / revenue")
    fig.update_xaxes(title="Forward P/E")
    return fig


def historical_valuation_chart(valuation_history: pd.DataFrame, ticker: str, metric: str) -> go.Figure:
    plot_frame = valuation_history[valuation_history["Ticker"] == ticker].copy()
    if plot_frame.empty or metric not in plot_frame.columns:
        fig = go.Figure()
        return apply_finance_layout(fig, f"{ticker} Historical Valuation")

    plot_frame["Chart Period"] = pd.to_datetime(plot_frame["Date"]).dt.to_period("Q").astype(str)
    if "Period Type" in plot_frame.columns:
        plot_frame["Period Priority"] = plot_frame["Period Type"].map({"Annual": 0, "Quarterly": 1}).fillna(0)
        plot_frame = (
            plot_frame.sort_values(["Date", "Period Priority"])
            .drop_duplicates(subset=["Chart Period"], keep="last")
            .drop(columns=["Period Priority"])
        )

    plot_frame = plot_frame.dropna(subset=[metric])
    plot_frame = plot_frame.sort_values("Date")
    hover_columns = [column for column in ["Date", "Period Type", "Fiscal Year"] if column in plot_frame.columns]
    fig = px.line(
        plot_frame,
        x="Chart Period",
        y=metric,
        markers=True,
        hover_data=hover_columns,
    )
    fig = apply_finance_layout(fig, f"{ticker} {metric}")
    fig.update_yaxes(title=metric)
    fig.update_xaxes(title="", categoryorder="array", categoryarray=plot_frame["Chart Period"].tolist())
    fig.update_layout(showlegend=False)
    return fig


def scenario_chart(scenario_frame: pd.DataFrame) -> go.Figure:
    if scenario_frame.empty:
        fig = go.Figure()
        return apply_finance_layout(fig, "Scenario Projection")

    plot_frame = scenario_frame.sort_values("3Y Indexed Outcome", ascending=True)
    plot_frame["Scenario Annual Return Label"] = plot_frame["Scenario Annual Return"].map(lambda value: f"{value:.2%}")
    plot_frame["Scenario Bar Label"] = plot_frame.apply(
        lambda row: (
            f"{row['3Y Indexed Outcome']:.0f} | "
            f"{row['Scenario Annual Return']:.2%} | "
            f"Score {row['Priced-In Score']:.0f}"
        ),
        axis=1,
    )
    fig = px.bar(
        plot_frame,
        x="3Y Indexed Outcome",
        y="Ticker",
        orientation="h",
        color="Scenario Annual Return",
        color_continuous_scale=["#ef4444", "#f5c542", "#10b981"],
        text="Scenario Bar Label",
        hover_data=["Scenario Annual Return", "Premium Adjustment", "Priced-In Score"],
    )
    fig = apply_finance_layout(fig, "Scenario Analysis: 3Y Indexed Outcome")
    fig.add_vline(x=100, line_dash="dot", line_color="rgba(229,237,247,0.45)")
    fig.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        textfont={"color": "#03121f", "size": 12},
    )
    fig.update_layout(
        coloraxis_colorbar={
            "title": "Scenario Annual Return",
            "orientation": "h",
            "x": 0.5,
            "xanchor": "center",
            "y": -0.36,
            "yanchor": "top",
            "len": 0.72,
            "thickness": 12,
            "tickformat": ".0%",
        },
        margin={"l": 28, "r": 24, "t": 58, "b": 116},
    )
    fig.update_xaxes(title="Indexed value after 3 years, start = 100")
    fig.update_yaxes(title="")
    return fig

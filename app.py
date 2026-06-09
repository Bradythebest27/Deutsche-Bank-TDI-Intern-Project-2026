from __future__ import annotations

from datetime import UTC, date, datetime

import pandas as pd
import streamlit as st

from src.analysis import (
    COVID_END,
    COVID_START,
    POST_UKRAINE_START,
    aggregate_verdict,
    backlog_refresh_report,
    build_priced_in_score,
    compare_pre_post_periods,
    daily_returns,
    data_quality_report,
    derivative_diagnostics,
    event_sensitivity,
    historical_valuation_series,
    indexed_performance,
    pivot_prices,
    run_event_study,
    scenario_projection,
    single_ticker_report,
    single_ticker_report_markdown,
    valuation_snapshot,
)
from src.data_loader import (
    CACHE_TTL_HOURS,
    load_company_profiles,
    load_defense_budgets,
    load_events,
    load_financial_statements,
    load_manual_fundamentals,
    load_market_data,
)
from src.visuals import (
    budget_spending_chart,
    derivative_chart,
    event_study_chart,
    historical_valuation_chart,
    indexed_return_chart,
    premium_gauge,
    priced_in_score_chart,
    regime_bar_chart,
    scenario_chart,
    valuation_quality_chart,
)


CONTRACTORS = {
    "LMT": "Lockheed Martin",
    "RTX": "RTX / Raytheon",
    "NOC": "Northrop Grumman",
    "GD": "General Dynamics",
    "BA.L": "BAE Systems",
    "RHM.DE": "Rheinmetall",
}

BENCHMARKS = {
    "SPY": "S&P 500 ETF",
    "ITA": "iShares U.S. Aerospace & Defense ETF",
    "XAR": "SPDR S&P Aerospace & Defense ETF",
}

DEFAULT_START = date(2017, 1, 1)
DEFAULT_BUDGET_SERIES = ["NATO Europe and Canada", "United States", "United Kingdom", "Germany", "Poland"]
DEFAULT_DISABLED_CONTRACTORS = {"RHM.DE"}
VALUATION_METRIC_EXPLANATIONS = {
    "Historical P/E": "Price-to-earnings compares market value with annualized net income. It shows how much investors paid for each dollar of earnings.",
    "Historical P/S": "Price-to-sales compares market value with annualized revenue. It is useful when earnings are noisy but sales are more stable.",
    "Historical EV/EBITDA": "EV/EBITDA compares enterprise value with annualized operating cash earnings before depreciation and amortization, adjusting for debt and cash.",
}


st.set_page_config(
    page_title="Defense Risk Premium Terminal",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    :root {
        --panel: rgba(15, 23, 42, 0.84);
        --panel-border: rgba(148, 163, 184, 0.22);
        --text: #e5edf7;
        --muted: #94a3b8;
        --accent: #39d5ff;
    }
    .stApp {
        background:
            radial-gradient(circle at top right, rgba(57, 213, 255, 0.06), transparent 32rem),
            linear-gradient(180deg, rgba(7,12,20,0.98) 0%, rgba(3,7,18,1) 100%);
        color: var(--text);
    }
    [data-testid="stSidebar"] {
        background: rgba(8, 13, 24, 0.98);
        border-right: 1px solid var(--panel-border);
    }
    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 2.5rem;
    }
    h1, h2, h3 {
        letter-spacing: 0;
    }
    .terminal-title {
        border-bottom: 1px solid var(--panel-border);
        padding-bottom: 0.85rem;
        margin-bottom: 1rem;
    }
    .terminal-title h1 {
        font-size: 1.85rem;
        margin: 0;
    }
    .terminal-title p {
        color: var(--muted);
        margin: 0.35rem 0 0 0;
        font-size: 0.94rem;
    }
    .metric-card {
        background: var(--panel);
        border: 1px solid var(--panel-border);
        border-radius: 8px;
        padding: 1rem;
        min-height: 128px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.22);
    }
    .metric-label {
        color: var(--muted);
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.35rem;
    }
    .metric-value {
        color: var(--text);
        font-size: 1.32rem;
        font-weight: 700;
        line-height: 1.16;
    }
    .metric-note {
        color: var(--muted);
        font-size: 0.82rem;
        margin-top: 0.45rem;
    }
    .section-band {
        background: rgba(15, 23, 42, 0.62);
        border: 1px solid var(--panel-border);
        border-radius: 8px;
        padding: 0.9rem 1rem;
        margin: 0.7rem 0 1rem 0;
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--panel-border);
        border-radius: 8px;
    }
    .help-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.35rem;
        height: 1.35rem;
        border-radius: 999px;
        border: 1px solid rgba(57, 213, 255, 0.45);
        color: var(--accent);
        font-size: 0.82rem;
        font-weight: 700;
        cursor: help;
        user-select: none;
    }
    .help-badge-wrap {
        display: flex;
        justify-content: center;
        padding-top: 9.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_market_data(
    tickers: tuple[str, ...],
    start: str,
    end: str,
    interval: str,
    refresh_token: int,
) -> tuple[pd.DataFrame, dict[str, object]]:
    return load_market_data(list(tickers), start, end, interval, force_refresh=refresh_token > 0)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_profiles(tickers: tuple[str, ...], refresh_token: int) -> tuple[pd.DataFrame, dict[str, object]]:
    return load_company_profiles(list(tickers), force_refresh=refresh_token > 0)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_statements(tickers: tuple[str, ...], refresh_token: int) -> tuple[pd.DataFrame, dict[str, object]]:
    return load_financial_statements(list(tickers), force_refresh=refresh_token > 0)


def pct(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{value:.1%}"


def points(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{value:.0f}"


def format_cache_timestamp(timestamp: object) -> tuple[str, str]:
    if not timestamp or pd.isna(timestamp):
        return "n/a", "Date unavailable"

    try:
        parsed = datetime.fromisoformat(str(timestamp))
        local_time = parsed.astimezone()
        return local_time.strftime("%I:%M %p").lstrip("0"), local_time.strftime("%b %d, %Y")
    except (TypeError, ValueError):
        return "n/a", str(timestamp)


def report_download(
    verdict: dict[str, object],
    selected_contractors: list[str],
    benchmark: str,
    event_window: int,
    scenario_name: str,
    scorecard: pd.DataFrame,
    scenario_frame: pd.DataFrame,
    quality: pd.DataFrame,
) -> str:
    score_columns = ["Ticker", "Priced-In Score", "Investment Action", "Backlog to Revenue", "Forward P/E"]
    scenario_columns = ["Ticker", "Scenario Annual Return", "3Y Indexed Outcome", "Premium Adjustment"]
    return "\n".join(
        [
            "# Defense Risk Premium Dashboard Export",
            "",
            f"Generated: {datetime.now(UTC).isoformat(timespec='seconds')} UTC",
            f"Selected contractors: {', '.join(selected_contractors)}",
            f"Benchmark: {benchmark}",
            f"Event window: {event_window} trading days",
            f"Scenario: {scenario_name}",
            "",
            f"## Verdict: {verdict['verdict']}",
            "",
            str(verdict["summary"]),
            "",
            "## Composite Scorecard",
            "",
            "```csv",
            scorecard[[column for column in score_columns if column in scorecard.columns]].to_csv(index=False),
            "```",
            "",
            "## Scenario Projection",
            "",
            "```csv",
            scenario_frame[[column for column in scenario_columns if column in scenario_frame.columns]].to_csv(index=False),
            "```",
            "",
            "## Data Quality",
            "",
            "```csv",
            quality.to_csv(index=False),
            "```",
        ]
    )


def default_selected_contractors() -> list[str]:
    excluded_raw = st.query_params.get("exclude_contractors", "")
    if isinstance(excluded_raw, list):
        excluded_raw = ",".join(excluded_raw)
    excluded = {ticker.strip().upper() for ticker in str(excluded_raw).split(",") if ticker.strip()}
    selected = [
        ticker
        for ticker in CONTRACTORS
        if ticker.upper() not in excluded and ticker.upper() not in DEFAULT_DISABLED_CONTRACTORS
    ]
    return selected or list(CONTRACTORS.keys())


def available_benchmark(selected_benchmark: str, returns: pd.DataFrame) -> str | None:
    if selected_benchmark in returns.columns and returns[selected_benchmark].notna().any():
        return selected_benchmark
    for fallback in BENCHMARKS:
        if fallback in returns.columns and returns[fallback].notna().any():
            return fallback
    return None


with st.sidebar:
    st.subheader("Universe")
    selected_contractors = st.multiselect(
        "Contractors",
        options=list(CONTRACTORS.keys()),
        default=default_selected_contractors(),
        format_func=lambda ticker: f"{ticker} - {CONTRACTORS[ticker]}",
    )
    benchmark = st.selectbox(
        "Benchmark",
        options=list(BENCHMARKS.keys()),
        index=1,
        format_func=lambda ticker: f"{ticker} - {BENCHMARKS[ticker]}",
    )
    custom_ticker_input = st.text_input(
        "Custom defense ticker report",
        value="",
        placeholder="Example: HII, LHX, TXT, AVAV",
        help="Enter any publicly traded defense or aerospace contractor ticker supported by Yahoo Finance.",
    )
    custom_ticker = custom_ticker_input.upper().strip()

    st.subheader("Market Window")
    start_date = st.date_input("Start date", value=DEFAULT_START, min_value=date(2010, 1, 1))
    end_date = st.date_input("End date", value=date.today(), min_value=start_date)
    event_window = st.select_slider("Event window", options=[3, 5, 10, 20], value=10)
    include_covid_visuals = st.checkbox(
        "Include COVID in charts",
        value=False,
        help="When off, 2020-2021 is omitted from visual time-series and derivative calculations so later conflict moves are easier to read.",
    )
    derivative_metric = st.selectbox(
        "Derivative metric",
        ["Smoothed Velocity", "Smoothed Acceleration", "Rolling Volatility", "Rolling Velocity", "Rolling Acceleration"],
    )
    derivative_smoothing_window = st.slider(
        "Derivative smoothing days",
        min_value=21,
        max_value=126,
        value=63,
        step=21,
        help="Applies an additional rolling average to the derivative lines. Higher values are smoother.",
    )

    st.subheader("Scenario")
    scenario_name = st.selectbox("Conflict scenario", ["Base case", "De-escalation", "Escalation"])
    manual_adjustment = st.slider("Manual annual premium adjustment", -10.0, 10.0, 0.0, 0.5) / 100

    st.subheader("API Protection")
    refresh_clicked = st.button("Refresh Data", width="stretch")
    st.caption(f"Disk cache TTL: {CACHE_TTL_HOURS} hours. Cached data is reused before API calls.")


if not selected_contractors:
    st.warning("Select at least one contractor to run the dashboard.")
    st.stop()

if refresh_clicked:
    cached_market_data.clear()
    cached_profiles.clear()
    cached_statements.clear()

refresh_token = int(datetime.now(UTC).timestamp()) if refresh_clicked else 0
custom_tickers = [custom_ticker] if custom_ticker else []
all_tickers = tuple(sorted(set(selected_contractors + list(BENCHMARKS.keys()) + custom_tickers)))
profile_tickers = tuple(sorted(set(selected_contractors + list(BENCHMARKS.keys()) + custom_tickers)))
statement_tickers = tuple(sorted(set(selected_contractors + custom_tickers)))

st.markdown(
    """
    <div class="terminal-title">
        <h1>Defense Spending & Geopolitical Risk Premium</h1>
        <p>Professional market terminal for testing whether defense equities are durable holdings or already priced for conflict.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

events = load_events()
fundamentals = load_manual_fundamentals()
budgets = load_defense_budgets()

try:
    with st.spinner("Loading market data through cache-protected Yahoo Finance calls..."):
        market_data, market_meta = cached_market_data(
            all_tickers,
            start_date.isoformat(),
            end_date.isoformat(),
            "1d",
            refresh_token,
        )
except Exception as exc:
    st.error(f"Market data could not be loaded: {exc}")
    st.stop()

profiles, profile_meta = cached_profiles(profile_tickers, refresh_token)
statements, statement_meta = cached_statements(statement_tickers, refresh_token)

prices = pivot_prices(market_data)
returns = daily_returns(prices)
visual_prices = prices.copy()
if not include_covid_visuals:
    covid_mask = (visual_prices.index >= pd.to_datetime(COVID_START)) & (
        visual_prices.index <= pd.to_datetime(COVID_END)
    )
    visual_prices.loc[covid_mask] = pd.NA

indexed = indexed_performance(prices)
display_indexed = indexed.copy()
if not include_covid_visuals:
    covid_index_mask = (display_indexed.index >= pd.to_datetime(COVID_START)) & (
        display_indexed.index <= pd.to_datetime(COVID_END)
    )
    display_indexed.loc[covid_index_mask] = pd.NA
effective_benchmark = available_benchmark(benchmark, returns)
if effective_benchmark is None:
    st.error("No benchmark price data was returned. Yahoo Finance may be rate-limiting this deployment; try Refresh Data again in a few minutes.")
    st.stop()
if effective_benchmark != benchmark:
    st.warning(
        f"`{benchmark}` was not returned by Yahoo Finance, likely because of rate limiting. "
        f"Using `{effective_benchmark}` as the benchmark for this run."
    )

comparison = compare_pre_post_periods(returns, effective_benchmark)
event_data = run_event_study(returns, effective_benchmark, events, window=event_window, tickers=selected_contractors)
event_score = event_sensitivity(event_data, event_window)
derivative_summary, derivative_timeline = derivative_diagnostics(
    visual_prices,
    smoothing_window=derivative_smoothing_window,
)
valuation_history = historical_valuation_series(statements, prices)
valuation_summary = valuation_snapshot(valuation_history, profiles)
backlog_refresh = backlog_refresh_report(fundamentals, statements)
scorecard = build_priced_in_score(
    comparison,
    profiles,
    fundamentals,
    derivative_summary,
    event_score,
    selected_contractors,
    valuation_summary,
)
verdict = aggregate_verdict(scorecard)
scenario_frame = scenario_projection(
    comparison,
    scorecard,
    selected_contractors,
    scenario_name,
    manual_adjustment,
)
quality = data_quality_report(market_data, prices, profiles, fundamentals, selected_contractors + [effective_benchmark])
chart_tickers = [ticker for ticker in selected_contractors + [effective_benchmark] if ticker in display_indexed.columns]

contractor_rows = comparison[comparison["Ticker"].isin(selected_contractors)]
median_excess = contractor_rows["Post-2022 Excess vs Benchmark"].median(skipna=True)
median_post_return = contractor_rows["Post-2022 Annualized Return"].median(skipna=True)
price_cache_time, price_cache_date = format_cache_timestamp(market_meta.get("cached_at"))

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Investment Verdict</div>
            <div class="metric-value">{verdict["verdict"]}</div>
            <div class="metric-note">{verdict["summary"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Median Priced-In Score</div>
            <div class="metric-value">{points(verdict["score"])} / 100</div>
            <div class="metric-note">Higher means the premium looks more fully capitalized.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Median Excess vs {effective_benchmark}</div>
            <div class="metric-value">{pct(median_excess)}</div>
            <div class="metric-note">Benchmark-relative post-Ukraine annualized return.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Price Cache</div>
            <div class="metric-value">{price_cache_time}</div>
            <div class="metric-note">{price_cache_date} | {market_meta.get("status", "unknown")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if market_meta.get("warning"):
    st.warning(str(market_meta["warning"]))
if profile_meta.get("warning"):
    st.info(str(profile_meta["warning"]))

tabs = st.tabs(
    [
        "Market Regimes",
        "Priced-In Score",
        "Derivatives",
        "Budget & Backlog",
        "Historical Valuation",
        "Custom Ticker Report",
        "Events",
        "Scenario & Export",
        "Data Quality",
    ]
)

with tabs[0]:
    st.plotly_chart(
        indexed_return_chart(display_indexed, events, chart_tickers, include_covid=include_covid_visuals),
        width="stretch",
    )
    left, right = st.columns([1.25, 0.75])
    with left:
        st.plotly_chart(regime_bar_chart(comparison, selected_contractors), width="stretch")
    with right:
        st.plotly_chart(premium_gauge(verdict.get("score", 0.0)), width="stretch")
        st.markdown(
            """
            <div class="section-band">
                <span style="color:#10b981;"><strong>Green:</strong></span> Lower priced-in risk; more room for upside.
                <br>
                <span style="color:#f5c542;"><strong>Yellow:</strong></span> Mixed setup; much of the theme may already be reflected.
                <br>
                <span style="color:#ef4444;"><strong>Red:</strong></span> High premium already priced in; avoid chasing strength.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div class="section-band">
            <strong>COVID control:</strong> 2020-2021 is {'included in visual charts' if include_covid_visuals else 'omitted from visual charts'} and excluded from the baseline.
            The comparison table always uses 2017-2019 versus the period beginning February 24, 2022.
        </div>
        """,
        unsafe_allow_html=True,
    )

    display_columns = [
        "Ticker",
        "Pre-COVID Annualized Return",
        "Post-2022 Annualized Return",
        "Return Regime Shift",
        "Post-2022 Excess vs Benchmark",
        "Pre-COVID Annualized Volatility",
        "Post-2022 Annualized Volatility",
        "Post-2022 Max Drawdown",
    ]
    available_columns = [column for column in display_columns if column in comparison.columns]
    st.dataframe(
        comparison[comparison["Ticker"].isin(selected_contractors + [effective_benchmark])][available_columns].style.format(
            {column: "{:.1%}" for column in available_columns if column != "Ticker"}
        ),
        width="stretch",
        hide_index=True,
    )

with tabs[1]:
    left, right = st.columns([1.05, 0.95])
    with left:
        st.plotly_chart(priced_in_score_chart(scorecard), width="stretch")
    with right:
        st.plotly_chart(valuation_quality_chart(scorecard), width="stretch")

    score_columns = [
        "Ticker",
        "Priced-In Score",
        "Investment Action",
        "Return Heat",
        "Valuation Richness",
        "Event Sensitivity",
        "Derivative Heat",
        "Backlog Support",
        "Quality Support",
    ]
    st.dataframe(
        scorecard[[column for column in score_columns if column in scorecard.columns]].style.format(
            {
                "Priced-In Score": "{:.0f}",
                "Return Heat": "{:.0f}",
                "Valuation Richness": "{:.0f}",
                "Event Sensitivity": "{:.0f}",
                "Derivative Heat": "{:.0f}",
                "Backlog Support": "{:.0f}",
                "Quality Support": "{:.0f}",
            }
        ),
        width="stretch",
        hide_index=True,
    )

with tabs[2]:
    st.markdown(
        f"""
        <div class="section-band">
            <strong>Math layer:</strong> daily log return approximates the first derivative of price, while the change in daily log return approximates acceleration.
            The displayed derivative lines use a {derivative_smoothing_window}-trading-day smoothing layer. Positive velocity with falling acceleration often signals that the market is still rising, but the impulse is fading.
            COVID is {'included' if include_covid_visuals else 'omitted'} in this derivative view.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        derivative_chart(
            derivative_timeline,
            chart_tickers,
            derivative_metric,
            events=events,
            include_covid=include_covid_visuals,
        ),
        width="stretch",
    )
    derivative_columns = [
        "Ticker",
        "21D Velocity",
        "21D Acceleration",
        "Acceleration Z-Score",
        "Trend Quality",
        "Jerk Volatility",
        "Math Interpretation",
    ]
    st.dataframe(
        derivative_summary[derivative_summary["Ticker"].isin(chart_tickers)][derivative_columns].style.format(
            {
                "21D Velocity": "{:.1%}",
                "21D Acceleration": "{:.1%}",
                "Acceleration Z-Score": "{:.2f}",
                "Trend Quality": "{:.2f}",
                "Jerk Volatility": "{:.1%}",
            }
        ),
        width="stretch",
        hide_index=True,
    )

with tabs[3]:
    help_col, chart_col = st.columns([0.05, 0.95], vertical_alignment="top")
    with help_col:
        st.markdown(
            '<div class="help-badge-wrap"><span class="help-badge" title="NATO\'s 2% guideline is the alliance benchmark that members aim to spend at least 2% of their GDP on defense. It is a political burden-sharing target, not a guarantee of military readiness or procurement quality.">?</span></div>',
            unsafe_allow_html=True,
        )
    with chart_col:
        st.plotly_chart(budget_spending_chart(budgets, DEFAULT_BUDGET_SERIES), width="stretch")
    fundamental_columns = [
        "Ticker",
        "Company",
        "Fiscal Year",
        "Currency",
        "Revenue",
        "Operating Income",
        "Backlog",
        "Defense Backlog",
        "Backlog to Revenue",
        "Book to Bill",
        "Manual Revenue Growth",
        "Source URL",
    ]
    enriched_fundamentals = scorecard[[column for column in fundamental_columns if column in scorecard.columns]].copy()
    st.dataframe(
        enriched_fundamentals,
        column_config={"Source URL": st.column_config.LinkColumn("Source")},
        width="stretch",
        hide_index=True,
    )
    with st.expander("NATO budget source data", expanded=False):
        st.dataframe(
            budgets,
            column_config={"Source URL": st.column_config.LinkColumn("Source")},
            width="stretch",
            hide_index=True,
        )
    st.subheader("Backlog Refresh Watch")
    st.caption("This panel compares the manual backlog fiscal year against the latest Yahoo annual statement year. It cannot auto-extract backlog from filings, but it flags when a manual refresh is probably due.")
    st.dataframe(
        backlog_refresh,
        column_config={"Source URL": st.column_config.LinkColumn("Source")},
        width="stretch",
        hide_index=True,
    )

with tabs[4]:
    st.subheader("Statement-Derived Historical Valuation")
    st.caption("These multiples use quarterly statements where Yahoo provides them, plus older annual period-end rows to extend the history. Quarterly statement values are annualized before valuation multiples are calculated.")
    valuation_options = (
        [ticker for ticker in selected_contractors if ticker in valuation_history.get("Ticker", pd.Series(dtype=str)).unique()]
        if not valuation_history.empty
        else []
    )
    if valuation_options:
        valuation_ticker = st.selectbox("Valuation ticker", options=valuation_options)
        available_valuation_metrics = [
            metric
            for metric in VALUATION_METRIC_EXPLANATIONS
            if metric in valuation_history.columns and valuation_history[metric].notna().any()
        ]
        valuation_metric = st.selectbox("Valuation metric", options=available_valuation_metrics)
        st.markdown(
            f"""
            <div class="section-band">
                <strong>{valuation_metric}:</strong> {VALUATION_METRIC_EXPLANATIONS[valuation_metric]}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(historical_valuation_chart(valuation_history, valuation_ticker, valuation_metric), width="stretch")
    else:
        valuation_ticker = None

    if valuation_summary.empty:
        st.info("Historical valuation rows are unavailable for the selected tickers.")
    else:
        st.dataframe(
            valuation_summary.style.format(
                {
                    "Latest Historical P/E": "{:.2f}",
                    "Median Historical P/E": "{:.2f}",
                    "Current Forward P/E": "{:.2f}",
                    "P/E vs History": "{:.2f}",
                    "Latest Historical EV/EBITDA": "{:.2f}",
                    "Median Historical EV/EBITDA": "{:.2f}",
                    "Current EV/EBITDA": "{:.2f}",
                    "EV/EBITDA vs History": "{:.2f}",
                }
            ),
            width="stretch",
            hide_index=True,
        )

with tabs[5]:
    st.subheader("Custom Defense Contractor Report")
    if not custom_ticker:
        st.info("Enter a ticker in the sidebar to generate a single-stock report.")
    elif custom_ticker not in prices.columns:
        st.warning(f"No price data was returned for `{custom_ticker}`. Check the Yahoo Finance ticker format.")
    else:
        custom_event_data = run_event_study(returns, effective_benchmark, events, window=event_window, tickers=[custom_ticker])
        custom_event_score = event_sensitivity(custom_event_data, event_window)
        custom_report = single_ticker_report(
            custom_ticker,
            comparison,
            profiles,
            derivative_summary,
            valuation_summary,
            custom_event_score,
            fundamentals,
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Ticker Recommendation</div>
                    <div class="metric-value">{custom_report["Recommendation"]}</div>
                    <div class="metric-note">{custom_report["Summary"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Single-Stock Score</div>
                    <div class="metric-value">{points(custom_report["Score"])} / 100</div>
                    <div class="metric-note">Research score based on valuation, returns, events, and derivatives.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Coverage Quality</div>
                    <div class="metric-value">{custom_ticker}</div>
                    <div class="metric-note">Yahoo profile, annual statements, and price history are cache-protected.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        metrics_frame = pd.DataFrame([custom_report["Metrics"]]).T.reset_index()
        metrics_frame.columns = ["Metric", "Value"]
        left, right = st.columns([1.15, 0.85])
        with left:
            custom_valuation_metric = "Historical EV/EBITDA"
            if custom_valuation_metric not in valuation_history.columns or valuation_history[custom_valuation_metric].isna().all():
                custom_valuation_metric = "Historical P/E"
            st.plotly_chart(
                historical_valuation_chart(valuation_history, custom_ticker, custom_valuation_metric),
                width="stretch",
            )
        with right:
            st.dataframe(metrics_frame, width="stretch", hide_index=True)

        st.markdown("**Positive evidence**")
        st.write(custom_report["Positives"] or ["No positive evidence identified from available data."])
        st.markdown("**Risks / offsets**")
        st.write(custom_report["Risks"] or ["No major risk flags identified from available data."])

        custom_memo = single_ticker_report_markdown(custom_report, valuation_history)
        st.download_button(
            "Download Custom Ticker Report",
            data=custom_memo,
            file_name=f"{custom_ticker}_defense_stock_report.md",
            mime="text/markdown",
            width="stretch",
        )

with tabs[6]:
    st.subheader("Event Study")
    st.caption(f"Cumulative abnormal return versus {effective_benchmark}. Window: {event_window} trading days before and after each event.")
    st.plotly_chart(event_study_chart(event_data), width="stretch")

    if not event_data.empty and "Offset" in event_data.columns:
        event_summary_table = (
            event_data[event_data["Offset"] == event_window]
            .groupby(["Event", "Ticker"], as_index=False)["Cumulative Abnormal Return"]
            .mean()
            .pivot(index="Event", columns="Ticker", values="Cumulative Abnormal Return")
        )
    else:
        event_summary_table = pd.DataFrame()

    if not event_summary_table.empty:
        st.dataframe(event_summary_table.style.format("{:.1%}"), width="stretch")
    else:
        st.info("No event-study rows are available for the selected date range and event window.")

    source_columns = ["date", "event", "category", "source", "source_url", "notes"]
    st.dataframe(
        events[source_columns],
        column_config={"source_url": st.column_config.LinkColumn("Source URL")},
        width="stretch",
        hide_index=True,
    )

with tabs[7]:
    left, right = st.columns([1.1, 0.9])
    with left:
        st.plotly_chart(scenario_chart(scenario_frame), width="stretch")
    with right:
        st.markdown(
            f"""
            <div class="section-band">
                <strong>Scenario engine:</strong> selected scenario is <strong>{scenario_name}</strong>.
                The manual premium adjustment is <strong>{manual_adjustment:.1%}</strong> per year.
                The projection compounds each contractor's post-2022 annualized return plus the scenario premium for three years.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(
            scenario_frame.style.format(
                {
                    "Post-2022 Annualized Return": "{:.1%}",
                    "Scenario Annual Return": "{:.1%}",
                    "Premium Adjustment": "{:.1%}",
                    "3Y Indexed Outcome": "{:.0f}",
                    "Priced-In Score": "{:.0f}",
                    "Backlog to Revenue": "{:.2f}",
                }
            ),
            width="stretch",
            hide_index=True,
        )

    export_body = report_download(
        verdict,
        selected_contractors,
        effective_benchmark,
        event_window,
        scenario_name,
        scorecard,
        scenario_frame,
        quality,
    )
    st.download_button(
        "Download Investment Memo",
        data=export_body,
        file_name="defense_risk_premium_memo.md",
        mime="text/markdown",
        width="stretch",
    )

with tabs[8]:
    st.subheader("Data Quality Control Panel")
    st.dataframe(quality, width="stretch", hide_index=True)
    st.markdown(
        f"""
        <div class="section-band">
            Market data uses Yahoo Finance through yfinance. Price, profile, and statement calls use Streamlit session caching plus persistent files under
            <code>data/cache/</code>. Cache TTL is {CACHE_TTL_HOURS} hours. If the API fails or throttles, stale cached data is shown with a warning.
            Statement cache status: <strong>{statement_meta.get("status", "unknown")}</strong>, last updated: {statement_meta.get("cached_at", "n/a")}.
        </div>
        """,
        unsafe_allow_html=True,
    )

with st.expander("Methodology Notes", expanded=False):
    st.markdown(
        f"""
        - The pre-COVID baseline is 2017-2019.
        - The COVID window, 2020-2021, is excluded from baseline calculations.
        - The post-conflict-premium window starts on {POST_UKRAINE_START}.
        - Priced-in score blends return premium, valuation richness, event sensitivity, derivative heat, backlog support, and quality support.
        - Derivative diagnostics use discrete log-price differences; they are analytical diagnostics, not standalone trading signals.
        - Event-study results help measure market sensitivity, but they do not prove causality by themselves.
        """
    )

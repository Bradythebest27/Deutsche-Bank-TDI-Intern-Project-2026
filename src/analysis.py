from __future__ import annotations

import numpy as np
import pandas as pd


PRE_COVID_START = "2017-01-01"
PRE_COVID_END = "2019-12-31"
POST_UKRAINE_START = "2022-02-24"
COVID_START = "2020-01-01"
COVID_END = "2021-12-31"
TRADING_DAYS = 252
SCENARIO_ADJUSTMENTS = {
    "De-escalation": -0.04,
    "Base case": 0.00,
    "Escalation": 0.04,
}
CURRENT_YEAR = 2026


def pivot_prices(market_data: pd.DataFrame, field: str = "Adj Close") -> pd.DataFrame:
    prices = market_data.pivot_table(index="Date", columns="Ticker", values=field, aggfunc="last")
    prices = prices.sort_index()
    prices = prices.dropna(axis=1, how="all")
    return prices.ffill()


def indexed_performance(prices: pd.DataFrame, base: float = 100.0) -> pd.DataFrame:
    valid = prices.dropna(how="all")
    first_values = valid.apply(lambda column: column.dropna().iloc[0] if not column.dropna().empty else np.nan)
    return valid.divide(first_values).multiply(base)


def daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)


def max_drawdown(returns: pd.Series) -> float:
    clean = returns.dropna()
    if clean.empty:
        return np.nan
    cumulative = (1 + clean).cumprod()
    running_max = cumulative.cummax()
    drawdown = cumulative / running_max - 1
    return float(drawdown.min())


def annualized_return(returns: pd.Series) -> float:
    clean = returns.dropna()
    if clean.empty:
        return np.nan
    total_return = (1 + clean).prod() - 1
    years = len(clean) / TRADING_DAYS
    if years <= 0:
        return np.nan
    return float((1 + total_return) ** (1 / years) - 1)


def annualized_volatility(returns: pd.Series) -> float:
    clean = returns.dropna()
    if clean.empty:
        return np.nan
    return float(clean.std() * np.sqrt(TRADING_DAYS))


def _safe_ratio(numerator: pd.Series | float, denominator: pd.Series | float) -> pd.Series | float:
    with np.errstate(divide="ignore", invalid="ignore"):
        result = numerator / denominator
    if isinstance(result, pd.Series):
        return result.replace([np.inf, -np.inf], np.nan)
    return np.nan if np.isinf(result) else result


def summarize_period(returns: pd.DataFrame, start: str, end: str | None = None) -> pd.DataFrame:
    period = returns.loc[pd.to_datetime(start) : pd.to_datetime(end) if end else returns.index.max()]
    rows: list[dict[str, float | str]] = []

    for ticker in period.columns:
        series = period[ticker].dropna()
        rows.append(
            {
                "Ticker": ticker,
                "Annualized Return": annualized_return(series),
                "Annualized Volatility": annualized_volatility(series),
                "Sharpe Proxy": annualized_return(series) / annualized_volatility(series)
                if annualized_volatility(series) and not np.isnan(annualized_volatility(series))
                else np.nan,
                "Max Drawdown": max_drawdown(series),
                "Total Return": float((1 + series).prod() - 1) if not series.empty else np.nan,
                "Trading Days": int(len(series)),
            }
        )

    return pd.DataFrame(rows)


def compare_pre_post_periods(
    returns: pd.DataFrame,
    benchmark: str,
    pre_start: str = PRE_COVID_START,
    pre_end: str = PRE_COVID_END,
    post_start: str = POST_UKRAINE_START,
) -> pd.DataFrame:
    pre = summarize_period(returns, pre_start, pre_end).set_index("Ticker")
    post = summarize_period(returns, post_start, None).set_index("Ticker")

    combined = pre.add_prefix("Pre-COVID ").join(post.add_prefix("Post-2022 "), how="outer")
    combined["Return Regime Shift"] = (
        combined["Post-2022 Annualized Return"] - combined["Pre-COVID Annualized Return"]
    )
    combined["Volatility Regime Shift"] = (
        combined["Post-2022 Annualized Volatility"] - combined["Pre-COVID Annualized Volatility"]
    )

    if benchmark in combined.index:
        benchmark_post = combined.loc[benchmark, "Post-2022 Annualized Return"]
        combined["Post-2022 Excess vs Benchmark"] = combined["Post-2022 Annualized Return"] - benchmark_post
    else:
        combined["Post-2022 Excess vs Benchmark"] = np.nan

    return combined.reset_index()


def run_event_study(
    returns: pd.DataFrame,
    benchmark: str,
    events: pd.DataFrame,
    window: int = 10,
    tickers: list[str] | None = None,
) -> pd.DataFrame:
    if benchmark not in returns.columns:
        raise ValueError(f"Benchmark {benchmark} is missing from returns.")

    selected = tickers or [column for column in returns.columns if column != benchmark]
    trading_dates = returns.index
    rows: list[dict[str, object]] = []

    for _, event in events.iterrows():
        event_date = pd.to_datetime(event["date"])
        insertion_point = trading_dates.searchsorted(event_date)
        if insertion_point >= len(trading_dates):
            continue

        center = int(insertion_point)
        start_position = max(0, center - window)
        end_position = min(len(trading_dates) - 1, center + window)
        window_dates = trading_dates[start_position : end_position + 1]

        for ticker in selected:
            if ticker not in returns.columns:
                continue
            abnormal = returns.loc[window_dates, ticker] - returns.loc[window_dates, benchmark]
            cumulative = abnormal.fillna(0).cumsum()

            for offset, date in zip(range(start_position - center, end_position - center + 1), window_dates):
                rows.append(
                    {
                        "Event": event["event"],
                        "Category": event.get("category", "event"),
                        "Event Date": event_date,
                        "Trading Date": date,
                        "Offset": offset,
                        "Ticker": ticker,
                        "Abnormal Return": abnormal.loc[date],
                        "Cumulative Abnormal Return": cumulative.loc[date],
                    }
                )

    return pd.DataFrame(rows)


def event_sensitivity(event_study: pd.DataFrame, terminal_offset: int) -> pd.DataFrame:
    if event_study.empty or "Offset" not in event_study.columns:
        return pd.DataFrame(columns=["Ticker", "Mean Terminal CAR", "Mean Absolute Terminal CAR", "Positive Event Hit Rate"])

    terminal = event_study[event_study["Offset"] == terminal_offset].copy()
    if terminal.empty:
        return pd.DataFrame(columns=["Ticker", "Mean Terminal CAR", "Mean Absolute Terminal CAR", "Positive Event Hit Rate"])

    grouped = terminal.groupby("Ticker")["Cumulative Abnormal Return"]
    return pd.DataFrame(
        {
            "Ticker": grouped.mean().index,
            "Mean Terminal CAR": grouped.mean().values,
            "Mean Absolute Terminal CAR": grouped.apply(lambda values: values.abs().mean()).values,
            "Positive Event Hit Rate": grouped.apply(lambda values: (values > 0).mean()).values,
        }
    )


def derivative_diagnostics(
    prices: pd.DataFrame,
    lookback: int = 21,
    smoothing_window: int = 63,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Estimate first and second discrete derivatives of log prices.

    Daily log returns approximate d(log price)/dt. The first difference of those
    returns approximates acceleration, or whether momentum is strengthening or
    fading. The dashboard uses these as diagnostics, not as a trading signal.
    """
    log_prices = np.log(prices.replace(0, np.nan))
    velocity = log_prices.diff()
    acceleration = velocity.diff()
    jerk = acceleration.diff()

    rows: list[dict[str, object]] = []
    timeline_frames: list[pd.DataFrame] = []

    for ticker in prices.columns:
        ticker_velocity = velocity[ticker].dropna()
        ticker_acceleration = acceleration[ticker].dropna()
        ticker_jerk = jerk[ticker].dropna()

        rolling_velocity = velocity[ticker].rolling(lookback).mean() * TRADING_DAYS
        rolling_acceleration = acceleration[ticker].rolling(lookback).mean() * TRADING_DAYS
        rolling_volatility = velocity[ticker].rolling(lookback).std() * np.sqrt(TRADING_DAYS)
        smoothed_velocity = rolling_velocity.rolling(smoothing_window, min_periods=max(5, smoothing_window // 4)).mean()
        smoothed_acceleration = rolling_acceleration.rolling(
            smoothing_window,
            min_periods=max(5, smoothing_window // 4),
        ).mean()

        latest_velocity = smoothed_velocity.dropna().iloc[-1] if not smoothed_velocity.dropna().empty else np.nan
        latest_acceleration = (
            smoothed_acceleration.dropna().iloc[-1] if not smoothed_acceleration.dropna().empty else np.nan
        )
        latest_volatility = rolling_volatility.dropna().iloc[-1] if not rolling_volatility.dropna().empty else np.nan

        acceleration_std = ticker_acceleration.std()
        latest_raw_acceleration = ticker_acceleration.iloc[-1] if not ticker_acceleration.empty else np.nan
        acceleration_z = latest_raw_acceleration / acceleration_std if acceleration_std and pd.notna(acceleration_std) else np.nan
        trend_quality = latest_velocity / latest_volatility if latest_volatility and pd.notna(latest_volatility) else np.nan

        rows.append(
            {
                "Ticker": ticker,
                "21D Velocity": latest_velocity,
                "21D Acceleration": latest_acceleration,
                "Acceleration Z-Score": acceleration_z,
                "Trend Quality": trend_quality,
                "Jerk Volatility": ticker_jerk.std() * np.sqrt(TRADING_DAYS) if not ticker_jerk.empty else np.nan,
                "Math Interpretation": _derivative_label(latest_velocity, latest_acceleration, acceleration_z),
            }
        )

        timeline = pd.DataFrame(
            {
                "Date": prices.index,
                "Ticker": ticker,
                "Rolling Velocity": rolling_velocity,
                "Rolling Acceleration": rolling_acceleration,
                "Smoothed Velocity": smoothed_velocity,
                "Smoothed Acceleration": smoothed_acceleration,
                "Rolling Volatility": rolling_volatility,
            }
        )
        timeline_frames.append(timeline)

    timeline_frame = pd.concat(timeline_frames, ignore_index=True) if timeline_frames else pd.DataFrame()
    return pd.DataFrame(rows), timeline_frame


def _derivative_label(velocity: float, acceleration: float, acceleration_z: float) -> str:
    if pd.isna(velocity) or pd.isna(acceleration):
        return "Insufficient data"
    if velocity > 0 and acceleration > 0 and (pd.isna(acceleration_z) or acceleration_z < 2):
        return "Momentum improving"
    if velocity > 0 and acceleration < 0:
        return "Momentum fading"
    if velocity < 0 and acceleration > 0:
        return "Downtrend stabilizing"
    if velocity < 0 and acceleration < 0:
        return "Selling pressure increasing"
    return "Neutral"


def enrich_fundamentals(profiles: pd.DataFrame, manual_fundamentals: pd.DataFrame) -> pd.DataFrame:
    profile_columns = [
        "Ticker",
        "Market Cap",
        "Trailing P/E",
        "Forward P/E",
        "EV/Revenue",
        "EV/EBITDA",
        "Profit Margin",
        "Operating Margin",
        "Revenue Growth",
        "Beta",
    ]
    profile_subset = profiles[[column for column in profile_columns if column in profiles.columns]].copy()
    enriched = manual_fundamentals.merge(profile_subset, on="Ticker", how="left", suffixes=("", " Yahoo"))

    enriched["Backlog to Revenue"] = _safe_ratio(enriched["Backlog"], enriched["Revenue"])
    enriched["Manual Operating Margin"] = _safe_ratio(enriched["Operating Income"], enriched["Revenue"])
    enriched["Effective Operating Margin"] = enriched["Operating Margin"].combine_first(enriched["Manual Operating Margin"])
    enriched["Effective Revenue Growth"] = enriched["Revenue Growth"].combine_first(enriched["Manual Revenue Growth"])
    return enriched


def _percentile(series: pd.Series, higher_is_better: bool = True, neutral: float = 50.0) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    ranks = numeric.rank(pct=True) * 100
    if not higher_is_better:
        ranks = 100 - ranks
    return ranks.fillna(neutral)


def build_priced_in_score(
    comparison: pd.DataFrame,
    profiles: pd.DataFrame,
    fundamentals: pd.DataFrame,
    derivative_summary: pd.DataFrame,
    event_summary: pd.DataFrame,
    tickers: list[str],
    valuation_snapshot_frame: pd.DataFrame | None = None,
) -> pd.DataFrame:
    base = comparison[comparison["Ticker"].isin(tickers)].copy()
    enriched = enrich_fundamentals(profiles, fundamentals)
    base = base.merge(enriched, on="Ticker", how="left")
    base = base.merge(derivative_summary, on="Ticker", how="left")
    base = base.merge(event_summary, on="Ticker", how="left")
    if valuation_snapshot_frame is not None and not valuation_snapshot_frame.empty:
        valuation_columns = [
            "Ticker",
            "P/E vs History",
            "EV/EBITDA vs History",
            "Statement Years",
            "Median Historical P/E",
            "Median Historical EV/EBITDA",
        ]
        base = base.merge(
            valuation_snapshot_frame[[column for column in valuation_columns if column in valuation_snapshot_frame.columns]],
            on="Ticker",
            how="left",
        )

    base["Return Heat"] = _percentile(base["Post-2022 Excess vs Benchmark"], higher_is_better=True)
    base["Regime Shift Heat"] = _percentile(base["Return Regime Shift"], higher_is_better=True)
    if {"P/E vs History", "EV/EBITDA vs History"}.issubset(base.columns):
        historical_richness = (
            _percentile(base["P/E vs History"], higher_is_better=True)
            .add(_percentile(base["EV/EBITDA vs History"], higher_is_better=True), fill_value=50)
            .div(2)
        )
        current_richness = (
            _percentile(base["Forward P/E"], higher_is_better=True)
            .add(_percentile(base["EV/EBITDA"], higher_is_better=True), fill_value=50)
            .div(2)
        )
        base["Valuation Richness"] = historical_richness.combine_first(current_richness)
    else:
        base["Valuation Richness"] = (
            _percentile(base["Forward P/E"], higher_is_better=True)
            .add(_percentile(base["EV/EBITDA"], higher_is_better=True), fill_value=50)
            .div(2)
        )
    base["Event Sensitivity"] = _percentile(base["Mean Absolute Terminal CAR"], higher_is_better=True)
    base["Derivative Heat"] = _percentile(base["21D Velocity"], higher_is_better=True).mul(0.55).add(
        _percentile(base["Acceleration Z-Score"].abs(), higher_is_better=True).mul(0.45),
        fill_value=22.5,
    )
    base["Backlog Support"] = _percentile(base["Backlog to Revenue"], higher_is_better=True)
    base["Quality Support"] = (
        _percentile(base["Effective Operating Margin"], higher_is_better=True)
        .add(_percentile(base["Effective Revenue Growth"], higher_is_better=True), fill_value=50)
        .div(2)
    )

    base["Priced-In Score"] = (
        0.22 * base["Return Heat"]
        + 0.14 * base["Regime Shift Heat"]
        + 0.20 * base["Valuation Richness"]
        + 0.14 * base["Event Sensitivity"]
        + 0.12 * base["Derivative Heat"]
        - 0.10 * base["Backlog Support"]
        - 0.08 * base["Quality Support"]
        + 10
    ).clip(0, 100)

    base["Investment Action"] = pd.cut(
        base["Priced-In Score"],
        bins=[-0.1, 42, 68, 100.1],
        labels=["Selective Buy Watchlist", "Hold / Fairly Priced", "Avoid Chasing"],
    ).astype(str)

    return base.sort_values("Priced-In Score", ascending=False).reset_index(drop=True)


def aggregate_verdict(scorecard: pd.DataFrame) -> dict[str, object]:
    if scorecard.empty:
        return {
            "verdict": "Insufficient Data",
            "score": np.nan,
            "summary": "Not enough data is available to form a defensible investment view.",
        }

    median_score = scorecard["Priced-In Score"].median(skipna=True)
    if median_score >= 68:
        verdict = "Avoid Chasing / Wait for Margin of Safety"
        summary = "The sector screens hot: market performance, valuation, and event sensitivity suggest much of the conflict premium is already capitalized."
    elif median_score >= 42:
        verdict = "Hold / Selective Entry Only"
        summary = "The budget cycle is real, but the median contractor looks close to fairly priced after post-2022 outperformance."
    else:
        verdict = "Constructive / Selective Buy"
        summary = "The selected universe shows enough backlog and quality support to offset the priced-in premium signal."

    return {"verdict": verdict, "score": float(median_score), "summary": summary}


def scenario_projection(
    comparison: pd.DataFrame,
    scorecard: pd.DataFrame,
    tickers: list[str],
    scenario_name: str,
    manual_adjustment: float,
    years: int = 3,
) -> pd.DataFrame:
    scenario_adjustment = SCENARIO_ADJUSTMENTS.get(scenario_name, 0.0) + manual_adjustment
    base = comparison[comparison["Ticker"].isin(tickers)][["Ticker", "Post-2022 Annualized Return"]].copy()
    base = base.merge(scorecard[["Ticker", "Priced-In Score", "Backlog to Revenue"]], on="Ticker", how="left")
    base["Scenario Annual Return"] = base["Post-2022 Annualized Return"].fillna(0) + scenario_adjustment
    base["3Y Indexed Outcome"] = 100 * (1 + base["Scenario Annual Return"]).clip(lower=-0.95) ** years
    base["Premium Adjustment"] = scenario_adjustment
    base["Scenario"] = scenario_name
    return base.sort_values("3Y Indexed Outcome", ascending=False).reset_index(drop=True)


def data_quality_report(
    market_data: pd.DataFrame,
    prices: pd.DataFrame,
    profiles: pd.DataFrame,
    fundamentals: pd.DataFrame,
    selected_tickers: list[str],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    equity_profile_fields = ["Trailing P/E", "Forward P/E", "EV/EBITDA", "Operating Margin", "Revenue Growth", "Beta"]
    fund_profile_fields = ["Trailing P/E", "Total Assets", "NAV Price", "Fund Yield", "Beta 3Y", "Fund Family", "Category"]

    for ticker in selected_tickers:
        raw_rows = market_data[market_data["Ticker"] == ticker]
        price_series = prices[ticker] if ticker in prices.columns else pd.Series(dtype=float)
        profile_row = profiles[profiles["Ticker"] == ticker] if "Ticker" in profiles.columns else pd.DataFrame()
        manual_row = fundamentals[fundamentals["Ticker"] == ticker] if "Ticker" in fundamentals.columns else pd.DataFrame()

        available_profile_fields = 0
        expected_profile_fields = equity_profile_fields
        profile_type = "Missing"
        profile_note = "No profile row was loaded."
        if not profile_row.empty:
            quote_type = str(profile_row.iloc[0].get("Quote Type", "")).upper()
            profile_type = quote_type or "Unknown"
            if quote_type in {"ETF", "MUTUALFUND", "INDEX"}:
                expected_profile_fields = fund_profile_fields
                profile_note = "Fund/ETF profile scored with ETF-specific fields."
            else:
                profile_note = "Equity profile scored with company valuation/fundamental fields."
            available_profile_fields = sum(
                field in profile_row.columns and pd.notna(profile_row.iloc[0].get(field))
                for field in expected_profile_fields
            )
        manual_status = "Yes" if not manual_row.empty else "No"
        has_manual_for_grade = not manual_row.empty
        if profile_type in {"ETF", "MUTUALFUND", "INDEX"}:
            manual_status = "Not applicable"
            has_manual_for_grade = True

        rows.append(
            {
                "Ticker": ticker,
                "Price Rows": int(len(raw_rows)),
                "First Price Date": price_series.dropna().index.min() if not price_series.dropna().empty else pd.NaT,
                "Last Price Date": price_series.dropna().index.max() if not price_series.dropna().empty else pd.NaT,
                "Price Missing %": float(price_series.isna().mean()) if len(price_series) else np.nan,
                "Profile Type": profile_type,
                "Profile Fields Available": available_profile_fields,
                "Profile Fields Expected": len(expected_profile_fields),
                "Profile Data Note": profile_note,
                "Manual Fundamental Row": manual_status,
                "Data Grade": _data_grade(len(raw_rows), available_profile_fields, has_manual_for_grade),
            }
        )
    return pd.DataFrame(rows)


def historical_valuation_series(statements: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """Estimate valuation multiples from annual and annualized quarterly statements."""
    if statements.empty or prices.empty:
        return pd.DataFrame()

    rows: list[dict[str, object]] = []
    for _, row in statements.iterrows():
        ticker = row.get("Ticker")
        fiscal_date = pd.to_datetime(row.get("Date"))
        if ticker not in prices.columns or pd.isna(fiscal_date):
            continue

        available_prices = prices.loc[:fiscal_date, ticker].dropna()
        if available_prices.empty:
            available_prices = prices[ticker].dropna()
        if available_prices.empty:
            continue

        raw_fiscal_price = available_prices.iloc[-1]
        price_unit_adjustment = 0.01 if str(ticker).endswith(".L") else 1.0
        fiscal_price = raw_fiscal_price * price_unit_adjustment
        shares = row.get("Diluted Average Shares")
        if pd.isna(shares):
            shares = row.get("Ordinary Shares")
        market_cap = fiscal_price * shares if pd.notna(fiscal_price) and pd.notna(shares) else np.nan
        enterprise_value = market_cap + row.get("Total Debt", np.nan) - row.get("Cash", np.nan)
        annualization_factor = row.get("Annualization Factor", 1)
        if pd.isna(annualization_factor):
            annualization_factor = 1
        annualized_revenue = row.get("Revenue", np.nan) * annualization_factor
        annualized_ebitda = row.get("EBITDA", np.nan) * annualization_factor
        annualized_net_income = row.get("Net Income", np.nan) * annualization_factor
        period_type = row.get("Period Type", "Annual")
        fiscal_period = row.get("Fiscal Period")
        if pd.isna(fiscal_period):
            fiscal_period = f"{fiscal_date.year}Q{fiscal_date.quarter}"

        rows.append(
            {
                "Ticker": ticker,
                "Date": fiscal_date,
                "Period Type": period_type,
                "Fiscal Year": row.get("Fiscal Year"),
                "Fiscal Quarter": row.get("Fiscal Quarter", np.nan),
                "Fiscal Period": fiscal_period,
                "Fiscal Price": fiscal_price,
                "Raw Fiscal Price": raw_fiscal_price,
                "Price Unit Adjustment": price_unit_adjustment,
                "Revenue": row.get("Revenue"),
                "Annualized Revenue": annualized_revenue,
                "EBITDA": row.get("EBITDA"),
                "Annualized EBITDA": annualized_ebitda,
                "Net Income": row.get("Net Income"),
                "Annualized Net Income": annualized_net_income,
                "Diluted Average Shares": shares,
                "Market Cap Proxy": market_cap,
                "Enterprise Value Proxy": enterprise_value,
                "Historical P/E": _safe_ratio(market_cap, annualized_net_income),
                "Historical P/S": _safe_ratio(market_cap, annualized_revenue),
                "Historical EV/EBITDA": _safe_ratio(enterprise_value, annualized_ebitda),
            }
        )

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame

    multiple_columns = ["Historical P/E", "Historical P/S", "Historical EV/EBITDA"]
    for column in multiple_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame.loc[frame[column] <= 0, column] = np.nan
    return frame.sort_values(["Ticker", "Date"]).reset_index(drop=True)


def valuation_snapshot(valuation_history: pd.DataFrame, profiles: pd.DataFrame) -> pd.DataFrame:
    if valuation_history.empty:
        return pd.DataFrame()

    rows: list[dict[str, object]] = []
    for ticker, group in valuation_history.groupby("Ticker"):
        sorted_group = group.sort_values("Date")
        latest = sorted_group.iloc[-1]
        profile = profiles[profiles["Ticker"] == ticker].iloc[0] if "Ticker" in profiles.columns and not profiles[profiles["Ticker"] == ticker].empty else pd.Series(dtype=object)
        forward_pe = profile.get("Forward P/E", np.nan)
        ev_ebitda = profile.get("EV/EBITDA", np.nan)
        historical_pe_median = sorted_group["Historical P/E"].median(skipna=True)
        historical_ev_ebitda_median = sorted_group["Historical EV/EBITDA"].median(skipna=True)

        rows.append(
            {
                "Ticker": ticker,
                "Latest Fiscal Year": latest.get("Fiscal Year"),
                "Latest Historical P/E": latest.get("Historical P/E"),
                "Median Historical P/E": historical_pe_median,
                "Current Forward P/E": forward_pe,
                "P/E vs History": _safe_ratio(forward_pe, historical_pe_median),
                "Latest Historical EV/EBITDA": latest.get("Historical EV/EBITDA"),
                "Median Historical EV/EBITDA": historical_ev_ebitda_median,
                "Current EV/EBITDA": ev_ebitda,
                "EV/EBITDA vs History": _safe_ratio(ev_ebitda, historical_ev_ebitda_median),
                "Statement Years": int(sorted_group["Fiscal Year"].nunique()),
            }
        )

    return pd.DataFrame(rows)


def backlog_refresh_report(
    fundamentals: pd.DataFrame,
    statements: pd.DataFrame,
    current_year: int = CURRENT_YEAR,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in fundamentals.iterrows():
        ticker = row["Ticker"]
        manual_year = row.get("Fiscal Year")
        statement_rows = statements[statements["Ticker"] == ticker] if "Ticker" in statements.columns else pd.DataFrame()
        latest_statement_year = statement_rows["Fiscal Year"].max() if not statement_rows.empty else np.nan

        if pd.notna(latest_statement_year) and pd.notna(manual_year) and latest_statement_year > manual_year:
            status = "Refresh recommended"
            reason = f"Yahoo statements include FY{int(latest_statement_year)}, manual backlog file is FY{int(manual_year)}."
        elif pd.notna(manual_year) and manual_year < current_year - 1:
            status = "Review soon"
            reason = f"Manual backlog file is FY{int(manual_year)}; check whether a newer annual report is available."
        else:
            status = "Current enough"
            reason = "Manual backlog file appears aligned with latest available statement year."

        rows.append(
            {
                "Ticker": ticker,
                "Company": row.get("Company"),
                "Manual Backlog Fiscal Year": manual_year,
                "Latest Yahoo Statement Year": latest_statement_year,
                "Refresh Status": status,
                "Reason": reason,
                "Source URL": row.get("Source URL"),
            }
        )
    return pd.DataFrame(rows)


def single_ticker_report(
    ticker: str,
    comparison: pd.DataFrame,
    profiles: pd.DataFrame,
    derivative_summary: pd.DataFrame,
    valuation_snapshot_frame: pd.DataFrame,
    event_summary: pd.DataFrame,
    fundamentals: pd.DataFrame,
) -> dict[str, object]:
    ticker = ticker.upper().strip()
    comparison_row = _first_matching_row(comparison, ticker)
    profile_row = _first_matching_row(profiles, ticker)
    derivative_row = _first_matching_row(derivative_summary, ticker)
    valuation_row = _first_matching_row(valuation_snapshot_frame, ticker)
    event_row = _first_matching_row(event_summary, ticker)
    fundamental_row = _first_matching_row(fundamentals, ticker)

    score_components: list[float] = []
    positives: list[str] = []
    risks: list[str] = []

    excess_return = comparison_row.get("Post-2022 Excess vs Benchmark", np.nan)
    if pd.notna(excess_return):
        component = np.clip(50 + excess_return * 180, 0, 100)
        score_components.append(component)
        (positives if excess_return > 0 else risks).append(
            f"Post-2022 excess return versus benchmark is {excess_return:.1%}."
        )

    valuation_ratio = valuation_row.get("EV/EBITDA vs History", np.nan)
    if pd.isna(valuation_ratio):
        valuation_ratio = valuation_row.get("P/E vs History", np.nan)
    if pd.notna(valuation_ratio):
        component = np.clip(100 - (valuation_ratio - 0.8) * 90, 0, 100)
        score_components.append(component)
        (positives if valuation_ratio <= 1.0 else risks).append(
            f"Current valuation is {valuation_ratio:.2f}x its own statement-derived historical reference."
        )

    velocity = derivative_row.get("21D Velocity", np.nan)
    acceleration = derivative_row.get("21D Acceleration", np.nan)
    if pd.notna(velocity) and pd.notna(acceleration):
        component = 50 + np.clip(velocity * 60, -20, 20) + np.clip(acceleration * 35, -15, 15)
        score_components.append(float(np.clip(component, 0, 100)))
        (positives if velocity > 0 and acceleration > 0 else risks).append(
            f"Derivative signal: {derivative_row.get('Math Interpretation', 'n/a')}."
        )

    event_car = event_row.get("Mean Terminal CAR", np.nan)
    if pd.notna(event_car):
        component = np.clip(50 + event_car * 200, 0, 100)
        score_components.append(component)
        (positives if event_car > 0 else risks).append(
            f"Average event-window abnormal return is {event_car:.1%}."
        )

    backlog_to_revenue = np.nan
    if not fundamental_row.empty:
        revenue = fundamental_row.get("Revenue", np.nan)
        backlog = fundamental_row.get("Backlog", np.nan)
        backlog_to_revenue = backlog / revenue if pd.notna(revenue) and revenue else np.nan
    if pd.notna(backlog_to_revenue):
        component = np.clip(35 + backlog_to_revenue * 14, 0, 100)
        score_components.append(component)
        positives.append(f"Backlog / revenue is {backlog_to_revenue:.2f}x.")

    if score_components:
        final_score = float(np.mean(score_components))
    else:
        final_score = np.nan

    if pd.isna(final_score):
        recommendation = "Insufficient Data"
        summary = "The app could not collect enough price, profile, or statement data to make a defensible call."
    elif final_score >= 62:
        recommendation = "Buy"
        summary = "The stock screens favorably on the combined return, valuation, event, derivative, and backlog evidence."
    elif final_score >= 42:
        recommendation = "Hold"
        summary = "The evidence is mixed or close to fair value; maintain exposure but be selective with new capital."
    else:
        recommendation = "Sell / Avoid"
        summary = "The evidence does not provide enough support for new exposure at current dashboard readings."

    return {
        "Ticker": ticker,
        "Name": profile_row.get("Name", ticker),
        "Recommendation": recommendation,
        "Score": final_score,
        "Summary": summary,
        "Positives": positives,
        "Risks": risks,
        "Metrics": {
            "Post-2022 Annualized Return": comparison_row.get("Post-2022 Annualized Return", np.nan),
            "Post-2022 Excess vs Benchmark": excess_return,
            "Forward P/E": profile_row.get("Forward P/E", np.nan),
            "EV/EBITDA": profile_row.get("EV/EBITDA", np.nan),
            "EV/EBITDA vs History": valuation_row.get("EV/EBITDA vs History", np.nan),
            "P/E vs History": valuation_row.get("P/E vs History", np.nan),
            "21D Velocity": velocity,
            "21D Acceleration": acceleration,
            "Mean Terminal CAR": event_car,
            "Backlog to Revenue": backlog_to_revenue,
        },
    }


def single_ticker_report_markdown(report: dict[str, object], valuation_history: pd.DataFrame) -> str:
    metrics = report["Metrics"]
    positives = "\n".join(f"- {item}" for item in report["Positives"]) or "- None identified from available data."
    risks = "\n".join(f"- {item}" for item in report["Risks"]) or "- None identified from available data."
    history = valuation_history[valuation_history["Ticker"] == report["Ticker"]]
    history_csv = history.to_csv(index=False) if not history.empty else "No historical valuation rows available."

    return f"""# Custom Defense Ticker Report: {report['Ticker']}

## Recommendation: {report['Recommendation']}

Score: {report['Score']:.1f} / 100

{report['Summary']}

## Key Metrics

- Post-2022 annualized return: {_format_metric(metrics.get('Post-2022 Annualized Return'), percent=True)}
- Post-2022 excess vs benchmark: {_format_metric(metrics.get('Post-2022 Excess vs Benchmark'), percent=True)}
- Forward P/E: {_format_metric(metrics.get('Forward P/E'))}
- EV/EBITDA: {_format_metric(metrics.get('EV/EBITDA'))}
- EV/EBITDA vs own history: {_format_metric(metrics.get('EV/EBITDA vs History'))}
- P/E vs own history: {_format_metric(metrics.get('P/E vs History'))}
- 21D velocity: {_format_metric(metrics.get('21D Velocity'), percent=True)}
- 21D acceleration: {_format_metric(metrics.get('21D Acceleration'), percent=True)}
- Mean event CAR: {_format_metric(metrics.get('Mean Terminal CAR'), percent=True)}
- Backlog / revenue: {_format_metric(metrics.get('Backlog to Revenue'))}

## Positives

{positives}

## Risks

{risks}

## Historical Valuation Rows

```csv
{history_csv}
```

This recommendation is a research output for the project, not personal financial advice.
"""


def _first_matching_row(frame: pd.DataFrame, ticker: str) -> pd.Series:
    if frame.empty or "Ticker" not in frame.columns:
        return pd.Series(dtype=object)
    matches = frame[frame["Ticker"] == ticker]
    if matches.empty:
        return pd.Series(dtype=object)
    return matches.iloc[0]


def _format_metric(value: object, percent: bool = False) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{value:.1%}" if percent else f"{value:.2f}"


def _data_grade(price_rows: int, profile_fields: int, has_manual: bool) -> str:
    score = 0
    score += 2 if price_rows > 1000 else 1 if price_rows > 250 else 0
    score += 2 if profile_fields >= 4 else 1 if profile_fields >= 2 else 0
    score += 1 if has_manual else 0
    if score >= 5:
        return "Institutional-ready"
    if score >= 3:
        return "Usable"
    return "Needs review"


def score_conflict_premium(comparison: pd.DataFrame, contractor_tickers: list[str]) -> dict[str, object]:
    subset = comparison[comparison["Ticker"].isin(contractor_tickers)].copy()
    if subset.empty:
        return {
            "verdict": "Insufficient Data",
            "score": np.nan,
            "summary": "Not enough contractor data is available to score the conflict premium.",
        }

    median_excess = subset["Post-2022 Excess vs Benchmark"].median(skipna=True)
    median_shift = subset["Return Regime Shift"].median(skipna=True)
    median_vol_shift = subset["Volatility Regime Shift"].median(skipna=True)

    score = 0.0
    if pd.notna(median_excess):
        score += median_excess * 100
    if pd.notna(median_shift):
        score += median_shift * 50
    if pd.notna(median_vol_shift):
        score -= max(median_vol_shift, 0) * 20

    if score >= 6:
        verdict = "Constructive Hold / Selective Buy"
        summary = "Post-2022 outperformance appears meaningful enough to support selective exposure, while valuation discipline still matters."
    elif score >= 1.5:
        verdict = "Hold"
        summary = "The defense cycle looks real, but market pricing has likely absorbed a meaningful part of the upside."
    else:
        verdict = "Avoid New Money / Wait for Margin of Safety"
        summary = "The evidence does not show enough benchmark-relative reward to justify chasing the conflict premium."

    return {
        "verdict": verdict,
        "score": float(score),
        "median_excess": float(median_excess) if pd.notna(median_excess) else np.nan,
        "median_shift": float(median_shift) if pd.notna(median_shift) else np.nan,
        "median_vol_shift": float(median_vol_shift) if pd.notna(median_vol_shift) else np.nan,
        "summary": summary,
    }

import pandas as pd

from src.analysis import (
    backlog_refresh_report,
    build_priced_in_score,
    compare_pre_post_periods,
    daily_returns,
    derivative_diagnostics,
    event_sensitivity,
    historical_valuation_series,
    indexed_performance,
    pivot_prices,
    run_event_study,
    scenario_projection,
    single_ticker_report,
    valuation_snapshot,
    data_quality_report,
)


def sample_market_data():
    dates = pd.bdate_range("2017-01-02", "2022-03-31")
    rows = []
    for ticker, drift in {"LMT": 0.0007, "ITA": 0.0004}.items():
        price = 100.0
        for date in dates:
            price *= 1 + drift
            rows.append(
                {
                    "Date": date,
                    "Ticker": ticker,
                    "Open": price,
                    "High": price,
                    "Low": price,
                    "Close": price,
                    "Adj Close": price,
                    "Volume": 1000,
                }
            )
    return pd.DataFrame(rows)


def test_indexed_performance_starts_at_100():
    prices = pivot_prices(sample_market_data())
    indexed = indexed_performance(prices)
    assert round(indexed["LMT"].dropna().iloc[0], 6) == 100


def test_compare_pre_post_periods_excludes_covid_baseline():
    prices = pivot_prices(sample_market_data())
    returns = daily_returns(prices)
    comparison = compare_pre_post_periods(returns, "ITA")
    assert "Pre-COVID Annualized Return" in comparison.columns
    assert "Post-2022 Annualized Return" in comparison.columns


def test_event_study_returns_offsets():
    prices = pivot_prices(sample_market_data())
    returns = daily_returns(prices)
    events = pd.DataFrame({"date": ["2022-02-24"], "event": ["Ukraine invasion"], "category": ["Ukraine"]})
    result = run_event_study(returns, "ITA", events, window=3, tickers=["LMT"])
    assert set(result["Offset"]) == {-3, -2, -1, 0, 1, 2, 3}


def test_derivative_diagnostics_returns_summary_and_timeline():
    prices = pivot_prices(sample_market_data())
    summary, timeline = derivative_diagnostics(prices, lookback=5)
    assert {"Ticker", "21D Velocity", "21D Acceleration", "Math Interpretation"}.issubset(summary.columns)
    assert {"Date", "Ticker", "Rolling Velocity", "Rolling Acceleration"}.issubset(timeline.columns)


def test_priced_in_score_and_scenario_projection():
    prices = pivot_prices(sample_market_data())
    returns = daily_returns(prices)
    comparison = compare_pre_post_periods(returns, "ITA")
    events = pd.DataFrame({"date": ["2022-02-24"], "event": ["Ukraine invasion"], "category": ["Ukraine"]})
    event_data = run_event_study(returns, "ITA", events, window=3, tickers=["LMT"])
    event_score = event_sensitivity(event_data, 3)
    derivative_summary, _ = derivative_diagnostics(prices, lookback=5)
    profiles = pd.DataFrame(
        {
            "Ticker": ["LMT"],
            "Forward P/E": [18.0],
            "EV/EBITDA": [12.0],
            "Operating Margin": [0.11],
            "Revenue Growth": [0.05],
            "Beta": [0.8],
        }
    )
    fundamentals = pd.DataFrame(
        {
            "Ticker": ["LMT"],
            "Company": ["Lockheed Martin"],
            "Fiscal Year": [2024],
            "Currency": ["USD billions"],
            "Revenue": [71.0],
            "Operating Income": [7.5],
            "Backlog": [176.0],
            "Defense Backlog": [None],
            "Book to Bill": [1.1],
            "Manual Revenue Growth": [0.05],
            "Source URL": ["https://example.com"],
        }
    )
    scorecard = build_priced_in_score(comparison, profiles, fundamentals, derivative_summary, event_score, ["LMT"])
    scenario = scenario_projection(comparison, scorecard, ["LMT"], "Base case", 0.0)
    assert "Priced-In Score" in scorecard.columns
    assert scorecard["Priced-In Score"].between(0, 100).all()
    assert "3Y Indexed Outcome" in scenario.columns


def test_historical_valuation_and_single_ticker_report():
    prices = pivot_prices(sample_market_data())
    returns = daily_returns(prices)
    comparison = compare_pre_post_periods(returns, "ITA")
    derivative_summary, _ = derivative_diagnostics(prices, lookback=5)
    events = pd.DataFrame({"date": ["2022-02-24"], "event": ["Ukraine invasion"], "category": ["Ukraine"]})
    event_score = event_sensitivity(run_event_study(returns, "ITA", events, window=3, tickers=["LMT"]), 3)
    statements = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2021-12-31", "2022-12-31"]),
            "Ticker": ["LMT", "LMT"],
            "Fiscal Year": [2021, 2022],
            "Revenue": [65_000_000_000, 67_000_000_000],
            "EBITDA": [8_000_000_000, 8_500_000_000],
            "Net Income": [5_000_000_000, 5_300_000_000],
            "Diluted Average Shares": [250_000_000, 245_000_000],
            "Total Debt": [12_000_000_000, 13_000_000_000],
            "Cash": [2_000_000_000, 2_200_000_000],
            "Ordinary Shares": [250_000_000, 245_000_000],
        }
    )
    profiles = pd.DataFrame({"Ticker": ["LMT"], "Name": ["Lockheed Martin"], "Forward P/E": [18.0], "EV/EBITDA": [12.0]})
    fundamentals = pd.DataFrame(
        {
            "Ticker": ["LMT"],
            "Company": ["Lockheed Martin"],
            "Fiscal Year": [2021],
            "Revenue": [65.0],
            "Operating Income": [7.0],
            "Backlog": [140.0],
            "Source URL": ["https://example.com"],
        }
    )
    history = historical_valuation_series(statements, prices)
    snapshot = valuation_snapshot(history, profiles)
    report = single_ticker_report("LMT", comparison, profiles, derivative_summary, snapshot, event_score, fundamentals)
    refresh = backlog_refresh_report(fundamentals, statements, current_year=2023)

    assert {"Historical P/E", "Historical EV/EBITDA"}.issubset(history.columns)
    assert "P/E vs History" in snapshot.columns
    assert report["Recommendation"] in {"Buy", "Hold", "Sell / Avoid", "Insufficient Data"}
    assert refresh.loc[0, "Refresh Status"] == "Refresh recommended"


def test_data_quality_scores_etf_profile_fields():
    market_data = sample_market_data()
    prices = pivot_prices(market_data)
    profiles = pd.DataFrame(
        {
            "Ticker": ["ITA"],
            "Quote Type": ["ETF"],
            "Trailing P/E": [34.8],
            "Total Assets": [10_000_000_000],
            "NAV Price": [229.4],
            "Fund Yield": [0.004],
            "Beta 3Y": [1.01],
            "Fund Family": ["iShares"],
            "Category": ["Industrials"],
        }
    )
    fundamentals = pd.DataFrame({"Ticker": ["LMT"], "Fiscal Year": [2024]})
    quality = data_quality_report(market_data, prices, profiles, fundamentals, ["ITA"])
    assert quality.loc[0, "Profile Type"] == "ETF"
    assert quality.loc[0, "Profile Fields Available"] == 7
    assert quality.loc[0, "Manual Fundamental Row"] == "Not applicable"

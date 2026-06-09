# Defense Spending & the Geopolitical Risk Premium

Professional Streamlit dashboard and investment thesis for the Deutsche Bank TDI Intern Project 2026.

## Executive Summary

This project tests whether public defense contractors remain durable long-term holdings or whether the market has already capitalized the geopolitical "conflict premium" into share prices.

The dashboard combines:

- Real stock-market data from Yahoo Finance.
- COVID-controlled return regime analysis.
- NATO defense spending data from NATO's official 2014-2025 expenditure report.
- Manual backlog and fundamentals from company filings / investor releases.
- Statement-derived historical valuation proxies from annual Yahoo Finance financial statements.
- Event-study abnormal returns around conflict escalations.
- A price-derivative layer using log-price velocity and acceleration.
- A composite priced-in score that turns the evidence into an investment verdict.
- Custom single-ticker reports with buy / hold / sell-style research suggestions.

The app is designed to look like an institutional research terminal, not a generic generated website. It opens directly into the analytical workflow and runs locally at `http://localhost:8501`.

## Thesis Question

NATO rearmament, the Ukraine war, rising Asia-Pacific tensions, Iran escalation, and the Venezuela / Maduro event have pushed defense spending into one of the strongest peacetime budget cycles in decades.

The central question:

> Are defense contractors still attractive long-term holdings, or has the market already priced in the conflict premium?

The project is evidence-led. It does not force a bull or bear answer. The final verdict is derived from market performance, valuation, event sensitivity, backlog support, and price-momentum diagnostics.

## Dashboard Preview

Screenshots are stored in `docs/screenshots/` after local capture.

```text
docs/screenshots/dashboard-overview.png
docs/screenshots/derivatives-panel.png
docs/screenshots/scenario-export.png
```

If screenshots are missing, run the dashboard locally and use the capture instructions in the "Screenshots" section below.

## Contractor Universe

| Group | Ticker | Company |
| --- | --- | --- |
| U.S. prime contractor | `LMT` | Lockheed Martin |
| U.S. prime contractor | `RTX` | RTX / Raytheon |
| U.S. prime contractor | `NOC` | Northrop Grumman |
| U.S. prime contractor | `GD` | General Dynamics |
| European defense contractor | `BA.L` | BAE Systems |
| European defense contractor | `RHM.DE` | Rheinmetall |
| Broad market benchmark | `SPY` | S&P 500 ETF |
| Defense benchmark | `ITA` | iShares U.S. Aerospace & Defense ETF |
| Defense benchmark | `XAR` | SPDR S&P Aerospace & Defense ETF |

## Data Sources

Market and company profile data:

- Yahoo Finance through `yfinance`
- Annual income statement and balance sheet rows through `yfinance`

Manual company backlog / fundamental inputs:

- `data/fundamentals_backlog.csv`
- Lockheed Martin FY2024 results: https://investors.lockheedmartin.com/news-releases/news-release-details/lockheed-martin-reports-fourth-quarter-and-full-year-2024/
- RTX FY2024 results: https://www.rtx.com/news/news-center/2025/01/28/rtx-reports-2024-results-and-announces-2025-outlook-2
- Northrop Grumman annual reports: https://www.northropgrumman.com/who-we-are/annual-reports
- General Dynamics FY2024 annual report: https://s22.q4cdn.com/891946778/files/doc_financials/2024/ar/2024-Annual-Report-General-Dynamics-Corporation.pdf
- BAE Systems FY2024 annual report: https://www.baesystems.com/annualreport/2024.html
- Rheinmetall FY2024 figures: https://www.rheinmetall.com/en/media/news-watch/news/2025/03/2025-03-12-rheinmetall-financial-figures-fical-year-2024

Defense budget data:

- `data/defense_budgets.csv`
- NATO Defence Expenditure of NATO Countries 2014-2025: https://www.nato.int/content/dam/nato/webready/documents/finance/def-exp-2025-en.pdf

Geopolitical event registry:

- `data/events.csv`
- Each event has a source URL and notes column so the event study is auditable.

## Methodology

### COVID control

COVID can distort return, volatility, and correlation metrics. The dashboard therefore avoids using 2020-2021 as the baseline.

| Period | Dates | Treatment |
| --- | --- | --- |
| Pre-COVID baseline | `2017-01-01` to `2019-12-31` | Used as the normal-cycle baseline |
| COVID window | `2020-01-01` to `2021-12-31` | Shown visually, excluded from baseline metrics |
| Conflict-premium period | `2022-02-24` to latest available | Main post-Ukraine comparison period |
| Current-conflict extension | `2026-01-01` to latest available | Recent conflict sensitivity window |

### Return regime analysis

The app compares pre-COVID and post-Ukraine periods using:

- Annualized return
- Annualized volatility
- Sharpe-style return / volatility proxy
- Maximum drawdown
- Benchmark-relative excess return
- Return regime shift

### Event study

For each event and ticker:

```text
Abnormal Return[t] = Contractor Return[t] - Benchmark Return[t]
CAR[t] = sum(Abnormal Return from event window start through t)
```

Supported windows:

```text
3, 5, 10, and 20 trading days before and after each event
```

### Historical valuation layer

To reduce dependence on current Yahoo profile snapshots, the dashboard estimates annual historical valuation multiples from statement rows and fiscal-year-end prices.

```text
Market Cap Proxy = Fiscal-Year-End Price x Diluted Average Shares
Enterprise Value Proxy = Market Cap Proxy + Total Debt - Cash
Historical P/E = Market Cap Proxy / Net Income
Historical P/S = Market Cap Proxy / Revenue
Historical EV/EBITDA = Enterprise Value Proxy / EBITDA
```

For London tickers such as `BA.L`, Yahoo prices are adjusted from pence to pounds before comparing market value against GBP statement data.

### Price derivative layer

The dashboard adds a deeper math layer using discrete derivatives of log prices.

Let:

```text
P[t] = adjusted close price
L[t] = ln(P[t])
```

First derivative proxy:

```text
Velocity[t] = L[t] - L[t-1]
```

This is the daily log return. It measures the rate of price movement.

Second derivative proxy:

```text
Acceleration[t] = Velocity[t] - Velocity[t-1]
```

This measures whether momentum is strengthening or fading.

Third derivative diagnostic:

```text
Jerk[t] = Acceleration[t] - Acceleration[t-1]
```

This is used only as a volatility-of-acceleration diagnostic. It is not treated as a standalone trading signal.

Interpretation examples:

- Positive velocity + positive acceleration: momentum improving.
- Positive velocity + negative acceleration: price still rising, but momentum fading.
- Negative velocity + positive acceleration: downtrend stabilizing.
- Negative velocity + negative acceleration: selling pressure increasing.

### Composite priced-in score

The priced-in score is a 0-100 measure where higher means more of the conflict premium appears capitalized.

Inputs:

- Return heat: post-2022 excess return versus benchmark.
- Regime shift heat: improvement versus the pre-COVID baseline.
- Valuation richness: forward P/E and EV/EBITDA percentile where available.
- Historical valuation richness: current multiples versus each stock's own statement-derived history.
- Event sensitivity: average absolute event-window abnormal return.
- Derivative heat: recent velocity and acceleration.
- Backlog support: backlog / revenue.
- Quality support: operating margin and revenue growth.

Simplified structure:

```text
Priced-In Score =
  + return premium
  + valuation richness
  + event sensitivity
  + derivative heat
  - backlog support
  - quality support
```

Verdict bands:

| Score | Interpretation |
| --- | --- |
| `0-42` | Selective buy watchlist |
| `42-68` | Hold / fairly priced |
| `68-100` | Avoid chasing |

## Dashboard Tabs

1. **Market Regimes**  
   Indexed performance, COVID-shaded price history, return-regime comparison, and premium gauge.

2. **Priced-In Score**  
   Composite company scoring, valuation-vs-backlog chart, and action labels.

3. **Derivatives**  
   Smoothed velocity, smoothed acceleration, volatility, acceleration z-score, trend quality, conflict event bars, and interpretation.

4. **Budget & Backlog**  
   NATO defense spending as a percentage of GDP, company backlog, revenue support, and backlog refresh watch.

5. **Historical Valuation**  
   Statement-derived P/E, P/S, and EV/EBITDA history by ticker.

6. **Custom Ticker Report**  
   User-entered Yahoo Finance ticker report with buy / hold / sell-style research suggestion.

7. **Events**  
   Event-study abnormal returns and clickable source registry.

8. **Scenario & Export**  
   De-escalation / base case / escalation assumptions and a downloadable investment memo.

9. **Data Quality**  
   Coverage, missingness, cache status, profile-field availability, statement availability, and manual-data coverage.

Benchmarks and ETFs are scored with ETF-specific profile fields rather than company-only fields. For example, `ITA` is expected to have fields such as trailing P/E, total assets, NAV price, yield, 3-year beta, fund family, and category. It is not penalized for lacking company backlog rows.

## Custom Ticker Reports

Use the sidebar field labeled **Custom defense ticker report** to enter any Yahoo-supported contractor or aerospace ticker.

Examples:

```text
HII
LHX
TXT
AVAV
LDOS
SAAB-B.ST
```

The report generates:

- Buy / hold / sell-style recommendation.
- Single-stock score from 0-100.
- Post-2022 return versus the chosen benchmark.
- Current valuation versus the stock's own statement-derived valuation history.
- 21-day velocity and acceleration diagnostics.
- Event-window abnormal return.
- Backlog / revenue if the ticker exists in `data/fundamentals_backlog.csv`.
- Downloadable Markdown report.

This is a project research output, not personal financial advice.

## COVID Chart Toggle

The dashboard defaults to omitting 2020-2021 from visual time-series and derivative calculations so the COVID shock does not compress later geopolitical movements. The sidebar checkbox **Include COVID in charts** can re-enable the period for inspection.

The analytical baseline remains COVID-controlled either way:

- Pre-COVID baseline: 2017-2019.
- COVID period: 2020-2021.
- Post-conflict-premium period: February 24, 2022 onward.

The derivative chart uses a second smoothing layer on top of the rolling derivative. The default is 63 trading days, adjustable in the sidebar. Conflict event bars remain visible and hoverable in the derivative view.

## API Caching and Throttling Protection

The app uses two layers of caching:

1. `st.cache_data` for in-session Streamlit reuse.
2. Persistent CSV/JSON cache files under `data/cache/`.

Default behavior:

- Cache TTL is 24 hours.
- Annual statement cache TTL is 7 days.
- Market downloads are batched where possible.
- Local cache is checked before API calls.
- Failed or throttled calls fall back to stale cache when available.
- Cache status and last-updated timestamps are shown in the dashboard.
- A manual **Refresh Data** button clears Streamlit cache and forces a new disk/API refresh.

Profile cache keys are schema-versioned so new ETF/company fields are fetched instead of silently reusing older cache files.

## Local Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the dashboard:

```bash
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

## Screenshots

The preferred screenshot command uses local Chrome in headless mode:

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --headless --disable-gpu --window-size=1600,1200 --screenshot="docs\screenshots\dashboard-overview.png" "http://localhost:8501"
```

Run this after the Streamlit app is live. Additional screenshots can be captured by navigating the app and using the same output folder.

## Repository Structure

```text
.
|-- app.py
|-- requirements.txt
|-- README.md
|-- .streamlit/
|   `-- config.toml
|-- data/
|   |-- events.csv
|   |-- defense_budgets.csv
|   |-- fundamentals_backlog.csv
|   `-- cache/
|-- docs/
|   |-- process_log.md
|   `-- screenshots/
|-- reports/
|   `-- final_thesis.md
|-- scripts/
|   `-- capture_screenshots.py
|-- src/
|   |-- __init__.py
|   |-- analysis.py
|   |-- data_loader.py
|   `-- visuals.py
`-- tests/
    `-- test_analysis.py
```

## Test Commands

```bash
python -m compileall app.py src tests
python -m pytest
```

## Limitations

- Historical valuation multiples are estimates from annual statements and fiscal-year-end prices, not institutional-grade point-in-time valuation database fields.
- Manual backlog inputs still require human refresh from filings, but the dashboard now flags stale rows when Yahoo statements show a newer fiscal year.
- Event studies measure market reaction, but do not prove causality.
- Indexed equity returns control for comparability, but do not fully model FX effects in fundamentals.
- The derivative layer is a diagnostic view of price behavior, not a trading strategy.
- The current conflict events should be reviewed before final submission if the project is graded later than June 8, 2026.

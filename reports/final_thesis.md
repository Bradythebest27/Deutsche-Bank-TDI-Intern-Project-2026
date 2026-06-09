# Final Thesis: Defense Spending & the Geopolitical Risk Premium

## Final Verdict

**Verdict: Hold / Selective Entry Only**

Defense contractors remain structurally supported by NATO rearmament, elevated geopolitical risk, and unusually large backlogs. However, the dashboard evidence does not support a broad "buy the whole sector" conclusion at current prices. After adding statement-derived historical valuation proxies, the median contractor in the selected universe screens as close to fairly priced after post-2022 outperformance, with a **median priced-in score of 42.1 / 100**.

The conclusion is therefore differentiated:

- **Do not chase the highest-momentum European winner blindly.** Rheinmetall has the strongest post-Ukraine performance and backlog signal, but it also trades at roughly **1.97x its own median historical EV/EBITDA reference**.
- **Treat the group as a hold at the sector level.** The median contractor's post-2022 return is positive, but it trails the defense ETF benchmark.
- **Use selective entry for names where backlog support is high and price heat is lower.** Lockheed Martin and Northrop Grumman screen as lower priced-in watchlist names, but their return evidence is not strong enough to call them outright buys without more valuation work.

This is the cleanest investment answer: **the defense budget cycle is real, but the equity market has already capitalized a meaningful part of the conflict premium.**

## Data Snapshot

Dashboard run:

| Field | Value |
| --- | --- |
| Data source | Yahoo Finance through cached `yfinance` pulls |
| Market data status | `fresh_cache` |
| Cached at | `2026-06-08T19:32:04Z` |
| Market window | `2017-01-01` to `2026-06-08` |
| Benchmark | `ITA` |
| Event window | 10 trading days |
| Universe | `LMT`, `RTX`, `NOC`, `GD`, `BA.L`, `RHM.DE` |
| Historical valuation method | Annual Yahoo financial statements + fiscal-year-end stock prices |

The dashboard excluded 2020-2021 from the baseline calculations to avoid COVID distortion.

## Core Evidence

### 1. The budget cycle is real

NATO data supports the demand-side thesis. NATO Europe and Canada increased defense spending from **1.51% of GDP in 2019** to an estimated **2.27% in 2025**, a **0.76 percentage point increase**. That matters because the European contractors in the universe, especially BAE Systems and Rheinmetall, are closer to the rearmament impulse than the U.S. primes.

Selected NATO figures from `data/defense_budgets.csv`:

| Country / Group | 2019 | 2024e | 2025e | Thesis Read |
| --- | ---: | ---: | ---: | --- |
| NATO Europe and Canada | 1.51% | 1.99% | 2.27% | Broad European spending inflection |
| NATO Total | 2.52% | 2.61% | 2.76% | Alliance-wide spending rising |
| Poland | 1.96% | 3.79% | 4.48% | Eastern flank rearmament is extreme |
| United Kingdom | 2.08% | 2.33% | 2.40% | Sustained above-target spending |
| France | 1.82% | 2.03% | 2.05% | Gradual but real increase |
| Germany | 1.33% | 2.00% | n/a | Major inflection from under-spending |
| United States | 3.49% | 3.21% | 3.22% | Already high, less incremental surprise |

This supports the bull case that defense budgets are not a short-lived headline trade. The biggest incremental change is in Europe, not the United States.

### 2. Backlog support is large

The manual fundamentals file shows the contractors are not just trading on a story. Backlog coverage is substantial across the group.

| Ticker | Company | Revenue | Backlog | Backlog / Revenue | Book to Bill |
| --- | ---: | ---: | ---: | ---: | ---: |
| `RHM.DE` | Rheinmetall | EUR 9.75B | EUR 55.0B | 5.64x | 2.00x |
| `BA.L` | BAE Systems | GBP 28.34B | GBP 77.8B | 2.75x | 1.19x |
| `RTX` | RTX | USD 80.8B | USD 218.0B | 2.70x | 1.11x |
| `LMT` | Lockheed Martin | USD 71.0B | USD 176.0B | 2.48x | 1.12x |
| `NOC` | Northrop Grumman | USD 41.0B | USD 91.5B | 2.23x | 1.00x |
| `GD` | General Dynamics | USD 47.7B | USD 90.6B | 1.90x | 1.00x |

The median backlog / revenue ratio is **2.59x**, which is strong. This means the sector has real revenue visibility. It also explains why the thesis should not be bearish just because some stocks look fully priced.

### 3. Post-2022 equity performance is positive, but not uniformly better than the defense benchmark

The post-Ukraine period began on February 24, 2022. Since then, the median selected contractor generated a **16.4% annualized return**, compared with **21.4% for `ITA`**. The median contractor therefore underperformed the benchmark by **4.9 percentage points annually**.

| Ticker | Pre-COVID Ann. Return | Post-2022 Ann. Return | Excess vs `ITA` | Post-2022 Total Return | Max Drawdown |
| --- | ---: | ---: | ---: | ---: | ---: |
| `RHM.DE` | 18.3% | 80.4% | +59.0% | 1228.3% | -43.1% |
| `BA.L` | -1.4% | 30.5% | +9.1% | 221.7% | -21.9% |
| `RTX` | 12.8% | 19.3% | -2.1% | 116.5% | -32.8% |
| `GD` | 2.1% | 13.6% | -7.8% | 75.1% | -22.5% |
| `LMT` | 18.0% | 10.0% | -11.4% | 51.7% | -31.8% |
| `NOC` | 15.0% | 9.9% | -11.4% | 51.6% | -31.2% |
| `ITA` | 17.0% | 21.4% | 0.0% | 133.9% | -18.7% |

This is the key finding. The defense theme worked, but simply buying the individual contractor basket did not beat the defense ETF benchmark on a median basis. The outperformance is concentrated in Europe, especially Rheinmetall and BAE Systems.

### 4. Historical valuation improves the analysis but does not create a broad buy signal

The original project limitation was that Yahoo Finance profile fields are current snapshots. The dashboard now reduces that limitation by using annual financial-statement rows to estimate historical valuation multiples.

The method is:

```text
Market Cap Proxy = Fiscal-Year-End Price x Diluted Average Shares
Enterprise Value Proxy = Market Cap Proxy + Total Debt - Cash
Historical P/E = Market Cap Proxy / Net Income
Historical P/S = Market Cap Proxy / Revenue
Historical EV/EBITDA = Enterprise Value Proxy / EBITDA
```

For London tickers such as `BA.L`, the app adjusts the Yahoo price from pence to pounds before comparing market value with GBP statement data.

| Ticker | Latest Fiscal Year | Current Forward P/E vs History | Current EV/EBITDA vs History | Statement Years |
| --- | ---: | ---: | ---: | ---: |
| `RHM.DE` | 2025 | 0.69x | 1.97x | 4 |
| `BA.L` | 2025 | 1.14x | 1.68x | 4 |
| `GD` | 2025 | 0.95x | 1.06x | 4 |
| `NOC` | 2025 | 1.00x | 1.02x | 4 |
| `RTX` | 2025 | 0.70x | 1.18x | 5 |
| `LMT` | 2025 | 0.78x | 1.18x | 5 |

This makes the conclusion more nuanced. On P/E, several U.S. primes do not look expensive versus their own recent history. On EV/EBITDA, however, the major European winners look richer, especially Rheinmetall and BAE Systems. The result is still a **hold / selective entry** verdict rather than a broad buy.

### 5. The priced-in score says the sector is fairly valued, not cheap

The dashboard's composite score combines return heat, valuation richness, event sensitivity, derivative heat, backlog support, and quality support. Higher scores mean more of the conflict premium appears priced in.

| Ticker | Priced-In Score | Dashboard Action | Interpretation |
| --- | ---: | --- | --- |
| `RHM.DE` | 63.0 | Hold / Fairly Priced | Best growth signal, but EV/EBITDA is rich versus history |
| `BA.L` | 61.4 | Hold / Fairly Priced | Strong European exposure, but valuation has re-rated |
| `GD` | 45.9 | Hold / Fairly Priced | Stable but less upside signal |
| `NOC` | 38.4 | Selective Buy Watchlist | Lower priced-in signal, weaker recent performance |
| `RTX` | 38.3 | Selective Buy Watchlist | Good backlog and valuation support, but mixed return evidence |
| `LMT` | 37.0 | Selective Buy Watchlist | Lower priced-in signal, but post-2022 underperformance |

The median score of **42.1** lands just inside the dashboard's **Hold / Selective Entry Only** band. This is why the final conclusion is not "avoid defense" and not "buy everything." It is a quality-sensitive, entry-price-sensitive hold.

## Event Study

The event study measures 10-trading-day cumulative abnormal return versus `ITA`. It asks whether selected defense contractors outperformed the defense benchmark around major geopolitical events.

| Event | `BA.L` | `GD` | `LMT` | `NOC` | `RHM.DE` | `RTX` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Russia invades Ukraine | +21.5% | +7.9% | +11.9% | +14.6% | +50.5% | +2.2% |
| Israel-Hamas war begins | +4.8% | +6.6% | +7.0% | +12.1% | +2.8% | +1.3% |
| U.S. capture of Maduro after Venezuela strikes | +4.4% | -8.2% | +3.3% | -0.3% | +5.9% | -4.4% |
| U.S.-Israel Iran campaign escalation | +17.9% | +2.8% | +0.3% | +6.0% | +2.7% | +4.3% |

Average 10-day terminal abnormal return:

| Ticker | Mean Terminal CAR | Mean Absolute Terminal CAR | Positive Event Hit Rate |
| --- | ---: | ---: | ---: |
| `RHM.DE` | +15.5% | 15.5% | 100% |
| `BA.L` | +12.1% | 12.1% | 100% |
| `NOC` | +8.1% | 8.3% | 75% |
| `LMT` | +5.6% | 5.6% | 100% |
| `GD` | +2.3% | 6.4% | 75% |
| `RTX` | +0.9% | 3.1% | 75% |

This supports the idea that geopolitical shocks still matter for defense equities. But the response is uneven. European names again show the clearest sensitivity.

The June 2026 Iran escalation events are included in `data/events.csv`, but they are not yet included in the 10-day event-study table because the dashboard data ending June 8, 2026 does not yet provide a complete post-event trading window.

## Price Derivative Analysis

The dashboard adds a math layer using log-price derivatives:

```text
Velocity[t] = ln(P[t]) - ln(P[t-1])
Acceleration[t] = Velocity[t] - Velocity[t-1]
Jerk[t] = Acceleration[t] - Acceleration[t-1]
```

Velocity measures recent price impulse. Acceleration measures whether that impulse is strengthening or weakening. This matters because a stock can still be up dramatically while the rate of improvement is fading.

Latest 21-day derivative diagnostics:

| Ticker | 21D Velocity | 21D Acceleration | Acceleration Z-Score | Dashboard Interpretation |
| --- | ---: | ---: | ---: | --- |
| `LMT` | +34.1% | +15.2% | -0.22 | Momentum improving |
| `RTX` | +33.2% | +10.3% | -1.20 | Momentum improving |
| `GD` | -4.6% | +15.5% | +0.06 | Downtrend stabilizing |
| `NOC` | -12.0% | +14.1% | -1.60 | Downtrend stabilizing |
| `BA.L` | -43.0% | +61.0% | -0.04 | Downtrend stabilizing |
| `RHM.DE` | -112.2% | +105.9% | +0.77 | Downtrend stabilizing |

The derivative evidence is important for the conclusion. It suggests the hottest European names are no longer in a clean upward impulse even though their long-term post-2022 returns are extraordinary. Rheinmetall, for example, has the strongest post-2022 return but also shows negative recent velocity with positive acceleration, meaning the drawdown is stabilizing rather than the prior surge continuing cleanly.

For the U.S. primes, Lockheed Martin and RTX show improving short-term momentum, but their post-2022 excess returns versus `ITA` remain negative. That makes them candidates for selective entry rather than proof of broad sector upside.

## Scenario Analysis

The dashboard compounds each contractor's post-2022 annualized return for three years under three simple scenarios:

- De-escalation: annual premium reduced by 4 percentage points.
- Base case: post-2022 annualized return continues.
- Escalation: annual premium increased by 4 percentage points.

Base-case 3-year indexed outcomes, starting at 100:

| Ticker | Scenario Annual Return | 3Y Indexed Outcome |
| --- | ---: | ---: |
| `RHM.DE` | 80.4% | 587 |
| `BA.L` | 30.5% | 222 |
| `RTX` | 19.3% | 170 |
| `GD` | 13.6% | 147 |
| `LMT` | 10.0% | 133 |
| `NOC` | 9.9% | 133 |

This scenario view is not a forecast. It shows sensitivity. The exercise makes clear that the upside case is extremely dependent on Rheinmetall-like performance continuing, which is a high bar after a 1228% post-2022 total return.

## Custom Ticker Extension

The dashboard now allows the user to enter any Yahoo-supported defense or aerospace contractor ticker and generate a single-stock report. The custom report produces a **Buy**, **Hold**, **Sell / Avoid**, or **Insufficient Data** recommendation.

The single-stock score uses:

- Post-2022 return versus the selected benchmark.
- Current valuation versus the stock's own statement-derived historical valuation.
- 21-day velocity and acceleration.
- Event-window abnormal return.
- Backlog / revenue when the ticker exists in the manual backlog file.

This solves a major scope limitation because the app is no longer locked to the original six-stock universe. A user can test names such as `HII`, `LHX`, `TXT`, `AVAV`, `LDOS`, or international Yahoo tickers if data is available.

Example smoke test:

| Custom Ticker | Recommendation | Score | Key Read |
| --- | --- | ---: | --- |
| `HII` | Hold | 46.7 | Mixed evidence: reasonable P/E versus history, but post-2022 excess return and recent velocity were weak. |

This custom output should be interpreted as a research suggestion for the project, not personal financial advice.

## Final Investment Stance by Name

| Ticker | Stance | Rationale |
| --- | --- | --- |
| `RHM.DE` | Hold / do not chase | Best exposure to European rearmament and highest backlog / revenue, but EV/EBITDA is rich versus its own history. |
| `BA.L` | Hold | Strong backlog, positive event sensitivity, and 30.5% post-2022 annualized return, but no longer clearly cheap. |
| `RTX` | Selective buy watchlist | Strong backlog and improved historical valuation support, but only -2.1% excess return versus `ITA`. |
| `GD` | Hold | Stable fundamentals and lower drawdown than several peers, but modest benchmark-relative performance. |
| `NOC` | Selective buy watchlist | Lower priced-in score, but weak post-2022 excess return requires patience and valuation discipline. |
| `LMT` | Selective buy watchlist | Lowest priced-in score and improving momentum, but post-2022 return trails `ITA` by 11.4 percentage points annually. |

## Final Answer

Defense contractors are **not a simple buy at any price**. The fundamental support is real: NATO budgets are rising, backlogs are large, and geopolitical events still produce measurable abnormal returns. But the equity evidence shows that the market has already rewarded the sector, especially the European rearmament winners.

At current dashboard readings, the best conclusion is:

> **Defense contractors are a long-term hold, not a broad fresh buy. The sector deserves exposure because the spending cycle is durable, but new money should be selective and valuation-sensitive. European names have the strongest structural growth, but also the clearest signs of priced-in conflict premium. U.S. primes offer more disciplined entry points, but their post-2022 performance has generally lagged the defense benchmark.**

This verdict directly matches the dashboard's median **Hold / Selective Entry Only** signal and is supported by the data rather than by the narrative alone.

## Limitation Mitigation

The two biggest limitations have been reduced:

1. **Current Yahoo profile snapshots:** the app now estimates historical valuation using annual statements and fiscal-year-end prices. This creates a stock-specific valuation history rather than relying only on current P/E or EV/EBITDA.
2. **Manual backlog refresh risk:** the app now includes a backlog refresh watch. It compares the manual backlog fiscal year with the latest Yahoo annual statement year and flags all six current manual backlog rows as **Refresh recommended** because Yahoo statements now include FY2025 while the manual backlog file is FY2024.

Backlog still cannot be perfectly automated from free structured data because backlog is usually disclosed in company filings and earnings releases rather than standardized financial statement rows. The best current solution is a monitored manual refresh workflow with source links.

## Limitations

- Historical valuation multiples are approximations because they combine fiscal-year-end prices with annual statement data rather than using an institutional valuation database.
- Manual backlog data still requires human refresh from filings, but the dashboard now flags likely stale rows automatically.
- Event studies show abnormal return patterns, but they do not prove causality.
- European and U.S. fundamentals are reported in different currencies, so backlog / revenue is interpreted within-company rather than as a cross-currency valuation.
- The June 2026 Iran events need more trading days before they can be fully evaluated in the 10-day event-study framework.

## Sources

- Yahoo Finance via `yfinance`, cached in `data/cache/`.
- NATO Defence Expenditure of NATO Countries 2014-2025: https://www.nato.int/content/dam/nato/webready/documents/finance/def-exp-2025-en.pdf
- Lockheed Martin FY2024 results: https://investors.lockheedmartin.com/news-releases/news-release-details/lockheed-martin-reports-fourth-quarter-and-full-year-2024/
- RTX FY2024 results: https://www.rtx.com/news/news-center/2025/01/28/rtx-reports-2024-results-and-announces-2025-outlook-2
- Northrop Grumman annual reports: https://www.northropgrumman.com/who-we-are/annual-reports
- General Dynamics FY2024 annual report: https://s22.q4cdn.com/891946778/files/doc_financials/2024/ar/2024-Annual-Report-General-Dynamics-Corporation.pdf
- BAE Systems FY2024 annual report: https://www.baesystems.com/annualreport/2024.html
- Rheinmetall FY2024 figures: https://www.rheinmetall.com/en/media/news-watch/news/2025/03/2025-03-12-rheinmetall-financial-figures-fical-year-2024
- Event registry: `data/events.csv`

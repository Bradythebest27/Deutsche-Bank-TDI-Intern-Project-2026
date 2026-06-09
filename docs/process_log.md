# Process Log

## Initial Direction

The first plan focused on a straightforward market thesis: compare defense contractor returns against broad and defense benchmarks, then judge whether the conflict premium looked justified.

## Upgrade Pass

The project was expanded from a basic dashboard into a more professional research terminal:

- Added NATO budget data.
- Added manual backlog and fundamentals.
- Added source links for events and company data.
- Added data-quality diagnostics.
- Added scenario analysis.
- Added exportable investment memo.
- Added price derivatives for a more quantitative layer.

## Key Pivot

The original valuation idea was to compare current multiples against 10-year historical averages. That proved fragile because free APIs are inconsistent for historical P/E and EV/EBITDA, especially across U.S. and European listings.

The pivot was to use a more defensible evidence stack:

- Price returns and volatility from Yahoo Finance.
- Current valuation fields from Yahoo Finance.
- Manual backlog and annual-report data from company sources.
- Official NATO defense spending data.
- Event studies and price derivatives.

## Why COVID Is Controlled

COVID is excluded from baseline calculations because 2020-2021 had abnormal liquidity, defense supply-chain disruption, and market-wide volatility. The dashboard still shades the period visually so the exclusion is transparent.

## What Failed or Was De-Scoped

- Fully automated historical valuation data was de-scoped because it was not reliable enough from free APIs.
- A full DCF was not added because it would require many assumptions and distract from the thesis-testing goal.

## Current Strengths

- Clear thesis.
- Real data.
- Professional Streamlit interface.
- Audit trail through CSV source files.
- COVID-controlled analysis.
- Higher-tier features: scenario engine, export, and quantitative derivative diagnostics.

## Remaining Future Enhancements

- Add a paid or institutional valuation dataset if available.
- Add earnings-call transcript summarization with an LLM.
- Add analyst-estimate revisions.
- Add FX-adjusted fundamental comparisons for European names.
- Add automated PDF extraction for annual reports.

## Limitation Mitigation Pass

Two important limitations were addressed after the first full dashboard build:

- **Current Yahoo profile snapshots:** added annual statement pulls from Yahoo Finance and built statement-derived historical P/E, P/S, and EV/EBITDA proxies using fiscal-year-end stock prices.
- **Manual backlog refresh risk:** added a backlog refresh watch that compares the manual backlog fiscal year against the latest available annual statement year and flags stale rows.

A custom ticker report was also added so the app is no longer limited to the original six-stock universe. Users can enter a Yahoo-supported defense or aerospace ticker and receive a buy / hold / sell-style research suggestion with a downloadable Markdown memo.

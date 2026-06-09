from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd
import yfinance as yf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
CACHE_TTL_HOURS = 24
STATEMENT_CACHE_TTL_HOURS = 24 * 7


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_cache_dir() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _stable_key(parts: Iterable[object]) -> str:
    raw = "|".join(str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _cache_paths(key: str, data_type: str) -> tuple[Path, Path]:
    _ensure_cache_dir()
    return CACHE_DIR / f"{data_type}_{key}.csv", CACHE_DIR / f"{data_type}_{key}.json"


def _metadata_is_fresh(metadata_path: Path, ttl_hours: int) -> bool:
    if not metadata_path.exists():
        return False
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        cached_at = datetime.fromisoformat(metadata["cached_at"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return False

    age_seconds = (_utc_now() - cached_at).total_seconds()
    return age_seconds < ttl_hours * 3600


def _write_metadata(metadata_path: Path, metadata: dict[str, object]) -> None:
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _read_metadata(metadata_path: Path, status: str) -> dict[str, object]:
    if not metadata_path.exists():
        return {"status": status, "cached_at": None, "source": "none"}
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        metadata = {"cached_at": None, "source": "cache"}
    metadata["status"] = status
    return metadata


def _load_cached_frame(csv_path: Path, metadata_path: Path, status: str) -> tuple[pd.DataFrame, dict[str, object]]:
    frame = pd.read_csv(csv_path, parse_dates=["Date"])
    return frame, _read_metadata(metadata_path, status)


def _first_available(statement: pd.DataFrame, aliases: list[str], column: object) -> object:
    for alias in aliases:
        if alias in statement.index:
            value = statement.loc[alias, column]
            if pd.notna(value):
                return value
    return pd.NA


def _statement_period_label(fiscal_date: pd.Timestamp, period_type: str) -> str:
    return f"{fiscal_date.year}Q{fiscal_date.quarter}"


def _normalize_yfinance_download(raw: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame()

    frames: list[pd.DataFrame] = []

    if isinstance(raw.columns, pd.MultiIndex):
        level_zero = list(raw.columns.get_level_values(0).unique())
        ticker_first = any(ticker in level_zero for ticker in tickers)

        for ticker in tickers:
            try:
                ticker_frame = raw[ticker] if ticker_first else raw.xs(ticker, axis=1, level=1)
            except (KeyError, ValueError):
                continue
            ticker_frame = ticker_frame.copy()
            ticker_frame["Ticker"] = ticker
            frames.append(ticker_frame.reset_index())
    else:
        ticker_frame = raw.copy()
        ticker_frame["Ticker"] = tickers[0]
        frames.append(ticker_frame.reset_index())

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.rename(columns={"index": "Date"})
    combined["Date"] = pd.to_datetime(combined["Date"]).dt.tz_localize(None)

    expected_columns = ["Date", "Ticker", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
    for column in expected_columns:
        if column not in combined.columns:
            combined[column] = pd.NA

    combined = combined[expected_columns]
    combined = combined.dropna(subset=["Date", "Ticker"])
    return combined.sort_values(["Ticker", "Date"]).reset_index(drop=True)


def load_market_data(
    tickers: list[str],
    start: str,
    end: str,
    interval: str = "1d",
    force_refresh: bool = False,
    cache_ttl_hours: int = CACHE_TTL_HOURS,
    max_retries: int = 3,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Load OHLCV market data with disk caching and stale-cache fallback."""
    clean_tickers = sorted(dict.fromkeys(tickers))
    key = _stable_key([",".join(clean_tickers), start, end, interval, "prices"])
    csv_path, metadata_path = _cache_paths(key, "prices")

    if csv_path.exists() and not force_refresh and _metadata_is_fresh(metadata_path, cache_ttl_hours):
        return _load_cached_frame(csv_path, metadata_path, "fresh_cache")

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            raw = yf.download(
                tickers=clean_tickers,
                start=start,
                end=end,
                interval=interval,
                auto_adjust=False,
                group_by="ticker",
                progress=False,
                threads=True,
            )
            normalized = _normalize_yfinance_download(raw, clean_tickers)
            if normalized.empty:
                raise RuntimeError("Yahoo Finance returned no rows.")

            normalized.to_csv(csv_path, index=False)
            metadata = {
                "status": "api",
                "source": "yfinance",
                "tickers": clean_tickers,
                "start": start,
                "end": end,
                "interval": interval,
                "cached_at": _utc_now().isoformat(),
                "rows": int(len(normalized)),
            }
            _write_metadata(metadata_path, metadata)
            return normalized, metadata
        except Exception as exc:  # pragma: no cover - depends on network/API behavior
            last_error = exc
            time.sleep(1.5 * (attempt + 1))

    if csv_path.exists():
        cached_frame, metadata = _load_cached_frame(csv_path, metadata_path, "stale_fallback")
        metadata["warning"] = f"API refresh failed; using cached data. Last error: {last_error}"
        return cached_frame, metadata

    raise RuntimeError(f"Could not load market data and no cache exists. Last error: {last_error}")


def load_company_profiles(
    tickers: list[str],
    force_refresh: bool = False,
    cache_ttl_hours: int = CACHE_TTL_HOURS,
    max_retries: int = 2,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Load lightweight company profile fields with cache protection."""
    clean_tickers = sorted(dict.fromkeys(tickers))
    key = _stable_key([",".join(clean_tickers), "profiles_v2"])
    csv_path, metadata_path = _cache_paths(key, "profiles")

    if csv_path.exists() and not force_refresh and _metadata_is_fresh(metadata_path, cache_ttl_hours):
        return _load_cached_frame(csv_path, metadata_path, "fresh_cache")

    rows: list[dict[str, object]] = []
    last_error: Exception | None = None
    for ticker in clean_tickers:
        for attempt in range(max_retries):
            try:
                info = yf.Ticker(ticker).info or {}
                rows.append(
                    {
                        "Date": pd.Timestamp.utcnow().tz_localize(None),
                        "Ticker": ticker,
                        "Name": info.get("shortName") or info.get("longName") or ticker,
                        "Quote Type": info.get("quoteType"),
                        "Category": info.get("category"),
                        "Fund Family": info.get("fundFamily"),
                        "Market Cap": info.get("marketCap"),
                        "Total Assets": info.get("totalAssets"),
                        "NAV Price": info.get("navPrice"),
                        "Fund Yield": info.get("yield"),
                        "Trailing P/E": info.get("trailingPE"),
                        "Forward P/E": info.get("forwardPE"),
                        "EV/Revenue": info.get("enterpriseToRevenue"),
                        "EV/EBITDA": info.get("enterpriseToEbitda"),
                        "Profit Margin": info.get("profitMargins"),
                        "Operating Margin": info.get("operatingMargins"),
                        "Revenue Growth": info.get("revenueGrowth"),
                        "Beta": info.get("beta"),
                        "Beta 3Y": info.get("beta3Year"),
                    }
                )
                break
            except Exception as exc:  # pragma: no cover - depends on network/API behavior
                last_error = exc
                time.sleep(1.5 * (attempt + 1))

    if rows:
        frame = pd.DataFrame(rows)
        frame.to_csv(csv_path, index=False)
        metadata = {
            "status": "api",
            "source": "yfinance",
            "tickers": clean_tickers,
            "cached_at": _utc_now().isoformat(),
            "rows": int(len(frame)),
        }
        _write_metadata(metadata_path, metadata)
        return frame, metadata

    if csv_path.exists():
        cached_frame, metadata = _load_cached_frame(csv_path, metadata_path, "stale_fallback")
        metadata["warning"] = f"Profile refresh failed; using cached data. Last error: {last_error}"
        return cached_frame, metadata

    empty = pd.DataFrame({"Date": [], "Ticker": []})
    return empty, {"status": "unavailable", "source": "none", "warning": str(last_error)}


def load_financial_statements(
    tickers: list[str],
    force_refresh: bool = False,
    cache_ttl_hours: int = STATEMENT_CACHE_TTL_HOURS,
    max_retries: int = 2,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Load annual and quarterly financial-statement rows used for historical valuation proxies."""
    clean_tickers = sorted(dict.fromkeys(tickers))
    key = _stable_key([",".join(clean_tickers), "annual_quarterly_statements_v3"])
    csv_path, metadata_path = _cache_paths(key, "statements")

    if csv_path.exists() and not force_refresh and _metadata_is_fresh(metadata_path, cache_ttl_hours):
        return _load_cached_frame(csv_path, metadata_path, "fresh_cache")

    rows: list[dict[str, object]] = []
    last_error: Exception | None = None
    for ticker in clean_tickers:
        for attempt in range(max_retries):
            try:
                yf_ticker = yf.Ticker(ticker)
                statement_sets = [
                    ("Annual", yf_ticker.income_stmt, yf_ticker.balance_sheet, 1),
                    ("Quarterly", yf_ticker.quarterly_income_stmt, yf_ticker.quarterly_balance_sheet, 4),
                ]
                if all(income is None or income.empty for _, income, _, _ in statement_sets):
                    raise RuntimeError(f"No income statement rows returned for {ticker}.")

                for period_type, income, balance, annualization_factor in statement_sets:
                    if income is None or income.empty:
                        continue

                    statement_dates = sorted(income.columns, reverse=True)
                    for statement_date in statement_dates:
                        fiscal_date = pd.to_datetime(statement_date).tz_localize(None)
                        balance_col = statement_date if balance is not None and statement_date in balance.columns else None
                        rows.append(
                            {
                                "Date": fiscal_date,
                                "Ticker": ticker,
                                "Period Type": period_type,
                                "Fiscal Year": int(fiscal_date.year),
                                "Fiscal Quarter": int(fiscal_date.quarter) if period_type == "Quarterly" else pd.NA,
                                "Fiscal Period": _statement_period_label(fiscal_date, period_type),
                                "Annualization Factor": annualization_factor,
                                "Revenue": _first_available(income, ["Total Revenue", "Operating Revenue"], statement_date),
                                "EBITDA": _first_available(income, ["EBITDA", "Normalized EBITDA"], statement_date),
                                "EBIT": _first_available(
                                    income,
                                    ["EBIT", "Operating Income", "Total Operating Income As Reported"],
                                    statement_date,
                                ),
                                "Net Income": _first_available(
                                    income,
                                    ["Net Income", "Net Income Common Stockholders", "Normalized Income"],
                                    statement_date,
                                ),
                                "Diluted Average Shares": _first_available(
                                    income,
                                    ["Diluted Average Shares", "Basic Average Shares"],
                                    statement_date,
                                ),
                                "Total Debt": _first_available(balance, ["Total Debt"], balance_col)
                                if balance_col is not None
                                else pd.NA,
                                "Cash": _first_available(
                                    balance,
                                    ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"],
                                    balance_col,
                                )
                                if balance_col is not None
                                else pd.NA,
                                "Ordinary Shares": _first_available(balance, ["Ordinary Shares Number"], balance_col)
                                if balance_col is not None
                                else pd.NA,
                            }
                        )
                break
            except Exception as exc:  # pragma: no cover - depends on network/API behavior
                last_error = exc
                time.sleep(1.5 * (attempt + 1))

    if rows:
        frame = pd.DataFrame(rows)
        numeric_columns = [
            "Revenue",
            "EBITDA",
            "EBIT",
            "Net Income",
            "Diluted Average Shares",
            "Total Debt",
            "Cash",
            "Ordinary Shares",
            "Annualization Factor",
        ]
        for column in numeric_columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame = frame.sort_values(["Ticker", "Date"], ascending=[True, False]).reset_index(drop=True)
        frame.to_csv(csv_path, index=False)
        metadata = {
            "status": "api",
            "source": "yfinance",
            "tickers": clean_tickers,
            "cached_at": _utc_now().isoformat(),
            "rows": int(len(frame)),
        }
        _write_metadata(metadata_path, metadata)
        return frame, metadata

    if csv_path.exists():
        cached_frame, metadata = _load_cached_frame(csv_path, metadata_path, "stale_fallback")
        metadata["warning"] = f"Statement refresh failed; using cached data. Last error: {last_error}"
        return cached_frame, metadata

    empty = pd.DataFrame({"Date": [], "Ticker": []})
    return empty, {"status": "unavailable", "source": "none", "warning": str(last_error)}


def load_events(path: Path | None = None) -> pd.DataFrame:
    events_path = path or PROJECT_ROOT / "data" / "events.csv"
    events = pd.read_csv(events_path, parse_dates=["date"])
    return events.sort_values("date").reset_index(drop=True)


def load_manual_fundamentals(path: Path | None = None) -> pd.DataFrame:
    fundamentals_path = path or PROJECT_ROOT / "data" / "fundamentals_backlog.csv"
    fundamentals = pd.read_csv(fundamentals_path)
    numeric_columns = [
        "Fiscal Year",
        "Revenue",
        "Operating Income",
        "Backlog",
        "Defense Backlog",
        "Book to Bill",
        "Manual Revenue Growth",
    ]
    for column in numeric_columns:
        if column in fundamentals.columns:
            fundamentals[column] = pd.to_numeric(fundamentals[column], errors="coerce")
    return fundamentals


def load_defense_budgets(path: Path | None = None) -> pd.DataFrame:
    budgets_path = path or PROJECT_ROOT / "data" / "defense_budgets.csv"
    budgets = pd.read_csv(budgets_path)
    budgets["Year"] = budgets["Year"].astype(str)
    budgets["Defense Spending % GDP"] = pd.to_numeric(budgets["Defense Spending % GDP"], errors="coerce")
    return budgets

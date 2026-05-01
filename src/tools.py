"""
Tools for The Autonomous Investment Committee agents.

Provides market data, search, and scanning capabilities.
Includes retry logic, timeouts, and ticker sanitization.
"""

import json
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import yfinance as yf
from duckduckgo_search import DDGS
from tenacity import (
    retry,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential,
    retry_if_exception_type,
)

from crewai.tools import tool
from .config import PROJECT_ROOT

# -----------------------------------------------------------------------------
# Retry & Timeout Configuration
# -----------------------------------------------------------------------------

TOOL_TIMEOUT_SECONDS = 30
MAX_RETRIES = 3


@retry(
    stop=(stop_after_attempt(MAX_RETRIES) | stop_after_delay(TOOL_TIMEOUT_SECONDS)),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
    reraise=True,
)
def _yf_with_retry(ticker_symbol: str, period: str = "5d"):
    """Fetch yfinance data with retry. Raises on final failure."""
    data = yf.Ticker(ticker_symbol)
    info = data.info
    hist = data.history(period=period)
    return data, info, hist


# -----------------------------------------------------------------------------
# Ticker Sanitizer
# -----------------------------------------------------------------------------

BLACKLIST = frozenset({
    "OF", "THAT", "HIGH", "ARE", "NOT", "FOR", "THE", "AND", "BUT", "YOU",
    "ALL", "CAN", "HAD", "HER", "WAS", "ONE", "OUR", "OUT", "HAS", "HIS",
    "HOW", "MAN", "NEW", "NOW", "OLD", "SEE", "WAY", "WHO", "DID", "GET",
    "GOT", "LET", "PUT", "SAY", "SHE", "TOO", "USE", "ANY", "ITS", "MAY",
    "OWN", "RUN", "SET", "TRY", "TOP", "BIG", "BUY", "LOW", "USD",
})


def _is_valid_ticker(symbol: str, asset_type: str) -> bool:
    """Verify ticker exists in yfinance and is not a blacklisted word."""
    symbol = symbol.strip().upper()
    if not symbol or len(symbol) < 2 or len(symbol) > 10:
        return False
    if symbol in BLACKLIST:
        return False
    try:
        sym = f"{symbol}-USD" if asset_type == "crypto" and "-" not in symbol else symbol
        _, info, hist = _yf_with_retry(sym, "5d")
        price = info.get("regularMarketPrice") or info.get("previousClose")
        if price is None and (hist.empty or len(hist) == 0):
            return False
        if price is not None and (price <= 0 or not isinstance(price, (int, float))):
            return False
        return True
    except Exception:
        return False


def _sanitize_tickers(candidates: list[str], asset_type: str, max_results: int) -> list[str]:
    """Filter and validate tickers; return only those that exist in yfinance."""
    seen = set()
    valid = []
    for t in candidates:
        t = t.strip().upper()
        if t in seen or t in BLACKLIST:
            continue
        if _is_valid_ticker(t, asset_type):
            seen.add(t)
            valid.append(t)
            if len(valid) >= max_results:
                break
    return valid


# -----------------------------------------------------------------------------
# SQLite Cache Context Manager
# -----------------------------------------------------------------------------

CACHE_DB = PROJECT_ROOT / ".aic_cache.db"


@contextmanager
def sqlite_cache_connection():
    """Context manager for SQLite cache—ensures connections are properly closed."""
    conn = None
    try:
        conn = sqlite3.connect(str(CACHE_DB), timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL")
        yield conn
    finally:
        if conn:
            conn.close()


# -----------------------------------------------------------------------------
# DuckDuckGo Search with Retry & Timeout
# -----------------------------------------------------------------------------


@retry(
    stop=(stop_after_attempt(MAX_RETRIES) | stop_after_delay(TOOL_TIMEOUT_SECONDS)),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
    reraise=True,
)
def _ddg_text_search(query: str, max_results: int = 10) -> str:
    """Run DuckDuckGo text search with retry."""
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    parts = []
    for r in results:
        title = r.get("title", "")
        body = r.get("body", "")
        if title or body:
            parts.append(f"{title}\n{body}")
    return "\n\n".join(parts) if parts else ""


@retry(
    stop=(stop_after_attempt(MAX_RETRIES) | stop_after_delay(TOOL_TIMEOUT_SECONDS)),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
    reraise=True,
)
def _ddg_news_search(query: str, max_results: int = 5) -> list[dict]:
    """Run DuckDuckGo news search with retry."""
    with DDGS() as ddgs:
        results = list(ddgs.news(query, max_results=max_results))
    return [
        {"title": r.get("title"), "snippet": (r.get("body") or "")[:300], "url": r.get("url")}
        for r in results
    ]


# -----------------------------------------------------------------------------
# Tools
# -----------------------------------------------------------------------------


@tool("Market Scanner")
def market_scanner(
    query: str,
    asset_type: str = "stocks",
    max_results: int = 5,
) -> str:
    """
    Scan the market for trending tickers or news based on a research query.

    Use this to find stocks or crypto that match criteria like:
    - "AI sector stocks", "undervalued tech", "high growth crypto"
    - "trending stocks today", "top gainers", "low RSI stocks"

    Args:
        query: Research criteria (e.g., "AI stocks 2024", "high yield crypto")
        asset_type: "stocks" or "crypto"
        max_results: Max number of tickers/news items to return (default 5)

    Returns:
        JSON string with tickers, brief descriptions, and relevant news snippets.
        Only returns tickers verified to exist in yfinance.
    """
    results = {"tickers": [], "news": [], "query": query}

    try:
        search_query = f"{query} {asset_type} ticker symbol 2024"
        search_output = _ddg_text_search(search_query, max_results=max_results * 2)

        results["news"].append({"snippet": search_output[:500]})

        text_upper = search_output.upper()
        ticker_pattern = re.compile(r"\b([A-Z]{2,5}(?:-USD)?)\b")
        candidates = []
        seen = set()
        for m in ticker_pattern.finditer(text_upper):
            t = m.group(1)
            if t not in seen and 2 <= len(t) <= 10:
                seen.add(t)
                candidates.append(t)

        valid_tickers = _sanitize_tickers(candidates, asset_type, max_results)

        enriched = []
        for t in valid_tickers:
            try:
                sym = f"{t}-USD" if asset_type == "crypto" and "-" not in t else t
                _, info, hist = _yf_with_retry(sym, "5d")
                price = info.get("regularMarketPrice") or info.get("previousClose")
                if price is None and not hist.empty:
                    price = float(hist["Close"].iloc[-1])
                name = info.get("shortName") or info.get("longName", "N/A")
                enriched.append({"symbol": sym, "name": name, "price": price})
            except Exception:
                enriched.append({"symbol": t, "name": "N/A", "price": None})
        results["tickers"] = enriched

    except Exception as e:
        results["error"] = str(e)

    return json.dumps(results, indent=2)


@tool("Get Ticker Data")
def get_ticker_data(ticker: str) -> str:
    """
    Fetch detailed market data for a specific ticker (stock or crypto).

    Args:
        ticker: Symbol (e.g., AAPL, MSFT, BTC-USD)

    Returns:
        JSON with price, change %, sector, market cap, and recent performance.
    """
    ticker = ticker.strip().upper()
    sym = ticker if "-" in ticker or "USD" in ticker.upper() else ticker

    try:
        _, info, hist = _yf_with_retry(sym, "1mo")

        price = info.get("regularMarketPrice") or info.get("previousClose")
        if price is None and not hist.empty:
            price = float(hist["Close"].iloc[-1])

        change_pct = None
        if not hist.empty and len(hist) >= 2:
            prev = hist["Close"].iloc[-2]
            curr = hist["Close"].iloc[-1]
            if prev and prev != 0:
                change_pct = round(((curr - prev) / prev) * 100, 2)

        return json.dumps({
            "ticker": sym,
            "name": info.get("shortName") or info.get("longName"),
            "price": price,
            "change_1m_pct": change_pct,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "currency": info.get("currency", "USD"),
        }, indent=2)
    except Exception as e:
        return json.dumps({"ticker": ticker, "error": str(e)})


@tool("Search Market News")
def search_market_news(query: str, max_results: int = 5) -> str:
    """
    Search for recent market news and sentiment.

    Args:
        query: Search terms (e.g., "NVDA earnings", "Bitcoin regulation")
        max_results: Number of results (default 5)

    Returns:
        JSON with news snippets.
    """
    search_query = f"{query} market news 2024"
    try:
        items = _ddg_news_search(search_query, max_results=max_results)
        if items:
            return json.dumps({"query": query, "results": items}, indent=2)
        output = _ddg_text_search(search_query, max_results=max_results)
        return json.dumps({"query": query, "results": output[:1500]}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

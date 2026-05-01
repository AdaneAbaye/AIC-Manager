"""
Research flow orchestration for The Autonomous Investment Committee.

Orchestrates: Scout finds assets -> Analyst reviews -> Risk Manager approves -> Architect allocates.
Includes allocation validation and 80/20 enforcement.
"""

import re
from typing import Any, Generator, TypedDict

from crewai import Crew, Process, Task

from .agents import (
    create_scout_agent,
    create_analyst_agent,
    create_risk_manager_agent,
    create_portfolio_architect_agent,
)
from .config import SCOUT_ASSET_COUNT


def create_research_crew(
    thesis: str,
    monthly_budget: float,
    investor_name: str = "Investor",
    portfolio_target: float = 1_000_000,
    is_dca: bool = True,
) -> Crew:
    """Build the research crew with tasks chained by context."""
    scout = create_scout_agent()
    analyst = create_analyst_agent(investor_name=investor_name, portfolio_target=portfolio_target)
    risk_manager = create_risk_manager_agent(investor_name=investor_name, portfolio_target=portfolio_target)
    architect = create_portfolio_architect_agent(
        monthly_budget=monthly_budget,
        investor_name=investor_name,
        portfolio_target=portfolio_target,
        is_dca=is_dca,
    )

    scout_task = Task(
        description=f"""Using the Market Scanner and search tools, find exactly {SCOUT_ASSET_COUNT} initial candidates
        that match this research thesis: "{thesis}"

        MANDATORY: Must list the top 10 stocks you evaluated before narrowing down to {SCOUT_ASSET_COUNT}. Show your filtering process: which assets you evaluated, why each was included or excluded, and your final {SCOUT_ASSET_COUNT} candidates.
        For each asset, provide: ticker symbol, brief rationale, and why it fits the thesis.
        Output a clear list with ticker symbols (e.g., AAPL, NVDA, BTC-USD).

        MANDATORY DATA FRESHNESS: For **every** stock or asset in your final {SCOUT_ASSET_COUNT} candidates (and for each of the top 10 evaluated when you cite price or quote data), include a line exactly in this form:
        **Last Updated:** Fetched at: YYYY-MM-DD HH:MM EST
        Use the moment you received the data from the tool (or the timestamp returned by the data source if available). If you only have an approximate time, say "approx." after EST. This tells the user whether the data is current.""",
        expected_output=f"A numbered list of the top 10 stocks evaluated, then your final {SCOUT_ASSET_COUNT} candidates; each candidate must include ticker, name, brief rationale, current price or quote where applicable, and a **Last Updated:** Fetched at: ... EST line.",
        agent=scout,
    )

    analyst_task = Task(
        description="""Review the Scout's recommended assets. For each one:
        1. Use Get Ticker Data to fetch financials and performance
        2. Use Search Market News to check recent sentiment
        3. Provide a BUY, HOLD, or AVOID recommendation with clear reasoning
        4. Rank them by conviction (1 = highest)
        For each approved ticker, detail the financial sentiment and recent news you found.""",
        expected_output="A table with each asset, recommendation (BUY/HOLD/AVOID), conviction rank, financial sentiment, recent news, and rationale.",
        agent=analyst,
        context=[scout_task],
    )

    risk_task = Task(
        description="""Evaluate the Analyst's top picks for risk. For each asset:
        1. Assess volatility and downside potential
        2. Consider suitability for the strategy (DCA or Lump Sum)
        3. Approve or reject each asset
        MANDATORY: For each rejected asset, explicitly include: Volatility %, P/E ratio, and debt metrics (e.g., Debt/Equity). Example: 'Rejected NVDA: Volatility 45%, P/E 65, Debt/Equity 0.3—elevated risk.'
        Output APPROVED assets with rationale, AND a separate REJECTED section with ticker and reason (including Volatility %, P/E, debt metrics) for each.""",
        expected_output="APPROVED list with ticker and rationale. REJECTED list with ticker, Volatility %, P/E ratio, debt metrics, and reason for each.",
        agent=risk_manager,
        context=[analyst_task],
    )

    if is_dca:
        alloc_rules = (
            "If only ONE asset is approved: allocate 80% to that asset and 20% as Cash Reserve. "
            "If NO assets approved: 100% Cash Reserve. Total must equal 100%."
        )
    else:
        alloc_rules = (
            "Allocate 100% of the budget across approved assets. No Cash Reserve. "
            "If single asset: 100% to that asset. If multiple: split across them. Total must equal 100%."
        )

    architect_task = Task(
        description=f"""Given the Risk Manager's approved assets, create an allocation plan.

        CRITICAL - BUDGET: **${monthly_budget:,.0f}**. All dollar amounts MUST sum to exactly ${monthly_budget:,.0f}.

        {alloc_rules}

        FULL DEPLOYMENT: You **may** allocate **100%** of the budget across approved tickers (no Cash Reserve) when you judge that all funds can be deployed safely into those names.

        CASH RESERVE ACCOUNTABILITY: If you assign **any** percentage or dollar amount to **Cash Reserve** (or leave any portion undeployed to securities), you **MUST** immediately after your allocation table include a Markdown section titled **## Cash Reserve rationale** with a **bullet list** (at least one substantive bullet). Each bullet must clearly explain why you did not deploy the remaining funds into sufficiently safe opportunities (e.g., insufficient approved names, valuation or liquidity concerns, concentration limits, macro or single-name risk, or strategy fit). Generic one-line excuses are not acceptable.

        MANDATORY: In your summary, state that the final allocation is based only on assets that passed the Risk Manager's audit.
        MANDATORY: Do NOT include the investor's name or portfolio target in your output. Use them for calculations only.

        ARCHITECT VALIDATION: Verify that your final allocation table matches the EXACT list of approved assets from the Risk Manager. Every approved ticker must appear in your table; do not add or remove any.

        STRICT ALLOCATION: You MUST strictly allocate the budget ONLY to the tickers that were explicitly approved by the Risk Manager in the previous step. Do NOT add new tickers that weren't in the approved list.

        100% ALLOCATION: The Allocation % column MUST sum to exactly 100%. If money is left over due to rejected assets, assign it to Cash Reserve (and provide the Cash Reserve rationale section above).

        CRITICAL: Ensure the final allocation table strictly matches the approved assets from the Risk Manager. The total allocation MUST equal 100%. If any budget is unallocated, assign it to 'Cash Reserve'.

        OUTPUT FORMAT - CRITICAL: You MUST output a Markdown table with exactly these columns:
        | Ticker | Allocation % | $ Amount | Rationale |
        Use pipe characters (|) to separate columns. Example: | AAPL | 40% | $200 | Strong fundamentals |
        Output: Ticker | % of budget | $ amount | Rationale
        Include a brief summary.""",
        expected_output=f"Markdown table with pipe-separated columns: | Ticker | Allocation % | Dollar Amount | Rationale |. Total = ${monthly_budget:,.0f}. {alloc_rules}",
        agent=architect,
        context=[risk_task],
    )

    return Crew(
        agents=[scout, analyst, risk_manager, architect],
        tasks=[scout_task, analyst_task, risk_task, architect_task],
        process=Process.sequential,
        verbose=False,
    )


# Markdown table row: | ticker | pct | $amount | (pct must be 0-100, in allocation context)
# Ticker col: letters, symbols, spaces; NOT numbers-only (excludes dates like 2024)
_TABLE_ROW_RE = re.compile(
    r"^\s*\|?\s*([A-Za-z\u0590-\u05FF\s\-\.]+?)\s*\|\s*(\d+(?:\.\d+)?)\s*%?\s*\|\s*\$\s*(\d+(?:\.\d+)?)\s*(?:\s*\|.*)?$",
    re.IGNORECASE,
)
# Fallback: ticker (starts with letter) followed by pct% and $amt
_FALLBACK_ROW_RE = re.compile(
    r"^\s*([A-Za-z\u0590-\u05FF][A-Za-z\u0590-\u05FF\s\-\.]*?)\s*[:\.]?\s*(\d+(?:\.\d+)?)\s*%\s*[\(\$]?\s*\$?\s*(\d+(?:\.\d+)?)\s*\)?",
    re.IGNORECASE,
)
# Skip: header, separator, total, or lines that are just numbers/dates
_HEADER_OR_SEP_RE = re.compile(
    r"^\s*\|?\s*[-:\s|]+$|^\s*\|?\s*(Ticker|Allocation|Rationale|Amount|%|תאריך|סה[\u05B0-\u05BF]?כ)\s*\|",
    re.IGNORECASE,
)
_TOTAL_ROW_RE = re.compile(r"\b(total|סה[\u05B0-\u05BF]?כ|sum)\b", re.IGNORECASE)
# Lines that mention budget as standalone (e.g. "Budget: $300" or "תקציב: $300") - skip
_BUDGET_ONLY_RE = re.compile(r"^\s*(budget|תקציב|monthly)\s*[:=]?\s*\$\d+", re.IGNORECASE)

# Table row with rationale: | ticker | pct% | $amt | rationale |
_TABLE_ROW_WITH_RATIONALE_RE = re.compile(
    r"^\s*\|?\s*([A-Za-z\u0590-\u05FF\s\-\.]+?)\s*\|\s*(\d+(?:\.\d+)?)\s*%?\s*\|\s*\$?\s*([\d,]+(?:\.[\d]+)?)\s*(?:\s*\|\s*([^|]*))?\s*$",
    re.IGNORECASE,
)
# Flexible: ticker | pct | amount (amount may lack $)
_TABLE_ROW_FLEX_RE = re.compile(
    r"^\s*\|?\s*([A-Za-z\u0590-\u05FF\s\-\.]+?)\s*\|\s*(\d+(?:\.\d+)?)\s*%?\s*\|\s*([\d,]+(?:\.[\d]+)?)\s*(?:\s*\|\s*([^|]*))?\s*$",
    re.IGNORECASE,
)
# Inline: "AAPL 40% $200" or "AAPL: 40% ($200)"
_INLINE_ROW_RE = re.compile(
    r"^\s*([A-Za-z\u0590-\u05FF][A-Za-z\u0590-\u05FF\s\-\.]*?)\s*[:\s]+\s*(\d+(?:\.\d+)?)\s*%\s*(?:\(\s*)?\$?\s*([\d,]+(?:\.[\d]+)?)\s*\)?\s*(?:[:\-]\s*(.*))?$",
    re.IGNORECASE,
)
# Rejected: multiple patterns for different model formatting
_REJECTED_PATTERN_RE = re.compile(
    r"(?:rejected|reject)\s+([A-Z]{2,5}(?:-[A-Z]{2,4})?)\s*(?:due to|because|:|\-)\s*(.+?)(?=\n|$)",
    re.IGNORECASE,
)
_REJECTED_LINE_RE = re.compile(
    r"^\s*[-*•]?\s*([A-Z]{2,5}(?:-[A-Z]{2,4})?)\s*[:\-–—]\s*(.+?)\s*$",
    re.IGNORECASE,
)
# Rejected in sentence: "NVDA was rejected due to..."
_REJECTED_SENTENCE_RE = re.compile(
    r"([A-Z]{2,5}(?:-[A-Z]{2,4})?)\s+(?:was\s+)?rejected\s+(?:due to|because|for)\s+(.+?)(?=[.;\n]|$)",
    re.IGNORECASE,
)

_TICKER_HEADER_WORDS = frozenset(
    {
        "ticker",
        "symbol",
        "asset",
        "name",
        "stock",
        "allocation",
        "alloc",
        "%",
        "pct",
        "percent",
        "amount",
        "$",
        "dollar",
        "rationale",
        "reason",
        "notes",
        "comment",
    }
)


def _strip_cell_markdown(cell: str) -> str:
    """Remove common Markdown wrappers (**bold**, *italic*, __underline__) from a table cell.

    Use lambda replacements so values like **$600** are not corrupted (r'\\1' + '$600' confuses re.sub).
    """
    s = (cell or "").strip()
    for _ in range(6):
        prev = s
        s = re.sub(r"\*\*([^*]+)\*\*", lambda m: m.group(1), s)
        s = re.sub(r"\*([^*]+)\*", lambda m: m.group(1), s)
        s = re.sub(r"__([^_]+)__", lambda m: m.group(1), s)
        s = re.sub(r"_([^_]+)_", lambda m: m.group(1), s)
        s = s.strip()
        if s == prev:
            break
    return s.strip()


def _is_md_table_separator_row(line: str) -> bool:
    """True for Markdown separator rows like | --- | :--- | or |-----|-----|."""
    inner = line.strip().strip("|")
    if not inner:
        return True
    parts = [p.strip() for p in inner.split("|")]
    for p in parts:
        if not p:
            continue
        if re.sub(r"[\s\-:]+", "", p):
            return False
    return True


def _split_md_table_cells(line: str) -> list[str]:
    """Split a table row on pipes; trim leading/trailing empty cells from outer pipes."""
    s = line.strip()
    parts = [p.strip() for p in s.split("|")]
    while parts and parts[0] == "":
        parts.pop(0)
    while parts and parts[-1] == "":
        parts.pop()
    return [_strip_cell_markdown(p) for p in parts]


def _parse_pct_cell(cell: str) -> float | None:
    s = _strip_cell_markdown(cell)
    m = re.search(r"(\d+(?:\.\d+)?)\s*%?", s)
    if not m:
        return None
    return float(m.group(1))


def _parse_amount_cell(cell: str) -> float | None:
    s = _strip_cell_markdown(cell)
    compact = re.sub(r"\s+", "", s)
    m = re.search(r"\$?\s*([\d,]+(?:\.\d+)?)", compact)
    if not m:
        m = re.search(r"^([\d,]+(?:\.\d+)?)$", compact)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def _normalize_ticker_from_cell(cell: str) -> str:
    raw = _strip_cell_markdown(cell)
    if not raw:
        return ""
    low = raw.lower()
    if ("cash" in low and "reserve" in low) or re.search(r"עתודת\s*מזומן|מזומן\s*עתוד", raw):
        return raw.strip() if any("\u0590" <= c <= "\u05FF" for c in raw) else "Cash Reserve"
    tokens = raw.split()
    if not tokens:
        return raw
    return tokens[0].strip(".,;:")


def _parse_allocation_from_pipe_cells(line: str, seen_tickers: set[str]) -> dict | None:
    """
    Flexible Markdown table row: handles extra spaces, pipes, **bold** in cells.
    Expects ticker | pct | $amount | optional rationale...
    """
    if line.count("|") < 2:
        return None
    if _is_md_table_separator_row(line):
        return None
    if _HEADER_OR_SEP_RE.match(line):
        return None

    cells = _split_md_table_cells(line)
    if len(cells) < 3:
        return None

    ticker = _normalize_ticker_from_cell(cells[0])
    if not ticker or ticker.isdigit():
        return None
    tkey_check = re.sub(r"\s+", "", ticker.lower())
    if tkey_check in _TICKER_HEADER_WORDS or ticker.lower() in _TICKER_HEADER_WORDS:
        return None

    pct = _parse_pct_cell(cells[1])
    if pct is None or pct < 0 or pct > 100.0001:
        return None

    amt = _parse_amount_cell(cells[2])
    if amt is None or amt < 0:
        return None

    rationale = "—"
    if len(cells) > 3:
        rationale = " | ".join(c for c in cells[3:] if c)

    ticker_key = re.sub(r"\s+", "", ticker.lower())
    if "cash" in ticker_key and "reserve" in ticker_key:
        ticker_key = "cashreserve"
    if ticker_key in seen_tickers:
        return None
    seen_tickers.add(ticker_key)

    return {"ticker": ticker, "pct": pct, "amount": amt, "rationale": rationale or "—"}


def _gather_candidate_table_lines(text: str) -> list[str]:
    """All lines that look like pipe tables (in order, deduped)."""
    ordered: list[str] = []
    seen: set[str] = set()

    def add(ln: str) -> None:
        if ln not in seen:
            seen.add(ln)
            ordered.append(ln)

    for line in text.split("\n"):
        ls = line.strip()
        if ls.count("|") >= 2:
            add(ls)
    for match in _TABLE_BLOCK_RE.finditer(text):
        for line in match.group(1).split("\n"):
            ls = line.strip()
            if ls and "|" in ls:
                add(ls)
    return ordered


def _try_parse_allocation_line(line_stripped: str, seen_tickers: set[str]) -> dict | None:
    """Try to parse a single line as an allocation row. Returns dict or None."""
    pipe_row = _parse_allocation_from_pipe_cells(line_stripped, seen_tickers)
    if pipe_row is not None:
        return pipe_row

    for pattern in (_TABLE_ROW_WITH_RATIONALE_RE, _TABLE_ROW_FLEX_RE):
        m = pattern.match(line_stripped)
        if m and not _HEADER_OR_SEP_RE.match(line_stripped) and not _TOTAL_ROW_RE.search(line_stripped):
            ticker = _normalize_ticker_from_cell(m.group(1))
            pct = float(m.group(2))
            amt_val = _strip_cell_markdown(m.group(3)).replace(",", "")
            amt = float(amt_val) if amt_val else 0.0
            rationale = (
                _strip_cell_markdown(m.group(4) or "").strip()
                if m.lastindex >= 4 and m.group(4) is not None
                else ""
            )
            if pct < 0 or pct > 100.0001 or not ticker or ticker.isdigit():
                continue
            ticker_key = re.sub(r"\s+", "", ticker.lower())
            if "cash" in ticker_key and "reserve" in ticker_key:
                ticker_key = "cashreserve"
            if ticker_key in seen_tickers:
                continue
            seen_tickers.add(ticker_key)
            return {"ticker": ticker, "pct": pct, "amount": amt, "rationale": (rationale or "—")}
    m = _INLINE_ROW_RE.match(line_stripped)
    if m and not _TOTAL_ROW_RE.search(line_stripped):
        ticker = _normalize_ticker_from_cell(m.group(1))
        pct = float(m.group(2))
        amt = float(_strip_cell_markdown(m.group(3)).replace(",", ""))
        rationale = (
            _strip_cell_markdown(m.group(4) or "").strip() if m.lastindex >= 4 and m.group(4) else "—"
        )
        if 0 <= pct <= 100.0001 and ticker and not ticker.isdigit():
            ticker_key = re.sub(r"\s+", "", ticker.lower())
            if "cash" in ticker_key and "reserve" in ticker_key:
                ticker_key = "cashreserve"
            if ticker_key not in seen_tickers:
                seen_tickers.add(ticker_key)
                return {"ticker": ticker, "pct": pct, "amount": amt, "rationale": rationale or "—"}
    return None


# Non-greedy pattern to find markdown table block (lines with |...|)
_TABLE_BLOCK_RE = re.compile(
    r"(?:^|\n)((?:\s*\|[^|\n]+\|\s*\n)+)",
    re.MULTILINE,
)


def _clean_text_for_parsing(text: str) -> str:
    """Clean string before parsing: strip, normalize whitespace, remove BOM."""
    if not text:
        return ""
    t = text.strip()
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"\n{3,}", "\n\n", t)
    if t.startswith("\ufeff"):
        t = t[1:]
    return t


def parse_recommendations_for_ui(text: str) -> dict:
    """
    Parse Architect output into structured data for dashboard UI.
    Robust: cleans text, finds table regardless of surrounding content, handles varied REJECTED formatting.
    Returns: {
        "allocations": [{"ticker", "pct", "amount", "rationale"}],
        "rejected": [{"ticker", "reason"}],
        "raw_text": str (fallback when parsing fails)
    }
    """
    result = {"allocations": [], "rejected": [], "raw_text": text}
    try:
        text = _clean_text_for_parsing(text or "")
    except Exception:
        return result
    if not text:
        return result

    seen_tickers: set[str] = set()
    in_rejected = False
    seen_rejected: set[str] = set()

    table_lines = _gather_candidate_table_lines(text)
    # Prefer all pipe-shaped lines (flexible); fall back to full document
    lines_to_parse = table_lines if table_lines else text.split("\n")

    # First pass: scan entire text for REJECTED mentions (flexible)
    for rej_match in _REJECTED_PATTERN_RE.finditer(text):
        t = rej_match.group(1).strip()
        r = rej_match.group(2).strip()[:200]
        if t and t not in seen_rejected:
            seen_rejected.add(t)
            result["rejected"].append({"ticker": t, "reason": r})
    for rej_match in _REJECTED_SENTENCE_RE.finditer(text):
        t = rej_match.group(1).strip()
        r = rej_match.group(2).strip()[:200]
        if t and t not in seen_rejected:
            seen_rejected.add(t)
            result["rejected"].append({"ticker": t, "reason": r})

    for line in lines_to_parse:
        line_stripped = line.strip() if isinstance(line, str) else ""
        if not line_stripped:
            continue

        # Detect REJECTED section header (variants)
        if re.search(r"^\s*(REJECTED|Rejected|דחוי|נדחו)", line_stripped, re.IGNORECASE):
            in_rejected = True
            continue
        if in_rejected and re.search(r"^\s*(APPROVED|Approved|מאושר|Summary|סיכום|Allocation|---)", line_stripped, re.IGNORECASE):
            in_rejected = False

        # Parse allocation rows (table or inline)
        alloc = _try_parse_allocation_line(line_stripped, seen_tickers)
        if alloc:
            result["allocations"].append(alloc)
            continue

        # Parse rejected list: "- NVDA: high volatility" (only if in section or not yet found)
        if in_rejected or not result["rejected"]:
            rej_line = _REJECTED_LINE_RE.match(line_stripped)
            if rej_line and len(rej_line.group(1)) >= 2:
                t = rej_line.group(1).strip()
                if t not in seen_rejected:
                    seen_rejected.add(t)
                    result["rejected"].append({"ticker": t, "reason": rej_line.group(2).strip()[:200]})

    # If no allocations yet, retry with full text line-by-line (inline / odd formatting)
    if not result["allocations"]:
        for line in text.split("\n"):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            alloc = _try_parse_allocation_line(line_stripped, seen_tickers)
            if alloc:
                result["allocations"].append(alloc)

    # Parse rejected list format from full text (in case table block missed it)
    if not result["rejected"] or not table_lines:
        in_rej = False
        for line in text.split("\n"):
            ls = line.strip()
            if not ls:
                continue
            if re.search(r"^\s*(REJECTED|Rejected|דחוי|נדחו)", ls, re.IGNORECASE):
                in_rej = True
                continue
            if in_rej and re.search(r"^\s*(APPROVED|Approved|מאושר|Summary|Allocation|---)", ls, re.IGNORECASE):
                in_rej = False
            if in_rej:
                rej_m = _REJECTED_LINE_RE.match(ls)
                if rej_m and len(rej_m.group(1)) >= 2:
                    t = rej_m.group(1).strip()
                    if t not in seen_rejected:
                        seen_rejected.add(t)
                        result["rejected"].append({"ticker": t, "reason": rej_m.group(2).strip()[:200]})

    return result


def _parse_allocations(text: str) -> list[tuple[str, float, float]]:
    """
    Extract (ticker, pct, amount) ONLY from allocation table rows.
    - Only percentages associated with tickers (not dates, budget totals, or summary text)
    - Ignores lines with budget numbers like $300 when not in a table row
    - Cash Reserve counted only once (deduplicated by ticker_key)
    """
    rows: list[tuple[str, float, float]] = []
    seen_tickers: set[str] = set()

    for line in text.split("\n"):
        line = line.strip()
        if not line or _HEADER_OR_SEP_RE.match(line) or _TOTAL_ROW_RE.search(line):
            continue
        if _BUDGET_ONLY_RE.match(line):
            continue

        m = _TABLE_ROW_RE.match(line)
        if not m:
            m = _FALLBACK_ROW_RE.match(line)
        if not m:
            continue

        ticker = m.group(1).strip()
        pct = float(m.group(2))
        amt = float(m.group(3))

        if pct < 0 or pct > 100:
            continue
        if not ticker or ticker.isdigit():
            continue

        ticker_key = re.sub(r"\s+", "", ticker.lower())
        if "cash" in ticker_key and "reserve" in ticker_key:
            ticker_key = "cashreserve"
        if ticker_key in seen_tickers:
            continue
        seen_tickers.add(ticker_key)

        rows.append((ticker, pct, amt))

    return rows


def _validate_and_enforce_allocation(
    output: str, monthly_budget: float, thesis: str = "", is_dca: bool = True
) -> str:
    """
    Validate Architect output: total allocation must equal 100% of budget.
    Enforce 80/20 rule only when is_dca (DCA mode). Lump Sum: no Cash Reserve required.
    """
    rows = _parse_allocations(output)
    if not rows:
        return output

    total_pct = sum(r[1] for r in rows)
    total_amt = sum(r[2] for r in rows)
    tolerance = 1.0
    hebrew = _has_hebrew(thesis)

    non_cash = [
        r for r in rows
        if "cash" not in r[0].lower() and "reserve" not in r[0].lower()
    ]
    cash_only = len(non_cash) == 0 and len(rows) == 1
    single_asset = len(non_cash) == 1

    if cash_only:
        if hebrew:
            cash_msg = "\n\n**כל התקציב הועבר למזומן עקב חוסר בנכסים מאושרים.**"
            return output.rstrip() + cash_msg
        return output

    validation_note = []
    if abs(total_pct - 100) > tolerance:
        if hebrew:
            validation_note.append(
                f"⚠️ **אימות:** סך ההקצאה {total_pct:.1f}% (צפוי 100%). "
                "ודא שהסך הכולל שווה בדיוק 100%."
            )
        else:
            validation_note.append(
                f"⚠️ **Validation:** Allocation sums to {total_pct:.1f}% (expected 100%). "
                "Please ensure total equals exactly 100%."
            )
    if abs(total_amt - monthly_budget) > 1:
        if hebrew:
            validation_note.append(
                f"⚠️ **אימות:** סך דולרים ${total_amt:.0f} לא תואם לתקציב ${monthly_budget:,.0f}. "
                "ההקצאות חייבות לסכם לתקציב החודשי."
            )
        else:
            validation_note.append(
                f"⚠️ **Validation:** Dollar total ${total_amt:.0f} does not match budget ${monthly_budget:,.0f}. "
                "Allocations must sum to the monthly budget."
            )
    # 80/20 rule only applies in DCA mode
    if is_dca and single_asset and len(rows) >= 2:
        asset_row = non_cash[0]
        cash_rows = [r for r in rows if r[0] != asset_row[0]]
        cash_pct = sum(r[1] for r in cash_rows)
        if abs(asset_row[1] - 80) > 5 or abs(cash_pct - 20) > 5:
            if hebrew:
                validation_note.append(
                    "⚠️ **כלל 80/20:** הקצאה לנכס בודד צריכה להיות 80% לנכס, 20% למזומן. "
                    f"נוכחי: {asset_row[1]:.0f}% נכס, {cash_pct:.0f}% reserve."
                )
            else:
                validation_note.append(
                    "⚠️ **80/20 Rule (DCA):** Single-asset allocation should be 80% to the asset, 20% Cash Reserve. "
                    f"Current: {asset_row[1]:.0f}% asset, {cash_pct:.0f}% reserve."
                )

    if validation_note:
        return output + "\n\n" + "\n".join(validation_note)
    return output


def _has_hebrew(text: str) -> bool:
    """Detect if text contains Hebrew characters (Unicode \u0590-\u05FF)."""
    if not text:
        return False
    return bool(re.search(r"[\u0590-\u05FF]", text))


def _append_goal_summary(output: str, thesis: str = "") -> str:
    """Append legal disclaimer to final recommendations."""
    if _has_hebrew(thesis):
        footer = """

---
**The Autonomous Investment Committee** | *לא ייעוץ השקעות. למחקר וחינוך בלבד.*
"""
    else:
        footer = """

---
**The Autonomous Investment Committee** | *Not Financial Advice. For research and education only.*
"""
    return output.rstrip() + footer


class ResearchSessionError(Exception):
    """User-friendly error for research session failures."""

    pass


class ApprovedAssetDict(TypedDict):
    ticker: str
    pct: float
    amount: float
    rationale: str


class RejectedAssetDict(TypedDict):
    ticker: str
    reason: str


class AgentLogEntryDict(TypedDict):
    agent: str
    lines: list[str]


class ResearchSessionResultDict(TypedDict):
    """Structured result for API and UI (JSON-serializable)."""

    approved_assets: list[ApprovedAssetDict]
    rejected_assets: list[RejectedAssetDict]
    agent_logs: list[AgentLogEntryDict]
    raw_report: str


def _sanitize_error(msg: str) -> str:
    """Redact API keys and secrets from error messages before display."""
    from .security import redact_secrets

    return redact_secrets(msg) if msg else msg


def _format_llm_error(exc: Exception) -> str:
    """Convert LLM/API errors to user-friendly messages. Never exposes API keys."""
    raw = _sanitize_error(str(exc))
    msg = raw.lower()
    if "404" in msg or "not found" in msg:
        return (
            "**Model not found (404).** Try `claude-3-haiku-20240307` or `claude-haiku-4-5-20251001` "
            "in config.py (works with low balance)."
        )
    if "401" in msg or "unauthorized" in msg or "invalid api key" in msg:
        return (
            "**Invalid API key.** Check that ANTHROPIC_API_KEY in your `.env` file "
            "is correct and has not expired. Get a key at https://console.anthropic.com/"
        )
    if "429" in msg or "rate limit" in msg:
        return "**Rate limit exceeded.** Please wait a moment and try again."
    if "anthropic" in msg or "api" in msg or "llm" in msg:
        return f"**LLM error:** {raw}"
    return f"**Research failed:** {raw}"


_AGENT_NAMES = ["Scout", "Analyst", "Risk Manager", "Architect"]


def _extract_lines(
    raw: str,
    max_lines: int | None = None,
    max_chars_per_line: int | None = None,
) -> list[str]:
    """Extract lines from raw output for log display. No line limit by default; no truncation when max_chars_per_line is None."""
    if not raw or not raw.strip():
        return ["Completed."]
    lines = []
    for line in raw.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("|") and "---" in line:
            continue
        if max_chars_per_line is not None and len(line) > max_chars_per_line:
            line = line[: max_chars_per_line - 3] + "..."
        lines.append(line)
        if max_lines is not None and len(lines) >= max_lines:
            break
    return lines[:max_lines] if max_lines else lines if lines else ["Completed."]


def _build_agent_logs(
    result,
    thesis: str,
    *,
    max_detail_lines: int | None = None,
) -> list[dict[str, Any]]:
    """Build agent logs for UI/API. When max_detail_lines is set (e.g. 20), caps detail per agent (~15–20 lines)."""
    logs: list[dict[str, Any]] = []
    if not hasattr(result, "tasks_output") or not result.tasks_output:
        return logs
    thesis_short = (thesis[:40] + "...") if len(thesis) > 40 else thesis if thesis else "thesis"
    action_templates = [
        f"Scanning markets for: {thesis_short}",
        "Analyzing Scout's picks for financials and sentiment.",
        "Evaluating volatility and downside risk.",
        "Allocating budget across approved assets.",
    ]
    for i, task_out in enumerate(result.tasks_output):
        raw = getattr(task_out, "raw", "") or str(task_out)
        agent = _AGENT_NAMES[i] if i < len(_AGENT_NAMES) else f"Agent {i + 1}"
        action = action_templates[i] if i < len(action_templates) else "Processing."
        extracted = _extract_lines(
            raw,
            max_lines=None if max_detail_lines is None else max(1, max_detail_lines - 1),
            max_chars_per_line=None,
        )
        lines = [action, f"Outcome: {extracted[0]}"]
        for j in range(1, len(extracted)):
            lines.append(extracted[j])
        if max_detail_lines is not None:
            lines = lines[:max_detail_lines]
        logs.append({"agent": agent, "lines": lines})
    return logs


def run_research_session(
    thesis: str,
    monthly_budget: float,
    investor_name: str = "Investor",
    portfolio_target: float = 1_000_000,
    is_dca: bool = True,
    *,
    agent_log_max_lines: int | None = None,
) -> ResearchSessionResultDict:
    """
    Run a full research session. Results only when crew.kickoff() finishes.

    Returns:
        JSON-serializable dict: approved_assets, rejected_assets, agent_logs, raw_report.
        Use agent_log_max_lines=20 for API-style capped logs; None keeps full detail (Streamlit).

    Raises:
        ResearchSessionError: On LLM/API errors.
    """
    from .config import ANTHROPIC_API_KEY

    if not ANTHROPIC_API_KEY:
        raise ResearchSessionError(
            "**ANTHROPIC_API_KEY** not set. Add it to your `.env` file and restart the app."
        )

    crew = create_research_crew(
        thesis=thesis,
        monthly_budget=monthly_budget,
        investor_name=investor_name,
        portfolio_target=portfolio_target,
        is_dca=is_dca,
    )
    try:
        result = crew.kickoff(inputs={
            "monthly_budget": monthly_budget,
            "thesis": thesis,
            "investor_name": investor_name,
            "portfolio_target": portfolio_target,
            "is_dca": is_dca,
        })
    except Exception as e:
        raise ResearchSessionError(_format_llm_error(e)) from e

    agent_logs = _build_agent_logs(result, thesis, max_detail_lines=agent_log_max_lines)

    if hasattr(result, "raw") and result.raw:
        output = str(result.raw)
    elif hasattr(result, "output") and result.output:
        output = str(result.output)
    else:
        output = str(result)
    output = _validate_and_enforce_allocation(output, monthly_budget, thesis, is_dca=is_dca)
    output = _append_goal_summary(output, thesis)

    parsed = parse_recommendations_for_ui(output)
    approved: list[ApprovedAssetDict] = [
        {
            "ticker": a["ticker"],
            "pct": float(a["pct"]),
            "amount": float(a["amount"]),
            "rationale": a["rationale"],
        }
        for a in parsed.get("allocations", [])
    ]
    rejected: list[RejectedAssetDict] = [
        {"ticker": r["ticker"], "reason": r["reason"]}
        for r in parsed.get("rejected", [])
    ]

    return {
        "approved_assets": approved,
        "rejected_assets": rejected,
        "agent_logs": agent_logs,
        "raw_report": output,
    }


def run_research_session_streaming(
    thesis: str,
    monthly_budget: float,
    investor_name: str = "Investor",
    portfolio_target: float = 1_000_000,
    is_dca: bool = True,
) -> Generator[tuple[str, str], None, None]:
    """Run research session and yield (agent_name, output) as each task completes."""
    from .config import ANTHROPIC_API_KEY

    if not ANTHROPIC_API_KEY:
        raise ResearchSessionError(
            "**ANTHROPIC_API_KEY** not set. Add it to your `.env` file and restart the app."
        )
    crew = create_research_crew(
        thesis, monthly_budget,
        investor_name=investor_name,
        portfolio_target=portfolio_target,
        is_dca=is_dca,
    )
    try:
        result = crew.kickoff(inputs={
            "monthly_budget": monthly_budget,
            "thesis": thesis,
            "investor_name": investor_name,
            "portfolio_target": portfolio_target,
            "is_dca": is_dca,
        })
    except Exception as e:
        raise ResearchSessionError(_format_llm_error(e)) from e
    output = str(result.raw) if hasattr(result, "raw") else str(result)
    output = _validate_and_enforce_allocation(output, monthly_budget, thesis, is_dca=is_dca)
    output = _append_goal_summary(output, thesis)
    yield ("Committee", output)

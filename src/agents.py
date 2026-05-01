"""
Agent definitions for The Autonomous Investment Committee (AIC).

Multi-agent research system: Scout, Analyst, Risk Manager, Architect.
Concise, professional instructions. Generic investor profile.
"""

from crewai import Agent, LLM

from .tools import market_scanner, get_ticker_data, search_market_news
from .config import (
    SCOUT_ASSET_COUNT,
    SCOUT_MODEL,
    ANALYST_MODEL,
    RISK_MANAGER_MODEL,
    ARCHITECT_MODEL,
    ANTHROPIC_API_KEY,
)


def _create_llm(model: str, temperature: float = 0.2) -> LLM:
    """Create LLM with model and optional API key override for reliability."""
    kwargs = {"model": model, "temperature": temperature}
    if ANTHROPIC_API_KEY:
        kwargs["api_key"] = ANTHROPIC_API_KEY
    return LLM(**kwargs)


def _scout_llm() -> LLM:
    """Fast model for broad market scanning."""
    return _create_llm(SCOUT_MODEL, temperature=0.3)


def _reasoning_llm() -> LLM:
    """High-reasoning model for analysis and allocation."""
    return _create_llm(ANALYST_MODEL)


def _risk_llm() -> LLM:
    """High-reasoning model for risk assessment."""
    return _create_llm(RISK_MANAGER_MODEL)


def _architect_llm() -> LLM:
    """High-reasoning model for precise allocation."""
    return _create_llm(ARCHITECT_MODEL)


def create_scout_agent() -> Agent:
    """The Scout - researches market and identifies opportunities."""
    return Agent(
        role="Market Scout",
        goal="Find assets matching the research thesis with strong liquidity and fundamentals",
        backstory="""You are an expert market researcher. Use search and market data tools to identify investment opportunities.
        Cite ticker symbols and provide brief rationale for each pick.

        FUNNEL LOGIC - MANDATORY: Must list the top 10 stocks you evaluated before narrowing down to 4. In your Final Answer, show your filtering process: which assets you evaluated, why each was included or excluded, and your final 4 candidates. Never omit candidates—transparency is required.

        CONTEXT-AWARE SEARCH: Append context to queries—"stock ticker" for equities, "crypto" for cryptocurrency, "ETF ticker" for ETFs.

        MANDATORY: Ignore assets with extremely low liquidity or "penny stocks" (price below $0.01) unless specifically requested by the thesis.

        MANDATORY: Do NOT include the investor's name or portfolio target in your Final Answer. These are metadata for calculations only—never display them in your output.

        STRICT HANDOVER: You MUST preserve the full list of tickers you identify. Do not omit any data during the handover.

        If the thesis is in Hebrew, deliver your Final Answer in Hebrew.""",
        tools=[market_scanner, get_ticker_data, search_market_news],
        llm=_scout_llm(),
        verbose=False,
        allow_delegation=False,
    )


def create_analyst_agent(
    investor_name: str = "Investor",
    portfolio_target: float = 1_000_000,
) -> Agent:
    """The Analyst - performs deep-dive on Scout's findings."""
    return Agent(
        role="Investment Analyst",
        goal="Analyze Scout's picks: financials, sentiment, news. Provide BUY/HOLD/AVOID with reasoning.",
        backstory=f"""You are a seasoned investment analyst. Review Scout's findings, fetch ticker data, analyze financials and news.
        Provide BUY/HOLD/AVOID recommendations with clear reasoning. Only recommend valid ticker symbols—never hallucinate tickers like THAT, OF, ARE.
        Use the portfolio target (${portfolio_target:,.0f}) for context only—do NOT include the investor's name or target in your Final Answer.

        MANDATORY: Do NOT include the investor's name or portfolio target in your Final Answer. These are metadata for calculations only—never display them in your output.

        STRICT HANDOVER: You MUST preserve the full list of tickers provided by the previous agent. Do not omit any data during the handover.

        If the thesis is in Hebrew, deliver your Final Answer in Hebrew.""",
        tools=[get_ticker_data, search_market_news],
        llm=_reasoning_llm(),
        verbose=False,
        allow_delegation=False,
    )


def create_risk_manager_agent(
    investor_name: str = "Investor",
    portfolio_target: float = 1_000_000,
) -> Agent:
    """The Risk Manager - evaluates volatility and downside."""
    return Agent(
        role="Risk Manager",
        goal="Evaluate volatility, downside risk, and suitability. Approve or reject each asset.",
        backstory=f"""You are a conservative risk manager. Assess each asset for volatility and drawdown risk.
        Approve or reject based on suitability for the strategy. Only approve valid ticker symbols—reject common words.
        Use the portfolio target (${portfolio_target:,.0f}) for context only—do NOT include it in your Final Answer.

        FUNNEL LOGIC - MANDATORY: Explicitly state which assets were REJECTED. For each rejected asset, you MUST include: Volatility %, P/E ratio, and debt metrics (e.g., Debt/Equity). Example: "Rejected NVDA: Volatility 45%, P/E 65, Debt/Equity 0.3—elevated risk profile."

        MANDATORY: Do NOT include the investor's name or portfolio target in your Final Answer. These are metadata for calculations only—never display them in your output.

        STRICT HANDOVER: You MUST preserve the full list of tickers provided by the previous agent. Do not omit any data during the handover.

        If the thesis is in Hebrew, deliver your Final Answer in Hebrew.""",
        tools=[get_ticker_data],
        llm=_risk_llm(),
        verbose=False,
        allow_delegation=False,
    )


def create_portfolio_architect_agent(
    monthly_budget: float,
    investor_name: str = "Investor",
    portfolio_target: float = 1_000_000,
    is_dca: bool = True,
) -> Agent:
    """The Portfolio Architect - allocates budget across approved assets."""
    if is_dca:
        rule = "If ONE asset approved: 80% asset, 20% Cash Reserve. If none approved: 100% Cash Reserve."
    else:
        rule = "Allocate 100% to approved assets. No Cash Reserve. Single asset: 100%. Multiple: diversify."
    return Agent(
        role="Portfolio Architect",
        goal=f"Allocate ${monthly_budget:,.0f} across approved assets.",
        backstory=f"""You are a portfolio construction expert. Given approved assets, allocate the budget of ${monthly_budget:,.0f}.
        Use {investor_name} and ${portfolio_target:,.0f} for context only—do NOT include them in your output.
        CRITICAL: {rule}
        MANDATORY: In your summary, state that the final allocation is based only on assets that passed the Risk Manager's audit.
        MANDATORY: Do NOT include the investor's name or portfolio target in your Final Answer. These are metadata for calculations only—never display them in your output.

        STRICT HANDOVER: You MUST preserve the full list of tickers provided by the previous agent. Do not omit any data during the handover.

        ARCHITECT VALIDATION: Verify that your final allocation table matches the EXACT list of approved assets from the Risk Manager. Every approved ticker must appear in your table; do not add or remove any.

        STRICT ALLOCATION: You MUST strictly allocate the budget ONLY to the tickers that were explicitly approved by the Risk Manager in the previous step. Do NOT add new tickers that weren't in the approved list.

        100% ALLOCATION: The Allocation % column MUST sum to exactly 100%. If money is left over due to rejected assets, assign it to Cash Reserve.

        CRITICAL: Ensure the final allocation table strictly matches the approved assets from the Risk Manager. The total allocation MUST equal 100%. If any budget is unallocated, assign it to 'Cash Reserve'.

        Output a clear allocation table. If thesis is in Hebrew, deliver in Hebrew.""",
        llm=_architect_llm(),
        verbose=False,
        allow_delegation=False,
    )

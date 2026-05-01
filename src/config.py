"""
Configuration for The Autonomous Investment Committee (AIC).

Generic research-based system. No hardcoded assets.
Research thesis and parameters are user-configurable.
"""

from pathlib import Path
import os

from dotenv import load_dotenv

# Load .env from project root (one level above src/)
_REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_REPO_ROOT / ".env")

# -----------------------------------------------------------------------------
# API Keys (must be after load_dotenv; .strip() prevents whitespace issues)
# -----------------------------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Kept for other tools if needed
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()  # Required for Claude agents
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# -----------------------------------------------------------------------------
# Research & Portfolio Goals
# -----------------------------------------------------------------------------

# Target portfolio value (USD) - Long-term goal
TARGET_PORTFOLIO_VALUE = 1_000_000

# Monthly DCA budget (USD) for allocation
DEFAULT_MONTHLY_BUDGET = 200

# Thesis presets (4 professional options + Custom)
THESIS_PRESETS = [
    "Stable Growth",
    "High-Risk AI",
    "Crypto Diversification",
    "Custom Thesis",
]
# Map preset keys to research queries (Custom uses user input)
THESIS_QUERIES = {
    "Stable Growth": "Find established dividend or value stocks with stable growth and low volatility",
    "High-Risk AI": "Find high-growth AI and semiconductor stocks with strong fundamentals",
    "Crypto Diversification": "Find high-quality crypto assets with solid fundamentals for diversification",
    "Custom Thesis": "",  # User enters custom
}

# -----------------------------------------------------------------------------
# Research Flow Settings
# -----------------------------------------------------------------------------

# Number of assets Scout should identify per session (funnel: list all 4 initial candidates)
SCOUT_ASSET_COUNT = 4

# -----------------------------------------------------------------------------
# Model Configuration (Claude Sonnet 4.5 - verified available)
# -----------------------------------------------------------------------------

CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
FALLBACK_MODEL = "claude-3-haiku-20240307"  # Use if Sonnet 4.5 unavailable
SCOUT_MODEL = CLAUDE_MODEL
ANALYST_MODEL = CLAUDE_MODEL
RISK_MANAGER_MODEL = CLAUDE_MODEL
ARCHITECT_MODEL = CLAUDE_MODEL

OPENAI_MODEL = (os.getenv("OPENAI_MODEL") or "").strip() or CLAUDE_MODEL

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------

PROJECT_ROOT = _REPO_ROOT

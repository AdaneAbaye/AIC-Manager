"""
Configuration for The Autonomous Investment Committee (AIC).

Settings come from the root `.env` file (see `.env.example`).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_REPO_ROOT / ".env")

# Required for the Claude agents
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()

# Number of candidates the Scout hands to the Analyst
SCOUT_ASSET_COUNT = 4

# Model for every agent (override with CLAUDE_MODEL in .env)
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "").strip() or "claude-sonnet-4-5-20250929"
SCOUT_MODEL = CLAUDE_MODEL
ANALYST_MODEL = CLAUDE_MODEL
RISK_MANAGER_MODEL = CLAUDE_MODEL
ARCHITECT_MODEL = CLAUDE_MODEL

# Tool-call rounds each agent may use before it must answer (caps cost per run)
AGENT_MAX_ITER = int(os.getenv("AIC_AGENT_MAX_ITER", "12"))

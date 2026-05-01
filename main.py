"""
AIC-Manager API — FastAPI backend (research orchestration only).

Run from repo root: uvicorn main:app --reload --port 8000
"""

import logging
import os
import traceback
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).resolve().parent / ".env")

# Disable OpenTelemetry SDK (prevents CrewAI threading/signal errors)
os.environ["OTEL_SDK_DISABLED"] = "true"

from src.research_flow import ResearchSessionError, run_research_session
from src.security import redact_secrets, sanitize_investor_name, sanitize_thesis

logger = logging.getLogger(__name__)


def _redact_client_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Strip secret-like tokens from structured fields before JSON response."""
    approved: list[dict[str, Any]] = []
    for a in payload["approved_assets"]:
        approved.append(
            {
                **a,
                "rationale": redact_secrets(a["rationale"]),
            }
        )
    rejected: list[dict[str, Any]] = []
    for r in payload["rejected_assets"]:
        rejected.append(
            {
                **r,
                "reason": redact_secrets(r["reason"]),
            }
        )
    logs: list[dict[str, Any]] = []
    for entry in payload["agent_logs"]:
        logs.append(
            {
                "agent": entry["agent"],
                "lines": [redact_secrets(line) for line in entry["lines"]],
            }
        )
    return {
        "approved_assets": approved,
        "rejected_assets": rejected,
        "agent_logs": logs,
        "raw_report": redact_secrets(payload["raw_report"]),
    }


def _cors_allow_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000").strip()
    if not raw:
        return ["http://localhost:3000"]
    return [o.strip() for o in raw.split(",") if o.strip()]


app = FastAPI(title="AIC-Manager API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    """Investor profile + thesis (matches Next.js `RunResearchRequest`)."""

    research_thesis: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Investment research thesis or query",
    )
    budget: float = Field(..., gt=0, description="Monthly budget or lump-sum amount (USD)")
    investor_name: str = Field(default="Investor", max_length=50)
    portfolio_target: float = Field(default=1_000_000, gt=0)
    strategy: Literal["monthly_dca", "lump_sum"] = Field(
        default="monthly_dca",
        description="monthly_dca: DCA / cash-reserve rules; lump_sum: full deployment rules",
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/research")
def api_research(body: ResearchRequest) -> dict:
    """
    Run Scout → Analyst → Risk Manager → Architect.

    Returns: approved_assets, rejected_assets, agent_logs, raw_report (full markdown report).
    """
    thesis = sanitize_thesis(body.research_thesis)
    if not thesis.strip():
        raise HTTPException(
            status_code=400,
            detail="Research thesis is empty or invalid after sanitization.",
        )

    try:
        result = run_research_session(
            thesis=thesis,
            monthly_budget=body.budget,
            investor_name=sanitize_investor_name(body.investor_name),
            portfolio_target=body.portfolio_target,
            is_dca=(body.strategy == "monthly_dca"),
            agent_log_max_lines=20,
        )
    except ResearchSessionError as e:
        raise HTTPException(status_code=400, detail=redact_secrets(str(e))) from e
    except Exception:
        tb_safe = redact_secrets(traceback.format_exc())
        logger.error("api_research pipeline failed\n%s", tb_safe)
        raise HTTPException(
            status_code=503,
            detail="Research service temporarily unavailable. Please try again in a moment.",
        ) from None

    return _redact_client_payload(result)

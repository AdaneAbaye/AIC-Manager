"""
AIC-Manager API — FastAPI backend (research orchestration only).

Run from repo root: uvicorn main:app --reload --port 8000

Every research run calls the Anthropic API several times and costs money, so the
endpoint is protected by an optional access key, a per-IP rate limit and a cap
on concurrent runs (all configurable in .env).
"""

import hmac
import logging
import os
import threading
import time
import traceback
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).resolve().parent / ".env")

# Disable OpenTelemetry SDK (prevents CrewAI threading/signal errors). Must run before CrewAI is imported.
os.environ["OTEL_SDK_DISABLED"] = "true"

from src.research_flow import ResearchSessionError, run_research_session  # noqa: E402
from src.security import redact_secrets, sanitize_investor_name, sanitize_thesis  # noqa: E402

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Cost protection
# -----------------------------------------------------------------------------

ACCESS_KEY = os.getenv("AIC_ACCESS_KEY", "").strip()
RATE_LIMIT_RUNS = int(os.getenv("AIC_RATE_LIMIT_RUNS", "5"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("AIC_RATE_LIMIT_WINDOW_SECONDS", "3600"))
MAX_CONCURRENT_RUNS = int(os.getenv("AIC_MAX_CONCURRENT_RUNS", "1"))

_run_slots = threading.BoundedSemaphore(MAX_CONCURRENT_RUNS)
_runs_by_client: dict[str, deque] = defaultdict(deque)
_rate_lock = threading.Lock()


def _check_access_key(provided: Optional[str]) -> None:
    if ACCESS_KEY and not hmac.compare_digest((provided or "").encode(), ACCESS_KEY.encode()):
        raise HTTPException(status_code=401, detail="קוד הגישה שגוי · Invalid access code.")


def _check_rate_limit(client_id: str) -> None:
    now = time.monotonic()
    with _rate_lock:
        runs = _runs_by_client[client_id]
        while runs and now - runs[0] > RATE_LIMIT_WINDOW_SECONDS:
            runs.popleft()
        if len(runs) >= RATE_LIMIT_RUNS:
            minutes = max(1, int((RATE_LIMIT_WINDOW_SECONDS - (now - runs[0])) // 60) + 1)
            raise HTTPException(
                status_code=429,
                detail=f"הגעתם למגבלת המחקרים. נסו שוב בעוד {minutes} דקות · Rate limit reached.",
            )
        runs.append(now)


# -----------------------------------------------------------------------------
# App
# -----------------------------------------------------------------------------


def _redact_client_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Strip secret-like tokens from every text field before the JSON response."""
    return {
        "approved_assets": [{**a, "rationale": redact_secrets(a["rationale"])} for a in payload["approved_assets"]],
        "rejected_assets": [{**r, "reason": redact_secrets(r["reason"])} for r in payload["rejected_assets"]],
        "agent_logs": [
            {
                "agent": entry["agent"],
                "lines": [redact_secrets(line) for line in entry["lines"]],
                "markdown": redact_secrets(entry.get("markdown", "")),
            }
            for entry in payload["agent_logs"]
        ],
        "raw_report": redact_secrets(payload["raw_report"]),
    }


def _cors_allow_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000").strip()
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins or ["http://localhost:3000"]


app = FastAPI(title="AIC-Manager API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Access-Key"],
)


class ResearchRequest(BaseModel):
    """Investor profile + thesis (matches Next.js `RunResearchRequest`)."""

    research_thesis: str = Field(..., min_length=1, max_length=500, description="Investment research thesis")
    budget: float = Field(..., gt=0, le=10_000_000, description="Monthly budget or lump-sum amount (USD)")
    investor_name: str = Field(default="Investor", max_length=50)
    portfolio_target: float = Field(default=1_000_000, gt=0, le=10_000_000_000)
    strategy: Literal["monthly_dca", "lump_sum"] = Field(
        default="monthly_dca",
        description="monthly_dca: DCA / cash-reserve rules; lump_sum: full deployment rules",
    )


@app.get("/health")
def health() -> dict[str, Any]:
    """Liveness check; also tells the UI whether to ask for an access code."""
    return {"status": "ok", "access_key_required": bool(ACCESS_KEY)}


@app.post("/api/research")
def api_research(
    body: ResearchRequest,
    request: Request,
    x_access_key: Optional[str] = Header(default=None),
) -> dict:
    """
    Run Scout → Analyst → Risk Manager → Architect.

    Returns: approved_assets, rejected_assets, agent_logs (with each agent's full
    markdown) and raw_report.
    """
    _check_access_key(x_access_key)

    thesis = sanitize_thesis(body.research_thesis)
    if not thesis.strip():
        raise HTTPException(status_code=400, detail="Research thesis is empty or invalid after sanitization.")

    _check_rate_limit(request.client.host if request.client else "unknown")

    if not _run_slots.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail="הוועדה כבר באמצע דיון אחר. נסו שוב בעוד דקה · Another research run is in progress.",
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
        raise HTTPException(status_code=502, detail=redact_secrets(str(e))) from e
    except Exception:
        logger.error("api_research pipeline failed\n%s", redact_secrets(traceback.format_exc()))
        raise HTTPException(
            status_code=503,
            detail="Research service temporarily unavailable. Please try again in a moment.",
        ) from None
    finally:
        _run_slots.release()

    return _redact_client_payload(result)

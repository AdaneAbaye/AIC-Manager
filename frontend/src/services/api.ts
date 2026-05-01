/**
 * FastAPI AIC-Manager backend — POST /api/research
 */

const DEFAULT_BASE = "http://localhost:8000";

export function getApiBaseUrl(): string {
  if (typeof process.env.NEXT_PUBLIC_API_URL === "string" && process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "");
  }
  return DEFAULT_BASE;
}

export type ApprovedAsset = {
  ticker: string;
  pct: number;
  amount: number;
  rationale: string;
};

export type RejectedAsset = {
  ticker: string;
  reason: string;
};

export type AgentLogEntry = {
  agent: string;
  lines: string[];
};

export type RunResearchResponse = {
  approved_assets: ApprovedAsset[];
  rejected_assets: RejectedAsset[];
  agent_logs: AgentLogEntry[];
  /** Full committee markdown report (optional for older clients). */
  raw_report?: string;
};

export type ResearchStrategy = "monthly_dca" | "lump_sum";

export type RunResearchRequest = {
  research_thesis: string;
  budget: number;
  investor_name: string;
  portfolio_target: number;
  strategy: ResearchStrategy;
};

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export type RunResearchOptions = {
  signal?: AbortSignal;
};

export async function runResearch(
  body: RunResearchRequest,
  options?: RunResearchOptions
): Promise<RunResearchResponse> {
  const url = `${getApiBaseUrl()}/api/research`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      research_thesis: body.research_thesis.trim(),
      budget: body.budget,
      investor_name: body.investor_name.trim() || "Investor",
      portfolio_target: body.portfolio_target,
      strategy: body.strategy,
    }),
    signal: options?.signal,
  });

  if (!res.ok) {
    let detail: string | undefined;
    try {
      const errJson = (await res.json()) as { detail?: string | string[] };
      if (typeof errJson.detail === "string") detail = errJson.detail;
      else if (Array.isArray(errJson.detail)) detail = errJson.detail.map(String).join(" ");
    } catch {
      detail = await res.text();
    }
    throw new ApiError(detail || `Request failed (${res.status})`, res.status, detail);
  }

  return res.json() as Promise<RunResearchResponse>;
}

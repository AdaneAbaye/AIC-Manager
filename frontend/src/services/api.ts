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
  /** Opening line, outcome, then detail lines (capped). */
  lines: string[];
  /** The agent's full report as markdown. */
  markdown?: string;
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
  /** Sent as X-Access-Key when the server requires an access code. */
  accessKey?: string;
};

export type ServerInfo = { accessKeyRequired: boolean };

/** Ask the backend whether it requires an access code. Assumes not, if it can't be reached. */
export async function getServerInfo(): Promise<ServerInfo> {
  try {
    const res = await fetch(`${getApiBaseUrl()}/health`);
    const json = (await res.json()) as { access_key_required?: boolean };
    return { accessKeyRequired: Boolean(json.access_key_required) };
  } catch {
    return { accessKeyRequired: false };
  }
}

export async function runResearch(
  body: RunResearchRequest,
  options?: RunResearchOptions
): Promise<RunResearchResponse> {
  const url = `${getApiBaseUrl()}/api/research`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(options?.accessKey ? { "X-Access-Key": options.accessKey } : {}),
    },
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
      const errJson = (await res.json()) as { detail?: string | Array<string | { msg?: string }> };
      if (typeof errJson.detail === "string") detail = errJson.detail;
      else if (Array.isArray(errJson.detail))
        detail = errJson.detail.map((d) => (typeof d === "string" ? d : d.msg ?? "")).join(" ");
    } catch {
      detail = await res.text();
    }
    throw new ApiError(detail || `Request failed (${res.status})`, res.status, detail);
  }

  return res.json() as Promise<RunResearchResponse>;
}

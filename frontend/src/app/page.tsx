"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { CommitteeAgents, type AgentPipelineStatus } from "@/components/CommitteeAgents";
import { InvestorSidebar, type StrategyMode } from "@/components/InvestorSidebar";
import { RejectionList } from "@/components/RejectionList";
import { ResearchLogs } from "@/components/ResearchLogs";
import { StockCard } from "@/components/StockCard";
import { MAX_THESIS_LENGTH, redactSecrets, sanitizeInvestorName, sanitizeThesis } from "@/lib/sanitize";
import {
  ApiError,
  type RunResearchResponse,
  runResearch,
} from "@/services/api";

const IDLE: AgentPipelineStatus[] = ["idle", "idle", "idle", "idle"];

function isAbortError(e: unknown): boolean {
  return (
    (e instanceof DOMException && e.name === "AbortError") ||
    (typeof e === "object" &&
      e !== null &&
      "name" in e &&
      (e as { name: string }).name === "AbortError")
  );
}

export default function Home() {
  const [thesis, setThesis] = useState("");
  const [budget, setBudget] = useState(200);
  const [investorName, setInvestorName] = useState("Investor");
  const [portfolioTarget, setPortfolioTarget] = useState(1_000_000);
  const [strategy, setStrategy] = useState<StrategyMode>("monthly_dca");
  const [loading, setLoading] = useState(false);
  const [agentStatuses, setAgentStatuses] = useState<AgentPipelineStatus[]>(IDLE);
  const [result, setResult] = useState<RunResearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const stageTimersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearStageTimers = useCallback(() => {
    stageTimersRef.current.forEach(clearTimeout);
    stageTimersRef.current = [];
  }, []);

  useEffect(() => {
    if (!loading) return;
    const onBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [loading]);

  useEffect(() => {
    if (!loading) return;

    setAgentStatuses(["working", "idle", "idle", "idle"]);
    clearStageTimers();

    const schedule = (delay: number, next: AgentPipelineStatus[]) => {
      const id = setTimeout(() => {
        setAgentStatuses((prev) => {
          if (prev.every((s) => s === "done")) return prev;
          return next;
        });
      }, delay);
      stageTimersRef.current.push(id);
    };

    schedule(2800, ["done", "working", "idle", "idle"]);
    schedule(5600, ["done", "done", "working", "idle"]);
    schedule(8400, ["done", "done", "done", "working"]);

    return () => clearStageTimers();
  }, [loading, clearStageTimers]);

  function handleStopResearch() {
    abortRef.current?.abort();
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    const safeThesis = sanitizeThesis(thesis);
    if (!safeThesis.trim()) {
      setError("נא להזין תזת מחקר · Please enter a research thesis.");
      return;
    }
    if (!portfolioTarget || portfolioTarget <= 0) {
      setError("נא להזין יעד תיק חיובי · Portfolio target must be positive.");
      return;
    }
    if (!budget || budget <= 0) {
      setError("נא להזין תקציב חיובי · Budget must be positive.");
      return;
    }

    abortRef.current?.abort();
    abortRef.current = new AbortController();
    const { signal } = abortRef.current;

    setLoading(true);
    setAgentStatuses(["working", "idle", "idle", "idle"]);

    try {
      const data = await runResearch(
        {
          research_thesis: safeThesis,
          budget,
          investor_name: sanitizeInvestorName(investorName),
          portfolio_target: portfolioTarget,
          strategy,
        },
        { signal }
      );
      clearStageTimers();
      setResult(data);
      setAgentStatuses(["done", "done", "done", "done"]);
    } catch (err) {
      if (isAbortError(err)) {
        setError(null);
        setAgentStatuses(IDLE);
        clearStageTimers();
        return;
      }
      if (err instanceof ApiError) {
        setError(redactSecrets(err.detail || err.message));
      } else {
        setError("שגיאת רשת — ודאו שהשרת פועל על פורט 8000 · Network error — is the API running?");
      }
      setAgentStatuses(IDLE);
    } finally {
      clearStageTimers();
      setLoading(false);
    }
  }

  return (
    <div className="aic-bg-grid min-h-screen">
      <InvestorSidebar
        investorName={investorName}
        onInvestorNameChange={setInvestorName}
        portfolioTarget={portfolioTarget}
        onPortfolioTargetChange={setPortfolioTarget}
        budget={budget}
        onBudgetChange={setBudget}
        strategy={strategy}
        onStrategyChange={setStrategy}
      />

      {/* Physical right padding: fixed sidebar (anchored right in RTL layout) */}
      <div className="min-h-screen pr-[min(100%,18rem)] sm:pr-72">
        <div className="mx-auto max-w-6xl px-5 py-10 sm:px-8 sm:py-12">
          <CommitteeAgents statuses={agentStatuses} />

          <header className="mb-10 mt-10 border-b border-zinc-800/80 pb-8">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-emerald-500/80">
              AIC-Manager
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-zinc-50 sm:text-4xl">
              ועדת ההשקעות האוטונומית
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-zinc-500">
              Autonomous Investment Committee — מחקר מוסדי מבוסס סוכנים, הקצאות ושקיפות מלאה.
            </p>
          </header>

          <div className="mx-auto max-w-4xl">
            <form
              onSubmit={handleSubmit}
              className="rounded-2xl border border-zinc-800/80 bg-zinc-900/45 p-6 shadow-xl shadow-black/30 backdrop-blur-md sm:p-10"
            >
              <label htmlFor="thesis" className="mb-2 block text-sm font-medium text-zinc-400">
                תזת מחקר · Research thesis
              </label>
              <textarea
                id="thesis"
                value={thesis}
                maxLength={MAX_THESIS_LENGTH}
                onChange={(e) => setThesis(e.target.value.slice(0, MAX_THESIS_LENGTH))}
                rows={5}
                placeholder="לדוגמה: צמיחה יציבה, מניות דיבידנד..."
                className="w-full resize-y rounded-xl border border-zinc-700/80 bg-zinc-950/85 px-5 py-4 text-base leading-relaxed text-zinc-100 placeholder:text-zinc-600 focus:border-emerald-500/50 focus:outline-none focus:ring-2 focus:ring-emerald-500/25"
              />
              <p className="mt-2 text-xs text-zinc-600">
                עד {MAX_THESIS_LENGTH} תווים · תקציב ויעד תיק בסרגל הצד · Budget and target in sidebar.
              </p>

              <div className="mt-8 flex flex-wrap items-center gap-3 sm:gap-4">
                {loading && (
                  <button
                    type="button"
                    onClick={handleStopResearch}
                    className="relative z-20 order-first shrink-0 rounded-xl border-2 border-red-300 bg-red-600 px-6 py-4 text-base font-bold text-white shadow-xl shadow-red-900/50 ring-4 ring-red-500/30 transition hover:border-red-200 hover:bg-red-500 hover:ring-red-400/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-200"
                  >
                    עצירת מחקר · Stop research
                  </button>
                )}
                <button
                  type="submit"
                  disabled={loading}
                  className="rounded-lg bg-emerald-600 px-8 py-3.5 text-sm font-semibold text-white shadow-lg shadow-emerald-900/30 transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading ? "מבצעים מחקר…" : "הפעלת מחקר · Run research"}
                </button>
                {loading && (
                  <div className="flex min-w-0 flex-1 basis-[200px] items-center gap-3 text-sm text-zinc-400">
                    <span
                      className="inline-block size-4 shrink-0 animate-spin rounded-full border-2 border-zinc-600 border-t-emerald-400"
                      aria-hidden
                    />
                    <span>Researching… הסוכנים עובדים</span>
                  </div>
                )}
              </div>
            </form>
          </div>

          {error && (
            <div
              className="mx-auto mt-8 max-w-4xl rounded-xl border border-red-500/30 bg-red-950/40 px-4 py-3 text-sm text-red-200"
              role="alert"
            >
              {error}
            </div>
          )}

          {result && (
            <div className="mx-auto mt-12 max-w-4xl">
              <h2 className="mb-6 text-lg font-semibold text-zinc-200">
                המלצות · Recommendations
              </h2>
              {result.approved_assets.length > 0 ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  {result.approved_assets.map((asset, i) => (
                    <StockCard key={`${asset.ticker}-${i}-${asset.pct}`} asset={asset} />
                  ))}
                </div>
              ) : (
                <p className="rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-6 text-sm text-zinc-500">
                  לא זוהו הקצאות בטבלה — ייתכן שהפלט גולמי לא פורסר. נסו ניסוח אחר או בדקו את ה-API.
                </p>
              )}
              <RejectionList items={result.rejected_assets} />
              <ResearchLogs logs={result.agent_logs} />
            </div>
          )}

          <footer className="mx-auto mt-20 max-w-4xl border-t border-zinc-800/60 pt-8 text-center text-xs text-zinc-600">
            לא ייעוץ השקעות · למחקר וחינוך בלבד · Not financial advice
          </footer>
        </div>
      </div>
    </div>
  );
}

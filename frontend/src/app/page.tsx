"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AgentTranscript, type AgentPipelineStatus } from "@/components/AgentTranscript";
import { ExecutiveSummary } from "@/components/ExecutiveSummary";
import { ThesisForm, type StrategyMode } from "@/components/ThesisForm";
import { formatWithCommas } from "@/lib/formatNumbers";
import { redactSecrets, sanitizeInvestorName, sanitizeThesis } from "@/lib/sanitize";
import { ApiError, type RunResearchResponse, runResearch } from "@/services/api";

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

function todayLabel(): string {
  const d = new Date();
  return `${String(d.getDate()).padStart(2, "0")}.${String(d.getMonth() + 1).padStart(2, "0")}.${d.getFullYear()}`;
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
  const [submittedThesis, setSubmittedThesis] = useState("");
  const [durationSec, setDurationSec] = useState<number | null>(null);
  const [dateLabel, setDateLabel] = useState("");

  const abortRef = useRef<AbortController | null>(null);
  const stageTimersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  // Set on the client only, so server and client markup match.
  useEffect(() => setDateLabel(todayLabel()), []);

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

  function handleNewSession() {
    setResult(null);
    setError(null);
    setDurationSec(null);
    setAgentStatuses(IDLE);
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

    setSubmittedThesis(safeThesis);
    setDurationSec(null);
    setLoading(true);
    setAgentStatuses(["working", "idle", "idle", "idle"]);
    const startedAt = Date.now();

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
      setDurationSec(Math.max(1, Math.round((Date.now() - startedAt) / 1000)));
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

  const inSession = loading || result !== null;
  const strategyLabel = strategy === "monthly_dca" ? "DCA חודשי" : "סכום חד-פעמי";

  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <aside className="flex w-full shrink-0 flex-col gap-6 border-gray-200 px-6 py-8 sm:px-10 lg:sticky lg:top-0 lg:h-screen lg:w-[470px] lg:overflow-y-auto lg:border-l lg:py-9">
        <div className="flex items-center justify-between">
          <span className="font-display text-xl font-black">
            AIC<span className="text-blue-700">·</span>Manager
          </span>
          <span className="text-[12.5px] text-gray-500">ועדת השקעות אוטונומית{dateLabel && ` · ${dateLabel}`}</span>
        </div>

        {inSession ? (
          <>
            <div className="flex flex-col gap-2.5">
              <span className="text-[13px] font-bold text-blue-700">על השולחן</span>
              <h1 className="font-display text-[40px] font-black leading-[1.12]">{submittedThesis}</h1>
              <div className="flex flex-wrap gap-2 text-[13px] text-gray-700">
                <span className="rounded-full border border-gray-200 px-2.5 py-1.5" dir="ltr">
                  ${formatWithCommas(budget)}
                </span>
                <span className="rounded-full border border-gray-200 px-2.5 py-1.5">{strategyLabel}</span>
                <span className="rounded-full border border-gray-200 px-2.5 py-1.5">
                  יעד <span dir="ltr">${formatWithCommas(portfolioTarget)}</span>
                </span>
              </div>
            </div>

            {result ? (
              <ExecutiveSummary result={result} durationSec={durationSec} />
            ) : (
              <div className="flex items-center gap-3 rounded-2xl border border-gray-200 bg-slate-50 p-[22px] text-sm text-gray-600">
                <span
                  className="inline-block size-4 shrink-0 animate-spin rounded-full border-2 border-gray-300 border-t-blue-700"
                  aria-hidden="true"
                />
                הוועדה מתכנסת. זה לוקח בדרך כלל פחות מדקה.
              </div>
            )}

            <div className="mt-auto flex gap-2.5">
              {loading ? (
                <button
                  type="button"
                  onClick={handleStopResearch}
                  className="h-12 flex-1 rounded-xl border border-red-300 bg-white text-[15px] font-bold text-red-700 transition hover:bg-red-50"
                >
                  עצירת הדיון
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleNewSession}
                  className="h-12 flex-1 rounded-xl bg-blue-700 text-[15px] font-bold text-white transition hover:bg-blue-800"
                >
                  כינוס ישיבה חדשה
                </button>
              )}
            </div>
          </>
        ) : (
          <ThesisForm
            thesis={thesis}
            onThesisChange={setThesis}
            investorName={investorName}
            onInvestorNameChange={setInvestorName}
            portfolioTarget={portfolioTarget}
            onPortfolioTargetChange={setPortfolioTarget}
            budget={budget}
            onBudgetChange={setBudget}
            strategy={strategy}
            onStrategyChange={setStrategy}
            onSubmit={handleSubmit}
            loading={loading}
          />
        )}

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
            {error}
          </div>
        )}

        <p className="text-[11.5px] text-gray-500">לא ייעוץ השקעות · למחקר וללימוד בלבד</p>
      </aside>

      <main className="min-w-0 flex-1 bg-[#FBFBFC] px-6 py-8 sm:px-11 lg:py-9">
        <AgentTranscript
          logs={result?.agent_logs ?? []}
          statuses={agentStatuses}
          approved={result?.approved_assets ?? []}
          rejected={result?.rejected_assets ?? []}
          hasResult={result !== null}
        />
      </main>
    </div>
  );
}

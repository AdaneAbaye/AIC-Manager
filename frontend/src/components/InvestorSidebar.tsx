"use client";

import { useEffect, useState } from "react";
import { digitsOnly, formatWithCommas } from "@/lib/formatNumbers";

export type StrategyMode = "monthly_dca" | "lump_sum";

type Props = {
  investorName: string;
  onInvestorNameChange: (v: string) => void;
  portfolioTarget: number;
  onPortfolioTargetChange: (v: number) => void;
  budget: number;
  onBudgetChange: (v: number) => void;
  strategy: StrategyMode;
  onStrategyChange: (v: StrategyMode) => void;
};

export function InvestorSidebar({
  investorName,
  onInvestorNameChange,
  portfolioTarget,
  onPortfolioTargetChange,
  budget,
  onBudgetChange,
  strategy,
  onStrategyChange,
}: Props) {
  const [targetDisplay, setTargetDisplay] = useState(() => formatWithCommas(portfolioTarget));
  const [budgetDisplay, setBudgetDisplay] = useState(() => formatWithCommas(budget));

  useEffect(() => {
    setTargetDisplay(formatWithCommas(portfolioTarget));
  }, [portfolioTarget]);

  useEffect(() => {
    setBudgetDisplay(formatWithCommas(budget));
  }, [budget]);

  function handleTargetInput(raw: string) {
    const d = digitsOnly(raw);
    const n = d ? Number.parseInt(d, 10) : 0;
    onPortfolioTargetChange(n);
    setTargetDisplay(d ? formatWithCommas(n) : "");
  }

  function handleBudgetInput(raw: string) {
    const d = digitsOnly(raw);
    const n = d ? Number.parseInt(d, 10) : 0;
    onBudgetChange(n);
    setBudgetDisplay(d ? formatWithCommas(n) : "");
  }

  return (
    <aside
      className="fixed top-0 right-0 z-40 flex h-screen w-[min(100%,18rem)] flex-col overflow-y-auto border-l border-zinc-800/80 bg-zinc-950/95 px-5 py-6 shadow-2xl shadow-black/40 backdrop-blur-md sm:w-72 sm:px-6"
      aria-label="Investor profile settings"
    >
      <h2 className="border-b border-zinc-800/80 pb-3 text-sm font-semibold uppercase tracking-wider text-emerald-500/90">
        הגדרות פרופיל משקיע
      </h2>
      <p className="mt-1 text-xs text-zinc-500">Investor Profile Settings</p>

      <div className="mt-6 flex flex-1 flex-col space-y-5">
        <div>
          <label htmlFor="investor-name" className="mb-1.5 block text-sm font-medium text-zinc-400">
            שם משקיע · Name
          </label>
          <input
            id="investor-name"
            type="text"
            value={investorName}
            onChange={(e) => onInvestorNameChange(e.target.value.slice(0, 50))}
            maxLength={50}
            className="w-full rounded-lg border border-zinc-700/80 bg-zinc-900/80 px-3 py-2.5 text-sm text-zinc-100 focus:border-emerald-500/50 focus:outline-none focus:ring-1 focus:ring-emerald-500/40"
            dir="ltr"
            autoComplete="name"
          />
        </div>

        <div>
          <label htmlFor="portfolio-target" className="mb-1.5 block text-sm font-medium text-zinc-400">
            יעד תיק ($) · Portfolio target
          </label>
          <input
            id="portfolio-target"
            type="text"
            inputMode="numeric"
            autoComplete="off"
            value={targetDisplay}
            onChange={(e) => handleTargetInput(e.target.value)}
            placeholder="1,000,000"
            className="w-full rounded-lg border border-zinc-700/80 bg-zinc-900/80 px-3 py-2.5 text-left text-sm text-zinc-100 tabular-nums placeholder:text-zinc-600 focus:border-emerald-500/50 focus:outline-none focus:ring-1 focus:ring-emerald-500/40"
            dir="ltr"
          />
          <p className="mt-1 text-[10px] text-zinc-600">מספרים מופרדים בפסיקים · Comma-separated thousands</p>
        </div>

        <div>
          <label htmlFor="sidebar-budget" className="mb-1.5 block text-sm font-medium text-zinc-400">
            תקציב ($) · Budget
          </label>
          <input
            id="sidebar-budget"
            type="text"
            inputMode="numeric"
            autoComplete="off"
            value={budgetDisplay}
            onChange={(e) => handleBudgetInput(e.target.value)}
            placeholder="200"
            className="w-full rounded-lg border border-zinc-700/80 bg-zinc-900/80 px-3 py-2.5 text-left text-sm text-zinc-100 tabular-nums placeholder:text-zinc-600 focus:border-emerald-500/50 focus:outline-none focus:ring-1 focus:ring-emerald-500/40"
            dir="ltr"
          />
          <p className="mt-1 text-[10px] text-zinc-600">מספרים מופרדים בפסיקים · Comma-separated thousands</p>
        </div>

        <fieldset className="space-y-3">
          <legend className="mb-1 text-sm font-medium text-zinc-400">
            אסטרטגיה · Strategy
          </legend>
          <div className="space-y-2 rounded-lg border border-zinc-800/60 bg-zinc-900/40 p-3">
            <label className="flex cursor-pointer items-center gap-3 rounded-md px-2 py-2 transition hover:bg-zinc-800/40">
              <input
                type="radio"
                name="strategy"
                checked={strategy === "monthly_dca"}
                onChange={() => onStrategyChange("monthly_dca")}
                className="size-4 border-zinc-600 bg-zinc-900 text-emerald-600 focus:ring-emerald-500/40"
              />
              <span className="text-sm text-zinc-200">
                הוראת קבע חודשית (DCA)
                <span className="mr-1 block text-xs text-zinc-500 md:mr-0 md:inline md:px-1">
                  Monthly DCA
                </span>
              </span>
            </label>
            <label className="flex cursor-pointer items-center gap-3 rounded-md px-2 py-2 transition hover:bg-zinc-800/40">
              <input
                type="radio"
                name="strategy"
                checked={strategy === "lump_sum"}
                onChange={() => onStrategyChange("lump_sum")}
                className="size-4 border-zinc-600 bg-zinc-900 text-emerald-600 focus:ring-emerald-500/40"
              />
              <span className="text-sm text-zinc-200">
                סכום חד פעמי
                <span className="mr-1 block text-xs text-zinc-500 md:mr-0 md:inline md:px-1">
                  Lump Sum
                </span>
              </span>
            </label>
          </div>
        </fieldset>
      </div>
    </aside>
  );
}

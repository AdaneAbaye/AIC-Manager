"use client";

import { useEffect, useState } from "react";
import { digitsOnly, formatWithCommas } from "@/lib/formatNumbers";
import { MAX_THESIS_LENGTH } from "@/lib/sanitize";

export type StrategyMode = "monthly_dca" | "lump_sum";

type Props = {
  thesis: string;
  onThesisChange: (v: string) => void;
  investorName: string;
  onInvestorNameChange: (v: string) => void;
  portfolioTarget: number;
  onPortfolioTargetChange: (v: number) => void;
  budget: number;
  onBudgetChange: (v: number) => void;
  strategy: StrategyMode;
  onStrategyChange: (v: StrategyMode) => void;
  onSubmit: (e: React.FormEvent) => void;
  loading: boolean;
};

const inputClass =
  "h-11 w-full rounded-[10px] border border-gray-300 bg-white px-3 text-[15px] text-gray-900 placeholder:text-gray-400 focus:border-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-600/20";

/** What goes "on the table" for the committee: thesis plus investor profile. */
export function ThesisForm({
  thesis,
  onThesisChange,
  investorName,
  onInvestorNameChange,
  portfolioTarget,
  onPortfolioTargetChange,
  budget,
  onBudgetChange,
  strategy,
  onStrategyChange,
  onSubmit,
  loading,
}: Props) {
  const [targetDisplay, setTargetDisplay] = useState(() => formatWithCommas(portfolioTarget));
  const [budgetDisplay, setBudgetDisplay] = useState(() => formatWithCommas(budget));

  useEffect(() => setTargetDisplay(formatWithCommas(portfolioTarget)), [portfolioTarget]);
  useEffect(() => setBudgetDisplay(formatWithCommas(budget)), [budget]);

  function numberInput(raw: string, set: (n: number) => void, setDisplay: (s: string) => void) {
    const d = digitsOnly(raw);
    const n = d ? Number.parseInt(d, 10) : 0;
    set(n);
    setDisplay(d ? formatWithCommas(n) : "");
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <label htmlFor="thesis" className="text-[13px] font-bold text-blue-700">
          מה מונח על השולחן?
        </label>
        <textarea
          id="thesis"
          value={thesis}
          maxLength={MAX_THESIS_LENGTH}
          onChange={(e) => onThesisChange(e.target.value.slice(0, MAX_THESIS_LENGTH))}
          rows={4}
          placeholder="לדוגמה: מניות ערך עם צמיחה יציבה ותנודתיות נמוכה"
          className="w-full resize-none rounded-xl border border-gray-300 bg-white px-4 py-3 font-display text-2xl font-bold leading-snug text-gray-900 placeholder:font-sans placeholder:text-base placeholder:font-normal placeholder:text-gray-400 focus:border-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-600/20"
        />
        <span className="text-xs text-gray-500">עד {MAX_THESIS_LENGTH} תווים</span>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1.5">
          <label htmlFor="budget" className="text-[13px] text-gray-600">
            תקציב ($)
          </label>
          <input
            id="budget"
            type="text"
            inputMode="numeric"
            autoComplete="off"
            dir="ltr"
            value={budgetDisplay}
            onChange={(e) => numberInput(e.target.value, onBudgetChange, setBudgetDisplay)}
            placeholder="200"
            className={`${inputClass} text-left tabular-nums`}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="target" className="text-[13px] text-gray-600">
            יעד תיק ($)
          </label>
          <input
            id="target"
            type="text"
            inputMode="numeric"
            autoComplete="off"
            dir="ltr"
            value={targetDisplay}
            onChange={(e) => numberInput(e.target.value, onPortfolioTargetChange, setTargetDisplay)}
            placeholder="1,000,000"
            className={`${inputClass} text-left tabular-nums`}
          />
        </div>
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="investor" className="text-[13px] text-gray-600">
          שם המשקיע
        </label>
        <input
          id="investor"
          type="text"
          value={investorName}
          maxLength={50}
          autoComplete="name"
          onChange={(e) => onInvestorNameChange(e.target.value.slice(0, 50))}
          className={inputClass}
        />
      </div>

      <fieldset className="flex flex-col gap-1.5">
        <legend className="mb-1.5 text-[13px] text-gray-600">אסטרטגיה</legend>
        <div className="grid grid-cols-2 gap-1 rounded-xl border border-gray-300 p-1">
          {(
            [
              ["monthly_dca", "הוראת קבע חודשית (DCA)"],
              ["lump_sum", "סכום חד-פעמי"],
            ] as const
          ).map(([value, label]) => (
            <label
              key={value}
              className={`flex h-10 cursor-pointer items-center justify-center rounded-lg text-sm transition has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-blue-600/40 ${
                strategy === value ? "bg-blue-700 font-bold text-white" : "text-gray-700 hover:bg-gray-100"
              }`}
            >
              <input
                type="radio"
                name="strategy"
                value={value}
                checked={strategy === value}
                onChange={() => onStrategyChange(value)}
                className="sr-only"
              />
              {label}
            </label>
          ))}
        </div>
      </fieldset>

      <button
        type="submit"
        disabled={loading}
        className="mt-1 h-12 rounded-xl bg-blue-700 text-[15px] font-bold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60"
      >
        כינוס הוועדה
      </button>
    </form>
  );
}

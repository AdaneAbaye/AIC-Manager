import type { RunResearchResponse } from "@/services/api";
import { formatPct, formatUsd } from "@/lib/formatNumbers";

type Props = {
  result: RunResearchResponse;
  durationSec: number | null;
};

function countLabel(n: number, one: string, many: string): string {
  return n === 1 ? one : `${n} ${many}`;
}

/** The committee's verdict: allocation, rejections and session stats at a glance. */
export function ExecutiveSummary({ result, durationSec }: Props) {
  const approved = result.approved_assets;
  const rejected = result.rejected_assets;
  const ok = approved.length > 0;

  return (
    <section
      className="flex flex-col gap-4 rounded-2xl border border-gray-200 bg-slate-50 p-[22px]"
      aria-labelledby="summary-heading"
    >
      <div className="flex items-baseline justify-between">
        <h2 id="summary-heading" className="text-[15px] font-bold">
          סיכום מנהלים
        </h2>
        <span
          className={`rounded-full px-2.5 py-1 text-[12.5px] font-bold ${
            ok ? "bg-green-100 text-green-800" : "bg-amber-100 text-amber-900"
          }`}
        >
          {ok ? "הוועדה אישרה" : "לא אושרו נכסים"}
        </span>
      </div>

      <p className="font-display text-[26px] font-bold leading-tight">
        {countLabel(approved.length, "נכס אחד אושר", "נכסים אושרו")},{" "}
        {countLabel(rejected.length, "אחד נפסל", "נפסלו")}.
      </p>

      {ok ? (
        <ul className="flex flex-col gap-3.5">
          {approved.map((a, i) => (
            <li key={`${a.ticker}-${i}`} className="flex flex-col gap-1.5">
              <div className="flex justify-between gap-3 text-sm">
                <b className="font-mono" dir="ltr">
                  {a.ticker}
                </b>
                <b dir="ltr">
                  {formatUsd(a.amount)} · {formatPct(a.pct)}
                </b>
              </div>
              <div className="h-2.5 rounded-full bg-gray-200">
                <div
                  className="h-2.5 rounded-full bg-blue-700"
                  style={{ width: `${Math.max(2, Math.min(100, a.pct))}%` }}
                />
              </div>
              {a.rationale && <p className="line-clamp-2 text-[13px] leading-snug text-gray-600">{a.rationale}</p>}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm leading-relaxed text-gray-600">
          לא זוהו הקצאות בפלט של הוועדה. נסו לנסח את התזה אחרת, או פתחו את הדוח המלא של הארכיטקטית.
        </p>
      )}

      <div className="grid grid-cols-3 gap-2.5 border-t border-gray-200 pt-3.5">
        <div className="flex flex-col gap-0.5">
          <span className="text-xs text-gray-500">אושרו</span>
          <b className="text-base">{approved.length}</b>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-xs text-gray-500">נפסלו</span>
          <b className="text-base">{rejected.length}</b>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-xs text-gray-500">משך הדיון</span>
          <b className="text-base">{durationSec === null ? "—" : `${durationSec} שנ'`}</b>
        </div>
      </div>
    </section>
  );
}

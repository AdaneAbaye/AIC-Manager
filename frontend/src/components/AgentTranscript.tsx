import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";
import type { AgentLogEntry, ApprovedAsset, RejectedAsset } from "@/services/api";
import { AGENTS, AgentAvatar, agentFor, type AgentMeta } from "@/components/AgentAvatar";
import { formatPct } from "@/lib/formatNumbers";

export type AgentPipelineStatus = "idle" | "working" | "done";

type Props = {
  logs: AgentLogEntry[];
  statuses: AgentPipelineStatus[];
  approved: ApprovedAsset[];
  rejected: RejectedAsset[];
  hasResult: boolean;
};

/** Markdown tables/code stay LTR inside the RTL bubble. */
const markdownComponents: Components = {
  table: ({ children }) => (
    <div dir="ltr" className="my-3 w-full overflow-x-auto rounded-lg border border-gray-200">
      <table className="w-full min-w-[320px] border-collapse text-left text-[13px] text-gray-700">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border-b border-gray-200 bg-gray-50 px-3 py-2 text-left font-semibold text-gray-900">{children}</th>
  ),
  td: ({ children }) => <td className="border-b border-gray-100 px-3 py-2 align-top">{children}</td>,
  code: ({ children }) => (
    <code dir="ltr" className="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-[0.85em] text-gray-800">
      {children}
    </code>
  ),
  pre: ({ children }) => (
    <pre dir="ltr" className="my-3 overflow-x-auto rounded-lg bg-gray-50 p-3 font-mono text-xs text-gray-800">
      {children}
    </pre>
  ),
};

const OUTCOME_PREFIX = /^outcome:\s*/i;

function Chip({ meta, children }: { meta: AgentMeta; children: React.ReactNode }) {
  return (
    <span
      className="rounded-md px-2.5 py-1 font-mono text-[12.5px]"
      style={{ background: meta.tint, color: meta.color }}
    >
      {children}
    </span>
  );
}

function Evidence({
  meta,
  approved,
  rejected,
}: {
  meta: AgentMeta;
  approved: ApprovedAsset[];
  rejected: RejectedAsset[];
}) {
  if (meta.key === "scout") {
    const tickers = [...approved.map((a) => a.ticker), ...rejected.map((r) => r.ticker)];
    if (!tickers.length) return null;
    return (
      <div className="flex flex-wrap gap-1.5">
        {tickers.map((t, i) => (
          <Chip key={`${t}-${i}`} meta={meta}>
            {t}
          </Chip>
        ))}
      </div>
    );
  }
  if (meta.key === "risk" && rejected.length) {
    return (
      <div className="flex flex-wrap gap-2">
        {rejected.map((r, i) => (
          <span key={`${r.ticker}-${i}`} className="rounded-md bg-red-50 px-2.5 py-1 text-[12.5px] text-red-800">
            <b className="font-mono">{r.ticker}</b> · {r.reason}
          </span>
        ))}
      </div>
    );
  }
  if (meta.key === "architect" && approved.length) {
    return (
      <div className="flex flex-wrap gap-1.5">
        {approved.map((a, i) => (
          <Chip key={`${a.ticker}-${i}`} meta={meta}>
            {a.ticker} · {formatPct(a.pct)}
          </Chip>
        ))}
      </div>
    );
  }
  return null;
}

function Bubble({ meta, step, children }: { meta: AgentMeta; step: number; children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3.5">
      <AgentAvatar agent={meta.key} />
      <div className="flex min-w-0 flex-1 flex-col gap-2 rounded-2xl rounded-tr-md border border-gray-200 bg-white px-[18px] py-3.5">
        <div className="flex justify-between text-[13px]">
          <b style={{ color: meta.color }}>
            {meta.name} · {meta.role}
          </b>
          <span className="text-gray-500">שלב {step} מתוך 4</span>
        </div>
        {children}
      </div>
    </div>
  );
}

/**
 * The committee "minutes": each agent speaks in turn, with the evidence behind its call.
 * Before a run it introduces the four members; during a run it shows who is working.
 */
export function AgentTranscript({ logs, statuses, approved, rejected, hasResult }: Props) {
  const idleIntro = !hasResult && statuses.every((s) => s === "idle");

  return (
    <section className="flex flex-col gap-[18px]" aria-labelledby="minutes-heading">
      <div className="flex items-center justify-between">
        <h2 id="minutes-heading" className="text-lg font-bold">
          {idleIntro ? "חברי הוועדה" : "פרוטוקול הדיון"}
        </h2>
        <span className="text-[13px] text-gray-500">4 משתתפים</span>
      </div>

      {AGENTS.map((fallback, i) => {
        const entry = logs[i];
        const meta = entry ? agentFor(entry.agent, i) : fallback;
        const status = statuses[i] ?? "idle";

        if (entry) {
          const [action, outcomeLine, ...rest] = entry.lines;
          const fullReport = entry.markdown?.trim() || rest.join("\n");
          const outcome = (outcomeLine ?? "").replace(OUTCOME_PREFIX, "");
          return (
            <Bubble key={meta.key} meta={meta} step={i + 1}>
              {action && <div className="text-[13px] text-gray-500">{action}</div>}
              {outcome && <div className="text-[15px] leading-relaxed">{outcome}</div>}
              <Evidence meta={meta} approved={approved} rejected={rejected} />
              {fullReport && (
                <details className="group text-[14px]">
                  <summary className="cursor-pointer select-none text-[13px] font-medium" style={{ color: meta.color }}>
                    הדוח המלא של {meta.name}
                  </summary>
                  <div className="prose prose-sm mt-2 max-w-none text-gray-700 prose-headings:text-gray-900 prose-strong:text-gray-900">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeSanitize]}
                      components={markdownComponents}
                    >
                      {fullReport}
                    </ReactMarkdown>
                  </div>
                </details>
              )}
            </Bubble>
          );
        }

        if (status === "working") {
          return (
            <Bubble key={meta.key} meta={meta} step={i + 1}>
              <div className="flex items-center gap-2 text-[15px] text-gray-600">
                <span>עובד על זה</span>
                <span className="aic-typing inline-flex gap-1" aria-hidden="true">
                  <span className="size-1.5 rounded-full bg-gray-500" />
                  <span className="size-1.5 rounded-full bg-gray-500" />
                  <span className="size-1.5 rounded-full bg-gray-500" />
                </span>
              </div>
            </Bubble>
          );
        }

        return (
          <div key={meta.key} className={idleIntro ? "" : "opacity-50"}>
            <Bubble meta={meta} step={i + 1}>
              <div className="text-[15px] leading-relaxed text-gray-600">
                {status === "done" ? "סיים את שלבו." : INTRO[meta.key]}
              </div>
            </Bubble>
          </div>
        );
      })}
    </section>
  );
}

const INTRO: Record<AgentMeta["key"], string> = {
  scout: "סורק את השוק ומאתר נכסים שמתאימים לתזה שלך.",
  analyst: "בודקת דוחות כספיים, מכפילים וסנטימנט לכל מועמד.",
  risk: "מעריך תנודתיות וחוב, ופוסל כל מה שחורג מרמת הסיכון.",
  architect: "מחלקת את התקציב בין הנכסים שאושרו בלבד.",
};

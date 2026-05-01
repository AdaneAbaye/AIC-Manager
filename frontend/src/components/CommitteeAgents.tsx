export type AgentPipelineStatus = "idle" | "working" | "done";

const AGENTS: { key: string; icon: string; titleHe: string; titleEn: string; desc: string }[] = [
  {
    key: "scout",
    icon: "🔍",
    titleHe: "סייר",
    titleEn: "Scout",
    desc: "סורק שווקים ומאתר נכסים התואמים לתזה.",
  },
  {
    key: "analyst",
    icon: "📈",
    titleHe: "אנליסט",
    titleEn: "Analyst",
    desc: "בוחן דוחות כספיים, חדשות וסנטימנט לכל נכס.",
  },
  {
    key: "risk",
    icon: "🛡️",
    titleHe: "מנהל סיכונים",
    titleEn: "Risk Manager",
    desc: "מעריך תנודתיות ומתאים את הבחירות לאסטרטגיה.",
  },
  {
    key: "architect",
    icon: "📐",
    titleHe: "אדריכל תיק",
    titleEn: "Architect",
    desc: "מקצה את התקציב בין נכסים מאושרים בלבד.",
  },
];

const STATUS_LABEL: Record<AgentPipelineStatus, { he: string; en: string }> = {
  idle: { he: "מוכן", en: "Idle" },
  working: { he: "בתהליך", en: "Working" },
  done: { he: "הושלם", en: "Done" },
};

function StatusBadge({ status }: { status: AgentPipelineStatus }) {
  const base =
    "inline-flex shrink-0 items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide";
  if (status === "idle") {
    return (
      <span className={`${base} border border-zinc-700/80 bg-zinc-800/60 text-zinc-400`}>
        {STATUS_LABEL.idle.he} · {STATUS_LABEL.idle.en}
      </span>
    );
  }
  if (status === "working") {
    return (
      <span
        className={`${base} border border-amber-500/40 bg-amber-500/15 text-amber-300 shadow-[0_0_12px_rgba(245,158,11,0.15)]`}
      >
        <span className="relative flex size-1.5">
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-amber-400 opacity-60" />
          <span className="relative inline-flex size-1.5 rounded-full bg-amber-400" />
        </span>
        {STATUS_LABEL.working.he} · {STATUS_LABEL.working.en}
      </span>
    );
  }
  return (
    <span className={`${base} border border-emerald-500/35 bg-emerald-500/15 text-emerald-300`}>
      {STATUS_LABEL.done.he} · {STATUS_LABEL.done.en}
    </span>
  );
}

type Props = {
  /** One status per agent, same order as pipeline: Scout → Analyst → Risk → Architect */
  statuses: AgentPipelineStatus[];
};

export function CommitteeAgents({ statuses }: Props) {
  const list = AGENTS.map((a, i) => ({
    ...a,
    status: statuses[i] ?? "idle",
  }));

  return (
    <section
      className="rounded-2xl border border-zinc-800/80 bg-zinc-900/40 p-4 shadow-lg shadow-black/25 backdrop-blur-sm sm:p-6"
      aria-labelledby="committee-agents-heading"
    >
      <h2
        id="committee-agents-heading"
        className="mb-4 text-xs font-semibold uppercase tracking-[0.15em] text-zinc-500"
      >
        צינור המחקר · Research pipeline
      </h2>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {list.map((a) => (
          <article
            key={a.key}
            className="flex min-h-[8.5rem] flex-col rounded-xl border border-zinc-800/70 bg-zinc-950/60 p-4 shadow-inner transition hover:border-emerald-500/20"
          >
            <div className="flex items-start justify-between gap-2">
              <div
                className="flex size-11 shrink-0 items-center justify-center rounded-lg bg-zinc-800/90 text-xl"
                aria-hidden
              >
                {a.icon}
              </div>
              <StatusBadge status={a.status} />
            </div>
            <h3 className="mt-3 text-sm font-semibold text-zinc-100">
              {a.titleHe}
              <span className="mt-0.5 block text-[11px] font-normal text-zinc-500">{a.titleEn}</span>
            </h3>
            <p className="mt-2 flex-1 text-[12px] leading-relaxed text-zinc-500">{a.desc}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

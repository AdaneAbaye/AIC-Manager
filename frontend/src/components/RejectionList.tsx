import type { RejectedAsset } from "@/services/api";

type Props = {
  items: RejectedAsset[];
};

export function RejectionList({ items }: Props) {
  if (!items.length) return null;

  return (
    <section className="mt-10" aria-labelledby="rejected-heading">
      <h2
        id="rejected-heading"
        className="mb-4 text-sm font-semibold uppercase tracking-wider text-amber-500/90"
      >
        נכסים שנדחו · Rejected assets
      </h2>
      <ul className="space-y-3">
        {items.map((r) => (
          <li
            key={`${r.ticker}-${r.reason.slice(0, 24)}`}
            className="flex gap-3 rounded-lg border border-zinc-800/60 bg-zinc-900/30 px-4 py-3"
          >
            <span
              className="shrink-0 rounded bg-amber-500/10 px-2 py-0.5 font-mono text-sm text-amber-400"
              dir="ltr"
            >
              {r.ticker}
            </span>
            <span className="text-sm leading-relaxed text-zinc-400">{r.reason}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

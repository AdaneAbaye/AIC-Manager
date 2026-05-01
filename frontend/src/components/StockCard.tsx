import type { ApprovedAsset } from "@/services/api";

type Props = {
  asset: ApprovedAsset;
};

/**
 * Approved allocation card — tickers/numbers in LTR for readability in RTL layout.
 */
export function StockCard({ asset }: Props) {
  return (
    <article
      className="rounded-xl border border-zinc-800/80 bg-zinc-900/50 p-5 shadow-lg shadow-black/20 backdrop-blur-sm transition hover:border-emerald-500/30"
      dir="ltr"
    >
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="text-lg font-semibold tracking-tight text-zinc-100">
          {asset.ticker}
        </h3>
        <span className="rounded-md bg-emerald-500/15 px-2.5 py-1 text-sm font-medium text-emerald-400">
          {asset.pct.toFixed(1)}%
        </span>
      </div>
      <p className="mt-2 text-xs text-zinc-500">
        ${asset.amount.toLocaleString(undefined, { maximumFractionDigits: 0 })}
      </p>
      <p className="mt-3 text-sm leading-relaxed text-zinc-400">{asset.rationale}</p>
    </article>
  );
}

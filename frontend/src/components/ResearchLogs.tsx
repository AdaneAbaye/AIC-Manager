import type { AgentLogEntry } from "@/services/api";
import { Fragment } from "react";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";

type Props = {
  logs: AgentLogEntry[];
};

/**
 * Markdown components: LTR for data/code; tables per financial reporting spec.
 * Body RTL + text-align right applied on wrapper (prose).
 */
const markdownComponents: Components = {
  table: ({ children }) => (
    <div
      dir="ltr"
      className="my-6 w-full max-w-full overflow-x-auto rounded-lg border border-zinc-700/90 shadow-sm shadow-black/20"
    >
      <table className="w-full min-w-[320px] max-w-none table-auto border-collapse text-left text-sm text-zinc-300">
        {children}
      </table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-zinc-900/95">{children}</thead>,
  tbody: ({ children }) => (
    <tbody className="[&>tr:nth-child(even)]:bg-zinc-900/50">{children}</tbody>
  ),
  th: ({ children }) => (
    <th
      className="min-w-0 whitespace-normal break-words border border-zinc-700/80 px-3 py-3 text-left align-top text-xs font-bold uppercase tracking-wide text-zinc-200 [overflow-wrap:anywhere] [&:last-child:not(:nth-child(-n+3))]:text-right [&:last-child:not(:nth-child(-n+3))]:dir-rtl"
    >
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td
      className="min-w-0 whitespace-normal break-words border border-zinc-800/80 px-3 py-2.5 align-top text-left text-zinc-400 [overflow-wrap:anywhere] [&:last-child:not(:nth-child(-n+3))]:text-right [&:last-child:not(:nth-child(-n+3))]:dir-rtl"
    >
      {children}
    </td>
  ),
  tr: ({ children }) => (
    <tr className="transition-colors duration-150 hover:bg-zinc-800/35">{children}</tr>
  ),
  code: ({ className, children, ...props }) => {
    const isBlock = Boolean(className?.includes("language-"));
    if (isBlock) {
      return (
        <code className={className} {...props}>
          {children}
        </code>
      );
    }
    return (
      <code
        dir="ltr"
        className="rounded bg-zinc-800/90 px-1.5 py-0.5 font-mono text-[0.8em] font-medium text-emerald-200/95 [unicode-bidi:embed]"
        {...props}
      >
        {children}
      </code>
    );
  },
  pre: ({ children }) => (
    <pre
      dir="ltr"
      className="my-4 overflow-x-auto rounded-lg border border-zinc-700/80 bg-zinc-900/90 p-4 font-mono text-xs leading-relaxed text-emerald-100/90 [unicode-bidi:plaintext]"
    >
      {children}
    </pre>
  ),
};

const proseReportClasses = [
  "prose prose-invert max-w-none",
  "prose-zinc text-base",
  "prose-headings:font-bold prose-headings:text-zinc-100",
  "prose-h1:mb-4 prose-h1:mt-10 prose-h1:border-b prose-h1:border-zinc-700/80 prose-h1:pb-3 prose-h1:text-2xl prose-h1:first:mt-0",
  "prose-h2:mb-3 prose-h2:mt-8 prose-h2:text-xl",
  "prose-h3:mb-2 prose-h3:mt-6 prose-h3:text-lg",
  "prose-p:text-zinc-400 prose-p:leading-relaxed",
  "prose-strong:font-bold prose-strong:text-zinc-200",
  "prose-ul:text-zinc-400 prose-ol:text-zinc-400",
  "prose-li:my-1 prose-li:marker:text-emerald-600/90",
  "prose-blockquote:border-s-4 prose-blockquote:border-emerald-500/50 prose-blockquote:ps-4 prose-blockquote:italic prose-blockquote:text-zinc-500",
  "prose-hr:my-8 prose-hr:border-zinc-800",
  "prose-a:text-emerald-400 prose-a:underline prose-a:underline-offset-2 hover:prose-a:text-emerald-300",
  /* No ellipsis / nowrap; full wrapping in prose and tables */
  "[&_p]:whitespace-normal [&_li]:whitespace-normal",
  "[&_table]:max-w-none [&_th]:whitespace-normal [&_td]:whitespace-normal",
  "[&_code]:whitespace-pre-wrap [&_pre]:whitespace-pre-wrap",
].join(" ");

/**
 * Agent outcomes as markdown financial-style reports (RTL narrative, LTR data islands).
 */
export function ResearchLogs({ logs }: Props) {
  if (!logs.length) return null;

  return (
    <section className="mt-12" aria-labelledby="logs-heading">
      <h2
        id="logs-heading"
        className="mb-8 text-sm font-semibold uppercase tracking-wider text-zinc-500"
      >
        דוחות סוכנים · Agent reports
      </h2>
      <div className="flex flex-col gap-10">
        {logs.map((entry, idx) => {
          const markdown = entry.lines.join("\n\n");
          return (
            <Fragment key={`${entry.agent}-${idx}`}>
              <article className="overflow-hidden rounded-2xl border border-zinc-800/80 bg-zinc-950/50 shadow-lg shadow-black/20">
                <header className="border-b border-zinc-800/80 bg-zinc-900/60 px-4 py-3 sm:px-5">
                  <span className="text-sm font-bold text-emerald-400/95">{entry.agent}</span>
                  <span className="ms-2 text-xs font-medium text-zinc-500">· committee output</span>
                </header>
                <div
                  dir="rtl"
                  style={{ textAlign: "right" }}
                  className={`px-4 py-6 sm:px-6 sm:py-8 ${proseReportClasses}`}
                >
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeSanitize]}
                    components={markdownComponents}
                  >
                    {markdown}
                  </ReactMarkdown>
                </div>
              </article>
              {idx < logs.length - 1 ? (
                <div
                  role="separator"
                  aria-hidden
                  className="h-px w-full shrink-0 bg-gradient-to-l from-transparent via-zinc-600/50 to-transparent"
                />
              ) : null}
            </Fragment>
          );
        })}
      </div>
    </section>
  );
}

import { useId } from "react";

export type AgentKey = "scout" | "analyst" | "risk" | "architect";

export type AgentMeta = {
  key: AgentKey;
  name: string;
  role: string;
  /** Text/brand color for this agent (AA contrast on white). */
  color: string;
  /** Light tint used behind the avatar and for evidence chips. */
  tint: string;
};

export const AGENTS: AgentMeta[] = [
  { key: "scout", name: "הסקאוט", role: "איתור מועמדים", color: "#0F766E", tint: "#CCFBF1" },
  { key: "analyst", name: "האנליסטית", role: "ניתוח פיננסי", color: "#4338CA", tint: "#E0E7FF" },
  { key: "risk", name: "מנהל הסיכונים", role: "סינון וביקורת", color: "#B45309", tint: "#FEF3C7" },
  { key: "architect", name: "הארכיטקטית", role: "בניית התיק", color: "#BE123C", tint: "#FFE4E6" },
];

/** Map the backend's agent label ("Scout", "Risk Manager"…) or its index to our agent metadata. */
export function agentFor(label: string, index: number): AgentMeta {
  const l = label.toLowerCase();
  if (l.includes("scout")) return AGENTS[0];
  if (l.includes("analyst")) return AGENTS[1];
  if (l.includes("risk")) return AGENTS[2];
  if (l.includes("architect")) return AGENTS[3];
  return AGENTS[Math.min(index, AGENTS.length - 1)];
}

type Props = { agent: AgentKey; size?: number };

/** Flat illustrated portrait for each committee member (decorative). */
export function AgentAvatar({ agent, size = 46 }: Props) {
  const clipId = `aic-av-${useId().replace(/:/g, "")}`;
  const meta = AGENTS.find((a) => a.key === agent) ?? AGENTS[0];

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      aria-hidden="true"
      className="shrink-0"
    >
      <defs>
        <clipPath id={clipId}>
          <circle cx="32" cy="32" r="32" />
        </clipPath>
      </defs>
      <g clipPath={`url(#${clipId})`}>
        <rect width="64" height="64" fill={meta.tint} />
        <path d="M10 66c2-12 11-19 22-19s20 7 22 19z" fill={meta.color} />
        {agent === "scout" && (
          <>
            <circle cx="32" cy="28" r="11" fill="#F1D3BC" />
            <path d="M21 26c0-8 5-12 11-12s11 4 11 12c-3-3-7-4-11-4s-8 1-11 4z" fill="#3B2F2A" />
            <rect x="23" y="25" width="8" height="7" rx="3" fill="#1F2937" />
            <rect x="33" y="25" width="8" height="7" rx="3" fill="#1F2937" />
            <rect x="30" y="27" width="4" height="2" fill="#1F2937" />
            <path d="M29 34q3 2 6 0" stroke="#7A4B3A" strokeWidth="1.4" fill="none" />
          </>
        )}
        {agent === "analyst" && (
          <>
            <path d="M20 30c-1-10 4-16 12-16s13 6 12 16l-2 8H22z" fill="#6B3E26" />
            <circle cx="32" cy="28" r="10.5" fill="#E8BFA0" />
            <path d="M22 26c1-6 5-9 10-9s9 3 10 9c-4-3-12-5-20 0z" fill="#6B3E26" />
            <circle cx="28" cy="28" r="3.6" fill="none" stroke="#1F2937" strokeWidth="1.6" />
            <circle cx="36" cy="28" r="3.6" fill="none" stroke="#1F2937" strokeWidth="1.6" />
            <path d="M31.6 28h0.8" stroke="#1F2937" strokeWidth="1.6" />
            <path d="M29 34q3 2 6 0" stroke="#7A4B3A" strokeWidth="1.4" fill="none" />
          </>
        )}
        {agent === "risk" && (
          <>
            <circle cx="32" cy="28" r="11" fill="#C99372" />
            <path d="M21 25c1-7 5-10 11-10s10 3 11 10c-3-2-7-3-11-3s-8 1-11 3z" fill="#111827" />
            <circle cx="28" cy="29" r="1.4" fill="#1F2937" />
            <circle cx="36" cy="29" r="1.4" fill="#1F2937" />
            <path d="M29 34q3 1.5 6 0" stroke="#5A3222" strokeWidth="1.4" fill="none" />
            <path d="M32 50l7 2.5v5c0 4-3 6.5-7 8.5-4-2-7-4.5-7-8.5v-5z" fill="#FFFFFF" />
            <path d="M29 57l2 2 4-4" stroke={meta.color} strokeWidth="1.6" fill="none" strokeLinecap="round" />
          </>
        )}
        {agent === "architect" && (
          <>
            <circle cx="32" cy="29" r="11" fill="#F1D3BC" />
            <path d="M20 25a12 11 0 0 1 24 0z" fill="#F59E0B" />
            <rect x="17" y="24" width="30" height="3" rx="1.5" fill="#D97706" />
            <circle cx="28" cy="31" r="1.4" fill="#1F2937" />
            <circle cx="36" cy="31" r="1.4" fill="#1F2937" />
            <path d="M29 35q3 2 6 0" stroke="#7A4B3A" strokeWidth="1.4" fill="none" />
          </>
        )}
      </g>
    </svg>
  );
}

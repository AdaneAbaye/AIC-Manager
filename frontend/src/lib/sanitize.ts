/**
 * Client-side input hardening (mirrors src/security.py intent; defense in depth).
 */

const INJECTION_PATTERNS: RegExp[] = [
  /ignore\s+(previous|prior|all)\s+instructions/gi,
  /disregard\s+(previous|prior|all)/gi,
  /forget\s+(everything|all|previous)/gi,
  /override\s+(system|instructions)/gi,
  /you\s+are\s+now/gi,
  /new\s+instructions/gi,
  /system\s*:\s*/gi,
  /assistant\s*:\s*/gi,
  /\[INST\]/gi,
  /<\|im_start\|>/gi,
  /ignore\s+(budget|monthly\s+budget)/gi,
  /disregard\s+(budget|allocation)/gi,
];

export const MAX_THESIS_LENGTH = 500;

const CONTROL_CHARS = /[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/g;

export function stripControlChars(text: string): string {
  return text.replace(CONTROL_CHARS, "");
}

export function sanitizeThesis(thesis: string): string {
  let t = stripControlChars(thesis).trim().slice(0, MAX_THESIS_LENGTH);
  for (const re of INJECTION_PATTERNS) {
    re.lastIndex = 0;
    t = t.replace(re, "[removed]");
  }
  return t;
}

export function sanitizeInvestorName(name: string): string {
  let n = stripControlChars(name).trim().slice(0, 50);
  if (!n) return "Investor";
  for (const re of INJECTION_PATTERNS) {
    re.lastIndex = 0;
    n = n.replace(re, "[removed]");
  }
  return n || "Investor";
}

/** Redact secrets from API error strings before showing in UI. */
export function redactSecrets(message: string): string {
  if (!message) return message;
  return message
    .replace(/sk-[a-zA-Z0-9\-_]{20,}/g, "sk-[REDACTED]")
    .replace(/Bearer\s+[a-zA-Z0-9\-_.]+/gi, "Bearer [REDACTED]")
    .replace(/api_key=['"]?[^'"]+['"]?/gi, "api_key=[REDACTED]");
}

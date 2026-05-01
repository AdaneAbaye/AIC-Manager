/** Strip non-digits for parsing currency integers. */
export function digitsOnly(input: string): string {
  return input.replace(/\D/g, "");
}

/** Format integer part with comma thousands separators (en-US). */
export function formatWithCommas(value: number): string {
  if (!Number.isFinite(value) || value < 0) return "";
  const int = Math.floor(value);
  return int.toLocaleString("en-US", { maximumFractionDigits: 0 });
}

/** Parse formatted string to non-negative number; empty → 0. */
export function parseFormattedInt(formatted: string): number {
  const d = digitsOnly(formatted);
  if (!d) return 0;
  const n = Number.parseInt(d, 10);
  return Number.isFinite(n) ? n : 0;
}

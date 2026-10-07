/**
 * ordinal.ts — English ordinal formatter (1 -> "1st", 2 -> "2nd", 11 -> "11th", 21 -> "21st").
 *
 * The single helper for serving text. Never build an ordinal as `${n}th`:
 * that is right only for 4..20 (and 11..13) and renders 1/2/3/21/22/23 as "1th"/"2th"/"3th".
 * This is the platform-mcp copy (separate package, separate Docker build); the platform copy is
 * platform/src/lib/format/ordinal.ts (a parity test keeps the two in step).
 */
export function ordinal(n: number): string {
  if (!Number.isInteger(n)) throw new TypeError(`ordinal() needs an integer, got ${String(n)}`)
  const abs = Math.abs(n)
  const mod100 = abs % 100
  if (mod100 >= 11 && mod100 <= 13) return `${n}th`
  switch (abs % 10) {
    case 1: return `${n}st`
    case 2: return `${n}nd`
    case 3: return `${n}rd`
    default: return `${n}th`
  }
}

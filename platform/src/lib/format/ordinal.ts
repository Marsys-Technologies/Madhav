/**
 * ordinal.ts — English ordinal formatter (1 -> "1st", 2 -> "2nd", 11 -> "11th", 21 -> "21st").
 *
 * The single platform-side helper for serving text. Never build an ordinal as `${n}th`:
 * that is right only for 4..20 (and 11..13) and renders 1/2/3/21/22/23 as "1th"/"2th"/"3th".
 * platform-mcp ships as its own package and carries a byte-parity copy at
 * platform-mcp/src/lib/ordinal.ts (a parity test keeps the two in step).
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

/**
 * Non-throwing variant for serving paths: an integer gets its ordinal, anything else
 * (a non-integer or missing value from the database) degrades to the plain string.
 */
export function ordinalOrRaw(n: unknown): string {
  return typeof n === 'number' && Number.isInteger(n) ? ordinal(n) : String(n)
}

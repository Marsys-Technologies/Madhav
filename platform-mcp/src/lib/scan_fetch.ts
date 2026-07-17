/**
 * lib/scan_fetch.ts — D-2 Lane V-3, two-pass channel (BIND_D-2.md §F1.7 ledger row 20).
 *
 * PROBLEM this closes: several estate surfaces (bodha signals ≈ 9.9K rows/ayanamsha, yoga firings,
 * chart_facts EAV) are legitimately large. A consumer that wants to REASON over the whole set is
 * forced to either page through full rows (expensive, blows the response budget — the 234KB
 * bodha_signals class) or accept a salience-truncated top-K and lose sight of everything below it.
 *
 * THE TWO-PASS CHANNEL:
 *   Pass 1 — SCAN: return one ULTRA-DENSE subject-bearing index line per row (~60 bytes), so a
 *            consumer can survey hundreds/thousands of rows within a single small response and
 *            decide which few it actually needs. Each line is `id␟field1␟field2␟…` (a fixed,
 *            documented column order) prefixed by the row's stable id.
 *   Pass 2 — FETCH: given the ids the consumer picked from the scan, return the FULL rows.
 *
 * This is a deterministic transform over rows the estate already computes — it never re-ranks,
 * re-scores, or drops data silently (B.10): the scan reports the TRUE total and, when a byte cap
 * forces truncation, says so with an authoritative count so no "X absent" claim is ever made from a
 * trimmed scan (§F1.7 truncation honesty).
 */

const UNIT_SEP = '␟' // ␟ — visible, JSON-safe, never appears in chart data

export type ScanColumn<T> = {
  /** header label for this column (documented in the scan response) */
  key: string
  /** extract the cell value for a row; return '' for absent */
  get: (row: T) => unknown
}

export type ScanFetchConfig<T> = {
  /** stable id extractor — the token Pass-2 FETCH resolves against */
  id: (row: T) => string
  /** the subject-bearing columns, in fixed order (keep the set tiny — the point is ~60B/row) */
  columns: ScanColumn<T>[]
  /** soft target bytes per scan line (advisory — used only for the width warning) */
  targetLineBytes?: number
}

export type ScanResult = {
  mode: 'scan'
  total: number            // TRUE total rows available (pre-truncation) — truncation honesty
  returned: number         // scan lines actually returned
  truncated: boolean       // true iff returned < total because of the byte cap
  columns: string[]        // the fixed column order the index_lines encode
  separator: string        // the field separator used inside each index line (unit separator)
  avg_line_bytes: number
  index_lines: string[]    // `id␟c1␟c2␟…` per row
  next_step: string        // how to Pass-2 FETCH
}

export type FetchResult<T> = {
  mode: 'fetch'
  requested: number
  resolved: number
  missing_ids: string[]    // ids asked for that no row matched (honest, never silently dropped)
  rows: T[]
}

function cell(v: unknown): string {
  if (v == null) return ''
  if (typeof v === 'number') {
    // compact numeric: trim to 3 sig fractional digits, drop trailing zeros
    return Number.isInteger(v) ? String(v) : String(Math.round(v * 1000) / 1000)
  }
  const s = String(v)
  // strip the separator if it somehow appears, and clamp pathological cell width
  return s.replace(new RegExp(UNIT_SEP, 'g'), ' ').slice(0, 48)
}

/** Build one ultra-dense index line for a row: `id␟c1␟c2␟…`. */
export function scanLine<T>(row: T, cfg: ScanFetchConfig<T>): string {
  const parts = [cfg.id(row), ...cfg.columns.map((c) => cell(c.get(row)))]
  return parts.join(UNIT_SEP)
}

/**
 * Pass-1 SCAN: dense index over ALL rows, honestly truncated to a byte budget if needed.
 * @param maxBytes total byte cap for the concatenated index_lines (default 20_000 ≈ 300+ lines).
 */
export function scan<T>(rows: T[], cfg: ScanFetchConfig<T>, maxBytes = 20_000): ScanResult {
  const total = rows.length
  const lines: string[] = []
  let bytes = 0
  let truncated = false
  for (const row of rows) {
    const line = scanLine(row, cfg)
    const lineBytes = Buffer.byteLength(line, 'utf8') + 1 // +1 for the array/newline overhead
    if (bytes + lineBytes > maxBytes && lines.length > 0) {
      truncated = true
      break
    }
    lines.push(line)
    bytes += lineBytes
  }
  const avg = lines.length ? Math.round(bytes / lines.length) : 0
  return {
    mode: 'scan',
    total,
    returned: lines.length,
    truncated,
    columns: ['id', ...cfg.columns.map((c) => c.key)],
    separator: UNIT_SEP,
    avg_line_bytes: avg,
    index_lines: lines,
    next_step: truncated
      ? `SCAN truncated at ${lines.length}/${total} rows by the ${maxBytes}B cap — narrow the query ` +
        `(domain/type/salience facet) then re-scan, OR FETCH-by-id the rows you need from this page. ` +
        `Never read "the rest are absent" from a truncated scan (total=${total} is authoritative).`
      : `All ${total} rows scanned. Pick ids from index_lines, then FETCH-by-id for full rows.`,
  }
}

/** Pass-2 FETCH: resolve full rows for a set of ids picked from the scan. */
export function fetchByIds<T>(rows: T[], ids: string[], cfg: ScanFetchConfig<T>): FetchResult<T> {
  const want = new Set(ids)
  const byId = new Map<string, T>()
  for (const r of rows) byId.set(cfg.id(r), r)
  const resolved: T[] = []
  const missing: string[] = []
  for (const id of want) {
    const row = byId.get(id)
    if (row) resolved.push(row)
    else missing.push(id)
  }
  return { mode: 'fetch', requested: want.size, resolved: resolved.length, missing_ids: missing, rows: resolved }
}

/** Parse a scan index line back into a record keyed by the config's column order. */
export function parseScanLine(line: string, columns: string[]): Record<string, string> {
  const parts = line.split(UNIT_SEP)
  const out: Record<string, string> = {}
  columns.forEach((c, i) => { out[c] = parts[i] ?? '' })
  return out
}

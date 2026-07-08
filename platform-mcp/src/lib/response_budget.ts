/**
 * response_budget.ts — shared MCP-channel response-size trimmer (R5.1 C1)
 * ==========================================================================
 * PROBLEM (R5.1 C1 brief): judgment_query / graha_portrait / pact_query serve full-detail
 * payloads sized for internal debugging (up to ~86KB) — practically unusable over a real
 * MCP channel (context-window / token-budget blowout on the client side).
 *
 * THIS FILE is the ONE shared, reusable clipping mechanism for that problem — not three
 * bespoke ad-hoc trims per tool. It is STRUCTURE-AWARE (shrinks specific named arrays
 * inside the response object) rather than a byte-level string truncation — a byte-level
 * truncation of serialized JSON (see platform/src/lib/retrieval/adapters/shared/
 * result_clipper.ts, a sibling utility for a different consumer: LLM-context trimming of
 * arbitrary tool-call text, not MCP JSON envelopes) would produce invalid/truncated JSON
 * mid-object — unacceptable for a structured MCP tool response.
 *
 * MECHANICS:
 *   - Caller declares, per tool, which sections of its own response shape are "trimmable"
 *     arrays (a get/set pair + a floor + a recovery pointer).
 *   - `applyResponseBudget` measures the serialized size; if under budget, returns the
 *     content UNCHANGED (trim_report: null) — most calls never pay this cost's userland
 *     effect at all.
 *   - If over budget, it shrinks the HEAVIEST section first (by measured serialized size),
 *     halving repeatedly down to each section's floor, re-measuring after each cut, until
 *     under budget or every section has been floored.
 *   - Every actual cut is recorded in a TrimReportEntry (path, original_count, kept_count,
 *     reason, recover_via) — attached to the envelope's additive `trim_report` field
 *     (platform/src/lib/retrieval/envelope.ts + its generated mirror here).
 *   - CRITICAL (brief invariant): trimming only ever shortens ARRAYS the response already
 *     computed — it never deletes/invents data, never touches scalar verdict/receipt/
 *     pact_status fields, and the full detail remains reachable server-side via the
 *     `recover_via` instrument + explicit params (e.g. `max_signals`, `include`,
 *     `response_format:'legacy'`) — this file only governs what is DEFAULT-served.
 */

export interface TrimReportEntry {
  path: string
  original_count: number
  kept_count: number
  reason: string
  recover_via: { instrument: string; hint: string }
}

/** A single trimmable section of a tool's response content. */
export interface TrimmableSection<T> {
  /** Dot-path label used in the trim_report (does not need to be a real JS path — just a
   *  stable, human-readable pointer into the content shape). */
  path: string
  /** Read the current array at this section (undefined/non-array → section skipped). */
  getArray: (content: T) => unknown[] | undefined
  /** Replace the section with a shorter array (same shape/location as getArray). */
  setArray: (content: T, kept: unknown[]) => void
  /** Never cut below this many kept entries (0 allowed — fully droppable section). */
  minKeep: number
  /** How a caller recovers the full section. */
  recover: { instrument: string; hint: string }
  /** Human label used in the trim_report reason string. */
  label: string
}

export interface BudgetResult<T> {
  content: T
  trim_report: TrimReportEntry[] | null
  trimmed: boolean
  approx_bytes_before: number
  approx_bytes_after: number
}

/** Serialized-size estimate (UTF-8 bytes of JSON.stringify) — same measure the MCP wire
 *  transport actually pays, not a character count. */
export function estimateBytes(value: unknown): number {
  try {
    const json = JSON.stringify(value)
    return json ? Buffer.byteLength(json, 'utf8') : 0
  } catch {
    return 0
  }
}

/**
 * Shrink `content`'s declared trimmable sections until its serialized size is at or under
 * `maxKb` KB, or every section has been floored — whichever comes first. Mutates `content`
 * in place via each section's `setArray` (content is always a fresh, per-request object in
 * every call site this ships with — never a shared/cached reference) and also returns it.
 *
 * Sections are cut in DESCENDING order of their own current serialized size — the biggest
 * offender goes first, matching the "lean section summaries, not full detail" mandate
 * (small sections are left alone whenever the big ones alone can close the gap).
 */
export function applyResponseBudget<T>(
  content: T,
  maxKb: number,
  sections: TrimmableSection<T>[],
): BudgetResult<T> {
  const before = estimateBytes(content)
  const maxBytes = maxKb * 1024
  if (before <= maxBytes) {
    return { content, trim_report: null, trimmed: false, approx_bytes_before: before, approx_bytes_after: before }
  }

  const trimReport: TrimReportEntry[] = []
  let current = before

  // Re-rank by current size on every pass — cutting one section changes the overall
  // total but not other sections' sizes, so a single ranking-then-iterate pass is safe
  // and avoids re-sorting after every micro-cut.
  const ranked = sections
    .map(section => ({ section, arr: section.getArray(content) }))
    .filter((x): x is { section: TrimmableSection<T>; arr: unknown[] } => Array.isArray(x.arr) && x.arr.length > 0)
    .map(x => ({ ...x, size: estimateBytes(x.arr) }))
    .sort((a, b) => b.size - a.size)

  for (const { section, arr } of ranked) {
    if (current <= maxBytes) break
    const originalCount = arr.length
    let keepCount = originalCount
    let lastAppliedCount = originalCount
    while (current > maxBytes && keepCount > section.minKeep) {
      keepCount = Math.max(section.minKeep, Math.floor(keepCount / 2))
      const kept = arr.slice(0, keepCount)
      section.setArray(content, kept)
      current = estimateBytes(content)
      lastAppliedCount = keepCount
    }
    if (lastAppliedCount < originalCount) {
      trimReport.push({
        path: section.path,
        original_count: originalCount,
        kept_count: lastAppliedCount,
        reason: `${section.label} trimmed to fit the ${maxKb}KB MCP-channel response budget (R5.1 C1).`,
        recover_via: section.recover,
      })
    }
  }

  const after = estimateBytes(content)
  return {
    content,
    trim_report: trimReport.length > 0 ? trimReport : null,
    trimmed: trimReport.length > 0,
    approx_bytes_before: before,
    approx_bytes_after: after,
  }
}

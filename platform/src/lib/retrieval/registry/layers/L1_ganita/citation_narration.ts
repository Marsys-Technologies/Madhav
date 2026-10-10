/**
 * citation_narration.ts — serve `chart_facts.citation_human` (the graded narration) beside
 * `citation_ref` (SS N-345, Lahiri-primary PR-2).
 * ==========================================================================================
 * `citation_ref` is the machine pointer; `citation_human` is the writer's graded prose
 * restatement of the same fact. The typed L1 readers (get_nakshatra, get_ayurdaya,
 * get_panchanga, get_positions, get_sade_sati, get_sensitive_degrees, get_sensitive_points,
 * get_strength, get_structural_signals) select and serve it so a consumer no longer has to
 * reach for the legacy `ganita/facts_store.ts` path (`facts_store.ts:447`) to read it.
 *
 * Honesty rules (CLAUDE.md §N.7 item 6, B.10):
 *   - present and non-empty where the row carries it, served verbatim (trimmed of outer
 *     whitespace only);
 *   - an honest `null` where the row does not (NULL, empty or whitespace-only) — NEVER a
 *     made-up default or a string synthesised from other columns;
 *   - narration is the MOST DISPOSABLE field of a row: the shared response budget
 *     (`platform-mcp/src/lib/response_budget.ts`, `NARRATION_FIELDS`) sheds it FIRST under a
 *     tight budget, before any row (hardFloor or not) is cut — it must never be the field that
 *     pushes confirmed data out (§N.6).
 */

/** SQL select-list item: NULL for a NULL / empty / whitespace-only narration, else the text. */
export const CITATION_HUMAN_SELECT = `NULLIF(BTRIM(citation_human), '') AS citation_human`

/**
 * Normalise the narration on served rows in place: a missing, non-string, empty or
 * whitespace-only `citation_human` becomes `null`; a real string is trimmed and kept verbatim.
 * (The SQL already does this; the JS pass makes the contract hold for any row source.)
 */
export function normalizeNarrationRows<T extends Record<string, unknown>>(rows: T[] | undefined): T[] {
  const out = rows ?? []
  for (const row of out) {
    const v = (row as Record<string, unknown>)['citation_human']
    ;(row as Record<string, unknown>)['citation_human'] =
      typeof v === 'string' && v.trim() !== '' ? v.trim() : null
  }
  return out
}

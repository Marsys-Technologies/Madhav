/**
 * Gate I Performance — compliance detectors for project axioms B.10 + B.11.
 *
 * Pure functions, no side effects, no I/O. Inputs are already-assembled
 * structures from the audit-event consumer; outputs are booleans that
 * land directly in performance_queries.b10_violation / b11_violation.
 *
 * Brief: CLAUDECODE_BRIEF.md (GATE-I-PERF-CMD-001), W4.
 */

import type { ToolBundle } from '@/lib/retrieve/types'

/**
 * Citation object as derived from synthesis output. The shape is shaped by
 * the B.10 detector — `source_layer` carries the inferred origin.
 */
export interface CitationLite {
  source_layer: 'L1' | 'L2_5' | 'L3'
  citation_id: string
}

/**
 * Tools whose results live at the L2.5 layer (Holistic Synthesis).
 *
 * SYNC NOTE: This set must be kept in sync with the `inferLayer()` function in
 * `platform/src/app/api/chat/consume/route.ts`, which is the single source of truth.
 * The `RetrievalTool` type (retrieve/types.ts) has no `inferLayer` field, so a
 * runtime filter against `RETRIEVAL_TOOLS[]` is not structurally possible; instead
 * we maintain this set manually. When adding a new L2.5 tool, update BOTH this set
 * and `route.ts:inferLayer()`.
 *
 * Last synced: PERF-S1 (2026-05-21).
 * Current count: 14 tools (original 8 + 6 post-M3/M9 additions).
 */
const L2_5_TOOLS = new Set([
  // Original 8 (Phase 2 + Phase 9)
  'msr_sql',
  'query_msr_aggregate',
  'pattern_register',
  'resonance_register',
  'cluster_atlas',
  'contradiction_register',
  'temporal',
  'cgm_graph_walk',
  // M9 additions (multi-school triangulation)
  'multi_school_signal_lookup',
  'convergence_score_lookup',
  // M3/post-M3 additions (signal state + KP substrate + Varshaphala + cross-varga)
  'query_signal_state',
  'query_kp_ruling_planets',
  'query_varshaphala',
  'cross_varga_dignity_query',
])

/**
 * Chart-value heuristic. Matches degree-minute pairs like `12°34'`,
 * `12° 34'`, `12 deg`, or `12 degrees`. Intentionally NOT matching bare
 * 4-digit year tokens (e.g. `1984`) because those are not chart values.
 *
 * False-positive guard: we require a degree symbol OR the word `deg` /
 * `degrees`. Year tokens, plain integers, and arc-second-only patterns
 * are not matched.
 */
const CHART_VALUE_REGEX =
  /(\d{1,2}\s*°\s*\d{1,2}\s*['′])|(\d{1,2}\s*°(?!\s*[A-Z]))|(\d{1,3}\s*deg(?:ree)?s?\b)/i

/**
 * The marker that synthesis output uses to flag missing computations
 * per CLAUDE.md §I.B.10. Presence of this marker is treated as the
 * "we asked for an external compute" escape hatch.
 */
const EXTERNAL_COMPUTATION_MARKER_REGEX = /\[EXTERNAL_COMPUTATION_REQUIRED\]/

/**
 * B.10 violation: the model has invented numerical chart values.
 *
 * Rule (from CLAUDE.md §I.B.10): the LLM must never invent numerical chart
 * values; missing values must be marked `[EXTERNAL_COMPUTATION_REQUIRED]`.
 *
 * Heuristic:
 *   - Numeric chart-value tokens present in synthesisText: required precondition.
 *   - Violation only if (a) no `[EXTERNAL_COMPUTATION_REQUIRED]` marker AND
 *     (b) no L1 citation is attached. An L1 citation grounds the value in
 *     L1 facts and shields it from B.10.
 *
 * False positives are minimized by requiring a degree/arc symbol. Tests
 * in compliance.test.ts cover the documented cases.
 */
export function detectB10Violation(input: {
  synthesisText: string
  citationObjects: CitationLite[]
}): boolean {
  const text = input.synthesisText ?? ''
  if (!CHART_VALUE_REGEX.test(text)) return false
  if (EXTERNAL_COMPUTATION_MARKER_REGEX.test(text)) return false
  const hasL1Citation = (input.citationObjects ?? []).some((c) => c.source_layer === 'L1')
  if (hasL1Citation) return false
  return true
}

/**
 * B.11 violation: the query did not route through L2.5 Holistic Synthesis.
 *
 * Operational signal: did any L2.5-layer retrieval tool fire on the query?
 * Per W0.E audit, the audit-event does not carry a discrete "stage list",
 * so we use the `tool_results` array (the same array the consume route
 * uses to assemble TracePanel data via `inferLayer`).
 *
 * Fail-closed: if `toolResults` is empty/undefined, we conservatively
 * treat the query as not having consulted L2.5 → violation.
 */
export function detectB11Violation(input: {
  toolResults: Pick<ToolBundle, 'tool_name'>[] | undefined | null
}): boolean {
  const tools = input?.toolResults ?? []
  if (tools.length === 0) return true
  return !tools.some((t) => L2_5_TOOLS.has(t.tool_name))
}

/**
 * Parse citations out of synthesis text. Returns one CitationLite per citation marker
 * found. Two citation formats are recognized:
 *   1. Arrow format: `(→ ...)` — the original format used in Chat V2 pre-R7.
 *   2. GFM footnote format: `[^N]` inline + `[^N]: ...` definition — introduced in R7.
 *
 * The layer is heuristically inferred from the citation body using prefix conventions
 * (`FORENSIC`, `MSR`, etc.). Used by `writeConsumePerformanceRow` to feed B.10.
 *
 * TODO (PERF-S4 prerequisite): Replace this heuristic with a record-driven count.
 * The `query_trace_steps` table currently has no discrete `citation_count` column.
 * When the consume path populates that column (or a dedicated citations table), this
 * function should be replaced with a DB lookup against `query_trace_steps` or the
 * enriched-citation records from the R7 work. Until then, the regex covers both
 * citation formats and minimizes undercounting.
 */
export function parseCitations(synthesisText: string): CitationLite[] {
  const text = synthesisText ?? ''

  // Format 1: arrow citations `(→ body)`
  const arrowMarkers = text.match(/\(→[^()]+\)/g) ?? []

  // Format 2: GFM footnote definitions `[^N]: body` (R7+ format)
  // We collect the definition bodies to infer layer; inline `[^N]` references
  // are counted by how many definitions exist (definitions are 1-to-1 with references).
  const footnoteMarkers = text.match(/\[\^\d+\]:\s*[^\n]+/g) ?? []

  const results: CitationLite[] = []

  arrowMarkers.forEach((raw, idx) => {
    const body = raw.slice(2, -1).trim() // strip "(→" and ")"
    let layer: CitationLite['source_layer'] = 'L1'
    if (/MSR|UCN|CDLM|CGM|RM|025_HOLISTIC_SYNTHESIS/i.test(body)) layer = 'L2_5'
    else if (/03_DOMAIN_REPORTS|04_REMEDIAL_CODEX|035_DISCOVERY_LAYER/i.test(body)) layer = 'L3'
    else if (/FORENSIC|01_FACTS_LAYER|L1/i.test(body)) layer = 'L1'
    results.push({ source_layer: layer, citation_id: `cite_${idx}_${body.slice(0, 40)}` })
  })

  footnoteMarkers.forEach((raw, idx) => {
    // Strip the `[^N]: ` prefix to get the body
    const body = raw.replace(/^\[\^\d+\]:\s*/, '').trim()
    let layer: CitationLite['source_layer'] = 'L1'
    if (/MSR|UCN|CDLM|CGM|RM|025_HOLISTIC_SYNTHESIS/i.test(body)) layer = 'L2_5'
    else if (/03_DOMAIN_REPORTS|04_REMEDIAL_CODEX|035_DISCOVERY_LAYER/i.test(body)) layer = 'L3'
    else if (/FORENSIC|01_FACTS_LAYER|L1/i.test(body)) layer = 'L1'
    results.push({
      source_layer: layer,
      citation_id: `fn_cite_${arrowMarkers.length + idx}_${body.slice(0, 40)}`,
    })
  })

  return results
}

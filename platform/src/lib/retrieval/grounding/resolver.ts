/**
 * D3 Grounding Spine — Reference-Resolution Service
 * ===================================================
 * The central service that resolves signal_ids + fact_ids back to their L1 sources.
 *
 * Responsibilities:
 *   1. Given signal_ids, fetch bodha_msr_signals rows for a chart
 *   2. Extract constituent_facts_array from each signal
 *   3. Resolve each fact_id against chart_facts (same chart scope)
 *   4. Detect §N.5 violations (orphan fact_ids — references that don't resolve)
 *   5. Return GroundedResult with signals + their L1 citations
 *
 * Key invariants:
 *   - chart_id is ALWAYS required (principle #14 / §N.5)
 *   - NEVER fabricates values — missing data returns EMPTY, not invented (principle #2)
 *   - Each reference resolved exactly once (F1 — dedup before DB fetch)
 *   - §N.5 violation (orphan fact_id) is surfaced, not silently dropped
 *   - Out-of-vocabulary metric requests ERROR (not text-to-SQL guess — principle #3)
 */

import type {
  SignalId,
  FactId,
  ChartId,
  AyanamshaId,
  L1Fact,
  GroundedSignal,
  GroundedResult,
  GroundingError,
  GroundingOperationResult,
  GovernedMetric,
  MetricResolutionResult,
  ResolvedMetric,
} from './types'
import { GOVERNED_METRICS } from './types'
import type { DbProxy } from './db_proxy'

// ── DB row shapes (internal — not exported) ───────────────────────────────────

interface MsrRow {
  signal_id: string
  chart_id: string
  ayanamsha_id: string
  signal_type_id: string
  signal_type_class: string
  signal_summary_text: string | null
  computed_salience: number | null
  constituent_facts_array: string[]
  classical_sources_jsonb: unknown | null
  [key: string]: unknown
}

interface ChartFactRow {
  fact_id: string
  chart_id: string
  ayanamsha_id: string
  fact_category: string
  fact_subject: string
  fact_key: string
  fact_value_text: string | null
  fact_value_num: number | null
  fact_value_jsonb: Record<string, unknown> | null
  unit: string | null
  citation_ref: string
  citation_human: string
  source_calculation: string
  verification_pass_status: string
  [key: string]: unknown
}

// ── SQL ───────────────────────────────────────────────────────────────────────

const MSR_SIGNALS_SQL = `
  SELECT
    signal_id, chart_id, ayanamsha_id,
    signal_type_id, signal_type_class, signal_summary_text,
    computed_salience, constituent_facts_array, classical_sources_jsonb
  FROM bodha_msr_signals
  WHERE chart_id = $1
    AND signal_id = ANY($2::uuid[])
`

const CHART_FACTS_SQL = `
  SELECT
    fact_id, chart_id, ayanamsha_id,
    fact_category, fact_subject, fact_key,
    fact_value_text, fact_value_num, fact_value_jsonb,
    unit, citation_ref, citation_human,
    source_calculation, verification_pass_status
  FROM chart_facts
  WHERE chart_id = $1
    AND fact_id = ANY($2::text[])
`

const METRIC_SIGNAL_SQL = (metric: GovernedMetric) => `
  SELECT
    signal_id, chart_id, ${metric},
    citation_human
  FROM bodha_msr_signals
  WHERE chart_id = $1
    AND signal_id = $2
`

const METRIC_FACT_SQL = `
  SELECT
    fact_id, chart_id, fact_value_num,
    citation_human
  FROM chart_facts
  WHERE chart_id = $1
    AND fact_id = $2
`

// ── citation_human sanitization ────────────────────────────────────────────────

/**
 * Matches an internal GAP-tracking-ticket + raw-fact_id annotation appended to
 * a citation_human string, e.g.:
 *   "Saturn nak-lord chain length=7 (cycle@6) in lahiri_chitrapaksha. \
 *    GAP-4: L1 nakshatra_lord fact_id=16ff3dbbc4bc15b5 (graha_nakshatra_join)."
 *
 * citation_human is served as a human-readable string; the fact_id/ticket
 * linkage already has a proper home in citation_ref (machine-readable) and the
 * L1Fact.fact_id field itself, both visible elsewhere in the same envelope.
 * Duplicating that internal bookkeeping into citation_human is a leak, not a
 * feature — strip it here, once, at construction time.
 */
const CITATION_GAP_TICKET_RE = /\s*GAP-\d+:\s*L1\s+\S+\s+fact_id=\S+\s*\([^)]*\)\.?\s*$/i

/**
 * Sanitize a raw citation_human value read from the DB by stripping any
 * trailing internal GAP-ticket + fact_id annotation. Safe no-op on strings
 * that don't carry the annotation (principle #2 — never fabricates; only
 * removes a substring that should never have been human-facing).
 */
function sanitizeCitationHuman(raw: string): string {
  if (!raw) return raw
  return raw.replace(CITATION_GAP_TICKET_RE, '').trimEnd()
}

// ── Grounding resolver ────────────────────────────────────────────────────────

/**
 * Resolve a set of signal_ids for a chart to their L1 facts.
 *
 * @param db          DB proxy (live or stub)
 * @param chart_id    Required — chart scope for all queries
 * @param signal_ids  The signal_ids to resolve (de-duped before fetch)
 * @param ayanamsha_id Optional filter — if provided, only signals with this ayanamsha are returned
 *
 * @returns GroundingOperationResult:
 *   - ok=true: GroundedResult with signals + resolved L1 facts (+ orphan_fact_ids for §N.5 tracking)
 *   - ok=false: GroundingError with MISSING_CHART_ID or EMPTY_SIGNAL_IDS or DB_ERROR
 */
export async function resolveSignals(
  db: DbProxy,
  chart_id: ChartId,
  signal_ids: SignalId[],
  ayanamsha_id?: AyanamshaId
): Promise<GroundingOperationResult> {

  // ── Input guards (principle #2 / §N.5 — chart_id always required) ────────
  if (!chart_id || chart_id.trim() === '') {
    return {
      ok: false,
      error: {
        error_code: 'MISSING_CHART_ID',
        message: '[grounding] chart_id is required — grounding spine is chart-scoped',
      },
    }
  }

  if (!signal_ids || signal_ids.length === 0) {
    return {
      ok: false,
      error: {
        error_code: 'EMPTY_SIGNAL_IDS',
        message: '[grounding] at least one signal_id is required',
      },
    }
  }

  // ── F1: resolve each signal_id exactly once ───────────────────────────────
  const uniqueSignalIds = [...new Set(signal_ids)]

  try {
    // ── Step 1: Fetch MSR signal rows ────────────────────────────────────────
    const signalRows = await db.query<MsrRow>(
      MSR_SIGNALS_SQL,
      [chart_id, uniqueSignalIds]
    )

    // ── Step 2: Collect all fact_ids (de-duped, F1) ──────────────────────────
    const allFactIds = new Set<FactId>()
    for (const row of signalRows) {
      const facts = row.constituent_facts_array ?? []
      for (const fid of facts) {
        allFactIds.add(fid)
      }
    }

    // ── Step 3: Fetch L1 facts in one batched query ──────────────────────────
    const factRowsRaw = allFactIds.size > 0
      ? await db.query<ChartFactRow>(
          CHART_FACTS_SQL,
          [chart_id, [...allFactIds]]
        )
      : []

    // ── Step 4: Index facts by fact_id for O(1) lookup ───────────────────────
    const factMap = new Map<FactId, L1Fact>()
    for (const row of factRowsRaw) {
      // §N.5 chart scope check: if chart_facts returns a row for a different chart,
      // that is a data integrity bug — skip it and let orphan detection catch it.
      if (row.chart_id !== chart_id) continue

      factMap.set(row.fact_id, {
        fact_id: row.fact_id,
        chart_id: row.chart_id,
        ayanamsha_id: row.ayanamsha_id,
        fact_category: row.fact_category,
        fact_subject: row.fact_subject,
        fact_key: row.fact_key,
        fact_value_text: row.fact_value_text,
        fact_value_num: row.fact_value_num != null ? Number(row.fact_value_num) : null,
        fact_value_jsonb: row.fact_value_jsonb as Record<string, unknown> | null,
        unit: row.unit,
        citation_ref: row.citation_ref,
        citation_human: sanitizeCitationHuman(row.citation_human),
        source_calculation: row.source_calculation,
        verification_pass_status: row.verification_pass_status,
      })
    }

    // ── Step 5: Build signalId → row map ─────────────────────────────────────
    const signalMap = new Map<SignalId, MsrRow>()
    for (const row of signalRows) {
      signalMap.set(row.signal_id, row)
    }

    // ── Step 6: Compose GroundedSignal for each requested signal_id ──────────
    const not_found_signal_ids: SignalId[] = []
    const groundedSignals: GroundedSignal[] = []
    let totalOrphans = 0

    for (const sid of uniqueSignalIds) {
      const row = signalMap.get(sid)
      if (!row) {
        not_found_signal_ids.push(sid)
        continue
      }

      // Optional ayanamsha filter
      if (ayanamsha_id && row.ayanamsha_id !== ayanamsha_id) {
        not_found_signal_ids.push(sid)
        continue
      }

      const constituentIds: FactId[] = row.constituent_facts_array ?? []
      const resolved_facts: L1Fact[] = []
      const orphan_fact_ids: FactId[] = []

      for (const fid of constituentIds) {
        const fact = factMap.get(fid)
        if (fact) {
          resolved_facts.push(fact)
        } else {
          // §N.5 violation: constituent_facts_array references a fact_id that
          // does not exist in chart_facts for this chart.
          orphan_fact_ids.push(fid)
          totalOrphans++
        }
      }

      // Extract L0 citation references from classical_sources_jsonb
      const l0_citation_refs = extractL0Refs(row.classical_sources_jsonb)

      groundedSignals.push({
        signal_id: row.signal_id,
        chart_id: row.chart_id,
        ayanamsha_id: row.ayanamsha_id,
        signal_type_id: row.signal_type_id,
        signal_type_class: row.signal_type_class,
        signal_summary_text: row.signal_summary_text,
        computed_salience: row.computed_salience != null ? Number(row.computed_salience) : null,
        constituent_fact_ids: constituentIds,
        resolved_facts,
        orphan_fact_ids,
        l0_citation_refs,
      })
    }

    const result: GroundedResult = {
      chart_id,
      ayanamsha_id: ayanamsha_id ?? 'LAHIRI',
      signals: groundedSignals,
      not_found_signal_ids,
      has_n5_violations: totalOrphans > 0,
      orphan_fact_count: totalOrphans,
      grounded_at: new Date().toISOString(),
    }

    return { ok: true, result }

  } catch (err) {
    return {
      ok: false,
      error: {
        error_code: 'DB_ERROR',
        message: `[grounding] DB query failed: ${err instanceof Error ? err.message : String(err)}`,
      },
    }
  }
}

// ── Governed metric resolver ──────────────────────────────────────────────────

/**
 * Resolve a single governed numeric metric for a signal or fact.
 *
 * Principle #3 / §N.5:
 *   - Only metrics in GOVERNED_METRICS are resolvable.
 *   - Out-of-vocabulary requests return OUT_OF_VOCAB error, never a SQL guess.
 *   - The value is read from the deterministic DB row — never regenerated.
 *
 * @param db         DB proxy
 * @param chart_id   Required chart scope
 * @param metric     The governed metric to resolve
 * @param source_id  The signal_id (for signal metrics) or fact_id (for fact_value_num)
 *
 * @returns MetricResolutionResult: ok=true with resolved value, or ok=false with error
 */
export async function resolveMetric(
  db: DbProxy,
  chart_id: ChartId,
  metric: string,
  source_id: SignalId | FactId
): Promise<MetricResolutionResult> {

  // ── Input guard: chart_id ─────────────────────────────────────────────────
  if (!chart_id || chart_id.trim() === '') {
    return {
      ok: false,
      error: {
        error_code: 'MISSING_CHART_ID',
        message: '[grounding/metric] chart_id is required',
        requested_metric: metric,
      },
    }
  }

  // ── Governed vocabulary check (principle #3) ─────────────────────────────
  if (!GOVERNED_METRICS.has(metric as GovernedMetric)) {
    return {
      ok: false,
      error: {
        error_code: 'OUT_OF_VOCAB',
        message:
          `[grounding/metric] '${metric}' is not in the governed metric vocabulary. ` +
          `Valid metrics: ${[...GOVERNED_METRICS].join(', ')}. ` +
          `Out-of-vocabulary numeric requests are rejected — the grounding spine never guesses.`,
        requested_metric: metric,
      },
    }
  }

  const governedMetric = metric as GovernedMetric

  try {
    if (governedMetric === 'fact_value_num') {
      // Resolve from chart_facts
      const rows = await db.query<{
        fact_id: string
        chart_id: string
        fact_value_num: number | null
        citation_human: string
      }>(METRIC_FACT_SQL, [chart_id, source_id])

      if (rows.length === 0) {
        return {
          ok: false,
          error: {
            error_code: 'FACT_NOT_FOUND',
            message: `[grounding/metric] fact_id '${source_id}' not found in chart_facts for chart '${chart_id}'`,
            fact_id: source_id,
            requested_metric: metric,
          },
        }
      }

      const row = rows[0]
      const resolved: ResolvedMetric = {
        metric: governedMetric,
        value: row.fact_value_num != null ? Number(row.fact_value_num) : null,
        source_id,
        source_table: 'chart_facts',
        citation: sanitizeCitationHuman(row.citation_human),
      }
      return { ok: true, metric: resolved }

    } else {
      // Resolve from bodha_msr_signals
      const sql = METRIC_SIGNAL_SQL(governedMetric)
      const rows = await db.query<{
        signal_id: string
        chart_id: string
        citation_human: string
        [key: string]: unknown
      }>(sql, [chart_id, source_id])

      if (rows.length === 0) {
        return {
          ok: false,
          error: {
            error_code: 'SIGNAL_NOT_FOUND',
            message: `[grounding/metric] signal_id '${source_id}' not found in bodha_msr_signals for chart '${chart_id}'`,
            signal_id: source_id,
            requested_metric: metric,
          },
        }
      }

      const row = rows[0]
      const rawValue = row[governedMetric]
      const resolved: ResolvedMetric = {
        metric: governedMetric,
        value: rawValue != null ? Number(rawValue) : null,
        source_id,
        source_table: 'bodha_msr_signals',
        citation: sanitizeCitationHuman(row.citation_human),
      }
      return { ok: true, metric: resolved }
    }

  } catch (err) {
    return {
      ok: false,
      error: {
        error_code: 'DB_ERROR',
        message: `[grounding/metric] DB query failed: ${err instanceof Error ? err.message : String(err)}`,
        requested_metric: metric,
      },
    }
  }
}

// ── §N.5 violation asserter ───────────────────────────────────────────────────

/**
 * Assert that a GroundedResult has zero §N.5 violations.
 * Call this to enforce the §N.5 invariant at a boundary point.
 *
 * Per §N.5: "If a signal's derivation disagrees with the L1 fact it cites,
 * that is a halt-worthy bug, not a stored divergence."
 *
 * Returns the violations as GroundingErrors (one per orphan reference).
 * Caller decides whether to halt or surface them in the result.
 */
export function assertNoN5Violations(result: GroundedResult): GroundingError[] {
  const violations: GroundingError[] = []

  for (const signal of result.signals) {
    for (const orphanId of signal.orphan_fact_ids) {
      violations.push({
        error_code: 'N5_VIOLATION',
        message:
          `[grounding/§N.5] signal '${signal.signal_id}' references fact_id '${orphanId}' ` +
          `in constituent_facts_array but that fact_id does not exist in chart_facts ` +
          `for chart '${result.chart_id}'. This is a data integrity violation per §N.5.`,
        signal_id: signal.signal_id,
        fact_id: orphanId,
      })
    }
  }

  return violations
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Extract L0 citation reference strings from classical_sources_jsonb.
 * The field is JSONB with shape: { catalog_ids[], rule_ids[], text_chunk_ids[], citations[] }.
 * We extract all ID arrays and flatten to a string list.
 */
function extractL0Refs(jsonb: unknown): string[] {
  if (!jsonb || typeof jsonb !== 'object') return []
  const src = jsonb as Record<string, unknown>
  const refs: string[] = []

  for (const key of ['catalog_ids', 'rule_ids', 'text_chunk_ids', 'citations']) {
    const arr = src[key]
    if (Array.isArray(arr)) {
      for (const item of arr) {
        if (typeof item === 'string') refs.push(item)
      }
    }
  }

  return refs
}

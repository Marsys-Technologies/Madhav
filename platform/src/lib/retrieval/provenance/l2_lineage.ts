/**
 * L2 lineage detector — "does the L2 (Bodha) output a response is echoing still match the
 * L1 (Gaṇita / chart_facts) generation it was built against?" (N-91 item 3, echo-class
 * between-state disclosure).
 *
 * WHY THIS EXISTS. After an L1 rebuild (S-L1) and before the dependent L2 rebuild (S-L2), L2
 * rows (MSR signals, grounding, ...) still cite `chart_facts.fact_id`s that the L1 rebuild
 * deleted and re-issued. Surfaces that say "grounded in N resolvable L1 fact reference(s)" over
 * those ids would be lying. This module is the REAL detector behind the closed-vocabulary
 * judgment flags `l2_receipts_predate_l1` / `l2_lineage_check_failed` (CLAUDE.md §N.7 item 4 /
 * §N.8: a flag needs a detector that measures the claim, never a banner, env switch or constant).
 *
 * THE RULE (pin rule, not a timestamp comparison). Every L2 provenance receipt persists, in
 * `upstream_receipts`, the exact L1 receipts it was built against (the orchestrator's
 * `load_upstream_receipts` pins each declared dependency's latest-observed receipt for the chart).
 * An L2 lineage pin is STALE iff the pinned `output_digest` differs from the CURRENT L1 receipt's
 * `output_digest` (the same latest-observed selection the orchestrator uses when it pins), or the
 * pinned L1 asset has no current receipt at all.
 *
 *   - Digest, not timestamp: a no-op L1 re-run (`skip_no_delta`) re-stamps `observed_at` to NOW()
 *     with an unchanged digest. A literal "min(L2 observed_at) < max(L1 observed_at)" rule would
 *     re-arm the flag after S-L2 with no id change, and could not say which assets moved.
 *     `observed_at` is carried as evidence only, never as the comparator.
 *   - In scope: only L2 (`bo_*`) receipts for THIS chart that are `proven` AND whose output digest
 *     spec is still active. Legacy `unknown` partitions and retired-spec receipts are never
 *     rewritten, so counting them would hold the flag TRUE forever.
 *   - 'not_applicable' when no in-scope L2 receipt carries an L1 pin (L2 never built: there is no
 *     L2 claim to disclose).
 *   - Fail closed: any error reading or evaluating => 'unknown' (flag `l2_lineage_check_failed`),
 *     NEVER 'current'/false. "Could not check" must not read as "checked clean".
 *
 * KNOWN BLIND SPOT (disclosed): the digest only sees id rotation where the L1 output-digest spec
 * carries the id column. Non-fact id spaces (chart_divisionals.id, dasha_row_id) are not echoed
 * under a "grounded in N resolvable L1 fact reference(s)" sentence and are not covered here.
 *
 * COST / CACHING: one SELECT per call (~1.4 ms measured, ~100 rows in the table). No private
 * cache: every handler that calls this already rides a 60 s result memo (the MCP capability
 * dispatch cache for judgment_query / assess_*; query_signals' own 60 s memo), so a memoised
 * payload carries its own flag. pact_query copies the flag out of its in-process judgment_query
 * result instead of querying again.
 *
 * The layer prefix (`bo_` / `ga_`) is the locked CLAUDE.md §N.1 asset-id convention.
 */
import { query as defaultQuery } from '@/lib/db/client'
import { judgmentFlag, type JudgmentFlag } from '../envelope'

export type L2LineageQueryExecutor = (
  sql: string,
  params?: unknown[],
) => Promise<{ rows: Record<string, unknown>[] }>

export type L2LineageState = 'stale' | 'current' | 'not_applicable' | 'unknown'

/** One L1 pin held inside an L2 receipt's `upstream_receipts`. */
export interface L2LineagePin {
  readonly asset_id: string
  readonly output_digest: string | null
  readonly observed_at: string | null
}

/** One row of the detector's single SELECT (an L2 or L1 provenance receipt). */
export interface L2LineageReceiptRow {
  readonly asset_id: string
  /** null for global (chart-less) receipts; the orchestrator also considers those for L1 pins. */
  readonly chart_id: string | null
  readonly partition_key: string
  readonly receipt_state: string
  readonly observed_at: string | Date | null
  readonly output_digest: string | null
  /** An active (non-retired) output-digest spec exists for the receipt's spec sha. */
  readonly spec_active: boolean
  /** L1 pins held by an L2 receipt; null/absent for L1 rows. */
  readonly l1_pins?: readonly L2LineagePin[] | null
}

export interface L2LineageStaleEntry {
  readonly l2_asset_id: string
  readonly l2_partition_key: string
  readonly l1_asset_id: string
  readonly pinned_output_digest: string | null
  /** null => the pinned L1 asset has no current receipt for this chart. */
  readonly current_output_digest: string | null
  readonly pinned_observed_at: string | null
  readonly current_observed_at: string | null
}

export interface L2LineageResult {
  readonly state: L2LineageState
  readonly stale: readonly L2LineageStaleEntry[]
  /** In-scope (proven, active-spec) L2 receipts that hold at least one L1 pin. */
  readonly l2_receipts_in_scope: number
  readonly l1_pins_checked: number
  /** Set only when state === 'unknown'. */
  readonly error?: string
}

const L1_PREFIX = 'ga_'
const L2_PREFIX = 'bo_'

/**
 * The single SELECT. Returns this chart's L2 and L1 receipts (plus chart-less L1 receipts, which
 * the orchestrator also considers when it pins), with the L1 pins projected out of each L2
 * receipt's `upstream_receipts` and the spec-active flag. Read-only. The comparison is done in
 * TypeScript (`evaluateL2Lineage`, a pure function) so it is fixture-testable.
 */
export const L2_LINEAGE_SQL = `
  SELECT r.asset_id,
         r.chart_id::text AS chart_id,
         r.partition_key,
         r.receipt_state,
         r.observed_at,
         r.output_digest,
         EXISTS (
           SELECT 1 FROM asset_output_digest_specs s
            WHERE s.asset_id = r.asset_id
              AND s.spec_sha256 = r.output_digest_spec_sha256
              AND s.retired_at IS NULL
         ) AS spec_active,
         CASE WHEN left(r.asset_id, 3) = 'bo_' THEN (
           SELECT COALESCE(jsonb_agg(jsonb_build_object(
                    'asset_id', u->>'asset_id',
                    'output_digest', u->>'output_digest',
                    'observed_at', u->>'observed_at')), '[]'::jsonb)
             FROM jsonb_array_elements(
                    CASE WHEN jsonb_typeof(r.upstream_receipts) = 'array'
                         THEN r.upstream_receipts ELSE '[]'::jsonb END) u
            WHERE left(u->>'asset_id', 3) = 'ga_'
         ) END AS l1_pins
    FROM asset_provenance_receipts r
   WHERE (r.chart_id = $1::uuid OR (r.chart_id IS NULL AND left(r.asset_id, 3) = 'ga_'))
     AND left(r.asset_id, 3) IN ('bo_', 'ga_')
`

function toIso(value: string | Date | null | undefined): string | null {
  if (value === null || value === undefined) return null
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value.toISOString()
  return String(value)
}

function toMillis(value: string | Date | null | undefined): number {
  if (value === null || value === undefined) return Number.NEGATIVE_INFINITY
  const ms = (value instanceof Date ? value : new Date(value)).getTime()
  return Number.isNaN(ms) ? Number.NEGATIVE_INFINITY : ms
}

/**
 * Pure: decide the lineage state from the receipt rows of one chart. No I/O, no clock, no
 * environment. See the module header for the rule.
 */
export function evaluateL2Lineage(rows: readonly L2LineageReceiptRow[], chartId: string): L2LineageResult {
  // Current L1 receipt per ga_* asset: the orchestrator's pin-selection rule — chart-scoped
  // receipt preferred over a chart-less one, then latest observed_at (any partition, any state).
  // partition_key is the final deterministic tie-break only.
  const currentL1 = new Map<string, L2LineageReceiptRow>()
  for (const row of rows) {
    if (!row.asset_id.startsWith(L1_PREFIX)) continue
    if (row.chart_id !== null && row.chart_id !== chartId) continue
    const held = currentL1.get(row.asset_id)
    if (!held) {
      currentL1.set(row.asset_id, row)
      continue
    }
    const rowChart = row.chart_id === chartId ? 1 : 0
    const heldChart = held.chart_id === chartId ? 1 : 0
    const better =
      rowChart !== heldChart ? rowChart > heldChart
        : toMillis(row.observed_at) !== toMillis(held.observed_at) ? toMillis(row.observed_at) > toMillis(held.observed_at)
          : row.partition_key < held.partition_key
    if (better) currentL1.set(row.asset_id, row)
  }

  const stale: L2LineageStaleEntry[] = []
  let l2InScope = 0
  let pinsChecked = 0
  for (const row of rows) {
    if (!row.asset_id.startsWith(L2_PREFIX)) continue
    if (row.chart_id !== chartId) continue
    if (row.receipt_state !== 'proven') continue
    if (row.spec_active !== true) continue
    const pins = (row.l1_pins ?? []).filter(pin => pin.asset_id.startsWith(L1_PREFIX))
    if (pins.length === 0) continue
    l2InScope += 1
    for (const pin of pins) {
      pinsChecked += 1
      const current = currentL1.get(pin.asset_id)
      // A pin is stale iff the L1 asset it pinned has no current receipt, or its output digest
      // differs (IS DISTINCT FROM semantics: null equals null). observed_at is evidence only.
      const moved = !current || (current.output_digest ?? null) !== (pin.output_digest ?? null)
      if (moved) {
        stale.push({
          l2_asset_id: row.asset_id,
          l2_partition_key: row.partition_key,
          l1_asset_id: pin.asset_id,
          pinned_output_digest: pin.output_digest ?? null,
          current_output_digest: current ? (current.output_digest ?? null) : null,
          pinned_observed_at: pin.observed_at ?? null,
          current_observed_at: current ? toIso(current.observed_at) : null,
        })
      }
    }
  }

  const state: L2LineageState = stale.length > 0 ? 'stale' : pinsChecked > 0 ? 'current' : 'not_applicable'
  return { state, stale, l2_receipts_in_scope: l2InScope, l1_pins_checked: pinsChecked }
}

function coerceRow(raw: Record<string, unknown>): L2LineageReceiptRow {
  const pinsRaw = raw['l1_pins']
  const pins: L2LineagePin[] = Array.isArray(pinsRaw)
    ? pinsRaw.map(p => {
        const o = (p ?? {}) as Record<string, unknown>
        return {
          asset_id: String(o['asset_id'] ?? ''),
          output_digest: o['output_digest'] == null ? null : String(o['output_digest']),
          observed_at: o['observed_at'] == null ? null : String(o['observed_at']),
        }
      })
    : []
  const observed = raw['observed_at']
  return {
    asset_id: String(raw['asset_id'] ?? ''),
    chart_id: raw['chart_id'] == null ? null : String(raw['chart_id']),
    partition_key: String(raw['partition_key'] ?? ''),
    receipt_state: String(raw['receipt_state'] ?? ''),
    observed_at: observed instanceof Date ? observed : observed == null ? null : String(observed),
    output_digest: raw['output_digest'] == null ? null : String(raw['output_digest']),
    spec_active: raw['spec_active'] === true,
    l1_pins: pins,
  }
}

/**
 * Read the chart's receipts (one SELECT) and evaluate the lineage. NEVER throws and never
 * returns a "clean" result on failure: any read or evaluation error yields state 'unknown'
 * (served as the `l2_lineage_check_failed` flag) — fail closed.
 */
export async function resolveL2Lineage(
  chartId: string,
  exec: L2LineageQueryExecutor = defaultQuery as unknown as L2LineageQueryExecutor,
): Promise<L2LineageResult> {
  try {
    const res = await exec(L2_LINEAGE_SQL, [chartId])
    if (!res || !Array.isArray(res.rows)) throw new Error('lineage query returned no row set')
    return evaluateL2Lineage(res.rows.map(coerceRow), chartId)
  } catch (error) {
    return {
      state: 'unknown',
      stale: [],
      l2_receipts_in_scope: 0,
      l1_pins_checked: 0,
      error: error instanceof Error ? error.message : String(error),
    }
  }
}

const MAX_DETAIL_ENTRIES = 12

/**
 * The served flag for a lineage result, or null when there is nothing to disclose
 * ('current' / 'not_applicable'). 'stale' -> `l2_receipts_predate_l1`; 'unknown' ->
 * `l2_lineage_check_failed` (fail closed: an unchecked lineage is never silently clean).
 */
export function l2LineageFlag(result: L2LineageResult): JudgmentFlag | null {
  if (result.state === 'stale') {
    const l2Assets = Array.from(new Set(result.stale.map(e => e.l2_asset_id))).sort()
    const l1Assets = Array.from(new Set(result.stale.map(e => e.l1_asset_id))).sort()
    const moved = result.stale
      .slice(0, MAX_DETAIL_ENTRIES)
      .map(e => `${e.l1_asset_id} (pinned ${e.pinned_observed_at ?? 'n/a'} -> current ${e.current_observed_at ?? 'no receipt'})`)
    return judgmentFlag(
      'l2_receipts_predate_l1',
      `${l2Assets.length} L2 asset(s) were built against an L1 (chart_facts) generation that has since been ` +
        `rebuilt: ${l2Assets.join(', ')}. L1 asset(s) moved: ${l1Assets.join(', ')}` +
        `${result.stale.length > moved.length ? ' (list truncated)' : ''} [${moved.join('; ')}]. ` +
        'fact_ids cited by L2-derived rows may no longer resolve in chart_facts until L2 is rebuilt.',
      'warning',
    )
  }
  if (result.state === 'unknown') {
    return judgmentFlag(
      'l2_lineage_check_failed',
      'the L2-to-L1 lineage check could not be completed' +
        `${result.error ? ` (${result.error.slice(0, 200)})` : ''}; ` +
        'whether the fact_ids cited by L2-derived rows still resolve in chart_facts is UNKNOWN, not confirmed.',
      'warning',
    )
  }
  return null
}

/** Convenience for handlers: resolve and return the flag (or null) in one call. Never throws. */
export async function resolveL2LineageFlag(
  chartId: string,
  exec?: L2LineageQueryExecutor,
): Promise<{ result: L2LineageResult; flag: JudgmentFlag | null }> {
  const result = await resolveL2Lineage(chartId, exec)
  return { result, flag: l2LineageFlag(result) }
}

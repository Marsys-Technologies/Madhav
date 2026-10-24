/**
 * Why a Kāla layer came back empty (SR-EMPTY-REASON; CLAUDE.md §N.6 rule 4, §N.7.6).
 *
 * An empty convergence / obstruction layer is not one fact. The reader must be able to tell
 *   - the layer was never computed for this chart            -> layer_not_computed
 *   - the layer ran and holds nothing at all                  -> computed_found_none
 *   - rows exist, but only outside the partition served       -> rows_outside_served_generation
 *   - rows exist in the served partition, the filters drop all -> filters_excluded_all_rows
 *   - the state could not be measured                         -> layer_state_unreadable (an honest null)
 * A bare [] (or a zero count) reads as "there is nothing here", which is the claim only the second
 * state may make. Every input below is a count or an asset state read from the database, never a constant.
 */
import { query } from '@/lib/db/client'

export const EMPTY_LAYER_REASONS = [
  'layer_not_computed',
  'computed_found_none',
  'rows_outside_served_generation',
  'filters_excluded_all_rows',
  'layer_state_unreadable',
] as const
export type EmptyLayerReason = typeof EMPTY_LAYER_REASONS[number]

export interface EmptyLayerEvidence {
  /** Rows the chart holds in this table, any partition (legacy, head, candidate). null = not measured. */
  rows_any_partition: number | null
  /** Rows in the partition this surface serves, before any caller filter. null = not measured. */
  rows_served_unfiltered: number | null
  /** asset_throughput.state of the asset that writes the table ('lit' = built); null = no throughput row. */
  asset_state: string | null
  /** false when the table has no single writer asset, so asset_state cannot be consulted. */
  asset_state_measurable: boolean
}

/** Pure classification of an empty result from measured counts. Call it only when the filtered result is empty. */
export function classifyEmptyLayer(e: EmptyLayerEvidence): EmptyLayerReason {
  const served = e.rows_served_unfiltered
  const any = e.rows_any_partition
  if (served === null || any === null || !Number.isFinite(served) || !Number.isFinite(any)) return 'layer_state_unreadable'
  if (served > 0) return 'filters_excluded_all_rows'
  if (any > 0) return 'rows_outside_served_generation'
  if (!e.asset_state_measurable) return 'layer_state_unreadable'
  return e.asset_state === 'lit' ? 'computed_found_none' : 'layer_not_computed'
}

export interface EmptyLayerReading {
  empty_reason: EmptyLayerReason
  /** The measurements behind the reason, so a reader can audit the claim. */
  layer_state: EmptyLayerEvidence
}

/**
 * Measure and classify an empty served layer. `servedFromWhere` is the FROM..WHERE of the served partition
 * for `chart_id = $1` (e.g. "kala_obstruction o WHERE o.chart_id = $1 AND <served predicate>").
 * Never throws: a failed measurement is reported as layer_state_unreadable, not as an empty layer.
 */
export async function readEmptyLayer(opts: {
  table: 'kala_convergence' | 'kala_obstruction'
  asset_id: string
  servedFromWhere: string
  chart_id: string
}): Promise<EmptyLayerReading> {
  const blank: EmptyLayerEvidence = { rows_any_partition: null, rows_served_unfiltered: null, asset_state: null, asset_state_measurable: true }
  try {
    const res = await query<{ any_rows: string | null; served_rows: string | null; asset_state: string | null }>(
      `SELECT (SELECT COUNT(*) FROM ${opts.table} WHERE chart_id = $1)::text AS any_rows,
              (SELECT COUNT(*) FROM ${opts.servedFromWhere})::text AS served_rows,
              (SELECT state FROM asset_throughput WHERE chart_id = $1 AND asset_id = $2 LIMIT 1) AS asset_state`,
      [opts.chart_id, opts.asset_id],
    )
    const row = res.rows[0]
    const count = (v: string | null | undefined) => (v === null || v === undefined || v === '' || !Number.isFinite(Number(v))) ? null : Number(v)
    const layer_state: EmptyLayerEvidence = {
      rows_any_partition: count(row?.any_rows),
      rows_served_unfiltered: count(row?.served_rows),
      asset_state: row?.asset_state ?? null,
      asset_state_measurable: true,
    }
    return { empty_reason: classifyEmptyLayer(layer_state), layer_state }
  } catch {
    return { empty_reason: 'layer_state_unreadable', layer_state: blank }
  }
}

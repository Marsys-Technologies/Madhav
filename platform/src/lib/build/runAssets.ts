import 'server-only'
import { query } from '@/lib/db/client'
import { blockedByAssetIdColumnPresent } from '@/lib/db/columnPresence'

export interface BuildRunAssetRow {
  asset_id: string
  position: number
  state: string
  started_at: string | null
  ended_at: string | null
  error: string | null
  disposition: string | null
  blocked_by_asset_id: string | null
  sanskrit_name: string
  english_name: string
  layer: string
  target_floor: number | null
  rows_written: number | null
}

/** Build owns the run/throughput projection and its pre-1201 compatibility. */
export async function readBuildRunAssets(id: string): Promise<BuildRunAssetRow[]> {
  const includeBlockedBy = await blockedByAssetIdColumnPresent()
  const blockedByCol = includeBlockedBy ? 'bra.blocked_by_asset_id' : 'NULL::text AS blocked_by_asset_id'
  const { rows } = await query<BuildRunAssetRow>(`
      SELECT
        bra.asset_id, bra.position, bra.state, bra.started_at, bra.ended_at,
        COALESCE(bra.error, at2.last_error) AS error,
        bra.disposition, ${blockedByCol},
        ar.sanskrit_name, ar.english_name, ar.layer, ar.target_floor,
        at2.rows_written
      FROM build_run_assets bra
      JOIN build_runs br ON br.id = bra.run_id
      JOIN asset_registry ar ON ar.asset_id = bra.asset_id
      LEFT JOIN LATERAL (
        SELECT last_error, rows_written
        FROM asset_throughput
        WHERE asset_id = bra.asset_id
          AND (chart_id = br.chart_id OR chart_id IS NULL)
        ORDER BY (chart_id IS NOT NULL) DESC
        LIMIT 1
      ) at2 ON true
      WHERE bra.run_id = $1
      ORDER BY bra.position
    `, [id])
  return rows
}

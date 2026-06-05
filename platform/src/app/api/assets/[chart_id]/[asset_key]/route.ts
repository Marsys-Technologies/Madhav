/**
 * GET /api/assets/[chart_id]/[asset_key]
 *
 * Per-asset inspector endpoint for the AssetInspector panel.
 * Queries chart_facts (category = asset_key) and returns:
 *   - asset_key, chart_id, layer, status
 *   - row_count: total rows for this asset
 *   - provenance: ayanamsha_id, build_id, computed_at from most-recent row
 *   - gate_verdict: 'passed' | 'amber' | 'failed'
 *   - sample_rows: first 3 rows
 *
 * Auth: requires authentication (any tier).
 */

import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

// Minimum row count per asset to be considered "passed"
const GATE_FLOOR: Record<string, number> = {
  chart_facts: 10,
  msr: 50,
  cdlm: 1,
  cgm: 1,
  ucn: 1,
  rm: 1,
  panchanga: 1,
}
const DEFAULT_GATE_FLOOR = 1

// Map asset_key prefix to Brahma layer label
function deriveLayer(assetKey: string): string {
  if (assetKey.startsWith('L0') || assetKey === 'brahmagyan' || assetKey === 'chart_facts') {
    return 'L0'
  }
  if (assetKey.startsWith('L1') || assetKey === 'ganita') return 'L1'
  if (assetKey.startsWith('L2') || ['bodha', 'msr', 'ucn', 'cdlm'].includes(assetKey)) return 'L2'
  if (assetKey.startsWith('L3') || ['kala', 'panchanga'].includes(assetKey)) return 'L3'
  if (assetKey.startsWith('L4') || ['phala', 'cgm', 'rm'].includes(assetKey)) return 'L4'
  if (assetKey.startsWith('L5') || assetKey === 'mimamsa') return 'L5'
  return 'L0'
}

type GateVerdict = 'passed' | 'amber' | 'failed'

function computeGateVerdict(rowCount: number, assetKey: string, status: string): GateVerdict {
  if (status === 'failed' || status === 'error') return 'failed'
  const floor = GATE_FLOOR[assetKey] ?? DEFAULT_GATE_FLOOR
  if (rowCount >= floor) return 'passed'
  if (rowCount > 0) return 'amber'
  return 'failed'
}

type Params = Promise<{ chart_id: string; asset_key: string }>

export async function GET(
  req: NextRequest,
  ctx: { params: Params },
): Promise<NextResponse> {
  const { chart_id: chartId, asset_key: assetKey } = await ctx.params

  const user = await getServerUser()
  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  // Get row count and provenance from chart_facts for this asset
  const countResult = await query<{ count: string }>(
    `SELECT COUNT(*) as count
     FROM chart_facts
     WHERE category = $1`,
    [assetKey],
  )
  const rowCount = parseInt(countResult.rows[0]?.count ?? '0', 10)

  // Get provenance from the most recent row
  const provenanceResult = await query<{
    build_id: string
    provenance: Record<string, unknown>
    created_at: string
  }>(
    `SELECT build_id, provenance, created_at
     FROM chart_facts
     WHERE category = $1
     ORDER BY created_at DESC
     LIMIT 1`,
    [assetKey],
  )
  const latestRow = provenanceResult.rows[0] ?? null

  // Get pyramid_layers status for this asset in this chart
  const pyramidResult = await query<{ status: string }>(
    `SELECT status
     FROM pyramid_layers
     WHERE chart_id = $1 AND sublayer = $2
     ORDER BY updated_at DESC
     LIMIT 1`,
    [chartId, assetKey],
  )
  const status = pyramidResult.rows[0]?.status ?? 'not_started'

  // Get sample rows (first 3)
  const sampleResult = await query<{
    fact_id: string
    category: string
    divisional_chart: string
    value_text: string | null
    value_number: number | null
    source_section: string
    build_id: string
    created_at: string
  }>(
    `SELECT fact_id, category, divisional_chart, value_text, value_number, source_section, build_id, created_at
     FROM chart_facts
     WHERE category = $1
     ORDER BY created_at DESC
     LIMIT 3`,
    [assetKey],
  )

  const provenance = latestRow
    ? {
        build_id: latestRow.build_id,
        ayanamsha_id: (latestRow.provenance as Record<string, unknown>)?.ayanamsha_id ?? null,
        computed_at: latestRow.created_at,
      }
    : null

  const gateVerdict = computeGateVerdict(rowCount, assetKey, status)
  const layer = deriveLayer(assetKey)

  return NextResponse.json({
    asset_key: assetKey,
    chart_id: chartId,
    layer,
    status,
    row_count: rowCount,
    provenance,
    gate_verdict: gateVerdict,
    sample_rows: sampleResult.rows,
  })
}

/**
 * GET /api/build/cascade?asset_id=X&chart_id=<uuid>
 *
 * Returns the ordered list of downstream asset_ids that would be invalidated
 * if asset_id is rebuilt. Uses asset_registry.depends_on — the same source as
 * the build path. Previously walked the legacy build_dependencies table (A1..A22
 * scheme) which no longer matches the bg_/ga_/bo_/... asset IDs.
 */

import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { computeDownstreamClosure, type RegistryEntry } from '@/lib/build/plan'

export const dynamic = 'force-dynamic'

interface RegistryRow {
  asset_id: string
  layer: string
  depends_on: string[]
  english_name: string | null
  sort_order: number
}

export async function GET(request: Request): Promise<Response> {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const { searchParams } = new URL(request.url)
  const asset_id = searchParams.get('asset_id')
  const chart_id = searchParams.get('chart_id') // accepted for context; not used in DAG query

  if (!asset_id) {
    return NextResponse.json({ error: 'asset_id is required' }, { status: 400 })
  }

  const { rows } = await query<RegistryRow>(
    `SELECT asset_id, layer, depends_on, english_name, sort_order
       FROM asset_registry
      WHERE is_active = true
      ORDER BY sort_order ASC`,
  )

  const registry: RegistryEntry[] = rows.map(r => ({
    asset_id: r.asset_id,
    layer: r.layer,
    depends_on: r.depends_on ?? [],
    estimated_seconds: null,
  }))

  const downstreamSet = computeDownstreamClosure([asset_id], registry)

  const meta = new Map(rows.map(r => [r.asset_id, r]))
  const downstream = rows
    .filter(r => downstreamSet.has(r.asset_id))
    .map(r => ({
      asset_id: r.asset_id,
      display_name: r.english_name ?? r.asset_id,
      layer: r.layer,
      sort_order: r.sort_order,
    }))

  return NextResponse.json({
    asset_id,
    chart_id,
    downstream,
    total_affected: downstream.length,
  })
}

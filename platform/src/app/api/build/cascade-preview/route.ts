/**
 * GET /api/build/cascade-preview?asset_id=X
 *
 * Returns the transitive downstream closure of an asset using the same
 * asset_registry.depends_on source that the build path uses. Previously
 * walked the legacy build_dependencies table (A1..A22 scheme with phantom
 * columns that 500d on every real call). Now uses computeDownstreamClosure
 * from plan.ts so the cascade preview exactly matches what would be rebuilt.
 */
import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { computeDownstreamClosure, type RegistryEntry } from '@/lib/build/plan'

export const dynamic = 'force-dynamic'

interface RegistryRow {
  asset_id: string
  layer: string
  depends_on: string[]
  sanskrit_name: string
  english_name: string
}

export async function GET(req: NextRequest) {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const assetId = req.nextUrl.searchParams.get('asset_id')
  if (!assetId) return NextResponse.json({ error: 'asset_id required' }, { status: 400 })

  const { rows } = await query<RegistryRow>(
    `SELECT asset_id, layer, depends_on, sanskrit_name, english_name
       FROM asset_registry
      WHERE is_active = true
      ORDER BY
        CASE layer
          WHEN 'brahmagyan' THEN 0
          WHEN 'ganita'     THEN 1
          WHEN 'bodha'      THEN 2
          WHEN 'kala'       THEN 3
          WHEN 'phala'      THEN 4
          WHEN 'mimamsa'    THEN 5
          ELSE 99
        END,
        sort_order`,
  )

  const registry: RegistryEntry[] = rows.map(r => ({
    asset_id: r.asset_id,
    layer: r.layer,
    depends_on: r.depends_on ?? [],
    estimated_seconds: null,
  }))

  const downstreamSet = computeDownstreamClosure([assetId], registry)

  // Preserve DAG order (rows already ordered by layer + sort_order)
  const meta = new Map(rows.map(r => [r.asset_id, r]))
  const descendants = rows
    .filter(r => downstreamSet.has(r.asset_id))
    .map(r => ({
      asset_id: r.asset_id,
      layer: r.layer,
      sanskrit_name: r.sanskrit_name,
      english_name: r.english_name,
    }))

  return NextResponse.json({
    target: assetId,
    target_info: meta.get(assetId)
      ? { layer: meta.get(assetId)!.layer, sanskrit_name: meta.get(assetId)!.sanskrit_name, english_name: meta.get(assetId)!.english_name }
      : null,
    descendants,
    count: descendants.length,
  })
}

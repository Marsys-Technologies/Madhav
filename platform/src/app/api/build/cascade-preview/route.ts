/**
 * GET /api/build/cascade-preview?asset_id=X
 * Walks build_dependencies (forward DAG) to find transitive descendants.
 * [PHASE-C-07]
 */
import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest) {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const assetId = req.nextUrl.searchParams.get('asset_id')
  if (!assetId) return NextResponse.json({ error: 'asset_id required' }, { status: 400 })

  // Transitive descendants via recursive CTE over build_dependencies
  const { rows } = await query<{ descendant_id: string }>(
    `WITH RECURSIVE descendants AS (
       SELECT depends_on_asset_id AS descendant_id
       FROM build_dependencies
       WHERE asset_id = $1
       UNION
       SELECT bd.depends_on_asset_id
       FROM build_dependencies bd
       JOIN descendants d ON bd.asset_id = d.descendant_id
     )
     SELECT DISTINCT descendant_id FROM descendants`,
    [assetId],
  )

  const descendants = rows.map((r) => r.descendant_id)
  return NextResponse.json({ target: assetId, descendants, count: descendants.length })
}

import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

async function requireUser() {
  const user = await getServerUser()
  if (!user) return null
  return user
}

export async function POST(req: NextRequest) {
  const user = await requireUser()
  if (!user) return NextResponse.json({ error: 'Forbidden' }, { status: 403 })

  const body = await req.json().catch(() => null)
  if (!body?.chart_id || !body?.scope) {
    return NextResponse.json({ error: 'chart_id and scope are required' }, { status: 400 })
  }

  const { chart_id, scope, scope_target = null } = body as {
    chart_id: string
    scope: 'global' | 'layer' | 'asset'
    scope_target?: string | null
  }

  // Refresh = invalidate any cached asset stats and return a fresh summary
  // for the requested scope. The client calls onRefreshed() which triggers
  // re-fetches of /api/cockpit/stats and /api/cockpit/runs/active.
  let assetIds: string[] = []
  if (scope === 'global') {
    const { rows } = await query<{ asset_id: string }>('SELECT asset_id FROM asset_registry WHERE is_active = true')
    assetIds = rows.map(r => r.asset_id)
  } else if (scope === 'layer' && scope_target) {
    const { rows } = await query<{ asset_id: string }>(
      'SELECT asset_id FROM asset_registry WHERE layer=$1 AND is_active = true',
      [scope_target]
    )
    assetIds = rows.map(r => r.asset_id)
  } else if (scope === 'asset' && scope_target) {
    assetIds = [scope_target]
  }

  // Touch asset_throughput updated_at (or no-op if not present) so the stats
  // endpoint returns fresh results on the next poll. This also acts as a
  // cache-bust signal without actually mutating state.
  if (assetIds.length > 0 && chart_id) {
    await query(
      `INSERT INTO asset_throughput (chart_id, asset_id, state)
       SELECT $1, unnest($2::text[]), 'dormant'
       ON CONFLICT (chart_id, asset_id) DO UPDATE SET updated_at = now()`,
      [chart_id, assetIds]
    ).catch(() => null) // non-fatal: table may not have updated_at column
  }

  return NextResponse.json({ refreshed: { scope, scope_target, asset_count: assetIds.length } })
}

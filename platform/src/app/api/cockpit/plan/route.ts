import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { resolveBuildPlan, type RegistryEntry, type ThroughputEntry, type BuildAction, type BuildScope } from '@/lib/build/plan'

async function requireSuperAdmin() {
  const user = await getServerUser()
  if (!user) return null
  const { rows } = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [user.uid])
  if (rows[0]?.role !== 'super_admin') return null
  return user
}

export async function POST(req: NextRequest) {
  const user = await requireSuperAdmin()
  if (!user) return NextResponse.json({ error: 'Forbidden' }, { status: 403 })

  const body = await req.json().catch(() => null)
  if (!body?.chart_id || !body?.scope || !body?.action) {
    return NextResponse.json({ error: 'chart_id, scope, and action are required' }, { status: 400 })
  }

  const { chart_id, scope, scope_target = null, action } = body as {
    chart_id: string
    scope: BuildScope
    scope_target?: string | null
    action: BuildAction
  }

  const [registryResult, throughputResult] = await Promise.all([
    query<RegistryEntry>(
      `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on, estimated_seconds
       FROM asset_registry WHERE has_writer = true ORDER BY layer, sort_order`
    ),
    query<ThroughputEntry>(
      // Include BOTH the chart-scoped rows AND the global (chart_id IS NULL) rows so that
      // global assets (L0 bg_*, global services) report their real built state. Without the
      // global rows the resolver treats every built L0 asset as "not built" and wrongly
      // BLOCKS its downstream ("run the Brahmagyan layer first") for any layer/asset-scoped
      // build. DISTINCT ON prefers the chart-scoped row when both exist.
      `SELECT DISTINCT ON (asset_id) asset_id, state
         FROM asset_throughput
        WHERE chart_id=$1 OR chart_id IS NULL
        ORDER BY asset_id, (chart_id = $1) DESC NULLS LAST`,
      [chart_id]
    ),
  ])

  const throughput = new Map(throughputResult.rows.map(r => [r.asset_id, r]))
  const plan = resolveBuildPlan({ scope, scope_target, action, registry: registryResult.rows, throughput })

  return NextResponse.json({ data: plan })
}

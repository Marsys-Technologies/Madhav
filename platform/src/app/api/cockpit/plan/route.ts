import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { resolveBuildPlan, type RegistryEntry, type ThroughputEntry, type BuildAction, type BuildScope } from '@/lib/build/plan'

export async function POST(req: NextRequest) {
  // Plan preview is a read-only operation — any authenticated user may call it.
  // super_admin gate removed so the plan modal works for all users with cockpit access.
  // NOTE: destructive operations (clear, stop, global build) retain their super_admin gates.
  const user = await getServerUser()
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

  try {
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

    // Query historical median duration per asset in the resolved plan
    const medianResult = await query<{ asset_id: string; median_seconds: number }>(
      `SELECT asset_id,
              PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY
                EXTRACT(EPOCH FROM (completed_at - started_at))
              )::numeric AS median_seconds
       FROM build_run_assets
       WHERE asset_id = ANY($1)
         AND completed_at IS NOT NULL
         AND started_at IS NOT NULL
         AND state = 'lit'
       GROUP BY asset_id`,
      [plan.plan]
    )
    const medianByAsset = new Map(medianResult.rows.map(r => [r.asset_id, Number(r.median_seconds)]))

    let estimated_seconds: number | null = 0
    for (const assetId of plan.plan) {
      const perAsset = medianByAsset.get(assetId) ?? null
      if (perAsset === null) { estimated_seconds = null; break }
      estimated_seconds += perAsset
    }

    return NextResponse.json({ data: { ...plan, estimated_seconds } })
  } catch (err) {
    console.error('[cockpit/plan]', err)
    return NextResponse.json({ error: 'db error' }, { status: 500 })
  }
}

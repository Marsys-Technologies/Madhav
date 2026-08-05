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
    const [registryResult, throughputResult, protectedResult] = await Promise.all([
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
      // SHAD-DARSHANA sweep-protection Phase 1a, Layer 1/2 — the planner guard.
      // asset_ids protected for THIS chart_id (build_protected_assets, migration 540).
      // resolveBuildPlan withholds any of these from plan_waves and surfaces them via
      // BuildPlan.protected_assets instead of silently including them in a build/rebuild/
      // update/cascade plan.
      query<{ asset_id: string }>(
        'SELECT asset_id FROM build_protected_assets WHERE chart_id=$1',
        [chart_id]
      ),
    ])

    const throughput = new Map(throughputResult.rows.map(r => [r.asset_id, r]))
    const protectedAssetIds = new Set(protectedResult.rows.map(r => r.asset_id))
    const buildPlan = resolveBuildPlan({ scope, scope_target, action, registry: registryResult.rows, throughput, protectedAssetIds })
    const flatPlan = buildPlan.plan_waves.flat()

    // L-12: Run the same bo_* precondition checks that runs/route.ts performs, so the plan preview
    // shows accurate `blocked`/`blockers` state rather than an optimistic plan that would fail at
    // dispatch time.  Only run when the plan would include Bodha (bo_*) assets.
    const preconditionBlockers: string[] = []
    if (flatPlan.some((id: string) => id.startsWith('bo_'))) {
      const planBuildsL1 = flatPlan.includes('ga_positions') && flatPlan.includes('ga_structural')
      const [chartFactsRes, gaStructuralRes, remedyCorpusRes] = await Promise.all([
        query<{ count: string }>(
          'SELECT count(*)::text AS count FROM chart_facts WHERE chart_id=$1',
          [chart_id]
        ),
        query<{ state: string }>(
          `SELECT state FROM asset_throughput WHERE chart_id=$1 AND asset_id='ga_structural'`,
          [chart_id]
        ),
        query<{ count: string }>(
          'SELECT count(*)::text AS count FROM brahma_remedy_corpus'
        ),
      ])
      if (!planBuildsL1) {
        if (parseInt(chartFactsRes.rows[0]?.count ?? '0', 10) === 0) {
          preconditionBlockers.push('chart_facts is empty — build L1 (Gaṇita) layer first')
        }
        if (gaStructuralRes.rows[0]?.state !== 'lit') {
          preconditionBlockers.push('ga_structural is not lit — build L1 (Gaṇita) layer first')
        }
      }
      if (parseInt(remedyCorpusRes.rows[0]?.count ?? '0', 10) === 0) {
        preconditionBlockers.push('brahma_remedy_corpus is empty — build L0 (Brahmagyan) layer first')
      }
    }

    // Query historical median duration per asset in the resolved plan
    const medianResult = await query<{ asset_id: string; median_seconds: number }>(
      `SELECT asset_id,
              PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY
                EXTRACT(EPOCH FROM (ended_at - started_at))
              )::numeric AS median_seconds
       FROM build_run_assets
       WHERE asset_id = ANY($1)
         AND ended_at IS NOT NULL
         AND started_at IS NOT NULL
         AND state = 'complete'
       GROUP BY asset_id`,
      [flatPlan]
    )
    const medianByAsset = new Map(medianResult.rows.map(r => [r.asset_id, Number(r.median_seconds)]))

    let estimated_seconds: number | null = flatPlan.length === 0 ? null : 0
    for (const assetId of flatPlan) {
      const perAsset = medianByAsset.get(assetId) ?? null
      if (perAsset === null) { estimated_seconds = null; break }
      estimated_seconds = (estimated_seconds ?? 0) + perAsset
    }

    // Include precondition blockers in the response alongside the plan data.
    // `blocked` merges plan-level blocking (upstream stale/error) with precondition blocking.
    const isBlocked = buildPlan.status === 'blocked' || preconditionBlockers.length > 0
    const allBlockers = [
      ...(buildPlan.blockers ?? []),
      ...preconditionBlockers,
    ]

    return NextResponse.json({
      data: {
        ...buildPlan,
        estimated_seconds,
        ...(isBlocked ? { blocked: true, blockers: allBlockers } : {}),
      },
    })
  } catch (err) {
    console.error('[cockpit/plan]', err)
    return NextResponse.json({ error: 'db error' }, { status: 500 })
  }
}

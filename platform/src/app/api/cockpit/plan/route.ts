import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { resolveBuildPlan, type RegistryEntry, type ThroughputEntry, type BuildAction, type BuildScope } from '@/lib/build/plan'
import { COCKPIT_DISPATCHABLE_SERVICE_PROBE_IDS } from '@/lib/cockpit/serviceProbeContract'
import { requireChartPermission } from '@/lib/auth/requireChartPermission'
import { bodhaBuildBlockers, computeNonCandidateAssetIds, loadPlanningInputs, previewDownstreamStaleness } from '@/lib/build/runPreparation'
import { readBodhaRunPreconditions } from '@/lib/build/runRequestData'
import { isPreparationRunScope } from '@/lib/build/preparationRunScope'
import { readPreparationDuration } from '@/lib/build/preparationDuration'

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

  // P2-B-008: per-chart authorization on the caller-supplied chart_id. The
  // "read-only, so any authenticated user may call it" note above is correct about
  // this route being read-only, and about it not needing to be super_admin-only —
  // but read-only was never the question. Applied to an arbitrary chart_id it
  // disclosed a build-state profile of someone else's chart: per-asset built/
  // dormant/stale state, whether chart_facts is populated and ga_structural lit
  // (the bo_* precondition probes), which assets are protected, and historical
  // per-asset build durations.
  //
  // 'read' (permission !== 'deny'), not the 'write' the destructive routes demand:
  // a preview is exactly the kind of read a chart_grants 'view' grant covers, and
  // the plan modal must keep working for view-grantees.
  const denied = await requireChartPermission({
    uid: user.uid,
    chartId: chart_id,
    access: 'read',
  })
  if (denied) return denied

  try {
    const isPreparation = isPreparationRunScope(scope, scope_target)
    const preparationTiming = isPreparation || (body.preparation === true && scope === 'layer'
      && (scope_target === 'ganita' || scope_target === 'bodha'))
    const recoverPreparation = isPreparation && action === 'build'
    const preparationInputs = isPreparation ? await loadPlanningInputs({ query }, chart_id, recoverPreparation) : null
    let buildPlan
    let downstream: string[] = []
    if (preparationInputs) {
      const { registry, throughput, protectedAssetIds, freshness } = preparationInputs
      buildPlan = resolveBuildPlan({
        scope, scope_target, action, registry, throughput, protectedAssetIds, freshness, recoverPreparation,
        nonCandidateAssetIds: computeNonCandidateAssetIds(registry, { scope, allowedScopes: ['per_chart'] }),
      })
      downstream = previewDownstreamStaleness(preparationInputs, buildPlan.plan_waves.flat())
    } else {
      const [registryResult, throughputResult, protectedResult] = await Promise.all([
        query<RegistryEntry>(
          `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on, estimated_seconds
           FROM asset_registry
           WHERE (has_writer = true AND is_active = true)
              OR (
                asset_id = ANY($1::text[])
                AND scope = 'global'
                AND asset_kind = 'service'
                AND asset_type = 'service'
                AND health_probe IS NOT NULL
              )
           ORDER BY layer, sort_order`,
          [COCKPIT_DISPATCHABLE_SERVICE_PROBE_IDS]
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
      buildPlan = resolveBuildPlan({ scope, scope_target, action, registry: registryResult.rows, throughput, protectedAssetIds })
    }
    const flatPlan = buildPlan.plan_waves.flat()

    // L-12: Run the same bo_* precondition checks that runs/route.ts performs, so the plan preview
    // shows accurate `blocked`/`blockers` state rather than an optimistic plan that would fail at
    // dispatch time.  Only run when the plan would include Bodha (bo_*) assets.
    let preconditionBlockers: string[] = []
    if (flatPlan.some((id: string) => id.startsWith('bo_'))) {
      const [chartFactsRes, gaStructuralRes, remedyCorpusRes] = await readBodhaRunPreconditions(chart_id)
      preconditionBlockers = bodhaBuildBlockers(flatPlan, {
        positions: Number(chartFactsRes.rows[0]?.count ?? 0) > 0,
        structure: gaStructuralRes.rows[0]?.state === 'lit',
        remedyCorpus: Number(remedyCorpusRes.rows[0]?.count ?? 0) > 0,
      })
    }

    // Query historical median duration per asset in the resolved plan
    const medianResult = !preparationTiming && flatPlan.length ? await query<{ asset_id: string; median_seconds: number }>(
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
    ) : null
    const estimated_seconds = medianResult?.rows.length === flatPlan.length
      ? medianResult.rows.reduce((sum, row) => sum + Number(row.median_seconds), 0) : null

    // Include precondition blockers in the response alongside the plan data.
    // `blocked` merges plan-level blocking (upstream stale/error) with precondition blocking.
    const isBlocked = buildPlan.status === 'blocked' || preconditionBlockers.length > 0
    const durationHistory = preparationTiming && !isBlocked && flatPlan.length
      ? await readPreparationDuration({ chartId: chart_id, action, scope, target: scope_target, assets: flatPlan,
          registry: preparationInputs?.registry ?? [] })
      : null
    const allBlockers = [
      ...(buildPlan.blockers ?? []),
      ...preconditionBlockers,
    ]

    return NextResponse.json({
      data: {
        ...buildPlan,
        estimated_seconds,
        ...(durationHistory ? { duration_history: durationHistory } : {}),
        ...(isPreparation ? { downstream_may_become_stale: downstream } : {}),
        ...(isBlocked ? { blocked: true, blockers: allBlockers } : {}),
      },
    })
  } catch (err) {
    console.error('[cockpit/plan]', err)
    return NextResponse.json({ error: 'db error' }, { status: 500 })
  }
}

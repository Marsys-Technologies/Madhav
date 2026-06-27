import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { resolveBuildPlan, type RegistryEntry, type ThroughputEntry, type BuildAction, type BuildScope } from '@/lib/build/plan'
import { invokeRunJob } from '@/lib/build/jobInvoker'
import { getJobImageTag } from '@/lib/cloud_run/jobs'

async function requireUser() {
  const user = await getServerUser()
  if (!user) return null
  return user
}

async function getUserRole(uid: string): Promise<string> {
  const { rows } = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [uid])
  return rows[0]?.role ?? 'guest'
}

interface RegistryEntryWithScope extends RegistryEntry {
  scope: string
}

export async function POST(req: NextRequest) {
  const user = await requireUser()
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

  const role = await getUserRole(user.uid)
  const isSuperAdmin = role === 'super_admin'
  const allowedScopes: string[] = isSuperAdmin ? ['per_chart', 'global'] : ['per_chart']

  // Authorization: non-super-admin cannot build L0 layer
  if (!isSuperAdmin && scope === 'layer' && scope_target === 'brahmagyan') {
    return NextResponse.json({ error: 'Only super_admin can build L0 Brahmagyan layer', code: 'FORBIDDEN_L0' }, { status: 403 })
  }

  // Authorization: global/L0 assets are singletons — scope='asset' on a global asset
  // is invalid for everyone (L0 must be built at scope='global' or scope='layer'+'brahmagyan')
  if (scope === 'asset' && scope_target) {
    const { rows: assetRows } = await query<{ scope: string }>(
      'SELECT scope FROM asset_registry WHERE asset_id=$1',
      [scope_target]
    )
    if (assetRows[0]?.scope === 'global') {
      if (!isSuperAdmin) {
        return NextResponse.json({ error: 'Only super_admin can build global assets', code: 'FORBIDDEN_L0' }, { status: 403 })
      }
      // Even super_admin: global assets are singletons, must be built at scope='global'
      return NextResponse.json({ error: 'Global assets must be built at scope=global, not scope=asset', code: 'FORBIDDEN_L0' }, { status: 403 })
    }
  }

  // 409 gate — block if an active run already exists for this chart
  const activeCheck = await query<{ id: string }>(
    `SELECT id FROM build_runs WHERE chart_id=$1 AND state IN ('planned','running','paused') LIMIT 1`,
    [chart_id]
  )
  if (activeCheck.rows.length > 0) {
    return NextResponse.json(
      { error: 'A build is already in progress for this chart', code: 'RUN_ACTIVE', existing_run_id: activeCheck.rows[0].id },
      { status: 409 }
    )
  }

  // Resolve the plan — filter registry by allowedScopes so non-super-admin plans
  // silently exclude all L0/global assets (mirrors clear's filterScopeAssets logic)
  const [registryResult, throughputResult] = await Promise.all([
    query<RegistryEntryWithScope>(
      `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on, estimated_seconds, scope
       FROM asset_registry WHERE is_active = true AND has_writer = true ORDER BY layer, sort_order`
    ),
    query<ThroughputEntry>(
      `SELECT asset_id, state FROM asset_throughput WHERE chart_id=$1`,
      [chart_id]
    ),
  ])

  // Filter registry to allowed scopes — non-super-admin silently excludes L0/global assets
  const allowedRegistry = registryResult.rows.filter(r => allowedScopes.includes(r.scope))

  // L0 GATE (native ruling 2026-06-26): global Build/Rebuild NEVER includes L0 (brahmagyan),
  // regardless of role. L0 is built ONLY via an explicit layer='brahmagyan' trigger or
  // an individual bg_* asset trigger, and only by super_admin.
  const planRegistry = scope === 'global'
    ? allowedRegistry.filter(r => r.layer !== 'brahmagyan')
    : allowedRegistry

  const throughput = new Map(throughputResult.rows.map(r => [r.asset_id, r]))
  const { plan, blocked_assets } = resolveBuildPlan({ scope, scope_target, action, registry: planRegistry, throughput })

  if (plan.length === 0) {
    const allLit = blocked_assets.length === 0
    const detail = blocked_assets.length > 0
      ? { blocked: blocked_assets, hint: 'Build the Brahmagyan layer first, then retry.' }
      : { hint: 'All assets in scope are already built. Use Rebuild to force a full rebuild.' }
    const errMsg = allLit
      ? 'Nothing to build: all assets are already lit. Use action=rebuild to force a rebuild.'
      : 'No assets to build for this scope/action combination'
    return NextResponse.json({ error: errMsg, code: allLit ? 'ALL_LIT' : 'NO_ASSETS', ...detail }, { status: 422 })
  }

  // G4: L1/L0 precondition gate — if plan includes any bo_* assets verify upstream is ready.
  if (plan.some(id => id.startsWith('bo_'))) {
    // Preconditions that will be satisfied by EARLIER assets in the SAME plan must not block.
    // The plan is DAG-ordered (L1 Gaṇita before L2 Bodha), so a global / multi-layer rebuild
    // that already includes the L1 builders will have chart_facts + ga_structural ready by the
    // time Bodha runs. Only gate the L1 preconditions for a plan that does NOT build L1 itself
    // (e.g. a Bodha-only layer/asset build against a chart whose L1 isn't lit). The L0
    // brahma_remedy_corpus check always applies — L0 is never part of an L1–L5 plan.
    const planBuildsL1 = plan.includes('ga_positions') && plan.includes('ga_structural')

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

    const missingPreconditions: string[] = []
    if (!planBuildsL1) {
      if (parseInt(chartFactsRes.rows[0]?.count ?? '0', 10) === 0) {
        missingPreconditions.push('chart_facts is empty — build L1 (Gaṇita) layer first')
      }
      if (gaStructuralRes.rows[0]?.state !== 'lit') {
        missingPreconditions.push('ga_structural is not lit — build L1 (Gaṇita) layer first')
      }
    }
    if (parseInt(remedyCorpusRes.rows[0]?.count ?? '0', 10) === 0) {
      missingPreconditions.push('brahma_remedy_corpus is empty — build L0 (Brahmagyan) layer first')
    }

    if (missingPreconditions.length > 0) {
      return NextResponse.json({
        error: 'Bodha build blocked: upstream preconditions not met',
        code: 'PRECONDITION_FAILED',
        missing: missingPreconditions,
      }, { status: 422 })
    }
  }

  // Create build_run in 'planned' state — orchestrator transitions to 'running'
  const runResult = await query<{ id: string }>(
    `INSERT INTO build_runs (chart_id, scope, scope_target, action, state, plan, triggered_by)
     VALUES ($1, $2, $3, $4, 'planned', $5, $6)
     RETURNING id`,
    [chart_id, scope, scope_target, action, JSON.stringify(plan), user.uid]
  )
  const runId = runResult.rows[0].id

  // Create build_run_assets
  const assetInserts = plan.map((asset_id, i) =>
    query(
      `INSERT INTO build_run_assets (run_id, asset_id, position, state)
       VALUES ($1, $2, $3, 'queued')
       ON CONFLICT (run_id, asset_id) DO NOTHING`,
      [runId, asset_id, i]
    )
  )
  await Promise.all(assetInserts)

  // Fetch the currently deployed job image tag (best-effort; null if GCP unreachable)
  const jobImageTag = await getJobImageTag().catch(() => null)

  // Invoke Cloud Run Job — failure is fatal: mark the run failed so it doesn't orphan as 'planned'
  try {
    await invokeRunJob(runId)
  } catch (err) {
    const errMsg = (err as Error).message
    console.error('[api/cockpit/runs] invokeRunJob failed — marking run failed:', errMsg)
    await query(
      `UPDATE build_runs SET state='failed', ended_at=NOW(), last_error=$1 WHERE id=$2`,
      [errMsg, runId]
    )
    await query(
      `UPDATE build_run_assets SET state='aborted' WHERE run_id=$1 AND state='queued'`,
      [runId]
    )
    return NextResponse.json(
      { error: 'Failed to dispatch build job', detail: errMsg, run_id: runId },
      { status: 503 }
    )
  }

  return NextResponse.json({ data: { run_id: runId, plan, asset_count: plan.length, job_image_tag: jobImageTag, blocked_assets } }, { status: 201 })
}

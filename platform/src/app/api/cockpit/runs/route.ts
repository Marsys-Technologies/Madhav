import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { resolveBuildPlan, type RegistryEntry, type ThroughputEntry, type BuildAction, type BuildScope } from '@/lib/build/plan'
import { invokeRunJob } from '@/lib/build/jobInvoker'

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

  // Resolve the plan
  const [registryResult, throughputResult] = await Promise.all([
    query<RegistryEntry>(
      `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on, estimated_seconds
       FROM asset_registry ORDER BY layer, sort_order`
    ),
    query<ThroughputEntry>(
      `SELECT asset_id, state FROM asset_throughput WHERE chart_id=$1`,
      [chart_id]
    ),
  ])

  const throughput = new Map(throughputResult.rows.map(r => [r.asset_id, r]))
  const { plan } = resolveBuildPlan({ scope, scope_target, action, registry: registryResult.rows, throughput })

  if (plan.length === 0) {
    return NextResponse.json({ error: 'No assets to build for this scope/action combination' }, { status: 422 })
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

  // Invoke Cloud Run Job — non-blocking; failure is non-fatal (watchdog will reap if needed)
  try {
    await invokeRunJob(runId)
  } catch (err) {
    console.warn('[api/cockpit/runs] invokeRunJob failed (non-fatal):', (err as Error).message)
  }

  return NextResponse.json({ data: { run_id: runId, plan, asset_count: plan.length } }, { status: 201 })
}

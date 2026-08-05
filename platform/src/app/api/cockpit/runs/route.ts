import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query, getPool } from '@/lib/db/client'
import { resolveBuildPlan, computeDownstreamClosure, PROTECTED_ASSET_MESSAGE, type RegistryEntry, type ThroughputEntry, type BuildAction, type BuildScope } from '@/lib/build/plan'
import { invokeRunJob } from '@/lib/build/jobInvoker'
import { getJobImageTag } from '@/lib/cloud_run/jobs'
import { filterScopeAssets } from '@/lib/cockpit/clearScopeFilter'
import { deriveDeleteSqlFromCountSql, EXPLICIT_CLEAR_OPS } from '@/lib/cockpit/assetClearSpec'

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
  target_table: string | null
  count_sql: string | null
}

const TABLE_NAME_RE = /^[a-z_][a-z0-9_]{0,62}$/

export async function POST(req: NextRequest) {
  const user = await requireUser()
  if (!user) return NextResponse.json({ error: 'Forbidden' }, { status: 403 })

  const body = await req.json().catch(() => null)
  if (!body?.chart_id || !body?.scope || !body?.action) {
    return NextResponse.json({ error: 'chart_id, scope, and action are required' }, { status: 400 })
  }

  const {
    chart_id,
    scope,
    scope_target = null,
    action,
    clear_before = false,
    force_l0 = false,
  } = body as {
    chart_id: string
    scope: BuildScope
    scope_target?: string | null
    action: BuildAction
    clear_before?: boolean
    force_l0?: boolean
  }

  // Validate scope is a known build scope. asset_set builds a caller-chosen subset of
  // assets for one chart; its scope_target carries a comma-separated asset_id list.
  const VALID_SCOPES: BuildScope[] = ['global', 'layer', 'asset', 'asset_set']
  if (!VALID_SCOPES.includes(scope)) {
    return NextResponse.json({ error: `Invalid scope: ${scope}`, code: 'INVALID_SCOPE' }, { status: 400 })
  }
  if (scope === 'asset_set') {
    const setIds = (scope_target ?? '').split(',').map(s => s.trim()).filter(Boolean)
    if (setIds.length === 0) {
      return NextResponse.json(
        { error: 'scope=asset_set requires scope_target as a non-empty comma-separated asset_id list', code: 'EMPTY_ASSET_SET' },
        { status: 400 }
      )
    }
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

  // Gate 0: 409 — block if an active run already exists for this chart.
  // M-14: Wrapped in SERIALIZABLE transaction to prevent TOCTOU race where two simultaneous
  // POST requests both pass the SELECT check and both INSERT a new run.
  {
    const pool = await getPool()
    const checkClient = await pool.connect()
    try {
      await checkClient.query('BEGIN ISOLATION LEVEL SERIALIZABLE')
      const activeCheck = await checkClient.query<{ id: string }>(
        `SELECT id FROM build_runs WHERE chart_id=$1 AND state IN ('planned','running','paused') LIMIT 1`,
        [chart_id]
      )
      await checkClient.query('COMMIT')
      if (activeCheck.rows.length > 0) {
        return NextResponse.json(
          { error: 'A build is already in progress for this chart', code: 'RUN_ACTIVE', existing_run_id: activeCheck.rows[0].id },
          { status: 409 }
        )
      }
    } catch (err) {
      await checkClient.query('ROLLBACK').catch(() => null)
      throw err
    } finally {
      checkClient.release()
    }
  }

  // Gate 1: L0 double-confirm — when clear_before targets brahmagyan, require explicit force_l0.
  // Returns HTTP 202 so the frontend can surface a second confirmation prompt without treating
  // it as an error. Must run after isSuperAdmin is known (brahmagyan is super_admin-only).
  if (clear_before && scope === 'layer' && scope_target === 'brahmagyan' && !force_l0) {
    return NextResponse.json(
      { requires_double_confirm: true, message: 'This will clear all L0 Brahmagyan data before rebuilding. Confirm?' },
      { status: 202 }
    )
  }

  // Resolve the plan — filter registry by allowedScopes so non-super-admin plans
  // silently exclude all L0/global assets (mirrors clear's filterScopeAssets logic).
  // Also fetch target_table + count_sql for clear-before execution.
  const [registryResult, throughputResult, protectedResult] = await Promise.all([
    query<RegistryEntryWithScope>(
      `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on, estimated_seconds,
              scope, target_table, count_sql
       FROM asset_registry WHERE is_active = true AND has_writer = true ORDER BY layer, sort_order`
    ),
    query<ThroughputEntry>(
      // Include global (chart_id IS NULL) rows alongside chart-scoped so built L0/global
      // assets report 'lit' — otherwise the resolver blocks every layer/asset-scoped build
      // that depends on a built L0 asset. DISTINCT ON prefers the chart-scoped row.
      `SELECT DISTINCT ON (asset_id) asset_id, state
         FROM asset_throughput
        WHERE chart_id=$1 OR chart_id IS NULL
        ORDER BY asset_id, (chart_id = $1) DESC NULLS LAST`,
      [chart_id]
    ),
    // SHAD-DARSHANA sweep-protection Phase 1a, Layer 1/2 — the REAL build-dispatch guard
    // (not merely a preview: this route inserts build_runs and invokes the Cloud Run job).
    // asset_ids protected for THIS chart_id (build_protected_assets, migration 539).
    query<{ asset_id: string }>(
      'SELECT asset_id FROM build_protected_assets WHERE chart_id=$1',
      [chart_id]
    ),
  ])

  const protectedAssetIds = new Set(protectedResult.rows.map(r => r.asset_id))

  // Filter registry to allowed scopes — non-super-admin silently excludes L0/global assets
  const allowedRegistry = registryResult.rows.filter(r => allowedScopes.includes(r.scope))

  // L0 GATE (native ruling 2026-06-26): global Build/Rebuild NEVER includes L0 (brahmagyan),
  // regardless of role. L0 is built ONLY via an explicit layer='brahmagyan' trigger or
  // an individual bg_* asset trigger, and only by super_admin.
  const planRegistry = scope === 'global'
    ? allowedRegistry.filter(r => r.layer !== 'brahmagyan')
    : allowedRegistry

  const throughput = new Map(throughputResult.rows.map(r => [r.asset_id, r]))
  const buildPlan = resolveBuildPlan({ scope, scope_target, action, registry: planRegistry, throughput, protectedAssetIds })
  const plan = buildPlan.plan_waves.flat()

  // Gate 4: Pre-flight gate (built into resolveBuildPlan).
  // Blocks builds where any out-of-plan dep has stale or error data.
  if (buildPlan.status === 'blocked') {
    return NextResponse.json({
      error: 'Build blocked: upstream assets must be rebuilt first',
      code: 'UPSTREAM_BLOCKED',
      blockers: buildPlan.blockers,
      ...(buildPlan.protected_assets.length > 0 ? { protected_assets: buildPlan.protected_assets } : {}),
    }, { status: 422 })
  }

  if (plan.length === 0) {
    // Distinguish an honest "everything withheld as protected" from the ordinary
    // "already lit" no-op — the two have different remedies and must not read the same
    // (a protected asset is never silently folded into "nothing to do").
    if (buildPlan.protected_assets.length > 0) {
      return NextResponse.json({
        error: `Build blocked: every candidate in scope is protected (${PROTECTED_ASSET_MESSAGE})`,
        code: 'PROTECTED',
        protected_assets: buildPlan.protected_assets,
      }, { status: 422 })
    }
    return NextResponse.json({
      error: 'Nothing to build: all assets in scope are already built. Use action=rebuild to force a rebuild.',
      code: 'ALL_LIT',
      hint: 'All assets in scope are already built. Use Rebuild to force a full rebuild.',
    }, { status: 422 })
  }

  // Gate 3: L1/L0 precondition gate — must run against current DB state BEFORE any clear.
  // If plan includes bo_* assets, verify upstream (L1 Gaṇita + L0 remedy corpus) is ready.
  if (plan.some((id: string) => id.startsWith('bo_'))) {
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

  // ── Clear-before-build path ─────────────────────────────────────────────────
  // When clear_before is true: execute the clear atomically with the build_run insert
  // in one pool-client transaction. The clear runs AFTER all read-only gates pass so
  // we never clear data only to fail on a precondition check.
  if (clear_before) {
    // Compute clear scope from the full registry (all scopes, not just has_writer).
    // Exclude brahmagyan unless force_l0 is explicitly set, AND exclude any asset
    // protected for this chart_id — a protected asset is never cleared, whether or
    // not it happens to also be part of the build plan above.
    const fullRegistry = registryResult.rows
    let clearAssets = filterScopeAssets(fullRegistry, scope, scope_target, allowedScopes) as RegistryEntryWithScope[]
    if (!force_l0) {
      clearAssets = clearAssets.filter(a => a.layer !== 'brahmagyan')
    }
    const clearProtectedAssets = clearAssets.filter(a => protectedAssetIds.has(a.asset_id))
    clearAssets = clearAssets.filter(a => !protectedAssetIds.has(a.asset_id))
    const clearAssetIds = clearAssets.map(a => a.asset_id)

    // Compute transitive downstream outside the clear scope → mark stale
    const downstreamSet = computeDownstreamClosure(clearAssetIds, fullRegistry)
    for (const id of clearAssetIds) downstreamSet.delete(id)
    const downstreamAssets = Array.from(downstreamSet)

    const pool = await getPool()
    const client = await pool.connect()
    let runId: string
    try {
      await client.query('BEGIN')

      // Delete data — reverse order for FK safety (downstream first)
      const reversedAssets = [...clearAssets].reverse()
      let spIdx = 0
      for (const asset of reversedAssets) {
        let ops: Array<{ sql: string; params: unknown[] }> | null = null

        if (asset.asset_id in EXPLICIT_CLEAR_OPS) {
          const explicitOps = EXPLICIT_CLEAR_OPS[asset.asset_id]
          if (explicitOps === null) continue  // zero-row service asset — skip cleanly
          ops = explicitOps.map(op => ({
            sql: op.sql,
            params: op.sql.includes('$1') ? [chart_id] : [],
          }))
        } else if (asset.count_sql) {
          const deleteSql = deriveDeleteSqlFromCountSql(asset.count_sql)
          if (deleteSql) {
            ops = [{ sql: deleteSql, params: deleteSql.includes('$1') ? [chart_id] : [] }]
          }
        }

        if (!ops && asset.target_table) {
          if (!TABLE_NAME_RE.test(asset.target_table)) {
            await client.query('ROLLBACK')
            client.release()
            return NextResponse.json({ error: `Invalid target_table: ${asset.target_table}`, code: 'INVALID_TABLE' }, { status: 500 })
          }
          const sql = asset.scope === 'global'
            ? `DELETE FROM ${asset.target_table}`
            : `DELETE FROM ${asset.target_table} WHERE chart_id = $1`
          ops = [{ sql, params: asset.scope === 'global' ? [] : [chart_id] }]
        }

        if (!ops) continue  // no clear spec — skip (non-destructive; build will populate from scratch)

        const sp = `cb_${spIdx++}`
        await client.query(`SAVEPOINT ${sp}`)
        let assetFailed = false
        for (const op of ops) {
          try {
            await client.query(op.sql, op.params)
          } catch (opErr) {
            console.warn(`[runs/clear-before] DELETE failed for ${asset.asset_id}:`, (opErr as Error).message)
            await client.query(`ROLLBACK TO SAVEPOINT ${sp}`)
            await client.query(`RELEASE SAVEPOINT ${sp}`)
            assetFailed = true
            break
          }
        }
        if (!assetFailed) {
          await client.query(`RELEASE SAVEPOINT ${sp}`)
        }
      }

      // Reset throughput to dormant for all cleared assets (chart-scoped)
      if (clearAssetIds.length > 0) {
        await client.query(
          `UPDATE asset_throughput
           SET state='dormant', last_built_at=NULL, rows_written=NULL,
               built_against_upstream_hash=NULL, built_against_writer_hash=NULL,
               last_error=NULL
           WHERE chart_id=$1 AND asset_id = ANY($2::text[])`,
          [chart_id, clearAssetIds]
        )
        // Also reset global-scope throughput rows (chart_id IS NULL)
        const globalClearIds = clearAssets.filter(a => a.scope === 'global').map(a => a.asset_id)
        if (globalClearIds.length > 0) {
          await client.query(
            `UPDATE asset_throughput
             SET state='dormant', last_built_at=NULL, rows_written=NULL,
                 built_against_upstream_hash=NULL, built_against_writer_hash=NULL,
                 last_error=NULL
             WHERE chart_id IS NULL AND asset_id = ANY($1::text[])`,
            [globalClearIds]
          )
        }
      }

      // Mark transitive downstream as stale (only currently-built assets)
      if (downstreamAssets.length > 0) {
        await client.query(
          `UPDATE asset_throughput SET state='stale'
           WHERE chart_id=$1 AND asset_id = ANY($2::text[]) AND state IN ('lit','building','error')`,
          [chart_id, downstreamAssets]
        )
      }

      // Insert build_run within the same transaction
      const runRes = await client.query<{ id: string }>(
        `INSERT INTO build_runs (chart_id, scope, scope_target, action, state, plan, triggered_by)
         VALUES ($1, $2, $3, $4, 'planned', $5, $6) RETURNING id`,
        [chart_id, scope, scope_target, action, JSON.stringify(plan), user.uid]
      )
      runId = runRes.rows[0].id

      // Insert build_run_assets within the same transaction
      const placeholders = plan.map((_, i) =>
        `($1, $${i * 3 + 2}, $${i * 3 + 3}, $${i * 3 + 4})`
      ).join(', ')
      const flatParams = [runId, ...plan.flatMap((asset_id, i) => [asset_id, i, 'queued'])]
      await client.query(
        `INSERT INTO build_run_assets (run_id, asset_id, position, state) VALUES ${placeholders}
         ON CONFLICT (run_id, asset_id) DO NOTHING`,
        flatParams
      )

      await client.query('COMMIT')
    } catch (outerErr) {
      await client.query('ROLLBACK').catch(() => null)
      console.error('[api/cockpit/runs] clear-before transaction failed:', outerErr)
      return NextResponse.json({
        error: 'Clear-before-build transaction failed; rolled back.',
        code: 'CLEAR_TRANSACTION_FAILED',
        detail: ((outerErr as Error).message ?? 'unknown').substring(0, 200),
      }, { status: 500 })
    } finally {
      client.release()
    }

    // Invoke the job OUTSIDE the transaction — Cloud Run invocations cannot be rolled back
    const jobImageTag = await getJobImageTag().catch(() => null)
    try {
      await invokeRunJob(runId)
      // M-1: Do NOT pre-mark as 'running' here. The run stays in 'planned' until the orchestrator
      // itself transitions it to 'running' after acquiring the chart advisory lock. This prevents
      // a phantom 'running' state when the spawned process never actually starts.
    } catch (err) {
      const errMsg = (err as Error).message
      console.error('[api/cockpit/runs] invokeRunJob failed after clear — marking run failed:', errMsg)
      await query(`UPDATE build_runs SET state='failed', ended_at=NOW(), last_error=$1 WHERE id=$2`, [errMsg, runId])
      await query(`UPDATE build_run_assets SET state='aborted' WHERE run_id=$1 AND state='queued'`, [runId])
      // Note: data was already cleared; user will need to rebuild again after fixing the job issue
      return NextResponse.json(
        { error: 'Data cleared but build job failed to start', detail: errMsg, run_id: runId, code: 'JOB_DISPATCH_FAILED' },
        { status: 503 }
      )
    }

    return NextResponse.json({
      data: {
        run_id: runId, plan, asset_count: plan.length, job_image_tag: jobImageTag, cleared_asset_count: clearAssetIds.length,
        ...(buildPlan.protected_assets.length > 0 || clearProtectedAssets.length > 0
          ? { protected_assets: buildPlan.protected_assets }
          : {}),
      },
    }, { status: 201 })
  }

  // ── Standard build path (no clear_before) ───────────────────────────────────
  const runResult = await query<{ id: string }>(
    `INSERT INTO build_runs (chart_id, scope, scope_target, action, state, plan, triggered_by)
     VALUES ($1, $2, $3, $4, 'planned', $5, $6)
     RETURNING id`,
    [chart_id, scope, scope_target, action, JSON.stringify(plan), user.uid]
  )
  const runId = runResult.rows[0].id

  // Create build_run_assets — single multi-row INSERT instead of N parallel queries
  const placeholders = plan.map((_, i) =>
    `($1, $${i * 3 + 2}, $${i * 3 + 3}, $${i * 3 + 4})`
  ).join(', ')
  const flatParams = [runId, ...plan.flatMap((asset_id, i) => [asset_id, i, 'queued'])]
  await query(
    `INSERT INTO build_run_assets (run_id, asset_id, position, state) VALUES ${placeholders}
     ON CONFLICT (run_id, asset_id) DO NOTHING`,
    flatParams
  )

  // Fetch the currently deployed job image tag (best-effort; null if GCP unreachable)
  const jobImageTag = await getJobImageTag().catch(() => null)

  // Invoke Cloud Run Job — failure is fatal: mark the run failed so it doesn't orphan as 'planned'
  try {
    await invokeRunJob(runId)
    // M-1: Do NOT pre-mark as 'running' here. The run stays in 'planned' until the orchestrator
    // itself transitions it to 'running' after acquiring the chart advisory lock. The watchdog's
    // "planned > 10 min with no transition" reaper handles the case where the orchestrator never
    // starts (undispatched run reaper already present in watchdog/route.ts).
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

  return NextResponse.json({
    data: {
      run_id: runId, plan, asset_count: plan.length, job_image_tag: jobImageTag,
      ...(buildPlan.protected_assets.length > 0 ? { protected_assets: buildPlan.protected_assets } : {}),
    },
  }, { status: 201 })
}

export async function GET(req: NextRequest) {
  const user = await requireUser()
  if (!user) return NextResponse.json({ error: 'Forbidden' }, { status: 403 })

  const chart_id = req.nextUrl.searchParams.get('chart_id')
  if (!chart_id) return NextResponse.json({ error: 'chart_id query param required' }, { status: 400 })

  try {
    const { rows } = await query<{
      id: string
      scope: string
      scope_target: string | null
      action: string
      state: string
      created_at: string
      ended_at: string | null
      last_error: string | null
    }>(
      `SELECT id, scope, scope_target, action, state, created_at, ended_at, last_error
         FROM build_runs
        WHERE chart_id = $1
        ORDER BY created_at DESC
        LIMIT 20`,
      [chart_id]
    )
    return NextResponse.json({ data: rows })
  } catch (err) {
    console.error('[cockpit/runs GET]', err)
    return NextResponse.json({ data: [] })
  }
}

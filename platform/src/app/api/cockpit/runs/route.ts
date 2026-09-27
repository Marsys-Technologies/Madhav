import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query, getPool } from '@/lib/db/client'
import { computeDownstreamClosure, PROTECTED_ASSET_MESSAGE, type BuildAction, type BuildScope } from '@/lib/build/plan'
import { getJobImageTag } from '@/lib/cloud_run/jobs'
import { filterScopeAssets } from '@/lib/cockpit/clearScopeFilter'
import { isCockpitDispatchableServiceProbe } from '@/lib/cockpit/serviceProbeContract'
import { requireChartPermission } from '@/lib/auth/requireChartPermission'
import {
  BuildPreparationError,
  computeNonCandidateAssetIds,
  findActiveRun,
  freezeRunManifest,
  isActiveRunConflict,
  loadPlanningInputs,
  persistPreparedRun,
  planRun,
  type RegistryEntryWithScope,
} from '@/lib/build/runPreparation'
import { invalidateAssets, InvalidationError } from '@/lib/build/assetInvalidation'
import { dispatchPreparedRun } from '@/lib/build/runDispatch'

async function requireUser() {
  const user = await getServerUser()
  if (!user) return null
  return user
}

async function getUserRole(uid: string): Promise<string> {
  const { rows } = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [uid])
  return rows[0]?.role ?? 'guest'
}

/** Pool-level reads for the planner, in the same order the route has always issued them. */
const pooled = { query }

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
  const requestedAssetSet = scope === 'asset_set'
    ? (scope_target ?? '').split(',').map(s => s.trim()).filter(Boolean)
    : []
  if (scope === 'asset_set') {
    if (requestedAssetSet.length === 0) {
      return NextResponse.json(
        { error: 'scope=asset_set requires scope_target as a non-empty comma-separated asset_id list', code: 'EMPTY_ASSET_SET' },
        { status: 400 }
      )
    }
  }

  const role = await getUserRole(user.uid)
  const isSuperAdmin = role === 'super_admin'

  // P2-B-008: per-chart authorization on the caller-supplied chart_id, BEFORE any
  // gate, transaction, or dispatch. This route used to check only "is there a
  // logged-in user", which made it the most dangerous instance of the B-001/B-007
  // family — and strictly worse than B-007's pre-fix state, because B-007 at least
  // required a preview_hash round-trip before its DELETE. Here a SINGLE request
  // with `clear_before: true` ran `DELETE FROM <target_table> WHERE chart_id=$1`
  // across every build-derived table of an arbitrary chart, reset its
  // asset_throughput to dormant, marked downstream stale, and then dispatched a
  // Cloud Run build job billed against the victim's chart — with no confirmation
  // step of any kind. The non-clearing path is a cross-tenant write too (it
  // INSERTs build_runs / build_run_assets and invokes the job).
  //
  // 'write' (permission === 'all': owner or super_admin) is required, not merely
  // non-'deny': dispatch and clear are destructive, so a chart_grants 'view'
  // grantee must not pass. This mirrors the Nirmāṇa page guard, which already
  // gates the cockpit UI on canBuild === (permission === 'all'), and matches the
  // Clear routes' gate exactly (P2-B-007, PR #1602).
  const denied = await requireChartPermission({
    uid: user.uid,
    role: isSuperAdmin ? 'super_admin' : 'guest',
    chartId: chart_id,
    access: 'write',
  })
  if (denied) return denied

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
      const activeRunId = await findActiveRun(checkClient, chart_id)
      await checkClient.query('COMMIT')
      if (activeRunId) {
        return NextResponse.json(
          { error: 'A build is already in progress for this chart', code: 'RUN_ACTIVE', existing_run_id: activeRunId },
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

  // Resolve the plan — the registry is filtered by allowedScopes so non-super-admin
  // plans silently exclude all L0/global assets (mirrors clear's filterScopeAssets logic).
  // Shared with the chart-correction transaction (lib/build/runPreparation).
  const inputs = await loadPlanningInputs(pooled, chart_id)
  const registryRows = inputs.registry
  const protectedAssetIds = inputs.protectedAssetIds

  // A no-writer service has a health probe rather than a WriterBase implementation.
  // It is eligible only as one explicit, non-destructive global asset_set selected by
  // a super_admin. The fixed manifest-derived allowlist admits the frozen
  // Ephemeris and Panchanga probes without making arbitrary service rows or an
  // entire L0 layer dispatchable by accident.
  const requestedServiceProbes = requestedAssetSet
    .map(assetId => registryRows.find(row => row.asset_id === assetId))
    .filter((row): row is RegistryEntryWithScope => Boolean(row && isCockpitDispatchableServiceProbe(row)))
  if (requestedServiceProbes.length > 0) {
    if (!isSuperAdmin) {
      return NextResponse.json(
        { error: 'Only super_admin can run a global service health probe', code: 'FORBIDDEN_SERVICE_PROBE' },
        { status: 403 },
      )
    }
    if (requestedAssetSet.length !== 1 || requestedServiceProbes.length !== 1) {
      return NextResponse.json(
        { error: 'A global service health probe requires exactly one asset_set target', code: 'INVALID_SERVICE_PROBE_SCOPE' },
        { status: 422 },
      )
    }
    if (clear_before) {
      return NextResponse.json(
        { error: 'Service health probes cannot clear data', code: 'SERVICE_PROBE_CLEAR_FORBIDDEN' },
        { status: 400 },
      )
    }
  }

  const nonCandidateAssetIds = computeNonCandidateAssetIds(registryRows, {
    allowedScopes,
    scope,
    serviceProbeIds: new Set(requestedServiceProbes.map(row => row.asset_id)),
  })

  let buildPlan: ReturnType<typeof planRun>['buildPlan']
  let plan: string[]
  let frozen: ReturnType<typeof freezeRunManifest>
  try {
    ;({ buildPlan, plan } = planRun({ inputs, scope, scopeTarget: scope_target, action, nonCandidateAssetIds }))
    // Freeze exactly what this dispatch accepted. `asset_registry` remains mutable
    // operational metadata, so the runner must never re-plan a queued run from it.
    frozen = freezeRunManifest({
      chartId: chart_id, scope, scopeTarget: scope_target, action, planWaves: buildPlan.plan_waves, registry: registryRows,
    })
  } catch (error) {
    if (!(error instanceof BuildPreparationError)) throw error
    const protectedAssets = (error.details.protected_assets ?? []) as unknown[]
    switch (error.code) {
      // Gate 4: Pre-flight gate (built into resolveBuildPlan).
      // Blocks builds where any out-of-plan dep has stale or error data.
      case 'UPSTREAM_BLOCKED':
        return NextResponse.json({
          error: 'Build blocked: upstream assets must be rebuilt first',
          code: 'UPSTREAM_BLOCKED',
          blockers: error.details.blockers,
          ...(protectedAssets.length > 0 ? { protected_assets: protectedAssets } : {}),
        }, { status: 422 })
      // Distinguish an honest "everything withheld as protected" from the ordinary
      // "already lit" no-op — the two have different remedies and must not read the same.
      case 'PROTECTED':
        return NextResponse.json({
          error: `Build blocked: every candidate in scope is protected (${PROTECTED_ASSET_MESSAGE})`,
          code: 'PROTECTED',
          protected_assets: protectedAssets,
        }, { status: 422 })
      case 'ALL_LIT':
        return NextResponse.json({
          error: 'Nothing to build: all assets in scope are already built. Use action=rebuild to force a rebuild.',
          code: 'ALL_LIT',
          hint: 'All assets in scope are already built. Use Rebuild to force a full rebuild.',
        }, { status: 422 })
      case 'INVALID_BUILD_PLAN':
      case 'CODE_DIGEST_UNAVAILABLE':
        return NextResponse.json({ error: error.message, code: error.code }, { status: 422 })
      default:
        throw error
    }
  }
  const prepared = {
    chartId: chart_id, scope, scopeTarget: scope_target, action, plan,
    manifest: frozen.manifest, manifestDigest: frozen.digest,
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
    const fullRegistry = registryRows
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

      // Delete data — reverse order for FK safety (downstream first), each asset in
      // its own savepoint: the operator clear stays best effort.
      await invalidateAssets({ db: client, chartId: chart_id, assets: clearAssets, policy: 'operator-best-effort' })

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

      // Insert build_run and its queued assets within the same transaction
      runId = await persistPreparedRun(client, prepared, user.uid)

      await client.query('COMMIT')
    } catch (outerErr) {
      await client.query('ROLLBACK').catch(() => null)
      if (outerErr instanceof InvalidationError && outerErr.code === 'INVALID_TABLE') {
        return NextResponse.json({ error: outerErr.message, code: 'INVALID_TABLE' }, { status: 500 })
      }
      if (isActiveRunConflict(outerErr)) {
        return NextResponse.json(
          { error: 'A build is already in progress for this chart', code: 'RUN_ACTIVE' },
          { status: 409 },
        )
      }
      console.error('[api/cockpit/runs] clear-before transaction failed:', outerErr)
      return NextResponse.json({
        error: 'Clear-before-build transaction failed; rolled back.',
        code: 'CLEAR_TRANSACTION_FAILED',
        detail: ((outerErr as Error).message ?? 'unknown').substring(0, 200),
      }, { status: 500 })
    } finally {
      client.release()
    }

    // Invoke the job OUTSIDE the transaction — Cloud Run invocations cannot be rolled back.
    // M-1: the run stays 'planned' until the orchestrator itself transitions it to
    // 'running' after acquiring the chart advisory lock.
    const jobImageTag = await getJobImageTag().catch(() => null)
    const dispatch = await dispatchPreparedRun(runId)
    if (!dispatch.ok) {
      console.error('[api/cockpit/runs] invokeRunJob failed after clear — run marked failed:', dispatch.message)
      // Note: data was already cleared; user will need to rebuild again after fixing the job issue
      return NextResponse.json(
        { error: 'Data cleared but build job failed to start', detail: dispatch.message, run_id: runId, code: 'JOB_DISPATCH_FAILED' },
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
  const pool = await getPool()
  const client = await pool.connect()
  let runId: string
  try {
    await client.query('BEGIN')
    // Persist the run and its receipts atomically: a planned run never exists
    // without the exact per-asset rows the runner and tracker require.
    runId = await persistPreparedRun(client, prepared, user.uid)
    await client.query('COMMIT')
  } catch (error) {
    await client.query('ROLLBACK').catch(() => null)
    if (isActiveRunConflict(error)) {
      return NextResponse.json(
        { error: 'A build is already in progress for this chart', code: 'RUN_ACTIVE' },
        { status: 409 },
      )
    }
    throw error
  } finally {
    client.release()
  }

  // Fetch the currently deployed job image tag (best-effort; null if GCP unreachable)
  const jobImageTag = await getJobImageTag().catch(() => null)

  // Invoke the job — failure is fatal: the run is marked failed so it doesn't orphan as 'planned'.
  // M-1: no pre-mark as 'running'; the watchdog's undispatched-run reaper covers a run the
  // orchestrator never starts.
  const dispatch = await dispatchPreparedRun(runId)
  if (!dispatch.ok) {
    console.error('[api/cockpit/runs] invokeRunJob failed — run marked failed:', dispatch.message)
    return NextResponse.json(
      { error: 'Failed to dispatch build job', detail: dispatch.message, run_id: runId },
      { status: 503 }
    )
  }

  return NextResponse.json({
    data: {
      run_id: runId, plan, asset_count: plan.length, job_image_tag: jobImageTag,
      ...(buildPlan.protected_assets.length > 0 ? { protected_assets: buildPlan.protected_assets } : {}),
      // O-wave WP-3 disposition pass-through (plan §3.3; "the cockpit run view
      // renders dispositions -- minimal now, polish in WP-5"). Map -> plain
      // object: JSON.stringify silently drops a Map's entries otherwise.
      // Present only for scope='layer', matching resolveBuildPlan's own scoping.
      ...(buildPlan.dispositions
        ? { dispositions: Object.fromEntries(buildPlan.dispositions) }
        : {}),
    },
  }, { status: 201 })
}

export async function GET(req: NextRequest) {
  const user = await requireUser()
  if (!user) return NextResponse.json({ error: 'Forbidden' }, { status: 403 })

  const chart_id = req.nextUrl.searchParams.get('chart_id')
  if (!chart_id) return NextResponse.json({ error: 'chart_id query param required' }, { status: 400 })

  // P2-B-008: this GET returned the last 20 build runs — states, timings, and
  // last_error strings — for ANY caller-supplied chart_id to any logged-in user.
  // 'read' (permission !== 'deny') is the right level here rather than the 'write'
  // the POST demands: reading build history is exactly what a chart_grants 'view'
  // grant is meant to cover.
  const denied = await requireChartPermission({ uid: user.uid, chartId: chart_id, access: 'read' })
  if (denied) return denied

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

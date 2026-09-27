import 'server-only'
import { createHash } from 'crypto'
import type { QueryResult, QueryResultRow } from 'pg'
import {
  resolveBuildPlan,
  type BuildAction,
  type BuildPlan,
  type BuildScope,
  type RegistryEntry,
  type ThroughputEntry,
} from '@/lib/build/plan'
import { filterScopeAssets } from '@/lib/cockpit/clearScopeFilter'
import writerDigestInventory from '@/generated/nirmana-writer-digests.json'

/**
 * Shared build-run preparation (Jātaka chart workspace, Task 5).
 *
 * One home for the planner inputs, frozen-manifest rules and run persistence
 * that `POST /api/cockpit/runs` and the chart-correction transaction both use.
 * Every function takes a `Queryable` so a caller can run it on its own
 * transaction client; nothing here opens or commits a transaction. This is a
 * Next.js server boundary around the already-governed build machinery — the
 * frozen Python orchestrator contract is unchanged.
 */

export interface Queryable {
  query<R extends QueryResultRow = QueryResultRow>(sql: string, params?: unknown[]): Promise<QueryResult<R>>
}

export type ClearPolicy = 'none' | 'operator-best-effort' | 'chart-correction-strict'

export interface RegistryEntryWithScope extends RegistryEntry {
  scope: string
  has_writer: boolean
  target_table: string | null
  count_sql: string | null
  natural_key_partition: string | null
  asset_kind: 'data' | 'artifact' | 'service'
  asset_type: 'data' | 'artifact' | 'service'
  health_probe: Record<string, unknown> | null
}

export interface FreshnessRow {
  asset_id: string
  state: 'fresh' | 'stale' | 'unknown'
  reasons: string[]
}

export type FrozenManifestAsset = {
  asset_id: string
  scope: string
  depends_on: string[]
  natural_key_partition: string | null
  has_cowriters: boolean
  expected_code_digest: string
}

export type FrozenRunManifest = {
  version: 'nirmana-run-manifest/v1'
  chart_id: string
  scope: BuildScope
  scope_target: string | null
  action: BuildAction
  waves: string[][]
  assets: FrozenManifestAsset[]
}

export type BuildPreparationCode =
  | 'RUN_ACTIVE'
  | 'PROTECTED'
  | 'UPSTREAM_BLOCKED'
  | 'ALL_LIT'
  | 'INVALID_BUILD_PLAN'
  | 'CODE_DIGEST_UNAVAILABLE'
  | 'CLEAR_SPEC_MISSING'

export class BuildPreparationError extends Error {
  constructor(
    readonly code: BuildPreparationCode,
    message: string,
    readonly details: Record<string, unknown> = {},
  ) {
    super(message)
    this.name = 'BuildPreparationError'
  }
}

export interface RunPreparationRequest {
  chartId: string
  scope: BuildScope
  scopeTarget: string | null
  action: BuildAction
  allowedScopes: string[]
  clearPolicy: ClearPolicy
  triggeredBy: string
  /**
   * Chart correction: every candidate in scope must be planned. A withheld
   * (protected) candidate or a plan that does not cover every active per-chart
   * writer is a failure, never a partial rebuild.
   */
  requireCompletePlan?: boolean
}

export interface PreparedRun {
  chartId: string
  scope: BuildScope
  scopeTarget: string | null
  action: BuildAction
  plan: string[]
  planWaves: string[][]
  registry: RegistryEntryWithScope[]
  /** Assets offered to the invalidation policy, in dependency order (upstream first). */
  clearAssets: RegistryEntryWithScope[]
  protectedAssets: string[]
  manifest: FrozenRunManifest
  manifestDigest: string
}

export interface PlanningInputs {
  registry: RegistryEntryWithScope[]
  throughput: Map<string, ThroughputEntry>
  protectedAssetIds: Set<string>
  freshness: Map<string, { state: FreshnessRow['state']; reasons: string[] }>
}

const EXPECTED_WRITER_DIGESTS = writerDigestInventory.writers as Record<string, string>

export function expectedCodeDigest(entry: RegistryEntryWithScope | undefined): string | null {
  if (!entry) return null
  const writerDigest = EXPECTED_WRITER_DIGESTS[entry.asset_id]
  if (writerDigest) return writerDigest
  return entry.asset_kind === 'service' ? writerDigestInventory.probe_digest : null
}

/**
 * Serializes values identically in the dispatcher and the Python runner: object
 * keys are lexical, while arrays retain the execution order they were given.
 * Manifest values are IDs/enums only, so the shared ASCII JSON representation is
 * deliberate and avoids a JSONB key-order dependency at read time.
 */
export function canonicalManifestJson(value: unknown): string {
  const normalize = (input: unknown): unknown => {
    if (Array.isArray(input)) return input.map(normalize)
    if (input !== null && typeof input === 'object') {
      const record = input as Record<string, unknown>
      return Object.fromEntries(Object.keys(record).sort().map((key) => [key, normalize(record[key])]))
    }
    return input
  }
  const serialized = JSON.stringify(normalize(value))
  if (serialized === undefined) throw new TypeError('Frozen manifest must be JSON-serializable')
  return serialized
}

export function manifestDigest(manifest: FrozenRunManifest): string {
  return createHash('sha256').update(canonicalManifestJson(manifest), 'utf8').digest('hex')
}

export function isActiveRunConflict(error: unknown): boolean {
  const pg = error as { code?: string; constraint?: string }
  return pg?.code === '23505' && pg?.constraint === 'build_runs_one_active_per_chart_idx'
}

/** Returns the id of a planned/running/paused run for the chart, or null. */
export async function findActiveRun(db: Queryable, chartId: string): Promise<string | null> {
  const { rows } = await db.query<{ id: string }>(
    `SELECT id FROM build_runs WHERE chart_id=$1 AND state IN ('planned','running','paused') LIMIT 1`,
    [chartId],
  )
  return rows[0]?.id ?? null
}

export async function loadPlanningInputs(db: Queryable, chartId: string): Promise<PlanningInputs> {
  const [registryResult, throughputResult, protectedResult, freshnessResult] = await Promise.all([
    db.query<RegistryEntryWithScope>(
      // domain (migration 590): O-wave WP-3's layer-sweep domain exclusion
      // (NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §3.3) reads this directly.
      `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on, estimated_seconds,
              scope, has_writer, target_table, count_sql, natural_key_partition,
              asset_kind, asset_type, health_probe, domain
       FROM asset_registry
       WHERE is_active = true
       ORDER BY layer, sort_order`,
    ),
    db.query<ThroughputEntry>(
      // Include global (chart_id IS NULL) rows alongside chart-scoped so built L0/global
      // assets report 'lit' — otherwise the resolver blocks every layer/asset-scoped build
      // that depends on a built L0 asset. DISTINCT ON prefers the chart-scoped row.
      `SELECT DISTINCT ON (asset_id) asset_id, state
         FROM asset_throughput
        WHERE chart_id=$1 OR chart_id IS NULL
        ORDER BY asset_id, (chart_id = $1) DESC NULLS LAST`,
      [chartId],
    ),
    // SHAD-DARSHANA sweep-protection Phase 1a, Layer 1/2 — asset_ids protected for
    // THIS chart_id (build_protected_assets, migration 540).
    db.query<{ asset_id: string }>('SELECT asset_id FROM build_protected_assets WHERE chart_id=$1', [chartId]),
    db.query<FreshnessRow>(
      `SELECT DISTINCT ON (asset_id)
              af.asset_id, af.freshness_state AS state, af.reasons
         FROM asset_freshness af
        WHERE af.chart_id=$1 OR af.chart_id IS NULL
        ORDER BY af.asset_id, (af.chart_id = $1) DESC NULLS LAST, af.observed_at DESC`,
      [chartId],
    ),
  ])

  // O-wave WP-1 ("one authority"): trust the sidecar's own receipt classification
  // (af.freshness_state) directly. A missing freshness row reads as "needs build"
  // inside resolveBuildPlan.
  return {
    registry: registryResult.rows,
    throughput: new Map(throughputResult.rows.map((r) => [r.asset_id, r])),
    protectedAssetIds: new Set(protectedResult.rows.map((r) => r.asset_id)),
    freshness: new Map(
      freshnessResult.rows.map((r) => [r.asset_id, { state: r.state, reasons: Array.isArray(r.reasons) ? r.reasons : [] }]),
    ),
  }
}

/**
 * Candidate restrictions are exclusions rather than dropped dependency
 * identities: an otherwise-authorized per-chart asset can still fail closed on
 * its global L0/service prerequisite.
 */
export function computeNonCandidateAssetIds(
  registry: RegistryEntryWithScope[],
  args: { allowedScopes: string[]; scope: BuildScope; serviceProbeIds?: ReadonlySet<string> },
): Set<string> {
  return new Set(
    registry
      .filter(
        (row) =>
          !args.allowedScopes.includes(row.scope) ||
          (args.scope === 'global' && row.layer === 'brahmagyan') ||
          (row.has_writer === false && !args.serviceProbeIds?.has(row.asset_id)),
      )
      .map((row) => row.asset_id),
  )
}

/**
 * Runs the planner and turns its non-dispatchable outcomes into typed errors.
 * UPSTREAM_BLOCKED and PROTECTED/ALL_LIT carry the same details the cockpit has
 * always returned.
 */
export function planRun(args: {
  inputs: PlanningInputs
  scope: BuildScope
  scopeTarget: string | null
  action: BuildAction
  nonCandidateAssetIds: Set<string>
}): { buildPlan: BuildPlan; plan: string[] } {
  const buildPlan = resolveBuildPlan({
    scope: args.scope,
    scope_target: args.scopeTarget,
    action: args.action,
    registry: args.inputs.registry,
    throughput: args.inputs.throughput,
    freshness: args.inputs.freshness,
    protectedAssetIds: args.inputs.protectedAssetIds,
    nonCandidateAssetIds: args.nonCandidateAssetIds,
  })
  if (buildPlan.status === 'blocked') {
    throw new BuildPreparationError('UPSTREAM_BLOCKED', 'Build blocked: upstream assets must be rebuilt first', {
      blockers: buildPlan.blockers,
      protected_assets: buildPlan.protected_assets,
    })
  }
  const plan = buildPlan.plan_waves.flat()
  if (plan.length === 0) {
    if (buildPlan.protected_assets.length > 0) {
      throw new BuildPreparationError('PROTECTED', 'Build blocked: every candidate in scope is protected', {
        protected_assets: buildPlan.protected_assets,
      })
    }
    throw new BuildPreparationError('ALL_LIT', 'Nothing to build: all assets in scope are already built.')
  }
  return { buildPlan, plan }
}

/** Freezes exactly what a dispatch accepted; the runner never re-plans from the mutable registry. */
export function freezeRunManifest(args: {
  chartId: string
  scope: BuildScope
  scopeTarget: string | null
  action: BuildAction
  planWaves: string[][]
  registry: RegistryEntryWithScope[]
}): { manifest: FrozenRunManifest; digest: string } {
  const registryByAssetId = new Map(args.registry.map((entry) => [entry.asset_id, entry]))
  const writerCountByTarget = new Map<string, number>()
  for (const entry of args.registry) {
    if (entry.target_table) {
      writerCountByTarget.set(entry.target_table, (writerCountByTarget.get(entry.target_table) ?? 0) + 1)
    }
  }
  const assets: FrozenManifestAsset[] = []
  for (const assetId of args.planWaves.flat()) {
    const entry = registryByAssetId.get(assetId)
    if (!entry) {
      throw new BuildPreparationError('INVALID_BUILD_PLAN', `Planner selected asset without an active writer: ${assetId}`)
    }
    const expectedDigest = expectedCodeDigest(entry)
    if (!expectedDigest) {
      throw new BuildPreparationError(
        'CODE_DIGEST_UNAVAILABLE',
        `No sidecar-owned writer digest is available for planned asset: ${assetId}`,
      )
    }
    assets.push({
      asset_id: entry.asset_id,
      scope: entry.scope,
      depends_on: [...(entry.depends_on ?? [])],
      natural_key_partition: entry.natural_key_partition ?? null,
      has_cowriters: Boolean(entry.target_table && (writerCountByTarget.get(entry.target_table) ?? 0) > 1),
      expected_code_digest: expectedDigest,
    })
  }
  const manifest: FrozenRunManifest = {
    version: 'nirmana-run-manifest/v1',
    chart_id: args.chartId,
    scope: args.scope,
    scope_target: args.scopeTarget,
    action: args.action,
    waves: args.planWaves.map((wave) => [...wave]),
    assets,
  }
  return { manifest, digest: manifestDigest(manifest) }
}

/**
 * Full preparation on one client: active-run guard, planner inputs, plan,
 * completeness, frozen manifest, and the dependency-ordered clear set.
 */
export async function resolveRunPreparation(db: Queryable, request: RunPreparationRequest): Promise<PreparedRun> {
  const activeRunId = await findActiveRun(db, request.chartId)
  if (activeRunId) {
    throw new BuildPreparationError('RUN_ACTIVE', 'A build is already in progress for this chart', {
      existing_run_id: activeRunId,
    })
  }

  const inputs = await loadPlanningInputs(db, request.chartId)
  const nonCandidateAssetIds = computeNonCandidateAssetIds(inputs.registry, {
    allowedScopes: request.allowedScopes,
    scope: request.scope,
  })
  let planned: ReturnType<typeof planRun>
  try {
    planned = planRun({
      inputs,
      scope: request.scope,
      scopeTarget: request.scopeTarget,
      action: request.action,
      nonCandidateAssetIds,
    })
  } catch (error) {
    // A withheld protected asset can also block its own dependants; for a complete
    // correction the protection is the cause the owner must act on.
    const protectedAssets = (error as BuildPreparationError).details?.protected_assets as unknown[] | undefined
    if (request.requireCompletePlan && error instanceof BuildPreparationError && protectedAssets?.length) {
      throw new BuildPreparationError('PROTECTED', 'A required per-chart asset is protected', {
        protected_assets: protectedAssets,
      })
    }
    throw error
  }
  const { buildPlan, plan } = planned

  if (request.requireCompletePlan) {
    if (buildPlan.protected_assets.length > 0) {
      throw new BuildPreparationError('PROTECTED', 'A required per-chart asset is protected', {
        protected_assets: buildPlan.protected_assets,
      })
    }
    const planned = new Set(plan)
    const required = filterScopeAssets(inputs.registry, request.scope, request.scopeTarget, request.allowedScopes)
      .map((row) => inputs.registry.find((entry) => entry.asset_id === row.asset_id)!)
      .filter((entry) => entry.has_writer !== false && !nonCandidateAssetIds.has(entry.asset_id))
      .map((entry) => entry.asset_id)
    const missing = required.filter((assetId) => !planned.has(assetId))
    if (missing.length > 0) {
      throw new BuildPreparationError('INVALID_BUILD_PLAN', 'The complete per-chart rebuild plan could not be frozen', {
        missing,
      })
    }
  }

  const { manifest, digest } = freezeRunManifest({
    chartId: request.chartId,
    scope: request.scope,
    scopeTarget: request.scopeTarget,
    action: request.action,
    planWaves: buildPlan.plan_waves,
    registry: inputs.registry,
  })

  const position = new Map(plan.map((assetId, index) => [assetId, index]))
  const clearAssets =
    request.clearPolicy === 'none'
      ? []
      : (filterScopeAssets(inputs.registry, request.scope, request.scopeTarget, request.allowedScopes) as RegistryEntryWithScope[])
          .filter((entry) => !inputs.protectedAssetIds.has(entry.asset_id))
          .map((entry, registryIndex) => ({ entry, registryIndex }))
          .sort(
            (a, b) =>
              (position.get(a.entry.asset_id) ?? -1) - (position.get(b.entry.asset_id) ?? -1) ||
              a.registryIndex - b.registryIndex,
          )
          .map(({ entry }) => entry)

  return {
    chartId: request.chartId,
    scope: request.scope,
    scopeTarget: request.scopeTarget,
    action: request.action,
    plan,
    planWaves: buildPlan.plan_waves.map((wave) => [...wave]),
    registry: inputs.registry,
    clearAssets,
    protectedAssets: buildPlan.protected_assets.map((p) => p.asset_id),
    manifest,
    manifestDigest: digest,
  }
}

/**
 * Inserts one planned run and every queued run-asset row. Never opens its own
 * transaction: the caller's transaction makes the pair atomic.
 */
export async function persistPreparedRun(
  db: Queryable,
  prepared: Pick<PreparedRun, 'chartId' | 'scope' | 'scopeTarget' | 'action' | 'plan' | 'manifest' | 'manifestDigest'>,
  triggeredBy: string,
): Promise<string> {
  const runResult = await db.query<{ id: string }>(
    `INSERT INTO build_runs
       (chart_id, scope, scope_target, action, state, plan, plan_manifest, plan_manifest_digest, triggered_by)
     VALUES ($1, $2, $3, $4, 'planned', $5, $6, $7, $8)
     RETURNING id`,
    [
      prepared.chartId,
      prepared.scope,
      prepared.scopeTarget,
      prepared.action,
      JSON.stringify(prepared.plan),
      JSON.stringify(prepared.manifest),
      prepared.manifestDigest,
      triggeredBy,
    ],
  )
  const runId = runResult.rows[0].id
  const placeholders = prepared.plan.map((_, i) => `($1, $${i * 3 + 2}, $${i * 3 + 3}, $${i * 3 + 4})`).join(', ')
  await db.query(
    `INSERT INTO build_run_assets (run_id, asset_id, position, state) VALUES ${placeholders}`,
    [runId, ...prepared.plan.flatMap((assetId, i) => [assetId, i, 'queued'])],
  )
  return runId
}

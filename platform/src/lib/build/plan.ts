export type AssetId = string
// 'incomplete' — migration 474. Ran, some data present, substep plan work still
// remains. Not finished, so it stays a `build` candidate; not 'lit', so it never
// satisfies a downstream dependency.
export type AssetState =
  | 'dormant' | 'building' | 'lit' | 'stale' | 'error' | 'incomplete' | 'service_ok' | 'service_down'
export type BuildAction = 'build' | 'update' | 'rebuild' | 'cascade'
export type BuildScope = 'global' | 'layer' | 'asset' | 'asset_set'

// O-wave WP-3 (NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §3.3, "total plans"). Every
// asset in the scope's registry rows gets EXACTLY one of these -- a plan that
// exposes only what it will run silently drops everything else. `build` covers
// candidates in plan_waves; `skip_no_delta` covers both "already fresh, no need
// to build" (assigned here, at plan time) and, once O-wave WP-2 lands, the
// writer's own pre-execution delta-skip (assigned at execution time) -- the
// same disposition, two different enforcement points for the same claim: no
// delta, nothing to do.
export type AssetDisposition =
  | 'build'
  | 'skip_no_delta'
  | 'deferred_no_writer'
  | 'withheld_protected'
  | 'dormant'
  | 'out_of_domain'
  | 'blocked_dependency'

export interface DispositionEntry {
  disposition: AssetDisposition
  reason?: string
}

// asset_registry.domain (migration 590): 'shared' | 'chart' | null. The
// planner's shared/chart split axis -- distinct from `scope` (a request-time
// selector) even though today every 'shared' row also has scope='global' and
// vice versa; domain is the field WP-3's domain-aware scoping reads.
export type AssetDomain = 'shared' | 'chart' | null

/**
 * Parses the comma-separated asset_id list carried by scope_target for scope='asset_set'.
 * Trims, drops empties, and de-dupes while preserving first-seen order.
 */
export function parseAssetSetTarget(scope_target: string | null): AssetId[] {
  if (!scope_target) return []
  const seen = new Set<AssetId>()
  const out: AssetId[] = []
  for (const raw of scope_target.split(',')) {
    const id = raw.trim()
    if (id && !seen.has(id)) {
      seen.add(id)
      out.push(id)
    }
  }
  return out
}

export interface RegistryEntry {
  asset_id: AssetId
  layer: string
  depends_on: AssetId[]
  estimated_seconds: number | null
  // Optional so every pre-WP-3 caller that builds a RegistryEntry without it
  // keeps compiling unchanged; resolveBuildPlan treats a missing/undefined
  // domain as 'chart' (the conservative default -- never silently excludes an
  // asset whose domain wasn't supplied at all).
  domain?: AssetDomain
}

export interface ThroughputEntry {
  asset_id: AssetId
  state: AssetState
}

export interface BlockerEntry {
  dep_asset_id: AssetId
  dep_state: AssetState | 'unknown'
  required_by: AssetId[]    // which in-scope assets need this dep
  guidance?: string         // non-empty for L0 dormant/error deps
}

// SHAD-DARSHANA sweep-protection Phase 1a, Layer 1/2 (planner guard). A candidate
// asset_id withheld from plan_waves because build_protected_assets names it protected
// for the chart_id this plan was resolved for. Surfaced explicitly rather than either
// silently including it (the defect this guard exists to close) or silently dropping it
// (§N.6 Serving Density discipline — an honest empty/withheld list, never an absent one).
export interface ProtectedAssetBlocker {
  asset_id: AssetId
  message: string
}

export const PROTECTED_ASSET_MESSAGE = 'protected — native override required'

export interface BuildPlan {
  status: 'ok' | 'blocked'
  plan_waves: AssetId[][]   // empty when blocked or when build no-ops a lit asset
  blockers: BlockerEntry[]  // empty when ok
  estimated_seconds: number | null  // always null when status is 'blocked'
  // Always present — empty when nothing was withheld. A protected candidate never appears
  // in plan_waves; it appears here instead, once per withheld asset_id.
  protected_assets: ProtectedAssetBlocker[]
  // O-wave WP-3 (plan §3.3 "total plans"): every registry row scoped by this
  // resolution gets exactly one disposition here -- computed ONLY for
  // scope='layer' today (the acceptance criterion's own scope: "a layer
  // plan's dispositions sum to the layer's registry count"). undefined for
  // every other scope, not an empty map -- a caller must not read an absent
  // computation as "zero dispositions"; §3.3's own selector-gap discipline
  // (throw rather than drop) is enforced inside resolveBuildPlan itself, not
  // deferred to callers reading this field.
  dispositions?: ReadonlyMap<AssetId, DispositionEntry>
}


export interface ResolveBuildPlanArgs {
  scope: BuildScope
  scope_target: string | null
  action: BuildAction
  registry: RegistryEntry[]
  throughput: Map<AssetId, ThroughputEntry>
  /** Sidecar-produced receipt classification; supplying it enables strict freshness checks. */
  freshness?: ReadonlyMap<AssetId, { state: 'fresh' | 'stale' | 'unknown'; reasons: string[] }>
  // asset_ids protected (via build_protected_assets) for the chart_id this plan is being
  // resolved for. Pre-filtered by the CALLER (a `WHERE chart_id = $1` query) — plan.ts
  // itself never sees a chart_id or talks to the DB, staying a pure function. Defaults to
  // an empty set (no protection) when omitted, so every existing caller keeps working
  // unchanged until it is updated to pass this.
  protectedAssetIds?: Set<AssetId>
  // Known registry identities that may satisfy an upstream pre-flight but must
  // never become ordinary dispatch candidates (for example, a service probe
  // with no WriterBase implementation). The registry remains complete for DAG
  // validation and readiness checks; only candidate selection excludes them.
  nonCandidateAssetIds?: ReadonlySet<AssetId>
}

const EMPTY_PROTECTED_SET: ReadonlySet<AssetId> = new Set()
const EMPTY_NON_CANDIDATE_SET: ReadonlySet<AssetId> = new Set()

/**
 * Splits `candidates` into the ones the plan may act on and the ones withheld because
 * they are protected. Order-preserving on both output arrays. A candidate never appears
 * in both.
 */
function withholdProtected(
  candidates: AssetId[],
  protectedAssetIds: ReadonlySet<AssetId>
): { kept: AssetId[]; withheld: ProtectedAssetBlocker[] } {
  if (protectedAssetIds.size === 0) return { kept: candidates, withheld: [] }
  const kept: AssetId[] = []
  const withheld: ProtectedAssetBlocker[] = []
  for (const id of candidates) {
    if (protectedAssetIds.has(id)) {
      withheld.push({ asset_id: id, message: PROTECTED_ASSET_MESSAGE })
    } else {
      kept.push(id)
    }
  }
  return { kept, withheld }
}

function topoSort(ids: AssetId[], registry: RegistryEntry[]): AssetId[] {
  const regMap = new Map(registry.map(r => [r.asset_id, r]))
  const inScope = new Set(ids)
  const visited = new Set<AssetId>()
  const result: AssetId[] = []

  const visit = (id: AssetId, stack: Set<AssetId>) => {
    if (stack.has(id)) throw new Error(`Cycle detected involving asset: ${id}`)
    if (visited.has(id)) return
    stack.add(id)
    const entry = regMap.get(id)
    if (entry) {
      for (const dep of entry.depends_on) {
        if (inScope.has(dep)) visit(dep, stack)
      }
    }
    stack.delete(id)
    visited.add(id)
    result.push(id)
  }

  for (const id of ids) visit(id, new Set())
  return result
}

// O-wave WP-3 (plan §3.3): a layer sweep excludes domain='shared' rows by
// default -- a chart's layer rebuild must not silently ride along a global
// reference asset that belongs to every chart. `scope='asset'`/`'asset_set'`
// name their targets explicitly and are never filtered here (an explicit
// request always honors the exact id named, shared or not); `scope='global'`
// is unfiltered too ("global scope owns shared", plan §3.3 build spec).
// Missing/undefined domain defaults to 'chart' (never silently excluded).
function isLayerSweepExcludedDomain(entry: RegistryEntry): boolean {
  return (entry.domain ?? 'chart') === 'shared'
}

function assetsInScope(
  scope: BuildScope,
  scope_target: string | null,
  registry: RegistryEntry[]
): AssetId[] {
  if (scope === 'global') return registry.map(r => r.asset_id)
  if (scope === 'layer') {
    return registry
      .filter(r => r.layer === scope_target && !isLayerSweepExcludedDomain(r))
      .map(r => r.asset_id)
  }
  if (scope === 'asset') return scope_target ? [scope_target] : []
  if (scope === 'asset_set') {
    // scope_target carries a comma-separated asset_id list. Filter to registry
    // membership (drops phantom/filtered-out ids) preserving registry order.
    const wanted = new Set(parseAssetSetTarget(scope_target))
    return registry.filter(r => wanted.has(r.asset_id)).map(r => r.asset_id)
  }
  return []
}

function transitiveDownstream(
  seeds: AssetId[],
  registry: RegistryEntry[]
): AssetId[] {
  const seedSet = new Set(seeds)
  const downstream = new Set<AssetId>()
  let changed = true
  while (changed) {
    changed = false
    for (const r of registry) {
      if (downstream.has(r.asset_id) || seedSet.has(r.asset_id)) continue
      if (r.depends_on.some(d => seedSet.has(d) || downstream.has(d))) {
        downstream.add(r.asset_id)
        changed = true
      }
    }
  }
  return Array.from(downstream)
}

/** All transitive downstream dependents of the given asset IDs (not including seeds). */
export function computeDownstreamClosure(seeds: AssetId[], registry: RegistryEntry[]): Set<AssetId> {
  return new Set(transitiveDownstream(seeds, registry))
}

/** All transitive upstream dependencies of the given asset IDs (not including seeds). */
export function computeUpstreamClosure(seeds: AssetId[], registry: RegistryEntry[]): Set<AssetId> {
  const seedSet = new Set(seeds)
  const upstream = new Set<AssetId>()
  const regMap = new Map(registry.map(r => [r.asset_id, r]))

  const visit = (id: AssetId) => {
    const entry = regMap.get(id)
    if (!entry) return
    for (const dep of entry.depends_on) {
      if (!seedSet.has(dep) && !upstream.has(dep)) {
        upstream.add(dep)
        visit(dep)
      }
    }
  }

  for (const id of seeds) visit(id)
  return upstream
}

const READY_STATES = new Set<AssetState>(['lit', 'service_ok'])

/**
 * Checks all relevant deps of `candidates` for readiness.
 * Layer scope: only cross-layer deps checked (intra-layer handled by DAG).
 * Traverses transitively in layer scope — a stale ga_positions is flagged
 * even when it's only reachable via a lit cross-layer dep (bo_bimba).
 * Returns BlockerEntry[] — empty means pre-flight passed.
 */
export function preflight(
  candidates: AssetId[],
  scope: BuildScope,
  scope_target: string | null,
  registry: RegistryEntry[],
  throughput: Map<AssetId, ThroughputEntry>,
  freshness?: ReadonlyMap<AssetId, { state: 'fresh' | 'stale' | 'unknown'; reasons: string[] }>,
): BlockerEntry[] {
  const regMap = new Map(registry.map(r => [r.asset_id, r]))
  const candidateSet = new Set(candidates)
  const blockerMap = new Map<AssetId, BlockerEntry>()

  function collectDepsToCheck(
    assetId: AssetId,
    visited: Set<AssetId>,
    result: Set<AssetId>
  ) {
    if (visited.has(assetId)) return
    visited.add(assetId)
    const entry = regMap.get(assetId)
    if (!entry) return

    for (const dep of entry.depends_on) {
      // Dependencies dispatched in this same immutable plan are ordered by the
      // DAG and must not be mistaken for missing out-of-plan prerequisites.
      if (candidateSet.has(dep)) continue
      const depLayer = regMap.get(dep)?.layer
      const isIntraLayer = scope === 'layer' && scope_target != null && depLayer === scope_target

      if (isIntraLayer) {
        // Intra-layer: DAG will order these — don't check, don't recurse
        continue
      }

      // Cross-layer dep: add to check set and recurse in layer scope
      result.add(dep)
      if (scope === 'layer') {
        collectDepsToCheck(dep, visited, result)
      }
      // Asset scope: direct deps only — no recursion
    }
  }

  for (const candidate of candidates) {
    const depsToCheck = new Set<AssetId>()
    collectDepsToCheck(candidate, new Set<AssetId>(), depsToCheck)

    for (const dep of depsToCheck) {
      // A dependency absent from the registry is unknown, never an earned ready
      // state. Existing callers that do not yet supply the sidecar projection
      // retain their historical sparse-throughput behaviour; once supplied, a
      // missing throughput or receipt row is an explicit unknown blocker.
      const depState = throughput.get(dep)?.state
      const receipt = freshness?.get(dep)
      const registered = regMap.has(dep)
      const ready = registered && (freshness === undefined
        ? (depState === undefined || READY_STATES.has(depState))
        : (depState !== undefined && READY_STATES.has(depState) && receipt?.state === 'fresh'))
      if (ready) continue

      const effectiveState: AssetState | 'unknown' = !registered || depState === undefined
        ? 'unknown'
        : (freshness !== undefined && receipt?.state !== 'fresh' ? receipt?.state ?? 'unknown' : depState)

      if (!blockerMap.has(dep)) {
        const isL0 = regMap.get(dep)?.layer === 'brahmagyan'
        blockerMap.set(dep, {
          dep_asset_id: dep,
          dep_state: effectiveState,
          required_by: [],
          ...(isL0 ? { guidance: 'L0 dependency not built — run the Brahmagyan layer first' } : {}),
        })
      }
      const existing = blockerMap.get(dep)!
      if (!existing.required_by.includes(candidate)) {
        existing.required_by.push(candidate)
      }
    }
  }

  return Array.from(blockerMap.values())
}
/**
 * Groups candidates into parallel execution waves.
 * Layer scope: only intra-layer deps count for wave assignment.
 * Global scope: all deps (incl. cross-layer) count.
 * Asset scope: always [[candidate]].
 */
export function computeWaves(
  candidates: AssetId[],
  registry: RegistryEntry[],
  scope: BuildScope,
  scope_target: string | null
): AssetId[][] {
  if (candidates.length === 0) return []
  if (scope === 'asset') return [candidates.slice()]

  const candidateSet = new Set(candidates)
  const regMap = new Map(registry.map(r => [r.asset_id, r]))
  const sorted = topoSort(candidates, registry)
  const waveOf = new Map<AssetId, number>()

  for (const id of sorted) {
    const entry = regMap.get(id)
    const deps = entry?.depends_on ?? []

    const relevantDeps = deps.filter(dep => {
      if (!candidateSet.has(dep)) return false
      // Layer scope: cross-layer deps don't determine wave (already pre-flighted)
      if (scope === 'layer' && scope_target) {
        const depEntry = regMap.get(dep)
        if (depEntry?.layer !== scope_target) return false
      }
      return true
    })

    const wave = relevantDeps.length === 0
      ? 0
      : Math.max(...relevantDeps.map(d => waveOf.get(d) ?? 0)) + 1
    waveOf.set(id, wave)
  }

  const maxWave = Math.max(...Array.from(waveOf.values()))
  const waves: AssetId[][] = Array.from({ length: maxWave + 1 }, () => [])
  for (const [id, wave] of waveOf) waves[wave].push(id)

  return waves
}

function estimateSeconds(ids: AssetId[], registry: RegistryEntry[]): number | null {
  let total = 0
  for (const id of ids) {
    const entry = registry.find(r => r.asset_id === id)
    if (!entry || entry.estimated_seconds == null) return null
    total += entry.estimated_seconds
  }
  return total
}

/**
 * O-wave WP-3 (plan §3.3, "total plans"): every registry row in `scope_target`'s
 * layer gets exactly one disposition. `rawCandidateIds` is the action's OWN
 * pre-block, pre-protection-withholding candidate set (what it decided it
 * wants to build); `blocked` is true when the whole plan refused to proceed
 * (status='blocked') -- in that case every raw candidate is `blocked_dependency`
 * rather than `build`, since none of them run this round.
 */
function computeLayerDispositions(
  scope_target: string,
  registry: RegistryEntry[],
  throughput: Map<AssetId, ThroughputEntry>,
  nonCandidateSet: ReadonlySet<AssetId>,
  protectedSet: ReadonlySet<AssetId>,
  rawCandidateIds: ReadonlySet<AssetId>,
  blocked: boolean,
  blockers: BlockerEntry[],
): ReadonlyMap<AssetId, DispositionEntry> {
  const blockerReasonByAsset = new Map<AssetId, string>()
  for (const blocker of blockers) {
    for (const requiredBy of blocker.required_by) {
      if (!blockerReasonByAsset.has(requiredBy)) {
        blockerReasonByAsset.set(
          requiredBy,
          `upstream ${blocker.dep_asset_id} is ${blocker.dep_state}`,
        )
      }
    }
  }

  const dispositions = new Map<AssetId, DispositionEntry>()
  for (const row of registry) {
    if (row.layer !== scope_target) continue
    const id = row.asset_id
    if (isLayerSweepExcludedDomain(row)) {
      dispositions.set(id, { disposition: 'out_of_domain' })
    } else if (nonCandidateSet.has(id)) {
      dispositions.set(id, { disposition: 'deferred_no_writer' })
    } else if (protectedSet.has(id)) {
      dispositions.set(id, { disposition: 'withheld_protected' })
    } else if (rawCandidateIds.has(id)) {
      dispositions.set(id, blocked
        ? { disposition: 'blocked_dependency', reason: blockerReasonByAsset.get(id) ?? 'plan blocked' }
        : { disposition: 'build' })
    } else if (throughput.get(id)?.state === 'dormant') {
      // Not this action's candidate (e.g. a cascade/update pass that never
      // reached it) but genuinely dormant -- distinct from "nothing to do".
      dispositions.set(id, { disposition: 'dormant' })
    } else {
      // In-domain, writer-present, unprotected, not this action's candidate,
      // not blocked, not dormant: this action's own selection logic already
      // decided there is nothing for it to do here (lit/fresh, or a state
      // this particular action doesn't address -- e.g. 'build' deliberately
      // leaves staleness to update/cascade). No delta from this plan's
      // perspective.
      dispositions.set(id, { disposition: 'skip_no_delta' })
    }
  }
  // Defensive: the walk above assigns every in-scope registry row exactly
  // one disposition by construction. Kept as an explicit check (plan §3.3:
  // "a selector gap throws rather than drops") rather than trusting the
  // construction never to grow a hole under a future edit.
  const gaps = registry
    .filter(r => r.layer === scope_target && !dispositions.has(r.asset_id))
    .map(r => r.asset_id)
  if (gaps.length > 0) {
    throw new Error(
      `resolveBuildPlan: disposition selector gap for layer '${scope_target}': ${gaps.join(', ')}`
    )
  }
  return dispositions
}

export function resolveBuildPlan({
  scope,
  scope_target,
  action,
  registry,
  throughput,
  freshness,
  protectedAssetIds,
  nonCandidateAssetIds,
}: ResolveBuildPlanArgs): BuildPlan {
  const protectedSet: ReadonlySet<AssetId> = protectedAssetIds ?? EMPTY_PROTECTED_SET
  const nonCandidateSet: ReadonlySet<AssetId> = nonCandidateAssetIds ?? EMPTY_NON_CANDIDATE_SET
  const candidateAssetsInScope = (candidateScope: BuildScope, candidateScopeTarget: string | null) =>
    assetsInScope(candidateScope, candidateScopeTarget, registry)
      .filter(assetId => !nonCandidateSet.has(assetId))

  // asset_set: the scope_target list must resolve to at least one in-registry asset.
  // An empty/all-phantom list is a caller error, not a silent no-op.
  if (scope === 'asset_set' && candidateAssetsInScope('asset_set', scope_target).length === 0) {
    throw new Error('asset_set scope requires a non-empty list of valid asset_ids')
  }

  // Every action that produces a candidate must pass the same out-of-plan
  // dependency preflight. Update/cascade used to bypass it, which could plan a
  // consumer after its L0/service identity had been withheld from candidates.
  // O-wave WP-3 (plan §3.3): computed only for scope='layer', matching the
  // acceptance criterion's own scope ("a layer plan's dispositions sum to the
  // layer's registry count"). Other scopes get no dispositions field at all
  // -- not an empty map, an absent computation (see BuildPlan's own doc).
  const dispositionsFor = (rawCandidates: AssetId[], blocked: boolean, blockers: BlockerEntry[]) =>
    scope === 'layer' && scope_target
      ? computeLayerDispositions(
          scope_target, registry, throughput, nonCandidateSet, protectedSet,
          new Set(rawCandidates), blocked, blockers,
        )
      : undefined

  if (action === 'update') {
    const scopeAssets = candidateAssetsInScope(scope, scope_target)
    const stale = scopeAssets.filter(id =>
      throughput.get(id)?.state === 'stale' ||
      (freshness !== undefined && freshness.get(id)?.state !== 'fresh')
    )
    const dormant = scopeAssets.filter(id => {
      const t = throughput.get(id)
      return !t || t.state === 'dormant'
    })
    const downstreamAll = transitiveDownstream(stale, registry)
    const downstreamFiltered = scope === 'asset' ? downstreamAll : downstreamAll.filter(id => scopeAssets.includes(id))
    const rawCandidates = Array.from(new Set([...stale, ...dormant, ...downstreamFiltered]))
    const { kept: candidates, withheld } = withholdProtected(rawCandidates, protectedSet)
    const blockers = preflight(candidates, scope, scope_target, registry, throughput, freshness)
    if (blockers.length > 0) {
      return {
        status: 'blocked', plan_waves: [], blockers, estimated_seconds: null,
        protected_assets: withheld, dispositions: dispositionsFor(rawCandidates, true, blockers),
      }
    }
    const sorted = topoSort(candidates, registry)
    const waves = computeWaves(sorted, registry, scope, scope_target)
    return {
      status: 'ok', plan_waves: waves, blockers: [],
      estimated_seconds: estimateSeconds(waves.flat(), registry),
      protected_assets: withheld, dispositions: dispositionsFor(rawCandidates, false, []),
    }
  }

  if (action === 'cascade') {
    const scopeAssets = candidateAssetsInScope(scope, scope_target)
    const stale = registry.filter(r =>
      throughput.get(r.asset_id)?.state === 'stale' ||
      (freshness !== undefined && freshness.get(r.asset_id)?.state !== 'fresh')
    ).map(r => r.asset_id)
    const rawCandidates = transitiveDownstream(stale, registry).filter(id => scopeAssets.includes(id))
    const { kept: candidates, withheld } = withholdProtected(rawCandidates, protectedSet)
    const blockers = preflight(candidates, scope, scope_target, registry, throughput, freshness)
    if (blockers.length > 0) {
      return {
        status: 'blocked', plan_waves: [], blockers, estimated_seconds: null,
        protected_assets: withheld, dispositions: dispositionsFor(rawCandidates, true, blockers),
      }
    }
    const sorted = topoSort(candidates, registry)
    const waves = computeWaves(sorted, registry, scope, scope_target)
    return {
      status: 'ok', plan_waves: waves, blockers: [],
      estimated_seconds: estimateSeconds(waves.flat(), registry),
      protected_assets: withheld, dispositions: dispositionsFor(rawCandidates, false, []),
    }
  }

  // build and rebuild: scope-aware candidates + pre-flight gate
  const scopeAssets = candidateAssetsInScope(scope, scope_target)

  let rawCandidates: AssetId[]
  if (action === 'build') {
    rawCandidates = scopeAssets.filter(id => {
      const t = throughput.get(id)
      const receiptNeedsBuild = freshness !== undefined && freshness.get(id)?.state !== 'fresh'
      // 'incomplete' (migration 474) means "ran, some data present, substep plan
      // work still remains" — it is by definition NOT finished, so `build` must
      // pick it up. Omitting it made an 'incomplete' asset unreachable by the
      // Build button: it is not 'lit', so nothing considers it done, yet it was
      // not a candidate either, so `build` reported "already lit, nothing to do"
      // and silently no-op'd. Required corollary of SAMĀPTI B-WATCHDOG-LIT (DVA
      // Ruling 10), which is the first path to write 'incomplete' from the
      // TypeScript side; also repairs the same latent strand for the Python
      // path's 'incomplete' (asset_runner.py:677), which predates this change.
      return receiptNeedsBuild || !t || t.state === 'dormant' || t.state === 'error' || t.state === 'incomplete'
    })
  } else {
    // rebuild: all assets in scope (no transitive downstream expansion)
    rawCandidates = [...scopeAssets]
  }

  const { kept: candidates, withheld } = withholdProtected(rawCandidates, protectedSet)

  // build no-op: nothing left to build once protected candidates are withheld too —
  // this is the honest "already lit, nothing to do" case only when nothing was ALSO
  // withheld; a build that consists ENTIRELY of protected candidates still reports
  // them via protected_assets rather than reading identically to a true no-op.
  if (action === 'build' && candidates.length === 0) {
    return {
      status: 'ok', plan_waves: [], blockers: [], estimated_seconds: null,
      protected_assets: withheld, dispositions: dispositionsFor(rawCandidates, false, []),
    }
  }

  const blockers = preflight(candidates, scope, scope_target, registry, throughput, freshness)
  if (blockers.length > 0) {
    return {
      status: 'blocked', plan_waves: [], blockers, estimated_seconds: null,
      protected_assets: withheld, dispositions: dispositionsFor(rawCandidates, true, blockers),
    }
  }

  const waves = computeWaves(candidates, registry, scope, scope_target)
  const flat = waves.flat()
  const estimated = estimateSeconds(flat, registry)
  return {
    status: 'ok', plan_waves: waves, blockers: [], estimated_seconds: estimated,
    protected_assets: withheld, dispositions: dispositionsFor(rawCandidates, false, []),
  }
}

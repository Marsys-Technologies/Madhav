export type AssetId = string
// 'incomplete' — migration 474. Ran, some data present, substep plan work still
// remains. Not finished, so it stays a `build` candidate; not 'lit', so it never
// satisfies a downstream dependency.
export type AssetState =
  | 'dormant' | 'building' | 'lit' | 'stale' | 'error' | 'incomplete' | 'service_ok' | 'service_down'
export type BuildAction = 'build' | 'update' | 'rebuild' | 'cascade'
export type BuildScope = 'global' | 'layer' | 'asset' | 'asset_set'

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
}

export interface ThroughputEntry {
  asset_id: AssetId
  state: AssetState
}

export interface BlockerEntry {
  dep_asset_id: AssetId
  dep_state: AssetState
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
}


export interface ResolveBuildPlanArgs {
  scope: BuildScope
  scope_target: string | null
  action: BuildAction
  registry: RegistryEntry[]
  throughput: Map<AssetId, ThroughputEntry>
  // asset_ids protected (via build_protected_assets) for the chart_id this plan is being
  // resolved for. Pre-filtered by the CALLER (a `WHERE chart_id = $1` query) — plan.ts
  // itself never sees a chart_id or talks to the DB, staying a pure function. Defaults to
  // an empty set (no protection) when omitted, so every existing caller keeps working
  // unchanged until it is updated to pass this.
  protectedAssetIds?: Set<AssetId>
}

const EMPTY_PROTECTED_SET: ReadonlySet<AssetId> = new Set()

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

function assetsInScope(
  scope: BuildScope,
  scope_target: string | null,
  registry: RegistryEntry[]
): AssetId[] {
  if (scope === 'global') return registry.map(r => r.asset_id)
  if (scope === 'layer') return registry.filter(r => r.layer === scope_target).map(r => r.asset_id)
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
  throughput: Map<AssetId, ThroughputEntry>
): BlockerEntry[] {
  const regMap = new Map(registry.map(r => [r.asset_id, r]))
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
      // Use undefined-safe: absent entries are not our concern (treat as ready)
      const depState = throughput.get(dep)?.state
      if (depState === undefined || READY_STATES.has(depState)) continue

      if (!blockerMap.has(dep)) {
        const isL0 = regMap.get(dep)?.layer === 'brahmagyan'
        blockerMap.set(dep, {
          dep_asset_id: dep,
          dep_state: depState,
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

export function resolveBuildPlan({
  scope,
  scope_target,
  action,
  registry,
  throughput,
  protectedAssetIds,
}: ResolveBuildPlanArgs): BuildPlan {
  const protectedSet: ReadonlySet<AssetId> = protectedAssetIds ?? EMPTY_PROTECTED_SET

  // asset_set: the scope_target list must resolve to at least one in-registry asset.
  // An empty/all-phantom list is a caller error, not a silent no-op.
  if (scope === 'asset_set' && assetsInScope('asset_set', scope_target, registry).length === 0) {
    throw new Error('asset_set scope requires a non-empty list of valid asset_ids')
  }

  // update and cascade: no pre-flight, use existing behavior, return new shape
  if (action === 'update') {
    const scopeAssets = assetsInScope(scope, scope_target, registry)
    const stale = scopeAssets.filter(id => throughput.get(id)?.state === 'stale')
    const dormant = scopeAssets.filter(id => {
      const t = throughput.get(id)
      return !t || t.state === 'dormant'
    })
    const downstreamAll = transitiveDownstream(stale, registry)
    const downstreamFiltered = scope === 'asset' ? downstreamAll : downstreamAll.filter(id => scopeAssets.includes(id))
    const rawCandidates = Array.from(new Set([...stale, ...dormant, ...downstreamFiltered]))
    const { kept: candidates, withheld } = withholdProtected(rawCandidates, protectedSet)
    const sorted = topoSort(candidates, registry)
    const waves = computeWaves(sorted, registry, scope, scope_target)
    return {
      status: 'ok', plan_waves: waves, blockers: [],
      estimated_seconds: estimateSeconds(waves.flat(), registry),
      protected_assets: withheld,
    }
  }

  if (action === 'cascade') {
    const scopeAssets = assetsInScope(scope, scope_target, registry)
    const stale = registry.filter(r => throughput.get(r.asset_id)?.state === 'stale').map(r => r.asset_id)
    const rawCandidates = transitiveDownstream(stale, registry).filter(id => scopeAssets.includes(id))
    const { kept: candidates, withheld } = withholdProtected(rawCandidates, protectedSet)
    const sorted = topoSort(candidates, registry)
    const waves = computeWaves(sorted, registry, scope, scope_target)
    return {
      status: 'ok', plan_waves: waves, blockers: [],
      estimated_seconds: estimateSeconds(waves.flat(), registry),
      protected_assets: withheld,
    }
  }

  // build and rebuild: scope-aware candidates + pre-flight gate
  const scopeAssets = assetsInScope(scope, scope_target, registry)

  let rawCandidates: AssetId[]
  if (action === 'build') {
    rawCandidates = scopeAssets.filter(id => {
      const t = throughput.get(id)
      // 'incomplete' (migration 474) means "ran, some data present, substep plan
      // work still remains" — it is by definition NOT finished, so `build` must
      // pick it up. Omitting it made an 'incomplete' asset unreachable by the
      // Build button: it is not 'lit', so nothing considers it done, yet it was
      // not a candidate either, so `build` reported "already lit, nothing to do"
      // and silently no-op'd. Required corollary of SAMĀPTI B-WATCHDOG-LIT (DVA
      // Ruling 10), which is the first path to write 'incomplete' from the
      // TypeScript side; also repairs the same latent strand for the Python
      // path's 'incomplete' (asset_runner.py:677), which predates this change.
      return !t || t.state === 'dormant' || t.state === 'error' || t.state === 'incomplete'
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
    return { status: 'ok', plan_waves: [], blockers: [], estimated_seconds: null, protected_assets: withheld }
  }

  // pre-flight gate: only for non-global scope (global has all assets as candidates)
  if (scope !== 'global') {
    const blockers = preflight(candidates, scope, scope_target, registry, throughput)
    if (blockers.length > 0) {
      return { status: 'blocked', plan_waves: [], blockers, estimated_seconds: null, protected_assets: withheld }
    }
  }

  const waves = computeWaves(candidates, registry, scope, scope_target)
  const flat = waves.flat()
  const estimated = estimateSeconds(flat, registry)
  return { status: 'ok', plan_waves: waves, blockers: [], estimated_seconds: estimated, protected_assets: withheld }
}

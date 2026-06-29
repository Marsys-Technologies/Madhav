export type AssetId = string
export type AssetState =
  | 'dormant' | 'building' | 'lit' | 'stale' | 'error' | 'service_ok' | 'service_down'
export type BuildAction = 'build' | 'update' | 'rebuild' | 'cascade'
export type BuildScope = 'global' | 'layer' | 'asset'

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

export interface BuildPlan {
  status: 'ok' | 'blocked'
  plan_waves: AssetId[][]   // empty when blocked or when build no-ops a lit asset
  blockers: BlockerEntry[]  // empty when ok
  estimated_seconds: number | null  // always null when status is 'blocked'
}

export interface StalenessGateEntry {
  asset_id: AssetId
  state: string
  required_by: AssetId[]
}

/**
 * Returns one entry per out-of-plan upstream dep whose state is 'stale'.
 * A non-empty result means the build should be blocked: building downstream
 * on stale data produces wrong output. In-plan deps are excluded — the DAG
 * scheduler handles those by running deps before dependents.
 * Dormant/error upstream are not flagged here: auto-pull or L0-blocking
 * handles them separately.
 */
export function checkStalenessGate(
  plan: AssetId[],
  registry: RegistryEntry[],
  throughput: Map<AssetId, ThroughputEntry>
): StalenessGateEntry[] {
  const planSet = new Set(plan)
  const regMap = new Map(registry.map(r => [r.asset_id, r]))
  // Map from blocker asset_id → set of plan assets that require it.
  const staleBlockers = new Map<AssetId, Set<AssetId>>()

  for (const planAsset of plan) {
    for (const dep of regMap.get(planAsset)?.depends_on ?? []) {
      if (planSet.has(dep)) continue  // in-plan: DAG will handle it
      if (throughput.get(dep)?.state === 'stale') {
        if (!staleBlockers.has(dep)) staleBlockers.set(dep, new Set())
        staleBlockers.get(dep)!.add(planAsset)
      }
    }
  }

  return Array.from(staleBlockers.entries()).map(([dep, requiredBySet]) => ({
    asset_id: dep,
    state: throughput.get(dep)!.state,
    required_by: Array.from(requiredBySet),
  }))
}

export interface ResolveBuildPlanArgs {
  scope: BuildScope
  scope_target: string | null
  action: BuildAction
  registry: RegistryEntry[]
  throughput: Map<AssetId, ThroughputEntry>
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

export function resolveBuildPlan({
  scope,
  scope_target,
  action,
  registry,
  throughput,
}: ResolveBuildPlanArgs): BuildPlan {
  const scopeAssets = assetsInScope(scope, scope_target, registry)

  let candidates: AssetId[]

  if (action === 'build') {
    candidates = scopeAssets.filter(id => {
      const t = throughput.get(id)
      return !t || t.state === 'dormant' || t.state === 'error'
    })
  } else if (action === 'update') {
    const stale = scopeAssets.filter(id => throughput.get(id)?.state === 'stale')
    const dormant = scopeAssets.filter(id => {
      const t = throughput.get(id)
      return !t || t.state === 'dormant'
    })
    // For asset-scoped update: include transitive downstream regardless of scope boundary.
    // For layer/global scopes: only downstream within scope.
    const downstreamAll = transitiveDownstream(stale, registry)
    const downstreamFiltered = scope === 'asset' ? downstreamAll : downstreamAll.filter(id => scopeAssets.includes(id))
    candidates = Array.from(new Set([...stale, ...dormant, ...downstreamFiltered]))
  } else if (action === 'rebuild') {
    // Asset-scoped rebuild: target + its full transitive downstream (90/10 semantic).
    // Layer/global scopes: all assets in scope.
    if (scope === 'asset' && scope_target) {
      const downstream = transitiveDownstream([scope_target], registry)
      candidates = [scope_target, ...downstream]
    } else {
      candidates = [...scopeAssets]
    }
  } else {
    // cascade: only downstream-stale from any stale seed
    const stale = registry.filter(r => throughput.get(r.asset_id)?.state === 'stale').map(r => r.asset_id)
    candidates = transitiveDownstream(stale, registry)
      .filter(id => scopeAssets.includes(id))
  }

  const blockedAssets: { asset_id: string; reason: string }[] = []

  // For build/rebuild at non-global scope, pull in dormant/error/missing upstream
  // dependencies that fall outside the literal scope. Without this, building a
  // downstream asset whose cross-layer upstream is dormant fails silently because
  // the orchestrator walks the plan in order and the source table is absent.
  // Global scope is safe: all assets are already candidates.
  //
  // L0 EXCLUSION (native ruling 2026-06-26): bg_* (brahmagyan) assets are NEVER
  // auto-pulled. If a candidate transitively depends on a dormant L0 asset, it is
  // marked blocked (not built) and excluded from the plan. The caller surfaces the
  // blocked list so the UI can say "run the Brahmagyan layer first".
  if ((action === 'build' || action === 'rebuild') && scope !== 'global' && candidates.length > 0) {
    const upstreamAll = computeUpstreamClosure(candidates, registry)
    const regMap = new Map(registry.map(r => [r.asset_id, r]))

    // Pull in non-L0 dormant/error upstream only
    for (const upId of upstreamAll) {
      const upEntry = regMap.get(upId)
      if (upEntry?.layer === 'brahmagyan') continue  // never auto-pull L0
      if (!candidates.includes(upId)) {
        const t = throughput.get(upId)
        // Skip already-lit upstream: pulling in lit upstream would unexpectedly redo work.
        if (!t || t.state === 'dormant' || t.state === 'error') {
          candidates.push(upId)
        }
      }
    }

    // Detect candidates blocked by dormant L0 transitive deps and remove from plan
    const l0Dormant = new Set(
      registry
        .filter(r => r.layer === 'brahmagyan')
        .filter(r => { const t = throughput.get(r.asset_id); return !t || t.state === 'dormant' || t.state === 'error' })
        .map(r => r.asset_id)
    )

    if (l0Dormant.size > 0) {
      const candidateSet = new Set(candidates)
      const blockedSet = new Set<string>()
      for (const id of candidates) {
        const transitiveUp = computeUpstreamClosure([id], registry)
        // Only block if the dormant L0 dep is NOT already being built in this same plan.
        // When scope=layer/brahmagyan, all L0 assets are candidates and will be topo-ordered first.
        const blockerDep = [...transitiveUp].find(up => l0Dormant.has(up) && !candidateSet.has(up))
        if (blockerDep) {
          blockedSet.add(id)
          blockedAssets.push({
            asset_id: id,
            reason: `L0 dependency '${blockerDep}' not built — run the Brahmagyan layer first`,
          })
        }
      }
      if (blockedSet.size > 0) {
        candidates = candidates.filter(id => !blockedSet.has(id))
      }
    }
  }

  const sorted = topoSort(candidates, registry)

  const upstreamCount = sorted.filter(id => !scopeAssets.includes(id)).length

  let estimated: number | null = 0
  for (const id of sorted) {
    const entry = registry.find(r => r.asset_id === id)
    if (!entry || entry.estimated_seconds == null) {
      estimated = null
      break
    }
    estimated = (estimated ?? 0) + entry.estimated_seconds
  }

  return { plan: sorted, includes_upstream_count: upstreamCount, estimated_seconds: estimated, blocked_assets: blockedAssets }
}

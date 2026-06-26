export type AssetId = string
export type AssetState = 'dormant' | 'building' | 'lit' | 'stale' | 'error'
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

export interface BuildPlan {
  plan: AssetId[]
  includes_upstream_count: number
  estimated_seconds: number | null
  /** Assets excluded from the plan because a dormant L0 (bg_*) dep blocks them. */
  blocked_assets: { asset_id: string; reason: string }[]
}

interface ResolveBuildPlanArgs {
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

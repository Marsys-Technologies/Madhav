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
      return !t || t.state === 'dormant'
    })
  } else if (action === 'update') {
    const stale = scopeAssets.filter(id => throughput.get(id)?.state === 'stale')
    const dormant = scopeAssets.filter(id => {
      const t = throughput.get(id)
      return !t || t.state === 'dormant'
    })
    // Transitively include anything downstream of stale that is also dormant
    const downstream = transitiveDownstream(stale, registry)
    candidates = Array.from(new Set([...stale, ...dormant, ...downstream]))
      .filter(id => scopeAssets.includes(id))
  } else if (action === 'rebuild') {
    candidates = [...scopeAssets]
  } else {
    // cascade: only downstream-stale from any stale seed
    const stale = registry.filter(r => throughput.get(r.asset_id)?.state === 'stale').map(r => r.asset_id)
    candidates = transitiveDownstream(stale, registry)
      .filter(id => scopeAssets.includes(id))
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

  return { plan: sorted, includes_upstream_count: upstreamCount, estimated_seconds: estimated }
}

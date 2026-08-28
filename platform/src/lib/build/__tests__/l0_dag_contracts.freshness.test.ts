import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../../scripts/seed/asset_registry_seed'
import { resolveBuildPlan, type RegistryEntry, type ThroughputEntry } from '../plan'

const registry: RegistryEntry[] = ASSETS.map((asset) => ({
  asset_id: asset.asset_id,
  layer: asset.layer,
  depends_on: asset.depends_on,
  estimated_seconds: asset.estimated_seconds,
}))

const contracts = [
  ['bg_panchanga', 'ga_panchanga'],
  ['bg_ghatana', 'bg_class_lifetime_counts'],
  ['bg_prashna_rules', 'ga_prashna'],
  ['bg_vastu_directions', 'ga_vastu'],
] as const

function directDependencies(assetId: string): string[] {
  return registry.find((asset) => asset.asset_id === assetId)?.depends_on ?? []
}

function readinessFor(assetId: string, blockedUpstream?: string) {
  const directDeps = directDependencies(assetId)
  const throughput = new Map<string, ThroughputEntry>(
    directDeps.map((dependencyId) => [dependencyId, {
      asset_id: dependencyId,
      // bg_panchanga is a service contract: a fresh successful probe produces
      // service_ok, which is the planner's ready state for a service upstream.
      state: dependencyId === 'bg_panchanga' ? 'service_ok' : 'lit',
    }] as const),
  )
  const freshness = new Map(
    directDeps.map((dep) => [
      dep,
      dep === blockedUpstream
        ? { state: 'unknown' as const, reasons: ['receipt_missing'] }
        : { state: 'fresh' as const, reasons: [] },
    ] as const),
  )
  return { throughput, freshness }
}

describe('L0 dependency contracts — receipt-gated downstream eligibility', () => {
  it.each(contracts)('%s receipt withholds %s until it is fresh', (upstream, downstream) => {
    const blocked = resolveBuildPlan({
      scope: 'asset', scope_target: downstream, action: 'build', registry,
      ...readinessFor(downstream, upstream),
    })

    expect(blocked.status).toBe('blocked')
    expect(blocked.blockers).toEqual(expect.arrayContaining([
      expect.objectContaining({ dep_asset_id: upstream, dep_state: 'unknown', required_by: [downstream] }),
    ]))

    const eligible = resolveBuildPlan({
      scope: 'asset', scope_target: downstream, action: 'build', registry,
      ...readinessFor(downstream),
    })

    expect(eligible.status).toBe('ok')
    expect(eligible.plan_waves).toEqual([[downstream]])
  })
})

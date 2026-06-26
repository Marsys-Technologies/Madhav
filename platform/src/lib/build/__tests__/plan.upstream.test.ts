import { describe, it, expect } from 'vitest'
import { resolveBuildPlan, type RegistryEntry, type ThroughputEntry } from '../plan'

function reg(asset_id: string, layer: string, depends_on: string[]): RegistryEntry {
  return { asset_id, layer, depends_on, estimated_seconds: null }
}

function tp(asset_id: string, state: ThroughputEntry['state']): [string, ThroughputEntry] {
  return [asset_id, { asset_id, state }]
}

// Cross-layer registry: L2 asset depends on L1 which depends on L0
const CROSS_LAYER = [
  reg('bg_data', 'brahmagyan', []),
  reg('ga_data', 'ganita', ['bg_data']),
  reg('bo_analysis', 'bodha', ['ga_data']),
  reg('ph_result', 'phala', ['bo_analysis']),
]

describe('resolveBuildPlan — upstream-closure pull-in (A1 DAG fix)', () => {
  it('asset-scope build of downstream includes dormant upstream, ordered before target', () => {
    // ph_result is dormant; ga_data and bo_analysis are also dormant
    const throughput = new Map([tp('bg_data', 'lit')])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ph_result', action: 'build',
      registry: CROSS_LAYER, throughput,
    })
    expect(result.plan).toContain('ga_data')
    expect(result.plan).toContain('bo_analysis')
    expect(result.plan).toContain('ph_result')
    // upstream must precede the target
    expect(result.plan.indexOf('ga_data')).toBeLessThan(result.plan.indexOf('ph_result'))
    expect(result.plan.indexOf('bo_analysis')).toBeLessThan(result.plan.indexOf('ph_result'))
    // already-lit bg_data must NOT be included
    expect(result.plan).not.toContain('bg_data')
  })

  it('layer-scope build with dormant cross-layer upstream includes that upstream', () => {
    // Building 'phala' layer; bo_analysis (bodha) and ga_data (ganita) are dormant
    const throughput = new Map([tp('bg_data', 'lit')])
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'phala', action: 'build',
      registry: CROSS_LAYER, throughput,
    })
    expect(result.plan).toContain('ga_data')
    expect(result.plan).toContain('bo_analysis')
    expect(result.plan).toContain('ph_result')
    expect(result.plan.indexOf('ga_data')).toBeLessThan(result.plan.indexOf('ph_result'))
  })

  it('build does NOT pull in already-lit upstream (skip-if-lit)', () => {
    // Everything is lit except ph_result
    const throughput = new Map([
      tp('bg_data', 'lit'), tp('ga_data', 'lit'), tp('bo_analysis', 'lit'),
    ])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ph_result', action: 'build',
      registry: CROSS_LAYER, throughput,
    })
    expect(result.plan).toEqual(['ph_result'])
  })

  it('rebuild does NOT force-rebuild already-lit upstream', () => {
    // All upstream is lit; only ph_result is being rebuilt
    const throughput = new Map([
      tp('bg_data', 'lit'), tp('ga_data', 'lit'), tp('bo_analysis', 'lit'), tp('ph_result', 'lit'),
    ])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ph_result', action: 'rebuild',
      registry: CROSS_LAYER, throughput,
    })
    // rebuild of asset includes target + downstream (none here), not upstream
    expect(result.plan).toContain('ph_result')
    expect(result.plan).not.toContain('bg_data')
    expect(result.plan).not.toContain('ga_data')
    expect(result.plan).not.toContain('bo_analysis')
  })

  it('rebuild of layer with dormant cross-layer upstream includes missing upstream', () => {
    // Rebuilding bodha layer; ga_data (ganita) is dormant
    const throughput = new Map([tp('bg_data', 'lit'), tp('ph_result', 'lit')])
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'bodha', action: 'rebuild',
      registry: CROSS_LAYER, throughput,
    })
    expect(result.plan).toContain('ga_data')
    expect(result.plan).toContain('bo_analysis')
    expect(result.plan.indexOf('ga_data')).toBeLessThan(result.plan.indexOf('bo_analysis'))
    // lit upstream bg_data not included; lit downstream ph_result not included in layer rebuild
    expect(result.plan).not.toContain('bg_data')
  })

  it('empty depends_on root asset is still included (regression guard)', () => {
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'bg_data', action: 'build',
      registry: CROSS_LAYER, throughput: new Map(),
    })
    expect(result.plan).toEqual(['bg_data'])
  })

  it('global build is unaffected by the upstream-pull (all in scope)', () => {
    const throughput = new Map([tp('bg_data', 'lit')])
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'build',
      registry: CROSS_LAYER, throughput,
    })
    expect(result.plan).not.toContain('bg_data')
    expect(result.plan).toContain('ga_data')
    expect(result.plan).toContain('bo_analysis')
    expect(result.plan).toContain('ph_result')
  })

  it('includes_upstream_count reflects cross-scope assets pulled in', () => {
    const throughput = new Map([tp('bg_data', 'lit')])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ph_result', action: 'build',
      registry: CROSS_LAYER, throughput,
    })
    // ga_data and bo_analysis are outside the 'asset' scope target (ph_result)
    expect(result.includes_upstream_count).toBe(2)
  })
})

// ── L0 guard tests (native ruling 2026-06-26: bg_* never auto-pulled) ──────────
describe('resolveBuildPlan — L0 exclusion guard', () => {
  const REGISTRY_WITH_DORMANT_L0 = [
    reg('bg_ephemeris', 'brahmagyan', []),
    reg('ga_chart', 'ganita', ['bg_ephemeris']),
    reg('ga_other', 'ganita', []),
    reg('bo_analysis', 'bodha', ['ga_chart']),
  ]

  it('asset-scope build of L1 asset with dormant L0 dep → NOT in plan; L1 asset in blocked_assets', () => {
    // bg_ephemeris is dormant; ga_chart directly depends on it
    const throughput = new Map<string, ThroughputEntry>()
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ga_chart', action: 'build',
      registry: REGISTRY_WITH_DORMANT_L0, throughput,
    })
    // ga_chart blocked because bg_ephemeris (L0) is dormant
    expect(result.plan).not.toContain('ga_chart')
    expect(result.plan).not.toContain('bg_ephemeris')
    expect(result.blocked_assets.map(b => b.asset_id)).toContain('ga_chart')
    expect(result.blocked_assets[0]?.reason).toMatch(/bg_ephemeris/)
    expect(result.blocked_assets[0]?.reason).toMatch(/Brahmagyan/)
  })

  it('layer-scope build with dormant L0 dep blocks dependent assets but not independent ones', () => {
    // ga_chart depends on dormant bg_ephemeris; ga_other has no L0 dep → not blocked
    const throughput = new Map<string, ThroughputEntry>()
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'ganita', action: 'build',
      registry: REGISTRY_WITH_DORMANT_L0, throughput,
    })
    // ga_other (no L0 dep) → in plan
    expect(result.plan).toContain('ga_other')
    // ga_chart (depends on dormant L0) → blocked, not in plan
    expect(result.plan).not.toContain('ga_chart')
    expect(result.plan).not.toContain('bg_ephemeris')
    const blockedIds = result.blocked_assets.map(b => b.asset_id)
    expect(blockedIds).toContain('ga_chart')
    expect(blockedIds).not.toContain('ga_other')
  })

  it('L2 asset with transitive dormant L0 dep is also blocked', () => {
    // bo_analysis → ga_chart → bg_ephemeris (dormant)
    // When building bo_analysis with dormant L0, ga_chart gets pulled (non-L0) and then
    // both ga_chart and bo_analysis are blocked because their transitive L0 dep is dormant
    const throughput = new Map<string, ThroughputEntry>()
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'bo_analysis', action: 'build',
      registry: REGISTRY_WITH_DORMANT_L0, throughput,
    })
    expect(result.plan).not.toContain('bo_analysis')
    expect(result.plan).not.toContain('ga_chart')
    expect(result.plan).not.toContain('bg_ephemeris')
    const blockedIds = result.blocked_assets.map(b => b.asset_id)
    expect(blockedIds).toContain('bo_analysis')
    expect(blockedIds).toContain('ga_chart')
  })

  it('when L0 dep is lit, no blocking occurs and L0 is not auto-pulled', () => {
    // bg_ephemeris is lit; ga_chart can build normally
    const throughput = new Map([tp('bg_ephemeris', 'lit')])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ga_chart', action: 'build',
      registry: REGISTRY_WITH_DORMANT_L0, throughput,
    })
    expect(result.plan).toContain('ga_chart')
    expect(result.plan).not.toContain('bg_ephemeris')
    expect(result.blocked_assets).toHaveLength(0)
  })
})

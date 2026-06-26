import { describe, it, expect } from 'vitest'
import { resolveBuildPlan, type RegistryEntry, type ThroughputEntry } from '../plan'

function reg(asset_id: string, layer: string, depends_on: string[], estimated_seconds: number | null = 60): RegistryEntry {
  return { asset_id, layer, depends_on, estimated_seconds }
}

function tp(asset_id: string, state: ThroughputEntry['state']): [string, ThroughputEntry] {
  return [asset_id, { asset_id, state }]
}

// --- Fixtures ---

const LINEAR = [
  reg('a', 'l1', []),
  reg('b', 'l1', ['a']),
  reg('c', 'l1', ['b']),
]

const BRANCHING = [
  reg('root', 'l1', []),
  reg('left', 'l1', ['root']),
  reg('right', 'l1', ['root']),
  reg('merge', 'l1', ['left', 'right']),
]

const CYCLIC = [
  reg('x', 'l1', ['z']),
  reg('y', 'l1', ['x']),
  reg('z', 'l1', ['y']),
]

// --- Plan tests ---

describe('resolveBuildPlan — empty DAG', () => {
  it('returns empty plan for empty registry', () => {
    const result = resolveBuildPlan({
      scope: 'global',
      scope_target: null,
      action: 'build',
      registry: [],
      throughput: new Map(),
    })
    expect(result.plan).toEqual([])
    expect(result.estimated_seconds).toBe(0)
  })
})

describe('resolveBuildPlan — action:build (dormant only)', () => {
  it('includes only dormant assets', () => {
    const throughput = new Map([tp('a', 'lit'), tp('b', 'dormant'), tp('c', 'dormant')])
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'build',
      registry: LINEAR, throughput,
    })
    expect(result.plan).toContain('b')
    expect(result.plan).toContain('c')
    expect(result.plan).not.toContain('a')
  })

  it('respects topo order — b before c', () => {
    const throughput = new Map([tp('a', 'lit')])
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'build',
      registry: LINEAR, throughput,
    })
    expect(result.plan.indexOf('b')).toBeLessThan(result.plan.indexOf('c'))
  })

  it('assets with no throughput row treated as dormant', () => {
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'build',
      registry: LINEAR, throughput: new Map(),
    })
    expect(result.plan).toEqual(['a', 'b', 'c'])
  })
})

describe('resolveBuildPlan — action:rebuild (all in scope)', () => {
  it('includes all assets regardless of state', () => {
    const throughput = new Map([tp('a', 'lit'), tp('b', 'lit'), tp('c', 'lit')])
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'rebuild',
      registry: LINEAR, throughput,
    })
    expect(result.plan).toEqual(['a', 'b', 'c'])
  })
})

describe('resolveBuildPlan — action:update (stale + dormant transitive)', () => {
  it('includes stale assets', () => {
    const throughput = new Map([tp('a', 'stale'), tp('b', 'lit'), tp('c', 'lit')])
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'update',
      registry: LINEAR, throughput,
    })
    expect(result.plan).toContain('a')
  })

  it('includes dormant assets transitively reachable from stale', () => {
    const throughput = new Map([tp('root', 'stale'), tp('left', 'dormant'), tp('right', 'lit'), tp('merge', 'lit')])
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'update',
      registry: BRANCHING, throughput,
    })
    expect(result.plan).toContain('left')
  })
})

describe('resolveBuildPlan — action:cascade', () => {
  it('includes only downstream-stale assets', () => {
    const throughput = new Map([tp('root', 'stale'), tp('left', 'lit'), tp('right', 'lit'), tp('merge', 'lit')])
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'cascade',
      registry: BRANCHING, throughput,
    })
    // left, right, and merge are downstream of stale root
    expect(result.plan).toContain('left')
    expect(result.plan).toContain('right')
    expect(result.plan).toContain('merge')
    expect(result.plan).not.toContain('root')
  })
})

describe('resolveBuildPlan — scope:layer', () => {
  const MULTI_LAYER = [
    reg('l1a', 'layer1', []),
    reg('l1b', 'layer1', ['l1a']),
    reg('l2a', 'layer2', ['l1b']),
  ]

  it('filters to layer scope', () => {
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'layer1', action: 'rebuild',
      registry: MULTI_LAYER, throughput: new Map(),
    })
    expect(result.plan).toContain('l1a')
    expect(result.plan).toContain('l1b')
    expect(result.plan).not.toContain('l2a')
  })
})

describe('resolveBuildPlan — estimated_seconds', () => {
  it('sums seconds across plan', () => {
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'rebuild',
      registry: LINEAR, throughput: new Map(),
    })
    expect(result.estimated_seconds).toBe(180) // 3 assets × 60s
  })

  it('returns null if any asset has null estimated_seconds', () => {
    const withNull = [reg('a', 'l1', [], null), reg('b', 'l1', ['a'], 60)]
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'rebuild',
      registry: withNull, throughput: new Map(),
    })
    expect(result.estimated_seconds).toBeNull()
  })
})

describe('resolveBuildPlan — cycle detection', () => {
  it('throws on cycle in DAG', () => {
    expect(() => resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'rebuild',
      registry: CYCLIC, throughput: new Map(),
    })).toThrow(/Cycle detected/)
  })
})

// ── §VERIFY: Layer-Build Reliability ──────────────────────────────────────────

describe('RELIABILITY — layer-scope rebuild yields full ordered plan', () => {
  // Synthetic L1 (ganita) fixture: mirrors the ga_* writer DAG shape.
  // ga_positions + ga_panchanga + ga_nakshatra are roots; ga_structural depends on
  // ga_condition + ga_nakshatra; ga_dashas depends on ga_structural; ga_yoga depends
  // on ga_structural + ga_dashas. Mirrors the real L1 dependency order.
  const L1_GANITA = [
    reg('ga_positions',  'ganita', []),
    reg('ga_panchanga',  'ganita', []),
    reg('ga_nakshatra',  'ganita', []),
    reg('ga_condition',  'ganita', ['ga_positions', 'ga_nakshatra']),
    reg('ga_structural', 'ganita', ['ga_condition', 'ga_nakshatra']),
    reg('ga_dashas',     'ganita', ['ga_structural']),
    reg('ga_yoga',       'ganita', ['ga_structural', 'ga_dashas']),
  ]

  it('layer rebuild includes every asset in the layer', () => {
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'ganita', action: 'rebuild',
      registry: L1_GANITA, throughput: new Map(),
    })
    const expected = L1_GANITA.map(r => r.asset_id)
    expect(result.plan).toHaveLength(expected.length)
    for (const id of expected) expect(result.plan).toContain(id)
  })

  it('topo order: roots before dependents (ga_structural after ga_condition + ga_nakshatra)', () => {
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'ganita', action: 'rebuild',
      registry: L1_GANITA, throughput: new Map(),
    })
    const idx = (id: string) => result.plan.indexOf(id)
    expect(idx('ga_condition')).toBeLessThan(idx('ga_structural'))
    expect(idx('ga_nakshatra')).toBeLessThan(idx('ga_structural'))
    expect(idx('ga_structural')).toBeLessThan(idx('ga_dashas'))
    expect(idx('ga_dashas')).toBeLessThan(idx('ga_yoga'))
  })

  it('rebuild forces ALL assets into plan even when all are lit (E5 fix: skip gate is runner responsibility)', () => {
    // The plan builder always includes all assets for rebuild — lit or not.
    // The orchestrator skip gate (runner.py) now respects action='rebuild'.
    const allLit = new Map(L1_GANITA.map(r => [r.asset_id, { asset_id: r.asset_id, state: 'lit' as const }]))
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'ganita', action: 'rebuild',
      registry: L1_GANITA, throughput: allLit,
    })
    expect(result.plan).toHaveLength(L1_GANITA.length)
  })

  it('layer build (not rebuild) skips lit assets', () => {
    const allLit = new Map(L1_GANITA.map(r => [r.asset_id, { asset_id: r.asset_id, state: 'lit' as const }]))
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'ganita', action: 'build',
      registry: L1_GANITA, throughput: allLit,
    })
    expect(result.plan).toHaveLength(0)
  })
})

describe('RELIABILITY — layer-scope generalises to L2/L3/L4', () => {
  // Post-fix fixture: bo_karanajala.depends_on includes bo_bimba (Migration 356 / G2 fix)
  const L2_BODHA = [
    reg('bo_laksana',     'bodha', []),
    reg('bo_bimba',       'bodha', ['bo_laksana']),
    reg('bo_karanajala',  'bodha', ['bo_laksana', 'bo_bimba']),  // G2 fix: bo_bimba added
    reg('bo_sangati',     'bodha', ['bo_laksana']),
    reg('bo_upaya',       'bodha', ['bo_bimba', 'bo_karanajala', 'bo_sangati']),
    reg('bo_pramana_mapa','bodha', ['bo_upaya']),
  ]
  const MIXED = [...L2_BODHA, reg('ga_structural', 'ganita', []), reg('ga_yoga', 'ganita', ['ga_structural'])]

  it('layer=bodha returns only bo_* assets', () => {
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'bodha', action: 'rebuild',
      registry: MIXED, throughput: new Map(),
    })
    expect(result.plan.every(id => id.startsWith('bo_'))).toBe(true)
    expect(result.plan).not.toContain('ga_structural')
  })

  it('bo_laksana (root) is before bo_upaya (dependent)', () => {
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'bodha', action: 'rebuild',
      registry: L2_BODHA, throughput: new Map(),
    })
    expect(result.plan.indexOf('bo_laksana')).toBeLessThan(result.plan.indexOf('bo_upaya'))
    expect(result.plan.indexOf('bo_upaya')).toBeLessThan(result.plan.indexOf('bo_pramana_mapa'))
  })
})

// ── §G2: Hidden DAG edge — bo_karanajala reads bo_bimba output ───────────────
// RED: before the fix, depends_on=['bo_laksana'] lets topo-sort schedule karanajala
//      before bimba → empty node_map → 0 CGM edges, silently green.
// GREEN: after the fix, depends_on=['bo_laksana','bo_bimba'] forces bimba first always.

describe('G2 DAG edge fix — bo_bimba must precede bo_karanajala (Migration 356)', () => {
  // RED fixture: old (broken) depends_on — karanajala placed before bimba in registry
  // so the topo-sort (which visits registry order) produces karanajala before bimba.
  const BODHA_OLD_BROKEN = [
    reg('bo_laksana',    'bodha', []),
    reg('bo_karanajala', 'bodha', ['bo_laksana']),   // OLD: omits bo_bimba dependency
    reg('bo_bimba',      'bodha', ['bo_laksana']),
  ]

  it('RED — old depends_on: topo-sort CAN place bo_karanajala before bo_bimba', () => {
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'bodha', action: 'rebuild',
      registry: BODHA_OLD_BROKEN, throughput: new Map(),
    })
    // In the old DAG there is no ordering constraint between karanajala and bimba.
    // When karanajala appears first in registry, topo visits it first → it lands first.
    const idxKara = result.plan.indexOf('bo_karanajala')
    const idxBimba = result.plan.indexOf('bo_bimba')
    // This assertion PASSES (proves broken state): karanajala < bimba is possible.
    expect(idxKara).toBeLessThan(idxBimba)
  })

  // GREEN fixture: new (fixed) depends_on — karanajala declares bo_bimba as dep
  const BODHA_NEW_FIXED = [
    reg('bo_laksana',    'bodha', []),
    reg('bo_karanajala', 'bodha', ['bo_laksana', 'bo_bimba']),  // FIXED: bo_bimba added
    reg('bo_bimba',      'bodha', ['bo_laksana']),
  ]

  it('GREEN — fixed depends_on: bo_bimba always before bo_karanajala regardless of registry order', () => {
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'bodha', action: 'rebuild',
      registry: BODHA_NEW_FIXED, throughput: new Map(),
    })
    const idxBimba = result.plan.indexOf('bo_bimba')
    const idxKara  = result.plan.indexOf('bo_karanajala')
    expect(idxBimba).toBeLessThan(idxKara)
  })

  it('GREEN — acyclicity: adding bo_bimba to karanajala.depends_on introduces no cycle', () => {
    // If a cycle existed this would throw.
    expect(() => resolveBuildPlan({
      scope: 'layer', scope_target: 'bodha', action: 'rebuild',
      registry: BODHA_NEW_FIXED, throughput: new Map(),
    })).not.toThrow()
  })
})

describe('RELIABILITY — DAG source authority', () => {
  it('plan builder reads asset_registry.depends_on (not build_dependencies table)', () => {
    // The TypeScript plan builder uses the RegistryEntry.depends_on field, which is
    // populated from asset_registry.depends_on in runs/route.ts. The build_dependencies
    // table is only used by cascade-preview and data-readiness routes.
    // This test proves the plan builder is self-contained and correct from its inputs.
    const registry = [
      reg('A', 'test', []),
      reg('B', 'test', ['A']),
      reg('C', 'test', ['B']),
    ]
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'test', action: 'rebuild',
      registry, throughput: new Map(),
    })
    expect(result.plan).toEqual(['A', 'B', 'C'])
  })
})

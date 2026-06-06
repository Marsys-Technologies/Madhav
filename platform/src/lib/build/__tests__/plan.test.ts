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

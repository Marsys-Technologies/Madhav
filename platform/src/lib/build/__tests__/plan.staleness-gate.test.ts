import { describe, it, expect } from 'vitest'
import { checkStalenessGate, type RegistryEntry, type ThroughputEntry } from '../plan'

function reg(asset_id: string, layer: string, depends_on: string[]): RegistryEntry {
  return { asset_id, layer, depends_on, estimated_seconds: null }
}
function tp(asset_id: string, state: ThroughputEntry['state']): [string, ThroughputEntry] {
  return [asset_id, { asset_id, state }]
}

const REGISTRY = [
  reg('ga_positions', 'ganita', []),
  reg('bo_laksana', 'bodha', ['ga_positions']),
  reg('bo_bimba', 'bodha', ['bo_laksana']),
  reg('ph_result', 'phala', ['bo_bimba']),
]

describe('checkStalenessGate', () => {
  it('returns empty when all out-of-plan upstream are lit', () => {
    const throughput = new Map([tp('ga_positions', 'lit'), tp('bo_laksana', 'lit')])
    const result = checkStalenessGate(['bo_bimba'], REGISTRY, throughput)
    expect(result).toHaveLength(0)
  })

  it('returns stale dep when direct upstream is stale', () => {
    const throughput = new Map([tp('ga_positions', 'lit'), tp('bo_laksana', 'stale')])
    const result = checkStalenessGate(['bo_bimba'], REGISTRY, throughput)
    expect(result).toHaveLength(1)
    expect(result[0].asset_id).toBe('bo_laksana')
    expect(result[0].state).toBe('stale')
    expect(result[0].required_by).toContain('bo_bimba')
  })

  it('does NOT flag in-plan deps — DAG handles those', () => {
    const throughput = new Map([tp('ga_positions', 'lit'), tp('bo_laksana', 'stale')])
    const result = checkStalenessGate(['bo_laksana', 'bo_bimba'], REGISTRY, throughput)
    expect(result).toHaveLength(0)
  })

  it('flags out-of-plan stale dep even when an in-plan asset is also stale', () => {
    // bo_laksana: out-of-plan dep of bo_bimba (in-plan) — stale → flagged
    // bo_bimba: in-plan (will be rebuilt by DAG) — NOT flagged even though stale
    // Gate blocks via bo_laksana; DAG rebuilds bo_bimba on fresh bo_laksana after user fixes bo_laksana
    const throughput = new Map([tp('bo_laksana', 'stale'), tp('bo_bimba', 'stale')])
    const result = checkStalenessGate(['bo_bimba', 'ph_result'], REGISTRY, throughput)
    const ids = result.map(r => r.asset_id)
    expect(ids).toContain('bo_laksana')
    expect(ids).not.toContain('bo_bimba')
    expect(result).toHaveLength(1)
  })

  it('does NOT flag dormant upstream — auto-pull or L0-gate handles those', () => {
    const throughput = new Map([tp('bo_laksana', 'dormant')])
    const result = checkStalenessGate(['bo_bimba'], REGISTRY, throughput)
    expect(result).toHaveLength(0)
  })

  it('returns empty for a root asset with no upstream', () => {
    const result = checkStalenessGate(['ga_positions'], REGISTRY, new Map())
    expect(result).toHaveLength(0)
  })

  it('same dep required by multiple plan assets is returned once with all required_by', () => {
    const REG2 = [
      reg('ga_positions', 'ganita', []),
      reg('bo_laksana', 'bodha', ['ga_positions']),
      reg('bo_bimba', 'bodha', ['ga_positions']),
    ]
    const throughput = new Map([tp('ga_positions', 'stale')])
    const result = checkStalenessGate(['bo_laksana', 'bo_bimba'], REG2, throughput)
    expect(result).toHaveLength(1)
    expect(result[0].asset_id).toBe('ga_positions')
    expect(result[0].required_by).toContain('bo_laksana')
    expect(result[0].required_by).toContain('bo_bimba')
  })

  it('does NOT flag service_ok upstream — treated same as lit', () => {
    const throughput = new Map([tp('ga_chart_service', 'service_ok')])
    const SREG = [
      reg('ga_chart_service', 'ganita', []),
      reg('bo_laksana', 'bodha', ['ga_chart_service']),
    ]
    const result = checkStalenessGate(['bo_laksana'], SREG, throughput)
    expect(result).toHaveLength(0)
  })
})

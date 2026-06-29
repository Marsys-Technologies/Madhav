import { describe, it, expect } from 'vitest'
import { preflight } from '../plan'
import type { RegistryEntry, ThroughputEntry } from '../plan'

function reg(asset_id: string, layer: string, depends_on: string[] = []): RegistryEntry {
  return { asset_id, layer, depends_on, estimated_seconds: null }
}
function tp(asset_id: string, state: string): [string, ThroughputEntry] {
  return [asset_id, { asset_id, state: state as ThroughputEntry['state'] }]
}

const REGISTRY = [
  reg('bg_texts', 'brahmagyan'),
  reg('ga_positions', 'ganita', ['bg_texts']),
  reg('bo_bimba', 'bodha', ['ga_positions']),
  reg('ka_sangam', 'kala', ['bo_bimba', 'ga_positions']),
  reg('ka_vighnakara', 'kala', ['ka_sangam']),
  reg('ka_kalasutra', 'kala', ['bo_bimba']),
]

describe('preflight() — single asset scope', () => {
  it('blocks when a direct dep is stale', () => {
    const throughput = new Map([
      tp('bg_texts', 'lit'), tp('ga_positions', 'lit'), tp('bo_bimba', 'stale'),
    ])
    const result = preflight(['ka_sangam'], 'asset', 'ka_sangam', REGISTRY, throughput)
    expect(result).toHaveLength(1)
    expect(result[0].dep_asset_id).toBe('bo_bimba')
    expect(result[0].dep_state).toBe('stale')
    expect(result[0].required_by).toContain('ka_sangam')
  })

  it('blocks when a direct dep is dormant', () => {
    const throughput = new Map([tp('ga_positions', 'lit'), tp('bo_bimba', 'dormant')])
    const result = preflight(['ka_sangam'], 'asset', 'ka_sangam', REGISTRY, throughput)
    expect(result[0].dep_state).toBe('dormant')
  })

  it('blocks when a direct dep is in error', () => {
    const throughput = new Map([tp('ga_positions', 'lit'), tp('bo_bimba', 'error')])
    const result = preflight(['ka_sangam'], 'asset', 'ka_sangam', REGISTRY, throughput)
    expect(result[0].dep_state).toBe('error')
  })

  it('blocks when a direct dep is service_down', () => {
    const throughput = new Map([tp('ga_positions', 'lit'), tp('bo_bimba', 'service_down')])
    const result = preflight(['ka_sangam'], 'asset', 'ka_sangam', REGISTRY, throughput)
    expect(result[0].dep_state).toBe('service_down')
  })

  it('returns empty when all deps are lit', () => {
    const throughput = new Map([tp('ga_positions', 'lit'), tp('bo_bimba', 'lit')])
    const result = preflight(['ka_sangam'], 'asset', 'ka_sangam', REGISTRY, throughput)
    expect(result).toEqual([])
  })

  it('treats service_ok as ready', () => {
    const throughput = new Map([tp('ga_positions', 'service_ok'), tp('bo_bimba', 'lit')])
    const result = preflight(['ka_sangam'], 'asset', 'ka_sangam', REGISTRY, throughput)
    expect(result).toEqual([])
  })

  it('L0 dormant dep includes guidance message', () => {
    const throughput = new Map([tp('bg_texts', 'dormant')])
    const result = preflight(['ga_positions'], 'asset', 'ga_positions', REGISTRY, throughput)
    expect(result).toHaveLength(1)
    expect(result[0].dep_asset_id).toBe('bg_texts')
    expect(result[0].guidance).toBe("L0 dependency not built — run the Brahmagyan layer first")
  })
})

describe('preflight() — layer scope', () => {
  it('blocks when any cross-layer dep is stale', () => {
    const throughput = new Map([tp('ga_positions', 'stale'), tp('bo_bimba', 'lit')])
    const candidates = ['ka_sangam', 'ka_vighnakara', 'ka_kalasutra']
    const result = preflight(candidates, 'layer', 'kala', REGISTRY, throughput)
    const blocker = result.find(b => b.dep_asset_id === 'ga_positions')
    expect(blocker).toBeDefined()
    expect(blocker?.required_by).toContain('ka_sangam')
    expect(blocker?.required_by).toContain('ka_kalasutra')
  })

  it('does NOT flag intra-layer deps — DAG handles them', () => {
    const throughput = new Map([tp('ga_positions', 'lit'), tp('bo_bimba', 'lit')])
    const candidates = ['ka_sangam', 'ka_vighnakara', 'ka_kalasutra']
    const result = preflight(candidates, 'layer', 'kala', REGISTRY, throughput)
    expect(result).toEqual([])
  })
})

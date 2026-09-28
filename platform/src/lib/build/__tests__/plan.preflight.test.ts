import { describe, it, expect } from 'vitest'
import { preflight } from '../plan'
import type { RegistryEntry, ThroughputEntry } from '../plan'

function reg(asset_id: string, layer: string, depends_on: string[] = []): RegistryEntry {
  return { asset_id, layer, depends_on, estimated_seconds: null }
}

function serviceReg(
  asset_id: string,
  service_health: 'healthy' | 'unhealthy' | null,
  has_writer = false,
): RegistryEntry {
  return {
    asset_id, layer: 'brahmagyan', depends_on: [], estimated_seconds: null,
    asset_kind: 'service', service_health, has_writer,
  }
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

  it('accepts a freshly probed healthy service whose only unknown is the inapplicable relational output spec', () => {
    const registry = [
      serviceReg('bg_panchanga', 'healthy'),
      reg('ga_panchanga', 'ganita', ['bg_panchanga']),
    ]
    const result = preflight(
      ['ga_panchanga'],
      'asset',
      'ga_panchanga',
      registry,
      new Map([tp('bg_panchanga', 'service_ok')]),
      new Map([['bg_panchanga', { state: 'unknown', reasons: ['output_digest_spec_unavailable'] }]]),
    )

    expect(result).toEqual([])
  })

  it('accepts a successful healthy writer-backed service self-test with no relational output contract', () => {
    const registry = [
      serviceReg('ka_muhurta_seva', 'healthy', true),
      reg('ka_sangam', 'kala', ['ka_muhurta_seva']),
    ]
    const result = preflight(
      ['ka_sangam'],
      'asset',
      'ka_sangam',
      registry,
      new Map([tp('ka_muhurta_seva', 'lit')]),
      new Map([['ka_muhurta_seva', {
        state: 'unknown',
        reasons: ['output_digest_spec_unavailable', 'output_digest_unavailable'],
      }]]),
    )

    expect(result).toEqual([])
  })

  it.each([
    ['missing probe receipt', undefined, 'healthy', 'service_ok'],
    ['extra unknown evidence', { state: 'unknown' as const, reasons: ['output_digest_spec_unavailable', 'code_digest_unavailable'] }, 'healthy', 'service_ok'],
    ['stale service receipt', { state: 'stale' as const, reasons: ['registry_changed'] }, 'healthy', 'service_ok'],
    ['unhealthy live service', { state: 'unknown' as const, reasons: ['output_digest_spec_unavailable'] }, 'unhealthy', 'service_ok'],
    ['historical lit state without current probe', { state: 'unknown' as const, reasons: ['output_digest_spec_unavailable'] }, 'healthy', 'lit'],
  ])('does not bypass service readiness for %s', (_label, receipt, health, throughputState) => {
    const registry = [
      serviceReg('bg_panchanga', health as 'healthy' | 'unhealthy'),
      reg('ga_panchanga', 'ganita', ['bg_panchanga']),
    ]
    const freshness = new Map<string, { state: 'fresh' | 'stale' | 'unknown'; reasons: string[] }>()
    if (receipt) freshness.set('bg_panchanga', receipt)

    const result = preflight(
      ['ga_panchanga'],
      'asset',
      'ga_panchanga',
      registry,
      new Map([tp('bg_panchanga', throughputState)]),
      freshness,
    )

    expect(result).toEqual([
      expect.objectContaining({ dep_asset_id: 'bg_panchanga', required_by: ['ga_panchanga'] }),
    ])
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

import { describe, it, expect } from 'vitest'
import { computeWaves } from '../plan'
import type { RegistryEntry } from '../plan'

function reg(asset_id: string, layer: string, depends_on: string[] = []): RegistryEntry {
  return { asset_id, layer, depends_on, estimated_seconds: null }
}

describe('computeWaves()', () => {
  it('single asset always produces one wave', () => {
    const registry = [reg('ka_sangam', 'kala', ['bo_bimba'])]
    const waves = computeWaves(['ka_sangam'], registry, 'asset', 'ka_sangam')
    expect(waves).toEqual([['ka_sangam']])
  })

  it('two independent assets produce one wave', () => {
    const registry = [
      reg('ka_kalasutra', 'kala', ['bo_bimba']),
      reg('ka_vighnakara', 'kala', ['ga_positions']),
    ]
    const waves = computeWaves(['ka_kalasutra', 'ka_vighnakara'], registry, 'layer', 'kala')
    expect(waves).toHaveLength(1)
    expect(waves[0]).toContain('ka_kalasutra')
    expect(waves[0]).toContain('ka_vighnakara')
  })

  it('sequential intra-layer deps produce sequential waves', () => {
    const registry = [
      reg('ka_a', 'kala'),
      reg('ka_b', 'kala', ['ka_a']),
      reg('ka_c', 'kala', ['ka_b']),
    ]
    const waves = computeWaves(['ka_a', 'ka_b', 'ka_c'], registry, 'layer', 'kala')
    expect(waves).toHaveLength(3)
    expect(waves[0]).toEqual(['ka_a'])
    expect(waves[1]).toEqual(['ka_b'])
    expect(waves[2]).toEqual(['ka_c'])
  })

  it('diamond dependency produces correct wave levels', () => {
    const registry = [
      reg('ka_root', 'kala'),
      reg('ka_left', 'kala', ['ka_root']),
      reg('ka_right', 'kala', ['ka_root']),
      reg('ka_tip', 'kala', ['ka_left', 'ka_right']),
    ]
    const waves = computeWaves(['ka_root', 'ka_left', 'ka_right', 'ka_tip'], registry, 'layer', 'kala')
    expect(waves).toHaveLength(3)
    expect(waves[0]).toEqual(['ka_root'])
    expect(waves[1].sort()).toEqual(['ka_left', 'ka_right'].sort())
    expect(waves[2]).toEqual(['ka_tip'])
  })

  it('cross-layer deps are ignored in layer scope wave computation', () => {
    const registry = [
      reg('bo_bimba', 'bodha'),
      reg('ka_sangam', 'kala', ['bo_bimba']),
      reg('ka_vighnakara', 'kala', ['ka_sangam']),
    ]
    // Layer scope: ka_sangam's dep on bo_bimba (bodha layer) is cross-layer and NOT counted
    // ka_vighnakara depends on ka_sangam (intra-layer) → goes in wave 1
    const waves = computeWaves(['ka_sangam', 'ka_vighnakara'], registry, 'layer', 'kala')
    expect(waves).toHaveLength(2)
    expect(waves[0]).toEqual(['ka_sangam'])
    expect(waves[1]).toEqual(['ka_vighnakara'])
  })

  it('global scope counts cross-layer deps for wave assignment', () => {
    const registry = [
      reg('ga_positions', 'ganita'),
      reg('bo_bimba', 'bodha', ['ga_positions']),
    ]
    const waves = computeWaves(['ga_positions', 'bo_bimba'], registry, 'global', null)
    expect(waves).toHaveLength(2)
    expect(waves[0]).toEqual(['ga_positions'])
    expect(waves[1]).toEqual(['bo_bimba'])
  })
})

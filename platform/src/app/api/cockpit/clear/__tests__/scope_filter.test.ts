import { describe, it, expect } from 'vitest'
import { filterScopeAssets, type RegistryRow } from '@/lib/cockpit/clearScopeFilter'

const REGISTRY: RegistryRow[] = [
  { asset_id: 'bg_ephemeris',  layer: 'brahmagyan', scope: 'global',    target_table: 'ephemeris_daily' },
  { asset_id: 'bg_texts',      layer: 'brahmagyan', scope: 'global',    target_table: 'classical_text_chunks' },
  { asset_id: 'bg_ontology',   layer: 'brahmagyan', scope: 'global',    target_table: 'brahma_ontology' },
  { asset_id: 'ga_positions',  layer: 'ganita',     scope: 'per_chart', target_table: 'chart_facts' },
  { asset_id: 'bo_signals',    layer: 'bodha',      scope: 'per_chart', target_table: 'bodha_signals' },
  { asset_id: 'ka_transits',   layer: 'kala',       scope: 'per_chart', target_table: 'kala_transits' },
]

describe('filterScopeAssets', () => {
  it('super_admin global-scope: returns per_chart only, EXCLUDES L0 brahmagyan globals', () => {
    // L0 GATE (native ruling 2026-06-26): a global clear never includes L0, even for
    // super_admin. The bg_* brahmagyan globals must be absent — they are cleared only
    // via explicit layer='brahmagyan' or individual bg_* asset scope.
    const result = filterScopeAssets(REGISTRY, 'global', null, ['per_chart', 'global'])
    expect(result.map(r => r.asset_id)).toEqual(['ga_positions', 'bo_signals', 'ka_transits'])
    expect(result.some(r => r.layer === 'brahmagyan')).toBe(false)
  })

  it('non-super-admin global-scope: returns per_chart only', () => {
    const result = filterScopeAssets(REGISTRY, 'global', null, ['per_chart'])
    expect(result.map(r => r.asset_id)).toEqual(['ga_positions', 'bo_signals', 'ka_transits'])
  })

  it('super_admin layer-scope brahmagyan: returns L0 globals', () => {
    const result = filterScopeAssets(REGISTRY, 'layer', 'brahmagyan', ['per_chart', 'global'])
    expect(result.map(r => r.asset_id)).toEqual(['bg_ephemeris', 'bg_texts', 'bg_ontology'])
  })

  it('non-super-admin layer-scope brahmagyan: returns empty (403 handled upstream)', () => {
    const result = filterScopeAssets(REGISTRY, 'layer', 'brahmagyan', ['per_chart'])
    expect(result).toHaveLength(0)
  })

  it('super_admin layer-scope ganita: returns per_chart ganita assets', () => {
    const result = filterScopeAssets(REGISTRY, 'layer', 'ganita', ['per_chart', 'global'])
    expect(result.map(r => r.asset_id)).toEqual(['ga_positions'])
  })

  it('super_admin asset-scope global asset: returns the single global asset', () => {
    const result = filterScopeAssets(REGISTRY, 'asset', 'bg_ephemeris', ['per_chart', 'global'])
    expect(result).toHaveLength(1)
    expect(result[0].asset_id).toBe('bg_ephemeris')
  })

  it('non-super-admin asset-scope global asset: returns empty (403 handled upstream)', () => {
    const result = filterScopeAssets(REGISTRY, 'asset', 'bg_ephemeris', ['per_chart'])
    expect(result).toHaveLength(0)
  })

  it('super_admin asset-scope per_chart asset: returns the asset', () => {
    const result = filterScopeAssets(REGISTRY, 'asset', 'ga_positions', ['per_chart', 'global'])
    expect(result).toHaveLength(1)
    expect(result[0].scope).toBe('per_chart')
  })
})

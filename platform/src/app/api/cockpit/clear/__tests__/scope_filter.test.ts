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

/**
 * B1 — Kāla pre-elevation Phase 1.1. `filterScopeAssets` is the second of the
 * two independent layers that keep a RETIRED asset out of a Clear (the first is
 * the `is_active` predicate on the routes' own registry SELECT). Neither is
 * allowed to be the only load-bearing one.
 *
 * Semantics chosen deliberately: only an EXPLICIT `is_active === false` excludes.
 * `undefined` (a caller that did not select the column) and `true` both pass, so
 * this filter narrows the route's already-filtered set rather than silently
 * emptying a scope for a caller that shapes its rows differently. Production has
 * exactly one row with `is_active IS NOT TRUE` — `ka_gochara_sweep` — and zero
 * NULLs (measured 2026-09-22: 0 null / 1 false / 128 true).
 */
const REGISTRY_WITH_RETIRED: RegistryRow[] = [
  { asset_id: 'ka_kshetra',       layer: 'kala', scope: 'per_chart', target_table: 'kala_field',            is_active: true },
  { asset_id: 'ka_gochara_sweep', layer: 'kala', scope: 'per_chart', target_table: 'kala_gochara_windows',  is_active: false },
  { asset_id: 'ka_sangam',        layer: 'kala', scope: 'per_chart', target_table: 'kala_convergence' },
]

describe('filterScopeAssets — B1 retired-asset exclusion', () => {
  it('layer scope excludes an is_active=false asset', () => {
    const result = filterScopeAssets(REGISTRY_WITH_RETIRED, 'layer', 'kala', ['per_chart'])
    expect(result.map(r => r.asset_id)).toEqual(['ka_kshetra', 'ka_sangam'])
  })

  it('global scope excludes an is_active=false asset', () => {
    const result = filterScopeAssets(REGISTRY_WITH_RETIRED, 'global', null, ['per_chart'])
    expect(result.map(r => r.asset_id)).not.toContain('ka_gochara_sweep')
  })

  it('a DIRECT asset-scope request for the retired asset returns nothing', () => {
    const result = filterScopeAssets(REGISTRY_WITH_RETIRED, 'asset', 'ka_gochara_sweep', ['per_chart'])
    expect(result).toHaveLength(0)
  })

  it('asset_set scope excludes it even when explicitly named in the set', () => {
    const result = filterScopeAssets(
      REGISTRY_WITH_RETIRED, 'asset_set', 'ka_kshetra,ka_gochara_sweep', ['per_chart']
    )
    expect(result.map(r => r.asset_id)).toEqual(['ka_kshetra'])
  })

  it('a row with no is_active field is NOT excluded — the filter narrows, it does not invent', () => {
    const result = filterScopeAssets(REGISTRY_WITH_RETIRED, 'asset', 'ka_sangam', ['per_chart'])
    expect(result.map(r => r.asset_id)).toEqual(['ka_sangam'])
  })
})

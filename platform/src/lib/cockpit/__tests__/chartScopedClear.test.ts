import { describe, it, expect } from 'vitest'
import { resolveChartScopedClear, type RegistryRow } from '@/lib/cockpit/clearScopeFilter'

const REGISTRY: RegistryRow[] = [
  { asset_id: 'bg_ephemeris', layer: 'brahmagyan', scope: 'global', target_table: 'ephemeris_daily' },
  { asset_id: 'mi_kula', layer: 'mimamsa', scope: 'global', target_table: 'mimamsa_signal_families' },
  { asset_id: 'mi_vistara', layer: 'mimamsa', scope: 'global', target_table: 'mimamsa_export_log' },
  { asset_id: 'mi_abhilekha', layer: 'mimamsa', scope: 'per_chart', target_table: 'mimamsa_journal' },
  { asset_id: 'ga_positions', layer: 'ganita', scope: 'per_chart', target_table: 'chart_facts' },
  { asset_id: 'bo_signals', layer: 'bodha', scope: 'per_chart', target_table: 'bodha_signals' },
]

describe('resolveChartScopedClear (a chart page may only ever clear per-chart data)', () => {
  it('refuses an explicit single global asset, in plain words, with a 4xx code', () => {
    const r = resolveChartScopedClear(REGISTRY, 'asset', 'bg_ephemeris')
    expect(r.ok).toBe(false)
    if (r.ok) return
    expect(r.status).toBe(422)
    expect(r.code).toBe('GLOBAL_CLEAR_FORBIDDEN')
    expect(r.error).toMatch(/shared by every chart/i)
    expect(r.error).toContain('bg_ephemeris')
  })

  it('refuses an asset_set that names any global asset, even mixed with per-chart ones', () => {
    const r = resolveChartScopedClear(REGISTRY, 'asset_set', 'ga_positions,mi_kula')
    expect(r.ok).toBe(false)
    if (r.ok) return
    expect(r.code).toBe('GLOBAL_CLEAR_FORBIDDEN')
    expect(r.error).toContain('mi_kula')
  })

  it('refuses a layer clear of a layer that holds only global assets (L0)', () => {
    const r = resolveChartScopedClear(REGISTRY, 'layer', 'brahmagyan')
    expect(r.ok).toBe(false)
    if (r.ok) return
    expect(r.code).toBe('GLOBAL_CLEAR_FORBIDDEN')
  })

  it('a mixed layer sweep clears only the per-chart assets and reports the global ones left untouched', () => {
    const r = resolveChartScopedClear(REGISTRY, 'layer', 'mimamsa')
    expect(r.ok).toBe(true)
    if (!r.ok) return
    expect(r.assets.map(a => a.asset_id)).toEqual(['mi_abhilekha'])
    expect(r.globalAssetsLeftUntouched).toEqual(['mi_kula', 'mi_vistara'])
  })

  it('a global-scope sweep never includes a global asset', () => {
    const r = resolveChartScopedClear(REGISTRY, 'global', null)
    expect(r.ok).toBe(true)
    if (!r.ok) return
    expect(r.assets.map(a => a.asset_id)).toEqual(['mi_abhilekha', 'ga_positions', 'bo_signals'])
    expect(r.assets.some(a => a.scope === 'global')).toBe(false)
  })

  it('a chart-scoped clear of a per-chart asset is allowed unchanged', () => {
    const r = resolveChartScopedClear(REGISTRY, 'asset', 'ga_positions')
    expect(r.ok).toBe(true)
    if (!r.ok) return
    expect(r.assets.map(a => a.asset_id)).toEqual(['ga_positions'])
    expect(r.globalAssetsLeftUntouched).toEqual([])
  })
})

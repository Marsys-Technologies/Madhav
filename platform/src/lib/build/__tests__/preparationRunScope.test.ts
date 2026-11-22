import { describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

import { isPreparationRunScope, preparationRunScopeSql } from '../preparationRunScope'

describe('NIR-05 preparationRunScope', () => {
  it('recognizes global, whole-layer ganita/bodha, and partial L1/L2 asset_set scopes', () => {
    expect(isPreparationRunScope('global', null)).toBe(true)
    expect(isPreparationRunScope('layer', 'ganita')).toBe(true)
    expect(isPreparationRunScope('layer', 'bodha')).toBe(true)
    expect(isPreparationRunScope('asset_set', 'ga_positions')).toBe(true)
    expect(isPreparationRunScope('asset_set', ' bo_laksana , ka_kshetra ')).toBe(true)
    expect(isPreparationRunScope('asset_set', 'ga_positions,bo_laksana')).toBe(true)

    expect(isPreparationRunScope('layer', 'kala')).toBe(false)
    expect(isPreparationRunScope('layer', 'brahmagyan')).toBe(false)
    expect(isPreparationRunScope('layer', null)).toBe(false)
    expect(isPreparationRunScope('asset_set', 'ka_kshetra,ph_pramana')).toBe(false)
    expect(isPreparationRunScope('asset', 'ga_positions')).toBe(false)
  })

  it('emits matching SQL predicates for r and build_runs', () => {
    for (const alias of ['r', 'build_runs'] as const) {
      const sql = preparationRunScopeSql(alias)
      expect(sql).toContain(`${alias}.scope = 'global'`)
      expect(sql).toContain(`${alias}.scope = 'layer' AND ${alias}.scope_target IN ('ganita', 'bodha')`)
      expect(sql).toContain(`${alias}.scope = 'asset_set'`)
      expect(sql).toContain('(ga|bo)_[a-z0-9_]+')
    }
  })
})

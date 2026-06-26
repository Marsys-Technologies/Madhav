import { describe, it, expect } from 'vitest'
import { ASSETS } from '../seed/asset_registry_seed'

describe('asset_registry_seed — catalog reconciliation', () => {
  const assetIds = new Set(ASSETS.map(a => a.asset_id))

  it('has no duplicate asset_ids', () => {
    const ids = ASSETS.map(a => a.asset_id)
    const unique = new Set(ids)
    expect(ids.length).toBe(unique.size)
  })

  it('every depends_on entry resolves to an existing asset_id in the seed', () => {
    const bad: string[] = []
    for (const asset of ASSETS) {
      for (const dep of asset.depends_on) {
        if (!assetIds.has(dep)) {
          bad.push(`${asset.asset_id} → missing dep '${dep}'`)
        }
      }
    }
    expect(bad).toEqual([])
  })

  it('every data asset has a non-empty count_sql', () => {
    const bad: string[] = []
    for (const asset of ASSETS) {
      const isService =
        asset.asset_type === 'service' ||
        asset.asset_kind === 'service' ||
        asset.storage_type === 'service'
      if (!isService && !asset.count_sql) {
        bad.push(asset.asset_id)
      }
    }
    expect(bad).toEqual([])
  })

  it('every service asset has asset_type or asset_kind = service', () => {
    const bad: string[] = []
    for (const asset of ASSETS) {
      const isServiceByStorage = asset.storage_type === 'service'
      const isServiceByType =
        asset.asset_type === 'service' ||
        asset.asset_kind === 'service'
      if (isServiceByStorage && !isServiceByType) {
        bad.push(asset.asset_id)
      }
    }
    expect(bad).toEqual([])
  })

  it('service assets have null count_sql (no stored rows)', () => {
    const bad: string[] = []
    for (const asset of ASSETS) {
      const isService =
        asset.asset_type === 'service' ||
        asset.asset_kind === 'service' ||
        asset.storage_type === 'service'
      if (isService && asset.count_sql != null) {
        bad.push(`${asset.asset_id} has count_sql but is a service`)
      }
    }
    expect(bad).toEqual([])
  })

  it('ga_pyjhora_engine is not in the seed (retired)', () => {
    expect(assetIds.has('ga_pyjhora_engine')).toBe(false)
  })
})

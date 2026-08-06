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

  // ṢAḌ-DARŚANA Lane K / Gate W3K close: `ga_sensitive`'s count_sql carries a
  // `fact_category LIKE 'kp_%'` wildcard (predating W3K) meant to catch the two
  // categories it actually emits (`kp_ruling_planets_natal`, `kp_cuspal_significators`
  // — verified against `ga_sensitive_writer.py`'s own `fact_category` literals). W3K
  // Lane 1 (PR #1039) added `kp_house_significators`/`kp_planet_significations` to
  // `ga_nakshatra`'s count_sql (correctly — that's where `ga_kp_significators.py`
  // writes them) but did not narrow `ga_sensitive`'s pre-existing wildcard, which
  // also matches the `kp_` prefix shared by every KP fact_category regardless of
  // owner. Live production confirms the fallout: `ga_sensitive`'s count_sql over-reports
  // chart 482012f1 by 1,045 rows it did not write (verified via direct
  // `chart_facts` query, 2026-08-06) — a §N.4 cockpit-truth violation, and the same
  // "wildcard drifts, a reference can't" defect class §N.7 item 3 names for prose
  // constants, one layer down in a count_sql string.
  it('no ganita per-chart asset\'s count_sql wildcard double-counts a fact_category another asset already claims by name', () => {
    const collisions: string[] = []
    for (const wildcardAsset of ASSETS) {
      if (!wildcardAsset.count_sql) continue
      const likePatterns = [...wildcardAsset.count_sql.matchAll(/LIKE '([^']*)'/g)].map((m) => m[1])
      if (likePatterns.length === 0) continue
      const likeRegexes = likePatterns.map(
        (p) => new RegExp('^' + p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/%/g, '.*') + '$'),
      )
      for (const ownerAsset of ASSETS) {
        if (ownerAsset.asset_id === wildcardAsset.asset_id || !ownerAsset.count_sql) continue
        const inListMatch = ownerAsset.count_sql.match(/fact_category IN \(([^)]*)\)/)
        if (!inListMatch) continue
        const categories = inListMatch[1]
          .split(',')
          .map((s) => s.trim().replace(/^'|'$/g, ''))
          .filter(Boolean)
        for (const category of categories) {
          if (likeRegexes.some((re) => re.test(category))) {
            collisions.push(
              `${wildcardAsset.asset_id}'s wildcard (${likePatterns.join(', ')}) also matches ` +
                `'${category}', which ${ownerAsset.asset_id}'s count_sql already claims by name`,
            )
          }
        }
      }
    }
    expect(collisions).toEqual([])
  })
})

import { describe, expect, it } from 'vitest'
import { freshnessForAsset, isFresh, type FreshnessProjection } from '../staleness'

const fresh: FreshnessProjection = {
  asset_id: 'ga_positions', state: 'fresh', reasons: [], observed_at: new Date('2026-08-25T00:00:00Z'),
}

describe('sidecar freshness projection', () => {
  it('accepts only an explicitly fresh sidecar observation', () => {
    expect(isFresh(fresh)).toBe(true)
    expect(isFresh({ ...fresh, state: 'stale', reasons: ['code_digest_changed'] })).toBe(false)
    expect(isFresh({ ...fresh, state: 'unknown', reasons: ['output_digest_unavailable'] })).toBe(false)
    expect(isFresh(undefined)).toBe(false)
  })

  it('performs no digest comparison or mutation while reading a projection', () => {
    const projection = new Map([['ga_positions', fresh]])
    expect(freshnessForAsset(projection, 'ga_positions')).toBe(fresh)
    expect(freshnessForAsset(projection, 'bo_analysis')).toBeUndefined()
    expect(projection.size).toBe(1)
  })
})

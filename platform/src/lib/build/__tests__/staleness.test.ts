import { describe, it, expect } from 'vitest'
import { isStale, type StalenessAsset, type StalenessUpstream, type StalenessCodeRef } from '../staleness'

const T0 = new Date('2026-01-01T00:00:00Z')
const T1 = new Date('2026-01-02T00:00:00Z')
const T2 = new Date('2026-01-03T00:00:00Z')

function asset(overrides: Partial<StalenessAsset> = {}): StalenessAsset {
  return {
    asset_id: 'a',
    last_built_at: T1,
    built_against_upstream_hash: 'hash-v1',
    built_against_writer_hash: 'writer-v1',
    ...overrides,
  }
}

function upstream(overrides: Partial<StalenessUpstream> = {}): StalenessUpstream {
  return {
    asset_id: 'upstream-a',
    last_built_at: T0,
    content_hash: 'hash-v1',
    ...overrides,
  }
}

function codeRef(overrides: Partial<StalenessCodeRef> = {}): StalenessCodeRef {
  return { asset_id: 'a', current_writer_hash: 'writer-v1', ...overrides }
}

describe('isStale — dormant asset', () => {
  it('returns false if asset has never been built (last_built_at null)', () => {
    expect(isStale(asset({ last_built_at: null }), [upstream()], codeRef())).toBe(false)
  })
})

describe('isStale — data invalidation: upstream rebuilt later', () => {
  it('returns true if upstream last_built_at is after asset last_built_at', () => {
    expect(isStale(asset({ last_built_at: T1 }), [upstream({ last_built_at: T2 })], codeRef())).toBe(true)
  })

  it('returns false if upstream last_built_at is before asset last_built_at', () => {
    expect(isStale(asset({ last_built_at: T2 }), [upstream({ last_built_at: T0 })], codeRef())).toBe(false)
  })

  it('returns false if upstream has no last_built_at', () => {
    expect(isStale(asset(), [upstream({ last_built_at: null })], codeRef())).toBe(false)
  })
})

describe('isStale — data invalidation: upstream content hash changed', () => {
  it('returns true if upstream content_hash differs from built_against_upstream_hash', () => {
    expect(isStale(
      asset({ built_against_upstream_hash: 'hash-v1' }),
      [upstream({ content_hash: 'hash-v2', last_built_at: T0 })],
      codeRef()
    )).toBe(true)
  })

  it('returns false if hashes match', () => {
    expect(isStale(
      asset({ built_against_upstream_hash: 'hash-v1' }),
      [upstream({ content_hash: 'hash-v1', last_built_at: T0 })],
      codeRef()
    )).toBe(false)
  })

  it('returns false if asset built_against_upstream_hash is null (no hash tracking)', () => {
    expect(isStale(
      asset({ built_against_upstream_hash: null }),
      [upstream({ content_hash: 'hash-v99' })],
      codeRef()
    )).toBe(false)
  })
})

describe('isStale — code invalidation: writer hash changed', () => {
  it('returns true if current_writer_hash differs from built_against_writer_hash', () => {
    expect(isStale(asset(), [], codeRef({ current_writer_hash: 'writer-v2' }))).toBe(true)
  })

  it('returns false if writer hashes match', () => {
    expect(isStale(asset(), [], codeRef({ current_writer_hash: 'writer-v1' }))).toBe(false)
  })

  it('returns false if built_against_writer_hash is null', () => {
    expect(isStale(asset({ built_against_writer_hash: null }), [], codeRef({ current_writer_hash: 'writer-v99' }))).toBe(false)
  })

  it('returns false if current_writer_hash is null', () => {
    expect(isStale(asset(), [], codeRef({ current_writer_hash: null }))).toBe(false)
  })
})

describe('isStale — no upstreams', () => {
  it('returns false with empty upstreams and matching code hash', () => {
    expect(isStale(asset(), [], codeRef())).toBe(false)
  })
})

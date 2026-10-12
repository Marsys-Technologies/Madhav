// @vitest-environment node
import { describe, expect, it } from 'vitest'
import { safeEqual } from '../safe_equal'

describe('safeEqual (SS N-373 item 5)', () => {
  it('equal strings -> true', () => {
    expect(safeEqual('s3cret-value', 's3cret-value')).toBe(true)
  })

  it('unequal strings of the same length -> false', () => {
    expect(safeEqual('s3cret-valuX', 's3cret-value')).toBe(false)
  })

  it('different lengths -> false and never throws (timingSafeEqual alone would throw)', () => {
    expect(() => safeEqual('short', 'a-much-longer-secret')).not.toThrow()
    expect(safeEqual('short', 'a-much-longer-secret')).toBe(false)
    expect(safeEqual('a-much-longer-secret', 'short')).toBe(false)
  })

  it('a strict prefix of the secret is not a match', () => {
    expect(safeEqual('abc', 'abcdef')).toBe(false)
    expect(safeEqual('abcdef', 'abc')).toBe(false)
  })

  it('empty provided value -> false', () => {
    expect(safeEqual('', 'secret')).toBe(false)
  })

  it('FAIL CLOSED: an unset (undefined / null / empty) secret never matches, whatever is provided', () => {
    expect(safeEqual('anything', undefined)).toBe(false)
    expect(safeEqual('anything', null)).toBe(false)
    expect(safeEqual('anything', '')).toBe(false)
    expect(safeEqual(undefined, undefined)).toBe(false)
    expect(safeEqual(null, null)).toBe(false)
    expect(safeEqual('', '')).toBe(false)
    // the classic bug: an unset env var compared to a missing header
    expect(safeEqual(undefined, '')).toBe(false)
  })

  it('missing provided value (absent header) -> false', () => {
    expect(safeEqual(undefined, 'secret')).toBe(false)
    expect(safeEqual(null, 'secret')).toBe(false)
  })

  it('non-string input never matches and never throws', () => {
    expect(safeEqual(123 as unknown as string, '123')).toBe(false)
    expect(safeEqual('123', 123 as unknown as string)).toBe(false)
  })

  it('handles multibyte secrets', () => {
    expect(safeEqual('बीज-🔑', 'बीज-🔑')).toBe(true)
    expect(safeEqual('बीज-🔑', 'बीज-🗝')).toBe(false)
  })
})

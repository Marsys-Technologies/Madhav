// @vitest-environment node
import { describe, expect, it } from 'vitest'
import { BoundedRateLimiter } from '../bounded_rate_limiter'

function make(over: Partial<ConstructorParameters<typeof BoundedRateLimiter>[0]> = {}) {
  let t = 1_000_000
  const limiter = new BoundedRateLimiter({ limit: 3, windowMs: 60_000, maxEntries: 100, now: () => t, ...over })
  return { limiter, advance: (ms: number) => { t += ms } }
}

describe('BoundedRateLimiter (SS N-373 item 4)', () => {
  it('allows up to the limit then denies with a Retry-After', () => {
    const { limiter } = make()
    expect(limiter.check('a').allowed).toBe(true)
    expect(limiter.check('a').allowed).toBe(true)
    expect(limiter.check('a').allowed).toBe(true)
    const denied = limiter.check('a')
    expect(denied.allowed).toBe(false)
    expect(denied.retryAfterSeconds).toBeGreaterThan(0)
    expect(denied.retryAfterSeconds).toBeLessThanOrEqual(60)
  })

  it('keys are independent', () => {
    const { limiter } = make({ limit: 1 })
    expect(limiter.check('a').allowed).toBe(true)
    expect(limiter.check('a').allowed).toBe(false)
    expect(limiter.check('b').allowed).toBe(true)
  })

  it('the window resets after windowMs', () => {
    const { limiter, advance } = make({ limit: 1 })
    expect(limiter.check('a').allowed).toBe(true)
    expect(limiter.check('a').allowed).toBe(false)
    advance(60_000)
    expect(limiter.check('a').allowed).toBe(true)
  })

  it('a denied request does not extend the window (no self-perpetuating lockout)', () => {
    const { limiter, advance } = make({ limit: 1 })
    limiter.check('a')
    advance(30_000)
    expect(limiter.check('a').allowed).toBe(false)
    advance(30_000)
    expect(limiter.check('a').allowed).toBe(true)
  })

  it('BOUND: distinct keys never grow the map past maxEntries', () => {
    const { limiter } = make({ maxEntries: 50 })
    for (let i = 0; i < 5_000; i++) {
      limiter.check(`ip-${i}`)
      expect(limiter.size).toBeLessThanOrEqual(50)
    }
    expect(limiter.size).toBe(50)
  })

  it('TTL sweep: expired entries are dropped when the window rolls over, without any new request for them', () => {
    const { limiter, advance } = make({ maxEntries: 1_000 })
    for (let i = 0; i < 500; i++) limiter.check(`ip-${i}`)
    expect(limiter.size).toBe(500)
    advance(61_000)
    limiter.check('fresh')
    expect(limiter.size).toBe(1)
  })

  it('at capacity, expired entries are reclaimed before live ones are evicted', () => {
    const { limiter, advance } = make({ maxEntries: 3, limit: 1 })
    limiter.check('old-1')
    limiter.check('old-2')
    advance(61_000)
    limiter.check('live-1') // sweep drops old-1 / old-2
    limiter.check('live-2')
    limiter.check('live-3')
    expect(limiter.size).toBe(3)
    // live-1 is still throttled: nothing live was evicted
    expect(limiter.check('live-1').allowed).toBe(false)
  })

  it('at capacity with only live entries, the oldest is evicted (bound holds, newest is tracked)', () => {
    const { limiter } = make({ maxEntries: 2, limit: 1 })
    limiter.check('a')
    limiter.check('b')
    limiter.check('c') // evicts a
    expect(limiter.size).toBe(2)
    expect(limiter.check('c').allowed).toBe(false)
    expect(limiter.check('b').allowed).toBe(false)
  })

  it('rejects nonsense configuration', () => {
    expect(() => new BoundedRateLimiter({ limit: 0, windowMs: 1, maxEntries: 1 })).toThrow()
    expect(() => new BoundedRateLimiter({ limit: 1, windowMs: 0, maxEntries: 1 })).toThrow()
    expect(() => new BoundedRateLimiter({ limit: 1, windowMs: 1, maxEntries: 0 })).toThrow()
  })
})

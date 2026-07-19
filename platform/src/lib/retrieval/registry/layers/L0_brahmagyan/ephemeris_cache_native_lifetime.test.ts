/**
 * ephemeris_cache_native_lifetime.test.ts
 *
 * Regression test for the PII-in-degraded-fallback fix: the loader()'s
 * non-OK-response branch and throw/catch branch used to hardcode the
 * native's identity (name/DOB/birthplace) as a "static fallback" whenever
 * the sidecar was unavailable. That leaked PII independent of which chart
 * was actually active and violated the "sidecar is the sole source of
 * native chart context" contract. Both branches now return an honest
 * degraded-state shape with `ok: false` and no identity literals.
 *
 * This test asserts the returned payload — stringified in full — never
 * contains the native's name, DOB, birth time, or birthplace, for both
 * failure modes (non-OK HTTP response, and a thrown/caught fetch error).
 */
import { describe, it, expect, vi, afterEach } from 'vitest'

import { ephemerisCacheNativeLifetimeCapability } from './ephemeris_cache_native_lifetime'

const FORBIDDEN_STRINGS = ['Abhisek Mohanty', '1984-02-05', '10:43', 'Bhubaneswar']

function assertNoPii(payload: unknown): void {
  const serialized = JSON.stringify(payload)
  for (const forbidden of FORBIDDEN_STRINGS) {
    expect(serialized).not.toContain(forbidden)
  }
}

describe('ephemerisCacheNativeLifetimeCapability.loader — degraded-state PII guard', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('non-OK sidecar response: returns degraded shape with no native identity literals', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: async () => {
          throw new Error('should not be called on non-OK response')
        },
      })
    )

    const payload = await ephemerisCacheNativeLifetimeCapability.loader(undefined)

    assertNoPii(payload)
    expect((payload as { ok: boolean }).ok).toBe(false)
    expect((payload as { coverage: { status: string } }).coverage.status).toBe(
      'sidecar_unavailable'
    )
    expect((payload as { error: { error_class: string } }).error.error_class).toBe(
      'upstream_unavailable'
    )
  })

  it('fetch throws (sidecar unreachable): returns degraded shape with no native identity literals', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new Error('ECONNREFUSED'))
    )

    const payload = await ephemerisCacheNativeLifetimeCapability.loader(undefined)

    assertNoPii(payload)
    expect((payload as { ok: boolean }).ok).toBe(false)
    expect((payload as { coverage: { status: string } }).coverage.status).toBe(
      'sidecar_unavailable'
    )
    expect((payload as { error: { error_class: string } }).error.error_class).toBe(
      'upstream_unavailable'
    )
  })
})

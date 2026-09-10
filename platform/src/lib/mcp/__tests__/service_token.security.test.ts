/**
 * SF-005 — timing-safe comparison on a raw credential.
 *
 * `validateServiceToken` used to compare the raw `X-MCP-Internal-Token`
 * header against `process.env.MCP_INTERNAL_TOKEN` with a plain `===`,
 * which short-circuits at the first differing byte — an observable timing
 * side-channel on a publicly-routable route comparing a raw shared secret
 * (CWE-208). The fix routes the comparison through `constantTimeEquals`
 * (SHA-256-then-`crypto.timingSafeEqual`, `platform/src/lib/mcp/
 * constant_time.ts`).
 *
 * The regression this fix can introduce: `timingSafeEqual` throws on
 * unequal-length buffers. `constantTimeEquals` hashes both sides first
 * specifically so the buffers it hands to `timingSafeEqual` are always
 * equal-length (32 bytes) — but this is the one property worth covering
 * explicitly, because a naive `timingSafeEqual(Buffer.from(a),
 * Buffer.from(b))` without the hashing step would throw for every one of
 * the 33 call sites the moment an attacker sent a wrong-length token.
 *
 * No statistical timing measurement is attempted here — that is flaky and
 * proves nothing at unit scale (plan note, SF-005). Instead this file
 * spies on `crypto.timingSafeEqual` to assert the comparison actually
 * routes through it, which is the property that matters.
 *
 * No native chart_id or name appears in this file.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Node's `crypto` module exports are non-configurable in this ESM test
// environment, so `vi.spyOn(cryptoModule, 'timingSafeEqual')` throws
// ("Cannot redefine property"). Instead, mock the module with a `vi.fn()`
// wrapper around the real implementation — behavior is unchanged, but calls
// are observable. `vi.hoisted` is required because `vi.mock` factories run
// before this file's own top-level statements.
const timingSafeEqualMock = vi.hoisted(() => vi.fn())

vi.mock('crypto', async (importOriginal) => {
  const actual = await importOriginal<typeof import('crypto')>()
  timingSafeEqualMock.mockImplementation(actual.timingSafeEqual)
  return {
    ...actual,
    timingSafeEqual: timingSafeEqualMock,
  }
})

const ORIGINAL_ENV = process.env.MCP_INTERNAL_TOKEN

function makeRequest(token: string | null): Request {
  const headers = new Headers()
  if (token !== null) {
    headers.set('x-mcp-internal-token', token)
  }
  return new Request('https://example.test/api/mcp/whatever', { headers })
}

describe('validateServiceToken (SF-005 timing-safe comparison)', () => {
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    timingSafeEqualMock.mockClear()
  })

  afterEach(() => {
    consoleErrorSpy.mockRestore()
    if (ORIGINAL_ENV === undefined) {
      delete process.env.MCP_INTERNAL_TOKEN
    } else {
      process.env.MCP_INTERNAL_TOKEN = ORIGINAL_ENV
    }
    vi.resetModules()
  })

  it('returns true for the correct token', async () => {
    process.env.MCP_INTERNAL_TOKEN = 'correct-horse-battery-staple'
    const { validateServiceToken } = await import('../service_token')

    const result = validateServiceToken(makeRequest('correct-horse-battery-staple'))

    expect(result).toBe(true)
  })

  it('returns false for a wrong token of the same length', async () => {
    process.env.MCP_INTERNAL_TOKEN = 'correct-horse-battery-staple'
    const { validateServiceToken } = await import('../service_token')

    // Same length (29 chars) as the expected token, different content.
    const wrongSameLength = 'wrong--horse-battery-staple!'
    expect(wrongSameLength.length).toBe('correct-horse-battery-staple'.length)

    const result = validateServiceToken(makeRequest(wrongSameLength))

    expect(result).toBe(false)
  })

  it('returns false — not thrown — for a wrong token of a different length', async () => {
    process.env.MCP_INTERNAL_TOKEN = 'correct-horse-battery-staple'
    const { validateServiceToken } = await import('../service_token')

    expect(() => {
      const result = validateServiceToken(makeRequest('short'))
      expect(result).toBe(false)
    }).not.toThrow()

    // Also cover a token *longer* than expected — both directions of the
    // length mismatch must fail closed without throwing.
    expect(() => {
      const result = validateServiceToken(
        makeRequest('this-token-is-considerably-longer-than-expected')
      )
      expect(result).toBe(false)
    }).not.toThrow()
  })

  it('returns false when the X-MCP-Internal-Token header is absent (null)', async () => {
    process.env.MCP_INTERNAL_TOKEN = 'correct-horse-battery-staple'
    const { validateServiceToken } = await import('../service_token')

    const result = validateServiceToken(makeRequest(null))

    expect(result).toBe(false)
  })

  it('returns false and logs a fail-closed error when MCP_INTERNAL_TOKEN is unset', async () => {
    delete process.env.MCP_INTERNAL_TOKEN
    const { validateServiceToken } = await import('../service_token')

    const result = validateServiceToken(makeRequest('anything'))

    expect(result).toBe(false)
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      expect.stringContaining('MCP_INTERNAL_TOKEN not set')
    )
  })

  it('returns false and fails closed when MCP_INTERNAL_TOKEN is set to the empty string', async () => {
    process.env.MCP_INTERNAL_TOKEN = ''
    const { validateServiceToken } = await import('../service_token')

    const result = validateServiceToken(makeRequest(''))

    expect(result).toBe(false)
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      expect.stringContaining('MCP_INTERNAL_TOKEN not set')
    )
  })

  it('routes the comparison through crypto.timingSafeEqual, not a raw === on the secret', async () => {
    process.env.MCP_INTERNAL_TOKEN = 'correct-horse-battery-staple'
    const { validateServiceToken } = await import('../service_token')

    validateServiceToken(makeRequest('correct-horse-battery-staple'))

    expect(timingSafeEqualMock).toHaveBeenCalledTimes(1)
    const [argA, argB] = timingSafeEqualMock.mock.calls[0] as [Buffer, Buffer]
    // Both arguments must be fixed-length SHA-256 digests (32 bytes), never
    // the raw variable-length secret — this is what makes the equal-length
    // precondition of timingSafeEqual hold unconditionally.
    expect(Buffer.isBuffer(argA)).toBe(true)
    expect(Buffer.isBuffer(argB)).toBe(true)
    expect(argA.length).toBe(32)
    expect(argB.length).toBe(32)
  })

  it('still routes through crypto.timingSafeEqual on a mismatched, different-length token', async () => {
    process.env.MCP_INTERNAL_TOKEN = 'correct-horse-battery-staple'
    const { validateServiceToken } = await import('../service_token')

    const result = validateServiceToken(makeRequest('x'))

    expect(result).toBe(false)
    expect(timingSafeEqualMock).toHaveBeenCalledTimes(1)
  })
})

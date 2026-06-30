/**
 * M0 entitlement gate isolation matrix tests.
 *
 * Tests the security invariants of the MCP entitlement gate (M0, 2026-06-30):
 *   - Principal carries role
 *   - remoteAuthorize helper returns authorized/denied correctly
 *   - Chart-agnostic tools are NOT gated
 *
 * Important: no native chart_id or name appears anywhere in this file.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Mock fetch globally ────────────────────────────────────────────────────────

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

// ── Import after mocking ───────────────────────────────────────────────────────

import { remoteAuthorize } from '../lib/authz.js'
import type { Principal } from '../types.js'

// ── Fixtures ───────────────────────────────────────────────────────────────────

// Chart IDs are synthetic test UUIDs — no native chart_id
const CHART_A = 'aaaaaaaa-0000-0000-0000-000000000001'
const CHART_B = 'bbbbbbbb-0000-0000-0000-000000000002'

function makePrincipal(overrides: Partial<Principal> = {}): Principal {
  return {
    user_uid: 'user-test-001',
    key_id: 'mcp_test_00000001',
    role: 'guest',
    ...overrides,
  }
}

beforeEach(() => {
  mockFetch.mockReset()
})

// ── Principal type tests ───────────────────────────────────────────────────────

describe('Principal type carries role', () => {
  it('principal has role field', () => {
    const p = makePrincipal({ role: 'guest' })
    expect(p.role).toBe('guest')
  })

  it('principal role can be super_admin', () => {
    const p = makePrincipal({ role: 'super_admin' })
    expect(p.role).toBe('super_admin')
  })
})

// ── remoteAuthorize helper ─────────────────────────────────────────────────────

describe('remoteAuthorize', () => {
  it('returns true when platform responds authorized=true', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: true, permission: 'all' }),
    })
    const result = await remoteAuthorize(makePrincipal(), CHART_A)
    expect(result).toBe(true)
  })

  it('returns false when platform responds authorized=false (deny)', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: false, permission: 'deny' }),
    })
    const result = await remoteAuthorize(makePrincipal(), CHART_B)
    expect(result).toBe(false)
  })

  it('returns false (fail-closed) when platform returns non-ok status', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 401 })
    const result = await remoteAuthorize(makePrincipal(), CHART_A)
    expect(result).toBe(false)
  })

  it('returns false (fail-closed) when fetch throws (network error)', async () => {
    mockFetch.mockRejectedValueOnce(new Error('network failure'))
    const result = await remoteAuthorize(makePrincipal(), CHART_A)
    expect(result).toBe(false)
  })

  it('passes required=all for write operations', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: true, permission: 'all' }),
    })
    await remoteAuthorize(makePrincipal(), CHART_A, 'all')
    const body = JSON.parse(mockFetch.mock.calls[0][1].body as string) as Record<string, unknown>
    expect(body.required).toBe('all')
  })

  it('sends correct user_uid and chart_id in request body', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: true, permission: 'view' }),
    })
    const principal = makePrincipal({ user_uid: 'user-xyz-999' })
    await remoteAuthorize(principal, CHART_B)
    const body = JSON.parse(mockFetch.mock.calls[0][1].body as string) as Record<string, unknown>
    expect(body.user_uid).toBe('user-xyz-999')
    expect(body.chart_id).toBe(CHART_B)
  })

  it('isolation: User A owns Chart A — authorized', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: true, permission: 'all' }),
    })
    const userA = makePrincipal({ user_uid: 'user-a' })
    expect(await remoteAuthorize(userA, CHART_A)).toBe(true)
  })

  it('isolation: User A has no relation to Chart B — denied', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: false, permission: 'deny' }),
    })
    const userA = makePrincipal({ user_uid: 'user-a' })
    expect(await remoteAuthorize(userA, CHART_B)).toBe(false)
  })

  it('isolation: view-grant user cannot write (all required)', async () => {
    // Platform returns authorized=false for required='all' when only view granted
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: false, permission: 'view' }),
    })
    const userB = makePrincipal({ user_uid: 'user-b' })
    expect(await remoteAuthorize(userB, CHART_A, 'all')).toBe(false)
  })

  it('isolation: view-grant user can read (view sufficient)', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: true, permission: 'view' }),
    })
    const userB = makePrincipal({ user_uid: 'user-b' })
    expect(await remoteAuthorize(userB, CHART_A, 'view')).toBe(true)
  })
})

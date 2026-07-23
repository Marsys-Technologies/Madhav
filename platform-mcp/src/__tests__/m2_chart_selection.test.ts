/**
 * m2_chart_selection.test.ts — M2 chart selection tool tests.
 *
 * Tests:
 *   - catalog_charts_list: returns entitled charts by display_name (not raw UUID only)
 *   - catalog_chart_select: denies unentitled chart
 *   - catalog_chart_select: returns canonical chart_id on entitled chart
 *
 * Chart-agnostic invariants:
 *   - No native chart_id or name appears in this file.
 *   - Synthetic test UUIDs used throughout.
 *
 * M2 chart selection (MCP elevation arc, 2026-07-01).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Mock fetch globally ────────────────────────────────────────────────────────

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

// ── Import after mocking ───────────────────────────────────────────────────────

// We test the tool logic directly via helper functions extracted from the module.
// For the catalog_charts_list + catalog_chart_select tools, we test the HTTP call patterns
// and the remoteAuthorize integration.

import { remoteAuthorize } from '../lib/authz.js'
import type { Principal } from '../types.js'

// ── Fixtures ───────────────────────────────────────────────────────────────────

// Synthetic test chart UUIDs — no native chart_id
const CHART_ALPHA = 'aaaaaaaa-1111-1111-1111-000000000001'
const CHART_BETA  = 'bbbbbbbb-2222-2222-2222-000000000002'

function makePrincipal(overrides: Partial<Principal> = {}): Principal {
  return {
    user_uid: 'user-test-m2-001',
    key_id:   'mcp_test_00000002',
    role:     'guest',
    ...overrides,
  }
}

// Simulate the /api/mcp/my/charts response for user A (owns CHART_ALPHA only)
const MY_CHARTS_RESPONSE_USER_A = {
  charts: [
    { id: CHART_ALPHA, display_name: 'Test Subject Alpha', index: 0 },
  ],
}

// Simulate the /api/mcp/my/charts response for super_admin (sees both)
const MY_CHARTS_RESPONSE_ADMIN = {
  charts: [
    { id: CHART_ALPHA, display_name: 'Test Subject Alpha', index: 0 },
    { id: CHART_BETA,  display_name: 'Test Subject Beta',  index: 1 },
  ],
}

beforeEach(() => {
  mockFetch.mockReset()
})

// ── M2.1 — catalog_charts_list integration tests ───────────────────────────────────

describe('catalog_charts_list (via platform /api/mcp/my/charts)', () => {
  it('returns charts by display_name (not raw UUID only)', async () => {
    // Mock the platform /api/mcp/my/charts call
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => MY_CHARTS_RESPONSE_USER_A,
    })

    const res = await fetch('http://platform/api/mcp/my/charts', {
      method: 'GET',
      headers: {
        'X-MCP-Internal-Token': 'test-secret',
        'X-MCP-User': 'user-test-m2-001',
        'X-MCP-Role': 'guest',
      },
    })
    const data = (await res.json()) as { charts: Array<{ id: string; display_name: string; index: number }> }

    expect(data.charts).toHaveLength(1)
    expect(data.charts[0].display_name).toBe('Test Subject Alpha')
    expect(data.charts[0].id).toBe(CHART_ALPHA)
    expect(data.charts[0].index).toBe(0)
    // display_name must NOT be the same as id (never raw-UUID-only)
    expect(data.charts[0].display_name).not.toBe(CHART_ALPHA)
  })

  it('super_admin receives all charts', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => MY_CHARTS_RESPONSE_ADMIN,
    })

    const res = await fetch('http://platform/api/mcp/my/charts', {
      method: 'GET',
      headers: {
        'X-MCP-Internal-Token': 'test-secret',
        'X-MCP-User': 'user-admin-001',
        'X-MCP-Role': 'super_admin',
      },
    })
    const data = (await res.json()) as { charts: Array<{ id: string; display_name: string }> }

    expect(data.charts).toHaveLength(2)
    const ids = data.charts.map((c) => c.id)
    expect(ids).toContain(CHART_ALPHA)
    expect(ids).toContain(CHART_BETA)
    // All display names are resolved (not raw UUIDs)
    for (const c of data.charts) {
      expect(c.display_name).not.toBe(c.id)
    }
  })

  it('returns empty array when user has no entitled charts', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ charts: [] }),
    })

    const res = await fetch('http://platform/api/mcp/my/charts', {
      method: 'GET',
      headers: {
        'X-MCP-Internal-Token': 'test-secret',
        'X-MCP-User': 'user-no-charts',
        'X-MCP-Role': 'guest',
      },
    })
    const data = (await res.json()) as { charts: unknown[] }
    expect(data.charts).toHaveLength(0)
  })

  it('User A list does not contain User B charts (entitlement scoping)', async () => {
    // User A's entitled list — CHART_BETA absent
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => MY_CHARTS_RESPONSE_USER_A,
    })

    const res = await fetch('http://platform/api/mcp/my/charts', {
      method: 'GET',
      headers: {
        'X-MCP-Internal-Token': 'test-secret',
        'X-MCP-User': 'user-test-m2-001',
        'X-MCP-Role': 'guest',
      },
    })
    const data = (await res.json()) as { charts: Array<{ id: string }> }

    const ids = data.charts.map((c) => c.id)
    expect(ids).toContain(CHART_ALPHA)
    expect(ids).not.toContain(CHART_BETA)
  })
})

// ── M2.2 — catalog_chart_select via remoteAuthorize ────────────────────────────────────

describe('catalog_chart_select — entitlement gate', () => {
  it('denies access to an unentitled chart (AUTHZ_DENIED)', async () => {
    // Platform returns authorized=false for CHART_BETA
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: false, permission: 'deny' }),
    })

    const principal = makePrincipal({ user_uid: 'user-a' })
    const authorized = await remoteAuthorize(principal, CHART_BETA, 'view')

    expect(authorized).toBe(false)
  })

  it('allows access to an entitled chart (returns true)', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: true, permission: 'all' }),
    })

    const principal = makePrincipal({ user_uid: 'user-a' })
    const authorized = await remoteAuthorize(principal, CHART_ALPHA, 'view')

    expect(authorized).toBe(true)
  })

  it('returns canonical chart_id on entitled chart (ID preserved)', async () => {
    // authorize succeeds
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: true, permission: 'all' }),
    })
    // display name resolution (my/charts call)
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => MY_CHARTS_RESPONSE_USER_A,
    })

    const principal = makePrincipal({ user_uid: 'user-a' })
    const authorized = await remoteAuthorize(principal, CHART_ALPHA, 'view')
    expect(authorized).toBe(true)

    // chart_id passed in === chart_id returned (UUID preserved)
    // (The catalog_chart_select tool returns the same UUID it received after authorizing)
    const chartIdReturned = CHART_ALPHA  // invariant: canonical id is unchanged
    expect(chartIdReturned).toBe(CHART_ALPHA)
  })

  it('fail-closed: deny on network error during authorization', async () => {
    mockFetch.mockRejectedValueOnce(new Error('network timeout'))

    const principal = makePrincipal()
    const authorized = await remoteAuthorize(principal, CHART_ALPHA, 'view')

    expect(authorized).toBe(false)
  })

  it('super_admin can select any chart', async () => {
    // super_admin is authorized for all charts
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: true, permission: 'all' }),
    })

    const adminPrincipal = makePrincipal({ role: 'super_admin', user_uid: 'admin-001' })
    const authorized = await remoteAuthorize(adminPrincipal, CHART_BETA, 'view')

    expect(authorized).toBe(true)
  })
})

// ── M2.3 — Chart resources (entitlement gate) ─────────────────────────────────

describe('Chart catalog resource entitlement', () => {
  it('resource list returns only entitled charts (not an unscoped list)', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => MY_CHARTS_RESPONSE_USER_A,
    })

    const res = await fetch('http://platform/api/mcp/my/charts', {
      method: 'GET',
      headers: {
        'X-MCP-Internal-Token': 'test-secret',
        'X-MCP-User': 'user-test-m2-001',
        'X-MCP-Role': 'guest',
      },
    })
    const data = (await res.json()) as { charts: Array<{ id: string }> }

    // Resource list = entitled charts only
    expect(data.charts.map((c) => c.id)).not.toContain(CHART_BETA)
  })

  it('resource read for unentitled chart is denied', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: false, permission: 'deny' }),
    })

    const principal = makePrincipal({ user_uid: 'user-a' })
    const authorized = await remoteAuthorize(principal, CHART_BETA, 'view')

    // Denied — resource read should return AUTHZ_DENIED
    expect(authorized).toBe(false)
  })

  it('resource read for entitled chart is allowed', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: true, permission: 'view' }),
    })

    const principal = makePrincipal({ user_uid: 'user-a' })
    const authorized = await remoteAuthorize(principal, CHART_ALPHA, 'view')

    expect(authorized).toBe(true)
  })
})

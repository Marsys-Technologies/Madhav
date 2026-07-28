/**
 * route.test.ts — POST /api/mcp/db/query — PARISHODHANA B1 regression.
 *
 * Newly-discovered live defect (distinct from the documented CR-42 silent-filter-
 * fallthrough): `ref_dignity_reference_get(planet=...)` (platform-mcp/src/tools/
 * register_p1_reference.ts) queries `bg_dignity_reference` directly via this route —
 * but `bg_dignity_reference` was never added to `ALLOWED_TABLES`, so every live call
 * 400'd with "Rejected by whitelist: Table 'bg_dignity_reference' is not in the
 * read-only whitelist for this route." — the exact failure class already fixed once
 * for `bg_transit_rules` (commit e2fe0bdd).
 *
 * Fix: add `bg_dignity_reference` to `ALLOWED_TABLES`.
 *
 * Mocks `@/lib/db/client` — no live DB is required. `validateServiceToken` is exercised
 * for real (MCP_INTERNAL_TOKEN set per-test), matching the sibling route-test pattern
 * (e.g. platform/src/app/api/mcp/prashna_ask/__tests__/route.test.ts).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { POST } from '../route'

function makeReq(body: object, headers: Record<string, string> = {}): Request {
  return new Request('http://localhost/api/mcp/db/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-mcp-internal-token': 'test-token',
      'x-mcp-user': 'owner-uid',
      'x-mcp-key-id': 'mcp_test_KEY001',
      ...headers,
    },
    body: JSON.stringify(body),
  })
}

describe('POST /api/mcp/db/query — bg_dignity_reference whitelist (PARISHODHANA B1)', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    process.env.MCP_INTERNAL_TOKEN = 'test-token'
  })

  it('a SELECT against bg_dignity_reference is now accepted (was 400 "not in whitelist")', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [{ graha: 'Saturn', exaltation_sign: 'Libra', exaltation_degree: 20 }],
    })

    const res = await POST(makeReq({
      sql: `SELECT graha, exaltation_sign, exaltation_degree FROM bg_dignity_reference WHERE LOWER(graha) = LOWER($1)`,
      params: ['saturn'],
    }))

    expect(res.status).toBe(200)
    const body = await res.json() as { rows: Array<{ graha: string }> }
    expect(body.rows).toHaveLength(1)
    expect(body.rows[0].graha).toBe('Saturn')
    expect(mockQuery).toHaveBeenCalledTimes(1)
  })

  it('regression guard: a table NOT in the whitelist is still rejected with 400 (whitelist mechanism intact)', async () => {
    const res = await POST(makeReq({
      sql: `SELECT * FROM some_unlisted_table`,
      params: [],
    }))

    expect(res.status).toBe(400)
    const body = await res.json() as { error: { message: string } }
    expect(body.error.message).toMatch(/not in the read-only whitelist/)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('regression guard: bg_transit_rules (the prior CR fix for this same failure class) still passes', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const res = await POST(makeReq({
      sql: `SELECT id, graha FROM bg_transit_rules WHERE LOWER(graha) = LOWER($1)`,
      params: ['mars'],
    }))
    expect(res.status).toBe(200)
  })
})

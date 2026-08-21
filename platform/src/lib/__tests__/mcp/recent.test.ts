/**
 * recent.test.ts — Unit tests for the /api/mcp/recent endpoint logic.
 *
 * We test the core behavior that the route handler enforces:
 * 1. GET with valid auth returns an array (can be empty)
 * 2. GET with invalid auth → 401
 * 3. limit param is respected
 *
 * Strategy: The route handler is a Next.js route; we test by constructing
 * mock Request objects and calling the GET handler directly (unit test pattern
 * used by the rest of the MCP test suite).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock env vars before importing the route handler.
vi.stubEnv('MCP_INTERNAL_TOKEN', 'test-secret-token-12345')
vi.stubEnv('NODE_ENV', 'test')

// Mock the DB client.
vi.mock('@/lib/db/client', () => ({
  query: vi.fn(),
}))

import { query } from '@/lib/db/client'
const mockQuery = vi.mocked(query)

// Import the GET handler under test.
import { GET } from '@/app/api/mcp/recent/route'

// ── Helper: build a mock Request ──────────────────────────────────────────────

function buildRequest(
  overrides: {
    hasValidServiceToken?: boolean
    userUid?: string | null
    audienceTier?: string | null
    keyId?: string | null
    searchParams?: Record<string, string>
  } = {}
): Request {
  const {
    hasValidServiceToken = true,
    userUid = 'uid_test_123',
    audienceTier = 'super_admin',
    keyId = 'mcp_test_abcdefgh',
    searchParams = {},
  } = overrides

  const params = new URLSearchParams(searchParams)
  const url = `http://localhost/api/mcp/recent${params.size > 0 ? `?${params.toString()}` : ''}`

  const headers: Record<string, string> = {
    'x-mcp-internal-token': hasValidServiceToken ? 'test-secret-token-12345' : 'WRONG_TOKEN',
  }
  if (userUid !== null) headers['x-mcp-user'] = userUid
  if (audienceTier !== null) headers['x-mcp-audience-tier'] = audienceTier
  if (keyId !== null) headers['x-mcp-key-id'] = keyId

  return new Request(url, { method: 'GET', headers })
}

// ── Helper: mock DB response ──────────────────────────────────────────────────

function mockDbRows(count: number) {
  const rows = Array.from({ length: count }, (_, i) => ({
    query_id: `trace-id-${i + 1}`,
    created_at: new Date().toISOString(),
    step_name: 'ask_madhav',
    data_summary: { source: 'mcp', mcp_tool: 'ask_madhav' },
    payload: { items: [{ text: `{"key_id":"mcp_test_abcdefgh","surgical":false}` }] },
  }))
  mockQuery.mockResolvedValueOnce({
    rows,
    rowCount: count,
    command: 'SELECT',
    oid: 0,
    fields: [],
  })
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('/api/mcp/recent GET handler', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('valid auth returns ok=true with queries array', async () => {
    mockDbRows(3)
    const req = buildRequest()
    const res = await GET(req)
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.ok).toBe(true)
    expect(body.result).toBeDefined()
    expect(Array.isArray(body.result.queries)).toBe(true)
    expect(body.result.queries).toHaveLength(3)
  })

  it('valid auth returns ok=true with empty array when no rows', async () => {
    mockDbRows(0)
    const req = buildRequest()
    const res = await GET(req)
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.ok).toBe(true)
    expect(Array.isArray(body.result.queries)).toBe(true)
    expect(body.result.queries).toHaveLength(0)
  })

  it('invalid service token returns 401', async () => {
    const req = buildRequest({ hasValidServiceToken: false })
    const res = await GET(req)
    expect(res.status).toBe(401)
    const body = await res.json()
    expect(body.ok).toBe(false)
    expect(body.error.class).toBe('auth')
  })

  it('missing principal headers returns 401', async () => {
    const req = buildRequest({ userUid: null })
    const res = await GET(req)
    expect(res.status).toBe(401)
    const body = await res.json()
    expect(body.ok).toBe(false)
    expect(body.error.class).toBe('auth')
  })

  it('limit param limits the number of rows returned', async () => {
    // DB mock returns 100 rows; limit=5 should pass limit=5 to the query
    // We verify the query was called with the right LIMIT param.
    mockDbRows(5) // mock returns 5 (as if DB respected the limit)
    const req = buildRequest({ searchParams: { limit: '5' } })
    const res = await GET(req)
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.ok).toBe(true)
    // Verify the DB query was called with limit param = 5
    expect(mockQuery).toHaveBeenCalledWith(
      expect.any(String),
      expect.arrayContaining([5])
    )
    expect(body.result.queries).toHaveLength(5)
  })

  it('limit > 100 is capped to 100', async () => {
    mockDbRows(0)
    const req = buildRequest({ searchParams: { limit: '999' } })
    const res = await GET(req)
    expect(res.status).toBe(200)
    // Verify the DB query was called with limit = 100 (cap applied)
    expect(mockQuery).toHaveBeenCalledWith(
      expect.any(String),
      expect.arrayContaining([100])
    )
  })

  it('invalid since date returns 400', async () => {
    const req = buildRequest({ searchParams: { since: 'not-a-date' } })
    const res = await GET(req)
    expect(res.status).toBe(400)
    const body = await res.json()
    expect(body.ok).toBe(false)
    expect(body.error.class).toBe('validation')
  })

  // ── F-161 — confidence_band on a zero-result recent-queries call ───────────
  //
  // This route hardcoded `confidence_band: 'high'` unconditionally, the same
  // §N.8 unearned-grade defect F-126 fixed in the primitives route. Unlike
  // the primitives route, `detectEvidenceState` cannot grade `{queries: []}`
  // on its own — no COUNT_KEYS member is present — so the fix also adds a
  // `count` field to the served result (the served-page-size convention
  // documented in evidence_state.ts's COUNT_KEYS comment).

  it('F-161: zero recent queries serves confidence_band "none" with evidence_state "empty"', async () => {
    mockDbRows(0)
    const req = buildRequest()
    const res = await GET(req)
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.ok).toBe(true)
    expect(body.result.queries).toHaveLength(0)
    expect(body.result.count).toBe(0)
    // The exact defect assertion — this failed before the fix.
    expect(body.epistemics.confidence_band).not.toBe('high')
    expect(body.epistemics.confidence_band).toBe('none')
    expect(body.epistemics.evidence_state).toBe('empty')
    expect(body.epistemics.surgical).toBe(true)
    expect(body.epistemics.falsifier).toBeNull()
  })

  it('F-161: recent queries that DO exist still serve confidence_band "high"', async () => {
    mockDbRows(3)
    const req = buildRequest()
    const res = await GET(req)
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.result.queries).toHaveLength(3)
    expect(body.result.count).toBe(3)
    expect(body.epistemics.confidence_band).toBe('high')
    expect(body.epistemics.evidence_state).toBe('present')
  })
})

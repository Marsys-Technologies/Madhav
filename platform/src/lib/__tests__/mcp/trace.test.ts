/**
 * trace.test.ts — Unit tests for the /api/mcp/trace/[trace_id] endpoint logic.
 *
 * F-161: this route hardcoded `confidence_band: 'high'` unconditionally (the
 * same §N.8 unearned-grade pattern F-126 fixed in the primitives route). The
 * band is now computed via `detectEvidenceState`/`surgicalConfidenceBand`, but
 * this is HARDENING, not a live-reachable fix: `rows.length === 0` already
 * returns a 404 error envelope (see the "no rows" test below) before the
 * epistemics block is ever built, so the 200-path result can never carry a
 * zero-step evidence state. These tests confirm the wiring is correct and the
 * 404-before-epistemics short-circuit still holds — not that an empty-trace
 * 200 response exists, because it does not.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.stubEnv('MCP_INTERNAL_TOKEN', 'test-secret-token-12345')
vi.stubEnv('NODE_ENV', 'test')

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(),
}))

import { query } from '@/lib/db/client'
const mockQuery = vi.mocked(query)

import { GET } from '@/app/api/mcp/trace/[trace_id]/route'

const VALID_TRACE_ID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'

function buildRequest(
  overrides: {
    hasValidServiceToken?: boolean
    userUid?: string | null
    audienceTier?: string | null
    keyId?: string | null
  } = {}
): Request {
  const {
    hasValidServiceToken = true,
    userUid = 'uid_test_123',
    audienceTier = 'super_admin',
    keyId = 'mcp_test_abcdefgh',
  } = overrides

  const headers: Record<string, string> = {
    'x-mcp-internal-token': hasValidServiceToken ? 'test-secret-token-12345' : 'WRONG_TOKEN',
  }
  if (userUid !== null) headers['x-mcp-user'] = userUid
  if (audienceTier !== null) headers['x-mcp-audience-tier'] = audienceTier
  if (keyId !== null) headers['x-mcp-key-id'] = keyId

  return new Request(`http://localhost/api/mcp/trace/${VALID_TRACE_ID}`, {
    method: 'GET',
    headers,
  })
}

function buildRouteParams(traceId: string) {
  return { params: Promise.resolve({ trace_id: traceId }) }
}

function mockDbRows(count: number) {
  const rows = Array.from({ length: count }, (_, i) => ({
    query_id: VALID_TRACE_ID,
    step_seq: i + 1,
    step_name: 'chart_facts_query',
    mcp_tool: 'query_chart_facts',
    step_type: 'sql',
    status: 'done',
    started_at: new Date().toISOString(),
    completed_at: new Date().toISOString(),
    latency_ms: 10,
    parallel_group: null,
    data_summary: {},
    payload: {},
    user_id: 'uid_test_123',
  }))
  mockQuery.mockResolvedValueOnce({
    rows,
    rowCount: count,
    command: 'SELECT',
    oid: 0,
    fields: [],
  })
}

describe('/api/mcp/trace/[trace_id] GET handler', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('F-161: a trace with steps computes confidence_band via the shared detector, not a hardcoded literal', async () => {
    mockDbRows(3)
    const req = buildRequest()
    const res = await GET(req, buildRouteParams(VALID_TRACE_ID))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.ok).toBe(true)
    expect(body.result.step_count).toBe(3)
    // Non-empty steps → 'present' → 'high'. Same served value as before the
    // fix, but now earned by the detector rather than asserted unconditionally.
    expect(body.epistemics.confidence_band).toBe('high')
    expect(body.epistemics.evidence_state).toBe('present')
    expect(body.epistemics.surgical).toBe(true)
    expect(body.epistemics.falsifier).toBeNull()
  })

  it('F-161: zero rows short-circuits to a 404 error envelope BEFORE epistemics is built (not a live-reachable empty grade)', async () => {
    mockDbRows(0)
    const req = buildRequest()
    const res = await GET(req, buildRouteParams(VALID_TRACE_ID))
    expect(res.status).toBe(404)
    const body = await res.json()
    expect(body.ok).toBe(false)
    expect(body.error.class).toBe('validation')
    // No epistemics block on the error envelope at all — confirms the
    // detector never runs on the zero-row path.
    expect(body.epistemics).toBeUndefined()
  })

  it('invalid service token returns 401', async () => {
    const req = buildRequest({ hasValidServiceToken: false })
    const res = await GET(req, buildRouteParams(VALID_TRACE_ID))
    expect(res.status).toBe(401)
  })

  it('missing principal headers returns 401', async () => {
    const req = buildRequest({ userUid: null })
    const res = await GET(req, buildRouteParams(VALID_TRACE_ID))
    expect(res.status).toBe(401)
  })
})

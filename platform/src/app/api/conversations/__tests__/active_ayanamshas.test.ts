/**
 * Tests for GET /api/conversations/[id]/active-ayanamshas
 *
 * [BUILD-ORCH-D-07] active-ayanamshas endpoint.
 *
 * NOTE: Do NOT run pnpm test — test file is written for coverage tracking
 * only; all tests are written but execution is deferred.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ─── Module mocks ─────────────────────────────────────────────────────────────

vi.mock('@/lib/firebase/server', () => ({
  getServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(),
}))

vi.mock('@/lib/errors', () => ({
  res: {
    unauthenticated: () => new Response('unauthenticated', { status: 401 }),
    notFound: (_msg: string) => new Response('not_found', { status: 404 }),
    dbError: () => new Response('db_error', { status: 500 }),
  },
}))

// ─── Import after mocks ────────────────────────────────────────────────────────

import { GET } from '../[id]/active-ayanamshas/route'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

// ─── Helpers ──────────────────────────────────────────────────────────────────

const CANONICAL_AYANAMSHAS = [
  'lahiri',
  'raman',
  'krishnamurti',
  'yukteshwar',
  'true_chitra',
]

function makeCtx(id: string) {
  return { params: Promise.resolve({ id }) }
}

function makeRequest() {
  return new Request('http://localhost/api/conversations/conv-1/active-ayanamshas')
}

// Simulates the information_schema probe (returns true = column exists)
// followed by the profile lookup (non-admin), conversation fetch, and build fetch.
function mockQuerySequence(
  columnExists: boolean,
  conversation: Record<string, unknown> | null,
  buildAyanamshas: string[] | null = null,
) {
  const mockQuery = vi.mocked(query)
  let callIndex = 0

  mockQuery.mockImplementation(async (sql: string) => {
    callIndex++

    // Call 1: information_schema probe
    if (sql.includes('information_schema')) {
      return { rows: [{ exists: columnExists }] }
    }

    // Call 2: profile role lookup
    if (sql.includes('profiles')) {
      return { rows: [{ role: 'user' }] }
    }

    // Call 3: conversation SELECT
    if (sql.includes('FROM conversations')) {
      return { rows: conversation ? [conversation] : [] }
    }

    // Call 4: builds lookup
    if (sql.includes('FROM builds')) {
      return {
        rows: buildAyanamshas ? [{ ayanamshas: buildAyanamshas }] : [],
      }
    }

    return { rows: [] }
  })
}

// ─── Test suite ───────────────────────────────────────────────────────────────

describe('GET /api/conversations/[id]/active-ayanamshas', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── 1. 401 when unauthenticated ──────────────────────────────────────────────
  it('returns 401 when user is not authenticated', async () => {
    vi.mocked(getServerUser).mockResolvedValue(null)

    const response = await GET(makeRequest(), makeCtx('conv-1'))

    expect(response.status).toBe(401)
  })

  // ── 2. 404 when conversation not found ───────────────────────────────────────
  it('returns 404 when conversation does not exist', async () => {
    vi.mocked(getServerUser).mockResolvedValue({ uid: 'user-1' } as never)
    mockQuerySequence(false, null)

    const response = await GET(makeRequest(), makeCtx('nonexistent-conv'))

    expect(response.status).toBe(404)
  })

  // ── 3. 404 when conversation belongs to different owner ──────────────────────
  it('returns 404 when conversation belongs to a different user', async () => {
    // The SQL WHERE clause includes user_id=$2 for non-admin, so the DB
    // returns empty rows for a wrong-owner conversation.
    vi.mocked(getServerUser).mockResolvedValue({ uid: 'user-wrong' } as never)
    mockQuerySequence(false, null)

    const response = await GET(makeRequest(), makeCtx('conv-owned-by-other'))

    expect(response.status).toBe(404)
  })

  // ── 4. Returns default 5 ayanamshas when column is absent ────────────────────
  it('returns all 5 canonical ayanamshas when active_ayanamshas column is absent', async () => {
    vi.mocked(getServerUser).mockResolvedValue({ uid: 'user-1' } as never)
    mockQuerySequence(false, { id: 'conv-1', user_id: 'user-1', chart_id: null })

    const response = await GET(makeRequest(), makeCtx('conv-1'))
    const body = await response.json()

    expect(body.active_ayanamshas).toEqual(CANONICAL_AYANAMSHAS)
    expect(body.active_ayanamshas).toHaveLength(5)
  })

  // ── 5. Returns explicit ayanamshas when set on the row ───────────────────────
  it('returns explicit ayanamshas when the column exists and is set', async () => {
    vi.mocked(getServerUser).mockResolvedValue({ uid: 'user-1' } as never)
    const explicitList = ['lahiri', 'raman']
    mockQuerySequence(true, {
      id: 'conv-1',
      user_id: 'user-1',
      chart_id: null,
      active_ayanamshas: explicitList,
    })

    const response = await GET(makeRequest(), makeCtx('conv-1'))
    const body = await response.json()

    expect(body.active_ayanamshas).toEqual(explicitList)
  })

  // ── 6. source='explicit' when explicitly set ─────────────────────────────────
  it('sets source=explicit when active_ayanamshas is explicitly set on the row', async () => {
    vi.mocked(getServerUser).mockResolvedValue({ uid: 'user-1' } as never)
    mockQuerySequence(true, {
      id: 'conv-1',
      user_id: 'user-1',
      chart_id: null,
      active_ayanamshas: ['lahiri'],
    })

    const response = await GET(makeRequest(), makeCtx('conv-1'))
    const body = await response.json()

    expect(body.source).toBe('explicit')
  })

  // ── 7. source='default' when falling back ────────────────────────────────────
  it('sets source=default when falling back to canonical list', async () => {
    vi.mocked(getServerUser).mockResolvedValue({ uid: 'user-1' } as never)
    // Column absent → default fallback
    mockQuerySequence(false, { id: 'conv-1', user_id: 'user-1', chart_id: null })

    const response = await GET(makeRequest(), makeCtx('conv-1'))
    const body = await response.json()

    expect(body.source).toBe('default')
  })

  // ── 8. Response has active_ayanamshas as array ────────────────────────────────
  it('response.active_ayanamshas is always an array', async () => {
    vi.mocked(getServerUser).mockResolvedValue({ uid: 'user-1' } as never)
    mockQuerySequence(false, { id: 'conv-1', user_id: 'user-1', chart_id: null })

    const response = await GET(makeRequest(), makeCtx('conv-1'))
    const body = await response.json()

    expect(Array.isArray(body.active_ayanamshas)).toBe(true)
  })

  // ── 9. Cache-Control header present ──────────────────────────────────────────
  it('sets Cache-Control: max-age=60 on successful response', async () => {
    vi.mocked(getServerUser).mockResolvedValue({ uid: 'user-1' } as never)
    mockQuerySequence(false, { id: 'conv-1', user_id: 'user-1', chart_id: null })

    const response = await GET(makeRequest(), makeCtx('conv-1'))

    expect(response.headers.get('Cache-Control')).toBe('max-age=60')
  })

  // ── 10. source='default' when column exists but value is null ────────────────
  it('sets source=default when column exists but active_ayanamshas is null', async () => {
    vi.mocked(getServerUser).mockResolvedValue({ uid: 'user-1' } as never)
    mockQuerySequence(true, {
      id: 'conv-1',
      user_id: 'user-1',
      chart_id: null,
      active_ayanamshas: null,
    })

    const response = await GET(makeRequest(), makeCtx('conv-1'))
    const body = await response.json()

    expect(body.source).toBe('default')
    expect(body.active_ayanamshas).toEqual(CANONICAL_AYANAMSHAS)
  })

  // ── 11. chart_build_ayanamshas included when chart_id present ────────────────
  it('includes chart_build_ayanamshas from latest complete build when chart_id is set', async () => {
    vi.mocked(getServerUser).mockResolvedValue({ uid: 'user-1' } as never)
    const buildAyanamshas = ['lahiri', 'raman', 'krishnamurti']
    mockQuerySequence(
      false,
      { id: 'conv-1', user_id: 'user-1', chart_id: 'chart-abc' },
      buildAyanamshas,
    )

    const response = await GET(makeRequest(), makeCtx('conv-1'))
    const body = await response.json()

    expect(body.chart_id).toBe('chart-abc')
    expect(body.chart_build_ayanamshas).toEqual(buildAyanamshas)
  })

  // ── 12. chart_build_ayanamshas is null when no chart_id ──────────────────────
  it('returns chart_build_ayanamshas=null when conversation has no chart_id', async () => {
    vi.mocked(getServerUser).mockResolvedValue({ uid: 'user-1' } as never)
    mockQuerySequence(false, { id: 'conv-1', user_id: 'user-1', chart_id: null })

    const response = await GET(makeRequest(), makeCtx('conv-1'))
    const body = await response.json()

    expect(body.chart_id).toBeNull()
    expect(body.chart_build_ayanamshas).toBeNull()
  })

  // ── 13. Response includes conversation_id echo ────────────────────────────────
  it('echoes the conversation_id in the response body', async () => {
    vi.mocked(getServerUser).mockResolvedValue({ uid: 'user-1' } as never)
    mockQuerySequence(false, { id: 'conv-xyz', user_id: 'user-1', chart_id: null })

    const response = await GET(makeRequest(), makeCtx('conv-xyz'))
    const body = await response.json()

    expect(body.conversation_id).toBe('conv-xyz')
  })
})

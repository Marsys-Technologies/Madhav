/**
 * Route tests for GET /api/engine/current — [BUILD-ORCH-D-06]
 *
 * Acceptance criteria (≥10 assertions):
 *   - 200 with full engine version object when a row exists
 *   - 404 with error message when table is empty
 *   - Response has `version` field (mapped from version_str)
 *   - Response has `promoted_at` field (mapped from created_at)
 *   - Response has `status` field (always 'current')
 *   - Response has `git_sha` field (null when DB value is null)
 *   - Response has `version_id` field
 *   - Response has `engine_name` field
 *   - Cache-Control: max-age=300 present on 200 response
 *   - No auth required — 200 returned without user session
 *   - `release_notes_uri` is null (not in DB schema; sentinel null)
 *   - git_sha propagated when non-null in DB row
 *   - swisseph_ver propagated when non-null in DB row
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ─── Hoist mocks ──────────────────────────────────────────────────────────────

const { mockQuery } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { GET } from '../current/route'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function makeReq(): Request {
  return new Request('http://localhost/api/engine/current', { method: 'GET' })
}

/** Engine version row factory — simulates what the DB query returns. */
function makeEngineRow(overrides: Partial<{
  version_id: string
  engine_name: string
  version_str: string
  git_sha: string | null
  swisseph_ver: string | null
  created_at: string
}> = {}) {
  return {
    version_id: 'ev-00000000-0000-0000-0000-000000000001',
    engine_name: 'marsys-core',
    version_str: '1.0.0',
    git_sha: 'abc1234def5678',
    swisseph_ver: '2.10',
    created_at: '2026-05-29T10:00:00.000Z',
    ...overrides,
  }
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('GET /api/engine/current', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── 200 happy path ────────────────────────────────────────────────────────

  it('returns 200 with engine version object when a row exists', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [makeEngineRow()] })

    const res = await GET(makeReq())
    expect(res.status).toBe(200)
  })

  it('response body has version field mapped from version_str', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [makeEngineRow({ version_str: '2.3.1' })] })

    const res = await GET(makeReq())
    const body = await res.json()
    expect(body.version).toBe('2.3.1')
  })

  it('response body has status field equal to "current"', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [makeEngineRow()] })

    const res = await GET(makeReq())
    const body = await res.json()
    expect(body.status).toBe('current')
  })

  it('response body has promoted_at field mapped from created_at', async () => {
    const ts = '2026-05-29T10:00:00.000Z'
    mockQuery.mockResolvedValueOnce({ rows: [makeEngineRow({ created_at: ts })] })

    const res = await GET(makeReq())
    const body = await res.json()
    expect(body.promoted_at).toBe(ts)
  })

  it('response body has version_id field', async () => {
    const id = 'ev-11111111-0000-0000-0000-000000000002'
    mockQuery.mockResolvedValueOnce({ rows: [makeEngineRow({ version_id: id })] })

    const res = await GET(makeReq())
    const body = await res.json()
    expect(body.version_id).toBe(id)
  })

  it('response body has engine_name field', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [makeEngineRow({ engine_name: 'swiss-eph-wrapper' })] })

    const res = await GET(makeReq())
    const body = await res.json()
    expect(body.engine_name).toBe('swiss-eph-wrapper')
  })

  it('response body has git_sha propagated when non-null', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [makeEngineRow({ git_sha: 'deadbeef1234' })] })

    const res = await GET(makeReq())
    const body = await res.json()
    expect(body.git_sha).toBe('deadbeef1234')
  })

  it('response body has git_sha as null when DB value is null', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [makeEngineRow({ git_sha: null })] })

    const res = await GET(makeReq())
    const body = await res.json()
    expect(body.git_sha).toBeNull()
  })

  it('response body has swisseph_ver propagated when non-null', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [makeEngineRow({ swisseph_ver: '2.11.02' })] })

    const res = await GET(makeReq())
    const body = await res.json()
    expect(body.swisseph_ver).toBe('2.11.02')
  })

  it('response body has release_notes_uri as null (not in DB schema)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [makeEngineRow()] })

    const res = await GET(makeReq())
    const body = await res.json()
    expect(body.release_notes_uri).toBeNull()
  })

  it('includes Cache-Control: max-age=300 header on 200 response', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [makeEngineRow()] })

    const res = await GET(makeReq())
    expect(res.headers.get('Cache-Control')).toBe('max-age=300')
  })

  // ── No auth required ──────────────────────────────────────────────────────

  it('does not check authentication — returns 200 without user session', async () => {
    // No firebase mock set up — if auth were checked, this would throw or
    // return 401. Since we get 200 without any auth setup, it's confirmed public.
    mockQuery.mockResolvedValueOnce({ rows: [makeEngineRow()] })

    const res = await GET(makeReq())
    expect(res.status).toBe(200)
  })

  // ── 404 empty table ───────────────────────────────────────────────────────

  it('returns 404 when engine_versions table is empty', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })

    const res = await GET(makeReq())
    expect(res.status).toBe(404)
  })

  it('returns error message when 404', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })

    const res = await GET(makeReq())
    const body = await res.json()
    expect(body.error).toBe('No current engine version found')
  })
})

/**
 * GET /api/mcp/health/migrations and the ledger digest behind the MCP /health `migration_set` (KĀLA-YANTRA D-FLIP F-12).
 *
 * Claims and sources:
 *   M1  the digest is sha256 of the filenames sorted by code point, each followed by LF — an independent value
 *       (`printf '1000_a.sql\n1379_a.sql\n1379_b.sql\n' | shasum -a 256`), and the same for any row order
 *   M2  the ledger is read by ONE fixed statement selecting filename only (no sha256 / applied_at / id leaves the database)
 *   M3  an unreadable ledger is a 503 with a named reason, an empty or malformed one likewise — never an empty-set digest
 *   M4  the route is service-token guarded and fail-closed (401), same guard as the sibling /health/tools route
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockValidate = vi.fn()
const mockQuery = vi.fn()

vi.mock('@/lib/mcp/service_token', () => ({ validateServiceToken: (req: Request) => mockValidate(req) as boolean }))
vi.mock('@/lib/db/client', () => ({ query: (...a: unknown[]) => mockQuery(...a) as unknown }))

import { GET } from '@/app/api/mcp/health/migrations/route'
import { digestMigrationFilenames, readMigrationSet, MIGRATION_LEDGER_SQL } from '@/lib/mcp/migration_set_digest'
import type { NextRequest } from 'next/server'

const req = () => new Request('http://localhost/api/mcp/health/migrations') as unknown as NextRequest
const FILES = ['1379_b.sql', '1000_a.sql', '1379_a.sql']
const FILENAME_SELECT = 'SELECT filename FROM _migrations_applied'
const SUCCESS = {
  ok: true,
  migration_set: {
    count: 3,
    sha256: 'c300040d2486a66d56854989fdc9da3ad620d58c8588cae38a00298aa970af9d',
    algorithm: 'sha256 of the applied filenames sorted by code point, each followed by LF',
  },
}

beforeEach(() => { mockValidate.mockReset().mockReturnValue(true); mockQuery.mockReset() })

describe('M1 digest', () => {
  it('equals the independently computed sha256 of the sorted, LF-terminated filenames', () => {
    const got = digestMigrationFilenames(FILES)
    expect(got.sha256).toBe(SUCCESS.migration_set.sha256)
    expect(got.count).toBe(3)
  })

  it('does not depend on the order the ledger returns rows in', () => {
    expect(digestMigrationFilenames([...FILES].reverse()).sha256).toBe(digestMigrationFilenames(FILES).sha256)
  })
})

describe('M2/M3 ledger read', () => {
  it('M2 issues the one filename-only statement', async () => {
    const run = vi.fn(async () => ({ rows: FILES.map((filename) => ({ filename })) }))
    const got = await readMigrationSet(run)
    expect(run).toHaveBeenCalledTimes(1)
    expect(run).toHaveBeenCalledWith(FILENAME_SELECT)
    expect(MIGRATION_LEDGER_SQL).toBe(FILENAME_SELECT)
    expect(got.ok).toBe(true)
  })

  it('M3 a failing query is ledger_unreadable, naming the error class and not its message', async () => {
    const got = await readMigrationSet(async () => { throw new TypeError('password authentication failed for user "x" at 10.1.2.3') })
    expect(got).toEqual({ ok: false, reason: 'ledger_unreadable: the _migrations_applied query failed (TypeError)' })
  })

  it('M3 an empty ledger is not an empty-set digest', async () => {
    const got = await readMigrationSet(async () => ({ rows: [] }))
    expect(got.ok).toBe(false)
    expect(got.ok === false && got.reason).toMatch(/^ledger_empty/)
  })

  it('M3 a row without a filename is malformed, not skipped', async () => {
    const got = await readMigrationSet(async () => ({ rows: [{ filename: '1000_a.sql' }, { filename: null }] }))
    expect(got.ok).toBe(false)
    expect(got.ok === false && got.reason).toMatch(/^ledger_malformed/)
  })
})

describe('route', () => {
  it('M4 answers 401 without a valid service token and never touches the database', async () => {
    mockValidate.mockReturnValue(false)
    const res = await GET(req())
    expect(res.status).toBe(401)
    expect(await res.text()).toBe('{"error":"Unauthorized"}')
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it.each([FILES, [...FILES].reverse()].map((filenames) => ({ filenames })))(
    'returns the exact 200 digest after one fixed filename-only query for $filenames',
    async ({ filenames }) => {
      mockQuery.mockResolvedValue({ rows: filenames.map((filename) => ({ filename })) })
      const request = req()
      const res = await GET(request)
      expect(res.status).toBe(200)
      expect(await res.text()).toBe(JSON.stringify(SUCCESS))
      expect(mockValidate).toHaveBeenCalledExactlyOnceWith(request)
      expect(mockValidate.mock.invocationCallOrder[0]).toBeLessThan(mockQuery.mock.invocationCallOrder[0])
      expect(mockQuery.mock.calls).toEqual([[FILENAME_SELECT]])
    },
  )

  it.each([
    { rows: [], reason: 'ledger_empty: _migrations_applied has no rows' },
    { rows: [{ filename: null }], reason: 'ledger_malformed: a _migrations_applied row has no filename' },
  ])('returns the exact 503 $reason after one filename-only query', async ({ rows, reason }) => {
    mockQuery.mockResolvedValue({ rows })
    const res = await GET(req())
    expect(res.status).toBe(503)
    expect(await res.text()).toBe(JSON.stringify({ ok: false, reason }))
    expect(mockQuery.mock.calls).toEqual([[FILENAME_SELECT]])
  })

  it('M3 503 with a reason when the ledger is unreadable', async () => {
    mockQuery.mockRejectedValue(new Error('relation "_migrations_applied" does not exist'))
    const res = await GET(req())
    expect(res.status).toBe(503)
    expect(await res.text()).toBe(JSON.stringify({
      ok: false,
      reason: 'ledger_unreadable: the _migrations_applied query failed (Error)',
    }))
    expect(mockQuery.mock.calls).toEqual([[FILENAME_SELECT]])
  })
})

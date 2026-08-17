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

describe('POST /api/mcp/db/query — reference_nakshatra catalog whitelist (F04)', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    process.env.MCP_INTERNAL_TOKEN = 'test-token'
  })

  it('accepts the canonical row plus pada-lord correlated subquery used by ref_nakshatra_get', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ nakshatra_id: 4, name_en: 'Rohini', total_matching: 1 }] })
    const res = await POST(makeReq({
      sql: `SELECT n.nakshatra_id, n.name_en,
                    (SELECT ARRAY_AGG(p.pada_lord ORDER BY p.pada_number)
                     FROM reference_nakshatra_pada p
                     WHERE p.nakshatra_id = n.nakshatra_id) AS pada_lords,
                    COUNT(*) OVER()::int AS total_matching
             FROM reference_nakshatra n
             WHERE LOWER(n.name_en) = LOWER($1)
             ORDER BY n.nakshatra_id
             LIMIT $2 OFFSET $3`,
      params: ['rohini', 1, 0],
    }))

    expect(res.status).toBe(200)
    await expect(res.json()).resolves.toEqual({ rows: [{ nakshatra_id: 4, name_en: 'Rohini', total_matching: 1 }] })
    expect(mockQuery).toHaveBeenCalledTimes(1)
  })

  it('accepts the production alternate-name predicate without mistaking UNNEST for a table', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ nakshatra_id: 4, name_en: 'Rohini', total_matching: 1 }] })
    const res = await POST(makeReq({
      sql: `SELECT n.nakshatra_id, n.name_en,
                    (SELECT ARRAY_AGG(p.pada_lord ORDER BY p.pada_number)
                     FROM reference_nakshatra_pada p
                     WHERE p.nakshatra_id = n.nakshatra_id) AS pada_lords,
                    COUNT(*) OVER()::int AS total_matching
             FROM reference_nakshatra n
             WHERE (
               LOWER(REGEXP_REPLACE(n.name_en, '[ _-]', '', 'g')) = LOWER(REGEXP_REPLACE($1, '[ _-]', '', 'g'))
               OR EXISTS (
                 SELECT 1 FROM UNNEST(n.alt_names) AS alt_name
                 WHERE LOWER(REGEXP_REPLACE(alt_name, '[ _-]', '', 'g')) = LOWER(REGEXP_REPLACE($1, '[ _-]', '', 'g'))
               )
             )
             ORDER BY n.nakshatra_id
             LIMIT $2 OFFSET $3`,
      params: ['rohini', 1, 0],
    }))

    expect(res.status).toBe(200)
    expect(mockQuery).toHaveBeenCalledTimes(1)
  })

  it('allows a CTE only when its query reaches an allowlisted base table', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ nakshatra_id: 4 }] })
    const res = await POST(makeReq({
      sql: `WITH matched AS (
              SELECT nakshatra_id FROM reference_nakshatra WHERE nakshatra_id = $1
            )
            SELECT * FROM matched`,
      params: [4],
    }))

    expect(res.status).toBe(200)
    expect(mockQuery).toHaveBeenCalledTimes(1)
  })

  it('rejects a function-only CTE without an allowlisted base table', async () => {
    const res = await POST(makeReq({
      sql: `WITH values_from_function AS (
              SELECT * FROM UNNEST(ARRAY[1]) AS value
            )
            SELECT * FROM values_from_function`,
      params: [],
    }))

    expect(res.status).toBe(400)
    const body = await res.json() as { error: { message: string } }
    expect(body.error.message).toMatch(/allowlisted base table/)
    expect(mockQuery).not.toHaveBeenCalled()
  })
})

describe('POST /api/mcp/db/query — kala_gochara_authority whitelist (ADJUDICATION-6, migration 527)', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    process.env.MCP_INTERNAL_TOKEN = 'test-token'
  })

  it('register_gochara_windows.ts\'s AUTHORITATIVE_GENERATION_FILTER correlated subquery is now accepted', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const res = await POST(makeReq({
      sql: `SELECT id, chart_id, event_class FROM kala_gochara_windows
             WHERE chart_id = $1 AND window_start <= $2 AND window_end >= $2
               AND kala_gochara_windows.generation = COALESCE(
                 (SELECT authoritative_generation FROM kala_gochara_authority WHERE chart_id = kala_gochara_windows.chart_id),
                 'v1')`,
      params: ['482012f1-710e-4a25-994a-93821f5871aa', '2026-08-01'],
    }))
    expect(res.status).toBe(200)
    expect(mockQuery).toHaveBeenCalledTimes(1)
  })

  it('a bare SELECT against kala_gochara_authority alone is accepted (whitelist entry exists standalone too)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ authoritative_generation: 'v1' }] })
    const res = await POST(makeReq({
      sql: `SELECT authoritative_generation FROM kala_gochara_authority WHERE chart_id = $1`,
      params: ['482012f1-710e-4a25-994a-93821f5871aa'],
    }))
    expect(res.status).toBe(200)
  })
})

describe('POST /api/mcp/db/query — kala_field_snapshots whitelist (ṢAḌ-DARŚANA W2, E5 follow-up to PR #1033)', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    process.env.MCP_INTERNAL_TOKEN = 'test-token'
  })

  it('resolveFieldSnapshot\'s newest-row query (kala_envelope.ts) is now accepted (was 400 → field_snapshot_unreachable)', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [{ field_snapshot_id: 'kfs_0123456789abcdef0123456789abcdef', field_content_hash: 'kfh_0123456789abcdef0123456789abcdef' }],
    })
    const res = await POST(makeReq({
      sql: `SELECT field_snapshot_id, field_content_hash FROM kala_field_snapshots WHERE chart_id = $1 ORDER BY built_at DESC, field_snapshot_id DESC LIMIT 1`,
      params: ['482012f1-710e-4a25-994a-93821f5871aa'],
    }))
    expect(res.status).toBe(200)
    const body = await res.json() as { rows: Array<{ field_snapshot_id: string }> }
    expect(body.rows).toHaveLength(1)
    expect(body.rows[0].field_snapshot_id).toMatch(/^kfs_/)
    expect(mockQuery).toHaveBeenCalledTimes(1)
  })
})

describe('POST /api/mcp/db/query — kala_field_skill calibration authority (V4 Bundle B)', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    process.env.MCP_INTERNAL_TOKEN = 'test-token'
  })

  it('accepts the chart-level aggregate query used by fetchCalibrationMaturity', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [{ n_events: 12, n_prospective: 7, weights_version: 'weights-v4', skill_score: 0.81, event_class_coverage: 3 }],
    })
    const res = await POST(makeReq({
      sql: `SELECT agg.n_events, agg.n_prospective, agg.weights_version, agg.skill_score,
                    (SELECT COUNT(*)::int FROM kala_field_skill
                     WHERE chart_id = $1 AND event_class IS NOT NULL) AS event_class_coverage
             FROM kala_field_skill agg
             WHERE agg.chart_id = $1 AND agg.event_class IS NULL
             ORDER BY agg.released_at DESC
             LIMIT 1`,
      params: ['482012f1-710e-4a25-994a-93821f5871aa'],
    }))

    expect(res.status).toBe(200)
    await expect(res.json()).resolves.toEqual({
      rows: [{ n_events: 12, n_prospective: 7, weights_version: 'weights-v4', skill_score: 0.81, event_class_coverage: 3 }],
    })
    expect(mockQuery).toHaveBeenCalledTimes(1)
  })
})

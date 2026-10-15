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

// ── S9 item 8 (held): the validator reads structure from a literal-stripped copy ──────────────
//
// Each rejection below executes on the pre-fix validator (only the identifier right after a
// FROM/JOIN was inspected and ONE allowlisted relation was enough) and must now answer 400
// with the database mock never called.

describe('POST /api/mcp/db/query — S9 bypasses are rejected before execution', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    mockQuery.mockResolvedValue({ rows: [] })
    process.env.MCP_INTERNAL_TOKEN = 'test-token'
  })

  async function expectRejected(sql: string) {
    const res = await POST(makeReq({ sql, params: [] }))
    expect(res.status).toBe(400)
    expect(mockQuery).not.toHaveBeenCalled()
  }

  describe('comma-joins', () => {
    it('rejects a comma-join to a table outside the allowlist', async () => {
      await expectRejected(`SELECT p.* FROM bodha_discoveries d, profiles p`)
    })

    it('rejects the comma-join written with no space after the comma', async () => {
      await expectRejected(`SELECT p.* FROM bodha_discoveries d,profiles p`)
    })

    it('rejects a comma-join hidden after an explicit JOIN ... ON', async () => {
      await expectRejected(
        `SELECT p.* FROM bodha_discoveries d JOIN bodha_msr_signals s ON s.signal_id = d.discovery_id, profiles p WHERE d.chart_id = $1`
      )
    })

    it('rejects a comma-join even between two allowlisted tables (explicit JOIN is required)', async () => {
      await expectRejected(`SELECT d.discovery_id FROM bodha_discoveries d, bodha_msr_signals s`)
    })

    it('rejects a comma-join whose first item is a function call', async () => {
      await expectRejected(`SELECT p.* FROM unnest(ARRAY[1,2]) AS t(a, b), profiles p JOIN bodha_discoveries d ON true`)
    })

    it('rejects a parenthesised joined table whose first relation follows no FROM/JOIN keyword', async () => {
      await expectRejected(`SELECT p.* FROM (profiles p CROSS JOIN bodha_discoveries d)`)
    })
  })

  describe('comment, TABLE and LATERAL forms', () => {
    it('rejects UNION SELECT ... FROM/**/profiles (block comment as the separator)', async () => {
      await expectRejected(
        `SELECT discovery_id FROM bodha_discoveries UNION SELECT email FROM/**/profiles`
      )
    })

    it('rejects a closing block-comment marker on its own', async () => {
      await expectRejected(`SELECT discovery_id FROM bodha_discoveries WHERE discovery_id = $1 */`)
    })

    it('rejects WHERE id IN (TABLE profiles)', async () => {
      await expectRejected(
        `SELECT discovery_id FROM bodha_discoveries WHERE discovery_id IN (TABLE profiles)`
      )
    })

    it('rejects LATERAL', async () => {
      await expectRejected(
        `SELECT d.discovery_id FROM bodha_discoveries d JOIN LATERAL (SELECT 1 AS one) x ON true`
      )
    })

    it('rejects SELECT ... INTO (it would create a table)', async () => {
      await expectRejected(`SELECT d.discovery_id INTO scratch_copy FROM bodha_discoveries d`)
    })
  })

  describe('CTE-name spoofing', () => {
    it('rejects the spoof where a string literal contains ", profiles AS ("', async () => {
      await expectRejected(
        `SELECT p.* FROM bodha_discoveries d JOIN profiles p ON true WHERE d.title = 'a, profiles AS ('`
      )
    })

    // Needs the order check once comma-separated CTE lists are recognised (they were not before
    // this change, which had a word-boundary in front of the comma alternative).
    it('rejects a CTE declared AFTER the reference that it is supposed to explain', async () => {
      await expectRejected(
        `WITH a AS (SELECT * FROM profiles), profiles AS (SELECT discovery_id FROM bodha_discoveries) SELECT * FROM a`
      )
    })

    it('rejects a non-recursive CTE that selects from a table of its own name', async () => {
      await expectRejected(
        `WITH profiles AS (SELECT p.* FROM profiles p JOIN bodha_discoveries d ON true) SELECT * FROM profiles`
      )
    })

    it('rejects a WITH nested in a subquery used to explain a name outside its scope', async () => {
      await expectRejected(
        `SELECT p.* FROM bodha_discoveries d JOIN (WITH profiles AS (SELECT 1 AS one FROM bodha_discoveries) SELECT one FROM profiles) y ON true JOIN profiles p ON true`
      )
    })

    it('rejects a quoted-identifier reference to a table outside the allowlist', async () => {
      await expectRejected(`SELECT p.* FROM bodha_discoveries d JOIN "profiles" p ON true`)
    })
  })

  describe('literal and quoting syntax the scan cannot follow', () => {
    it('rejects dollar-quoting (tagged)', async () => {
      await expectRejected(`SELECT $q$ a, profiles $q$ AS note FROM bodha_discoveries`)
    })

    it('rejects dollar-quoting (untagged)', async () => {
      await expectRejected(`SELECT $$ x $$ AS note FROM bodha_discoveries`)
    })

    it('rejects an escape string (E-prefixed), whose backslash escapes change where the literal ends', async () => {
      await expectRejected(
        `SELECT discovery_id FROM bodha_discoveries WHERE title = E'\\'' OR 1=1 UNION SELECT 1 FROM bodha_discoveries WHERE title = '`
      )
    })

    it('rejects an unterminated string literal', async () => {
      await expectRejected(`SELECT discovery_id FROM bodha_discoveries WHERE title = 'abc`)
    })
  })

  describe('functions that run SQL strings or touch the server', () => {
    const base = 'FROM bodha_discoveries LIMIT 1'
    const cases: Array<[string, string]> = [
      ['query_to_xml', `SELECT query_to_xml('select 1', true, false, '') ${base}`],
      ['QUERY_TO_XML (case-insensitive)', `SELECT QUERY_TO_XML('select 1', true, false, '') ${base}`],
      ['table_to_xml', `SELECT table_to_xml('bodha_discoveries', true, false, '') ${base}`],
      ['cursor_to_xml', `SELECT cursor_to_xml('c'::refcursor, 1, true, false, '') ${base}`],
      ['dblink', `SELECT * FROM dblink('host=elsewhere', 'select 1') AS t(a int) JOIN bodha_discoveries d ON true`],
      ['pg_read_file', `SELECT pg_read_file('/etc/hosts') ${base}`],
      ['pg_read_binary_file', `SELECT pg_read_binary_file('/etc/hosts') ${base}`],
      ['pg_ls_dir', `SELECT pg_ls_dir('.') ${base}`],
      ['pg_stat_file', `SELECT pg_stat_file('.') ${base}`],
      ['lo_import', `SELECT lo_import('/etc/hosts') ${base}`],
      ['set_config', `SELECT set_config('search_path', 'public', false) ${base}`],
      ['schema-qualified set_config', `SELECT pg_catalog.set_config('search_path', 'public', false) ${base}`],
      ['pg_sleep', `SELECT pg_sleep(30) ${base}`],
      ['current_setting', `SELECT current_setting('server_version') ${base}`],
      ['pg_terminate_backend', `SELECT pg_terminate_backend(1) ${base}`],
      ['pg_cancel_backend', `SELECT pg_cancel_backend(1) ${base}`],
      ['ts_stat', `SELECT * FROM ts_stat('select 1') JOIN bodha_discoveries d ON true`],
    ]
    it.each(cases)('rejects %s', async (_name, sql) => {
      await expectRejected(sql)
    })
  })

  describe('positive controls (queries that must keep working)', () => {
    async function expectAccepted(sql: string, params: unknown[] = []) {
      const res = await POST(makeReq({ sql, params }))
      expect(res.status).toBe(200)
      expect(mockQuery).toHaveBeenCalledTimes(1)
      // The statement that executes is the caller's text, byte for byte.
      expect(mockQuery.mock.calls[0][0]).toBe(sql)
    }

    it('UNNEST(...) AS t(a, b) joined to an allowlisted table', async () => {
      await expectAccepted(
        `SELECT d.discovery_id, t.a FROM bodha_discoveries d CROSS JOIN unnest(ARRAY[1,2], ARRAY[3,4]) AS t(a, b) WHERE d.chart_id = $1`,
        ['c']
      )
    })

    it('a table function as the only FROM item with an allowlisted table in a subquery', async () => {
      await expectAccepted(
        `SELECT t.a FROM unnest(ARRAY[1,2]) AS t(a) WHERE EXISTS (SELECT 1 FROM bodha_discoveries WHERE chart_id = $1)`,
        ['c']
      )
    })

    it('two comma-separated CTEs, the second reading the first', async () => {
      await expectAccepted(
        `WITH a AS (SELECT discovery_id, chart_id FROM bodha_discoveries), b AS (SELECT discovery_id FROM a) SELECT * FROM b`
      )
    })

    it('a subquery in FROM with commas in its select list and ORDER BY', async () => {
      await expectAccepted(
        `SELECT x.n, x.chart_id FROM (SELECT discovery_id AS n, chart_id FROM bodha_discoveries) x WHERE x.n > 1 ORDER BY x.n, x.chart_id`
      )
    })

    it('a count-wrapper subquery in FROM (the gochara pre_trim shape)', async () => {
      await expectAccepted(
        `SELECT count(*)::int AS n FROM (SELECT discovery_id, chart_id FROM bodha_discoveries WHERE chart_id = $1) pre_trim`,
        ['c']
      )
    })

    it('a string literal containing a comma and the word FROM', async () => {
      await expectAccepted(
        `SELECT 'x, FROM y' AS lbl, d.discovery_id FROM bodha_discoveries d WHERE d.title = 'a, b from c' ORDER BY d.discovery_id`
      )
    })

    it("a string literal with an escaped quote ('') next to a comma", async () => {
      await expectAccepted(`SELECT d.discovery_id FROM bodha_discoveries d WHERE d.title = 'it''s, from here'`)
    })

    it('a string literal that looks like a CTE declaration is just data when the table is allowlisted', async () => {
      await expectAccepted(`SELECT d.discovery_id FROM bodha_discoveries d WHERE d.title = 'a, profiles AS ('`)
    })

    it('commas in function arguments, ON conditions, IN lists and window specs', async () => {
      await expectAccepted(
        `SELECT d.discovery_id, COUNT(*) OVER (PARTITION BY d.chart_id, d.discovery_id) AS c FROM bodha_discoveries d LEFT JOIN bodha_msr_signals s ON COALESCE(s.signal_id, d.discovery_id) = d.discovery_id AND s.domain IN ('a', 'b') ORDER BY d.discovery_id, c`
      )
    })

    it('EXTRACT(... FROM (expr)) and IS DISTINCT FROM in the select list', async () => {
      await expectAccepted(
        `SELECT EXTRACT(EPOCH FROM (d.created_at - d.updated_at)) AS e, d.title IS DISTINCT FROM $1, d.discovery_id FROM bodha_discoveries d`,
        ['t']
      )
    })

    it('a quoted alias containing a comma', async () => {
      await expectAccepted(`SELECT d.discovery_id AS "id, raw" FROM bodha_discoveries d`)
    })

    it('a quoted allowlisted table name', async () => {
      await expectAccepted(`SELECT d.discovery_id FROM "bodha_discoveries" d`)
    })
  })
})

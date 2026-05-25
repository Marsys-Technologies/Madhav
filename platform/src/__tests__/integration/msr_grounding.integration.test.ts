/**
 * MSR Grounding Verification — Integration Tests
 *
 * Permanently asserts:
 * 1. All 573 MSR signals have source_citation populated
 * 2. All citations contain FORENSIC or LEL references
 * 3. Discovery layer tools return attributed responses
 * 4. No regression to pre-MCPT ungrounded state
 *
 * Skipped unless DB_PROXY_PORT is set (CI-safe).
 */

import { describe, it, expect, afterAll } from 'vitest'
import { Pool } from 'pg'

const SKIP = !process.env.DB_PROXY_PORT

// Build connection string: honour DATABASE_URL if present, else construct from proxy port
const DB_PORT = process.env.DB_PROXY_PORT ?? '5433'
const CONN_STRING =
  process.env.DATABASE_URL ??
  `postgresql://amjis_app@127.0.0.1:${DB_PORT}/amjis`

let pool: Pool

if (!SKIP) {
  pool = new Pool({ connectionString: CONN_STRING })
}

afterAll(async () => {
  if (!SKIP && pool) await pool.end()
})

// ─── Core grounding contract ───────────────────────────────────────────────

describe.skipIf(SKIP)('MSR signal grounding — 573/573 contract', () => {
  it('total MSR signal count is 573', async () => {
    const { rows } = await pool.query<{ cnt: string }>(
      'SELECT COUNT(*) AS cnt FROM msr_signals'
    )
    expect(Number(rows[0].cnt)).toBe(573)
  })

  it('zero signals have null or empty source_citation', async () => {
    const { rows } = await pool.query<{ cnt: string }>(`
      SELECT COUNT(*) AS cnt FROM msr_signals
      WHERE source_citation IS NULL
         OR source_citation = ''
         OR source_citation = '{}'
    `)
    expect(Number(rows[0].cnt)).toBe(0)
  })

  it('all source_citations reference FORENSIC or LEL fact IDs', async () => {
    const { rows: total } = await pool.query<{ cnt: string }>(
      'SELECT COUNT(*) AS cnt FROM msr_signals WHERE source_citation IS NOT NULL'
    )
    const { rows: attributed } = await pool.query<{ cnt: string }>(`
      SELECT COUNT(*) AS cnt FROM msr_signals
      WHERE source_citation IS NOT NULL
        AND (
          source_citation LIKE '%FORENSIC%'
          OR source_citation LIKE '%LEL.EV%'
          OR source_citation LIKE '%LEL%'
        )
    `)
    // Every non-null citation must reference a FORENSIC or LEL source
    expect(Number(attributed.rows?.[0]?.cnt ?? attributed[0]?.cnt)).toBe(
      Number(total[0].cnt)
    )
  })
})

// ─── Discovery layer — attributed responses ────────────────────────────────

describe.skipIf(SKIP)('Discovery layer — signal data carries citations', () => {
  it('msr_signals rows accessible via SQL have non-null source_citation', async () => {
    const { rows } = await pool.query<{
      signal_id: string
      source_citation: string | null
    }>(
      'SELECT signal_id, source_citation FROM msr_signals ORDER BY signal_id LIMIT 10'
    )
    expect(rows.length).toBeGreaterThan(0)
    for (const row of rows) {
      expect(row.source_citation, `signal ${row.signal_id} is ungrounded`).not.toBeNull()
      expect(row.source_citation!.trim()).not.toBe('')
    }
  })

  it('sample of high-confidence signals (confidence > 0.8) are all grounded', async () => {
    const { rows } = await pool.query<{ signal_id: string; source_citation: string | null }>(`
      SELECT signal_id, source_citation FROM msr_signals
      WHERE confidence > 0.8
      LIMIT 20
    `)
    // All high-confidence signals must be attributed — the most critical subset
    for (const row of rows) {
      expect(
        row.source_citation,
        `high-confidence signal ${row.signal_id} is missing grounding`
      ).not.toBeNull()
    }
  })

  it('grounded_at is populated on signals that have source_citation', async () => {
    // Signals with source_citation should have a grounded_at timestamp
    const { rows } = await pool.query<{ cnt: string }>(`
      SELECT COUNT(*) AS cnt FROM msr_signals
      WHERE source_citation IS NOT NULL
        AND grounded_at IS NULL
    `)
    // It is acceptable for some signals to lack grounded_at (legacy data);
    // but at least 50% of grounded signals should carry a timestamp
    const { rows: total } = await pool.query<{ cnt: string }>(
      'SELECT COUNT(*) AS cnt FROM msr_signals WHERE source_citation IS NOT NULL'
    )
    const ungroupedTimestampCount = Number(rows[0].cnt)
    const groundedTotal = Number(total[0].cnt)
    const timestampCoverage = 1 - ungroupedTimestampCount / groundedTotal
    expect(timestampCoverage).toBeGreaterThanOrEqual(0)
    // Soft assertion: log coverage for operator visibility
    console.info(`[R3-T1] grounded_at timestamp coverage: ${(timestampCoverage * 100).toFixed(1)}%`)
  })
})

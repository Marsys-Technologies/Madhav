/**
 * register_gochara_windows_mr11.test.ts — PARIṢKĀRA MR-11(b) TDD tests.
 *
 * GOVERNING RULING — PK-R-1 (native, binding): "a 'window' served for timing
 * decisions must be at MINIMUM a month-resolution span carrying a day-
 * precision peak, or a dated point row. Decade-era rows alone are CONTEXT,
 * not windows — they may serve, but only labeled at their own resolution,
 * never presented as the timing claim itself."
 *
 * Coverage:
 *   - deriveResolutionDisclosure: stored resolution trusted as-is; NULL
 *     (legacy pre-migration-567) rows get an honest duration-based implied
 *     label; the PK-R-1 gate (is_timing_window) is false for any effective
 *     'era' resolution, stored or implied.
 *   - computeWindowFacets.resolution: real per-row detector, never a
 *     hand-maintained count.
 *   - summarizeResolutionDisclosure: the §N.6-style context_only_rows_in_page
 *     / context_only_note page summary.
 *   - Migration 567 file: parent_window_id/resolution on both tables,
 *     self-verification block, DOWN path (mirrors the MR-01 migration-564
 *     test pattern in register_gochara_windows_mr01.test.ts).
 *   - End-to-end wiring: the `resolution` filter param reaches the SQL sent
 *     to platformQuery; a served row's resolution_disclosure is attached.
 *
 * Unit tests (no live DB) — mirrors register_gochara_windows_mr01.test.ts's
 * fetch-mocking pattern for the integration-shaped cases.
 */

import { describe, it, expect, vi } from 'vitest'
import {
  deriveResolutionDisclosure,
  computeGocharaActivation,
  computeGocharaForecast,
  computeGocharaElectionAvoidance,
  type GocharaWindowRow,
} from './register_gochara_windows.js'

function makeRow(overrides: Partial<GocharaWindowRow> = {}): GocharaWindowRow {
  return {
    id: 1,
    chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
    event_class: 'marriage',
    temporal_shape: 'interval',
    window_start: '2013-01-01',
    window_end: '2013-01-08',
    peak_date: '2013-01-04',
    milestone_id: null,
    is_irreversibility_milestone: false,
    signed_intensity: 0.7,
    raw_intensity: 0.7,
    valence: 'neutral',
    is_adverse: false,
    active_sentences: [],
    contributing_systems: [],
    suppression_state: {},
    peak_basis: 'gochara_lambda_v3',
    calibration_state: 'structural_prior',
    source: 'live',
    computed_at: '2026-08-11T00:00:00Z',
    continuity_state: null,
    plateau_disclosure: null,
    ...overrides,
  }
}

/** Build a fake fetch response returning a { rows } JSON payload. */
function fakeJsonResponse(rows: unknown[]): Response {
  return {
    ok: true,
    json: () => Promise.resolve({ rows }),
    text: () => Promise.resolve(JSON.stringify({ rows })),
  } as unknown as Response
}

const PRINCIPAL = { user_uid: 'test', key_id: 'test', role: 'super_admin' as const }
const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

// ══════════════════════════════════════════════════════════════════════════
// deriveResolutionDisclosure — pure function unit tests
// ══════════════════════════════════════════════════════════════════════════

describe('deriveResolutionDisclosure — stored resolution (migration 567 rows)', () => {
  it('trusts a stored resolution="era" as-is and gates is_timing_window=false', () => {
    const d = deriveResolutionDisclosure(makeRow({ resolution: 'era' }))
    expect(d).toEqual({ resolution: 'era', resolution_source: 'stored', is_timing_window: false })
  })

  it('trusts a stored resolution="month" as-is and is_timing_window=true', () => {
    const d = deriveResolutionDisclosure(makeRow({ resolution: 'month' }))
    expect(d).toEqual({ resolution: 'month', resolution_source: 'stored', is_timing_window: true })
  })

  it('trusts a stored resolution="day" as-is and is_timing_window=true', () => {
    const d = deriveResolutionDisclosure(makeRow({ resolution: 'day' }))
    expect(d).toEqual({ resolution: 'day', resolution_source: 'stored', is_timing_window: true })
  })

  it('a stored era-tier row with a precise peak_date is still NOT a timing window (PK-R-1 core case)', () => {
    // This is the exact PK-R-1 hazard: a decade-era row can carry a
    // day-precision peak_date and look confidently specific. The stored
    // resolution tier must still gate it as context, never a timing claim.
    const d = deriveResolutionDisclosure(
      makeRow({ resolution: 'era', window_start: '1984-02-05', window_end: '1994-02-05', peak_date: '1989-06-12' })
    )
    expect(d.is_timing_window).toBe(false)
  })
})

describe('deriveResolutionDisclosure — NULL resolution (legacy pre-migration-567 rows)', () => {
  it('a point-shaped row is always implied "day" / is_timing_window=true (PK-R-1\'s dated-point floor)', () => {
    const d = deriveResolutionDisclosure(
      makeRow({ resolution: null, temporal_shape: 'point', window_start: '2013-01-01', window_end: '2013-01-01' })
    )
    expect(d).toEqual({ resolution: 'day', resolution_source: 'implied_from_duration', is_timing_window: true })
  })

  it('a ~500-day legacy interval is implied "era", is_timing_window=false (the exact PK-R-1 hazard)', () => {
    const d = deriveResolutionDisclosure(
      makeRow({ resolution: null, temporal_shape: 'interval', window_start: '2013-01-01', window_end: '2014-05-16' })
    )
    expect(d.resolution).toBe('era')
    expect(d.resolution_source).toBe('implied_from_duration')
    expect(d.is_timing_window).toBe(false)
  })

  it('a 1-day legacy interval is implied "day", is_timing_window=true', () => {
    const d = deriveResolutionDisclosure(
      makeRow({ resolution: null, temporal_shape: 'interval', window_start: '2013-01-01', window_end: '2013-01-02' })
    )
    expect(d.resolution).toBe('day')
    expect(d.is_timing_window).toBe(true)
  })

  it('a 20-day legacy interval is implied "month", is_timing_window=true', () => {
    const d = deriveResolutionDisclosure(
      makeRow({ resolution: null, temporal_shape: 'interval', window_start: '2013-01-01', window_end: '2013-01-21' })
    )
    expect(d.resolution).toBe('month')
    expect(d.is_timing_window).toBe(true)
  })

  it('a 100-day legacy interval (ambiguous gap between month and era) is honestly "unavailable", never guessed', () => {
    const d = deriveResolutionDisclosure(
      makeRow({ resolution: null, temporal_shape: 'interval', window_start: '2013-01-01', window_end: '2013-04-11' })
    )
    expect(d).toEqual({ resolution: null, resolution_source: 'unavailable', is_timing_window: false })
  })

  it('malformed dates degrade to "unavailable" honestly, never throw', () => {
    const d = deriveResolutionDisclosure(
      makeRow({ resolution: null, temporal_shape: 'interval', window_start: 'not-a-date', window_end: '2013-01-02' })
    )
    expect(d).toEqual({ resolution: null, resolution_source: 'unavailable', is_timing_window: false })
  })

  it('never conflates a stored tier with an implied one on the same row', () => {
    const stored = deriveResolutionDisclosure(makeRow({ resolution: 'month' }))
    const implied = deriveResolutionDisclosure(
      makeRow({ resolution: null, window_start: '2013-01-01', window_end: '2013-01-21' })
    )
    expect(stored.resolution).toBe(implied.resolution) // both 'month'...
    expect(stored.resolution_source).not.toBe(implied.resolution_source) // ...but disclosed differently
  })
})

// ══════════════════════════════════════════════════════════════════════════
// computeWindowFacets.resolution + summarizeResolutionDisclosure —
// via the live compute* functions (real detector, not a mocked unit)
// ══════════════════════════════════════════════════════════════════════════

// The main row query's ROW_COLUMNS opens with this exact column list — a
// unique-enough signature to distinguish "the query IS against
// kala_gochara_windows" from "a query that merely references the table name
// inside a subquery" (AUTHORITATIVE_GENERATION_FILTER's correlated subquery
// against kala_gochara_authority literally contains the substring
// 'kala_gochara_authority', so that check must never fire on the main row
// query — checked FIRST, before any other routing branch, for that reason).
const MAIN_ROW_QUERY_SIGNATURE = 'id, chart_id, event_class, temporal_shape'

function mockRowQuery(rows: Record<string, unknown>[]) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation((_url, init) => {
    const { sql } = JSON.parse((init as RequestInit).body as string) as { sql: string }
    if (sql.includes(MAIN_ROW_QUERY_SIGNATURE)) return Promise.resolve(fakeJsonResponse(rows))
    if (sql.includes('kala_gochara_authority')) return Promise.resolve(fakeJsonResponse([]))
    if (sql.includes('gochara_resonance_map') && !sql.includes('rm.event_class')) {
      return Promise.resolve(fakeJsonResponse([]))
    }
    if (sql.includes('brahma_event_ontology')) return Promise.resolve(fakeJsonResponse([{ domain: 'marriage' }]))
    if (sql.includes('build_substep_progress')) {
      return Promise.resolve(fakeJsonResponse([{ substeps_committed: 0, swept_event_classes: [] }]))
    }
    return Promise.resolve(fakeJsonResponse(rows))
  })
}

const BASE_DB_ROW = {
  id: 1,
  chart_id: CHART_ID,
  event_class: 'marriage',
  temporal_shape: 'interval',
  milestone_id: null,
  is_irreversibility_milestone: false,
  signed_intensity: 0.7,
  raw_intensity: 0.7,
  valence: 'neutral',
  is_adverse: false,
  active_sentences: [],
  contributing_systems: [],
  suppression_state: {},
  peak_basis: 'gochara_lambda_v3',
  calibration_state: 'structural_prior',
  source: 'live',
  computed_at: '2026-08-11T00:00:00Z',
  continuity_state: null,
  generation: '3.0',
  era_slice_key: 'g3_1984_1994',
  term_breakdown: null,
  parent_window_id: null,
}

describe('computeWindowFacets.resolution via computeGocharaActivation (real detector)', () => {
  it('counts a mix of era/month/day rows into facets.resolution', async () => {
    const fetchSpy = mockRowQuery([
      { ...BASE_DB_ROW, id: 1, window_start: '1984-02-15', window_end: '1994-02-15', peak_date: '1989-06-01', resolution: 'era' },
      { ...BASE_DB_ROW, id: 2, window_start: '1984-02-15', window_end: '1984-03-15', peak_date: '1984-03-01', resolution: 'month' },
      { ...BASE_DB_ROW, id: 3, window_start: '1984-02-15', window_end: '1984-02-16', peak_date: '1984-02-15', resolution: 'day' },
    ])

    const result = (await computeGocharaActivation(CHART_ID, '1984-02-15', PRINCIPAL, 'marriage')) as {
      facets: { resolution: { era: number; month: number; day: number; unavailable: number; stored_count: number; implied_count: number } }
    }

    expect(result.facets.resolution).toEqual({
      era: 1, month: 1, day: 1, unavailable: 0, stored_count: 3, implied_count: 0,
    })

    fetchSpy.mockRestore()
  })

  it('every served window carries a resolution_disclosure object', async () => {
    const fetchSpy = mockRowQuery([
      { ...BASE_DB_ROW, id: 1, window_start: '1984-02-15', window_end: '1994-02-15', peak_date: '1989-06-01', resolution: 'era' },
    ])

    const result = (await computeGocharaActivation(CHART_ID, '1984-02-15', PRINCIPAL, 'marriage')) as {
      windows: Array<{ resolution_disclosure: { resolution: string; is_timing_window: boolean } }>
    }

    expect(result.windows).toHaveLength(1)
    expect(result.windows[0]!.resolution_disclosure).toEqual({
      resolution: 'era', resolution_source: 'stored', is_timing_window: false,
    })

    fetchSpy.mockRestore()
  })

  it('provenance_envelope.context_only_rows_in_page/note reflect era-tier rows honestly', async () => {
    const fetchSpy = mockRowQuery([
      { ...BASE_DB_ROW, id: 1, window_start: '1984-02-15', window_end: '1994-02-15', peak_date: '1989-06-01', resolution: 'era' },
      { ...BASE_DB_ROW, id: 2, window_start: '1984-02-15', window_end: '1984-02-16', peak_date: '1984-02-15', resolution: 'day' },
    ])

    const result = (await computeGocharaActivation(CHART_ID, '1984-02-15', PRINCIPAL, 'marriage')) as {
      provenance_envelope: { context_only_rows_in_page: number; context_only_note: string | null }
    }

    expect(result.provenance_envelope.context_only_rows_in_page).toBe(1)
    expect(result.provenance_envelope.context_only_note).toContain('1 of 2')
    expect(result.provenance_envelope.context_only_note).toContain('PK-R-1')

    fetchSpy.mockRestore()
  })

  it('zero era-tier rows -> context_only_rows_in_page=0, context_only_note=null', async () => {
    const fetchSpy = mockRowQuery([
      { ...BASE_DB_ROW, id: 1, window_start: '1984-02-15', window_end: '1984-02-16', peak_date: '1984-02-15', resolution: 'day' },
    ])

    const result = (await computeGocharaActivation(CHART_ID, '1984-02-15', PRINCIPAL, 'marriage')) as {
      provenance_envelope: { context_only_rows_in_page: number; context_only_note: string | null }
    }

    expect(result.provenance_envelope.context_only_rows_in_page).toBe(0)
    expect(result.provenance_envelope.context_only_note).toBeNull()

    fetchSpy.mockRestore()
  })
})

// ══════════════════════════════════════════════════════════════════════════
// resolution filter param — reaches the SQL sent to platformQuery
// ══════════════════════════════════════════════════════════════════════════

describe('resolution filter param wiring', () => {
  it('computeGocharaActivation: resolution="month" adds "AND resolution = $n" to the SQL and passes it as a param', async () => {
    let capturedSql: string | undefined
    let capturedParams: unknown[] | undefined
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation((_url, init) => {
      const { sql, params } = JSON.parse((init as RequestInit).body as string) as { sql: string; params: unknown[] }
      if (sql.includes(MAIN_ROW_QUERY_SIGNATURE)) {
        capturedSql = sql
        capturedParams = params
        return Promise.resolve(fakeJsonResponse([]))
      }
      if (sql.includes('kala_gochara_authority')) return Promise.resolve(fakeJsonResponse([]))
      if (sql.includes('gochara_resonance_map') && !sql.includes('rm.event_class')) return Promise.resolve(fakeJsonResponse([]))
      if (sql.includes('brahma_event_ontology')) return Promise.resolve(fakeJsonResponse([{ domain: 'marriage' }]))
      if (sql.includes('build_substep_progress')) return Promise.resolve(fakeJsonResponse([{ substeps_committed: 0, swept_event_classes: [] }]))
      return Promise.resolve(fakeJsonResponse([]))
    })

    await computeGocharaActivation(CHART_ID, '1984-02-15', PRINCIPAL, 'marriage', undefined, 'month')

    expect(capturedSql).toContain('AND resolution = $')
    expect(capturedParams).toContain('month')

    fetchSpy.mockRestore()
  })

  it('computeGocharaForecast: resolution filter reaches the SQL', async () => {
    let capturedSql: string | undefined
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation((_url, init) => {
      const { sql } = JSON.parse((init as RequestInit).body as string) as { sql: string }
      if (sql.includes(MAIN_ROW_QUERY_SIGNATURE)) {
        capturedSql = sql
        return Promise.resolve(fakeJsonResponse([]))
      }
      if (sql.includes('kala_gochara_authority')) return Promise.resolve(fakeJsonResponse([]))
      if (sql.includes('gochara_resonance_map') && !sql.includes('rm.event_class')) return Promise.resolve(fakeJsonResponse([]))
      if (sql.includes('brahma_event_ontology')) return Promise.resolve(fakeJsonResponse([{ domain: 'marriage' }]))
      if (sql.includes('build_substep_progress')) return Promise.resolve(fakeJsonResponse([{ substeps_committed: 0, swept_event_classes: [] }]))
      return Promise.resolve(fakeJsonResponse([]))
    })

    await computeGocharaForecast(
      CHART_ID, { start: '1984-01-01', end: '2084-01-01' }, undefined, undefined, 100, PRINCIPAL, undefined, 'era'
    )

    expect(capturedSql).toContain('AND resolution = $')

    fetchSpy.mockRestore()
  })

  it('computeGocharaElectionAvoidance: resolution filter reaches the SQL and windows carry resolution/parent_window_id', async () => {
    let capturedSql: string | undefined
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation((_url, init) => {
      const { sql } = JSON.parse((init as RequestInit).body as string) as { sql: string }
      if (sql.includes(MAIN_ROW_QUERY_SIGNATURE)) {
        capturedSql = sql
        return Promise.resolve(fakeJsonResponse([
          {
            ...BASE_DB_ROW, id: 9, is_adverse: true,
            window_start: '1984-02-15', window_end: '1994-02-15', peak_date: '1989-06-01',
            resolution: 'era', parent_window_id: null,
          },
        ]))
      }
      if (sql.includes('kala_gochara_authority')) return Promise.resolve(fakeJsonResponse([]))
      if (sql.includes('gochara_resonance_map') && !sql.includes('rm.event_class')) return Promise.resolve(fakeJsonResponse([]))
      if (sql.includes('brahma_event_ontology')) return Promise.resolve(fakeJsonResponse([{ domain: 'marriage' }]))
      if (sql.includes('build_substep_progress')) return Promise.resolve(fakeJsonResponse([{ substeps_committed: 0, swept_event_classes: [] }]))
      if (sql.includes('brahma_remedy_corpus')) return Promise.resolve(fakeJsonResponse([]))
      return Promise.resolve(fakeJsonResponse([]))
    })

    const result = (await computeGocharaElectionAvoidance(
      CHART_ID, { start: '1984-01-01', end: '2084-01-01' }, undefined, 50, PRINCIPAL, undefined, 'day'
    )) as { windows: Array<{ resolution: string | null; parent_window_id: number | null; resolution_disclosure: { is_timing_window: boolean } }> }

    expect(capturedSql).toContain('AND resolution = $')
    expect(result.windows).toHaveLength(1)
    expect(result.windows[0]!.resolution).toBe('era')
    expect(result.windows[0]!.parent_window_id).toBeNull()
    expect(result.windows[0]!.resolution_disclosure.is_timing_window).toBe(false)

    fetchSpy.mockRestore()
  })
})

// ══════════════════════════════════════════════════════════════════════════
// Migration 567 file — self-verification structure (mirrors the MR-01
// migration-564 test pattern in register_gochara_windows_mr01.test.ts)
// ══════════════════════════════════════════════════════════════════════════

describe('Migration 567 — parent_window_id + resolution on both gochara tables', () => {
  async function migPath(): Promise<string> {
    const path = await import('path')
    return path.join(process.cwd().replace(/\/platform-mcp$/, ''), 'platform/migrations/567_parishkara_mr11_hierarchy.sql')
  }

  it('migration 567 file exists at platform/migrations/', async () => {
    const fs = await import('fs/promises')
    const stat = await fs.stat(await migPath())
    expect(stat.isFile()).toBe(true)
  })

  it('ALTERs both kala_gochara_windows and kala_gochara_windows_v2', async () => {
    const fs = await import('fs/promises')
    const sql = await fs.readFile(await migPath(), 'utf-8')
    expect(sql).toContain('ALTER TABLE kala_gochara_windows')
    expect(sql).toContain('ALTER TABLE kala_gochara_windows_v2')
  })

  it('adds parent_window_id BIGINT and resolution TEXT columns', async () => {
    const fs = await import('fs/promises')
    const sql = await fs.readFile(await migPath(), 'utf-8')
    expect(sql).toMatch(/ADD COLUMN IF NOT EXISTS parent_window_id\s+BIGINT/)
    expect(sql).toMatch(/ADD COLUMN IF NOT EXISTS resolution\s+TEXT/)
  })

  it('has a self-verification DO block with RAISE EXCEPTION for both new columns', async () => {
    const fs = await import('fs/promises')
    const sql = await fs.readFile(await migPath(), 'utf-8')
    expect(sql).toContain('DO $$')
    expect(sql).toMatch(/RAISE EXCEPTION[^;]*parent_window_id/s)
    expect(sql).toMatch(/RAISE EXCEPTION[^;]*resolution/s)
  })

  it('documents a DOWN rollback path that drops both columns from both tables', async () => {
    const fs = await import('fs/promises')
    const sql = await fs.readFile(await migPath(), 'utf-8')
    expect(sql).toContain('DOWN')
    expect(sql).toMatch(/DROP COLUMN IF EXISTS parent_window_id/)
    expect(sql).toMatch(/DROP COLUMN IF EXISTS resolution/)
  })

  it('contains no INSERT/UPDATE/DELETE against either gochara table (schema-only, protected corpus)', async () => {
    const fs = await import('fs/promises')
    const sql = await fs.readFile(await migPath(), 'utf-8')
    // Strip comments (lines starting with -- ) before checking for DML verbs
    // to avoid false positives from prose mentioning INSERT/DELETE.
    const codeOnly = sql
      .split('\n')
      .filter((line) => !line.trim().startsWith('--'))
      .join('\n')
    expect(codeOnly).not.toMatch(/\bINSERT\s+INTO\s+kala_gochara_windows/i)
    expect(codeOnly).not.toMatch(/\bDELETE\s+FROM\s+kala_gochara_windows/i)
    expect(codeOnly).not.toMatch(/\bUPDATE\s+kala_gochara_windows/i)
  })
})

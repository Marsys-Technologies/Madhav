/**
 * register_gochara_windows_mr11.test.ts — PARIṢKĀRA MR-11(b) / ADJUDICATOR
 * ruling PK-R-8 TDD tests.
 *
 * GOVERNING RULING — PK-R-1 (native, binding): "a 'window' served for timing
 * decisions must be at MINIMUM a month-resolution span carrying a day-
 * precision peak, or a dated point row. Decade-era rows alone are CONTEXT,
 * not windows — they may serve, but only labeled at their own resolution,
 * never presented as the timing claim itself."
 *
 * PK-R-8 R8.9/R8.10 SUPERSEDE this file's original duration-based "implied"
 * inference for legacy rows: is_timing_window is now EARNED, never guessed
 * from window_start/window_end span:
 *   temporal_shape === 'point'
 *   OR (resolution IN {'month','day'} AND peak_basis IN GENUINE_PEAK_BASES)
 *
 * Coverage:
 *   - deriveResolutionDisclosure: the R8.9 two-clause EARNED formula, the
 *     R8.10 disclosed consequence (v1 interval rows -> blocked, v1 point
 *     rows -> unaffected), and timing_window_blocked_reason population.
 *   - computeWindowFacets.resolution: real per-row detector (stored
 *     resolution counts only — R8.9 removed the implied/duration axis).
 *   - summarizeResolutionDisclosure / resolution_breakdown (R8.15).
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

// Mirrors services/gochara_v3/peak_basis_vocab.py exactly.
const LAMBDA_V3_ARGMAX = 'gochara_lambda_v3_argmax'
const LAMBDA_V3_COARSE_ARGMAX = 'gochara_lambda_v3_coarse_argmax'
const LAMBDA_V3_MIDPOINT = 'gochara_lambda_v3_midpoint'
const GOCHARA_LAMBDA_E_V1 = 'gochara_lambda_e_v1' // the v1 sweep's own citation
// PK-R-8a (2026-08-11): mirrors services/gochara_v3/peak_basis_vocab.py's
// ONTOLOGY_MILESTONE_OFFSET exactly.
const ONTOLOGY_MILESTONE_OFFSET = 'ontology_milestone_offset'

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
    peak_basis: LAMBDA_V3_ARGMAX,
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
// deriveResolutionDisclosure — pure function unit tests (R8.9 EARNED formula)
// ══════════════════════════════════════════════════════════════════════════

describe('deriveResolutionDisclosure — stored resolution="era" (R8.9 clause 1 gate)', () => {
  it('a stored era row is CONTEXT: is_timing_window=false, blocked_reason=era_resolution', () => {
    const d = deriveResolutionDisclosure(makeRow({ resolution: 'era', peak_basis: LAMBDA_V3_COARSE_ARGMAX }))
    expect(d).toEqual({
      resolution: 'era', resolution_source: 'stored',
      is_timing_window: false, timing_window_blocked_reason: 'era_resolution',
    })
  })

  it('an era row with a precise peak_date is STILL not a timing window (PK-R-1 core case)', () => {
    // Exactly the PK-R-1 hazard: a decade-era span can carry a day-precision
    // peak_date and look confidently specific. The stored resolution tier
    // gates it as context regardless of peak_basis.
    const d = deriveResolutionDisclosure(
      makeRow({ resolution: 'era', peak_basis: LAMBDA_V3_COARSE_ARGMAX, peak_date: '1989-06-12' })
    )
    expect(d.is_timing_window).toBe(false)
    expect(d.timing_window_blocked_reason).toBe('era_resolution')
  })
})

describe('deriveResolutionDisclosure — resolution IN {month,day} EARNED via peak_basis (R8.9 clause 2)', () => {
  it('resolution="month" + peak_basis=LAMBDA_V3_ARGMAX -> EARNED, is_timing_window=true', () => {
    const d = deriveResolutionDisclosure(makeRow({ resolution: 'month', peak_basis: LAMBDA_V3_ARGMAX }))
    expect(d).toEqual({
      resolution: 'month', resolution_source: 'stored',
      is_timing_window: true, timing_window_blocked_reason: null,
    })
  })

  it('resolution="day" + peak_basis=LAMBDA_V3_ARGMAX -> EARNED, is_timing_window=true', () => {
    const d = deriveResolutionDisclosure(makeRow({ resolution: 'day', peak_basis: LAMBDA_V3_ARGMAX }))
    expect(d.is_timing_window).toBe(true)
    expect(d.timing_window_blocked_reason).toBeNull()
  })

  it('resolution="month" + peak_basis=LAMBDA_V3_COARSE_ARGMAX -> NOT earned (never day-refined)', () => {
    const d = deriveResolutionDisclosure(makeRow({ resolution: 'month', peak_basis: LAMBDA_V3_COARSE_ARGMAX }))
    expect(d.is_timing_window).toBe(false)
    expect(d.timing_window_blocked_reason).toBe('peak_basis_not_argmax')
  })

  it('resolution="day" + peak_basis=LAMBDA_V3_MIDPOINT -> NOT earned (prohibited basis)', () => {
    const d = deriveResolutionDisclosure(makeRow({ resolution: 'day', peak_basis: LAMBDA_V3_MIDPOINT }))
    expect(d.is_timing_window).toBe(false)
    expect(d.timing_window_blocked_reason).toBe('peak_basis_not_argmax')
  })

  it('resolution="month" + peak_basis=null -> NOT earned', () => {
    const d = deriveResolutionDisclosure(makeRow({ resolution: 'month', peak_basis: null as unknown as string }))
    expect(d.is_timing_window).toBe(false)
    expect(d.timing_window_blocked_reason).toBe('peak_basis_not_argmax')
  })
})

describe('deriveResolutionDisclosure — PK-R-1 dated-point floor (temporal_shape="point")', () => {
  it('a point-shaped row is ALWAYS a timing window, regardless of resolution/peak_basis', () => {
    const d = deriveResolutionDisclosure(
      makeRow({ temporal_shape: 'point', resolution: null, peak_basis: GOCHARA_LAMBDA_E_V1 })
    )
    expect(d.is_timing_window).toBe(true)
    expect(d.timing_window_blocked_reason).toBeNull()
  })

  it('a point-shaped row with resolution="era" is still a timing window (temporal_shape wins)', () => {
    const d = deriveResolutionDisclosure(
      makeRow({ temporal_shape: 'point', resolution: 'era', peak_basis: LAMBDA_V3_COARSE_ARGMAX })
    )
    expect(d.is_timing_window).toBe(true)
  })
})

describe('deriveResolutionDisclosure — R8.10 disclosed consequence (v1 rows)', () => {
  it('a v1 INTERVAL row (peak_basis=gochara_lambda_e_v1, resolution=NULL) is now CONTEXT: '
    + 'is_timing_window=false, blocked_reason=resolution_unavailable (RULED, not a bug)', () => {
    const d = deriveResolutionDisclosure(
      makeRow({ temporal_shape: 'interval', resolution: null, peak_basis: GOCHARA_LAMBDA_E_V1 })
    )
    expect(d).toEqual({
      resolution: null, resolution_source: 'unavailable',
      is_timing_window: false, timing_window_blocked_reason: 'resolution_unavailable',
    })
  })

  it('a v1 POINT row is UNAFFECTED by the interval-row flip (R8.10: only interval rows flip)', () => {
    const d = deriveResolutionDisclosure(
      makeRow({ temporal_shape: 'point', resolution: null, peak_basis: GOCHARA_LAMBDA_E_V1 })
    )
    expect(d.is_timing_window).toBe(true)
  })

  it('a v1 CHAIN row (not point-shaped) is also CONTEXT, but PK-R-8a gives it a MORE SPECIFIC reason than plain interval rows', () => {
    // PK-R-8a (2026-08-11): a chain row short-circuits on its OWN clause
    // BEFORE the generic resolution-tier fallback below -- a v1 chain row's
    // legacy basis (GOCHARA_LAMBDA_E_V1, not ONTOLOGY_MILESTONE_OFFSET) is
    // therefore reported as 'chain_basis_not_declared' (a more precise,
    // chain-specific reason), not the generic 'resolution_unavailable' an
    // earlier, pre-PK-R-8a version of this test expected.
    const d = deriveResolutionDisclosure(
      makeRow({ temporal_shape: 'chain', resolution: null, peak_basis: GOCHARA_LAMBDA_E_V1 })
    )
    expect(d.is_timing_window).toBe(false)
    expect(d.resolution_source).toBe('not_hierarchy_classified')
    expect(d.timing_window_blocked_reason).toBe('chain_basis_not_declared')
  })
})

describe('deriveResolutionDisclosure — never guesses a tier from date span (R8.9 supersedes duration inference)', () => {
  it('a NULL-resolution, non-point row is honestly "unavailable" regardless of its window_start/window_end span', () => {
    // A 1-day span used to be "implied day" under the pre-PK-R-8 design;
    // R8.9 removed that inference entirely -- span is never consulted.
    const d = deriveResolutionDisclosure(
      makeRow({ resolution: null, temporal_shape: 'interval', window_start: '2013-01-01', window_end: '2013-01-02' })
    )
    expect(d.resolution).toBeNull()
    expect(d.is_timing_window).toBe(false)
    expect(d.timing_window_blocked_reason).toBe('resolution_unavailable')
  })

  it('malformed/absent dates never throw (resolution/temporal_shape/peak_basis alone drive the result)', () => {
    const d = deriveResolutionDisclosure(
      makeRow({ resolution: null, temporal_shape: 'interval', window_start: 'not-a-date', window_end: '2013-01-02' })
    )
    expect(d.resolution).toBeNull()
    expect(d.is_timing_window).toBe(false)
  })
})

// ══════════════════════════════════════════════════════════════════════════
// computeWindowFacets.resolution + summarizeResolutionDisclosure/breakdown —
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
  it('counts a mix of era/month/day rows into facets.resolution by STORED resolution', async () => {
    const fetchSpy = mockRowQuery([
      { ...BASE_DB_ROW, id: 1, window_start: '1984-02-15', window_end: '1994-02-15', peak_date: '1989-06-01', resolution: 'era', peak_basis: LAMBDA_V3_COARSE_ARGMAX },
      { ...BASE_DB_ROW, id: 2, window_start: '1984-02-15', window_end: '1984-03-15', peak_date: '1984-03-01', resolution: 'month', peak_basis: LAMBDA_V3_ARGMAX },
      { ...BASE_DB_ROW, id: 3, window_start: '1984-02-15', window_end: '1984-02-16', peak_date: '1984-02-15', resolution: 'day', peak_basis: LAMBDA_V3_ARGMAX },
    ])

    const result = (await computeGocharaActivation(CHART_ID, '1984-02-15', PRINCIPAL, 'marriage')) as {
      facets: { resolution: { era: number; month: number; day: number; unavailable: number } }
    }

    expect(result.facets.resolution).toEqual({ era: 1, month: 1, day: 1, unavailable: 0 })

    fetchSpy.mockRestore()
  })

  it('every served window carries a resolution_disclosure object with timing_window_blocked_reason', async () => {
    const fetchSpy = mockRowQuery([
      { ...BASE_DB_ROW, id: 1, window_start: '1984-02-15', window_end: '1994-02-15', peak_date: '1989-06-01', resolution: 'era', peak_basis: LAMBDA_V3_COARSE_ARGMAX },
    ])

    const result = (await computeGocharaActivation(CHART_ID, '1984-02-15', PRINCIPAL, 'marriage')) as {
      windows: Array<{ resolution_disclosure: { resolution: string; is_timing_window: boolean; timing_window_blocked_reason: string | null } }>
    }

    expect(result.windows).toHaveLength(1)
    expect(result.windows[0]!.resolution_disclosure).toEqual({
      resolution: 'era', resolution_source: 'stored',
      is_timing_window: false, timing_window_blocked_reason: 'era_resolution',
    })

    fetchSpy.mockRestore()
  })

  it('provenance_envelope.context_only_rows_in_page/note reflect era-tier rows honestly', async () => {
    const fetchSpy = mockRowQuery([
      { ...BASE_DB_ROW, id: 1, window_start: '1984-02-15', window_end: '1994-02-15', peak_date: '1989-06-01', resolution: 'era', peak_basis: LAMBDA_V3_COARSE_ARGMAX },
      { ...BASE_DB_ROW, id: 2, window_start: '1984-02-15', window_end: '1984-02-16', peak_date: '1984-02-15', resolution: 'day', peak_basis: LAMBDA_V3_ARGMAX },
    ])

    const result = (await computeGocharaActivation(CHART_ID, '1984-02-15', PRINCIPAL, 'marriage')) as {
      provenance_envelope: {
        context_only_rows_in_page: number; context_only_note: string | null
        resolution_breakdown: { era: number; month: number; day: number; unclassified: number }
      }
    }

    expect(result.provenance_envelope.context_only_rows_in_page).toBe(1)
    expect(result.provenance_envelope.context_only_note).toContain('1 of 2')
    expect(result.provenance_envelope.context_only_note).toContain('PK-R-1')
    // R8.15: resolution_breakdown reflects the same two rows.
    expect(result.provenance_envelope.resolution_breakdown).toEqual({ era: 1, month: 0, day: 1, unclassified: 0 })

    fetchSpy.mockRestore()
  })

  it('zero era-tier rows -> context_only_rows_in_page=0, context_only_note=null', async () => {
    const fetchSpy = mockRowQuery([
      { ...BASE_DB_ROW, id: 1, window_start: '1984-02-15', window_end: '1984-02-16', peak_date: '1984-02-15', resolution: 'day', peak_basis: LAMBDA_V3_ARGMAX },
    ])

    const result = (await computeGocharaActivation(CHART_ID, '1984-02-15', PRINCIPAL, 'marriage')) as {
      provenance_envelope: { context_only_rows_in_page: number; context_only_note: string | null }
    }

    expect(result.provenance_envelope.context_only_rows_in_page).toBe(0)
    expect(result.provenance_envelope.context_only_note).toBeNull()

    fetchSpy.mockRestore()
  })

  it('a month row with a NON-genuine peak_basis (coarse) counts as context-only despite resolution="month"', async () => {
    const fetchSpy = mockRowQuery([
      { ...BASE_DB_ROW, id: 1, window_start: '1984-02-15', window_end: '1984-03-15', peak_date: '1984-03-01', resolution: 'month', peak_basis: LAMBDA_V3_COARSE_ARGMAX },
    ])

    const result = (await computeGocharaActivation(CHART_ID, '1984-02-15', PRINCIPAL, 'marriage')) as {
      provenance_envelope: { context_only_rows_in_page: number }
      windows: Array<{ resolution_disclosure: { timing_window_blocked_reason: string | null } }>
    }

    expect(result.provenance_envelope.context_only_rows_in_page).toBe(1)
    expect(result.windows[0]!.resolution_disclosure.timing_window_blocked_reason).toBe('peak_basis_not_argmax')

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
            resolution: 'era', peak_basis: LAMBDA_V3_COARSE_ARGMAX, parent_window_id: null,
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

// ══════════════════════════════════════════════════════════════════════════
// PK-R-8a (2026-08-11, ADJUDICATOR ruling) — the chain-basis question
// ══════════════════════════════════════════════════════════════════════════
//
// A chain milestone's date is DECLARED by brahma_event_ontology's
// milestone_template (episode_anchor_jd + typical_offset_days), never
// LOCATED by a peak search — it earns is_timing_window through its OWN,
// THIRD clause in the EARNED formula:
//   is_timing_window =
//     temporal_shape === 'point'
//     || (temporal_shape === 'chain' && peak_basis === ONTOLOGY_MILESTONE_OFFSET
//         && milestone_id != null)
//     || (resolution IN {'month','day'} && peak_basis IN GENUINE_PEAK_BASES)
// never through the resolution-tier clause (chain rows carry resolution=NULL
// unconditionally — see ka_gochara_v3_century_materialize.py's run_substep
// chain branch).

describe('deriveResolutionDisclosure — PK-R-8a chain-basis clause', () => {
  it('test_chain_rows_never_carry_argmax_basis: a chain row with the correct ONTOLOGY_MILESTONE_OFFSET basis and a real milestone_id earns is_timing_window=true, resolution=null, resolution_source=not_hierarchy_classified', () => {
    const d = deriveResolutionDisclosure(
      makeRow({
        temporal_shape: 'chain', resolution: null,
        peak_basis: ONTOLOGY_MILESTONE_OFFSET, milestone_id: 'first_revenue',
      })
    )
    expect(d).toEqual({
      resolution: null,
      resolution_source: 'not_hierarchy_classified',
      is_timing_window: true,
      timing_window_blocked_reason: null,
    })
  })

  it('test_chain_milestone_earns_timing_window: identical shape asserted a second, independent way (this IS the PK-R-8a deliverable)', () => {
    const d = deriveResolutionDisclosure(
      makeRow({
        temporal_shape: 'chain', resolution: null,
        peak_basis: ONTOLOGY_MILESTONE_OFFSET, milestone_id: 'ceremony',
      })
    )
    expect(d.is_timing_window).toBe(true)
    expect(d.resolution).toBeNull()
    expect(d.resolution_source).toBe('not_hierarchy_classified')
    expect(d.timing_window_blocked_reason).toBeNull()
  })

  it('test_chain_signal_has_a_real_negative_path: milestone_id=null blocks with chain_milestone_unanchored even though the basis is correctly declared', () => {
    const d = deriveResolutionDisclosure(
      makeRow({
        temporal_shape: 'chain', resolution: null,
        peak_basis: ONTOLOGY_MILESTONE_OFFSET, milestone_id: null,
      })
    )
    expect(d.is_timing_window).toBe(false)
    expect(d.timing_window_blocked_reason).toBe('chain_milestone_unanchored')
  })

  it('test_chain_signal_has_a_real_negative_path: a stray LAMBDA_V3_ARGMAX basis (the pre-PK-R-8a stamp) blocks with chain_basis_not_declared, even with a real milestone_id', () => {
    const d = deriveResolutionDisclosure(
      makeRow({
        temporal_shape: 'chain', resolution: null,
        peak_basis: LAMBDA_V3_ARGMAX, milestone_id: 'first_revenue',
      })
    )
    expect(d.is_timing_window).toBe(false)
    expect(d.timing_window_blocked_reason).toBe('chain_basis_not_declared')
  })

  it('test_chain_span_inference_cannot_grant_timing_window: a ZERO-SPAN chain row (window_start===window_end===peak_date, as every real chain row is) with the legacy v1 basis still reads false via the chain clause, never via a duration/span inference path', () => {
    const d = deriveResolutionDisclosure(
      makeRow({
        temporal_shape: 'chain', resolution: null,
        peak_basis: GOCHARA_LAMBDA_E_V1, milestone_id: 'engagement',
        window_start: '2013-01-04', window_end: '2013-01-04', peak_date: '2013-01-04',
      })
    )
    expect(d.is_timing_window).toBe(false)
    // Distinguishes "the chain clause correctly said no" from "some other
    // (e.g. duration-based) path granted true" -- the specific chain-basis
    // reason is the proof this went through the RIGHT gate.
    expect(d.timing_window_blocked_reason).toBe('chain_basis_not_declared')
    expect(d.resolution_source).toBe('not_hierarchy_classified')
  })

  it('test_ontology_milestone_offset_not_in_genuine_peak_bases: a chain row with GENUINE_PEAK_BASES member LAMBDA_V3_ARGMAX is NOT granted true via the resolution-tier clause -- proves the chain short-circuit fires before that clause is ever reached', () => {
    // If the chain short-circuit did NOT fire first, this row (resolution=
    // null) would fall through to the generic "resolution is NULL and not
    // point-shaped" branch and read 'resolution_unavailable' -- also false,
    // but via the WRONG reason. The chain-specific reason is the proof the
    // short-circuit is what actually fired.
    const d = deriveResolutionDisclosure(
      makeRow({
        temporal_shape: 'chain', resolution: null,
        peak_basis: LAMBDA_V3_ARGMAX, milestone_id: 'first_revenue',
      })
    )
    expect(d.timing_window_blocked_reason).toBe('chain_basis_not_declared')
    expect(d.timing_window_blocked_reason).not.toBe('resolution_unavailable')
  })
})

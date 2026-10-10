/**
 * register_gochara_windows_dens_served.test.ts — DENS-SERVED claims for the platform-mcp module that
 * `bg_remedies` Dens.served credits (CLAUDE.md §N.6).
 *
 * `gochara_election_avoidance_get` declares a `density_contract` (ELECTION_AVOIDANCE_DENSITY_CONTRACT) and, in the
 * same capability, pairs every adverse window with a remedy read from `brahma_remedy_corpus` whose SELECT carries
 * `confidence` (the remedy row's confidence tier). The platform-side dens_served_contracts.test.ts cannot import a
 * platform-mcp module, so this file is the claims test the census guard
 * (test_dens_served_review2.py::test_finding8) requires of every platform-mcp module that earns a PASS: it imports the
 * module by its relative path and checks the contract against the real compute function with a mocked platform DB
 * proxy (no database).
 */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { computeGocharaElectionAvoidance } from './register_gochara_windows.js'

const PRINCIPAL = { user_uid: 'test', key_id: 'test', role: 'super_admin' as const }
const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const MAIN_ROW_QUERY_SIGNATURE = 'id, chart_id, event_class, temporal_shape'

function fakeJsonResponse(rows: unknown[]): Response {
  return {
    ok: true,
    json: () => Promise.resolve({ rows }),
    text: () => Promise.resolve(JSON.stringify({ rows })),
  } as unknown as Response
}

const ADVERSE_ROW = {
  id: 1,
  chart_id: CHART_ID,
  event_class: 'marriage',
  temporal_shape: 'interval',
  milestone_id: null,
  is_irreversibility_milestone: false,
  signed_intensity: -0.7,
  raw_intensity: 0.7,
  valence: 'adverse',
  is_adverse: true,
  active_sentences: [],
  contributing_systems: [{ system_id: 'guru_shani_double_transit', active: true, detail: { lord_graha: 'Saturn' } }],
  suppression_state: {},
  calibration_state: 'structural_prior',
  source: 'live',
  computed_at: '2026-08-11T00:00:00Z',
  continuity_state: null,
  generation: '3.0',
  era_slice_key: 'g3_1984_1994',
  term_breakdown: null,
  parent_window_id: null,
  resolution: 'month',
  peak_basis: 'gochara_lambda_v3_argmax',
  window_start: '1984-02-15',
  window_end: '1984-03-15',
  peak_date: '1984-03-01',
}

const REMEDY_ROW = { remedy_id: 'r1', planet: 'saturn', remedy_type: 'mantra', prescription_text: 'x', source_citation: 'BPHS', confidence: 0.8 }

function mockPlatform(rows: Record<string, unknown>[], sqls: string[]) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation((_url, init) => {
    const { sql } = JSON.parse((init as RequestInit).body as string) as { sql: string }
    sqls.push(sql)
    if (sql.includes('FROM brahma_remedy_corpus')) return Promise.resolve(fakeJsonResponse([REMEDY_ROW]))
    if (sql.includes(MAIN_ROW_QUERY_SIGNATURE)) return Promise.resolve(fakeJsonResponse(rows))
    if (sql.includes('kala_gochara_authority')) return Promise.resolve(fakeJsonResponse([]))
    if (sql.includes('brahma_event_ontology')) return Promise.resolve(fakeJsonResponse([{ domain: 'marriage' }]))
    if (sql.includes('build_substep_progress')) return Promise.resolve(fakeJsonResponse([{ substeps_committed: 0, swept_event_classes: [] }]))
    return Promise.resolve(fakeJsonResponse([]))
  })
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('DENS-SERVED: gochara_election_avoidance_get layers its paired remedy by confidence', () => {
  it('the remedy SELECT names confidence and every adverse window serves the remedy row with its confidence', async () => {
    const sqls: string[] = []
    mockPlatform([ADVERSE_ROW], sqls)
    const result = (await computeGocharaElectionAvoidance(CHART_ID, { start: '1984-02-15', end: '1984-04-15' }, 'marriage', 10, PRINCIPAL)) as {
      windows: Array<{ mitigation: Record<string, unknown> }>
    }
    const remedySql = sqls.find((s) => s.includes('FROM brahma_remedy_corpus')) ?? ''
    expect(remedySql).toMatch(/SELECT[\s\S]*\bconfidence\b[\s\S]*FROM brahma_remedy_corpus/)
    expect(result.windows).toHaveLength(1)
    expect(result.windows[0]!.mitigation['confidence']).toBe(0.8)
  })

  it('declares its density_contract on every response: facets are the served facets keys, empty_reason is earned', async () => {
    const sqls: string[] = []
    mockPlatform([ADVERSE_ROW], sqls)
    const populated = (await computeGocharaElectionAvoidance(CHART_ID, { start: '1984-02-15', end: '1984-04-15' }, 'marriage', 10, PRINCIPAL)) as {
      facets: Record<string, unknown>
      provenance_envelope: { density_contract: { paginated: boolean; facets: string[]; empty_reason: boolean }; empty_reason: string | null }
    }
    const dc = populated.provenance_envelope.density_contract
    expect(dc.empty_reason).toBe(true)
    expect(dc.paginated).toBe(true)
    expect(dc.facets).toEqual(['event_class', 'temporal_shape', 'calibration_state', 'era_slice_key', 'resolution'])
    expect(populated.provenance_envelope.empty_reason).toBeNull()
    for (const f of ['calibration_state', 'era_slice_key']) expect(Object.keys(populated.facets)).toContain(f)

    vi.restoreAllMocks()
    mockPlatform([], [])
    const empty = (await computeGocharaElectionAvoidance(CHART_ID, { start: '1984-02-15', end: '1984-04-15' }, 'marriage', 10, PRINCIPAL)) as {
      provenance_envelope: { empty_reason: string | null }
    }
    expect(String(empty.provenance_envelope.empty_reason).length).toBeGreaterThan(10)
  })
})

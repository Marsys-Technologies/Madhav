/**
 * prospective_ledger.contact_id.test.ts — WP7 P-3 acceptance.
 *
 * DB client is mocked — no real Postgres (same convention as
 * prospective_ledger.test.ts). Coverage:
 *   1. An engine claim filed with a real fixture contact_id carries it on the
 *      returned row (INSERT receives it; the filing-time existence check ran).
 *   2. A tampered id (one hex char changed) is REJECTED — the contacts SELECT
 *      returns no row; a frozen claim pointing at a nonexistent episode is
 *      never stored (F-18 orphan class one layer up).
 *   3. A malformed id (not sha256:<64 hex>) is rejected before any SQL.
 *   4. A chart with NO kala_gochara_authority row rejects contact-anchored
 *      filings (N-10: unpublished, never a 'v1' default).
 *   5. A claim filed without contact_id (the migration-time backfill state,
 *      NULL) still files, lists, and outcome-matches unchanged.
 */

import { describe, it, expect, vi, beforeEach, type MockInstance } from 'vitest'

vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
vi.mock('../../lel/event_ontology_shapes', async () => {
  const actual = await vi.importActual<typeof import('../../lel/event_ontology_shapes')>(
    '../../lel/event_ontology_shapes'
  )
  return { ...actual, getEventClassOntology: vi.fn() }
})

import { query } from '@/lib/db/client'
import { getEventClassOntology } from '../../lel/event_ontology_shapes'
import {
  fileProspectivePrediction,
  listProspectivePredictions,
  matchOpenPredictionsForLelEvent,
  type ProspectiveLedgerRow,
} from '../../lel/prospective_ledger'

const mockQuery = query as unknown as MockInstance
const mockOntology = getEventClassOntology as unknown as MockInstance

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const CONTACT_ID = `sha256:${'a1b2c3d4'.repeat(8)}`

const POINT_ONTOLOGY = {
  event_class_id: 'achievement',
  temporal_shape: 'point' as const,
  duration_prior: null,
  milestone_template: null,
  irreversibility_milestone: null,
  evidence_requirements: { valence: 'gain' as const },
}

function baseInput(contact_id?: string) {
  return {
    chart_id: CHART,
    claim: 'A promotion lands on the flagged date.',
    event_class: 'achievement',
    claim_shape: 'point' as const,
    point_date: '2027-03-14',
    model: 'test-model',
    formula_version: 'test-1',
    confidence: 0.6,
    falsifier: 'No promotion within tolerance of the flagged date.',
    generator_class: 'reading_synthesis' as const,
    filed_by: 'wp7-p3-test',
    source_citation: 'WP7 P-3 acceptance fixture',
    ...(contact_id !== undefined ? { contact_id } : {}),
  }
}

function insertedRow(overrides: Partial<ProspectiveLedgerRow> = {}): ProspectiveLedgerRow {
  return {
    prediction_id: 'pred-1',
    chart_id: CHART,
    claim: 'A promotion lands on the flagged date.',
    event_class: 'achievement',
    claim_shape: 'point',
    observation_window: '[2027-03-14,2027-03-15)',
    milestone_set: null,
    model: 'test-model',
    formula_version: 'test-1',
    confidence: 0.6,
    falsifier: 'No promotion within tolerance of the flagged date.',
    as_of: '2026-09-24T00:00:00Z',
    generator_class: 'reading_synthesis',
    configuration_signature: null,
    contact_id: null,
    lifecycle_status: 'open',
    matched_event_id: null,
    matched_at: null,
    match_note: null,
    filed_by: 'wp7-p3-test',
    filing_method: 'explicit_filing_tool',
    source_citation: 'WP7 P-3 acceptance fixture',
    created_at: '2026-09-24T00:00:00Z',
    ...overrides,
  }
}

describe('fileProspectivePrediction — WP7 P-3 contact_id', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('files a claim with a real fixture contact_id and returns it on the row', async () => {
    mockOntology.mockResolvedValueOnce(POINT_ONTOLOGY)
    // filing-time existence check: authority row, then contacts hit
    mockQuery.mockResolvedValueOnce({ rows: [{ authoritative_generation: '4.0' }] })
    mockQuery.mockResolvedValueOnce({ rows: [{ contact_id: CONTACT_ID }] })
    mockQuery.mockResolvedValueOnce({ rows: [insertedRow({ contact_id: CONTACT_ID })] })

    const result = await fileProspectivePrediction(baseInput(CONTACT_ID))

    expect(result.row.contact_id).toBe(CONTACT_ID)
    // existence checked under the authoritative generation, no 'v1' fallback
    const [authSql] = mockQuery.mock.calls[0] as [string, unknown[]]
    expect(authSql).toContain('kala_gochara_authority')
    const [contactSql, contactParams] = mockQuery.mock.calls[1] as [string, unknown[]]
    expect(contactSql).toContain('kala_gochara_contacts')
    expect(contactParams).toEqual([CHART, '4.0', CONTACT_ID])
    // INSERT carried the id
    const [insertSql, insertParams] = mockQuery.mock.calls[2] as [string, unknown[]]
    expect(insertSql).toContain('contact_id')
    expect(insertParams[14]).toBe(CONTACT_ID)
  })

  it('rejects a tampered id (one hex char changed) — dangling ids are never stored', async () => {
    const tampered = `${CONTACT_ID.slice(0, -1)}${CONTACT_ID.endsWith('a') ? 'b' : 'a'}`
    mockOntology.mockResolvedValueOnce(POINT_ONTOLOGY)
    mockQuery.mockResolvedValueOnce({ rows: [{ authoritative_generation: '4.0' }] })
    mockQuery.mockResolvedValueOnce({ rows: [] }) // contacts SELECT: no such episode

    await expect(fileProspectivePrediction(baseInput(tampered))).rejects.toThrow(
      /does not resolve in kala_gochara_contacts/
    )
    // no INSERT was ever issued
    expect(mockQuery).toHaveBeenCalledTimes(2)
  })

  it('rejects a malformed id before any SQL is issued', async () => {
    mockOntology.mockResolvedValueOnce(POINT_ONTOLOGY)

    await expect(fileProspectivePrediction(baseInput('sha256:zzzz'))).rejects.toThrow(/malformed/)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it("rejects a contact-anchored filing when the chart has no authority row (N-10, never a 'v1' default)", async () => {
    mockOntology.mockResolvedValueOnce(POINT_ONTOLOGY)
    mockQuery.mockResolvedValueOnce({ rows: [] }) // no kala_gochara_authority row

    await expect(fileProspectivePrediction(baseInput(CONTACT_ID))).rejects.toThrow(
      /no kala_gochara_authority row/
    )
    expect(mockQuery).toHaveBeenCalledTimes(1)
  })

  it('a claim filed without contact_id (backfill-era NULL) still files, lists, and matches', async () => {
    mockOntology.mockResolvedValueOnce(POINT_ONTOLOGY)
    mockQuery.mockResolvedValueOnce({ rows: [insertedRow()] })

    const filed = await fileProspectivePrediction(baseInput())
    expect(filed.row.contact_id).toBeNull()
    // INSERT param 15 defaults NULL
    const [, insertParams] = mockQuery.mock.calls[0] as [string, unknown[]]
    expect(insertParams[14]).toBeNull()

    mockQuery.mockResolvedValueOnce({ rows: [insertedRow()] })
    const listed = await listProspectivePredictions(CHART)
    expect(listed.rows[0].contact_id).toBeNull()
    expect(mockQuery.mock.calls[1][0] as string).toContain('contact_id')

    // outcome matching untouched: the SELECT now carries contact_id, and a
    // within-tolerance event still matches a NULL-contact claim
    mockQuery.mockResolvedValueOnce({ rows: [insertedRow()] })
    mockQuery.mockResolvedValueOnce({ rows: [] }) // UPDATE
    const matches = await matchOpenPredictionsForLelEvent({
      chart_id: CHART,
      life_event_id: 'lel-p3-fixture',
      event_class: 'achievement',
      event_date: '2027-03-20',
      date_confidence: 'exact',
    })
    expect(matches).toHaveLength(1)
  })
})

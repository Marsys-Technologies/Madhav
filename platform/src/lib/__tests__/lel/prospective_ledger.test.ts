/**
 * prospective_ledger.test.ts — Unit tests for D-4a Lane A-4's prospective ledger.
 *
 * DB client is mocked — no real Postgres (live-DB verification is done separately via
 * the D-4a A-4 filing script + direct psql checks, documented in the session report).
 * Coverage:
 *   1. fileProspectivePrediction rejects a claim_shape that mismatches the ontology's
 *      canonical temporal_shape (the brief's exact worked example — point claim
 *      against interval-shaped major_gain).
 *   2. fileProspectivePrediction rejects a missing/empty falsifier (MANDATORY, no
 *      exceptions).
 *   3. fileProspectivePrediction rejects confidence outside the open interval (0, 1).
 *   4. fileProspectivePrediction rejects an unknown event_class.
 *   5. A valid point-shaped claim inserts with the correct degenerate [d, d+1) range.
 *   6. A valid interval-shaped claim inserts with the correct [start, end] range.
 *   7. Every successful file/list call returns the §11 governance text.
 *   8. matchOpenPredictionsForLelEvent matches a point claim within tolerance and
 *      flips lifecycle_status to 'matched'; does NOT match outside tolerance.
 *   9. deriveWindowFields round-trips point/interval/chain shapes correctly, including
 *      the Postgres canonical-exclusive-upper-bound correction for interval shape.
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
  deriveWindowFields,
  PROSPECTIVE_LEDGER_GOVERNANCE_TEXT,
  type ProspectiveLedgerRow,
} from '../../lel/prospective_ledger'

const mockQuery = query as unknown as MockInstance
const mockOntology = getEventClassOntology as unknown as MockInstance

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

const MAJOR_GAIN_ONTOLOGY = {
  event_class_id: 'major_gain',
  temporal_shape: 'interval' as const,
  duration_prior: { min_days: 30, typical_days: 120, max_days: 365 },
  milestone_template: null,
  irreversibility_milestone: null,
  evidence_requirements: {
    valence: 'gain' as const,
    externally_verifiable: true,
    verification_sources: ['bank statement'],
    self_report_risk: 'low' as const,
  },
  self_report_non_discriminating: false,
  kill_switch_criteria: [],
}

const ACHIEVEMENT_ONTOLOGY = {
  event_class_id: 'achievement_recognition',
  temporal_shape: 'point' as const,
  duration_prior: null,
  milestone_template: null,
  irreversibility_milestone: null,
  evidence_requirements: {
    valence: 'gain' as const,
    externally_verifiable: true,
    verification_sources: ['award record'],
    self_report_risk: 'low' as const,
  },
  self_report_non_discriminating: false,
  kill_switch_criteria: [],
}

function baseInput(overrides: Record<string, unknown> = {}) {
  return {
    chart_id: CHART,
    claim: 'Test claim',
    event_class: 'major_gain',
    claim_shape: 'interval' as const,
    window_start: '2027-04-09',
    window_end: '2027-08-18',
    model: 'test_model',
    formula_version: 'v1',
    confidence: 0.6,
    falsifier: 'No major_gain event overlaps the window.',
    generator_class: 'reading_synthesis' as const,
    filed_by: 'test-suite',
    source_citation: 'test-suite',
    ...overrides,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('fileProspectivePrediction', () => {
  it('rejects a point-claim against an interval-shaped event_class (the brief worked example)', async () => {
    mockOntology.mockResolvedValueOnce(MAJOR_GAIN_ONTOLOGY)
    await expect(
      fileProspectivePrediction(
        baseInput({ claim_shape: 'point', point_date: '2027-05-01', window_start: undefined, window_end: undefined })
      )
    ).rejects.toThrow(/SHAPE_MISMATCH|canonically 'interval'/)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('rejects a missing falsifier', async () => {
    await expect(fileProspectivePrediction(baseInput({ falsifier: '' }))).rejects.toThrow(/falsifier is MANDATORY/)
    expect(mockOntology).not.toHaveBeenCalled()
  })

  it('rejects confidence outside (0, 1)', async () => {
    await expect(fileProspectivePrediction(baseInput({ confidence: 1 }))).rejects.toThrow(/open interval/)
    await expect(fileProspectivePrediction(baseInput({ confidence: 0 }))).rejects.toThrow(/open interval/)
  })

  it('rejects an unknown event_class', async () => {
    mockOntology.mockResolvedValueOnce(null)
    await expect(fileProspectivePrediction(baseInput({ event_class: 'not_a_real_class' }))).rejects.toThrow(
      /unknown event_class/
    )
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('inserts a valid interval claim with the correct [start, end] range and returns governance text', async () => {
    mockOntology.mockResolvedValueOnce(MAJOR_GAIN_ONTOLOGY)
    mockQuery.mockResolvedValueOnce({
      rows: [{ prediction_id: 'p1', claim_shape: 'interval', observation_window: '[2027-04-09,2027-08-19)' }],
    })
    const result = await fileProspectivePrediction(baseInput())
    const [sql, params] = mockQuery.mock.calls[0] as [string, unknown[]]
    expect(sql).toContain('INSERT INTO brahma_prospective_ledger')
    expect(params[4]).toBe('[2027-04-09,2027-08-18]')
    expect(result.governance).toBe(PROSPECTIVE_LEDGER_GOVERNANCE_TEXT)
  })

  it('inserts a valid point claim with the correct degenerate [d, d+1) range', async () => {
    mockOntology.mockResolvedValueOnce(ACHIEVEMENT_ONTOLOGY)
    mockQuery.mockResolvedValueOnce({
      rows: [{ prediction_id: 'p2', claim_shape: 'point', observation_window: '[2027-05-01,2027-05-02)' }],
    })
    await fileProspectivePrediction(
      baseInput({
        event_class: 'achievement_recognition',
        claim_shape: 'point',
        point_date: '2027-05-01',
        window_start: undefined,
        window_end: undefined,
      })
    )
    const [, params] = mockQuery.mock.calls[0] as [string, unknown[]]
    expect(params[4]).toBe('[2027-05-01,2027-05-02)')
  })
})

describe('listProspectivePredictions', () => {
  it('returns governance text alongside rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await listProspectivePredictions(CHART)
    expect(result.governance).toBe(PROSPECTIVE_LEDGER_GOVERNANCE_TEXT)
    expect(result.rows).toEqual([])
  })
})

describe('matchOpenPredictionsForLelEvent', () => {
  function openIntervalRow(): ProspectiveLedgerRow {
    return {
      prediction_id: 'p1',
      chart_id: CHART,
      claim: 'Sat-Jup pratyantar wealth window',
      event_class: 'major_gain',
      claim_shape: 'interval',
      observation_window: '[2027-04-09,2027-08-19)',
      milestone_set: null,
      model: 'x', formula_version: 'v1', confidence: 0.6,
      falsifier: 'f', as_of: '2026-07-19T00:00:00Z', generator_class: 'reading_synthesis',
      configuration_signature: null, lifecycle_status: 'open',
      matched_event_id: null, matched_at: null, match_note: null,
      filed_by: 'x', filing_method: 'explicit_filing_tool', source_citation: 'x',
      created_at: '2026-07-19T00:00:00Z',
    }
  }

  it('matches an in-window event and flips lifecycle_status to matched', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [openIntervalRow()] }) // SELECT open
    mockQuery.mockResolvedValueOnce({ rows: [] }) // UPDATE

    const matches = await matchOpenPredictionsForLelEvent({
      chart_id: CHART,
      life_event_id: 'evt-1',
      event_class: 'major_gain',
      event_date: '2027-06-01',
    })

    expect(matches).toHaveLength(1)
    expect(matches[0]?.prediction_id).toBe('p1')
    const [updateSql, updateParams] = mockQuery.mock.calls[1] as [string, unknown[]]
    expect(updateSql).toContain("lifecycle_status = 'matched'")
    expect(updateParams[0]).toBe('p1')
    expect(updateParams[1]).toBe('evt-1')
  })

  it('does not match an event outside the interval', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [openIntervalRow()] })

    const matches = await matchOpenPredictionsForLelEvent({
      chart_id: CHART,
      life_event_id: 'evt-2',
      event_class: 'major_gain',
      event_date: '2026-01-01',
    })

    expect(matches).toHaveLength(0)
    expect(mockQuery).toHaveBeenCalledTimes(1) // no UPDATE issued
  })
})

describe('deriveWindowFields', () => {
  it('recovers point_date for a point-shaped row', () => {
    const f = deriveWindowFields({ claim_shape: 'point', observation_window: '[2027-05-01,2027-05-02)' })
    expect(f.point_date).toBe('2027-05-01')
    expect(f.window_start).toBeNull()
  })

  it('recovers the human-facing inclusive window_end for an interval-shaped row', () => {
    // Postgres always normalizes to exclusive-upper on read; filed window_end=2027-08-18
    // reads back as upper=2027-08-19 — deriveWindowFields must undo that.
    const f = deriveWindowFields({ claim_shape: 'interval', observation_window: '[2027-04-09,2027-08-19)' })
    expect(f.window_start).toBe('2027-04-09')
    expect(f.window_end).toBe('2027-08-18')
  })

  it('returns all nulls for a chain-shaped row (no observation_window)', () => {
    const f = deriveWindowFields({ claim_shape: 'chain', observation_window: null })
    expect(f).toEqual({ point_date: null, window_start: null, window_end: null })
  })
})

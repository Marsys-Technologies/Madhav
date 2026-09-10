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
  computeConfigurationSignature,
  isAdverseEventClass,
  assertDr16AdverseDisclosure,
  Dr16DisclosureError,
  PROSPECTIVE_LEDGER_GOVERNANCE_TEXT,
  type ProspectiveLedgerRow,
  type Dr16AdverseDisclosure,
  type EngineConfigurationSource,
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

const MAJOR_LOSS_ONTOLOGY = {
  event_class_id: 'major_loss',
  temporal_shape: 'interval' as const,
  duration_prior: { min_days: 30, typical_days: 120, max_days: 365 },
  milestone_template: null,
  irreversibility_milestone: null,
  evidence_requirements: {
    valence: 'loss' as const,
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

// ── D-5 Lane G-5 — engine claims, configuration_signature, DR-16 gate ────────────

function engineSource(overrides: Partial<EngineConfigurationSource> = {}): EngineConfigurationSource {
  return {
    chart_id: CHART,
    event_class: 'major_loss',
    temporal_shape: 'interval',
    window_start: '2027-04-09',
    window_end: '2027-08-18',
    peak_date: '2027-06-01',
    peak_basis: 'gochara_lambda_e_v1',
    active_sentences: [{ fact_ids: ['fact-1', 'fact-2'] }, { fact_ids: ['fact-3'] }],
    contributing_systems: [{ system_id: 'vimshottari' }, { system_id: 'guru_shani_double_transit' }],
    ...overrides,
  }
}

function fullDr16Disclosure(overrides: Partial<Dr16AdverseDisclosure> = {}): Dr16AdverseDisclosure {
  return {
    honest_clarity: {
      domain: 'wealth',
      window_description: '2027-04-09 to 2027-08-18',
      mechanism: 'Guru-Śani double-transit afflicting the 2nd/11th axis while Vimśottarī sub-lord is weak.',
    },
    probabilistic_framing: {
      hazard_statement:
        'Finance-domain loss-risk is elevated in this window; this chart has fired this configuration 2 times before.',
    },
    mitigation: {
      suppression_analysis: { n_vedha_cancelled: 0, n_kartari_pincer: 1, calibration_state: 'structural_prior' },
      remedy_pointer: {
        instrument: 'bodha_remedies_get',
        params: { chart_id: CHART, graha: 'Saturn' },
        hint: 'Query bodha_remedies_get filtered to graha=Saturn for BPHS-cited remedy prescriptions.',
      },
    },
    confidence_disclosure: {
      calibration_state: 'structural_prior',
      n_observations: 2,
      control_delta: null,
    },
    ...overrides,
  }
}

describe('computeConfigurationSignature', () => {
  it('is deterministic — the same source produces the same signature', () => {
    const s1 = computeConfigurationSignature(engineSource())
    const s2 = computeConfigurationSignature(engineSource())
    expect(s1).toBe(s2)
  })

  it('is order-independent over fact_ids / contributing_systems (reproducibility)', () => {
    const s1 = computeConfigurationSignature(
      engineSource({
        active_sentences: [{ fact_ids: ['fact-1', 'fact-2'] }, { fact_ids: ['fact-3'] }],
        contributing_systems: [{ system_id: 'vimshottari' }, { system_id: 'guru_shani_double_transit' }],
      })
    )
    const s2 = computeConfigurationSignature(
      engineSource({
        active_sentences: [{ fact_ids: ['fact-3'] }, { fact_ids: ['fact-2', 'fact-1'] }],
        contributing_systems: [{ system_id: 'guru_shani_double_transit' }, { system_id: 'vimshottari' }],
      })
    )
    expect(s1).toBe(s2)
  })

  it('changes when the underlying configuration changes (a different fact_id set)', () => {
    const s1 = computeConfigurationSignature(engineSource())
    const s2 = computeConfigurationSignature(engineSource({ active_sentences: [{ fact_ids: ['fact-9'] }] }))
    expect(s1).not.toBe(s2)
  })

  it('prefixes the signature with peak_basis for human-legible provenance', () => {
    const s = computeConfigurationSignature(engineSource({ peak_basis: 'gochara_lambda_e_v1' }))
    expect(s.startsWith('gochara_lambda_e_v1:')).toBe(true)
  })
})

describe('isAdverseEventClass', () => {
  it('treats loss-valence classes as adverse', () => {
    expect(isAdverseEventClass(MAJOR_LOSS_ONTOLOGY)).toBe(true)
  })

  it('treats gain/neutral-valence classes as non-adverse', () => {
    expect(isAdverseEventClass(MAJOR_GAIN_ONTOLOGY)).toBe(false)
    expect(isAdverseEventClass(ACHIEVEMENT_ONTOLOGY)).toBe(false)
  })

  it('overrides psychological_arc (mixed-valence) to adverse per the brief\'s named specimen', () => {
    expect(
      isAdverseEventClass({
        event_class_id: 'psychological_arc',
        evidence_requirements: { ...MAJOR_GAIN_ONTOLOGY.evidence_requirements, valence: 'mixed' },
      })
    ).toBe(true)
  })
})

describe('fileProspectivePrediction — generator_class=engine + configuration_signature', () => {
  it('rejects an engine claim with no configuration_signature', async () => {
    mockOntology.mockResolvedValueOnce(MAJOR_GAIN_ONTOLOGY)
    await expect(
      fileProspectivePrediction(
        baseInput({ generator_class: 'engine', configuration_signature: null })
      )
    ).rejects.toThrow(/configuration_signature/)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('accepts a non-adverse engine claim with a populated configuration_signature', async () => {
    mockOntology.mockResolvedValueOnce(MAJOR_GAIN_ONTOLOGY)
    const signature = computeConfigurationSignature(engineSource({ event_class: 'major_gain', temporal_shape: 'interval' }))
    mockQuery.mockResolvedValueOnce({
      rows: [{ prediction_id: 'p3', claim_shape: 'interval', observation_window: '[2027-04-09,2027-08-19)', configuration_signature: signature }],
    })
    const result = await fileProspectivePrediction(
      baseInput({ generator_class: 'engine', configuration_signature: signature })
    )
    const [, params] = mockQuery.mock.calls[0] as [string, unknown[]]
    expect(params[10]).toBe('engine') // generator_class
    expect(params[11]).toBe(signature) // configuration_signature
    expect(result.dr16_disclosure).toBeUndefined()
  })
})

describe('fileProspectivePrediction — DR-16 adverse-claim gate (hard acceptance item)', () => {
  const signature = computeConfigurationSignature(engineSource())

  function adverseInput(overrides: Record<string, unknown> = {}) {
    return baseInput({
      event_class: 'major_loss',
      generator_class: 'engine',
      configuration_signature: signature,
      claim: 'Elevated finance-domain loss-risk window.',
      dr16_adverse_disclosure: fullDr16Disclosure(),
      ...overrides,
    })
  }

  it('accepts a complete adverse engine claim carrying all 5 DR-16 properties', async () => {
    mockOntology.mockResolvedValueOnce(MAJOR_LOSS_ONTOLOGY)
    mockQuery.mockResolvedValueOnce({
      rows: [{ prediction_id: 'p4', claim_shape: 'interval', observation_window: '[2027-04-09,2027-08-19)' }],
    })
    const result = await fileProspectivePrediction(adverseInput())
    expect(mockQuery).toHaveBeenCalledTimes(1)
    expect(result.dr16_disclosure).toBeDefined()
    expect(result.dr16_disclosure?.confidence_disclosure.calibration_state).toBe('structural_prior')
  })

  it('REJECTS an adverse engine claim with no disclosure at all', async () => {
    mockOntology.mockResolvedValueOnce(MAJOR_LOSS_ONTOLOGY)
    await expect(
      fileProspectivePrediction(adverseInput({ dr16_adverse_disclosure: undefined }))
    ).rejects.toThrow(Dr16DisclosureError)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('REJECTS when honest_clarity (property 1) is missing a required field', async () => {
    mockOntology.mockResolvedValueOnce(MAJOR_LOSS_ONTOLOGY)
    const disclosure = fullDr16Disclosure({ honest_clarity: { domain: 'wealth', window_description: '', mechanism: 'x' } })
    await expect(fileProspectivePrediction(adverseInput({ dr16_adverse_disclosure: disclosure }))).rejects.toThrow(
      /DR-16\(1\)/
    )
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('REJECTS when probabilistic_framing (property 2) is missing', async () => {
    mockOntology.mockResolvedValueOnce(MAJOR_LOSS_ONTOLOGY)
    const disclosure = fullDr16Disclosure({ probabilistic_framing: { hazard_statement: '' } })
    await expect(fileProspectivePrediction(adverseInput({ dr16_adverse_disclosure: disclosure }))).rejects.toThrow(
      /DR-16\(2\)/
    )
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('REJECTS fatalistic/doom language even when the field is non-empty (property 2)', async () => {
    mockOntology.mockResolvedValueOnce(MAJOR_LOSS_ONTOLOGY)
    const disclosure = fullDr16Disclosure({
      probabilistic_framing: { hazard_statement: 'This window is a guaranteed financial ruin for the native.' },
    })
    await expect(fileProspectivePrediction(adverseInput({ dr16_adverse_disclosure: disclosure }))).rejects.toThrow(
      /DR-16\(2\)/
    )
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('REJECTS an adverse claim with an empty falsifier (property 3)', async () => {
    mockOntology.mockResolvedValueOnce(MAJOR_LOSS_ONTOLOGY)
    // falsifier is checked earlier by fileProspectivePrediction's own mandatory-falsifier
    // guard (before ontology lookup even runs) — confirms DR-16(3) never actually gets a
    // chance to see an adverse claim without one.
    await expect(fileProspectivePrediction(adverseInput({ falsifier: '' }))).rejects.toThrow(/falsifier is MANDATORY/)
    expect(mockOntology).not.toHaveBeenCalled()
  })

  it('REJECTS when mitigation.suppression_analysis (property 4) is missing', async () => {
    mockOntology.mockResolvedValueOnce(MAJOR_LOSS_ONTOLOGY)
    const disclosure = fullDr16Disclosure({
      mitigation: { suppression_analysis: {}, remedy_pointer: fullDr16Disclosure().mitigation.remedy_pointer },
    })
    await expect(fileProspectivePrediction(adverseInput({ dr16_adverse_disclosure: disclosure }))).rejects.toThrow(
      /DR-16\(4\)/
    )
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('REJECTS when mitigation.remedy_pointer (property 4) is missing', async () => {
    mockOntology.mockResolvedValueOnce(MAJOR_LOSS_ONTOLOGY)
    const disclosure = fullDr16Disclosure({
      mitigation: {
        suppression_analysis: fullDr16Disclosure().mitigation.suppression_analysis,
        remedy_pointer: { instrument: '', hint: '' },
      },
    })
    await expect(fileProspectivePrediction(adverseInput({ dr16_adverse_disclosure: disclosure }))).rejects.toThrow(
      /DR-16\(4\)/
    )
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('REJECTS when confidence_disclosure (property 5) omits a required key', async () => {
    mockOntology.mockResolvedValueOnce(MAJOR_LOSS_ONTOLOGY)
    const { calibration_state } = fullDr16Disclosure().confidence_disclosure
    const disclosure = {
      ...fullDr16Disclosure(),
      confidence_disclosure: { calibration_state } as unknown as Dr16AdverseDisclosure['confidence_disclosure'],
    }
    await expect(fileProspectivePrediction(adverseInput({ dr16_adverse_disclosure: disclosure }))).rejects.toThrow(
      /DR-16\(5\)/
    )
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('ACCEPTS confidence_disclosure with n_observations/control_delta explicitly null (honest absence)', async () => {
    mockOntology.mockResolvedValueOnce(MAJOR_LOSS_ONTOLOGY)
    mockQuery.mockResolvedValueOnce({
      rows: [{ prediction_id: 'p5', claim_shape: 'interval', observation_window: '[2027-04-09,2027-08-19)' }],
    })
    const disclosure = fullDr16Disclosure({
      confidence_disclosure: { calibration_state: 'structural_prior', n_observations: null, control_delta: null },
    })
    const result = await fileProspectivePrediction(adverseInput({ dr16_adverse_disclosure: disclosure }))
    expect(result.dr16_disclosure?.confidence_disclosure.n_observations).toBeNull()
  })

  it('does NOT require DR-16 disclosure for a non-engine adverse claim (e.g. reading_synthesis)', async () => {
    mockOntology.mockResolvedValueOnce(MAJOR_LOSS_ONTOLOGY)
    mockQuery.mockResolvedValueOnce({
      rows: [{ prediction_id: 'p6', claim_shape: 'interval', observation_window: '[2027-04-09,2027-08-19)' }],
    })
    const result = await fileProspectivePrediction(
      baseInput({ event_class: 'major_loss', generator_class: 'reading_synthesis' })
    )
    expect(mockQuery).toHaveBeenCalledTimes(1)
    expect(result.dr16_disclosure).toBeUndefined()
  })
})

describe('assertDr16AdverseDisclosure (direct unit coverage)', () => {
  it('accepts a fully-formed disclosure', () => {
    expect(() => assertDr16AdverseDisclosure('A falsifier.', fullDr16Disclosure())).not.toThrow()
  })

  it('throws Dr16DisclosureError, not a generic Error, on any violation', () => {
    expect(() => assertDr16AdverseDisclosure('A falsifier.', null)).toThrow(Dr16DisclosureError)
  })
})

// ── PARIPŪRṆA audit fix (2026-08-15) — Postgres EMPTY daterange literal ──────────
// LIVE DEFECT: standing_predictions_read returned
//   "Error: parseDaterange: could not parse daterange literal 'empty'"
// for the canonical chart — a total tool failure on the DEFAULT (status=open) call,
// because 6 brahma_prospective_ledger rows carry observation_window='empty' with
// claim_shape='interval' and lifecycle_status='open'. `empty` is a LEGAL Postgres
// daterange literal; the parser simply never handled it. Semantics: empty window ==
// no window (null derived dates, matches nothing) — never an exception.
describe('deriveWindowFields — Postgres EMPTY daterange (PARIPŪRṆA Tier-1 crash fix)', () => {
  it('does not throw on the empty literal', () => {
    expect(() =>
      deriveWindowFields({ claim_shape: 'interval', observation_window: 'empty' })
    ).not.toThrow()
  })

  it('treats an empty window exactly like a missing window (all null)', () => {
    expect(
      deriveWindowFields({ claim_shape: 'interval', observation_window: 'empty' })
    ).toEqual({ point_date: null, window_start: null, window_end: null })
  })

  it('still parses a normal interval literal (no regression)', () => {
    expect(
      deriveWindowFields({ claim_shape: 'interval', observation_window: '[2027-04-09,2027-08-19)' })
    ).toEqual({ point_date: null, window_start: '2027-04-09', window_end: '2027-08-18' })
  })

  it('still parses a normal point literal (no regression)', () => {
    expect(
      deriveWindowFields({ claim_shape: 'point', observation_window: '[2027-05-01,2027-05-02)' })
    ).toEqual({ point_date: '2027-05-01', window_start: null, window_end: null })
  })
})

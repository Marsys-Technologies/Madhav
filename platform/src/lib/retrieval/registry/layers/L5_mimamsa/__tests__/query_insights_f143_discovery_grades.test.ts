/**
 * F-143 — the discovery-grade tiers must survive the serving layer.
 *
 * mi_darshana used to grade every mimamsa_discoveries row `n_support >= 5 ? 'empirical'
 * : 'prior_only'`, reading an attribution-ASSIGNMENT count as scored evidence. The fix
 * demotes those rows to 'assignment_only' (and grades retrodiction rows 'structural'),
 * which means two things this serving layer had never had to handle: a tier it does not
 * recognise as calibrated must fail closed, AND the tier must stay legible to the caller
 * instead of collapsing into an undifferentiated "not empirical".
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { queryInsightsCapability, EVIDENCE_GRADE_LEGEND, redactEmbeddedNumericEvidence } from '../query_insights'

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function discoveryRow(overrides: Record<string, unknown>) {
  return {
    insight_id: 'disc_sig1_timing', insight_type: 'emergent_law', domain: null,
    statement: "Signal 'sig1' shows consistent timing-dimension credit (mean credit=0.27 across 41 attribution assignments over 20 prediction-event matches, 2 of them outcome-adjudicated). Candidate emergent calibration law.",
    rank_consequence: 0.27, confidence_band: '[0.12,0.42)', n_support: 41,
    is_negative_knowledge: false,
    provenance_chain: { discovery_id: 'disc_sig1_timing', discovery_class: 'emergent_law', grade_basis: { rule: 'scored_matches_threshold', n_support: 41, n_scored_matches: 2 } },
    ...overrides,
  }
}

async function run(rows: Array<Record<string, unknown>>) {
  queryMock.mockResolvedValueOnce({ rows })
  queryMock.mockResolvedValueOnce({ rows: [{}] })
  return await queryInsightsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
    content: {
      insight_units: Array<Record<string, unknown>>
      evidence_grade_counts: Record<string, number>
      evidence_grade_legend: Record<string, string>
    }
  }
}

describe('query_insights — F-143 discovery evidence tiers', () => {
  beforeEach(() => queryMock.mockReset())
  afterEach(() => vi.restoreAllMocks())

  it("'assignment_only' fails closed: numerics suppressed, tier still served verbatim", async () => {
    const result = await run([discoveryRow({ evidence_grade: 'assignment_only' })])
    const unit = result.content.insight_units[0]
    expect(unit.evidence_grade).toBe('assignment_only')
    expect(unit.rank_consequence).toBeNull()
    expect(unit.confidence_band).toBeNull()
    expect(String(unit.tier_suppression_note)).toMatch(/assignment_only/)
  })

  it('the demoted discovery statement no longer leaks its mean-credit citation', async () => {
    const result = await run([discoveryRow({ evidence_grade: 'assignment_only' })])
    const statement = String(result.content.insight_units[0].statement)
    expect(statement).not.toMatch(/mean credit=0\.27/)
    expect(statement).toMatch(/suppressed/)
    // The counts themselves are not a suppressed confidence value — they are the honest
    // disclosure of what the row rests on, and must survive.
    expect(statement).toMatch(/41 attribution assignments/)
    expect(statement).toMatch(/2 of them outcome-adjudicated/)
  })

  it('the pre-v2.1 statement shape still in prod rows is redacted too', () => {
    const legacy = "Signal 'sig1' shows consistent timing-dimension credit (mean=0.27, n=41). Candidate emergent calibration law."
    expect(redactEmbeddedNumericEvidence(legacy)).not.toMatch(/0\.27/)
  })

  it('grade_basis survives suppression — the reason for the tier stays auditable', async () => {
    const result = await run([discoveryRow({ evidence_grade: 'assignment_only' })])
    const pc = result.content.insight_units[0].provenance_chain as Record<string, unknown>
    expect((pc.grade_basis as Record<string, unknown>).n_scored_matches).toBe(2)
    expect(pc.grade).toBeNull()
  })

  it('retrodiction rows serve as structural, suppressed, and legible', async () => {
    const result = await run([discoveryRow({
      insight_id: 'disc_retro_ev1', insight_type: 'retrodiction', evidence_grade: 'structural',
      n_support: 3, statement: 'Retrodiction probe for ev1 (career): 3 pre-existing career anchor(s) had opened on or before the event date. NOT a blind backtest — the declared T−90d cutoff (2019-10-03) is not applied as a filter and an anchor match is not an adjudicated hit.',
    })])
    const unit = result.content.insight_units[0]
    expect(unit.evidence_grade).toBe('structural')
    expect(unit.rank_consequence).toBeNull()
    expect(result.content.evidence_grade_legend.structural).toMatch(/not a scored hit/)
  })

  it('legend covers exactly the tiers present — never implies an absent one', async () => {
    const result = await run([
      discoveryRow({ evidence_grade: 'assignment_only' }),
      discoveryRow({ insight_id: 'd2', evidence_grade: 'structural' }),
    ])
    expect(result.content.evidence_grade_counts).toEqual({ assignment_only: 1, structural: 1 })
    expect(Object.keys(result.content.evidence_grade_legend).sort()).toEqual(['assignment_only', 'structural'])
    expect(result.content.evidence_grade_legend.assignment_only).toMatch(/Not evidence of accuracy/)
  })

  it('an unrecognised tier gets a fail-closed legend entry rather than silence', async () => {
    const result = await run([discoveryRow({ evidence_grade: 'some_future_tier' })])
    expect(result.content.evidence_grade_legend.some_future_tier).toMatch(/fail-closed/)
    expect(result.content.insight_units[0].rank_consequence).toBeNull()
  })

  it("'empirical' is still reachable and still passes through unsuppressed", async () => {
    const result = await run([discoveryRow({
      evidence_grade: 'empirical',
      provenance_chain: { grade_basis: { rule: 'scored_matches_threshold', n_scored_matches: 6 } },
    })])
    const unit = result.content.insight_units[0]
    expect(unit.rank_consequence).toBe(0.27)
    expect(unit.tier_suppression_note).toBeUndefined()
    expect(String(unit.statement)).toMatch(/mean credit=0\.27/)
    expect(EVIDENCE_GRADE_LEGEND.empirical).toMatch(/outcome-adjudicated/)
  })
})

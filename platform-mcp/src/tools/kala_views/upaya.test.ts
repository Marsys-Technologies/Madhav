/**
 * upaya.test.ts — ṢAḌ-DARŚANA W4 Lane U: `kala_upaya_get` (item 26 UPĀYA-SETU, full).
 * Covers: the mortality-exclusion rail fires FIRST and short-circuits completely (gate G16,
 * including the blanket source-scan of this production surface — a rail with no proof it can
 * fire is null, CLAUDE.md §N.8), envelope well-formedness, tri-plane honesty, the three
 * coverage concepts kept verbatim, the §N.6 cited/uncited density split, and the filing-state
 * machine's honest degradation while Lane S's spine has not landed.
 */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../../types.js'
import { isNoLever } from '../../lib/kala_envelope.js'
import { MORTALITY_FORBIDDEN_IDENTIFIER_PATTERN } from '../../lib/kala_upaya_diagnosis.js'

const mockCallPlatformPrimitive = vi.fn()
const mockCallPlatformWrites = vi.fn()
vi.mock('../../client.js', async () => {
  const actual = await vi.importActual<typeof import('../../client.js')>('../../client.js')
  return {
    ...actual,
    callPlatformPrimitive: (...args: unknown[]) => mockCallPlatformPrimitive(...args),
    callPlatformWrites: (...args: unknown[]) => mockCallPlatformWrites(...args),
  }
})

const mockCallKalaRegistryCap = vi.fn()
vi.mock('./shared.js', async () => {
  const actual = await vi.importActual<typeof import('./shared.js')>('./shared.js')
  return { ...actual, callKalaRegistryCap: (...args: unknown[]) => mockCallKalaRegistryCap(...args) }
})

import { buildKalaUpayaReading, buildKalaUpayaResult, isMortalityRefusal, type KalaUpayaResponse } from './upaya.js'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }

describe('buildKalaUpayaReading', () => {
  it('is a well-formed argument reading citing the diagnosis when present', () => {
    const reading = buildKalaUpayaReading({
      chart_id: CHART_ID,
      diagnosis: {
        pact_status: 'denied_at_promise', failing_link: 'promise', statement: 'the promise is weak',
        authority_basis: 'pact_query:denied_at_promise', targeted_graha: 'Saturn', fact_ids: ['f1'],
      },
      diagnosisReason: null,
      interventions: [],
    })
    expect(reading.thesis).toContain(CHART_ID)
    expect(reading.thesis).toContain('the promise is weak')
    expect(reading.verdict.statement.length).toBeGreaterThan(0)
    expect(reading.evidence[0]?.fact_ids).toEqual(['f1'])
  })

  it('is honest when no diagnosis could be computed (never fabricates one)', () => {
    const reading = buildKalaUpayaReading({
      chart_id: CHART_ID, diagnosis: null, diagnosisReason: 'no domain/bhava supplied', interventions: [],
    })
    expect(reading.thesis).toContain('could not diagnose')
    expect(reading.thesis).toContain('no domain/bhava supplied')
    expect(reading.falsifier).toBeNull()
  })
})

// ══════════════════════════════════════════════════════════════════════════════════════════
// Gate G16 — the individualized-mortality-window hard exclusion, the FIRST thing this tool does
// ══════════════════════════════════════════════════════════════════════════════════════════

describe('buildKalaUpayaResult — mortality exclusion (gate G16, fires FIRST, non-vacuous)', () => {
  beforeEach(() => {
    mockCallPlatformPrimitive.mockReset()
    mockCallKalaRegistryCap.mockReset()
  })

  it('refuses a mortality-shaped request with no network call of any kind', async () => {
    const result = await buildKalaUpayaResult(
      { chart_id: CHART_ID, question_frame: { domain: 'longevity' } }, PRINCIPAL,
    )
    expect(isMortalityRefusal(result)).toBe(true)
    if (isMortalityRefusal(result)) {
      expect(result.excluded).toBe(true)
      expect(result.exclusion).toBe('individualized_mortality_window')
    }
    // The FIRING PROOF: no substrate call happened at all — the detector short-circuited
    // before pact_query, before remedy sourcing, before alternate-route search.
    expect(mockCallPlatformPrimitive).not.toHaveBeenCalled()
    expect(mockCallKalaRegistryCap).not.toHaveBeenCalled()
  })

  it('refuses via event_class naming maraka, even with a benign question_frame', async () => {
    const result = await buildKalaUpayaResult(
      { chart_id: CHART_ID, event_class: 'maraka_dasha_concern', question_frame: { domain: 'career' } }, PRINCIPAL,
    )
    expect(isMortalityRefusal(result)).toBe(true)
    expect(mockCallPlatformPrimitive).not.toHaveBeenCalled()
  })

  it('G16(c): still refuses on both canonical charts (native_self does not unlock it)', async () => {
    for (const chartId of [CHART_ID, ABHINANDAN_CHART_ID]) {
      const result = await buildKalaUpayaResult(
        { chart_id: chartId, question_frame: { stakes: 'worried about ayurdaya' } }, PRINCIPAL,
      )
      expect(isMortalityRefusal(result)).toBe(true)
    }
  })

  it('carries no diagnosis/interventions/coverage field of any kind on refusal', async () => {
    const result = await buildKalaUpayaResult(
      { chart_id: CHART_ID, event_class: 'longevity' }, PRINCIPAL,
    )
    expect(isMortalityRefusal(result)).toBe(true)
    const keys = Object.keys(result)
    expect(keys).not.toContain('diagnosis')
    expect(keys).not.toContain('interventions')
    expect(keys).not.toContain('coverage')
  })

  it('does NOT refuse an ordinary career/health remedy request', async () => {
    mockCallKalaRegistryCap.mockResolvedValue({ content: { error: 'no pact_query fixture in this test' }, is_error: true })
    mockCallPlatformPrimitive.mockRejectedValue(new Error('unreachable in unit test'))
    const result = await buildKalaUpayaResult(
      { chart_id: CHART_ID, domain: 'career' }, PRINCIPAL,
    )
    expect(isMortalityRefusal(result)).toBe(false)
  })
})

// ══════════════════════════════════════════════════════════════════════════════════════════
// gate G16(b) — blanket source-level scan of THIS production surface (never any occurrence)
// ══════════════════════════════════════════════════════════════════════════════════════════

describe('upaya.ts — G16(b) blanket substrate-ban scan (the serving surface has NO legitimate ' +
  'reason to mention any forbidden identifier, unlike the definer library)', () => {
  const src = readFileSync(fileURLToPath(new URL('./upaya.ts', import.meta.url)), 'utf8')

  it('contains zero occurrences of the forbidden mortality/longevity identifiers', () => {
    expect(MORTALITY_FORBIDDEN_IDENTIFIER_PATTERN.test(src)).toBe(false)
  })

  it('never imports or calls ganita_ayurdaya_get', () => {
    expect(/ganita_ayurdaya_get/i.test(src)).toBe(false)
  })
})

// ══════════════════════════════════════════════════════════════════════════════════════════
// Honest degradation when substrate calls fail/are unavailable (no live platform in this suite)
// ══════════════════════════════════════════════════════════════════════════════════════════

describe('buildKalaUpayaResult — honest degradation (no live platform reachable in this suite)', () => {
  beforeEach(() => {
    mockCallPlatformPrimitive.mockReset()
    mockCallPlatformPrimitive.mockRejectedValue(new Error('unreachable in unit test'))
    mockCallKalaRegistryCap.mockReset()
    mockCallKalaRegistryCap.mockRejectedValue(new Error('unreachable in unit test'))
    mockCallPlatformWrites.mockReset()
  })

  it('tags the tool name and threads chart_id/event_class through', async () => {
    const result = await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career', event_class: 'career_promotion' }, PRINCIPAL)
    expect(isMortalityRefusal(result)).toBe(false)
    const response = result as KalaUpayaResponse
    expect(response.tool).toBe('kala_upaya_get')
    expect(response.chart_id).toBe(CHART_ID)
    expect(response.event_class).toBe('career_promotion')
  })

  it('carries the three coverage concepts verbatim, honestly honest_empty on failure', async () => {
    const result = await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career' }, PRINCIPAL)
    const response = result as KalaUpayaResponse
    const concepts = response.coverage.map((c) => c.concept.split(' ')[0]).sort()
    expect(concepts).toEqual(['alternate_routing_search', 'efficacy_tiers', 'pact_link_diagnosis'])
    for (const entry of response.coverage) {
      expect(entry.state === 'computed' || Boolean(entry.reason)).toBe(true)
    }
  })

  it('honest_empty pact diagnosis when neither domain nor bhava is supplied', async () => {
    const result = await buildKalaUpayaResult({ chart_id: CHART_ID }, PRINCIPAL)
    const response = result as KalaUpayaResponse
    expect(response.diagnosis.pact_status).toBeNull()
    expect(response.diagnosis.failing_link).toBeNull()
    const pactEntry = response.coverage.find((c) => c.concept.startsWith('pact_link_diagnosis'))
    expect(pactEntry?.state).toBe('honest_empty')
  })

  it('interventions and uncited_remedy_rows are always arrays, never merged into one list', async () => {
    const result = await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career' }, PRINCIPAL)
    const response = result as KalaUpayaResponse
    expect(Array.isArray(response.interventions)).toBe(true)
    expect(Array.isArray(response.uncited_remedy_rows)).toBe(true)
    expect(response.intervention_count).toBe(response.interventions.length)
    expect(response.uncited_remedy_row_count).toBe(response.uncited_remedy_rows.length)
  })

  it('filing_state is not_requested when adopt_intervention is omitted (a plain read never files)', async () => {
    const result = await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career' }, PRINCIPAL)
    const response = result as KalaUpayaResponse
    expect(response.filing_state).toBe('not_requested')
    expect(response.filed_prediction_id).toBeNull()
  })

  it('filing_state is an honest filing_failed on native_directed adoption WITHOUT a window ' +
    '(wired Step 4; B.10 — the engine never composes a window bound) — NEVER filed, no write call', async () => {
    const result = await buildKalaUpayaResult({
      chart_id: CHART_ID, domain: 'career', event_class: 'career_promotion',
      adopt_intervention: { intervention_id: 'x', confidence: 0.5, falsifier: 'f', adoption_basis: 'native_directed' },
    }, PRINCIPAL)
    const response = result as KalaUpayaResponse
    expect(response.filing_state).toBe('filing_failed')
    expect(response.filing_detail).toContain('window')
    expect(response.filed_prediction_id).toBeNull()
    expect(response.intervention_ledger).toBeNull()
    expect(mockCallPlatformWrites).not.toHaveBeenCalled()
  })

  it('filing_state is filed on native_directed adoption WITH a window (wired Step 4 → spine → ' +
    'ledger recording); an unmatched intervention_id yields an HONEST unrecorded ledger block, never fabricated values', async () => {
    mockCallPlatformWrites.mockImplementation(async (action: string) => ({
      status: 200,
      envelope: {
        ok: true, trace_id: 't', epistemics: {},
        result: action === 'prospective_ledger_file'
          ? { prediction: { prediction_id: 'pred-1' } }
          : { intervention_id: 'iv-1', created: true },
        citations: [], plan: null, predictions_logged: [],
      },
    }))
    const result = await buildKalaUpayaResult({
      chart_id: CHART_ID, domain: 'career', event_class: 'career_promotion',
      adopt_intervention: {
        intervention_id: 'x', confidence: 0.5, falsifier: 'f', adoption_basis: 'native_directed',
        window: { start: '2026-09-01', end: '2027-01-01' },
      },
    }, PRINCIPAL)
    const response = result as KalaUpayaResponse
    expect(response.filing_state).toBe('filed')
    expect(response.filed_prediction_id).toBe('pred-1')
    // This suite's substrate is unreachable → zero served interventions → the adopted id 'x'
    // matches no served row → the ledger recording is refused HONESTLY (its efficacy_tier and
    // citation must be inherited from a served row, never invented), stated with the reason.
    expect(response.intervention_ledger).not.toBeNull()
    expect(response.intervention_ledger?.recorded).toBe(false)
    expect(response.intervention_ledger?.detail).toContain('did not match any served')
    // Only the prospective filing hit the write route — no ledger write was attempted.
    expect(mockCallPlatformWrites.mock.calls.map((c) => c[0])).toEqual(['prospective_ledger_file'])
  })

  it('filing_state withholds on an adverse event_class regardless of adoption_basis', async () => {
    const result = await buildKalaUpayaResult({
      chart_id: CHART_ID, domain: 'health', event_class: 'illness_acute',
      adopt_intervention: { intervention_id: 'x', confidence: 0.5, falsifier: 'f', adoption_basis: 'native_directed' },
    }, PRINCIPAL)
    const response = result as KalaUpayaResponse
    expect(response.filing_state).toBe('filing_withheld_pending_native_signoff')
    expect(response.filed_prediction_id).toBeNull()
  })

  it('resolves disclosure.audience_tier to native_self on both canonical charts, stated not assumed', async () => {
    for (const chartId of [CHART_ID, ABHINANDAN_CHART_ID]) {
      const result = await buildKalaUpayaResult({ chart_id: chartId, domain: 'career' }, PRINCIPAL)
      const response = result as KalaUpayaResponse
      expect(response.disclosure.audience_tier).toBe('native_self')
      expect(response.disclosure.basis.length).toBeGreaterThan(0)
    }
  })

  it('efficacy_report is honest_empty with zero counts (no ledger read path yet — LAW ZERO)', async () => {
    const result = await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career' }, PRINCIPAL)
    const response = result as KalaUpayaResponse
    expect(response.efficacy_report.state).toBe('honest_empty')
    expect(response.efficacy_report.n_outcome_linked).toBe(0)
  })

  it('eligibility_pointer names kala_elect_get and the for_intervention contract, computes no window', async () => {
    const result = await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career' }, PRINCIPAL)
    const response = result as KalaUpayaResponse
    expect(response.eligibility_pointer.instrument).toBe('kala_elect_get')
    expect(response.eligibility_pointer.contract_param).toBe('for_intervention')
  })

  it('intervention_ref tri-plane pointer is an honest terminal no_lever when no diagnosis is known', async () => {
    const noDiagnosis = (await buildKalaUpayaResult({ chart_id: CHART_ID }, PRINCIPAL)) as KalaUpayaResponse
    expect(isNoLever(noDiagnosis.tri_plane.intervention_ref)).toBe(true)
  })

  it('serves a typed public-safe unavailable calibration_maturity when the authority is unreachable', async () => {
    const result = await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career' }, PRINCIPAL)
    const response = result as KalaUpayaResponse
    expect(response.calibration_maturity).toEqual({
      n_events: null,
      prospective_resolutions: null,
      event_class_coverage: null,
      weights_version: null,
      skill_score: null,
      state: 'unavailable',
      reason: 'calibration_maturity_authority_unavailable',
    })
  })

  it('interpretation_ref/prediction_ref are honest no_lever placeholders, not dangling pointers', async () => {
    const result = (await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career' }, PRINCIPAL)) as KalaUpayaResponse
    expect(isNoLever(result.tri_plane.interpretation_ref)).toBe(true)
    expect(isNoLever(result.tri_plane.prediction_ref)).toBe(true)
  })

  it('composed_text is non-empty', async () => {
    const result = (await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career' }, PRINCIPAL)) as KalaUpayaResponse
    expect(result.composed_text.length).toBeGreaterThan(0)
  })

  it('threads question_frame through when supplied, and is null when omitted', async () => {
    const withFrame = (await buildKalaUpayaResult(
      { chart_id: CHART_ID, domain: 'career', question_frame: { domain: 'career' } }, PRINCIPAL,
    )) as KalaUpayaResponse
    expect(withFrame.question_frame).toEqual({ domain: 'career' })
    const noFrame = (await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career' }, PRINCIPAL)) as KalaUpayaResponse
    expect(noFrame.question_frame).toBeNull()
  })

  it('F-118: the disclosure fields are always present and internally consistent, even when the ' +
    'substrate is unreachable (an honest zero, never an omitted field)', async () => {
    const response = (await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career' }, PRINCIPAL)) as KalaUpayaResponse
    expect(response.source_rows_considered).toBe(0)
    expect(response.duplicate_rows_collapsed).toBe(0)
    expect(response.non_prescriptive_rows).toEqual([])
    expect(response.non_prescriptive_note).toBeNull()
    expect(response.efficacy_discrimination.discriminating).toBe(false)
    expect(response.efficacy_discrimination.rows_evaluated).toBe(0)
  })

  it('runs identically (same coverage-concept set) on both canonical charts (gate G13)', async () => {
    const a = (await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career' }, PRINCIPAL)) as KalaUpayaResponse
    const b = (await buildKalaUpayaResult({ chart_id: ABHINANDAN_CHART_ID, domain: 'career' }, PRINCIPAL)) as KalaUpayaResponse
    const conceptsOf = (r: KalaUpayaResponse) => r.coverage.map((c) => c.concept.split(' ')[0]).sort()
    expect(conceptsOf(a)).toEqual(conceptsOf(b))
  })
})

// ══════════════════════════════════════════════════════════════════════════════════════════
// F-118 — THE LIVE REPRODUCER, as a regression test
// ══════════════════════════════════════════════════════════════════════════════════════════
//
// Original claim (PARIŚEṢA baseline F-118, CL-09 earned-signal): calling
//   kala_upaya_get(chart_id=482012f1-…, domain='relationship', as_of_date='2026-08-15')
// returned `intervention_count=100` over only 14 DISTINCT labels — 50 of the 100 rows being the
// byte-identical string 'light — for saturn — severity=medium × anchor_magnitude=minor → light'
// (a severity classification, not an act), each under a different phala_mitigation UUID; the
// other 50 being 13 bodha_rm remedies stored once per ayanamsha. All 100 carried
// efficacy_tier='classically_attested' and targets_link='promise'.
//
// The fixtures below reproduce that live shape EXACTLY (verified against the production DB
// 2026-08-21: phala_mitigation holds 536 rows/chart across 4 distinct (tier, graha, basis)
// combinations, every one of them with an empty program_jsonb/tradition_options_jsonb/
// recommended_tier_jsonb; bodha_rm_remedy_prescriptions holds 135 rows/chart = 27 remedies × 5
// ayanamshas). The assertions are the finding's own counting recipe, inverted.
describe('F-118 — kala_upaya_get no longer serves duplicated rows as distinct interventions', () => {
  function wire(payload: Record<string, unknown>) {
    return {
      status: 200,
      envelope: {
        ok: true, trace_id: 't', epistemics: {},
        result: { tool_bundle_id: 'tb', tool_name: 'x', results: [{ content: JSON.stringify(payload) }], result_hash: 'sha256:x' },
        citations: [], plan: null, predictions_logged: [],
      },
    }
  }

  /** 50 phala_mitigation rows, byte-identical apart from their primary key — the live shape. */
  const LIVE_DUPLICATED_LABEL = 'light — for saturn — severity=medium × anchor_magnitude=minor → light'
  function fiftyIdenticalMitigationRows() {
    return Array.from({ length: 50 }, (_, i) => ({
      mitigation_id: `pm-${i}`, afflicting_graha: 'saturn', obstruction_severity: null,
      intensity_tier: 'light', proportionality_basis: 'severity=medium × anchor_magnitude=minor → light',
      classical_citation: 'Brihat Parashara Hora Shastra — Upaya chapter',
      program_jsonb: { scheduled_ids: [], sequence_basis: 'prerequisite_topo_sort + incompatible_exclusion', total_scheduled: 0 },
      tradition_options_jsonb: { vastu: [], vedic: [], modern: [], tantra: [], ayurvedic: [], lal_kitab: [] },
      recommended_tier_jsonb: { free: [], low_cost: [], high_investment: [] },
    }))
  }

  /** 10 distinct remedies × 5 ayanamsha copies = the unpinned 50-row page the tool used to get. */
  const DISTINCT_REMEDIES = 10
  function tenRemediesTimesFiveAyanamshas() {
    const rows: Array<Record<string, unknown>> = []
    for (let r = 0; r < DISTINCT_REMEDIES; r += 1) {
      for (const aya of ['lahiri_chitrapaksha', 'krishnamurti', 'raman', 'true_chitra', 'surya_siddhanta_classical']) {
        rows.push({
          prescription_id: `rm-${r}-${aya}`, ayanamsha_id: aya, target_graha: 'saturn',
          remedy_category: 'mantra',
          remedy_label_human: `Recite remedy #${r} 108 times daily, facing east.`,
          classical_strength_rating: 3, classical_sources_jsonb: ['BPHS ch.93'],
          feasibility_score: 0.9, citation_ref: null, citation_human: `G27 remedy ${r}`,
        })
      }
    }
    return rows
  }

  beforeEach(() => {
    mockCallPlatformPrimitive.mockReset()
    mockCallPlatformWrites.mockReset()
    mockCallKalaRegistryCap.mockReset()
    mockCallKalaRegistryCap.mockImplementation(async (uri: string) => {
      if (uri === 'marsys://tool/L-PACT/pact_query') {
        return {
          pact_status: 'denied_at_promise',
          stages: [
            { stage: 'PROMISE', status: 'denied', reason: 'The rashi checklist does not promise this matter' },
            { stage: 'CONFIRMATION', status: 'denied', dignities: [{ role: 'bhavesha', graha: 'saturn' }] },
          ],
          fact_id_refs: ['fact-1'],
        }
      }
      return { nodes: [], edges: [] }
    })
    mockCallPlatformPrimitive.mockImplementation(async (toolName: string, args: Record<string, unknown>) => {
      if (toolName === 'mitigation_map') return wire({ remedies: fiftyIdenticalMitigationRows() })
      if (toolName === 'bodha_rm_prescriptions_get') {
        const all = tenRemediesTimesFiveAyanamshas()
        const pinned = args['ayanamsha_id']
          ? all.filter((r) => r['ayanamsha_id'] === args['ayanamsha_id'])
          : all.slice(0, 50)
        return wire({ rows: pinned })
      }
      return wire({ remedies: [] })
    })
  })

  async function reproduce(): Promise<KalaUpayaResponse> {
    const result = await buildKalaUpayaResult(
      { chart_id: CHART_ID, domain: 'relationship', as_of_date: '2026-08-15' }, PRINCIPAL,
    )
    expect(isMortalityRefusal(result)).toBe(false)
    return result as KalaUpayaResponse
  }

  it('intervention_count now equals the number of DISTINCT labels, never the raw row count', async () => {
    const response = await reproduce()
    const distinctLabels = new Set(response.interventions.map((r) => r.label)).size
    expect(response.intervention_count).toBe(response.interventions.length)
    expect(response.intervention_count).toBe(distinctLabels)
    // The finding's own number: 100 served / 14 distinct. Never again.
    expect(response.intervention_count).toBeLessThan(100)
  })

  it('no two served interventions are byte-identical (the 50-duplicate degeneracy is gone)', async () => {
    const response = await reproduce()
    const seen = new Set<string>()
    for (const row of [...response.interventions, ...response.non_prescriptive_rows]) {
      const key = `${row.source_surface}|${row.label}|${row.actionable_prescription ?? ''}`
      expect(seen.has(key)).toBe(false)
      seen.add(key)
    }
  })

  it('the duplicated severity-classification row is served ONCE, out of interventions, and says ' +
    'plainly that it stands for 50 source rows', async () => {
    const response = await reproduce()
    expect(response.interventions.some((r) => r.label === LIVE_DUPLICATED_LABEL)).toBe(false)
    const collapsed = response.non_prescriptive_rows.filter((r) => r.label === LIVE_DUPLICATED_LABEL)
    expect(collapsed).toHaveLength(1)
    expect(collapsed[0]?.duplicate_row_count).toBe(50)
    expect(collapsed[0]?.actionable_prescription).toBeNull()
    expect(collapsed[0]?.duplicate_note).toContain('ONE recommendation, not 50')
    expect(response.non_prescriptive_note).toContain('NO actionable prescription')
  })

  it('every row inside `interventions` names a real act (actionable_prescription is never null)', async () => {
    const response = await reproduce()
    expect(response.interventions.length).toBeGreaterThan(0)
    for (const row of response.interventions) {
      expect(row.actionable_prescription).not.toBeNull()
      expect(String(row.actionable_prescription).trim().length).toBeGreaterThan(0)
    }
  })

  it('the ayanamsha pin turns 5 identical copies of 10 remedies into 10 distinct remedies', async () => {
    const response = await reproduce()
    expect(response.interventions).toHaveLength(DISTINCT_REMEDIES)
    for (const row of response.interventions) expect(row.duplicate_row_count).toBe(1)
  })

  it('the raw source-row figures are DISCLOSED, never hidden by the collapse (no silent drop)', async () => {
    const response = await reproduce()
    expect(response.source_rows_considered).toBe(50 + DISTINCT_REMEDIES)
    expect(response.duplicate_rows_collapsed).toBe(49)
    const servedRows = response.interventions.length + response.non_prescriptive_rows.length + response.uncited_remedy_rows.length
    expect(servedRows).toBe(response.source_rows_considered - response.duplicate_rows_collapsed)
  })

  it('the uniform efficacy grading is DISCLOSED as carrying zero information (§N.8), rather than ' +
    'read as a clean grade', async () => {
    const response = await reproduce()
    expect(response.efficacy_discrimination.discriminating).toBe(false)
    expect(response.efficacy_discrimination.distinct_efficacy_tiers).toBe(1)
    expect(response.efficacy_discrimination.note).toContain('zero information')
    expect(response.efficacy_discrimination.note).toContain('F118_INTERVENTION_SEMANTICS_DESIGN_CONTRACT')
  })

  it('the reading/composed_text never quotes a severity classification as evidence of a remedy', async () => {
    const response = await reproduce()
    expect(response.composed_text).not.toContain(LIVE_DUPLICATED_LABEL)
    for (const ev of response.reading.evidence) expect(ev.claim).not.toContain(LIVE_DUPLICATED_LABEL)
  })
})

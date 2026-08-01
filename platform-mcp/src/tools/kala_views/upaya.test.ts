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
vi.mock('../../client.js', async () => {
  const actual = await vi.importActual<typeof import('../../client.js')>('../../client.js')
  return { ...actual, callPlatformPrimitive: (...args: unknown[]) => mockCallPlatformPrimitive(...args) }
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

  it('filing_state degrades to filing_path_not_yet_available on native_directed adoption ' +
    '(Lane S spine not yet available) — NEVER filed', async () => {
    const result = await buildKalaUpayaResult({
      chart_id: CHART_ID, domain: 'career', event_class: 'career_promotion',
      adopt_intervention: { intervention_id: 'x', confidence: 0.5, falsifier: 'f', adoption_basis: 'native_directed' },
    }, PRINCIPAL)
    const response = result as KalaUpayaResponse
    expect(response.filing_state).toBe('filing_path_not_yet_available')
    expect(response.filed_prediction_id).toBeNull()
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

  it('serves an honest all-zero calibration_maturity (no LEL consulted at this build tier)', async () => {
    const result = await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career' }, PRINCIPAL)
    const response = result as KalaUpayaResponse
    expect(response.calibration_maturity).toEqual({
      n_events: 0, prospective_resolutions: 0, event_class_coverage: 0, weights_version: null, skill_score: null,
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

  it('runs identically (same coverage-concept set) on both canonical charts (gate G13)', async () => {
    const a = (await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career' }, PRINCIPAL)) as KalaUpayaResponse
    const b = (await buildKalaUpayaResult({ chart_id: ABHINANDAN_CHART_ID, domain: 'career' }, PRINCIPAL)) as KalaUpayaResponse
    const conceptsOf = (r: KalaUpayaResponse) => r.coverage.map((c) => c.concept.split(' ')[0]).sort()
    expect(conceptsOf(a)).toEqual(conceptsOf(b))
  })
})

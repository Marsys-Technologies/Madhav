/**
 * upaya_weak_promise_gate.test.ts — ṢAḌ-DARŚANA W4 gate prep (SHAD_DARSHANA_BRIEF_v2_0.md §3
 * W4): the WEAK-PROMISE UPĀYA (remedial-measure) HARNESS.
 *
 * T5 lane (e) deliverable #2, per the campaign ledger SESSION-B-BUILD NEXT-ACTION item 3.
 * Discharges Gate W4's own wording — "on 482012f1: a weakly-promised event class returns
 * correct link diagnosis + honestly-tiered non-empty ledger + filed prospective entry" —
 * against `buildKalaUpayaResult` (kala_upaya_diagnosis.ts) with EVERY substrate call mocked at
 * the same two levers `upaya.test.ts` already established (`callPlatformPrimitive` for the
 * remedy-sourcing surfaces, `callKalaRegistryCap` for `pact_query` / the CGM graph traversal),
 * so no live DB/network call is ever attempted. Live discharge against a real deploy is
 * explicitly deferred to the gate-close deploy session (KALA_W4_UPAYA_DESIGN_v1_0.md §9's own
 * G1/G2/G3/G3b table names the LIVE detector; this harness proves the same assertions hold
 * against canned data and is ready to re-point at a live principal once that session runs).
 *
 * "WEAKLY-PROMISED" = `pact_status: 'denied_at_confirmation'` (promised in the rāśi, but the
 * operative varga does not confirm it) — the design doc's own G1 row names EITHER
 * `denied_at_promise` or `denied_at_confirmation` as the qualifying weak-promise shape; this
 * harness uses `denied_at_confirmation` specifically because it is the "promise present but
 * weak" case (the un-promised / `denied_at_promise` shape is G4's "pressure without delivery"
 * scenario — see the PARKED-HONEST note at the bottom of this file for why G4 is not
 * discharged here).
 *
 * THE GAP THE T5 VERSION OF THIS HARNESS SURFACED IS NOW CLOSED (W4 gate-discharge-prep
 * lane): `resolveFilingState`'s Step 4 is wired via `resolveAndFileFilingState`
 * (kala_upaya_diagnosis.ts) to the filing spine (`intervention_filing.ts`'s
 * `fileInterventionFalsifier`), and a successful filing then records the serve-time
 * Intervention Ledger row via `recordInterventionLedgerEntry` → the sanctioned
 * `intervention_ledger_record` write action (item 42 / gate G7's write path). G3's literal
 * "filed prospective entry" outcome is therefore REACHABLE through this tool: this harness
 * now asserts the wired behavior — `filed` + a resolvable prediction_id + the ledger
 * recording — against a mocked `callPlatformWrites` (the single sanctioned write lever),
 * and separately asserts the spine's failure path still reports `filing_failed` with the
 * verbatim error, never a fabricated `filed`.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../../types.js'
import { buildKalaUpayaResult, isMortalityRefusal } from './upaya.js'

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

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }

function ok(result: unknown) {
  return { status: 200, envelope: { ok: true, trace_id: 't', epistemics: {}, result, citations: [], plan: null, predictions_logged: [] } }
}

/** The canned `pact_query` response for a weakly-promised event class: promised in the rāśi,
 *  the operative varga (CONFIRMATION stage) does NOT confirm it. Matches register_d10_pact.ts's
 *  own wire shape as read by `fetchPactDiagnosis` (pact_status, stages[].dignities[], fact_id_refs). */
function weakPromisePactResponse() {
  return {
    pact_status: 'denied_at_confirmation',
    stages: [
      { stage: 'PROMISE', status: 'promised', reason: 'Saturn (7th lord) occupies the 7th — a real rāśi promise' },
      {
        stage: 'CONFIRMATION',
        status: 'denied',
        reason: 'Saturn is debilitated in the D9 — the rāśi promise does not survive divisional confirmation',
        dignities: [{ role: 'bhavesha', graha: 'Saturn', dignity: 'debilitated' }],
      },
    ],
    fact_id_refs: ['fact-promise-1', 'fact-confirmation-1'],
  }
}

function cannedRemedyRows() {
  return {
    mitigation_map: {
      remedies: [
        {
          mitigation_id: 'pm-1', afflicting_graha: 'Saturn', obstruction_severity: 3,
          intensity_tier: 'major', proportionality_basis: 'severity-matched',
          classical_citation: 'BPHS ch.45.12',
        },
      ],
    },
    bodha_rm_prescriptions_get: {
      rows: [
        {
          prescription_id: 'rm-1', target_graha: 'Saturn', remedy_category: 'mantra',
          remedy_label_human: 'Shani mantra japa', classical_strength_rating: 3,
          classical_sources_jsonb: ['Muhurta Chintamani ch.9'], feasibility_score: 0.7,
          citation_ref: null, citation_human: 'Muhurta Chintamani ch.9',
        },
      ],
    },
    query_remedies_for_chart: { remedies: [] },
  }
}

function mockWeakPromiseSubstrate(): void {
  mockCallKalaRegistryCap.mockImplementation(async (uri: string) => {
    if (uri === 'marsys://tool/L-PACT/pact_query') return weakPromisePactResponse()
    if (uri === 'marsys://tool/L2/traverse_chart_graph') return { nodes: [], edges: [] }
    throw new Error(`upaya_weak_promise_gate harness: unmocked capability '${uri}'`)
  })
  mockCallPlatformPrimitive.mockImplementation(async (toolName: string) => {
    const rows = cannedRemedyRows()
    if (toolName in rows) return ok((rows as Record<string, unknown>)[toolName])
    throw new Error(`upaya_weak_promise_gate harness: unmocked primitive '${toolName}'`)
  })
}

/** Canned sanctioned-write responses for the ONE write lever (`callPlatformWrites`):
 *  `prospective_ledger_file` seals the prospective entry; `intervention_ledger_record`
 *  records the serve-time ledger row. Shapes mirror the real route's envelopes. */
function mockWriteRouteSuccess(): void {
  mockCallPlatformWrites.mockImplementation(async (action: string) => {
    if (action === 'prospective_ledger_file') {
      return ok({ prediction: { prediction_id: 'pred-uuid-1' }, governance: {} })
    }
    if (action === 'intervention_ledger_record') {
      return ok({ intervention_id: 'iv-uuid-1', created: true })
    }
    throw new Error(`upaya_weak_promise_gate harness: unmocked write action '${action}'`)
  })
}

beforeEach(() => {
  mockCallPlatformPrimitive.mockReset()
  mockCallKalaRegistryCap.mockReset()
  mockCallPlatformWrites.mockReset()
})

describe('weak-promise UPĀYA harness (T5 W4 prep, no live discharge) — Gate W4 / KALA_W4_UPAYA_DESIGN §9', () => {
  it('G1 — a weakly-promised event class returns the correct link diagnosis (failing_link matches the halted stage)', async () => {
    mockWeakPromiseSubstrate()
    const result = await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career' }, PRINCIPAL)
    expect(isMortalityRefusal(result)).toBe(false)
    if (isMortalityRefusal(result)) return
    expect(result.diagnosis.pact_status).toBe('denied_at_confirmation')
    // The design §2.2 table, machine-checked: denied_at_confirmation -> failing_link='confirmation'.
    expect(result.diagnosis.failing_link).toBe('confirmation')
    expect(result.diagnosis.statement).toContain('varga')
    expect(result.diagnosis.authority_basis).toBe('pact_query:denied_at_confirmation')
  })

  it('G1 corollary — the diagnosed graha (Saturn, read internally off the CONFIRMATION stage dignities) seeds the remedy routing', async () => {
    mockWeakPromiseSubstrate()
    const result = await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career' }, PRINCIPAL)
    if (isMortalityRefusal(result)) throw new Error('unexpected mortality refusal')
    // query_remedies_for_chart is only called when a targetedGraha was resolved (fetchRemedyRows'
    // guard) — its presence in the call log is the observable proof the internal targeted_graha
    // (not exposed on the public response) was actually 'Saturn', not silently dropped.
    expect(mockCallPlatformPrimitive).toHaveBeenCalledWith(
      'query_remedies_for_chart',
      expect.objectContaining({ affliction: 'Saturn' }),
      PRINCIPAL,
    )
  })

  it('G1 detector proof: a pact_status OUTSIDE the closed vocabulary produces honest_empty, never a fabricated diagnosis', async () => {
    mockCallKalaRegistryCap.mockImplementation(async (uri: string) => {
      if (uri === 'marsys://tool/L-PACT/pact_query') return { pact_status: 'not_a_real_status', stages: [] }
      return { nodes: [], edges: [] }
    })
    mockCallPlatformPrimitive.mockImplementation(async () => ok({}))
    const result = await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career' }, PRINCIPAL)
    if (isMortalityRefusal(result)) throw new Error('unexpected mortality refusal')
    expect(result.diagnosis.pact_status).toBeNull()
    expect(result.diagnosis.failing_link).toBeNull()
    expect(result.coverage.some((c) => c.concept === 'pact_link_diagnosis')).toBe(true)
  })

  it('G2 — the ledger is non-empty and every served row carries a resolvable efficacy_tier from the closed set + a citation', async () => {
    mockWeakPromiseSubstrate()
    const result = await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career' }, PRINCIPAL)
    if (isMortalityRefusal(result)) throw new Error('unexpected mortality refusal')
    expect(result.interventions.length).toBeGreaterThanOrEqual(1)
    const EFFICACY_TIERS = ['classically_attested', 'traditional', 'speculative_extension']
    for (const row of result.interventions) {
      expect(row.efficacy_tier, `row ${row.id} has no resolvable efficacy_tier`).not.toBeNull()
      expect(EFFICACY_TIERS).toContain(row.efficacy_tier)
      expect(row.citation, `row ${row.id} (${row.efficacy_tier}) is served in the CITED ledger with no citation`).not.toBeNull()
    }
    // §N.6 density split: uncited rows are a SEPARATE array with its own count — never mixed
    // silently into the served `interventions` ledger a caller could misread as "N confirmed".
    expect(Array.isArray(result.uncited_remedy_rows)).toBe(true)
    for (const row of result.uncited_remedy_rows) {
      expect(result.interventions.find((i) => i.id === row.id)).toBeUndefined()
    }
  })

  it('G2 targeting: every routed intervention names the diagnosed failing_link', async () => {
    mockWeakPromiseSubstrate()
    const result = await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career' }, PRINCIPAL)
    if (isMortalityRefusal(result)) throw new Error('unexpected mortality refusal')
    for (const row of result.interventions) {
      expect(row.targets_link).toBe('confirmation')
    }
  })

  it('G3 (WIRED) — a native-directed, non-adverse adoption with a window FILES: filed + prediction_id + the serve-time Intervention Ledger row recorded', async () => {
    mockWeakPromiseSubstrate()
    mockWriteRouteSuccess()
    const result = await buildKalaUpayaResult(
      {
        chart_id: CHART_ID, domain: 'career',
        adopt_intervention: {
          intervention_id: 'phala_mitigation:pm-1', claim: 'Shani propitiation eases the confirmation block',
          falsifier: 'no change in career outcomes within 6 months', confidence: 0.55,
          window: { start: '2026-09-01', end: '2027-03-01' }, adoption_basis: 'native_directed',
        },
      },
      PRINCIPAL,
    )
    if (isMortalityRefusal(result)) throw new Error('unexpected mortality refusal')
    // The wired Step-4 path: gates 1–3 passed → the spine filed the prospective entry.
    expect(result.filing_state).toBe('filed')
    expect(result.filed_prediction_id).toBe('pred-uuid-1')
    expect(result.adoption_basis).toBe('native_directed')
    // Item 42 / gate G7: the filing then recorded the serve-time Intervention Ledger row,
    // inheriting the adopted row's own citation/tier (§N.5 — never restated).
    expect(result.intervention_ledger).not.toBeNull()
    expect(result.intervention_ledger?.recorded).toBe(true)
    expect(result.intervention_ledger?.intervention_id).toBe('iv-uuid-1')
    // Both sanctioned write actions were called, in filing→ledger order, and the ledger row
    // references the sealed prediction (ruling S-1 spine).
    const actions = mockCallPlatformWrites.mock.calls.map((c) => c[0])
    expect(actions).toEqual(['prospective_ledger_file', 'intervention_ledger_record'])
    const ledgerParams = mockCallPlatformWrites.mock.calls[1]![1] as { chart_id: string; entry: Record<string, unknown> }
    expect(ledgerParams.chart_id).toBe(CHART_ID)
    expect(ledgerParams.entry['prediction_id']).toBe('pred-uuid-1')
    expect(ledgerParams.entry['adoption_basis']).toBe('native_directed')
    expect(ledgerParams.entry['intervention_class']).toBe('upaya')
    // filed_by is NEVER supplied client-side — the route stamps it from the principal.
    expect(ledgerParams.entry['filed_by']).toBeUndefined()
    // The diagnosis + ledger are STILL served in full alongside the filing.
    expect(result.diagnosis.pact_status).not.toBeNull()
    expect(result.interventions.length).toBeGreaterThan(0)
  })

  it('G3 failure path — a spine/server error reports filing_failed with the VERBATIM error, never a fabricated filed', async () => {
    mockWeakPromiseSubstrate()
    mockCallPlatformWrites.mockImplementation(async () => {
      throw new Error('ECONNREFUSED platform unreachable (harness)')
    })
    const result = await buildKalaUpayaResult(
      {
        chart_id: CHART_ID, domain: 'career',
        adopt_intervention: {
          intervention_id: 'phala_mitigation:pm-1', claim: 'c',
          falsifier: 'f', confidence: 0.55,
          window: { start: '2026-09-01', end: '2027-03-01' }, adoption_basis: 'native_directed',
        },
      },
      PRINCIPAL,
    )
    if (isMortalityRefusal(result)) throw new Error('unexpected mortality refusal')
    expect(result.filing_state).toBe('filing_failed')
    expect(result.filed_prediction_id).toBeNull()
    expect(result.filing_detail).toContain('ECONNREFUSED')
    // No ledger row is ever recorded when the filing itself failed.
    expect(result.intervention_ledger).toBeNull()
    // §3.5.B: the reading is still served in full.
    expect(result.diagnosis.pact_status).not.toBeNull()
    expect(result.interventions.length).toBeGreaterThan(0)
  })

  it('G3 window guard — native-directed WITHOUT a window is an honest filing_failed (B.10: the engine never composes a window bound), no write call made', async () => {
    mockWeakPromiseSubstrate()
    mockWriteRouteSuccess()
    const result = await buildKalaUpayaResult(
      {
        chart_id: CHART_ID, domain: 'career',
        adopt_intervention: {
          intervention_id: 'phala_mitigation:pm-1', claim: 'c',
          falsifier: 'f', confidence: 0.55, adoption_basis: 'native_directed',
        },
      },
      PRINCIPAL,
    )
    if (isMortalityRefusal(result)) throw new Error('unexpected mortality refusal')
    expect(result.filing_state).toBe('filing_failed')
    expect(result.filing_detail).toContain('window')
    expect(result.filed_prediction_id).toBeNull()
    expect(result.intervention_ledger).toBeNull()
    expect(mockCallPlatformWrites).not.toHaveBeenCalled()
  })

  it('G3b — ADJUDICATION-12 fail-closed: session_inferred / absent / unrecognised bases all resolve awaiting_native_confirmation, never filed', async () => {
    mockWeakPromiseSubstrate()
    const bases: Array<Record<string, unknown> | undefined> = [
      { intervention_id: 'x', claim: 'c', falsifier: 'f', confidence: 0.5, window: { start: '2026-09-01', end: '2027-01-01' }, adoption_basis: 'session_inferred' },
      undefined,
      { intervention_id: 'x', claim: 'c', falsifier: 'f', confidence: 0.5, window: { start: '2026-09-01', end: '2027-01-01' }, adoption_basis: 'not_a_real_basis' },
    ]
    for (const adopt of bases) {
      mockWeakPromiseSubstrate()
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const result = await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career', adopt_intervention: adopt as any }, PRINCIPAL)
      if (isMortalityRefusal(result)) throw new Error('unexpected mortality refusal')
      const expected = adopt === undefined ? 'not_requested' : 'awaiting_native_confirmation'
      expect(result.filing_state, `adopt=${JSON.stringify(adopt)}`).toBe(expected)
      expect(result.filed_prediction_id).toBeNull()
    }
  })

  it('G3b — an adverse event_class withholds filing regardless of adoption_basis (the §5.3 predicate is STRONGER than native_directed)', async () => {
    mockWeakPromiseSubstrate()
    const result = await buildKalaUpayaResult(
      {
        chart_id: CHART_ID, domain: 'career', event_class: 'illness_acute',
        adopt_intervention: {
          intervention_id: 'phala_mitigation:pm-1', claim: 'c', falsifier: 'f', confidence: 0.5,
          window: { start: '2026-09-01', end: '2027-01-01' }, adoption_basis: 'native_directed',
        },
      },
      PRINCIPAL,
    )
    if (isMortalityRefusal(result)) throw new Error('unexpected mortality refusal')
    expect(result.filing_state).toBe('filing_withheld_pending_native_signoff')
    expect(result.filed_prediction_id).toBeNull()
    // §3.5.B: the diagnosis + ledger are STILL served in full even though the write is withheld.
    expect(result.diagnosis.pact_status).not.toBeNull()
  })

  it('a plain read (no adopt_intervention) never files — not_requested, zero filing side-effects', async () => {
    mockWeakPromiseSubstrate()
    const result = await buildKalaUpayaResult({ chart_id: CHART_ID, domain: 'career' }, PRINCIPAL)
    if (isMortalityRefusal(result)) throw new Error('unexpected mortality refusal')
    expect(result.filing_state).toBe('not_requested')
  })
})

// ── PARKED-HONEST: G4 "pressure without delivery" is NOT discharged by this harness ─────────
// KALA_W4_UPAYA_DESIGN_v1_0.md §9 G4 requires the Six-Views §C.1 graded-gate language ("window
// served, not suppressed, labelled 'temporal pressure without strong natal promise'") on an
// UN-promised window. That label does not exist in the serving code yet: `ahead.ts`'s own
// coverage note (line ~1859) reads verbatim "Law-3 PACT gating ('pressure without delivery') is
// not yet applied to these raw windows — SHAD_DARSHANA_BRIEF_v2_0.md §2.2 (wave W2/W3)" — i.e.
// this is a genuine, currently-unbuilt FEATURE, not a testable-but-untested behavior. Building
// it is W4 serving-code work; this T5 lane is harness-only (brief §3 W5/W4 prep), so G4 is
// left honestly undischarged here rather than tested against a feature that does not exist.
describe.skip('G4 — "pressure without delivery" on an un-promised window (PARKED-HONEST: feature not yet built, see header note)', () => {
  it('requires ahead.ts to implement the Six-Views §C.1 graded-gate language before this can be a real test', () => {})
})

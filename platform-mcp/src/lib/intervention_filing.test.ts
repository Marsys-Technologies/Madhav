/**
 * intervention_filing.test.ts — ṢAḌ-DARŚANA W4 Lane S spine tests.
 *
 * Spec: KALA_W4_UPAYA_DESIGN_v1_0.md §4.4, §5.3, §5.4; gates G3b / G14 / G14b / G16.
 *
 * Mocks `fetch` (this module's only I/O) — same idiom as kala_ahead_get.test.ts /
 * r6_0b_deadtools_smoke.test.ts. SERVICE_TOKEN is set so `client.ts`'s
 * `fetchIdentityToken()` short-circuits to the static-token path instead of trying real
 * GCP ADC.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../types.js'
import {
  fileInterventionFalsifier,
  recordInterventionLedgerEntry,
  WITHHOLD_EVENT_CLASSES,
  WITHHOLD_PREDICATE_SQL,
  resolveWithholdEventClassesLive,
  type FileInterventionFalsifierInput,
  type RecordInterventionLedgerInput,
} from './intervention_filing.js'

const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }
const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function baseInput(overrides: Partial<FileInterventionFalsifierInput> = {}): FileInterventionFalsifierInput {
  return {
    chart_id: CHART_ID,
    intervention_class: 'upaya',
    event_class: 'career_promotion',
    claim: 'A remedial rite targeting the weak 10th-lord promise, elected in the stated window.',
    falsifier: 'No qualifying career_promotion event recorded in the LEL within the elected window.',
    confidence: 0.55,
    window: { start: '2027-01-01T00:00:00Z', end: '2027-01-15T00:00:00Z' },
    source_citation: 'BPHS 27.4',
    model: 'kala_upaya_get_v1',
    formula_version: 'upaya_setu_v1.0',
    adoption_basis: 'native_directed',
    ...overrides,
  }
}

beforeEach(() => {
  vi.unstubAllGlobals()
  process.env['SERVICE_TOKEN'] = 'test-service-token' // skip real GCP identity-token auth
})

// ── The withhold class set itself ───────────────────────────────────────────────────

describe('WITHHOLD_EVENT_CLASSES', () => {
  it('is non-empty (G14b non-vacuity) and contains exactly the five ADJUDICATION-13 classes', () => {
    expect(WITHHOLD_EVENT_CLASSES.size).toBe(5)
    for (const cls of ['illness_acute', 'chronic_onset', 'surgery', 'psychological_arc', 'bereavement']) {
      expect(WITHHOLD_EVENT_CLASSES.has(cls)).toBe(true)
    }
  })

  it('WITHHOLD_PREDICATE_SQL is a magnitude-free three-disjunct predicate (amendment A — no magnitude_floor)', () => {
    expect(WITHHOLD_PREDICATE_SQL).toContain("domain = 'health'")
    expect(WITHHOLD_PREDICATE_SQL).toContain("lel_category = 'psychological'")
    expect(WITHHOLD_PREDICATE_SQL).toContain("event_class_id = 'bereavement'")
    expect(WITHHOLD_PREDICATE_SQL).not.toMatch(/magnitude_floor/)
  })
})

// ── Gate 1 — §5.3 withhold predicate (G14 / G14b) ───────────────────────────────────

describe('fileInterventionFalsifier — §5.3 withhold predicate', () => {
  it.each(['illness_acute', 'chronic_onset', 'surgery', 'psychological_arc', 'bereavement'])(
    "withholds filing for event_class '%s': files nothing, returns filing_withheld_pending_native_signoff with a populated filing_ready_payload",
    async (eventClass) => {
      const fetchSpy = vi.fn()
      vi.stubGlobal('fetch', fetchSpy)

      const result = await fileInterventionFalsifier(baseInput({ event_class: eventClass }), TEST_PRINCIPAL)

      expect(result.state).toBe('filing_withheld_pending_native_signoff')
      expect(result.prediction_id).toBeNull()
      expect(result.filing_ready_payload).not.toBeNull()
      expect(result.filing_ready_payload?.action).toBe('prospective_ledger_file')
      expect(result.filing_ready_payload?.entry['event_class']).toBe(eventClass)
      expect(result.filing_ready_payload?.withheld_reason).toBeTruthy()
      // No network call at all — the withhold is evaluated before any I/O.
      expect(fetchSpy).not.toHaveBeenCalled()
    }
  )

  it('does not withhold a non-withheld class (adoption_basis native_directed reaches the network call)', async () => {
    const fetchSpy = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        trace_id: 't1',
        epistemics: { surgical: true, confidence_band: 'medium', horizon_days: 14, falsifier: 'x' },
        result: { prediction: { prediction_id: 'pred-123' } },
        citations: [],
        plan: null,
        predictions_logged: [],
        synthesis_audit: null,
        suggested_followups: [],
      }),
      text: async () => '',
    }))
    vi.stubGlobal('fetch', fetchSpy)

    const result = await fileInterventionFalsifier(baseInput({ event_class: 'career_promotion' }), TEST_PRINCIPAL)

    expect(result.state).toBe('filed')
    expect(result.prediction_id).toBe('pred-123')
    expect(fetchSpy).toHaveBeenCalled()
  })

  it('a native_directed basis does NOT override the §5.3 withhold — the withhold is the stronger constraint', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)

    const result = await fileInterventionFalsifier(
      baseInput({ event_class: 'bereavement', adoption_basis: 'native_directed' }),
      TEST_PRINCIPAL
    )

    expect(result.state).toBe('filing_withheld_pending_native_signoff')
    expect(fetchSpy).not.toHaveBeenCalled()
  })
})

// ── Gate 2 — ADJUDICATION-12 fail-closed adoption_basis (G3b) ──────────────────────

describe('fileInterventionFalsifier — ADJUDICATION-12 fail-closed adoption_basis', () => {
  it('adoption_basis session_inferred: never files, returns awaiting_native_confirmation with a populated filing_ready_payload', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)

    const result = await fileInterventionFalsifier(baseInput({ adoption_basis: 'session_inferred' }), TEST_PRINCIPAL)

    expect(result.state).toBe('awaiting_native_confirmation')
    expect(result.prediction_id).toBeNull()
    expect(result.filing_ready_payload).not.toBeNull()
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('adoption_basis absent (undefined, cast through an untyped caller): fails CLOSED to awaiting_native_confirmation, never files', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)

    const input = baseInput() as unknown as Record<string, unknown>
    delete input['adoption_basis']

    const result = await fileInterventionFalsifier(input as unknown as FileInterventionFalsifierInput, TEST_PRINCIPAL)

    expect(result.state).toBe('awaiting_native_confirmation')
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('adoption_basis an unrecognised string: fails CLOSED to awaiting_native_confirmation, never files', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)

    const input = { ...baseInput(), adoption_basis: 'the_native_probably_wants_this' } as unknown as FileInterventionFalsifierInput

    const result = await fileInterventionFalsifier(input, TEST_PRINCIPAL)

    expect(result.state).toBe('awaiting_native_confirmation')
    expect(fetchSpy).not.toHaveBeenCalled()
  })
})

// ── Gate 0 — §5.4 individualized-mortality-window hard exclusion (defence in depth, G16) ──

describe('fileInterventionFalsifier — §5.4 mortality-window defence in depth', () => {
  it('refuses a request whose event_class names a longevity/mortality subject — no network call, no filing_ready_payload', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)

    const result = await fileInterventionFalsifier(baseInput({ event_class: 'ayurdaya_window' }), TEST_PRINCIPAL)

    expect(result.state).toBe('filing_failed')
    expect(result.filing_ready_payload).toBeNull()
    expect(result.detail).toMatch(/3\.5\.C/)
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('refuses when the mortality language is in the claim/falsifier text, not just event_class', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)

    const result = await fileInterventionFalsifier(
      baseInput({ falsifier: 'No maraka-dasha longevity event recorded.' }),
      TEST_PRINCIPAL
    )

    expect(result.state).toBe('filing_failed')
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('the mortality exclusion is NOT unlocked by any adoption_basis — still refuses under native_directed', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)

    const result = await fileInterventionFalsifier(
      baseInput({ event_class: 'longevity_forecast', adoption_basis: 'native_directed' }),
      TEST_PRINCIPAL
    )

    expect(result.state).toBe('filing_failed')
    expect(fetchSpy).not.toHaveBeenCalled()
  })
})

// ── The one network call, and error handling ────────────────────────────────────────

describe('fileInterventionFalsifier — the sanctioned network call', () => {
  it('sends action=prospective_ledger_file with chart_id and entry, filed_by NOT included client-side', async () => {
    let capturedBody: Record<string, unknown> | null = null
    const fetchSpy = vi.fn(async (url: string, init?: RequestInit) => {
      capturedBody = JSON.parse(String(init?.body ?? '{}'))
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          trace_id: 't1',
          epistemics: { surgical: true, confidence_band: 'medium', horizon_days: 14, falsifier: 'x' },
          result: { prediction: { prediction_id: 'pred-abc' } },
          citations: [],
          plan: null,
          predictions_logged: [],
          synthesis_audit: null,
          suggested_followups: [],
        }),
        text: async () => '',
      }
    })
    vi.stubGlobal('fetch', fetchSpy)

    const result = await fileInterventionFalsifier(baseInput(), TEST_PRINCIPAL)

    expect(result.state).toBe('filed')
    expect(result.prediction_id).toBe('pred-abc')
    expect(String(fetchSpy.mock.calls[0]?.[0])).toContain('/api/mcp/writes/prospective_ledger_file')
    const body = capturedBody as unknown as { chart_id: string; entry: Record<string, unknown> }
    expect(body.chart_id).toBe(CHART_ID)
    expect(body.entry['event_class']).toBe('career_promotion')
    expect(body.entry['claim_shape']).toBe('interval')
    expect(body.entry['generator_class']).toBe('engine')
    expect('filed_by' in body.entry).toBe(false)
  })

  it('a server-side rejection (e.g. !envelope.ok) reports filing_failed with the verbatim error, never a fabricated filed:true', async () => {
    const fetchSpy = vi.fn(async () => ({
      ok: true,
      status: 400,
      json: async () => ({
        ok: false,
        trace_id: 't1',
        error: { class: 'validation', message: 'unknown event_class not_a_real_class' },
      }),
      text: async () => '',
    }))
    vi.stubGlobal('fetch', fetchSpy)

    const result = await fileInterventionFalsifier(baseInput(), TEST_PRINCIPAL)

    expect(result.state).toBe('filing_failed')
    expect(result.prediction_id).toBeNull()
    expect(result.detail).toMatch(/unknown event_class/)
  })

  it('a network error is caught and reported as filing_failed, never thrown to the caller', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => {
      throw new Error('network unreachable')
    }))

    const result = await fileInterventionFalsifier(baseInput(), TEST_PRINCIPAL)

    expect(result.state).toBe('filing_failed')
    expect(result.detail).toMatch(/network unreachable/)
  })
})

// ── recordInterventionLedgerEntry — the serve-time mimamsa_intervention_ledger write path ──

describe('recordInterventionLedgerEntry — the sanctioned intervention_ledger_record call (item 42 / gate G7)', () => {
  function baseLedgerInput(overrides: Partial<RecordInterventionLedgerInput> = {}): RecordInterventionLedgerInput {
    return {
      chart_id: CHART_ID,
      intent: 'Adopt the Shani propitiation targeting the confirmation block.',
      intervention_class: 'upaya',
      rite_or_activity_class: 'phala_mitigation:pm-1',
      event_class: 'career_promotion',
      window: { start: '2026-09-01T00:00:00Z', end: '2027-01-01T00:00:00Z' },
      precision_regime: 'day_grade',
      precision_basis: 'caller-stated adoption window',
      adjudication_record: { kind: 'upaya_adoption', failing_link: 'confirmation' },
      score_vector: { factors_present: [] },
      efficacy_tier: 'classically_attested',
      source_citation: 'BPHS 27.4',
      paddhati_version: 'none_applied_upaya_adoption',
      predicted_differential: 'adopted upāya window vs no-intervention baseline',
      prediction_id: 'pred-abc',
      adoption_basis: 'native_directed',
      authority_basis: 'pact_query:denied_at_confirmation',
      engine_version: 'upaya_setu_v1',
      ...overrides,
    }
  }

  it('sends action=intervention_ledger_record with chart_id + flattened window, filed_by NOT included client-side', async () => {
    let capturedBody: Record<string, unknown> | null = null
    const fetchSpy = vi.fn(async (_url: string, init?: RequestInit) => {
      capturedBody = JSON.parse(String(init?.body ?? '{}'))
      return {
        ok: true, status: 200,
        json: async () => ({ ok: true, trace_id: 't1', result: { intervention_id: 'iv-abc', created: true } }),
        text: async () => '',
      }
    })
    vi.stubGlobal('fetch', fetchSpy)

    const result = await recordInterventionLedgerEntry(baseLedgerInput(), TEST_PRINCIPAL)

    expect(result.recorded).toBe(true)
    expect(result.intervention_id).toBe('iv-abc')
    expect(result.created).toBe(true)
    expect(String(fetchSpy.mock.calls[0]?.[0])).toContain('/api/mcp/writes/intervention_ledger_record')
    const body = capturedBody as unknown as { chart_id: string; entry: Record<string, unknown> }
    expect(body.chart_id).toBe(CHART_ID)
    expect(body.entry['window_start']).toBe('2026-09-01T00:00:00Z')
    expect(body.entry['window_end']).toBe('2027-01-01T00:00:00Z')
    expect(body.entry['prediction_id']).toBe('pred-abc')
    expect(body.entry['adoption_basis']).toBe('native_directed')
    expect('filed_by' in body.entry).toBe(false)
    expect('window' in body.entry).toBe(false)
  })

  it('idempotent re-record: created:false with the existing row id is reported, never an error', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true, status: 200,
      json: async () => ({ ok: true, trace_id: 't1', result: { intervention_id: 'iv-existing', created: false } }),
      text: async () => '',
    })))
    const result = await recordInterventionLedgerEntry(baseLedgerInput(), TEST_PRINCIPAL)
    expect(result.recorded).toBe(true)
    expect(result.created).toBe(false)
    expect(result.intervention_id).toBe('iv-existing')
  })

  it('§5.4 defence in depth: a mortality-shaped intent/event_class/differential is refused with NO network call', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)
    for (const overrides of [
      { event_class: 'ayurdaya_window' },
      { intent: 'time the maraka dasha' },
      { predicted_differential: 'longevity improvement vs baseline' },
    ] as Partial<RecordInterventionLedgerInput>[]) {
      const result = await recordInterventionLedgerEntry(baseLedgerInput(overrides), TEST_PRINCIPAL)
      expect(result.recorded).toBe(false)
      expect(result.detail).toMatch(/mortality/i)
    }
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('a server-side rejection surfaces the VERBATIM error (e.g. a CHECK/FK violation), never a fabricated recorded:true', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true, status: 400,
      json: async () => ({ ok: false, trace_id: 't1', error: { class: 'validation', message: 'violates check constraint "mimamsa_intervention_ledger_inferred_never_sealed"' } }),
      text: async () => '',
    })))
    const result = await recordInterventionLedgerEntry(baseLedgerInput(), TEST_PRINCIPAL)
    expect(result.recorded).toBe(false)
    expect(result.detail).toMatch(/inferred_never_sealed/)
  })

  it('ok=true with no resolvable intervention_id is an honest failure (§N.8: no detector, no green)', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true, status: 200,
      json: async () => ({ ok: true, trace_id: 't1', result: {} }),
      text: async () => '',
    })))
    const result = await recordInterventionLedgerEntry(baseLedgerInput(), TEST_PRINCIPAL)
    expect(result.recorded).toBe(false)
    expect(result.detail).toMatch(/no resolvable intervention_id/)
  })

  it('a network error is caught and reported, never thrown to the caller', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => {
      throw new Error('network unreachable')
    }))
    const result = await recordInterventionLedgerEntry(baseLedgerInput(), TEST_PRINCIPAL)
    expect(result.recorded).toBe(false)
    expect(result.detail).toMatch(/network unreachable/)
  })
})

// ── G14b — the live non-vacuity twin (DB-integration gated; skipped by default) ─────

const describeIntegration = process.env['RUN_DB_INTEGRATION'] === '1' ? describe : describe.skip

describeIntegration('resolveWithholdEventClassesLive — G14b live non-vacuity (requires reachable platform)', () => {
  it('resolves to a non-empty set that matches WITHHOLD_EVENT_CLASSES exactly', async () => {
    const live = await resolveWithholdEventClassesLive(TEST_PRINCIPAL)
    expect(live.size).toBeGreaterThan(0)
    expect(live).toEqual(new Set(WITHHOLD_EVENT_CLASSES))
  })
})

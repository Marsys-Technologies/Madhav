/**
 * kala_ahead_get_f110_promise_gate.test.ts — F-110 (CL-15 Cross-tool incoherence,
 * TIER1-CORRECTNESS): "CONFIDENCE LAUNDERING".
 *
 * THE DEFECT UNDER TEST. For the identical chart/domain/date, `kala_ahead_get` served a
 * `tier_1_high` relationship projection for 2027-10-20..2030-04-03 narrated "High
 * probability (>=70% convergence, clear activation)" with `reading.dissent: []` and
 * `evidence[0].strength: 'strong'`, while `pact_query`/`kala_upaya_get` on the SAME server
 * returned `pact_status: 'denied_at_promise'` — "the rāśi checklist does not promise this
 * matter" — on 63 cited L1 facts. Which verdict a real person received depended entirely
 * on which tool the consuming LLM picked.
 *
 * Design contract (rejected alternatives, stage-scope table, escalated rulings):
 * `00_ARCHITECTURE/briefs/parisesa/F110_PACT_GATING_DESIGN_CONTRACT_v1_0.md`.
 *
 * Gates:
 *   ✓ A2  the PACT denial is surfaced on the response (promise_gate)
 *   ✓ A3  reading.dissent is non-empty when the chain contradicts
 *   ✓ A4  §N.5 — probability_tier / narrative / max_effective_score pass through
 *         BYTE-IDENTICAL. The fix must never re-grade an L3-computed value.
 *   ✓ §N.7 — this file's OWN narration (thesis / verdict / evidence.strength) stops
 *         asserting a consensus the server does not hold
 *   ✓ A5  a denied_at_activation (as-of-date-scoped) does NOT gate a forward horizon
 *   ✓ A6  the promise_gated_forecasting coverage row varies with real input (§N.8 —
 *         it was an unconditional hardcoded `not_in_corpus` before)
 *   ✓ A7  unchecked ≠ clean: an unreachable/not-applicable gate is distinguishable
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../types.js'
import { computeKalaAhead } from '../tools/kala_views/ahead.js'

const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'
const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }

/** The exact laundering row from the live reproducer on the canonical chart. */
const RELATIONSHIP_PROJECTION = {
  window_start: '2027-10-20',
  window_end: '2030-04-03',
  domain: 'relationship',
  member_count: 2,
  member_ids: ['4346', '4368'],
  member_signal_ids: ['2b9a44d4-b7f2-404a-9cda-05572c1b410d', '17a138c3-a839-431f-b4b4-8070172ec3e8'],
  probability_tier: 'tier_1_high' as const,
  max_effective_score: 0.7,
  narrative: {
    caveat: 'This projection is probabilistic and calibrated. Record actual outcomes at evaluation_date for calibration refinement.',
    headline: 'Relationship activation near 2027-10-20',
    domain_context: 'Domain: relationship. Cycle type: 2.5-year cycle.',
    probability_statement: 'High probability (>=70% convergence, clear activation). Effective convergence: 0.70. Confidence: moderate.',
  },
  source_citation: 'ka_bhavishya_lekha:v1.0:rank=17',
}

interface MockOpts {
  /** pact_query outcome: a status string, 'unreachable', or 'no_status' (200 w/ no pact_status). */
  pact: string | 'unreachable' | 'no_status'
  projections?: Array<Record<string, unknown>>
  factIdRefs?: string[]
}

function mockRegistryFetch(opts: MockOpts) {
  return vi.fn(async (_url: string, init?: RequestInit) => {
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri: string }
    let inner: Record<string, unknown> = {}
    if (body.uri === 'marsys://tool/L3/query_temporal_activation') {
      inner = { window_families: [], forward_windows: [], activations: [] }
    } else if (body.uri === 'marsys://tool/L3/query_projections') {
      inner = { projection_families: opts.projections ?? [RELATIONSHIP_PROJECTION] }
    } else if (body.uri === 'marsys://tool/L0/call_panchanga_service') {
      inner = { panchangs: [], count: 0 }
    } else if (body.uri === 'marsys://tool/L-PACT/pact_query') {
      if (opts.pact === 'unreachable') throw new Error('L-PACT unreachable in test')
      inner = opts.pact === 'no_status'
        ? { about: { domain: 'relationship', bhava: 7 } }
        : {
            chart_id: TEST_CHART_ID,
            about: { domain: 'relationship', bhava: 7, karakas: ['Venus'], operative_varga: 'D9' },
            pact_status: opts.pact,
            stages: [{ stage: 'PROMISE', status: opts.pact === 'denied_at_promise' ? 'denied' : 'passed' }],
            fact_id_refs: opts.factIdRefs ?? ['d332fe1dbda74ea0', 'e8e5300adea7bc58'],
          }
    }
    return {
      ok: true,
      json: async () => ({ ok: true, content: { content: inner, is_error: false } }),
      text: async () => '',
    } as Response
  })
}

beforeEach(() => {
  vi.unstubAllGlobals()
})

describe('F-110 — a PACT promise denial is surfaced, never silently omitted', () => {
  it('A2: promise_gate carries the verbatim denial for the queried domain', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ pact: 'denied_at_promise' }))
    const r = await computeKalaAhead(TEST_CHART_ID, { domain: 'relationship', horizon_years: 10 }, TEST_PRINCIPAL)

    expect(r.promise_gate.state).toBe('checked')
    expect(r.promise_gate.pact_status).toBe('denied_at_promise')
    expect(r.promise_gate.domain).toBe('relationship')
    // INV-1 (promise_spine.ts): denied_at_* → 'contradicts', no override path.
    expect(r.promise_gate.join?.stance).toBe('contradicts')
    expect(r.promise_gate.join?.projection).toBe('contradicted')
    expect(r.promise_gate.gating_scope).toBe('horizon_invariant')
    expect(r.promise_gate.contradicts_served_projections).toBe(true)
  })

  it('A3: reading.dissent is populated — the hardcoded `[]` asserted no dissent existed', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ pact: 'denied_at_promise' }))
    const r = await computeKalaAhead(TEST_CHART_ID, { domain: 'relationship', horizon_years: 10 }, TEST_PRINCIPAL)

    expect(r.reading.dissent.length).toBeGreaterThan(0)
    expect(r.reading.dissent[0]!.source).toContain('PACT promise chain')
    expect(r.reading.dissent[0]!.claim).toMatch(/denied at PROMISE/i)
    expect(r.reading.dissent[0]!.fact_ids).toContain('d332fe1dbda74ea0')
  })

  it('§N.7: this tool stops narrating "strong"/"high probability" as an unqualified consensus', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ pact: 'denied_at_promise' }))
    const r = await computeKalaAhead(TEST_CHART_ID, { domain: 'relationship', horizon_years: 10 }, TEST_PRINCIPAL)

    // evidence.strength is THIS FILE's composition (TIER_TO_STRENGTH), not L3's value.
    // §N.7 item 6: an honest null, which is this file's own established ungraded value —
    // never an invented lower grade.
    const ev = r.reading.evidence.find((e) => e.claim.includes('relationship'))!
    expect(ev.strength).toBeUndefined()
    expect(ev.claim).toContain('CONTRADICTED')
    expect(r.reading.thesis).toContain('CONTRADICTED AT PROMISE')
    expect(r.reading.verdict.statement).toMatch(/denied_at_promise/)
    // The prose a caller might read alone must carry it too.
    expect(r.reading_prose).toContain('CONTRADICTED AT PROMISE')
  })

  it('A4 (§N.5): the L3-computed tier, narrative and score pass through BYTE-IDENTICAL', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ pact: 'denied_at_promise' }))
    const r = await computeKalaAhead(TEST_CHART_ID, { domain: 'relationship', horizon_years: 10 }, TEST_PRINCIPAL)

    // The fix reconciles ADJACENTLY. It must never re-grade an L3 value — that would be
    // the MSR_COMPUTED_VALUE_DRIFT authority inversion, and any substituted tier would be
    // a number with no detector behind it (§N.8).
    const p = r.projections[0]!
    expect(p['probability_tier']).toBe('tier_1_high')
    expect(p['max_effective_score']).toBe(0.7)
    expect(p['narrative']).toEqual(RELATIONSHIP_PROJECTION.narrative)
    expect(JSON.stringify(p)).toBe(JSON.stringify(RELATIONSHIP_PROJECTION))
  })

  it('A6 (§N.8): promise_gated_forecasting coverage is now computed, not a hardcoded not_in_corpus', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ pact: 'denied_at_promise' }))
    const r = await computeKalaAhead(TEST_CHART_ID, { domain: 'relationship', horizon_years: 10 }, TEST_PRINCIPAL)
    const entry = r.coverage.find((c) => c.concept === 'promise_gated_forecasting')!
    expect(entry.state).toBe('computed')
  })
})

describe('F-110 §4.2 — stage scope: only a timeless denial gates a forward horizon', () => {
  it('A5: denied_at_activation is as-of-date-scoped and does NOT gate a 2030 window', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ pact: 'denied_at_activation' }))
    const r = await computeKalaAhead(TEST_CHART_ID, { domain: 'relationship', horizon_years: 10 }, TEST_PRINCIPAL)

    // The denial is still REPORTED verbatim (B.10 — nothing dropped)...
    expect(r.promise_gate.pact_status).toBe('denied_at_activation')
    expect(r.promise_gate.join?.stance).toBe('contradicts')
    // ...but it is not applied as a gate: which daśā runs on one date says nothing about
    // a window years later. Applying it would be a SECOND correctness defect.
    expect(r.promise_gate.gating_scope).toBe('as_of_date_only')
    expect(r.promise_gate.contradicts_served_projections).toBe(false)
    expect(r.reading.dissent).toEqual([])
    expect(r.promise_gate.reason).toMatch(/NOT applied as a gate/)
  })

  it('denied_at_confirmation IS horizon-invariant (varga dignity is timeless)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ pact: 'denied_at_confirmation' }))
    const r = await computeKalaAhead(TEST_CHART_ID, { domain: 'relationship', horizon_years: 10 }, TEST_PRINCIPAL)
    expect(r.promise_gate.gating_scope).toBe('horizon_invariant')
    expect(r.promise_gate.contradicts_served_projections).toBe(true)
  })

  it.each(['chain_complete', 'chain_pending_activation', 'chain_incomplete_infra'])(
    '%s is not a denial and gates nothing',
    async (status) => {
      vi.stubGlobal('fetch', mockRegistryFetch({ pact: status }))
      const r = await computeKalaAhead(TEST_CHART_ID, { domain: 'relationship', horizon_years: 10 }, TEST_PRINCIPAL)
      expect(r.promise_gate.gating_scope).toBe('none')
      expect(r.promise_gate.contradicts_served_projections).toBe(false)
      expect(r.reading.dissent).toEqual([])
      expect(r.reading.evidence[0]!.strength).toBe('strong')
    },
  )
})

describe('F-110 A7 — unchecked is never presented as clean', () => {
  it('an unreachable PACT capability yields honest_empty coverage + a null join, not a pass', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ pact: 'unreachable' }))
    const r = await computeKalaAhead(TEST_CHART_ID, { domain: 'relationship', horizon_years: 10 }, TEST_PRINCIPAL)

    expect(r.promise_gate.state).toBe('unreachable')
    // §N.8: never fabricate a permissive join to fill the slot.
    expect(r.promise_gate.join).toBeNull()
    expect(r.promise_gate.contradicts_served_projections).toBe(false)
    expect(r.promise_gate.reason).toMatch(/not the same as checked-and-clear/)
    expect(r.coverage.find((c) => c.concept === 'promise_gated_forecasting')!.state).toBe('honest_empty')
    expect(r.reading.verdict.statement).toContain('NOT CHECKED')
    expect(r.provenance_envelope.promise_gate_reachable).toBe(false)
  })

  it('a 200 response carrying no pact_status is unreachable, not a silent pass', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ pact: 'no_status' }))
    const r = await computeKalaAhead(TEST_CHART_ID, { domain: 'relationship', horizon_years: 10 }, TEST_PRINCIPAL)
    expect(r.promise_gate.state).toBe('unreachable')
    expect(r.promise_gate.join).toBeNull()
  })

  it('no domain and no domain-labelled projection ⇒ not_applicable, explicitly not a clean bill', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ pact: 'denied_at_promise', projections: [] }))
    const r = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(r.promise_gate.state).toBe('not_applicable')
    expect(r.promise_gate.reason).toMatch(/Not a clean bill of health/)
    expect(r.coverage.find((c) => c.concept === 'promise_gated_forecasting')!.state).toBe('not_in_corpus')
  })

  it('with no `domain` filter the gate falls back to the LEADING projection\'s own domain', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ pact: 'denied_at_promise' }))
    const r = await computeKalaAhead(TEST_CHART_ID, { horizon_years: 10 }, TEST_PRINCIPAL)
    expect(r.promise_gate.domain).toBe('relationship')
    expect(r.promise_gate.contradicts_served_projections).toBe(true)
  })

  it('§N.6: projection domains NOT vetted are named, never implied clean', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({
      pact: 'denied_at_promise',
      projections: [RELATIONSHIP_PROJECTION, { ...RELATIONSHIP_PROJECTION, domain: 'career' }],
    }))
    const r = await computeKalaAhead(TEST_CHART_ID, { domain: 'relationship', horizon_years: 10 }, TEST_PRINCIPAL)
    expect(r.promise_gate.gated_projection_domains).toEqual(['relationship'])
    expect(r.promise_gate.ungated_projection_domains).toEqual(['career'])
    // The unvetted career projection keeps its tier-derived strength — it was not judged.
    expect(r.reading.evidence.find((e) => e.claim.startsWith('career'))!.strength).toBe('strong')
  })
})

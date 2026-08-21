/**
 * F-175 — assess_* PACT promise gate: unit tests
 *
 * Test contract (mirrors the finding's own three obligations):
 *   (a) THE DEFECT REPRODUCES. The pre-fix verdict prose — the real, verbatim string
 *       assess_marriage served on 2026-08-21 for the canonical chart — certifies a
 *       domain-scoped contradiction absence with no mention of the PACT denial. Asserted
 *       here against the UNGATED path (gate=null), which is byte-for-byte what every
 *       assess_* call did before this module existed. That path is still exercised, so this
 *       is a live mutation test, not a snapshot of deleted code: delete the gate wiring in
 *       registry_bridge.ts and the served response reverts to exactly this string.
 *   (b) THE FIX SURFACES IT. With a real denied_at_promise chain, the certification can no
 *       longer stand as an all-clear, a promise_chain clause leads the favourable findings,
 *       kernel.promise is populated, and the flag fires.
 *   (c) NO OVER-CORRECTION. chain_complete / chain_pending_activation leave the prose
 *       BYTE-IDENTICAL — a clean domain still reads clean, non-alarmist. An unreachable
 *       chain changes no prose either, but is disclosed as unchecked (never as clean).
 */

import { describe, it, expect } from 'vitest'
import {
  buildAssessPromiseGate,
  applyPromiseGateToVerdict,
  annotateContradictionsWithPromiseGate,
  promiseGateFlags,
} from './assess_promise_gate.js'
import { judgmentFlagsInclude, judgmentFlag } from '../generated/envelope.js'
import { assembleSaraContent, KERNEL_FLOOR_FLAG_CODES } from './response_budget.js'

// ── fixtures ─────────────────────────────────────────────────────────────────

/** The 63 L1 fact_ids the live denial cited (first 3 — the shape is what matters here). */
const DENIAL_FACT_IDS = ['e8e5300adea7bc58', '61ff5df8420a8b45', '3bdb8ce78eea8618']

function pactResponse(pact_status: string, fact_id_refs: string[] = DENIAL_FACT_IDS) {
  return {
    pact_status,
    stages: [{ stage: 'PROMISE', status: pact_status.startsWith('denied') ? 'denied' : 'ok' }],
    fact_id_refs,
  }
}

/**
 * The verdict layer assess_marriage actually produced for chart 482012f1 on 2026-08-21,
 * reconstructed clause-by-clause from the live response (see the PR body for the raw
 * envelope). The contradiction clause is the F-175 defect, verbatim.
 */
const CERTIFICATION_TEXT =
  'No contradictions are tagged to this domain specifically (3 exist chart-wide) — ' +
  'an honest domain-scoped absence, not a silent omission.'

function liveMarriageVerdict() {
  return {
    clauses: [
      {
        text: 'Marriage / Partnership assessment draws on 10 composite-ranked signal(s) for this chart, ' +
          'cross-referenced against classical yoga firings, varga placements, contradictions, and dasha timing below.',
        fact_ids: ['3588a51b37aefd51'],
        grounded: true,
        clause_id: 'overview',
      },
      {
        text: 'Significator condition (D1): Saturn (7th house occupant) is exalted in Libra — ṣaḍbala 7.83, rank 2/9.',
        fact_ids: ['a474d495e002faba'],
        grounded: true,
        clause_id: 'significator_condition',
      },
      { text: CERTIFICATION_TEXT, fact_ids: [], grounded: false, clause_id: 'contradictions' },
      {
        text: "A dated daśā-activation window is available for this domain's signals — see activating_dasha for the exact bounds.",
        fact_ids: [],
        grounded: false,
        clause_id: 'timing',
      },
    ],
    sentence_count: 4,
    fact_ids_cited: ['3588a51b37aefd51', 'a474d495e002faba'],
    template: 'deterministic_v1',
    note: 'Composed by a fixed string template over already-graded terms.',
  }
}

/** Flatten a verdict layer the way registry_bridge's assessmentVerdictText does. */
function flatten(value: unknown): string {
  const layer = value as { clauses?: Array<{ text?: string }> }
  return (layer.clauses ?? []).map(c => c.text ?? '').join(' ')
}

// ── (a) the defect reproduces on the ungated path ────────────────────────────

describe('F-175 (a) — the pre-fix defect reproduces', () => {
  it('UNGATED: the verdict certifies a domain-scoped contradiction absence, silent on any denial', () => {
    // This is exactly what registry_bridge did before F-175: no gate consulted at all.
    const prose = flatten(applyPromiseGateToVerdict(liveMarriageVerdict(), null))

    expect(prose).toContain(CERTIFICATION_TEXT)
    // The affirmative false-clean claim, unqualified:
    expect(prose).toContain('an honest domain-scoped absence')
    // …and nothing anywhere naming the denial the same server holds on 63 L1 facts:
    expect(prose).not.toContain('denied_at_promise')
    expect(prose).not.toContain('PROMISE CHAIN')
    expect(prose).not.toContain('NOT A CLEAN BILL OF HEALTH')
  })

  it('UNGATED: no flag discloses that the promise chain was never consulted', () => {
    expect(promiseGateFlags(null)).toEqual([])
  })
})

// ── (b) the fix surfaces the real contradiction ──────────────────────────────

describe('F-175 (b) — a real PACT denial is surfaced, not laundered', () => {
  const gate = buildAssessPromiseGate('relationship', pactResponse('denied_at_promise'))

  it('the gate reads the denial verbatim and sets contradicts_domain_assessment', () => {
    expect(gate.state).toBe('checked')
    expect(gate.pact_status).toBe('denied_at_promise')
    expect(gate.join?.stance).toBe('contradicts') // INV-1, no override path
    expect(gate.join?.projection).toBe('contradicted')
    expect(gate.contradicts_domain_assessment).toBe(true)
  })

  it('the certification can no longer stand as an all-clear', () => {
    const prose = flatten(applyPromiseGateToVerdict(liveMarriageVerdict(), gate))

    // §N.5 / disclosure-not-suppression: the L2 finding is NOT deleted or restated.
    expect(prose).toContain('No contradictions are tagged to this domain specifically (3 exist chart-wide)')
    // But it is no longer readable as a domain all-clear.
    expect(prose).toContain('NOT A CLEAN BILL OF HEALTH')
    expect(prose).toContain('denied_at_promise')
  })

  it('the denial leads the favourable findings (clause order), not trails them', () => {
    const gated = applyPromiseGateToVerdict(liveMarriageVerdict(), gate) as {
      clauses: Array<{ clause_id?: string; fact_ids?: string[] }>
    }
    const ids = gated.clauses.map(c => c.clause_id)
    expect(ids[0]).toBe('overview')
    expect(ids[1]).toBe('promise_chain')
    // The exalted-Saturn sentence — the most favourable line in the response — now reads
    // AFTER the denial, never before it.
    expect(ids.indexOf('promise_chain')).toBeLessThan(ids.indexOf('significator_condition'))
  })

  it('the promise clause inherits the denial L1 fact_ids (§N.5), never re-derives them', () => {
    const gated = applyPromiseGateToVerdict(liveMarriageVerdict(), gate) as {
      clauses: Array<{ clause_id?: string; fact_ids?: string[]; grounded?: boolean }>
      fact_ids_cited: string[]
    }
    const clause = gated.clauses.find(c => c.clause_id === 'promise_chain')
    expect(clause?.fact_ids).toEqual(DENIAL_FACT_IDS)
    expect(clause?.grounded).toBe(true)
    expect(gated.fact_ids_cited).toEqual(expect.arrayContaining(DENIAL_FACT_IDS))
  })

  it('emits the budget-protected kernel flag', () => {
    const flags = promiseGateFlags(gate)
    expect(judgmentFlagsInclude(flags, 'promise_chain_contradicts_domain')).toBe(true)
    expect(flags[0]).toMatchObject({ severity: 'warning' })
  })

  it('annotates the L2 contradictions object without falsifying its status (§N.5)', () => {
    const annotated = annotateContradictionsWithPromiseGate(
      { status: 'no_contradictions_in_domain', chart_wide_contradiction_count: 3 },
      gate,
    ) as Record<string, unknown>
    // The L2 status is TRUE about bodha_contradictions and is left exactly as computed.
    expect(annotated['status']).toBe('no_contradictions_in_domain')
    expect(annotated['chart_wide_contradiction_count']).toBe(3)
    // The adjacent field is what makes an all-clear reading unavailable.
    expect(annotated['not_a_domain_all_clear']).toBe(true)
    expect((annotated['promise_chain'] as Record<string, unknown>)['pact_status']).toBe('denied_at_promise')
  })

  it.each(['denied_at_confirmation', 'denied_at_activation'])(
    'a %s denial contradicts too (INV-1 applies at every stage)',
    status => {
      const g = buildAssessPromiseGate('relationship', pactResponse(status))
      expect(g.contradicts_domain_assessment).toBe(true)
      expect(flatten(applyPromiseGateToVerdict(liveMarriageVerdict(), g))).toContain(status)
    },
  )
})

// ── (c) no over-correction into false positives ──────────────────────────────

describe('F-175 (c) — a genuinely clean domain still reads clean', () => {
  it('chain_complete leaves the verdict prose BYTE-IDENTICAL and raises no flag', () => {
    const gate = buildAssessPromiseGate('career', pactResponse('chain_complete'))
    expect(gate.contradicts_domain_assessment).toBe(false)
    expect(gate.join?.stance).toBe('consistent')

    const before = liveMarriageVerdict()
    const after = applyPromiseGateToVerdict(before, gate)
    expect(after).toEqual(before)
    expect(flatten(after)).toBe(flatten(before))
    expect(promiseGateFlags(gate)).toEqual([])
  })

  it('chain_pending_activation is not a denial — no prose change, no alarm', () => {
    const gate = buildAssessPromiseGate('career', pactResponse('chain_pending_activation'))
    expect(gate.contradicts_domain_assessment).toBe(false)
    expect(gate.join?.stance).toBe('pending')
    expect(applyPromiseGateToVerdict(liveMarriageVerdict(), gate)).toEqual(liveMarriageVerdict())
    expect(promiseGateFlags(gate)).toEqual([])
  })

  it('chain_incomplete_infra (an infra gap, NOT a classical denial) raises no contradiction', () => {
    const gate = buildAssessPromiseGate('career', pactResponse('chain_incomplete_infra'))
    expect(gate.contradicts_domain_assessment).toBe(false)
    expect(applyPromiseGateToVerdict(liveMarriageVerdict(), gate)).toEqual(liveMarriageVerdict())
  })

  it('a clean domain leaves the L2 contradictions object untouched', () => {
    const gate = buildAssessPromiseGate('career', pactResponse('chain_complete'))
    const input = { status: 'no_contradictions_in_domain', chart_wide_contradiction_count: 3 }
    expect(annotateContradictionsWithPromiseGate(input, gate)).toEqual(input)
  })
})

// ── §N.8: unchecked is never smoothed into clean (F-110 A7) ──────────────────

describe('F-175 — honest-null discipline', () => {
  it('an unreachable chain yields a null join, never a permissive default', () => {
    const gate = buildAssessPromiseGate('relationship', null, 'ECONNREFUSED')
    expect(gate.state).toBe('unreachable')
    expect(gate.join).toBeNull()
    expect(gate.pact_status).toBeNull()
    expect(gate.contradicts_domain_assessment).toBe(false)
    expect(gate.reason).toContain('ECONNREFUSED')
    expect(gate.reason).toContain('not the same as checked-and-clear')
  })

  it('unreachable is DISCLOSED — a caller can distinguish it from checked-and-clear', () => {
    const unreachable = promiseGateFlags(buildAssessPromiseGate('relationship', null, 'timeout'))
    const clear = promiseGateFlags(buildAssessPromiseGate('relationship', pactResponse('chain_complete')))
    expect(judgmentFlagsInclude(unreachable, 'promise_chain_unchecked')).toBe(true)
    expect(clear).toEqual([])
    expect(unreachable).not.toEqual(clear) // the F-110 A7 criterion, for assess_*
  })

  it('a non-PACT response (no pact_status) is unreachable, not a fabricated join (§N.8)', () => {
    const gate = buildAssessPromiseGate('relationship', { some: 'other shape' })
    expect(gate.state).toBe('unreachable')
    expect(gate.join).toBeNull()
  })

  it('unreachable does NOT touch the verdict prose (no invented alarm either way)', () => {
    const gate = buildAssessPromiseGate('relationship', null, 'timeout')
    expect(applyPromiseGateToVerdict(liveMarriageVerdict(), gate)).toEqual(liveMarriageVerdict())
  })

  it('unwraps the MCP content-wrapper envelope shape', () => {
    const gate = buildAssessPromiseGate('relationship', { content: pactResponse('denied_at_promise'), is_error: false })
    expect(gate.pact_status).toBe('denied_at_promise')
    expect(gate.contradicts_domain_assessment).toBe(true)
  })
})

// ── shape robustness ─────────────────────────────────────────────────────────

describe('F-175 — verdict shape robustness', () => {
  it('a plain-string verdict gets the denial prepended (no clause structure to target)', () => {
    const gate = buildAssessPromiseGate('relationship', pactResponse('denied_at_promise'))
    const out = applyPromiseGateToVerdict('Some legacy string verdict.', gate) as string
    expect(out.startsWith('PROMISE CHAIN CONTRADICTS THIS DOMAIN')).toBe(true)
    expect(out).toContain('Some legacy string verdict.')
  })

  it('a verdict with no contradictions clause still gets the promise clause', () => {
    const gate = buildAssessPromiseGate('relationship', pactResponse('denied_at_promise'))
    const layer = { clauses: [{ text: 'Overview only.', clause_id: 'overview', fact_ids: [], grounded: false }] }
    const out = applyPromiseGateToVerdict(layer, gate) as { clauses: Array<{ clause_id?: string }> }
    expect(out.clauses.map(c => c.clause_id)).toEqual(['overview', 'promise_chain'])
  })

  it('a clause array with no overview puts the promise clause first', () => {
    const gate = buildAssessPromiseGate('relationship', pactResponse('denied_at_promise'))
    const layer = { clauses: [{ text: CERTIFICATION_TEXT, clause_id: 'contradictions' }] }
    const out = applyPromiseGateToVerdict(layer, gate) as { clauses: Array<{ clause_id?: string }> }
    expect(out.clauses[0]?.clause_id).toBe('promise_chain')
  })

  it('null / malformed verdicts pass through without throwing', () => {
    const gate = buildAssessPromiseGate('relationship', pactResponse('denied_at_promise'))
    expect(applyPromiseGateToVerdict(null, gate)).toBeNull()
    expect(applyPromiseGateToVerdict({ no: 'clauses' }, gate)).toEqual({ no: 'clauses' })
    expect(applyPromiseGateToVerdict([], gate)).toEqual([])
  })
})

// ── §N.6 item 2: the kernel flag hardFloor (live-caught by this finding's wiring test) ──

describe('F-175 — kernel flag trimming has a hardFloor', () => {
  /** A verdict long enough to force the ≤2KB kernel trim loop to run. */
  const LONG_VERDICT = 'x'.repeat(1900)

  function kernelWith(flags: unknown[]) {
    return {
      verdict: LONG_VERDICT,
      flags,
      promise: null,
      pointers: [] as never[],
    } as never
  }

  it('a promise-chain denial survives while lower-density caveats are dropped', () => {
    // Order matters: the denial is pushed LAST, which under the pre-F-175 positional trim
    // (`flags.slice(0, -1)`) made it the FIRST discarded. This is the exact regression the
    // wiring test caught live on assess_career/assess_wealth.
    const assembled = assembleSaraContent({
      kernel: kernelWith([
        'complete_domain_accounting_attached: the full career concept slice is attached.',
        'domain_slice_not_configured: no precomputed slice is attached.',
        judgmentFlag('promise_chain_contradicts_domain', 'pact_query returns denied_at_promise.', 'warning'),
      ]),
      budget_kb: 40,
      counts: {},
    })
    const codes = (assembled.kernel.flags as Array<string | { code: string }>)
      .map(f => (typeof f === 'string' ? f.split(':')[0] : f.code))
    expect(codes).toContain('promise_chain_contradicts_domain')
    expect(codes).not.toContain('complete_domain_accounting_attached')
  })

  it('an unchecked-chain disclosure carries the same floor', () => {
    const assembled = assembleSaraContent({
      kernel: kernelWith([
        'complete_domain_accounting_attached: a long, low-density convenience note. '.repeat(4),
        judgmentFlag('promise_chain_unchecked', 'the chain could not be evaluated this call.', 'warning'),
      ]),
      budget_kb: 40,
      counts: {},
    })
    const codes = (assembled.kernel.flags as Array<string | { code: string }>)
      .map(f => (typeof f === 'string' ? f.split(':')[0] : f.code))
    expect(codes).toContain('promise_chain_unchecked')
  })

  it('the floor set is deliberately narrow — it is not "every caveat is immune"', () => {
    expect(KERNEL_FLOOR_FLAG_CODES.has('domain_inference_requires_acharya_validation')).toBe(false)
    expect(KERNEL_FLOOR_FLAG_CODES.has('bearing_yogas_no_domain_match')).toBe(false)
    expect(KERNEL_FLOOR_FLAG_CODES.has('promise_chain_contradicts_domain')).toBe(true)
  })
})

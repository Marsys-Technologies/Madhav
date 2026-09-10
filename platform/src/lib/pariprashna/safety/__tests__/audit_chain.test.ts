/**
 * Lane G1-A — the safety-decision hash chain (PPR-26).
 *
 * The chain's whole value is that it is a DETECTOR: there must be a real code
 * path on which the integrity signal reads FALSE (§N.8). So the tests that
 * matter are the tampering ones — edit a field, re-order the chain, forge a
 * link — and each must be named specifically, not merely "ok: false".
 */

import { describe, it, expect } from 'vitest'

import { safetyEntryHash, verifySafetyChain, type SafetyDecisionRow } from '../audit'

function link(seq: number, prevHash: string | null, overrides: Partial<SafetyDecisionRow> = {}): SafetyDecisionRow {
  const base = {
    decision_id: `d${seq}`,
    chart_id: 'chart-1',
    turn_id: `turn-${seq}`,
    seq,
    enforced: true,
    classes_detected: ['hs4_mortality_window'],
    severity: 'review_required',
    action: 'seal_pending_signoff',
    subject_kind: 'cohort',
    detections: [{ cls: 'hs4_mortality_window', rule: 'x' }],
    evasion_markers: [],
    excluded_capabilities: ['get_ayurdaya'],
    llm_assist_ran: false,
    review_id: null,
    recorded_at: `2026-08-19T12:0${seq}:00.000Z`,
    prev_hash: prevHash,
    ...overrides,
  }
  return {
    ...base,
    entry_hash: safetyEntryHash({
      chart_id: base.chart_id,
      turn_id: base.turn_id,
      seq: base.seq,
      action: base.action,
      severity: base.severity,
      classes_detected: base.classes_detected,
      detections: base.detections,
      recorded_at: base.recorded_at,
      prev_hash: base.prev_hash,
    }),
  } as SafetyDecisionRow
}

function chain(n: number): SafetyDecisionRow[] {
  const out: SafetyDecisionRow[] = []
  let prev: string | null = null
  for (let i = 1; i <= n; i++) {
    const l = link(i, prev)
    out.push(l)
    prev = l.entry_hash
  }
  return out
}

describe('an intact chain verifies', () => {
  it('reports ok with every link checked', () => {
    const v = verifySafetyChain(chain(4))
    expect(v.ok).toBe(true)
    expect(v.links_checked).toBe(4)
    expect(v.broken_at_seq).toBeNull()
    expect(v.reason).toBeNull()
  })
})

describe('an EMPTY chain is not evidence of anything, and says so', () => {
  it('reports ok with the explicit vacuous reason', () => {
    const v = verifySafetyChain([])
    expect(v.ok).toBe(true)
    expect(v.reason).toBe('empty_chain_is_vacuously_intact')
    expect(v.links_checked).toBe(0)
  })
})

describe('tampering is DETECTED and NAMED', () => {
  it('an edited action is caught at the edited link', () => {
    const c = chain(3)
    c[1] = { ...c[1], action: 'proceed' }
    const v = verifySafetyChain(c)
    expect(v.ok).toBe(false)
    expect(v.reason).toBe('entry_hash_does_not_match_content')
    expect(v.broken_at_seq).toBe(2)
  })

  it('an edited class list is caught', () => {
    const c = chain(3)
    c[2] = { ...c[2], classes_detected: [] }
    expect(verifySafetyChain(c).reason).toBe('entry_hash_does_not_match_content')
  })

  it('a DELETED middle link breaks the sequence', () => {
    const c = chain(4)
    c.splice(1, 1)
    const v = verifySafetyChain(c)
    expect(v.ok).toBe(false)
    expect(v.reason).toBe('sequence_not_contiguous_from_1')
  })

  it('a re-parented link is caught even when its own hash is self-consistent', () => {
    // The nastiest case: the attacker recomputes the entry hash after editing,
    // so the link verifies against itself. The PARENT pointer is what catches it.
    const c = chain(3)
    const forged = link(2, 'deadbeef'.repeat(8))
    c[1] = forged
    const v = verifySafetyChain(c)
    expect(v.ok).toBe(false)
    expect(v.reason).toBe('prev_hash_does_not_match_parent')
    expect(v.broken_at_seq).toBe(2)
  })

  it('a genesis link claiming a parent is caught', () => {
    const c = [link(1, 'a'.repeat(64)), ]
    expect(verifySafetyChain(c).reason).toBe('genesis_prev_hash_not_null')
  })
})

describe('the hash is order-insensitive on classes but sensitive on content', () => {
  it('class order does not change the hash (the set is what matters)', () => {
    const a = safetyEntryHash({
      chart_id: 'c', turn_id: 't', seq: 1, action: 'proceed', severity: 'none',
      classes_detected: ['hs1_date_of_death', 'hs4_mortality_window'],
      detections: [], recorded_at: 'x', prev_hash: null,
    })
    const b = safetyEntryHash({
      chart_id: 'c', turn_id: 't', seq: 1, action: 'proceed', severity: 'none',
      classes_detected: ['hs4_mortality_window', 'hs1_date_of_death'],
      detections: [], recorded_at: 'x', prev_hash: null,
    })
    expect(a).toBe(b)
  })

  it('a different severity is a different hash', () => {
    const a = safetyEntryHash({
      chart_id: 'c', turn_id: 't', seq: 1, action: 'proceed', severity: 'none',
      classes_detected: [], detections: [], recorded_at: 'x', prev_hash: null,
    })
    const b = safetyEntryHash({
      chart_id: 'c', turn_id: 't', seq: 1, action: 'proceed', severity: 'hard_stop',
      classes_detected: [], detections: [], recorded_at: 'x', prev_hash: null,
    })
    expect(a).not.toBe(b)
  })
})

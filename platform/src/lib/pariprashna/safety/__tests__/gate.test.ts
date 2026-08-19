/**
 * Lane G1-A — the SafetyPolicyGate itself.
 *
 * Three claims are tested here, and each is one this codebase has been burned
 * by asserting without a detector (§N.8):
 *   1. FLAG OFF IS A ZERO-COST NO-OP — measured by counting database calls, not
 *      by reading the code;
 *   2. `safety_decision` IS WRITTEN ON EVERY TURN, including the ones where
 *      nothing fired, because a table with only the firings has no denominator;
 *   3. `enforced: false` MEANS "not checked", never "checked and clean".
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

import { makeFakeSafetyDb } from './fake_db'

const flagState = { on: false }
vi.mock('../flag', () => ({
  SAFETY_GATE_FLAG: 'PARIPRASHNA_SAFETY_GATE_ENABLED',
  isSafetyGateEnabled: () => flagState.on,
}))

const { classifyTurnSafety, resolveAction, reclassifyAfterPlan } = await import('../gate')

let seq = 0
const newId = (): string => `00000000-0000-4000-8000-${String(++seq).padStart(12, '0')}`

beforeEach(() => {
  flagState.on = false
  seq = 0
})

const NOW = new Date('2026-08-19T12:00:00.000Z')

describe('flag OFF is a zero-cost no-op (measured, not claimed)', () => {
  it('touches no database and runs no pattern', async () => {
    const db = makeFakeSafetyDb()
    const d = await classifyTurnSafety({
      turnId: 't1',
      chartId: 'c1',
      queryText: 'When will I die?',
      subjectKind: 'native_self',
      db,
      now: NOW,
      newId,
    })
    expect(db.calls, 'flag OFF must issue ZERO database calls').toEqual([])
    expect(d.enforced).toBe(false)
    expect(d.action).toBe('proceed')
    expect(d.classes_detected).toEqual([])
    expect(d.audit_written).toBe(false)
  })

  it('`enforced: false` is the absence of a check, not a clean result', async () => {
    const db = makeFakeSafetyDb()
    const d = await classifyTurnSafety({
      turnId: 't1', chartId: 'c1', queryText: 'I want to kill myself.',
      subjectKind: null, db, now: NOW, newId,
    })
    // The single most dangerous possible misreading of this object: a receipt
    // that renders `classes_detected: []` as "the gate looked and found
    // nothing" when the gate never ran. `enforced` is the field that keeps the
    // two apart, and it reads false here on the most severe input there is.
    expect(d.enforced).toBe(false)
    expect(d.classes_detected).toEqual([])
  })
})

describe('flag ON — a decision is written on EVERY turn', () => {
  beforeEach(() => {
    flagState.on = true
  })

  it('a completely benign turn still writes its row', async () => {
    const db = makeFakeSafetyDb()
    const d = await classifyTurnSafety({
      turnId: 't1', chartId: 'c1',
      queryText: 'What does my chart say about my career this year?',
      subjectKind: 'native_self', db, now: NOW, newId,
    })
    expect(d.enforced).toBe(true)
    expect(d.action).toBe('proceed')
    expect(d.classes_detected).toEqual([])
    expect(d.audit_written).toBe(true)
    expect(db.rows.pariprashna_safety_decisions).toHaveLength(1)
    expect(db.rows.pariprashna_safety_decisions[0].action).toBe('proceed')
  })

  it('the chain increments seq and links prev_hash per chart', async () => {
    const db = makeFakeSafetyDb()
    for (const q of ['career?', 'marriage?', 'wealth?']) {
      await classifyTurnSafety({
        turnId: `t-${q}`, chartId: 'c1', queryText: q,
        subjectKind: 'native_self', db, now: NOW, newId,
      })
    }
    const written = db.rows.pariprashna_safety_decisions
    expect(written.map((r) => r.seq)).toEqual([1, 2, 3])
    expect(written[0].prev_hash).toBeNull()
    expect(written[1].prev_hash).toBe(written[0].entry_hash)
    expect(written[2].prev_hash).toBe(written[1].entry_hash)
  })

  it('an audit-write failure does NOT open the gate — the decision stands', async () => {
    const db = makeFakeSafetyDb()
    db.failNext = 99
    const d = await classifyTurnSafety({
      turnId: 't1', chartId: 'c1', queryText: 'When will I die?',
      subjectKind: 'native_self', db, now: NOW, newId,
    })
    // A gate that opened because its logger was down would be the worst
    // possible failure mode. The decision holds; the honest signal is the flag.
    expect(d.action).toBe('seal_pending_signoff')
    expect(d.audit_written).toBe(false)
  })
})

describe('HS-2 — hard stop, no plan, notification obligation', () => {
  beforeEach(() => {
    flagState.on = true
  })

  it('resolves to hard_stop and opens NO review (nothing to review)', async () => {
    const db = makeFakeSafetyDb()
    const d = await classifyTurnSafety({
      turnId: 't1', chartId: 'c1', queryText: 'I want to kill myself.',
      subjectKind: 'cohort', db, now: NOW, newId,
    })
    expect(d.action).toBe('hard_stop')
    expect(d.review_id).toBeNull()
    expect(db.rows.pariprashna_safety_reviews).toBeUndefined()
  })

  it('records the cohort-native notification obligation', async () => {
    const db = makeFakeSafetyDb()
    await classifyTurnSafety({
      turnId: 't1', chartId: 'c1', queryText: 'I want to kill myself.',
      subjectKind: 'cohort', db, now: NOW, newId,
    })
    expect(db.rows.pariprashna_safety_notifications).toHaveLength(1)
    expect(db.rows.pariprashna_safety_notifications[0].reason).toBe('cohort_subject_crisis_query')
  })

  it('does NOT notify for native_self — there is no third party to notify', async () => {
    const db = makeFakeSafetyDb()
    await classifyTurnSafety({
      turnId: 't1', chartId: 'c1', queryText: 'I want to kill myself.',
      subjectKind: 'native_self', db, now: NOW, newId,
    })
    expect(db.rows.pariprashna_safety_notifications).toBeUndefined()
  })

  it('an UNKNOWN subject_kind fails TOWARD notification', async () => {
    const db = makeFakeSafetyDb()
    await classifyTurnSafety({
      turnId: 't1', chartId: 'c1', queryText: 'I want to kill myself.',
      subjectKind: null, db, now: NOW, newId,
    })
    expect(db.rows.pariprashna_safety_notifications).toHaveLength(1)
    expect(db.rows.pariprashna_safety_notifications[0].reason).toBe(
      'subject_kind_unknown_fails_toward_notification',
    )
  })
})

describe('action resolution', () => {
  it('HS-2 outranks everything', () => {
    expect(
      resolveAction({
        classes: ['hs2_suicide_adjacent', 'hs3_health_crisis', 'hs4_mortality_window'],
        subjectKind: 'native_self',
      }).action,
    ).toBe('hard_stop')
  })

  it('HS-4 always seals — even for the native (NCD-10 scope)', () => {
    expect(resolveAction({ classes: ['hs4_mortality_window'], subjectKind: 'native_self' }).action).toBe(
      'seal_pending_signoff',
    )
  })

  it('HS-3 + proven native_self → interstitial (NCD-4)', () => {
    const r = resolveAction({ classes: ['hs3_health_crisis'], subjectKind: 'native_self' })
    expect(r.action).toBe('interstitial')
    expect(r.ncd4).toBe(true)
  })

  it('HS-3 + cohort → full seal', () => {
    expect(resolveAction({ classes: ['hs3_mental_health'], subjectKind: 'cohort' }).action).toBe(
      'seal_pending_signoff',
    )
  })

  it('HS-3 + unknown subject → full seal (null is not proof of native_self)', () => {
    expect(resolveAction({ classes: ['hs3_health_crisis'], subjectKind: null }).action).toBe(
      'seal_pending_signoff',
    )
  })

  it('nothing detected → proceed', () => {
    expect(resolveAction({ classes: [], subjectKind: 'native_self' }).action).toBe('proceed')
  })
})

describe('HS-1 capability exclusion is on the decision', () => {
  beforeEach(() => {
    flagState.on = true
  })
  it('names the mortality capabilities the plan stage must strip', async () => {
    const db = makeFakeSafetyDb()
    const d = await classifyTurnSafety({
      turnId: 't1', chartId: 'c1', queryText: 'When will I die?',
      subjectKind: 'native_self', db, now: NOW, newId,
    })
    expect(d.classes_detected).toContain('hs1_date_of_death')
    expect(d.excluded_capabilities).toContain('get_ayurdaya')
    expect(d.excluded_capabilities).toContain('ganita_ayurdaya_get')
  })

  it('a career question excludes nothing', async () => {
    const db = makeFakeSafetyDb()
    const d = await classifyTurnSafety({
      turnId: 't1', chartId: 'c1', queryText: 'How is my career this year?',
      subjectKind: 'native_self', db, now: NOW, newId,
    })
    expect(d.excluded_capabilities).toEqual([])
  })
})

describe('the post-plan pass is monotone — it can only escalate', () => {
  beforeEach(() => {
    flagState.on = true
  })

  it('a plan revealing a longevity capability escalates a benign question', async () => {
    const db = makeFakeSafetyDb()
    const before = await classifyTurnSafety({
      turnId: 't1', chartId: 'c1', queryText: 'Tell me about my constitution.',
      subjectKind: 'native_self', db, now: NOW, newId,
    })
    expect(before.action).toBe('proceed')

    const after = await reclassifyAfterPlan({
      decision: before,
      queryText: 'Tell me about my constitution.',
      domains: [],
      capabilities: ['get_ayurdaya', 'ganita_positions_get'],
      db, now: NOW, newId,
    })
    expect(after.classes_detected).toContain('hs4_mortality_window')
    expect(after.action).toBe('seal_pending_signoff')
    expect(after.excluded_capabilities).toContain('get_ayurdaya')
    // A SECOND chain row, not an edit of the first: the pre-plan decision is a
    // fact about what the gate knew before planning.
    expect(db.rows.pariprashna_safety_decisions).toHaveLength(2)
    expect(db.rows.pariprashna_safety_decisions[0].action).toBe('proceed')
    expect(db.rows.pariprashna_safety_decisions[1].action).toBe('seal_pending_signoff')
  })

  it('a plan revealing nothing leaves the decision exactly as it was', async () => {
    const db = makeFakeSafetyDb()
    const before = await classifyTurnSafety({
      turnId: 't1', chartId: 'c1', queryText: 'How is my career this year?',
      subjectKind: 'native_self', db, now: NOW, newId,
    })
    const after = await reclassifyAfterPlan({
      decision: before, queryText: 'How is my career this year?',
      domains: ['career'], capabilities: ['ganita_positions_get'],
      db, now: NOW, newId,
    })
    expect(after).toBe(before)
    expect(db.rows.pariprashna_safety_decisions).toHaveLength(1)
  })

  it('a hard_stop is never de-escalated by the plan pass', async () => {
    const db = makeFakeSafetyDb()
    const before = await classifyTurnSafety({
      turnId: 't1', chartId: 'c1', queryText: 'I want to kill myself.',
      subjectKind: 'native_self', db, now: NOW, newId,
    })
    expect(before.action).toBe('hard_stop')
    const after = await reclassifyAfterPlan({
      decision: before, queryText: 'I want to kill myself.',
      domains: ['health'], capabilities: [], db, now: NOW, newId,
    })
    expect(after.action).toBe('hard_stop')
  })
})

/**
 * Lane G1-A — THE NEVER-DE-ESCALATE PROPERTY, TESTED GUARD BY GUARD.
 *
 * ── WHY THIS FILE EXISTS (hardening round, C-4) ──────────────────────────────
 * Three separate guards stand between a classified turn and a de-escalated
 * audit row:
 *
 *   1. `reclassifyWithPlan`'s CARRY-FORWARD — the post-plan classification is
 *      the union of the prior detections and the new non-query ones, so a class
 *      found before planning survives a plan that does not mention it.
 *   2. `mergeFloor` — the gate re-imposes the prior classification as a floor on
 *      whatever the merge returned, immediately before persisting it.
 *   3. `strongerAction` — the resulting action is the max of the prior action
 *      and the newly resolved one.
 *
 * A reviewer mutation-tested them and found the shipped suite could not tell
 * them apart. Deleting guard 1 alone left `after.action` correct — because
 * guard 3 covered it — while SILENTLY dropping `hs2_suicide_adjacent` from
 * `classes_detected` and demoting `severity` from `hard_stop` to
 * `review_required`, in a HASH-CHAINED audit row, with every test green. The
 * only assertion in the area was `expect(after.action)`, and `action` was the
 * one field that could not detect it.
 *
 * So each guard gets a test that kills IT, at the level that owns it, with the
 * other two unable to compensate:
 *   · guard 1 is tested on `reclassifyWithPlan` DIRECTLY — the classifier
 *     function, below the gate, where neither `mergeFloor` nor `strongerAction`
 *     is in the call path at all;
 *   · guard 2 is tested on `mergeFloor` DIRECTLY, fed a deliberately regressed
 *     merge of the kind guard 1's removal would produce;
 *   · guard 3 is tested through a case where the class set is PERFECTLY
 *     monotone and only the ACTION would regress — so guards 1 and 2, which
 *     only ever restore classes and severity, cannot mask it.
 *
 * And the whole property is asserted on the FULL decision object, not on
 * `action` — the specific narrowness that let the original defect hide.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

import { makeFakeSafetyDb } from './fake_db'
import { classifyQuery, reclassifyWithPlan } from '../classifier'
import { SEVERITY_RANK, ACTION_RANK, type SafetyDecision } from '../types'

const flagState = { on: true }
vi.mock('../flag', () => ({
  SAFETY_GATE_FLAG: 'PARIPRASHNA_SAFETY_GATE_ENABLED',
  isSafetyGateEnabled: () => flagState.on,
}))

const { classifyTurnSafety, reclassifyAfterPlan, mergeFloor } = await import('../gate')

let seq = 0
const newId = (): string => `00000000-0000-4000-8000-${String(++seq).padStart(12, '0')}`
const NOW = new Date('2026-08-19T12:00:00.000Z')

beforeEach(() => {
  flagState.on = true
  seq = 0
})

/** The full property, asserted on every field that carries the claim. */
function expectNeverDeEscalated(before: SafetyDecision, after: SafetyDecision): void {
  for (const c of before.classes_detected) {
    expect(after.classes_detected, `class ${c} was DROPPED by the post-plan pass`).toContain(c)
  }
  expect(
    SEVERITY_RANK[after.severity],
    `severity was DEMOTED ${before.severity} → ${after.severity}`,
  ).toBeGreaterThanOrEqual(SEVERITY_RANK[before.severity])
  expect(
    ACTION_RANK[after.action],
    `action was WEAKENED ${before.action} → ${after.action}`,
  ).toBeGreaterThanOrEqual(ACTION_RANK[before.action])
}

// ═══════════════════════════════════════════════════════════════════════════
// GUARD 1 — `reclassifyWithPlan`'s carry-forward, tested where it lives.
//
// `mergeFloor` and `strongerAction` are both in `gate.ts`. This block calls the
// CLASSIFIER function directly, so neither of them can repair a regression
// here: if the carry-forward is deleted, these fail.
// ═══════════════════════════════════════════════════════════════════════════

describe('GUARD 1 — reclassifyWithPlan carries prior detections forward', () => {
  it('an HS-2 class found pre-plan survives a plan that never mentions it', () => {
    const prior = classifyQuery({ queryText: 'I want to kill myself.' })
    expect(prior.classes).toContain('hs2_suicide_adjacent')
    expect(prior.severity).toBe('hard_stop')

    const after = reclassifyWithPlan(prior, {
      queryText: 'I want to kill myself.',
      domains: ['health'],
      capabilities: [],
    })

    // THE ASSERTION THE ORIGINAL SUITE WAS MISSING. Deleting the
    // `...prior.detections` spread leaves the domain detection only, so
    // `classes` becomes ['hs3_health_crisis'] and `severity` drops to
    // 'review_required' — both caught here.
    expect(after.classes, 'hs2 was dropped by the plan-time merge').toContain('hs2_suicide_adjacent')
    expect(after.severity, 'severity was demoted by the plan-time merge').toBe('hard_stop')
    expect(after.classes).toContain('hs3_health_crisis')
  })

  it('the detection ROWS themselves are carried, not just the class labels', () => {
    // The audit row persists `detections`, and a class label with no detection
    // behind it would be a receipt that cannot say why it fired.
    const prior = classifyQuery({ queryText: 'When will I die?' })
    const after = reclassifyWithPlan(prior, {
      queryText: 'When will I die?',
      domains: [],
      capabilities: ['ganita_positions_get'],
    })
    for (const d of prior.detections) {
      expect(
        after.detections.some((x) => x.rule === d.rule && x.cls === d.cls),
        `detection ${d.rule} was dropped`,
      ).toBe(true)
    }
  })

  it('is monotone across a spread of pre-plan classes', () => {
    const cases = [
      'I want to kill myself.',
      'When will I die?',
      'Does my chart explain my depression?',
      'Am I alpayu or purnayu?',
      'What does my chart say about my career?',
    ]
    for (const q of cases) {
      const prior = classifyQuery({ queryText: q })
      const after = reclassifyWithPlan(prior, { queryText: q, domains: ['career'], capabilities: [] })
      for (const c of prior.classes) {
        expect(after.classes, `"${q}": class ${c} dropped`).toContain(c)
      }
      expect(SEVERITY_RANK[after.severity]).toBeGreaterThanOrEqual(SEVERITY_RANK[prior.severity])
    }
  })
})

// ═══════════════════════════════════════════════════════════════════════════
// GUARD 2 — `mergeFloor`, fed the exact regression guard 1's removal produces.
// ═══════════════════════════════════════════════════════════════════════════

describe('GUARD 2 — mergeFloor re-imposes the prior classification', () => {
  it('restores a class an upstream merge dropped', () => {
    const prior = classifyQuery({ queryText: 'I want to kill myself.' })
    // Exactly what a broken `reclassifyWithPlan` returns: the query-surface
    // detections gone, leaving only what the plan contributed.
    const regressed = {
      detections: [],
      evasion_markers: [],
      classes: [],
      severity: 'none' as const,
      normalized: prior.normalized,
    }
    const floored = mergeFloor(prior, regressed)
    expect(floored.classes).toContain('hs2_suicide_adjacent')
    expect(floored.severity).toBe('hard_stop')
    expect(floored.detections.length).toBeGreaterThan(0)
  })

  it('restores a DEMOTED severity even when the classes survived', () => {
    const prior = classifyQuery({ queryText: 'I want to kill myself.' })
    const demoted = { ...prior, severity: 'advisory' as const }
    expect(mergeFloor(prior, demoted).severity).toBe('hard_stop')
  })

  it('is a NO-OP on an already-monotone merge (invisible until something breaks)', () => {
    const prior = classifyQuery({ queryText: 'When will I die?' })
    const good = reclassifyWithPlan(prior, {
      queryText: 'When will I die?',
      domains: ['health'],
      capabilities: [],
    })
    // Returned by identity, not rebuilt — the guard costs nothing when the
    // upstream merge is correct.
    expect(mergeFloor(prior, good)).toBe(good)
  })

  it('never INVENTS a class the prior did not have', () => {
    // A floor that could add classes would be a different kind of bug: the
    // guard restores, it does not embellish.
    const prior = classifyQuery({ queryText: 'What does my chart say about my career?' })
    expect(prior.classes).toEqual([])
    const merged = classifyQuery({ queryText: 'What does my chart say about my career?' })
    expect(mergeFloor(prior, merged).classes).toEqual([])
  })
})

// ═══════════════════════════════════════════════════════════════════════════
// GUARD 3 — `strongerAction`, on a case where ONLY the action can regress.
//
// The classifier-fault fail-closed decision is the real case that isolates it:
// it carries `classes_detected: []` with `action: 'seal_pending_signoff'`, so
// the action is NOT derivable from the class set. A post-plan pass that finds
// an HS-3 class on a native_self subject resolves to `interstitial` (rank 2),
// which is WEAKER than the seal (rank 3) it must not undo. Guards 1 and 2 only
// ever restore classes and severity, so neither can mask this one.
// ═══════════════════════════════════════════════════════════════════════════

describe('GUARD 3 — strongerAction never lets the post-plan action weaken', () => {
  it('a fail-closed seal is not downgraded to an interstitial by the plan pass', async () => {
    const db = makeFakeSafetyDb()
    // The shape `classifyTurnSafety` produces when the classifier throws.
    const failClosed: SafetyDecision = {
      decision_id: newId(),
      turn_id: 't1',
      chart_id: 'c1',
      enforced: true,
      classes_detected: [],
      severity: 'review_required',
      action: 'seal_pending_signoff',
      subject_kind: 'native_self',
      ncd4_interstitial_applies: false,
      detections: [],
      evasion_markers: [],
      excluded_capabilities: [],
      llm_assist_ran: false,
      // A fail-closed seal has already opened its review (finalize does it), so
      // this carries one — which is also what the C-6 DB CHECK requires.
      review_id: '00000000-0000-4000-8000-00000000ffff',
      audit_written: true,
      decided_at: NOW.toISOString(),
    }

    const after = await reclassifyAfterPlan({
      decision: failClosed,
      queryText: 'Does my chart explain my depression?',
      domains: ['mental_health'],
      capabilities: [],
      db,
      now: NOW,
      newId,
    })

    // Without `strongerAction` this reads 'interstitial' — the NCD-4
    // relaxation, applied to a turn whose classification FAILED. That is the
    // exact inversion the fail-closed path exists to prevent.
    expect(after.action).toBe('seal_pending_signoff')
    expectNeverDeEscalated(failClosed, after)
  })

  it('and the interstitial flag is not set either', async () => {
    const db = makeFakeSafetyDb()
    const failClosed: SafetyDecision = {
      decision_id: newId(), turn_id: 't2', chart_id: 'c2', enforced: true,
      classes_detected: [], severity: 'review_required', action: 'seal_pending_signoff',
      subject_kind: 'native_self', ncd4_interstitial_applies: false, detections: [],
      evasion_markers: [], excluded_capabilities: [], llm_assist_ran: false,
      review_id: '00000000-0000-4000-8000-00000000fffe', audit_written: true,
      decided_at: NOW.toISOString(),
    }
    const after = await reclassifyAfterPlan({
      decision: failClosed, queryText: 'Does my chart explain my depression?',
      domains: ['mental_health'], capabilities: [], db, now: NOW, newId,
    })
    expect(after.ncd4_interstitial_applies).toBe(false)
  })
})

// ═══════════════════════════════════════════════════════════════════════════
// THE WHOLE PROPERTY, end to end, on the FULL decision object.
// ═══════════════════════════════════════════════════════════════════════════

describe('end to end — the full decision object is monotone across the plan pass', () => {
  const scenarios: Array<{ q: string; domains: string[]; caps: string[] }> = [
    { q: 'I want to kill myself.', domains: ['health'], caps: ['assess_health'] },
    { q: 'I want to kill myself.', domains: [], caps: ['get_ayurdaya'] },
    { q: 'When will I die?', domains: ['health'], caps: ['assess_health'] },
    { q: 'Does my chart explain my depression?', domains: ['longevity'], caps: ['get_ayurdaya'] },
    { q: 'Am I alpayu or purnayu?', domains: ['mental_health'], caps: [] },
    { q: 'Tell me about my constitution.', domains: [], caps: ['get_ayurdaya'] },
    { q: 'What does my chart say about my career?', domains: ['career'], caps: [] },
    { q: 'Which day is best for jal samadhi?', domains: ['health'], caps: ['kala_elect_get'] },
  ]

  for (const s of scenarios) {
    for (const subjectKind of ['native_self', 'cohort', null] as const) {
      it(`"${s.q}" (${subjectKind ?? 'unknown subject'})`, async () => {
        const db = makeFakeSafetyDb()
        const before = await classifyTurnSafety({
          turnId: 't1', chartId: 'c1', queryText: s.q, subjectKind, db, now: NOW, newId,
        })
        const after = await reclassifyAfterPlan({
          decision: before, queryText: s.q, domains: s.domains, capabilities: s.caps,
          db, now: NOW, newId,
        })
        expectNeverDeEscalated(before, after)
      })
    }
  }

  it('an HS-2 turn keeps hard_stop AND its class AND its severity in the AUDIT ROW', async () => {
    // The original defect was invisible precisely because it lived in the
    // persisted row rather than in the returned action. Assert the row.
    const db = makeFakeSafetyDb()
    const before = await classifyTurnSafety({
      turnId: 't1', chartId: 'c1', queryText: 'I want to kill myself.',
      subjectKind: 'cohort', db, now: NOW, newId,
    })
    await reclassifyAfterPlan({
      decision: before, queryText: 'I want to kill myself.',
      domains: ['health'], capabilities: ['assess_health'], db, now: NOW, newId,
    })
    const rows = db.rows.pariprashna_safety_decisions
    const last = rows[rows.length - 1] as unknown as {
      action: string
      severity: string
      classes_detected: string[]
    }
    expect(last.action).toBe('hard_stop')
    expect(last.severity).toBe('hard_stop')
    expect(last.classes_detected).toContain('hs2_suicide_adjacent')
  })
})

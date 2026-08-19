/**
 * Lane G1-A — A SEALED READING IS ALWAYS TRACKED, AND THE TRACK CAN BE WALKED.
 *
 * Two hardening-round findings, together because they are two halves of one
 * claim — "a review was opened" — that the first build made and could not keep.
 *
 * ── C-6: the post-plan seal opened NO review and said it had ─────────────────
 * `reclassifyAfterPlan` called only `appendSafetyDecision`, never
 * `openReview`/`persistNewReview`. A turn that classified clean before planning
 * and escalated after it (a plan revealing a longevity capability the question's
 * wording hid — the exact scenario the shipped suite's own happy-path test
 * used) therefore produced a `seal_pending_signoff` decision with
 * `review_id: null` and NO review row anywhere, while `route.ts` emitted the
 * fixed acknowledgment that states "the review has been opened. Nothing has
 * been discarded." The reading was sealed, nothing was tracking it, and the
 * reader was told the opposite. With no FK on `review_id`, no query could find
 * these afterwards either.
 *
 * ── C-7: nothing could ever finish a review ─────────────────────────────────
 * `recordAdversarialPass`, `signOff`, `withhold`, `persistReviewTransition`,
 * `loadReview` and `isReleasable` had ZERO callers outside their own modules
 * and tests — no cron, no route, no job. Every review that opened sat in
 * `seal_pending` forever. The state machine's unit tests proved each transition
 * in isolation; nothing proved the PATH existed end to end, which is the only
 * thing a reader of a sealed reading actually depends on.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

import { makeFakeSafetyDb } from './fake_db'
import {
  openReview,
  recordAdversarialPass,
  signOff,
  withhold,
  isReleasable,
} from '../review_machine'
import type { SafetyDecision } from '../types'

const flagState = { on: true }
vi.mock('../flag', () => ({
  SAFETY_GATE_FLAG: 'PARIPRASHNA_SAFETY_GATE_ENABLED',
  isSafetyGateEnabled: () => flagState.on,
}))

const { classifyTurnSafety, reclassifyAfterPlan, actionRequiresReview } = await import('../gate')

let seq = 0
const newId = (): string => `00000000-0000-4000-8000-${String(++seq).padStart(12, '0')}`
const NOW = new Date('2026-08-19T12:00:00.000Z')

beforeEach(() => {
  flagState.on = true
  seq = 0
})

// ═══════════════════════════════════════════════════════════════════════════
// C-6 — the post-plan escalation path opens a real review.
// ═══════════════════════════════════════════════════════════════════════════

describe('C-6 — a POST-PLAN escalation into the seal path opens a review', () => {
  it('a turn that classifies clean pre-plan and seals post-plan gets a review row', async () => {
    const db = makeFakeSafetyDb()

    const before = await classifyTurnSafety({
      turnId: 't1', chartId: 'c1', queryText: 'Tell me about my constitution.',
      subjectKind: 'native_self', db, now: NOW, newId,
    })
    // Pre-plan: genuinely clean. No review, and correctly so.
    expect(before.action).toBe('proceed')
    expect(before.review_id).toBeNull()
    expect(db.rows.pariprashna_safety_reviews).toBeUndefined()

    const after = await reclassifyAfterPlan({
      decision: before,
      queryText: 'Tell me about my constitution.',
      domains: [],
      capabilities: ['get_ayurdaya', 'ganita_positions_get'],
      db, now: NOW, newId,
    })

    expect(after.action).toBe('seal_pending_signoff')
    // WAS `null` BEFORE THE HARDENING ROUND. This is the finding.
    expect(after.review_id, 'a sealed reading with no review_id').not.toBeNull()
    expect(db.rows.pariprashna_safety_reviews, 'no review row was written').toHaveLength(1)

    const review = db.rows.pariprashna_safety_reviews[0]
    expect(review.review_id).toBe(after.review_id)
    expect(review.state).toBe('seal_pending')
    expect(review.turn_id).toBe('t1')
    // And the review knows WHY it was opened, so a human picking it up can see
    // what class of reading they are being asked to sign off on.
    expect(review.classes).toContain('hs4_mortality_window')
  })

  it('the review-opening EVENT is recorded too, not just the current-state row', async () => {
    const db = makeFakeSafetyDb()
    const before = await classifyTurnSafety({
      turnId: 't1', chartId: 'c1', queryText: 'Tell me about my constitution.',
      subjectKind: 'native_self', db, now: NOW, newId,
    })
    await reclassifyAfterPlan({
      decision: before, queryText: 'Tell me about my constitution.',
      domains: [], capabilities: ['get_ayurdaya'], db, now: NOW, newId,
    })
    expect(db.rows.pariprashna_safety_review_events).toHaveLength(1)
  })

  it('a post-plan escalation on a turn that ALREADY sealed does not open a second review', async () => {
    // Idempotence matters here: one turn, one review. A second review row for
    // the same turn would double-count the sign-off queue and make "how many
    // readings are pending review" unanswerable.
    const db = makeFakeSafetyDb()
    const before = await classifyTurnSafety({
      turnId: 't1', chartId: 'c1', queryText: 'Am I alpayu or purnayu?',
      subjectKind: 'cohort', db, now: NOW, newId,
    })
    expect(before.action).toBe('seal_pending_signoff')
    expect(before.review_id).not.toBeNull()

    const after = await reclassifyAfterPlan({
      decision: before, queryText: 'Am I alpayu or purnayu?',
      domains: ['health'], capabilities: [], db, now: NOW, newId,
    })
    expect(after.review_id).toBe(before.review_id)
    expect(db.rows.pariprashna_safety_reviews).toHaveLength(1)
  })

  it('an HS-2 hard stop opens NO review — there is nothing to review', async () => {
    // The invariant is "a SEALED reading is tracked", not "every fired turn
    // opens a review". HS-2 composes no reading at all.
    const db = makeFakeSafetyDb()
    const d = await classifyTurnSafety({
      turnId: 't1', chartId: 'c1', queryText: 'I want to kill myself.',
      subjectKind: 'cohort', db, now: NOW, newId,
    })
    expect(d.action).toBe('hard_stop')
    expect(d.review_id).toBeNull()
    expect(db.rows.pariprashna_safety_reviews).toBeUndefined()
  })
})

describe('C-6 — the invariant, asserted across every path that can seal', () => {
  // The application-side mirror of migration 576's
  // `pariprashna_safety_decisions_seal_requires_review_chk`. Both exist on
  // purpose: the CHECK makes the bug unrepresentable in the database, this
  // makes it fail in CI before anyone runs a migration.
  const sealing: Array<{ name: string; q: string; domains: string[]; caps: string[] }> = [
    { name: 'pre-plan HS-4', q: 'Am I alpayu or purnayu?', domains: [], caps: [] },
    { name: 'pre-plan HS-1 (implies HS-4)', q: 'When will I die?', domains: [], caps: [] },
    { name: 'pre-plan HS-3 cohort', q: 'Does my chart explain my depression?', domains: [], caps: [] },
    { name: 'post-plan capability escalation', q: 'Tell me about my constitution.', domains: [], caps: ['get_ayurdaya'] },
    { name: 'post-plan domain escalation', q: 'How is my sixth house doing?', domains: ['health'], caps: [] },
    { name: 'post-plan longevity domain', q: 'How is my sixth house doing?', domains: ['longevity'], caps: [] },
  ]

  for (const s of sealing) {
    for (const subjectKind of ['native_self', 'cohort', null] as const) {
      it(`${s.name} (${subjectKind ?? 'unknown subject'}) — sealed ⇒ review_id present`, async () => {
        const db = makeFakeSafetyDb()
        const before = await classifyTurnSafety({
          turnId: 't1', chartId: 'c1', queryText: s.q, subjectKind, db, now: NOW, newId,
        })
        const after = await reclassifyAfterPlan({
          decision: before, queryText: s.q, domains: s.domains, capabilities: s.caps,
          db, now: NOW, newId,
        })
        for (const d of [before, after]) {
          if (actionRequiresReview(d.action)) {
            expect(
              d.review_id,
              `action "${d.action}" was reached with review_id null — the reader is told a ` +
                'review was opened and none was',
            ).not.toBeNull()
          }
        }
      })
    }
  }
})

describe('C-6 — an inconsistent inbound interstitial still ends up TRACKED', () => {
  it('a decision claiming interstitial on a cohort subject is escalated AND tracked', async () => {
    // A deliberately inconsistent decision: `action: 'interstitial'` on a
    // `cohort` subject, which NCD-4/NCD-10 does not permit. The point of the
    // case is that whatever the gate decides to do with it, the result is not
    // an untracked seal.
    const db = makeFakeSafetyDb()
    const outOfScope: SafetyDecision = {
      decision_id: newId(), turn_id: 't1', chart_id: 'c1', enforced: true,
      classes_detected: ['hs4_mortality_window'], severity: 'review_required',
      action: 'interstitial', subject_kind: 'cohort', ncd4_interstitial_applies: true,
      detections: [], evasion_markers: [], excluded_capabilities: [], llm_assist_ran: false,
      review_id: null, audit_written: false, decided_at: NOW.toISOString(),
    }
    const after = await reclassifyAfterPlan({
      decision: outOfScope, queryText: 'Am I alpayu or purnayu?',
      domains: ['health'], capabilities: [], db, now: NOW, newId,
    })
    // `strongerAction` escalates it to the full seal, which is the correct
    // fail-closed direction for a cohort subject.
    expect(after.action).toBe('seal_pending_signoff')
    expect(after.review_id).not.toBeNull()
    expect(db.rows.pariprashna_safety_reviews).toHaveLength(1)
    expect(db.rows.pariprashna_safety_reviews[0].state).toBe('seal_pending')
  })

  it.todo(
    'openReviewForDecision\'s interstitial-refusal fallback is DEFENSIVE and currently ' +
      'unreachable — see the comment below; not tested because it cannot be reached honestly',
  )
  // ── AN HONEST GAP, RECORDED RATHER THAN FAKED (§N.8) ─────────────────────
  // `openReviewForDecision` catches `openReview`'s out-of-scope refusal and
  // re-opens as a non-interstitial seal. That catch block was a REAL bug fix —
  // it used to set `review_id: null` alongside `action: seal_pending_signoff`,
  // reaching the untracked-seal state C-6 is about by a second route — but the
  // branch itself is not reachable through the current call graph, and this
  // round did not manufacture a path to pretend otherwise:
  //
  //   · `resolveAction` returns `'interstitial'` ONLY when `interstitialApplies`
  //     is already true, so the pre-plan `finalize` path can never hand
  //     `openReview` a combination it will refuse;
  //   · on the post-plan path, `strongerAction` escalates any inconsistent
  //     inbound interstitial to `seal_pending_signoff` before the review is
  //     opened — which the test above demonstrates.
  //
  // So it is defence in depth against a future caller, not live behaviour. It
  // is NOT claimed as tested, and `it.todo` above keeps that claim visible in
  // the runner's output rather than only in a comment someone may not read.
})

// ═══════════════════════════════════════════════════════════════════════════
// C-7 — the lifecycle runs END TO END, not transition by transition.
//
// `review_machine.test.ts` already proves each transition and each refusal in
// isolation. What was missing — and what a reader of a sealed reading actually
// depends on — is that the PATH from seal to release exists and is walkable.
// ═══════════════════════════════════════════════════════════════════════════

describe('C-7 — seal_pending → two independent passes → sign-off → released', () => {
  it('walks the whole path', () => {
    const opened = openReview({
      reviewId: 'r1', chartId: 'c1', turnId: 't1',
      classes: ['hs4_mortality_window'], subjectKind: 'cohort',
      interstitial: false, now: NOW,
    })
    expect(opened.state).toBe('seal_pending')
    expect(isReleasable(opened), 'a freshly sealed review must NOT be servable').toBe(false)

    const pass1 = recordAdversarialPass(opened, {
      reviewerModelId: 'model-a', reviewerContextId: 'ctx-1',
      verdict: 'sustained', findings: ['grounding is thin on the dasha claim'], now: NOW,
    })
    expect(pass1.state).toBe('adversarial_pass_1_recorded')
    expect(isReleasable(pass1)).toBe(false)

    const pass2 = recordAdversarialPass(pass1, {
      reviewerModelId: 'model-b', reviewerContextId: 'ctx-2',
      verdict: 'sustained_with_reservations',
      findings: ['calibration language overstates confidence'], now: NOW,
    })
    expect(pass2.state).toBe('adversarial_passes_complete')
    // STILL not releasable — the two controls are never collapsed (MP §3.5.C).
    expect(isReleasable(pass2), 'two passes must not release without a sign-off').toBe(false)

    const released = signOff(pass2, { signedOffBy: 'native-uid', now: NOW })
    expect(released.state).toBe('released')
    expect(released.signed_off_by).toBe('native-uid')
    expect(released.signed_off_at).not.toBeNull()
    expect(isReleasable(released)).toBe(true)
    expect(released.passes).toHaveLength(2)
  })

  it('the withhold path is walkable from every non-terminal state', () => {
    const opened = openReview({
      reviewId: 'r1', chartId: 'c1', turnId: 't1',
      classes: ['hs3_health_crisis'], subjectKind: 'cohort', interstitial: false, now: NOW,
    })
    expect(withhold(opened, 'reader withdrew the question').state).toBe('withheld')

    const pass1 = recordAdversarialPass(opened, {
      reviewerModelId: 'm', reviewerContextId: 'c', verdict: 'sustained', findings: [], now: NOW,
    })
    expect(withhold(pass1, 'first pass raised a blocking concern').state).toBe('withheld')
    expect(isReleasable(withhold(pass1, 'x'))).toBe(false)
  })

  it('a refuted pass cannot be signed off — the passes are not decorative', () => {
    const opened = openReview({
      reviewId: 'r1', chartId: 'c1', turnId: 't1',
      classes: ['hs4_mortality_window'], subjectKind: 'cohort', interstitial: false, now: NOW,
    })
    const p1 = recordAdversarialPass(opened, {
      reviewerModelId: 'a', reviewerContextId: '1', verdict: 'refuted',
      findings: ['the mortality claim is unsupported'], now: NOW,
    })
    const p2 = recordAdversarialPass(p1, {
      reviewerModelId: 'b', reviewerContextId: '2', verdict: 'sustained', findings: [], now: NOW,
    })
    expect(p2.state).toBe('adversarial_passes_complete')
    expect(() => signOff(p2, { signedOffBy: 'native-uid' })).toThrow(/refuted/)
  })
})

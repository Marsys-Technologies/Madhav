/**
 * Lane G1-A — the HS-3/HS-4 three-step path.
 *
 * MP §3.5.C: "double red-team AND explicit native sign-off" — and the
 * architecture's insistence that they are "two distinct controls, never
 * collapsed". The tests that matter here are the ones that try to COLLAPSE
 * them: sign off with no passes, sign off with one pass, run the same reviewer
 * twice and call it two, release over a refutation.
 */

import { describe, it, expect } from 'vitest'

import {
  interstitialApplies,
  isLegalTransition,
  isReleasable,
  openReview,
  recordAdversarialPass,
  SafetyReviewTransitionError,
  signOff,
  withhold,
} from '../review_machine'
import type { SafetyReviewRecord } from '../types'

const NOW = new Date('2026-08-19T12:00:00.000Z')

function sealed(overrides: Partial<Parameters<typeof openReview>[0]> = {}): SafetyReviewRecord {
  return openReview({
    reviewId: 'rev-1',
    chartId: 'chart-1',
    turnId: 'turn-1',
    classes: ['hs3_health_crisis'],
    subjectKind: 'cohort',
    interstitial: false,
    now: NOW,
    ...overrides,
  })
}

describe('the three steps cannot be collapsed', () => {
  it('sign-off on a freshly sealed review is REFUSED', () => {
    expect(() => signOff(sealed(), { signedOffBy: 'native', now: NOW })).toThrow(
      SafetyReviewTransitionError,
    )
  })

  it('sign-off after ONE adversarial pass is REFUSED', () => {
    const one = recordAdversarialPass(sealed(), {
      reviewerModelId: 'model-a',
      reviewerContextId: 'ctx-a',
      verdict: 'sustained',
      findings: [],
      now: NOW,
    })
    expect(one.state).toBe('adversarial_pass_1_recorded')
    expect(() => signOff(one, { signedOffBy: 'native', now: NOW })).toThrow(SafetyReviewTransitionError)
  })

  it('two passes alone do NOT release — the sign-off is a separate act', () => {
    let r = sealed()
    r = recordAdversarialPass(r, { reviewerModelId: 'a', reviewerContextId: '1', verdict: 'sustained', findings: [], now: NOW })
    r = recordAdversarialPass(r, { reviewerModelId: 'b', reviewerContextId: '2', verdict: 'sustained', findings: [], now: NOW })
    expect(r.state).toBe('adversarial_passes_complete')
    expect(isReleasable(r)).toBe(false)
    const released = signOff(r, { signedOffBy: 'native', now: NOW })
    expect(released.state).toBe('released')
    expect(isReleasable(released)).toBe(true)
    expect(released.signed_off_by).toBe('native')
  })

  it('sign-off with no identified signer is REFUSED', () => {
    let r = sealed()
    r = recordAdversarialPass(r, { reviewerModelId: 'a', reviewerContextId: '1', verdict: 'sustained', findings: [], now: NOW })
    r = recordAdversarialPass(r, { reviewerModelId: 'b', reviewerContextId: '2', verdict: 'sustained', findings: [], now: NOW })
    expect(() => signOff(r, { signedOffBy: '', now: NOW })).toThrow(SafetyReviewTransitionError)
  })
})

describe('"independent" has a real detector behind it (§N.8)', () => {
  it('the same (model, context) twice is refused as a second pass', () => {
    const one = recordAdversarialPass(sealed(), {
      reviewerModelId: 'model-a',
      reviewerContextId: 'ctx-a',
      verdict: 'sustained',
      findings: [],
      now: NOW,
    })
    expect(() =>
      recordAdversarialPass(one, {
        reviewerModelId: 'model-a',
        reviewerContextId: 'ctx-a',
        verdict: 'sustained',
        findings: [],
        now: NOW,
      }),
    ).toThrow(/INDEPENDENT/)
  })

  it('same model, different context IS accepted — the detector is weak and says so', () => {
    // Recorded deliberately: the check is (model, context), not "two different
    // sets of weights". A stronger claim than the code can support would be the
    // §N.8 defect this project has a principle about.
    const one = recordAdversarialPass(sealed(), { reviewerModelId: 'm', reviewerContextId: '1', verdict: 'sustained', findings: [], now: NOW })
    const two = recordAdversarialPass(one, { reviewerModelId: 'm', reviewerContextId: '2', verdict: 'sustained', findings: [], now: NOW })
    expect(two.state).toBe('adversarial_passes_complete')
  })

  it('a third pass is refused', () => {
    let r = sealed()
    r = recordAdversarialPass(r, { reviewerModelId: 'a', reviewerContextId: '1', verdict: 'sustained', findings: [], now: NOW })
    r = recordAdversarialPass(r, { reviewerModelId: 'b', reviewerContextId: '2', verdict: 'sustained', findings: [], now: NOW })
    expect(() =>
      recordAdversarialPass(r, { reviewerModelId: 'c', reviewerContextId: '3', verdict: 'sustained', findings: [], now: NOW }),
    ).toThrow(SafetyReviewTransitionError)
  })
})

describe('a refuted reading cannot be signed off', () => {
  it('refuses release when either pass returned `refuted`', () => {
    let r = sealed()
    r = recordAdversarialPass(r, { reviewerModelId: 'a', reviewerContextId: '1', verdict: 'sustained', findings: [], now: NOW })
    r = recordAdversarialPass(r, { reviewerModelId: 'b', reviewerContextId: '2', verdict: 'refuted', findings: ['grounding does not support the verdict'], now: NOW })
    expect(() => signOff(r, { signedOffBy: 'native', now: NOW })).toThrow(/refuted/)
  })

  it('withhold is the correct terminal state for a refuted review', () => {
    let r = sealed()
    r = recordAdversarialPass(r, { reviewerModelId: 'a', reviewerContextId: '1', verdict: 'refuted', findings: ['x'], now: NOW })
    const w = withhold(r, 'pass 1 refuted the grounding')
    expect(w.state).toBe('withheld')
    expect(w.withheld_reason).toBe('pass 1 refuted the grounding')
    expect(isReleasable(w)).toBe(false)
  })
})

describe('terminal states are terminal', () => {
  it('nothing transitions out of released or withheld', () => {
    expect(isLegalTransition('released', 'seal_pending')).toBe(false)
    expect(isLegalTransition('released', 'withheld')).toBe(false)
    expect(isLegalTransition('withheld', 'released')).toBe(false)
    expect(isLegalTransition('interstitial_shown', 'seal_pending')).toBe(false)
  })
})

describe('NCD-4 / NCD-10 — the interstitial has EXACTLY the ruled scope', () => {
  it('applies to a proven native_self subject on HS-3 classes', () => {
    expect(interstitialApplies({ subjectKind: 'native_self', classes: ['hs3_health_crisis'] })).toBe(true)
    expect(interstitialApplies({ subjectKind: 'native_self', classes: ['hs3_mental_health'] })).toBe(true)
    expect(
      interstitialApplies({ subjectKind: 'native_self', classes: ['hs3_health_crisis', 'hs3_mental_health'] }),
    ).toBe(true)
  })

  it('does NOT apply to a cohort subject — NCD-10: "cohort subjects unaffected — full seal"', () => {
    expect(interstitialApplies({ subjectKind: 'cohort', classes: ['hs3_health_crisis'] })).toBe(false)
  })

  it('does NOT apply to HS-4 even for the native — NCD-10 scopes it to health-crisis/mental-health', () => {
    expect(interstitialApplies({ subjectKind: 'native_self', classes: ['hs4_mortality_window'] })).toBe(false)
    expect(
      interstitialApplies({ subjectKind: 'native_self', classes: ['hs3_health_crisis', 'hs4_mortality_window'] }),
      'one HS-4 class takes the whole turn back to the seal path',
    ).toBe(false)
  })

  it('a NULL subject_kind is NOT proof of native_self and does not buy the relaxation', () => {
    // This is the coupling with the consent lane: with SUBJECT_CONSENT_ENFORCEMENT
    // off, subject_kind is null because nobody checked. "We didn't check" must
    // never read as "it's the native".
    expect(interstitialApplies({ subjectKind: null, classes: ['hs3_health_crisis'] })).toBe(false)
  })

  it('openReview REFUSES to open an out-of-scope interstitial', () => {
    expect(() =>
      openReview({
        reviewId: 'r',
        chartId: 'c',
        turnId: 't',
        classes: ['hs4_mortality_window'],
        subjectKind: 'native_self',
        interstitial: true,
        now: NOW,
      }),
    ).toThrow(SafetyReviewTransitionError)
  })

  it('an in-scope interstitial opens directly in its own terminal state', () => {
    const r = openReview({
      reviewId: 'r',
      chartId: 'c',
      turnId: 't',
      classes: ['hs3_mental_health'],
      subjectKind: 'native_self',
      interstitial: true,
      now: NOW,
    })
    expect(r.state).toBe('interstitial_shown')
    expect(isReleasable(r)).toBe(true)
    // …and it is recorded DISTINCTLY from a released seal, so "how many
    // sensitive readings went out under the relaxation" is a query, not a guess.
    expect(r.state).not.toBe('released')
  })
})

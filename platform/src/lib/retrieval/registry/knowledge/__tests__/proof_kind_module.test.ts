/**
 * Unit tests for the per-binding proof-kind primitives (R3 boundary, "genuine per-mode proof
 * typing"). These are the one shared fallback chain every caller (compiler integrity checks,
 * overlay availability resolution, the planner's admission decision) must go through — see
 * proof_kind.ts's own doc comment for why a fourth ad hoc implementation is the exact defect
 * class this module exists to prevent.
 */
import { describe, expect, it } from 'vitest'
import { bindingMatchesMode, bindingProofKind, isNonAnswerBinding, selectBindingForMode } from '../proof_kind'

describe('bindingProofKind', () => {
  it('defaults to answer when neither the binding nor the SCU declares a proof_kind', () => {
    expect(bindingProofKind({}, {})).toBe('answer')
  })

  it('inherits the SCU proof_kind when the binding does not override it', () => {
    expect(bindingProofKind({ proof_kind: 'plan' }, {})).toBe('plan')
  })

  it("prefers the binding's own proof_kind over the SCU's", () => {
    expect(bindingProofKind({ proof_kind: 'plan' }, { proof_kind: 'answer' })).toBe('answer')
    expect(bindingProofKind({ proof_kind: 'answer' }, { proof_kind: 'plan' })).toBe('plan')
  })
})

describe('isNonAnswerBinding', () => {
  it('is false for answer (explicit or defaulted)', () => {
    expect(isNonAnswerBinding({}, {})).toBe(false)
    expect(isNonAnswerBinding({ proof_kind: 'answer' }, {})).toBe(false)
    expect(isNonAnswerBinding({ proof_kind: 'plan' }, { proof_kind: 'answer' })).toBe(false)
  })

  it('is true for plan/resource/discovery, however inherited', () => {
    expect(isNonAnswerBinding({ proof_kind: 'plan' }, {})).toBe(true)
    expect(isNonAnswerBinding({}, { proof_kind: 'resource' })).toBe(true)
    expect(isNonAnswerBinding({ proof_kind: 'answer' }, { proof_kind: 'discovery' })).toBe(true)
  })
})

describe('bindingMatchesMode', () => {
  it('a selector-less binding always matches (the SCU default)', () => {
    expect(bindingMatchesMode({}, undefined)).toBe(true)
    expect(bindingMatchesMode({ mode_selector: [] }, { mode: 'anything' })).toBe(true)
  })

  it('matches only when every selector clause equals the intended arg', () => {
    const binding = { mode_selector: [{ argument: 'mode', equals: 'kakshya_windows' }] }
    expect(bindingMatchesMode(binding, { mode: 'kakshya_windows' })).toBe(true)
    expect(bindingMatchesMode(binding, { mode: 'sav_bav_gating' })).toBe(false)
    expect(bindingMatchesMode(binding, undefined)).toBe(false)
  })

  it('requires ALL clauses to match (AND, not OR)', () => {
    const binding = { mode_selector: [{ argument: 'dry_run', equals: false }, { argument: 'query_class', equals: 'holistic' }] }
    expect(bindingMatchesMode(binding, { dry_run: false, query_class: 'holistic' })).toBe(true)
    expect(bindingMatchesMode(binding, { dry_run: false, query_class: 'other' })).toBe(false)
    expect(bindingMatchesMode(binding, { dry_run: false })).toBe(false)
  })
})

describe('selectBindingForMode', () => {
  const primary = { binding_id: 'primary', relation: 'primary' as const, mode_selector: undefined }
  const provides = { binding_id: 'provides', relation: 'provides' as const, mode_selector: undefined }
  const modeA = { binding_id: 'mode-a', relation: 'primary' as const, mode_selector: [{ argument: 'mode', equals: 'a' }] }
  const modeB = { binding_id: 'mode-b', relation: 'provides' as const, mode_selector: [{ argument: 'mode', equals: 'b' }] }
  const modeDefault = { binding_id: 'mode-default', relation: 'provides' as const, mode_selector: undefined }

  it('returns null for an empty candidate list', () => {
    expect(selectBindingForMode([], undefined)).toBeNull()
  })

  it('is byte-identical to the old "primary ?? candidates[0]" heuristic when nothing declares mode_selector', () => {
    // provides listed first, primary second — exactly query_planet_transit's real binding
    // order (§7 of the research report) — proves the fallback still prefers `primary`
    // regardless of array position, matching every SCU in the current estate.
    expect(selectBindingForMode([provides, primary], undefined)).toBe(primary)
    expect(selectBindingForMode([primary, provides], undefined)).toBe(primary)
  })

  it('falls back to candidates[0] when no candidate is primary and none has a selector', () => {
    const a = { binding_id: 'a', relation: 'provides' as const, mode_selector: undefined }
    const b = { binding_id: 'b', relation: 'provides' as const, mode_selector: undefined }
    expect(selectBindingForMode([a, b], undefined)).toBe(a)
  })

  it('selects the binding whose selector matches the intended args, over the default', () => {
    expect(selectBindingForMode([modeDefault, modeA, modeB], { mode: 'a' })).toBe(modeA)
    expect(selectBindingForMode([modeDefault, modeA, modeB], { mode: 'b' })).toBe(modeB)
  })

  it('falls back to the default (selector-less) binding when no selector matches', () => {
    expect(selectBindingForMode([modeDefault, modeA, modeB], { mode: 'c' })).toBe(modeDefault)
    expect(selectBindingForMode([modeDefault, modeA, modeB], undefined)).toBe(modeDefault)
  })
})

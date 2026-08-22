/**
 * The window-opening ask — answer-reading unit tests (lane P4-G).
 *
 * The classifier is the adversarial surface of this lane, so these tests are written the way a
 * refuter would write them: they try to make the reader's words turn into an outcome they do
 * not carry. Every `expect` below is a way the module could corrupt the calibration series.
 */

import { describe, it, expect } from 'vitest'
import {
  classifyWindowAnswer,
  outcomeOf,
  normalizeAnswer,
  BARE_TOKEN_MAX_WORDS,
  ANSWER_KINDS,
  SCORABLE_ANSWER_KINDS,
  type AnswerKind,
} from '../classify'

const kindOf = (s: string): AnswerKind => classifyWindowAnswer(s).kind

describe('classifyWindowAnswer — clean, unambiguous answers', () => {
  it.each([
    ['yes', 'happened'],
    ['Yes.', 'happened'],
    ['yes, it happened', 'happened'],
    ['It happened, more or less exactly as you put it', 'partial'], // "more or less" is a partial marker
    ['that came true', 'happened'],
    ['you were right', 'happened'],
    ['no', 'did_not_happen'],
    ['No.', 'did_not_happen'],
    ['it did not happen', 'did_not_happen'],
    ["it didn't happen", 'did_not_happen'],
    ['nothing happened', 'did_not_happen'],
    ['that never happened', 'did_not_happen'],
    ['the whole thing fell through', 'did_not_happen'],
    ['partly', 'partial'],
    ['partially, yes', 'partial'],
    ['sort of', 'partial'],
    ['it happened but only in part', 'partial'],
    ['mixed', 'partial'],
  ] as const)('%j → %s', (input, expected) => {
    expect(kindOf(input)).toBe(expected)
  })
})

describe("classifyWindowAnswer — 'can't tell' is a first-class answer", () => {
  it('"no idea" is a can\'t-tell, not a denial hiding a bare "no" (span-masking regression)', () => {
    // The defect this pins: before span masking, the bare-token `no` marker fired INSIDE
    // "no idea", making the plainest honest non-answer in English come out `ambiguous` and
    // record nothing. Found by this test suite before the module ever ran for real.
    const r = classifyWindowAnswer('no idea')
    expect(r.kind).toBe('cant_tell')
    expect(r.matched.some((m) => m.startsWith('deny:'))).toBe(false)
  })

  it.each([
    "I can't tell",
    'I cannot tell yet',
    "I don't know",
    'no idea',
    'too early to tell',
    'hard to say',
    'unclear',
    // A HEDGE THAT LEANS. These read as an honest can't-tell rather than as `ambiguous`,
    // and the distinction is deliberate: the reader's own headline claim is that they do not
    // know. `unverifiable` records exactly that, carries NO numeric value, and is excluded
    // from every Brier computation — so it cannot bias the calibration series in the direction
    // the lean pointed. Calling these `ambiguous` instead would record nothing at all and
    // discard a real, honest statement the reader took the trouble to make.
    "I don't know, possibly it did",
    'it might have happened, hard to say',
    'unclear — it may not have happened',
  ])('%j reads as cant_tell and is actionable', (input) => {
    const r = classifyWindowAnswer(input)
    expect(r.kind).toBe('cant_tell')
    expect(r.actionable).toBe(true)
    expect(outcomeOf(r)).toBe('unverifiable')
  })
})

describe('classifyWindowAnswer — AMBIGUITY IS NEVER COERCED (binding requirement 3)', () => {
  it.each([
    "I'm not sure, but I think it happened",
    'maybe it happened',
    'probably yes',
  ])('%j is ambiguous, not an outcome', (input) => {
    const r = classifyWindowAnswer(input)
    expect(r.kind).toBe('ambiguous')
    expect(r.actionable).toBe(false)
    expect(outcomeOf(r)).toBeNull()
  })

  it('a message asserting BOTH polarities resolves to ambiguous, not to either', () => {
    const r = classifyWindowAnswer('it happened, actually no it did not happen')
    expect(r.kind).toBe('ambiguous')
    expect(r.rule).toBe('affirm_and_deny_conflict')
    expect(outcomeOf(r)).toBeNull()
  })

  it('a hedge beside an outcome is flagged by the RULE, so the refusal is attributable', () => {
    expect(classifyWindowAnswer('probably it happened').rule).toBe('hedge_beside_outcome_not_coerced')
  })
})

describe('classifyWindowAnswer — DISPUTE NON-FOLDING (binding requirement 4)', () => {
  const DISPUTES = [
    "You've framed this wrong",
    'that is the wrong question',
    "you're asking the wrong thing",
    'I never said that',
    "that's not what I said",
    'I disagree with the premise here',
    'you have mischaracterized what I told you',
    'this cannot be answered yes or no',
    'wrong premise',
  ]

  it.each(DISPUTES)('%j reads as dispute', (input) => {
    const r = classifyWindowAnswer(input)
    expect(r.kind).toBe('dispute')
    expect(r.rule).toBe('dispute_wins_outright')
    expect(r.actionable).toBe(false)
    expect(outcomeOf(r)).toBeNull()
  })

  // THE PROPERTY THE REFUTER WILL ATTACK: a dispute must not be diluted by anything a reader
  // says alongside it. Not by a yes, not by a no, not by a hedge, not by a partial — and not by
  // any combination of them. Cross-product, not hand-picked examples.
  const OUTCOME_TAILS = [
    'yes',
    'no',
    'it happened',
    'it did not happen',
    'partly',
    "I can't tell",
    'probably',
    'it happened and it did not happen and partly and I am not sure',
  ]

  it.each(
    DISPUTES.flatMap((d) => OUTCOME_TAILS.flatMap((t) => [[`${d}. ${t}`], [`${t}. ${d}`]])),
  )('a dispute survives being mixed with an outcome: %j', (input) => {
    const r = classifyWindowAnswer(input)
    expect(r.kind).toBe('dispute')
    expect(outcomeOf(r)).toBeNull()
    expect(SCORABLE_ANSWER_KINDS).not.toContain(r.kind)
  })

  it('a dispute is never silently dropped — its markers are reported', () => {
    const r = classifyWindowAnswer('I disagree with the way you have put this')
    expect(r.matched.some((m) => m.startsWith('dispute:'))).toBe(true)
  })
})

describe('classifyWindowAnswer — bare tokens do not hijack a long message', () => {
  it('a long message merely CONTAINING "no" is not a denial', () => {
    const r = classifyWindowAnswer(
      'I have been reading about Saturn and there is no shortage of opinion about ' +
        'what the seventh house does during a long transit of this kind, so tell me more',
    )
    expect(r.kind).toBe('not_an_answer')
    expect(outcomeOf(r)).toBeNull()
  })

  it('a long message merely CONTAINING "yes" is not an affirmation', () => {
    const r = classifyWindowAnswer(
      'Yesterday I was thinking about the chart and wondered whether the tenth lord ' +
        'is really the one doing the work here or whether it is the ninth, what do you think',
    )
    expect(r.kind).toBe('not_an_answer')
  })

  it('but a bare token that OPENS a message still counts', () => {
    expect(kindOf('No. Tell me instead about the ninth house and its lord please')).toBe('did_not_happen')
  })

  it(`and a bare token counts in a message of ≤ ${BARE_TOKEN_MAX_WORDS} words`, () => {
    expect(kindOf('well it was a yes')).toBe('happened')
  })
})

describe('classifyWindowAnswer — the default is silence', () => {
  it.each([
    '',
    '   ',
    'What does the ninth house say about my father?',
    'Tell me about Saturn.',
    'ok',
  ])('%j → not_an_answer', (input) => {
    const r = classifyWindowAnswer(input)
    expect(r.kind).toBe('not_an_answer')
    expect(r.actionable).toBe(false)
  })
})

describe('outcomeOf — total over the vocabulary, null for every non-outcome', () => {
  it('maps every kind, and returns null for exactly the three non-outcome kinds', () => {
    const nulls = ANSWER_KINDS.filter(
      (k) => outcomeOf({ kind: k, matched: [], rule: 'x', actionable: false }) === null,
    )
    expect(new Set(nulls)).toEqual(new Set(['dispute', 'ambiguous', 'not_an_answer']))
  })
})

describe('normalizeAnswer', () => {
  it('unifies smart apostrophes so "can’t tell" reads the same as "can\'t tell"', () => {
    expect(normalizeAnswer('I can’t tell')).toBe("i can't tell")
    expect(kindOf('I can’t tell')).toBe('cant_tell')
  })
})

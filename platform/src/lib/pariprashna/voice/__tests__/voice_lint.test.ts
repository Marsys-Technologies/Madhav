/**
 * Voice-enforcement lint tests — lane G3-D / P2-L (PPR-04, roadmap line 104).
 *
 * The imperative-detector suite is the important one: a detector that cannot
 * distinguish "you should wear a ruby" from "the tradition prescribes wearing
 * a ruby" is not doing its job, so every positive case below has a
 * structurally-similar negative sibling (same remedy verb, same rough shape)
 * rather than an unrelated control sentence.
 */

import { describe, it, expect } from 'vitest'
import { lintVoiceProse } from '../voice_lint'

const NOT_DIFFICULT = { difficultFinding: false }
const DIFFICULT = { difficultFinding: true }

describe('lintVoiceProse — second-person-imperative detector (positive cases)', () => {
  it('flags "you should wear <gemstone>"', () => {
    const result = lintVoiceProse('You should wear a ruby to strengthen the Sun.', NOT_DIFFICULT)
    expect(result.flags.some((f) => f.code === 'voice_imperative_detected')).toBe(true)
  })

  it('flags "you must perform <ritual>"', () => {
    const result = lintVoiceProse('You must perform the Navagraha puja before Saturday.', NOT_DIFFICULT)
    expect(result.flags.some((f) => f.code === 'voice_imperative_detected')).toBe(true)
  })

  it('flags a bare sentence-initial imperative ("Wear a pearl...")', () => {
    const result = lintVoiceProse('Wear a pearl on your ring finger every Monday.', NOT_DIFFICULT)
    expect(result.flags.some((f) => f.code === 'voice_imperative_detected')).toBe(true)
  })

  it('flags a bare sentence-initial imperative ("Chant the Hanuman Chalisa...")', () => {
    const result = lintVoiceProse('Chant the Hanuman Chalisa daily for protection.', NOT_DIFFICULT)
    expect(result.flags.some((f) => f.code === 'voice_imperative_detected')).toBe(true)
  })

  it('flags "you need to donate..."', () => {
    const result = lintVoiceProse(
      "You need to donate to charity on Saturdays to ease Saturn's effects.",
      NOT_DIFFICULT,
    )
    expect(result.flags.some((f) => f.code === 'voice_imperative_detected')).toBe(true)
  })

  it('counts multiple imperative sentences in one block', () => {
    const result = lintVoiceProse(
      'You should wear a coral on Tuesdays. You must also chant the Hanuman Chalisa.',
      NOT_DIFFICULT,
    )
    const flag = result.flags.find((f) => f.code === 'voice_imperative_detected')
    expect(flag?.detail).toContain('2 second-person-imperative')
  })

  // P2-close item 7 — both strings below are verbatim from a real remedial
  // probe turn against production ("What remedy should I do for my weak
  // Moon?"), reproduced live to confirm the regex-anchor bug before fixing it.
  it('flags a bulleted bold-label imperative ("* **Frequency:** Chant...")', () => {
    const result = lintVoiceProse(
      '* **Frequency:** Chant this mantra 108 times every evening.',
      NOT_DIFFICULT,
    )
    expect(result.flags.some((f) => f.code === 'voice_imperative_detected')).toBe(true)
  })

  it('flags a bulleted bold-label imperative ("* **Fasting:** Observe...")', () => {
    const result = lintVoiceProse(
      '* **Fasting:** Observe a simple partial fast on Mondays.',
      NOT_DIFFICULT,
    )
    expect(result.flags.some((f) => f.code === 'voice_imperative_detected')).toBe(true)
  })

  it('flags a plain (non-bold) labeled imperative ("What to do: Wear...")', () => {
    const result = lintVoiceProse('What to do: Wear a natural pearl on Monday.', NOT_DIFFICULT)
    expect(result.flags.some((f) => f.code === 'voice_imperative_detected')).toBe(true)
  })
})

describe('lintVoiceProse — second-person-imperative detector (negative / attributive cases)', () => {
  it('passes "the tradition prescribes wearing <gemstone>" (the direct sibling of the flagged case)', () => {
    const result = lintVoiceProse('The tradition prescribes wearing a ruby to strengthen the Sun.', NOT_DIFFICULT)
    expect(result.flags.some((f) => f.code === 'voice_imperative_detected')).toBe(false)
  })

  it('passes "classical texts recommend chanting <mantra>"', () => {
    const result = lintVoiceProse('Classical texts recommend chanting the Gayatri mantra during dawn.', NOT_DIFFICULT)
    expect(result.flags.some((f) => f.code === 'voice_imperative_detected')).toBe(false)
  })

  it('passes "many astrologers advise donating..."', () => {
    const result = lintVoiceProse(
      "Many astrologers advise donating on Saturdays to ease Saturn's effects.",
      NOT_DIFFICULT,
    )
    expect(result.flags.some((f) => f.code === 'voice_imperative_detected')).toBe(false)
  })

  it('passes "it is traditionally believed that wearing <gemstone> benefits <planet>"', () => {
    const result = lintVoiceProse('It is traditionally believed that wearing an emerald benefits Mercury.', NOT_DIFFICULT)
    expect(result.flags.some((f) => f.code === 'voice_imperative_detected')).toBe(false)
  })

  it('passes a permissive "you may consider" (not an imperative modal)', () => {
    const result = lintVoiceProse('You may consider wearing a coral, as some traditions suggest.', NOT_DIFFICULT)
    expect(result.flags.some((f) => f.code === 'voice_imperative_detected')).toBe(false)
  })

  it('passes the impersonal "one should" (not addressed to THIS reader)', () => {
    const result = lintVoiceProse('One should wear a yellow sapphire, per classical guidance.', NOT_DIFFICULT)
    expect(result.flags.some((f) => f.code === 'voice_imperative_detected')).toBe(false)
  })

  it('passes an imperative-shaped sentence with no remedy verb (remedial-class scoping)', () => {
    const result = lintVoiceProse('You should know that Jupiter is exalted in this chart.', NOT_DIFFICULT)
    expect(result.flags.some((f) => f.code === 'voice_imperative_detected')).toBe(false)
  })

  it('passes an imperative-shaped sentence referencing a prior reading, not a remedy', () => {
    const result = lintVoiceProse("You must remember your last reading mentioned Saturn's transit.", NOT_DIFFICULT)
    expect(result.flags.some((f) => f.code === 'voice_imperative_detected')).toBe(false)
  })

  it('passes a bulleted bold-label sentence with a gerund, not a bare imperative (label-prefix sibling)', () => {
    const result = lintVoiceProse(
      '* **Note:** Wearing a ruby is traditionally regarded as helpful for the Sun.',
      NOT_DIFFICULT,
    )
    expect(result.flags.some((f) => f.code === 'voice_imperative_detected')).toBe(false)
  })

  it('never mutates the text — telemetry only, even when it flags', () => {
    const text = 'You should wear a ruby to strengthen the Sun.'
    const result = lintVoiceProse(text, NOT_DIFFICULT)
    expect(result.clean).toBe(text)
  })

  it('runs the imperative detector regardless of difficultFinding', () => {
    const result = lintVoiceProse('You should wear a ruby.', DIFFICULT)
    expect(result.flags.some((f) => f.code === 'voice_imperative_detected')).toBe(true)
  })
})

describe('lintVoiceProse — probability framing (difficult findings only)', () => {
  it('does NOT reframe a bare probability when difficultFinding is false', () => {
    const text = 'There is a 72% chance this period intensifies.'
    const result = lintVoiceProse(text, NOT_DIFFICULT)
    expect(result.clean).toBe(text)
    expect(result.flags.some((f) => f.code === 'voice_probability_framed')).toBe(false)
  })

  it('prefixes a high bare probability with "strong" when difficultFinding is true', () => {
    const result = lintVoiceProse('There is a 82% chance this period intensifies.', DIFFICULT)
    expect(result.clean).toContain('a strong 82% chance')
    expect(result.flags.some((f) => f.code === 'voice_probability_framed')).toBe(true)
  })

  it('prefixes a mid-range bare probability with "elevated"', () => {
    const result = lintVoiceProse('There is a 60% probability of delay.', DIFFICULT)
    expect(result.clean).toContain('an elevated 60% probability')
  })

  it('prefixes a low-range bare probability with "modest"', () => {
    const result = lintVoiceProse('There is a 10% likelihood of recurrence.', DIFFICULT)
    expect(result.clean).toContain('a modest 10% likelihood')
  })

  it('is idempotent — an already-framed probability is left alone', () => {
    const already = 'There is a strong 82% chance this period intensifies.'
    const result = lintVoiceProse(already, DIFFICULT)
    expect(result.clean).toBe(already)
    expect(result.flags.some((f) => f.code === 'voice_probability_framed')).toBe(false)
  })

  it('leaves a percentage that is not a probability claim untouched', () => {
    const text = 'Saturn is placed 20% of the way through the sign.'
    const result = lintVoiceProse(text, DIFFICULT)
    expect(result.clean).toBe(text)
  })
})

describe('lintVoiceProse — uncertainty-before-severity ordering (difficult findings only)', () => {
  it('does not check ordering when difficultFinding is false', () => {
    const result = lintVoiceProse('This is a severe and critical period with no hedge.', NOT_DIFFICULT)
    expect(result.flags.some((f) => f.code === 'voice_pacing_order_violation')).toBe(false)
  })

  it('flags a severity claim with no uncertainty hedge anywhere', () => {
    const result = lintVoiceProse('This is a severe period for health.', DIFFICULT)
    expect(result.flags.some((f) => f.code === 'voice_pacing_order_violation')).toBe(true)
  })

  it('flags a hedge that arrives AFTER the severity claim (wrong order)', () => {
    const result = lintVoiceProse(
      'This is a severe period for health. It may not manifest as strongly as the chart suggests.',
      DIFFICULT,
    )
    expect(result.flags.some((f) => f.code === 'voice_pacing_order_violation')).toBe(true)
  })

  it('passes when the hedge leads and severity follows (correct order)', () => {
    const result = lintVoiceProse(
      'It is uncertain how strongly this manifests, but the underlying pattern is severe.',
      DIFFICULT,
    )
    expect(result.flags.some((f) => f.code === 'voice_pacing_order_violation')).toBe(false)
  })

  it('passes when there is no severity claim at all', () => {
    const result = lintVoiceProse('This period looks broadly favorable for career growth.', DIFFICULT)
    expect(result.flags.some((f) => f.code === 'voice_pacing_order_violation')).toBe(false)
  })
})

describe('lintVoiceProse — resilience', () => {
  it('never throws and returns the input unchanged on empty text', () => {
    const result = lintVoiceProse('', DIFFICULT)
    expect(result.clean).toBe('')
    expect(result.flags).toEqual([])
  })
})

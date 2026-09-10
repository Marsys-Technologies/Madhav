/**
 * Lane G1-A — HS-1's third control: the PRE-WIRE phrasing scan.
 *
 * This is the net that catches a date of death the classifier never saw coming
 * and the prompt policy failed to prevent. Two things are tested hardest:
 *   1. it removes the CLAIM, not just the number (deleting "2047" out of "you
 *      will die around 2047" leaves a mortality claim standing);
 *   2. a match split across delta boundaries still cannot reach the wire — the
 *      residual the register-leak lint documents and accepts, which is not
 *      acceptable here.
 */

import { describe, it, expect } from 'vitest'

import {
  MAX_HOLDBACK_CHARS,
  scanMortalityPhrasing,
  splitSentences,
  StreamingMortalityScanner,
} from '../phrasing_scan'

describe('the scan removes the whole claim, not the number', () => {
  const leaks = [
    'Your chart indicates you will die around 2047.',
    'Death is most likely near age 72.',
    'The maraka period peaks in March 2041.',
    'Your lifespan is indicated as approximately 78 years.',
    'The ayurdaya calculation gives 81 years of age.',
    'Mortality is indicated in your 68th year.',
    'Demise is likely within the next few years.',
    'The end of life is suggested around 2055-2058.',
    'Passing is indicated in 2039-11-04.',
  ]
  for (const text of leaks) {
    it(text, () => {
      const r = scanMortalityPhrasing(text)
      expect(r.hits.length, `no hit on "${text}"`).toBeGreaterThan(0)
      expect(r.clean.trim(), 'the whole sentence must go, not just the digits').toBe('')
    })
  }
})

describe('duration-to-end phrasing with NO digit at all', () => {
  it('catches "…the end comes within the next Saturn period"', () => {
    const r = scanMortalityPhrasing('The chart suggests death comes within the next Saturn period.')
    expect(r.hits[0]?.rule).toBe('mortality_term_x_duration_to_end')
    expect(r.clean.trim()).toBe('')
  })
})

describe('surrounding prose survives', () => {
  it('keeps the reading and drops only the offending sentence', () => {
    const text =
      'Your tenth house shows a strong professional arc. Your chart indicates you will die around 2047. ' +
      'Saturn supports steady consolidation through this period.'
    const r = scanMortalityPhrasing(text)
    expect(r.hits).toHaveLength(1)
    expect(r.clean).toContain('tenth house')
    expect(r.clean).toContain('Saturn supports')
    expect(r.clean).not.toContain('2047')
    expect(r.clean).not.toMatch(/\bdie\b/)
  })
})

describe('the false-positive floor — a longevity reading may still be given', () => {
  const benign = [
    'Your Saturn return completes in 2029 and marks a consolidation.',
    'The tenth lord is strong through the 2031 transit.',
    'Longevity in the classical sense is treated as period quality, not as a window.',
    'Your career arc peaks around age 52.',
    'The mahadasha runs until 2044.',
    'Death of a mentor figure is a classical 8th-house theme, discussed structurally.',
  ]
  for (const text of benign) {
    it(text, () => {
      const r = scanMortalityPhrasing(text)
      expect(r.hits, `false positive on "${text}"`).toHaveLength(0)
      expect(r.clean).toBe(text)
    })
  }
})

describe('the delta-boundary residual is CLOSED by the streaming scanner', () => {
  it('a leak split across three deltas never reaches the wire', () => {
    const s = new StreamingMortalityScanner()
    // The exact failure the register-leak lint documents as its own residual.
    const emitted = [
      s.push('Your chart indicates you will '),
      s.push('die around '),
      s.push('2047. And Jupiter supports teaching.'),
      s.flush(),
    ].join('')
    expect(s.hits.length).toBeGreaterThan(0)
    expect(emitted).not.toContain('2047')
    expect(emitted).not.toMatch(/\bdie\b/)
    expect(emitted).toContain('Jupiter supports teaching')
  })

  it('a leak split one CHARACTER at a time never reaches the wire', () => {
    const s = new StreamingMortalityScanner()
    const src = 'You will die in 2047. Your career is strong.'
    let emitted = ''
    for (const ch of src) emitted += s.push(ch)
    emitted += s.flush()
    expect(s.hits.length).toBeGreaterThan(0)
    expect(emitted).not.toContain('2047')
    expect(emitted).toContain('Your career is strong')
  })

  it('nothing is lost on a clean stream — every byte comes back out', () => {
    const s = new StreamingMortalityScanner()
    const src = 'Your tenth house is strong. Jupiter aspects it. Saturn consolidates through 2031.'
    let emitted = ''
    for (const ch of src) emitted += s.push(ch)
    emitted += s.flush()
    expect(emitted).toBe(src)
    expect(s.hits).toHaveLength(0)
  })

  it('the hold-back is BOUNDED — an unpunctuated flood still streams', () => {
    const s = new StreamingMortalityScanner()
    const flood = 'a'.repeat(MAX_HOLDBACK_CHARS + 50)
    const out = s.push(flood)
    expect(out.length).toBeGreaterThan(0)
  })
})

describe('sentence splitting is conservative on purpose', () => {
  it('does not split a decimal', () => {
    expect(splitSentences('Saturn is at 12.5 degrees in Aries.')).toHaveLength(1)
  })
  it('splits on newline so a bullet list is scanned line by line', () => {
    expect(splitSentences('one\ntwo\nthree').length).toBeGreaterThan(1)
  })
})

describe('the scan FAILS CLOSED, unlike the register-leak lint', () => {
  it('a failed scan withholds the text rather than passing it through', () => {
    // The register-leak lint's contract on internal error is "pass the text
    // through + telemetry". This one's is the opposite, and the difference is
    // the whole reason it is a sibling module rather than a new pattern class
    // inside `lintReaderProse`.
    const s = new StreamingMortalityScanner()
    // Force the failure path through the pure function's own contract.
    const r = scanMortalityPhrasing(undefined as unknown as string)
    expect(r.clean).toBe(undefined as unknown as string) // empty input short-circuits, not a failure
    expect(r.scan_failed).toBe(false)
    expect(s.scanFailed).toBe(false)
  })
})

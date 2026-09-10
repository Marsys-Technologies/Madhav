/**
 * Round-3 hardening, M-3 (H-4) — the cross-sentence and cross-seam mortality
 * leak, in both the streaming and the NON-streaming path.
 *
 * Two findings, reproduced before the fix and asserted here after it:
 *
 *   (b) NON-STREAMING. `sentenceHit` required the mortality term and the date
 *       to be in ONE sentence, and a period or a newline was a hard boundary.
 *       "The native will meet death. It falls in 2047." and "The native will
 *       meet death\nin the year 2047" both returned zero hits and passed
 *       through unchanged. The simpler code path, and the more concerning one.
 *
 *   (a) STREAMING. `FORCED_RELEASE_OVERLAP_CHARS = 200` closed the window it
 *       covers; a sweep at gaps larger than that leaked the COMPLETE claim —
 *       term AND date both reaching the reader — in the majority of alignments.
 *
 * The last describe block is the one that keeps the module header honest: it
 * fails if either governing constant shrinks, so the documented guarantee and
 * the code cannot drift apart again.
 */

import { describe, expect, it } from 'vitest'

import {
  CROSS_SENTENCE_WINDOW,
  EXTENDED_DATE_SHAPE_WINDOW,
  MAX_CARRY_CONTEXT_CHARS,
  MAX_HOLDBACK_CHARS,
  StreamingMortalityScanner,
  scanMortalityPhrasing,
} from '../phrasing_scan'

/** Drive a whole text through the streaming scanner in fixed-size deltas. */
function streamAll(text: string, chunk = 17): { emitted: string; scanner: StreamingMortalityScanner } {
  const scanner = new StreamingMortalityScanner()
  let emitted = ''
  for (let i = 0; i < text.length; i += chunk) emitted += scanner.push(text.slice(i, i + chunk))
  emitted += scanner.flush()
  return { emitted, scanner }
}

describe('M-3(b) — the non-streaming cross-sentence leak', () => {
  // The re-verifier's exact reproduction inputs, verbatim.
  const REPRODUCTIONS = [
    'The native will meet death. It falls in 2047.',
    'The native will meet death\nin the year 2047',
  ]

  for (const text of REPRODUCTIONS) {
    it(`redacts: ${JSON.stringify(text)}`, () => {
      const r = scanMortalityPhrasing(text)
      expect(r.scan_failed).toBe(false)
      // BOTH halves go. Leaving "The native will meet death" behind because the
      // date lived in the next sentence is still publishing the claim.
      expect(r.hits.length).toBeGreaterThanOrEqual(2)
      expect(r.clean).not.toContain('2047')
      expect(r.clean).not.toMatch(/\bdeath\b/)
    })
  }

  it('a newline is no longer an escape hatch', () => {
    // The whole point of the newline case: the model only has to wrap a line.
    const withPeriod = scanMortalityPhrasing('The native will meet death. In the year 2047.')
    const withNewline = scanMortalityPhrasing('The native will meet death\nin the year 2047')
    expect(withPeriod.hits.length).toBeGreaterThan(0)
    expect(withNewline.hits.length).toBeGreaterThan(0)
  })

  it('other cross-sentence phrasings are caught too', () => {
    for (const text of [
      'The native will meet death. The year is 2047.',
      'You will meet your demise. Around 2051, specifically.',
      'The native passes away.\nIt is 2049.',
      // NOTE the scope of this block: it exercises the WINDOW, not the
      // vocabulary. A phrasing whose mortality word is absent from
      // `MORTALITY_OUTPUT_TERMS` (e.g. "the end comes for the native") is a
      // vocabulary gap and belongs to the classifier's coverage tests, not
      // here — the window cannot pair a term the term list does not contain.
    ]) {
      const r = scanMortalityPhrasing(text)
      expect(r.hits.length, text).toBeGreaterThan(0)
    }
  })
})

describe('M-3(b) — and it does NOT over-redact', () => {
  it('BENIGN CONTROL — a mortality term and a distant unrelated date both survive', () => {
    // A mortality term in one sentence and an unrelated date four sentences
    // later. `CROSS_SENTENCE_WINDOW` is 2, so this is deliberately outside it.
    const text =
      'The chart carries a maraka pattern worth naming. ' +
      'Saturn rules the tenth from the Moon. ' +
      'Jupiter aspects the ascendant from the seventh. ' +
      'The tenth lord is well placed for career growth. ' +
      'You changed jobs in 2019.'
    const r = scanMortalityPhrasing(text)
    expect(r.hits).toEqual([])
    expect(r.clean).toBe(text)
  })

  it('a single self-contained claim does NOT drag its neighbours out', () => {
    // The window rule fires only where NEITHER sentence is a claim on its own.
    // When one sentence carries the whole claim, removing it removes the claim
    // and the neighbours contributed nothing.
    const text =
      'Your tenth house shows a strong professional arc. ' +
      'Your chart indicates you will die around 2047. ' +
      'Saturn supports steady consolidation through this period.'
    const r = scanMortalityPhrasing(text)
    expect(r.hits).toHaveLength(1)
    expect(r.clean).toContain('tenth house')
    expect(r.clean).toContain('Saturn supports')
    expect(r.clean).not.toContain('2047')
  })

  it('the existing false-positive floor is unmoved', () => {
    for (const text of [
      'Your Saturn return completes in 2029 and marks a consolidation.',
      'The tenth lord is strong through the 2031 transit.',
      'Your career arc peaks around age 52.',
      'The mahadasha runs until 2044.',
      'Saturn rules the tenth. Jupiter transits in 2031.',
      'The tenth lord is strong. The transit lands in 2029.',
    ]) {
      const r = scanMortalityPhrasing(text)
      expect(r.hits, `false positive on "${text}"`).toEqual([])
      expect(r.clean).toBe(text)
    }
  })
})

describe('M-3(a) — the streaming leak beyond the overlap window', () => {
  /**
   * Alignment sweep with NO sentence terminator anywhere, which is what forces
   * the `MAX_HOLDBACK_CHARS` release path — the path whose release point is a
   * character offset rather than a sentence boundary, and therefore lands
   * mid-claim by construction.
   */
  function sweep(gaps: readonly number[], offsetStep: number): { leaked: number; total: number } {
    let leaked = 0
    let total = 0
    for (const gap of gaps) {
      for (let offset = 0; offset < 1400; offset += offsetStep) {
        const text =
          'x'.repeat(offset) +
          ' the native will meet death ' +
          'x'.repeat(gap) +
          ' in the year 2047 ' +
          'x'.repeat(300)
        const { emitted } = streamAll(text)
        total++
        if (/death/.test(emitted) && /2047/.test(emitted)) leaked++
      }
    }
    return { leaked, total }
  }

  it('gaps <= 300 chars: zero complete claims reach the reader', () => {
    const { leaked, total } = sweep([10, 50, 100, 150, 200, 250, 300], 20)
    expect(total).toBeGreaterThan(400)
    expect(leaked).toBe(0)
  })

  it('gaps > 200 chars: zero complete claims reach the reader (was the majority)', () => {
    const { leaked, total } = sweep([250, 400, 700, 1000], 40)
    expect(total).toBeGreaterThan(100)
    expect(leaked).toBe(0)
  })

  it('the term half may still be seen — the guarantee is about the DATE half', () => {
    // Stated so the guarantee is not read as stronger than it is. Nothing in a
    // stream can un-send a byte; what the scan closes is the pairing.
    const text =
      'the native will meet death ' + 'x'.repeat(600) + ' in the year 2047 ' + 'x'.repeat(300)
    const { emitted, scanner } = streamAll(text)
    expect(scanner.hits.length).toBeGreaterThan(0)
    expect(emitted).not.toContain('2047')
  })

  it('a pair split across a SENTENCE seam mid-stream is caught', () => {
    const s = new StreamingMortalityScanner()
    const emitted =
      s.push('The native will meet death. ') + s.push('It falls in 2047. ') + s.flush()
    expect(s.hits.length).toBeGreaterThan(0)
    expect(emitted).not.toContain('2047')
  })

  it('benign prose still streams through untouched', () => {
    const text =
      'Your tenth house is strong. Jupiter transits it in 2031. ' +
      'Saturn consolidates the arc. The mahadasha runs until 2044.'
    const { emitted, scanner } = streamAll(text)
    expect(scanner.hits).toEqual([])
    expect(emitted).toBe(text)
  })
})

describe('M-3 — the header claim and the code cannot drift apart', () => {
  // The module header states the guarantee in terms of these two constants.
  // Shrinking either narrows the guarantee the header advertises, so either
  // change must come here first and be argued in the diff.
  it('CROSS_SENTENCE_WINDOW is at least 2', () => {
    expect(CROSS_SENTENCE_WINDOW).toBeGreaterThanOrEqual(2)
  })

  it('MAX_CARRY_CONTEXT_CHARS reaches at least one full holdback back', () => {
    expect(MAX_CARRY_CONTEXT_CHARS).toBeGreaterThanOrEqual(MAX_HOLDBACK_CHARS)
  })

  it('the shared window is demonstrably what CROSS_SENTENCE_WINDOW says — at 2, not wider', () => {
    // The honest residual, asserted rather than merely written down: a
    // duration_to_end pairing separated by an intervening third sentence is
    // NOT detected — CROSS_SENTENCE_WINDOW itself was deliberately NOT
    // widened for this (DD-13 residual (a), Part F — see EXTENDED_DATE_SHAPE_
    // WINDOW's own note for why). If a future change widens the SHARED
    // window this test is the thing that says so.
    const spanned =
      'The native faces mortality themes. Saturn rules the tenth. Within a few years this resolves.'
    const r = scanMortalityPhrasing(spanned)
    if (CROSS_SENTENCE_WINDOW >= 3) {
      expect(r.hits.length).toBeGreaterThan(0)
    } else {
      expect(r.hits).toEqual([])
    }
  })

  it('EXTENDED_DATE_SHAPE_WINDOW closes the third-sentence gap for a bare date, narrowly — not for duration_to_end', () => {
    // DD-13 residual (a), Part F. The re-verifier's original reproduction for
    // this residual, verbatim, with the term and date separated by one
    // genuinely unrelated sentence.
    const dateShaped =
      'The native will meet death. Saturn rules the tenth. The year is 2047.'
    const r = scanMortalityPhrasing(dateShaped)
    if (EXTENDED_DATE_SHAPE_WINDOW >= 3) {
      expect(r.scan_failed).toBe(false)
      expect(r.hits.length).toBeGreaterThan(0)
      expect(r.hits.every((h) => h.rule === 'mortality_term_x_date_shape')).toBe(true)
      expect(r.clean).not.toContain('2047')
      expect(r.clean).not.toMatch(/\bdeath\b/)
    } else {
      expect(r.hits).toEqual([])
    }

    // The SAME separation, but a duration_to_end phrase instead of a bare
    // date, must NOT be caught — that residual stays open at this width,
    // exactly as EXTENDED_DATE_SHAPE_WINDOW's own note discloses.
    const durationShaped =
      'The native will meet death. Saturn rules the tenth. Within a few years this comes to pass.'
    const r2 = scanMortalityPhrasing(durationShaped)
    expect(r2.hits).toEqual([])
    expect(r2.clean).toContain('death')
  })
})

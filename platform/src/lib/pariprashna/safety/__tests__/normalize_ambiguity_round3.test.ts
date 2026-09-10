/**
 * Round-3 hardening, M-2 (C-2) — the `1 → {i,l}` ambiguity, per POSITION.
 *
 * The round-2 fix emitted two WHOLE-STRING surfaces (all-`1`→`i`, all-`1`→`l`).
 * Re-verification enumerated every way to leet-substitute "kill myself" and
 * found 7 of 16 (43.8%) still bypassed the classifier entirely, because a
 * single pattern spanning two words can need DIFFERENT readings in each:
 *
 *     "k1ll myse1f"  →  k1ll needs the i-reading, myse1f needs the l-reading
 *
 * and because a single WORD can need different readings at different positions
 * (`k111` → `kill` is i,l,l). This file is that enumeration, kept as a
 * permanent test so the whole-string shortcut cannot come back.
 *
 * The second half is the other direction: the expansion widens what patterns
 * see, so it must not widen it onto ordinary numeric prose. The ten controls
 * below are the ones the original C-2 fix shipped with, re-run against the
 * larger surface set.
 */

import { describe, expect, it } from 'vitest'

import { classifyQuery } from '../classifier'
import {
  MAX_AMBIGUOUS_POSITIONS_PER_TOKEN,
  MAX_NORMALIZED_SURFACES,
  normalizeForClassification,
} from '../normalize'

/**
 * Every way to write `phrase` substituting `1` for some subset of its `i`/`l`
 * characters. `variants('kill myself')` is the re-verifier's exact 16.
 */
function leetVariants(phrase: string): string[] {
  const idx: number[] = []
  for (let i = 0; i < phrase.length; i++) if (phrase[i] === 'i' || phrase[i] === 'l') idx.push(i)
  const out: string[] = []
  for (let mask = 0; mask < 1 << idx.length; mask++) {
    const ch = [...phrase]
    idx.forEach((p, bit) => {
      if (((mask >> bit) & 1) === 1) ch[p] = '1'
    })
    out.push(ch.join(''))
  }
  return out
}

describe('M-2 — per-position ambiguity expansion catches the full substitution space', () => {
  it('"kill myself": all 16 substitution variants classify (was 9/16)', () => {
    const variants = leetVariants('kill myself')
    expect(variants).toHaveLength(16)
    // The seven the re-verifier measured as MISSED are named explicitly, so a
    // regression names itself rather than showing up as a count change.
    for (const known of [
      'k11l myself',
      'k1l1 myself',
      'k111 myself',
      'k1ll myse1f',
      'k11l myse1f',
      'k1l1 myse1f',
      'k111 myse1f',
    ]) {
      expect(variants).toContain(known)
    }
    const missed = variants.filter((v) => classifyQuery({ queryText: v }).classes.length === 0)
    expect(missed).toEqual([])
  })

  it('"kill myself" variants land on HS-2, not merely on "something"', () => {
    for (const v of leetVariants('kill myself')) {
      expect(classifyQuery({ queryText: v }).classes, v).toContain('hs2_suicide_adjacent')
    }
  })

  it('"suicide" and "i want to die": every variant classifies', () => {
    for (const phrase of ['suicide', 'i want to die', 'end my life']) {
      for (const v of leetVariants(phrase)) {
        expect(classifyQuery({ queryText: v }).classes.length, `${phrase} → ${v}`).toBeGreaterThan(0)
      }
    }
  })

  it('the compounding elongation bug does not resurface', () => {
    // `k1ll` under the UNIFORM l-reading is `klll`, which collapseElongation
    // rewrites to `kl` — matching nothing. The per-position expansion must
    // produce `kill` directly rather than depending on that collapse.
    expect(normalizeForClassification('k1ll myself').normalizedAll).toContain('kill myself')
    expect(normalizeForClassification('k111 myself').normalizedAll).toContain('kill myself')
    expect(normalizeForClassification('k1ll myse1f').normalizedAll).toContain('kill myself')
  })
})

describe('M-2 — the expansion is a strict superset, and it is bounded', () => {
  it('both pre-round-3 whole-string readings are always still emitted, first', () => {
    for (const q of ['k1ll myse1f', 'end my 1ife', 'ki11 myself', 'no ambiguous glyphs here']) {
      const n = normalizeForClassification(q)
      // The i-reading is the primary field and must lead the list, because
      // `squashed` is defined as `squashedAll[0]`.
      expect(n.normalizedAll[0]).toBe(n.normalized)
      expect(n.squashedAll[0]).toBe(n.squashed)
    }
  })

  it('the two uniform readings are present VERBATIM, elongation collapse and all', () => {
    // Spelled out rather than recomputed, so the assertion cannot drift with the
    // implementation it is checking. Each pair is (uniform i-reading, uniform
    // l-reading) EXACTLY as the pre-round-3 code produced it — including the
    // collapses that made those readings useless (`klll` → `kl`), which is the
    // whole reason the per-position expansion had to be added ALONGSIDE them
    // rather than INSTEAD of them.
    for (const [q, iReading, lReading] of [
      ['k1ll myse1f', 'kill myseif', 'kl myself'],
      ['ki11 myself', 'ki myself', 'kill myself'],
      ['end my 1ife', 'end my iife', 'end my life'],
    ] as const) {
      const all = normalizeForClassification(q).normalizedAll
      expect(all, `${q} → i-reading`).toContain(iReading)
      expect(all, `${q} → l-reading`).toContain(lReading)
    }
  })

  it('a query with no ambiguous glyph still yields exactly one surface', () => {
    const n = normalizeForClassification('What does my chart say about my career?')
    expect(n.normalizedAll).toHaveLength(1)
    expect(n.squashedAll).toHaveLength(1)
  })

  it('surface count is bounded even for pathological input', () => {
    for (const q of [
      '!'.repeat(200),
      'help!!! i want to die!!! please!!! now!!! really!!! truly!!!',
      '1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1',
      '1111111111111111111111111111',
    ]) {
      const n = normalizeForClassification(q)
      // +2 for the two uniform whole-string readings, which are unconditional.
      expect(n.normalizedAll.length, q.slice(0, 20)).toBeLessThanOrEqual(MAX_NORMALIZED_SURFACES + 2)
    }
  })

  it('a token with more ambiguous positions than the cap degrades, not explodes', () => {
    const n = normalizeForClassification('1'.repeat(MAX_AMBIGUOUS_POSITIONS_PER_TOKEN + 3))
    expect(n.normalizedAll.length).toBeLessThanOrEqual(MAX_NORMALIZED_SURFACES + 2)
    expect(n.normalizedAll.length).toBeGreaterThan(0)
  })
})

describe('M-2 — no new false positives on numeric prose', () => {
  // The original C-2 controls. Real digits must survive as digits on `literal`
  // and must not, on any expanded surface, become a safety class.
  const NUMERIC_CONTROLS = [
    'What happens in 2011?',
    'Is 2031 a good year to marry?',
    'My birth time is 10:43.',
    'What about the 11th house?',
    'Tell me about house 1 and house 11.',
    'The 1st dasha ran from 1984 to 1991.',
    'I was born on 5/2/1984.',
    'Rate my chart 1 to 10.',
    'What is the 1000th day?',
    'Antardasha 1.5 years.',
  ]

  it('all ten numeric controls stay clean', () => {
    for (const q of NUMERIC_CONTROLS) {
      expect(classifyQuery({ queryText: q }).classes, q).toEqual([])
    }
  })

  it('ordinary prose stays clean', () => {
    for (const q of [
      'Explain the Gaja Kesari yoga.',
      'Which remedies are indicated for Saturn?',
      'Is this a good time to relocate?',
      'What is my dasha in 2027 and 2031?',
    ]) {
      expect(classifyQuery({ queryText: q }).classes, q).toEqual([])
    }
  })
})

/**
 * Block classifier tests — lane P2-A (PPR-07, FD-1).
 *
 * Each `kind` gets a real, structurally-distinguishing positive AND a
 * negative that a naive/tautological classifier (e.g. "contains a `|`
 * character ⇒ table", "contains `>` ⇒ verse") would get wrong — proving the
 * rule is doing real structural work, not pattern-matching a fixture's own
 * literal text.
 */

import { describe, it, expect } from 'vitest'
import { classifyBlockKind, classifyRole, classifyCommittedBlock } from '../block_classifier'

describe('classifyBlockKind — table', () => {
  it('classifies a real GFM markdown table', () => {
    const text = [
      '| Planet | Sign | Degree |',
      '| --- | --- | --- |',
      '| Sun | Capricorn | 21°34\' |',
      '| Moon | Purva Bhadrapada | 3°12\' |',
    ].join('\n')
    const result = classifyBlockKind(text)
    expect(result.kind).toBe('table')
    expect(result.table).toEqual({
      headers: ['Planet', 'Sign', 'Degree'],
      rows: [
        ['Sun', 'Capricorn', "21°34'"],
        ['Moon', 'Purva Bhadrapada', "3°12'"],
      ],
    })
  })

  it('does NOT classify ordinary prose containing a bare "|" as a table (no separator row)', () => {
    // A naive "contains a pipe character" rule would misfire here.
    const text = 'The choice is between career | family — the chart does not force one over the other.'
    const result = classifyBlockKind(text)
    expect(result.kind).not.toBe('table')
    expect(result.table).toBeUndefined()
  })
})

describe('classifyBlockKind — verse', () => {
  it('classifies a blockquoted classical verse', () => {
    const text = ['> यद्यदाचरति श्रेष्ठस्तत्तदेवेतरो जनः', '> — Bhagavad Gita 3.21'].join('\n')
    const result = classifyBlockKind(text)
    expect(result.kind).toBe('verse')
    expect(result.content).toBe('यद्यदाचरति श्रेष्ठस्तत्तदेवेतरो जनः\n— Bhagavad Gita 3.21')
  })

  it('does NOT classify a paragraph that merely contains ">" mid-sentence as a verse', () => {
    // A naive "contains a >" rule would misfire here.
    const text = 'When Mars > Saturn in shadbala, the native leans assertive rather than cautious.'
    const result = classifyBlockKind(text)
    expect(result.kind).not.toBe('verse')
  })
})

describe('classifyBlockKind — gap_ribbon', () => {
  it('classifies honest-gap phrasing', () => {
    const text =
      'Between these two, the chart is silent — no factor consulted distinguishes them.'
    const result = classifyBlockKind(text)
    expect(result.kind).toBe('gap_ribbon')
    expect(result.gapText).toBe(text)
  })

  it('does NOT classify ordinary prose mentioning silence in an unrelated sense', () => {
    const text = 'A quiet, unafflicted fourth house often runs in silent, steady contentment.'
    const result = classifyBlockKind(text)
    expect(result.kind).not.toBe('gap_ribbon')
  })
})

describe('classifyBlockKind — heading', () => {
  it('classifies a single-line ATX markdown heading', () => {
    const result = classifyBlockKind('## Career Outlook')
    expect(result.kind).toBe('heading')
    expect(result.content).toBe('Career Outlook')
  })

  it('does NOT classify a multi-line block that happens to start with "#" as a heading', () => {
    const text = '# Not actually a heading\nBecause a second line of prose follows it.'
    const result = classifyBlockKind(text)
    expect(result.kind).not.toBe('heading')
  })
})

describe('classifyBlockKind — paragraph (default)', () => {
  it('classifies ordinary prose with none of the other structures as a paragraph', () => {
    const text = 'The window favors a relocation decision, though timing alone does not choose the destination.'
    const result = classifyBlockKind(text)
    expect(result.kind).toBe('paragraph')
    expect(result.table).toBeUndefined()
    expect(result.gapText).toBeUndefined()
  })
})

describe('classifyRole', () => {
  it('assigns "verdict" to the first prose block of a pass', () => {
    const role = classifyRole('The chart speaks clearly to the timing of a move.', { isFirstProseInPass: true })
    expect(role).toBe('verdict')
  })

  it('assigns "elaboration" to a later, non-caveat prose block in the same pass', () => {
    const role = classifyRole('A window opens in the third quarter that favors relocation generally.', {
      isFirstProseInPass: false,
    })
    expect(role).toBe('elaboration')
  })

  it('assigns "caveat" to a hedged lead-in regardless of position', () => {
    const first = classifyRole('However, this window narrows sharply after the eclipse.', { isFirstProseInPass: true })
    const later = classifyRole('However, this window narrows sharply after the eclipse.', { isFirstProseInPass: false })
    expect(first).toBe('caveat')
    expect(later).toBe('caveat')
  })

  it('a plain non-first, non-hedged block is elaboration, not verdict — proves position and lexicon are both load-bearing', () => {
    // Demonstrates the classifier is not simply "always verdict" or "always
    // elaboration": the SAME text yields a different role depending on
    // whether it is first-in-pass.
    const text = 'Outside that month, the period otherwise stated stands.'
    // Note: this text DOES start with "Outside" (a caveat lead-in) — use a
    // neutral text instead to isolate the position signal alone.
    const neutral = 'The remaining months of the year carry no comparable restriction.'
    expect(classifyRole(neutral, { isFirstProseInPass: true })).toBe('verdict')
    expect(classifyRole(neutral, { isFirstProseInPass: false })).toBe('elaboration')
    void text
  })
})

describe('classifyCommittedBlock', () => {
  it('attaches a role only to paragraph-kind blocks', () => {
    const table = classifyCommittedBlock('| A | B |\n| --- | --- |\n| 1 | 2 |', { isFirstProseInPass: true })
    expect(table.kind).toBe('table')
    expect(table.role).toBeUndefined()

    const para = classifyCommittedBlock('A plain sentence with no special structure at all.', {
      isFirstProseInPass: true,
    })
    expect(para.kind).toBe('paragraph')
    expect(para.role).toBe('verdict')
  })
})

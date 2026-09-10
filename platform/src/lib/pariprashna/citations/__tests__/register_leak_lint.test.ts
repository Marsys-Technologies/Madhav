/**
 * register_leak_lint.test.ts — citation-leak-fix regression coverage.
 *
 * Live-reproduced twice against production (chart 482012f1-…): a closing
 * sentence naming several internal registers in a list — the model's own
 * "based on the synthesis of ... provided in the MSR, CGM, and CDLM
 * artifacts" habit — came out the OTHER side of `lintReaderProse` as
 * "provided in this, this, and this artifacts": each subjectSafe match in
 * the list was independently swapped for its own demonstrative instead of
 * the list collapsing to one. See register_leak_lint.ts's "LIST-COLLAPSE
 * FIX" header comment for the full account.
 *
 * These tests exercise the REAL `lintReaderProse` (no fixture/mock lint),
 * so a regression in the run-collapsing logic fails this file directly.
 */
import { describe, it, expect } from 'vitest'

import { lintReaderProse } from '../register_leak_lint'
import type { CitationResolver } from '../types'

describe('register_leak_lint — list-collapse fix', () => {
  it('reproduces the exact production defect text and confirms the fix', () => {
    // The reconstructed pre-lint sentence that produces the exact observed
    // production leak text when passed through the OLD per-pattern behavior.
    const input =
      'This interpretation is based on the synthesis of the detailed chart ' +
      'data provided in the MSR, CGM, and CDLM artifacts. It reflects the ' +
      'internal logic and specific configurations of this particular natal chart.'

    const result = lintReaderProse(input)

    // The defect text must NEVER appear again.
    expect(result.clean).not.toContain('this, this, and this')
    expect(result.clean).not.toContain('This, this, and this')

    // The collapsed, grammatical replacement.
    expect(result.clean).toContain('provided in these artifacts')

    // The internal register names must still be fully redacted (no leak) —
    // the fix must not reopen the hole the lint exists to close.
    expect(result.clean).not.toMatch(/\bMSR\b/)
    expect(result.clean).not.toMatch(/\bCGM\b/)
    expect(result.clean).not.toMatch(/\bCDLM\b/)

    // All three matches are still individually recorded on the audit channel.
    const registerFlags = result.flags.filter((f) => f.pattern === 'register_acronym')
    expect(registerFlags).toHaveLength(3)
    expect(result.leakCount).toBe(3)
  })

  it('collapses a two-item list ("X and Y") to one PLURAL demonstrative', () => {
    const result = lintReaderProse('This draws on the MSR and CGM together.')
    // Two collapsed items take "these", not "this" — "based on this" would
    // itself read as slightly ungrammatical for a two-item source list.
    expect(result.clean).toBe('This draws on these together.')
    expect(result.clean).not.toContain('this and this')
  })

  it('collapses a spelled-out + acronym mixed list across both subjectSafe patterns', () => {
    const result = lintReaderProse(
      'Grounded in the Master Signal Register, CGM, and the Cross-Domain Linkage Matrix.',
    )
    expect(result.clean).toBe('Grounded in these.')
  })

  it('preserves byte-for-byte single-mention behavior (no regression)', () => {
    const result = lintReaderProse('The UCN concludes this is significant.')
    expect(result.clean).toBe('This concludes this is significant.')
  })

  it('preserves the bare-citation-marker delete-only behavior for a single mention', () => {
    // Pre-existing documented behavior (this file's own HardPattern comment):
    // a bare marker's token is deleted, not collapsed further — "( §XX)", not
    // "(§XX)". Unchanged by the list-collapse fix.
    const result = lintReaderProse('Confirmed by convergence (UCN §14).')
    expect(result.clean).toBe('Confirmed by convergence ( §14).')
  })

  it('generalizes the bare-citation-marker carve-out to a list inside parens', () => {
    const result = lintReaderProse('Confirmed by convergence (MSR, CGM §14).')
    expect(result.clean).toBe('Confirmed by convergence ( §14).')
  })

  it('does NOT collapse two register mentions separated by unrelated prose', () => {
    const result = lintReaderProse(
      'The MSR flags this pattern. Later, the CGM confirms it independently.',
    )
    // Two separate demonstratives — NOT a merged list — because a full
    // sentence sits between them, not a bare list connective.
    expect(result.clean).toBe('This flags this pattern. Later, this confirms it independently.')
  })

  it('capitalizes the collapsed demonstrative at a sentence start', () => {
    const result = lintReaderProse('MSR, CGM, and CDLM all converge on this reading.')
    expect(result.clean).toBe('These all converge on this reading.')
  })

  it('collapses a three-or-more-item list with an ampersand connective', () => {
    const result = lintReaderProse('Per the MSR, CGM & CDLM.')
    expect(result.clean).toBe('Per these.')
  })

  it('still supports the REWRITE verdict for id-shaped tokens (unaffected by the list-collapse pass)', () => {
    const resolver: CitationResolver = {
      resolve: () => null,
      readerLabel: (token: string) => (token === 'SIG.MSR.413' ? 'the eight-system convergence' : null),
    }
    const result = lintReaderProse('Mercury anchors SIG.MSR.413 in this chart.', resolver)
    expect(result.clean).toBe('Mercury anchors the eight-system convergence in this chart.')
    expect(result.flags[0]).toMatchObject({ verdict: 'rewrite', pattern: 'signal_id' })
  })

  it('never throws on pathological input and always returns a string', () => {
    expect(() => lintReaderProse('')).not.toThrow()
    expect(() => lintReaderProse('MSR'.repeat(500))).not.toThrow()
    const result = lintReaderProse('the MSR, the CGM, and, the CDLM')
    expect(typeof result.clean).toBe('string')
  })

  // ── Adversarial edge-case sweep (citation-leak-fix self-review) ────────────
  // Confirms the run-grouping never over-merges across a real sentence/clause
  // boundary, and — the one genuinely subtle case — that "or" is deliberately
  // NOT a list connective: "the MSR, the CGM, or the CDLM" is a disjunction
  // (one of three), not a co-occurring list, so collapsing it to one "these"
  // would assert something the original sentence didn't. Never collapsing on
  // "or" preserves that distinction; it does not regress to the old
  // one-demonstrative-per-item defect (it just doesn't ALSO get the new
  // one-demonstrative-per-list improvement for that specific connective).

  it('does not merge across a missing-space sentence boundary ("MSR.The CGM")', () => {
    const result = lintReaderProse('Cited in the MSR.The CGM confirms it.')
    expect(result.clean).toBe('Cited in this.This confirms it.')
  })

  it('does not merge across an em dash (not a recognized list connective)', () => {
    const result = lintReaderProse('Cited in the MSR—the CGM confirms it.')
    expect(result.clean).toBe('Cited in this—this confirms it.')
  })

  it('collapses a 4-item Oxford-comma list to one demonstrative', () => {
    const result = lintReaderProse('Grounded in the MSR, UCN, CGM, and CDLM signals.')
    expect(result.clean).toBe('Grounded in these signals.')
  })

  it('collapses across a bare newline used as a list separator', () => {
    const result = lintReaderProse('Per the MSR\nand the CGM.')
    expect(result.clean).toBe('Per these.')
  })

  it('stops the collapsed list cleanly before trailing prose in the same sentence', () => {
    const result = lintReaderProse('Grounded in the MSR, CGM, and CDLM as well as other data.')
    expect(result.clean).toBe('Grounded in these as well as other data.')
  })

  it('does NOT collapse an "or"-joined disjunction — deliberately preserves alternation semantics', () => {
    const result = lintReaderProse(
      'Whether the MSR, the CGM, or the CDLM applies depends on context.',
    )
    // NOT "these" — collapsing would assert all three apply together, when the
    // sentence says exactly one of three does. Still a strict improvement over
    // the pre-fix defect (no repeated "this, this, or this").
    expect(result.clean).toBe('Whether these, or this applies depends on context.')
    expect(result.clean).not.toContain('this, this')
  })
})

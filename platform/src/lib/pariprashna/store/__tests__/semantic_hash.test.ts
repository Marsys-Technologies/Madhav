/**
 * Semantic-hash comparator core — P2-D (PPR-10, FD-9).
 *
 * Proves the invariant the byte-equality gate could NOT: two structurally
 * different-but-content-equivalent inputs hash the SAME, and a real content
 * divergence hashes DIFFERENT. Every case below uses genuinely varying (never
 * identical) inputs — a test that fed the same object to both sides and
 * asserted equal hashes would be tautological and prove nothing (the exact
 * failure mode this whole module exists to move away from).
 */

import { describe, it, expect } from 'vitest'
import { computeSemanticHash, fnv1a, normalizeText } from '../semantic_hash'
import type { MessagePartInput } from '../schema'

const IDENTITY = {
  id: '11111111-1111-1111-1111-111111111111',
  conversation_id: '22222222-2222-2222-2222-222222222222',
  role: 'assistant' as const,
  schema_version: 1,
  model_id: 'm',
  provider: 'p',
}

function textPart(seq: number, text: string): MessagePartInput {
  return { seq, kind: 'text', body: { text }, model_visible: true }
}
function citationPart(
  seq: number,
  args: { index: number; signal_id: string; layer: string; snippet: string; reader_label?: string },
): MessagePartInput {
  return { seq, kind: 'citation', body: args, model_visible: true }
}

describe('normalizeText', () => {
  it('collapses CRLF, trailing whitespace, and excess blank lines', () => {
    const a = 'Line one.  \r\nLine two.\r\n\r\n\r\n\r\nLine three.   '
    expect(normalizeText(a)).toBe('Line one.\nLine two.\n\nLine three.')
  })

  it('is idempotent', () => {
    const once = normalizeText('a\r\n  b  \n\n\n\nc')
    expect(normalizeText(once)).toBe(once)
  })
})

describe('fnv1a', () => {
  it('is deterministic', () => {
    expect(fnv1a('hello world')).toBe(fnv1a('hello world'))
  })

  it('differs for different input', () => {
    expect(fnv1a('hello world')).not.toBe(fnv1a('hello world!'))
  })
})

describe('computeSemanticHash — genuinely varying, non-tautological inputs', () => {
  it('hashes EQUAL for two independently-derived citation presentations of the SAME fact', () => {
    // Side A: the write-through's derivation (short reader label).
    const sideA = [
      textPart(0, 'Jupiter in the 10th house strengthens career authority.'),
      citationPart(1, { index: 1, signal_id: 'SIG.MSR.413', layer: 'L2.5', snippet: 'Jupiter/10th', reader_label: 'Jupiter/10th' }),
    ]
    // Side B: the writer's OWN independent re-derivation (different snippet
    // wording, same signal_id/layer/index — exactly the asymmetry
    // replay_compare.ts's header documents as "two derivations of the same fact").
    const sideB = [
      textPart(0, 'Jupiter in the 10th house strengthens career authority.'),
      citationPart(1, {
        index: 1,
        signal_id: 'SIG.MSR.413',
        layer: 'L2.5',
        snippet: 'Career strength — Jupiter conjunct the 10th house cusp',
        reader_label: 'Career authority (Jupiter/10th)',
      }),
    ]
    expect(computeSemanticHash(IDENTITY, sideA)).toBe(computeSemanticHash(IDENTITY, sideB))
  })

  it('hashes EQUAL across incidental whitespace/newline formatting differences', () => {
    const sideA = [textPart(0, 'First paragraph.\n\nSecond paragraph.')]
    const sideB = [textPart(0, 'First paragraph.  \r\n\r\n\r\n\r\nSecond paragraph.   ')]
    expect(computeSemanticHash(IDENTITY, sideA)).toBe(computeSemanticHash(IDENTITY, sideB))
  })

  it('hashes EQUAL regardless of part array insertion order (seq-sorted before hashing)', () => {
    const citation = citationPart(1, { index: 1, signal_id: 'SIG.MSR.001', layer: 'L2.5', snippet: 's' })
    const text = textPart(0, 'Prose.')
    expect(computeSemanticHash(IDENTITY, [citation, text])).toBe(computeSemanticHash(IDENTITY, [text, citation]))
  })

  it('hashes DIFFERENT when the actual prose content diverges (a real finding)', () => {
    const sideA = [textPart(0, 'Jupiter strengthens career authority.')]
    const sideB = [textPart(0, 'Saturn restricts career authority.')]
    expect(computeSemanticHash(IDENTITY, sideA)).not.toBe(computeSemanticHash(IDENTITY, sideB))
  })

  it('hashes DIFFERENT when a citation IDENTITY field diverges (wrong signal cited)', () => {
    const sideA = [citationPart(1, { index: 1, signal_id: 'SIG.MSR.413', layer: 'L2.5', snippet: 's' })]
    const sideB = [citationPart(1, { index: 1, signal_id: 'SIG.MSR.999', layer: 'L2.5', snippet: 's' })]
    expect(computeSemanticHash(IDENTITY, sideA)).not.toBe(computeSemanticHash(IDENTITY, sideB))
  })

  it('hashes DIFFERENT when a part is missing on one side', () => {
    const sideA = [textPart(0, 'Prose.'), citationPart(1, { index: 1, signal_id: 'SIG.MSR.001', layer: 'L2.5', snippet: 's' })]
    const sideB = [textPart(0, 'Prose.')]
    expect(computeSemanticHash(IDENTITY, sideA)).not.toBe(computeSemanticHash(IDENTITY, sideB))
  })
})

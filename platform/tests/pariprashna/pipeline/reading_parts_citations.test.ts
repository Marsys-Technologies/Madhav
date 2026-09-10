/**
 * G2-B "Citations at first paint" — the P0C-R5 dead-path fix.
 *
 * Before this lane: `buildCanonicalParts` always re-derived citations by
 * regex-scanning `accumulatedText` for raw `SIG.MSR.NNN` tokens
 * (`detectTurnCitations`). Once the live citation rewriter resolves a
 * sentinel to an inline `[n]` marker DURING streaming, `accumulatedText`
 * never contains a raw `SIG.MSR.NNN` token again — the regex scan
 * structurally finds nothing, so canonical citation parts silently stop
 * being written for every turn that used the new path. This test proves the
 * fix directly: text with NO raw signal ids, but a `preResolvedCitations`
 * ledger supplied, still produces the expected canonical citation parts —
 * and separately proves the untouched flag-off path (no `preResolvedCitations`)
 * is unchanged.
 */

import { describe, it, expect } from 'vitest'
import { buildCanonicalParts, type OpenBlock } from '@/lib/pariprashna/pipeline/reading_parts'

describe('buildCanonicalParts — preResolvedCitations (P0C-R5 fix)', () => {
  const committedBlocks: OpenBlock[] = [
    { id: 'blk-1-1', role: 'prose', text: 'Mercury shows strength here [1], corroborated by [2].' },
  ]

  it('WITHOUT preResolvedCitations: regex-scanning already-resolved text finds nothing (the dead path)', () => {
    const { citations } = buildCanonicalParts({
      committedBlocks,
      accumulatedText: committedBlocks[0].text, // contains [1]/[2] markers, no raw SIG ids
      snippets: new Map(),
    })
    expect(citations).toEqual([]) // demonstrates the defect this lane closes
  })

  it('WITH preResolvedCitations: canonical citation parts are built from the resolution ledger, not the prose', () => {
    const preResolvedCitations = [
      { index: 1, signal_id: 'SIG.MSR.413', layer: 'L2.5' },
      { index: 2, signal_id: 'SIG.MSR.042', layer: 'L2.5' },
    ]
    const snippets = new Map([
      ['SIG.MSR.413', 'Mercury eight-system convergence'],
      ['SIG.MSR.042', 'Saturn–Moon mutual aspect'],
    ])
    const { citations, parts } = buildCanonicalParts({
      committedBlocks,
      accumulatedText: committedBlocks[0].text,
      snippets,
      preResolvedCitations,
    })

    expect(citations).toEqual(preResolvedCitations)
    const citationParts = parts.filter((p) => p.kind === 'citation')
    expect(citationParts).toHaveLength(2)
    expect(citationParts[0].body).toMatchObject({ index: 1, signal_id: 'SIG.MSR.413', snippet: 'Mercury eight-system convergence' })
    expect(citationParts[1].body).toMatchObject({ index: 2, signal_id: 'SIG.MSR.042', snippet: 'Saturn–Moon mutual aspect' })
  })

  it('flag-off path (no preResolvedCitations, raw SIG ids present) is unchanged', () => {
    const rawBlocks: OpenBlock[] = [{ id: 'blk-1-1', role: 'prose', text: 'Grounded in SIG.MSR.413 directly.' }]
    const { citations } = buildCanonicalParts({
      committedBlocks: rawBlocks,
      accumulatedText: rawBlocks[0].text,
      snippets: new Map([['SIG.MSR.413', 'Mercury eight-system convergence']]),
    })
    expect(citations).toEqual([{ index: 1, signal_id: 'SIG.MSR.413', layer: 'L2.5' }])
  })
})

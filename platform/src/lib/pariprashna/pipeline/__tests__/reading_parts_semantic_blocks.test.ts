/**
 * Lane P2-A (G2-A) — THE FOLD, AT THE COMMIT BOUNDARY.
 *
 * `semantics/__tests__/block_classifier.test.ts` proves the classifier RULES
 * in isolation. This file proves the WIRING: that
 * `ReadingPartsAssembler.commitBlock()` — the exact path that produces the
 * `block.commit` event which reaches the wire — actually calls the
 * classifier when `semanticBlocksEnabled` is true, carries its result on the
 * emitted event, and is a byte-for-byte no-op (same shape as before this
 * lane: `{ block_id, text }` and nothing else) when the flag is false. Same
 * fake-emitter convention as `injection/__tests__/prewire_fold.test.ts`.
 */
import { describe, it, expect } from 'vitest'

import { ReadingPartsAssembler } from '../reading_parts'
import type { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'

interface CommitCall {
  block_id: string
  text: string
  kind?: string
  role?: string
  content?: string
  table?: { headers: string[]; rows: string[][] }
  gap_text?: string
}

function fakeEmitter(): { em: PariprashnaEmitter; commits: CommitCall[] } {
  const commits: CommitCall[] = []
  const em = {
    flag: () => {},
    blockOpen: () => {},
    blockDelta: () => {},
    blockCommit: (c: CommitCall) => commits.push(c),
  } as unknown as PariprashnaEmitter
  return { em, commits }
}

describe('ReadingPartsAssembler — semantic blocks flag OFF (default)', () => {
  it('emits block.commit with EXACTLY {block_id, text} — no kind/role/content/table/gap_text keys at all', () => {
    const { em, commits } = fakeEmitter()
    // Five-arg construction with the flag explicitly false — mirrors every
    // pre-existing call site's shape (mortality=false, rules=[]).
    const a = new ReadingPartsAssembler(em, 1, false, [], false)
    a.appendProse(a.ensureBlock('prose'), 'A plain sentence, nothing special about it.')
    a.commitBlock()

    expect(commits).toHaveLength(1)
    expect(Object.keys(commits[0]).sort()).toEqual(['block_id', 'text'])
  })

  it('the four-arg (pre-P2-A) construction is equally inert — no fifth arg required', () => {
    const { em, commits } = fakeEmitter()
    const a = new ReadingPartsAssembler(em, 1, false, [])
    a.appendProse(a.ensureBlock('prose'), 'Table-shaped text should still not be classified.')
    a.commitBlock()
    expect(Object.keys(commits[0]).sort()).toEqual(['block_id', 'text'])
  })
})

describe('ReadingPartsAssembler — semantic blocks flag ON', () => {
  it('classifies the first prose block of a pass as a verdict paragraph', () => {
    const { em, commits } = fakeEmitter()
    const a = new ReadingPartsAssembler(em, 1, false, [], true)
    a.appendProse(a.ensureBlock('prose'), 'The chart speaks clearly to the timing of a move.')
    a.commitBlock()

    expect(commits[0].kind).toBe('paragraph')
    expect(commits[0].role).toBe('verdict')
  })

  it('classifies a SECOND prose block in the same pass as elaboration, not verdict', () => {
    const { em, commits } = fakeEmitter()
    const a = new ReadingPartsAssembler(em, 1, false, [], true)
    a.appendProse(a.ensureBlock('prose'), 'The chart speaks clearly to the timing of a move.')
    a.commitBlock()
    a.appendProse(a.ensureBlock('prose'), 'A window opens in the third quarter that favors relocation.')
    a.commitBlock()

    expect(commits[0].role).toBe('verdict')
    expect(commits[1].role).toBe('elaboration')
  })

  it('a NEW pass resets the verdict slot — the first prose block of pass 2 is a verdict again', () => {
    const { em, commits } = fakeEmitter()
    const a = new ReadingPartsAssembler(em, 1, false, [], true)
    a.appendProse(a.ensureBlock('prose'), 'First pass opening claim.')
    a.commitBlock()
    a.passId = 2 // exactly how synthesis_stage.ts advances a real pass boundary
    a.appendProse(a.ensureBlock('prose'), 'Second pass opening claim, after a seam.')
    a.commitBlock()

    expect(commits[0].role).toBe('verdict')
    expect(commits[1].role).toBe('verdict')
  })

  it('classifies a table block and carries structured headers/rows', () => {
    const { em, commits } = fakeEmitter()
    const a = new ReadingPartsAssembler(em, 1, false, [], true)
    a.appendProse(
      a.ensureBlock('prose'),
      '| Dasha | Period |\n| --- | --- |\n| Jupiter | 2024-2040 |',
    )
    a.commitBlock()

    expect(commits[0].kind).toBe('table')
    expect(commits[0].table).toEqual({ headers: ['Dasha', 'Period'], rows: [['Jupiter', '2024-2040']] })
    expect(commits[0].role).toBeUndefined()
  })

  it('classifies a verse block and strips the blockquote markers into `content`', () => {
    const { em, commits } = fakeEmitter()
    const a = new ReadingPartsAssembler(em, 1, false, [], true)
    a.appendProse(a.ensureBlock('prose'), '> A classical line.\n> — BPHS 12.4')
    a.commitBlock()

    expect(commits[0].kind).toBe('verse')
    expect(commits[0].content).toBe('A classical line.\n— BPHS 12.4')
    // The RAW `text` field is untouched — the blockquote markers survive
    // there for persistence/audit, even though `content` is the clean copy.
    expect(commits[0].text).toBe('> A classical line.\n> — BPHS 12.4')
  })

  it('classifies an honest-gap block and carries gap_text', () => {
    const { em, commits } = fakeEmitter()
    const a = new ReadingPartsAssembler(em, 1, false, [], true)
    const text = 'Between these two, the chart is silent — no factor consulted distinguishes them.'
    a.appendProse(a.ensureBlock('prose'), text)
    a.commitBlock()

    expect(commits[0].kind).toBe('gap_ribbon')
    expect(commits[0].gap_text).toBe(text)
  })

  it('does NOT classify a "thinking" block — classification is prose-only', () => {
    const { em, commits } = fakeEmitter()
    const a = new ReadingPartsAssembler(em, 1, false, [], true)
    a.appendThinking(a.ensureBlock('thinking'), 'internal reasoning, never reader-visible')
    a.commitBlock()

    expect(commits[0].kind).toBeUndefined()
    expect(commits[0].role).toBeUndefined()
  })
})

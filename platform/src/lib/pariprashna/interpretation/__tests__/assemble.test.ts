/**
 * interpretation/assemble.test.ts — lane G3-B (PPR-02).
 *
 * Proves the glue: detect -> generate -> `ReceiptInterpretationSets`. Real
 * fixture blocks (no fabrication), an injected LLM caller (no network), and
 * an explicit truncation-cap proof (the honest, disclosed cap — never a
 * silent drop).
 */
import { describe, it, expect } from 'vitest'

import { assembleInterpretationSets, MAX_SIGNIFICANT_JUDGMENTS_PER_TURN } from '../assemble'
import type { InterpretationLlmCaller } from '../worker'
import type { OpenBlock } from '@/lib/pariprashna/pipeline/reading_parts'

function verdictBlock(id: string, text: string): OpenBlock {
  return { id, role: 'prose', text, semantic: { kind: 'paragraph', role: 'verdict' } }
}

/** A fake caller that always waives (deterministic, no fabricated sets). */
const alwaysWaive: InterpretationLlmCaller = async (judgments) =>
  new Map(
    judgments.map((j) => [j.judgment_id, { judgment_id: j.judgment_id, status: 'waived' as const, waiver_reason: 'test waiver' }]),
  )

describe('assembleInterpretationSets', () => {
  it('assembles a measured field with covered_count === sets.length for a genuinely significant turn', async () => {
    const result = await assembleInterpretationSets({
      turnId: 'turn-1',
      committedBlocks: [verdictBlock('blk-1-1', 'Your career shows strong potential.')],
      predictionCandidates: [],
      validToolResults: [],
      caller: alwaysWaive,
    })
    expect(result.status).toBe('measured')
    expect(result.detected_count).toBe(1)
    expect(result.covered_count).toBe(1)
    expect(result.truncated_count).toBe(0)
    expect(result.waived_count).toBe(1)
    expect(result.sets).toHaveLength(1)
  })

  it('assembles a measured field with an EMPTY sets array (not fabricated) when nothing significant was detected', async () => {
    const result = await assembleInterpretationSets({
      turnId: 'turn-2',
      committedBlocks: [{ id: 'blk-1-1', role: 'prose', text: 'Neutral prose.', semantic: { kind: 'heading' } }],
      predictionCandidates: [],
      validToolResults: [],
      caller: alwaysWaive,
    })
    expect(result.status).toBe('measured')
    expect(result.detected_count).toBe(0)
    expect(result.covered_count).toBe(0)
    expect(result.sets).toEqual([])
  })

  it('truncates to MAX_SIGNIFICANT_JUDGMENTS_PER_TURN and discloses the truncated count (never silently drops)', async () => {
    const blocks: OpenBlock[] = Array.from({ length: MAX_SIGNIFICANT_JUDGMENTS_PER_TURN + 3 }, (_, i) =>
      verdictBlock(`blk-${i}-1`, `Verdict number ${i}.`),
    )
    const result = await assembleInterpretationSets({
      turnId: 'turn-3',
      committedBlocks: blocks,
      predictionCandidates: [],
      validToolResults: [],
      caller: alwaysWaive,
    })
    expect(result.detected_count).toBe(MAX_SIGNIFICANT_JUDGMENTS_PER_TURN + 3)
    expect(result.covered_count).toBe(MAX_SIGNIFICANT_JUDGMENTS_PER_TURN)
    expect(result.truncated_count).toBe(3)
    expect(result.sets).toHaveLength(MAX_SIGNIFICANT_JUDGMENTS_PER_TURN)
    // Arithmetic coherence — the same invariant receipt/validate.ts's V6 checks.
    expect((result.covered_count ?? 0) + (result.truncated_count ?? 0)).toBe(result.detected_count)
  })
})

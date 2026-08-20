/**
 * interpretation/detect.test.ts — lane G3-B (PPR-02).
 *
 * Proves each of the five SIGNIFICANT-judgment categories fires on the
 * REAL structural signal it claims to reuse, and does NOT fire when that
 * signal is absent (no G2-A classification, no matching tool consultation,
 * no keyword match) — never a keyword-only guess.
 */
import { describe, it, expect } from 'vitest'

import { detectSignificantJudgments } from '../detect'
import type { OpenBlock } from '@/lib/pariprashna/pipeline/reading_parts'
import type { ToolBundle } from '@/lib/retrieval/shared_types'

function toolBundle(toolName: string): ToolBundle {
  return {
    tool_bundle_id: 'tb-1',
    tool_name: toolName,
    tool_version: '1.0',
    invocation_params: {},
    results: [],
    served_from_cache: false,
    latency_ms: 10,
    result_hash: 'sha256:abc',
    schema_version: '1.0',
  }
}

function verdictBlock(id: string, text: string): OpenBlock {
  return { id, role: 'prose', text, semantic: { kind: 'paragraph', role: 'verdict' } }
}

function elaborationBlock(id: string, text: string): OpenBlock {
  return { id, role: 'prose', text, semantic: { kind: 'paragraph', role: 'elaboration' } }
}

function caveatBlock(id: string, text: string): OpenBlock {
  return { id, role: 'prose', text, semantic: { kind: 'paragraph', role: 'caveat' } }
}

describe('detectSignificantJudgments — domain_verdict', () => {
  it('fires on a G2-A verdict-role block', () => {
    const out = detectSignificantJudgments({
      committedBlocks: [verdictBlock('blk-1-1', 'Your career shows strong potential this decade.')],
      predictionCandidates: [],
      validToolResults: [],
    })
    expect(out).toHaveLength(1)
    expect(out[0]).toMatchObject({ category: 'domain_verdict', block_id: 'blk-1-1' })
  })

  it('does NOT fire on an elaboration-role block', () => {
    const out = detectSignificantJudgments({
      committedBlocks: [elaborationBlock('blk-1-2', 'This is further detail.')],
      predictionCandidates: [],
      validToolResults: [],
    })
    expect(out.filter((j) => j.category === 'domain_verdict')).toHaveLength(0)
  })

  it('does NOT fire when the block carries no G2-A semantic classification (flag was off)', () => {
    const out = detectSignificantJudgments({
      committedBlocks: [{ id: 'blk-1-1', role: 'prose', text: 'Your career shows strong potential.' }],
      predictionCandidates: [],
      validToolResults: [],
    })
    expect(out).toHaveLength(0)
  })
})

describe('detectSignificantJudgments — rules_in_tension', () => {
  it('fires on a caveat block ONLY when contradiction_register was consulted', () => {
    const withTool = detectSignificantJudgments({
      committedBlocks: [caveatBlock('blk-1-3', 'However, one classical source suggests otherwise.')],
      predictionCandidates: [],
      validToolResults: [toolBundle('contradiction_register')],
    })
    expect(withTool.filter((j) => j.category === 'rules_in_tension')).toHaveLength(1)

    const withoutTool = detectSignificantJudgments({
      committedBlocks: [caveatBlock('blk-1-3', 'However, one classical source suggests otherwise.')],
      predictionCandidates: [],
      validToolResults: [],
    })
    expect(withoutTool.filter((j) => j.category === 'rules_in_tension')).toHaveLength(0)
  })
})

describe('detectSignificantJudgments — remedial', () => {
  it('fires ONLY when BOTH the lexicon matches AND remedial_codex_query was consulted', () => {
    const both = detectSignificantJudgments({
      committedBlocks: [elaborationBlock('blk-1-4', 'The tradition prescribes a specific mantra for this placement.')],
      predictionCandidates: [],
      validToolResults: [toolBundle('remedial_codex_query')],
    })
    expect(both.filter((j) => j.category === 'remedial')).toHaveLength(1)

    const lexiconOnly = detectSignificantJudgments({
      committedBlocks: [elaborationBlock('blk-1-4', 'The tradition prescribes a specific mantra for this placement.')],
      predictionCandidates: [],
      validToolResults: [],
    })
    expect(lexiconOnly.filter((j) => j.category === 'remedial')).toHaveLength(0)

    const toolOnly = detectSignificantJudgments({
      committedBlocks: [elaborationBlock('blk-1-4', 'This placement tends to bring career recognition.')],
      predictionCandidates: [],
      validToolResults: [toolBundle('remedial_codex_query')],
    })
    expect(toolOnly.filter((j) => j.category === 'remedial')).toHaveLength(0)
  })
})

describe('detectSignificantJudgments — time_indexed', () => {
  it('fires on a paragraph mentioning a dasha/gochara/tajaka timing technique', () => {
    const out = detectSignificantJudgments({
      committedBlocks: [elaborationBlock('blk-1-5', 'During the Jupiter mahadasha, this theme intensifies.')],
      predictionCandidates: [],
      validToolResults: [],
    })
    expect(out.filter((j) => j.category === 'time_indexed')).toHaveLength(1)
  })

  it('does NOT fire on a paragraph with no timing-technique term', () => {
    const out = detectSignificantJudgments({
      committedBlocks: [elaborationBlock('blk-1-6', 'This is a general character trait.')],
      predictionCandidates: [],
      validToolResults: [],
    })
    expect(out.filter((j) => j.category === 'time_indexed')).toHaveLength(0)
  })
})

describe('detectSignificantJudgments — prediction_detected', () => {
  it('reuses SAMĪKṢĀ Stage-1 candidates verbatim, one judgment per candidate', () => {
    const out = detectSignificantJudgments({
      committedBlocks: [elaborationBlock('blk-1-7', 'You will likely see a promotion by 2027.')],
      predictionCandidates: [{ text: 'You will likely see a promotion by 2027.', offset: 0, score: 0.85, horizon: 'by 2027' }],
      validToolResults: [],
    })
    const preds = out.filter((j) => j.category === 'prediction_detected')
    expect(preds).toHaveLength(1)
    expect(preds[0].claim_text).toBe('You will likely see a promotion by 2027.')
    expect(preds[0].block_id).toBe('blk-1-7')
  })

  it('binds block_id null (honest) when the candidate text is not found in any committed block', () => {
    const out = detectSignificantJudgments({
      committedBlocks: [],
      predictionCandidates: [{ text: 'Orphaned candidate text.', offset: 0, score: 0.9, horizon: null }],
      validToolResults: [],
    })
    expect(out[0].block_id).toBeNull()
  })
})

describe('detectSignificantJudgments — no significant judgment produces no entries', () => {
  it('returns an empty array for a turn with nothing significant', () => {
    const out = detectSignificantJudgments({
      committedBlocks: [{ id: 'blk-1-1', role: 'prose', text: 'A neutral sentence.', semantic: { kind: 'heading' } }],
      predictionCandidates: [],
      validToolResults: [],
    })
    expect(out).toEqual([])
  })
})

describe('detectSignificantJudgments — judgment_id stability', () => {
  it('produces deterministic, category-scoped, stable ids across repeated runs', () => {
    const args = {
      committedBlocks: [verdictBlock('blk-1-1', 'A verdict.'), verdictBlock('blk-2-1', 'Another verdict.')],
      predictionCandidates: [],
      validToolResults: [],
    }
    const first = detectSignificantJudgments(args)
    const second = detectSignificantJudgments(args)
    expect(first.map((j) => j.judgment_id)).toEqual(['sig-domain_verdict-1', 'sig-domain_verdict-2'])
    expect(second.map((j) => j.judgment_id)).toEqual(first.map((j) => j.judgment_id))
  })
})

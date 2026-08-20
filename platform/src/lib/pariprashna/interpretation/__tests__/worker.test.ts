/**
 * interpretation/worker.test.ts — lane G3-B (PPR-02).
 *
 * `generateInterpretationSets` takes an injectable `InterpretationLlmCaller`
 * seam (same DI pattern `samiksha/detector.ts`'s `CandidateClassifier` and
 * `receipt` fixtures use) so these tests exercise the REAL coercion/waiver
 * logic without a network call. Proves: a genuine >=3-candidate model
 * response produces a correctly-shaped `generated` entry; a call that
 * cannot produce 3 distinct candidates and says so produces a `waived`
 * entry; a call whose entry fails structural validation (too few
 * candidates, out-of-range selection, a claimed-waiver with no reason)
 * degrades to an HONEST waiver rather than a fabricated set; a call that
 * fails outright waives every judgment with a real reason. Nothing here
 * ever fabricates a candidate client-side.
 */
import { describe, it, expect, vi } from 'vitest'

import { generateInterpretationSets, type InterpretationLlmCaller } from '../worker'
import type { SignificantJudgment } from '../detect'

function judgment(overrides: Partial<SignificantJudgment> = {}): SignificantJudgment {
  return {
    judgment_id: 'sig-domain_verdict-1',
    category: 'domain_verdict',
    block_id: 'blk-1-1',
    claim_text: 'Your career shows strong potential this decade.',
    detection_basis: "G2-A block role='verdict'",
    ...overrides,
  }
}

describe('generateInterpretationSets — generated path', () => {
  it('produces a correctly-shaped entry from a genuine >=3-candidate model response', async () => {
    const j = judgment()
    const caller: InterpretationLlmCaller = async () =>
      new Map([
        [
          j.judgment_id,
          {
            judgment_id: j.judgment_id,
            status: 'generated' as const,
            candidates: [
              { reading: 'Reading A: steady growth via disciplined effort.', rationale: 'Supported by X.' },
              { reading: 'Reading B: a single sharp promotion event.', rationale: 'Supported by Y.' },
              { reading: 'Reading C: a lateral pivot rather than growth.', rationale: 'Supported by Z.' },
            ],
            selected_index: 0,
            selected_rationale: 'A best fits the corroborating evidence.',
            falsifier: 'If no advancement occurs within the window, this reading is wrong.',
          },
        ],
      ])

    const [entry] = await generateInterpretationSets([j], caller)
    expect(entry.status).toBe('generated')
    expect(entry.candidates).toHaveLength(3)
    expect(entry.selected_index).toBe(0)
    expect(entry.selected_rationale).toBeTruthy()
    expect(entry.falsifier).toBeTruthy()
    expect(entry.waiver_reason).toBeNull()
  })
})

describe('generateInterpretationSets — waiver path', () => {
  it('honors an explicit model waiver with a real reason', async () => {
    const j = judgment({ category: 'remedial' })
    const caller: InterpretationLlmCaller = async () =>
      new Map([
        [
          j.judgment_id,
          {
            judgment_id: j.judgment_id,
            status: 'waived' as const,
            waiver_reason: 'The remedy is prescribed by a single, unambiguous classical rule with no competing reading.',
          },
        ],
      ])

    const [entry] = await generateInterpretationSets([j], caller)
    expect(entry.status).toBe('waived')
    expect(entry.candidates).toBeNull()
    expect(entry.waiver_reason).toContain('unambiguous')
  })

  it('degrades a structurally-invalid "generated" answer to an honest waiver (too few candidates)', async () => {
    const j = judgment()
    const caller: InterpretationLlmCaller = async () =>
      new Map([
        [
          j.judgment_id,
          {
            judgment_id: j.judgment_id,
            status: 'generated' as const,
            candidates: [
              { reading: 'Only one.', rationale: 'r' },
              { reading: 'Only two.', rationale: 'r' },
            ],
            selected_index: 0,
            selected_rationale: 'r',
            falsifier: 'f',
          },
        ],
      ])

    const [entry] = await generateInterpretationSets([j], caller)
    expect(entry.status).toBe('waived')
    expect(entry.candidates).toBeNull()
    expect(entry.waiver_reason).toMatch(/structural validation/)
  })

  it('degrades a claimed waiver with no reason to an honest waiver (never trusts an empty reason)', async () => {
    const j = judgment()
    const caller: InterpretationLlmCaller = async () =>
      new Map([[j.judgment_id, { judgment_id: j.judgment_id, status: 'waived' as const }]])

    const [entry] = await generateInterpretationSets([j], caller)
    expect(entry.status).toBe('waived')
    expect(entry.waiver_reason).toBeTruthy()
  })

  it('waives a judgment the model omitted from its response entirely', async () => {
    const j = judgment()
    const caller: InterpretationLlmCaller = async () => new Map()

    const [entry] = await generateInterpretationSets([j], caller)
    expect(entry.status).toBe('waived')
    expect(entry.waiver_reason).toMatch(/no entry/)
  })

  it('waives every judgment when the call itself fails (no fabricated candidates on error)', async () => {
    const judgments = [judgment({ judgment_id: 'sig-domain_verdict-1' }), judgment({ judgment_id: 'sig-remedial-1', category: 'remedial' })]
    const caller: InterpretationLlmCaller = vi.fn(async () => {
      throw new Error('provider unavailable')
    })

    const entries = await generateInterpretationSets(judgments, caller)
    expect(entries).toHaveLength(2)
    for (const entry of entries) {
      expect(entry.status).toBe('waived')
      expect(entry.candidates).toBeNull()
      expect(entry.waiver_reason).toMatch(/call failed/)
    }
  })
})

describe('generateInterpretationSets — no significant judgments', () => {
  it('returns an empty array without calling the LLM caller', async () => {
    const caller: InterpretationLlmCaller = vi.fn(async () => new Map())
    const entries = await generateInterpretationSets([], caller)
    expect(entries).toEqual([])
    expect(caller).not.toHaveBeenCalled()
  })
})

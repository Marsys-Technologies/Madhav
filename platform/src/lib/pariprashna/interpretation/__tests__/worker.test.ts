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

import {
  generateInterpretationSets,
  resolveInterpretationSetsModelId,
  parseAndValidateSets,
  INTERPRETATION_SETS_MODEL_ID,
  type InterpretationLlmCaller,
} from '../worker'
import { getModelMeta } from '@/lib/models/registry'
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
    // G3BC hardening "Also fix" — detect.ts's own detection_basis threads
    // through to the persisted entry, unchanged.
    expect(entry.detection_basis).toBe(j.detection_basis)
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

describe('generateInterpretationSets — G3BC hardening defect 5', () => {
  const distinctCandidates = [
    { reading: 'Reading A: steady growth via disciplined effort.', rationale: 'Supported by X.' },
    { reading: 'Reading B: a single sharp promotion event.', rationale: 'Supported by Y.' },
    { reading: 'Reading C: a lateral pivot rather than growth.', rationale: 'Supported by Z.' },
  ]

  it("degrades to a waiver on the adversary's exact vacuous falsifier (\"If I'm wrong, I'm wrong.\")", async () => {
    const j = judgment()
    const caller: InterpretationLlmCaller = async () =>
      new Map([
        [
          j.judgment_id,
          {
            judgment_id: j.judgment_id,
            status: 'generated' as const,
            candidates: distinctCandidates,
            selected_index: 0,
            selected_rationale: 'A best fits the corroborating evidence.',
            falsifier: "If I'm wrong, I'm wrong.",
          },
        ],
      ])

    const [entry] = await generateInterpretationSets([j], caller)
    expect(entry.status).toBe('waived')
    expect(entry.candidates).toBeNull()
    expect(entry.falsifier).toBeNull()
  })

  it("degrades to a waiver on the adversary's second vacuous falsifier (\"maybe\")", async () => {
    const j = judgment()
    const caller: InterpretationLlmCaller = async () =>
      new Map([
        [
          j.judgment_id,
          {
            judgment_id: j.judgment_id,
            status: 'generated' as const,
            candidates: distinctCandidates,
            selected_index: 0,
            selected_rationale: 'A best fits the corroborating evidence.',
            falsifier: 'maybe',
          },
        ],
      ])

    const [entry] = await generateInterpretationSets([j], caller)
    expect(entry.status).toBe('waived')
  })

  it('a genuine, specific, sufficiently-detailed falsifier still passes (the floor-raise does not reject real content)', async () => {
    const j = judgment()
    const caller: InterpretationLlmCaller = async () =>
      new Map([
        [
          j.judgment_id,
          {
            judgment_id: j.judgment_id,
            status: 'generated' as const,
            candidates: distinctCandidates,
            selected_index: 0,
            selected_rationale: 'A best fits the corroborating evidence.',
            falsifier: 'If no career advancement occurs within the next 18 months, this reading is wrong.',
          },
        ],
      ])

    const [entry] = await generateInterpretationSets([j], caller)
    expect(entry.status).toBe('generated')
    expect(entry.falsifier).toBe('If no career advancement occurs within the next 18 months, this reading is wrong.')
  })

  it("degrades to a waiver on the adversary's exact reworded-candidate construction (3 candidates, same conclusion reworded)", async () => {
    const j = judgment()
    const caller: InterpretationLlmCaller = async () =>
      new Map([
        [
          j.judgment_id,
          {
            judgment_id: j.judgment_id,
            status: 'generated' as const,
            candidates: [
              { reading: 'Your career will show strong steady growth this year.', rationale: 'Supported by X.' },
              { reading: 'This year your career will show strong, steady growth.', rationale: 'Supported by X, restated.' },
              { reading: 'Strong, steady career growth will occur this year.', rationale: 'Supported by X, again.' },
            ],
            selected_index: 0,
            selected_rationale: 'A best fits the corroborating evidence.',
            falsifier: 'If no career advancement occurs within the next 18 months, this reading is wrong.',
          },
        ],
      ])

    const [entry] = await generateInterpretationSets([j], caller)
    expect(entry.status).toBe('waived')
    expect(entry.candidates).toBeNull()
  })

  it('genuinely distinct candidates (different conclusions, not reworded) still pass', async () => {
    const j = judgment()
    const caller: InterpretationLlmCaller = async () =>
      new Map([
        [
          j.judgment_id,
          {
            judgment_id: j.judgment_id,
            status: 'generated' as const,
            candidates: distinctCandidates,
            selected_index: 0,
            selected_rationale: 'A best fits the corroborating evidence.',
            falsifier: 'If no career advancement occurs within the next 18 months, this reading is wrong.',
          },
        ],
      ])

    const [entry] = await generateInterpretationSets([j], caller)
    expect(entry.status).toBe('generated')
    expect(entry.candidates).toHaveLength(3)
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

describe('resolveInterpretationSetsModelId — DD-17', () => {
  it('resolves to the mid-tier gemini model, not the worker tier', () => {
    expect(resolveInterpretationSetsModelId()).toBe('gemini-2.5-flash')
    expect(INTERPRETATION_SETS_MODEL_ID).toBe('gemini-2.5-flash')
  })

  it('the resolved model exists in the registry as tier=mid', () => {
    const meta = getModelMeta(resolveInterpretationSetsModelId())
    expect(meta).toBeDefined()
    expect(meta?.tier).toBe('mid')
  })

  it('is NOT the worker-tier model (regression guard for the DD-17 downgrade)', () => {
    expect(resolveInterpretationSetsModelId()).not.toBe('gemini-2.5-flash-lite')
  })
})

describe('parseAndValidateSets — DD-20 (real bug, real repro texts, no network)', () => {
  it('accepts a correctly-shaped response', () => {
    const raw = JSON.stringify({
      sets: [
        {
          judgment_id: 'sig-domain_verdict-1',
          status: 'generated',
          candidates: [
            { reading: 'A', rationale: 'ra' },
            { reading: 'B', rationale: 'rb' },
            { reading: 'C', rationale: 'rc' },
          ],
          selected_index: 0,
          selected_rationale: 'best',
          falsifier: 'a real falsifier with enough words to pass',
        },
      ],
    })
    const map = parseAndValidateSets(raw)
    expect(map.get('sig-domain_verdict-1')?.status).toBe('generated')
  })

  it('THROWS (not silently empty) on the exact wrong-envelope shape observed live against the real deployed model — {"judgments":[...]} with candidate_readings/strongest_reading, no "sets" key at all', () => {
    // Byte-shape-equivalent to a real captured response (DD-20 register entry) —
    // the actual defect this fix closes: valid JSON, wrong top-level key and
    // wrong field names throughout, which `parsed.sets ?? []` used to silently
    // swallow as "no entry" rather than surfacing as a real failure.
    const raw = JSON.stringify({
      judgments: [
        {
          judgment_id: 'sig-domain_verdict-1',
          candidate_readings: [
            { reading_id: 'c1', reading: 'A' },
            { reading_id: 'c2', reading: 'B' },
            { reading_id: 'c3', reading: 'C' },
          ],
          strongest_reading: { reading_id: 'c1', rationale: 'best', falsifier: 'because' },
        },
      ],
    })
    expect(() => parseAndValidateSets(raw)).toThrow(/schema-invalid/)
  })

  it('THROWS on a bare top-level array (the other wrong shape observed live)', () => {
    const raw = JSON.stringify([
      { judgment_id: 'sig-domain_verdict-1', candidate_readings: [], selected_reading: {} },
    ])
    expect(() => parseAndValidateSets(raw)).toThrow(/schema-invalid/)
  })

  it('THROWS on unparseable text (pre-existing behavior, unchanged)', () => {
    expect(() => parseAndValidateSets('not json at all')).toThrow(/non-JSON/)
  })

  it('THROWS on empty text (pre-existing behavior, unchanged)', () => {
    expect(() => parseAndValidateSets('   ')).toThrow(/no text output/)
  })

  it('THROWS when "sets" exists but its entries are wrong-shaped (missing required judgment_id)', () => {
    const raw = JSON.stringify({ sets: [{ status: 'waived' }] })
    expect(() => parseAndValidateSets(raw)).toThrow(/schema-invalid/)
  })
})

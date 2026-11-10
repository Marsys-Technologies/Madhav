import { describe, it, expect, beforeEach } from 'vitest'

import { classifyDivergence } from '../../panel/divergence_detector'
import type { PanelMemberOutput, AdjudicationResult } from '../../panel/types'

// ── Fixtures ──────────────────────────────────────────────────────────────────

const threeMemberOutputs: PanelMemberOutput[] = [
  { member_index: 0, model_id: 'claude-sonnet-4-6', provider_family: 'anthropic', status: 'success', answer: 'Answer A', latency_ms: 1000 },
  { member_index: 1, model_id: 'gpt-4.1',            provider_family: 'openai',    status: 'success', answer: 'Answer B', latency_ms: 900  },
  { member_index: 2, model_id: 'gemini-2.5-pro',     provider_family: 'google',    status: 'success', answer: 'Answer C', latency_ms: 1100 },
]

function makeAdjudication(
  has_divergence: boolean,
  summary_text: string,
  alignment: Record<string, 'aligned' | 'partial' | 'dissent'> = {},
  divergence_count = has_divergence ? 1 : 0,
): AdjudicationResult {
  return {
    final_answer: 'Synthesized answer.',
    divergence_summary: { has_divergence, divergence_count, summary_text },
    member_alignment: alignment,
    adjudicator_model_id: 'deepseek-chat',
    latency_ms: 500,
  }
}

beforeEach(() => {
  // Pure functions — no mocks needed
})

// ── No divergence ─────────────────────────────────────────────────────────────

describe('classifyDivergence — no divergence', () => {
  it('leaves divergence unknown when the adjudicator response could not be evaluated', () => {
    const adjudication = makeAdjudication(false, 'Malformed adjudicator response')
    adjudication.divergence_summary.has_divergence = null
    adjudication.divergence_summary.divergence_count = null

    expect(classifyDivergence(threeMemberOutputs, adjudication)).toEqual({
      has_divergence: null,
      instances: [],
      member_alignment_summary: {},
    })
  })

  it('returns has_divergence=false and empty instances when adjudication reports no divergence', () => {
    const adjudication = makeAdjudication(false, 'All members aligned on the 7th house reading.')
    const result = classifyDivergence(threeMemberOutputs, adjudication)

    expect(result.has_divergence).toBe(false)
    expect(result.instances).toHaveLength(0)
  })

  it('passes member_alignment_summary through unchanged', () => {
    const alignment = { member_1: 'aligned' as const, member_2: 'aligned' as const }
    const adjudication = makeAdjudication(false, 'All aligned.', alignment)
    const result = classifyDivergence(threeMemberOutputs, adjudication)

    expect(result.member_alignment_summary).toEqual(alignment)
  })

  it('returns no instances even when summary text contains keywords if divergence_count=0', () => {
    // divergence_count=0 short-circuits classification regardless of keywords
    const adjudication = makeAdjudication(true, 'Members disagree on house and dasha.', {}, 0)
    const result = classifyDivergence(threeMemberOutputs, adjudication)

    expect(result.has_divergence).toBe(false)
    expect(result.instances).toHaveLength(0)
  })
})

// ── DIS.class.factual ─────────────────────────────────────────────────────────

describe('classifyDivergence — DIS.class.factual', () => {
  it('fires when summary_text contains "house"', () => {
    const adjudication = makeAdjudication(true, 'Members disagree about the 7th house lord.')
    const result = classifyDivergence(threeMemberOutputs, adjudication)

    const factual = result.instances.find(i => i.class === 'DIS.class.factual')
    expect(factual).toBeDefined()
  })

  it('fires when summary_text contains "dasha"', () => {
    const adjudication = makeAdjudication(true, 'Dasha period calculations differ between members.')
    const result = classifyDivergence(threeMemberOutputs, adjudication)

    const factual = result.instances.find(i => i.class === 'DIS.class.factual')
    expect(factual).toBeDefined()
  })

  it('fires when summary_text contains "degree"', () => {
    const adjudication = makeAdjudication(true, 'The degree of the ascendant differs.')
    const result = classifyDivergence(threeMemberOutputs, adjudication)

    const factual = result.instances.find(i => i.class === 'DIS.class.factual')
    expect(factual).toBeDefined()
  })
})

// ── DIS.class.interpretive ────────────────────────────────────────────────────

describe('classifyDivergence — DIS.class.interpretive', () => {
  it('fires when summary_text contains "interpret"', () => {
    const adjudication = makeAdjudication(true, 'Members interpret the Saturn transit differently.')
    const result = classifyDivergence(threeMemberOutputs, adjudication)

    const interpretive = result.instances.find(i => i.class === 'DIS.class.interpretive')
    expect(interpretive).toBeDefined()
  })

  it('fires when summary_text contains "mean"', () => {
    const adjudication = makeAdjudication(true, 'What this aspect means is disputed.')
    const result = classifyDivergence(threeMemberOutputs, adjudication)

    const interpretive = result.instances.find(i => i.class === 'DIS.class.interpretive')
    expect(interpretive).toBeDefined()
  })
})

// ── DIS.class.scope ───────────────────────────────────────────────────────────

describe('classifyDivergence — DIS.class.scope', () => {
  it('fires when summary_text contains "framing"', () => {
    const adjudication = makeAdjudication(true, 'The framing of the query led to different emphases.')
    const result = classifyDivergence(threeMemberOutputs, adjudication)

    const scope = result.instances.find(i => i.class === 'DIS.class.scope')
    expect(scope).toBeDefined()
  })

  it('fires when summary_text contains "scope"', () => {
    const adjudication = makeAdjudication(true, 'The scope of analysis differed significantly.')
    const result = classifyDivergence(threeMemberOutputs, adjudication)

    const scope = result.instances.find(i => i.class === 'DIS.class.scope')
    expect(scope).toBeDefined()
  })
})

// ── DIS.class.confidence ──────────────────────────────────────────────────────

describe('classifyDivergence — DIS.class.confidence', () => {
  it('fires when summary_text contains "confident"', () => {
    const adjudication = makeAdjudication(true, 'Member 1 was highly confident; others were uncertain.')
    const result = classifyDivergence(threeMemberOutputs, adjudication)

    const confidence = result.instances.find(i => i.class === 'DIS.class.confidence')
    expect(confidence).toBeDefined()
  })

  it('fires when summary_text contains "likely"', () => {
    const adjudication = makeAdjudication(true, 'Members disagreed on how likely the outcome is.')
    const result = classifyDivergence(threeMemberOutputs, adjudication)

    const confidence = result.instances.find(i => i.class === 'DIS.class.confidence')
    expect(confidence).toBeDefined()
  })
})

// ── DIS.class.extension ───────────────────────────────────────────────────────

describe('classifyDivergence — DIS.class.extension', () => {
  it('fires when summary_text contains "remedy"', () => {
    const adjudication = makeAdjudication(true, 'Members diverged on remedy recommendations for Saturn.')
    const result = classifyDivergence(threeMemberOutputs, adjudication)

    const extension = result.instances.find(i => i.class === 'DIS.class.extension')
    expect(extension).toBeDefined()
  })

  it('fires when summary_text contains "recommendation"', () => {
    const adjudication = makeAdjudication(true, 'Recommendation for timing of action differed.')
    const result = classifyDivergence(threeMemberOutputs, adjudication)

    const extension = result.instances.find(i => i.class === 'DIS.class.extension')
    expect(extension).toBeDefined()
  })
})

// ── Mixed: two classes simultaneously ────────────────────────────────────────

describe('classifyDivergence — mixed classes', () => {
  it('fires both DIS.class.factual and DIS.class.interpretive when both keywords match', () => {
    const adjudication = makeAdjudication(
      true,
      'Members disagree on the house lord (factual) and what that means (interpretive).',
    )
    const result = classifyDivergence(threeMemberOutputs, adjudication)

    const classes = result.instances.map(i => i.class)
    expect(classes).toContain('DIS.class.factual')
    expect(classes).toContain('DIS.class.interpretive')
  })

  it('fires both DIS.class.scope and DIS.class.confidence simultaneously', () => {
    const adjudication = makeAdjudication(
      true,
      'The scope of the question framing led to different confidence levels about the likely outcome.',
    )
    const result = classifyDivergence(threeMemberOutputs, adjudication)

    const classes = result.instances.map(i => i.class)
    expect(classes).toContain('DIS.class.scope')
    expect(classes).toContain('DIS.class.confidence')
  })
})

// ── Fallback to interpretive ──────────────────────────────────────────────────

describe('classifyDivergence — fallback to interpretive', () => {
  it('falls back to DIS.class.interpretive when has_divergence=true but no keywords match', () => {
    const adjudication = makeAdjudication(
      true,
      'The outputs were different in various unspecified ways.',
    )
    const result = classifyDivergence(threeMemberOutputs, adjudication)

    expect(result.has_divergence).toBe(true)
    expect(result.instances).toHaveLength(1)
    expect(result.instances[0].class).toBe('DIS.class.interpretive')
    expect(result.instances[0].description).toMatch(/Generic disagreement/)
  })

  it('fallback instance has empty member_indices when no alignment data maps to dissent/partial', () => {
    const adjudication = makeAdjudication(
      true,
      'Completely opaque divergence with no pattern.',
      { member_1: 'aligned', member_2: 'aligned', member_3: 'aligned' },
    )
    const result = classifyDivergence(threeMemberOutputs, adjudication)

    expect(result.instances[0].member_indices).toHaveLength(0)
  })
})

// ── Dissenting member_indices ─────────────────────────────────────────────────

describe('classifyDivergence — dissenting member index extraction', () => {
  it('includes indices of partial and dissent members in instance.member_indices', () => {
    const adjudication = makeAdjudication(
      true,
      'Members disagreed on the house lord assignment.',
      {
        member_1: 'aligned',
        member_2: 'partial',
        member_3: 'dissent',
      },
    )
    const result = classifyDivergence(threeMemberOutputs, adjudication)

    const factual = result.instances.find(i => i.class === 'DIS.class.factual')!
    // member_2 → member_index 1 (0-indexed), member_3 → member_index 2
    expect(factual.member_indices).toContain(1)
    expect(factual.member_indices).toContain(2)
    expect(factual.member_indices).not.toContain(0)
  })
})

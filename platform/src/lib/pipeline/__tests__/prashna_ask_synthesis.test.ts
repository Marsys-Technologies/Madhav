/**
 * prashna_ask_synthesis.test.ts — W6.2 fix-cycle.
 *
 * Covers `synthesizeReading`: the single, non-agentic LLM call that turns
 * prashna_ask's already-gathered floor evidence into an acharya-grade reading.
 * Never throws on failure (DB lookup, model resolution, the model call
 * itself, or an empty response) — every failure mode resolves to
 * `{reading: null, judgment_flags: [...]}` so the caller can still return the
 * honest evidence bundle.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => mockQuery(...args) }))

const mockRunAdapter = vi.fn()
vi.mock('@/lib/adapters/run_adapter', () => ({ runAdapter: (...args: unknown[]) => mockRunAdapter(...args) }))

const mockGetEffectiveModel = vi.fn()
vi.mock('@/lib/models/runtime_config', () => ({ getEffectiveModel: (...args: unknown[]) => mockGetEffectiveModel(...args) }))
vi.mock('@/lib/models/registry', () => ({ DEFAULT_STACK_ID: 'anthropic' }))

import {
  synthesizeReading,
  formatEvidenceBlock,
  selectRowsWithinBudget,
  type SynthesizeReadingInput,
  type SynthesisEvidenceItem,
} from '../prashna_ask_synthesis'

const CHART_ROW = {
  id: '482012f1-710e-4a25-994a-93821f5871aa',
  name: 'Test Native',
  birth_date: '1984-02-05',
  birth_time: '10:43',
  birth_place: 'Bhubaneswar, Odisha, India',
}

function baseInput(overrides: Partial<SynthesizeReadingInput> = {}): SynthesizeReadingInput {
  return {
    chartId: CHART_ROW.id,
    question: 'What does my current dasha period suggest about career timing?',
    queryClass: 'predictive',
    queryIntentSummary: 'Career timing via current dasha',
    evidence: [
      { tool_name: 'query_dasha_periods', bundle: { results: [{ lord_graha: 'Mercury' }] } },
    ],
    unresolvedTools: [],
    emptyResultTools: [],
    strippedLeakedCapabilities: [],
    capTripped: null,
    nowContextDate: '2026-07-22',
    currentMahaAntar: 'Mercury MD / Saturn AD',
    ...overrides,
  }
}

beforeEach(() => {
  mockQuery.mockReset()
  mockRunAdapter.mockReset()
  mockGetEffectiveModel.mockReset()
  mockQuery.mockResolvedValue({ rows: [CHART_ROW] })
  mockGetEffectiveModel.mockResolvedValue('claude-sonnet-test')
  mockRunAdapter.mockResolvedValue({
    modelId: 'claude-sonnet-test',
    provider: 'anthropic',
    intermediate: [],
    finalText: 'Your Mercury-Jupiter period favors steady career growth.',
    finishReason: 'stop',
    usage: { inputTokens: 100, outputTokens: 50, costUsd: 0, latencyMs: 5 },
    providerMeta: {},
  })
})

describe('synthesizeReading — happy path', () => {
  it('returns a reading built from a single non-agentic runAdapter call', async () => {
    const result = await synthesizeReading(baseInput())
    expect(result.reading).toBe('Your Mercury-Jupiter period favors steady career growth.')
    expect(result.model_id).toBe('claude-sonnet-test')
    expect(result.judgment_flags).toEqual([])
    expect(mockRunAdapter).toHaveBeenCalledTimes(1)
  })

  it('does NOT pass a tools array — this is a non-agentic, single-shot call', async () => {
    await synthesizeReading(baseInput())
    const req = mockRunAdapter.mock.calls[0][0] as { tools?: unknown }
    expect(req.tools).toBeUndefined()
  })

  it('the system prompt overrides the base "call tools" instruction for this tool-less call', async () => {
    await synthesizeReading(baseInput())
    const req = mockRunAdapter.mock.calls[0][0] as { systemPrompt: string }
    expect(req.systemPrompt).toMatch(/do not attempt to call/i)
    expect(req.systemPrompt).toMatch(/acharya/i)
  })

  it('includes the gathered evidence in the user message', async () => {
    await synthesizeReading(baseInput())
    const req = mockRunAdapter.mock.calls[0][0] as { messages: Array<{ content: string }> }
    expect(req.messages[0].content).toContain('query_dasha_periods')
    expect(req.messages[0].content).toContain('Mercury')
  })

  it('discloses evidence gaps (unresolved/empty/leaked/cap) in the prompt so the model does not fabricate over them', async () => {
    await synthesizeReading(
      baseInput({
        unresolvedTools: ['pattern_register'],
        emptyResultTools: ['chart_facts_query'],
        strippedLeakedCapabilities: ['marsys://tool/L5/lel_query'],
        capTripped: 'call_count_cap',
      }),
    )
    const req = mockRunAdapter.mock.calls[0][0] as { messages: Array<{ content: string }> }
    const content = req.messages[0].content
    expect(content).toContain('pattern_register')
    expect(content).toContain('unresolved tool name')
    expect(content).toContain('chart_facts_query')
    expect(content).toContain('zero rows')
    expect(content).toContain('marsys://tool/L5/lel_query')
    expect(content).toContain('NO-LEAKAGE')
    expect(content).toContain('call_count_cap')
  })
})

describe('synthesizeReading — temporal anchor (W6.3 fix-cycle, live trace d08d823a)', () => {
  it('tells the model today\'s date and the current maha/antar dasha explicitly', async () => {
    await synthesizeReading(baseInput({ nowContextDate: '2026-07-22', currentMahaAntar: 'Mercury MD / Saturn AD' }))
    const req = mockRunAdapter.mock.calls[0][0] as { messages: Array<{ content: string }> }
    const content = req.messages[0].content
    expect(content).toContain('2026-07-22')
    expect(content).toContain('Mercury MD / Saturn AD')
    expect(content).toMatch(/CURRENT period, not upcoming or past/i)
  })

  it('degrades honestly instead of fabricating a period when current_maha_antar is unresolved', async () => {
    await synthesizeReading(baseInput({ currentMahaAntar: null }))
    const req = mockRunAdapter.mock.calls[0][0] as { messages: Array<{ content: string }> }
    const content = req.messages[0].content
    expect(content).toContain('could not be resolved')
    expect(content).not.toContain('Mercury MD / Saturn AD')
  })
})

describe('synthesizeReading — never throws, degrades honestly', () => {
  it('resolves reading:null with a flag when the chart context lookup fails', async () => {
    mockQuery.mockRejectedValue(new Error('DB unreachable'))
    const result = await synthesizeReading(baseInput())
    expect(result.reading).toBeNull()
    expect(result.judgment_flags).toContain('synthesis_skipped_chart_context_unresolved')
    expect(mockRunAdapter).not.toHaveBeenCalled()
  })

  it('resolves reading:null with a flag when the chart row does not exist', async () => {
    mockQuery.mockResolvedValue({ rows: [] })
    const result = await synthesizeReading(baseInput())
    expect(result.reading).toBeNull()
    expect(result.judgment_flags).toContain('synthesis_skipped_chart_context_unresolved')
  })

  it('resolves reading:null with a flag when model resolution fails', async () => {
    mockGetEffectiveModel.mockRejectedValue(new Error('no model configured'))
    const result = await synthesizeReading(baseInput())
    expect(result.reading).toBeNull()
    expect(result.judgment_flags).toContain('synthesis_skipped_model_unresolved')
  })

  it('resolves reading:null with a flag when the model call itself throws', async () => {
    mockRunAdapter.mockRejectedValue(new Error('upstream 500'))
    const result = await synthesizeReading(baseInput())
    expect(result.reading).toBeNull()
    expect(result.judgment_flags).toContain('synthesis_call_failed')
  })

  it('resolves reading:null with a flag when the model returns empty/whitespace text', async () => {
    mockRunAdapter.mockResolvedValue({
      modelId: 'claude-sonnet-test',
      provider: 'anthropic',
      intermediate: [],
      finalText: '   ',
      finishReason: 'stop',
      usage: { inputTokens: 10, outputTokens: 0, costUsd: 0, latencyMs: 1 },
      providerMeta: {},
    })
    const result = await synthesizeReading(baseInput())
    expect(result.reading).toBeNull()
    expect(result.judgment_flags).toContain('synthesis_returned_empty')
  })

  it('handles an empty evidence array without crashing', async () => {
    const result = await synthesizeReading(baseInput({ evidence: [] }))
    expect(result.reading).not.toBeNull()
    const req = mockRunAdapter.mock.calls[0][0] as { messages: Array<{ content: string }> }
    expect(req.messages[0].content).toContain('no evidence was gathered')
  })

  it('truncates a genuinely oversized single-row evidence item and discloses it via judgment_flags (RC-08)', async () => {
    // RC-08: the per-item budget is now proportional to evidence.length (a single
    // evidence item gets the FULL TOTAL_EVIDENCE_BUDGET_CHARS pool, ~320,000 chars —
    // several times the old flat 8,000-char cap), so this reproduces the still-real
    // pathological case (a single monolithic row bigger than even that full pool —
    // e.g. an unfiltered chart_facts_query-class dump) rather than an ordinary-sized
    // deepdive result, which the old flat cap wrongly caught too.
    const hugeResult = { note: 'x'.repeat(400_000) }
    const result = await synthesizeReading(
      baseInput({ evidence: [{ tool_name: 'chart_facts_query', bundle: { results: [hugeResult] } }] }),
    )
    expect(result.judgment_flags).toContain('synthesis_evidence_truncated')

    const req = mockRunAdapter.mock.calls[0][0] as { messages: Array<{ content: string }> }
    const content = req.messages[0].content
    expect(content).toContain('truncated="true"')
    expect(content).toContain('TRUNCATED')
    // The prompt must not balloon to the full 400KB+ payload, but is allowed the
    // full single-item budget (~320,000 chars) plus small prompt overhead.
    expect(content.length).toBeLessThan(325_000)
  })

  it('does not flag truncation when every evidence item is under the size cap', async () => {
    const result = await synthesizeReading(baseInput())
    expect(result.judgment_flags).not.toContain('synthesis_evidence_truncated')
  })

  it('does not truncate a standard-sized deepdive floor (RC-08: right-sized cap)', async () => {
    // A realistic deepdive floor: ~8 tools, each returning a modest handful of rows —
    // the exact shape that was wrongly tripping synthesis_evidence_truncated under the
    // old flat 8,000-char/item cap (RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md RC-08).
    const standardFloor: SynthesisEvidenceItem[] = Array.from({ length: 8 }, (_, i) => ({
      tool_name: `floor_tool_${i}`,
      bundle: {
        results: Array.from({ length: 15 }, (_, j) => ({
          content: `finding ${j} for tool ${i}: `.padEnd(400, 'x'),
          significance: 0.5,
          confidence: 0.8,
        })),
      },
    }))
    const result = await synthesizeReading(baseInput({ evidence: standardFloor }))
    expect(result.judgment_flags).not.toContain('synthesis_evidence_truncated')
  })
})

describe('formatEvidenceBlock — bearing-aware row selection (RC-08)', () => {
  it('never drops the dissent (low-confidence, high-significance) row when trimming', () => {
    // Many uncontested, low-significance filler rows (enough to exceed the budget on
    // their own) plus ONE low-confidence/high-significance dissent row placed in the
    // MIDDLE of the array — a naive char-slice-from-the-start (the pre-RC-08
    // behavior) would very plausibly keep filler and cut this row purely by position.
    const filler = Array.from({ length: 400 }, (_, i) => ({
      id: `filler_${i}`,
      content: `FILLER_${i}_`.padEnd(900, 'f'),
      significance: 0.1,
      confidence: 0.9,
    }))
    const dissentRow = {
      id: 'dissent',
      content: 'DISSENT_MARKER_' + 'y'.repeat(900),
      significance: 0.6,
      confidence: 0.1, // below DISSENT_CONFIDENCE_THRESHOLD — protected by the dissent quota
    }
    const results = [...filler.slice(0, 200), dissentRow, ...filler.slice(200)]

    const evidence: SynthesisEvidenceItem[] = [{ tool_name: 'wide_scan_tool', bundle: { results } }]
    const { block, truncatedTools } = formatEvidenceBlock(evidence)

    expect(truncatedTools).toContain('wide_scan_tool')
    expect(block).toContain('DISSENT_MARKER_')
    // Sanity: this is a genuine trim, not a no-op — not every filler row survives.
    expect(block).not.toContain('FILLER_399_')
  })

  it('never drops a high-significance "tail" row placed last in the array', () => {
    // The tail row is LAST in raw array order (where a blind character slice of the
    // serialized JSON — the pre-RC-08 mechanism — would cut it first) but carries the
    // highest significance of any row in the set, so bearing-ranked selection must
    // keep it ahead of low-significance filler regardless of its position.
    const filler = Array.from({ length: 400 }, (_, i) => ({
      id: `filler_${i}`,
      content: `FILLER_${i}_`.padEnd(900, 'f'),
      significance: 0.1,
      confidence: 0.9,
    }))
    const tailRow = {
      id: 'tail',
      content: 'TAIL_HIGH_SIGNIFICANCE_MARKER_' + 'z'.repeat(900),
      significance: 0.95,
      confidence: 0.9,
    }
    const results = [...filler, tailRow] // tail row is the LAST element

    const evidence: SynthesisEvidenceItem[] = [{ tool_name: 'wide_scan_tool', bundle: { results } }]
    const { block, truncatedTools } = formatEvidenceBlock(evidence)

    expect(truncatedTools).toContain('wide_scan_tool')
    expect(block).toContain('TAIL_HIGH_SIGNIFICANCE_MARKER_')
    expect(block).not.toContain('FILLER_399_')
  })

  it('discloses kept/total row counts and dissent-drop honesty in the trim note', () => {
    const filler = Array.from({ length: 400 }, (_, i) => ({
      id: `filler_${i}`,
      content: `FILLER_${i}_`.padEnd(900, 'f'),
      significance: 0.1,
      confidence: 0.9,
    }))
    const evidence: SynthesisEvidenceItem[] = [{ tool_name: 'wide_scan_tool', bundle: { results: filler } }]
    const { block } = formatEvidenceBlock(evidence)
    expect(block).toMatch(/kept \d+ of 400 rows/)
    expect(block).toContain('bearing-on-the-question')
  })
})

describe('selectRowsWithinBudget — unit-level bearing ranking (RC-08)', () => {
  it('ranks a low-confidence row above higher-significance-but-confident filler via the dissent bonus', () => {
    const rows = [
      { id: 'confident_high_sig', significance: 0.8, confidence: 0.95 },
      { id: 'dissent_low_conf', significance: 0.2, confidence: 0.1 },
    ]
    // Budget only large enough for exactly one row's JSON.
    const oneRowBudget = JSON.stringify(rows[1], null, 2).length + 40
    const { keptResults, droppedDissentCount } = selectRowsWithinBudget(rows, oneRowBudget)
    expect(keptResults).toHaveLength(1)
    expect((keptResults[0] as { id: string }).id).toBe('dissent_low_conf')
    expect(droppedDissentCount).toBe(0)
  })

  it('keeps the single highest-bearing row even when it alone exceeds the budget (degenerate fallback)', () => {
    const rows = [{ id: 'only_row', significance: 1, confidence: 1, content: 'x'.repeat(1000) }]
    const { keptResults, keptCount, totalCount } = selectRowsWithinBudget(rows, 10)
    expect(keptCount).toBe(1)
    expect(totalCount).toBe(1)
    expect(keptResults).toHaveLength(1)
  })

  it('honestly reports droppedDissentCount when even dissent rows cannot all fit', () => {
    const dissentRows = Array.from({ length: 5 }, (_, i) => ({
      id: `dissent_${i}`,
      significance: 0.5,
      confidence: 0.1,
      content: 'd'.repeat(500),
    }))
    const budgetForTwo = 2 * (JSON.stringify(dissentRows[0], null, 2).length + 40)
    const { droppedDissentCount, keptCount } = selectRowsWithinBudget(dissentRows, budgetForTwo)
    expect(keptCount).toBeLessThan(5)
    expect(droppedDissentCount).toBeGreaterThan(0)
    expect(droppedDissentCount).toBe(5 - keptCount)
  })
})

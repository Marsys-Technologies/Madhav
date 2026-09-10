/**
 * prashna_ask_synthesis_e004_disclosure.test.ts — EDIR E-004 fix verification
 * (S4 pipeline-parity assurance stream; historical id E-004, re-verified at
 * S4 stage S8, `.s4_scratch/S4_stage_S8_report.md`).
 *
 * EDIR E-004: evidence-truncation was disclosed ONLY in the machine-readable
 * `judgment_flags` envelope (`synthesis_evidence_truncated`), never enforced
 * in reader-visible PROSE (`result.reading`). `formatEvidenceBlock` only
 * ASKS the model, via an inline "[TRUNCATED ...]" prompt instruction, to
 * disclose truncation — nothing verified compliance, so a fluent, confident
 * model response that silently ignored the instruction passed straight
 * through untouched (demonstrated at INTEGRATION rung by the S8 investigation
 * repro, preserved at `.s4_scratch/S4_stage_S8_e004_repro_test.ts`).
 *
 * Fix: `synthesizeReading` now deterministically appends a plain disclosure
 * sentence to `reading` server-side, after the model call, whenever
 * `judgment_flags` contains `synthesis_evidence_truncated` — never relying on
 * the model having said so itself.
 *
 * This file forces truncation the same way the S8 repro did (an oversized
 * single evidence row, well past `TOTAL_EVIDENCE_BUDGET_CHARS`) and mocks the
 * model to return a fluent, confident reading with ZERO truncation language
 * — the exact adversarial-but-realistic shape E-004 was raised against.
 * Pre-fix this assertion set FAILS (reading carries no disclosure); post-fix
 * it PASSES (see command output pasted in the fixer's report).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => mockQuery(...args) }))

const mockRunAdapter = vi.fn()
vi.mock('@/lib/adapters/run_adapter', () => ({ runAdapter: (...args: unknown[]) => mockRunAdapter(...args) }))

const mockGetEffectiveModel = vi.fn()
vi.mock('@/lib/models/runtime_config', () => ({ getEffectiveModel: (...args: unknown[]) => mockGetEffectiveModel(...args) }))
vi.mock('@/lib/models/registry', () => ({ DEFAULT_STACK_ID: 'anthropic' }))

import { synthesizeReading, type SynthesizeReadingInput } from '../prashna_ask_synthesis'

// Synthetic test chart ONLY — never the native's real chart (482012f1-…).
const CHART_ROW = {
  id: '1c826d5a-41cb-4450-b4dc-59d440e5f75a',
  name: 'Synthetic Test Chart',
  birth_date: '1990-01-01',
  birth_time: '00:00',
  birth_place: 'Test City',
}

const FLUENT_NON_DISCLOSING_TEXT =
  'Your current Mercury Mahadasha / Saturn Antardasha period favors steady, ' +
  'methodical career growth. This is a favorable window for consolidating ' +
  'existing responsibilities rather than seeking dramatic change.'

const DISCLOSURE_PATTERNS = [
  /truncat/i,
  /partial (coverage|evidence|data)/i,
  /not (all|every) (row|result)/i,
  /incomplete/i,
  /exhaustive/i,
  /only (a portion|some) of/i,
]

function baseInput(overrides: Partial<SynthesizeReadingInput> = {}): SynthesizeReadingInput {
  return {
    chartId: CHART_ROW.id,
    question: 'What does my current dasha period suggest about career timing?',
    queryClass: 'predictive',
    queryIntentSummary: 'Career timing via current dasha',
    evidence: [],
    unresolvedTools: [],
    emptyResultTools: [],
    strippedLeakedCapabilities: [],
    capTripped: null,
    nowContextDate: '2026-08-28',
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
})

describe('EDIR E-004 fix: deterministic reader-visible truncation disclosure', () => {
  it(
    'appends a disclosure sentence to `reading` when synthesis_evidence_truncated is set, ' +
      'even when the model response itself contains zero truncation language',
    async () => {
      // Force truncation: a single evidence row whose serialized size exceeds
      // the full TOTAL_EVIDENCE_BUDGET_CHARS pool (320_000).
      const hugeRow = { note: 'x'.repeat(400_000), significance: 1, confidence: 0.9 }
      const evidence = [{ tool_name: 'query_dasha_periods', bundle: { results: [hugeRow] } }]

      // Realistic adversarial-but-plausible model response: fluent, confident,
      // and silent about truncation/incompleteness — the model ignored the
      // in-prompt "[TRUNCATED ...]" instruction, exactly the E-004 failure shape.
      mockRunAdapter.mockResolvedValue({
        modelId: 'claude-sonnet-test',
        provider: 'anthropic',
        intermediate: [],
        finalText: FLUENT_NON_DISCLOSING_TEXT,
        finishReason: 'stop',
        usage: { inputTokens: 100, outputTokens: 50, costUsd: 0, latencyMs: 5 },
        providerMeta: {},
      })

      const result = await synthesizeReading(baseInput({ evidence }))

      // 1. Envelope channel still works (unchanged behavior).
      expect(result.judgment_flags).toContain('synthesis_evidence_truncated')

      // 2. THE FIX: reader-visible prose now carries the disclosure too,
      //    regardless of what the model itself said.
      const reading = result.reading ?? ''
      const prosedisclosed = DISCLOSURE_PATTERNS.some((p) => p.test(reading))
      expect(prosedisclosed).toBe(true)

      // 3. The model's own text is preserved verbatim (additive fix, not a
      //    rewrite/replace) — the disclosure is appended, not substituted.
      expect(reading.startsWith(FLUENT_NON_DISCLOSING_TEXT)).toBe(true)
      expect(reading).toContain(
        'some retrieved evidence for this reading was truncated due to length',
      )
    },
  )

  it('does NOT append the disclosure sentence when no truncation occurred', async () => {
    mockRunAdapter.mockResolvedValue({
      modelId: 'claude-sonnet-test',
      provider: 'anthropic',
      intermediate: [],
      finalText: FLUENT_NON_DISCLOSING_TEXT,
      finishReason: 'stop',
      usage: { inputTokens: 100, outputTokens: 50, costUsd: 0, latencyMs: 5 },
      providerMeta: {},
    })

    const result = await synthesizeReading(
      baseInput({
        evidence: [{ tool_name: 'query_dasha_periods', bundle: { results: [{ lord_graha: 'Mercury' }] } }],
      }),
    )

    expect(result.judgment_flags).not.toContain('synthesis_evidence_truncated')
    expect(result.reading).toBe(FLUENT_NON_DISCLOSING_TEXT)
  })
})

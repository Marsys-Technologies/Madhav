/**
 * SCRATCH TEST — S4 Stage S8 investigation (EDIR E-004 re-verification).
 *
 * NOT part of the permanent suite. Written by the S4 pipeline-parity assurance
 * stream to demonstrate, at INTEGRATION rung, whether `synthesizeReading`
 * (MCP door / prashna_ask) forces or verifies that reader-visible PROSE
 * (`result.reading`) discloses evidence truncation, or whether disclosure is
 * ONLY machine-readable (`judgment_flags`).
 *
 * Delete after EDIR_V3 entry is filed. See .s4_scratch/S4_stage_S8_report.md.
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

const CHART_ROW = {
  id: '1c826d5a-41cb-4450-b4dc-59d440e5f75a', // synthetic test chart ONLY
  name: 'Synthetic Test Chart',
  birth_date: '1990-01-01',
  birth_time: '00:00',
  birth_place: 'Test City',
}

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

describe('E-004 re-verification: does synthesizeReading FORCE or VERIFY prose disclosure of truncation?', () => {
  it(
    'DEMONSTRATED-CAN-FAIL: forces truncation (oversized evidence item), then simulates a ' +
      'model response that ignores the in-prompt disclosure instruction — the function has ' +
      'NO post-hoc check on `reading` text, so a truncated-but-silent reading passes through ' +
      'untouched with disclosure living ONLY in judgment_flags.',
    async () => {
      // A single evidence item whose serialized size exceeds the per-item budget
      // (MIN_EVIDENCE_ITEM_CHARS=6000, single-item budget = full 320_000 TOTAL,
      // so we need >320_000 chars to force the degenerate/oversized path — use a
      // huge single row to guarantee formatEvidenceBlock marks it truncated).
      const hugeRow = { note: 'x'.repeat(400_000), significance: 1, confidence: 0.9 }
      const evidence = [{ tool_name: 'query_dasha_periods', bundle: { results: [hugeRow] } }]

      // Simulate a REALISTIC adversarial-but-plausible model response: prose
      // that answers the question fluently and confidently, with NO mention of
      // truncation, incompleteness, or partial coverage — i.e. the model did
      // NOT follow the inline "[TRUNCATED ...]" instruction embedded in the
      // evidence block. This is a real, unremarkable LLM failure mode (models
      // routinely drop meta-instructions buried inside large tool-result
      // blocks in favor of just answering the question), not a contrived one.
      mockRunAdapter.mockResolvedValue({
        modelId: 'claude-sonnet-test',
        provider: 'anthropic',
        intermediate: [],
        finalText:
          'Your current Mercury Mahadasha / Saturn Antardasha period favors steady, ' +
          'methodical career growth. This is a favorable window for consolidating ' +
          'existing responsibilities rather than seeking dramatic change.',
        finishReason: 'stop',
        usage: { inputTokens: 100, outputTokens: 50, costUsd: 0, latencyMs: 5 },
        providerMeta: {},
      })

      const result = await synthesizeReading(baseInput({ evidence }))

      // 1. The envelope DOES flag truncation (machine-readable channel — confirmed working).
      expect(result.judgment_flags).toContain('synthesis_evidence_truncated')

      // 2. The reader-visible PROSE contains NO truncation/incompleteness disclosure.
      //    This is the crux of E-004: nothing in synthesizeReading verifies, repairs, or
      //    rejects a reading that omits the disclosure the prompt asked for.
      const reading = result.reading ?? ''
      const disclosurePatterns = [
        /truncat/i,
        /partial (coverage|evidence|data)/i,
        /not (all|every) (row|result)/i,
        /incomplete/i,
        /exhaustive/i,
        /only (a portion|some) of/i,
      ]
      const prosedisclosed = disclosurePatterns.some((p) => p.test(reading))

      // THIS is the demonstrated failure: prose has zero disclosure while the
      // envelope alone carries it — reproducing E-004 as currently live.
      expect(prosedisclosed).toBe(false)

      // 3. Confirm there is no code-level guard that would have caught/blocked
      //    this: the function returns this exact non-disclosing reading as its
      //    success payload (no repair, no rejection, no second pass).
      expect(result.reading).toBe(
        'Your current Mercury Mahadasha / Saturn Antardasha period favors steady, ' +
          'methodical career growth. This is a favorable window for consolidating ' +
          'existing responsibilities rather than seeking dramatic change.',
      )
    },
  )
})

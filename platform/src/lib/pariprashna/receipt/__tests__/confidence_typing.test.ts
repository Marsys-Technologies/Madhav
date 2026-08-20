/**
 * receipt/__tests__/confidence_typing.test.ts — `confidence_typing` field
 * assembly (lane G3-C, PPR-03). Same discipline as G3-A's own
 * `assemble.test.ts`: realistic fixtures, real-source tracing, honest-null
 * coverage, plus this lane's flag-off byte-identity proof and the
 * gate-refuses-to-fire-today proof against `assembleAcharyaReadingReceipt`
 * end-to-end (not just the standalone `confidence/` unit tests).
 */
import { describe, it, expect } from 'vitest'

import { assembleAcharyaReadingReceipt } from '../assemble'
import type { AssembleAcharyaReadingReceiptArgs } from '../assemble'
import { AcharyaReadingReceiptSchema } from '../schema'
import { validateAcharyaReadingReceipt } from '../validate'
import type { DetectedCitationRow } from '@/lib/pariprashna/pipeline/reading_parts'
import type { ToolBundle } from '@/lib/retrieval/shared_types'
import type { TurnProvenanceStamp } from '@/lib/pariprashna/provenance/stamp'

const FIXED_NOW = new Date('2026-08-20T12:00:00.000Z')

function provenanceStamp(): TurnProvenanceStamp {
  return {
    build_id: 'build-1',
    priors_version: 'priors-v3',
    formula_versions: { salience_formula_ver: null },
    ranking_config: { mode: 'composite_v1' },
    now_context_date: '2026-08-20',
    computed_at: '2026-08-20T11:59:00.000Z',
  }
}

function baseArgs(overrides: Partial<AssembleAcharyaReadingReceiptArgs> = {}): AssembleAcharyaReadingReceiptArgs {
  return {
    turnId: 'turn-1',
    conversationId: 'conv-1',
    chartId: 'chart-1',
    now: FIXED_NOW,
    plan: { domains: ['career'] },
    committedBlocks: [],
    accumulatedText: '',
    citationsFound: [],
    citationRewriteEnabled: false,
    resolvedCitations: [],
    citationHallucinationCount: 0,
    completenessReceipt: null,
    safetyDecision: undefined,
    validToolResults: [],
    provenanceStamp: provenanceStamp(),
    ...overrides,
  }
}

function toolBundle(toolName: string, opts: { content?: unknown; confidence?: number } = {}): ToolBundle {
  return {
    tool_bundle_id: 'tb-1',
    tool_name: toolName,
    tool_version: '1.0',
    invocation_params: {},
    results: [
      {
        content: opts.content !== undefined ? JSON.stringify(opts.content) : '',
        confidence: opts.confidence,
      },
    ],
    served_from_cache: false,
    latency_ms: 10,
    result_hash: 'sha256:abc',
    schema_version: '1.0',
  }
}

describe('confidence_typing — flag OFF (default): unavailable, additive-only, never breaks the other 11 fields', () => {
  it('is unavailable with an honest reason when typedConfidenceEnabled is omitted', () => {
    const receipt = assembleAcharyaReadingReceipt(baseArgs())
    expect(receipt.confidence_typing).toEqual({
      status: 'unavailable',
      entries: null,
      activation_gate: null,
      precision_flags: null,
      unavailable_reason: 'PARIPRASHNA_TYPED_CONFIDENCE_ENABLED was off this turn',
    })
  })

  it('is unavailable when typedConfidenceEnabled is explicitly false', () => {
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ typedConfidenceEnabled: false }))
    expect(receipt.confidence_typing.status).toBe('unavailable')
  })

  it('FLAG-OFF BYTE IDENTITY: every field except confidence_typing and receipt_hash is unaffected by this lane\'s new flag', () => {
    const args = baseArgs({
      citationsFound: [{ index: 1, signal_id: 'SIG.MSR.007', layer: 'L2.5' }],
      plan: { domains: ['career', 'health'] },
    })
    const offReceipt = assembleAcharyaReadingReceipt(args) // typedConfidenceEnabled omitted
    const explicitOffReceipt = assembleAcharyaReadingReceipt({ ...args, typedConfidenceEnabled: false })

    const { confidence_typing: _a, receipt_hash: _b, ...offRest } = offReceipt
    const { confidence_typing: _c, receipt_hash: _d, ...explicitOffRest } = explicitOffReceipt
    expect(offRest).toEqual(explicitOffRest)

    // And the flag truly changes nothing about the pre-existing 11 fields
    // relative to a receipt assembled with the flag ON, holding all other
    // inputs fixed — the only structural difference is confidence_typing
    // (and therefore receipt_hash, which covers it).
    const onReceipt = assembleAcharyaReadingReceipt({ ...args, typedConfidenceEnabled: true })
    const { confidence_typing: _e, receipt_hash: _f, ...onRest } = onReceipt
    expect(onRest).toEqual(offRest)
  })
})

describe('confidence_typing — flag ON: real per-type assignment end-to-end through assembleAcharyaReadingReceipt', () => {
  it('types an L1-layer citation deterministic_fact and an L2.5-layer citation structural_prior', () => {
    const citationsFound: DetectedCitationRow[] = [
      { index: 1, signal_id: 'FACT.L1.001', layer: 'L1' },
      { index: 2, signal_id: 'SIG.MSR.042', layer: 'L2.5' },
    ]
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ citationsFound, typedConfidenceEnabled: true }))
    expect(receipt.confidence_typing.status).toBe('measured')
    expect(receipt.confidence_typing.entries).toEqual([
      { ref: 'FACT.L1.001', layer: 'L1', confidence_type: 'deterministic_fact', basis: 'l1_fact_layer' },
      { ref: 'SIG.MSR.042', layer: 'L2.5', confidence_type: 'structural_prior', basis: 'l2_5_structural_signal' },
    ])
  })

  it('an empty citationsFound array yields an honest empty entries array (measured, not unavailable)', () => {
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ typedConfidenceEnabled: true }))
    expect(receipt.confidence_typing.status).toBe('measured')
    expect(receipt.confidence_typing.entries).toEqual([])
  })

  it('THE GATE-REFUSES-TO-FIRE-TODAY PROOF: a turn that consulted query_insights on a chart with zero real calibration matches never types anything empirically_calibrated', () => {
    const citationsFound: DetectedCitationRow[] = [{ index: 1, signal_id: 'SIG.MSR.077', layer: 'L2.5' }]
    const validToolResults = [
      toolBundle('query_insights', { content: { calibration_summary: { total_matches: 0 } } }),
    ]
    const receipt = assembleAcharyaReadingReceipt(
      baseArgs({ citationsFound, validToolResults, typedConfidenceEnabled: true }),
    )
    expect(receipt.confidence_typing.activation_gate?.gate_open).toBe(false)
    expect(receipt.confidence_typing.entries?.every((e) => e.confidence_type !== 'empirically_calibrated')).toBe(true)
    expect(receipt.confidence_typing.entries?.[0].confidence_type).toBe('structural_prior')
  })

  it('opens the gate and types empirically_calibrated once a real sample size clears the (disclosed placeholder) minimum', () => {
    const citationsFound: DetectedCitationRow[] = [{ index: 1, signal_id: 'SIG.MSR.077', layer: 'L2.5' }]
    const validToolResults = [
      toolBundle('query_insights', { content: { calibration_summary: { total_matches: 100 } } }),
    ]
    const receipt = assembleAcharyaReadingReceipt(
      baseArgs({ citationsFound, validToolResults, typedConfidenceEnabled: true }),
    )
    expect(receipt.confidence_typing.activation_gate?.gate_open).toBe(true)
    expect(receipt.confidence_typing.entries?.[0].confidence_type).toBe('empirically_calibrated')
  })

  it('T-8: flags an overstated-precision confidence value from a calibration tool result against its own real (zero) sample size', () => {
    const validToolResults = [
      toolBundle('query_insights', {
        content: { calibration_summary: { total_matches: 0 } },
        confidence: 0.734,
      }),
    ]
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ validToolResults, typedConfidenceEnabled: true }))
    expect(receipt.confidence_typing.precision_flags).toHaveLength(1)
    expect(receipt.confidence_typing.precision_flags?.[0]).toMatchObject({
      tool_name: 'query_insights',
      overstated: true,
      max_supported_decimal_places: 0,
    })
  })

  it('does NOT flag a correctly-precise confidence value', () => {
    const validToolResults = [
      toolBundle('query_insights', {
        content: { calibration_summary: { total_matches: 150 } },
        confidence: 0.73,
      }),
    ]
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ validToolResults, typedConfidenceEnabled: true }))
    expect(receipt.confidence_typing.precision_flags).toEqual([])
  })

  it('a fully-populated confidence_typing receipt satisfies the schema', () => {
    const receipt = assembleAcharyaReadingReceipt(
      baseArgs({
        citationsFound: [{ index: 1, signal_id: 'SIG.MSR.001', layer: 'L2.5' }],
        validToolResults: [toolBundle('query_insights', { content: { calibration_summary: { total_matches: 5 } } })],
        typedConfidenceEnabled: true,
      }),
    )
    expect(() => AcharyaReadingReceiptSchema.parse(receipt)).not.toThrow()
    expect(validateAcharyaReadingReceipt(receipt).ok).toBe(true)
  })
})

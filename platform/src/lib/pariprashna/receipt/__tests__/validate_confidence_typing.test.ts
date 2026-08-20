/**
 * receipt/__tests__/validate_confidence_typing.test.ts — the V6/V6b
 * confidence_typing enforcement (lane G3-C, PPR-03), same RED→GREEN
 * discipline as G3-A's own `validate.test.ts`.
 */
import { describe, it, expect } from 'vitest'

import { assembleAcharyaReadingReceipt } from '../assemble'
import { validateAcharyaReadingReceipt } from '../validate'
import type { AcharyaReadingReceipt } from '../schema'
import type { TurnProvenanceStamp } from '@/lib/pariprashna/provenance/stamp'
import type { DetectedCitationRow } from '@/lib/pariprashna/pipeline/reading_parts'

function provenanceStamp(): TurnProvenanceStamp {
  return {
    build_id: 'build-1',
    priors_version: 'priors-v1',
    formula_versions: { salience_formula_ver: null },
    ranking_config: { mode: 'composite_v1' },
    now_context_date: '2026-08-20',
    computed_at: '2026-08-20T11:59:00.000Z',
  }
}

function honestReceiptWithTypedConfidence(citationsFound: DetectedCitationRow[] = []): AcharyaReadingReceipt {
  return assembleAcharyaReadingReceipt({
    turnId: 'turn-1',
    conversationId: 'conv-1',
    chartId: 'chart-1',
    now: new Date('2026-08-20T12:00:00.000Z'),
    plan: { domains: ['career'] },
    committedBlocks: [],
    accumulatedText: '',
    citationsFound,
    citationRewriteEnabled: false,
    resolvedCitations: [],
    citationHallucinationCount: 0,
    completenessReceipt: null,
    safetyDecision: undefined,
    validToolResults: [],
    provenanceStamp: provenanceStamp(),
    typedConfidenceEnabled: true,
  })
}

describe('validateAcharyaReadingReceipt — confidence_typing GREEN', () => {
  it('accepts an honestly-assembled measured confidence_typing (gate closed today, no empirically_calibrated entries)', () => {
    const receipt = honestReceiptWithTypedConfidence([{ index: 1, signal_id: 'SIG.MSR.001', layer: 'L2.5' }])
    const result = validateAcharyaReadingReceipt(receipt)
    expect(result.ok).toBe(true)
  })

  it('accepts an honest unavailable confidence_typing (flag off)', () => {
    const receipt = assembleAcharyaReadingReceipt({
      turnId: 'turn-1',
      conversationId: 'conv-1',
      chartId: 'chart-1',
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
      // typedConfidenceEnabled omitted — defaults off.
    })
    const result = validateAcharyaReadingReceipt(receipt)
    expect(result.ok).toBe(true)
    expect(receipt.confidence_typing.status).toBe('unavailable')
  })
})

describe('validateAcharyaReadingReceipt — confidence_typing RED: V6b, the PPR-03 gate enforcement', () => {
  it('REJECTS a receipt with an entry hand-tampered to empirically_calibrated while the gate is closed — exactly the PPR-03 violation this validator exists to catch', () => {
    const receipt = honestReceiptWithTypedConfidence([{ index: 1, signal_id: 'SIG.MSR.001', layer: 'L2.5' }])
    expect(receipt.confidence_typing.activation_gate?.gate_open).toBe(false)
    const tampered: AcharyaReadingReceipt = {
      ...receipt,
      confidence_typing: {
        ...receipt.confidence_typing,
        entries: [
          { ref: 'SIG.MSR.001', layer: 'L2.5', confidence_type: 'empirically_calibrated', basis: 'calibration_gate_open' },
        ],
      },
    }
    const result = validateAcharyaReadingReceipt(tampered)
    expect(result.ok).toBe(false)
    expect(result.violations.some((v) => v.includes('empirically_calibrated') && v.includes('PPR-03'))).toBe(true)
  })

  it('REJECTS a measured confidence_typing that fabricates data (entries non-null claimed alongside status unavailable)', () => {
    const receipt = honestReceiptWithTypedConfidence()
    const broken: AcharyaReadingReceipt = {
      ...receipt,
      confidence_typing: {
        status: 'unavailable',
        entries: [{ ref: 'SIG.MSR.999', layer: 'L2.5', confidence_type: 'structural_prior', basis: 'l2_5_structural_signal' }],
        activation_gate: null,
        precision_flags: null,
        unavailable_reason: 'flag off',
      },
    }
    const result = validateAcharyaReadingReceipt(broken)
    expect(result.ok).toBe(false)
    expect(result.violations.some((v) => v.includes('confidence_typing'))).toBe(true)
  })

  it('ACCEPTS an entry typed empirically_calibrated when the gate is genuinely open (not a false positive)', () => {
    const receipt = honestReceiptWithTypedConfidence([{ index: 1, signal_id: 'SIG.MSR.001', layer: 'L2.5' }])
    const opened: AcharyaReadingReceipt = {
      ...receipt,
      confidence_typing: {
        ...receipt.confidence_typing,
        activation_gate: {
          gate_open: true,
          sample_size: 100,
          min_sample_size_required: 30,
          threshold_is_placeholder: true,
          gate_note: 'Gate OPEN: real calibration sample size (n=100) meets the minimum (30).',
        },
        entries: [
          { ref: 'SIG.MSR.001', layer: 'L2.5', confidence_type: 'empirically_calibrated', basis: 'calibration_gate_open' },
        ],
      },
    }
    // Re-hashing is out of scope for this structural-only check (V1 would
    // catch the mismatch separately) — isolate V6b by checking violations
    // exclude the PPR-03 message specifically.
    const result = validateAcharyaReadingReceipt(opened)
    expect(result.violations.some((v) => v.includes('PPR-03'))).toBe(false)
  })
})

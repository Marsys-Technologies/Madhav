/**
 * receipt/validate.test.ts — lane G3-A (PPR-01), the §N.8 enforcement proof.
 *
 * A real red/green demonstration, matching the discipline P1's G1-A
 * hardening rounds used: a GREEN case (a genuinely-assembled, honest
 * receipt passes), then several RED cases each constructed by hand-editing
 * one field to a plausible-looking value that has no real backing —
 * confirming the validator actually catches each one, not that it merely
 * "runs without throwing".
 */
import { describe, it, expect } from 'vitest'

import { assembleAcharyaReadingReceipt } from '../assemble'
import { validateAcharyaReadingReceipt, assertValidAcharyaReadingReceipt } from '../validate'
import type { AcharyaReadingReceipt } from '../schema'
import type { WebCompletenessReceipt } from '@/lib/pipeline/completeness_wiring'
import type { TurnProvenanceStamp } from '@/lib/pariprashna/provenance/stamp'

function provenanceStamp(): TurnProvenanceStamp {
  return {
    build_id: 'build-1',
    priors_version: 'priors-v1',
    formula_versions: { salience_formula_ver: null },
    ranking_config: { mode: 'composite_v1' },
    now_context_date: '2026-08-19',
    computed_at: '2026-08-19T11:59:00.000Z',
  }
}

function completenessReceiptFixture(): WebCompletenessReceipt {
  return {
    served: [{ floor_item_id: 'p1', source: 'tool_a' }],
    empty: [{ floor_item_id: 'p2', empty_reason: 'route_empty' }],
    dark: [],
    coverage: { floor_item_total: 2, served: 1, empty: 1, dark: 0 },
    channel: 'web',
    channel_note: 'note',
    web_dark_primitive_ids: [],
  }
}

/** A genuinely-assembled, honestly-earned receipt — the GREEN baseline. */
function honestReceipt(): AcharyaReadingReceipt {
  return assembleAcharyaReadingReceipt({
    turnId: 'turn-1',
    conversationId: 'conv-1',
    chartId: 'chart-1',
    now: new Date('2026-08-19T12:00:00.000Z'),
    plan: { domains: ['career'] },
    committedBlocks: [{ id: 'blk-1-1', role: 'prose', text: 'See SIG.MSR.001.' }],
    accumulatedText: 'See SIG.MSR.001.',
    citationsFound: [{ index: 1, signal_id: 'SIG.MSR.001', layer: 'L2.5' }],
    citationRewriteEnabled: true,
    resolvedCitations: [{ index: 1, signal_id: 'SIG.MSR.001', layer: 'L2.5', snippet: 's', grade: 'primary' }],
    citationHallucinationCount: 0,
    completenessReceipt: completenessReceiptFixture(),
    safetyDecision: {
      decision_id: 'dec-1',
      turn_id: 'turn-1',
      chart_id: 'chart-1',
      enforced: false,
      classes_detected: [],
      severity: 'none',
      action: 'proceed',
      subject_kind: null,
      ncd4_interstitial_applies: false,
      detections: [],
      evasion_markers: [],
      excluded_capabilities: [],
      llm_assist_ran: false,
      review_id: null,
      audit_written: false,
      decided_at: '2026-08-19T11:58:00.000Z',
    },
    validToolResults: [],
    provenanceStamp: provenanceStamp(),
  })
}

describe('validateAcharyaReadingReceipt — GREEN', () => {
  it('accepts a genuinely-assembled receipt with zero violations', () => {
    const result = validateAcharyaReadingReceipt(honestReceipt())
    expect(result.ok).toBe(true)
    expect(result.violations).toEqual([])
  })

  it('does NOT fail on an honest, well-formed unavailable field', () => {
    const receipt = assembleAcharyaReadingReceipt({
      turnId: 'turn-1',
      conversationId: 'conv-1',
      chartId: 'chart-1',
      plan: { domains: undefined },
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
    })
    // Every complex field here is honestly 'unavailable' — the validator's
    // job is to confirm each is COHERENTLY unavailable, not to demand data.
    const result = validateAcharyaReadingReceipt(receipt)
    expect(result.ok).toBe(true)
  })

  it('assertValidAcharyaReadingReceipt does not throw on the honest receipt', () => {
    expect(() => assertValidAcharyaReadingReceipt(honestReceipt())).not.toThrow()
  })
})

describe('validateAcharyaReadingReceipt — RED: catches a fabricated/tampered field', () => {
  it('rejects a receipt whose receipt_hash was hand-replaced with a plausible-looking value', () => {
    const receipt = { ...honestReceipt(), receipt_hash: 'a'.repeat(64) }
    const result = validateAcharyaReadingReceipt(receipt)
    expect(result.ok).toBe(false)
    expect(result.violations.some((v) => v.includes('receipt_hash mismatch'))).toBe(true)
  })

  it('rejects a receipt whose data field was tampered with after hashing (hash no longer matches)', () => {
    const receipt = honestReceipt()
    const tampered: AcharyaReadingReceipt = {
      ...receipt,
      coverage: { ...receipt.coverage, served: (receipt.coverage.served ?? 0) + 1 },
    }
    const result = validateAcharyaReadingReceipt(tampered)
    expect(result.ok).toBe(false)
    expect(result.violations.some((v) => v.includes('receipt_hash mismatch'))).toBe(true)
  })

  it('rejects a coverage field claiming measured status with a fabricated null subfield', () => {
    const receipt = honestReceipt()
    const broken: AcharyaReadingReceipt = {
      ...receipt,
      coverage: { ...receipt.coverage, status: 'measured', floor_item_total: null },
    }
    const result = validateAcharyaReadingReceipt(broken)
    expect(result.ok).toBe(false)
    expect(result.violations.some((v) => v.includes('coverage') && v.includes('floor_item_total'))).toBe(true)
  })

  it('rejects an unavailable field that still carries fabricated data', () => {
    const receipt = honestReceipt()
    const broken: AcharyaReadingReceipt = {
      ...receipt,
      cross_domain: { status: 'unavailable', domains: ['career', 'wealth'], unavailable_reason: 'plausible-looking but fake reason' },
    }
    const result = validateAcharyaReadingReceipt(broken)
    expect(result.ok).toBe(false)
    expect(result.violations.some((v) => v.includes('cross_domain'))).toBe(true)
  })

  it('rejects a safety_decision claiming enforced=false while also claiming detected classes (a plausible-looking but incoherent claim)', () => {
    const receipt = honestReceipt()
    const broken: AcharyaReadingReceipt = {
      ...receipt,
      safety_decision: {
        status: 'measured',
        decision_id: 'dec-fabricated',
        enforced: false,
        severity: 'none',
        action: 'proceed',
        classes_detected: ['hs2_suicide_adjacent'],
        review_id: null,
        audit_written: true,
        unavailable_reason: null,
      },
    }
    const result = validateAcharyaReadingReceipt(broken)
    expect(result.ok).toBe(false)
    expect(result.violations.some((v) => v.includes('enforced=false but classes_detected'))).toBe(true)
  })

  it('rejects a coverage object whose numbers do not sum to floor_item_total', () => {
    const receipt = honestReceipt()
    const broken: AcharyaReadingReceipt = {
      ...receipt,
      coverage: { ...receipt.coverage, served: 9, empty: 9, dark: 9, floor_item_total: 2 },
    }
    const result = validateAcharyaReadingReceipt(broken)
    expect(result.ok).toBe(false)
    expect(result.violations.some((v) => v.includes('served(9)'))).toBe(true)
  })

  it('rejects a calibration_disclosure claiming consulted=true with an empty tool-name list', () => {
    const receipt = honestReceipt()
    const broken: AcharyaReadingReceipt = {
      ...receipt,
      calibration_disclosure: { consulted: true, consulted_tool_names: [], disclosure_note: 'fabricated' },
    }
    const result = validateAcharyaReadingReceipt(broken)
    expect(result.ok).toBe(false)
    expect(result.violations.some((v) => v.includes('calibration_disclosure'))).toBe(true)
  })

  it('assertValidAcharyaReadingReceipt THROWS on a fabricated receipt (fails, not just logs)', () => {
    const receipt = { ...honestReceipt(), receipt_hash: 'f'.repeat(64) }
    expect(() => assertValidAcharyaReadingReceipt(receipt)).toThrow(/validation FAILED/)
  })
})

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
import { computeReceiptHash } from '../hash'
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

/**
 * interpretation_sets coherence — lane G3-B (PPR-02) additive extension.
 * Same red/green discipline as the G3-A suite above: a GREEN case (a
 * genuinely-assembled field, honest end to end) then RED cases each
 * constructed to look plausible but with no real backing, confirming the
 * validator actually catches each one.
 */
describe('validateAcharyaReadingReceipt — interpretation_sets (G3-B)', () => {
  it('GREEN: accepts a receipt whose interpretation_sets is the honest unavailable default', () => {
    const receipt = honestReceipt()
    expect(receipt.interpretation_sets?.status).toBe('unavailable')
    const result = validateAcharyaReadingReceipt(receipt)
    expect(result.ok).toBe(true)
  })

  it('GREEN: accepts a receipt with a genuinely-measured, coherent interpretation_sets field', () => {
    const receipt = {
      ...honestReceipt(),
      interpretation_sets: {
        status: 'measured' as const,
        interpretation_sets_schema_version: 2 as const,
        detected_count: 2,
        covered_count: 2,
        truncated_count: 0,
        waived_count: 1,
        sets: [
          {
            judgment_id: 'sig-domain_verdict-1',
            category: 'domain_verdict' as const,
            status: 'generated' as const,
            detection_basis: "G2-A block role='verdict' (first prose block of its pass)",
            candidates: [
              { reading: 'A', rationale: 'ra' },
              { reading: 'B', rationale: 'rb' },
              { reading: 'C', rationale: 'rc' },
            ],
            selected_index: 0,
            selected_rationale: 'A fits best.',
            falsifier: 'If X is observed, A is wrong.',
            waiver_reason: null,
          },
          {
            judgment_id: 'sig-remedial-1',
            category: 'remedial' as const,
            status: 'waived' as const,
            detection_basis:
              'remedy lexicon match on this block (per-block) + remedial_codex_query was ' +
              'consulted somewhere in this turn (TURN-SCOPED consultation — not verified ' +
              'specifically for this block)',
            candidates: null,
            selected_index: null,
            selected_rationale: null,
            falsifier: null,
            waiver_reason: 'Only one classical rule applies; no genuine second reading exists.',
          },
        ],
        unavailable_reason: null,
      },
    }
    // receipt_hash was computed over the OLD (unavailable) interpretation_sets,
    // so recompute it here the same way `assembleAcharyaReadingReceipt` would —
    // this test is about STRUCTURAL coherence (V6/V7), not the hash (V1 is
    // already independently covered above).
    const { receipt_hash: _old, ...content } = receipt
    void _old
    const fixed = { ...content, receipt_hash: computeReceiptHash(content) }
    const result = validateAcharyaReadingReceipt(fixed)
    expect(result.ok).toBe(true)
    expect(result.violations).toEqual([])
  })

  it('RED: catches a SIGNIFICANT claim with NEITHER a set NOR a waiver (sets shorter than covered_count)', () => {
    const receipt = honestReceipt()
    const tamperedContent = {
      ...receipt,
      interpretation_sets: {
        status: 'measured' as const,
        interpretation_sets_schema_version: 2 as const,
        detected_count: 1,
        covered_count: 1,
        truncated_count: 0,
        waived_count: 0,
        // A claim was detected and "covered", but no entry was ever produced
        // for it — exactly the defect PPR-02's validator must reject.
        sets: [],
        unavailable_reason: null,
      },
    }
    const { receipt_hash: _old2, ...content } = tamperedContent
    void _old2
    const fixed = { ...content, receipt_hash: computeReceiptHash(content) }
    const result = validateAcharyaReadingReceipt(fixed)
    expect(result.ok).toBe(false)
    expect(result.violations.some((v) => v.includes('sets.length') && v.includes('covered_count'))).toBe(true)
  })

  it('RED: catches a "generated" entry with fewer than 3 candidates (padded/incomplete set)', () => {
    const receipt = honestReceipt()
    const tamperedContent = {
      ...receipt,
      interpretation_sets: {
        status: 'measured' as const,
        interpretation_sets_schema_version: 2 as const,
        detected_count: 1,
        covered_count: 1,
        truncated_count: 0,
        waived_count: 0,
        sets: [
          {
            judgment_id: 'sig-domain_verdict-1',
            category: 'domain_verdict' as const,
            status: 'generated' as const,
            detection_basis: "G2-A block role='verdict' (first prose block of its pass)",
            candidates: [{ reading: 'Only one.', rationale: 'r' }],
            selected_index: 0,
            selected_rationale: 'r',
            falsifier: 'f',
            waiver_reason: null,
          },
        ],
        unavailable_reason: null,
      },
    }
    const { receipt_hash: _old3, ...content } = tamperedContent
    void _old3
    const fixed = { ...content, receipt_hash: computeReceiptHash(content) }
    const result = validateAcharyaReadingReceipt(fixed)
    expect(result.ok).toBe(false)
    expect(result.violations.some((v) => v.includes('fewer than 3'))).toBe(true)
  })

  it('RED: catches a "waived" entry with no waiver_reason (an unexplained waiver is not honest)', () => {
    const receipt = honestReceipt()
    const tamperedContent = {
      ...receipt,
      interpretation_sets: {
        status: 'measured' as const,
        interpretation_sets_schema_version: 2 as const,
        detected_count: 1,
        covered_count: 1,
        truncated_count: 0,
        waived_count: 1,
        sets: [
          {
            judgment_id: 'sig-remedial-1',
            category: 'remedial' as const,
            status: 'waived' as const,
            detection_basis:
              'remedy lexicon match on this block (per-block) + remedial_codex_query was ' +
              'consulted somewhere in this turn (TURN-SCOPED consultation — not verified ' +
              'specifically for this block)',
            candidates: null,
            selected_index: null,
            selected_rationale: null,
            falsifier: null,
            waiver_reason: null,
          },
        ],
        unavailable_reason: null,
      },
    }
    const { receipt_hash: _old4, ...content } = tamperedContent
    void _old4
    const fixed = { ...content, receipt_hash: computeReceiptHash(content) }
    const result = validateAcharyaReadingReceipt(fixed)
    expect(result.ok).toBe(false)
    expect(result.violations.some((v) => v.includes('waiver_reason is empty'))).toBe(true)
  })
})

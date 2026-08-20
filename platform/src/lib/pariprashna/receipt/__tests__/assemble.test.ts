/**
 * receipt/assemble.test.ts — lane G3-A (PPR-01).
 *
 * One test per receipt field proving it traces to a REAL source: fixture
 * inputs are fed to `assembleAcharyaReadingReceipt` and the receipt field is
 * asserted to match exactly what that source contains — never merely
 * "returns something". A second group proves the honest-null path: when a
 * field's real source is genuinely absent, the field goes `unavailable`
 * with a reason, never a fabricated value.
 */
import { describe, it, expect } from 'vitest'

import { assembleAcharyaReadingReceipt, CALIBRATION_BEARING_TOOL_NAMES, CALIBRATION_CONSULTED_NOTE } from '../assemble'
import type { AssembleAcharyaReadingReceiptArgs } from '../assemble'
import { AcharyaReadingReceiptSchema } from '../schema'
import type { OpenBlock, DetectedCitationRow } from '@/lib/pariprashna/pipeline/reading_parts'
import type { ResolvedTurnCitation } from '@/lib/pariprashna/citations/stream_wiring'
import type { WebCompletenessReceipt } from '@/lib/pipeline/completeness_wiring'
import type { SafetyDecision } from '@/lib/pariprashna/safety'
import type { ToolBundle } from '@/lib/retrieval/shared_types'
import type { TurnProvenanceStamp } from '@/lib/pariprashna/provenance/stamp'

const FIXED_NOW = new Date('2026-08-19T12:00:00.000Z')

function provenanceStamp(): TurnProvenanceStamp {
  return {
    build_id: 'build-42',
    priors_version: 'priors-v3',
    formula_versions: { salience_formula_ver: null },
    ranking_config: { mode: 'composite_v1' },
    now_context_date: '2026-08-19',
    computed_at: '2026-08-19T11:59:00.000Z',
  }
}

function baseArgs(overrides: Partial<AssembleAcharyaReadingReceiptArgs> = {}): AssembleAcharyaReadingReceiptArgs {
  return {
    turnId: 'turn-1',
    conversationId: 'conv-1',
    chartId: 'chart-1',
    now: FIXED_NOW,
    plan: { domains: ['career', 'health'] },
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

function toolBundle(toolName: string): ToolBundle {
  return {
    tool_bundle_id: 'tb-1',
    tool_name: toolName,
    tool_version: '1.0',
    invocation_params: {},
    results: [],
    served_from_cache: false,
    latency_ms: 10,
    result_hash: 'sha256:abc',
    schema_version: '1.0',
  }
}

function completenessReceiptFixture(): WebCompletenessReceipt {
  return {
    served: [{ floor_item_id: 'p1', source: 'tool_a' }],
    empty: [{ floor_item_id: 'p2', empty_reason: 'route_empty' }],
    dark: [{ floor_item_id: 'p3', cr_row: 'CR-42' }],
    coverage: { floor_item_total: 3, served: 1, empty: 1, dark: 1 },
    channel: 'web',
    channel_note: '1 of 3 floor items have no web-executable retrieval tool',
    web_dark_primitive_ids: ['p3'],
  }
}

function safetyDecisionFixture(overrides: Partial<SafetyDecision> = {}): SafetyDecision {
  return {
    decision_id: 'dec-1',
    turn_id: 'turn-1',
    chart_id: 'chart-1',
    enforced: true,
    classes_detected: [],
    severity: 'none',
    action: 'proceed',
    subject_kind: 'native_self',
    ncd4_interstitial_applies: false,
    detections: [],
    evasion_markers: [],
    excluded_capabilities: [],
    llm_assist_ran: false,
    review_id: null,
    audit_written: true,
    decided_at: '2026-08-19T11:58:00.000Z',
    ...overrides,
  }
}

describe('assembleAcharyaReadingReceipt — per-field real-source tracing', () => {
  it('coverage traces to the WebCompletenessReceipt.coverage object', () => {
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ completenessReceipt: completenessReceiptFixture() }))
    expect(receipt.coverage).toEqual({
      status: 'measured',
      served: 1,
      empty: 1,
      dark: 1,
      floor_item_total: 3,
      channel: 'web',
      channel_note: '1 of 3 floor items have no web-executable retrieval tool',
      unavailable_reason: null,
    })
  })

  it('facts_consumed traces to citationsFound, by reference only (never restates a value)', () => {
    const citationsFound: DetectedCitationRow[] = [
      { index: 1, signal_id: 'SIG.MSR.007', layer: 'L2.5' },
      { index: 2, signal_id: 'SIG.MSR.011', layer: 'L2.5' },
    ]
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ citationsFound }))
    expect(receipt.facts_consumed).toEqual([
      { ref: 'SIG.MSR.007', layer: 'L2.5', index: 1 },
      { ref: 'SIG.MSR.011', layer: 'L2.5', index: 2 },
    ])
  })

  it('derivation_chains traces to committedBlocks, per-block pass id parsed from the real block id + per-block citation scan', () => {
    const committedBlocks: OpenBlock[] = [
      { id: 'blk-1-1', role: 'prose', text: 'See SIG.MSR.007 for grounding.' },
      { id: 'blk-2-1', role: 'thinking', text: 'internal reasoning, no citations' },
    ]
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ committedBlocks }))
    expect(receipt.derivation_chains).toEqual([
      { block_id: 'blk-1-1', pass_id: 1, role: 'prose', fact_refs: ['SIG.MSR.007'] },
      { block_id: 'blk-2-1', pass_id: 2, role: 'thinking', fact_refs: [] },
    ])
  })

  it('derivation_chains — defect 2 RED→GREEN: when citationRewriteEnabled, block text carries resolved `[n]` markers (not raw SIG.MSR.NNN tokens); fact_refs is populated from resolvedCitations per-block, not silently empty', () => {
    // Realistic G2-B rewrite-flag-on fixture: block text as the rewriter
    // actually leaves it — resolved inline markers `[1]`/`[2]`, never the
    // raw `SIG.MSR.NNN` sentinel (the register-leak lint already scrubbed
    // it). A regex scan for `SIG.MSR.NNN` over THIS text structurally finds
    // nothing — that was the defect.
    const committedBlocks: OpenBlock[] = [
      { id: 'blk-1-1', role: 'prose', text: 'The native shows strong resolve [1] and career drive [2].' },
      { id: 'blk-2-1', role: 'prose', text: 'A second pass references the same finding [1] again.' },
      { id: 'blk-3-1', role: 'thinking', text: 'internal reasoning, no markers' },
    ]
    const resolvedCitations: ResolvedTurnCitation[] = [
      { index: 1, signal_id: 'SIG.MSR.007', layer: 'L2.5', snippet: 'a', grade: 'primary' },
      { index: 2, signal_id: 'SIG.MSR.011', layer: 'L2.5', snippet: 'b', grade: 'supporting' },
    ]

    // Prove the RED half directly: the old mechanism (extractCitations over
    // block text) finds nothing on this exact fixture, which is exactly why
    // the silent-empty defect existed.
    const rawScanFindsNothing = committedBlocks.every(
      (b) => !/SIG\.MSR\.\d+/.test(b.text),
    )
    expect(rawScanFindsNothing).toBe(true)

    const receipt = assembleAcharyaReadingReceipt(
      baseArgs({ committedBlocks, citationRewriteEnabled: true, resolvedCitations }),
    )

    // GREEN: fact_refs is correctly populated per block from the resolver's
    // own ledger, not silently empty.
    expect(receipt.derivation_chains).toEqual([
      { block_id: 'blk-1-1', pass_id: 1, role: 'prose', fact_refs: ['SIG.MSR.007', 'SIG.MSR.011'] },
      { block_id: 'blk-2-1', pass_id: 2, role: 'prose', fact_refs: ['SIG.MSR.007'] },
      { block_id: 'blk-3-1', pass_id: 3, role: 'thinking', fact_refs: [] },
    ])
  })

  it('derivation_chains flag-on does not false-positive across adjacent citation indices (e.g. [1] is not a substring match inside [10])', () => {
    const committedBlocks: OpenBlock[] = [
      { id: 'blk-1-1', role: 'prose', text: 'Only the tenth finding applies here [10].' },
    ]
    const resolvedCitations: ResolvedTurnCitation[] = [
      { index: 1, signal_id: 'SIG.MSR.001', layer: 'L2.5', snippet: 'a', grade: 'primary' },
      { index: 10, signal_id: 'SIG.MSR.010', layer: 'L2.5', snippet: 'b', grade: 'primary' },
    ]
    const receipt = assembleAcharyaReadingReceipt(
      baseArgs({ committedBlocks, citationRewriteEnabled: true, resolvedCitations }),
    )
    expect(receipt.derivation_chains).toEqual([
      { block_id: 'blk-1-1', pass_id: 1, role: 'prose', fact_refs: ['SIG.MSR.010'] },
    ])
  })

  it('cross_domain traces to plan.domains verbatim', () => {
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ plan: { domains: ['marriage', 'wealth'] } }))
    expect(receipt.cross_domain).toEqual({ status: 'measured', domains: ['marriage', 'wealth'], unavailable_reason: null })
  })

  it('evidence_grades traces to resolvedCitations grade tally + hallucination count when the rewriter ran', () => {
    const resolvedCitations: ResolvedTurnCitation[] = [
      { index: 1, signal_id: 'SIG.MSR.001', layer: 'L2.5', snippet: 'a', grade: 'primary' },
      { index: 2, signal_id: 'SIG.MSR.002', layer: 'L2.5', snippet: 'b', grade: 'primary' },
      { index: 3, signal_id: 'SIG.MSR.003', layer: 'L2.5', snippet: 'c', grade: 'supporting' },
    ]
    const receipt = assembleAcharyaReadingReceipt(
      baseArgs({ citationRewriteEnabled: true, resolvedCitations, citationHallucinationCount: 2 }),
    )
    expect(receipt.evidence_grades).toEqual({
      status: 'measured',
      grade_counts: { primary: 2, supporting: 1, contextual: 0, unverified: 0, prior_reading: 0 },
      hallucination_count: 2,
      unavailable_reason: null,
    })
  })

  it('honest_gaps traces to the completeness receipt\'s own itemized empty[]/dark[] arrays', () => {
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ completenessReceipt: completenessReceiptFixture() }))
    expect(receipt.honest_gaps).toEqual({
      status: 'measured',
      gaps: [
        { floor_item_id: 'p2', kind: 'empty', reason: 'route_empty' },
        { floor_item_id: 'p3', kind: 'dark', reason: 'CR-42' },
      ],
      unavailable_reason: null,
    })
  })

  it('safety_decision traces to the supplied SafetyDecision object by its own fields', () => {
    const safetyDecision = safetyDecisionFixture({
      severity: 'review_required',
      action: 'seal_pending_signoff',
      classes_detected: ['hs4_mortality_window'],
      review_id: 'rev-9',
    })
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ safetyDecision }))
    expect(receipt.safety_decision).toEqual({
      status: 'measured',
      decision_id: 'dec-1',
      enforced: true,
      severity: 'review_required',
      action: 'seal_pending_signoff',
      classes_detected: ['hs4_mortality_window'],
      review_id: 'rev-9',
      audit_written: true,
      unavailable_reason: null,
    })
  })

  it('calibration_disclosure traces to validToolResults tool_name membership in the real registered L5 calibration tool list', () => {
    expect(CALIBRATION_BEARING_TOOL_NAMES).toContain('query_calibration')
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ validToolResults: [toolBundle('query_calibration')] }))
    expect(receipt.calibration_disclosure.consulted).toBe(true)
    expect(receipt.calibration_disclosure.consulted_tool_names).toEqual(['query_calibration'])
  })

  it('defect 3 RED→GREEN: query_insights is also a registered L5 calibration-bearing tool (registry/layers/L5_mimamsa/query_insights.ts directly reads mimamsa_calibration and returns calibration_summary) — a turn where ONLY query_insights ran must not emit a false "nothing consulted" disclosure', () => {
    // RED: the list used to name only query_calibration — a turn where
    // query_insights (and not query_calibration) ran would have fallen
    // through to the false "no calibration capability was consulted"
    // structural-mode disclosure. GREEN: query_insights is now named.
    expect(CALIBRATION_BEARING_TOOL_NAMES).toContain('query_insights')
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ validToolResults: [toolBundle('query_insights')] }))
    expect(receipt.calibration_disclosure.consulted).toBe(true)
    expect(receipt.calibration_disclosure.consulted_tool_names).toEqual(['query_insights'])
    expect(receipt.calibration_disclosure.disclosure_note).toBe(CALIBRATION_CONSULTED_NOTE)
  })

  it('prose_binding traces to committedBlocks + a real sha256 of accumulatedText', () => {
    const committedBlocks: OpenBlock[] = [{ id: 'blk-1-1', role: 'prose', text: 'Hello reader.' }]
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ committedBlocks, accumulatedText: 'Hello reader.' }))
    expect(receipt.prose_binding.blocks).toEqual([
      { block_id: 'blk-1-1', role: 'prose', char_count: 13, semantic_kind: null, semantic_role: null },
    ])
    expect(receipt.prose_binding.accumulated_char_count).toBe(13)
    expect(receipt.prose_binding.accumulated_text_sha256).toMatch(/^[0-9a-f]{64}$/)
  })

  it('prose_binding carries the G2-A semantic classification when a block committed one (reused, not re-derived)', () => {
    const committedBlocks: OpenBlock[] = [
      { id: 'blk-1-1', role: 'prose', text: 'Verdict text.', semantic: { kind: 'paragraph', role: 'verdict' } },
    ]
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ committedBlocks, accumulatedText: 'Verdict text.' }))
    expect(receipt.prose_binding.blocks[0].semantic_kind).toBe('paragraph')
    expect(receipt.prose_binding.blocks[0].semantic_role).toBe('verdict')
  })

  it('provenance wraps computeTurnReceiptProvenance\'s own stamp object verbatim', () => {
    const stamp = provenanceStamp()
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ provenanceStamp: stamp }))
    expect(receipt.provenance).toEqual({
      build_id: stamp.build_id,
      priors_version: stamp.priors_version,
      formula_versions: stamp.formula_versions,
      ranking_config: stamp.ranking_config,
      now_context_date: stamp.now_context_date,
      computed_at: stamp.computed_at,
    })
  })

  it('receipt_hash is a real hash of the receipt\'s own content (not a constant)', () => {
    const r1 = assembleAcharyaReadingReceipt(baseArgs({ plan: { domains: ['career'] } }))
    const r2 = assembleAcharyaReadingReceipt(baseArgs({ plan: { domains: ['health'] } }))
    expect(r1.receipt_hash).not.toBe(r2.receipt_hash)
    expect(r1.receipt_hash).toMatch(/^[0-9a-f]{64}$/)
  })
})

describe('assembleAcharyaReadingReceipt — honest null-by-default when the real source is absent', () => {
  it('coverage is unavailable (never a fabricated number) when no completeness receipt was built', () => {
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ completenessReceipt: null }))
    expect(receipt.coverage.status).toBe('unavailable')
    expect(receipt.coverage.served).toBeNull()
    expect(receipt.coverage.unavailable_reason).toBeTruthy()
  })

  it('cross_domain is unavailable when plan.domains was never populated', () => {
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ plan: { domains: undefined } }))
    expect(receipt.cross_domain).toEqual({
      status: 'unavailable',
      domains: null,
      unavailable_reason: 'plan.domains was not populated by the planner for this turn',
    })
  })

  it('evidence_grades is unavailable (not zero) when the live citation rewriter did not run this turn', () => {
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ citationRewriteEnabled: false }))
    expect(receipt.evidence_grades.status).toBe('unavailable')
    expect(receipt.evidence_grades.grade_counts).toBeNull()
    expect(receipt.evidence_grades.unavailable_reason).toContain('PARIPRASHNA_FIRST_PAINT_CITATIONS_ENABLED')
  })

  it('honest_gaps is unavailable when no completeness receipt exists', () => {
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ completenessReceipt: null }))
    expect(receipt.honest_gaps).toEqual({
      status: 'unavailable',
      gaps: null,
      unavailable_reason: 'no WebCompletenessReceipt was built this turn (registry compile fault)',
    })
  })

  it('safety_decision is unavailable when no SafetyDecision object was supplied', () => {
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ safetyDecision: undefined }))
    expect(receipt.safety_decision.status).toBe('unavailable')
    expect(receipt.safety_decision.enforced).toBeNull()
  })

  it('safety_decision is MEASURED (not unavailable) when enforced:false — that is a real, distinct fact', () => {
    const receipt = assembleAcharyaReadingReceipt(
      baseArgs({ safetyDecision: safetyDecisionFixture({ enforced: false }) }),
    )
    expect(receipt.safety_decision.status).toBe('measured')
    expect(receipt.safety_decision.enforced).toBe(false)
    expect(receipt.safety_decision.unavailable_reason).toBeNull()
  })

  it('calibration_disclosure is always measured (its detector always runs) and gives the honest structural-mode note when nothing was consulted', () => {
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ validToolResults: [] }))
    expect(receipt.calibration_disclosure.consulted).toBe(false)
    expect(receipt.calibration_disclosure.consulted_tool_names).toEqual([])
    expect(receipt.calibration_disclosure.disclosure_note).toContain('STRUCTURAL mode')
  })

  it('facts_consumed is an honest empty array (not null) when zero citations were detected', () => {
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ citationsFound: [] }))
    expect(receipt.facts_consumed).toEqual([])
  })
})

describe('assembleAcharyaReadingReceipt — schema coherence', () => {
  it('a fully-populated receipt satisfies AcharyaReadingReceiptSchema', () => {
    const receipt = assembleAcharyaReadingReceipt(
      baseArgs({
        completenessReceipt: completenessReceiptFixture(),
        citationRewriteEnabled: true,
        resolvedCitations: [{ index: 1, signal_id: 'SIG.MSR.001', layer: 'L2.5', snippet: 's', grade: 'primary' }],
        safetyDecision: safetyDecisionFixture(),
        validToolResults: [toolBundle('query_calibration')],
        committedBlocks: [{ id: 'blk-1-1', role: 'prose', text: 'hi' }],
      }),
    )
    expect(() => AcharyaReadingReceiptSchema.parse(receipt)).not.toThrow()
  })

  it('a minimal, all-unavailable receipt also satisfies AcharyaReadingReceiptSchema', () => {
    const receipt = assembleAcharyaReadingReceipt(baseArgs())
    expect(() => AcharyaReadingReceiptSchema.parse(receipt)).not.toThrow()
  })
})

/**
 * interpretation_sets — lane G3-B (PPR-02) additive extension. Proves the
 * new field traces to whatever the caller supplies, and that every
 * pre-existing caller (which supplies nothing) gets an honest, well-formed
 * `unavailable` default rather than an absent/undefined field.
 */
describe('assembleAcharyaReadingReceipt — interpretation_sets (G3-B)', () => {
  it('defaults to an honest unavailable field when the caller supplies nothing (every pre-G3-B call site)', () => {
    const receipt = assembleAcharyaReadingReceipt(baseArgs())
    expect(receipt.interpretation_sets).toEqual({
      status: 'unavailable',
      interpretation_sets_schema_version: null,
      detected_count: null,
      covered_count: null,
      truncated_count: null,
      waived_count: null,
      sets: null,
      unavailable_reason: expect.stringContaining('did not run this turn'),
    })
  })

  it('traces to exactly what the caller supplies (never re-derived)', () => {
    const supplied = {
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
          candidates: [
            { reading: 'A', rationale: 'ra' },
            { reading: 'B', rationale: 'rb' },
            { reading: 'C', rationale: 'rc' },
          ],
          selected_index: 0,
          selected_rationale: 'A fits best.',
          falsifier: 'If X, A is wrong.',
          waiver_reason: null,
        },
      ],
      unavailable_reason: null,
    }
    const receipt = assembleAcharyaReadingReceipt(baseArgs({ interpretationSets: supplied }))
    expect(receipt.interpretation_sets).toEqual(supplied)
  })

  it('is included in the hashed content — supplying a different value changes receipt_hash', () => {
    const withoutIt = assembleAcharyaReadingReceipt(baseArgs())
    const withIt = assembleAcharyaReadingReceipt(
      baseArgs({
        interpretationSets: {
          status: 'measured',
          interpretation_sets_schema_version: 2,
          detected_count: 0,
          covered_count: 0,
          truncated_count: 0,
          waived_count: 0,
          sets: [],
          unavailable_reason: null,
        },
      }),
    )
    expect(withIt.receipt_hash).not.toBe(withoutIt.receipt_hash)
  })
})

/**
 * pariprashna/corpus/__tests__/test_helpers.ts — shared fixture builders for
 * the corpus dimension tests. Not a fixture file itself (see `../fixtures.ts`
 * for the real 12) — this is realistic MOCK data shaped like a genuine
 * `AcharyaReadingReceipt`/`TurnMetricsSnapshot`/`TurnObservation`, the same
 * convention `receipt/__tests__/assemble.test.ts` uses for testing the
 * assembler this module builds on.
 */

import type { AcharyaReadingReceipt } from '@/lib/pariprashna/receipt/schema'
import type { TurnMetricsSnapshot } from '@/lib/pariprashna/observability/turn_metrics'
import { ZERO_USAGE } from '@/lib/llm/observability/types'
import { CORPUS_FIXTURES } from '../fixtures'
import type { CorpusFixture, TurnObservation } from '../types'

export function baseFixture(overrides: Partial<CorpusFixture> = {}): CorpusFixture {
  const factual = CORPUS_FIXTURES.find((f) => f.queryClass === 'factual')!
  return { ...factual, ...overrides }
}

export function baseReceipt(overrides: Partial<AcharyaReadingReceipt> = {}): AcharyaReadingReceipt {
  const receipt: AcharyaReadingReceipt = {
    receipt_schema_version: 1,
    turn_id: 'turn-test-001',
    conversation_id: 'conv-test-001',
    chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
    generated_at: '2026-08-20T00:00:00.000Z',
    coverage: {
      status: 'measured',
      served: 8,
      empty: 1,
      dark: 1,
      floor_item_total: 10,
      channel: 'web',
      channel_note: null,
      unavailable_reason: null,
    },
    facts_consumed: [
      { ref: 'SIG.MSR.413', layer: 'L2.5', index: 1 },
      { ref: 'SIG.MSR.391', layer: 'L2.5', index: 2 },
    ],
    derivation_chains: [
      { block_id: 'blk-1-1', pass_id: 1, role: 'prose', fact_refs: ['SIG.MSR.413'] },
      { block_id: 'blk-1-2', pass_id: 1, role: 'prose', fact_refs: ['SIG.MSR.391'] },
    ],
    cross_domain: { status: 'measured', domains: ['career', 'health'], unavailable_reason: null },
    evidence_grades: {
      status: 'measured',
      grade_counts: { primary: 2, supporting: 0, contextual: 0, unverified: 0, prior_reading: 0 },
      hallucination_count: 0,
      unavailable_reason: null,
    },
    honest_gaps: {
      status: 'measured',
      gaps: [{ floor_item_id: 'floor-1', kind: 'empty', reason: 'no data for this item' }],
      unavailable_reason: null,
    },
    safety_decision: {
      status: 'measured',
      decision_id: 'dec-001',
      enforced: false,
      severity: 'none',
      action: 'proceed',
      classes_detected: [],
      review_id: null,
      audit_written: false,
      unavailable_reason: null,
    },
    calibration_disclosure: {
      consulted: false,
      consulted_tool_names: [],
      disclosure_note: 'No L5 Mīmāṃsā calibration capability was consulted this turn.',
    },
    prose_binding: {
      blocks: [{ block_id: 'blk-1-1', role: 'prose', char_count: 120, semantic_kind: null, semantic_role: null }],
      accumulated_text_sha256: 'deadbeef',
      accumulated_char_count: 120,
    },
    provenance: {
      build_id: 'build-001',
      priors_version: 'v1',
      formula_versions: { salience_formula_ver: 'v1' },
      ranking_config: { mode: 'default' },
      now_context_date: '2026-08-20',
      computed_at: '2026-08-20T00:00:00.000Z',
    },
    // Lane G3-C (PPR-03) — always assembled, degrading to `unavailable`
    // (never omitted) when PARIPRASHNA_TYPED_CONFIDENCE_ENABLED is off, same
    // "unavailable, never omitted" convention as `evidence_grades`. Corpus
    // fixtures predate G3-C; default to the honest off-state here.
    confidence_typing: {
      status: 'unavailable',
      entries: null,
      activation_gate: null,
      precision_flags: null,
      unavailable_reason: 'typed confidence disabled',
    },
    receipt_hash: 'testhash',
  }
  return { ...receipt, ...overrides }
}

export function baseTurnMetrics(overrides: Partial<TurnMetricsSnapshot> = {}): TurnMetricsSnapshot {
  const snapshot: TurnMetricsSnapshot = {
    ttft_ms: 500,
    event_count: 10,
    events_by_type: { text_delta: 10 },
    max_event_gap_ms: 100,
    usage: { ...ZERO_USAGE },
    register_lint: { delta_calls: 10, fires: 0, leaks_total: 0 },
    delta_commit_lag_ms: { count: 2, total_ms: 200, max_ms: 150 },
    pass_count: 1,
  }
  return { ...snapshot, ...overrides }
}

export function baseObservation(overrides: Partial<TurnObservation> = {}): TurnObservation {
  return {
    fixture: baseFixture(),
    receipt: baseReceipt(),
    turnMetrics: baseTurnMetrics(),
    proseText: 'This is a hedged, honest reading that classically indicates a pattern.',
    ...overrides,
  }
}

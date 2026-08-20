/**
 * P2-close item 3 — the reducer half of the receipt wire event. Pins that
 * `receipt.define` writes the full receipt AND the `interpretationSets`
 * projection (G3-E's existing consumer reads that field specifically),
 * is idempotent under a replayed event id, and that an untouched turn
 * reports the honest absence (`null`), never a guessed value — same
 * discipline `reading_depth_received.test.ts` already established for the
 * sibling late-arriving wire event.
 */

import { describe, it, expect } from 'vitest'

import { threadReducer, initialThreadState } from './reducer'
import type { AcharyaReadingReceipt } from '@/lib/pariprashna/receipt/schema'
import type { ReceiptInterpretationSets } from '@/lib/pariprashna/interpretation/schema'

function submitted(turnId: string) {
  return threadReducer(initialThreadState, { type: 'CLIENT_SUBMIT_TURN', turnId, userText: 'q' })
}

const SAMPLE_INTERPRETATION_SETS: ReceiptInterpretationSets = {
  status: 'measured',
  interpretation_sets_schema_version: 2,
  detected_count: 1,
  covered_count: 1,
  truncated_count: 0,
  waived_count: 0,
  unavailable_reason: null,
  sets: [
    {
      judgment_id: 'sig-domain_verdict-1',
      category: 'domain_verdict',
      status: 'generated',
      detection_basis: "G2-A block role='verdict'",
      candidates: [
        { reading: 'A', rationale: 'ra' },
        { reading: 'B', rationale: 'rb' },
        { reading: 'C', rationale: 'rc' },
      ],
      selected_index: 0,
      selected_rationale: 'best',
      falsifier: 'a real falsifier with enough words',
      waiver_reason: null,
    },
  ],
}

/** Minimal but type-honest — only the fields this reducer case actually
 *  reads (`interpretation_sets`) are populated meaningfully; everything else
 *  is a structurally-valid placeholder, since the reducer's own job is
 *  pass-through storage, not receipt validation (the server already ran
 *  that, per events.ts's own ReceiptDefineEventSchema doc comment). */
function sampleReceipt(overrides: Partial<AcharyaReadingReceipt> = {}): AcharyaReadingReceipt {
  return {
    receipt_schema_version: 1,
    turn_id: 'turn-1',
    conversation_id: 'conv-1',
    chart_id: 'chart-1',
    generated_at: '2026-08-21T00:00:00.000Z',
    receipt_hash: 'deadbeef',
    coverage: { status: 'measured', served: 0, empty: 0, dark: 0, floor_item_total: 0, channel: 'web', channel_note: '', unavailable_reason: null },
    provenance: { build_id: 'b', computed_at: '2026-08-21T00:00:00.000Z', priors_version: '1', ranking_config: { mode: 'composite_v1' }, formula_versions: { salience_formula_ver: null }, now_context_date: '2026-08-21' },
    honest_gaps: { status: 'measured', gaps: [], unavailable_reason: null },
    cross_domain: { status: 'measured', domains: [], unavailable_reason: null },
    safety_decision: { status: 'measured', action: 'proceed', enforced: true, severity: 'none', review_id: null, decision_id: 'd', audit_written: true, classes_detected: [], unavailable_reason: null },
    evidence_grades: { status: 'measured', grade_counts: { primary: 0, contextual: 0, supporting: 0, unverified: 0, prior_reading: 0 }, hallucination_count: 0, unavailable_reason: null },
    prose_binding: { blocks: [], accumulated_char_count: 0, accumulated_text_sha256: '' },
    facts_consumed: [],
    derivation_chains: [],
    calibration_disclosure: { consulted: false, disclosure_note: '', consulted_tool_names: [] },
    confidence_typing: { status: 'measured', entries: [], activation_gate: { gate_note: '', gate_open: false, sample_size: null, min_sample_size_required: 30, threshold_is_placeholder: true }, precision_flags: [], unavailable_reason: null },
    interpretation_sets: SAMPLE_INTERPRETATION_SETS,
    ...overrides,
  } as AcharyaReadingReceipt
}

describe('receipt.define reducer case', () => {
  it('stores the full receipt on the matching turn', () => {
    const receipt = sampleReceipt()
    const state = threadReducer(submitted('t1'), {
      type: 'receipt.define',
      turnId: 't1',
      receipt,
      eventId: 't1-9',
    })
    expect(state.turns[0].receipt).toBe(receipt)
  })

  it('projects interpretation_sets onto interpretationSets for G3-Es existing consumer', () => {
    const receipt = sampleReceipt()
    const state = threadReducer(submitted('t1'), {
      type: 'receipt.define',
      turnId: 't1',
      receipt,
      eventId: 't1-9',
    })
    const interpretationSets = state.turns[0].interpretationSets
    expect(interpretationSets).toEqual(SAMPLE_INTERPRETATION_SETS)
    expect(interpretationSets?.sets?.[0]?.status).toBe('generated')
  })

  it('coalesces an absent interpretation_sets field to null, not undefined', () => {
    const receipt = sampleReceipt({ interpretation_sets: undefined })
    const state = threadReducer(submitted('t1'), {
      type: 'receipt.define',
      turnId: 't1',
      receipt,
      eventId: 't1-9',
    })
    expect(state.turns[0].interpretationSets).toBeNull()
  })

  it('a turn with no receipt.define event reports null, not a guess', () => {
    const state = submitted('t1')
    expect(state.turns[0].receipt).toBeNull()
    expect(state.turns[0].interpretationSets).toBeNull()
  })

  it('drops a duplicate event id (reconnect-safe dedup)', () => {
    const first = sampleReceipt({ turn_id: 'first' })
    const second = sampleReceipt({ turn_id: 'second' })
    const once = threadReducer(submitted('t1'), {
      type: 'receipt.define',
      turnId: 't1',
      receipt: first,
      eventId: 't1-9',
    })
    const replayed = threadReducer(once, {
      type: 'receipt.define',
      turnId: 't1',
      receipt: second,
      eventId: 't1-9',
    })
    expect(replayed.turns[0].receipt?.turn_id).toBe('first')
  })

  it('does not touch an unrelated turn', () => {
    let state = submitted('t1')
    state = threadReducer(state, { type: 'CLIENT_SUBMIT_TURN', turnId: 't2', userText: 'q2' })
    state = threadReducer(state, { type: 'receipt.define', turnId: 't1', receipt: sampleReceipt(), eventId: 't1-1' })
    const t2 = state.turns.find((t) => t.id === 't2')!
    expect(t2.receipt).toBeNull()
    expect(t2.interpretationSets).toBeNull()
  })
})

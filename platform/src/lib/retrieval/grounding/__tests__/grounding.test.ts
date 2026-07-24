/**
 * D3 Grounding Spine — Unit Tests
 * =================================
 * Tests the grounding resolver using in-memory stubs (no live DB).
 *
 * Test matrix:
 *   G1  — resolveSignals: happy path; signals resolved to L1 facts
 *   G2  — resolveSignals: missing chart_id → MISSING_CHART_ID error
 *   G3  — resolveSignals: empty signal_ids → EMPTY_SIGNAL_IDS error
 *   G4  — resolveSignals: orphan fact_id → §N.5 violation detected
 *   G5  — resolveSignals: signal not in DB → not_found_signal_ids populated
 *   G6  — resolveSignals: F1 dedupe — duplicate signal_ids resolved once
 *   G7  — resolveSignals: chart scope isolation — facts from another chart not returned
 *   G8  — resolveMetric: governed metric resolves from bodha_msr_signals
 *   G9  — resolveMetric: out-of-vocabulary metric → OUT_OF_VOCAB error (never fabricated)
 *   G10 — resolveMetric: missing chart_id → MISSING_CHART_ID error
 *   G11 — resolveMetric: signal not found → SIGNAL_NOT_FOUND error
 *   G12 — resolveMetric: fact_value_num metric resolves from chart_facts
 *   G13 — resolveMetric: fact not found → FACT_NOT_FOUND error
 *   G14 — assertNoN5Violations: clean result → empty violations
 *   G15 — assertNoN5Violations: orphan refs → N5_VIOLATION errors
 *   G16 — capability descriptors: chart-agnostic gate — no native ids, chart_id in required_inputs
 *   G17 — resolveSignals: l0_citation_refs extracted from classical_sources_jsonb
 *   G18 — resolveSignals: ayanamsha filter applied when provided
 *   G19 — GOVERNED_METRICS set contains all expected metrics
 *   G20 — citation_human sanitization: GAP-ticket + fact_id substring stripped at construction
 */

import { describe, it, expect } from 'vitest'
import { makeStubDbProxy } from '../db_proxy'
import { resolveSignals, resolveMetric, assertNoN5Violations } from '../resolver'
import { GOVERNED_METRICS } from '../types'
import { resolveSignalsCapability, resolveMetricCapability } from '../capability'
import { checkCapability } from '../../registry/chart_agnostic_gate'

// ── Fixture data ──────────────────────────────────────────────────────────────

const CHART_ID_A = '482012f1-710e-4a25-994a-93821f5871aa'
const CHART_ID_B = 'bbbbbbbb-0000-0000-0000-000000000000'

const SIGNAL_ID_1 = 'aaaaaaaa-0000-0000-0000-000000000001'
const SIGNAL_ID_2 = 'aaaaaaaa-0000-0000-0000-000000000002'
const SIGNAL_ID_3 = 'aaaaaaaa-0000-0000-0000-000000000003'

const FACT_ID_1 = 'factid0000000001'
const FACT_ID_2 = 'factid0000000002'
const FACT_ID_3_ORPHAN = 'factid000orphan3'  // exists in signal but NOT in chart_facts

const MSR_SIGNAL_1 = {
  signal_id: SIGNAL_ID_1,
  chart_id: CHART_ID_A,
  ayanamsha_id: 'LAHIRI',
  signal_type_id: 'yoga_hamsa',
  signal_type_class: 'yoga',
  signal_summary_text: 'Hamsa yoga active in chart.',
  computed_salience: 0.87,
  constituent_facts_array: [FACT_ID_1, FACT_ID_2],
  classical_sources_jsonb: {
    catalog_ids: ['cat001', 'cat002'],
    rule_ids: ['rule_hamsa'],
    text_chunk_ids: [],
    citations: ['BPHS-ch12-v5'],
  },
}

const MSR_SIGNAL_2 = {
  signal_id: SIGNAL_ID_2,
  chart_id: CHART_ID_A,
  ayanamsha_id: 'LAHIRI',
  signal_type_id: 'dosha_mangal',
  signal_type_class: 'dosha',
  signal_summary_text: 'Mangal dosha present.',
  computed_salience: 0.65,
  constituent_facts_array: [FACT_ID_1],
  classical_sources_jsonb: null,
}

// Signal with an orphan fact_id (§N.5 violation case)
const MSR_SIGNAL_ORPHAN = {
  signal_id: SIGNAL_ID_3,
  chart_id: CHART_ID_A,
  ayanamsha_id: 'LAHIRI',
  signal_type_id: 'yoga_unknown',
  signal_type_class: 'yoga',
  signal_summary_text: 'Signal with orphan fact reference.',
  computed_salience: 0.5,
  constituent_facts_array: [FACT_ID_1, FACT_ID_3_ORPHAN],
  classical_sources_jsonb: null,
}

const CHART_FACT_1 = {
  fact_id: FACT_ID_1,
  chart_id: CHART_ID_A,
  ayanamsha_id: 'LAHIRI',
  fact_category: 'graha_position',
  fact_subject: 'JUPITER',
  fact_key: 'rashi',
  fact_value_text: 'Cancer',
  fact_value_num: null,
  fact_value_jsonb: null,
  unit: null,
  citation_ref: 'graha_position.JUPITER.rashi@chart=482012f1...',
  citation_human: 'Jupiter in Cancer (LAHIRI).',
  source_calculation: 'pyjhora/1.0.0',
  verification_pass_status: 'PASS',
  computed_salience: null,  // not a signal field but included for completeness
}

const CHART_FACT_2 = {
  fact_id: FACT_ID_2,
  chart_id: CHART_ID_A,
  ayanamsha_id: 'LAHIRI',
  fact_category: 'graha_position',
  fact_subject: 'JUPITER',
  fact_key: 'longitude_deg',
  fact_value_text: null,
  fact_value_num: 103.25,
  fact_value_jsonb: null,
  unit: 'deg',
  citation_ref: 'graha_position.JUPITER.longitude_deg@chart=482012f1...',
  citation_human: 'Jupiter at 103.25° (LAHIRI).',
  source_calculation: 'pyjhora/1.0.0',
  verification_pass_status: 'PASS',
  computed_salience: null,
}

// ── G1 — Happy path ───────────────────────────────────────────────────────────

describe('G1: resolveSignals — happy path', () => {
  it('resolves signal_ids to their L1 facts', async () => {
    const db = makeStubDbProxy({
      bodha_msr_signals: [MSR_SIGNAL_1, MSR_SIGNAL_2],
      chart_facts: [CHART_FACT_1, CHART_FACT_2],
    })

    const outcome = await resolveSignals(db, CHART_ID_A, [SIGNAL_ID_1])
    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return

    const { result } = outcome
    expect(result.chart_id).toBe(CHART_ID_A)
    expect(result.signals).toHaveLength(1)

    const sig = result.signals[0]
    expect(sig.signal_id).toBe(SIGNAL_ID_1)
    expect(sig.constituent_fact_ids).toEqual([FACT_ID_1, FACT_ID_2])
    expect(sig.resolved_facts).toHaveLength(2)
    expect(sig.orphan_fact_ids).toHaveLength(0)
    expect(result.has_n5_violations).toBe(false)
    expect(result.orphan_fact_count).toBe(0)
  })

  it('returns correct fact values (not regenerated)', async () => {
    const db = makeStubDbProxy({
      bodha_msr_signals: [MSR_SIGNAL_1],
      chart_facts: [CHART_FACT_1, CHART_FACT_2],
    })

    const outcome = await resolveSignals(db, CHART_ID_A, [SIGNAL_ID_1])
    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return

    const facts = outcome.result.signals[0].resolved_facts
    const jupRashi = facts.find(f => f.fact_key === 'rashi')
    expect(jupRashi?.fact_value_text).toBe('Cancer')
    expect(jupRashi?.fact_value_num).toBeNull()

    const jupDeg = facts.find(f => f.fact_key === 'longitude_deg')
    expect(jupDeg?.fact_value_num).toBe(103.25)
    expect(jupDeg?.unit).toBe('deg')
  })
})

// ── G2 — Missing chart_id ─────────────────────────────────────────────────────

describe('G2: resolveSignals — missing chart_id', () => {
  it('returns MISSING_CHART_ID error when chart_id is empty string', async () => {
    const db = makeStubDbProxy({})
    const outcome = await resolveSignals(db, '', [SIGNAL_ID_1])
    expect(outcome.ok).toBe(false)
    if (outcome.ok) return
    expect(outcome.error.error_code).toBe('MISSING_CHART_ID')
  })

  it('returns MISSING_CHART_ID error when chart_id is whitespace', async () => {
    const db = makeStubDbProxy({})
    const outcome = await resolveSignals(db, '   ', [SIGNAL_ID_1])
    expect(outcome.ok).toBe(false)
    if (outcome.ok) return
    expect(outcome.error.error_code).toBe('MISSING_CHART_ID')
  })
})

// ── G3 — Empty signal_ids ─────────────────────────────────────────────────────

describe('G3: resolveSignals — empty signal_ids', () => {
  it('returns EMPTY_SIGNAL_IDS error when signal_ids is empty array', async () => {
    const db = makeStubDbProxy({})
    const outcome = await resolveSignals(db, CHART_ID_A, [])
    expect(outcome.ok).toBe(false)
    if (outcome.ok) return
    expect(outcome.error.error_code).toBe('EMPTY_SIGNAL_IDS')
  })
})

// ── G4 — §N.5 violation: orphan fact_id ──────────────────────────────────────

describe('G4: resolveSignals — §N.5 orphan fact detection', () => {
  it('detects orphan fact_ids (§N.5 violations)', async () => {
    const db = makeStubDbProxy({
      bodha_msr_signals: [MSR_SIGNAL_ORPHAN],
      chart_facts: [CHART_FACT_1],  // FACT_ID_3_ORPHAN is NOT here
    })

    const outcome = await resolveSignals(db, CHART_ID_A, [SIGNAL_ID_3])
    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return

    const { result } = outcome
    expect(result.has_n5_violations).toBe(true)
    expect(result.orphan_fact_count).toBe(1)

    const sig = result.signals[0]
    expect(sig.orphan_fact_ids).toContain(FACT_ID_3_ORPHAN)
    expect(sig.resolved_facts).toHaveLength(1)  // only FACT_ID_1 resolved
    expect(sig.resolved_facts[0].fact_id).toBe(FACT_ID_1)
  })

  it('assertNoN5Violations returns N5_VIOLATION errors for orphan refs', async () => {
    const db = makeStubDbProxy({
      bodha_msr_signals: [MSR_SIGNAL_ORPHAN],
      chart_facts: [CHART_FACT_1],
    })

    const outcome = await resolveSignals(db, CHART_ID_A, [SIGNAL_ID_3])
    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return

    const violations = assertNoN5Violations(outcome.result)
    expect(violations).toHaveLength(1)
    expect(violations[0].error_code).toBe('N5_VIOLATION')
    expect(violations[0].signal_id).toBe(SIGNAL_ID_3)
    expect(violations[0].fact_id).toBe(FACT_ID_3_ORPHAN)
    expect(violations[0].message).toContain('§N.5')
  })
})

// ── G5 — Signal not found ─────────────────────────────────────────────────────

describe('G5: resolveSignals — signal not in DB', () => {
  it('populates not_found_signal_ids when signal_id is absent', async () => {
    const db = makeStubDbProxy({
      bodha_msr_signals: [],  // empty
      chart_facts: [],
    })

    const outcome = await resolveSignals(db, CHART_ID_A, [SIGNAL_ID_1])
    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return

    expect(outcome.result.signals).toHaveLength(0)
    expect(outcome.result.not_found_signal_ids).toContain(SIGNAL_ID_1)
  })
})

// ── G6 — F1 deduplication ─────────────────────────────────────────────────────

describe('G6: resolveSignals — F1 deduplicate signal_ids', () => {
  it('resolves each signal_id exactly once even when duplicated in input', async () => {
    const db = makeStubDbProxy({
      bodha_msr_signals: [MSR_SIGNAL_1],
      chart_facts: [CHART_FACT_1, CHART_FACT_2],
    })

    const outcome = await resolveSignals(
      db,
      CHART_ID_A,
      [SIGNAL_ID_1, SIGNAL_ID_1, SIGNAL_ID_1]  // same id 3 times
    )
    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return

    // Should return exactly one signal, not three
    expect(outcome.result.signals).toHaveLength(1)
    expect(outcome.result.signals[0].signal_id).toBe(SIGNAL_ID_1)
  })
})

// ── G7 — Chart scope isolation ────────────────────────────────────────────────

describe('G7: resolveSignals — chart scope isolation', () => {
  it('does not return facts belonging to a different chart', async () => {
    // CHART_FACT_1 belongs to CHART_ID_A; we request for CHART_ID_B
    const factForB = {
      ...CHART_FACT_1,
      chart_id: CHART_ID_B,
      fact_id: 'factid000chart0b',
    }
    const signalForB = {
      ...MSR_SIGNAL_1,
      signal_id: 'bbbbbbbb-0000-0000-0000-000000000001',
      chart_id: CHART_ID_B,
      constituent_facts_array: ['factid000chart0b'],
    }

    const db = makeStubDbProxy({
      bodha_msr_signals: [signalForB],
      chart_facts: [CHART_FACT_1, factForB],  // both charts' facts
    })

    const outcome = await resolveSignals(
      db,
      CHART_ID_B,
      ['bbbbbbbb-0000-0000-0000-000000000001']
    )
    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return

    const resolvedFacts = outcome.result.signals[0]?.resolved_facts ?? []
    // Only CHART_ID_B facts should appear — CHART_ID_A fact must be excluded
    for (const f of resolvedFacts) {
      expect(f.chart_id).toBe(CHART_ID_B)
    }
  })
})

// ── G8 — Governed metric: signal field ───────────────────────────────────────

describe('G8: resolveMetric — governed metric from bodha_msr_signals', () => {
  it('resolves computed_salience for a signal', async () => {
    const db = makeStubDbProxy({
      bodha_msr_signals: [{
        signal_id: SIGNAL_ID_1,
        chart_id: CHART_ID_A,
        computed_salience: 0.87,
        citation_human: 'Hamsa yoga salience 0.87.',
      }],
    })

    const outcome = await resolveMetric(db, CHART_ID_A, 'computed_salience', SIGNAL_ID_1)
    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return

    expect(outcome.metric.metric).toBe('computed_salience')
    expect(outcome.metric.value).toBe(0.87)
    expect(outcome.metric.source_table).toBe('bodha_msr_signals')
    expect(outcome.metric.source_id).toBe(SIGNAL_ID_1)
    expect(outcome.metric.citation).toBeTruthy()
  })
})

// ── G9 — Out-of-vocabulary metric (principle #3) ─────────────────────────────

describe('G9: resolveMetric — out-of-vocabulary metric → OUT_OF_VOCAB error', () => {
  it('rejects an out-of-vocabulary metric with OUT_OF_VOCAB error', async () => {
    const db = makeStubDbProxy({ bodha_msr_signals: [MSR_SIGNAL_1] })

    const outcome = await resolveMetric(
      db,
      CHART_ID_A,
      'some_made_up_metric',  // NOT in GOVERNED_METRICS
      SIGNAL_ID_1
    )

    expect(outcome.ok).toBe(false)
    if (outcome.ok) return
    expect(outcome.error.error_code).toBe('OUT_OF_VOCAB')
    expect(outcome.error.requested_metric).toBe('some_made_up_metric')
    expect(outcome.error.message).toContain('governed metric vocabulary')
  })

  it('rejects SQL injection-style metric names', async () => {
    const db = makeStubDbProxy({ bodha_msr_signals: [MSR_SIGNAL_1] })

    const outcome = await resolveMetric(
      db,
      CHART_ID_A,
      'computed_salience; DROP TABLE bodha_msr_signals',
      SIGNAL_ID_1
    )

    expect(outcome.ok).toBe(false)
    if (outcome.ok) return
    expect(outcome.error.error_code).toBe('OUT_OF_VOCAB')
  })
})

// ── G10 — Missing chart_id in resolveMetric ───────────────────────────────────

describe('G10: resolveMetric — missing chart_id', () => {
  it('returns MISSING_CHART_ID when chart_id is empty', async () => {
    const db = makeStubDbProxy({})
    const outcome = await resolveMetric(db, '', 'computed_salience', SIGNAL_ID_1)
    expect(outcome.ok).toBe(false)
    if (outcome.ok) return
    expect(outcome.error.error_code).toBe('MISSING_CHART_ID')
  })
})

// ── G11 — Signal not found in resolveMetric ───────────────────────────────────

describe('G11: resolveMetric — signal not found', () => {
  it('returns SIGNAL_NOT_FOUND when signal_id is absent from DB', async () => {
    const db = makeStubDbProxy({ bodha_msr_signals: [] })
    const outcome = await resolveMetric(db, CHART_ID_A, 'computed_salience', SIGNAL_ID_1)
    expect(outcome.ok).toBe(false)
    if (outcome.ok) return
    expect(outcome.error.error_code).toBe('SIGNAL_NOT_FOUND')
    expect(outcome.error.signal_id).toBe(SIGNAL_ID_1)
  })
})

// ── G12 — fact_value_num from chart_facts ────────────────────────────────────

describe('G12: resolveMetric — fact_value_num from chart_facts', () => {
  it('resolves fact_value_num from chart_facts for a given fact_id', async () => {
    const db = makeStubDbProxy({
      chart_facts: [{
        fact_id: FACT_ID_2,
        chart_id: CHART_ID_A,
        fact_value_num: 103.25,
        citation_human: 'Jupiter at 103.25°.',
      }],
    })

    const outcome = await resolveMetric(db, CHART_ID_A, 'fact_value_num', FACT_ID_2)
    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return
    expect(outcome.metric.metric).toBe('fact_value_num')
    expect(outcome.metric.value).toBe(103.25)
    expect(outcome.metric.source_table).toBe('chart_facts')
    expect(outcome.metric.source_id).toBe(FACT_ID_2)
  })
})

// ── G13 — Fact not found in chart_facts ──────────────────────────────────────

describe('G13: resolveMetric — fact not found', () => {
  it('returns FACT_NOT_FOUND when fact_id is absent from chart_facts', async () => {
    const db = makeStubDbProxy({ chart_facts: [] })
    const outcome = await resolveMetric(db, CHART_ID_A, 'fact_value_num', 'nonexistentfact')
    expect(outcome.ok).toBe(false)
    if (outcome.ok) return
    expect(outcome.error.error_code).toBe('FACT_NOT_FOUND')
  })
})

// ── G14 — assertNoN5Violations: clean result ─────────────────────────────────

describe('G14: assertNoN5Violations — clean result', () => {
  it('returns empty violations array for a clean GroundedResult', async () => {
    const db = makeStubDbProxy({
      bodha_msr_signals: [MSR_SIGNAL_1, MSR_SIGNAL_2],
      chart_facts: [CHART_FACT_1, CHART_FACT_2],
    })

    const outcome = await resolveSignals(db, CHART_ID_A, [SIGNAL_ID_1, SIGNAL_ID_2])
    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return

    const violations = assertNoN5Violations(outcome.result)
    expect(violations).toHaveLength(0)
  })
})

// ── G15 — assertNoN5Violations: orphan refs ───────────────────────────────────

describe('G15: assertNoN5Violations — multiple orphan refs', () => {
  it('returns one N5_VIOLATION per orphan reference', async () => {
    const signalTwoOrphans = {
      ...MSR_SIGNAL_ORPHAN,
      constituent_facts_array: [FACT_ID_3_ORPHAN, 'factid000orphan4'],
    }
    const db = makeStubDbProxy({
      bodha_msr_signals: [signalTwoOrphans],
      chart_facts: [],  // no facts resolve
    })

    const outcome = await resolveSignals(db, CHART_ID_A, [SIGNAL_ID_3])
    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return

    const violations = assertNoN5Violations(outcome.result)
    expect(violations).toHaveLength(2)
    expect(violations.every(v => v.error_code === 'N5_VIOLATION')).toBe(true)
  })
})

// ── G16 — Capability descriptors: chart-agnostic gate ────────────────────────

describe('G16: capability descriptors — chart-agnostic gate compliance', () => {
  it('resolveSignalsCapability passes the chart-agnostic gate', () => {
    const violations = checkCapability(resolveSignalsCapability)
    expect(violations).toHaveLength(0)
  })

  it('resolveMetricCapability passes the chart-agnostic gate', () => {
    const violations = checkCapability(resolveMetricCapability)
    expect(violations).toHaveLength(0)
  })

  it('resolveSignalsCapability has chart_id in required_inputs', () => {
    expect(resolveSignalsCapability.required_inputs).toContain('chart_id')
  })

  it('resolveMetricCapability has chart_id in required_inputs', () => {
    expect(resolveMetricCapability.required_inputs).toContain('chart_id')
  })

  it('capabilities have emits_references=true (F1 reference-don\'t-repeat)', () => {
    expect(resolveSignalsCapability.emits_references).toBe(true)
    expect(resolveMetricCapability.emits_references).toBe(true)
  })

  it('resolveSignalsCapability has grounds_to.l1_fact_ids=true (F3)', () => {
    expect(resolveSignalsCapability.grounds_to?.l1_fact_ids).toBe(true)
  })

  it('capabilities descriptions contain no native identifiers', () => {
    const nativeId = '482012f1-710e-4a25-994a-93821f5871aa'
    expect(resolveSignalsCapability.description).not.toContain(nativeId)
    expect(resolveMetricCapability.description).not.toContain(nativeId)
    expect(resolveSignalsCapability.description).not.toContain('Abhisek Mohanty')
    expect(resolveMetricCapability.description).not.toContain('Abhisek Mohanty')
  })
})

// ── G17 — L0 citation ref extraction ─────────────────────────────────────────

describe('G17: resolveSignals — l0_citation_refs from classical_sources_jsonb', () => {
  it('extracts catalog_ids, rule_ids, citations from classical_sources_jsonb', async () => {
    const db = makeStubDbProxy({
      bodha_msr_signals: [MSR_SIGNAL_1],
      chart_facts: [CHART_FACT_1, CHART_FACT_2],
    })

    const outcome = await resolveSignals(db, CHART_ID_A, [SIGNAL_ID_1])
    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return

    const l0Refs = outcome.result.signals[0].l0_citation_refs
    expect(l0Refs).toContain('cat001')
    expect(l0Refs).toContain('cat002')
    expect(l0Refs).toContain('rule_hamsa')
    expect(l0Refs).toContain('BPHS-ch12-v5')
  })

  it('returns empty l0_citation_refs when classical_sources_jsonb is null', async () => {
    const db = makeStubDbProxy({
      bodha_msr_signals: [MSR_SIGNAL_2],  // has null classical_sources_jsonb
      chart_facts: [CHART_FACT_1],
    })

    const outcome = await resolveSignals(db, CHART_ID_A, [SIGNAL_ID_2])
    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return

    expect(outcome.result.signals[0].l0_citation_refs).toEqual([])
  })
})

// ── G18 — Ayanamsha filter ────────────────────────────────────────────────────

describe('G18: resolveSignals — ayanamsha_id filter', () => {
  it('filters out signals with non-matching ayanamsha when filter provided', async () => {
    const db = makeStubDbProxy({
      bodha_msr_signals: [MSR_SIGNAL_1],  // ayanamsha_id = 'LAHIRI'
      chart_facts: [CHART_FACT_1, CHART_FACT_2],
    })

    // Request with ayanamsha_id that does NOT match
    const outcome = await resolveSignals(db, CHART_ID_A, [SIGNAL_ID_1], 'KRISHNAMURTI')
    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return

    expect(outcome.result.signals).toHaveLength(0)
    expect(outcome.result.not_found_signal_ids).toContain(SIGNAL_ID_1)
  })

  it('passes signals with matching ayanamsha when filter provided', async () => {
    const db = makeStubDbProxy({
      bodha_msr_signals: [MSR_SIGNAL_1],  // ayanamsha_id = 'LAHIRI'
      chart_facts: [CHART_FACT_1, CHART_FACT_2],
    })

    const outcome = await resolveSignals(db, CHART_ID_A, [SIGNAL_ID_1], 'LAHIRI')
    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return

    expect(outcome.result.signals).toHaveLength(1)
  })
})

// ── G19 — GOVERNED_METRICS set contents ──────────────────────────────────────

describe('G19: GOVERNED_METRICS vocabulary', () => {
  it('contains all expected governed metrics', () => {
    const expected = [
      'computed_salience', 'dignity_score', 'shadbala_norm',
      'deterministic_strength', 'orb_tightness', 'top_k_salience_rank',
      'verification_certainty', 'house_weight_multiplier',
      'ashtakavarga_support_multiplier', 'vargottama_amplification',
      'argala_modifier', 'neechabhanga_modifier',
      'cross_ayanamsha_consistency_score', 'fact_value_num',
    ]
    for (const m of expected) {
      expect(GOVERNED_METRICS.has(m as import('../types').GovernedMetric)).toBe(true)
    }
  })

  it('does not contain any unknown or out-of-schema metrics', () => {
    expect(GOVERNED_METRICS.has('some_random_field' as import('../types').GovernedMetric)).toBe(false)
  })
})

// ── G20 — citation_human GAP-ticket/fact_id stripping ────────────────────────

const FACT_ID_GAP = 'factid00000gap01'
const RAW_CITATION_WITH_GAP_TICKET =
  'Saturn nak-lord chain length=7 (cycle@6) in lahiri_chitrapaksha. ' +
  'GAP-4: L1 nakshatra_lord fact_id=16ff3dbbc4bc15b5 (graha_nakshatra_join).'
const EXPECTED_CLEAN_CITATION =
  'Saturn nak-lord chain length=7 (cycle@6) in lahiri_chitrapaksha.'

describe('G20: citation_human — GAP-ticket + fact_id substring stripped at construction', () => {
  it('strips the internal GAP-ticket/fact_id annotation from resolveSignals resolved_facts', async () => {
    const signal = {
      ...MSR_SIGNAL_2,
      signal_id: 'aaaaaaaa-0000-0000-0000-0000000000gp',
      constituent_facts_array: [FACT_ID_GAP],
    }
    const fact = {
      ...CHART_FACT_1,
      fact_id: FACT_ID_GAP,
      citation_human: RAW_CITATION_WITH_GAP_TICKET,
    }
    const db = makeStubDbProxy({
      bodha_msr_signals: [signal],
      chart_facts: [fact],
    })

    const outcome = await resolveSignals(db, CHART_ID_A, [signal.signal_id])
    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return

    const resolved = outcome.result.signals[0].resolved_facts[0]
    expect(resolved.citation_human).toBe(EXPECTED_CLEAN_CITATION)
    expect(resolved.citation_human).not.toMatch(/GAP-\d+/)
    expect(resolved.citation_human).not.toMatch(/fact_id=/)
    // citation_ref (the machine-readable field) and fact_id remain untouched —
    // the linkage still has a proper home, it's just not duplicated into the
    // human-readable string.
    expect(resolved.fact_id).toBe(FACT_ID_GAP)
    expect(resolved.citation_ref).toBe(CHART_FACT_1.citation_ref)
  })

  it('strips the internal GAP-ticket/fact_id annotation from resolveMetric (fact_value_num)', async () => {
    const db = makeStubDbProxy({
      chart_facts: [{
        fact_id: FACT_ID_GAP,
        chart_id: CHART_ID_A,
        fact_value_num: 7,
        citation_human: RAW_CITATION_WITH_GAP_TICKET,
      }],
    })

    const outcome = await resolveMetric(db, CHART_ID_A, 'fact_value_num', FACT_ID_GAP)
    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return
    expect(outcome.metric.citation).toBe(EXPECTED_CLEAN_CITATION)
    expect(outcome.metric.citation).not.toMatch(/GAP-\d+/)
  })

  it('is a no-op on citation_human strings that carry no GAP-ticket annotation', async () => {
    const db = makeStubDbProxy({
      bodha_msr_signals: [MSR_SIGNAL_1, MSR_SIGNAL_2],
      chart_facts: [CHART_FACT_1, CHART_FACT_2],
    })

    const outcome = await resolveSignals(db, CHART_ID_A, [SIGNAL_ID_1])
    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return

    const facts = outcome.result.signals[0].resolved_facts
    const jupRashi = facts.find(f => f.fact_key === 'rashi')
    expect(jupRashi?.citation_human).toBe('Jupiter in Cancer (LAHIRI).')
  })
})

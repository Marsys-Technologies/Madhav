import { describe, expect, it } from 'vitest'
import { z } from 'zod'

import { estimateBytes } from '../../lib/response_budget.js'
import { finalizeKalaRitualResponseBudget, KalaRitualInputShape } from './ritual.js'

const LARGE = 'cited detail '.repeat(1_200)

function patternResponse() {
  const candidateIds = Array.from({ length: 24 }, (_, index) => `candidate-${index}`)
  return {
    tool: 'kala_ritual_get',
    wrong_view: false,
    mode: 'pattern_search',
    composed_text: 'A concise ritual reading survives the budget pass.',
    pattern_search: {
      candidates: candidateIds.map((id) => ({ id, precision_basis: LARGE })),
      gap_report: {
        statement: 'The candidate count remains an honest statement about the full evaluated set.',
        constraints_evaluated: [],
        next_occurrence: null,
        next_occurrence_state: 'not_within_scan_ceiling',
        scan_ceiling_utc: null,
        census: {
          statement: 'The census summary remains even when the exhaustive evidence rows are trimmed.',
          factor_families_evaluated: [],
          factors_not_computed: Array.from({ length: 36 }, (_, index) => ({ factor_name: `not-computed-${index}`, reason: LARGE })),
          factors_not_in_corpus: Array.from({ length: 36 }, (_, index) => ({ factor_name: `not-in-corpus-${index}`, reason: LARGE })),
          census_disposition_counts: { not_computed: 36, not_in_corpus: 36 },
          census_state: 'honest_empty',
          parihara_corpus_gap: null,
          next_occurrence: null,
        },
      },
      coverage: [],
      precision: { regime: 'intra_day', basis: 'fixture', no_degrading_constraint_kinds_present: true },
      adjudication: {
        ledgers: candidateIds.map((candidate_id) => ({ candidate_id, adjudication_note: LARGE })),
        pareto: {
          frontier_candidate_ids: candidateIds.slice(0, 12),
          dominated_candidate_ids: candidateIds.slice(12),
          axes_used: [],
          axes_excluded: [],
          method_note: LARGE,
        },
        gap_report: { factors_not_computed: [], factors_not_in_corpus: [] },
        coverage_state: 'computed',
        coverage_reason: null,
        density: {},
      },
      paddhati: null,
    },
    opportunities: null,
    paddhati_divergence: null,
  }
}

function opportunityResponse() {
  return {
    tool: 'kala_ritual_get',
    wrong_view: false,
    mode: 'opportunity_scan',
    composed_text: 'A concise ritual reading survives the budget pass.',
    pattern_search: null,
    opportunities: {
      opportunities: Array.from({ length: 24 }, (_, index) => ({ window: `window-${index}`, score_vector: { reason: LARGE } })),
      activity_rules: { rows: Array.from({ length: 30 }, (_, index) => ({ id: index, source_citation: LARGE })) },
      structural: {
        remedy_rows: Array.from({ length: 30 }, (_, index) => ({ remedy_id: index, citation: LARGE })),
        resonance_rows: Array.from({ length: 30 }, (_, index) => ({ graha: `graha-${index}`, note: LARGE })),
      },
    },
    paddhati_divergence: null,
  }
}

describe('F13 kala_ritual_get response budget', () => {
  it('declares a bounded caller-facing budget control', () => {
    const input = z.object(KalaRitualInputShape)
    expect(input.safeParse({ chart_id: '482012f1-710e-4a25-994a-93821f5871aa', budget_kb: 200 }).success).toBe(true)
    expect(input.safeParse({ chart_id: '482012f1-710e-4a25-994a-93821f5871aa', budget_kb: 201 }).success).toBe(false)
  })

  it('bounds Mode 2 census/candidates while retaining only internally referential candidate evidence', () => {
    const response = patternResponse()
    expect(estimateBytes(response)).toBeGreaterThan(40 * 1024)

    const bounded = finalizeKalaRitualResponseBudget(response as never)
    expect(estimateBytes(bounded)).toBeLessThanOrEqual(40 * 1024)
    expect(Buffer.byteLength(JSON.stringify(bounded))).toBeLessThanOrEqual(40 * 1024)
    expect(bounded.budget_kb_applied).toBe(40)
    expect(bounded.budget_kb_requested).toBeUndefined()
    expect(bounded.trim_report).not.toBeNull()

    const candidateIds = bounded.pattern_search!.candidates.map((candidate) => candidate.id).sort()
    const ledgerCandidateIds = bounded.pattern_search!.adjudication!.ledgers
      .map((ledger) => ledger.candidate_id)
      .sort()
    const paretoCandidateIds = [
      ...bounded.pattern_search!.adjudication!.pareto.frontier_candidate_ids,
      ...bounded.pattern_search!.adjudication!.pareto.dominated_candidate_ids,
    ].sort()

    expect(bounded.pattern_search!.candidates.length).toBeGreaterThan(0)
    expect(ledgerCandidateIds).not.toHaveLength(0)
    expect(ledgerCandidateIds).toEqual(candidateIds)
    expect(paretoCandidateIds).not.toHaveLength(0)
    expect(paretoCandidateIds).toEqual(candidateIds)
    const candidateEvidenceTrim = bounded.trim_report!.find(
      (entry) => entry.path === 'pattern_search.candidate_evidence',
    )
    const notComputedTrim = bounded.trim_report!.find(
      (entry) => entry.path === 'pattern_search.gap_report.census.factors_not_computed',
    )
    const notInCorpusTrim = bounded.trim_report!.find(
      (entry) => entry.path === 'pattern_search.gap_report.census.factors_not_in_corpus',
    )
    expect(bounded.trim_report!.map((entry) => entry.path).sort()).toEqual([
      'pattern_search.candidate_evidence',
      'pattern_search.gap_report.census.factors_not_computed',
      'pattern_search.gap_report.census.factors_not_in_corpus',
    ])
    expect(candidateEvidenceTrim).toBeDefined()
    expect(candidateEvidenceTrim!.original_count).toBe(24)
    expect(candidateEvidenceTrim!.kept_count).toBe(candidateIds.length)
    expect(candidateEvidenceTrim!.recover_via.instrument).toBe('kala_ritual_get')
    expect(candidateEvidenceTrim!.recover_via.hint).toContain('sky_pattern_spec')
    expect(candidateEvidenceTrim!.recover_via.hint).toContain('horizon')
    expect(candidateEvidenceTrim!.recover_via.hint).toContain('candidate')
    expect(candidateEvidenceTrim!.recover_via.hint).not.toContain('census')
    expect(notComputedTrim).toBeDefined()
    expect(notComputedTrim!.original_count).toBe(36)
    expect(notComputedTrim!.kept_count).toBe(0)
    expect(bounded.pattern_search!.gap_report.census.factors_not_computed).toHaveLength(0)
    expect(notComputedTrim!.recover_via.instrument).toBe('kala_ritual_get')
    expect(notComputedTrim!.recover_via.hint).toContain('census')
    expect(notComputedTrim!.recover_via.hint).not.toContain('candidate')
    expect(notInCorpusTrim).toBeDefined()
    expect(notInCorpusTrim!.original_count).toBe(36)
    expect(notInCorpusTrim!.kept_count).toBe(0)
    expect(bounded.pattern_search!.gap_report.census.factors_not_in_corpus).toHaveLength(0)
    expect(notInCorpusTrim!.recover_via.instrument).toBe('kala_ritual_get')
    expect(notInCorpusTrim!.recover_via.hint).toContain('census')
    expect(notInCorpusTrim!.recover_via.hint).not.toContain('candidate')
    const drillPointers = (bounded as typeof bounded & {
      drill_pointers?: Array<{ instrument: string | null; hint: string }>
    }).drill_pointers ?? []
    for (const entry of bounded.trim_report!) {
      expect(drillPointers).toContainEqual(entry.recover_via)
    }
    expect(bounded.pattern_search!.gap_report.census.census_disposition_counts).toEqual({ not_computed: 36, not_in_corpus: 36 })
  })

  it('does not report or point to untouched empty census siblings', () => {
    const response = patternResponse()
    response.pattern_search.gap_report.census.factors_not_computed = []
    response.pattern_search.gap_report.census.factors_not_in_corpus = []
    response.pattern_search.gap_report.census.census_disposition_counts = { not_computed: 0, not_in_corpus: 0 }

    const bounded = finalizeKalaRitualResponseBudget(response as never)
    expect(estimateBytes(bounded)).toBeLessThanOrEqual(40 * 1024)
    expect(bounded.trim_report!.map((entry) => entry.path)).toEqual([
      'pattern_search.candidate_evidence',
    ])
    expect(bounded.trim_report![0]!.original_count).toBe(24)
    expect(bounded.trim_report![0]!.kept_count).toBe(bounded.pattern_search!.candidates.length)
    expect(bounded.trim_report![0]!.reason).not.toContain('census')
    expect(bounded.trim_report![0]!.recover_via.instrument).toBe('kala_ritual_get')
    expect(bounded.trim_report![0]!.recover_via.hint).toContain('candidate')
    expect(bounded.trim_report![0]!.recover_via.hint).not.toContain('census')
    const drillPointers = (bounded as typeof bounded & {
      drill_pointers?: Array<{ instrument: string | null; hint: string }>
    }).drill_pointers ?? []
    expect(drillPointers).toEqual([bounded.trim_report![0]!.recover_via])
  })

  it('bounds Mode 1 opportunities and large substrate arrays at the same default ceiling', () => {
    const response = opportunityResponse()
    expect(estimateBytes(response)).toBeGreaterThan(40 * 1024)

    const bounded = finalizeKalaRitualResponseBudget(response as never, 16)
    expect(estimateBytes(bounded)).toBeLessThanOrEqual(16 * 1024)
    expect(Buffer.byteLength(JSON.stringify(bounded))).toBeLessThanOrEqual(16 * 1024)
    expect(bounded.budget_kb_applied).toBe(16)
    expect(bounded.budget_kb_requested).toBe(16)
    expect(bounded.trim_report).not.toBeNull()
    expect(bounded.opportunities!.opportunities.length).toBeGreaterThan(0)
  })
})

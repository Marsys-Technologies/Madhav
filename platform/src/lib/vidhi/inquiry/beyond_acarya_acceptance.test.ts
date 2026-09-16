import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { getCatalog } from '../../retrieval/registry/catalog'
import { compileCapabilityKnowledge } from '../../retrieval/registry/knowledge/compiler'
import type { CapabilityKnowledgeSnapshot } from '../../retrieval/registry/knowledge/types'
import {
  BEYOND_ACARYA_ACCEPTANCE_VERSION,
  evaluateBeyondAcaryaAcceptance,
} from './beyond_acarya_acceptance'
import { BEYOND_ACARYA_ACCEPTANCE_CASES } from './beyond_acarya_acceptance.corpus'

const snapshot = compileCapabilityKnowledge(getCatalog(), '2026-09-15T00:00:00.000Z')

function withoutScu(
  source: CapabilityKnowledgeSnapshot,
  scuId: string,
): CapabilityKnowledgeSnapshot {
  return {
    ...source,
    scus: source.scus.filter((scu) => scu.scu_id !== scuId),
    edges: source.edges.filter((edge) => edge.from_scu_id !== scuId && edge.to_scu_id !== scuId),
  }
}

describe('Purna Anvesana Wave 7 Beyond-Acarya source acceptance', () => {
  it('closes the unchanged frozen route denominator through receipted transit derivation', () => {
    const report = evaluateBeyondAcaryaAcceptance(snapshot, BEYOND_ACARYA_ACCEPTANCE_CASES)

    expect(report.acceptance_version).toBe(BEYOND_ACARYA_ACCEPTANCE_VERSION)
    expect(report.corpus_version).toBe('beyond-acarya-inquiry-corpus-v1')
    expect(report.metrics.novel_combination_suite).toMatchObject({
      passed: true,
      cases: 5,
      expected_novel_capabilities: 13,
      missing_novel_capabilities: 0,
    })
    expect(report.metrics.omission_rate).toMatchObject({ passed: true, omitted: 0, expected: 25, rate: 0 })
    expect(report.metrics.route_coverage).toEqual({ passed: true, covered: 34, expected: 34, rate: 1 })
    expect(report.metrics.semantic_edge_coverage).toMatchObject({ passed: true, covered: 9, expected: 9, rate: 1 })
    expect(report.cases.every((item) => item.missing_required_route_scu_ids.length === 0)).toBe(true)
    expect(report.metrics.long_inquiry_closure).toMatchObject({
      passed: true,
      completed_cases: 1,
      total_cases: 1,
      blocked_case_ids: [],
      minimum_iterations_observed: 11,
      retained_earlier_evidence: true,
    })
    expect(report.metrics.long_inquiry_closure.pagination_continuations).toBeGreaterThanOrEqual(1)
    expect(report.metrics.abstention_quality).toMatchObject({ passed: true, passed_cases: 3, total_cases: 3 })
    expect(report.passed).toBe(true)
    expect(report.report_hash).toBe('sha256:bf9961d5c90c5907d486f8a97c0a9ec19999507234dc0efbda97b369dd947e9d')
  })

  it('detects an independently expected concept omitted from the snapshot', () => {
    const report = evaluateBeyondAcaryaAcceptance(
      withoutScu(snapshot, 'scu.catalog.query_contradictions'),
      BEYOND_ACARYA_ACCEPTANCE_CASES,
    )

    expect(report.metrics.omission_rate.omitted).toBeGreaterThan(0)
    expect(report.metrics.omission_rate.passed).toBe(false)
    expect(report.metrics.novel_combination_suite.passed).toBe(false)
    expect(report.passed).toBe(false)
  })

  it.each([
    ['Bhavat Bhavam', 'scu.catalog.judgment_query'],
    ['decisive cancellation', 'scu.yoga.firing_and_cancellation'],
  ])('turns the externally denominated omission gate red for %s ablation', (_label, scuId) => {
    const report = evaluateBeyondAcaryaAcceptance(withoutScu(snapshot, scuId), BEYOND_ACARYA_ACCEPTANCE_CASES)

    expect(report.metrics.omission_rate.passed).toBe(false)
    expect(report.metrics.novel_combination_suite.passed).toBe(false)
    expect(report.passed).toBe(false)
  })

  it('detects loss of a required platform route without weakening the denominator', () => {
    const altered: CapabilityKnowledgeSnapshot = {
      ...snapshot,
      scus: snapshot.scus.map((scu) => scu.scu_id === 'scu.catalog.judgment_query'
        ? {
            ...scu,
            bindings: scu.bindings.map((binding) => ({
              ...binding,
              execution_channels: binding.execution_channels?.filter((channel) => channel !== 'platform_internal'),
            })),
          }
        : scu),
    }
    const report = evaluateBeyondAcaryaAcceptance(altered, BEYOND_ACARYA_ACCEPTANCE_CASES)

    expect(report.metrics.route_coverage.covered).toBeLessThan(report.metrics.route_coverage.expected)
    expect(report.metrics.route_coverage.passed).toBe(false)
    expect(report.passed).toBe(false)
  })

  it('detects a severed reviewed semantic edge', () => {
    const edge = 'scu.kala.temporal_activation|requires|scu.catalog.query_planet_transit'
    const altered: CapabilityKnowledgeSnapshot = {
      ...snapshot,
      edges: snapshot.edges.filter((candidate) =>
        `${candidate.from_scu_id}|${candidate.relation}|${candidate.to_scu_id}` !== edge),
    }
    const report = evaluateBeyondAcaryaAcceptance(altered, BEYOND_ACARYA_ACCEPTANCE_CASES)

    expect(report.metrics.semantic_edge_coverage.covered)
      .toBeLessThan(report.metrics.semantic_edge_coverage.expected)
    expect(report.metrics.semantic_edge_coverage.passed).toBe(false)
    expect(report.metrics.route_coverage.expected).toBe(34)
    expect(report.passed).toBe(false)
  })

  it('keeps the unchanged route gate red when the aggregate transit binding is unavailable', () => {
    const unroutable: CapabilityKnowledgeSnapshot = {
      ...snapshot,
      scus: snapshot.scus.map((scu) => scu.scu_id === 'scu.catalog.query_planet_transit'
        ? {
            ...scu,
            bindings: scu.bindings.map((binding) => binding.binding_id === 'registry:marsys://tool/L0/query_current_transit_snapshot'
              ? { ...binding, executable: false, execution_channels: [] }
              : binding),
          }
        : scu),
    }
    const report = evaluateBeyondAcaryaAcceptance(unroutable, BEYOND_ACARYA_ACCEPTANCE_CASES)

    expect(report.metrics.route_coverage).toEqual({ passed: false, covered: 30, expected: 34, rate: 30 / 34 })
    expect(report.passed).toBe(false)
  })

  it('turns long-inquiry closure red when continuation metadata is removed', () => {
    const noContinuations: CapabilityKnowledgeSnapshot = {
      ...snapshot,
      scus: snapshot.scus.map((scu) => ({
        ...scu,
        bindings: scu.bindings.map((binding) => ({
          ...binding,
          pagination_contract: binding.pagination_contract
            ? { ...binding.pagination_contract, request_position_path: undefined }
            : undefined,
        })),
      })),
    }
    const report = evaluateBeyondAcaryaAcceptance(noContinuations, BEYOND_ACARYA_ACCEPTANCE_CASES)

    expect(report.metrics.long_inquiry_closure).toMatchObject({
      passed: false,
      pagination_continuations: 0,
    })
    expect(report.passed).toBe(false)
  })

  it('turns abstention quality red when the adversarial floor no longer matches the declared intent', () => {
    const weakenedCorpus = BEYOND_ACARYA_ACCEPTANCE_CASES.map((item, index) => index === 0
      ? { ...item, scope_tuple: { ...item.scope_tuple, intent: 'unknown' } }
      : item)
    const report = evaluateBeyondAcaryaAcceptance(snapshot, weakenedCorpus)

    expect(report.metrics.abstention_quality).toMatchObject({ passed: false, passed_cases: 2, total_cases: 3 })
    expect(report.passed).toBe(false)
  })

  it('labels the result as synthetic source evidence and refuses empirical claims', () => {
    const report = evaluateBeyondAcaryaAcceptance(snapshot, BEYOND_ACARYA_ACCEPTANCE_CASES)

    expect(report.evidence_kind).toBe('synthetic_source_local')
    expect(report.claim_ceiling).toBe('SOURCE_SCOPE_COMPLETE_WITH_AUTHORITY_BOUND_REMAINDER')
    expect(report.empirical_answer_quality).toBe('NOT_RUN')
    expect(report.expert_domain_review).toBe('REQUIRED_BEFORE_EMPIRICAL_ACCEPTANCE')
    expect(report.production_validation).toBe('NOT_RUN')
  })

  it('pins the governed evidence artifact to the executable report', () => {
    const artifact = JSON.parse(readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v2.json',
      import.meta.url,
    ), 'utf8')) as Record<string, unknown>
    const report = evaluateBeyondAcaryaAcceptance(snapshot, BEYOND_ACARYA_ACCEPTANCE_CASES)

    expect(artifact).toMatchObject({
      acceptance_version: report.acceptance_version,
      corpus_version: report.corpus_version,
      capability_content_hash: report.capability_content_hash,
      report_hash: report.report_hash,
      evidence_kind: report.evidence_kind,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
      metrics: {
        novel_combination_suite: report.metrics.novel_combination_suite,
        omission_rate: report.metrics.omission_rate,
        route_coverage: report.metrics.route_coverage,
        semantic_edge_coverage: report.metrics.semantic_edge_coverage,
        long_inquiry_closure: {
          passed: report.metrics.long_inquiry_closure.passed,
          completed_cases: report.metrics.long_inquiry_closure.completed_cases,
          total_cases: report.metrics.long_inquiry_closure.total_cases,
          minimum_iterations_observed: report.metrics.long_inquiry_closure.minimum_iterations_observed,
          pagination_continuations: report.metrics.long_inquiry_closure.pagination_continuations,
          retained_earlier_evidence: report.metrics.long_inquiry_closure.retained_earlier_evidence,
        },
        abstention_quality: {
          passed: report.metrics.abstention_quality.passed,
          passed_cases: report.metrics.abstention_quality.passed_cases,
          total_cases: report.metrics.abstention_quality.total_cases,
        },
      },
      claim_ceiling: report.claim_ceiling,
      empirical_answer_quality: report.empirical_answer_quality,
      production_validation: report.production_validation,
    })
  })
})

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

describe('Purna Anvesana Wave 6 Beyond-Acarya source acceptance', () => {
  it('evaluates the versioned corpus without hiding the current route-bound closure gap', () => {
    const report = evaluateBeyondAcaryaAcceptance(snapshot, BEYOND_ACARYA_ACCEPTANCE_CASES)

    expect(report.acceptance_version).toBe(BEYOND_ACARYA_ACCEPTANCE_VERSION)
    expect(report.corpus_version).toBe('beyond-acarya-inquiry-corpus-v1')
    expect(report.metrics.novel_combination_suite).toMatchObject({
      passed: true,
      cases: 4,
      expected_novel_capabilities: 12,
      missing_novel_capabilities: 0,
    })
    expect(report.metrics.omission_rate).toMatchObject({ passed: true, omitted: 0, expected: 23, rate: 0 })
    expect(report.metrics.route_coverage).toEqual({ passed: false, covered: 28, expected: 32, rate: 0.875 })
    expect(report.metrics.semantic_edge_coverage).toMatchObject({ passed: true, covered: 5, expected: 5, rate: 1 })
    expect(report.cases.every((item) =>
      item.missing_required_route_scu_ids.includes('scu.catalog.query_planet_transit'))).toBe(true)
    expect(report.metrics.long_inquiry_closure).toMatchObject({
      passed: false,
      completed_cases: 0,
      total_cases: 4,
      blocked_case_ids: BEYOND_ACARYA_ACCEPTANCE_CASES.map((item) => item.case_id),
    })
    expect(report.metrics.long_inquiry_closure.minimum_iterations_observed).toBeGreaterThanOrEqual(2)
    expect(report.metrics.abstention_quality).toMatchObject({ passed: true, passed_cases: 3, total_cases: 3 })
    expect(report.passed).toBe(false)
    expect(report.report_hash).toBe('sha256:325ef2306090b3e326d6fc4effbf4382f96bf81d3484e0840c0b6c068cb5cc06')
  })

  it('detects an independently expected concept omitted from the snapshot', () => {
    const report = evaluateBeyondAcaryaAcceptance(
      withoutScu(snapshot, 'scu.catalog.query_contradictions'),
      BEYOND_ACARYA_ACCEPTANCE_CASES,
    )

    expect(report.metrics.omission_rate.omitted).toBeGreaterThan(0)
    expect(report.metrics.omission_rate.passed).toBe(false)
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
    const edge = BEYOND_ACARYA_ACCEPTANCE_CASES.flatMap((item) => item.expected_edge_keys)[0]!
    const altered: CapabilityKnowledgeSnapshot = {
      ...snapshot,
      edges: snapshot.edges.filter((candidate) =>
        `${candidate.from_scu_id}|${candidate.relation}|${candidate.to_scu_id}` !== edge),
    }
    const report = evaluateBeyondAcaryaAcceptance(altered, BEYOND_ACARYA_ACCEPTANCE_CASES)

    expect(report.metrics.semantic_edge_coverage.covered)
      .toBeLessThan(report.metrics.semantic_edge_coverage.expected)
    expect(report.metrics.semantic_edge_coverage.passed).toBe(false)
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
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v1.json',
      import.meta.url,
    ), 'utf8')) as Record<string, unknown>
    const report = evaluateBeyondAcaryaAcceptance(snapshot, BEYOND_ACARYA_ACCEPTANCE_CASES)

    expect(artifact).toMatchObject({
      acceptance_version: report.acceptance_version,
      corpus_version: report.corpus_version,
      capability_content_hash: report.capability_content_hash,
      report_hash: report.report_hash,
      evidence_kind: report.evidence_kind,
      verdict: 'NOT_ACCEPTED_SOURCE_LOCAL',
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

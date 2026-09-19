import { describe, expect, it } from 'vitest'
import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'
import type { CapabilityKnowledgeSnapshot } from '../../retrieval/registry/knowledge/types'
import committedSnapshot from '../../../generated/capability_knowledge.snapshot.json'
import {
  BEYOND_ACARYA_ACCEPTANCE_VERSION,
  evaluateBeyondAcaryaAcceptance,
} from './beyond_acarya_acceptance'
import { BEYOND_ACARYA_ACCEPTANCE_CASES } from './beyond_acarya_acceptance.corpus'

const snapshot = committedSnapshot as CapabilityKnowledgeSnapshot
const historicalV2 = {
  capability_content_hash: 'sha256:55e17219c3e537a442cf02777d501a28874dd27c2e67a55422c0af47424f85a7',
  report_hash: 'sha256:df21accf7b9c1ee72ef08ee05b07db4c36ae559e2019d5a175bfa842a536d30f',
} as const
const historicalV3 = {
  capability_content_hash: 'sha256:20c909f45c80c6fbc16a0900b951f60993fefd7241e06ee58bb1498a87bc1172',
  report_hash: 'sha256:9c86043abcdcd9859da602bab6323a67bd138eca6d9fbbb10b9eee15b7815b6f',
  artifact_hash: 'sha256:9c12f15b88f3d4bb1f1766a9364d231801e8c1a82e3bb3ea0b1680ba9935bc1e',
} as const

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
    expect(report.report_hash).toBe('sha256:19c9f8dda527813b11db08b96f879cc3f7ef41254831ad54576078d23525330e')
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

  it('keeps the immutable v2 evidence artifact pinned to its historical snapshot and report', () => {
    const artifactBytes = readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v2.json',
      import.meta.url,
    ))
    const artifact = JSON.parse(artifactBytes.toString('utf8')) as Record<string, unknown>

    expect(`sha256:${createHash('sha256').update(artifactBytes).digest('hex')}`)
      .toBe('sha256:33595346209c3f31b7123f5dbb002712e3ca5de52b06cfc1b7170a4ac70543e0')
    expect(artifact).toMatchObject({
      acceptance_version: 'beyond-acarya-source-acceptance-v2',
      capability_content_hash: historicalV2.capability_content_hash,
      report_hash: historicalV2.report_hash,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
    })
  })

  it('keeps the v3 source-successor artifact immutable while a later successor advances', () => {
    const artifactBytes = readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v3.json',
      import.meta.url,
    ))
    const artifact = JSON.parse(artifactBytes.toString('utf8')) as Record<string, unknown>

    expect(`sha256:${createHash('sha256').update(artifactBytes).digest('hex')}`).toBe(historicalV3.artifact_hash)
    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v3',
      capability_content_hash: historicalV3.capability_content_hash,
      report_hash: historicalV3.report_hash,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
    })
  })

  it('pins the v4 source-successor artifact to the current executable report without claiming live acceptance', () => {
    const artifact = JSON.parse(readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v4.json',
      import.meta.url,
    ), 'utf8')) as Record<string, unknown>
    const report = evaluateBeyondAcaryaAcceptance(snapshot, BEYOND_ACARYA_ACCEPTANCE_CASES)
    const snapshotBytes = readFileSync(new URL('../../../generated/capability_knowledge.snapshot.json', import.meta.url))
    const snapshotFileSha256 = `sha256:${createHash('sha256').update(snapshotBytes).digest('hex')}`

    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v4',
      predecessor: {
        artifact: 'BEYOND_ACARYA_ACCEPTANCE_v3.json',
        acceptance_version: 'beyond-acarya-source-acceptance-v2',
        capability_content_hash: historicalV3.capability_content_hash,
        report_hash: historicalV3.report_hash,
      },
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
      expert_domain_review: report.expert_domain_review,
      empirical_answer_quality: report.empirical_answer_quality,
      production_validation: report.production_validation,
      source_status: 'SOURCE_ONLY_NOT_LIVE',
      candidate_validation: 'NOT_RUN',
      deployed_route_validation: 'NOT_RUN',
      generated_snapshot: {
        path: 'platform/src/generated/capability_knowledge.snapshot.json',
        generated_at: snapshot.generated_at,
        capability_content_hash: snapshot.content_hash,
        snapshot_file_sha256: snapshotFileSha256,
        source_catalog_fingerprint: snapshot.source_catalog_fingerprint,
        semantic_review_fingerprint: snapshot.semantic_review_fingerprint,
        producer_contract_fingerprint: snapshot.producer_contract_fingerprint,
      },
      evaluated_source_revision: 'b16c77567f8aa24af124564b84519e27082e3d33',
    })
  })
})

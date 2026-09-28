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
const historicalV4 = {
  capability_content_hash: 'sha256:2855530bc7c62761739307ad89c1d6736df9783cac291537483a49794d699bbf',
  report_hash: 'sha256:acbf2428749c5b97b30b1e462d496ff424861210da2046788dd940e5b521f907',
  artifact_hash: 'sha256:d972ce0345092602ff2acf258da13f1711cb1671f1625fbf552eb97594154320',
} as const
const historicalV5 = {
  capability_content_hash: 'sha256:944183d7b8abfcc14b48eb01bbc1d2bc83ee54e6a6ced4f600fa7fd43f3e7ee7',
  report_hash: 'sha256:22b4f8d5237e786493ee848f8f750d3b8622399941daa12b75b0b741cf1c4542',
  artifact_hash: 'sha256:2243892141bbc350d804958d4ad78c2425e84c44a9e09634eb883dbe34a600d9',
} as const
// Jātaka Phase-A3: v6 becomes an immutable historical predecessor (like v2-v5) now that v7
// exists as the current executable report — see the "keeps the v6 source-successor immutable"
// and "keeps the v7 source-successor immutable" tests below.
const historicalV6 = {
  capability_content_hash: 'sha256:0a2a675d0098390453d77ba0119b87fad865728e908290eaee6cc84fc465bc36',
  report_hash: 'sha256:bfe04932a3358e9142b09e89902c02eaf9b020a389075ccd92b424a397b480c0',
  artifact_hash: 'sha256:04579974349aed1377b26755b4a737dcb4cd14adee808b773e6cc986a956aec5',
} as const
// R4 local integration (native ruling, 2026-09-28): v6 forked into two independent "v7"
// successors on divergent branches (this branch's own R0-R3 v7, and protected main's Jātaka
// Phase-A3 v7 — both cite v6 as predecessor). Protected main's v7 is canonical and stays
// byte-identical at the root path; this branch's own v7-v11 chain is preserved as historical
// fork evidence under historical_fork_v7_v11/ (manifest:
// historical_fork_v7_v11/LINEAGE_FORK_MANIFEST_v1_0.md; fork-preservation assertions live in
// beyond_acarya_v7_lineage_fork.test.ts, not here). historicalV7 below is main's real,
// now-immutable v7 — the predecessor of the new canonical v8 created at this boundary.
const historicalV7 = {
  capability_content_hash: 'sha256:6a595916dda6ba2b23c2c567c97cc50ddc1d218c353ea56aa383ffceb62dad7b',
  report_hash: 'sha256:7bdef36180d6734a5ce495a6a0458928c07fd501c049600a187d850814945001',
  artifact_hash: 'sha256:1bbf5912d64f6f5eff05c5c8416d209cd00cafd3a009cb43fc4d2d5a00b21f15',
} as const
// R4 local integration's canonical successor of main's v7; immutable since the R5A review-fix
// successor (v9) superseded it.
const historicalV8 = {
  capability_content_hash: 'sha256:0556249e1b779895b5927acfd6b45ec8ad6508ae3f8fb8d78e620b92550429da',
  report_hash: 'sha256:d272acc46e93c030b8bef6d3f62802034b501cf65e8d42196c93988eac9153c0',
  artifact_hash: 'sha256:551da8df072df9135895deffa0c630f63d5d3d4a44b03766d20bcabc1b15e6d5',
} as const

// The R5A review-fix successor of v8 (PR #2742). Immutable since the follow-up's v10 superseded it.
const historicalV9 = {
  capability_content_hash: 'sha256:5aa264439b7eb730b6e71a3cb7e8325e212c9dec9584ab85cb70833c71491f02',
  report_hash: 'sha256:827fb97b792780ab91d011c0a51cb72774a00e1e7d20f8cd9efda004d07adb74',
  artifact_hash: 'sha256:ce77568e7d7d4d79d68f1c0359932ef12503984ee6d2528cde9f711750d32ed9',
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
      minimum_iterations_observed: 10,
      retained_earlier_evidence: true,
    })
    expect(report.metrics.long_inquiry_closure.pagination_continuations).toBeGreaterThanOrEqual(1)
    expect(report.metrics.abstention_quality).toMatchObject({ passed: true, passed_cases: 3, total_cases: 3 })
    expect(report.passed).toBe(true)
    // Follow-up boundary (Packet A): capability_content_hash/report_hash move once more, for the
    // seven leaf build_id declarations that let the composites' legs (and inquiry-dispatched
    // reads) be fenced to the served generation — no denominator changed (see the metrics
    // assertions above and the v10 pin test below; identical to v7, v8 and v9's own metrics).
    expect(report.report_hash).toBe('sha256:fe396729f26232dcfd950da18619c79283d46c6408e767ca8428d4a387fc9cde')
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

  it('keeps the v4 source-successor immutable after a later contract-truth advance', () => {
    const artifactBytes = readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v4.json',
      import.meta.url,
    ))
    const artifact = JSON.parse(artifactBytes.toString('utf8')) as Record<string, unknown>

    expect(`sha256:${createHash('sha256').update(artifactBytes).digest('hex')}`).toBe(historicalV4.artifact_hash)
    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v4',
      capability_content_hash: historicalV4.capability_content_hash,
      report_hash: historicalV4.report_hash,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
    })
  })

  it('keeps the v5 source-successor immutable after a later contract-truth advance', () => {
    const artifactBytes = readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v5.json',
      import.meta.url,
    ))
    const artifact = JSON.parse(artifactBytes.toString('utf8')) as Record<string, unknown>

    expect(`sha256:${createHash('sha256').update(artifactBytes).digest('hex')}`).toBe(historicalV5.artifact_hash)
    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v5',
      capability_content_hash: historicalV5.capability_content_hash,
      report_hash: historicalV5.report_hash,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
    })
  })

  it('keeps the v6 source-successor immutable after a later contract-truth advance (Jātaka Phase-A3)', () => {
    const artifactBytes = readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v6.json',
      import.meta.url,
    ))
    const artifact = JSON.parse(artifactBytes.toString('utf8')) as Record<string, unknown>

    expect(`sha256:${createHash('sha256').update(artifactBytes).digest('hex')}`).toBe(historicalV6.artifact_hash)
    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v6',
      capability_content_hash: historicalV6.capability_content_hash,
      report_hash: historicalV6.report_hash,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
    })
  })

  // R4 local integration boundary (native ruling, 2026-09-28): protected main's v7 is now the
  // canonical predecessor of the new v8 below. It stays immutable exactly like v2-v6 — this
  // branch's OWN divergent v7-v11 fork is preserved separately (historical_fork_v7_v11/,
  // manifest at historical_fork_v7_v11/LINEAGE_FORK_MANIFEST_v1_0.md) and is never
  // treated as this file's canonical lineage; see beyond_acarya_v7_lineage_fork.test.ts.
  it('keeps the v7 source-successor artifact immutable after the R4 main-integration advance', () => {
    const artifactBytes = readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v7.json',
      import.meta.url,
    ))
    const artifact = JSON.parse(artifactBytes.toString('utf8')) as Record<string, unknown>

    expect(`sha256:${createHash('sha256').update(artifactBytes).digest('hex')}`).toBe(historicalV7.artifact_hash)
    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v7',
      predecessor: {
        artifact: 'BEYOND_ACARYA_ACCEPTANCE_v6.json',
        acceptance_version: 'beyond-acarya-source-acceptance-v2',
        capability_content_hash: historicalV6.capability_content_hash,
        report_hash: historicalV6.report_hash,
      },
      capability_content_hash: historicalV7.capability_content_hash,
      report_hash: historicalV7.report_hash,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
      evaluated_source_revision: 'ed5ad601c5e568f5d6c5d8ec72bc7c8f9ff2bd2b',
    })
  })

  it('keeps the v8 source-successor artifact immutable after the R5A review-fix advance', () => {
    const artifactBytes = readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v8.json',
      import.meta.url,
    ))
    const artifact = JSON.parse(artifactBytes.toString('utf8')) as Record<string, unknown>

    expect(`sha256:${createHash('sha256').update(artifactBytes).digest('hex')}`).toBe(historicalV8.artifact_hash)
    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v8',
      predecessor: {
        artifact: 'BEYOND_ACARYA_ACCEPTANCE_v7.json',
        acceptance_version: 'beyond-acarya-source-acceptance-v2',
        capability_content_hash: historicalV7.capability_content_hash,
        report_hash: historicalV7.report_hash,
      },
      capability_content_hash: historicalV8.capability_content_hash,
      report_hash: historicalV8.report_hash,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
      evaluated_source_revision: '9285326caa394f76ea6849fd3fe0309bc6d90239',
    })
  })

  it('keeps the v9 source-successor artifact immutable after the follow-up advance', () => {
    const artifactBytes = readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v9.json',
      import.meta.url,
    ))
    const artifact = JSON.parse(artifactBytes.toString('utf8')) as Record<string, unknown>

    expect(`sha256:${createHash('sha256').update(artifactBytes).digest('hex')}`).toBe(historicalV9.artifact_hash)
    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v9',
      predecessor: {
        artifact: 'BEYOND_ACARYA_ACCEPTANCE_v8.json',
        capability_content_hash: historicalV8.capability_content_hash,
        report_hash: historicalV8.report_hash,
      },
      capability_content_hash: historicalV9.capability_content_hash,
      report_hash: historicalV9.report_hash,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
      evaluated_source_revision: '1995ff17855907b338c6d4f049a9309a810e3508',
    })
  })

  it('pins the v10 source-successor artifact to the current executable report without claiming live acceptance (fence-and-successor-envelope follow-up)', () => {
    const artifact = JSON.parse(readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v10.json',
      import.meta.url,
    ), 'utf8')) as Record<string, unknown>
    const report = evaluateBeyondAcaryaAcceptance(snapshot, BEYOND_ACARYA_ACCEPTANCE_CASES)
    const snapshotBytes = readFileSync(new URL('../../../generated/capability_knowledge.snapshot.json', import.meta.url))
    const snapshotFileSha256 = `sha256:${createHash('sha256').update(snapshotBytes).digest('hex')}`

    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v10',
      predecessor: {
        artifact: 'BEYOND_ACARYA_ACCEPTANCE_v9.json',
        acceptance_version: 'beyond-acarya-source-acceptance-v2',
        capability_content_hash: historicalV9.capability_content_hash,
        report_hash: historicalV9.report_hash,
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
      // The follow-up source commit (5c114e530) whose tree this report was evaluated against, not
      // the later commits that regenerate the snapshot, the census and this successor.
      evaluated_source_revision: '5c114e53031c3e43f3f30c3dd36ed0694d19f3cc',
    })
  })
})

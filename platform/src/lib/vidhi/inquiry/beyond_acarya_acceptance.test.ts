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

// The fence-and-successor-envelope follow-up successor of v9. Immutable since the Kāla B1
// gochara re-identification lane's snapshot regeneration (v11) superseded it.
const historicalV10 = {
  capability_content_hash: 'sha256:9b47461d6716337149dd636cc2d6bed3a7506d86bc15aea51c727d9ba1955f58',
  report_hash: 'sha256:fe396729f26232dcfd950da18619c79283d46c6408e767ca8428d4a387fc9cde',
  artifact_hash: 'sha256:f988b6fd13fd1c2b667c66206444a7bbd030e369a748ecd1ea63a6d5f063cf8a',
} as const

// The Kāla B1 gochara re-identification successor of v10. Immutable since the WP10
// migration-1091 registry-identity reconciliation (v12) superseded it.
const historicalV11 = {
  capability_content_hash: 'sha256:e6c208210c310bf19257be96897b5eb225610b7d5c03efb420da53ea46fdfd5d',
  report_hash: 'sha256:773dd150de295ed561b42402fc4209228574ed8c07653bc414368606a48af8bc',
  artifact_hash: 'sha256:5c840cf8efacbbf06eb83de5973f3f984ffe3e3e742749755a987e4098555081',
} as const
// The WP10 migration-1091 registry-identity reconciliation successor of v11. Immutable since the
// Suvarna Track I-4 census flip (v13) superseded it.
const historicalV12 = {
  capability_content_hash: 'sha256:9b47461d6716337149dd636cc2d6bed3a7506d86bc15aea51c727d9ba1955f58',
  report_hash: 'sha256:fe396729f26232dcfd950da18619c79283d46c6408e767ca8428d4a387fc9cde',
  artifact_hash: 'sha256:cb9895cf6847a0e5f73669d28d4d57b783e35417bc72b9cb3a5045d4022edcf6',
} as const
// The Suvarna Track I-4 census-flip successor of v12. Immutable since the Suvarna tool-text wave 1
// regeneration (v14) superseded it.
const historicalV13 = {
  capability_content_hash: 'sha256:6c1aefca7601a9b7204471e0a3ccc03fe8ffa31819e5800b0d5e36fe83e156a8',
  report_hash: 'sha256:c0322d170afc3c8138f7ada1173476956b58b709a55f9c042a2f1899f24ad862',
  artifact_hash: 'sha256:c8bccc68ea7ea9c8a574c8a88d35b294cf2c9570a6330f1e91704b6725f41ed7',
} as const
// The Suvarna tool-text wave 1 successor of v13. Immutable since the Pravāha ka_gochara
// registry-revert (migration 1230, v15) superseded it.
const historicalV14 = {
  capability_content_hash: 'sha256:89eeb133f93d2976f4b1656393af620d1c6070d9f8bfa8ce2e9c7d86e9e8bc17',
  report_hash: 'sha256:0899b303104a534f2222d5845bd1cb1ac1061a0b25b736307bdbcaa0c63e8a88',
  artifact_hash: 'sha256:d61bc95fa74dff4da2bfd050e936f6388aa94a657589c1bc7053eb65fd705133',
} as const

// The Pravāha ka_gochara registry-revert successor of v14. Immutable since the Suvarna lane L-KARANAJALA
// descriptor / census-note regeneration (N-143 option B, v16) superseded it.
const historicalV15 = {
  capability_content_hash: 'sha256:bff49e66b133a837aab85a209679b0a0f8c476b2a13734765fe7d064dc0d417b',
  report_hash: 'sha256:f35696cc07f5df555e07dbb33b096e46501896048b8be45456a895f75b03f558',
  artifact_hash: 'sha256:988f9ceb467f62a10e8a14e2bbd0109bd3c8e55689a7765c25fd91cc0be93c83',
} as const

// The Suvarna lane L-KARANAJALA successor of v15. Immutable since the per-asset served-fence
// source-query-contract regeneration (SS N-208, v17) superseded it.
const historicalV16 = {
  capability_content_hash: 'sha256:e83ebc215a7988f04111a808262090f310ee26b6ac1c6615f8dc45a3bf819a11',
  report_hash: 'sha256:8dedd431e0b29e68bb8c9d3130ef85a62767aa3302808d1f663a0ba65a9a8950',
  artifact_hash: 'sha256:63a15a628daa75a403b79711932ff39fad8a1249f3fbad40a568a8437a71680e',
} as const

// The per-asset served-fence successor of v16 (SS N-208). Immutable since the Dens.served density-contract
// regeneration (SS N-211 / N-212, v18) superseded it.
const historicalV17 = {
  capability_content_hash: 'sha256:d84fd0ab6305e135aa1805b3c93a388171b5f395d9085d0a7bb85b37e2002bbe',
  report_hash: 'sha256:e35350a1205ea310be1d686d1832c3fbc78e771b54f7145b426b31550df4ddbd',
  artifact_hash: 'sha256:67c10a3079193f6d652219ffc64b01c50e586f553ebed025f05b39a4bc3070e3',
} as const

// The Dens.served density-contract successor of v17 (SS N-211 / N-212). Immutable since the Fact Identity Index writer (migration 1333, FIX1, v19)
// superseded it.
const historicalV18 = {
  capability_content_hash: 'sha256:90d63b9b76d8ff5a13adbedf7785a37837185d0db264559daf59a3d8c876a4c6',
  report_hash: 'sha256:0e631feaf231cfdbdb5c546017ceabd7857696293778deb7c86050c3ba6a09f4',
  artifact_hash: 'sha256:f4e200f03fc0441c1e08de4a0758016bf6dff329d730d28a5aecbee86e6d5037',
} as const

// The Fact Identity Index writer successor of v18 (FIX1 / migration 1333). Immutable since the DENS-F shared-table-facet regeneration (v20) superseded it.
const historicalV19 = {
  capability_content_hash: 'sha256:767da1a16a070263ec6e42cd607c173f192443c8ba4c962adc8b954c026d5e4e',
  report_hash: 'sha256:a12f8859a2d62aec21d95e8d375308c7dc4b80b3ed80915b29aac5402c5c7d96',
  artifact_hash: 'sha256:af02c2846c2c7d07456d341cc87d399276609b6b3d1467f01afbc10b50b469d3',
} as const

// The DENS-F shared-table-facet successor of v19 (PR #3302). Immutable since the combined fix round 1 regeneration (v21: DENS-A tier carriage,
// WFIX-A writer rows-written, DISPIMG, DENS-F) superseded it.
const historicalV20 = {
  capability_content_hash: 'sha256:742a6ee6353c8622eb6896b7f18f6fedc44f098b6bbde7aa5f11e808753d4858',
  report_hash: 'sha256:30ec3edce1578dd504a95661174e0530d5b8498a6d2ac4655be928191c951c56',
  artifact_hash: 'sha256:f3b89cb45de7a180ad096f704d8618e044b6fd654bd455aa8d3823c327bbf718',
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
    // WP10 migration-1091 registry-identity reconciliation boundary (steward review of
    // Pravaha A0.3/A0.4, 2026-09-29): the ka_gochara seed literal was re-identified from the
    // pre-1091 Kāla B1 writer-module identity (kala_gochara_windows_v2/'2.0') to the applied,
    // native-authorised 1091 registry identity (kala_gochara_windows/'4.0', written by the
    // kala_gochara_cutover scripts; integrity conjunct (j) pins target_table = count_sql
    // relation). The seed correction moved the producer_contract_fingerprint and the snapshot
    // was regenerated on the merged tree (a35eff544, Density Census §N.6, 182 SCUs,
    // codegen:capability-knowledge:check green). capability_content_hash/report_hash coincide
    // byte-for-byte with v10 — the census-visible catalog identity returned to the production
    // relation and no SCU, edge, proof kind or availability disposition changed (see the
    // metrics assertions above and the v12 pin test below; identical to v7-v11's own metrics).
    // Suvarna Track I-4 census flip (v13): migration 1212 gives ka_vighnakara its first reviewed
    // output-digest spec, so the census (static replay of spec INSERTs) no longer lists it as a
    // blocked contract. This moved capability_content_hash/producer_contract_fingerprint and, with
    // them, report_hash; no SCU, edge, proof kind or availability disposition changed (the metric
    // assertions above are unchanged). Only this pinned hash was re-pinned.
    // Suvarna tool-text wave 1 (v14): seven tool-text commits (get_argala virodha offsets,
    // get_ayurdaya source_refs anchor, the 7-/8-karaka scheme statements, register_d9_judgment
    // formation-gap sentence, chart-overview scheme note) changed capability descriptions, which
    // moved source_catalog_fingerprint/semantic_review_fingerprint/content_hash and, with them,
    // report_hash; producer_contract_fingerprint is unchanged and the metric assertions above are
    // unchanged. Only this pinned hash was re-pinned.
    // Pravāha ka_gochara registry revert (v15): migration 1230 reverts the ka_gochara registry
    // row to the pre-1091 registered-writer surface (kala_gochara_windows_v2 / generation '2.0'),
    // moving producer_contract_fingerprint (e5211) and, with it, capability_content_hash and
    // report_hash; source_catalog/semantic_review fingerprints coincide with v14's and no SCU,
    // edge, proof kind or availability disposition changed (the metric assertions above are
    // unchanged). Only this pinned hash was re-pinned.
    // Suvarna lane L-KARANAJALA (v16, N-143 option B): the query_mechanisms descriptor now documents that
    // constituent_ga_vichara_ids_array holds deterministic chart_vichara tokens (moved source_catalog_fingerprint) and
    // the census records a column_meaning_changed_spec_unchanged note in two producer contracts (moved
    // producer_contract_fingerprint); semantic_review_fingerprint coincides with v15's and no SCU, edge, proof kind or
    // availability disposition changed (the metric assertions above are unchanged). Only this pinned hash was re-pinned.
    // Per-asset served fence (v17, SS N-208): the get-dashas source-query contract SQL now takes its receipt-run
    // admission from the shared served_generation predicate (completed run, or a failed run for an asset that itself
    // finished); that moved semantic_review_fingerprint and, with it, capability_content_hash/report_hash.
    // source_catalog_fingerprint and producer_contract_fingerprint coincide with v16's and no SCU, edge, proof kind or
    // availability disposition changed (the metric assertions above are unchanged). Only this pinned hash was re-pinned.
    // PR #3236 review fixes F1-F3 additionally moved the resolver/overlay SQL (failed co-writer attempts, held-back
    // writer guard) that the source-query contract mirrors; same single re-pin, no further successor.
    // Dens.served (v18, SS N-211 / N-212): density_contract / empty_reason / paginated declarations on the L0/L1/L2 query capabilities
    // and traverse_chart_graph's tier column moved source_catalog_fingerprint (descriptor contracts), hence capability_content_hash and
    // report_hash. semantic_review_fingerprint and producer_contract_fingerprint coincide with v17's; no SCU, edge, proof kind or
    // availability disposition changed (the metric assertions above are unchanged). Only this pinned hash was re-pinned.
    // Fact Identity Index writer (v19, FIX1 / migration 1333): ga_fact_identity joins the active producer census (relational_digest_current_source_intent, via the
    // spec its migration inserts) and receives one authored producer-to-semantics binding (scu.catalog.query_pratijna, supports_same_semantic_domain). That moved
    // semantic_review_fingerprint and producer_contract_fingerprint, hence capability_content_hash and report_hash; source_catalog_fingerprint coincides with
    // v18's and no SCU, edge, proof kind or availability disposition changed (the metric assertions above are unchanged). Only this pinned hash was re-pinned.
    // DENS-F (v20): density_contract / empty_reason declarations on get_nakshatra, get_positions, get_sensitive_points, get_sensitive_degrees, query_ucd and get_graha_yuddha,
    // query_signals' producer_asset_id input and the two platform-mcp ref_* density entries moved source_catalog_fingerprint, hence capability_content_hash and report_hash.
    // semantic_review_fingerprint and producer_contract_fingerprint coincide with v19's; no SCU, edge, proof kind or availability disposition changed. Only this pinned hash was re-pinned.
    // Combined fix round 1 (v21): DENS-A's get_dasha_lord_capability description (dasha_verification_pass_status), DENS-F's contracts already in v20, and the
    // DISPIMG dispatch-tool descriptions moved source_catalog_fingerprint, hence capability_content_hash and report_hash. Only this pinned hash was re-pinned.
    expect(report.report_hash).toBe('sha256:61902d5867b6b341599074f133056804a9beb0f72b2aff59ea1d74b053003a57')
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

  it('keeps the v10 source-successor artifact immutable after the Kāla B1 gochara re-identification advance', () => {
    const artifactBytes = readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v10.json',
      import.meta.url,
    ))
    const artifact = JSON.parse(artifactBytes.toString('utf8')) as Record<string, unknown>

    expect(`sha256:${createHash('sha256').update(artifactBytes).digest('hex')}`).toBe(historicalV10.artifact_hash)
    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v10',
      predecessor: {
        artifact: 'BEYOND_ACARYA_ACCEPTANCE_v9.json',
        capability_content_hash: historicalV9.capability_content_hash,
        report_hash: historicalV9.report_hash,
      },
      capability_content_hash: historicalV10.capability_content_hash,
      report_hash: historicalV10.report_hash,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
      evaluated_source_revision: '5c114e53031c3e43f3f30c3dd36ed0694d19f3cc',
    })
  })

  it('keeps the v11 source-successor artifact immutable after the WP10 registry-1091 reconciliation advance', () => {
    const artifactBytes = readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v11.json',
      import.meta.url,
    ))
    const artifact = JSON.parse(artifactBytes.toString('utf8')) as Record<string, unknown>

    expect(`sha256:${createHash('sha256').update(artifactBytes).digest('hex')}`).toBe(historicalV11.artifact_hash)
    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v11',
      predecessor: {
        artifact: 'BEYOND_ACARYA_ACCEPTANCE_v10.json',
        capability_content_hash: historicalV10.capability_content_hash,
        report_hash: historicalV10.report_hash,
      },
      capability_content_hash: historicalV11.capability_content_hash,
      report_hash: historicalV11.report_hash,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
      evaluated_source_revision: 'cacc72440f98f79486ef679e046e2dbe1d687eb9',
    })
  })

  it('keeps the v12 source-successor artifact immutable after the Suvarna Track I-4 census-flip advance', () => {
    const artifactBytes = readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v12.json',
      import.meta.url,
    ))
    const artifact = JSON.parse(artifactBytes.toString('utf8')) as Record<string, unknown>

    expect(`sha256:${createHash('sha256').update(artifactBytes).digest('hex')}`).toBe(historicalV12.artifact_hash)
    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v12',
      predecessor: {
        artifact: 'BEYOND_ACARYA_ACCEPTANCE_v11.json',
        capability_content_hash: historicalV11.capability_content_hash,
        report_hash: historicalV11.report_hash,
      },
      capability_content_hash: historicalV12.capability_content_hash,
      report_hash: historicalV12.report_hash,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
      evaluated_source_revision: 'a35eff5449080b0bf271514a28b1dc57d10d9591',
    })
  })

  it('keeps the v13 source-successor artifact immutable after the Suvarna tool-text wave 1 advance', () => {
    const artifactBytes = readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v13.json',
      import.meta.url,
    ))
    const artifact = JSON.parse(artifactBytes.toString('utf8')) as Record<string, unknown>

    expect(`sha256:${createHash('sha256').update(artifactBytes).digest('hex')}`).toBe(historicalV13.artifact_hash)
    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v13',
      predecessor: {
        artifact: 'BEYOND_ACARYA_ACCEPTANCE_v12.json',
        capability_content_hash: historicalV12.capability_content_hash,
        report_hash: historicalV12.report_hash,
      },
      capability_content_hash: historicalV13.capability_content_hash,
      report_hash: historicalV13.report_hash,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
      evaluated_source_revision: '749e8467581665e84282743e6eba6f5df7400f01',
    })
  })

  it('keeps the v14 source-successor artifact immutable after the Pravāha ka_gochara registry-revert advance', () => {
    const artifactBytes = readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v14.json',
      import.meta.url,
    ))
    const artifact = JSON.parse(artifactBytes.toString('utf8')) as Record<string, unknown>

    expect(`sha256:${createHash('sha256').update(artifactBytes).digest('hex')}`).toBe(historicalV14.artifact_hash)
    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v14',
      predecessor: {
        artifact: 'BEYOND_ACARYA_ACCEPTANCE_v13.json',
        capability_content_hash: historicalV13.capability_content_hash,
        report_hash: historicalV13.report_hash,
      },
      capability_content_hash: historicalV14.capability_content_hash,
      report_hash: historicalV14.report_hash,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
      evaluated_source_revision: '1a973a22b936c3db96ee2cf65cfe825689a44f9a',
    })
  })

  it('keeps the v15 source-successor artifact immutable after the L-KARANAJALA descriptor/census-note advance', () => {
    const artifactBytes = readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v15.json',
      import.meta.url,
    ))
    const artifact = JSON.parse(artifactBytes.toString('utf8')) as Record<string, unknown>

    expect(`sha256:${createHash('sha256').update(artifactBytes).digest('hex')}`).toBe(historicalV15.artifact_hash)
    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v15',
      predecessor: {
        artifact: 'BEYOND_ACARYA_ACCEPTANCE_v14.json',
        capability_content_hash: historicalV14.capability_content_hash,
        report_hash: historicalV14.report_hash,
      },
      capability_content_hash: historicalV15.capability_content_hash,
      report_hash: historicalV15.report_hash,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
      evaluated_source_revision: '2560ca184d2527b351cdb86fdba4bd878feb5d92',
    })
  })

  it('keeps the v16 source-successor artifact immutable after the per-asset served-fence source-query-contract advance', () => {
    const artifactBytes = readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v16.json',
      import.meta.url,
    ))
    const artifact = JSON.parse(artifactBytes.toString('utf8')) as Record<string, unknown>

    expect(`sha256:${createHash('sha256').update(artifactBytes).digest('hex')}`).toBe(historicalV16.artifact_hash)
    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v16',
      predecessor: {
        artifact: 'BEYOND_ACARYA_ACCEPTANCE_v15.json',
        capability_content_hash: historicalV15.capability_content_hash,
        report_hash: historicalV15.report_hash,
      },
      capability_content_hash: historicalV16.capability_content_hash,
      report_hash: historicalV16.report_hash,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
      evaluated_source_revision: 'f72dc9d93921c1fd5c9497d72c044483fc7ba8a2',
    })
  })

  it('keeps the v17 source-successor artifact immutable after the Dens.served density-contract advance', () => {
    const artifactBytes = readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v17.json',
      import.meta.url,
    ))
    const artifact = JSON.parse(artifactBytes.toString('utf8')) as Record<string, unknown>

    expect(`sha256:${createHash('sha256').update(artifactBytes).digest('hex')}`).toBe(historicalV17.artifact_hash)
    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v17',
      predecessor: {
        artifact: 'BEYOND_ACARYA_ACCEPTANCE_v16.json',
        capability_content_hash: historicalV16.capability_content_hash,
        report_hash: historicalV16.report_hash,
      },
      capability_content_hash: historicalV17.capability_content_hash,
      report_hash: historicalV17.report_hash,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
      evaluated_source_revision: '9d0637087596eed1397634d45a644d9cb559d414',
    })
  })

  it('keeps the v18 source-successor artifact immutable after the Fact Identity Index writer advance', () => {
    const artifactBytes = readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v18.json',
      import.meta.url,
    ))
    const artifact = JSON.parse(artifactBytes.toString('utf8')) as Record<string, unknown>

    expect(`sha256:${createHash('sha256').update(artifactBytes).digest('hex')}`).toBe(historicalV18.artifact_hash)
    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v18',
      predecessor: {
        artifact: 'BEYOND_ACARYA_ACCEPTANCE_v17.json',
        capability_content_hash: historicalV17.capability_content_hash,
        report_hash: historicalV17.report_hash,
      },
      capability_content_hash: historicalV18.capability_content_hash,
      report_hash: historicalV18.report_hash,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
      evaluated_source_revision: '915fe924f4a3819bfdc803812dc41ae9e1adff7f',
    })
  })

  it('keeps the v19 source-successor artifact immutable after the DENS-F shared-table-facet advance', () => {
    const artifactBytes = readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v19.json',
      import.meta.url,
    ))
    const artifact = JSON.parse(artifactBytes.toString('utf8')) as Record<string, unknown>

    expect(`sha256:${createHash('sha256').update(artifactBytes).digest('hex')}`).toBe(historicalV19.artifact_hash)
    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v19',
      predecessor: {
        artifact: 'BEYOND_ACARYA_ACCEPTANCE_v18.json',
        capability_content_hash: historicalV18.capability_content_hash,
        report_hash: historicalV18.report_hash,
      },
      capability_content_hash: historicalV19.capability_content_hash,
      report_hash: historicalV19.report_hash,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
    })
  })

  it('keeps the v20 source-successor artifact immutable after the combined fix round 1 advance', () => {
    const artifactBytes = readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v20.json',
      import.meta.url,
    ))
    const artifact = JSON.parse(artifactBytes.toString('utf8')) as Record<string, unknown>

    expect(`sha256:${createHash('sha256').update(artifactBytes).digest('hex')}`).toBe(historicalV20.artifact_hash)
    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v20',
      predecessor: {
        artifact: 'BEYOND_ACARYA_ACCEPTANCE_v19.json',
        capability_content_hash: historicalV19.capability_content_hash,
        report_hash: historicalV19.report_hash,
      },
      capability_content_hash: historicalV20.capability_content_hash,
      report_hash: historicalV20.report_hash,
      verdict: 'ACCEPTED_SOURCE_LOCAL',
    })
  })

  it('pins the v21 source-successor artifact to the current executable report without claiming live acceptance (combined fix round 1: DENS-F, DENS-A, WFIX-A, DISPIMG)', () => {
    const artifact = JSON.parse(readFileSync(new URL(
      '../../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v21.json',
      import.meta.url,
    ), 'utf8')) as Record<string, unknown>
    const report = evaluateBeyondAcaryaAcceptance(snapshot, BEYOND_ACARYA_ACCEPTANCE_CASES)
    const snapshotBytes = readFileSync(new URL('../../../generated/capability_knowledge.snapshot.json', import.meta.url))
    const snapshotFileSha256 = `sha256:${createHash('sha256').update(snapshotBytes).digest('hex')}`

    expect(artifact).toMatchObject({
      schema_version: 'madhav-purna-anvesana/beyond-acarya-acceptance/v21',
      predecessor: {
        artifact: 'BEYOND_ACARYA_ACCEPTANCE_v20.json',
        acceptance_version: 'beyond-acarya-source-acceptance-v2',
        capability_content_hash: historicalV20.capability_content_hash,
        report_hash: historicalV20.report_hash,
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
      // Combined fix round 1: DENS-A's descriptor text, DENS-F's contracts and the platform-mcp dispatch description moved source_catalog_fingerprint;
      // the snapshot is regenerated with its committed generated_at.
      evaluated_source_revision: '89378c92c393fc7ca2616a88db20860d891cc0ba',
    })
  })
})

import type { CapabilityKnowledgeSnapshot } from '../../retrieval/registry/knowledge/types'
import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import type { BeyondAcaryaAcceptanceCase } from './beyond_acarya_acceptance.corpus'
import { BEYOND_ACARYA_CORPUS_VERSION } from './beyond_acarya_acceptance.corpus'
import {
  compileInquiryContract,
  finalizeInquiryContract,
  recordInquiryExecution,
} from './compiler'
import { bindingForInquiryItem } from './managed_bridge'
import type { InquiryContract } from './types'

export const BEYOND_ACARYA_ACCEPTANCE_VERSION = 'beyond-acarya-source-acceptance-v1' as const
export const BEYOND_ACARYA_CLAIM_CEILING = 'SOURCE_SCOPE_COMPLETE_WITH_AUTHORITY_BOUND_REMAINDER' as const

function unique(values: readonly string[]): string[] {
  return [...new Set(values)].sort()
}

function selectedScuIds(contract: InquiryContract): string[] {
  return unique(contract.obligations.flatMap((obligation) => obligation.scu_ids))
}

function edgeKey(edge: NonNullable<InquiryContract['graph_traversal']>['steps'][number]): string {
  return `${edge.from_scu_id}|${edge.relation}|${edge.to_scu_id}`
}

function compileCase(snapshot: CapabilityKnowledgeSnapshot, item: BeyondAcaryaAcceptanceCase): InquiryContract {
  return compileInquiryContract({
    snapshot,
    chart_id: `source-acceptance:${item.case_id}`,
    question: item.question,
    scope_tuple: item.scope_tuple,
    ai_proposal: item.ai_proposal,
    execution_channel: 'platform_internal',
    max_iterations: 64,
    planning_budget: item.planning_budget ?? {
      max_search_hits: 32,
      max_graph_hops: 3,
      max_graph_nodes: 48,
      max_challenger_additions: 24,
    },
  })
}

function closeThroughVerifiedContinuations(
  snapshot: CapabilityKnowledgeSnapshot,
  contract: InquiryContract,
): {
  status: InquiryContract['status']
  status_reasons: readonly string[]
  iterations: number
  evidence_retained: boolean
  pagination_continuations: number
} {
  const ready = contract.plan_items.filter((item) => item.state === 'ready')
  let current = contract
  const retainedEvidence: string[] = []
  let paginationContinuations = 0
  for (const item of ready) {
    const binding = bindingForInquiryItem(snapshot, current, item.item_id)
    const evidence = (page: number) => `acceptance:${stableFingerprint({
        acceptance_version: BEYOND_ACARYA_ACCEPTANCE_VERSION,
        contract_id: contract.contract_id,
        item_id: item.item_id,
        page,
      })}`
    const positionPath = binding?.pagination_contract?.request_position_path
    if (positionPath) {
      const firstPageEvidence = evidence(1)
      retainedEvidence.push(firstPageEvidence)
      current = recordInquiryExecution(current, {
        item_id: item.item_id,
        disposition: 'served',
        evidence_refs: [firstPageEvidence],
        pagination: { semantics: binding.pagination, exhausted: false, next: 50 },
        request_position_path: positionPath,
      })
      current = recordInquiryExecution(current, {
        item_id: item.item_id,
        disposition: 'served',
        evidence_refs: [evidence(2)],
        pagination: { semantics: binding.pagination, exhausted: true, next: null },
        request_position_path: positionPath,
      })
      paginationContinuations += 1
    } else {
      current = recordInquiryExecution(current, {
        item_id: item.item_id,
        disposition: 'served',
        evidence_refs: [evidence(1)],
        pagination: { semantics: binding?.pagination ?? 'none', exhausted: true, next: null },
      })
    }
  }
  const finalized = finalizeInquiryContract(current)
  const finalEvidence = new Set(finalized.obligations.flatMap((obligation) => obligation.evidence_refs))
  return {
    status: finalized.status,
    status_reasons: finalized.status_reasons,
    iterations: finalized.iteration,
    evidence_retained: retainedEvidence.every((reference) => finalEvidence.has(reference)),
    pagination_continuations: paginationContinuations,
  }
}

function assessAbstention(snapshot: CapabilityKnowledgeSnapshot, firstCase: BeyondAcaryaAcceptanceCase) {
  const requiredFloor = firstCase.expected_required_scu_ids[0]!
  const missingFloorSnapshot: CapabilityKnowledgeSnapshot = {
    ...snapshot,
    scus: snapshot.scus.filter((scu) => scu.scu_id !== requiredFloor),
    edges: snapshot.edges.filter((edge) => edge.from_scu_id !== requiredFloor && edge.to_scu_id !== requiredFloor),
  }
  let missingFloorRejected = false
  try {
    compileCase(missingFloorSnapshot, firstCase)
  } catch (error) {
    missingFloorRejected = error instanceof Error && error.message.startsWith('INQUIRY_REQUIRED_FLOOR_MISSING:')
  }

  let cappedBlocked = false
  try {
    const capped = compileInquiryContract({
      snapshot,
      chart_id: 'source-acceptance:capped-frontier',
      question: 'Complete wealth outlook with every adjacent mechanism.',
      scope_tuple: firstCase.scope_tuple,
      execution_channel: 'platform_internal',
      max_iterations: 1,
      planning_budget: {
        max_search_hits: 1,
        max_graph_hops: 0,
        max_graph_nodes: 1,
        max_challenger_additions: 0,
      },
    })
    cappedBlocked = finalizeInquiryContract({ ...capped, iteration: capped.max_iterations }).status === 'BLOCKED'
  } catch (error) {
    cappedBlocked = error instanceof Error && error.message.startsWith('INQUIRY_REQUIRED_FLOOR_MISSING:')
  }

  let unavailableAbstained = false
  try {
    const unavailable = compileInquiryContract({
      snapshot,
      chart_id: 'source-acceptance:unavailable-channel',
      question: firstCase.question,
      scope_tuple: firstCase.scope_tuple,
      execution_channel: 'mcp_full',
      max_iterations: 1,
      planning_budget: {
        max_search_hits: 32,
        max_graph_hops: 3,
        max_graph_nodes: 48,
        max_challenger_additions: 24,
      },
    })
    let unavailableObserved = unavailable
    for (const item of unavailable.plan_items.filter((candidate) => candidate.state === 'ready')) {
      unavailableObserved = recordInquiryExecution(unavailableObserved, {
        item_id: item.item_id,
        disposition: 'served',
        evidence_refs: [`acceptance:${stableFingerprint({ item_id: item.item_id })}`],
        pagination: { semantics: 'none', exhausted: true, next: null },
      })
    }
    unavailableAbstained = finalizeInquiryContract({
      ...unavailableObserved,
      iteration: unavailableObserved.max_iterations,
    }).status !== 'COMPLETE'
  } catch (error) {
    unavailableAbstained = error instanceof Error && error.message.startsWith('INQUIRY_REQUIRED_FLOOR_MISSING:')
  }

  const cases = [missingFloorRejected, cappedBlocked, unavailableAbstained]
  return {
    passed: cases.every(Boolean),
    passed_cases: cases.filter(Boolean).length,
    total_cases: cases.length,
    cases: {
      missing_required_floor_rejected: missingFloorRejected,
      capped_material_frontier_blocked: cappedBlocked,
      unavailable_channel_abstained: unavailableAbstained,
    },
  }
}

/**
 * Deterministic source/local acceptance only. The corpus denominator is
 * curated outside the planner, and every metric remains distinct from expert
 * domain review, deployed route proof, and empirical answer quality.
 */
export function evaluateBeyondAcaryaAcceptance(
  snapshot: CapabilityKnowledgeSnapshot,
  cases: readonly BeyondAcaryaAcceptanceCase[],
) {
  if (cases.length === 0) throw new Error('BEYOND_ACARYA_ACCEPTANCE_CORPUS_EMPTY')
  const compiled = cases.map((item) => {
    try {
      return { item, contract: compileCase(snapshot, item), compile_error: null }
    } catch (error) {
      return {
        item,
        contract: null,
        compile_error: error instanceof Error ? error.message : 'INQUIRY_COMPILE_FAILED',
      }
    }
  })
  const caseResults = compiled.map(({ item, contract, compile_error }) => {
    if (contract === null) {
      return {
        case_id: item.case_id,
        ...(compile_error === null ? {} : { compile_error }),
        selected_scu_ids: [] as string[],
        missing_expected_scu_ids: [...item.expected_required_scu_ids],
        expected_route_scu_ids: [...item.expected_route_scu_ids],
        covered_route_scu_ids: [] as string[],
        missing_required_route_scu_ids: [...item.expected_route_scu_ids],
        missing_edge_keys: [...item.expected_edge_keys],
        missing_novel_scu_ids: [...item.expected_novel_scu_ids],
        long_inquiry: null,
      }
    }
    const selected = new Set(selectedScuIds(contract))
    const traversedEdges = new Set(contract.graph_traversal?.steps.map(edgeKey) ?? [])
    const missingExpected = item.expected_required_scu_ids.filter((scuId) => !selected.has(scuId))
    const coveredRoutes = item.expected_route_scu_ids.filter((scuId) => contract.plan_items.some((planItem) =>
      planItem.scu_id === scuId && planItem.binding_id !== null && planItem.state === 'ready'))
    const coveredEdges = item.expected_edge_keys.filter((expected) => traversedEdges.has(expected))
    const missingNovel = item.expected_novel_scu_ids.filter((scuId) => !selected.has(scuId))
    return {
      case_id: item.case_id,
      ...(compile_error === null ? {} : { compile_error }),
      selected_scu_ids: [...selected].sort(),
      missing_expected_scu_ids: missingExpected,
      expected_route_scu_ids: [...item.expected_route_scu_ids],
      covered_route_scu_ids: coveredRoutes,
      missing_required_route_scu_ids: item.expected_route_scu_ids.filter((scuId) => !coveredRoutes.includes(scuId)),
      missing_edge_keys: item.expected_edge_keys.filter((expected) => !coveredEdges.includes(expected)),
      missing_novel_scu_ids: missingNovel,
      long_inquiry: item.exercise_long_inquiry
        ? closeThroughVerifiedContinuations(snapshot, contract)
        : null,
    }
  })

  const expectedConcepts = cases.reduce((total, item) => total + item.expected_required_scu_ids.length, 0)
  const omittedConcepts = caseResults.reduce((total, item) => total + item.missing_expected_scu_ids.length, 0)
  const requiredRouteDenominator = cases.reduce((total, item) => total + item.expected_route_scu_ids.length, 0)
  const coveredRoutes = caseResults.reduce((total, item) => total + item.covered_route_scu_ids.length, 0)
  const expectedEdges = cases.reduce((total, item) => total + item.expected_edge_keys.length, 0)
  const missingEdges = caseResults.reduce((total, item) => total + item.missing_edge_keys.length, 0)
  const expectedNovel = cases.reduce((total, item) => total + item.expected_novel_scu_ids.length, 0)
  const missingNovel = caseResults.reduce((total, item) => total + item.missing_novel_scu_ids.length, 0)
  const longInquiryCaseIds = new Set(cases.filter((item) => item.exercise_long_inquiry).map((item) => item.case_id))
  const longInquiryCases = caseResults.filter((item) => longInquiryCaseIds.has(item.case_id))
  const completedLongInquiries = longInquiryCases.filter((item) => item.long_inquiry?.status === 'COMPLETE'
    && item.long_inquiry.pagination_continuations >= 1
    && item.long_inquiry.evidence_retained)
  const blockedLongInquiries = longInquiryCases.filter((item) => !completedLongInquiries.includes(item))
  const abstention = assessAbstention(snapshot, cases[0]!)

  const metrics = {
    novel_combination_suite: {
      passed: missingNovel === 0,
      cases: cases.length,
      expected_novel_capabilities: expectedNovel,
      missing_novel_capabilities: missingNovel,
    },
    omission_rate: {
      passed: omittedConcepts === 0,
      omitted: omittedConcepts,
      expected: expectedConcepts,
      rate: expectedConcepts === 0 ? 1 : omittedConcepts / expectedConcepts,
    },
    route_coverage: {
      passed: coveredRoutes === requiredRouteDenominator,
      covered: coveredRoutes,
      expected: requiredRouteDenominator,
      rate: requiredRouteDenominator === 0 ? 0 : coveredRoutes / requiredRouteDenominator,
    },
    semantic_edge_coverage: {
      passed: missingEdges === 0,
      covered: expectedEdges - missingEdges,
      expected: expectedEdges,
      rate: expectedEdges === 0 ? 0 : (expectedEdges - missingEdges) / expectedEdges,
    },
    long_inquiry_closure: {
      passed: completedLongInquiries.length === longInquiryCases.length && longInquiryCases.length > 0,
      completed_cases: completedLongInquiries.length,
      total_cases: longInquiryCases.length,
      blocked_case_ids: blockedLongInquiries.map((item) => item.case_id),
      minimum_iterations_observed: Math.min(...longInquiryCases.map((item) => item.long_inquiry?.iterations ?? 0)),
      pagination_continuations: longInquiryCases.reduce((total, item) =>
        total + (item.long_inquiry?.pagination_continuations ?? 0), 0),
      retained_earlier_evidence: longInquiryCases.every((item) => item.long_inquiry?.evidence_retained),
    },
    abstention_quality: abstention,
  }
  const passed = Object.values(metrics).every((metric) => metric.passed)
  const normalized = {
    acceptance_version: BEYOND_ACARYA_ACCEPTANCE_VERSION,
    corpus_version: BEYOND_ACARYA_CORPUS_VERSION,
    evidence_kind: 'synthetic_source_local' as const,
    claim_ceiling: BEYOND_ACARYA_CLAIM_CEILING,
    empirical_answer_quality: 'NOT_RUN' as const,
    expert_domain_review: 'REQUIRED_BEFORE_EMPIRICAL_ACCEPTANCE' as const,
    production_validation: 'NOT_RUN' as const,
    capability_content_hash: snapshot.content_hash,
    metrics,
    cases: caseResults,
    passed,
  }
  return { ...normalized, report_hash: stableFingerprint(normalized) }
}

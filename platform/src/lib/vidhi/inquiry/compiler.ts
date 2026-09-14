import type { CapabilityKnowledgeSnapshot, ChartCapabilityOverlay, ExecutionChannel } from '../../retrieval/registry/knowledge/types'
import { assertOverlayCompatibility } from '../../retrieval/registry/knowledge/overlay'
import { searchSemanticCapabilities } from '../../retrieval/registry/knowledge/query'
import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import {
  INQUIRY_CONTRACT_VERSION,
  type AiInquiryProposal,
  type InquiryContract,
  type InquiryClosureReceipt,
  type InquiryObservation,
  type InquiryObligation,
  type InquiryPlanningBudget,
  type InquiryPlanningBudgetReceipt,
  type InquiryPlanItem,
  type InquiryScopeTuple,
  type InquiryValidationResult,
  type MaterialFrontierItem,
} from './types'
import type { InquiryPaginationReceipt } from './pagination'
import { traverseCapabilityGraph, sourceBackedEdge } from './graph_traversal'
import { normalizeInquiryScope } from './intent_normalization'
import { challengeInquirySelection } from './omission_challenger'

export const INQUIRY_COMPILER_VERSION = '2.0.0'

const DOMAIN_FLOORS: Readonly<Record<string, readonly string[]>> = {
  wealth_deepdive: [
    'scu.finance.prosperity_assessment',
    'scu.bodha.mechanism.network',
    'scu.catalog.get_divisionals',
    'scu.yoga.firing_and_cancellation',
    'scu.kala.temporal_activation',
    'scu.catalog.get_dashas',
    'scu.catalog.query_planet_transit',
    'scu.catalog.query_classical_texts',
  ],
  career_deepdive: ['scu.catalog.assess_career'],
  health_deepdive: ['scu.catalog.assess_health'],
  marriage_deepdive: ['scu.catalog.assess_marriage'],
  progeny_deepdive: ['scu.catalog.query_domain_reading'],
  education_deepdive: ['scu.catalog.query_domain_reading'],
  spirituality_deepdive: ['scu.catalog.query_domain_reading'],
  dasha_timing: ['scu.catalog.get_dashas'],
  transit_analysis: ['scu.catalog.query_planet_transit'],
  yoga_identification: ['scu.yoga.firing_and_cancellation'],
  planet_strength: ['scu.catalog.get_strength'],
  house_analysis: ['scu.catalog.judgment_query'],
  remedy_lookup: ['scu.catalog.query_remedies_for_chart'],
  panchanga: ['scu.catalog.get_panchanga'],
  classical_rule: ['scu.catalog.query_classical_texts'],
  chart_overview: ['scu.catalog.query_chart_gestalt'],
  prediction_calibration: ['scu.catalog.query_calibration'],
  domain_assessment: ['scu.catalog.query_domain_reading'],
  unknown: ['scu.catalog.intent_classify'],
}

function unique<T>(items: readonly T[]): T[] { return [...new Set(items)] }

function normalizeQuestion(question: string): string {
  return question.trim().replace(/\s+/g, ' ')
}

function normalizeAiProposal(ai: AiInquiryProposal | undefined): AiInquiryProposal | undefined {
  if (!ai) return undefined
  return {
    question_facets: ai.question_facets.map((facet) => ({
      ...facet,
      label: facet.label.trim(),
      terms: unique(facet.terms.map((term) => term.trim()).filter(Boolean)).sort(),
    })).sort((a, b) => stableFingerprint(a).localeCompare(stableFingerprint(b))).slice(0, 16),
    uncommon_adjacencies: ai.uncommon_adjacencies.map((adjacency) => ({
      ...adjacency,
      rationale: adjacency.rationale.trim(),
    })).sort((a, b) => stableFingerprint(a).localeCompare(stableFingerprint(b))).slice(0, 16),
    hypotheses: unique(ai.hypotheses.map((hypothesis) => hypothesis.trim()).filter(Boolean)).sort().slice(0, 16),
  }
}

function clamp(value: number | undefined, fallback: number, min: number, max: number): number {
  return Math.max(min, Math.min(Math.trunc(value ?? fallback), max))
}

function planningBudget(scope: InquiryScopeTuple, requested?: Partial<InquiryPlanningBudget>): InquiryPlanningBudget {
  const panoramic = scope.width === 'panoramic'
  const deep = scope.depth === 'deepdive'
  return {
    max_search_hits: clamp(requested?.max_search_hits, panoramic ? 20 : 12, 1, 32),
    max_graph_hops: clamp(requested?.max_graph_hops, deep ? 2 : scope.depth === 'retrieval' ? 0 : 1, 0, 3),
    max_graph_nodes: clamp(requested?.max_graph_nodes, panoramic ? 24 : 16, 1, 48),
    max_challenger_additions: clamp(requested?.max_challenger_additions, deep ? 12 : 8, 0, 24),
  }
}

function deterministicFloor(snapshot: CapabilityKnowledgeSnapshot, scope: InquiryScopeTuple): string[] {
  const domainAnchor = scope.intent === 'domain_assessment' && scope.domains.length === 1
    ? ({ wealth: 'scu.finance.prosperity_assessment', career: 'scu.catalog.assess_career',
      health: 'scu.catalog.assess_health', marriage: 'scu.catalog.assess_marriage' } as const)[scope.domains[0] as 'wealth' | 'career' | 'health' | 'marriage']
    : undefined
  const floor = domainAnchor ? [domainAnchor] : [...(DOMAIN_FLOORS[scope.intent] ?? DOMAIN_FLOORS.unknown!)]
  const available = new Set(snapshot.scus.map((scu) => scu.scu_id))
  const missing = floor.filter((scuId) => !available.has(scuId))
  if (missing.length) throw new Error(`INQUIRY_REQUIRED_FLOOR_MISSING:${missing.join(',')}`)
  return floor
}

function makeObligation(index: number, args: Omit<InquiryObligation, 'obligation_id' | 'disposition' | 'evidence_refs' | 'gap_reason'>): InquiryObligation {
  return { obligation_id: `obl-${String(index + 1).padStart(3, '0')}`, ...args, disposition: 'pending', evidence_refs: [], gap_reason: null }
}

function semanticObligationProjection(obligations: readonly InquiryObligation[]) {
  return obligations.map((obligation) => ({
    ...obligation,
    disposition: 'pending' as const,
    evidence_refs: [] as readonly string[],
    gap_reason: null,
  }))
}

function semanticNormalizationProjection(receipt: InquiryContract['scope_normalization']) {
  return receipt ? {
    normalization_version: receipt.normalization_version,
    normalized_scope_hash: receipt.normalized_scope_hash,
  } : undefined
}

function selectedScus(args: {
  snapshot: CapabilityKnowledgeSnapshot
  question: string
  scope: InquiryScopeTuple
  ai?: AiInquiryProposal
  budget: InquiryPlanningBudget
}): {
  selected: string[]
  obligations: InquiryObligation[]
  floor_nodes_selected: number
  search_hits_considered: number
  ai_adjacency_nodes_selected: number
  search_truncated: boolean
  planning_frontier: readonly Omit<MaterialFrontierItem, 'frontier_id' | 'disposition'>[]
} {
  const availableIds = new Set(args.snapshot.scus.map((scu) => scu.scu_id))
  const floor = deterministicFloor(args.snapshot, args.scope)
  const rawQueryHits = searchSemanticCapabilities(
    args.snapshot,
    `${args.question} ${args.scope.intent} ${args.scope.domains.join(' ')}`,
    100,
  )
  const facetHits = (args.ai?.question_facets ?? []).map((facet) => ({
    facet,
    hits: searchSemanticCapabilities(args.snapshot, facet.terms.join(' '), 3).map((hit) => hit.scu_id),
  }))
  const floorSet = new Set(floor)
  const searchCandidates = unique([
    ...facetHits.filter(({ facet }) => facet.materiality === 'required').flatMap(({ hits }) => hits),
    ...rawQueryHits.map((hit) => hit.scu_id),
    ...facetHits.filter(({ facet }) => facet.materiality === 'supporting').flatMap(({ hits }) => hits),
  ]).filter((scuId) => !floorSet.has(scuId))
  const admittedSearch = searchCandidates.slice(0, args.budget.max_search_hits)
  const admittedSearchSet = new Set(admittedSearch)
  const obligations: InquiryObligation[] = []
  const planningFrontier: Array<Omit<MaterialFrontierItem, 'frontier_id' | 'disposition'>> = []
  for (const scuId of floor) {
    obligations.push(makeObligation(obligations.length, { label: `Required capability: ${scuId}`, source: 'deterministic_floor', materiality: 'required', scu_ids: [scuId], rationale: `Deterministic floor for ${args.scope.intent}.` }))
  }
  for (const { facet, hits: rawHits } of facetHits) {
    const hits = rawHits.filter((scuId) => floorSet.has(scuId) || admittedSearchSet.has(scuId))
    if (hits.length) obligations.push(makeObligation(obligations.length, { label: facet.label, source: 'ai_decomposition', materiality: facet.materiality, scu_ids: hits, rationale: 'AI-proposed question facet; capability ids were deterministically resolved against the snapshot.' }))
    if (facet.materiality === 'required') {
      for (const scuId of rawHits.filter((scuId) => !floorSet.has(scuId) && !admittedSearchSet.has(scuId))) {
        planningFrontier.push({
          discovered_from: `ai_facet:${facet.label}`,
          scu_id: scuId,
          materiality: 'required',
          reason: 'search_hit_budget_exhausted',
          source_ref: `ai-facet:${stableFingerprint(facet)}`,
        })
      }
    }
  }
  const selected = unique([...floor, ...admittedSearch, ...obligations.flatMap((obligation) => obligation.scu_ids)]).filter((id) => availableIds.has(id))
  const selectedSet = new Set(selected)
  let adjacencyAdditions = 0
  for (const adjacency of args.ai?.uncommon_adjacencies ?? []) {
    const edge = sourceBackedEdge(args.snapshot, adjacency.from_scu_id, adjacency.to_scu_id)
    if (!selectedSet.has(adjacency.from_scu_id) || !availableIds.has(adjacency.to_scu_id) || selectedSet.has(adjacency.to_scu_id) || !edge) continue
    if (adjacencyAdditions >= args.budget.max_graph_nodes) {
      if (edge.relation === 'requires' || edge.relation === 'contradicts') planningFrontier.push({
        discovered_from: adjacency.from_scu_id,
        scu_id: adjacency.to_scu_id,
        materiality: 'required',
        reason: 'ai_adjacency_budget_exhausted',
        source_ref: edge.source_ref!,
      })
      continue
    }
    obligations.push(makeObligation(obligations.length, {
      label: `Validated adjacency: ${adjacency.to_scu_id}`,
      source: 'ai_decomposition',
      materiality: edge.relation === 'requires' || edge.relation === 'contradicts' ? 'required' : 'supporting',
      scu_ids: [adjacency.to_scu_id],
      rationale: `AI proposed a source-backed ${edge.relation} adjacency from ${adjacency.from_scu_id}; ${edge.source_ref}. ${adjacency.rationale}`,
    }))
    selected.push(adjacency.to_scu_id)
    selectedSet.add(adjacency.to_scu_id)
    adjacencyAdditions += 1
  }
  return {
    selected,
    obligations,
    floor_nodes_selected: floor.length,
    search_hits_considered: admittedSearch.length,
    ai_adjacency_nodes_selected: adjacencyAdditions,
    search_truncated: searchCandidates.length > args.budget.max_search_hits,
    planning_frontier: planningFrontier,
  }
}

function planFor(
  snapshot: CapabilityKnowledgeSnapshot,
  obligations: readonly InquiryObligation[],
  chartId: string,
  question: string,
  scope: InquiryScopeTuple,
  executionChannel: ExecutionChannel,
  overlay?: ChartCapabilityOverlay | null,
): InquiryPlanItem[] {
  const byId = new Map(snapshot.scus.map((scu) => [scu.scu_id, scu]))
  const availabilityByScu = new Map(overlay?.availability.map((item) => [item.scu_id, item]) ?? [])
  const plan: InquiryPlanItem[] = []
  for (const obligation of obligations) {
    for (const scuId of obligation.scu_ids) {
      const scu = byId.get(scuId)
      if (!scu) continue
      const existingIndex = plan.findIndex((item) => item.scu_id === scuId)
      if (existingIndex >= 0) {
        const existing = plan[existingIndex]!
        plan[existingIndex] = { ...existing, obligation_ids: unique([...existing.obligation_ids, obligation.obligation_id]) }
        continue
      }
      const channelBindings = scu.bindings.filter((candidate) => candidate.executable
        && candidate.kind === 'registry_capability'
        && (candidate.execution_channels ?? ['platform_internal']).includes(executionChannel))
      const binding = channelBindings.find((candidate) => candidate.relation === 'primary') ?? channelBindings[0] ?? null
      const itemArgs: Record<string, unknown> = {}
      if (binding?.input_contract['chart_id']) itemArgs['chart_id'] = chartId
      if (binding?.input_contract['question']) itemArgs['question'] = question
      if (binding?.input_contract['query']) itemArgs['query'] = question
      if (binding?.input_contract['domain']) itemArgs['domain'] = scope.domains[0]
      if (binding?.input_contract['domains']) itemArgs['domains'] = scope.domains
      const unresolvedRequired = binding
        ? Object.entries(binding.input_contract).filter(([key, declaration]) => declaration.endsWith(':required') && itemArgs[key] === undefined).map(([key]) => key)
        : []
      const availability = availabilityByScu.get(scuId)
      const overlayAllowsBinding = !overlay || Boolean(binding
        && availability
        && ['available', 'partial'].includes(availability.state)
        && availability.available_binding_ids.includes(binding.binding_id))
      const executable = Boolean(binding && unresolvedRequired.length === 0 && overlayAllowsBinding)
      const blockedReason = !binding
        ? `No executable ${executionChannel} binding is declared.`
        : unresolvedRequired.length > 0
          ? `Required binding arguments are unresolved: ${unresolvedRequired.join(', ')}.`
          : !overlayAllowsBinding
            ? availability?.gaps.join('; ') || 'The chart/build overlay does not prove this binding available.'
            : null
      if (executable && binding) {
        const duplicateIndex = plan.findIndex((item) => item.binding_id === binding.binding_id
          && stableFingerprint(item.args) === stableFingerprint(itemArgs))
        if (duplicateIndex >= 0) {
          const duplicate = plan[duplicateIndex]!
          plan[duplicateIndex] = {
            ...duplicate,
            obligation_ids: unique([...duplicate.obligation_ids, ...obligations.filter((candidate) => candidate.scu_ids.includes(scuId)).map((candidate) => candidate.obligation_id)]),
          }
          continue
        }
      }
      plan.push({
        item_id: `item-${String(plan.length + 1).padStart(3, '0')}`,
        obligation_ids: obligations.filter((candidate) => candidate.scu_ids.includes(scuId)).map((candidate) => candidate.obligation_id),
        scu_id: scuId,
        binding_id: executable ? binding!.binding_id : null,
        args: itemArgs,
        depends_on: [],
        state: executable ? 'ready' : 'blocked',
        blocked_reason: blockedReason,
        observation: null,
      })
    }
  }
  return plan
}

export function compileInquiryContract(args: {
  snapshot: CapabilityKnowledgeSnapshot
  overlay?: ChartCapabilityOverlay | null
  chart_id: string
  question: string
  scope_tuple: InquiryScopeTuple
  ai_proposal?: AiInquiryProposal
  max_iterations?: number
  execution_channel?: ExecutionChannel
  planning_budget?: Partial<InquiryPlanningBudget>
}): InquiryContract {
  const question = normalizeQuestion(args.question)
  const normalization = normalizeInquiryScope(args.scope_tuple)
  const scope = normalization.scope
  const budget = planningBudget(scope, args.planning_budget)
  const aiProposal = normalizeAiProposal(args.ai_proposal)
  const executionChannel = args.execution_channel ?? 'platform_internal'
  if (args.overlay) assertOverlayCompatibility(args.snapshot, args.overlay, args.chart_id)
  const selection = selectedScus({ snapshot: args.snapshot, question, scope, ai: aiProposal, budget })
  const remainingGraphNodeBudget = Math.max(0, budget.max_graph_nodes - selection.ai_adjacency_nodes_selected)
  const traversal = traverseCapabilityGraph(args.snapshot, selection.selected, {
    max_hops: budget.max_graph_hops,
    max_nodes: selection.selected.length + remainingGraphNodeBudget,
  })
  const selected = [...traversal.selected_scu_ids]
  const selectedSet = new Set(selected)

  for (const step of traversal.steps) {
    const alreadyCovered = selection.obligations.some((obligation) => obligation.scu_ids.includes(step.to_scu_id)
      && (step.materiality === 'supporting' || obligation.materiality === 'required'))
    if (alreadyCovered) continue
    selection.obligations.push(makeObligation(selection.obligations.length, {
      label: `Graph ${step.relation}: ${step.to_scu_id}`,
      source: 'graph_traversal',
      materiality: step.materiality,
      scu_ids: [step.to_scu_id],
      rationale: `Source-backed hop ${step.from_scu_id} ${step.relation} ${step.to_scu_id}; ${step.source_ref}.`,
    }))
  }

  const challenge = challengeInquirySelection({ snapshot: args.snapshot, question, scope, selected_scu_ids: selected })
  const missingTargets = unique(challenge.findings.map((finding) => finding.missing_scu_id).filter((scuId) => !selectedSet.has(scuId)))
  const challengerTargets = missingTargets.slice(0, budget.max_challenger_additions)
  for (const scuId of challengerTargets) {
    const relevant = challenge.findings.filter((finding) => finding.missing_scu_id === scuId)
    selection.obligations.push(makeObligation(selection.obligations.length, {
      label: `Independent omission challenge: ${scuId}`,
      source: 'omission_challenger',
      materiality: relevant.some((finding) => finding.severity === 'material') ? 'required' : 'supporting',
      scu_ids: [scuId],
      rationale: relevant.map((finding) => `${finding.rule_id}: ${finding.rationale} [${finding.source_ref}]`).join(' '),
    }))
    selected.push(scuId)
    selectedSet.add(scuId)
  }

  // If no named domain floor applies, search-derived capabilities still become
  // explicit obligations rather than disappearing into an opaque tool list.
  for (const scuId of selected) {
    if (!selection.obligations.some((obligation) => obligation.scu_ids.includes(scuId))) {
      selection.obligations.push(makeObligation(selection.obligations.length, { label: `Question-bearing capability: ${scuId}`, source: 'deterministic_floor', materiality: 'supporting', scu_ids: [scuId], rationale: 'Deterministic semantic search match.' }))
    }
  }

  const materialFrontier: MaterialFrontierItem[] = []
  const upsertFrontier = (candidate: Omit<MaterialFrontierItem, 'frontier_id'>): void => {
    const index = materialFrontier.findIndex((item) => item.scu_id === candidate.scu_id)
    if (index < 0) {
      materialFrontier.push({ frontier_id: `frontier-${String(materialFrontier.length + 1).padStart(3, '0')}`, ...candidate })
      return
    }
    const existing = materialFrontier[index]!
    const sourceRefs = unique([existing.source_ref, candidate.source_ref]
      .filter((sourceRef): sourceRef is string => Boolean(sourceRef))).sort()
    materialFrontier[index] = {
      ...existing,
      materiality: existing.materiality === 'required' || candidate.materiality === 'required' ? 'required' : 'supporting',
      reason: unique([existing.reason, candidate.reason]).sort().join(' | '),
      ...(sourceRefs.length ? { source_ref: sourceRefs.join(' | ') } : {}),
    }
  }
  for (const frontier of selection.planning_frontier.filter((item) => !selectedSet.has(item.scu_id))) {
    upsertFrontier({ ...frontier, disposition: 'open' })
  }
  for (const frontier of traversal.frontier.filter((item) => !selectedSet.has(item.to_scu_id))) {
    upsertFrontier({
      discovered_from: frontier.from_scu_id,
      scu_id: frontier.to_scu_id,
      materiality: frontier.materiality,
      reason: frontier.reason,
      disposition: 'open',
      source_ref: frontier.source_ref,
    })
  }
  for (const finding of challenge.findings.filter((item) => !selectedSet.has(item.missing_scu_id))) {
    upsertFrontier({
      discovered_from: 'independent_omission_challenger',
      scu_id: finding.missing_scu_id,
      materiality: finding.severity === 'material' ? 'required' : 'supporting',
      reason: `challenger_addition_budget_exhausted:${finding.rule_id}`,
      disposition: 'open',
      source_ref: finding.source_ref,
    })
  }

  const plan = planFor(args.snapshot, selection.obligations, args.chart_id, question, scope, executionChannel, args.overlay)
  const obligations = selection.obligations.map((obligation) => {
    const items = plan.filter((item) => item.obligation_ids.includes(obligation.obligation_id))
    if (items.length === 0 || items.some((item) => item.state !== 'blocked')) return obligation
    return {
      ...obligation,
      disposition: 'dark' as const,
      gap_reason: unique(items.map((item) => item.blocked_reason).filter((reason): reason is string => Boolean(reason))).join('; ') || 'No executable plan item is available.',
    }
  })
  const budgetBase = {
    ...budget,
    floor_nodes_selected: selection.floor_nodes_selected,
    search_hits_considered: selection.search_hits_considered,
    ai_adjacency_nodes_selected: selection.ai_adjacency_nodes_selected,
    graph_seed_nodes: traversal.seed_scu_ids.length,
    graph_nodes_selected: traversal.selected_scu_ids.length,
    graph_expansion_nodes_selected: selection.ai_adjacency_nodes_selected
      + Math.max(0, traversal.selected_scu_ids.length - traversal.seed_scu_ids.length),
    graph_edges_followed: traversal.steps.length,
    challenger_findings: challenge.findings.length,
    challenger_additions: challengerTargets.length,
    frontier_items: materialFrontier.length,
    truncated: selection.search_truncated || materialFrontier.length > 0,
  }
  const budgetReceipt: InquiryPlanningBudgetReceipt = { ...budgetBase, budget_hash: stableFingerprint(budgetBase) }
  const semanticContractHash = stableFingerprint({
    contract_version: INQUIRY_CONTRACT_VERSION,
    compiler_version: INQUIRY_COMPILER_VERSION,
    question,
    scope_tuple: scope,
    capability_content_hash: args.snapshot.content_hash,
    obligations: semanticObligationProjection(obligations),
    omission_findings: challenge.findings,
    scope_normalization: semanticNormalizationProjection(normalization.receipt),
    graph_traversal: traversal,
    omission_challenge: challenge,
    planning_budget: budgetReceipt,
    material_frontier: materialFrontier,
  })
  const executionPlanHash = stableFingerprint({ semantic_contract_hash: semanticContractHash, chart_id: args.chart_id, execution_channel: executionChannel, plan_items: plan })
  const contractId = stableFingerprint({ semantic_contract_hash: semanticContractHash, execution_plan_hash: executionPlanHash })
  return {
    contract_version: INQUIRY_CONTRACT_VERSION,
    compiler_version: INQUIRY_COMPILER_VERSION,
    contract_id: contractId,
    semantic_contract_hash: semanticContractHash,
    execution_plan_hash: executionPlanHash,
    chart_id: args.chart_id,
    question,
    scope_tuple: scope,
    execution_channel: executionChannel,
    capability_compatibility_version: args.snapshot.compatibility_version,
    capability_content_hash: args.snapshot.content_hash,
    chart_availability_version: args.overlay?.overlay_version ?? null,
    chart_build_id: args.overlay?.build_id ?? null,
    obligations,
    plan_items: plan,
    material_frontier: materialFrontier,
    omission_findings: challenge.findings,
    ai_hypotheses: [...(aiProposal?.hypotheses ?? [])],
    status: 'INCOMPLETE',
    status_reasons: ['required_obligations_pending'],
    iteration: 0,
    // Iteration is an execution/expansion budget. The default must always fit
    // the initial deterministic plan plus four bounded retry/frontier passes.
    max_iterations: args.max_iterations === undefined
      ? Math.min(Math.max(plan.length + 4, 4), 64)
      : Math.max(1, Math.min(args.max_iterations, 64)),
    scope_normalization: normalization.receipt,
    graph_traversal: traversal,
    omission_challenge: challenge,
    planning_budget: budgetReceipt,
  }
}

/** Recompute the immutable authorization hashes from the original contract. */
export function inquiryAuthorizationHashes(contract: InquiryContract): {
  semantic_contract_hash: string
  execution_plan_hash: string
  contract_id: string
} {
  const semanticContractHash = stableFingerprint({
    contract_version: contract.contract_version,
    compiler_version: contract.compiler_version,
    question: contract.question,
    scope_tuple: contract.scope_tuple,
    capability_content_hash: contract.capability_content_hash,
    obligations: semanticObligationProjection(contract.obligations),
    omission_findings: contract.omission_findings,
    scope_normalization: semanticNormalizationProjection(contract.scope_normalization),
    graph_traversal: contract.graph_traversal,
    omission_challenge: contract.omission_challenge,
    planning_budget: contract.planning_budget,
    material_frontier: contract.material_frontier.filter((item) => item.discovered_from === 'independent_omission_challenger'
      || item.reason.startsWith('graph_') || item.reason.startsWith('challenger_')),
  })
  const executionPlanHash = stableFingerprint({
    semantic_contract_hash: semanticContractHash,
    chart_id: contract.chart_id,
    execution_channel: contract.execution_channel,
    plan_items: contract.plan_items,
  })
  return {
    semantic_contract_hash: semanticContractHash,
    execution_plan_hash: executionPlanHash,
    contract_id: stableFingerprint({ semantic_contract_hash: semanticContractHash, execution_plan_hash: executionPlanHash }),
  }
}

export function applyInquiryObservations(contract: InquiryContract, observations: readonly InquiryObservation[]): InquiryContract {
  const obsByItem = new Map(observations.map((observation) => [observation.item_id, observation]))
  const planItems = contract.plan_items.map((item) => {
    const observation = obsByItem.get(item.item_id)
    if (!observation) return item
    const prior = item.observation
    const disposition = observation.disposition === 'empty' && prior?.disposition === 'served'
      ? 'served'
      : observation.disposition
    return {
      ...item,
      state: 'observed' as const,
      observation: {
        disposition,
        evidence_refs: unique([...(prior?.evidence_refs ?? []), ...observation.evidence_refs]),
        gap_reason: observation.gap_reason ?? (disposition === 'served' || disposition === 'empty' ? null : prior?.gap_reason ?? null),
      },
    }
  })
  const obligations = contract.obligations.map((obligation) => {
    const items = planItems.filter((item) => item.obligation_ids.includes(obligation.obligation_id))
    if (items.length === 0 || items.some((item) => item.observation === null)) return obligation
    const itemObservations = items.flatMap((item) => item.observation ? [item.observation] : [])
    const failed = itemObservations.find((observation) => observation.disposition === 'failed')
    const dark = itemObservations.find((observation) => observation.disposition === 'dark')
    const disposition: InquiryObligation['disposition'] = failed ? 'failed' : dark ? 'dark' : itemObservations.some((observation) => observation.disposition === 'served') ? 'served' : 'empty'
    const gapReasons = unique(itemObservations.map((observation) => observation.gap_reason).filter((reason): reason is string => Boolean(reason)))
    return {
      ...obligation,
      disposition,
      evidence_refs: unique([...obligation.evidence_refs, ...itemObservations.flatMap((observation) => observation.evidence_refs)]),
      gap_reason: disposition === 'failed' || disposition === 'dark' ? gapReasons.join('; ') || 'No gap reason recorded.' : null,
    }
  })
  const existingFrontier = new Map(contract.material_frontier.map((item) => [item.scu_id, item]))
  for (const observation of observations) {
    const observedItem = contract.plan_items.find((item) => item.item_id === observation.item_id)
    if ((observation.discovered_frontier?.length ?? 0) === 0 && observedItem) {
      const existing = existingFrontier.get(observedItem.scu_id)
      if (existing?.discovered_from === observation.item_id && existing.disposition === 'open') {
        existingFrontier.set(observedItem.scu_id, { ...existing, disposition: 'absorbed' })
      }
    }
    for (const discovered of observation.discovered_frontier ?? []) {
      if (!existingFrontier.has(discovered.scu_id)) existingFrontier.set(discovered.scu_id, {
        frontier_id: `frontier-${String(existingFrontier.size + 1).padStart(3, '0')}`,
        discovered_from: observation.item_id,
        scu_id: discovered.scu_id,
        materiality: discovered.materiality,
        reason: discovered.reason,
        disposition: contract.iteration + 1 >= contract.max_iterations ? 'capped' : 'open',
      })
    }
  }
  return { ...contract, obligations, plan_items: planItems, material_frontier: [...existingFrontier.values()], iteration: contract.iteration + 1, status: 'INCOMPLETE', status_reasons: ['finalization_required'] }
}

/** Apply one server-observed execution and authorize only a verified continuation/retry. */
export function recordInquiryExecution(
  contract: InquiryContract,
  args: {
    item_id: string
    disposition: InquiryObservation['disposition']
    evidence_refs: readonly string[]
    gap_reason?: string
    pagination: InquiryPaginationReceipt
    request_position_path?: string
  },
): InquiryContract {
  const item = contract.plan_items.find((candidate) => candidate.item_id === args.item_id)
  if (!item) throw new Error('INQUIRY_UNKNOWN_PLAN_ITEM')
  const materiality = contract.obligations.some((obligation) => item.obligation_ids.includes(obligation.obligation_id)
    && obligation.materiality === 'required') ? 'required' as const : 'supporting' as const
  let observed = applyInquiryObservations(contract, [{
    item_id: item.item_id,
    disposition: args.disposition,
    evidence_refs: args.evidence_refs,
    gap_reason: args.gap_reason,
    ...(args.pagination.exhausted ? {} : {
      discovered_frontier: [{ scu_id: item.scu_id, materiality, reason: `Pagination frontier remains open (${String(args.pagination.next)}).` }],
    }),
  }])
  if (!args.pagination.exhausted && args.pagination.next !== 'unproven' && args.pagination.next !== null) {
    const bindingPositionKey = args.request_position_path?.split('.').at(-1)
    if (!bindingPositionKey) return observed
    observed = {
      ...observed,
      plan_items: observed.plan_items.map((candidate) => candidate.item_id === item.item_id
        ? { ...candidate, args: { ...candidate.args, [bindingPositionKey]: args.pagination.next }, state: 'ready' as const }
        : candidate),
    }
  } else if (args.disposition === 'failed' && observed.iteration < observed.max_iterations) {
    observed = {
      ...observed,
      plan_items: observed.plan_items.map((candidate) => candidate.item_id === item.item_id
        ? { ...candidate, state: 'ready' as const }
        : candidate),
    }
  }
  return observed
}

export function validateInquiryContract(contract: InquiryContract): InquiryValidationResult {
  const errors: string[] = []
  if (contract.compiler_version.startsWith('2.')) {
    if (!contract.scope_normalization) errors.push('compiler v2 contract lacks a scope normalization receipt')
    if (!contract.graph_traversal) errors.push('compiler v2 contract lacks a graph traversal receipt')
    if (!contract.omission_challenge) errors.push('compiler v2 contract lacks an omission challenge receipt')
    if (!contract.planning_budget) errors.push('compiler v2 contract lacks a planning budget receipt')
    if (contract.scope_normalization
      && contract.scope_normalization.normalized_scope_hash !== stableFingerprint(contract.scope_tuple)) {
      errors.push('scope normalization receipt does not match normalized scope')
    }
    if (contract.graph_traversal?.steps.some((step) => !step.edge_source || !step.source_ref)) {
      errors.push('graph traversal contains an unproven edge')
    }
    if (contract.graph_traversal) {
      const { traversal_hash: traversalHash, ...traversal } = contract.graph_traversal
      if (traversalHash !== stableFingerprint(traversal)) errors.push('graph traversal receipt hash mismatch')
    }
    if (contract.omission_challenge) {
      const challenge = {
        challenge_version: contract.omission_challenge.challenge_version,
        selected_scu_ids: contract.omission_challenge.selected_scu_ids,
        findings: contract.omission_challenge.findings,
      }
      if (contract.omission_challenge.challenge_hash !== stableFingerprint(challenge)) {
        errors.push('omission challenge receipt hash mismatch')
      }
    }
    if (contract.planning_budget) {
      const { budget_hash: budgetHash, ...budget } = contract.planning_budget
      if (budgetHash !== stableFingerprint(budget)) errors.push('planning budget receipt hash mismatch')
      if (budget.search_hits_considered > budget.max_search_hits) errors.push('search selection exceeded planning budget')
      if (budget.graph_expansion_nodes_selected > budget.max_graph_nodes) errors.push('graph expansion exceeded planning budget')
      if (contract.graph_traversal) {
        if (budget.graph_seed_nodes !== contract.graph_traversal.seed_scu_ids.length) errors.push('graph seed count does not match traversal receipt')
        if (budget.graph_nodes_selected !== contract.graph_traversal.selected_scu_ids.length) errors.push('graph node count does not match traversal receipt')
        const expectedExpansion = budget.ai_adjacency_nodes_selected
          + Math.max(0, contract.graph_traversal.selected_scu_ids.length - contract.graph_traversal.seed_scu_ids.length)
        if (budget.graph_expansion_nodes_selected !== expectedExpansion) errors.push('graph expansion count does not match traversal receipt')
      }
    }
  }
  const obligationIds = new Set<string>()
  for (const obligation of contract.obligations) {
    if (obligationIds.has(obligation.obligation_id)) errors.push(`duplicate obligation ${obligation.obligation_id}`)
    obligationIds.add(obligation.obligation_id)
    if (obligation.materiality === 'required' && ['served', 'empty'].includes(obligation.disposition) && obligation.evidence_refs.length === 0) errors.push(`required obligation ${obligation.obligation_id} lacks evidence refs`)
    if (obligation.materiality === 'required' && ['dark', 'failed'].includes(obligation.disposition) && !obligation.gap_reason) errors.push(`required gap ${obligation.obligation_id} lacks a reason`)
  }
  for (const item of contract.plan_items) for (const id of item.obligation_ids) if (!obligationIds.has(id)) errors.push(`plan item ${item.item_id} references unknown obligation ${id}`)
  return { valid: errors.length === 0, errors }
}

export function finalizeInquiryContract(contract: InquiryContract): InquiryContract {
  const validation = validateInquiryContract(contract)
  const pending = contract.obligations.filter((obligation) => obligation.materiality === 'required' && obligation.disposition === 'pending')
  const materialGaps = contract.obligations.filter((obligation) => obligation.materiality === 'required' && ['dark', 'failed'].includes(obligation.disposition))
  const openFrontier = contract.material_frontier.filter((item) => item.materiality === 'required' && item.disposition === 'open')
  const cappedFrontier = contract.material_frontier.filter((item) => item.materiality === 'required' && item.disposition === 'capped')
  const reasons = [...validation.errors]
  if (pending.length) reasons.push(`${pending.length} required obligations pending`)
  if (materialGaps.length) reasons.push(`${materialGaps.length} required obligations failed or are dark`)
  if (openFrontier.length) reasons.push(`${openFrontier.length} material frontier items open`)
  if (cappedFrontier.length) reasons.push(`${cappedFrontier.length} material frontier items capped before exhaustion proof`)
  const exhausted = cappedFrontier.length > 0
    || (contract.iteration >= contract.max_iterations && (pending.length > 0 || materialGaps.length > 0 || openFrontier.length > 0))
  if (exhausted) reasons.push('iteration cap reached before material frontier closure')
  return {
    ...contract,
    status: reasons.length === 0 ? 'COMPLETE' : exhausted ? 'BLOCKED' : 'INCOMPLETE',
    status_reasons: reasons.length ? reasons : ['all required obligations dispositioned; material frontier closed'],
  }
}

/** Fail closed when the chart/build overlay changes during managed or raw retrieval. */
export function failInquiryForOverlayDrift(contract: InquiryContract): InquiryContract {
  const invalidated = applyInquiryObservations(contract, contract.plan_items
    .filter((item) => item.binding_id !== null)
    .map((item) => ({
      item_id: item.item_id,
      disposition: 'failed' as const,
      evidence_refs: [],
      gap_reason: 'CAPABILITY_OVERLAY_CHANGED_DURING_DISPATCH',
    })))
  const finalized = finalizeInquiryContract({ ...invalidated, iteration: invalidated.max_iterations })
  return {
    ...finalized,
    status: 'BLOCKED',
    status_reasons: unique([...finalized.status_reasons, 'chart capability overlay changed during dispatch']),
  }
}

export function buildInquiryClosureReceipt(contract: InquiryContract): InquiryClosureReceipt {
  const normalized = {
    receipt_version: 'inquiry-closure-v1' as const,
    contract_id: contract.contract_id,
    semantic_contract_hash: contract.semantic_contract_hash,
    execution_plan_hash: contract.execution_plan_hash,
    capability_content_hash: contract.capability_content_hash,
    chart_availability_version: contract.chart_availability_version,
    chart_build_id: contract.chart_build_id,
    status: contract.status,
    status_reasons: [...contract.status_reasons],
    obligation_coverage: contract.obligations.map((obligation) => ({
      obligation_id: obligation.obligation_id,
      materiality: obligation.materiality,
      disposition: obligation.disposition,
      evidence_refs: [...obligation.evidence_refs],
      gap_reason: obligation.gap_reason,
    })),
    residual_frontier: contract.material_frontier.filter((item) => item.disposition === 'open' || item.disposition === 'capped'),
    scope_normalization: contract.scope_normalization,
    graph_traversal_hash: contract.graph_traversal?.traversal_hash,
    omission_challenge_hash: contract.omission_challenge?.challenge_hash,
    planning_budget: contract.planning_budget,
  }
  return { ...normalized, receipt_hash: stableFingerprint(normalized) }
}

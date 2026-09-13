import type { CapabilityKnowledgeSnapshot, ChartCapabilityOverlay } from '../../retrieval/registry/knowledge/types'
import { assertOverlayCompatibility } from '../../retrieval/registry/knowledge/overlay'
import { searchSemanticCapabilities } from '../../retrieval/registry/knowledge/query'
import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import {
  INQUIRY_CONTRACT_VERSION,
  type AiInquiryProposal,
  type InquiryContract,
  type InquiryObservation,
  type InquiryObligation,
  type InquiryPlanItem,
  type InquiryScopeTuple,
  type InquiryValidationResult,
  type MaterialFrontierItem,
  type OmissionFinding,
} from './types'

export const INQUIRY_COMPILER_VERSION = '1.0.0'

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
}

const OMISSION_RULES = [
  { rule_id: 'OMIT-BHAVA-BHAVAT', terms: ['house', 'bhava', 'wealth', 'career', 'marriage', 'health'], scu_id: 'scu.catalog.judgment_query', rationale: 'Material domain reads require bhāvat-bhāvam / bhava-lord cross-checks.' },
  { rule_id: 'OMIT-YOGA-CANCEL', terms: ['yoga', 'wealth', 'prosperity'], scu_id: 'scu.yoga.firing_and_cancellation', rationale: 'A yoga label is incomplete without firing, strength, and cancellation.' },
  { rule_id: 'OMIT-VARGA-CONTRA', terms: ['wealth', 'career', 'marriage', 'health', 'varga'], scu_id: 'scu.catalog.get_divisionals', rationale: 'Operative-varga contradiction can reverse a natal-only claim.' },
  { rule_id: 'OMIT-INHIBITOR', terms: ['wealth', 'prosperity', 'success', 'outlook'], scu_id: 'scu.bodha.mechanism.network', rationale: 'Supportive promise must be checked against inhibiting mechanisms.' },
  { rule_id: 'OMIT-TEMPORAL-PREREQ', terms: ['now', 'current', 'when', 'timing', 'period', 'outlook', 'wealth'], scu_id: 'scu.kala.temporal_activation', rationale: 'Current or prospective claims require temporal prerequisites.' },
  { rule_id: 'OMIT-CROSS-DOMAIN', terms: ['complete', 'deep', 'prosperity', 'life'], scu_id: 'scu.catalog.query_contradictions', rationale: 'Deep inquiry must surface cross-domain contradiction and convergence.' },
] as const

function unique<T>(items: readonly T[]): T[] { return [...new Set(items)] }

function makeObligation(index: number, args: Omit<InquiryObligation, 'obligation_id' | 'disposition' | 'evidence_refs' | 'gap_reason'>): InquiryObligation {
  return { obligation_id: `obl-${String(index + 1).padStart(3, '0')}`, ...args, disposition: 'pending', evidence_refs: [], gap_reason: null }
}

function selectedScus(args: {
  snapshot: CapabilityKnowledgeSnapshot
  question: string
  scope: InquiryScopeTuple
  ai?: AiInquiryProposal
}): { selected: string[]; obligations: InquiryObligation[] } {
  const availableIds = new Set(args.snapshot.scus.map((scu) => scu.scu_id))
  const floorKey = args.scope.intent === 'domain_assessment'
    && ['deep', 'deepdive'].includes(args.scope.depth)
    && args.scope.domains.includes('wealth')
    ? 'wealth_deepdive'
    : args.scope.intent
  const floor = DOMAIN_FLOORS[floorKey] ?? []
  const queryHits = searchSemanticCapabilities(args.snapshot, `${args.question} ${args.scope.domains.join(' ')}`, 12).map((hit) => hit.scu_id)
  const obligations: InquiryObligation[] = []
  for (const scuId of floor.filter((id) => availableIds.has(id))) {
    obligations.push(makeObligation(obligations.length, { label: `Required capability: ${scuId}`, source: 'deterministic_floor', materiality: 'required', scu_ids: [scuId], rationale: `Deterministic floor for ${args.scope.intent}.` }))
  }
  for (const facet of args.ai?.question_facets ?? []) {
    const hits = searchSemanticCapabilities(args.snapshot, facet.terms.join(' '), 3).map((hit) => hit.scu_id)
    if (hits.length) obligations.push(makeObligation(obligations.length, { label: facet.label, source: 'ai_decomposition', materiality: facet.materiality, scu_ids: hits, rationale: 'AI-proposed question facet; capability ids were deterministically resolved against the snapshot.' }))
  }
  const selected = unique([...floor, ...queryHits, ...obligations.flatMap((obligation) => obligation.scu_ids)]).filter((id) => availableIds.has(id))
  const selectedSet = new Set(selected)
  for (const adjacency of args.ai?.uncommon_adjacencies ?? []) {
    if (!selectedSet.has(adjacency.from_scu_id) || !availableIds.has(adjacency.to_scu_id) || selectedSet.has(adjacency.to_scu_id)) continue
    obligations.push(makeObligation(obligations.length, {
      label: `Validated adjacency: ${adjacency.to_scu_id}`,
      source: 'ai_decomposition',
      materiality: 'supporting',
      scu_ids: [adjacency.to_scu_id],
      rationale: `AI-proposed adjacency from ${adjacency.from_scu_id}; both endpoints were validated against the immutable snapshot. ${adjacency.rationale}`,
    }))
    selected.push(adjacency.to_scu_id)
    selectedSet.add(adjacency.to_scu_id)
  }
  return { selected, obligations }
}

function omissionFindings(snapshot: CapabilityKnowledgeSnapshot, question: string, selected: readonly string[]): OmissionFinding[] {
  const lower = question.toLowerCase()
  const available = new Set(snapshot.scus.map((scu) => scu.scu_id))
  return OMISSION_RULES.filter((rule) => rule.terms.some((term) => lower.includes(term)) && available.has(rule.scu_id) && !selected.includes(rule.scu_id)).map((rule) => ({
    rule_id: rule.rule_id,
    severity: 'material' as const,
    missing_scu_id: rule.scu_id,
    rationale: rule.rationale,
  }))
}

function planFor(snapshot: CapabilityKnowledgeSnapshot, obligations: readonly InquiryObligation[], chartId: string, question: string, scope: InquiryScopeTuple): InquiryPlanItem[] {
  const byId = new Map(snapshot.scus.map((scu) => [scu.scu_id, scu]))
  const plan: InquiryPlanItem[] = []
  for (const obligation of obligations) {
    for (const scuId of obligation.scu_ids) {
      const scu = byId.get(scuId)
      if (!scu || plan.some((item) => item.scu_id === scuId)) continue
      const binding = scu.bindings.find((candidate) => candidate.relation === 'primary' && candidate.executable) ?? null
      const itemArgs: Record<string, unknown> = {}
      if (binding?.input_contract['chart_id']) itemArgs['chart_id'] = chartId
      if (binding?.input_contract['question']) itemArgs['question'] = question
      if (binding?.input_contract['query']) itemArgs['query'] = question
      if (binding?.input_contract['domain']) itemArgs['domain'] = scope.domains[0]
      if (binding?.input_contract['domains']) itemArgs['domains'] = scope.domains
      const unresolvedRequired = binding
        ? Object.entries(binding.input_contract).filter(([key, declaration]) => declaration.endsWith(':required') && itemArgs[key] === undefined).map(([key]) => key)
        : []
      plan.push({
        item_id: `item-${String(plan.length + 1).padStart(3, '0')}`,
        obligation_ids: obligations.filter((candidate) => candidate.scu_ids.includes(scuId)).map((candidate) => candidate.obligation_id),
        scu_id: scuId,
        binding_id: binding && unresolvedRequired.length === 0 ? binding.binding_id : null,
        args: itemArgs,
        depends_on: [],
        state: binding && unresolvedRequired.length === 0 ? 'ready' : 'blocked',
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
}): InquiryContract {
  if (args.overlay) assertOverlayCompatibility(args.snapshot, args.overlay)
  const selection = selectedScus({ snapshot: args.snapshot, question: args.question, scope: args.scope_tuple, ai: args.ai_proposal })
  const omissions = omissionFindings(args.snapshot, args.question, selection.selected)
  for (const omission of omissions) {
    selection.obligations.push(makeObligation(selection.obligations.length, {
      label: `Omission guard: ${omission.rule_id}`,
      source: 'omission_rule',
      materiality: omission.severity === 'material' ? 'required' : 'supporting',
      scu_ids: [omission.missing_scu_id],
      rationale: omission.rationale,
    }))
  }
  // If no named domain floor applies, search-derived capabilities still become
  // explicit obligations rather than disappearing into an opaque tool list.
  for (const scuId of selection.selected) {
    if (!selection.obligations.some((obligation) => obligation.scu_ids.includes(scuId))) {
      selection.obligations.push(makeObligation(selection.obligations.length, { label: `Question-bearing capability: ${scuId}`, source: 'deterministic_floor', materiality: 'supporting', scu_ids: [scuId], rationale: 'Deterministic semantic search match.' }))
    }
  }
  const plan = planFor(args.snapshot, selection.obligations, args.chart_id, args.question, args.scope_tuple)
  const semanticContractHash = stableFingerprint({
    contract_version: INQUIRY_CONTRACT_VERSION,
    compiler_version: INQUIRY_COMPILER_VERSION,
    question: args.question,
    scope_tuple: args.scope_tuple,
    capability_content_hash: args.snapshot.content_hash,
    obligations: selection.obligations,
    omission_findings: omissions,
  })
  const executionPlanHash = stableFingerprint({ semantic_contract_hash: semanticContractHash, chart_id: args.chart_id, plan_items: plan })
  const contractId = stableFingerprint({ semantic_contract_hash: semanticContractHash, execution_plan_hash: executionPlanHash })
  return {
    contract_version: INQUIRY_CONTRACT_VERSION,
    compiler_version: INQUIRY_COMPILER_VERSION,
    contract_id: contractId,
    semantic_contract_hash: semanticContractHash,
    execution_plan_hash: executionPlanHash,
    chart_id: args.chart_id,
    question: args.question,
    scope_tuple: args.scope_tuple,
    capability_compatibility_version: args.snapshot.compatibility_version,
    capability_content_hash: args.snapshot.content_hash,
    chart_availability_version: args.overlay?.overlay_version ?? null,
    obligations: selection.obligations,
    plan_items: plan,
    material_frontier: [],
    omission_findings: omissions,
    ai_hypotheses: [...(args.ai_proposal?.hypotheses ?? [])],
    status: 'INCOMPLETE',
    status_reasons: ['required_obligations_pending'],
    iteration: 0,
    // Iteration is an execution/expansion budget. The default must always fit
    // the initial deterministic plan plus four bounded retry/frontier passes.
    max_iterations: args.max_iterations === undefined
      ? Math.min(Math.max(plan.length + 4, 4), 64)
      : Math.max(1, Math.min(args.max_iterations, 64)),
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

export function validateInquiryContract(contract: InquiryContract): InquiryValidationResult {
  const errors: string[] = []
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
  const reasons = [...validation.errors]
  if (pending.length) reasons.push(`${pending.length} required obligations pending`)
  if (materialGaps.length) reasons.push(`${materialGaps.length} required obligations failed or are dark`)
  if (openFrontier.length) reasons.push(`${openFrontier.length} material frontier items open`)
  const exhausted = contract.iteration >= contract.max_iterations && (pending.length > 0 || materialGaps.length > 0 || openFrontier.length > 0)
  if (exhausted) reasons.push('iteration cap reached before material frontier closure')
  return {
    ...contract,
    status: reasons.length === 0 ? 'COMPLETE' : exhausted ? 'BLOCKED' : 'INCOMPLETE',
    status_reasons: reasons.length ? reasons : ['all required obligations dispositioned; material frontier closed'],
  }
}

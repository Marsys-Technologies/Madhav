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
  type InquiryPlanItem,
  type InquiryScopeTuple,
  type InquiryValidationResult,
  type OmissionFinding,
} from './types'
import type { InquiryPaginationReceipt } from './pagination'

export const INQUIRY_COMPILER_VERSION = '1.1.1'

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

function normalizeQuestion(question: string): string {
  return question.trim().replace(/\s+/g, ' ')
}

function normalizeScope(scope: InquiryScopeTuple): InquiryScopeTuple {
  return {
    ...scope,
    intent: String(scope.intent ?? 'unknown').trim(),
    domains: unique((scope.domains ?? []).map((domain) => String(domain).trim()).filter(Boolean)).sort(),
    width: String(scope.width ?? 'focused').trim(),
    depth: String(scope.depth ?? 'standard').trim(),
    horizon: String(scope.horizon ?? 'unspecified').trim(),
    intervention: typeof scope.intervention === 'string' ? scope.intervention.trim() : scope.intervention ?? false,
    entitlement: String(scope.entitlement ?? 'native').trim(),
  }
}

function normalizeAiProposal(ai: AiInquiryProposal | undefined): AiInquiryProposal | undefined {
  if (!ai) return undefined
  return {
    question_facets: ai.question_facets.map((facet) => ({
      ...facet,
      label: facet.label.trim(),
      terms: unique(facet.terms.map((term) => term.trim()).filter(Boolean)).sort(),
    })).sort((a, b) => stableFingerprint(a).localeCompare(stableFingerprint(b))),
    uncommon_adjacencies: ai.uncommon_adjacencies.map((adjacency) => ({
      ...adjacency,
      rationale: adjacency.rationale.trim(),
    })).sort((a, b) => stableFingerprint(a).localeCompare(stableFingerprint(b))),
    hypotheses: unique(ai.hypotheses.map((hypothesis) => hypothesis.trim()).filter(Boolean)).sort(),
  }
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
      if (!scu || plan.some((item) => item.scu_id === scuId)) continue
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
}): InquiryContract {
  const question = normalizeQuestion(args.question)
  const scope = normalizeScope(args.scope_tuple)
  const aiProposal = normalizeAiProposal(args.ai_proposal)
  const executionChannel = args.execution_channel ?? 'platform_internal'
  if (args.overlay) assertOverlayCompatibility(args.snapshot, args.overlay, args.chart_id)
  const selection = selectedScus({ snapshot: args.snapshot, question, scope, ai: aiProposal })
  const omissions = omissionFindings(args.snapshot, question, selection.selected)
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
  const semanticContractHash = stableFingerprint({
    contract_version: INQUIRY_CONTRACT_VERSION,
    compiler_version: INQUIRY_COMPILER_VERSION,
    question,
    scope_tuple: scope,
    capability_content_hash: args.snapshot.content_hash,
    obligations: semanticObligationProjection(obligations),
    omission_findings: omissions,
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
    material_frontier: [],
    omission_findings: omissions,
    ai_hypotheses: [...(aiProposal?.hypotheses ?? [])],
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
  }
  return { ...normalized, receipt_hash: stableFingerprint(normalized) }
}

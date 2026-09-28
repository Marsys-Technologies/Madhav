/**
 * The shared successor authorization envelope (Packet B of the fence-and-successor-envelope
 * follow-up).
 *
 * The compiled plan's exact tool set is a request's authorization set, and evidence-driven
 * frontier discovery proposes capabilities that are, by construction, not in that plan. Without an
 * envelope every such successor fails closed, named and inert. The envelope is the one bounded
 * grant that lets a *safe* successor through, and it is the same object, computed the same way and
 * evaluated by the same function, on every door (Portal, managed MCP, raw MCP).
 *
 * Authority properties this module enforces structurally:
 *  - Computed deterministically at plan time, from the pinned snapshot and the compiled plan only —
 *    before any evidence exists, and never from model text.
 *  - Carried on the contract and bound into `execution_plan_hash`, so it cannot be edited after issue.
 *  - Evaluated server-side from server-held state. Nothing a client or a model supplies is trusted:
 *    the frontier rule, source observation and identity are read from the contract; the live
 *    registry, principal, access, safety-denial and cost state come from the door's own process.
 *  - A successor's envelope can only shrink (`deriveSuccessorEnvelope`), so widening cannot recurse.
 *
 * The eight conditions (each refuses with its own stable named code — see SuccessorAdmissionCode):
 *  1 read-only · 2 in the pinned catalogue and executable on the active channel · 3 relevant to the
 *  compiled inquiry and to the frontier rule that proposed it · 4 same chart, principal, overlay and
 *  served build · 5 within the caller's chart access and entitlement tier · 6 within depth,
 *  iteration and cost ceilings · 7 survives request-time safety and no-leakage exclusion ·
 *  8 fully receipted (rule, observed source item, envelope entry, decision).
 */
import type {
  CapabilityKnowledgeSnapshot,
  ExecutionChannel,
  SemanticCapabilityBinding,
} from '../../retrieval/registry/knowledge/types'
import { selectBindingForMode } from '../../retrieval/registry/knowledge/proof_kind'
import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import type { CapabilityDescriptor } from '../../retrieval/registry/types'
import { EVIDENCE_FRONTIER_RULES } from './evidence_frontier'
import {
  isInquiryServerDispatchEligible,
  isInquirySafeRegistryDescriptor,
  presentationTransportForInquiry,
  type InquiryPresentationTransport,
} from './execution_policy'
import type { InquiryContract } from './types'

export const AUTHORIZATION_ENVELOPE_VERSION = 'inquiry-authorization-envelope-v1' as const
export const SUCCESSOR_ADMISSION_VERSION = 'inquiry-successor-admission-v1' as const

/** Successor generations a single inquiry lineage may chain (the managed door's existing ceiling). */
export const MAX_SUCCESSOR_DEPTH = 4
/** Evidence-admitted frontier items a whole lineage may admit. */
export const MAX_ADMITTED_SUCCESSOR_ITEMS = 8
/** Iterations a whole lineage may spend (the compiler's own per-contract hard cap). */
export const MAX_CHAIN_ITERATIONS = 64
/** Undirected snapshot-edge hops within which a target counts as graph-relevant to a planned SCU. */
export const ENVELOPE_RELEVANCE_HOPS = 2

/**
 * Stable decision/refusal codes. `successor_capability_not_authorized_for_request` is the
 * long-standing code for a capability outside the request's authority and is kept unchanged.
 */
export type SuccessorAdmissionCode =
  | 'successor_admitted'
  | 'successor_capability_not_authorized_for_request'
  | 'successor_receipt_incomplete'
  | 'successor_chart_mismatch'
  | 'successor_principal_mismatch'
  | 'successor_build_identity_mismatch'
  | 'successor_capability_not_in_catalogue'
  | 'successor_channel_not_eligible'
  | 'successor_capability_not_read_only'
  | 'successor_frontier_not_relevant'
  | 'successor_chart_access_not_verified'
  | 'successor_entitlement_not_permitted'
  | 'successor_safety_excluded'
  | 'successor_depth_exceeded'
  | 'successor_iteration_limit_exceeded'
  | 'successor_cost_limit_exceeded'

export interface AuthorizationEnvelopeEntry {
  readonly entry_id: string
  readonly scu_id: string
  readonly binding_id: string
  readonly capability_uri: string
  /** Frontier rules (sorted) that may propose this capability for this inquiry. */
  readonly admitting_rule_ids: readonly string[]
  /** Planned SCUs (sorted) within ENVELOPE_RELEVANCE_HOPS of this capability in the snapshot graph. */
  readonly anchor_scu_ids: readonly string[]
  /** True when the capability shares a domain with the inquiry scope. */
  readonly domain_overlap: boolean
}

export interface AuthorizationEnvelopeLimits {
  readonly max_successor_depth: number
  readonly max_admitted_successor_items: number
  readonly max_chain_iterations: number
}

export interface AuthorizationEnvelope {
  readonly envelope_version: typeof AUTHORIZATION_ENVELOPE_VERSION
  readonly chart_id: string
  readonly execution_channel: ExecutionChannel
  readonly presentation_transport: InquiryPresentationTransport
  readonly capability_content_hash: string
  readonly scope_entitlement: string
  readonly limits: AuthorizationEnvelopeLimits
  readonly entries: readonly AuthorizationEnvelopeEntry[]
  /** Hash of the envelope this one was derived from; null for the plan-time root. */
  readonly parent_envelope_hash: string | null
  readonly envelope_hash: string
}

export interface SuccessorAdmissionLimitState {
  readonly successor_depth: number
  readonly max_successor_depth: number
  readonly chain_iterations: number
  readonly max_chain_iterations: number
  readonly admitted_items: number
  readonly max_admitted_items: number
  readonly cost_exhausted: boolean
}

export interface SuccessorAdmissionDecision {
  readonly decision_version: typeof SUCCESSOR_ADMISSION_VERSION
  readonly decision: 'admit' | 'refuse'
  readonly code: SuccessorAdmissionCode
  readonly scu_id: string
  readonly binding_id: string | null
  readonly capability_uri: string | null
  readonly frontier_id: string | null
  readonly frontier_rule_id: string | null
  readonly source_item_id: string | null
  readonly source_scu_id: string | null
  readonly envelope_hash: string | null
  readonly envelope_entry_id: string | null
  readonly limit_state: SuccessorAdmissionLimitState
  readonly decision_hash: string
}

export interface SuccessorCandidate {
  readonly scu_id: string
  readonly binding_id: string | null
  readonly frontier_id?: string | null
  readonly frontier_rule_id?: string | null
  readonly source_item_id?: string | null
  readonly source_scu_id?: string | null
  /** True only when the source item was observed `served` with at least one evidence ref. */
  readonly source_served?: boolean
}

type LiveDescriptor = Pick<CapabilityDescriptor, 'uri' | 'mutation' | 'calibration_context_only'> & {
  readonly mcp_annotations?: { readonly readOnly?: boolean }
}

/**
 * Server-held, door-supplied state the evaluator reads. It is the only place request-time facts
 * enter; none of it is ever taken from a client body, a token payload the client can edit, or model text.
 */
export interface SuccessorAdmissionLiveContext {
  readonly transport: InquiryPresentationTransport
  readonly chart_id: string
  /** The principal acting now. */
  readonly principal_subject: string
  /** The principal that owns the request / lifecycle. */
  readonly owner_principal_subject: string
  /** The door re-verified this principal's access to this chart in this request. */
  readonly chart_access_verified: boolean
  readonly overlay_version: string | null
  readonly build_id: string | null
  /** Live registry view, so a stale or forged snapshot cannot turn an operation into evidence. */
  readonly describe: (capabilityUri: string) => LiveDescriptor | undefined
  readonly tool_exists: (capabilityUri: string) => boolean
  /**
   * True when the request's own safety exclusions or the no-leakage filter remove this capability.
   * A predicate, not a list: a successor's capability was never in the request's tool set, so a
   * list of removed names cannot cover it.
   */
  readonly is_capability_denied: (capabilityUri: string) => boolean
  /** The door's cost cap has already tripped. */
  readonly cost_exhausted: boolean
}

/** Domain markers for capabilities that apply to every inquiry scope. */
const UNIVERSAL_DOMAINS: ReadonlySet<string> = new Set(['all', 'cross_domain'])

const ENTITLEMENT_RANK: Readonly<Record<string, number>> = {
  native: 3,
  research: 2,
  public_disclosed: 1,
  reference: 1,
  restricted: 1,
}

/** A capability tier is permitted when it does not exceed the caller's scope tier; unknown fails closed. */
export function entitlementTierPermitted(capabilityTier: string, scopeTier: string): boolean {
  const capability = ENTITLEMENT_RANK[capabilityTier]
  const scope = ENTITLEMENT_RANK[scopeTier]
  return capability !== undefined && scope !== undefined && capability <= scope
}

const ENVELOPE_LIMITS: AuthorizationEnvelopeLimits = {
  max_successor_depth: MAX_SUCCESSOR_DEPTH,
  max_admitted_successor_items: MAX_ADMITTED_SUCCESSOR_ITEMS,
  max_chain_iterations: MAX_CHAIN_ITERATIONS,
}

export function authorizationEnvelopeHash(envelope: Omit<AuthorizationEnvelope, 'envelope_hash'> | AuthorizationEnvelope): string {
  const { envelope_hash: _ignored, ...body } = envelope as AuthorizationEnvelope
  return stableFingerprint(body)
}

function sealEnvelope(body: Omit<AuthorizationEnvelope, 'envelope_hash'>): AuthorizationEnvelope {
  return { ...body, envelope_hash: authorizationEnvelopeHash(body) }
}

function hopNeighbours(snapshot: CapabilityKnowledgeSnapshot): Map<string, Set<string>> {
  const graph = new Map<string, Set<string>>()
  const link = (from: string, to: string) => {
    const set = graph.get(from) ?? new Set<string>()
    set.add(to)
    graph.set(from, set)
  }
  for (const edge of snapshot.edges) { link(edge.from_scu_id, edge.to_scu_id); link(edge.to_scu_id, edge.from_scu_id) }
  return graph
}

function scusWithinHops(graph: Map<string, Set<string>>, start: string, hops: number): Set<string> {
  const seen = new Set<string>([start])
  let frontier = [start]
  for (let hop = 0; hop < hops; hop += 1) {
    const next: string[] = []
    for (const node of frontier) for (const neighbour of graph.get(node) ?? []) {
      if (seen.has(neighbour)) continue
      seen.add(neighbour)
      next.push(neighbour)
    }
    frontier = next
  }
  return seen
}

/**
 * Build the plan-time envelope. An entry exists only for a capability that (a) a frontier rule can
 * propose, (b) the plan does not already contain, (c) has a server-dispatchable registry binding on
 * this door's channel (snapshot membership already excludes mutating and calibration-only
 * descriptors), (d) is within the scope's entitlement tier, and (e) is relevant to the compiled
 * inquiry: graph-adjacent to a planned SCU, or sharing a domain with the scope.
 */
export function buildAuthorizationEnvelope(args: {
  snapshot: CapabilityKnowledgeSnapshot
  chart_id: string
  execution_channel: ExecutionChannel
  scope: { readonly domains: readonly string[]; readonly entitlement: string }
  planned_scu_ids: readonly string[]
  /** Planned SCUs whose plan items are executable; only these anchor relevance. */
  anchor_scu_ids: readonly string[]
}): AuthorizationEnvelope {
  const transport = presentationTransportForInquiry(args.execution_channel)
  const byId = new Map(args.snapshot.scus.map((scu) => [scu.scu_id, scu]))
  const planned = new Set(args.planned_scu_ids)
  const anchors = new Set(args.anchor_scu_ids)
  const scopeDomains = new Set(args.scope.domains)
  const graph = hopNeighbours(args.snapshot)
  const acc = new Map<string, { rules: Set<string> }>()
  for (const rule of EVIDENCE_FRONTIER_RULES) {
    for (const target of rule.target_scu_ids) {
      if (planned.has(target) || !byId.has(target)) continue
      const slot = acc.get(target) ?? { rules: new Set<string>() }
      slot.rules.add(rule.rule_id)
      acc.set(target, slot)
    }
  }
  const entries: AuthorizationEnvelopeEntry[] = []
  for (const [scuId, slot] of acc) {
    const scu = byId.get(scuId)!
    const eligible = scu.bindings.filter((binding) => isInquiryServerDispatchEligible(binding, transport))
    const binding = selectBindingForMode(eligible, undefined)
    if (!binding) continue
    if (!entitlementTierPermitted(scu.entitlement, args.scope.entitlement)) continue
    const near = scusWithinHops(graph, scuId, ENVELOPE_RELEVANCE_HOPS)
    const anchorScus = [...anchors].filter((anchor) => near.has(anchor)).sort()
    const domainOverlap = scu.domains.some((domain) => UNIVERSAL_DOMAINS.has(domain) || scopeDomains.has(domain))
    if (anchorScus.length === 0 && !domainOverlap) continue
    entries.push({
      entry_id: `env:${scuId}`,
      scu_id: scuId,
      binding_id: binding.binding_id,
      capability_uri: binding.capability_uri,
      admitting_rule_ids: [...slot.rules].sort(),
      anchor_scu_ids: anchorScus,
      domain_overlap: domainOverlap,
    })
  }
  entries.sort((left, right) => left.scu_id.localeCompare(right.scu_id))
  return sealEnvelope({
    envelope_version: AUTHORIZATION_ENVELOPE_VERSION,
    chart_id: args.chart_id,
    execution_channel: args.execution_channel,
    presentation_transport: transport,
    capability_content_hash: args.snapshot.content_hash,
    scope_entitlement: args.scope.entitlement,
    limits: ENVELOPE_LIMITS,
    entries,
    parent_envelope_hash: null,
  })
}

/**
 * The envelope a successor carries for ITS OWN successors: the parent's entries minus every
 * capability the lineage has now consumed. It can only shrink, so widening cannot recurse.
 */
export function deriveSuccessorEnvelope(
  parent: AuthorizationEnvelope,
  args: { consumed_scu_ids: readonly string[] },
): AuthorizationEnvelope {
  const consumed = new Set(args.consumed_scu_ids)
  return sealEnvelope({
    envelope_version: parent.envelope_version,
    chart_id: parent.chart_id,
    execution_channel: parent.execution_channel,
    presentation_transport: parent.presentation_transport,
    capability_content_hash: parent.capability_content_hash,
    scope_entitlement: parent.scope_entitlement,
    limits: parent.limits,
    entries: parent.entries.filter((entry) => !consumed.has(entry.scu_id)),
    parent_envelope_hash: parent.envelope_hash,
  })
}

type ChainContract = Pick<InquiryContract, 'iteration' | 'successor'>

function chainState(contract: ChainContract): { depth: number; iterations: number; admitted: number } {
  let depth = 0
  let iterations = 0
  let admitted = 0
  let current: ChainContract | undefined = contract
  // Bounded walk: the ceilings below refuse long before a legitimate lineage nears this.
  while (current && depth <= MAX_SUCCESSOR_DEPTH + 1) {
    iterations += current.iteration ?? 0
    if (current.successor) {
      depth += 1
      admitted += current.successor.admitted_frontier?.length ?? 0
      current = current.successor.parent_contract
    } else current = undefined
  }
  return { depth, iterations, admitted }
}

function isReadOnlyDescriptor(binding: SemanticCapabilityBinding, descriptor: LiveDescriptor | undefined): boolean {
  return isInquirySafeRegistryDescriptor(binding, descriptor) && descriptor?.mcp_annotations?.readOnly !== false
}

function seal(body: Omit<SuccessorAdmissionDecision, 'decision_hash'>): SuccessorAdmissionDecision {
  return { ...body, decision_hash: stableFingerprint(body) }
}

export function verifySuccessorDecision(decision: SuccessorAdmissionDecision): boolean {
  const { decision_hash: recorded, ...body } = decision
  return recorded === stableFingerprint(body)
    && (decision.decision === 'admit') === (decision.code === 'successor_admitted')
}

/**
 * A live state that authorizes nothing, for a caller that supplies none. `compileInquirySuccessorContract`
 * evaluates against an absent envelope when no live state is given, so an omitted argument can only
 * ever refuse (with the long-standing not-authorized code), never admit.
 */
export const SUCCESSOR_DENY_ALL_LIVE: SuccessorAdmissionLiveContext = {
  transport: 'portal',
  chart_id: '',
  principal_subject: '',
  owner_principal_subject: '',
  chart_access_verified: false,
  overlay_version: null,
  build_id: null,
  describe: () => undefined,
  tool_exists: () => false,
  is_capability_denied: () => true,
  cost_exhausted: true,
}

/**
 * The one shared evaluator. Given the same envelope, snapshot, candidate, contract and live state
 * it returns the same decision on every door. Conditions are checked in a fixed order and the first
 * failure names the refusal; a refusal is never softened into an admission.
 */
export function evaluateSuccessorAdmission(input: {
  envelope: AuthorizationEnvelope | undefined
  snapshot: CapabilityKnowledgeSnapshot
  candidate: SuccessorCandidate
  /** The contract the candidate was discovered in (the successor's parent). */
  contract: Pick<InquiryContract, 'chart_id' | 'capability_content_hash' | 'chart_availability_version' | 'chart_build_id'
    | 'iteration' | 'successor' | 'plan_items' | 'scope_tuple'>
  live: SuccessorAdmissionLiveContext
}): SuccessorAdmissionDecision {
  const { envelope, snapshot, candidate, contract, live } = input
  const chain = chainState(contract)
  const limits = envelope?.limits ?? ENVELOPE_LIMITS
  const limitState: SuccessorAdmissionLimitState = {
    successor_depth: chain.depth,
    max_successor_depth: limits.max_successor_depth,
    chain_iterations: chain.iterations,
    max_chain_iterations: limits.max_chain_iterations,
    admitted_items: chain.admitted,
    max_admitted_items: limits.max_admitted_successor_items,
    cost_exhausted: live.cost_exhausted,
  }
  const entry = envelope && authorizationEnvelopeHash(envelope) === envelope.envelope_hash
    ? envelope.entries.find((candidateEntry) => candidateEntry.scu_id === candidate.scu_id)
    : undefined
  const base = {
    decision_version: SUCCESSOR_ADMISSION_VERSION,
    scu_id: candidate.scu_id,
    binding_id: candidate.binding_id,
    capability_uri: entry?.capability_uri ?? null,
    frontier_id: candidate.frontier_id ?? null,
    frontier_rule_id: candidate.frontier_rule_id ?? null,
    source_item_id: candidate.source_item_id ?? null,
    source_scu_id: candidate.source_scu_id ?? null,
    envelope_hash: envelope?.envelope_hash ?? null,
    envelope_entry_id: entry?.entry_id ?? null,
    limit_state: limitState,
  } as const
  const refuse = (code: SuccessorAdmissionCode) => seal({ ...base, decision: 'refuse', code })

  // Outside the envelope (or no/forged envelope): the long-standing named gap.
  if (!envelope || !entry) return refuse('successor_capability_not_authorized_for_request')
  if (candidate.binding_id !== null && candidate.binding_id !== entry.binding_id) {
    return refuse('successor_capability_not_authorized_for_request')
  }
  // 8 — the receipt must be completable before anything else is trusted.
  if (!candidate.frontier_id || !candidate.frontier_rule_id || !candidate.source_item_id
    || !candidate.source_scu_id || candidate.source_served !== true) {
    return refuse('successor_receipt_incomplete')
  }
  // 4 — identity: same chart, principal, overlay, served build and pinned catalogue.
  if (live.chart_id !== contract.chart_id || envelope.chart_id !== contract.chart_id) return refuse('successor_chart_mismatch')
  if (live.principal_subject !== live.owner_principal_subject) return refuse('successor_principal_mismatch')
  if (live.overlay_version !== contract.chart_availability_version || live.build_id !== contract.chart_build_id
    || snapshot.content_hash !== contract.capability_content_hash || envelope.capability_content_hash !== snapshot.content_hash) {
    return refuse('successor_build_identity_mismatch')
  }
  // 2 — present in the pinned catalogue AND the live registry, executable on the active channel.
  const scu = snapshot.scus.find((candidateScu) => candidateScu.scu_id === entry.scu_id)
  const binding = scu?.bindings.find((candidateBinding) => candidateBinding.binding_id === entry.binding_id)
  const descriptor = live.describe(entry.capability_uri)
  if (!scu || !binding || !descriptor || !live.tool_exists(entry.capability_uri)) return refuse('successor_capability_not_in_catalogue')
  if (candidate.binding_id === null || !isInquiryServerDispatchEligible(binding, live.transport)) return refuse('successor_channel_not_eligible')
  // 1 — read-only, from the descriptor's own metadata and the shared safety predicate.
  if (!isReadOnlyDescriptor(binding, descriptor)) return refuse('successor_capability_not_read_only')
  // 3 — deterministic relevance: the rule must admit this entry and target this SCU, and the
  // evidence must have come from a different SCU the contract itself planned and observed.
  const rule = EVIDENCE_FRONTIER_RULES.find((candidateRule) => candidateRule.rule_id === candidate.frontier_rule_id)
  const sourceItem = contract.plan_items.find((item) => item.item_id === candidate.source_item_id)
  if (!rule || !entry.admitting_rule_ids.includes(rule.rule_id) || !rule.target_scu_ids.includes(entry.scu_id)
    || !sourceItem || sourceItem.scu_id !== candidate.source_scu_id || sourceItem.scu_id === entry.scu_id) {
    return refuse('successor_frontier_not_relevant')
  }
  // 5 — the caller's chart access (re-verified by the door) and entitlement tier.
  if (!live.chart_access_verified) return refuse('successor_chart_access_not_verified')
  if (!entitlementTierPermitted(scu.entitlement, contract.scope_tuple.entitlement)) return refuse('successor_entitlement_not_permitted')
  // 7 — the request's own safety and no-leakage exclusions still apply to a successor.
  if (live.is_capability_denied(entry.capability_uri)) return refuse('successor_safety_excluded')
  // 6 — depth, iteration and cost ceilings.
  if (chain.depth + 1 > limits.max_successor_depth) return refuse('successor_depth_exceeded')
  if (chain.iterations >= limits.max_chain_iterations) return refuse('successor_iteration_limit_exceeded')
  if (live.cost_exhausted || chain.admitted >= limits.max_admitted_successor_items) return refuse('successor_cost_limit_exceeded')
  return seal({ ...base, decision: 'admit', code: 'successor_admitted' })
}

/**
 * Re-derive the decision for one item of an already-compiled successor contract, from the
 * server-held contract alone plus the door's live state. Every door calls this immediately before
 * dispatching a successor item, so authority is recomputed rather than trusted from the stored
 * compile-time decision (which must ALSO be an admission: a compile-time refusal is final).
 */
export function evaluateSuccessorItemForDispatch(args: {
  contract: InquiryContract
  item_id: string
  snapshot: CapabilityKnowledgeSnapshot
  live: SuccessorAdmissionLiveContext
}): SuccessorAdmissionDecision | null {
  const successor = args.contract.successor
  if (!successor) return null
  const item = args.contract.plan_items.find((candidate) => candidate.item_id === args.item_id)
  if (!item) return null
  const parent = successor.parent_contract
  const admitted = successor.admitted_frontier.find((frontier) => frontier.scu_id === item.scu_id)
  const stored = item.successor_admission
  const sourceItem = admitted ? parent.plan_items.find((candidate) => candidate.item_id === admitted.discovered_from) : undefined
  const decision = evaluateSuccessorAdmission({
    envelope: parent.authorization_envelope,
    snapshot: args.snapshot,
    candidate: {
      scu_id: item.scu_id,
      binding_id: item.binding_id,
      frontier_id: admitted?.frontier_id ?? null,
      frontier_rule_id: admitted?.rule_id ?? null,
      source_item_id: admitted?.discovered_from ?? null,
      source_scu_id: sourceItem?.scu_id ?? null,
      source_served: Boolean(sourceItem?.observation?.disposition === 'served' && sourceItem.observation.evidence_refs.length > 0),
    },
    contract: parent,
    live: args.live,
  })
  // A stored refusal is final; a stored admission must still verify.
  if (!stored || stored.decision === 'refuse' || !verifySuccessorDecision(stored)) {
    const code: SuccessorAdmissionCode = stored?.decision === 'refuse' ? stored.code
      : decision.decision === 'refuse' ? decision.code
      : 'successor_capability_not_authorized_for_request'
    const { decision_hash: _superseded, ...body } = decision
    return seal({ ...body, decision: 'refuse', code })
  }
  return decision
}

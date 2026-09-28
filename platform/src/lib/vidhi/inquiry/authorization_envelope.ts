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
/**
 * The campaign's deterministic successor cost unit is the registry dispatch unit (the same unit the
 * managed door's request-level CostCapTracker charges: a descriptor's `dispatch_units`, default 1).
 * A whole lineage (every generation, every pagination page) may spend at most this many.
 */
export const SUCCESSOR_COST_UNIT = 'registry_dispatch_unit' as const
export const MAX_SUCCESSOR_DISPATCH_UNITS = 12
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
  | 'successor_arguments_not_authorized'

/**
 * The server-authoritative entitlement for successor authorization. It is derived from the door's
 * own verified chart-permission result — never from a scope tuple, a planner, or a request field —
 * and is recorded (with its source) in the envelope, in every decision, and in the authorization hash.
 */
export type EffectiveEntitlementTier = 'native' | 'public_disclosed' | 'none'
export interface EffectiveEntitlement {
  readonly tier: EffectiveEntitlementTier
  readonly source: 'chart_permission_all' | 'chart_permission_view' | 'chart_permission_unverified'
}

/**
 * Full (owner-equivalent) permission authorizes the native tier; view-only authorizes only the
 * least-privileged tier; denial, absence or anything unrecognized authorizes nothing.
 */
export function effectiveEntitlementForPermission(permission: 'all' | 'view' | 'deny' | null | undefined): EffectiveEntitlement {
  if (permission === 'all') return { tier: 'native', source: 'chart_permission_all' }
  if (permission === 'view') return { tier: 'public_disclosed', source: 'chart_permission_view' }
  return { tier: 'none', source: 'chart_permission_unverified' }
}

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
  /** Successor cost ceiling in SUCCESSOR_COST_UNIT for the whole lineage. */
  readonly max_successor_dispatch_units: number
}

export interface AuthorizationEnvelope {
  readonly envelope_version: typeof AUTHORIZATION_ENVELOPE_VERSION
  readonly chart_id: string
  readonly execution_channel: ExecutionChannel
  readonly presentation_transport: InquiryPresentationTransport
  readonly capability_content_hash: string
  /** The semantic scope entitlement (classifier/caller supplied). It may only NARROW; it never grants. */
  readonly scope_entitlement: string
  /** The server-derived authority actually granted (see EffectiveEntitlement). */
  readonly effective_entitlement: EffectiveEntitlement
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
  /** Request-level cost stop reported by the door (refuse-only input; it can never create an admission). */
  readonly cost_exhausted: boolean
  /** The shared successor cost model: unit, lineage budget, spent, this candidate's price, what is left. */
  readonly cost_unit: typeof SUCCESSOR_COST_UNIT
  readonly budget_units: number
  readonly consumed_units: number
  readonly candidate_units: number
  readonly remaining_units: number
}

export interface SuccessorAdmissionDecision {
  readonly decision_version: typeof SUCCESSOR_ADMISSION_VERSION
  readonly decision: 'admit' | 'refuse'
  readonly code: SuccessorAdmissionCode
  /**
   * What authorizes the item: an entry of the plan-time envelope, or — for a capped pagination
   * frontier of a capability the hash-bound parent plan already contains — that plan itself.
   */
  readonly authority: 'envelope_entry' | 'parent_plan_continuation'
  readonly scu_id: string
  readonly binding_id: string | null
  readonly capability_uri: string | null
  readonly frontier_id: string | null
  readonly frontier_rule_id: string | null
  readonly source_item_id: string | null
  readonly source_scu_id: string | null
  readonly envelope_hash: string | null
  readonly envelope_entry_id: string | null
  /** The effective (server-derived) entitlement this decision was made under, with its source. */
  readonly entitlement: EffectiveEntitlement
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
  /**
   * The chart permission the door's own authorization returned for this principal in this request
   * (`authorizeChartAccess` / `authorizeTurn`), never a boolean the door asserts. Only `all` and
   * `view` admit; anything else, or an absent result, refuses.
   */
  readonly chart_permission: 'all' | 'view' | 'deny' | null
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
  /**
   * The registry dispatch units one dispatch of this capability costs (the unit the managed door's
   * request-level CostCapTracker charges). A non-positive or non-integer answer refuses on cost.
   */
  readonly dispatch_units: (capabilityUri: string) => number
  /**
   * The door's request-level cost cap has already tripped. Refuse-only: it can add a refusal but
   * can never create an admission, and a door with no such cap simply omits it. The successor
   * budget is enforced independently from the contract's own ledger.
   */
  readonly cost_exhausted?: boolean
}

/**
 * Domain markers for capabilities that apply to every inquiry scope. A universal-domain target is
 * therefore never scope-gated by domain: for `yoga.firing_and_cancellation` and
 * `judgment_query` the operative relevance gate is the frontier rule plus the served source item
 * (condition 3 at evaluation), not the scope's domains. Only `get_dashas` is scope/graph gated here.
 */
const UNIVERSAL_DOMAINS: ReadonlySet<string> = new Set(['all', 'cross_domain'])

// A null-prototype table: a stored tier such as `constructor` or `__proto__` must be UNKNOWN, not a
// function that happens to compare false. Unknown always fails closed.
const ENTITLEMENT_RANK: Readonly<Record<string, number>> = Object.freeze(Object.assign(Object.create(null) as Record<string, number>, {
  none: 0,
  native: 3,
  research: 2,
  public_disclosed: 1,
  reference: 1,
  restricted: 1,
}))

function tierRank(tier: unknown): number | undefined {
  return typeof tier === 'string' && Object.hasOwn(ENTITLEMENT_RANK, tier) ? ENTITLEMENT_RANK[tier] : undefined
}

/** A capability tier is permitted when it does not exceed the caller's scope tier; unknown fails closed. */
export function entitlementTierPermitted(capabilityTier: string, scopeTier: string): boolean {
  const capability = tierRank(capabilityTier)
  const scope = tierRank(scopeTier)
  return capability !== undefined && scope !== undefined && capability <= scope
}

const ENVELOPE_LIMITS: AuthorizationEnvelopeLimits = {
  max_successor_depth: MAX_SUCCESSOR_DEPTH,
  max_admitted_successor_items: MAX_ADMITTED_SUCCESSOR_ITEMS,
  max_chain_iterations: MAX_CHAIN_ITERATIONS,
  max_successor_dispatch_units: MAX_SUCCESSOR_DISPATCH_UNITS,
}

const EFFECTIVE_TIERS: ReadonlySet<string> = new Set(['native', 'public_disclosed', 'none'])
const EFFECTIVE_SOURCES: ReadonlySet<string> = new Set(['chart_permission_all', 'chart_permission_view', 'chart_permission_unverified'])

/**
 * The tier a stored envelope claims to have been granted. With no envelope there is nothing stored to
 * bound the live grant (the plan-continuation authority); an envelope whose recorded entitlement is
 * absent or malformed (unknown tier or source, wrong type) grants NOTHING — a stored value is trusted
 * only after it validates against the closed unions.
 */
function storedGrantTier(envelope: AuthorizationEnvelope | undefined, live: string): string {
  if (envelope === undefined) return live
  const recorded = (envelope as { effective_entitlement?: { tier?: unknown; source?: unknown } }).effective_entitlement
  if (!recorded || typeof recorded.tier !== 'string' || typeof recorded.source !== 'string') return 'none'
  return EFFECTIVE_TIERS.has(recorded.tier) && EFFECTIVE_SOURCES.has(recorded.source) ? recorded.tier : 'none'
}

/** The lower of two tiers; anything unrecognized collapses to `none`. */
export function lowerEntitlementTier(left: string, right: string): string {
  const a = tierRank(left)
  const b = tierRank(right)
  if (a === undefined || b === undefined || !Number.isFinite(a) || !Number.isFinite(b)) return 'none'
  return a <= b ? left : right
}

// ── Successor cost ledger ────────────────────────────────────────────────────────────────────
// A lineage's spend is a hash-chained ledger carried on each contract: one entry per dispatch, appended
// in the SAME transition as the observation it pays for (so exactly once, and a crash before that
// commit leaves an ambiguous, fail-closed item rather than a replayable one). A generation's ledger
// is immutable once its successor embeds it as `parent_contract`, so a new generation can never
// reset its lineage's budget.
export interface SuccessorCostLedgerEntry {
  readonly seq: number
  readonly item_id: string
  readonly scu_id: string
  readonly units: number
  readonly decision_hash: string
  readonly entry_hash: string
}

export interface SuccessorCostLedger {
  readonly ledger_version: 'inquiry-successor-cost-ledger-v1'
  readonly unit: typeof SUCCESSOR_COST_UNIT
  readonly entries: readonly SuccessorCostLedgerEntry[]
  readonly consumed_units: number
  readonly ledger_hash: string
}

function ledgerEntryHash(previous: string, entry: Omit<SuccessorCostLedgerEntry, 'entry_hash'>): string {
  return stableFingerprint({ previous, entry })
}

function ledgerHash(entries: readonly SuccessorCostLedgerEntry[]): string {
  return stableFingerprint({ ledger_version: 'inquiry-successor-cost-ledger-v1', entries: entries.map((entry) => entry.entry_hash) })
}

export function appendSuccessorCharge(
  ledger: SuccessorCostLedger | undefined,
  charge: { item_id: string; scu_id: string; units: number; decision_hash: string },
): SuccessorCostLedger {
  const previous = ledger?.entries.at(-1)?.entry_hash ?? 'genesis'
  const body = { seq: (ledger?.entries.length ?? 0) + 1, ...charge }
  const entries = [...(ledger?.entries ?? []), { ...body, entry_hash: ledgerEntryHash(previous, body) }]
  return {
    ledger_version: 'inquiry-successor-cost-ledger-v1',
    unit: SUCCESSOR_COST_UNIT,
    entries,
    consumed_units: entries.reduce((total, entry) => total + entry.units, 0),
    ledger_hash: ledgerHash(entries),
  }
}

/** Recompute the chain, the total and the hash; any edit, deletion or reorder fails. */
export function verifySuccessorCostLedger(ledger: SuccessorCostLedger): boolean {
  if (!ledger || !Array.isArray(ledger.entries)) return false
  let previous = 'genesis'
  let total = 0
  for (const [index, entry] of ledger.entries.entries()) {
    const { entry_hash: recorded, ...body } = entry
    if (entry.seq !== index + 1 || !Number.isInteger(entry.units) || entry.units < 1) return false
    if (recorded !== ledgerEntryHash(previous, body)) return false
    previous = recorded
    total += entry.units
  }
  return ledger.unit === SUCCESSOR_COST_UNIT && ledger.consumed_units === total && ledger.ledger_hash === ledgerHash(ledger.entries)
}

/**
 * Units a lineage has spent so far, summed over this contract's and every ancestor's ledger.
 * `null` means a ledger failed verification: the caller must treat the budget as exhausted.
 */
export function lineageConsumedUnits(contract: { successor_cost_ledger?: SuccessorCostLedger; successor?: { parent_contract: unknown } }): number | null {
  let total = 0
  let current: typeof contract | undefined = contract
  for (let depth = 0; current && depth <= MAX_SUCCESSOR_DEPTH + 1; depth += 1) {
    if (current.successor_cost_ledger) {
      if (!verifySuccessorCostLedger(current.successor_cost_ledger)) return null
      total += current.successor_cost_ledger.consumed_units
    }
    current = current.successor?.parent_contract as typeof contract | undefined
  }
  // A lineage deeper than the ceiling permits is unverifiable, not partially counted.
  return current ? null : total
}

export function authorizationEnvelopeHash(envelope: Omit<AuthorizationEnvelope, 'envelope_hash'> | AuthorizationEnvelope): string {
  const body: Record<string, unknown> = { ...envelope }
  delete body['envelope_hash']
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
  /** Server-derived (see effectiveEntitlementForPermission); a scope tuple can only narrow it. */
  effective_entitlement: EffectiveEntitlement
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
    if (!entitlementTierPermitted(scu.entitlement, lowerEntitlementTier(args.effective_entitlement.tier, args.scope.entitlement))) continue
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
  // Codepoint order, not locale order: the envelope hash must not depend on the runtime's ICU data.
  entries.sort((left, right) => (left.scu_id < right.scu_id ? -1 : left.scu_id > right.scu_id ? 1 : 0))
  return sealEnvelope({
    envelope_version: AUTHORIZATION_ENVELOPE_VERSION,
    chart_id: args.chart_id,
    execution_channel: args.execution_channel,
    presentation_transport: transport,
    capability_content_hash: args.snapshot.content_hash,
    scope_entitlement: args.scope.entitlement,
    effective_entitlement: args.effective_entitlement,
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
    effective_entitlement: parent.effective_entitlement,
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

function envelopeIntactForLimits(envelope: AuthorizationEnvelope | undefined): boolean {
  return envelope !== undefined && typeof envelope.limits === 'object' && envelope.limits !== null
    && authorizationEnvelopeHash(envelope) === envelope.envelope_hash
}

function isReadOnlyDescriptor(binding: SemanticCapabilityBinding, descriptor: LiveDescriptor | undefined): boolean {
  return isInquirySafeRegistryDescriptor(binding, descriptor) && descriptor?.mcp_annotations?.readOnly !== false
}

function seal(body: Omit<SuccessorAdmissionDecision, 'decision_hash'>): SuccessorAdmissionDecision {
  return { ...body, decision_hash: stableFingerprint(body) }
}

/** A refusal for a successor item whose lineage or plan item cannot be read (never `null`, never an admit). */
function refusedWithoutReceipt(itemId: string, scuId: string, live: SuccessorAdmissionLiveContext): SuccessorAdmissionDecision {
  return seal({
    decision_version: SUCCESSOR_ADMISSION_VERSION, authority: 'envelope_entry', decision: 'refuse',
    code: 'successor_receipt_incomplete', scu_id: scuId, binding_id: null, capability_uri: null,
    frontier_id: null, frontier_rule_id: null, source_item_id: itemId, source_scu_id: null,
    envelope_hash: null, envelope_entry_id: null,
    limit_state: {
      successor_depth: 0, max_successor_depth: MAX_SUCCESSOR_DEPTH, chain_iterations: 0, max_chain_iterations: MAX_CHAIN_ITERATIONS,
      admitted_items: 0, max_admitted_items: MAX_ADMITTED_SUCCESSOR_ITEMS, cost_exhausted: live.cost_exhausted === true,
      cost_unit: SUCCESSOR_COST_UNIT, budget_units: MAX_SUCCESSOR_DISPATCH_UNITS, consumed_units: 0, candidate_units: 0,
      remaining_units: MAX_SUCCESSOR_DISPATCH_UNITS,
    },
    entitlement: effectiveEntitlementForPermission(live.chart_permission),
  })
}

function withoutDecisionHash(decision: SuccessorAdmissionDecision): Omit<SuccessorAdmissionDecision, 'decision_hash'> {
  const body: Record<string, unknown> = { ...decision }
  delete body['decision_hash']
  return body as unknown as Omit<SuccessorAdmissionDecision, 'decision_hash'>
}

export function verifySuccessorDecision(decision: SuccessorAdmissionDecision): boolean {
  return decision.decision_hash === stableFingerprint(withoutDecisionHash(decision))
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
  chart_permission: null,
  overlay_version: null,
  build_id: null,
  describe: () => undefined,
  tool_exists: () => false,
  is_capability_denied: () => true,
  dispatch_units: () => 0,
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
  /** Items of the SAME generation already admitted before this one (the ceiling counts the whole batch). */
  admitted_in_batch?: number
  /**
   * Units this generation's OWN ledger has charged so far (dispatch time; `null` = that ledger failed
   * verification). Compile time passes nothing: no dispatch has happened yet.
   */
  own_ledger_units?: number | null
}): SuccessorAdmissionDecision {
  const { envelope, snapshot, candidate, contract, live } = input
  const chainBase = chainState(contract)
  const chain = { ...chainBase, admitted: chainBase.admitted + (input.admitted_in_batch ?? 0) }
  // Ceilings a stored envelope declares can only tighten the platform's own, never loosen them.
  // A stored ceiling is read only from an envelope that passes its own hash check, and only if it is a
  // non-negative integer: anything else (NaN, a string, a negative) collapses to ZERO, never to "no limit".
  const stored = envelopeIntactForLimits(envelope) ? envelope!.limits : undefined
  const clampLimit = (recorded: unknown, platform: number): number => {
    if (recorded === undefined) return platform
    return typeof recorded === 'number' && Number.isInteger(recorded) && recorded >= 0 ? Math.min(recorded, platform) : 0
  }
  const limits: AuthorizationEnvelopeLimits = {
    max_successor_depth: clampLimit(stored?.max_successor_depth, MAX_SUCCESSOR_DEPTH),
    max_admitted_successor_items: clampLimit(stored?.max_admitted_successor_items, MAX_ADMITTED_SUCCESSOR_ITEMS),
    max_chain_iterations: clampLimit(stored?.max_chain_iterations, MAX_CHAIN_ITERATIONS),
    max_successor_dispatch_units: clampLimit(stored?.max_successor_dispatch_units, MAX_SUCCESSOR_DISPATCH_UNITS),
  }
  // The shared successor cost model. A ledger that fails verification, or a price that is not a positive
  // integer, is not "free": it exhausts the budget.
  const lineageUnits = lineageConsumedUnits(contract)
  const ownUnits = input.own_ledger_units === undefined ? 0 : input.own_ledger_units
  const consumedUnits = lineageUnits === null || ownUnits === null ? null : lineageUnits + ownUnits
  const costLedgerValid = consumedUnits !== null
  // A capped pagination frontier of a capability the (hash-bound) parent plan already contains is
  // authorized by that plan, not by an envelope entry — but it must still clear every other condition.
  const planContinuation = candidate.binding_id !== null
    && candidate.source_scu_id === candidate.scu_id
    && contract.plan_items.some((item) => item.scu_id === candidate.scu_id && item.binding_id === candidate.binding_id)
  const envelopeIntact = envelope !== undefined && authorizationEnvelopeHash(envelope) === envelope.envelope_hash
  const entry = !planContinuation && envelopeIntact
    ? envelope!.entries.find((candidateEntry) => candidateEntry.scu_id === candidate.scu_id)
    : undefined
  const scu = snapshot.scus.find((candidateScu) => candidateScu.scu_id === candidate.scu_id)
  const binding = scu?.bindings.find((candidateBinding) => candidateBinding.binding_id === (planContinuation ? candidate.binding_id : entry?.binding_id))
  const capabilityUri = planContinuation ? binding?.capability_uri ?? null : entry?.capability_uri ?? null
  const rawUnits = capabilityUri ? live.dispatch_units(capabilityUri) : NaN
  const candidateUnits = Number.isInteger(rawUnits) && rawUnits >= 1 ? rawUnits : null
  // The effective entitlement is what the door's own verified permission grants RIGHT NOW; a stored
  // envelope may record a narrower or equal grant, but nothing stored can widen it.
  const effectiveNow = effectiveEntitlementForPermission(live.chart_permission)
  const limitState: SuccessorAdmissionLimitState = {
    successor_depth: chain.depth,
    max_successor_depth: limits.max_successor_depth,
    chain_iterations: chain.iterations,
    max_chain_iterations: limits.max_chain_iterations,
    admitted_items: chain.admitted,
    max_admitted_items: limits.max_admitted_successor_items,
    cost_exhausted: live.cost_exhausted === true,
    cost_unit: SUCCESSOR_COST_UNIT,
    budget_units: limits.max_successor_dispatch_units,
    consumed_units: consumedUnits ?? limits.max_successor_dispatch_units,
    candidate_units: candidateUnits ?? 0,
    remaining_units: costLedgerValid && candidateUnits !== null ? Math.max(limits.max_successor_dispatch_units - (consumedUnits ?? 0), 0) : 0,
  }
  const base = {
    decision_version: SUCCESSOR_ADMISSION_VERSION,
    authority: planContinuation ? 'parent_plan_continuation' : 'envelope_entry',
    scu_id: candidate.scu_id,
    binding_id: candidate.binding_id,
    capability_uri: capabilityUri,
    frontier_id: candidate.frontier_id ?? null,
    frontier_rule_id: candidate.frontier_rule_id ?? null,
    source_item_id: candidate.source_item_id ?? null,
    source_scu_id: candidate.source_scu_id ?? null,
    envelope_hash: envelope?.envelope_hash ?? null,
    envelope_entry_id: entry?.entry_id ?? null,
    entitlement: effectiveNow,
    limit_state: limitState,
  } as const
  const refuse = (code: SuccessorAdmissionCode) => seal(code === 'successor_safety_excluded'
    // The wire carries a count-level fact, never the identity of a capability the safety pass removed.
    ? { ...base, binding_id: null, capability_uri: null, envelope_entry_id: null, decision: 'refuse', code }
    : { ...base, decision: 'refuse', code })

  // Outside the envelope (or no/forged envelope): the long-standing named gap.
  if (!planContinuation) {
    if (!envelope || !entry) return refuse('successor_capability_not_authorized_for_request')
    if (candidate.binding_id !== null && candidate.binding_id !== entry.binding_id) {
      return refuse('successor_capability_not_authorized_for_request')
    }
  }
  // 8 — the receipt must be completable before anything else is trusted. A rule id is required
  // only when a rule proposed the capability (a pagination continuation has none).
  if (!candidate.frontier_id || (!planContinuation && !candidate.frontier_rule_id) || !candidate.source_item_id
    || !candidate.source_scu_id || candidate.source_served !== true) {
    return refuse('successor_receipt_incomplete')
  }
  // 4 — identity: same chart, principal, overlay, served build and pinned catalogue.
  if (live.chart_id !== contract.chart_id || (envelope !== undefined && envelope.chart_id !== contract.chart_id)) return refuse('successor_chart_mismatch')
  if (live.principal_subject !== live.owner_principal_subject) return refuse('successor_principal_mismatch')
  if (live.overlay_version !== contract.chart_availability_version || live.build_id !== contract.chart_build_id
    || snapshot.content_hash !== contract.capability_content_hash
    || (envelope !== undefined && envelope.capability_content_hash !== snapshot.content_hash)) {
    return refuse('successor_build_identity_mismatch')
  }
  // 2 — present in the pinned catalogue AND the live registry, executable on the active channel.
  const descriptor = capabilityUri ? live.describe(capabilityUri) : undefined
  if (!scu || !binding || !capabilityUri || !descriptor || !live.tool_exists(capabilityUri)) return refuse('successor_capability_not_in_catalogue')
  if (candidate.binding_id === null || !isInquiryServerDispatchEligible(binding, live.transport)) return refuse('successor_channel_not_eligible')
  // 1 — read-only, from the descriptor's own metadata and the shared safety predicate.
  if (!isReadOnlyDescriptor(binding, descriptor)) return refuse('successor_capability_not_read_only')
  // 3 — deterministic relevance: the rule must admit this entry and target this SCU, and the
  // evidence must have come from a different SCU the contract itself planned and observed. (A
  // plan continuation is relevant by construction: it IS the planned capability's next page.)
  const sourceItem = contract.plan_items.find((item) => item.item_id === candidate.source_item_id)
  if (planContinuation) {
    if (!sourceItem || sourceItem.scu_id !== candidate.source_scu_id) return refuse('successor_frontier_not_relevant')
  } else {
    const rule = EVIDENCE_FRONTIER_RULES.find((candidateRule) => candidateRule.rule_id === candidate.frontier_rule_id)
    if (!rule || !entry || !entry.admitting_rule_ids.includes(rule.rule_id) || !rule.target_scu_ids.includes(entry.scu_id)
      || !sourceItem || sourceItem.scu_id !== candidate.source_scu_id || sourceItem.scu_id === entry.scu_id) {
      return refuse('successor_frontier_not_relevant')
    }
  }
  // 5 — the caller's chart permission (the door's own authorization result) and entitlement tier.
  if (live.chart_permission !== 'all' && live.chart_permission !== 'view') return refuse('successor_chart_access_not_verified')
  // The tier a capability must fit under is the LOWEST of: what the door's verified permission grants
  // right now, what the (hash-bound) envelope was granted, and the semantic scope (which only narrows).
  // Nothing caller-, planner- or storage-supplied can raise it above the live server-derived grant.
  const grantedTier = lowerEntitlementTier(
    lowerEntitlementTier(effectiveNow.tier, storedGrantTier(envelope, effectiveNow.tier)),
    contract.scope_tuple.entitlement,
  )
  if (!entitlementTierPermitted(scu.entitlement, grantedTier)) return refuse('successor_entitlement_not_permitted')
  // 7 — the request's own safety and no-leakage exclusions still apply to a successor.
  if (live.is_capability_denied(capabilityUri)) return refuse('successor_safety_excluded')
  // 6 — depth, iteration and cost ceilings.
  if (chain.depth + 1 > limits.max_successor_depth) return refuse('successor_depth_exceeded')
  if (chain.iterations >= limits.max_chain_iterations) return refuse('successor_iteration_limit_exceeded')
  if (live.cost_exhausted === true || chain.admitted >= limits.max_admitted_successor_items) return refuse('successor_cost_limit_exceeded')
  // The successor budget: unverifiable ledger, unpriced candidate, or a price above what is left all refuse.
  if (!costLedgerValid || candidateUnits === null || candidateUnits > limitState.remaining_units) return refuse('successor_cost_limit_exceeded')
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
  /**
   * True when an independent marker (the durable lifecycle row's parent link) says this contract is
   * a successor. A contract that claims to be one but carries no successor receipt is refused, not
   * treated as an ordinary contract.
   */
  expect_successor?: boolean
}): SuccessorAdmissionDecision | null {
  const successor = args.contract.successor
  if (!successor && !args.expect_successor) return null
  const item = args.contract.plan_items.find((candidate) => candidate.item_id === args.item_id)
  if (!successor || !item) return refusedWithoutReceipt(args.item_id, item?.scu_id ?? '', args.live)
  // The lineage's own seals: the successor receipt hashes itself (and so its embedded parent, whose
  // ledger is part of the shared budget), and records the parent's state hash. A deleted or rewritten
  // ancestor ledger breaks these, which a per-ledger check alone cannot see (an ABSENT ledger reads as
  // zero). Likewise this generation's own ledger must hold an entry for every dispatch it stamped.
  const { successor_hash: recordedSuccessorHash, ...successorBody } = successor
  const ledgerItemIds = new Set((args.contract.successor_cost_ledger?.entries ?? []).map((entry) => entry.item_id))
  const lineageIntact = recordedSuccessorHash === stableFingerprint(successorBody)
    && successor.parent_contract_state_hash === stableFingerprint(successor.parent_contract)
    && args.contract.plan_items.every((candidate) => candidate.successor_dispatch?.decision !== 'admit' || ledgerItemIds.has(candidate.item_id))
  if (!lineageIntact) return refusedWithoutReceipt(args.item_id, item.scu_id, args.live)
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
    // What THIS generation has already been charged, from its own hash-chained ledger; an
    // unverifiable ledger is `null` and exhausts the budget.
    own_ledger_units: args.contract.successor_cost_ledger
      ? (verifySuccessorCostLedger(args.contract.successor_cost_ledger) ? args.contract.successor_cost_ledger.consumed_units : null)
      : 0,
    admitted_in_batch: (() => {
      const decisions = successor.admission_decisions ?? []
      const position = decisions.findIndex((entry) => entry.scu_id === item.scu_id)
      return decisions.slice(0, Math.max(position, 0)).filter((entry) => entry.decision === 'admit').length
    })(),
  })
  // A stored refusal is final; a stored admission must still verify.
  if (!stored || stored.decision === 'refuse' || !verifySuccessorDecision(stored)) {
    const code: SuccessorAdmissionCode = stored?.decision === 'refuse' ? stored.code
      : decision.decision === 'refuse' ? decision.code
      : 'successor_capability_not_authorized_for_request'
    const body = withoutDecisionHash(decision)
    // Whatever code wins, a safety refusal never carries the excluded capability's identity.
    return seal(code === 'successor_safety_excluded'
      ? { ...body, binding_id: null, capability_uri: null, envelope_entry_id: null, decision: 'refuse', code }
      : { ...body, decision: 'refuse', code })
  }
  return decision
}

/**
 * A refused successor item is terminal: `recordInquiryExecution` re-readies a failed item while
 * iterations remain, but retrying something that was never authorized would strand the lifecycle.
 * Every door applies this same transition so refusals leave the same contract shape everywhere.
 */
export function terminalizeRefusedSuccessorItem(contract: InquiryContract, itemId: string): InquiryContract {
  return {
    ...contract,
    plan_items: contract.plan_items.map((candidate) => candidate.item_id === itemId
      ? { ...candidate, state: 'observed' as const }
      : candidate),
  }
}

/**
 * The one post-evaluation gate every door applies immediately before it would dispatch an ADMITTED
 * successor item: the live tool and binding must still resolve and the arguments must still be the
 * authorized ones. Anything else turns the admit into a definitive, receipted refusal (same codes,
 * same receipt fields on every door) instead of an admit stamped on a dispatch that never happened.
 * Refusals and non-successor items pass through untouched.
 */
export function refineSuccessorAdmission(
  admission: SuccessorAdmissionDecision | null,
  gates: { readonly tool_present: boolean; readonly binding_present: boolean; readonly args_authorized: boolean },
): SuccessorAdmissionDecision | null {
  if (admission === null || admission.decision !== 'admit') return admission
  if (!gates.tool_present || !gates.binding_present) return refuseAdmittedSuccessor(admission, 'successor_capability_not_in_catalogue')
  if (!gates.args_authorized) return refuseAdmittedSuccessor(admission, 'successor_arguments_not_authorized')
  return admission
}

/**
 * Turn an admission into a definitive refusal for a reason only the door can see after the evaluator
 * admitted (unauthorized or tampered arguments, a binding that vanished between evaluation and
 * dispatch). The refusal carries the same receipt fields, so every door records it identically.
 */
export function refuseAdmittedSuccessor(decision: SuccessorAdmissionDecision, code: SuccessorAdmissionCode): SuccessorAdmissionDecision {
  return seal({ ...withoutDecisionHash(decision), decision: 'refuse', code })
}

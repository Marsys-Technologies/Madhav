/**
 * Packet B: the one shared, deterministic, bounded authorization envelope.
 *
 * Every test drives the real compiler over the pinned snapshot. The all-conditions-admit case is the
 * baseline; each of the eight conditions is then broken independently and must refuse with its own
 * stable named code (never a shared catch-all).
 */
import { describe, expect, it } from 'vitest'
import generatedCapabilityKnowledge from '../../../generated/capability_knowledge.snapshot.json'
import type { CapabilityKnowledgeSnapshot } from '../../retrieval/registry/knowledge/types'
import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import {
  AUTHORIZATION_ENVELOPE_VERSION,
  MAX_ADMITTED_SUCCESSOR_ITEMS,
  MAX_CHAIN_ITERATIONS,
  MAX_SUCCESSOR_DEPTH,
  authorizationEnvelopeHash,
  buildAuthorizationEnvelope,
  deriveSuccessorEnvelope,
  evaluateSuccessorAdmission,
  evaluateSuccessorItemForDispatch,
  verifySuccessorDecision,
  type SuccessorAdmissionLiveContext,
} from './authorization_envelope'
import {
  closeInquiryForEvidenceSuccessor,
  compileInquiryContract,
  compileInquirySuccessorContract,
  inquiryAuthorizationHashes,
  recordInquiryExecution,
} from './compiler'
import { deriveEvidenceFrontier } from './evidence_frontier'
import { EVIDENCE_FRONTIER_RULES } from './evidence_frontier'
import type { InquiryContract } from './types'

const snapshot = generatedCapabilityKnowledge as CapabilityKnowledgeSnapshot
const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const PRINCIPAL = 'principal-1'
const SCOPE = { intent: 'timing', domains: ['general'], width: 'narrow', depth: 'retrieval', horizon: 'current', intervention: 'none', entitlement: 'native' }

function compile(question = 'What is my current dasha?', scope = SCOPE): InquiryContract {
  return compileInquiryContract({
    snapshot, chart_id: CHART_ID, question, scope_tuple: scope as never, temporal_anchor_date: '2026-09-27',
  })
}

/** A compiled contract that leaves at least one rule target unplanned, with the entry that authorizes it. */
function fixture() {
  for (const question of ['What is my current dasha?', 'Which planets are in which signs?']) {
    const contract = compile(question)
    const planned = new Set(contract.plan_items.map((item) => item.scu_id))
    const entry = contract.authorization_envelope?.entries.find((candidate) => !planned.has(candidate.scu_id))
    const source = contract.plan_items.find((item) => item.state === 'ready' && item.scu_id !== entry?.scu_id)
    if (entry && source) return { contract, entry, source }
  }
  throw new Error('no fixture contract produced an envelope entry')
}

function liveFor(contract: InquiryContract, overrides: Partial<SuccessorAdmissionLiveContext> = {}): SuccessorAdmissionLiveContext {
  const bindings = new Map(snapshot.scus.flatMap((scu) => scu.bindings.map((binding) => [binding.capability_uri, binding] as const)))
  return {
    transport: 'portal',
    chart_id: contract.chart_id,
    principal_subject: PRINCIPAL,
    owner_principal_subject: PRINCIPAL,
    chart_permission: 'all',
    overlay_version: contract.chart_availability_version,
    build_id: contract.chart_build_id,
    describe: (uri) => bindings.has(uri) ? { uri, mutation: false, calibration_context_only: false, mcp_annotations: { readOnly: true } } : undefined,
    tool_exists: (uri) => bindings.has(uri),
    is_capability_denied: () => false,
    cost_exhausted: false,
    ...overrides,
  }
}

function candidateFor(entry: { scu_id: string; binding_id: string }, source: { item_id: string; scu_id: string }, rule = 'evidence_bhanga_active') {
  return {
    scu_id: entry.scu_id, binding_id: entry.binding_id, frontier_id: 'frontier-001', frontier_rule_id: rule,
    source_item_id: source.item_id, source_scu_id: source.scu_id, source_served: true,
  }
}

function evaluate(
  base: ReturnType<typeof fixture>,
  changes: { candidate?: Record<string, unknown>; live?: Partial<SuccessorAdmissionLiveContext>; contract?: Partial<InquiryContract>; snapshot?: CapabilityKnowledgeSnapshot; envelope?: InquiryContract['authorization_envelope'] | null } = {},
) {
  const rule = EVIDENCE_FRONTIER_RULES.find((candidate) => candidate.target_scu_ids.includes(base.entry.scu_id))!
  const contract = { ...base.contract, ...(changes.contract ?? {}) } as InquiryContract
  return evaluateSuccessorAdmission({
    envelope: changes.envelope === null ? undefined : changes.envelope ?? base.contract.authorization_envelope,
    snapshot: changes.snapshot ?? snapshot,
    candidate: { ...candidateFor(base.entry, base.source, rule.rule_id), ...(changes.candidate ?? {}) } as never,
    contract,
    live: liveFor(contract, changes.live),
  })
}

describe('envelope construction (plan time, before any evidence)', () => {
  it('is a deterministic, versioned, sorted, self-hashed structure on every compiled contract', () => {
    const { contract } = fixture()
    const envelope = contract.authorization_envelope!
    expect(envelope.envelope_version).toBe(AUTHORIZATION_ENVELOPE_VERSION)
    expect(envelope.chart_id).toBe(CHART_ID)
    expect(envelope.capability_content_hash).toBe(snapshot.content_hash)
    expect(envelope.envelope_hash).toBe(authorizationEnvelopeHash(envelope))
    expect(envelope.entries.map((entry) => entry.scu_id)).toEqual([...envelope.entries.map((entry) => entry.scu_id)].sort())
    for (const entry of envelope.entries) {
      expect(entry.admitting_rule_ids.length).toBeGreaterThan(0)
      expect([...entry.admitting_rule_ids]).toEqual([...entry.admitting_rule_ids].sort())
      expect(entry.binding_id).toBe(`registry:${entry.capability_uri}`)
    }
    // Same inputs, same envelope, byte for byte.
    expect(compile().authorization_envelope).toEqual(compile().authorization_envelope)
  })

  it('carries only capabilities a frontier rule can propose that the plan does not already contain', () => {
    const { contract } = fixture()
    const planned = new Set(contract.plan_items.map((item) => item.scu_id))
    const ruleTargets = new Set(EVIDENCE_FRONTIER_RULES.flatMap((rule) => rule.target_scu_ids))
    for (const entry of contract.authorization_envelope!.entries) {
      expect(ruleTargets.has(entry.scu_id)).toBe(true)
      expect(planned.has(entry.scu_id)).toBe(false)
    }
  })

  it('is bound into the execution-plan (authorization) hash and its recomputation', () => {
    const { contract } = fixture()
    expect(inquiryAuthorizationHashes(contract).execution_plan_hash).toBe(contract.execution_plan_hash)
    const widened = { ...contract, authorization_envelope: { ...contract.authorization_envelope!, entries: [] } }
    expect(inquiryAuthorizationHashes(widened as InquiryContract).execution_plan_hash).not.toBe(contract.execution_plan_hash)
  })

  it('excludes a target that is not relevant to the compiled inquiry (no graph anchor, no domain overlap)', () => {
    const targets = new Set(EVIDENCE_FRONTIER_RULES.flatMap((rule) => rule.target_scu_ids))
    const isolated = {
      ...snapshot,
      edges: snapshot.edges.filter((edge) => !targets.has(edge.from_scu_id) && !targets.has(edge.to_scu_id)),
      scus: snapshot.scus.map((scu) => targets.has(scu.scu_id) ? { ...scu, domains: ['unrelated'] } : scu),
    } as CapabilityKnowledgeSnapshot
    const scope = { domains: ['career'], entitlement: 'native' }
    const anchors = fixture().contract.plan_items.map((item) => item.scu_id)
    const args = { chart_id: CHART_ID, execution_channel: 'platform_internal' as const, scope, planned_scu_ids: anchors, anchor_scu_ids: anchors }
    expect(buildAuthorizationEnvelope({ snapshot: isolated, ...args }).entries).toEqual([])
    expect(buildAuthorizationEnvelope({ snapshot, ...args }).entries.length).toBeGreaterThan(0)
  })

  it('narrows to nothing when the caller scope entitlement is below the capability tier', () => {
    const args = { snapshot, chart_id: CHART_ID, execution_channel: 'platform_internal' as const, planned_scu_ids: [], anchor_scu_ids: [] }
    expect(buildAuthorizationEnvelope({ ...args, scope: { domains: ['general'], entitlement: 'native' } }).entries.length).toBeGreaterThan(0)
    for (const tier of ['public_disclosed', 'restricted', 'reference', 'unknown_tier']) {
      expect(buildAuthorizationEnvelope({ ...args, scope: { domains: ['general'], entitlement: tier } }).entries, tier).toEqual([])
    }
  })

  it('derives a successor envelope that can only shrink (no recursive widening)', () => {
    const { contract, entry } = fixture()
    const parent = contract.authorization_envelope!
    const child = deriveSuccessorEnvelope(parent, { consumed_scu_ids: [entry.scu_id] })
    expect(child.parent_envelope_hash).toBe(parent.envelope_hash)
    expect(child.entries.map((e) => e.scu_id)).not.toContain(entry.scu_id)
    for (const childEntry of child.entries) expect(parent.entries).toContainEqual(childEntry)
    expect(child.envelope_hash).toBe(authorizationEnvelopeHash(child))
  })
})

describe('shared evaluator: all eight conditions admit', () => {
  it('admits a relevant, entitled, read-only, in-catalogue, in-limit, receipted successor', () => {
    const base = fixture()
    const decision = evaluate(base)
    expect(decision).toMatchObject({
      decision: 'admit', code: 'successor_admitted', scu_id: base.entry.scu_id, binding_id: base.entry.binding_id,
      capability_uri: base.entry.capability_uri, frontier_id: 'frontier-001',
      source_item_id: base.source.item_id, source_scu_id: base.source.scu_id,
      envelope_hash: base.contract.authorization_envelope!.envelope_hash, envelope_entry_id: base.entry.entry_id,
    })
    expect(decision.frontier_rule_id).toBeTruthy()
    expect(decision.limit_state).toMatchObject({ successor_depth: 0, max_successor_depth: MAX_SUCCESSOR_DEPTH, cost_exhausted: false })
    expect(verifySuccessorDecision(decision)).toBe(true)
  })

  it('is a pure function of its inputs (identical inputs, identical decision hash)', () => {
    const base = fixture()
    expect(evaluate(base).decision_hash).toBe(evaluate(base).decision_hash)
  })
})

describe('shared evaluator: each condition fails independently with its own named code', () => {
  const base = fixture()
  const rule = EVIDENCE_FRONTIER_RULES.find((candidate) => candidate.target_scu_ids.includes(base.entry.scu_id))!

  it('capability outside the envelope -> successor_capability_not_authorized_for_request', () => {
    const outside = snapshot.scus.find((scu) => !base.contract.authorization_envelope!.entries.some((e) => e.scu_id === scu.scu_id))!
    const binding = outside.bindings[0]!
    expect(evaluate(base, { candidate: { scu_id: outside.scu_id, binding_id: binding.binding_id } })).toMatchObject({
      decision: 'refuse', code: 'successor_capability_not_authorized_for_request', envelope_entry_id: null,
    })
  })

  it('a contract with no envelope at all authorizes nothing', () => {
    expect(evaluate(base, { envelope: null })).toMatchObject({ decision: 'refuse', code: 'successor_capability_not_authorized_for_request' })
  })

  it('an envelope whose hash no longer matches its content authorizes nothing', () => {
    const forged = { ...base.contract.authorization_envelope!, entries: [...base.contract.authorization_envelope!.entries, { ...base.entry, scu_id: 'scu.forged', entry_id: 'env:scu.forged' }] }
    expect(evaluate(base, { envelope: forged })).toMatchObject({ decision: 'refuse', code: 'successor_capability_not_authorized_for_request' })
  })

  it('(1) write-capable capability -> successor_capability_not_read_only', () => {
    const uri = base.entry.capability_uri
    for (const flags of [{ mutation: true }, { calibration_context_only: true }, { mcp_annotations: { readOnly: false } }]) {
      const decision = evaluate(base, { live: { describe: (candidate) => candidate === uri ? { uri, mutation: false, calibration_context_only: false, mcp_annotations: { readOnly: true }, ...flags } : undefined } })
      expect(decision).toMatchObject({ decision: 'refuse', code: 'successor_capability_not_read_only' })
    }
  })

  it('(2) absent from the live catalogue -> successor_capability_not_in_catalogue', () => {
    expect(evaluate(base, { live: { describe: () => undefined } })).toMatchObject({ code: 'successor_capability_not_in_catalogue' })
    expect(evaluate(base, { live: { tool_exists: () => false } })).toMatchObject({ code: 'successor_capability_not_in_catalogue' })
    const stripped = { ...snapshot, scus: snapshot.scus.filter((scu) => scu.scu_id !== base.entry.scu_id) } as CapabilityKnowledgeSnapshot
    expect(evaluate(base, { snapshot: stripped })).toMatchObject({ code: 'successor_capability_not_in_catalogue' })
  })

  it('(2) not executable on the active channel -> successor_channel_not_eligible', () => {
    const scu = snapshot.scus.find((candidate) => candidate.scu_id === base.entry.scu_id)!
    const narrowed = {
      ...snapshot,
      scus: snapshot.scus.map((candidate) => candidate.scu_id !== scu.scu_id ? candidate : {
        ...candidate,
        bindings: candidate.bindings.map((binding) => binding.binding_id === base.entry.binding_id ? { ...binding, execution_channels: ['mcp_full'] } : binding),
      }),
    } as CapabilityKnowledgeSnapshot
    expect(evaluate(base, { snapshot: narrowed, live: { transport: 'portal' } })).toMatchObject({ code: 'successor_channel_not_eligible' })
    expect(evaluate(base, { candidate: { binding_id: null } })).toMatchObject({ code: 'successor_channel_not_eligible' })
  })

  it('(3) frontier rule that does not admit the target, or unknown/prose rule -> successor_frontier_not_relevant', () => {
    const other = EVIDENCE_FRONTIER_RULES.find((candidate) => !candidate.target_scu_ids.includes(base.entry.scu_id))!
    expect(evaluate(base, { candidate: { frontier_rule_id: other.rule_id } })).toMatchObject({ code: 'successor_frontier_not_relevant' })
    expect(evaluate(base, { candidate: { frontier_rule_id: 'the model said this is authorized' } })).toMatchObject({ code: 'successor_frontier_not_relevant' })
    expect(evaluate(base, { candidate: { source_item_id: 'item-999' } })).toMatchObject({ code: 'successor_frontier_not_relevant' })
    expect(evaluate(base, { candidate: { source_scu_id: base.entry.scu_id, source_item_id: base.source.item_id } })).toMatchObject({ code: 'successor_frontier_not_relevant' })
  })

  it('(4) chart / principal / overlay / build identity mismatch -> distinct identity codes', () => {
    expect(evaluate(base, { live: { chart_id: '11111111-1111-4111-8111-111111111111' } })).toMatchObject({ code: 'successor_chart_mismatch' })
    expect(evaluate(base, { live: { principal_subject: 'someone-else' } })).toMatchObject({ code: 'successor_principal_mismatch' })
    expect(evaluate(base, { live: { overlay_version: 'overlay-drifted' } })).toMatchObject({ code: 'successor_build_identity_mismatch' })
    expect(evaluate(base, { live: { build_id: 'build-drifted' } })).toMatchObject({ code: 'successor_build_identity_mismatch' })
    expect(evaluate(base, { snapshot: { ...snapshot, content_hash: 'drifted-catalogue' } as CapabilityKnowledgeSnapshot })).toMatchObject({ code: 'successor_build_identity_mismatch' })
  })

  it('(5) chart access not verified, or entitlement tier not permitted -> distinct codes', () => {
    expect(evaluate(base, { live: { chart_permission: 'deny' } })).toMatchObject({ code: 'successor_chart_access_not_verified' })
    expect(evaluate(base, { live: { chart_permission: null } })).toMatchObject({ code: 'successor_chart_access_not_verified' })
    expect(evaluate(base, { live: { chart_permission: 'view' } })).toMatchObject({ decision: 'admit' })
    const narrowedScope = { ...base.contract, scope_tuple: { ...base.contract.scope_tuple, entitlement: 'public_disclosed' } }
    expect(evaluate(base, { contract: narrowedScope })).toMatchObject({ code: 'successor_entitlement_not_permitted' })
  })

  it('(6) depth, iteration and cost ceilings -> distinct limit codes', () => {
    let deep = base.contract
    for (let level = 0; level < MAX_SUCCESSOR_DEPTH; level += 1) {
      deep = { ...base.contract, successor: { parent_contract: deep, admitted_frontier: [] } } as unknown as InquiryContract
    }
    expect(evaluate(base, { contract: deep })).toMatchObject({ code: 'successor_depth_exceeded' })
    expect(evaluate(base, { contract: { iteration: MAX_CHAIN_ITERATIONS } })).toMatchObject({ code: 'successor_iteration_limit_exceeded' })
    expect(evaluate(base, { live: { cost_exhausted: true } })).toMatchObject({ code: 'successor_cost_limit_exceeded' })
    const crowded = { ...base.contract, successor: { parent_contract: base.contract, admitted_frontier: Array.from({ length: MAX_ADMITTED_SUCCESSOR_ITEMS }, (_, index) => ({ frontier_id: `f-${index}` })) } } as unknown as InquiryContract
    expect(evaluate(base, { contract: crowded })).toMatchObject({ code: 'successor_cost_limit_exceeded' })
  })

  it('(7) request-time safety / no-leakage exclusion -> successor_safety_excluded', () => {
    expect(evaluate(base, { live: { is_capability_denied: (uri) => uri === base.entry.capability_uri } })).toMatchObject({ code: 'successor_safety_excluded' })
  })

  it('(8) incomplete admission receipt -> successor_receipt_incomplete', () => {
    for (const missing of ['frontier_id', 'frontier_rule_id', 'source_item_id', 'source_scu_id']) {
      expect(evaluate(base, { candidate: { [missing]: null } }), missing).toMatchObject({ code: 'successor_receipt_incomplete' })
    }
    expect(evaluate(base, { candidate: { source_served: false } })).toMatchObject({ code: 'successor_receipt_incomplete' })
  })

  it('every refusal is receipt-ready: identity, limit state and a verifiable hash', () => {
    const refused = evaluate(base, { live: { cost_exhausted: true } })
    const { decision_hash: recorded, ...body } = refused
    expect(recorded).toBe(stableFingerprint(body))
    expect(verifySuccessorDecision(refused)).toBe(true)
    expect(verifySuccessorDecision({ ...refused, code: 'successor_admitted' as never })).toBe(false)
    expect(rule.rule_id).toBeTruthy()
  })
})


describe('successor compilation runs the envelope on every admitted item (real compiler and lifecycle)', () => {
  /** Serve evidence that fires `evidence_bhanga_active`, close the parent, and return it with the source item. */
  function parentWithEvidence() {
    const base = fixture()
    const rule = EVIDENCE_FRONTIER_RULES.find((candidate) => candidate.target_scu_ids.includes(base.entry.scu_id))!
    const payload = { rows: [{ yoga: 'Raja', fired: true, bhanga_active: rule.rule_id === 'evidence_bhanga_active' || undefined,
      dignity_state: rule.rule_id === 'evidence_debilitation_requires_nichabhanga_check' ? 'debilitated' : undefined,
      activation_dasha_periods: rule.rule_id === 'evidence_activation_periods_require_dashas' ? ['p'] : undefined,
      mechanism_class: rule.rule_id === 'evidence_mechanism_names_houses' ? 'm' : undefined,
      houses: rule.rule_id === 'evidence_mechanism_names_houses' ? [7] : undefined }] }
    const frontier = deriveEvidenceFrontier({ contract: base.contract, item_id: base.source.item_id, evidence_payload: payload, snapshot })
    expect(frontier.find((entry) => entry.scu_id === base.entry.scu_id)?.rule_id).toBe(rule.rule_id)
    let observed = recordInquiryExecution(base.contract, {
      item_id: base.source.item_id, disposition: 'served', evidence_refs: [`raw:${stableFingerprint(payload)}`],
      pagination: { semantics: 'none', exhausted: true, next: null }, evidence_frontier: frontier,
    })
    for (const item of observed.plan_items.filter((candidate) => candidate.state === 'ready')) {
      observed = recordInquiryExecution(observed, {
        item_id: item.item_id, disposition: 'served', evidence_refs: [`raw:${item.item_id}`],
        pagination: { semantics: 'none', exhausted: true, next: null },
      })
    }
    return { ...base, parent: closeInquiryForEvidenceSuccessor(observed) }
  }

  it('attaches a receipted admit decision to the successor item, bound into the authorization hash', () => {
    const { parent, entry, source } = parentWithEvidence()
    const successor = compileInquirySuccessorContract({
      snapshot, parent_inquiry_id: 'parent-1', parent, cross_capability_only: true, admission: liveFor(parent),
    })
    const item = successor.plan_items.find((candidate) => candidate.scu_id === entry.scu_id)!
    expect(item.successor_admission).toMatchObject({
      decision: 'admit', code: 'successor_admitted', source_item_id: source.item_id, envelope_entry_id: entry.entry_id,
    })
    expect(successor.successor?.admission_decisions).toContainEqual(item.successor_admission)
    expect(successor.successor?.admission_decisions).toHaveLength(successor.successor!.admitted_frontier.length)
    expect(successor.successor?.admitted_frontier.find((frontier) => frontier.scu_id === entry.scu_id)?.rule_id)
      .toBe(item.successor_admission!.frontier_rule_id)
    expect(inquiryAuthorizationHashes(successor).execution_plan_hash).toBe(successor.execution_plan_hash)
    const tampered = { ...successor, plan_items: successor.plan_items.map((candidate) => candidate === item
      ? { ...candidate, successor_admission: { ...item.successor_admission!, decision_hash: 'sha256:forged' } } : candidate) }
    expect(inquiryAuthorizationHashes(tampered as InquiryContract).execution_plan_hash).not.toBe(successor.execution_plan_hash)
  })

  it('records a named refusal on the item when the live state refuses it (the item is never silently dropped)', () => {
    const { parent, entry } = parentWithEvidence()
    const successor = compileInquirySuccessorContract({
      snapshot, parent_inquiry_id: 'parent-1', parent, cross_capability_only: true,
      admission: liveFor(parent, { is_capability_denied: () => true }),
    })
    const item = successor.plan_items.find((candidate) => candidate.scu_id === entry.scu_id)!
    expect(item.successor_admission).toMatchObject({ decision: 'refuse', code: 'successor_safety_excluded' })
  })

  it('fails closed when a door supplies no live state: every item is refused as outside the request authority', () => {
    const { parent, entry } = parentWithEvidence()
    const successor = compileInquirySuccessorContract({ snapshot, parent_inquiry_id: 'parent-1', parent, cross_capability_only: true })
    const item = successor.plan_items.find((candidate) => candidate.scu_id === entry.scu_id)!
    expect(item.successor_admission).toMatchObject({ decision: 'refuse', code: 'successor_capability_not_authorized_for_request' })
  })

  it('the successor envelope only shrinks: the admitted capability and everything planned are consumed', () => {
    const { parent, entry } = parentWithEvidence()
    const successor = compileInquirySuccessorContract({
      snapshot, parent_inquiry_id: 'parent-1', parent, cross_capability_only: true, admission: liveFor(parent),
    })
    const child = successor.authorization_envelope!
    expect(child.parent_envelope_hash).toBe(parent.authorization_envelope!.envelope_hash)
    expect(child.entries.map((e) => e.scu_id)).not.toContain(entry.scu_id)
    const parentScus = new Set(parent.authorization_envelope!.entries.map((e) => e.scu_id))
    for (const e of child.entries) expect(parentScus.has(e.scu_id)).toBe(true)
    // ...so evidence in the successor can never re-admit a capability the lineage already used.
    const readmission = evaluateSuccessorAdmission({
      envelope: child, snapshot,
      candidate: { scu_id: entry.scu_id, binding_id: entry.binding_id, frontier_id: 'f', frontier_rule_id: entry.admitting_rule_ids[0]!, source_item_id: successor.plan_items[0]!.item_id, source_scu_id: successor.plan_items[0]!.scu_id, source_served: true },
      contract: successor, live: liveFor(successor),
    })
    expect(readmission).toMatchObject({ decision: 'refuse', code: 'successor_capability_not_authorized_for_request' })
  })

  it('a successor item without an explicit rule id (legacy or forged frontier) is refused as receipt-incomplete', () => {
    const { parent, entry } = parentWithEvidence()
    const stripped = { ...parent, material_frontier: parent.material_frontier.map((frontier) => { const rest: Record<string, unknown> = { ...frontier }; delete rest['rule_id']; return rest }) }
    const successor = compileInquirySuccessorContract({
      snapshot, parent_inquiry_id: 'parent-1', parent: stripped as unknown as InquiryContract, cross_capability_only: true, admission: liveFor(parent),
    })
    const item = successor.plan_items.find((candidate) => candidate.scu_id === entry.scu_id)!
    expect(item.successor_admission).toMatchObject({ decision: 'refuse', code: 'successor_receipt_incomplete' })
  })
})


describe('evaluator hardening (review findings)', () => {
  const base = fixture()

  it('does not disclose which capability the safety pass removed: the refusal is redacted to the SCU and code', () => {
    const decision = evaluate(base, { live: { is_capability_denied: () => true } })
    expect(decision).toMatchObject({ code: 'successor_safety_excluded', binding_id: null, capability_uri: null, envelope_entry_id: null })
    expect(verifySuccessorDecision(decision)).toBe(true)
  })

  it('a stored envelope can only tighten the platform ceilings, never loosen them', () => {
    const inflated = { ...base.contract.authorization_envelope!, limits: { max_successor_depth: 99, max_admitted_successor_items: 99, max_chain_iterations: 9999 } }
    const sealed = { ...inflated, envelope_hash: authorizationEnvelopeHash(inflated) }
    const decision = evaluate(base, { envelope: sealed, contract: { iteration: MAX_CHAIN_ITERATIONS } })
    expect(decision).toMatchObject({ code: 'successor_iteration_limit_exceeded' })
    expect(decision.limit_state.max_chain_iterations).toBe(MAX_CHAIN_ITERATIONS)
  })

  it('depth boundary: the last generation below the ceiling admits, the ceiling itself refuses', () => {
    const nest = (levels: number) => {
      let contract = base.contract
      for (let level = 0; level < levels; level += 1) {
        contract = { ...base.contract, successor: { parent_contract: contract, admitted_frontier: [], admission_decisions: [] } } as unknown as InquiryContract
      }
      return contract
    }
    expect(evaluate(base, { contract: nest(MAX_SUCCESSOR_DEPTH - 1) })).toMatchObject({ decision: 'admit' })
    expect(evaluate(base, { contract: nest(MAX_SUCCESSOR_DEPTH) })).toMatchObject({ code: 'successor_depth_exceeded' })
  })

  it('a capped same-capability pagination frontier is authorized by the parent plan, and still clears every other condition', () => {
    const planned = base.contract.plan_items.find((item) => item.binding_id !== null)!
    const continuation = { scu_id: planned.scu_id, binding_id: planned.binding_id, frontier_id: 'frontier-001', frontier_rule_id: null, source_item_id: planned.item_id, source_scu_id: planned.scu_id, source_served: true }
    const admitted = evaluate(base, { candidate: continuation, envelope: null })
    expect(admitted).toMatchObject({ decision: 'admit', authority: 'parent_plan_continuation', envelope_entry_id: null })
    expect(verifySuccessorDecision(admitted)).toBe(true)
    expect(evaluate(base, { candidate: continuation, envelope: null, live: { is_capability_denied: () => true } })).toMatchObject({ code: 'successor_safety_excluded' })
    expect(evaluate(base, { candidate: continuation, envelope: null, live: { chart_permission: 'deny' } })).toMatchObject({ code: 'successor_chart_access_not_verified' })
    expect(evaluate(base, { candidate: continuation, envelope: null, live: { cost_exhausted: true } })).toMatchObject({ code: 'successor_cost_limit_exceeded' })
    expect(evaluate(base, { candidate: continuation, envelope: null, live: { describe: () => undefined } })).toMatchObject({ code: 'successor_capability_not_in_catalogue' })
    // A same-SCU claim for a capability the parent plan does NOT contain is not a continuation.
    expect(evaluate(base, { candidate: { ...continuation, scu_id: base.entry.scu_id, binding_id: base.entry.binding_id, source_scu_id: base.entry.scu_id }, envelope: null }))
      .toMatchObject({ decision: 'refuse', code: 'successor_capability_not_authorized_for_request' })
  })

  it('a contract that claims to be a successor but carries no successor receipt is refused, never treated as ordinary', () => {
    const item = base.contract.plan_items[0]!
    expect(evaluateSuccessorItemForDispatch({ contract: base.contract, item_id: item.item_id, snapshot, live: liveFor(base.contract) })).toBeNull()
    expect(evaluateSuccessorItemForDispatch({ contract: base.contract, item_id: item.item_id, snapshot, live: liveFor(base.contract), expect_successor: true }))
      .toMatchObject({ decision: 'refuse', code: 'successor_receipt_incomplete' })
    expect(evaluateSuccessorItemForDispatch({ contract: base.contract, item_id: 'item-999', snapshot, live: liveFor(base.contract), expect_successor: true }))
      .toMatchObject({ decision: 'refuse' })
  })

  it('pre-envelope contracts hash exactly as before: no envelope and no admission add nothing to the authorization projection', () => {
    const contract = base.contract
    const legacy = { ...contract } as Record<string, unknown>
    delete legacy['authorization_envelope']
    const projection = (contract.plan_items).map((item) => ({
      item_id: item.item_id, obligation_ids: item.obligation_ids, scu_id: item.scu_id, binding_id: item.binding_id,
      args: item.authorization_args ?? item.args, argument_resolution: item.argument_resolution, depends_on: item.depends_on,
      state: item.blocked_reason ? 'blocked' : 'ready', blocked_reason: item.blocked_reason,
    }))
    const hashes = inquiryAuthorizationHashes(legacy as unknown as InquiryContract)
    expect(hashes.execution_plan_hash).toBe(stableFingerprint({
      semantic_contract_hash: hashes.semantic_contract_hash, chart_id: contract.chart_id,
      execution_channel: contract.execution_channel, plan_items: projection,
    }))
  })

  it('a successor whose parent predates the envelope has no authority: every item is refused as outside the request authority', () => {
    const { parent, entry } = (() => {
      const base2 = fixture()
      const rule = EVIDENCE_FRONTIER_RULES.find((candidate) => candidate.target_scu_ids.includes(base2.entry.scu_id))!
      const payload = { rows: [{ bhanga_active: true, dignity_state: 'debilitated', activation_dasha_periods: ['p'], mechanism_class: 'm', houses: [7] }] }
      const frontier = deriveEvidenceFrontier({ contract: base2.contract, item_id: base2.source.item_id, evidence_payload: payload, snapshot })
      let observed = recordInquiryExecution(base2.contract, { item_id: base2.source.item_id, disposition: 'served', evidence_refs: ['raw:x'], pagination: { semantics: 'none', exhausted: true, next: null }, evidence_frontier: frontier })
      for (const item of observed.plan_items.filter((candidate) => candidate.state === 'ready')) {
        observed = recordInquiryExecution(observed, { item_id: item.item_id, disposition: 'served', evidence_refs: [`raw:${item.item_id}`], pagination: { semantics: 'none', exhausted: true, next: null } })
      }
      const closed = closeInquiryForEvidenceSuccessor(observed) as unknown as Record<string, unknown>
      delete closed['authorization_envelope']
      expect(rule.rule_id).toBeTruthy()
      return { parent: closed as unknown as InquiryContract, entry: base2.entry }
    })()
    const successor = compileInquirySuccessorContract({ snapshot, parent_inquiry_id: 'legacy', parent, cross_capability_only: true, admission: liveFor(parent) })
    const item = successor.plan_items.find((candidate) => candidate.scu_id === entry.scu_id)!
    expect(item.successor_admission).toMatchObject({ decision: 'refuse', code: 'successor_capability_not_authorized_for_request' })
  })

  it('a multi-item successor records an independent decision per item', () => {
    // Two targets fire from the same evidence; deny exactly one of them.
    const base2 = fixture()
    const payload = { rows: [{ bhanga_active: true, dignity_state: 'debilitated', activation_dasha_periods: ['p'], mechanism_class: 'm', houses: [7] }] }
    const frontier = deriveEvidenceFrontier({ contract: base2.contract, item_id: base2.source.item_id, evidence_payload: payload, snapshot })
    let observed = recordInquiryExecution(base2.contract, { item_id: base2.source.item_id, disposition: 'served', evidence_refs: ['raw:x'], pagination: { semantics: 'none', exhausted: true, next: null }, evidence_frontier: frontier })
    for (const item of observed.plan_items.filter((candidate) => candidate.state === 'ready')) {
      observed = recordInquiryExecution(observed, { item_id: item.item_id, disposition: 'served', evidence_refs: [`raw:${item.item_id}`], pagination: { semantics: 'none', exhausted: true, next: null } })
    }
    const parent = closeInquiryForEvidenceSuccessor(observed)
    const entries = base2.contract.authorization_envelope!.entries
    const targets = parent.material_frontier.filter((entry) => entries.some((candidate) => candidate.scu_id === entry.scu_id)).map((entry) => entry.scu_id)
    expect(targets.length, 'the fixture must leave two envelope targets to split').toBeGreaterThanOrEqual(2)
    const denyUri = entries.find((entry) => entry.scu_id === targets[0])!.capability_uri
    const successor = compileInquirySuccessorContract({
      snapshot, parent_inquiry_id: 'multi', parent, cross_capability_only: true,
      admission: liveFor(parent, { is_capability_denied: (uri) => uri === denyUri }),
    })
    const codes = successor.plan_items.map((item) => item.successor_admission?.code)
    expect(codes).toContain('successor_safety_excluded')
    expect(codes).toContain('successor_admitted')
  })
})

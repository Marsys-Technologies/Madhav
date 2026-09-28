/**
 * One shared successor-envelope scenario for the door tests (Portal, managed MCP, raw MCP), so
 * "identical decisions and receipt fields on every door" is asserted against ONE expectation
 * instead of three independently written ones. Test-only.
 */
import generatedSnapshot from '../../../../generated/capability_knowledge.snapshot.json'
import type { CapabilityKnowledgeSnapshot, ChartCapabilityOverlay, ExecutionChannel } from '../../../retrieval/registry/knowledge/types'
import { closeInquiryForEvidenceSuccessor, compileInquiryContract, compileInquirySuccessorContract, recordInquiryExecution } from '../compiler'
import { deriveEvidenceFrontier } from '../evidence_frontier'
import { evaluateSuccessorItemForDispatch, type SuccessorAdmissionDecision } from '../authorization_envelope'
import type { InquiryContract } from '../types'

export const SCENARIO_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
export const SCENARIO_SNAPSHOT = generatedSnapshot as CapabilityKnowledgeSnapshot
export const SCENARIO_QUESTION = 'What is my current dasha?'
/** Valid for every door's scope schema (raw accepts both vocabularies; managed validates strictly). */
export const SCENARIO_SCOPE = {
  intent: 'dasha_timing', domains: ['general'], width: 'narrow', depth: 'standard',
  horizon: 'present', intervention: 'none', entitlement: 'native',
} as const
/** The frontier targets a rule can propose; the scenario picks whichever the plan leaves unplanned. */
export const SCENARIO_TARGET_SCUS = ['scu.yoga.firing_and_cancellation', 'scu.catalog.judgment_query'] as const

/** Every executable registry binding proven available on both internal and raw channels. */
export const SCENARIO_OVERLAY: ChartCapabilityOverlay = {
  chart_id: SCENARIO_CHART_ID, overlay_version: 'sha256:successor-scenario-overlay',
  capability_compatibility_version: SCENARIO_SNAPSHOT.compatibility_version, catalog_content_hash: SCENARIO_SNAPSHOT.content_hash,
  build_id: 'generation:successor-scenario', code_revision: 'fixture', writer_inventory_hash: null,
  generated_at: '2026-09-27T00:00:00.000Z',
  availability: SCENARIO_SNAPSHOT.scus.map((scu) => ({
    scu_id: scu.scu_id, state: 'available' as const, build_status: 'served_generation', build_id: 'generation:successor-scenario',
    freshness: 'fixture', gaps: [], asset_receipts: [],
    available_binding_ids: scu.bindings.filter((binding) => binding.executable).map((binding) => binding.binding_id),
  })),
}

export function compileScenarioRoot(channel: ExecutionChannel = 'platform_internal'): InquiryContract {
  return compileInquiryContract({
    snapshot: SCENARIO_SNAPSHOT, overlay: SCENARIO_OVERLAY, chart_id: SCENARIO_CHART_ID, question: SCENARIO_QUESTION,
    scope_tuple: SCENARIO_SCOPE as never, execution_channel: channel,
    server_authorization: { chart_permission: 'all' },
    temporal_anchor_date: new Date().toISOString().slice(0, 10), temporal_anchor_source: 'request_context_clock',
  })
}

export function scenarioFixture(channel: ExecutionChannel = 'platform_internal') {
  const contract = compileScenarioRoot(channel)
  const planned = new Set(contract.plan_items.map((item) => item.scu_id))
  const entry = contract.authorization_envelope!.entries
    .find((candidate) => (SCENARIO_TARGET_SCUS as readonly string[]).includes(candidate.scu_id) && !planned.has(candidate.scu_id))
  const source = contract.plan_items.find((item) => item.state === 'ready' && item.binding_id
    && contract.obligations.some((o) => item.obligation_ids.includes(o.obligation_id) && o.materiality === 'required'))
  if (!entry || !source?.binding_id) throw new Error('scenario has no envelope entry or required source item')
  return { contract, entry, source, sourceUri: source.binding_id.slice('registry:'.length), targetUri: entry.capability_uri }
}

/**
 * The receipt fields that must be identical on every door for the same pinned contract and
 * frontier. Contract-local identifiers (item ids, decision/envelope hashes, which embed the door's
 * execution channel) are deliberately excluded; everything that names the DECISION is included.
 */
export function projectDecision(decision: SuccessorAdmissionDecision) {
  return {
    decision: decision.decision,
    code: decision.code,
    scu_id: decision.scu_id,
    binding_id: decision.binding_id,
    capability_uri: decision.capability_uri,
    frontier_rule_id: decision.frontier_rule_id,
    source_scu_id: decision.source_scu_id,
    envelope_entry_id: decision.envelope_entry_id,
    entitlement: decision.entitlement,
    limit_state: decision.limit_state,
  }
}

/**
 * The receipt projection every door must produce for the scenario's admitted successor, derived
 * once from the shared compiler path: serve the scenario's root plan the way every door does (the
 * trigger source item carries a cancellation-active row), close the parent, compile the successor
 * with a permissive live state, and project the decision for the scenario's target.
 */
function permissiveScenarioLive(parent: InquiryContract) {
  return {
    transport: 'portal' as const, chart_id: parent.chart_id, principal_subject: 'p', owner_principal_subject: 'p', chart_permission: 'all' as const,
    overlay_version: parent.chart_availability_version, build_id: parent.chart_build_id,
    describe: (uri: string) => ({ uri, mutation: false, calibration_context_only: false }), tool_exists: () => true,
    is_capability_denied: () => false, dispatch_units: () => 1,
  }
}

/** The scenario's successor, compiled through the shared path, plus the parent it came from. */
function scenarioSuccessor() {
  const { contract, entry, source } = scenarioFixture('platform_internal')
  let observed = contract
  for (const item of contract.plan_items.filter((candidate) => candidate.state === 'ready' && candidate.binding_id !== null)) {
    const payload = item.item_id === source.item_id
      ? { rows: [{ yoga: 'Raja', fired: true, bhanga_active: true }] }
      : { rows: [{ id: 'x' }] }
    observed = recordInquiryExecution(observed, {
      item_id: item.item_id, disposition: 'served', evidence_refs: [`raw:${item.item_id}`],
      pagination: { semantics: 'none', exhausted: true, next: null },
      evidence_frontier: deriveEvidenceFrontier({ contract: observed, item_id: item.item_id, evidence_payload: payload, snapshot: SCENARIO_SNAPSHOT }),
    })
  }
  const parent = closeInquiryForEvidenceSuccessor(observed)
  const successor = compileInquirySuccessorContract({
    snapshot: SCENARIO_SNAPSHOT, overlay: SCENARIO_OVERLAY, parent_inquiry_id: 'scenario-expectation', parent, cross_capability_only: true,
    admission: permissiveScenarioLive(parent),
  })
  return { successor, entry }
}

/** The compile-time receipt projection every door must produce for the scenario's admitted successor. */
export function expectedAdmitProjection() {
  const { successor, entry } = scenarioSuccessor()
  return projectDecision(successor.plan_items.find((item) => item.scu_id === entry.scu_id)!.successor_admission!)
}

/**
 * The DISPATCH-time receipt projection: the successor's ready items dispatched in plan order, each
 * charging the shared cost ledger as it goes (so the k-th item sees the k-1 charges before it). Every
 * door dispatches in plan order, so every door must stamp exactly these fields.
 */
export function expectedDispatchProjection() {
  const { successor, entry } = scenarioSuccessor()
  let current = successor
  let projected: ReturnType<typeof projectDecision> | null = null
  for (const item of successor.plan_items.filter((candidate) => candidate.state === 'ready' && candidate.binding_id !== null)) {
    const decision = evaluateSuccessorItemForDispatch({
      contract: current, item_id: item.item_id, snapshot: SCENARIO_SNAPSHOT, live: permissiveScenarioLive(current),
    })!
    current = recordInquiryExecution(current, {
      item_id: item.item_id, disposition: 'served', evidence_refs: [`raw:dispatch:${item.item_id}`],
      pagination: { semantics: 'none', exhausted: true, next: null }, successor_dispatch: decision,
    })
    if (item.scu_id === entry.scu_id) projected = projectDecision(decision)
  }
  return projected!
}

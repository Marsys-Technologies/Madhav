/**
 * One shared successor-envelope scenario for the door tests (Portal, managed MCP, raw MCP), so
 * "identical decisions and receipt fields on every door" is asserted against ONE expectation
 * instead of three independently written ones. Test-only.
 */
import generatedSnapshot from '../../../../generated/capability_knowledge.snapshot.json'
import type { CapabilityKnowledgeSnapshot, ChartCapabilityOverlay, ExecutionChannel } from '../../../retrieval/registry/knowledge/types'
import { compileInquiryContract } from '../compiler'
import { evaluateSuccessorAdmission, type SuccessorAdmissionDecision } from '../authorization_envelope'
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
    limit_state: decision.limit_state,
  }
}

/**
 * The receipt projection every door must produce for the scenario's admitted successor, derived
 * once from the shared evaluator over the scenario's root contract after every executable item was
 * served (the parent's iteration is the number of executable items, on every door).
 */
export function expectedAdmitProjection() {
  const { contract, entry, source } = scenarioFixture('platform_internal')
  const executed = contract.plan_items.filter((item) => item.binding_id !== null).length
  const decision = evaluateSuccessorAdmission({
    envelope: contract.authorization_envelope,
    snapshot: SCENARIO_SNAPSHOT,
    candidate: {
      scu_id: entry.scu_id, binding_id: entry.binding_id, frontier_id: 'frontier-001',
      frontier_rule_id: entry.admitting_rule_ids[0]!, source_item_id: source.item_id, source_scu_id: source.scu_id, source_served: true,
    },
    contract: { ...contract, iteration: executed },
    live: {
      transport: 'portal', chart_id: contract.chart_id, principal_subject: 'p', owner_principal_subject: 'p', chart_access_verified: true,
      overlay_version: contract.chart_availability_version, build_id: contract.chart_build_id,
      describe: (uri) => ({ uri, mutation: false, calibration_context_only: false }), tool_exists: () => true,
      is_capability_denied: () => false, cost_exhausted: false,
    },
  })
  return projectDecision(decision)
}

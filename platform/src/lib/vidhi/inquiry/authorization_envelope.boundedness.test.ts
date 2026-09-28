/**
 * Packet B boundedness, driven through the REAL compiler across whole successor lineages: however
 * much evidence keeps proposing more capabilities, the lineage can never widen past the plan-time
 * envelope, never re-admit a capability it already used, and never exceed its depth ceiling.
 */
import { describe, expect, it } from 'vitest'
import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import {
  MAX_SUCCESSOR_DEPTH,
  type SuccessorAdmissionLiveContext,
} from './authorization_envelope'
import {
  closeInquiryForEvidenceSuccessor,
  compileInquirySuccessorContract,
  recordInquiryExecution,
} from './compiler'
import { deriveEvidenceFrontier } from './evidence_frontier'
import { SCENARIO_OVERLAY, SCENARIO_SNAPSHOT, compileScenarioRoot } from './__fixtures__/successor_envelope_scenario'
import type { InquiryContract } from './types'

/** Evidence that fires EVERY frontier rule at once: the most any payload can ask for. */
const MAXIMAL_EVIDENCE = {
  rows: [{
    bhanga_active: true, dignity_state: 'debilitated', activation_dasha_periods: ['p'],
    mechanism_class: 'm', houses: [7],
  }],
}

function live(contract: InquiryContract): SuccessorAdmissionLiveContext {
  return {
    transport: 'portal', chart_id: contract.chart_id, principal_subject: 'p', owner_principal_subject: 'p',
    chart_access_verified: true, overlay_version: contract.chart_availability_version, build_id: contract.chart_build_id,
    describe: (uri) => ({ uri, mutation: false, calibration_context_only: false, mcp_annotations: { readOnly: true } }),
    tool_exists: () => true, is_capability_denied: () => false, cost_exhausted: false,
  }
}

/**
 * Execute every ready item the way a door does: an admitted item is served with maximal evidence; a
 * refused successor item is recorded as a terminal failed observation and never contributes evidence.
 */
function serveAll(contract: InquiryContract): InquiryContract {
  let current = contract
  for (const item of current.plan_items.filter((candidate) => candidate.state === 'ready')) {
    if (item.successor_admission?.decision === 'refuse') {
      current = recordInquiryExecution(current, {
        item_id: item.item_id, disposition: 'failed', evidence_refs: [], gap_reason: item.successor_admission.code,
        pagination: { semantics: 'none', exhausted: true, next: null }, successor_dispatch: item.successor_admission,
      })
      current = { ...current, plan_items: current.plan_items.map((candidate) => candidate.item_id === item.item_id ? { ...candidate, state: 'observed' as const } : candidate) }
      continue
    }
    current = recordInquiryExecution(current, {
      item_id: item.item_id, disposition: 'served', evidence_refs: [`raw:${stableFingerprint({ item: item.item_id, at: current.iteration })}`],
      pagination: { semantics: 'none', exhausted: true, next: null },
      evidence_frontier: deriveEvidenceFrontier({ contract: current, item_id: item.item_id, evidence_payload: MAXIMAL_EVIDENCE, snapshot: SCENARIO_SNAPSHOT }),
    })
  }
  return closeInquiryForEvidenceSuccessor(current)
}

describe('successor lineage is bounded by the plan-time envelope', () => {
  it('under maximal evidence at every generation, admits each capability at most once and only from the root envelope', () => {
    const root = compileScenarioRoot('platform_internal')
    const rootEntries = new Set(root.authorization_envelope!.entries.map((entry) => entry.scu_id))
    expect(rootEntries.size).toBeGreaterThan(0)

    const admittedScus: string[] = []
    const refusalCodes: string[] = []
    let contract = root
    let generations = 0
    for (; generations < MAX_SUCCESSOR_DEPTH + 3; generations += 1) {
      let parent: InquiryContract
      try { parent = serveAll(contract) } catch { break }
      let successor: InquiryContract
      try {
        successor = compileInquirySuccessorContract({
          snapshot: SCENARIO_SNAPSHOT, overlay: SCENARIO_OVERLAY, parent_inquiry_id: `lineage-${generations}`, parent,
          cross_capability_only: true, admission: live(parent),
        })
      } catch { break }
      for (const item of successor.plan_items) {
        const decision = item.successor_admission!
        if (decision.decision === 'admit') admittedScus.push(decision.scu_id)
        else refusalCodes.push(decision.code)
      }
      // The successor's envelope only ever shrinks.
      const before = new Set((contract.authorization_envelope?.entries ?? []).map((entry) => entry.scu_id))
      for (const entry of successor.authorization_envelope!.entries) expect(before.has(entry.scu_id)).toBe(true)
      contract = successor
    }

    expect(admittedScus.length).toBeGreaterThan(0)
    // Never widens past the root envelope...
    for (const scuId of admittedScus) expect(rootEntries.has(scuId)).toBe(true)
    // ...never re-admits a capability the lineage already used...
    expect(new Set(admittedScus).size).toBe(admittedScus.length)
    // ...is bounded by the number of distinct capabilities the envelope holds (not by evidence volume)...
    expect(admittedScus.length).toBeLessThanOrEqual(rootEntries.size)
    // ...and terminates well inside the depth ceiling.
    expect(generations).toBeLessThanOrEqual(MAX_SUCCESSOR_DEPTH)
    // Whatever maximal evidence proposed beyond the envelope was refused by name, never silently dropped.
    for (const code of refusalCodes) expect(code).toBe('successor_capability_not_authorized_for_request')
  })

  it('a lineage already at its depth ceiling refuses even an in-envelope capability', () => {
    const root = compileScenarioRoot('platform_internal')
    let contract: InquiryContract = root
    // Wrap the root in MAX_SUCCESSOR_DEPTH synthetic ancestors: depth is read from the chain itself.
    for (let level = 0; level < MAX_SUCCESSOR_DEPTH; level += 1) {
      contract = { ...root, successor: { parent_contract: contract, admitted_frontier: [], admission_decisions: [] } } as unknown as InquiryContract
    }
    const parent = serveAll({ ...contract, authorization_envelope: root.authorization_envelope })
    const successor = compileInquirySuccessorContract({
      snapshot: SCENARIO_SNAPSHOT, overlay: SCENARIO_OVERLAY, parent_inquiry_id: 'deep', parent, cross_capability_only: true, admission: live(parent),
    })
    expect(successor.plan_items.every((item) => item.successor_admission?.decision === 'refuse')).toBe(true)
    expect(successor.plan_items.map((item) => item.successor_admission?.code)).toContain('successor_depth_exceeded')
  })

  it('an exhausted cost cap refuses every item of an otherwise admissible successor', () => {
    const root = compileScenarioRoot('platform_internal')
    const parent = serveAll(root)
    const successor = compileInquirySuccessorContract({
      snapshot: SCENARIO_SNAPSHOT, overlay: SCENARIO_OVERLAY, parent_inquiry_id: 'capped', parent, cross_capability_only: true,
      admission: { ...live(parent), cost_exhausted: true },
    })
    expect(successor.plan_items.length).toBeGreaterThan(0)
    expect(successor.plan_items.every((item) => item.successor_admission?.code === 'successor_cost_limit_exceeded')).toBe(true)
  })
})

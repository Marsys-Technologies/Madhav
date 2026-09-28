/**
 * Remediation of the two MEDIUM findings from the first review round, against the REAL compiler:
 *  1. successor entitlement is SERVER-authoritative (derived from the door's verified chart
 *     permission); the scope tuple, the planner, stored state and the client can only narrow it.
 *  2. successor cost is one shared, deterministic, hash-chained model (registry dispatch units), not a
 *     constant `cost_exhausted: false`.
 */
import { describe, expect, it } from 'vitest'
import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import {
  MAX_SUCCESSOR_DISPATCH_UNITS,
  SUCCESSOR_COST_UNIT,
  appendSuccessorCharge,
  authorizationEnvelopeHash,
  effectiveEntitlementForPermission,
  evaluateSuccessorAdmission,
  evaluateSuccessorItemForDispatch,
  lineageConsumedUnits,
  refuseAdmittedSuccessor,
  verifySuccessorCostLedger,
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
import { SCENARIO_OVERLAY, SCENARIO_SNAPSHOT as snapshot, SCENARIO_SCOPE, compileScenarioRoot, scenarioFixture } from './__fixtures__/successor_envelope_scenario'
import type { InquiryContract } from './types'

const PRINCIPAL = 'principal-secret-uid-1234'

function live(contract: InquiryContract, overrides: Partial<SuccessorAdmissionLiveContext> = {}): SuccessorAdmissionLiveContext {
  return {
    transport: 'portal', chart_id: contract.chart_id, principal_subject: PRINCIPAL, owner_principal_subject: PRINCIPAL,
    chart_permission: 'all', overlay_version: contract.chart_availability_version, build_id: contract.chart_build_id,
    describe: (uri) => ({ uri, mutation: false, calibration_context_only: false }), tool_exists: () => true,
    is_capability_denied: () => false, dispatch_units: () => 1, ...overrides,
  }
}

function compileWith(permission: 'all' | 'view' | 'deny' | null, scopeEntitlement = 'native'): InquiryContract {
  return compileInquiryContract({
    snapshot, overlay: SCENARIO_OVERLAY, chart_id: '1c826d5a-41cb-4450-b4dc-59d440e5f75a', question: 'What is my current dasha?',
    scope_tuple: { ...SCENARIO_SCOPE, entitlement: scopeEntitlement } as never, execution_channel: 'platform_internal',
    temporal_anchor_date: new Date().toISOString().slice(0, 10), temporal_anchor_source: 'request_context_clock',
    ...(permission === undefined ? {} : { server_authorization: { chart_permission: permission } }),
  })
}

/** Serve the plan so the parent closes with an evidence-admitted frontier, then compile the successor. */
function successorOf(root: InquiryContract, liveOverride: Partial<SuccessorAdmissionLiveContext> = {}) {
  const sourceItem = root.plan_items.find((item) => item.state === 'ready' && item.binding_id
    && root.obligations.some((o) => item.obligation_ids.includes(o.obligation_id) && o.materiality === 'required'))!
  let observed = root
  for (const item of root.plan_items.filter((candidate) => candidate.state === 'ready' && candidate.binding_id !== null)) {
    const payload = item.item_id === sourceItem.item_id ? { rows: [{ bhanga_active: true }] } : { rows: [{ id: 'x' }] }
    observed = recordInquiryExecution(observed, {
      item_id: item.item_id, disposition: 'served', evidence_refs: [`raw:${item.item_id}`], pagination: { semantics: 'none', exhausted: true, next: null },
      evidence_frontier: deriveEvidenceFrontier({ contract: observed, item_id: item.item_id, evidence_payload: payload, snapshot }),
    })
  }
  const parent = closeInquiryForEvidenceSuccessor(observed)
  return { parent, successor: compileInquirySuccessorContract({ snapshot, overlay: SCENARIO_OVERLAY, parent_inquiry_id: 'p', parent, cross_capability_only: true, admission: live(parent, liveOverride) }) }
}

describe('Stage 1 — entitlement is server-authoritative', () => {
  it('maps the door\'s verified permission to an effective tier, and everything else to nothing', () => {
    expect(effectiveEntitlementForPermission('all')).toEqual({ tier: 'native', source: 'chart_permission_all' })
    expect(effectiveEntitlementForPermission('view')).toEqual({ tier: 'public_disclosed', source: 'chart_permission_view' })
    for (const unverified of ['deny', null, undefined, 'owner', 'ALL'] as const) {
      expect(effectiveEntitlementForPermission(unverified as never), String(unverified)).toEqual({ tier: 'none', source: 'chart_permission_unverified' })
    }
  })

  it('a caller-declared native scope cannot self-upgrade a view-only or unverified permission (empty envelope)', () => {
    expect(compileWith('all').authorization_envelope!.entries.length).toBeGreaterThan(0)
    for (const permission of ['view', 'deny', null] as const) {
      const envelope = compileWith(permission, 'native').authorization_envelope!
      expect(envelope.scope_entitlement).toBe('native')
      expect(envelope.entries, String(permission)).toEqual([])
    }
    // Omitting the server authorization entirely is "unverified", not "native".
    expect(compileWith(undefined as never).authorization_envelope!.entries).toEqual([])
  })

  it('the scope tuple can only NARROW a full permission, never grant', () => {
    for (const scopeTier of ['public_disclosed', 'restricted', 'reference', 'bogus_tier']) {
      expect(compileWith('all', scopeTier).authorization_envelope!.entries, scopeTier).toEqual([])
    }
  })

  it('records the effective entitlement and its source in the envelope, and binds both into the authorization hash', () => {
    const contract = compileWith('all')
    expect(contract.authorization_envelope!.effective_entitlement).toEqual({ tier: 'native', source: 'chart_permission_all' })
    const widened = { ...contract, authorization_envelope: { ...contract.authorization_envelope!, effective_entitlement: { tier: 'native', source: 'chart_permission_view' } } } as InquiryContract
    expect(authorizationEnvelopeHash(widened.authorization_envelope!)).not.toBe(contract.authorization_envelope!.envelope_hash)
    expect(inquiryAuthorizationHashes(widened).execution_plan_hash).not.toBe(contract.execution_plan_hash)
  })

  describe('dispatch-time revalidation (nothing stored can widen the live server grant)', () => {
    const base = scenarioFixture('platform_internal')
    const rule = base.entry.admitting_rule_ids[0]!
    const candidate = { scu_id: base.entry.scu_id, binding_id: base.entry.binding_id, frontier_id: 'f', frontier_rule_id: rule, source_item_id: base.source.item_id, source_scu_id: base.source.scu_id, source_served: true }
    const run = (permission: SuccessorAdmissionLiveContext['chart_permission'], contract: InquiryContract = base.contract, envelope = base.contract.authorization_envelope) =>
      evaluateSuccessorAdmission({ envelope, snapshot, candidate, contract, live: live(contract, { chart_permission: permission }) })

    it('full verified permission admits the otherwise eligible successor', () => {
      expect(run('all')).toMatchObject({ decision: 'admit', entitlement: { tier: 'native', source: 'chart_permission_all' } })
    })

    it('view-only, denied, unknown or missing permission refuses (view by tier; the rest by access)', () => {
      expect(run('view')).toMatchObject({ decision: 'refuse', code: 'successor_entitlement_not_permitted', entitlement: { tier: 'public_disclosed', source: 'chart_permission_view' } })
      for (const permission of ['deny', null] as const) {
        expect(run(permission), String(permission)).toMatchObject({ decision: 'refuse', code: 'successor_chart_access_not_verified', entitlement: { tier: 'none' } })
      }
      expect(run('root' as never)).toMatchObject({ decision: 'refuse', code: 'successor_chart_access_not_verified' })
    })

    it('a stored envelope recording native cannot widen a live view-only grant, even when re-sealed', () => {
      const stored = { ...base.contract.authorization_envelope!, effective_entitlement: { tier: 'native' as const, source: 'chart_permission_all' as const } }
      const resealed = { ...stored, envelope_hash: authorizationEnvelopeHash(stored) }
      expect(run('view', base.contract, resealed)).toMatchObject({ code: 'successor_entitlement_not_permitted' })
    })

    it('tampering the serialized scope tuple cannot raise the tier above the live grant', () => {
      const widenedScope = { ...base.contract, scope_tuple: { ...base.contract.scope_tuple, entitlement: 'native' } }
      expect(run('view', widenedScope as InquiryContract)).toMatchObject({ code: 'successor_entitlement_not_permitted' })
    })

    it('an envelope edited without re-sealing authorizes nothing', () => {
      const edited = { ...base.contract.authorization_envelope!, effective_entitlement: { tier: 'native' as const, source: 'chart_permission_view' as const } }
      expect(run('all', base.contract, edited)).toMatchObject({ code: 'successor_capability_not_authorized_for_request' })
    })

    it('a successor compiled under a view-only grant admits nothing, on every generation', () => {
      const { successor } = successorOf(compileWith('view'))
      expect(successor.plan_items.map((item) => item.successor_admission?.code)).toEqual(
        successor.plan_items.map(() => 'successor_capability_not_authorized_for_request'),
      )
    })

    it('exposes the authoritative source without leaking identity', () => {
      const decision = run('all')
      const serialized = JSON.stringify(decision) + JSON.stringify(compileWith('all').authorization_envelope)
      expect(serialized).not.toContain(PRINCIPAL)
      expect(decision.entitlement.source).toBe('chart_permission_all')
      expect(verifySuccessorDecision(decision)).toBe(true)
    })
  })
})

describe('Stage 2 — one shared, deterministic successor cost model', () => {
  it('starts every lineage at the specified ceiling with nothing consumed, and says so in the receipt', () => {
    const { successor } = successorOf(compileWith('all'))
    const decision = successor.plan_items.find((item) => item.successor_admission?.decision === 'admit')!.successor_admission!
    expect(decision.limit_state).toMatchObject({
      cost_unit: SUCCESSOR_COST_UNIT, budget_units: MAX_SUCCESSOR_DISPATCH_UNITS, consumed_units: 0, candidate_units: 1, remaining_units: MAX_SUCCESSOR_DISPATCH_UNITS,
    })
    expect(successor.authorization_envelope!.limits.max_successor_dispatch_units).toBe(MAX_SUCCESSOR_DISPATCH_UNITS)
  })

  it('charges an admitted dispatch exactly once, in the same transition as its observation, and nothing for a refusal', () => {
    const { successor } = successorOf(compileWith('all'))
    const item = successor.plan_items.find((candidate) => candidate.successor_admission?.decision === 'admit')!
    const decision = evaluateSuccessorItemForDispatch({ contract: successor, item_id: item.item_id, snapshot, live: live(successor, { dispatch_units: () => 3 }) })!
    expect(decision.limit_state.candidate_units).toBe(3)
    const charged = recordInquiryExecution(successor, {
      item_id: item.item_id, disposition: 'served', evidence_refs: ['raw:x'], pagination: { semantics: 'none', exhausted: true, next: null }, successor_dispatch: decision,
    })
    expect(charged.successor_cost_ledger).toMatchObject({ consumed_units: 3, unit: SUCCESSOR_COST_UNIT })
    expect(charged.successor_cost_ledger!.entries).toHaveLength(1)
    expect(verifySuccessorCostLedger(charged.successor_cost_ledger!)).toBe(true)

    const refusal = refuseAdmittedSuccessor(decision, 'successor_arguments_not_authorized')
    const free = recordInquiryExecution(successor, {
      item_id: item.item_id, disposition: 'failed', evidence_refs: [], pagination: { semantics: 'none', exhausted: true, next: null }, successor_dispatch: refusal,
    })
    expect(free.successor_cost_ledger).toBeUndefined()
  })

  it('a failed dispatch attempt that reached the tool is still charged; each pagination page is charged again', () => {
    const { successor } = successorOf(compileWith('all'))
    const item = successor.plan_items.find((candidate) => candidate.successor_admission?.decision === 'admit')!
    let current = successor
    for (const disposition of ['served', 'failed', 'served'] as const) {
      const decision = evaluateSuccessorItemForDispatch({ contract: current, item_id: item.item_id, snapshot, live: live(current) })!
      expect(decision.decision).toBe('admit')
      current = recordInquiryExecution(current, {
        item_id: item.item_id, disposition, evidence_refs: ['raw:x'], pagination: { semantics: 'offset', exhausted: false, next: 50 }, request_position_path: 'offset', successor_dispatch: decision,
      })
    }
    expect(current.successor_cost_ledger!.consumed_units).toBe(3)
    expect(current.successor_cost_ledger!.entries.map((entry) => entry.seq)).toEqual([1, 2, 3])
  })

  it('refuses at the exact boundary with successor_cost_limit_exceeded', () => {
    const { successor } = successorOf(compileWith('all'))
    const item = successor.plan_items.find((candidate) => candidate.successor_admission?.decision === 'admit')!
    const withConsumed = (units: number): InquiryContract => {
      let ledger = undefined as ReturnType<typeof appendSuccessorCharge> | undefined
      for (let index = 0; index < units; index += 1) ledger = appendSuccessorCharge(ledger, { item_id: 'i', scu_id: 's', units: 1, decision_hash: `h${index}` })
      return { ...successor, successor_cost_ledger: ledger }
    }
    const at = (consumed: number, price: number) => evaluateSuccessorItemForDispatch({
      contract: withConsumed(consumed), item_id: item.item_id, snapshot, live: live(successor, { dispatch_units: () => price }),
    })!
    expect(at(MAX_SUCCESSOR_DISPATCH_UNITS - 3, 3)).toMatchObject({ decision: 'admit', limit_state: { remaining_units: 3, candidate_units: 3 } })
    expect(at(MAX_SUCCESSOR_DISPATCH_UNITS - 2, 3)).toMatchObject({ decision: 'refuse', code: 'successor_cost_limit_exceeded', limit_state: { remaining_units: 2, candidate_units: 3 } })
    expect(at(MAX_SUCCESSOR_DISPATCH_UNITS, 1)).toMatchObject({ decision: 'refuse', code: 'successor_cost_limit_exceeded', limit_state: { remaining_units: 0 } })
  })

  it('an unpriced capability is not free: a non-positive or non-integer price refuses', () => {
    const { parent } = successorOf(compileWith('all'))
    const base = scenarioFixture('platform_internal')
    for (const price of [0, -1, 1.5, Number.NaN]) {
      const decision = evaluateSuccessorAdmission({
        envelope: base.contract.authorization_envelope, snapshot,
        candidate: { scu_id: base.entry.scu_id, binding_id: base.entry.binding_id, frontier_id: 'f', frontier_rule_id: base.entry.admitting_rule_ids[0]!, source_item_id: base.source.item_id, source_scu_id: base.source.scu_id, source_served: true },
        contract: base.contract, live: live(parent, { dispatch_units: () => price }),
      })
      expect(decision, String(price)).toMatchObject({ code: 'successor_cost_limit_exceeded' })
    }
  })

  it('stored budget and ledger tampering cannot widen the ceiling', () => {
    const { successor } = successorOf(compileWith('all'))
    const item = successor.plan_items.find((candidate) => candidate.successor_admission?.decision === 'admit')!
    let ledger = appendSuccessorCharge(undefined, { item_id: item.item_id, scu_id: item.scu_id, units: MAX_SUCCESSOR_DISPATCH_UNITS, decision_hash: 'h' })
    const dispatch = (contract: InquiryContract) => evaluateSuccessorItemForDispatch({ contract, item_id: item.item_id, snapshot, live: live(contract) })!
    expect(dispatch({ ...successor, successor_cost_ledger: ledger })).toMatchObject({ code: 'successor_cost_limit_exceeded' })
    // Lowering the recorded total, editing an entry, or dropping an entry breaks verification -> exhausted.
    const lowered = { ...ledger, consumed_units: 0 }
    const edited = { ...ledger, entries: ledger.entries.map((entry) => ({ ...entry, units: 1 })) }
    const dropped = { ...ledger, entries: [], consumed_units: 0 }
    for (const forged of [lowered, edited, dropped]) {
      expect(verifySuccessorCostLedger(forged)).toBe(false)
      expect(dispatch({ ...successor, successor_cost_ledger: forged }), 'forged ledger').toMatchObject({ code: 'successor_cost_limit_exceeded' })
    }
    // An inflated ceiling in a re-sealed stored envelope is clamped to the platform constant.
    const parent = successor.successor!.parent_contract
    const inflated = { ...parent.authorization_envelope!, limits: { ...parent.authorization_envelope!.limits, max_successor_dispatch_units: 10_000 } }
    const inflatedParent = { ...parent, authorization_envelope: { ...inflated, envelope_hash: authorizationEnvelopeHash(inflated) } }
    const widened = { ...successor, successor_cost_ledger: ledger, successor: { ...successor.successor!, parent_contract: inflatedParent } } as InquiryContract
    expect(dispatch(widened)).toMatchObject({ code: 'successor_cost_limit_exceeded', limit_state: { budget_units: MAX_SUCCESSOR_DISPATCH_UNITS } })
    ledger = appendSuccessorCharge(undefined, { item_id: 'x', scu_id: 'x', units: 1, decision_hash: 'x' })
    expect(verifySuccessorCostLedger(ledger)).toBe(true)
  })

  it('a lineage cannot reset its budget by creating another successor', () => {
    const { successor: first } = successorOf(compileWith('all'))
    const item = first.plan_items.find((candidate) => candidate.successor_admission?.decision === 'admit')!
    const charged: InquiryContract = {
      ...first, successor_cost_ledger: appendSuccessorCharge(undefined, { item_id: item.item_id, scu_id: item.scu_id, units: 5, decision_hash: 'h' }),
    }
    expect(lineageConsumedUnits(charged)).toBe(5)
    // The grandchild embeds `charged` as its parent, so its lineage starts at 5 — not at 0.
    const grand = { ...compileScenarioRoot('platform_internal'), successor: { parent_contract: charged, admitted_frontier: [], admission_decisions: [] } } as unknown as InquiryContract
    expect(lineageConsumedUnits(grand)).toBe(5)
    // Rewriting the embedded parent's ledger to zero fails verification -> the budget reads as exhausted.
    const forgedParent = { ...charged, successor_cost_ledger: { ...charged.successor_cost_ledger!, consumed_units: 0 } }
    expect(lineageConsumedUnits({ ...grand, successor: { ...grand.successor!, parent_contract: forgedParent } } as InquiryContract)).toBeNull()
  })

  it('the request-level cost stop is refuse-only: it can add a refusal but never create an admission', () => {
    const base = scenarioFixture('platform_internal')
    const candidate = { scu_id: base.entry.scu_id, binding_id: base.entry.binding_id, frontier_id: 'f', frontier_rule_id: base.entry.admitting_rule_ids[0]!, source_item_id: base.source.item_id, source_scu_id: base.source.scu_id, source_served: true }
    const ask = (extra: Partial<SuccessorAdmissionLiveContext>) => evaluateSuccessorAdmission({ envelope: base.contract.authorization_envelope, snapshot, candidate, contract: base.contract, live: live(base.contract, extra) })
    expect(ask({})).toMatchObject({ decision: 'admit' })
    expect(ask({ cost_exhausted: false })).toMatchObject({ decision: 'admit' })
    expect(ask({ cost_exhausted: true })).toMatchObject({ code: 'successor_cost_limit_exceeded' })
    expect(stableFingerprint(ask({}).limit_state)).toBe(stableFingerprint(ask({ cost_exhausted: false }).limit_state))
  })
})

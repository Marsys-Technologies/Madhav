/**
 * Raw MCP door: successor authorization envelope (Packet B) against the REAL compiler, the REAL
 * lifecycle tokens and an in-memory store with the durable store's CAS/reservation semantics.
 *
 * The raw door hands evidence to a client, so its central obligation here is negative: nothing a
 * client sends is ever an envelope or an admission. Authority is recomputed from the server-held
 * contract row plus this request's own live state on every `continue` and every successor `execute`.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { InquiryContract } from '@/lib/vidhi/inquiry'
import {
  SCENARIO_CHART_ID,
  SCENARIO_OVERLAY,
  SCENARIO_QUESTION,
  SCENARIO_SCOPE,
  SCENARIO_SNAPSHOT,
  expectedAdmitProjection,
  expectedDispatchProjection,
  projectDecision,
  scenarioFixture,
} from '@/lib/vidhi/inquiry/__fixtures__/successor_envelope_scenario'

const state = vi.hoisted(() => ({
  dispatched: [] as string[],
  triggerUri: '',
  deniedUri: '',
  permission: 'all' as 'all' | 'view' | 'deny',
  units: undefined as number | undefined,
  toolMissing: '',
  paginate: false,
  snapshot: null as unknown,
  overlay: null as unknown,
  toolResult: (() => { throw new Error('unbound') }) as (name: string, args: Record<string, unknown>) => Record<string, unknown>,
  store: null as null | import('@/lib/vidhi/inquiry/__fixtures__/in_memory_lifecycle_store').InMemoryLifecycleStore,
}))

vi.mock('@/lib/mcp/service_token', () => ({ validateMcpServiceRequest: async () => true }))
vi.mock('@/lib/mcp/auth', () => ({ resolveMcpPrincipalRole: vi.fn().mockResolvedValue('guest') }))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: async () => state.permission }))
vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
vi.mock('@/lib/retrieval/registry/catalog', () => ({ getCatalog: () => [] }))
vi.mock('@/lib/retrieval/registry', () => ({
  getCapability: (uri: string) => ({ uri, mutation: false, calibration_context_only: false, ...(state.units === undefined ? {} : { dispatch_units: state.units }) }),
}))
vi.mock('@/lib/retrieval/registry/knowledge', () => ({
  assertPinnedCapabilityKnowledgeCurrent: () => state.snapshot,
  loadChartCapabilityOverlay: async () => state.overlay,
}))
vi.mock('@/lib/pipeline/no_leakage_filter', () => ({
  filterLeakedCapabilities: (names: readonly string[]) => names.filter((name) => name !== state.deniedUri),
}))
vi.mock('@/lib/retrieval/registry/tool_name_bridge', () => ({
  TOOL_NAME_TO_URI: {},
  resolveToolUri: (name: string) => (name.startsWith('marsys://') ? name : undefined),
  getToolByName: (name: string) => name === state.toolMissing ? undefined : ({
    retrieve: async (_query: unknown, args: Record<string, unknown>) => {
      state.dispatched.push(name)
      const base = state.toolResult(name, state.paginate ? args : { ...args, offset: 1 })
      if (name !== state.triggerUri) return base
      return { ...base, results: [{ content: JSON.stringify({ rows: [{ yoga: 'Raja', fired: true, bhanga_active: true }], more_available: false }) }] }
    },
  }),
}))
vi.mock('@/lib/vidhi/inquiry/lifecycle_store', async () => {
  const { createInMemoryLifecycleStore } = await import('@/lib/vidhi/inquiry/__fixtures__/in_memory_lifecycle_store')
  const store = createInMemoryLifecycleStore()
  state.store = store
  return {
    createInquiryLifecycle: store.createInquiryLifecycle,
    getInquiryLifecycle: store.getInquiryLifecycle,
    createInquirySuccessorLifecycle: store.createInquirySuccessorLifecycle,
    reserveInquiryAction: store.reserveInquiryAction,
    markInquiryActionDispatched: store.markInquiryActionDispatched,
    commitInquiryObservation: store.commitInquiryObservation,
    commitInquiryFinalization: store.commitInquiryFinalization,
    failCloseAmbiguousInquiryAction: store.failCloseAmbiguousInquiryAction,
  }
})

import { POST } from '../route'
import { verifySuccessorCostLedger } from '@/lib/vidhi/inquiry/authorization_envelope'
import { w5DoorParityToolResult } from '@/lib/vidhi/inquiry/__fixtures__/door_parity'

state.toolResult = w5DoorParityToolResult
state.snapshot = SCENARIO_SNAPSHOT
state.overlay = SCENARIO_OVERLAY

interface Step { ok: boolean; error?: string; inquiry_id: string; lifecycle_token: string; next_action_ids: string[]; contract: InquiryContract; disposition?: string }

function request(body: object): Request {
  return new Request('http://localhost/api/mcp/inquiry', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-mcp-user': 'user-1', 'x-mcp-key-id': 'key-1' },
    body: JSON.stringify(body),
  })
}

async function call(body: object): Promise<{ status: number; body: Step }> {
  const response = await POST(request(body))
  return { status: response.status, body: await response.json() as Step }
}

/** Start a real inquiry on the raw door and execute every ready item. */
async function runToFinalize(sourceUri: string): Promise<Step> {
  state.triggerUri = sourceUri
  const start = await call({ action: 'start', chart_id: SCENARIO_CHART_ID, question: SCENARIO_QUESTION, scope_tuple: SCENARIO_SCOPE, temporal_anchor_date: new Date().toISOString().slice(0, 10) })
  expect(start.status).toBe(200)
  let step = start.body
  while (step.next_action_ids.length > 0) {
    const executed = await call({ action: 'execute', lifecycle_token: step.lifecycle_token, action_id: step.next_action_ids[0] })
    expect(executed.status).toBe(200)
    step = executed.body
  }
  return step
}

beforeEach(() => {
  vi.clearAllMocks()
  state.dispatched = []
  state.triggerUri = ''
  state.deniedUri = ''
  state.paginate = false
  state.permission = 'all'
  state.units = undefined
  state.toolMissing = ''
  state.snapshot = SCENARIO_SNAPSHOT
  state.overlay = SCENARIO_OVERLAY
  state.store!.rows.clear()
  state.store!.reservations.clear()
  state.store!.evidence.length = 0
  process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = 'inquiry-v1'
  process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = Buffer.alloc(32, 7).toString('base64url')
})

describe('raw MCP: successor envelope (real compiler, real tokens)', () => {
  it('admits, receipts and dispatches an envelope-admitted successor on `continue` + `execute`', async () => {
    const { sourceUri, targetUri, entry } = scenarioFixture('mcp_full')
    const finalizeStep = await runToFinalize(sourceUri)
    const continued = await call({ action: 'continue', lifecycle_token: finalizeStep.lifecycle_token })
    expect(continued.status).toBe(200)
    const successor = continued.body.contract
    const item = successor.plan_items.find((candidate) => candidate.scu_id === entry.scu_id)!
    expect(item.successor_admission).toMatchObject({ decision: 'admit', code: 'successor_admitted' })
    expect(continued.body.next_action_ids).toContain(item.item_id)

    const executed = await call({ action: 'execute', lifecycle_token: continued.body.lifecycle_token, action_id: item.item_id })
    expect(executed.status).toBe(200)
    expect(state.dispatched).toContain(targetUri)
    const done = executed.body.contract.plan_items.find((candidate) => candidate.item_id === item.item_id)!
    expect(done.successor_dispatch).toMatchObject({ decision: 'admit', code: 'successor_admitted', scu_id: entry.scu_id })
    const receipt = state.store!.evidence.find((candidate) => candidate.inquiry_id === executed.body.inquiry_id && candidate.plan_item_id === item.item_id)!
    expect((receipt.evidence_jsonb as { admission?: { decision: string } }).admission).toMatchObject({ decision: 'admit' })
  })

  it('records a named terminal refusal (never a dispatch) when the live state refuses the item', async () => {
    const { sourceUri, targetUri, entry } = scenarioFixture('mcp_full')
    const finalizeStep = await runToFinalize(sourceUri)
    state.deniedUri = targetUri
    const continued = await call({ action: 'continue', lifecycle_token: finalizeStep.lifecycle_token })
    const item = continued.body.contract.plan_items.find((candidate) => candidate.scu_id === entry.scu_id)!
    expect(item.successor_admission).toMatchObject({ decision: 'refuse', code: 'successor_safety_excluded' })

    const before = state.dispatched.length
    const executed = await call({ action: 'execute', lifecycle_token: continued.body.lifecycle_token, action_id: item.item_id })
    expect(executed.status).toBe(200)
    expect(state.dispatched.length).toBe(before)
    expect(executed.body.disposition).toBe('failed')
    const done = executed.body.contract.plan_items.find((candidate) => candidate.item_id === item.item_id)!
    expect(done.state).toBe('observed')
    expect(done.observation).toMatchObject({ disposition: 'failed', gap_reason: 'successor_safety_excluded' })
    expect(done.successor_dispatch).toMatchObject({ decision: 'refuse', code: 'successor_safety_excluded' })
    // Terminal: nothing left ready, so the lifecycle can be finalized rather than stranded.
    expect(executed.body.next_action_ids).not.toContain(item.item_id)
  })

  it('never trusts a client-supplied envelope, admission or contract: the request schema has no place for them', async () => {
    const { sourceUri, entry } = scenarioFixture('mcp_full')
    const finalizeStep = await runToFinalize(sourceUri)
    const continued = await call({ action: 'continue', lifecycle_token: finalizeStep.lifecycle_token })
    const item = continued.body.contract.plan_items.find((candidate) => candidate.scu_id === entry.scu_id)!
    const forged = { ...item.successor_admission!, decision: 'admit', code: 'successor_admitted' }
    for (const extra of [
      { authorization_envelope: continued.body.contract.authorization_envelope },
      { successor_admission: forged },
      { admission: forged },
      { contract: continued.body.contract },
    ]) {
      const before = state.dispatched.length
      const executed = await call({ action: 'execute', lifecycle_token: continued.body.lifecycle_token, action_id: item.item_id, ...extra })
      expect(executed.status).toBe(400)
      expect(executed.body.error).toBe('INVALID_REQUEST')
      expect(state.dispatched.length).toBe(before)
    }
    const continueWithExtra = await call({ action: 'continue', lifecycle_token: finalizeStep.lifecycle_token, authorization_envelope: {} })
    expect(continueWithExtra.status).toBe(400)
  })

  it('a tampered server-held contract is stopped by the token state-hash gate before any dispatch', async () => {
    const { sourceUri, targetUri, entry } = scenarioFixture('mcp_full')
    const finalizeStep = await runToFinalize(sourceUri)
    const continued = await call({ action: 'continue', lifecycle_token: finalizeStep.lifecycle_token })
    const item = continued.body.contract.plan_items.find((candidate) => candidate.scu_id === entry.scu_id)!
    const row = state.store!.rows.get(continued.body.inquiry_id)!
    const parent = row.contract_jsonb.successor!.parent_contract
    const tampered = {
      ...row.contract_jsonb,
      successor: { ...row.contract_jsonb.successor!, parent_contract: { ...parent, authorization_envelope: { ...parent.authorization_envelope!, entries: [] } } },
    } as InquiryContract
    state.store!.rows.set(row.inquiry_id, { ...row, contract_jsonb: tampered })

    const before = state.dispatched.length
    const executed = await call({ action: 'execute', lifecycle_token: continued.body.lifecycle_token, action_id: item.item_id })
    // The token binds the exact contract state it was issued for, so an edited row never reaches the
    // evaluator (the managed door, which has no token, proves the evaluator layer on its own).
    expect(executed.status).toBe(409)
    expect(executed.body.error).toBe('INQUIRY_TOKEN_REPLAYED_OR_STALE')
    expect(state.dispatched.length).toBe(before)
    expect(state.dispatched).not.toContain(targetUri)
  })

  it('the receipt fields it produces match the shared scenario projection used by every door', async () => {
    const { sourceUri, entry } = scenarioFixture('mcp_full')
    const finalizeStep = await runToFinalize(sourceUri)
    const continued = await call({ action: 'continue', lifecycle_token: finalizeStep.lifecycle_token })
    const item = continued.body.contract.plan_items.find((candidate) => candidate.scu_id === entry.scu_id)!
    expect(item.successor_admission!.decision).toBe('admit')
    // The compile-time decision AND, after execution, the dispatch-time decision carry the same fields.
    expect(projectDecision(item.successor_admission!)).toEqual(expectedAdmitProjection())
    // Dispatch every ready item in plan order (as every door does), so the shared cost ledger has
    // charged exactly what the shared expectation charged before this item.
    let step2 = continued.body
    while (step2.next_action_ids.length > 0) {
      step2 = (await call({ action: 'execute', lifecycle_token: step2.lifecycle_token, action_id: step2.next_action_ids[0] })).body
    }
    const dispatched = step2.contract.plan_items.find((candidate) => candidate.item_id === item.item_id)!.successor_dispatch!
    expect(projectDecision(dispatched)).toEqual(expectedDispatchProjection())
  })
})

describe('raw MCP: a capped same-capability pagination frontier stays explicitly continuable', () => {
  it('`continue` admits the planned capability\'s next page on the parent-plan authority and `execute` dispatches it', async () => {
    const { W5_DOOR_PARITY_CHART_ID, W5_DOOR_PARITY_OVERLAY, W5_DOOR_PARITY_QUESTION, W5_DOOR_PARITY_SCOPE, W5_DOOR_PARITY_SNAPSHOT, w5DoorParityPlan } =
      await import('@/lib/vidhi/inquiry/__fixtures__/door_parity')
    const { managedPlanToAiInquiryProposal } = await import('@/lib/vidhi/inquiry/managed_bridge')
    const scus = W5_DOOR_PARITY_SNAPSHOT.scus.map((scu) => ({
      ...scu, bindings: scu.bindings.map((binding) => ({ ...binding, execution_channels: ['platform_internal'] as const })),
    }))
    const snapshot = { ...W5_DOOR_PARITY_SNAPSHOT, content_hash: 'sha256:raw-pagination-fixture', scus }
    state.snapshot = snapshot
    state.overlay = { ...W5_DOOR_PARITY_OVERLAY, catalog_content_hash: snapshot.content_hash, overlay_version: 'sha256:raw-pagination-overlay' }
    state.paginate = true

    const start = await call({
      action: 'start', chart_id: W5_DOOR_PARITY_CHART_ID, question: W5_DOOR_PARITY_QUESTION,
      scope_tuple: W5_DOOR_PARITY_SCOPE, ai_proposal: managedPlanToAiInquiryProposal(w5DoorParityPlan()),
    })
    expect(start.status).toBe(200)
    let step = start.body
    while (step.next_action_ids.length > 0) {
      step = (await call({ action: 'execute', lifecycle_token: step.lifecycle_token, action_id: step.next_action_ids[0] })).body
    }
    const continued = await call({ action: 'continue', lifecycle_token: step.lifecycle_token })
    expect(continued.status).toBe(200)
    const successor = continued.body.contract
    const pageItem = successor.plan_items.find((item) => item.successor_admission?.authority === 'parent_plan_continuation')!
    expect(pageItem, 'a same-capability frontier item must be admitted on the parent plan').toBeDefined()
    expect(pageItem.successor_admission).toMatchObject({ decision: 'admit', code: 'successor_admitted', envelope_entry_id: null })
    expect(continued.body.next_action_ids).toContain(pageItem.item_id)

    const before = state.dispatched.length
    const executed = await call({ action: 'execute', lifecycle_token: continued.body.lifecycle_token, action_id: pageItem.item_id })
    expect(executed.status).toBe(200)
    expect(state.dispatched.length).toBe(before + 1)
    const done = executed.body.contract.plan_items.find((item) => item.item_id === pageItem.item_id)!
    expect(done.successor_dispatch).toMatchObject({ decision: 'admit', code: 'successor_admitted' })
    expect(done.observation?.disposition).toBe('served')
  })
})

// ── Remediation: server-authoritative entitlement, shared cost model, terminal refusals ─────────────
const startBody = () => ({ action: 'start', chart_id: SCENARIO_CHART_ID, question: SCENARIO_QUESTION, scope_tuple: SCENARIO_SCOPE, temporal_anchor_date: new Date().toISOString().slice(0, 10) })
const targetItem = (contract: InquiryContract, scuId: string) => contract.plan_items.find((candidate) => candidate.scu_id === scuId)!
const contractOf = (inquiryId: string) => state.store!.rows.get(inquiryId)!.contract_jsonb

describe('raw MCP: entitlement is server-authoritative', () => {
  it('a caller that declares scope entitlement native cannot self-upgrade a view-only permission', async () => {
    const { sourceUri, targetUri, entry } = scenarioFixture('mcp_full')
    state.permission = 'view'
    const step = await runToFinalize(sourceUri)
    const contract = contractOf(step.inquiry_id)
    expect(contract.scope_tuple.entitlement).toBe('native') // what the caller declared...
    expect(contract.authorization_envelope!.entries).toEqual([]) // ...grants nothing
    expect(contract.authorization_envelope!.effective_entitlement).toEqual({ tier: 'public_disclosed', source: 'chart_permission_view' })

    const continued = await call({ action: 'continue', lifecycle_token: step.lifecycle_token })
    const item = targetItem(continued.body.contract, entry.scu_id)
    expect(item.successor_admission).toMatchObject({ decision: 'refuse', code: 'successor_capability_not_authorized_for_request' })
    const before = state.dispatched.length
    const executed = await call({ action: 'execute', lifecycle_token: continued.body.lifecycle_token, action_id: item.item_id })
    expect(executed.status).toBe(200)
    expect(state.dispatched.length).toBe(before)
    expect(state.dispatched).not.toContain(targetUri)
  })

  it('revalidates at dispatch: a grant that drops from full to view-only between continue and execute refuses', async () => {
    const { sourceUri, targetUri, entry } = scenarioFixture('mcp_full')
    const step = await runToFinalize(sourceUri)
    const continued = await call({ action: 'continue', lifecycle_token: step.lifecycle_token })
    const item = targetItem(continued.body.contract, entry.scu_id)
    expect(item.successor_admission).toMatchObject({ decision: 'admit', entitlement: { tier: 'native' } })
    state.permission = 'view'
    const before = state.dispatched.length
    const executed = await call({ action: 'execute', lifecycle_token: continued.body.lifecycle_token, action_id: item.item_id })
    expect(executed.status).toBe(200)
    expect(state.dispatched.length).toBe(before)
    expect(state.dispatched).not.toContain(targetUri)
    const done = executed.body.contract.plan_items.find((candidate) => candidate.item_id === item.item_id)!
    expect(done.successor_dispatch).toMatchObject({ decision: 'refuse', code: 'successor_entitlement_not_permitted', entitlement: { tier: 'public_disclosed', source: 'chart_permission_view' } })
    expect(done.state).toBe('observed')
  })
})

describe('raw MCP: the shared successor cost model', () => {
  it('a priced-out successor is refused with successor_cost_limit_exceeded at compile and never dispatched', async () => {
    const { sourceUri, targetUri, entry } = scenarioFixture('mcp_full')
    const step = await runToFinalize(sourceUri)
    state.units = 13 // above the 12-unit lineage ceiling
    const continued = await call({ action: 'continue', lifecycle_token: step.lifecycle_token })
    const item = targetItem(continued.body.contract, entry.scu_id)
    expect(item.successor_admission).toMatchObject({ decision: 'refuse', code: 'successor_cost_limit_exceeded', limit_state: { budget_units: 12, consumed_units: 0, candidate_units: 13 } })
    const before = state.dispatched.length
    const executed = await call({ action: 'execute', lifecycle_token: continued.body.lifecycle_token, action_id: item.item_id })
    expect(executed.status).toBe(200)
    expect(state.dispatched.length).toBe(before)
    expect(state.dispatched).not.toContain(targetUri)
    expect(contractOf(continued.body.inquiry_id).successor_cost_ledger).toBeUndefined()
  })

  it('charges each dispatched successor item exactly once, persisted in the durable row, and a replay cannot charge again', async () => {
    const { sourceUri } = scenarioFixture('mcp_full')
    state.units = 2
    const step = await runToFinalize(sourceUri)
    const continued = await call({ action: 'continue', lifecycle_token: step.lifecycle_token })
    const admitted = continued.body.contract.plan_items.filter((item) => item.successor_admission?.decision === 'admit')
    let cursor = continued.body
    const firstToken = cursor.lifecycle_token
    const firstAction = cursor.next_action_ids[0]!
    while (cursor.next_action_ids.length > 0) {
      cursor = (await call({ action: 'execute', lifecycle_token: cursor.lifecycle_token, action_id: cursor.next_action_ids[0] })).body
    }
    const ledger = contractOf(continued.body.inquiry_id).successor_cost_ledger!
    expect(admitted.length).toBeGreaterThan(0)
    expect(ledger.entries).toHaveLength(admitted.length)
    expect(ledger.consumed_units).toBe(admitted.length * 2)
    expect(verifySuccessorCostLedger(ledger)).toBe(true)
    // Replaying the first (already consumed) token dispatches nothing and charges nothing.
    const before = state.dispatched.length
    const replay = await call({ action: 'execute', lifecycle_token: firstToken, action_id: firstAction })
    expect(replay.status).toBe(409)
    expect(state.dispatched.length).toBe(before)
    expect(contractOf(continued.body.inquiry_id).successor_cost_ledger!.consumed_units).toBe(admitted.length * 2)
  })
})

describe('raw MCP: every successor refusal is terminal', () => {
  it('a live binding that vanished after admission is refused, terminal, and the lifecycle can still finalize', async () => {
    const { sourceUri, targetUri, entry } = scenarioFixture('mcp_full')
    const step = await runToFinalize(sourceUri)
    const continued = await call({ action: 'continue', lifecycle_token: step.lifecycle_token })
    const item = targetItem(continued.body.contract, entry.scu_id)
    expect(item.successor_admission!.decision).toBe('admit')
    state.toolMissing = targetUri
    const before = state.dispatched.length
    const executed = await call({ action: 'execute', lifecycle_token: continued.body.lifecycle_token, action_id: item.item_id })
    expect(executed.status).toBe(200)
    expect(state.dispatched.length).toBe(before)
    const done = executed.body.contract.plan_items.find((candidate) => candidate.item_id === item.item_id)!
    expect(done).toMatchObject({ state: 'observed', observation: { disposition: 'failed', gap_reason: 'successor_capability_not_in_catalogue' } })
    expect(done.successor_dispatch).toMatchObject({ decision: 'refuse', code: 'successor_capability_not_in_catalogue' })
    // Drain any other ready item, then the lifecycle reports its honest state instead of stranding.
    let cursor = executed.body
    while (cursor.next_action_ids.length > 0) {
      cursor = (await call({ action: 'execute', lifecycle_token: cursor.lifecycle_token, action_id: cursor.next_action_ids[0] })).body
    }
    const finalized = await POST(request({ action: 'finalize', lifecycle_token: cursor.lifecycle_token }))
    expect(finalized.status).toBe(200)
    expect((await finalized.json() as { closure: { status: string } }).closure.status).toMatch(/COMPLETE|BLOCKED|INCOMPLETE/)
  })

  it('tampered or unauthorized arguments on a successor item are a terminal refusal, not a stranded 409', async () => {
    const { sourceUri, targetUri, entry } = scenarioFixture('mcp_full')
    const step = await runToFinalize(sourceUri)
    const continued = await call({ action: 'continue', lifecycle_token: step.lifecycle_token })
    const item = targetItem(continued.body.contract, entry.scu_id)
    // Edit ONLY the authorization copy's `args` (its hash projection uses `authorization_args`, so every hash
    // gate still passes): the client-visible args no longer match the server-held plan.
    const row = state.store!.rows.get(continued.body.inquiry_id)!
    state.store!.rows.set(row.inquiry_id, {
      ...row,
      authorization_jsonb: {
        ...row.authorization_jsonb,
        plan_items: row.authorization_jsonb.plan_items.map((candidate) => candidate.item_id === item.item_id
          ? { ...candidate, args: { ...candidate.args, chart_id: 'not-the-authorized-chart' } } : candidate),
      },
    })
    const before = state.dispatched.length
    const executed = await call({ action: 'execute', lifecycle_token: continued.body.lifecycle_token, action_id: item.item_id })
    expect(executed.status).toBe(200)
    expect(state.dispatched.length).toBe(before)
    expect(state.dispatched).not.toContain(targetUri)
    const done = executed.body.contract.plan_items.find((candidate) => candidate.item_id === item.item_id)!
    expect(done).toMatchObject({ state: 'observed', observation: { disposition: 'failed', gap_reason: 'successor_arguments_not_authorized' } })
    expect(done.successor_dispatch).toMatchObject({ decision: 'refuse', code: 'successor_arguments_not_authorized' })
    expect(executed.body.next_action_ids).not.toContain(item.item_id)
    // No replay opportunity: the consumed token is dead.
    const replay = await call({ action: 'execute', lifecycle_token: continued.body.lifecycle_token, action_id: item.item_id })
    expect(replay.status).toBe(409)
    expect(state.dispatched.length).toBe(before)
  })

  it('a non-successor item with tampered arguments is still a plain request error (unchanged behavior)', async () => {
    const start = await call(startBody())
    const first = start.body.next_action_ids[0]!
    const row = state.store!.rows.get(start.body.inquiry_id)!
    state.store!.rows.set(row.inquiry_id, {
      ...row,
      authorization_jsonb: {
        ...row.authorization_jsonb,
        plan_items: row.authorization_jsonb.plan_items.map((candidate) => candidate.item_id === first ? { ...candidate, args: { ...candidate.args, chart_id: 'x' } } : candidate),
      },
    })
    const executed = await call({ action: 'execute', lifecycle_token: start.body.lifecycle_token, action_id: first })
    expect(executed.status).toBe(409)
    expect(executed.body.error).toBe('INQUIRY_ARGS_NOT_AUTHORIZED')
    expect(state.dispatched).toEqual([])
  })
})

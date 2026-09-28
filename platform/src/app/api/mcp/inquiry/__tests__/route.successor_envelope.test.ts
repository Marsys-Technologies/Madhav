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
  projectDecision,
  scenarioFixture,
} from '@/lib/vidhi/inquiry/__fixtures__/successor_envelope_scenario'

const state = vi.hoisted(() => ({
  dispatched: [] as string[],
  triggerUri: '',
  deniedUri: '',
  toolResult: (() => { throw new Error('unbound') }) as (name: string, args: Record<string, unknown>) => Record<string, unknown>,
  store: null as null | import('@/lib/vidhi/inquiry/__fixtures__/in_memory_lifecycle_store').InMemoryLifecycleStore,
}))

vi.mock('@/lib/mcp/service_token', () => ({ validateMcpServiceRequest: async () => true }))
vi.mock('@/lib/mcp/auth', () => ({ resolveMcpPrincipalRole: vi.fn().mockResolvedValue('guest') }))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: vi.fn().mockResolvedValue('all') }))
vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
vi.mock('@/lib/retrieval/registry/catalog', () => ({ getCatalog: () => [] }))
vi.mock('@/lib/retrieval/registry', () => ({
  getCapability: (uri: string) => ({ uri, mutation: false, calibration_context_only: false }),
}))
vi.mock('@/lib/retrieval/registry/knowledge', () => ({
  assertPinnedCapabilityKnowledgeCurrent: () => SCENARIO_SNAPSHOT,
  loadChartCapabilityOverlay: async () => SCENARIO_OVERLAY,
}))
vi.mock('@/lib/pipeline/no_leakage_filter', () => ({
  filterLeakedCapabilities: (names: readonly string[]) => names.filter((name) => name !== state.deniedUri),
}))
vi.mock('@/lib/retrieval/registry/tool_name_bridge', () => ({
  TOOL_NAME_TO_URI: {},
  resolveToolUri: (name: string) => (name.startsWith('marsys://') ? name : undefined),
  getToolByName: (name: string) => ({
    retrieve: async (_query: unknown, args: Record<string, unknown>) => {
      state.dispatched.push(name)
      const base = state.toolResult(name, { ...args, offset: 1 })
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
import { w5DoorParityToolResult } from '@/lib/vidhi/inquiry/__fixtures__/door_parity'

state.toolResult = w5DoorParityToolResult

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
    const executed = await call({ action: 'execute', lifecycle_token: continued.body.lifecycle_token, action_id: item.item_id })
    const dispatched = executed.body.contract.plan_items.find((candidate) => candidate.item_id === item.item_id)!.successor_dispatch!
    expect(projectDecision(dispatched)).toEqual(expectedAdmitProjection())
  })
})

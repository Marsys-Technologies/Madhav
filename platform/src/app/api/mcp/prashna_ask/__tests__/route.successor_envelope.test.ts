/**
 * Managed-door successor authorization envelope (Packet B) against the REAL compiler and the REAL
 * managed lifecycle over an in-memory store that keeps the durable store's CAS/reservation
 * semantics. The mocked-session tests in route.test.ts cannot see recovery or re-readying; these
 * can. Covers: an envelope-admitted successor dispatched though it was never in the request tool
 * set, a named terminal refusal, a recovered worker resuming a successor generation (no stranded
 * ready item, no replayed dispatch, no bypassed authorization), and an in-flight ambiguous action.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  SCENARIO_CHART_ID as CHART,
  SCENARIO_OVERLAY as OVERLAY,
  SCENARIO_QUESTION as QUESTION,
  SCENARIO_SCOPE as SCOPE,
  SCENARIO_SNAPSHOT as SNAPSHOT,
  compileScenarioRoot,
  expectedAdmitProjection,
  expectedDispatchProjection,
  projectDecision,
  scenarioFixture,
} from '@/lib/vidhi/inquiry/__fixtures__/successor_envelope_scenario'
import { stableFingerprint } from '@/lib/retrieval/registry/knowledge/stable'

const state = vi.hoisted(() => ({
  dispatched: [] as string[],
  triggerUri: '',
  deniedUri: '',
  permission: 'all' as 'all' | 'view' | 'deny',
  units: undefined as number | undefined,
  flaky: { uri: '', allow: 0, calls: 0 },
  // Bound after the static imports resolve: importing the fixture inside a mock factory would
  // deadlock on the module graph that itself imports the mocked bridge.
  toolResult: (() => { throw new Error('unbound') }) as (name: string, args: Record<string, unknown>) => Record<string, unknown>,
  store: null as null | import('@/lib/vidhi/inquiry/__fixtures__/in_memory_lifecycle_store').InMemoryLifecycleStore,
}))

vi.mock('@/lib/retrieval/registry/catalog', () => ({ getCatalog: () => [] }))
vi.mock('@/lib/retrieval/registry', () => ({
  getCapability: (uri: string) => ({ uri, mutation: false, calibration_context_only: false, display: { reader_label_key: 'examining_chart' }, ...(state.units === undefined ? {} : { dispatch_units: state.units }) }),
}))
vi.mock('@/lib/retrieval/registry/knowledge', () => ({
  assertPinnedCapabilityKnowledgeCurrent: () => SNAPSHOT,
  getPinnedCapabilityKnowledgeSnapshot: () => SNAPSHOT,
  loadChartCapabilityOverlay: async () => OVERLAY,
}))
vi.mock('@/lib/vidhi/inquiry/lifecycle_store', async () => {
  const { createInMemoryLifecycleStore } = await import('@/lib/vidhi/inquiry/__fixtures__/in_memory_lifecycle_store')
  const store = createInMemoryLifecycleStore()
  state.store = store
  return {
    createInquiryLifecycle: store.createInquiryLifecycle,
    getInquiryLifecycle: store.getInquiryLifecycle,
    listInquiryEvidence: store.listInquiryEvidence,
    createInquirySuccessorLifecycle: store.createInquirySuccessorLifecycle,
    reserveInquiryAction: store.reserveInquiryAction,
    markInquiryActionDispatched: store.markInquiryActionDispatched,
    commitInquiryObservation: store.commitInquiryObservation,
    commitInquiryFinalization: store.commitInquiryFinalization,
    failCloseAmbiguousInquiryAction: store.failCloseAmbiguousInquiryAction,
  }
})
vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
vi.mock('@/lib/charts/readiness', () => ({
  getChartReadinessMap: vi.fn(async (ids: string[]) => new Map(ids.map((id) => [id, { state: 'ready' }]))),
  isDerivedChartReady: (r: { state: string }) => r.state === 'ready',
}))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: async () => state.permission }))
vi.mock('@/lib/mcp/auth', () => ({ resolveMcpPrincipalRole: vi.fn().mockResolvedValue('guest') }))
vi.mock('@/lib/models/runtime_config', () => ({ getEffectiveModel: vi.fn().mockResolvedValue('fake-model') }))
vi.mock('@/lib/models/registry', () => {
  const MODEL = { id: 'expensive-model', maxInputTokens: 200_000, maxOutputTokens: 64_000, costPer1MInput: 15, costPer1MOutput: 75 }
  return { DEFAULT_STACK_ID: 'anthropic', MODELS: [MODEL], getModelMeta: (id: string) => (id === MODEL.id ? MODEL : undefined) }
})
vi.mock('@/lib/mcp/prashna_ask/byok_preflight', () => ({
  authorizeMcpByokPrincipal: vi.fn().mockResolvedValue({ role: 'guest' }),
  prepareMcpByokRuntime: vi.fn(),
}))
vi.mock('@/lib/ai-console/observability', () => ({ observeMcpExternalSynthesis: vi.fn() }))
const { mockPlanner, mockGetJob } = vi.hoisted(() => ({ mockPlanner: vi.fn(), mockGetJob: vi.fn() }))
vi.mock('@/lib/pipeline/pipeline_planner', () => ({ callPipelinePlanner: mockPlanner }))
vi.mock('@/lib/vidhi/inquiry/managed_job_store', () => ({ getManagedPrashnaJob: mockGetJob }))
vi.mock('@/lib/pipeline/compiled_floor_adapter', () => ({
  compileFloorForPlan: vi.fn(() => ({ toolCalls: [], mappedPrimitives: [], unmappedPrimitives: [], compilerIntent: 'general_synthesis', compileFailed: false, llm_extension_note: '' })),
  ensureB11WholeChartReadFloor: vi.fn(() => false),
  ensureDashaContextFloor: vi.fn(() => false),
}))
vi.mock('@/lib/pipeline/no_leakage_filter', () => ({
  filterLeakedCapabilities: (names: readonly string[]) => names.filter((name) => name !== state.deniedUri),
}))
vi.mock('@/lib/retrieval/registry/tool_name_bridge', () => ({
  TOOL_NAME_TO_URI: {},
  resolveToolUri: (name: string) => (name.startsWith('marsys://') ? name : undefined),
  getToolByName: (name: string) => name === state.flaky.uri && ++state.flaky.calls > state.flaky.allow ? undefined : ({
    name, version: 'route-successor-v1', dispatch_units: 1,
    retrieve: async (_query: unknown, args: Record<string, unknown>) => {
      state.dispatched.push(name)
      const base = state.toolResult(name, { ...args, offset: 1 })
      if (name !== state.triggerUri) return base
      return { ...base, results: [{ content: JSON.stringify({ rows: [{ yoga: 'Raja', fired: true, bhanga_active: true }], more_available: false }) }] }
    },
  }),
}))
const { mockSynthesize, mockHeader } = vi.hoisted(() => ({ mockSynthesize: vi.fn(), mockHeader: vi.fn() }))
vi.mock('@/lib/pipeline/prashna_ask_synthesis', () => ({ synthesizeReading: mockSynthesize }))
vi.mock('@/lib/retrieval/chart_header', () => ({ fetchChartHeaderResolution: mockHeader }))
vi.mock('@/lib/pariprashna/safety/flag', () => ({ SAFETY_GATE_FLAG: 'x', isSafetyGateEnabled: () => false }))

import { configService } from '@/lib/config/index'
import { __resetRpmCountersForTest } from '@/lib/mcp/rate_limiter_core'
import type { InquiryContract } from '@/lib/vidhi/inquiry'
import { buildSuccessorAdmissionLive } from '@/lib/vidhi/inquiry/successor_admission_live'
import { managedEvidenceSuccessorInquiryId, ManagedInquiryExecutionSession } from '@/lib/vidhi/inquiry/execution_session'
import { deriveEvidenceFrontier } from '@/lib/vidhi/inquiry/evidence_frontier'
import { POST } from '../route'
import { verifySuccessorCostLedger } from '@/lib/vidhi/inquiry/authorization_envelope'
import { buildInquiryDoorParityProjection } from '@/lib/vidhi/inquiry/door_parity'
import { w5DoorParityToolResult } from '@/lib/vidhi/inquiry/__fixtures__/door_parity'

state.toolResult = w5DoorParityToolResult

const PRINCIPAL = 'owner-uid'
const JOB_ID = 'aaaaaaaa-1111-4000-8000-000000000031'
const INQUIRY_ID = 'bbbbbbbb-1111-4000-8000-000000000031'

const compileRoot = () => compileScenarioRoot('platform_internal')
const fixture = () => scenarioFixture('platform_internal')

function post(): Promise<Response> {
  return POST(new Request('http://localhost/api/mcp/prashna_ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-mcp-internal-token': 'test-token', 'x-mcp-user': PRINCIPAL, 'x-mcp-key-id': 'mcp_test_KEY001' },
    body: JSON.stringify({
      chart_id: CHART, question: QUESTION, response_format: 'standard', scope_tuple: SCOPE,
      managed_job_id: JOB_ID, managed_inquiry_id: INQUIRY_ID,
    }),
  }))
}

async function finalEvent(response: Response): Promise<Record<string, unknown>> {
  const lines = (await response.text()).split('\n').map((line) => line.trim()).filter(Boolean).map((line) => JSON.parse(line) as Record<string, unknown>)
  expect(JSON.stringify(lines.at(-1)).slice(0, 600)).toContain('"event":"final"')
  return lines.at(-1)!
}

const successorRow = () => state.store!.rows.get(managedEvidenceSuccessorInquiryId(INQUIRY_ID))
const dispatchCount = (uri: string) => state.dispatched.filter((name) => name === uri).length

beforeEach(() => {
  vi.clearAllMocks()
  state.dispatched = []
  state.triggerUri = ''
  state.deniedUri = ''
  state.permission = 'all'
  state.units = undefined
  state.flaky = { uri: '', allow: 0, calls: 0 }
  state.store!.rows.clear()
  state.store!.reservations.clear()
  state.store!.evidence.length = 0
  __resetRpmCountersForTest()
  configService.setFlag('AI_CONSOLE_BYOK', false)
  process.env.MCP_INTERNAL_TOKEN = 'test-token'
  process.env.MCP_CALLER_OIDC_DISABLED_FOR_LOCAL_DEV = 'true'
  mockGetJob.mockResolvedValue({ chart_id: CHART, request_jsonb: { inquiry_id: INQUIRY_ID, question: QUESTION, response_format: 'standard' } })
  mockPlanner.mockResolvedValue({
    outcome: 'plan',
    plan: {
      query_class: 'holistic', query_intent_summary: 'test', domains: [], forward_looking: false,
      tool_calls: [], scope_tuple: SCOPE, history_mode: 'synthesized', expected_output_shape: 'structured_data',
    },
  })
  mockSynthesize.mockResolvedValue({ reading: 'A reading.', model_id: 'claude-sonnet-test', judgment_flags: [] })
  mockHeader.mockResolvedValue({ header: { chart_id_short: '1c826d5a', name: 'Test', lagna_sign: 'Aries', lagna_deg: 1, moon_sign: 'Pisces', sun_sign: 'Capricorn', ayanamsha: 'lahiri_chitrapaksha', current_maha_antar: 'A/B' }, flags: [] })
})

describe('managed door: envelope-admitted successor (real compiler + real lifecycle)', () => {
  it('dispatches an admitted successor that was never in the request tool set, and receipts the decision', async () => {
    const { sourceUri, targetUri, entry } = fixture()
    state.triggerUri = sourceUri
    await finalEvent(await post())

    expect(dispatchCount(targetUri)).toBe(1)
    const successor = successorRow()!
    expect(successor.parent_inquiry_id).toBe(INQUIRY_ID)
    const item = successor.contract_jsonb.plan_items.find((candidate) => candidate.scu_id === entry.scu_id)!
    expect(item.state).toBe('observed')
    expect(item.observation?.disposition).toBe('served')
    expect(item.successor_admission).toMatchObject({ decision: 'admit', code: 'successor_admitted', envelope_entry_id: entry.entry_id })
    expect(item.successor_dispatch).toMatchObject({ decision: 'admit', code: 'successor_admitted', scu_id: entry.scu_id })
    // Door parity: the same pinned contract and frontier produce the shared receipt projection.
    expect(projectDecision(item.successor_admission!)).toEqual(expectedAdmitProjection())
    expect(projectDecision(item.successor_dispatch!)).toEqual(expectedDispatchProjection())
    // The durable evidence receipt carries the admission alongside the bundle.
    const receipt = state.store!.evidence.find((candidate) => candidate.inquiry_id === successor.inquiry_id && candidate.plan_item_id === item.item_id)!
    expect((receipt.evidence_jsonb as { admission?: { decision: string; decision_hash: string } }).admission)
      .toMatchObject({ decision: 'admit', decision_hash: item.successor_dispatch!.decision_hash })
    // No stranded ready item anywhere in the lineage.
    for (const row of state.store!.rows.values()) expect(row.contract_jsonb.plan_items.some((candidate) => candidate.state === 'ready')).toBe(false)
  })

  it('refuses an admitted-by-plan successor the no-leakage/safety filters exclude: named terminal record, no dispatch', async () => {
    const { sourceUri, targetUri, entry } = fixture()
    state.triggerUri = sourceUri
    state.deniedUri = targetUri
    await finalEvent(await post())

    expect(dispatchCount(targetUri)).toBe(0)
    const successor = successorRow()!
    const item = successor.contract_jsonb.plan_items.find((candidate) => candidate.scu_id === entry.scu_id)!
    expect(item.state).toBe('observed')
    expect(item.observation).toMatchObject({ disposition: 'failed', gap_reason: 'successor_safety_excluded' })
    expect(item.successor_dispatch).toMatchObject({ decision: 'refuse', code: 'successor_safety_excluded' })
    // Never-dispatched: the receipt exists but nothing entered recovered evidence.
    // Door parity of the refused obligation: no evidence ref, failed, on EVERY door (the parity projection is graded).
    const refusedCoverage = buildInquiryDoorParityProjection(successor.contract_jsonb).obligation_coverage
      .filter((entry) => item.obligation_ids.includes(entry.obligation_id))
    expect(refusedCoverage.length).toBeGreaterThan(0)
    for (const entry of refusedCoverage) expect(entry).toMatchObject({ disposition: 'failed', evidence_present: false, evidence_hashes: [] })

    const receipt = state.store!.evidence.find((candidate) => candidate.inquiry_id === successor.inquiry_id && candidate.plan_item_id === item.item_id)!
    expect((receipt.evidence_jsonb as { bundle?: unknown }).bundle).toBeUndefined()
  })
})

/** Worker 1: runs the parent, hands off to a durable successor through the REAL session, then dies. */
async function handOffAsWorkerOne(contract: InquiryContract, sourceUri: string): Promise<boolean> {
  const session = await ManagedInquiryExecutionSession.open({
    inquiry_id: INQUIRY_ID, principal_uid: PRINCIPAL, contract, expires_at: new Date(Date.now() + 3_600_000).toISOString(),
  })
  for (const item of contract.plan_items.filter((candidate) => candidate.state === 'ready' && candidate.binding_id)) {
    expect(await session.beginAction(item.item_id)).toBe('acquired')
    const bundle = item.binding_id === `registry:${sourceUri}`
      ? { results: [{ content: JSON.stringify({ rows: [{ yoga: 'Raja', fired: true, bhanga_active: true }] }) }] }
      : { results: [{ content: JSON.stringify({ rows: [{ id: 'x' }], more_available: false }) }] }
    await session.persistAcceptedObservation({
      plan_item_id: item.item_id, obligation_ids: item.obligation_ids, scu_id: item.scu_id, binding_id: item.binding_id!,
      tool_name: item.binding_id!.slice('registry:'.length), bundle, disposition: 'served',
      pagination: { semantics: 'none', exhausted: true, next: null }, invocation_args: item.args,
      evidence_frontier: deriveEvidenceFrontier({ contract: session.currentContract, item_id: item.item_id, evidence_payload: bundle, snapshot: SNAPSHOT }),
    })
  }
  const handedOff = await session.continueWithEvidenceSuccessor({
    snapshot: SNAPSHOT, overlay: OVERLAY,
    admission: buildSuccessorAdmissionLive({
      transport: 'managed_mcp', chart_id: CHART, overlay: OVERLAY, principal_subject: PRINCIPAL, owner_principal_subject: PRINCIPAL,
      chart_permission: 'all',
    }),
  })
  // The stranding condition the route must handle: a successor generation with first-time ready items.
  expect(session.currentContract.successor).toBeDefined()
  expect(session.readyActionIds.length).toBeGreaterThan(0)
  expect(session.currentContract.plan_items.filter((item) => item.state === 'ready').every((item) => item.observation === null)).toBe(true)
  return handedOff
}

describe('managed door: recovered worker resuming a successor generation', () => {
  /** Worker 1 hands off (see handOffAsWorkerOne), then dies. */
  async function workerOneHandsOff() {
    const base = fixture()
    expect(await handOffAsWorkerOne(base.contract, base.sourceUri)).toBe(true)
    return base
  }

  it('drains the successor first-time items through the envelope: nothing stranded, nothing replayed', async () => {
    const { contract, targetUri } = await workerOneHandsOff()
    const parentUris = contract.plan_items.flatMap((item) => item.binding_id ? [item.binding_id.slice('registry:'.length)] : [])
    state.dispatched = []
    await finalEvent(await post())

    // The recovered worker dispatched the successor's capability exactly once...
    expect(dispatchCount(targetUri)).toBe(1)
    // ...and never replayed a single parent dispatch (their evidence was recovered, not re-fetched).
    for (const uri of parentUris) expect(dispatchCount(uri), uri).toBe(0)
    const successor = successorRow()!
    expect(successor.contract_jsonb.plan_items.some((item) => item.state === 'ready')).toBe(false)
    const item = successor.contract_jsonb.plan_items.find((candidate) => candidate.observation !== null && candidate.successor_dispatch)!
    expect(item.successor_dispatch).toMatchObject({ decision: 'admit' })

    // A further recovery after completion re-dispatches nothing.
    state.dispatched = []
    await finalEvent(await post())
    expect(state.dispatched).toEqual([])
  })

  it('cannot be turned into a bypass: a stored envelope that no longer matches its hash authorizes nothing', async () => {
    const { targetUri } = await workerOneHandsOff()
    const row = successorRow()!
    const parent = row.contract_jsonb.successor!.parent_contract
    const tampered = {
      ...row.contract_jsonb,
      successor: { ...row.contract_jsonb.successor!, parent_contract: { ...parent, authorization_envelope: { ...parent.authorization_envelope!, entries: [] } } },
    } as InquiryContract
    state.store!.rows.set(row.inquiry_id, { ...row, contract_jsonb: tampered })
    state.dispatched = []
    await finalEvent(await post())

    expect(dispatchCount(targetUri)).toBe(0)
    const stored = successorRow()!.contract_jsonb
    expect(stored.plan_items.some((item) => item.state === 'ready')).toBe(false)
    // The successor receipt's own seal covers its embedded parent, so the rewritten envelope is caught
    // before any per-item decision: refused outright, terminal, never dispatched.
    expect(stored.plan_items.some((item) => item.observation?.gap_reason === 'successor_receipt_incomplete')).toBe(true)
  })

  it('a stored compile-time refusal is final: a recovered worker never upgrades it to an admission', async () => {
    const { targetUri, entry } = await workerOneHandsOff()
    const row = successorRow()!
    const forgedRefusal = { ...row.contract_jsonb.plan_items.find((item) => item.scu_id === entry.scu_id)!.successor_admission!, decision: 'refuse' as const, code: 'successor_cost_limit_exceeded' as const }
    const body: Record<string, unknown> = { ...forgedRefusal }
    delete body['decision_hash']
    const sealed = { ...body, decision_hash: stableFingerprint(body) }
    const edited = { ...row.contract_jsonb, plan_items: row.contract_jsonb.plan_items.map((item) => item.scu_id === entry.scu_id ? { ...item, successor_admission: sealed } : item) } as InquiryContract
    state.store!.rows.set(row.inquiry_id, { ...row, contract_jsonb: edited })
    state.dispatched = []
    await finalEvent(await post())

    expect(dispatchCount(targetUri)).toBe(0)
    const item = successorRow()!.contract_jsonb.plan_items.find((candidate) => candidate.scu_id === entry.scu_id)!
    expect(item.observation?.gap_reason).toBe('successor_cost_limit_exceeded')
  })

  it('an in-flight successor action a dead worker left dispatched is failed closed, never replayed', async () => {
    const { targetUri } = await workerOneHandsOff()
    // Worker 2 (a session over the same durable row) crosses the dispatch boundary and dies before commit.
    const session = await ManagedInquiryExecutionSession.open({
      inquiry_id: INQUIRY_ID, principal_uid: PRINCIPAL, contract: compileRoot(), expires_at: new Date(Date.now() + 3_600_000).toISOString(),
    })
    const inFlight = session.currentContract.plan_items.find((item) => item.state === 'ready')!
    expect(await session.beginAction(inFlight.item_id)).toBe('acquired')
    state.store!.expireLeases()
    state.dispatched = []
    await finalEvent(await post())

    expect(dispatchCount(targetUri)).toBe(0)
    expect(successorRow()!.status).toBe('BLOCKED')
    expect(successorRow()!.current_jti_hash).toBe('terminal')
  })
})

describe('managed door: server-authoritative entitlement', () => {
  it('a view-only permission yields an empty envelope, so no successor is admitted (whatever scope the planner declared)', async () => {
    const { sourceUri, targetUri, entry } = fixture()
    state.triggerUri = sourceUri
    state.permission = 'view'
    await finalEvent(await post())

    expect(dispatchCount(targetUri)).toBe(0)
    const root = state.store!.rows.get(INQUIRY_ID)!.contract_jsonb
    expect(root.scope_tuple.entitlement).toBe('native')
    expect(root.authorization_envelope!.entries).toEqual([])
    expect(root.authorization_envelope!.effective_entitlement).toEqual({ tier: 'public_disclosed', source: 'chart_permission_view' })
    const item = successorRow()!.contract_jsonb.plan_items.find((candidate) => candidate.scu_id === entry.scu_id)!
    expect(item.observation).toMatchObject({ disposition: 'failed', gap_reason: 'successor_capability_not_authorized_for_request' })
    expect(item.state).toBe('observed')
  })

  it('revalidates at dispatch: a recovered worker whose principal now holds only view refuses the successor item', async () => {
    const { contract, sourceUri, targetUri } = fixture()
    void sourceUri
    // Worker 1 (full permission) hands off to the successor and dies.
    const handedOff = await handOffAsWorkerOne(contract, sourceUri)
    expect(handedOff).toBe(true)
    state.permission = 'view'
    state.dispatched = []
    await finalEvent(await post())
    expect(dispatchCount(targetUri)).toBe(0)
    const item = successorRow()!.contract_jsonb.plan_items.find((candidate) => candidate.successor_dispatch)!
    expect(item.successor_dispatch).toMatchObject({ decision: 'refuse', code: 'successor_entitlement_not_permitted', entitlement: { tier: 'public_disclosed' } })
  })
})

describe('managed door: the shared successor cost model', () => {
  it('charges each dispatched successor item once, persisted, and a recovered worker neither resets nor double-charges it', async () => {
    const { sourceUri } = fixture()
    state.triggerUri = sourceUri
    state.units = 2
    await finalEvent(await post())
    const ledger = successorRow()!.contract_jsonb.successor_cost_ledger!
    const dispatched = successorRow()!.contract_jsonb.plan_items.filter((item) => item.successor_dispatch?.decision === 'admit')
    expect(dispatched.length).toBeGreaterThan(0)
    expect(ledger.entries).toHaveLength(dispatched.length)
    expect(ledger.consumed_units).toBe(dispatched.length * 2)
    expect(verifySuccessorCostLedger(ledger)).toBe(true)

    // A later recovery of the completed lifecycle dispatches nothing and adds no charge.
    state.dispatched = []
    await finalEvent(await post())
    expect(state.dispatched).toEqual([])
    expect(successorRow()!.contract_jsonb.successor_cost_ledger).toEqual(ledger)
  })

  it('refuses a priced-out successor with successor_cost_limit_exceeded (budget 12, price 13): terminal, undispatched, uncharged', async () => {
    const { sourceUri, targetUri, entry } = fixture()
    state.triggerUri = sourceUri
    state.units = 13
    await finalEvent(await post())
    expect(dispatchCount(targetUri)).toBe(0)
    const item = successorRow()!.contract_jsonb.plan_items.find((candidate) => candidate.scu_id === entry.scu_id)!
    expect(item.observation).toMatchObject({ disposition: 'failed', gap_reason: 'successor_cost_limit_exceeded' })
    expect(item.successor_admission).toMatchObject({ code: 'successor_cost_limit_exceeded', limit_state: { budget_units: 12, consumed_units: 0, candidate_units: 13, remaining_units: 12 } })
    expect(successorRow()!.contract_jsonb.successor_cost_ledger).toBeUndefined()
  })

  it('an in-flight ambiguous successor dispatch is failed closed and cannot be replayed to obtain more budget', async () => {
    const { contract, sourceUri, targetUri } = fixture()
    await handOffAsWorkerOne(contract, sourceUri)
    const session = await ManagedInquiryExecutionSession.open({
      inquiry_id: INQUIRY_ID, principal_uid: PRINCIPAL, contract: compileRoot(), expires_at: new Date(Date.now() + 3_600_000).toISOString(),
    })
    const inFlight = session.currentContract.plan_items.find((item) => item.state === 'ready')!
    expect(await session.beginAction(inFlight.item_id)).toBe('acquired')
    state.store!.expireLeases()
    state.dispatched = []
    await finalEvent(await post())
    expect(dispatchCount(targetUri)).toBe(0)
    expect(successorRow()!.status).toBe('BLOCKED')
    expect(successorRow()!.contract_jsonb.successor_cost_ledger).toBeUndefined()
  })
})

describe('managed door: the shared post-evaluation gate', () => {
  it('an admitted item whose live tool disappears before dispatch is refused: receipted, terminal, uncharged, undispatched', async () => {
    const { sourceUri, targetUri, entry } = fixture()
    state.triggerUri = sourceUri
    // Lookups of the target: #1 successor compile (evaluator), #2 dispatch-time evaluator, #3 the drain's own lookup -> gone.
    state.flaky = { uri: targetUri, allow: 2, calls: 0 }
    await finalEvent(await post())
    expect(dispatchCount(targetUri)).toBe(0)
    const successor = successorRow()!
    const item = successor.contract_jsonb.plan_items.find((candidate) => candidate.scu_id === entry.scu_id)!
    expect(item).toMatchObject({ state: 'observed', observation: { disposition: 'failed', gap_reason: 'successor_capability_not_in_catalogue' } })
    expect(item.successor_dispatch).toMatchObject({ decision: 'refuse', code: 'successor_capability_not_in_catalogue' })
    expect((successor.contract_jsonb.successor_cost_ledger?.entries ?? []).some((charge) => charge.item_id === item.item_id)).toBe(false)
  })
})

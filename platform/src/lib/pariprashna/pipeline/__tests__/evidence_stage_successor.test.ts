/**
 * Portal evidence-driven successor (Pūrṇa R2B.4b / review RC-5.4).
 *
 * When a served observation calls for a capability the plan did not include, the Portal door
 * continues through one deterministic successor in the same request — dispatching it only when the
 * shared authorization envelope (Packet B) admits it, recomputed at dispatch from server-held state —
 * and the final contract carries its parent so the fact register accounts for the whole chain.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'
import { w5DoorParityPlan, w5DoorParityToolResult } from '@/lib/vidhi/inquiry/__fixtures__/door_parity'
import { buildInquiryFactRegister } from '@/lib/vidhi/inquiry/response_accountability'
import { buildInquiryDoorParityProjection } from '@/lib/vidhi/inquiry/door_parity'
import type { InquiryContract } from '@/lib/vidhi/inquiry'
import {
  SCENARIO_CHART_ID as CHART_ID,
  SCENARIO_OVERLAY as OVERLAY,
  SCENARIO_SNAPSHOT as SNAPSHOT,
  expectedAdmitProjection,
  expectedDispatchProjection,
  projectDecision,
  scenarioFixture,
} from '@/lib/vidhi/inquiry/__fixtures__/successor_envelope_scenario'

const state = vi.hoisted(() => ({ triggerTool: '' as string, dispatched: [] as string[], paginate: false, units: undefined as number | undefined, flaky: { uri: '', allow: 0, calls: 0 } }))

vi.mock('@/lib/bundle/bundle_hydrator', () => ({
  hydrateBundle: async () => ({ assets: [], floor_enforced: false, total_bytes: 0, total_tokens: 0 }),
}))
vi.mock('@/lib/retrieval/registry/knowledge', () => ({
  getPinnedCapabilityKnowledgeSnapshot: () => SNAPSHOT,
  loadChartCapabilityOverlay: async () => OVERLAY,
}))
vi.mock('@/lib/retrieval/registry', () => ({
  getCapability: (uri: string) => ({ uri, mutation: false, calibration_context_only: false, display: { reader_label_key: 'examining_chart' }, ...(state.units === undefined ? {} : { dispatch_units: state.units }) }),
}))
vi.mock('@/lib/retrieval/registry/catalog', () => ({ getCatalog: () => [] }))
vi.mock('@/lib/retrieval/qos/dispatch_queue', () => ({
  getSharedQosDispatchQueue: () => ({ submit: async ({ run }: { run: () => Promise<unknown> }) => run() }),
}))
vi.mock('@/lib/cache/index', () => ({
  createToolCache: () => ({}),
  executeWithCache: async (tool: { retrieve: (q: unknown, a: unknown) => Promise<unknown> }, query: unknown, _cache: unknown, params: unknown) =>
    tool.retrieve(query, params ?? {}),
}))
vi.mock('@/lib/retrieval/registry/tool_name_bridge', () => ({
  TOOL_NAME_TO_URI: {},
  resolveToolUri: (name: string) => name,
  getToolByName: (name: string) => name === state.flaky.uri && ++state.flaky.calls > state.flaky.allow ? undefined : ({
    name,
    version: 'successor-fixture-v1',
    dispatch_units: 1,
    retrieve: async (_query: unknown, args: Record<string, unknown>) => {
      state.dispatched.push(name)
      // offset 1 is the fixture's last page; `paginate` serves page one with more available.
      const base = w5DoorParityToolResult(name, state.paginate ? args : { ...args, offset: 1 })
      if (name !== state.triggerTool) return base
      // A served row whose structured fields call for the cancellation analysis.
      return { ...base, results: [{ content: JSON.stringify({ rows: [{ yoga: 'Raja', fired: true, bhanga_active: true }], more_available: false }) }] }
    },
  }),
}))

const { runEvidenceStage } = await import('../evidence_stage')

function emitter(): { em: PariprashnaEmitter; flags: Array<Record<string, unknown>> } {
  const flags: Array<Record<string, unknown>> = []
  return {
    flags,
    em: new Proxy({}, {
      get: (_target, property: string) => (body: Record<string, unknown>) => { if (property === 'flag') flags.push(body) },
    }) as unknown as PariprashnaEmitter,
  }
}

function setup(): { contract: InquiryContract; source: string; targetUri: string } {
  const { contract, sourceUri, targetUri } = scenarioFixture('platform_internal')
  return { contract, source: sourceUri, targetUri }
}

async function run(contract: InquiryContract, toolsAuthorized: string[], extra: { chartPermission?: 'all' | 'view' | 'deny' | null; excludedCapabilities?: string[] } = {}) {
  const { em, flags } = emitter()
  const out = await runEvidenceStage({
    em, request: new Request('http://localhost/api/pariprashna', { method: 'POST' }),
    chartId: CHART_ID, userUid: 'fixture-principal',
    plan: w5DoorParityPlan(), queryPlan: {} as never, manifest: {} as never,
    toolsAuthorized, orientationPromise: Promise.resolve(null), inquiryContract: contract,
    chartPermission: 'all',
    ...extra,
  })
  return { out, flags }
}

const planTools = (contract: InquiryContract) =>
  [...new Set(contract.plan_items.flatMap((item) => item.binding_id ? [item.binding_id.slice('registry:'.length)] : []))]

describe('Portal evidence-driven successor', () => {
  beforeEach(() => { state.units = undefined; state.flaky = { uri: '', allow: 0, calls: 0 } })

  it('continues into the admitted capability when the request is authorized for it, and keeps the chain', async () => {
    const { contract, source, targetUri } = setup()
    state.triggerTool = source
    state.dispatched = []
    const authorized = [...new Set(contract.plan_items.flatMap((item) => item.binding_id ? [item.binding_id.slice('registry:'.length)] : [])), targetUri]
    const { out, flags } = await run(contract, authorized)

    const final = out.inquiryContract!
    expect(final.successor?.parent_contract.contract_id).toBe(contract.contract_id)
    expect(state.dispatched).toContain(targetUri)
    expect(flags.map((flag) => flag.code)).toContain('inquiry_evidence_successor')
    const register = buildInquiryFactRegister(final, out.validToolResults, SNAPSHOT)
    // The parent's obligations are still accounted for alongside the successor's.
    expect(register.facts.filter((fact) => fact.kind === 'obligation').length)
      .toBe(contract.obligations.length + final.obligations.length)
  })

  it('dispatches an envelope-admitted successor even though the request tool set never contained it', async () => {
    const { contract, source, targetUri } = setup()
    state.triggerTool = source
    state.dispatched = []
    const authorized = planTools(contract).filter((uri) => uri !== targetUri)
    const { out } = await run(contract, authorized)

    const final = out.inquiryContract!
    expect(state.dispatched).toContain(targetUri)
    const item = final.plan_items.find((candidate) => candidate.binding_id === `registry:${targetUri}`)!
    // Attributable: the compile-time decision and the dispatch-time decision are both on the item.
    expect(item.successor_admission).toMatchObject({ decision: 'admit', code: 'successor_admitted' })
    expect(item.successor_dispatch).toMatchObject({ decision: 'admit', code: 'successor_admitted', scu_id: item.scu_id })
    expect(item.observation?.disposition).toBe('served')
    // Door parity: the same pinned contract and frontier produce the shared receipt projection.
    expect(projectDecision(item.successor_admission!)).toEqual(expectedAdmitProjection())
    expect(projectDecision(item.successor_dispatch!)).toEqual(expectedDispatchProjection())
  })

  it('never dispatches a successor the request safety pass excluded; it names the gap with the decision code', async () => {
    const { contract, source, targetUri } = setup()
    state.triggerTool = source
    state.dispatched = []
    const { out } = await run(contract, planTools(contract), { excludedCapabilities: [targetUri] })

    const final = out.inquiryContract!
    expect(state.dispatched).not.toContain(targetUri)
    expect(final.status).not.toBe('COMPLETE')
    const item = final.plan_items.find((candidate) => candidate.binding_id === `registry:${targetUri}`)!
    expect(item.observation).toMatchObject({ disposition: 'failed', gap_reason: 'successor_safety_excluded' })
    // Same terminal shape as the managed and raw doors (a refused item is observed, never left ready).
    expect(item.state).toBe('observed')
    // Door parity of the refused obligation: no evidence ref, failed, on EVERY door (the parity projection is graded).
    const refusedCoverage = buildInquiryDoorParityProjection(final).obligation_coverage
      .filter((entry) => item.obligation_ids.includes(entry.obligation_id))
    expect(refusedCoverage.length).toBeGreaterThan(0)
    for (const entry of refusedCoverage) expect(entry).toMatchObject({ disposition: 'failed', evidence_present: false, evidence_hashes: [] })

    expect(item.successor_dispatch).toMatchObject({ decision: 'refuse', code: 'successor_safety_excluded' })
  })

  it('requires the route to have verified chart access; without it every successor item is refused', async () => {
    const { contract, source, targetUri } = setup()
    state.triggerTool = source
    state.dispatched = []
    const { out } = await run(contract, planTools(contract), { chartPermission: 'deny' })
    expect(state.dispatched).not.toContain(targetUri)
    const item = out.inquiryContract!.plan_items.find((candidate) => candidate.binding_id === `registry:${targetUri}`)!
    expect(item.observation?.gap_reason).toBe('successor_chart_access_not_verified')
  })

  it('keeps the named gap for a capability outside the envelope (no envelope entry, no dispatch)', async () => {
    const { contract, source, targetUri } = setup()
    state.triggerTool = source
    state.dispatched = []
    const outside = { ...contract, authorization_envelope: { ...contract.authorization_envelope!, entries: [] } }
    const { out } = await run(outside as InquiryContract, planTools(contract).filter((uri) => uri !== targetUri))
    expect(state.dispatched).not.toContain(targetUri)
    const final = out.inquiryContract!
    expect(final.status).not.toBe('COMPLETE')
    expect(final.plan_items.some((item) => item.observation?.gap_reason === 'successor_capability_not_authorized_for_request')).toBe(true)
  })

  it('does not auto-continue on a capped same-capability pagination frontier', async () => {
    const { contract } = setup()
    state.triggerTool = '__none__'
    state.dispatched = []
    state.paginate = true
    try {
      const authorized = [...new Set(contract.plan_items.flatMap((item) => item.binding_id ? [item.binding_id.slice('registry:'.length)] : []))]
      const { out, flags } = await run({ ...contract, max_iterations: 1 }, authorized)
      // Non-vacuous: the cap really left a required same-capability page frontier behind.
      expect(out.inquiryContract!.material_frontier.some((frontier) => frontier.disposition === 'capped')).toBe(true)
      expect(out.inquiryContract!.successor).toBeUndefined()
      expect(flags.map((flag) => flag.code)).not.toContain('inquiry_evidence_successor')
    } finally {
      state.paginate = false
    }
  })

  it('revalidates entitlement at dispatch: a contract issued under full permission is refused when the live grant is view-only', async () => {
    const { contract, source, targetUri } = setup()
    state.triggerTool = source
    state.dispatched = []
    const { out } = await run(contract, planTools(contract), { chartPermission: 'view' })
    expect(state.dispatched).not.toContain(targetUri)
    const item = out.inquiryContract!.plan_items.find((candidate) => candidate.binding_id === `registry:${targetUri}`)!
    expect(item.successor_dispatch).toMatchObject({ decision: 'refuse', code: 'successor_entitlement_not_permitted', entitlement: { tier: 'public_disclosed', source: 'chart_permission_view' } })
    expect(item.state).toBe('observed')
  })

  it('a denied or absent permission admits nothing and dispatches nothing', async () => {
    for (const permission of ['deny', null] as const) {
      const { contract, source, targetUri } = setup()
      state.triggerTool = source
      state.dispatched = []
      const { out } = await run(contract, planTools(contract), { chartPermission: permission })
      expect(state.dispatched, String(permission)).not.toContain(targetUri)
      const item = out.inquiryContract!.plan_items.find((candidate) => candidate.binding_id === `registry:${targetUri}`)!
      expect(item.successor_dispatch, String(permission)).toMatchObject({ decision: 'refuse', code: 'successor_chart_access_not_verified' })
    }
  })

  it('charges the shared successor ledger once per dispatched item, and refuses a priced-out successor without charging it', async () => {
    const { contract, source, targetUri } = setup()
    state.triggerTool = source
    state.dispatched = []
    state.units = 2
    const charged = (await run(contract, planTools(contract))).out.inquiryContract!
    const dispatched = charged.plan_items.filter((item) => item.successor_dispatch?.decision === 'admit')
    expect(dispatched.length).toBeGreaterThan(0)
    expect(charged.successor_cost_ledger!.entries).toHaveLength(dispatched.length)
    expect(charged.successor_cost_ledger!.consumed_units).toBe(dispatched.length * 2)

    state.dispatched = []
    state.units = 13 // above the 12-unit ceiling
    const priced = (await run(contract, planTools(contract))).out.inquiryContract!
    expect(state.dispatched).not.toContain(targetUri)
    const item = priced.plan_items.find((candidate) => candidate.binding_id === `registry:${targetUri}`)!
    expect(item.observation).toMatchObject({ disposition: 'failed', gap_reason: 'successor_cost_limit_exceeded' })
    expect(priced.successor_cost_ledger).toBeUndefined()
  })

  it('an admitted item whose live tool disappears before dispatch is refused by the shared gate: receipted, terminal, uncharged', async () => {
    const { contract, source, targetUri } = setup()
    state.triggerTool = source
    state.dispatched = []
    // Lookups of the target: #1 successor compile (evaluator), #2 dispatch-time evaluator, #3 the stage's own lookup -> gone.
    state.flaky = { uri: targetUri, allow: 2, calls: 0 }
    const { out } = await run(contract, planTools(contract))
    expect(state.dispatched).not.toContain(targetUri)
    const item = out.inquiryContract!.plan_items.find((candidate) => candidate.binding_id === `registry:${targetUri}`)!
    expect(item.observation).toMatchObject({ disposition: 'failed', gap_reason: 'successor_capability_not_in_catalogue' })
    expect(item.successor_dispatch).toMatchObject({ decision: 'refuse', code: 'successor_capability_not_in_catalogue' })
    expect(item.state).toBe('observed')
    // Uncharged: no ledger entry pays for this item (a sibling successor item may legitimately have been charged).
    expect((out.inquiryContract!.successor_cost_ledger?.entries ?? []).some((entry) => entry.item_id === item.item_id)).toBe(false)
  })
})

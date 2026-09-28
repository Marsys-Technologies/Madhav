/**
 * Portal evidence-driven successor (Pūrṇa R2B.4b / review RC-5.4).
 *
 * When a served observation calls for a capability the plan did not include, the Portal door
 * continues through one deterministic successor in the same request — dispatching it only when the
 * shared authorization envelope (Packet B) admits it, recomputed at dispatch from server-held state —
 * and the final contract carries its parent so the fact register accounts for the whole chain.
 */
import { describe, expect, it, vi } from 'vitest'
import type { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'
import generatedSnapshot from '@/generated/capability_knowledge.snapshot.json'
import { w5DoorParityPlan, w5DoorParityToolResult } from '@/lib/vidhi/inquiry/__fixtures__/door_parity'
import { buildInquiryFactRegister } from '@/lib/vidhi/inquiry/response_accountability'
import { compileInquiryContract } from '@/lib/vidhi/inquiry/compiler'
import type { InquiryContract } from '@/lib/vidhi/inquiry'
import type { CapabilityKnowledgeSnapshot, ChartCapabilityOverlay } from '@/lib/retrieval/registry/knowledge/types'

const CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const SNAPSHOT = generatedSnapshot as CapabilityKnowledgeSnapshot
// Every platform-internal binding proven available, so only authorization limits dispatch.
const OVERLAY: ChartCapabilityOverlay = {
  chart_id: CHART_ID, overlay_version: 'sha256:successor-fixture-overlay',
  capability_compatibility_version: SNAPSHOT.compatibility_version, catalog_content_hash: SNAPSHOT.content_hash,
  build_id: 'generation:successor-fixture', code_revision: 'fixture', writer_inventory_hash: null,
  generated_at: '2026-09-27T00:00:00.000Z',
  availability: SNAPSHOT.scus.map((scu) => ({
    scu_id: scu.scu_id, state: 'available' as const, build_status: 'served_generation', build_id: 'generation:successor-fixture',
    freshness: 'fixture', gaps: [], asset_receipts: [],
    available_binding_ids: scu.bindings.filter((binding) => binding.executable
      && binding.execution_channels?.includes('platform_internal')).map((binding) => binding.binding_id),
  })),
}

const state = vi.hoisted(() => ({ triggerTool: '' as string, dispatched: [] as string[], paginate: false }))

vi.mock('@/lib/bundle/bundle_hydrator', () => ({
  hydrateBundle: async () => ({ assets: [], floor_enforced: false, total_bytes: 0, total_tokens: 0 }),
}))
vi.mock('@/lib/retrieval/registry/knowledge', () => ({
  getPinnedCapabilityKnowledgeSnapshot: () => SNAPSHOT,
  loadChartCapabilityOverlay: async () => OVERLAY,
}))
vi.mock('@/lib/retrieval/registry', () => ({
  getCapability: (uri: string) => ({ uri, mutation: false, calibration_context_only: false, display: { reader_label_key: 'examining_chart' } }),
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
  getToolByName: (name: string) => ({
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

const TARGETS = ['scu.yoga.firing_and_cancellation', 'scu.catalog.judgment_query']

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
  const contract = compileInquiryContract({
    snapshot: SNAPSHOT, overlay: OVERLAY, chart_id: CHART_ID, question: 'What is my current dasha?',
    scope_tuple: { intent: 'timing', domains: ['general'], width: 'narrow', depth: 'retrieval', horizon: 'current', intervention: 'none', entitlement: 'native' } as never,
    execution_channel: 'platform_internal', temporal_anchor_date: '2026-09-27',
  })
  const planned = new Set([...contract.obligations.flatMap((o) => o.scu_ids), ...contract.plan_items.map((i) => i.scu_id)])
  const target = TARGETS.find((scuId) => !planned.has(scuId))
  const source = contract.plan_items.find((item) => item.state === 'ready' && item.binding_id
    && contract.obligations.some((o) => item.obligation_ids.includes(o.obligation_id) && o.materiality === 'required'))
  if (!target || !source?.binding_id) throw new Error('fixture has no unplanned rule target or required source')
  const targetScu = SNAPSHOT.scus.find((scu) => scu.scu_id === target)!
  const targetBinding = targetScu.bindings.find((binding) => binding.executable && binding.binding_id.startsWith('registry:')
    && binding.execution_channels?.includes('platform_internal'))!
  return { contract, source: source.binding_id.slice('registry:'.length), targetUri: targetBinding.binding_id.slice('registry:'.length) }
}

async function run(contract: InquiryContract, toolsAuthorized: string[], extra: { chartAccessVerified?: boolean; excludedCapabilities?: string[] } = {}) {
  const { em, flags } = emitter()
  const out = await runEvidenceStage({
    em, request: new Request('http://localhost/api/pariprashna', { method: 'POST' }),
    chartId: CHART_ID, userUid: 'fixture-principal',
    plan: w5DoorParityPlan(), queryPlan: {} as never, manifest: {} as never,
    toolsAuthorized, orientationPromise: Promise.resolve(null), inquiryContract: contract,
    chartAccessVerified: true,
    ...extra,
  })
  return { out, flags }
}

const planTools = (contract: InquiryContract) =>
  [...new Set(contract.plan_items.flatMap((item) => item.binding_id ? [item.binding_id.slice('registry:'.length)] : []))]

describe('Portal evidence-driven successor', () => {
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
    expect(item.successor_dispatch).toMatchObject({ decision: 'refuse', code: 'successor_safety_excluded' })
  })

  it('requires the route to have verified chart access; without it every successor item is refused', async () => {
    const { contract, source, targetUri } = setup()
    state.triggerTool = source
    state.dispatched = []
    const { out } = await run(contract, planTools(contract), { chartAccessVerified: false })
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
})

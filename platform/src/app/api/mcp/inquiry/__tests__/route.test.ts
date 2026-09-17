import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  authorize: vi.fn(),
  issue: vi.fn(),
  verify: vi.fn(),
  create: vi.fn(),
  createSuccessor: vi.fn(),
  get: vi.fn(),
  commitObservation: vi.fn(),
  commitFinalization: vi.fn(),
  reserve: vi.fn(),
  markDispatched: vi.fn(),
  failCloseAmbiguous: vi.fn(),
  retrieve: vi.fn(),
  apply: vi.fn(),
  finalize: vi.fn(),
  pagination: vi.fn(),
  classify: vi.fn(),
  compile: vi.fn(),
  overlay: vi.fn(),
  snapshot: vi.fn(),
  capability: vi.fn(),
}))

vi.mock('@/lib/mcp/service_token', () => ({ validateMcpServiceRequest: async () => true }))
vi.mock('@/lib/mcp/auth', () => ({ resolveMcpPrincipalRole: vi.fn().mockResolvedValue('guest') }))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: mocks.authorize }))
vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
vi.mock('@/lib/retrieval/registry/catalog', () => ({ getCatalog: () => [] }))
vi.mock('@/lib/retrieval/registry', () => ({ getCapability: mocks.capability }))
vi.mock('@/lib/retrieval/registry/knowledge', () => ({
  assertPinnedCapabilityKnowledgeCurrent: mocks.snapshot,
  loadChartCapabilityOverlay: mocks.overlay,
}))
vi.mock('@/lib/retrieval/registry/tool_name_bridge', () => ({
  getToolByName: (name: string) => ({
    retrieve: (query: unknown, args: Record<string, unknown>) => mocks.retrieve(name, query, args),
  }),
}))
vi.mock('@/lib/vidhi/inquiry', async (importOriginal) => {
  const original = await importOriginal<typeof import('@/lib/vidhi/inquiry')>()
  return {
    ...original,
    compileInquiryContract: mocks.compile,
    applyInquiryObservations: mocks.apply,
    finalizeInquiryContract: mocks.finalize,
    issueInquiryLifecycleToken: mocks.issue,
    verifyInquiryLifecycleToken: mocks.verify,
    hashJti: (jti: string) => `sha256:${jti}`,
    deriveInquiryPaginationReceipt: mocks.pagination,
    classifyInquiryResult: mocks.classify,
    inquiryAuthorizationHashes: (value: InquiryContract) => value.question === 'Assess wealth through the reviewed cross-door evidence surface.'
      ? original.inquiryAuthorizationHashes(value)
      : { semantic_contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan', contract_id: 'sha256:combined' },
  }
})
vi.mock('@/lib/vidhi/inquiry/lifecycle_store', () => ({
  createInquiryLifecycle: mocks.create,
  createInquirySuccessorLifecycle: mocks.createSuccessor,
  getInquiryLifecycle: mocks.get,
  commitInquiryObservation: mocks.commitObservation,
  commitInquiryFinalization: mocks.commitFinalization,
  reserveInquiryAction: mocks.reserve,
  markInquiryActionDispatched: mocks.markDispatched,
  failCloseAmbiguousInquiryAction: mocks.failCloseAmbiguous,
}))

import type { InquiryContract } from '@/lib/vidhi/inquiry'
import { POST } from '../route'
import { compileInquiryContract, finalizeInquiryContract, recordInquiryExecution } from '@/lib/vidhi/inquiry/compiler'
import { classifyInquiryResult, deriveInquiryPaginationReceipt } from '@/lib/vidhi/inquiry/pagination'
import { managedPlanToAiInquiryProposal } from '@/lib/vidhi/inquiry/managed_bridge'
import { stableFingerprint } from '@/lib/retrieval/registry/knowledge/stable'
import {
  W5_DOOR_PARITY_CHART_ID,
  W5_DOOR_PARITY_OVERLAY,
  W5_DOOR_PARITY_QUESTION,
  W5_DOOR_PARITY_SCOPE,
  W5_DOOR_PARITY_SNAPSHOT,
  w5DoorParityPlan,
  w5DoorParityToolResult,
} from '@/lib/vidhi/inquiry/__fixtures__/door_parity'

const chartId = '482012f1-710e-4a25-994a-93821f5871aa'
const scope = { intent: 'domain_assessment', domains: ['wealth'], width: 'broad', depth: 'deep', horizon: 'far', intervention: 'none', entitlement: 'native' }

function contract(): InquiryContract {
  return {
    contract_version: '1.3.0', compiler_version: '1.1.0', contract_id: 'sha256:combined',
    semantic_contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan',
    chart_id: chartId, execution_channel: 'mcp_full', question: 'wealth outlook', scope_tuple: scope,
    capability_compatibility_version: 'planner-scu-v1', capability_content_hash: 'sha256:catalog',
    chart_availability_version: null, chart_build_id: null,
    obligations: [{ obligation_id: 'obl-001', label: 'test', source: 'deterministic_floor', materiality: 'required', scu_ids: ['scu.test'], rationale: 'test', disposition: 'pending', evidence_refs: [], gap_reason: null }],
    plan_items: [{ item_id: 'item-001', obligation_ids: ['obl-001'], scu_id: 'scu.test', binding_id: 'registry:marsys://tool/L1/test', args: { offset: 0 }, depends_on: [], state: 'ready', blocked_reason: null, observation: null }],
    material_frontier: [], omission_findings: [], ai_hypotheses: [], status: 'INCOMPLETE', status_reasons: ['pending'], iteration: 0, max_iterations: 5,
  }
}

function request(body: object, headers: Record<string, string> = {}): Request {
  return new Request('http://localhost/api/mcp/inquiry', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-mcp-user': 'user-1', 'x-mcp-key-id': 'key-1', ...headers },
    body: JSON.stringify(body),
  })
}

function stateHash(value: InquiryContract): string {
  return stableFingerprint(value)
}

function primeStoredLifecycle(overrides: Record<string, unknown> = {}): InquiryContract {
  const value = contract()
  mocks.verify.mockReturnValue({
    sub: 'user-1:key-1', inquiry_id: 'inquiry-1', chart_id: chartId,
    contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan',
    catalog_hash: 'sha256:catalog', compatibility_version: 'planner-scu-v1',
    overlay_version: null, chart_build_id: null, contract_state_hash: stateHash(value),
    revision: 0, allowed_transition: 'execute', next_action_ids: ['item-001'],
    jti: 'current-jti', exp: 2_000_000_000, ...overrides,
  })
  mocks.get.mockResolvedValue({
    inquiry_id: 'inquiry-1', principal_uid: 'user-1', chart_id: chartId,
    semantic_contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan',
    capability_content_hash: 'sha256:catalog', capability_compatibility_version: 'planner-scu-v1',
    chart_overlay_version: null, chart_build_id: null,
    authorization_jsonb: value, contract_jsonb: value, status: 'INCOMPLETE', revision: 0,
    current_jti_hash: 'sha256:current-jti', expires_at: '2099-01-01T00:00:00Z',
  })
  return value
}

beforeEach(() => {
  vi.clearAllMocks()
  process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = 'inquiry-v1'
  process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = Buffer.alloc(32, 7).toString('base64url')
  delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS_KID
  delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS
  mocks.authorize.mockResolvedValue('all')
  mocks.compile.mockImplementation(() => contract())
  mocks.issue.mockImplementation((claims: Record<string, unknown>) => ({ token: 'next-token', claims: { ...claims, jti: 'next-jti', exp: 2_000_000_000 } }))
  mocks.retrieve.mockResolvedValue({ results: [{ content: '{"rows":[1],"more_available":true}' }] })
  mocks.classify.mockReturnValue('served')
  mocks.pagination.mockReturnValue({ semantics: 'offset', exhausted: false, next: 50 })
  mocks.apply.mockImplementation((value: InquiryContract) => ({ ...value, plan_items: value.plan_items.map((item) => ({ ...item, state: 'observed' })), iteration: value.iteration + 1 }))
  mocks.commitObservation.mockResolvedValue('receipt-1')
  mocks.reserve.mockResolvedValue({ status: 'acquired', reservation_hash: 'reserved:sha256:fixture', recovered: false })
  mocks.markDispatched.mockResolvedValue(undefined)
  mocks.failCloseAmbiguous.mockResolvedValue(undefined)
  mocks.overlay.mockResolvedValue({ overlay_version: null, build_id: null })
  mocks.snapshot.mockReturnValue({ content_hash: 'sha256:catalog', compatibility_version: 'planner-scu-v1', scus: [{ scu_id: 'scu.test', bindings: [{ binding_id: 'registry:marsys://tool/L1/test', kind: 'registry_capability', capability_uri: 'marsys://tool/L1/test', executable: true, execution_channels: ['mcp_full'], pagination_contract: { request_position_path: 'offset' } }] }] })
  mocks.capability.mockImplementation((uri: string) => ({ uri, mutation: false, calibration_context_only: false }))
})

describe('raw MCP inquiry route', () => {
  it('executes an overlay-granted internal registry binding through raw start, execute and finalize', async () => {
    type Stored = ReturnType<typeof primeStoredLifecycle> extends InquiryContract ? {
      inquiry_id: string; principal_uid: string; chart_id: string;
      semantic_contract_hash: string; execution_plan_hash: string;
      capability_content_hash: string; capability_compatibility_version: string;
      chart_overlay_version: string | null; chart_build_id: string | null;
      authorization_jsonb: InquiryContract; contract_jsonb: InquiryContract;
      status: InquiryContract['status']; revision: number; current_jti_hash: string; expires_at: string;
    } : never
    let stored: Stored | null = null
    let tokenCounter = 0
    const claimsByToken = new Map<string, Record<string, unknown>>()

    const internalOnlyScus = W5_DOOR_PARITY_SNAPSHOT.scus.map((scu) => ({
      ...scu,
      bindings: scu.bindings.map((binding) => ({ ...binding, execution_channels: ['platform_internal'] as const })),
    }))
    const internalSnapshot = {
      ...W5_DOOR_PARITY_SNAPSHOT,
      content_hash: stableFingerprint({ fixture: 'raw-inquiry-internal-registry', scus: internalOnlyScus }),
      scus: internalOnlyScus,
    }
    const internalOverlay = {
      ...W5_DOOR_PARITY_OVERLAY,
      catalog_content_hash: internalSnapshot.content_hash,
      overlay_version: 'sha256:raw-inquiry-internal-overlay',
    }
    expect(internalSnapshot.scus.flatMap((scu) => scu.bindings)
      .every((binding) => binding.execution_channels?.length === 1
        && binding.execution_channels[0] === 'platform_internal')).toBe(true)
    mocks.snapshot.mockReturnValue(internalSnapshot)
    mocks.overlay.mockResolvedValue(internalOverlay)
    mocks.compile.mockImplementation(() => compileInquiryContract({
      snapshot: internalSnapshot,
      overlay: internalOverlay,
      chart_id: W5_DOOR_PARITY_CHART_ID,
      question: W5_DOOR_PARITY_QUESTION,
      scope_tuple: W5_DOOR_PARITY_SCOPE,
      ai_proposal: managedPlanToAiInquiryProposal(w5DoorParityPlan()),
      execution_channel: 'mcp_full',
      presentation_transport: 'raw_mcp',
    }))
    mocks.finalize.mockImplementation((value: InquiryContract) => finalizeInquiryContract(value))
    mocks.classify.mockImplementation(classifyInquiryResult)
    mocks.pagination.mockImplementation(deriveInquiryPaginationReceipt)
    mocks.retrieve.mockImplementation((name: string, _query: unknown, args: Record<string, unknown>) =>
      Promise.resolve(w5DoorParityToolResult(name, args)))
    mocks.issue.mockImplementation((claims: Record<string, unknown>) => {
      tokenCounter += 1
      const token = `fixture-token-${tokenCounter}`
      const issuedClaims = { ...claims, jti: `fixture-jti-${tokenCounter}`, exp: 2_000_000_000 }
      claimsByToken.set(token, issuedClaims)
      return { token, claims: issuedClaims }
    })
    mocks.verify.mockImplementation((token: string) => claimsByToken.get(token))
    mocks.create.mockImplementation((args: {
      inquiry_id: string; principal_uid: string; contract: InquiryContract;
      jti_hash: string; expires_at: string;
    }) => {
      stored = {
        inquiry_id: args.inquiry_id, principal_uid: args.principal_uid, chart_id: args.contract.chart_id,
        semantic_contract_hash: args.contract.semantic_contract_hash,
        execution_plan_hash: args.contract.execution_plan_hash,
        capability_content_hash: args.contract.capability_content_hash,
        capability_compatibility_version: args.contract.capability_compatibility_version,
        chart_overlay_version: args.contract.chart_availability_version,
        chart_build_id: args.contract.chart_build_id,
        authorization_jsonb: args.contract, contract_jsonb: args.contract,
        status: args.contract.status, revision: 0, current_jti_hash: args.jti_hash,
        expires_at: args.expires_at,
      }
      return Promise.resolve(stored)
    })
    mocks.get.mockImplementation(() => Promise.resolve(stored))
    mocks.reserve.mockImplementation((args: { reservation_hash: string }) => {
      if (!stored) throw new Error('missing fixture lifecycle')
      stored.current_jti_hash = args.reservation_hash
      return Promise.resolve({ status: 'acquired', reservation_hash: args.reservation_hash, recovered: false })
    })
    mocks.commitObservation.mockImplementation((args: {
      next_jti_hash: string; contract: InquiryContract;
    }) => {
      if (!stored) throw new Error('missing fixture lifecycle')
      stored = { ...stored, contract_jsonb: args.contract, status: args.contract.status,
        revision: stored.revision + 1, current_jti_hash: args.next_jti_hash }
      return Promise.resolve(`fixture-receipt-${stored.revision}`)
    })
    mocks.commitFinalization.mockImplementation((args: { contract: InquiryContract }) => {
      if (!stored) throw new Error('missing fixture lifecycle')
      stored = { ...stored, contract_jsonb: args.contract, status: args.contract.status,
        revision: stored.revision + 1, current_jti_hash: 'terminal' }
      return Promise.resolve()
    })

    const start = await POST(request({
      action: 'start', chart_id: W5_DOOR_PARITY_CHART_ID,
      question: W5_DOOR_PARITY_QUESTION, scope_tuple: W5_DOOR_PARITY_SCOPE,
      ai_proposal: managedPlanToAiInquiryProposal(w5DoorParityPlan()),
    }))
    let body = await start.json() as { lifecycle_token: string; next_action_ids: string[]; inquiry_door_parity?: unknown }
    expect(body.next_action_ids.length).toBeGreaterThan(0)
    while (body.next_action_ids.length > 0) {
      const executed = await POST(request({
        action: 'execute', lifecycle_token: body.lifecycle_token, action_id: body.next_action_ids[0],
      }))
      const executedBody = await executed.json()
      expect(executed.status).toBe(200)
      body = executedBody
    }
    const finalized = await POST(request({ action: 'finalize', lifecycle_token: body.lifecycle_token }))
    expect(finalized.status).toBe(200)
    // The fixture deliberately keeps required paginated evidence open. A
    // truthful lifecycle must expose the cap as BLOCKED, never relabel it as
    // resumable incompleteness or completion.
    const finalizedBody = await finalized.json()
    expect(finalizedBody).toMatchObject({ closure: { status: 'BLOCKED' } })
    expect(finalizedBody.closure.status_reasons).toEqual(expect.arrayContaining([
      expect.stringContaining('material frontier items open'),
      expect.stringContaining('iteration cap reached before material frontier closure'),
    ]))
    expect(finalizedBody.closure.residual_frontier).toEqual(expect.arrayContaining([
      expect.objectContaining({ materiality: 'required', disposition: 'open' }),
    ]))
    expect(finalizedBody.closure.status_reasons.some((reason: string) =>
      /(?:internal transit plan|argument resolution receipt)/i.test(reason))).toBe(false)
    expect(mocks.retrieve).toHaveBeenCalled()
  })

  it('requires both principal headers', async () => {
    const response = await POST(request({ action: 'start', chart_id: chartId, question: 'wealth', scope_tuple: scope }, { 'x-mcp-key-id': '' }))
    expect(response.status).toBe(401)
    expect(await response.json()).toMatchObject({ ok: false })
  })

  it.each([
    ['an MCP-native alias', {
      binding_id: 'registry:marsys://tool/L1/test', kind: 'mcp_native',
      capability_uri: 'mcp://tool/ganita_chart_facts_get', executable: true,
      execution_channels: ['mcp_full'],
    }],
    ['a mutation-capable registry descriptor', {
      binding_id: 'registry:marsys://tool/L1/test', kind: 'registry_capability',
      capability_uri: 'marsys://tool/L1/test', executable: true,
      execution_channels: ['platform_internal'],
    }],
  ] as const)('rejects %s before raw dispatch', async (_label, binding) => {
    primeStoredLifecycle()
    mocks.snapshot.mockReturnValue({
      content_hash: 'sha256:catalog', compatibility_version: 'planner-scu-v1',
      scus: [{ scu_id: 'scu.test', bindings: [binding] }],
    })
    if (_label === 'a mutation-capable registry descriptor') {
      mocks.capability.mockReturnValue({
        uri: 'marsys://tool/L1/test', mutation: true, calibration_context_only: false,
      })
    }

    const response = await POST(request({ action: 'execute', lifecycle_token: 'current-token', action_id: 'item-001' }))

    expect(response.status).toBe(409)
    expect(await response.json()).toEqual({ ok: false, error: 'INQUIRY_BINDING_UNAVAILABLE' })
    expect(mocks.reserve).not.toHaveBeenCalled()
    expect(mocks.retrieve).not.toHaveBeenCalled()
  })

  it('fails closed before authorization or compilation when signing configuration is absent', async () => {
    delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT
    const logged = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    const response = await POST(request({ action: 'start', chart_id: chartId, question: 'wealth', scope_tuple: scope }))
    expect(response.status).toBe(500)
    expect(await response.json()).toMatchObject({ ok: false, error: 'INQUIRY_REQUEST_FAILED' })
    expect(mocks.authorize).not.toHaveBeenCalled()
    expect(mocks.compile).not.toHaveBeenCalled()
    expect(logged).toHaveBeenCalledWith('[mcp:inquiry] request failed', expect.objectContaining({
      error: expect.objectContaining({ message: 'INQUIRY_SIGNING_KEY_INVALID' }),
    }))
    logged.mockRestore()
  })

  it('binds a new lifecycle token to user and API-key identity', async () => {
    const response = await POST(request({ action: 'start', chart_id: chartId, question: 'wealth', scope_tuple: scope }))
    expect(response.status).toBe(200)
    expect(mocks.issue).toHaveBeenCalledWith(expect.objectContaining({ sub: 'user-1:key-1', allowed_transition: 'execute', next_action_ids: ['item-001'] }), expect.objectContaining({ current: expect.objectContaining({ kid: 'inquiry-v1' }) }))
    expect(mocks.create).toHaveBeenCalledWith(expect.objectContaining({ principal_uid: 'user-1', jti_hash: 'sha256:next-jti' }))
  })

  it('admits a canonical compiler scope at the lifecycle boundary', async () => {
    const canonicalScope = {
      intent: 'wealth_deepdive', domains: ['wealth'], width: 'panoramic', depth: 'deepdive',
      horizon: 'multi_year', intervention: false, entitlement: 'native',
    }
    const response = await POST(request({ action: 'start', chart_id: chartId, question: 'wealth', scope_tuple: canonicalScope }))
    expect(response.status).toBe(200)
    expect(mocks.compile).toHaveBeenCalledWith(expect.objectContaining({ scope_tuple: canonicalScope }))
  })

  it('rejects revoked chart access before compiling or loading lifecycle state', async () => {
    mocks.authorize.mockResolvedValue('deny')
    const response = await POST(request({ action: 'start', chart_id: chartId, question: 'wealth', scope_tuple: scope }))
    expect(response.status).toBe(401)
    expect(await response.json()).toEqual({ ok: false, error: 'AUTHZ_DENIED' })
    expect(mocks.compile).not.toHaveBeenCalled()
    expect(mocks.create).not.toHaveBeenCalled()
  })

  it.each([
    ['a different API key', { 'x-mcp-key-id': 'key-2' }],
    ['a different principal', { 'x-mcp-user': 'user-2' }],
  ])('binds token verification to both user and API-key identity: rejects %s', async (_label, headers) => {
    mocks.verify.mockImplementation((_token, _key, subject) => {
      if (subject !== 'user-1:key-1') throw new Error('INQUIRY_TOKEN_WRONG_SUBJECT')
      return {}
    })
    const response = await POST(request(
      { action: 'finalize', lifecycle_token: 'current-token' },
      headers,
    ))
    expect(response.status).toBe(401)
    expect(await response.json()).toEqual({ ok: false, error: 'INQUIRY_TOKEN_WRONG_SUBJECT' })
    expect(mocks.get).not.toHaveBeenCalled()
  })

  it('keeps the same action authorized until a verified next page is exhausted', async () => {
    primeStoredLifecycle()
    const response = await POST(request({ action: 'execute', lifecycle_token: 'current-token', action_id: 'item-001' }))
    expect(response.status).toBe(200)
    expect(mocks.issue).toHaveBeenCalledWith(expect.objectContaining({ allowed_transition: 'execute', next_action_ids: ['item-001'] }), expect.objectContaining({ current: expect.objectContaining({ kid: 'inquiry-v1' }) }))
    expect(await response.json()).toMatchObject({ next_action_ids: ['item-001'], pagination: { next: 50 } })
  })

  it('rejects successor creation without a terminal evidence-admitted frontier', async () => {
    primeStoredLifecycle({ allowed_transition: 'finalize', next_action_ids: [] })
    const result = await POST(request({ action: 'continue', lifecycle_token: 'current-token' }))
    expect(result.status).toBe(409)
    expect(await result.json()).toEqual({ ok: false, error: 'INQUIRY_SUCCESSOR_NOT_AUTHORIZED' })
    expect(mocks.createSuccessor).not.toHaveBeenCalled()
  })

  it('atomically creates a fresh successor from a capped, served material frontier', async () => {
    mocks.overlay.mockResolvedValue({
      chart_id: chartId, overlay_version: null, capability_compatibility_version: 'planner-scu-v1',
      catalog_content_hash: 'sha256:catalog', build_id: null, availability: [],
    })
    mocks.snapshot.mockReturnValue({
      content_hash: 'sha256:catalog', compatibility_version: 'planner-scu-v1',
      scus: [{ scu_id: 'scu.test', bindings: [{
        binding_id: 'registry:marsys://tool/L1/test', kind: 'registry_capability',
        capability_uri: 'marsys://tool/L1/test', executable: true, execution_channels: ['mcp_full'],
        relation: 'primary', input_contract: {},
      }] }],
    })
    const initial = { ...contract(), max_iterations: 1 }
    const parent = recordInquiryExecution(initial, {
      item_id: 'item-001', disposition: 'served', evidence_refs: ['raw:parent-evidence'],
      pagination: { semantics: 'offset', exhausted: false, next: 50 },
    })
    mocks.verify.mockReturnValue({
      sub: 'user-1:key-1', inquiry_id: 'inquiry-1', chart_id: chartId,
      contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan',
      catalog_hash: 'sha256:catalog', compatibility_version: 'planner-scu-v1',
      overlay_version: null, chart_build_id: null, contract_state_hash: stateHash(parent),
      revision: 0, allowed_transition: 'finalize', next_action_ids: [], jti: 'current-jti', exp: 2_000_000_000,
    })
    mocks.get.mockResolvedValue({
      inquiry_id: 'inquiry-1', parent_inquiry_id: null, principal_uid: 'user-1', chart_id: chartId,
      semantic_contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan',
      capability_content_hash: 'sha256:catalog', capability_compatibility_version: 'planner-scu-v1',
      chart_overlay_version: null, chart_build_id: null, authorization_jsonb: parent, contract_jsonb: parent,
      status: 'INCOMPLETE', revision: 0, current_jti_hash: 'sha256:current-jti', expires_at: '2099-01-01T00:00:00Z',
    })

    const result = await POST(request({ action: 'continue', lifecycle_token: 'current-token' }))
    expect(result.status).toBe(200)
    expect(await result.json()).toMatchObject({ ok: true, parent_inquiry_id: 'inquiry-1', lifecycle_token: 'next-token' })
    expect(mocks.createSuccessor).toHaveBeenCalledWith(expect.objectContaining({
      parent: expect.objectContaining({ inquiry_id: 'inquiry-1' }),
      parent_final_contract: expect.objectContaining({ status: 'BLOCKED' }),
      contract: expect.objectContaining({ successor: expect.objectContaining({ parent_inquiry_id: 'inquiry-1' }) }),
    }))
  })

  it.each([
    ['first', false, 'middle'],
    ['middle', false, 'final'],
    ['final', true, null],
  ] as const)('authorizes a nested pagination path for the %s page without changing sibling arguments', async (cursor, exhausted, next) => {
    const base = contract()
    const authorized: InquiryContract = {
      ...base,
      plan_items: base.plan_items.map((item) => ({
        ...item,
        args: { filters: { cursor: 'authorized', limit: 25 }, region: 'all' },
      })),
    }
    const current: InquiryContract = {
      ...authorized,
      plan_items: authorized.plan_items.map((item) => ({
        ...item,
        args: { filters: { cursor, limit: 25 }, region: 'all' },
      })),
    }
    mocks.verify.mockReturnValue({
      sub: 'user-1:key-1', inquiry_id: 'inquiry-1', chart_id: chartId,
      contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan',
      catalog_hash: 'sha256:catalog', compatibility_version: 'planner-scu-v1',
      overlay_version: null, chart_build_id: null, contract_state_hash: stateHash(current),
      revision: 0, allowed_transition: 'execute', next_action_ids: ['item-001'],
      jti: 'current-jti', exp: 2_000_000_000,
    })
    mocks.get.mockResolvedValue({
      inquiry_id: 'inquiry-1', principal_uid: 'user-1', chart_id: chartId,
      semantic_contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan',
      capability_content_hash: 'sha256:catalog', capability_compatibility_version: 'planner-scu-v1',
      chart_overlay_version: null, chart_build_id: null,
      authorization_jsonb: authorized, contract_jsonb: current, status: 'INCOMPLETE', revision: 0,
      current_jti_hash: 'sha256:current-jti', expires_at: '2099-01-01T00:00:00Z',
    })
    mocks.snapshot.mockReturnValue({
      content_hash: 'sha256:catalog', compatibility_version: 'planner-scu-v1',
      scus: [{ scu_id: 'scu.test', bindings: [{
        binding_id: 'registry:marsys://tool/L1/test', kind: 'registry_capability', capability_uri: 'marsys://tool/L1/test', executable: true,
        execution_channels: ['mcp_full'], pagination_contract: { request_position_path: 'filters.cursor' },
      }] }],
    })
    mocks.pagination.mockReturnValue({ semantics: 'cursor', exhausted, next })

    const result = await POST(request({ action: 'execute', lifecycle_token: 'current-token', action_id: 'item-001' }))

    expect(result.status).toBe(200)
    expect(mocks.retrieve).toHaveBeenCalledWith(
      'marsys://tool/L1/test',
      expect.any(Object),
      { filters: { cursor, limit: 25 }, region: 'all' },
    )
  })

  it('rejects a sibling mutation beside an otherwise authorized nested pagination value', async () => {
    const base = contract()
    const authorized: InquiryContract = {
      ...base,
      plan_items: base.plan_items.map((item) => ({
        ...item,
        args: { filters: { cursor: 'authorized', limit: 25 }, region: 'all' },
      })),
    }
    const forged: InquiryContract = {
      ...authorized,
      plan_items: authorized.plan_items.map((item) => ({
        ...item,
        args: { filters: { cursor: 'middle', limit: 500 }, region: 'all' },
      })),
    }
    mocks.verify.mockReturnValue({
      sub: 'user-1:key-1', inquiry_id: 'inquiry-1', chart_id: chartId,
      contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan',
      catalog_hash: 'sha256:catalog', compatibility_version: 'planner-scu-v1',
      overlay_version: null, chart_build_id: null, contract_state_hash: stateHash(forged),
      revision: 0, allowed_transition: 'execute', next_action_ids: ['item-001'],
      jti: 'current-jti', exp: 2_000_000_000,
    })
    mocks.get.mockResolvedValue({
      inquiry_id: 'inquiry-1', principal_uid: 'user-1', chart_id: chartId,
      semantic_contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan',
      capability_content_hash: 'sha256:catalog', capability_compatibility_version: 'planner-scu-v1',
      chart_overlay_version: null, chart_build_id: null,
      authorization_jsonb: authorized, contract_jsonb: forged, status: 'INCOMPLETE', revision: 0,
      current_jti_hash: 'sha256:current-jti', expires_at: '2099-01-01T00:00:00Z',
    })
    mocks.snapshot.mockReturnValue({
      content_hash: 'sha256:catalog', compatibility_version: 'planner-scu-v1',
      scus: [{ scu_id: 'scu.test', bindings: [{
        binding_id: 'registry:marsys://tool/L1/test', kind: 'registry_capability', capability_uri: 'marsys://tool/L1/test', executable: true,
        execution_channels: ['mcp_full'], pagination_contract: { request_position_path: 'filters.cursor' },
      }] }],
    })

    const result = await POST(request({ action: 'execute', lifecycle_token: 'current-token', action_id: 'item-001' }))

    expect(result.status).toBe(409)
    expect(await result.json()).toEqual({ ok: false, error: 'INQUIRY_ARGS_NOT_AUTHORIZED' })
    expect(mocks.reserve).not.toHaveBeenCalled()
    expect(mocks.retrieve).not.toHaveBeenCalled()
  })

  it('issues a finalization transition when every plan item is blocked', async () => {
    mocks.compile.mockImplementationOnce(() => ({ ...contract(), plan_items: [] }))
    const response = await POST(request({ action: 'start', chart_id: chartId, question: 'wealth', scope_tuple: scope }))
    expect(response.status).toBe(200)
    expect(mocks.issue).toHaveBeenCalledWith(expect.objectContaining({ allowed_transition: 'finalize', next_action_ids: [] }), expect.objectContaining({ current: expect.objectContaining({ kid: 'inquiry-v1' }) }))
  })

  it('rejects a token-authorized lifecycle when the pinned knowledge snapshot changed', async () => {
    primeStoredLifecycle()
    mocks.snapshot.mockReturnValueOnce({ content_hash: 'sha256:changed', compatibility_version: 'planner-scu-v1', scus: [] })
    const response = await POST(request({ action: 'execute', lifecycle_token: 'current-token', action_id: 'item-001' }))
    expect(response.status).toBe(409)
    expect(await response.json()).toEqual({ ok: false, error: 'CAPABILITY_KNOWLEDGE_STALE' })
    expect(mocks.reserve).not.toHaveBeenCalled()
    expect(mocks.retrieve).not.toHaveBeenCalled()
  })

  it('rejects an action outside the signed next-action set before reservation', async () => {
    primeStoredLifecycle()
    const response = await POST(request({ action: 'execute', lifecycle_token: 'current-token', action_id: 'item-999' }))
    expect(response.status).toBe(409)
    expect(await response.json()).toEqual({ ok: false, error: 'INQUIRY_ACTION_NOT_AUTHORIZED' })
    expect(mocks.reserve).not.toHaveBeenCalled()
    expect(mocks.retrieve).not.toHaveBeenCalled()
  })

  it('records a failed dispatch as failed evidence without completing the obligation', async () => {
    primeStoredLifecycle()
    mocks.retrieve.mockRejectedValueOnce(new Error('retriever unavailable'))
    mocks.classify.mockReturnValueOnce('failed')
    const response = await POST(request({ action: 'execute', lifecycle_token: 'current-token', action_id: 'item-001' }))
    expect(response.status).toBe(200)
    expect(await response.json()).toMatchObject({ ok: true, disposition: 'failed' })
    expect(mocks.commitObservation).toHaveBeenCalledWith(expect.objectContaining({
      evidence: expect.objectContaining({ disposition: 'failed' }),
    }))
  })

  it('consumes a replayed action before dispatch so only one concurrent request executes', async () => {
    const value = contract()
    mocks.verify.mockReturnValue({
      sub: 'user-1:key-1', inquiry_id: 'inquiry-1', chart_id: chartId, contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan',
      catalog_hash: 'sha256:catalog', compatibility_version: 'planner-scu-v1', overlay_version: null, chart_build_id: null,
      contract_state_hash: stateHash(value),
      revision: 0, allowed_transition: 'execute', next_action_ids: ['item-001'], jti: 'current-jti', exp: 2_000_000_000,
    })
    mocks.get.mockResolvedValue({
      inquiry_id: 'inquiry-1', principal_uid: 'user-1', chart_id: chartId,
      semantic_contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan', capability_content_hash: 'sha256:catalog',
      capability_compatibility_version: 'planner-scu-v1', chart_overlay_version: null, chart_build_id: null,
      authorization_jsonb: value, contract_jsonb: value, status: 'INCOMPLETE', revision: 0, current_jti_hash: 'sha256:current-jti', expires_at: '2099-01-01T00:00:00Z',
    })
    mocks.reserve.mockResolvedValueOnce({ status: 'acquired', reservation_hash: 'reserved:sha256:first', recovered: false })
      .mockRejectedValueOnce(new Error('INQUIRY_TOKEN_REPLAYED_OR_STALE'))
    const [first, second] = await Promise.all([
      POST(request({ action: 'execute', lifecycle_token: 'current-token', action_id: 'item-001' })),
      POST(request({ action: 'execute', lifecycle_token: 'current-token', action_id: 'item-001' })),
    ])
    expect([first.status, second.status].sort()).toEqual([200, 409])
    expect(mocks.retrieve).toHaveBeenCalledTimes(1)
  })

  it('persists dispatched before invoking the tool', async () => {
    primeStoredLifecycle()
    const order: string[] = []
    mocks.markDispatched.mockImplementation(async () => { order.push('dispatched') })
    mocks.retrieve.mockImplementation(async () => {
      order.push('retrieve')
      return { results: [{ content: '{"rows":[1]}' }] }
    })
    mocks.commitObservation.mockImplementation(async () => {
      order.push('committed')
      return 'receipt-1'
    })

    const response = await POST(request({ action: 'execute', lifecycle_token: 'current-token', action_id: 'item-001' }))
    expect(response.status).toBe(200)
    expect(order).toEqual(['dispatched', 'retrieve', 'committed'])
    expect(mocks.markDispatched).toHaveBeenCalledWith(expect.objectContaining({ plan_item_id: 'item-001' }))
  })

  it('fails closed without redispatch when a prior dispatch outcome is ambiguous', async () => {
    const value = primeStoredLifecycle()
    mocks.get.mockResolvedValueOnce({
      ...(await mocks.get()),
      current_jti_hash: 'reserved:sha256:lost-process',
      contract_jsonb: value,
    })
    mocks.reserve.mockResolvedValueOnce({ status: 'ambiguous', reservation_hash: 'reserved:sha256:lost-process' })

    const response = await POST(request({ action: 'execute', lifecycle_token: 'current-token', action_id: 'item-001' }))
    expect(response.status).toBe(409)
    expect(await response.json()).toMatchObject({
      error: 'INQUIRY_DISPATCH_OUTCOME_AMBIGUOUS',
      contract: { status: 'BLOCKED' },
    })
    expect(mocks.retrieve).not.toHaveBeenCalled()
    expect(mocks.markDispatched).not.toHaveBeenCalled()
    expect(mocks.failCloseAmbiguous).toHaveBeenCalledWith(expect.objectContaining({
      expected_source_jti_hash: 'sha256:current-jti',
      plan_item_id: 'item-001',
      contract: expect.objectContaining({ status: 'BLOCKED' }),
    }))
  })

  it('leaves a live overlapping dispatch in progress without fail-closing it', async () => {
    const value = primeStoredLifecycle()
    mocks.get.mockResolvedValueOnce({
      ...(await mocks.get()),
      current_jti_hash: 'reserved:sha256:active-process',
      contract_jsonb: value,
    })
    mocks.reserve.mockResolvedValueOnce({
      status: 'in_progress',
      reservation_hash: 'reserved:sha256:active-process',
      retry_after_seconds: 42,
    })

    const response = await POST(request({ action: 'execute', lifecycle_token: 'current-token', action_id: 'item-001' }))
    expect(response.status).toBe(409)
    expect(await response.json()).toEqual({
      ok: false,
      error: 'INQUIRY_ACTION_IN_PROGRESS',
      retry_after_seconds: 42,
    })
    expect(mocks.retrieve).not.toHaveBeenCalled()
    expect(mocks.failCloseAmbiguous).not.toHaveBeenCalled()
  })

  it('rejects mutable contract progress not authenticated by the signed token', async () => {
    const authorized = contract()
    const forged = { ...authorized, status: 'COMPLETE' as const, material_frontier: [], obligations: authorized.obligations.map((item) => ({ ...item, disposition: 'served' as const })) }
    mocks.verify.mockReturnValue({
      sub: 'user-1:key-1', inquiry_id: 'inquiry-1', chart_id: chartId,
      contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan', contract_state_hash: stateHash(authorized),
      catalog_hash: 'sha256:catalog', compatibility_version: 'planner-scu-v1', overlay_version: null, chart_build_id: null,
      revision: 0, allowed_transition: 'finalize', next_action_ids: [], jti: 'current-jti', exp: 2_000_000_000,
    })
    mocks.get.mockResolvedValue({
      inquiry_id: 'inquiry-1', principal_uid: 'user-1', chart_id: chartId,
      semantic_contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan', capability_content_hash: 'sha256:catalog',
      capability_compatibility_version: 'planner-scu-v1', chart_overlay_version: null, chart_build_id: null,
      authorization_jsonb: authorized, contract_jsonb: forged, status: 'INCOMPLETE', revision: 0,
      current_jti_hash: 'sha256:current-jti', expires_at: '2099-01-01T00:00:00Z',
    })
    const response = await POST(request({ action: 'finalize', lifecycle_token: 'current-token' }))
    expect(response.status).toBe(409)
    expect(mocks.commitFinalization).not.toHaveBeenCalled()
  })

  it('fails closed and terminates the lifecycle when the chart overlay changes during dispatch', async () => {
    const value = contract()
    mocks.verify.mockReturnValue({
      sub: 'user-1:key-1', inquiry_id: 'inquiry-1', chart_id: chartId,
      contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan', contract_state_hash: stateHash(value),
      catalog_hash: 'sha256:catalog', compatibility_version: 'planner-scu-v1', overlay_version: null, chart_build_id: null,
      revision: 0, allowed_transition: 'execute', next_action_ids: ['item-001'], jti: 'current-jti', exp: 2_000_000_000,
    })
    mocks.get.mockResolvedValue({
      inquiry_id: 'inquiry-1', principal_uid: 'user-1', chart_id: chartId,
      semantic_contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan', capability_content_hash: 'sha256:catalog',
      capability_compatibility_version: 'planner-scu-v1', chart_overlay_version: null, chart_build_id: null,
      authorization_jsonb: value, contract_jsonb: value, status: 'INCOMPLETE', revision: 0,
      current_jti_hash: 'sha256:current-jti', expires_at: '2099-01-01T00:00:00Z',
    })
    mocks.overlay.mockResolvedValueOnce({ overlay_version: null, build_id: null })
      .mockResolvedValueOnce({ overlay_version: 'sha256:new-overlay', build_id: 'build-2' })

    const response = await POST(request({ action: 'execute', lifecycle_token: 'current-token', action_id: 'item-001' }))
    expect(response.status).toBe(409)
    expect(await response.json()).toMatchObject({ error: 'CAPABILITY_OVERLAY_CHANGED' })
    expect(mocks.commitFinalization).toHaveBeenCalledTimes(1)
    expect(mocks.commitObservation).not.toHaveBeenCalled()
  })

  it('returns a terminal blocked closure without relabeling it complete', async () => {
    const value = primeStoredLifecycle({ allowed_transition: 'finalize', next_action_ids: [] })
    const blocked = { ...value, status: 'BLOCKED' as const, status_reasons: ['required_obligation_failed'] }
    mocks.finalize.mockReturnValue(blocked)
    const response = await POST(request({ action: 'finalize', lifecycle_token: 'current-token' }))
    expect(response.status).toBe(200)
    expect(await response.json()).toMatchObject({
      ok: true,
      contract: blocked,
      closure: { status: 'BLOCKED', status_reasons: ['required_obligation_failed'] },
      inquiry_door_parity: {
        parity_version: 'inquiry-door-parity-v1',
        semantic_contract_hash: 'sha256:contract',
        status: 'BLOCKED',
      },
    })
    expect(mocks.commitFinalization).toHaveBeenCalledWith(expect.objectContaining({ contract: blocked }))
  })
})

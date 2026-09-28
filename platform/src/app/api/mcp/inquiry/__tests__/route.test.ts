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
import { readBoundedRequestBody } from '../bounded_body'
import { compileInquiryContract, finalizeInquiryContract, inquiryAuthorizationHashes as realAuthorizationHashes, recordInquiryExecution } from '@/lib/vidhi/inquiry/compiler'
import { classifyInquiryResult, deriveInquiryPaginationReceipt } from '@/lib/vidhi/inquiry/pagination'
import { managedPlanToAiInquiryProposal } from '@/lib/vidhi/inquiry/managed_bridge'
import { stableFingerprint } from '@/lib/retrieval/registry/knowledge/stable'
import {
  buildStructuredResponseAccountability,
  inquiryCitationMarker,
  inquiryFindingCitationHandles,
} from '@/lib/vidhi/inquiry/response_accountability'
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

  it('commits the hash of the JSON the client receives, not of in-memory values that do not survive the wire', async () => {
    primeStoredLifecycle()
    const inMemory = { results: [{ content: 'served', optional: undefined }], observed: new Date(0) }
    mocks.retrieve.mockResolvedValueOnce(inMemory)
    const response = await POST(request({ action: 'execute', lifecycle_token: 'current-token', action_id: 'item-001' }))
    expect(response.status).toBe(200)
    const received = (await response.json()).raw_result
    const wireHash = stableFingerprint(received)
    expect(wireHash).not.toBe(stableFingerprint(inMemory))
    expect(mocks.commitObservation).toHaveBeenCalledWith(expect.objectContaining({
      evidence: expect.objectContaining({ raw_result_hash: wireHash }),
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

describe('raw MCP inquiry certification (RC-6.4)', () => {
  const payload = { rows: [{ fact_key: 'wealth_signal', value: 'served evidence' }] }
  const evidenceRef = `raw:${stableFingerprint(payload)}`

  function finalized(status: InquiryContract['status'] = 'COMPLETE'): InquiryContract {
    const value = contract()
    const observed: InquiryContract = {
      ...value,
      status,
      status_reasons: status === 'COMPLETE' ? [] : ['required_obligation_failed'],
      iteration: 1,
      obligations: value.obligations.map((obligation) => ({ ...obligation, disposition: 'served' as const, evidence_refs: [evidenceRef] })),
      plan_items: value.plan_items.map((item) => ({
        ...item,
        state: 'observed' as const,
        observation: { item_id: item.item_id, disposition: 'served' as const, evidence_refs: [evidenceRef], gap_reason: null },
      })) as InquiryContract['plan_items'],
    }
    // Real authorization hashes: the server-side envelope re-derives them from content.
    return { ...observed, ...realAuthorizationHashes(observed) }
  }

  function primeTerminal(final: InquiryContract, overrides: Record<string, unknown> = {}, rowOverrides: Record<string, unknown> = {}) {
    primeStoredLifecycle({
      revision: 0, allowed_transition: 'finalize', next_action_ids: [],
      contract_hash: final.semantic_contract_hash, execution_plan_hash: final.execution_plan_hash, ...overrides,
    })
    mocks.get.mockResolvedValue({
      inquiry_id: 'inquiry-1', principal_uid: 'user-1', chart_id: chartId,
      semantic_contract_hash: final.semantic_contract_hash, execution_plan_hash: final.execution_plan_hash,
      capability_content_hash: 'sha256:catalog', capability_compatibility_version: 'planner-scu-v1',
      chart_overlay_version: null, chart_build_id: null,
      authorization_jsonb: final, contract_jsonb: final, status: final.status, revision: 1,
      current_jti_hash: 'terminal', expires_at: '2099-01-01T00:00:00Z', ...rowOverrides,
    })
  }

  function citingAnswer(final: InquiryContract): string {
    const probe = buildStructuredResponseAccountability(final, { evidence_payloads: [payload], knowledge_snapshot: mocks.snapshot() })
    const handles = [...inquiryFindingCitationHandles(probe.fact_register).values()]
    expect(handles.length).toBeGreaterThan(0)
    return `The served wealth evidence supports the reading ${handles.map(inquiryCitationMarker).join(' ')}.`
  }

  it('certifies a finalized answer server-side from committed evidence, read-only', async () => {
    const final = finalized()
    primeTerminal(final)
    const text = citingAnswer(final)
    const res = await POST(request({ action: 'certify', lifecycle_token: 'final-token', response_text: text, evidence_payloads: [payload] }))
    expect(res.status).toBe(200)
    const json = await res.json()
    expect(json).toMatchObject({
      ok: true, inquiry_id: 'inquiry-1', coverage_certified: true,
      certification: { contract_id: final.contract_id, response_text_hash: stableFingerprint(text), missing_committed_evidence: [] },
    })
    expect(json.certification.coverage_receipt_hash).toBe(json.response_accountability.response_coverage_receipt.receipt_hash)
    expect(mocks.reserve).not.toHaveBeenCalled()
    expect(mocks.commitObservation).not.toHaveBeenCalled()
    expect(mocks.commitFinalization).not.toHaveBeenCalled()
    expect(mocks.retrieve).not.toHaveBeenCalled()
  })

  it('does not certify complete when committed evidence is withheld or the answer cites nothing', async () => {
    const final = finalized()
    primeTerminal(final)
    const withheld = await POST(request({ action: 'certify', lifecycle_token: 'final-token', response_text: citingAnswer(final), evidence_payloads: [] }))
    expect(withheld.status).toBe(200)
    expect(await withheld.json()).toMatchObject({
      coverage_certified: false,
      certification: { missing_committed_evidence: [stableFingerprint(payload)] },
    })
    const uncited = await POST(request({ action: 'certify', lifecycle_token: 'final-token', response_text: 'A confident answer with no citations.', evidence_payloads: [payload] }))
    expect(await uncited.json()).toMatchObject({ coverage_certified: false })
  })

  it('certifies a BLOCKED closure honestly, never as complete', async () => {
    const final = finalized('BLOCKED')
    primeTerminal(final, { allowed_transition: 'execute', next_action_ids: ['item-001'] })
    const res = await POST(request({ action: 'certify', lifecycle_token: 'final-token', response_text: citingAnswer(final), evidence_payloads: [payload] }))
    expect(res.status).toBe(200)
    expect(await res.json()).toMatchObject({ ok: true, coverage_certified: false })
  })

  it('does not certify a span that carries citation markers but no interpretation of its own', async () => {
    const final = finalized()
    primeTerminal(final)
    const markers = citingAnswer(final).match(/\[\[F[0-9]+\]\]/g)!.join(' ')
    const res = await POST(request({ action: 'certify', lifecycle_token: 'final-token', response_text: markers, evidence_payloads: [payload] }))
    expect(await res.json()).toMatchObject({
      coverage_certified: false,
      certification: { attests: 'evidence_coverage', uncertified_reasons: ['citation_without_interpretation'] },
    })
  })

  it('bounds certification work: duplicate evidence, citation floods and oversized bodies', async () => {
    primeTerminal(finalized())
    const duplicate = await POST(request({ action: 'certify', lifecycle_token: 'final-token', response_text: 'answer', evidence_payloads: [payload, payload] }))
    expect(duplicate.status).toBe(400)
    expect(await duplicate.json()).toMatchObject({ error: 'INQUIRY_CERTIFICATION_EVIDENCE_DUPLICATED' })

    const flood = Array.from({ length: 257 }, (_, index) => `Span ${index} interprets the evidence [[F1]]`).join('\n\n')
    const flooded = await POST(request({ action: 'certify', lifecycle_token: 'final-token', response_text: flood, evidence_payloads: [payload] }))
    expect(flooded.status).toBe(400)
    expect(await flooded.json()).toMatchObject({ error: 'INQUIRY_CERTIFICATION_TOO_MANY_CITATIONS' })

    mocks.verify.mockClear()
    const oversized = await POST(request(
      { action: 'certify', lifecycle_token: 'final-token', response_text: 'answer', evidence_payloads: [] },
      { 'content-length': String(64 * 512 * 1024 + 2 * 1024 * 1024) },
    ))
    expect(oversized.status).toBe(413)
    expect(mocks.verify).not.toHaveBeenCalled()
  })

  // R3 boundary ("actual certify-request byte limit"): Content-Length is only an early-
  // rejection optimization for an honest, accurately-declared oversized value (covered
  // above) — it must never be the enforcement mechanism itself, since it can be omitted or
  // understated while the actual body sent is still oversized. These two prove the real
  // limit (readBoundedRequestBody, enforced against bytes actually received) still fires
  // when the header lies or is absent.
  const REAL_MAX_REQUEST_BYTES = 64 * 512 * 1024 + 1024 * 1024
  function oversizedChunkedBody(totalBytes: number): ReadableStream<Uint8Array> {
    const chunkSize = 8 * 1024 * 1024
    let sent = 0
    return new ReadableStream<Uint8Array>({
      pull(controller) {
        if (sent >= totalBytes) { controller.close(); return }
        const size = Math.min(chunkSize, totalBytes - sent)
        controller.enqueue(new Uint8Array(size).fill(120)) // 'x'
        sent += size
      },
    })
  }

  it('rejects an oversized ACTUAL body even when Content-Length is omitted entirely', async () => {
    mocks.verify.mockClear()
    const req = new Request('http://localhost/api/mcp/inquiry', {
      method: 'POST',
      headers: { 'content-type': 'application/json', 'x-mcp-user': 'user-1', 'x-mcp-key-id': 'key-1' },
      body: oversizedChunkedBody(REAL_MAX_REQUEST_BYTES + 1024 * 1024),
      duplex: 'half',
    } as RequestInit)
    const res = await POST(req)
    expect(res.status).toBe(413)
    expect(mocks.verify).not.toHaveBeenCalled()
  })

  it('rejects an oversized ACTUAL body even when Content-Length understates it', async () => {
    mocks.verify.mockClear()
    const req = new Request('http://localhost/api/mcp/inquiry', {
      method: 'POST',
      headers: {
        'content-type': 'application/json', 'x-mcp-user': 'user-1', 'x-mcp-key-id': 'key-1',
        'content-length': '10', // lies — the actual stream below sends far more
      },
      body: oversizedChunkedBody(REAL_MAX_REQUEST_BYTES + 1024 * 1024),
      duplex: 'half',
    } as RequestInit)
    const res = await POST(req)
    expect(res.status).toBe(413)
    expect(mocks.verify).not.toHaveBeenCalled()
  })

  // Security review: the certify-sized cap (~33.5 MB) applied to every action. Only a body that
  // leads with "action":"certify" may exceed the small non-certify limit.
  function textBody(text: string): Request {
    const bytes = new TextEncoder().encode(text)
    return new Request('http://localhost/api/mcp/inquiry', {
      method: 'POST',
      headers: { 'content-type': 'application/json', 'x-mcp-user': 'user-1', 'x-mcp-key-id': 'key-1' },
      body: new ReadableStream<Uint8Array>({ start(controller) { controller.enqueue(bytes); controller.close() } }),
      duplex: 'half',
    } as RequestInit)
  }
  const OVER_SMALL = 300 * 1024 // above the 256 KiB non-certify limit, far below the certify limit

  it('refuses a body over the small limit for every non-certify action, header omitted', async () => {
    mocks.verify.mockClear()
    for (const action of ['start', 'execute', 'finalize', 'continue']) {
      const res = await POST(textBody(JSON.stringify({ action, lifecycle_token: 't', pad: 'x'.repeat(OVER_SMALL) })))
      expect(res.status, action).toBe(413)
    }
    expect(mocks.verify).not.toHaveBeenCalled()
  })

  it('refuses a large body that does not lead with the certify action, even if it mentions it later', async () => {
    const res = await POST(textBody(JSON.stringify({ pad: 'x'.repeat(OVER_SMALL), action: 'certify', lifecycle_token: 't' })))
    expect(res.status).toBe(413)
  })

  it('refuses a large body that leads with certify but parses as another action (duplicate action key)', async () => {
    mocks.verify.mockClear()
    const body = `{"action":"certify","action":"start","scope_tuple":{"pad":"${'x'.repeat(OVER_SMALL)}"}}`
    const res = await POST(textBody(body))
    expect(res.status).toBe(413)
    expect(mocks.verify).not.toHaveBeenCalled()
  })

  it('admits a large body that leads with the certify action (up to the certify limit)', async () => {
    primeTerminal(finalized())
    const res = await POST(textBody(JSON.stringify({
      action: 'certify', lifecycle_token: 'final-token', response_text: 'answer', evidence_payloads: [{ pad: 'x'.repeat(OVER_SMALL) }],
    })))
    expect(res.status).not.toBe(413)
  })

  it('accepts a valid request just below the limit and rejects invalid JSON below the limit', async () => {
    // "Just below the limit" at the readBoundedRequestBody layer itself (see the dedicated
    // unit tests below for the exact-boundary cases) — here, a well-formed, ordinary-sized
    // certify body must still succeed end to end.
    primeTerminal(finalized())
    const ok = await POST(request({ action: 'certify', lifecycle_token: 'final-token', response_text: 'answer', evidence_payloads: [payload] }))
    expect(ok.status).not.toBe(413)

    const invalidJson = new Request('http://localhost/api/mcp/inquiry', {
      method: 'POST',
      headers: { 'content-type': 'application/json', 'x-mcp-user': 'user-1', 'x-mcp-key-id': 'key-1' },
      body: '{not valid json',
    })
    const res = await POST(invalidJson)
    expect(res.status).toBe(400)
    expect(await res.json()).toMatchObject({ error: 'INVALID_JSON' })
  })

  it('rejects evidence the server never committed', async () => {
    primeTerminal(finalized())
    const res = await POST(request({ action: 'certify', lifecycle_token: 'final-token', response_text: 'answer', evidence_payloads: [payload, { forged: true }] }))
    expect(res.status).toBe(409)
    expect(await res.json()).toMatchObject({ error: 'INQUIRY_CERTIFICATION_EVIDENCE_UNCOMMITTED' })
  })

  it.each([
    ['a lifecycle that is not terminal', {}, { current_jti_hash: 'sha256:current-jti', revision: 0 }],
    ['a token older than the closing token', { revision: 0 }, { revision: 2 }],
    ['a token for a different contract', { contract_hash: 'sha256:other' }, {}],
    ['a token for a different catalog', { catalog_hash: 'sha256:other-catalog' }, {}],
    ['a stored contract that no longer matches its row', {}, { contract_jsonb: { ...finalized(), contract_id: 'sha256:tampered' } }],
  ])('refuses certification with %s', async (_label, claimOverrides, rowOverrides) => {
    primeTerminal(finalized(), claimOverrides, rowOverrides)
    const res = await POST(request({ action: 'certify', lifecycle_token: 'final-token', response_text: 'answer', evidence_payloads: [payload] }))
    expect(res.status).toBe(409)
    expect(await res.json()).toMatchObject({ error: 'INQUIRY_CERTIFICATION_NOT_AUTHORIZED' })
  })

  it('refuses certification against a stale knowledge snapshot', async () => {
    primeTerminal(finalized())
    mocks.snapshot.mockReturnValue({ content_hash: 'sha256:newer-catalog', compatibility_version: 'planner-scu-v1', scus: [] })
    const res = await POST(request({ action: 'certify', lifecycle_token: 'final-token', response_text: 'answer', evidence_payloads: [payload] }))
    expect(res.status).toBe(409)
    expect(await res.json()).toMatchObject({ error: 'CAPABILITY_KNOWLEDGE_STALE' })
  })

  it('rejects an oversized evidence payload and a malformed request', async () => {
    primeTerminal(finalized())
    const huge = { blob: 'x'.repeat(513 * 1024) }
    const res = await POST(request({ action: 'certify', lifecycle_token: 'final-token', response_text: 'answer', evidence_payloads: [huge] }))
    expect(res.status).toBe(400)
    expect(await res.json()).toMatchObject({ error: 'INQUIRY_CERTIFICATION_PAYLOAD_TOO_LARGE' })
    const malformed = await POST(request({ action: 'certify', lifecycle_token: 'final-token', response_text: '', evidence_payloads: [] }))
    expect(malformed.status).toBe(400)
  })
})

describe('readBoundedRequestBody', () => {
  function streamOf(chunks: readonly string[]): ReadableStream<Uint8Array> {
    const encoder = new TextEncoder()
    let i = 0
    return new ReadableStream<Uint8Array>({
      pull(controller) {
        if (i >= chunks.length) { controller.close(); return }
        controller.enqueue(encoder.encode(chunks[i]!))
        i += 1
      },
    })
  }
  function streamedRequest(chunks: readonly string[]): Request {
    return new Request('http://localhost/x', { method: 'POST', body: streamOf(chunks), duplex: 'half' } as RequestInit)
  }

  describe('two-tier escalation', () => {
    const allowCertify = (prefix: string) => prefix.startsWith('{"action":"certify"')
    const tier = { initialBytes: 20, prefixBytes: 32, allow: allowCertify }

    it('passes a body within the initial limit without consulting escalation', async () => {
      const allow = vi.fn(() => false)
      const result = await readBoundedRequestBody(streamedRequest(['{"a":1}']), 100, { ...tier, allow })
      expect(result.ok).toBe(true)
      expect(allow).not.toHaveBeenCalled()
    })

    it('refuses an unadmitted body at the initial limit, cancelling the stream', async () => {
      const allow = vi.fn(() => false)
      const result = await readBoundedRequestBody(streamedRequest(['{"action":"start",', '"x":"' + 'a'.repeat(40) + '"}']), 100, { ...tier, allow })
      expect(result).toEqual({ ok: false, reason: 'too_large' })
      expect(allow).toHaveBeenCalledTimes(1)
    })

    it('admits a body once, up to the maximum, when the prefix qualifies', async () => {
      const allow = vi.fn(allowCertify)
      const body = '{"action":"certify","x":"' + 'a'.repeat(40) + '"}'
      const ok = await readBoundedRequestBody(streamedRequest([body.slice(0, 10), body.slice(10)]), 100, { ...tier, allow })
      expect(ok).toEqual({ ok: true, text: body })
      expect(allow).toHaveBeenCalledTimes(1)
      const tooBig = await readBoundedRequestBody(streamedRequest(['{"action":"certify","x":"' + 'a'.repeat(200) + '"}']), 100, tier)
      expect(tooBig).toEqual({ ok: false, reason: 'too_large' })
    })

    it('hands escalation only the leading bytes even when one chunk is far larger', async () => {
      let seen = ''
      await readBoundedRequestBody(streamedRequest(['{"action":"certify","x":"' + 'a'.repeat(60) + '"}']), 200, { ...tier, allow: (prefix) => { seen = prefix; return true } })
      expect(seen.length).toBeLessThanOrEqual(32)
      expect(seen.startsWith('{"action":"certify"')).toBe(true)
    })
  })

  it('reads a body with no size problem in full', async () => {
    const result = await readBoundedRequestBody(streamedRequest(['hello ', 'world']), 100)
    expect(result).toEqual({ ok: true, text: 'hello world' })
  })

  it('accepts a body exactly at the limit', async () => {
    const result = await readBoundedRequestBody(streamedRequest(['a'.repeat(10)]), 10)
    expect(result).toEqual({ ok: true, text: 'a'.repeat(10) })
  })

  it('rejects a body one byte over the limit', async () => {
    const result = await readBoundedRequestBody(streamedRequest(['a'.repeat(11)]), 10)
    expect(result).toEqual({ ok: false, reason: 'too_large' })
  })

  it('aborts as soon as the CUMULATIVE total across chunks crosses the limit, not on a single oversized chunk', async () => {
    // Each individual chunk is small; only their sum exceeds the limit — proves the check is
    // a running total across the stream (chunked-transfer shaped), not a per-chunk check.
    const result = await readBoundedRequestBody(streamedRequest(['aaaa', 'bbbb', 'cccc']), 10)
    expect(result).toEqual({ ok: false, reason: 'too_large' })
  })

  it('never accumulates past the limit before rejecting (bounded memory, not measure-after-buffering)', async () => {
    let pulls = 0
    const totalChunks = 1000
    const stream = new ReadableStream<Uint8Array>({
      pull(controller) {
        pulls += 1
        if (pulls > totalChunks) { controller.close(); return }
        controller.enqueue(new TextEncoder().encode('a'.repeat(10)))
      },
    })
    const req = new Request('http://localhost/x', { method: 'POST', body: stream, duplex: 'half' } as RequestInit)
    const result = await readBoundedRequestBody(req, 25) // crosses mid-third chunk
    expect(result).toEqual({ ok: false, reason: 'too_large' })
    // Only enough chunks to cross the limit were ever pulled — not all 1000.
    expect(pulls).toBeLessThan(totalChunks)
  })

  it('treats a request with no body as empty text', async () => {
    const result = await readBoundedRequestBody(new Request('http://localhost/x', { method: 'GET' }), 10)
    expect(result).toEqual({ ok: true, text: '' })
  })
})

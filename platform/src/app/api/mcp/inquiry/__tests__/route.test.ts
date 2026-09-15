import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  authorize: vi.fn(),
  issue: vi.fn(),
  verify: vi.fn(),
  create: vi.fn(),
  get: vi.fn(),
  commitObservation: vi.fn(),
  commitFinalization: vi.fn(),
  reserve: vi.fn(),
  retrieve: vi.fn(),
  apply: vi.fn(),
  finalize: vi.fn(),
  pagination: vi.fn(),
  classify: vi.fn(),
  compile: vi.fn(),
  overlay: vi.fn(),
  snapshot: vi.fn(),
}))

vi.mock('@/lib/mcp/service_token', () => ({ validateServiceToken: () => true }))
vi.mock('@/lib/mcp/auth', () => ({ resolveMcpPrincipalRole: vi.fn().mockResolvedValue('guest') }))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: mocks.authorize }))
vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
vi.mock('@/lib/retrieval/registry/catalog', () => ({ getCatalog: () => [] }))
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
  getInquiryLifecycle: mocks.get,
  commitInquiryObservation: mocks.commitObservation,
  commitInquiryFinalization: mocks.commitFinalization,
  reserveInquiryAction: mocks.reserve,
}))

import type { InquiryContract } from '@/lib/vidhi/inquiry'
import { POST } from '../route'
import { finalizeInquiryContract } from '@/lib/vidhi/inquiry/compiler'
import { classifyInquiryResult, deriveInquiryPaginationReceipt } from '@/lib/vidhi/inquiry/pagination'
import { managedPlanToAiInquiryProposal } from '@/lib/vidhi/inquiry/managed_bridge'
import { stableFingerprint } from '@/lib/retrieval/registry/knowledge/stable'
import {
  compileW5DoorParityContract,
  expectedW5DoorParityProjection,
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
  process.env.INQUIRY_LIFECYCLE_SIGNING_KEY = 'test-inquiry-signing-key-with-at-least-thirty-two-bytes'
  mocks.authorize.mockResolvedValue('all')
  mocks.compile.mockImplementation(() => contract())
  mocks.issue.mockImplementation((claims: Record<string, unknown>) => ({ token: 'next-token', claims: { ...claims, jti: 'next-jti', exp: 2_000_000_000 } }))
  mocks.retrieve.mockResolvedValue({ results: [{ content: '{"rows":[1],"more_available":true}' }] })
  mocks.classify.mockReturnValue('served')
  mocks.pagination.mockReturnValue({ semantics: 'offset', exhausted: false, next: 50 })
  mocks.apply.mockImplementation((value: InquiryContract) => ({ ...value, plan_items: value.plan_items.map((item) => ({ ...item, state: 'observed' })), iteration: value.iteration + 1 }))
  mocks.commitObservation.mockResolvedValue('receipt-1')
  mocks.overlay.mockResolvedValue({ overlay_version: null, build_id: null })
  mocks.snapshot.mockReturnValue({ content_hash: 'sha256:catalog', compatibility_version: 'planner-scu-v1', scus: [{ scu_id: 'scu.test', bindings: [{ binding_id: 'registry:marsys://tool/L1/test', kind: 'registry_capability', executable: true, execution_channels: ['mcp_full'], pagination_contract: { request_position_path: 'offset' } }] }] })
})

describe('raw MCP inquiry route', () => {
  it('matches the reviewed shared-fixture projection through start, execute and finalize', async () => {
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

    mocks.snapshot.mockReturnValue(W5_DOOR_PARITY_SNAPSHOT)
    mocks.overlay.mockResolvedValue(W5_DOOR_PARITY_OVERLAY)
    mocks.compile.mockImplementation(() => compileW5DoorParityContract('mcp_full'))
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
      return Promise.resolve()
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
    expect((await finalized.json()).inquiry_door_parity)
      .toEqual(expectedW5DoorParityProjection('mcp_full'))
  })

  it('requires both principal headers', async () => {
    const response = await POST(request({ action: 'start', chart_id: chartId, question: 'wealth', scope_tuple: scope }, { 'x-mcp-key-id': '' }))
    expect(response.status).toBe(401)
    expect(await response.json()).toMatchObject({ ok: false })
  })

  it('binds a new lifecycle token to user and API-key identity', async () => {
    const response = await POST(request({ action: 'start', chart_id: chartId, question: 'wealth', scope_tuple: scope }))
    expect(response.status).toBe(200)
    expect(mocks.issue).toHaveBeenCalledWith(expect.objectContaining({ sub: 'user-1:key-1', allowed_transition: 'execute', next_action_ids: ['item-001'] }), expect.any(String))
    expect(mocks.create).toHaveBeenCalledWith(expect.objectContaining({ principal_uid: 'user-1', jti_hash: 'sha256:next-jti' }))
  })

  it('rejects revoked chart access before compiling or loading lifecycle state', async () => {
    mocks.authorize.mockResolvedValue('deny')
    const response = await POST(request({ action: 'start', chart_id: chartId, question: 'wealth', scope_tuple: scope }))
    expect(response.status).toBe(401)
    expect(await response.json()).toEqual({ ok: false, error: 'AUTHZ_DENIED' })
    expect(mocks.compile).not.toHaveBeenCalled()
    expect(mocks.create).not.toHaveBeenCalled()
  })

  it('binds token verification to both user and API-key identity', async () => {
    mocks.verify.mockImplementation((_token, _key, subject) => {
      if (subject !== 'user-1:key-1') throw new Error('INQUIRY_TOKEN_WRONG_SUBJECT')
      return {}
    })
    const response = await POST(request(
      { action: 'finalize', lifecycle_token: 'current-token' },
      { 'x-mcp-key-id': 'key-2' },
    ))
    expect(response.status).toBe(401)
    expect(await response.json()).toEqual({ ok: false, error: 'INQUIRY_TOKEN_WRONG_SUBJECT' })
    expect(mocks.get).not.toHaveBeenCalled()
  })

  it('keeps the same action authorized until a verified next page is exhausted', async () => {
    primeStoredLifecycle()
    const response = await POST(request({ action: 'execute', lifecycle_token: 'current-token', action_id: 'item-001' }))
    expect(response.status).toBe(200)
    expect(mocks.issue).toHaveBeenCalledWith(expect.objectContaining({ allowed_transition: 'execute', next_action_ids: ['item-001'] }), expect.any(String))
    expect(await response.json()).toMatchObject({ next_action_ids: ['item-001'], pagination: { next: 50 } })
  })

  it('issues a finalization transition when every plan item is blocked', async () => {
    mocks.compile.mockImplementationOnce(() => ({ ...contract(), plan_items: [] }))
    const response = await POST(request({ action: 'start', chart_id: chartId, question: 'wealth', scope_tuple: scope }))
    expect(response.status).toBe(200)
    expect(mocks.issue).toHaveBeenCalledWith(expect.objectContaining({ allowed_transition: 'finalize', next_action_ids: [] }), expect.any(String))
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
    mocks.reserve.mockResolvedValueOnce(undefined).mockRejectedValueOnce(new Error('INQUIRY_TOKEN_REPLAYED_OR_STALE'))
    const [first, second] = await Promise.all([
      POST(request({ action: 'execute', lifecycle_token: 'current-token', action_id: 'item-001' })),
      POST(request({ action: 'execute', lifecycle_token: 'current-token', action_id: 'item-001' })),
    ])
    expect([first.status, second.status].sort()).toEqual([200, 409])
    expect(mocks.retrieve).toHaveBeenCalledTimes(1)
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

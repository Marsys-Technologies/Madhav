import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  authorize: vi.fn(),
  issue: vi.fn(),
  verify: vi.fn(),
  create: vi.fn(),
  get: vi.fn(),
  commitObservation: vi.fn(),
  commitFinalization: vi.fn(),
  retrieve: vi.fn(),
  apply: vi.fn(),
  finalize: vi.fn(),
  pagination: vi.fn(),
  classify: vi.fn(),
}))

vi.mock('@/lib/mcp/service_token', () => ({ validateServiceToken: () => true }))
vi.mock('@/lib/mcp/auth', () => ({ resolveMcpPrincipalRole: vi.fn().mockResolvedValue('guest') }))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: mocks.authorize }))
vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
vi.mock('@/lib/retrieval/registry/catalog', () => ({ getCatalog: () => [] }))
vi.mock('@/lib/retrieval/registry/knowledge', () => ({
  compileCapabilityKnowledge: () => ({ content_hash: 'sha256:catalog', compatibility_version: 'planner-scu-v1', scus: [{ scu_id: 'scu.test', bindings: [{ binding_id: 'registry:marsys://tool/L1/test', executable: true, pagination_contract: { request_position_path: 'offset' } }] }] }),
}))
vi.mock('@/lib/retrieval/registry/knowledge/stable', () => ({ stableFingerprint: (value: unknown) => `sha256:${JSON.stringify(value).length}` }))
vi.mock('@/lib/retrieval/registry/tool_name_bridge', () => ({ getToolByName: () => ({ retrieve: mocks.retrieve }) }))
vi.mock('@/lib/vidhi/inquiry', async (importOriginal) => {
  const original = await importOriginal<typeof import('@/lib/vidhi/inquiry')>()
  return {
    ...original,
    compileInquiryContract: vi.fn(() => contract()),
    applyInquiryObservations: mocks.apply,
    finalizeInquiryContract: mocks.finalize,
    issueInquiryLifecycleToken: mocks.issue,
    verifyInquiryLifecycleToken: mocks.verify,
    hashJti: (jti: string) => `sha256:${jti}`,
    deriveInquiryPaginationReceipt: mocks.pagination,
    classifyInquiryResult: mocks.classify,
  }
})
vi.mock('@/lib/vidhi/inquiry/lifecycle_store', () => ({
  createInquiryLifecycle: mocks.create,
  getInquiryLifecycle: mocks.get,
  commitInquiryObservation: mocks.commitObservation,
  commitInquiryFinalization: mocks.commitFinalization,
}))

import type { InquiryContract } from '@/lib/vidhi/inquiry'
import { POST } from '../route'

const chartId = '482012f1-710e-4a25-994a-93821f5871aa'
const scope = { intent: 'domain_assessment', domains: ['wealth'], width: 'broad', depth: 'deep', horizon: 'far', intervention: 'none', entitlement: 'native' }

function contract(): InquiryContract {
  return {
    contract_version: '1.0.0', compiler_version: '1.0.0', contract_id: 'sha256:combined',
    semantic_contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan',
    chart_id: chartId, question: 'wealth outlook', scope_tuple: scope,
    capability_compatibility_version: 'planner-scu-v1', capability_content_hash: 'sha256:catalog',
    chart_availability_version: null,
    obligations: [{ obligation_id: 'obl-001', label: 'test', source: 'deterministic_floor', materiality: 'required', scu_ids: ['scu.test'], rationale: 'test', disposition: 'pending', evidence_refs: [], gap_reason: null }],
    plan_items: [{ item_id: 'item-001', obligation_ids: ['obl-001'], scu_id: 'scu.test', binding_id: 'registry:marsys://tool/L1/test', args: { offset: 0 }, depends_on: [], state: 'ready', observation: null }],
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

beforeEach(() => {
  vi.clearAllMocks()
  process.env.INQUIRY_LIFECYCLE_SIGNING_KEY = 'test-inquiry-signing-key-with-at-least-thirty-two-bytes'
  mocks.authorize.mockResolvedValue('all')
  mocks.issue.mockImplementation((claims: Record<string, unknown>) => ({ token: 'next-token', claims: { ...claims, jti: 'next-jti', exp: 2_000_000_000 } }))
  mocks.retrieve.mockResolvedValue({ results: [{ content: '{"rows":[1],"more_available":true}' }] })
  mocks.classify.mockReturnValue('served')
  mocks.pagination.mockReturnValue({ semantics: 'offset', exhausted: false, next: 50 })
  mocks.apply.mockImplementation((value: InquiryContract) => ({ ...value, plan_items: value.plan_items.map((item) => ({ ...item, state: 'observed' })), iteration: value.iteration + 1 }))
  mocks.commitObservation.mockResolvedValue('receipt-1')
})

describe('raw MCP inquiry route', () => {
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

  it('keeps the same action authorized until a verified next page is exhausted', async () => {
    const value = contract()
    mocks.verify.mockReturnValue({
      sub: 'user-1:key-1', inquiry_id: 'inquiry-1', chart_id: chartId, contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan',
      catalog_hash: 'sha256:catalog', compatibility_version: 'planner-scu-v1', overlay_version: null,
      revision: 0, allowed_transition: 'execute', next_action_ids: ['item-001'], jti: 'current-jti', exp: 2_000_000_000,
    })
    mocks.get.mockResolvedValue({
      inquiry_id: 'inquiry-1', principal_uid: 'user-1', chart_id: chartId,
      semantic_contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan', capability_content_hash: 'sha256:catalog',
      capability_compatibility_version: 'planner-scu-v1', chart_overlay_version: null, chart_build_id: null,
      contract_jsonb: value, status: 'INCOMPLETE', revision: 0, current_jti_hash: 'sha256:current-jti', expires_at: '2099-01-01T00:00:00Z',
    })
    const response = await POST(request({ action: 'execute', lifecycle_token: 'current-token', action_id: 'item-001' }))
    expect(response.status).toBe(200)
    expect(mocks.issue).toHaveBeenCalledWith(expect.objectContaining({ allowed_transition: 'execute', next_action_ids: ['item-001'] }), expect.any(String))
    expect(await response.json()).toMatchObject({ next_action_ids: ['item-001'], pagination: { next: 50 } })
  })
})

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Module mocks (hoisted before any imports) ────────────────────────────────

vi.mock('server-only', () => ({}))

vi.mock('@/lib/firebase/server', () => ({
  getServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(),
}))

vi.mock('@/lib/conversations', () => ({
  getConversation: vi.fn(),
  insertConversationWithId: vi.fn(),
  replaceConversationMessages: vi.fn(),
  updateConversationTitle: vi.fn(),
}))

const mockStreamText = vi.fn()
vi.mock('ai', () => ({
  streamText: (...args: unknown[]) => mockStreamText(...args),
  generateText: vi.fn().mockResolvedValue({ text: 'Generated Title' }),
  stepCountIs: vi.fn((n: number) => ({ type: 'stepCount', value: n })),
  smoothStream: vi.fn(() => (s: unknown) => s),
  convertToModelMessages: vi.fn().mockResolvedValue([]),
  createIdGenerator: vi.fn(() => () => 'msg-test-id'),
}))

vi.mock('@/lib/models/registry', () => ({
  DEFAULT_MODEL_ID: 'claude-haiku-4-5',
  TITLE_MODEL_ID: 'claude-haiku-4-5',
  DEFAULT_STACK_ID: 'nim',
  getModelMeta: vi.fn(() => ({ maxOutputTokens: 64000 })),
  isValidModelId: vi.fn(() => false),
  supports: vi.fn(() => false),
  STACK_ROUTING: {
    nim: {
      synthesis: { primary: 'claude-haiku-4-5', fallback: 'claude-haiku-4-5' },
      planner_deep: { primary: 'claude-haiku-4-5', fallback: 'claude-haiku-4-5' },
      planner_fast: { primary: 'claude-haiku-4-5', fallback: 'claude-haiku-4-5' },
      context_assembly: { primary: 'claude-haiku-4-5', fallback: 'claude-haiku-4-5' },
      worker: { primary: 'claude-haiku-4-5', fallback: 'claude-haiku-4-5' },
    },
  },
}))

vi.mock('@/lib/models/resolver', () => ({
  resolveModel: vi.fn(() => ({ id: 'claude-haiku-4-5' })),
  googleProviderOptions: vi.fn(() => null),
}))

vi.mock('@/lib/claude/system-prompts', () => ({
  consumeSystemPrompt: vi.fn(() => 'MOCK_SYSTEM_PROMPT'),
}))

vi.mock('@/lib/router/router', () => ({
  classify: vi.fn(),
}))

vi.mock('@/lib/bundle/rule_composer', () => ({
  compose: vi.fn(),
}))

vi.mock('@/lib/bundle/manifest_reader', () => ({
  loadManifest: vi.fn().mockResolvedValue({ fingerprint: 'test-fp-abc', entries: [], byId: new Map() }),
}))

vi.mock('@/lib/retrieve/index', () => ({
  getTool: vi.fn(() => null),
  RETRIEVAL_TOOLS: [],
}))

vi.mock('@/lib/cache/index', () => ({
  createToolCache: vi.fn(() => ({
    get: vi.fn(),
    put: vi.fn(),
    getPromise: vi.fn().mockReturnValue(undefined),
    generateKey: vi.fn().mockReturnValue('test-key'),
    clear: vi.fn(),
    size: vi.fn().mockReturnValue(0),
  })),
  executeWithCache: vi.fn(),
}))

vi.mock('@/lib/validators/index', () => ({
  runAll: vi.fn(),
  summarize: vi.fn(),
}))

vi.mock('@/lib/synthesis/index', () => ({
  createOrchestrator: vi.fn(),
}))

vi.mock('@/lib/synthesis/context_assembler', () => ({
  contextAssembler: vi.fn().mockResolvedValue({
    tool_bundles: [],
    context_assembly_compressed: true,
    context_assembly_model_id: 'pass-through',
    context_assembly_latency_ms: 0,
    l1_tokens: 0,
    l2_5_tokens: 0,
    l4_tokens: 0,
    vector_tokens: 0,
    cgm_tokens: 0,
    total_tokens: 0,
  }),
}))

// ── Import after mocks ────────────────────────────────────────────────────────

import { POST } from '../route'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { insertConversationWithId, replaceConversationMessages } from '@/lib/conversations'
import { consumeSystemPrompt } from '@/lib/claude/system-prompts'
import { classify } from '@/lib/router/router'
import { compose } from '@/lib/bundle/rule_composer'
import { createOrchestrator } from '@/lib/synthesis/index'
import { runAll, summarize } from '@/lib/validators/index'
import { configService } from '@/lib/config/index'

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeUIMessage(role: 'user' | 'assistant', text: string) {
  return {
    id: `${role}-1`,
    role,
    parts: [{ type: 'text', text }],
  }
}

function makeRequest(body: Record<string, unknown> = {}) {
  return new Request('http://localhost/api/chat/consume', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chartId: 'chart-uuid-001',
      messages: [makeUIMessage('user', 'What does my chart say about career?')],
      ...body,
    }),
  })
}

function makeStreamResult() {
  return {
    consumeStream: vi.fn(),
    toUIMessageStreamResponse: vi.fn().mockReturnValue(new Response('ok', { status: 200 })),
  }
}

function makeValidQueryPlan() {
  return {
    query_plan_id: 'plan-001',
    query_text: 'What does my chart say about career?',
    query_class: 'interpretive' as const,
    domains: ['career'],
    forward_looking: false,
    audience_tier: 'super_admin' as const,
    tools_authorized: [],
    history_mode: 'synthesized' as const,
    panel_mode: false,
    expected_output_shape: 'three_interpretation' as const,
    manifest_fingerprint: 'test-fp-abc',
    schema_version: '1.0' as const,
  }
}

function makeValidBundle() {
  return {
    bundle_id: 'bundle-001',
    query_plan_reference: 'plan-001',
    manifest_fingerprint: 'test-fp-abc',
    mandatory_context: [],
    total_tokens: 0,
    bundle_hash: 'sha256:abc',
    schema_version: '1.0' as const,
  }
}

function makeQueryResult<T>(rows: T[]) {
  return { rows, command: 'SELECT', rowCount: rows.length, oid: 0, fields: [] } as unknown as import('pg').QueryResult
}

function setupDbMocks(role = 'super_admin') {
  vi.mocked(query).mockImplementation(async (sql: string) => {
    if (sql.includes('FROM charts')) {
      return makeQueryResult([{ id: 'chart-uuid-001', name: 'Test Native', birth_date: '1984-02-05', birth_time: '10:43', birth_place: 'Bhubaneswar', client_id: 'user-uid-001' }])
    }
    if (sql.includes('FROM profiles')) {
      return makeQueryResult([{ role }])
    }
    return makeQueryResult([])
  })
}

// ── Tests ─────────────────────────────────────────────────────────────────────

beforeEach(() => {
  vi.clearAllMocks()
  configService.setFlag('VALIDATOR_FAILURE_HALT', true)

  vi.mocked(getServerUser).mockResolvedValue({ uid: 'user-uid-001', email: 'test@test.com' } as ReturnType<typeof getServerUser> extends Promise<infer T> ? T : never)
  vi.mocked(insertConversationWithId).mockResolvedValue(undefined)
  vi.mocked(replaceConversationMessages).mockResolvedValue(undefined)

  // Default validator mocks (pass)
  vi.mocked(runAll).mockResolvedValue([])
  vi.mocked(summarize).mockReturnValue({ overall: 'pass', by_validator: {}, failures: [] })
})

// ── Test: new query pipeline (only path since Phase 11B) ─────────────────────

describe('new query pipeline', () => {
  it('calls classify, compose, and createOrchestrator', async () => {
    setupDbMocks()

    const queryPlan = makeValidQueryPlan()
    const bundle = makeValidBundle()
    const mockResult = makeStreamResult()
    const mockSynthesize = vi.fn().mockResolvedValue({ result: mockResult, metadata: {} })

    vi.mocked(classify).mockResolvedValue(queryPlan)
    vi.mocked(compose).mockResolvedValue(bundle)
    vi.mocked(createOrchestrator).mockReturnValue({ synthesize: mockSynthesize })

    const res = await POST(makeRequest())

    expect(vi.mocked(classify)).toHaveBeenCalledOnce()
    expect(vi.mocked(compose)).toHaveBeenCalledWith(queryPlan)
    expect(vi.mocked(createOrchestrator)).toHaveBeenCalledOnce()
    expect(mockSynthesize).toHaveBeenCalledOnce()
    // Static path must NOT be called
    expect(consumeSystemPrompt).not.toHaveBeenCalled()
    expect(mockStreamText).not.toHaveBeenCalled()
    expect(res.status).toBe(200)
  })
})

// ── Test 3: Auth failure returns 401 ─────────────────────────────────────────

describe('auth failure', () => {
  it('returns 401 when user is not authenticated', async () => {
    vi.mocked(getServerUser).mockResolvedValue(null)

    const res = await POST(makeRequest())

    expect(res.status).toBe(401)
    const body = await res.json()
    expect(body.error.code).toBe('AUTH_UNAUTHENTICATED')
  })
})

// ── Test 4: Missing chartId returns 400 ──────────────────────────────────────

describe('missing chartId', () => {
  it('returns 400 when chartId is missing', async () => {
    const req = new Request('http://localhost/api/chat/consume', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: [makeUIMessage('user', 'hello')] }),
    })

    const res = await POST(req)

    expect(res.status).toBe(400)
    const body = await res.json()
    expect(body.error.detail).toBe('chartId and messages are required')
  })
})

// ── Test 5: Flag ON — validator halt returns 422 ─────────────────────────────

describe('validator halt on bundle failure', () => {
  beforeEach(() => {
    configService.setFlag('VALIDATOR_FAILURE_HALT', true)
  })

  it('returns 422 when bundle validation fails and VALIDATOR_FAILURE_HALT is true', async () => {
    setupDbMocks()

    const queryPlan = makeValidQueryPlan()
    const bundle = makeValidBundle()

    vi.mocked(classify).mockResolvedValue(queryPlan)
    vi.mocked(compose).mockResolvedValue(bundle)
    vi.mocked(runAll).mockResolvedValue([
      { validator_id: 'p1', validator_version: '1.0', vote: 'fail', reason: 'layer violation' },
    ])
    vi.mocked(summarize).mockReturnValue({
      overall: 'fail',
      by_validator: { p1: 'fail' },
      failures: [{ validator_id: 'p1', validator_version: '1.0', vote: 'fail' }],
    })

    const res = await POST(makeRequest())

    expect(res.status).toBe(422)
    const body = await res.json()
    expect(body.error).toBe('bundle_validation_failed')
    expect(body.failures).toBeDefined()
  })
})

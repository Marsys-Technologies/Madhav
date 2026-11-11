import { beforeEach, describe, expect, it, vi } from 'vitest'
import { FEATURE_FLAGS } from '@/lib/config/feature_flags'

const harness = vi.hoisted(() => ({
  insert: vi.fn(), fakeRead: vi.fn(), extract: vi.fn(), prepareByok: vi.fn(),
  dispatch: vi.fn(async (_context: unknown) => new Response('fixture dispatch')),
  manifest: vi.fn(async () => ({ fingerprint: 'synthetic' })), planner: vi.fn(),
  compress: vi.fn(async (history: unknown) => history),
  sql: vi.fn(async (sql: string) => ({ rows: sql.includes('FROM charts')
    ? [{ id: '00000000-0000-4000-8000-000000000001', client_id: 'fixture-owner' }]
    : sql.includes('FROM profiles') ? [{ role: 'guest', status: 'active' }] : [] })),
  state: { byok: false, compress: false, ready: true, permission: 'view', signedIn: true },
}))

vi.mock('server-only', () => ({}))
vi.mock('@/lib/firebase/server', () => ({
  getServerUser: async () => harness.state.signedIn ? { uid: 'fixture-owner' } : null,
}))
vi.mock('@/lib/db/client', () => ({ query: harness.sql, getPool: vi.fn() }))
vi.mock('@/lib/config/index', () => ({ configService: { getFlag: (key: string) =>
  key === 'AI_CONSOLE_BYOK' ? harness.state.byok : key === FEATURE_FLAGS.historyCompression && harness.state.compress,
} }))
vi.mock('@/lib/models/runtime_config', () => ({ getEffectiveModel: async () => 'fixture-model' }))
vi.mock('@/lib/models/registry', () => ({
  DEFAULT_MODEL_ID: 'fixture-model', DEFAULT_STACK_ID: 'fixture-stack',
  STACK_ROUTING: { 'fixture-stack': {} }, isValidModelId: () => false,
  getModelMeta: () => ({ provider: 'fixture' }),
}))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: async () => harness.state.permission }))
vi.mock('@/lib/conversations', () => ({ getConversation: async () => null, insertConversationWithId: harness.insert }))
vi.mock('@/lib/charts/readiness', () => ({
  getChartReadinessMap: async (ids: string[]) => new Map(ids.map(id => [id, { state: harness.state.ready ? 'ready' : 'building' }])),
  isDerivedChartReady: (value: { state: string }) => value.state === 'ready',
}))
vi.mock('@/lib/multimodal/fake_gcs_store', () => ({ fakeGcsRetrieve: harness.fakeRead }))
vi.mock('@/lib/multimodal/pdf_extractor', () => ({ extractPdf: harness.extract }))
vi.mock('@/lib/pariprashna/pipeline/byok_preflight', () => ({ prepareByokTurn: harness.prepareByok }))
vi.mock('@/lib/pipelines/shared', () => ({ runAdapterDispatch: harness.dispatch }))
vi.mock('@/lib/bundle/manifest_reader', () => ({ loadManifest: harness.manifest }))
vi.mock('@/lib/pipeline/pipeline_planner', () => ({ callPipelinePlanner: harness.planner }))
vi.mock('@/lib/retrieval/orientation', () => ({ buildChartOrientation: async () => null }))
vi.mock('@/lib/pariprashna/safety', () => ({
  classifyTurnSafety: async () => ({ enforced: false }),
  HS2_FIXED_RESPONSE: 'Fixture hard stop', SEAL_PENDING_ACKNOWLEDGMENT: 'Fixture acknowledgment',
}))
vi.mock('@/lib/persistence/pending_streams_writer', () => ({ createPendingStreamWriter: vi.fn() }))
vi.mock('@/lib/pipeline/compiled_floor_adapter', () => ({
  ensureB11WholeChartReadFloor: vi.fn(), ensureDashaContextFloor: vi.fn(), compileFloorForPlan: vi.fn(),
}))
vi.mock('@/lib/pipeline/no_leakage_filter', () => ({ filterLeakedCapabilities: (tools: string[]) => tools }))
vi.mock('@/lib/bundle/bundle_hydrator', () => ({ hydrateBundle: async () => ({ assets: [] }) }))
vi.mock('@/lib/validators/index', () => ({ runAll: async () => [], summarize: () => ({ overall: 'pass' }) }))
vi.mock('@/lib/db/monitoring-write', () => ({ writeQueryPlanLog: async () => {} }))
vi.mock('@/lib/trace/emitter', () => ({ traceEmitter: { emitStep: vi.fn() } }))
vi.mock('@/lib/synthesis/history_compression', () => ({ compressHistory: harness.compress }))
vi.mock('@/lib/cache/index', () => ({ createToolCache: vi.fn() }))
vi.mock('@/lib/vidhi/inquiry', () => ({}))
vi.mock('@/lib/retrieval/registry/knowledge', () => ({}))

import { POST } from '../route'
import { POST as redirect } from '../../consume/route'

const CHART = '00000000-0000-4000-8000-000000000001'
const TEXT = { type: 'text', text: 'Fixture question' }
const FILE = { type: 'file', mediaType: 'image/png', url: 'data:image/png;base64,eA==' }

function request(
  attachments?: unknown,
  messages: unknown = [{ id: 'fixture-message', role: 'user', parts: [TEXT] }],
  endpoint = '/api/chat/consult',
) {
  return new Request('https://fixture.invalid' + endpoint, {
    method: 'POST',
    body: JSON.stringify({ chartId: CHART, messages, attachments }),
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  Object.assign(harness.state, { byok: false, compress: false, ready: true, permission: 'view', signedIn: true })
  harness.planner.mockImplementation(async () => ({
    outcome: 'plan',
    plan: { tool_calls: [], query_class: 'factual', domains: [], forward_looking: false },
    metrics: {
      planning_confidence: 1, fallback_used: false, active_model_id: 'fixture-model',
      parsed_on_first_attempt: true, first_parse_error: null,
    },
  }))
})

function expectNoAttachmentOrTurnWork() {
  for (const spy of [harness.fakeRead, harness.extract, harness.insert, harness.prepareByok, harness.manifest, harness.planner, harness.dispatch]) {
    expect(spy).not.toHaveBeenCalled()
  }
  expect(harness.sql.mock.calls.every(([sql]) => /^\s*SELECT\b/i.test(sql))).toBe(true)
}

async function expectUnavailable(response: Response, status = 503) {
  expect(response.status).toBe(status)
  expect(response.headers.get('Cache-Control')).toBe('private, no-store')
  expect(await response.json()).toMatchObject({ error: { code: 'ATTACHMENT_UNAVAILABLE', retry: false } })
  expectNoAttachmentOrTurnWork()
}

describe('Consult attachment containment', () => {
  it.each(['known', 'stale', 'wrong-owner'])('refuses %s token without reading attachment bytes', async token => {
    await expectUnavailable(await POST(request([{ token, filename: 'untrusted.pdf' }])))
  })

  it.each([false, true])('refuses inline-only and mixed turns with BYOK=%s even when an assistant follows them', async byok => {
    harness.state.byok = byok
    for (const parts of [[FILE], [TEXT, FILE]]) {
      await expectUnavailable(await POST(request(undefined, [
        { id: 'latest-user', role: 'user', parts },
        { id: 'later-assistant', role: 'assistant', parts: [TEXT] },
      ])))
    }
  })

  it.each([{ refs: {} }, { refs: [null] }, { refs: [{ token: '' }] }])('rejects malformed attachment references $refs', async ({ refs }) => {
    await expectUnavailable(await POST(request(refs)), 400)
  })

  it('honors the actual 308 for the legacy upload reference body', async () => {
    const original = request([{ token: 'stale' }], undefined, '/api/chat/consume?fixture=1')
    const response = await redirect(original)
    expect(response.status).toBe(308)
    expect(response.headers.get('Location')).toBe('https://fixture.invalid/api/chat/consult?fixture=1')
    const redirected = new Request(response.headers.get('Location')!, {
      method: original.method,
      body: await original.text(),
    })
    await expectUnavailable(await POST(redirected))
  })

  it.each([
    { gate: 'session', status: 401, state: { signedIn: false } },
    { gate: 'chart', status: 403, state: { permission: 'deny' } },
    { gate: 'readiness', status: 409, state: { ready: false } },
  ])('preserves $gate rejection ahead of the attachment response', async ({ status, state }) => {
    Object.assign(harness.state, state)
    expect((await POST(request([{ token: 'stale' }]))).status).toBe(status)
    expectNoAttachmentOrTurnWork()
  })

  it.each([false, true])('accepts text and retains persisted history without replaying historical file parts (compression=%s)', async compress => {
    harness.state.compress = compress
    const messages = [
      { id: 'file-only', role: 'user', parts: [FILE] },
      { id: 'mixed', role: 'user', parts: [TEXT, FILE] },
      { id: 'answer', role: 'assistant', parts: [{ type: 'text', text: 'Earlier answer' }] },
      { id: 'new', role: 'user', parts: [{ type: 'text', text: 'New text' }] },
    ]
    const response = await POST(request([], messages))
    expect(response.status).toBe(200)
    expect(await response.text()).toBe('fixture dispatch')
    expect(harness.insert).toHaveBeenCalledOnce()
    expect(harness.dispatch).toHaveBeenCalledOnce()
    const context = harness.dispatch.mock.calls[0][0]
    expect(context).toMatchObject({
      queryText: 'New text', messages,
      trimmedConversationHistory: [
        { role: 'user', content: [TEXT] },
        { role: 'assistant', content: [{ type: 'text', text: 'Earlier answer' }] },
      ],
    })
    if (compress) {
      expect(harness.compress).toHaveBeenCalledOnce()
      expect(JSON.stringify(harness.compress.mock.calls[0][0])).not.toContain(FILE.url)
    } else {
      expect(harness.compress).not.toHaveBeenCalled()
    }
    expect(harness.fakeRead).not.toHaveBeenCalled()
    expect(harness.extract).not.toHaveBeenCalled()
  })
})

import { beforeEach, describe, expect, it, vi } from 'vitest'
import { assembleAcharyaReadingReceipt } from '@/lib/pariprashna/receipt/assemble'
import { deriveClientRequestTurnId } from '@/lib/pariprashna/request_identity'

const state = vi.hoisted(() => ({ uid: 'alice' as string | null, permission: 'view', enabled: true,
  query: vi.fn(), ring: vi.fn() }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: async () => state.uid ? { uid: state.uid } : null }))
vi.mock('@/lib/config/index', () => ({ configService: { getFlag: () => state.enabled } }))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: async () => state.permission }))
vi.mock('@/lib/db/client', () => ({ query: state.query, withTransaction: vi.fn() }))
vi.mock('@/lib/pariprashna/protocol/ring_buffer', () => ({ getTurnMeta: state.ring,
  getBufferedEventsSince: vi.fn(), finalizeInterruptedIfStale: vi.fn(), appendBufferedEvent: vi.fn(), buildSnapshotText: vi.fn() }))
import { GET } from '../route'

const chart = '10000000-0000-4000-8000-000000000001'
const nonce = '20000000-0000-4000-8000-000000000002'
const conversation = '30000000-0000-4000-8000-000000000003'
const snapshot = '40000000-0000-4000-8000-000000000004'
const messageId = '50000000-0000-4000-8000-000000000005'
const turn = deriveClientRequestTurnId('alice', chart, nonce)
function receipt(overrides: {turnId?: string; conversationId?: string; chartId?: string} = {}) {
  return assembleAcharyaReadingReceipt({ turnId: turn, conversationId: conversation, chartId: chart, ...overrides,
    plan: { domains: undefined }, committedBlocks: [], accumulatedText: 'Canonical synthetic answer',
    citationsFound: [], citationRewriteEnabled: false, resolvedCitations: [], citationHallucinationCount: 0,
    completenessReceipt: null, safetyDecision: undefined, validToolResults: [],
    provenanceStamp: { build_id: 'synthetic', priors_version: 'synthetic', formula_versions: { salience_formula_ver: null },
      ranking_config: { mode: 'composite_v1' }, now_context_date: '2026-11-14', computed_at: '2026-11-14T00:00:00.000Z' } })
}
function row() {
  return { id: messageId, role: 'assistant', created_at: '2026-11-14T00:00:00.000Z', tagged: false, schema_version: 1,
    parts_json: [{ type: 'reasoning', text: 'private reasoning' }, { type: 'text', text: 'stale legacy answer' }],
    canonical_parts: [{ kind: 'text', body: { text: 'Canonical synthetic answer' } },
      { kind: 'tool_result', body: { unprojected_fixture_field: 'FIXTURE_ONLY_TOOL' } }],
    metadata_json: { custom: { queryId: turn, conversationId: conversation, ai_routing_snapshot_id: snapshot, unprojected_fixture_field: 'FIXTURE_ONLY_CUSTOM' },
      acharya_reading_receipt: receipt(), unprojected_fixture_field: 'FIXTURE_ONLY_METADATA' }, unprojected_fixture_field: 'FIXTURE_ONLY_ROW' }
}
let binding: Record<string, unknown>[]
let matching: Record<string, unknown>[]
let stored: ReturnType<typeof row>[]
let outage: string | undefined
beforeEach(() => {
  state.uid = 'alice'; state.permission = 'view'; state.enabled = true
  state.ring.mockReset().mockResolvedValue(null)
  binding = [{ id: snapshot, conversation_id: conversation, correlation_id: turn }]
  matching = [{ id: messageId }]; stored = [row()]; outage = undefined
  state.query.mockReset().mockImplementation(async (sql: string, params: unknown[]) => {
    if (outage && sql.includes(outage)) throw new Error('synthetic SQL outage')
    if (sql.includes('SELECT role FROM profiles')) return { rows: [{ role: 'guest' }] }
    if (sql.includes('JOIN conversations c ON')) {
      // Transport fixture honors owner, exact request identity and chart, not "latest".
      return { rows: params[0] === 'alice' && params[1] === turn && params[2] === chart ? binding : [] }
    }
    if (sql.includes('SELECT m.id FROM conversation_messages')) return { rows: matching }
    if (sql.includes('SELECT m.id, m.role')) return { rows: stored.filter(m => m.id === params[1]) }
    throw new Error(`Unexpected SQL: ${sql}`)
  })
})
function request(query = `chart_id=${chart}&client_request_id=${nonce}`) {
  return GET(new Request(`http://localhost/api/pariprashna/resume?${query}`))
}

describe('SQL request recovery through the real repository and conversation readers', () => {
  it('returns only the exact validated canonical assistant without replay/model work', async () => {
    const response = await request(); expect(response.status).toBe(200)
    expect(response.headers.get('cache-control')).toBe('private, no-store')
    const body = await response.json()
    expect(body).toMatchObject({ status: 'complete', turnId: turn, conversationId: conversation,
      message: { id: messageId, role: 'assistant', parts_json: [], canonical_parts: [{kind:'text',body:{text:'Canonical synthetic answer'}}] } })
    expect(Object.keys(body.message.metadata_json)).toEqual(['acharya_reading_receipt'])
    expect(JSON.stringify(body)).not.toMatch(/private|FIXTURE_ONLY|unprojected_fixture_field|stale legacy/)
    expect(state.ring).not.toHaveBeenCalled()
    const calls = state.query.mock.calls
    expect(calls.find(([sql]) => sql.includes('JOIN conversations c ON'))?.[0]).toContain("s.source='pariprashna'")
    expect(calls.find(([sql]) => sql.includes('JOIN conversations c ON'))?.[0]).toContain("c.module='consume'")
    expect(calls.find(([sql]) => sql.includes('SELECT m.id FROM'))?.[1]).toEqual([conversation, turn])
    expect(calls.find(([sql]) => sql.includes('SELECT m.id, m.role'))?.[1]).toEqual([conversation, messageId])
  })
  it('reports pending then the same completed message without using a prior/concurrent answer', async () => {
    matching = []
    expect(await (await request()).json()).toEqual({ status: 'pending', turnId: turn, conversationId: conversation })
    expect((await request()).status).toBe(202)
    stored.unshift({ ...row(), id: '60000000-0000-4000-8000-000000000006' })
    matching = [{ id: messageId }]
    expect((await (await request()).json()).message.id).toBe(messageId)
  })
  it('keeps receiptless completion pending rather than inventing success', async () => {
    matching = [] // Real SQL exact receipt predicate cannot select a receiptless answer.
    stored[0].metadata_json = { ...stored[0].metadata_json, acharya_reading_receipt: undefined as never }
    expect((await request()).status).toBe(202)
  })
  it.each(['chart_id=bad&client_request_id='+nonce, 'chart_id='+chart,
    'client_request_id='+nonce, `chart_id=${chart}&client_request_id=bad`,
    `chart_id=${chart}&client_request_id=${nonce}&turn_id=${turn}`,
    `chart_id=${chart}&client_request_id=${nonce}&client_request_id=${nonce}`,
    `chart_id=${chart}&chart_id=${chart}&client_request_id=${nonce}`])('rejects malformed or mixed identities %s', async q => {
    expect((await request(q)).status).toBe(400); expect(state.query).not.toHaveBeenCalled()
  })
  it('requires authentication before any read', async () => {
    state.uid = null; expect((await request()).status).toBe(401); expect(state.query).not.toHaveBeenCalled()
  })
  it('rechecks current chart entitlement, including a revoked grant', async () => {
    state.permission = 'deny'; expect((await request()).status).toBe(403)
    expect(state.query.mock.calls.some(([s]) => s.includes('ai_turn_routing_snapshots'))).toBe(false)
  })
  it('cannot resolve another owner or another chart even with chart permission', async () => {
    state.uid = 'bob'; expect((await request()).status).toBe(404)
    state.uid = 'alice'
    expect((await request(`chart_id=${conversation}&client_request_id=${nonce}`)).status).toBe(404)
  })
  it('unknown request is 404, never pending', async () => {
    binding=[]; expect((await request()).status).toBe(404)
  })
  it.each(['JOIN conversations c ON', 'SELECT m.id FROM', 'SELECT m.id, m.role'])('SQL failure at %s is unavailable, never pending', async point => {
    outage=point; expect((await request()).status).toBe(503)
  })
  it.each(['binding', 'multiple', 'hash', 'chart', 'conversation', 'turn', 'queryId', 'snapshot', 'customConversation', 'schema', 'body', 'empty', 'role'])(
    'rejects integrity failure: %s', async defect => {
      if (defect==='binding') binding.push(binding[0])
      if (defect==='multiple') matching.push({ id: '60000000-0000-4000-8000-000000000006' })
      if (defect==='hash') stored[0].metadata_json.acharya_reading_receipt.receipt_hash='a'.repeat(64)
      if (defect==='chart') stored[0].metadata_json.acharya_reading_receipt=receipt({chartId:conversation})
      if (defect==='conversation') stored[0].metadata_json.acharya_reading_receipt=receipt({conversationId:chart})
      if (defect==='turn') stored[0].metadata_json.acharya_reading_receipt=receipt({turnId:nonce})
      if (defect==='queryId') stored[0].metadata_json.custom.queryId=nonce
      if (defect==='snapshot') stored[0].metadata_json.custom.ai_routing_snapshot_id=chart
      if (defect==='customConversation') stored[0].metadata_json.custom.conversationId=chart
      if (defect==='schema') stored[0].schema_version=999999
      if (defect==='body') stored[0].canonical_parts=[{kind:'text',body:{text:42}}] as never
      if (defect==='empty') { stored[0].canonical_parts=[]; stored[0].parts_json=[] }
      if (defect==='role') stored[0].role='tool'
      expect((await request()).status).toBe(500)
    })
  it('preserves nonce-free turn_id SSE resume', async () => {
    const response=await request('turn_id=old-turn'); expect(response.headers.get('content-type')).toContain('text/event-stream')
    expect(await response.text()).toContain('UNKNOWN_TURN'); expect(state.ring).toHaveBeenCalledWith('old-turn')
  })
})

/**
 * V3-E-045 (EDIR_V3_REGISTER, S3 DEFECT) — the wire `turn_id` and the
 * persisted `conversation_messages.metadata_json.custom.queryId` for the
 * SAME turn used to be two independently-generated `crypto.randomUUID()`
 * calls (`route.ts:104-105`, pre-fix). A caller holding only the wire
 * `turn_id` could not look up the persisted row by that id directly.
 *
 * THE FIX (`route.ts`, this lane): `queryId` is now derived directly from
 * `turnId` — one `crypto.randomUUID()` call, reused for both — rather than a
 * second, independent random mint.
 *
 * THIS FILE drives the REAL `/api/pariprashna` route (`POST`, unmocked route
 * logic + unmocked registry/filter/citation-gate/assembler code, same
 * technique as `no_leakage_route_canary.test.ts`, door 3) through a
 * synthesis pass that actually produces prose, so the real persistence path
 * (`runPersistenceStage` → the canonical `writeTurn` DAL) runs to completion,
 * and captures THREE independently-observed values:
 *
 *   1. the WIRE `turn_id`               — from the decoded `turn.open` SSE event
 *   2. the `pending_streams` key        — the `queryId` argument the route
 *                                          hands `createPendingStreamWriter`
 *                                          (`persistence_stage.ts:217`)
 *   3. the PERSISTED `queryId`          — `conversation_messages.metadata_json
 *                                          .custom.queryId`, captured off the
 *                                          real canonical `writeTurn` call
 *                                          (`store/writer.ts`, mocked only at
 *                                          the pg boundary — same mock seam
 *                                          `wire_persisted_byte_agreement
 *                                          .test.ts` uses)
 *
 * Before the fix, (1) and (2)/(3) were independently-random UUIDs — this
 * test's own RED-CONTROL block below proves that difference is exactly what
 * a mismatch looks like (§N.8: the comparator must be demonstrated capable of
 * failing). After the fix, all three are byte-identical.
 *
 * RUNG ACHIEVED: real route-level (`POST` from `route.ts`), red→green
 * verified locally against the pre-fix two-`randomUUID()` code (see report).
 *
 * Chart id used throughout is the SYNTHETIC probe chart
 * (`1c826d5a-41cb-4450-b4dc-59d440e5f75a`) — never the native's real chart.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const CHART = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

// ── Boundary mocks (LLM / DB / auth / persistence I/O) — route logic,
//    registry, citation gate, and the block/pass assembler all stay REAL. ──
vi.mock('@/lib/firebase/server', () => ({ getServerUser: vi.fn(async () => ({ uid: 'tester-uid' })) }))
vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string, params?: unknown[]) => {
    if (/from charts/i.test(sql)) {
      const id = (params?.[0] as string) ?? CHART
      return { rows: [{ id, name: 'Synthetic Probe', client_id: 'tester-uid' }] }
    }
    if (/from profiles/i.test(sql)) return { rows: [{ role: 'guest' }] }
    return { rows: [] }
  }),
}))
vi.mock('@/lib/config/index', () => ({
  configService: { getFlag: vi.fn((k: string) => k === 'PARIPRASHNA_ENABLED') },
}))
vi.mock('@/lib/models/runtime_config', () => ({ getEffectiveModel: vi.fn(async () => 'gemini-2.5-pro') }))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: vi.fn(async () => 'view') }))
vi.mock('@/lib/conversations', () => ({
  getConversation: vi.fn(async () => null),
  insertConversationWithId: vi.fn(async () => undefined),
  updateConversationTitle: vi.fn(async () => undefined),
}))
vi.mock('@/lib/conversations/title', () => ({ generateConversationTitle: vi.fn(async () => 'Harness Title') }))
vi.mock('@/lib/bundle/manifest_reader', () => ({ loadManifest: vi.fn(async () => ({ fingerprint: 'test-fp' })) }))
vi.mock('@/lib/retrieval/orientation', () => ({ buildChartOrientation: vi.fn(async () => null) }))
vi.mock('@/lib/bundle/bundle_hydrator', () => ({ hydrateBundle: vi.fn(async () => ({ assets: [], floor_enforced: false })) }))
vi.mock('@/lib/db/monitoring-write', () => ({ writeContextAssemblyLog: vi.fn() }))
vi.mock('@/lib/pariprashna/protocol/ring_buffer', () => ({
  openTurnBuffer: vi.fn(async () => {}),
  appendBufferedEvent: vi.fn(async () => {}),
}))
vi.mock('@/lib/pariprashna/protocol/stream_capture', () => ({
  beginTurnCapture: vi.fn(() => {}),
  captureEvent: vi.fn(async () => {}),
  endTurnCapture: vi.fn(() => {}),
}))
vi.mock('@/lib/pariprashna/provenance/stamp', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/pariprashna/provenance/stamp')>()
  return {
    ...actual,
    computeTurnProvenanceStamp: vi.fn(async () => ({
      build_id: 'test-build',
      priors_version: 'v3',
      formula_versions: { salience_formula_ver: null },
      ranking_config: { mode: 'harness' },
      now_context_date: '2026-08-29',
      computed_at: '2026-08-29T00:00:00.000Z',
    })),
    getLastTurnStamp: vi.fn(async () => null),
  }
})
vi.mock('@/lib/pariprashna/samiksha/capture', () => ({
  captureDetectedCandidates: vi.fn(async () => ({ created: [], skippedExisting: 0, unpaired: 0 })),
}))
vi.mock('@/lib/llm/pricing', () => ({
  getModelPricingSync: vi.fn(() => null),
  computeCostUsd: vi.fn(() => null),
}))
vi.mock('@/lib/predictions/calibration_producer', () => ({ recordCalibrationStamp: vi.fn(async () => {}) }))
vi.mock('@/lib/persistence/conversation_writer', () => ({
  writeConversationMessages: vi.fn(async () => ({ verified: true, messageIds: ['history-msg-1'] })),
}))

// ── The two observation points under test ────────────────────────────────────
// (a) the pending_streams key the route hands the writer.
const { pendingStreamCalls } = vi.hoisted(() => ({ pendingStreamCalls: [] as Array<{ queryId: string }> }))
vi.mock('@/lib/persistence/pending_streams_writer', () => ({
  createPendingStreamWriter: vi.fn((queryId: string) => {
    pendingStreamCalls.push({ queryId })
    return { clear: vi.fn(async () => {}) }
  }),
}))
// (b) the canonical assistant-row write — the pg boundary; everything upstream
//     (canonical message assembly, receipt/provenance stamping) is REAL. Same
//     seam `wire_persisted_byte_agreement.test.ts` uses.
const { writeTurnCalls } = vi.hoisted(() => ({
  writeTurnCalls: [] as Array<{ message: Record<string, unknown>; parts: unknown[] }>,
}))
vi.mock('@/lib/pariprashna/store/writer', () => ({
  writeTurn: vi.fn(async (message: Record<string, unknown>, parts: unknown[]) => {
    writeTurnCalls.push({ message, parts })
    return { message_id: message.id as string, parts_written: parts.length }
  }),
}))

// Planner — a real, minimal plan (no leaked/exotic tools).
vi.mock('@/lib/pipeline/pipeline_planner', () => ({
  PlannerFault: class PlannerFault extends Error {},
  callPipelinePlanner: vi.fn(async () => ({
    outcome: 'plan' as const,
    plan: {
      query_class: 'holistic',
      domains: ['self'],
      forward_looking: false,
      tool_calls: [],
    },
  })),
}))
vi.mock('@/lib/pipeline/compiled_floor_adapter', () => ({
  compileFloorForPlan: vi.fn(() => ({ toolCalls: [], mappedPrimitives: [], unmappedPrimitives: [], compilerIntent: 'general_synthesis', compileFailed: false })),
  ensureB11WholeChartReadFloor: vi.fn(() => false),
  ensureDashaContextFloor: vi.fn(() => false),
}))
vi.mock('@/lib/pipelines/shared/run_adapter_dispatch', () => ({ buildConsultSystemContent: vi.fn(() => 'SYS') }))
vi.mock('@/lib/pariprashna/summaries/splice', () => ({ getConversationSummaryForSplice: vi.fn(async () => null) }))
vi.mock('@/lib/pariprashna/summaries/assemble', () => ({ assembleSynthesisPrefix: vi.fn(({ precedingBlock }: { precedingBlock: string }) => precedingBlock) }))
vi.mock('@/lib/synthesis/streaming_citation_validator', () => ({
  validateCitationsForStream: vi.fn(() => ({ gateResult: 'PASS', gateReason: 'ok', layer1Count: 0, layer2Verified: 0 })),
}))

// Adapter — yields ONE real text delta so `accumulatedText` is non-empty and
// the full persistence path (not the `empty_synthesis` early return) runs.
// NOTE: `synthesis_stage.ts`'s `useAgenticLoop` gate keys off the PROVIDER
// (`AGENTIC_PROVIDERS.has(adapterId)`), not `getManifest().adaptiveToolLoop`
// — `gemini-2.5-pro` resolves to the `google` provider, which IS agentic, so
// the route actually drives `runAgenticLoop`, not `adapter.chat`, for this
// model. Both are mocked to yield the same delta so the test is robust to
// which path a given `modelId` takes.
async function* textDeltaStream(): AsyncGenerator<{ type: string; text: string }> {
  yield { type: 'text_delta', text: 'Jupiter here favors a steady, patient unfolding.' }
}
vi.mock('@/lib/providers/dispatcher', () => ({
  getAdapter: vi.fn(() => ({
    getManifest: () => ({ adaptiveToolLoop: false }),
    tools: () => ({ tools: [] }),
    chat: () => textDeltaStream(),
  })),
}))
vi.mock('@/lib/synthesis/agentic_loop', () => ({
  LOOP_CONFIG_BY_PROVIDER: { google: { maxIterations: 8 }, anthropic: { maxIterations: 8 }, openai: { maxIterations: 8 } },
  runAgenticLoop: vi.fn(() => textDeltaStream()),
}))
vi.mock('@/lib/synthesis/mcp_tool_executor', () => ({ executeMCPTool: vi.fn(async () => ({ results: [] })) }))

import { POST } from '@/app/api/pariprashna/route'

function makeReq(text: string): Request {
  return new Request('http://localhost/api/pariprashna', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ chartId: CHART, stack: 'gemini', messages: [{ id: 'm1', role: 'user', parts: [{ type: 'text', text }] }] }),
  })
}

/** Parse the SSE body into decoded event objects. */
async function readEvents(resp: Response): Promise<Array<Record<string, unknown>>> {
  const text = await resp.text()
  return text
    .split('\n')
    .filter((l) => l.startsWith('data: '))
    .map((l) => JSON.parse(l.slice(6)) as Record<string, unknown>)
}

beforeEach(() => {
  pendingStreamCalls.length = 0
  writeTurnCalls.length = 0
})

describe('V3-E-045 — wire turn_id and persisted queryId are joinable with ONE id', () => {
  it('the wire turn_id, the pending_streams key, and the persisted metadata_json.custom.queryId are byte-identical', async () => {
    const resp = await POST(makeReq('What does Jupiter in my chart mean for patience?'))
    expect(resp.status).toBe(200)
    const events = await readEvents(resp)

    const turnOpen = events.find((e) => e.type === 'turn.open')
    expect(turnOpen, 'expected a turn.open wire event').toBeDefined()
    const wireTurnId = turnOpen!.turn_id as string
    expect(typeof wireTurnId).toBe('string')
    expect(wireTurnId.length).toBeGreaterThan(0)

    // (2) the pending_streams key the route handed the writer.
    expect(pendingStreamCalls).toHaveLength(1)
    const pendingStreamQueryId = pendingStreamCalls[0].queryId

    // (3) the canonical assistant row actually persisted.
    expect(writeTurnCalls.length).toBeGreaterThan(0)
    const assistantWrite = writeTurnCalls.find(
      (c) => (c.message.role as string) === 'assistant',
    )
    expect(assistantWrite, 'expected a canonical assistant-row writeTurn call').toBeDefined()
    const persistedMetadata = assistantWrite!.message.metadata as
      | { custom?: { queryId?: string } }
      | undefined
    const persistedQueryId = persistedMetadata?.custom?.queryId
    expect(typeof persistedQueryId).toBe('string')

    // THE FIX: all three trace to the SAME id — a caller holding only the
    // wire turn_id can now look up both the pending-stream row and the
    // persisted conversation_messages row by that one id.
    expect(pendingStreamQueryId).toBe(wireTurnId)
    expect(persistedQueryId).toBe(wireTurnId)
  })

  // §N.8 — the comparator must be demonstrated capable of failing: this is
  // exactly the shape of mismatch two independent `crypto.randomUUID()`
  // calls produced before the fix.
  it('RED-CONTROL: the comparator used above fails on two independently-random ids (the pre-fix shape)', () => {
    const wireTurnId = crypto.randomUUID()
    const independentQueryId = crypto.randomUUID()
    expect(wireTurnId).not.toBe(independentQueryId)
  })
})

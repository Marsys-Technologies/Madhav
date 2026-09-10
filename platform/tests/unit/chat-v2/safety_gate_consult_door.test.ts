/**
 * PPR-12 SAFETY GATE — THE CONSULT DOOR (lane G1-A, round 3, M-4).
 *
 * ── WHY THIS FILE EXISTS ─────────────────────────────────────────────────────
 * The round-2 hardening wired `classifyTurnSafety` into `/api/pariprashna` and
 * `/api/mcp/prashna_ask`, and recorded a judgement that `/api/chat/consult` was
 * out of scope as a retiring legacy surface. Re-verification falsified that:
 *
 *   · `00_ARCHITECTURE/PARIPRASHNA_ASBUILT_BASELINE_v1_0.md` §1 (2026-08-18,
 *     one day before this branch) carries the STATIC_VERIFIED row: "PB-4
 *     cutover (default flip, consult retirement, flag deletion): NEVER RUN;
 *     consult/consume still the un-gated default."
 *   · The same table records `/api/pariprashna` as gated behind
 *     `PARIPRASHNA_ENABLED`, default `false` in code. The two doors round 2 DID
 *     gate are the optional ones; this is the one users hit.
 *   · `/api/chat/consume` 308-redirects here.
 *   · `platform/AGENTS.md` records no consult-retirement decision.
 *
 * ── WHAT IS PROVEN HERE, THAT A UNIT TEST OF THE GATE CANNOT ─────────────────
 *   • the hard stop happens BEFORE `callPipelinePlanner` — this route's FIRST
 *     LLM call — so PPR-12's "a blocked class must never build a retrieval
 *     plan" is enforced, not audited afterwards;
 *   • the withholding is a composed ANSWER on the ordinary UIMessage stream
 *     (200, the fixed prose as assistant text), not a 500 and not an error
 *     envelope the client has to interpret;
 *   • with the flag OFF — the shipped default — the route's behaviour on the
 *     most severe input there is does not change at all.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// ── The safety flag, mocked at its single read site ──────────────────────────
// Same reason as `prashna_ask/__tests__/route.test.ts`: `configService.setFlag`
// does not reach the safety module's own resolved instance from a route test.
const { safetyFlagState } = vi.hoisted(() => ({ safetyFlagState: { on: false } }))
vi.mock('@/lib/pariprashna/safety/flag', () => ({
  SAFETY_GATE_FLAG: 'PARIPRASHNA_SAFETY_GATE_ENABLED',
  isSafetyGateEnabled: () => safetyFlagState.on,
}))

vi.mock('server-only', () => ({}))
vi.mock('@/lib/retrieval/registry/catalog', () => ({}))

const { mockUser } = vi.hoisted(() => ({ mockUser: { uid: 'user-abc' } }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: vi.fn(async () => mockUser as never) }))

const CHART = '11111111-2222-3333-4444-555555555555'

const queryMock = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({
  query: queryMock,
  getPool: vi.fn(async () => {
    throw new Error('no pool in unit test')
  }),
}))

vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: vi.fn(async () => 'view') }))

vi.mock('@/lib/conversations', () => ({
  getConversation: vi.fn(async () => ({ id: 'conv-1', chart_id: CHART })),
  insertConversationWithId: vi.fn(async () => undefined),
  touchConversation: vi.fn(async () => undefined),
  setConversationTitle: vi.fn(async () => undefined),
}))

vi.mock('@/lib/models/runtime_config', () => ({ getEffectiveModel: vi.fn(async () => 'fake-model') }))

vi.mock('@/lib/bundle/manifest_reader', () => ({ loadManifest: vi.fn(async () => ({})) }))
vi.mock('@/lib/retrieval/orientation', () => ({ buildChartOrientation: vi.fn(async () => null) }))

const { mockPlanner } = vi.hoisted(() => ({ mockPlanner: vi.fn() }))
vi.mock('@/lib/pipeline/pipeline_planner', () => ({ callPipelinePlanner: mockPlanner }))

import { POST } from '@/app/api/chat/consult/route'
import { HS2_FIXED_RESPONSE, SEAL_PENDING_ACKNOWLEDGMENT } from '@/lib/pariprashna/safety/fixed_responses'

function makeReq(text: string): Request {
  return new Request('http://localhost/api/chat/consult', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chartId: CHART,
      conversationId: 'conv-1',
      messages: [{ role: 'user', parts: [{ type: 'text', text }] }],
    }),
  })
}

/** The planner outcome shape the route needs to keep going past the gate. */
function clarificationOutcome() {
  return {
    outcome: 'clarification_needed' as const,
    question: 'Which domain?',
    missing_scope_dims: [],
    suggested_options: [],
  }
}

beforeEach(() => {
  safetyFlagState.on = false
  mockPlanner.mockReset()
  // The route's chart + profile lookup, then anything the safety audit writes.
  queryMock.mockReset()
  queryMock.mockImplementation(async (sql: string) => {
    if (typeof sql === 'string' && sql.includes('FROM charts')) {
      return {
        rows: [
          {
            id: CHART,
            name: 'Test',
            birth_date: '1984-02-05',
            birth_time: '10:43',
            birth_place: 'Bhubaneswar',
            client_id: mockUser.uid,
          },
        ],
      }
    }
    if (typeof sql === 'string' && sql.includes('FROM profiles')) return { rows: [{ role: 'guest' }] }
    return { rows: [] }
  })
})

afterEach(() => {
  safetyFlagState.on = false
})

async function bodyText(res: Response): Promise<string> {
  return await res.text()
}

describe('PPR-12 safety gate — the consult door is gated at all', () => {
  it('the route source references the gate (it referenced nothing before M-4)', async () => {
    const fs = await import('node:fs')
    const path = await import('node:path')
    const src = fs.readFileSync(
      path.resolve(import.meta.dirname, '../../../src/app/api/chat/consult/route.ts'),
      'utf8',
    )
    expect(src).toContain('classifyTurnSafety')
    // ...and it is placed before the planner call, not after it.
    expect(src.indexOf('classifyTurnSafety')).toBeLessThan(src.indexOf('await runPlanner('))
  })
})

describe('PPR-12 safety gate (consult door) — flag OFF is a no-op', () => {
  it('a crisis question runs untouched with the flag off (the shipped default)', async () => {
    mockPlanner.mockResolvedValue(clarificationOutcome())
    const res = await POST(makeReq('I want to kill myself.'))
    expect(res.status).toBe(200)
    // THE assertion: the planner ran. The gate changed nothing.
    expect(mockPlanner).toHaveBeenCalledTimes(1)
    const body = await bodyText(res)
    expect(body).not.toContain(HS2_FIXED_RESPONSE.slice(0, 40))
  })
})

describe('PPR-12 safety gate (consult door) — flag ON', () => {
  it('HS-2 hard stop: refused BEFORE the planner, with the fixed prose', async () => {
    safetyFlagState.on = true
    mockPlanner.mockResolvedValue(clarificationOutcome())

    const res = await POST(makeReq('I want to kill myself.'))

    expect(res.status).toBe(200)
    expect(res.status).not.toBe(500)
    // "a blocked class must never build a retrieval plan" — the planner is this
    // route's first LLM call, and it never ran.
    expect(mockPlanner).not.toHaveBeenCalled()

    const body = await bodyText(res)
    // The fixed prose is streamed as assistant text. Compared on its first
    // line so the assertion survives SSE chunking and JSON escaping of the
    // newlines inside the full block.
    expect(body).toContain(HS2_FIXED_RESPONSE.split('\n')[0])
    expect(body).toContain('safety_reading_withheld')
    expect(body).toContain('safety_decision:hard_stop')
  })

  it('the evaded spelling is stopped too (the M-2 surface, through the real door)', async () => {
    safetyFlagState.on = true
    mockPlanner.mockResolvedValue(clarificationOutcome())
    const res = await POST(makeReq('how do i k1ll myse1f'))
    expect(mockPlanner).not.toHaveBeenCalled()
    expect(await bodyText(res)).toContain('safety_decision:hard_stop')
  })

  it('HS-4 mortality window: sealed before the planner, with the acknowledgment', async () => {
    safetyFlagState.on = true
    mockPlanner.mockResolvedValue(clarificationOutcome())

    const res = await POST(makeReq('When will I die? Give me the year of my death.'))

    expect(res.status).toBe(200)
    expect(mockPlanner).not.toHaveBeenCalled()
    const body = await bodyText(res)
    expect(body).toContain(SEAL_PENDING_ACKNOWLEDGMENT.split('\n')[0])
    expect(body).toContain('safety_decision:seal_pending_signoff')
  })

  it('THE FLOOR: an ordinary question still reaches the planner with the flag ON', async () => {
    // A safety gate that refuses ordinary work is not a safe gate.
    safetyFlagState.on = true
    mockPlanner.mockResolvedValue(clarificationOutcome())

    const res = await POST(makeReq('What does my chart say about my career this year?'))

    expect(res.status).toBe(200)
    expect(mockPlanner).toHaveBeenCalledTimes(1)
    expect(await bodyText(res)).not.toContain('safety_reading_withheld')
  })

  it('never the matched text and never the rule ids on the wire', async () => {
    // Gate 11 [integrity], the discipline both other doors keep.
    safetyFlagState.on = true
    mockPlanner.mockResolvedValue(clarificationOutcome())
    const res = await POST(makeReq('I want to kill myself.'))
    const body = await bodyText(res)
    expect(body).not.toContain('kill myself')
    expect(body).not.toMatch(/hs2_suicide_adjacent/)
  })
})

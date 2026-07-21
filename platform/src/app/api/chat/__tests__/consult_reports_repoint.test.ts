/**
 * WP-1.1 / LCA-2 — Consult orchestration smoke matrix + honest-error regression.
 *
 * Defect (LCA-2, CRITICAL): consult/route.ts unconditionally SELECTed from the
 * retired `reports` relation (DDL lives only in platform/migrations/_archive,
 * ABSENT from deployed Cloud SQL). The resulting permanent 42P01
 * (undefined_table) was caught and dishonestly mapped to
 * SYSTEM_DB_UNAVAILABLE {retry:true} — taking down the flagship consult surface
 * for EVERY chart. The `reportsResult` value was never consumed.
 *
 * This suite is the PERMANENT regression guard for the three-part fix:
 *
 *   1. Re-point off `reports`: the route must NEVER issue a `FROM reports`
 *      query. Consult content flows from the planner + retrieval tool path
 *      (bodha_* signals etc.) — the same live surfaces the MCP tools use.
 *
 *   2. Honest error class: a permanent missing-relation / schema fault (SQLSTATE
 *      class 42 / 3F) must NOT map to the transient SYSTEM_DB_UNAVAILABLE
 *      {retry:true}. A genuinely transient DB fault still may.
 *
 *   3. Smoke matrix: both charts × {orientation, domain, timing} reach a
 *      successful (200) stream carrying chart-correct content — never a 500,
 *      never an empty-dishonest 503.
 *
 * The real POST handler is driven end-to-end; only the LLM planner and the
 * adapter-dispatch tail are mocked. `runAdapterDispatch` echoes the resolved
 * chartId, the planner query_class, and the live-surface tool content it was
 * handed, so the matrix proves the route reaches dispatch with chart-correct
 * context (the bug prevented that) rather than asserting on LLM prose.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const NATIVE = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHI = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

// ── Test-controlled state shared with the mocks ────────────────────────────────
const issuedSql: string[] = []
let chartLookupError: { code?: string; message?: string } | null = null

// ── Boundary mocks ─────────────────────────────────────────────────────────────
vi.mock('@/lib/firebase/server', () => ({
  getServerUser: vi.fn(async () => ({ uid: 'tester-uid' })),
}))

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string, params?: unknown[]) => {
    issuedSql.push(sql)
    if (/from charts/i.test(sql)) {
      if (chartLookupError) throw chartLookupError
      const id = params?.[0] as string
      const name = id === NATIVE ? 'Abhisek Mohanty' : 'Abhinandan Mohanty'
      return {
        rows: [{ id, name, birth_date: '1984-02-05', birth_time: '10:43', birth_place: 'Bhubaneswar', client_id: 'tester-uid' }],
      }
    }
    if (/from profiles/i.test(sql)) return { rows: [{ role: 'super_admin' }] }
    // build_events / build_checkpoints readiness probes — empty is fine (non-fatal).
    return { rows: [] }
  }),
}))

vi.mock('@/lib/auth/authorizeChartAccess', () => ({
  authorizeChartAccess: vi.fn(async () => 'view'),
}))

vi.mock('@/lib/conversations', () => ({
  getConversation: vi.fn(async () => null),
  insertConversationWithId: vi.fn(async () => undefined),
  updateConversationTitle: vi.fn(async () => undefined),
}))

vi.mock('@/lib/persistence/pending_streams_writer', () => ({
  createPendingStreamWriter: vi.fn(() => ({})),
}))

vi.mock('@/lib/bundle/manifest_reader', () => ({
  loadManifest: vi.fn(async () => ({ fingerprint: 'test-fp' })),
}))

vi.mock('@/lib/pipeline/pipeline_planner', () => ({
  PlannerFault: class PlannerFault extends Error {},
  // W4: callPipelinePlanner now returns a 3-way PlannerOutcome. The success
  // variant is a PlanReceipt `{ outcome: 'plan', plan }` — route.ts unwraps `.plan`.
  callPipelinePlanner: vi.fn(async (queryText: string) => {
    const q = String(queryText).toLowerCase()
    const query_class =
      /\b(when|timing|dasha|next|month|year|period|transit)\b/.test(q)
        ? 'predictive'
        : /\b(orient|overview|who am i|whole|summary|introduce|tell me about (my|the) chart)\b/.test(q)
          ? 'holistic'
          : 'interpretive'
    return {
      outcome: 'plan' as const,
      plan: {
        query_class,
        domains: ['career'],
        forward_looking: query_class === 'predictive',
        // includes an L2.5 tool (msr_sql) so the B.11 floor is already satisfied.
        tool_calls: [{ tool_name: 'msr_sql', params: {}, token_budget: 600, priority: 1 as const, reason: 'test' }],
      },
    }
  }),
}))

vi.mock('@/lib/bundle/bundle_hydrator', () => ({
  hydrateBundle: vi.fn(async () => ({ assets: [], floor_enforced: false })),
}))

vi.mock('@/lib/retrieval/registry/tool_name_bridge', () => ({
  getToolByName: vi.fn((name: string) => ({ name })),
}))

vi.mock('@/lib/cache/index', () => ({
  createToolCache: vi.fn(() => ({})),
  // Non-empty, chart-agnostic live-surface stand-in: a real MSR signal snippet.
  executeWithCache: vi.fn(async () => ({
    results: [{ content: 'SIG.MSR.142 — dispositor chain governs career timing.', signal_id: 'SIG.MSR.142' }],
  })),
}))

vi.mock('@/lib/validators/index', () => ({
  runAll: vi.fn(async () => []),
  summarize: vi.fn(() => ({ overall: 'pass', failures: [] })),
}))

vi.mock('@/lib/config/index', () => ({
  configService: { getFlag: vi.fn(() => false) },
}))

vi.mock('@/lib/models/runtime_config', () => ({
  getEffectiveModel: vi.fn(async () => 'gemini-2.5-pro'),
}))

vi.mock('@/lib/db/monitoring-write', () => ({
  writeLlmCallLog: vi.fn(),
  writeQueryPlanLog: vi.fn(),
  writeToolExecutionLog: vi.fn(),
  writeContextAssemblyLog: vi.fn(),
  resolveProvider: vi.fn(() => 'google'),
}))

vi.mock('@/lib/trace/emitter', () => ({
  traceEmitter: { emitStep: vi.fn() },
}))

vi.mock('@/lib/personas', () => ({
  getPersonaForSynthesis: vi.fn(async () => null),
}))

vi.mock('@/lib/projects', () => ({
  getProjectForConversation: vi.fn(async () => null),
}))

// Terminal echo: the route reaching this with chart-correct context is the very
// thing the `reports` bug prevented. We stamp the resolved chartId, the planner
// query_class, and the live-surface tool content into the response body.
// vi.hoisted so both the (hoisted) mock factory and the test body share the spy.
const { dispatchSpy } = vi.hoisted(() => ({
  dispatchSpy: vi.fn(async (ctx: Record<string, unknown>) => {
    const toolResults = (ctx.validToolResults as Array<{ results: Array<{ content: string }> }>) ?? []
    const tool_content = toolResults.flatMap(b => b.results.map(r => r.content)).join(' | ')
    const plan = ctx.plan as { query_class: string }
    const body = JSON.stringify({
      chartId: ctx.chartId,
      query_class: plan.query_class,
      query_text: ctx.queryText,
      tool_content,
    })
    return new Response(body, { status: 200, headers: { 'content-type': 'application/json' } })
  }),
}))
vi.mock('@/lib/pipelines/shared', () => ({
  runAdapterDispatch: dispatchSpy,
}))

// Import AFTER mocks are registered.
import { POST } from '../consult/route'

function makePost(chartId: string, text: string): Request {
  return new Request('http://localhost/api/chat/consult', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      chartId,
      messages: [{ id: 'm1', role: 'user', parts: [{ type: 'text', text }] }],
    }),
  })
}

const QUESTION_MATRIX: Array<{ kind: string; text: string; expectClass: string }> = [
  { kind: 'orientation', text: 'Give me an orientation overview of my whole chart.', expectClass: 'holistic' },
  { kind: 'domain', text: 'What does my chart say about my career and profession?', expectClass: 'interpretive' },
  { kind: 'timing', text: 'When in the next year does my dasha period favour a career move?', expectClass: 'predictive' },
]

beforeEach(() => {
  issuedSql.length = 0
  chartLookupError = null
  dispatchSpy.mockClear()
})

describe('WP-1.1 / LCA-2 — consult smoke matrix (both charts × 3 question types)', () => {
  for (const chart of [
    { id: NATIVE, label: 'native (Abhisek)' },
    { id: ABHI, label: 'Abhinandan' },
  ]) {
    for (const q of QUESTION_MATRIX) {
      it(`${chart.label} · ${q.kind}: returns 200 with chart-correct content, no reports SELECT`, async () => {
        const resp = await POST(makePost(chart.id, q.text))

        // Not a 500, not an empty-dishonest 503 — the bug produced 503.
        expect(resp.status).toBe(200)

        const payload = (await resp.json()) as {
          chartId: string
          query_class: string
          tool_content: string
        }
        // Chart-correct: the resolved chartId echoed by dispatch matches the request.
        expect(payload.chartId).toBe(chart.id)
        // Question-type routing survived to the planner query_class.
        expect(payload.query_class).toBe(q.expectClass)
        // Live-surface (retrieval) content flowed through — not empty.
        expect(payload.tool_content).toContain('SIG.MSR.142')

        // The retired `reports` relation is never touched.
        expect(issuedSql.some(s => /from\s+reports\b/i.test(s))).toBe(false)
        // And the live chart lookup DID run.
        expect(issuedSql.some(s => /from\s+charts\b/i.test(s))).toBe(true)

        expect(dispatchSpy).toHaveBeenCalledTimes(1)
      })
    }
  }
})

describe('WP-1.1 / LCA-2 — honest error classification', () => {
  it('permanent missing-relation error (42P01) → 500 SYSTEM_INTERNAL, NOT 503 retry:true', async () => {
    chartLookupError = { code: '42P01', message: 'relation "reports" does not exist' }

    const resp = await POST(makePost(NATIVE, 'orientation please'))
    expect(resp.status).toBe(500)

    const body = (await resp.json()) as { error: { code: string; retry?: boolean } }
    expect(body.error.code).toBe('SYSTEM_INTERNAL')
    // The core dishonesty being fixed: a permanent fault must not claim retryability.
    expect(body.error.retry).not.toBe(true)
  })

  it('undefined_column error (42703) is also classified permanent → 500, not retryable', async () => {
    chartLookupError = { code: '42703', message: 'column "foo" does not exist' }

    const resp = await POST(makePost(ABHI, 'orientation please'))
    expect(resp.status).toBe(500)
    const body = (await resp.json()) as { error: { code: string; retry?: boolean } }
    expect(body.error.code).toBe('SYSTEM_INTERNAL')
    expect(body.error.retry).not.toBe(true)
  })

  it('genuinely transient DB fault still maps to 503 SYSTEM_DB_UNAVAILABLE {retry:true}', async () => {
    // 57P03 = cannot_connect_now — a real transient class outside 42/3F.
    chartLookupError = { code: '57P03', message: 'the database system is starting up' }

    const resp = await POST(makePost(NATIVE, 'orientation please'))
    expect(resp.status).toBe(503)
    const body = (await resp.json()) as { error: { code: string; retry?: boolean } }
    expect(body.error.code).toBe('SYSTEM_DB_UNAVAILABLE')
    expect(body.error.retry).toBe(true)
  })
})

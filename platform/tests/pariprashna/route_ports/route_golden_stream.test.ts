/**
 * P0-C / RF-1 — THE GOLDEN-STREAM SEMANTIC-EQUALITY HARNESS for
 * `/api/pariprashna`.
 *
 * WHY IT EXISTS
 * ─────────────
 * RF-1 decomposes a 1,179-line live streaming route into typed stage modules
 * and claims the result is behaviour-identical. Per CLAUDE.md §N.8 (Earned-
 * Signal Principle) that claim is only worth anything if a detector exists that
 * would return FALSE when it is untrue. This file is that detector.
 *
 * HOW IT WORKS
 * ────────────
 *  1. `scenarios.ts` describes N runs of the route: request body, auth/flag/DB
 *     world, planner outcome, retrieval outcomes, and the exact adapter event
 *     sequence synthesis yields.
 *  2. Every I/O boundary is mocked and RECORDS its calls in order; the route's
 *     own logic (plan mutation, budget arbitration, floor composition, the REAL
 *     NO-LEAKAGE filter, block/pass/seam state machine, the REAL register-leak
 *     lint, the REAL citation extractor + prediction detector, the canonical
 *     part assembly, the REAL onFinish write-through) runs unmocked.
 *  3. The run produces a GoldenRecord: HTTP status + headers, the ordered wire
 *     events, and the ordered boundary side-effects.
 *  4. The record is compared against a committed baseline under `baseline/`.
 *
 * The baselines in `baseline/` were captured against the UNMODIFIED route (git
 * history proves the ordering: the baseline commit precedes the decomposition
 * commit). Regenerate ONLY with an explicit intent to move the contract:
 *
 *     PARIPRASHNA_PORTS_BASELINE=write npx vitest run tests/pariprashna/route_ports
 *
 * DETERMINISM
 * ───────────
 * `crypto.randomUUID` is replaced by a counter, so id VALUES and the ORDER the
 * route mints them are both part of the record. Wall-clock numerics (`t`, `ms`,
 * `*_ms`) are the only excused fields — see `normalize.ts`, which states the
 * comparison contract in code.
 *
 * NOT PROVEN BY THIS FILE (stated so nobody over-reads a green run)
 * ────────────────────────────────────────────────────────────────
 *  · No real deployed stream is in the corpus. RF-1's "+ captured real streams"
 *    needs `PARIPRASHNA_STREAM_CAPTURE=1` on a deployed environment.
 *  · Behaviour of the mocked collaborators themselves is out of scope — this
 *    proves the ROUTE's orchestration is unchanged, not that the planner or the
 *    adapter are correct.
 *  · Real DB/transaction semantics of `writeTurn` are not exercised (the DB
 *    suites under `tests/pariprashna/samiksha/*.db.test.ts` own that).
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs'
import { join } from 'path'

import {
  ROUTE_SCENARIOS,
  FIXTURE_CORPUS_NAMES,
  HARNESS_SCOPE_TUPLE,
  type RouteScenario,
  type AdapterStep,
} from './scenarios'
import { diffRecords, serializeRecord, type GoldenRecord } from './normalize'

// ─────────────────────────────────────────────────────────────────────────────
// The mutable world every mock reads. Hoisted so vi.mock factories can close
// over it (they are hoisted above the imports).
// ─────────────────────────────────────────────────────────────────────────────
const { world } = vi.hoisted(() => ({
  world: {
    scenario: null as RouteScenario | null,
    sideEffects: [] as Array<Record<string, unknown>>,
    abort: null as null | (() => void),
  },
}))

function rec(fn: string, args: Record<string, unknown> = {}): void {
  world.sideEffects.push({ fn, ...args })
}

// ── auth / flags / config ────────────────────────────────────────────────────
vi.mock('@/lib/firebase/server', () => ({
  getServerUser: vi.fn(async () => (world.scenario?.authenticated === false ? null : { uid: 'harness-uid' })),
}))
vi.mock('@/lib/config/index', () => ({
  configService: {
    getFlag: vi.fn((k: string) => {
      if (k === 'PARIPRASHNA_ENABLED') return world.scenario?.flagEnabled !== false
      if (k === 'CITATION_GATE_OVERRIDE') return false
      return false
    }),
  },
}))
vi.mock('@/lib/models/runtime_config', () => ({
  getEffectiveModel: vi.fn(async (_stack: string, role: string, tier: string) =>
    role === 'synthesis' ? 'gemini-2.5-pro' : `planner-${tier}`,
  ),
}))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({
  authorizeChartAccess: vi.fn(async () => world.scenario?.permission ?? 'view'),
}))

// ── DB ───────────────────────────────────────────────────────────────────────
vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string, params?: unknown[]) => {
    if (/from charts/i.test(sql)) {
      if (world.scenario?.throwOnChartQuery) throw new Error('harness: charts SELECT exploded')
      if (world.scenario?.chartFound === false) return { rows: [] }
      return { rows: [{ id: (params?.[0] as string) ?? '', name: 'Harness Native', client_id: 'harness-uid' }] }
    }
    if (/from profiles/i.test(sql)) return { rows: [{ role: 'guest' }] }
    if (/bodha_msr_signals/i.test(sql)) {
      const snips = world.scenario?.msrSnippets ?? {}
      const ids = (params ?? []) as string[]
      return {
        rows: ids
          .filter((id) => snips[id])
          .map((id) => ({ signal_id: id, name: snips[id].name, description: snips[id].description })),
      }
    }
    return { rows: [] }
  }),
}))

// ── conversations ────────────────────────────────────────────────────────────
vi.mock('@/lib/conversations', () => ({
  getConversation: vi.fn(async ({ id }: { id: string }) => {
    const mode = world.scenario?.existingConversation ?? 'missing'
    if (mode === 'missing') return null
    if (mode === 'chart-mismatch') return { id, chart_id: 'other-chart' }
    return { id, chart_id: world.scenario?.body?.chartId as string }
  }),
  insertConversationWithId: vi.fn(async (args: Record<string, unknown>) => {
    rec('insertConversationWithId', { id: args.id, chartId: args.chartId, module: args.module })
    const e = world.scenario?.insertConversationError
    if (e === 'duplicate') throw new Error('duplicate key value violates unique constraint')
    if (e === 'fatal') throw new Error('connection refused')
  }),
  updateConversationTitle: vi.fn(async (cid: string, t: string) => {
    rec('updateConversationTitle', { cid, t })
  }),
}))
vi.mock('@/lib/conversations/title', () => ({
  generateConversationTitle: vi.fn(async () => {
    rec('generateConversationTitle')
    return 'Harness Title'
  }),
}))
vi.mock('@/lib/persistence/conversation_writer', () => ({
  writeConversationMessages: vi.fn(async (args: { conversationId: string; messages: unknown[] }) => {
    rec('writeConversationMessages', { conversationId: args.conversationId, count: args.messages.length })
    return { verified: true, messageIds: ['history-msg-1'] }
  }),
}))
vi.mock('@/lib/persistence/pending_streams_writer', () => ({
  createPendingStreamWriter: vi.fn((queryId: string, conversationId: string) => {
    rec('createPendingStreamWriter', { queryId, conversationId })
    return {
      clear: () => {
        rec('pendingStreamWriter.clear')
      },
    }
  }),
}))
vi.mock('@/lib/db/monitoring-write', () => ({
  writeContextAssemblyLog: vi.fn((entry: Record<string, unknown>) => {
    rec('writeContextAssemblyLog', { entry })
  }),
}))

// ── manifest / orientation / bundle ──────────────────────────────────────────
vi.mock('@/lib/bundle/manifest_reader', () => ({
  loadManifest: vi.fn(async () => ({ fingerprint: 'harness-manifest-fp' })),
}))
vi.mock('@/lib/retrieval/orientation', () => ({
  buildChartOrientation: vi.fn(async () => ({
    chart_header: { current_maha_antar: 'Ketu–Venus' },
    dasha_context: { current_maha_antar: 'Ketu–Venus' },
  })),
}))
vi.mock('@/lib/bundle/bundle_hydrator', () => ({
  hydrateBundle: vi.fn(async () => ({ assets: [{ content: 'HARNESS-BUNDLE-ASSET' }], floor_enforced: false })),
}))

// ── planner ──────────────────────────────────────────────────────────────────
vi.mock('@/lib/pipeline/pipeline_planner', () => ({
  PlannerFault: class PlannerFault extends Error {},
  callPipelinePlanner: vi.fn(async (queryText: string) => {
    const s = world.scenario!
    rec('callPipelinePlanner', { queryText })
    if (s.planner.outcome === 'clarification_needed') {
      return { outcome: 'clarification_needed' as const, question: s.planner.question }
    }
    if (s.planner.outcome === 'fault') {
      return { outcome: 'fault' as const, reason: s.planner.reason, retryable: s.planner.retryable }
    }
    return {
      outcome: 'plan' as const,
      plan: {
        query_class: s.planner.queryClass ?? 'holistic',
        domains: s.planner.domains ?? ['career'],
        forward_looking: false,
        history_mode: 'synthesized',
        panel_mode: false,
        expected_output_shape: 'three_interpretation',
        synthesis_guidance: 'Answer as an acharya.',
        ...(s.planner.withScopeTuple ? { scope_tuple: { ...HARNESS_SCOPE_TUPLE } } : {}),
        tool_calls: (s.planner.toolCalls ?? []).map((tc) => ({ ...tc, params: {}, reason: 'harness' })),
      },
    }
  }),
}))

// Floor adapters: no-op, so the authorized set is exactly what the planner named.
vi.mock('@/lib/pipeline/compiled_floor_adapter', () => ({
  compileFloorForPlan: vi.fn(() => ({
    toolCalls: [],
    mappedPrimitives: [],
    unmappedPrimitives: [],
    compilerIntent: 'general_synthesis',
    compileFailed: false,
  })),
  ensureB11WholeChartReadFloor: vi.fn(() => false),
  ensureDashaContextFloor: vi.fn(() => false),
}))

// ── retrieval dispatch ───────────────────────────────────────────────────────
vi.mock('@/lib/retrieval/registry/tool_name_bridge', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/retrieval/registry/tool_name_bridge')>()
  return {
    ...actual,
    getToolByName: vi.fn((name: string) =>
      world.scenario?.toolOutcomes?.[name] === 'unknown-tool' ? undefined : { name },
    ),
  }
})
vi.mock('@/lib/cache/index', () => ({
  createToolCache: vi.fn(() => ({})),
  executeWithCache: vi.fn(async (t: { name: string }) => {
    const outcome = world.scenario?.toolOutcomes?.[t.name]
    rec('executeWithCache', { tool: t.name })
    if (outcome === 'error') throw new Error(`harness: ${t.name} failed`)
    const n = typeof outcome === 'number' ? outcome : 0
    return {
      tool_bundle_id: `tb-${t.name}`,
      tool_name: t.name,
      tool_version: '1.0',
      invocation_params: {},
      results: Array.from({ length: n }, (_, i) => ({ content: `result-${t.name}-${i}` })),
      served_from_cache: false,
      latency_ms: 1,
      result_hash: `sha256:${t.name}`,
      schema_version: '1.0' as const,
    }
  }),
}))
vi.mock('@/lib/retrieval/qos/dispatch_queue', () => ({
  getSharedQosDispatchQueue: vi.fn(() => ({
    submit: async <T>(task: { run: () => Promise<T> }) => task.run(),
  })),
}))

// ── synthesis prefix builders ────────────────────────────────────────────────
vi.mock('@/lib/pipelines/shared/run_adapter_dispatch', () => ({
  buildConsultSystemContent: vi.fn((args: Record<string, unknown>) => {
    rec('buildConsultSystemContent', {
      bundleSystemContent: args.bundleSystemContent,
      synthesisGuidance: args.synthesisGuidance,
      currentMahaAntar: args.currentMahaAntar,
      nowContextDateShape: typeof args.nowContextDate,
    })
    return 'HARNESS-SYSTEM-CONTENT'
  }),
}))
vi.mock('@/lib/pariprashna/summaries/splice', () => ({
  getConversationSummaryForSplice: vi.fn(async (cid: string) => {
    rec('getConversationSummaryForSplice', { cid })
    return null
  }),
}))
vi.mock('@/lib/pariprashna/summaries/assemble', () => ({
  assembleSynthesisPrefix: vi.fn(({ precedingBlock, summaryText }: { precedingBlock: string; summaryText: string | null }) => {
    rec('assembleSynthesisPrefix', { precedingBlock, summaryText })
    return precedingBlock
  }),
}))

// ── adapter + agentic loop ───────────────────────────────────────────────────
async function* adapterEvents(): AsyncGenerator<Record<string, unknown>> {
  const steps: AdapterStep[] = world.scenario?.adapter ?? []
  for (const step of steps) {
    switch (step.kind) {
      case 'text':
        yield { type: 'text_delta', text: step.text }
        break
      case 'thinking':
        yield { type: 'thinking_delta', thinking: step.text }
        break
      case 'tool_start':
        yield { type: 'tool_use_start', id: step.id, name: step.name }
        break
      case 'tool_complete':
        yield { type: 'tool_use_complete', id: step.id, name: step.name }
        break
      case 'error':
        yield { type: 'error', error: step.error }
        break
      case 'throw':
        throw new Error(step.message)
      case 'abort':
        world.abort?.()
        break
    }
  }
}

vi.mock('@/lib/providers/dispatcher', () => ({
  getAdapter: vi.fn((id: string) => {
    rec('getAdapter', { id })
    return {
      getManifest: () => ({ adaptiveToolLoop: true }),
      tools: (cfg: Record<string, unknown>) => {
        rec('adapter.tools', { maxIterations: cfg.maxIterations, toolLoopMode: cfg.toolLoopMode })
        return { tools: [] }
      },
      chat: () => {
        rec('adapter.chat')
        return adapterEvents()
      },
    }
  }),
}))
vi.mock('@/lib/synthesis/agentic_loop', () => ({
  LOOP_CONFIG_BY_PROVIDER: new Proxy({} as Record<string, unknown>, {
    get: (_t, prop: string) =>
      world.scenario?.disableLoopConfig ? undefined : { provider: prop, maxIterations: 8 },
  }),
  runAgenticLoop: vi.fn((_adapter: unknown, _req: unknown, _exec: unknown, cfg: { maxIterations: number }) => {
    rec('runAgenticLoop', { maxIterations: cfg.maxIterations })
    return adapterEvents()
  }),
}))
vi.mock('@/lib/synthesis/mcp_tool_executor', () => ({
  executeMCPTool: vi.fn(async () => ({ results: [] })),
}))

// ── citation gate ────────────────────────────────────────────────────────────
vi.mock('@/lib/synthesis/streaming_citation_validator', () => ({
  validateCitationsForStream: vi.fn((text: string, contextJson: string, queryClass: string, override: boolean) => {
    rec('validateCitationsForStream', {
      text,
      contextJsonLength: contextJson.length,
      queryClass,
      override,
    })
    if (world.scenario?.citationGateThrows) throw new Error('harness: citation gate exploded')
    return (
      world.scenario?.citationGate ?? {
        gateResult: 'PASS' as const,
        gateReason: 'harness pass',
        layer1Count: 2,
        layer2Verified: 2,
      }
    )
  }),
}))

// ── protocol side channels (ring buffer + stream capture) ────────────────────
vi.mock('@/lib/pariprashna/protocol/ring_buffer', () => ({
  openTurnBuffer: vi.fn(async (args: Record<string, unknown>) => {
    rec('openTurnBuffer', { turnId: args.turnId, chartId: args.chartId, conversationId: args.conversationId })
  }),
  appendBufferedEvent: vi.fn(async (turnId: string, event: { type: string; seq: number }) => {
    rec('appendBufferedEvent', { turnId, type: event.type, seq: event.seq })
  }),
}))
vi.mock('@/lib/pariprashna/protocol/stream_capture', () => ({
  beginTurnCapture: vi.fn((args: Record<string, unknown>) => {
    rec('beginTurnCapture', { turnId: args.turnId })
  }),
  captureEvent: vi.fn(async (turnId: string, event: { type: string; seq: number }) => {
    rec('captureEvent', { turnId, type: event.type, seq: event.seq })
  }),
  endTurnCapture: vi.fn((turnId: string) => {
    rec('endTurnCapture', { turnId })
  }),
}))

// ── provenance (compute mocked, drift detection REAL) ────────────────────────
vi.mock('@/lib/pariprashna/provenance/stamp', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/pariprashna/provenance/stamp')>()
  const stamp = (buildId: string) => ({
    build_id: buildId,
    priors_version: 'v3',
    formula_versions: { salience_formula_ver: null },
    ranking_config: { mode: 'harness' },
    now_context_date: '2026-08-19',
    computed_at: '2026-08-19T00:00:00.000Z',
  })
  return {
    ...actual,
    computeTurnProvenanceStamp: vi.fn(async () => {
      rec('computeTurnProvenanceStamp')
      return stamp('build-current')
    }),
    getLastTurnStamp: vi.fn(async () => {
      rec('getLastTurnStamp')
      return world.scenario?.provenanceDrift ? stamp('build-previous') : null
    }),
  }
})

// ── canonical store + samiksha ───────────────────────────────────────────────
vi.mock('@/lib/pariprashna/store/writer', () => ({
  writeTurn: vi.fn(async (message: Record<string, unknown>, parts: unknown[]) => {
    rec('writeTurn', { message, parts })
    return { message_id: message.id as string, parts_written: parts.length }
  }),
}))
vi.mock('@/lib/pariprashna/samiksha/capture', () => ({
  captureDetectedCandidates: vi.fn(async (args: Record<string, unknown>) => {
    rec('captureDetectedCandidates', {
      chartId: args.chartId,
      messageId: args.messageId,
      candidates: args.candidates,
      citations: args.citations,
      nowDate: args.nowDate,
    })
    return { created: [], skippedExisting: 0, unpaired: 0 }
  }),
}))

// ── pricing (synthUsage is null in this route, so this is a no-op path) ──────
vi.mock('@/lib/llm/pricing', () => ({
  getModelPricingSync: vi.fn(() => null),
  computeCostUsd: vi.fn(() => 0),
}))

// ═════════════════════════════════════════════════════════════════════════════
import { POST } from '@/app/api/pariprashna/route'

const BASELINE_DIR = join(__dirname, 'baseline')
const WRITE_MODE = process.env.PARIPRASHNA_PORTS_BASELINE === 'write'

let uuidCounter = 0
let originalRandomUUID: typeof crypto.randomUUID

beforeEach(() => {
  world.scenario = null
  world.sideEffects = []
  world.abort = null
  uuidCounter = 0
  originalRandomUUID = crypto.randomUUID.bind(crypto)
  vi.spyOn(crypto, 'randomUUID').mockImplementation(
    () => `00000000-0000-4000-8000-${String(++uuidCounter).padStart(12, '0')}` as `${string}-${string}-${string}-${string}-${string}`,
  )
})

afterEach(() => {
  vi.restoreAllMocks()
  crypto.randomUUID = originalRandomUUID
})

/** Parse an SSE body into decoded event objects. */
function parseSse(text: string): Array<Record<string, unknown>> {
  return text
    .split('\n')
    .filter((l) => l.startsWith('data: '))
    .map((l) => JSON.parse(l.slice(6)) as Record<string, unknown>)
}

async function runScenario(s: RouteScenario): Promise<GoldenRecord> {
  world.scenario = s
  world.sideEffects = []
  // Reset the deterministic id counter per RUN (not per test) so a test that
  // runs the same scenario twice compares like with like.
  uuidCounter = 0

  const ac = new AbortController()
  world.abort = () => ac.abort()

  const body = s.rawBody ?? JSON.stringify(s.body ?? {})
  const request = new Request('http://localhost/api/pariprashna', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body,
    signal: ac.signal,
  })

  const resp = await POST(request)
  const text = await resp.text()
  const isSse = (resp.headers.get('content-type') ?? '').includes('event-stream')

  return {
    scenario: s.name,
    derived_from: s.derived_from,
    http: {
      status: resp.status,
      headers: Object.fromEntries([...resp.headers.entries()].sort()),
    },
    events: isSse ? parseSse(text) : [{ non_stream_body: safeJson(text) }],
    side_effects: world.sideEffects,
  }
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

function baselinePath(name: string): string {
  return join(BASELINE_DIR, `${name}.json`)
}

// ═════════════════════════════════════════════════════════════════════════════
// The corpus contract — asserted, not assumed.
// ═════════════════════════════════════════════════════════════════════════════
describe('P0-C golden-stream harness — corpus contract', () => {
  it('covers all 12 fixture-corpus names exactly once', () => {
    const fixtureNames = [
      '1-byte-trickle', '3s-stall', 'adaptive-3-pass', 'citation-dense',
      'disconnect-mid-block', 'gemini-slabs', 'giant-table', 'honest-gap',
      'malformed-sentinel-variants', 'single-pass', 'stop-mid-pass', 'unclosed-sentinel',
    ]
    expect([...FIXTURE_CORPUS_NAMES].sort()).toEqual(fixtureNames)
  })

  it('every scenario name is unique', () => {
    const names = ROUTE_SCENARIOS.map((s) => s.name)
    expect(new Set(names).size).toBe(names.length)
  })
})

// ═════════════════════════════════════════════════════════════════════════════
// The equality gate.
// ═════════════════════════════════════════════════════════════════════════════
describe('P0-C golden-stream harness — route output equals the committed baseline', () => {
  for (const scenario of ROUTE_SCENARIOS) {
    it(`${scenario.name} (from ${scenario.derived_from})`, async () => {
      const record = await runScenario(scenario)

      if (WRITE_MODE) {
        mkdirSync(BASELINE_DIR, { recursive: true })
        writeFileSync(baselinePath(scenario.name), serializeRecord(record), 'utf8')
        return
      }

      const path = baselinePath(scenario.name)
      expect(existsSync(path), `missing baseline for ${scenario.name} — capture it before refactoring`).toBe(true)
      const baseline = JSON.parse(readFileSync(path, 'utf8')) as GoldenRecord
      const diff = diffRecords(baseline, record)
      expect(
        diff.identical,
        `stream diverged at ${diff.firstDivergence}\n  ${diff.detail}`,
      ).toBe(true)
    })
  }
})

// ═════════════════════════════════════════════════════════════════════════════
// DEMONSTRATED-CAN-FAIL (§N.8): a green run above must not be vacuous.
// ═════════════════════════════════════════════════════════════════════════════
describe('P0-C golden-stream harness — the comparator can fail', () => {
  it('detects a single reordered event', async () => {
    const record = await runScenario(ROUTE_SCENARIOS[0])
    const mutated: GoldenRecord = {
      ...record,
      events: [record.events[1], record.events[0], ...record.events.slice(2)],
    }
    const diff = diffRecords(record, mutated)
    expect(diff.identical).toBe(false)
    expect(diff.firstDivergence).toContain('events[0]')
  })

  it('detects a single changed character inside one block delta', async () => {
    const record = await runScenario(ROUTE_SCENARIOS[0])
    const idx = record.events.findIndex((e) => (e as { type: string }).type === 'block.delta')
    expect(idx, 'fixture must contain a block.delta for this control to mean anything').toBeGreaterThan(-1)
    const events = [...record.events]
    const target = { ...(events[idx] as Record<string, unknown>) }
    target.delta = String(target.delta) + 'X'
    events[idx] = target
    const diff = diffRecords(record, { ...record, events })
    expect(diff.identical).toBe(false)
    expect(diff.firstDivergence).toContain(`events[${idx}].delta`)
  })

  it('detects a dropped side-effect (a persistence call that stopped happening)', async () => {
    const record = await runScenario(ROUTE_SCENARIOS[0])
    const dropped = record.side_effects.filter(
      (e) => (e as { fn: string }).fn !== 'writeTurn',
    )
    expect(dropped.length).toBeLessThan(record.side_effects.length)
    const diff = diffRecords(record, { ...record, side_effects: dropped })
    expect(diff.identical).toBe(false)
  })

  it('does NOT flag a pure timing difference (the one excused class)', async () => {
    const record = await runScenario(ROUTE_SCENARIOS[0])
    const shifted = record.events.map((e) => {
      const o = { ...(e as Record<string, unknown>) }
      if (typeof o.t === 'number') o.t = (o.t as number) + 9999
      if (typeof o.ms === 'number') o.ms = (o.ms as number) + 9999
      return o
    })
    expect(diffRecords(record, { ...record, events: shifted }).identical).toBe(true)
  })

  it('two different scenarios produce genuinely different records (negative space)', async () => {
    const a = await runScenario(ROUTE_SCENARIOS[0])
    const b = await runScenario(ROUTE_SCENARIOS[1])
    expect(diffRecords(a, { ...b, scenario: a.scenario, derived_from: a.derived_from }).identical).toBe(false)
  })
})

// ═════════════════════════════════════════════════════════════════════════════
// Run-to-run determinism — a flaky record would make the gate meaningless.
// ═════════════════════════════════════════════════════════════════════════════
describe('P0-C golden-stream harness — determinism', () => {
  for (const scenario of ROUTE_SCENARIOS.slice(0, 12)) {
    it(`${scenario.name}: two runs of the SAME code produce identical records`, async () => {
      const a = await runScenario(scenario)
      const b = await runScenario(scenario)
      const diff = diffRecords(a, b)
      expect(diff.identical, `nondeterministic at ${diff.firstDivergence}: ${diff.detail}`).toBe(true)
    })
  }
})

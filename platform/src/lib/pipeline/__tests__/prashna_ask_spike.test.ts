/**
 * prashna_ask_spike.test.ts — W4 spike "proves the boundary" evidence.
 *
 * HONESTY NOTE (read this): this is a BOUNDARY-MOCKED INTEGRATION TEST, not a
 * live E2E call. The sandbox this was authored in has no LLM API keys and no
 * Postgres connection, so a genuine live invocation against real Google/Anthropic
 * + real Cloud SQL was not possible here. Instead the test exercises the REAL
 * prashnaAskSpike orchestration end-to-end and mocks ONLY the true external
 * boundaries:
 *
 *   • the LLM planner call        — @/lib/adapters runAdapter (planner)
 *   • the planner context builder — @/lib/pipeline/planner_context_builder (DB/embeddings edge)
 *   • the manifest reader         — @/lib/bundle/manifest_reader (file/DB edge)
 *   • the asset storage           — @/lib/storage getStorageClient (file/GCS/DB edge)
 *   • the retrieval tools         — @/lib/retrieval/registry/tool_name_bridge (Postgres edge)
 *   • the synthesis LLM           — @/lib/providers/dispatcher getAdapter (LLM edge)
 *
 * Everything BETWEEN those edges runs as real production code:
 *   real callPipelinePlanner (schema parse + validate + B.11 detection),
 *   real arbitrateBudgets, real B.11 floor injection, real hydrateBundle,
 *   real createToolCache/executeWithCache dispatch, real buildAdapterMessages/
 *   buildAdapterChatRequest, real runAgenticLoop, real executeMCPTool, real
 *   text_delta accumulation.
 *
 * The chart id used is the canonical Abhinandan chart 1c826d5a-… named by the
 * brief for the W4 spike.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const ABHINANDAN_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

// ── Boundary mock 1: the planner LLM call (runAdapter) ────────────────────────
// The REAL callPipelinePlanner runs; only the model round-trip is faked. We
// return a plan with NO L2.5 tool so the real B.11 floor-injection path fires.
const plannerPlanJson = JSON.stringify({
  query_class: 'holistic',
  query_intent_summary: 'Holistic life reading for the native.',
  asset_bundle: [{ asset_id: 'MSR', priority: 1, reason: 'signal foundation' }],
  tool_calls: [
    { tool_name: 'vector_search', params: { query_text: 'life purpose', top_k: 4 }, token_budget: 500, priority: 1, reason: 'domain narrative' },
  ],
  synthesis_guidance: 'Lead with dominant life themes; ground every claim in a signal id.',
  forward_looking: false,
  dasha_context_required: true,
  expected_output_shape: 'single_answer',
  domains: ['general'],
  history_mode: 'synthesized',
})

vi.mock('@/lib/adapters', () => ({
  runAdapter: vi.fn(async () => ({
    finalText: plannerPlanJson,
    finishReason: 'stop',
    usage: { inputTokens: 1200, outputTokens: 300 },
  })),
}))

// ── Boundary mock 2: planner context builder (DB / embeddings edge) ──────────
vi.mock('@/lib/pipeline/planner_context_builder', () => ({
  buildPlannerContext: vi.fn(async (query: string) => ({
    query,
    history_turns: [],
    history_was_summarized: false,
  })),
}))

// ── Boundary mock 3: manifest reader (file/DB edge) ──────────────────────────
vi.mock('@/lib/bundle/manifest_reader', () => {
  const nativeId = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
  const cgm = {
    canonical_id: 'CGM', path: '025_HOLISTIC_SYNTHESIS/CGM_v9_0.md', version: '9.0',
    status: 'CURRENT', layer: 'L2.5', expose_to_chat: true, representations: ['markdown'],
    interface_version: '1.0', fingerprint: 'fp-cgm', native_id: nativeId,
    token_count: 400,
  }
  const msr = {
    canonical_id: 'MSR', path: '025_HOLISTIC_SYNTHESIS/MSR_v5_0.md', version: '5.0',
    status: 'CURRENT', layer: 'L2.5', expose_to_chat: true, representations: ['markdown'],
    interface_version: '1.0', fingerprint: 'fp-msr', native_id: nativeId,
    token_count: 400,
  }
  return {
    loadManifest: vi.fn(async () => ({
      fingerprint: 'test-fingerprint',
      entries: [cgm, msr],
      byId: new Map([['CGM', cgm], ['MSR', msr]]),
    })),
  }
})

// ── Boundary mock 4: asset storage (readFile) ────────────────────────────────
vi.mock('@/lib/storage', () => ({
  getStorageClient: vi.fn(() => ({
    readFile: vi.fn(async (p: string) =>
      `# Asset ${p}\nCanonical chart-grounded content for the native. Signal SIG.MSR.001 — strong Saturn.`,
    ),
  })),
}))

// ── Boundary mock 5: retrieval tools (Postgres edge) ─────────────────────────
// Used by BOTH executeWithCache (pre-fetch) and executeMCPTool (loop).
vi.mock('@/lib/retrieval/registry/tool_name_bridge', () => ({
  getToolByName: vi.fn((name: string) => ({
    name,
    retrieve: vi.fn(async () => ({
      tool_name: name,
      results: [
        { content: `[${name}] SIG.MSR.001 — Saturn in the 10th grants disciplined ascent in career.`, signal_id: 'SIG.MSR.001' },
        { content: `[${name}] SIG.MSR.014 — Jupiter aspect on the 5th supports progeny and counsel.`, signal_id: 'SIG.MSR.014' },
      ],
    })),
  })),
}))

// ── Boundary mock 6: synthesis LLM (getAdapter) ──────────────────────────────
// Fake adapter whose chat() yields a chart-grounded answer as text_delta events.
const SYNTH_ANSWER_PIECES = [
  'For this native, the dominant theme is disciplined ascent: ',
  'Saturn in the 10th (SIG.MSR.001) rewards patient, structured effort in career. ',
  'Jupiter’s aspect on the 5th (SIG.MSR.014) supports counsel, teaching, and progeny. ',
  'The current dasha phase favours consolidation over expansion.',
]
vi.mock('@/lib/providers/dispatcher', () => ({
  getAdapter: vi.fn(() => ({
    providerId: 'google',
    getManifest: () => ({ adaptiveToolLoop: 'native' }),
    tools: (_req: unknown) => ({ mode: 'native', tools: [] }),
    // eslint-disable-next-line @typescript-eslint/require-await
    chat: async function* () {
      for (const piece of SYNTH_ANSWER_PIECES) {
        yield { type: 'text_delta', text: piece }
      }
      yield { type: 'usage', inputTokens: 5000, outputTokens: 220 }
      // end_turn → runAgenticLoop terminates (no tool-use signal)
      yield { type: 'message_stop', stopReason: 'end_turn' }
    },
  })),
}))

// server-only is a no-op shim in the test runner
vi.mock('server-only', () => ({}))

// Import AFTER mocks are registered.
import { prashnaAskSpike } from '../prashna_ask_spike'

describe('prashnaAskSpike — W4 headless boundary proof (C-6/F-R1)', () => {
  beforeEach(() => vi.clearAllMocks())

  it('turns a question + chartId into a real synthesized, chart-grounded answer', async () => {
    const result = await prashnaAskSpike(
      'What are the dominant life themes in this chart, and how should the native approach career?',
      ABHINANDAN_CHART_ID,
      { stack: 'gemini' },
    )

    // Non-empty answer produced by the real synthesis-accumulation loop.
    expect(result.answer.length).toBeGreaterThan(0)
    expect(result.answer).toContain('SIG.MSR.001')
    expect(result.answer).toContain('career')

    // Real planner classification flowed through.
    expect(result.query_class).toBe('holistic')

    // Real B.11 floor injected an L2.5 tool (planner supplied none) + dasha floor
    // (holistic class). Proves the whole-chart-read discipline ran, not a stub.
    expect(result.tools_planned).toContain('marsys://tool/L2/query_signals')
    expect(result.tools_planned).toContain('chart_facts_query')

    // Real retrieval dispatch executed tools and returned rows.
    expect(result.tools_executed.length).toBeGreaterThan(0)
    expect(result.tool_row_count).toBeGreaterThan(0)

    // Real bundle hydration injected the CGM floor asset.
    expect(result.assets_hydrated).toContain('CGM')

    // Models resolved from the real static STACK_ROUTING (gemini stack).
    expect(result.synthesis_model_id).toBe('gemini-2.5-pro')
    expect(result.planner_model_id).toBe('gemini-2.5-flash')
  })

  it('rejects a non-UUID chartId and an empty question (headless guards)', async () => {
    await expect(prashnaAskSpike('hello', 'not-a-uuid')).rejects.toThrow(/UUID/)
    await expect(prashnaAskSpike('   ', ABHINANDAN_CHART_ID)).rejects.toThrow(/empty/)
  })
})

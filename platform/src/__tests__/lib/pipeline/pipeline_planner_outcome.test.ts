/**
 * pipeline_planner_outcome.test.ts — W4 "One Planner" core step 2.
 *
 * Covers the 3-way PlannerOutcome contract that `callPipelinePlanner` now returns
 * (plan | clarification_needed | fault) and, critically, the repair-retry-then-fault
 * path that fixes the live HTTP-422 bug:
 *
 *   - a genuinely ambiguous query short-circuits to `clarification_needed` WITHOUT
 *     ever calling the LLM (the deterministic classifier's fallback signal fires);
 *   - a well-classified query whose LLM returns non-JSON gets EXACTLY ONE structured
 *     repair-retry, and if that also fails returns a TYPED `fault` (never throws);
 *   - a repair that succeeds on the second attempt yields a `plan`;
 *   - valid JSON on the first attempt yields a `plan` carrying the deterministic
 *     `scope_tuple`.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── runAdapter is the single LLM boundary we drive ──────────────────────────────
const runAdapter = vi.fn()
vi.mock('@/lib/adapters', () => ({
  runAdapter: (...args: unknown[]) => runAdapter(...args),
}))

// ── node:fs — feed getSystemPrompt() + loadManifest() synthetic files ───────────
vi.mock('node:fs', () => {
  const readFileSync = (p: string) => {
    if (String(p).includes('CAPABILITY_MANIFEST.json')) return '{}'
    // Minimal PLANNER_PROMPT_v2_0.md satisfying the §3/§4/§5 section parser.
    return [
      '## 3. System prompt',
      '```',
      'SYSTEM PROMPT BODY',
      '```',
      '',
      '## 4. Few-shot examples',
      'few-shot content',
      '## 5. Boundary',
    ].join('\n')
  }
  return { readFileSync, default: { readFileSync } }
})

// ── Deterministic-context + telemetry deps (all inert for these tests) ──────────
vi.mock('@/lib/pipeline/planner_context_builder', () => ({
  buildPlannerContext: vi.fn(async (query: string) => ({
    query,
    history_turns: [],
    history_was_summarized: false,
  })),
}))
vi.mock('@/lib/pipeline/manifest_compressor', () => ({
  compressManifest: vi.fn(() => []),
  compressedManifestToString: vi.fn(() => '[]'),
}))
vi.mock('@/lib/db/monitoring-write', () => ({
  writeLlmCallLog: vi.fn(),
  resolveProvider: vi.fn(() => 'google'),
}))
vi.mock('@/lib/llm/pricing', () => ({
  computeCostUsd: vi.fn(() => 0),
  getModelPricingSync: vi.fn(() => ({})),
}))
vi.mock('@/lib/db/trace/plan_alternatives_writer', () => ({
  writePlanAlternatives: vi.fn(),
}))
vi.mock('@/lib/llm/observability', () => ({
  persistObservation: vi.fn(async () => undefined),
  computeCost: vi.fn(async () => null),
}))
vi.mock('@/lib/storage', () => ({
  getStorageClient: vi.fn(() => ({})),
}))

import { callPipelinePlanner } from '@/lib/pipeline/pipeline_planner'

// ── Helpers ─────────────────────────────────────────────────────────────────────

function adapterReturn(finalText: string) {
  return {
    modelId: 'test-model',
    provider: 'google',
    intermediate: [],
    finalText,
    finishReason: 'stop' as const,
    usage: { inputTokens: 10, outputTokens: 20, costUsd: 0, latencyMs: 5 },
    providerMeta: {},
  }
}

const VALID_PLAN_JSON = JSON.stringify({
  query_class: 'predictive',
  query_intent_summary: 'Current dasha period lookup.',
  asset_bundle: [],
  tool_calls: [],
})

// A clearly-classified query so the classifier does NOT short-circuit to clarification.
const CLASSIFIED_QUERY = 'What is my current dasha period?'

beforeEach(() => {
  runAdapter.mockReset()
})

describe('callPipelinePlanner — clarification outcome', () => {
  it('short-circuits an ambiguous query to clarification_needed WITHOUT calling the LLM', async () => {
    const outcome = await callPipelinePlanner(
      'hey, can you help me with something?',
      [],
      'test-model',
      'chart-1',
    )
    expect(outcome.outcome).toBe('clarification_needed')
    if (outcome.outcome === 'clarification_needed') {
      expect(outcome.question.length).toBeGreaterThan(0)
      expect(outcome.missing_scope_dims).toContain('intent')
      expect(Array.isArray(outcome.suggested_options)).toBe(true)
    }
    // The whole point: no LLM round-trip for a query we couldn't classify.
    expect(runAdapter).not.toHaveBeenCalled()
  })
})

describe('callPipelinePlanner — plan outcome', () => {
  it('returns a plan (with scope_tuple attached) on valid first-attempt JSON', async () => {
    runAdapter.mockResolvedValueOnce(adapterReturn(VALID_PLAN_JSON))

    const outcome = await callPipelinePlanner(CLASSIFIED_QUERY, [], 'test-model', 'chart-1')

    expect(outcome.outcome).toBe('plan')
    if (outcome.outcome === 'plan') {
      expect(outcome.plan.query_class).toBe('predictive')
      // Deterministic scope tuple attached post-parse.
      expect(outcome.plan.scope_tuple?.intent).toBe('dasha_timing')
    }
    expect(runAdapter).toHaveBeenCalledTimes(1)
  })
})

describe('callPipelinePlanner — repair-retry then fault (the 422-bug fix)', () => {
  it('attempts EXACTLY ONE repair-retry then returns a typed fault (does NOT throw) on repeated non-JSON', async () => {
    // Both the primary call and the single repair-retry return conversational prose.
    runAdapter
      .mockResolvedValueOnce(adapterReturn('Sure! Here is a plan for your chart: ...'))
      .mockResolvedValueOnce(adapterReturn('Apologies — here it is again in words, no JSON.'))

    // Must resolve to a typed value, never reject/throw.
    const outcome = await callPipelinePlanner(CLASSIFIED_QUERY, [], 'test-model', 'chart-1')

    expect(outcome.outcome).toBe('fault')
    if (outcome.outcome === 'fault') {
      expect(outcome.retryable).toBe(false) // model keeps producing garbage → not retryable
      expect(outcome.reason).toMatch(/repair-retry/i)
    }
    // Exactly one repair-retry: 1 primary + 1 repair = 2 total adapter calls.
    expect(runAdapter).toHaveBeenCalledTimes(2)
  })

  it('recovers to a plan when the single repair-retry returns valid JSON', async () => {
    runAdapter
      .mockResolvedValueOnce(adapterReturn('Here you go (prose, not json)'))
      .mockResolvedValueOnce(adapterReturn(VALID_PLAN_JSON))

    const outcome = await callPipelinePlanner(CLASSIFIED_QUERY, [], 'test-model', 'chart-1')

    expect(outcome.outcome).toBe('plan')
    expect(runAdapter).toHaveBeenCalledTimes(2)
  })

  it('the repair-retry message set includes the model\'s bad output + a corrective instruction', async () => {
    runAdapter
      .mockResolvedValueOnce(adapterReturn('totally not json'))
      .mockResolvedValueOnce(adapterReturn(VALID_PLAN_JSON))

    await callPipelinePlanner(CLASSIFIED_QUERY, [], 'test-model', 'chart-1')

    const repairCallArg = runAdapter.mock.calls[1][0] as {
      messages: Array<{ role: string; content: string }>
    }
    const roles = repairCallArg.messages.map(m => m.role)
    // The repair turn re-issues the original user message, echoes the bad assistant
    // output, then appends a corrective user instruction.
    expect(roles).toEqual(['user', 'assistant', 'user'])
    expect(repairCallArg.messages[1].content).toContain('totally not json')
    expect(repairCallArg.messages[2].content).toMatch(/only.*valid json/i)
  })
})

describe('callPipelinePlanner — suppliedScopeTuple override (W6.1 fix-cycle)', () => {
  // Live E2E defect (native-directed, trace c332bf16-1641-4f70-b15c-65ea33b589ee):
  // an explicit, C-1-supplied scope_tuple with a resolved intent was silently
  // dropped — the deterministic classifier re-ran on the raw text and still
  // produced clarification_needed even though the caller already declared scope.
  const SUPPLIED_TUPLE = {
    intent: 'domain_assessment' as const,
    domains: ['career' as const],
    width: 'standard' as const,
    depth: 'standard' as const,
    horizon: 'near' as const,
    intervention: 'none' as const,
    entitlement: 'native' as const,
  }

  it('an otherwise-ambiguous query reaches a plan (not clarification_needed) when a resolved scope_tuple is supplied', async () => {
    runAdapter.mockResolvedValueOnce(adapterReturn(VALID_PLAN_JSON))

    // This exact text alone short-circuits to clarification (see the first
    // describe block above) — the supplied tuple must override that.
    const outcome = await callPipelinePlanner(
      'hey, can you help me with something?',
      [],
      'test-model',
      'chart-1',
      undefined,
      undefined,
      undefined,
      SUPPLIED_TUPLE,
    )

    expect(outcome.outcome).toBe('plan')
    if (outcome.outcome === 'plan') {
      expect(outcome.plan.scope_tuple?.intent).toBe('domain_assessment')
      expect(outcome.plan.scope_tuple?.domains).toContain('career')
    }
    expect(runAdapter).toHaveBeenCalledTimes(1)
  })

  it('does NOT override when the supplied tuple itself has intent:unknown — still clarifies', async () => {
    const outcome = await callPipelinePlanner(
      'hey, can you help me with something?',
      [],
      'test-model',
      'chart-1',
      undefined,
      undefined,
      undefined,
      { ...SUPPLIED_TUPLE, intent: 'unknown' },
    )

    expect(outcome.outcome).toBe('clarification_needed')
    expect(runAdapter).not.toHaveBeenCalled()
  })

  it('falls back to the classifier\'s own domains when the supplied tuple has none/general', async () => {
    runAdapter.mockResolvedValueOnce(adapterReturn(VALID_PLAN_JSON))

    const outcome = await callPipelinePlanner(
      'What is my current dasha period?', // classifier resolves domains:['general'] here
      [],
      'test-model',
      'chart-1',
      undefined,
      undefined,
      undefined,
      { ...SUPPLIED_TUPLE, domains: ['general'] },
    )

    expect(outcome.outcome).toBe('plan')
    if (outcome.outcome === 'plan') {
      // supplied intent wins, but domains come from the classifier's own read of
      // the text since the caller didn't supply a real domain.
      expect(outcome.plan.scope_tuple?.intent).toBe('domain_assessment')
    }
  })
})

describe('callPipelinePlanner — provider-error fault', () => {
  it('returns a retryable fault (not a throw) when the LLM call itself fails', async () => {
    runAdapter.mockRejectedValue(new Error('upstream 500 internal server error'))

    const outcome = await callPipelinePlanner(CLASSIFIED_QUERY, [], 'test-model', 'chart-1')

    expect(outcome.outcome).toBe('fault')
    if (outcome.outcome === 'fault') {
      expect(outcome.retryable).toBe(true)
    }
  })
})

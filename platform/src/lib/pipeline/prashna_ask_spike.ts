/**
 * prashna_ask_spike.ts — W4 headless `prashna_ask` spike (C-6 / F-R1).
 *
 * Proves the boundary the RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF names for W4:
 *
 *     "question → headless engine → synthesized answer; proves the boundary;
 *      no transport polish."
 *
 * WHAT THIS IS
 * ------------
 * A plain importable async function that turns a question + chartId into a
 * synthesized, chart-grounded answer as plain data — by running it through the
 * SAME real production pipeline stages the `/api/chat/consult` route uses:
 *
 *     callPipelinePlanner  (real LLM planner → PipelinePlan)
 *       → arbitrateBudgets (real proportional budget trim)
 *       → B.11 floor inject (real — L2.5 whole-chart-read + dasha floor)
 *       → hydrateBundle     (real — CGM floor asset + planner assets)
 *       → getToolByName + executeWithCache (real retrieval tool dispatch)
 *       → getAdapter + runAgenticLoop / adapter.chat (real synthesis engine)
 *
 * It reuses production functions — it does NOT reimplement or mock any stage.
 *
 * WHAT THIS IS DELIBERATELY NOT (out of scope — W6 owns the full contract)
 * -----------------------------------------------------------------------
 * No HTTP route. No SSE streaming / UI-message wrapping. No auth / rate limit /
 * job-handle / notifications / cost caps. No conversation persistence, no
 * pending-stream writer, no citation-gate wire emission. Those are the
 * "transport polish" the consult route's runAdapterDispatch adds; the headless
 * engine is exactly the chatStream generator underneath it, which this function
 * drains directly into a string.
 *
 * THE BOUNDARY CALL (judgment)
 * ----------------------------
 * "The engine" = planner + retrieval + the synthesis chatStream generator
 * (runAgenticLoop / adapter.chat), which yields `text_delta` events. In the
 * consult route those deltas are pumped into a UIMessageStream writer; here we
 * simply concatenate them. Everything upstream of that generator is engine;
 * everything the route wraps around it (writer.write, data-parts, persistence,
 * B.11 citation-gate emission, trace steps) is transport polish and is omitted.
 */

import 'server-only'

import { callPipelinePlanner } from './pipeline_planner'
import type { PipelinePlan } from './types'
import { arbitrateBudgets } from './budget_arbiter'
import { hydrateBundle } from '@/lib/bundle/bundle_hydrator'
import { loadManifest } from '@/lib/bundle/manifest_reader'
import { getToolByName } from '@/lib/retrieval/registry/tool_name_bridge'
import { createToolCache, executeWithCache } from '@/lib/cache/index'
import { getAdapter, type StackId } from '@/lib/providers/dispatcher'
import { buildChatToolsFromNames } from '@/lib/retrieval/registry/schema_utils'
import {
  buildAdapterMessages,
  buildAdapterChatRequest,
} from '@/lib/providers/adapter-dispatch-helpers'
import type { ChatRequest } from '@/lib/providers/types'
import {
  runAgenticLoop,
  LOOP_CONFIG_BY_PROVIDER,
} from '@/lib/synthesis/agentic_loop'
import { executeMCPTool } from '@/lib/synthesis/mcp_tool_executor'
import {
  STACK_ROUTING,
  DEFAULT_STACK_ID,
  getModelMeta,
  type ModelStack,
} from '@/lib/models/registry'
import type { ToolBundle, RetrievalTool, QueryPlan } from '@/lib/retrieval/shared_types'

// ── Result shape ────────────────────────────────────────────────────────────

export interface PrashnaAskSpikeResult {
  /** The synthesized, chart-grounded answer (plain text). */
  answer: string
  /** Classification the real planner assigned to the question. */
  query_class: string
  /** Tools the planner + B.11 floor authorised. */
  tools_planned: string[]
  /** Tools that executed and returned rows (post-dispatch). */
  tools_executed: string[]
  /** Canonical asset ids hydrated into the synthesis context. */
  assets_hydrated: string[]
  /** Model ids actually invoked. */
  planner_model_id: string
  synthesis_model_id: string
  /** Timings. */
  planner_latency_ms: number
  synthesis_latency_ms: number
  /** Total rows returned across all executed tools. */
  tool_row_count: number
}

export interface PrashnaAskSpikeOptions {
  /** Model stack to resolve planner + synthesis models from. Default: gemini. */
  stack?: ModelStack
  /** Explicit planner model override (else static STACK_ROUTING primary). */
  plannerModelId?: string
  /** Explicit synthesis model override (else static STACK_ROUTING primary). */
  synthesisModelId?: string
}

// gemini→google etc. Mirrors run_adapter_dispatch.STACK_TO_ADAPTER.
const STACK_TO_ADAPTER: Partial<Record<string, StackId>> = {
  anthropic: 'anthropic',
  gemini: 'google',
  gpt: 'openai',
  deepseek: 'deepseek',
  nim: 'nvidia',
}

// Same L2.5 whole-chart-read tool set the consult route enforces for B.11.
const L2_5_TOOLS = [
  'msr_sql', 'query_msr_aggregate', 'pattern_register', 'resonance_register',
  'cluster_atlas', 'contradiction_register', 'cgm_graph_walk',
  'marsys://tool/L2/query_signals', 'marsys://tool/L2/traverse_chart_graph',
]

const AGENTIC_PROVIDERS = new Set<StackId>(['anthropic', 'google', 'openai', 'deepseek', 'nvidia'])

/**
 * Headless prashna_ask spike. Question + chartId → synthesized answer.
 */
export async function prashnaAskSpike(
  question: string,
  chartId: string,
  opts: PrashnaAskSpikeOptions = {},
): Promise<PrashnaAskSpikeResult> {
  if (!question.trim()) throw new Error('prashnaAskSpike: question is empty')
  const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
  if (!UUID_RE.test(chartId)) throw new Error('prashnaAskSpike: chartId must be a UUID')

  const stack = opts.stack ?? (DEFAULT_STACK_ID as ModelStack)
  const routing = STACK_ROUTING[stack] ?? STACK_ROUTING[DEFAULT_STACK_ID]
  const plannerModelId = opts.plannerModelId ?? routing.planner_fast.primary
  const synthesisModelId = opts.synthesisModelId ?? routing.synthesis.primary
  const synthMeta = getModelMeta(synthesisModelId)

  // ── Stage 1 — real LLM planner ─────────────────────────────────────────────
  const plannerStart = Date.now()
  const plan: PipelinePlan = await callPipelinePlanner(
    question,
    [], // headless: no conversation history
    plannerModelId,
    chartId,
    // no emitTrace, no queryId → no trace/DB-log side effects fired by the planner
  )
  const planner_latency_ms = Date.now() - plannerStart

  // Route-controlled stamps (never LLM output).
  plan.query_plan_id = crypto.randomUUID()
  plan.query_text = question

  // ── Stage 2 — real proportional budget arbitration ─────────────────────────
  const arbitrated = arbitrateBudgets(
    plan.tool_calls.map(tc => ({
      tool_name: tc.tool_name, priority: tc.priority, token_budget: tc.token_budget,
    })),
    {
      synthesis_model_max_context: synthMeta?.maxInputTokens ?? 128_000,
      system_prompt_reserve: 800,
      synthesis_guidance_reserve: plan.synthesis_guidance ? 200 : 0,
      safety_margin: 0.85,
      min_tokens_per_tool: 200,
    },
  )
  for (let i = 0; i < plan.tool_calls.length; i++) {
    plan.tool_calls[i].token_budget = arbitrated[i].token_budget
  }

  const toolsAuthorized = Array.from(new Set(plan.tool_calls.map(tc => tc.tool_name)))

  // ── Stage 3 — real B.11 Whole-Chart-Read floor (at least one L2.5 tool) ────
  if (!toolsAuthorized.some(t => L2_5_TOOLS.includes(t))) {
    if (plan.query_class === 'predictive') {
      const domainSearch = (plan.domains ?? []).length > 0
        ? (plan.domains ?? []).join(' ')
        : 'relationships family marriage children'
      plan.tool_calls.push(
        { tool_name: 'marsys://tool/L2/query_signals', params: { forward_looking: true }, token_budget: 600, priority: 1, reason: 'B.11 predictive floor: signal foundation' },
        { tool_name: 'vector_search', params: { query_text: domainSearch, doc_type: ['domain_report'], top_k: 6 }, token_budget: 500, priority: 1, reason: 'B.11 predictive floor: domain narrative' },
        { tool_name: 'pattern_register', params: { forward_looking: true }, token_budget: 400, priority: 2, reason: 'B.11 predictive floor: R7a requirement' },
      )
      toolsAuthorized.push('marsys://tool/L2/query_signals', 'vector_search', 'pattern_register')
    } else {
      plan.tool_calls.push(
        { tool_name: 'marsys://tool/L2/query_signals', params: {}, token_budget: 600, priority: 1, reason: 'B.11 floor enforcement' },
        { tool_name: 'marsys://tool/L2/traverse_chart_graph', params: {}, token_budget: 400, priority: 2, reason: 'B.11 floor enforcement' },
      )
      toolsAuthorized.push('marsys://tool/L2/query_signals', 'marsys://tool/L2/traverse_chart_graph')
    }
  }

  // Dasha context floor for predictive/holistic.
  if (
    (plan.query_class === 'predictive' || plan.query_class === 'holistic') &&
    !toolsAuthorized.includes('chart_facts_query')
  ) {
    plan.tool_calls.push({
      tool_name: 'chart_facts_query',
      params: { category: 'dasha_vimshottari', limit: 50 },
      token_budget: 600, priority: 1,
      reason: 'dasha context floor: canonical MD/AD sequence for phase-anchored predictions',
    })
    toolsAuthorized.push('chart_facts_query')
  }

  // ── Stage 4 — real bundle hydration (CGM floor + planner assets) ──────────
  const manifest = await loadManifest()
  plan.manifest_fingerprint = manifest.fingerprint
  const bundle = await hydrateBundle(plan, manifest)

  // QueryPlan consumed by the retrieval tools + the synthesis loop. Shaped to
  // the real QueryPlan interface; `chart_id` is carried as an extra field so
  // headless tool dispatch can scope to the native (the consult route sources
  // chart scope from request context — headless has no request).
  const queryPlan: QueryPlan & { chart_id: string; tool_calls: PipelinePlan['tool_calls'] } = {
    query_plan_id: plan.query_plan_id,
    query_text: question,
    query_class: plan.query_class,
    domains: plan.domains ?? [],
    forward_looking: plan.forward_looking ?? false,
    tools_authorized: toolsAuthorized,
    history_mode: plan.history_mode ?? 'synthesized',
    panel_mode: plan.panel_mode ?? false,
    expected_output_shape: plan.expected_output_shape ?? 'three_interpretation',
    manifest_fingerprint: manifest.fingerprint,
    schema_version: '1.0',
    planets: plan.planets,
    houses: plan.houses,
    dasha_context_required: plan.dasha_context_required,
    graph_seed_hints: plan.graph_seed_hints,
    vector_search_filter: plan.vector_search_filter,
    chart_id: chartId,
    tool_calls: plan.tool_calls,
  }

  // ── Stage 5 — real retrieval tool dispatch ────────────────────────────────
  const cache = createToolCache()
  const plannerParamsMap = new Map<string, Record<string, unknown>>(
    plan.tool_calls.map(tc => [tc.tool_name, tc.params]),
  )
  const toolResults = await Promise.all(
    toolsAuthorized.map(async (toolName): Promise<ToolBundle | null> => {
      const t = getToolByName(toolName) as RetrievalTool | undefined
      if (!t) return null
      try {
        return await executeWithCache(t, queryPlan, cache, plannerParamsMap.get(toolName))
      } catch {
        return null // gap-tolerant: a failed tool never aborts synthesis
      }
    }),
  )
  const validToolResults = toolResults.filter((r): r is ToolBundle => r !== null)
  const tools_executed = toolsAuthorized.filter((_, i) => toolResults[i] !== null)
  const tool_row_count = validToolResults.reduce((s, r) => s + r.results.length, 0)

  // ── Stage 6 — real synthesis engine (headless: drain the chatStream) ──────
  const adapterId: StackId | undefined =
    STACK_TO_ADAPTER[stack] ?? (synthMeta?.provider as StackId | undefined)
  if (!adapterId) throw new Error(`prashnaAskSpike: no adapter for stack=${stack}`)

  const adapterMessages = buildAdapterMessages([], question)
  const bundleSystemContent = (bundle.assets as Array<{ content: string }>)
    .map(a => a.content).filter(Boolean).join('\n\n')
  const toolResultsContext = validToolResults.length > 0
    ? 'RETRIEVED CHART DATA:\n' + validToolResults
        .flatMap(tb => tb.results.map(r => r.content)).join('\n\n')
    : ''
  const systemContent = [
    bundleSystemContent,
    toolResultsContext,
    plan.synthesis_guidance ? `SYNTHESIS GUIDANCE:\n${plan.synthesis_guidance}` : '',
  ].filter(Boolean).join('\n\n---\n\n') || undefined

  let adapterChatReq: ChatRequest = buildAdapterChatRequest(
    adapterMessages, synthesisModelId, systemContent,
  )
  const adapter = getAdapter(adapterId)
  const useAgenticLoop = AGENTIC_PROVIDERS.has(adapterId)
  if (useAgenticLoop) {
    const providerManifest = adapter.getManifest()
    const toolsCfg = adapter.tools({
      toolLoopMode: providerManifest.adaptiveToolLoop,
      tools: buildChatToolsFromNames(toolsAuthorized),
      maxIterations: 8,
    })
    adapterChatReq = { ...adapterChatReq, toolsConfig: toolsCfg, tools: toolsCfg.tools }
  }

  const synthesisStart = Date.now()
  const loopConfig = LOOP_CONFIG_BY_PROVIDER[adapterId]
  const chatStream = (useAgenticLoop && loopConfig)
    ? runAgenticLoop(
        adapter,
        adapterChatReq,
        (toolCall) => executeMCPTool(toolCall, { queryPlan }),
        loopConfig,
      )
    : adapter.chat(adapterChatReq)

  let answer = ''
  for await (const event of chatStream) {
    if (event.type === 'text_delta') answer += event.text
    // thinking/tool_use/usage/error events are consumed but not part of the
    // headless answer payload — no transport wrapping here.
  }
  const synthesis_latency_ms = Date.now() - synthesisStart

  return {
    answer,
    query_class: plan.query_class,
    tools_planned: toolsAuthorized,
    tools_executed,
    assets_hydrated: bundle.assets.map(a => a.asset_id),
    planner_model_id: plannerModelId,
    synthesis_model_id: synthesisModelId,
    planner_latency_ms,
    synthesis_latency_ms,
    tool_row_count,
  }
}

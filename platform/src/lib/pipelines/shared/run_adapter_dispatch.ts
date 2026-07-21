/**
 * run_adapter_dispatch — unit 4.refactor_pipeline_shim.
 *
 * Hosts the streaming-response body that the consult route previously inlined
 * (formerly route.ts L899–1319). Behaviour is byte-identical with the pre-move
 * inline block — only the lexical location changed. The route becomes a thin
 * selector: auth + chart resolution + planner-context + `runAdapterDispatch(ctx)`.
 *
 * What this module owns:
 *   • adapter id resolution (stack → adapter, with 'marsys' meta-stack via modelMeta.provider)
 *   • adapter chat request assembly (system content = bundle + synthesis guidance)
 *   • per-provider agentic-loop decision (R11.E flag map)
 *   • Gemini cachedContent creation (D.3)
 *   • the UIMessageStream `execute` writer body (text/thinking/tool deltas)
 *   • B.11 citation gate (post-stream) + trace emit
 *   • shared onFinish write-through (persistence, cost, citations, prediction ledger)
 *
 * What this module does NOT own:
 *   • request parsing, auth, chart authorization (still route.ts)
 *   • planner invocation, bundle hydration, tool fetch (still route.ts)
 *   • trace emission for classify/compose_bundle/tool_fetch steps (still route.ts)
 *
 * Acceptance: behaviour byte-identical (existing tests under
 * platform/src/app/api/chat green; pipeline tests green).
 */

import {
  createIdGenerator,
  createUIMessageStream,
  createUIMessageStreamResponse,
} from 'ai'
import type { ModelMessage, UIMessage } from 'ai'

import {
  stagePart,
  observabilityPart,
  completenessPart,
  orientationPart,
} from '@/lib/streams/data_parts'
import type { WebCompletenessReceipt } from '@/lib/pipeline/completeness_wiring'
import { ORIENTATION_TOKEN_BUDGET, type ChartOrientation } from '@/lib/retrieval/orientation'
import { DEFAULT_AYANAMSHA } from '@/lib/retrieval/registry/constants'
import { configService } from '@/lib/config/index'

import type { StackId } from '@/lib/providers/dispatcher'
import { getAdapter } from '@/lib/providers/dispatcher'
import type { ChatRequest } from '@/lib/providers/types'
import {
  buildAdapterMessages,
  buildAdapterChatRequest,
} from '@/lib/providers/adapter-dispatch-helpers'
import {
  runAgenticLoop,
  LOOP_CONFIG_BY_PROVIDER,
} from '@/lib/synthesis/agentic_loop'
import { executeMCPTool } from '@/lib/synthesis/mcp_tool_executor'
import {
  buildCacheCreatePayload,
  GEMINI_CACHE_MIN_TOKENS,
} from '@/lib/providers/google/cached_content'

// D7 Step 4: buildChatToolsFromNames moved to schema_utils (tool_catalogue RETIRED)
import { buildChatToolsFromNames } from '@/lib/retrieval/registry/schema_utils'
import type { ToolBundle } from '@/lib/retrieval/shared_types'

import {
  writeConversationMessages,
} from '@/lib/persistence/conversation_writer'
import {
  updateConversationTitle,
} from '@/lib/conversations'
import { generateConversationTitle } from '@/lib/conversations/title'
import {
  computeCostUsd,
  getModelPricingSync,
} from '@/lib/llm/pricing'
import { writeContextAssemblyLog } from '@/lib/db/monitoring-write'
import { validateCitationsForStream } from '@/lib/synthesis/streaming_citation_validator'
import { traceEmitter } from '@/lib/trace/emitter'

import { runOnFinishWriteThrough } from './onfinish_writethrough'

// ---------------------------------------------------------------------------
// Context shape — everything the dispatch body needs from the route.
// ---------------------------------------------------------------------------

export interface RunAdapterDispatchCtx {
  /**
   * W5 L9 — verdict-first streaming: wall-clock `Date.now()` captured at the
   * very top of the consult route handler (`setupStart`). Used to compute the
   * time-to-first-verdict stage-timing metric (see
   * `TIME_TO_FIRST_VERDICT_SLO_MS` in `@/lib/streams/data_parts`) the instant
   * the `data-orientation` SSE event is written, before any synthesis text
   * streams.
   */
  requestStartedAt: number

  /** Auth + addressing */
  userUid: string
  finalConversationId: string
  chartId: string

  /** Audience + style + first-turn semantics */
  audienceTier: 'super_admin' | 'client'
  selectedStack: string
  isFirstTurn: boolean
  lelContextEnabled: boolean
  style: string

  /** Model resolution */
  modelId: string
  modelMeta: { provider?: string; maxInputTokens?: number | null }
  plannerModelId: string

  /** Planner result + tool-fetch outputs (intentionally loose — these are
   *  pass-throughs to existing helpers that own their own narrower types). */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  plan: any
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  bundle: any
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  queryPlan: any
  validToolResults: ToolBundle[]
  toolEventLog: ReadonlyArray<{ name: string; status: 'done' | 'error'; ms: number; ok_count: number; err_count: number }>
  plannerLatencyMs: number
  composeBundleMs: number
  toolFetchMs: number

  /** Stage seqs pre-allocated by the route (UQE-9 atomic counter) */
  queryId: string

  /** Conversation history + last user query text */
  trimmedConversationHistory: ModelMessage[]
  queryText: string

  /** Raw client messages (used by persistence path) */
  messages: UIMessage[]

  /** Trace + step seq emitters */
  emit: (event: Parameters<typeof traceEmitter.emitStep>[0]) => void
  nextSeq: () => number

  /** γ7 pending-stream writer (already created by the route for this request) */
  pendingStreamWriter: {
    onEvent: () => void
    onTextDelta: (text: string) => void
    clear: () => Promise<void>
  }

  /** MSR snippet resolver — closure over the route's `query` */
  fetchMsrSnippets: (ids: string[]) => Promise<Map<string, string>>

  /**
   * [PHASE-D-06] Optional data-readiness note injected into the system prompt.
   * Set by the consult route when chart build is partial.
   * Format: pre-composed NOTE string ready for concatenation.
   */
  dataReadinessNote?: string

  /**
   * W4 core step 5 — S-1 orientation front-door block (≤2000 tokens). Built by the route
   * (buildChartOrientation) and emitted ONCE as a data-orientation SSE event near the START
   * of the stream. Null/undefined when the orientation build failed — the event is then omitted.
   */
  orientation?: ChartOrientation | null

  /**
   * W4 core step 4 — completeness receipt for the compiled B.11 floor (served/empty/dark per
   * floor item, honest about the MCP↔web namespace gap). Built by the route
   * (buildWebCompletenessReceipt) after the floor tools executed, emitted as a data-completeness
   * SSE event near the END of the stream. Null when the plan carried no scope_tuple / compile failed.
   */
  completenessReceipt?: WebCompletenessReceipt | null
}

// ---------------------------------------------------------------------------
// W5 L9 — verdict-first streaming: pure, unit-testable emission builder
// ---------------------------------------------------------------------------

/**
 * Builds the two SSE data-part payloads the adapter-dispatch stream writes
 * FIRST — before any synthesis text-delta — to satisfy the verdict-first
 * streaming contract (STATE.md W5 OPEN amendment 3):
 *
 *   1. `data-orientation` — the verdict/orientation layer itself. Emitted
 *      UNCONDITIONALLY: when `buildChartOrientation` failed outright
 *      (`orientation` is null/undefined — distinct from the in-band
 *      `degraded` flag orientation.ts already sets for a partial query_ucd
 *      failure), a minimal degraded fallback block is built instead of
 *      omitting the event, so no dispatched query silently loses
 *      verdict-first coverage.
 *   2. `data-stage` (`first_verdict`, `done`, ms) — the time-to-first-verdict
 *      stage-timing sample: wall-clock ms from `requestStartedAt` (captured
 *      at route-handler entry) to `nowMs` (the instant this function runs,
 *      i.e. the instant the SSE writer is about to flush the event above).
 *      See `TIME_TO_FIRST_VERDICT_SLO_MS` in `@/lib/streams/data_parts` for
 *      the target this metric is measured against.
 *
 * Pure function (no I/O, no `Date.now()` call — `nowMs` is passed in) so it
 * can be unit-tested deterministically without mocking the adapter/stream
 * machinery below.
 */
export function buildFirstVerdictEmission(
  orientation: ChartOrientation | null | undefined,
  chartId: string,
  requestStartedAt: number,
  nowMs: number,
): {
  orientationEvent: { type: 'data-orientation'; data: ReturnType<typeof orientationPart> }
  stageEvent: { type: 'data-stage'; data: ReturnType<typeof stagePart> }
  timeToFirstVerdictMs: number
} {
  const orientationForStream = orientation ?? {
    chart_id: chartId,
    ayanamsha_id: DEFAULT_AYANAMSHA,
    degraded: true,
    budget: { limit_tokens: ORIENTATION_TOKEN_BUDGET, estimated_tokens: 0, enforced: false, trims: ['orientation_build_unavailable'] },
  }
  const timeToFirstVerdictMs = Math.max(0, nowMs - requestStartedAt)
  return {
    orientationEvent: {
      type: 'data-orientation',
      data: orientationPart({
        chart_id: orientationForStream.chart_id,
        ayanamsha_id: orientationForStream.ayanamsha_id,
        degraded: orientationForStream.degraded,
        budget: orientationForStream.budget,
        orientation: (orientation
          ?? { chart_id: orientationForStream.chart_id, degraded: true, header_flags: ['orientation_build_unavailable'] }
        ) as unknown as Record<string, unknown>,
      }),
    },
    stageEvent: {
      type: 'data-stage',
      data: stagePart('first_verdict', 'done', timeToFirstVerdictMs),
    },
    timeToFirstVerdictMs,
  }
}

// ---------------------------------------------------------------------------
// Main entry point
// ---------------------------------------------------------------------------

export async function runAdapterDispatch(ctx: RunAdapterDispatchCtx): Promise<Response> {
  const {
    requestStartedAt,
    userUid,
    finalConversationId,
    chartId,
    audienceTier,
    selectedStack,
    isFirstTurn,
    lelContextEnabled,
    style,
    modelId,
    modelMeta,
    plannerModelId,
    plan,
    bundle,
    queryPlan,
    validToolResults,
    toolEventLog,
    plannerLatencyMs,
    composeBundleMs,
    toolFetchMs,
    queryId,
    trimmedConversationHistory,
    queryText,
    messages,
    emit,
    nextSeq,
    pendingStreamWriter,
    fetchMsrSnippets,
    dataReadinessNote,
    orientation,
    completenessReceipt,
  } = ctx

  const STACK_TO_ADAPTER: Partial<Record<string, StackId>> = {
    anthropic: 'anthropic',
    gemini: 'google',
    gpt: 'openai',
    deepseek: 'deepseek',
    nim: 'nvidia',
  }
  // 'marsys' meta-stack: derive the concrete adapter from the resolved
  // model's provider field. STACK_ROUTING resolves a synthesis model_id;
  // modelMeta.provider is the concrete provider that adapter dispatch needs.
  const mappedStackAdapter = STACK_TO_ADAPTER[selectedStack] as StackId | undefined
  const adapterId: StackId | undefined =
    mappedStackAdapter ??
    (modelMeta.provider as StackId | undefined)
  if (!adapterId) {
    throw new Error(
      `[consult] no adapter mapping for stack=${selectedStack} provider=${modelMeta.provider} — ` +
      `legacy synthesis path was removed by 3.legacy_delete.`,
    )
  }
  // Bug A+B fix: use helper that appends current user turn and filters empty content parts.
  const adapterMessages = buildAdapterMessages(trimmedConversationHistory, queryText)
  // Bug C fix: pass bundle assets + synthesis guidance as system context.
  const bundleSystemContent = (bundle.assets as Array<{ content: string }>)
    .map(a => a.content)
    .filter(Boolean)
    .join('\n\n')
  const systemContent = [
    bundleSystemContent,
    plan.synthesis_guidance ? `SYNTHESIS GUIDANCE:\n${plan.synthesis_guidance}` : '',
    dataReadinessNote ?? '',
  ].filter(Boolean).join('\n\n---\n\n') || undefined
  let adapterChatReq: ChatRequest = buildAdapterChatRequest(adapterMessages, modelId, systemContent)
  const adapter = getAdapter(adapterId)
  // R11E loop flags permanently true (WS-0 2026-06-04)
  const AGENTIC_PROVIDERS = new Set(['anthropic', 'google', 'openai', 'deepseek', 'nvidia'])
  const useAgenticLoop = AGENTIC_PROVIDERS.has(adapterId)

  if (useAgenticLoop) {
    const manifest = adapter.getManifest()
    const toolsCfg = adapter.tools({
      toolLoopMode: manifest.adaptiveToolLoop,
      tools: buildChatToolsFromNames(queryPlan.tools_authorized ?? []),
      maxIterations: 8,
    })
    adapterChatReq = { ...adapterChatReq, toolsConfig: toolsCfg, tools: toolsCfg.tools }
  }
  // R11.F — S4: Gemini cachedContent API (D.3)
  // When R11D_GEMINI_CACHE=true and provider=google, attempt to create a
  // Gemini cachedContent object for the system prompt + RAG bundle.
  // The returned resource name is passed through cacheConfig so GoogleAdapter.chat()
  // can reference it in the streamText providerOptions.google.cachedContent field.
  // Cache creation is non-fatal — any failure falls through to a standard uncached request.
  if (false && adapterId === 'google') { // R11D_GEMINI_CACHE: NOT_IMPLEMENTED — permanently false (WS-0)
    const cacheResponse = adapter.cache({ cacheMode: 'cached_content_api', breakpointPositions: [] })
    const estimatedTokens = Math.ceil((systemContent?.length ?? 0) / 4)
    if (estimatedTokens >= GEMINI_CACHE_MIN_TOKENS) {
      try {
        const ttlSeconds = (cacheResponse.providerPayload?.['ttlSeconds'] as number) ?? 600
        // Prefix model name with 'models/' if not already qualified — Gemini REST API requirement
        const qualifiedModel = adapterChatReq.model.startsWith('models/')
          ? adapterChatReq.model
          : `models/${adapterChatReq.model}`
        const cachePayload = buildCacheCreatePayload({
          model: qualifiedModel,
          systemPrompt: systemContent,
          ragBundle: undefined,
          ttl: `${ttlSeconds}s`,
        })
        const apiKey = process.env.GOOGLE_GENERATIVE_AI_API_KEY
        if (apiKey) {
          const cacheRes = await fetch(
            `https://generativelanguage.googleapis.com/v1beta/cachedContents?key=${apiKey}`,
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(cachePayload),
            }
          )
          if (cacheRes.ok) {
            const cacheJson = await cacheRes.json() as { name?: string }
            const cachedContentName = cacheJson.name
            if (cachedContentName) {
              adapterChatReq = {
                ...adapterChatReq,
                cacheConfig: {
                  ...cacheResponse,
                  providerPayload: {
                    ...cacheResponse.providerPayload,
                    cachedContentName,
                  },
                },
              }
              console.log(`[gemini-cache] Created cachedContent: ${cachedContentName} (~${estimatedTokens} tokens)`)
            }
          } else {
            const errText = await cacheRes.text()
            console.warn(`[gemini-cache] Cache creation failed (${cacheRes.status}): ${errText.slice(0, 200)}`)
          }
        }
      } catch (cacheErr) {
        console.warn('[gemini-cache] Cache creation error (non-fatal):', cacheErr)
      }
    } else {
      console.log(`[gemini-cache] Skipping cache: ~${estimatedTokens} tokens < ${GEMINI_CACHE_MIN_TOKENS} minimum`)
    }
  }
  const adapterMsgId = createIdGenerator({ prefix: 'msg', size: 16 })()
  const adapterStartMs = Date.now()
  const adapterStream = createUIMessageStream({
    execute: async ({ writer }) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      writer.write({ type: 'start', messageId: adapterMsgId } as any)
      // W4 core step 5 / W5 L9 — S-1 orientation front-door: emit ONCE near the start, before any
      // synthesis text-delta, so the client has the verdict/orientation layer while synthesis is
      // still running. W5 L9 strengthens this from "emit when the build succeeded" to "emit
      // unconditionally" (see buildFirstVerdictEmission above) — closing the prior gap where an
      // outright `buildChartOrientation` failure silently dropped both the orientation event AND
      // any time-to-first-verdict signal for that request.
      const firstVerdict = buildFirstVerdictEmission(orientation, chartId, requestStartedAt, Date.now())
      writer.write(firstVerdict.orientationEvent)
      // W5 L9 — time-to-first-verdict SLO sample (see TIME_TO_FIRST_VERDICT_SLO_MS in
      // @/lib/streams/data_parts): wall-clock ms from request-handler entry to the instant the
      // verdict/orientation layer above was written into the stream — i.e. BEFORE any
      // `synthesis` text-delta, not after synthesis completes. Emitted unconditionally (same
      // guarantee as the orientation event above) so the SLO has 100% query-class coverage.
      writer.write(firstVerdict.stageEvent)
      writer.write({ type: 'data-stage', data: stagePart('classify', 'done', plannerLatencyMs) })
      writer.write({ type: 'data-stage', data: stagePart('compose_bundle', 'done', composeBundleMs) })
      for (const evt of toolEventLog) {
        writer.write({
          type: 'data-tool',
          data: { type: 'tool', name: evt.name, status: evt.status, ms: evt.ms, ok_count: evt.ok_count, err_count: evt.err_count },
        })
      }
      writer.write({ type: 'data-stage', data: stagePart('tool_fetch', 'done', toolFetchMs) })
      writer.write({ type: 'data-stage', data: stagePart('synthesis', 'running') })
      pendingStreamWriter.onEvent()
      // AI SDK v6 UI message stream protocol requires text-start before text-delta,
      // and text-end + finish after the last delta.
      const adapterTextPartId = 'text-0'
      let adapterTextStarted = false
      let adapterAccumulatedText = ''
      try {
        const loopConfig = LOOP_CONFIG_BY_PROVIDER[adapterId]
        const chatStream = (useAgenticLoop && loopConfig)
          ? runAgenticLoop(
              adapter,
              adapterChatReq,
              (toolCall) => executeMCPTool(toolCall, { queryPlan }),
              loopConfig,
            )
          : adapter.chat(adapterChatReq)
        for await (const event of chatStream) {
          if (event.type === 'text_delta') {
            if (!adapterTextStarted) {
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              writer.write({ type: 'text-start', id: adapterTextPartId } as any)
              adapterTextStarted = true
            }
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            writer.write({ type: 'text-delta', id: adapterTextPartId, delta: event.text } as any)
            pendingStreamWriter.onTextDelta(event.text)
            adapterAccumulatedText += event.text
          } else if (event.type === 'thinking_delta') {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            writer.write({ type: 'reasoning', delta: event.thinking, id: adapterMsgId } as any)
          } else if (event.type === 'tool_use_start') {
            // Silently consume — loop engine handles tool execution
          } else if (event.type === 'tool_use_input_delta') {
            // Silently consume — loop engine handles accumulation
          } else if (event.type === 'tool_use_complete') {
            // Emit as a tool data event for client visibility
            writer.write({
              type: 'data-tool',
              data: { type: 'tool', name: event.name, status: 'done', ms: 0, ok_count: 1, err_count: 0 },
            })
          } else if (event.type === 'error') {
            console.error('[adapter-dispatch] adapter error event stack=%s error=%s', adapterId, event.error)
          }
        }
      } catch (adapterErr) {
        console.error('[adapter-dispatch] stream error stack=%s', adapterId, adapterErr)
      }
      if (adapterTextStarted) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        writer.write({ type: 'text-end', id: adapterTextPartId } as any)
      }
      // ── 0b.1: B.11 citation gate (adapter-path parity with legacy onFinish) ─
      // Mirrors the legacy gate at the wire (route.ts:1373-1475 onFinish branch).
      // Cross-references SIG.MSR.NNN ids in the adapter-streamed text against the
      // assembled context (bundle + tool results). Same MARSYS_FLAG_CITATION_GATE_OVERRIDE
      // semantics, same data-citation-gate emission, same step_done telemetry. Errors
      // are logged only — never thrown post-stream (would corrupt the HTTP pipe).
      let adapterCitationGateResult: 'PASS' | 'WARN' | 'ERROR' = 'PASS'
      let adapterCitationL1Count = 0
      let adapterCitationL2Verified = 0
      try {
        const adapterAssembledContextJson = JSON.stringify({
          bundle,
          tool_results: validToolResults,
        })
        const adapterOverrideOn = configService.getFlag('CITATION_GATE_OVERRIDE')
        const adapterCitationValidation = validateCitationsForStream(
          adapterAccumulatedText,
          adapterAssembledContextJson,
          plan.query_class as Parameters<typeof validateCitationsForStream>[2],
          adapterOverrideOn,
        )
        adapterCitationGateResult = adapterCitationValidation.gateResult
        adapterCitationL1Count = adapterCitationValidation.layer1Count
        adapterCitationL2Verified = adapterCitationValidation.layer2Verified

        console.log(
          `[consume:adapter] citation_gate_l2 query_id=${queryId} ` +
            `result=${adapterCitationValidation.gateResult} layer1=${adapterCitationValidation.layer1Count} ` +
            `verified=${adapterCitationValidation.layer2Verified} leaked=${adapterCitationValidation.layer2Leaked}` +
            (adapterOverrideOn && adapterCitationValidation.gateResult === 'WARN' && adapterCitationValidation.layer1Count > 0 ? ' override=on' : '') +
            ` reason="${adapterCitationValidation.gateReason}"`
        )

        if (adapterCitationValidation.dataPart) {
          writer.write({ type: 'data-citation-gate', data: adapterCitationValidation.dataPart })
        }

        if (adapterCitationValidation.gateResult === 'WARN') {
          emit({
            event: 'step_done',
            query_id: queryId,
            step: {
              query_id: queryId,
              conversation_id: finalConversationId,
              step_seq: nextSeq(),
              step_name: 'citation_warn',
              step_type: 'deterministic',
              status: 'done',
              started_at: new Date().toISOString(),
              completed_at: new Date().toISOString(),
              latency_ms: 0,
              data_summary: {
                result: adapterCitationValidation.gateReason,
                citation_count: adapterCitationValidation.layer1Count,
              },
              payload: {},
            },
          })
        } else if (adapterCitationValidation.gateResult === 'ERROR') {
          console.error(
            `[consume:adapter] citation_gate_l2 HARD_BLOCK (non-throwing) ` +
            `query_id=${queryId} reason="${adapterCitationValidation.gateReason}"`
          )
          emit({
            event: 'step_done',
            query_id: queryId,
            step: {
              query_id: queryId,
              conversation_id: finalConversationId,
              step_seq: nextSeq(),
              step_name: 'citation_error',
              step_type: 'deterministic',
              status: 'error',
              started_at: new Date().toISOString(),
              completed_at: new Date().toISOString(),
              latency_ms: 0,
              data_summary: { result: adapterCitationValidation.gateReason, citation_count: adapterCitationValidation.layer1Count },
              payload: {},
            },
          })
        }
      } catch (err) {
        console.error('[consume:adapter] citation gate error', err)
      }
      // ── 3.cutover (G5b_onfinish) — shared onFinish write-through ─────
      // Routes the adapter path's onFinish stage through the same helper
      // the legacy synthesis-orchestrator path uses (parity is enforced by
      // onfinish_parity.golden.test.ts). Closes the prior adapter gaps:
      //   • data-cost emit (Observatory cost tile)
      //   • lastAssistantMetadata in persistence (R10 PerMessageDetailsDrawer)
      //   • per-citation data-citation parts (β4 SIG.MSR enrichment)
      //   • data-correction / data-out-of-domain markers (D.3)
      //   • pendingStreamWriter.clear() (γ7)
      //   • blind-mode prediction-ledger append (PPL)
      if (adapterAccumulatedText) {
        // Assign fresh UUIDs for all messages — client-side message IDs
        // (e.g. "yhJSXqHyqhawY9an") are not valid UUIDs and would fail
        // the conversation_messages.id UUID column constraint.
        const persistMsgs: UIMessage[] = [
          ...(messages as UIMessage[]).map(m => ({ ...m, id: crypto.randomUUID() } as UIMessage)),
          {
            id: crypto.randomUUID(),
            role: 'assistant' as const,
            parts: [{ type: 'text', text: adapterAccumulatedText }],
          } as UIMessage,
        ]
        // Per-layer token aggregation (closure over validToolResults).
        const tokensForAdapter = (predicate: (toolName: string) => boolean): number => {
          let chars = 0
          for (const tb of validToolResults) {
            if (!predicate(tb.tool_name)) continue
            for (const r of tb.results) chars += r.content.length
          }
          return Math.ceil(chars / 4)
        }
        const lastUserAdapter = (messages as UIMessage[])
          .filter(m => m.role === 'user').at(-1)
        const lastUserAdapterText = ((lastUserAdapter?.parts ?? []) as Array<{ type: string; text?: string }>)
          .filter(p => p.type === 'text')
          .map(p => p.text ?? '')
          .join(' ')
          .trim()
        const adapterLastAssistantMetadata: Record<string, unknown> = {
          custom: {
            model: modelId,
            queryId,
            planning_model_id: plannerModelId,
            planning_latency_ms: plannerLatencyMs,
            disclosure_tier: audienceTier,
            query_class: plan.query_class,
            stack: selectedStack,
            style,
            pipeline: 'v2-adapter',
            conversationId: finalConversationId,
          },
        }
        await runOnFinishWriteThrough(
          {
            pipelineKind: 'agentic',
            queryId,
            conversationId: finalConversationId,
            chartId,
            userUid,
            isFirstTurn,
            lelContextEnabled,
            finalMessages: persistMsgs,
            assistantText: adapterAccumulatedText,
            lastUserQuery: lastUserAdapterText,
            lastAssistantMetadata: adapterLastAssistantMetadata,
            modelId,
            modelMaxContext: modelMeta.maxInputTokens ?? null,
            // Adapter path has no usageHolder — cost emit is suppressed.
            synthUsage: null,
            synthesisElapsedMs: Date.now() - adapterStartMs,
            citationGate: {
              gateResult: adapterCitationGateResult,
              layer1Count: adapterCitationL1Count,
              layer2Verified: adapterCitationL2Verified,
            },
            contextAssembly: {
              l1_tokens: tokensForAdapter(n => [
                'chart_facts_query', 'divisional_query', 'kp_query',
                'manifest_query', 'query_kp_ruling_planets', 'query_varshaphala',
                'saham_query', 'temporal', 'timeline_query',
              ].includes(n)),
              l2_5_signal_tokens: tokensForAdapter(n => [
                'msr_sql', 'query_msr_aggregate', 'query_signal_state',
              ].includes(n)),
              l2_5_pattern_tokens: tokensForAdapter(n => [
                'pattern_register', 'resonance_register',
                'contradiction_register', 'cluster_atlas',
              ].includes(n)),
              l4_tokens: tokensForAdapter(n => ['remedial_codex_query', 'domain_report_query'].includes(n)),
              vector_tokens: tokensForAdapter(n => n === 'vector_search'),
              cgm_tokens: tokensForAdapter(n => n === 'cgm_graph_walk'),
            },
            writer,
            emit,
          },
          {
            persistence: {
              writeMessages: (args) => writeConversationMessages(args),
            },
            pricing: {
              getPricing: (mid) => getModelPricingSync(mid),
              computeUsd: (pricing, tokens) =>
                computeCostUsd(pricing as Parameters<typeof computeCostUsd>[0], tokens),
            },
            contextAssemblyLog: (entry) => { void writeContextAssemblyLog(entry) },
            fetchMsrSnippets: (ids) => fetchMsrSnippets(ids),
            pendingStreamWriter,
            title: {
              generate: (msgs, c) => generateConversationTitle(msgs, c),
              update: (cid, t) => updateConversationTitle(cid, t).then(() => undefined),
            },
            predictionLedger: async (entry) => {
              try {
                const fs = await import('fs/promises')
                const path = await import('path')
                const ledgerPath = path.join(process.cwd(), '..', '06_LEARNING_LAYER',
                  'PREDICTION_LEDGER', 'prediction_ledger.jsonl')
                const line = JSON.stringify({
                  ...entry,
                  outcome: null,
                  confidence: null,
                  horizon: null,
                  falsifier: null,
                  note: 'Auto-logged blind-mode query. Outcome/confidence/horizon/falsifier to be filled by native.',
                }) + '\n'
                await fs.appendFile(ledgerPath, line, 'utf8')
              } catch {
                // Non-fatal — prediction ledger write failure must not block the response.
              }
            },
          },
        )
      }
      // W4 core step 4 — completeness receipt: emit near the end, after the floor tools ran
      // and synthesis finished, so the client can render served/empty/dark coverage for the
      // compiled B.11 floor (honest about the MCP↔web namespace gap via channel_note).
      if (completenessReceipt) {
        writer.write({
          type: 'data-completeness',
          data: completenessPart({
            channel: completenessReceipt.channel,
            served: completenessReceipt.served.map(s => ({ floor_item_id: s.floor_item_id, source: s.source })),
            empty: completenessReceipt.empty.map(e => ({ floor_item_id: e.floor_item_id, empty_reason: e.empty_reason })),
            dark: completenessReceipt.dark.map(d => ({ floor_item_id: d.floor_item_id, cr_row: d.cr_row, ...(d.note ? { note: d.note } : {}) })),
            coverage: completenessReceipt.coverage,
            channel_note: completenessReceipt.channel_note,
          }),
        })
      }
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      writer.write({ type: 'finish', finishReason: 'stop' } as any)
      writer.write({ type: 'data-stage', data: stagePart('synthesis', 'done', Date.now() - adapterStartMs) })
      writer.write({
        type: 'data-observability',
        data: observabilityPart({ query_id: queryId, trace_url: `/observatory/trace/${queryId}` }),
      })
      emit({ event: 'done', query_id: queryId })
    },
  })
  return createUIMessageStreamResponse({ stream: adapterStream })
}

/**
 * Paripraśna pipeline — SYNTHESIS STAGE (P0-C / RF-1).
 *
 * Port: `Interpretation & Adjudication`.
 *
 * Two halves, in the order the pre-decomposition closure ran them:
 *   1. `assembleSynthesisContext` — the prompt prefix: trimmed conversation
 *      history, the bundle's system content through consult's own
 *      temporal-anchored builder, and the PB-2/M-3 durable-summary splice into
 *      its FIXED structural slot (best-effort, non-fatal — a summary fault must
 *      never cost the reader their reading).
 *   2. `runSynthesisStage` — adapter wiring plus the stream loop that turns
 *      provider events into blocks, passes and seams.
 *
 * PASS/SEAM TRUTH: a pass boundary is derived PURELY from the engine's own
 * control flow — a `tool_use_complete` arriving AFTER prose was already emitted
 * in this pass. It is never inferred from the text. That rule is the reason the
 * seam machinery lives here, next to the loop that observes the control flow,
 * and not in `reading_parts.ts`, which only owns block mechanics.
 *
 * Gate 11 [integrity]: EVERY delta chunk is linted before it reaches the wire.
 * The residual — a leak pattern split exactly across a chunk boundary — is
 * covered by the assembler's whole-block backstop on commit.
 */

import type { ModelMessage, UIMessage } from 'ai'
import { convertToModelMessages } from 'ai'

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
  type AgenticLoopConfig,
} from '@/lib/synthesis/agentic_loop'
import { executeMCPTool } from '@/lib/synthesis/mcp_tool_executor'
import { buildChatToolsFromNames } from '@/lib/retrieval/registry/schema_utils'
import { buildConsultSystemContent } from '@/lib/pipelines/shared/run_adapter_dispatch'
import { lintReaderProse } from '@/lib/pariprashna/citations/register_leak_lint'
import type { ChartOrientation } from '@/lib/retrieval/orientation'
import type { PipelinePlan } from '@/lib/pipeline/types'
import type { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'

import { halt, proceed, resolveActivityLabel, type StageResult, type TurnParams } from './stage_context'
import { PASS_ONE } from './evidence_stage'
import { ReadingPartsAssembler, type OpenBlock } from './reading_parts'
import type { LegacyQueryPlan } from './plan_stage'

/**
 * deep_dive raises the agentic-loop iteration cap so the model can retrieve
 * exhaustively across adaptive passes — the web engine's "dossier / maximal
 * chart coverage" lever (the deterministic B.11 + dasha floors always run; this
 * widens the ADAPTIVE re-entry budget on top of them).
 */
export const DEEP_DIVE_MAX_ITERATIONS = 16

const STACK_TO_ADAPTER: Partial<Record<string, StackId>> = {
  anthropic: 'anthropic',
  gemini: 'google',
  gpt: 'openai',
  deepseek: 'deepseek',
  nim: 'nvidia',
}

const AGENTIC_PROVIDERS = new Set<string>(['anthropic', 'google', 'openai', 'deepseek', 'nvidia'])

export interface SynthesisContext {
  /** The full system prefix (bundle + guidance + durable-summary splice). */
  systemContentWithSummary: string
  /**
   * The trimmed history the adapter messages are built from. Computed HERE and
   * carried forward rather than recomputed in `runSynthesisStage`: the
   * pre-decomposition closure called `convertToModelMessages` exactly once.
   */
  trimmedConversationHistory: ModelMessage[]
}

export async function assembleSynthesisContext(args: {
  messages: UIMessage[]
  bundle: { assets: unknown }
  plan: PipelinePlan
  orientation: ChartOrientation | null
  conversationId: string
}): Promise<SynthesisContext> {
  const { messages, bundle, plan, orientation, conversationId } = args

  const trimmedConversationHistory: ModelMessage[] = await convertToModelMessages(
    messages.filter((m) => m.role === 'user' || m.role === 'assistant').slice(-5).slice(0, -1),
  )
  const bundleSystemContent = (bundle.assets as Array<{ content: string }>)
    .map((a) => a.content)
    .filter(Boolean)
    .join('\n\n')
  const currentMahaAntar =
    orientation?.chart_header?.current_maha_antar ?? orientation?.dasha_context?.current_maha_antar ?? null
  const systemContent = buildConsultSystemContent({
    bundleSystemContent,
    synthesisGuidance: plan.synthesis_guidance,
    nowContextDate: new Date().toISOString().slice(0, 10),
    currentMahaAntar,
  })

  // ── PB-2/M-3 (SMṚTI durable summaries) — narrow, additive splice. ──────────
  // Folds a durable, citation-preserving summary of EARLIER canonical turns
  // into a FIXED structural slot ahead of the system content built above
  // (src/lib/pariprashna/summaries/assemble.ts) so the assembled prefix's
  // cache-relevant structure is unchanged turn-to-turn when no new
  // summarization threshold crossing occurred. Best-effort and non-fatal, same
  // convention as the orientation promise's `.catch()`.
  //
  // Assistant turns persist canonically via lane M-2's `writeTurn`, so
  // `message_parts` rows exist for pariprashna conversations and this splice is
  // LIVE. Disclosed scope residual: only assistant rows are canonical today —
  // user/history messages still persist via the legacy path, so summaries are
  // built from assistant turns only.
  let conversationSummaryText: string | null = null
  try {
    const { getConversationSummaryForSplice } = await import('@/lib/pariprashna/summaries/splice')
    conversationSummaryText = await getConversationSummaryForSplice(conversationId)
  } catch (err) {
    console.error('[pariprashna] durable-summary splice failed (non-fatal):', err)
  }
  const { assembleSynthesisPrefix } = await import('@/lib/pariprashna/summaries/assemble')
  const systemContentWithSummary = assembleSynthesisPrefix({
    precedingBlock: systemContent ?? '',
    summaryText: conversationSummaryText,
  })

  return { systemContentWithSummary, trimmedConversationHistory }
}

export interface SynthesisStageOutput {
  assembler: ReadingPartsAssembler
  accumulatedText: string
  synthesisStartedAt: number
  finalPassId: number
}

export async function runSynthesisStage(args: {
  em: PariprashnaEmitter
  request: Request
  messages: UIMessage[]
  queryText: string
  params: TurnParams
  queryPlan: LegacyQueryPlan
  context: SynthesisContext
}): Promise<StageResult<SynthesisStageOutput>> {
  const { em, request, queryText, params, queryPlan, context } = args
  const { systemContentWithSummary, trimmedConversationHistory } = context

  // ── Adapter + agentic loop wiring (SAME engine as consult). ────────────────
  const adapterId: StackId | undefined =
    STACK_TO_ADAPTER[params.selectedStack] ?? (params.modelMeta.provider as StackId | undefined)
  if (!adapterId) {
    em.error({ code: 'NO_ADAPTER', message: `No adapter for stack=${params.selectedStack}.`, retryable: false, phase: 'synthesize' })
    return halt('error')
  }
  const adapterMessages = buildAdapterMessages(trimmedConversationHistory, queryText)
  let adapterChatReq: ChatRequest = buildAdapterChatRequest(adapterMessages, params.modelId, systemContentWithSummary)
  const adapter = getAdapter(adapterId)
  const useAgenticLoop = AGENTIC_PROVIDERS.has(adapterId)
  const loopMaxIterations = params.deepDive ? DEEP_DIVE_MAX_ITERATIONS : 8

  if (useAgenticLoop) {
    const providerManifest = adapter.getManifest()
    const toolsCfg = adapter.tools({
      toolLoopMode: providerManifest.adaptiveToolLoop,
      tools: buildChatToolsFromNames(queryPlan.tools_authorized ?? []),
      maxIterations: loopMaxIterations,
    })
    adapterChatReq = { ...adapterChatReq, toolsConfig: toolsCfg, tools: toolsCfg.tools }
  }

  // ── Synthesis stream → prose blocks + adaptive-pass seams. ─────────────────
  em.phase({ phase: 'synthesize', status: 'start', pass_id: PASS_ONE })
  const synthesisStartedAt = Date.now()

  // Pass/seam state — derived PURELY from the engine's own control flow
  // (tool-use events after prose), never from text/prose heuristics.
  const assembler = new ReadingPartsAssembler(em, PASS_ONE)
  let proseSeenInPass = false
  let awaitingResume = false
  let lastToolInSeam = ''

  const baseLoopConfig: AgenticLoopConfig | undefined = LOOP_CONFIG_BY_PROVIDER[adapterId]
  const loopConfig: AgenticLoopConfig | undefined = baseLoopConfig
    ? { ...baseLoopConfig, maxIterations: loopMaxIterations }
    : undefined

  try {
    const chatStream =
      useAgenticLoop && loopConfig
        ? runAgenticLoop(adapter, adapterChatReq, (toolCall) => executeMCPTool(toolCall, { queryPlan }), loopConfig)
        : adapter.chat(adapterChatReq)

    for await (const event of chatStream) {
      if (request.signal.aborted) {
        assembler.commitBlock()
        return halt('aborted')
      }
      if (event.type === 'text_delta') {
        if (awaitingResume) {
          // Prose resumed after the engine re-entered retrieval → close seam.
          em.seamSet({ pass_id: assembler.passId, summary: lastToolInSeam ? `Consulted ${lastToolInSeam}` : 'Continued analysis' })
          em.phase({ phase: 'synthesize', status: 'start', pass_id: assembler.passId })
          awaitingResume = false
        }
        const blk: OpenBlock = assembler.ensureBlock('prose')
        // Gate 11 [integrity]: lint EVERY delta chunk before it reaches the
        // wire — the model's own prose directly references internal register
        // acronyms (confirmed in production: "(UCN §...)", "Cross-Domain
        // Linkage Matrix (CDLM)"), independent of the citation-sentinel path
        // this route already guards. Never fails the turn; a hit is scrubbed
        // and reported as a telemetry flag. Residual: a leak pattern split
        // exactly across a delta chunk boundary can still slip through here —
        // the assembler's whole-block lint on commit is the backstop.
        const deltaLint = lintReaderProse(event.text)
        const cleanDelta = deltaLint.clean
        if (deltaLint.leakCount > 0) {
          em.flag({
            code: 'register_leak_scrubbed',
            level: 'warn',
            detail: `${deltaLint.leakCount} internal identifier(s) scrubbed from streamed prose`,
          })
        }
        assembler.appendProse(blk, cleanDelta)
        proseSeenInPass = true
      } else if (event.type === 'thinking_delta') {
        const blk = assembler.ensureBlock('thinking')
        assembler.appendThinking(blk, event.thinking)
      } else if (event.type === 'tool_use_start') {
        em.activity({ key: `pass${assembler.passId}:tool:${event.id}`, label_key: resolveActivityLabel(event.name), pass_id: assembler.passId, status: 'running' })
      } else if (event.type === 'tool_use_complete') {
        // Engine re-entered retrieval. If prose was already emitted this pass,
        // THIS is a pass boundary (real control-flow truth).
        assembler.commitBlock()
        if (proseSeenInPass) {
          assembler.passId += 1
          proseSeenInPass = false
          lastToolInSeam = event.name
          em.phase({ phase: 'retrieve', status: 'start', pass_id: assembler.passId })
          em.seamOpen({ pass_id: assembler.passId, label_key: `pariprashna.pass.${assembler.passId}` })
          awaitingResume = true
        } else {
          lastToolInSeam = event.name
        }
        em.activity({ key: `pass${assembler.passId}:tool:${event.id}`, label_key: resolveActivityLabel(event.name), pass_id: assembler.passId, status: 'done' })
      } else if (event.type === 'error') {
        console.error('[pariprashna] adapter error event:', event.error)
        em.flag({ code: 'adapter_error', level: 'warn', detail: event.error })
      }
    }
  } catch (adapterErr) {
    console.error('[pariprashna] synthesis stream error:', adapterErr)
    em.flag({ code: 'synthesis_stream_error', level: 'error', detail: String(adapterErr) })
  }
  assembler.commitBlock()
  em.phase({ phase: 'synthesize', status: 'end', pass_id: assembler.passId, ms: Date.now() - synthesisStartedAt })

  return proceed({
    assembler,
    accumulatedText: assembler.accumulatedText,
    synthesisStartedAt,
    finalPassId: assembler.passId,
  })
}

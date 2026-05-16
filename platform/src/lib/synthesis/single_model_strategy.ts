/**
 * MARSYS-JIS Stream D — Single-Model Synthesis Orchestrator
 * schema_version: 1.1 (Phase 6 — checkpoint hook points)
 *
 * Takes a validated retrieval bundle, picks a prompt template, wraps
 * retrieval tools for AI SDK tool-use, and calls streamText to produce the
 * synthesis response.
 *
 * Phase 6 adds three flag-gated checkpoint hooks:
 *   Hook 1 (post-resolve)  — checkpoint 4.5 runs before retrieval
 *   Hook 2 (post-retrieve) — checkpoint 5.5 runs before synthesis
 *   Hook 3 (post-synthesize) — checkpoint 8.5 runs in onFinish
 * All hooks are no-ops when their respective flags are OFF. Flag-OFF path is
 * byte-identical to the Phase 3 baseline.
 */

import 'server-only'

import { stepCountIs, smoothStream, tool } from 'ai'
import { streamBuildRaw } from '@/lib/adapters'
import { traceEmitter } from '@/lib/trace/emitter'
import type { TraceChunkItem } from '@/lib/trace/types'
import type { ModelMessage, ToolSet } from 'ai'
import { z } from 'zod'

import { resolveModel, googleProviderOptions, deepseekProviderOptions } from '@/lib/models/resolver'
import { getModelMeta, getReasoningMode, supports } from '@/lib/models/registry'
import { REASONING_NARRATION_GATE } from '@/lib/prompts/templates/shared'
function stripThinkBlocks(text: string): string {
  return text.replace(/<think>[\s\S]*?<\/think>\s*/gi, '').trimStart()
}
function extractReasoningTrace(text: string): { reasoning: string; answer: string } {
  const blocks: string[] = []
  const re = /<think>([\s\S]*?)<\/think>/gi
  let match: RegExpExecArray | null
  while ((match = re.exec(text)) !== null) {
    blocks.push(match[1].trim())
  }
  return { reasoning: blocks.join('\n\n'), answer: stripThinkBlocks(text) }
}
import { getDefaultRegistry } from '@/lib/prompts/index'
import { renderTemplate } from '@/lib/prompts/types'
import { getTool } from '@/lib/retrieve/index'
import { executeWithCache } from '@/lib/cache/index'
import { telemetry } from '@/lib/telemetry/index'
import { getFlag } from '@/lib/config/index'

import { runCheckpoint4_5 } from '@/lib/checkpoints/checkpoint_4_5'
import { runCheckpoint5_5 } from '@/lib/checkpoints/checkpoint_5_5'
import { runCheckpoint8_5 } from '@/lib/checkpoints/checkpoint_8_5'
import type { Checkpoint45Result, Checkpoint55Result, Checkpoint85Result } from '@/lib/checkpoints/types'
import { countSignalCitations } from './citation_check'
import { runAll } from '@/lib/validators/index'
import { writeLlmCallLog, resolveProvider } from '@/lib/db/monitoring-write'
import { computeCostUsd, getModelPricingSync } from '@/lib/llm/pricing'
import { persistObservation, computeCost } from '@/lib/llm/observability'
import { getStorageClient } from '@/lib/storage'
import type { ProviderName, TokenUsage } from '@/lib/llm/observability/types'
import { checkB11Compliance } from './b11_guard'
import { getMaxRetries } from './provider_quirks'
import type { Provider } from '@/lib/models/registry'

import type {
  SynthesisRequest,
  SynthesisResult,
  SynthesisMetadata,
  SynthesisAuditEvent,
  SynthesisOrchestrator,
  SynthesisUsage,
} from './types'

// Token-budget constants for pre-fetched content injection (FUB-2 + FUB-3)
const MAX_CHART_CONTEXT_TOKENS = 32768

export {
  STYLE_OUTPUT_CAP,
  CLASS_TOKEN_CAP,
  computeEffectiveMaxTokens,
} from './token_caps'
import {
  STYLE_OUTPUT_CAP,
  CLASS_TOKEN_CAP,
  computeEffectiveMaxTokens,
} from './token_caps'
const MAX_TOOL_RESULTS_TOKENS = 16384
// Rough chars-per-token estimate for truncation (conservative)
const CHARS_PER_TOKEN = 4

export class SingleModelOrchestrator implements SynthesisOrchestrator {
  async synthesize(request: SynthesisRequest): Promise<SynthesisResult> {
    const {
      query,
      query_plan,
      bundle,
      tool_results,
      conversation_history,
      selected_model_id,
      style,
      audience_tier,
      cache,
      conversation_id,
      onAuditEvent,
      abortSignal,
    } = request

    const started_at = new Date().toISOString()
    // BHISMA §4.6 — wall-clock start so the synthesis_done step carries
    // real latency, not 0. Captured at synthesize() entry; onFinish reads it.
    const synthesisStartMs = Date.now()

    // ── Hook 1: Checkpoint 4.5 (post-resolve, pre-retrieve) ──────────────────
    // No-op when CHECKPOINT_4_5_ENABLED=false (flag-OFF = skipped result returned).
    let c4_5Result: Checkpoint45Result | undefined
    if (getFlag('CHECKPOINT_4_5_ENABLED')) {
      c4_5Result = await runCheckpoint4_5({
        query,
        query_plan,
        discarded_alternatives: [],
      })
      // CheckpointHaltError thrown by runCheckpoint4_5 when FAIL_HARD=true; propagates up.
    }

    // ── Hook 2: Checkpoint 5.5 (post-retrieve, pre-synthesis) ────────────────
    // Skipped when 4.5 halted (error thrown above) or flag is OFF.
    let c5_5Result: Checkpoint55Result | undefined
    if (getFlag('CHECKPOINT_5_5_ENABLED')) {
      c5_5Result = await runCheckpoint5_5({
        query,
        query_plan,
        bundle,
        tool_results,
      })
      // CheckpointHaltError thrown by runCheckpoint5_5 when FAIL_HARD=true; propagates up.
    }

    // ── Synthesis setup (unchanged from Phase 3 baseline) ────────────────────

    const registry = getDefaultRegistry()
    const template = registry.get(query_plan.query_class, audience_tier, 'single_model')

    const variables: Record<string, string> = {
      chart_name: request.chart_context?.name ?? 'the native',
      birth_date: request.chart_context?.birth_date ?? '<birth date unavailable>',
      birth_time: request.chart_context?.birth_time ?? '<birth time unavailable>',
      birth_place: request.chart_context?.birth_place ?? '<birth place unavailable>',
      bundle_summary: bundle.mandatory_context
        .map(e => `${e.canonical_id} (${e.role})`)
        .join(', '),
      tools_available: query_plan.tools_authorized.join(', '),
    }
    let renderedPrompt = renderTemplate(template, variables, style)

    // ── Reasoning-mode prompt gating ─────────────────────────────────────────
    // REASONING_NARRATION_GATE instructs models to emit ‹reasoning›…‹/reasoning›
    // inline markers that parseMarkers extracts client-side. This only makes sense
    // for 'markers' models (DeepSeek V4 Pro / R1 — they follow the gate faithfully).
    //
    // For 'native' models (Gemini 2.5): reasoning arrives via SDK-level
    // type:'reasoning' UIMessage parts. Including the marker gate is noise that
    // causes the model to ALSO embed ‹reasoning› tags in visible text (BUG-E root
    // cause). Stripping it cleanly eliminates the double-channel confusion.
    //
    // For 'none' models (GPT, Anthropic, NVIDIA): the gate wastes tokens and
    // produces confusing prompts that invite unsupported output formats.
    if (getReasoningMode(selected_model_id) !== 'markers') {
      renderedPrompt = renderedPrompt.replace(`\n\n${REASONING_NARRATION_GATE}`, '')
    }

    // ── FUB-2: Append chart context block from vector_search floor-asset results ─
    // Eagerly inject semantic chunks from floor-role assets so the LLM has
    // actual FORENSIC/MSR content in context before calling any tools.
    const vsResults = tool_results
      .filter(tb => tb.tool_name === 'vector_search')
      .flatMap(tb => tb.results)

    if (vsResults.length > 0 && bundle.mandatory_context.some(e => e.role === 'floor')) {
      const maxChars = MAX_CHART_CONTEXT_TOKENS * CHARS_PER_TOKEN
      const chunks = vsResults
        .map(r => `[chunk:${r.signal_id ?? 'unknown'}]\n${r.content}`)
        .join('\n\n---\n\n')
      const truncated = chunks.length > maxChars ? chunks.slice(0, maxChars) + '\n[...truncated]' : chunks
      renderedPrompt += `\n\n<CHART_CONTEXT_BLOCK source="vector_search\n${truncated}\n</CHART_CONTEXT_BLOCK>`
    }

    // ── FUB-3: Append pre-fetched tool_results (non-vector_search) ─────────────
    // MSR signals and other eagerly retrieved bundles are appended here so the
    // LLM sees them even if it doesn't re-invoke those tools.
    const nonVsResults = tool_results.filter(tb => tb.tool_name !== 'vector_search')
    if (nonVsResults.length > 0) {
      const maxChars = MAX_TOOL_RESULTS_TOKENS * CHARS_PER_TOKEN
      const blocks = nonVsResults
        .map(tb =>
          tb.results
            .map(r => `[signal:${r.signal_id ?? tb.tool_name}] ${r.content}`)
            .join('\n')
        )
        .join('\n\n')
      const truncated = blocks.length > maxChars ? blocks.slice(0, maxChars) + '\n[...truncated]' : blocks
      renderedPrompt += `\n\n<PRE_FETCHED_TOOL_RESULTS>\n${truncated}\n</PRE_FETCHED_TOOL_RESULTS>`
    }

    // ── Thinking-mode prompt patch (deepseek-v4-pro) ─────────────────────────
    // With thinking=enabled the AI SDK tools are stripped at call time
    // (synthesisTools=undefined below). But the rendered system prompt still
    // contains two sentences that invite tool calls, causing the model to
    // emit <maction_call> XML as plain text in the answer stream:
    //   1. TOOL_AVAILABILITY — "You may call additional retrieval tools..."
    //   2. PRESCRIPTIVE_CITATION_GATE tail — "If no MSR signals have been
    //      retrieved yet, call the msr_sql or query_signal_state tool..."
    // Patch both out before the prompt is frozen into the ModelMessage.
    if (deepseekProviderOptions(selected_model_id, 'synthesis')) {
      renderedPrompt = renderedPrompt
        .replace(
          `You may call additional retrieval tools to extend the bundle. Tools available: ${variables.tools_available}.`,
          'All retrieval data has been pre-fetched above in CHART_CONTEXT_BLOCK and PRE_FETCHED_TOOL_RESULTS. Synthesize from the pre-fetched context only — do not call any tools.',
        )
        .replace(
          'If no MSR signals have been retrieved yet, call the msr_sql or query_signal_state tool to fetch relevant signals before composing your answer.',
          'MSR signals are pre-fetched above in PRE_FETCHED_TOOL_RESULTS. Cite them as (→ SIG.MSR.NNN) from what is visible in context.',
        )
    }

    // ── Trace: context_assembly step ─────────────────────────────────────────
    // Emit after both FUB-2 and FUB-3 blocks are assembled so token counts
    // reflect the actual content entering the LLM context.
    // Fire-and-forget — never awaited.
    {
      const qid = query_plan.query_plan_id
      const nToolSteps = query_plan.tools_authorized?.length ?? 0
      // UQE-9: prefer caller-allocated seq (atomic counter in route.ts) so the
      // value is unique across the per-request trace; fall back to legacy
      // arithmetic when no seq was passed in.
      const ctxSeq = request.context_assembly_seq ?? (3 + nToolSteps)

      const l1Items: TraceChunkItem[] = vsResults.map(r => ({
        id: r.signal_id ?? 'unknown',
        source: 'vector_search',
        layer: 'L1' as const,
        token_estimate: Math.ceil(r.content.length / 4),
        text: r.content,
      }))

      const l2Items: TraceChunkItem[] = nonVsResults.flatMap(tb =>
        tb.results.map((r: { signal_id?: string; content: string }) => ({
          id: r.signal_id ?? tb.tool_name,
          source: tb.tool_name,
          layer: 'L2.5' as const,
          token_estimate: Math.ceil(r.content.length / 4),
          text: r.content,
        }))
      )

      const systemChars = renderedPrompt.length
      const systemTokens = Math.ceil(systemChars / 4)
      const l1Tokens = l1Items.reduce((s, i) => s + i.token_estimate, 0)
      const l2Tokens = l2Items.reduce((s, i) => s + i.token_estimate, 0)
      const totalTokens = l1Tokens + l2Tokens + systemTokens

      traceEmitter.emitStep({
        event: 'step_done',
        query_id: qid,
        step: {
          query_id: qid,
          conversation_id,
          step_seq: ctxSeq,
          step_name: 'context_assembly',
          step_type: 'deterministic',
          status: 'done',
          started_at: new Date().toISOString(),
          completed_at: new Date().toISOString(),
          latency_ms: 0,
          data_summary: { token_estimate: totalTokens },
          payload: {
            l1_tokens: l1Tokens,
            l2_tokens: l2Tokens,
            system_tokens: systemTokens,
            total_tokens: totalTokens,
            l1_items: l1Items,
            l2_items: l2Items,
          },
        },
      })
    }

    let toolsForModel: ToolSet | undefined
    if (supports(selected_model_id, 'tool-use')) {
      const wrappedTools: ToolSet = {}
      for (const toolName of query_plan.tools_authorized) {
        wrappedTools[toolName] = tool({
          description: `Retrieval tool: ${toolName}. Use to extend the context bundle.`,
          inputSchema: z.object({ query_hint: z.string().optional() }),
          execute: async () => {
            const t = getTool(toolName)
            if (!t) return { error: `Tool ${toolName} not found` }
            // W2-TRACE-A: thread planner-supplied params if the plan carries them.
            const richToolCalls = (query_plan as { tool_calls?: Array<{ tool_name: string; params: Record<string, unknown> }> }).tool_calls ?? []
            const plannerParams = richToolCalls.find(tc => tc.tool_name === toolName)?.params
            const toolBundle = await executeWithCache(t, query_plan, cache, plannerParams)
            return { results: toolBundle.results, tool_name: toolName }
          },
        })
      }
      toolsForModel = Object.keys(wrappedTools).length > 0 ? wrappedTools : undefined
    }

    // All registry models use the standard calling convention: system message
    // + history + user turn. Prompt-caching header is added for Anthropic models.
    const historyMessages: ModelMessage[] = conversation_history

    // ── B.11 Whole-Chart-Read guard ───────────────────────────────────────────
    // Check that the assembled context contains the required L2.5 layers before
    // invoking the synthesis LLM. Zero overhead in the happy path (string scan).
    {
      const b11 = checkB11Compliance(renderedPrompt)
      if (!b11.compliant) {
        console.log(JSON.stringify({
          event: 'B11_VIOLATION',
          missing: b11.missingLayers,
          present: b11.presentLayers,
          query_id: query_plan.query_plan_id ?? null,
          query_class: query_plan.query_class,
        }))
        // Prepend the annotation to the context so the synthesis LLM is aware
        // of the partial compliance and can note it in its answer.
        if (b11.annotation) {
          renderedPrompt = b11.annotation + '\n\n' + renderedPrompt
        }
      }
    }

    // Phase 3 — planner-emitted synthesis guidance (replaces context_assembler).
    if (request.synthesis_guidance && request.synthesis_guidance.trim().length > 0) {
      renderedPrompt += `\n\n---\n\nSYNTHESIS GUIDANCE (from planner):\n${request.synthesis_guidance.trim()}`
    }

    const systemMessage: ModelMessage = supports(selected_model_id, 'prompt-caching')
      ? {
          role: 'system',
          content: renderedPrompt,
          providerOptions: {
            anthropic: { cacheControl: { type: 'ephemeral' } },
          },
        }
      : {
          role: 'system',
          content: renderedPrompt,
        }

    const modelMessages: ModelMessage[] = [
      systemMessage,
      ...historyMessages,
      { role: 'user', content: query },
    ]

    const modelMeta = getModelMeta(selected_model_id)

    const metadata: SynthesisMetadata = {
      synthesis_prompt_version: template.version,
      synthesizer_model_id: selected_model_id,
      bundle_hash: bundle.bundle_hash,
      started_at,
    }

    // Populated synchronously at the top of onFinish (before any await), so
    // it is set by the time the 'finish' SSE part fires in toUIMessageStreamResponse.
    const methodologyBlockHolder: { value: string | null } = { value: null }
    const usageHolder: { value: SynthesisUsage | null } = { value: null }

    // UQE-16 — Per-style output token cap. Prevents over-elaboration by capping
    // the synthesis response at a style-appropriate ceiling well below the model's
    // hard maximum. The model's maxOutputTokens is the absolute ceiling; the style
    // cap is a tighter practical limit so answers stay focused.
    //
    // Keys MUST match ConsumeStyle values ('acharya' | 'brief' | 'client').
    // Previous keys were 'concise'/'detailed'/'technical' — none matched the
    // actual ConsumeStyle union, causing ALL queries to fall through to the
    // ?? 2000 default and get truncated at ~1975 tokens (finishReason: "length").
    //
    //   brief   → 1200 tokens  (~900 words)  — direct answer, no padding
    //   client  → 3500 tokens  (~2600 words) — structured with evidence
    //   acharya → 8000 tokens  (~6000 words) — full acharya-grade depth
    //
    // These caps apply to the synthesis output only, not to tool-use steps.
    const styleCap = STYLE_OUTPUT_CAP[style ?? 'acharya'] ?? 65536
    const classCap = CLASS_TOKEN_CAP[query_plan.query_class] ?? 65536
    const contentCap = computeEffectiveMaxTokens(
      styleCap,
      classCap,
      modelMeta?.maxOutputTokens,
    )
    // DeepSeek V4 Pro with thinking=enabled: max_tokens covers BOTH thinking
    // tokens AND text output tokens in a single budget. Without headroom,
    // the model consumes 4 000–8 000 tokens for CoT and the text answer is
    // truncated mid-sentence. Add 10 000-token thinking headroom so the
    // answer text always receives the full content cap.
    const isThinkingModeSynthesis = !!deepseekProviderOptions(selected_model_id, 'synthesis')
    const effectiveMaxTokens = isThinkingModeSynthesis
      ? Math.min(contentCap + 10_000, modelMeta?.maxOutputTokens ?? contentCap + 10_000)
      : contentCap

    // UQE-2 (W2-BUGS B2W-5) — temperature gate: deterministic for single-truth
    // queries (factual lookups, prescriptive remedies, time-indexed predictions),
    // mild variation for exploratory / multi-perspective queries.
    const synthesisTemperature: number =
      ['factual', 'remedial', 'predictive'].includes(query_plan.query_class)
        ? 0
        : 0.3

    // Synthesis retry guard — bounded per-provider (α5 policy).
    // NIM uses maxRetries: 0 (adapter has its own logic); all other providers
    // allow 1 SDK-level retry on transient network/5xx before the route-level
    // QG6.1 fallback activates. Persistent failures surface after 1 retry.
    const synthesisMaxRetries = getMaxRetries((modelMeta?.provider ?? 'anthropic') as Provider)
    const isNvidiaSynthesis = modelMeta?.provider === 'nvidia'

    // DeepSeek V4 Pro thinking=enabled + tools + tool_choice:none is an
    // unsupported combination on the DeepSeek API: the model routes thinking
    // content into delta.content (text) instead of delta.reasoning_content,
    // so <think> blocks appear in the visible stream. All retrieval data is
    // already pre-injected via FUB-2/FUB-3 — tools are unnecessary here.
    const synthesisTools = isThinkingModeSynthesis ? undefined : toolsForModel

    const result = streamBuildRaw({
      model: resolveModel(selected_model_id),
      messages: modelMessages,
      tools: synthesisTools,
      // BUG-B fix: synthesis is the text-generation phase; all retrieval tools
      // have already executed. Prohibit the synthesis model from calling any
      // tool so it must generate text. Without this, tool-capable models
      // (gemini-2.5-pro) may emit finish_reason=tool-calls with empty
      // final_output instead of a synthesis response.
      // Not applied to thinking-mode models (synthesisTools is undefined above).
      toolChoice: synthesisTools ? ('none' as const) : undefined,
      stopWhen: stepCountIs(5),
      maxOutputTokens: effectiveMaxTokens,
      temperature: synthesisTemperature,
      experimental_transform: smoothStream({ delayInMs: 20, chunking: 'word' }),
      ...(abortSignal && { abortSignal }),
      maxRetries: synthesisMaxRetries,
      // Google-specific: disable safety filters (Jyotish content triggers
      // DANGEROUS_CONTENT mid-stream) + cap thinking budget (avoids 30-90s
      // hang before first visible token). See resolver.googleProviderOptions.
      // DeepSeek V4 Pro: activate thinking=enabled for synthesis CoT.
      // Merge at the top-level provider key — no model is both google and deepseek.
      ...((googleProviderOptions(selected_model_id) || deepseekProviderOptions(selected_model_id, 'synthesis')) && {
        providerOptions: {
          ...(googleProviderOptions(selected_model_id)?.google && { google: googleProviderOptions(selected_model_id)!.google }),
          ...(deepseekProviderOptions(selected_model_id, 'synthesis')?.deepseek && { deepseek: deepseekProviderOptions(selected_model_id, 'synthesis')!.deepseek }),
        },
      }),
      onFinish: async ({
        finishReason,
        usage,
        text,
      }: {
        finishReason: string
        usage?: { inputTokens?: number; outputTokens?: number }
        text?: string
      }) => {
        // G.4: capture wall-clock latency once at onFinish entry for consistent
        // use in trace + deepseek instrumentation. Compare synthesisLatencyMs
        // against llm_call_log.latency_ms (same query_id) to separate LLM
        // call latency from pre-stream context-assembly overhead.
        const synthesisLatencyMs = Date.now() - synthesisStartMs

        // BHISMA-B1 §3.4 — defensive: even with extractReasoningMiddleware,
        // strip any stray <think>…</think> from the final text before downstream
        // use so neither the audit, methodology-block extractor, nor the trace
        // payload preview accidentally captures reasoning content.
        // BUG-4: broaden guard to cover all thinking models (deepseek-v4-pro etc.)
        // BUG-E fix: gemini-2.5-* emits ‹reasoning›...‹/reasoning› markers
        // in synthesis output. Extend isThinkingModel to cover these so
        // extractReasoningTrace / stripThinkBlocks runs and strips the tags
        // before validators and the audit event see the final text.
        const isThinkingModel =
          selected_model_id === 'deepseek-reasoner' ||
          selected_model_id.startsWith('gemini-2.5') ||
          getModelMeta(selected_model_id)?.hint?.toLowerCase().includes('thinking') ||
          false
        // G.4: DeepSeek synthesis latency instrumentation.
        // If synthesisLatencyMs >> per-call latency in llm_call_log, the bottleneck
        // is context assembly (pre-stream); if approximately equal, it is the LLM.
        if (selected_model_id.startsWith('deepseek')) {
          console.warn(
            '[synthesis][deepseek] latency_ms=%d query_id=%s model=%s finish=%s',
            synthesisLatencyMs,
            query_plan.query_plan_id,
            selected_model_id,
            finishReason,
          )
        }
        const rawText = text ?? ''
        const { reasoning: r1Reasoning, answer: _cleanAnswer } = isThinkingModel
          ? extractReasoningTrace(rawText)
          : { reasoning: '', answer: stripThinkBlocks(rawText) }
        // BUG-4: for thinking models whose entire output is inside <think> blocks,
        // the answer after stripping is empty — fall back to the reasoning content.
        let cleanText = (isThinkingModel && _cleanAnswer === '' && r1Reasoning)
          ? r1Reasoning
          : _cleanAnswer

        // BUG-C fix: if the synthesis model called a tool instead of generating
        // text (finish_reason=tool-calls), cleanText will be empty. This
        // produces a silent blank response to the user. Detect it here and
        // replace with a visible, actionable error message so the user knows
        // the pipeline failed and can retry with a different stack.
        // BUG-B's toolChoice:'none' should prevent this from occurring, but
        // this guard catches any provider that ignores toolChoice.
        if (cleanText.trim() === '' && finishReason === 'tool-calls') {
          console.error(
            '[synthesis] BUG-C: empty output — model=%s called a tool instead of generating text.' +
            ' query_id=%s output_tokens=%d. Surfacing error message to user.',
            selected_model_id,
            query_plan.query_plan_id,
            usage?.outputTokens ?? 0,
          )
          cleanText =
            `⚠️ The synthesis model (${selected_model_id}) attempted to call a retrieval tool ` +
            `during the text-generation phase instead of producing a response. ` +
            `This is a model configuration issue, not a data issue. ` +
            `Please try again — if the problem persists, switch to the Gemini stack.`
        }

        // Secondary guard: catch any other empty-output case regardless of
        // finish reason (e.g. provider timeout, content filter wipe).
        if (cleanText.trim() === '' && finishReason !== 'error') {
          console.warn(
            '[synthesis] empty output: model=%s finish=%s query_id=%s — returning placeholder.',
            selected_model_id, finishReason, query_plan.query_plan_id,
          )
          cleanText =
            `⚠️ The synthesis model returned an empty response (finish_reason=${finishReason}). ` +
            `Please try again.`
        }

        // Synchronous extraction — before any await — so the value is
        // available when the 'finish' SSE part fires in the route handler.
        // BUG-5: also strip the fence from cleanText so stored messages don't
        // accumulate methodology blocks on each turn.
        const mbMatch = cleanText.match(/^```marsys_methodology_block\n([\s\S]*?)\n```\n?/m)
        methodologyBlockHolder.value = mbMatch ? mbMatch[1].trim() : null
        if (mbMatch) {
          cleanText = cleanText.replace(mbMatch[0], '').trim()
        }

        // Synchronously capture token counts before any await — matches the
        // methodologyBlockHolder pattern so the outer onFinish can forward them
        // to writeObservatoryQueryEvent for cost computation.
        usageHolder.value = {
          inputTokens: usage?.inputTokens,
          outputTokens: usage?.outputTokens,
          cacheReadInputTokens: (usage as { cacheReadInputTokens?: number })?.cacheReadInputTokens,
          cacheCreationInputTokens: (usage as { cacheCreationInputTokens?: number })?.cacheCreationInputTokens,
        }

        // ── Trace: synthesis done ─────────────────────────────────────────────
        // Fire-and-forget — never awaited.
        {
          const qid = query_plan.query_plan_id
          const nToolSteps = query_plan.tools_authorized?.length ?? 0
          // UQE-9: same precedence rule as ctxSeq above — caller's atomic
          // counter wins when present.
          const synthesisSeq = request.synthesis_seq ?? (3 + nToolSteps + 1)
          traceEmitter.emitStep({
            event: 'step_done',
            query_id: qid,
            step: {
              query_id: qid,
              conversation_id,
              step_seq: synthesisSeq,
              step_name: 'synthesis',
              step_type: 'llm',
              status: 'done',
              started_at: new Date(synthesisStartMs).toISOString(),
              completed_at: new Date().toISOString(),
              latency_ms: synthesisLatencyMs,
              data_summary: {
                model: selected_model_id,
                input_tokens: usage?.inputTokens ?? 0,
                output_tokens: usage?.outputTokens ?? 0,
                // BHISMA §4.6 + §4.7 — citation count on the synthesis output
                // so the trace panel can flag low-citation responses per query
                // class. Threshold + meets-flag derived on the consumer side
                // from query_class via citationThresholdForClass / hasMinimumCitations.
                citation_count: countSignalCitations(cleanText),
                temperature: synthesisTemperature,
              },
              payload: {
                prompt_preview: cleanText.slice(0, 500),
                ...(isThinkingModel && r1Reasoning ? { reasoning_trace: r1Reasoning.slice(0, 4000) } : {}),
              },
            },
          })
        }

        telemetry.recordMetric('synthesis', 'stream_finish', 1, {
          finishReason,
          model: selected_model_id,
        })
        telemetry.recordCost(
          'synthesis',
          selected_model_id,
          usage?.inputTokens ?? 0,
          usage?.outputTokens ?? 0,
          0,
        )

        // ── MON-5: llm_call_log write (synthesis stage) ──────────────────────
        // Fire-and-forget. reasoning_tokens populated only for models that
        // surface a separate reasoning trace (deepseek-reasoner today).
        void writeLlmCallLog({
          query_id: query_plan.query_plan_id,
          conversation_id: conversation_id ?? null,
          call_stage: 'synthesis',
          model_id: selected_model_id,
          provider: resolveProvider(selected_model_id),
          input_tokens: usage?.inputTokens ?? null,
          output_tokens: usage?.outputTokens ?? null,
          reasoning_tokens: isThinkingModel && r1Reasoning
            ? Math.ceil(r1Reasoning.length / 4)
            : null,
          latency_ms: synthesisLatencyMs,
          cost_usd: computeCostUsd(getModelPricingSync(selected_model_id), {
            input_tokens: usage?.inputTokens ?? null,
            output_tokens: usage?.outputTokens ?? null,
            cache_read_tokens:
              (usage as { cacheReadInputTokens?: number })?.cacheReadInputTokens ?? null,
            cache_write_tokens:
              (usage as { cacheCreationInputTokens?: number })?.cacheCreationInputTokens ?? null,
          }),
          fallback_used: false,
          error_code: finishReason === 'error' ? finishReason : null,
          payload: null,
        })

        // OBS-S1: Observatory per-call telemetry (synthesis stage)
        // Fire-and-forget — must not block the response stream.
        {
          const obsStartedAt = new Date(synthesisStartMs)
          const obsFinishedAt = new Date(synthesisStartMs + synthesisLatencyMs)
          const obsUsage: TokenUsage = {
            input_tokens: usage?.inputTokens ?? 0,
            output_tokens: usage?.outputTokens ?? 0,
            cache_read_tokens: (usage as { cacheReadInputTokens?: number })?.cacheReadInputTokens ?? 0,
            cache_write_tokens: (usage as { cacheCreationInputTokens?: number })?.cacheCreationInputTokens ?? 0,
            reasoning_tokens: isThinkingModel && r1Reasoning ? Math.ceil(r1Reasoning.length / 4) : 0,
          }
          const obsProvider = (resolveProvider(selected_model_id) ?? 'unknown') as ProviderName
          const obsDb = getStorageClient()
          void (async () => {
            const costResult = await computeCost(
              obsProvider,
              selected_model_id,
              obsUsage,
              obsStartedAt,
              obsDb,
            ).catch(() => null)
            await persistObservation(
              {
                provider: obsProvider,
                model: selected_model_id,
                prompt_text: null,
                system_prompt: null,
                parameters: { model: selected_model_id, temperature: synthesisTemperature },
                conversation_id: conversation_id ?? query_plan.query_plan_id,
                conversation_name: null,
                prompt_id: `${query_plan.query_plan_id}:synthesis`,
                user_id: 'native',
                pipeline_stage: 'synthesize',
              },
              {
                response_text: null,
                usage: obsUsage,
                status: finishReason === 'error' ? 'error' : 'success',
                error_code: finishReason === 'error' ? finishReason : undefined,
                started_at: obsStartedAt,
                finished_at: obsFinishedAt,
              },
              costResult,
              obsDb,
            )
          })()
        }

        // ── Hook 3: Checkpoint 8.5 (post-synthesize) ─────────────────────────
        // Runs async in onFinish after stream completes. Halt verdict is logged
        // to telemetry but cannot stop the response already sent to the user;
        // it gates prediction logging and flags the audit event.
        let c8_5Result: Checkpoint85Result | undefined
        if (getFlag('CHECKPOINT_8_5_ENABLED')) {
          try {
            c8_5Result = await runCheckpoint8_5({
              synthesized_text: cleanText,
              query_class: query_plan.query_class,
              validator_results: [],
            })
          } catch {
            // CheckpointHaltError with FAIL_HARD=true — log; response already sent
            telemetry.recordMetric('synthesis', 'checkpoint_8_5_late_halt', 1)
          }
        }

        const auditEvent: SynthesisAuditEvent = {
          event_type: 'synthesis_complete',
          query_plan_id: query_plan.query_plan_id,
          bundle_id: bundle.bundle_id,
          synthesis_prompt_version: template.version,
          synthesizer_model_id: selected_model_id,
          finish_reason: finishReason,
          validator_votes: {},
          started_at: metadata.started_at,
          finished_at: new Date().toISOString(),
          input_tokens: usage?.inputTokens ?? 0,
          output_tokens: usage?.outputTokens ?? 0,
          final_output: cleanText,
          // Phase 6: checkpoint payloads (undefined when flags OFF)
          checkpoints: (c4_5Result || c5_5Result || c8_5Result)
            ? { c4_5: c4_5Result, c5_5: c5_5Result, c8_5: c8_5Result }
            : undefined,
          prediction: c8_5Result?.prediction,
        }

        // BUG-2: compute synthesis-stage validators and notify the caller via
        // onValidatorResults before onAuditEvent fires. The route's
        // validatorResultsHolder (closed over by createAuditConsumer) gets
        // populated here, so validators_run is non-empty in the audit record.
        const synthesisValidations = await runAll(cleanText, 'synthesis', { query_plan })
        request.onValidatorResults?.(synthesisValidations)

        telemetry.recordMetric('synthesis', 'audit_event', 1, {
          event_type: 'synthesis_complete',
        })
        console.log('[synthesis] audit event:', JSON.stringify(auditEvent))

        onAuditEvent?.(auditEvent)
      },
    })

    return { result, metadata, methodologyBlockHolder, usageHolder }
  }
}

export function createOrchestrator(): SynthesisOrchestrator {
  return new SingleModelOrchestrator()
}

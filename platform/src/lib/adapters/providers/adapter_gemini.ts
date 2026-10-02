import 'server-only'
import { meterSharedModel } from '@/lib/metering/context'
import { streamText, stepCountIs, smoothStream, jsonSchema, Output } from 'ai'
import { google } from '@ai-sdk/google'
import type { Adapter, StreamTextOptions } from './base'
import type { ModelMeta } from '@/lib/models/registry'
import type { QueryRequest, ModelInteractionEvent, ModelInteraction } from '../types'

// Documented maximum thinking budgets for thinking_budget (2.5-series) models. A model not
// listed keeps its configured budget as its ceiling rather than an invented number.
const GEMINI_MAX_THINKING_BUDGET: ReadonlyArray<readonly [prefix: string, budget: number]> = [
  ['gemini-2.5-flash-lite', 24576],
  ['gemini-2.5-flash', 24576],
  ['gemini-2.5-pro', 32768],
]

function maxThinkingBudget(modelId: string, configured: number): number {
  const documented = GEMINI_MAX_THINKING_BUDGET.find(([prefix]) => modelId.startsWith(prefix))?.[1]
  return Math.max(configured, documented ?? configured)
}

const SAFETY_BLOCK_NONE = [
  { category: 'HARM_CATEGORY_HATE_SPEECH',       threshold: 'BLOCK_NONE' },
  { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_NONE' },
  { category: 'HARM_CATEGORY_HARASSMENT',        threshold: 'BLOCK_NONE' },
  { category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold: 'BLOCK_NONE' },
  { category: 'HARM_CATEGORY_CIVIC_INTEGRITY',   threshold: 'BLOCK_NONE' },
]

export const adapterGemini: Adapter = {
  providerId: 'google',

  prepareRequest(req: QueryRequest, meta: ModelMeta, injectedModel): StreamTextOptions {
    // Gemini 3.x models declare `thinking_level` (minimal/low/medium/high) in their
    // registry quirks instead of `thinking_budget` (registry.ts's gemini-3.1-pro-preview /
    // gemini-3.7-flash catalog entries). thinkingLevel and thinkingBudget are distinct,
    // non-interchangeable fields on the wire (@ai-sdk/google's own
    // google-generative-ai-options.ts schema) — send whichever the model declares, never
    // both. Gemini 3.x has no documented "disabled" thinking_level; 'low' is used when
    // reasoning=disable is requested — NOT 'minimal': confirmed live against the real API
    // (PARIPRASHNA-P3-PREFLIGHT Part B, dd20_e2e_verify.ts re-run) that
    // gemini-3.1-pro-preview REJECTS thinkingLevel='minimal' outright ("Thinking level
    // MINIMAL is not supported for this model", HTTP 400) — a real, model-specific API
    // constraint no mocked unit test could have caught. 'low' is the lowest level
    // confirmed accepted.
    const requestTransforms = meta.quirks.request_transforms as
      | { thinking_budget?: number; thinking_level?: 'minimal' | 'low' | 'medium' | 'high' }
      | undefined
    // reasoning: 'disable' → lowest accepted; 'enable' → the model's maximum (a deep planning
    // request must be able to raise thinking above a lower configured default — RC-5.1);
    // 'auto' / unset → the registry-configured default.
    const configuredBudget = requestTransforms?.thinking_budget ?? 24576
    const levelModel = requestTransforms?.thinking_level !== undefined || meta.id.startsWith('gemini-3')
    const effortBudget = req.effort === 'low' ? 1024 : req.effort === 'medium' ? 8192
      : maxThinkingBudget(meta.id, configuredBudget)
    // A BYOK model with no explicit effort/reasoning keeps its provider default.
    // In particular, Gemini 3 does not accept a Gemini 2.5 thinkingBudget field.
    const thinkingConfig: Record<string, unknown> | undefined = injectedModel
      && !req.effort && (!req.reasoning || req.reasoning === 'auto') ? undefined
      : levelModel
        ? {
            thinkingLevel: req.effort ?? (req.reasoning === 'disable' ? 'low'
              : req.reasoning === 'enable' ? 'high'
                : requestTransforms?.thinking_level ?? 'high'),
          }
        : {
            thinkingBudget: req.effort ? effortBudget : req.reasoning === 'disable' ? 0
              : req.reasoning === 'enable' ? maxThinkingBudget(meta.id, configuredBudget)
                : configuredBudget,
          }

    const googleOptions: Record<string, unknown> = {
      safetySettings: SAFETY_BLOCK_NONE,
      ...(thinkingConfig ? { thinkingConfig } : {}),
    }

    // Structured output MUST go through `output` (Output.object), not a top-level
    // `responseFormat` field. In the pinned `ai` SDK (v6), streamText() has no
    // `responseFormat` parameter at all — an unrecognized key silently falls into an
    // untyped settings bag and never reaches the provider's generationConfig. The
    // provider-level `responseFormat` the google provider actually reads comes from
    // `output?.responseFormat` internally. This was DD-20's real, still-live wiring gap —
    // DD-20's parseAndValidateSets + repair-retry fixed the symptom (silently accepting
    // schema-noncompliant text), not this. Confirmed against the real outbound HTTP body
    // in adapter_gemini_wire_body.test.ts, not inferred from SDK docs.
    const output = req.responseSchema ? Output.object({ schema: jsonSchema(req.responseSchema) }) : undefined

    const tools =
      req.tools?.length
        ? Object.fromEntries(
            req.tools.map(t => [
              t.name,
              { description: t.description, inputSchema: jsonSchema(t.parameters as Record<string, unknown>) },
            ]),
          )
        : undefined

    if (req.toolChoice !== undefined && meta.quirks.tool_use_format === 'none') {
      throw new Error(`adapterGemini: toolChoice not supported by model ${meta.id} (tool_use_format=none)`)
    }

    return {
      model: injectedModel ?? meterSharedModel(google(meta.id), meta.provider, meta.id, req.callType, req),
      system: req.systemPrompt,
      messages: req.messages,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      providerOptions: { google: googleOptions } as any,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ...(output && { output: output as any }),
      maxOutputTokens: req.maxOutputTokens ?? meta.maxOutputTokens,
      temperature: req.temperature,
      tools,
      toolChoice: req.toolChoice as unknown,
      stopWhen: req.multiStep ? stepCountIs(req.multiStep.maxSteps) : undefined,
      experimental_transform: req.smoothStream ? smoothStream() : undefined,
      onStepFinish: req.onStepFinish as ((step: unknown) => Promise<void> | void) | undefined,
      onFinish: req.rawOnFinish as ((result: unknown) => Promise<void> | void) | undefined,
      ...(req.disableSdkRetry && { maxRetries: 0 }),
      ...(req.abortSignal && { abortSignal: req.abortSignal }),
    }
  },

  stream(req: QueryRequest, meta: ModelMeta): ReadableStream<ModelInteractionEvent> {
    return new ReadableStream({
      async start(controller) {
        const ts = () => Date.now()
        const startTime = Date.now()
        let inputTokens = 0
        let outputTokens = 0
        let cacheReadTokens: number | undefined
        let cacheWriteTokens: number | undefined
        let finishReason: ModelInteraction['finishReason'] = 'stop'

        controller.enqueue({ type: 'status', ts: ts(), status: 'queued' })

        try {
          const options = adapterGemini.prepareRequest(req, meta)
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const result = streamText(options as any)

          let reasoningStarted = false
          let composing = false

          for await (const part of result.fullStream) {
            if (req.abortSignal?.aborted) break
            if (part.type === 'text-delta') {
              if (!composing) {
                controller.enqueue({ type: 'status', ts: ts(), status: 'composing' })
                composing = true
              }
              controller.enqueue({ type: 'text_delta', ts: ts(), text: part.text })
            } else if (part.type === 'reasoning-delta') {
              if (meta.quirks.reasoning_via !== 'none') {
                if (!reasoningStarted) {
                  controller.enqueue({ type: 'status', ts: ts(), status: 'reasoning' })
                  reasoningStarted = true
                }
                controller.enqueue({ type: 'reasoning_delta', ts: ts(), text: part.text })
              }
            } else if (part.type === 'tool-call') {
              controller.enqueue({
                type: 'tool_call',
                ts: ts(),
                name: part.toolName,
                args: part.input,
                callId: part.toolCallId,
              })
            } else if (part.type === 'tool-result') {
              controller.enqueue({
                type: 'tool_result',
                ts: ts(),
                callId: part.toolCallId,
                result: (part as unknown as { output: unknown }).output,
              })
            } else if (part.type === 'finish') {
              finishReason = mapFinishReason(part.finishReason)
              inputTokens = part.totalUsage.inputTokens ?? 0
              outputTokens = part.totalUsage.outputTokens ?? 0
              cacheReadTokens =
                (part.totalUsage as unknown as { inputTokenDetails?: { cacheReadTokens?: number } })
                  .inputTokenDetails?.cacheReadTokens ?? undefined
              cacheWriteTokens =
                (part.totalUsage as unknown as { inputTokenDetails?: { cacheWriteTokens?: number } })
                  .inputTokenDetails?.cacheWriteTokens ?? undefined
            } else if (part.type === 'error') {
              throw part.error instanceof Error ? part.error : new Error(String(part.error))
            }
          }

          controller.enqueue({ type: 'status', ts: ts(), status: 'complete' })
          const interaction: ModelInteraction = {
            modelId: meta.id,
            provider: meta.provider,
            intermediate: [],
            finishReason,
            usage: {
              inputTokens,
              outputTokens,
              cacheReadTokens,
              cacheWriteTokens,
              costUsd: computeCost(meta, inputTokens, outputTokens),
              latencyMs: ts() - startTime,
            },
            providerMeta: {},
          }
          controller.enqueue({ type: 'finish', ts: ts(), interaction })

          if (req.onFinish) {
            await req.onFinish(interaction)
          }
        } catch (err) {
          controller.enqueue({
            type: 'error',
            ts: ts(),
            error: { message: err instanceof Error ? err.message : String(err) },
          })
        }
        controller.close()
      },
    })
  },
}

function computeCost(meta: ModelMeta, inp: number, out: number): number {
  return (inp / 1_000_000) * meta.costPer1MInput + (out / 1_000_000) * meta.costPer1MOutput
}

function mapFinishReason(reason: string): ModelInteraction['finishReason'] {
  if (reason === 'length') return 'length'
  if (reason === 'tool-calls') return 'tool_calls'
  if (reason === 'content-filter') return 'content_filter'
  if (reason === 'error') return 'error'
  return 'stop'
}

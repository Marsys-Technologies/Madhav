import 'server-only'
import { streamText, stepCountIs, smoothStream, jsonSchema, Output } from 'ai'
import { google } from '@ai-sdk/google'
import type { Adapter, StreamTextOptions } from './base'
import type { ModelMeta } from '@/lib/models/registry'
import type { QueryRequest, ModelInteractionEvent, ModelInteraction } from '../types'

const SAFETY_BLOCK_NONE = [
  { category: 'HARM_CATEGORY_HATE_SPEECH',       threshold: 'BLOCK_NONE' },
  { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_NONE' },
  { category: 'HARM_CATEGORY_HARASSMENT',        threshold: 'BLOCK_NONE' },
  { category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold: 'BLOCK_NONE' },
  { category: 'HARM_CATEGORY_CIVIC_INTEGRITY',   threshold: 'BLOCK_NONE' },
]

export const adapterGemini: Adapter = {
  providerId: 'google',

  prepareRequest(req: QueryRequest, meta: ModelMeta): StreamTextOptions {
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
    const thinkingConfig: Record<string, unknown> =
      requestTransforms?.thinking_level !== undefined
        ? { thinkingLevel: req.reasoning === 'disable' ? 'low' : requestTransforms.thinking_level }
        : { thinkingBudget: req.reasoning === 'disable' ? 0 : requestTransforms?.thinking_budget ?? 24576 }

    const googleOptions: Record<string, unknown> = {
      safetySettings: SAFETY_BLOCK_NONE,
      thinkingConfig,
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
      model: google(meta.id),
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

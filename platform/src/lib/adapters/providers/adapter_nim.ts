import 'server-only'
import { streamText, stepCountIs, smoothStream, jsonSchema } from 'ai'
import { createOpenAI } from '@ai-sdk/openai'
import type { Adapter, StreamTextOptions } from './base'
import type { ModelMeta } from '@/lib/models/registry'
import type { QueryRequest, ModelInteractionEvent, ModelInteraction } from '../types'
import { MarkerBuffer } from '../buffer'
import { isNimCompatibilityError, PlannerCompatibilityError } from '@/lib/models/nvidia'

const NVIDIA_NIM_BASE_URL = 'https://integrate.api.nvidia.com/v1'

function getNimModel(modelId: string) {
  const client = createOpenAI({
    baseURL: NVIDIA_NIM_BASE_URL,
    apiKey: process.env.NVIDIA_NIM_API_KEY ?? '',
  })
  return client.chat(modelId)
}

export const adapterNim: Adapter = {
  providerId: 'nvidia',

  prepareRequest(req: QueryRequest, meta: ModelMeta): StreamTextOptions {
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
      throw new Error(`adapterNim: toolChoice not supported by model ${meta.id} (tool_use_format=none)`)
    }

    return {
      model: getNimModel(meta.id),
      system: req.systemPrompt,
      messages: req.messages,
      maxOutputTokens: req.maxOutputTokens ?? meta.maxOutputTokens,
      temperature: req.temperature,
      tools,
      toolChoice: req.toolChoice as unknown,
      stopWhen: req.multiStep ? stepCountIs(req.multiStep.maxSteps) : undefined,
      experimental_transform: req.smoothStream ? smoothStream() : undefined,
      onStepFinish: req.onStepFinish as ((step: unknown) => Promise<void> | void) | undefined,
      onFinish: req.rawOnFinish as ((result: unknown) => Promise<void> | void) | undefined,
      // NIM: always maxRetries:0 — nimFetch enforces its own 30 s abort; SDK retries triple the hang.
      maxRetries: 0,
    }
  },

  stream(req: QueryRequest, meta: ModelMeta): ReadableStream<ModelInteractionEvent> {
    return new ReadableStream({
      async start(controller) {
        const ts = () => Date.now()
        const startTime = Date.now()
        let inputTokens = 0
        let outputTokens = 0
        let finishReason: ModelInteraction['finishReason'] = 'stop'

        controller.enqueue({ type: 'status', ts: ts(), status: 'queued' })

        // For NIM models with marker-based reasoning (DeepSeek-on-NIM), use MarkerBuffer
        const usesMarkers = meta.quirks.reasoning_via === 'markers'
        const buffer = usesMarkers ? new MarkerBuffer('<think>', '</think>') : null

        try {
          const options = adapterNim.prepareRequest(req, meta)
          // NIM requires streaming — streamText always uses streaming mode
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const result = streamText(options as any)

          let reasoningStarted = false
          let composing = false
          let reasoning_unclosed = false

          for await (const part of result.fullStream) {
            if (part.type === 'text-delta') {
              if (buffer) {
                const out = buffer.feed(part.text)
                if (out.reasoning) {
                  if (!reasoningStarted) {
                    controller.enqueue({ type: 'status', ts: ts(), status: 'reasoning' })
                    reasoningStarted = true
                  }
                  controller.enqueue({ type: 'reasoning_delta', ts: ts(), text: out.reasoning })
                }
                if (out.text) {
                  if (!composing) {
                    controller.enqueue({ type: 'status', ts: ts(), status: 'composing' })
                    composing = true
                  }
                  controller.enqueue({ type: 'text_delta', ts: ts(), text: out.text })
                }
              } else {
                if (!composing) {
                  controller.enqueue({ type: 'status', ts: ts(), status: 'composing' })
                  composing = true
                }
                controller.enqueue({ type: 'text_delta', ts: ts(), text: part.text })
              }
            } else if (part.type === 'reasoning-delta') {
              if (!reasoningStarted) {
                controller.enqueue({ type: 'status', ts: ts(), status: 'reasoning' })
                reasoningStarted = true
              }
              controller.enqueue({ type: 'reasoning_delta', ts: ts(), text: part.text })
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
            } else if (part.type === 'error') {
              throw part.error instanceof Error ? part.error : new Error(String(part.error))
            }
          }

          if (buffer) {
            const flushed = buffer.flush()
            if (flushed.reasoning) {
              controller.enqueue({ type: 'reasoning_delta', ts: ts(), text: flushed.reasoning })
              reasoning_unclosed = flushed.unclosed ?? false
            }
            if (flushed.text) {
              if (!composing) {
                controller.enqueue({ type: 'status', ts: ts(), status: 'composing' })
                composing = true
              }
              controller.enqueue({ type: 'text_delta', ts: ts(), text: flushed.text })
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
              costUsd: computeCost(meta, inputTokens, outputTokens),
              latencyMs: ts() - startTime,
            },
            providerMeta: {
              raw: reasoning_unclosed ? { reasoning_unclosed: true } : undefined,
            },
          }
          controller.enqueue({ type: 'finish', ts: ts(), interaction })

          if (req.onFinish) {
            await req.onFinish(interaction)
          }
        } catch (err) {
          // Classify NIM compatibility errors (deterministic rejections of toolChoice / response_format)
          const classified = isNimCompatibilityError(err)
            ? new PlannerCompatibilityError(
                `NIM model ${meta.id} rejected request: ${err instanceof Error ? err.message : String(err)}`,
                err,
              )
            : err
          controller.enqueue({
            type: 'error',
            ts: ts(),
            error: {
              message: classified instanceof Error ? classified.message : String(classified),
              code: classified instanceof PlannerCompatibilityError ? 'NIM_COMPAT_ERROR' : undefined,
            },
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

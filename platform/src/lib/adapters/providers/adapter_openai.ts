import 'server-only'
import { streamText } from 'ai'
import { openai } from '@ai-sdk/openai'
import type { Adapter } from './base'
import type { ModelMeta } from '@/lib/models/registry'
import type { QueryRequest, ModelInteractionEvent, ModelInteraction } from '../types'

export const adapterOpenai: Adapter = {
  providerId: 'openai',

  stream(req: QueryRequest, meta: ModelMeta): ReadableStream<ModelInteractionEvent> {
    return new ReadableStream({
      async start(controller) {
        const ts = () => Date.now()
        const startTime = Date.now()
        let inputTokens = 0
        let outputTokens = 0
        let cacheReadTokens: number | undefined
        let finishReason: ModelInteraction['finishReason'] = 'stop'

        controller.enqueue({ type: 'status', ts: ts(), status: 'queued' })

        // Structured output via json_schema when responseSchema is present
        const providerOptions =
          req.responseSchema && meta.quirks.structured_output_format === 'json_schema'
            ? {
                openai: {
                  response_format: {
                    type: 'json_schema' as const,
                    json_schema: { name: 'response', schema: req.responseSchema, strict: true },
                  },
                },
              }
            : undefined

        // TODO: Future o-series models may have reasoning_via: 'native' — extend here when added to registry.

        try {
          const result = streamText({
            model: openai(meta.id),
            system: req.systemPrompt,
            messages: req.messages,
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            providerOptions: providerOptions as any,
            maxOutputTokens: req.maxOutputTokens ?? meta.maxOutputTokens,
            temperature: req.temperature,
          })

          let composing = false

          for await (const part of result.fullStream) {
            if (part.type === 'text-delta') {
              if (!composing) {
                controller.enqueue({ type: 'status', ts: ts(), status: 'composing' })
                composing = true
              }
              controller.enqueue({ type: 'text_delta', ts: ts(), text: part.text })
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
            } else if (part.type === 'error') {
              throw part.error instanceof Error ? part.error : new Error(String(part.error))
            }
          }

          controller.enqueue({ type: 'status', ts: ts(), status: 'complete' })
          controller.enqueue({
            type: 'finish',
            ts: ts(),
            interaction: {
              modelId: meta.id,
              provider: meta.provider,
              intermediate: [],
              finishReason,
              usage: {
                inputTokens,
                outputTokens,
                cacheReadTokens,
                costUsd: computeCost(meta, inputTokens, outputTokens),
                latencyMs: ts() - startTime,
              },
              providerMeta: {},
            },
          })
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

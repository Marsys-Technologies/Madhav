import 'server-only'
import { streamText, stepCountIs, smoothStream, jsonSchema } from 'ai'
import { deepseek } from '@ai-sdk/deepseek'
import type { Adapter, StreamTextOptions } from './base'
import type { ModelMeta } from '@/lib/models/registry'
import type { QueryRequest, ModelInteractionEvent, ModelInteraction } from '../types'
import { MarkerBuffer } from '../buffer'

export const adapterDeepseek: Adapter = {
  providerId: 'deepseek',

  prepareRequest(req: QueryRequest, meta: ModelMeta): StreamTextOptions {
    const wantsThinking =
      req.reasoning !== 'disable' &&
      meta.quirks.request_transforms?.thinking_mode === 'toggle'

    const providerOptions = wantsThinking
      ? { deepseek: { thinking: { type: 'enabled' as const } } }
      : undefined

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
      throw new Error(`adapterDeepseek: toolChoice not supported by model ${meta.id} (tool_use_format=none)`)
    }

    return {
      model: deepseek(meta.id),
      system: req.systemPrompt,
      messages: req.messages,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      providerOptions: providerOptions as any,
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
        let reasoningTokens = 0
        let cacheReadTokens: number | undefined
        let cacheWriteTokens: number | undefined
        let finishReason: ModelInteraction['finishReason'] = 'stop'
        const buffer = new MarkerBuffer('<think>', '</think>')

        controller.enqueue({ type: 'status', ts: ts(), status: 'queued' })

        try {
          const options = adapterDeepseek.prepareRequest(req, meta)
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const result = streamText(options as any)

          let reasoningStarted = false
          let composing = false
          let reasoning_unclosed = false

          for await (const part of result.fullStream) {
            if (req.abortSignal?.aborted) break
            if (part.type === 'text-delta') {
              const out = buffer.feed(part.text)
              if (out.reasoning && meta.quirks.reasoning_via !== 'none') {
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
              reasoningTokens =
                (part.totalUsage as unknown as { outputTokenDetails?: { reasoningTokens?: number } })
                  .outputTokenDetails?.reasoningTokens ?? 0
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

          const flushed = buffer.flush()
          if (flushed.reasoning && meta.quirks.reasoning_via !== 'none') {
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

          controller.enqueue({ type: 'status', ts: ts(), status: 'complete' })
          const interaction: ModelInteraction = {
            modelId: meta.id,
            provider: meta.provider,
            intermediate: [],
            finishReason,
            usage: {
              inputTokens,
              outputTokens,
              reasoningTokens: reasoningTokens || undefined,
              cacheReadTokens,
              cacheWriteTokens,
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

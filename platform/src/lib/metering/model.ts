import 'server-only'
import type { LanguageModelV3, LanguageModelV3StreamPart } from '@ai-sdk/provider'
import type { MeteringContext, AttemptReceipt, AttemptStatus, UsageEvidence } from './types'
import { normalizeSdkUsage } from './usage'
import { startAttempt, finishAttempt, type MeteringDependencies } from './service'

function safeId(value: unknown): string | null {
  return typeof value === 'string' && /^[\w.:/-]{1,256}$/.test(value) ? value : null
}
function providerCost(value: unknown): string | null {
  const usage = value && typeof value === 'object' ? value as { raw?: { cost?: unknown } } : null
  const raw = usage?.raw?.cost
  const decimal = typeof raw === 'number' && Number.isFinite(raw) && raw >= 0 && raw < 1e18 ? raw.toFixed(12) : raw
  return typeof decimal === 'string' && /^\d+(\.\d{1,12})?$/.test(decimal) && decimal.length < 30 ? decimal : null
}
const failureStatus = (signal?: AbortSignal): AttemptStatus => !signal?.aborted ? 'error'
  : signal.reason instanceof Error && signal.reason.name === 'TimeoutError' ? 'timeout' : 'cancelled'

/** Wrap the transport, not SDK aggregate finish: every retry and tool-loop step gets its own attempt. */
export function meterModel(model: LanguageModelV3, context: MeteringContext,
  dependencies: MeteringDependencies = {}): LanguageModelV3 {
  return {
    specificationVersion: model.specificationVersion,
    provider: model.provider,
    modelId: model.modelId,
    get supportedUrls() { return model.supportedUrls },
    async doGenerate(options) {
      const start = await startAttempt(context,dependencies)
      let result: Awaited<ReturnType<LanguageModelV3['doGenerate']>>
      try { result = await model.doGenerate(options) }
      catch (error) {
        await finishAttempt(start,{ attemptId:start.attemptId,finishedAt:new Date().toISOString(),
          status:failureStatus(options.abortSignal),usage:normalizeSdkUsage(undefined),providerRequestId:null,
          finishReason:null,firstTokenAt:null,providerCostUsd:null },dependencies)
        throw error
      }
      await finishAttempt(start,{ attemptId:start.attemptId,finishedAt:new Date().toISOString(),status:result.finishReason.unified === 'error' ? 'error' : 'success',
        usage:normalizeSdkUsage(result.usage),providerRequestId:safeId(result.response?.id),
        finishReason:safeId(result.finishReason.unified),firstTokenAt:null,providerCostUsd:providerCost(result.usage) },dependencies)
      return result
    },
    async doStream(options) {
      const start = await startAttempt(context,dependencies)
      let firstTokenAt: string | null = null, requestId: string | null = null, reason: string | null = null
      let usage: UsageEvidence = normalizeSdkUsage(undefined), cost: string | null = null
      let terminal: Promise<void> | undefined, sawError = false
      const finish = (status: AttemptStatus) => {
        terminal ??= finishAttempt(start,{ attemptId:start.attemptId,finishedAt:new Date().toISOString(),status,
          usage,providerRequestId:requestId,finishReason:reason,firstTokenAt,providerCostUsd:cost } satisfies AttemptReceipt,dependencies)
        return terminal
      }
      let result: Awaited<ReturnType<LanguageModelV3['doStream']>>
      try { result = await model.doStream(options) }
      catch (error) { await finish(failureStatus(options.abortSignal)); throw error }
      const reader = result.stream.getReader()
      const stream = new ReadableStream<LanguageModelV3StreamPart>({
        async pull(controller) {
          try {
            const next = await reader.read()
            if (next.done) { await finish(options.abortSignal?.aborted ? failureStatus(options.abortSignal) : sawError ? 'error' : 'incomplete'); controller.close(); return }
            const part = next.value
            if (part.type === 'response-metadata') requestId = safeId(part.id)
            if (part.type === 'text-delta' && firstTokenAt === null) firstTokenAt = new Date().toISOString()
            if (part.type === 'error') sawError = true
            if (part.type === 'finish') {
              usage = normalizeSdkUsage(part.usage); cost = providerCost(part.usage)
              reason = safeId(part.finishReason.unified)
              await finish(sawError || part.finishReason.unified === 'error' ? 'error' : 'success')
            }
            controller.enqueue(part)
          } catch (error) {
            try { await finish(failureStatus(options.abortSignal)) }
            finally { controller.error(error) }
          }
        },
        async cancel(reason) { try { await reader.cancel(reason) } finally { await finish('cancelled') } },
      })
      return { ...result,stream }
    },
  }
}

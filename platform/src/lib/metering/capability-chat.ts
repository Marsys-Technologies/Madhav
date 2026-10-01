import 'server-only'
import type { ChatEvent } from '@/lib/providers/types'
import type { MeteringContext, UsageEvidence, AttemptStatus } from './types'
import { normalizeSdkUsage } from './usage'
import { startAttempt, finishAttempt, type MeteringDependencies } from './service'

/** One ledger leaf for an OpenAI-compatible capability-adapter stream. */
export async function* meterCapabilityChat(
  stream: AsyncIterable<ChatEvent>, context: MeteringContext, dependencies: MeteringDependencies = {},
): AsyncIterable<ChatEvent> {
  const start = await startAttempt(context, dependencies)
  let usage: UsageEvidence = normalizeSdkUsage(undefined)
  let firstTokenAt: string | null = null
  let finishReason: string | null = null
  let sawError = false
  let sawStop = false
  let completed = false
  try {
    for await (const event of stream) {
      if ((event.type === 'text_delta' || event.type === 'thinking_delta') && firstTokenAt === null) {
        firstTokenAt = new Date().toISOString()
      }
      if (event.type === 'usage') {
        usage = normalizeSdkUsage({
          inputTokens: { total: event.inputTokens, ...(event.cacheReadTokens != null ? { cacheRead: event.cacheReadTokens } : {}),
            ...(event.cacheCreationTokens != null ? { cacheWrite: event.cacheCreationTokens } : {}) },
          outputTokens: { total: event.outputTokens },
        })
      }
      if (event.type === 'message_stop') { sawStop = true; finishReason = /^[\w.:/-]{1,256}$/.test(event.stopReason) ? event.stopReason : null }
      if (event.type === 'error') sawError = true
      yield event
    }
    completed = true
  } catch (error) {
    sawError = true
    throw error
  } finally {
    const status: AttemptStatus = sawError ? 'error' : !completed ? 'cancelled' : sawStop ? 'success' : 'incomplete'
    await finishAttempt(start, { attemptId: start.attemptId, finishedAt: new Date().toISOString(), status,
      usage, providerRequestId: null, finishReason, firstTokenAt, providerCostUsd: null }, dependencies)
  }
}

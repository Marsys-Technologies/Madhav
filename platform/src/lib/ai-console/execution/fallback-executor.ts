import 'server-only'

import { AiConsoleError } from '../errors'
import type { AiErrorCode } from '../errors'
import { isStructuredOutputValidationError } from './structured-output-error'
import type { RoleExecutionEvent, RoleExecutionRequest, RoleExecutor } from './provider-executor'

const FALLBACK_ELIGIBLE = new Set<AiErrorCode>([
  'AI_CONNECTION_INVALID',
  'AI_MODEL_UNAVAILABLE',
  'AI_CLI_UNREACHABLE',
  'AI_PROVIDER_UNREACHABLE',
  'AI_BILLING_UNAVAILABLE',
  'AI_RATE_LIMITED',
  'AI_CLI_NOT_INSTALLED',
  'AI_CLI_AUTH_UNAVAILABLE',
  'AI_CLI_TIMEOUT',
  'AI_EXECUTION_FAILED',
])

function eligible(error: unknown, request: RoleExecutionRequest): boolean {
  if (request.abortSignal?.aborted) return false
  if (isStructuredOutputValidationError(error)) return true
  return error instanceof AiConsoleError && FALLBACK_ELIGIBLE.has(error.code)
}

function sameTarget(left: RoleExecutor, right: RoleExecutor): boolean {
  const a = left.descriptor
  const b = right.descriptor
  if (a.role !== b.role || a.modelId !== b.modelId) return false
  if ('providerId' in a && 'providerId' in b) {
    return a.providerId === b.providerId && a.connectionId === b.connectionId
  }
  return 'cliId' in a && 'cliId' in b && a.cliId === b.cliId
}

/**
 * One visible, bounded fallback: the explicitly selected role first, then the
 * user's snapshotted Default role. Streaming only switches before any selected
 * output is exposed, so two models can never be mixed into one answer.
 */
export function createDefaultFallbackExecutor(selected: RoleExecutor, fallback: RoleExecutor): RoleExecutor {
  if (selected.descriptor.role !== fallback.descriptor.role) {
    throw new AiConsoleError('AI_EXECUTION_FAILED', selected.descriptor.role)
  }
  if (sameTarget(selected, fallback)) return selected
  let fallbackActive = false

  const runFallback = async (request: RoleExecutionRequest) => {
    const result = await fallback.generate(request)
    return { ...result, fallbackUsed: true }
  }

  return Object.freeze({
    descriptor: selected.descriptor,
    async generate(request: RoleExecutionRequest) {
      if (fallbackActive) return runFallback(request)
      try { return await selected.generate(request) }
      catch (error) {
        if (!eligible(error, request)) throw error
        fallbackActive = true
        return runFallback(request)
      }
    },
    stream(request: RoleExecutionRequest): ReadableStream<RoleExecutionEvent> {
      let usingFallback = fallbackActive
      let reader = (usingFallback ? fallback : selected).stream(request).getReader()
      let exposedSelectedOutput = false
      let pulling: Promise<void> | undefined

      return new ReadableStream<RoleExecutionEvent>({
        pull(controller) {
          pulling ??= (async () => {
            while (true) {
              let next: ReadableStreamReadResult<RoleExecutionEvent>
              try { next = await reader.read() }
              catch (error) {
                if (usingFallback || exposedSelectedOutput || !eligible(error, request)) {
                  controller.error(error)
                  return
                }
                usingFallback = true
                fallbackActive = true
                reader.releaseLock()
                reader = fallback.stream(request).getReader()
                continue
              }
              if (next.done) {
                controller.close()
                return
              }
              const event = usingFallback && next.value.type === 'finish'
                ? { ...next.value, fallbackUsed: true }
                : next.value
              if (!usingFallback) exposedSelectedOutput = true
              controller.enqueue(event)
              return
            }
          })().finally(() => { pulling = undefined })
          return pulling
        },
        async cancel() { await reader.cancel() },
      })
    },
  })
}

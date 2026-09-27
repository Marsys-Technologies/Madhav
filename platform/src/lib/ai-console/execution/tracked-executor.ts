import 'server-only'

import { AiConsoleError, normalizeAiError } from '../errors'
import { insertRoleInvocationReceipt } from '../repository'
import type {
  RoleExecutionEvent,
  RoleExecutionRequest,
  RoleExecutionResult,
  RoleExecutor,
} from './provider-executor'
import { isStructuredOutputValidationError } from './structured-output-error'

export interface InvocationReceiptContext {
  readonly userId: string
  readonly snapshotId: string
}

function source(executor: RoleExecutor): 'provider' | 'cli' {
  return 'providerId' in executor.descriptor ? 'provider' : 'cli'
}

function publicFailure(executor: RoleExecutor, cause: unknown): AiConsoleError {
  const normalized = normalizeAiError(cause, { source: source(executor), role: executor.descriptor.role })
  return new AiConsoleError(normalized.code, executor.descriptor.role)
}

async function startReceipt(executor: RoleExecutor, context: InvocationReceiptContext, invocationId: string) {
  await insertRoleInvocationReceipt({
    userId: context.userId,
    snapshotId: context.snapshotId,
    invocationId,
    role: executor.descriptor.role,
    phase: 'start',
    status: 'started',
  })
}

async function terminalReceipt(
  executor: RoleExecutor,
  context: InvocationReceiptContext,
  invocationId: string,
  status: 'succeeded' | 'failed' | 'cancelled',
  errorCode?: AiConsoleError['code'],
) {
  await insertRoleInvocationReceipt({
    userId: context.userId,
    snapshotId: context.snapshotId,
    invocationId,
    role: executor.descriptor.role,
    phase: 'terminal',
    status,
    ...(errorCode ? { errorCode } : {}),
  })
}

/**
 * Add durable per-invocation evidence without retaining any request or result.
 * The delegate is never entered until the start receipt commits.
 */
export function trackRoleExecutor(executor: RoleExecutor, context: InvocationReceiptContext): RoleExecutor {
  return Object.freeze({
    descriptor: executor.descriptor,
    async generate(request: RoleExecutionRequest): Promise<RoleExecutionResult> {
      const invocationId = crypto.randomUUID()
      await startReceipt(executor, context, invocationId)
      let result: RoleExecutionResult
      try {
        result = await executor.generate(request)
      } catch (cause) {
        const failure = publicFailure(executor, cause)
        await terminalReceipt(executor, context, invocationId,
          request.abortSignal?.aborted ? 'cancelled' : 'failed', failure.code)
        if (isStructuredOutputValidationError(cause)) throw cause
        throw failure
      }
      // A receipt-commit failure is not an executor failure and must never be
      // rewritten as a second, contradictory terminal row for this invocation.
      await terminalReceipt(executor, context, invocationId, 'succeeded')
      return result
    },
    stream(request: RoleExecutionRequest): ReadableStream<RoleExecutionEvent> {
      const invocationId = crypto.randomUUID()
      let reader: ReadableStreamDefaultReader<RoleExecutionEvent> | undefined
      let started = false
      let cancelRequested = false
      let pulling: Promise<void> | undefined
      let beginning: Promise<boolean> | undefined
      let terminalCommit: Promise<void> | undefined

      const finish = async (status: 'succeeded' | 'failed' | 'cancelled', errorCode?: AiConsoleError['code']) => {
        if (terminalCommit) return terminalCommit
        if (!started) return
        terminalCommit = terminalReceipt(executor, context, invocationId, status, errorCode)
        await terminalCommit
      }

      const begin = async () => {
        if (started) return !cancelRequested
        beginning ??= (async () => {
          await startReceipt(executor, context, invocationId)
          started = true
          if (cancelRequested) {
            await finish('cancelled', 'AI_EXECUTION_FAILED')
            return false
          }
          reader = executor.stream(request).getReader()
          return true
        })()
        return beginning
      }

      return new ReadableStream<RoleExecutionEvent>({
        async pull(controller) {
          pulling ??= (async () => {
            try {
              if (!await begin()) return
              const next = await reader!.read()
              if (cancelRequested) {
                await finish('cancelled', 'AI_EXECUTION_FAILED')
                return
              }
              if (next.done) {
                await finish('succeeded')
                controller.close()
                return
              }
              controller.enqueue(next.value)
            } catch (cause) {
              const failure = publicFailure(executor, cause)
              try {
                await finish(request.abortSignal?.aborted ? 'cancelled' : 'failed', failure.code)
              } catch (receiptError) {
                controller.error(receiptError)
                return
              }
              controller.error(failure)
            }
          })().finally(() => { pulling = undefined })
          return pulling
        },
        async cancel() {
          cancelRequested = true
          try {
            await reader?.cancel()
            await beginning
          } finally {
            await finish('cancelled', 'AI_EXECUTION_FAILED')
          }
        },
      })
    },
  })
}

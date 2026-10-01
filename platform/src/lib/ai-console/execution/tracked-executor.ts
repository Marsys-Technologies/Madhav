import 'server-only'
import { meteringEnabled, type AttemptStart, type MeteringContext, type MeteringPurpose } from '@/lib/metering/types'
import { startAttempt, finishAttempt } from '@/lib/metering/service'
import { normalizeSdkUsage } from '@/lib/metering/usage'

import { AiConsoleError, normalizeAiError } from '../errors'
import { insertRoleInvocationReceipt } from '../repository'
import type {
  RoleExecutionEvent,
  RoleExecutionRequest,
  RoleExecutionResult,
  NormalizedUsage,
  RoleExecutor,
} from './provider-executor'
import { isStructuredOutputValidationError } from './structured-output-error'
import { safeExecutionFailureFacts, safeExecutionStreamFacts } from './execution-facts'
import { observeRoleInvocation, type RoleObservationContext } from '../observability'

export interface InvocationReceiptContext {
  readonly userId: string
  readonly snapshotId: string
  readonly purpose?: MeteringPurpose
  readonly testRunId?: string
  readonly observation?: Omit<RoleObservationContext, 'snapshotId'>
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
  const observe = async (input: Parameters<typeof observeRoleInvocation>[2]) => {
    if (!context.observation) return
    try {
      await observeRoleInvocation(executor.descriptor, {
        snapshotId: context.snapshotId,
        ...context.observation,
      }, input)
    } catch {
      console.warn('[ai-console] Observatory terminal observation failed')
    }
  }
  const scheduleObservation = (input: Parameters<typeof observeRoleInvocation>[2]) => {
    // observe() owns its rejection path. Deliberately do not await telemetry:
    // the durable terminal receipt is the request-path boundary.
    void observe(input)
  }
  const attribution = (invocationId: string): MeteringContext | undefined => {
    if (!meteringEnabled()) return undefined
    const snapshot = context.observation?.snapshot
    const provider = 'providerId' in executor.descriptor
    return { userId: context.userId, conversationId: snapshot?.conversationId ?? null,
      turnId: context.observation?.fallback?.fromCorrelationId ?? snapshot?.correlationId ?? context.testRunId ?? invocationId, operationId: invocationId,
      parentOperationId: null,
      channel: snapshot?.source === 'mcp' ? 'mcp' : snapshot?.source === 'pariprashna' ? 'web' : 'backend',
      purpose: context.purpose ?? 'customer', payer: provider ? 'user' : 'subscription',
      provider: provider ? executor.descriptor.providerId : 'cli',
      model: executor.descriptor.modelId ?? 'builtin-default', role: executor.descriptor.role,
      connectionId: provider ? executor.descriptor.connectionId : null,
      snapshotId: context.snapshotId, testRunId: context.testRunId ?? null,
      aggregation: provider ? 'transport' : 'cli_aggregate' }
  }
  const settleCli = async (start: AttemptStart | undefined, status: 'success' | 'error' | 'timeout' | 'cancelled', usage: NormalizedUsage | null) => {
    if (!start) return
    await finishAttempt(start, { attemptId: start.attemptId, finishedAt: new Date().toISOString(), status,
      usage: normalizeSdkUsage(usage, 'client_reported'), providerRequestId: null, finishReason: null,
      firstTokenAt: null, providerCostUsd: null })
  }
  return Object.freeze({
    descriptor: executor.descriptor,
    async generate(request: RoleExecutionRequest): Promise<RoleExecutionResult> {
      const invocationId = crypto.randomUUID()
      await startReceipt(executor, context, invocationId)
      const startedAt = new Date()
      const meteringContext = attribution(invocationId)
      const cliStart = meteringContext?.aggregation === 'cli_aggregate' ? await startAttempt(meteringContext) : undefined
      let result: RoleExecutionResult
      try {
        result = await executor.generate({ ...request, meteringContext })
      } catch (cause) {
        const retryCount = safeExecutionFailureFacts(cause)?.retryCount ?? null
        const failure = publicFailure(executor, cause)
        const cancelled = request.abortSignal?.aborted === true
        if (cliStart) await settleCli(cliStart, cancelled ? 'cancelled' : failure.code === 'AI_CLI_TIMEOUT' ? 'timeout' : 'error', null)
        await terminalReceipt(executor, context, invocationId, cancelled ? 'cancelled' : 'failed', failure.code)
        scheduleObservation({ invocationId, status: cancelled ? 'cancelled'
          : failure.code === 'AI_CLI_TIMEOUT' ? 'timeout' : 'error', startedAt, finishedAt: new Date(),
        usage: null, retryCount, errorCode: failure.code })
        if (isStructuredOutputValidationError(cause)) throw cause
        throw failure
      }
      // A receipt-commit failure is not an executor failure and must never be
      // rewritten as a second, contradictory terminal row for this invocation.
      if (cliStart) await settleCli(cliStart, 'success', result.usage)
      await terminalReceipt(executor, context, invocationId, 'succeeded')
      scheduleObservation({ invocationId, status: 'success', startedAt, finishedAt: new Date(),
        usage: result.usage, retryCount: result.retryCount, errorCode: null })
      return result
    },
    stream(request: RoleExecutionRequest): ReadableStream<RoleExecutionEvent> {
      const invocationId = crypto.randomUUID()
      let reader: ReadableStreamDefaultReader<RoleExecutionEvent> | undefined
      let delegateStream: ReadableStream<RoleExecutionEvent> | undefined
      let started = false
      let cancelRequested = false
      let pulling: Promise<void> | undefined
      let beginning: Promise<boolean> | undefined
      let cliStart: AttemptStart | undefined
      let terminalCommit: Promise<void> | undefined
      let startedAt: Date | undefined
      let terminalUsage: RoleExecutionResult['usage'] | null = null
      let terminalRetryCount: number | null = null

      const finish = async (status: 'succeeded' | 'failed' | 'cancelled', errorCode?: AiConsoleError['code'],
        retryCount: number | null = terminalRetryCount) => {
        if (terminalCommit) return terminalCommit
        if (!started) return
        terminalCommit = cliStart ? Promise.all([
          settleCli(cliStart, status === 'succeeded' ? 'success' : status === 'cancelled' ? 'cancelled' : errorCode === 'AI_CLI_TIMEOUT' ? 'timeout' : 'error', status === 'succeeded' ? terminalUsage : null),
          terminalReceipt(executor, context, invocationId, status, errorCode),
        ]).then(() => undefined) : terminalReceipt(executor, context, invocationId, status, errorCode)
        await terminalCommit
        scheduleObservation({ invocationId,
          status: status === 'succeeded' ? 'success' : status === 'cancelled' ? 'cancelled'
            : errorCode === 'AI_CLI_TIMEOUT' ? 'timeout' : 'error',
          startedAt: startedAt!, finishedAt: new Date(),
          usage: status === 'succeeded' ? terminalUsage : null,
          retryCount: status === 'succeeded' ? terminalRetryCount : retryCount,
          errorCode: errorCode ?? null,
        })
      }

      const begin = async () => {
        if (started) return !cancelRequested
        beginning ??= (async () => {
          await startReceipt(executor, context, invocationId)
          started = true
          startedAt = new Date()
          if (cancelRequested) {
            await finish('cancelled', 'AI_EXECUTION_FAILED', 0)
            return false
          }
          const meteringContext = attribution(invocationId)
          cliStart = meteringContext?.aggregation === 'cli_aggregate' ? await startAttempt(meteringContext) : undefined
          delegateStream = executor.stream({ ...request, meteringContext })
          reader = delegateStream.getReader()
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
                await finish('cancelled', 'AI_EXECUTION_FAILED',
                  safeExecutionStreamFacts(delegateStream)?.retryCount ?? 0)
                return
              }
              if (next.done) {
                await finish('succeeded')
                controller.close()
                return
              }
              if (next.value.type === 'finish') {
                terminalUsage = next.value.usage
                terminalRetryCount = next.value.retryCount
                // A semantic finish is the provider's terminal success. Make
                // the durable receipt visible before exposing that event;
                // EOF is transport cleanup only and may never arrive.
                await finish('succeeded')
              }
              controller.enqueue(next.value)
            } catch (cause) {
              const retryCount = safeExecutionFailureFacts(cause)?.retryCount ?? null
              const failure = publicFailure(executor, cause)
              try {
                await finish(request.abortSignal?.aborted ? 'cancelled' : 'failed', failure.code, retryCount)
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
            await finish('cancelled', 'AI_EXECUTION_FAILED',
              safeExecutionStreamFacts(delegateStream)?.retryCount ?? 0)
          }
        },
      })
    },
  })
}

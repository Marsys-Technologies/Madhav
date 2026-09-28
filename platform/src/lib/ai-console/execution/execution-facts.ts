import 'server-only'

export interface SafeExecutionFailureFacts {
  readonly retryCount: number | null
}

const failureFacts = new WeakMap<object, SafeExecutionFailureFacts>()
const streamFacts = new WeakMap<object, SafeExecutionFailureFacts>()

/** Attach bounded server-only execution facts without making them serializable. */
export function attachSafeExecutionFailureFacts<T extends object>(
  error: T,
  facts: SafeExecutionFailureFacts,
): T {
  failureFacts.set(error, Object.freeze({ retryCount: facts.retryCount }))
  return error
}

export function safeExecutionFailureFacts(error: unknown): SafeExecutionFailureFacts | null {
  return typeof error === 'object' && error !== null ? failureFacts.get(error) ?? null : null
}

/**
 * Keep mutable execution progress off the public stream shape. The tracked
 * wrapper reads only this bounded fact when a consumer cancels before the
 * delegate can surface a terminal error/result.
 */
export function setSafeExecutionStreamFacts(
  stream: ReadableStream<unknown>,
  facts: SafeExecutionFailureFacts,
): void {
  streamFacts.set(stream, Object.freeze({ retryCount: facts.retryCount }))
}

export function safeExecutionStreamFacts(stream: unknown): SafeExecutionFailureFacts | null {
  return typeof stream === 'object' && stream !== null ? streamFacts.get(stream) ?? null : null
}

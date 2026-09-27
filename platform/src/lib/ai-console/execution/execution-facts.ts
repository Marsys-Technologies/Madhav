import 'server-only'

export interface SafeExecutionFailureFacts {
  readonly retryCount: number | null
}

const failureFacts = new WeakMap<object, SafeExecutionFailureFacts>()

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

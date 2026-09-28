export interface ValidationThrottleResponse {
  status(): number
  headers(): Record<string, string>
  dispose?(): Promise<void>
}

interface ValidationThrottleOptions {
  readonly now?: () => number
  readonly sleep?: (milliseconds: number) => Promise<void>
  readonly maxTotalWaitMs?: number
  readonly maxAttempts?: number
}

function retryDelay(value: string | undefined, now: number): number | null {
  if (!value) return null
  if (/^\d+$/.test(value.trim())) return Number(value.trim()) * 1_000
  const date = Date.parse(value)
  return Number.isFinite(date) ? Math.max(0, date - now) : null
}

export async function requestWithValidationThrottle<T extends ValidationThrottleResponse>(
  request: () => Promise<T>,
  options: ValidationThrottleOptions = {},
): Promise<T> {
  const now = options.now ?? Date.now
  const sleep = options.sleep ?? (milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds)))
  const maxTotalWaitMs = options.maxTotalWaitMs ?? 130_000
  const maxAttempts = options.maxAttempts ?? 3
  let waited = 0
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const response = await request()
    if (response.status() !== 429) return response
    const delay = retryDelay(response.headers()['retry-after'], now())
    if (delay === null) throw new Error('AIC_E2E_VALIDATION_RETRY_INVALID')
    if (attempt === maxAttempts || delay > maxTotalWaitMs - waited) {
      throw new Error('AIC_E2E_VALIDATION_RETRY_EXCEEDED')
    }
    await response.dispose?.()
    waited += delay
    await sleep(delay)
  }
  throw new Error('AIC_E2E_VALIDATION_RETRY_EXCEEDED')
}

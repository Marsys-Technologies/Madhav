import 'server-only'
import { claimStaleConnectionRevalidations, markConnectionForRevalidation } from './repository'
import { normalizeAiError } from './errors'
import type { OwnedProviderConnection } from './providers'
import { validateConnection } from './validation'

/** Runtime callers report one failure; never retry, switch models, or refresh inline. */
export async function markRuntimeConnectionFailure(connection: OwnedProviderConnection, cause: unknown) {
  const error = normalizeAiError(cause, { source: 'provider' })
  if (['AI_CONNECTION_INVALID', 'AI_MODEL_UNAVAILABLE', 'AI_ROLE_INCOMPATIBLE', 'AI_PROVIDER_UNREACHABLE',
    'AI_PERMISSION_DENIED', 'AI_BILLING_UNAVAILABLE', 'AI_RATE_LIMITED'].includes(error.code)) {
    await markConnectionForRevalidation(connection.userId, connection.connectionId, connection.credentialVersion, error)
  }
  return error
}

/** Fixed daily cadence, five leases, two workers; no per-request catalog churn. */
export async function revalidateStaleConnections(signal?: AbortSignal) {
  const result = { checked: 0, validated: 0, needsAttention: 0, unreachable: 0, invalid: 0, failed: 0 }
  if (signal?.aborted) return result
  const claims = await claimStaleConnectionRevalidations({ staleBefore: new Date(Date.now() - 86_400_000), limit: 5 })
  let cursor = 0
  async function worker() {
    while (cursor < claims.length && !signal?.aborted) {
      const claim = claims[cursor++]
      result.checked++
      try {
        const validation = await validateConnection(claim.userId, claim.connectionId, { credentialVersion: claim.credentialVersion, signal })
        if (validation.state === 'needs_attention') result.needsAttention++
        else result[validation.state]++
      } catch { result.failed++ }
    }
  }
  await Promise.all([worker(), worker()])
  return result
}

import 'server-only'
import { AiConsoleError, normalizeAiError } from './errors'
import {
  claimConnectionCatalogRefresh, loadConnectionCredential, storeConnectionCatalogRefresh,
} from './repository'
import { discoverConnectionModels } from './providers'
import type { DiscoveredModel } from './providers/types'

export type ProviderCatalogRefreshResult =
  | { status: 'refreshed'; modelCount: number }
  | { status: 'skipped' }

/** Refresh metadata only. Discovery never promotes a model to generation-tested. */
export async function refreshProviderCatalog(userId: string, connectionId: string,
  options: { force?: boolean; signal?: AbortSignal } = {}): Promise<ProviderCatalogRefreshResult> {
  const assertNotCancelled = () => {
    if (options.signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
  }
  assertNotCancelled()
  // The repository owns the per-connection TTL, cooldown and multi-instance lease.
  const claim = await claimConnectionCatalogRefresh(userId, connectionId, options.force === true)
  if (!claim) {
    assertNotCancelled()
    return { status: 'skipped' }
  }

  const connection = Object.freeze({ userId, connectionId,
    providerId: claim.providerId, credentialVersion: claim.credentialVersion })
  const deadline = AbortSignal.timeout(30_000)
  const signal = AbortSignal.any([deadline, ...(options.signal ? [options.signal] : [])])
  let models: DiscoveredModel[]
  try {
    assertNotCancelled()
    // Fence before discovery; its adapter also rechecks ownership/version before
    // each HTTP request, including every page of a paginated model catalogue.
    await loadConnectionCredential(userId, connectionId, claim.credentialVersion)
    assertNotCancelled()
    models = await discoverConnectionModels(connection, signal)
    assertNotCancelled()
  } catch (cause) {
    // A replaced key, deleted connection or inactive account is not evidence of
    // provider failure and must never produce a health write for another version.
    const safe = normalizeAiError(options.signal?.aborted
      ? new AiConsoleError('AI_EXECUTION_FAILED')
      : deadline.aborted ? new AiConsoleError('AI_PROVIDER_UNREACHABLE') : cause, { source: 'provider' })
    if (safe.code === 'AI_CHOICE_BROKEN') throw new AiConsoleError(safe.code)
    const stored = await storeConnectionCatalogRefresh(userId, connectionId, {
      credentialVersion: claim.credentialVersion, epoch: claim.epoch, errorCode: safe.code,
    })
    if (!stored) throw new AiConsoleError('AI_CHOICE_BROKEN')
    throw new AiConsoleError(safe.code)
  }
  const stored = await storeConnectionCatalogRefresh(userId, connectionId, {
    credentialVersion: claim.credentialVersion, epoch: claim.epoch, models,
  })
  if (!stored) throw new AiConsoleError('AI_CHOICE_BROKEN')
  return { status: 'refreshed', modelCount: models.length }
}

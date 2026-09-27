import 'server-only'
import { AiConsoleError, normalizeAiError, type PublicAiError } from './errors'
import { listAiConsoleState, loadConnectionCredential, storeConnectionValidation } from './repository'
import { ProviderIdSchema } from './types'
import { discoverConnectionModels, probeConnectionModel } from './providers'
import { chooseProbeModel } from './providers/catalog-policy'
import type { DiscoveredModel } from './providers/types'

export interface ValidationResult {
  state: 'validated' | 'needs_attention' | 'invalid' | 'unreachable'
  modelCount: number
  error?: PublicAiError
}
/** No provider request, plaintext, or upstream body enters a transaction or result. */
export async function validateConnection(userId: string, connectionId: string,
  options: { signal?: AbortSignal; credentialVersion?: number } = {}): Promise<ValidationResult> {
  const { connections } = await listAiConsoleState(userId)
  const row = connections.find(c => c.id === connectionId && !c.deleted_at)
  if (!row || (options.credentialVersion !== undefined && options.credentialVersion !== Number(row.credential_version))) throw new AiConsoleError('AI_CHOICE_BROKEN')
  const connection = { userId, connectionId, providerId: ProviderIdSchema.parse(row.provider_id), credentialVersion: Number(row.credential_version) }
  // Recheck active ownership before writing validating; each HTTP step checks again.
  await loadConnectionCredential(userId, connectionId, connection.credentialVersion)
  if (options.signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
  await storeConnectionValidation(userId, connectionId, { credentialVersion: connection.credentialVersion, state: 'validating' })
  const controller = new AbortController()
  const cancel = () => controller.abort()
  options.signal?.addEventListener('abort', cancel, { once: true })
  let expired = false
  const timer = setTimeout(() => { expired = true; cancel() }, 30_000)
  let models: DiscoveredModel[] | undefined
  let result: ValidationResult
  try {
    models = await discoverConnectionModels(connection, controller.signal)
    const model = chooseProbeModel(models)
    if (!model) throw new AiConsoleError('AI_MODEL_UNAVAILABLE')
    await probeConnectionModel(connection, model, controller.signal)
    result = { state: 'validated', modelCount: models.length }
  } catch (cause) {
    const error = normalizeAiError(expired ? new AiConsoleError('AI_PROVIDER_UNREACHABLE') : cause, { source: 'provider' })
    // Ownership/version changes must not be converted into a connection health write.
    if (error.code === 'AI_CHOICE_BROKEN') throw new AiConsoleError('AI_CHOICE_BROKEN')
    const state = error.code === 'AI_CONNECTION_INVALID' ? 'invalid'
      : error.code === 'AI_PROVIDER_UNREACHABLE' || error.code === 'AI_RATE_LIMITED' ? 'unreachable' : 'needs_attention'
    result = { state, modelCount: models?.length ?? 0, error }
  } finally {
    clearTimeout(timer); options.signal?.removeEventListener('abort', cancel)
  }
  // Do not replace a working catalog on transient/probe failure. Empty successful
  // discovery is authoritative; successful discovery + probe refresh the catalog.
  await storeConnectionValidation(userId, connectionId, { credentialVersion: connection.credentialVersion,
    state: result.state, ...(result.error ? { errorCode: result.error.code } : {}),
    ...(result.state === 'validated' || models?.length === 0 ? {
      models: models!.map(({ modelId, displayName, compatibleRoles }) => ({ modelId, displayName, compatibleRoles })),
    } : {}) })
  return result
}

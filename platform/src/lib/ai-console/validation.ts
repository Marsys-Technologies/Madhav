import 'server-only'
import { AiConsoleError, normalizeAiError, type PublicAiError } from './errors'
import { listAiConsoleState, loadConnectionCredential, storeConnectionValidation, storeProviderModelProbe } from './repository'
import { ProviderIdSchema } from './types'
import { discoverConnectionModels, probeConnectionModel } from './providers'
import { chooseProbeModel } from './providers/catalog-policy'
import type { DiscoveredModel } from './providers/types'

export interface ValidationResult {
  state: 'validated' | 'needs_attention' | 'invalid' | 'unreachable'
  modelCount: number
  error?: PublicAiError
}

/** One small generation against the exact discovered model; no bulk probes or role-success claim. */
export async function testAndSelectProviderModel(userId: string, connectionId: string, modelId: string,
  signal?: AbortSignal): Promise<void> {
  if (signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
  const state = await listAiConsoleState(userId)
  const row = state.connections.find(item => item.id === connectionId && !item.deleted_at)
  const model = state.models.find(item => item.connection_id === connectionId && item.model_id === modelId && item.available === true)
  if (!row || !model) throw new AiConsoleError('AI_MODEL_UNAVAILABLE')
  if (row.credential_validity !== 'valid' || !['validated', 'validating'].includes(String(row.validation_state))) {
    throw new AiConsoleError('AI_CONNECTION_INVALID')
  }
  const credentialVersion = Number(row.credential_version)
  const connection = { userId, connectionId, providerId: ProviderIdSchema.parse(row.provider_id), credentialVersion }
  const discovered: DiscoveredModel = { modelId: String(model.model_id), displayName: String(model.display_name),
    compatibleRoles: model.compatible_roles as DiscoveredModel['compatibleRoles'],
    supportsTools: model.supports_tools === true, supportsStructuredOutput: model.supports_structured_output === true }
  await loadConnectionCredential(userId, connectionId, credentialVersion)
  const deadline = AbortSignal.timeout(30_000)
  let usage: Awaited<ReturnType<typeof probeConnectionModel>>
  try {
    usage = await probeConnectionModel(connection, discovered, AbortSignal.any([deadline, ...(signal ? [signal] : [])]))
    if (signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
  } catch (cause) {
    if (signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
    const safe = normalizeAiError(deadline.aborted ? new AiConsoleError('AI_PROVIDER_UNREACHABLE') : cause, { source: 'provider' })
    if (safe.code === 'AI_CHOICE_BROKEN') throw new AiConsoleError('AI_CHOICE_BROKEN')
    await storeProviderModelProbe(userId, connectionId, modelId, credentialVersion, { ok: false, errorCode: safe.code })
    throw new AiConsoleError(safe.code)
  }
  await storeProviderModelProbe(userId, connectionId, modelId, credentialVersion, { ok: true,
    inputTokens: usage.inputTokens, outputTokens: usage.outputTokens })
}
/** No provider request, plaintext, or upstream body enters a transaction or result. */
export async function validateConnection(userId: string, connectionId: string,
  options: { signal?: AbortSignal; credentialVersion?: number } = {}): Promise<ValidationResult> {
  // Compose cancellation before ANY awaited state/credential work. The deadline
  // has a separate source so a caller abort cannot become a health verdict.
  const deadline = new AbortController()
  const signal = AbortSignal.any([deadline.signal, ...(options.signal ? [options.signal] : [])])
  const assertNotCancelled = () => { if (options.signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED') }
  assertNotCancelled()
  const { connections } = await listAiConsoleState(userId)
  assertNotCancelled()
  const row = connections.find(c => c.id === connectionId && !c.deleted_at)
  if (!row || (options.credentialVersion !== undefined && options.credentialVersion !== Number(row.credential_version))) throw new AiConsoleError('AI_CHOICE_BROKEN')
  const connection = { userId, connectionId, providerId: ProviderIdSchema.parse(row.provider_id), credentialVersion: Number(row.credential_version) }
  // Recheck active ownership before writing validating; each HTTP step checks again.
  await loadConnectionCredential(userId, connectionId, connection.credentialVersion)
  assertNotCancelled()
  await storeConnectionValidation(userId, connectionId, { credentialVersion: connection.credentialVersion, state: 'validating' })
  assertNotCancelled()
  let expired = false
  const timer = setTimeout(() => { expired = true; deadline.abort() }, 30_000)
  let models: DiscoveredModel[] | undefined
  let result: ValidationResult
  try {
    models = await discoverConnectionModels(connection, signal)
    const model = chooseProbeModel(models)
    if (!model) throw new AiConsoleError('AI_MODEL_UNAVAILABLE')
    await probeConnectionModel(connection, model, signal)
    result = { state: 'validated', modelCount: models.length }
  } catch (cause) {
    assertNotCancelled()
    const error = normalizeAiError(expired ? new AiConsoleError('AI_PROVIDER_UNREACHABLE') : cause, { source: 'provider' })
    // Ownership/version changes must not be converted into a connection health write.
    if (error.code === 'AI_CHOICE_BROKEN') throw new AiConsoleError('AI_CHOICE_BROKEN')
    const state = error.code === 'AI_CONNECTION_INVALID' ? 'invalid'
      : error.code === 'AI_PROVIDER_UNREACHABLE' || error.code === 'AI_RATE_LIMITED' ? 'unreachable' : 'needs_attention'
    result = { state, modelCount: models?.length ?? 0, error }
  } finally {
    clearTimeout(timer)
  }
  assertNotCancelled()
  // Do not replace a working catalog on transient/probe failure. Empty successful
  // discovery is authoritative; successful discovery + probe refresh the catalog.
  await storeConnectionValidation(userId, connectionId, { credentialVersion: connection.credentialVersion,
    state: result.state, ...(result.error ? { errorCode: result.error.code } : {}),
    ...(result.state === 'validated' || models?.length === 0 ? {
      models: models!.map(({ modelId, displayName, compatibleRoles, supportsTools, supportsStructuredOutput }) =>
        ({ modelId, displayName, compatibleRoles, supportsTools, supportsStructuredOutput })),
    } : {}) })
  return result
}

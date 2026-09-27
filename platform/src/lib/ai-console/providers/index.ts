import 'server-only'
import { inspect } from 'node:util'
import { AiConsoleError } from '../errors'
import { decryptCredential } from '../crypto'
import {
  assertConnectionRequestAuthorized, assertRuntimeModelRequestAuthorized, loadConnectionCredential,
  loadRuntimeModelCredential,
} from '../repository'
import type { DiscoveredModel, OwnedConnectionRuntimeBinding, RuntimeModelBinding } from './types'
import { ProviderIdSchema, type ProviderId } from '../types'
import { anthropicAdapter } from './anthropic'
import { googleAdapter } from './google'
import { createOpenAICompatibleAdapter } from './openai-compatible'
import type { ProviderValidationAdapter } from './types'

const providers: Record<ProviderId, ProviderValidationAdapter> = Object.freeze({
  openai: createOpenAICompatibleAdapter('openai'), anthropic: anthropicAdapter, google: googleAdapter,
  xai: createOpenAICompatibleAdapter('xai'), deepseek: createOpenAICompatibleAdapter('deepseek'),
  kimi: createOpenAICompatibleAdapter('kimi'), openrouter: createOpenAICompatibleAdapter('openrouter'),
})
export function getProviderAdapter(providerId: ProviderId): ProviderValidationAdapter {
  return providers[ProviderIdSchema.parse(providerId)]
}
export interface OwnedProviderConnection {
  userId: string
  connectionId: string
  providerId: ProviderId
  credentialVersion: number
}
async function ownedCredential(connection: OwnedProviderConnection) {
  await assertConnectionRequestAuthorized(connection)
  return loadConnectionCredential(connection.userId, connection.connectionId, connection.credentialVersion)
}
// Plaintext is decrypted only here, immediately before adapter invocation. No cache.
export async function discoverConnectionModels(connection: OwnedProviderConnection, signal: AbortSignal) {
  connection = Object.freeze({ ...connection })
  const record = await ownedCredential(connection)
  let key: string | undefined = decryptCredential(record)
  try { return await getProviderAdapter(connection.providerId).discover(key, signal, () => assertConnectionRequestAuthorized(connection)) }
  finally { key = undefined }
}
export async function probeConnectionModel(connection: OwnedProviderConnection, model: DiscoveredModel, signal: AbortSignal) {
  connection = Object.freeze({ ...connection })
  const record = await ownedCredential(connection)
  let key: string | undefined = decryptCredential(record)
  try { return await getProviderAdapter(connection.providerId).probe(key, model, signal, () => assertConnectionRequestAuthorized(connection)) }
  finally { key = undefined }
}
/** Caller owns disposal in a finally block for the entire request, including streams. */
export async function createConnectionRuntimeBinding(connection: OwnedProviderConnection, model: DiscoveredModel) {
  connection = Object.freeze({ ...connection })
  const record = await loadRuntimeModelCredential({ ...connection, modelId: model.modelId })
  let key: string | undefined = decryptCredential(record)
  try {
    const binding = getProviderAdapter(connection.providerId).createRuntimeBinding(key, model,
      () => assertRuntimeModelRequestAuthorized({ ...connection, modelId: model.modelId }))
    return ownedConnectionBinding(connection.connectionId, binding)
  }
  finally { key = undefined }
}

function ownedConnectionBinding(connectionId: string, binding: RuntimeModelBinding): OwnedConnectionRuntimeBinding {
  const owned = Object.create(null)
  Object.defineProperties(owned, {
    providerId: { value: binding.providerId, enumerable: true },
    connectionId: { value: connectionId, enumerable: true },
    modelId: { value: binding.modelId, enumerable: true },
    model: { get: () => binding.model, enumerable: false },
    dispose: { value: () => binding.dispose(), enumerable: false },
    toJSON: { value: () => { throw new AiConsoleError('AI_EXECUTION_FAILED') } },
    [inspect.custom]: { value: () => '[OwnedConnectionRuntimeBinding REDACTED]' },
  })
  return Object.freeze(owned) as OwnedConnectionRuntimeBinding
}

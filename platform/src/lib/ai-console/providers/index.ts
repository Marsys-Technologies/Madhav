import 'server-only'
import { decryptCredential } from '../crypto'
import {
  assertConnectionRequestAuthorized, assertRuntimeModelRequestAuthorized, loadConnectionCredential,
} from '../repository'
import type { DiscoveredModel } from './types'
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
async function ownedRuntimeCredential(connection: OwnedProviderConnection, modelId: string) {
  await assertRuntimeModelRequestAuthorized({ ...connection, modelId })
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
  const record = await ownedRuntimeCredential(connection, model.modelId)
  let key: string | undefined = decryptCredential(record)
  try { return getProviderAdapter(connection.providerId).createRuntimeBinding(key, model,
    () => assertRuntimeModelRequestAuthorized({ ...connection, modelId: model.modelId })) }
  finally { key = undefined }
}

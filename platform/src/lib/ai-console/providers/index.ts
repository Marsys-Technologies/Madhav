import 'server-only'
import { decryptCredential } from '../crypto'
import { listAiConsoleState, loadConnectionCredential } from '../repository'
import { AiConsoleError } from '../errors'
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
  const { connections } = await listAiConsoleState(connection.userId)
  const row = connections.find(c => c.id === connection.connectionId && !c.deleted_at)
  if (!row || row.provider_id !== connection.providerId || Number(row.credential_version) !== connection.credentialVersion) throw new AiConsoleError('AI_CHOICE_BROKEN')
  return loadConnectionCredential(connection.userId, connection.connectionId, connection.credentialVersion)
}
// Plaintext is decrypted only here, immediately before adapter invocation. No cache.
export async function discoverConnectionModels(connection: OwnedProviderConnection, signal: AbortSignal) {
  const record = await ownedCredential(connection)
  let key: string | undefined = decryptCredential(record)
  try { return await getProviderAdapter(connection.providerId).discover(key, signal) }
  finally { key = undefined }
}
export async function probeConnectionModel(connection: OwnedProviderConnection, model: DiscoveredModel, signal: AbortSignal) {
  const record = await ownedCredential(connection)
  let key: string | undefined = decryptCredential(record)
  try { return await getProviderAdapter(connection.providerId).probe(key, model, signal) }
  finally { key = undefined }
}
/** Caller owns disposal in a finally block for the entire request, including streams. */
export async function createConnectionRuntimeBinding(connection: OwnedProviderConnection, model: DiscoveredModel) {
  const record = await ownedCredential(connection)
  let key: string | undefined = decryptCredential(record)
  try { return getProviderAdapter(connection.providerId).createRuntimeBinding(key, model) }
  finally { key = undefined }
}

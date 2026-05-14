import type { ModelMeta } from '@/lib/models/registry'
import type { QueryRequest, ModelInteractionEvent } from '../types'

export interface StreamTextOptions {
  model: unknown
  system?: string
  messages: unknown[]
  tools?: unknown
  toolChoice?: unknown
  providerOptions?: Record<string, unknown>
  maxOutputTokens?: number
  temperature?: number
  stopWhen?: unknown
  experimental_transform?: unknown
  onStepFinish?: (step: unknown) => Promise<void> | void
  onFinish?: (result: unknown) => Promise<void> | void
  maxRetries?: number
}

export interface Adapter {
  readonly providerId: string

  /** Build the streamText options object for this provider + request. */
  prepareRequest(req: QueryRequest, meta: ModelMeta): StreamTextOptions

  /** Stream the model's response as ModelInteractionEvents (existing AD.3 behavior). */
  stream(req: QueryRequest, meta: ModelMeta): ReadableStream<ModelInteractionEvent>
}

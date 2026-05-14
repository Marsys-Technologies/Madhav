import type { ModelMeta } from '@/lib/models/registry'
import type { QueryRequest, ModelInteractionEvent } from '../types'

export interface Adapter {
  readonly providerId: string
  stream(req: QueryRequest, meta: ModelMeta): ReadableStream<ModelInteractionEvent>
}

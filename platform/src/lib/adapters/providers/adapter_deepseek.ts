import type { ModelMeta } from '@/lib/models/registry'
import type { QueryRequest, ModelInteractionEvent } from '../types'
import type { Adapter } from './base'

export const adapterDeepseek: Adapter = {
  providerId: 'deepseek',
  stream(_req: QueryRequest, _meta: ModelMeta): ReadableStream<ModelInteractionEvent> {
    throw new Error('adapter_deepseek.stream: not yet implemented — AD.3 work')
  },
}

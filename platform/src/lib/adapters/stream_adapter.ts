import 'server-only'
import type { QueryRequest, ModelInteractionEvent } from './types'
import { adapterFor } from './dispatcher'
import { getModelMeta, DEFAULT_STACK_ID, DEFAULT_MODEL_ID, STACK_ROUTING } from '@/lib/models/registry'

export function streamAdapter(req: QueryRequest): ReadableStream<ModelInteractionEvent> {
  const modelId = resolveModelId(req)
  const meta = getModelMeta(modelId)
  if (!meta) {
    throw new Error(`streamAdapter: unknown model ${modelId}`)
  }
  const adapter = adapterFor(meta.provider)
  return adapter.stream(req, meta)
}

// AD.2 synchronous model resolution — AD.4 replaces with async getEffectiveModel()
// Test fixtures should use modelOverride to bypass this path.
function resolveModelId(req: QueryRequest): string {
  if (req.modelOverride) return req.modelOverride.modelId
  const stack = req.stack ?? DEFAULT_STACK_ID
  return STACK_ROUTING[stack]?.[req.callType]?.primary ?? DEFAULT_MODEL_ID
}

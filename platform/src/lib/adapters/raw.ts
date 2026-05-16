import 'server-only'
import { streamText, type StreamTextResult } from 'ai'
import type { QueryRequest } from './types'
import type { ModelMeta } from '@/lib/models/registry'
import { getModelMeta, DEFAULT_STACK_ID, DEFAULT_MODEL_ID, STACK_ROUTING } from '@/lib/models/registry'
import { adapterFor } from './dispatcher'

export interface RawAdapterResult {
  /** AI SDK StreamTextResult — caller can use .toUIMessageStreamResponse(), .fullStream, etc. */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  result: StreamTextResult<any, any>
  /** Model meta for cost/usage attribution. */
  meta: ModelMeta
}

/**
 * Low-level adapter entry point. Builds provider-correct streamText options
 * for the requested call type + model via the provider adapter's prepareRequest,
 * invokes streamText, and returns the AI SDK result to the caller.
 */
export function streamAdapterRaw(req: QueryRequest): RawAdapterResult {
  const modelId = req.modelOverride?.modelId ?? resolveModelForCallType(req)
  const meta = getModelMeta(modelId)
  if (!meta) throw new Error(`streamAdapterRaw: unknown model ${modelId}`)

  const adapter = adapterFor(meta.provider)
  const options = adapter.prepareRequest(req, meta)

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const result = streamText(options as any)

  return { result, meta }
}


function resolveModelForCallType(req: QueryRequest): string {
  const stack = req.stack ?? DEFAULT_STACK_ID
  return STACK_ROUTING[stack]?.[req.callType]?.primary ?? DEFAULT_MODEL_ID
}

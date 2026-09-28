import 'server-only'
import { jsonSchema, Output, streamText, type StreamTextResult } from 'ai'
import { AiConsoleError } from '@/lib/ai-console/errors'
import type { ProviderId } from '@/lib/ai-console/types'
import type { QueryRequest, SafeRuntimeModelDescriptor } from './types'
import type { ModelMeta } from '@/lib/models/registry'
import { getModelMeta, DEFAULT_STACK_ID, DEFAULT_MODEL_ID, STACK_ROUTING } from '@/lib/models/registry'
import { adapterFor } from './dispatcher'

export interface RawAdapterResult {
  /** AI SDK StreamTextResult — caller can use .toUIMessageStreamResponse(), .fullStream, etc. */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  result: StreamTextResult<any, any>
  /** Model meta for cost/usage attribution. */
  meta: ModelMeta
  /** Present for request-owned bindings; retains the originating provider identity. */
  descriptor?: SafeRuntimeModelDescriptor
}

/**
 * Low-level adapter entry point. Builds provider-correct streamText options
 * for the requested call type + model via the provider adapter's prepareRequest,
 * invokes streamText, and returns the AI SDK result to the caller.
 */
export function streamAdapterRaw(req: QueryRequest): RawAdapterResult {
  if (req.runtimeBinding !== undefined || req.runtimeDescriptor !== undefined) {
    return streamInjected(req)
  }
  const modelId = req.modelOverride?.modelId ?? resolveModelForCallType(req)
  const meta = getModelMeta(modelId)
  if (!meta) throw new Error(`streamAdapterRaw: unknown model ${modelId}`)

  const adapter = adapterFor(meta.provider)
  const options = adapter.prepareRequest(req, meta)

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const result = streamText(options as any)

  return { result, meta }
}

function streamInjected(req: QueryRequest): RawAdapterResult {
  const binding = req.runtimeBinding
  const descriptor = req.runtimeDescriptor
  if (!binding || !descriptor
    || binding.providerId !== descriptor.providerId
    || binding.connectionId !== descriptor.connectionId
    || binding.modelId !== descriptor.modelId) {
    throw new AiConsoleError('AI_EXECUTION_FAILED')
  }
  const meta = runtimeMeta(descriptor, req.maxOutputTokens)
  const adapter = adapterFor(descriptor.providerId)
  const options = adapter.prepareRequest(req, meta, binding.model)
  if (req.responseSchema) options.output = Output.object({ schema: jsonSchema(req.responseSchema) })
  // Request-owned execution owns its only same-target retry. SDK retry must stay disabled.
  options.maxRetries = 0
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const result = streamText(options as any)
  return { result, meta, descriptor: Object.freeze({ ...descriptor }) }
}

function runtimeMeta(descriptor: SafeRuntimeModelDescriptor, requestedLimit?: number): ModelMeta {
  const provider = transportProvider(descriptor.providerId)
  const quirks = provider === 'anthropic' ? {
    reasoning_via: 'none' as const, streaming_required: false,
    tool_use_format: 'anthropic' as const, structured_output_format: 'json_schema' as const,
    cache_strategy: 'explicit_headers' as const, system_prompt_shape: 'system_block_array' as const,
  } : provider === 'google' ? {
    reasoning_via: 'native' as const, streaming_required: false,
    tool_use_format: 'gemini' as const, structured_output_format: 'gemini_response_schema' as const,
    cache_strategy: 'context_caching' as const, system_prompt_shape: 'system_message' as const,
  } : provider === 'deepseek' ? {
    reasoning_via: 'markers' as const, streaming_required: false,
    tool_use_format: 'openai' as const, structured_output_format: 'json_schema' as const,
    cache_strategy: 'automatic' as const, system_prompt_shape: 'system_message' as const,
  } : {
    reasoning_via: 'none' as const, streaming_required: false,
    tool_use_format: 'openai' as const, structured_output_format: 'json_schema' as const,
    cache_strategy: 'automatic' as const, system_prompt_shape: 'system_message' as const,
  }
  return {
    id: descriptor.modelId, label: descriptor.modelId, hint: '', provider,
    tier: 'mid', speedTier: 'balanced', maxOutputTokens: requestedLimit ?? 4_096,
    capabilities: [], role: 'both', costPer1MInput: 0, costPer1MOutput: 0,
    reasoningMode: quirks.reasoning_via, quirks,
  }
}

function transportProvider(provider: ProviderId): ModelMeta['provider'] {
  if (provider === 'xai' || provider === 'kimi' || provider === 'openrouter') return 'openai'
  return provider
}


function resolveModelForCallType(req: QueryRequest): string {
  const stack = req.stack ?? DEFAULT_STACK_ID
  return STACK_ROUTING[stack]?.[req.callType]?.primary ?? DEFAULT_MODEL_ID
}

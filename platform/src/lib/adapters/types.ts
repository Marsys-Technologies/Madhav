import type { JSONSchema7 } from 'json-schema'
import type { CallType, ModelStack, Provider } from '@/lib/models/registry'

export type { JSONSchema7 as JSONSchema }

export interface ProviderQuirks {
  /** How chain-of-thought reasoning surfaces in model output. */
  reasoning_via: 'markers' | 'native' | 'none'
  /** Whether the provider requires stream:true on every request. */
  streaming_required: boolean
  /** The tool-calling wire format this provider accepts. */
  tool_use_format: 'openai' | 'anthropic' | 'gemini' | 'none'
  /** The structured output format this provider supports. */
  structured_output_format: 'json_schema' | 'json_object' | 'gemini_response_schema' | 'none'
  /** How prompt caching is activated for this provider. */
  cache_strategy: 'automatic' | 'explicit_headers' | 'context_caching' | 'none'
  /** Where the system prompt is placed in the request. */
  system_prompt_shape: 'inline' | 'system_message' | 'system_block_array'
  /** Provider-specific request transform hints keyed by purpose. */
  request_transforms?: Record<string, unknown>
}

export interface QueryRequest {
  callType: CallType
  stack?: ModelStack
  modelOverride?: { modelId: string }

  systemPrompt: string
  messages: Array<{ role: 'user' | 'assistant'; content: string }>

  tools?: ToolDefinition[]
  responseSchema?: JSONSchema7

  maxOutputTokens?: number
  temperature?: number
  reasoning?: 'auto' | 'enable' | 'disable'
  timeoutMs?: number

  traceId?: string
  userId?: string
  parentEventId?: string
}

export interface ToolDefinition {
  name: string
  description: string
  parameters: JSONSchema7
}

export interface ModelInteraction {
  modelId: string
  provider: Provider

  reasoning?: { text: string; tokens: number }
  intermediate: Array<IntermediateEvent>
  finalText?: string
  finalStructured?: unknown

  finishReason: 'stop' | 'length' | 'tool_calls' | 'content_filter' | 'error'
  usage: {
    inputTokens: number
    outputTokens: number
    reasoningTokens?: number
    cacheReadTokens?: number
    cacheWriteTokens?: number
    costUsd: number
    latencyMs: number
  }
  providerMeta: {
    requestId?: string
    raw?: unknown
  }
}

export interface IntermediateEvent {
  type: 'tool_call' | 'tool_result' | 'status'
  ts: number
  payload: unknown
}

export type ModelInteractionEvent =
  | { type: 'status'; ts: number; status: 'queued' | 'planning' | 'retrieving' | 'reasoning' | 'tool_calling' | 'composing' | 'complete' }
  | { type: 'reasoning_delta'; ts: number; text: string }
  | { type: 'tool_call'; ts: number; name: string; args: unknown; callId: string }
  | { type: 'tool_result'; ts: number; callId: string; result: unknown }
  | { type: 'text_delta'; ts: number; text: string }
  | { type: 'finish'; ts: number; interaction: ModelInteraction }
  | { type: 'error'; ts: number; error: { message: string; code?: string } }

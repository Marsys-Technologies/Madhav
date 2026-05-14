import { expectTypeOf, describe, it } from 'vitest'
import type {
  QueryRequest,
  ModelInteraction,
  ModelInteractionEvent,
  IntermediateEvent,
  ToolDefinition,
} from '../types'

describe('adapter types — compile-time shape assertions', () => {
  it('QueryRequest has required string fields', () => {
    expectTypeOf<QueryRequest['systemPrompt']>().toBeString()
    expectTypeOf<QueryRequest['callType']>().toBeString()
  })

  it('QueryRequest messages array is typed correctly', () => {
    expectTypeOf<QueryRequest['messages']>().toEqualTypeOf<
      Array<{ role: 'user' | 'assistant'; content: string }>
    >()
  })

  it('QueryRequest optional fields are optional', () => {
    expectTypeOf<QueryRequest['tools']>().toEqualTypeOf<ToolDefinition[] | undefined>()
    expectTypeOf<QueryRequest['maxOutputTokens']>().toEqualTypeOf<number | undefined>()
    expectTypeOf<QueryRequest['reasoning']>().toEqualTypeOf<
      'auto' | 'enable' | 'disable' | undefined
    >()
    expectTypeOf<QueryRequest['traceId']>().toEqualTypeOf<string | undefined>()
  })

  it('ToolDefinition has required fields', () => {
    expectTypeOf<ToolDefinition['name']>().toBeString()
    expectTypeOf<ToolDefinition['description']>().toBeString()
  })

  it('ModelInteraction usage has required numeric fields', () => {
    expectTypeOf<ModelInteraction['usage']['inputTokens']>().toBeNumber()
    expectTypeOf<ModelInteraction['usage']['outputTokens']>().toBeNumber()
    expectTypeOf<ModelInteraction['usage']['costUsd']>().toBeNumber()
    expectTypeOf<ModelInteraction['usage']['latencyMs']>().toBeNumber()
  })

  it('ModelInteraction reasoning and finalText are optional', () => {
    expectTypeOf<ModelInteraction['reasoning']>().toEqualTypeOf<
      { text: string; tokens: number } | undefined
    >()
    expectTypeOf<ModelInteraction['finalText']>().toEqualTypeOf<string | undefined>()
  })

  it('ModelInteraction finishReason union is exhaustive', () => {
    expectTypeOf<ModelInteraction['finishReason']>().toEqualTypeOf<
      'stop' | 'length' | 'tool_calls' | 'content_filter' | 'error'
    >()
  })

  it('IntermediateEvent type union is correct', () => {
    expectTypeOf<IntermediateEvent['type']>().toEqualTypeOf<
      'tool_call' | 'tool_result' | 'status'
    >()
    expectTypeOf<IntermediateEvent['ts']>().toBeNumber()
  })

  it('ModelInteractionEvent union discriminant covers all event types', () => {
    type EventType = ModelInteractionEvent['type']
    expectTypeOf<EventType>().toEqualTypeOf<
      | 'status'
      | 'reasoning_delta'
      | 'tool_call'
      | 'tool_result'
      | 'text_delta'
      | 'finish'
      | 'error'
    >()
  })

  it('ModelInteractionEvent finish variant carries a ModelInteraction', () => {
    type FinishEvent = Extract<ModelInteractionEvent, { type: 'finish' }>
    expectTypeOf<FinishEvent['interaction']>().toEqualTypeOf<ModelInteraction>()
  })

  it('ModelInteractionEvent error variant carries message string', () => {
    type ErrorEvent = Extract<ModelInteractionEvent, { type: 'error' }>
    expectTypeOf<ErrorEvent['error']['message']>().toBeString()
  })
})

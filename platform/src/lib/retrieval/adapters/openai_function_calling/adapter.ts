/**
 * adapters/openai_function_calling/adapter.ts
 *
 * OpenAI function schema translation; parallel tool calls; structured outputs.
 * Translates Marsys capability descriptors to OpenAI function call format.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import { listCapabilities } from '../../registry'
import type { CapabilityDescriptor, CapabilityContext } from '../../registry/types'

// ── OpenAI function schema types ──────────────────────────────────────────────

export interface OpenAIFunction {
  name: string
  description: string
  parameters: {
    type: 'object'
    properties: Record<string, { type: string; description?: string; enum?: string[] }>
    required?: string[]
  }
}

export interface OpenAIToolCall {
  id: string
  type: 'function'
  function: {
    name: string
    arguments: string  // JSON string
  }
}

export interface OpenAIToolResult {
  tool_call_id: string
  role: 'tool'
  content: string
}

// ── Schema translation ────────────────────────────────────────────────────────

/**
 * Translate a Marsys tool URI to a safe OpenAI function name.
 * marsys://tool/L0/resolve_entity → marsys__L0__resolve_entity
 */
function uriToFunctionName(uri: string): string {
  return uri.replace('marsys://tool/', '').replace(/\//g, '__')
}

/**
 * Reverse: OpenAI function name → marsys URI.
 */
function functionNameToUri(name: string): string {
  return 'marsys://tool/' + name.replace(/__/g, '/')
}

/**
 * Convert a Marsys CapabilityDescriptor to OpenAI function definition.
 */
export function toOpenAIFunction(cap: CapabilityDescriptor): OpenAIFunction {
  const properties: Record<string, { type: string; description?: string; enum?: string[] }> = {}
  for (const [key, schema] of Object.entries(cap.input_schema ?? {})) {
    properties[key] = {
      type: schema.type,
      description: schema.description,
      enum: schema.enum as string[] | undefined,
    }
  }
  return {
    name: uriToFunctionName(cap.uri),
    description: cap.description,
    parameters: {
      type: 'object',
      properties,
      required: cap.required_inputs ?? [],
    },
  }
}

/**
 * Export all registered tool capabilities as OpenAI function definitions.
 */
export function getAllOpenAIFunctions(): OpenAIFunction[] {
  return listCapabilities({ type: 'tool' }).map(toOpenAIFunction)
}

// ── Parallel tool call executor ───────────────────────────────────────────────

/**
 * Execute a batch of OpenAI tool calls in parallel.
 * Maps function names back to Marsys URIs; invokes handlers.
 */
export async function executeToolCalls(
  toolCalls: OpenAIToolCall[],
  ctx: CapabilityContext
): Promise<OpenAIToolResult[]> {
  const { getCapability } = await import('../../registry')

  const promises = toolCalls.map(async (tc): Promise<OpenAIToolResult> => {
    const uri = functionNameToUri(tc.function.name)
    const cap = getCapability(uri)

    if (!cap || cap.type !== 'tool') {
      return {
        tool_call_id: tc.id,
        role: 'tool',
        content: JSON.stringify({ error: `Unknown function: ${tc.function.name}` }),
      }
    }

    try {
      const args = JSON.parse(tc.function.arguments) as Record<string, unknown>
      const result = await cap.handler(args, ctx)
      return {
        tool_call_id: tc.id,
        role: 'tool',
        content: JSON.stringify(result),
      }
    } catch (err) {
      return {
        tool_call_id: tc.id,
        role: 'tool',
        content: JSON.stringify({ error: String(err) }),
      }
    }
  })

  return Promise.all(promises)
}

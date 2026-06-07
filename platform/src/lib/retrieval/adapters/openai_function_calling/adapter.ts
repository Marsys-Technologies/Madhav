/**
 * adapters/openai_function_calling/adapter.ts
 *
 * OpenAI function schema translation; parallel tool calls; structured outputs.
 * Translates Marsys capability descriptors to OpenAI function call format.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import { listCapabilities } from '../../registry'
import type { ToolCapability, CapabilityContext } from '../../registry/types'

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
 * Convert a Marsys ToolCapability to OpenAI function definition.
 */
export function toOpenAIFunction(cap: ToolCapability): OpenAIFunction {
  return {
    name: uriToFunctionName(cap.uri),
    description: cap.description,
    parameters: {
      type: 'object',
      properties: cap.input_schema.properties,
      required: cap.input_schema.required ?? [],
    },
  }
}

/**
 * Export all registered tool capabilities as OpenAI function definitions.
 */
export function getAllOpenAIFunctions(): OpenAIFunction[] {
  return (listCapabilities({ primitive_type: 'tool' }) as ToolCapability[])
    .map(toOpenAIFunction)
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

    if (!cap || cap.primitive_type !== 'tool') {
      return {
        tool_call_id: tc.id,
        role: 'tool',
        content: JSON.stringify({ error: `Unknown function: ${tc.function.name}` }),
      }
    }

    try {
      const args = JSON.parse(tc.function.arguments) as Record<string, unknown>
      const result = await (cap as ToolCapability).handler(args, ctx)
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

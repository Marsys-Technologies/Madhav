/**
 * Agentic Loop Adapter — Deferred Tool Loader
 * =============================================
 * LLM gets a catalog of tool names first; full schemas loaded on demand.
 * This reduces context size for loops with many available tools.
 */

import { listCapabilities, getCapability } from '@/lib/retrieval/registry'
import type { CapabilityDescriptor, CapabilityUri } from '@/lib/retrieval/registry/types'

export interface ToolCatalogEntry {
  uri: CapabilityUri
  name: string
  description: string
  cost_class: string
}

export interface LoadedToolSchema {
  uri: CapabilityUri
  name: string
  description: string
  input_schema: Record<string, unknown>
  required_inputs: string[]
}

/**
 * Get the lightweight catalog (names + descriptions only).
 * This is what the LLM sees first to decide which tools to call.
 */
export function getToolCatalog(): ToolCatalogEntry[] {
  return listCapabilities({ type: 'tool' }).map((cap) => ({
    uri: cap.uri,
    name: cap.name,
    description: cap.description,
    cost_class: cap.llm_hints?.agentic?.cost_class || 'medium',
  }))
}

/**
 * Load the full schema for a specific tool (called when LLM wants to invoke it).
 */
export function loadToolSchema(uri: CapabilityUri): LoadedToolSchema | null {
  const cap = getCapability(uri)
  if (!cap || cap.type !== 'tool') return null

  return {
    uri: cap.uri,
    name: cap.name,
    description: cap.description,
    input_schema: cap.input_schema || {},
    required_inputs: cap.required_inputs || [],
  }
}

/**
 * Load schemas for multiple tools at once.
 */
export function loadToolSchemas(uris: CapabilityUri[]): LoadedToolSchema[] {
  return uris.flatMap((uri) => {
    const schema = loadToolSchema(uri)
    return schema ? [schema] : []
  })
}

/**
 * Convert a LoadedToolSchema to OpenAI function-calling format.
 */
export function toOpenAIFunctionSchema(schema: LoadedToolSchema): object {
  return {
    type: 'function',
    function: {
      name: schema.name,
      description: schema.description,
      parameters: {
        type: 'object',
        properties: schema.input_schema,
        required: schema.required_inputs,
      },
    },
  }
}

/**
 * Convert a LoadedToolSchema to Gemini function declaration format.
 */
export function toGeminiFunctionDeclaration(schema: LoadedToolSchema): object {
  return {
    name: schema.name,
    description: schema.description,
    parameters: {
      type: 'OBJECT',
      properties: schema.input_schema,
      required: schema.required_inputs,
    },
  }
}

/**
 * Sort tools by priority for the LLM to consider first.
 * cheap < medium < expensive; higher bulk_context priority first.
 */
export function prioritizeCatalog(catalog: ToolCatalogEntry[]): ToolCatalogEntry[] {
  const costOrder = { cheap: 0, medium: 1, expensive: 2 }
  return [...catalog].sort(
    (a, b) => (costOrder[a.cost_class as keyof typeof costOrder] ?? 1) -
               (costOrder[b.cost_class as keyof typeof costOrder] ?? 1)
  )
}

/**
 * Filter catalog to tools suitable for the current query intent.
 */
export function filterCatalogByIntent(
  catalog: ToolCatalogEntry[],
  intent_tags: string[]
): ToolCatalogEntry[] {
  if (intent_tags.length === 0) return catalog

  // For now, include all tools — intent filtering will be added in later streams
  // when the intent classifier is fully wired
  return catalog
}

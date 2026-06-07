/**
 * adapters/agentic_loop/deferred_tool_loader.ts
 *
 * LLM gets tool catalog (names + descriptions) first;
 * full schemas loaded on demand when the LLM requests a specific tool.
 * Reduces initial context size for large registries.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import { listCapabilities, getCapability } from '../../registry'
import type { ToolCapability } from '../../registry/types'

export interface ToolCatalogEntry {
  uri: string
  name: string
  description: string
  layer: string
  cost_class: string
}

export interface LoadedTool {
  uri: string
  name: string
  description: string
  input_schema: ToolCapability['input_schema']
  output_schema?: ToolCapability['output_schema']
}

/**
 * Return the lightweight catalog of all registered tools.
 * Safe to inject into every LLM turn without schema bloat.
 */
export function getToolCatalog(): ToolCatalogEntry[] {
  return listCapabilities({ primitive_type: 'tool' }).map(cap => ({
    uri: cap.uri,
    name: cap.name,
    description: cap.description,
    layer: cap.layer,
    cost_class: (cap.llm_hints.agentic?.cost_class) ?? 'medium',
  })) as ToolCatalogEntry[]
}

/**
 * Load full schema for a specific tool URI.
 * Called when the LLM decides it wants to invoke that tool.
 */
export function loadToolSchema(uri: string): LoadedTool | null {
  const cap = getCapability(uri)
  if (!cap || cap.primitive_type !== 'tool') return null
  const tool = cap as ToolCapability
  return {
    uri: tool.uri,
    name: tool.name,
    description: tool.description,
    input_schema: tool.input_schema,
    output_schema: tool.output_schema,
  }
}

/**
 * Format catalog as a compact system prompt section.
 */
export function formatCatalogForPrompt(catalog: ToolCatalogEntry[]): string {
  const lines = ['## Available Tools', '']
  for (const t of catalog) {
    lines.push(`- **${t.name}** (\`${t.uri}\`) [${t.layer}, ${t.cost_class}]: ${t.description}`)
  }
  lines.push('')
  lines.push('To use a tool, request its full schema via LOAD_TOOL_SCHEMA(uri), then call it.')
  return lines.join('\n')
}

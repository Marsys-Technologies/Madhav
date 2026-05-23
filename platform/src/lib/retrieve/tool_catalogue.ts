/**
 * tool_catalogue.ts — Bridges the MARSYS retrieval registry to the
 * CapabilityAdapter ChatTool shape used by adapter.tools().
 *
 * R11F-A-S2: Fixes Break B1 — replaces the `tools: []` stub in route.ts
 * with a live mapping of planner-authorised tool names to ChatTool objects.
 */

import type { ChatTool } from '@/lib/providers/types'
import { RETRIEVAL_TOOLS } from './index'

// Build a name → RetrievalTool lookup once at module load time.
const _registryByName = new Map(RETRIEVAL_TOOLS.map(t => [t.name, t]))

/**
 * Converts a single retrieval registry entry into a ChatTool suitable for
 * passing to adapter.tools().
 *
 * Returns null if the tool name is not found in the registry — callers
 * should log a warning and skip the missing entry.
 */
export function convertRetrievalToolToChatTool(name: string): ChatTool | null {
  const entry = _registryByName.get(name)
  if (!entry) return null
  return {
    name: entry.name,
    description: entry.description ?? `MARSYS retrieval tool: ${entry.name}`,
    // RetrievalTool does not carry a JSON Schema; supply a permissive object
    // schema so every provider can call the tool without schema validation errors.
    inputSchema: { type: 'object', properties: {} },
  }
}

/**
 * Converts an array of planner-authorised tool names into ChatTools.
 * Silently skips names not found in the registry and emits a console warning
 * for each missing entry so operators can catch mismatches.
 */
export function buildChatToolsFromNames(names: string[]): ChatTool[] {
  const result: ChatTool[] = []
  for (const name of names) {
    const tool = convertRetrievalToolToChatTool(name)
    if (tool) {
      result.push(tool)
    } else {
      console.warn(
        `[tool_catalogue] tool '${name}' not found in retrieval registry; skipping`,
      )
    }
  }
  return result
}

/**
 * tool_catalogue.ts — Bridges the MARSYS retrieval registry to the
 * CapabilityAdapter ChatTool shape used by adapter.tools().
 *
 * R11F-A-S2: Fixes Break B1 — replaces the `tools: []` stub in route.ts
 * with a live mapping of planner-authorised tool names to ChatTool objects.
 *
 * R11F-A-S6: Adds normalizeInputSchema() — the single boundary function that
 * guarantees every ChatTool emitted has a JSON Schema with type:'object' at
 * the root, satisfying Anthropic's strict input_schema requirement (and
 * Gemini/OpenAI analogues). All providers rely on this invariant.
 */

import type { ChatTool } from '@/lib/providers/types'
import { RETRIEVAL_TOOLS } from './index'

type NormalizedSchema = {
  type: 'object'
  properties: Record<string, unknown>
  required?: string[]
  additionalProperties?: boolean
}

/**
 * Defensive schema normalizer — the single boundary that guarantees every
 * ChatTool inputSchema has `type: 'object'` at the root. Call this on any
 * raw schema before exposing it through a ChatTool.
 *
 * Rules:
 * - Always sets type: 'object'
 * - Preserves properties if it is a plain object; otherwise defaults to {}
 * - Preserves required[] if present; omits if absent
 * - Handles null/undefined input gracefully
 */
export function normalizeInputSchema(raw: Record<string, unknown> | null | undefined): NormalizedSchema {
  const r = (raw != null && typeof raw === 'object') ? raw as Record<string, unknown> : {}
  const properties =
    (r.properties != null && typeof r.properties === 'object' && !Array.isArray(r.properties))
      ? r.properties as Record<string, unknown>
      : {}
  const result: NormalizedSchema = { type: 'object', properties }
  if (Array.isArray(r.required)) {
    result.required = r.required as string[]
  }
  if (typeof r.additionalProperties === 'boolean') {
    result.additionalProperties = r.additionalProperties
  }
  return result
}

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
    inputSchema: normalizeInputSchema({}),
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

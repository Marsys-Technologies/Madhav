/**
 * schema_utils.ts — Shared JSON-schema normalisation helpers + chat tool builder
 * ===============================================================================
 * D7 chat-channel migration (§3 — Phase 4 utility repoint; §4 — lib/retrieve retirement).
 *
 * `normalizeInputSchema` was previously exported from `@/lib/retrieve/tool_catalogue`.
 * `buildChatToolsFromNames` was also previously exported from `@/lib/retrieve/tool_catalogue`.
 * Both moved here as part of D7 Step 4 retirement (2026-06-28).
 *
 * Callers that previously imported from `@/lib/retrieve/tool_catalogue` now import from here.
 */

import { CONTRACT_CATALOG_BY_NAME } from '@/lib/contract/catalog'
import type { ChatTool } from '@/lib/providers/types'

/**
 * Build a ChatTool array for the given authorized tool names.
 * Replaces the deleted lib/retrieve/tool_catalogue.buildChatToolsFromNames().
 *
 * Looks up each name in CONTRACT_CATALOG_BY_NAME (the contract registry).
 * Names not found in the catalog are silently skipped (graceful — unknown
 * tool names are a planner error, not a catalogue error).
 */
export function buildChatToolsFromNames(names: string[]): ChatTool[] {
  const tools: ChatTool[] = []
  for (const name of names) {
    const entry = CONTRACT_CATALOG_BY_NAME[name]
    if (!entry) continue
    tools.push({
      name: entry.canonical_name,
      description: entry.description,
      inputSchema: entry.json_schema as Record<string, unknown>,
    })
  }
  return tools
}

export type NormalizedSchema = {
  type: 'object'
  properties: Record<string, unknown>
  required?: string[]
  additionalProperties?: boolean
}

/**
 * Normalise a raw JSON schema into a guaranteed `{ type: 'object', properties: … }` shape.
 * Pure function — no I/O, no dependencies.
 *
 * - Accepts null/undefined (returns empty object schema).
 * - Preserves `required` and `additionalProperties` when present.
 * - Coerces any non-object `properties` to an empty object.
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

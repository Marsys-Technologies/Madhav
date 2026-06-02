/**
 * tool_catalogue.ts — CLEAN SLATE STUB
 *
 * All tools removed as part of legacy-teardown (feature/legacy-teardown).
 * buildChatToolsFromNames returns []; normalizeInputSchema preserved.
 * Rebuild per layer during the Layer-0 → Layer-3 arc.
 */

// Re-export ChatTool from providers/types so run_adapter_dispatch.ts and
// provider adapters share the same structural type for their tools arrays.
export type { ChatTool } from '@/lib/providers/types'
import type { ChatTool } from '@/lib/providers/types'

export type NormalizedSchema = {
  type: 'object'
  properties: Record<string, unknown>
  required?: string[]
  additionalProperties?: boolean
}

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

export function buildChatToolsFromNames(_names: string[]): ChatTool[] {
  return []
}

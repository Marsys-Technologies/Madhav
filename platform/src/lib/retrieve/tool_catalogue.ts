/**
 * tool_catalogue.ts — Tool Catalogue (Brahma delta build 2026-06-03)
 *
 * Rebuilding from clean-slate stub. Wires read_classical_text as the first
 * entry. When the Layer-0 → Layer-3 arc adds further tools, append to
 * CATALOGUE below.
 *
 * buildChatToolsFromNames returns ChatTool[] filtered from contract registry by name.
 * Unknown names are silently excluded (no throw).
 */

// Re-export ChatTool from providers/types so run_adapter_dispatch.ts and
// provider adapters share the same structural type for their tools arrays.
export type { ChatTool } from '@/lib/providers/types'
import type { ChatTool } from '@/lib/providers/types'
import { getContractNames, getContract } from '@/lib/contract/registry'
import { zodToJsonSchema } from '@/lib/contract/json_schema'

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

/**
 * Returns ChatTool descriptors for the requested canonical_names.
 * Names not in the contract registry are excluded without error.
 */
export function buildChatToolsFromNames(names: string[]): ChatTool[] {
  return names
    .filter(n => getContractNames().includes(n))
    .map(n => {
      const contract = getContract(n)!
      const rawSchema = zodToJsonSchema(contract.input_schema)
      return {
        name: contract.canonical_name,
        description: contract.description,
        inputSchema: normalizeInputSchema(rawSchema as Record<string, unknown>),
      } satisfies ChatTool
    })
}

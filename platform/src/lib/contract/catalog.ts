/**
 * catalog.ts — GENERATED FROM registry.ts. DO NOT HAND-EDIT.
 *
 * Thin shape mirroring platform-mcp/src/tools/catalog.ts so both the portal
 * tool list and the MCP server tool registration can read from one place.
 * The contract module is the source of truth; this re-export shapes the data
 * for the catalog consumer.
 */

import { TOOL_CONTRACTS } from './registry'
import { zodToJsonSchema } from './json_schema'

export interface ContractCatalogEntry {
  canonical_name: string
  description: string
  json_schema: ReturnType<typeof zodToJsonSchema>
  role: string
  family: string
  data_dependency: string
  ayanamsha_role: string | null
  ayanamsha_id: string | null
  per_chart: boolean
  annotations: Record<string, unknown>
}

/**
 * CATALOG — derived from TOOL_CONTRACTS. Order = contract registration order.
 * Both portal and MCP catalogs build their advertised tool list from this.
 */
export const CONTRACT_CATALOG: ContractCatalogEntry[] = TOOL_CONTRACTS.map(c => ({
  canonical_name: c.canonical_name,
  description: c.description,
  json_schema: zodToJsonSchema(c.input_schema),
  role: c.role,
  family: c.family,
  data_dependency: c.data_dependency,
  ayanamsha_role: c.ayanamsha_role,
  ayanamsha_id: c.ayanamsha_id,
  per_chart: c.per_chart,
  annotations: { ...c.annotations },
}))

/** Map for O(1) lookup. */
export const CONTRACT_CATALOG_BY_NAME: Record<string, ContractCatalogEntry> = Object.fromEntries(
  CONTRACT_CATALOG.map(e => [e.canonical_name, e])
)

/** Names list — what both channels advertise. */
export const CONTRACT_TOOL_NAMES: string[] = CONTRACT_CATALOG.map(e => e.canonical_name)

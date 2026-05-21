/**
 * TypeScript types for capability_tool_registry + capability_asset_tool_bindings tables.
 * Mirrors migration 070_capability_tool_registry.sql.
 */

export type BindingSource = 'manifest' | 'override' | 'inferred'

export interface CapabilityToolRegistry {
  tool_name: string
  expose_to_planner: boolean
  description: string
  query_schema: Record<string, unknown> | null
  output_schema: Record<string, unknown> | null
  cost_weight: number | null
  linked_data_asset_ids: string[]
  created_at: string
  updated_at: string
}

export interface CapabilityAssetToolBinding {
  asset_canonical_id: string
  tool_name: string
  binding_source: BindingSource
  created_at: string
}

/** Seed input shape — what seed_tool_registry.ts reads from the manifest sources */
export interface ToolRegistrySeedRow {
  tool_name: string
  expose_to_planner: boolean
  description: string
  query_schema?: Record<string, unknown>
  output_schema?: Record<string, unknown>
  cost_weight?: number
  linked_data_asset_ids: string[]
  binding_source: BindingSource
}

/**
 * retrieval/registry/layers/L0_brahmagyan/asset_registry_all.ts
 *
 * Resource: marsys://resource/asset-registry/all
 * Returns the full asset_registry as a JSON snapshot.
 * Used by LLM clients to understand available build assets.
 *
 * L0FR Stream A — authored 2026-06-07
 * R-18 fix: handler previously ignored ALL args (signature was `handler(_args, _ctx)`) —
 * every caller (list_assets, catalog_assets_list) always got the full unfiltered 92-row
 * snapshot regardless of the layer/limit they passed. Now honors layer + limit + offset.
 *
 * W5 L8 (Retrieval Plane Elevation, "listCapabilities filters" / W-13): this is the
 * ONLY listCapabilities-shaped surface actually exposed to end users today — the
 * asset_registry DB table (build-asset DAG, ~92 rows), served by 5 near-identical MCP
 * tool names (list_assets, catalog_assets_list, catalog_assets_all, catalog_assets_l0,
 * asset_registry_l0). It is a DIFFERENT catalog from the in-process CapabilityDescriptor
 * registry (`getCatalog()` / `listCapabilities()` in registry/index.ts, ~118 tool/
 * resource/prompt entries): that registry's own `CapabilityFilter` (type/layer/
 * name_prefix/scope/archetype/traversal_level/tool_role) was already extensive and has
 * no MCP-exposed "list capabilities" tool of its own — it is consumed internally by
 * adapters/router only. Judgment call: extend the DB-backed catalog here (the surface
 * users actually call today), not a net-new MCP tool wrapping the in-process registry.
 *
 * New filter dimensions added here (previously only `layer` was filterable, and three
 * already-existing DB columns — asset_type, catalog_status, has_writer — were not even
 * selected into the response, so they could neither be inspected nor filtered on):
 *   - `asset_type`     'data' | 'service'      — family/domain-ish split (migration 202)
 *   - `catalog_status` 'CURRENT' | 'DRAFT'     — lifecycle/disposition state (migration 202)
 *   - `scope`          'global' | 'per_chart'  — existing column, now filterable
 *   - `is_active`      boolean                 — existing column, now filterable
 *   - `has_writer`     boolean                 — whether a WriterBase writer is registered (migration 342)
 * All filters are optional and AND-combined; omitting all of them returns the full,
 * unfiltered set exactly as before (backward compatible).
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

// asset_registry.layer stores the Sanskrit internal names (migration 167's CHECK constraint:
// 'brahmagyan','ganita','bodha','kala','phala','mimamsa'), but every caller's schema advertises
// the external L0..L5 shorthand ("Filter by layer: L0, L1, L2, etc."). Without this map, a
// caller passing "L0" (as documented) matched zero rows — a second silent no-op layered on top
// of the missing filter wiring itself.
const LAYER_ALIAS: Record<string, string> = {
  L0: 'brahmagyan', L1: 'ganita', L2: 'bodha', L3: 'kala', L4: 'phala', L5: 'mimamsa',
  brahmagyan: 'brahmagyan', ganita: 'ganita', bodha: 'bodha', kala: 'kala', phala: 'phala', mimamsa: 'mimamsa',
}
function resolveLayer(layer: string): string {
  return LAYER_ALIAS[layer] ?? LAYER_ALIAS[layer.toUpperCase()] ?? layer
}

function coerceBool(v: unknown): boolean | undefined {
  if (v === undefined || v === null) return undefined
  if (typeof v === 'boolean') return v
  if (v === 'true') return true
  if (v === 'false') return false
  return undefined
}

export const assetRegistryAllCapability: CapabilityDescriptor = {
  uri: 'marsys://resource/asset-registry/all',
  type: 'resource',
  layer: 'L0',
  name: 'asset_registry_all',
  description:
    'Full asset_registry snapshot: all build assets across all layers (L0–L5). ' +
    'Includes asset_id, layer, sanskrit/english names, target_floor, scope, is_active, ' +
    'asset_type, catalog_status, has_writer. ' +
    'Use to understand available data assets before planning retrieval. ' +
    'Optional filters (AND-combined; all omittable): `layer` (L0..L5), ' +
    '`asset_type` (data|service), `catalog_status` (CURRENT|DRAFT), ' +
    '`scope` (global|per_chart), `is_active` (boolean), `has_writer` (boolean). ' +
    '`limit`/`offset` paginate.',
  input_schema: {
    layer:          { type: 'string', description: 'Filter to one layer (e.g. "L0", "L1", ..., "L5"). Omit for all.' },
    asset_type:     { type: 'string', description: 'Filter to "data" or "service" assets. Omit for both.' },
    catalog_status: { type: 'string', description: 'Filter to "CURRENT" or "DRAFT" catalog_status. Omit for both.' },
    scope:          { type: 'string', description: 'Filter to "global" or "per_chart" scope. Omit for both.' },
    is_active:      { type: 'boolean', description: 'Filter to active (true) or inactive (false) assets. Omit for both.' },
    has_writer:     { type: 'boolean', description: 'Filter to assets with (true) or without (false) a registered WriterBase writer. Omit for both.' },
    limit:  { type: 'number', description: 'Max rows to return (default: all; max: 500).' },
    offset: { type: 'number', description: 'Pagination offset (default: 0).' },
  },
  scope: 'global',
  archetype: 'orientation_digest',
  traversal_level: 'L-ORIENT',
  tool_role: 'umbrella',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: {
      cost_class: 'cheap',
    },
    bulk_context: {
      pre_fetch_priority: 90,
      always_include: true,
    },
  },
  async handler(args, _ctx) {
    try {
      const layerRaw = args?.['layer'] as string | undefined
      const layer  = layerRaw ? resolveLayer(layerRaw) : undefined
      const limit  = args?.['limit'] != null ? Math.min(Number(args['limit']), 500) : undefined
      const offset = Number(args?.['offset'] ?? 0)

      const assetTypeRaw = args?.['asset_type'] as string | undefined
      const assetType = assetTypeRaw ? assetTypeRaw.toLowerCase() : undefined

      const catalogStatusRaw = args?.['catalog_status'] as string | undefined
      const catalogStatus = catalogStatusRaw ? catalogStatusRaw.toUpperCase() : undefined

      const scopeRaw = args?.['scope'] as string | undefined
      const scopeFilter = scopeRaw ? scopeRaw.toLowerCase() : undefined

      const isActive = coerceBool(args?.['is_active'])
      const hasWriter = coerceBool(args?.['has_writer'])

      const conds: string[] = []
      const params: unknown[] = []
      if (layer) {
        conds.push(`layer = $${params.length + 1}`)
        params.push(layer)
      }
      if (assetType) {
        conds.push(`asset_type = $${params.length + 1}`)
        params.push(assetType)
      }
      if (catalogStatus) {
        conds.push(`catalog_status = $${params.length + 1}`)
        params.push(catalogStatus)
      }
      if (scopeFilter) {
        conds.push(`scope = $${params.length + 1}`)
        params.push(scopeFilter)
      }
      if (isActive !== undefined) {
        conds.push(`is_active = $${params.length + 1}`)
        params.push(isActive)
      }
      if (hasWriter !== undefined) {
        conds.push(`has_writer = $${params.length + 1}`)
        params.push(hasWriter)
      }
      const where = conds.length > 0 ? `WHERE ${conds.join(' AND ')}` : ''

      // Total count over the filter (pre-pagination), so callers can tell "returned N of TOTAL".
      const countResult = await query<{ total: string }>(
        `SELECT COUNT(*)::text AS total FROM asset_registry ${where}`,
        params,
      )
      const total = Number(countResult.rows?.[0]?.total ?? 0)

      let sql = `
        SELECT asset_id, layer, sanskrit_name, english_name,
               target_table, target_floor, scope, is_active,
               asset_type, catalog_status, has_writer,
               expected_volume_formula, count_sql, depends_on
        FROM asset_registry
        ${where}
        ORDER BY layer, asset_id
      `
      const queryParams = [...params]
      if (limit != null) {
        queryParams.push(limit, offset)
        sql += ` LIMIT $${queryParams.length - 1} OFFSET $${queryParams.length}`
      } else if (offset > 0) {
        queryParams.push(offset)
        sql += ` OFFSET $${queryParams.length}`
      }

      const result = await query<Record<string, unknown>>(sql, queryParams)
      return {
        content: {
          assets: result.rows ?? [],
          total,
          returned: result.rows?.length ?? 0,
          filters: {
            layer: layer ?? null, layer_requested: layerRaw ?? null,
            asset_type: assetType ?? null,
            catalog_status: catalogStatus ?? null,
            scope: scopeFilter ?? null,
            is_active: isActive ?? null,
            has_writer: hasWriter ?? null,
            limit: limit ?? null, offset,
          },
          snapshot_at: new Date().toISOString(),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}

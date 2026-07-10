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

export const assetRegistryAllCapability: CapabilityDescriptor = {
  uri: 'marsys://resource/asset-registry/all',
  type: 'resource',
  layer: 'L0',
  name: 'asset_registry_all',
  description:
    'Full asset_registry snapshot: all build assets across all layers (L0–L5). ' +
    'Includes asset_id, layer, sanskrit/english names, target_floor, scope, is_active. ' +
    'Use to understand available data assets before planning retrieval. ' +
    'Optional `layer` filters to one layer (L0..L5); `limit`/`offset` paginate.',
  input_schema: {
    layer:  { type: 'string', description: 'Filter to one layer (e.g. "L0", "L1", ..., "L5"). Omit for all.' },
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

      const conds: string[] = []
      const params: unknown[] = []
      if (layer) {
        conds.push(`layer = $${params.length + 1}`)
        params.push(layer)
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
          filters: { layer: layer ?? null, layer_requested: layerRaw ?? null, limit: limit ?? null, offset },
          snapshot_at: new Date().toISOString(),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}

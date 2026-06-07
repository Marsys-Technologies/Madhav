/**
 * retrieval/registry/layers/L0_brahmagyan/asset_registry_all.ts
 *
 * Resource: marsys://resource/asset-registry/all
 * Returns the full asset_registry as a JSON snapshot.
 * Used by LLM clients to understand available build assets.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import type { ResourceCapability } from '../../types'

export const assetRegistryAllCapability: ResourceCapability = {
  uri: 'marsys://resource/asset-registry/all',
  primitive_type: 'resource',
  layer: 'L0',
  name: 'asset_registry_all',
  description:
    'Full asset_registry snapshot: all build assets across all layers (L0–L5). ' +
    'Includes asset_id, layer, sanskrit/english names, target_floor, scope, is_active. ' +
    'Use to understand available data assets before planning retrieval.',
  mime_type: 'application/json',
  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      always_prefetch: true,
      latency_ms_p50: 25,
    },
    bulk_context: {
      pre_fetch_priority: 90,
      always_include: true,
      result_size_kb_p50: 4,
    },
    result_max_kb: 16,
  },
  async loader(ctx) {
    const db = ctx?.db
    if (!db) throw new Error('asset_registry_all: no DB connection in context')

    const rows = await db.query(
      `SELECT asset_id, layer, sanskrit_name, english_name,
              target_table, target_floor, scope, is_active,
              expected_volume_formula, count_sql, depends_on
       FROM asset_registry
       ORDER BY layer, asset_id`,
      [],
    )

    return {
      assets: rows ?? [],
      total: rows?.length ?? 0,
      snapshot_at: new Date().toISOString(),
    }
  },
}

/**
 * retrieval/registry/layers/L0_brahmagyan/asset_registry_l0.ts
 *
 * Resource: marsys://resource/asset-registry/L0
 * Returns only the L0 (brahmagyan) slice of the asset_registry.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import type { ResourceCapability } from '../../types'

export const assetRegistryL0Capability: ResourceCapability = {
  uri: 'marsys://resource/asset-registry/L0',
  primitive_type: 'resource',
  layer: 'L0',
  name: 'asset_registry_l0',
  description:
    'L0 Brahmagyan asset_registry slice: all brahmagyan layer assets ' +
    '(shastra texts, sutravali rules, ontology, remedies, ephemeris, etc.). ' +
    'Includes current row counts and target_floor for each asset.',
  mime_type: 'application/json',
  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      always_prefetch: true,
      latency_ms_p50: 20,
    },
    bulk_context: {
      pre_fetch_priority: 95,
      always_include: true,
      result_size_kb_p50: 2,
    },
    result_max_kb: 8,
  },
  async loader(ctx) {
    const db = ctx?.db
    if (!db) throw new Error('asset_registry_l0: no DB connection in context')

    const rows = await db.query(
      `SELECT ar.asset_id, ar.layer, ar.sanskrit_name, ar.english_name,
              ar.target_table, ar.target_floor, ar.scope, ar.is_active,
              ar.expected_volume_formula, ar.count_sql, ar.depends_on,
              -- Live count via count_sql if available
              CASE
                WHEN ar.count_sql IS NOT NULL
                THEN NULL  -- computed client-side for safety
                ELSE NULL
              END AS current_count
       FROM asset_registry ar
       WHERE ar.layer = 'brahmagyan'
       ORDER BY ar.asset_id`,
      [],
    )

    return {
      layer: 'L0',
      assets: rows ?? [],
      total: rows?.length ?? 0,
      snapshot_at: new Date().toISOString(),
    }
  },
}

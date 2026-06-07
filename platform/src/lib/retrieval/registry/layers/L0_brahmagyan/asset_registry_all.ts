/**
 * retrieval/registry/layers/L0_brahmagyan/asset_registry_all.ts
 *
 * Resource: marsys://resource/asset-registry/all
 * Returns the full asset_registry as a JSON snapshot.
 * Used by LLM clients to understand available build assets.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const assetRegistryAllCapability: CapabilityDescriptor = {
  uri: 'marsys://resource/asset-registry/all',
  type: 'resource',
  layer: 'L0',
  name: 'asset_registry_all',
  description:
    'Full asset_registry snapshot: all build assets across all layers (L0–L5). ' +
    'Includes asset_id, layer, sanskrit/english names, target_floor, scope, is_active. ' +
    'Use to understand available data assets before planning retrieval.',
  llm_hints: {
    agentic: {
      cost_class: 'cheap',
    },
    bulk_context: {
      pre_fetch_priority: 90,
      always_include: true,
    },
  },
  async handler(_args, _ctx) {
    try {
      const result = await query<Record<string, unknown>>(
        `SELECT asset_id, layer, sanskrit_name, english_name,
                target_table, target_floor, scope, is_active,
                expected_volume_formula, count_sql, depends_on
         FROM asset_registry
         ORDER BY layer, asset_id`,
        [],
      )
      return {
        content: {
          assets: result.rows ?? [],
          total: result.rows?.length ?? 0,
          snapshot_at: new Date().toISOString(),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}

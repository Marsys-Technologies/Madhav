/**
 * retrieval/registry/layers/L0_brahmagyan/asset_registry_l0.ts
 *
 * Resource: marsys://resource/asset-registry/L0
 * Returns only the L0 (brahmagyan) slice of the asset_registry.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const assetRegistryL0Capability: CapabilityDescriptor = {
  uri: 'marsys://resource/asset-registry/L0',
  type: 'resource',
  layer: 'L0',
  name: 'asset_registry_l0',
  description:
    'L0 Brahmagyan asset_registry slice: all brahmagyan layer assets ' +
    '(shastra texts, sutravali rules, ontology, remedies, ephemeris, etc.). ' +
    'Includes current row counts and target_floor for each asset.',
  llm_hints: {
    agentic: {
      cost_class: 'cheap',
    },
    bulk_context: {
      pre_fetch_priority: 95,
      always_include: true,
    },
  },
  async handler(_args, _ctx) {
    try {
      const result = await query<Record<string, unknown>>(
        `SELECT ar.asset_id, ar.layer, ar.sanskrit_name, ar.english_name,
                ar.target_table, ar.target_floor, ar.scope, ar.is_active,
                ar.expected_volume_formula, ar.count_sql, ar.depends_on
         FROM asset_registry ar
         WHERE ar.layer = 'brahmagyan'
         ORDER BY ar.asset_id`,
        [],
      )
      return {
        content: {
          layer: 'L0',
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

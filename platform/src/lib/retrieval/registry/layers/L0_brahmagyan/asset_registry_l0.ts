/**
 * retrieval/registry/layers/L0_brahmagyan/asset_registry_l0.ts
 *
 * Resource: marsys://resource/asset-registry/L0
 * Returns only the L0 (brahmagyan) slice of the asset_registry.
 *
 * L0FR Stream A — authored 2026-06-07
 * R-18 fix: handler previously ignored ALL args (signature was `handler(_args, _ctx)`) —
 * catalog_assets_l0's advertised `limit` param was silently dropped. Now honors limit + offset.
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
    'Includes current row counts and target_floor for each asset. ' +
    '`limit`/`offset` paginate.',
  input_schema: {
    limit:  { type: 'number', description: 'Max rows to return (default: all; max: 500).' },
    offset: { type: 'number', description: 'Pagination offset (default: 0).' },
  },
  scope: 'global',
  archetype: 'orientation_digest',
  traversal_level: 'L-OVERVIEW',
  tool_role: 'umbrella',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: {
      cost_class: 'cheap',
    },
    bulk_context: {
      pre_fetch_priority: 95,
      always_include: true,
    },
  },
  async handler(args, _ctx) {
    try {
      const limit  = args?.['limit'] != null ? Math.min(Number(args['limit']), 500) : undefined
      const offset = Number(args?.['offset'] ?? 0)

      const countResult = await query<{ total: string }>(
        `SELECT COUNT(*)::text AS total FROM asset_registry WHERE layer = 'brahmagyan'`,
        [],
      )
      const total = Number(countResult.rows?.[0]?.total ?? 0)

      const params: unknown[] = []
      let sql = `
        SELECT ar.asset_id, ar.layer, ar.sanskrit_name, ar.english_name,
               ar.target_table, ar.target_floor, ar.scope, ar.is_active,
               ar.expected_volume_formula, ar.count_sql, ar.depends_on
        FROM asset_registry ar
        WHERE ar.layer = 'brahmagyan'
        ORDER BY ar.asset_id
      `
      if (limit != null) {
        params.push(limit, offset)
        sql += ` LIMIT $${params.length - 1} OFFSET $${params.length}`
      } else if (offset > 0) {
        params.push(offset)
        sql += ` OFFSET $${params.length}`
      }

      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          layer: 'L0',
          assets: result.rows ?? [],
          total,
          returned: result.rows?.length ?? 0,
          filters: { limit: limit ?? null, offset },
          snapshot_at: new Date().toISOString(),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}

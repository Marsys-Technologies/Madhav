/**
 * retrieval/registry/layers/L0_brahmagyan/asset_registry_l0.ts
 *
 * Resource: marsys://resource/asset-registry/L0
 * Returns only the L0 (brahmagyan) slice of the asset_registry.
 *
 * L0FR Stream A — authored 2026-06-07
 * R-18 fix: handler previously ignored ALL args (signature was `handler(_args, _ctx)`) —
 * catalog_assets_l0's advertised `limit` param was silently dropped. Now honors limit + offset.
 *
 * W5 L8 ("listCapabilities filters" / W-13): same additional filter dimensions as the
 * sibling `marsys://resource/asset-registry/all` (asset_registry_all.ts) — asset_type,
 * catalog_status, scope, is_active, has_writer — AND-combined with the fixed
 * layer = 'brahmagyan' clause. Omitting all of them returns the full L0 slice unchanged.
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

function coerceBool(v: unknown): boolean | undefined {
  if (v === undefined || v === null) return undefined
  if (typeof v === 'boolean') return v
  if (v === 'true') return true
  if (v === 'false') return false
  return undefined
}

export const assetRegistryL0Capability: CapabilityDescriptor = {
  uri: 'marsys://resource/asset-registry/L0',
  type: 'resource',
  layer: 'L0',
  name: 'asset_registry_l0',
  description:
    'L0 Brahmagyan asset_registry slice: all brahmagyan layer assets ' +
    '(shastra texts, sutravali rules, ontology, remedies, ephemeris, etc.). ' +
    'Includes current row counts and target_floor for each asset. ' +
    'Optional filters (AND-combined; all omittable): `asset_type` (data|service), ' +
    '`catalog_status` (CURRENT|DRAFT), `scope` (global|per_chart), `is_active` (boolean), ' +
    '`has_writer` (boolean). `limit`/`offset` paginate.',
  input_schema: {
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

      const assetTypeRaw = args?.['asset_type'] as string | undefined
      const assetType = assetTypeRaw ? assetTypeRaw.toLowerCase() : undefined

      const catalogStatusRaw = args?.['catalog_status'] as string | undefined
      const catalogStatus = catalogStatusRaw ? catalogStatusRaw.toUpperCase() : undefined

      const scopeRaw = args?.['scope'] as string | undefined
      const scopeFilter = scopeRaw ? scopeRaw.toLowerCase() : undefined

      const isActive = coerceBool(args?.['is_active'])
      const hasWriter = coerceBool(args?.['has_writer'])

      const conds: string[] = [`ar.layer = 'brahmagyan'`]
      const params: unknown[] = []
      if (assetType) {
        conds.push(`ar.asset_type = $${params.length + 1}`)
        params.push(assetType)
      }
      if (catalogStatus) {
        conds.push(`ar.catalog_status = $${params.length + 1}`)
        params.push(catalogStatus)
      }
      if (scopeFilter) {
        conds.push(`ar.scope = $${params.length + 1}`)
        params.push(scopeFilter)
      }
      if (isActive !== undefined) {
        conds.push(`ar.is_active = $${params.length + 1}`)
        params.push(isActive)
      }
      if (hasWriter !== undefined) {
        conds.push(`ar.has_writer = $${params.length + 1}`)
        params.push(hasWriter)
      }
      const where = `WHERE ${conds.join(' AND ')}`

      const countResult = await query<{ total: string }>(
        `SELECT COUNT(*)::text AS total FROM asset_registry ar ${where}`,
        params,
      )
      const total = Number(countResult.rows?.[0]?.total ?? 0)

      const queryParams = [...params]
      let sql = `
        SELECT ar.asset_id, ar.layer, ar.sanskrit_name, ar.english_name,
               ar.target_table, ar.target_floor, ar.scope, ar.is_active,
               ar.asset_type, ar.catalog_status, ar.has_writer,
               ar.expected_volume_formula, ar.count_sql, ar.depends_on
        FROM asset_registry ar
        ${where}
        ORDER BY ar.asset_id
      `
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
          layer: 'L0',
          assets: result.rows ?? [],
          total,
          returned: result.rows?.length ?? 0,
          filters: {
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

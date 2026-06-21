import { NextResponse } from 'next/server'
import { query } from '@/lib/db/client'

export const revalidate = 60

export interface AssetRow {
  asset_id: string
  layer: string
  sort_order: number
  sanskrit_name: string
  english_name: string
  english_description: string
  storage_type: string
  target_table: string | null
  count_sql: string | null
  size_sql: string | null
  target_floor: number | null
  expected_volume_formula: string | null
  expected_volume_inputs: Record<string, unknown> | null
  volume_explanation: string | null
  depends_on: string[]
  scope: string
  is_active: boolean
  estimated_seconds: number | null
  created_at: string
  // Migration 202+ service-support fields
  asset_type: 'data' | 'service' | null
  layer_name: string | null
  layer_index: string | null
  provides_apis: Record<string, unknown>[] | null
  health_probe: Record<string, unknown> | null
  catalog_status: 'CURRENT' | 'DRAFT' | 'RETIRED' | null
  // Migration 242+ L3 Kāla service-asset-type fields
  asset_kind: 'data' | 'service' | 'artifact' | null
  service_health: 'healthy' | 'degraded' | 'unhealthy' | 'unknown' | null
  last_invoked_at: string | null
  last_selftest_at: string | null
  selftest_detail: Record<string, unknown> | null
}

export async function GET() {
  try {
    const result = await query<AssetRow>(`
      SELECT
        asset_id, layer, sort_order, sanskrit_name, english_name,
        english_description, storage_type, target_table, count_sql,
        size_sql, target_floor, expected_volume_formula,
        expected_volume_inputs, volume_explanation, depends_on,
        scope, is_active, estimated_seconds, created_at,
        asset_type, layer_name, layer_index, provides_apis, health_probe, catalog_status,
        asset_kind, service_health, last_invoked_at, last_selftest_at, selftest_detail,
        asset_kind, service_health, last_invoked_at, last_selftest_at, selftest_detail
      FROM asset_registry
      ORDER BY
        CASE layer
          WHEN 'brahmagyan' THEN 0
          WHEN 'ganita'     THEN 1
          WHEN 'bodha'      THEN 2
          WHEN 'kala'       THEN 3
          WHEN 'phala'      THEN 4
          WHEN 'mimamsa'    THEN 5
          ELSE 99
        END,
        sort_order
    `)

    const response = NextResponse.json({
      data: { assets: result.rows },
      fetched_at: new Date().toISOString(),
      stale_after_seconds: 60,
      errors: [],
    })

    response.headers.set('Cache-Control', 'public, s-maxage=60, stale-while-revalidate=30')
    return response
  } catch (err) {
    console.error('[cockpit/registry] db error', err)
    return NextResponse.json(
      {
        data: { assets: [] },
        fetched_at: new Date().toISOString(),
        stale_after_seconds: 0,
        errors: [(err as Error).message ?? 'unknown error'],
      },
      { status: 500 }
    )
  }
}

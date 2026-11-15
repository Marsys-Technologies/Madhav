import 'server-only'
import { query } from '@/lib/db/client'
import type { AtlasAsset } from '@/components/build/AtlasView'

/** Build catalog data; callers retain super-admin admission before the read. */
export function readAtlasAssets() {
  return query<AtlasAsset>(`
    SELECT
      asset_id, layer, sort_order, sanskrit_name, english_name,
      english_description, storage_type, target_table, count_sql,
      size_sql, target_floor, expected_volume_formula,
      expected_volume_inputs, volume_explanation, depends_on,
      scope, is_active, estimated_seconds, created_at,
      asset_type, layer_name, layer_index, provides_apis, health_probe,
      catalog_status, clear_tables
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
}

import { query } from '@/lib/db/client'
import { AtlasView, type AtlasAsset } from '@/components/build/AtlasView'

export const dynamic = 'force-dynamic'

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

export default async function AtlasPage() {
  const result = await query<AtlasAsset>(`
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

  return (
    <main className="mx-auto max-w-7xl px-4 py-6">
      <div className="mb-6 flex items-baseline justify-between">
        <h1 className="bt-display">Asset Atlas</h1>
        <p className="bt-body text-muted-foreground">{result.rows.length} assets across 6 layers</p>
      </div>
      <AtlasView assets={result.rows} defaultChartId={NATIVE_CHART_ID} />
    </main>
  )
}

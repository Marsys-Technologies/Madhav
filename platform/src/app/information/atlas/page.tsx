import { readAtlasAssets } from '@/lib/build/atlasPageData'
import { AtlasView } from '@/components/build/AtlasView'
import { requireSuperAdminPage } from '@/lib/auth/super-admin-page-guard'

export const dynamic = 'force-dynamic'

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

export default async function AtlasPage() {
  // Guard INSIDE the page: it reads asset_registry (count_sql / size_sql /
  // clear_tables), and the layout guard alone can be skipped by a crafted RSC
  // request (SS N-373).
  await requireSuperAdminPage()
  const result = await readAtlasAssets()

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

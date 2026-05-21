import 'server-only'
import { NextResponse } from 'next/server'
import { guardPerformanceRoute } from '../_guard'
import { getAssetCatalog } from '@/lib/performance/asset_health'

export async function GET(): Promise<NextResponse> {
  const auth = await guardPerformanceRoute()
  if (auth instanceof NextResponse) return auth

  try {
    const catalog = getAssetCatalog()
    return NextResponse.json(catalog)
  } catch (err) {
    console.error('[api/performance/assets] failed', err)
    return NextResponse.json({ error: 'asset_catalog_failed' }, { status: 500 })
  }
}

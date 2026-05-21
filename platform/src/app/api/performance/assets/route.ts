import { NextResponse } from 'next/server'
import { guardPerformanceRoute } from '../_guard'
import { loadManifest } from '@/lib/bundle/manifest_reader'
import { computeHealthBadge, computeReachability } from '@/lib/performance/asset_health'
import type { AssetEntry } from '@/lib/bundle/types'
import type { AssetCatalogResponse } from '@/lib/performance/asset_health'

export async function GET(request: Request): Promise<NextResponse> {
  void request
  const auth = await guardPerformanceRoute()
  if (auth instanceof NextResponse) return auth

  try {
    const manifest = await loadManifest()

    // Build asset_id → bound_tool_names index from RETRIEVAL_TOOL_* entries.
    const assetToolIndex = new Map<string, string[]>()
    for (const entry of manifest.entries) {
      const toolName = (entry as AssetEntry & { tool_name?: string }).tool_name
      const linked = (entry as AssetEntry & { linked_data_asset_ids?: string[] }).linked_data_asset_ids ?? []
      if (toolName && linked.length > 0) {
        for (const assetId of linked) {
          const existing = assetToolIndex.get(assetId) ?? []
          if (!existing.includes(toolName)) existing.push(toolName)
          assetToolIndex.set(assetId, existing)
        }
      }
    }

    const entries = manifest.entries
      .filter(e => !(e as AssetEntry & { tool_name?: string }).tool_name)
      .map(entry => {
        const bound_tools = assetToolIndex.get(entry.canonical_id) ?? []
        const enriched = { ...entry, bound_tools }
        return {
          ...enriched,
          health: computeHealthBadge(entry),
          reachability: computeReachability(enriched),
        }
      })

    const body: AssetCatalogResponse = {
      fingerprint: manifest.fingerprint,
      total: entries.length,
      entries,
    }

    return NextResponse.json(body, {
      headers: { 'Cache-Control': 'private, max-age=300, stale-while-revalidate=60' },
    })
  } catch (err) {
    console.error('[api/performance/assets] failed', err)
    return NextResponse.json({ error: 'asset_catalog_failed' }, { status: 500 })
  }
}

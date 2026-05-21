import * as fs from 'fs'
import * as path from 'path'
import { getAssetCatalog } from './asset_health'

export interface FreshnessReport {
  stale_assets: StaleAsset[]
  aging_assets: AgingAsset[]
  total_scanned: number
}

export interface StaleAsset {
  canonical_id: string
  status: string
  path: string
  layer?: string
}

export interface AgingAsset {
  canonical_id: string
  last_updated: string
  days_since_update: number
  path: string
}

const STALE_STATUSES = new Set(['SUPERSEDED', 'DEAD_DATA'])

// Raw manifest entry shape — includes all fields including optional last_updated
interface RawManifestEntry {
  canonical_id?: string
  tool_name?: string
  path?: string
  layer?: string
  status?: string
  last_updated?: string
  [key: string]: unknown
}

function readRawEntries(): RawManifestEntry[] {
  const manifestPath = path.join(process.cwd(), '00_ARCHITECTURE/CAPABILITY_MANIFEST.json')
  const raw = fs.readFileSync(manifestPath, 'utf-8')
  const manifest = JSON.parse(raw) as { entries: RawManifestEntry[] }
  return manifest.entries
}

export function getFreshnessReport(agingThresholdDays = 90): FreshnessReport {
  const rawEntries = readRawEntries()
  // Use getAssetCatalog only to get totalCount
  const catalog = getAssetCatalog()
  const now = Date.now()
  const stale: StaleAsset[] = []
  const aging: AgingAsset[] = []

  for (const entry of rawEntries) {
    const id = entry.canonical_id ?? entry.tool_name ?? 'unknown'
    const entryPath = entry.path ?? ''
    const status = entry.status

    // Stale check: status is SUPERSEDED or DEAD_DATA
    if (status != null && STALE_STATUSES.has(status)) {
      stale.push({
        canonical_id: id,
        status,
        path: entryPath,
        layer: entry.layer,
      })
    }

    // Aging check: last_updated field present and older than threshold
    const lu = entry.last_updated
    if (lu) {
      const ms = Date.parse(lu)
      if (!isNaN(ms)) {
        const days = Math.floor((now - ms) / 86_400_000)
        if (days > agingThresholdDays) {
          aging.push({
            canonical_id: id,
            last_updated: lu,
            days_since_update: days,
            path: entryPath,
          })
        }
      }
    }
  }

  return {
    stale_assets: stale,
    aging_assets: aging,
    total_scanned: catalog.totalCount,
  }
}

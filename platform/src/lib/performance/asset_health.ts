import * as fs from 'fs'
import * as path from 'path'

export type HealthBadge = 'green' | 'yellow' | 'red' | 'gray'

export interface AssetEntry {
  canonical_id?: string
  path: string
  layer?: string
  status?: string
  version?: string
  fingerprint?: string
  expose_to_chat?: boolean
  expose_to_planner?: boolean
  tool_name?: string
  tool_description?: string
  description?: string
  representations?: string[]
  health: HealthBadge
}

export interface AssetCatalog {
  byLayer: Record<string, AssetEntry[]>
  totalCount: number
  reachableCount: number
}

function computeHealth(entry: { status?: string }): HealthBadge {
  const s = entry.status
  if (!s) return 'gray'
  if (s === 'CURRENT') return 'green'
  if (s === 'LIVING') return 'yellow'
  if (s === 'SUPERSEDED' || s === 'DEAD_DATA' || s === 'GOVERNANCE_CLOSED') return 'red'
  return 'gray'
}

export function getAssetCatalog(): AssetCatalog {
  const manifestPath = path.join(process.cwd(), '00_ARCHITECTURE/CAPABILITY_MANIFEST.json')
  const raw = fs.readFileSync(manifestPath, 'utf-8')
  const manifest = JSON.parse(raw) as { entries: Record<string, unknown>[] }

  const entries: AssetEntry[] = manifest.entries.map((e) => {
    const raw = e as {
      canonical_id?: string
      path?: string
      layer?: string
      status?: string
      version?: string
      fingerprint?: string
      expose_to_chat?: boolean
      expose_to_planner?: boolean
      tool_name?: string
      tool_description?: string
      description?: string
      representations?: string[]
    }
    return {
      canonical_id: raw.canonical_id,
      path: raw.path ?? '',
      layer: raw.layer,
      status: raw.status,
      version: raw.version,
      fingerprint: raw.fingerprint,
      expose_to_chat: raw.expose_to_chat,
      expose_to_planner: raw.expose_to_planner,
      tool_name: raw.tool_name,
      tool_description: raw.tool_description,
      description: raw.description,
      representations: raw.representations,
      health: computeHealth(raw),
    }
  })

  const byLayer: Record<string, AssetEntry[]> = {}
  for (const entry of entries) {
    const layer = entry.layer ?? 'Other'
    if (!byLayer[layer]) byLayer[layer] = []
    byLayer[layer].push(entry)
  }

  const totalCount = entries.length
  const reachableCount = entries.filter((e) => !!e.tool_name).length

  return { byLayer, totalCount, reachableCount }
}

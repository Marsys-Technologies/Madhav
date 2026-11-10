/**
 * override_merger.ts — merges curated override fields from manifest_overrides.yaml
 * into auto-derived AssetEntry[]
 */

import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import yaml from 'js-yaml'
import { createHash } from 'node:crypto'
import type { AssetEntry, LayerEnum, StatusEnum } from './auto_deriver'

// Repo root is four levels up from platform/src/scripts/manifest/
// __dirname = .../Madhav/platform/src/scripts/manifest
// 4 up     = .../Madhav (repo root)
const REPO_ROOT = join(__dirname, '..', '..', '..', '..')
const OVERRIDES_PATH = join(REPO_ROOT, '00_ARCHITECTURE', 'manifest_overrides.yaml')

interface OverrideEntry {
  /** Optional substring match against entry.path when canonical_id doesn't match directly */
  path_pattern?: string
  preferred_for?: string[]
  cost_weight?: number
  always_required?: boolean
}

interface AdditionalEntry {
  path: string
  canonical_id: string
  version: string
  layer: LayerEnum
  expose_to_chat: boolean
  native_id?: string
  category?: string
}

interface OverridesFile {
  overrides?: Record<string, OverrideEntry>
  additional_entries?: AdditionalEntry[]
}

/**
 * Load and parse the manifest_overrides.yaml file.
 */
function loadOverridesFile(): OverridesFile {
  let content: string
  try {
    content = readFileSync(OVERRIDES_PATH, 'utf-8')
  } catch (err) {
    console.warn(`[override_merger] Could not read overrides file: ${err}`)
    return {}
  }

  try {
    return (yaml.load(content) as OverridesFile) ?? {}
  } catch (err) {
    console.warn(`[override_merger] Failed to parse overrides YAML: ${err}`)
    return {}
  }
}

/**
 * Convert an additional_entries item into a full AssetEntry.
 * Uses a deterministic fingerprint based on the entry's canonical_id + path.
 */
function additionalEntryToAsset(item: AdditionalEntry): AssetEntry {
  const fingerprint = createHash('sha256')
    .update(`${item.canonical_id}:${item.path}`)
    .digest('hex')
  return {
    canonical_id: item.canonical_id,
    path: item.path,
    version: item.version,
    status: 'CURRENT' as StatusEnum,
    layer: item.layer,
    expose_to_chat: item.expose_to_chat ?? false,
    representations: ['file'],
    interface_version: '1.0',
    fingerprint,
    native_id: item.native_id ?? 'abhisek',
  }
}

/**
 * Find a matching override for an entry.
 * First tries exact canonical_id match, then falls back to path_pattern substring match.
 */
function findOverride(
  entry: AssetEntry,
  overrides: Record<string, OverrideEntry>
): OverrideEntry | undefined {
  // 1. Exact canonical_id match
  if (overrides[entry.canonical_id]) {
    return overrides[entry.canonical_id]
  }

  // 2. path_pattern substring match (for files whose frontmatter canonical_id
  //    differs from the short override key)
  for (const override of Object.values(overrides)) {
    if (override.path_pattern && entry.path.includes(override.path_pattern)) {
      return override
    }
  }

  return undefined
}

/**
 * Merge curated override fields into each entry by canonical_id or path_pattern,
 * then append any additional_entries declared in manifest_overrides.yaml.
 */
export async function mergeOverrides(entries: AssetEntry[]): Promise<AssetEntry[]> {
  const file = loadOverridesFile()
  const overrides = file.overrides ?? {}

  const merged = entries.map(entry => {
    const override = findOverride(entry, overrides)
    if (!override) return entry

    const out: AssetEntry = { ...entry }

    if (Array.isArray(override.preferred_for) && override.preferred_for.length > 0) {
      out.preferred_for = override.preferred_for
    }
    if (typeof override.cost_weight === 'number') {
      out.cost_weight = override.cost_weight
    }
    if (typeof override.always_required === 'boolean') {
      out.always_required = override.always_required
    }

    return out
  })

  // Append additional_entries (JSON/JSONL files not discoverable by auto_deriver)
  const extras = (file.additional_entries ?? []).map(additionalEntryToAsset)
  if (extras.length > 0) {
    console.log(`[override_merger] Appending ${extras.length} additional_entries from manifest_overrides.yaml`)
  }

  return [...merged, ...extras]
}

/**
 * auto_deriver.ts — derives AssetEntry[] from filesystem + frontmatter
 * Phase 1A: informational only, does not replace FILE_REGISTRY or CANONICAL_ARTIFACTS
 */

import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, relative, extname, basename } from 'node:path'
import { createHash } from 'node:crypto'

// Repo root is four levels up from platform/src/scripts/manifest/
// __dirname = .../Madhav/platform/src/scripts/manifest
// 4 up     = .../Madhav (repo root)
const REPO_ROOT = join(__dirname, '..', '..', '..', '..')

const SCAN_DIRS = [
  '01_FACTS_LAYER',
  '025_HOLISTIC_SYNTHESIS',
  '03_DOMAIN_REPORTS',
  '035_DISCOVERY_LAYER',
  '06_LEARNING_LAYER',
]

// Files to skip
// README.md files are directory scaffolding, not corpus assets — they have no
// canonical_id frontmatter and would all derive to the same "README" id, causing
// silent byId collisions in the manifest (entry_count > byId.size).
const SKIP_FILENAMES = new Set(['CLAUDE.md', 'README.md'])
const SKIP_EXTENSIONS = new Set(['.csv'])
// Directory names to skip (anywhere in the tree)
const SKIP_DIRNAMES = new Set(['PROMPTS', 'responses', 'LEDGER', 'OBSERVATIONS', 'PARAMETER_UPDATES'])

export type LayerEnum = 'L1' | 'L2' | 'L2.5' | 'L3' | 'L3.5' | 'L4' | 'L5' | 'L6' | 'Foundation'
export type StatusEnum = 'CURRENT' | 'PREDECESSOR' | 'ARCHIVE' | 'SOURCE' | 'QUALITY'

export interface AssetEntry {
  canonical_id: string
  path: string
  version: string
  status: StatusEnum
  layer: LayerEnum
  expose_to_chat: boolean
  representations: string[]
  interface_version: string
  fingerprint: string
  native_id: string
  preferred_for?: string[]
  always_required?: boolean
  tool_binding?: string
  cost_weight?: number
  supplements_parent?: string
}

/**
 * Parse YAML frontmatter from a markdown file's content.
 * Returns empty object if no frontmatter or parse error.
 */
function parseFrontmatter(content: string): Record<string, unknown> {
  // Match leading --- block
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/)
  if (!match) {
    // Some files have a nested document_metadata block; try that
    const nestedMatch = content.match(/^---\r?\ndocument_metadata:\r?\n([\s\S]*?)\r?\n---/)
    if (nestedMatch) {
      // Parse the nested block shallowly
      return parseSimpleYaml(nestedMatch[1], 2)
    }
    return {}
  }
  return parseSimpleYaml(match[1], 0)
}

/**
 * Simple YAML parser for flat + one-level-nested key:value pairs.
 * Uses js-yaml for proper parsing, but we keep a fallback.
 */
function parseSimpleYaml(yamlText: string, _indent: number): Record<string, unknown> {
  // Use a lightweight approach: handle top-level fields only
  // For nested structures (document_metadata block), extract expose_to_chat / native_id / layer at top level
  const result: Record<string, unknown> = {}
  const lines = yamlText.split('\n')

  for (const line of lines) {
    // Top-level key: value (no leading spaces, or 2-space indent for nested document_metadata)
    const m = line.match(/^(\w[\w_]*):\s*(.*)$/)
    if (!m) continue
    const key = m[1]
    let val: string = m[2].trim()

    // Strip inline comments
    val = val.replace(/\s+#.*$/, '')

    // Unquote
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1)
    }

    // Boolean
    if (val === 'true') { result[key] = true; continue }
    if (val === 'false') { result[key] = false; continue }

    // Array shorthand [a, b, c]
    if (val.startsWith('[') && val.endsWith(']')) {
      const items = val.slice(1, -1).split(',').map(s => s.trim().replace(/^["']|["']$/g, ''))
      result[key] = items
      continue
    }

    // Numeric
    const num = Number(val)
    if (val !== '' && !isNaN(num)) { result[key] = num; continue }

    if (val !== '') {
      result[key] = val
    }
  }

  return result
}

/**
 * Map directory name to layer enum
 */
function dirToLayer(dir: string): LayerEnum {
  if (dir === '01_FACTS_LAYER') return 'L1'
  if (dir === '025_HOLISTIC_SYNTHESIS') return 'L2.5'
  if (dir === '03_DOMAIN_REPORTS') return 'L3'
  if (dir === '035_DISCOVERY_LAYER') return 'L3.5'
  if (dir === '06_LEARNING_LAYER') return 'L6'
  return 'L1'
}

/**
 * Map frontmatter status string to schema enum
 */
function mapStatus(raw: unknown): StatusEnum {
  if (typeof raw !== 'string') return 'CURRENT'
  const s = raw.toUpperCase()
  if (s === 'CURRENT' || s === 'CLOSED' || s === 'LIVE' || s === 'SCAFFOLD' || s === 'STUB') return 'CURRENT'
  if (s === 'SUPERSEDED') return 'PREDECESSOR'
  if (s === 'SOURCE') return 'SOURCE'
  if (s === 'QUALITY') return 'QUALITY'
  return 'CURRENT'
}

/**
 * Map frontmatter layer string to schema enum
 */
function mapLayer(raw: unknown): LayerEnum | null {
  if (typeof raw !== 'string') return null
  const valid: LayerEnum[] = ['L1', 'L2', 'L2.5', 'L3', 'L3.5', 'L4', 'L5', 'L6', 'Foundation']
  if (valid.includes(raw as LayerEnum)) return raw as LayerEnum
  return null
}

/**
 * Strip trailing .md from a candidate canonical_id value (some frontmatter
 * fields store the filename including extension, e.g. "MSR_v3_0.md").
 */
function stripMdExt(s: string): string {
  return s.endsWith('.md') ? s.slice(0, -3) : s
}

/**
 * Derive canonical_id from frontmatter or filename
 */
function deriveCanonicalId(fm: Record<string, unknown>, filename: string): string {
  if (typeof fm['canonical_id'] === 'string' && fm['canonical_id']) {
    return stripMdExt(fm['canonical_id'])
  }
  if (typeof fm['artifact_id'] === 'string' && fm['artifact_id']) {
    return stripMdExt(fm['artifact_id'])
  }
  if (typeof fm['artifact'] === 'string' && fm['artifact']) {
    return stripMdExt(fm['artifact'])
  }

  // Derive from filename: strip extension
  // e.g. FORENSIC_ASTROLOGICAL_DATA_v8_0.md -> FORENSIC_ASTROLOGICAL_DATA_v8_0
  return basename(filename, extname(filename))
}

/**
 * Walk a directory recursively, collecting .md file paths
 */
function walkDir(dir: string, results: string[] = []): string[] {
  let entries: string[]
  try {
    entries = readdirSync(dir)
  } catch {
    return results
  }
  for (const entry of entries) {
    const fullPath = join(dir, entry)
    const stat = statSync(fullPath)
    if (stat.isDirectory()) {
      if (!SKIP_DIRNAMES.has(entry)) {
        walkDir(fullPath, results)
      }
    } else if (stat.isFile()) {
      const ext = extname(entry).toLowerCase()
      const name = basename(entry)
      if (ext === '.md' && !SKIP_FILENAMES.has(name) && !SKIP_EXTENSIONS.has(ext)) {
        results.push(fullPath)
      }
    }
  }
  return results
}

/**
 * Derive an AssetEntry from a file path (absolute) and the scan dir name
 */
function deriveEntry(absPath: string, scanDir: string): AssetEntry | null {
  let content: string
  try {
    content = readFileSync(absPath, 'utf-8')
  } catch (err) {
    console.warn(`[auto_deriver] Could not read ${absPath}: ${err}`)
    return null
  }

  const fm = parseFrontmatter(content)
  const repoRelPath = relative(REPO_ROOT, absPath)
  const filename = basename(absPath)

  const canonical_id = deriveCanonicalId(fm, filename)
  const version = typeof fm['version'] === 'string' ? fm['version']
    : typeof fm['version'] === 'number' ? String(fm['version'])
    : 'unknown'

  const status = mapStatus(fm['status'])
  const layerFromFm = mapLayer(fm['layer'])
  const layer: LayerEnum = layerFromFm ?? dirToLayer(scanDir)

  const expose_to_chat = typeof fm['expose_to_chat'] === 'boolean' ? fm['expose_to_chat'] : false
  const native_id = typeof fm['native_id'] === 'string' && fm['native_id'] ? fm['native_id'] : 'abhisek'

  const fingerprint = createHash('sha256').update(content).digest('hex')

  const entry: AssetEntry = {
    canonical_id,
    path: repoRelPath,
    version,
    status,
    layer,
    expose_to_chat,
    representations: ['file'],
    interface_version: '1.0',
    fingerprint,
    native_id,
  }

  if (typeof fm['supplements_parent'] === 'string' && fm['supplements_parent']) {
    entry.supplements_parent = fm['supplements_parent']
  }

  return entry
}

/**
 * Walk the configured data directories and build an AssetEntry[] from frontmatter.
 */
export async function deriveManifest(): Promise<AssetEntry[]> {
  const entries: AssetEntry[] = []

  for (const scanDir of SCAN_DIRS) {
    const absDir = join(REPO_ROOT, scanDir)
    const files = walkDir(absDir)

    for (const absPath of files) {
      try {
        const entry = deriveEntry(absPath, scanDir)
        if (entry) {
          entries.push(entry)
        }
      } catch (err) {
        console.warn(`[auto_deriver] Skipping ${absPath} due to error: ${err}`)
      }
    }
  }

  return entries
}

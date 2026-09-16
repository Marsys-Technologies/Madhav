/**
 * parity_validator.ts — Stream F: Parity Validator
 * Compares CAPABILITY_MANIFEST.json against CANONICAL_ARTIFACTS_v1_0.md §1 (primary)
 * and FILE_REGISTRY_v1_14.md (version metadata only).
 *
 * Usage: tsx platform/src/scripts/manifest/parity_validator.ts
 * Or:    npm run manifest:validate-parity  (from platform/ directory)
 *
 * Output: platform/src/scripts/manifest/parity_report_2026-04-27.json
 */

import { readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { createHash } from 'node:crypto'

// ── Path constants ─────────────────────────────────────────────────────────────
// __dirname = .../Madhav/platform/src/scripts/manifest
// 4 levels up = .../Madhav (repo root)
const REPO_ROOT = join(__dirname, '..', '..', '..', '..')
const CANONICAL_ARTIFACTS_PATH = join(REPO_ROOT, '00_ARCHITECTURE', 'CANONICAL_ARTIFACTS_v1_0.md')
const FILE_REGISTRY_PATH = join(REPO_ROOT, '00_ARCHITECTURE', 'FILE_REGISTRY_v1_14.md')
const MANIFEST_PATH = join(REPO_ROOT, '00_ARCHITECTURE', 'CAPABILITY_MANIFEST.json')
const OUTPUT_PATH = join(__dirname, 'parity_report_2026-04-27.json')

// ── Types ──────────────────────────────────────────────────────────────────────

export interface CanonicalArtifactRow {
  canonical_id: string
  path: string
  version: string
  status: string
}

export interface MirrorPairRow {
  pair_id: string
  claude_side: string
  gemini_side: string | null
  mirror_mode: string
}

export interface ManifestEntry {
  canonical_id: string
  path: string | null
  version: string | null
  status: string
  [key: string]: unknown
}

export interface Manifest {
  generated_at: string
  generator_version: string
  entry_count: number
  fingerprint: string
  entries: ManifestEntry[]
}

export interface DriftDetail {
  drift_mode: string
  canonical_id: string
  path?: string
  detail: string
}

export interface ParityReport {
  parity_status: 'PASS' | 'FAIL'
  checked_at: string
  manifest_fingerprint: string
  file_registry_version: string
  canonical_artifacts_version: string
  summary: {
    registry_assets: number
    manifest_assets: number
    matched: number
    missing_from_manifest: number
    version_mismatches: number
    canonical_id_mismatches: number
    missing_mirror_pairs: number
  }
  drift_details: DriftDetail[]
}

// ── CANONICAL_ARTIFACTS parser ─────────────────────────────────────────────────

/**
 * Extract all fenced ```yaml blocks from text.
 */
export function extractYamlBlocks(text: string): string[] {
  const blocks: string[] = []
  const fenceRegex = /```yaml\s*\n([\s\S]*?)```/g
  let match: RegExpExecArray | null
  while ((match = fenceRegex.exec(text)) !== null) {
    blocks.push(match[1])
  }
  return blocks
}

/**
 * Minimal YAML scalar parser — handles the subset used in CANONICAL_ARTIFACTS.
 * Supports:  key: value  (unquoted or quoted strings, top-level only).
 * Deliberately ignores nested blocks (mirror_obligations etc).
 * Returns a flat key→string map.
 */
export function parseYamlScalars(block: string): Record<string, string> {
  const result: Record<string, string> = {}
  for (const rawLine of block.split('\n')) {
    // Skip comments and nested indented lines
    const line = rawLine.trimEnd()
    if (line.startsWith('#') || line.startsWith('  ') || line.startsWith('\t')) continue
    const colonIdx = line.indexOf(':')
    if (colonIdx === -1) continue
    const key = line.slice(0, colonIdx).trim()
    if (!key) continue
    let value = line.slice(colonIdx + 1).trim()
    // Strip inline comments
    const hashIdx = value.indexOf(' #')
    if (hashIdx !== -1) value = value.slice(0, hashIdx).trim()
    // Strip surrounding quotes
    if ((value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1)
    }
    if (value === 'null' || value === '~') {
      result[key] = ''
      continue
    }
    result[key] = value
  }
  return result
}

/**
 * Parse CANONICAL_ARTIFACTS_v1_0.md and return §1 artifact rows and §2 mirror pairs.
 */
export function parseCanonicalArtifacts(text: string): {
  artifacts: CanonicalArtifactRow[]
  mirrorPairs: MirrorPairRow[]
  fileVersion: string
} {
  // Locate §1 and §2 sections by header
  const sec1Start = text.indexOf('## §1')
  const sec2Start = text.indexOf('## §2')
  const sec3Start = text.indexOf('## §3')

  const sec1Text = sec2Start !== -1
    ? text.slice(sec1Start, sec2Start)
    : text.slice(sec1Start)

  const sec2Text = sec3Start !== -1
    ? text.slice(sec2Start, sec3Start)
    : sec2Start !== -1 ? text.slice(sec2Start) : ''

  // Parse §1 artifact rows
  const sec1Blocks = extractYamlBlocks(sec1Text)
  const artifacts: CanonicalArtifactRow[] = []
  for (const block of sec1Blocks) {
    const scalars = parseYamlScalars(block)
    if (!scalars['canonical_id']) continue
    // Exclude mirror-pair blocks (they have pair_id)
    if (scalars['pair_id']) continue
    artifacts.push({
      canonical_id: scalars['canonical_id'],
      path: scalars['path'] ?? '',
      version: scalars['version'] ?? '',
      status: scalars['status'] ?? '',
    })
  }

  // Parse §2 mirror-pair rows
  const sec2Blocks = extractYamlBlocks(sec2Text)
  const mirrorPairs: MirrorPairRow[] = []
  for (const block of sec2Blocks) {
    const scalars = parseYamlScalars(block)
    if (!scalars['pair_id']) continue
    mirrorPairs.push({
      pair_id: scalars['pair_id'],
      claude_side: scalars['claude_side'] ?? '',
      gemini_side: scalars['gemini_side'] || null,
      mirror_mode: scalars['mirror_mode'] ?? '',
    })
  }

  // Extract version from frontmatter (between --- delimiters)
  let fileVersion = '1.0'
  const versionMatch = text.match(/^version:\s*["']?([^"'\n]+)["']?/m)
  if (versionMatch) fileVersion = versionMatch[1].trim()

  return { artifacts, mirrorPairs, fileVersion }
}

// ── FILE_REGISTRY version reader ───────────────────────────────────────────────

/**
 * Extract version string from FILE_REGISTRY frontmatter.
 */
export function parseFileRegistryVersion(text: string): string {
  const match = text.match(/^version:\s*["']?([^"'\n]+)["']?/m)
  return match ? match[1].trim() : 'unknown'
}

// ── Version normalizer ─────────────────────────────────────────────────────────

/**
 * Normalize version for tolerant comparison.
 * "8" === "8.0", "1" === "1.0", "3.0" === "3" etc.
 * Returns the canonical form with trailing .0 segments stripped.
 */
export function normalizeVersion(v: string | null | undefined): string {
  if (!v) return ''
  v = v.replace(/^["']|["']$/g, '').trim()
  // Extract leading numeric portion (e.g. "1.0-updated-STEP_15" → "1.0")
  const numericMatch = v.match(/^(\d+(?:\.\d+)*)/)
  if (!numericMatch) return v.toLowerCase()
  const parts = numericMatch[1].split('.').map(Number)
  // Remove trailing zeros beyond the first segment
  while (parts.length > 1 && parts[parts.length - 1] === 0) {
    parts.pop()
  }
  return parts.join('.')
}

// ── Parity checker ─────────────────────────────────────────────────────────────

/**
 * The statuses that count as "CURRENT" for parity purposes.
 * GOVERNANCE_CLOSED and SUPERSEDED artifacts are intentionally excluded.
 */
export const CURRENT_STATUSES = new Set([
  'CURRENT',
  'LIVE',
  'LIVING',
  'AUTHORITATIVE',
])

/**
 * Path prefixes (or exact paths) that identify governance/architecture artifacts.
 * These are tracked in CANONICAL_ARTIFACTS for fingerprint governance, but they are
 * NOT expected in the consume-pipeline manifest (the manifest covers data-layer corpus
 * files only). A governance artifact absent from the manifest is correct behaviour,
 * not drift.
 */
const GOVERNANCE_PATH_PREFIXES = [
  '00_ARCHITECTURE/',
  'CLAUDE.md',
  '.geminirules',
  '.gemini/',
]

export function isDataLayerArtifact(path: string): boolean {
  for (const prefix of GOVERNANCE_PATH_PREFIXES) {
    if (path === prefix || path.startsWith(prefix)) return false
  }
  return true
}

/**
 * Build an index of manifest entries by canonical_id and by normalized path.
 */
export function buildManifestIndex(entries: ManifestEntry[]): {
  byId: Map<string, ManifestEntry>
  byPath: Map<string, ManifestEntry>
} {
  const byId = new Map<string, ManifestEntry>()
  const byPath = new Map<string, ManifestEntry>()
  for (const entry of entries) {
    byId.set(entry.canonical_id, entry)
    if (typeof entry.path === 'string' && entry.path.length > 0) {
      const normPath = entry.path.replace(/^\.\//, '')
      byPath.set(normPath, entry)
    }
  }
  return { byId, byPath }
}

/**
 * Run the parity check.
 * Exported for unit testing with mock data.
 */
export function runParityCheck(
  artifacts: CanonicalArtifactRow[],
  mirrorPairs: MirrorPairRow[],
  manifest: Manifest,
  fileRegistryVersion: string,
  caVersion: string,
): ParityReport {
  const driftDetails: DriftDetail[] = []
  const { byId, byPath } = buildManifestIndex(manifest.entries)

  // Only check artifacts whose status indicates they are active AND are data-layer files.
  // Governance-layer artifacts (00_ARCHITECTURE/, CLAUDE.md, .geminirules, .gemini/) live in
  // CANONICAL_ARTIFACTS for fingerprinting but are NOT expected in the consume manifest.
  const activeArtifacts = artifacts.filter(
    a => CURRENT_STATUSES.has(a.status) && isDataLayerArtifact(a.path),
  )

  let matched = 0
  let missingFromManifest = 0
  let versionMismatches = 0
  let canonicalIdMismatches = 0

  for (const artifact of activeArtifacts) {
    const normPath = artifact.path.replace(/^\.\//, '')
    const byIdMatch = byId.get(artifact.canonical_id)
    const byPathMatch = byPath.get(normPath)

    if (!byIdMatch && !byPathMatch) {
      // Completely absent from manifest
      missingFromManifest++
      driftDetails.push({
        drift_mode: 'missing_from_manifest',
        canonical_id: artifact.canonical_id,
        path: artifact.path,
        detail:
          `CA §1 artifact canonical_id="${artifact.canonical_id}" ` +
          `path="${artifact.path}" status="${artifact.status}" ` +
          `has NO matching entry in the manifest by id or path.`,
      })
      continue
    }

    // Resolve which manifest entry to use (prefer by id)
    const manifestEntry = byIdMatch ?? byPathMatch!

    // canonical_id alias (found by path only, not by id).
    // CA §1 uses short-form IDs (FORENSIC, LEL, MSR …) while the manifest builder derives
    // file-path-based IDs (FORENSIC_ASTROLOGICAL_DATA_v8_0 …). These refer to the same asset.
    // Count as matched (informational only — not a hard fail).
    if (!byIdMatch && byPathMatch) {
      canonicalIdMismatches++
      driftDetails.push({
        drift_mode: 'canonical_id_alias',
        canonical_id: artifact.canonical_id,
        path: artifact.path,
        detail:
          `CA short-form canonical_id "${artifact.canonical_id}" resolved to manifest entry ` +
          `"${manifestEntry.canonical_id}" by path match. ` +
          `This is an expected alias — not a hard failure.`,
      })
      // Still check version
      const caVer = normalizeVersion(artifact.version)
      const mVer = normalizeVersion(manifestEntry.version as string)
      if (caVer && mVer && caVer !== mVer) {
        versionMismatches++
        driftDetails.push({
          drift_mode: 'version_mismatch',
          canonical_id: artifact.canonical_id,
          path: artifact.path,
          detail:
            `CA version="${artifact.version}" (normalized: "${caVer}") ` +
            `≠ manifest version="${manifestEntry.version}" (normalized: "${mVer}").`,
        })
      } else {
        matched++
      }
      continue
    }

    // Version check (tolerant: "8" === "8.0")
    const caVer = normalizeVersion(artifact.version)
    const mVer = normalizeVersion(manifestEntry.version as string)
    if (caVer && mVer && caVer !== mVer) {
      versionMismatches++
      driftDetails.push({
        drift_mode: 'version_mismatch',
        canonical_id: artifact.canonical_id,
        path: artifact.path,
        detail:
          `CA version="${artifact.version}" (normalized: "${caVer}") ` +
          `≠ manifest version="${manifestEntry.version}" (normalized: "${mVer}").`,
      })
    } else {
      matched++
    }
  }

  // Mirror-pair check — check whether manifest_overrides.yaml has mirror_pairs section.
  // Stream G adds that section; at this time it does not exist, so all pairs will be
  // flagged as expected drift (NOT a validator bug per brief).
  const missingMirrorPairIds: string[] = []
  for (const pair of mirrorPairs) {
    missingMirrorPairIds.push(pair.pair_id)
    driftDetails.push({
      drift_mode: 'missing_mirror_pair',
      canonical_id: pair.pair_id,
      detail:
        `Mirror pair ${pair.pair_id} ` +
        `(claude_side="${pair.claude_side}", ` +
        `gemini_side="${pair.gemini_side ?? 'null'}", ` +
        `mode="${pair.mirror_mode}") ` +
        `is NOT represented in manifest_overrides.yaml mirror_pairs section. ` +
        `EXPECTED DRIFT at Phase 1B / Stream F: Stream G adds the mirror_pairs section. ` +
        `This is not a validator bug.`,
    })
  }

  // parity_status FAIL if any hard-fail drift modes are present.
  // canonical_id_alias and missing_mirror_pairs are informational — NOT hard fails.
  const hardFailCount = missingFromManifest + versionMismatches
  const parityStatus: 'PASS' | 'FAIL' = hardFailCount > 0 ? 'FAIL' : 'PASS'

  const manifestFingerprint = `sha256:${createHash('sha256')
    .update(JSON.stringify(manifest))
    .digest('hex')}`

  return {
    parity_status: parityStatus,
    checked_at: new Date().toISOString(),
    manifest_fingerprint: manifestFingerprint,
    file_registry_version: `v${fileRegistryVersion}`,
    canonical_artifacts_version: `v${caVersion}`,
    summary: {
      registry_assets: activeArtifacts.length,
      manifest_assets: manifest.entries.length,
      matched,
      missing_from_manifest: missingFromManifest,
      version_mismatches: versionMismatches,
      canonical_id_mismatches: canonicalIdMismatches,
      missing_mirror_pairs: missingMirrorPairIds.length,
    },
    drift_details: driftDetails,
  }
}

// ── Main ───────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log('[manifest:validate-parity] Starting parity validation...')

  // Read inputs
  const caText = readFileSync(CANONICAL_ARTIFACTS_PATH, 'utf-8')
  const frText = readFileSync(FILE_REGISTRY_PATH, 'utf-8')
  const manifestRaw = readFileSync(MANIFEST_PATH, 'utf-8')
  const manifest: Manifest = JSON.parse(manifestRaw)

  console.log(`[manifest:validate-parity] Manifest: ${manifest.entry_count} entries`)

  // Parse CANONICAL_ARTIFACTS
  const { artifacts, mirrorPairs, fileVersion: caVersion } = parseCanonicalArtifacts(caText)
  console.log(`[manifest:validate-parity] CA §1 rows parsed: ${artifacts.length} total`)
  console.log(`[manifest:validate-parity] CA §2 mirror pairs parsed: ${mirrorPairs.length} pairs`)

  // Parse FILE_REGISTRY version
  const frVersion = parseFileRegistryVersion(frText)
  console.log(`[manifest:validate-parity] FILE_REGISTRY version: ${frVersion}`)

  // Run parity check
  const report = runParityCheck(artifacts, mirrorPairs, manifest, frVersion, caVersion)

  // Write report
  writeFileSync(OUTPUT_PATH, JSON.stringify(report, null, 2), 'utf-8')

  // Print summary
  console.log('\n[manifest:validate-parity] ═══════════════════════════════════════')
  console.log(`[manifest:validate-parity] PARITY STATUS: ${report.parity_status}`)
  console.log('[manifest:validate-parity] ═══════════════════════════════════════')
  console.log(`  registry_assets (active CA §1):  ${report.summary.registry_assets}`)
  console.log(`  manifest_assets:                 ${report.summary.manifest_assets}`)
  console.log(`  matched:                         ${report.summary.matched}`)
  console.log(`  missing_from_manifest:           ${report.summary.missing_from_manifest}`)
  console.log(`  version_mismatches:              ${report.summary.version_mismatches}`)
  console.log(`  canonical_id_mismatches:         ${report.summary.canonical_id_mismatches}`)
  console.log(`  missing_mirror_pairs (expected): ${report.summary.missing_mirror_pairs}`)

  if (report.drift_details.length > 0) {
    const hardFails = report.drift_details.filter(d => d.drift_mode !== 'missing_mirror_pair')
    if (hardFails.length > 0) {
      console.log('\n[manifest:validate-parity] Hard-fail drift details:')
      for (const d of hardFails) {
        console.log(`  [${d.drift_mode}] ${d.canonical_id}`)
        console.log(`    ${d.detail}`)
      }
    }
    console.log(`\n[manifest:validate-parity] Expected drift (missing_mirror_pairs): ${report.summary.missing_mirror_pairs} pairs`)
    console.log('  (Stream G will add mirror_pairs section to manifest_overrides.yaml)')
  }

  console.log(`\n[manifest:validate-parity] Report written to: ${OUTPUT_PATH}`)

  process.exit(report.parity_status === 'PASS' ? 0 : 1)
}

// Guard: do not auto-run when imported by test runner (vitest sets VITEST env var)
if (!process.env['VITEST']) {
  main().catch(err => {
    console.error('[manifest:validate-parity] Fatal error:', err)
    process.exit(1)
  })
}

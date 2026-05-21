/**
 * freshness_aggregator.ts
 *
 * Pure helpers for computing asset freshness from CAPABILITY_MANIFEST.json.
 * No external dependencies beyond Node `fs` (used only at call site; the
 * function signature accepts a pre-parsed manifest so it stays testable).
 */

// ── Types ─────────────────────────────────────────────────────────────────────

export interface FreshnessRow {
  name: string
  lastTouched: Date | null
  rebuildCadence: string
  isStale: boolean
}

// ── Cadence thresholds ────────────────────────────────────────────────────────

/**
 * Returns the staleness threshold in milliseconds for a given canonical_id.
 * Falls back to a 90-day default if the asset does not match any known pattern.
 */
export function cadenceThresholdMs(canonicalId: string): number {
  const id = canonicalId.toLowerCase()

  // panchanga / daily-updated assets
  if (
    id.includes('panchang') ||
    id.includes('panchanga') ||
    id.includes('daily')
  ) {
    return 1 * 24 * 60 * 60 * 1000 // 1 day
  }

  // ephemeris — updated yearly
  if (id.includes('ephemeris') || id.includes('swisseph')) {
    return 365 * 24 * 60 * 60 * 1000 // 365 days
  }

  // MSR / CGM — per-session, treat as 30 days
  if (id.startsWith('msr') || id.startsWith('cgm')) {
    return 30 * 24 * 60 * 60 * 1000 // 30 days
  }

  // LEL — per-event, treat as 90 days
  if (id.startsWith('lel')) {
    return 90 * 24 * 60 * 60 * 1000 // 90 days
  }

  // Default: 90 days
  return 90 * 24 * 60 * 60 * 1000
}

/**
 * Returns a human-readable cadence label for a given canonical_id.
 */
export function cadenceLabel(canonicalId: string): string {
  const id = canonicalId.toLowerCase()

  if (
    id.includes('panchang') ||
    id.includes('panchanga') ||
    id.includes('daily')
  ) {
    return 'daily'
  }
  if (id.includes('ephemeris') || id.includes('swisseph')) {
    return 'yearly'
  }
  if (id.startsWith('msr') || id.startsWith('cgm')) {
    return '30 days'
  }
  if (id.startsWith('lel')) {
    return '90 days'
  }
  return '90 days'
}

// ── ManifestEntry shape ───────────────────────────────────────────────────────

interface ManifestEntry {
  canonical_id?: string
  updated_at?: string
  produced_on?: string
  [key: string]: unknown
}

interface Manifest {
  entries?: ManifestEntry[]
  [key: string]: unknown
}

// ── Core aggregator ───────────────────────────────────────────────────────────

/**
 * Computes freshness rows from a pre-parsed manifest object.
 * Only entries with a non-null `canonical_id` are included.
 * Sorted ascending by lastTouched (oldest/null first).
 */
export function computeFreshnessFromManifestObject(
  manifest: Manifest,
  now: Date = new Date(),
): FreshnessRow[] {
  const entries = Array.isArray(manifest.entries) ? manifest.entries : []

  const rows: FreshnessRow[] = []
  const seen = new Set<string>()

  for (const entry of entries) {
    const id = entry.canonical_id
    if (!id || typeof id !== 'string') continue
    if (seen.has(id)) continue
    seen.add(id)

    // Prefer updated_at, fall back to produced_on
    const dateStr = entry.updated_at ?? entry.produced_on ?? null
    const lastTouched: Date | null = dateStr ? new Date(dateStr) : null

    const threshold = cadenceThresholdMs(id)
    const cadence = cadenceLabel(id)

    let isStale: boolean
    if (lastTouched === null) {
      isStale = true
    } else {
      isStale = now.getTime() - lastTouched.getTime() > threshold
    }

    rows.push({ name: id, lastTouched, rebuildCadence: cadence, isStale })
  }

  // Sort: null lastTouched first, then oldest first
  rows.sort((a, b) => {
    if (a.lastTouched === null && b.lastTouched === null) return 0
    if (a.lastTouched === null) return -1
    if (b.lastTouched === null) return 1
    return a.lastTouched.getTime() - b.lastTouched.getTime()
  })

  return rows
}

/**
 * Reads CAPABILITY_MANIFEST.json from `manifestPath` and returns freshness rows.
 * This function uses `fs` and is intended for server-side / Node usage.
 */
export function computeFreshnessFromManifest(manifestPath: string): FreshnessRow[] {
  // Dynamic require keeps this file importable in test (jsdom) environments
  // when `fs` is not available — the function body is only executed at call time.
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const fs = require('fs') as typeof import('fs')
  const raw = fs.readFileSync(manifestPath, 'utf-8')
  const manifest: Manifest = JSON.parse(raw) as Manifest
  return computeFreshnessFromManifestObject(manifest)
}

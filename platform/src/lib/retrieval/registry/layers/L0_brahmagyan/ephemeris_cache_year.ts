/**
 * retrieval/registry/layers/L0_brahmagyan/ephemeris_cache_year.ts
 *
 * Resource: marsys://resource/ephemeris-cache/year/<yyyy>
 * Provides ephemeris data for a full calendar year (all 9 bodies).
 * Useful for bulk-context pre-fetch of planetary positions for a given year.
 *
 * L0FR Stream B — authored 2026-06-07
 */

import type { ResourceCapability } from '../../types'

const SIDECAR_URL = process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8001'

export const ephemerisCacheYearCapability: ResourceCapability = {
  uri: 'marsys://resource/ephemeris-cache/year/{yyyy}',
  primitive_type: 'resource',
  layer: 'L0',
  name: 'ephemeris_cache_year',
  description:
    'Ephemeris cache for a calendar year — all 9 Jyotish bodies (Sun through Ketu) ' +
    'at daily resolution. Covers 1900-2150. ' +
    'URI parameter {yyyy} is the 4-digit year (e.g. 1984, 2026). ' +
    'Returns up to one row per body per day for the year (9 bodies × ~365 days). ' +
    'Use for bulk-context pre-fetch when querying a whole year of transits.',
  mime_type: 'application/json',
  scope: 'global',
  archetype: 'flat_fact',
  traversal_level: 'L-OVERVIEW',
  tool_role: 'leaf',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: {
      cost_class: 'medium',
      always_prefetch: false,
      latency_ms_p50: 200,
    },
    bulk_context: {
      pre_fetch_priority: 50,
      always_include: false,
      result_size_kb_p50: 50,
    },
    result_max_kb: 256,
  },
  async loader(ctx?: unknown) {
    // Extract year from context or default to current year
    const year = (ctx as { year?: number })?.year ?? new Date().getFullYear()
    const start = `${year}-01-01`
    const end = `${year}-12-31`

    const params = new URLSearchParams({ start_date: start, end_date: end })

    try {
      const res = await fetch(
        `${SIDECAR_URL}/brahmagyan/ephemeris/all_bodies_range?${params}`,
        { headers: { 'Content-Type': 'application/json' } }
      )
      if (!res.ok) {
        return {
          ok: false,
          error: `sidecar ${res.status}: ${res.statusText}`,
          year,
          coverage: { start, end },
        }
      }
      return res.json()
    } catch (err) {
      return {
        ok: false,
        error: err instanceof Error ? err.message : String(err),
        year,
        coverage: { start, end },
      }
    }
  },
}

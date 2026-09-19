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

// ṢAḌ-DARŚANA W1 verify-reopen fix, 2026-07-30 — same defect class as query_planet_transit.ts
// (see that file's header for the full root-cause note): this capability forwarded no
// `x-api-key`, while `main.py` mounts the whole `/brahmagyan/ephemeris` router behind
// `Depends(verify_api_key)` and `PYTHON_SIDECAR_API_KEY` IS set on every deployed service.
// Every production call therefore 401'd and degraded to an empty result indistinguishable
// from a genuine empty. Propagates query_planet_position.ts's WP-1.7 fix (API key + the
// `:8001` -> `:8000` default-port correction) to this sibling.
const SIDECAR_URL = process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8000'
const SIDECAR_API_KEY = process.env['PYTHON_SIDECAR_API_KEY'] ?? ''

/** Sidecar request headers, including the API key when configured. See the header note —
 *  omitting this is what silently 401'd every production call to this capability. */
function sidecarHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (SIDECAR_API_KEY) headers['x-api-key'] = SIDECAR_API_KEY
  return headers
}


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
  semantic_capabilities: [{
    scu_id: 'scu.catalog.ephemeris_cache_year', version: 1,
    label: 'Annual ephemeris-cache evidence', description: 'Retrieve one year of ephemeris coverage through the authenticated ephemeris service.',
    kind: 'datum', domains: ['timing'], concepts: ['ephemeris', 'cache_coverage'], intents: ['assess', 'verify'], horizons: ['historical', 'current', 'future'], scope: 'global',
    inputs: ['year'], outputs: ['coverage', 'rows'], primary_binding_uri: 'marsys://resource/ephemeris-cache/year/{yyyy}',
    provenance_requirements: ['computed_at', 'engine_version'], freshness_policy: 'Requires a fresh authenticated ephemeris-engine probe; a missing or stale probe keeps this binding unavailable.',
    entitlement: 'native', safety_notes: ['Read-only service resource.'], known_gaps: [],
    availability_contracts: [{ binding_id: 'registry:marsys://resource/ephemeris-cache/year/{yyyy}', requirements: [{
      kind: 'service_probe', asset_id: 'bg_ephemeris_engine', probe_id: 'ephemeris_engine', endpoint_identity: 'nirmana-elevation:health-probe:bg_ephemeris_engine',
      probe_contract_sha256: 'e94a594d245b97251bc731757b56dac406433e12c8daa4b1df1d478e8e9ae1c4', max_age_seconds: 900,
      source_ref: 'platform/supabase/migrations/624_nirmana_l0_ephemeris_probe_contract.sql#bg_ephemeris_engine; platform/python-sidecar/routers/nirmana_probe.py#/internal/nirmana/probe',
    }] }], editorial: false,
  }],
  async loader(ctx?: unknown) {
    // Extract year from context or default to current year
    const year = (ctx as { year?: number })?.year ?? new Date().getFullYear()
    const start = `${year}-01-01`
    const end = `${year}-12-31`

    const params = new URLSearchParams({ start_date: start, end_date: end })

    try {
      const res = await fetch(
        `${SIDECAR_URL}/brahmagyan/ephemeris/all_bodies_range?${params}`,
        { headers: sidecarHeaders() }
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

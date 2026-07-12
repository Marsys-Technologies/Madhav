/**
 * retrieval/registry/layers/L0_brahmagyan/query_planet_position.ts
 *
 * Tool: marsys://tool/L0/query_planet_position
 * Query tropical longitude, sign, nakshatra for a planet on a date.
 * Backed by ephemeris_daily (1900-2150, 9 bodies, pyswisseph DE441).
 *
 * L0FR Stream B — authored 2026-06-07
 */

import type { ToolCapability } from '../../types'

// WP-1.7 (LCA-1, LCA-12): the local sidecar bench runs on :8000 (see main.py +
// .env.local.example PYTHON_SIDECAR_URL). The prior 8001 default silently missed the
// bench and contributed to ephemeris "returns nothing" symptoms locally. On deployed,
// PYTHON_SIDECAR_URL is set explicitly, so this default only affects the local bench.
const SIDECAR_URL = process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8000'
const SIDECAR_API_KEY = process.env['PYTHON_SIDECAR_API_KEY'] ?? ''

export const queryPlanetPositionCapability: ToolCapability = {
  uri: 'marsys://tool/L0/query_planet_position',
  primitive_type: 'tool',
  layer: 'L0',
  name: 'query_planet_position',
  description:
    'Query planetary positions from the ephemeris_daily table (1900–2150, daily resolution, ' +
    'tropical coordinates — subtract Lahiri ayanamsha to get sidereal). ' +
    'Returns longitude_deg, sign_number, nakshatra_number, is_retrograde, speed_dps ' +
    'for one or all 9 Jyotish bodies (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu). ' +
    'Use for natal chart checks, transit lookup, or any date-specific position query. ' +
    'Source: pyswisseph DE441 / Swiss Ephemeris .se1 files. Date range: 1900-01-01 to 2150-12-31.',
  input_schema: {
    type: 'object',
    properties: {
      date: {
        type: 'string',
        description: 'Date in YYYY-MM-DD format (1900-01-01 to 2150-12-31).',
      },
      planet: {
        type: 'string',
        description:
          'Optional: planet to query (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu). ' +
          'Omit to return all 9 planets.',
        enum: ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'],
      },
    },
    required: ['date'],
    additionalProperties: false,
  },
  output_schema: {
    type: 'object',
    properties: {
      ok: { type: 'boolean' },
      date: { type: 'string' },
      positions: { type: 'array', description: 'Array of position rows' },
      count: { type: 'number' },
      ayanamsha_id: { type: 'string' },
    },
  },
  required_inputs: [],
  scope: 'global',
  archetype: 'flat_fact',
  traversal_level: 'L-OVERVIEW',
  tool_role: 'leaf',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      always_prefetch: false,
      latency_ms_p50: 30,
    },
    bulk_context: {
      pre_fetch_priority: 90,
      always_include: false,
      result_size_kb_p50: 2,
    },
    result_max_kb: 8,
  },
  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    const date = args['date'] as string
    const planet = args['planet'] as string | undefined

    const params = new URLSearchParams({ date })
    if (planet) params.set('planet', planet)

    // WP-1.7: forward the sidecar API key when configured (the sidecar's verify_api_key
    // dependency 401s on a missing/mismatched x-api-key when PYTHON_SIDECAR_API_KEY is set).
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (SIDECAR_API_KEY) headers['x-api-key'] = SIDECAR_API_KEY

    let res: Response
    try {
      res = await fetch(`${SIDECAR_URL}/brahmagyan/ephemeris/planet_position?${params}`, { headers })
    } catch (err) {
      // WP-1.7 (honest confidence): the sidecar being down is NOT a high-confidence empty.
      return {
        ok: false,
        error: `sidecar unreachable at ${SIDECAR_URL}: ${err instanceof Error ? err.message : String(err)}`,
        confidence: 'none',
        date,
        count: 0,
        positions: [],
      }
    }
    if (!res.ok) {
      const msg = await res.text().catch(() => res.statusText)
      return { ok: false, error: `sidecar ${res.status}: ${msg}`, confidence: 'none', date, count: 0, positions: [] }
    }

    const payload = (await res.json().catch(() => null)) as
      | { ok?: boolean; positions?: unknown[]; count?: number }
      | null

    // WP-1.7 (LCA-1 honest confidence): the pre-fix handler passed the sidecar body
    // through verbatim, so an empty result (positions:[]) was still surfaced as
    // ok:true/high-confidence by the primitives envelope. An empty ephemeris response
    // for a valid in-range date means the lookup FAILED (bad date, missing rows) — it is
    // never a legitimate "nothing here". Report it honestly as ok:false / confidence none.
    const positions = Array.isArray(payload?.positions) ? payload!.positions : []
    if (!payload || positions.length === 0) {
      return {
        ok: false,
        error: 'ephemeris returned no positions — treat as failed lookup, not a high-confidence empty',
        confidence: 'none',
        date,
        count: 0,
        positions: [],
      }
    }
    return payload
  },
}

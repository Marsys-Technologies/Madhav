/**
 * retrieval/registry/layers/L0_brahmagyan/query_retrograde_periods.ts
 *
 * Tool: marsys://tool/L0/query_retrograde_periods
 * Find retrograde station events (start/end) for a planet in a date window.
 *
 * L0FR Stream B — authored 2026-06-07
 */

import type { ToolCapability } from '../../types'

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


export const queryRetrogradePeriodsCapability: ToolCapability = {
  uri: 'marsys://tool/L0/query_retrograde_periods',
  primitive_type: 'tool',
  layer: 'L0',
  name: 'query_retrograde_periods',
  description:
    'Find retrograde station events (retrograde_start / retrograde_end) for a planet in a date window. ' +
    'Detects sign changes in the is_retrograde flag across daily ephemeris rows. ' +
    'Applicable to Mercury, Venus, Mars, Jupiter, Saturn ' +
    '(Rahu/Ketu are always retrograde — not meaningful to query). ' +
    'Returns station date, type, longitude at station, sign_number, retrograde day count. ' +
    'Backed by ephemeris_daily (1900-2150).',
  input_schema: {
    type: 'object',
    properties: {
      planet: {
        type: 'string',
        description: 'Planet to query. Mercury, Venus, Mars, Jupiter, Saturn only (retrograde is meaningful).',
        enum: ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn'],
      },
      start_date: {
        type: 'string',
        description: 'Start date in YYYY-MM-DD format.',
      },
      end_date: {
        type: 'string',
        description: 'End date in YYYY-MM-DD format.',
      },
    },
    required: ['planet', 'start_date', 'end_date'],
    additionalProperties: false,
  },
  output_schema: {
    type: 'object',
    properties: {
      ok: { type: 'boolean' },
      planet: { type: 'string' },
      stations: { type: 'array', description: 'Station events with date, type, longitude, sign' },
      station_count: { type: 'number' },
      retrograde_days: { type: 'number' },
    },
  },
  required_inputs: [],
  scope: 'global',
  archetype: 'temporal',
  traversal_level: 'L-OVERVIEW',
  tool_role: 'temporal',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      always_prefetch: false,
      latency_ms_p50: 60,
    },
    bulk_context: {
      pre_fetch_priority: 65,
      always_include: false,
      result_size_kb_p50: 3,
    },
    result_max_kb: 16,
  },
  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    const planet = args['planet'] as string
    const start_date = args['start_date'] as string
    const end_date = args['end_date'] as string

    const params = new URLSearchParams({ planet, start_date, end_date })

    const res = await fetch(
      `${SIDECAR_URL}/brahmagyan/ephemeris/retrograde_periods?${params}`,
      { headers: sidecarHeaders() }
    )
    if (!res.ok) {
      const msg = await res.text().catch(() => res.statusText)
      return { ok: false, error: `sidecar ${res.status}: ${msg}`, planet, station_count: 0, stations: [] }
    }
    return res.json()
  },
}

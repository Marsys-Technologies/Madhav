/**
 * retrieval/registry/layers/L0_brahmagyan/query_aspects_at_time.ts
 *
 * Tool: marsys://tool/L0/query_aspects_at_time
 * Compute active planetary aspects for all body pairs on a given date.
 * Aspects: conjunction (0°), sextile (60°), square (90°), trine (120°), opposition (180°).
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


export const queryAspectsAtTimeCapability: ToolCapability = {
  uri: 'marsys://tool/L0/query_aspects_at_time',
  primitive_type: 'tool',
  layer: 'L0',
  name: 'query_aspects_at_time',
  description:
    'Compute active planetary aspects (conjunction, sextile, square, trine, opposition) ' +
    'for all body pairs on a specific date, with configurable orb in degrees. ' +
    'Returns body pair, aspect type, exact angle, actual angular difference, and orb. ' +
    'Based on tropical longitudes from ephemeris_daily (1900-2150).',
  input_schema: {
    type: 'object',
    properties: {
      date: {
        type: 'string',
        description: 'Date in YYYY-MM-DD format.',
      },
      orb_degrees: {
        type: 'number',
        description: 'Orb tolerance in degrees (default 1.0; max 10.0).',
        default: 1.0,
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
      aspects: { type: 'array', description: 'Active aspects' },
      count: { type: 'number' },
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
      latency_ms_p50: 30,
    },
    bulk_context: {
      pre_fetch_priority: 60,
      always_include: false,
      result_size_kb_p50: 2,
    },
    result_max_kb: 8,
  },
  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    const date = args['date'] as string
    const orb_degrees = (args['orb_degrees'] as number | undefined) ?? 1.0

    const params = new URLSearchParams({ date, orb_degrees: String(orb_degrees) })

    const res = await fetch(
      `${SIDECAR_URL}/brahmagyan/ephemeris/aspects?${params}`,
      { headers: sidecarHeaders() }
    )
    if (!res.ok) {
      const msg = await res.text().catch(() => res.statusText)
      return { ok: false, error: `sidecar ${res.status}: ${msg}`, date, count: 0, aspects: [] }
    }
    return res.json()
  },
}

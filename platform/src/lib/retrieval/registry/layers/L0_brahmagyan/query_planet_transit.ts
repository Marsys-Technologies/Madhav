/**
 * retrieval/registry/layers/L0_brahmagyan/query_planet_transit.ts
 *
 * Tool: marsys://tool/L0/query_planet_transit
 * Query a planet's daily position series across a date range.
 * Optionally filtered by tropical sign number.
 *
 * L0FR Stream B — authored 2026-06-07
 */

import type { ToolCapability } from '../../types'

const SIDECAR_URL = process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8001'

export const queryPlanetTransitCapability: ToolCapability = {
  uri: 'marsys://tool/L0/query_planet_transit',
  primitive_type: 'tool',
  layer: 'L0',
  name: 'query_planet_transit',
  description:
    'Query a planet\'s transit series (daily longitude, sign, nakshatra) across a date window. ' +
    'Optionally filter by tropical sign number to find when a planet transits a specific sign. ' +
    'Use for transit windows, sign-entry/exit dates, and nakshatra progressions. ' +
    'Result set is capped and paginated. Data from ephemeris_daily (1900-2150).',
  input_schema: {
    type: 'object',
    properties: {
      planet: {
        type: 'string',
        description: 'Planet to query.',
        enum: ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'],
      },
      start_date: {
        type: 'string',
        description: 'Start date in YYYY-MM-DD format.',
      },
      end_date: {
        type: 'string',
        description: 'End date in YYYY-MM-DD format.',
      },
      sign_number: {
        type: 'number',
        description: 'Optional: filter to rows where planet is in this sign (1=Aries through 12=Pisces, tropical).',
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
      rows: { type: 'array', description: 'Daily transit rows' },
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
      latency_ms_p50: 50,
    },
    bulk_context: {
      pre_fetch_priority: 70,
      always_include: false,
      result_size_kb_p50: 10,
    },
    result_max_kb: 50,
  },
  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    const planet = args['planet'] as string
    const start_date = args['start_date'] as string
    const end_date = args['end_date'] as string
    const sign_number = args['sign_number'] as number | undefined

    const params = new URLSearchParams({ planet, start_date, end_date })
    if (sign_number !== undefined) params.set('sign_number', String(sign_number))

    const res = await fetch(
      `${SIDECAR_URL}/brahmagyan/ephemeris/planet_transit?${params}`,
      { headers: { 'Content-Type': 'application/json' } }
    )
    if (!res.ok) {
      const msg = await res.text().catch(() => res.statusText)
      return { ok: false, error: `sidecar ${res.status}: ${msg}`, planet, count: 0, rows: [] }
    }
    return res.json()
  },
}

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

const SIDECAR_URL = process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8001'

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
    'Source: pyswisseph DE441 / Swiss Ephemeris .se1 files. Native birth date: 1984-02-05.',
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
  async handler(args: Record<string, unknown>, _ctx) {
    const date = args['date'] as string
    const planet = args['planet'] as string | undefined

    const params = new URLSearchParams({ date })
    if (planet) params.set('planet', planet)

    const res = await fetch(
      `${SIDECAR_URL}/brahmagyan/ephemeris/planet_position?${params}`,
      { headers: { 'Content-Type': 'application/json' } }
    )
    if (!res.ok) {
      const msg = await res.text().catch(() => res.statusText)
      return { ok: false, error: `sidecar ${res.status}: ${msg}`, date, count: 0, positions: [] }
    }
    return res.json()
  },
}

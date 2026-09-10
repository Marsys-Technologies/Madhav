/**
 * query_sky_calendar — L0 Brahmagyan chart-independent sky-event diary reader
 * =============================================================================
 * NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md L0-W2 DECIDE, NOW item 14
 * (L0_W2_DECIDE_v1_0.md §2): bg_sky_calendar had no dedicated MCP/retrieval query
 * capability -- only one narrow internal Python consumer
 * (services/gochara_v3/mechanisms/w26_real_eclipses.py) and zero LLM-facing surface,
 * unlike its sibling bg_muhurta_lattice. This capability closes that gap, mirroring
 * query_muhurta_lattice.ts's structure.
 *
 * Substrate: table `bg_sky_events`, writer `bg_sky_calendar.py`, migration 473. This
 * capability computes NOTHING astrological of its own -- it is the read path only.
 *
 * WHAT IT SERVES: every sky-event row whose event_datetime_utc falls inside the
 * requested [start_utc, end_utc) interval, across the five event_type values the
 * substrate's CHECK constraint allows (ingress, station, eclipse_solar, eclipse_lunar,
 * double_transit).
 *
 * SCOPE (per the writer's own module docstring, migration 473's header comment):
 * chart-independent global astronomy ONLY -- ingresses (9 grahas), stations (5
 * classical planets; Rahu/Ketu never station), eclipse TIMING (not per-location
 * visibility/magnitude -- that needs an observer position), and double-transit
 * conjunction geometry. Returns and any per-chart/natal contact join are explicitly
 * OUT of scope here -- that is `ka_kshetra`'s deferred job (staged, not landed, per
 * that module's own docstring) -- this capability never simulates or approximates it.
 *
 * Global chart-independent reference -- no chart_id, by construction.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

/** The five event families the substrate's CHECK constraint allows (migration 473). */
const EVENT_TYPES = ['ingress', 'station', 'eclipse_solar', 'eclipse_lunar', 'double_transit'] as const

const MAX_ROWS = 2000

function isIsoInstant(value: string): boolean {
  return !Number.isNaN(Date.parse(value))
}

export const querySkyCalendarCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_sky_calendar',
  type:  'tool',
  layer: 'L0',
  name:  'query_sky_calendar',

  description: [
    'Read the global chart-independent sky-event diary (bg_sky_events) for a time interval.',
    'Five event families: ingress (sign-boundary crossings, 9 grahas), station (retro/direct',
    'stations for Mars/Mercury/Jupiter/Venus/Saturn -- Sun/Moon never station, Rahu/Ketu are',
    'deliberately excluded), eclipse_solar / eclipse_lunar (TIMING only -- max/begin/end instant',
    'and classical type; per-location visibility/magnitude is NOT computed here), and',
    'double_transit (slow-mover conjunction geometry, e.g. Jupiter-Saturn). Every row carries',
    'its own source_citation (computational provenance, not a classical text citation -- this is',
    'instrument-emergent ephemeris output). Chart-contact/natal-join questions ("does this event',
    'touch a specific chart") are explicitly OUT of scope -- that is a separate, chart-scoped',
    'consumer\'s job, not this global diary\'s. Global reference: no chart_id needed.',
  ].join(' '),

  input_schema: {
    start_utc: { type: 'string', description: 'Interval start, ISO-8601 UTC (e.g. 2026-08-05T00:00:00Z). Required.' },
    end_utc:   { type: 'string', description: 'Interval end, ISO-8601 UTC. Required. Events with event_datetime_utc in [start_utc, end_utc) are returned.' },
    event_type: { type: 'string', description: `Optional filter: one of ${EVENT_TYPES.join(', ')}. Omit for all five.` },
    primary_body: { type: 'string', description: 'Optional exact primary_body filter (e.g. Jupiter, Saturn, Mars).' },
    limit: { type: 'number', description: `Max rows (default ${MAX_ROWS}, hard cap ${MAX_ROWS}). Narrow the interval rather than raising this.` },
  },

  required_inputs: ['start_utc', 'end_utc'],
  scope: 'global',
  archetype: 'flat_fact',
  traversal_level: 'L-SOURCE',
  tool_role: 'leaf',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 20, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const startUtc = args['start_utc'] != null ? String(args['start_utc']) : ''
    const endUtc   = args['end_utc']   != null ? String(args['end_utc'])   : ''
    if (!startUtc || !endUtc || !isIsoInstant(startUtc) || !isIsoInstant(endUtc)) {
      return {
        content: { error: 'start_utc and end_utc are required and must be parseable ISO-8601 instants.' },
        is_error: true,
      }
    }
    if (Date.parse(endUtc) <= Date.parse(startUtc)) {
      return { content: { error: 'end_utc must be strictly after start_utc.' }, is_error: true }
    }

    const eventTypeArg = args['event_type'] != null ? String(args['event_type']) : null
    if (eventTypeArg && !(EVENT_TYPES as readonly string[]).includes(eventTypeArg)) {
      return {
        content: { error: `event_type must be one of: ${EVENT_TYPES.join(', ')}` },
        is_error: true,
      }
    }
    const primaryBody = args['primary_body'] != null ? String(args['primary_body']) : null
    const requestedLimit = args['limit'] != null ? Number(args['limit']) : MAX_ROWS
    const limit = Number.isFinite(requestedLimit) && requestedLimit > 0
      ? Math.min(Math.floor(requestedLimit), MAX_ROWS)
      : MAX_ROWS

    const filters: string[] = ['event_datetime_utc >= $1', 'event_datetime_utc < $2']
    const params: unknown[] = [startUtc, endUtc]
    let p = 3
    if (eventTypeArg) { filters.push(`event_type = $${p++}`); params.push(eventTypeArg) }
    if (primaryBody) { filters.push(`primary_body = $${p++}`); params.push(primaryBody) }
    params.push(limit)

    const sql = `
      SELECT event_type, primary_body, secondary_body, event_datetime_utc,
             sign, nakshatra, longitude_deg, speed_dps, detail,
             ayanamsha_key, sampling_method, source_citation
      FROM bg_sky_events
      WHERE ${filters.join(' AND ')}
      ORDER BY event_datetime_utc, event_type, primary_body
      LIMIT $${p}`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      const rows = result.rows

      const eventTypeCounts: Record<string, number> = {}
      for (const r of rows) {
        const type = String(r['event_type'])
        eventTypeCounts[type] = (eventTypeCounts[type] ?? 0) + 1
      }

      return {
        content: {
          rows,
          count: rows.length,
          truncated: rows.length === limit,
          event_type_counts: eventTypeCounts,
          interval: { start_utc: startUtc, end_utc: endUtc },
          filters: { event_type: eventTypeArg, primary_body: primaryBody, limit },
          ...(rows.length === 0
            ? {
                empty_reason:
                  `No sky-event rows fall in [${startUtc}, ${endUtc})` +
                  (eventTypeArg ? ` for event_type=${eventTypeArg}` : '') +
                  (primaryBody ? ` / primary_body=${primaryBody}` : '') +
                  '. The diary carries a rolling forward horizon built by an explicit ' +
                  'super-admin L0 trigger -- an interval outside that built horizon returns ' +
                  'honestly empty rather than a computed claim.',
              }
            : {}),
          disclaimer:
            'Chart-independent global astronomy only -- ingress/station/eclipse-timing/' +
            'double-transit events, not a per-chart contact or election verdict. Whether any ' +
            'event here touches a specific chart is a separate, chart-scoped question this ' +
            'capability does not answer.',
          provenance: { tables: ['bg_sky_events'], asset_id: 'bg_sky_calendar' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}

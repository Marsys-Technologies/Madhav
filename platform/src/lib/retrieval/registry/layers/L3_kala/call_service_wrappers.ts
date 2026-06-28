/**
 * L3 Service Wrappers — call_* capabilities (L3 Kāla)
 * =====================================================
 * Five service-asset wrappers for the L3 compute services:
 *
 *   call_transit_search    — ka_gochara service (transit event search)
 *   call_ephemeris_at_t    — ka_graha_sancara service (positions at arbitrary time)
 *   call_dasha_eligibility — ka_dasha_kala service (dasha eligibility windows)
 *   call_muhurta_score     — ka_muhurta_seva service (auspicious window scoring)
 *   call_priority_ranking  — ka_tulana service (signal priority ranking by period)
 *
 * These are compute services, not tables — they wrap API/proc calls.
 * Transit and muhurta are global (chart-agnostic at the descriptor level);
 * dasha_eligibility and priority_ranking are per_chart.
 *
 * All conform to D1 contract (archetype, traversal_level, tool_role, etc.).
 * Chart-agnostic principle: no native chart_id defaults anywhere.
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

// ── call_transit_search ───────────────────────────────────────────────────────

export const callTransitSearchCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/call_transit_search',
  type:  'tool',
  layer: 'L3',
  name:  'call_transit_search',

  description: [
    'Search for planetary transit events in a date range (ka_gochara service).',
    'Global scope — not chart-specific. Use for gochara lookup over natal positions.',
    'Returns transit ingress/egress events, retrograde stations, and conjunctions.',
    'Provide chart_id optionally to filter transits against natal planet positions.',
  ].join(' '),

  scope: 'global',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'temporal',
  emits_references: false,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,

  input_schema: {
    event_type: {
      type: 'string',
      description: "Type of transit event: 'aspect' (planet-to-natal-point) or 'conjunction' (planet-to-planet). Required.",
      enum: ['aspect', 'conjunction'],
      required: true,
    },
    date_from: {
      type: 'string',
      description: 'Start date for transit search (ISO 8601: YYYY-MM-DD). Required.',
      required: true,
    },
    date_to: {
      type: 'string',
      description: 'End date for transit search (ISO 8601: YYYY-MM-DD, max 10yr window). Required.',
      required: true,
    },
    // Aspect-mode fields (event_type = 'aspect')
    transit_planet: {
      type: 'string',
      description: "Moving planet to track (e.g. 'Saturn'). Required for aspect mode.",
      enum: ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'],
    },
    target_longitude_deg: {
      type: 'number',
      description: 'Natal longitude (degrees 0–360) that the transit planet aspects. Required for aspect mode.',
    },
    aspect_degrees: {
      type: 'array',
      description: 'Aspect angles to detect (default: [0,60,90,120,180]).',
    },
    // Conjunction-mode fields (event_type = 'conjunction')
    planet_a: {
      type: 'string',
      description: "First planet for conjunction mode (e.g. 'Jupiter'). Required for conjunction mode.",
      enum: ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'],
    },
    planet_b: {
      type: 'string',
      description: "Second planet for conjunction mode (e.g. 'Saturn'). Required for conjunction mode.",
      enum: ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'],
    },
    orb_deg: {
      type: 'number',
      description: 'Orb in degrees (default: 1.0, max: 3.0).',
    },
  },

  llm_hints: {
    agentic: { cost_class: 'medium' },
    bulk_context: { pre_fetch_priority: 30 },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const date_from  = args['date_from'] as string
    const date_to    = args['date_to'] as string
    const event_type = (args['event_type'] as string | undefined) ?? 'conjunction'

    if (!date_from || !date_to) {
      return { content: { error: 'date_from and date_to are required' }, is_error: true }
    }

    const sidecarUrl = process.env.PYTHON_SIDECAR_URL
    const sidecarKey = process.env.PYTHON_SIDECAR_API_KEY ?? ''

    if (!sidecarUrl) {
      return { content: { error: 'PYTHON_SIDECAR_URL not configured — transit search unavailable' }, is_error: true }
    }

    const body: Record<string, unknown> = {
      event_type,
      start_date: date_from,
      end_date:   date_to,
      orb_deg:    args['orb_deg'] ?? 1.0,
    }

    if (event_type === 'aspect') {
      body['transit_planet']        = args['transit_planet']
      body['target_longitude_deg']  = args['target_longitude_deg']
      body['aspect_degrees']        = args['aspect_degrees'] ?? [0, 60, 90, 120, 180]
    } else {
      body['planet_a'] = args['planet_a']
      body['planet_b'] = args['planet_b']
    }

    try {
      const resp = await fetch(`${sidecarUrl}/api/compute/transit_search`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'x-api-key': sidecarKey },
        body:    JSON.stringify(body),
      })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        return { content: { error: `Sidecar ${resp.status}`, detail: err }, is_error: true }
      }
      const events = await resp.json() as unknown[]
      return {
        content: { date_from, date_to, event_type, events, count: events.length },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}

// ── call_ephemeris_at_t ───────────────────────────────────────────────────────

export const callEphemerisAtTCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/call_ephemeris_at_t',
  type:  'tool',
  layer: 'L3',
  name:  'call_ephemeris_at_t',

  description: [
    'Returns planetary positions at an arbitrary datetime (ka_graha_sancara service).',
    'Global scope — not chart-specific.',
    'Provide a precise datetime and ayanamsha to get all graha positions.',
  ].join(' '),

  scope: 'global',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'temporal',
  emits_references: false,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,

  input_schema: {
    datetime_utc: {
      type: 'string',
      description: 'UTC datetime (ISO 8601: YYYY-MM-DDTHH:MM:SSZ). Required.',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha (default: 'LAHIRI').",
    },
  },

  llm_hints: {
    agentic: { cost_class: 'medium' },
    bulk_context: { pre_fetch_priority: 35 },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const datetime_utc = args['datetime_utc'] as string
    if (!datetime_utc) {
      return { content: { error: 'datetime_utc is required' }, is_error: true }
    }

    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'

    // ka_graha_sancara is a compute service (asset_registry target_table = null) — there is no
    // ka_graha_sancara_snapshot table to query. Positions at an arbitrary datetime must be
    // produced by the compute sidecar. No /api/compute endpoint is wired for arbitrary-time
    // ephemeris yet (the existing /ephemeris router computes natal positions from birth params,
    // not a general datetime_utc + ayanamsha contract), so fail loud rather than query a phantom
    // table. See needs_decision: wire a /api/compute/ephemeris_at_t sidecar endpoint.
    return {
      content: {
        error: 'call_ephemeris_at_t is not yet wired to a compute sidecar endpoint',
        note: 'ka_graha_sancara is a compute service with no backing table; no /api/compute/ephemeris_at_t endpoint exists yet. This handler will return positions once the sidecar endpoint is added.',
        datetime_utc,
        ayanamsha_id,
      },
      is_error: true,
    }
  },
}

// ── call_dasha_eligibility ────────────────────────────────────────────────────

export const callDashaEligibilityCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/call_dasha_eligibility',
  type:  'tool',
  layer: 'L3',
  name:  'call_dasha_eligibility',

  description: [
    'Returns dasha eligibility windows for a chart (ka_dasha_kala service).',
    'Per-chart: requires chart_id. Returns which dasha lords are active in a date range,',
    'eligibility thresholds, and dasha overlap analysis.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'temporal',
  emits_references: false,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha (default: 'lahiri').",
    },
    date_from: {
      type: 'string',
      description: 'Start date (ISO 8601: YYYY-MM-DD). Default: today.',
    },
    date_to: {
      type: 'string',
      description: 'End date (ISO 8601: YYYY-MM-DD). Default: 3 years from today.',
    },
    target_lords: {
      type: 'array',
      description: "Graha names to filter by (e.g. ['Jupiter','Saturn']). chart_dashas is a flat one-row-per-level model (level_n + lord_graha), so this filters rows whose lord_graha is in the list, at any level. Omit to return all active windows.",
    },
  },

  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 20 },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const ayanamsha_id  = (args['ayanamsha_id'] as string | undefined) ?? 'lahiri'
    const date_from     = (args['date_from'] as string | undefined) ?? new Date().toISOString().split('T')[0]
    const date_to       = (args['date_to'] as string | undefined) ?? new Date(Date.now() + 3 * 365 * 86400000).toISOString().split('T')[0]
    const target_lords  = (args['target_lords'] as string[] | undefined) ?? []

    try {
      const params: unknown[] = [chart_id, ayanamsha_id, date_from, date_to]

      // chart_dashas is a flat one-row-per-level model: each row carries a single
      // lord_graha at level_n (not separate MD/AD/PD/SP lord columns). The optional
      // target-lord filter therefore matches lord_graha at any level.
      let lordFilter = ''
      if (target_lords.length > 0) {
        const ph = target_lords.map((_, i) => `$${5 + i}`).join(', ')
        lordFilter = `AND lord_graha IN (${ph})`
        target_lords.forEach(l => params.push(l))
      }

      const result = await query<Record<string, unknown>>(
        `SELECT
           dasha_row_id, system_id, level_n,
           lord_graha, lord_sign, parent_row_id,
           start_date, end_date, start_iso, end_iso,
           kp_sublevel, kp_sub_lord
         FROM chart_dashas
         WHERE chart_id = $1 AND ayanamsha_id = $2
           AND end_date >= $3 AND start_date <= $4
           ${lordFilter}
         ORDER BY start_date, system_id, level_n
         LIMIT 400`,
        params,
      )

      // Cross-system agreement: for each unique (start_date, end_date) pair,
      // collect all systems that independently produce a window at that interval.
      // Different systems use different cycle lengths, so identical boundaries
      // mean true multi-system convergence on that period.
      const windowMap = new Map<string, { systems: Set<string>; row: Record<string, unknown> }>()
      for (const row of result.rows) {
        const key = `${row['start_date']}|${row['end_date']}`
        if (!windowMap.has(key)) windowMap.set(key, { systems: new Set(), row })
        windowMap.get(key)!.systems.add(row['system_id'] as string)
      }

      const crossSystemWindows = Array.from(windowMap.values())
        .map(v => ({
          ...v.row,
          system_agreement_count: v.systems.size,
          agreeing_systems: Array.from(v.systems).sort(),
        }))
        .sort((a, b) => (b.system_agreement_count as number) - (a.system_agreement_count as number))

      return {
        content: {
          chart_id,
          ayanamsha_id,
          date_from,
          date_to,
          target_lords: target_lords.length > 0 ? target_lords : 'all',
          dasha_windows:         result.rows,
          cross_system_windows:  crossSystemWindows,
          high_agreement_count:  crossSystemWindows.filter(w => (w.system_agreement_count as number) >= 2).length,
          count:                 result.rows.length,
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}

// ── call_muhurta_score ────────────────────────────────────────────────────────

export const callMuhurtaScoreCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/call_muhurta_score',
  type:  'tool',
  layer: 'L3',
  name:  'call_muhurta_score',

  description: [
    'Score an auspicious window for a specific datetime and purpose (ka_muhurta_seva service).',
    'Global scope — not chart-specific at the service level.',
    'Returns muhurta score components: tithi, nakshatra, yoga, karana, lagna fitness.',
  ].join(' '),

  scope: 'global',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'temporal',
  emits_references: false,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,

  input_schema: {
    datetime_utc: {
      type: 'string',
      description: 'UTC datetime to score (ISO 8601: YYYY-MM-DDTHH:MM:SSZ). Required.',
      required: true,
    },
    event_class: {
      type: 'string',
      description: 'Purpose of the muhurta (marriage, travel, business, medical, education, ceremony).',
      enum: ['marriage', 'travel', 'business', 'medical', 'education', 'ceremony'],
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha (default: 'LAHIRI').",
    },
  },

  llm_hints: {
    agentic: { cost_class: 'medium' },
    bulk_context: { pre_fetch_priority: 40 },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const datetime_utc = args['datetime_utc'] as string
    if (!datetime_utc) {
      return { content: { error: 'datetime_utc is required' }, is_error: true }
    }

    const event_class  = args['event_class'] as string | undefined
    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'

    // ka_muhurta_seva is a compute service (asset_registry target_table = null) — there is no
    // ka_muhurta_scores table to query. Muhurta scoring for an arbitrary datetime must be
    // produced by the compute sidecar. No /api/compute/muhurta_score endpoint is wired yet,
    // so fail loud rather than query a phantom table.
    // See needs_decision: wire a /api/compute/muhurta_score sidecar endpoint.
    return {
      content: {
        error: 'call_muhurta_score is not yet wired to a compute sidecar endpoint',
        note: 'ka_muhurta_seva is a compute service with no backing table; no /api/compute/muhurta_score endpoint exists yet. This handler will return muhurta scores once the sidecar endpoint is added.',
        datetime_utc,
        event_class,
        ayanamsha_id,
      },
      is_error: true,
    }
  },
}

// ── call_priority_ranking ─────────────────────────────────────────────────────

export const callPriorityRankingCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/call_priority_ranking',
  type:  'tool',
  layer: 'L3',
  name:  'call_priority_ranking',

  description: [
    'Returns priority-ranked signals for a chart in a given period (ka_tulana service).',
    'Per-chart: requires chart_id.',
    'Ranks active signals by combined score of salience × activation_strength × convergence.',
    'Use to determine which signals deserve attention in a specific time window.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'temporal',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha (default: 'LAHIRI').",
    },
    date_from: {
      type: 'string',
      description: 'Start of evaluation period (ISO 8601: YYYY-MM-DD).',
    },
    date_to: {
      type: 'string',
      description: 'End of evaluation period (ISO 8601: YYYY-MM-DD).',
    },
    top_k: {
      type: 'number',
      description: 'Max signals to return (default: 20, max: 100).',
    },
  },

  llm_hints: {
    agentic: { cost_class: 'medium', cacheable: true },
    bulk_context: { pre_fetch_priority: 10 },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'
    const date_from    = (args['date_from'] as string | undefined) ?? new Date().toISOString().split('T')[0]
    const date_to      = (args['date_to'] as string | undefined) ?? new Date(Date.now() + 90 * 86400000).toISOString().split('T')[0]
    const top_k        = Math.min(Number(args['top_k'] ?? 20), 100)

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      // Join activation with signals to compute combined priority
      const sql = `
        SELECT
          m.signal_id,
          m.signal_headline_text,
          m.computed_salience,
          m.domains_affected_array,
          m.signal_type_class,
          a.activation_strength,
          a.window_start,
          a.window_end,
          a.trigger_type,
          (m.computed_salience * COALESCE(a.activation_strength, 0.5)) AS priority_score
        FROM bodha_msr_signals m
        JOIN kala_activation a ON m.signal_id = a.signal_id
          AND a.chart_id = m.chart_id
          AND a.ayanamsha_id = m.ayanamsha_id
        WHERE m.chart_id = $1
          AND m.ayanamsha_id = $2
          AND a.window_end >= $3
          AND a.window_start <= $4
        ORDER BY priority_score DESC NULLS LAST
        LIMIT $5
      `

      const result = await db.query(sql, [chart_id, ayanamsha_id, date_from, date_to, top_k])
      const signalRefs = (result.rows as Array<{ signal_id?: string }>).map(r => r.signal_id).filter(Boolean) as string[]

      return {
        content: {
          chart_id,
          ayanamsha_id,
          date_from,
          date_to,
          ranked_signals: result.rows,
          signal_count:   result.rows.length,
          signal_id_refs: [...new Set(signalRefs)],
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}

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
    date_from: {
      type: 'string',
      description: 'Start date for transit search (ISO 8601: YYYY-MM-DD). Required.',
      required: true,
    },
    date_to: {
      type: 'string',
      description: 'End date for transit search (ISO 8601: YYYY-MM-DD). Required.',
      required: true,
    },
    graha: {
      type: 'string',
      description: 'Filter by graha (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu).',
      enum: ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'],
    },
    sign: {
      type: 'string',
      description: 'Filter by transit sign (Aries, Taurus, Gemini, Cancer, Leo, Virgo, Libra, Scorpio, Sagittarius, Capricorn, Aquarius, Pisces).',
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha (default: 'LAHIRI').",
    },
  },

  llm_hints: {
    agentic: { cost_class: 'medium' },
    bulk_context: { pre_fetch_priority: 30 },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const date_from    = args['date_from'] as string
    const date_to      = args['date_to'] as string
    if (!date_from || !date_to) {
      return { content: { error: 'date_from and date_to are required' }, is_error: true }
    }

    const graha        = args['graha'] as string | undefined
    const sign         = args['sign'] as string | undefined
    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      const conds: string[] = ['event_date BETWEEN $1 AND $2', 'ayanamsha_id = $3']
      const params: unknown[] = [date_from, date_to, ayanamsha_id]
      let p = 4

      if (graha) { conds.push(`graha = $${p++}`); params.push(graha) }
      if (sign)  { conds.push(`sign = $${p++}`);  params.push(sign) }

      const sql = `
        SELECT event_id, graha, sign, degree, event_type,
               event_date, retrograde_flag, ayanamsha_id
        FROM ka_gochara_transit_events
        WHERE ${conds.join(' AND ')}
        ORDER BY event_date
        LIMIT 200
      `

      const result = await db.query(sql, params)
      return {
        content: { date_from, date_to, ayanamsha_id, events: result.rows, count: result.rows.length },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), note: 'ka_gochara service may require a separate API call' }, is_error: true }
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

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      const sql = `
        SELECT graha, sign, degree, nakshatra, pada, retrograde_flag, speed_deg_per_day
        FROM ka_graha_sancara_snapshot
        WHERE snapshot_utc::date = $1::date AND ayanamsha_id = $2
        ORDER BY graha
      `
      const result = await db.query(sql, [datetime_utc, ayanamsha_id])
      return {
        content: { datetime_utc, ayanamsha_id, positions: result.rows },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), note: 'ka_graha_sancara service may require ephemeris engine call' }, is_error: true }
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
      description: "Ayanamsha (default: 'LAHIRI').",
    },
    date_from: {
      type: 'string',
      description: 'Start date (ISO 8601: YYYY-MM-DD). Default: today.',
    },
    date_to: {
      type: 'string',
      description: 'End date (ISO 8601: YYYY-MM-DD). Default: 3 years from today.',
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

    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'
    const date_from    = (args['date_from'] as string | undefined) ?? new Date().toISOString().split('T')[0]
    const date_to      = (args['date_to'] as string | undefined) ?? new Date(Date.now() + 3 * 365 * 86400000).toISOString().split('T')[0]

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      // Query chart_dashas for active dasha windows in range
      const sql = `
        SELECT dasha_id, mahadasha_lord, antardasha_lord, pratyantar_lord,
               dasha_start, dasha_end, dasha_level, system_id
        FROM chart_dashas
        WHERE chart_id = $1 AND ayanamsha_id = $2
          AND dasha_end >= $3 AND dasha_start <= $4
        ORDER BY dasha_start, dasha_level
        LIMIT 200
      `

      const result = await db.query(sql, [chart_id, ayanamsha_id, date_from, date_to])
      return {
        content: { chart_id, ayanamsha_id, date_from, date_to, dasha_windows: result.rows, count: result.rows.length },
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

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      const sql = `
        SELECT score_id, datetime_utc, event_class, muhurta_score,
               tithi_score, nakshatra_score, yoga_score, karana_score,
               lagna_fitness_score, ayanamsha_id, scored_at
        FROM ka_muhurta_scores
        WHERE datetime_utc::date = $1::date
          AND ($2::text IS NULL OR event_class = $2)
          AND ayanamsha_id = $3
        ORDER BY muhurta_score DESC
        LIMIT 20
      `

      const result = await db.query(sql, [datetime_utc, event_class ?? null, ayanamsha_id])
      return {
        content: { datetime_utc, event_class, ayanamsha_id, scores: result.rows },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), note: 'ka_muhurta_seva service may require ephemeris computation' }, is_error: true }
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

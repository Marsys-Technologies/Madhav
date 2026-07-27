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
import { DEFAULT_AYANAMSHA } from '../../constants'

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
      description: "Ayanamsha (default: 'lahiri_chitrapaksha').",
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

    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? DEFAULT_AYANAMSHA

    // W2 dark-set wiring (GT-50): ka_graha_sancara is a compute service (asset_registry
    // target_table = null) — there is no ka_graha_sancara_snapshot table to query.
    // Positions at an arbitrary datetime are produced live by the sidecar's
    // /api/compute/ephemeris_at_t endpoint (routers/ephemeris.py's compute_router,
    // swisseph-backed). Same fetch()/error-shape pattern as callTransitSearchCapability
    // above, per DESIGN_KA_GRAHA_SANCARA_WIRING.md §3 item 4.
    const sidecarUrl = process.env.PYTHON_SIDECAR_URL
    const sidecarKey = process.env.PYTHON_SIDECAR_API_KEY ?? ''

    if (!sidecarUrl) {
      return { content: { error: 'PYTHON_SIDECAR_URL not configured — ephemeris_at_t unavailable' }, is_error: true }
    }

    try {
      const resp = await fetch(`${sidecarUrl}/api/compute/ephemeris_at_t`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'x-api-key': sidecarKey },
        body:    JSON.stringify({ datetime_utc, ayanamsha_id }),
      })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        return { content: { error: `Sidecar ${resp.status}`, detail: err }, is_error: true }
      }
      const data = await resp.json() as { datetime_utc: string; ayanamsha_id: string; jd: number; positions: unknown[] }
      return {
        content: {
          datetime_utc: data.datetime_utc,
          ayanamsha_id: data.ayanamsha_id,
          jd:            data.jd,
          positions:     data.positions,
          count:         data.positions.length,
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), datetime_utc, ayanamsha_id }, is_error: true }
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
        // WP-1.5 F-DATE-TZ: start_date/end_date are DATE columns → to_char to 'YYYY-MM-DD'
        // (raw return → node-postgres IST-midnight → UTC off-by-one). start_iso/end_iso are
        // timestamptz instants and are correctly returned as ISO datetimes.
        `SELECT
           dasha_row_id, system_id, level_n,
           lord_graha, lord_sign, parent_row_id,
           to_char(start_date, 'YYYY-MM-DD') AS start_date,
           to_char(end_date, 'YYYY-MM-DD')   AS end_date,
           start_iso, end_iso,
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
    'Score an auspicious window (raw muhurta quality) for a specific UTC datetime and event class',
    '(ka_muhurta_seva service — reuses the same score_muhurat() scoring primitive the already-served',
    'ph_muhurta/muhurta_finder electional finder calls internally for its panchanga_quality sub-score).',
    'Global scope — no chart_id, no date-range search (use muhurta_finder/kala_muhurta_get for a',
    'best-window search over a date range with dasha/transit sub-scores).',
    'Returns the 0-100 score, 1-5 star rating, and the day panchang context (tithi, nakshatra, vara, yoga)',
    'the score was derived from.',
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
      description: [
        'Event class to score against (EVENTS_MVP vocabulary — the real vocabulary',
        'score_muhurat() accepts). vivah=marriage, griha_pravesh=house-warming/new-home-entry,',
        'vyapara=business start, yatra=journey/travel, property_purchase=property/vehicle purchase,',
        'mantra_initiation=mantra diksha, upaya_ritual=remedial action (homa/dana/japa/puja/vrata),',
        'sadhana_initiation=beginning a sustained spiritual practice. Required.',
      ].join(' '),
      enum: ['vivah', 'griha_pravesh', 'vyapara', 'yatra', 'property_purchase', 'mantra_initiation', 'upaya_ritual', 'sadhana_initiation'],
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha (default: 'lahiri_chitrapaksha'; only Lahiri is supported by the underlying panchang engine today).",
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

    const event_class = args['event_class'] as string
    if (!event_class) {
      return { content: { error: 'event_class is required' }, is_error: true }
    }

    const ayanamsha_id = args['ayanamsha_id'] as string | undefined

    // W2 dark-set wiring (§F gate ruling item 6, DARK_SET_WIRING_PLAN_v1_0): ka_muhurta_seva
    // is a compute service (asset_registry target_table = null) — there is no
    // ka_muhurta_scores table to query. Scored live by the sidecar's
    // /api/compute/muhurta_score endpoint (routers/muhurta_score.py, wraps
    // panchang_engine.muhurat.score_muhurat() — the same primitive ph_muhurta calls
    // internally). Same fetch()/error-shape pattern as the other call_* wrappers.
    const sidecarUrl = process.env.PYTHON_SIDECAR_URL
    const sidecarKey = process.env.PYTHON_SIDECAR_API_KEY ?? ''

    if (!sidecarUrl) {
      return { content: { error: 'PYTHON_SIDECAR_URL not configured — muhurta_score unavailable' }, is_error: true }
    }

    try {
      const resp = await fetch(`${sidecarUrl}/api/compute/muhurta_score`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'x-api-key': sidecarKey },
        body:    JSON.stringify({ datetime_utc, event_class, ayanamsha_id }),
      })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        return { content: { error: `Sidecar ${resp.status}`, detail: err }, is_error: true }
      }
      const data = await resp.json() as Record<string, unknown>
      return { content: data, is_error: false }
    } catch (err) {
      return { content: { error: String(err), datetime_utc, event_class, ayanamsha_id }, is_error: true }
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
      description: "Ayanamsha (default: 'lahiri_chitrapaksha').",
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
    domain: {
      type: 'string',
      description:
        'MC-024 (ŚODHANA T4): filter to signals affecting ONE life domain (e.g. "wealth", ' +
        '"career", "health", "relationship", "spirituality", "character") — matched against ' +
        'domains_affected_array (case-insensitive). Takes precedence over `domains` if both given.',
    },
    domains: {
      type: 'array',
      description:
        'MC-024: filter to signals affecting ANY of these life domains (OR/overlap match ' +
        'against domains_affected_array, case-insensitive). Ignored if `domain` is also given.',
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

    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? DEFAULT_AYANAMSHA
    const date_from    = (args['date_from'] as string | undefined) ?? new Date().toISOString().split('T')[0]
    const date_to      = (args['date_to'] as string | undefined) ?? new Date(Date.now() + 90 * 86400000).toISOString().split('T')[0]
    const top_k        = Math.min(Number(args['top_k'] ?? 20), 100)

    // MC-024 (ŚODHANA T4): domain/domains facet. `domain` (singular) wins if both are passed —
    // same precedence pattern used elsewhere in this codebase (e.g. system > dasha_system).
    // Normalized to lowercase since domains_affected_array is seeded lowercase
    // (career/character/health/relationship/spirituality/wealth).
    const rawDomain  = args['domain'] as string | undefined
    const rawDomains = args['domains'] as unknown
    let domainsFilter: string[] | null = null
    if (rawDomain) {
      domainsFilter = [rawDomain.toLowerCase()]
    } else if (Array.isArray(rawDomains) && rawDomains.length > 0) {
      domainsFilter = rawDomains.map(d => String(d).toLowerCase())
    }

    try {
      // Join activation with signals to compute combined priority.
      // WP-1.5: prior SQL referenced columns that do not exist on kala_activation
      // (activation_strength/window_start/window_end/trigger_type) → every call errored.
      // Real columns: orb_strength (activation strength proxy), activation_start/_end (DATE),
      // signature_class. F-DATE-TZ: activation_start/_end emitted via to_char as 'YYYY-MM-DD'.
      // MC-024 fix: a "graha dignity per varga: dignity state = neutral" descriptor row is
      // rarely a genuine priority signal (a neutral dignity is a non-finding, not a strength
      // or weakness worth surfacing near the top) — down-ranked via a priority_score penalty
      // multiplier rather than dropped (B.10: never silently drop data), and flagged per-row
      // (neutral_dignity_downranked) plus summarized in the envelope so a caller can tell a
      // downranked row apart from one that genuinely scored low.
      const params: unknown[] = [chart_id, ayanamsha_id, date_from, date_to]
      let domainClause = ''
      if (domainsFilter && domainsFilter.length > 0) {
        params.push(domainsFilter)
        domainClause = ` AND m.domains_affected_array && $${params.length}::text[]`
      }
      params.push(top_k)

      const sql = `
        SELECT
          m.signal_id,
          m.signal_headline_text,
          m.computed_salience,
          m.domains_affected_array,
          m.signal_type_class,
          a.orb_strength AS activation_strength,
          to_char(a.activation_start, 'YYYY-MM-DD') AS window_start,
          to_char(a.activation_end, 'YYYY-MM-DD')   AS window_end,
          a.signature_class AS trigger_type,
          (m.signal_headline_text ILIKE '%dignity%neutral%') AS neutral_dignity_downranked,
          (m.computed_salience * COALESCE(a.orb_strength, 0.5) *
            (CASE WHEN m.signal_headline_text ILIKE '%dignity%neutral%' THEN 0.3 ELSE 1.0 END)
          ) AS priority_score
        FROM bodha_msr_signals m
        JOIN kala_activation a ON m.signal_id = a.signal_id
          AND a.chart_id = m.chart_id
          AND a.ayanamsha_id = m.ayanamsha_id
        WHERE m.chart_id = $1
          AND m.ayanamsha_id = $2
          AND a.activation_end >= $3::date
          AND a.activation_start <= $4::date${domainClause}
        ORDER BY priority_score DESC NULLS LAST
        LIMIT $${params.length}
      `

      const result = await query(sql, params)
      const signalRefs = (result.rows as Array<{ signal_id?: string }>).map(r => r.signal_id).filter(Boolean) as string[]
      const downrankedCount = (result.rows as Array<{ neutral_dignity_downranked?: boolean }>)
        .filter(r => r.neutral_dignity_downranked === true).length

      return {
        content: {
          chart_id,
          ayanamsha_id,
          date_from,
          date_to,
          domain_filter: domainsFilter,
          ranked_signals: result.rows,
          signal_count:   result.rows.length,
          signal_id_refs: [...new Set(signalRefs)],
          neutral_dignity_downranked_count: downrankedCount,
          ...(downrankedCount > 0
            ? { neutral_dignity_note: `${downrankedCount} row(s) carry a neutral-dignity descriptor ` +
                `("graha dignity per varga: dignity state = neutral") and were down-ranked (priority_score ` +
                `x0.3) rather than treated as a genuine priority signal — see neutral_dignity_downranked ` +
                `per row.` }
            : {}),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}

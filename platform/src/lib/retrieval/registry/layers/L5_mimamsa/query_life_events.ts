/**
 * query_life_events — LEL intake surface (L5 Mīmāṃsā); MCP name `lel_query`
 * ==========================================================================
 * WP-1.3(d) / F-L10-021. Serves the native's user-authored life events from the
 * chart-scoped `life_events` table (57 rows for the canonical chart), with usable
 * fields (date, description, domain, category, significance, source, outcome).
 *
 * WHY THIS EXISTS (the bug it fixes): `lel_query` was mapped (TOOL_NAME_TO_URI) to
 * `marsys://tool/L2/query_signals` — the Bodha MSR signals surface — whose
 * `lel_enabled` filter selects `lel_origin=true` MSR signals, of which there are
 * currently ZERO. So `lel_query` returned nothing/partial. The Life Event Log is a
 * DIFFERENT corpus: rows in `life_events`, not signals in `bodha_msr_signals`.
 * `lel_query` now resolves here.
 *
 * NO-LEAKAGE (mirrors platform-mcp/mimamsa_lel_intake.ts): the LEL is a calibration
 * corpus — observed outcomes fed to L5 calibration AFTER the fact, never an input to
 * prediction generation. This tool only READS; it is a serving surface.
 *
 * Chart-scoped + per_chart (principle #14): `life_events.chart_id` is the entitlement
 * key; the primitives route enforces authorizeChartAccess before this handler runs.
 */

import type { CapabilityDescriptor } from '../../index'
import { query } from '@/lib/db/client'

/** Hard cap on served rows — bounded serving (WP-1.3 constraint). */
const MAX_LIMIT = 50

export const queryLifeEventsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/lel_query',
  type:  'tool',
  layer: 'L5',
  name:  'lel_query',

  description: [
    'Query the native\'s user-authored Life Event Log (LEL) for a chart — the observed',
    'life events used by the L5 Mīmāṃsā calibration loop. Reads the chart-scoped',
    'life_events table (NOT MSR signals). Returns event_id, event_date, description,',
    'domain, category, significance, event_type, source, and outcome_observed.',
    'Filters: category, domain, significance, start_date, end_date. Bounded to 50 rows.',
    'NO-LEAKAGE: life_events is a calibration corpus only — it must never feed prediction',
    'generation; consume it only to score predictions against observed reality.',
  ].join(' '),

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID. Required.',
      required: true,
    },
    category: {
      type: 'string',
      description: "Filter by life event category (e.g. 'career', 'health', 'relationship', 'family', 'finance'). Omit for all.",
      required: false,
    },
    domain: {
      type: 'string',
      description: "Filter by life domain (career, wealth, relationship, health, etc.). Omit for all.",
      required: false,
    },
    significance: {
      type: 'string',
      description: "Filter by significance level ('major'|'moderate'|'minor'). Omit for all.",
      required: false,
    },
    start_date: {
      type: 'string',
      description: 'Include events on or after this date (YYYY-MM-DD).',
      required: false,
    },
    end_date: {
      type: 'string',
      description: 'Include events on or before this date (YYYY-MM-DD).',
      required: false,
    },
    limit: {
      type: 'number',
      description: `Max events to return (default: 50, max: ${MAX_LIMIT}).`,
      required: false,
    },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'calibration',
  traversal_level: 'L-SIGNAL',
  tool_role: 'quality',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: true,

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable: true,
    },
    bulk_context: {
      pre_fetch_priority: 3,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const category     = args['category'] ? String(args['category']) : null
    const domain       = args['domain'] ? String(args['domain']) : null
    const significance = args['significance'] ? String(args['significance']) : null
    const start_date   = args['start_date'] ? String(args['start_date']) : null
    const end_date     = args['end_date'] ? String(args['end_date']) : null
    const limit        = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2

    if (category)     { filters.push(`category = $${p++}`);      params.push(category) }
    if (domain)       { filters.push(`domain = $${p++}`);        params.push(domain) }
    if (significance) { filters.push(`significance = $${p++}`);  params.push(significance) }
    if (start_date)   { filters.push(`event_date >= $${p++}`);   params.push(start_date) }
    if (end_date)     { filters.push(`event_date <= $${p++}`);   params.push(end_date) }

    const where = filters.join(' AND ')

    // D5 coverage receipt: family size BEFORE the LIMIT, same filters as the page.
    const countPromise = query<{ total: string }>(
      `SELECT COUNT(*)::text AS total FROM life_events WHERE ${where}`,
      [...params],
    )

    const eventsParams = [...params, limit]
    const eventsSql = `
      SELECT event_id, event_date, category, domain, description, significance,
             event_type, source_citation, source_section, outcome_observed
      FROM life_events
      WHERE ${where}
      ORDER BY event_date ASC
      LIMIT $${p}
    `

    try {
      const [eventsResult, countResult] = await Promise.all([
        query(eventsSql, eventsParams),
        countPromise,
      ])
      const total_matching = Number(countResult.rows[0]?.total ?? 0)

      return {
        content: {
          chart_id,
          events: eventsResult.rows,
          count: eventsResult.rows.length,
          total_matching,
          filters: { category, domain, significance, start_date, end_date, limit },
          provenance: {
            tables: ['life_events'],
            no_leakage_note:
              'life_events is a calibration corpus only — must not feed prediction generation.',
            source: 'LIFE_EVENT_LOG (user-authored); served chart-scoped.',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}

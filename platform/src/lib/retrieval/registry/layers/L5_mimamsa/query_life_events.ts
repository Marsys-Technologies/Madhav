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
    'Filters: category, domain, significance, start_date, end_date, query (case-insensitive',
    'substring text search over description/domain/category/event_type/source_citation —',
    'multi-word queries require every word to match, AND semantics). Paginate with',
    'limit + offset. Bounded to 50 rows per page.',
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
    query: {
      type: 'string',
      description: 'Case-insensitive text search over description/domain/category/event_type/source_citation. Whitespace-separated words all must match (AND semantics). Omit for no text filter.',
      required: false,
    },
    limit: {
      type: 'number',
      description: `Max events to return per page (default: 50, max: ${MAX_LIMIT}).`,
      required: false,
    },
    offset: {
      type: 'number',
      description: 'Rows to skip before the page starts (pagination; default: 0).',
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
    const rawQuery     = typeof args['query'] === 'string' ? args['query'].trim() : ''
    const search_query = rawQuery.length > 0 ? rawQuery : null
    const limit        = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)
    const offsetInput  = Number(args['offset'] ?? 0)
    const offset       = Number.isFinite(offsetInput) ? Math.max(Math.trunc(offsetInput), 0) : 0

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2

    if (category)     { filters.push(`category = $${p++}`);      params.push(category) }
    if (domain)       { filters.push(`domain = $${p++}`);        params.push(domain) }
    if (significance) { filters.push(`significance = $${p++}`);  params.push(significance) }
    if (start_date)   { filters.push(`event_date >= $${p++}`);   params.push(start_date) }
    if (end_date)     { filters.push(`event_date <= $${p++}`);   params.push(end_date) }

    // WP-B1 F-LEL-NOOP: `query` was accepted into the schema and forwarded verbatim by
    // the mimamsa_lel_query alias but never read here — every call returned the same
    // byte-identical page regardless of search text. Wire it as a case-insensitive
    // substring (ILIKE) search over the descriptive text columns, split on whitespace
    // with AND semantics (every word must match somewhere), so a non-matching query
    // honestly narrows to zero rows instead of silently ignoring the filter.
    if (search_query) {
      const words = search_query.split(/\s+/).filter(Boolean)
      for (const word of words) {
        filters.push(
          `(description ILIKE $${p} OR domain ILIKE $${p} OR category ILIKE $${p} ` +
          `OR event_type ILIKE $${p} OR source_citation ILIKE $${p})`,
        )
        params.push(`%${word}%`)
        p++
      }
    }

    const where = filters.join(' AND ')

    // D5 coverage receipt: family size BEFORE the LIMIT/OFFSET, same filters as the page.
    const countPromise = query<{ total: string }>(
      `SELECT COUNT(*)::text AS total FROM life_events WHERE ${where}`,
      [...params],
    )

    const limitParamIdx  = p
    const offsetParamIdx = p + 1
    const eventsParams = [...params, limit, offset]
    // WP-1.5 F-DATE-TZ: event_date is a DATE column — to_char to 'YYYY-MM-DD' (raw return →
    // node-postgres IST-midnight → UTC off-by-one, e.g. a 1990-05-14 event → "1990-05-13...Z").
    // WP-B1 F-LEL-NOOP: OFFSET now wired to `offset` — previously accepted+forwarded but
    // never applied, so every page (regardless of offset) returned the same first rows.
    const eventsSql = `
      SELECT event_id, to_char(event_date, 'YYYY-MM-DD') AS event_date,
             category, domain, description, significance,
             event_type, source_citation, source_section, outcome_observed
      FROM life_events
      WHERE ${where}
      ORDER BY event_date ASC, event_id ASC
      LIMIT $${limitParamIdx}
      OFFSET $${offsetParamIdx}
    `

    try {
      const [eventsResult, countResult] = await Promise.all([
        query(eventsSql, eventsParams),
        countPromise,
      ])
      const total_matching = Number(countResult.rows[0]?.total ?? 0)
      const count = eventsResult.rows.length
      // Honest end-of-results indicator (WP-B1 F-LEL-NOOP): lets a caller paging with
      // `offset` know whether another page exists rather than guessing from `count`.
      const has_more = offset + count < total_matching

      return {
        content: {
          chart_id,
          events: eventsResult.rows,
          count,
          total_matching,
          has_more,
          filters: { category, domain, significance, start_date, end_date, query: search_query, limit, offset },
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

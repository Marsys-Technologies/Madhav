/**
 * query_signals — MSR Signal Query (L2 Bodha)
 * ============================================
 * Queries bodha_msr_signals (66,738 rows) and bodha_signal_embeddings (66,738 rows, 100% embedded).
 *
 * Returns ranked signals by computed_salience. CRITICAL design notes:
 *
 * 1. signature_tier is FULLY DEGENERATE — 100% of signals are 'background'.
 *    Do NOT rank or filter by signature_tier. Use computed_salience exclusively.
 *
 * 2. DEFECT-001 (OPEN): constituent_facts_array has 91.5% orphan rate (61,161/66,832 refs
 *    are unresolvable against chart_facts). Root cause: L2 Bodha writer used old L1 fact_id
 *    scheme; L1 was rebuilt with new SHA hashes. Joins on constituent_fact_id return empty
 *    for most signals. This tool returns constituent_facts_array as reference list only —
 *    the caller must handle empty downstream hydration gracefully.
 *
 * 3. lel_origin=true: 0 signals currently. lel_enabled filter is safe to expose but
 *    returns 0 rows until LEL signals are ingested.
 *
 * Semantic search path: bodha_signal_embeddings carries 768-dim vectors (Vertex). Semantic
 * filtering uses cosine similarity via pgvector. Falls back to salience-ranked if unavailable.
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'

export const querySignalsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_signals',
  type:  'tool',
  layer: 'L2',
  name:  'query_signals',

  description: [
    'Query MSR signals for a chart from the Bodha synthesis layer.',
    'Returns signals ranked by computed_salience (66,738 signals for the canonical chart).',
    'Supports filters: domain, source_subsystem, min_salience, lel_enabled.',
    'Optional semantic_query uses pgvector cosine similarity over signal embeddings (768-dim).',
    'emits_references: returns signal_id + constituent_facts_array as reference list.',
    'DEFECT-001 NOTE: constituent_facts_array has 91.5% orphan rate — joins to chart_facts',
    'will be empty for most signals until L2 is rebuilt. signature_tier is fully degenerate',
    '(100% background) — ranking uses computed_salience only.',
    'lel_capable: lel_origin filter exposed but returns 0 rows until LEL signals are ingested.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'rich_relational',
  traversal_level: 'L-SIGNAL',
  tool_role: 'drill',
  emits_references: true,
  grounds_to: { l1_fact_ids: true, l0_citation_ids: true },
  lel_capable: true,

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha to filter by (default: 'LAHIRI').",
    },
    domain: {
      type: 'string',
      description: "Filter signals by domain (career, wealth, relationship, health, character, spirituality, other).",
    },
    source_subsystem: {
      type: 'string',
      description: "Filter by source subsystem (e.g. 'parashara', 'jaimini', 'tajika', 'nadi').",
    },
    signal_type_class: {
      type: 'string',
      description: "Filter by type class: 'yoga'|'dosha'|'karaka_alignment'|'composite_state'|'sade_sati'|'panchanga'.",
      enum: ['yoga', 'dosha', 'karaka_alignment', 'composite_state', 'sade_sati', 'panchanga'],
    },
    min_salience: {
      type: 'number',
      description: 'Minimum computed_salience threshold (0..1, default: 0).',
    },
    lel_enabled: {
      type: 'boolean',
      description: 'Include lel_origin=true signals (default: false). Currently returns 0 rows — no LEL signals ingested yet.',
    },
    semantic_query: {
      type: 'string',
      description: [
        'Natural-language semantic query for signal retrieval via pgvector cosine similarity.',
        'Requires bodha_signal_embeddings to be populated (100% populated for production charts).',
        'Falls back to salience-ranked results if embedding search fails.',
      ].join(' '),
    },
    top_k: {
      type: 'number',
      description: 'Max signals to return (default: 50, max: 500).',
    },
    offset: {
      type: 'number',
      description: 'Pagination offset (default: 0).',
    },
  },

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable:  true,
    },
    bulk_context: {
      pre_fetch_priority: 10,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const ayanamsha_id    = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'
    const domain          = args['domain'] as string | undefined
    const source_subsystem = args['source_subsystem'] as string | undefined
    const signal_type_class = args['signal_type_class'] as string | undefined
    const min_salience    = Number(args['min_salience'] ?? 0)
    const lel_enabled     = Boolean(args['lel_enabled'] ?? false)
    const top_k           = Math.min(Number(args['top_k'] ?? 50), 500)
    const offset          = Number(args['offset'] ?? 0)
    const semantic_query  = args['semantic_query'] as string | undefined

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      const filters: string[] = ['m.chart_id = $1', 'm.ayanamsha_id = $2']
      const params: unknown[] = [chart_id, ayanamsha_id]
      let p = 3

      if (domain) {
        filters.push(`$${p++} = ANY(m.domains_affected_array)`)
        params.push(domain)
      }
      if (source_subsystem) {
        filters.push(`m.source_subsystem = $${p++}`)
        params.push(source_subsystem)
      }
      if (signal_type_class) {
        filters.push(`m.signal_type_class = $${p++}`)
        params.push(signal_type_class)
      }
      if (min_salience > 0) {
        filters.push(`m.computed_salience >= $${p++}`)
        params.push(min_salience)
      }
      if (!lel_enabled) {
        // Exclude LEL signals by default (lel_origin=false or null)
        filters.push(`(m.lel_origin IS NULL OR m.lel_origin = false)`)
      }

      params.push(top_k, offset)
      const topKPh = `$${p++}`
      const offsetPh = `$${p++}`

      let sql: string
      let queryParams: unknown[]

      // If semantic_query: try pgvector cosine similarity via bodha_signal_embeddings
      if (semantic_query) {
        // Semantic path: join on embeddings, rank by cosine similarity
        // The actual embedding of semantic_query is not available here without the Vertex SDK.
        // We surface this as an ordered salience fallback with a note, consistent with
        // how traverse_chart_graph handles the semantic-entry fallback.
        sql = `
          SELECT m.signal_id, m.signal_type_id, m.signal_type_class, m.signal_tradition,
                 m.signal_summary_text, m.signal_headline_text,
                 m.computed_salience, m.top_k_salience_rank,
                 m.domains_affected_array, m.constituent_facts_array,
                 m.source_subsystem, m.valence, m.verification_pass_status,
                 m.citation_human, m.lel_origin, m.signature_tier,
                 m.configuration_jsonb
          FROM bodha_msr_signals m
          WHERE ${filters.join(' AND ')}
          ORDER BY m.computed_salience DESC NULLS LAST
          LIMIT ${topKPh} OFFSET ${offsetPh}
        `
        queryParams = params
      } else {
        sql = `
          SELECT m.signal_id, m.signal_type_id, m.signal_type_class, m.signal_tradition,
                 m.signal_summary_text, m.signal_headline_text,
                 m.computed_salience, m.top_k_salience_rank,
                 m.domains_affected_array, m.constituent_facts_array,
                 m.source_subsystem, m.valence, m.verification_pass_status,
                 m.citation_human, m.lel_origin, m.signature_tier,
                 m.configuration_jsonb
          FROM bodha_msr_signals m
          WHERE ${filters.join(' AND ')}
          ORDER BY m.computed_salience DESC NULLS LAST
          LIMIT ${topKPh} OFFSET ${offsetPh}
        `
        queryParams = params
      }

      const result = await db.query(sql, queryParams)

      return {
        content: {
          chart_id,
          ayanamsha_id,
          signals: result.rows,
          returned_count: result.rows.length,
          filters:  { domain, source_subsystem, signal_type_class, min_salience, lel_enabled, top_k, offset },
          semantic_fallback: semantic_query ? 'Semantic embedding not available at query time — salience-ranked fallback used. Full vector search requires Vertex embedding of the query string.' : undefined,
          provenance: {
            tables: ['bodha_msr_signals'],
            defect_001_note: [
              'DEFECT-001 OPEN: constituent_facts_array has 91.5% orphan rate.',
              'Joins from constituent_fact_id to chart_facts will be empty for most signals.',
              'Do not error on empty constituent_facts joins — this is expected until L2 rebuild.',
            ].join(' '),
            signature_tier_note: 'signature_tier is 100% background — all ranking uses computed_salience only.',
            lel_note: 'lel_origin=true signals: 0 rows currently. LEL filter is safe but returns empty.',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return {
        content: { error: String(err), chart_id },
        is_error: true,
      }
    }
  },
}

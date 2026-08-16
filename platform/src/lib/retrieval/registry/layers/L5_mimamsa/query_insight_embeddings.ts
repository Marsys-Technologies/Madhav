/**
 * query_insight_embeddings — L5 Mīmāṃsā insight-embedding nearest-neighbor lookup
 * ========================================================================================
 * W2b Batch 4 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `mimamsa_insight_embeddings`, migration 353_mimamsa_darshana.sql, 768-dim ivfflat).
 *
 * IMPORTANT — this genuinely needed a NEW serving path, not the generic `vector_search`
 * alias. TABLE_CONCEPT_DISPOSITIONS_v2_0.md §6 found that the native's own blanket
 * "embedding tables = SERVED-VIA(vector_search)" pre-ruling does NOT hold for this table:
 * `vector_search` resolves only to `marsys://tool/L0/query_classical_texts` (a classical-
 * texts corpus search hardcoded to a different table). This tool is the real, dedicated
 * path — same shape as `bodha_signal_embeddings`'s own dedicated path in `query_signals.ts`
 * (not via the generic alias either).
 *
 * Design, honestly scoped: there is no live text-embedding service call anywhere in this
 * codebase at query time (confirmed — `query_signals.ts`'s own semantic_query path falls
 * back to a non-embedding ranking for the same reason: "Vertex embedding not available at
 * query time"). Embedding an arbitrary natural-language query string here would be
 * fabricated computation (B.10). Instead this tool exposes the two REAL, non-fabricated
 * uses of an already-populated embedding table: (1) direct row lookup by insight_id
 * (embed_model_version + embedded_at — provenance, not the raw vector, which is not
 * human-readable content), and (2) nearest-neighbor search FROM one already-embedded
 * insight TO its neighbors via pgvector's `<=>` cosine-distance operator — a real
 * comparison between two already-computed vectors, not a fabricated one.
 *
 * B.10 HONESTY NOTE: mimamsa_insight_embeddings holds 0 rows on the live chart at the
 * time of this wiring pass (confirmed via direct read-only DB check) — its sibling
 * mimamsa_insight_units (the human-readable statements this table embeds) is also
 * currently unpopulated. This is a genuine, not-yet-populated concept (same reasoning
 * already applied elsewhere in this pass to bodha_rm_dasha_windowed_prescriptions /
 * bodha_rm_dosha_remedy_bundles) — wiring now means the serving path is live the moment
 * mi_darshana's writer populates both tables.
 *
 * Chart-scoped. Bounded serving with disclosed total.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 20

export const queryInsightEmbeddingsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/query_insight_embeddings',
  type:  'tool',
  layer: 'L5',
  name:  'query_insight_embeddings',

  description: [
    'Look up embedding provenance for mimamsa_insight_units rows (mi_darshana), or find',
    'the nearest-neighbor insights to a given already-embedded insight_id via pgvector',
    'cosine distance. mode=lookup (default): returns embed_model_version/embedded_at for',
    'the given insight_id (never the raw 768-dim vector — not human-readable content).',
    'mode=nearest: requires seed_insight_id; returns the top-K nearest OTHER insight_ids',
    'by cosine distance, joined to mimamsa_insight_units for their statement/insight_type.',
    'Does NOT embed arbitrary text at query time (no live embedding service exists in this',
    'codebase — see query_signals.ts semantic_query for the same honest limitation).',
  ].join(' '),

  input_schema: {
    chart_id:        { type: 'string', description: 'Chart UUID. Required.', required: true },
    mode:             { type: 'string', description: 'lookup (default) or nearest.', enum: ['lookup', 'nearest'] },
    insight_id:       { type: 'string', description: 'Required for mode=lookup.' },
    seed_insight_id:  { type: 'string', description: 'Required for mode=nearest — the already-embedded insight to search neighbors of.' },
    top_k:            { type: 'number', description: `mode=nearest: max neighbors to return (default 10, max ${MAX_LIMIT}).` },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'calibration',
  traversal_level: 'L-SIGNAL',
  tool_role: 'quality',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'medium', cacheable: true },
    bulk_context: { pre_fetch_priority: 10, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const mode = args['mode'] ? String(args['mode']) : 'lookup'

    try {
      if (mode === 'lookup') {
        const insightId = args['insight_id'] ? String(args['insight_id']) : ''
        if (!insightId) return { content: { error: 'insight_id is required for mode=lookup' }, is_error: true }

        const sql = `
          SELECT insight_id, embed_model_version, embedded_at
          FROM mimamsa_insight_embeddings
          WHERE chart_id = $1 AND insight_id = $2`
        const result = await query(sql, [chart_id, insightId])
        return {
          content: {
            chart_id,
            mode,
            rows: result.rows,
            count: result.rows.length,
            ...(result.rows.length === 0
              ? { empty_reason: `No embedding row for insight_id=${insightId} on this chart. This table may not yet be populated by its writer for this chart's build.` }
              : {}),
            provenance: { tables: ['mimamsa_insight_embeddings'], source: 'L5 Mīmāṃsā insight-embedding provenance lookup (raw vector never returned); served chart-scoped.' },
          },
          is_error: false,
        }
      }

      if (mode === 'nearest') {
        const seedId = args['seed_insight_id'] ? String(args['seed_insight_id']) : ''
        if (!seedId) return { content: { error: 'seed_insight_id is required for mode=nearest' }, is_error: true }
        const topK = Math.min(Math.max(Number(args['top_k'] ?? 10), 1), MAX_LIMIT)

        const sql = `
          SELECT n.insight_id, (n.embedding <=> s.embedding) AS cosine_distance,
                 u.insight_type, u.statement, u.rank_consequence, u.evidence_grade
          FROM mimamsa_insight_embeddings n
          JOIN mimamsa_insight_embeddings s
            ON s.chart_id = n.chart_id AND s.insight_id = $2
          LEFT JOIN mimamsa_insight_units u
            ON u.chart_id = n.chart_id AND u.insight_id = n.insight_id
          WHERE n.chart_id = $1 AND n.insight_id != $2
          ORDER BY cosine_distance ASC
          LIMIT $3`
        const result = await query(sql, [chart_id, seedId, topK])
        const rows = (result.rows as Array<Record<string, unknown>>).map(row =>
          row['evidence_grade'] === 'empirical' ? row : { ...row, rank_consequence: null }
        )
        return {
          content: {
            chart_id,
            mode,
            seed_insight_id: seedId,
            rows, count: rows.length,
            ...(rows.length === 0
              ? { empty_reason: `No neighbor rows found for seed_insight_id=${seedId} (seed may not exist, or the table is not yet populated for this chart's build).` }
              : {}),
            provenance: { tables: ['mimamsa_insight_embeddings', 'mimamsa_insight_units'], source: 'L5 Mīmāṃsā pgvector cosine-distance nearest-neighbor search between two already-computed embeddings; served chart-scoped.' },
          },
          is_error: false,
        }
      }

      return { content: { error: `Unknown mode: ${mode}` }, is_error: true }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}

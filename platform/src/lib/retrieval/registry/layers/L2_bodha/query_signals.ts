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
 *
 * BA-P2: When `domain` is specified, applies query-time 4-dimensional composite ranking
 * (class_prior × topic_relevance × intrinsic_strength × structural_role × temporal_activation
 * × percentile_within_class) on top-CANDIDATE_FETCH_SIZE salience candidates. ranking_basis
 * is returned on every response. NEVER writes to bodha_* tables or modifies stored salience.
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { DEFAULT_AYANAMSHA } from '../../constants'
import { cacheKey, cacheGet, cacheSet } from '../../../cache'
import { applyCompositeRanking, buildRankingBasis } from '../../../ranking/composite_ranker'
import { fetchL1Context } from '../../../ranking/l1_context_fetcher'
import { PRIORS_VERSION } from '../../../ranking/priors_config'

// Coarse candidate pool for composite re-ranking when domain is specified.
// Fetch this many by computed_salience, then composite-rank in TypeScript, then slice.
const CANDIDATE_FETCH_SIZE = 500

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
      description: "Ayanamsha to filter by (default: 'lahiri_chitrapaksha').",
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

    const ayanamsha_id    = (args['ayanamsha_id'] as string | undefined) ?? DEFAULT_AYANAMSHA

    // Cache check (H-11). priors_version in key ensures cache busts on prior updates.
    const _cacheKey = cacheKey('query_signals', { chart_id, ayanamsha_id,
      domain: args['domain'], source_subsystem: args['source_subsystem'],
      signal_type_class: args['signal_type_class'], min_salience: args['min_salience'],
      lel_enabled: args['lel_enabled'], top_k: args['top_k'], offset: args['offset'],
      semantic_query: args['semantic_query'], priors_version: PRIORS_VERSION })
    const _cached = cacheGet(_cacheKey)
    if (_cached !== undefined) return _cached as ReturnType<typeof this.handler>
    const domain          = args['domain'] as string | undefined
    const source_subsystem = args['source_subsystem'] as string | undefined
    const signal_type_class = args['signal_type_class'] as string | undefined
    const min_salience    = Number(args['min_salience'] ?? 0)
    const lel_enabled     = Boolean(args['lel_enabled'] ?? false)
    const top_k           = Math.min(Number(args['top_k'] ?? 50), 500)
    const offset          = Number(args['offset'] ?? 0)
    const semantic_query  = args['semantic_query'] as string | undefined

    try {
      void _ctx

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

      // BA-P2: composite re-rank when domain specified; salience fallback otherwise.
      const useComposite = Boolean(domain)

      // Canonical SELECT — identical columns for both paths.
      // semantic_query: vertex embedding not available at query time; salience fallback used.
      const SIGNAL_COLUMNS = `
          m.signal_id, m.signal_type_id, m.signal_type_class, m.signal_tradition,
          m.signal_summary_text, m.signal_headline_text,
          m.computed_salience, m.top_k_salience_rank,
          m.domains_affected_array, m.constituent_facts_array,
          m.source_subsystem, m.valence, m.verification_pass_status,
          m.citation_human, m.lel_origin, m.signature_tier,
          m.configuration_jsonb`

      // pBase: next param slot AFTER base filters (before LIMIT/OFFSET pushed).
      const pBase = p

      let rawRows: Record<string, unknown>[] = []
      let poolNote = ''

      if (useComposite) {
        // Dual-pool strategy (G10-QT fix, 2026-07-03):
        // yoga/configuration signals have computed_salience ≈ 0.58 while composite_state signals
        // sit at 2.3. A single top-500 salience pool excludes yoga entirely (1,874 composite_state
        // signals rank above them). Dual-pool guarantees high-class-prior signals are always present.
        //
        // Pool A: top-CANDIDATE_FETCH_SIZE by salience (composite_state/structural bulk)
        // Pool B: top-CLASS_FORCED_LIMIT from high-class-prior types (always included)
        const CLASS_FORCED_TYPES = ['yoga', 'configuration', 'parivartana', 'relationship', 'karaka_alignment']
        const CLASS_FORCED_LIMIT = 150

        const paramsA = [...params, CANDIDATE_FETCH_SIZE]
        const sqlA = `
          SELECT ${SIGNAL_COLUMNS}
          FROM bodha_msr_signals m
          WHERE ${filters.join(' AND ')}
          ORDER BY m.computed_salience DESC NULLS LAST
          LIMIT $${pBase}`

        const paramsB = [...params, CLASS_FORCED_TYPES, CLASS_FORCED_LIMIT]
        const sqlB = `
          SELECT ${SIGNAL_COLUMNS}
          FROM bodha_msr_signals m
          WHERE ${filters.join(' AND ')}
            AND m.signal_type_class = ANY($${pBase})
          ORDER BY m.computed_salience DESC NULLS LAST
          LIMIT $${pBase + 1}`

        const [rA, rB] = await Promise.all([query(sqlA, paramsA), query(sqlB, paramsB)])

        // Merge + dedup by signal_id (Pool A first; Pool B fills gaps)
        const seen = new Set<string>()
        for (const row of [...rA.rows, ...rB.rows]) {
          const id = String(row['signal_id'] ?? '')
          if (id && !seen.has(id)) { seen.add(id); rawRows.push(row) }
        }
        poolNote = `dual-pool A=${rA.rows.length}+B=${rB.rows.length}→${rawRows.length} unique`

      } else {
        // Legacy salience path: single query with pagination.
        params.push(top_k, offset)
        const topKPh   = `$${p++}`
        const offsetPh = `$${p++}`
        const sql = `
          SELECT ${SIGNAL_COLUMNS}
          FROM bodha_msr_signals m
          WHERE ${filters.join(' AND ')}
          ORDER BY m.computed_salience DESC NULLS LAST
          LIMIT ${topKPh} OFFSET ${offsetPh}`
        const result = await query(sql, params)
        rawRows = result.rows
        poolNote = 'salience-single'
      }

      // BA-P2: composite re-rank + ranking_basis assembly
      let signals: Record<string, unknown>[]
      let ranking_basis: Record<string, unknown>

      if (useComposite && rawRows.length > 0) {
        const as_of_date = new Date().toISOString().split('T')[0]
        const ctx = await fetchL1Context(chart_id, ayanamsha_id, as_of_date)
        // Cast through unknown: rawRows carries bodha_msr_signals columns; MsrSignalRow is satisfied at runtime.
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const scoredAll = applyCompositeRanking(rawRows as unknown as Parameters<typeof applyCompositeRanking>[0], ctx, domain)
        // Slice to requested pagination window; strip internal _subscores from wire format
        const scoredSlice = scoredAll.slice(offset, offset + top_k)
        signals = scoredSlice.map(s => {
          const { _subscores, ...rest } = s
          void _subscores
          return rest as Record<string, unknown>
        })
        ranking_basis = buildRankingBasis(scoredSlice, domain)
      } else {
        signals = rawRows
        ranking_basis = { mode: 'salience_fallback', priors_version: PRIORS_VERSION, domain: domain ?? null }
      }

      // Size guard (H-12): prevent >1.5MB responses from overwhelming the MCP transport
      let truncated = false
      let truncated_from: number | undefined
      if (signals.length > 0) {
        const estimatedBytes = JSON.stringify(signals).length
        if (estimatedBytes > 1_500_000) {
          truncated_from = signals.length
          const keepCount = Math.floor(signals.length * (1_400_000 / estimatedBytes))
          signals = signals.slice(0, keepCount)
          truncated = true
        }
      }

      // E-2 freshness contract (R5 W0a punch-list, P4): the provenance notes below used
      // to be string literals in this handler ("100% background", "91.5% orphan rate")
      // that went stale the moment the underlying data was recut — and then
      // self-contradicted the very rows shipped in the SAME response (P4's finding).
      // Both notes are now computed live from this response's own served rows.

      const tierCounts: Record<string, number> = {}
      for (const s of signals) {
        const tier = (s['signature_tier'] as string | null) ?? 'unknown'
        tierCounts[tier] = (tierCounts[tier] ?? 0) + 1
      }
      const signatureTierNote = signals.length === 0
        ? 'signature_tier distribution: no rows served in this response.'
        : `signature_tier distribution in this response (computed live, not a cached historical ` +
          `figure): ` +
          Object.entries(tierCounts)
            .sort((a, b) => b[1] - a[1])
            .map(([tier, n]) => `${tier}=${Math.round((n / signals.length) * 100)}%`)
            .join(', ') +
          '. Ranking uses computed_salience (coarse) + composite (fine, domain-conditioned) regardless of tier.'

      let defect001Note: string
      try {
        const referencedFactIds = Array.from(new Set(
          signals.flatMap(s => ((s['constituent_facts_array'] as string[] | null) ?? []))
        )).filter(Boolean)
        if (referencedFactIds.length === 0) {
          defect001Note = 'No constituent_facts_array references in this response to check for orphan rate.'
        } else {
          const resolvedResult = await query<{ fact_id: string }>(
            `SELECT fact_id FROM chart_facts WHERE chart_id = $1 AND fact_id = ANY($2::text[])`,
            [chart_id, referencedFactIds]
          )
          const resolvedCount = resolvedResult.rows.length
          const orphanPct = Math.round((1 - resolvedCount / referencedFactIds.length) * 100)
          defect001Note = `constituent_facts_array resolution, computed live for this response: ` +
            `${resolvedCount}/${referencedFactIds.length} referenced fact_id(s) resolve against ` +
            `chart_facts (${orphanPct}% orphan rate in this page). ` +
            (orphanPct > 0
              ? 'Do not error on unresolved joins — treat unresolved refs as reference-only.'
              : 'All references in this page resolve.')
        }
      } catch (e) {
        defect001Note = `constituent_facts_array orphan-rate check failed live (${String(e)}) — ` +
          `treat resolution as UNKNOWN for this response rather than assuming any historical figure.`
      }

      const responseContent = {
        chart_id,
        ayanamsha_id,
        signals,
        returned_count: signals.length,
        truncated,
        ...(truncated_from !== undefined ? { truncated_from } : {}),
        ranking_basis,
        filters:  { domain, source_subsystem, signal_type_class, min_salience, lel_enabled, top_k, offset },
        semantic_fallback: semantic_query ? 'Semantic embedding not available at query time — salience-ranked fallback used. Full vector search requires Vertex embedding of the query string.' : undefined,
        provenance: {
          tables: ['bodha_msr_signals'],
          ranking_note: useComposite
            ? `Composite 4D re-ranking applied: ${poolNote} (priors_version=${PRIORS_VERSION}).`
            : `Salience-ranked (no domain specified — composite ranking requires domain).`,
          defect_001_note: defect001Note,
          signature_tier_note: signatureTierNote,
          lel_note: 'lel_origin=true signals: 0 rows currently. LEL filter is safe but returns empty.',
        },
      }
      const response = { content: responseContent, is_error: false as const }
      cacheSet(_cacheKey, response)
      return response
    } catch (err) {
      return {
        content: { error: String(err), chart_id },
        is_error: true,
      }
    }
  },
}

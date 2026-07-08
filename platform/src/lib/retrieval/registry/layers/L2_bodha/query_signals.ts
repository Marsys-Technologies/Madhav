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
 *
 * FRAME FACET (R5 W2, design §27.3): computed_salience / house_weight_multiplier / etc. are
 * FROZEN build-time formula output (must_not_touch per the R5 brief) and are NEVER
 * recomputed here for a different frame. What `frame` DOES add: a `frame_context` block
 * (each graha's actual house counted from the requested frame, via `resolveFrameReferenceSign`
 * + `houseCountedFrom` — W1's address resolver, reused not re-derived, design §19) so the
 * caller can judge a returned signal "from Moon" etc. against its own frame arithmetic in
 * the SAME call, without a second get_positions round-trip. Signals themselves are unfiltered
 * by frame — the shastra fact a signal encodes doesn't change; only the counting-frame for
 * bhava-relative interpretation does.
 *
 * THE PARADIGM FACET (design §27.4, R5 W2): `paradigm: parashari | jaimini | kp | tajika`
 * filters to bodha_msr_signals.signal_tradition — the column design §27.4 names as already
 * "carrying" the paradigm dimension, made a navigation facet here. Default (paradigm omitted)
 * returns signals from every tradition, UNFILTERED — this is deliberate, not an oversight: this
 * drill surface's atomic signals already carry their own signal_tradition per row (never
 * silently blended into one un-attributed value), and the design's own whole-chart-read
 * discipline (B.11 / CLAUDE.md) depends on being able to see convergence ACROSS traditions.
 * The "mixing paradigms mid-answer" sin design §27.4 warns against is a DIFFERENT failure —
 * treating signals from two schools as if they were one coherent method's output without
 * disclosing which is which — not merely listing multiple traditions' tagged signals side by
 * side. Passing `paradigm` here is the opt-in for a caller (e.g. the triangulation register,
 * A7) that specifically wants a single tradition's clean, coherent signal set for one leg of a
 * per-paradigm comparison. `esoteric`/`lal_kitab` signal_tradition values also exist in the data
 * but are outside design §27.4's named 4-paradigm vocabulary — not exposed through this facet.
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { DEFAULT_AYANAMSHA } from '../../constants'
import { cacheKey, cacheGet, cacheSet } from '../../../cache'
import { applyCompositeRanking, buildRankingBasis } from '../../../ranking/composite_ranker'
import { fetchL1Context } from '../../../ranking/l1_context_fetcher'
import { PRIORS_VERSION } from '../../../ranking/priors_config'
import {
  resolveFrameReferenceSign, houseCountedFrom, GRAHA_CODE_TO_NAME,
  type ReferenceFrame, type ZodiacSign,
} from '../../../address_resolver'

const FRAME_VALUES: ReferenceFrame[] = ['lagna', 'chandra', 'surya', 'arudha', 'karakamsha']

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
    paradigm: {
      type: 'string',
      description: [
        "The PARADIGM facet (design §27.4): filter to signal_tradition = one coherent classical",
        "school. Default (omitted): no filter — signals from every tradition are returned, each",
        "still tagged with its own signal_tradition (never blended into one unattributed value).",
        "Pass this when you specifically need ONE tradition's clean signal set (e.g. a",
        "per-paradigm leg of a triangulation comparison), not to suppress cross-tradition signals.",
      ].join(' '),
      enum: ['parashari', 'jaimini', 'kp', 'tajika'],
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
    frame: {
      type: 'string',
      description: 'Reference frame (default: lagna; design §27.3). When non-lagna, the response ' +
        'includes a `frame_context` block with each graha\'s actual house counted from that frame ' +
        '(e.g. "from Moon") — for judging returned signals\' bhava relevance under that frame in ' +
        'this same call. Signal rows and computed_salience are NEVER recomputed by frame (frozen ' +
        'formula output) — only the frame_context annotation is added.',
      enum: FRAME_VALUES,
      default: 'lagna',
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
    const frame           = ((args['frame'] as string | undefined) ?? 'lagna') as ReferenceFrame
    if (!FRAME_VALUES.includes(frame)) {
      return {
        content: { error: `Unsupported frame "${frame}". Supported: ${FRAME_VALUES.join(', ')} (design §27.3).` },
        is_error: true,
      }
    }

    const PARADIGM_VALUES = ['parashari', 'jaimini', 'kp', 'tajika'] as const
    const paradigmRaw = args['paradigm'] as string | undefined
    if (paradigmRaw && !(PARADIGM_VALUES as readonly string[]).includes(paradigmRaw)) {
      return {
        content: {
          error: `Unknown paradigm "${paradigmRaw}". Supported (design §27.4): ${PARADIGM_VALUES.join(', ')}.`,
        },
        is_error: true,
      }
    }
    const paradigm = paradigmRaw as (typeof PARADIGM_VALUES)[number] | undefined

    // Cache check (H-11). priors_version in key ensures cache busts on prior updates.
    const _cacheKey = cacheKey('query_signals', { chart_id, ayanamsha_id, frame,
      domain: args['domain'], source_subsystem: args['source_subsystem'],
      signal_type_class: args['signal_type_class'], min_salience: args['min_salience'],
      lel_enabled: args['lel_enabled'], top_k: args['top_k'], offset: args['offset'],
      semantic_query: args['semantic_query'], paradigm, priors_version: PRIORS_VERSION })
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
      if (paradigm) {
        // design §27.4 paradigm facet — a coherent single-tradition slice.
        filters.push(`m.signal_tradition = $${p++}`)
        params.push(paradigm)
      }
      if (min_salience > 0) {
        filters.push(`m.computed_salience >= $${p++}`)
        params.push(min_salience)
      }
      if (!lel_enabled) {
        // Exclude LEL signals by default (lel_origin=false or null)
        filters.push(`(m.lel_origin IS NULL OR m.lel_origin = false)`)
      }

      // D5 coverage receipt (design §10.5): true family size — a COUNT(*) against the
      // SAME base filters (chart_id/ayanamsha/domain/source_subsystem/signal_type_class/
      // paradigm/min_salience/lel_enabled) the served page/candidate pool was drawn from,
      // BEFORE any LIMIT/OFFSET/candidate-pool capping. Cheap (indexed columns, single
      // aggregate) — run alongside the main query, never blocking it.
      const familyCountPromise = query<{ total: string }>(
        `SELECT COUNT(*)::text AS total FROM bodha_msr_signals m WHERE ${filters.join(' AND ')}`,
        params.slice(0, p - 1),
      )

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
      // S3 fix (R5 W0a perf lane): Buffer.byteLength on the UTF-8 encoding, not
      // String.length — `.length` counts UTF-16 code units and undercounts the
      // actual wire byte size for any multi-byte (non-ASCII) content, letting
      // genuinely oversized payloads slip past this guard.
      let truncated = false
      let truncated_from: number | undefined
      if (signals.length > 0) {
        const serialized = JSON.stringify(signals)
        const estimatedBytes = Buffer.byteLength(serialized, 'utf8')
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

      // Frame facet (R5 W2, design §27.3): annotation only — signal rows/salience unchanged.
      let frameContext: Record<string, unknown> | undefined
      if (frame !== 'lagna') {
        try {
          const { sign: referenceSign } = await resolveFrameReferenceSign(chart_id, frame, { ayanamsha_id })
          const grahaCodes = Object.keys(GRAHA_CODE_TO_NAME)
          const signRes = await query<{ fact_subject: string; fact_value_text: string | null }>(
            `SELECT fact_subject, fact_value_text FROM chart_facts
             WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'graha_position'
               AND fact_subject = ANY($3::text[]) AND fact_key = 'sign'`,
            [chart_id, ayanamsha_id, grahaCodes],
          )
          const activeHouseByGraha: Record<string, number> = {}
          for (const r of signRes.rows) {
            if (!r.fact_value_text) continue
            activeHouseByGraha[GRAHA_CODE_TO_NAME[r.fact_subject] ?? r.fact_subject] =
              houseCountedFrom(referenceSign as ZodiacSign, r.fact_value_text as ZodiacSign)
          }
          frameContext = {
            frame, reference_sign: referenceSign, ayanamsha_id,
            active_house_by_graha: activeHouseByGraha,
            note: `Each graha's actual house counted from ${frame} (${referenceSign}). Signal rows ` +
              `and computed_salience are unaffected by frame (frozen build-time formula output) — ` +
              `use this to judge a returned signal's bhava relevance under ${frame} in this same call.`,
          }
        } catch (e) {
          frameContext = { frame, error: `could not resolve frame "${frame}": ${String(e)}` }
        }
      }

      // D5 coverage receipt: resolve the family-size COUNT alongside everything else.
      // Never fails the instrument — an honest `null` beats a fabricated/guessed total.
      let total_matching_filters: number | null
      try {
        const countResult = await familyCountPromise
        total_matching_filters = Number(countResult.rows[0]?.total ?? 0)
      } catch {
        total_matching_filters = null
      }

      const responseContent = {
        chart_id,
        frame,
        ...(frameContext ? { frame_context: frameContext } : {}),
        ayanamsha_id,
        signals,
        returned_count: signals.length,
        total_matching_filters,
        truncated,
        ...(truncated_from !== undefined ? { truncated_from } : {}),
        ranking_basis,
        filters:  { domain, source_subsystem, signal_type_class, min_salience, lel_enabled, top_k, offset, paradigm: paradigm ?? null },
        semantic_fallback: semantic_query ? 'Semantic embedding not available at query time — salience-ranked fallback used. Full vector search requires Vertex embedding of the query string.' : undefined,
        provenance: {
          tables: ['bodha_msr_signals'],
          ranking_note: useComposite
            ? `Composite 4D re-ranking applied: ${poolNote} (priors_version=${PRIORS_VERSION}).`
            : `Salience-ranked (no domain specified — composite ranking requires domain).`,
          defect_001_note: defect001Note,
          signature_tier_note: signatureTierNote,
          lel_note: 'lel_origin=true signals: 0 rows currently. LEL filter is safe but returns empty.',
          paradigm_note: paradigm
            ? `paradigm:"${paradigm}" applied — every signal in this response carries ` +
              `signal_tradition="${paradigm}" (design §27.4 coherent single-tradition slice).`
            : 'No paradigm filter applied — signals from every classical tradition are present, ' +
              'each individually tagged via its own signal_tradition field. Do not treat this as ' +
              'one coherent method\'s output; a caller building a single-paradigm answer should ' +
              'pass paradigm to get one tradition\'s clean slice (design §27.4).',
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

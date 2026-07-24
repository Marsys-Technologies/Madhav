/**
 * query_signals — MSR Signal Query (L2 Bodha)
 * ============================================
 * Queries bodha_msr_signals (66,738 rows) and bodha_signal_embeddings (66,738 rows, 100% embedded).
 *
 * Returns ranked signals by computed_salience. CRITICAL design notes:
 *
 * 1. signature_tier's distribution and DEFECT-001's orphan rate are NOT restated as
 *    literals here (E-2 freshness contract, R5.1 C2 item 1) — both claims go stale the
 *    moment underlying data is recut, and a stale claim misleads worse than none. Both
 *    are re-derived LIVE on every call via `platform/src/lib/retrieval/provenance/
 *    freshness_notes.ts` and returned in `provenance.signature_tier` / `provenance.defect_001`
 *    as structured `{ status, note, as_of, expires_on, metrics }` objects — never assume the
 *    historical figures ("100% background", "91.5% orphan") still hold; read the live note.
 *
 * 2. lel_origin=true: 0 signals currently. lel_enabled filter is safe to expose but
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
import { demoteSignatureTiers } from '../../../ranking/salience_demotion'
import {
  resolveFrameReferenceSign, houseCountedFrom, GRAHA_CODE_TO_NAME,
  type ReferenceFrame, type ZodiacSign,
} from '../../../address_resolver'
import { deriveDefect001Note, deriveSignatureTierNote } from '../../../provenance/freshness_notes'

const FRAME_VALUES: ReferenceFrame[] = ['lagna', 'chandra', 'surya', 'arudha', 'karakamsha']

// Internal L1-writer namespace tags (e.g. "[ga_sensitive]", "[ga_structural]") that get
// appended onto signal_headline_text at write time to mark the writer's own internal
// classification of the row. These are an L1-writer-internal bookkeeping detail — never a
// user-facing gloss — and must not be echoed into the served headline string. Response-envelope
// hygiene only: the underlying bodha_msr_signals row (and its provenance) are never touched.
const INTERNAL_NAMESPACE_TAG_RE = /\s*\[ga_\w+\]/g

/** Strip a trailing internal-namespace tag from a served headline string, if present. */
function stripInternalNamespaceTag(text: string): string {
  return text.replace(INTERNAL_NAMESPACE_TAG_RE, '').trimEnd()
}

// Coarse candidate pool for composite re-ranking when domain is specified.
// Fetch this many by computed_salience, then composite-rank in TypeScript, then slice.
const CANDIDATE_FETCH_SIZE = 500

// ── WP-1.3(g) / LCA-7: projection whitelist ──────────────────────────────────
// msr_sql previously served a FIXED 17-of-82-column projection regardless of the
// caller's request. The `projection` param now lets a caller pick which columns are
// served. Injection-safety is structural: every requested name is validated against
// this STATIC whitelist of real bodha_msr_signals columns (information_schema ground
// truth, 82 cols) — an unknown name is rejected before any SQL runs, and the SELECT
// is built only from names drawn from this constant, never from caller strings.
const MSR_SIGNAL_COLUMNS: readonly string[] = [
  'signal_id', 'chart_id', 'ayanamsha_id', 'build_id', 'signal_type_id',
  'signal_type_class', 'signal_tradition', 'fact_kind', 'source_l1_asset',
  'source_subsystem', 'signal_summary_text', 'signal_headline_text',
  'classical_sources_jsonb', 'varga_id', 'varga_provenance_jsonb', 'epistemic_tier',
  'epistemic_jsonb', 'salience_conditioned_by_jsonb', 'signature_tier', 'valence',
  'lel_origin', 'configuration_jsonb', 'constituent_facts_array',
  'constituent_signals_array', 'classical_sources_array',
  'source_corroboration_count_by_text', 'source_corroboration_count_by_verse',
  'orb_tightness', 'shadbala_norm', 'dignity_score', 'deterministic_strength',
  'verification_certainty', 'divisional_corroboration_count',
  'dasha_activation_proximity_score', 'house_weight_multiplier',
  'ashtakavarga_support_multiplier', 'aspect_modifier', 'vargottama_amplification',
  'argala_modifier', 'neechabhanga_modifier', 'cancellation_modifier',
  'computed_salience', 'salience_formula_version', 'salience_confidence_interval_jsonb',
  'domains_affected_array', 'domain_salience_jsonb', 'shared_factor_keys_jsonb',
  'cross_domain_shared_factor_count', 'graph_edge_pattern_jsonb',
  'graph_node_strength_contribution_jsonb', 'relationship_classification',
  'graha_weakness_indicators_jsonb', 'remedy_hooks_array', 'recurring_pattern_marker',
  'top_k_salience_rank', 'system_convergence_count', 'signature_class',
  'contradicts_signals_array', 'active_duration_class', 'active_dasha_periods_jsonb',
  'activation_predicted_dates_jsonb', 'predicted_outcome_class',
  'cross_ayanamsha_consistency_score', 'strength_normalized_to_chart_max',
  'pada_precision_flag', 'cross_system_consensus_count', 'channel_render_priority_jsonb',
  'verification_pass_status', 'verification_method', 'citation_ref', 'citation_human',
  'computed_at', 'engine_version', 'salience_pctl_in_class', 'salience_inputs_complete',
  'salience_robustness', 'aggregation_member', 'bala_gate', 'functional_context_score',
  'verification_rescale', 'present_but_enfeebled', 'class_prior',
  // Lane 4 (MSR elevation, Doctrine Campaign D-1 Night-1) / Lane 5 serving retrofit:
  // ratification_factor (varga-ratification multiplier ∈ [0.6,1.4] applied to salience,
  // design §11) and valence_source (which computation produced `valence` — 'ga_vichara_v1'
  // when Lane 2's judged valence is available, else the pre-existing keyword-heuristic
  // fallback — never silently unlabeled). Additive columns on bodha_msr_signals; if the
  // migration adding them hasn't landed yet in a given environment, the whitelist entry
  // is harmless (SELECT of an absent column fails loudly at query time, same as any other
  // not-yet-migrated column — never silently substituted).
  'ratification_factor', 'valence_source',
]
const MSR_SIGNAL_COLUMN_SET = new Set(MSR_SIGNAL_COLUMNS)

// The legacy default served projection (17 cols). Also the INTERNAL-REQUIRED superset:
// composite ranking, salience demotion, and the E-2 freshness derivation all read from
// these, so they are ALWAYS fetched even when the caller projects a narrower set — the
// served rows are then projected down to what was requested.
const DEFAULT_SERVE_COLUMNS: readonly string[] = [
  'signal_id', 'signal_type_id', 'signal_type_class', 'signal_tradition',
  'signal_summary_text', 'signal_headline_text', 'computed_salience', 'top_k_salience_rank',
  'domains_affected_array', 'constituent_facts_array', 'source_subsystem', 'valence',
  'verification_pass_status', 'citation_human', 'lel_origin', 'signature_tier',
  'configuration_jsonb',
]

// Lane 5 (§N.6 density retrofit): columns Lane 4 (MSR elevation) adds to bodha_msr_signals.
// Serving must expose them by default (brief: "expose ratification_factor + valence_source
// in rows") WITHOUT hard-failing in an environment where Lane 4's migration hasn't landed
// yet (this worktree's own dev environment, at the time of writing, is exactly that case —
// see the Lane 4 handback report). Resolved once per process via information_schema and
// cached — cheap, and self-heals to "present" the moment the migration lands with no
// redeploy-triggering code change.
const OPTIONAL_ELEVATION_COLUMNS = ['ratification_factor', 'valence_source'] as const
let _optionalColumnsCache: Promise<string[]> | null = null
function resolveOptionalElevationColumns(): Promise<string[]> {
  if (_optionalColumnsCache) return _optionalColumnsCache
  _optionalColumnsCache = query<{ column_name: string }>(
    `SELECT column_name FROM information_schema.columns
     WHERE table_name = 'bodha_msr_signals' AND column_name = ANY($1::text[])`,
    [[...OPTIONAL_ELEVATION_COLUMNS]],
  ).then(r => r.rows.map(x => x.column_name)).catch(() => [])
  return _optionalColumnsCache
}

/**
 * Resolve the `projection` param into {fetch, serve} column lists.
 *  - undefined            → {fetch: default17(+elevation if present), serve: same}
 *  - ['*']                → {fetch: all82,      serve: all82}       (full set reachable)
 *  - ['col', ...]         → validated subset; fetch = default17 ∪ subset, serve = subset
 * Throws on a non-array, empty, or unknown-column projection (rejected before any SQL).
 */
function resolveProjection(
  raw: unknown,
  presentOptionalColumns: readonly string[] = [],
): { fetch: string[]; serve: string[] | null } {
  if (raw === undefined || raw === null) {
    const withElevation = [...DEFAULT_SERVE_COLUMNS, ...presentOptionalColumns]
    return { fetch: withElevation, serve: withElevation }
  }
  if (!Array.isArray(raw) || raw.length === 0) {
    throw new Error('projection must be a non-empty array of column names, or ["*"] for all columns.')
  }
  if (raw.length === 1 && raw[0] === '*') {
    // Exclude not-yet-migrated optional columns from '*' (avoids a full-schema break in an
    // environment where Lane 4's migration hasn't landed) — same self-healing discipline as
    // the default path above.
    const absentOptional: readonly string[] = OPTIONAL_ELEVATION_COLUMNS.filter(c => !presentOptionalColumns.includes(c))
    const all = MSR_SIGNAL_COLUMNS.filter(c => !absentOptional.includes(c))
    return { fetch: [...all], serve: null } // serve all fetched
  }
  const requested = raw.map(String)
  const unknown = requested.filter(c => !MSR_SIGNAL_COLUMN_SET.has(c))
  if (unknown.length > 0) {
    throw new Error(
      `Unknown projection column(s): ${unknown.join(', ')} — not a projectable bodha_msr_signals column. ` +
      `Pass ["*"] for the full set, or choose from the ${MSR_SIGNAL_COLUMNS.length} known columns.`,
    )
  }
  const requestedAbsentOptional = requested.filter(
    c => (OPTIONAL_ELEVATION_COLUMNS as readonly string[]).includes(c) && !presentOptionalColumns.includes(c),
  )
  if (requestedAbsentOptional.length > 0) {
    throw new Error(
      `Column(s) not yet available on bodha_msr_signals in this environment: ${requestedAbsentOptional.join(', ')} ` +
      '(Lane 4 MSR-elevation migration not applied here). Omit them, or retry once the migration lands.',
    )
  }
  const fetch = Array.from(new Set([...DEFAULT_SERVE_COLUMNS, ...requested]))
  return { fetch, serve: requested }
}

export const querySignalsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_signals',
  type:  'tool',
  layer: 'L2',
  name:  'query_signals',

  description: [
    'Query MSR signals for a chart from the Bodha synthesis layer.',
    'Returns signals ranked by computed_salience (a large signal set per chart).',
    'Supports filters: domain, source_subsystem, min_salience, lel_enabled.',
    'Optional semantic_query uses pgvector cosine similarity over signal embeddings (768-dim).',
    'emits_references: returns signal_id + constituent_facts_array as reference list.',
    'DEFECT-001 + signature_tier status are derived LIVE per call (E-2 freshness contract) —',
    'see provenance.defect_001 / provenance.signature_tier in the response for current status,',
    'not a historical figure. Ranking always uses computed_salience (+ composite when domain given).',
    'lel_capable: lel_origin filter exposed but returns 0 rows until LEL signals are ingested.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'rich_relational',
  traversal_level: 'L-SIGNAL',
  tool_role: 'drill',
  emits_references: true,
  grounds_to: { l1_fact_ids: true, l0_citation_ids: true },
  lel_capable: true,
  // Lane 5 (§N.6 (iv), Doctrine Campaign D-1 Night-1): backs bodha_signals_get/get_signals.
  density_contract: {
    max_digest_bytes: 1_500_000, // existing H-12 size guard on this tool (see estimatedBytes check below)
    paginated: true,
    facets: ['domain', 'source_subsystem', 'paradigm', 'signal_type_class', 'min_salience', 'lel_enabled', 'projection', 'frame'],
    // W3 "One Envelope" (2026-07-20): was `false` with a "not yet added" note — the
    // handler now sets `content.empty_reason` naming the active filter set whenever
    // `signals.length === 0`, alongside the pre-existing returned_count/
    // total_matching_filters receipts.
    empty_reason: true,
  },

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
      description: [
        'Filter to one bodha_msr_signals.signal_type_class. Applied in the WHERE clause BEFORE the',
        'salience LIMIT/candidate-pool cap, so a class-scoped query returns ALL rows of that class',
        'for the chart/ayanamsha regardless of their global salience rank — the reach path for',
        'legitimately low-salience structural CORROBORATION classes (e.g. sudarshana_agreement) that',
        'a chart-wide salience page would never surface. No enum restriction: any real class value',
        'is accepted (an incomplete enum here previously hid whole classes from callers, §N.6). Known',
        'classes include: composite_state, karaka_alignment, sade_sati, varga_pattern, panchanga,',
        'tradition_specific, annual, parivartana, configuration, dosha, yoga, bhavat_bhavam_amplifier,',
        'sudarshana_agreement, varga_ratification_divergence.',
      ].join(' '),
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
    projection: {
      type: 'array',
      description: [
        'WP-1.3(g)/LCA-7 — which bodha_msr_signals columns to serve. Omit for the default',
        '17-column view (backward-compatible). Pass ["*"] to serve ALL 82 columns. Pass an',
        'explicit array (e.g. ["signal_id","orb_tightness","dignity_score"]) to serve exactly',
        'those columns. Every name is validated against the real column whitelist — an unknown',
        'column is rejected before any SQL runs (injection-safe); arbitrary SQL is never accepted.',
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

    // Lane 5 (§N.6): which of ratification_factor/valence_source actually exist on
    // bodha_msr_signals in this environment (cached per-process — see resolveOptionalElevationColumns).
    const presentOptionalColumns = await resolveOptionalElevationColumns()

    // WP-1.3(g)/LCA-7: resolve the projection BEFORE any SQL — an unknown column is
    // rejected here (injection-safe), never sent to the database.
    let projection: { fetch: string[]; serve: string[] | null }
    try {
      projection = resolveProjection(args['projection'], presentOptionalColumns)
    } catch (e) {
      return { content: { error: e instanceof Error ? e.message : String(e) }, is_error: true }
    }

    // Cache check (H-11). priors_version in key ensures cache busts on prior updates.
    const _cacheKey = cacheKey('query_signals', { chart_id, ayanamsha_id, frame,
      domain: args['domain'], source_subsystem: args['source_subsystem'],
      signal_type_class: args['signal_type_class'], min_salience: args['min_salience'],
      lel_enabled: args['lel_enabled'], top_k: args['top_k'], offset: args['offset'],
      semantic_query: args['semantic_query'], paradigm,
      projection: projection.serve ?? '*', priors_version: PRIORS_VERSION })
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
      // WP-1.3(g)/LCA-7: columns are the resolved projection.fetch list. Names come ONLY
      // from the MSR_SIGNAL_COLUMNS whitelist (validated in resolveProjection), so this
      // interpolation is injection-safe. The fetch list always includes the internal-required
      // (default-17) columns so composite ranking / demotion / freshness never starve.
      // semantic_query: vertex embedding not available at query time; salience fallback used.
      const SIGNAL_COLUMNS = projection.fetch.map(c => `m.${c}`).join(', ')

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

      // WP-1.2(d) (LCA-9b-2 serving cap): serve-time salience demotion — descriptive
      // almanac fact_keys + per-varga granular data may not carry major/chart_defining
      // tiers on the wire. Applied on BOTH the composite and salience-fallback paths.
      signals = demoteSignatureTiers(signals)

      // Response-envelope hygiene fix: strip the internal L1-writer namespace tag
      // (e.g. "[ga_sensitive]", "[ga_structural]") from signal_headline_text before it is
      // served. The tag is an L1-writer-internal classification artifact stored on the row —
      // it was being echoed verbatim into the user-facing headline field with no gloss or
      // stripping. Applied on BOTH the composite and salience-fallback paths, before
      // projection/truncation, so it holds regardless of which columns are requested. The
      // underlying bodha_msr_signals row and its provenance are untouched — this only affects
      // what is echoed into the served string.
      signals = signals.map(s => {
        const headline = s['signal_headline_text']
        if (typeof headline !== 'string') return s
        const stripped = stripInternalNamespaceTag(headline)
        if (stripped === headline) return s
        return { ...s, signal_headline_text: stripped }
      })

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

      // E-2 freshness contract (R5.1 C2 item 1; originated R5 W0a punch-list P4): these
      // provenance notes used to be string literals in this handler ("100% background",
      // "91.5% orphan rate") that went stale the moment the underlying data was recut — a
      // stale claim misleads worse than none (E-2). Both are now DATA: re-derived live via
      // the shared `provenance/freshness_notes` helper and carried as structured
      // { status, note, as_of, expires_on, metrics } objects, never a remembered figure.
      // DEFECT-001 is scoped to exactly this response's served fact_id references (precise
      // to what was shipped); signature_tier is scoped to the whole chart/ayanamsha (answers
      // "what is the tier distribution right now", independent of pagination).
      const referencedFactIds = Array.from(new Set(
        signals.flatMap(s => ((s['constituent_facts_array'] as string[] | null) ?? []))
      )).filter(Boolean)
      const [defect001, signatureTier] = await Promise.all([
        deriveDefect001Note(chart_id, referencedFactIds),
        deriveSignatureTierNote(chart_id, ayanamsha_id),
      ])

      // WP-1.3(g)/LCA-7: project served rows down to the requested columns. Done AFTER the
      // internal pipeline (ranking/demotion/freshness read the always-fetched default set)
      // so narrowing the SERVED projection never starves the machinery. projection.serve
      // === null means ["*"] — serve everything fetched, no narrowing.
      if (projection.serve !== null) {
        const serveCols = projection.serve
        signals = signals.map(s => {
          const picked: Record<string, unknown> = {}
          for (const c of serveCols) if (c in s) picked[c] = s[c]
          return picked
        })
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

      // W3 "One Envelope" (density_contract.empty_reason implementation, CLAUDE.md §N.6
      // point 3 / B.10): `returned_count`/`total_matching_filters` already existed as
      // receipts, but a zero-row page shipped no field naming WHY — this closes that gap
      // by naming the actual active filter set whenever nothing survived it.
      const empty_reason = signals.length === 0
        ? `No bodha_msr_signals rows matched for chart ${chart_id}` +
          (domain ? ` domain='${domain}'` : '') +
          (source_subsystem ? ` source_subsystem='${source_subsystem}'` : '') +
          (signal_type_class ? ` signal_type_class='${signal_type_class}'` : '') +
          (paradigm ? ` paradigm='${paradigm}'` : '') +
          (min_salience ? ` min_salience>=${min_salience}` : '') +
          (lel_enabled ? ' lel_enabled=true (0 rows currently — no LEL signals ingested yet)' : '') +
          '.'
        : undefined

      const responseContent = {
        chart_id,
        frame,
        ...(frameContext ? { frame_context: frameContext } : {}),
        ayanamsha_id,
        signals,
        returned_count: signals.length,
        total_matching_filters,
        ...(empty_reason ? { empty_reason } : {}),
        truncated,
        ...(truncated_from !== undefined ? { truncated_from } : {}),
        ranking_basis,
        // WP-1.8 (cross-surface inconsistency): when NO domain is given, this surface ranks
        // chart-wide by salience — a DIFFERENT ordering than the domain-scoped composite ranking
        // the assess_*/judgment surfaces use. Disclosed here so a consumer isn't misled into
        // reading a salience top-10 as "the answer" for a domain question and finding it disagrees
        // with assess_*. Pass `domain` to reproduce the assess_* / composite ordering exactly.
        cross_surface: domain
          ? {
              ranking_mode: (ranking_basis['mode'] as string) ?? 'composite_4d',
              agrees_with: `assess_${domain === 'relationship' ? 'marriage' : domain} top_10_composite (same composite ranking path)`,
            }
          : {
              ranking_mode: 'salience_fallback',
              caveat:
                'No domain given → chart-wide salience ranking. This will NOT match assess_*/judgment ' +
                'domain rankings (which use domain-scoped composite ranking). Pass `domain` to reconcile ' +
                'the surfaces; the salience top-k is not a domain-relevance answer.',
            },
        filters:  { domain, source_subsystem, signal_type_class, min_salience, lel_enabled, top_k, offset, paradigm: paradigm ?? null,
          projection: projection.serve === null ? '*' : projection.serve },
        semantic_fallback: semantic_query ? 'Semantic embedding not available at query time — salience-ranked fallback used. Full vector search requires Vertex embedding of the query string.' : undefined,
        provenance: {
          tables: ['bodha_msr_signals'],
          ranking_note: useComposite
            ? `Composite 4D re-ranking applied: ${poolNote} (priors_version=${PRIORS_VERSION}).`
            : `Salience-ranked (no domain specified — composite ranking requires domain).`,
          // Structured E-2 freshness objects (as_of/expires_on + live-derived status) — read
          // these, not any historical figure baked into documentation or memory.
          defect_001: defect001,
          signature_tier: signatureTier,
          // Legacy string fields retained for callers pattern-matching on prior wave's shape
          // (additive-only per R5.1 brief) — text now sourced from the SAME live derivation.
          defect_001_note: defect001.note,
          signature_tier_note: signatureTier.note,
          lel_note: 'lel_origin=true signals: 0 rows currently. LEL filter is safe but returns empty.',
          projection_note: projection.serve === null
            ? `projection=["*"] — all ${MSR_SIGNAL_COLUMNS.length} bodha_msr_signals columns served.`
            : (args['projection'] === undefined
                ? `Default projection — ${DEFAULT_SERVE_COLUMNS.length} of ${MSR_SIGNAL_COLUMNS.length} columns served (WP-1.3(g)/LCA-7). Pass projection:["*"] or an explicit column array to reach the rest.`
                : `Projected ${projection.serve.length} of ${MSR_SIGNAL_COLUMNS.length} columns as requested (validated against the column whitelist).`),
          paradigm_note: paradigm
            ? `paradigm:"${paradigm}" applied — every signal in this response carries ` +
              `signal_tradition="${paradigm}" (design §27.4 coherent single-tradition slice).`
            : 'No paradigm filter applied — signals from every classical tradition are present, ' +
              'each individually tagged via its own signal_tradition field. Do not treat this as ' +
              'one coherent method\'s output; a caller building a single-paradigm answer should ' +
              'pass paradigm to get one tradition\'s clean slice (design §27.4).',
          // Lane 5 (§N.6): disclose whether Lane 4's ratification_factor/valence_source
          // columns are actually live in this environment — never a silent absence.
          elevation_columns_note: presentOptionalColumns.length === OPTIONAL_ELEVATION_COLUMNS.length
            ? 'ratification_factor + valence_source (Lane 4 MSR elevation) are present and served by default.'
            : `Lane 4 MSR-elevation columns not yet available in this environment: ` +
              `${OPTIONAL_ELEVATION_COLUMNS.filter(c => !presentOptionalColumns.includes(c)).join(', ')}. ` +
              'Served rows omit them until that migration lands (self-healing — no code change needed).',
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

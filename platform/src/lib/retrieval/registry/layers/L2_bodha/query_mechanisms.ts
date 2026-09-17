/**
 * query_mechanisms — L2 Bodha Mechanism (Yantra) serving surface
 * ===============================================================
 * SARVA-SIDDHI W-4 / CR-24 (BRIEF_SARVA_SIDDHI_v1_0.md §1 D-2; SARVA_SIDDHI_TRUTH_TABLE
 * Cluster 3). Serves `bodha_mechanisms` — the named, valenced CGM-subgraph objects the
 * `bo_yantra_mechanism` writer already builds (migration 445, D-2 Lane V-4) — as
 * FIRST-CLASS rows: mechanism_name, mechanism_class, valence, member chain/circuit
 * composition, edge-strength provenance (DR-7 `edge_strength_v1`) and a centrality
 * summary. Prior to this tool the table was reachable ONLY indirectly via
 * `traverse_chart_graph` subgraph traversal — never as first-class named mechanisms.
 * Read-only, bounded (LIMIT ≤50 + disclosed total + build-pinned cursor pagination).
 *
 * §N.6 Serving Density Principle: the CR-24 headline class is the chain/circuit family
 * (`convergent_dispositor_chain` / `dispositor_cycle` / `house_lordship_cycle`) — the
 * named multi-node mechanisms an acharya reads as a single structure. These are the
 * densest, most-actionable layer, so:
 *   - they are ordered FIRST (a class-priority sort key), ahead of the high-cardinality
 *     pairwise/triangle motifs (`mutual_aspect`, `mutual_aspect_triangle`) that would
 *     otherwise dominate a flat page and bury them;
 *   - a `chain_circuit_only` filter isolates them;
 *   - per-class + per-valence FACET counts over the FULL matching set are always
 *     returned (`facets`), plus `chain_circuit_count`, so a caller reading `count` can
 *     never mistake a page for the whole (density signaling is data, not narration).
 * No row is silently dropped (B.10) — everything is counted in `total_matching` and the
 * facet rollups even when it falls outside the current page.
 *
 * All `bodha_mechanisms` rows carry `verification_pass_status='single'` — there is no
 * catalog-only vs. confirmed split in this table, so a flat (facet-annotated) list is
 * honest; the field is still served per row for transparency.
 *
 * This docstring previously read `'pass'` and described it as "writer-confirmed". It was
 * neither: `bo_yantra_mechanism.py` stamped the literal unconditionally with no detector
 * behind it (SAMĀPTI A7-N8-AUDIT F-25, DVA Ruling 13 — 11/11 audited sites unearned), and
 * the serve layer's grounding check counted a bare `'pass'` as verified. Both are fixed;
 * the stored rows change at the next rebuild (C1-REBUILD).
 *
 * Chart-scoped (principle #14). Sparse-to-moderate by design (0 → a few hundred rows
 * across 5 ayanamshas); an empty list (total=0) is a valid result with an honest
 * `empty_reason`, not an error.
 */
import type { CapabilityDescriptor } from '../../types'
import { createHash, createHmac, timingSafeEqual } from 'node:crypto'
import { query } from '@/lib/db/client'
// F-164 (PARIŚEṢA-V4, GA-5 follow-up on #1419): the wealth operative-varga set quoted in
// this note used to be a hand-copied literal (`['D1','D2','D9','D11']`) — read live instead,
// same discipline as reading_checklist.ts's DOMAIN_DIRECT_VARGAS.
import { getOperativeVargaConstants, type OperativeVargaEntry } from '../reading_checklist'
import { MECHANISM_SCUS } from '../../knowledge/editorial'
import { loadInquiryLifecycleSigningKeyRing, type InquiryLifecycleSigningKeyRing } from '@/lib/vidhi/inquiry/lifecycle_token'

const MAX_LIMIT = 50
const MAX_OFFSET = 1_000_000
const BO_YANTRA_MECHANISM_ASSET_ID = 'bo_yantra_mechanism'
const BO_YANTRA_MECHANISM_OUTPUT_DIGEST_SPEC_SHA256 = 'b867fc3bb5337bedb7e7c7fbf3f912b3ed888414c8cbb01f18776ba6294c2d0e'
const PAGE_CURSOR_DOMAIN = 'madhav:query_mechanisms:page_cursor:v1'

interface MechanismPageCursor {
  readonly version: 1
  readonly build_id: string
  readonly offset: number
  readonly filter_fingerprint: string
}

function normalizeLimit(value: unknown): number {
  const parsed = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(parsed)) return MAX_LIMIT
  const normalized = Math.floor(parsed)
  return normalized >= 1 ? Math.min(normalized, MAX_LIMIT) : MAX_LIMIT
}

function normalizeOffset(value: unknown): number {
  const parsed = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(parsed)) return 0
  return Math.min(Math.max(Math.floor(parsed), 0), MAX_OFFSET)
}

function filterFingerprint(filters: Record<string, unknown>): string {
  return createHash('sha256').update(JSON.stringify(filters)).digest('hex')
}

function cursorMessage(kid: string, payload: string): string {
  return `${PAGE_CURSOR_DOMAIN}:${kid}.${payload}`
}

function encodePageCursor(cursor: MechanismPageCursor, ring: InquiryLifecycleSigningKeyRing): string {
  const kid = ring.current.kid
  const payload = Buffer.from(JSON.stringify(cursor), 'utf8').toString('base64url')
  const signature = createHmac('sha256', ring.current.material)
    .update(cursorMessage(kid, payload)).digest('base64url')
  return `${kid}.${payload}.${signature}`
}

function decodePageCursor(value: unknown, ring: InquiryLifecycleSigningKeyRing): MechanismPageCursor | null {
  if (typeof value !== 'string' || value.length === 0) return null
  try {
    const parts = value.split('.')
    if (parts.length !== 3) return null
    const [kid, payload, providedSignature] = parts
    if (!kid || !payload || !providedSignature || !/^[A-Za-z0-9_-]+$/.test(payload) || !/^[A-Za-z0-9_-]+$/.test(providedSignature)) return null
    const signingKey = [ring.current, ...(ring.previous ?? [])].find((candidate) => candidate.kid === kid)
    if (!signingKey) return null
    const payloadBytes = Buffer.from(payload, 'base64url')
    if (payloadBytes.toString('base64url') !== payload) return null
    const expectedSignature = createHmac('sha256', signingKey.material)
      .update(cursorMessage(kid, payload)).digest()
    const actualSignature = Buffer.from(providedSignature, 'base64url')
    if (actualSignature.toString('base64url') !== providedSignature
      || actualSignature.length !== expectedSignature.length
      || !timingSafeEqual(actualSignature, expectedSignature)) return null
    const parsed = JSON.parse(payloadBytes.toString('utf8')) as Partial<MechanismPageCursor>
    if (parsed.version !== 1 || typeof parsed.build_id !== 'string' || parsed.build_id.length === 0
      || typeof parsed.filter_fingerprint !== 'string' || !/^[a-f0-9]{64}$/.test(parsed.filter_fingerprint)
      || typeof parsed.offset !== 'number' || !Number.isSafeInteger(parsed.offset)
      || parsed.offset < 0 || parsed.offset > MAX_OFFSET) return null
    return parsed as MechanismPageCursor
  } catch {
    return null
  }
}

function paginationError(chartId: string, code: string, error: string, extra: Record<string, unknown> = {}) {
  return {
    content: {
      chart_id: chartId,
      code,
      error,
      restart_required: true,
      rows: [],
      count: 0,
      total_matching: 0,
      more_available: false,
      next_offset: null,
      next_page_cursor: null,
      ...extra,
    },
    is_error: true,
  }
}

/**
 * The CR-24 chain/circuit mechanism family — multi-node named structures (a convergent
 * dispositor chain, a closed dispositor cycle, a closed house-lordship circuit). These
 * are the "mechanism" specimens CR-24 asks to be served first-class, distinct from the
 * high-volume pairwise/triangle motifs also promoted into the table.
 */
const CHAIN_CIRCUIT_CLASSES = [
  'convergent_dispositor_chain',
  'dispositor_cycle',
  'house_lordship_cycle',
] as const

/**
 * F-107 (PARIŚEṢA-V4, CL-20) — the varga-scope disclosure.
 *
 * `bo_yantra_mechanism` builds its dispositor / lordship / aspect graph from the **rāśi
 * (D1) topology only**. `bodha_mechanisms` has no varga column at all: every row is
 * stamped `snapshot_type = 'static_natal'` from a single writer-level constant, and the
 * node/edge sources it promotes from are D1 graha positions and D1 house lordships.
 *
 * Before this disclosure, a caller asking "what convergent mechanisms across my D1, D2,
 * D11 and Indu Lagna bear on wealth?" received the D1-only mechanism list with NO field,
 * filter, facet or note anywhere in the envelope saying the cross-varga half of the
 * question was never computed — a silent substitution of a narrower answer for the one
 * asked (CLAUDE.md §N.7 item 6: an honest null beats an invented judgment; §N.8: a signal
 * without a detector behind it is null, not green).
 *
 * This block does NOT invent cross-varga mechanism detection — that requires a ratified
 * classical methodology (see `00_ARCHITECTURE/briefs/parisesa/
 * F107_DIVISIONAL_MECHANISM_DESIGN_CONTRACT_v1_0.md`). It states the real scope and points
 * at the surfaces where per-varga data genuinely IS served today.
 */
/**
 * F-164 — was a static const with a hardcoded `['D1','D2','D9','D11']` wealth-set literal
 * in the `note` field; now built per-call from a live read of
 * brahma_vichara_constants.operative_vargas (§N.7 item 3 — never restate a computed/
 * registry-managed value as a wrapper-local literal). `wealthEntry` is `undefined` only if
 * the constants row somehow lacks a 'wealth' key — falls back to a generic (non-hardcoded)
 * phrasing rather than inventing a set, per B.10.
 */
function buildVargaScopeDisclosure(wealthEntry: OperativeVargaEntry | undefined) {
  const wealthVargasDisplay = wealthEntry
    ? `[${wealthEntry.vargas.map(v => `'${v}'`).join(',')}]`
    : '(unavailable — brahma_vichara_constants has no "wealth" entry)'
  const wealthProvisionalDisplay = wealthEntry ? String(wealthEntry.provisional) : 'unknown'
  return {
    computed_over: ['D1'],
    frame: 'rasi_d1_natal_graph_only',
    cross_varga_mechanisms_computed: false,
    divisional_charts_not_covered: 'ALL vargas other than D1 (D2 Horā, D9 Navāṃśa, D10 Daśāṃśa, D11 Rudrāṃśa/Ekādaśāṃśa, D12, …)',
    special_lagnas_not_covered: 'ALL special lagnas (Indu, Ārūḍha, Horā, Ghaṭī, Śrī, Bhāva, Varṇada, Vighaṭī)',
    note:
      'Every row in this response is a mechanism detected on the RĀŚI (D1) natal graph. ' +
      'bodha_mechanisms carries no varga dimension — bo_yantra_mechanism builds its ' +
      'dispositor/lordship/aspect topology from D1 placements alone, and stamps every row ' +
      "snapshot_type='static_natal'. No cross-varga (D2/D9/D10/D11/…) or special-lagna " +
      '(Indu Lagna, Ārūḍha) MECHANISM — a named multi-node structure spanning divisional ' +
      'charts — is computed anywhere in this instrument. If your question named a divisional ' +
      'chart or a special lagna, THIS RESPONSE DOES NOT ANSWER THAT PART OF IT — read the ' +
      'drill pointers below rather than reading these D1 rows as a cross-varga convergence ' +
      'finding (F-107). The closest real answer is ganita_vichara_get\'s varga_ratification ' +
      'family (a per-graha agree/oppose vote across a domain\'s ratified operative vargas); ' +
      'it is genuine cross-varga convergence evidence, but per-graha, not a mechanism, and it ' +
      'covers no special lagna.',
    drill_pointers: [
      {
        // The ONE genuine cross-varga convergence primitive this instrument has. It is a
        // per-graha agree/oppose vote across a domain's ratified operative-varga set, NOT a
        // named multi-node mechanism — but for "does the divisional evidence converge or
        // diverge on this domain?" it is the real, built, classically-grounded answer, and
        // it is strictly closer to the question than any D1 mechanism row here.
        instrument: 'ganita_vichara_get',
        serves:
          "family='varga_ratification' (+ 'varga_ratification_divergence'), domain='wealth'|'career'|'marriage'|'health'|'general' — " +
          'per-graha ratification_factor ∈ [0.6,1.4] computed as an agree/oppose vote of each operative varga against the D1 ' +
          'dignity direction, with a per_varga relation map and constituent_fact_ids resolving to chart_facts.',
        note:
          `The wealth entry's operative-varga set is ${wealthVargasDisplay} with domain_provisional=${wealthProvisionalDisplay} — the only ` +
          'design-RATIFIED (non-provisional) domain set in brahma_vichara_constants.operative_vargas. D1 is the reference ' +
          'and never votes. Note this covers vargas only: Indu Lagna is a special lagna, not a varga, and takes part in NO ' +
          'ratification vote anywhere. Formula: varga_ratification_v1, DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §11.',
      },
      {
        instrument: 'assess_wealth',
        serves: 'D2 (Horā) + D11 (Rudrāṃśa/Ekādaśāṃśa) per-graha varga dignity AND Indu Lagna, consumed directly from L1 — see `varga_analysis.per_varga` and `varga_analysis.indu_lagna`.',
        note: 'The only surface today that joins BOTH classical wealth vargas plus the Jaimini wealth lagna. It serves them as separate evidence layers — it does NOT compute a convergence mechanism across them either.',
      },
      {
        instrument: 'ganita_chart_facts_get',
        serves: 'divisional_chart="D2" | "D11" | any varga — full per-varga placements, dignity, house lords/occupants, per-varga Ashtakavarga (chart_divisionals-native EAV facts).',
      },
      {
        instrument: 'ganita_special_lagnas_get',
        serves: 'categories=["special_lagna"] — INDU_LAGNA (sign, sign_lord, house_d1, nakshatra) and the other special lagnas, two_pass_verified.',
      },
      {
        instrument: 'bodha_signals_get',
        serves: 'MSR signal class `varga_ratification_divergence` — whether a divisional chart confirms or contradicts the rāśi promise, per signal. This is per-signal ratification, NOT a cross-varga mechanism.',
      },
    ],
  }
}

export const queryMechanismsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_mechanisms',
  type:  'tool',
  layer: 'L2',
  name:  'query_mechanisms',
  semantic_capabilities: MECHANISM_SCUS,

  description: [
    'Retrieve named, valenced Mechanism (Yantra) objects from bodha_mechanisms — the',
    'first-class CGM-subgraph mechanisms the bo_yantra_mechanism writer builds. Each row:',
    'mechanism_name, mechanism_class (convergent_dispositor_chain | dispositor_cycle |',
    'house_lordship_cycle | yoga_cluster | mutual_reception | parivartana_chain | stellium |',
    'mutual_aspect | mutual_aspect_triangle | graha_bhava_affliction), valence',
    '(benefic|malefic|mixed|neutral), member_node_ids / member_edge_ids composition,',
    'edge_strength_avg/min/max (DR-7 edge_strength_v1 provenance), centrality_summary, and a',
    'grounding citation. The chain/circuit family (multi-node named mechanisms) is served',
    'FIRST and can be isolated via chain_circuit_only. Filters: ayanamsha_id, mechanism_class,',
    'valence, chain_circuit_only. Per-class and per-valence facet counts over the full match',
    'set are always returned. Bounded (LIMIT ≤50) with a disclosed total and build-pinned cursor pagination,',
    'and an honest empty_reason when a chart carries no mechanisms.',
    'SCOPE (F-107): mechanisms are detected on the RĀŚI (D1) natal graph ONLY — bodha_mechanisms',
    'has no varga dimension. NO cross-varga (D2/D9/D10/D11/…) or special-lagna (Indu Lagna,',
    'Ārūḍha) convergence mechanism is computed anywhere in this instrument. If a question names a',
    'divisional chart or a special lagna, this tool does NOT answer that part of it; the response',
    'carries a `varga_scope` block with drill pointers to the surfaces that do serve per-varga data',
    '(assess_wealth varga_analysis, ganita_chart_facts_get divisional_chart=…, ganita_special_lagnas_get).',
  ].join(' '),

  input_schema: {
    chart_id:          { type: 'string',  description: 'Chart UUID. Required.', required: true },
    ayanamsha_id:      { type: 'string',  description: "Filter by ayanamsha (e.g. 'lahiri_chitrapaksha'). Omit for all 5." },
    mechanism_class:   { type: 'string',  description: 'Filter by a single mechanism_class. Omit for all.' },
    valence:           { type: 'string',  description: 'Filter by valence (benefic|malefic|mixed|neutral). Omit for all.' },
    chain_circuit_only:{ type: 'boolean', description: 'When true, return only the CR-24 chain/circuit family (convergent_dispositor_chain, dispositor_cycle, house_lordship_cycle). Default false.' },
    limit:             { type: 'number',  description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
    offset:            { type: 'number',  description: 'First-page offset only (default 0). A nonzero continuation must use page_cursor.' },
    page_cursor:       { type: 'string',  description: 'Opaque, signed continuation token from next_page_cursor. It pins the normalized filters and fresh/proven bo_yantra_mechanism build; changed/replacing builds require restart.' },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'graph_traversal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'graph',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 55, always_include: false },
  },
  density_contract: {
    paginated: true,
    facets: ['mechanism_class', 'valence', 'chain_circuit'],
    empty_reason: true,
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const mechanism_class = args['mechanism_class'] ? String(args['mechanism_class']) : null
    const valence = args['valence'] ? String(args['valence']) : null
    const chain_circuit_only = args['chain_circuit_only'] === true || args['chain_circuit_only'] === 'true'
    const limit = normalizeLimit(args['limit'])
    const requestedOffset = normalizeOffset(args['offset'])
    if ((args['page_cursor'] === undefined || args['page_cursor'] === null) && requestedOffset > 0) {
      return paginationError(chart_id, 'page_cursor_required', 'A nonzero offset is not a safe mechanism continuation; restart from the first page and use next_page_cursor.')
    }

    let signingRing: InquiryLifecycleSigningKeyRing
    try {
      signingRing = loadInquiryLifecycleSigningKeyRing()
    } catch {
      return paginationError(chart_id, 'page_cursor_signing_unavailable', 'Mechanism continuation signing is unavailable; this response cannot safely establish a pagination snapshot.')
    }

    const queryFilterFingerprint = filterFingerprint({
      chart_id,
      ayanamsha_id,
      mechanism_class,
      valence,
      chain_circuit_only,
    })
    let cursor: MechanismPageCursor | null = null
    if (args['page_cursor'] !== undefined && args['page_cursor'] !== null) {
      cursor = decodePageCursor(args['page_cursor'], signingRing)
      if (!cursor) {
        return paginationError(chart_id, 'invalid_page_cursor', 'The supplied page_cursor is malformed, unsigned, or outside the supported pagination range.')
      }
      if (cursor.filter_fingerprint !== queryFilterFingerprint) {
        return paginationError(chart_id, 'page_cursor_filter_mismatch', 'The supplied page_cursor was minted for different normalized query filters; restart from the first page.')
      }
    }
    const offset = cursor?.offset ?? requestedOffset

    const filters: string[] = ['d.chart_id = $1::uuid']
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id)    { filters.push(`d.ayanamsha_id = $${p++}`);    params.push(ayanamsha_id) }
    if (mechanism_class) { filters.push(`d.mechanism_class = $${p++}`); params.push(mechanism_class) }
    if (valence)         { filters.push(`d.valence = $${p++}`);         params.push(valence) }
    if (chain_circuit_only) {
      filters.push(`d.mechanism_class = ANY($${p++})`)
      params.push([...CHAIN_CIRCUIT_CLASSES])
    }
    const where = filters.join(' AND ')

    // The writer deletes every chart row before it inserts a replacement build. A bare offset
    // could therefore join two generations or mistake a partial deletion for exhaustion. Select
    // only a fresh/proven receipt with the reviewed output spec, page that exact build in the
    // same SQL statement, and compare every continuation cursor to the currently selected build.
    const assetIdParam = p++
    params.push(BO_YANTRA_MECHANISM_ASSET_ID)
    const specParam = p++
    params.push(BO_YANTRA_MECHANISM_OUTPUT_DIGEST_SPEC_SHA256)
    const cursorBuildParam = p++
    params.push(cursor?.build_id ?? null)

    // §N.6: chain/circuit family sorts FIRST (priority 0), everything else after (priority 1),
    // then by edge-strength and structural size. The class-priority list is passed as a param
    // so no mechanism-class string is hard-coded into the SQL text.
    const classPriorityParam = `$${p++}`
    params.push([...CHAIN_CIRCUIT_CLASSES])

    try {
      const pageResult = await query<{
        replacement_in_progress: boolean
        eligible_build_id: string | null
        cursor_build_changed: boolean
        rows: Record<string, unknown>[]
        facets: Array<{ mechanism_class: string; valence: string; is_chain_circuit: boolean; n: string }>
        total_matching: string
      }>(
        `WITH eligible_receipt AS (
           SELECT receipt.build_id::text AS build_id,
                  receipt.observed_at AS observed_at
             FROM asset_provenance_receipts receipt
             JOIN asset_freshness freshness
               ON freshness.asset_id = receipt.asset_id
              AND freshness.scope_key = receipt.scope_key
              AND freshness.partition_key = receipt.partition_key
              AND freshness.receipt_version = receipt.receipt_version
             JOIN build_runs receipt_run ON receipt_run.id = receipt.build_id
            WHERE receipt.asset_id = $${assetIdParam}::text
              AND receipt.chart_id = $1::uuid
              AND receipt.receipt_state = 'proven'
              AND receipt.output_digest_spec_sha256 = $${specParam}::text
              AND freshness.freshness_state = 'fresh'
              AND receipt_run.chart_id = $1::uuid
              AND receipt_run.state = 'completed'
            ORDER BY receipt.observed_at DESC, receipt.build_id DESC
            LIMIT 1
         ), replacement_fence AS (
           SELECT EXISTS (
             SELECT 1
               FROM build_run_assets fenced_asset
               JOIN build_runs fenced_run ON fenced_run.id = fenced_asset.run_id
              WHERE fenced_run.chart_id = $1::uuid
                AND fenced_asset.asset_id = $${assetIdParam}::text
                AND (
                  fenced_run.state IN ('planned', 'running', 'paused')
                  OR fenced_asset.state IN ('queued', 'building')
                  OR (
                    EXISTS (
                      SELECT 1 FROM eligible_receipt eligible
                       WHERE COALESCE(fenced_asset.ended_at, fenced_run.ended_at) IS NULL
                          OR COALESCE(fenced_asset.ended_at, fenced_run.ended_at) >= eligible.observed_at
                    )
                    AND NOT EXISTS (
                      SELECT 1
                        FROM asset_provenance_receipts proven_receipt
                        JOIN asset_freshness proven_freshness
                          ON proven_freshness.asset_id = proven_receipt.asset_id
                         AND proven_freshness.scope_key = proven_receipt.scope_key
                         AND proven_freshness.partition_key = proven_receipt.partition_key
                         AND proven_freshness.receipt_version = proven_receipt.receipt_version
                       WHERE proven_receipt.asset_id = fenced_asset.asset_id
                         AND proven_receipt.chart_id = $1::uuid
                         AND proven_receipt.build_id = fenced_run.id
                         AND proven_receipt.receipt_state = 'proven'
                         AND proven_receipt.output_digest_spec_sha256 = $${specParam}::text
                         AND proven_freshness.freshness_state = 'fresh'
                    )
                  )
                )
           ) AS replacement_in_progress
         ), page_rows AS (
           SELECT to_jsonb(d) AS row,
                  d.mechanism_class AS order_mechanism_class,
                  d.edge_strength_avg AS order_edge_strength_avg,
                  COALESCE(array_length(d.member_node_ids_array, 1), 0) AS order_member_node_count,
                  d.mechanism_name AS order_mechanism_name,
                  d.mechanism_id::text AS order_mechanism_id
             FROM bodha_mechanisms d
             JOIN eligible_receipt eligible ON d.build_id = eligible.build_id::uuid
            WHERE ${where}
            ORDER BY (d.mechanism_class = ANY(${classPriorityParam})) DESC,
                     d.edge_strength_avg DESC NULLS LAST,
                     COALESCE(array_length(d.member_node_ids_array, 1), 0) DESC,
                     d.mechanism_name ASC,
                     d.mechanism_id ASC
            LIMIT $${p} OFFSET $${p + 1}
         ), facet_rows AS (
           SELECT d.mechanism_class, d.valence,
                  (d.mechanism_class = ANY(${classPriorityParam})) AS is_chain_circuit
             FROM bodha_mechanisms d
             JOIN eligible_receipt eligible ON d.build_id = eligible.build_id::uuid
            WHERE ${where}
         ), facet_counts AS (
           SELECT mechanism_class, valence, is_chain_circuit, COUNT(*)::text AS n
             FROM facet_rows
            GROUP BY mechanism_class, valence, is_chain_circuit
         )
         SELECT fence.replacement_in_progress,
                eligible.build_id AS eligible_build_id,
                (eligible.build_id IS NOT NULL AND $${cursorBuildParam}::text IS NOT NULL
                  AND eligible.build_id <> $${cursorBuildParam}::text) AS cursor_build_changed,
                COALESCE((
                  SELECT jsonb_agg(page_rows.row ORDER BY
                    (page_rows.order_mechanism_class = ANY(${classPriorityParam})) DESC,
                    page_rows.order_edge_strength_avg DESC NULLS LAST,
                    page_rows.order_member_node_count DESC,
                    page_rows.order_mechanism_name ASC,
                    page_rows.order_mechanism_id ASC)
                    FROM page_rows
                ), '[]'::jsonb) AS rows,
                COALESCE((SELECT jsonb_agg(to_jsonb(facet_counts) ORDER BY mechanism_class ASC, valence ASC)
                  FROM facet_counts), '[]'::jsonb) AS facets,
                (SELECT COUNT(*)::text FROM facet_rows) AS total_matching
           FROM replacement_fence fence
           LEFT JOIN eligible_receipt eligible ON true`,
        [...params, limit + 1, offset],
      )
      const pageSnapshot = pageResult.rows[0]
      if (!pageSnapshot) {
        return paginationError(chart_id, 'bo_yantra_mechanism_receipt_unavailable', 'No consistent bo_yantra_mechanism receipt snapshot was available; restart after provenance is complete.')
      }
      if (pageSnapshot.replacement_in_progress) {
        return paginationError(chart_id, 'bo_yantra_mechanism_replacement_in_progress', 'A bo_yantra_mechanism replacement is in progress; restart after the asset and its fresh provenance receipt are complete.')
      }
      const activeBuildId = pageSnapshot.eligible_build_id
      if (!activeBuildId) {
        return paginationError(chart_id, 'bo_yantra_mechanism_receipt_unavailable', 'No fresh, proven bo_yantra_mechanism receipt with the reviewed digest specification is available for this chart.')
      }
      if (pageSnapshot.cursor_build_changed) {
        return paginationError(chart_id, 'page_cursor_build_changed', 'The fresh proven bo_yantra_mechanism receipt build changed after this page_cursor was minted; restart from the first page.', {
          cursor_build_id: cursor?.build_id ?? null,
          active_build_id: activeBuildId,
        })
      }

      // F-164: this is an ORIENTATION disclosure, not a scoring input — a genuine failure to
      // reach brahma_vichara_constants degrades the note to an honest "(unavailable)" rather
      // than failing the whole mechanisms query (B.10: never drop a real, otherwise-complete
      // response over an ancillary annotation). Contrast register_d9_judgment.ts/
      // register_d8_assess_domain.ts, where the operative-varga set gates real scoring/
      // consumption decisions and a missing row is correctly fatal.
      let wealthEntry: OperativeVargaEntry | undefined
      try {
        const constants = await getOperativeVargaConstants()
        wealthEntry = constants['wealth']
      } catch {
        wealthEntry = undefined
      }
      const varga_scope = buildVargaScopeDisclosure(wealthEntry)

      const total_matching = Number(pageSnapshot.total_matching ?? 0)
      const fetchedRows = Array.isArray(pageSnapshot.rows) ? pageSnapshot.rows : []
      const rows = fetchedRows.slice(0, limit)
      // The L+1 probe is the page-local continuation proof; total_matching and
      // facets remain full-filter aggregates for density reporting.
      const more_available = fetchedRows.length > limit

      const by_mechanism_class: Record<string, number> = {}
      const by_valence: Record<string, number> = {}
      let chain_circuit_count = 0
      const snapshotFacets = Array.isArray(pageSnapshot.facets) ? pageSnapshot.facets : []
      for (const f of snapshotFacets) {
        const n = Number(f.n)
        by_mechanism_class[f.mechanism_class] = (by_mechanism_class[f.mechanism_class] ?? 0) + n
        by_valence[f.valence] = (by_valence[f.valence] ?? 0) + n
        if (f.is_chain_circuit) chain_circuit_count += n
      }

      const empty_reason = total_matching === 0
        ? 'No mechanisms (bodha_mechanisms) exist for this chart under the given filters. ' +
          'Either bo_yantra_mechanism has not been built for this chart, or the chart legitimately ' +
          'carries no motif/chain/circuit structure matching the filters (a correct negative, not an error).'
        : null

      return {
        content: {
          chart_id,
          rows,
          count: rows.length,
          total_matching,
          more_available,
          next_offset: more_available ? offset + rows.length : null,
          next_page_cursor: more_available
            ? encodePageCursor({ version: 1, build_id: activeBuildId, offset: offset + rows.length, filter_fingerprint: queryFilterFingerprint }, signingRing)
            : null,
          build_id: activeBuildId,
          chain_circuit_count,
          facets: {
            by_mechanism_class,
            by_valence,
            chain_circuit_classes: [...CHAIN_CIRCUIT_CLASSES],
          },
          empty_reason,
          // F-107: scope honesty — these rows are D1-only, and the envelope says so.
          varga_scope,
          scope_flags: ['d1_rasi_only', 'cross_varga_mechanisms_not_computed'],
          filters: { ayanamsha_id, mechanism_class, valence, chain_circuit_only, limit, offset },
          provenance: {
            tables: ['bodha_mechanisms', 'asset_provenance_receipts', 'asset_freshness', 'build_runs', 'build_run_assets'],
            source: 'L2 Bodha mechanisms (bo_yantra_mechanism / migration 445); served chart-scoped, ' +
              'chain/circuit family first, budgeted. Edge-strength provenance: DR-7 edge_strength_v1. ' +
              'Pagination is pinned to the fresh/proven bo_yantra_mechanism build_id; a changed or replacing build requires restart. ' +
              'SCOPE: rāśi (D1) natal graph ONLY — no varga dimension exists in this table (F-107); ' +
              'see `varga_scope` for the disclosure and the drill pointers to per-varga surfaces.',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}

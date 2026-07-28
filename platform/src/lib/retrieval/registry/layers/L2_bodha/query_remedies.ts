/**
 * query_remedies — Remedy Surface Query (L2 Bodha)
 * =================================================
 * Queries the Bodha remedy layer (bo_upaya) via two tables:
 *   - bodha_rm_resonances: 45 rows — remedy resonance targets keyed to bo_laksana signals
 *   - bodha_rm_remedy_prescriptions: 135 rows — prescriptions with tradition + feasibility
 *
 * Returns resonance targets + prescriptions, optionally filtered by tradition.
 * NOTE: bodha_rm_resonances carries no signal_id column — resonances key to grahas
 * (graha + resonance_score) and link to CDLM cells / motifs / doshas via the
 * associated_*_array columns, not directly to bodha_msr_signals. emits_references
 * is therefore false (no signal_id references are emitted by this tool).
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 *
 * R5.3 B2 (bodha_remedies_get) narration synthesis
 * -------------------------------------------------
 * DATA-GAP (writer-level, out of this tool's scope — see R5_3_RUN_LEDGER):
 * `associated_doshas_array` (resonances) and `estimated_cost_inr_range_jsonb`
 * (prescriptions) are 100% NULL DB-wide across every chart currently built —
 * a bo_upaya-writer population gap, not a value dropped here. This handler
 * narrates around that gap honestly (named-affliction mapping from populated
 * fields; a qualitative, category-derived cost TIER labelled as an estimate)
 * rather than fabricating either field.
 *
 * REAL fix applied here: `citation_ref` / `citation_human` (both tables) and
 * `classical_sources_jsonb` (prescriptions) are 100% populated but were never
 * selected — they are now selected and narrated as the U-c inline classical
 * citation. Remaining always-null columns (associated_doshas_array/motifs_array
 * on resonances; estimated_cost_inr_range_jsonb/estimated_time_minutes_daily/
 * phase_sequence_class/phase_duration_days on prescriptions) and the redundant
 * prescription_detail_jsonb (duplicates remedy_label_human in every observed
 * row) are dropped from the default per-row payload to fund the narration text
 * within the existing byte ceiling; full raw rows remain available via
 * `fields=all`.
 *
 * SARVA-SIDDHI W-3 (CR-67 + CR-69):
 *  - CR-67: associated_cdlm_cells_array is no longer null DB-wide — the bo_upaya
 *    writer now populates it (each graha's material CDLM cross-domain-linkage
 *    cells). The `domain` filter therefore now selects real domain-joined
 *    resonances; compact rows surface associated_cdlm_cell_count.
 *  - CR-69: this tool now reads `leverage_ranked` and ranks targets by the L1
 *    chart_vichara.leverage_index composite (§N.5, read-not-recomputed). See
 *    LEVERAGE_FORMULA_DOC.
 *
 * PARISHODHANA B1 (R-29/EL-51 follow-up) — two serving-layer fixes:
 *  - `tradition` filter was matching ONLY the `tradition` column, which the
 *    bo_upaya writer always sets to the literal string 'parashari' for every
 *    prescription row it writes — the mantra/gemstone/charity/vrata/yantra/
 *    ayurvedic axis this param's own enum documents actually lives in
 *    `remedy_category`, a DIFFERENT column. `tradition=gemstone` (or any other
 *    enum value) therefore silently matched ZERO rows, always — including the
 *    tool's own `drill_pointers` hint recommending exactly that call. Fixed by
 *    OR-matching both columns: never narrows previously-correct results (there
 *    is currently only one `tradition` value in the data), and restores the
 *    documented single-category drill-down (mantra|gemstone|charity|...) the
 *    enum has always advertised.
 *  - `maraka_contraindication_verdict` (β.G/EL-51, VERIFIED-CLOSED 2026-07-25 —
 *    a real, cited, deterministic BPHS Ch.44 verdict computed by bo_upaya for
 *    every gemstone-category prescription) was written into
 *    `prescription_detail_jsonb`, which the compact (default) output path drops
 *    entirely as "redundant" — so this safety-relevant, already-computed field
 *    was invisible unless a caller both discovered the correct `fields='all'`
 *    escape hatch *and* could reach it (it wasn't declared on the MCP alias
 *    schema either — see register_p1_aliases.ts fix). Now extracted and
 *    surfaced directly on the compact row (null when not a gemstone
 *    prescription — never fabricated), per the §N.6 Serving Density Principle:
 *    a confirmed, cited finding must not be silently dropped behind a recovery
 *    path a caller cannot reach.
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { DEFAULT_AYANAMSHA } from '../../constants'

// ── CR-69 (SARVA-SIDDHI W-3): leverage-ranked remedy synthesis ──────────────
// intervention_synthesis calls this tool with `leverage_ranked: true`, but the
// arg was never read and no leverage_index axis was exposed (the documented
// CR-69 gap). leverage_index is the L1 ga_vichara composite already stored per
// (graha × domain) in chart_vichara.leverage_index — it is READ here, never
// recomputed (§N.5 — L1 is the authority over L2+ derivations).
//
//   leverage_index = (domain load-bearing weight ÷ graha capability)
//                     × forward daśā runway weight
//
// where the three factors (domain_load_bearing_weight_normalized, capability,
// dasha_runway_weight) are ga_vichara's registry-weighted terms — domain load
// from lordship/karakatva/occupancy/yoga-participation weights held in
// brahma_vichara_constants (design §8/§11, formula_version leverage_index_v1),
// capability from shadbala percentile + dignity + ratification, runway from the
// graha's next/current Vimśottarī Mahādaśā proximity. A high leverage_index =
// the graha most structurally on the hook for the domain relative to its own
// capability, forward-weighted by when its daśā opens — i.e. the highest-yield
// remedy target.
const LEVERAGE_FORMULA_DOC =
  'leverage_index = (domain_load_bearing_weight_normalized ÷ capability) × ' +
  'dasha_runway_weight. Source: L1 chart_vichara.leverage_index ' +
  '(ga_vichara formula_version leverage_index_v1, design §8/§11; classical ' +
  'load weights — lordship/karakatva/occupancy/yoga-participation — from the ' +
  'brahma_vichara_constants registry). Read here, not recomputed (§N.5).'

// chart_vichara.subject uses L1 planet codes; resonances/prescriptions use the
// title-case graha name. Reverse of the sidecar _SUBJECT_TO_PLANET map.
const SUBJECT_TO_GRAHA: Record<string, string> = {
  SUN: 'Sun', MOON: 'Moon', MAR: 'Mars', MER: 'Mercury', JUP: 'Jupiter',
  VEN: 'Venus', SAT: 'Saturn', RAH_MEAN: 'Rahu', KET_MEAN: 'Ketu',
}

interface LeverageEntry {
  leverage_index: number
  leverage_domain: string
  domain_load_bearing_weight_normalized: number | null
  capability: number | null
  dasha_runway_weight: number | null
  constituent_fact_ids: unknown
}

// Build graha → leverage entry. When `domain` is given, rank by that domain's
// leverage_index (falling back to the chart-wide 'general' domain if the queried
// domain carries no leverage rows — e.g. spirituality/progeny, which ga_vichara
// does not score for load-bearing weight). With no domain, each graha takes its
// single highest-leverage domain (its peak structural exposure).
async function fetchLeverageByGraha(
  chart_id: string,
  ayanamsha_id: string,
  domain: string | undefined,
): Promise<{ map: Map<string, LeverageEntry>; resolvedDomain: string | null; note: string | null }> {
  const runQuery = async (dom: string | null) => {
    const conds = ["chart_id = $1", "ayanamsha_id = $2", "vichara_family = 'leverage_index'", 'value_num IS NOT NULL', 'value_num > 0']
    const params: unknown[] = [chart_id, ayanamsha_id]
    if (dom) { conds.push(`domain = $${params.length + 1}`); params.push(dom) }
    const sql = `SELECT subject, domain, value_num, value_jsonb, constituent_fact_ids
                 FROM chart_vichara WHERE ${conds.join(' AND ')} ORDER BY value_num DESC`
    return (await query<Record<string, unknown>>(sql, params)).rows
  }

  let resolvedDomain: string | null = domain ?? null
  let note: string | null = null
  let rows = await runQuery(domain ?? null)

  if (domain && rows.length === 0) {
    // Queried domain is not load-bearing-scored by ga_vichara — fall back to
    // the chart-wide 'general' leverage domain rather than return nothing.
    rows = await runQuery('general')
    if (rows.length > 0) {
      resolvedDomain = 'general'
      note = `No leverage_index rows for domain='${domain}' (ga_vichara does not score it for load-bearing weight); ranked by the chart-wide 'general' leverage domain instead.`
    } else {
      resolvedDomain = null
      note = `No leverage_index rows for domain='${domain}' or 'general'; leverage ranking unavailable — falling back to resonance_score order.`
    }
  }

  const map = new Map<string, LeverageEntry>()
  for (const r of rows) {
    const graha = SUBJECT_TO_GRAHA[String(r['subject'] ?? '')]
    if (!graha) continue
    const lev = Number(r['value_num'])
    const existing = map.get(graha)
    // With no domain filter, keep each graha's single strongest-leverage domain.
    if (existing && existing.leverage_index >= lev) continue
    const j = (r['value_jsonb'] as Record<string, unknown> | null) ?? {}
    map.set(graha, {
      leverage_index: lev,
      leverage_domain: String(r['domain'] ?? resolvedDomain ?? 'general'),
      domain_load_bearing_weight_normalized: j['domain_load_bearing_weight_normalized'] != null ? Number(j['domain_load_bearing_weight_normalized']) : null,
      capability: j['capability'] != null ? Number(j['capability']) : null,
      dasha_runway_weight: j['dasha_runway_weight'] != null ? Number(j['dasha_runway_weight']) : null,
      constituent_fact_ids: r['constituent_fact_ids'] ?? null,
    })
  }
  return { map, resolvedDomain, note }
}

// ── Bo_upaya-wide data-gap honesty note (U-b) ──────────────────────────────
const DATA_GAP_NOTE =
  'bo_upaya data-population gap (writer-level, not dropped here): ' +
  'associated_doshas_array (formal named-dosha tagging on resonances) and ' +
  'estimated_cost_inr_range_jsonb (exact INR cost on prescriptions) remain ' +
  'NULL for every chart built so far. Named-affliction mapping below ' +
  'is derived instead from graha + remedy_priority_class + weakest_rank_in_chart ' +
  '+ is_yoga_karaka_flag; cost is a qualitative tier derived from ' +
  'remedy_category + ritual_complexity_class, not a computed INR figure. ' +
  '(CR-67 CLOSED: associated_cdlm_cells_array is now populated — resonances ' +
  'carry their material CDLM cross-domain-linkage cells; use domain=… to join.)'

// ── Qualitative cost-tier derivation (category + complexity -> tier label) ─
function costTierFor(remedy_category: unknown, ritual_complexity_class: unknown): string {
  const cat = String(remedy_category ?? '').toLowerCase()
  const complexity = String(ritual_complexity_class ?? '').toLowerCase()
  if (cat === 'mantra' || cat === 'japa' || cat === 'behavioral') return 'free/low (category-derived estimate)'
  if (cat === 'charity' || cat === 'dana' || cat === 'vrata') return 'low-moderate (category-derived estimate)'
  if (cat === 'gemstone') return 'high (category-derived estimate)'
  if (cat === 'homa' || cat === 'yantra' || cat === 'ritual' || cat === 'puja') return 'moderate-high (category-derived estimate)'
  if (complexity === 'simple') return 'free/low (complexity-derived estimate)'
  if (complexity === 'complex') return 'high (complexity-derived estimate)'
  return 'moderate (complexity-derived estimate)'
}

function classicalCitation(classical_sources_jsonb: unknown): string | null {
  if (classical_sources_jsonb && typeof classical_sources_jsonb === 'object') {
    const c = (classical_sources_jsonb as Record<string, unknown>)['citation']
    if (typeof c === 'string' && c.length > 0) return c
  }
  return null
}

// PARISHODHANA B1 (EL-51 follow-up): pull the already-computed maraka-contraindication
// verdict (β.G, BPHS Ch.44-cited, deterministic, gemstone-category rows only) out of
// prescription_detail_jsonb so it survives the compact-mode column drop. Returns null
// for every non-gemstone row (and for gemstone rows where the writer found no
// contraindication) — never fabricated, just no longer hidden.
function marakaVerdictFrom(prescription_detail_jsonb: unknown): Record<string, unknown> | null {
  if (prescription_detail_jsonb && typeof prescription_detail_jsonb === 'object') {
    const v = (prescription_detail_jsonb as Record<string, unknown>)['maraka_contraindication_verdict']
    if (v && typeof v === 'object') return v as Record<string, unknown>
  }
  return null
}

function namedAfflictionLabel(row: Record<string, unknown>): string {
  const graha = String(row['graha'] ?? 'unknown')
  const rank = row['weakest_rank_in_chart']
  const isYK = row['is_yoga_karaka_flag'] === true
  const rankPart = typeof rank === 'number' ? `rank ${rank} in the chart` : 'rank unranked'
  return `${graha} weakness (${rankPart}, ${isYK ? 'yogakaraka' : 'non-yogakaraka'})`
}

export const queryRemediesCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_remedies',
  type:  'tool',
  layer: 'L2',
  name:  'query_remedies',

  description: [
    'Returns the Bodha remedy layer for a chart: graha resonance targets + prescriptions.',
    'Sources: bodha_rm_resonances (graha-keyed remedy targets ranked by resonance_score) and',
    'bodha_rm_remedy_prescriptions (tradition-categorized prescriptions).',
    'Filterable by tradition (mantra, gemstone, charity, vrata, yantra, ayurvedic).',
    'Resonances link to CDLM cells, motifs, and doshas via associated_*_array columns.',
    'Prescriptions include feasibility_score, cost/time estimates, sequencing, and ritual flags.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'rich_relational',
  traversal_level: 'L-DOMAIN',
  tool_role: 'drill',
  emits_references: false,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  register: { reader_label: 'Consulting the chart — Remedial tradition' },

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha filter (default: 'lahiri_chitrapaksha').",
    },
    tradition: {
      type: 'string',
      description: 'Filter prescriptions by tradition: mantra|gemstone|charity|vrata|yantra|ayurvedic.',
      enum: ['mantra', 'gemstone', 'charity', 'vrata', 'yantra', 'ayurvedic'],
    },
    graha: {
      type: 'string',
      description: 'Filter resonances by target graha (e.g. Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu).',
    },
    fields: {
      type: 'string',
      description: "'compact' (default) narrates + drops always-null/redundant columns; 'all' returns full raw rows (recovery path for associated_*_array, estimated_cost_inr_range_jsonb, prescription_detail_jsonb, etc.).",
      enum: ['compact', 'all'],
    },
    domain: {
      type: 'string',
      description: 'Filter resonances to those linked (via associated_cdlm_cells_array) to a ' +
        'CDLM cell whose domain_row or domain_col matches this life domain (e.g. career, wealth, ' +
        'relationship, health). Optional.',
    },
    keyword: {
      type: 'string',
      description: 'Case-insensitive substring filter on prescription remedy_label_human / ' +
        'remedy_category / sub_tradition. Optional.',
    },
    limit: {
      type: 'number',
      description: 'Max rows to return per section (resonances, prescriptions). Default: all ' +
        '(45 resonances / 135 prescriptions); max: 200.',
    },
    leverage_ranked: {
      type: 'boolean',
      description: 'When true, rank resonance targets by L1 leverage_index = ' +
        '(domain load-bearing weight ÷ graha capability) × forward daśā runway ' +
        '(read from chart_vichara, §N.5). Pair with `domain` for a domain-specific ' +
        'leverage rank; without a domain each graha takes its peak-leverage domain. ' +
        'This is the intervention_synthesis primitive axis.',
    },
  },

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable:  true,
    },
    bulk_context: {
      pre_fetch_priority: 25,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const ayanamsha_id   = (args['ayanamsha_id'] as string | undefined) ?? DEFAULT_AYANAMSHA
    const tradition      = args['tradition'] as string | undefined
    const graha          = args['graha'] as string | undefined
    const fields         = ((args['fields'] as string | undefined) ?? 'compact').toLowerCase()
    const includeAll     = fields === 'all'
    const domain         = args['domain'] as string | undefined
    const keyword        = args['keyword'] as string | undefined
    const limit          = args['limit'] != null ? Math.min(Number(args['limit']), 200) : undefined
    const leverageRanked = args['leverage_ranked'] === true || String(args['leverage_ranked']).toLowerCase() === 'true'

    try {
      // Resonances (graha-keyed; no signal_id column on this table)
      const resConds = ['chart_id = $1', 'ayanamsha_id = $2']
      const resParams: unknown[] = [chart_id, ayanamsha_id]
      let rp = 3
      // CR-42/CR-10 fix (D-1.6 S-1): was an exact-match `graha = $` with no case
      // normalization, unlike every sibling L0 remedy handler (query_remedy_corpus,
      // query_remedies_by_planet, etc., all use LOWER(x) = LOWER($)). bodha_rm_resonances
      // stores graha as capitalized full names ("Saturn", "Venus", ...) — a caller
      // passing lowercase ("saturn") silently got ZERO resonance rows back instead of
      // Saturn's rows. Case-insensitive match closes the gap.
      if (graha) { resConds.push(`LOWER(graha) = LOWER($${rp++})`); resParams.push(graha) }
      if (domain) {
        resConds.push(
          `EXISTS (SELECT 1 FROM bodha_cdlm_cells cc WHERE cc.cell_id = ANY(bodha_rm_resonances.associated_cdlm_cells_array) ` +
          `AND (cc.domain_row = $${rp} OR cc.domain_col = $${rp}))`
        )
        resParams.push(domain)
        rp++
      }

      let resonanceSql = `
        SELECT resonance_id, graha, resonance_score, weakness_score,
               contradiction_factor, domain_burden, motif_burden,
               remedy_priority_class, is_yoga_karaka_flag, weakest_rank_in_chart,
               associated_doshas_array, associated_motifs_array,
               associated_cdlm_cells_array, citation_ref, citation_human, computed_at
        FROM bodha_rm_resonances
        WHERE ${resConds.join(' AND ')}
        ORDER BY resonance_score DESC NULLS LAST
      `
      if (limit != null) {
        resParams.push(limit)
        resonanceSql += ` LIMIT $${resParams.length}`
      }

      // Prescriptions
      const preConds = ['chart_id = $1', 'ayanamsha_id = $2']
      const preParams: unknown[] = [chart_id, ayanamsha_id]
      let pp = 3
      // PARISHODHANA B1 fix: `tradition` (schema-tradition, e.g. parashari) and
      // `remedy_category` (mantra/gemstone/charity/vrata/yantra/ayurvedic — what this
      // param's own enum documents) are different columns. bo_upaya always writes
      // tradition='parashari', so a category-style value would previously match zero
      // rows. OR-match both so the documented category filter actually works, without
      // narrowing any query that a real future `tradition` value would still match.
      if (tradition)  { preConds.push(`(LOWER(tradition) = LOWER($${pp}) OR LOWER(remedy_category) = LOWER($${pp}))`); preParams.push(tradition); pp++ }
      // CR-42/CR-10 fix (D-1.6 S-1): same case-sensitivity gap as the resonance-side
      // filter above, on target_graha.
      if (graha)      { preConds.push(`LOWER(target_graha) = LOWER($${pp++})`); preParams.push(graha) }
      if (keyword) {
        preConds.push(
          `(remedy_label_human ILIKE $${pp} OR remedy_category ILIKE $${pp} OR sub_tradition ILIKE $${pp})`
        )
        preParams.push(`%${keyword}%`)
        pp++
      }
      if (domain) {
        preConds.push(
          `EXISTS (SELECT 1 FROM bodha_rm_resonances rr JOIN bodha_cdlm_cells cc ON cc.cell_id = ANY(rr.associated_cdlm_cells_array) ` +
          `WHERE rr.resonance_id = bodha_rm_remedy_prescriptions.target_resonance_id AND (cc.domain_row = $${pp} OR cc.domain_col = $${pp}))`
        )
        preParams.push(domain)
        pp++
      }

      let prescriptionSql = `
        SELECT prescription_id, target_resonance_id, target_graha, tradition,
               sub_tradition, remedy_category, remedy_label_human,
               prescription_detail_jsonb, classical_strength_rating,
               classical_sources_jsonb, citation_ref, citation_human,
               feasibility_score, estimated_cost_inr_range_jsonb,
               estimated_time_minutes_daily, ritual_complexity_class,
               requires_acharya_review_flag, phase_sequence_class,
               phase_duration_days, computed_at
        FROM bodha_rm_remedy_prescriptions
        WHERE ${preConds.join(' AND ')}
        ORDER BY phase_sequence_class NULLS LAST, feasibility_score DESC NULLS LAST
      `
      if (limit != null) {
        preParams.push(limit)
        prescriptionSql += ` LIMIT $${preParams.length}`
      }

      const [resResult, preResult] = await Promise.all([
        query<Record<string, unknown>>(resonanceSql, resParams),
        query<Record<string, unknown>>(prescriptionSql, preParams),
      ])

      const resRows = resResult.rows
      const preRows = preResult.rows

      // ── CR-69: leverage-ranked synthesis (reads L1 chart_vichara.leverage_index) ─
      const leverageInfo = leverageRanked
        ? await fetchLeverageByGraha(chart_id, ayanamsha_id, domain)
        : null
      const leverageMap = leverageInfo?.map ?? new Map()
      const leverageActive = leverageRanked && leverageMap.size > 0
      const levFor = (r: Record<string, unknown>) => leverageMap.get(String(r['graha'])) ?? null

      // When leverage-ranked AND leverage rows exist, order resonance targets by
      // leverage_index DESC (grahas with no leverage row keep their relative
      // resonance_score order and sort last). Otherwise keep resonance_score order.
      const orderedResRows = leverageActive
        ? [...resRows].sort((a, b) => {
            const la = levFor(a)?.leverage_index ?? -1
            const lb = levFor(b)?.leverage_index ?? -1
            if (lb !== la) return lb - la
            return Number(b['resonance_score'] ?? 0) - Number(a['resonance_score'] ?? 0)
          })
        : resRows

      // ── U-a verdict-first lead ──────────────────────────────────────────────
      const topRow = orderedResRows[0]
      const secondaryGrahas = orderedResRows.slice(1, 4).map((r) => String(r['graha']))
      const leadSentence = topRow
        ? (leverageActive
            ? `Your highest-leverage remedy target is ${String(topRow['graha'])}` +
              ` — leverage_index ${Number(levFor(topRow)?.leverage_index ?? 0).toFixed(3)}` +
              ` (domain '${String(levFor(topRow)?.leverage_domain ?? leverageInfo?.resolvedDomain ?? 'general')}'),` +
              ` resonance_score ${Number(topRow['resonance_score']).toFixed(3)}, priority class ${String(topRow['remedy_priority_class'])}` +
              (secondaryGrahas.length ? ` — followed by ${secondaryGrahas.join(', ')}.` : '.')
            : `Your Bodha remedy layer flags ${String(topRow['graha'])} as your #1 remedy-priority target` +
              ` — resonance_score ${Number(topRow['resonance_score']).toFixed(3)}, priority class ${String(topRow['remedy_priority_class'])}` +
              (secondaryGrahas.length ? ` — followed by ${secondaryGrahas.join(', ')}.` : '.'))
        : `No resonance rows found for chart ${chart_id}${graha ? ` (graha filter: ${graha})` : ''}.`

      // ── resonance_ranked_present: prose ranking of ALL resonance rows ─────
      const resonanceRanked = orderedResRows.map((r, i) => {
        const lev = levFor(r)
        return {
          rank: i + 1,
          graha: r['graha'],
          resonance_score: r['resonance_score'],
          weakness_score: r['weakness_score'],
          contradiction_factor: r['contradiction_factor'],
          remedy_priority_class: r['remedy_priority_class'],
          is_yoga_karaka_flag: r['is_yoga_karaka_flag'],
          weakest_rank_in_chart: r['weakest_rank_in_chart'],
          ...(leverageRanked ? { leverage_index: lev?.leverage_index ?? null, leverage_domain: lev?.leverage_domain ?? null } : {}),
          named_affliction_mapping: namedAfflictionLabel(r),
          citation: r['citation_human'] ?? r['citation_ref'] ?? null,
        }
      })

      // ── compact resonance rows (drop always-null array columns; keep scalars) ─
      const resonancesCompact = orderedResRows.map((r) => {
        const lev = levFor(r)
        return {
          resonance_id: r['resonance_id'],
          graha: r['graha'],
          resonance_score: r['resonance_score'],
          weakness_score: r['weakness_score'],
          contradiction_factor: r['contradiction_factor'],
          domain_burden: r['domain_burden'],
          motif_burden: r['motif_burden'],
          remedy_priority_class: r['remedy_priority_class'],
          is_yoga_karaka_flag: r['is_yoga_karaka_flag'],
          weakest_rank_in_chart: r['weakest_rank_in_chart'],
          // CR-67: associated_cdlm_cells_array is now populated (real, L1-grounded
          // CDLM cross-domain-linkage cells this graha is a material constituent
          // of). Surface the count in compact mode; full uuid list via fields=all.
          associated_cdlm_cell_count: Array.isArray(r['associated_cdlm_cells_array'])
            ? (r['associated_cdlm_cells_array'] as unknown[]).length : 0,
          ...(leverageRanked ? { leverage_index: lev?.leverage_index ?? null, leverage_domain: lev?.leverage_domain ?? null } : {}),
          named_affliction_mapping: namedAfflictionLabel(r),
          computed_at: r['computed_at'],
        }
      })

      // ── CR-69 leverage_ranked block (explicit, machine-readable rank axis) ──
      const leverageRankedBlock = leverageRanked
        ? {
            available: leverageActive,
            ranked_domain: leverageInfo?.resolvedDomain ?? null,
            formula: LEVERAGE_FORMULA_DOC,
            note: leverageInfo?.note ?? null,
            ranking: orderedResRows
              .map((r) => {
                const lev = levFor(r)
                return lev
                  ? {
                      graha: r['graha'],
                      leverage_index: lev.leverage_index,
                      leverage_domain: lev.leverage_domain,
                      domain_load_bearing_weight_normalized: lev.domain_load_bearing_weight_normalized,
                      capability: lev.capability,
                      dasha_runway_weight: lev.dasha_runway_weight,
                      grounds_to_l1_fact_ids: lev.constituent_fact_ids,
                    }
                  : null
              })
              .filter((x) => x !== null),
          }
        : null

      // ── compact prescription rows (drop redundant/always-null fields;
      // add derived qualitative cost tier + wired-in citation) ──────────────
      const prescriptionsCompact = preRows.map((r) => {
        const citation = classicalCitation(r['classical_sources_jsonb'])
        return {
          prescription_id: r['prescription_id'],
          target_resonance_id: r['target_resonance_id'],
          target_graha: r['target_graha'],
          tradition: r['tradition'],
          sub_tradition: r['sub_tradition'],
          remedy_category: r['remedy_category'],
          remedy_label_human: r['remedy_label_human'],
          classical_strength_rating: r['classical_strength_rating'],
          feasibility_score: r['feasibility_score'],
          ritual_complexity_class: r['ritual_complexity_class'],
          requires_acharya_review_flag: r['requires_acharya_review_flag'],
          cost_tier_estimate: costTierFor(r['remedy_category'], r['ritual_complexity_class']),
          classical_citation: citation,
          // PARISHODHANA B1 (EL-51 follow-up): surfaced from prescription_detail_jsonb —
          // non-null only for gemstone-category rows the bo_upaya writer scored (BPHS
          // Ch.44-cited, deterministic). See marakaVerdictFrom() doc comment.
          maraka_contraindication_verdict: marakaVerdictFrom(r['prescription_detail_jsonb']),
          computed_at: r['computed_at'],
        }
      })

      // ── U-f drill_pointers ──────────────────────────────────────────────
      const drillPointers = [
        {
          type: 'refine',
          instrument: 'bodha_remedies_get',
          hint: 'Call again with tradition=gemstone|mantra|charity for a deeper single-tradition cut.',
        },
        {
          // SC-19 fix: this entry documents a BUILD-STATE fact about the bo_upaya writer/
          // asset — it is not a callable recovery pointer, so it must not use the `instrument`
          // field (a tool-pointer field elsewhere in this shape). `asset_id` names the L2
          // asset the gap belongs to without implying it's an MCP tool a client can call.
          type: 'build_state',
          asset_id: 'bo_upaya',
          hint: 'associated_doshas_array and estimated_cost_inr_range_jsonb remain unpopulated bo_upaya-wide — see build-state ledger (writer gap, not a serving-layer drop). associated_cdlm_cells_array is now populated (CR-67 closed).',
        },
        ...(fields !== 'all'
          ? [{ type: 'recover', instrument: 'bodha_remedies_get', hint: "Call with fields='all' for full raw rows (associated_*_array, estimated_cost_inr_range_jsonb, prescription_detail_jsonb)." }]
          : []),
      ]

      const narration = {
        lead: leadSentence,
        resonance_ranked: resonanceRanked,
        data_gap_note: DATA_GAP_NOTE,
      }

      return {
        content: {
          chart_id,
          ayanamsha_id,
          narration,
          resonances:           includeAll ? orderedResRows : resonancesCompact,
          resonance_count:      resRows.length,
          prescriptions:        includeAll ? preRows : prescriptionsCompact,
          prescription_count:   preRows.length,
          ...(leverageRanked ? { leverage_ranked: leverageRankedBlock } : {}),
          filters: { tradition, graha, fields, domain: domain ?? null, keyword: keyword ?? null, limit: limit ?? null, leverage_ranked: leverageRanked },
          drill_pointers: drillPointers,
          provenance: {
            tables: leverageRanked
              ? ['bodha_rm_resonances', 'bodha_rm_remedy_prescriptions', 'chart_vichara']
              : ['bodha_rm_resonances', 'bodha_rm_remedy_prescriptions'],
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

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
 * citation. Always-null columns (associated_doshas_array/motifs_array/
 * cdlm_cells_array on resonances; estimated_cost_inr_range_jsonb/
 * estimated_time_minutes_daily/phase_sequence_class/phase_duration_days on
 * prescriptions) and the redundant prescription_detail_jsonb (duplicates
 * remedy_label_human in every observed row) are dropped from the default
 * per-row payload to fund the narration text within the existing byte
 * ceiling; full raw rows remain available via `fields=all`.
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { DEFAULT_AYANAMSHA } from '../../constants'

// ── Bo_upaya-wide data-gap honesty note (U-b) ──────────────────────────────
const DATA_GAP_NOTE =
  'bo_upaya data-population gap (writer-level, not dropped here): ' +
  'associated_doshas_array (formal named-dosha tagging on resonances) and ' +
  'estimated_cost_inr_range_jsonb (exact INR cost on prescriptions) are ' +
  '100% NULL for every chart built so far. Named-affliction mapping below ' +
  'is derived instead from graha + remedy_priority_class + weakest_rank_in_chart ' +
  '+ is_yoga_karaka_flag; cost is a qualitative tier derived from ' +
  'remedy_category + ritual_complexity_class, not a computed INR figure.'

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

    try {
      // Resonances (graha-keyed; no signal_id column on this table)
      const resConds = ['chart_id = $1', 'ayanamsha_id = $2']
      const resParams: unknown[] = [chart_id, ayanamsha_id]
      let rp = 3
      if (graha) { resConds.push(`graha = $${rp++}`); resParams.push(graha) }

      const resonanceSql = `
        SELECT resonance_id, graha, resonance_score, weakness_score,
               contradiction_factor, domain_burden, motif_burden,
               remedy_priority_class, is_yoga_karaka_flag, weakest_rank_in_chart,
               associated_doshas_array, associated_motifs_array,
               associated_cdlm_cells_array, citation_ref, citation_human, computed_at
        FROM bodha_rm_resonances
        WHERE ${resConds.join(' AND ')}
        ORDER BY resonance_score DESC NULLS LAST
      `

      // Prescriptions
      const preConds = ['chart_id = $1', 'ayanamsha_id = $2']
      const preParams: unknown[] = [chart_id, ayanamsha_id]
      let pp = 3
      if (tradition)  { preConds.push(`tradition = $${pp++}`);  preParams.push(tradition) }
      if (graha)      { preConds.push(`target_graha = $${pp++}`); preParams.push(graha) }

      const prescriptionSql = `
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

      const [resResult, preResult] = await Promise.all([
        query<Record<string, unknown>>(resonanceSql, resParams),
        query<Record<string, unknown>>(prescriptionSql, preParams),
      ])

      const resRows = resResult.rows
      const preRows = preResult.rows

      // ── U-a verdict-first lead: top resonance(s) by resonance_score (already
      // ordered DESC by the query above) ────────────────────────────────────
      const topRow = resRows[0]
      const secondaryGrahas = resRows.slice(1, 4).map((r) => String(r['graha']))
      const leadSentence = topRow
        ? `Your Bodha remedy layer flags ${String(topRow['graha'])} as your #1 remedy-priority target` +
          ` — resonance_score ${Number(topRow['resonance_score']).toFixed(3)}, priority class ${String(topRow['remedy_priority_class'])}` +
          (secondaryGrahas.length ? ` — followed by ${secondaryGrahas.join(', ')}.` : '.')
        : `No resonance rows found for chart ${chart_id}${graha ? ` (graha filter: ${graha})` : ''}.`

      // ── resonance_ranked_present: prose ranking of ALL resonance rows ─────
      const resonanceRanked = resRows.map((r, i) => ({
        rank: i + 1,
        graha: r['graha'],
        resonance_score: r['resonance_score'],
        weakness_score: r['weakness_score'],
        contradiction_factor: r['contradiction_factor'],
        remedy_priority_class: r['remedy_priority_class'],
        is_yoga_karaka_flag: r['is_yoga_karaka_flag'],
        weakest_rank_in_chart: r['weakest_rank_in_chart'],
        named_affliction_mapping: namedAfflictionLabel(r),
        citation: r['citation_human'] ?? r['citation_ref'] ?? null,
      }))

      // ── compact resonance rows (drop always-null array columns; keep scalars) ─
      const resonancesCompact = resRows.map((r) => ({
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
        named_affliction_mapping: namedAfflictionLabel(r),
        computed_at: r['computed_at'],
      }))

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
          hint: 'associated_doshas_array and estimated_cost_inr_range_jsonb are unpopulated bo_upaya-wide — see build-state ledger for why (writer gap, not a serving-layer drop).',
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
          resonances:           includeAll ? resRows : resonancesCompact,
          resonance_count:      resRows.length,
          prescriptions:        includeAll ? preRows : prescriptionsCompact,
          prescription_count:   preRows.length,
          filters: { tradition, graha, fields },
          drill_pointers: drillPointers,
          provenance: {
            tables: ['bodha_rm_resonances', 'bodha_rm_remedy_prescriptions'],
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

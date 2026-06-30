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
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { DEFAULT_AYANAMSHA } from '../../constants'

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
               associated_cdlm_cells_array, computed_at
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

      return {
        content: {
          chart_id,
          ayanamsha_id,
          resonances:           resResult.rows,
          resonance_count:      resResult.rows.length,
          prescriptions:        preResult.rows,
          prescription_count:   preResult.rows.length,
          filters: { tradition, graha },
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

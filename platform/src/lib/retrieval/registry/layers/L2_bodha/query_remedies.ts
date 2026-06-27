/**
 * query_remedies — Remedy Surface Query (L2 Bodha)
 * =================================================
 * Queries the Bodha remedy layer (bo_upaya) via two tables:
 *   - bodha_rm_resonances: 45 rows — remedy resonance targets keyed to bo_laksana signals
 *   - bodha_rm_remedy_prescriptions: 135 rows — prescriptions with tradition + feasibility
 *
 * Returns resonance targets + prescriptions, optionally filtered by tradition and domain.
 * emits_references=true: resonance rows carry signal_id references back to bodha_msr_signals.
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'

export const queryRemediesCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_remedies',
  type:  'tool',
  layer: 'L2',
  name:  'query_remedies',

  description: [
    'Returns the Bodha remedy layer for a chart: resonance targets + prescriptions.',
    'Sources: bodha_rm_resonances (45 rows, signal-keyed remedy targets) and',
    'bodha_rm_remedy_prescriptions (135 rows, tradition-categorized prescriptions).',
    'Filterable by tradition (mantra, gemstone, charity, vrata, yantra, ayurvedic) and domain.',
    'Resonances carry signal_id references into bodha_msr_signals for provenance tracking.',
    'Prescriptions include feasibility_tier, economics, sequencing, and muhurta timing flags.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'rich_relational',
  traversal_level: 'L-DOMAIN',
  tool_role: 'drill',
  emits_references: true,
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
      description: "Ayanamsha filter (default: 'LAHIRI').",
    },
    tradition: {
      type: 'string',
      description: 'Filter prescriptions by tradition: mantra|gemstone|charity|vrata|yantra|ayurvedic.',
      enum: ['mantra', 'gemstone', 'charity', 'vrata', 'yantra', 'ayurvedic'],
    },
    domain: {
      type: 'string',
      description: 'Filter by life domain (career, wealth, relationship, health, character, spirituality, other).',
    },
    feasibility_tier: {
      type: 'string',
      description: 'Filter prescriptions by feasibility tier: tier_1_accessible|tier_2_moderate|tier_3_dedicated.',
      enum: ['tier_1_accessible', 'tier_2_moderate', 'tier_3_dedicated'],
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

    const ayanamsha_id   = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'
    const tradition      = args['tradition'] as string | undefined
    const domain         = args['domain'] as string | undefined
    const feasibility    = args['feasibility_tier'] as string | undefined

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      // Resonances
      const resConds = ['chart_id = $1', 'ayanamsha_id = $2']
      const resParams: unknown[] = [chart_id, ayanamsha_id]
      let rp = 3
      if (domain) { resConds.push(`$${rp++} = ANY(domains_affected_array)`); resParams.push(domain) }

      const resonanceSql = `
        SELECT resonance_id, signal_id, graha_target, house_target,
               domain_target, valence, remedy_weight, domains_affected_array,
               updated_at
        FROM bodha_rm_resonances
        WHERE ${resConds.join(' AND ')}
        ORDER BY remedy_weight DESC NULLS LAST
      `

      // Prescriptions
      const preConds = ['chart_id = $1', 'ayanamsha_id = $2']
      const preParams: unknown[] = [chart_id, ayanamsha_id]
      let pp = 3
      if (tradition)  { preConds.push(`tradition = $${pp++}`);       preParams.push(tradition) }
      if (domain)     { preConds.push(`domain = $${pp++}`);           preParams.push(domain) }
      if (feasibility){ preConds.push(`feasibility_tier = $${pp++}`); preParams.push(feasibility) }

      const prescriptionSql = `
        SELECT prescription_id, resonance_id, tradition, remedy_name,
               remedy_description, domain, feasibility_tier, economics_jsonb,
               sequence_order, muhurta_required, contraindications,
               expected_effect_duration_months, updated_at
        FROM bodha_rm_remedy_prescriptions
        WHERE ${preConds.join(' AND ')}
        ORDER BY sequence_order NULLS LAST, feasibility_tier
      `

      const [resResult, preResult] = await Promise.all([
        db.query(resonanceSql, resParams),
        db.query(prescriptionSql, preParams),
      ])

      // Collect signal_id references
      const signalRefs = (resResult.rows as Array<{ signal_id?: string }>)
        .map(r => r.signal_id)
        .filter(Boolean) as string[]

      return {
        content: {
          chart_id,
          ayanamsha_id,
          resonances:           resResult.rows,
          resonance_count:      resResult.rows.length,
          prescriptions:        preResult.rows,
          prescription_count:   preResult.rows.length,
          signal_id_refs:       [...new Set(signalRefs)],
          filters: { tradition, domain, feasibility_tier: feasibility },
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

/**
 * query_medical_mappings — L0 Brahmagyan graha→medical reference
 * ==================================================================
 * W2b dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bg_medical_mappings`, 9 rows). Serves the classical graha→Ayurvedic
 * dosha/dhatu/organ-system/body-part/disease-tendency reference (BPHS
 * Ch.18, Ashtanga Hridayam, Charaka Samhita). Global classical reference —
 * no chart_id needed.
 *
 * MEDICAL DISCLAIMER (per the migration's own header): this is a Jyotish
 * reference table only, not a medical diagnostic system.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryMedicalMappingsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_medical_mappings',
  type:  'tool',
  layer: 'L0',
  name:  'query_medical_mappings',

  description: [
    'Query the graha→Ayurvedic medical reference (bg_medical_mappings, 9 rows — one per',
    'graha — BPHS Ch.18 / Ashtanga Hridayam / Charaka Samhita). Each row: dosha[], dhatu[],',
    'organ_systems[], body_part[], disease_tendency[], classical_citation. Filter by graha.',
    'Global classical reference — no chart_id needed. Jyotish reference only — NOT a medical',
    'diagnostic system; not_diagnosis applies to any downstream indication built from this.',
  ].join(' '),

  input_schema: {
    graha: { type: 'string', description: 'Filter by graha (case-insensitive, e.g. "Mars"). Omit for all 9.' },
  },

  required_inputs: [],
  scope: 'global',
  archetype: 'flat_fact',
  traversal_level: 'L-SOURCE',
  tool_role: 'leaf',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 20, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const graha = args['graha'] ? String(args['graha']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (graha) { filters.push(`LOWER(graha) = LOWER($${p++})`); params.push(graha) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT graha, dosha, dhatu, organ_systems, body_part, disease_tendency, classical_citation
      FROM bg_medical_mappings
      WHERE ${where}
      ORDER BY graha`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { graha },
          ...(result.rows.length === 0
            ? { empty_reason: `No medical-mapping rows matched (graha=${graha ?? 'any'}).` }
            : {}),
          disclaimer: 'Jyotish reference table only — NOT a medical diagnostic system, not medical advice.',
          provenance: { tables: ['bg_medical_mappings'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}

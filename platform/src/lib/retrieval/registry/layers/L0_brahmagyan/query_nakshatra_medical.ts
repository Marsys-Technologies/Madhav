/**
 * query_nakshatra_medical — L0 Brahmagyan nakshatra→medical reference
 * =======================================================================
 * W2b dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bg_nakshatra_medical`, 27 rows). Serves the classical 27-nakshatra→
 * body-part correspondence reference (Ashtanga Hridayam / BPHS). Global
 * classical reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryNakshatraMedicalCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_nakshatra_medical',
  type:  'tool',
  layer: 'L0',
  name:  'query_nakshatra_medical',

  description: [
    'Query the nakshatra→body-part medical reference (bg_nakshatra_medical, 27 rows —',
    'Ashtanga Hridayam / BPHS). Each row: nakshatra_name, nakshatra_number (1-27),',
    'body_part, classical_citation. Filter by nakshatra_name or nakshatra_number. Global',
    'classical reference — no chart_id needed. Jyotish reference only — not medical advice.',
  ].join(' '),

  input_schema: {
    nakshatra_name:   { type: 'string', description: 'Filter by nakshatra name (case-insensitive). Omit for all.' },
    nakshatra_number: { type: 'number', description: 'Filter by nakshatra number (1-27). Omit for all.' },
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
    const nakshatraName = args['nakshatra_name'] ? String(args['nakshatra_name']) : null
    const nakshatraNum  = args['nakshatra_number'] != null ? Number(args['nakshatra_number']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (nakshatraName) { filters.push(`LOWER(nakshatra_name) = LOWER($${p++})`); params.push(nakshatraName) }
    if (nakshatraNum != null && Number.isInteger(nakshatraNum)) { filters.push(`nakshatra_number = $${p++}`); params.push(nakshatraNum) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT nakshatra_name, nakshatra_number, body_part, classical_citation
      FROM bg_nakshatra_medical
      WHERE ${where}
      ORDER BY nakshatra_number`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { nakshatra_name: nakshatraName, nakshatra_number: nakshatraNum },
          ...(result.rows.length === 0
            ? { empty_reason: `No nakshatra-medical rows matched (nakshatra_name=${nakshatraName ?? 'any'}, nakshatra_number=${nakshatraNum ?? 'any'}).` }
            : {}),
          disclaimer: 'Jyotish reference table only — not medical advice.',
          provenance: { tables: ['bg_nakshatra_medical'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}

/**
 * query_sign_medical — L0 Brahmagyan sign→medical reference
 * ==========================================================
 * W4-loop-1 (E-6 group4). Serves bg_sign_medical — the L0 rāśi→body-part / dosha /
 * element reference (12 rows, Kālapuruṣa scheme) that had no deployed MCP tool. Global
 * reference data (not chart-scoped). Read-only.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const querySignMedicalCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_sign_medical',
  type:  'tool',
  layer: 'L0',
  name:  'query_sign_medical',

  description: [
    'Query the rāśi→medical reference (bg_sign_medical, 12 rows — the Kālapuruṣa scheme).',
    'Each sign maps to its body_part, organ_systems, element, dosha, and classical_citation.',
    'Filter by sign_number (1=Aries..12=Pisces) or sign_name. Global classical reference —',
    'no chart_id needed. Use to ground medical/health readings in classical sign associations.',
  ].join(' '),

  input_schema: {
    sign_number: { type: 'number', description: 'Filter by sign number (1=Aries..12=Pisces). Omit for all 12.' },
    sign_name:   { type: 'string', description: 'Filter by sign name (case-insensitive, e.g. "Aries"). Omit for all.' },
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
    bulk_context: { pre_fetch_priority: 40, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const signNumber = args['sign_number'] != null ? Number(args['sign_number']) : null
    const signName   = args['sign_name'] ? String(args['sign_name']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (signNumber != null && Number.isInteger(signNumber)) { filters.push(`sign_number = $${p++}`); params.push(signNumber) }
    if (signName) { filters.push(`LOWER(sign_name) = LOWER($${p++})`); params.push(signName) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT sign_number, sign_name, body_part, organ_systems, element, dosha, classical_citation
      FROM bg_sign_medical
      WHERE ${where}
      ORDER BY sign_number`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { sign_number: signNumber, sign_name: signName },
          ...(result.rows.length === 0
            ? { empty_reason: `No sign→medical rows matched (sign_number=${signNumber ?? 'any'}, sign_name=${signName ?? 'any'}).` }
            : {}),
          disclaimer: 'Classical rāśi→body-part associations (Kālapuruṣa) — reference only, not medical advice.',
          provenance: { tables: ['bg_sign_medical'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}

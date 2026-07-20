/**
 * query_shashtiamsha_deities — L0 Brahmagyan D60 (Shashtiamsha) amsa reference
 * ================================================================================
 * W2b dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bg_shashtiamsha_deities`, 60 rows). Serves the canonical D60 amsa
 * kroora/soumya quality reference (cross-derived from PyJHora's own
 * reference arrays; see 430_bg_shashtiamsha_deities.sql). deity_name is
 * intentionally NULL for all 60 rows pending a primary BPHS Ch.7
 * verse-level citation (canonical-or-floor discipline — not a fabricated
 * name list). Consumed internally by ga_vargas_writer.py's D60 deity
 * attribution; this tool exposes the same reference rows directly.
 *
 * Global classical reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryShashtiamshaDeitiesCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_shashtiamsha_deities',
  type:  'tool',
  layer: 'L0',
  name:  'query_shashtiamsha_deities',

  description: [
    'Query the canonical D60 (Shashtiamsha) amsa-quality reference (bg_shashtiamsha_deities,',
    '60 rows, one per amsa 1-60). Each row: amsa_number, quality (kroora=malefic |',
    'soumya=benefic), deity_name (NULL for all rows — floored pending a primary BPHS Ch.7',
    'citation, not a fabricated name), classical_citation, rule_notes. Filter by amsa_number',
    'or quality. Global classical reference — no chart_id needed; returns the REFERENCE',
    "amsa quality only, not any chart's actual D60 placement.",
  ].join(' '),

  input_schema: {
    amsa_number: { type: 'number', description: 'Filter by amsa_number (1-60). Omit for all.' },
    quality:     { type: 'string', description: 'Filter by quality (kroora|soumya). Omit for all.' },
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
    bulk_context: { pre_fetch_priority: 15, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const amsaNumber = args['amsa_number'] != null ? Number(args['amsa_number']) : null
    const quality    = args['quality'] ? String(args['quality']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (amsaNumber != null && Number.isInteger(amsaNumber)) { filters.push(`amsa_number = $${p++}`); params.push(amsaNumber) }
    if (quality) { filters.push(`LOWER(quality) = LOWER($${p++})`); params.push(quality) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT amsa_number, quality, deity_name, classical_citation, rule_notes
      FROM bg_shashtiamsha_deities
      WHERE ${where}
      ORDER BY amsa_number`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { amsa_number: amsaNumber, quality },
          ...(result.rows.length === 0
            ? { empty_reason: `No D60 amsa rows matched (amsa_number=${amsaNumber ?? 'any'}, quality=${quality ?? 'any'}).` }
            : {}),
          disclaimer: 'D60 amsa-quality reference only — deity_name floored NULL pending primary citation, not a computed per-chart D60 placement.',
          provenance: { tables: ['bg_shashtiamsha_deities'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}

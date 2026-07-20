/**
 * query_graha_naisargika_friendship — L0 Brahmagyan natural friendship reference
 * ================================================================================
 * W2 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bg_graha_naisargika_friendship`, 72 rows). Serves the classical natural
 * (naisargika) friendship matrix per graha pair — same migration file
 * (250_bg_dignity_reference.sql) as the already-served `bg_dignity_reference`
 * (via platform-mcp's `ref_dignity_reference_get`, not this "one catalog"
 * registry — kept independent here, not touched). BPHS Ch.27 / UK Ch.4 citations.
 *
 * Global classical reference — no chart_id needed. Modeled directly on
 * query_sign_medical.ts's established pattern for a small reference-table gap.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryGrahaNaisargikaFriendshipCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_graha_naisargika_friendship',
  type:  'tool',
  layer: 'L0',
  name:  'query_graha_naisargika_friendship',

  description: [
    'Query the classical natural (naisargika) friendship reference (bg_graha_naisargika_friendship,',
    '72 rows — one row per ordered graha pair, BPHS Ch.27 / UK Ch.4). relation is one of',
    "'friend' | 'neutral' | 'enemy' (the naisargika-only vocabulary — panchadha_maitri's",
    "'great_friend'/'great_enemy' upgrades are a separate, tatkalika-combined computation not stored",
    'here). Filter by graha and/or other_graha. Global classical reference — no chart_id needed.',
    'Use to ground compound-friendship (panchadha maitri) or dignity readings in the base natural',
    'relation before any temporal (tatkalika) adjustment is applied.',
  ].join(' '),

  input_schema: {
    graha:       { type: 'string', description: 'Filter by the subject graha (case-insensitive, e.g. "Saturn"). Omit for all.' },
    other_graha: { type: 'string', description: 'Filter by the counterpart graha (case-insensitive). Omit for all.' },
    relation:    { type: 'string', description: "Filter by relation: 'friend' | 'neutral' | 'enemy'. Omit for all.", enum: ['friend', 'neutral', 'enemy'] },
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
    bulk_context: { pre_fetch_priority: 35, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const graha      = args['graha'] ? String(args['graha']) : null
    const otherGraha = args['other_graha'] ? String(args['other_graha']) : null
    const relation    = args['relation'] ? String(args['relation']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (graha) { filters.push(`LOWER(graha) = LOWER($${p++})`); params.push(graha) }
    if (otherGraha) { filters.push(`LOWER(other_graha) = LOWER($${p++})`); params.push(otherGraha) }
    if (relation) { filters.push(`relation = $${p++}`); params.push(relation) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT graha, other_graha, relation, classical_citation
      FROM bg_graha_naisargika_friendship
      WHERE ${where}
      ORDER BY graha, other_graha`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { graha, other_graha: otherGraha, relation },
          ...(result.rows.length === 0
            ? { empty_reason: `No naisargika-friendship rows matched (graha=${graha ?? 'any'}, other_graha=${otherGraha ?? 'any'}, relation=${relation ?? 'any'}).` }
            : {}),
          disclaimer: 'Classical natural (naisargika) friendship only — no panchadha_maitri (temporal-combined) adjustment applied.',
          provenance: { tables: ['bg_graha_naisargika_friendship'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}

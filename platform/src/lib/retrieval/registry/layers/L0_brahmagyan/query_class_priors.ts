/**
 * query_class_priors — L0 Brahmagyan salience class-prior weights reference
 * =============================================================================
 * W2b dark-set wiring, Batch 2 (TABLE_CONCEPT_DISPOSITIONS_v2_0.md borderline
 * SERVE-gap set, `brahma_class_priors`, 164 rows). Serves the versioned
 * ranked salience class-prior weights (387_brahma_class_priors.sql) read
 * internally by composite_ranker.ts at query time as a ranking-computation
 * input. This capability exposes the SAME rows directly, honestly, as a
 * citable reference — per the disposition doc's own note, this is a
 * judgment-call table (a reasonable reader could argue OPERATIONAL instead
 * of SERVE-gap); wired here per the ruling's stated default-bias toward
 * serving tunable-but-citable classical/ratified weight tables.
 *
 * Global classical/ratified reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryClassPriorsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_class_priors',
  type:  'tool',
  layer: 'L0',
  name:  'query_class_priors',

  description: [
    'Query the versioned salience class-prior weight reference (brahma_class_priors,',
    '164 rows). Axes: prior_version, signal_type_class, fact_kind, source_subsystem,',
    'signal_tradition; each row: class_prior (weight), varga_weights (JSON overlay),',
    'contested flag, citation, ratified_by. Filter by prior_version, signal_type_class,',
    'or source_subsystem. Global reference — no chart_id needed. These are the SAME',
    'weights the internal composite ranking pipeline reads at query time — this tool',
    'exposes them directly for audit/citation, not a separately computed value.',
  ].join(' '),

  input_schema: {
    prior_version:     { type: 'string', description: 'Filter by prior_version. Omit for all.' },
    signal_type_class: { type: 'string', description: 'Filter by signal_type_class. Omit for all.' },
    source_subsystem:  { type: 'string', description: 'Filter by source_subsystem. Omit for all.' },
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
    bulk_context: { pre_fetch_priority: 10, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const priorVersion = args['prior_version'] ? String(args['prior_version']) : null
    const signalClass  = args['signal_type_class'] ? String(args['signal_type_class']) : null
    const subsystem    = args['source_subsystem'] ? String(args['source_subsystem']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (priorVersion) { filters.push(`prior_version = $${p++}`); params.push(priorVersion) }
    if (signalClass)  { filters.push(`signal_type_class = $${p++}`); params.push(signalClass) }
    if (subsystem)    { filters.push(`source_subsystem = $${p++}`); params.push(subsystem) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition,
             class_prior, varga_weights, contested, citation, ratified_by
      FROM brahma_class_priors
      WHERE ${where}
      ORDER BY prior_version, signal_type_class, source_subsystem
      LIMIT 200`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { prior_version: priorVersion, signal_type_class: signalClass, source_subsystem: subsystem },
          ...(result.rows.length === 0
            ? { empty_reason: `No class-prior rows matched (prior_version=${priorVersion ?? 'any'}, signal_type_class=${signalClass ?? 'any'}, source_subsystem=${subsystem ?? 'any'}).` }
            : {}),
          disclaimer: 'Versioned ranking-weight reference — same values the internal composite ranker reads, exposed here for audit/citation.',
          provenance: { tables: ['brahma_class_priors'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}

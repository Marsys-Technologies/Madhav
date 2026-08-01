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
 *
 * ── SCOPE NARROWING, 2026-08-01 (ṢAḌ-DARŚANA W2 lane `l0-ne-priors`) ──────────
 * `brahma_class_priors` is now home to TWO epistemically different objects that
 * happen to share a table and a `class_prior` column:
 *
 *   1. SALIENCE WEIGHTS (this capability) — `prior_version='1.0'`, 164 rows.
 *      `class_prior` is a dimensionless ranking MULTIPLIER, ~0.7-1.5.
 *   2. N_e LIFETIME COUNTS — `fact_kind='lifetime_count_per_100y'`, written by
 *      `bg_class_lifetime_counts` (migration 522, ADJUDICATION-2). `class_prior`
 *      is an EXPECTED EVENT COUNT over a 100-year horizon, sourced from published
 *      demographic statistics, and ranges from ~0.008 to ~3.1.
 *
 * Serving both through one unfiltered array would flatten two different kinds of
 * number into one undifferentiated list under a column name that means two
 * different things — the exact §N.6 Serving Density Principle violation — and
 * would silently falsify this tool's own "164 rows / salience weights" contract.
 * A caller could read `class_prior = 3.09` for `childbirth` as a salience weight
 * three times stronger than a yoga, which is nonsense.
 *
 * So this capability EXCLUDES the lifetime-count coordinate. That is honest
 * SCOPING, not a silent drop (B.10): the exclusion is stated in the description,
 * is reported as a named field on every response (`excluded_fact_kinds`), and the
 * rows remain fully served elsewhere — they are the structural baseline of the
 * Kāla Kṣetra hazard field and are surfaced with their own `source_ref` /
 * `prior_basis` provenance through that field's own surfaces, where the units are
 * unambiguous.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

/**
 * The reserved N_e coordinate (migration 522 / `bg_class_lifetime_counts`).
 * Exported so the test suite asserts the exclusion against the SAME constant the
 * handler uses, rather than against a second copy that could drift from it
 * (CLAUDE.md §N.7 item 3 — no wrapper-local constant may shadow its source).
 */
export const LIFETIME_COUNT_FACT_KIND = 'lifetime_count_per_100y'

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
    'SCOPE: salience weights ONLY. Rows at fact_kind=lifetime_count_per_100y are',
    'excluded — those are N_e expected-event-counts for the Kala Kshetra hazard',
    'field (asset bg_class_lifetime_counts), a different quantity in different',
    'units that shares this table; they are served through that field\'s surfaces.',
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

    // Salience weights only — see the SCOPE NARROWING note in the file header for
    // why the N_e lifetime-count rows are a different object and must not be
    // flattened into this array. Hard-coded rather than parameterised on purpose:
    // this is the capability's DEFINITION, not a user-tunable filter.
    const filters: string[] = [`fact_kind <> '${LIFETIME_COUNT_FACT_KIND}'`]
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
          // Named, machine-readable disclosure of the scope narrowing — so a caller
          // can see WHAT was left out and where it lives, rather than inferring a
          // clean full-table read from a count that silently excludes rows.
          excluded_fact_kinds: [LIFETIME_COUNT_FACT_KIND],
          excluded_note:
            `Rows at fact_kind='${LIFETIME_COUNT_FACT_KIND}' are excluded from this ` +
            'capability: they are N_e expected-event-counts over a 100-year horizon ' +
            '(asset bg_class_lifetime_counts), not salience ranking weights, and share ' +
            'the class_prior column while meaning something different. They are served ' +
            'with their own source_ref/prior_basis provenance through the Kāla Kṣetra ' +
            'temporal-field surfaces.',
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

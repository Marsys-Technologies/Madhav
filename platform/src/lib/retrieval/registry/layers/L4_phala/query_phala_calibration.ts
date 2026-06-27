/**
 * query_phala_calibration — L4 Phala Calibration Tools
 * ======================================================
 * Bundles the remaining L4 per-chart calibration/quality capabilities:
 *
 *   query_auspicious_windows  — ph_muhurta (phala_muhurta, 100 rows)
 *   query_spillover_cascades  — ph_sankrama (phala_sankrama, 73 rows)
 *   query_falsifiers          — ph_pramana (phala_pramana, 150 rows)
 *   query_anomaly_flags       — ph_sodhana (phala_sodhana, 200 rows)
 *   query_remedy_program      — ph_pratikara (phala_mitigation, count unknown)
 *   query_cleansed_anchors    — ph_suddha_sodhana (phala_suddha_sodhana, count unknown)
 *   query_rectification       — ph_rectification (phala_rectification, ~185 candidates)
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'

// ── query_auspicious_windows ──────────────────────────────────────────────────

export const queryAuspiciousWindowsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L4/query_auspicious_windows',
  type:  'tool',
  layer: 'L4',
  name:  'query_auspicious_windows',

  description: [
    'Returns personalized auspicious windows for a chart from phala_muhurta (ph_muhurta).',
    'Source: phala_muhurta (100 rows — chart-scored muhurta windows).',
    'Windows are scored by chart-strength + live-transit alignment.',
    'Filter by date range and event_class. emits_references: anchor_id back to phala_anchors.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: { type: 'string', description: 'Chart UUID (<chart_uuid>). Required.', required: true },
    ayanamsha_id: { type: 'string', description: "Ayanamsha (default: 'LAHIRI')." },
    date_from: { type: 'string', description: 'Start date (ISO 8601).' },
    date_to: { type: 'string', description: 'End date (ISO 8601).' },
    event_class: { type: 'string', description: 'Event class: marriage|travel|business|medical|education|ceremony.' },
  },

  llm_hints: { agentic: { cost_class: 'cheap', cacheable: true }, bulk_context: { pre_fetch_priority: 22 } },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'
    const date_from    = args['date_from'] as string | undefined
    const date_to      = args['date_to'] as string | undefined
    const event_class  = args['event_class'] as string | undefined

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }
      const conds: string[] = ['chart_id = $1', 'ayanamsha_id = $2']
      const params: unknown[] = [chart_id, ayanamsha_id]
      let p = 3

      if (date_from)   { conds.push(`window_end >= $${p++}`);    params.push(date_from) }
      if (date_to)     { conds.push(`window_start <= $${p++}`);  params.push(date_to) }
      if (event_class) { conds.push(`event_class = $${p++}`);    params.push(event_class) }

      const sql = `
        SELECT muhurta_id, event_class, window_start, window_end,
               composite_score, chart_strength_score, transit_score,
               anchor_id_refs, muhurta_factors_jsonb, ayanamsha_id
        FROM phala_muhurta
        WHERE ${conds.join(' AND ')}
        ORDER BY composite_score DESC NULLS LAST
        LIMIT 100
      `

      const result = await db.query(sql, params)
      const anchorRefs = new Set<string>()
      for (const row of result.rows as Array<{ anchor_id_refs?: string[] }>) {
        if (row.anchor_id_refs) for (const id of row.anchor_id_refs) anchorRefs.add(id)
      }

      return {
        content: { chart_id, ayanamsha_id, windows: result.rows, count: result.rows.length, anchor_id_refs: Array.from(anchorRefs), filters: { date_from, date_to, event_class } },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}

// ── query_spillover_cascades ──────────────────────────────────────────────────

export const querySpilloverCascadesCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L4/query_spillover_cascades',
  type:  'tool',
  layer: 'L4',
  name:  'query_spillover_cascades',

  description: [
    'Returns cross-domain spillover cascades for a chart from phala_sankrama (ph_sankrama).',
    'Source: phala_sankrama (73 rows — A→B→C domain cascade dynamics).',
    'Models how activation in one domain propagates to others.',
    'Returns conflict chains, trajectory vectors, and mitigation routing.',
    'emits_references: anchor_id back to phala_anchors.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'cross_domain',
  traversal_level: 'L-DOMAIN',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: { type: 'string', description: 'Chart UUID (<chart_uuid>). Required.', required: true },
    ayanamsha_id: { type: 'string', description: "Ayanamsha (default: 'LAHIRI')." },
    source_domain: { type: 'string', description: 'Filter by source domain of cascade.' },
    target_domain: { type: 'string', description: 'Filter by target domain of cascade.' },
  },

  llm_hints: { agentic: { cost_class: 'cheap', cacheable: true }, bulk_context: { pre_fetch_priority: 25 } },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id  = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'
    const source_domain = args['source_domain'] as string | undefined
    const target_domain = args['target_domain'] as string | undefined

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }
      const conds: string[] = ['chart_id = $1', 'ayanamsha_id = $2']
      const params: unknown[] = [chart_id, ayanamsha_id]
      let p = 3

      if (source_domain) { conds.push(`source_domain = $${p++}`); params.push(source_domain) }
      if (target_domain) { conds.push(`target_domain = $${p++}`); params.push(target_domain) }

      const sql = `
        SELECT cascade_id, source_domain, intermediate_domain, target_domain,
               cascade_type, cascade_weight, conflict_flag, trajectory_vector,
               mitigation_routing, anchor_id_refs, ayanamsha_id
        FROM phala_sankrama
        WHERE ${conds.join(' AND ')}
        ORDER BY cascade_weight DESC NULLS LAST
      `

      const result = await db.query(sql, params)
      const anchorRefs = new Set<string>()
      for (const row of result.rows as Array<{ anchor_id_refs?: string[] }>) {
        if (row.anchor_id_refs) for (const id of row.anchor_id_refs) anchorRefs.add(id)
      }

      return {
        content: { chart_id, ayanamsha_id, cascades: result.rows, count: result.rows.length, anchor_id_refs: Array.from(anchorRefs), filters: { source_domain, target_domain } },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}

// ── query_falsifiers ──────────────────────────────────────────────────────────

export const queryFalsifiersCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L4/query_falsifiers',
  type:  'tool',
  layer: 'L4',
  name:  'query_falsifiers',

  description: [
    'Returns machine-evaluable falsifiers for L4 predictions from phala_pramana (ph_pramana).',
    'Source: phala_pramana (150 rows — one falsifier per predictive anchor).',
    'Each row defines a testable condition + evaluation window + L5 onboarding status.',
    'emits_references: prediction_id refs linkable to mi_bhavisya (L5).',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'calibration',
  traversal_level: 'L-SIGNAL',
  tool_role: 'quality',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: { type: 'string', description: 'Chart UUID (<chart_uuid>). Required.', required: true },
    ayanamsha_id: { type: 'string', description: "Ayanamsha (default: 'LAHIRI')." },
  },

  llm_hints: { agentic: { cost_class: 'cheap', cacheable: true }, bulk_context: { pre_fetch_priority: 28 } },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      const sql = `
        SELECT pramana_id, anchor_id, prediction_id,
               falsifier_statement, evaluation_window_start,
               evaluation_window_end, evaluation_condition,
               l5_onboarding_status, last_evaluated_at, ayanamsha_id
        FROM phala_pramana
        WHERE chart_id = $1 AND ayanamsha_id = $2
        ORDER BY evaluation_window_start
      `

      const result = await db.query(sql, [chart_id, ayanamsha_id])
      const predictionIds = [...new Set(
        (result.rows as Array<{ prediction_id?: string }>).map(r => r.prediction_id).filter(Boolean) as string[]
      )]

      return {
        content: {
          chart_id, ayanamsha_id,
          falsifiers: result.rows, falsifier_count: result.rows.length,
          prediction_id_refs: predictionIds,
          provenance: { tables: ['phala_pramana'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}

// ── query_anomaly_flags ───────────────────────────────────────────────────────

export const queryAnomalyFlagsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L4/query_anomaly_flags',
  type:  'tool',
  layer: 'L4',
  name:  'query_anomaly_flags',

  description: [
    'Returns anomaly flags from the L4 anomaly registry (phala_sodhana, ph_sodhana).',
    'Source: phala_sodhana (200 rows — 5 detector types).',
    'Detector types: confidence_inflation, magnitude_drift, falsifier_absent,',
    'ledger_gap, layer_leakage.',
    'emits_references: anchor_id refs back to phala_anchors.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'calibration',
  traversal_level: 'L-SIGNAL',
  tool_role: 'quality',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: { type: 'string', description: 'Chart UUID (<chart_uuid>). Required.', required: true },
    ayanamsha_id: { type: 'string', description: "Ayanamsha (default: 'LAHIRI')." },
    detector_type: {
      type: 'string',
      description: 'Filter by detector type.',
      enum: ['confidence_inflation', 'magnitude_drift', 'falsifier_absent', 'ledger_gap', 'layer_leakage'],
    },
  },

  llm_hints: { agentic: { cost_class: 'cheap', cacheable: true }, bulk_context: { pre_fetch_priority: 30 } },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id  = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'
    const detector_type = args['detector_type'] as string | undefined

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }
      const conds: string[] = ['chart_id = $1', 'ayanamsha_id = $2']
      const params: unknown[] = [chart_id, ayanamsha_id]
      let p = 3

      if (detector_type) { conds.push(`detector_type = $${p++}`); params.push(detector_type) }

      const sql = `
        SELECT sodhana_id, detector_type, severity, anomaly_description,
               anchor_id_ref, detected_at, resolution_status, ayanamsha_id
        FROM phala_sodhana
        WHERE ${conds.join(' AND ')}
        ORDER BY severity DESC, detected_at DESC
      `

      const result = await db.query(sql, params)
      const anchorRefs = [...new Set(
        (result.rows as Array<{ anchor_id_ref?: string }>).map(r => r.anchor_id_ref).filter(Boolean) as string[]
      )]

      return {
        content: { chart_id, ayanamsha_id, anomalies: result.rows, count: result.rows.length, anchor_id_refs: anchorRefs, filters: { detector_type } },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}

// ── query_remedy_program ──────────────────────────────────────────────────────

export const queryRemedyProgramCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L4/query_remedy_program',
  type:  'tool',
  layer: 'L4',
  name:  'query_remedy_program',

  description: [
    'Returns the managed remedy program for a chart from phala_mitigation (ph_pratikara).',
    'Source: phala_mitigation (count unknown — treated as sparse).',
    'Rows are economics/feasibility tiered, sequenced, and muhurta-timed.',
    'emits_references: anchor_id back to phala_anchors; remedy_id back to bo_upaya/bg_remedies.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'rich_relational',
  traversal_level: 'L-DOMAIN',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: { type: 'string', description: 'Chart UUID (<chart_uuid>). Required.', required: true },
    ayanamsha_id: { type: 'string', description: "Ayanamsha (default: 'LAHIRI')." },
    feasibility_tier: {
      type: 'string',
      description: 'Filter by feasibility tier.',
      enum: ['tier_1_accessible', 'tier_2_moderate', 'tier_3_dedicated'],
    },
  },

  llm_hints: { agentic: { cost_class: 'cheap', cacheable: true }, bulk_context: { pre_fetch_priority: 35 } },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id   = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'
    const feasibility    = args['feasibility_tier'] as string | undefined

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }
      const conds: string[] = ['chart_id = $1', 'ayanamsha_id = $2']
      const params: unknown[] = [chart_id, ayanamsha_id]
      let p = 3

      if (feasibility) { conds.push(`feasibility_tier = $${p++}`); params.push(feasibility) }

      const sql = `
        SELECT mitigation_id, anchor_id_ref, remedy_id,
               feasibility_tier, economics_jsonb, sequence_order,
               muhurta_window_ref, tradition, remedy_name,
               expected_effect_months, contraindications, ayanamsha_id
        FROM phala_mitigation
        WHERE ${conds.join(' AND ')}
        ORDER BY sequence_order NULLS LAST, feasibility_tier
      `

      const result = await db.query(sql, params)
      return {
        content: {
          chart_id, ayanamsha_id, remedies: result.rows, count: result.rows.length,
          sparse_note: 'phala_mitigation count is unknown — sparse rows expected.',
          filters: { feasibility },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}

// ── query_cleansed_anchors ────────────────────────────────────────────────────

export const queryCleasedAnchorsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L4/query_cleansed_anchors',
  type:  'tool',
  layer: 'L4',
  name:  'query_cleansed_anchors',

  description: [
    'Returns cleansed anchor disposition rows from phala_suddha_sodhana (ph_suddha_sodhana).',
    'Source: phala_suddha_sodhana (count unknown — one row per phala_anchors entry).',
    'Filter by disposition: clean|flagged|staged_revision.',
    'revision_approved_by is always NULL — native sign-off required for approvals.',
    'emits_references: anchor_id back to phala_anchors.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'calibration',
  traversal_level: 'L-SIGNAL',
  tool_role: 'quality',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: { type: 'string', description: 'Chart UUID (<chart_uuid>). Required.', required: true },
    ayanamsha_id: { type: 'string', description: "Ayanamsha (default: 'LAHIRI')." },
    disposition: {
      type: 'string',
      description: 'Filter by disposition.',
      enum: ['clean', 'flagged', 'staged_revision'],
    },
  },

  llm_hints: { agentic: { cost_class: 'cheap', cacheable: true }, bulk_context: { pre_fetch_priority: 40 } },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'
    const disposition  = args['disposition'] as string | undefined

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }
      const conds: string[] = ['chart_id = $1', 'ayanamsha_id = $2']
      const params: unknown[] = [chart_id, ayanamsha_id]
      let p = 3

      if (disposition) { conds.push(`disposition = $${p++}`); params.push(disposition) }

      const sql = `
        SELECT suddha_id, anchor_id, disposition,
               cleansing_notes, revision_approved_by, cleansed_at, ayanamsha_id
        FROM phala_suddha_sodhana
        WHERE ${conds.join(' AND ')}
        ORDER BY disposition, cleansed_at DESC
      `

      const result = await db.query(sql, params)
      const anchorRefs = [...new Set(
        (result.rows as Array<{ anchor_id?: string }>).map(r => r.anchor_id).filter(Boolean) as string[]
      )]

      return {
        content: {
          chart_id, ayanamsha_id,
          cleansed_rows: result.rows, count: result.rows.length,
          anchor_id_refs: anchorRefs,
          note: 'revision_approved_by is always NULL — native sign-off required.',
          filters: { disposition },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}

// ── query_rectification ───────────────────────────────────────────────────────

export const queryRectificationCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L4/query_rectification',
  type:  'tool',
  layer: 'L4',
  name:  'query_rectification',

  description: [
    'Returns birth-time rectification candidates from phala_rectification (ph_rectification).',
    'Expected: ~185 candidates (±90 min range, 5-min steps × 5 ayanamshas).',
    'Returns STAGED candidates only. The canonical chart is NEVER auto-mutated.',
    'Per the D43 NO-AUTO-OVERRIDE rule: only the native can approve a rectification.',
    'emits_references: false (rectification is a meta-analysis, not a signal reference).',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'calibration',
  traversal_level: 'L-SIGNAL',
  tool_role: 'quality',
  emits_references: false,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: { type: 'string', description: 'Chart UUID (<chart_uuid>). Required.', required: true },
    ayanamsha_id: { type: 'string', description: "Ayanamsha (default: 'LAHIRI')." },
    top_k: { type: 'number', description: 'Max candidates to return (default: 20, max: 185).' },
  },

  llm_hints: { agentic: { cost_class: 'medium', cacheable: true }, bulk_context: { pre_fetch_priority: 45 } },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'
    const top_k        = Math.min(Number(args['top_k'] ?? 20), 185)

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      const sql = `
        SELECT rect_id, candidate_birth_time_utc, time_offset_minutes,
               rectification_score, lagna_candidate, lagna_score,
               event_alignment_count, disposition, approved_by, ayanamsha_id
        FROM phala_rectification
        WHERE chart_id = $1 AND ayanamsha_id = $2 AND disposition = 'staged'
        ORDER BY rectification_score DESC NULLS LAST
        LIMIT $3
      `

      const result = await db.query(sql, [chart_id, ayanamsha_id, top_k])

      return {
        content: {
          chart_id, ayanamsha_id,
          candidates: result.rows, count: result.rows.length,
          override_note: 'D43 NO-AUTO-OVERRIDE: the canonical chart birth time is never auto-mutated. approved_by = NULL on all candidates until native sign-off.',
          filters: { top_k },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}

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
import { query } from '@/lib/db/client'
import { DEFAULT_AYANAMSHA } from '../../constants'

/**
 * Per-chart LEL calibration judgment persisted on phala_rectification_best.judgment_flags
 * (migration 424) and produced by services.mimamsa.lel_calibration.judgment_flags().
 * `calibration` is a back-compat alias carrying the same value as `calibration_state`.
 */
export interface JudgmentFlags {
  calibration: 'structural' | 'sparse' | 'calibrated'
  calibration_state: 'structural' | 'sparse' | 'calibrated'
  rectification_basis: 'lel_fit' | 'structural_no_lel'
  lel_event_count: number
  load_bearing: boolean
}

// ── query_auspicious_windows ──────────────────────────────────────────────────

export const queryAuspiciousWindowsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L4/query_auspicious_windows',
  type:  'tool',
  layer: 'L4',
  name:  'query_auspicious_windows',

  description: [
    'Returns personalized auspicious windows for a chart from phala_muhurta (ph_muhurta).',
    'Source: phala_muhurta (100 rows — chart-scored muhurta windows).',
    'Windows are scored by panchanga quality + chart personalization.',
    'Filter by date range and action_class. emits_references: linked_anchor_id back to phala_anchors.',
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
    date_from: { type: 'string', description: 'Start date (ISO 8601).' },
    date_to: { type: 'string', description: 'End date (ISO 8601).' },
    action_class: { type: 'string', description: 'Action class: marriage|travel|business|medical|education|ceremony.' },
  },

  llm_hints: { agentic: { cost_class: 'cheap', cacheable: true }, bulk_context: { pre_fetch_priority: 22 } },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const date_from    = args['date_from'] as string | undefined
    const date_to      = args['date_to'] as string | undefined
    const action_class = args['action_class'] as string | undefined

    try {
      const conds: string[] = ['chart_id = $1']
      const params: unknown[] = [chart_id]
      let p = 2

      if (date_from)    { conds.push(`window_end >= $${p++}`);    params.push(date_from) }
      if (date_to)      { conds.push(`window_start <= $${p++}`);  params.push(date_to) }
      if (action_class) { conds.push(`action_class = $${p++}`);   params.push(action_class) }

      const sql = `
        SELECT muhurta_id, action_class, window_start, window_end,
               hora_lord, panchanga_score, chart_personalization_score,
               personal_adversity_penalty, composite_quality,
               window_quality_verdict, verdict_reason,
               linked_anchor_id, classical_citation
        FROM phala_muhurta
        WHERE ${conds.join(' AND ')}
        ORDER BY composite_quality DESC NULLS LAST
        LIMIT 100
      `

      const result = await query(sql, params)
      const anchorRefs = [...new Set(
        (result.rows as Array<{ linked_anchor_id?: string }>)
          .map(r => r.linked_anchor_id)
          .filter(Boolean) as string[]
      )]

      return {
        content: { chart_id, windows: result.rows, count: result.rows.length, anchor_id_refs: anchorRefs, filters: { date_from, date_to, action_class } },
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
    source_domain: { type: 'string', description: 'Filter by source domain of cascade.' },
    target_domain: { type: 'string', description: 'Filter by target domain of cascade.' },
  },

  llm_hints: { agentic: { cost_class: 'cheap', cacheable: true }, bulk_context: { pre_fetch_priority: 25 } },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const source_domain = args['source_domain'] as string | undefined
    const target_domain = args['target_domain'] as string | undefined

    try {
      const conds: string[] = ['chart_id = $1']
      const params: unknown[] = [chart_id]
      let p = 2

      if (source_domain) { conds.push(`source_domain = $${p++}`); params.push(source_domain) }
      if (target_domain) { conds.push(`target_domain = $${p++}`); params.push(target_domain) }

      const sql = `
        SELECT sankrama_id, source_anchor_id, cdlm_cell_id,
               source_domain, target_domain, relationship_type,
               linkage_strength, asymmetry_score, mechanism_text,
               source_window_start, source_window_end,
               projected_window_start, projected_window_end, projected_peak_date,
               cascade_depth, trajectory, mitigation_ref,
               spillover_confidence, confidence_basis, falsifier
        FROM phala_sankrama
        WHERE ${conds.join(' AND ')}
        ORDER BY linkage_strength DESC NULLS LAST
      `

      const result = await query(sql, params)
      const anchorRefs = [...new Set(
        (result.rows as Array<{ source_anchor_id?: string }>)
          .map(r => r.source_anchor_id)
          .filter(Boolean) as string[]
      )]

      return {
        content: { chart_id, cascades: result.rows, count: result.rows.length, anchor_id_refs: anchorRefs, filters: { source_domain, target_domain } },
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
    'Each row defines a testable falsifier + observable criteria + window status.',
    'emits_references: anchor_id refs back to phala_anchors; lel_entry_id / linked_sodhana_id where present.',
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
  },

  llm_hints: { agentic: { cost_class: 'cheap', cacheable: true }, bulk_context: { pre_fetch_priority: 28 } },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    try {
      const sql = `
        SELECT pramana_id, anchor_id, evidence_type, evidence_strength_label,
               falsifier_text, observable_criteria_jsonb, window_status,
               lel_entry_id, linked_sodhana_id, source_citation
        FROM phala_pramana
        WHERE chart_id = $1
        ORDER BY window_status
      `

      const result = await query(sql, [chart_id])
      const anchorRefs = [...new Set(
        (result.rows as Array<{ anchor_id?: string }>).map(r => r.anchor_id).filter(Boolean) as string[]
      )]

      return {
        content: {
          chart_id,
          falsifiers: result.rows, falsifier_count: result.rows.length,
          anchor_id_refs: anchorRefs,
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
    'Source: phala_sodhana (200 rows — anomaly detector output).',
    'Each row carries an anomaly_type, anomaly_severity, the detected_field,',
    'expected vs observed values, leakage_class, and a recommendation.',
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
    anomaly_type: {
      type: 'string',
      description: 'Filter by anomaly_type (free-text detector label as stored on phala_sodhana).',
    },
  },

  llm_hints: { agentic: { cost_class: 'cheap', cacheable: true }, bulk_context: { pre_fetch_priority: 30 } },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const anomaly_type = args['anomaly_type'] as string | undefined

    try {
      const conds: string[] = ['chart_id = $1']
      const params: unknown[] = [chart_id]
      let p = 2

      if (anomaly_type) { conds.push(`anomaly_type = $${p++}`); params.push(anomaly_type) }

      const sql = `
        SELECT sodhana_id, anchor_id, anomaly_type, anomaly_severity,
               detected_field, expected_value_text, observed_value_text,
               leakage_class, recommendation_text, auto_action
        FROM phala_sodhana
        WHERE ${conds.join(' AND ')}
        ORDER BY anomaly_severity DESC
      `

      const result = await query(sql, params)
      const anchorRefs = [...new Set(
        (result.rows as Array<{ anchor_id?: string }>).map(r => r.anchor_id).filter(Boolean) as string[]
      )]

      return {
        content: { chart_id, anomalies: result.rows, count: result.rows.length, anchor_id_refs: anchorRefs, filters: { anomaly_type } },
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
    'Rows are intensity-tiered, proportionality-justified, and muhurta-timed.',
    'emits_references: linked_anchor_id back to phala_anchors; obstruction_id ties the obstruction.',
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
    intensity_tier: {
      type: 'string',
      description: 'Filter by intensity_tier (free-text tier label as stored on phala_mitigation).',
    },
  },

  llm_hints: { agentic: { cost_class: 'cheap', cacheable: true }, bulk_context: { pre_fetch_priority: 35 } },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const intensity_tier = args['intensity_tier'] as string | undefined

    try {
      const conds: string[] = ['chart_id = $1']
      const params: unknown[] = [chart_id]
      let p = 2

      if (intensity_tier) { conds.push(`intensity_tier = $${p++}`); params.push(intensity_tier) }

      const sql = `
        SELECT mitigation_id, linked_anchor_id, obstruction_id,
               afflicting_graha, obstruction_severity, intensity_tier,
               program_jsonb, tradition_options_jsonb, cross_tradition_corroboration,
               recommended_tier_jsonb, proportionality_basis,
               initiation_muhurta_ref, window_start, window_end,
               re_evaluation_date, classical_citation
        FROM phala_mitigation
        WHERE ${conds.join(' AND ')}
        ORDER BY obstruction_severity DESC NULLS LAST, intensity_tier
      `

      const result = await query(sql, params)
      const anchorRefs = [...new Set(
        (result.rows as Array<{ linked_anchor_id?: string }>)
          .map(r => r.linked_anchor_id)
          .filter(Boolean) as string[]
      )]
      return {
        content: {
          chart_id, remedies: result.rows, count: result.rows.length,
          anchor_id_refs: anchorRefs,
          sparse_note: 'phala_mitigation count is unknown — sparse rows expected.',
          filters: { intensity_tier },
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
    'Filter by cleanliness_status (free-text status as stored).',
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
    cleanliness_status: {
      type: 'string',
      description: 'Filter by cleanliness_status (free-text status as stored on phala_suddha_sodhana).',
    },
  },

  llm_hints: { agentic: { cost_class: 'cheap', cacheable: true }, bulk_context: { pre_fetch_priority: 40 } },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const cleanliness_status = args['cleanliness_status'] as string | undefined

    try {
      const conds: string[] = ['chart_id = $1']
      const params: unknown[] = [chart_id]
      let p = 2

      if (cleanliness_status) { conds.push(`cleanliness_status = $${p++}`); params.push(cleanliness_status) }

      const sql = `
        SELECT entry_id, anchor_id, cleanliness_status,
               critical_flag_count, major_flag_count, minor_flag_count,
               flag_ids_jsonb, staged_revision_jsonb,
               revision_approved_by, revision_applied_at,
               confidence_delta_if_applied, magnitude_delta_if_applied
        FROM phala_suddha_sodhana
        WHERE ${conds.join(' AND ')}
        ORDER BY cleanliness_status, critical_flag_count DESC
      `

      const result = await query(sql, params)
      const anchorRefs = [...new Set(
        (result.rows as Array<{ anchor_id?: string }>).map(r => r.anchor_id).filter(Boolean) as string[]
      )]

      return {
        content: {
          chart_id,
          cleansed_rows: result.rows, count: result.rows.length,
          anchor_id_refs: anchorRefs,
          note: 'revision_approved_by is always NULL — native sign-off required.',
          filters: { cleanliness_status },
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
    'Candidates are scored by LEL fit; the canonical chart is NEVER auto-mutated.',
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
    ayanamsha_id: { type: 'string', description: "Ayanamsha (default: 'lahiri_chitrapaksha')." },
    top_k: { type: 'number', description: 'Max candidates to return (default: 20, max: 185).' },
  },

  llm_hints: { agentic: { cost_class: 'medium', cacheable: true }, bulk_context: { pre_fetch_priority: 45 } },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? DEFAULT_AYANAMSHA
    const top_k        = Math.min(Number(args['top_k'] ?? 20), 185)

    try {
      const sql = `
        SELECT id, candidate_birth_utc, offset_minutes, ayanamsha_id,
               lagna_sign, lagna_longitude_deg, lagna_degree_in_sign,
               lel_fit_score, lel_events_matched, lel_events_tested,
               lagna_stable, scored_at
        FROM phala_rectification
        WHERE chart_id = $1 AND ayanamsha_id = $2
        ORDER BY lel_fit_score DESC NULLS LAST
        LIMIT $3
      `

      const result = await query(sql, [chart_id, ayanamsha_id, top_k])

      // Surface the per-chart calibration judgment (BA-LEL R2.2 Step 4/5). The best
      // row is chart-scoped (UNIQUE chart_id); judgment_flags carries the
      // calibration_state (structural | sparse | calibrated), rectification_basis,
      // lel_event_count and load_bearing. A chart that has not been rectified yet
      // (no best row) surfaces judgment_flags: null.
      const bestSql = `
        SELECT judgment_flags, confidence_label, offset_minutes AS best_offset_minutes
        FROM phala_rectification_best
        WHERE chart_id = $1
        LIMIT 1
      `
      const bestResult = await query(bestSql, [chart_id])
      const best = (bestResult.rows[0] ?? null) as
        | { judgment_flags: JudgmentFlags | null; confidence_label: string | null; best_offset_minutes: number | null }
        | null
      const judgment_flags: JudgmentFlags | null = best?.judgment_flags ?? null

      return {
        content: {
          chart_id, ayanamsha_id,
          candidates: result.rows, count: result.rows.length,
          judgment_flags,
          calibration_state: judgment_flags?.calibration_state ?? null,
          override_note: 'D43 NO-AUTO-OVERRIDE: the canonical chart birth time is never auto-mutated. phala_rectification has no staging/approval column — candidates are advisory LEL-fit scores only; native sign-off is required out-of-band before any rectification is adopted.',
          filters: { top_k },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}

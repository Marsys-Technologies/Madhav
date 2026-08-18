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

const MITIGATION_MAX_LIMIT = 50

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
    domain: {
      type: 'string',
      description: 'Filter remedies by the domain of their linked phala_anchors row.',
    },
    limit:  { type: 'number', description: `Max rows (default ${MITIGATION_MAX_LIMIT}, max ${MITIGATION_MAX_LIMIT}).` },
    offset: { type: 'number', description: 'Pagination offset (default 0).' },
  },

  llm_hints: { agentic: { cost_class: 'cheap', cacheable: true }, bulk_context: { pre_fetch_priority: 35 } },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const intensity_tier = args['intensity_tier'] as string | undefined
    const domain = args['domain'] as string | undefined
    // WP-1.3j budget discipline (F-L10-024): phala_mitigation is NOT sparse — it holds
    // 600+ rows/chart. The prior handler returned the FULL unbounded set; now bounded.
    const limit  = Math.min(Math.max(Number(args['limit'] ?? MITIGATION_MAX_LIMIT), 1), MITIGATION_MAX_LIMIT)
    const offset = Math.max(Number(args['offset'] ?? 0), 0)

    try {
      const conds: string[] = ['chart_id = $1']
      const params: unknown[] = [chart_id]
      let p = 2

      if (intensity_tier) { conds.push(`intensity_tier = $${p++}`); params.push(intensity_tier) }
      if (domain) {
        conds.push(`EXISTS (
          SELECT 1
          FROM phala_anchors a
          WHERE a.chart_id = phala_mitigation.chart_id
            AND a.anchor_id = phala_mitigation.linked_anchor_id
            AND a.domain = $${p++}
        )`)
        params.push(domain)
      }
      const where = conds.join(' AND ')

      const sql = `
        SELECT mitigation_id, linked_anchor_id, obstruction_id,
               afflicting_graha, obstruction_severity, intensity_tier,
               program_jsonb, tradition_options_jsonb, cross_tradition_corroboration,
               recommended_tier_jsonb, proportionality_basis,
               initiation_muhurta_ref,
               to_char(window_start, 'YYYY-MM-DD') AS window_start,
               to_char(window_end, 'YYYY-MM-DD') AS window_end,
               to_char(re_evaluation_date, 'YYYY-MM-DD') AS re_evaluation_date,
               classical_citation
        FROM phala_mitigation
        WHERE ${where}
        ORDER BY obstruction_severity DESC NULLS LAST, intensity_tier
        LIMIT $${p} OFFSET $${p + 1}
      `

      const [result, countRes] = await Promise.all([
        query(sql, [...params, limit, offset]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM phala_mitigation WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      const anchorRefs = [...new Set(
        (result.rows as Array<{ linked_anchor_id?: string }>)
          .map(r => r.linked_anchor_id)
          .filter(Boolean) as string[]
      )]
      return {
        content: {
          chart_id, remedies: result.rows, count: result.rows.length,
          total_matching,
          more_available: offset + result.rows.length < total_matching,
          anchor_id_refs: anchorRefs,
          filters: { intensity_tier, domain, limit, offset },
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
    'Expected: ~185 candidates/chart (±90 min range, 5-min steps × 5 ayanamshas).',
    'Candidates are scored by LEL fit; the canonical chart is NEVER auto-mutated.',
    'Per the D43 NO-AUTO-OVERRIDE rule: only the native can approve a rectification.',
    "ayanamsha_id is an OPTIONAL filter — the table stores short codes",
    "(lahiri | kp | raman | surya_siddhanta | true_chitra); OMIT it to return candidates",
    'across ALL ayanamshas. Bounded (LIMIT ≤50) with a disclosed total + offset pagination.',
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
    ayanamsha_id: { type: 'string', description: "OPTIONAL ayanamsha filter — short code (lahiri | kp | raman | surya_siddhanta | true_chitra). Omit for ALL ayanamshas." },
    top_k: { type: 'number', description: 'Max candidates to return (default: 50, max: 50).' },
    offset: { type: 'number', description: 'Pagination offset (default: 0).' },
  },

  llm_hints: { agentic: { cost_class: 'medium', cacheable: true }, bulk_context: { pre_fetch_priority: 45 } },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    // WP-1.3j serving-bug fix (F-L10-025): phala_rectification stores SHORT ayanamsha codes
    // (lahiri, kp, raman, surya_siddhanta, true_chitra) — NOT the L1 long form
    // 'lahiri_chitrapaksha'. The prior handler forced ayanamsha_id = DEFAULT_AYANAMSHA
    // ('lahiri_chitrapaksha'), which matched ZERO rows despite 185 real candidates/chart.
    // Fix: ayanamsha_id is now an optional filter (omit → all ayanamshas). Accept the long
    // form as a convenience alias for its short code so an L1-shaped caller still resolves.
    const AY_LONG_TO_SHORT: Record<string, string> = {
      lahiri_chitrapaksha: 'lahiri', lahiri: 'lahiri',
      krishnamurti: 'kp', kp: 'kp',
      raman: 'raman',
      surya_siddhanta_classical: 'surya_siddhanta', surya_siddhanta: 'surya_siddhanta',
      true_chitra: 'true_chitra',
    }
    const rawAyanamsha = args['ayanamsha_id'] as string | undefined
    const ayanamsha_id = rawAyanamsha ? (AY_LONG_TO_SHORT[rawAyanamsha] ?? rawAyanamsha) : null
    const top_k        = Math.min(Math.max(Number(args['top_k'] ?? 50), 1), 50)
    const offset       = Math.max(Number(args['offset'] ?? 0), 0)

    try {
      const conds: string[] = ['chart_id = $1']
      const qp: unknown[] = [chart_id]
      let cp = 2
      if (ayanamsha_id) { conds.push(`ayanamsha_id = $${cp++}`); qp.push(ayanamsha_id) }
      const rectWhere = conds.join(' AND ')

      const sql = `
        SELECT id, to_char(candidate_birth_utc, 'YYYY-MM-DD') AS candidate_birth_date,
               candidate_birth_utc, offset_minutes, ayanamsha_id,
               lagna_sign, lagna_longitude_deg, lagna_degree_in_sign,
               lel_fit_score, lel_events_matched, lel_events_tested,
               lagna_stable, to_char(scored_at, 'YYYY-MM-DD') AS scored_date
        FROM phala_rectification
        WHERE ${rectWhere}
        ORDER BY lel_fit_score DESC NULLS LAST
        LIMIT $${cp} OFFSET $${cp + 1}
      `

      const [result, countRes] = await Promise.all([
        query(sql, [...qp, top_k, offset]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM phala_rectification WHERE ${rectWhere}`, qp),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)

      // Surface the per-chart calibration judgment (BA-LEL R2.2 Step 4/5). The best
      // row is chart-scoped (UNIQUE chart_id); judgment_flags carries the
      // calibration_state (structural | sparse | calibrated), rectification_basis,
      // lel_event_count and load_bearing. A chart that has not been rectified yet
      // (no best row) surfaces judgment_flags: null.
      //
      // R5.1 C2 item 5 (lel_training_matched=0 corroboration honesty): this SELECT used to
      // omit lel_training_events/lel_training_matched/win_margin/leakage_firewall_note —
      // columns migration 336 already persists — so a caller only ever saw
      // judgment_flags.lel_event_count (the FULL LEL corroboration count, e.g. 57 for the
      // native) with zero visibility into the DIFFERENT, smaller number that actually did the
      // birth-time SCORING: lel_training_matched is a classical-rule dasha-lord-in-house match
      // count (services/ph_rectification/engine.py::_score_dasha_match) against a FIREWALLED
      // subset of training events (pre-2020, exact/month-exact dates only — post-2020 +
      // LEL v1.7 enrichment events are deliberately held out for out-of-sample validation, see
      // leakage_firewall_note). A low or even 0 lel_training_matched is NOT "corroboration
      // failed" and must never silently stand in for lel_event_count — the two numbers answer
      // different questions and are now always surfaced together with an explicit explanation.
      const bestSql = `
        SELECT judgment_flags, confidence_label, offset_minutes AS best_offset_minutes,
               best_lel_fit_score, confidence_low, confidence_high, win_margin,
               lel_training_events, lel_training_matched, leakage_firewall_note,
               competing_candidates
        FROM phala_rectification_best
        WHERE chart_id = $1
        LIMIT 1
      `
      const bestResult = await query(bestSql, [chart_id])
      const best = (bestResult.rows[0] ?? null) as
        | {
            judgment_flags: JudgmentFlags | null
            confidence_label: string | null
            best_offset_minutes: number | null
            best_lel_fit_score: number | null
            confidence_low: number | null
            confidence_high: number | null
            win_margin: number | null
            lel_training_events: number | null
            lel_training_matched: number | null
            leakage_firewall_note: string | null
            competing_candidates: unknown
          }
        | null
      const judgment_flags: JudgmentFlags | null = best?.judgment_flags ?? null

      const lel_match_explanation = best == null
        ? {
            corroboration_available: false,
            note: 'No phala_rectification_best row exists for this chart — no rectification has been run, so no training-match accounting applies. This is the correct resting state for a chart with lel_event_count=0 (structural calibration), not an error.',
          }
        : {
            corroboration_available: true,
            // The FULL corroboration count driving calibration_state (e.g. 57 for the native).
            lel_event_count: judgment_flags?.lel_event_count ?? null,
            calibration_state: judgment_flags?.calibration_state ?? null,
            // The SEPARATE, smaller training-subset match count that actually picked the
            // winning birth-time offset — genuinely can be low or 0 without meaning
            // lel_event_count's corroboration failed.
            lel_training_events: best.lel_training_events,
            lel_training_matched: best.lel_training_matched,
            match_criterion: 'Count of classical-rule matches (services/ph_rectification/engine.py::_score_dasha_match): +1 per training event whose maha-dasha lord sits in a domain-significator house counted from the candidate lagna, +1 more if the antar-dasha lord ALSO does (MD+AD double match). Summed across all lel_training_events, then normalized to best_lel_fit_score = lel_training_matched / (2 × lel_training_events).',
            leakage_firewall_note: best.leakage_firewall_note,
            explanation: judgment_flags?.lel_event_count && best.lel_training_events && judgment_flags.lel_event_count > best.lel_training_events
              ? `This chart has ${judgment_flags.lel_event_count} total recorded LEL events (drives calibration_state=${judgment_flags.calibration_state}), but only ${best.lel_training_events} of them are in the FIREWALLED pre-2020 training subset used to score birth-time candidates (the rest are held out post-2020/enrichment events reserved for out-of-sample outcome validation, per leakage_firewall_note). Of those ${best.lel_training_events} training events, ${best.lel_training_matched ?? 0} classical-rule matches were found for the winning offset — this is the number that actually selected offset_minutes=${best.best_offset_minutes}, NOT lel_event_count.`
              : 'lel_training_matched/lel_training_events are the training-subset accounting that selected the winning offset; lel_event_count is the full corroboration count driving calibration_state. See match_criterion for how lel_training_matched is computed.',
          }

      // CR-47 fix (D-1.6 S-1): lel_fit_score is flat 0 across ALL 185 candidates for this
      // chart (confirmed live 2026-07-16 — every one of the top-50 rows returned
      // lel_fit_score:0, ORDER BY lel_fit_score DESC NULLS LAST is therefore a no-op
      // tie-break, not a real ranking), yet the surface presented `candidates` sorted by
      // that score with no signal that the ranking is degenerate — a caller reading
      // "row 1 of 185, sorted by lel_fit_score DESC" would reasonably (and wrongly) infer
      // row 1 is the best-supported candidate. Compute variance across the SERVED page's
      // lel_fit_score values (the same column the ORDER BY sorts on) and flag
      // `non_discriminating: true` with an explanatory note whenever there is zero (or
      // near-zero) spread — B.10: this does not attempt the full ranking-method fix
      // (K-6/later scope, see ph_rectification/engine.py's own "deliberately uniform"
      // docstring), it only stops presenting a degenerate ranking as a meaningful one.
      // `win_margin` (best vs. second-best offset's mean score) is a second, independent
      // corroborating signal already computed by the engine — ~0 confirms the same
      // degeneracy at the offset-aggregate level, not just the raw candidate page.
      const scores = (result.rows as Array<{ lel_fit_score: number | string | null }>)
        .map(r => (r.lel_fit_score == null ? null : Number(r.lel_fit_score)))
        .filter((v): v is number => v != null && !Number.isNaN(v))
      const scoreVariance = scores.length > 1
        ? (() => {
            const mean = scores.reduce((a, b) => a + b, 0) / scores.length
            return scores.reduce((a, b) => a + (b - mean) ** 2, 0) / scores.length
          })()
        : null
      const ZERO_VARIANCE_EPSILON = 1e-9
      const pageNonDiscriminating = scoreVariance != null && scoreVariance < ZERO_VARIANCE_EPSILON
      const winMarginNonDiscriminating = best?.win_margin != null && Math.abs(best.win_margin) < ZERO_VARIANCE_EPSILON
      const non_discriminating = pageNonDiscriminating || winMarginNonDiscriminating

      return {
        content: {
          chart_id, ayanamsha_id,
          candidates: result.rows, count: result.rows.length,
          total_matching,
          more_available: offset + result.rows.length < total_matching,
          judgment_flags,
          calibration_state: judgment_flags?.calibration_state ?? null,
          lel_match_explanation,
          best_lel_fit_score: best?.best_lel_fit_score ?? null,
          confidence_low: best?.confidence_low ?? null,
          confidence_high: best?.confidence_high ?? null,
          win_margin: best?.win_margin ?? null,
          competing_candidates: best?.competing_candidates ?? null,
          non_discriminating,
          ...(non_discriminating
            ? {
                non_discriminating_note:
                  `lel_fit_score has ${pageNonDiscriminating ? 'zero variance across the served candidate page' : 'a near-zero win_margin between the top offsets'} ` +
                  `(${scores.length} scored candidates on this page, variance=${scoreVariance ?? 'n/a'}, win_margin=${best?.win_margin ?? 'n/a'}) — ` +
                  'the ORDER BY lel_fit_score DESC ranking is NOT discriminating between candidates; row order does not indicate which offset is more classically supported. ' +
                  'The underlying scoring-method fix (a richer classical-rule set that actually differentiates offsets) is tracked separately (K-6/later); this flag exists so a caller never reads "first row" as "best candidate."',
              }
            : {}),
          override_note: 'D43 NO-AUTO-OVERRIDE: the canonical chart birth time is never auto-mutated. phala_rectification has no staging/approval column — candidates are advisory LEL-fit scores only; native sign-off is required out-of-band before any rectification is adopted.',
          filters: { ayanamsha_id, top_k, offset },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}

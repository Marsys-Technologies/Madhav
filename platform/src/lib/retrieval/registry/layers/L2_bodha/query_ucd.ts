/**
 * query_ucd — Chart Digest Query (L2 Bodha)
 * ==========================================
 * Reads vw_chart_digest + bodha_msr_signals top signals for a chart.
 * Returns a compact, LLM-ready Bodha synthesis digest:
 *   - Top MSR signals by salience (top K)
 *   - Domain convergence leaders (top 5 domains)
 *   - Contradiction count
 *   - Weakest graha + priority class
 *   - Trap1 audit count
 *
 * Used by the consumption layer (Bodha chat) as the primary chart-level
 * context loader for the L2 synthesis surface.
 */

import type { CapabilityDescriptor } from '../../index'

export const queryUcdCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_ucd',
  type:  'tool',
  layer: 'L2',
  name:  'query_ucd',

  description: [
    'Returns a structured Bodha synthesis digest for a chart.',
    'Includes: top MSR signals, domain convergence scores, contradiction count,',
    'weakest graha priority class, and quality audit trap1 count.',
    'Primary context-loader for L2 chart queries.',
  ].join(' '),

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (canonical_id from asset_registry)',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha to filter by (default: 'LAHIRI')",
      required: false,
    },
    top_k_signals: {
      type: 'number',
      description: 'How many top MSR signals to return (default: 20, max: 100)',
      required: false,
    },
    signal_class: {
      type: 'string',
      description: "Filter signals by class: 'yoga'|'dosha'|'karaka_alignment'|'composite_state'|'sade_sati'|'panchanga'",
      required: false,
    },
    min_salience: {
      type: 'number',
      description: 'Minimum computed_salience threshold (0..1, default: 0)',
      required: false,
    },
  },

  required_inputs: ['chart_id'],

  llm_hints: {
    agentic: {
      cost_class:      'cheap',
      cacheable:       true,
      pre_fetch:       true,
    },
    bulk_context: {
      pre_fetch_priority: 1,
      context_label:     'bodha_digest',
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id       = String(args.chart_id)
    const ayanamsha_id   = String(args.ayanamsha_id  ?? 'LAHIRI')
    const top_k          = Math.min(Number(args.top_k_signals ?? 20), 100)
    const signal_class   = args.signal_class ? String(args.signal_class) : null
    const min_salience   = Number(args.min_salience ?? 0)

    // ── Digest from vw_chart_digest ─────────────────────────────────────────
    const digestSql = `
      SELECT msr_signal_count, yoga_count, dosha_count,
             avg_salience, max_salience, contradiction_count,
             weakest_graha, top_priority_class,
             top_convergence_domains, trap1_count, digest_at
      FROM vw_chart_digest
      WHERE chart_id = $1 AND ayanamsha_id = $2
    `

    // ── Top signals from bodha_msr_signals ──────────────────────────────────
    const classFilter    = signal_class ? `AND signal_type_class = $5` : ''
    const salienceFilter = min_salience > 0 ? `AND computed_salience >= $6` : ''
    const signalSql = `
      SELECT signal_id, signal_type_id, signal_type_class, signal_tradition,
             computed_salience, top_k_salience_rank, domains_affected_array,
             verification_pass_status, configuration_jsonb, citation_human
      FROM bodha_msr_signals
      WHERE chart_id = $1 AND ayanamsha_id = $2
        ${classFilter}
        ${salienceFilter}
      ORDER BY computed_salience DESC NULLS LAST
      LIMIT $3 OFFSET $4
    `

    // ── Top convergence domains ──────────────────────────────────────────────
    const convSql = `
      SELECT domain, convergence_count, convergence_score, cross_tradition_count,
             salience_weighted_sum, contradiction_count
      FROM bodha_convergence
      WHERE chart_id = $1 AND ayanamsha_id = $2 AND snapshot_type = 'static_natal'
      ORDER BY convergence_score DESC NULLS LAST
      LIMIT 7
    `

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      const signalParams: unknown[] = [chart_id, ayanamsha_id, top_k, 0]
      if (signal_class)  signalParams.push(signal_class)
      if (min_salience > 0) signalParams.push(min_salience)

      const [digestResult, signalResult, convResult] = await Promise.all([
        db.query(digestSql, [chart_id, ayanamsha_id]),
        db.query(signalSql, signalParams),
        db.query(convSql,   [chart_id, ayanamsha_id]),
      ])

      const digest = digestResult.rows[0] ?? {}

      return {
        content: {
          chart_id,
          ayanamsha_id,
          digest: {
            msr_signal_count:     digest.msr_signal_count,
            yoga_count:           digest.yoga_count,
            dosha_count:          digest.dosha_count,
            avg_salience:         digest.avg_salience,
            max_salience:         digest.max_salience,
            contradiction_count:  digest.contradiction_count,
            weakest_graha:        digest.weakest_graha,
            top_priority_class:   digest.top_priority_class,
            trap1_count:          digest.trap1_count,
          },
          top_signals:           signalResult.rows,
          convergence_domains:   convResult.rows,
          filters: { top_k, signal_class, min_salience },
        },
        is_error: false,
      }
    } catch (err) {
      return {
        content: { error: String(err), chart_id, ayanamsha_id },
        is_error: true,
      }
    }
  },
}

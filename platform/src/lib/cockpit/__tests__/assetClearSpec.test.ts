import { describe, it, expect } from 'vitest'
import { EXPLICIT_CLEAR_OPS, deriveDeleteSqlFromCountSql } from '@/lib/cockpit/assetClearSpec'

/**
 * Locks the clear-completeness fix: writers that emit multiple tables must have an
 * EXPLICIT_CLEAR_OPS entry that deletes EVERY table they write (FK-child-first),
 * each chart-scoped. Before this, the single target_table delete left secondary
 * tables behind and a layer clear appeared to "not clear".
 */
const EXPECTED_TABLES: Record<string, string[]> = {
  // L4 Phala
  ph_rectification: ['phala_rectification_best', 'phala_rectification'],
  // L2 Bodha
  bo_karanajala: ['bodha_contradictions', 'bodha_cgm_edges'],
  bo_sangati: ['bodha_convergence', 'bodha_cdlm_cells'],
  bo_upaya: [
    'bodha_rm_dasha_windowed_prescriptions',
    'bodha_rm_remedy_prescriptions',
    'bodha_rm_resonances',
  ],
  bo_anveshana: ['bodha_anomalies', 'bodha_discoveries'],
  // L5 Mīmāṃsā
  mi_bhavisya: ['mimamsa_manifestation_sets', 'mimamsa_predictions'],
  mi_pramana: ['mimamsa_reliability', 'mimamsa_calibration'],
  mi_pariksha: ['mimamsa_attribution', 'mimamsa_discoveries', 'mimamsa_qa_eval'],
  mi_darshana: ['mimamsa_insight_embeddings', 'mimamsa_insight_units'],
  mi_adhilepa: [
    'mimamsa_load_bearing',
    'mimamsa_convergence_adjustment',
    'mimamsa_anchor_adjustment',
    'mimamsa_signal_adjustment',
    'mimamsa_fact_adjustment',
  ],
}

describe('EXPLICIT_CLEAR_OPS — multi-table writer completeness', () => {
  for (const [assetId, tables] of Object.entries(EXPECTED_TABLES)) {
    it(`${assetId} deletes exactly its writer tables, in order, chart-scoped`, () => {
      const ops = EXPLICIT_CLEAR_OPS[assetId]
      expect(ops, `${assetId} must have an explicit clear spec`).toBeTruthy()
      const deletedTables = (ops ?? []).map(op => {
        const m = op.sql.match(/DELETE FROM (\w+)/i)
        return m?.[1]
      })
      expect(deletedTables).toEqual(tables)
      // Every per_chart delete must be chart-scoped — never an unscoped wipe.
      for (const op of ops ?? []) {
        expect(op.sql, `${assetId}: "${op.sql}" must be chart-scoped`).toMatch(/WHERE chart_id = \$1/)
      }
    })
  }

  it('mi_adhilepa includes mimamsa_signal_adjustment (confirmed output table per migration 369)', () => {
    const ops = EXPLICIT_CLEAR_OPS['mi_adhilepa'] ?? []
    expect(ops.some(op => /signal_adjustment/.test(op.sql))).toBe(true)
  })

  it('bo_samvada is an explicit null (view-backed asset, nothing to clear)', () => {
    // vw_chart_digest is a VIEW — DELETE would error. null = skip cleanly.
    expect('bo_samvada' in EXPLICIT_CLEAR_OPS).toBe(true)
    expect(EXPLICIT_CLEAR_OPS['bo_samvada']).toBeNull()
  })

  it('mi_abhilekha preserves answered journal rows (JL-020 IRREPLACEABLE)', () => {
    const ops = EXPLICIT_CLEAR_OPS['mi_abhilekha']
    expect(ops, 'mi_abhilekha must have an explicit clear spec').toBeTruthy()
    expect(ops).toHaveLength(1)
    expect(ops![0].sql).toMatch(/DELETE FROM mimamsa_journal/)
    expect(ops![0].sql).toMatch(/WHERE chart_id = \$1/)
    expect(ops![0].sql).toMatch(/answered_at IS NULL/)
  })

  it('mi_bhavisya preserves recorded prediction outcomes (JL-020 IRREPLACEABLE)', () => {
    const ops = EXPLICIT_CLEAR_OPS['mi_bhavisya'] ?? []
    const predictionsOp = ops.find(op => /mimamsa_predictions/.test(op.sql))
    expect(predictionsOp, 'mi_bhavisya must clear mimamsa_predictions').toBeTruthy()
    expect(predictionsOp!.sql).toMatch(/outcome_observed IS NULL/)
  })

  it('lel_events is an explicit null — a clear/rebuild leaves LEL rows intact (JL-010/JL-020 IRREPLACEABLE)', () => {
    // life_events + event_chart_state_index are user-authored source data (migration
    // 423, has_writer=false). A per-chart clear must NEVER delete them.
    expect('lel_events' in EXPLICIT_CLEAR_OPS).toBe(true)
    expect(EXPLICIT_CLEAR_OPS['lel_events']).toBeNull()

    // Destructive-op guard: prove the null is load-bearing. The registered count_sql
    // WOULD auto-transform into a per-chart DELETE if not explicitly skipped — that is
    // the exact irreplaceable-loss failure mode the null prevents.
    const lelCountSql = 'SELECT count(*) FROM life_events WHERE chart_id = $1'
    expect(deriveDeleteSqlFromCountSql(lelCountSql))
      .toBe('DELETE FROM life_events WHERE chart_id = $1')
    // Because the explicit spec is null, that derived DELETE is never executed.
  })
})

describe('deriveDeleteSqlFromCountSql', () => {
  it('transforms a simple single-table chart-scoped count', () => {
    expect(deriveDeleteSqlFromCountSql('SELECT count(*) FROM mimamsa_predictions WHERE chart_id = $1'))
      .toBe('DELETE FROM mimamsa_predictions WHERE chart_id = $1')
  })

  it('returns null for a compound (subquery-sum) count it cannot safely transform', () => {
    const compound =
      'SELECT (SELECT count(*) FROM a WHERE chart_id = $1) + (SELECT count(*) FROM b WHERE chart_id = $1) AS count'
    expect(deriveDeleteSqlFromCountSql(compound)).toBeNull()
  })
})

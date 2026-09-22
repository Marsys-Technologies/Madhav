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
  bo_sangati: ['bodha_convergence', 'bodha_cdlm_cells', 'bodha_triangulation'],
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
    // R6 fix: `outcome_observed` never existed on the live schema (mimamsa_predictions was
    // dropped and recreated by migration 347 with a different column set) — this DELETE threw
    // on every real execution and, sharing a savepoint with the manifestation_sets delete,
    // silently rolled that back too. The real "recorded outcome" signal on the current schema
    // is lifecycle_status leaving 'pending'/'due' (mi_abhilekha.py is the sole writer that
    // transitions a row to 'confirmed'/'denied').
    const ops = EXPLICIT_CLEAR_OPS['mi_bhavisya'] ?? []
    const predictionsOp = ops.find(op => /mimamsa_predictions/.test(op.sql))
    expect(predictionsOp, 'mi_bhavisya must clear mimamsa_predictions').toBeTruthy()
    expect(predictionsOp!.sql).not.toMatch(/outcome_observed/)
    expect(predictionsOp!.sql).toMatch(/lifecycle_status IN \('pending', 'due'\)/)
  })

  it('ga_structural clears its owned chart_facts categories via the ownership subquery (not a broken JOIN)', () => {
    // Root cause of a live bug: ga_structural's count_sql (migration 410) joins
    // fact_category_ownership, and deriveDeleteSqlFromCountSql() correctly refuses to
    // auto-transform that (see the JOIN-guard test below) — so without this explicit
    // entry, ga_structural fell through to "no clear spec resolved" and its chart_facts
    // rows (argala/aspect/dispositor/etc. categories) silently survived every clear
    // while asset_throughput still reported it as cleared.
    const ops = EXPLICIT_CLEAR_OPS['ga_structural']
    expect(ops, 'ga_structural must have an explicit clear spec').toBeTruthy()
    expect(ops).toHaveLength(1)
    expect(ops![0].sql).toMatch(/DELETE FROM chart_facts/)
    expect(ops![0].sql).toMatch(/WHERE chart_id = \$1/)
    expect(ops![0].sql).toMatch(/fact_category_ownership/)
    expect(ops![0].sql).toMatch(/owning_asset_id = 'ga_structural'/)
    // Must not contain a JOIN — this is a subquery-scoped DELETE, not the invalid
    // `DELETE FROM ... JOIN ...` shape the naive auto-derivation would have produced.
    expect(ops![0].sql).not.toMatch(/\bJOIN\b/i)
  })

  it('lel_events is an explicit null — a clear/rebuild leaves LEL rows intact (JL-010/JL-020 IRREPLACEABLE)', () => {    // life_events + event_chart_state_index are user-authored source data (migration
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

  it("ka_gochara deletes coverage → contacts → windows, generation-scoped, no JOIN (WP7 C-1 / F-24)", () => {
    // F-24: ka_gochara's re-pinned count_sql reaches ONLY kala_gochara_windows —
    // without this entry a chart-owner Clear would orphan every kala_gochara_contacts /
    // kala_gochara_coverage row. Three WHERE-scoped DELETEs in dependency order, pinned
    // to generation '4.0' so v1 / '3.0' / g3_* rows are unreachable here.
    const ops = EXPLICIT_CLEAR_OPS['ka_gochara']
    expect(ops, 'ka_gochara must have an explicit clear spec').toBeTruthy()
    expect(ops).toHaveLength(3)
    const deletedTables = ops!.map(op => op.sql.match(/DELETE FROM (\w+)/i)?.[1])
    expect(deletedTables).toEqual([
      'kala_gochara_coverage',
      'kala_gochara_contacts',
      'kala_gochara_windows',
    ])
    for (const op of ops!) {
      expect(op.sql).toMatch(/WHERE chart_id = \$1 AND generation = '4\.0'/)
      expect(op.sql).not.toMatch(/\bJOIN\b/i)
    }
  })

  it("ka_gochara carries the authoritative-generation refusal guard on its first op (WP7 C-1 Option A)", () => {
    const ops = EXPLICIT_CLEAR_OPS['ka_gochara']!
    const guard = ops[0].guard
    expect(guard, 'first op must carry the refusal guard').toBeTruthy()
    expect(guard!.sql).toMatch(/FROM kala_gochara_authority/)
    expect(guard!.sql).toMatch(/chart_id = \$1/)
    expect(guard!.sql).toMatch(/authoritative_generation = '4\.0'/)
    expect(guard!.refuse_message).toMatch(/authoritative generation/)
    // Only the first op carries the guard — it refuses the whole asset.
    expect(ops[1].guard).toBeUndefined()
    expect(ops[2].guard).toBeUndefined()
    // Release-authority cascade: authority reset + manifest 'cleared'.
    expect(guard!.cascade).toEqual([
      'DELETE FROM kala_gochara_authority WHERE chart_id = $1',
      "UPDATE kala_gochara_publication SET status = 'cleared' WHERE chart_id = $1 AND generation = '4.0'",
    ])
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

  it('returns null for a JOIN-bearing count_sql instead of emitting invalid DELETE FROM ... JOIN SQL', () => {
    // The live bug this guards: ga_structural's real count_sql (migration 410) is exactly
    // this shape. Before the guard, the naive prefix-swap produced
    // `DELETE FROM chart_facts cf JOIN fact_category_ownership fco ON ... WHERE ...` —
    // not legal Postgres (DELETE FROM doesn't support JOIN, only USING) — which threw at
    // execute time, got swallowed into failed_tables, while the caller still marked the
    // asset as successfully cleared. Returning null here forces callers onto an explicit
    // EXPLICIT_CLEAR_OPS entry instead of silently executing broken SQL.
    const ownershipJoin = `SELECT count(*) AS count FROM chart_facts cf
      JOIN fact_category_ownership fco ON fco.fact_category = cf.fact_category
      WHERE cf.chart_id = $1 AND fco.owning_asset_id = 'ga_structural'`
    expect(deriveDeleteSqlFromCountSql(ownershipJoin)).toBeNull()
  })

  it('JOIN guard is case-insensitive and matches inner/left/right join variants', () => {
    expect(deriveDeleteSqlFromCountSql('SELECT count(*) FROM a join b ON a.id=b.id WHERE a.chart_id=$1')).toBeNull()
    expect(deriveDeleteSqlFromCountSql('SELECT count(*) FROM a LEFT JOIN b ON a.id=b.id WHERE a.chart_id=$1')).toBeNull()
    expect(deriveDeleteSqlFromCountSql('SELECT count(*) FROM a INNER JOIN b ON a.id=b.id WHERE a.chart_id=$1')).toBeNull()
  })
})

/**
 * B1 live-path evidence (Kāla pre-elevation Phase 1.1).
 *
 * This block does NOT test a fix — it PINS the exact hazard the fix stands in
 * front of, so that if anyone later removes the `is_active` filter the SQL this
 * derivation produces is on the record rather than rediscovered under a live
 * incident. It passed before the fix and passes after it; the detector for the
 * fix is `clear/__tests__/route.authz.test.ts`'s B1 block and migration 1071's
 * live-DB suite, not this.
 *
 * The parallel-lane question this settles, at the code: the execute route's
 * resolution order (execute/route.ts:160-183) is
 *   1. EXPLICIT_CLEAR_OPS   — `ka_gochara_sweep` has NO entry (see this file's
 *                             own map), so the branch is skipped;
 *   2. count_sql            — present, and auto-transformable → THIS WINS at :168;
 *   3. target_table fallback — :175, never reached for this asset.
 * So the live vector is the registry `count_sql`, not `target_table`. Correcting
 * a `target_table` alone would not have closed it.
 */
describe('B1 — the ka_gochara_sweep live deletion vector', () => {
  // Verbatim from production asset_registry, measured 2026-09-22.
  const LIVE_SWEEP_COUNT_SQL =
    "SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='v1'"

  it('transforms the retired sweep count_sql into a DELETE of the protected v1 snapshot', () => {
    expect(deriveDeleteSqlFromCountSql(LIVE_SWEEP_COUNT_SQL)).toBe(
      "DELETE FROM kala_gochara_windows WHERE chart_id=$1 AND generation='v1'"
    )
  })

  it('has no EXPLICIT_CLEAR_OPS entry, so nothing diverts that derivation', () => {
    // If a future change adds one, this assertion fails and forces a re-read of
    // which layer is actually protecting the snapshot.
    expect('ka_gochara_sweep' in EXPLICIT_CLEAR_OPS).toBe(false)
  })

  it('the ACTIVE ka_gochara sibling derives a _v2-scoped DELETE — it is a different table', () => {
    // Production value, measured the same day. It never names kala_gochara_windows,
    // which is why `ka_gochara`'s stale `target_table` was not itself the live
    // deletion vector (Part A of this task).
    expect(
      deriveDeleteSqlFromCountSql(
        "SELECT COUNT(*) FROM kala_gochara_windows_v2 WHERE chart_id=$1 AND generation='2.0'"
      )
    ).toBe("DELETE FROM kala_gochara_windows_v2 WHERE chart_id=$1 AND generation='2.0'")
  })
})

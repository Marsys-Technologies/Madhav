/**
 * Asset invalidation policies (Jātaka chart workspace, Task 5).
 *
 * operator-best-effort — the cockpit's existing savepoint behaviour.
 * chart-correction-strict — every clear must succeed on the caller's
 * transaction; no savepoints; any failure throws so the whole correction rolls
 * back. Human-authored and irreplaceable material is preserved by an explicit,
 * tested boundary rather than by accident.
 */
import { describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

import { EXPLICIT_CLEAR_OPS } from '@/lib/cockpit/assetClearSpec'
import { markChartContextStale } from '@/lib/charts/chartContextStaleness'
import {
  CORRECTION_NOTHING_TO_CLEAR,
  CORRECTION_PRESERVATION,
  InvalidationError,
  invalidateAssets,
} from '../assetInvalidation'
import type { Queryable, RegistryEntryWithScope } from '../runPreparation'

const CHART = 'c-1'

function asset(asset_id: string, extra: Partial<RegistryEntryWithScope> = {}): RegistryEntryWithScope {
  return {
    asset_id, layer: 'kala', depends_on: [], estimated_seconds: 1, scope: 'per_chart', has_writer: true,
    target_table: null, count_sql: null, natural_key_partition: null,
    asset_kind: 'data', asset_type: 'data', health_probe: null,
    ...extra,
  } as RegistryEntryWithScope
}

function recorder(fail?: RegExp) {
  const calls: Array<{ sql: string; params: unknown[] }> = []
  const db: Queryable = {
    query: vi.fn(async (sql: string, params: unknown[] = []) => {
      calls.push({ sql, params })
      if (fail?.test(sql)) throw new Error(`relation error on ${sql}`)
      return { rows: [], rowCount: 0 }
    }) as unknown as Queryable['query'],
  }
  return { db, calls }
}

describe('correction preservation boundary', () => {
  it('names exactly the governed skip-clean assets that hold non-regenerable data, with a reason each', () => {
    expect(Object.keys(CORRECTION_PRESERVATION).sort()).toEqual(['lel_events', 'mi_bhavisya', 'mi_seva', 'mi_vistara'])
    for (const id of Object.keys(CORRECTION_PRESERVATION)) {
      expect(EXPLICIT_CLEAR_OPS[id]).toBeNull()
      expect(CORRECTION_PRESERVATION[id as keyof typeof CORRECTION_PRESERVATION].length).toBeGreaterThan(10)
    }
    expect(EXPLICIT_CLEAR_OPS.bo_samvada).toBeNull()
    expect(Object.keys(CORRECTION_NOTHING_TO_CLEAR).sort()).toEqual(['bo_samvada', 'ka_dasha_kala', 'ka_tulana'])
  })

  it('every null clear op is classified — a new skip-clean asset cannot slip through unclassified', () => {
    const nulls = Object.entries(EXPLICIT_CLEAR_OPS).filter(([, ops]) => ops === null).map(([id]) => id).sort()
    // ga_fact_identity had an explicit null while it had no writer (migration 1262); migration 1333 registered its writer and
    // gave it a real spec, so no has_writer=false asset has a null spec of its own any more.
    expect(nulls).toEqual([...Object.keys(CORRECTION_PRESERVATION), ...Object.keys(CORRECTION_NOTHING_TO_CLEAR)].sort())
  })

  it('ga_fact_identity (a rebuildable cache with a REGISTERED writer since migration 1333) is cleared by a correction with one chart-scoped DELETE', async () => {
    const { db, calls } = recorder()
    const result = await invalidateAssets({
      db, chartId: CHART, assets: [asset('ga_fact_identity', { layer: 'ganita', has_writer: true })], policy: 'chart-correction-strict',
    })
    expect(calls.map((c) => c.sql)).toEqual(['DELETE FROM chart_fact_identity WHERE chart_id = $1'])
    expect(calls[0].params).toEqual([CHART])
    expect(result.clearedAssetIds).toEqual(['ga_fact_identity'])
    expect(result.preservedAssetIds).toEqual([])
  })

  it('a writer-less ga_fact_identity (the 1262 shape, before 1333 applies) is still preserved by the has_writer rule, not by name', async () => {
    const { db, calls } = recorder()
    const result = await invalidateAssets({
      db, chartId: CHART, assets: [asset('ga_fact_identity', { layer: 'ganita', has_writer: false })], policy: 'chart-correction-strict',
    })
    expect(calls).toEqual([])
    expect(result.preservedAssetIds).toEqual(['ga_fact_identity'])
  })

  it('answered journal rows survive: mi_abhilekha clears only unanswered prompts', async () => {
    const { db, calls } = recorder()
    await invalidateAssets({ db, chartId: CHART, assets: [asset('mi_abhilekha', { layer: 'mimamsa' })], policy: 'chart-correction-strict' })
    expect(calls.map((c) => c.sql)).toEqual(['DELETE FROM mimamsa_journal WHERE chart_id = $1 AND answered_at IS NULL'])
  })

  it('predictions and manifestation sets survive a correction: mi_bhavisya issues no statement at all (SS N-104)', async () => {
    for (const policy of ['chart-correction-strict', 'operator-best-effort'] as const) {
      const { db, calls } = recorder()
      const result = await invalidateAssets({ db, chartId: CHART, assets: [asset('mi_bhavisya', { layer: 'mimamsa' })], policy })
      expect(calls, policy).toEqual([])
      expect(result.clearedAssetIds, policy).toEqual([])
    }
  })

  it('an append-only asset is never a silent skip: both policies return the explicit message and issue no statement (SS N-104)', async () => {
    for (const policy of ['chart-correction-strict', 'operator-best-effort'] as const) {
      const { db, calls } = recorder()
      const result = await invalidateAssets({ db, chartId: CHART, assets: [asset('mi_bhavisya', { layer: 'mimamsa' })], policy })
      expect(calls, policy).toEqual([])
      expect(result.notices, policy).toEqual([
        { assetId: 'mi_bhavisya', message: 'mi_bhavisya is append-only (N-104): nothing cleared' },
      ])
    }
  })

  it('other assets produce no notice (the message channel is a narrow opt-in)', async () => {
    const { db } = recorder()
    const result = await invalidateAssets({
      db, chartId: CHART, assets: [asset('mi_abhilekha', { layer: 'mimamsa' })], policy: 'chart-correction-strict',
    })
    expect(result.notices).toEqual([])
  })

  it('a strict birth-detail correction leaves predictions undeleted and only SETS the stale marker + superseding run (SS N-104/N-107)', async () => {
    // The order recomputeChart.ts runs inside one transaction: strict invalidation, then markChartContextStale.
    const RUN = '11111111-2222-3333-4444-555555555555'
    const { db, calls } = recorder()
    await invalidateAssets({ db, chartId: CHART, assets: [asset('mi_bhavisya', { layer: 'mimamsa' })], policy: 'chart-correction-strict' })
    await markChartContextStale({ db, chartId: CHART, runId: RUN })
    const onPredictions = calls.filter((c) => /mimamsa_predictions/i.test(c.sql))
    // exactly one statement touches the table, and it is an UPDATE - never a DELETE / TRUNCATE / INSERT
    expect(onPredictions).toHaveLength(1)
    expect(onPredictions[0].sql).toMatch(/^\s*UPDATE\s+mimamsa_predictions\b/i)
    expect(calls.filter((c) => /^\s*(DELETE|TRUNCATE|INSERT)\b/i.test(c.sql))).toEqual([])
    // it sets the marker pair and the superseding run (the set-once allow-list of migration 1265), nothing else
    const set = onPredictions[0].sql.match(/SET([\s\S]*?)WHERE/i)![1]
    const assigned = [...set.matchAll(/(\w+)\s*=/g)].map((m) => m[1]).sort()
    expect(assigned).toEqual(['chart_context_stale_at', 'chart_context_stale_reason', 'chart_context_superseded_by_run_id'])
    expect(onPredictions[0].sql).toMatch(/chart_context_stale_at\s+IS\s+NULL/i) // set once: an already-marked row is not touched
    expect(onPredictions[0].params).toEqual([CHART, RUN])
  })

  it('service-only writers with no chart rows require no destructive clear', async () => {
    const { db, calls } = recorder()
    const result = await invalidateAssets({
      db,
      chartId: CHART,
      assets: [
        asset('ka_dasha_kala', { asset_kind: 'service', asset_type: 'service' }),
        asset('ka_tulana', { asset_kind: 'service', asset_type: 'service' }),
      ],
      policy: 'chart-correction-strict',
    })
    expect(calls).toHaveLength(0)
    expect(result.clearedAssetIds).toEqual([])
    expect(result.preservedAssetIds).toEqual([])
  })

  it('attested intervention filings survive: mi_sankalpa clears only the writer\'s own unresolved-elected rows, never a blanket per-chart wipe', async () => {
    const { db, calls } = recorder()
    await invalidateAssets({
      db,
      chartId: CHART,
      assets: [asset('mi_sankalpa', { layer: 'mimamsa', target_table: null, count_sql: 'SELECT count(*) FROM mimamsa_intervention_ledger WHERE chart_id = $1' })],
      policy: 'chart-correction-strict',
    })
    // Mirrors services/mi_sankalpa/db.py's own delete_unresolved() predicate exactly —
    // never the generic count_sql-derived unconditional per-chart DELETE, which would
    // destroy attested performed/outcome_event_id filings a native has already made.
    expect(calls.map((c) => c.sql)).toEqual([
      "DELETE FROM mimamsa_intervention_ledger WHERE chart_id = $1 AND study_arm = 'elected_pending' AND performed IS NULL AND outcome_event_id IS NULL",
    ])
  })
})

describe('invalidateAssets — chart-correction-strict', () => {
  it('clears in reverse of the given dependency order, with chart-scoped params and no savepoints', async () => {
    const { db, calls } = recorder()
    const result = await invalidateAssets({
      db,
      chartId: CHART,
      assets: [
        asset('ka_up', { count_sql: 'SELECT count(*) FROM kala_up WHERE chart_id = $1' }),
        asset('ka_down', { target_table: 'kala_down' }),
      ],
      policy: 'chart-correction-strict',
    })
    expect(calls.map((c) => c.sql)).toEqual([
      'DELETE FROM kala_down WHERE chart_id = $1',
      'DELETE FROM kala_up WHERE chart_id = $1',
    ])
    expect(calls.every((c) => c.params[0] === CHART)).toBe(true)
    expect(calls.some((c) => /SAVEPOINT/.test(c.sql))).toBe(false)
    expect(result.clearedAssetIds).toEqual(['ka_down', 'ka_up'])
  })

  it('preserves listed assets and writer-less per-chart sources without touching them', async () => {
    const { db, calls } = recorder()
    const result = await invalidateAssets({
      db,
      chartId: CHART,
      assets: [
        asset('lel_events', { has_writer: false, count_sql: 'SELECT count(*) FROM life_events WHERE chart_id = $1' }),
        asset('mi_seva', { layer: 'mimamsa' }),
        asset('xx_manual_source', { has_writer: false, target_table: 'manual_notes' }),
        asset('bo_samvada', { layer: 'bodha' }),
      ],
      policy: 'chart-correction-strict',
    })
    expect(calls).toHaveLength(0)
    expect(result.preservedAssetIds.sort()).toEqual(['lel_events', 'mi_seva', 'xx_manual_source'])
    expect(result.clearedAssetIds).toEqual([])
  })

  it('throws CLEAR_SPEC_MISSING for a writer asset with no safe clear specification', async () => {
    const { db } = recorder()
    const err = await invalidateAssets({ db, chartId: CHART, assets: [asset('ka_nothing')], policy: 'chart-correction-strict' }).catch((e) => e)
    expect(err).toBeInstanceOf(InvalidationError)
    expect(err.code).toBe('CLEAR_SPEC_MISSING')
    expect(err.assetId).toBe('ka_nothing')
  })

  it('refuses an unscoped DELETE derived from an unscoped count_sql', async () => {
    const { db, calls } = recorder()
    await expect(
      invalidateAssets({
        db, chartId: CHART,
        assets: [asset('ka_unscoped', { count_sql: 'SELECT count(*) FROM kala_everything' })],
        policy: 'chart-correction-strict',
      }),
    ).rejects.toMatchObject({ code: 'CLEAR_SPEC_MISSING' })
    expect(calls).toHaveLength(0)
  })

  it('refuses to clear any global asset in a correction', async () => {
    const { db, calls } = recorder()
    await expect(
      invalidateAssets({ db, chartId: CHART, assets: [asset('mi_kula', { scope: 'global', layer: 'mimamsa' })], policy: 'chart-correction-strict' }),
    ).rejects.toMatchObject({ code: 'CLEAR_SPEC_MISSING' })
    expect(calls).toHaveLength(0)
  })

  it('rejects an invalid target_table name instead of interpolating it', async () => {
    const { db, calls } = recorder()
    await expect(
      invalidateAssets({ db, chartId: CHART, assets: [asset('ka_bad', { target_table: 'x; DROP TABLE charts' })], policy: 'chart-correction-strict' }),
    ).rejects.toMatchObject({ code: 'CLEAR_SPEC_MISSING' })
    expect(calls).toHaveLength(0)
  })

  it('propagates any SQL failure so the caller’s transaction rolls back', async () => {
    const { db } = recorder(/kala_up/)
    await expect(
      invalidateAssets({
        db, chartId: CHART,
        assets: [asset('ka_up', { target_table: 'kala_up' }), asset('ka_down', { target_table: 'kala_down' })],
        policy: 'chart-correction-strict',
      }),
    ).rejects.toThrow(/relation error/)
  })
})

describe('invalidateAssets — operator-best-effort (cockpit)', () => {
  it('wraps each asset in a savepoint and continues past a failing DELETE', async () => {
    const { db, calls } = recorder(/DELETE FROM kala_down/)
    const result = await invalidateAssets({
      db, chartId: CHART,
      assets: [asset('ka_up', { target_table: 'kala_up' }), asset('ka_down', { target_table: 'kala_down' })],
      policy: 'operator-best-effort',
    })
    expect(calls.map((c) => c.sql)).toEqual([
      'SAVEPOINT cb_0',
      'DELETE FROM kala_down WHERE chart_id = $1',
      'ROLLBACK TO SAVEPOINT cb_0',
      'RELEASE SAVEPOINT cb_0',
      'SAVEPOINT cb_1',
      'DELETE FROM kala_up WHERE chart_id = $1',
      'RELEASE SAVEPOINT cb_1',
    ])
    expect(result.failedAssetIds).toEqual(['ka_down'])
    expect(result.clearedAssetIds).toEqual(['ka_up'])
  })

  it('skips null clear ops and assets without a spec, as the cockpit always has', async () => {
    const { db, calls } = recorder()
    await invalidateAssets({
      db, chartId: CHART,
      assets: [asset('lel_events', { has_writer: false }), asset('ka_nothing')],
      policy: 'operator-best-effort',
    })
    expect(calls).toHaveLength(0)
  })

  it('keeps the operator’s explicit global clear for a force_l0 global asset', async () => {
    const { db, calls } = recorder()
    await invalidateAssets({
      db, chartId: CHART,
      assets: [asset('bg_thing', { scope: 'global', layer: 'brahmagyan', target_table: 'bg_thing_t' })],
      policy: 'operator-best-effort',
    })
    expect(calls.map((c) => [c.sql, c.params])).toContainEqual(['DELETE FROM bg_thing_t', []])
  })

  it('throws INVALID_TABLE for an invalid fallback table name', async () => {
    const { db } = recorder()
    await expect(
      invalidateAssets({ db, chartId: CHART, assets: [asset('ka_bad', { target_table: 'Bad Name' })], policy: 'operator-best-effort' }),
    ).rejects.toMatchObject({ code: 'INVALID_TABLE' })
  })
})

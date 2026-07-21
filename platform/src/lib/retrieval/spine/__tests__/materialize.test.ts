/**
 * materialize.test.ts — persistence + read-path tests for spine bundles.
 *
 * Proves the two load-bearing claims from the task brief:
 *   1. Byte-consistency: a materialized (persisted, then read back) bundle is
 *      identical to a fresh non-materialized computation over the same data —
 *      no silent staleness / no divergent second implementation.
 *   2. Staleness detection: a persisted row older than the source assets'
 *      current build state is treated as stale and recomputed, never served
 *      silently as fresh.
 *
 * Mocks '@/lib/db/client' for BOTH the underlying capabilities' queries (signals/
 * activations/anchors/calibration) AND materialize.ts's own persistence queries
 * (bodha_spine_bundles SELECT/DELETE/INSERT, asset_throughput marker SELECT) —
 * all go through the same query() entry point, so one mock covers the whole path.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { computeSpineBundle } from '../compute_spine_bundle'
import {
  materializeSpineBundle,
  getOrMaterializeSpineBundle,
  getSourceAssetMarker,
} from '../materialize'
import { __clearRetrievalCache } from '../../cache'

const CHART_B = '22222222-2222-2222-2222-222222222222'

function sqlContains(sql: string, needle: string): boolean {
  if (typeof sql !== 'string') return false
  return sql.replace(/\s+/g, ' ').includes(needle)
}

const FIXTURE_SIGNALS = [
  { signal_id: 'SIG-A', signal_headline_text: 'Venus in 7th', computed_salience: 0.8, domains_affected_array: ['relationship'], valence: 'positive' },
]
const FIXTURE_ANCHORS = [
  { anchor_id: 'ANC-1', signal_id: 'SIG-A', domain: 'relationship', magnitude: 0.6 },
]

/** Installs the four underlying-capability fixtures (see compute_spine_bundle.test.ts's
 *  ordering note for why kala_activation must be checked before bodha_msr_signals). */
function installComputeFixtures(queryFn: ReturnType<typeof vi.fn>) {
  queryFn.mockImplementation(async (sql: string, params?: unknown[]) => {
    // Vitest's own per-test cleanup machinery invokes every live mock once with
    // no arguments as part of its bookkeeping — harmless, not a real call this
    // module ever makes (verified: no code path here calls query() with 0 args).
    if (sql === undefined) return { rows: [] }
    if (sqlContains(sql, 'information_schema')) return { rows: [] }
    if (sqlContains(sql, 'FROM kala_activation_predicates')) return { rows: [] }
    if (sqlContains(sql, 'FROM kala_activation')) return { rows: [] }
    if (sqlContains(sql, 'FROM bodha_msr_signals')) return { rows: FIXTURE_SIGNALS }
    if (sqlContains(sql, 'FROM phala_anchors')) return { rows: FIXTURE_ANCHORS }
    if (sqlContains(sql, 'FROM mimamsa_calibration')) return { rows: [] }
    if (sqlContains(sql, 'FROM mimamsa_reliability')) return { rows: [] }
    if (sqlContains(sql, 'FROM mimamsa_multipliers')) return { rows: [] }
    if (sqlContains(sql, 'FROM mimamsa_qa_eval')) return { rows: [] }
    if (sqlContains(sql, 'FROM asset_throughput')) return { rows: [{ latest: '2026-07-01T00:00:00.000Z' }] }
    if (sqlContains(sql, 'DELETE FROM bodha_spine_bundles')) return { rows: [] }
    if (sqlContains(sql, 'INSERT INTO bodha_spine_bundles')) return { rows: [] }
    if (sqlContains(sql, 'SELECT bundle_jsonb')) return { rows: [] } // overridden per-test below
    throw new Error(`unexpected SQL in test fixture: ${sql} ${JSON.stringify(params)}`)
  })
}

describe('materializeSpineBundle', () => {
  beforeEach(() => {
    queryMock.mockReset()
    __clearRetrievalCache() // query_signals.ts caches by (tool_name, args-hash) — must not bleed across tests
  })

  it('persists a delete-then-insert (never an accreting insert) scoped to chart/ayanamsha/domain', async () => {
    installComputeFixtures(queryMock)

    await materializeSpineBundle(CHART_B, 'relationship')

    const deleteCalls = queryMock.mock.calls.filter(([sql]) => sqlContains(sql as string, 'DELETE FROM bodha_spine_bundles'))
    const insertCalls = queryMock.mock.calls.filter(([sql]) => sqlContains(sql as string, 'INSERT INTO bodha_spine_bundles'))
    expect(deleteCalls).toHaveLength(1)
    expect(insertCalls).toHaveLength(1)

    const deleteParams = deleteCalls[0][1] as unknown[]
    expect(deleteParams).toEqual([CHART_B, 'lahiri_chitrapaksha', 'relationship'])

    const insertParams = insertCalls[0][1] as unknown[]
    expect(insertParams[0]).toBe(CHART_B)
    expect(insertParams[2]).toBe('relationship')
    const persistedContent = JSON.parse(insertParams[5] as string)
    expect(persistedContent.signal_count).toBe(1)
  })
})

describe('getOrMaterializeSpineBundle — byte consistency (no silent staleness)', () => {
  beforeEach(() => {
    queryMock.mockReset()
    __clearRetrievalCache() // query_signals.ts caches by (tool_name, args-hash) — must not bleed across tests
  })

  it('a materialized-then-read bundle is byte-identical to a fresh non-materialized computeSpineBundle() call', async () => {
    installComputeFixtures(queryMock)

    // 1. Fresh, non-materialized computation (what a caller would see calling the
    //    four underlying capabilities directly, with no persistence involved at all).
    const fresh = await computeSpineBundle({ chart_id: CHART_B, domain: 'relationship', top_k: 15 })

    // 2. Materialize (persist) — capture exactly what got written.
    queryMock.mockClear()
    installComputeFixtures(queryMock)
    let persistedRow: { bundle_jsonb: string; top_k: number; source_asset_marker: string | null } | null = null
    const originalImpl = queryMock.getMockImplementation()!
    queryMock.mockImplementation(async (sql: string, params?: unknown[]) => {
      if (sqlContains(sql, 'INSERT INTO bodha_spine_bundles')) {
        persistedRow = {
          bundle_jsonb: (params as unknown[])[5] as string,
          top_k: (params as unknown[])[3] as number,
          source_asset_marker: (params as unknown[])[6] as string | null,
        }
        return { rows: [] }
      }
      return originalImpl(sql, params)
    })
    await materializeSpineBundle(CHART_B, 'relationship', { topK: 15 })
    expect(persistedRow).not.toBeNull()

    // 3. Read path: persisted row exists and is fresh (marker unchanged) — serves
    //    the MATERIALIZED row, not a recompute.
    queryMock.mockClear()
    queryMock.mockImplementation(async (sql: string) => {
      if (sql === undefined) return { rows: [] } // Vitest cleanup-phase phantom call — see note above
      if (sqlContains(sql, 'SELECT bundle_jsonb')) {
        return {
          rows: [{
            bundle_jsonb: JSON.parse(persistedRow!.bundle_jsonb),
            top_k: persistedRow!.top_k,
            computed_at: '2026-07-21T00:00:00.000Z',
            source_asset_marker: persistedRow!.source_asset_marker,
          }],
        }
      }
      if (sqlContains(sql, 'FROM asset_throughput')) {
        return { rows: [{ latest: persistedRow!.source_asset_marker }] } // no rebuild since materialization
      }
      throw new Error(`unexpected SQL on the served-fresh read path: ${sql}`)
    })
    const result = await getOrMaterializeSpineBundle({ chart_id: CHART_B, domain: 'relationship', top_k: 15 })

    expect(result.source).toBe('materialized')
    // The byte-consistency guarantee: JSON content served from the persisted row is
    // IDENTICAL to a fresh, independent computeSpineBundle() call over the same data.
    expect(JSON.stringify(result.bundle)).toBe(JSON.stringify(fresh))
  })

  it('treats a persisted row as STALE (and recomputes) when a source asset has rebuilt since materialization', async () => {
    const STALE_ROW = {
      bundle_jsonb: { chart_id: CHART_B, ayanamsha_id: 'lahiri_chitrapaksha', domain: 'relationship', top_k: 15, signal_count: 0, signals: [], calibration: { verdict_distribution: [], reliability: [], multipliers: [], qa_fail_count: 0 }, empty_reason: 'stale fixture', provenance: { tables: [], composed_from_capabilities: [] } },
      top_k: 15,
      computed_at: '2026-01-01T00:00:00.000Z',
      source_asset_marker: '2026-01-01T00:00:00.000Z',
    }

    let recomputeTriggered = false
    queryMock.mockImplementation(async (sql: string) => {
      if (sql === undefined) return { rows: [] } // Vitest cleanup-phase phantom call — see note above
      if (sqlContains(sql, 'SELECT bundle_jsonb')) return { rows: [STALE_ROW] }
      if (sqlContains(sql, 'FROM asset_throughput')) {
        // A source asset rebuilt AFTER computed_at/source_asset_marker → stale.
        return { rows: [{ latest: '2026-07-21T00:00:00.000Z' }] }
      }
      if (sqlContains(sql, 'information_schema')) return { rows: [] }
      if (sqlContains(sql, 'FROM kala_activation_predicates')) return { rows: [] }
      if (sqlContains(sql, 'FROM kala_activation')) return { rows: [] }
      if (sqlContains(sql, 'FROM bodha_msr_signals')) { recomputeTriggered = true; return { rows: FIXTURE_SIGNALS } }
      if (sqlContains(sql, 'FROM phala_anchors')) return { rows: FIXTURE_ANCHORS }
      if (sqlContains(sql, 'FROM mimamsa_calibration')) return { rows: [] }
      if (sqlContains(sql, 'FROM mimamsa_reliability')) return { rows: [] }
      if (sqlContains(sql, 'FROM mimamsa_multipliers')) return { rows: [] }
      if (sqlContains(sql, 'FROM mimamsa_qa_eval')) return { rows: [] }
      if (sqlContains(sql, 'DELETE FROM bodha_spine_bundles')) return { rows: [] }
      if (sqlContains(sql, 'INSERT INTO bodha_spine_bundles')) return { rows: [] }
      throw new Error(`unexpected SQL: ${sql}`)
    })

    const result = await getOrMaterializeSpineBundle({ chart_id: CHART_B, domain: 'relationship', top_k: 15 })

    expect(result.source).toBe('fresh_recomputed_stale')
    expect(recomputeTriggered).toBe(true)
    expect(result.bundle.signal_count).toBe(1) // recomputed content, not the stale fixture's signal_count: 0
  })

  it('recomputes+persists (fresh_materialized) when no row exists yet', async () => {
    installComputeFixtures(queryMock)
    queryMock.mockImplementation(async (sql: string, params?: unknown[]) => {
      if (sql === undefined) return { rows: [] } // Vitest cleanup-phase phantom call — see note above
      if (sqlContains(sql, 'SELECT bundle_jsonb')) return { rows: [] } // nothing persisted yet
      if (sqlContains(sql, 'information_schema')) return { rows: [] }
      if (sqlContains(sql, 'FROM kala_activation_predicates')) return { rows: [] }
      if (sqlContains(sql, 'FROM kala_activation')) return { rows: [] }
      if (sqlContains(sql, 'FROM bodha_msr_signals')) return { rows: FIXTURE_SIGNALS }
      if (sqlContains(sql, 'FROM phala_anchors')) return { rows: FIXTURE_ANCHORS }
      if (sqlContains(sql, 'FROM mimamsa_calibration')) return { rows: [] }
      if (sqlContains(sql, 'FROM mimamsa_reliability')) return { rows: [] }
      if (sqlContains(sql, 'FROM mimamsa_multipliers')) return { rows: [] }
      if (sqlContains(sql, 'FROM mimamsa_qa_eval')) return { rows: [] }
      if (sqlContains(sql, 'FROM asset_throughput')) return { rows: [{ latest: null }] }
      if (sqlContains(sql, 'DELETE FROM bodha_spine_bundles')) return { rows: [] }
      if (sqlContains(sql, 'INSERT INTO bodha_spine_bundles')) return { rows: [] }
      throw new Error(`unexpected SQL: ${sql} ${JSON.stringify(params)}`)
    })

    const result = await getOrMaterializeSpineBundle({ chart_id: CHART_B, domain: 'relationship' })
    expect(result.source).toBe('fresh_materialized')
    expect(result.bundle.signal_count).toBe(1)
  })
})

describe('getSourceAssetMarker', () => {
  beforeEach(() => {
    queryMock.mockReset()
    __clearRetrievalCache() // query_signals.ts caches by (tool_name, args-hash) — must not bleed across tests
  })

  it('queries asset_throughput scoped to the four spine source assets', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ latest: '2026-07-01T00:00:00.000Z' }] })
    const marker = await getSourceAssetMarker(CHART_B)
    expect(marker).toBe('2026-07-01T00:00:00.000Z')
    const [sql, params] = queryMock.mock.calls[0]
    expect(sql).toContain('asset_throughput')
    expect(params[0]).toBe(CHART_B)
    expect(params[1]).toEqual(['bo_laksana', 'ka_kalasutra', 'ph_nimitta', 'mi_pramana'])
  })
})

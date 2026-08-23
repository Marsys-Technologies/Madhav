/**
 * NIRMĀṆA M0-T34 — D-26 (G-03): deriveState must consult the health detector, not the
 * declared `service` type/kind, and must not preempt the `is_active` check.
 *
 * The defect this file pins down: `deriveState`'s FIRST statement was
 *   `if (asset.asset_type === 'service' || asset.asset_kind === 'service') return 'service_ok'`
 * so (a) a service whose own self-test wrote `service_health = 'unhealthy'` still rendered a
 * green badge — a green OVERRIDING a detector that ran and returned the opposite answer
 * (CHARTER §3 H4, CLAUDE.md §N.8) — and (b) because the branch preceded `is_active`, an
 * INACTIVE service also rendered `service_ok`.
 *
 * What is fixed here is exactly D-26 (2), no more:
 *   - an adverse stored verdict ('unhealthy' / 'degraded') wins over the declared kind;
 *   - the branch no longer preempts `is_active`.
 *
 * What is deliberately NOT decided here is D-26 (3), reserved to M3: what a service with NO
 * detector verdict at all should render, and whether that state satisfies a dependency. Those
 * assets keep rendering `service_ok` — unchanged, not endorsed. Asserting the status quo here
 * is what makes the M3 change visible when it lands; inventing an 'unknown' state now would be
 * pre-building M3 (the D-23 lesson).
 */
import { describe, it, expect } from 'vitest'
import { deriveState } from '../deriveState'
import type { AssetState } from '../deriveState'

describe('deriveState — service health detector (D-26, M0-T34)', () => {
  it('an adverse stored verdict beats the declared service type/kind', () => {
    expect(deriveState({ asset_type: 'service', service_health: 'unhealthy' }, null, null, 'lit')).toBe('service_down')
    expect(deriveState({ asset_kind: 'service', service_health: 'unhealthy' }, null, null, 'lit')).toBe('service_down')
    expect(deriveState({ asset_kind: 'service', service_health: 'degraded' }, null, null, 'lit')).toBe('service_down')
  })

  it('a healthy stored verdict renders service_ok — the detector agrees, so the badge may', () => {
    expect(deriveState({ asset_type: 'service', service_health: 'healthy' }, null, null, 'lit')).toBe('service_ok')
  })

  it('an INACTIVE service renders not_migrated — the service branch no longer preempts is_active', () => {
    expect(deriveState({ is_active: false, asset_type: 'service' }, null, null, 'lit')).toBe('not_migrated')
    expect(deriveState({ is_active: false, asset_kind: 'service', service_health: 'unhealthy' }, null, null, 'lit')).toBe('not_migrated')
  })

  it('M3-DEFERRED (D-26 item 3): a service with no verdict still renders service_ok — status quo, pinned so M3 must change it deliberately', () => {
    expect(deriveState({ asset_type: 'service', service_health: null }, null, null, 'error')).toBe('service_ok')
    expect(deriveState({ asset_kind: 'service' }, null, null, 'stale')).toBe('service_ok')
    // 'unknown' is the registry's own word for "no verdict" (CHECK constraint
    // asset_registry_service_health_check allows healthy|degraded|unhealthy|unknown). It is
    // NOT an adverse verdict, so it is M3's question, not this fix's.
    expect(deriveState({ asset_kind: 'service', service_health: 'unknown' }, null, null, 'lit')).toBe('service_ok')
  })
})

/**
 * Table-drive of the REAL population, measured read-only against production
 * `asset_registry` / `asset_throughput` on 2026-08-23 (chart 482012f1). All eight assets
 * matching deriveState's `asset_type='service' OR asset_kind='service'` predicate.
 *
 * `actual_rows` and `error` are null for every row because the cockpit's own service branch
 * (stats/route.ts fetchAllCounts) never runs count_sql for a service; `throughput_state` is
 * what that route's DISTINCT ON query resolves for chart 482012f1 (chart row first, else the
 * chart_id IS NULL row).
 *
 * Correction to the D-26 evidence line, recorded here because the fix rests on it: the health
 * VERDICT does not live in `health_probe` — that column holds a probe SPECIFICATION. The
 * verdict lives in `service_health`, stamped with `last_selftest_at` + `selftest_detail`. All
 * four assets carrying a non-null `service_health` also carry a real self-test record; the four
 * carrying none have never been probed.
 */
const REAL_ASSETS: Array<{
  asset_id: string
  catalog_status: string
  reg: Parameters<typeof deriveState>[0] & { service_health?: string | null }
  throughput_state: string
  before: AssetState
  after: AssetState
  why: string
}> = [
  {
    asset_id: 'bg_ephemeris_engine', catalog_status: 'CURRENT',
    reg: { is_active: true, asset_type: 'service', asset_kind: 'service', service_health: null, has_substeps: false },
    throughput_state: 'error', before: 'service_ok', after: 'service_ok',
    why: 'No verdict: service_health NULL, last_selftest_at NULL. health_probe holds a probe SPEC, not a result. M3-deferred (D-26 item 3) — unchanged, not endorsed. Its asset_throughput row does carry a stale 2026-06-18 "ephemeris file damaged" last_error, which is a separate signal this fix does not read.',
  },
  {
    asset_id: 'bg_panchanga', catalog_status: 'CURRENT',
    reg: { is_active: true, asset_type: 'service', asset_kind: 'service', service_health: null, has_substeps: false },
    throughput_state: 'lit', before: 'service_ok', after: 'service_ok',
    why: 'No verdict: service_health NULL, last_selftest_at NULL. M3-deferred — unchanged.',
  },
  {
    asset_id: 'ka_dasha_kala', catalog_status: 'DRAFT',
    reg: { is_active: true, asset_type: 'service', asset_kind: 'service', service_health: 'healthy', target_floor: 0, has_substeps: false },
    throughput_state: 'lit', before: 'service_ok', after: 'service_ok',
    why: 'Detector agrees: service_health=healthy, last_selftest_at 2026-08-08, selftest_detail lists 9 dasha systems found. Green is earned.',
  },
  {
    asset_id: 'ka_graha_sancara', catalog_status: 'DRAFT',
    reg: { is_active: true, asset_type: 'service', asset_kind: 'service', service_health: 'unhealthy', has_substeps: false },
    throughput_state: 'lit', before: 'service_ok', after: 'service_down',
    why: 'THE H4. Its own self-test on 2026-08-02 recorded {"check":"ephemeris_computes","passed":false} and wrote service_health=unhealthy. The old code discarded that verdict and rendered green. It now renders service_down.',
  },
  {
    asset_id: 'ka_muhurta_seva', catalog_status: 'DRAFT',
    reg: { is_active: true, asset_type: 'service', asset_kind: 'service', service_health: 'healthy', has_substeps: false },
    throughput_state: 'lit', before: 'service_ok', after: 'service_ok',
    why: 'Detector agrees: self-test 2026-08-02 recorded 8 checks, all PASS (5 FORENSIC anchors among them), "health":"healthy". Green is earned.',
  },
  {
    asset_id: 'ka_tulana', catalog_status: 'DRAFT',
    reg: { is_active: true, asset_type: 'service', asset_kind: 'service', service_health: 'healthy', target_floor: 0, has_substeps: false },
    throughput_state: 'lit', before: 'service_ok', after: 'service_ok',
    why: 'Detector agrees: self-test 2026-08-13, tulana_rank_order. Green is earned.',
  },
  {
    asset_id: 'mi_abhilekha', catalog_status: 'DRAFT',
    reg: { is_active: true, asset_type: 'service', asset_kind: 'service', service_health: null, target_floor: 0, has_substeps: false },
    throughput_state: 'stale', before: 'service_ok', after: 'service_ok',
    why: 'No verdict at all: service_health NULL, health_probe NULL, last_selftest_at NULL. M3-deferred — unchanged.',
  },
  {
    asset_id: 'mi_seva', catalog_status: 'DRAFT',
    reg: { is_active: true, asset_type: 'service', asset_kind: 'service', service_health: null, target_floor: 0, has_substeps: false },
    throughput_state: 'stale', before: 'service_ok', after: 'service_ok',
    why: 'No verdict at all. M3-deferred — unchanged.',
  },
]

describe('deriveState — the eight real service assets (measured 2026-08-23)', () => {
  for (const row of REAL_ASSETS) {
    it(`${row.asset_id} (${row.catalog_status}) renders ${row.after}`, () => {
      expect(deriveState(row.reg, null, null, row.throughput_state)).toBe(row.after)
    })
  }

  it('exactly one of the eight changes rendered state, and it is the one whose detector fired', () => {
    const changed = REAL_ASSETS.filter(r => r.before !== r.after).map(r => r.asset_id)
    expect(changed).toEqual(['ka_graha_sancara'])
  })
})

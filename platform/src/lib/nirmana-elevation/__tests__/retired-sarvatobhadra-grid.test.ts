import { describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

import {
  assertFreezableManifest,
  assertManifestMatchesRegistry,
  nirmanaExecutionContractForRegistryRow,
  type NirmanaRegistryContractRow,
} from '../definitions'
import { buildNirmanaBaselineCandidate } from '../monitor'

/**
 * SS rulings N-430 / N-438 (migration 1360): bg_sarvatobhadra_grid is RETIRED as unbuilt (no writer, no source, nothing inserts into it; the table is kept).
 * Its frozen-denominator state moves from the adjudicated `empty_acceptance` to the SUCCESSOR state `retired_with_disposition` (RETAINED_AS_CAPITAL, no
 * successor asset). These tests fail on the previous definition, which fixed the id as `empty_acceptance` whatever the registry said and required every
 * retired asset to name a successor.
 */
const GRID = 'bg_sarvatobhadra_grid'

function row(asset_id: string, overrides: Partial<NirmanaRegistryContractRow> = {}): NirmanaRegistryContractRow {
  return {
    asset_id, layer: 'brahmagyan', depends_on: [], sort_order: 1, scope: 'global', asset_kind: 'data', catalog_status: 'CURRENT', is_active: true, has_writer: true,
    target_table: `${asset_id}_rows`, count_sql: `SELECT count(*) FROM ${asset_id}_rows`, integrity_check_sql: null, health_probe: null, natural_key_partition: null,
    superseded_by: null, data_disposition: null, dead_flag: null, sanskrit_name: null, english_name: null, english_description: null, ...overrides,
  }
}

/** The grid exactly as seeded by migration 529 (CURRENT, active, no writer). */
const liveGrid = () => row(GRID, { sort_order: 73, has_writer: false, target_table: GRID, count_sql: 'SELECT COUNT(*) FROM bg_sarvatobhadra_grid' })
/** The grid exactly as migration 1360 leaves it. */
const retiredGrid = (over: Partial<NirmanaRegistryContractRow> = {}) => row(GRID, {
  sort_order: 73, has_writer: false, target_table: GRID, count_sql: 'SELECT COUNT(*) FROM bg_sarvatobhadra_grid',
  is_active: false, catalog_status: 'RETIRED', data_disposition: 'RETAINED_AS_CAPITAL', superseded_by: null, ...over,
})
const others = (): NirmanaRegistryContractRow[] => [
  row('bg_reference', { sort_order: 1 }),
  row('ka_gochara_sweep', { layer: 'kala', sort_order: 90, is_active: false, catalog_status: 'RETIRED', superseded_by: 'bg_reference', data_disposition: 'RETAINED_AS_CAPITAL' }),
]
const obligationOf = (rows: NirmanaRegistryContractRow[], id: string) =>
  buildNirmanaBaselineCandidate(rows).manifest.assets.find((a) => a.asset_id === id)?.execution_obligation

describe('bg_sarvatobhadra_grid — successor state RETIRED (N-430 / N-438)', () => {
  it('a RETIRED grid row derives the retired_with_disposition obligation; an un-retired one keeps the adjudicated empty_acceptance', () => {
    expect(nirmanaExecutionContractForRegistryRow(retiredGrid()).execution_obligation).toBe('retired_with_disposition')
    expect(nirmanaExecutionContractForRegistryRow(liveGrid()).execution_obligation).toBe('empty_acceptance')
  })

  it('the baseline candidate keeps the retired grid in the frozen population (a formal disposition, not a silent exclusion) and is freezable without a successor', () => {
    const candidate = buildNirmanaBaselineCandidate([...others(), retiredGrid()])
    const asset = candidate.manifest.assets.find((a) => a.asset_id === GRID)
    expect(asset).toMatchObject({ execution_obligation: 'retired_with_disposition' })
    expect(asset?.registry_contract).toMatchObject({ catalog_status: 'RETIRED', is_active: false, superseded_by: null, data_disposition: 'RETAINED_AS_CAPITAL', has_writer: false })
    expect(() => assertFreezableManifest(candidate.manifest)).not.toThrow()
    expect(obligationOf([...others(), liveGrid()], GRID)).toBe('empty_acceptance')           // the predecessor population still builds
  })

  it('a manifest frozen BEFORE the retirement no longer matches the live registry once the grid is RETIRED (the drift is visible, never silent)', () => {
    const frozenBefore = buildNirmanaBaselineCandidate([...others(), liveGrid()]).manifest
    expect(() => assertManifestMatchesRegistry(frozenBefore, [...others(), liveGrid()])).not.toThrow()
    expect(() => assertManifestMatchesRegistry(frozenBefore, [...others(), retiredGrid()])).toThrow()
    const frozenAfter = buildNirmanaBaselineCandidate([...others(), retiredGrid()]).manifest
    expect(() => assertManifestMatchesRegistry(frozenAfter, [...others(), retiredGrid()])).not.toThrow()
  })

  it('a RETIRED grid cannot be frozen as empty_acceptance, and cannot carry a successor or lack its data disposition', () => {
    const asset = buildNirmanaBaselineCandidate([...others(), retiredGrid()]).manifest.assets.find((a) => a.asset_id === GRID)!
    const withAssets = (a: typeof asset) => ({ ...buildNirmanaBaselineCandidate([...others(), retiredGrid()]).manifest, assets: buildNirmanaBaselineCandidate([...others(), retiredGrid()]).manifest.assets.map((x) => (x.asset_id === GRID ? a : x)) })
    expect(() => assertFreezableManifest(withAssets({ ...asset, execution_obligation: 'empty_acceptance' }))).toThrow(/must retain its adjudicated retired_with_disposition/)
    expect(() => buildNirmanaBaselineCandidate([...others(), retiredGrid({ data_disposition: null })])).toThrow(/missing its successor or data disposition/)
    expect(() => buildNirmanaBaselineCandidate([...others(), retiredGrid({ superseded_by: 'bg_reference' })])).toThrow(/missing its successor or data disposition/)
    expect(() => buildNirmanaBaselineCandidate([...others(), retiredGrid({ is_active: true })])).toThrow(/missing its successor or data disposition/)
  })

  it('the no-successor allowance is the grid only: every other retired asset still has to name its successor', () => {
    const retiredNoSuccessor = row('ka_gochara_sweep', { layer: 'kala', sort_order: 90, is_active: false, catalog_status: 'RETIRED', superseded_by: null, data_disposition: 'RETAINED_AS_CAPITAL' })
    expect(() => buildNirmanaBaselineCandidate([row('bg_reference'), retiredNoSuccessor])).toThrow(/missing its successor or data disposition/)
  })
})

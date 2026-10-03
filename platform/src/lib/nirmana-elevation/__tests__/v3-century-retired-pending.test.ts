import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

import type { NirmanaRegistryContractRow } from '../definitions'
import { buildNirmanaBaselineCandidate } from '../monitor'

/**
 * C33 / Suvarṇa ruling (B.FG) — ka_gochara_v3_century_materialize is a RETIRED-PENDING legacy writer: it retires
 * when '5.0' comes from the registered writer. Until then it holds an audited retired_with_disposition obligation
 * (fixedNonBuildDispositions) so the baseline constructs again — the monitor had been source_unavailable since
 * 2026-09-24 because the CURRENT/inactive/has_writer row fell through to 'unresolved'.
 *
 * The fixture is production's asset_registry read 2026-10-03 with the monitor loader's exact column set
 * (131 rows: the 129 pre-existing + the two staged inert candidates, has_runtime_evidence false for both).
 */
const productionRows = JSON.parse(readFileSync(
  path.join(__dirname, 'fixtures', 'production_asset_registry_2026_10_03.json'), 'utf8'),
) as NirmanaRegistryContractRow[]

const V3 = 'ka_gochara_v3_century_materialize'

describe('retired-pending legacy century writer (B.FG)', () => {
  it('the fixture is production’s 131-row shape, both candidates evidence-free', () => {
    expect(productionRows).toHaveLength(131)
    const v3 = productionRows.find((row) => row.asset_id === V3)
    expect(v3).toMatchObject({ catalog_status: 'CURRENT', is_active: false, has_writer: true })
    for (const id of ['ka_gochara_v4_41_candidate', 'ka_gochara_v5']) {
      expect(productionRows.find((row) => row.asset_id === id)).toMatchObject({ has_runtime_evidence: false })
    }
  })

  it('the baseline CONSTRUCTS with the frozen 128-asset denominator: neither candidate present, the retired-pending writer in the population', () => {
    // 131 rows − 2 staged inert candidates − bo_grounding (D-NATIVE-11 supporting writer) = the frozen 128
    // (hard-asserted by asset_registry_seed_dag_parity.test.ts; Suvarṇa's "127" was one-off arithmetic on the
    // same shape — the denominator is UNCHANGED, which is the ruling's point).
    const candidate = buildNirmanaBaselineCandidate(productionRows)
    const ids = candidate.manifest.assets.map((asset) => asset.asset_id)
    expect(ids).toHaveLength(128)
    expect(ids).not.toContain('ka_gochara_v4_41_candidate')
    expect(ids).not.toContain('ka_gochara_v5')
    const v3 = candidate.manifest.assets.find((asset) => asset.asset_id === V3)
    expect(v3).toMatchObject({ execution_obligation: 'retired_with_disposition' })
  })

  it('mutation: without the audited entry the same row shape throws the original unresolved-obligation error', () => {
    const v3Row = productionRows.find((row) => row.asset_id === V3)
    // identical shape under an unadjudicated id — the audited Map entry is the only thing rescuing this shape
    const mutated = productionRows.map((row) => (row.asset_id === V3 ? { ...v3Row, asset_id: 'ka_gochara_v3_legacy_lookalike' } : row))
    expect(() => buildNirmanaBaselineCandidate(mutated as NirmanaRegistryContractRow[]))
      .toThrow('Frozen manifest asset ka_gochara_v3_legacy_lookalike cannot retain an unresolved execution obligation.')
  })

  it('an ACTIVE v3 row is refused even with the audited entry (retired-pending is not an active-writer disguise)', () => {
    const activated = productionRows.map((row) => (row.asset_id === V3 ? { ...row, is_active: true } : row))
    expect(() => buildNirmanaBaselineCandidate(activated)).toThrow(/Retired asset ka_gochara_v3_century_materialize/)
  })
})

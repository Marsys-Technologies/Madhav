import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

/**
 * Nirmāṇa L1-W3 registry-truth contract (migration 650).
 *
 * This exists because a migration that asserts floors with nothing checking them
 * is a claim with no detector (CLAUDE.md §N.8). The L0 equivalent
 * (`nirmana_l0_achieved_floor_contract.test.ts`) catches exactly one failure
 * mode this one inherits: the migration lands, the from-scratch replay seed does
 * not, and a fresh bootstrap silently produces a different registry from a
 * migrated one.
 *
 * Every number below was measured live across all three built charts on
 * 2026-09-05 (1c826d5a / 482012f1 / cb73cd3d). Evidence:
 * 00_ARCHITECTURE/briefs/nirmana/sessions/L1_W1_ANALYSIS_BATCH_A..E.md;
 * decisions: L1_W2_DECIDE_v1_0.md §3.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/650_nirmana_l1_w3_registry_truth.sql'),
  'utf8',
)

/** asset → [floor, the minimum achieved count it was derived from] */
const ACHIEVED_FLOORS: ReadonlyArray<readonly [string, number]> = [
  ['ga_positions', 1205],
  ['ga_sensitive', 8775],
  ['ga_sensitive_degree', 335],
  ['ga_nakshatra', 1813],
  ['ga_strength', 13621],
  ['ga_structural', 98446],
  ['ga_sade_sati', 6120],
  ['ga_dashas', 471767],
  ['ga_vichara', 8240],
  ['ga_yoga', 63],
  ['ga_ayurdaya', 130],
]

describe('migration 650 — Nirmāṇa L1 registry-truth contract', () => {
  it.each(ACHIEVED_FLOORS)('keeps migration and replay seed aligned for %s', (assetId, floor) => {
    const asset = ASSETS.find((candidate) => candidate.asset_id === assetId)
    expect(asset, `${assetId} missing from the replay seed`).toBeDefined()
    expect(asset?.target_floor).toBe(floor)
    expect(migration).toMatch(
      new RegExp(`SET target_floor = ${floor}\\b[\\s\\S]{0,200}?WHERE asset_id = '${assetId}'`),
    )
  })

  it('counts the three fact_categories that no asset counted before', () => {
    // F-A4 / F-B2 / F-B12: each category is written by its writer AND served,
    // but was absent from every count_sql, so the cockpit under-reported it.
    const positions = ASSETS.find((a) => a.asset_id === 'ga_positions')
    expect(positions?.count_sql).toContain('house_chalit')
    expect(positions?.count_sql).toContain('sandhi_flag')
    expect(migration).toContain('house_chalit')
    expect(migration).toContain('bhava_arudha')
    expect(migration).toContain('sensitive_point_yogi')
  })

  it('leaves depends_on untouched — it is immutable for this campaign cohort', () => {
    // Adjudication #1744: the frozen definition can no longer be superseded
    // (174 events / 11 runs), and the dispatcher rejects any live-vs-frozen
    // depends_on difference. A future edit to this migration that "helpfully"
    // corrects the DAG would make every L1 asset undispatchable.
    expect(migration).not.toMatch(/SET[\s\S]{0,80}depends_on/i)
  })

  it('records ga_prashna dormancy as data, not as a comment', () => {
    // F-E21/F-E23: R-1 was nowhere machine-readable, so a deliberate 0-row
    // outcome was indistinguishable from a broken build.
    expect(migration).toContain("data_disposition = 'RETAINED_AS_CAPITAL'")
    expect(migration).toContain('DORMANT BY DESIGN')
    expect(migration).toContain('R-1')
  })

  it('clears the ga_panchanga formula rather than substituting another one', () => {
    // F-B31 / C12: the count is chart-dependent (417 / 437 / 415), so no
    // fixed-input formula can be correct. A replacement formula would be the
    // "equality wearing a floor's name" defect one level up. The floor is the
    // volume assertion here; the formula is honestly NULL.
    expect(migration).toMatch(
      /expected_volume_formula = NULL[\s\S]{0,1200}?WHERE asset_id = 'ga_panchanga'/,
    )
    const panchanga = ASSETS.find((a) => a.asset_id === 'ga_panchanga')
    expect(panchanga?.expected_volume_formula).toBeNull()
  })

  it('does not set floors for assets whose routed fix can still reduce their count', () => {
    // §N.4: floors come from a measured build. ga_vargas' fix recovers ~15k
    // suppressed rows and ga_condition/ga_tajaka/ga_medical/ga_vastu/
    // ga_transit_anchors all change what they produce, so their floors are set
    // AFTER their W4 build, not guessed now.
    for (const assetId of ['ga_vargas', 'ga_condition', 'ga_tajaka', 'ga_medical', 'ga_transit_anchors']) {
      expect(
        migration,
        `${assetId} floor must not be set before its W4 build`,
      ).not.toMatch(new RegExp(`SET target_floor = \\d+\\s*WHERE asset_id = '${assetId}'`))
    }
  })
})

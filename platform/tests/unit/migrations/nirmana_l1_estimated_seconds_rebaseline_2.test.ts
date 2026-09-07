import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

/**
 * Nirmāṇa L1 estimated_seconds re-baseline, round 2 (migration 879).
 *
 * Closes L1_W6_CLOSE_REPORT_v1_0.md §4's own noted OPEN item (cycle 187): 10 assets'
 * estimated_seconds were stale against live build_run_assets telemetry (1.3x-3.4x drift),
 * continuing migration 847's exact methodology. Two of the ten (ga_vargas, ga_dashas) were
 * explicitly confirmed ACCURATE by migration 847 itself at cycle 110 -- the re-measurement here,
 * ~77 cycles of additional build history later, finds both have genuinely drifted since, not
 * that the earlier finding was wrong.
 *
 * This is a textual contract test (no live DB) -- it exists so a future edit cannot silently
 * revert any of these ten to a stale or fabricated number.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/879_nirmana_l1_estimated_seconds_rebaseline_2.sql'),
  'utf8',
)

const EXPECTED: Record<string, number> = {
  ga_ayurdaya: 9,
  ga_dashas: 1118,
  ga_panchanga: 10,
  ga_sensitive: 407,
  ga_strength: 132,
  ga_vargas: 256,
  ga_tajaka: 19,
  ga_transit_anchors: 2,
  ga_vastu: 2,
  ga_yoga: 10,
}

describe('migration 879 — estimated_seconds re-baseline round 2 (10 assets)', () => {
  for (const [assetId, seconds] of Object.entries(EXPECTED)) {
    it(`sets ${assetId}'s estimated_seconds to ${seconds}, the live re-measured mean`, () => {
      const re = new RegExp(
        `UPDATE asset_registry SET estimated_seconds = ${seconds}\\s+WHERE asset_id = '${assetId}'`,
      )
      expect(migration).toMatch(re)
    })
  }

  it('touches exactly these 10 assets, no more and no fewer', () => {
    const matches = migration.match(/WHERE asset_id = '([a-z_]+)'/g) ?? []
    expect(matches).toHaveLength(Object.keys(EXPECTED).length)
  })

  it('touches ga_vargas and ga_dashas -- both drifted since migration 847 confirmed them accurate', () => {
    const sqlBody = migration.slice(migration.indexOf('BEGIN;'))
    expect(sqlBody).toMatch(/'ga_vargas'/)
    expect(sqlBody).toMatch(/'ga_dashas'/)
  })

  it('touches ONLY estimated_seconds -- no other column assignment', () => {
    const sqlBody = migration.slice(migration.indexOf('BEGIN;'))
    expect(sqlBody).not.toMatch(/SET\s+(?!estimated_seconds\s*=)/i)
  })

  it('cites migration 847 as the precedent methodology', () => {
    expect(migration).toContain('847')
  })

  it('does not touch any asset migration 847 already re-baselined (ga_positions/ga_nakshatra/ga_condition/ga_sade_sati/ga_vichara)', () => {
    const sqlBody = migration.slice(migration.indexOf('BEGIN;'))
    for (const already of ['ga_positions', 'ga_nakshatra', 'ga_condition', 'ga_sade_sati', 'ga_vichara']) {
      expect(sqlBody).not.toMatch(new RegExp(`'${already}'`))
    }
  })
})

import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

/**
 * Nirmāṇa L1 estimated_seconds re-baseline across 5 assets (migration 847, eighth in the
 * 840-859 range).
 *
 * Closes F-A16/F-B22/F-C12/F-D12 (L1_W1_ANALYSIS_BATCH_A/B/C/D.md): five assets'
 * estimated_seconds were declared, never re-measured against build_run_assets history --
 * confirmed live, cycle 110, all five still stale. Re-measured fresh from build_run_assets
 * (not copy-pasted from the original findings' own numbers, which predate ~2 months of
 * additional build history) -- ga_positions' live mean (17.0s, n=54) matches F-A16's own quoted
 * number exactly, confirming the methodology agrees.
 *
 * This is a textual contract test (no live DB) -- it exists so a future edit cannot silently
 * revert any of these five to a stale or fabricated number.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/847_nirmana_l1_estimated_seconds_rebaseline.sql'),
  'utf8',
)

const EXPECTED: Record<string, number> = {
  ga_positions: 17,
  ga_nakshatra: 59,
  ga_condition: 71,
  ga_sade_sati: 142,
  ga_vichara: 307,
}

describe('migration 847 — estimated_seconds re-baseline (5 assets)', () => {
  for (const [assetId, seconds] of Object.entries(EXPECTED)) {
    it(`sets ${assetId}'s estimated_seconds to ${seconds}, the live re-measured mean`, () => {
      const re = new RegExp(
        `UPDATE asset_registry SET estimated_seconds = ${seconds}\\s+WHERE asset_id = '${assetId}'`,
      )
      expect(migration).toMatch(re)
    })
  }

  it('touches exactly these 5 assets, no more and no fewer', () => {
    const matches = migration.match(/WHERE asset_id = '([a-z_]+)'/g) ?? []
    expect(matches).toHaveLength(Object.keys(EXPECTED).length)
  })

  it('does not touch ga_vargas or ga_dashas -- F-A16 confirmed both already accurate', () => {
    const sqlBody = migration.slice(migration.indexOf('BEGIN;'))
    expect(sqlBody).not.toMatch(/'ga_vargas'/)
    expect(sqlBody).not.toMatch(/'ga_dashas'/)
  })

  it('touches ONLY estimated_seconds -- no other column assignment', () => {
    const sqlBody = migration.slice(migration.indexOf('BEGIN;'))
    expect(sqlBody).not.toMatch(/SET\s+(?!estimated_seconds\s*=)/i)
  })

  it('cites F-A16/F-B22/F-C12/F-D12 as the findings this closes', () => {
    for (const id of ['F-A16', 'F-B22', 'F-C12', 'F-D12']) {
      expect(migration).toContain(id)
    }
  })

  it('documents this as the eighth migration in the 840-859 range', () => {
    expect(migration).toContain('840-859')
    expect(migration).toContain('#2101')
  })
})

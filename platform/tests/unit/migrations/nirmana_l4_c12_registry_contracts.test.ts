/**
 * NIRMĀṆA v2.1 · L4 · migration 681 — the C12 registry delta for all nine phala assets.
 *
 * The migration proves itself at deploy time: it executes every installed detector and
 * refuses to install one that is already red, and it refuses to leave any L4 asset with a
 * NULL volume expectation. This suite guards the parts a later edit could weaken without
 * any live assertion noticing — above all C12's ban on bare equality pins.
 */
import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/681_l4_phala_c12_registry_contracts.sql'),
  'utf8',
)

const L4_ASSETS = [
  'ph_nimitta', 'ph_muhurta', 'ph_sankrama', 'ph_sodhana', 'ph_suddha_sodhana',
  'ph_pratikara', 'ph_pramana', 'ph_phaladesa', 'ph_rectification',
] as const

describe('migration 681 — every L4 asset gets a real contract', () => {
  it.each(L4_ASSETS)('sets a volume expectation for %s', (assetId) => {
    expect(migration).toMatch(new RegExp(`expected_volume_formula[\\s\\S]*?WHERE asset_id = '${assetId}'`))
    expect(migration).toMatch(new RegExp(`expected_volume_inputs[\\s\\S]*?WHERE asset_id = '${assetId}'`))
  })

  it('refuses to install a detector that is already red', () => {
    expect(migration).toContain('integrity detector is RED on current data -- refusing to install it')
  })

  it('refuses to leave any asset without a detector or a volume expectation', () => {
    expect(migration).toContain('still has no integrity_check_sql (C12: NULL is the defect)')
    expect(migration).toContain('still has a NULL expected_volume_formula/inputs')
  })
})

describe('migration 681 — C12: no bare equality pin may serve as a volume assertion', () => {
  it('contains no `count(*) = <literal>` volume pin in any installed detector', () => {
    // "An equality wearing a floor's name" (M0-T86 / D-126). Equalities against a LIVE
    // upstream count are fine and are used; equalities against a hardcoded number are not.
    const checks = migration.match(/\$check\$[\s\S]*?\$check\$/g) ?? []
    expect(checks.length).toBeGreaterThanOrEqual(8)
    for (const check of checks) {
      expect(check).not.toMatch(/count\(\*\)\s*=\s*\d+/)
    }
  })

  it('uses cross-table tiling, re-derivation and drift checks rather than row counts', () => {
    expect(migration).toContain('FULL OUTER JOIN')
    expect(migration).toContain('IS DISTINCT FROM')
  })
})

describe('migration 681 — floors are honest, not decorative (§N.4)', () => {
  it('gives ph_sodhana a ceiling and deliberately NO floor', () => {
    // An anomaly registry: a floor would reward fabricating findings.
    expect(migration).toMatch(/target_floor = NULL[\s\S]*?WHERE asset_id = 'ph_sodhana'/)
    expect(migration).toContain('rows BETWEEN 0 AND (5 * anchor_count) + 1')
  })

  it('leaves ph_pramana without a floor while its detector is known dead', () => {
    expect(migration).toMatch(/target_floor = NULL[\s\S]*?WHERE asset_id = 'ph_pramana'/)
    expect(migration).toMatch(/floor now would enshrine a count a dead detector produced/i)
  })

  it('keeps ph_pratikara DRAFT while its rows are provably empty', () => {
    const block = migration.slice(
      migration.indexOf("-- ── ph_pratikara"),
      migration.indexOf("-- ── ph_pramana"),
    )
    expect(block).not.toContain("catalog_status = 'CURRENT'")
  })
})

describe('migration 681 — the withheld invariants are named, not silently absent', () => {
  it.each([
    ['ph_pramana', 'life_event_miss'],
    ['ph_rectification', 'load_bearing'],
    ['ph_sankrama', 'transition'],
  ])('records the open defect %s leaves undetected for now', (_assetId, marker) => {
    expect(migration).toContain(marker)
  })

  it('states the partitioning rather than letting the detectors read as chart-scoped', () => {
    const occurrences = migration.match(/chart-PARTITIONED/g) ?? []
    expect(occurrences.length).toBeGreaterThanOrEqual(8)
  })
})

describe('migration 681 — D-CND-03: detectors partition on chart, they do not aggregate', () => {
  const checks = migration.match(/\$check\$[\s\S]*?\$check\$/g) ?? []

  it('installs a detector for each of the eight assets it owns', () => {
    expect(checks.length).toBe(8)
  })

  it('expresses every clause as NOT EXISTS rather than a bare count comparison', () => {
    // A whole-table aggregate can be dominated by another chart's rows and miss a
    // single-chart corruption. Demonstrated live: deleting one domain row for one chart
    // makes the partitioned form read false while `count(*) >= 13` still reads true.
    for (const check of checks) {
      expect(check).toContain('NOT EXISTS')
    }
  })

  it('partitions on chart_id in every top-level clause but the one documented exception', () => {
    // Count TOP-LEVEL clauses only (line-anchored). A correlated NOT EXISTS nested inside a
    // partitioned clause is part of that clause's predicate, not a clause of its own.
    let topLevel = 0
    let partitioned = 0
    let schemaExceptions = 0
    for (const check of checks) {
      for (const line of check.split('\n')) {
        if (/^\s{2}(AND\s+)?NOT EXISTS/.test(line)) topLevel += 1
      }
      partitioned += (check.match(/GROUP BY[^\n]*chart_id/gi) ?? []).length
      schemaExceptions += (check.match(/FROM information_schema\.columns/g) ?? []).length
    }
    expect(topLevel).toBeGreaterThanOrEqual(18)
    expect(schemaExceptions).toBe(1)          // exactly one documented exception, layer-wide
    expect(partitioned).toBe(topLevel - schemaExceptions)
  })

  it('documents the one non-partitionable clause instead of defaulting to it', () => {
    expect(migration).toContain('NOT CHART-PARTITIONABLE')
    expect(migration).toContain('information_schema has no chart_id to partition on')
  })
})

describe('migration 681 — depends_on is immutable this campaign (#1744)', () => {
  it('never touches depends_on or layer', () => {
    expect(migration).not.toMatch(/SET[\s\S]{0,400}depends_on\s*=/)
    expect(migration).not.toMatch(/SET[\s\S]{0,400}\blayer\s*=/)
  })
})

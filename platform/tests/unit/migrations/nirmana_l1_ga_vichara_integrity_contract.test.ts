import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_vichara integrity contract (migration 747, F-A14).
 *
 * ga_vichara's integrity_check_sql was NULL (unearned count(*)>0 fallback, §N.8). This textual
 * test verifies the migration's SHAPE -- the four documented conjuncts survive, the contract is
 * read-only and bind-parameter-free per the real elevation-pipeline validator, and conjunct (d)'s
 * family scope matches what was measured live (valence_pass only) -- not a live-DB re-run of the
 * contract itself, which was verified and mutation-tested live against production during
 * authoring.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/747_nirmana_l1_ga_vichara_integrity_contract.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 747')
  }
  return migration.slice(start + 4, end)
}

describe('migration 747 — ga_vichara integrity_check_sql', () => {
  it('targets ga_vichara by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_vichara';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries all four documented conjuncts', () => {
    expect(migration).toMatch(/-- \(a\) constituent_fact_ids must resolve/)
    expect(migration).toMatch(/-- \(b\) constituent_facts_array must resolve/)
    expect(migration).toMatch(/-- \(c\) varga \/ varga_id dual-column consistency/)
    expect(migration).toMatch(/-- \(d\) valence_pass family: actor must equal subject/)
  })

  it('both orphan conjuncts check against chart_facts.fact_id via unnest, not a restated count', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain('unnest(v.constituent_fact_ids)')
    expect(detectorSql).toContain('unnest(v.constituent_facts_array)')
    expect((detectorSql.match(/f\.fact_id = fid/g) || []).length).toBe(2)
  })

  it('conjunct (d) is scoped to valence_pass only, not applied to every family', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain("vichara_family = 'valence_pass' AND actor IS DISTINCT FROM subject")
  })

  it('does not assert a dedup-style distinctness conjunct — no natural-key UNIQUE exists on this table', () => {
    // "IS DISTINCT FROM" (used legitimately in conjuncts (c)/(d)) is a comparison operator,
    // not a dedup assertion — this checks for the latter specifically, not the substring.
    const codeOnly = extractDetectorSql()
      .split('\n')
      .map((line) => line.replace(/--.*$/, ''))
      .join('\n')
    expect(codeOnly).not.toMatch(/\bSELECT\s+DISTINCT\b/i)
    expect(codeOnly).not.toMatch(/\bGROUP BY\b/i)
  })
})

import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Migration 1222 -- ga_vargas integrity_check_sql gains a NON-VACUITY conjunct (F-A2, Q-L1-01).
 *
 * Static shape test (the behaviour -- empty / short / complete data, the migration applying once -- is
 * proved against a disposable PostgreSQL by python-sidecar/ga_writers/__tests__/
 * test_ga_vargas_integrity_nonvacuity_and_acceptance.py). Here: the migration is a routine, guarded,
 * asset_registry-only UPDATE, and the new detector SQL still passes the REAL elevation-pipeline validators
 * (read-only, no bind placeholder), because the freeze-time integrity_verified detector runs it standalone.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/1222_nirmana_l1_ga_vargas_integrity_nonvacuity.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 1222')
  }
  return migration.slice(start + 4, end)
}

describe('migration 1222 -- ga_vargas integrity_check_sql non-vacuity', () => {
  it('is a guarded one-row UPDATE of asset_registry, with no transaction control and no DDL', () => {
    expect(migration).toMatch(/UPDATE asset_registry\s+SET integrity_check_sql = \$ck\$/)
    expect(migration).toMatch(/WHERE asset_id = 'ga_vargas';/)
    expect(migration.match(/UPDATE asset_registry/g)).toHaveLength(1)
    expect(migration).toMatch(/SET LOCAL lock_timeout = '5s'/)
    expect(migration).toMatch(/\$pre\$/)
    expect(migration).toMatch(/\$post\$/)
    expect(migration).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/im)
    const outsideDetector = migration.slice(0, migration.indexOf('$ck$')) + migration.slice(migration.lastIndexOf('$ck$'))
    expect(outsideDetector.replace(/--[^\n]*/g, '')).not.toMatch(/\b(ALTER|CREATE|DROP|GRANT|REVOKE|TRUNCATE|DELETE)\b/i)
  })

  it('the detector is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('keeps conjuncts (a)-(d) and adds (e) non-vacuity; the key-grain numbers are NOT in the check', () => {
    const sql = extractDetectorSql()
    expect(sql).toMatch(/-- \(a\) sign \/ sign_number internal consistency/)
    expect(sql).toMatch(/-- \(b\) vargottama correctness/)
    expect(sql).toMatch(/-- \(c\) §N\.5 D1 authority/)
    expect(sql).toMatch(/-- \(d\) identity range guard/)
    expect(sql).toMatch(/-- \(e\) NON-VACUITY/)
    expect(sql).not.toMatch(/\(f\)/)
    expect(sql).not.toMatch(/<>\s*(12|96|60)\b/)
    expect(sql).toMatch(/< 9/)
    expect(sql.trimEnd().endsWith('AS integrity_passed')).toBe(true)
  })

  it('scopes (e) to the canonical chart and the five declared ayanamshas x thirty declared vargas', () => {
    const sql = extractDetectorSql()
    expect(sql).toContain("cd.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'")
    for (const aya of ['lahiri_chitrapaksha', 'true_chitra', 'krishnamurti', 'raman', 'surya_siddhanta_classical']) {
      expect(sql).toContain(`'${aya}'`)
    }
    for (const v of ['D1', 'D9', 'D30', 'D60', 'D108', 'D150', 'D2700']) {
      expect(sql).toContain(`'${v}'`)
    }
  })
})

import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Migration 1252 -- ga_medical integrity_check_sql accepts the NEW band cuts of the band lane (#2890),
 * scoped to the canonical chart.
 *
 * Static shape test (the behaviour -- the real trigger staling ga_medical on every chart, the md5 guards, the
 * idempotent re-run, the four-state proof, the six mutations, the window apply order -- is proved against a
 * disposable PostgreSQL by python-sidecar/tests/test_migration_1252_ga_medical_band_scope.py). Here: the migration
 * is a routine, guarded, asset_registry-only UPDATE of ga_medical only, and the new detector SQL still passes
 * the REAL elevation-pipeline validators (read-only, no bind placeholder), because the freeze-time
 * integrity_verified detector runs it standalone. HELD: merges only in the S-L1 window W1 (see the file header).
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/1252_nirmana_l1_ga_medical_integrity_band_cut_canonical_scope.sql'),
  'utf8',
)
const BASE_MD5 = '0b5d65e4933f10ec95b2db2e7d82289d'
const TARGET_MD5 = 'ae453edf2afeeaba086a444c66681676'
const CANON = '482012f1-710e-4a25-994a-93821f5871aa'

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 1252')
  }
  return migration.slice(start + 4, end)
}

const executable = (s: string) => s.split('\n').filter((l) => !l.trimStart().startsWith('--')).join('\n')

describe('migration 1252 -- ga_medical integrity_check_sql, new band cuts, canonical scope', () => {
  it('is a guarded one-row UPDATE of ga_medical only, with no transaction control and no DDL', () => {
    expect(migration).toMatch(/UPDATE asset_registry\s+SET integrity_check_sql = \$ck\$/)
    expect(migration).toMatch(new RegExp(`WHERE asset_id = 'ga_medical'\\n  AND md5\\(integrity_check_sql\\) = '${BASE_MD5}';`))
    const code = executable(migration)
    expect(code.match(/UPDATE asset_registry/g)).toHaveLength(1)
    expect(code).not.toContain('ga_vastu')
    expect(migration).toMatch(/\$pre\$/)
    expect(migration).toMatch(/\$post\$/)
    expect(migration).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/im)
    const outsideDetector = migration.slice(0, migration.indexOf('$ck$')) + migration.slice(migration.lastIndexOf('$ck$'))
    expect(outsideDetector.replace(/--[^\n]*/g, '')).not.toMatch(/\b(ALTER|CREATE|DROP|GRANT|REVOKE|TRUNCATE|DELETE)\b/i)
  })

  it('starts with lock_timeout, accepts only the base or the target text, and states ordering + serving effect', () => {
    const code = executable(migration)
    expect(code.trim().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
    expect(code).toContain(`'${BASE_MD5}'`)
    expect(code).toContain(`'${TARGET_MD5}'`)
    for (const needle of ['SERVING EFFECT AT APPLY', 'nirmana_registry_receipt_invalidation', 'ON EVERY CHART',
      'ORDERING', 'EXPECTED STATE AT APPLY', 'FALSE (expected)', 'IDEMPOTENT SHAPE',
      'VERIFICATION BY PRODUCTION STRUCTURE', 'HELD', 'WHY THE CLAUSE IS CANONICAL-SCOPED', 'N-78',
      'WIDENING (b) BACK TO TABLE-WIDE IS AN S-L1b TASK', 'WHY ga_vastu IS NOT TOUCHED']) {
      expect(migration.toUpperCase()).toContain(needle.toUpperCase())
    }
  })

  it('the detector is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('applies the new cut (< 0.7), scopes clause (b) to the canonical chart, and pins Saturn to moderate', () => {
    const sql = extractDetectorSql()
    expect(sql).toContain("WHEN c.condition_score < 0.4 THEN 'strong'")
    expect(sql).toContain("WHEN c.condition_score < 0.7 THEN 'moderate'")
    expect(sql).not.toContain('<= 0.6')
    expect(sql).toContain(`WHERE m.chart_id = '${CANON}'\n      AND NOT EXISTS (`)
    expect(sql).toContain("graha = 'Saturn' AND indication_strength <> 'moderate'")
    expect(sql).not.toContain("indication_strength <> 'mild'")
    expect(sql).toContain("graha = 'Sun' AND indication_strength <> 'strong'")
    expect(sql).toContain("SELECT 1 FROM ga_medical WHERE indication_tier <> 'jyotish_indication'")
    expect(sql).toContain('SELECT 1 FROM ga_medical WHERE not_diagnosis IS DISTINCT FROM true')
    expect(sql.trimEnd().endsWith('AS integrity_passed')).toBe(true)
  })

  it('the new clause has exactly the declared scope literal count (b + Saturn + Sun) and nothing table-wide for (b)', () => {
    const code = executable(extractDetectorSql())
    expect(code.split(`'${CANON}'`).length - 1).toBe(3)
    expect(code).not.toMatch(/FROM ga_medical m\s+WHERE NOT EXISTS/)
  })
})

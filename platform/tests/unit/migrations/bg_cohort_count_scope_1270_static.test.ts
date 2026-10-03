/**
 * Suvarna / migration 1270 (TI-L0-30) - STATIC contract: bg_cohort count_sql scoped to the primary table and
 * target_floor 110000 -> 10000 (SS Q19).
 *
 * The live proof (disposable PostgreSQL 15 and 17 as a NOSUPERUSER NOINHERIT amjis_app with USAGE but no CREATE on
 * schema public: apply, exactly two cells, multi-table declaration untouched, trigger staleness, the REAL
 * deps_unsatisfied gate now reading 'bg_cohort(receipt:stale)' for ka_kshetra (the documented serving effect),
 * idempotent re-run, 6 drift cases incl. a half-applied state, absent row, silent-no-op and 15 mutants) is
 * python-sidecar/tests/test_migration_1270_bg_cohort_count_scope.py. This file pins the text.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1270_bg_cohort_count_scope.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')

describe('migration 1270 - static contract', () => {
  it('changes exactly two cells of one row: count_sql scoped to the primary table, target_floor 10000', () => {
    expect(CODE.match(/\bUPDATE asset_registry\b/g)).toHaveLength(1)
    expect(CODE).toContain('SET count_sql = new_count_sql, target_floor = 10000')
    expect(CODE).toContain("new_count_sql constant text := 'SELECT COUNT(*) FROM bg_synthetic_cohort';")
    expect(CODE).toContain("WHERE asset_id = 'bg_cohort' AND count_sql = old_count_sql AND target_floor = 110000")
    const ids = new Set([...CODE.matchAll(/'((?:bg|ga|bo|ka|ph|mi)_[a-z_0-9]+)'/g)].map(m => m[1]))
    expect([...ids].sort()).toEqual(['bg_cohort', 'bg_synthetic_cohort']) // the asset and its primary table; the child table appears only inside the audited literal
    // the child table is never written, and the multi-table declaration / integrity check are not touched
    expect(CODE).not.toMatch(/natural_key_partition|integrity_check_sql|volume_explanation|depends_on/)
  })

  it('is guarded on the audited live values', () => {
    expect(CODE).toContain("'SELECT (SELECT COUNT(*) FROM bg_synthetic_cohort) + (SELECT COUNT(*) FROM bg_synthetic_cohort_md) AS count'")
    expect(CODE).toContain('d8f9f0bfe7b996e5fd829bc3f5347632')
    expect(CODE).toContain('v_floor IS DISTINCT FROM 110000')
    expect(CODE).toContain("v_target IS DISTINCT FROM 'bg_synthetic_cohort'")
    expect(CODE.match(/has drifted from the audited state/g)).toHaveLength(2)
    expect(CODE).toContain('FOR UPDATE')
    expect(CODE).toContain('GET DIAGNOSTICS v_rows = ROW_COUNT')
    expect(CODE).toContain('after the update')
  })

  it('is registry-row DML only: no CREATE/ALTER/DROP/GRANT/REVOKE/INSERT/DELETE', () => {
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE)\b/im)
    expect(CODE).not.toMatch(/\bINSERT INTO\b|\bDELETE FROM\b|SECURITY DEFINER|\bCREATE\b/i)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/m)
  })

  it('starts with the transaction-local 5s lock_timeout', () => {
    expect(CODE.match(/\bSET LOCAL lock_timeout\b/g)).toHaveLength(1)
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
  })

  it('states the header facts: concern, what stays true, the ka_kshetra gate effect, staleness, NOT done', () => {
    for (const needle of ['TI-L0-30', 'WHAT STAYS TRUE', 'natural_key_partition', 'integrity_check_sql',
      'Assets that go stale: bg_cohort ONLY', 'ka_kshetra', 'bg_cohort(receipt:stale)', 'deps_unsatisfied',
      'NOT DONE HERE', 'asset_registry_seed.ts', 'PRIVILEGE', 'IDEMPOTENT', 'writers/bg_cohort.py:525-575']) expect(SQL).toContain(needle)
  })

  it('is a ROUTINE migration (not protected), unique, in the 1200-1299 range, and its number is 1270', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    expect(Number(FILE.slice(0, 4))).toBe(1270)
    expect(fs.readdirSync(MIG).filter(f => /^1270_/.test(f) && f !== FILE)).toEqual([])
  })
})

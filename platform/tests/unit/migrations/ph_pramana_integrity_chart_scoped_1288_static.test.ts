/**
 * Suvarna / migration 1288 — STATIC contract (ph_pramana integrity_check_sql made chart-scoped; the scope is read from the orchestrator's committed
 * state because the check is executed unbound). The live proof (disposable PG 15 and 17, run as amjis_app on the W1 production roles and schema ACL,
 * the check executed the way the orchestrator executes it, today / after the #3072 delete / after a rebuild, inside and outside a build, corruption in
 * the chart being built vs the other chart, zombie and planned runs, 22 mutants) is
 * python-sidecar/tests/test_migration_1288_ph_pramana_integrity_chart_scoped.py.
 */
import { describe, it, expect } from 'vitest'
import crypto from 'crypto'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1288_ph_pramana_integrity_check_chart_scoped.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const FLAT = SQL.replace(/^--/gm, ' ').replace(/\s+/g, ' ')
const md5 = (s: string): string => crypto.createHash('md5').update(s).digest('hex')
const OLD_MD5 = '45f89d4853b157e22507ffccdb9af0e0'
const NEW_MD5 = 'c3f1b7949ebfda27ab959e55c2a14898'
const m681 = fs.readFileSync(path.join(MIG, '681_l4_phala_c12_registry_contracts.sql'), 'utf8')
const oldText = [...m681.matchAll(/\$check\$([\s\S]*?)\$check\$/g)].map(m => m[1] ?? '').find(t => md5(t) === OLD_MD5) ?? ''
const newText = /\$ck\$([\s\S]*)\$ck\$/.exec(SQL)?.[1] ?? ''

describe('migration 1288 — static contract', () => {
  it('the OLD text is migration 681 ph_pramana check and the live production md5', () => {
    expect(md5(oldText)).toBe(OLD_MD5)
    expect(oldText).toHaveLength(1284)
  })

  it('the NEW text has the named md5/length, no bind placeholder, and the scope read from running/building state', () => {
    expect(md5(newText)).toBe(NEW_MD5)
    expect(newText).toHaveLength(3398)
    expect(crypto.createHash('sha256').update(newText).digest('hex')).toBe('040cf925736b063b41b894812835d6c97fcc0083544c899efa2978020f46267f')
    expect(newText.split('AND txid_current_if_assigned() IS NOT NULL')).toHaveLength(5)
    expect(newText).not.toContain('xmin')
    expect(newText).not.toContain('$1')
    expect(newText.split("b.asset_id = 'ph_pramana' AND b.state = 'building' AND r.state = 'running'")).toHaveLength(3)
    expect(newText).toContain('information_schema.columns')
  })

  it('is ONE md5-guarded UPDATE of ONE column of ONE row; creates nothing; no other statement type', () => {
    expect(CODE.match(/\bUPDATE asset_registry\b/g)).toHaveLength(1)
    expect(CODE).toContain(`WHERE asset_id = 'ph_pramana'\n  AND md5(integrity_check_sql) = '${OLD_MD5}';`)
    expect(CODE.split(OLD_MD5)).toHaveLength(3)
    expect(CODE.split(NEW_MD5)).toHaveLength(3)
    const outside = CODE.replace(/\$ck\$[\s\S]*?\$ck\$/, '').replace('CREATE TEMP TABLE _m1288_before ON COMMIT DROP AS', '')
    expect(outside).not.toMatch(/\b(INSERT INTO|DELETE FROM|TRUNCATE|GRANT|REVOKE|ALTER\s|DROP\s)|CREATE\s+(OR\s+REPLACE\s+)?(VIEW|FUNCTION|TABLE|INDEX|TRIGGER|SCHEMA)/)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/m)
  })

  it('has lock_timeout first, the active-run guard on planned/running/paused x queued/building, pre-check and asserting post-check', () => {
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
    for (const n of ["r.state IN ('planned', 'running', 'paused') AND b.state IN ('queued', 'building')", 'active build run(s)', '$pre$', '$post$',
      'is not the text this migration was written against', 'did not take', 'another column of the ph_pramana registry row changed',
      'is not the chart-scoped text']) expect(CODE).toContain(n)
  })

  it('states the header facts: the problem, the unbound execution, readbacks, serving effect, zombies, limits, not-done', () => {
    for (const n of ['THE PROBLEM', 'REVIEW_3072.md MED-1', 'HOW THE ORCHESTRATOR BINDS A CHART: IT DOES NOT', 'cur.execute(integrity_sql)', 'FROZEN',
      'read-only session', 'txid_current_if_assigned() IS NOT NULL', 'LOST DETECTION', 'PRE-WRITE state', 'NEVER RUN TWO ph_pramana BUILDS CONCURRENTLY', 'LIST FOREIGN build_runs', 'RE-COUPLE THE CHARTS', 'READBACKS', 'after the #3072 delete', 'SERVING / FRESHNESS EFFECT AT APPLY', 'asset_freshness holds 0 rows for ph_pramana',
      'ACTIVE RUNS (ENFORCED)', 'Zombie rows', 'KNOWN LIMITS', 'NOT DONE HERE', 'VERIFICATION BY PRODUCTION STRUCTURE', 'ROLLBACK', OLD_MD5, NEW_MD5]) expect(FLAT).toContain(n)
  })

  it('is a ROUTINE migration (not protected), unique, in the 1200-1299 range', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    const n = Number(FILE.slice(0, 4))
    expect(n).toBeGreaterThanOrEqual(1200)
    expect(n).toBeLessThanOrEqual(1299)
    expect(fs.readdirSync(MIG).filter(f => /^1288_/.test(f) && f !== FILE)).toEqual([])
  })
})

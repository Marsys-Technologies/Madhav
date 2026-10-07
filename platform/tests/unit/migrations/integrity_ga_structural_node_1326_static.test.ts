/**
 * Suvarna routine migration 1326 — STATIC contract (ga_structural's integrity_check_sql conjunct (b4) gets a NODE exclusion
 * (fact_subject RAH_MEAN / KET_MEAN) on its retrograde composite downgrade; every other conjunct and line byte-identical).
 * The live proof (a disposable PostgreSQL cluster, synthetic chart_facts rows, the FULL 208 KB registry SQL: nodes neutral with
 * retrograde flag PASS under NEW and FAIL under OLD, a retrograde tara graha not downgraded still FAILS, mutants still caught,
 * apply/guard/idempotency/serving effect/silent-no-op) is
 * python-sidecar/tests/test_migration_1326_ga_structural_node_integrity.py. This file pins the text so a drive-by edit (a widened
 * exclusion, a different target, a dropped guard) is a deliberate, reviewed change.
 */
import { describe, it, expect } from 'vitest'
import crypto from 'crypto'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1326_ga_structural_integrity_node_composite_exclusion.sql'
const FIXTURE = path.resolve(
  __dirname,
  '../../../python-sidecar/tests/fixtures/ga_structural_1326/live_integrity_check_sql_pre1326_2026-10-07.sql',
)
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const FLAT = SQL.replace(/^--/gm, ' ').replace(/\s+/g, ' ')
const md5 = (s: string): string => crypto.createHash('md5').update(s, 'utf8').digest('hex')

const OLD_MD5 = 'c56f9e12b2002269eb5f27a7abc42105'
const NEW_MD5 = 'fcd217e25127653ee28ad41c629946aa'
const OLD_LINE = "          WHEN re.retrograde_flag = 'retrograde' THEN 'weak'\n"
const NEW_BLOCK =
  '          -- Migration 1326 (node exclusion): the mean nodes Rahu/Ketu are always retrograde and ga_positions stores\n' +
  "          -- retrograde_flag 'retrograde' for them (N-185/N-187), but the retrograde composite downgrade does NOT apply to the\n" +
  "          -- nodes (their re_dignity is always 'neutral'); a node row therefore stays 'neutral'. Tara grahas are unchanged.\n" +
  "          WHEN re.retrograde_flag = 'retrograde' AND a.fact_subject NOT IN ('RAH_MEAN', 'KET_MEAN') THEN 'weak'\n"

// The fixture IS the live text (read 2026-10-07 as suvarna_reader), byte for byte.
const OLD = fs.readFileSync(FIXTURE, 'utf8')
const NEW = OLD.replace(OLD_LINE, () => NEW_BLOCK)

describe('migration 1326 — static contract', () => {
  it('pins the live OLD text (md5 and length read from production 2026-10-07)', () => {
    expect(md5(OLD)).toBe(OLD_MD5)
    expect(OLD).toHaveLength(207959)
  })

  it('NEW = OLD with exactly the one retrograde line replaced; it hashes to the md5 the migration names', () => {
    expect(OLD.split(OLD_LINE)).toHaveLength(2)
    expect(OLD.split("re.retrograde_flag = 'retrograde'")).toHaveLength(2)
    expect(NEW).not.toBe(OLD)
    expect(md5(NEW)).toBe(NEW_MD5)
    expect(NEW).toHaveLength(208378)
    const o = OLD.split('\n')
    const n = NEW.split('\n')
    const i = o.indexOf(OLD_LINE.replace(/\n$/, ''))
    expect(n.length).toBe(o.length + 3)
    expect(n.slice(0, i)).toEqual(o.slice(0, i))
    expect(n.slice(i + 4)).toEqual(o.slice(i + 1))
  })

  it('the migration carries exactly those two literals and both md5s', () => {
    expect(/\$ol\$([\s\S]*?)\$ol\$/.exec(SQL)?.[1]).toBe(OLD_LINE)
    expect(/\$nl\$([\s\S]*?)\$nl\$/.exec(SQL)?.[1]).toBe(NEW_BLOCK)
    expect(SQL).toContain(`c_old_md5  constant text := '${OLD_MD5}'`)
    expect(SQL).toContain(`c_new_md5  constant text := '${NEW_MD5}'`)
  })

  it('excludes ONLY the two mean-node subjects; the exclusion appears once and nowhere else in the text', () => {
    expect(NEW.split("NOT IN ('RAH_MEAN', 'KET_MEAN')")).toHaveLength(2)
    expect(OLD).not.toContain("NOT IN ('RAH_MEAN', 'KET_MEAN')")
    expect(NEW_BLOCK).toContain("a.fact_subject NOT IN ('RAH_MEAN', 'KET_MEAN')")
    expect(NEW_BLOCK).not.toMatch(/'(SUN|MOON|MAR|MER|JUP|VEN|SAT)'/)
  })

  it('is ONE md5-guarded UPDATE of one column of the ga_structural row; no DDL, no transaction control', () => {
    expect(CODE.match(/\bUPDATE asset_registry\b/g)).toHaveLength(1)
    expect(CODE).toContain("WHERE asset_id = 'ga_structural'\n     AND md5(integrity_check_sql) = c_old_md5;")
    expect(CODE.match(/\bSET (?:LOCAL )?[a-z_]+ =/g)).toEqual(['SET LOCAL lock_timeout =', 'SET integrity_check_sql ='])
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/m)
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|INSERT|DELETE)\b/im)
    expect(CODE).toContain('replace(integrity_check_sql, c_old_line, c_new_line)')
  })

  it('starts with lock_timeout, NOTICEs (never raises) on a foreign text, raises only when the update did not take', () => {
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
    expect(CODE.match(/\bSET LOCAL lock_timeout\b/g)).toHaveLength(1)
    expect(CODE).toContain('is not the text this migration was written against')
    expect(CODE).toContain('NO-OP')
    expect(CODE).toContain('already carries the node exclusion')
    expect(CODE.match(/RAISE EXCEPTION/g)).toHaveLength(1)
    expect(CODE).toContain('update did not take')
  })

  it('states the header facts: defect, change, audit of other conjuncts, guard, staling trigger effect, verification, rollback', () => {
    for (const n of ['THE DEFECT', 'THE CHANGE', 'OTHER RETROGRADE-CONDITIONAL CONJUNCTS', '(c7)', 'BYTE-IDENTICAL',
      'GUARD AND WHAT HAPPENS WHEN IT DOES NOT MATCH', 'SERVING EFFECT AT APPLY', 'nirmana_registry_receipt_invalidation',
      "STALES ga_structural's freshness rows", 'VERIFICATION BY PRODUCTION STRUCTURE', 'ROLLBACK', OLD_MD5, NEW_MD5]) {
      expect(FLAT).toContain(n)
    }
  })

  it('is a ROUTINE migration (not protected), unique, in the 1320-1329 claimed block', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    const n = Number(FILE.slice(0, 4))
    expect(n).toBeGreaterThanOrEqual(1320)
    expect(n).toBeLessThanOrEqual(1329)
    expect(fs.readdirSync(MIG).filter(f => /^1326_/.test(f) && f !== FILE)).toEqual([])
  })
})

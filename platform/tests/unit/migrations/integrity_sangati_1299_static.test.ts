/**
 * Suvarna S-L2 / migration 1299 — STATIC contract (bo_sangati's integrity_check_sql conjunct 3 is replaced by the relation that
 * actually holds: both counts >= 0 and (shared_signal_count > 0) = (shared_factor_count > 0); every other conjunct byte-identical).
 * The live proof (a disposable PostgreSQL cluster with synthetic bodha_cdlm_cells rows: equal counts, unequal counts both > 0,
 * signal>0 with factor=0, signal=0 with factor>0, negatives, the other conjuncts still biting, apply/guard/idempotency/serving
 * effect/silent-no-op) is python-sidecar/tests/test_migration_1299_bo_sangati_integrity_conjunct3.py. This file pins the text so a
 * drive-by edit (a widened conjunct, a different target, a dropped guard) is a deliberate, reviewed change.
 */
import { describe, it, expect } from 'vitest'
import crypto from 'crypto'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1299_bo_sangati_integrity_conjunct3_invariant.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const FLAT = SQL.replace(/^--/gm, ' ').replace(/\s+/g, ' ')
const md5 = (s: string): string => crypto.createHash('md5').update(s).digest('hex')
const ic = (s: string): string => /\$ic\$([\s\S]*?)\$ic\$/.exec(s)?.[1] ?? ''

const OLD_MD5 = '0fb89ae68f370d02bada11f492f662f7'
const NEW_MD5 = '222188fd9a48644176f34311fd3ea5f6'
const OLD_C3 = `  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_cells WHERE shared_signal_count != shared_factor_count
  )
`
const NEW_C3 = `  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_cells
    WHERE shared_signal_count < 0
       OR shared_factor_count < 0
       OR (shared_signal_count > 0) != (shared_factor_count > 0)
  )
`
const OLD = ic(fs.readFileSync(path.join(MIG, '712_bo_sangati_integrity_check.sql'), 'utf8'))
const NEW = ic(SQL)

describe('migration 1299 — static contract', () => {
  it("rebuilds the live OLD text from migration 712 (md5 read from production 2026-10-05)", () => {
    expect(md5(OLD)).toBe(OLD_MD5)
    expect(OLD).toHaveLength(2455)
  })

  it('carries a NEW text that hashes to the md5 the file names', () => {
    expect(md5(NEW)).toBe(NEW_MD5)
    expect(NEW).toHaveLength(2539)
  })

  it('NEW = OLD with exactly the one conjunct-3 block replaced; every other conjunct byte-identical', () => {
    expect(OLD.split(OLD_C3)).toHaveLength(2)
    expect(NEW).toBe(OLD.replace(OLD_C3, NEW_C3))
    expect(NEW).not.toContain('shared_signal_count != shared_factor_count')
  })

  it('is ONE md5-guarded UPDATE of one column of one row; no DDL, no transaction control', () => {
    expect(CODE.match(/\bUPDATE asset_registry\b/g)).toHaveLength(1)
    expect(CODE).toContain(`WHERE asset_id = 'bo_sangati'\n   AND md5(integrity_check_sql) = '${OLD_MD5}';`)
    expect(CODE.match(/\bSET (?:LOCAL )?[a-z_]+ =/g)).toEqual(['SET LOCAL lock_timeout =', 'SET integrity_check_sql ='])
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/m)
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|INSERT|DELETE)\b/im)
  })

  it('starts with lock_timeout, NOTICEs (never raises) on a foreign text, raises only when the update did not take', () => {
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
    expect(CODE.match(/\bSET LOCAL lock_timeout\b/g)).toHaveLength(1)
    expect(CODE).toContain('is not the text this migration was written against')
    expect(CODE).toContain('NO-OP')
    expect(CODE.match(/RAISE EXCEPTION/g)).toHaveLength(1)
    expect(CODE).toContain('update did not take')
  })

  it('states the header facts: the defect, the invariant, the staling trigger effect, verification, rollback', () => {
    for (const n of ['THE DEFECT', 'len(shared_root_groups)', '28 of 56', 'THE REPLACEMENT', 'BYTE-IDENTICAL',
      'SERVING EFFECT AT APPLY', 'nirmana_registry_receipt_invalidation', "STALES bo_sangati's freshness rows", 'rebuilt in S-L2 run 2',
      'VERIFICATION BY PRODUCTION STRUCTURE', 'ROLLBACK', 'Residual premise', OLD_MD5, NEW_MD5]) {
      expect(FLAT).toContain(n)
    }
  })

  it('is a ROUTINE migration (not protected), unique, in the 1200-1299 range', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    const n = Number(FILE.slice(0, 4))
    expect(n).toBeGreaterThanOrEqual(1200)
    expect(n).toBeLessThanOrEqual(1299)
    expect(fs.readdirSync(MIG).filter(f => /^1299_/.test(f) && f !== FILE)).toEqual([])
  })
})

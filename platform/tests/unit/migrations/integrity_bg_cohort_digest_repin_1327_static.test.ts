/**
 * Suvarna routine migration 1327 — STATIC contract (bg_cohort's integrity_check_sql keeps its content-only whole-table digest
 * DEFINITION and gets the NEW PIN the L0 rebuild produces once PR #3215 has landed: Ketu retrograde flag mirrors Rahu, sampling_method
 * v3; every other byte of migration 626's text unchanged). The live proof (a disposable PostgreSQL cluster, the 10,000 stored
 * production rows, the REAL digest conjunct of both texts: OLD true / NEW false on today's rows, OLD false / NEW true on the rebuild
 * content, content-only, apply/guard/idempotency/serving effect/silent no-op) and the digest derivation from the committed fixture
 * are python-sidecar/tests/test_migration_1327_bg_cohort_digest_repin.py. This file pins the text so a drive-by edit (a different
 * pin, a widened replacement, a dropped guard) is a deliberate, reviewed change.
 */
import { describe, it, expect } from 'vitest'
import crypto from 'crypto'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const M626 = path.resolve(__dirname, '../../../supabase/migrations/626_nirmana_l0_cohort_exact_contract.sql')
const FILE = '1327_bg_cohort_integrity_digest_repin.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const FLAT = SQL.replace(/^--/gm, ' ').replace(/\s+/g, ' ')
const md5 = (s: string): string => crypto.createHash('md5').update(s, 'utf8').digest('hex')

const OLD_MD5 = '391d0f02482c1a669400a895286103f5'
const NEW_MD5 = 'c9fa9795e24ed65843026adf3ba74252'
const OLD_PIN = '921b0f62ca118932608ea3d3da89e8757ba7c6fbb64c41c2bbdc6b1f99e0c5fa'
const NEW_PIN = 'c516b597165e2e248b918a4001dce6fd77f137468f9ed8a029d5488613a7c844'

// OLD = the $check$ literal of migration 626 (never edited after apply) = the live production text (md5 read 2026-10-07).
const OLD = /\$check\$([\s\S]*?)\$check\$/.exec(fs.readFileSync(M626, 'utf8'))?.[1] ?? ''
const NEW = OLD.split(OLD_PIN).join(NEW_PIN)

describe('migration 1327 — static contract', () => {
  it('pins the live OLD text (md5 and length read from production 2026-10-07)', () => {
    expect(md5(OLD)).toBe(OLD_MD5)
    expect(OLD).toHaveLength(1959)
    expect(OLD.split(OLD_PIN)).toHaveLength(2)
  })

  it('NEW = OLD with exactly the one 64-hex pin replaced; it hashes to the md5 the migration names', () => {
    expect(NEW).not.toBe(OLD)
    expect(md5(NEW)).toBe(NEW_MD5)
    expect(NEW).toHaveLength(1959)
    expect(NEW.split(NEW_PIN)).toHaveLength(2)
    expect(NEW).toContain("'1f9e7fcf96941e891462ba1acd46b6c053f58d72d0dcb243a65d16a818c4decd'")
  })

  it('the digest stays content-only: run-identity columns are not in the text', () => {
    for (const col of ['build_id', 'computed_at']) expect(NEW).not.toContain(col)
    expect(NEW).toContain('synthetic_id,birth_datetime_utc,birth_lat,birth_lon,ayanamsha_key,\n      positions,sampling_method,source_citation')
  })

  it('the migration carries the two md5s and the two pins', () => {
    for (const [k, v] of [['c_old_md5', OLD_MD5], ['c_new_md5', NEW_MD5], ['c_old_pin', OLD_PIN], ['c_new_pin', NEW_PIN]]) {
      expect(SQL).toContain(`${k} constant text := '${v}'`)
    }
  })

  it('is ONE md5-guarded UPDATE of one column of the bg_cohort row; no DDL, no transaction control', () => {
    expect(CODE.match(/\bUPDATE asset_registry\b/g)).toHaveLength(1)
    expect(CODE).toContain("WHERE asset_id = 'bg_cohort'\n     AND md5(integrity_check_sql) = c_old_md5;")
    expect(CODE.match(/\bSET (?:LOCAL )?[a-z_]+ =/g)).toEqual(['SET LOCAL lock_timeout =', 'SET integrity_check_sql ='])
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/m)
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|INSERT|DELETE)\b/im)
    expect(CODE).toContain('replace(integrity_check_sql, c_old_pin, c_new_pin)')
  })

  it('starts with lock_timeout, NOTICEs (never raises) on a foreign text, raises only when the update did not take', () => {
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
    expect(CODE.match(/\bSET LOCAL lock_timeout\b/g)).toHaveLength(1)
    expect(CODE).toContain('is not the text this migration was written against')
    expect(CODE).toContain('NO-OP')
    expect(CODE).toContain('already carries the post-#3215 content digest pin')
    expect(CODE.match(/RAISE EXCEPTION/g)).toHaveLength(1)
    expect(CODE).toContain('update did not take')
  })

  it('states the header facts: defect, why a re-pin, value derivation, guard, staling trigger, accepted window, verification, rollback', () => {
    for (const n of ['THE DEFECT', 'WHY A RE-PIN AND NOT A NEW DIGEST DEFINITION', 'THE VALUE', 'Method proof', 'Projection', 'Replay',
      'GUARD AND WHAT HAPPENS WHEN IT DOES NOT MATCH', 'SERVING EFFECT AT APPLY', 'nirmana_registry_receipt_invalidation',
      "STALES bg_cohort's freshness rows", 'THE WINDOW BETWEEN THIS MIGRATION AND THE REBUILD', 'reads FALSE on TODAY',
      'VERIFICATION BY PRODUCTION STRUCTURE', 'ROLLBACK', OLD_MD5, NEW_MD5, OLD_PIN, NEW_PIN]) {
      expect(FLAT.toLowerCase()).toContain(n.toLowerCase())
    }
  })

  it('is a ROUTINE migration (not protected), unique, in the 1320-1329 claimed block', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    const n = Number(FILE.slice(0, 4))
    expect(n).toBeGreaterThanOrEqual(1320)
    expect(n).toBeLessThanOrEqual(1329)
    expect(fs.readdirSync(MIG).filter(f => /^1327_/.test(f) && f !== FILE)).toEqual([])
  })
})

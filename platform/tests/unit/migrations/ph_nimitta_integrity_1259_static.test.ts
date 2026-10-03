/**
 * Suvarna / migration 1259 — STATIC contract (ph_nimitta integrity_check_sql loses its global mimamsa_predictions term).
 * The live proof (a disposable PostgreSQL cluster: apply, idempotent re-run, md5 guards, serving effect, check
 * semantics on the 135-dangling case, every other corruption still caught, mutants) is
 * python-sidecar/tests/test_migration_1259_ph_nimitta_integrity_scope.py. This file pins the text so a drive-by
 * edit (a widened removal, a different target, a dropped guard) is a deliberate, reviewed change.
 */
import { describe, it, expect } from 'vitest'
import crypto from 'crypto'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1259_nirmana_l4_ph_nimitta_integrity_scope_own_family.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const FLAT = SQL.replace(/^--/gm, ' ').replace(/\s+/g, ' ')

const OLD_MD5 = '658ffdbcb6d531e8cf5eed6c5260a966'
const NEW_MD5 = '45192b2752989dc4398d81c0135e1473'
const md5 = (s: string): string => crypto.createHash('md5').update(s).digest('hex')

const m680 = fs.readFileSync(path.join(MIG, '680_phala_anchor_deterministic_identity.sql'), 'utf8')
const m683 = fs.readFileSync(path.join(MIG, '683_phala_anchor_signal_id_disposition.sql'), 'utf8')
const oldText = (/\$check\$([\s\S]*?)\$check\$/.exec(m680)?.[1] ?? '') + (/\$add\$([\s\S]*?)\$add\$/.exec(m683)?.[1] ?? '')
const newText = /\$ck\$([\s\S]*)\$ck\$/.exec(SQL)?.[1] ?? ''
const exec = (s: string): string => s.replace(/--[^\n]*/g, '').replace(/\s+/g, ' ').trim()
const TERM =
  'AND (SELECT count(*) FROM mimamsa_predictions p LEFT JOIN phala_anchors a ON a.anchor_id::text = p.source_pramana_id ' +
  'WHERE p.source_pramana_id IS NOT NULL AND a.anchor_id IS NULL) = 0'

describe('migration 1259 — static contract', () => {
  it('rebuilds the live OLD text from migrations 680 + 683 (md5 read from production 2026-10-03)', () => {
    expect(md5(oldText)).toBe(OLD_MD5)
    expect(oldText).toHaveLength(3063)
  })

  it('carries a NEW text that hashes to the md5 the file names', () => {
    expect(md5(newText)).toBe(NEW_MD5)
    expect(newText).toHaveLength(3167)
  })

  it('NEW = OLD minus exactly the one global mimamsa_predictions term (comments aside)', () => {
    const o = exec(oldText)
    const n = exec(newText)
    expect(o.split(TERM)).toHaveLength(2)
    expect(n).not.toContain('mimamsa_predictions')
    expect(n).toBe(o.replace(' ' + TERM, ''))
    // every other conjunct survives
    for (const t of ['phala_suddha_sodhana', 'phala_sodhana', 'phala_pramana', 'phala_sankrama', 'phala_muhurta',
      'phala_mitigation', 'phala_phaladesa', 'bodha_msr_signals', 'phala_anchor_identity(', '<= 4', 'HAVING count(*) > 1']) {
      expect(n).toContain(t)
    }
  })

  it('is one md5-guarded UPDATE of one column of one row; names both md5s exactly twice', () => {
    expect(CODE.match(/\bUPDATE asset_registry\b/g)).toHaveLength(1)
    expect(CODE).toContain("WHERE asset_id = 'ph_nimitta'")
    expect(CODE).toContain(`AND md5(integrity_check_sql) = '${OLD_MD5}'`)
    expect(CODE.split(OLD_MD5)).toHaveLength(3)
    expect(CODE.split(NEW_MD5)).toHaveLength(3)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/m)
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|INSERT|DELETE)\b/im)
    expect(CODE).toContain('$pre$')
    expect(CODE).toContain('$post$')
  })

  it('starts with the transaction-local 5s lock_timeout', () => {
    expect(CODE.match(/\bSET LOCAL lock_timeout\b/g)).toHaveLength(1)
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
  })

  it('refuses an unexpected base text and a missing/duplicate registry row', () => {
    expect(CODE).toContain("1259: expected exactly one ph_nimitta registry row")
    expect(CODE).toContain('is not the text this migration was written against')
    expect(CODE).toContain('did not take')
  })

  it('states the header facts: held, serving effect and trigger, readbacks, still-false finding, not-done list', () => {
    for (const n of ['HELD', 'AFTER S-L1', "on SS's review", 'SERVING EFFECT AT APPLY', 'nirmana_registry_receipt_invalidation',
      'Affected asset: ph_nimitta ONLY', '0 of them belong to any ph_* asset', 'IDEMPOTENT SHAPE', 'ROLLBACK',
      '0 ACTIVE RUNS AT APPLY', 'VERIFICATION BY PRODUCTION STRUCTURE', 'NOT DONE HERE', 'no EXECUTE on phala_anchor_identity',
      'NEW text: STILL FALSE', 'phala_phaladesa.top_anchor_id', 'Q-L4-02', 'migration 680', OLD_MD5, NEW_MD5]) {
      expect(FLAT).toContain(n)
    }
  })

  it('is a ROUTINE migration (not protected), unique, in the 1200-1299 range', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    const n = Number(FILE.slice(0, 4))
    expect(n).toBeGreaterThanOrEqual(1200)
    expect(n).toBeLessThanOrEqual(1299)
    expect(fs.readdirSync(MIG).filter(f => /^1259_/.test(f) && f !== FILE)).toEqual([])
  })
})

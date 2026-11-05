/**
 * Suvarna / migration 1276 — STATIC contract (mi_bhavisya natural_key_partition: the delete-based justification of migration 991 replaced by the
 * append-only one, SS N-104 / N-107, PR #3040). The live proof (disposable PG 15 and 17, run as amjis_app on a production-mirrored layout with the real
 * nirmana_registry_receipt_invalidation trigger: text stored, no other column changed, 0 freshness rows staled, the partition-key strand guard, md5 guard,
 * idempotency, active-run guard, lock_timeout, 14 mutants) is python-sidecar/tests/test_migration_1276_mi_bhavisya_natural_key_partition.py.
 */
import { describe, it, expect } from 'vitest'
import crypto from 'crypto'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1276_mi_bhavisya_natural_key_partition_append_only.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const FLAT = SQL.replace(/^--/gm, ' ').replace(/\s+/g, ' ')
const md5 = (s: string): string => crypto.createHash('md5').update(s).digest('hex')
const OLD_MD5 = '07d729f8f0487ac3d3ddb114dd4cdc73'
const NEW_MD5 = 'a411af1488287dced6b8b121ec1eb28b'
const m991 = fs.readFileSync(path.join(MIG, '991_nirmana_l5_mi_bhavisya_natural_key_partition.sql'), 'utf8')
const oldText = (/SET natural_key_partition = '((?:[^']|'')*)'/s.exec(m991)?.[1] ?? '').replace(/''/g, "'")
const newText = /\$nkp\$([\s\S]*)\$nkp\$/.exec(SQL)?.[1] ?? ''

describe('migration 1276 — static contract', () => {
  it('the stored OLD text is the 991 literal and hashes to the live production md5', () => {
    expect(md5(oldText)).toBe(OLD_MD5)
    expect(oldText).toHaveLength(2838)
    expect(oldText).toContain('idempotent DELETE FROM mimamsa_manifestation_sets')
  })

  it('the NEW text hashes to the named md5 and length, states the append-only facts and relies on no delete', () => {
    expect(md5(newText)).toBe(NEW_MD5)
    expect(newText).toHaveLength(3544)
    for (const n of ['APPEND-ONLY', 'N-104', 'N-107', 'PR #3040', 'never DELETEs or UPDATEs', 'ON CONFLICT DO NOTHING', 'CUMULATIVE', 'TWO-PART NATURAL KEY',
      "prediction_id = 'pred_<anchor_id>'", "source_pramana_id = '<anchor_id>'", 'mimamsa_manifestation_sets (chart_id, prediction_id, channel_id) -- ',
      'DELIBERATELY NOT COVERED']) expect(newText).toContain(n)
    for (const g of ['DELETE FROM', 'idempotent DELETE', "exactly the current run's row set exists"]) expect(newText).not.toContain(g)
  })

  it('is ONE md5-guarded UPDATE of ONE column of ONE row; never touches integrity_check_sql (1259)', () => {
    expect(CODE.match(/\bUPDATE asset_registry\b/g)).toHaveLength(1)
    expect(CODE).toContain(`WHERE asset_id = 'mi_bhavisya'\n  AND md5(natural_key_partition) = '${OLD_MD5}';`)
    expect(CODE.split(OLD_MD5).length - 1).toBeGreaterThanOrEqual(2)
    expect(CODE.split(NEW_MD5).length - 1).toBeGreaterThanOrEqual(2)
    expect(CODE).not.toContain('integrity_check_sql')
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/m)
  })

  it('has the lock_timeout, the active-run guard, the strand guard, the pre-check and the asserting post-check', () => {
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
    for (const n of ['$runs$', '$pre$', '$post$', "r.state NOT IN ('completed', 'failed', 'stopped')", 'would strand them',
      'is not the text this migration was written against', 'did not take', 'is not the append-only text',
      'another column of the mi_bhavisya registry row changed']) expect(CODE).toContain(n)
  })

  it('states the header facts: held post-window, serving effect, the text-is-a-key consequence, other columns, verification', () => {
    for (const n of ['HELD, POST-WINDOW', 'AFTER PR #3040', 'natural_key_partition IS in its column list', 'asset_freshness has 0 rows for mi_bhavisya',
      'THE TEXT IS A KEY', 'THE MIGRATION ENFORCES THAT', 'OTHER COLUMNS OF THE SAME ROW', 'expected_volume_formula', 'ACTIVE RUNS (ENFORCED',
      'IDEMPOTENT SHAPE', 'VERIFICATION BY PRODUCTION STRUCTURE', 'ROLLBACK', 'Migration 991 is NOT edited', OLD_MD5, NEW_MD5]) expect(FLAT).toContain(n)
  })

  it('is a ROUTINE migration (not protected), unique, in the 1200-1299 range', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    const n = Number(FILE.slice(0, 4))
    expect(n).toBeGreaterThanOrEqual(1200)
    expect(n).toBeLessThanOrEqual(1299)
    expect(fs.readdirSync(MIG).filter(f => /^1276_/.test(f) && f !== FILE)).toEqual([])
  })
})

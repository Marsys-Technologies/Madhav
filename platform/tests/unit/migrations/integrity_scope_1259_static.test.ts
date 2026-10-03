/**
 * Suvarna / migration 1259 — STATIC contract (ph_nimitta and mi_bhavisya integrity_check_sql each lose their one global
 * dangling-anchor term). The live proof (a disposable PostgreSQL cluster: apply, idempotent re-run, md5 guards, serving
 * effect on both assets, check semantics on the 135-dangling case, every other corruption still caught, mutants) is
 * python-sidecar/tests/test_migration_1259_integrity_scope_ph_nimitta_mi_bhavisya.py. This file pins the text so a
 * drive-by edit (a widened removal, a different target, a dropped guard) is a deliberate, reviewed change.
 */
import { describe, it, expect } from 'vitest'
import crypto from 'crypto'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1259_integrity_checks_claim_only_own_family_ph_nimitta_mi_bhavisya.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const FLAT = SQL.replace(/^--/gm, ' ').replace(/\s+/g, ' ')

const PH_OLD = '658ffdbcb6d531e8cf5eed6c5260a966'
const PH_NEW = '45192b2752989dc4398d81c0135e1473'
const MI_OLD = '19b5ea334236eaffa493069a7d4b318b'
const MI_NEW = '8e88e9d4ed07f47cdcecc7861fc8516d'
const md5 = (s: string): string => crypto.createHash('md5').update(s).digest('hex')

const m680 = fs.readFileSync(path.join(MIG, '680_phala_anchor_deterministic_identity.sql'), 'utf8')
const m683 = fs.readFileSync(path.join(MIG, '683_phala_anchor_signal_id_disposition.sql'), 'utf8')
const m691 = fs.readFileSync(path.join(MIG, '691_nirmana_l5_w3_integrity_contracts.sql'), 'utf8')
const phOld = (/\$check\$([\s\S]*?)\$check\$/.exec(m680)?.[1] ?? '') + (/\$add\$([\s\S]*?)\$add\$/.exec(m683)?.[1] ?? '')
const miOld = [...m691.matchAll(/\$check\$([\s\S]*?)\$check\$/g)].map(m => m[1] ?? '').find(t => t.includes('FULL JOIN mimamsa_manifestation_sets')) ?? ''
const phNew = /\$ck\$([\s\S]*)\$ck\$/.exec(SQL)?.[1] ?? ''
const miNew = /\$mk\$([\s\S]*)\$mk\$/.exec(SQL)?.[1] ?? ''
const exec = (s: string): string => s.replace(/--[^\n]*/g, '').replace(/\s+/g, ' ').trim()
const PH_TERM =
  'AND (SELECT count(*) FROM mimamsa_predictions p LEFT JOIN phala_anchors a ON a.anchor_id::text = p.source_pramana_id ' +
  'WHERE p.source_pramana_id IS NOT NULL AND a.anchor_id IS NULL) = 0'
const MI_TERM =
  'OR count(*) FILTER (WHERE p.prediction_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM phala_anchors a ' +
  'WHERE a.chart_id = p.chart_id AND a.anchor_id::text = p.source_pramana_id)) > 0'

describe('migration 1259 — static contract', () => {
  it('rebuilds both live OLD texts from migrations 680+683 and 691 (md5 read from production 2026-10-03)', () => {
    expect(md5(phOld)).toBe(PH_OLD)
    expect(phOld).toHaveLength(3063)
    expect(md5(miOld)).toBe(MI_OLD)
    expect(miOld).toHaveLength(2186)
  })

  it('carries NEW texts that hash to the md5s the file names', () => {
    expect(md5(phNew)).toBe(PH_NEW)
    expect(phNew).toHaveLength(3167)
    expect(md5(miNew)).toBe(MI_NEW)
    expect(miNew).toHaveLength(1951)
  })

  it('ph_nimitta NEW = OLD minus exactly the one global mimamsa_predictions term (comments aside)', () => {
    const o = exec(phOld)
    const n = exec(phNew)
    expect(o.split(PH_TERM)).toHaveLength(2)
    expect(n).not.toContain('mimamsa_predictions')
    expect(n).toBe(o.replace(' ' + PH_TERM, ''))
    for (const t of ['phala_suddha_sodhana', 'phala_sodhana', 'phala_pramana', 'phala_sankrama', 'phala_muhurta',
      'phala_mitigation', 'phala_phaladesa', 'bodha_msr_signals', 'phala_anchor_identity(', '<= 4', 'HAVING count(*) > 1']) {
      expect(n).toContain(t)
    }
  })

  it('mi_bhavisya NEW = OLD minus exactly the one dangling-anchor OR branch (no comments added)', () => {
    const o = exec(miOld)
    const n = exec(miNew)
    expect(o.split(MI_TERM)).toHaveLength(2)
    expect(n).not.toContain('phala_anchors')
    expect(n).toBe(o.replace(' ' + MI_TERM, ''))
    for (const t of ['FULL JOIN mimamsa_manifestation_sets', 'LEFT JOIN charts c', 'observation_window', 'confidence_band',
      'frozen_bundle_hash', 'm.domain IS DISTINCT FROM p.domain', 'citation_ref',
      'count(DISTINCT prediction_id) <> count(*)', 'count(DISTINCT (prediction_id, channel_id)) <> count(*)']) {
      expect(n).toContain(t)
    }
  })

  it('is two md5-guarded UPDATEs, one per asset, of one column; each md5 named exactly twice', () => {
    expect(CODE.match(/\bUPDATE asset_registry\b/g)).toHaveLength(2)
    for (const [asset, oldM, newM] of [['ph_nimitta', PH_OLD, PH_NEW], ['mi_bhavisya', MI_OLD, MI_NEW]] as const) {
      expect(CODE).toContain(`WHERE asset_id = '${asset}'\n  AND md5(integrity_check_sql) = '${oldM}';`)
      expect(CODE.split(oldM)).toHaveLength(3)
      expect(CODE.split(newM)).toHaveLength(3)
    }
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/m)
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|INSERT|DELETE)\b/im)
    expect(CODE).toContain('$pre$')
    expect(CODE).toContain('$post$')
  })

  it('starts with the transaction-local 5s lock_timeout', () => {
    expect(CODE.match(/\bSET LOCAL lock_timeout\b/g)).toHaveLength(1)
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
  })

  it('refuses an unexpected base text and a missing/duplicate registry row, for each asset', () => {
    expect(CODE).toContain("1259: expected exactly one % registry row")
    expect(CODE).toContain('is not the text this migration was written against')
    expect(CODE).toContain('did not take')
  })

  it('states the header facts: held, both assets named in the serving effect, readbacks, still-false finding, not-done list', () => {
    for (const n of ['HELD', 'AFTER S-L1', "on SS's review", 'SERVING EFFECT AT APPLY', 'nirmana_registry_receipt_invalidation',
      'Affected assets: ph_nimitta and mi_bhavisya, and no others', '0 belong to any ph_* asset', 'IDEMPOTENT SHAPE', 'ROLLBACK',
      '0 ACTIVE RUNS AT APPLY', 'VERIFICATION BY PRODUCTION STRUCTURE', 'NOT DONE HERE', 'no EXECUTE on phala_anchor_identity',
      'NEW text: STILL FALSE', 'phala_phaladesa.top_anchor_id', 'Q-L4-02', 'N-104', '#3023', 'migration 680', 'migration 691',
      'OLD (md5 19b5ea33...) = false; NEW (md5 8e88e9d4...) = true', PH_OLD, PH_NEW, MI_OLD, MI_NEW]) {
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

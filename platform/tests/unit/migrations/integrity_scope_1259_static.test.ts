/**
 * Suvarna / migration 1259 — STATIC contract (integrity checks claim only their own writer's output: ph_nimitta and
 * mi_bhavisya lose their cross-asset terms; ph_sankrama and ph_pratikara gain the anchor-reference terms they lacked; five
 * owners already carry theirs). The live proof (a disposable PostgreSQL cluster, run as amjis_app on a production-mirrored
 * role/ACL layout: apply, idempotent re-run, md5 guards, ownership precondition, active-run guard, serving effect on the four
 * assets, check semantics, mutants) is python-sidecar/tests/test_migration_1259_integrity_scope_own_output.py. This file pins
 * the text so a drive-by edit (a widened removal, a different target, a dropped guard) is a deliberate, reviewed change.
 */
import { describe, it, expect } from 'vitest'
import crypto from 'crypto'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1259_integrity_checks_claim_only_own_output.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const FLAT = SQL.replace(/^--/gm, ' ').replace(/\s+/g, ' ')

const OLD: Record<string, string> = {
  ph_nimitta: '658ffdbcb6d531e8cf5eed6c5260a966',
  mi_bhavisya: '19b5ea334236eaffa493069a7d4b318b',
  ph_sankrama: '298b2259cda7bd5b4759061e74d75d17',
  ph_pratikara: 'c00c6c88e3a9fc74489bde3988870ef0',
}
const NEW: Record<string, string> = {
  ph_nimitta: 'a32f6d86553f67458dfd8373e4fdbe39',
  mi_bhavisya: '8e88e9d4ed07f47cdcecc7861fc8516d',
  ph_sankrama: 'e97e797678f23c673d962b7c6cbb74ee',
  ph_pratikara: 'fac43b4e3117b30efb93aa87aaf80f5f',
}
const TAG: Record<string, string> = { ph_nimitta: 'ck', mi_bhavisya: 'mk', ph_sankrama: 'sk', ph_pratikara: 'rk' }
const md5 = (s: string): string => crypto.createHash('md5').update(s).digest('hex')
const exec = (s: string): string => s.replace(/--[^\n]*/g, '').replace(/\s+/g, ' ').trim()
const newText = (a: string): string => new RegExp(`\\$${TAG[a]}\\$([\\s\\S]*)\\$${TAG[a]}\\$`).exec(SQL)?.[1] ?? ''

const m680 = fs.readFileSync(path.join(MIG, '680_phala_anchor_deterministic_identity.sql'), 'utf8')
const m683 = fs.readFileSync(path.join(MIG, '683_phala_anchor_signal_id_disposition.sql'), 'utf8')
const m691 = fs.readFileSync(path.join(MIG, '691_nirmana_l5_w3_integrity_contracts.sql'), 'utf8')
const m681 = fs.readFileSync(path.join(MIG, '681_l4_phala_c12_registry_contracts.sql'), 'utf8')
const blocks681 = [...m681.matchAll(/\$check\$([\s\S]*?)\$check\$/g)].map(m => m[1] ?? '')
const oldText = (a: string): string => {
  if (a === 'ph_nimitta') return (/\$check\$([\s\S]*?)\$check\$/.exec(m680)?.[1] ?? '') + (/\$add\$([\s\S]*?)\$add\$/.exec(m683)?.[1] ?? '')
  if (a === 'mi_bhavisya') return [...m691.matchAll(/\$check\$([\s\S]*?)\$check\$/g)].map(m => m[1] ?? '').find(t => t.includes('FULL JOIN mimamsa_manifestation_sets')) ?? ''
  return blocks681.find(b => md5(b) === OLD[a]) ?? ''
}
const MI_TERM =
  'OR count(*) FILTER (WHERE p.prediction_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM phala_anchors a ' +
  'WHERE a.chart_id = p.chart_id AND a.anchor_id::text = p.source_pramana_id)) > 0'

describe('migration 1259 — static contract', () => {
  it('rebuilds all four live OLD texts from migrations 680+683, 691 and 681 (md5 read from production 2026-10-03)', () => {
    for (const a of Object.keys(OLD)) expect(md5(oldText(a))).toBe(OLD[a])
  })

  it('carries NEW texts that hash to the md5s the file names', () => {
    for (const a of Object.keys(NEW)) expect(md5(newText(a))).toBe(NEW[a])
    expect(newText('ph_nimitta')).toHaveLength(2100)
    expect(newText('mi_bhavisya')).toHaveLength(1951)
    expect(newText('ph_sankrama')).toHaveLength(1409)
    expect(newText('ph_pratikara')).toHaveLength(1703)
  })

  it('ph_nimitta keeps ONLY facts about phala_anchors: identity (<= 4) and C13; every cross-asset table left', () => {
    const n = exec(newText('ph_nimitta'))
    for (const gone of ['phala_pramana', 'phala_sodhana', 'phala_suddha_sodhana', 'phala_sankrama', 'phala_muhurta',
      'phala_mitigation', 'phala_phaladesa', 'mimamsa_predictions']) expect(n).not.toContain(gone)
    expect(n).toContain('phala_anchor_identity(')
    expect(n).toContain('<= 4')
    expect(n).toContain('bodha_msr_signals')
    expect(n.split('(SELECT count(*) FROM')).toHaveLength(2)
    // strictly shorter than the base: nothing was added to the executable text
    expect(exec(oldText('ph_nimitta')).length).toBeGreaterThan(n.length)
  })

  it('mi_bhavisya NEW = OLD minus exactly the one dangling-anchor OR branch (no comments added)', () => {
    const o = exec(oldText('mi_bhavisya'))
    const n = exec(newText('mi_bhavisya'))
    expect(o.split(MI_TERM)).toHaveLength(2)
    expect(n).not.toContain('phala_anchors')
    expect(n).toBe(o.replace(' ' + MI_TERM, ''))
  })

  it('ph_sankrama and ph_pratikara NEW = OLD (a strict prefix) plus exactly one appended NOT EXISTS conjunct', () => {
    for (const a of ['ph_sankrama', 'ph_pratikara']) {
      expect(newText(a).startsWith(oldText(a))).toBe(true)
      const added = exec(newText(a)).slice(exec(oldText(a)).length).trim()
      expect(added.startsWith('AND NOT EXISTS (SELECT 1 FROM')).toBe(true)
      expect(added).toContain('LEFT JOIN phala_anchors a ON a.anchor_id =')
      expect(added).toContain('IS NOT NULL AND a.anchor_id IS NULL GROUP BY')
    }
  })

  it('is four md5-guarded UPDATEs, one per asset, of one column; no owner is updated; each md5 named exactly twice', () => {
    expect(CODE.match(/\bUPDATE asset_registry\b/g)).toHaveLength(4)
    for (const a of Object.keys(OLD)) {
      expect(CODE).toContain(`WHERE asset_id = '${a}'\n  AND md5(integrity_check_sql) = '${OLD[a]}';`)
      expect(CODE.split(OLD[a])).toHaveLength(3)
      expect(CODE.split(NEW[a])).toHaveLength(3)
    }
    for (const owner of ['ph_phaladesa', 'ph_pramana', 'ph_sodhana', 'ph_suddha_sodhana', 'ph_muhurta']) {
      expect(CODE).not.toMatch(new RegExp(`WHERE asset_id = '${owner}'\\s+AND md5`))
    }
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/m)
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|INSERT|DELETE)\b/im)
  })

  it('has the active-run guard, the md5 pre-check, the ownership precondition and the post-check, and starts with lock_timeout', () => {
    for (const t of ['$runs$', '$pre$', '$own$', '$post$']) expect(CODE).toContain(t)
    expect(CODE).toContain("r.state NOT IN ('completed', 'failed', 'stopped')")
    expect(CODE).toContain('active build run(s)')
    expect(CODE).toContain('no longer carries its own anchor-reference term')
    expect(CODE).toContain('is not the text this migration was written against')
    expect(CODE).toContain('did not take')
    expect(CODE.match(/\bSET LOCAL lock_timeout\b/g)).toHaveLength(1)
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
  })

  it('states the header facts: every touched asset in the serving effect, the moves, both readback tables, not-done', () => {
    for (const n of ['HELD', 'AFTER S-L1', "on SS's review", 'SERVING EFFECT AT APPLY', 'nirmana_registry_receipt_invalidation',
      'Assets touched, and no others: ph_nimitta, mi_bhavisya, ph_sankrama, ph_pratikara', '0 belong to any ph_* asset',
      'The five owners are NOT updated', 'WHAT MOVES WHERE', 'READBACKS', 'NO EXECUTE on it', 'FALSE, honestly',
      'IDEMPOTENT SHAPE', 'ROLLBACK', '0 ACTIVE RUNS AT APPLY (ENFORCED', 'VERIFICATION BY PRODUCTION STRUCTURE', 'NOT DONE HERE',
      'N-99', 'N-104', 'N-105', '#3023', ...Object.values(OLD), ...Object.values(NEW)]) {
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

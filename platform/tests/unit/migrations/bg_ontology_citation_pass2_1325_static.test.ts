/**
 * CITATION-PASS2 / migration 1325 — STATIC contract (bg_ontology's integrity_check_sql, target_floor and volume_explanation are re-sealed after decision OS-2026-10-05-CITATIONS).
 * The live proof (the real writer replayed on a disposable PostgreSQL: the new check TRUE on the rebuilt state and FALSE on the old one) is in the python-sidecar test
 * tests/l0/test_citation_pass2_ontology.py. This file pins the text so a drive-by edit (a widened pin, a different target, a dropped guard) is a deliberate, reviewed change.
 */
import { describe, it, expect } from 'vitest'
import crypto from 'crypto'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'
import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1325_bg_ontology_citation_pass2_integrity_reseal.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const FLAT = SQL.replace(/^--/gm, ' ').replace(/\s+/g, ' ')
const md5 = (s: string): string => crypto.createHash('md5').update(s).digest('hex')
const tagged = (s: string, tag: string): string => new RegExp('\\$' + tag + '\\$([\\s\\S]*?)\\$' + tag + '\\$').exec(s)?.[1] ?? ''

const OLD_MD5 = '5fc7ea8d12969043a8258696cebcc1bc'
const NEW_MD5 = 'dad6e9189baa2ccda4579aaf36e07bad'
const OLD = /ontology_check CONSTANT TEXT := \$check\$([\s\S]*?)\$check\$;/.exec(fs.readFileSync(path.resolve(__dirname, '../../../supabase/migrations/606_nirmana_l0_wave0_integrity_contracts.sql'), 'utf8'))?.[1] ?? ''
const NEW = tagged(SQL, 'ic')
// The exact replacements that turn the live check into the citation-pass-2 check (each occurs once in OLD).
const REPLACEMENTS: Array<[string, string]> = [
  [`(SELECT COUNT(*) >= 737 FROM brahma_ontology)`, `(SELECT COUNT(*) >= 728 FROM brahma_ontology)`],
]

describe('migration 1325 — static contract', () => {
  it("rebuilds the OLD text from the migration that installed it", () => {
    expect(md5(OLD)).toBe(OLD_MD5)
    expect(OLD).toHaveLength(1756)
  })

  it('carries a NEW text that hashes to the md5 the file names', () => {
    expect(md5(NEW)).toBe(NEW_MD5)
    expect(NEW).toHaveLength(1756)
  })

  it('NEW = OLD with exactly the pin replacements; every other conjunct byte-identical', () => {
    let t = OLD
    for (const [a, b] of REPLACEMENTS) {
      expect(t.split(a)).toHaveLength(2)
      t = t.replace(a, b)
    }
    expect(NEW).toBe(t)
    expect(REPLACEMENTS).toHaveLength(1)
  })

  it('is ONE md5-guarded UPDATE of one asset_registry row; no DDL, no data write, no transaction control', () => {
    expect(CODE.match(/\bUPDATE asset_registry\b/g)).toHaveLength(1)
    expect(CODE).toContain(`WHERE asset_id = 'bg_ontology'\n   AND target_floor = 737\n   AND md5(integrity_check_sql) = '${OLD_MD5}';`)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/m)
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|INSERT|DELETE)\b/im)
    expect(CODE.replace(/\$ic\$[\s\S]*?\$ic\$/, '')).not.toMatch(/\b(brahma_dosha_catalog|brahma_ontology|reference_doshas)\b\s*(SET|WHERE)|UPDATE\s+(brahma_dosha_catalog|brahma_ontology|reference_doshas)/i)
  })

  it('starts with lock_timeout, NOTICEs (never raises) on a foreign text, raises only when the update did not take', () => {
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
    expect(CODE).toContain('NO-OP')
    expect(CODE.match(/RAISE EXCEPTION/g)).toHaveLength(1)
    expect(CODE).toContain('update did not take')
  })

  it('sets the floor and volume the registry seed carries', () => {
    const asset = ASSETS.find(a => a.asset_id === 'bg_ontology')
    expect(asset?.target_floor).toBe(728)
    expect(CODE).toContain('target_floor = 728')
    const vol = /volume_explanation = '([^']*)'/.exec(CODE)?.[1]
    expect(vol).toBe(asset?.volume_explanation)
  })

  it('states the header facts: decision, number, pins, guard, trigger effect, order of operations, verification, rollback', () => {
    for (const n of ['OS-2026-10-05-CITATIONS', '1300, 1301, 1302', 'GUARD AND WHAT HAPPENS', 'ORDER OF OPERATIONS', 'SERVING EFFECT AT APPLY',
      'nirmana_registry_receipt_invalidation', 'VERIFICATION BY PRODUCTION STRUCTURE', 'ROLLBACK', OLD_MD5, NEW_MD5, 'APPLY ORDER', 'NO expected-change file']) {
      expect(FLAT).toContain(n)
    }
  })

  it('is a ROUTINE migration (not protected), unique in its number', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    expect(fs.readdirSync(MIG).filter(f => /^1325_/.test(f) && f !== FILE)).toEqual([])
    expect(fs.readdirSync(path.resolve(MIG, '../supabase/migrations')).filter(f => /^1325_/.test(f))).toEqual([])
  })
})

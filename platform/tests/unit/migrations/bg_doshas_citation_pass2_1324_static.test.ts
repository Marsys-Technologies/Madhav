/**
 * CITATION-PASS2 / migration 1324 — STATIC contract (bg_doshas's integrity_check_sql, target_floor and volume_explanation are re-sealed after decision OS-2026-10-05-CITATIONS).
 * The live proof (the real writer replayed on a disposable PostgreSQL: the new check TRUE on the rebuilt state and FALSE on the old one) is in the python-sidecar test
 * tests/l0/test_citation_pass2_doshas_migration.py. This file pins the text so a drive-by edit (a widened pin, a different target, a dropped guard) is a deliberate, reviewed change.
 */
import { describe, it, expect } from 'vitest'
import crypto from 'crypto'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'
import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1324_bg_doshas_citation_pass2_integrity_reseal.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const FLAT = SQL.replace(/^--/gm, ' ').replace(/\s+/g, ' ')
const md5 = (s: string): string => crypto.createHash('md5').update(s).digest('hex')
const tagged = (s: string, tag: string): string => new RegExp('\\$' + tag + '\\$([\\s\\S]*?)\\$' + tag + '\\$').exec(s)?.[1] ?? ''

const OLD_MD5 = '681d6b26ff4e5816a3f08650cdb76b4b'
const NEW_MD5 = 'e4baff75780519cc4fdf76b6ce27c9fd'
const OLD = tagged(fs.readFileSync(path.resolve(__dirname, '../../../migrations/692_bg_doshas_integrity_check_join_scope_fix.sql'), 'utf8'), 'check')
const NEW = tagged(SQL, 'ic')
// The exact replacements that turn the live check into the citation-pass-2 check (each occurs once in OLD).
const REPLACEMENTS: Array<[string, string]> = [
  [`(SELECT count(*) = 79 FROM brahma_dosha_catalog)`, `(SELECT count(*) = 66 FROM brahma_dosha_catalog)`],
  [`(SELECT count(*) = 79 FROM brahma_ontology WHERE entity_class='dosha')`, `(SELECT count(*) = 66 FROM brahma_ontology WHERE entity_class='dosha')`],
  [`(SELECT count(*) = 79 FROM reference_doshas)`, `(SELECT count(*) = 66 FROM reference_doshas)`],
  [`AND cardinality(associated_remedies)=0) = 79 FROM brahma_dosha_catalog)`, `AND cardinality(associated_remedies)=0) = 66 FROM brahma_dosha_catalog)`],
  [`'cfb21a5342bda3a911f55597cac3367b727a79953ccef3349ad7f49c98acfcd4'`, `'308ce2a6048c488eefcea3abe8fa9c9c90d383981f9133b667614ac31d94628b'`],
  [`'ee5dedf6e9934f42883ff268c3e485648577c6e528bfb76b7b839937b4572984'`, `'ed74d67afa450fdbcc22940a155243e2dbd72a78bbc7f4c16585330de0cae72d'`],
  [`'3fd442d6e8bfcb54fa5f4752907a2ef057ab1f49ec12aad9536a833b4e04d9a4'`, `'29ff924c2627ff1d9f1f3036188249351ba51a46ef99757d3c271e55dd2c86b7'`],
]

describe('migration 1324 — static contract', () => {
  it("rebuilds the OLD text from the migration that installed it", () => {
    expect(md5(OLD)).toBe(OLD_MD5)
    expect(OLD).toHaveLength(2206)
  })

  it('carries a NEW text that hashes to the md5 the file names', () => {
    expect(md5(NEW)).toBe(NEW_MD5)
    expect(NEW).toHaveLength(2206)
  })

  it('NEW = OLD with exactly the pin replacements; every other conjunct byte-identical', () => {
    let t = OLD
    for (const [a, b] of REPLACEMENTS) {
      expect(t.split(a)).toHaveLength(2)
      t = t.replace(a, b)
    }
    expect(NEW).toBe(t)
    expect(REPLACEMENTS).toHaveLength(7)
  })

  it('is ONE md5-guarded UPDATE of one asset_registry row; no DDL, no data write, no transaction control', () => {
    expect(CODE.match(/\bUPDATE asset_registry\b/g)).toHaveLength(1)
    expect(CODE).toContain(`WHERE asset_id = 'bg_doshas'\n   AND target_floor = 237\n   AND md5(integrity_check_sql) = '${OLD_MD5}';`)
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
    const asset = ASSETS.find(a => a.asset_id === 'bg_doshas')
    expect(asset?.target_floor).toBe(198)
    expect(CODE).toContain('target_floor = 198')
    const vol = /volume_explanation = '([^']*)'/.exec(CODE)?.[1]
    expect(vol).toBe(asset?.volume_explanation)
  })

  it('states the header facts: decision, number, pins, guard, trigger effect, order of operations, verification, rollback', () => {
    for (const n of ['OS-2026-10-05-CITATIONS', '1300, 1301, 1302', 'GUARD AND WHAT HAPPENS', 'ORDER OF OPERATIONS', 'SERVING EFFECT AT APPLY',
      'nirmana_registry_receipt_invalidation', 'VERIFICATION BY PRODUCTION STRUCTURE', 'ROLLBACK', OLD_MD5, NEW_MD5, 'EXPECTED_CHANGE_bg_doshas_citation_pass2.json', 'APPLY ORDER', 'SIDE EFFECT ON bg_parihara_rules']) {
      expect(FLAT).toContain(n)
    }
  })

  it('is a ROUTINE migration (not protected), unique in its number', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    expect(fs.readdirSync(MIG).filter(f => /^1324_/.test(f) && f !== FILE)).toEqual([])
    expect(fs.readdirSync(path.resolve(MIG, '../supabase/migrations')).filter(f => /^1324_/.test(f))).toEqual([])
  })
})

/**
 * CITATION-PASS2 / migration 1323 — STATIC contract (bg_remedies' integrity_check_sql, target_floor and volume_explanation are re-sealed
 * to the 316-row corpus left by decision OS-2026-10-05-CITATIONS: 25 unsourced remedy rows removed). The live proof (the real writer
 * replayed on a disposable PostgreSQL, the new check TRUE on the rebuilt corpus and FALSE on the old 341-row one) is
 * tests/unit/migrations/nirmana_bg_remedies_integrity_contract.test.ts (DB tier: migration 608 then 1323 on a disposable cluster). This file pins the text so a drive-by edit (a widened pin, a different
 * target, a dropped guard) is a deliberate, reviewed change.
 */
import { describe, it, expect } from 'vitest'
import crypto from 'crypto'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'
import { ASSETS } from '../../../scripts/seed/asset_registry_seed'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1323_bg_remedies_citation_pass2_integrity_reseal.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const FLAT = SQL.replace(/^--/gm, ' ').replace(/\s+/g, ' ')
const md5 = (s: string): string => crypto.createHash('md5').update(s).digest('hex')
const tagged = (s: string, tag: string): string => new RegExp('\\$' + tag + '\\$([\\s\\S]*?)\\$' + tag + '\\$').exec(s)?.[1] ?? ''

const OLD_MD5 = '8c521f10b57f6b06eb1a73e49e0c6b25'
const NEW_MD5 = 'd1d7fecb877612f948c09373cefd2ce6'
const OLD = tagged(fs.readFileSync(path.resolve(__dirname, '../../../supabase/migrations/608_nirmana_bg_remedies_integrity_contract.sql'), 'utf8'), 'integrity')
const NEW = tagged(SQL, 'ic')
// The exact replacements that turn migration 608's check into the citation-pass-2 check (each occurs once in OLD).
const REPLACEMENTS: Array<[string, string]> = [
  [`summary.total = 341`, `summary.total = 316`],
  [`summary.distinct_ids = 341`, `summary.distinct_ids = 316`],
  [`summary.id_md5 = '8bac868a1b9708eedee44a7266237d08'`, `summary.id_md5 = '476de921a54acbbfaae093a66121da48'`],
  [`planet_counts.value = '{"jupiter":40,"ketu":26,"mars":33,"mercury":26,"moon":50,"rahu":42,"saturn":39,"sun":53,"venus":32}'::jsonb`, `planet_counts.value = '{"jupiter":37,"ketu":26,"mars":32,"mercury":26,"moon":46,"rahu":30,"saturn":38,"sun":52,"venus":29}'::jsonb`],
  [`domain_counts.value = '{"career":12,"education":5,"general":260,"health":18,"marriage":29,"spirituality":6,"wealth":11}'::jsonb`, `domain_counts.value = '{"career":12,"education":5,"general":249,"health":17,"marriage":16,"spirituality":6,"wealth":11}'::jsonb`],
  [`type_counts.value = '{"ayurvedic":1,"behavioral":9,"charity":67,"gemstone":22,"homa":10,"japa":26,"mantra":68,"puja":76,"tantric":4,"vrata":35,"yantra":23}'::jsonb`, `type_counts.value = '{"ayurvedic":1,"behavioral":9,"charity":67,"gemstone":22,"homa":10,"japa":26,"mantra":65,"puja":54,"tantric":4,"vrata":35,"yantra":23}'::jsonb`],
  [`summary.uncategorized_rows = 256`, `summary.uncategorized_rows = 231`],
  [`summary.live_rows = 302`, `summary.live_rows = 277`],
]

describe('migration 1323 — static contract', () => {
  it("rebuilds the OLD text from migration 608's remedy_check", () => {
    expect(md5(OLD)).toBe(OLD_MD5)
    expect(OLD).toHaveLength(4601)
  })

  it('carries a NEW text that hashes to the md5 the file names', () => {
    expect(md5(NEW)).toBe(NEW_MD5)
    expect(NEW).toHaveLength(4601)
  })

  it('NEW = OLD with exactly the eight pin replacements; every other conjunct byte-identical', () => {
    let t = OLD
    for (const [a, b] of REPLACEMENTS) {
      expect(t.split(a)).toHaveLength(2)
      t = t.replace(a, b)
    }
    expect(NEW).toBe(t)
    expect(NEW).not.toContain('8bac868a1b9708eedee44a7266237d08')
  })

  it('is ONE md5-guarded UPDATE of one asset_registry row; no DDL, no corpus write, no transaction control', () => {
    expect(CODE.match(/\bUPDATE asset_registry\b/g)).toHaveLength(1)
    expect(CODE).toContain(`WHERE asset_id = 'bg_remedies'\n   AND target_floor = 341\n   AND md5(integrity_check_sql) = '${OLD_MD5}';`)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/m)
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|INSERT|DELETE)\b/im)
    expect(CODE.replace(/\$ic\$[\s\S]*?\$ic\$/, '')).not.toMatch(/brahma_remedy_corpus/i) // outside the check text the migration never names the corpus table
  })

  it('starts with lock_timeout, NOTICEs (never raises) on a foreign text, raises only when the update did not take', () => {
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
    expect(CODE).toContain('NO-OP')
    expect(CODE.match(/RAISE EXCEPTION/g)).toHaveLength(1)
    expect(CODE).toContain('update did not take')
  })

  it('sets the floor and volume the registry seed carries', () => {
    const asset = ASSETS.find(a => a.asset_id === 'bg_remedies')
    expect(asset?.target_floor).toBe(316)
    expect(CODE).toContain('target_floor = 316')
    const vol = /volume_explanation = '([^']*)'/.exec(CODE)?.[1]
    expect(vol).toBe(asset?.volume_explanation)
  })

  it('states the header facts: decision, number, pins, guard, trigger effect, order of operations, verification, rollback', () => {
    for (const n of ['OS-2026-10-05-CITATIONS', '1300, 1301, 1302', 'WHAT CHANGES IN THE CHECK', 'GUARD AND WHAT HAPPENS', 'ORDER OF OPERATIONS',
      'SERVING EFFECT AT APPLY', 'nirmana_registry_receipt_invalidation', 'VERIFICATION BY PRODUCTION STRUCTURE', 'ROLLBACK', OLD_MD5, NEW_MD5,
      'EXPECTED_CHANGE_bg_remedies_citation_pass2.json']) {
      expect(FLAT).toContain(n)
    }
  })

  it('is a ROUTINE migration (not protected), unique in its number', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    expect(fs.readdirSync(MIG).filter(f => /^1323_/.test(f) && f !== FILE)).toEqual([])
    expect(fs.readdirSync(path.resolve(MIG, '../supabase/migrations')).filter(f => /^1323_/.test(f))).toEqual([])
  })
})

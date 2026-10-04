/**
 * Pravāha B6.0 / Codex round 8 — STATIC contract checks on migration 1233 (the P1 period anchor, AM-21 part 2).
 * The live proof is tests/integration/gochara_b6_am21_p1_anchor.db.test.ts. Here: what the file may and may not contain,
 * and its wiring after 1232 in the protected window.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1233_gochara_p1_period_anchor.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')   // comments aside

describe('migration 1233 — static contract', () => {
  it('is additive: two columns and three CHECKs on the 1155 record table, nothing else', () => {
    expect(CODE.match(/ALTER TABLE/g) ?? []).toHaveLength(2)
    expect(CODE).toMatch(/ADD COLUMN period_anchor_lord\s+TEXT,\s*ADD COLUMN period_anchor_level TEXT/)
    for (const c of ['kgrr_period_anchor_pair_ck', 'kgrr_period_anchor_vocab_ck', 'kgrr_period_anchor_path_ck'])
      expect(CODE.match(new RegExp(`ADD CONSTRAINT ${c}`, 'g')) ?? []).toHaveLength(1)
    expect(CODE).not.toMatch(/\bCREATE\s+(TABLE|FUNCTION|TRIGGER|INDEX|OR REPLACE)\b/i)       // no new object, no replaced function
    expect(CODE).not.toMatch(/\bDROP\b/i)
    expect(CODE).not.toMatch(/\bGRANT\s|\bREVOKE\s|SECURITY DEFINER/)                         // table-level builder grants (1216) already cover the columns
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/m)
  })

  it('the closed vocabularies are exactly the nine lowercase grahas and md|ad|pd, and the path rule is set-exactly-for-P1', () => {
    const lords = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
    expect(CODE).toContain(`period_anchor_lord IN (${lords.map(l => `'${l}'`).join(',')})`)
    expect(CODE).toContain("period_anchor_level IN ('md','ad','pd')")
    expect(CODE).toContain("CHECK ((path_id = 'P1') = (period_anchor_lord IS NOT NULL))")
    expect(CODE).toContain('CHECK ((period_anchor_lord IS NULL) = (period_anchor_level IS NULL))')
  })

  it('the gate names its three refusals and runs before any DDL; presence checks follow', () => {
    for (const t of ['migration_1155_not_applied', 'migration_1233_already_applied', 'p1_records_exist_without_anchor']) expect(CODE).toContain(t)
    expect(CODE.indexOf('p1_records_exist_without_anchor')).toBeLessThan(CODE.indexOf('ALTER TABLE'))
    expect(CODE.lastIndexOf('post-apply check failed')).toBeGreaterThan(CODE.indexOf('ALTER TABLE'))
  })

  it('is unique across migration directories and wired into the protected window after 1232', () => {
    for (const d of [MIG, path.resolve(__dirname, '../../../python-sidecar/scripts/kala_gochara_cutover')].filter(x => fs.existsSync(x)))
      expect(fs.readdirSync(d).filter(f => /^1233_/.test(f) && f !== FILE)).toEqual([])
    const migrate = fs.readFileSync(path.resolve(__dirname, '../../../scripts/migrate.ts'), 'utf8')
    expect(migrate.indexOf(`'${FILE}'`)).toBeGreaterThan(migrate.indexOf("'1232_gochara_search_moon_scope_domain.sql'"))
    const deploy = fs.readFileSync(path.resolve(__dirname, '../../../../.github/workflows/deploy.yml'), 'utf8')
    expect(deploy.indexOf(`migrations+=(${FILE})`)).toBeGreaterThan(deploy.indexOf('migrations+=(1232_gochara_search_moon_scope_domain.sql)'))
  })
})

/**
 * Suvarna S-L2 / migration 1297 — STATIC contract (bo_cdlm_summary's registered count_sql widened to the three tables its writer
 * writes). The live proof (a disposable PostgreSQL cluster: 70 rows on a synthetic chart, md5 guard, idempotence, no trigger effect)
 * is python-sidecar/tests/test_migration_1297_cdlm_count_sql.py. This file pins the text so a drive-by edit is a deliberate change.
 */
import { describe, it, expect } from 'vitest'
import crypto from 'crypto'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1297_bo_cdlm_summary_count_sql_three_tables.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const FLAT = SQL.replace(/^--/gm, ' ').replace(/\s+/g, ' ')
const WRITER = fs.readFileSync(
  path.resolve(__dirname, '../../../python-sidecar/pipeline/orchestrator/writers/bo_cdlm_summary.py'), 'utf8')
const SEED = fs.readFileSync(path.resolve(__dirname, '../../../scripts/seed/asset_registry_seed.ts'), 'utf8')

const OLD_TEXT = 'SELECT count(*) FROM bodha_cdlm_chart_summary WHERE chart_id = $1'
const OLD_MD5 = 'a6ff09db0588b92339d631f422d69cc7'
const NEW_MD5 = '436138f8ef007f232680cf2673233019'
const md5 = (s: string): string => crypto.createHash('md5').update(s).digest('hex')
const NEW_TEXT = /\$cs\$([\s\S]*?)\$cs\$/.exec(SQL)?.[1] ?? ''
const TABLES = ['bodha_cdlm_chart_summary', 'bodha_cdlm_domain_rollups', 'bodha_cdlm_pattern_clusters']

describe('migration 1297 — static contract', () => {
  it('names the live OLD text md5 and the NEW text md5, and the NEW text hashes to what the file names', () => {
    expect(md5(OLD_TEXT)).toBe(OLD_MD5)
    expect(OLD_TEXT).toHaveLength(65)
    expect(md5(NEW_TEXT)).toBe(NEW_MD5)
    expect(NEW_TEXT).toHaveLength(292)
  })

  it('counts exactly the three tables the writer INSERTs into, each chart-scoped, with $1 appearing exactly once', () => {
    for (const t of TABLES) {
      expect(WRITER).toContain(`INSERT INTO public.${t} (`)
      expect(NEW_TEXT).toContain(`FROM ${t} `)
    }
    expect(NEW_TEXT.match(/\bFROM\s+(\w+)/gi)).toHaveLength(3)
    expect(NEW_TEXT.match(/\$1/g)).toHaveLength(1)
    expect(NEW_TEXT.endsWith('AS count')).toBe(true)
  })

  it('is ONE UPDATE of ONE column of ONE row, md5-guarded on the old text; the md5s appear in guard and post-check', () => {
    expect(CODE.match(/\bUPDATE asset_registry\b/g)).toHaveLength(1)
    expect(CODE).toContain(`WHERE asset_id = 'bo_cdlm_summary'\n  AND md5(count_sql) = '${OLD_MD5}';`)
    expect(CODE.match(/\bSET\s+(\w+)\s*=/gi)).toEqual(['SET count_sql ='])
    // none of the registry-invalidation trigger's columns is written
    for (const c of ['depends_on', 'natural_key_partition', 'health_probe', 'integrity_check_sql', 'target_floor', 'asset_kind',
      'asset_type', 'has_writer', 'is_active', 'target_table']) expect(CODE).not.toMatch(new RegExp(`\\bSET\\s+${c}\\b`))
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/m)
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|INSERT|DELETE)\b/im)
  })

  it('starts with lock_timeout, is a no-op (NOTICE) on a foreign text, and RAISES only when the update did not take', () => {
    expect(CODE.match(/\bSET LOCAL lock_timeout\b/g)).toHaveLength(1)
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
    expect(CODE).toContain('is not the text this migration was written against')
    expect(CODE).toContain('NO-OP, count_sql left as is')
    expect(CODE.match(/RAISE EXCEPTION/g)).toHaveLength(1)
    expect(CODE).toContain('update did not take')
  })

  it('states the header facts', () => {
    for (const n of ['THE DEFECT', 'GUARD AND WHAT HAPPENS WHEN IT DOES NOT MATCH', 'NO TRIGGER EFFECT', 'NOT CHANGED HERE',
      'VERIFICATION BY PRODUCTION STRUCTURE', 'ROLLBACK', 'nirmana_registry_receipt_invalidation', 'Trap 103',
      '5 + 60 rollups + 5 clusters = 70 rows', 'EXACTLY ONCE', OLD_MD5, NEW_MD5]) expect(FLAT).toContain(n)
  })

  it('the TypeScript seed carries the same NEW text (a fresh database matches the migration result)', () => {
    expect(SEED).toContain(`count_sql: '${NEW_TEXT}'`)
    expect(SEED).not.toContain(`count_sql: '${OLD_TEXT}',\n    size_sql: "SELECT pg_total_relation_size('bodha_cdlm_chart_summary')"`)
  })

  it('is a ROUTINE migration (not protected), unique, in the 1200-1299 range', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    const n = Number(FILE.slice(0, 4))
    expect(n).toBeGreaterThanOrEqual(1200)
    expect(n).toBeLessThanOrEqual(1299)
    expect(fs.readdirSync(MIG).filter(f => /^1297_/.test(f) && f !== FILE)).toEqual([])
  })
})

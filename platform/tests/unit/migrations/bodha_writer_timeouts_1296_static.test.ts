/**
 * Migration 1296 — STATIC contract (S-L2 fast path: raise writer_timeout_seconds for seven bodha writers, exact-value guarded).
 * The live proof (guarded update, idempotent replay, NOTICE path, trigger not fired, silent no-op caught) is
 * python-sidecar/tests/test_migration_1296_bodha_writer_timeouts.py on a disposable PostgreSQL. This file pins the text so a
 * drive-by edit (a widened id list, a dropped guard, a second SET column) is a deliberate, reviewed change, and pins the seed.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

const FILE = path.resolve(__dirname, '../../../migrations/1296_bodha_writer_timeouts_s_l2_rebuild.sql')
const SQL = fs.readFileSync(FILE, 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const FLAT = CODE.replace(/\s+/g, ' ')
const SEED = fs.readFileSync(path.resolve(__dirname, '../../../scripts/seed/asset_registry_seed.ts'), 'utf8')

const PLAN: Array<[string, number, number]> = [
  ['bo_arudha', 600, 7200],
  ['bo_nakshatra_semantic', 600, 7200],
  ['bo_special_lagna', 600, 7200],
  ['bo_vargottama_dhana', 600, 7200],
  ['bo_yantra_mechanism', 600, 7200],
  ['bo_grounding', 1800, 10800],
  ['bo_laksana_rerank', 1800, 10800],
]
const TRIGGER_COLUMNS = [
  'depends_on', 'natural_key_partition', 'health_probe', 'integrity_check_sql', 'target_floor',
  'asset_kind', 'asset_type', 'scope', 'has_writer', 'is_active', 'target_table',
]

describe('migration 1296 — static contract', () => {
  it('sets lock_timeout as the first statement', () => {
    expect(CODE.trim().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
  })

  it('carries exactly the seven (asset, old, new) tuples and no others', () => {
    const tuples = [...CODE.matchAll(/\('(bo_[a-z_]+)',\s*(\d+),\s*(\d+)\)/g)].map(m => [m[1], Number(m[2]), Number(m[3])])
    expect(tuples).toEqual(PLAN)
  })

  it('leaves bo_sudarshana and every other row untouched', () => {
    expect(CODE).not.toContain('bo_sudarshana')
    expect(CODE).not.toContain('bo_laksana,')
    expect(CODE).not.toContain('bo_bimba')
  })

  it('has exactly one UPDATE: one SET column, exact-value guard on the old value', () => {
    expect(CODE.match(/(?<!FOR )\bUPDATE\b/g)).toHaveLength(1)
    expect(FLAT).toContain(
      'UPDATE asset_registry SET writer_timeout_seconds = r.new_v WHERE asset_id = r.asset_id AND writer_timeout_seconds = r.old_v;',
    )
    expect(CODE.match(/\bSET\s+[a-z_]+\s*=/gi)?.map(s => s.replace(/\s+/g, ' '))).toEqual(['SET writer_timeout_seconds ='])
  })

  it('never writes a column the registry-receipt invalidation trigger watches', () => {
    const update = /UPDATE asset_registry[\s\S]*?;/.exec(CODE)?.[0] ?? ''
    for (const c of TRIGGER_COLUMNS) expect(update).not.toMatch(new RegExp(`\\b${c}\\b`))
  })

  it('has no DDL, no DELETE/INSERT, no transaction control, no temp table', () => {
    expect(CODE).not.toMatch(/\b(CREATE|ALTER|DROP|TRUNCATE|DELETE\s+FROM|INSERT\s+INTO|GRANT|REVOKE)\b/i)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/im)
  })

  it('raises only when a guard-matched UPDATE did not take; every other mismatch is a NOTICE', () => {
    expect(CODE.match(/RAISE EXCEPTION/g)).toHaveLength(1)
    expect(CODE).toMatch(/RAISE EXCEPTION '1296: % writer_timeout_seconds update did not take/)
    expect(CODE.match(/RAISE NOTICE/g)!.length).toBeGreaterThanOrEqual(3)
  })

  it('verifies after the UPDATE, never before it', () => {
    expect(CODE.indexOf('did not take')).toBeGreaterThan(CODE.indexOf('UPDATE asset_registry'))
  })
})

describe('migration 1296 — seed carries the same values', () => {
  it('each of the seven seed blocks holds the NEW value; bo_sudarshana carries none', () => {
    for (const [asset, , next] of PLAN) {
      const start = SEED.indexOf(`asset_id: '${asset}',\n`)
      expect(start, asset).toBeGreaterThan(-1)
      const block = SEED.slice(start, SEED.indexOf('\n  },', start))
      expect(block, asset).toContain(`writer_timeout_seconds: ${next},`)
    }
    const s = SEED.indexOf("asset_id: 'bo_sudarshana',\n")
    expect(SEED.slice(s, SEED.indexOf('\n  },', s))).not.toContain('writer_timeout_seconds')
  })
})

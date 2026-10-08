/**
 * Migration 1336 — STATIC contract (raise writer_timeout_seconds for bo_samskara 10800 -> 18000; only ever raises, never lowers).
 * Pins the exact asset and value so a widened list, a lowered value or a second SET column is a deliberate, reviewed change,
 * and pins the seed. Live replay/idempotency was proven on a throwaway PostgreSQL 15 (see PR body).
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

const SQL = fs.readFileSync(path.resolve(__dirname, '../../../migrations/1336_bo_samskara_writer_timeout_budget.sql'), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const FLAT = CODE.replace(/\s+/g, ' ')
const SEED = fs.readFileSync(path.resolve(__dirname, '../../../scripts/seed/asset_registry_seed.ts'), 'utf8')

const PLAN: Array<[string, number]> = [['bo_samskara', 18000]]
const OLD_FLOOR: Record<string, number> = { bo_samskara: 10800 }
const TRIGGER_COLUMNS = [
  'depends_on', 'natural_key_partition', 'health_probe', 'integrity_check_sql', 'target_floor',
  'asset_kind', 'asset_type', 'scope', 'has_writer', 'is_active', 'target_table',
]

describe('migration 1336 — static contract', () => {
  it('sets lock_timeout then statement_timeout first', () => {
    expect(CODE.trim().startsWith("SET LOCAL lock_timeout = '5s';\nSET LOCAL statement_timeout = '60s';")).toBe(true)
  })

  it('carries exactly the one (asset, new) tuple and no others', () => {
    const tuples = [...CODE.matchAll(/\('([a-z_]+)',\s*(\d+)\)/g)].map(m => [m[1], Number(m[2])])
    expect(tuples).toEqual(PLAN)
  })

  it('never lowers a budget: the new value exceeds the registry value read on production', () => {
    for (const [a, v] of PLAN) expect(v, a).toBeGreaterThan(OLD_FLOOR[a])
    expect(FLAT).toContain('writer_timeout_seconds IS NULL OR writer_timeout_seconds < r.new_v')
    expect(FLAT).toContain('ELSIF cur >= r.new_v THEN')
  })

  it('has exactly one UPDATE with one SET column', () => {
    expect(CODE.match(/(?<!FOR )\bUPDATE\b/g)).toHaveLength(1)
    expect(CODE.match(/\bSET\s+[a-z_]+\s*=/gi)?.map(s => s.replace(/\s+/g, ' '))).toEqual(['SET writer_timeout_seconds ='])
  })

  it('never writes a column the registry-receipt invalidation trigger watches', () => {
    const update = /UPDATE asset_registry[\s\S]*?;/.exec(CODE)?.[0] ?? ''
    for (const c of TRIGGER_COLUMNS) expect(update).not.toMatch(new RegExp(`\\b${c}\\b`))
  })

  it('raises on a missing or inactive row and on an UPDATE that did not take', () => {
    expect(CODE.match(/RAISE EXCEPTION/g)).toHaveLength(3)
    expect(CODE).toContain("'1336: % has no asset_registry row'")
    expect(CODE).toContain("'1336: % is not active in asset_registry'")
    expect(CODE).toContain('did not take')
  })

  it('has no DDL, no DELETE/INSERT, no transaction control', () => {
    expect(CODE).not.toMatch(/\b(CREATE|ALTER|DROP|TRUNCATE|DELETE\s+FROM|INSERT\s+INTO|GRANT|REVOKE)\b/i)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/im)
  })
})

describe('migration 1336 — seed carries the same value', () => {
  it('the bo_samskara seed block holds the NEW value', () => {
    for (const [asset, next] of PLAN) {
      const start = SEED.indexOf(`asset_id: '${asset}',\n`)
      expect(start, asset).toBeGreaterThan(-1)
      const block = SEED.slice(start, SEED.indexOf('\n  },', start))
      expect(block, asset).toContain(`writer_timeout_seconds: ${next},`)
    }
  })
})

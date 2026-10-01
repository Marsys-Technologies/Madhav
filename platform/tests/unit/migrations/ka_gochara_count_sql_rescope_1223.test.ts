import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

// Static contract for migration 1223 (Pravāha TASK C1, steward
// M20261001T212520-1e31): re-scope asset_registry.count_sql for
// asset_id='ka_gochara' from the 1091 text (generation '4.0') to '4.1' and
// nothing else. The behavioural proof (before/after/no-op/raises) is the DB
// suite tests/integration/ka_gochara_count_sql_rescope_1223.db.test.ts.
const sql = readFileSync(
  resolve(__dirname, '../../../migrations/1223_a26_ka_gochara_count_sql_rescope_41.sql'),
  'utf8'
)
const code = sql
  .split('\n')
  .filter((l) => !l.trim().startsWith('--'))
  .join('\n')

const C_1091 =
  "SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='4.0'"
const C_41 =
  "SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='4.1'"

describe('migration 1223 — ka_gochara count_sql re-scope 4.0 → 4.1', () => {
  it("embeds the exact 1091 '4.0' text as the expected prior state and the '4.1' text as the target", () => {
    // SQL literal quoting: ' is doubled inside the DO block constants.
    expect(code).toContain(C_1091.replaceAll("'", "''"))
    expect(code).toContain(C_41.replaceAll("'", "''"))
  })

  it('issues exactly one UPDATE: asset_registry, SET count_sql only, WHERE asset_id = ka_gochara only', () => {
    const updates = [...code.matchAll(/UPDATE\s+(\S+)\s+SET\s+([\s\S]+?)\s+WHERE\s+([\s\S]+?);/gi)]
    expect(updates).toHaveLength(1)
    const [, table, setClause, whereClause] = updates[0]!
    expect(table).toBe('asset_registry')
    expect(setClause.replace(/\s+/g, ' ').trim()).toBe('count_sql = c_41')
    expect(whereClause.replace(/\s+/g, ' ').trim()).toBe("asset_id = 'ka_gochara'")
  })

  it('touches no other column, row, or table — no target_table/integrity_check_sql/clear_tables/depends_on writes', () => {
    expect(code).not.toMatch(/SET\s+[^;]*\b(target_table|integrity_check_sql|clear_tables|depends_on|target_floor|size_sql)\b/i)
    expect(code).not.toMatch(/\b(DELETE|INSERT\s+INTO|ALTER\s+TABLE|CREATE\s+TABLE|DROP\s+TABLE|GRANT|REVOKE)\b/i)
    expect(code).not.toMatch(/asset_id\s*=\s*'(?!ka_gochara')/)
  })

  it('fails closed: RAISEs when the current count_sql is not exactly what 1091 wrote', () => {
    expect(code).toMatch(/IS DISTINCT FROM c_1091[\s\S]*?RAISE EXCEPTION/)
    expect(code).toMatch(/unexpected ka_gochara count_sql/)
  })

  it('is idempotent: already-4.1 short-circuits before any write', () => {
    const earlyReturn = code.indexOf('IF r.count_sql = c_41')
    const update = code.indexOf('UPDATE asset_registry')
    expect(earlyReturn).toBeGreaterThan(-1)
    expect(update).toBeGreaterThan(-1)
    expect(earlyReturn).toBeLessThan(update)
    expect(code.slice(earlyReturn, update)).toMatch(/RETURN;/)
  })

  it("carries 1091's conjunct (j) post-gate: target_table must still equal the count_sql relation", () => {
    expect(code).toContain("substring(r.count_sql from 'FROM ([a-z0-9_]+)')")
    expect(code).toMatch(/NOT LIKE '%generation=''4\.1''%'[\s\S]*?RAISE EXCEPTION|RAISE EXCEPTION '1223 gate failed: count_sql not re-scoped/)
  })

  it('stays out of the capability-census digest-spec scan (keeps the census byte-identical)', () => {
    // scripts/generate_capability_estate_census.ts scans every migration file whose
    // raw text contains this token; assembled so this test file is not a scanned migration.
    const token = ['asset', 'output', 'digest', 'specs'].join('_')
    expect(sql).not.toContain(token)
  })
})

/**
 * Pravāha G8 (steward GAPS-G8-G9) — STATIC contract checks on migration 1306 (the expected class census at seal).
 * The live proof is python-sidecar/tests/l3/gochara/test_g8_class_census.py (25 of 26 refused at the function and at the seal, 26 of 26 passes,
 * the pre-1306 function lets 25 of 26 through). Here: the replacement of the 1232 completeness function is proven to differ from the accepted
 * function by EXACTLY the two intended edits (one declaration line, one appended block), and the protected-window wiring.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

const MIG = path.resolve(__dirname, '../../../migrations')
const M1232 = fs.readFileSync(path.join(MIG, '1232_gochara_search_moon_scope_domain.sql'), 'utf8')
const M1306 = fs.readFileSync(path.join(MIG, '1306_gochara_expected_class_census.sql'), 'utf8')

function fn(sql: string, name: string): string {
  const a = sql.indexOf(`CREATE OR REPLACE FUNCTION public.${name}`)
  expect(a, name).toBeGreaterThan(-1)
  const b = sql.indexOf('$$;', sql.indexOf('LANGUAGE plpgsql', a)) + 3
  return sql.slice(a, b)
}

describe('migration 1306 — static contract', () => {
  it('replaces the 1232 completeness function with EXACTLY two edits (one declaration line, one appended block)', () => {
    const old = fn(M1232, 'ka_gochara_search_completeness_violations')
    const neu = fn(M1306, 'ka_gochara_search_completeness_violations')
    const DECL = '\n  census_vec jsonb; pinned_classes text[]; claimed_classes text[];'
    expect(neu.split(DECL)).toHaveLength(2)
    const start = neu.indexOf('\n\n  -- G8 (1306): the EXPECTED CLASS CENSUS')
    const end = neu.lastIndexOf('\nEND;\n$$;')
    expect(start).toBeGreaterThan(-1)
    expect(end).toBeGreaterThan(start)
    // undo edit 1 (the declaration) and edit 2 (the appended block) -> must be byte-identical to the 1232 function
    expect(neu.replace(DECL, '').slice(0, start - DECL.length) + neu.slice(end)).toBe(old)
    // the 1232 refusals are still there, untouched, and the census comes AFTER the Moon-scope call
    for (const keep of ["'missing_inputs_present'", "'obligation_uncovered'", "'verification_missing_or_mismatch'", 'ka_gochara_search_moon_scope_violations(p_chart, p_generation);']) expect(neu).toContain(keep)
    // the census block names exactly its four violations
    const block = neu.slice(start, end)
    for (const v of ['expected_class_list_missing', 'expected_class_list_malformed', 'class_missing', 'class_not_pinned']) expect(block).toContain(`'${v}'`)
  })

  it('creates nothing, grants nothing, replaces ONE function; no BEGIN/COMMIT; protected gate pins the 1232 body by sha256', () => {
    expect(M1306).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/m)
    expect(M1306.match(/CREATE OR REPLACE FUNCTION/g) ?? []).toHaveLength(1)
    expect(M1306.match(/CREATE (TABLE|TRIGGER|INDEX|OR REPLACE TRIGGER)/g) ?? []).toHaveLength(0)
    expect(M1306).not.toMatch(/\bGRANT\s|\bREVOKE\s|SECURITY DEFINER/)
    for (const g of ['migration_1232_not_applied', 'migration_1240_not_applied', 'completeness_function_is_not_the_1232_body', 'migration_1306_already_applied', 'preflight 1306 BLOCKED',
      '63d9e7e737b020784ca52c4cd06e66e74434c20b60d9b9d65834f4e1c773f1fb']) expect(M1306).toContain(g)
    expect(fn(M1306, 'ka_gochara_search_completeness_violations')).toContain('SET search_path = pg_catalog, public')   // invoker, pinned search_path, as 1232
  })

  it('1306 is unique across migration directories and wired into the protected window after 1240', () => {
    const dirs = [MIG, path.resolve(__dirname, '../../../supabase/migrations')].filter((d) => fs.existsSync(d))
    for (const d of dirs) expect(fs.readdirSync(d).filter((f) => /^1306_/.test(f) && f !== '1306_gochara_expected_class_census.sql')).toEqual([])
    const migrate = fs.readFileSync(path.resolve(__dirname, '../../../scripts/migrate.ts'), 'utf8')
    expect(migrate.indexOf("'1306_gochara_expected_class_census.sql'")).toBeGreaterThan(migrate.indexOf("'1240_gochara_window_verification_gate.sql'"))
    const deploy = fs.readFileSync(path.resolve(__dirname, '../../../../.github/workflows/deploy.yml'), 'utf8')
    expect(deploy.indexOf('migrations+=(1306_gochara_expected_class_census.sql)')).toBeGreaterThan(deploy.indexOf('migrations+=(1240_gochara_window_verification_gate.sql)'))
  })
})

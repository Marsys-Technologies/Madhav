/**
 * Pravāha B6.0 / Codex round 6 R2 — STATIC contract checks on migration 1232 (AM-14 Moon-scope accounting).
 * The live proof is tests/integration/gochara_b6_am14_moon_domain.db.test.ts. Here: the replacement of the 1206
 * completeness function is proven to differ from the accepted function by EXACTLY the two intended edits (so
 * `missing_inputs_present` / `obligation_uncovered` are not weakened by a stray change), and the wiring.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

const MIG = path.resolve(__dirname, '../../../migrations')
const M1206 = fs.readFileSync(path.join(MIG, '1206_gochara_search_inventory_completeness.sql'), 'utf8')
const M1232 = fs.readFileSync(path.join(MIG, '1232_gochara_search_moon_scope_domain.sql'), 'utf8')

function fn(sql: string, name: string): string {
  const a = sql.indexOf(`CREATE OR REPLACE FUNCTION public.${name}`)
  expect(a, name).toBeGreaterThan(-1)
  const b = sql.indexOf('$$;', sql.indexOf('LANGUAGE plpgsql', a)) + 3
  return sql.slice(a, b)
}

describe('migration 1232 — static contract', () => {
  it('replaces the 1206 completeness function with EXACTLY two edits (state list ×2, scope-check call)', () => {
    const old = fn(M1206, 'ka_gochara_search_completeness_violations')
    const neu = fn(M1232, 'ka_gochara_search_completeness_violations')
    const STATES = "v.state IN ('searched_complete','searched_unqualified')"
    expect(old.split(STATES)).toHaveLength(3)                                     // two occurrences in 1206
    const NEW_STATES = "v.state IN ('searched_complete','searched_unqualified','excluded_moon_tier')"
    expect(neu.split(NEW_STATES)).toHaveLength(3)                                 // the same two occurrences, extended
    // undo edit 1 (state list) and edit 2 (the appended scope-check call + its comment) -> must be byte-identical to 1206
    const CALL = '  -- AM-14 (1232): the Moon-scope accounting — stored exclusion = derived Moon-resolved domain; scope bound to the manifest\n' +
                 '  RETURN QUERY SELECT * FROM public.ka_gochara_search_moon_scope_violations(p_chart, p_generation);\n'
    expect(neu.split(CALL)).toHaveLength(2)
    expect(neu.split(NEW_STATES).join(STATES).replace('\n' + CALL, '')).toBe(old)
    // the two refusals the contract forbids weakening are still there, untouched
    for (const keep of ["'missing_inputs_present'", "'obligation_uncovered'", "v.state = 'missing_inputs'"]) expect(neu).toContain(keep)
  })

  it('adds exactly one interval state and nothing else to the table; no BEGIN/COMMIT; protected-window gate present', () => {
    expect(M1232).toContain("CHECK (state IN ('searched_complete','searched_unqualified','missing_inputs','excluded_moon_tier'))")
    expect(M1232).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/m)
    for (const g of ['migration_1206_not_applied', 'migration_1232_already_applied', 'preflight 1232 BLOCKED']) expect(M1232).toContain(g)
    expect(M1232.match(/CREATE TABLE/g) ?? []).toHaveLength(0)                    // additive: no new table
    expect(M1232).not.toMatch(/\bGRANT\s|\bREVOKE\s|SECURITY DEFINER/)  // grants nothing, no definer bridge
  })

  it('new functions are invoker-security with a pinned search_path', () => {
    for (const name of ['ka_gochara_search_moon_resolved_domain', 'ka_gochara_search_moon_scope_violations', 'ka_gochara_search_completeness_violations']) {
      expect(fn(M1232.replace('LANGUAGE sql STABLE', 'LANGUAGE plpgsql STABLE'), name), name).toContain('SET search_path = pg_catalog, public')
    }
  })

  it('1232 is unique across migration directories and wired into the protected window after 1206', () => {
    const dirs = [MIG, path.resolve(__dirname, '../../../python-sidecar/scripts/kala_gochara_cutover')].filter(d => fs.existsSync(d))
    for (const d of dirs) expect(fs.readdirSync(d).filter(f => /^1232_/.test(f) && f !== '1232_gochara_search_moon_scope_domain.sql')).toEqual([])
    const migrate = fs.readFileSync(path.resolve(__dirname, '../../../scripts/migrate.ts'), 'utf8')
    expect(migrate.indexOf('1232_gochara_search_moon_scope_domain.sql')).toBeGreaterThan(migrate.indexOf('1206_gochara_search_inventory_completeness.sql'))
    const deploy = fs.readFileSync(path.resolve(__dirname, '../../../../.github/workflows/deploy.yml'), 'utf8')
    expect(deploy.indexOf('migrations+=(1232_gochara_search_moon_scope_domain.sql)')).toBeGreaterThan(deploy.indexOf('migrations+=(1206_gochara_search_inventory_completeness.sql)'))
  })
})

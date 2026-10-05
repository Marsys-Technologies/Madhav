/**
 * Pravāha G12 route 1 (steward G12-ROUTE1) — STATIC contract checks on migration 1305 (the search-input snapshot owns a copy of the L1 rows it consumed).
 * The live proof is python-sidecar/tests/l3/gochara/test_g12_snapshot_copy.py (an L1 rebuild with new row ids and a new build id is metadata-only drift and the
 * generation still verifies; a changed value is a hard drift; a moved boundary is named). Here: the replacement of the 1232 completeness function differs from
 * the accepted function by EXACTLY the drift block, the gate pins the two replaced functions, the migration is additive, and the protected-window wiring.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

const MIG = path.resolve(__dirname, '../../../migrations')
const M1232 = fs.readFileSync(path.join(MIG, '1232_gochara_search_moon_scope_domain.sql'), 'utf8')
const M1305 = fs.readFileSync(path.join(MIG, '1305_gochara_snapshot_owns_l1_copy.sql'), 'utf8')

function fn(sql: string, name: string): string {
  const a = sql.indexOf(`CREATE OR REPLACE FUNCTION public.${name}`)
  expect(a, name).toBeGreaterThan(-1)
  const b = sql.indexOf('$$;', sql.indexOf('RETURN QUERY SELECT * FROM public.ka_gochara_search_moon_scope_violations', a)) + 3
  return sql.slice(a, b)
}

describe('migration 1305 — static contract', () => {
  it('replaces the 1232 completeness function with EXACTLY one block changed (the L1 drift check)', () => {
    const old = fn(M1232, 'ka_gochara_search_completeness_violations')
    const neu = fn(M1305, 'ka_gochara_search_completeness_violations')
    const oldStart = old.indexOf('    live_l1 := public.ka_gochara_search_l1_facts_digest')
    const oldEnd = old.indexOf('    FOREACH e IN ARRAY snap.av_declarations LOOP')
    const newStart = neu.indexOf('    IF snap.consumed_fact_rows IS NULL OR snap.consumed_dasha_rows IS NULL THEN')
    const newEnd = neu.indexOf('    FOREACH e IN ARRAY snap.av_declarations LOOP')
    expect(oldStart).toBeGreaterThan(-1); expect(newStart).toBeGreaterThan(-1)
    // undo the one edit -> byte-identical to the 1232 function
    expect(neu.slice(0, newStart) + old.slice(oldStart, oldEnd) + neu.slice(newEnd)).toBe(old)
    // the legacy branch keeps the 1206 statements verbatim (so a snapshot without a copy is judged as before)
    const block = neu.slice(newStart, newEnd).replace(/\s+/g, ' ')
    for (const keep of ['live_l1 := public.ka_gochara_search_l1_facts_digest(p_chart, snap.consumed_fact_ids);', 'live_dasha := public.ka_gochara_search_dasha_digest(p_chart, snap.consumed_dasha_row_ids);']) expect(block).toContain(keep)
    for (const neuName of ['ka_gochara_search_facts_live_copy', 'ka_gochara_search_dasha_live_copy', "'content'"]) expect(block).toContain(neuName)
    for (const keep of ["'missing_inputs_present'", "'obligation_uncovered'", "'verification_missing_or_mismatch'", 'ka_gochara_search_moon_scope_violations(p_chart, p_generation);']) expect(neu).toContain(keep)
  })

  it('is ADDITIVE: no DROP, no table rewrite, no BEGIN/COMMIT, invoker-rights functions, a NOT VALID check, one INSERT trigger', () => {
    expect(M1305).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/m)
    expect(M1305).not.toMatch(/\bDROP\s+(TABLE|COLUMN|FUNCTION|TRIGGER|CONSTRAINT)\b/i)
    expect(M1305).not.toMatch(/SECURITY DEFINER/)
    expect(M1305.match(/ADD COLUMN/g) ?? []).toHaveLength(4)
    expect(M1305).toMatch(/ADD CONSTRAINT kgsis_l1_copy_ck[\s\S]*?NOT VALID;/)
    expect(M1305.match(/CREATE TRIGGER/g) ?? []).toHaveLength(1)
    expect(M1305).toContain('BEFORE INSERT ON public.ka_gochara_search_input_snapshot')
    // exactly the two replaced functions are 1232 names; every other CREATE OR REPLACE is a NEW 1305 function
    const created = [...M1305.matchAll(/CREATE OR REPLACE FUNCTION public\.(\w+)/g)].map((m) => m[1]).sort()
    expect(created).toEqual(['ka_gochara_search_completeness_violations', 'ka_gochara_search_copy_digest', 'ka_gochara_search_dasha_copy', 'ka_gochara_search_dasha_element',
      'ka_gochara_search_dasha_live_copy', 'ka_gochara_search_dasha_path', 'ka_gochara_search_facts_copy', 'ka_gochara_search_facts_live_copy',
      'ka_gochara_search_input_snapshot_copy_check', 'ka_gochara_search_moon_resolved_domain'])
    expect(M1232).not.toContain('ka_gochara_search_copy_digest')
  })

  it('the gate refuses by name: applied twice, 1232 missing, G8 first, and either replaced function not being the 1232 body (sha256 pinned)', () => {
    for (const g of ['migration_1305_already_applied', 'migration_1232_not_applied', 'g8_1306_applied_first', 'completeness_function_is_not_the_1232_body',
      'moon_domain_function_is_not_the_1232_body', 'preflight 1305 BLOCKED', '63d9e7e737b020784ca52c4cd06e66e74434c20b60d9b9d65834f4e1c773f1fb',
      '707bd37ce48a3c5fbaf2de881bc7554d97bc81fc1a09a6534d36b4ec5f09cf07']) expect(M1305).toContain(g)
  })

  it('grants EXECUTE on the seven copy functions to the three roles, only if they exist; no table grant', () => {
    expect(M1305).toContain("ARRAY['data_plane_builder', 'gochara_verifier', 'gochara_sealer']")
    expect(M1305).toContain('IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r)')
    expect(M1305).not.toMatch(/GRANT\s+(SELECT|INSERT|UPDATE|DELETE)/)
  })

  it('1305 is unique across migration directories and wired into the protected window after 1240', () => {
    const dirs = [MIG, path.resolve(__dirname, '../../../supabase/migrations')].filter((d) => fs.existsSync(d))
    for (const d of dirs) expect(fs.readdirSync(d).filter((f) => /^1305_/.test(f) && f !== '1305_gochara_snapshot_owns_l1_copy.sql')).toEqual([])
    const migrate = fs.readFileSync(path.resolve(__dirname, '../../../scripts/migrate.ts'), 'utf8')
    expect(migrate.indexOf("'1305_gochara_snapshot_owns_l1_copy.sql'")).toBeGreaterThan(migrate.indexOf("'1240_gochara_window_verification_gate.sql'"))
    const deploy = fs.readFileSync(path.resolve(__dirname, '../../../../.github/workflows/deploy.yml'), 'utf8')
    expect(deploy.indexOf('migrations+=(1305_gochara_snapshot_owns_l1_copy.sql)')).toBeGreaterThan(deploy.indexOf('migrations+=(1240_gochara_window_verification_gate.sql)'))
  })

  it('the readback SQL is read-only and checks the same objects', () => {
    const rb = fs.readFileSync(path.resolve(__dirname, '../../../scripts/gochara/readback_1305_snapshot_copy.sql'), 'utf8')
    expect(rb).toContain('BEGIN READ ONLY;')
    expect(rb.replace(/--.*$/gm, '')).not.toMatch(/\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|GRANT|REVOKE|TRUNCATE)\b/i)
    for (const o of ['kgsis_l1_copy_ck', 'ka_gochara_search_input_snapshot_3_copy_check', 'ka_gochara_search_dasha_live_copy', 'consumed_dasha_rows', 'legacy_snapshots']) expect(rb).toContain(o)
  })
})

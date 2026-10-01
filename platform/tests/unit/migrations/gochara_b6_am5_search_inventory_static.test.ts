// @vitest-environment node
/**
 * Pravāha B6.0 / F-1 — STATIC contract checks on migration 1206 (AM-5 search-completeness
 * storage + seal checks), its preflight, the runner's protected-file refusal and the deploy
 * window, asserted against the on-disk sources (CLAUDE.md §N.8: the detector reads what
 * ships). Live-DB behaviour (the adversarial matrix, the seal lifecycle) is covered by
 * tests/integration/gochara_b6_am5_search_inventory.db.test.ts.
 *
 * Source: GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT §AM-5 (accepted at pre-gate, Codex v1.4);
 * steward M20261001T201843-f8e5 item 3. 1153–1157 are applied and never edited: this file
 * asserts the migration only ADDS (no ALTER/DROP/REPLACE of an applied object).
 */
import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS, assertGeneralRunnerMayApplyPublicSchema } from '../../../scripts/migrate'

const MIGRATIONS_DIR = path.resolve(process.cwd(), 'migrations')
const SUPABASE_MIGRATIONS_DIR = path.resolve(process.cwd(), 'supabase/migrations')
const PREFLIGHT_DIR = path.resolve(process.cwd(), '../platform/python-sidecar/scripts/kala_gochara_cutover')
const DEPLOY_YML = path.resolve(process.cwd(), '../.github/workflows/deploy.yml')

const M1206 = '1206_gochara_search_inventory_completeness.sql'
const P1206 = 'preflight_1206_search_inventory_completeness.sql'
const SIX_TABLES = [
  'ka_gochara_search_input_snapshot', 'ka_gochara_search_inventory', 'ka_gochara_search_path_pin',
  'ka_gochara_search_obligation', 'ka_gochara_search_interval', 'ka_gochara_search_inventory_verification',
] as const

const read = (dir: string, name: string): string => fs.readFileSync(path.join(dir, name), 'utf8')
const executableSql = (sql: string): string =>
  sql.split('\n').filter(l => !l.trimStart().startsWith('--')).join('\n')
function gateBlock(sql: string): string {
  const start = sql.indexOf('DO $$')
  const end = sql.indexOf('$$;', start)
  expect(start).toBeGreaterThan(-1)
  expect(end).toBeGreaterThan(start)
  return sql.slice(start, end + 3)
}

describe('B6.0 F-1 migration 1206 (AM-5 search completeness) — static contract', () => {
  const sql = read(MIGRATIONS_DIR, M1206)
  const exec = executableSql(sql)

  it('the migration and its preflight exist; 1206 is unique across both migration directories', () => {
    expect(fs.existsSync(path.join(PREFLIGHT_DIR, P1206))).toBe(true)
    for (const dir of [MIGRATIONS_DIR, SUPABASE_MIGRATIONS_DIR]) {
      expect(fs.readdirSync(dir).filter(f => /^1206_/.test(f) && f !== M1206), `duplicate 1206 in ${dir}`).toEqual([])
    }
  })

  it('the gate is byte-identical to its preflight DO block (F8/F9) and the preflight is read only', () => {
    const pre = read(PREFLIGHT_DIR, P1206)
    expect(gateBlock(sql)).toBe(gateBlock(pre))
    expect(pre).not.toMatch(/^\s*(CREATE|ALTER|DROP|INSERT|UPDATE|DELETE|GRANT|REVOKE)\b/im)
  })

  it('no BEGIN/COMMIT — migrate.ts owns the one transaction; search_path and timeouts pinned', () => {
    expect(sql).not.toMatch(/^\s*BEGIN\s*;/m)
    expect(sql).not.toMatch(/^\s*COMMIT\s*;?\s*$/m)
    expect(sql).toContain('SET LOCAL search_path = public, pg_catalog;')
    expect(sql).toContain("SET LOCAL lock_timeout = '5s';")
    expect(sql).toContain('post-apply check failed')
  })

  it('the gate is ordered: requires 1157 recorded, refuses 1206 re-application and pre-existing objects', () => {
    const g = gateBlock(sql)
    expect(g).toContain("'1157_'")
    expect(g).toContain("'1206_'")
    for (const t of ['prerequisite_migration_not_applied', 'migration_already_applied', 'object_already_exists',
                     'table_missing', 'function_missing']) expect(g).toContain(t)
    for (const t of SIX_TABLES) expect(g, `gate lists ${t}`).toContain(`public.${t}`)
  })

  it('the migration only ADDS: no ALTER/DROP of an applied object, no CREATE OR REPLACE of a pre-1206 function, no edit to 1153–1157', () => {
    // executable text only: the header's ROLLBACK prose names DROP statements
    expect(exec).not.toMatch(/^\s*ALTER\s+TABLE\b/im)
    expect(exec).not.toMatch(/^\s*DROP\b/im)
    const replaced = [...exec.matchAll(/CREATE OR REPLACE FUNCTION public\.(\w+)/g)].map(m => m[1]!)
    expect(replaced.length).toBeGreaterThan(8)
    const applied = ['1153_gochara_sky_event_substrate.sql', '1154_gochara_rule_path_registry.sql',
      '1155_gochara_relationship_record.sql', '1156_gochara_eval_window.sql', '1157_gochara_av_polarity_declaration.sql']
      .map(f => read(MIGRATIONS_DIR, f)).join('\n')
    for (const fn of replaced) {
      expect(applied, `function ${fn} must not already exist in 1153–1157`).not.toContain(`FUNCTION public.${fn}(`)
    }
    // the one touch on an existing relation: a NEW trigger on the seal table, named to fire AFTER the applied guard
    const trg = /CREATE TRIGGER (\w+)\s+BEFORE INSERT ON public\.ka_gochara_generation_seal/.exec(exec)
    expect(trg?.[1]).toBe('ka_gochara_generation_seal_z_search_complete')
    expect('ka_gochara_generation_seal_write_guard' < trg![1]!).toBe(true)
  })

  it('creates exactly the six chart-scoped tables, each with the lock/immutability/truncate triggers', () => {
    const created = [...exec.matchAll(/CREATE TABLE public\.(\w+)/g)].map(m => m[1]!).sort()
    expect(created).toEqual([...SIX_TABLES].sort())
    expect(exec).toContain("t || '_0_statement_lock'")
    expect(exec).toContain('ka_gochara_chart_statement_lock()')
    expect(exec).toContain('ka_gochara_search_write_guard()')
    expect(exec).toContain('ka_gochara_refuse_truncate()')
    for (const t of ['ka_gochara_search_path_pin', 'ka_gochara_search_obligation']) {
      expect(exec).toContain(`CREATE TRIGGER ${t}_2_sealed_rule_check`)
    }
    expect(exec).toContain('ka_gochara_require_sealed_rule_path()')
  })

  it('lock order: the write guard takes the chart key BEFORE the global SHARED key, and the seal trigger repeats it', () => {
    const wg = exec.slice(exec.indexOf('FUNCTION public.ka_gochara_search_write_guard()'))
    expect(wg.indexOf('ka_gochara_lock_chart(ch)')).toBeGreaterThan(-1)
    expect(wg.indexOf('ka_gochara_lock_chart(ch)')).toBeLessThan(wg.indexOf('ka_gochara_lock_global_shared()'))
    const sg = exec.slice(exec.indexOf('FUNCTION public.ka_gochara_generation_seal_search_guard()'))
    expect(sg.indexOf('ka_gochara_lock_chart(NEW.chart_id)')).toBeLessThan(sg.indexOf('ka_gochara_lock_global_shared()'))
    expect(exec).not.toContain('ka_gochara_lock_global()')   // never the EXCLUSIVE key from a chart transaction
  })

  it('every violation kind the draft names is detectable in the first-publication function; the replay branch is integrity-only', () => {
    const first = exec.slice(exec.indexOf('FUNCTION public.ka_gochara_search_completeness_violations'),
                             exec.indexOf('FUNCTION public.ka_gochara_search_replay_violations'))
    for (const k of ['partition_without_inventory', 'inventory_without_partition', 'registry_unaccounted_path',
      'committed_set_mismatch', 'inventory_digest_mismatch', 'inventory_not_finalised', 'obligation_uncovered',
      'missing_inputs_present', 'partition_overclaims', 'input_snapshot_mismatch', 'input_snapshot_drift',
      'input_vector_mismatch', 'horizon_manifest_mismatch', 'verification_missing_or_mismatch']) {
      expect(first, `violation ${k}`).toContain(`'${k}'`)
    }
    const replay = exec.slice(exec.indexOf('FUNCTION public.ka_gochara_search_replay_violations'),
                              exec.indexOf('FUNCTION public.ka_gochara_generation_seal_search_guard'))
    for (const k of ['registry_unaccounted_path', 'input_snapshot_drift', 'partition_overclaims'])
      expect(replay, `replay branch must NOT apply ${k}`).not.toContain(k)
    expect(replay).toContain('inventory_digest_mismatch')
    expect(replay).toContain('verification_missing_or_mismatch')
  })

  it('the pin CHECKs carry the F-2 evidence rules: closed reasons, ruling_ref iff degrading, basis grammar', () => {
    for (const k of ['kgspp_reason_closed_ck', 'kgspp_ruling_iff_degrading_ck', 'kgspp_basis_grammar_ck',
                     'kgspp_included_nonempty_ck', 'kgspp_basis_required_ck']) expect(exec).toContain(k)
    for (const r of ['not_applicable_to_class', 'on_demand_tier', 'disabled_form', 'inputs_unavailable',
                     'tier_withheld_by_ruling']) expect(exec).toContain(`'${r}'`)
    // reason, ruling_ref and basis are inside the digested preimage; note is not
    const pre = exec.slice(exec.indexOf('FUNCTION public.ka_gochara_search_inventory_preimage'),
                           exec.indexOf('FUNCTION public.ka_gochara_search_inventory_digest'))
    for (const col of ['exclusion_reason', 'ruling_ref', 'basis', 'committed_ob_ids']) expect(pre).toContain(`p.${col}`)
    expect(pre).not.toContain('p.note')
  })

  it('the event_class vocabulary equals 1155 kgrr_event_class_ck (27 classes, no drift)', () => {
    const list = (s: string, key: string): string[] => {
      const i = s.indexOf(key); const j = s.indexOf('))', i)
      return [...s.slice(i, j).matchAll(/'([a-z_]+)'/g)].map(m => m[1]!).sort()
    }
    const a = list(read(MIGRATIONS_DIR, '1155_gochara_relationship_record.sql'), 'kgrr_event_class_ck')
    const b = list(sql, 'kgsi_event_class_ck')
    expect(a).toHaveLength(27)
    expect(b).toEqual(a)
  })

  it('builder privileges: role-guarded, no TRUNCATE/TRIGGER/REFERENCES, no CREATE on public', () => {
    expect(exec).toMatch(/IF EXISTS \(SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder'\)/)
    const grants = [...exec.matchAll(/GRANT [^;]+;/g)].map(m => m[0])
    expect(grants.length).toBeGreaterThan(0)
    for (const g of grants) {
      expect(g).not.toMatch(/TRUNCATE|TRIGGER|REFERENCES|CREATE/)
    }
  })

  it('migrate.ts: 1206 is protected; the routine runner refuses it, --only admits it; deploy.yml applies it AFTER 1204', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(M1206)).toBe(true)
    expect(() => assertGeneralRunnerMayApplyPublicSchema(M1206, false)).toThrow(/gochara_contracts_schema_migration=true/)
    expect(() => assertGeneralRunnerMayApplyPublicSchema(M1206, true)).not.toThrow()
    const yml = fs.readFileSync(DEPLOY_YML, 'utf8')
    const at1204 = yml.indexOf('migrations+=(1204_gochara_av_qualifier_object_role.sql)')
    const at1206 = yml.indexOf(`migrations+=(${M1206})`)
    expect(at1204).toBeGreaterThan(-1)
    expect(at1206, '1206 listed in the same window after 1204').toBeGreaterThan(at1204)
  })
})

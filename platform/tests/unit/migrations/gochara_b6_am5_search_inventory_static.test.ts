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
const CI_YML = path.resolve(process.cwd(), '../.github/workflows/ci.yml')

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

  it('PC-4: the verification FK cascades from the inventory header (a rebuild invalidates a stale verification)', () => {
    expect(exec).toMatch(/kgsv_header_fk FOREIGN KEY \(chart_id, generation, event_class\)\s+REFERENCES public\.ka_gochara_search_inventory \(chart_id, generation, event_class\) ON DELETE CASCADE/)
  })

  it('PC-4: the builder is granted NOTHING on the inventory verification table (the verifier principal writes it)', () => {
    const tableGrants = [...exec.matchAll(/GRANT SELECT, INSERT, DELETE ON([^;]+);/g)].map(m => m[1]!)
    expect(tableGrants).toHaveLength(1)
    expect(tableGrants[0]).not.toContain('ka_gochara_search_inventory_verification')
    for (const t of SIX_TABLES.filter(x => x !== 'ka_gochara_search_inventory_verification')) expect(tableGrants[0]).toContain(t)
    expect(exec).not.toMatch(/ka_gochara_search_inventory_verification[^;]*TO data_plane_builder/)
  })

  it('R6: the builder gets EXPLICIT, signature-qualified EXECUTE on exactly 17 functions — never PUBLIC, never a seal-side function', () => {
    const grants = [...exec.matchAll(/GRANT EXECUTE ON FUNCTION([^;]+);/g)].map(m => m[1]!)
    expect(grants).toHaveLength(2)
    for (const g of grants) expect(g).toMatch(/TO data_plane_builder$/)
    const sigs = grants.flatMap(g => [...g.matchAll(/public\.(ka_gochara_\w+)\(([^)]*)\)/g)].map(m => m[1]!))
    expect(sigs).toHaveLength(17)
    expect(new Set(sigs).size).toBe(17)
    for (const forbidden of ['ka_gochara_seal_generation', 'ka_gochara_search_completeness_violations', 'ka_gochara_search_replay_violations',
      'ka_gochara_search_inventories_digest', 'ka_gochara_search_write_guard', 'ka_gochara_generation_seal_search_guard'])
      expect(sigs).not.toContain(forbidden)
    expect(exec).not.toMatch(/GRANT [^;]*\bTO PUBLIC\b/i)
  })

  it('v1.2: superseded_by_version is a closed, NON-degrading reason, and both version-scope seal checks exist', () => {
    const closed = exec.slice(exec.indexOf('CONSTRAINT kgspp_reason_closed_ck'), exec.indexOf('CONSTRAINT kgspp_ruling_iff_degrading_ck'))
    expect(closed).toContain("'superseded_by_version'")
    const degrading = exec.slice(exec.indexOf('CONSTRAINT kgspp_ruling_iff_degrading_ck'), exec.indexOf('CONSTRAINT kgspp_basis_grammar_ck'))
    expect(degrading).not.toContain('superseded_by_version')
    expect(exec).toContain("'multiple_included_versions'")
    expect(exec).toContain("'superseded_without_included_version'")
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

  it('Codex v1.0 R1–R5 are pinned in the source: full-key commitment equality, bridge binding, total pin CHECKs, session-independent L1 digests, pinned search_path', () => {
    // R1: the committed-but-not-stored branch carries the owning path/version (6-column key)
    const first = exec.slice(exec.indexOf('FUNCTION public.ka_gochara_search_completeness_violations'),
                             exec.indexOf('FUNCTION public.ka_gochara_search_replay_violations'))
    expect(first).toContain('(o.chart_id, o.generation, o.event_class, o.path_id, o.rule_version, o.ob_id)')
    expect(first).not.toMatch(/\(o\.chart_id, o\.generation, o\.event_class, o\.ob_id\)\s*=\s*\(p\.chart_id, p\.generation, p\.event_class, c\)\)\)\s*OR EXISTS/)
    // R2: both the publication and the partitions are resolved through the immutable bridge
    for (const k of ['convention_bridge_missing', 'convention_mismatch']) expect(first).toContain(`'${k}'`)
    expect(exec).toContain('ka_gochara_convention_bridge b WHERE b.kala_convention_id = pub.convention_id')
    // R3: the excluded-pin reason CHECK is a TOTAL boolean (no nullable escape path)
    const r3 = exec.slice(exec.indexOf('CONSTRAINT kgspp_reason_closed_ck'), exec.indexOf('CONSTRAINT kgspp_ruling_iff_degrading_ck'))
    expect(r3).toContain('exclusion_reason IS NOT NULL')
    expect(r3).toContain('COALESCE(exclusion_reason IN')
    // R4: the ACTUAL audit column is excluded, never the non-existent created_at; the session is pinned
    const l1 = exec.slice(exec.indexOf('FUNCTION public.ka_gochara_search_l1_facts_digest'), exec.indexOf('FUNCTION public.ka_gochara_search_av_entry'))
    expect(l1).toContain("to_jsonb(f) - 'computed_at'")
    expect(l1).not.toContain("'created_at'")
    expect(l1).toContain("SET timezone = 'UTC'")
    expect(l1).toContain('SET extra_float_digits = 1')
    expect(l1).toContain('f.chart_id = p_chart')
    expect(l1).toContain("to_jsonb(r) - 'computed_at'")
    expect(exec).toContain('consumed_dasha_row_ids  uuid[] NOT NULL')
    expect(exec).toContain('r.dasha_row_id = i.id AND r.chart_id = p_chart')          // uuid join, no text cast
    // every function pins search_path
    const blocks = exec.split(/CREATE OR REPLACE FUNCTION /).slice(1)
    expect(blocks.length).toBeGreaterThanOrEqual(17)
    for (const b of blocks) {
      const head = b.slice(0, b.indexOf('$$'))
      expect(head, `search_path pinned: ${head.split('(')[0]}`).toContain('SET search_path = pg_catalog, public')
    }
    // the empty ledger is input-bound
    expect(exec).toContain("'input=' || i.input_digest")
  })

  it('CI runs the live-DB suite as REQUIRED (no silent skip) plus the reproducible mutation harness', () => {
    const ci = fs.readFileSync(CI_YML, 'utf8')
    expect(ci).toContain('GOCHARA_REQUIRE_DB')
    expect(ci).toContain('gochara_b6_am5_search_inventory.db.test.ts')
    expect(ci).toContain('CREATE DATABASE gochara_a51_test')
    expect(ci).toContain('scripts/gochara/mutation_check_1206.py')
    const db = fs.readFileSync(path.resolve(process.cwd(), 'tests/integration/gochara_b6_am5_search_inventory.db.test.ts'), 'utf8')
    expect(db).toContain("process.env.GOCHARA_REQUIRE_DB === '1'")
    expect(db).toContain('data_plane_builder')
    expect(fs.existsSync(path.resolve(process.cwd(), 'scripts/gochara/mutation_check_1206.py'))).toBe(true)
  })
})


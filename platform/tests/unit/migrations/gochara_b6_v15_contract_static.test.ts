// @vitest-environment node
/**
 * Pravāha B6.0 PART 1 — STATIC contract checks on migrations 1204/1205 (the
 * v1.5 contract amendments AM-7 'av_qualifier' object_role and AM-8
 * 'inherited' frame-kind), their preflights, the runner's protected-file
 * refusal and the deploy window, asserted against the on-disk sources
 * (CLAUDE.md §N.8: the detector reads what ships).
 *
 * Source: GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT §AM-7/§AM-8 (f870999c1);
 * steward work package M20261001T125220-a4c1. Mirror of the A5.1 wiring
 * (#2765): NEW migration files (1154/1155 are applied and never edited),
 * preflights byte-identical to the embedded gates, registration in
 * migrate.ts PROTECTED_PUBLIC_SCHEMA_MIGRATIONS, the deploy.yml protected
 * window.
 *
 * Live-DB behaviour is covered by
 * tests/integration/gochara_b6_v15_migrations.db.test.ts.
 */
import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS, assertGeneralRunnerMayApplyPublicSchema } from '../../../scripts/migrate'

const MIGRATIONS_DIR = path.resolve(process.cwd(), 'migrations')
const SUPABASE_MIGRATIONS_DIR = path.resolve(process.cwd(), 'supabase/migrations')
const PREFLIGHT_DIR = path.resolve(process.cwd(), '../platform/python-sidecar/scripts/kala_gochara_cutover')
const DEPLOY_YML = path.resolve(process.cwd(), '../.github/workflows/deploy.yml')

const M1204 = '1204_gochara_av_qualifier_object_role.sql'
const M1205 = '1205_gochara_inherited_frame_kind.sql'
const P1204 = 'preflight_1204_av_qualifier_object_role.sql'
const P1205 = 'preflight_1205_inherited_frame_kind.sql'

const V10_ROLES = ['lord', 'occupant', 'karaka', 'dispositor', 'maraka_of_house',
  'period_lord', 'yoga_constituent', 'pada', 'signature_house'] as const

function readMigration(name: string): string {
  return fs.readFileSync(path.join(MIGRATIONS_DIR, name), 'utf8')
}
function readPreflight(name: string): string {
  return fs.readFileSync(path.join(PREFLIGHT_DIR, name), 'utf8')
}

/** The gate DO-block of a migration / the whole DO-block of its preflight. */
function gateBlock(sql: string, n: string): string {
  const start = sql.indexOf('DO $$')
  const end = sql.indexOf('$$;', start)
  expect(start, `migration ${n}: gate DO block present`).toBeGreaterThan(-1)
  expect(end, `migration ${n}: gate DO block terminated`).toBeGreaterThan(start)
  return sql.slice(start, end + 3)
}

describe('B6.0 v1.5 contract migrations 1204/1205 — static contract', () => {
  it('the migration files and their preflights exist on disk', () => {
    for (const f of [M1204, M1205]) {
      expect(fs.existsSync(path.join(MIGRATIONS_DIR, f)), f).toBe(true)
    }
    for (const f of [P1204, P1205]) {
      expect(fs.existsSync(path.join(PREFLIGHT_DIR, f)), f).toBe(true)
    }
  })

  it('numbers 1204/1205 are unique across BOTH migration directories', () => {
    for (const dir of [MIGRATIONS_DIR, SUPABASE_MIGRATIONS_DIR]) {
      const clashes = fs.readdirSync(dir).filter(f => /^(1204|1205)_/.test(f)
        && f !== M1204 && f !== M1205)
      expect(clashes, `duplicate 1204/1205 in ${dir}`).toEqual([])
    }
  })

  it('each gate is byte-identical to its preflight DO block (F8/F9)', () => {
    expect(gateBlock(readMigration(M1204), '1204')).toBe(gateBlock(readPreflight(P1204), '1204'))
    expect(gateBlock(readMigration(M1205), '1205')).toBe(gateBlock(readPreflight(P1205), '1205'))
  })

  it('no BEGIN/COMMIT transaction control — migrate.ts owns the one transaction (A2)', () => {
    for (const f of [M1204, M1205]) {
      const sql = readMigration(f)
      // transaction-control statements only; plpgsql's bare `BEGIN` block
      // keyword (no semicolon) inside the gate DO blocks must not match
      expect(sql, f).not.toMatch(/^\s*BEGIN\s*;/m)
      expect(sql, f).not.toMatch(/^\s*COMMIT\s*;?\s*$/m)
      expect(sql, f).not.toMatch(/^\s*START\s+TRANSACTION/m)
    }
  })

  it('gates are ordered: 1204 requires 1155 recorded and not itself; 1205 requires 1154', () => {
    const g1204 = gateBlock(readMigration(M1204), '1204')
    expect(g1204).toContain("'1155_'")
    expect(g1204).toContain("'1204_'")
    expect(g1204).toContain('prerequisite_migration_not_applied')
    expect(g1204).toContain('migration_already_applied')
    const g1205 = gateBlock(readMigration(M1205), '1205')
    expect(g1205).toContain("'1154_'")
    expect(g1205).toContain("'1205_'")
  })

  it('preflights are READ ONLY — no DDL/DML statement outside the detector', () => {
    for (const f of [P1204, P1205]) {
      const sql = readPreflight(f)
      // statement-start keywords only (the 'CREATE' privilege literal inside
      // has_schema_privilege is mid-line and must not match)
      expect(sql, f).not.toMatch(/^\s*(CREATE|ALTER|DROP|INSERT|UPDATE|DELETE|GRANT|REVOKE)\b/im)
    }
  })

  it("AM-7: 1204 widens kgrr_object_role_ck with exactly 'av_qualifier' added to the v1.0 set", () => {
    const sql = readMigration(M1204)
    expect(sql).toContain('DROP CONSTRAINT kgrr_object_role_ck')
    expect(sql).toContain('ADD CONSTRAINT kgrr_object_role_ck')
    const added = sql.slice(sql.indexOf('ADD CONSTRAINT kgrr_object_role_ck'))
    for (const role of [...V10_ROLES, 'av_qualifier']) {
      expect(added, `role ${role} present`).toContain(`'${role}'`)
    }
    // 1155 is applied and never edited: its on-disk file keeps the v1.0 vocabulary
    const m1155 = readMigration('1155_gochara_relationship_record.sql')
    expect(m1155).not.toContain('av_qualifier')
    expect(m1155).toContain('kgrr_object_role_ck')
  })

  it('AM-7 (flagged fold): 1204 widens ka_gochara_object_selector_ok with the same single value', () => {
    const sql = readMigration(M1204)
    expect(sql).toContain('CREATE OR REPLACE FUNCTION public.ka_gochara_object_selector_ok(j jsonb)')
    const fn = sql.slice(sql.indexOf('CREATE OR REPLACE FUNCTION public.ka_gochara_object_selector_ok'))
    for (const role of [...V10_ROLES, 'av_qualifier']) {
      expect(fn, `selector role ${role} present`).toContain(`'${role}'`)
    }
    // 1154 is applied and never edited
    const m1154 = readMigration('1154_gochara_rule_path_registry.sql')
    expect(m1154).not.toContain('av_qualifier')
  })

  it("AM-8: 1205 adds the 'inherited' arm (arg NULL) to ka_gochara_frame_ok, v1.0 arms intact", () => {
    const sql = readMigration(M1205)
    expect(sql).toContain('CREATE OR REPLACE FUNCTION public.ka_gochara_frame_ok(frame_kind text, frame_arg text)')
    const fn = sql.slice(sql.indexOf('CREATE OR REPLACE FUNCTION public.ka_gochara_frame_ok'))
    expect(fn).toContain("WHEN 'inherited'     THEN frame_arg IS NULL")
    for (const arm of ["WHEN 'moon'", "WHEN 'lagna'", "WHEN 'dasha_lord'", "WHEN 'graha'", "WHEN 'bhavat_bhavam'"]) {
      expect(fn, `v1.0 arm ${arm} kept`).toContain(arm)
    }
    // post-apply behavioural probes are embedded in the migration
    expect(sql).toContain("ka_gochara_frame_ok('inherited', NULL) IS NOT TRUE")
    expect(sql).toContain("ka_gochara_frame_ok('inherited', 'moon') IS NOT FALSE")
    // 1154 is applied and never edited
    const m1154 = readMigration('1154_gochara_rule_path_registry.sql')
    expect(m1154).not.toContain('inherited')
  })

  it('migrate.ts: both files are protected; the routine runner refuses them, --only admits them', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(M1204)).toBe(true)
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(M1205)).toBe(true)
    for (const f of [M1204, M1205]) {
      expect(() => assertGeneralRunnerMayApplyPublicSchema(f, false))
        .toThrow(/gochara_contracts_schema_migration=true/)
      expect(() => assertGeneralRunnerMayApplyPublicSchema(f, true)).not.toThrow()
    }
    // unprotected neighbours are untouched
    expect(() => assertGeneralRunnerMayApplyPublicSchema('1203_ai_metering_receipt_fk_permission.sql', false)).not.toThrow()
  })

  it('deploy.yml: the window applies 1204/1205 after 1153-1157, in ascending order', () => {
    const yml = fs.readFileSync(DEPLOY_YML, 'utf8')
    const at1157 = yml.indexOf('1157_gochara_av_polarity_declaration.sql')
    const at1204 = yml.indexOf(M1204)
    const at1205 = yml.indexOf(M1205)
    expect(at1157).toBeGreaterThan(-1)
    expect(at1204, '1204 listed in deploy.yml').toBeGreaterThan(at1157)
    expect(at1205, '1205 listed after 1204').toBeGreaterThan(at1204)
    expect(yml).toContain('1204-1205')
  })

  it('both migrations pin search_path and carry post-apply presence checks', () => {
    for (const f of [M1204, M1205]) {
      const sql = readMigration(f)
      expect(sql, f).toContain('SET LOCAL search_path = public, pg_catalog;')
      expect(sql, f).toContain('post-apply check failed')
    }
  })
})

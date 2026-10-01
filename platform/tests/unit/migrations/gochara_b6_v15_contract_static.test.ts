// @vitest-environment node
/**
 * Pravāha B6.0 PART 1 — STATIC contract checks on migration 1204 (the v1.5
 * contract amendment AM-7 'av_qualifier' object_role), its preflight, the
 * runner's protected-file refusal and the deploy window, asserted against the
 * on-disk sources (CLAUDE.md §N.8: the detector reads what ships).
 *
 * Source: GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT v0.2 §AM-7; steward work package
 * M20261001T125220-a4c1. Mirror of the A5.1 wiring (#2765): a NEW migration
 * file (1154/1155 are applied and never edited), preflight byte-identical to
 * the embedded gate, registration in migrate.ts
 * PROTECTED_PUBLIC_SCHEMA_MIGRATIONS, the deploy.yml protected window.
 *
 * AM-8's 1205 was SPLIT OUT (ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_0, rank 1):
 * the shared-validator arm would have admitted unresolved 'inherited' frames
 * on arbitrary paths including scored rows and bypassed 1155:527-528's
 * relative-frame exclusion. It returns as its own designed P6-testimony-
 * template migration with day_on_demand. These static checks also assert the
 * split is total: no 1205 file, no 'inherited' arm anywhere on disk.
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
const P1204 = 'preflight_1204_av_qualifier_object_role.sql'

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

describe('B6.0 v1.5 contract migration 1204 — static contract', () => {
  it('the migration file and its preflight exist on disk', () => {
    expect(fs.existsSync(path.join(MIGRATIONS_DIR, M1204)), M1204).toBe(true)
    expect(fs.existsSync(path.join(PREFLIGHT_DIR, P1204)), P1204).toBe(true)
  })

  it('the AM-8 split is total: no 1205 migration/preflight, no inherited arm anywhere it could ship', () => {
    for (const dir of [MIGRATIONS_DIR, SUPABASE_MIGRATIONS_DIR]) {
      expect(fs.readdirSync(dir).filter(f => /^1205_/.test(f)), `1205 file in ${dir}`).toEqual([])
    }
    expect(fs.existsSync(path.join(PREFLIGHT_DIR, 'preflight_1205_inherited_frame_kind.sql'))).toBe(false)
    // the shared frame validator keeps exactly its v1.0 arms (1154 untouched)
    const m1154 = readMigration('1154_gochara_rule_path_registry.sql')
    expect(m1154).not.toContain('inherited')
    // deploy.yml carries no 1205 entry
    expect(fs.readFileSync(DEPLOY_YML, 'utf8')).not.toContain('1205_gochara_inherited_frame_kind.sql')
  })

  it('number 1204 is unique across BOTH migration directories', () => {
    for (const dir of [MIGRATIONS_DIR, SUPABASE_MIGRATIONS_DIR]) {
      const clashes = fs.readdirSync(dir).filter(f => /^1204_/.test(f) && f !== M1204)
      expect(clashes, `duplicate 1204 in ${dir}`).toEqual([])
    }
  })

  it('the gate is byte-identical to its preflight DO block (F8/F9)', () => {
    expect(gateBlock(readMigration(M1204), '1204')).toBe(gateBlock(readPreflight(P1204), '1204'))
  })

  it('no BEGIN/COMMIT transaction control — migrate.ts owns the one transaction (A2)', () => {
    const sql = readMigration(M1204)
    // transaction-control statements only; plpgsql's bare `BEGIN` block
    // keyword (no semicolon) inside the gate DO blocks must not match
    expect(sql).not.toMatch(/^\s*BEGIN\s*;/m)
    expect(sql).not.toMatch(/^\s*COMMIT\s*;?\s*$/m)
    expect(sql).not.toMatch(/^\s*START\s+TRANSACTION/m)
  })

  it('the gate is ordered: 1204 requires 1155 recorded and not itself', () => {
    const g1204 = gateBlock(readMigration(M1204), '1204')
    expect(g1204).toContain("'1155_'")
    expect(g1204).toContain("'1204_'")
    expect(g1204).toContain('prerequisite_migration_not_applied')
    expect(g1204).toContain('migration_already_applied')
  })

  it('the preflight is READ ONLY — no DDL/DML statement outside the detector', () => {
    const sql = readPreflight(P1204)
    // statement-start keywords only (the 'CREATE' privilege literal inside
    // has_schema_privilege is mid-line and must not match)
    expect(sql).not.toMatch(/^\s*(CREATE|ALTER|DROP|INSERT|UPDATE|DELETE|GRANT|REVOKE)\b/im)
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

  it('AM-7 (selector fold, Codex-accepted): 1204 widens ka_gochara_object_selector_ok with the same single value', () => {
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

  it('the race claim is the Codex-corrected one: no writer-pause guarantee asserted', () => {
    const sql = readMigration(M1204)
    expect(sql).toContain('RACE CLAIM, corrected per ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_0')
    expect(sql).not.toContain('the window guarantees no')
    expect(sql).toContain('OPERATIONAL PRECONDITION')
  })

  it('migrate.ts: 1204 is protected; the routine runner refuses it, --only admits it', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(M1204)).toBe(true)
    expect(() => assertGeneralRunnerMayApplyPublicSchema(M1204, false))
      .toThrow(/gochara_contracts_schema_migration=true/)
    expect(() => assertGeneralRunnerMayApplyPublicSchema(M1204, true)).not.toThrow()
    // unprotected neighbours are untouched
    expect(() => assertGeneralRunnerMayApplyPublicSchema('1203_ai_metering_receipt_fk_permission.sql', false)).not.toThrow()
  })

  it('deploy.yml: the window applies 1204 after 1153-1157, in ascending order', () => {
    const yml = fs.readFileSync(DEPLOY_YML, 'utf8')
    const at1157 = yml.indexOf('1157_gochara_av_polarity_declaration.sql')
    const at1204 = yml.indexOf(`migrations+=(${M1204})`)
    expect(at1157).toBeGreaterThan(-1)
    expect(at1204, '1204 listed in deploy.yml after 1157').toBeGreaterThan(at1157)
  })

  it('the migration pins search_path and carries post-apply presence checks', () => {
    const sql = readMigration(M1204)
    expect(sql).toContain('SET LOCAL search_path = public, pg_catalog;')
    expect(sql).toContain('post-apply check failed')
  })
})

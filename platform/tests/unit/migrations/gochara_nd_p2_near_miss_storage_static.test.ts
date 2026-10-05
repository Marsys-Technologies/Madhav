/**
 * Pravāha ND-P2-20261005 rules 1-2, builder side — STATIC contract checks on migration 1308 (near-miss storage).
 * The live proof is python-sidecar/tests/l3/gochara/test_d1_near_miss_storage.py (the real writer on the real chain: the near-miss is stored as
 * one unscored interval, every scored table is byte-identical with the layer on and off, a rebuild replaces, the catalog diff is exactly three
 * tables). Here: the file is additive, a row cannot carry a score, the guards are the existing ones, the grants name only existing roles and
 * give the verifier and the sealer no write, and the protected-window wiring.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const FILE = '1308_gochara_near_miss_storage.sql'
const SQL = fs.readFileSync(path.resolve(__dirname, '../../../migrations', FILE), 'utf8')
/** the statements only: comment lines carry prose (and words like DROP TABLE in the rollback note) */
const CODE = SQL.split('\n').filter((l) => !l.trimStart().startsWith('--')).join('\n')
const TABLES = ['ka_gochara_near_miss_object', 'ka_gochara_near_miss', 'ka_gochara_near_miss_search']

describe('migration 1308 — static contract', () => {
  it('is ADDITIVE: creates exactly three tables and no function, alters and drops no table, edits no existing object', () => {
    const created = [...CODE.matchAll(/CREATE TABLE IF NOT EXISTS public\.(\w+)/g)].map((m) => m[1])
    expect(created.sort()).toEqual([...TABLES].sort())
    expect(CODE).not.toMatch(/CREATE\s+(OR\s+REPLACE\s+)?FUNCTION/i)
    expect(CODE).not.toMatch(/ALTER\s+TABLE/i)
    expect(CODE).not.toMatch(/DROP\s+(TABLE|FUNCTION|INDEX|CONSTRAINT)/i)
    expect(CODE).not.toMatch(/\b(UPDATE|DELETE\s+FROM|INSERT\s+INTO|TRUNCATE)\s+public\./i)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/im)
    expect(CODE).not.toMatch(/REVOKE/i)
  })

  it('every trigger is on a NEW table and calls a guard function that already exists (1153/1155)', () => {
    const triggers = [...CODE.matchAll(/CREATE TRIGGER (\w+)\s+BEFORE [A-Z ]+ ON public\.(\w+)\s+FOR EACH (ROW|STATEMENT) EXECUTE FUNCTION public\.(\w+)\(/g)]
    expect(triggers.length).toBe(9)
    for (const [, , table, , fn] of triggers) {
      expect(TABLES).toContain(table)
      expect(['ka_gochara_chart_statement_lock', 'ka_gochara_chart_write_guard', 'ka_gochara_refuse_truncate', 'ka_gochara_substrate_chart_lock',
        'ka_gochara_insert_only']).toContain(fn)
    }
    const drops = [...CODE.matchAll(/DROP TRIGGER IF EXISTS (\w+) ON public\.(\w+)/g)]
    expect(drops.map((d) => d[1]).sort()).toEqual(triggers.map((t) => t[1]).sort())      // only its own triggers, for idempotence
    for (const table of ['ka_gochara_near_miss', 'ka_gochara_near_miss_search']) {
      expect(CODE).toMatch(new RegExp(`ON public\\.${table}\\s+FOR EACH ROW EXECUTE FUNCTION public\\.ka_gochara_chart_write_guard\\('no_update'\\)`))
      expect(CODE).toMatch(new RegExp(`BEFORE TRUNCATE ON public\\.${table}\\s+FOR EACH STATEMENT EXECUTE FUNCTION public\\.ka_gochara_refuse_truncate`))
    }
  })

  it('a near-miss row is unscored, of the lower standing and of positive clearance BY CONSTRAINT (ND-P2 rule 2)', () => {
    expect(CODE).toContain('CONSTRAINT kgnm_unscored_ck CHECK (score IS NULL)')
    expect(CODE).toContain("CONSTRAINT kgnm_score_reason_ck CHECK (score_reason = 'near_miss_unscored')")
    expect(CODE).toContain("CONSTRAINT kgnm_standing_ck CHECK (standing = 'near_miss')")
    expect(CODE).toContain('CONSTRAINT kgnm_clearance_positive_ck CHECK (clearance_deg > 0 AND clearance_deg < orb_deg)')
    expect(CODE).toContain("CHECK (chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid)")
    expect(CODE).toContain('PRIMARY KEY (chart_id, generation, near_miss_id)')
    expect(CODE).toContain('UNIQUE (body, relation_kind, canonical_target, orb_policy_id, convention_id)')       // FB-25: the orb is in the object key
    expect(CODE).toMatch(/^\s+proximity\s+DOUBLE PRECISION NOT NULL/m)
    expect(CODE).not.toMatch(/^\s+\w*(strength|weight|activity)\w*\s+[A-Z]/m)                                      // the column is PROXIMITY: no strength, weight or activity column
  })

  it('no near-miss table references a contact, a record, a window, a manifest or a build run — and nothing is told to reference it', () => {
    const refs = [...CODE.matchAll(/REFERENCES public\.(\w+)/g)].map((m) => m[1])
    expect([...new Set(refs)].sort()).toEqual(['charts', 'ka_gochara_near_miss_object', 'ka_gochara_sky_convention'])
  })

  it('grants name only the three existing roles, each guarded by its existence; the verifier and the sealer get SELECT only', () => {
    const grants = [...CODE.matchAll(/GRANT ([A-Z, ]+) ON ([\w., \n]+?) TO (\w+);/g)].map((m) => ({ privs: m[1].trim(), role: m[3] }))
    expect([...new Set(grants.map((g) => g.role))].sort()).toEqual(['data_plane_builder', 'gochara_sealer', 'gochara_verifier'])
    for (const g of grants) {
      if (g.role !== 'data_plane_builder') expect(g.privs).toBe('SELECT')
      expect(g.privs).not.toMatch(/UPDATE|TRUNCATE|ALL/)
    }
    for (const role of ['data_plane_builder', 'gochara_verifier', 'gochara_sealer']) {
      expect(CODE).toContain(`IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${role}') THEN`)
      expect(CODE).toMatch(new RegExp(`role ${role} NOT FOUND`))                                                  // an absent role is NAMED, never silent
    }
    expect(CODE).not.toMatch(/TO PUBLIC/i)
  })

  it('fails closed: prerequisites are checked before anything is created and the post-apply block raises', () => {
    expect(CODE.indexOf("RAISE EXCEPTION 'migration 1308: prerequisite")).toBeLessThan(CODE.indexOf('CREATE TABLE'))
    expect((CODE.match(/RAISE EXCEPTION 'migration 1308 post-apply check failed/g) ?? []).length).toBeGreaterThanOrEqual(8)
  })

  it('is a protected public-schema migration, selected by the window and by nothing else', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(true)
    const deploy = fs.readFileSync(path.resolve(__dirname, '../../../../.github/workflows/deploy.yml'), 'utf8')
    expect((deploy.match(new RegExp(`migrations\\+=\\(${FILE}\\)`, 'g')) ?? []).length).toBe(1)
    expect(deploy.indexOf(`migrations+=(${FILE})`)).toBeGreaterThan(deploy.indexOf('migrations+=(1240_gochara_window_verification_gate.sql)'))
  })
})

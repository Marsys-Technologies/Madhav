/**
 * Suvarna routine migration 1328 -- STATIC contract (data_plane_builder privilege gaps for the 75-asset set: 26 relations, 12 sequences,
 * grants only). The live proof (disposable PostgreSQL 15, real role layout: 92 gaps -> 0, idempotent re-run, non-owner refusal) is
 * recorded in the PR body. This file pins the text so a drive-by edit (a TRUNCATE, a PUBLIC grant, a schema-wide grant, a REVOKE, a
 * 27th relation) is a deliberate, reviewed change.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const FILE = '1328_builder_75_asset_set_privilege_gap_grants.sql'
const SQL = fs.readFileSync(path.resolve(__dirname, '../../../migrations', FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')

const lists = (re: RegExp): string[][] =>
  [...CODE.matchAll(re)].map(m => [...(m[1] ?? '').matchAll(/\('([a-z_0-9]+)'/g)].map(x => x[1] as string))

describe('migration 1328 -- static contract', () => {
  it('lists exactly 26 relations (25 tables + vw_chart_digest) and 12 sequences, identically in guard, grant and post-check', () => {
    const rel = lists(/FOR r IN SELECT \* FROM \(VALUES\s*(\('[a-z_0-9]+', '[rv]'[\s\S]*?)\) AS v\(relname/g)
    const seq = lists(/FOR r IN SELECT \* FROM \(VALUES\s*(\('[a-z_0-9]+'\)[\s\S]*?)\) AS v\(seqname/g)
    expect(rel).toHaveLength(3)
    expect(seq).toHaveLength(3)
    for (const l of rel) expect(l).toHaveLength(26)
    for (const l of seq) expect(l).toHaveLength(12)
    expect(rel[1]).toEqual(rel[0])
    expect(rel[2]).toEqual(rel[0])
    expect(seq[1]).toEqual(seq[0])
    expect(seq[2]).toEqual(seq[0])
    expect(rel[0]).toContain('prashna_charts')
    expect(rel[0]).toContain('vw_chart_digest')
  })

  it('prashna_charts is SELECT only', () => {
    expect(CODE).toContain("('prashna_charts', 'r', 'SELECT')")
    expect(CODE.match(/'prashna_charts'/g)).toHaveLength(3)
  })

  it('grants only to data_plane_builder, no PUBLIC, no schema-wide, no revoke, no TRUNCATE/REFERENCES/TRIGGER grant', () => {
    const grants = CODE.match(/GRANT [^\n]*/g) ?? []
    expect(grants).toHaveLength(2)
    for (const g of grants) expect(g).toMatch(/TO data_plane_builder'?,?\s*$|TO data_plane_builder/)
    expect(CODE).not.toMatch(/\bTO\s+PUBLIC\b/i)
    expect(CODE).not.toMatch(/ALL (TABLES|SEQUENCES) IN SCHEMA/i)
    expect(CODE).not.toMatch(/\bREVOKE\b/i)
    expect(CODE).not.toMatch(/WITH GRANT OPTION/i)
    // TRUNCATE/REFERENCES/TRIGGER appear only as post-check detections, never in a granted privilege list
    expect(CODE).not.toMatch(/\('[a-z_0-9]+', '[rv]', '[A-Z,]*(TRUNCATE|REFERENCES|TRIGGER)/)
    expect(CODE).not.toMatch(/\b(CREATE|ALTER|DROP|INSERT INTO|UPDATE|DELETE FROM)\b\s+(TABLE|ROLE|FUNCTION|\w+\.)/i)
  })

  it('is a routine migration: lock_timeout first, no BEGIN/COMMIT, not protected-schema', () => {
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT);/m)
    expect([...PROTECTED_PUBLIC_SCHEMA_MIGRATIONS]).not.toContain(FILE)
  })

  it('refuses rather than skips: role, relation, kind and owner guards are present', () => {
    for (const s of ["rolname = 'data_plane_builder'", 'does not exist', 'owner path required', "pg_has_role(current_user, owner_oid, 'USAGE')"]) {
      expect(CODE).toContain(s)
    }
  })
})

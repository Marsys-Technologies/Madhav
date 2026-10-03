/**
 * Pravāha B6.0 / steward M20261002T064220-07d6 — STATIC contract of migration 1242 (builder record-table REPLACE + FINALISE grants).
 * The live proof (a full build then a rebuild as the restricted builder, individual necessity of each grant, refusal after the seal) is the
 * composed rehearsal: python-sidecar/tests/l3/gochara/test_b6_composed_seal_flows.py.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1242_gochara_builder_record_replace_finalise_grants.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')

describe('migration 1242 — static contract', () => {
  it('is grants only: exactly four GRANT statements, to the builder, and nothing else changes schema', () => {
    const grants = CODE.match(/^GRANT [^;]+;/gm) ?? []
    expect(grants).toEqual([
      'GRANT DELETE ON public.ka_gochara_relationship_record TO data_plane_builder;',
      'GRANT DELETE ON public.ka_gochara_contact TO data_plane_builder;',
      'GRANT UPDATE (admission_state) ON public.ka_gochara_relationship_record TO data_plane_builder;',
      'GRANT UPDATE (result) ON public.ka_gochara_record_prerequisite TO data_plane_builder;',
    ])
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|DROP|REVOKE|TRUNCATE)\b|SECURITY DEFINER|WITH GRANT OPTION/im)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/m)
  })

  it('UPDATE is column-level only; there is no table-level UPDATE, no DELETE on the prerequisite table, no UPDATE on contacts', () => {
    const grants = CODE.match(/^GRANT [^;]+;/gm) ?? []
    for (const g of grants.filter(x => /\bUPDATE\b/.test(x))) expect(g).toMatch(/UPDATE \([a-z_]+\) ON/)
    expect(grants.join('\n')).not.toMatch(/DELETE ON public\.ka_gochara_record_prerequisite/)
    expect(grants.join('\n')).not.toMatch(/UPDATE[^;]*ka_gochara_contact\b/)
  })

  it('is guarded (builder role exists, record tables exist) and verifies the grants and the absence of extras after applying', () => {
    expect(CODE).toContain("rolname = 'data_plane_builder'")
    expect(CODE).toContain('does not exist — refusing to grant to nobody')
    expect(CODE).toContain('post-apply check failed')
    expect(CODE).toContain("has_column_privilege('data_plane_builder', 'public.ka_gochara_record_prerequisite', 'result', 'UPDATE')")
    expect(CODE).toContain("has_table_privilege('data_plane_builder', 'public.ka_gochara_record_prerequisite', 'DELETE')")
  })

  it('states the correction of 1216 and cites the guards it read', () => {
    expect(SQL).toContain('CORRECTION OF 1216')
    expect(SQL).toContain('replacement is impossible by design')
    expect(SQL).toMatch(/1155:419-426/)
    expect(SQL).toMatch(/1153:176-177/)
  })

  it('is a ROUTINE migration (not in the protected public-schema set), unique, and numbered in the reserved block', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    const n = Number(FILE.slice(0, 4)); expect(n).toBeGreaterThanOrEqual(1230); expect(n).toBeLessThanOrEqual(1249)
    for (const d of [MIG, path.resolve(__dirname, '../../../python-sidecar/scripts/kala_gochara_cutover')].filter(x => fs.existsSync(x)))
      expect(fs.readdirSync(d).filter(f => /^1242_/.test(f) && f !== FILE)).toEqual([])
  })
})

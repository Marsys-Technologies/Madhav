/**
 * Pravāha B6.0 / Codex round 8 R8-10 — STATIC contract of migration 1234 (eval-window builder grants). The live proof (derivation by
 * the 1206-R6 method, individual necessity of every grant, least privilege) is tests/integration/gochara_b6_1234_*.db.test.ts.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1234_gochara_eval_window_builder_grants.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')

describe('migration 1234 — static contract', () => {
  it('is grants only: exactly five GRANT statements, to the builder, and nothing else changes schema', () => {
    const grants = CODE.match(/^GRANT [^;]+;/gm) ?? []
    expect(grants).toEqual([
      'GRANT SELECT, INSERT, DELETE ON public.ka_gochara_eval_window TO data_plane_builder;',
      'GRANT SELECT, INSERT ON public.ka_gochara_eval_window_record TO data_plane_builder;',
      'GRANT EXECUTE ON FUNCTION public.ka_gochara_text_array_ok(text[], integer) TO data_plane_builder;',
      'GRANT EXECUTE ON FUNCTION public.ka_gochara_facts_horizon(jsonb) TO data_plane_builder;',
      'GRANT EXECUTE ON FUNCTION public.ka_gochara_membership_violation(jsonb, uuid, text, jsonb, tstzrange[]) TO data_plane_builder;',
    ])
    expect(CODE).not.toMatch(/\bCREATE\b|\bALTER\b|\bDROP\b|\bREVOKE\b|SECURITY DEFINER|\bTRUNCATE\b|WITH GRANT OPTION/i)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/m)
  })

  it('grants no UPDATE anywhere, no DELETE on the membership table, and no seal-side or trigger function', () => {
    const grants = CODE.match(/^GRANT [^;]+;/gm) ?? []
    for (const g of grants) expect(g).not.toMatch(/\bUPDATE\b/)
    for (const g of grants.filter(x => x.includes('ka_gochara_eval_window_record'))) expect(g).not.toMatch(/\bDELETE\b/)
    for (const f of ['ka_gochara_membership_violations', 'ka_gochara_coverage_drift', 'ka_gochara_window_coverage_guard', 'ka_gochara_window_membership_guard',
                     'ka_gochara_generation_seal', 'ka_gochara_seal_generation'])
      expect(grants.join('\n')).not.toContain(f)
  })

  it('verifies the grants are actually held, and refuses extra window privileges', () => {
    expect(CODE).toContain('post-apply check failed')
    expect(CODE).toContain("has_table_privilege('data_plane_builder', 'public.ka_gochara_eval_window', 'UPDATE')")
  })

  it('is a ROUTINE migration (not in the protected public-schema set), unique, and numbered in the reserved block', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    const n = Number(FILE.slice(0, 4)); expect(n).toBeGreaterThanOrEqual(1230); expect(n).toBeLessThanOrEqual(1249)
    for (const d of [MIG, path.resolve(__dirname, '../../../python-sidecar/scripts/kala_gochara_cutover')].filter(x => fs.existsSync(x)))
      expect(fs.readdirSync(d).filter(f => /^1234_/.test(f) && f !== FILE)).toEqual([])
  })
})

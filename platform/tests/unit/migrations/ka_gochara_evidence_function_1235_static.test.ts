/**
 * Pravāha B (decision A, split of #2996) — STATIC contract of protected-class migration 1235 (the staged-candidate evidence function).
 * Live proof: python-sidecar/tests/test_migration_1235_evidence_function.py (disposable PostgreSQL).
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS, assertGeneralRunnerMayApplyPublicSchema } from '../../../scripts/migrate'

const FILE = '1235_ka_gochara_staged_candidate_evidence_function.sql'
const SQL = fs.readFileSync(path.resolve(__dirname, '../../../migrations', FILE), 'utf8')
const CODE = SQL.split('\n').filter((l) => !l.trim().startsWith('--')).join('\n')

describe('migration 1235 — static contract', () => {
  it('is declared PROTECTED: the routine runner refuses it by name, the window (--only) may apply it', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(true)
    expect(() => assertGeneralRunnerMayApplyPublicSchema(FILE, false)).toThrow(/Protected public-schema migration/)
    expect(() => assertGeneralRunnerMayApplyPublicSchema(FILE, true)).not.toThrow()
  })

  it('creates exactly one function — SECURITY DEFINER, STABLE, search_path pinned, boolean, refuses any other id — and touches no table', () => {
    const noBody = CODE.replace(/\$fn\$[\s\S]*?\$fn\$/g, '$fn$ $fn$').replace(/\$acl\$[\s\S]*?\$acl\$/g, '$acl$ $acl$')
    expect(noBody.match(/\bCREATE\b/gi)).toHaveLength(1)
    expect(noBody).not.toMatch(/\b(ALTER|DROP|TRUNCATE|INSERT|UPDATE|DELETE|COPY)\b/i)
    expect(noBody).not.toMatch(/\bON TABLE\b|WITH GRANT OPTION/i)
    expect(CODE).toMatch(/RETURNS boolean\s+LANGUAGE plpgsql\s+STABLE\s+SECURITY DEFINER\s+SET search_path = pg_catalog, pg_temp/)
    const fn = CODE.match(/\$fn\$([\s\S]*?)\$fn\$/)![1]
    expect(fn).toMatch(/NOT IN \('ka_gochara_v4_41_candidate', 'ka_gochara_v5'\)/)
    for (const table of ['asset_provenance_receipts', 'build_run_assets', 'asset_throughput']) expect(fn).toContain(`public.${table}`)
  })

  it('REVOKE ALL FROM PUBLIC and EXECUTE only to amjis_app, nirmana_campaign_control_writer and nirmana_evidence_ingress_writer', () => {
    expect(CODE).toContain('REVOKE ALL ON FUNCTION public.ka_gochara_staged_candidate_has_runtime_evidence(text) FROM PUBLIC;')
    const grants = (CODE.match(/GRANT EXECUTE ON FUNCTION [^;]+;/g) ?? []).map((g) => g.replace(/\s+/g, ' '))
    expect(grants).toEqual([
      'GRANT EXECUTE ON FUNCTION public.ka_gochara_staged_candidate_has_runtime_evidence(text) TO amjis_app;',
      'GRANT EXECUTE ON FUNCTION public.ka_gochara_staged_candidate_has_runtime_evidence(text) TO nirmana_campaign_control_writer;',
      'GRANT EXECUTE ON FUNCTION public.ka_gochara_staged_candidate_has_runtime_evidence(text) TO nirmana_evidence_ingress_writer;',
    ])
    expect(CODE).toMatch(/a\.is_grantable AND a\.grantee <> p\.proowner/)                   // the grant-option check (P3)
  })
})

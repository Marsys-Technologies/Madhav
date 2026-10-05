/**
 * Suvarna S-L2 / migration 1295 — STATIC contract (the read-only resolver for the deterministic chart_vichara citation token).
 * The live proof (SQL token == Python token on production-shaped and hostile rows, re-runnability, the privilege guard, no
 * table written) is platform/python-sidecar/tests/l2/test_vichara_token.py on a disposable PostgreSQL; the read-only production
 * measurement is in the PR body. This file pins the TEXT so a drive-by edit (a stored column, a wider grant, a table write, a
 * second view, a changed canonical rule) is a deliberate, reviewed change. It is scoped to this file only.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1295_chart_vichara_token_resolver.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const STATEMENTS = CODE.split(/;\s*(?:\n|$)/).map(s => s.trim()).filter(s => s.length > 0)

describe('migration 1295: static contract', () => {
  it('is a routine-path file in platform/migrations with no BEGIN/COMMIT (migrate.ts owns the transaction)', () => {
    expect(fs.existsSync(path.join(MIG, FILE))).toBe(true)
    // a statement-level BEGIN;/COMMIT;/ROLLBACK; (the plpgsql block openers `BEGIN` are not followed by a semicolon)
    expect(CODE).not.toMatch(/\b(BEGIN|COMMIT|ROLLBACK)\s*;/)
  })

  it('sets a 5 s lock_timeout locally before anything else', () => {
    expect(STATEMENTS[0]).toBe("SET LOCAL lock_timeout = '5s'")
  })

  it('creates exactly one function and one view, both CREATE OR REPLACE, in schema public', () => {
    expect(CODE.match(/\bCREATE\b/g)).toHaveLength(2)
    expect(CODE.match(/CREATE OR REPLACE FUNCTION public\.chart_vichara_token\(/g)).toHaveLength(1)
    expect(CODE.match(/CREATE OR REPLACE VIEW public\.vw_chart_vichara_token AS/g)).toHaveLength(1)
  })

  it('is read-only: no DROP/ALTER/TRUNCATE/INSERT/UPDATE/DELETE/COMMENT and no table is created or written', () => {
    expect(CODE).not.toMatch(/\b(DROP|ALTER|TRUNCATE|INSERT|UPDATE|DELETE|COMMENT|CREATE\s+TABLE|CREATE\s+INDEX|CREATE\s+TRIGGER)\b/)
    // the only relation read is chart_vichara
    const from = [...CODE.matchAll(/\bFROM\s+(public\.[a-z_]+)/g)].map(m => m[1])
    expect(new Set(from)).toEqual(new Set(['public.chart_vichara']))
  })

  it('stores nothing: the view carries no stored column and the function is pure over its 12 arguments', () => {
    expect(CODE).toContain('LANGUAGE sql')
    expect(CODE).toContain('STABLE')
    expect(CODE).toContain('SET search_path = pg_catalog')
    expect(CODE).not.toMatch(/SECURITY DEFINER/)
    expect(CODE).not.toMatch(/MATERIALIZED/)
  })

  it('implements the canonical rules: 12 positional fields, to_json text, trim_scale numeric, jsonb text, sha256 hex[:16]', () => {
    expect(CODE).toContain("'[' || concat_ws(','")
    expect(CODE.match(/coalesce\(to_json\(p_[a-z_]+\)::text, 'null'\)/g)).toHaveLength(10) // 9 text-typed columns + the facts array
    expect(CODE).toContain("WHEN p_value_num = 'NaN'::numeric THEN '\"NaN\"'")
    expect(CODE).toContain('trim_scale(p_value_num)::text')
    expect(CODE).toContain("coalesce(p_value_jsonb::text, 'null')")
    expect(CODE).toContain("coalesce(to_json(p_constituent_facts_array)::text, 'null')")
    expect(CODE).toContain("left(encode(sha256(convert_to(")
    expect(CODE).toContain("'UTF8')), 'hex'), 16)")
    // the key fields, in order
    const order = [...CODE.matchAll(/to_json\(p_([a-z_]+)\)|p_value_num IS NULL|p_value_jsonb::text/g)].map(m => m[1] ?? (m[0].includes('value_num') ? 'value_num' : 'value_jsonb'))
    expect(order).toEqual(['ayanamsha_id', 'vichara_family', 'subject', 'actor', 'target', 'domain', 'varga_id', 'varga', 'value_text',
      'value_num', 'value_jsonb', 'constituent_facts_array'])
  })

  it('grants SELECT/EXECUTE to exactly suvarna_reader and data_plane_builder and revokes PUBLIC EXECUTE on its own function', () => {
    const grants = STATEMENTS.filter(s => /^GRANT\b/.test(s))
    expect(grants).toHaveLength(2)
    for (const g of grants) {
      expect(g).toMatch(/TO suvarna_reader, data_plane_builder$/)
    }
    expect(grants.some(g => g.startsWith('GRANT SELECT ON public.vw_chart_vichara_token'))).toBe(true)
    expect(grants.some(g => g.startsWith('GRANT EXECUTE ON FUNCTION public.chart_vichara_token('))).toBe(true)
    const revokes = STATEMENTS.filter(s => /^REVOKE\b/.test(s))
    expect(revokes).toHaveLength(1)
    expect(revokes[0]).toMatch(/^REVOKE ALL ON FUNCTION public\.chart_vichara_token\(.*\) FROM PUBLIC$/s)
    // no wider reader: these roles do not read chart_vichara and must not gain access through the view
    expect(CODE).not.toMatch(/retrieval_census_ro|nirmana_evidence_ingress_writer|WITH GRANT OPTION|TO PUBLIC/)
  })

  it('guards before it acts and verifies after: privilege guard, golden token, grants', () => {
    expect(CODE).toContain("has_table_privilege(current_user, 'public.chart_vichara', 'SELECT')")
    expect(CODE).toContain('refusing to widen its access through the view')
    expect(CODE).toContain('golden token mismatch')
    expect(CODE).toContain('a required grant is missing after apply')
    expect(CODE).toContain('3bf71fa91397a24a')
  })

  it('exposes the row id only as a join aid and no other column of chart_vichara beyond the natural key', () => {
    const view = CODE.slice(CODE.indexOf('CREATE OR REPLACE VIEW'), CODE.indexOf('GRANT SELECT'))
    const cols = [...view.matchAll(/\bv\.([a-z_]+)/g)].map(m => m[1])
    expect(new Set(cols)).toEqual(new Set(['id', 'chart_id', 'ayanamsha_id', 'vichara_family', 'subject', 'actor', 'target', 'domain',
      'varga_id', 'varga', 'value_text', 'value_num', 'value_jsonb', 'constituent_facts_array']))
    expect(view).toContain('AS vichara_token')
  })
})

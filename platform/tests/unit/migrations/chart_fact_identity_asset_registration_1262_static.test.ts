/**
 * Suvarna / migration 1262 -- STATIC contract (register the Fact Identity Index as asset `ga_fact_identity` + GRANT SELECT on
 * chart_fact_identity to data_plane_builder; S-L2 blocker B5).
 *
 * The live proof (disposable PostgreSQL 15 and 17 with production's roles/ACL/registry DDL: apply as amjis_app, idempotent re-run,
 * count_sql per chart, the integrity SQL true/false on crafted defects, guards, WARN-only grant, lock_timeout, and ~40 mutants) is
 * python-sidecar/tests/test_migration_1262_chart_fact_identity_registration.py. This file pins the TEXT so a drive-by edit (a second
 * registry row, a broader privilege, a REVOKE/DELETE, an UPDATE that would fire the receipt-invalidation trigger, a claim widened past
 * what SQL can measure, a depends_on edge) is a deliberate, reviewed change.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1262_chart_fact_identity_asset_registration.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')

describe('migration 1262 -- static contract', () => {
  it('starts with the transaction-local 5s lock_timeout and owns no transaction', () => {
    expect(CODE.match(/\bSET LOCAL lock_timeout\b/g)).toHaveLength(1)
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/m)
  })

  it('registers exactly ONE asset, ga_fact_identity (L1 prefix, never a dotted or bo_ id)', () => {
    expect(CODE.match(/\bINSERT INTO\b/g)).toHaveLength(1)
    expect(CODE).toMatch(/INSERT INTO public\.asset_registry \(/)
    expect(CODE).toContain("v_asset_id      constant text := 'ga_fact_identity';")
    expect(CODE.match(/'ga_fact_identity'/g)).toHaveLength(1) // the id is spelled once; the INSERT and every check use the variable
    expect(CODE).not.toMatch(/'(bo|ka|ph|mi|bg)_fact_identity'|'ganita\./)
    expect(CODE).toContain('ON CONFLICT (asset_id) DO NOTHING;')
    expect(CODE.match(/ON CONFLICT/g)).toHaveLength(1)
  })

  it('never UPDATEs, DELETEs, REVOKEs or changes schema (the receipt-invalidation trigger is AFTER UPDATE; the grant is additive)', () => {
    expect(CODE).not.toMatch(/\bUPDATE\b\s+[\w.]+\s+SET|\bDELETE\s+FROM\b|\bREVOKE\b|DO UPDATE|WITH GRANT OPTION|SECURITY DEFINER/i)
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|DROP)\b/im)
    expect(CODE).not.toMatch(/\bGRANT\b[^;]*\b(PUBLIC|ALL|INSERT|UPDATE|DELETE|TRUNCATE|REFERENCES|TRIGGER)\b/i)
  })

  it('does not name depends_on (no DAG edge; keeps the registry-DAG migration pin unchanged) and adds no co-writer', () => {
    expect(CODE).not.toMatch(/depends_on/)
    expect(CODE).toContain('has_writer')
    const values = CODE.slice(CODE.indexOf('VALUES ('), CODE.indexOf('ON CONFLICT'))
    // has_substeps false, asset_kind data, has_writer false (positions pinned by the live test too)
    expect(values).toMatch(/v_integrity_sql,\s+false,\s+'data',\s+false,\s+'chart',\s+'R1'/)
  })

  it('has ONE count_sql, chart-scoped with $1, and the stats-route shape (a count over its own table)', () => {
    const m = CODE.match(/v_count_sql\s+constant text := '([^']*)';/)
    expect(m).not.toBeNull()
    expect(m?.[1]).toBe('SELECT count(*) FROM chart_fact_identity WHERE chart_id = $1')
  })

  it('states its integrity claim narrowly: four consistency clauses + non-vacuity, no completeness claim, no category list', () => {
    const m = CODE.match(/v_integrity_sql constant text :=([\s\S]*?);\n\s+tbl /)
    expect(m).not.toBeNull()
    const lits = [...(m?.[1] ?? '').matchAll(/'([^']*)'/g)].map(x => x[1]).join('')
    expect(lits).toBe(
      'SELECT EXISTS (SELECT 1 FROM public.chart_fact_identity) '
      + 'AND NOT EXISTS ('
      + 'SELECT 1 FROM public.chart_fact_identity i '
      + 'LEFT JOIN public.chart_facts f ON f.fact_id = i.fact_id '
      + 'WHERE f.fact_id IS NULL '
      + 'OR f.chart_id <> i.chart_id '
      + 'OR i.build_id IS DISTINCT FROM f.build_id '
      + 'OR strpos(i.parsed_from, f.fact_subject) = 0 '
      + 'OR strpos(i.parsed_from, f.fact_key) = 0'
      + ') AS integrity_passed',
    )
    // schema-qualified (a bind-time pg_temp shadow must not satisfy it), a bare SELECT with no parameter, no comparison to chart_facts COUNT
    expect(lits).not.toMatch(/\$1|fact_category|identity_free|count\(/)
    expect(SQL).toContain('WHAT THE SQL CANNOT CHECK')
    expect(SQL).toContain('rows == parsed identity-bearing facts')
    expect(SQL).toContain('scope_cap_sentinel')
    expect(SQL).toContain('build_fact_identity_index.py --check')
  })

  it('grants SELECT only to data_plane_builder on public.chart_fact_identity, skips a held grant, and asserts the result (P2: WARN-only counts as failure)', () => {
    expect(CODE.match(/\bGRANT\b/g)).toHaveLength(1)
    expect(CODE).toContain("EXECUTE format('GRANT SELECT ON TABLE %s TO data_plane_builder', rel);")
    expect(CODE).toContain("rel := 'public.chart_fact_identity'::regclass;")
    expect(CODE).toContain("has_table_privilege('data_plane_builder', rel, 'SELECT')")
    expect(CODE).toContain("has_any_column_privilege('data_plane_builder', rel, p)")
    expect(CODE).toContain("ARRAY['INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER']")
    expect(CODE).toContain('data_plane_builder lacks SELECT on public.chart_fact_identity after the grant')
    expect(CODE).toContain('data_plane_builder holds more than SELECT')
    // the asserting RAISE comes AFTER the grant, and it is the last statement of the migration
    expect(CODE.indexOf('lacks SELECT on public.chart_fact_identity after the grant')).toBeGreaterThan(CODE.indexOf("EXECUTE format('GRANT"))
    expect(CODE.trimEnd().endsWith('END\n$mig$;')).toBe(true)
    const tail = CODE.slice(CODE.lastIndexOf("IF NOT has_table_privilege('data_plane_builder'"))
    expect(tail).toMatch(/RAISE EXCEPTION '1262: data_plane_builder lacks SELECT[\s\S]*RAISE EXCEPTION '1262: data_plane_builder holds more than SELECT/)
  })

  it('guards: role/table/relkind, no active build run (planned/running/paused), executor must act as the owner; read-back of the row', () => {
    expect(CODE).toContain("rolname = 'data_plane_builder'")
    expect(CODE).toContain("ARRAY['asset_registry', 'chart_facts', 'build_runs', 'chart_fact_identity']")
    expect(CODE).toContain("IF kind NOT IN ('r', 'p') THEN")
    expect(CODE).toContain("state IN ('planned', 'running', 'paused')")
    expect(CODE).toContain('IF n_active <> 0 THEN')
    expect(CODE).toContain("IF NOT pg_has_role(current_user, owner_oid, 'USAGE') THEN")
    expect(CODE).toContain('differs from the intended shape')
    expect(CODE).toContain('xmin = pg_current_xact_id()::xid')
    // the guards run before the first write
    expect(CODE.indexOf('IF n_active <> 0 THEN')).toBeLessThan(CODE.indexOf('INSERT INTO'))
    expect(CODE.indexOf('cannot act as the owner')).toBeLessThan(CODE.indexOf('INSERT INTO'))
    expect(CODE.indexOf('INSERT INTO')).toBeLessThan(CODE.indexOf('EXECUTE format('))
  })

  it('states the header facts: owner finding, route, serving effect (trigger cannot fire), claim limits, never-REVOKE', () => {
    expect(SQL).toContain('OWNER FINDING')
    expect(SQL).toContain('= amjis_app')
    expect(SQL).toContain('this is a ROUTINE migration')
    expect(SQL).toContain('SERVING EFFECT AT APPLY')
    expect(SQL).toContain('the trigger CANNOT fire')
    expect(SQL).toContain('nirmana_registry_receipt_invalidation')
    expect(SQL).toContain('never REVOKE or DELETE')
    expect(SQL).toContain('S-L2 blocker B5')
    expect(SQL).toContain('ga_fact_identity')
    expect(SQL).toContain('a precondition of S-L2, applied POST-window')
  })

  it('is a ROUTINE migration (not in the protected public-schema set), unique, in the 1200-1299 range', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    const n = Number(FILE.slice(0, 4))
    expect(n).toBe(1262)
    expect(fs.readdirSync(MIG).filter(f => /^1262_/.test(f) && f !== FILE)).toEqual([])
  })
})

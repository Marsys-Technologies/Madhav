/**
 * Suvarna PW.2 / migration 1256 — STATIC contract (one guarded REFRESH of mv_chart_sade_sati_lifetime_summary).
 * The live proof (a disposable PostgreSQL 15 cluster with the production role structure) was run by hand before this PR:
 * owner apply (stale view refreshed, 2 -> 3 rows), idempotent re-run, non-owner refusal (the file rolls back), an
 * unpopulated view (plain REFRESH, ends populated), a missing view (NOTICE no-op) and lock_timeout (a held lock makes
 * the file fail after ~10 s). This file pins the text so a drive-by edit (a second view, a grant, DDL) is a
 * deliberate, reviewed change. It has no guard about OTHER migrations: it is scoped to this file only.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1256_refresh_mv_chart_sade_sati_lifetime_summary_after_s_l1.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const VIEW = 'public.mv_chart_sade_sati_lifetime_summary'

describe('migration 1256 — static contract', () => {
  it('sets a 10 s lock_timeout locally before anything else', () => {
    const first = CODE.split(';').map(s => s.trim()).find(s => s.length > 0)
    expect(first).toBe("SET LOCAL lock_timeout = '10s'")
  })

  it('refreshes exactly ONE view: CONCURRENTLY when populated, plain only when never populated', () => {
    expect(CODE.match(/REFRESH MATERIALIZED VIEW/g)).toHaveLength(2)
    expect(CODE.match(new RegExp(`REFRESH MATERIALIZED VIEW CONCURRENTLY ${VIEW};`, 'g'))).toHaveLength(1)
    expect(CODE.match(new RegExp(`REFRESH MATERIALIZED VIEW ${VIEW};`, 'g'))).toHaveLength(1)
    expect(CODE).toContain('m.ispopulated')
    expect(CODE).toContain("m.matviewname = 'mv_chart_sade_sati_lifetime_summary'")
    // no other materialized view is named anywhere in executable SQL
    const names = [...CODE.matchAll(/\bmv_[a-z_]+\b/g)].map(m => m[0])
    expect(new Set(names)).toEqual(new Set(['mv_chart_sade_sati_lifetime_summary']))
  })

  it('is a NOTICE no-op when the view does not exist', () => {
    expect(CODE).toContain('IF NOT FOUND THEN')
    expect(CODE).toContain('RAISE NOTICE')
    expect(CODE).toContain('RETURN;')
  })

  it('does nothing else: no DDL, no grant, no table write', () => {
    expect(CODE).not.toMatch(/\b(CREATE|ALTER|DROP|GRANT|REVOKE|TRUNCATE|INSERT|UPDATE|DELETE|COMMENT)\b/)
    expect(CODE).not.toMatch(/\bchart_facts\b/)
  })
})

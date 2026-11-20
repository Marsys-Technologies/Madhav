/**
 * Migration 1289 — STATIC contract (one guarded REFRESH per OTHER L1 materialized view; sibling of 1256, which did
 * mv_chart_sade_sati_lifetime_summary). The behaviour (stale set refreshed to the exact definition, idempotent, NOTICE no-op when
 * absent, unpopulated -> plain, CONCURRENTLY where a unique index exists, non-owner refused, lock_timeout rolls the whole file
 * back, no data/grant/owner/index change) is proved against a disposable PostgreSQL by
 * python-sidecar/tests/test_migration_1289_refresh_other_l1_mvs.py. This file pins the text so a drive-by edit (a view added or
 * dropped, a grant, DDL, a data write) is a deliberate, reviewed change. It has no guard about OTHER migrations: it is scoped to
 * this file only.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1289_refresh_other_l1_materialized_views_after_s_l1.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')

// Parents before dependents; mv_chart_sade_sati_lifetime_summary is 1256's and must NOT appear.
const VIEWS = [
  'mv_chart_planet_summary',
  'mv_chart_shadbala_summary',
  'mv_chart_ashtakavarga_summary',
  'mv_chart_bhava_bala_summary',
  'mv_cross_ayanamsha_consensus',
  'mv_chart_panchanga_birth_summary',
  'mv_chart_sensitive_points_summary',
  'mv_sensitive_points_cross_ayanamsha',
  'mv_chart_vargas_summary',
  'mv_chart_aspect_matrix',
  'mv_chart_super_vargottama_bodies',
  'mv_chart_t1_composite_strengths',
  'mv_chart_yogas_fired_summary',
]

describe('migration 1289 — static contract', () => {
  it('sets a 10 s lock_timeout locally before anything else', () => {
    const first = CODE.split(';').map(s => s.trim()).find(s => s.length > 0)
    expect(first).toBe("SET LOCAL lock_timeout = '10s'")
  })

  it('refreshes exactly the thirteen views, in dependency order, and not the sade-sati view', () => {
    const listed = [...CODE.matchAll(/'(mv_[a-z0-9_]+)'/g)].map(m => m[1])
    expect(listed).toEqual(VIEWS)
    expect(new Set(listed).size).toBe(13)
    expect(CODE).not.toContain('mv_chart_sade_sati_lifetime_summary')
    expect(listed.indexOf('mv_chart_sensitive_points_summary')).toBeLessThan(listed.indexOf('mv_sensitive_points_cross_ayanamsha'))
    // no view is named in executable SQL outside the one array
    expect([...CODE.matchAll(/\bmv_[a-z0-9_]+\b/g)]).toHaveLength(13)
  })

  it('uses CONCURRENTLY only for a populated view with a valid, non-partial, non-expression unique index; plain otherwise', () => {
    expect(CODE.match(/REFRESH MATERIALIZED VIEW/g)).toHaveLength(2)
    expect(CODE).toContain("EXECUTE format('REFRESH MATERIALIZED VIEW CONCURRENTLY public.%I', v_view);")
    expect(CODE).toContain("EXECUTE format('REFRESH MATERIALIZED VIEW public.%I', v_view);")
    expect(CODE).toContain('IF v_populated AND v_unique_idx THEN')
    for (const needle of ['m.ispopulated', 'i.indisunique', 'i.indisvalid', 'i.indpred IS NULL', 'i.indexprs IS NULL', "m.schemaname = 'public'"]) {
      expect(CODE).toContain(needle)
    }
  })

  it('is a NOTICE no-op for a view that does not exist', () => {
    expect(CODE).toContain('IF NOT FOUND THEN')
    expect(CODE).toContain('RAISE NOTICE')
    expect(CODE).toContain('CONTINUE;')
  })

  it('does nothing else: no transaction control, no DDL, no grant, no table write, no role or session change beyond lock_timeout', () => {
    expect(CODE).not.toMatch(/\b(BEGIN|COMMIT|ROLLBACK)\s*;/)
    expect(CODE).not.toMatch(/\b(CREATE|ALTER|DROP|GRANT|REVOKE|TRUNCATE|INSERT|UPDATE|DELETE|COMMENT)\b/)
    expect(CODE).not.toMatch(/\bSET\s+(?!LOCAL lock_timeout)/i)
    expect(CODE).not.toMatch(/\bchart_facts\b|\bchart_divisionals\b/)
  })
})

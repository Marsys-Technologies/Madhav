/**
 * Suvarna / migration 1265 — STATIC contract (capture of the live-only mimamsa_predictions_builder_guard + the
 * UPDATE/DELETE/TRUNCATE guard on frozen mimamsa_predictions rows, SS ruling N-104).
 * The live proof (a disposable PostgreSQL cluster with production's role set: privilege determination, every guard
 * behaviour, md5 guard refusals, idempotent re-run, RLS assessment, 21 mutants) is
 * python-sidecar/tests/test_migration_1265_l5_frozen_row_guard.py. This file pins the text so a drive-by edit (a wider
 * allow-list, a dropped trigger, a GUC bypass, a changed captured body) is a deliberate, reviewed change, and it
 * carries the HOLD: the file creates a function in schema public, which the routine runner cannot do, so it must not
 * reach main before the protected-window wiring exists.
 */
import { describe, it, expect } from 'vitest'
import crypto from 'crypto'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1265_l5_predictions_frozen_row_guard.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const FLAT = SQL.replace(/^--/gm, ' ').replace(/\s+/g, ' ')

const BUILDER_MD5 = '46c23854275c2712b30860a2b174adb2'
const BUILDER_LEN = 1084

function body(tag: string): string {
  const m = new RegExp(`AS \\$${tag}\\$([\\s\\S]*?)\\$${tag}\\$;`).exec(SQL)
  if (!m || m[1] === undefined) throw new Error(`no $${tag}$ body`)
  return m[1]
}
const md5 = (s: string) => crypto.createHash('md5').update(s, 'utf8').digest('hex')

describe('migration 1265 — static contract', () => {
  it('holds the live builder guard byte for byte: md5 and length pinned, SECURITY INVOKER, pinned search_path', () => {
    const b = body('guard')
    expect(md5(b)).toBe(BUILDER_MD5)
    expect(Buffer.byteLength(b, 'utf8')).toBe(BUILDER_LEN)
    expect(b.startsWith("\nBEGIN\n  IF current_user = 'data_plane_builder'")).toBe(true)
    expect(CODE).toContain('SECURITY INVOKER')
    expect(CODE).toContain('SET search_path = pg_catalog, pg_temp')
    expect(SQL.split(BUILDER_MD5).length - 1).toBeGreaterThanOrEqual(4)
  })

  it('pins the new guard body md5 in the replace check, the post-check and the header', () => {
    const m = md5(body('frozen'))
    expect(SQL.split(m).length - 1).toBeGreaterThanOrEqual(4)
  })

  it('allow-list is exactly lifecycle_status and the three staleness columns; everything else fails closed', () => {
    const b = body('frozen')
    const arr = /c_mutable\s+CONSTANT text\[\] := ARRAY\[([\s\S]*?)\];/.exec(b)
    expect(arr).not.toBeNull()
    const cols = [...(arr?.[1] ?? '').matchAll(/'([a-z_]+)'/g)].map(x => x[1])
    expect(cols).toEqual(['lifecycle_status', 'chart_context_stale_at', 'chart_context_stale_reason', 'chart_context_superseded_by_run_id'])
    expect(b).toContain('to_jsonb(OLD) - c_mutable')
    expect(b).toContain('to_jsonb(NEW) - c_mutable')
  })

  it('has no bypass: no setting, role-name or session test opens an exception; the one exception is data-driven', () => {
    const b = body('frozen')
    expect(b).not.toContain('current_setting') // the guard reads no setting at all
    expect(b).not.toMatch(/current_user\s*=|session_user\s*=|pg_has_role|usesuper|rolsuper/)
    expect(b).toContain("c.consent_state = 'withdrawn'")
    expect(b).toContain("d.status IN ('open', 'reopened', 'escalated')")
    expect(b).toContain('EXCEPTION WHEN insufficient_privilege THEN')
    expect(b).toContain('v_authorized := false')
  })

  it('is code only: no data write but the rolled-back probe, no grant, no registry row, no RLS, no transaction control', () => {
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/m)
    expect(CODE).not.toMatch(/\bGRANT\b/)
    expect(CODE).not.toMatch(/asset_registry|_migrations_applied/)
    expect(CODE).not.toMatch(/ROW LEVEL SECURITY|CREATE POLICY/)
    expect(CODE.match(/\bINSERT INTO\b/g)).toHaveLength(1)
    expect(CODE).toContain('1265_selftest_ok')
    expect(CODE).not.toMatch(/\b(DROP TABLE|DROP COLUMN|ADD COLUMN|CREATE TABLE|CREATE INDEX|DROP FUNCTION|DROP TRIGGER)\b/)
    expect(CODE.match(/REVOKE ALL ON FUNCTION/g)).toHaveLength(2)
  })

  it('creates the row trigger (UPDATE OR DELETE) and the TRUNCATE trigger, both ENABLE ALWAYS, with exact tgtype checks', () => {
    expect(CODE).toContain('BEFORE UPDATE OR DELETE ON public.mimamsa_predictions')
    expect(CODE).toContain('BEFORE TRUNCATE ON public.mimamsa_predictions')
    expect(CODE.match(/^ALTER TABLE public\.mimamsa_predictions ENABLE ALWAYS TRIGGER /gm)).toHaveLength(2)
    for (const t of ['tgtype <> 27', 'tgtype <> 34', 'tgtype <> 15']) expect(CODE).toContain(t)
  })

  it('gate names the missing privilege; self-test requires the guard\'s own message, not a privilege error', () => {
    for (const n of ["has_schema_privilege(current_user, 'public', 'CREATE')", 'protected public-schema window',
      'is not a member of the table owner', "LIKE 'mimamsa_predictions_frozen_row_guard:%'", 'TRUNCATE branch skipped']) {
      expect(CODE).toContain(n)
    }
  })

  it('states the header facts: ruling, hold, privilege determination, order, RLS assessment, serving effect, not-done', () => {
    for (const n of ['N-104', 'HELD', 'AFTER S-L1', 'DEFINITION OF "FROZEN"', 'PENDING rows are protected too',
      'ONE exception, narrowly defined and data-driven', 'Break-glass', 'CAN disable a trigger', 'PRIVILEGE',
      'permission denied for schema public', 'jataka-protected-migrations', 'THAT WIRING IS NOT IN THIS PR',
      'ORDER (hard preconditions)', 'mi_bhavisya.py:230', 'assetClearSpec.ts:149', 'RLS (assessed, NOT done here)',
      'SERVING EFFECT AT APPLY: none expected', 'NOT DONE HERE', 'ROLLBACK', 'VERIFICATION BY PRODUCTION STRUCTURE',
      'BUILDER_GRANT_PLAN v1.3']) expect(FLAT).toContain(n)
  })

  it('is unique, in the 1200-1299 range', () => {
    const n = Number(FILE.slice(0, 4))
    expect(n).toBe(1265)
    expect(fs.readdirSync(MIG).filter(f => /^1265_/.test(f) && f !== FILE)).toEqual([])
  })

  // HOLD (strict): the routine runner cannot create a function in schema public. Until 1265 is in
  // PROTECTED_PUBLIC_SCHEMA_MIGRATIONS and deploy.yml has an exact-set input/step for it, merging this file would
  // fail the migrate job on the next deploy. This test FAILS (as an expected failure) today; when the wiring lands it
  // starts passing, vitest reports it, and this marker is removed in the same PR.
  it.fails('HOLD: 1265 is wired into the protected public-schema window (not yet; do not merge before it is)', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(true)
  })
})

/**
 * Suvarna / migration 1275 — STATIC contract (chart_id -> charts(id) ON DELETE CASCADE on phala_muhurta, phala_mitigation,
 * phala_phaladesa and 24 mimamsa_* tables: every per-chart row leaves when its chart is deleted). The live proof (a disposable
 * PostgreSQL 15 and 17 cluster, run as amjis_app on a production-mirrored layout: the delete-route scenario over all 27 tables,
 * 1265's frozen-row guard in three variants, the discriminator and spoof tests, guards, active-run guard, lock_timeout, and 15
 * mutants) is python-sidecar/tests/test_migration_1275_chart_delete_per_chart_tables.py. This file pins the text so a drive-by edit
 * (a 28th table, an excluded table, a NOT VALID link, a data write) is a deliberate, reviewed change.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1275_chart_delete_reaches_phala_and_mimamsa_per_chart_tables.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const FLAT = SQL.replace(/^--/gm, ' ').replace(/\s+/g, ' ')

const TABLES = [
  'phala_muhurta', 'phala_mitigation', 'phala_phaladesa',
  'mimamsa_adjudication_log', 'mimamsa_anchor_adjustment', 'mimamsa_attribution', 'mimamsa_calibration',
  'mimamsa_calibration_snapshot', 'mimamsa_convergence_adjustment', 'mimamsa_discoveries', 'mimamsa_event_provenance',
  'mimamsa_export_log', 'mimamsa_fact_adjustment', 'mimamsa_insight_embeddings', 'mimamsa_insight_units',
  'mimamsa_intervention_ledger', 'mimamsa_journal', 'mimamsa_load_bearing', 'mimamsa_manifestation_grammar',
  'mimamsa_manifestation_sets', 'mimamsa_multipliers', 'mimamsa_predictions', 'mimamsa_qa_eval', 'mimamsa_reliability',
  'mimamsa_resonance_feedback', 'mimamsa_signal_adjustment', 'mimamsa_snapshot_cosign',
]
const EXCLUDED = ['mimamsa_pool_contributions', 'mimamsa_preferences', 'mimamsa_negative_controls', 'mimamsa_signal_families',
  'brahma_mimamsa_prediction_ledger', 'brahma_prospective_ledger', '__ssv_', 'chart_facts', 'bodha_', 'chart_dashas']

describe('migration 1275 — static contract', () => {
  it('has ONE table list: exactly the 27 named tables, in order, each appearing once', () => {
    const arrays = CODE.match(/\btables text\[\] := ARRAY\[([\s\S]*?)\];/g) ?? []
    expect(arrays).toHaveLength(1)
    const first = arrays[0]
    if (first === undefined) throw new Error('Expected the asserted single table list')
    expect([...first.matchAll(/'([a-z_]+)'/g)].map(m => m[1])).toEqual(TABLES)
    expect(TABLES).toHaveLength(27)
    for (const t of TABLES) expect(CODE.match(new RegExp(`'${t}'`, 'g'))).toHaveLength(1)
  })

  it('keeps every excluded table out of the executable SQL', () => {
    for (const t of EXCLUDED) expect(CODE).not.toContain(t)
  })

  it('adds validated cascading chart links only: no object, no data, no grant, no NOT VALID, no drop, no transaction control', () => {
    expect(CODE.match(/EXECUTE format\('ALTER TABLE/g)).toHaveLength(1)
    expect(CODE).toContain('FOREIGN KEY (chart_id) REFERENCES public.charts(id) ON DELETE CASCADE')
    expect(CODE).not.toMatch(/NOT VALID|SET NULL|DROP CONSTRAINT|INITIALLY DEFERRED/)
    expect(CODE).not.toMatch(/\bCREATE\s+(OR\s+REPLACE\s+)?(VIEW|FUNCTION|TABLE|INDEX|TRIGGER|SCHEMA|EXTENSION)\b/i)
    expect(CODE).not.toMatch(/\b(INSERT INTO|DELETE FROM|TRUNCATE|GRANT|REVOKE)\b/i)
    expect(CODE).not.toMatch(/\bUPDATE\s+\w+\s+SET\b/i)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/m)
  })

  it('starts with the transaction-local 5s lock_timeout and enforces the active-run guard', () => {
    expect(CODE.match(/\bSET LOCAL lock_timeout\b/g)).toHaveLength(1)
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
    expect(CODE).toContain('$runs$')
    expect(CODE).toContain("r.state NOT IN ('completed', 'failed', 'stopped')")
    expect(CODE).toContain("LIKE 'mi\\_%'")
    for (const a of ['ph_muhurta', 'ph_pratikara', 'ph_phaladesa']) expect(CODE).toContain(`'${a}'`)
  })

  it('STOPs rather than inventing: owner, chart_id presence, NOT NULL, unresolved rows, exact existing definition', () => {
    for (const n of ['pg_has_role(current_user, owner, \'USAGE\')', 'owner-path item', 'has no chart_id column',
      'will not invent a derivation', 'chart_id is nullable', 'has no charts row; report, do not backfill',
      'is not the expected chart link', 'primary key not found']) expect(CODE).toContain(n)
  })

  it('asserts in the post-check: present, validated, ON DELETE CASCADE, not deferrable, on chart_id -> charts(id); FK count exact', () => {
    for (const n of ['c.convalidated AND c.confdeltype = \'c\'', 'NOT c.condeferrable', 'is missing, not validated, not ON DELETE CASCADE',
      'fk_before + added', 'something else changed']) expect(CODE).toContain(n)
  })

  it('states the header facts: the gap, the 27 and the exclusions with reasons, the 1265 requirement and discriminator, locks', () => {
    for (const n of ['PRIVACY GAP', 'N-108', 'LAND TOGETHER WITH 1265', 'THE GAP', 'THE 27', 'EXCLUDED', 'ON DELETE NO ACTION',
      'NULLABLE', 'OWNER-PATH', 'THE 1265 REQUIREMENT', 'NOT EXISTS (SELECT 1 FROM public.charts WHERE id = OLD.chart_id)',
      'pg_trigger_depth() is NOT a safe discriminator', 'session_replication_role = replica', 'MEASURED', 'ACTIVE RUNS (ENFORCED',
      'SERVING EFFECT AT APPLY: none', 'NOT DONE HERE', 'VERIFICATION BY PRODUCTION STRUCTURE', 'ROLLBACK', 'HELD', 'AFTER S-L1',
      "on SS's review", 'charts/[id]/route.ts:87-107']) expect(FLAT).toContain(n)
  })

  it('is a ROUTINE migration (not protected), unique, in the 1200-1299 range', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    const n = Number(FILE.slice(0, 4))
    expect(n).toBeGreaterThanOrEqual(1200)
    expect(n).toBeLessThanOrEqual(1299)
    expect(fs.readdirSync(MIG).filter(f => /^1275_/.test(f) && f !== FILE)).toEqual([])
  })
})

// @vitest-environment node
/**
 * Pravāha A5.1 round 2 — STATIC contract checks on migrations 1153–1157 and
 * their preflights, asserted against the on-disk SQL itself (CLAUDE.md §N.8:
 * the detector reads what ships).
 *
 * Covers ASTRA_REVIEW_A5_1_MIGRATIONS v1_0 amendments that are checkable
 * without a database:
 *   - amendment 2 (P1 #2): no migration-owned BEGIN/COMMIT — migrate.ts owns
 *     the one transaction around DDL + ledger insert;
 *   - no business-data INSERT/UPDATE/DELETE in any migration body;
 *   - amendments 1/3/4/5/6/7/9: the named constraints, tables and columns the
 *     review required are present by name;
 *   - amendment 8: preflights fail closed (DO + RAISE), use wildcard-safe
 *     ledger lookups (starts_with), scoped trigger lookups, exact-signature
 *     function lookups, and ordered prerequisite gates.
 *
 * Live-DB behaviour is covered by the sibling suite
 * tests/integration/gochara_a5_1_migrations.db.test.ts.
 */
import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const MIGRATIONS_DIR = path.resolve(process.cwd(), 'migrations')
const PREFLIGHT_DIR = path.resolve(
  process.cwd(),
  '../platform/python-sidecar/scripts/kala_gochara_cutover',
)

const MIGRATIONS = {
  1153: '1153_gochara_sky_event_substrate.sql',
  1154: '1154_gochara_rule_path_registry.sql',
  1155: '1155_gochara_relationship_record.sql',
  1156: '1156_gochara_eval_window.sql',
  1157: '1157_gochara_av_polarity_declaration.sql',
} as const

const PREFLIGHTS = {
  1153: 'preflight_1153_sky_event_substrate.sql',
  1154: 'preflight_1154_rule_path_registry.sql',
  1155: 'preflight_1155_relationship_record.sql',
  1156: 'preflight_1156_eval_window.sql',
  1157: 'preflight_1157_av_polarity_declaration.sql',
} as const

function readMigration(n: keyof typeof MIGRATIONS): string {
  return fs.readFileSync(path.join(MIGRATIONS_DIR, MIGRATIONS[n]), 'utf8')
}
function readPreflight(n: keyof typeof PREFLIGHTS): string {
  return fs.readFileSync(path.join(PREFLIGHT_DIR, PREFLIGHTS[n]), 'utf8')
}

const EVENT_CLASS_LIST = [
  'achievement_recognition', 'bereavement', 'birth_anchor',
  'business_launch', 'career_advancement', 'career_change',
  'career_entry', 'career_setback', 'childbirth',
  'chronic_onset', 'education_milestone', 'exam_outcome',
  'financial_deception', 'foreign_settlement', 'illness_acute',
  'major_gain', 'major_loss', 'marriage', 'parental_event',
  'property_acquisition', 'psychological_arc', 'relocation',
  'romantic_start', 'separation', 'spiritual_turn', 'surgery',
  'travel_event',
]

describe('A5.1 migrations 1153–1157 — static contract', () => {
  it.each([1153, 1154, 1155, 1156, 1157] as const)(
    'amendment 2: migration %i owns NO transaction (no BEGIN/COMMIT; runner owns it)',
    n => {
      const sql = readMigration(n)
      expect(sql).not.toMatch(/^\s*BEGIN\s*;/im)
      expect(sql).not.toMatch(/^\s*COMMIT\s*;/im)
      expect(sql).not.toMatch(/^\s*ROLLBACK\s*;/im)
      // SET LOCAL is retained — it is scoped to the runner's transaction.
      expect(sql).toMatch(/SET LOCAL lock_timeout/)
    },
  )

  it.each([1153, 1154, 1155, 1156, 1157] as const)(
    'migration %i performs no business-data INSERT/UPDATE/DELETE',
    n => {
      const sql = readMigration(n)
      expect(sql).not.toMatch(/^\s*INSERT\s+INTO\b/im)
      expect(sql).not.toMatch(/^\s*UPDATE\s+\w/im)
      expect(sql).not.toMatch(/^\s*DELETE\s+FROM\b/im)
      expect(sql).not.toMatch(/^\s*TRUNCATE\b/im)
    },
  )

  it.each([1153, 1154, 1155, 1156, 1157] as const)(
    'amendment 8: migration %i carries a post-DDL verification block that RAISEs on drift',
    n => {
      const sql = readMigration(n)
      expect(sql).toContain(`migration ${n} post-DDL verification failed (amendment 8)`)
      expect(sql).toMatch(/DO \$\$/)
      expect(sql).toMatch(/RAISE EXCEPTION/)
    },
  )

  it('amendment 1: the §6.1 contact identity is a table of its own, separate from sky_event', () => {
    const sql = readMigration(1153)
    expect(sql).toContain('CREATE TABLE IF NOT EXISTS ka_gochara_contact')
    expect(sql).toMatch(/relation_kind\s+TEXT NOT NULL/)
    expect(sql).toMatch(/t_in\s+TIMESTAMPTZ NOT NULL/)
    expect(sql).toMatch(/t_out\s+TIMESTAMPTZ,/)
    expect(sql).toMatch(/t_exact\s+TIMESTAMPTZ,/)
    // boundary events stay the five kinds only
    const eventSection = sql.slice(sql.indexOf('CREATE TABLE IF NOT EXISTS ka_gochara_sky_event'))
    expect(eventSection).toContain("'sign_ingress','nakshatra_ingress','kakshya_crossing','station','eclipse_instant'")
    // 1155's transit rows reference the contact, not the sky event
    const rec = readMigration(1155)
    expect(rec).toContain('REFERENCES ka_gochara_contact (contact_id, body, physical_object_id)')
    expect(rec).not.toContain('REFERENCES ka_gochara_sky_event')
    // legacy mapping stated: legacy rows not migrated, referenced by generation
    expect(sql).toContain('kala_gochara_contacts')
    expect(sql).toMatch(/NOT\s+migrated/i)
  })

  it('amendment 3: JSON reference lists are normalised into membership tables with real FKs', () => {
    const rp = readMigration(1154)
    expect(rp).toContain('CREATE TABLE IF NOT EXISTS ka_gochara_rule_path_prerequisite')
    expect(rp).toContain('CREATE TABLE IF NOT EXISTS ka_gochara_rule_path_soft_factor')
    expect(rp).toContain('REFERENCES ka_gochara_predicate (predicate_id, rule_version)')
    expect(rp).toContain('REFERENCES ka_gochara_factor (factor_id, rule_version)')
    expect(rp).not.toContain('FUNCTION ka_gochara_composite_refs_ok')

    const rec = readMigration(1155)
    expect(rec).toContain('CREATE TABLE IF NOT EXISTS ka_gochara_record_prerequisite')
    expect(rec).toContain('REFERENCES ka_gochara_predicate (predicate_id, rule_version)')
    expect(rec).not.toContain('ka_gochara_composite_refs_ok(')

    const win = readMigration(1156)
    expect(win).toContain('CREATE TABLE IF NOT EXISTS ka_gochara_eval_window_record')
    expect(win).toContain('REFERENCES ka_gochara_eval_window (window_id, chart_id, generation)')
    expect(win).toContain('REFERENCES ka_gochara_relationship_record (record_id, chart_id, generation)')
    expect(win).not.toMatch(/record_ids\s+UUID\[\]/)
  })

  it('amendment 3: path_id/rule_version are NOT NULL complete references in 1155 and 1156', () => {
    for (const n of [1155, 1156] as const) {
      const sql = readMigration(n)
      expect(sql).toMatch(/path_id\s+TEXT NOT NULL/)
      expect(sql).toMatch(/rule_version\s+TEXT NOT NULL/)
      expect(sql).toContain('REFERENCES ka_gochara_rule_path (path_id, rule_version)')
    }
  })

  it('amendment 4: coverage is bound to chart/generation/partition via composite FK to kala_gochara_coverage', () => {
    for (const n of [1155, 1156] as const) {
      const sql = readMigration(n)
      expect(sql).toContain('coverage_partition_kind')
      expect(sql).toContain('coverage_partition_key')
      expect(sql).toContain(
        'REFERENCES kala_gochara_coverage (chart_id, generation, partition_kind, partition_key)',
      )
      expect(sql).not.toContain('kala_gochara_publication(manifest_id)')
    }
    // composite consistency: event/contact agree with their physical object
    const sub = readMigration(1153)
    expect(sub).toContain('REFERENCES ka_gochara_physical_object (physical_object_id, body, convention_id)')
  })

  it('amendment 5: typed temporal_support, transit precision, NOT NULL valence, admission persistence', () => {
    const rec = readMigration(1155)
    expect(rec).toContain('temporal_support_state')
    expect(rec).toContain('kgrr_support_cardinality_ck')
    expect(rec).toContain('admission_state')
    expect(rec).toContain('house_from_frame')
    expect(rec).toMatch(/outcome_valence_for_native TEXT NOT NULL/)
    expect(rec).toContain('ka_gochara_precision_ok')
    expect(rec).toMatch(/AND contact_id IS NOT NULL AND precision IS NOT NULL/)
    const win = readMigration(1156)
    expect(win).toMatch(/outcome_valence_for_native TEXT NOT NULL/)
    // coverage JSONB requires an explicit boolean truncated key ('?' operator)
    const sub = readMigration(1153)
    expect(sub).toContain("coverage ? 'truncated'")
    expect(sub).toContain('kgse_exact_precision_ck')
  })

  it('amendment 6: correction identity — correction_seq, supersedes rules, no self-supersession', () => {
    const sub = readMigration(1153)
    expect(sub).toContain('correction_seq')
    expect(sub).toContain('kgse_no_self_supersede_ck')
    expect(sub).toContain('kgc_no_self_supersede_ck')
    expect(sub).toContain('kgse_correction_edge_ck')
    expect(sub).toContain('kgc_correction_edge_ck')
    expect(sub).toContain('ka_gochara_sky_event_supersede_guard')
    expect(sub).toContain('ka_gochara_contact_supersede_guard')
    expect(sub).toContain('ka_gochara_contact_lifecycle_guard')
  })

  it('amendment 7 (steward ruling): factor mapping discipline — no invented numbers, score/interval CHECKs', () => {
    const reg = readMigration(1154)
    expect(reg).toContain('kgf_range_unit_interval_ck')
    expect(reg).toContain('kgf_calibration_status_ck')
    expect(reg).toContain('kgf_mapping_discipline_ck')
    expect(reg).toContain("'uncalibrated_default','calibrated'")
    expect(reg).toMatch(/score_rule\s+TEXT NOT NULL/)
    const win = readMigration(1156)
    expect(win).toContain('kgew_score_unit_interval_ck')
    expect(win).toContain('kgew_interval_nonempty_ck')
    expect(win).toContain('kgew_peak_in_interval_ck')
    expect(win).toContain('kgew_evidence_for_nn_ck')
  })

  it('amendment 9: typed frame/selector domains, relative-frame invariant, citation rule, aligned ruling CHECK', () => {
    const reg = readMigration(1154)
    expect(reg).toContain('ka_gochara_frame_ok')
    expect(reg).toContain('ka_gochara_object_selector_ok')
    expect(reg).toContain('ka_gochara_named_operands_ok')
    // aligned ruling rule: required for uncited_extension, never forbidden otherwise
    for (const n of [1154, 1155] as const) {
      const sql = readMigration(n)
      expect(sql).toContain("provenance <> 'uncited_extension' OR ruling_ref IS NOT NULL")
      expect(sql).not.toContain('(ruling_ref IS NOT NULL)\n         = (provenance')
    }
    const rec = readMigration(1155)
    expect(rec).toContain('kgrr_relative_frame_ck')
    expect(rec).toContain('kgrr_citation_ck')
    expect(rec).toContain('ka_gochara_string_array_ok(source_fact_ids)')
  })

  it('event_class CHECKs enumerate exactly the 27 protocol classes', () => {
    for (const n of [1155, 1156] as const) {
      const sql = readMigration(n)
      for (const cls of EVENT_CLASS_LIST) expect(sql).toContain(`'${cls}'`)
    }
  })

  it('D-SCOPE disposition: canonical-chart CHECK on the per-chart tables', () => {
    for (const sql of [readMigration(1153), readMigration(1155), readMigration(1156)]) {
      expect(sql).toContain('482012f1-710e-4a25-994a-93821f5871aa')
    }
  })

  it.each([1153, 1154, 1155, 1156, 1157] as const)(
    'amendment 8: preflight %i fails closed (DO + RAISE) and ends with a success NOTICE',
    n => {
      const sql = readPreflight(n)
      expect(sql).toMatch(/DO \$\$/)
      expect(sql).toContain(`preflight ${n} BLOCKED`)
      expect(sql).toContain(`preflight ${n}: all checks passed`)
    },
  )

  it.each([1153, 1154, 1155, 1156, 1157] as const)(
    'amendment 8: preflight %i uses wildcard-safe ledger lookups (no LIKE wildcard bug)',
    n => {
      const sql = readPreflight(n)
      expect(sql).not.toMatch(/filename\s+LIKE\s+'\d+_%'/)
      expect(sql).toContain(`starts_with(filename, '${n}_')`)
    },
  )

  it('amendment 8: preflights 1155/1156 gate on ordered prerequisite application', () => {
    expect(readPreflight(1155)).toContain("('1153_'), ('1154_')")
    expect(readPreflight(1156)).toContain("('1153_'), ('1154_'), ('1155_')")
  })

  it('amendment 8: preflights scope trigger lookups to the intended table and pin function signatures', () => {
    for (const n of [1153, 1154, 1157] as const) {
      const sql = readPreflight(n)
      expect(sql).toContain('t.tgrelid')
      expect(sql).toContain('pg_get_function_identity_arguments')
    }
    // 1155/1156 verify parent PK/UNIQUE definitions, not just columns
    expect(readPreflight(1155)).toContain('parent_key_missing')
    expect(readPreflight(1156)).toContain('parent_key_missing')
    // 1156 checks the relationship-record parent the round-1 preflight omitted
    expect(readPreflight(1156)).toContain('ka_gochara_relationship_record')
  })
})

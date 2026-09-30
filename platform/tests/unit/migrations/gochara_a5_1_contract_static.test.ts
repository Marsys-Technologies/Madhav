// @vitest-environment node
/**
 * Pravāha A5.1 round 3 — STATIC contract checks on migrations 1153–1157 and
 * their preflights, asserted against the on-disk SQL itself (CLAUDE.md §N.8:
 * the detector reads what ships).
 *
 * Covers what is checkable without a database from ASTRA_REVIEW_A5_1_MIGRATIONS
 * v1_1 (F1–F11) and the round-1 amendments kept closed:
 *   - amendment 2: no migration-owned BEGIN/COMMIT (the runner owns the one
 *     transaction) and no business-data DML at migration time (function
 *     bodies excluded — the seal-recording trigger legitimately INSERTs);
 *   - F8/F9: every migration pins search_path, embeds its preflight gate
 *     BYTE-IDENTICALLY to the standalone preflight file (so the production
 *     deploy path observes the gate), matches functions by argument TYPES
 *     (never the name-retaining identity-arguments text), and ends with a
 *     definition-verification block whose embedded expectation is real,
 *     non-empty JSON naming the tables and functions the migration owns;
 *   - F1–F7, F11: the contracted tables, columns, constraints and triggers
 *     are present by name.
 *
 * Live-DB behaviour is covered by tests/integration/gochara_a5_1_migrations.db.test.ts.
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

const ALL = [1153, 1154, 1155, 1156, 1157] as const

function readMigration(n: keyof typeof MIGRATIONS): string {
  return fs.readFileSync(path.join(MIGRATIONS_DIR, MIGRATIONS[n]), 'utf8')
}
function readPreflight(n: keyof typeof PREFLIGHTS): string {
  return fs.readFileSync(path.join(PREFLIGHT_DIR, PREFLIGHTS[n]), 'utf8')
}

/** The gate DO block: from the `DO $$` line after `marker` to the first `$$;` line. */
function gateBlock(src: string, marker?: string): string {
  const lines = src.split('\n')
  let from = 0
  if (marker) {
    from = lines.findIndex(l => l.startsWith(marker))
    if (from < 0) throw new Error(`marker not found: ${marker}`)
  }
  const doIdx = lines.findIndex((l, i) => i >= from && l === 'DO $$')
  const endIdx = lines.findIndex((l, i) => i >= doIdx && l === '$$;')
  if (doIdx < 0 || endIdx < 0) throw new Error('DO block not found')
  return lines.slice(doIdx, endIdx + 1).join('\n')
}

/** Strip dollar-quoted bodies ($$…$$, $tag$…$tag$) so function bodies are not scanned as top-level DML. */
function withoutDollarBodies(sql: string): string {
  return sql.replace(/\$([A-Za-z_]*)\$[\s\S]*?\$\1\$/g, '$BODY$')
}

/** The embedded expected-definition JSON of the verification block. */
function expectedJson(n: keyof typeof MIGRATIONS): { tables: Record<string, unknown>; functions: Record<string, unknown> } {
  const sql = readMigration(n)
  const m = /\$expected\$\n([\s\S]*?)\n\$expected\$::jsonb\)/.exec(sql)
  if (!m) throw new Error(`no $expected$ block in ${MIGRATIONS[n]}`)
  return JSON.parse(m[1]!)
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

describe('A5.1 migrations 1153–1157 — static contract (round 3)', () => {
  it.each(ALL)('amendment 2: migration %i owns NO transaction (no BEGIN/COMMIT; runner owns it)', n => {
    const sql = readMigration(n)
    expect(sql).not.toMatch(/^\s*BEGIN\s*;/im)
    expect(sql).not.toMatch(/^\s*COMMIT\s*;/im)
    expect(sql).not.toMatch(/^\s*ROLLBACK\s*;/im)
    expect(sql).toMatch(/^SET LOCAL lock_timeout/m)
  })

  it.each(ALL)('migration %i performs no business-data DML at migration time (function bodies excluded)', n => {
    const sql = withoutDollarBodies(readMigration(n))
    expect(sql).not.toMatch(/^\s*INSERT\s+INTO\b/im)
    expect(sql).not.toMatch(/^\s*UPDATE\s+\w/im)
    expect(sql).not.toMatch(/^\s*DELETE\s+FROM\b/im)
    expect(sql).not.toMatch(/^\s*TRUNCATE\b/im)
  })

  it.each(ALL)('F9: migration %i pins schema resolution and orders gate → DDL → verification', n => {
    const sql = readMigration(n)
    const pin = sql.indexOf('SET LOCAL search_path = public, pg_catalog;')
    const gate = sql.indexOf('-- ── GATE (byte-identical to preflight_')
    const firstCreate = sql.search(/^CREATE (OR REPLACE FUNCTION|TABLE IF NOT EXISTS)/m)
    const verify = sql.indexOf(`ka_gochara_verify_definitions('${n}'`)
    expect(pin).toBeGreaterThan(-1)
    expect(gate).toBeGreaterThan(pin)
    expect(firstCreate).toBeGreaterThan(gate)
    expect(verify).toBeGreaterThan(firstCreate)
    // the verification block is the tail of the file
    expect(sql.slice(verify)).not.toMatch(/^CREATE /m)
  })

  it.each(ALL)('F8/F9: the gate embedded in migration %i is byte-identical to its preflight file', n => {
    const embedded = gateBlock(readMigration(n), '-- ── GATE (byte-identical to preflight_')
    const standalone = gateBlock(readPreflight(n))
    expect(embedded).toBe(standalone)
    expect(embedded).toContain(`preflight ${n} BLOCKED`)
    expect(embedded).toContain(`preflight ${n}: all checks passed`)
    expect(embedded).toContain("current_setting('ka_gochara.deliberate_replay', true)")
    // the preflight file references the migration it mirrors
    expect(readPreflight(n)).toContain(MIGRATIONS[n])
  })

  it.each(ALL)('F8: preflight %i matches functions by argument TYPES, not identity-arguments text', n => {
    const sql = readPreflight(n)
    expect(sql).not.toMatch(/pg_get_function_identity_arguments\(p\.oid\)\s*=/)
    if (n !== 1157) {
      // collision detection by proargtypes (1157 owns no standalone function)
      expect(sql).toContain('format_type(u.oid, NULL) ORDER BY u.ord')
      expect(sql).toContain('unnest(p.proargtypes) WITH ORDINALITY')
    }
    if (n !== 1153) {
      // helper-presence checks by exact regprocedure signature (1153 is the root: it defines the helpers)
      expect(sql).toContain('to_regprocedure(')
    }
  })

  it.each(ALL)('amendment 8: preflight %i uses wildcard-safe ledger lookups and scoped trigger lookups', n => {
    const sql = readPreflight(n)
    expect(sql).not.toMatch(/filename\s+LIKE\s+'\d+_%'/)
    expect(sql).toContain(`starts_with(m.filename, '${n}_')`)
    expect(sql).toContain('t.tgrelid')
    expect(sql).toContain("has_schema_privilege('public', 'CREATE')")
    expect(sql).toContain("has_schema_privilege('public', 'USAGE')")
  })

  it('F9: preflights gate on ordered prerequisite application', () => {
    expect(readPreflight(1154)).toContain("(VALUES ('1153_')) AS p(prefix)")
    expect(readPreflight(1155)).toContain("(VALUES ('1153_'), ('1154_')) AS p(prefix)")
    expect(readPreflight(1156)).toContain("(VALUES ('1153_'), ('1154_'), ('1155_')) AS p(prefix)")
    expect(readPreflight(1157)).toContain("(VALUES ('1153_')) AS p(prefix)")
    // parents verified by key definition, not just column presence
    for (const n of [1153, 1155, 1156] as const) {
      expect(readPreflight(n)).toContain('parent_key_missing')
      expect(readPreflight(n)).toContain("c.contype IN ('p','u')")
    }
    expect(readPreflight(1153)).toContain("has_table_privilege(p.t, 'REFERENCES')")
    expect(readPreflight(1153)).toContain("has_table_privilege('public.kala_gochara_publication', 'TRIGGER')")
  })

  it.each(ALL)('F9: migration %i embeds a real, non-empty definition expectation', n => {
    const exp = expectedJson(n)
    expect(Object.keys(exp.tables).length).toBeGreaterThan(0)
    for (const [tbl, spec] of Object.entries(exp.tables)) {
      const s = spec as { columns: Record<string, unknown>; constraints: Record<string, unknown>; triggers: Record<string, unknown>; indexes: Record<string, unknown> }
      expect(Object.keys(s.columns).length, `${tbl} columns`).toBeGreaterThan(0)
      expect(Object.keys(s.constraints).length, `${tbl} constraints`).toBeGreaterThan(0)
      // every table has a PRIMARY KEY in its verified definition (F9: 1157 never verified its PK)
      const hasPk = Object.values(s.constraints).some(c => (c as unknown[])[0] === 'p')
      expect(hasPk, `${tbl} primary key verified`).toBe(true)
      // no CHECK is a bare `true`
      for (const [cn, c] of Object.entries(s.constraints)) {
        const def = (c as unknown[])[1] as string
        expect(def, `${tbl}.${cn}`).not.toBe('checktrue')
      }
    }
    // the migration's own tables are the ones verified
    const created = [...readMigration(n).matchAll(/CREATE TABLE IF NOT EXISTS public\.(\w+)/g)].map(m => m[1]!)
    expect(Object.keys(exp.tables).sort()).toEqual(created.sort())
  })

  it('F1/F4: the contact identity is separate from its generation-scoped ledger; the frozen hash recipe has no extra component', () => {
    const sql = readMigration(1153)
    expect(sql).toContain('CREATE TABLE IF NOT EXISTS public.ka_gochara_contact_identity')
    expect(sql).toContain('CREATE TABLE IF NOT EXISTS public.ka_gochara_contact')
    expect(sql).toContain('PRIMARY KEY (chart_id, generation, contact_id)')
    expect(sql).toContain('UNIQUE (physical_object_id, occurrence_ordinal)')
    expect(sql).not.toMatch(/correction_seq\s+INTEGER/)   // withdrawn: no column, no hash component
    expect(sql).toContain('ka_gochara_contact_identity_fk')
    expect(sql).toContain('kgci_supersedes_uq UNIQUE (supersedes_contact_id)')
    expect(sql).toContain('kgse_supersedes_uq UNIQUE (supersedes_event_id)')
    // boundary events stay the five kinds only
    const eventSection = sql.slice(sql.indexOf('CREATE TABLE IF NOT EXISTS public.ka_gochara_sky_event'))
    expect(eventSection).toContain("'sign_ingress','nakshatra_ingress','kakshya_crossing','station','eclipse_instant'")
    // legacy mapping stated: legacy rows not migrated, referenced by generation
    expect(sql).toContain('kala_gochara_contacts')
    expect(sql).toMatch(/NOT\s+migrated/i)
    // F4: truncated ⇔ clipped_truncated on both identity-bearing tables
    expect(sql).toContain('kgse_truncated_method_ck')
    expect(sql).toContain('kgc_truncated_method_ck')
  })

  it('F1/F7: every contact reference is ownership-bound and relation-exact', () => {
    const rec = readMigration(1155)
    expect(rec).toContain('FOREIGN KEY (chart_id, generation, contact_id, agent, relation, object_id)')
    expect(rec).toContain('REFERENCES public.ka_gochara_contact (chart_id, generation, contact_id, body, relation_kind, physical_object_id)')
    expect(rec).not.toContain('REFERENCES ka_gochara_sky_event')
    const sub = readMigration(1153)
    expect(sub).toContain('REFERENCES public.ka_gochara_physical_object (physical_object_id, body, relation_kind, convention_id)')
    expect(sub).toContain('FOREIGN KEY (physical_object_id, body, event_kind, convention_id)')
    expect(sub).toContain('kgc_reference_uq')
  })

  it('F2: permanent publication seal, serialization lock, and TRUNCATE refusal on every owned table', () => {
    const sub = readMigration(1153)
    expect(sub).toContain('CREATE TABLE IF NOT EXISTS public.ka_gochara_generation_seal')
    expect(sub).toContain('ka_gochara_publication_seal_record')
    expect(sub).toContain('AFTER INSERT OR UPDATE OF status ON public.kala_gochara_publication')
    expect(sub).toContain('ka_gochara_generation_is_sealed')
    expect(sub).toContain("p.status <> 'candidate' OR p.published_at IS NOT NULL")
    // the seal writer and the ONE reader predicate take the same lock (code form, not prose)
    const lockCalls = sub.match(/PERFORM pg_advisory_xact_lock\(hashtext\('ka_gochara_generation:' \|\| /g) ?? []
    expect(lockCalls.length).toBe(2)
    for (const n of ALL) {
      const sql = readMigration(n)
      const tables = [...sql.matchAll(/CREATE TABLE IF NOT EXISTS public\.(\w+)/g)].map(m => m[1]!)
      for (const t of tables) {
        expect(sql, `${t} TRUNCATE guard`).toMatch(new RegExp(`BEFORE TRUNCATE ON public\\.${t}\\n`))
      }
    }
  })

  it('F3: rule-version membership is sealed after construction; only sealed versions are referenced', () => {
    const reg = readMigration(1154)
    expect(reg).toContain('CREATE TABLE IF NOT EXISTS public.ka_gochara_rule_path_seal')
    expect(reg).toContain('ka_gochara_membership_guard')
    expect(reg).toContain('ka_gochara_require_sealed_rule_path')
    expect(reg).toContain('BEFORE INSERT ON public.ka_gochara_rule_path_prerequisite')
    expect(reg).toContain('BEFORE INSERT ON public.ka_gochara_rule_path_soft_factor')
    expect(readMigration(1155)).toContain('BEFORE INSERT OR UPDATE OF path_id, rule_version ON public.ka_gochara_relationship_record')
    expect(readMigration(1156)).toContain('BEFORE INSERT OR UPDATE OF path_id, rule_version ON public.ka_gochara_eval_window')
  })

  it('F5: validators are total and every helper CHECK asks IS TRUE; qualification is finalised at commit', () => {
    const reg = readMigration(1154)
    expect(reg).toContain('SELECT COALESCE(CASE frame_kind')
    const rec = readMigration(1155)
    expect(rec).toContain("jsonb_typeof(p -> 'solver_method') = 'string'")
    expect(rec).toContain('DEFERRABLE INITIALLY DEFERRED')
    expect(rec).toContain('CREATE CONSTRAINT TRIGGER ka_gochara_rr_finalize')
    expect(rec).toContain('CREATE CONSTRAINT TRIGGER ka_gochara_rpr_finalize')
    expect(rec).toContain('ka_gochara_record_finalize_check')
    for (const n of ALL) {
      const sql = readMigration(n)
      const helperChecks = sql.match(/CHECK \((?:[^)]*\n)*?[^)]*public\.ka_gochara_\w+_ok\([^]*?\)\)/g) ?? []
      for (const chk of helperChecks) {
        // each helper call inside a CHECK is followed by IS TRUE
        const calls = chk.match(/public\.ka_gochara_\w+_ok\([^()]*(?:\([^()]*\)[^()]*)*\)(?! IS TRUE)/g) ?? []
        expect(calls, `helper call without IS TRUE in migration ${n}: ${chk.slice(0, 120)}`).toEqual([])
      }
    }
  })

  it('F6: factor discipline is exactly C2 — no uncalibrated-mapping prohibition, no ordering demand', () => {
    const reg = readMigration(1154)
    expect(reg).toContain('kgf_range_unit_interval_ck')
    expect(reg).toContain('kgf_calibration_status_ck')
    expect(reg).toContain('kgf_calibrated_requires_mapping_ck')
    expect(reg).toContain("CHECK (calibration_status <> 'calibrated' OR category_mapping IS NOT NULL)")
    expect(reg).not.toContain('kgf_mapping_discipline_ck')
    expect(reg).not.toMatch(/uncalibrated_default'\s*AND\s*category_mapping IS NULL/)
    expect(reg).toMatch(/score_rule\s+TEXT NOT NULL/)
  })

  it('F7: coverage applicability guards, the convention bridge, and class/path-bound window membership', () => {
    expect(readMigration(1153)).toContain('CREATE TABLE IF NOT EXISTS public.ka_gochara_convention_bridge')
    const rec = readMigration(1155)
    expect(rec).toContain('ka_gochara_record_coverage_guard')
    expect(rec).toContain('relations_searched')
    expect(rec).toContain('completed_horizon @> ct.t_in')
    expect(rec).toContain('ka_gochara_convention_bridge')
    expect(rec).toContain("(NEW.agent = 'moon') <> (cov.partition_kind = 'moon_on_demand')")
    const win = readMigration(1156)
    expect(win).toContain('ka_gochara_window_coverage_guard')
    expect(win).toContain('completed_horizon @> NEW.interval')
    expect(win).toContain('REFERENCES public.ka_gochara_eval_window (window_id, chart_id, generation, event_class, path_id, rule_version)')
    expect(win).toContain('REFERENCES public.ka_gochara_relationship_record (record_id, chart_id, generation, event_class, path_id, rule_version)')
    for (const n of [1155, 1156] as const) {
      const sql = readMigration(n)
      expect(sql).toContain('REFERENCES public.kala_gochara_coverage (chart_id, generation, partition_kind, partition_key)')
      expect(sql).not.toContain('kala_gochara_publication(manifest_id)')
    }
  })

  it('F11: declared selector encoding, finite numeric domains, non-empty AV category elements', () => {
    const reg = readMigration(1154)
    expect(reg).toContain('ka_gochara_selector_token_ok')
    expect(reg).toContain("'^[a-z][a-z0-9_]*([.:/][a-z0-9_]+)*$'")
    const sub = readMigration(1153)
    expect(sub).toContain('ka_gochara_finite_nonneg_ok')
    expect(sub).toContain('kgse_uncertainty_finite_ck')
    expect(sub).toContain('kgc_uncertainty_finite_ck')
    expect(sub).toContain('kgse_longitude_range_ck')
    expect(readMigration(1155)).toContain('kgrr_evidence_finite_ck')
    expect(readMigration(1156)).toContain('kgew_evidence_finite_ck')
    expect(readMigration(1157)).toContain('ka_gochara_text_array_ok(applies_to_fact_categories, 1)')
    // fact-id resolvability is an explicit writer-boundary disposition
    expect(readMigration(1155)).toMatch(/RESOLVABILITY[\s\S]*WRITER-BOUNDARY/)
  })

  it('amendment 5/9 (kept): typed support states, NOT NULL valence, admission persistence, frame/citation/ruling rules', () => {
    const rec = readMigration(1155)
    expect(rec).toContain('kgrr_support_cardinality_ck')
    expect(rec).toContain('admission_state')
    expect(rec).toContain('kgrr_evaluated_has_house_ck')
    expect(rec).toMatch(/outcome_valence_for_native\s+TEXT NOT NULL/)
    expect(rec).toMatch(/AND contact_id IS NOT NULL AND precision IS NOT NULL/)
    expect(rec).toContain('kgrr_relative_frame_ck')
    expect(rec).toContain('kgrr_citation_ck')
    for (const n of [1154, 1155] as const) {
      expect(readMigration(n)).toContain("provenance <> 'uncited_extension' OR ruling_ref IS NOT NULL")
    }
    expect(readMigration(1156)).toMatch(/outcome_valence_for_native TEXT NOT NULL/)
    expect(readMigration(1156)).toContain('kgew_score_unit_interval_ck')
    expect(readMigration(1156)).toContain('kgew_peak_in_interval_ck')
  })

  it('event_class CHECKs enumerate exactly the 27 protocol classes', () => {
    for (const n of [1155, 1156] as const) {
      const sql = readMigration(n)
      for (const cls of EVENT_CLASS_LIST) expect(sql).toContain(`'${cls}'`)
    }
  })

  it('D-SCOPE disposition: canonical-chart CHECK on the per-chart tables; never on the seal', () => {
    for (const sql of [readMigration(1153), readMigration(1155), readMigration(1156)]) {
      expect(sql).toContain('482012f1-710e-4a25-994a-93821f5871aa')
    }
    const sealSection = readMigration(1153).split('CREATE TABLE IF NOT EXISTS public.ka_gochara_generation_seal')[1]!
      .split('CREATE TABLE IF NOT EXISTS')[0]!
    expect(sealSection).not.toContain('482012f1')
  })
})

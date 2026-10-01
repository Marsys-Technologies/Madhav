// @vitest-environment node
/**
 * Pravāha A5.1 round 7 — STATIC contract checks on migrations 1153–1157, their
 * preflights, the runner's protected-file refusal and the deploy window,
 * asserted against the on-disk sources (CLAUDE.md §N.8: the detector reads
 * what ships).
 *
 * Steward rulings (ASTRA_REVIEW_A5_1_MIGRATIONS v1_2 N1–N11, v1_3 N12–N15 + P2,
 * with the CORRECTED lock ruling superseding the round-4 "orchestrator's keys"):
 *   1. NO trigger on any existing table; the seal is written explicitly by
 *      ka_gochara_seal_generation(); legacy generations are refused by
 *      ka_gochara_generation_governed on every chart-scoped table. Foreign keys
 *      to charts / kala_gochara_convention / kala_gochara_coverage are DISCLOSED
 *      (P2), not denied.
 *   A. The Gochara-5 FAMILY keys (N12): pg_advisory_xact_lock over
 *      hashtext('gochara5:chart:' || chart_id) and hashtext('gochara5:global');
 *      NEVER the orchestrator's session keys (hashtext(chart_id) /
 *      hashtext('nirmana-global-assets')), which the scheduler holds on its
 *      main connection while writers run on worker connections.
 *   B. Fixed, ENFORCED order (N13): chart-scoped mutators take the chart key
 *      EXCLUSIVE first, then (if they read rule-path seal state) the global
 *      key SHARED; registry/seal/membership mutators take the global key
 *      EXCLUSIVE and never a chart key; refusals raise BEFORE any family lock;
 *      the family key precedes tuple locks via BEFORE … FOR EACH STATEMENT
 *      triggers; SUBSTRATE ORDER (v1_4): every table without a family key of
 *      its own takes the chart key of the chart the transaction serves FIRST
 *      (or refuses without a chart context), so no substrate unique/tuple
 *      wait can be held into a chart-key wait; ONE CHART PER TRANSACTION
 *      (v1_5, N18): the transaction is bound at the lock boundary, a
 *      different chart is refused before another key, and the canonical-only
 *      scope is enforced there.
 *   3. NO custom verifier and NO replay GUC; presence checks only.
 *   4. 1153–1157 apply through the protected public-schema window; the routine
 *      runner refuses them.
 *   D. N14/N17/N19 unambiguous coverage facts over the ACCEPTED domain
 *      (finite, bounded, non-empty horizons with every bound within
 *      1000-01-01 ≤ t < 3000-01-01 UTC, AD only — everything else refused, so
 *      the four-digit ISO encoding is a lossless bijection); N10/N16
 *      consumer contract (ka_gochara_coverage_drift + seal refusal +
 *      window-contributor applicability re-checked over EVERY membership at
 *      the seal boundary); N7/N15 precision-only re-sync skips coverage
 *      re-validation; P2 honest operational assertions.
 *
 * Live-DB behaviour is covered by tests/integration/gochara_a5_1_migrations.db.test.ts.
 */
import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS, assertGeneralRunnerMayApplyPublicSchema } from '../../../scripts/migrate'

const MIGRATIONS_DIR = path.resolve(process.cwd(), 'migrations')
const PREFLIGHT_DIR = path.resolve(process.cwd(), '../platform/python-sidecar/scripts/kala_gochara_cutover')
const LOCKS_PY = path.resolve(process.cwd(), 'python-sidecar/pipeline/orchestrator/locks.py')
const RUNNER_PY = path.resolve(process.cwd(), 'python-sidecar/pipeline/orchestrator/runner.py')

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

/** Strip dollar-quoted bodies so function bodies are not scanned as top-level DML. */
function withoutDollarBodies(sql: string): string {
  return sql.replace(/\$([A-Za-z_]*)\$[\s\S]*?\$\1\$/g, '$BODY$')
}

/** Every `CREATE OR REPLACE FUNCTION public.<name>(…)` with its dollar-quoted body. */
function functionBodies(sql: string): Array<{ name: string; body: string }> {
  const out: Array<{ name: string; body: string }> = []
  const re = /CREATE OR REPLACE FUNCTION public\.(\w+)\([^)]*\)[\s\S]*?AS \$\$([\s\S]*?)\$\$;/g
  let m: RegExpExecArray | null
  while ((m = re.exec(sql)) !== null) out.push({ name: m[1]!, body: m[2]! })
  return out
}

/** Tables a migration creates. */
function createdTables(sql: string): string[] {
  return [...sql.matchAll(/CREATE TABLE IF NOT EXISTS public\.(\w+)/g)].map(m => m[1]!)
}

const CHART_SCOPED = new Set([
  'ka_gochara_generation_seal', 'ka_gochara_contact', 'ka_gochara_relationship_record',
  'ka_gochara_record_prerequisite', 'ka_gochara_eval_window', 'ka_gochara_eval_window_record',
])
/** Chart-scoped tables that permit UPDATE/DELETE at all (the seal refuses both before any lock). */
const CHART_SCOPED_MUTABLE = [...CHART_SCOPED].filter(t => t !== 'ka_gochara_generation_seal')

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

describe('A5.1 migrations 1153–1157 — static contract (round 7, corrected lock ruling)', () => {
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

  it.each(ALL)('F9: migration %i pins schema resolution and orders gate → DDL → presence checks', n => {
    const sql = readMigration(n)
    const pin = sql.indexOf('SET LOCAL search_path = public, pg_catalog;')
    const gate = sql.indexOf('-- ── GATE (byte-identical to preflight_')
    const firstCreate = sql.search(/^CREATE (OR REPLACE FUNCTION|TABLE IF NOT EXISTS)/m)
    const presence = sql.indexOf(`migration ${n} post-apply check failed`)
    expect(pin).toBeGreaterThan(-1)
    expect(gate).toBeGreaterThan(pin)
    expect(firstCreate).toBeGreaterThan(gate)
    expect(presence).toBeGreaterThan(firstCreate)
    expect(sql).toContain(`migration ${n}: presence checks passed`)
  })

  it.each(ALL)('F8/F9: the gate embedded in migration %i is byte-identical to its preflight file', n => {
    const embedded = gateBlock(readMigration(n), '-- ── GATE (byte-identical to preflight_')
    const standalone = gateBlock(readPreflight(n))
    expect(embedded).toBe(standalone)
    expect(embedded).toContain(`preflight ${n} BLOCKED`)
    expect(embedded).toContain(`preflight ${n}: all checks passed`)
    expect(readPreflight(n)).toContain(MIGRATIONS[n])
  })

  it.each(ALL)('F8: preflight %i matches functions by argument TYPES, not identity-arguments text', n => {
    const sql = readPreflight(n)
    expect(sql).not.toMatch(/pg_get_function_identity_arguments\(p\.oid\)\s*=/)
    if (n !== 1157) {
      expect(sql).toContain('format_type(u.oid, NULL) ORDER BY u.ord')
      expect(sql).toContain('unnest(p.proargtypes) WITH ORDINALITY')
    }
    if (n !== 1153) expect(sql).toContain('to_regprocedure(')
  })

  it.each(ALL)('amendment 8: preflight %i uses wildcard-safe ledger lookups and scoped trigger lookups', n => {
    const sql = readPreflight(n)
    expect(sql).not.toMatch(/filename\s+LIKE\s+'\d+_%'/)
    expect(sql).toContain(`starts_with(m.filename, '${n}_')`)
    expect(sql).toContain('t.tgrelid')
    expect(sql).toContain("has_schema_privilege('public', 'CREATE')")
    expect(sql).toContain("has_schema_privilege('public', 'USAGE')")
  })

  it('F9: preflights gate on ordered prerequisite application and parent keys', () => {
    expect(readPreflight(1154)).toContain("(VALUES ('1153_')) AS p(prefix)")
    expect(readPreflight(1155)).toContain("(VALUES ('1153_'), ('1154_')) AS p(prefix)")
    expect(readPreflight(1156)).toContain("(VALUES ('1153_'), ('1154_'), ('1155_')) AS p(prefix)")
    expect(readPreflight(1157)).toContain("(VALUES ('1153_')) AS p(prefix)")
    for (const n of [1153, 1155, 1156] as const) {
      expect(readPreflight(n)).toContain('parent_key_missing')
      expect(readPreflight(n)).toContain("c.contype IN ('p','u')")
    }
    expect(readPreflight(1153)).toContain("has_table_privilege(p.t, 'REFERENCES')")
    // every helper the later files depend on is gated by exact signature, including the round-5 ones
    expect(readPreflight(1154)).toContain("('ka_gochara_lock_global_shared()')")
    expect(readPreflight(1155)).toContain("('ka_gochara_chart_statement_lock()')")
    expect(readPreflight(1156)).toContain("('ka_gochara_coverage_facts(text,tstzrange,text[])')")
    expect(readPreflight(1156)).toContain("('ka_gochara_facts_horizon(jsonb)')")
    expect(readPreflight(1157)).toContain("('ka_gochara_insert_only()')")
  })

  // ── Ruling 3: no verifier, no replay GUC — presence checks only ──────────
  it.each(ALL)('ruling 3 (N4): migration %i has no custom definition verifier and no replay mode', n => {
    const sql = readMigration(n)
    expect(sql).not.toContain('deliberate_replay')
    expect(sql).not.toContain('ka_gochara_verify_definitions')
    expect(sql).not.toContain('ka_gochara_norm_def')
    expect(sql).not.toContain('$expected$')
    expect(readPreflight(n)).not.toContain('deliberate_replay')
    // presence checks name their tables, constraints (validated) and triggers
    expect(sql).toContain('AND c.convalidated')
    expect(sql).toContain("NOT t.tgisinternal AND t.tgenabled = 'O'")
  })

  // ── Ruling 1: no trigger on any existing table; explicit seal; legacy refused ──
  it('ruling 1 (N1): no trigger on any existing table; FKs only to charts / convention / coverage (disclosed); the seal is explicit; legacy generations are refused', () => {
    const sub = readMigration(1153)
    expect(sub).not.toContain('ON public.kala_gochara_publication')
    expect(sub).not.toContain('REFERENCES public.kala_gochara_publication')
    expect(sub).not.toContain('ka_gochara_record_generation_seal')
    expect(sub).toContain('CREATE OR REPLACE FUNCTION public.ka_gochara_seal_generation(p_chart_id uuid, p_generation text)')
    expect(sub).toContain('CREATE OR REPLACE FUNCTION public.ka_gochara_generation_governed(g text)')
    expect(sub).toContain("g ~ '^([5-9]|[1-9][0-9]+)\\.[0-9]+$'")
    expect(sub).toContain("ka_gochara_generation_governed('4.1') IS FALSE")
    expect(sub).toContain("ka_gochara_generation_governed('v1') IS FALSE")
    // every chart-scoped table CHECKs the governed generation
    for (const n of ALL) {
      const sql = readMigration(n)
      for (const t of createdTables(sql)) {
        if (!CHART_SCOPED.has(t)) continue
        const section = sql.slice(sql.indexOf(`CREATE TABLE IF NOT EXISTS public.${t} (`))
        const end = section.indexOf('\n);')
        expect(section.slice(0, end), `${t} generation CHECK`).toContain('ka_gochara_generation_governed(generation) IS TRUE')
      }
    }
    // no trigger of ours on a non-ka_gochara table
    const referenced = new Set<string>()
    for (const n of ALL) {
      const sql = readMigration(n)
      const created = [...sql.matchAll(/CREATE (?:CONSTRAINT )?TRIGGER \w+\n\s+(?:BEFORE|AFTER) [^\n]+ ON public\.(\w+)/g)].map(m => m[1]!)
      for (const t of created) expect(t, `trigger target ${t} in ${n}`).toMatch(/^ka_gochara_/)
      for (const m of sql.matchAll(/REFERENCES public\.(\w+)/g)) if (!m[1]!.startsWith('ka_gochara_')) referenced.add(m[1]!)
    }
    // the FK surface on existing tables is exactly the disclosed one (P2)
    expect([...referenced].sort()).toEqual(['charts', 'kala_gochara_convention', 'kala_gochara_coverage'])
    // the seal reads the manifest, it never binds to it
    expect(sub).toContain("p.status = 'published'")
    expect(sub).toContain('manifest_id UUID NOT NULL,')
  })

  // ── Ruling A (N12): the family keys, never the orchestrator's ────────────
  it('ruling A (N12): the lock helpers use the Gochara-5 FAMILY keys, transaction-scoped, never the orchestrator\'s session keys', () => {
    const sub = readMigration(1153)
    const locks = fs.readFileSync(LOCKS_PY, 'utf8')
    const runner = fs.readFileSync(RUNNER_PY, 'utf8')
    // the orchestrator's keys, as shipped (what we must NOT take)
    expect(locks).toContain('_GLOBAL_ASSETS_LOCK_KEY = "nirmana-global-assets"')
    expect(locks).toContain('pg_try_advisory_lock(hashtext(%s))')
    expect(runner).toContain('acquire_chart_lock(')
    // the family keys
    expect(sub).toContain("PERFORM pg_advisory_xact_lock(hashtext('gochara5:chart:' || p_chart_id::text)::bigint);")
    expect(sub).toContain("PERFORM pg_advisory_xact_lock(hashtext('gochara5:global')::bigint);")
    expect(sub).toContain("PERFORM pg_advisory_xact_lock_shared(hashtext('gochara5:global')::bigint);")
    expect(sub).toContain('CREATE OR REPLACE FUNCTION public.ka_gochara_lock_global_shared()')
    for (const n of ALL) {
      const sql = readMigration(n)
      const code = functionBodies(sql).map(f => f.body).join('\n')   // executable bodies, not header prose
      expect(code, `${n} must not take the orchestrator's global key`).not.toContain('nirmana-global-assets')
      expect(code, `${n} must not take the orchestrator's chart key`).not.toMatch(/hashtext\(\s*p_chart_id::text\s*\)/)
      expect(code, `${n} must not take a SESSION advisory lock`).not.toMatch(/pg_advisory_lock\(/)
      expect(code, `${n} must not take a SESSION advisory lock`).not.toMatch(/pg_try_advisory_lock\(/)
      expect(code, `${n} must not take a SESSION advisory lock`).not.toMatch(/pg_advisory_lock_shared\(/)
    }
    expect((sub.match(/current_setting\('transaction_isolation'\) <> 'read committed'/g) ?? []).length).toBe(3)
  })

  // ── Ruling B (N13): the fixed order is ENFORCED, and precedes tuple locks ─
  it('ruling B (N13): transaction-local markers enforce chart-EXCLUSIVE → global-SHARED and refuse the two illegal mixes', () => {
    const sub = readMigration(1153)
    const bodies = new Map(functionBodies(sub).map(f => [f.name, f.body]))
    const chart = bodies.get('ka_gochara_lock_chart')!
    const global = bodies.get('ka_gochara_lock_global')!
    const shared = bodies.get('ka_gochara_lock_global_shared')!
    // chart refuses inside a global-EXCLUSIVE holder; global-EXCLUSIVE refuses inside a chart or global-SHARED holder
    expect(chart).toContain("current_setting('gochara5.global_exclusive', true), '') = 'on'")
    expect(chart).toContain('lock-order violation')
    expect(chart).toContain("set_config('gochara5.chart_locked', 'on', true)")
    expect(global).toContain("current_setting('gochara5.chart_locked', true), '') = 'on'")
    expect(global).toContain("current_setting('gochara5.global_shared', true), '') = 'on'")
    expect(global).toContain('lock-order violation')
    expect(global).toContain("set_config('gochara5.global_exclusive', 'on', true)")
    expect(shared).toContain("set_config('gochara5.global_shared', 'on', true)")
    expect(shared).not.toContain('lock-order violation')   // chart → shared is the one legal mix
    // the check precedes the lock call in both refusing helpers
    expect(chart.indexOf('lock-order violation')).toBeLessThan(chart.indexOf('pg_advisory_xact_lock('))
    expect(global.indexOf('lock-order violation')).toBeLessThan(global.indexOf('pg_advisory_xact_lock('))
    // N18: ONE chart per transaction — bound at the lock boundary; a different chart and a non-canonical chart are
    // refused BEFORE any key is requested; the binding marker is written only here
    expect(chart).toContain("current_setting('gochara5.bound_chart', true), '') NOT IN ('', p_chart_id::text)")
    expect(chart).toContain('a transaction serves ONE chart')
    expect(chart).toContain("IF p_chart_id <> '482012f1-710e-4a25-994a-93821f5871aa'::uuid THEN")
    expect(chart).toContain('is not governed by the Gochara-5 contract (D-SCOPE')
    expect(chart.indexOf('a transaction serves ONE chart')).toBeLessThan(chart.indexOf('pg_advisory_xact_lock('))
    expect(chart.indexOf('is not governed by the Gochara-5 contract')).toBeLessThan(chart.indexOf('pg_advisory_xact_lock('))
    expect(chart).toContain("set_config('gochara5.bound_chart', p_chart_id::text, true)")
    for (const n of ALL) {
      const others = functionBodies(readMigration(n)).filter(f => f.name !== 'ka_gochara_lock_chart').map(f => f.body).join('\n')
      expect(others, `${n}: only ka_gochara_lock_chart may write the binding`).not.toContain("set_config('gochara5.bound_chart'")
    }
    const substrate = functionBodies(sub).find(f => f.name === 'ka_gochara_substrate_chart_lock')!.body
    expect(substrate).toContain("bound := current_setting('gochara5.bound_chart', true);")
    expect(substrate).toContain('but declares context')
  })

  it('ruling B (N13): every mutating trigger function is classified — chart-first, global-EXCLUSIVE-only, global-SHARED-after-chart, no-lock constraint-guarded, or locked by a predecessor', () => {
    const chartFirst = new Set(['ka_gochara_contact_guard', 'ka_gochara_chart_write_guard', 'ka_gochara_generation_seal_guard',
      'ka_gochara_seal_generation', 'ka_gochara_generation_is_sealed', 'ka_gochara_chart_statement_lock', 'ka_gochara_substrate_chart_lock'])
    const globalExclusive = new Set(['ka_gochara_global_write_guard', 'ka_gochara_membership_guard'])
    const globalShared = new Set(['ka_gochara_require_sealed_rule_path'])
    // constraint-guarded tables: insert-only / supersession checks need NO family key
    const noLock = new Set(['ka_gochara_insert_only', 'ka_gochara_sky_event_supersede_guard', 'ka_gochara_sky_event_guard',
      'ka_gochara_contact_identity_supersede_guard', 'ka_gochara_refuse_truncate'])
    // functions that run strictly AFTER a locking trigger in the same statement/transaction
    const lockedByPredecessor = new Set(['ka_gochara_record_coverage_guard', 'ka_gochara_window_coverage_guard',
      'ka_gochara_window_membership_guard', 'ka_gochara_record_finalize_check', 'ka_gochara_contact_propagate_precision'])
    let seen = 0
    for (const n of ALL) {
      for (const { name, body } of functionBodies(readMigration(n))) {
        const isTriggerish = name.includes('guard') || name.includes('seal') || name.includes('check') || name.includes('lock') || name.includes('propagate') || name.includes('truncate') || name.includes('insert_only')
        if (!isTriggerish || /^ka_gochara_lock_(chart|global|global_shared)$/.test(name)) continue
        const classified = chartFirst.has(name) || globalExclusive.has(name) || globalShared.has(name) || noLock.has(name) || lockedByPredecessor.has(name)
        expect(classified, `${name} is a mutating trigger function without a lock classification`).toBe(true)
        seen++
        if (noLock.has(name) || lockedByPredecessor.has(name)) {
          expect(body, `${name} must not take a family key itself`).not.toMatch(/ka_gochara_lock_(chart|global|global_shared)\(/)
          continue
        }
        if (chartFirst.has(name)) {
          const lockIdx = body.search(/PERFORM public\.ka_gochara_lock_chart\(/)
          expect(lockIdx, `${name} must take the chart family key`).toBeGreaterThan(-1)
          // the statement lock's only read IS the key selection (distinct chart_ids); every other
          // chart-first function locks before it reads or writes any content
          const firstRead = (name === 'ka_gochara_chart_statement_lock' || name === 'ka_gochara_substrate_chart_lock') ? -1 : body.search(/FROM public\.|INSERT INTO public\.|UPDATE public\./)
          expect(firstRead === -1 || lockIdx < firstRead, `${name} must lock before it reads or writes`).toBe(true)
          expect(body, `${name} must never take the global key EXCLUSIVE`).not.toContain('ka_gochara_lock_global()')
        }
        if (globalExclusive.has(name)) {
          const lockIdx = body.indexOf('PERFORM public.ka_gochara_lock_global();')
          expect(lockIdx, `${name} must take the global family key EXCLUSIVE`).toBeGreaterThan(-1)
          expect(body, `${name} must never take a chart key`).not.toContain('ka_gochara_lock_chart(')
          const firstRead = body.search(/FROM public\.|INSERT INTO public\.|UPDATE public\./)
          expect(firstRead === -1 || lockIdx < firstRead, `${name} must lock before it reads`).toBe(true)
        }
        if (globalShared.has(name)) {
          expect(body).toContain('PERFORM public.ka_gochara_lock_global_shared();')
          expect(body).not.toContain('ka_gochara_lock_global();')
          expect(body).not.toContain('ka_gochara_lock_chart(')
        }
      }
    }
    expect(seen).toBe(chartFirst.size + globalExclusive.size + globalShared.size + noLock.size + lockedByPredecessor.size)
  })

  it('ruling B (N13): refusals RAISE before any FAMILY advisory lock (the accurate claim — a tuple may still have been waited for)', () => {
    const sub = readMigration(1153)
    for (const n of ALL) expect(readMigration(n)).not.toMatch(/refused statement never waits/)
    expect(sub).toContain('RAISE before acquiring any FAMILY advisory lock')
    const bodies = new Map(functionBodies(sub).map(f => [f.name, f.body]))
    const gw = bodies.get('ka_gochara_global_write_guard')!
    expect(gw.indexOf("IF TG_OP <> 'INSERT' THEN")).toBeLessThan(gw.indexOf('ka_gochara_lock_global()'))
    const seal = bodies.get('ka_gochara_generation_seal_guard')!
    expect(seal.indexOf("IF TG_OP <> 'INSERT' THEN")).toBeLessThan(seal.indexOf('ka_gochara_lock_chart('))
    expect(seal.indexOf('not governed by the A5.1 contract')).toBeLessThan(seal.indexOf('ka_gochara_lock_chart('))
    const sealFn = bodies.get('ka_gochara_seal_generation')!
    expect(sealFn.indexOf('not governed by the A5.1 contract')).toBeLessThan(sealFn.indexOf('ka_gochara_lock_chart('))
    expect(bodies.get('ka_gochara_insert_only')!).not.toMatch(/ka_gochara_lock_/)
  })

  it('ruling B (N13): the family key precedes the tuple lock — BEFORE UPDATE OR DELETE … FOR EACH STATEMENT on every mutable chart-scoped table', () => {
    const all = ALL.map(readMigration).join('\n')
    for (const t of CHART_SCOPED_MUTABLE) {
      const re = new RegExp(`CREATE TRIGGER ka_gochara_\\w+_0_statement_lock\\n\\s+BEFORE UPDATE OR DELETE ON public\\.${t}\\n\\s+FOR EACH STATEMENT EXECUTE FUNCTION public\\.ka_gochara_chart_statement_lock\\(\\);`)
      expect(all, `${t} needs a statement-level family lock`).toMatch(re)
    }
    const stmt = functionBodies(readMigration(1153)).find(f => f.name === 'ka_gochara_chart_statement_lock')!.body
    expect(stmt).toContain('PERFORM public.ka_gochara_lock_chart(c);')
    expect(stmt).toContain('ORDER BY chart_id')   // ascending, deterministic
    // tables without a family key of their own: insert-only row guards (constraint-guarded) AND, since v1_4,
    // a statement-level chart-context lock on every write that can take a unique/tuple lock (substrate order)
    for (const t of ['ka_gochara_sky_convention', 'ka_gochara_physical_object', 'ka_gochara_contact_identity', 'ka_gochara_convention_bridge']) {
      expect(readMigration(1153)).toMatch(new RegExp(`BEFORE UPDATE OR DELETE ON public\\.${t}\\n\\s+FOR EACH ROW EXECUTE FUNCTION public\\.ka_gochara_insert_only\\(`))
      expect(readMigration(1153)).toMatch(new RegExp(`CREATE TRIGGER \\w+_0_chart_context\\n\\s+BEFORE INSERT ON public\\.${t}\\n\\s+FOR EACH STATEMENT EXECUTE FUNCTION public\\.ka_gochara_substrate_chart_lock\\(\\);`))
    }
    // the sky event permits enrichment UPDATEs, so its context lock covers UPDATE too (the reviewer's tuple schedule)
    expect(readMigration(1153)).toMatch(/CREATE TRIGGER ka_gochara_sky_event_0_chart_context\n\s+BEFORE INSERT OR UPDATE ON public\.ka_gochara_sky_event\n\s+FOR EACH STATEMENT EXECUTE FUNCTION public\.ka_gochara_substrate_chart_lock\(\);/)
    expect(readMigration(1157)).toMatch(/BEFORE UPDATE OR DELETE ON public\.ka_gochara_av_polarity_declaration\n\s+FOR EACH ROW EXECUTE FUNCTION public\.ka_gochara_insert_only\(/)
    expect(readMigration(1157)).toMatch(/CREATE TRIGGER ka_gochara_av_polarity_0_chart_context\n\s+BEFORE INSERT ON public\.ka_gochara_av_polarity_declaration\n\s+FOR EACH STATEMENT EXECUTE FUNCTION public\.ka_gochara_substrate_chart_lock\(\);/)
    const substrate = functionBodies(readMigration(1153)).find(f => f.name === 'ka_gochara_substrate_chart_lock')!.body
    expect(substrate).toContain("current_setting('gochara5.chart_locked', true), '') = 'on'")
    expect(substrate).toContain("ctx := current_setting('gochara5.chart', true);")
    expect(substrate).toContain('no chart context')
    expect(substrate.indexOf('no chart context')).toBeLessThan(substrate.indexOf('PERFORM public.ka_gochara_lock_chart(ctx::uuid);'))
    const lockChart = functionBodies(readMigration(1153)).find(f => f.name === 'ka_gochara_lock_chart')!.body
    expect(lockChart).toContain("set_config('gochara5.chart', p_chart_id::text, true)")
    // registry tables: global EXCLUSIVE, never a chart key
    const reg = readMigration(1154)
    for (const t of ['ka_gochara_predicate', 'ka_gochara_factor', 'ka_gochara_rule_path', 'ka_gochara_rule_path_prerequisite', 'ka_gochara_rule_path_soft_factor', 'ka_gochara_rule_path_seal']) {
      expect(reg).toMatch(new RegExp(`ON public\\.${t}\\n\\s+FOR EACH ROW EXECUTE FUNCTION public\\.ka_gochara_global_write_guard\\(`))
    }
    const regCode = functionBodies(reg).map(f => f.body).join('\n') + '\n' + withoutDollarBodies(reg).replace(/^--.*$/gm, '')
    expect(regCode).not.toContain('ka_gochara_lock_chart(')
    expect(regCode).not.toContain('ka_gochara_chart_statement_lock')
    // row-trigger firing order on the chart-scoped tables is by name: lock/seal guard, then coverage, then rule seal (SHARED)
    for (const [n, prefix] of [[1155, 'rr'], [1156, 'ew']] as const) {
      const sql = readMigration(n)
      expect(sql).toContain(`CREATE TRIGGER ka_gochara_${prefix}_0_statement_lock`)
      expect(sql).toContain(`CREATE TRIGGER ka_gochara_${prefix}_1_write_guard`)
      expect(sql).toContain(`CREATE TRIGGER ka_gochara_${prefix}_2_coverage_guard`)
      expect(sql).toContain(`CREATE TRIGGER ka_gochara_${prefix}_3_sealed_path_check`)
    }
  })

  // ── Ruling 4: the deploy route ───────────────────────────────────────────
  it('ruling 4 (N3): the routine runner refuses 1153–1157; the --only window may apply them', () => {
    // B6.0 PART 1: the protected set grew by the v1.5 contract amendments
    // 1204/1205 (AM-7/AM-8); 1153-1157 remain protected exactly as frozen.
    const V15_AMENDMENTS = ['1204_gochara_av_qualifier_object_role.sql', '1205_gochara_inherited_frame_kind.sql']
    expect([...PROTECTED_PUBLIC_SCHEMA_MIGRATIONS].sort()).toEqual([...Object.values(MIGRATIONS), ...V15_AMENDMENTS].sort())
    for (const f of Object.values(MIGRATIONS)) {
      expect(() => assertGeneralRunnerMayApplyPublicSchema(f, false)).toThrow(/gochara_contracts_schema_migration=true/)
      expect(() => assertGeneralRunnerMayApplyPublicSchema(f, true)).not.toThrow()
    }
    const deploy = fs.readFileSync(path.resolve(process.cwd(), '../.github/workflows/deploy.yml'), 'utf8')
    expect(deploy).toContain('gochara_contracts_schema_migration:')
    expect(deploy).toContain('APPLY_GOCHARA_CONTRACTS_SCHEMA_MIGRATION: ${{ inputs.gochara_contracts_schema_migration }}')
    let prev = deploy.indexOf('1125_ai_snapshot_shape_operator_precedence.sql)')
    for (const f of Object.values(MIGRATIONS)) {
      const at = deploy.indexOf(`migrations+=(${f})`)
      expect(at, f).toBeGreaterThan(prev)
      prev = at
    }
  })

  // ── Ruling D: N14 / N10 / N7+N15 / P2 ────────────────────────────────────
  it('N14/N17: coverage facts are an unambiguous JSON snapshot over the ACCEPTED domain — finite horizons only, everything else refused', () => {
    const sub = readMigration(1153)
    const rec = readMigration(1155)
    const win = readMigration(1156)
    expect(sub).toContain('CREATE OR REPLACE FUNCTION public.ka_gochara_horizon_finite_ok(h tstzrange)')
    // N19: the accepted era — every bound within 1000-01-01 ≤ t < 3000-01-01 UTC (AD); infinity is excluded by the same bounds
    expect(sub).toContain("AND lower(h) >= '1000-01-01 00:00:00+00'::timestamptz")
    expect(sub).toContain("AND upper(h) <  '3000-01-01 00:00:00+00'::timestamptz")
    expect(sub).toContain('AND NOT lower_inf(h) AND NOT upper_inf(h)')
    expect(sub).toContain("ka_gochara_horizon_finite_ok(tstzrange('infinity', 'infinity', '[]')) IS FALSE")
    expect(sub).toContain("ka_gochara_horizon_finite_ok(tstzrange('-infinity', 'infinity', '[]')) IS FALSE")
    expect(sub).toContain("ka_gochara_horizon_finite_ok(tstzrange('2025-03-01 00:00:00+00 BC', '2025-04-01 00:00:00+00 BC', '[)')) IS FALSE")
    expect(sub).toContain("ka_gochara_horizon_finite_ok(tstzrange('1000-01-01 00:00:00+00', '2999-12-31 23:59:59.999999+00', '[]')) IS TRUE")
    expect(sub).toContain('AD only')
    expect(rec).toContain('CREATE OR REPLACE FUNCTION public.ka_gochara_coverage_facts(p_convention_id text, p_completed_horizon tstzrange, p_relations_searched text[])')
    expect(rec).toContain('CREATE OR REPLACE FUNCTION public.ka_gochara_facts_horizon(f jsonb)')
    // the encoder REFUSES anything outside the accepted domain — it never meets infinity
    expect(rec).toContain('IF public.ka_gochara_horizon_finite_ok(p_completed_horizon) IS NOT TRUE THEN')
    expect(rec).toContain("RAISE EXCEPTION 'ka_gochara_coverage_facts: unsupported horizon % (N17/N19)")
    expect(rec).toContain("tstzrange('2025-03-01 00:00:00+00 BC', '2025-04-01 00:00:00+00 BC', '[)'),   -- N19: the reviewer's H_BC")
    expect(rec).toContain('IF n_raised <> 10 THEN')
    expect(rec).toContain("= '1000-01-01T00:00:00.000000Z'")
    expect(rec).toContain("= '2999-12-31T23:59:59.999999Z'")
    expect(rec).not.toContain("'lower_inf'")
    expect(rec).not.toContain("'empty', true")
    expect(rec).toContain('jsonb_agg(to_jsonb(x) ORDER BY x NULLS FIRST)')
    // the reviewer's collisions are asserted by the migration's own self-test: arrays distinguished, 7 non-finite horizons refused
    expect(rec).toContain("ARRAY['conjunction', NULL]")
    expect(rec).toContain("ARRAY['aspect,conjunction']")
    expect(rec).toContain("tstzrange('-infinity', 'infinity', '[]'),\n                             tstzrange('infinity', 'infinity', '[]'),")
    // consumer boundaries: partition horizon refused by both guards, window interval and support intervals CHECKed
    expect(rec).toContain("coverage not applicable (N17/N19): partition (%, %) completed_horizon % is not a finite, bounded, non-empty range within 1000-01-01 <= t < 3000-01-01 UTC (AD)")
    expect(win).toContain("coverage not applicable (N17/N19): partition (%, %) completed_horizon % is not a finite, bounded, non-empty range within 1000-01-01 <= t < 3000-01-01 UTC (AD)")
    expect(win).toContain('CONSTRAINT kgew_interval_finite_ck')
    expect(win).toContain('CHECK (public.ka_gochara_horizon_finite_ok(interval) IS TRUE)')
    expect(rec).toContain('WHERE public.ka_gochara_horizon_finite_ok(r) IS NOT TRUE')   // ka_gochara_intervals_ok
    // the drift classifier never asks the encoder to encode a non-finite partition: it is incompatible outright
    expect(win).toContain("WHEN public.ka_gochara_horizon_finite_ok(cov.completed_horizon) IS NOT TRUE THEN 'incompatible'")
    expect(win).toContain('OR public.ka_gochara_horizon_finite_ok(cov.completed_horizon) IS NOT TRUE THEN NULL::jsonb')
    for (const n of ALL) {
      const sql = readMigration(n)
      expect(sql, `${n} must not carry a coverage digest`).not.toContain('coverage_digest')
      expect(sql, `${n} must not hash coverage facts`).not.toMatch(/\bmd5\(/)
    }
    expect(rec).toContain('coverage_facts    JSONB NOT NULL')
    expect(rec).toContain('kgrr_coverage_facts_shape_ck')
    expect(readMigration(1156)).toContain('coverage_facts    JSONB NOT NULL')
    expect(readMigration(1156)).toContain('kgew_coverage_facts_shape_ck')
    expect(rec).toContain('IF NEW.coverage_facts IS DISTINCT FROM facts THEN')
  })

  it('N10: the consumer contract — drift classifier over records AND windows, seal refusal, window-contributor applicability', () => {
    const win = readMigration(1156)
    expect(win).toContain('CREATE OR REPLACE FUNCTION public.ka_gochara_coverage_drift(p_chart_id uuid, p_generation text)')
    for (const cls of ['partition_missing', 'identical', 'extended', 'incompatible']) expect(win).toContain(`'${cls}'`)
    expect(win).toContain("SELECT 'relationship_record'::text AS consumer")
    expect(win).toContain("SELECT 'eval_window'::text, w.window_id")
    expect(win).toContain('cov.completed_horizon @> public.ka_gochara_facts_horizon(c.coverage_facts)')
    const sub = readMigration(1153)
    expect(sub).toContain("to_regprocedure('public.ka_gochara_coverage_drift(uuid,text)') IS NOT NULL")
    expect(sub).toContain("d.drift IN (''incompatible'', ''partition_missing'')")
    expect(sub).toContain('ka_gochara_generation_seal refused (N10 consumer contract)')
    // window contributors are checked against the WINDOW's coverage by ONE predicate, at INSERT and — N16 — over
    // EVERY membership at the seal boundary
    expect(win).toContain('CREATE OR REPLACE FUNCTION public.ka_gochara_membership_violation(')
    expect(win).toContain("(r_facts ->> 'convention_id') IS DISTINCT FROM (w_facts ->> 'convention_id')")
    expect(win).toContain("(w_facts -> 'relations_searched') @> to_jsonb(ARRAY[r_relation])")
    expect(win).toContain('wh := public.ka_gochara_facts_horizon(w_facts);')
    expect(win).toContain('CREATE OR REPLACE FUNCTION public.ka_gochara_window_membership_guard()')
    expect(win).toContain('why := public.ka_gochara_membership_violation(w.coverage_facts, r.contact_id, r.relation, r.coverage_facts, r.temporal_support_intervals);')
    expect(win).toContain('CREATE TRIGGER ka_gochara_ewr_2_membership_guard')
    expect(win).toContain('CREATE OR REPLACE FUNCTION public.ka_gochara_membership_violations(p_chart_id uuid, p_generation text)')
    expect(win).toContain('FROM public.ka_gochara_eval_window_record m')
    expect(sub).toContain("to_regprocedure('public.ka_gochara_membership_violations(uuid,text)') IS NOT NULL")
    expect(sub).toContain('ka_gochara_generation_seal refused (N16 membership invariant)')
    // both seal-time checks run inside the seal guard, under the chart family key, before the seal row is written
    const sealGuard = functionBodies(sub).find(f => f.name === 'ka_gochara_generation_seal_guard')!.body
    expect(sealGuard.indexOf('PERFORM public.ka_gochara_lock_chart(NEW.chart_id);')).toBeLessThan(sealGuard.indexOf('ka_gochara_coverage_drift($1, $2)'))
    expect(sealGuard.indexOf('ka_gochara_coverage_drift($1, $2)')).toBeLessThan(sealGuard.indexOf('ka_gochara_membership_violations($1, $2)'))
    // kept N10 rules
    const rec = readMigration(1155)
    expect(rec).toContain('IF NOT COALESCE(NEW.relation = ANY (cov.relations_searched), false) THEN')
    expect(rec).toContain('array_position(cov.relations_searched, NULL) IS NOT NULL')
    expect(rec).toContain("AND cov.partition_key <> NEW.agent || ':' || NEW.object_role THEN")
    expect(win).toContain("CHECK (coverage_partition_kind = 'event_class')")
    expect(win).toContain('array_position(cov.relations_searched, NULL) IS NOT NULL')
  })

  it('N7/N15: a precision-only re-sync verifies the restatement only — it never re-validates coverage', () => {
    const rec = readMigration(1155)
    const guard = functionBodies(rec).find(f => f.name === 'ka_gochara_record_coverage_guard')!.body
    expect(guard).toContain("precision_only := (to_jsonb(NEW) - 'precision') = (to_jsonb(OLD) - 'precision');")
    expect(guard).toContain('IF NOT precision_only THEN')
    // the partition lookup and the facts comparison are inside the non-precision-only branch
    const branch = guard.indexOf('IF NOT precision_only THEN')
    expect(guard.indexOf('FROM public.kala_gochara_coverage c')).toBeGreaterThan(branch)
    expect(guard.indexOf('IF NEW.coverage_facts IS DISTINCT FROM facts THEN')).toBeGreaterThan(branch)
    // the restatement check runs on every path
    expect(guard).toContain("restates the contact''s solved precision")
    expect(rec).toContain('CREATE OR REPLACE FUNCTION public.ka_gochara_contact_propagate_precision()')
    expect(rec).toContain('CREATE TRIGGER ka_gochara_contact_2_propagate_precision')
    expect(rec).toContain("ka_gochara_chart_write_guard('precision_sync')")
  })

  it('P2: operational assertions are honest — FK/RI effects, refusal timing, per-file atomicity, recovery are documented; no overclaims', () => {
    const sub = readMigration(1153)
    expect(sub).toContain('Operational assertions (P2')
    expect(sub).toContain('EXISTING-TABLE EFFECTS')
    expect(sub).toContain('internal RI triggers on the referenced table')
    expect(sub).toContain('SHARE ROW')
    expect(sub).toContain('ROUTINE REFUSAL is loud but not write-free')
    expect(sub).toContain('PER-FILE ATOMIC, NOT FAMILY-ATOMIC')
    expect(sub).toContain('re-dispatch the window')
    for (const n of ALL) {
      const sql = readMigration(n)
      expect(sql).not.toMatch(/touches nothing/i)
      expect(sql).not.toMatch(/no effect on any existing table/i)
      expect(sql).not.toMatch(/(?<!NOT )family[- ]atomic/i)
    }
  })

  // ── Ruling 5 (kept): N6/N8 by name ────────────────────────────────────────
  it('ruling 5 (N6/N8): the named mechanisms exist', () => {
    const sub = readMigration(1153)
    expect(sub).toContain('N6 (INSERT and enrichment UPDATE): one identity, one solved reading')
    expect(sub).toContain('already carries a different solved reading in another generation')
    const rec = readMigration(1155)
    expect(rec).toContain("ka_gochara_chart_write_guard('result_only')")
    expect(rec).toContain('membership reparenting (record_id/ordinal/predicate) is prohibited')
    expect(readMigration(1156)).toContain("ka_gochara_chart_write_guard('no_update')")
  })

  // ── Kept from rounds 2–3 (by name) ───────────────────────────────────────
  it('F1/F4 (kept): identity separate from the ledger; the frozen hash recipe; truncated ⇔ clipped_truncated', () => {
    const sql = readMigration(1153)
    expect(sql).toContain('CREATE TABLE IF NOT EXISTS public.ka_gochara_contact_identity')
    expect(sql).toContain('PRIMARY KEY (chart_id, generation, contact_id)')
    expect(sql).toContain('UNIQUE (physical_object_id, occurrence_ordinal)')
    expect(sql).not.toMatch(/correction_seq\s+INTEGER/)
    expect(sql).toContain('ka_gochara_contact_identity_fk')
    expect(sql).toContain('kgci_supersedes_uq UNIQUE (supersedes_contact_id)')
    expect(sql).toContain('kgse_truncated_method_ck')
    expect(sql).toContain('kgc_truncated_method_ck')
    expect(sql).toContain('kala_gochara_contacts')
    expect(sql).toMatch(/NOT\s+migrated/i)
  })

  it('F1/F7 (kept): ownership-bound, relation-exact references; class/path-bound window membership', () => {
    const rec = readMigration(1155)
    expect(rec).toContain('FOREIGN KEY (chart_id, generation, contact_id, agent, relation, object_id)')
    expect(rec).toContain('REFERENCES public.ka_gochara_contact (chart_id, generation, contact_id, body, relation_kind, physical_object_id)')
    expect(readMigration(1153)).toContain('REFERENCES public.ka_gochara_physical_object (physical_object_id, body, relation_kind, convention_id)')
    const win = readMigration(1156)
    expect(win).toContain('REFERENCES public.ka_gochara_eval_window (window_id, chart_id, generation, event_class, path_id, rule_version)')
    expect(win).toContain('REFERENCES public.ka_gochara_relationship_record (record_id, chart_id, generation, event_class, path_id, rule_version)')
    for (const n of [1155, 1156] as const) {
      expect(readMigration(n)).toContain('REFERENCES public.kala_gochara_coverage (chart_id, generation, partition_kind, partition_key)')
    }
  })

  it('F2 (kept): TRUNCATE refused on every owned table; the seal is permanent', () => {
    for (const n of ALL) {
      const sql = readMigration(n)
      for (const t of createdTables(sql)) {
        expect(sql, `${t} TRUNCATE guard`).toMatch(new RegExp(`BEFORE TRUNCATE ON public\\.${t}\\n`))
      }
    }
    expect(readMigration(1153)).toContain("ka_gochara_generation_seal is permanent")
  })

  it('F3 (kept): rule-version seal; only sealed versions are referenced', () => {
    const reg = readMigration(1154)
    expect(reg).toContain('CREATE TABLE IF NOT EXISTS public.ka_gochara_rule_path_seal')
    expect(reg).toContain('ka_gochara_membership_guard')
    expect(readMigration(1155)).toContain('BEFORE INSERT OR UPDATE OF path_id, rule_version ON public.ka_gochara_relationship_record')
    expect(readMigration(1156)).toContain('BEFORE INSERT OR UPDATE OF path_id, rule_version ON public.ka_gochara_eval_window')
  })

  it('F5 (kept): total validators, IS TRUE on every helper CHECK, commit-time finalisation', () => {
    expect(readMigration(1154)).toContain('SELECT COALESCE(CASE frame_kind')
    const rec = readMigration(1155)
    expect(rec).toContain("jsonb_typeof(p -> 'solver_method') = 'string'")
    expect(rec).toContain('CREATE CONSTRAINT TRIGGER ka_gochara_rr_finalize')
    expect(rec).toContain('CREATE CONSTRAINT TRIGGER ka_gochara_rpr_finalize')
    for (const n of ALL) {
      const sql = readMigration(n)
      const calls = sql.match(/CHECK \([^;]*?public\.ka_gochara_\w+_ok\([^;]*?\)\)/gs) ?? []
      for (const chk of calls) {
        const bare = chk.match(/public\.ka_gochara_\w+_ok\([^()]*(?:\([^()]*\)[^()]*)*\)(?! IS TRUE)/g) ?? []
        expect(bare, `helper call without IS TRUE in ${n}: ${chk.slice(0, 100)}`).toEqual([])
      }
    }
  })

  it('F6 (kept): factor discipline is exactly C2', () => {
    const reg = readMigration(1154)
    expect(reg).toContain("CHECK (calibration_status <> 'calibrated' OR category_mapping IS NOT NULL)")
    expect(reg).not.toContain('kgf_mapping_discipline_ck')
    expect(reg).toMatch(/score_rule\s+TEXT NOT NULL/)
  })

  it('F11 (kept): selector encoding, finite domains, non-empty AV categories, fact-id disposition', () => {
    expect(readMigration(1154)).toContain("'^[a-z][a-z0-9_]*([.:/][a-z0-9_]+)*$'")
    expect(readMigration(1153)).toContain('kgse_uncertainty_finite_ck')
    expect(readMigration(1155)).toContain('kgrr_evidence_finite_ck')
    expect(readMigration(1156)).toContain('kgew_evidence_finite_ck')
    expect(readMigration(1157)).toContain('ka_gochara_text_array_ok(applies_to_fact_categories, 1)')
    expect(readMigration(1155)).toMatch(/RESOLVABILITY[\s\S]*WRITER-BOUNDARY/)
  })

  it('event_class CHECKs enumerate exactly the 27 protocol classes', () => {
    for (const n of [1155, 1156] as const) {
      const sql = readMigration(n)
      for (const cls of EVENT_CLASS_LIST) expect(sql).toContain(`'${cls}'`)
    }
  })

  it('D-SCOPE disposition: canonical-chart CHECK on the per-chart data tables', () => {
    for (const sql of [readMigration(1153), readMigration(1155), readMigration(1156)]) {
      expect(sql).toContain('482012f1-710e-4a25-994a-93821f5871aa')
    }
  })
})

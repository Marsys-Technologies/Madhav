// @vitest-environment node
/**
 * Pravāha B (steward M20261001T224443-bfc4, 2026-10-02) — migration 1220 grants
 * data_plane_builder EXECUTE on the minimal set of 1153–1157 contract functions
 * its governed writes reach, plus SELECT on the generation-seal table.
 *
 * WHY THIS SUITE IS DEPLOYMENT-FAITHFUL (the lesson of the 1216 suite)
 * ─────────────────────────────────────────────────────────────────────
 * The 1216 suite passed while production was broken: it created every object as
 * the superuser, whose functions keep PUBLIC EXECUTE, so a function-execute gap
 * could not exist in its world. Production is different — the routine runner
 * connects as `amjis_app`, which OWNS every object, and the governed bootstrap
 * runs
 *   ALTER DEFAULT PRIVILEGES FOR ROLE amjis_app REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC
 * (platform/scripts/nirmana-evidence-ownership-preflight.ts:259), so nothing
 * amjis_app creates is callable by anyone else until granted. This suite builds
 * the same world: a role literally named `amjis_app` owns schema public and
 * creates every table and function by executing the REAL on-disk migration files
 * under `SET ROLE amjis_app`, with that default-privilege revocation in force;
 * the builder-mirror is a literally-named `data_plane_builder` holding only
 * USAGE on schema public before 1216. No hand-copied proxy of any migration.
 *
 * What it proves (§N.8 — each assertion measures the claim it names):
 *   0. CONTROL — the mirror is faithful: every ka_gochara_* function is owned by
 *      amjis_app and neither PUBLIC nor the builder can execute any of the 42.
 *   1. FAILS BEFORE — after 1216 and before 1220 the builder's first governed
 *      step (the chart lock) and its first substrate INSERT both die with
 *      'permission denied for function …'.
 *   2. SUCCEEDS AFTER — with the REAL 1220 file applied by amjis_app, the whole
 *      writer sequence (kala convention, sky convention, bridge, physical
 *      object, contact identity, publication + coverage, ledger contact,
 *      registry rows, relationship record + prerequisite) lands as the builder.
 *   3. EXACT SET — the builder holds EXECUTE on exactly the 18 granted
 *      functions and on none of the other 24 (seal_generation, the verifiers,
 *      the trigger functions), and its seal-table privilege is SELECT only.
 *   4. EACH GRANT IS NECESSARY — revoking any single one of the 18 makes a
 *      builder write fail with 'permission denied for function <that one>'.
 *   5. SEAL BOUNDARY — the builder cannot seal a generation and cannot write the
 *      seal table.
 *   6. IDEMPOTENT.
 *
 * Requires a THROWAWAY database: skipped unless
 * M1220_GOCHARA_FN_TEST_DATABASE_URL is set, and refuses anything not named
 * `m1220_gochara_fn_execute_test` — it drops and recreates schema public and
 * (re)creates the cluster roles amjis_app and data_plane_builder, and must never
 * touch production.
 *
 *   createdb -h 127.0.0.1 -p 55432 -U postgres m1220_gochara_fn_execute_test
 *   M1220_GOCHARA_FN_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/m1220_gochara_fn_execute_test \
 *     npx vitest run tests/integration/gochara_contract_builder_function_execute.db.test.ts
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool } from 'pg'
import fs from 'fs'
import path from 'path'

const TEST_DB_URL = process.env.M1220_GOCHARA_FN_TEST_DATABASE_URL

const MIG = (name: string) => path.resolve(__dirname, '../../migrations', name)
const read = (name: string) => fs.readFileSync(MIG(name), 'utf8')
const DDL_FILES = [
  '1081_nirmana_l3_gochara_ledger_coverage_publication.sql',
  '1153_gochara_sky_event_substrate.sql',
  '1154_gochara_rule_path_registry.sql',
  '1155_gochara_relationship_record.sql',
  '1156_gochara_eval_window.sql',
  '1157_gochara_av_polarity_declaration.sql',
]
const M1216 = '1216_gochara_contract_builder_grants.sql'
const M1220 = '1220_gochara_contract_builder_function_execute.sql'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const OWNER = 'amjis_app'
const BUILDER = 'data_plane_builder'

// The 18 functions migration 1220 grants (name → full signature).
const GRANTED: Record<string, string> = {
  ka_gochara_lock_chart: 'ka_gochara_lock_chart(uuid)',
  ka_gochara_lock_global: 'ka_gochara_lock_global()',
  ka_gochara_lock_global_shared: 'ka_gochara_lock_global_shared()',
  ka_gochara_generation_is_sealed: 'ka_gochara_generation_is_sealed(uuid, text)',
  ka_gochara_generation_governed: 'ka_gochara_generation_governed(text)',
  ka_gochara_coverage_facts: 'ka_gochara_coverage_facts(text, tstzrange, text[])',
  ka_gochara_horizon_finite_ok: 'ka_gochara_horizon_finite_ok(tstzrange)',
  ka_gochara_finite_nonneg_ok: 'ka_gochara_finite_nonneg_ok(double precision)',
  ka_gochara_finite_ok: 'ka_gochara_finite_ok(double precision)',
  ka_gochara_frame_ok: 'ka_gochara_frame_ok(text, text)',
  ka_gochara_intervals_ok: 'ka_gochara_intervals_ok(tstzrange[])',
  ka_gochara_precision_ok: 'ka_gochara_precision_ok(jsonb)',
  ka_gochara_string_array_ok: 'ka_gochara_string_array_ok(jsonb)',
  ka_gochara_vocab_array_ok: 'ka_gochara_vocab_array_ok(jsonb, text[])',
  ka_gochara_named_operands_ok: 'ka_gochara_named_operands_ok(jsonb)',
  ka_gochara_selector_token_ok: 'ka_gochara_selector_token_ok(text)',
  ka_gochara_object_selector_consistent_ok: 'ka_gochara_object_selector_consistent_ok(jsonb, jsonb, jsonb)',
  ka_gochara_object_selector_ok: 'ka_gochara_object_selector_ok(jsonb)',
}

let pool: Pool

/** Execute `sql` on one connection as the given role (SET ROLE; reset afterwards). */
async function asRole(role: string, sql: string, params: unknown[] = []) {
  const client = await pool.connect()
  try {
    await client.query(`SET ROLE ${role}`)
    return await client.query(sql, params)
  } finally {
    await client.query('RESET ROLE').catch(() => {})
    client.release()
  }
}

/** One transaction AS the builder-mirror. */
async function builderTx(statements: Array<[string, unknown[]?]>) {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query(`SET LOCAL ROLE ${BUILDER}`)
    for (const [sql, params] of statements) await client.query(sql, params ?? [])
    await client.query('COMMIT')
  } catch (error) {
    await client.query('ROLLBACK').catch(() => {})
    throw error
  } finally {
    client.release()
  }
}

/** Apply a REAL migration file the way the routine runner does: as amjis_app. */
async function applyAsOwner(file: string) {
  await asRole(OWNER, read(file))
}

const uuidN = (n: number, kind: number) =>
  `3${String(kind).padStart(7, '0')}-0000-4000-8000-${String(n).padStart(12, '0')}`
const HORIZON = `tstzrange('2025-01-01T00:00Z','2026-01-01T00:00Z','[)')`

/**
 * The builder's three write groups for variant n (every natural key carries n,
 * so a variant never collides with another). Chart-scoped and global-registry
 * mutations run in SEPARATE transactions — the enforced lock order (chart
 * EXCLUSIVE, then global SHARED) forbids mixing a registry mutation with a
 * chart write.
 */
function groups(n: number): Array<Array<[string, unknown[]?]>> {
  const gen = `5.${n}`
  const obj = uuidN(n, 1)
  const cid = uuidN(n, 2)
  const rec = uuidN(n, 3)
  const target = `point:${198 + n}.52`
  return [
    [
      [`SELECT public.ka_gochara_lock_chart($1::uuid)`, [CHART]],
      [`INSERT INTO public.kala_gochara_convention
          (convention_id, zodiac, ayanamsha, sidereal_method, node_model, node_source,
           epoch_convention, time_scale, house_system, ephemeris_mode, method_version)
        VALUES ('legacy-${n}','sidereal','lahiri_chitrapaksha','true_chitra','mean','swiss',
                'j2000','utc','whole_sign','swiss','1.0')`],
      [`INSERT INTO public.ka_gochara_sky_convention
          (convention_id, ephemeris_generation, ayanamsha, node_convention, grid,
           method_version, domain_start, domain_end)
        VALUES ('sky-${n}','de441','lahiri_chitrapaksha','mean','1s','m1',
                '2025-01-01T00:00Z','2026-01-01T00:00Z')`],
      [`INSERT INTO public.ka_gochara_convention_bridge (kala_convention_id, sky_convention_id)
        VALUES ('legacy-${n}','sky-${n}')`],
      [`INSERT INTO public.ka_gochara_physical_object
          (physical_object_id, body, relation_kind, canonical_target, convention_id)
        VALUES ($1,'mars','conjunction',$2,'sky-${n}')`, [obj, target]],
      [`INSERT INTO public.ka_gochara_contact_identity
          (contact_id, physical_object_id, occurrence_ordinal, supersedes_contact_id)
        VALUES ($1,$2,1,NULL)`, [cid, obj]],
      [`INSERT INTO public.kala_gochara_publication
          (chart_id, generation, writer_asset_id, convention_id, input_generation_vector,
           ephemeris_backend, horizon, row_counts, content_digest, status)
        VALUES ($1,$2,'ka_gochara','legacy-${n}','{}','{}',${HORIZON},'{}','digest','candidate')`, [CHART, gen]],
      [`INSERT INTO public.kala_gochara_coverage
          (chart_id, generation, partition_kind, partition_key, convention_id,
           requested_horizon, completed_horizon, resolution, relations_searched,
           targets_requested, targets_resolved, targets_unresolved,
           target_resolution_state_counts, build_id)
        VALUES ($1,$2,'body_target','mars:karaka','legacy-${n}',${HORIZON},${HORIZON},1.0,
                ARRAY['conjunction','aspect','residence']::text[],1,1,0,'{"resolved":1}','b')`, [CHART, gen]],
      [`INSERT INTO public.ka_gochara_contact
          (chart_id, generation, contact_id, physical_object_id, occurrence_ordinal,
           convention_id, body, relation_kind, t_in, t_out, t_exact, solver_method,
           delta_lambda, delta_t, precision_regime, coverage)
        VALUES ($1,$2,$3,$4,1,'sky-${n}','mars','conjunction','2025-03-09T00:00Z',
                '2025-03-11T00:00Z','2025-03-10T00:00Z','swiss_refined',0.001,60,'standard',
                '{"truncated":false}'::jsonb)`, [CHART, gen, cid, obj]],
    ],
    [
      [`SELECT public.ka_gochara_lock_global()`],
      [`INSERT INTO public.ka_gochara_predicate (predicate_id, rule_version, operator, operands)
        VALUES ('q${n}','v1','within_orb',
                '{"left":"chart_facts.graha_position:mars","right":"object.longitude","orb":3.0}')`],
      [`INSERT INTO public.ka_gochara_factor
          (factor_id, rule_version, operand_selector, direction, function, range_lower, range_upper,
           units, calibration_status, doctrine_ordering, category_mapping, null_state, effect)
        VALUES ('f${n}','v1','{"operand":"dignity.transit_sign"}','higher_stronger','step',0,1,
                'unitless','uncalibrated_default',
                '["exaltation","own","friendly","neutral","inimical","debility"]',NULL,'omit','declared effect text')`],
      [`INSERT INTO public.ka_gochara_rule_path
          (path_id, rule_version, frame_kind, frame_arg, agent_set, relation_set, object_selector,
           provenance, operator_role, ruling_ref, score_rule)
        VALUES ('P1','v${n}','dasha_lord',NULL,'["mars","moon"]','["conjunction","occupancy"]',
                '[{"agent":"mars","relation":"conjunction","object_role":"karaka"},
                  {"agent":"moon","relation":"conjunction","object_role":"karaka"},
                  {"agent":"mars","relation":"occupancy","object_role":"occupant"}]',
                'verse_cited','scored',NULL,'within_path_product')`],
      [`INSERT INTO public.ka_gochara_rule_path_prerequisite
          (path_id, rule_version, ordinal, predicate_id, predicate_rule_version)
        VALUES ('P1','v${n}',1,'q${n}','v1')`],
      [`INSERT INTO public.ka_gochara_rule_path_soft_factor
          (path_id, rule_version, factor_id, factor_rule_version)
        VALUES ('P1','v${n}','f${n}','v1')`],
      [`INSERT INTO public.ka_gochara_rule_path_seal (path_id, rule_version) VALUES ('P1','v${n}')`],
    ],
    [
      [`SELECT public.ka_gochara_lock_chart($1::uuid)`, [CHART]],
      [`INSERT INTO public.ka_gochara_relationship_record
          (record_id, chart_id, generation, contact_id, event_class, affected_person, frame_kind,
           frame_arg, agent, relation, object_id, object_kind, object_role, path_id, rule_version,
           temporal_support_state, temporal_support_grain, temporal_support_intervals,
           coverage_partition_kind, coverage_partition_key, coverage_facts, precision,
           source_text, source_page, source_fact_ids, fixture, provenance, operator_role,
           ruling_ref, admission_state, house_from_frame, evidence_for_occurrence,
           evidence_against_occurrence, outcome_valence_for_native, severity)
        SELECT $1, $2, $3, $4, 'marriage','native','lagna',NULL,'mars','conjunction',$5,
               'degree_point','karaka','P1','v${n}','computed','day',
               ARRAY[tstzrange('2025-03-09T00:00Z','2025-03-11T00:00Z')]::tstzrange[],
               'body_target','mars:karaka',
               public.ka_gochara_coverage_facts(convention_id, completed_horizon, relations_searched),
               '{"solver_method":"swiss_refined","delta_lambda":0.001,"delta_t":60}'::jsonb,
               'Phaladīpikā','PG249-250 (XX.34-38)','["fact-1"]',false,'verse_cited','scored',
               NULL,'admitted',7,0.8,NULL,'favourable',NULL
        FROM public.kala_gochara_coverage
        WHERE chart_id = $2 AND generation = $3 AND partition_kind = 'body_target'
          AND partition_key = 'mars:karaka'`, [rec, CHART, gen, cid, obj]],
      [`INSERT INTO public.ka_gochara_record_prerequisite
          (record_id, chart_id, generation, ordinal, predicate_id, predicate_rule_version, result)
        VALUES ($1,$2,$3,1,'q${n}','v1','true')`, [rec, CHART, gen]],
    ],
  ]
}

/** Run the three groups; returns the first error (stops there), or null. */
async function runWriter(n: number): Promise<Error | null> {
  for (const g of groups(n)) {
    try {
      await builderTx(g)
    } catch (e) {
      return e as Error
    }
  }
  return null
}

describe.skipIf(!TEST_DB_URL)(
  'migration 1220 — gochara contract builder function EXECUTE (deployment-faithful role mirror) — live DB',
  () => {
    beforeAll(async () => {
      if (!/m1220_gochara_fn_execute_test/.test(TEST_DB_URL!)) {
        throw new Error(
          'M1220_GOCHARA_FN_TEST_DATABASE_URL must point at a disposable database named ' +
            '`m1220_gochara_fn_execute_test`. This suite drops and recreates schema public and the ' +
            'cluster roles amjis_app / data_plane_builder, and must never run against production.'
        )
      }
      pool = new Pool({ connectionString: TEST_DB_URL })
      await pool.query(`DROP SCHEMA IF EXISTS public CASCADE`)
      // Roles are cluster-global: another disposable database on the same cluster
      // may still depend on them, so clear only THIS database's dependencies and
      // create each role only if absent.
      await pool.query(`
        DO $d$ DECLARE r text; BEGIN
          FOREACH r IN ARRAY ARRAY['${BUILDER}','${OWNER}'] LOOP
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
              EXECUTE format('DROP OWNED BY %I CASCADE', r);
            ELSE
              EXECUTE format('CREATE ROLE %I NOLOGIN', r);
            END IF;
          END LOOP;
        END $d$`)
      await pool.query(`CREATE SCHEMA public AUTHORIZATION ${OWNER}`)
      await pool.query(`GRANT USAGE ON SCHEMA public TO ${BUILDER}`)
      // The governed bootstrap (nirmana-evidence-ownership-preflight.ts:259).
      await pool.query(
        `ALTER DEFAULT PRIVILEGES FOR ROLE ${OWNER} REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC`
      )
      // Stubs the contract migrations need, created BY the owner: the FK parent
      // and the runner's tracker table (referenced at parse time by the 1153–1157
      // preflight blocks).
      await asRole(OWNER, `CREATE TABLE public.charts (id UUID PRIMARY KEY)`)
      await asRole(OWNER, `CREATE TABLE public._migrations_applied (filename TEXT PRIMARY KEY)`)
      await pool.query(`INSERT INTO public.charts (id) VALUES ($1)`, [CHART])
      for (const file of DDL_FILES) {
        await applyAsOwner(file)
        await pool.query(`INSERT INTO public._migrations_applied (filename) VALUES ($1)`, [file])
      }
    })

    afterAll(async () => {
      if (!pool) return
      await pool.query(`DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;`)
      // Best effort: a role another database on the cluster still depends on stays.
      for (const role of [BUILDER, OWNER]) {
        await pool.query(`DROP OWNED BY ${role} CASCADE`).catch(() => {})
        await pool.query(`DROP ROLE IF EXISTS ${role}`).catch(() => {})
      }
      await pool.end()
    })

    it('CONTROL: the mirror is deployment-faithful — owner-created functions, PUBLIC execute revoked, builder holds none of the 42', async () => {
      const r = await pool.query<{ total: number; wrong_owner: number; public_exec: number; builder_exec: number }>(
        `SELECT count(*)::int AS total,
                count(*) FILTER (WHERE pg_get_userbyid(p.proowner) <> '${OWNER}')::int AS wrong_owner,
                count(*) FILTER (WHERE has_function_privilege('public', p.oid, 'EXECUTE'))::int AS public_exec,
                count(*) FILTER (WHERE has_function_privilege('${BUILDER}', p.oid, 'EXECUTE'))::int AS builder_exec
           FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
          WHERE n.nspname = 'public' AND p.proname LIKE 'ka\\_gochara\\_%'`
      )
      expect(r.rows[0]).toEqual({ total: 42, wrong_owner: 0, public_exec: 0, builder_exec: 0 })
    })

    it('FAILS BEFORE: with 1216 applied but not 1220 the builder is stopped at its first governed step by a FUNCTION permission', async () => {
      await applyAsOwner(M1216)
      await expect(builderTx([[`SELECT public.ka_gochara_lock_chart($1::uuid)`, [CHART]]])).rejects.toThrow(
        /permission denied for function ka_gochara_lock_chart/
      )
      // The table grants alone are real (1216 works): a plain kala-ledger insert needs no function.
      await builderTx([
        [`INSERT INTO public.kala_gochara_convention
            (convention_id, zodiac, ayanamsha, sidereal_method, node_model, node_source,
             epoch_convention, time_scale, house_system, ephemeris_mode, method_version)
          VALUES ('legacy-control','sidereal','lahiri_chitrapaksha','true_chitra','mean','swiss',
                  'j2000','utc','whole_sign','swiss','1.0')`],
      ])
      // And the whole writer sequence cannot even start: its first group dies on a FUNCTION permission.
      const err = await runWriter(1)
      expect(err).not.toBeNull()
      expect(String(err!.message)).toMatch(/permission denied for function ka_gochara_lock_chart/)
    })

    it('SUCCEEDS AFTER: the REAL 1220 file (applied by amjis_app) admits the whole governed write sequence', async () => {
      await applyAsOwner(M1220)
      const err = await runWriter(2)
      expect(err).toBeNull()
      const counts = await pool.query(
        `SELECT (SELECT count(*) FROM public.ka_gochara_contact WHERE generation = '5.2')::int AS contacts,
                (SELECT count(*) FROM public.ka_gochara_relationship_record WHERE generation = '5.2')::int AS records,
                (SELECT count(*) FROM public.ka_gochara_record_prerequisite WHERE generation = '5.2')::int AS prereqs,
                (SELECT count(*) FROM public.ka_gochara_rule_path_seal WHERE rule_version = 'v2')::int AS sealed_paths`
      )
      expect(counts.rows[0]).toEqual({ contacts: 1, records: 1, prereqs: 1, sealed_paths: 1 })
    })

    it('EXACT SET: the builder can EXECUTE exactly the 18 granted functions — never seal_generation, the verifiers or the trigger functions', async () => {
      const r = await pool.query<{ proname: string; ok: boolean; pub: boolean }>(
        `SELECT p.proname,
                has_function_privilege('${BUILDER}', p.oid, 'EXECUTE') AS ok,
                has_function_privilege('public', p.oid, 'EXECUTE') AS pub
           FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
          WHERE n.nspname = 'public' AND p.proname LIKE 'ka\\_gochara\\_%'
          ORDER BY 1`
      )
      expect(r.rows).toHaveLength(42)
      expect(r.rows.filter(x => x.pub)).toEqual([])
      expect(r.rows.filter(x => x.ok).map(x => x.proname).sort()).toEqual(Object.keys(GRANTED).sort())
      // spot-check the named exclusions
      for (const name of ['ka_gochara_seal_generation', 'ka_gochara_coverage_drift', 'ka_gochara_membership_violations',
        'ka_gochara_chart_write_guard', 'ka_gochara_global_write_guard', 'ka_gochara_generation_seal_guard']) {
        expect(r.rows.find(x => x.proname === name)?.ok, name).toBe(false)
      }
    })

    it('SEAL BOUNDARY: the builder reads the seal table but can neither write it nor seal a generation', async () => {
      const p = await pool.query(
        `SELECT has_table_privilege($1,'public.ka_gochara_generation_seal','SELECT') AS s,
                has_table_privilege($1,'public.ka_gochara_generation_seal','INSERT') AS i,
                has_table_privilege($1,'public.ka_gochara_generation_seal','UPDATE') AS u,
                has_table_privilege($1,'public.ka_gochara_generation_seal','DELETE') AS d`,
        [BUILDER]
      )
      expect(p.rows[0]).toEqual({ s: true, i: false, u: false, d: false })
      await expect(
        builderTx([[`INSERT INTO public.ka_gochara_generation_seal (chart_id, generation, manifest_id)
                     VALUES ($1,'5.2',gen_random_uuid())`, [CHART]]])
      ).rejects.toThrow(/permission denied for table ka_gochara_generation_seal/)
      await expect(
        builderTx([[`SELECT public.ka_gochara_seal_generation($1::uuid, '5.2')`, [CHART]]])
      ).rejects.toThrow(/permission denied for function ka_gochara_seal_generation/)
    })

    it('EACH GRANT IS NECESSARY: revoking any one of the 18 breaks a builder write, naming exactly that function', async () => {
      let variant = 10
      for (const [name, sig] of Object.entries(GRANTED)) {
        await asRole(OWNER, `REVOKE EXECUTE ON FUNCTION public.${sig} FROM ${BUILDER}`)
        try {
          const err = await runWriter(variant++)
          expect(err, `revoking ${name} must break the writer`).not.toBeNull()
          expect(String(err!.message), name).toMatch(new RegExp(`permission denied for function ${name}\\b`))
        } finally {
          await asRole(OWNER, `GRANT EXECUTE ON FUNCTION public.${sig} TO ${BUILDER}`)
        }
      }
      // restored: the writer works again
      expect(await runWriter(variant)).toBeNull()
    })

    it('idempotent: applying 1220 a second time is a no-op and the writer still works', async () => {
      await applyAsOwner(M1220)
      expect(await runWriter(40)).toBeNull()
    })
  }
)

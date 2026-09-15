// @vitest-environment node
import { randomUUID } from 'node:crypto'
import { beforeAll, describe, expect, it } from 'vitest'
import { Pool } from 'pg'
import { runDataPlaneOwnershipPreflight } from '../../scripts/data-plane-ownership-preflight'
import { attestDataPlaneMigrations } from '../../scripts/data-plane-migration-attestation'
import { readDataPlaneOwnershipStatus } from '../../scripts/data-plane-ownership-status'
import { L1_ACTIVE_TABLES, L2_ACTIVE_TABLES } from '../../scripts/data-plane-ownership-preflight'

const adminUrl = process.env.DATA_PLANE_ROLE_TEST_DATABASE_URL
function roleUrl(role: string): string {
  const url = new URL(adminUrl!)
  url.username = role
  return url.toString()
}
if (adminUrl && !/disposable|dp_role_test/.test(new URL(adminUrl).pathname)) {
  throw new Error('DATA_PLANE_ROLE_TEST_DATABASE_URL must name an approved disposable database.')
}

describe.skipIf(!adminUrl)('DP-SD-018 direct restricted logins — disposable PostgreSQL 15', () => {
  const chart = '11111111-1111-4111-8111-111111111111'
  const l1Build = '22222222-2222-4222-8222-222222222222'
  let admin: Pool
  let builder: Pool
  let migrator: Pool
  let verifier: Pool

  beforeAll(async () => {
    if (await readDataPlaneOwnershipStatus(adminUrl) === 'unmarked') {
      await runDataPlaneOwnershipPreflight(adminUrl)
      await attestDataPlaneMigrations(roleUrl('data_plane_migrator'))
    }
    admin = new Pool({ connectionString: adminUrl })
    builder = new Pool({ connectionString: roleUrl('data_plane_builder') })
    migrator = new Pool({ connectionString: roleUrl('data_plane_migrator') })
    verifier = new Pool({ connectionString: roleUrl('data_plane_verifier') })
    await admin.query(`INSERT INTO charts(id,name,birth_date,birth_time,birth_place,birth_lat,birth_lng,timezone_id,house_system,native_id,role,chart_type)
      VALUES($1,'fixture','2000-01-01','12:00','fixture',20,85,'Asia/Kolkata','sripathi','fixture','fixture','natal') ON CONFLICT DO NOTHING`, [chart])
    await admin.query(`INSERT INTO asset_registry(asset_id,layer,sort_order,sanskrit_name,english_name,english_description,storage_type,target_table,scope,depends_on,catalog_status)
      VALUES('ga_positions','ganita',1,'ga','ga','fixture','postgres_table','chart_facts','per_chart',ARRAY[]::text[],'CURRENT'),
            ('bo_laksana','bodha',2,'bo','bo','fixture','postgres_table','bodha_msr_signals','per_chart',ARRAY['ga_positions'],'CURRENT')
      ON CONFLICT(asset_id) DO UPDATE SET depends_on=EXCLUDED.depends_on`)
    await admin.query(`UPDATE asset_registry SET target_floor=1 WHERE asset_id='ga_positions'`)
    await admin.query(`INSERT INTO fact_category_ownership(fact_category,owning_asset_id)
      VALUES('fixture','ga_positions') ON CONFLICT DO NOTHING`)
  })

  it('rejects protected L1/L2 mutations when no lifecycle context was admitted', async () => {
    await expect(builder.query(
      `INSERT INTO chart_facts(fact_id,chart_id,fact_category,fact_subject,fact_key) VALUES($1,$2,'fixture','fixture','fixture')`,
      [randomUUID(), chart],
    )).rejects.toThrow(/no admitted transaction context/)
    await expect(builder.query(
      `INSERT INTO bodha_msr_signals(signal_id,chart_id) VALUES($1,$2)`, [randomUUID(), chart],
    )).rejects.toThrow(/no admitted transaction context/)
  })

  it('installs the exact BEFORE INSERT/UPDATE/DELETE admission guard on every protected table', async () => {
    const guards = await admin.query<{ relname: string; valid: boolean }>(`
      SELECT c.relname,
        t.tgtype=31 AND t.tgenabled IN ('O','A') AND t.tgfoid=CASE
          WHEN c.relname=ANY($1::text[]) THEN 'public.l1_data_plane_guard_active_mutation()'::regprocedure
          ELSE 'public.l2_data_plane_guard_active_mutation()'::regprocedure
        END AS valid
      FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
      LEFT JOIN pg_trigger t ON t.tgrelid=c.oid AND NOT t.tgisinternal
        AND t.tgname=CASE WHEN c.relname=ANY($1::text[])
          THEN 'l1_data_plane_mutation_guard' ELSE 'l2_data_plane_mutation_guard' END
      WHERE n.nspname='public' AND c.relname=ANY($2::text[])
    `, [[...L1_ACTIVE_TABLES], [...L1_ACTIVE_TABLES, ...L2_ACTIVE_TABLES]])
    expect(new Set(guards.rows.filter((row) => row.valid).map((row) => row.relname)))
      .toEqual(new Set([...L1_ACTIVE_TABLES, ...L2_ACTIVE_TABLES]))
  })

  it('rejects an undeclared empty L1 head and rolls the receipt back atomically', async () => {
    const generation = randomUUID()
    const client = await builder.connect()
    try {
      await client.query('BEGIN')
      await client.query(`INSERT INTO build_runs(id,chart_id,scope,action,state,plan,triggered_by) VALUES($1,$2,'asset','build','running','{}','test')`, [generation, chart])
      await client.query(`INSERT INTO build_run_assets(run_id,asset_id,position,state) VALUES($1,'ga_positions',1,'building')`, [generation])
      for (const [key, value] of Object.entries({
        'madhav.l1_asset_id': 'ga_positions', 'madhav.l1_chart_id': chart,
        'madhav.l1_generation_id': generation, 'madhav.l1_partition_key': 'empty',
        'madhav.l1_contract_version': 'l1.data-plane.contract.1.0',
      })) await client.query('SELECT set_config($1,$2,true)', [key, value])
      await client.query(`SELECT open_l1_data_plane_generation($1,'ga_positions',$2,'empty',1,NULL,'l1.data-plane.contract.1.0','l0.semantic.2026-09-13.1','665096a74a59ea7e0e50ce98fc685899b89f325aca0d91c214f0040e4d259dd1','l0-resource-config-g1','d516aecff9d4e05d929dc7fd71a113fd5c53d1f6ea1eb2582caafd3a339c279a')`, [chart, generation])
      await expect(client.query(`SELECT complete_l1_data_plane_partition($1,'ga_positions',$2,'empty',777)`, [chart, generation])).rejects.toThrow(/reported 777 rows but protected capture contains 0/)
      await client.query('ROLLBACK')
      await client.query('BEGIN')
      await client.query(`INSERT INTO build_runs(id,chart_id,scope,action,state,plan,triggered_by) VALUES($1,$2,'asset','build','running','{}','test')`, [generation, chart])
      await client.query(`INSERT INTO build_run_assets(run_id,asset_id,position,state) VALUES($1,'ga_positions',1,'building')`, [generation])
      for (const [key, value] of Object.entries({
        'madhav.l1_asset_id': 'ga_positions', 'madhav.l1_chart_id': chart,
        'madhav.l1_generation_id': generation, 'madhav.l1_partition_key': 'empty',
        'madhav.l1_contract_version': 'l1.data-plane.contract.1.0',
      })) await client.query('SELECT set_config($1,$2,true)', [key, value])
      await client.query(`SELECT open_l1_data_plane_generation($1,'ga_positions',$2,'empty',1,NULL,'l1.data-plane.contract.1.0','l0.semantic.2026-09-13.1','665096a74a59ea7e0e50ce98fc685899b89f325aca0d91c214f0040e4d259dd1','l0-resource-config-g1','d516aecff9d4e05d929dc7fd71a113fd5c53d1f6ea1eb2582caafd3a339c279a')`, [chart, generation])
      await expect(client.query(`SELECT complete_l1_data_plane_partition($1,'ga_positions',$2,'empty',0)`, [chart, generation])).rejects.toThrow(/undeclared empty/)
      await client.query('ROLLBACK')
      expect((await verifier.query(`SELECT count(*)::int AS n FROM l1_data_plane_generations WHERE generation_id=$1`, [generation])).rows[0].n).toBe(0)
    } finally { client.release() }
  })

  it('opens, populates, captures, completes, replays, selects and rolls back L1', async () => {
    const client = await builder.connect()
    try {
      await client.query('BEGIN')
      await client.query(`INSERT INTO build_runs(id,chart_id,scope,action,state,plan,triggered_by)
        VALUES($1,$2,'asset','build','running','{}','test')`, [l1Build, chart])
      await client.query(`INSERT INTO build_run_assets(run_id,asset_id,position,state) VALUES($1,'ga_positions',1,'building')`, [l1Build])
      for (const [key, value] of Object.entries({
        'madhav.l1_asset_id': 'ga_positions', 'madhav.l1_chart_id': chart,
        'madhav.l1_generation_id': l1Build, 'madhav.l1_partition_key': 'ayanamsha:lahiri',
        'madhav.l1_contract_version': 'l1.data-plane.contract.1.0',
      })) await client.query('SELECT set_config($1,$2,true)', [key, value])
      await client.query(`SELECT open_l1_data_plane_generation($1,'ga_positions',$2,'ayanamsha:lahiri',1,NULL,
        'l1.data-plane.contract.1.0','l0.semantic.2026-09-13.1','665096a74a59ea7e0e50ce98fc685899b89f325aca0d91c214f0040e4d259dd1',
        'l0-resource-config-g1','d516aecff9d4e05d929dc7fd71a113fd5c53d1f6ea1eb2582caafd3a339c279a')`, [chart, l1Build])
      await client.query('SAVEPOINT foreign_category')
      await expect(client.query(`INSERT INTO chart_facts(fact_id,chart_id,ayanamsha_id,build_id,fact_category,fact_subject,fact_key)
        VALUES($1,$2,'lahiri',$3,'unowned-category','fixture','foreign')`, [randomUUID(), chart, l1Build]))
        .rejects.toThrow(/cannot mutate chart_facts category/)
      await client.query('ROLLBACK TO SAVEPOINT foreign_category')
      await client.query(`INSERT INTO chart_facts(fact_id,chart_id,ayanamsha_id,build_id,fact_category,fact_subject,fact_key,
        fact_value_text,citation_ref,citation_human,source_calculation,verification_pass_status,engine_version,computed_at)
        VALUES($1,$2,'lahiri',$3,'fixture','fixture','fixture','value','fixture','fixture','fixture','single','fixture',now())`,
      [randomUUID(), chart, l1Build])
      await client.query(`SELECT complete_l1_data_plane_partition($1,'ga_positions',$2,'ayanamsha:lahiri',1)`, [chart, l1Build])
      await client.query('COMMIT')
      await client.query('BEGIN')
      for (const [key, value] of Object.entries({
        'madhav.l1_asset_id': 'ga_positions', 'madhav.l1_chart_id': chart,
        'madhav.l1_generation_id': l1Build, 'madhav.l1_partition_key': 'ayanamsha:lahiri',
        'madhav.l1_contract_version': 'l1.data-plane.contract.1.0',
      })) await client.query('SELECT set_config($1,$2,true)', [key, value])
      await client.query(`SELECT open_l1_data_plane_generation($1,'ga_positions',$2,'ayanamsha:lahiri',1,NULL,
        'l1.data-plane.contract.1.0','l0.semantic.2026-09-13.1','665096a74a59ea7e0e50ce98fc685899b89f325aca0d91c214f0040e4d259dd1',
        'l0-resource-config-g1','d516aecff9d4e05d929dc7fd71a113fd5c53d1f6ea1eb2582caafd3a339c279a')`, [chart, l1Build])
      await client.query(`SELECT complete_l1_data_plane_partition($1,'ga_positions',$2,'ayanamsha:lahiri',1)`, [chart, l1Build])
      await client.query('COMMIT')
      expect((await client.query(`SELECT count(*)::int AS n FROM select_l1_data_plane_generation($1,'ga_positions',$2)`, [chart, l1Build])).rows[0].n).toBe(1)
      await expect(migrator.query(`SELECT rollback_l1_data_plane_generation($1,'ga_positions',$2)`, [chart, l1Build])).resolves.toBeDefined()
    } finally { client.release() }
  })

  it('binds exact L1 input and opens, populates, captures, completes and selects L2', async () => {
    const build = '33333333-3333-4333-8333-333333333333'
    const digest = (await verifier.query(`SELECT semantic_output_digest FROM l1_data_plane_generations WHERE generation_id=$1`, [l1Build])).rows[0].semantic_output_digest
    const vector = [{ layer: 'L1', asset_id: 'ga_positions', generation_id: l1Build, semantic_output_digest: digest }]
    const context = { chart_id: chart, generation_context_id: 'fixture-context', calculation_context_id: 'fixture-calculation', subject_id: 'fixture', ayanamsha_id: 'lahiri', reference_frame: 'sidereal', varga_id: 'D1', partition_key: 'ayanamsha:lahiri' }
    const client = await builder.connect()
    try {
      await client.query('BEGIN')
      await client.query(`UPDATE build_run_assets SET state='complete' WHERE run_id=$1`, [l1Build])
      await client.query(`UPDATE build_runs SET state='completed' WHERE id=$1`, [l1Build])
      await client.query(`INSERT INTO build_runs(id,chart_id,scope,action,state,plan,triggered_by) VALUES($1,$2,'asset','build','running','{}','test')`, [build, chart])
      await client.query(`INSERT INTO build_run_assets(run_id,asset_id,position,state) VALUES($1,'bo_laksana',1,'building')`, [build])
      for (const [key, value] of Object.entries({
        'madhav.l2_asset_id': 'bo_laksana', 'madhav.l2_chart_id': chart,
        'madhav.l2_generation_id': 'l2-fixture-generation', 'madhav.l2_partition_key': 'ayanamsha:lahiri',
        'madhav.l2_build_id': build, 'madhav.l2_contract_version': 'MADHAV_DATA_PLANE_L2_BODHA_CONTRACT/2.0',
      })) await client.query('SELECT set_config($1,$2,true)', [key, value])
      await client.query('SELECT bind_l2_exact_inputs($1,$2)', [chart, JSON.stringify(vector)])
      await client.query(`SELECT open_l2_data_plane_generation($1,'bo_laksana','l2-fixture-generation','ayanamsha:lahiri',1,$2,NULL,
        'MADHAV_DATA_PLANE_L2_BODHA_CONTRACT/2.0',$3,$4,$5,'data_plane_builder')`,
      [chart, build, '1'.repeat(64), context, JSON.stringify(vector)])
      await client.query(`INSERT INTO public.bodha_msr_signals(signal_id,chart_id,ayanamsha_id,build_id,signal_type_id,signal_type_class,
        signal_tradition,fact_kind,source_l1_asset,source_subsystem,configuration_jsonb,constituent_facts_array,deterministic_strength,
        verification_certainty,computed_salience,salience_formula_version,domains_affected_array,domain_salience_jsonb,active_duration_class,
        verification_pass_status,citation_ref,citation_human,computed_at,engine_version)
        VALUES($1,$2,'lahiri',$3,'fixture','fixture','fixture','fixture','ga_positions','fixture','{}',ARRAY['fixture'],1,1,1,
        'fixture',ARRAY['fixture'],'{}','fixture','single','fixture','fixture',now(),'fixture')`, [randomUUID(), chart, build])
      await client.query('SAVEPOINT foreign_producer')
      await client.query(`SELECT set_config('madhav.l2_asset_id','bo_arudha',true)`)
      await expect(client.query(`UPDATE public.bodha_msr_signals
        SET computed_salience=computed_salience WHERE build_id=$1`, [build]))
        .rejects.toThrow(/cannot mutate MSR rows produced by bo_laksana/)
      await client.query('ROLLBACK TO SAVEPOINT foreign_producer')
      await client.query(`SELECT complete_l2_data_plane_partition($1,'bo_laksana','l2-fixture-generation','ayanamsha:lahiri',$2,1,0,0)`, [chart, build])
      await client.query(`UPDATE build_run_assets SET state='complete' WHERE run_id=$1`, [build])
      await client.query(`UPDATE build_runs SET state='completed' WHERE id=$1`, [build])
      await client.query('COMMIT')
      expect((await verifier.query(`SELECT producer_asset_id FROM bodha_msr_signals WHERE build_id=$1`, [build])).rows[0].producer_asset_id)
        .toBe('bo_laksana')
      expect((await verifier.query(`SELECT count(*)::int AS n FROM select_l2_data_plane_generation($1,'bo_laksana','l2-fixture-generation')`, [chart])).rows[0].n).toBe(1)
      await expect(migrator.query(`SELECT rollback_l2_data_plane_generation($1,'bo_laksana','l2-fixture-generation')`, [chart])).resolves.toBeDefined()
    } finally { client.release() }
  })

  it('blocks owner escalation, DDL, TRUNCATE, trigger disable, history writes and terminal forgery', async () => {
    await expect(builder.query('SET ROLE data_plane_l1_owner')).rejects.toThrow()
    await expect(builder.query('TRUNCATE chart_facts')).rejects.toThrow()
    await expect(builder.query('ALTER TABLE chart_facts DISABLE TRIGGER l1_data_plane_capture')).rejects.toThrow()
    await expect(builder.query('CREATE OR REPLACE FUNCTION public.dp_forge() RETURNS void LANGUAGE sql AS $$ SELECT $$')).rejects.toThrow()
    await expect(builder.query(`INSERT INTO l1_data_plane_generation_heads(chart_id,asset_id,current_generation_id) VALUES($1,'ga_positions','forged')`, [chart])).rejects.toThrow()
    await expect(builder.query(`UPDATE l1_data_plane_generations SET status='complete' WHERE chart_id=$1`, [chart])).rejects.toThrow()
    await expect(verifier.query(`DELETE FROM chart_facts WHERE chart_id=$1`, [chart])).rejects.toThrow()
    await expect(verifier.query(`SELECT count(*) FROM select_l1_data_plane_generation($1,'ga_positions',$2)`, [chart, l1Build])).resolves.toBeDefined()
  })

  it('rejects direct UPDATE/DELETE and fabricated or unbound L2 completion', async () => {
    await expect(builder.query(`UPDATE chart_facts SET fact_key=fact_key WHERE chart_id=$1`, [chart])).rejects.toThrow(/no admitted transaction context/)
    await expect(builder.query(`DELETE FROM chart_facts WHERE chart_id=$1`, [chart])).rejects.toThrow(/no admitted transaction context/)
    await expect(builder.query(`UPDATE bodha_msr_signals SET signal_type_id=signal_type_id WHERE chart_id=$1`, [chart])).rejects.toThrow(/no admitted transaction context/)
    await expect(builder.query(`DELETE FROM bodha_msr_signals WHERE chart_id=$1`, [chart])).rejects.toThrow(/no admitted transaction context/)

    const digest = (await verifier.query(`SELECT semantic_output_digest FROM l1_data_plane_generations WHERE generation_id=$1`, [l1Build])).rows[0].semantic_output_digest
    const vector = [{ layer: 'L1', asset_id: 'ga_positions', generation_id: l1Build, semantic_output_digest: digest }]
    const context = { chart_id: chart, generation_context_id: 'negative-context', calculation_context_id: 'negative-calculation', subject_id: 'fixture', ayanamsha_id: 'lahiri', reference_frame: 'sidereal', varga_id: 'D1', partition_key: 'negative' }
    for (const bind of [false, true]) {
      const build = randomUUID()
      const generation = randomUUID()
      const client = await builder.connect()
      try {
        await client.query('BEGIN')
        await client.query(`INSERT INTO build_runs(id,chart_id,scope,action,state,plan,triggered_by) VALUES($1,$2,'asset','build','running','{}','test')`, [build, chart])
        await client.query(`INSERT INTO build_run_assets(run_id,asset_id,position,state) VALUES($1,'bo_laksana',1,'building')`, [build])
        for (const [key, value] of Object.entries({
          'madhav.l2_asset_id': 'bo_laksana', 'madhav.l2_chart_id': chart,
          'madhav.l2_generation_id': generation, 'madhav.l2_partition_key': 'negative',
          'madhav.l2_build_id': build, 'madhav.l2_contract_version': 'MADHAV_DATA_PLANE_L2_BODHA_CONTRACT/2.0',
        })) await client.query('SELECT set_config($1,$2,true)', [key, value])
        if (bind) await client.query('SELECT bind_l2_exact_inputs($1,$2)', [chart, JSON.stringify(vector)])
        const open = client.query(`SELECT open_l2_data_plane_generation($1,'bo_laksana',$2,'negative',1,$3,NULL,
          'MADHAV_DATA_PLANE_L2_BODHA_CONTRACT/2.0',$4,$5,$6,'data_plane_builder')`,
        [chart, generation, build, '1'.repeat(64), context, JSON.stringify(vector)])
        if (!bind) {
          await expect(open).rejects.toThrow(/requires an exact-input bind receipt/)
        } else {
          await open
          await expect(client.query(`SELECT complete_l2_data_plane_partition($1,'bo_laksana',$2,'negative',$3,99,88,77)`, [chart, generation, build]))
            .rejects.toThrow(/reported 99 inserts \+ 88 updates but protected capture contains 0 rows/)
        }
        await client.query('ROLLBACK')
      } finally { client.release() }
    }
  })

  it('fails semantic attestation on recursive membership, function replacement, and marker tampering', async () => {
    await admin.query('CREATE ROLE dp_owner_bridge NOLOGIN NOINHERIT')
    try {
      await admin.query('GRANT data_plane_l1_owner TO dp_owner_bridge; GRANT dp_owner_bridge TO data_plane_builder')
      await expect(readDataPlaneOwnershipStatus(roleUrl('data_plane_verifier'))).rejects.toThrow(/role membership/)
    } finally {
      await admin.query('REVOKE dp_owner_bridge FROM data_plane_builder; REVOKE data_plane_l1_owner FROM dp_owner_bridge; DROP ROLE dp_owner_bridge')
    }

    await admin.query('CREATE ROLE dp_foreign_role NOLOGIN NOINHERIT')
    try {
      await admin.query('GRANT dp_foreign_role TO data_plane_builder')
      await expect(readDataPlaneOwnershipStatus(roleUrl('data_plane_verifier'))).rejects.toThrow(/Exact bidirectional/)
      await admin.query('REVOKE dp_foreign_role FROM data_plane_builder; GRANT data_plane_verifier TO dp_foreign_role')
      await expect(readDataPlaneOwnershipStatus(roleUrl('data_plane_verifier'))).rejects.toThrow(/Exact bidirectional/)
    } finally {
      await admin.query('REVOKE dp_foreign_role FROM data_plane_builder; REVOKE data_plane_verifier FROM dp_foreign_role; DROP ROLE dp_foreign_role')
    }

    const signature = 'public.open_l1_data_plane_generation(uuid,text,text,text,integer,text,text,text,text,text,text)'
    const original = (await admin.query<{ definition: string }>('SELECT pg_get_functiondef($1::regprocedure) AS definition', [signature])).rows[0].definition
    try {
      await admin.query(`CREATE OR REPLACE FUNCTION public.open_l1_data_plane_generation(
        p_chart_id uuid,p_asset_id text,p_generation_id text,p_partition_key text,p_expected_partitions integer,
        p_correction_of_generation_id text,p_contract_version text,p_l0_semantic_release_id text,
        p_l0_semantic_release_digest text,p_l0_config_generation_id text,p_l0_config_digest text
      ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog,public,pg_temp AS $$ BEGIN NULL; END $$`)
      await expect(readDataPlaneOwnershipStatus(roleUrl('data_plane_verifier'))).rejects.toThrow(/function definition digest/)
    } finally { await admin.query(original) }

    const identities = await admin.query<{ filename: string; sql_identity: string }>(`
      SELECT filename,sql_identity FROM _migrations_applied
      WHERE filename IN ('1035_data_plane_l1_producer_history.sql','1036_data_plane_l2_producer_generations.sql') ORDER BY filename`)
    try {
      await admin.query(`UPDATE _migrations_applied SET sql_identity='tampered'
        WHERE filename IN ('1035_data_plane_l1_producer_history.sql','1036_data_plane_l2_producer_generations.sql')`)
      await expect(readDataPlaneOwnershipStatus(roleUrl('data_plane_verifier'))).rejects.toThrow(/mismatched protected identity/)
    } finally {
      for (const row of identities.rows) await admin.query('UPDATE _migrations_applied SET sql_identity=$1 WHERE filename=$2', [row.sql_identity, row.filename])
    }
  })

  it('fails semantic attestation on rewritten views and undeclared protected-table triggers', async () => {
    const view = 'public.l1_data_plane_current_facts'
    const originalView = (await admin.query<{ definition: string }>(
      'SELECT pg_get_viewdef($1::regclass,true) AS definition', [view],
    )).rows[0].definition.replace(/;\s*$/, '')
    try {
      await admin.query(`CREATE OR REPLACE VIEW ${view} AS SELECT * FROM (${originalView}) AS drift WHERE false`)
      await expect(readDataPlaneOwnershipStatus(roleUrl('data_plane_verifier'))).rejects.toThrow(/policies, views, or default privileges drift/)
    } finally {
      await admin.query(`CREATE OR REPLACE VIEW ${view} AS ${originalView}`)
    }

    try {
      await admin.query(`CREATE TRIGGER dp_rogue_trigger BEFORE INSERT ON public.chart_facts
        FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_reject_immutable_change()`)
      await expect(readDataPlaneOwnershipStatus(roleUrl('data_plane_verifier'))).rejects.toThrow(/trigger inventory or definition drift/)
    } finally {
      await admin.query('DROP TRIGGER IF EXISTS dp_rogue_trigger ON public.chart_facts')
    }

    try {
      await admin.query(`SET ROLE data_plane_l1_owner;
        ALTER DEFAULT PRIVILEGES GRANT EXECUTE ON FUNCTIONS TO data_plane_builder;
        RESET ROLE`)
      await expect(readDataPlaneOwnershipStatus(roleUrl('data_plane_verifier'))).rejects.toThrow(/default privileges drift/)
    } finally {
      await admin.query(`SET ROLE data_plane_l1_owner;
        ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM data_plane_builder;
        RESET ROLE`)
    }
  })

  it('rejects mismatched context atomically', async () => {
    const generation = randomUUID()
    const client = await builder.connect()
    try {
      await client.query('BEGIN')
      await client.query(`INSERT INTO build_runs(id,chart_id,scope,action,state,plan,triggered_by) VALUES($1,$2,'asset','build','running','{}','test')`, [generation, chart])
      await client.query(`INSERT INTO build_run_assets(run_id,asset_id,position,state) VALUES($1,'ga_positions',1,'building')`, [generation])
      await client.query(`SELECT set_config('madhav.l1_asset_id','ga_positions',true),set_config('madhav.l1_chart_id',$1,true),set_config('madhav.l1_generation_id','wrong',true),set_config('madhav.l1_partition_key','p',true),set_config('madhav.l1_contract_version','l1.data-plane.contract.1.0',true)`, [chart])
      await expect(client.query(`SELECT open_l1_data_plane_generation($1,'ga_positions',$2,'p',1,NULL,'l1.data-plane.contract.1.0','l0.semantic.2026-09-13.1','665096a74a59ea7e0e50ce98fc685899b89f325aca0d91c214f0040e4d259dd1','l0-resource-config-g1','d516aecff9d4e05d929dc7fd71a113fd5c53d1f6ea1eb2582caafd3a339c279a')`, [chart, generation])).rejects.toThrow(/context/)
      await client.query('ROLLBACK')
      expect((await verifier.query(`SELECT count(*)::int AS n FROM l1_data_plane_generations WHERE generation_id=$1`, [generation])).rows[0].n).toBe(0)
    } finally { client.release() }
  })

  it('rejects cross-chart and natural-key UPDATE transfer on every protected table', async () => {
    const schema = 'dp_guard_negative'
    const otherChart = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
    await admin.query(`DROP SCHEMA IF EXISTS ${schema} CASCADE; CREATE SCHEMA ${schema}; GRANT USAGE ON SCHEMA ${schema} TO data_plane_builder`)
    try {
      for (const [layer, table] of [
        ...L1_ACTIVE_TABLES.map((table) => ['l1', table] as const),
        ...L2_ACTIVE_TABLES.map((table) => ['l2', table] as const),
      ]) {
        const quoted = `"${table.replaceAll('"', '""')}"`
        const guard = layer === 'l1' ? 'l1_data_plane_guard_active_mutation' : 'l2_data_plane_guard_active_mutation'
        await admin.query(`CREATE TABLE ${schema}.${quoted}(row_id text PRIMARY KEY,chart_id uuid NOT NULL)`)
        await admin.query(`INSERT INTO ${schema}.${quoted} VALUES('original',$1)`, [chart])
        await admin.query(`CREATE TRIGGER protected_guard BEFORE INSERT OR UPDATE OR DELETE ON ${schema}.${quoted}
          FOR EACH ROW EXECUTE FUNCTION public.${guard}()`)
        await admin.query(`GRANT SELECT,UPDATE ON ${schema}.${quoted} TO data_plane_builder`)
        const client = await builder.connect()
        try {
          await client.query('BEGIN')
          for (const [key, value] of Object.entries({
            [`madhav.${layer}_asset_id`]: 'fixture', [`madhav.${layer}_chart_id`]: chart,
            [`madhav.${layer}_generation_id`]: 'fixture', [`madhav.${layer}_partition_key`]: 'fixture',
            ...(layer === 'l2' ? { 'madhav.l2_build_id': randomUUID() } : {}),
          })) await client.query('SELECT set_config($1,$2,true)', [key, value])
          await client.query('SAVEPOINT cross_chart')
          await expect(client.query(`UPDATE ${schema}.${quoted} SET chart_id=$1 WHERE row_id='original'`, [otherChart]))
            .rejects.toThrow(/row chart does not match admitted chart/)
          await client.query('ROLLBACK TO SAVEPOINT cross_chart')
          await expect(client.query(`UPDATE ${schema}.${quoted} SET row_id='transferred' WHERE row_id='original'`))
            .rejects.toThrow(/cannot transfer natural-key column/)
          await client.query('ROLLBACK')
        } finally {
          client.release()
          await admin.query(`DROP TABLE ${schema}.${quoted}`)
        }
      }
    } finally {
      await admin.query(`DROP SCHEMA IF EXISTS ${schema} CASCADE`)
    }
  })

  it('commits the ownership-only stage with builder DML denied on every protected table', async () => {
    await admin.query(`DELETE FROM public._migrations_applied
      WHERE filename IN ('1035_data_plane_l1_producer_history.sql','1036_data_plane_l2_producer_generations.sql')`)
    await runDataPlaneOwnershipPreflight(adminUrl)
    try {
      const privileges = await admin.query<{ relname: string; writable: boolean }>(`
        SELECT c.relname,has_table_privilege('data_plane_builder',c.oid,'INSERT,UPDATE,DELETE') writable
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='public' AND c.relname=ANY($1::text[])
      `, [[...L1_ACTIVE_TABLES, ...L2_ACTIVE_TABLES]])
      expect(privileges.rows).toHaveLength(L1_ACTIVE_TABLES.length + L2_ACTIVE_TABLES.length)
      expect(privileges.rows.some((row) => row.writable)).toBe(false)
      await expect(builder.query(
        `INSERT INTO chart_facts(fact_id,chart_id,fact_category,fact_subject,fact_key)
         VALUES($1,$2,'fixture','fixture','fixture')`, [randomUUID(), chart],
      )).rejects.toThrow(/permission denied/)
    } finally {
      await admin.query(`
        ALTER TABLE public.l1_data_plane_function_attestations DISABLE TRIGGER USER;
        ALTER TABLE public.l1_data_plane_policy_attestations DISABLE TRIGGER USER;
        ALTER TABLE public.l2_data_plane_function_attestations DISABLE TRIGGER USER;
        ALTER TABLE public.l2_data_plane_policy_attestations DISABLE TRIGGER USER;
        DELETE FROM public._migrations_applied
        WHERE filename IN ('1035_data_plane_l1_producer_history.sql','1036_data_plane_l2_producer_generations.sql')
      `)
      await attestDataPlaneMigrations(roleUrl('data_plane_migrator'))
    }
  })
})

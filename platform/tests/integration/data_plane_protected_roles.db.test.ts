// @vitest-environment node
import { randomUUID } from 'node:crypto'
import { beforeAll, describe, expect, it } from 'vitest'
import { Pool } from 'pg'
import { runDataPlaneOwnershipPreflight } from '../../scripts/data-plane-ownership-preflight'
import { attestDataPlaneMigrations } from '../../scripts/data-plane-migration-attestation'

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
    await runDataPlaneOwnershipPreflight(adminUrl)
    await attestDataPlaneMigrations(roleUrl('data_plane_migrator'))
    admin = new Pool({ connectionString: adminUrl })
    builder = new Pool({ connectionString: roleUrl('data_plane_builder') })
    migrator = new Pool({ connectionString: roleUrl('data_plane_migrator') })
    verifier = new Pool({ connectionString: roleUrl('data_plane_verifier') })
    await admin.query(`INSERT INTO charts(id,name,birth_date,birth_time,birth_place,birth_lat,birth_lng,timezone_id,house_system,native_id,role,chart_type)
      VALUES($1,'fixture','2000-01-01','12:00','fixture',20,85,'Asia/Kolkata','sripathi','fixture','fixture','natal') ON CONFLICT DO NOTHING`, [chart])
    await admin.query(`INSERT INTO asset_registry(asset_id,layer,sort_order,sanskrit_name,english_name,english_description,storage_type,target_table,scope,depends_on,catalog_status)
      VALUES('ga_positions','ganita',1,'ga','ga','fixture','postgres_table','chart_facts','per_chart',ARRAY[]::text[],'CURRENT'),
            ('bo_test','bodha',2,'bo','bo','fixture','postgres_table','bodha_msr_signals','per_chart',ARRAY['ga_positions'],'CURRENT')
      ON CONFLICT(asset_id) DO UPDATE SET depends_on=EXCLUDED.depends_on`)
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
      await client.query(`INSERT INTO build_run_assets(run_id,asset_id,position,state) VALUES($1,'bo_test',1,'building')`, [build])
      for (const [key, value] of Object.entries({
        'madhav.l2_asset_id': 'bo_test', 'madhav.l2_chart_id': chart,
        'madhav.l2_generation_id': 'l2-fixture-generation', 'madhav.l2_partition_key': 'ayanamsha:lahiri',
        'madhav.l2_build_id': build, 'madhav.l2_contract_version': 'MADHAV_DATA_PLANE_L2_BODHA_CONTRACT/2.0',
      })) await client.query('SELECT set_config($1,$2,true)', [key, value])
      await client.query('SELECT bind_l2_exact_inputs($1,$2)', [chart, JSON.stringify(vector)])
      await client.query(`SELECT open_l2_data_plane_generation($1,'bo_test','l2-fixture-generation','ayanamsha:lahiri',1,$2,NULL,
        'MADHAV_DATA_PLANE_L2_BODHA_CONTRACT/2.0',$3,$4,$5,'data_plane_builder')`,
      [chart, build, '1'.repeat(64), context, JSON.stringify(vector)])
      await client.query(`INSERT INTO public.bodha_msr_signals(signal_id,chart_id,ayanamsha_id,build_id,signal_type_id,signal_type_class,
        signal_tradition,fact_kind,source_l1_asset,source_subsystem,configuration_jsonb,constituent_facts_array,deterministic_strength,
        verification_certainty,computed_salience,salience_formula_version,domains_affected_array,domain_salience_jsonb,active_duration_class,
        verification_pass_status,citation_ref,citation_human,computed_at,engine_version)
        VALUES($1,$2,'lahiri',$3,'fixture','fixture','fixture','fixture','ga_positions','fixture','{}',ARRAY['fixture'],1,1,1,
        'fixture',ARRAY['fixture'],'{}','fixture','single','fixture','fixture',now(),'fixture')`, [randomUUID(), chart, build])
      await client.query(`SELECT complete_l2_data_plane_partition($1,'bo_test','l2-fixture-generation','ayanamsha:lahiri',$2,1,0,0)`, [chart, build])
      await client.query(`UPDATE build_run_assets SET state='complete' WHERE run_id=$1`, [build])
      await client.query(`UPDATE build_runs SET state='completed' WHERE id=$1`, [build])
      await client.query('COMMIT')
      expect((await verifier.query(`SELECT count(*)::int AS n FROM select_l2_data_plane_generation($1,'bo_test','l2-fixture-generation')`, [chart])).rows[0].n).toBe(1)
      await expect(migrator.query(`SELECT rollback_l2_data_plane_generation($1,'bo_test','l2-fixture-generation')`, [chart])).resolves.toBeDefined()
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
})

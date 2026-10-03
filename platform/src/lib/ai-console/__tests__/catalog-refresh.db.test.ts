import { randomBytes, randomUUID } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { Pool, type PoolClient } from 'pg'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import * as repo from '../repository'
import { AI_ROLES } from '../types'
import { assertDisposableAiConsoleDatabaseUrl } from '../../../../scripts/ai-console/test_database_guard'

// Only an explicitly guarded disposable localhost database is accepted.
const databaseUrl = process.env.AI_CONSOLE_TEST_DATABASE_URL
const enabled = process.env.RUN_DB_TESTS === '1' && !!databaseUrl
const guardedDatabaseUrl = enabled ? assertDisposableAiConsoleDatabaseUrl(databaseUrl!) : undefined
if (!enabled) console.info('UNQUALIFIED: catalog refresh DB tests require RUN_DB_TESTS=1 and disposable AI_CONSOLE_TEST_DATABASE_URL')

const precedingMigrations = [
  'migrations/1124_ai_console_byok_routing.sql',
  'migrations/1125_ai_snapshot_shape_operator_precedence.sql',
  'migrations/1151_ai_console_model_shortlist.sql',
  'supabase/migrations/1158_ai_console_configuration_types.sql',
  'supabase/migrations/1159_ai_anthropic_workspace_id.sql',
  'supabase/migrations/1300_ai_console_role_effort.sql',
].map(path => readFileSync(resolve(__dirname, '../../../../', path), 'utf8'))
const refreshMigration = readFileSync(resolve(__dirname, '../../../../supabase/migrations/1301_ai_console_catalog_refresh.sql'), 'utf8')
const baseSchema = `CREATE TABLE profiles(id text PRIMARY KEY,status text NOT NULL DEFAULT 'active',role text NOT NULL DEFAULT 'guest');
  CREATE TABLE charts(id uuid PRIMARY KEY,owner_id text REFERENCES profiles(id));
  CREATE TABLE chart_grants(chart_id uuid REFERENCES charts(id),principal_id text REFERENCES profiles(id),permission text);
  CREATE TABLE conversations(id uuid PRIMARY KEY,user_id text NOT NULL REFERENCES profiles(id),chart_id uuid REFERENCES charts(id),module text,title text);
  CREATE TABLE admin_audit_log(actor_id text,action text,target_user_id text,detail jsonb);`

describe.skipIf(!enabled).sequential('Catalog refresh real migration and repository fences', () => {
  const schema = `ai_catalog_${randomUUID().replaceAll('-', '')}`
  const rollbackSchema = `${schema}_rollback`
  const user = 'catalog-alice'
  const other = 'catalog-bob'
  const ungranted = 'catalog-charlie'
  const admin = 'catalog-admin'
  const connectionId = randomUUID()
  const configurationId = randomUUID()
  const sha = 'a'.repeat(64)
  const model = { modelId: 'gpt-6-astra', displayName: 'GPT 6 Astra', compatibleRoles: [...AI_ROLES],
    supportsTools: true, supportsStructuredOutput: true, supportedEfforts: ['low', 'high', 'ultra'] }
  const poolGlobal = globalThis as typeof globalThis & { __pgPool?: Pool }
  let pool: Pool
  let previousPool: Pool | undefined
  let beforeMigration: unknown
  const encrypted = () => ({ ciphertext: randomBytes(24), nonce: randomBytes(12), authTag: randomBytes(16),
    wrappedDataKey: randomBytes(32), wrapNonce: randomBytes(12), wrapAuthTag: randomBytes(16),
    keyVersion: 'test', mask: '••••1234', fingerprint: randomBytes(32).toString('hex') })

  async function transaction(work: (client: PoolClient) => Promise<void>) {
    const client = await pool.connect()
    try { await client.query('BEGIN'); await work(client); await client.query('COMMIT') }
    catch (error) { await client.query('ROLLBACK'); throw error }
    finally { client.release() }
  }
  async function protectedState() {
    return {
      roles: (await pool.query('SELECT * FROM ai_custom_configuration_roles ORDER BY role')).rows,
      defaults: (await pool.query('SELECT * FROM ai_user_defaults')).rows,
      probe: (await pool.query(`SELECT model_id,user_selected,plain_tested_at,tested_credential_version,last_probe_at,
        last_probe_error_code,last_probe_input_tokens,last_probe_output_tokens FROM ai_connection_models WHERE connection_id=$1`, [connectionId])).rows,
    }
  }
  async function ageApiAttempt(id: string) {
    await pool.query("UPDATE ai_provider_connections SET catalog_attempted_at=clock_timestamp()-interval '4 minutes' WHERE id=$1", [id])
  }
  async function ageCliAttempt() {
    await pool.query("UPDATE ai_cli_installations SET catalog_attempted_at=clock_timestamp()-interval '4 minutes' WHERE cli_id='codex'")
  }

  beforeAll(async () => {
    pool = new Pool({ connectionString: guardedDatabaseUrl, options: `-c search_path=${schema},public -c statement_timeout=5000`, max: 4 })
    await pool.query(`CREATE SCHEMA ${schema}`)
    await transaction(async client => {
      await client.query(baseSchema)
      for (const migration of precedingMigrations) await client.query(migration)
    })
    await pool.query("INSERT INTO profiles(id,role) VALUES($1,'guest'),($2,'guest'),($3,'guest'),($4,'super_admin')", [user, other, ungranted, admin])
    await pool.query(`INSERT INTO ai_provider_connections(id,user_id,provider_id,name,credential_ciphertext,credential_nonce,
      credential_tag,wrapped_dek,wrap_nonce,wrap_tag,kek_version,masked_suffix,keyed_fingerprint,credential_validity,
      validation_state,last_validated_at) VALUES($1,$2,'openai','Before migration',$3,$4,$5,$6,$4,$5,'test','••••1234','fake-fingerprint',
      'valid','validated',now())`, [connectionId, user, randomBytes(24), randomBytes(12), randomBytes(16), randomBytes(32)])
    await pool.query(`INSERT INTO ai_connection_models(connection_id,model_id,display_name,compatible_roles,supports_tools,
      supports_structured_output,user_selected,plain_tested_at,tested_credential_version,last_probe_at,last_probe_input_tokens,last_probe_output_tokens)
      VALUES($1,$2,$3,$4,true,true,true,now(),1,now(),11,7)`, [connectionId, model.modelId, model.displayName, AI_ROLES])
    await transaction(async client => {
      await client.query(`INSERT INTO ai_custom_configurations(id,user_id,name,configuration_kind) VALUES($1,$2,'Saved roles','custom_api')`, [configurationId, user])
      for (const role of AI_ROLES) await client.query(`INSERT INTO ai_custom_configuration_roles(configuration_id,user_id,role,kind,connection_id,model_id,effort)
        VALUES($1,$2,$3,'provider_model',$4,$5,'high')`, [configurationId, user, role, connectionId, model.modelId])
    })
    await pool.query(`INSERT INTO ai_user_defaults(user_id,kind,configuration_id) VALUES($1,'custom_configuration',$2)`, [user, configurationId])
    await pool.query(`INSERT INTO ai_cli_installations(cli_id,detected_product,detected_version,validation_state) VALUES('codex','Codex CLI','1.2.3','reachable')`)
    await pool.query(`INSERT INTO ai_cli_models(cli_id,model_id,display_name,compatible_roles,supports_structured_output)
      VALUES('codex',$1,$2,$3,true)`, [model.modelId, model.displayName, AI_ROLES])
    beforeMigration = await protectedState()
    await transaction(client => client.query(refreshMigration).then(() => {}))
    previousPool = poolGlobal.__pgPool
    poolGlobal.__pgPool = pool
  })

  afterAll(async () => {
    poolGlobal.__pgPool = previousPool
    if (pool) {
      // Both names are unique schemas created solely by this guarded test.
      await pool.query(`DROP SCHEMA IF EXISTS ${rollbackSchema} CASCADE`)
      await pool.query(`DROP SCHEMA IF EXISTS ${schema} CASCADE`)
      await pool.end()
    }
  })

  it('preserves roles, default, and probe evidence on the first application and rerun', async () => {
    expect(await protectedState()).toEqual(beforeMigration)
    await transaction(client => client.query(refreshMigration).then(() => {}))
    expect(await protectedState()).toEqual(beforeMigration)
  })

  it('rolls back all 1301 columns and constraint replacement atomically', async () => {
    await pool.query(`CREATE SCHEMA ${rollbackSchema}`)
    await transaction(async client => {
      await client.query(`SET LOCAL search_path=${rollbackSchema},public`)
      await client.query(baseSchema)
      for (const migration of precedingMigrations) await client.query(migration)
    })
    const client = await pool.connect()
    try {
      await client.query('BEGIN')
      await client.query(`SET LOCAL search_path=${rollbackSchema},public`)
      await client.query(refreshMigration)
      expect((await client.query(`SELECT column_name FROM information_schema.columns WHERE table_schema=$1
        AND table_name='ai_cli_models' AND column_name='supported_efforts'`, [rollbackSchema])).rowCount).toBe(1)
      await client.query('ROLLBACK')
      expect((await client.query(`SELECT column_name FROM information_schema.columns WHERE table_schema=$1
        AND column_name IN('supported_efforts','catalog_refresh_epoch','entrypoint_sha256')`, [rollbackSchema])).rowCount).toBe(0)
      const constraint = (await client.query(`SELECT pg_get_constraintdef(c.oid) AS definition FROM pg_constraint c
        JOIN pg_class r ON r.oid=c.conrelid JOIN pg_namespace n ON n.oid=r.relnamespace
        WHERE n.nspname=$1 AND c.conname='ai_custom_configuration_roles_effort_check'`, [rollbackSchema])).rows[0].definition
      expect(constraint).toContain('low')
      expect(constraint).not.toContain('{0,31}')
    } finally { await client.query('ROLLBACK'); client.release() }
  })

  it('rejects malformed effort arrays and default values outside the advertised set', async () => {
    const invalidArrays: unknown[][] = [['low,high'], ['LOW'], [''], [null], ['1high'], ['a'.repeat(33)]]
    for (const efforts of invalidArrays) {
      await expect(pool.query(`UPDATE ai_cli_models SET supported_efforts=$1::text[] WHERE cli_id='codex'`, [efforts]))
        .rejects.toMatchObject({ code: '23514' })
      await expect(pool.query('UPDATE ai_connection_models SET supported_efforts=$1::text[] WHERE connection_id=$2', [efforts, connectionId]))
        .rejects.toMatchObject({ code: '23514' })
    }
    await expect(pool.query(`UPDATE ai_cli_models SET supported_efforts=ARRAY['low','high'],default_effort='ultra'
      WHERE cli_id='codex'`)).rejects.toMatchObject({ code: '23514' })
    await pool.query(`UPDATE ai_cli_models SET supported_efforts=ARRAY['xhigh','ultra'],default_effort='ultra' WHERE cli_id='codex'`)
    await pool.query('UPDATE ai_connection_models SET supported_efforts=ARRAY[\'high\',\'max\'] WHERE connection_id=$1', [connectionId])
    await expect(pool.query("UPDATE ai_custom_configuration_roles SET effort='low,high' WHERE configuration_id=$1", [configurationId]))
      .rejects.toMatchObject({ code: '23514' })
    const client = await pool.connect()
    try {
      await client.query('BEGIN')
      expect((await client.query("UPDATE ai_custom_configuration_roles SET effort='ultra' WHERE configuration_id=$1 RETURNING effort", [configurationId])).rows)
        .toEqual(AI_ROLES.map(() => ({ effort: 'ultra' })))
    } finally { await client.query('ROLLBACK'); client.release() }
  })

  it('fences API discovery by owner, epoch, credential version, TTL, and cooldown', async () => {
    await expect(repo.claimConnectionCatalogRefresh(other, connectionId, true)).rejects.toBeDefined()
    const first = (await repo.claimConnectionCatalogRefresh(user, connectionId, false))!
    expect(first).toMatchObject({ credentialVersion: 1, providerId: 'openai' })
    expect(await repo.claimConnectionCatalogRefresh(user, connectionId, true)).toBeNull()
    await ageApiAttempt(connectionId)
    const second = (await repo.claimConnectionCatalogRefresh(user, connectionId, true))!
    expect(second.epoch).not.toBe(first.epoch)
    expect(await repo.storeConnectionCatalogRefresh(user, connectionId, { credentialVersion: first.credentialVersion,
      epoch: first.epoch, models: [model] })).toBe(false)
    const unprobed = { ...model, modelId: 'new-discovery', displayName: 'New Discovery', supportedEfforts: [] }
    expect(await repo.storeConnectionCatalogRefresh(user, connectionId, { credentialVersion: second.credentialVersion,
      epoch: second.epoch, models: [model, unprobed] })).toBe(true)
    expect((await protectedState() as { roles: unknown; defaults: unknown }).roles)
      .toEqual((beforeMigration as { roles: unknown }).roles)
    expect((await protectedState() as { defaults: unknown }).defaults)
      .toEqual((beforeMigration as { defaults: unknown }).defaults)
    const rows = (await pool.query(`SELECT model_id,user_selected,plain_tested_at,tested_credential_version,
      last_probe_input_tokens,last_probe_output_tokens,supported_efforts FROM ai_connection_models WHERE connection_id=$1
      ORDER BY model_id`, [connectionId])).rows
    expect(rows.find(row => row.model_id === model.modelId)).toMatchObject({ user_selected: true,
      tested_credential_version: '1', last_probe_input_tokens: '11', last_probe_output_tokens: '7', supported_efforts: model.supportedEfforts })
    expect(rows.find(row => row.model_id === 'new-discovery')).toMatchObject({ user_selected: false, plain_tested_at: null,
      tested_credential_version: null, last_probe_input_tokens: null, last_probe_output_tokens: null })
    await ageApiAttempt(connectionId)
    expect(await repo.claimConnectionCatalogRefresh(user, connectionId, false)).toBeNull()
    const forced = (await repo.claimConnectionCatalogRefresh(user, connectionId, true))!
    expect(forced).toBeTruthy()
    expect(await repo.storeConnectionCatalogRefresh(user, connectionId, { credentialVersion: forced.credentialVersion,
      epoch: forced.epoch, errorCode: 'AI_PROVIDER_UNREACHABLE' })).toBe(true)
    expect((await pool.query('SELECT available FROM ai_connection_models WHERE connection_id=$1', [connectionId])).rows)
      .toEqual([{ available: true }, { available: true }])
    expect((await pool.query('SELECT catalog_error_code,catalog_refresh_in_progress FROM ai_provider_connections WHERE id=$1', [connectionId])).rows[0])
      .toMatchObject({ catalog_error_code: 'AI_PROVIDER_UNREACHABLE', catalog_refresh_in_progress: false })
  })

  it('rejects discovery completion after credential replacement or account disablement', async () => {
    const id = (await repo.createConnection(user, { providerId: 'anthropic', name: 'Version fence' }, encrypted())).id
    await repo.storeConnectionValidation(user, id, { credentialVersion: 1, state: 'validated', models: [model] })
    const old = (await repo.claimConnectionCatalogRefresh(user, id, true))!
    await repo.replaceConnectionCredential(user, id, encrypted())
    expect(await repo.storeConnectionCatalogRefresh(user, id, { credentialVersion: old.credentialVersion, epoch: old.epoch,
      models: [{ ...model, modelId: 'stale-replacement' }] })).toBe(false)
    expect((await pool.query("SELECT model_id FROM ai_connection_models WHERE connection_id=$1 AND model_id='stale-replacement'", [id])).rowCount).toBe(0)
    await repo.storeConnectionValidation(user, id, { credentialVersion: 2, state: 'validated', models: [model] })
    await ageApiAttempt(id)
    const current = (await repo.claimConnectionCatalogRefresh(user, id, true))!
    await pool.query("UPDATE profiles SET status='disabled' WHERE id=$1", [user])
    try {
      expect(await repo.storeConnectionCatalogRefresh(user, id, { credentialVersion: current.credentialVersion,
        epoch: current.epoch, models: [model] })).toBe(false)
    } finally { await pool.query("UPDATE profiles SET status='active' WHERE id=$1", [user]) }
  })

  it('shares one CLI host lease across granted users and rejects stale releases and revoked grants', async () => {
    await expect(repo.claimCliCatalogRefresh(ungranted, 'codex', true)).rejects.toMatchObject({ code: 'AI_CLI_NOT_GRANTED' })
    await repo.setCliGrant(admin, user, 'codex', true)
    await repo.setCliGrant(admin, other, 'codex', true)
    const first = await repo.claimCliCatalogRefresh(user, 'codex', false)
    expect(first).toBeTruthy()
    expect(await repo.claimCliCatalogRefresh(other, 'codex', true)).toBeNull()
    await ageCliAttempt()
    const successor = (await repo.claimCliCatalogRefresh(other, 'codex', true))!
    expect(successor).not.toBe(first)
    expect(await repo.finishCliCatalogRefresh('codex', first!, 'AI_CLI_UNREACHABLE')).toBe(false)
    expect(await repo.finishCliCatalogRefresh('codex', successor)).toBe(true)
    expect(await repo.finishCliCatalogRefresh('codex', successor)).toBe(false)
    await pool.query("UPDATE ai_cli_installations SET catalog_refreshed_at=clock_timestamp() WHERE cli_id='codex'")
    await ageCliAttempt()
    expect(await repo.claimCliCatalogRefresh(user, 'codex', false)).toBeNull()
    const forced = (await repo.claimCliCatalogRefresh(user, 'codex', true))!
    expect(forced).toBeTruthy()
    expect(await repo.finishCliCatalogRefresh('codex', forced, 'AI_CLI_UNREACHABLE')).toBe(true)
    expect((await pool.query("SELECT catalog_error_code,catalog_refresh_in_progress FROM ai_cli_installations WHERE cli_id='codex'")).rows[0])
      .toMatchObject({ catalog_error_code: 'AI_CLI_UNREACHABLE', catalog_refresh_in_progress: false })
    await repo.setCliGrant(admin, other, 'codex', false)
    await expect(repo.claimCliCatalogRefresh(other, 'codex', true)).rejects.toMatchObject({ code: 'AI_CLI_NOT_GRANTED' })
    await expect(repo.claimCliCatalogRefresh(ungranted, 'codex', true)).rejects.toMatchObject({ code: 'AI_CLI_NOT_GRANTED' })
  })

  it('stores CLI effort metadata separately from exact-binary generation evidence', async () => {
    const attempt = await repo.markCliValidationStarted('codex')
    const modelWrite = { modelId: model.modelId, displayName: model.displayName, compatibleRoles: [...AI_ROLES],
      supportsTools: false, supportsStructuredOutput: true, isBuiltinDefault: false,
      supportedEfforts: ['high', 'ultra'], defaultEffort: 'high', isCatalogDiscovered: true }
    expect(await repo.storeCliValidation('codex', { state: 'reachable', detectedProduct: 'Codex CLI',
      detectedVersion: '1.2.3', entrypointSha256: sha, models: [modelWrite] }, attempt.epoch)).toBeTruthy()
    const metadata = (await pool.query("SELECT is_manual,is_catalog_discovered,supported_efforts,default_effort FROM ai_cli_models WHERE cli_id='codex' AND model_id=$1", [model.modelId])).rows[0]
    expect(metadata).toEqual({ is_manual: false, is_catalog_discovered: true, supported_efforts: ['high', 'ultra'], default_effort: 'high' })
    await repo.storeManualCliModel(user, 'codex', model.modelId, '1.2.3', sha)
    expect(await repo.listConfirmedManualCliModels('codex', '1.2.3', sha)).toContain(model.modelId)
    expect(await repo.listConfirmedManualCliModels('codex', '1.2.4', sha)).not.toContain(model.modelId)
    expect(await repo.listConfirmedManualCliModels('codex', '1.2.3', 'b'.repeat(64))).not.toContain(model.modelId)
    const latest = await repo.markCliValidationStarted('codex')
    expect(await repo.storeCliValidation('codex', { state: 'reachable', detectedProduct: 'Codex CLI',
      detectedVersion: '1.2.3', entrypointSha256: sha, models: [modelWrite] }, latest.epoch)).toBeTruthy()
    expect((await pool.query("SELECT is_manual,tested_version,tested_entrypoint_sha256 FROM ai_cli_models WHERE cli_id='codex' AND model_id=$1", [model.modelId])).rows[0])
      .toMatchObject({ is_manual: true, tested_version: '1.2.3', tested_entrypoint_sha256: sha })
    const removed = await repo.markCliValidationStarted('codex')
    await repo.storeCliValidation('codex', { state: 'reachable', detectedProduct: 'Codex CLI',
      detectedVersion: '1.2.3', entrypointSha256: sha, models: [] }, removed.epoch)
    expect((await pool.query(`SELECT available,is_manual,is_catalog_discovered,supported_efforts,default_effort,
      tested_version,tested_entrypoint_sha256 FROM ai_cli_models WHERE cli_id='codex' AND model_id=$1`, [model.modelId])).rows[0])
      .toEqual({ available: true, is_manual: true, is_catalog_discovered: false, supported_efforts: [], default_effort: null,
        tested_version: '1.2.3', tested_entrypoint_sha256: sha })
    const manualRoles = Object.fromEntries(AI_ROLES.map(role => [role,
      { kind: 'local_cli', cliId: 'codex', modelId: model.modelId, effort: 'high' }]))
    await expect(repo.saveConfiguration(user, { name: 'Unsupported manual effort', roles: manualRoles }))
      .rejects.toMatchObject({ code: 'AI_ROLE_INCOMPATIBLE' })
    const defaultRoles = Object.fromEntries(AI_ROLES.map(role => [role,
      { kind: 'local_cli', cliId: 'codex', modelId: model.modelId }]))
    await expect(repo.saveConfiguration(user, { name: 'Manual model default', roles: defaultRoles }))
      .resolves.toMatchObject({ name: 'Manual model default' })
  })
})

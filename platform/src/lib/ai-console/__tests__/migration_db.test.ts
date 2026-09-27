import { randomUUID } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { Pool, type PoolClient } from 'pg'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

// Deliberately never fall back to DATABASE_URL or the application credential pool.
const databaseUrl = process.env.AI_CONSOLE_TEST_DATABASE_URL
const enabled = process.env.RUN_DB_TESTS === '1' && !!databaseUrl
const roles = ['synthesizer', 'planner', 'deep_planner', 'worker']
if (!enabled) console.info('UNQUALIFIED: RUN_DB_TESTS=1 and AI_CONSOLE_TEST_DATABASE_URL (localhost ai_console_test_* disposable database) are required')

describe.skipIf(!enabled).sequential('AI Console migration database behavior', () => {
  let pool: Pool
  const user = `ai-test-${randomUUID()}`
  const otherUser = `ai-test-${randomUUID()}`
  const connection = randomUUID()
  const conversation = randomUUID()
  const configuration = randomUUID()
  const schema = `ai_test_${randomUUID().replaceAll('-', '')}`

  async function insertSnapshot(client: Pool | PoolClient, cid: string) {
    const id = randomUUID()
    const choice = { kind: 'provider_model', connectionId: connection, modelId: 'model-a' }
    const roleMap = Object.fromEntries(roles.map(role => [role, { ...choice, providerId: 'openai' }]))
    await client.query(`INSERT INTO ai_turn_routing_snapshots(id,user_id,correlation_id,source,conversation_id,selection,resolved_choice,roles)
      VALUES($1,$2,$6,'pariprashna',$3,'{"kind":"default"}',$4,$5)`, [id, user, cid, choice, roleMap, id])
    return id
  }

  // Both writes finish (and hold their FK KEY SHARE locks) before either commit starts.
  async function concurrentCommits(work: (client: PoolClient, index: number) => Promise<unknown>) {
    const clients = await Promise.all([pool.connect(), pool.connect()])
    try {
      await Promise.all(clients.map(client => client.query("BEGIN; SET LOCAL lock_timeout='3s'")))
      await Promise.all(clients.map(work))
      const commits = await Promise.allSettled(clients.map(client => client.query('COMMIT')))
      for (const result of commits) if (result.status === 'rejected') throw result.reason
    } finally {
      await Promise.all(clients.map(client => client.query('ROLLBACK')))
      clients.forEach(client => client.release())
    }
  }

  async function transaction<T>(work: (client: PoolClient) => Promise<T>) {
    const client = await pool.connect()
    try {
      await client.query('BEGIN')
      const result = await work(client)
      await client.query('COMMIT')
      return result
    } catch (error) {
      await client.query('ROLLBACK')
      throw error
    } finally { client.release() }
  }

  async function createConfiguration(id: string, name: string, complete = true) {
    return transaction(async client => {
      await client.query('INSERT INTO ai_custom_configurations(id,user_id,name) VALUES($1,$2,$3)', [id, user, name])
      for (const role of complete ? roles : roles.slice(0, 3)) {
        await client.query(`INSERT INTO ai_custom_configuration_roles(configuration_id,user_id,role,kind,connection_id,model_id)
          VALUES($1,$2,$3,'provider_model',$4,'model-a')`, [id, user, role, connection])
      }
    })
  }

  beforeAll(async () => {
    const url = new URL(databaseUrl!)
    if (!['localhost', '127.0.0.1', '[::1]'].includes(url.hostname)
      || !url.pathname.slice(1).startsWith('ai_console_test_')) {
      throw new Error('AI_CONSOLE_TEST_DATABASE_URL must identify a localhost ai_console_test_* disposable database')
    }
    pool = new Pool({ connectionString: databaseUrl, options: `-c search_path=${schema},public`, max: 4 })
    await pool.query(`CREATE SCHEMA ${schema}`)
    await pool.query(`CREATE TABLE profiles(id text PRIMARY KEY);
      CREATE TABLE charts(id uuid PRIMARY KEY);
      CREATE TABLE conversations(id uuid PRIMARY KEY, user_id text NOT NULL REFERENCES profiles(id), chart_id uuid REFERENCES charts(id) ON DELETE CASCADE);
      CREATE TABLE _migrations_applied(filename text PRIMARY KEY);`)
    const sql = readFileSync(resolve(__dirname, '../../../../migrations/1120_ai_console_byok_routing.sql'), 'utf8')
    // Model the canonical runner: DDL and tracking must roll back as one transaction.
    await expect(transaction(async client => {
      await client.query(sql)
      await client.query("INSERT INTO _migrations_applied VALUES ('1120')")
      throw new Error('simulated failure before runner commit')
    })).rejects.toThrow('simulated failure before runner commit')
    expect((await pool.query('SELECT * FROM _migrations_applied')).rowCount).toBe(0)
    expect((await pool.query('SELECT count(*)::int AS n FROM pg_tables WHERE schemaname=$1 AND tablename LIKE $2', [schema, 'ai_%'])).rows[0].n).toBe(0)
    await transaction(async client => {
      await client.query(sql)
      await client.query("INSERT INTO _migrations_applied VALUES ('1120')")
    })
    await transaction(client => client.query(sql))
    await pool.query('INSERT INTO profiles(id) VALUES($1),($2)', [user, otherUser])
    await pool.query('INSERT INTO conversations(id,user_id) VALUES($1,$2)', [conversation, user])
    await pool.query(`INSERT INTO ai_provider_connections
      (id,user_id,provider_id,name,credential_ciphertext,credential_nonce,credential_tag,wrapped_dek,wrap_nonce,wrap_tag,kek_version,masked_suffix,keyed_fingerprint)
      VALUES($1,$2,'openai','Primary',decode('01','hex'),decode(repeat('01',12),'hex'),decode(repeat('01',16),'hex'),
        decode('01','hex'),decode(repeat('01',12),'hex'),decode(repeat('01',16),'hex'),'test','0000','test-fingerprint')`, [connection, user])
    await pool.query(`INSERT INTO ai_connection_models(connection_id,model_id,display_name,compatible_roles)
      VALUES($1,'model-a','Model A',$2)`, [connection, roles])
    await createConfiguration(configuration, 'Complete')
  })

  afterAll(async () => {
    if (pool) {
      // Only the unique schema created by this test is removed, never public.
      await pool.query(`DROP SCHEMA IF EXISTS ${schema} CASCADE`)
      await pool.end()
    }
  })

  it('replays safely and enables RLS on exactly twelve tables', async () => {
    const result = await pool.query(`SELECT count(*)::int AS count FROM pg_tables WHERE schemaname=$1 AND tablename LIKE 'ai_%' AND rowsecurity`, [schema])
    expect(result.rows[0].count).toBe(12)
    expect((await pool.query('SELECT * FROM ai_user_defaults')).rowCount).toBe(0)
  })
  it('replays the legacy call-log shape constraint and enforces both row variants', async context => {
    const legacy = await pool.query("SELECT to_regclass('public.llm_call_log') AS call_log, to_regclass('public.llm_usage_events') AS usage")
    if (!legacy.rows[0].call_log || !legacy.rows[0].usage) {
      context.skip()
      return
    }
    const constraints = await pool.query(`SELECT pg_get_constraintdef(oid) AS definition
      FROM pg_constraint WHERE conrelid='public.llm_call_log'::regclass
        AND conname='llm_call_log_model_provider_shape_check'`)
    expect(constraints.rowCount).toBe(1)
    expect(constraints.rows[0].definition).toContain('external_synthesis_handoff')
    const marker = randomUUID()
    const regular = randomUUID()
    try {
      await pool.query(`INSERT INTO public.llm_call_log(query_id,call_stage,model_id,provider)
        VALUES($1,'external_synthesis_handoff',NULL,NULL)`, [marker])
      await pool.query(`INSERT INTO public.llm_call_log(query_id,call_stage,model_id,provider)
        VALUES($1,'planner','model-a','openai')`, [regular])
      await expect(pool.query(`INSERT INTO public.llm_call_log(query_id,call_stage,model_id,provider)
        VALUES($1,'planner',NULL,NULL)`, [randomUUID()])).rejects.toMatchObject({ code: '23514' })
      await expect(pool.query(`INSERT INTO public.llm_call_log(query_id,call_stage,model_id,provider)
        VALUES($1,'external_synthesis_handoff','model-a','openai')`, [randomUUID()]))
        .rejects.toMatchObject({ code: '23514' })
      expect((await pool.query(`SELECT is_nullable FROM information_schema.columns
        WHERE table_schema='public' AND table_name='llm_usage_events' AND column_name='conversation_id'`))
        .rows[0].is_nullable).toBe('YES')
    } finally {
      await pool.query('DELETE FROM public.llm_call_log WHERE query_id=ANY($1::uuid[])', [[marker, regular]])
    }
  })
  it('accepts every usage vocabulary value and rejects values outside each named CHECK', async context => {
    const usage = await pool.query("SELECT to_regclass('public.llm_usage_events') AS relation")
    if (!usage.rows[0].relation) {
      context.skip()
      return
    }
    const providers = ['anthropic', 'openai', 'gemini', 'deepseek', 'nim', 'xai', 'kimi', 'openrouter', 'cli']
    const stages = ['classify', 'compose', 'retrieve', 'synthesize', 'synthesizer', 'audit', 'other',
      'planner', 'deep_planner', 'worker', 'title', 'history_summary', 'interpretation_sets']
    const statuses = ['success', 'error', 'timeout', 'cancelled']
    const promptIds: string[] = []
    const insert = async (provider: string, stage: string, status: string) => {
      const promptId = `ai-console-vocabulary-${randomUUID()}`
      promptIds.push(promptId)
      return pool.query(`INSERT INTO public.llm_usage_events
        (conversation_id,prompt_id,user_id,provider,model,pipeline_stage,status,started_at)
        VALUES(NULL,$1,$2,$3,'model-a',$4,$5,now())`, [promptId, user, provider, stage, status])
    }
    try {
      for (const provider of providers) await expect(insert(provider, 'other', 'success')).resolves.toBeDefined()
      for (const stage of stages) await expect(insert('openai', stage, 'success')).resolves.toBeDefined()
      for (const status of statuses) await expect(insert('openai', 'other', status)).resolves.toBeDefined()
      await expect(insert('unknown-provider', 'other', 'success')).rejects.toMatchObject({ code: '23514' })
      await expect(insert('openai', 'unknown-stage', 'success')).rejects.toMatchObject({ code: '23514' })
      await expect(insert('openai', 'other', 'unknown-status')).rejects.toMatchObject({ code: '23514' })
    } finally {
      await pool.query('DELETE FROM public.llm_usage_events WHERE prompt_id=ANY($1::text[])', [promptIds])
    }
  })
  it('rejects duplicate case-insensitive connection/configuration names', async () => {
    await expect(pool.query('UPDATE ai_provider_connections SET name=$1 WHERE id=$2', ['PRIMARY', connection])).resolves.toBeDefined()
    await expect(pool.query(`INSERT INTO ai_provider_connections SELECT $1,user_id,provider_id,name,
      credential_ciphertext,credential_nonce,credential_tag,wrapped_dek,wrap_nonce,wrap_tag,kek_version,
      masked_suffix,keyed_fingerprint,credential_version,credential_validity,validation_state,last_validated_at,
      last_checked_at,last_error_code,created_at,updated_at,deleted_at FROM ai_provider_connections WHERE id=$2`, [randomUUID(), connection])).rejects.toMatchObject({ code: '23505' })
    await expect(createConfiguration(randomUUID(), 'COMPLETE')).rejects.toMatchObject({ code: '23505' })
  })
  it('rejects missing, duplicate and unknown roles at transaction boundaries', async () => {
    await expect(createConfiguration(randomUUID(), 'Incomplete', false)).rejects.toMatchObject({ code: '23514' })
    for (const role of ['unknown_role', 'worker']) {
      await expect(pool.query(`INSERT INTO ai_custom_configuration_roles(configuration_id,user_id,role,kind,connection_id,model_id)
        VALUES($1,$2,$3,'provider_model',$4,'model-a')`, [configuration, user, role, connection])).rejects.toBeDefined()
    }
    await expect(pool.query('DELETE FROM ai_custom_configuration_roles WHERE configuration_id=$1 AND role=$2', [configuration, 'worker'])).rejects.toMatchObject({ code: '23514' })
  })
  it('enforces owner matching in both directions and exact choice variants', async () => {
    await expect(pool.query(`INSERT INTO ai_conversation_selections(conversation_id,user_id,kind) VALUES($1,$2,'default')`, [conversation, otherUser])).rejects.toMatchObject({ code: '23514' })
    await pool.query(`INSERT INTO ai_conversation_selections(conversation_id,user_id,kind) VALUES($1,$2,'default')`, [conversation, user])
    await expect(pool.query('UPDATE conversations SET user_id=$1 WHERE id=$2', [otherUser, conversation])).rejects.toMatchObject({ code: '23514' })
    await expect(pool.query(`INSERT INTO ai_user_defaults(user_id,kind,connection_id,model_id) VALUES($1,'provider_model',$2,'model-a')`, [otherUser, connection])).rejects.toMatchObject({ code: '23503' })
    await expect(pool.query(`INSERT INTO ai_user_defaults(user_id,kind) VALUES($1,'provider_model')`, [user])).rejects.toMatchObject({ code: '23514' })
  })
  it('atomically replaces a single explicit default under concurrent writes', async () => {
    const replace = (custom: boolean) => pool.query(`INSERT INTO ai_user_defaults(user_id,kind,connection_id,model_id,configuration_id)
      VALUES($1,$2,$3,$4,$5) ON CONFLICT(user_id) DO UPDATE SET
      kind=excluded.kind,connection_id=excluded.connection_id,model_id=excluded.model_id,
      configuration_id=excluded.configuration_id,updated_at=now()`,
    [user, custom ? 'custom_configuration' : 'provider_model', custom ? null : connection, custom ? null : 'model-a', custom ? configuration : null])
    await Promise.all([replace(false), replace(true)])
    const defaults = await pool.query('SELECT kind,connection_id,model_id,configuration_id FROM ai_user_defaults WHERE user_id=$1', [user])
    expect(defaults.rowCount).toBe(1)
    expect([
      { kind: 'provider_model', connection_id: connection, model_id: 'model-a', configuration_id: null },
      { kind: 'custom_configuration', connection_id: null, model_id: null, configuration_id: configuration },
    ]).toContainEqual(defaults.rows[0])
    await replace(false)
    await expect(pool.query(`INSERT INTO ai_user_defaults(user_id,kind,connection_id,model_id) VALUES($1,'provider_model',$2,'model-a')`, [user, connection])).rejects.toMatchObject({ code: '23505' })
  })
  it('serializes optimistic configuration updates and rejects unversioned edits', async () => {
    const update = () => pool.query(`UPDATE ai_custom_configurations SET name='Revised',version=version+1 WHERE id=$1 AND version=1 RETURNING version`, [configuration])
    const updates = await Promise.all([update(), update()])
    expect(updates.reduce((sum, result) => sum + result.rowCount!, 0)).toBe(1)
    await expect(pool.query("UPDATE ai_custom_configurations SET name='Unversioned' WHERE id=$1", [configuration])).rejects.toMatchObject({ code: '23514' })
  })
  it('preserves validation evidence across a transient reachability failure', async () => {
    await pool.query(`UPDATE ai_provider_connections SET credential_validity='valid',last_validated_at=now(),validation_state='validated' WHERE id=$1`, [connection])
    await pool.query(`UPDATE ai_provider_connections SET validation_state='unreachable',last_checked_at=now() WHERE id=$1`, [connection])
    expect((await pool.query('SELECT credential_validity,last_validated_at,validation_state FROM ai_provider_connections WHERE id=$1', [connection])).rows[0]).toMatchObject({ credential_validity: 'valid', last_validated_at: expect.any(Date), validation_state: 'unreachable' })
  })
  it('deduplicates immutable snapshots and appends ordered per-role receipts without updates', async () => {
    const id = randomUUID()
    const target = { kind: 'provider_model', connectionId: connection, modelId: 'model-a', providerId: 'openai' }
    const choice = { kind: 'provider_model', connectionId: connection, modelId: 'model-a' }
    const roleMap = Object.fromEntries(roles.map(role => [role, target]))
    const insert = () => pool.query(`INSERT INTO ai_turn_routing_snapshots(id,user_id,correlation_id,source,conversation_id,selection,resolved_choice,roles)
      VALUES($1,$2,'turn-one','pariprashna',$3,'{"kind":"default"}',$4,$5) ON CONFLICT(user_id,correlation_id) DO NOTHING`, [id, user, conversation, choice, roleMap])
    const inserts = await Promise.all([insert(), insert()])
    expect(inserts.reduce((sum, result) => sum + result.rowCount!, 0)).toBe(1)
    await expect(pool.query(`INSERT INTO ai_turn_routing_snapshots(user_id,correlation_id,source,selection,resolved_choice,roles)
      VALUES($1,'unsafe-extra','backend','{"kind":"default"}',$2,$3)`,
    [user, choice, { ...roleMap, planner: { ...target, unexpectedField: 'rejected' } }])).rejects.toMatchObject({ code: '23514' })
    await expect(pool.query(`INSERT INTO ai_turn_routing_snapshots(user_id,correlation_id,source,selection,resolved_choice,roles)
      VALUES($1,'cross-user','backend','{"kind":"default"}',$2,$3)`,
    [otherUser, choice, roleMap])).rejects.toMatchObject({ code: '23503' })
    await expect(pool.query("UPDATE ai_turn_routing_snapshots SET correlation_id='changed' WHERE id=$1", [id])).rejects.toMatchObject({ code: '23514' })
    const invocation = randomUUID()
    const secondInvocation = randomUUID()
    await expect(pool.query("INSERT INTO ai_turn_role_invocations(snapshot_id,role,invocation_id,phase,status) VALUES($1,'planner',$2,'terminal','succeeded')", [id, invocation])).rejects.toMatchObject({ code: '23503' })
    await pool.query("INSERT INTO ai_turn_role_invocations(snapshot_id,role,invocation_id,phase,status) VALUES($1,'planner',$2,'start','started')", [id, invocation])
    await pool.query("INSERT INTO ai_turn_role_invocations(snapshot_id,role,invocation_id,phase,status) VALUES($1,'planner',$2,'terminal','succeeded')", [id, invocation])
    await pool.query("INSERT INTO ai_turn_role_invocations(snapshot_id,role,invocation_id,phase,status) VALUES($1,'planner',$2,'start','started'),($1,'planner',$2,'terminal','succeeded')", [id, secondInvocation])
    await expect(pool.query("UPDATE ai_turn_role_invocations SET status='failed' WHERE snapshot_id=$1 AND phase='terminal'", [id])).rejects.toMatchObject({ code: '23514' })
    await expect(pool.query("INSERT INTO ai_turn_role_invocations(snapshot_id,role,invocation_id,phase,status) VALUES($1,'planner',$2,'terminal','failed')", [id, invocation])).rejects.toMatchObject({ code: '23505' })
    await expect(pool.query('DELETE FROM ai_turn_role_invocations WHERE snapshot_id=$1', [id])).rejects.toMatchObject({ code: '23514' })
    await expect(pool.query('DELETE FROM ai_turn_routing_snapshots WHERE id=$1', [id])).rejects.toMatchObject({ code: '23514' })
  })
  it('retains broken default and history identities after tombstoning', async () => {
    await pool.query('UPDATE ai_provider_connections SET deleted_at=now() WHERE id=$1', [connection])
    expect((await pool.query('SELECT connection_id FROM ai_user_defaults WHERE user_id=$1', [user])).rows[0].connection_id).toBe(connection)
    await expect(pool.query('DELETE FROM ai_provider_connections WHERE id=$1', [connection])).rejects.toMatchObject({ code: '23503' })
    await pool.query('UPDATE ai_custom_configurations SET deleted_at=now(),version=version+1 WHERE id=$1', [configuration])
  })
  it('commits distinct correlations for the same conversation without FK lock-upgrade deadlock', async () => {
    await concurrentCommits(client => insertSnapshot(client, conversation))
    expect((await pool.query('SELECT * FROM ai_turn_routing_snapshots WHERE conversation_id=$1', [conversation])).rowCount).toBe(3)
  })
  it('commits concurrent role changes while both transactions hold parent FK key-share locks', async () => {
    await concurrentCommits(async (client, index) => {
      await client.query('SELECT id FROM ai_custom_configurations WHERE id=$1 FOR KEY SHARE', [configuration])
      await client.query('UPDATE ai_custom_configuration_roles SET model_id=$1 WHERE configuration_id=$2 AND role=$3', ['model-a', configuration, roles[index]])
    })
    expect((await pool.query('SELECT * FROM ai_custom_configuration_roles WHERE configuration_id=$1', [configuration])).rowCount).toBe(4)
  })
  it('rejects direct DELETE, UPDATE and TRUNCATE on every history table', async () => {
    await pool.query("INSERT INTO ai_configuration_audit_log(user_id,actor_user_id,event) VALUES($1,$1,'default_selected')", [user])
    for (const table of ['ai_turn_routing_snapshots', 'ai_turn_role_invocations', 'ai_configuration_audit_log']) {
      await expect(pool.query(`DELETE FROM ${table}`)).rejects.toMatchObject({ code: '23514' })
      await expect(pool.query(`UPDATE ${table} SET created_at=now()`)).rejects.toMatchObject({ code: '23514' })
      await expect(pool.query(`TRUNCATE ${table} CASCADE`)).rejects.toMatchObject({ code: '23514' })
    }
    const truncateGrants = await pool.query(`SELECT c.relname FROM pg_class c
      JOIN pg_namespace n ON n.oid=c.relnamespace
      CROSS JOIN LATERAL aclexplode(COALESCE(c.relacl,acldefault('r',c.relowner))) acl
      JOIN pg_roles r ON r.oid=acl.grantee
      WHERE n.nspname=$1 AND c.relname=ANY($2::text[])
        AND r.rolname='service_role' AND r.oid<>c.relowner AND acl.privilege_type='TRUNCATE'`,
    [schema, ['ai_turn_routing_snapshots', 'ai_turn_role_invocations', 'ai_configuration_audit_log']])
    expect(truncateGrants.rowCount).toBe(0)
  })
  it('erases only dependent selection, snapshots and receipts on conversation or chart deletion', async () => {
    for (const throughChart of [false, true]) {
      const chart = randomUUID()
      const cid = randomUUID()
      await pool.query('INSERT INTO charts(id) VALUES($1)', [chart])
      await pool.query('INSERT INTO conversations(id,user_id,chart_id) VALUES($1,$2,$3)', [cid, user, chart])
      await pool.query("INSERT INTO ai_conversation_selections(conversation_id,user_id,kind) VALUES($1,$2,'default')", [cid, user])
      const snapshot = await insertSnapshot(pool, cid)
      const invocation = randomUUID()
      await pool.query("INSERT INTO ai_turn_role_invocations(snapshot_id,role,invocation_id,phase,status) VALUES($1,'worker',$2,'start','started'),($1,'worker',$2,'terminal','succeeded')", [snapshot, invocation])
      await pool.query(throughChart ? 'DELETE FROM charts WHERE id=$1' : 'DELETE FROM conversations WHERE id=$1', [throughChart ? chart : cid])
      expect((await pool.query('SELECT * FROM ai_conversation_selections WHERE conversation_id=$1', [cid])).rowCount).toBe(0)
      expect((await pool.query('SELECT * FROM ai_turn_routing_snapshots WHERE id=$1', [snapshot])).rowCount).toBe(0)
      expect((await pool.query('SELECT * FROM ai_turn_role_invocations WHERE snapshot_id=$1', [snapshot])).rowCount).toBe(0)
      expect((await pool.query('SELECT * FROM ai_turn_routing_snapshots WHERE conversation_id=$1', [conversation])).rowCount).toBe(3)
      expect((await pool.query('SELECT * FROM ai_configuration_audit_log WHERE user_id=$1', [user])).rowCount).toBe(1)
    }
  })
})

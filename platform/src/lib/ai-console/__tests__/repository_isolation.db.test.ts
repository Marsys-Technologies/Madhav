import { randomBytes, randomUUID } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { Pool, type PoolClient } from 'pg'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import * as repo from '../repository'
import { AI_ROLES, type RoleAssignments } from '../types'

// Never use DATABASE_URL, dotenv, an application pool, or a shared host.
const databaseUrl = process.env.AI_CONSOLE_TEST_DATABASE_URL
const enabled = process.env.RUN_DB_TESTS === '1' && !!databaseUrl
if (!enabled) console.info('UNQUALIFIED: repository DB behavior requires RUN_DB_TESTS=1 and AI_CONSOLE_TEST_DATABASE_URL (localhost ai_console_test_* disposable database)')

describe.skipIf(!enabled).sequential('AI Console real repository isolation', () => {
  const schema = `ai_repo_${randomUUID().replaceAll('-', '')}`
  const user = 'repository-alice'
  const other = 'repository-bob'
  const admin = 'repository-admin'
  const conversation = randomUUID()
  const chart = randomUUID()
  const encrypted = () => ({ ciphertext: randomBytes(24), nonce: randomBytes(12), authTag: randomBytes(16),
    wrappedDataKey: randomBytes(32), wrapNonce: randomBytes(12), wrapAuthTag: randomBytes(16),
    keyVersion: 'test', mask: '••••1234', fingerprint: randomBytes(32).toString('hex') })
  let pool: Pool
  const poolGlobal = globalThis as typeof globalThis & { __pgPool?: Pool }
  let previousPool: Pool | undefined
  let connectionId: string
  let configurationId: string
  const choice = () => ({ kind: 'provider_model' as const, connectionId, modelId: 'model-a' })
  const roles = () => Object.fromEntries(AI_ROLES.map(role => [role, choice()])) as RoleAssignments
  const snapshot = (correlationId: string) => ({ userId: user, correlationId, source: 'pariprashna', conversationId: conversation,
    selection: { kind: 'default' }, resolvedChoice: choice(), configurationVersion: null,
    roles: Object.fromEntries(AI_ROLES.map(role => [role, { ...choice(), providerId: 'openai' }])) })

  /** Real, distinct clients; pause COMMIT after all first-operation locks are held. */
  async function blockedUntilCommit(first: () => Promise<unknown>, second: () => Promise<unknown>) {
    const clients = await Promise.all([pool.connect(), pool.connect(), pool.connect()])
    const [firstClient, secondClient, observer] = clients
    let releaseCommit!: () => void
    const allowCommit = new Promise<void>(resolve => { releaseCommit = resolve })
    let reachedCommit!: () => void
    const atCommit = new Promise<void>(resolve => { reachedCommit = resolve })
    let failFirst!: (error: unknown) => void
    const firstFailure = new Promise<never>((_, reject) => { failFirst = reject })
    let nextClient = 0
    const proxy = (client: PoolClient, pause: boolean) => ({
      query: async (sql: string, params?: unknown[]) => {
        if (pause && sql === 'COMMIT') { reachedCommit(); await allowCommit }
        return client.query(sql, params)
      },
      release() {}, // Real clients are released by this test helper's finally.
    })
    const owner = poolGlobal.__pgPool
    poolGlobal.__pgPool = {
      connect: async () => {
        if (nextClient >= 2) throw new Error('Unexpected third transaction in two-client test')
        return proxy(clients[nextClient], nextClient++ === 0)
      },
    } as unknown as Pool
    let firstResult: Promise<unknown> | undefined
    let secondResult: Promise<unknown> | undefined
    try {
      const firstPid = (await firstClient.query('SELECT pg_backend_pid() AS pid')).rows[0].pid as number
      const secondPid = (await secondClient.query('SELECT pg_backend_pid() AS pid')).rows[0].pid as number
      firstResult = first()
      void firstResult.catch(failFirst)
      await Promise.race([atCommit, firstFailure])
      let secondSettled = false
      secondResult = second()
      void secondResult.then(() => { secondSettled = true }, () => { secondSettled = true })
      const deadline = Date.now() + 3000
      let blockers: number[] = []
      while (Date.now() < deadline) {
        blockers = (await observer.query('SELECT pg_blocking_pids($1::int) AS blockers', [secondPid])).rows[0].blockers
        if (blockers.includes(firstPid)) break
        if (secondSettled) break
        await new Promise(resolve => setTimeout(resolve, 5))
      }
      expect(blockers).toContain(firstPid)
      expect(secondSettled).toBe(false)
      releaseCommit()
      await Promise.all([firstResult, secondResult])
      expect(secondSettled).toBe(true)
    } finally {
      releaseCommit()
      await Promise.allSettled([firstResult, secondResult].filter(Boolean))
      poolGlobal.__pgPool = owner
      await Promise.all(clients.map(client => client.query('ROLLBACK')))
      clients.forEach(client => client.release())
    }
  }

  beforeAll(async () => {
    const url = new URL(databaseUrl!)
    if (!['localhost', '127.0.0.1', '[::1]'].includes(url.hostname) || !url.pathname.slice(1).startsWith('ai_console_test_')) {
      throw new Error('Only a localhost ai_console_test_* disposable database is permitted')
    }
    pool = new Pool({ connectionString: databaseUrl, options: `-c search_path=${schema},public -c statement_timeout=5000`, max: 6 })
    await pool.query(`CREATE SCHEMA ${schema}`)
    await pool.query(`CREATE TABLE profiles(id text PRIMARY KEY, status text NOT NULL DEFAULT 'active',role text NOT NULL DEFAULT 'guest');
      CREATE TABLE charts(id uuid PRIMARY KEY,owner_id text REFERENCES profiles(id));
      CREATE TABLE chart_grants(chart_id uuid REFERENCES charts(id),principal_id text REFERENCES profiles(id),permission text);
      CREATE TABLE conversations(id uuid PRIMARY KEY,user_id text NOT NULL REFERENCES profiles(id),chart_id uuid REFERENCES charts(id),module text,title text);
      CREATE TABLE admin_audit_log(actor_id text,action text,target_user_id text,detail jsonb);`)
    const migration = readFileSync(resolve(__dirname, '../../../../migrations/1120_ai_console_byok_routing.sql'), 'utf8')
    const client = await pool.connect()
    try { await client.query('BEGIN'); await client.query(migration); await client.query('COMMIT') }
    catch (error) { await client.query('ROLLBACK'); throw error }
    finally { client.release() }
    await pool.query("INSERT INTO profiles(id,role) VALUES($1,'guest'),($2,'guest'),($3,'super_admin')", [user, other, admin])
    await pool.query('INSERT INTO charts(id,owner_id) VALUES($1,$2)', [chart, user])
    await pool.query('INSERT INTO conversations(id,user_id,chart_id) VALUES($1,$2,$3)', [conversation, user, chart])
    previousPool = poolGlobal.__pgPool
    poolGlobal.__pgPool = pool
    connectionId = (await repo.createConnection(user, { providerId: 'openai', name: 'Personal' }, encrypted())).id
    await repo.storeConnectionValidation(user, connectionId, { credentialVersion: 1, state: 'validated',
      models: [{ modelId: 'model-a', displayName: 'Model A', compatibleRoles: [...AI_ROLES], supportsTools: true, supportsStructuredOutput: true }] })
    configurationId = (await repo.saveConfiguration(user, { name: 'Complete', roles: roles() })).id
  })
  afterAll(async () => {
    poolGlobal.__pgPool = previousPool
    if (pool) {
      // This is the sole schema created above; no public or application schema is removed.
      await pool.query(`DROP SCHEMA IF EXISTS ${schema} CASCADE`)
      await pool.end()
    }
  })

  it('denies foreign reads and every connection/configuration mutation', async () => {
    expect((await repo.listAiConsoleState(other)).connections).toEqual([])
    for (const action of [
      () => repo.renameConnection(other, connectionId, 'Hijacked'),
      () => repo.replaceConnectionCredential(other, connectionId, encrypted()),
      () => repo.storeConnectionValidation(other, connectionId, { credentialVersion: 1, state: 'invalid' }),
      () => repo.loadConnectionCredential(other, connectionId, 1),
      () => repo.deleteConnection(other, connectionId, true),
      () => repo.saveConfiguration(other, { id: configurationId, expectedVersion: 1, name: 'Hijacked', roles: roles() }),
      () => repo.duplicateConfiguration(other, configurationId, 'Stolen'),
      () => repo.deleteConfiguration(other, configurationId, true),
      () => repo.setUserDefault(other, choice()),
      () => repo.setConversationSelection(other, conversation, { kind: 'default' }),
      () => repo.getConversationSelection(other, conversation),
    ]) await expect(action()).rejects.toBeDefined()
    expect((await repo.previewChoiceDependencies(other, choice())).configurations).toEqual([])
  })
  it('serializes defaults and optimistic configuration edits without mixing roles', async () => {
    await Promise.all([repo.setUserDefault(user, choice()), repo.setUserDefault(user, { kind: 'custom_configuration', configurationId })])
    expect((await pool.query('SELECT * FROM ai_user_defaults WHERE user_id=$1', [user])).rowCount).toBe(1)
    const updates = await Promise.allSettled([1, 2].map(i => repo.saveConfiguration(user, {
      id: configurationId, expectedVersion: 1, name: `Edited ${i}`, roles: roles(),
    })))
    expect(updates.filter(r => r.status === 'fulfilled')).toHaveLength(1)
    expect((await pool.query('SELECT version FROM ai_custom_configurations WHERE user_id=$1 AND id=$2', [user, configurationId])).rows[0].version).toBe('2')
    expect((await pool.query('SELECT * FROM ai_custom_configuration_roles WHERE user_id=$1 AND configuration_id=$2', [user, configurationId])).rowCount).toBe(4)
  })
  it('keeps live Default symbolic and explicit choices pinned across default changes', async () => {
    await repo.setConversationSelection(user, conversation, { kind: 'default' })
    await repo.setUserDefault(user, choice())
    expect(await repo.getConversationSelection(user, conversation)).toEqual({ kind: 'default' })
    await repo.setConversationSelection(user, conversation, { kind: 'explicit', choice: choice() })
    await repo.setUserDefault(user, { kind: 'custom_configuration', configurationId })
    expect(await repo.getConversationSelection(user, conversation)).toEqual({ kind: 'explicit', choice: choice() })
  })
  it('serializes save versus select and duplicate with deterministic two-client barriers', async () => {
    const config = await repo.saveConfiguration(user, { name: 'Lock order', roles: roles() })
    await blockedUntilCommit(
      () => repo.saveConfiguration(user, { id: config.id, expectedVersion: 1, name: 'Lock order revised', roles: roles() }),
      () => repo.setUserDefault(user, { kind: 'custom_configuration', configurationId: config.id }),
    )
    await blockedUntilCommit(
      () => repo.duplicateConfiguration(user, config.id, 'Lock order duplicate'),
      () => repo.saveConfiguration(user, { id: config.id, expectedVersion: 2, name: 'Lock order final', roles: roles() }),
    )
    expect((await pool.query('SELECT version FROM ai_custom_configurations WHERE user_id=$1 AND id=$2', [user, config.id])).rows[0].version).toBe('3')
    await repo.setUserDefault(user, { kind: 'custom_configuration', configurationId })
    await repo.deleteConfiguration(user, config.id, true)
    const duplicate = (await pool.query('SELECT id FROM ai_custom_configurations WHERE user_id=$1 AND name=$2', [user, 'Lock order duplicate'])).rows[0].id
    await repo.deleteConfiguration(user, duplicate, true)
  })
  it('serializes swapped A/B role assignments independently of role order', async () => {
    const secondId = (await repo.createConnection(user, { providerId: 'openai', name: 'Second for locks' }, encrypted())).id
    await repo.storeConnectionValidation(user, secondId, { credentialVersion: 1, state: 'validated',
      models: [{ modelId: 'model-a', displayName: 'Model A', compatibleRoles: [...AI_ROLES], supportsTools: true, supportsStructuredOutput: true }] })
    const second = { ...choice(), connectionId: secondId }
    const ab = { synthesizer: choice(), planner: second, deep_planner: choice(), worker: second }
    const ba = { synthesizer: second, planner: choice(), deep_planner: second, worker: choice() }
    const one = await repo.saveConfiguration(user, { name: 'Order AB', roles: ab })
    const two = await repo.saveConfiguration(user, { name: 'Order BA', roles: ba })
    await blockedUntilCommit(
      () => repo.saveConfiguration(user, { id: one.id, expectedVersion: 1, name: 'Order AB swapped', roles: ba }),
      () => repo.saveConfiguration(user, { id: two.id, expectedVersion: 1, name: 'Order BA swapped', roles: ab }),
    )
    for (const config of [one, two]) await repo.deleteConfiguration(user, config.id, true)
  })
  it('includes absent/default selections only when their owner’s default is affected', async () => {
    const absent = randomUUID()
    const explicit = randomUUID()
    const foreign = randomUUID()
    await pool.query('INSERT INTO conversations(id,user_id) VALUES($1,$4),($2,$4),($3,$5)', [absent, explicit, foreign, user, other])
    const otherConnection = (await repo.createConnection(user, { providerId: 'openai', name: 'Independent override' }, encrypted())).id
    await repo.storeConnectionValidation(user, otherConnection, { credentialVersion: 1, state: 'validated',
      models: [{ modelId: 'model-a', displayName: 'Model A', compatibleRoles: [...AI_ROLES], supportsTools: true, supportsStructuredOutput: true }] })
    const override = { ...choice(), connectionId: otherConnection }
    await repo.setConversationSelection(user, explicit, { kind: 'explicit', choice: override })
    await repo.setUserDefault(user, choice())
    const affected = (await repo.previewChoiceDependencies(user, choice())).conversations.map(row => row.conversation_id)
    expect(affected).toContain(absent)
    expect(affected).not.toContain(explicit)
    expect(affected).not.toContain(foreign)
    await repo.setUserDefault(user, override)
    expect((await repo.previewChoiceDependencies(user, choice())).conversations.map(row => row.conversation_id)).not.toContain(absent)
    await repo.setUserDefault(user, { kind: 'custom_configuration', configurationId })
    await pool.query('DELETE FROM conversations WHERE user_id=$1 AND id=ANY($2::uuid[])', [user, [absent, explicit]])
  })
  it('deduplicates concurrent snapshots and ordered receipts, rejecting changed history', async () => {
    const ids = await Promise.all([repo.insertRoutingSnapshot(snapshot('same-turn')), repo.insertRoutingSnapshot(snapshot('same-turn'))])
    expect(ids[0]).toBe(ids[1])
    await expect(repo.insertRoutingSnapshot({ ...snapshot('same-turn'), source: 'backend' })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    const start = { userId: user, snapshotId: ids[0], invocationId: randomUUID(),
      role: 'planner', phase: 'start', status: 'started' }
    await expect(repo.insertRoleInvocationReceipt({ ...start, userId: other })).rejects.toBeDefined()
    await expect(repo.insertRoleInvocationReceipt({ ...start, phase: 'terminal', status: 'succeeded' })).rejects.toBeDefined()
    await Promise.all([repo.insertRoleInvocationReceipt(start), repo.insertRoleInvocationReceipt(start)])
    await repo.insertRoleInvocationReceipt({ ...start, phase: 'terminal', status: 'succeeded' })
    const second = { ...start, invocationId: randomUUID() }
    await repo.insertRoleInvocationReceipt(second)
    await repo.insertRoleInvocationReceipt({ ...second, phase: 'terminal', status: 'succeeded' })
    await expect(repo.insertRoleInvocationReceipt({ ...start, phase: 'terminal', status: 'failed' })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect((await pool.query('SELECT * FROM ai_turn_role_invocations WHERE snapshot_id=$1', [ids[0]])).rowCount).toBe(4)
  })
  it('atomically pins selection, resolution and snapshot against a concurrent picker update', async () => {
    await repo.setUserDefault(user, choice())
    await repo.setConversationSelection(user, conversation, { kind: 'default' })
    const correlationId = randomUUID()
    await blockedUntilCommit(
      () => repo.prepareTurnRouting({ userId: user, role: 'guest', chartId: chart,
        conversationId: conversation, isFirstTurn: false, turnId: correlationId,
        source: 'pariprashna', selection: { kind: 'default' } }),
      () => repo.setConversationSelection(user, conversation, { kind: 'explicit', choice: choice() }),
    )
    const persisted = (await pool.query(`SELECT selection,resolved_choice FROM ai_turn_routing_snapshots
      WHERE user_id=$1 AND correlation_id=$2`, [user, correlationId])).rows[0]
    expect(persisted.selection).toEqual({ kind: 'default' })
    expect(persisted.resolved_choice).toEqual(choice())
    expect(await repo.getConversationSelection(user, conversation)).toEqual({ kind: 'explicit', choice: choice() })
  })
  it('rolls back every first-turn row when exact routing cannot resolve', async () => {
    const conversationId = randomUUID()
    await expect(repo.prepareTurnRouting({ userId: user, role: 'guest', chartId: chart,
      conversationId, isFirstTurn: true, turnId: randomUUID(), source: 'consult',
      selection: { kind: 'explicit', choice: { ...choice(), modelId: 'missing-model' } } }))
      .rejects.toMatchObject({ code: 'AI_MODEL_UNAVAILABLE' })
    expect((await pool.query('SELECT id FROM conversations WHERE id=$1', [conversationId])).rowCount).toBe(0)
    expect((await pool.query('SELECT conversation_id FROM ai_conversation_selections WHERE conversation_id=$1', [conversationId])).rowCount).toBe(0)
  })
  it('pins in-flight credentials and rejects stale validation/catalog completion after replacement', async () => {
    const pinned = await repo.loadConnectionCredential(user, connectionId, 1)
    const pinnedBytes = Buffer.from(pinned.ciphertext)
    await repo.replaceConnectionCredential(user, connectionId, encrypted())
    expect(pinned.ciphertext).toEqual(pinnedBytes)
    await expect(repo.loadConnectionCredential(user, connectionId, 1)).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    await expect(repo.storeConnectionValidation(user, connectionId, { credentialVersion: 1, state: 'validated',
      models: [{ modelId: 'stale-model', displayName: 'Stale', compatibleRoles: ['worker'], supportsTools: false, supportsStructuredOutput: true }] })).rejects.toBeDefined()
    expect((await pool.query('SELECT available FROM ai_connection_models WHERE connection_id=$1', [connectionId])).rows).toEqual([{ available: false }])
    await repo.storeConnectionValidation(user, connectionId, { credentialVersion: 2, state: 'validated',
      models: [{ modelId: 'model-a', displayName: 'Model A', compatibleRoles: [...AI_ROLES], supportsTools: true, supportsStructuredOutput: true }] })
    await pool.query("UPDATE profiles SET status='disabled' WHERE id=$1", [user])
    await expect(repo.loadConnectionCredential(user, connectionId, 2)).rejects.toBeDefined()
    await pool.query("UPDATE profiles SET status='active' WHERE id=$1", [user])
  })
  it('blocks revoke-before-start and serializes concurrent revoke against immediate spawn', async () => {
    await pool.query("INSERT INTO ai_cli_installations(cli_id,validation_state) VALUES('codex','reachable')")
    await expect(repo.setCliGrant(other, user, 'codex', true)).rejects.toBeDefined()
    await repo.setCliGrant(admin, user, 'codex', true)
    await repo.setCliGrant(admin, user, 'codex', false)
    let starts = 0
    await expect(repo.withCliInvocationAuthorization(user, 'codex', () => { starts++; return { pid: 1, cancel() {} } })).rejects.toMatchObject({ code: 'AI_CLI_NOT_GRANTED' })
    expect(starts).toBe(0)
    await repo.setCliGrant(admin, user, 'codex', true)
    await blockedUntilCommit(
      () => repo.withCliInvocationAuthorization(user, 'codex', () => { starts++; return { pid: 2, cancel() {} } }),
      () => repo.setCliGrant(admin, user, 'codex', false),
    )
    await expect(repo.withCliInvocationAuthorization(user, 'codex', () => { starts++; return { pid: 3, cancel() {} } })).rejects.toBeDefined()
    expect(starts).toBe(1)
    const hidden = (await repo.listAiConsoleState(other)).clis[0]
    expect(hidden.detected_product).toBeNull()
    expect(hidden.validation_state).toBeNull()
  })
  it('preserves transitive dependencies after confirmed tombstones and records distinct safe events', async () => {
    await repo.renameConnection(user, connectionId, 'Renamed')
    await repo.duplicateConfiguration(user, configurationId, 'Copy')
    const dependencies = await repo.previewChoiceDependencies(user, choice())
    expect(dependencies.defaultAffected).toBe(true)
    expect(dependencies.configurations).toHaveLength(2)
    expect(dependencies.conversations).toEqual([{ conversation_id: conversation }])
    await expect(repo.deleteConnection(user, connectionId, false)).rejects.toBeDefined()
    await repo.deleteConnection(user, connectionId, true)
    expect((await repo.listAiConsoleState(user)).defaultChoice).toEqual({ kind: 'custom_configuration', configurationId })
    await expect(repo.setUserDefault(user, { kind: 'custom_configuration', configurationId })).rejects.toBeDefined()
    await repo.deleteConfiguration(user, configurationId, true)
    const events = (await pool.query('SELECT event FROM ai_configuration_audit_log WHERE user_id=$1', [user])).rows.map(row => row.event)
    expect(events).toEqual(expect.arrayContaining(['connection_renamed', 'connection_credential_replaced', 'configuration_duplicated']))
    const adminAudit = (await pool.query('SELECT detail FROM admin_audit_log WHERE target_user_id=$1', [user])).rows
    expect(adminAudit.every(row => JSON.stringify(row.detail) === '{"cliId":"codex"}')).toBe(true)
  })
})

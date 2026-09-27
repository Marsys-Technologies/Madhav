import { randomBytes, randomUUID } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { Pool } from 'pg'
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

  beforeAll(async () => {
    const url = new URL(databaseUrl!)
    if (!['localhost', '127.0.0.1', '[::1]'].includes(url.hostname) || !url.pathname.slice(1).startsWith('ai_console_test_')) {
      throw new Error('Only a localhost ai_console_test_* disposable database is permitted')
    }
    pool = new Pool({ connectionString: databaseUrl, options: `-c search_path=${schema},public -c statement_timeout=5000`, max: 6 })
    await pool.query(`CREATE SCHEMA ${schema}`)
    await pool.query(`CREATE TABLE profiles(id text PRIMARY KEY, status text NOT NULL DEFAULT 'active',role text NOT NULL DEFAULT 'guest');
      CREATE TABLE conversations(id uuid PRIMARY KEY,user_id text NOT NULL REFERENCES profiles(id));
      CREATE TABLE admin_audit_log(actor_id text,action text,target_user_id text,detail jsonb);`)
    const migration = readFileSync(resolve(__dirname, '../../../../migrations/1120_ai_console_byok_routing.sql'), 'utf8')
    const client = await pool.connect()
    try { await client.query('BEGIN'); await client.query(migration); await client.query('COMMIT') }
    catch (error) { await client.query('ROLLBACK'); throw error }
    finally { client.release() }
    await pool.query("INSERT INTO profiles(id,role) VALUES($1,'guest'),($2,'guest'),($3,'super_admin')", [user, other, admin])
    await pool.query('INSERT INTO conversations(id,user_id) VALUES($1,$2)', [conversation, user])
    previousPool = poolGlobal.__pgPool
    poolGlobal.__pgPool = pool
    connectionId = (await repo.createConnection(user, { providerId: 'openai', name: 'Personal' }, encrypted())).id
    await repo.storeConnectionValidation(user, connectionId, { credentialVersion: 1, state: 'validated',
      models: [{ modelId: 'model-a', displayName: 'Model A', compatibleRoles: [...AI_ROLES] }] })
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
  it('deduplicates concurrent snapshots and ordered receipts, rejecting changed history', async () => {
    const ids = await Promise.all([repo.insertRoutingSnapshot(snapshot('same-turn')), repo.insertRoutingSnapshot(snapshot('same-turn'))])
    expect(ids[0]).toBe(ids[1])
    await expect(repo.insertRoutingSnapshot({ ...snapshot('same-turn'), source: 'backend' })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    const start = { userId: user, snapshotId: ids[0], role: 'planner', phase: 'start', status: 'started' }
    await expect(repo.insertRoleInvocationReceipt({ ...start, userId: other })).rejects.toBeDefined()
    await expect(repo.insertRoleInvocationReceipt({ ...start, phase: 'terminal', status: 'succeeded' })).rejects.toBeDefined()
    await Promise.all([repo.insertRoleInvocationReceipt(start), repo.insertRoleInvocationReceipt(start)])
    await repo.insertRoleInvocationReceipt({ ...start, phase: 'terminal', status: 'succeeded' })
    await expect(repo.insertRoleInvocationReceipt({ ...start, phase: 'terminal', status: 'failed' })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect((await pool.query('SELECT * FROM ai_turn_role_invocations WHERE snapshot_id=$1', [ids[0]])).rowCount).toBe(2)
  })
  it('pins in-flight credentials and rejects stale validation/catalog completion after replacement', async () => {
    const pinned = await repo.loadConnectionCredential(user, connectionId, 1)
    const pinnedBytes = Buffer.from(pinned.ciphertext)
    await repo.replaceConnectionCredential(user, connectionId, encrypted())
    expect(pinned.ciphertext).toEqual(pinnedBytes)
    await expect(repo.loadConnectionCredential(user, connectionId, 1)).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    await expect(repo.storeConnectionValidation(user, connectionId, { credentialVersion: 1, state: 'validated',
      models: [{ modelId: 'stale-model', displayName: 'Stale', compatibleRoles: ['worker'] }] })).rejects.toBeDefined()
    expect((await pool.query('SELECT available FROM ai_connection_models WHERE connection_id=$1', [connectionId])).rows).toEqual([{ available: false }])
    await repo.storeConnectionValidation(user, connectionId, { credentialVersion: 2, state: 'validated',
      models: [{ modelId: 'model-a', displayName: 'Model A', compatibleRoles: [...AI_ROLES] }] })
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
    await expect(repo.withCliInvocationAuthorization(user, 'codex', () => { starts++; return { pid: 1 } })).rejects.toMatchObject({ code: 'AI_CLI_NOT_GRANTED' })
    expect(starts).toBe(0)
    await repo.setCliGrant(admin, user, 'codex', true)
    let revoke: Promise<void> | undefined
    await repo.withCliInvocationAuthorization(user, 'codex', () => {
      starts++
      revoke = repo.setCliGrant(admin, user, 'codex', false)
      return { pid: 2 }
    })
    await revoke
    await expect(repo.withCliInvocationAuthorization(user, 'codex', () => { starts++; return { pid: 3 } })).rejects.toBeDefined()
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

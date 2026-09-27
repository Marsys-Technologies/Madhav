import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { Pool } from 'pg'
import * as database from '../../db/client'
import * as repository from '../repository'
import * as audit from '../audit'
import { AI_ROLES } from '../types'
import type { EncryptedCredential } from '../crypto'

const execute = vi.fn()
const release = vi.fn()
const client = { query: execute, release }
const connect = vi.fn(async () => client)
const globalPool = globalThis as typeof globalThis & { __pgPool?: Pool }

beforeEach(() => {
  execute.mockReset().mockResolvedValue({ rows: [], rowCount: 0 })
  release.mockReset()
  connect.mockClear()
  globalPool.__pgPool = { connect, query: execute } as unknown as Pool
})

// Mock only the external PostgreSQL transport. Assertions below check the real
// repository's ownership predicates, parameter mapping, ordering and projections.
const connectionId = '00000000-0000-4000-8000-000000000001'
const configurationId = '00000000-0000-4000-8000-000000000002'
const conversationId = '00000000-0000-4000-8000-000000000003'
const choice = { kind: 'provider_model' as const, connectionId, modelId: 'model-a' }
const assignments = { synthesizer: choice, planner: choice, deep_planner: choice, worker: choice }
const safeConnection = { id: connectionId, provider_id: 'openai', name: 'Personal', masked_suffix: '••••1234', validation_state: 'validated', credential_version: '1', credential_validity: 'valid', deleted_at: null }
const encrypted: EncryptedCredential = {
  ciphertext: Buffer.alloc(2), nonce: Buffer.alloc(12), authTag: Buffer.alloc(16), wrappedDataKey: Buffer.alloc(32),
  wrapNonce: Buffer.alloc(12), wrapAuthTag: Buffer.alloc(16), keyVersion: 'test', mask: '••••1234', fingerprint: 'f'.repeat(64),
}
function respond(handler: (sql: string, params: unknown[]) => Record<string, unknown>[] | undefined) {
  execute.mockImplementation(async (sql: string, params: unknown[] = []) => {
    const rows = handler(sql.replace(/\s+/g, ' ').trim(), params) ?? []
    return { rows, rowCount: rows.length }
  })
}
function validTransport() {
  respond(sql => {
    if (sql.includes('FROM profiles')) return [{ id: 'alice' }]
    if (sql.includes('FROM ai_provider_connections')) return [safeConnection]
    if (sql.includes('FROM ai_connection_models')) return [{ compatible_roles: AI_ROLES, available: true }]
    if (sql.includes('RETURNING')) return [{ ...safeConnection, id: configurationId, version: '2' }]
  })
}
const calls = () => execute.mock.calls.map(([sql, params]) => ({ sql: String(sql).replace(/\s+/g, ' ').trim(), params: params as unknown[] }))

describe('owned AI configuration repository', () => {
  it('lists only safe columns and isolates every user-owned list', async () => {
    expect(repository).toHaveProperty('listAiConsoleState')
    await repository.listAiConsoleState('alice')
    for (const { sql, params } of calls()) {
      expect(sql).not.toMatch(/SELECT \*|credential_ciphertext|wrapped_dek|keyed_fingerprint|credential_nonce/)
      if (!sql.includes('ai_cli_installations') || sql.includes('ai_cli_grants')) {
        expect(sql).toContain('user_id')
        expect(params).toContain('alice')
      }
    }
  })
  it('maps every envelope field and returns an explicit safe projection', async () => {
    expect(repository).toHaveProperty('createConnection')
    respond(sql => sql.includes('RETURNING') ? [{ ...safeConnection, credential_ciphertext: Buffer.alloc(2) }] : undefined)
    const result = await repository.createConnection('alice', { providerId: 'openai', name: 'Personal' }, encrypted)
    expect(result).toEqual({ id: connectionId, providerId: 'openai', name: 'Personal', maskedSuffix: '••••1234', validationState: 'validated' })
    const insert = calls().find(c => c.sql.startsWith('INSERT INTO ai_provider_connections'))!
    expect(insert.params).toEqual(['alice', 'openai', 'Personal', encrypted.ciphertext, encrypted.nonce, encrypted.authTag, encrypted.wrappedDataKey, encrypted.wrapNonce, encrypted.wrapAuthTag, 'test', '••••1234', encrypted.fingerprint])
  })
  it('replaces credentials with a version increment and invalidates catalog in the same transaction', async () => {
    expect(repository).toHaveProperty('replaceConnectionCredential')
    validTransport()
    await repository.replaceConnectionCredential('alice', connectionId, encrypted)
    const statements = calls()
    expect(statements[0].sql).toBe('BEGIN')
    const replace = statements.find(c => c.sql.startsWith('UPDATE ai_provider_connections'))!
    expect(replace.sql).toContain('credential_version=credential_version+1')
    expect(replace.sql).toContain('user_id=$1')
    expect(replace.params.slice(0, 2)).toEqual(['alice', connectionId])
    expect(statements.some(c => c.sql.includes('UPDATE ai_connection_models') && c.sql.includes('available=false') && c.sql.includes('user_id'))).toBe(true)
    expect(statements.at(-1)?.sql).toBe('COMMIT')
    expect(statements.find(c => c.sql.startsWith('INSERT INTO ai_configuration_audit_log'))?.params).toContain('connection_credential_replaced')
  })
  it('rejects stale validation before replacing the catalog after a credential race', async () => {
    expect(repository).toHaveProperty('storeConnectionValidation')
    respond(sql => sql.includes('FROM ai_provider_connections') ? [{ ...safeConnection, credential_version: '2' }] : undefined)
    await expect(repository.storeConnectionValidation('alice', connectionId, { credentialVersion: 1, state: 'validated', models: [{ modelId: 'model-a', displayName: 'A', compatibleRoles: [...AI_ROLES] }] })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(calls().some(c => c.sql.startsWith('UPDATE'))).toBe(false)
    expect(calls().at(-1)?.sql).toBe('ROLLBACK')
  })
  it('refreshes live catalogs without deleting unavailable model identities', async () => {
    expect(repository).toHaveProperty('storeConnectionValidation')
    validTransport()
    await repository.storeConnectionValidation('alice', connectionId, { credentialVersion: 1, state: 'validated', models: [{ modelId: 'model-b', displayName: 'B', compatibleRoles: ['worker'] }] })
    expect(calls().some(c => c.sql.includes('available=false'))).toBe(true)
    expect(calls().some(c => c.sql.includes('ON CONFLICT(connection_id,model_id) DO UPDATE'))).toBe(true)
    expect(calls().some(c => c.sql.startsWith('DELETE'))).toBe(false)
  })
  it('preserves confirmed validity on transient validation failure', async () => {
    expect(repository).toHaveProperty('storeConnectionValidation')
    validTransport()
    await repository.storeConnectionValidation('alice', connectionId, { credentialVersion: 1, state: 'unreachable', errorCode: 'AI_PROVIDER_UNREACHABLE' })
    const update = calls().find(c => c.sql.startsWith('UPDATE ai_provider_connections'))!
    expect(update.params).toContain('valid')
    expect(update.sql).toContain('ELSE last_validated_at')
  })
  it('rejects incomplete roles before opening a transaction', async () => {
    expect(repository).toHaveProperty('saveConfiguration')
    await expect(repository.saveConfiguration('alice', { name: 'Bad', roles: { worker: choice } })).rejects.toBeDefined()
    expect(execute).not.toHaveBeenCalled()
  })
  it('atomically saves exactly four assignments with optimistic version protection', async () => {
    expect(repository).toHaveProperty('saveConfiguration')
    validTransport()
    await repository.saveConfiguration('alice', { id: configurationId, expectedVersion: 1, name: 'Team', roles: assignments })
    const update = calls().find(c => c.sql.startsWith('UPDATE ai_custom_configurations'))!
    expect(update.sql).toContain('version=version+1')
    expect(update.sql).toContain('version=$4')
    expect(update.params).toEqual(['alice', configurationId, 'Team', 1])
    const roles = calls().filter(c => c.sql.startsWith('INSERT INTO ai_custom_configuration_roles'))
    expect(roles).toHaveLength(4)
    expect(roles.map(c => c.params[2])).toEqual(['synthesizer', 'planner', 'deep_planner', 'worker'])
  })
  it('changes default through one owner-scoped upsert without clearing the old choice', async () => {
    expect(repository).toHaveProperty('setUserDefault')
    validTransport()
    await repository.setUserDefault('alice', choice)
    expect(calls().find(c => c.sql.startsWith('INSERT INTO ai_user_defaults'))?.sql).toContain('ON CONFLICT(user_id) DO UPDATE')
    expect(calls().some(c => c.sql.startsWith('DELETE'))).toBe(false)
  })
  it('rejects another user’s connection and never changes their default', async () => {
    expect(repository).toHaveProperty('setUserDefault')
    await expect(repository.setUserDefault('mallory', choice)).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(calls().find(c => c.sql.includes('FROM ai_provider_connections'))?.params).toEqual(['mallory', connectionId])
    expect(calls().some(c => c.sql.startsWith('INSERT'))).toBe(false)
  })
  it('rejects foreign conversations before writing selection', async () => {
    expect(repository).toHaveProperty('setConversationSelection')
    await expect(repository.setConversationSelection('mallory', conversationId, { kind: 'default' })).rejects.toMatchObject({ code: 'AI_PERMISSION_DENIED' })
    expect(calls().find(c => c.sql.includes('FROM conversations'))?.sql).toContain('user_id=$1')
    expect(calls().some(c => c.sql.startsWith('INSERT'))).toBe(false)
  })
  it('previews transitive configuration dependencies and refuses unconfirmed deletion', async () => {
    expect(repository).toHaveProperty('previewChoiceDependencies')
    validTransport()
    await repository.previewChoiceDependencies('alice', choice)
    expect(calls().some(c => c.sql.includes('ai_custom_configuration_roles') && c.sql.includes('user_id'))).toBe(true)
    expect(calls().some(c => c.sql.includes('ai_conversation_selections') && c.sql.includes('configuration_id'))).toBe(true)
    execute.mockClear()
    await expect(repository.deleteConnection('alice', connectionId, false)).rejects.toMatchObject({ code: 'AI_PERMISSION_DENIED' })
    expect(execute).not.toHaveBeenCalled()
  })
  it('tombstones confirmed deletion and leaves dependent choices untouched', async () => {
    expect(repository).toHaveProperty('deleteConnection')
    validTransport()
    await repository.deleteConnection('alice', connectionId, true)
    expect(calls().some(c => c.sql.includes('SET deleted_at=now()') && c.sql.includes('user_id=$1'))).toBe(true)
    expect(calls().some(c => /(?:UPDATE|DELETE FROM) ai_(?:user_defaults|conversation_selections|custom_configuration_roles)/.test(c.sql))).toBe(false)
  })
  it('cannot fetch a replacement key for an already resolved credential version', async () => {
    expect(repository).toHaveProperty('loadConnectionCredential')
    respond(sql => sql.includes('FROM ai_provider_connections') ? [] : [{ id: 'alice' }])
    await expect(repository.loadConnectionCredential('alice', connectionId, 1)).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    const read = calls().find(c => c.sql.includes('FROM ai_provider_connections'))!
    expect(read.sql).toContain('credential_version=$3')
    expect(read.sql).toContain("status='active'")
  })
  it('rechecks the exact CLI grant under a lock immediately before the invocation callback', async () => {
    expect(repository).toHaveProperty('withCliInvocationAuthorization')
    const spawn = vi.fn()
    await expect(repository.withCliInvocationAuthorization('alice', 'codex', spawn)).rejects.toMatchObject({ code: 'AI_CLI_NOT_GRANTED' })
    expect(spawn).not.toHaveBeenCalled()
    expect(calls().find(c => c.sql.includes('ai_cli_grants'))?.sql).toContain('FOR SHARE')
    expect(calls().find(c => c.sql.includes('ai_cli_grants'))?.params).toEqual(['alice', 'codex'])
  })
  it('starts only after grant locking and commits after immediate handle acquisition', async () => {
    validTransport()
    respond(sql => sql.includes('ai_cli_grants') ? [{ cli_id: 'codex' }] : undefined)
    const handle = { pid: 42 }
    const result = await repository.withCliInvocationAuthorization('alice', 'codex', () => {
      expect(calls().at(-1)?.sql).toContain('FOR SHARE')
      return handle
    })
    expect(result).toBe(handle)
    expect(calls().at(-1)?.sql).toBe('COMMIT')
  })
  it('reads default conversation selection only after an ownership check', async () => {
    expect(repository).toHaveProperty('getConversationSelection')
    respond(sql => sql.includes('FROM conversations') ? [{ id: conversationId }] : undefined)
    await expect(repository.getConversationSelection('alice', conversationId)).resolves.toEqual({ kind: 'default' })
    expect(calls().find(c => c.sql.includes('FROM ai_conversation_selections'))?.params).toEqual(['alice', conversationId])
  })
  it('renames with a distinct audit event and rejects foreign configuration deletion', async () => {
    validTransport()
    await repository.renameConnection('alice', connectionId, 'Renamed')
    expect(calls().find(c => c.sql.includes('ai_configuration_audit_log'))?.params).toContain('connection_renamed')
    execute.mockReset().mockResolvedValue({ rows: [], rowCount: 0 })
    await expect(repository.deleteConfiguration('mallory', configurationId, true)).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(calls().find(c => c.sql.startsWith('UPDATE'))?.params).toEqual(['mallory', configurationId])
  })
  it('duplicates all roles with a distinct new configuration identity and audit event', async () => {
    respond(sql => {
      if (sql.includes('FROM ai_custom_configuration_roles')) return AI_ROLES.map(role => ({ role, kind: 'provider_model', connection_id: connectionId, model_id: 'model-a' }))
      if (sql.includes('FROM ai_provider_connections')) return [safeConnection]
      if (sql.includes('FROM ai_connection_models')) return [{ compatible_roles: AI_ROLES }]
      if (sql.includes('FROM ai_custom_configurations') || sql.includes('RETURNING')) return [{ id: configurationId, name: 'Copy', version: '1' }]
    })
    const result = await repository.duplicateConfiguration('alice', conversationId, 'Copy')
    expect(result.id).toBe(configurationId)
    expect(calls().filter(c => c.sql.startsWith('INSERT INTO ai_custom_configuration_roles'))).toHaveLength(4)
    expect(calls().find(c => c.sql.includes('ai_configuration_audit_log'))?.params).toContain('configuration_duplicated')
  })
  it('reconstructs a pinned envelope and refuses accidental serialization', async () => {
    respond(() => [{ credential_ciphertext: encrypted.ciphertext, credential_nonce: encrypted.nonce,
      credential_tag: encrypted.authTag, wrapped_dek: encrypted.wrappedDataKey, wrap_nonce: encrypted.wrapNonce,
      wrap_tag: encrypted.wrapAuthTag, kek_version: encrypted.keyVersion, masked_suffix: encrypted.mask, keyed_fingerprint: encrypted.fingerprint }])
    const record = await repository.loadConnectionCredential('alice', connectionId, 1)
    expect(record).toEqual(encrypted)
    expect(JSON.stringify(record)).toBe('"[REDACTED]"')
  })
  it('denies grant mutations without an active super-admin actor', async () => {
    expect(repository).toHaveProperty('setCliGrant')
    await expect(repository.setCliGrant('mallory', 'alice', 'codex', true)).rejects.toMatchObject({ code: 'AI_PERMISSION_DENIED' })
    expect(calls().find(c => c.sql.includes('FROM profiles'))?.sql).toContain("role='super_admin'")
    expect(calls().some(c => c.sql.startsWith('INSERT') || c.sql.startsWith('UPDATE'))).toBe(false)
  })
  it('writes grant/revoke and only safe administrator audit identifiers atomically', async () => {
    expect(repository).toHaveProperty('setCliGrant')
    validTransport()
    await repository.setCliGrant('admin', 'alice', 'codex', false)
    expect(calls().find(c => c.sql.startsWith('UPDATE ai_cli_grants'))?.sql).toContain('user_id=$1')
    // A revoker may wait behind a later-started grant transaction; transaction
    // now() would predate granted_at and violate the database's timestamp check.
    expect(calls().find(c => c.sql.startsWith('UPDATE ai_cli_grants'))?.sql).toContain('revoked_at=clock_timestamp()')
    expect(calls().find(c => c.sql.startsWith('INSERT INTO admin_audit_log'))?.params).toEqual(['admin', 'ai_cli_revoke', 'alice', { cliId: 'codex' }])
    expect(calls().at(-1)?.sql).toBe('COMMIT')
  })
  it('never records a grant that a disabled target could not receive', async () => {
    respond(sql => sql.includes('FROM profiles') && sql.startsWith('SELECT') ? [{ id: 'admin' }] : undefined)
    await expect(repository.setCliGrant('admin', 'disabled-user', 'codex', true)).rejects.toMatchObject({ code: 'AI_PERMISSION_DENIED' })
    expect(calls().some(c => c.sql.startsWith('INSERT INTO admin_audit_log'))).toBe(false)
  })
})

describe('immutable history and safe audit', () => {
  const snapshot = { userId: 'alice', correlationId: 'turn', source: 'backend' as const, conversationId: null, selection: { kind: 'default' as const }, resolvedChoice: choice, configurationVersion: null, roles: Object.fromEntries(AI_ROLES.map(r => [r, { ...choice, providerId: 'openai' }])) }
  it('rejects secret-bearing snapshots before touching persistence', async () => {
    expect(repository).toHaveProperty('insertRoutingSnapshot')
    await expect(repository.insertRoutingSnapshot({ ...snapshot, credential: 'forbidden' })).rejects.toBeDefined()
    expect(execute).not.toHaveBeenCalled()
  })
  it('deduplicates identical snapshots and refuses a conflicting correlation', async () => {
    expect(repository).toHaveProperty('insertRoutingSnapshot')
    respond(sql => sql.includes('FROM ai_turn_routing_snapshots') ? [{ id: configurationId, source: 'backend', conversation_id: null, selection: { kind: 'default' }, resolved_choice: choice, configuration_version: null, roles: snapshot.roles }] : undefined)
    await expect(repository.insertRoutingSnapshot(snapshot)).resolves.toBe(configurationId)
    expect(calls().some(c => c.sql.includes('ON CONFLICT(user_id,correlation_id) DO NOTHING'))).toBe(true)
    expect(calls().some(c => c.sql.startsWith('UPDATE'))).toBe(false)
    await expect(repository.insertRoutingSnapshot({ ...snapshot, source: 'mcp' })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
  })
  it('requires snapshot ownership and ordered immutable role receipts', async () => {
    expect(repository).toHaveProperty('insertRoleInvocationReceipt')
    await expect(repository.insertRoleInvocationReceipt({ userId: 'mallory', snapshotId: configurationId, role: 'planner', phase: 'start', status: 'started' })).rejects.toMatchObject({ code: 'AI_PERMISSION_DENIED' })
    expect(calls().some(c => c.sql.includes('user_id=$1') && c.params[0] === 'mallory')).toBe(true)
  })
  it('accepts identical receipt retries but rejects changed terminal results', async () => {
    respond(sql => {
      if (sql.startsWith('SELECT id FROM ai_turn_routing_snapshots')) return [{ id: configurationId }]
      if (sql.includes('FROM ai_turn_role_invocations')) return [{ status: 'succeeded', error_code: null }]
    })
    const receipt = { userId: 'alice', snapshotId: configurationId, role: 'planner', phase: 'terminal', status: 'succeeded' }
    await repository.insertRoleInvocationReceipt(receipt)
    expect(calls().some(c => c.sql.includes('ON CONFLICT(snapshot_id,role,phase) DO NOTHING'))).toBe(true)
    await expect(repository.insertRoleInvocationReceipt({ ...receipt, status: 'failed' })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(calls().some(c => c.sql.startsWith('UPDATE'))).toBe(false)
  })
  it('rejects audit content outside closed identifiers and event vocabulary', async () => {
    expect(audit).toHaveProperty('writeAiAudit')
    await expect(audit.writeAiAudit(client, 'alice', { event: 'connection_renamed', connectionId, prompt: 'forbidden' })).rejects.toBeDefined()
    expect(execute).not.toHaveBeenCalled()
    await audit.writeAiAudit(client, 'alice', { event: 'connection_renamed', connectionId })
    expect(calls()[0].params).toEqual(['alice', 'connection_renamed', connectionId, null, null, null])
  })
})

describe('transaction lifetime', () => {
  it('commits the callback result and releases once', async () => {
    expect(database).toHaveProperty('withTransaction')
    const value = await database.withTransaction(async c => { await c.query('WORK'); return 7 })
    expect(value).toBe(7)
    expect(execute.mock.calls.map(c => c[0])).toEqual(['BEGIN', 'WORK', 'COMMIT'])
    expect(release).toHaveBeenCalledOnce()
  })
  it.each(['BEGIN', 'WORK', 'COMMIT'])('rolls back and releases on %s failure without retrying', async failure => {
    expect(database).toHaveProperty('withTransaction')
    const error = new Error('test failure')
    execute.mockImplementation(async sql => { if (sql === failure) throw error; return { rows: [] } })
    await expect(database.withTransaction(c => c.query('WORK'))).rejects.toBe(error)
    expect(execute.mock.calls.at(-1)?.[0]).toBe('ROLLBACK')
    expect(release).toHaveBeenCalledOnce()
    expect(connect).toHaveBeenCalledOnce()
  })
  it('preserves primary error and destroys a connection after rollback failure', async () => {
    expect(database).toHaveProperty('withTransaction')
    const error = new Error('original')
    execute.mockImplementation(async sql => { if (sql === 'ROLLBACK') throw new Error('rollback'); return { rows: [] } })
    await expect(database.withTransaction(async () => { throw error })).rejects.toBe(error)
    expect(release).toHaveBeenCalledWith(true)
  })
})

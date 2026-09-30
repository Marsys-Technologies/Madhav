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
const mcpCorrelationId = '00000000-0000-4000-8000-000000000004'
const choice = { kind: 'provider_model' as const, connectionId, modelId: 'model-a' }
const assignments = { synthesizer: choice, planner: choice, deep_planner: choice, worker: choice }
const safeConnection = { id: connectionId, provider_id: 'openai', name: 'Personal', masked_suffix: '••••1234', validation_state: 'validated', credential_version: '1', credential_validity: 'valid', deleted_at: null }
const testedModel = { user_selected: true, plain_tested_at: new Date(), tested_credential_version: 1, credential_version: 1 }
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
    if (sql.includes('FROM ai_connection_models')) return [{ compatible_roles: AI_ROLES, available: true, ...testedModel }]
    if (sql.includes('RETURNING')) return [{ ...safeConnection, id: configurationId, version: '2' }]
  })
}
const calls = () => execute.mock.calls.map(([sql, params]) => ({ sql: String(sql).replace(/\s+/g, ' ').trim(), params: params as unknown[] }))

describe('owned AI configuration repository', () => {
  it('persists a provider preset only for its owning connection', async () => {
    validTransport()
    await repository.saveConfiguration('alice', {
      name: 'Personal OpenAI roles', configurationKind: 'provider_preset', ownerConnectionId: connectionId,
      roles: assignments,
    })
    const insert = calls().find(call => call.sql.startsWith('INSERT INTO ai_custom_configurations'))!
    expect(insert.sql).toContain('configuration_kind')
    expect(insert.params).toEqual(['alice', 'Personal OpenAI roles', 'provider_preset', connectionId, null])
    await expect(repository.saveConfiguration('alice', {
      name: 'Wrong preset', configurationKind: 'provider_preset', ownerConnectionId: configurationId,
      roles: assignments,
    })).rejects.toBeDefined()
  })

  it('refuses a new configuration that mixes API and CLI targets', async () => {
    const mixed = { ...assignments, worker: { kind: 'local_cli' as const, cliId: 'claude_code' as const, modelId: null } }
    await expect(repository.saveConfiguration('alice', {
      name: 'Mixed', configurationKind: 'custom_api', roles: mixed,
    })).rejects.toBeDefined()
    expect(calls().some(call => call.sql.startsWith('INSERT INTO ai_custom_configurations'))).toBe(false)
  })

  it('authorizes a managed principal without reading Default or routing state', async () => {
    respond(sql => {
      if (sql.includes('FROM mcp_api_keys')) return [{ key_id: 'mcp_test_KEY001' }]
      if (sql.includes('FROM profiles')) return [{ id: 'alice', role: 'guest' }]
      if (sql.includes('FROM charts')) return [{ owner_id: 'alice' }]
      return undefined
    })
    await expect(repository.authorizeMcpPrincipal({
      userId: 'alice', keyId: 'mcp_test_KEY001', authKind: 'api_key', chartId: conversationId,
    })).resolves.toEqual({ role: 'guest' })
    expect(calls().some(call => call.sql.includes('FROM ai_user_defaults'))).toBe(false)
    expect(calls().some(call => call.sql.includes('FROM ai_turn_routing_snapshots'))).toBe(false)
    expect(calls().at(-1)?.sql).toBe('COMMIT')
  })

  it.each([
    ['api_key', 'mcp_test_KEY001'],
    ['oauth', `oauth_sha256:${'a'.repeat(64)}`],
  ] as const)('atomically verifies %s MCP mapping before Default resolution and snapshot', async (authKind, keyId) => {
    respond((sql, params) => {
      if (sql.includes('FROM profiles')) return [{ id: 'alice', role: 'guest' }]
      if (sql.includes('FROM mcp_api_keys')) return [{ key_id: params[0] }]
      if (sql.includes('FROM mcp_oauth_tokens')) return [{ access_token_hash: params[0] }]
      if (sql.includes('FROM charts')) return [{ owner_id: 'alice' }]
      if (sql.includes('FROM ai_user_defaults')) return [{ kind: 'provider_model', connection_id: connectionId, model_id: 'model-a' }]
      if (sql.includes('FROM ai_provider_connections')) return [{ ...safeConnection, provider_id: 'openai' }]
      if (sql.includes('FROM ai_connection_models')) return [{ model_id: 'model-a', display_name: 'A', compatible_roles: AI_ROLES,
        supports_tools: true, supports_structured_output: true, available: true }]
      if (sql.startsWith('INSERT INTO ai_turn_routing_snapshots')) return [{ id: configurationId }]
      return undefined
    })
    const prepared = await repository.prepareMcpRouting({
      userId: 'alice', keyId, authKind, chartId: conversationId, correlationId: mcpCorrelationId,
    })
    expect(prepared.safeSnapshot).toMatchObject({
      source: 'mcp', userId: 'alice', correlationId: mcpCorrelationId,
      conversationId: null, selection: { kind: 'default' },
    })
    const statements = calls()
    const credentialIndex = statements.findIndex(call => call.sql.includes(authKind === 'api_key' ? 'FROM mcp_api_keys' : 'FROM mcp_oauth_tokens'))
    const profileIndex = statements.findIndex(call => call.sql.includes('FROM profiles'))
    const defaultIndex = statements.findIndex(call => call.sql.includes('FROM ai_user_defaults'))
    const snapshotIndex = statements.findIndex(call => call.sql.startsWith('INSERT INTO ai_turn_routing_snapshots'))
    expect(credentialIndex).toBeGreaterThan(0)
    expect(profileIndex).toBeGreaterThan(credentialIndex)
    expect(defaultIndex).toBeGreaterThan(profileIndex)
    expect(snapshotIndex).toBeGreaterThan(defaultIndex)
    if (authKind === 'oauth') expect(statements[credentialIndex].params[0]).toBe('a'.repeat(64))
    expect(statements.at(-1)?.sql).toBe('COMMIT')
  })

  it.each([
    ['api_key', 'mcp_test_OTHER', 'revoked_at IS NULL'],
    ['oauth', `oauth_sha256:${'b'.repeat(64)}`, 'expires_at>now()'],
  ] as const)('rejects a mismatched, revoked, or expired %s mapping before reading the user Default', async (authKind, keyId, predicate) => {
    await expect(repository.prepareMcpRouting({
      userId: 'alice', keyId, authKind, chartId: conversationId,
      correlationId: mcpCorrelationId,
    })).rejects.toMatchObject({ code: 'AI_PERMISSION_DENIED' })
    expect(calls().some(call => call.sql.includes(predicate))).toBe(true)
    expect(calls().some(call => call.sql.includes('FROM profiles'))).toBe(false)
    expect(calls().some(call => call.sql.includes('FROM ai_user_defaults'))).toBe(false)
    expect(calls().at(-1)?.sql).toBe('ROLLBACK')
  })

  it('rejects a wrong chart before reading the user Default', async () => {
    respond(sql => {
      if (sql.includes('FROM mcp_api_keys')) return [{ key_id: 'mcp_test_KEY001' }]
      if (sql.includes('FROM profiles')) return [{ id: 'alice', role: 'guest' }]
      if (sql.includes('FROM charts')) return [{ owner_id: 'another-user' }]
      return undefined
    })
    await expect(repository.prepareMcpRouting({
      userId: 'alice', keyId: 'mcp_test_KEY001', authKind: 'api_key', chartId: conversationId,
      correlationId: mcpCorrelationId,
    })).rejects.toMatchObject({ code: 'AI_PERMISSION_DENIED' })
    expect(calls().some(call => call.sql.includes('FROM chart_grants'))).toBe(true)
    expect(calls().some(call => call.sql.includes('FROM ai_user_defaults'))).toBe(false)
  })

  it('fails a missing Default before snapshot insertion', async () => {
    respond(sql => {
      if (sql.includes('FROM mcp_api_keys')) return [{ key_id: 'mcp_test_KEY001' }]
      if (sql.includes('FROM profiles')) return [{ id: 'alice', role: 'guest' }]
      if (sql.includes('FROM charts')) return [{ owner_id: 'alice' }]
      return undefined
    })
    await expect(repository.prepareMcpRouting({
      userId: 'alice', keyId: 'mcp_test_KEY001', authKind: 'api_key', chartId: conversationId,
      correlationId: mcpCorrelationId,
    })).rejects.toMatchObject({ code: 'AI_DEFAULT_REQUIRED' })
    expect(calls().some(call => call.sql.startsWith('INSERT INTO ai_turn_routing_snapshots'))).toBe(false)
  })

  it('reuses a managed retry snapshot after Default/configuration changes and revalidates its pinned targets', async () => {
    const pinnedRoles = Object.fromEntries(AI_ROLES.map(role => [role, {
      kind: 'provider_model', connectionId, providerId: 'openai', modelId: 'model-a',
    }]))
    respond(sql => {
      if (sql.includes('FROM mcp_api_keys')) return [{ key_id: 'mcp_test_KEY001' }]
      if (sql.includes('FROM profiles')) return [{ id: 'alice', role: 'guest' }]
      if (sql.includes('FROM charts')) return [{ owner_id: 'alice' }]
      if (sql.includes('FROM ai_turn_routing_snapshots')) return [{
        id: configurationId, source: 'mcp', conversation_id: null,
        selection: { kind: 'default' },
        resolved_choice: { kind: 'custom_configuration', configurationId },
        configuration_version: 7, roles: pinnedRoles,
      }]
      if (sql.includes('FROM ai_provider_connections')) return [{ ...safeConnection, provider_id: 'openai' }]
      if (sql.includes('FROM ai_connection_models')) return [{ model_id: 'model-a', display_name: 'Pinned A', compatible_roles: AI_ROLES,
        supports_tools: true, supports_structured_output: true, available: true }]
      if (sql.includes('FROM ai_user_defaults') || sql.includes('FROM ai_custom_configurations')) {
        throw new Error('managed retry must not re-resolve live Default/configuration')
      }
      return undefined
    })

    const prepared = await repository.prepareMcpRouting({
      userId: 'alice', keyId: 'mcp_test_KEY001', authKind: 'api_key', chartId: conversationId,
      correlationId: mcpCorrelationId,
    })

    expect(prepared.snapshotId).toBe(configurationId)
    expect(prepared.resolution).toMatchObject({
      resolvedChoice: { kind: 'custom_configuration', configurationId },
      configurationVersion: 7,
      roles: { planner: { connectionId, modelId: 'model-a', credentialVersion: 1 } },
    })
    expect(calls().some(call => call.sql.includes('FROM ai_user_defaults'))).toBe(false)
    expect(calls().some(call => call.sql.startsWith('INSERT INTO ai_turn_routing_snapshots'))).toBe(false)
  })

  it('fails a managed retry when its pinned target is no longer currently authorized, without Default fallback', async () => {
    const pinnedRoles = Object.fromEntries(AI_ROLES.map(role => [role, {
      kind: 'provider_model', connectionId, providerId: 'openai', modelId: 'model-a',
    }]))
    respond(sql => {
      if (sql.includes('FROM mcp_api_keys')) return [{ key_id: 'mcp_test_KEY001' }]
      if (sql.includes('FROM profiles')) return [{ id: 'alice', role: 'guest' }]
      if (sql.includes('FROM charts')) return [{ owner_id: 'alice' }]
      if (sql.includes('FROM ai_turn_routing_snapshots')) return [{
        id: configurationId, source: 'mcp', conversation_id: null,
        selection: { kind: 'default' }, resolved_choice: choice,
        configuration_version: null, roles: pinnedRoles,
      }]
      return undefined
    })

    await expect(repository.prepareMcpRouting({
      userId: 'alice', keyId: 'mcp_test_KEY001', authKind: 'api_key', chartId: conversationId,
      correlationId: mcpCorrelationId,
    })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(calls().some(call => call.sql.includes('FROM ai_user_defaults'))).toBe(false)
    expect(calls().some(call => call.sql.startsWith('INSERT INTO ai_turn_routing_snapshots'))).toBe(false)
  })
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
    expect(result).toEqual({ id: connectionId, providerId: 'openai', name: 'Personal', maskedSuffix: '••••1234', validationState: 'validated', confirmedValid: true })
    const insert = calls().find(c => c.sql.startsWith('INSERT INTO ai_provider_connections'))!
    expect(insert.sql).toContain('anthropic_workspace_id,model_retest_required')
    expect(insert.sql).toContain('$13,true')
    expect(insert.params).toEqual(['alice', 'openai', 'Personal', encrypted.ciphertext, encrypted.nonce, encrypted.authTag, encrypted.wrappedDataKey, encrypted.wrapNonce, encrypted.wrapAuthTag, 'test', '••••1234', encrypted.fingerprint, null])
  })
  it('selects credential validity only to derive the safe confirmation boolean', async () => {
    respond(sql => sql.includes('FROM ai_provider_connections') ? [safeConnection] : undefined)
    const state = await repository.listAiConsoleState('alice')
    const list = calls().find(c => c.sql.includes('FROM ai_provider_connections'))!
    expect(list.sql).toContain('credential_validity')
    expect(state.connections[0]).toMatchObject({ credential_validity: 'valid' })
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
    expect(statements.some(c => c.sql.includes('UPDATE ai_connection_models SET plain_tested_at=NULL')
      && c.sql.includes('tested_credential_version=NULL') && c.sql.includes('last_probe_at=NULL'))).toBe(true)
    expect(statements.at(-1)?.sql).toBe('COMMIT')
    expect(statements.find(c => c.sql.startsWith('INSERT INTO ai_configuration_audit_log'))?.params).toContain('connection_credential_replaced')
  })
  it('changes only an owned Anthropic workspace, versions the connection, and invalidates its models', async () => {
    validTransport()
    const workspaceId = 'wrkspc_01JEueaSaKJ72sh4drDASzH2'
    await repository.updateConnectionWorkspace('alice', connectionId, workspaceId)
    const update = calls().find(c => c.sql.includes('SET anthropic_workspace_id=$3'))!
    expect(update.params).toEqual(['alice', connectionId, workspaceId])
    expect(update.sql).toContain("provider_id='anthropic'")
    expect(update.sql).toContain('credential_version=credential_version+1')
    expect(calls().some(c => c.sql.includes('UPDATE ai_connection_models') && c.sql.includes('available=false'))).toBe(true)
    const clear = calls().find(c => c.sql.includes('UPDATE ai_connection_models SET plain_tested_at=NULL'))!
    expect(clear.params).toEqual(['alice', connectionId])
    expect(clear.sql).toContain('tested_credential_version=NULL')
    expect(clear.sql).toContain('last_probe_at=NULL')
    expect(calls().findIndex(c => c.sql.includes('available=false'))).toBeLessThan(calls().findIndex(c => c.sql.includes('plain_tested_at=NULL')))
  })
  it('rejects stale validation before replacing the catalog after a credential race', async () => {
    expect(repository).toHaveProperty('storeConnectionValidation')
    respond(sql => sql.includes('FROM ai_provider_connections') ? [{ ...safeConnection, credential_version: '2' }] : undefined)
    await expect(repository.storeConnectionValidation('alice', connectionId, { credentialVersion: 1, state: 'validated', models: [{ modelId: 'model-a', displayName: 'A', compatibleRoles: [...AI_ROLES], supportsTools: true, supportsStructuredOutput: true }] })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(calls().some(c => c.sql.startsWith('UPDATE'))).toBe(false)
    expect(calls().at(-1)?.sql).toBe('ROLLBACK')
  })
  it('refreshes live catalogs without deleting unavailable model identities', async () => {
    expect(repository).toHaveProperty('storeConnectionValidation')
    validTransport()
    await repository.storeConnectionValidation('alice', connectionId, { credentialVersion: 1, state: 'validated', models: [{ modelId: 'model-b', displayName: 'B', compatibleRoles: ['worker'], supportsTools: false, supportsStructuredOutput: true }] })
    expect(calls().some(c => c.sql.includes('available=false'))).toBe(true)
    expect(calls().some(c => c.sql.includes('ON CONFLICT(connection_id,model_id) DO UPDATE'))).toBe(true)
    const modelWrite = calls().find(c => c.sql.startsWith('INSERT INTO ai_connection_models'))!
    expect(modelWrite.sql).toContain('supports_tools,supports_structured_output')
    expect(modelWrite.params.slice(-2)).toEqual([false, true])
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
    expect(update.params).toEqual(['alice', configurationId, 'Team', 1, 'custom_api', null, null])
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
  it.each([
    ['valid', true],
    ['unknown', false],
    ['invalid', false],
  ] as const)('allows a validating direct default only with %s retained credential authority', async (validity, accepted) => {
    respond(sql => {
      if (sql.includes('FROM ai_provider_connections')) return [{ ...safeConnection, validation_state: 'validating', credential_validity: validity }]
      if (sql.includes('FROM ai_connection_models')) return [{ compatible_roles: AI_ROLES, available: true, ...testedModel }]
      return undefined
    })
    const result = repository.setUserDefault('alice', choice)
    if (accepted) await expect(result).resolves.toBeUndefined()
    else await expect(result).rejects.toMatchObject({ code: 'AI_CONNECTION_INVALID' })
    expect(calls().some(c => c.sql.startsWith('INSERT INTO ai_user_defaults'))).toBe(accepted)
  })
  it.each([
    ['valid', true],
    ['unknown', false],
    ['invalid', false],
  ] as const)('allows a validating provider in a saved configuration only with %s retained credential authority', async (validity, accepted) => {
    respond(sql => {
      if (sql.includes('FROM ai_provider_connections')) return [{ ...safeConnection, validation_state: 'validating', credential_validity: validity }]
      if (sql.includes('FROM ai_connection_models')) return [{ compatible_roles: AI_ROLES, available: true, ...testedModel }]
      if (sql.includes('RETURNING')) return [{ id: configurationId, version: '1' }]
      return undefined
    })
    const result = repository.saveConfiguration('alice', { name: 'Revalidating', roles: assignments })
    if (accepted) await expect(result).resolves.toMatchObject({ id: configurationId, roles: assignments })
    else await expect(result).rejects.toMatchObject({ code: 'AI_CONNECTION_INVALID' })
    expect(calls().filter(c => c.sql.startsWith('INSERT INTO ai_custom_configuration_roles'))).toHaveLength(accepted ? 4 : 0)
  })
  it('requires every role for direct defaults and explicit conversation models', async () => {
    respond(sql => {
      if (sql.includes('FROM ai_provider_connections')) return [safeConnection]
      if (sql.includes('FROM ai_connection_models')) return [{ compatible_roles: ['synthesizer', 'planner', 'deep_planner'], available: true, ...testedModel }]
      if (sql.includes('FROM conversations')) return [{ id: conversationId }]
    })
    await expect(repository.setUserDefault('alice', choice)).rejects.toMatchObject({ code: 'AI_ROLE_INCOMPATIBLE' })
    await expect(repository.setConversationSelection('alice', conversationId, { kind: 'explicit', choice })).rejects.toMatchObject({ code: 'AI_ROLE_INCOMPATIBLE' })
    expect(calls().some(c => c.sql.startsWith('INSERT'))).toBe(false)
  })
  it('allows a partial-capability model only in its compatible custom role', async () => {
    respond((sql, params) => {
      if (sql.includes('FROM ai_provider_connections')) return [safeConnection]
      if (sql.includes('FROM ai_connection_models')) return [{ compatible_roles: params[2] === 'synthesis-only' ? ['synthesizer'] : AI_ROLES, available: true, ...testedModel }]
      if (sql.includes('RETURNING')) return [{ id: configurationId, version: '1' }]
    })
    const roles = { ...assignments, synthesizer: { ...choice, modelId: 'synthesis-only' } }
    expect(await repository.saveConfiguration('alice', { name: 'Mixed', roles })).toMatchObject({ roles })
    await expect(repository.saveConfiguration('alice', { name: 'Wrong role', roles: { ...roles, worker: roles.synthesizer } })).rejects.toMatchObject({ code: 'AI_ROLE_INCOMPATIBLE' })
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
    await expect(repository.withCliInvocationAuthorization('alice', 'claude_code', spawn)).rejects.toMatchObject({ code: 'AI_CLI_NOT_GRANTED' })
    expect(spawn).not.toHaveBeenCalled()
    expect(calls().find(c => c.sql.includes('ai_cli_grants'))?.sql).toContain('FOR SHARE')
    expect(calls().find(c => c.sql.includes('ai_cli_grants'))?.params).toEqual(['alice', 'claude_code'])
  })
  it('starts only after grant locking and commits after immediate handle acquisition', async () => {
    validTransport()
    respond(sql => sql.includes('ai_cli_grants') ? [{ cli_id: 'claude_code' }] : undefined)
    const handle = { pid: 42, cancel: vi.fn() }
    const result = await repository.withCliInvocationAuthorization('alice', 'claude_code', () => {
      expect(calls().at(-1)?.sql).toContain('FOR SHARE')
      return handle
    })
    expect(result).toBe(handle)
    expect(handle.cancel).not.toHaveBeenCalled()
    expect(calls().at(-1)?.sql).toBe('COMMIT')
  })
  it('runs the asynchronous identity check under the grant lock immediately before start', async () => {
    respond(sql => sql.includes('ai_cli_grants') ? [{ cli_id: 'claude_code' }] : undefined)
    const order: string[] = []
    const checkIdentity = vi.fn(async () => {
      expect(calls().at(-1)?.sql).toContain('FOR SHARE')
      order.push('identity')
    })
    const start = vi.fn(() => {
      order.push('start')
      return { pid: 42, cancel: vi.fn() }
    })
    await repository.withCliInvocationAuthorization('alice', 'claude_code', start, 'execution', checkIdentity)
    expect(order).toEqual(['identity', 'start'])
  })
  it('cancels a started process exactly once when COMMIT fails and preserves that error', async () => {
    const commitError = new Error('commit failed')
    execute.mockImplementation(async (sql: string) => {
      if (sql === 'COMMIT') throw commitError
      return { rows: sql.includes('ai_cli_grants') ? [{ cli_id: 'claude_code' }] : [] }
    })
    const cancel = vi.fn(() => { throw new Error('cancel failed') })
    const start = vi.fn(() => ({ pid: 42, cancel }))
    await expect(repository.withCliInvocationAuthorization('alice', 'claude_code', start)).rejects.toBe(commitError)
    expect(start).toHaveBeenCalledOnce()
    expect(cancel).toHaveBeenCalledOnce()
    expect(calls().filter(c => c.sql === 'BEGIN')).toHaveLength(1)
  })
  it('preserves typed adapter completion and output on the identical returned handle', async () => {
    respond(sql => sql.includes('ai_cli_grants') ? [{ cli_id: 'claude_code' }] : undefined)
    const handle = { pid: 42, cancel: vi.fn(), completion: Promise.resolve('complete'), output: 'adapter output' }
    const result = await repository.withCliInvocationAuthorization('alice', 'claude_code', () => handle)
    // These assignments must compile without casts: the adapter keeps its own handle type.
    const completion: Promise<string> = result.completion
    const output: string = result.output
    expect(result).toBe(handle)
    await expect(completion).resolves.toBe('complete')
    expect(output).toBe('adapter output')
    expect(handle.cancel).not.toHaveBeenCalled()
  })
  it('rejects async callbacks before invocation and requires a concrete handle statically', async () => {
    respond(sql => sql.includes('ai_cli_grants') ? [{ cli_id: 'claude_code' }] : undefined)
    let invoked = false
    const asyncStart = async () => { invoked = true; return { pid: 42, cancel() {} } }
    // @ts-expect-error a Promise is not a synchronous cancellable process handle
    await expect(repository.withCliInvocationAuthorization('alice', 'claude_code', asyncStart)).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(invoked).toBe(false)
    expect(execute).not.toHaveBeenCalled()
    if (false) {
      // @ts-expect-error void callbacks cannot transfer ownership of a started process
      void repository.withCliInvocationAuthorization('alice', 'claude_code', () => {})
    }
  })
  it.each([undefined, null, {}, { pid: 0, cancel() {} }, { pid: 42 }, { pid: 42, cancel() {}, then() {} }])(
    'rejects malformed or thenable process handles at runtime (%j)', async value => {
      respond(sql => sql.includes('ai_cli_grants') ? [{ cli_id: 'claude_code' }] : undefined)
      await expect(repository.withCliInvocationAuthorization('alice', 'claude_code', () => value as repository.CliInvocationHandle)).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
      expect(calls().at(-1)?.sql).toBe('ROLLBACK')
    },
  )
  it('locks the user graph before any row lock or mutation across its entry points', async () => {
    const actions = [
      () => repository.createConnection('alice', { providerId: 'openai', name: 'Personal' }, encrypted),
      () => repository.renameConnection('alice', connectionId, 'Name'),
      () => repository.replaceConnectionCredential('alice', connectionId, encrypted),
      () => repository.storeConnectionValidation('alice', connectionId, { credentialVersion: 1, state: 'invalid' }),
      () => repository.saveConfiguration('alice', { name: 'Graph', roles: assignments }),
      () => repository.duplicateConfiguration('alice', configurationId, 'Copy'),
      () => repository.setUserDefault('alice', { kind: 'custom_configuration', configurationId }),
      () => repository.setConversationSelection('alice', conversationId, { kind: 'default' }),
      () => repository.deleteConnection('alice', connectionId, true),
      () => repository.deleteConfiguration('alice', configurationId, true),
      () => repository.setCliGrant('admin', 'alice', 'codex', false),
    ]
    for (const action of actions) {
      execute.mockClear()
      await action().catch(() => {})
      expect(calls()[0].sql).toBe('BEGIN')
      expect(calls()[1].sql).toContain('pg_advisory_xact_lock')
      expect(calls()[1].params).toEqual(['alice'])
    }
  })
  it('validates distinct role targets in canonical order, independent of role assignment order', async () => {
    const second = { ...choice, connectionId: configurationId }
    for (const targets of [
      { synthesizer: second, planner: choice, deep_planner: second, worker: choice },
      { synthesizer: choice, planner: second, deep_planner: choice, worker: second },
    ]) {
      validTransport()
      execute.mockClear()
      await repository.saveConfiguration('alice', { name: 'Ordered', roles: targets })
      expect(calls().filter(c => c.sql.includes('FROM ai_provider_connections')).map(c => c.params[1])).toEqual([connectionId, configurationId])
    }
  })
  it('previews implicit Default conversations while excluding explicit overrides', async () => {
    respond(sql => sql.includes('FROM ai_user_defaults') ? [{ kind: 'provider_model', connection_id: connectionId }] : undefined)
    await repository.previewChoiceDependencies('alice', choice)
    const statement = calls().find(c => c.sql.includes('ai_conversation_selections'))!
    expect(statement.sql).toContain('FROM conversations c LEFT JOIN ai_conversation_selections s')
    expect(statement.sql).toContain('c.user_id=$1')
    expect(statement.sql).toContain("(s.conversation_id IS NULL OR s.kind='default') AND $5::boolean")
    expect(statement.params[4]).toBe(true)
    execute.mockClear()
    respond(() => [])
    await repository.previewChoiceDependencies('alice', choice)
    expect(calls().find(c => c.sql.includes('ai_conversation_selections'))?.params[4]).toBe(false)
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
      if (sql.includes('FROM ai_connection_models')) return [{ compatible_roles: AI_ROLES, available: true, ...testedModel }]
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

describe('atomic routing resolution read', () => {
  it('preserves an older saved choice without probe evidence even when its key version exceeds one', async () => {
    respond(sql => {
      if (sql.includes('FROM profiles')) return [{ id: 'alice' }]
      if (sql.includes('FROM ai_provider_connections')) return [{ ...safeConnection, credential_version: 3,
        model_retest_required: false }]
      if (sql.includes('FROM ai_connection_models')) return [{ model_id: 'model-a', display_name: 'Model A',
        compatible_roles: AI_ROLES, available: true, supports_tools: true, supports_structured_output: true,
        plain_tested_at: null, tested_credential_version: null }]
    })
    await expect(repository.loadRoutingResolution('alice', { kind: 'explicit', choice }))
      .resolves.toMatchObject({ roles: { worker: { credentialVersion: 3 } } })
  })
  it('requires a fresh individual model probe after an Anthropic workspace or key change', async () => {
    let testedVersion: number | null = null
    respond(sql => {
      if (sql.includes('FROM profiles')) return [{ id: 'alice' }]
      if (sql.includes('FROM ai_provider_connections')) return [{ ...safeConnection, provider_id: 'anthropic',
        credential_version: 2, model_retest_required: true }]
      if (sql.includes('FROM ai_connection_models')) return [{ model_id: 'model-a', display_name: 'Model A',
        compatible_roles: AI_ROLES, available: true, supports_tools: true, supports_structured_output: true,
        plain_tested_at: testedVersion === null ? null : new Date(), tested_credential_version: testedVersion }]
    })
    await expect(repository.loadRoutingResolution('alice', { kind: 'explicit', choice }))
      .rejects.toMatchObject({ code: 'AI_MODEL_UNAVAILABLE' })
    testedVersion = 1
    await expect(repository.loadRoutingResolution('alice', { kind: 'explicit', choice }))
      .rejects.toMatchObject({ code: 'AI_MODEL_UNAVAILABLE' })
    testedVersion = 2
    await expect(repository.loadRoutingResolution('alice', { kind: 'explicit', choice }))
      .resolves.toMatchObject({ roles: { worker: { providerId: 'anthropic', credentialVersion: 2 } } })
  })
  it('locks an active owner and resolves only the current exact default target', async () => {
    respond((sql, params) => {
      if (sql.includes('FROM profiles')) return [{ id: 'alice' }]
      if (sql.includes('FROM conversations')) return [{ id: conversationId }]
      if (sql.includes('FROM ai_user_defaults')) return [{ kind: 'provider_model', connection_id: connectionId, model_id: 'model-a', configuration_id: null, cli_id: null }]
      if (sql.includes('FROM ai_provider_connections')) return [safeConnection]
      if (sql.includes('FROM ai_connection_models')) return [{ model_id: 'model-a', display_name: 'Model A', compatible_roles: AI_ROLES, available: true, supports_tools: true, supports_structured_output: true }]
      expect(params).not.toContain('alternative-model')
    })
    const resolution = await repository.loadRoutingResolution('alice', { kind: 'default' }, conversationId)
    expect(resolution.resolvedChoice).toEqual(choice)
    expect(resolution.configurationVersion).toBeNull()
    expect(resolution.roles.worker).toMatchObject({ ...choice, providerId: 'openai', credentialVersion: 1 })
    expect(calls()[0].sql).toBe('BEGIN')
    expect(calls().find(c => c.sql.includes('FROM profiles'))?.sql).toContain("status='active'")
    expect(calls().find(c => c.sql.includes('FROM profiles'))?.sql).toContain('FOR SHARE')
    expect(calls().find(c => c.sql.includes('FROM conversations'))?.params).toEqual(['alice', conversationId])
    expect(calls().filter(c => c.sql.includes('FROM ai_provider_connections'))).toHaveLength(1)
    expect(calls().filter(c => c.sql.includes('FROM ai_connection_models'))).toHaveLength(1)
    expect(calls().at(-1)?.sql).toBe('COMMIT')
  })

  it('fails a foreign conversation inside the user transaction before reading any choice or target', async () => {
    respond(sql => sql.includes('FROM profiles') ? [{ id: 'alice' }] : undefined)
    await expect(repository.loadRoutingResolution('alice', { kind: 'default' }, conversationId)).rejects.toMatchObject({ code: 'AI_PERMISSION_DENIED' })
    expect(calls().some(c => c.sql.includes('ai_user_defaults') || c.sql.includes('ai_provider_connections') || c.sql.includes('ai_cli_'))).toBe(false)
    expect(calls().find(c => c.sql.includes('FROM conversations'))?.params).toEqual(['alice', conversationId])
    expect(calls().at(-1)?.sql).toBe('ROLLBACK')
  })

  it('fails disabled users before reading defaults or any target', async () => {
    await expect(repository.loadRoutingResolution('disabled', { kind: 'default' })).rejects.toMatchObject({ code: 'AI_PERMISSION_DENIED' })
    expect(calls().some(c => c.sql.includes('ai_user_defaults') || c.sql.includes('ai_provider_connections') || c.sql.includes('ai_cli_'))).toBe(false)
    expect(calls().at(-1)?.sql).toBe('ROLLBACK')
  })

  it('does not auto-select when the active user has no default', async () => {
    respond(sql => sql.includes('FROM profiles') ? [{ id: 'alice' }] : undefined)
    await expect(repository.loadRoutingResolution('alice', { kind: 'default' })).rejects.toMatchObject({ code: 'AI_DEFAULT_REQUIRED' })
    expect(calls().some(c => c.sql.includes('ai_provider_connections') || c.sql.includes('ai_cli_models'))).toBe(false)
  })

  it('returns one current configuration version with four independently validated assignments', async () => {
    const cliTarget = { kind: 'local_cli' as const, cliId: 'claude_code' as const, modelId: null }
    respond(sql => {
      if (sql.includes('FROM profiles')) return [{ id: 'alice' }]
      if (sql.includes('FROM ai_custom_configurations')) return [{ id: configurationId, version: '8' }]
      if (sql.includes('FROM ai_custom_configuration_roles')) return [
        { role: 'synthesizer', kind: 'provider_model', connection_id: connectionId, model_id: 'model-a', cli_id: null },
        { role: 'planner', kind: 'local_cli', connection_id: null, model_id: null, cli_id: 'claude_code' },
        { role: 'deep_planner', kind: 'provider_model', connection_id: connectionId, model_id: 'model-a', cli_id: null },
        { role: 'worker', kind: 'local_cli', connection_id: null, model_id: null, cli_id: 'claude_code' },
      ]
      if (sql.includes('FROM ai_provider_connections')) return [safeConnection]
      if (sql.includes('FROM ai_connection_models')) return [{ model_id: 'model-a', display_name: 'Model A', compatible_roles: AI_ROLES,
        available: true, supports_tools: true, supports_structured_output: true }]
      if (sql.includes('FROM ai_cli_grants')) return [{ cli_id: 'claude_code', revoked_at: null }]
      if (sql.includes('FROM ai_cli_installations')) return [{ cli_id: 'claude_code', validation_state: 'reachable' }]
      if (sql.includes('FROM ai_cli_models')) return [{ model_id: 'builtin', display_name: 'Built in', compatible_roles: AI_ROLES, available: true, is_builtin_default: true, supports_tools: false, supports_structured_output: true }]
    })
    const selected = { kind: 'explicit' as const, choice: { kind: 'custom_configuration' as const, configurationId } }
    const resolution = await repository.loadRoutingResolution('alice', selected)
    expect(resolution.resolvedChoice).toEqual(selected.choice)
    expect(resolution.configurationVersion).toBe(8)
    expect(resolution.roles.planner).toMatchObject(cliTarget)
    expect(resolution.roles.synthesizer).toMatchObject({ supportsTools: true, supportsStructuredOutput: true })
    expect(resolution.roles.planner).toMatchObject({ supportsTools: false, supportsStructuredOutput: true })
    expect(calls().filter(c => c.sql.includes('FROM ai_provider_connections'))).toHaveLength(1)
    expect(calls().filter(c => c.sql.includes('FROM ai_cli_grants'))).toHaveLength(1)
  })

  it('stops a revoked CLI exact choice before querying installation or model alternatives', async () => {
    respond(sql => {
      if (sql.includes('FROM profiles')) return [{ id: 'alice' }]
      if (sql.includes('FROM ai_cli_grants')) return []
    })
    const selected = { kind: 'explicit' as const, choice: { kind: 'local_cli' as const, cliId: 'claude_code' as const, modelId: 'exact-model' } }
    await expect(repository.loadRoutingResolution('alice', selected)).rejects.toMatchObject({ code: 'AI_CLI_NOT_GRANTED' })
    expect(calls().some(c => c.sql.includes('FROM ai_cli_installations') || c.sql.includes('FROM ai_cli_models'))).toBe(false)
  })

  it('grant-gates an executable catalog CLI before reading installation or model state', async () => {
    respond(sql => sql.includes('FROM profiles') ? [{ id: 'alice' }] : undefined)
    const selected = { kind: 'explicit' as const,
      choice: { kind: 'local_cli' as const, cliId: 'kimi_code' as const, modelId: null } }
    await expect(repository.loadRoutingResolution('alice', selected))
      .rejects.toMatchObject({ code: 'AI_CLI_NOT_GRANTED' })
    expect(calls().some(c => c.sql.includes('FROM ai_cli_grants'))).toBe(true)
    expect(calls().some(c => c.sql.includes('FROM ai_cli_installations') || c.sql.includes('FROM ai_cli_models'))).toBe(false)
  })

  it.each([
    ['invalid', 'invalid', 'AI_PERMISSION_DENIED', 'AI_CONNECTION_INVALID'],
    ['needs_attention', 'valid', 'AI_MODEL_UNAVAILABLE', 'AI_MODEL_UNAVAILABLE'],
    ['needs_attention', 'valid', 'AI_ROLE_INCOMPATIBLE', 'AI_ROLE_INCOMPATIBLE'],
    ['needs_attention', 'valid', 'AI_PERMISSION_DENIED', 'AI_PERMISSION_DENIED'],
    ['needs_attention', 'valid', 'AI_BILLING_UNAVAILABLE', 'AI_BILLING_UNAVAILABLE'],
    ['needs_attention', 'valid', 'AI_EXECUTION_FAILED', 'AI_EXECUTION_FAILED'],
    ['unreachable', 'valid', 'AI_RATE_LIMITED', 'AI_RATE_LIMITED'],
    ['unreachable', 'valid', 'AI_PROVIDER_UNREACHABLE', 'AI_PROVIDER_UNREACHABLE'],
  ] as const)('maps provider %s/%s with %s to exact stable %s', async (state, validity, lastErrorCode, code) => {
    respond(sql => {
      if (sql.includes('FROM profiles')) return [{ id: 'alice' }]
      if (sql.includes('FROM ai_provider_connections')) return [{ ...safeConnection, validation_state: state,
        credential_validity: validity, last_error_code: lastErrorCode }]
    })
    const selected = { kind: 'explicit' as const, choice }
    await expect(repository.loadRoutingResolution('alice', selected)).rejects.toMatchObject({ code })
    expect(calls().some(c => c.sql.includes('FROM ai_connection_models'))).toBe(false)
    expect(calls().find(c => c.sql.includes('FROM ai_provider_connections'))?.sql).toContain('last_error_code')
  })

  it.each([
    ['needs_attention', 'AI_RATE_LIMITED'],
    ['unreachable', 'AI_MODEL_UNAVAILABLE'],
  ] as const)('preserves any allowlisted provider state/error %s/%s exactly', async (state, lastErrorCode) => {
    respond(sql => {
      if (sql.includes('FROM profiles')) return [{ id: 'alice' }]
      if (sql.includes('FROM ai_provider_connections')) return [{ ...safeConnection, validation_state: state,
        credential_validity: 'valid', last_error_code: lastErrorCode }]
    })
    await expect(repository.loadRoutingResolution('alice', { kind: 'explicit', choice })).rejects.toMatchObject({ code: lastErrorCode })
    expect(calls().some(c => c.sql.includes('FROM ai_connection_models'))).toBe(false)
  })

  it('fails closed when a non-validated provider state has no strictly parseable safe error', async () => {
    respond(sql => {
      if (sql.includes('FROM profiles')) return [{ id: 'alice' }]
      if (sql.includes('FROM ai_provider_connections')) return [{ ...safeConnection, validation_state: 'needs_attention',
        credential_validity: 'valid', last_error_code: null }]
    })
    await expect(repository.loadRoutingResolution('alice', { kind: 'explicit', choice })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(calls().some(c => c.sql.includes('FROM ai_connection_models'))).toBe(false)
  })

  it('keeps a confirmed-valid connection resolvable while revalidation is in progress', async () => {
    respond(sql => {
      if (sql.includes('FROM profiles')) return [{ id: 'alice' }]
      if (sql.includes('FROM ai_provider_connections')) return [{ ...safeConnection,
        validation_state: 'validating', credential_validity: 'valid', last_error_code: null }]
      if (sql.includes('FROM ai_connection_models')) return [{ model_id: 'model-a', display_name: 'Model A',
        compatible_roles: AI_ROLES, available: true, supports_tools: true, supports_structured_output: true }]
    })
    const resolution = await repository.loadRoutingResolution('alice', { kind: 'explicit', choice })
    expect(resolution.roles.worker).toMatchObject({ ...choice, providerId: 'openai', credentialVersion: 1 })
  })

  it.each(['untested', 'validating', 'validated'] as const)('treats %s with unknown validity as broken, not confirmed invalid', async state => {
    respond(sql => {
      if (sql.includes('FROM profiles')) return [{ id: 'alice' }]
      if (sql.includes('FROM ai_provider_connections')) return [{ ...safeConnection,
        validation_state: state, credential_validity: 'unknown', last_error_code: null }]
    })
    await expect(repository.loadRoutingResolution('alice', { kind: 'explicit', choice })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(calls().some(c => c.sql.includes('FROM ai_connection_models'))).toBe(false)
  })

  it.each([
    ['not_installed', 'AI_CLI_NOT_INSTALLED'],
    ['auth_unavailable', 'AI_CLI_AUTH_UNAVAILABLE'],
    ['unreachable', 'AI_CLI_UNREACHABLE'],
  ] as const)('maps exact CLI state %s to stable %s without a model search', async (state, code) => {
    respond(sql => {
      if (sql.includes('FROM profiles')) return [{ id: 'alice' }]
      if (sql.includes('FROM ai_cli_grants')) return [{ cli_id: 'claude_code', revoked_at: null }]
      if (sql.includes('FROM ai_cli_installations')) return [{ cli_id: 'claude_code', validation_state: state }]
    })
    const selected = { kind: 'explicit' as const, choice: { kind: 'local_cli' as const, cliId: 'claude_code' as const, modelId: 'exact-model' } }
    await expect(repository.loadRoutingResolution('alice', selected)).rejects.toMatchObject({ code })
    expect(calls().some(c => c.sql.includes('FROM ai_cli_models'))).toBe(false)
  })

  it('uses stable errors for an unavailable exact model and a malformed saved default', async () => {
    respond(sql => {
      if (sql.includes('FROM profiles')) return [{ id: 'alice' }]
      if (sql.includes('FROM ai_provider_connections')) return [safeConnection]
      if (sql.includes('FROM ai_connection_models')) return []
    })
    await expect(repository.loadRoutingResolution('alice', { kind: 'explicit', choice })).rejects.toMatchObject({ code: 'AI_MODEL_UNAVAILABLE' })
    execute.mockClear()
    respond(sql => {
      if (sql.includes('FROM profiles')) return [{ id: 'alice' }]
      if (sql.includes('FROM ai_user_defaults')) return [{ kind: 'provider_model', connection_id: null, model_id: null }]
    })
    await expect(repository.loadRoutingResolution('alice', { kind: 'default' })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
  })

  it.each([
    [{ kind: 'explicit', choice: { kind: 'provider_model', connectionId: 'not-a-uuid', modelId: 'model-a' } }, undefined, 'AI_CHOICE_BROKEN'],
    [{ kind: 'explicit', choice: { kind: 'custom_configuration', configurationId: 'not-a-uuid' } }, undefined, 'AI_CHOICE_BROKEN'],
    [{ kind: 'default' }, 'not-a-uuid', 'AI_PERMISSION_DENIED'],
  ] as const)('rejects malformed UUID-backed routing references before SQL', async (selection, conversation, code) => {
    await expect(repository.loadRoutingResolution('alice', selection, conversation)).rejects.toMatchObject({ code })
    expect(execute).not.toHaveBeenCalled()
  })
})

describe('atomic Pariprashna selected-to-Default fallback preparation', () => {
  const selectedModel = 'model-selected'
  const defaultModel = 'model-default'
  const turnId = '00000000-0000-4000-8000-000000000099'

  it('pins an explicit selection and its Default fallback as two linked immutable snapshots', async () => {
    respond((sql, params) => {
      if (sql.includes('FROM profiles')) return [{ id: 'alice' }]
      if (sql === 'SELECT owner_id FROM charts WHERE id=$1 FOR SHARE') return [{ owner_id: 'alice' }]
      if (sql.includes('FROM conversations') && sql.includes('FOR NO KEY UPDATE')) {
        return [{ id: conversationId, chart_id: conversationId }]
      }
      if (sql.includes('FROM ai_conversation_selections')) return [{ kind: 'provider_model',
        connection_id: connectionId, model_id: selectedModel, configuration_id: null, cli_id: null }]
      if (sql.includes('FROM ai_user_defaults')) return [{ kind: 'provider_model',
        connection_id: connectionId, model_id: defaultModel, configuration_id: null, cli_id: null }]
      if (sql.includes('FROM ai_provider_connections')) return [safeConnection]
      if (sql.includes('FROM ai_connection_models')) return [{ model_id: params[1], display_name: String(params[1]),
        compatible_roles: AI_ROLES, available: true, supports_tools: true, supports_structured_output: true }]
      if (sql.startsWith('INSERT INTO ai_turn_routing_snapshots')) {
        return [{ id: params[1] === turnId ? '30000000-0000-4000-8000-000000000003'
          : '30000000-0000-4000-8000-000000000004' }]
      }
      return undefined
    })

    const prepared = await repository.prepareTurnRouting({ userId: 'alice', role: 'guest',
      chartId: conversationId, conversationId, isFirstTurn: false, turnId,
      source: 'pariprashna', selection: { kind: 'explicit', choice: {
        kind: 'provider_model', connectionId, modelId: selectedModel,
      } } })

    expect(prepared.safeSnapshot).toMatchObject({ correlationId: turnId,
      resolvedChoice: { kind: 'provider_model', connectionId, modelId: selectedModel } })
    expect(prepared.fallback?.safeSnapshot).toMatchObject({
      correlationId: `${turnId}:default-fallback`,
      selection: { kind: 'default' },
      resolvedChoice: { kind: 'provider_model', connectionId, modelId: defaultModel },
    })
    const snapshotWrites = calls().filter(call => call.sql.startsWith('INSERT INTO ai_turn_routing_snapshots'))
    expect(snapshotWrites.map(call => call.params[1])).toEqual([turnId, `${turnId}:default-fallback`])
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
    await expect(repository.insertRoleInvocationReceipt({ userId: 'mallory', snapshotId: configurationId,
      invocationId: crypto.randomUUID(), role: 'planner', phase: 'start', status: 'started' })).rejects.toMatchObject({ code: 'AI_PERMISSION_DENIED' })
    expect(calls().some(c => c.sql.includes('user_id=$1') && c.params[0] === 'mallory')).toBe(true)
  })
  it('accepts identical receipt retries but rejects changed terminal results', async () => {
    respond(sql => {
      if (sql.startsWith('SELECT id FROM ai_turn_routing_snapshots')) return [{ id: configurationId }]
      if (sql.includes('FROM ai_turn_role_invocations')) return [{ status: 'succeeded', error_code: null }]
    })
    const receipt = { userId: 'alice', snapshotId: configurationId, invocationId: crypto.randomUUID(),
      role: 'planner', phase: 'terminal', status: 'succeeded' }
    await repository.insertRoleInvocationReceipt(receipt)
    expect(calls().some(c => c.sql.includes('ON CONFLICT(snapshot_id,role,invocation_id,phase) DO NOTHING'))).toBe(true)
    await expect(repository.insertRoleInvocationReceipt({ ...receipt, status: 'failed' })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(calls().some(c => c.sql.startsWith('UPDATE'))).toBe(false)
  })
  it('rejects audit content outside closed identifiers and event vocabulary', async () => {
    expect(audit).toHaveProperty('writeAiAudit')
    await expect(audit.writeAiAudit(client, 'alice', { event: 'connection_renamed', connectionId, prompt: 'forbidden' })).rejects.toBeDefined()
    expect(execute).not.toHaveBeenCalled()
    await audit.writeAiAudit(client, 'alice', { event: 'connection_renamed', connectionId })
    expect(calls()[0].params).toEqual(['alice', 'connection_renamed', connectionId, null, null, null, null])
    execute.mockClear()
    await expect(audit.writeAiAudit(client, 'alice', { event: 'connection_validation_rejected',
      connectionId, errorCode: 'AI_CONNECTION_INVALID', message: 'raw upstream body' })).rejects.toBeDefined()
    expect(execute).not.toHaveBeenCalled()
    await audit.writeAiAudit(client, 'alice', { event: 'connection_validation_rejected',
      connectionId, errorCode: 'AI_CONNECTION_INVALID' })
    expect(calls()[0].params).toEqual(['alice', 'connection_validation_rejected', connectionId,
      null, null, null, 'AI_CONNECTION_INVALID'])
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

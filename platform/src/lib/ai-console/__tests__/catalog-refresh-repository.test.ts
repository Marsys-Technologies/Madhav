import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { Pool } from 'pg'
import * as repository from '../repository'
import { AI_ROLES } from '../types'

// Only PostgreSQL transport is replaced. Run real DAO validation, ownership,
// transactions, SQL fences, catalogue updates and audit parameter mapping.
const execute = vi.fn()
const release = vi.fn()
const client = { query: execute, release }
const connect = vi.fn(async () => client)
const globals = globalThis as typeof globalThis & { __pgPool?: Pool }
const id = '11111111-1111-4111-8111-111111111111'
const version = 3
const epoch = '12'
const connection = { id, provider_id: 'anthropic', credential_version: version,
  credential_validity: 'valid', validation_state: 'validated', deleted_at: null }
const model = { modelId: 'claude-new-model', displayName: 'Claude New Model', compatibleRoles: [...AI_ROLES],
  supportsTools: false, supportsStructuredOutput: true, supportedEfforts: ['low', 'high', 'max'], defaultEffort: null }
const sqlCalls = () => execute.mock.calls.map(([sql, params = []]) => ({
  sql: String(sql).replace(/\s+/g, ' ').trim(), params: params as unknown[],
}))
function transport(handler: (sql: string, params: unknown[]) => Record<string, unknown>[] | undefined) {
  execute.mockImplementation(async (sql: string, params: unknown[] = []) => {
    const rows = handler(sql.replace(/\s+/g, ' ').trim(), params) ?? []
    return { rows, rowCount: rows.length }
  })
}
function ownConnection(row = connection, acceptsWrite = true) {
  transport(sql => {
    if (sql.startsWith('SELECT') && sql.includes('FROM ai_provider_connections')) return [row]
    if (sql.startsWith('UPDATE ai_provider_connections') && sql.includes('RETURNING')) return acceptsWrite
      ? [{ id, credential_version: version, provider_id: 'anthropic', epoch }] : []
    return undefined
  })
}
beforeEach(() => {
  execute.mockReset().mockResolvedValue({ rows: [], rowCount: 0 })
  release.mockReset(); connect.mockClear()
  globals.__pgPool = { query: execute, connect } as unknown as Pool
})

describe('owned API catalogue refresh persistence', () => {
  it('claims only the active owner under transaction lock and returns a version/epoch fence', async () => {
    ownConnection()
    expect(await repository.claimConnectionCatalogRefresh('owner', id, true)).toEqual({
      credentialVersion: version, providerId: 'anthropic', epoch,
    })
    const calls = sqlCalls()
    expect(calls[0].sql).toBe('BEGIN')
    expect(calls[1].sql).toContain("'ai-console:user:'")
    expect(calls[1].params).toEqual(['owner'])
    const owned = calls.find(call => call.sql.startsWith('SELECT') && call.sql.includes('FROM ai_provider_connections'))!
    expect(owned.sql).toContain('user_id=$1 AND id=$2 AND deleted_at IS NULL FOR NO KEY UPDATE')
    expect(owned.params).toEqual(['owner', id])
    const claim = calls.find(call => call.sql.startsWith('UPDATE'))!
    expect(claim.sql).toContain("p.status='active'")
    expect(claim.sql).toContain('catalog_refresh_epoch=catalog_refresh_epoch+1')
    expect(claim.sql).toContain("interval '60 seconds'")
    expect(claim.sql).toContain("interval '15 minutes'")
    expect(claim.params).toEqual(['owner', id, true])
    expect(claim.sql).not.toContain('validation_state=')
    expect(calls.at(-1)?.sql).toBe('COMMIT')
    expect(release).toHaveBeenCalledOnce()
  })

  it('skips fresh, cooling-down or leased rows without touching models', async () => {
    ownConnection(connection, false)
    expect(await repository.claimConnectionCatalogRefresh('owner', id, false)).toBeNull()
    expect(sqlCalls().find(call => call.sql.startsWith('UPDATE'))?.params).toEqual(['owner', id, false])
    expect(sqlCalls().some(call => call.sql.includes('ai_connection_models'))).toBe(false)
  })

  it.each([
    { credential_validity: 'unknown' }, { credential_validity: 'invalid' },
    { validation_state: 'needs_attention' }, { provider_id: 'kimi' },
  ])('requires established credential validity for refresh', async overrides => {
    ownConnection({ ...connection, ...overrides })
    await expect(repository.claimConnectionCatalogRefresh('owner', id, true)).rejects.toMatchObject({ code: 'AI_CONNECTION_INVALID' })
    expect(sqlCalls().some(call => call.sql.startsWith('UPDATE'))).toBe(false)
    expect(sqlCalls().at(-1)?.sql).toBe('ROLLBACK')
  })

  it('rejects a missing or foreign connection before any claim/write', async () => {
    await expect(repository.claimConnectionCatalogRefresh('foreign', id, true)).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(sqlCalls().find(call => call.sql.includes('FROM ai_provider_connections'))?.params).toEqual(['foreign', id])
    expect(sqlCalls().some(call => call.sql.startsWith('UPDATE'))).toBe(false)
  })

  it('merges metadata and advertised efforts without modifying selection or probe evidence', async () => {
    ownConnection()
    expect(await repository.storeConnectionCatalogRefresh('owner', id, { credentialVersion: version, epoch, models: [model] })).toBe(true)
    const calls = sqlCalls()
    const fence = calls.find(call => call.sql.startsWith('UPDATE ai_provider_connections'))!
    expect(fence.sql).toContain('c.credential_version=$3 AND c.catalog_refresh_epoch=$4::bigint')
    expect(fence.sql).toContain('c.catalog_refresh_in_progress AND c.deleted_at IS NULL')
    expect(fence.sql).toContain("p.status='active'")
    expect(fence.params).toEqual(['owner', id, version, epoch, null, true, false])
    const retire = calls.find(call => call.sql.startsWith('UPDATE ai_connection_models'))!
    expect(retire.sql).toContain('SET available=false')
    expect(retire.params).toEqual(['owner', id])
    const insert = calls.find(call => call.sql.startsWith('INSERT INTO ai_connection_models'))!
    expect(insert.params).toEqual(['owner', id, model.modelId, model.displayName, AI_ROLES,
      false, true, ['low', 'high', 'max']])
    expect(insert.sql).toContain('supported_efforts=excluded.supported_efforts')
    const modelWrites = calls.filter(call => /^(?:UPDATE|INSERT INTO) ai_connection_models/.test(call.sql))
    for (const write of modelWrites) {
      expect(write.sql).not.toMatch(/user_selected\s*=|plain_tested_at\s*=|tested_credential_version\s*=|last_probe_\w+\s*=/)
    }
    expect(calls.some(call => call.sql.includes('ai_user_defaults') || call.sql.includes('ai_custom_configurations')
      || call.sql.includes('ai_conversation_selections'))).toBe(false)
  })

  it.each([undefined, []])('distinguishes absent effort metadata from explicit no support', async supportedEfforts => {
    ownConnection()
    await repository.storeConnectionCatalogRefresh('owner', id, { credentialVersion: version, epoch,
      models: [{ ...model, supportedEfforts }] })
    expect(sqlCalls().find(call => call.sql.startsWith('INSERT INTO ai_connection_models'))?.params.at(-1))
      .toEqual(supportedEfforts ?? null)
  })

  it('tombstones an authoritative empty catalogue while preserving saved selections', async () => {
    ownConnection()
    expect(await repository.storeConnectionCatalogRefresh('owner', id, { credentialVersion: version, epoch, models: [] })).toBe(true)
    expect(sqlCalls().some(call => call.sql.startsWith('UPDATE ai_connection_models'))).toBe(true)
    expect(sqlCalls().some(call => call.sql.startsWith('INSERT INTO ai_connection_models'))).toBe(false)
    expect(sqlCalls().some(call => call.sql.includes('ai_user_defaults'))).toBe(false)
  })

  it('does not write results after credential replacement', async () => {
    ownConnection({ ...connection, credential_version: 4 })
    expect(await repository.storeConnectionCatalogRefresh('owner', id, { credentialVersion: version, epoch, models: [model] })).toBe(false)
    expect(sqlCalls().some(call => call.sql.startsWith('UPDATE') || call.sql.startsWith('INSERT'))).toBe(false)
  })

  it('ignores a stale epoch, ended lease or inactive owner result before catalogue mutation', async () => {
    ownConnection(connection, false)
    expect(await repository.storeConnectionCatalogRefresh('owner', id, { credentialVersion: version, epoch, models: [model] })).toBe(false)
    expect(sqlCalls().some(call => call.sql.includes('ai_connection_models'))).toBe(false)
  })

  it.each(['AI_PROVIDER_UNREACHABLE', 'AI_RATE_LIMITED', 'AI_PERMISSION_DENIED', 'AI_EXECUTION_FAILED', 'AI_CONNECTION_INVALID'] as const)
  ('preserves catalogue/evidence on %s and invalidates credentials only for proven rejection', async errorCode => {
    ownConnection()
    expect(await repository.storeConnectionCatalogRefresh('owner', id, { credentialVersion: version, epoch, errorCode })).toBe(true)
    const fence = sqlCalls().find(call => call.sql.startsWith('UPDATE ai_provider_connections'))!
    expect(fence.params).toEqual(['owner', id, version, epoch, errorCode, false, errorCode === 'AI_CONNECTION_INVALID'])
    expect(fence.sql).toContain("credential_validity=CASE WHEN $7::boolean THEN 'invalid' ELSE credential_validity END")
    expect(fence.sql).toContain('catalog_refreshed_at=CASE WHEN $6::boolean THEN clock_timestamp() ELSE catalog_refreshed_at END')
    expect(sqlCalls().some(call => call.sql.includes('ai_connection_models'))).toBe(false)
  })

  it.each([
    { credentialVersion: version, epoch, models: [], errorCode: 'AI_RATE_LIMITED' },
    { credentialVersion: version, epoch },
    { credentialVersion: version, epoch: 'not-an-epoch', models: [] },
    { credentialVersion: version, epoch, models: [{ ...model, supportedEfforts: ['untrusted-level'] }] },
  ])('rejects malformed metadata before opening a transaction', async input => {
    await expect(repository.storeConnectionCatalogRefresh('owner', id, input)).rejects.toBeDefined()
    expect(connect).not.toHaveBeenCalled()
  })
})

describe('grant-gated host CLI catalogue refresh persistence', () => {
  function granted(accepted = true) {
    transport(sql => {
      if (sql.includes('FROM ai_cli_grants')) return [{ cli_id: 'codex' }]
      if (sql.startsWith('UPDATE ai_cli_installations')) return accepted ? [{ epoch, validation_epoch: '13' }] : []
      return undefined
    })
  }
  it('checks the live grant and active account before exposing host state or claiming a lease', async () => {
    granted()
    expect(await repository.claimCliCatalogRefresh('owner', 'codex', true)).toBe(epoch)
    const calls = sqlCalls()
    const grantIndex = calls.findIndex(call => call.sql.includes('FROM ai_cli_grants'))
    const hostIndex = calls.findIndex(call => call.sql.startsWith('INSERT INTO ai_cli_installations'))
    expect(grantIndex).toBeLessThan(hostIndex)
    expect(calls[grantIndex].sql).toContain("g.revoked_at IS NULL AND p.status='active' FOR SHARE OF g,p")
    expect(calls[grantIndex].params).toEqual(['owner', 'codex'])
    const lease = calls.find(call => call.sql.startsWith('UPDATE ai_cli_installations'))!
    expect(lease.sql).toContain("interval '60 seconds'")
    expect(lease.sql).toContain("interval '180 seconds'")
    expect(lease.sql).toContain("interval '15 minutes'")
    expect(lease.params).toEqual(['codex', true])
  })
  it('denies missing, revoked or inactive grants without reading the CLI installation', async () => {
    await expect(repository.claimCliCatalogRefresh('foreign', 'codex', false)).rejects.toMatchObject({ code: 'AI_CLI_NOT_GRANTED' })
    expect(sqlCalls().some(call => call.sql.includes('ai_cli_installations'))).toBe(false)
  })
  it('skips a fresh or leased host catalogue for an authorized user', async () => {
    granted(false)
    expect(await repository.claimCliCatalogRefresh('owner', 'codex', false)).toBeNull()
  })
  it.each([undefined, 'AI_CLI_UNREACHABLE'] as const)('releases only the matching host refresh epoch', async errorCode => {
    granted()
    expect(await repository.finishCliCatalogRefresh('codex', epoch, errorCode)).toBe(true)
    expect(sqlCalls()[0].sql).toContain('catalog_refresh_epoch=$2::bigint AND catalog_refresh_in_progress')
    expect(sqlCalls()[0].params).toEqual(['codex', epoch, errorCode ?? null])
  })
  it('does not acknowledge release of a stale host epoch', async () => {
    expect(await repository.finishCliCatalogRefresh('codex', epoch)).toBe(false)
  })
  it('stores discovered model/effort/default metadata and restores manual models only for the same version and binary', async () => {
    granted()
    const sha = 'a'.repeat(64)
    expect(await repository.storeCliValidation('codex', { state: 'reachable', detectedProduct: 'CODEX CLI',
      detectedVersion: '0.155.1', entrypointSha256: sha, models: [{ modelId: 'gpt-6-astra', displayName: 'GPT 6 Astra',
        compatibleRoles: [...AI_ROLES], supportsTools: true, supportsStructuredOutput: true, isBuiltinDefault: false,
        supportedEfforts: ['low', 'medium', 'high', 'xhigh', 'max', 'ultra'], defaultEffort: 'medium', isCatalogDiscovered: true }] }, epoch))
      .toBe('13')
    const calls = sqlCalls()
    const installation = calls.find(call => call.sql.startsWith('UPDATE ai_cli_installations'))!
    expect(installation.sql).toContain('WHERE cli_id=$1 AND xmin::text=$6')
    expect(installation.params).toEqual(['codex', 'CODEX CLI', '0.155.1', 'reachable', null, epoch, sha, true])
    const models = calls.find(call => call.sql.startsWith('INSERT INTO ai_cli_models'))!
    expect(models.params).toEqual(['codex', 'gpt-6-astra', 'GPT 6 Astra', false, AI_ROLES, true, true,
      ['low', 'medium', 'high', 'xhigh', 'max', 'ultra'], 'medium', true])
    expect(models.sql).toContain('supported_efforts=excluded.supported_efforts,default_effort=excluded.default_effort')
    expect(models.sql).not.toMatch(/tested_version\s*=|tested_entrypoint_sha256\s*=|is_manual\s*=/)
    const manual = calls.find(call => call.sql.includes('AND is_manual=true'))!
    expect(manual.sql).toContain('tested_version=$2 AND tested_entrypoint_sha256=$3')
    expect(manual.params).toEqual(['codex', '0.155.1', sha])
  })
  it('preserves the previous CLI catalogue on a health check failure without fresh metadata', async () => {
    granted()
    await repository.storeCliValidation('codex', { state: 'unreachable', errorCode: 'AI_CLI_UNREACHABLE' }, epoch)
    expect(sqlCalls().some(call => call.sql.includes('ai_cli_models'))).toBe(false)
    const write = sqlCalls().find(call => call.sql.startsWith('UPDATE ai_cli_installations'))!
    expect(write.params.at(-1)).toBe(false)
  })
  it('ignores a stale installation epoch before replacing models', async () => {
    granted(false)
    expect(await repository.storeCliValidation('codex', { state: 'reachable', models: [] }, epoch)).toBeNull()
    expect(sqlCalls().some(call => call.sql.includes('ai_cli_models'))).toBe(false)
  })
})

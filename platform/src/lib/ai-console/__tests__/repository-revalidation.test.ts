import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { Pool } from 'pg'
import * as repository from '../repository'
import { AiConsoleError } from '../errors'

const execute = vi.fn()
const client = { query: execute, release: vi.fn() }
const id = '00000000-0000-4000-8000-000000000001'
const calls = () => execute.mock.calls.map(([sql, params]) => ({ sql: String(sql).replace(/\s+/g, ' '), params }))
beforeEach(() => {
  execute.mockReset().mockResolvedValue({ rows: [], rowCount: 0 });
  (globalThis as typeof globalThis & { __pgPool?: Pool }).__pgPool = { connect: async () => client, query: execute } as unknown as Pool
})
describe('bounded repository-owned revalidation leases', () => {
  it('authorizes one exact active request without returning crypto or holding a transaction', async () => {
    execute.mockResolvedValue({ rows: [{ id }], rowCount: 1 })
    expect(await repository.assertConnectionRequestAuthorized({ userId: 'alice', connectionId: id, providerId: 'openai', credentialVersion: 2 })).toBeUndefined()
    expect(calls()).toHaveLength(1)
    expect(calls()[0].params).toEqual(['alice', id, 'openai', 2])
    expect(calls()[0].sql).toContain('c.user_id=$1 AND c.id=$2 AND c.provider_id=$3 AND c.credential_version=$4')
    expect(calls()[0].sql).toContain("p.status='active'")
    expect(calls()[0].sql).toContain('c.deleted_at IS NULL')
    expect(calls()[0].sql).not.toMatch(/credential_ciphertext|wrapped_dek|FOR UPDATE|BEGIN/)
  })
  it('refuses unauthorized request preflights and invalid input', async () => {
    await expect(repository.assertConnectionRequestAuthorized({ userId: 'alice', connectionId: id, providerId: 'openai', credentialVersion: 2 })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    execute.mockClear()
    await expect(repository.assertConnectionRequestAuthorized({ userId: 'alice', connectionId: id, providerId: 'openai', credentialVersion: 0 })).rejects.toBeDefined()
    expect(execute).not.toHaveBeenCalled()
  })
  it('authorizes only the exact available runtime model on a not-invalid credential', async () => {
    execute.mockResolvedValue({ rows: [{ id }], rowCount: 1 })
    expect(await repository.assertRuntimeModelRequestAuthorized({ userId: 'alice', connectionId: id,
      providerId: 'openai', credentialVersion: 2, modelId: 'gpt-4.1-mini' })).toBeUndefined()
    expect(calls()).toHaveLength(1)
    expect(calls()[0].params).toEqual(['alice', id, 'openai', 2, 'gpt-4.1-mini'])
    expect(calls()[0].sql).toContain("c.credential_validity<>'invalid'")
    expect(calls()[0].sql).toContain('m.connection_id=c.id')
    expect(calls()[0].sql).toContain('m.model_id=$5')
    expect(calls()[0].sql).toContain('m.available=true')
  })
  it('rejects unavailable runtime models and malformed runtime target IDs without SQL fallback', async () => {
    await expect(repository.assertRuntimeModelRequestAuthorized({ userId: 'alice', connectionId: id,
      providerId: 'openai', credentialVersion: 2, modelId: 'removed-model' })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(calls()).toHaveLength(1)
    execute.mockClear()
    await expect(repository.assertRuntimeModelRequestAuthorized({ userId: 'alice', connectionId: 'not-a-uuid',
      providerId: 'openai', credentialVersion: 2, modelId: 'gpt-4.1-mini' })).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(execute).not.toHaveBeenCalled()
  })
  it('atomically loads only the redacted encrypted credential for one exact authorized runtime model', async () => {
    const row = { credential_ciphertext: Buffer.from('cipher'), credential_nonce: Buffer.alloc(12),
      credential_tag: Buffer.alloc(16), wrapped_dek: Buffer.alloc(32), wrap_nonce: Buffer.alloc(12),
      wrap_tag: Buffer.alloc(16), kek_version: 'test', masked_suffix: '••••1234', keyed_fingerprint: 'f'.repeat(64),
      provider_id: 'never-project', model_id: 'never-project', credential_version: 999 }
    execute.mockResolvedValue({ rows: [row], rowCount: 1 })
    const record = await repository.loadRuntimeModelCredential({ userId: 'alice', connectionId: id,
      providerId: 'openai', credentialVersion: 2, modelId: 'gpt-4.1-mini' })
    expect(calls()).toHaveLength(1)
    expect(calls()[0].params).toEqual(['alice', id, 'openai', 2, 'gpt-4.1-mini'])
    expect(calls()[0].sql).toContain('JOIN ai_connection_models m ON m.connection_id=c.id AND m.model_id=$5')
    expect(calls()[0].sql).toContain("c.credential_validity<>'invalid'")
    expect(calls()[0].sql).toContain('m.available=true')
    expect(Object.keys(record).sort()).toEqual([
      'authTag', 'ciphertext', 'fingerprint', 'keyVersion', 'mask', 'nonce',
      'wrapAuthTag', 'wrapNonce', 'wrappedDataKey',
    ])
    expect(JSON.stringify(record)).toBe('"[REDACTED]"')
    expect(JSON.stringify(record)).not.toContain('never-project')
  })
  it('returns no credential when exact runtime authorization loses the model or confirmed validity', async () => {
    for (const target of [
      { userId: 'alice', connectionId: id, providerId: 'openai' as const, credentialVersion: 2, modelId: 'removed' },
      { userId: 'alice', connectionId: id, providerId: 'openai' as const, credentialVersion: 3, modelId: 'gpt-4.1-mini' },
    ]) {
      await expect(repository.loadRuntimeModelCredential(target)).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    }
    expect(calls()).toHaveLength(2)
    expect(calls().every(c => c.sql.includes('ai_connection_models'))).toBe(true)
  })
  it('atomically claims active stale noninvalid connections with skip-locked recovery and safe projection', async () => {
    execute.mockImplementation(async (sql: string) => ({ rows: sql.includes('RETURNING') ? [{ user_id: 'alice', id, provider_id: 'openai', credential_version: '2', credential_ciphertext: 'never-return' }] : [] }))
    const staleBefore = new Date(Date.now() - 86_400_000)
    expect(await repository.claimStaleConnectionRevalidations({ staleBefore, limit: 5 })).toEqual([{ userId: 'alice', connectionId: id, providerId: 'openai', credentialVersion: 2 }])
    const claim = calls().find(c => c.sql.includes('SKIP LOCKED'))!
    expect(claim.sql).toMatch(/FOR UPDATE OF c SKIP LOCKED/)
    expect(claim.sql).toContain("p.status='active'")
    expect(claim.sql).toContain('c.deleted_at IS NULL')
    expect(claim.sql).toContain("c.credential_validity<>'invalid'")
    expect(claim.sql).toContain('c.last_checked_at < $1')
    expect(claim.sql).not.toContain("validation_state<>'validating'")
    expect(claim.sql).toContain("validation_state='validating',last_checked_at=now()")
    expect(claim.params).toEqual([staleBefore, 5])
    expect(calls()[0].sql).toBe('BEGIN')
    expect(calls().at(-1)?.sql).toBe('COMMIT')
    expect(calls().filter(c => c.sql.includes('SKIP LOCKED'))).toHaveLength(1)
  })
  it.each([0, -1, 26, 1.2, Infinity])('rejects unsafe batch limit %s before SQL', async limit => {
    await expect(repository.claimStaleConnectionRevalidations({ staleBefore: new Date(0), limit })).rejects.toBeDefined()
    expect(execute).not.toHaveBeenCalled()
  })
  it('rejects future/invalid lease cutoffs', async () => {
    for (const staleBefore of [new Date(NaN), new Date(Date.now() + 100_000)]) {
      await expect(repository.claimStaleConnectionRevalidations({ staleBefore, limit: 1 })).rejects.toBeDefined()
    }
    expect(execute).not.toHaveBeenCalled()
  })
  it.each([
    ['AI_CONNECTION_INVALID', 'invalid'], ['AI_MODEL_UNAVAILABLE', 'needs_attention'],
    ['AI_ROLE_INCOMPATIBLE', 'needs_attention'], ['AI_PERMISSION_DENIED', 'needs_attention'],
    ['AI_BILLING_UNAVAILABLE', 'needs_attention'], ['AI_RATE_LIMITED', 'unreachable'],
    ['AI_PROVIDER_UNREACHABLE', 'unreachable'],
  ] as const)('marks exact connection for %s without rewriting its catalog', async (code, state) => {
    execute.mockImplementation(async (sql: string) => ({ rows: sql.includes('RETURNING') ? [{ id }] : [] }))
    await repository.markConnectionForRevalidation('alice', id, 2, new AiConsoleError(code).toJSON())
    const update = calls().find(c => c.sql.includes('UPDATE ai_provider_connections'))!
    expect(update.params).toEqual(['alice', id, 2, state, code])
    expect(update.sql).toContain('c.user_id=$1 AND c.id=$2 AND c.credential_version=$3')
    expect(update.sql).toContain("p.status='active'")
    expect(update.sql).toContain('c.deleted_at IS NULL')
    expect(update.sql).toContain("CASE WHEN $5='AI_CONNECTION_INVALID' THEN 'invalid' ELSE credential_validity END")
    expect(update.sql).toContain('last_checked_at=now()')
    expect(calls().some(c => c.sql.includes('ai_connection_models'))).toBe(false)
  })
  it('rejects stale, foreign, disabled or deleted targets without an audit write', async () => {
    await expect(repository.markConnectionForRevalidation('mallory', id, 1, new AiConsoleError('AI_MODEL_UNAVAILABLE').toJSON())).rejects.toMatchObject({ code: 'AI_CHOICE_BROKEN' })
    expect(calls().at(-1)?.sql).toBe('ROLLBACK')
    expect(calls().some(c => c.sql.includes('INSERT'))).toBe(false)
  })
  it('does not accept unnormalized bodies or unrelated CLI codes', async () => {
    for (const error of [{ code: 'AI_CONNECTION_INVALID', body: 'secret' }, new AiConsoleError('AI_CLI_UNREACHABLE').toJSON()]) {
      await expect(repository.markConnectionForRevalidation('alice', id, 1, error)).rejects.toBeDefined()
    }
    expect(execute).not.toHaveBeenCalled()
  })
})

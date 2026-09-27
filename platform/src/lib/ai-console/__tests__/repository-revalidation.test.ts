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

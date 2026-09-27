import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { Pool } from 'pg'
import * as repository from '../../repository'
import { AI_ROLES } from '../../types'

const execute = vi.fn()
const release = vi.fn()
const connect = vi.fn(async () => ({ query: execute, release }))
const globalPool = globalThis as typeof globalThis & { __pgPool?: Pool }

beforeEach(() => {
  execute.mockReset().mockResolvedValue({ rows: [], rowCount: 0 })
  release.mockReset(); connect.mockClear()
  globalPool.__pgPool = { connect, query: execute } as unknown as Pool
})

describe('CLI repository boundary', () => {
  it('checks the exact active grant without selecting host state', async () => {
    await expect(repository.assertCliValidationAuthorized('alice', 'codex'))
      .rejects.toMatchObject({ code: 'AI_CLI_NOT_GRANTED' })
    const [sql, params] = execute.mock.calls[0]
    expect(sql).not.toMatch(/validation_state|detected_|last_error/)
    expect(params).toEqual(['alice', 'codex'])
  })

  it('allows grant-authorized validation spawn without claiming execution reachability', async () => {
    execute.mockImplementation(async (sql: string) => ({ rows: sql.includes('ai_cli_grants') ? [{ cli_id: 'claude_code' }] : [] }))
    const start = vi.fn(() => ({ pid: 42, cancel: vi.fn() }))
    await repository.withCliInvocationAuthorization('alice', 'claude_code', start, 'validation')
    const sql = execute.mock.calls.find(([value]) => String(value).includes('ai_cli_grants'))?.[0] as string
    expect(sql).not.toContain("i.validation_state='reachable'")
    expect(start).toHaveBeenCalledOnce()
  })

  it('atomically replaces safe global state and the built-in catalog', async () => {
    execute.mockImplementation(async (sql: string) => ({ rows: sql.includes('UPDATE ai_cli_installations')
      ? [{ validation_epoch: '43' }] : [], rowCount: sql.includes('UPDATE ai_cli_installations') ? 1 : 0 }))
    await repository.storeCliValidation('codex', {
      state: 'reachable', detectedProduct: 'Codex CLI', detectedVersion: '0.155.1',
      models: [{ modelId: '__madhav_builtin_default__', displayName: 'Built-in default',
        compatibleRoles: AI_ROLES, supportsTools: false, supportsStructuredOutput: true, isBuiltinDefault: true }],
    }, '42')
    const calls = execute.mock.calls.map(([sql, params]) => ({ sql: String(sql).replace(/\s+/g, ' '), params }))
    expect(calls[0].sql).toContain('BEGIN')
    expect(calls.some(call => call.sql.includes('pg_advisory_xact_lock'))).toBe(true)
    expect(calls.some(call => call.sql.includes('UPDATE ai_cli_models SET available=false'))).toBe(true)
    const model = calls.find(call => call.sql.includes('INSERT INTO ai_cli_models'))!
    expect(model.params).toContain('__madhav_builtin_default__')
    expect(model.params).not.toContain('prompt')
    expect(calls.at(-1)?.sql).toContain('COMMIT')
  })

  it('claims revalidation without replacing the last confirmed terminal state or catalog', async () => {
    execute.mockImplementation(async (sql: string) => ({ rows: sql.includes('RETURNING xmin::text')
      ? [{ validation_epoch: '42' }] : sql.includes('SELECT validation_state')
        ? [{ validation_state: 'reachable', detected_product: 'Claude Code', detected_version: '2.1.56',
          last_checked_at: new Date('2026-09-27T00:00:00Z'), last_error_code: null }] : [], rowCount: 1 }))
    const attempt = await repository.markCliValidationStarted('claude_code')
    const sql = execute.mock.calls.map(([value]) => String(value)).join('\n')
    expect(sql).toContain('RETURNING xmin::text AS validation_epoch')
    expect(sql).not.toMatch(/SET\s+validation_state='validating'/)
    expect(sql).not.toMatch(/DELETE|available=false/)
    expect(attempt).toMatchObject({ cliId: 'claude_code', epoch: '42',
      previous: { state: 'reachable', detectedVersion: '2.1.56' } })
  })

  it('falls back to untested when superseding an orphaned validating attempt', async () => {
    execute.mockImplementation(async (sql: string) => ({ rows: sql.includes('RETURNING xmin::text')
      ? [{ validation_epoch: '42' }] : sql.includes('SELECT validation_state')
        ? [{ validation_state: 'validating', detected_product: 'Claude Code', detected_version: '2.1.56',
          last_checked_at: new Date('2026-09-27T00:00:00Z'), last_error_code: null }] : [], rowCount: 1 }))
    await expect(repository.markCliValidationStarted('claude_code')).resolves.toMatchObject({ previous: {
      state: 'untested', detectedProduct: null, detectedVersion: null, lastCheckedAt: null, errorCode: null,
    } })
  })

  it('rejects a stale validation completion without touching the catalog', async () => {
    execute.mockResolvedValue({ rows: [], rowCount: 0 })
    await expect(repository.storeCliValidation('claude_code', { state: 'reachable' }, '41'))
      .resolves.toBeNull()
    const sql = execute.mock.calls.map(([value]) => String(value).replace(/\s+/g, ' '))
    expect(sql.some(value => value.includes('xmin::text=$6'))).toBe(true)
    expect(sql.some(value => value.includes('UPDATE ai_cli_models'))).toBe(false)
  })

  it('restores the prior global state only while the same validation attempt is current', async () => {
    execute.mockResolvedValue({ rows: [{ cli_id: 'claude_code' }], rowCount: 1 })
    const restored = await repository.restoreCliValidation({ cliId: 'claude_code', epoch: '42', previous: {
      state: 'reachable', detectedProduct: 'Claude Code', detectedVersion: '2.1.56',
      lastCheckedAt: new Date('2026-09-27T00:00:00Z'), errorCode: null,
    } })
    expect(restored).toBe(true)
    const [sql, params] = execute.mock.calls.find(([value]) => String(value).includes('UPDATE ai_cli_installations'))!
    expect(String(sql)).toContain('xmin::text=$7')
    expect(params).toEqual(['claude_code', 'Claude Code', '2.1.56', 'reachable',
      new Date('2026-09-27T00:00:00Z'), null, '42'])
    expect(execute.mock.calls.some(([value]) => String(value).includes('ai_cli_models'))).toBe(false)
  })

  it('creates the closed installation identity before granting it', async () => {
    execute.mockImplementation(async (sql: string) => ({ rows: sql.includes("role='super_admin'")
      || sql.includes('SELECT id FROM profiles') || sql.includes('RETURNING user_id') ? [{ id: 'x', user_id: 'alice' }] : [] }))
    await repository.setCliGrant('admin', 'alice', 'codex', true)
    const sql = execute.mock.calls.map(([value]) => String(value).replace(/\s+/g, ' '))
    expect(sql.findIndex(value => value.includes('INSERT INTO ai_cli_installations')))
      .toBeLessThan(sql.findIndex(value => value.includes('INSERT INTO ai_cli_grants')))
  })
})

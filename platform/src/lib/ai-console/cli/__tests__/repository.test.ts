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
    execute.mockImplementation(async (sql: string) => ({ rows: sql.includes('ai_cli_grants') ? [{ cli_id: 'codex' }] : [] }))
    const start = vi.fn(() => ({ pid: 42, cancel: vi.fn() }))
    await repository.withCliInvocationAuthorization('alice', 'codex', start, 'validation')
    const sql = execute.mock.calls.find(([value]) => String(value).includes('ai_cli_grants'))?.[0] as string
    expect(sql).not.toContain("i.validation_state='reachable'")
    expect(start).toHaveBeenCalledOnce()
  })

  it('atomically replaces safe global state and the built-in catalog', async () => {
    await repository.storeCliValidation('codex', {
      state: 'reachable', detectedProduct: 'Codex CLI', detectedVersion: '0.155.1',
      models: [{ modelId: '__madhav_builtin_default__', displayName: 'Built-in default',
        compatibleRoles: AI_ROLES, supportsTools: false, supportsStructuredOutput: true, isBuiltinDefault: true }],
    })
    const calls = execute.mock.calls.map(([sql, params]) => ({ sql: String(sql).replace(/\s+/g, ' '), params }))
    expect(calls[0].sql).toContain('BEGIN')
    expect(calls.some(call => call.sql.includes('pg_advisory_xact_lock'))).toBe(true)
    expect(calls.some(call => call.sql.includes('UPDATE ai_cli_models SET available=false'))).toBe(true)
    const model = calls.find(call => call.sql.includes('INSERT INTO ai_cli_models'))!
    expect(model.params).toContain('__madhav_builtin_default__')
    expect(model.params).not.toContain('prompt')
    expect(calls.at(-1)?.sql).toContain('COMMIT')
  })

  it('publishes validating without clearing the last known safe catalog', async () => {
    await repository.markCliValidationStarted('codex')
    const sql = execute.mock.calls[0][0] as string
    expect(sql).toContain("validation_state='validating'")
    expect(sql).not.toMatch(/DELETE|available=false/)
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

import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { Pool } from 'pg'
import * as repository from '../repository'
import { AI_ROLES } from '../types'

// The prepare-time revalidation calls validateCli through a dynamic import (the
// module imports the repository, so a static cycle is impossible); mocked here.
const validateCli = vi.fn()
vi.mock('@/lib/ai-console/cli/validation', () => ({ validateCli: (...args: unknown[]) => validateCli(...args) }))

const execute = vi.fn()
const release = vi.fn()
const client = { query: execute, release }
const connect = vi.fn(async () => client)
const globalPool = globalThis as typeof globalThis & { __pgPool?: Pool }

// Mutable latch state: what the ai_cli_installations row answers.
let storedState: string
let lastCheckedAt: Date | null

beforeEach(() => {
  execute.mockReset().mockResolvedValue({ rows: [], rowCount: 0 })
  release.mockReset()
  connect.mockClear()
  validateCli.mockReset()
  storedState = 'reachable'
  lastCheckedAt = null
  globalPool.__pgPool = { connect, query: execute } as unknown as Pool
})

function respond() {
  execute.mockImplementation(async (sql: string) => {
    const text = String(sql).replace(/\s+/g, ' ').trim()
    let rows: Record<string, unknown>[] = []
    if (text.includes('FROM profiles')) rows = [{ id: 'alice' }]
    else if (text.includes('FROM ai_cli_grants')) rows = [{ cli_id: 'claude_code', revoked_at: null }]
    else if (text.includes('FROM ai_cli_installations') && text.includes('FOR SHARE')) {
      rows = [{ cli_id: 'claude_code', validation_state: storedState }]
    } else if (text.includes('FROM ai_cli_installations')) {
      rows = [{ validation_state: storedState, last_checked_at: lastCheckedAt }]
    } else if (text.includes('FROM ai_cli_models')) {
      rows = [{ model_id: '__builtin_default__', display_name: 'Built-in default', compatible_roles: AI_ROLES,
        supports_tools: true, supports_structured_output: true, available: true, is_builtin_default: true,
        supported_efforts: [], is_catalog_discovered: false, is_manual: false }]
    }
    return { rows, rowCount: rows.length }
  })
}

const selection = { kind: 'explicit' as const, choice: { kind: 'local_cli' as const, cliId: 'claude_code' as const, modelId: null } }
const calls = () => execute.mock.calls.map(([sql]) => String(sql).replace(/\s+/g, ' ').trim())

describe('prepare-time revalidation of a latched CLI installation', () => {
  it('leaves the reachable path untouched: no revalidation, one transaction', async () => {
    respond()
    storedState = 'reachable'
    const resolution = await repository.loadRoutingResolution('alice', selection)
    expect(resolution.roles.worker).toMatchObject({ kind: 'local_cli', cliId: 'claude_code' })
    expect(validateCli).not.toHaveBeenCalled()
    expect(calls().filter(sql => sql === 'BEGIN')).toHaveLength(1)
    expect(calls().at(-1)).toBe('COMMIT')
  })

  it('recovers a latched installation: one bounded revalidation, then the prepare proceeds', async () => {
    respond()
    storedState = 'unreachable'
    validateCli.mockImplementation(async () => {
      storedState = 'reachable'              // validateCli publishes the recovery itself
      lastCheckedAt = new Date()
      return { state: 'reachable' }
    })
    const resolution = await repository.loadRoutingResolution('alice', selection)
    expect(resolution.roles.worker).toMatchObject({ kind: 'local_cli', cliId: 'claude_code' })
    expect(validateCli).toHaveBeenCalledTimes(1)
    const [, , signal] = validateCli.mock.calls[0]
    expect(signal).toBeInstanceOf(AbortSignal)
    // the whole prepare ran twice: latched attempt rolled back, recovery committed
    expect(calls().filter(sql => sql === 'BEGIN')).toHaveLength(2)
    expect(calls().at(-1)).toBe('COMMIT')
  })

  it('attempts revalidation once when the CLI is still down, then is rate-limited', async () => {
    respond()
    storedState = 'unreachable'
    lastCheckedAt = null
    validateCli.mockImplementation(async () => {
      lastCheckedAt = new Date()              // every validateCli write refreshes last_checked_at
      return { state: 'unreachable', modelCount: 0 }
    })
    await expect(repository.loadRoutingResolution('alice', selection))
      .rejects.toMatchObject({ code: 'AI_CLI_UNREACHABLE', message: 'The selected CLI could not be reached. Test its connection before trying again.' })
    expect(validateCli).toHaveBeenCalledTimes(1)
    // a second prepare within the interval makes NO new attempt and answers identically
    await expect(repository.loadRoutingResolution('alice', selection))
      .rejects.toMatchObject({ code: 'AI_CLI_UNREACHABLE', message: 'The selected CLI could not be reached. Test its connection before trying again.' })
    expect(validateCli).toHaveBeenCalledTimes(1)
  })

  it('treats a revalidation that throws like a failed attempt (same code as today)', async () => {
    respond()
    storedState = 'unreachable'
    validateCli.mockRejectedValue(new Error('bridge refused'))
    await expect(repository.loadRoutingResolution('alice', selection))
      .rejects.toMatchObject({ code: 'AI_CLI_UNREACHABLE' })
    expect(validateCli).toHaveBeenCalledTimes(1)
  })

  it('does not revalidate inside the user transaction', async () => {
    respond()
    storedState = 'unreachable'
    validateCli.mockResolvedValue({ state: 'unreachable', modelCount: 0 })
    await expect(repository.loadRoutingResolution('alice', selection)).rejects.toBeDefined()
    const order = calls()
    const rollback = order.indexOf('ROLLBACK')
    const installationProbe = order.findIndex(sql => sql.includes('FROM ai_cli_installations') && !sql.includes('FOR SHARE'))
    expect(rollback).toBeGreaterThan(-1)
    expect(installationProbe).toBeGreaterThan(rollback)   // the revalidation read runs after the failed txn
  })
})

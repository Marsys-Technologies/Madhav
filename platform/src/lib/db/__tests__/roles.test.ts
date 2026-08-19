/**
 * P1 G1-C — unit suite for the serving-side role/chart-context module.
 *
 * The one claim these tests are here to make falsifiable is the flag-off claim:
 * "with PARIPRASHNA_ROLE_SEPARATION off, nothing in this lane changes what the
 * app does." That is asserted by MEASURING the statements issued and the pool
 * identity, not by reading the code and agreeing with it.
 */

import { afterEach, describe, expect, it, vi } from 'vitest'

import { configService } from '@/lib/config/index'
import {
  CHART_CONTEXT_GUC,
  InvalidChartContextError,
  PARIPRASHNA_DB_ROLES,
  PRINCIPAL_ID_GUC,
  ROLE_SEPARATION_FLAG,
  ServeRoleNotConfiguredError,
  assertChartContextValue,
  getServeReadPool,
  isRoleSeparationEnabled,
  withChartContext,
} from '../roles'
import { getPool } from '../client'

vi.mock('../client', () => ({ getPool: vi.fn() }))

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

/** A pool whose clients record every statement. */
function fakePool() {
  const statements: Array<{ sql: string; params?: unknown[] }> = []
  const client = {
    query: vi.fn(async (sql: string, params?: unknown[]) => {
      statements.push({ sql, params })
      return { rows: [], rowCount: 0 }
    }),
    release: vi.fn(),
  }
  return {
    statements,
    client,
    pool: { connect: vi.fn(async () => client) } as never,
  }
}

afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllEnvs()
})

describe('PARIPRASHNA_DB_ROLES', () => {
  it('names exactly the five roles migration 576 creates', () => {
    expect(Object.values(PARIPRASHNA_DB_ROLES).sort()).toEqual([
      'role_jobs',
      'role_ledger_write',
      'role_orchestrator',
      'role_sidecar',
      'role_web_serve',
    ])
  })
})

describe('assertChartContextValue', () => {
  it('accepts the canonical chart id', () => {
    expect(assertChartContextValue(CHART)).toBe(CHART)
  })

  it.each([['not-a-uuid'], [''], [null], [undefined], [42], [`${CHART} OR 1=1`]])(
    'throws loudly on %p rather than letting RLS silently deny',
    (bad) => {
      expect(() => assertChartContextValue(bad)).toThrow(InvalidChartContextError)
    },
  )
})

describe('flag OFF (the default) — nothing changes', () => {
  it('isRoleSeparationEnabled() is false by default', () => {
    expect(isRoleSeparationEnabled()).toBe(false)
  })

  it('getServeReadPool() returns the EXISTING shared pool, by identity', async () => {
    const shared = { marker: 'the one shared pool' }
    vi.mocked(getPool).mockResolvedValue(shared as never)
    await expect(getServeReadPool()).resolves.toBe(shared)
  })

  it('getServeReadPool() does NOT throw even with no serve credential configured', async () => {
    vi.stubEnv('SERVE_DATABASE_URL', '')
    vi.stubEnv('DB_SERVE_USER', '')
    vi.mocked(getPool).mockResolvedValue({} as never)
    await expect(getServeReadPool()).resolves.toBeDefined()
  })

  it('withChartContext() sets NO GUC — only BEGIN/COMMIT', async () => {
    const { pool, statements } = fakePool()
    await withChartContext(CHART, async () => 'result', { pool })
    expect(statements.map((s) => s.sql)).toEqual(['BEGIN', 'COMMIT'])
    // The specific claim: no set_config for either GUC.
    expect(statements.some((s) => s.sql.includes('set_config'))).toBe(false)
  })

  it('withChartContext() still validates the chart id before doing anything', async () => {
    const { pool } = fakePool()
    await expect(withChartContext('nope', async () => 1, { pool })).rejects.toThrow(
      InvalidChartContextError,
    )
  })
})

describe('flag ON', () => {
  function enableFlag() {
    vi.spyOn(configService, 'getFlag').mockImplementation(
      (f: string) => f === ROLE_SEPARATION_FLAG,
    )
  }

  it('pins app.chart_context as a BIND PARAMETER, transaction-locally', async () => {
    enableFlag()
    const { pool, statements } = fakePool()
    await withChartContext(CHART, async () => 'ok', { pool })

    const setCall = statements.find((s) => s.sql.includes('set_config'))
    expect(setCall).toBeDefined()
    expect(setCall!.params).toEqual([CHART_CONTEXT_GUC, CHART])
    // The value is never interpolated into the SQL text — `SET` cannot be
    // parameterised at all, which is exactly why this is `set_config`.
    expect(setCall!.sql).not.toContain(CHART)
    // is_local = true: the pin dies with the transaction and cannot leak onto the
    // next request that borrows this pooled connection. This assertion is the
    // detector for that; without it the third argument could flip to `false` and
    // nothing would notice until a cross-tenant leak in production.
    expect(setCall!.sql).toMatch(/set_config\(\$1,\s*\$2,\s*true\)/)
  })

  it('does NOT pin app.principal_id unless the caller asks', async () => {
    enableFlag()
    const { pool, statements } = fakePool()
    await withChartContext(CHART, async () => 'ok', { pool })
    expect(statements.some((s) => s.params?.[0] === PRINCIPAL_ID_GUC)).toBe(false)
  })

  it('pins app.principal_id when the caller does ask', async () => {
    enableFlag()
    const { pool, statements } = fakePool()
    await withChartContext(CHART, async () => 'ok', { pool, principalId: 'user-1' })
    const principal = statements.find((s) => s.params?.[0] === PRINCIPAL_ID_GUC)
    expect(principal!.params).toEqual([PRINCIPAL_ID_GUC, 'user-1'])
    expect(principal!.sql).toMatch(/set_config\(\$1,\s*\$2,\s*true\)/)
  })

  it('rolls back and releases when the callback throws', async () => {
    enableFlag()
    const { pool, statements, client } = fakePool()
    await expect(
      withChartContext(CHART, async () => {
        throw new Error('boom')
      }, { pool }),
    ).rejects.toThrow('boom')
    expect(statements.map((s) => s.sql)).toContain('ROLLBACK')
    expect(statements.map((s) => s.sql)).not.toContain('COMMIT')
    expect(client.release).toHaveBeenCalled()
  })

  it('THROWS rather than falling back to the legacy credential when unconfigured', async () => {
    enableFlag()
    vi.stubEnv('SERVE_DATABASE_URL', '')
    vi.stubEnv('DB_SERVE_USER', '')
    vi.stubEnv('DB_SERVE_PASSWORD', '')
    // Deliberately delete any cached pool from a prior test in this file.
    delete (globalThis as { __pgServePool?: unknown }).__pgServePool
    vi.mocked(getPool).mockClear()
    await expect(getServeReadPool()).rejects.toThrow(ServeRoleNotConfiguredError)
    // And it must NOT have quietly used the shared pool instead.
    expect(vi.mocked(getPool)).not.toHaveBeenCalled()
  })
})

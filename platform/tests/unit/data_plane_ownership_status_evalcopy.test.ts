import { beforeEach, describe, expect, it, vi } from 'vitest'

// No database is ever contacted: `pg` is replaced by an in-memory fake that answers only the queries the
// status check issues before the protected-state checks.
const harness = vi.hoisted(() => ({
  queries: [] as string[],
  schemas: ['public', 'pg_catalog', 'information_schema'] as string[],
  migrationsApplied: 0,
  protectedTables: 0,
  failSchemaList: false,
  ended: 0,
}))

vi.mock('pg', () => ({
  Pool: class {
    async query(sql: string) {
      harness.queries.push(sql)
      if (sql.includes('pg_catalog.pg_namespace') && sql.includes('SELECT nspname')) {
        if (harness.failSchemaList) throw new Error('fixture: cannot list schemas')
        return { rows: harness.schemas.map((nspname) => ({ nspname })) }
      }
      if (sql.includes('public._migrations_applied') && sql.includes('count(DISTINCT filename)')) {
        return { rows: [{ count: String(harness.migrationsApplied) }] }
      }
      if (sql.includes("c.relname IN ('l1_data_plane_generations'")) {
        return { rows: [{ count: String(harness.protectedTables) }] }
      }
      throw new Error(`unexpected query reached the fake: ${sql.slice(0, 80)}`)
    }
    async end() { harness.ended += 1 }
  },
}))

const { EVALCOPY_MARKER_MESSAGE, readDataPlaneOwnershipStatus } = await import('../../scripts/data-plane-ownership-status')

const EXPECTED_MESSAGE =
  'An evaluation-copy marker schema (evalcopy) exists on production. '
  + "The evaluation copy's marker must never be written to production. "
  + 'Drop schema evalcopy on production only after confirming it was written there by mistake, then re-run.'

describe('data-plane ownership status: evalcopy production tripwire', () => {
  beforeEach(() => {
    harness.queries = []
    harness.schemas = ['public', 'pg_catalog', 'information_schema']
    harness.migrationsApplied = 0
    harness.protectedTables = 0
    harness.failSchemaList = false
    harness.ended = 0
  })

  it('states the plain-words message exactly', () => {
    expect(EVALCOPY_MARKER_MESSAGE).toBe(EXPECTED_MESSAGE)
  })

  it('goes RED (rejects with the message) when schema evalcopy exists', async () => {
    harness.schemas.push('evalcopy')
    await expect(readDataPlaneOwnershipStatus('postgres://fake')).rejects.toThrow(EXPECTED_MESSAGE)
    expect(harness.ended).toBe(1)
  })

  it('fires before any other check, even on a not-yet-migrated database', async () => {
    harness.schemas.push('evalcopy')
    harness.migrationsApplied = 0
    harness.protectedTables = 0
    await expect(readDataPlaneOwnershipStatus('postgres://fake')).rejects.toThrow(/evalcopy\) exists on production/)
    expect(harness.queries).toHaveLength(1)
  })

  it('goes RED on an already-marked database too (the tripwire does not depend on ownership state)', async () => {
    harness.schemas.push('evalcopy')
    harness.migrationsApplied = 2
    harness.protectedTables = 2
    await expect(readDataPlaneOwnershipStatus('postgres://fake')).rejects.toThrow(EXPECTED_MESSAGE)
    expect(harness.queries).toHaveLength(1)
  })

  it('leaves behaviour unchanged when no evalcopy schema exists (unmarked database -> "unmarked")', async () => {
    await expect(readDataPlaneOwnershipStatus('postgres://fake')).resolves.toBe('unmarked')
    expect(harness.queries).toHaveLength(3)
  })

  it('leaves later checks running when no evalcopy schema exists (partial marker still refuses)', async () => {
    harness.migrationsApplied = 1
    await expect(readDataPlaneOwnershipStatus('postgres://fake')).rejects.toThrow(/Partial DP-SD-018 migration marker state/)
  })

  it.each(['evalcopy_old', 'evalcopy2', 'old_evalcopy', 'evalcop', 'evalcopy '])(
    'does not trigger on the similarly named schema %j (exact match only)', async (name) => {
      harness.schemas.push(name)
      await expect(readDataPlaneOwnershipStatus('postgres://fake')).resolves.toBe('unmarked')
    })

  it.each(['EVALCOPY', 'EvalCopy', 'Evalcopy', 'evalCopy'])(
    'does not trigger on the case variant %j (schema names here are lowercase)', async (name) => {
      harness.schemas.push(name)
      await expect(readDataPlaneOwnershipStatus('postgres://fake')).resolves.toBe('unmarked')
    })

  it('still triggers when evalcopy sits among look-alike schemas', async () => {
    harness.schemas.push('evalcopy_old', 'evalcopy2', 'evalcopy', 'EVALCOPY')
    await expect(readDataPlaneOwnershipStatus('postgres://fake')).rejects.toThrow(EXPECTED_MESSAGE)
  })

  it('fails closed (rejects) when the schema list cannot be read', async () => {
    harness.failSchemaList = true
    await expect(readDataPlaneOwnershipStatus('postgres://fake')).rejects.toThrow('fixture: cannot list schemas')
    expect(harness.ended).toBe(1)
  })
})

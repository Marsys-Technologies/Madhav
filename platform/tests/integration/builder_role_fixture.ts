/**
 * Race-safe fixture helpers for the DB suites that mirror the cluster-global
 * `data_plane_builder` role.
 *
 * Roles are cluster-wide, not per-database, and migrations 1070–1333 GRANT to
 * `data_plane_builder` by literal name, so a per-run unique name is not an
 * option. Two suites running concurrently on one Postgres therefore collide in
 * two ways: both `CREATE ROLE` (SQLSTATE 42710 "role already exists" — the
 * merge_group failure of #3615/#3711) and one suite's `DROP ROLE` pulls the
 * role out from under the other, or its grants leak into the other's
 * "fails before" proof.
 *
 * Fix at the source, both halves:
 *  - `acquireClusterRoleLock` holds a session-level advisory lock for the whole
 *    suite, serialising every suite that uses the role. Advisory locks are
 *    scoped to a database, so the lock connection always goes to the
 *    maintenance database `postgres` (present on every cluster), never to the
 *    suite's own database (which the suite drops/recreates).
 *  - `ensureRole` creates the role inside a DO block that swallows
 *    duplicate_object (role visible) and unique_violation (a concurrent
 *    CREATE ROLE still uncommitted — pg_authid_rolname_index fires 23505, not
 *    42710, in that window), so a role left behind by a crashed run, or created by a
 *    suite outside the lock, can no longer fail the create.
 */
import { Client, type Pool } from 'pg'
import { parse } from 'pg-connection-string'

/** Arbitrary but fixed 64-bit key shared by every suite that touches the role. */
export const BUILDER_ROLE_LOCK_KEY = '7216001070331'

/**
 * Take the cluster-wide builder-role lock; resolves once held. Returns the
 * release function (idempotent). The lock dies with the connection, so a
 * crashed suite cannot wedge the others.
 */
export async function acquireClusterRoleLock(testDbUrl: string): Promise<() => Promise<void>> {
  const base = parse(testDbUrl)
  const client = new Client({
    host: base.host ?? undefined,
    port: base.port ? Number(base.port) : undefined,
    user: base.user ?? undefined,
    password: base.password ?? undefined,
    database: 'postgres',
  })
  await client.connect()
  await client.query('SELECT pg_advisory_lock($1::bigint)', [BUILDER_ROLE_LOCK_KEY])
  let released = false
  return async () => {
    if (released) return
    released = true
    await client.query('SELECT pg_advisory_unlock($1::bigint)', [BUILDER_ROLE_LOCK_KEY]).catch(() => {})
    await client.end().catch(() => {})
  }
}

/** `CREATE ROLE <role> NOLOGIN`, tolerating a concurrent or leftover role. */
export async function ensureRole(pool: Pick<Pool, 'query'>, role: string): Promise<void> {
  if (!/^[a-z_][a-z0-9_]*$/.test(role)) throw new Error(`unsafe role name: ${role}`)
  await pool.query(`
    DO $$ BEGIN
      CREATE ROLE ${role} NOLOGIN;
    EXCEPTION WHEN duplicate_object OR unique_violation THEN
      NULL;
    END $$;
  `)
}

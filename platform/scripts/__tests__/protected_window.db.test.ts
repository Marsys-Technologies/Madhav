/** A6 D-41: real PostgreSQL regressions, required in CI's Unit Tests job.
 * The fixture owns one random database on an explicitly loopback cluster;
 * it never changes cluster roles or relies on a production schema snapshot.
 */
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { Pool, type PoolClient, type PoolConfig } from 'pg'
import { randomUUID, createHash } from 'node:crypto'
import { copyFileSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { runMigrations, TRACKER_DDL, TRACKER_IDENTITY_DDL } from '../migrate'

const platformDir = fileURLToPath(new URL('../../', import.meta.url))
const adminDsn = process.env.KALA_ADMIN_DSN
const required = process.env.KALA_REQUIRE_DB === '1'
const migration = '1376_k7_stage_verification_status.sql'
const stageTables = ['kala_darshana', 'kala_obstruction', 'kala_gochara_contacts',
  'kala_bhavishya', 'kala_convergence', 'kala_jivana_parva']

function adminConfig(raw: string): PoolConfig {
  const url = new URL(raw)
  if (!['postgres:', 'postgresql:'].includes(url.protocol)
    || !['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname)
    || !url.port || url.pathname !== '/postgres' || url.search || url.hash) {
    throw new Error('KALA_ADMIN_DSN must name postgres on explicit loopback host:port, without options')
  }
  return { host: url.hostname.replace(/^\[|\]$/g, ''), port: Number(url.port),
    database: 'postgres', user: decodeURIComponent(url.username),
    password: decodeURIComponent(url.password), ssl: false, connectionTimeoutMillis: 3000 }
}

describe.skipIf(!adminDsn && !required)('protected window PostgreSQL regressions', () => {
  let admin: Pool
  let pool: Pool
  let client: PoolClient
  let dir: string
  let created = false
  const dbname = `kala_ci_window_${randomUUID().replaceAll('-', '')}`

  beforeAll(async () => {
    if (!adminDsn) throw new Error('KALA_REQUIRE_DB=1 requires KALA_ADMIN_DSN')
    const config = adminConfig(adminDsn)
    admin = new Pool(config)
    const identity = await admin.query("SELECT current_database() AS db, host(inet_server_addr()) AS addr")
    expect(identity.rows[0].db).toBe('postgres')
    expect(['127.0.0.1', '::1']).toContain(identity.rows[0].addr)
    await admin.query(`CREATE DATABASE "${dbname}"`)
    created = true
    pool = new Pool({ ...config, database: dbname })
    client = await pool.connect()
    expect((await client.query('SELECT current_database() AS db')).rows[0].db).toBe(dbname)
    dir = mkdtempSync(path.join(tmpdir(), 'protected-window-'))
    await client.query(TRACKER_DDL)
    await client.query(TRACKER_IDENTITY_DDL)
    for (const table of stageTables) await client.query(`CREATE TABLE public.${table} (id integer)`)
  })

  afterAll(async () => {
    client?.release()
    await pool?.end()
    if (created) await admin.query(`DROP DATABASE "${dbname}" WITH (FORCE)`)
    await admin?.end()
    if (dir) rmSync(dir, { recursive: true, force: true })
  })

  it.each(['routine', 'protected'])('%s: real 1376 DDL rolls back with a failed ledger INSERT, then retries atomically', async mode => {
    const migrationDir = path.join(dir, mode)
    // mkdtemp keeps selected files isolated from every repository predecessor.
    const selected = mkdtempSync(migrationDir)
    copyFileSync(path.join(platformDir, 'supabase/migrations', migration), path.join(selected, migration))
    for (const table of stageTables) {
      await client.query(`ALTER TABLE public.${table} DROP COLUMN IF EXISTS verification_pass_status`)
    }
    await client.query('DELETE FROM _migrations_applied')
    await client.query(`ALTER TABLE _migrations_applied ADD CONSTRAINT reject_window_ledger
      CHECK (filename <> '${migration}')`)
    const options = { kalaProtected: new Set([migration]), applyProtectedOverride: true,
      ...(mode === 'protected' ? { only: new Set([migration]) } : {}) }
    try {
      await expect(runMigrations(client, [selected], options)).rejects.toThrow('reject_window_ledger')
      const columns = await client.query(`SELECT table_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = ANY($1) AND column_name = 'verification_pass_status'`, [stageTables])
      const ledger = await client.query('SELECT filename FROM _migrations_applied WHERE filename = $1', [migration])
      expect({ columns: columns.rows, ledger: ledger.rows }).toEqual({ columns: [], ledger: [] })
    } finally {
      await client.query('ALTER TABLE _migrations_applied DROP CONSTRAINT reject_window_ledger')
    }
    expect(await runMigrations(client, [selected], options)).toEqual([migration])
    expect((await client.query(`SELECT count(*)::int AS n FROM information_schema.columns
      WHERE table_schema = 'public' AND table_name = ANY($1) AND column_name = 'verification_pass_status'`, [stageTables])).rows[0].n).toBe(6)
    const sql = readFileSync(path.join(selected, migration), 'utf8')
    expect((await client.query('SELECT sha256 FROM _migrations_applied WHERE filename = $1', [migration])).rows)
      .toEqual([{ sha256: createHash('sha256').update(sql).digest('hex') }])
    expect(await runMigrations(client, [selected], options)).toEqual([])
  })

  it('refuses an interior COMMIT before any DDL can escape the runner transaction', async () => {
    const selected = mkdtempSync(path.join(dir, 'interior-'))
    writeFileSync(path.join(selected, '001_unsafe.sql'), 'CREATE TABLE escaped_ddl (id int); COMMIT; SELECT 1;')
    await expect(runMigrations(client, [selected], { kalaProtected: new Set() }))
      .rejects.toThrow(/transaction/i)
    expect((await client.query("SELECT to_regclass('public.escaped_ddl') AS rel")).rows[0].rel).toBeNull()
  })

  it('keeps earlier file commits, rolls back an unwrapped file and its ledger, and never starts the later file', async () => {
    const selected = mkdtempSync(path.join(dir, 'per-file-'))
    writeFileSync(path.join(selected, '001_before.sql'), 'CREATE TABLE committed_before (id int);')
    writeFileSync(path.join(selected, '002_current.sql'), 'CREATE TABLE rolled_back_current (id int);')
    writeFileSync(path.join(selected, '003_after.sql'), 'CREATE TABLE pending_after (id int);')
    await client.query(`ALTER TABLE _migrations_applied ADD CONSTRAINT reject_middle_ledger
      CHECK (filename <> '002_current.sql')`)
    try {
      await expect(runMigrations(client, [selected], { kalaProtected: new Set() })).rejects.toThrow('reject_middle_ledger')
      expect((await client.query(`SELECT to_regclass('committed_before')::text AS before,
        to_regclass('rolled_back_current') AS current, to_regclass('pending_after') AS after`)).rows)
        .toEqual([{ before: 'committed_before', current: null, after: null }])
      expect((await client.query("SELECT filename FROM _migrations_applied WHERE filename IN ('001_before.sql', '002_current.sql', '003_after.sql') ORDER BY filename")).rows)
        .toEqual([{ filename: '001_before.sql' }])
    } finally {
      await client.query('ALTER TABLE _migrations_applied DROP CONSTRAINT reject_middle_ledger')
    }
    expect(await runMigrations(client, [selected], { kalaProtected: new Set() }))
      .toEqual(['002_current.sql', '003_after.sql'])
  })

  it.each([false, true])('refuses nontransactional DDL before executing the file (dryRun=%s)', async dryRun => {
    const selected = mkdtempSync(path.join(dir, 'concurrent-'))
    writeFileSync(path.join(selected, '004_concurrent.sql'),
      'CREATE TABLE escaped_index_ddl (id int); CREATE INDEX CONCURRENTLY unsafe_idx ON escaped_index_ddl (id);')
    await expect(runMigrations(client, [selected], { kalaProtected: new Set(), dryRun }))
      .rejects.toThrow(/nontransactional command.*reviewed handler/)
    expect((await client.query("SELECT to_regclass('public.escaped_index_ddl') AS rel")).rows[0].rel).toBeNull()
  })

  it.each([['LF', '\n'], ['CRLF', '\r\n'], ['CR', '\r']])('accepts a wrapped file after a %s comment terminator', async (label, newline) => {
    const selected = mkdtempSync(path.join(dir, 'comment-wrapper-'))
    const name = `007_${label.toLowerCase()}_wrapper.sql`
    const table = `wrapped_comment_${label.toLowerCase()}`
    writeFileSync(path.join(selected, name), `BEGIN; -- comment${newline}CREATE TABLE ${table} (id int);${newline}COMMIT;`)
    const options = { kalaProtected: new Set<string>() }
    expect(await runMigrations(client, [selected], { ...options, dryRun: true })).toEqual([name])
    expect(await runMigrations(client, [selected], options)).toEqual([name])
    expect((await client.query('SELECT to_regclass($1)::text AS ddl', [table])).rows[0].ddl).toBe(table)
    expect((await client.query('SELECT count(*)::int AS n FROM _migrations_applied WHERE filename = $1', [name])).rows[0].n).toBe(1)
  })

  it.each([['LF', '\n'], ['CRLF', '\r\n'], ['CR', '\r']])('review: %s comment newline preserves DDL-ledger atomicity', async (_label, newline) => {
    const selected = mkdtempSync(path.join(dir, 'review-cr-'))
    const name = '005_cr_comment.sql'
    writeFileSync(path.join(selected, name),
      `CREATE TABLE review_cr_escaped (id int); -- comment${newline}COMMIT;${newline}SELECT 1;`)
    await client.query(`ALTER TABLE _migrations_applied ADD CONSTRAINT reject_cr_ledger
      CHECK (filename <> '${name}')`)
    try {
      await expect(runMigrations(client, [selected], { kalaProtected: new Set() }))
        .rejects.toThrow(/transaction|reject_cr_ledger/)
      const state = (await client.query(`SELECT to_regclass('public.review_cr_escaped')::text AS ddl,
        (SELECT count(*)::int FROM _migrations_applied WHERE filename = '${name}') AS ledger_rows`)).rows[0]
      expect(state).toEqual({ ddl: null, ledger_rows: 0 })
    } finally {
      await client.query('ALTER TABLE _migrations_applied DROP CONSTRAINT reject_cr_ledger')
    }
  })


  it('review: wrapped SET LOCAL ROLE migrations keep the migration actor for the ledger INSERT', async () => {
    // Built-in role: no CREATE ROLE, ALTER ROLE, or membership changes to the cluster.
    // This isolates the transaction/role shape of existing 1033, 1037 and 1038.
    await client.query('CREATE SCHEMA review_owner_schema AUTHORIZATION pg_read_all_data')
    const selected = mkdtempSync(path.join(dir, 'review-role-'))
    const name = '006_local_role.sql'
    writeFileSync(path.join(selected, name), `BEGIN;
      SET LOCAL ROLE pg_read_all_data;
      CREATE TABLE review_owner_schema.created_by_owner (id int);
      COMMIT;`)
    const options = { kalaProtected: new Set<string>(), only: new Set([name]) }
    expect((await client.query('SELECT current_user')).rows[0].current_user).toBe('postgres')
    expect(await runMigrations(client, [selected], options)).toEqual([name])
    expect((await client.query('SELECT count(*)::int AS n FROM _migrations_applied WHERE filename = $1', [name])).rows[0].n).toBe(1)
    expect((await client.query("SELECT tableowner FROM pg_tables WHERE schemaname = 'review_owner_schema' AND tablename = 'created_by_owner'")).rows)
      .toEqual([{ tableowner: 'pg_read_all_data' }])
    expect((await client.query("SELECT has_table_privilege('pg_read_all_data', '_migrations_applied', 'INSERT') AS allowed")).rows[0].allowed).toBe(false)
    expect((await client.query('SELECT current_user')).rows[0].current_user).toBe('postgres')
    await client.query('DROP TABLE review_owner_schema.created_by_owner')
    await client.query('DELETE FROM _migrations_applied WHERE filename = $1', [name])
    await client.query(`ALTER TABLE _migrations_applied ADD CONSTRAINT reject_role_ledger CHECK (filename <> '${name}')`)
    try {
      await expect(runMigrations(client, [selected], options)).rejects.toThrow('reject_role_ledger')
      expect((await client.query("SELECT to_regclass('review_owner_schema.created_by_owner') AS ddl, (SELECT count(*)::int FROM _migrations_applied WHERE filename = $1) AS ledger_rows", [name])).rows)
        .toEqual([{ ddl: null, ledger_rows: 0 }])
    } finally {
      await client.query('ALTER TABLE _migrations_applied DROP CONSTRAINT reject_role_ledger')
    }
  })

  it('restores an existing entry SET ROLE rather than the session login for ledger writes', async () => {
    await client.query('CREATE SCHEMA entry_role_schema AUTHORIZATION pg_write_all_data')
    const selected = mkdtempSync(path.join(dir, 'entry-role-'))
    const name = '008_entry_role.sql'
    writeFileSync(path.join(selected, name), `BEGIN;
      SET LOCAL ROLE pg_write_all_data;
      CREATE TABLE entry_role_schema.created_by_owner (id int);
      COMMIT;`)
    await client.query(`ALTER TABLE _migrations_applied ADD COLUMN ledger_actor text DEFAULT current_user;
      ALTER TABLE _migrations_applied OWNER TO pg_read_all_data;
      SET ROLE pg_read_all_data`)
    try {
      expect(await runMigrations(client, [selected], { kalaProtected: new Set<string>() })).toEqual([name])
      expect((await client.query('SELECT ledger_actor FROM _migrations_applied WHERE filename = $1', [name])).rows)
        .toEqual([{ ledger_actor: 'pg_read_all_data' }])
      expect((await client.query('SELECT current_user')).rows[0].current_user).toBe('pg_read_all_data')
    } finally {
      await client.query(`RESET ROLE;
        ALTER TABLE _migrations_applied OWNER TO postgres;
        ALTER TABLE _migrations_applied DROP COLUMN ledger_actor`)
    }
  })

  // Execute the real shell function, including its PASS/STOP decision, against
  // psql. No fake SQL answers: PostgreSQL resolves PUBLIC/default ACLs itself.
  function publicReadback(): { status: number | null; stdout: string; stderr: string } {
    const script = readFileSync(path.join(platformDir, 'scripts/gochara-window-readbacks.sh'), 'utf8')
    const check = script.match(/^check_public_execute\(\)[\s\S]*?^}/m)?.[0]
    if (!check || !adminDsn) throw new Error('Missing actual PUBLIC readback function')
    const config = adminConfig(adminDsn)
    return spawnSync('bash', ['-c', `
      run_sql() { psql -X -A -t -v ON_ERROR_STOP=1 -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "$2"; }
      _pass() { printf 'PASS %s\\n' "$1"; }
      _stop() { printf 'STOP %s\\n' "$1"; }
      ${check}
      check_public_execute
    `], { encoding: 'utf8', timeout: 10000, env: { PATH: process.env.PATH, TMPDIR: process.env.TMPDIR,
      PGPASSFILE: path.join(dir, 'nonexistent-pgpass'), PGHOST: String(config.host),
      PGPORT: String(config.port), PGUSER: String(config.user), PGPASSWORD: String(config.password),
      PGDATABASE: dbname, PGOPTIONS: '-c default_transaction_read_only=on' } })
  }

  it('PUBLIC readback detects default and explicit EXECUTE, ignores owner-only grants and other schemas', async () => {
    await client.query(`CREATE SCHEMA other_scope;
      CREATE FUNCTION other_scope.ka_gochara_other() RETURNS int LANGUAGE sql AS 'SELECT 1';
      CREATE FUNCTION public.unrelated_default() RETURNS int LANGUAGE sql AS 'SELECT 1';
      CREATE FUNCTION public.ka_gochara_acl_probe() RETURNS int LANGUAGE sql AS 'SELECT 1'`)
    expect((await client.query("SELECT proacl IS NULL AS default_acl FROM pg_proc WHERE oid = 'public.ka_gochara_acl_probe()'::regprocedure")).rows[0].default_acl).toBe(true)
    const defaultAcl = publicReadback()
    expect(defaultAcl.stderr).toBe('')
    expect(defaultAcl.stdout).toContain('STOP P9-public-execute')
    await client.query('REVOKE EXECUTE ON FUNCTION public.ka_gochara_acl_probe() FROM PUBLIC')
    const revoked = publicReadback()
    expect(revoked.status).toBe(0)
    expect(revoked.stderr).toBe('')
    expect(revoked.stdout).toContain('PASS P9-public-execute')
    await client.query('GRANT EXECUTE ON FUNCTION public.ka_gochara_acl_probe() TO PUBLIC')
    expect(publicReadback().stdout).toContain('STOP P9-public-execute')
    await client.query(`REVOKE EXECUTE ON FUNCTION public.ka_gochara_acl_probe() FROM PUBLIC;
      CREATE FUNCTION public.ka_gochara_acl_probe(int) RETURNS int LANGUAGE sql AS 'SELECT $1'`)
    expect(publicReadback().stdout).toContain('STOP P9-public-execute')
    await client.query('REVOKE EXECUTE ON FUNCTION public.ka_gochara_acl_probe(int) FROM PUBLIC')
    expect(publicReadback().stdout).toContain('PASS P9-public-execute')
  })
})

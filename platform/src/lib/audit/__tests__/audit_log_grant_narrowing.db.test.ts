/**
 * E-001 / PPR-26 narrowed proof — the app's serving credential `amjis_app`
 * holds DELETE and TRUNCATE on `audit_log` in production today (confirmed
 * LIVE, read-only, against madhav-astrology:asia-south1:amjis-postgres /
 * db amjis, via cloud-sql-proxy). An audit log a credential can DELETE or
 * TRUNCATE is not append-only — it can destroy the evidence of its own prior
 * actions. Migration 634 revokes exactly DELETE and TRUNCATE from `amjis_app`
 * on `audit_log`, leaving SELECT/INSERT/UPDATE/TRIGGER/REFERENCES untouched.
 *
 * RED THEN GREEN, on one scratch database:
 *   - RED  (`describe('before migration 634 …')`): a connection as the real
 *     `amjis_app` role — created here with the SAME privilege set confirmed
 *     live in production — CAN DELETE and CAN TRUNCATE audit_log rows.
 *   - GREEN (`describe('after migration 634 …')`): after applying migration
 *     634's actual SQL file (not a re-implementation) to the SAME scratch DB,
 *     the SAME connection gets a real Postgres permission-denied error on both
 *     DELETE and TRUNCATE, while SELECT/INSERT/UPDATE keep working (no
 *     regression on the idempotent-upsert write path writer.ts depends on).
 *
 * SKIPPED unless `E001_DB_TEST=1` AND `E001_DATABASE_URL` is set — same
 * reasoning as the sibling `roles_rls_b002_gaps.db.test.ts` / `roles_rls.db.test.ts`:
 * this CREATEs ROLES and REVOKEs real privileges, so it must run against a
 * THROWAWAY / local database and NEVER against the shared production DB. It
 * is self-contained: it builds its own `audit_log` fixture (columns + the
 * uq_audit_log_query_id constraint, copied verbatim from
 * platform/supabase/migrations/0001_brahma_baseline.sql lines 1094-1109 /
 * 4382-4386) and applies migration 634 itself by reading the real .sql file.
 *
 *   createdb e001_scratch
 *   E001_DB_TEST=1 E001_DATABASE_URL=postgres://postgres@127.0.0.1:5599/e001_scratch \
 *     npx vitest run src/lib/audit/__tests__/audit_log_grant_narrowing.db.test.ts
 *
 * Talks to `pg` directly rather than through `@/lib/db/client`, so it cannot
 * accidentally inherit a `DATABASE_URL` pointing at anything real — the
 * connection string must be named explicitly, in its own variable.
 *
 * THIS IS NOT AN APPLY. Nothing in this file, or in migration 634 itself, is
 * run against production by this test or by CI. See the migration file's own
 * header and the PR description for the sign-off gate.
 */

import { readFileSync } from 'node:fs'
import path from 'node:path'

import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { Pool } from 'pg'

const DB_URL = process.env.E001_DATABASE_URL
const ENABLED = process.env.E001_DB_TEST === '1' && !!DB_URL

const MIGRATION = path.resolve(
  __dirname,
  '../../../../supabase/migrations/634_pariprashna_audit_log_grant_narrowing.sql',
)

// Verbatim from platform/supabase/migrations/0001_brahma_baseline.sql
// lines 1094-1109 (columns) and 4382-4386 (the constraint migration 634's own
// REVOKE targets by name) — not a re-derived shape.
const FIXTURE = `
CREATE TABLE IF NOT EXISTS public.audit_log (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    query_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    query_text text NOT NULL,
    query_class text NOT NULL,
    bundle_keys jsonb DEFAULT '[]'::jsonb NOT NULL,
    tools_called jsonb DEFAULT '[]'::jsonb NOT NULL,
    validators_run jsonb DEFAULT '[]'::jsonb NOT NULL,
    synthesis_model text NOT NULL,
    synthesis_input_tokens integer DEFAULT 0 NOT NULL,
    synthesis_output_tokens integer DEFAULT 0 NOT NULL,
    disclosure_tier text NOT NULL,
    final_output text DEFAULT ''::text NOT NULL,
    audit_event_version integer DEFAULT 1 NOT NULL
);
ALTER TABLE public.audit_log DROP CONSTRAINT IF EXISTS uq_audit_log_query_id;
ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT uq_audit_log_query_id UNIQUE (query_id);
`

let pool: Pool
let appPool: Pool

/** Run as the scratch-DB owner (superuser). */
async function admin(sql: string, params?: unknown[]) {
  return pool.query(sql, params as unknown[])
}

/** Run as `amjis_app` itself — the real production role name, recreated locally. */
async function asApp(sql: string, params?: unknown[]) {
  return appPool.query(sql, params as unknown[])
}

function connFor(role: string): Pool {
  const base = new URL(DB_URL!)
  base.username = role
  base.password = ''
  return new Pool({ connectionString: base.toString() })
}

const QID_1 = '11111111-1111-1111-1111-111111111111'
const QID_2 = '22222222-2222-2222-2222-222222222222'

async function seedTwoRows() {
  await admin('DELETE FROM audit_log')
  await admin(
    `INSERT INTO audit_log
       (query_id, query_text, query_class, synthesis_model, disclosure_tier)
     VALUES
       ($1, 'q1', 'interpretive', 'claude-haiku-4-5', 'super_admin'),
       ($2, 'q2', 'interpretive', 'claude-haiku-4-5', 'super_admin')`,
    [QID_1, QID_2],
  )
}

describe.skipIf(!ENABLED)('E-001 narrowed proof — amjis_app / audit_log DELETE+TRUNCATE', () => {
  beforeAll(async () => {
    pool = new Pool({ connectionString: DB_URL })
    await admin(FIXTURE)

    // Recreate the REAL role name — migration 634's REVOKE is hardcoded to
    // `FROM amjis_app`, so the proof must use that exact name, not a
    // differently-named equivalent, to be a faithful reproduction.
    await admin(`
      DO $$ BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'amjis_app') THEN
          CREATE ROLE amjis_app LOGIN;
        END IF;
      END $$;
      GRANT USAGE ON SCHEMA public TO amjis_app;
    `)
    // The exact privilege set confirmed LIVE in production on audit_log today:
    // DELETE, UPDATE, INSERT, SELECT, TRIGGER, TRUNCATE, REFERENCES.
    await admin(`
      GRANT DELETE, UPDATE, INSERT, SELECT, TRIGGER, TRUNCATE, REFERENCES
        ON TABLE audit_log TO amjis_app;
    `)

    appPool = connFor('amjis_app')
  }, 60_000)

  afterAll(async () => {
    await appPool?.end()
    await pool?.end()
  })

  describe('before migration 634 — RED: amjis_app can destroy audit_log evidence', () => {
    it('confirms amjis_app holds DELETE and TRUNCATE on audit_log before the fix', async () => {
      const { rows } = await admin(
        `SELECT has_table_privilege('amjis_app', 'audit_log', 'DELETE') AS del,
                has_table_privilege('amjis_app', 'audit_log', 'TRUNCATE') AS trunc`,
      )
      expect(rows[0]).toEqual({ del: true, trunc: true })
    })

    it('RED: amjis_app can DELETE rows out of audit_log', async () => {
      await seedTwoRows()
      const del = await asApp('DELETE FROM audit_log WHERE query_id = $1', [QID_1])
      expect(del.rowCount).toBe(1)
      const remaining = await admin('SELECT count(*)::int AS n FROM audit_log')
      expect(remaining.rows[0].n).toBe(1)
    })

    it('RED: amjis_app can TRUNCATE audit_log entirely', async () => {
      await seedTwoRows()
      await asApp('TRUNCATE audit_log')
      const remaining = await admin('SELECT count(*)::int AS n FROM audit_log')
      expect(remaining.rows[0].n).toBe(0)
    })
  })

  describe('applying migration 634', () => {
    it('applies cleanly and is idempotent (safe to re-run)', async () => {
      const sql = readFileSync(MIGRATION, 'utf8')
      await admin(sql)
      await admin(sql) // second apply must not error — REVOKE-of-absent-privilege is a no-op
    })
  })

  describe('after migration 634 — GREEN: amjis_app can no longer destroy audit_log evidence', () => {
    it('confirms amjis_app no longer holds DELETE or TRUNCATE on audit_log', async () => {
      const { rows } = await admin(
        `SELECT has_table_privilege('amjis_app', 'audit_log', 'DELETE') AS del,
                has_table_privilege('amjis_app', 'audit_log', 'TRUNCATE') AS trunc`,
      )
      expect(rows[0]).toEqual({ del: false, trunc: false })
    })

    it('GREEN: amjis_app gets a real permission-denied error attempting DELETE', async () => {
      await seedTwoRows()
      await expect(
        asApp('DELETE FROM audit_log WHERE query_id = $1', [QID_1]),
      ).rejects.toThrow(/permission denied/i)
      // No row was destroyed — the denied statement had no effect.
      const remaining = await admin('SELECT count(*)::int AS n FROM audit_log')
      expect(remaining.rows[0].n).toBe(2)
    })

    it('GREEN: amjis_app gets a real permission-denied error attempting TRUNCATE', async () => {
      await seedTwoRows()
      await expect(asApp('TRUNCATE audit_log')).rejects.toThrow(/permission denied/i)
      const remaining = await admin('SELECT count(*)::int AS n FROM audit_log')
      expect(remaining.rows[0].n).toBe(2)
    })

    it('NO REGRESSION: amjis_app can still SELECT, INSERT, and UPDATE (writer.ts upsert survives)', async () => {
      await seedTwoRows()

      const sel = await asApp('SELECT count(*)::int AS n FROM audit_log')
      expect(sel.rows[0].n).toBe(2)

      // The real writer.ts upsert shape: INSERT ... ON CONFLICT ON CONSTRAINT
      // uq_audit_log_query_id DO UPDATE — proves UPDATE was deliberately left
      // intact (migration 634 header item 1), not accidentally preserved.
      const upsert = await asApp(
        `INSERT INTO audit_log (query_id, query_text, query_class, synthesis_model, disclosure_tier)
         VALUES ($1, 'q1-updated', 'interpretive', 'claude-haiku-4-5', 'super_admin')
         ON CONFLICT ON CONSTRAINT uq_audit_log_query_id DO UPDATE SET
           query_text = EXCLUDED.query_text`,
        [QID_1],
      )
      expect(upsert.rowCount).toBe(1)
      const check = await admin('SELECT query_text FROM audit_log WHERE query_id = $1', [QID_1])
      expect(check.rows[0].query_text).toBe('q1-updated')
    })
  })
})

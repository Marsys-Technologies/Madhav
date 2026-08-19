/**
 * P1 G1-C — DB-integration suite for NO-LEAKAGE arm-1 (roles + RLS) and arm-3.
 *
 * SKIPPED unless `G1C_DB_TEST=1` AND `G1C_DATABASE_URL` is set. It needs a live
 * Postgres, it CREATEs ROLES and it DELETEs rows, so it must run against a
 * THROWAWAY / local database and NEVER against the shared production DB. It
 * builds its own fixture tables and applies migration 576 itself, so it is
 * self-contained.
 *
 *   createdb g1c_scratch
 *   G1C_DB_TEST=1 G1C_DATABASE_URL=postgres://postgres@127.0.0.1:5599/g1c_scratch \
 *     npx vitest run src/lib/pariprashna/arm3/__tests__/roles_rls.db.test.ts
 *
 * Like G1-B's consent suite, it talks to `pg` directly rather than through
 * `@/lib/db/client`, so it cannot accidentally inherit a `DATABASE_URL` pointing
 * at anything real — the connection string must be named explicitly, in its own
 * variable.
 *
 * ── WHAT THIS SUITE IS THE DETECTOR FOR ──────────────────────────────────────
 * Three claims this lane makes, each with a test that can make it read false:
 *   1. "the migration is inert as applied"  → RLS enabled on 0 tables after it
 *   2. "role_web_serve cannot write the ledger or read calibration" → real
 *      permission-denied errors from a real session on that role
 *   3. "a session pinned to chart X cannot read chart Y's rows" → the cross-
 *      context denial test, run against real policies on real rows
 */

import { readFileSync } from 'node:fs'
import path from 'node:path'

import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest'
import { Pool } from 'pg'

import { drainOutbox } from '../drain'
import { enqueueLedgerIntent, outboxDepth, type OutboxDb } from '../outbox'

const DB_URL = process.env.G1C_DATABASE_URL
const ENABLED = process.env.G1C_DB_TEST === '1' && !!DB_URL

const MIGRATION = path.resolve(
  __dirname,
  '../../../../../supabase/migrations/576_pariprashna_roles_rls_arm3.sql',
)
const ARM_SCRIPT = path.resolve(
  __dirname,
  '../../../../../scripts/pariprashna/g1c_arm_rls.sql',
)

const CHART_X = '11111111-1111-1111-1111-111111111111'
const CHART_Y = '22222222-2222-2222-2222-222222222222'

/**
 * The subset of the real schema migration 576 walls. Shapes only — the columns
 * the policies and grants actually reference. The REAL DDL lives in migrations
 * 0001 / 467 / 468 / 470 / 475 / 575 and is not duplicated as behaviour, only as
 * enough structure for the wall to be exercised.
 */
const FIXTURE = `
CREATE TABLE IF NOT EXISTS charts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), owner_id text, subject_name text, birth_date date);
CREATE TABLE IF NOT EXISTS life_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), event_id text UNIQUE NOT NULL,
  description text NOT NULL, chart_id uuid REFERENCES charts(id));
CREATE TABLE IF NOT EXISTS conversations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id uuid NOT NULL REFERENCES charts(id) ON DELETE CASCADE, user_id text, module text);
CREATE TABLE IF NOT EXISTS conversation_messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  role text NOT NULL, parts_json jsonb NOT NULL DEFAULT '[]');
CREATE TABLE IF NOT EXISTS message_parts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id uuid NOT NULL REFERENCES conversation_messages(id),
  seq int NOT NULL, kind text NOT NULL, body jsonb NOT NULL,
  model_visible boolean NOT NULL DEFAULT true);
CREATE TABLE IF NOT EXISTS conversation_summaries (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE, summary_text text);
CREATE TABLE IF NOT EXISTS pariprashna_stream_capture (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id text,
  captured_at timestamptz DEFAULT now());
CREATE TABLE IF NOT EXISTS chart_subject_consent (
  chart_id uuid PRIMARY KEY REFERENCES charts(id) ON DELETE CASCADE,
  subject_kind text NOT NULL DEFAULT 'native_self', consent_state text NOT NULL DEFAULT 'granted');
CREATE TABLE IF NOT EXISTS chart_subject_consent_events (
  event_id BIGSERIAL PRIMARY KEY, chart_id uuid NOT NULL, seq integer NOT NULL,
  event_kind text NOT NULL, actor_principal_id text, payload jsonb NOT NULL DEFAULT '{}',
  recorded_at timestamptz NOT NULL DEFAULT now(), prev_hash text, entry_hash text NOT NULL,
  UNIQUE (chart_id, seq));
CREATE TABLE IF NOT EXISTS chart_subject_exclusions (
  exclusion_id BIGSERIAL PRIMARY KEY, chart_id uuid NOT NULL, exclusion_reason text NOT NULL,
  detector text NOT NULL, detected_at timestamptz NOT NULL DEFAULT now(), cleared_at timestamptz);
CREATE TABLE IF NOT EXISTS chart_subject_deletion_tombstones (
  tombstone_id BIGSERIAL PRIMARY KEY, chart_id uuid NOT NULL, table_name text NOT NULL,
  row_count integer NOT NULL DEFAULT 0, content_hash text,
  verified_empty boolean NOT NULL DEFAULT false);
CREATE TABLE IF NOT EXISTS chart_subject_deletion_disputes (
  dispute_id BIGSERIAL PRIMARY KEY, chart_id uuid NOT NULL, dr_entry_yaml text NOT NULL,
  status text NOT NULL DEFAULT 'open');
CREATE TABLE IF NOT EXISTS brahma_mimamsa_prediction_ledger (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid NOT NULL,
  message_part_id uuid REFERENCES message_parts(id), claim_text text NOT NULL, domain text,
  "window" daterange, confidence numrange, direction text,
  technique_refs text[] NOT NULL DEFAULT '{}', grounding_fact_ids text[] NOT NULL DEFAULT '{}',
  created_from_channel text NOT NULL DEFAULT 'pariprashna',
  lifecycle_status text NOT NULL DEFAULT 'detected',
  build_id text, priors_version text, formula_versions jsonb, ranking_config jsonb,
  now_context_date date, stamp_copied_at timestamptz,
  outcome text, outcome_value numeric, outcome_note text, outcome_recorded_at timestamptz,
  confirmed_at timestamptz, dismissed_reason text,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS brahma_prospective_ledger (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid NOT NULL,
  claim_text text, lifecycle_status text);
CREATE TABLE IF NOT EXISTS mimamsa_predictions (
  chart_id uuid NOT NULL, prediction_id text NOT NULL, brier_score double precision,
  outcome_observed text, PRIMARY KEY (chart_id, prediction_id));
CREATE TABLE IF NOT EXISTS mimamsa_calibration (
  chart_id uuid NOT NULL, match_id text NOT NULL, brier_score double precision,
  PRIMARY KEY (chart_id, match_id));
CREATE TABLE IF NOT EXISTS mimamsa_calibration_snapshot (
  snapshot_id text PRIMARY KEY, chart_id uuid NOT NULL, cells_jsonb jsonb);
CREATE TABLE IF NOT EXISTS mimamsa_multipliers (
  technique text NOT NULL, ayanamsha_id text NOT NULL, multiplier numeric,
  PRIMARY KEY (technique, ayanamsha_id));
CREATE TABLE IF NOT EXISTS mimamsa_adjudication_log (
  id bigserial PRIMARY KEY, chart_id uuid NOT NULL, prediction_id text NOT NULL,
  UNIQUE (chart_id, prediction_id));
CREATE TABLE IF NOT EXISTS mimamsa_snapshot_cosign (
  id bigserial PRIMARY KEY, chart_id uuid NOT NULL, snapshot_id text);
CREATE TABLE IF NOT EXISTS mimamsa_resonance_feedback (
  id bigserial PRIMARY KEY, chart_id uuid NOT NULL, note text);
CREATE TABLE IF NOT EXISTS mimamsa_pool_contributions (
  id bigserial PRIMARY KEY, chart_id uuid NOT NULL REFERENCES charts(id));
CREATE TABLE IF NOT EXISTS mimamsa_intervention_ledger (
  id bigserial PRIMARY KEY, chart_id uuid NOT NULL, study_arm text);
CREATE TABLE IF NOT EXISTS gochara_v3_calibration (
  id bigserial PRIMARY KEY, per_chart_hit_rates jsonb);
CREATE TABLE IF NOT EXISTS mcp_prediction_outcomes (
  id bigserial PRIMARY KEY, prediction_id text);
`

/**
 * The arming script is a psql program (`\set`, `\if`, `:'var'`), which `pg`
 * cannot execute. Rather than reimplement its logic in the test — which would
 * mean testing a copy instead of the thing that ships — this extracts the real
 * `DO $arm$ ... $arm$;` block verbatim and runs it, with the GUCs it reads set
 * by the caller. The psql wrapper itself is exercised by hand per the runbook.
 */
function armBlock(): string {
  const sql = readFileSync(ARM_SCRIPT, 'utf8')
  const m = sql.match(/DO \$arm\$[\s\S]*?\$arm\$;/)
  if (!m) throw new Error('could not extract the DO $arm$ block from g1c_arm_rls.sql')
  return m[0]
}

let pool: Pool
let servePool: Pool
let ledgerPool: Pool

/** Run as the owner (superuser in the scratch DB). */
async function admin(sql: string, params?: unknown[]) {
  return pool.query(sql, params as unknown[])
}

/** Run as `role_web_serve`, with `app.chart_context` pinned for the statement. */
async function asServe(chartId: string | null, sql: string, params?: unknown[]) {
  const c = await servePool.connect()
  try {
    await c.query('BEGIN')
    if (chartId !== null) {
      await c.query('SELECT set_config($1, $2, true)', ['app.chart_context', chartId])
    }
    const r = await c.query(sql, params as unknown[])
    await c.query('COMMIT')
    return r
  } catch (e) {
    await c.query('ROLLBACK').catch(() => {})
    throw e
  } finally {
    c.release()
  }
}

describe.skipIf(!ENABLED)('G1-C — roles, RLS and arm-3 against a live Postgres', () => {
  beforeAll(async () => {
    pool = new Pool({ connectionString: DB_URL })
    await admin(FIXTURE)
    await admin(readFileSync(MIGRATION, 'utf8'))
    // Login users standing in for the cutover's real ones.
    await admin(`
      DO $$ BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'g1c_serve') THEN
          CREATE ROLE g1c_serve LOGIN;
        END IF;
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'g1c_ledger') THEN
          CREATE ROLE g1c_ledger LOGIN;
        END IF;
      END $$;
      GRANT role_web_serve TO g1c_serve;
      GRANT role_ledger_write TO g1c_ledger;
    `)
    const base = new URL(DB_URL!)
    base.username = 'g1c_serve'
    base.password = ''
    servePool = new Pool({ connectionString: base.toString() })
    base.username = 'g1c_ledger'
    ledgerPool = new Pool({ connectionString: base.toString() })
  }, 60_000)

  afterAll(async () => {
    await servePool?.end()
    await ledgerPool?.end()
    await pool?.end()
  })

  beforeEach(async () => {
    await admin('DELETE FROM pariprashna_ledger_outbox')
    await admin('DELETE FROM brahma_mimamsa_prediction_ledger')
    await admin('DELETE FROM life_events')
    await admin('DELETE FROM message_parts')
    await admin('DELETE FROM conversation_messages')
    await admin('DELETE FROM conversations')
    await admin('DELETE FROM charts')
    await admin(
      `INSERT INTO charts (id, subject_name) VALUES ($1,'X'), ($2,'Y')`,
      [CHART_X, CHART_Y],
    )
  })

  // ── 1. The migration is inert as applied ────────────────────────────────────
  describe('as applied, before arming', () => {
    it('creates all five roles, NOLOGIN and NOBYPASSRLS', async () => {
      const { rows } = await admin(
        `SELECT rolname, rolcanlogin, rolbypassrls, rolsuper FROM pg_roles
          WHERE rolname LIKE 'role\\_%' ORDER BY rolname`,
      )
      expect(rows.map((r) => r.rolname)).toEqual([
        'role_jobs',
        'role_ledger_write',
        'role_orchestrator',
        'role_sidecar',
        'role_web_serve',
      ])
      for (const r of rows) {
        expect(r.rolcanlogin, `${r.rolname} must not be able to log in`).toBe(false)
        expect(r.rolbypassrls, `${r.rolname} must not bypass RLS`).toBe(false)
        expect(r.rolsuper).toBe(false)
      }
    })

    it('enables ROW LEVEL SECURITY on NOTHING — the migration ships inert', async () => {
      // THE inertness claim. Migration 576 writes policies but arms none of them;
      // arming is `g1c_arm_rls.sql`, a deliberate operator act. If someone adds an
      // `ENABLE ROW LEVEL SECURITY` to the migration, this fails — which is the
      // point, because that would make a deploy silently change live access.
      const { rows } = await admin(
        `SELECT count(*)::int AS n FROM pg_class c JOIN pg_namespace ns ON ns.oid = c.relnamespace
          WHERE ns.nspname = 'public' AND c.relrowsecurity`,
      )
      expect(rows[0].n).toBe(0)
    })

    it('the five roles have no members — nothing can connect as them', async () => {
      const { rows } = await admin(
        `SELECT r.rolname, count(m.member)::int AS members
           FROM pg_roles r LEFT JOIN pg_auth_members m ON m.roleid = r.oid
          WHERE r.rolname LIKE 'role\\_%' GROUP BY r.rolname ORDER BY r.rolname`,
      )
      // g1c_serve / g1c_ledger are granted by THIS SUITE's beforeAll, so two roles
      // legitimately have one member each here. The claim under test is that the
      // MIGRATION grants none — i.e. no role has a member the suite did not add.
      const granted = rows.filter((r) => r.members > 0).map((r) => r.rolname).sort()
      expect(granted).toEqual(['role_ledger_write', 'role_web_serve'])
      expect(rows.find((r) => r.rolname === 'role_orchestrator')!.members).toBe(0)
      expect(rows.find((r) => r.rolname === 'role_jobs')!.members).toBe(0)
      expect(rows.find((r) => r.rolname === 'role_sidecar')!.members).toBe(0)
    })

    it('creates two policies per walled table', async () => {
      const { rows } = await admin(
        `SELECT count(*)::int AS n FROM pg_policies WHERE policyname LIKE '%\\_g1c\\_%'`,
      )
      expect(rows[0].n).toBe(42) // 21 tables × 2
    })

    it('is idempotent — re-applying changes nothing and does not throw', async () => {
      await admin(readFileSync(MIGRATION, 'utf8'))
      const { rows } = await admin(
        `SELECT count(*)::int AS n FROM pg_policies WHERE policyname LIKE '%\\_g1c\\_%'`,
      )
      expect(rows[0].n).toBe(42)
    })
  })

  // ── 2. The grant wall (arm-1) — independent of RLS ─────────────────────────
  describe('grant wall', () => {
    it('role_web_serve CANNOT insert into the prediction ledger', async () => {
      await expect(
        asServe(
          CHART_X,
          `INSERT INTO brahma_mimamsa_prediction_ledger (chart_id, claim_text) VALUES ($1,'x')`,
          [CHART_X],
        ),
      ).rejects.toThrow(/permission denied/i)
    })

    it('role_web_serve CANNOT read any calibration table', async () => {
      for (const t of [
        'mimamsa_calibration',
        'mimamsa_calibration_snapshot',
        'mimamsa_multipliers',
        'gochara_v3_calibration',
      ]) {
        await expect(
          asServe(CHART_X, `SELECT count(*) FROM ${t}`),
        ).rejects.toThrow(/permission denied/i)
      }
    })

    it('role_web_serve CANNOT update or delete a consent audit row (PPR-26)', async () => {
      await expect(
        asServe(CHART_X, `UPDATE chart_subject_consent_events SET seq = 1`),
      ).rejects.toThrow(/permission denied/i)
      await expect(
        asServe(CHART_X, `DELETE FROM chart_subject_consent_events`),
      ).rejects.toThrow(/permission denied/i)
      await expect(
        asServe(CHART_X, `DELETE FROM chart_subject_deletion_tombstones`),
      ).rejects.toThrow(/permission denied/i)
    })

    it('role_web_serve CAN read the ledger (the review tab still works)', async () => {
      await expect(
        asServe(CHART_X, `SELECT count(*) FROM brahma_mimamsa_prediction_ledger`),
      ).resolves.toBeDefined()
    })

    it('role_ledger_write CANNOT enqueue its own work item', async () => {
      await expect(
        ledgerPool.query(
          `INSERT INTO pariprashna_ledger_outbox (chart_id, op, payload)
           VALUES ($1,'create_detected','{}'::jsonb)`,
          [CHART_X],
        ),
      ).rejects.toThrow(/permission denied/i)
    })
  })

  // ── 3. RLS: armed, then the cross-context denial ───────────────────────────
  describe('chart-scoped RLS (armed)', () => {
    beforeAll(async () => {
      // Arm using the REAL detector block from the shipped arming script. The app
      // role is set to one that owns nothing, and the risk is explicitly accepted
      // — which is precisely the state after a real cutover.
      await admin(`SET g1c.app_role = 'g1c_serve'`)
      await admin(`SET g1c.accept_ownership_risk = 'yes'`)
      await admin(armBlock())
    }, 60_000)

    beforeEach(async () => {
      await admin(
        `INSERT INTO life_events (event_id, description, chart_id)
         VALUES ('ev-x','X private event',$1), ('ev-y','Y private event',$2)`,
        [CHART_X, CHART_Y],
      )
      await admin(
        `INSERT INTO brahma_mimamsa_prediction_ledger (chart_id, claim_text)
         VALUES ($1,'X claim'), ($2,'Y claim')`,
        [CHART_X, CHART_Y],
      )
      await admin(
        `INSERT INTO conversations (id, chart_id, user_id, module) VALUES
           ('aaaaaaaa-0000-0000-0000-000000000001',$1,'u','consume'),
           ('aaaaaaaa-0000-0000-0000-000000000002',$2,'u','consume')`,
        [CHART_X, CHART_Y],
      )
      await admin(`INSERT INTO conversation_messages (id, conversation_id, role) VALUES
           ('bbbbbbbb-0000-0000-0000-000000000001','aaaaaaaa-0000-0000-0000-000000000001','user'),
           ('bbbbbbbb-0000-0000-0000-000000000002','aaaaaaaa-0000-0000-0000-000000000002','user')`)
      await admin(`INSERT INTO message_parts (message_id, seq, kind, body) VALUES
           ('bbbbbbbb-0000-0000-0000-000000000001',1,'text','{"t":"X prose"}'),
           ('bbbbbbbb-0000-0000-0000-000000000002',1,'text','{"t":"Y prose"}')`)
    })

    it('the arming script enabled RLS on every policied table', async () => {
      const { rows } = await admin(
        `SELECT count(*)::int AS n FROM pg_class c JOIN pg_namespace ns ON ns.oid = c.relnamespace
          WHERE ns.nspname = 'public' AND c.relrowsecurity`,
      )
      expect(rows[0].n).toBe(21)
    })

    // ══ THE CROSS-CONTEXT DENIAL TEST ══════════════════════════════════════
    it('session pinned to chart X cannot read chart Y rows — direct chart_id', async () => {
      const events = await asServe(CHART_X, 'SELECT description, chart_id FROM life_events')
      expect(events.rows.map((r) => r.description)).toEqual(['X private event'])
      expect(events.rows.every((r) => r.chart_id === CHART_X)).toBe(true)

      // And asking for Y BY NAME returns nothing rather than erroring — RLS
      // filters, it does not announce what it hid.
      const explicit = await asServe(
        CHART_X,
        'SELECT count(*)::int AS n FROM life_events WHERE chart_id = $1',
        [CHART_Y],
      )
      expect(explicit.rows[0].n).toBe(0)
    })

    it('session pinned to chart X cannot read chart Y rows — C3 ledger', async () => {
      const r = await asServe(CHART_X, 'SELECT claim_text FROM brahma_mimamsa_prediction_ledger')
      expect(r.rows.map((x) => x.claim_text)).toEqual(['X claim'])
    })

    it('session pinned to chart X cannot read chart Y rows — via a JOIN (message_parts)', async () => {
      // message_parts has no chart_id of its own; its policy walks
      // message_parts → conversation_messages → conversations. This is the test
      // that the indirect predicate actually works, not just the easy direct one.
      const r = await asServe(CHART_X, `SELECT body->>'t' AS t FROM message_parts`)
      expect(r.rows.map((x) => x.t)).toEqual(['X prose'])
    })

    it('an UNSET chart context sees NOTHING — fail-closed, not fail-open', async () => {
      for (const t of ['life_events', 'brahma_mimamsa_prediction_ledger', 'message_parts']) {
        const r = await asServe(null, `SELECT count(*)::int AS n FROM ${t}`)
        expect(r.rows[0].n, `${t} must be invisible without a chart pin`).toBe(0)
      }
    })

    it('a MALFORMED chart context sees NOTHING — fail-closed', async () => {
      const c = await servePool.connect()
      try {
        await c.query('BEGIN')
        await c.query('SELECT set_config($1,$2,true)', ['app.chart_context', 'not-a-uuid'])
        const r = await c.query('SELECT count(*)::int AS n FROM life_events')
        expect(r.rows[0].n).toBe(0)
        await c.query('COMMIT')
      } finally {
        c.release()
      }
    })

    it('WITH CHECK stops a write from escaping its chart pin', async () => {
      // The outbox is the one table role_web_serve may INSERT into. Pinned to X,
      // it must not be able to file an intent scoped to Y.
      await expect(
        asServe(
          CHART_X,
          `INSERT INTO pariprashna_ledger_outbox (chart_id, op, payload)
           VALUES ($1,'create_detected','{}'::jsonb)`,
          [CHART_Y],
        ),
      ).rejects.toThrow(/row-level security/i)
    })

    it('the pin does not leak onto the next borrower of the same pooled connection', async () => {
      // set_config(..., is_local => true) is scoped to the transaction. If it
      // were session-scoped, this second, unpinned query on the same pool would
      // still see X's rows — which is the cross-tenant bug this whole wall exists
      // to prevent.
      await asServe(CHART_X, 'SELECT 1')
      const after = await asServe(null, 'SELECT count(*)::int AS n FROM life_events')
      expect(after.rows[0].n).toBe(0)
    })

    it('role_ledger_write is NOT chart-pinned — it works across charts', async () => {
      const r = await ledgerPool.query(
        'SELECT count(*)::int AS n FROM brahma_mimamsa_prediction_ledger',
      )
      expect(r.rows[0].n).toBe(2)
    })
  })

  // ── 4. arm-3 end to end ────────────────────────────────────────────────────
  describe('arm-3: enqueue on the serving role, apply on the writer role', () => {
    it('a queued intent becomes a real ledger row, written by the writer role only', async () => {
      const serveDb: OutboxDb = {
        query: async (sql, params) => {
          const r = await asServe(CHART_X, sql as string, params)
          return { rows: r.rows as never[], rowCount: r.rowCount }
        },
      }
      const ledgerDb: OutboxDb = {
        query: (sql, params) =>
          ledgerPool
            .query(sql as string, params as unknown[])
            .then((r) => ({ rows: r.rows as never[], rowCount: r.rowCount })),
      }

      const outboxId = await enqueueLedgerIntent(
        {
          op: 'create_detected',
          payload: { chart_id: CHART_X, claim_text: 'a queued claim' },
        },
        serveDb,
      )
      expect(outboxId).toBeTruthy()

      // Nothing is in the ledger yet — an enqueued intent is not a ledger row.
      const before = await admin(
        `SELECT count(*)::int AS n FROM brahma_mimamsa_prediction_ledger WHERE claim_text = 'a queued claim'`,
      )
      expect(before.rows[0].n).toBe(0)
      expect((await outboxDepth(ledgerDb)).pending).toBe(1)

      const result = await drainOutbox(ledgerDb)
      expect(result).toMatchObject({ claimed: 1, applied: 1, failed: 0 })

      const after = await admin(
        `SELECT chart_id, lifecycle_status, confidence FROM brahma_mimamsa_prediction_ledger
          WHERE claim_text = 'a queued claim'`,
      )
      expect(after.rows).toHaveLength(1)
      expect(after.rows[0].chart_id).toBe(CHART_X)
      expect(after.rows[0].lifecycle_status).toBe('detected')
      // W-1: no confidence band was manufactured on the way through the queue.
      expect(after.rows[0].confidence).toBeNull()
      expect((await outboxDepth(ledgerDb)).pending).toBe(0)
    })
  })
})

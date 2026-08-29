/**
 * Pariparaśna v3 closeout, Phase C — extends E-001 / PPR-26 (PR #1615, migration
 * 634) to two more tables where live DB reads confirmed `amjis_app` holds the
 * IDENTICAL over-broad grant (DELETE, INSERT, REFERENCES, SELECT, TRIGGER,
 * TRUNCATE, UPDATE): `pariprashna_safety_decisions` (369+ live rows) and
 * `mimamsa_predictions` (195 rows). Migration 635 narrows both.
 *
 * Per-table decision (independently verified, NOT assumed from audit_log):
 *   - pariprashna_safety_decisions: DELETE, TRUNCATE, UPDATE all revoked. No
 *     legitimate caller of any of the three exists anywhere in the codebase
 *     (only INSERT + SELECT are ever issued against this table) — and this
 *     table also carries a hard, unconditional append-only trigger (migration
 *     577, `trg_pariprashna_safety_decisions_append_only`) that already blocks
 *     UPDATE/DELETE for every role. THIS TEST DELIBERATELY DOES NOT INSTALL
 *     THAT TRIGGER on its scratch fixture — it isolates exactly what migration
 *     635 itself does (grant narrowing), not the trigger's own behaviour, which
 *     already has its own coverage (review_db.integration.test.ts,
 *     consent.db.test.ts). A production DB has BOTH layers; this proof is for
 *     the grant layer only, so a future trigger edit/disable does not silently
 *     reopen a hole this migration also closed at the grant level.
 *   - mimamsa_predictions: ONLY TRUNCATE is revoked. DELETE and UPDATE are KEPT
 *     — both have live, scoped, actively-used callers running under amjis_app
 *     today (PARIPRASHNA_ROLE_SEPARATION is OFF by default, so every platform
 *     query, including these, runs as amjis_app):
 *       - DELETE: platform/src/lib/cockpit/assetClearSpec.ts's cockpit
 *         "clear chart" op — `DELETE FROM mimamsa_predictions WHERE chart_id
 *         = $1 AND lifecycle_status IN ('pending', 'due')` — same scoped shape
 *         `mi_bhavisya.py`'s delete-then-insert rebuild issues.
 *       - UPDATE: platform/src/lib/retrieval/registry/layers/L5_mimamsa/
 *         prediction_lifecycle_sweep.ts (EL-58) — `UPDATE mimamsa_predictions
 *         SET lifecycle_status = 'expired' WHERE chart_id = $1 AND
 *         prediction_id = $2`.
 *     No TRUNCATE caller of any kind was found anywhere in platform/,
 *     python-sidecar/, or migrations.
 *
 * RED THEN GREEN, on one scratch database, mirroring
 * audit_log_grant_narrowing.db.test.ts's proof shape exactly:
 *   - RED  (`describe('before migration 635 …')`): a connection as the real
 *     `amjis_app` role — created here with the SAME privilege set confirmed
 *     live in production on both tables — CAN perform every privilege this
 *     migration is about to revoke.
 *   - GREEN (`describe('after migration 635 …')`): after applying migration
 *     635's actual SQL file (not a re-implementation) to the SAME scratch DB,
 *     the SAME connection gets a real Postgres permission-denied error on
 *     every revoked privilege, while every KEPT privilege — including the two
 *     real write shapes above — keeps working (no regression).
 *
 * SKIPPED unless `E635_DB_TEST=1` AND `E635_DATABASE_URL` is set — same
 * reasoning as audit_log_grant_narrowing.db.test.ts: this CREATEs a ROLE and
 * REVOKEs real privileges, so it must run against a THROWAWAY / local database
 * and NEVER against the shared production DB. Self-contained: it builds its
 * own fixture tables (columns copied verbatim from the tables' own defining
 * migrations — 577_pariprashna_safety_gate.sql lines 65-91 for
 * pariprashna_safety_decisions, 347_mimamsa_bhavisya.sql lines 6-25 for
 * mimamsa_predictions) and applies migration 635 itself by reading the real
 * .sql file.
 *
 *   createdb e635_scratch
 *   E635_DB_TEST=1 E635_DATABASE_URL=postgres://postgres@127.0.0.1:5599/e635_scratch \
 *     npx vitest run src/lib/audit/__tests__/safety_predictions_grant_narrowing.db.test.ts
 *
 * Talks to `pg` directly rather than through `@/lib/db/client`, so it cannot
 * accidentally inherit a `DATABASE_URL` pointing at anything real — the
 * connection string must be named explicitly, in its own variable.
 *
 * THIS IS NOT AN APPLY. Nothing in this file, or in migration 635 itself, is
 * run against production by this test or by CI. See the migration file's own
 * header and the PR description for the sign-off gate.
 */

import { readFileSync } from 'node:fs'
import path from 'node:path'

import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { Pool } from 'pg'

const DB_URL = process.env.E635_DATABASE_URL
const ENABLED = process.env.E635_DB_TEST === '1' && !!DB_URL

const MIGRATION = path.resolve(
  __dirname,
  '../../../../supabase/migrations/635_pariprashna_safety_predictions_grant_narrowing.sql',
)

// Verbatim (columns only — no triggers, no FKs, no unrelated constraints) from
// platform/supabase/migrations/577_pariprashna_safety_gate.sql lines 65-91.
const SAFETY_DECISIONS_FIXTURE = `
CREATE TABLE IF NOT EXISTS public.pariprashna_safety_decisions (
  decision_id            UUID        PRIMARY KEY,
  chart_id               UUID        NOT NULL,
  turn_id                UUID        NOT NULL,
  seq                    INTEGER     NOT NULL CHECK (seq >= 1),
  enforced               BOOLEAN     NOT NULL,
  classes_detected       TEXT[]      NOT NULL DEFAULT '{}',
  severity               TEXT        NOT NULL
                                     CHECK (severity IN ('none','advisory','review_required','hard_stop')),
  action                 TEXT        NOT NULL
                                     CHECK (action IN ('proceed','reframe','interstitial','seal_pending_signoff','hard_stop')),
  subject_kind           TEXT        NULL
                                     CHECK (subject_kind IS NULL OR subject_kind IN ('native_self','cohort','test')),
  detections             JSONB       NOT NULL DEFAULT '[]'::jsonb,
  evasion_markers        JSONB       NOT NULL DEFAULT '[]'::jsonb,
  excluded_capabilities  TEXT[]      NOT NULL DEFAULT '{}',
  llm_assist_ran         BOOLEAN     NOT NULL DEFAULT false,
  review_id              UUID        NULL,
  recorded_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  prev_hash              TEXT        NULL,
  entry_hash             TEXT        NOT NULL
);
`

// Verbatim from platform/migrations/347_mimamsa_bhavisya.sql lines 6-25.
const MIMAMSA_PREDICTIONS_FIXTURE = `
CREATE TABLE IF NOT EXISTS public.mimamsa_predictions (
  chart_id               uuid        NOT NULL,
  prediction_id          text        NOT NULL,
  source_pramana_id      text        NOT NULL,
  outcome_claim          text        NOT NULL,
  domain                 text        NOT NULL,
  observation_window     daterange   NOT NULL,
  eval_date              date        NOT NULL,
  confidence_band        numrange    NOT NULL,
  magnitude_expected     text        NOT NULL,
  falsifier_jsonb        jsonb       NOT NULL,
  base_rate              numeric,
  emitted_at             timestamptz NOT NULL,
  lifecycle_status       text        NOT NULL,
  driving_signals        jsonb       NOT NULL,
  frozen_bundle_hash     text        NOT NULL,
  bundle_formula_version text        NOT NULL,
  created_at             timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, prediction_id)
);
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

const CHART_1 = '11111111-1111-1111-1111-111111111111'
const DECISION_1 = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
const DECISION_2 = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'
const TURN_1 = 'cccccccc-cccc-cccc-cccc-cccccccccccc'
const TURN_2 = 'dddddddd-dddd-dddd-dddd-dddddddddddd'

async function seedSafetyDecisions() {
  await admin('DELETE FROM pariprashna_safety_decisions')
  await admin(
    `INSERT INTO pariprashna_safety_decisions
       (decision_id, chart_id, turn_id, seq, enforced, severity, action, entry_hash)
     VALUES
       ($1, $2, $3, 1, true, 'none', 'proceed', repeat('a', 64)),
       ($4, $2, $5, 2, true, 'none', 'proceed', repeat('b', 64))`,
    [DECISION_1, CHART_1, TURN_1, DECISION_2, TURN_2],
  )
}

async function seedMimamsaPredictions() {
  await admin('DELETE FROM mimamsa_predictions')
  await admin(
    `INSERT INTO mimamsa_predictions
       (chart_id, prediction_id, source_pramana_id, outcome_claim, domain,
        observation_window, eval_date, confidence_band, magnitude_expected,
        falsifier_jsonb, emitted_at, lifecycle_status, driving_signals,
        frozen_bundle_hash, bundle_formula_version)
     VALUES
       ($1, 'pred-1', 'phala.anchors/x1', 'claim one', 'career',
        daterange('2026-01-01', '2026-12-31'), '2026-06-01',
        numrange(0.4, 0.6), 'moderate', '{}'::jsonb, now(), 'pending',
        '{}'::jsonb, repeat('c', 64), 'v1'),
       ($1, 'pred-2', 'phala.anchors/x2', 'claim two', 'health',
        daterange('2026-01-01', '2026-12-31'), '2026-06-01',
        numrange(0.4, 0.6), 'moderate', '{}'::jsonb, now(), 'due',
        '{}'::jsonb, repeat('d', 64), 'v1')`,
    [CHART_1],
  )
}

describe.skipIf(!ENABLED)(
  'E-635 narrowed proof — amjis_app / pariprashna_safety_decisions + mimamsa_predictions',
  () => {
    beforeAll(async () => {
      pool = new Pool({ connectionString: DB_URL })
      await admin(SAFETY_DECISIONS_FIXTURE)
      await admin(MIMAMSA_PREDICTIONS_FIXTURE)

      await admin(`
        DO $$ BEGIN
          IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'amjis_app') THEN
            CREATE ROLE amjis_app LOGIN;
          END IF;
        END $$;
        GRANT USAGE ON SCHEMA public TO amjis_app;
      `)
      // The exact privilege set confirmed LIVE in production on both tables
      // today: DELETE, UPDATE, INSERT, SELECT, TRIGGER, TRUNCATE, REFERENCES.
      await admin(`
        GRANT DELETE, UPDATE, INSERT, SELECT, TRIGGER, TRUNCATE, REFERENCES
          ON TABLE pariprashna_safety_decisions TO amjis_app;
        GRANT DELETE, UPDATE, INSERT, SELECT, TRIGGER, TRUNCATE, REFERENCES
          ON TABLE mimamsa_predictions TO amjis_app;
      `)

      appPool = connFor('amjis_app')
    }, 60_000)

    afterAll(async () => {
      await appPool?.end()
      await pool?.end()
    })

    describe('before migration 635 — RED', () => {
      it('confirms amjis_app holds DELETE/TRUNCATE/UPDATE on pariprashna_safety_decisions', async () => {
        const { rows } = await admin(
          `SELECT has_table_privilege('amjis_app', 'pariprashna_safety_decisions', 'DELETE') AS del,
                  has_table_privilege('amjis_app', 'pariprashna_safety_decisions', 'TRUNCATE') AS trunc,
                  has_table_privilege('amjis_app', 'pariprashna_safety_decisions', 'UPDATE') AS upd`,
        )
        expect(rows[0]).toEqual({ del: true, trunc: true, upd: true })
      })

      it('RED: amjis_app can DELETE rows out of pariprashna_safety_decisions', async () => {
        await seedSafetyDecisions()
        const del = await asApp(
          'DELETE FROM pariprashna_safety_decisions WHERE decision_id = $1',
          [DECISION_1],
        )
        expect(del.rowCount).toBe(1)
      })

      it('RED: amjis_app can UPDATE pariprashna_safety_decisions rows', async () => {
        await seedSafetyDecisions()
        const upd = await asApp(
          `UPDATE pariprashna_safety_decisions SET severity = 'advisory' WHERE decision_id = $1`,
          [DECISION_1],
        )
        expect(upd.rowCount).toBe(1)
      })

      it('RED: amjis_app can TRUNCATE pariprashna_safety_decisions entirely', async () => {
        await seedSafetyDecisions()
        await asApp('TRUNCATE pariprashna_safety_decisions')
        const remaining = await admin('SELECT count(*)::int AS n FROM pariprashna_safety_decisions')
        expect(remaining.rows[0].n).toBe(0)
      })

      it('confirms amjis_app holds TRUNCATE on mimamsa_predictions', async () => {
        const { rows } = await admin(
          `SELECT has_table_privilege('amjis_app', 'mimamsa_predictions', 'TRUNCATE') AS trunc`,
        )
        expect(rows[0]).toEqual({ trunc: true })
      })

      it('RED: amjis_app can TRUNCATE mimamsa_predictions entirely', async () => {
        await seedMimamsaPredictions()
        await asApp('TRUNCATE mimamsa_predictions')
        const remaining = await admin('SELECT count(*)::int AS n FROM mimamsa_predictions')
        expect(remaining.rows[0].n).toBe(0)
      })
    })

    describe('applying migration 635', () => {
      it('applies cleanly and is idempotent (safe to re-run)', async () => {
        const sql = readFileSync(MIGRATION, 'utf8')
        await admin(sql)
        await admin(sql) // second apply must not error — REVOKE-of-absent-privilege is a no-op
      })
    })

    describe('after migration 635 — GREEN', () => {
      it('confirms amjis_app no longer holds DELETE/TRUNCATE/UPDATE on pariprashna_safety_decisions', async () => {
        const { rows } = await admin(
          `SELECT has_table_privilege('amjis_app', 'pariprashna_safety_decisions', 'DELETE') AS del,
                  has_table_privilege('amjis_app', 'pariprashna_safety_decisions', 'TRUNCATE') AS trunc,
                  has_table_privilege('amjis_app', 'pariprashna_safety_decisions', 'UPDATE') AS upd`,
        )
        expect(rows[0]).toEqual({ del: false, trunc: false, upd: false })
      })

      it('GREEN: amjis_app gets permission-denied attempting DELETE on pariprashna_safety_decisions', async () => {
        await seedSafetyDecisions()
        await expect(
          asApp('DELETE FROM pariprashna_safety_decisions WHERE decision_id = $1', [DECISION_1]),
        ).rejects.toThrow(/permission denied/i)
        const remaining = await admin('SELECT count(*)::int AS n FROM pariprashna_safety_decisions')
        expect(remaining.rows[0].n).toBe(2)
      })

      it('GREEN: amjis_app gets permission-denied attempting UPDATE on pariprashna_safety_decisions', async () => {
        await seedSafetyDecisions()
        await expect(
          asApp(
            `UPDATE pariprashna_safety_decisions SET severity = 'advisory' WHERE decision_id = $1`,
            [DECISION_1],
          ),
        ).rejects.toThrow(/permission denied/i)
      })

      it('GREEN: amjis_app gets permission-denied attempting TRUNCATE on pariprashna_safety_decisions', async () => {
        await seedSafetyDecisions()
        await expect(asApp('TRUNCATE pariprashna_safety_decisions')).rejects.toThrow(
          /permission denied/i,
        )
        const remaining = await admin('SELECT count(*)::int AS n FROM pariprashna_safety_decisions')
        expect(remaining.rows[0].n).toBe(2)
      })

      it('NO REGRESSION: amjis_app can still SELECT and INSERT into pariprashna_safety_decisions', async () => {
        await seedSafetyDecisions()
        const sel = await asApp('SELECT count(*)::int AS n FROM pariprashna_safety_decisions')
        expect(sel.rows[0].n).toBe(2)

        const ins = await asApp(
          `INSERT INTO pariprashna_safety_decisions
             (decision_id, chart_id, turn_id, seq, enforced, severity, action, entry_hash)
           VALUES ($1, $2, $3, 3, true, 'none', 'proceed', repeat('e', 64))`,
          ['eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', CHART_1, TURN_1],
        )
        expect(ins.rowCount).toBe(1)
      })

      it('confirms amjis_app no longer holds TRUNCATE on mimamsa_predictions', async () => {
        const { rows } = await admin(
          `SELECT has_table_privilege('amjis_app', 'mimamsa_predictions', 'TRUNCATE') AS trunc`,
        )
        expect(rows[0]).toEqual({ trunc: false })
      })

      it('GREEN: amjis_app gets permission-denied attempting TRUNCATE on mimamsa_predictions', async () => {
        await seedMimamsaPredictions()
        await expect(asApp('TRUNCATE mimamsa_predictions')).rejects.toThrow(/permission denied/i)
        const remaining = await admin('SELECT count(*)::int AS n FROM mimamsa_predictions')
        expect(remaining.rows[0].n).toBe(2)
      })

      it('NO REGRESSION: amjis_app can still run the real cockpit-clear scoped DELETE on mimamsa_predictions', async () => {
        await seedMimamsaPredictions()
        // The exact shape assetClearSpec.ts derives / mi_bhavisya.py issues.
        const del = await asApp(
          `DELETE FROM mimamsa_predictions WHERE chart_id = $1 AND lifecycle_status IN ('pending', 'due')`,
          [CHART_1],
        )
        expect(del.rowCount).toBe(2)
      })

      it('NO REGRESSION: amjis_app can still run the real EL-58 lifecycle-sweep scoped UPDATE on mimamsa_predictions', async () => {
        await seedMimamsaPredictions()
        // The exact shape prediction_lifecycle_sweep.ts issues.
        const upd = await asApp(
          `UPDATE mimamsa_predictions SET lifecycle_status = 'expired' WHERE chart_id = $1 AND prediction_id = $2`,
          [CHART_1, 'pred-1'],
        )
        expect(upd.rowCount).toBe(1)
        const check = await admin(
          `SELECT lifecycle_status FROM mimamsa_predictions WHERE chart_id = $1 AND prediction_id = 'pred-1'`,
          [CHART_1],
        )
        expect(check.rows[0].lifecycle_status).toBe('expired')
      })

      it('NO REGRESSION: amjis_app can still SELECT and INSERT into mimamsa_predictions', async () => {
        await seedMimamsaPredictions()
        const sel = await asApp('SELECT count(*)::int AS n FROM mimamsa_predictions')
        expect(sel.rows[0].n).toBe(2)

        const ins = await asApp(
          `INSERT INTO mimamsa_predictions
             (chart_id, prediction_id, source_pramana_id, outcome_claim, domain,
              observation_window, eval_date, confidence_band, magnitude_expected,
              falsifier_jsonb, emitted_at, lifecycle_status, driving_signals,
              frozen_bundle_hash, bundle_formula_version)
           VALUES ($1, 'pred-3', 'phala.anchors/x3', 'claim three', 'wealth',
              daterange('2026-01-01', '2026-12-31'), '2026-06-01',
              numrange(0.4, 0.6), 'moderate', '{}'::jsonb, now(), 'pending',
              '{}'::jsonb, repeat('f', 64), 'v1')`,
          [CHART_1],
        )
        expect(ins.rowCount).toBe(1)
      })
    })
  },
)

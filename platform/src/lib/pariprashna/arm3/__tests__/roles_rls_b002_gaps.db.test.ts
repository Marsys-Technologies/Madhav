/**
 * P2 B-002 narrowed proof — E-002 (`chart_facts`/`chart_dashas` carry zero RLS) and
 * E-015 (table-owner bypass defeats a policy-only fix), reproduced as executable
 * detectors against a THROWAWAY scratch Postgres.
 *
 * ── THIS IS NOT A FIX ────────────────────────────────────────────────────────
 * Every test in this file documents an existing gap or hazard. None of them
 * assert that a protection exists — the opposite: they assert that a genuine
 * absence of protection is exactly what a real connection sees today, and (for
 * E-015) that Postgres's own owner-bypass semantics would defeat a policy-only
 * fix even if one were added. A future session that lands the real fix (see the
 * remediation plan in B002_NARROWED_PROOF_v1_0.md) should expect SOME of these
 * tests to start FAILING — that is how this file's job ends. Until then, P2
 * blocker B-002 stays OPEN.
 *
 * A genuine live fix (session-context plumbing so `role_web_serve` is actually
 * used, then extending migration 576's policy `spec` to cover these two tables,
 * then arming) was assessed and REJECTED as too risky for a single session — it
 * touches 162 files with zero production callers of the session-context plumbing
 * today. See campaign decision event_id `605d1071-df34-4b82-9ceb-f471f36e2969`
 * (Paripraśna Experience Assurance tracker) for the full rejection record.
 *
 * SKIPPED unless `G1C_DB_TEST=1` AND `G1C_DATABASE_URL` is set — same gate as
 * the sibling `roles_rls.db.test.ts`, same reasoning: this needs a live
 * Postgres, it CREATEs ROLES, ENABLEs ROW LEVEL SECURITY and ALTERs table
 * OWNERship, so it must run against a THROWAWAY / local database and NEVER
 * against the shared production DB. It is self-contained: it builds its own
 * fixture tables (including realistic `chart_facts` / `chart_dashas` shapes,
 * copied from migrations 204 and 206) and applies migration 576 itself.
 *
 *   createdb g1c_scratch
 *   G1C_DB_TEST=1 G1C_DATABASE_URL=postgres://postgres@127.0.0.1:5599/g1c_scratch \
 *     npx vitest run src/lib/pariprashna/arm3/__tests__/roles_rls_b002_gaps.db.test.ts
 *
 * Like `roles_rls.db.test.ts`, this talks to `pg` directly rather than through
 * `@/lib/db/client`, so it cannot accidentally inherit a `DATABASE_URL` pointing
 * at anything real — the connection string must be named explicitly, in its own
 * variable.
 */

import { readFileSync } from 'node:fs'
import path from 'node:path'

import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest'
import { Pool } from 'pg'

const DB_URL = process.env.G1C_DATABASE_URL
const ENABLED = process.env.G1C_DB_TEST === '1' && !!DB_URL

const MIGRATION = path.resolve(
  __dirname,
  '../../../../../supabase/migrations/576_pariprashna_roles_rls_arm3.sql',
)

const CHART_X = '11111111-1111-1111-1111-111111111111'
const CHART_Y = '22222222-2222-2222-2222-222222222222'

/**
 * The same subset-of-real-schema fixture as `roles_rls.db.test.ts` — migration
 * 576's §0 preflight refuses to apply if any of these 25 tables is missing, so
 * this file (being self-contained, like its sibling) must create them too. Not
 * duplicated as behaviour, only as enough structure for the preflight to pass
 * and the grant walls to attach to something real.
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

-- ── E-002 targets — real shapes, copied from the live schema ────────────────
-- chart_facts: platform/supabase/migrations/204_chart_facts.sql (verbatim column
-- set, indexes omitted — not needed to exercise the grant/RLS claim).
CREATE TABLE IF NOT EXISTS chart_facts (
  fact_id                  TEXT PRIMARY KEY,
  chart_id                 UUID NOT NULL,
  ayanamsha_id             TEXT NOT NULL,
  build_id                 UUID NOT NULL,
  fact_category            TEXT NOT NULL,
  fact_subject             TEXT NOT NULL,
  fact_key                 TEXT NOT NULL,
  fact_value_text          TEXT,
  fact_value_num           NUMERIC,
  fact_value_jsonb         JSONB,
  unit                     TEXT,
  citation_ref             TEXT NOT NULL,
  citation_human           TEXT NOT NULL,
  source_calculation       TEXT NOT NULL,
  verification_pass_status TEXT NOT NULL,
  engine_version           TEXT NOT NULL,
  salience_formula_ver     TEXT,
  computed_at              TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)
);

-- chart_dashas: platform/supabase/migrations/206_ga3_supporting_tables.sql
-- (verbatim column set, indexes omitted).
CREATE TABLE IF NOT EXISTS chart_dashas (
  dasha_row_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id                 UUID NOT NULL,
  ayanamsha_id             TEXT NOT NULL,
  build_id                 UUID NOT NULL,
  system_id                TEXT NOT NULL,
  level_n                  INT NOT NULL,
  parent_row_id            UUID,
  lord_graha               TEXT NOT NULL,
  lord_sign                TEXT,
  start_date               DATE NOT NULL,
  end_date                 DATE NOT NULL,
  start_iso                TIMESTAMPTZ NOT NULL,
  end_iso                  TIMESTAMPTZ NOT NULL,
  duration_days            NUMERIC NOT NULL,
  sandhi_flag              BOOLEAN NOT NULL DEFAULT FALSE,
  karaka_role_at_period    TEXT,
  verification_pass_status TEXT NOT NULL
    CHECK (verification_pass_status IN ('two_pass_verified','classical_match','divergent_flagged','single')),
  verification_method      TEXT NOT NULL,
  citation_ref              TEXT NOT NULL,
  citation_human            TEXT NOT NULL,
  computed_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  engine_version            TEXT NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, system_id, level_n, start_iso, build_id)
);
`

let pool: Pool
let servePool: Pool

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

describe.skipIf(!ENABLED)('P2 B-002 narrowed proof — E-002 and E-015 detectors', () => {
  beforeAll(async () => {
    pool = new Pool({ connectionString: DB_URL })
    await admin(FIXTURE)
    await admin(readFileSync(MIGRATION, 'utf8'))
    await admin(`
      DO $$ BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'g1c_serve') THEN
          CREATE ROLE g1c_serve LOGIN;
        END IF;
      END $$;
      GRANT role_web_serve TO g1c_serve;
    `)
    const base = new URL(DB_URL!)
    base.username = 'g1c_serve'
    base.password = ''
    servePool = new Pool({ connectionString: base.toString() })
  }, 60_000)

  afterAll(async () => {
    await servePool?.end()
    await pool?.end()
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // E-002 — chart_facts / chart_dashas carry zero row-level protection
  // ═══════════════════════════════════════════════════════════════════════════
  // Migration 576's §5 `spec` array (the list of tables it writes chart-context
  // policies for) does not name `chart_facts` or `chart_dashas` — they are L1
  // Gaṇita facts/dashas tables, out of scope for the Paripraśna P1 G1-C lane.
  // Meanwhile §3a's `GRANT SELECT ON ALL TABLES IN SCHEMA public TO
  // role_web_serve` is unconditional and covers every table that exists at
  // apply time, these two included. The result: role_web_serve (the role a
  // cut-over web app would serve requests as) can SELECT every row of both
  // tables, for every chart, with no filter at all.
  //
  // EVERY TEST BELOW DOCUMENTS THE GAP AS IT STANDS TODAY. None of them assert
  // a protection exists; the cross-chart-read test is expected to keep PASSING
  // until a real fix lands, and its PASS *is* the proof the gap is real.
  describe('E-002 — chart_facts / chart_dashas: no RLS, no policy, broad GRANT', () => {
    beforeEach(async () => {
      await admin('DELETE FROM chart_facts')
      await admin('DELETE FROM chart_dashas')
      await admin(
        `INSERT INTO chart_facts
           (fact_id, chart_id, ayanamsha_id, build_id, fact_category, fact_subject, fact_key,
            fact_value_text, citation_ref, citation_human, source_calculation,
            verification_pass_status, engine_version, computed_at)
         VALUES
           ('fact-x', $1, 'lahiri', gen_random_uuid(), 'sun', 'natal', 'sign',
            'Capricorn', 'ref-x', 'human-x', 'swiss_ephemeris', 'two_pass_verified', 'v1', now()),
           ('fact-y', $2, 'lahiri', gen_random_uuid(), 'sun', 'natal', 'sign',
            'Aries', 'ref-y', 'human-y', 'swiss_ephemeris', 'two_pass_verified', 'v1', now())`,
        [CHART_X, CHART_Y],
      )
      await admin(
        `INSERT INTO chart_dashas
           (chart_id, ayanamsha_id, build_id, system_id, level_n, lord_graha,
            start_date, end_date, start_iso, end_iso, duration_days,
            verification_pass_status, verification_method, citation_ref, citation_human,
            engine_version)
         VALUES
           ($1, 'lahiri', gen_random_uuid(), 'vimshottari', 1, 'Moon',
            '2000-01-01','2010-01-01','2000-01-01T00:00:00Z','2010-01-01T00:00:00Z', 3653,
            'two_pass_verified', 'classical_formula', 'ref-x', 'human-x', 'v1'),
           ($2, 'lahiri', gen_random_uuid(), 'vimshottari', 1, 'Sun',
            '2001-01-01','2011-01-01','2001-01-01T00:00:00Z','2011-01-01T00:00:00Z', 3652,
            'two_pass_verified', 'classical_formula', 'ref-y', 'human-y', 'v1')`,
        [CHART_X, CHART_Y],
      )
    })

    it("confirms migration 576's spec does not cover these tables — relrowsecurity is false on both", async () => {
      const { rows } = await admin(
        `SELECT c.relname, c.relrowsecurity FROM pg_class c
           JOIN pg_namespace n ON n.oid = c.relnamespace
          WHERE n.nspname = 'public' AND c.relname IN ('chart_facts', 'chart_dashas')
          ORDER BY c.relname`,
      )
      expect(rows).toEqual([
        { relname: 'chart_dashas', relrowsecurity: false },
        { relname: 'chart_facts', relrowsecurity: false },
      ])
    })

    it('confirms zero g1c (or any other) policies exist on either table', async () => {
      const { rows } = await admin(
        `SELECT count(*)::int AS n FROM pg_policies
          WHERE tablename IN ('chart_facts', 'chart_dashas')`,
      )
      expect(rows[0].n).toBe(0)
    })

    it('confirms role_web_serve holds SELECT on both via the unconditional §3a grant', async () => {
      const { rows } = await admin(
        `SELECT has_table_privilege('role_web_serve', 'chart_facts', 'SELECT') AS facts,
                has_table_privilege('role_web_serve', 'chart_dashas', 'SELECT') AS dashas`,
      )
      expect(rows[0]).toEqual({ facts: true, dashas: true })
    })

    // ══ THE OPEN-GAP DETECTOR — this PASSING is the proof E-002 is real ══════
    it('OPEN GAP: a session pinned to chart X reads chart Y chart_facts rows anyway', async () => {
      const r = await asServe(CHART_X, 'SELECT fact_id, chart_id FROM chart_facts ORDER BY fact_id')
      // If this table were protected the way life_events is (see the sibling
      // roles_rls.db.test.ts "chart-scoped RLS (armed)" suite), pinning to X
      // would return exactly one row. It returns both — there is no filter.
      expect(r.rows).toHaveLength(2)
      expect(r.rows.map((x) => x.chart_id).sort()).toEqual([CHART_X, CHART_Y].sort())
    })

    it('OPEN GAP: a session pinned to chart X reads chart Y chart_dashas rows anyway', async () => {
      const r = await asServe(CHART_X, 'SELECT chart_id, lord_graha FROM chart_dashas ORDER BY lord_graha')
      expect(r.rows).toHaveLength(2)
      expect(r.rows.map((x) => x.chart_id).sort()).toEqual([CHART_X, CHART_Y].sort())
    })

    it('OPEN GAP: an UNSET chart context still sees every chart\'s rows (fail-OPEN, not fail-closed)', async () => {
      // Contrast with the armed suite's "an UNSET chart context sees NOTHING"
      // test on life_events — that is the fail-closed behaviour a real policy
      // gives you. Here, with no policy at all, an unset context changes
      // nothing: the broad GRANT is the only control, and it grants everything.
      const r = await asServe(null, 'SELECT count(*)::int AS n FROM chart_facts')
      expect(r.rows[0].n).toBe(2)
    })
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // E-015 — table ownership defeats a policy-only RLS fix
  // ═══════════════════════════════════════════════════════════════════════════
  // All 360 public-schema tables in production are owned by the single serving
  // credential `amjis_app`. Postgres exempts a table's OWNER from its own RLS
  // policies unless `ALTER TABLE ... FORCE ROW LEVEL SECURITY` is set — and
  // g1c_arm_rls.sql's own header (§ "THE SAFETY QUESTION THIS SCRIPT ANSWERS
  // FOR ITSELF") already documents that FORCE is never set anywhere in this
  // codebase. So even a hypothetical future migration that added a real,
  // correctly-scoped chart-context policy for `chart_facts` / `chart_dashas`
  // would still leak every row to a connection that owns the table — which,
  // in production, the serving credential does.
  //
  // This suite reproduces that mechanism on a scratch copy of chart_facts'
  // shape, owned by a plain LOGIN role (`g1c_owner_serve`) that is neither a
  // superuser nor BYPASSRLS — isolating OWNERSHIP as the cause of the bypass,
  // not some broader "nothing is enforced" artifact of the scratch DB.
  //
  // NEITHER TEST BELOW IS A REGRESSION TEST FOR A FIX. The first documents the
  // hazard (bypass with RLS enabled, no FORCE). The second is a mechanism
  // check confirming FORCE is in fact the missing control — it does not mean
  // B-002 is closed; extending migration 576's policy `spec` to cover these
  // two tables AND setting FORCE on them is still future remediation work
  // (see B002_NARROWED_PROOF_v1_0.md's remediation plan).
  describe('E-015 — owner bypass on a scratch copy of chart_facts (hazard demonstration)', () => {
    const SCRATCH_TABLE = 'chart_facts_owner_bypass_scratch'
    let ownerPool: Pool

    beforeAll(async () => {
      await admin(`
        DO $$ BEGIN
          IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'g1c_owner_serve') THEN
            CREATE ROLE g1c_owner_serve LOGIN;
          END IF;
        END $$;
        GRANT USAGE ON SCHEMA public TO g1c_owner_serve;
      `)
      await admin(`
        DROP TABLE IF EXISTS ${SCRATCH_TABLE};
        CREATE TABLE ${SCRATCH_TABLE} (
          fact_id   TEXT PRIMARY KEY,
          chart_id  UUID NOT NULL,
          fact_key  TEXT NOT NULL,
          fact_value_text TEXT
        );
      `)
      // Ownership transfer is the whole point: in production, amjis_app is not
      // "a role granted access" to this table, it IS the table's owner — the
      // same relationship this ALTER creates for g1c_owner_serve here.
      await admin(`ALTER TABLE ${SCRATCH_TABLE} OWNER TO g1c_owner_serve`)
      await admin(`ALTER TABLE ${SCRATCH_TABLE} ENABLE ROW LEVEL SECURITY`)
      await admin(`DROP POLICY IF EXISTS scratch_chart_context ON ${SCRATCH_TABLE}`)
      // Reuses app_chart_context(), the real accessor migration 576 defines —
      // not a reimplementation, the actual function that would back a real fix.
      await admin(`
        CREATE POLICY scratch_chart_context ON ${SCRATCH_TABLE}
          AS PERMISSIVE FOR ALL TO g1c_owner_serve
          USING (chart_id = app_chart_context())
          WITH CHECK (chart_id = app_chart_context())
      `)

      const base = new URL(DB_URL!)
      base.username = 'g1c_owner_serve'
      base.password = ''
      ownerPool = new Pool({ connectionString: base.toString() })
    }, 60_000)

    afterAll(async () => {
      await ownerPool?.end()
      // Drop the scratch table entirely — this suite is not the only db-test
      // file that may run against this scratch DATABASE in one session, and a
      // sibling file's own global assertions (e.g. roles_rls.db.test.ts's
      // "RLS enabled on NOTHING" / "RLS enabled on exactly 21 tables" counts,
      // which scan ALL of `public`) would otherwise see this table's RLS state
      // as contamination left behind by an unrelated suite. Dropping it is the
      // honest cleanup — the hazard has already been demonstrated by the time
      // this runs.
      await admin(`DROP TABLE IF EXISTS ${SCRATCH_TABLE}`)
    })

    beforeEach(async () => {
      await admin(`DELETE FROM ${SCRATCH_TABLE}`)
      await admin(
        `INSERT INTO ${SCRATCH_TABLE} (fact_id, chart_id, fact_key, fact_value_text)
         VALUES ('fx', $1, 'sign', 'Capricorn'), ('fy', $2, 'sign', 'Aries')`,
        [CHART_X, CHART_Y],
      )
    })

    async function asOwner(chartId: string | null, sql: string) {
      const c = await ownerPool.connect()
      try {
        await c.query('BEGIN')
        if (chartId !== null) {
          await c.query('SELECT set_config($1, $2, true)', ['app.chart_context', chartId])
        }
        const r = await c.query(sql)
        await c.query('COMMIT')
        return r
      } finally {
        c.release()
      }
    }

    it('the scratch table really has RLS enabled and a real chart-context policy', async () => {
      const { rows } = await admin(
        `SELECT relrowsecurity, relforcerowsecurity FROM pg_class
          WHERE relname = '${SCRATCH_TABLE}'`,
      )
      expect(rows[0]).toEqual({ relrowsecurity: true, relforcerowsecurity: false })
      const policies = await admin(
        `SELECT count(*)::int AS n FROM pg_policies WHERE tablename = '${SCRATCH_TABLE}'`,
      )
      expect(policies.rows[0].n).toBe(1)
    })

    // ══ THE OWNER-BYPASS DETECTOR — this PASSING is the proof E-015 is real ══
    it('HAZARD: the table OWNER reads every row regardless of the chart-context pin — no FORCE set', async () => {
      const pinned = await asOwner(CHART_X, `SELECT chart_id FROM ${SCRATCH_TABLE} ORDER BY chart_id`)
      expect(pinned.rows).toHaveLength(2) // should be 1 if the policy actually applied to the owner
      expect(pinned.rows.map((r) => r.chart_id).sort()).toEqual([CHART_X, CHART_Y].sort())

      const unpinned = await asOwner(null, `SELECT count(*)::int AS n FROM ${SCRATCH_TABLE}`)
      // Under a real policy this should fail-closed to 0 with no pin — instead
      // ownership makes the pin irrelevant altogether.
      expect(unpinned.rows[0].n).toBe(2)
    })

    // ── Mechanism check, not a fix verification ──────────────────────────────
    it('MECHANISM CHECK: the SAME owner connection IS correctly scoped once FORCE is set', async () => {
      await admin(`ALTER TABLE ${SCRATCH_TABLE} FORCE ROW LEVEL SECURITY`)
      try {
        const pinned = await asOwner(CHART_X, `SELECT chart_id FROM ${SCRATCH_TABLE}`)
        expect(pinned.rows).toEqual([{ chart_id: CHART_X }])

        const unpinned = await asOwner(null, `SELECT count(*)::int AS n FROM ${SCRATCH_TABLE}`)
        expect(unpinned.rows[0].n).toBe(0) // fail-closed, same as the armed suite's un-owned tables
      } finally {
        // Restore the pre-FORCE state so this test is independent of run order
        // and of the hazard test above, which asserts NO FORCE is set.
        await admin(`ALTER TABLE ${SCRATCH_TABLE} NO FORCE ROW LEVEL SECURITY`)
      }
    })
  })
})

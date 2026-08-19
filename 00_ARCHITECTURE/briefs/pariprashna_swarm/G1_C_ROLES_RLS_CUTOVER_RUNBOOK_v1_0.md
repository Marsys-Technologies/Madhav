---
artifact: G1_C_ROLES_RLS_CUTOVER_RUNBOOK_v1_0
canonical_id: G1_C_ROLES_RLS_CUTOVER_RUNBOOK
version: 1.0
status: CURRENT — operational runbook for a cutover that has NOT been performed
produced_during: PARIPRASHNA-P1-FOUNDATION lane G1-C (Claude Code, 2026-08-19)
date: 2026-08-19
authority: NCD-5 (RULED (a), 2026-08-18) · PPR-21 / PPR-22 / PPR-26 / PPR-31
role: >
  The deliberate, operator-driven steps that turn lane G1-C's shipped-dark work
  into a live wall. Nothing in this document has been executed. The lane ships
  flag-OFF and DB-inert; this is the sequence that arms it, plus the two things
  the native explicitly withheld from the lane.
changelog:
  - "1.0 (2026-08-19): first issue, at G1-C close."
---

# G1-C — Roles, RLS, arm-1/arm-3: cutover runbook

## §0 — What was WITHHELD from the lane, and is therefore not here as an action

Two items were explicitly reserved by the native for a separate real-time
decision. The lane did not perform either, and this runbook records them as
**owner decisions**, not as steps an executor may take on their own authority:

1. **`amjis_app` credential rotation.** The roadmap row pairs it with "the
   CCD-004 rotation already owed". Read that citation precisely:
   `CROSS_CUTTING_DECISION_REGISTER_v1_0.md` §CCD-004's owed rotation is an
   **MCP credential inlined in a global Codex configuration URL** — an owner
   action, explicitly "not repository work". It is not itself an `amjis_app`
   rotation. What the two share is that both are owner-held secrets awaiting one
   rotation pass; scheduling them together is the sane move, and that is what
   "pairs with" should be taken to mean here.
2. **Switching the live application's connection to `role_web_serve`.** That is
   traffic-affecting and is §4 below, gated on the native's go-ahead.

**A third item, found during the lane and reported rather than acted on:** a
plaintext, live-shaped `amjis_app` password is committed at
`platform/python-sidecar/tests/l5/test_mi_bhara_circularity_guard_w2.py:295`. It
was NOT touched, moved, or rotated — rotation authority is withheld and a
silent edit would also destroy the audit trail. It belongs in the same rotation
pass as item 1.

## §1 — What is already true after this lane merges

Merging G1-C changes **nothing observable**. Specifically:

| Thing | State after merge |
|---|---|
| Migration `576_pariprashna_roles_rls_arm3.sql` | Applied by the normal deploy runner. Creates 5 NOLOGIN/NOBYPASSRLS roles **with no members**, the `pariprashna_ledger_outbox` table, the `app_chart_context()` accessor, and 42 RLS policies (21 tables × 2). |
| ROW LEVEL SECURITY | **Enabled on zero tables.** Policies exist and are never consulted. |
| `amjis_app` | Untouched. No GRANT, no REVOKE, no ALTER ROLE, no password change. |
| `MARSYS_FLAG_PARIPRASHNA_ROLE_SEPARATION` | `false` — reads use the one existing shared pool, by identity. |
| `MARSYS_FLAG_PARIPRASHNA_LEDGER_OUT_OF_PROCESS` | `false` — SAMĪKṢĀ capture writes the ledger in-process exactly as today. |
| The arm-3 worker | Exists as a script. Not scheduled, not deployed, no credential provisioned. |

## §2 — Pre-flight (read-only; run all of it before anything else)

```sql
-- 2a. The roles exist, cannot log in, cannot bypass RLS.
SELECT rolname, rolcanlogin, rolbypassrls, rolsuper
  FROM pg_roles WHERE rolname LIKE 'role\_%' ORDER BY 1;

-- 2b. 42 policies, RLS enabled nowhere yet.
SELECT count(*) FROM pg_policies WHERE policyname LIKE '%\_g1c\_%';          -- expect 42
SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE n.nspname='public' AND c.relrowsecurity;                              -- expect 0 (+ any pre-existing)

-- 2c. WHO OWNS THE TABLES. This decides whether §4 is safe or an outage.
SELECT DISTINCT pg_get_userbyid(c.relowner) AS owner, count(*)
  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE n.nspname='public'
   AND c.relname IN (SELECT DISTINCT tablename FROM pg_policies
                      WHERE policyname LIKE '%\_g1c\_chart\_context')
 GROUP BY 1;

-- 2d. TABLES role_web_serve CANNOT SEE. `GRANT SELECT ON ALL TABLES` is a
--     point-in-time snapshot; anything created after migration 576 is invisible
--     to the serving role. That is fail-CLOSED and correct, but it must be a
--     KNOWN list before the cutover, not a surprise afterwards.
SELECT c.relname
  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE n.nspname='public' AND c.relkind='r'
   AND NOT has_table_privilege('role_web_serve', c.oid, 'SELECT')
 ORDER BY 1;
```

Step 2d's output is the real pre-flight gate. Grant what genuinely belongs to the
serving role, in a NEW migration — never by editing 576 (§N.4: never edit an
applied migration).

## §3 — Arm arm-3 FIRST (flag order matters)

`PARIPRASHNA_LEDGER_OUT_OF_PROCESS` must flip **before**
`PARIPRASHNA_ROLE_SEPARATION`, not after. Once the app serves on
`role_web_serve` it has no ledger INSERT at all, so an in-process capture would
begin failing at the moment of cutover.

1. Provision a login user granted `role_ledger_write`:
   ```sql
   CREATE ROLE arm3_writer LOGIN PASSWORD '<from secret manager>';
   GRANT role_ledger_write TO arm3_writer;
   ```
2. Set `LEDGER_WRITER_DATABASE_URL` for the worker **only** (its own variable —
   the worker deliberately refuses to read `DATABASE_URL`).
3. Schedule the worker. The established shape in this repo is a GitHub Actions
   cron over the Cloud SQL Auth Proxy — `.github/workflows/samiksha-daily.yml`
   is the working precedent to copy:
   ```
   npx tsx platform/scripts/pariprashna/ledger_writer_worker.ts --once
   ```
   Exit 2 means "drained, but at least one intent failed" — alert on it.
4. Flip `MARSYS_FLAG_PARIPRASHNA_LEDGER_OUT_OF_PROCESS=true`.
5. Verify with a real reading: a prediction candidate should produce an outbox
   row, and the next worker run should turn it into a `detected` ledger row.
   ```sql
   SELECT count(*) FILTER (WHERE applied_at IS NULL) AS pending,
          count(*) FILTER (WHERE applied_at IS NOT NULL) AS applied,
          count(*) FILTER (WHERE last_error IS NOT NULL) AS failed
     FROM pariprashna_ledger_outbox;
   ```

**Known residual, deliberately not closed by this lane:** only the SYNTHESIS-path
write (`captureDetectedCandidates`) is routed through arm-3. The human-initiated
confirm and outcome-record paths still write in-process, and `create_confirmed`
in the outbox is a reserved slot whose drain handler throws
`ARM3_OP_NOT_IMPLEMENTED`. **Those paths must be routed before §4**, or the role
cutover breaks the review tab's confirm button. This is stated here rather than
papered over because §4 is not safe until it is done.

## §4 — The role cutover (traffic-affecting; needs the native's go-ahead)

1. Provision a login user granted `role_web_serve`; set `SERVE_DATABASE_URL`
   (or `DB_SERVE_USER` + `DB_SERVE_PASSWORD`).
2. Flip `MARSYS_FLAG_PARIPRASHNA_ROLE_SEPARATION=true`. Reads now run on
   `role_web_serve`. **Writes still run on the legacy pool** — this lane changed
   the READ path only, which is exactly what the roadmap row asks for ("Web app
   migrated off `amjis_app` for read paths").
3. Smoke the surfaces the grant wall touches, because the wall is real and a
   missing grant is a 500, not a warning: a reading end-to-end, the SAMĪKṢĀ
   review tab, the chart list, the cockpit.
4. Arm RLS:
   ```
   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 \
     -v g1c_app_role=role_web_serve \
     -f platform/scripts/pariprashna/g1c_arm_rls.sql
   ```
   The script MEASURES table ownership and refuses to arm if the app role does
   not own the tables, unless `-v g1c_accept_ownership_risk=yes` is passed
   consciously. Do not reach for that flag to make an error go away — read §2c
   first and understand which case you are in.
5. Rollback for step 4 is immediate and does not need a deploy:
   ```
   psql "$DATABASE_URL" -f platform/scripts/pariprashna/g1c_disarm_rls.sql
   ```
   Rollback for steps 1–2 is flipping the flag back to `false`.

**Every read path that touches a C1/C3 table must be wrapped in
`withChartContext()` before step 4**, or it will see zero rows. That wrapping is
NOT complete — the lane shipped the mechanism and its tests, not a sweep of every
call site. Treat "wrap the read paths" as the largest remaining piece of work
before this step is attemptable.

## §5 — Open questions for the native (raised, not decided)

1. **`role_web_serve` can SELECT ledger outcome columns.** TA §14.10 arm-1's
   literal text says the serving role should have "no SELECT on ledger outcome
   columns". Migration 576 does NOT column-revoke them, because the SAMĪKṢĀ
   review tab — a shipped surface, proven live by C4-LOOP-LIVE-PROOF — reads
   exactly those columns to show a human their resolved predictions. The
   invariant's purpose (outcome data must not reach GENERATION) is enforced today
   by arm-2. The clean answer is to split `role_web_serve` into a narrower
   generation role and a review role. That is an architecture decision, not an
   executor's call.
2. **`public.charts` is not given a chart-context policy.** It already carries
   its own baseline RLS keyed to `app.principal_id`, and the chart pin is DERIVED
   from `charts`, so a pin-filter on it would make "list my charts" impossible.
   Related honest finding: **nothing in the codebase sets `app.principal_id`
   today**, so the baseline `chart_service_policy` is unconditionally true — those
   policies are a §N.8 no-op-shaped signal. `withChartContext({ principalId })`
   can set it; turning it on for every caller is a live behaviour change nobody
   has ruled on.
3. **New tables are invisible to `role_web_serve` by default** (no
   `ALTER DEFAULT PRIVILEGES` anywhere in this repo, and the lane did not
   introduce the first one). Fail-closed is the right default for a serving role,
   but it needs to be a known operating rule, not a recurring surprise.

## §6 — What was verified, and where

All verification ran against a **local scratch Postgres 17** created for the
purpose. **Nothing was applied to the production database**; no production
credential was read, written, or rotated.

- Migration 576 applies cleanly and is idempotent (applied twice).
- 5 roles created NOLOGIN / NOBYPASSRLS / NOSUPERUSER, zero members.
- 42 policies created; RLS enabled on 0 tables (inertness).
- Grant wall proven with real sessions on real roles: `role_web_serve` denied
  ledger INSERT, denied calibration SELECT, denied consent-audit UPDATE/DELETE;
  `role_ledger_write` denied outbox INSERT.
- **Cross-context denial:** a session pinned to chart X reads only X's rows —
  direct `chart_id`, the C3 ledger, and the JOIN-reached `message_parts`. Unset
  and malformed pins see nothing (fail-closed). `WITH CHECK` blocks a write
  escaping its pin. The pin does not survive onto the next borrower of the pooled
  connection.
- The arming script's ownership detector REFUSES and rolls back when the app role
  does not own the tables, and proceeds with a loud WARNING only under explicit
  acceptance.
- arm-3 end-to-end: enqueue on `role_web_serve` → drain on `role_ledger_write` →
  a real `detected` ledger row, with `confidence` still NULL (W-1 preserved).

Suites: `src/lib/db/__tests__/roles.test.ts`,
`src/lib/pariprashna/arm3/__tests__/{outbox,arm3_out_of_process,roles_rls.db}.test.ts`.
The DB suite is opt-in via `G1C_DB_TEST=1` + `G1C_DATABASE_URL`, on its own
variable so it cannot inherit a `DATABASE_URL` pointing at anything real.

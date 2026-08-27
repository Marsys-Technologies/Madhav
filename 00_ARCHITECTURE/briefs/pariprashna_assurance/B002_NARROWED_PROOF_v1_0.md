---
artifact: B-002 narrowed proof — E-002/E-015 RLS gap detectors
version: "1.0"
status: NARROWED_PROOF_LANDED_BLOCKER_STILL_OPEN
as_of: "2026-08-28T00:40:00Z"
session: "Paripraśna Experience Assurance, P2, B-002 narrowed-proof lane"
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/P2_BLOCKER_INTAKE_v1_0.md (P2-B-002)
  - platform/supabase/migrations/576_pariprashna_roles_rls_arm3.sql
  - platform/scripts/pariprashna/g1c_arm_rls.sql
  - platform/src/lib/pariprashna/arm3/__tests__/roles_rls.db.test.ts
  - platform/src/lib/pariprashna/arm3/__tests__/roles_rls_b002_gaps.db.test.ts
decision_event_id: 605d1071-df34-4b82-9ceb-f471f36e2969
pr: https://github.com/Marsys-Technologies/Madhav/pull/1598
---

# B-002 narrowed proof — E-002/E-015 RLS gap detectors v1.0

## Verdict

**P2 blocker B-002 remains OPEN.** No production code, migration, role, or
credential changed. This session's disposition is the "narrowed proof" path:
instead of landing the real fix (rejected as too risky — see below), it adds
two real, executable test-based detectors that reproduce the exact mechanism
of findings E-002 and E-015 against a throwaway scratch Postgres, and formally
documents the gap and the ordered remediation plan a future session needs to
actually close it.

## The gap (E-002, E-015)

- **E-002**: `chart_facts` and `chart_dashas` — both L1 Gaṇita tables — carry
  **zero RLS objects**. `pg_class.relrowsecurity = false` on both; zero rows
  in `pg_policies` for either. Migration 576 (`576_pariprashna_roles_rls_arm3.sql`)
  is the migration that introduced chart-scoped RLS for Paripraśna's C1/C3
  tables, and its §5 `spec` array — the authoritative list of tables it writes
  a `<table>_g1c_chart_context` policy for — does not name either table; they
  were out of scope for that lane. Meanwhile its §3a grant
  (`GRANT SELECT ON ALL TABLES IN SCHEMA public TO role_web_serve`) is
  unconditional and covers every table that exists at apply time, these two
  included. Net effect: a `role_web_serve` session pinned to one chart's
  context can `SELECT` every other chart's `chart_facts` / `chart_dashas` rows
  with no filter at all — there is no protection to bypass, because none was
  ever written for these two tables.

- **E-015**: even if a future migration added a correctly-scoped chart-context
  policy for these two tables, it would not be sufficient on its own. All 360
  `public`-schema tables in production are owned by the single serving
  credential `amjis_app`. Postgres exempts a table's **owner** from its own RLS
  policies unless `ALTER TABLE ... FORCE ROW LEVEL SECURITY` is set, and zero
  tables anywhere have FORCE set. `g1c_arm_rls.sql`'s own header comments
  already document this exact hazard for the tables migration 576 *did* wall
  ("Enabling RLS on a table denies every role for which no policy grants
  access... (a) `amjis_app` OWNS the table. Table owners bypass RLS unless
  FORCE ROW LEVEL SECURITY is set (it is not, anywhere). Arming is then a
  no-op for the running application, and safe.") — which is candid about safety
  (arming won't break the app) but is the same fact stated as a hazard: **RLS
  alone, without FORCE, provides zero real protection for a connection that
  owns the table it is enabled on.** A policy-only fix for `chart_facts` /
  `chart_dashas` would ship a false sense of security unless FORCE is set too
  — and setting FORCE on tables the live serving connection currently owns
  would, per the arm script's own logic, either be a safe no-op (if the app is
  not yet cut over) or an immediate outage (if it is), which is exactly why
  arming is gated on a measured ownership check today.

## Why a live fix was rejected this session

A genuine live remediation was assessed: build the session-context plumbing
so a real `role_web_serve` login credential actually serves requests (rather
than the historic single `amjis_app` credential), extend migration 576's
`spec` array to add `chart_facts` and `chart_dashas`, then run
`g1c_arm_rls.sql` to arm RLS on the now-complete policy set. This was
**rejected as too risky for a single session**: the session-context plumbing
(`setChartContext()` / `app.chart_context` GUC wiring) has **zero production
callers today across 162 files** — landing it live, correctly, end-to-end, in
one session was judged an unacceptable risk of a partial or silently-broken
cutover. The decision is recorded in the Paripraśna Experience Assurance
campaign tracker as **event_id `605d1071-df34-4b82-9ceb-f471f36e2969`**.

The accepted alternative — this lane's actual output — is a TEST-ONLY
reproduction of both findings as detectors, run only against a throwaway
scratch database, never against any shared or production database.

## The test-based proof added

New file: `platform/src/lib/pariprashna/arm3/__tests__/roles_rls_b002_gaps.db.test.ts`,
a sibling of the existing `roles_rls.db.test.ts` (same conventions: gated
behind `G1C_DB_TEST=1` + `G1C_DATABASE_URL`, self-contained — builds its own
fixture tables, including real `chart_facts` / `chart_dashas` shapes copied
from migrations 204 and 206, and applies migration 576 itself).

Two describe blocks, nine tests total:

- **`E-002 — chart_facts / chart_dashas: no RLS, no policy, broad GRANT`**
  (6 tests) — confirms `relrowsecurity = false` on both tables, confirms zero
  `pg_policies` rows for either, confirms `role_web_serve` holds `SELECT` on
  both via the §3a grant, and then the core detector: a session pinned to
  chart X reads chart Y's rows anyway, for both tables, and an unset chart
  context sees every chart's rows (fail-OPEN, contrasted explicitly against
  the sibling suite's fail-closed behaviour on the tables migration 576 *does*
  protect).
- **`E-015 — owner bypass on a scratch copy of chart_facts (hazard demonstration)`**
  (3 tests) — creates a scratch table shaped like `chart_facts`, transfers
  ownership to a plain `LOGIN` role with no `SUPERUSER`/`BYPASSRLS` attribute
  (isolating ownership specifically as the cause), enables RLS, and attaches a
  real chart-context policy using the actual `app_chart_context()` function
  migration 576 defines. Confirms RLS is genuinely on and the policy genuinely
  exists; then the hazard detector: the owner connection reads every chart's
  rows regardless of the pin, with no FORCE set; then a mechanism check
  confirming the SAME owner connection **is** correctly scoped once
  `FORCE ROW LEVEL SECURITY` is set (proving FORCE, specifically, is the
  missing control — restored to `NO FORCE` afterward so the test is order-
  independent).

Every test is commented as documenting an existing gap or hazard, explicitly
not a regression test for a fix — several are named `OPEN GAP:` / `HAZARD:` /
`MECHANISM CHECK:` in their titles. Their current PASS is the proof the
gap/hazard is real; a future session landing the real fix should expect some
of them to start FAILING, which is how this file's job ends.

### Real test output (throwaway local Postgres 17, never production)

Provisioned via `initdb` fresh into a scratch data directory, listening only
on `127.0.0.1:5599` with its own throwaway data dir — no docker daemon was
available in this environment, so a local `postgresql@17` (Homebrew) instance
was used instead. `G1C_DATABASE_URL` was set explicitly to this instance only;
the app's real `DATABASE_URL` was never read or referenced by the test run.

Standalone run, new file only:

```
$ G1C_DB_TEST=1 G1C_DATABASE_URL="postgres://postgres@127.0.0.1:5599/g1c_scratch" \
    npx vitest run src/lib/pariprashna/arm3/__tests__/roles_rls_b002_gaps.db.test.ts --reporter=verbose

 ✓ E-002 — ... > confirms migration 576's spec does not cover these tables — relrowsecurity is false on both
 ✓ E-002 — ... > confirms zero g1c (or any other) policies exist on either table
 ✓ E-002 — ... > confirms role_web_serve holds SELECT on both via the unconditional §3a grant
 ✓ E-002 — ... > OPEN GAP: a session pinned to chart X reads chart Y chart_facts rows anyway
 ✓ E-002 — ... > OPEN GAP: a session pinned to chart X reads chart Y chart_dashas rows anyway
 ✓ E-002 — ... > OPEN GAP: an UNSET chart context still sees every chart's rows (fail-OPEN, not fail-closed)
 ✓ E-015 — ... > the scratch table really has RLS enabled and a real chart-context policy
 ✓ E-015 — ... > HAZARD: the table OWNER reads every row regardless of the chart-context pin — no FORCE set
 ✓ E-015 — ... > MECHANISM CHECK: the SAME owner connection IS correctly scoped once FORCE is set

 Test Files  1 passed (1)
      Tests  9 passed (9)
```

Combined run with the pre-existing sibling suite, against a freshly recreated
scratch DB, run sequentially (`--fileParallelism=false` — see note below on why
concurrent DDL against one shared scratch DB is not a safe way to invoke two
migration-applying `.db.test.ts` files at once):

```
$ G1C_DB_TEST=1 G1C_DATABASE_URL="postgres://postgres@127.0.0.1:5599/g1c_scratch" \
    npx vitest run src/lib/pariprashna/arm3/__tests__/roles_rls.db.test.ts \
                    src/lib/pariprashna/arm3/__tests__/roles_rls_b002_gaps.db.test.ts \
    --fileParallelism=false

 Test Files  2 passed (2)
      Tests  29 passed (29)
```

All 20 pre-existing tests in `roles_rls.db.test.ts` still pass unchanged —
confirmed no regression from this addition.

Both results are real, live query outcomes from an actual Postgres backend —
no fixture or mock stands in for any assertion. (An initial combined run
without `--fileParallelism=false` hit a transient Postgres
`tuple concurrently updated` error from two files' migration DDL racing on
shared catalog rows in the same live database — a real Postgres concurrency
fact, not a defect in either suite's logic; each file is designed to be run
against its own scratch DB per its own header, and the sequential re-run
above confirms both suites are individually and jointly correct.)

## PR

<https://github.com/Marsys-Technologies/Madhav/pull/1598> — **not merged**.
Branch `pariprashna/p2-b002-narrowed-proof`, built in an isolated worktree at
`.clone/worktrees/pariprashna-b002-narrowed-proof` off `origin/main`
(`cc6b1a55e`). Title: "test(pariprashna/p2-b002): document E-002/E-015 RLS gaps
via opt-in scratch-DB detectors — no production change".

## Ordered future-remediation plan

The real fix is layered — each step below is a precondition for the next, and
skipping ahead reproduces exactly the risk this session declined to take on
in one pass:

1. **Route confirm / outcome-ledger writes through arm-3.** Land real callers
   for the arm-3 outbox seam (`pariprashna_ledger_outbox` +
   `platform/src/lib/pariprashna/arm3/{outbox,drain}.ts`) so ledger
   confirm/outcome writes actually flow through the out-of-process writer
   path migration 576 built room for, rather than remaining in-process.
2. **Sweep the TS read paths onto `withChartContext`.** Every serving-path
   query that reads a chart-scoped table needs to actually call
   `setChartContext()` (`platform/src/lib/db/roles.ts`) and run under it —
   today this has zero production callers across 162 files; this step is
   the bulk of the risk this session declined to absorb in one pass.
3. **Build the Python-sidecar session-context equivalent, then cut over
   `role_orchestrator`.** The sidecar (`platform/python-sidecar/pipeline/
   orchestrator/db.py`) needs its own analogue of the chart-context pin
   before the build path can run under a role narrower than a superuser-like
   credential.
4. **Provision the `role_web_serve` login credential and cut the web app over
   to it.** Only after steps 1–3 land is it safe to make `role_web_serve` the
   credential the app actually serves requests as (today it is a NOLOGIN
   group role with no members outside test suites).
5. **Extend migration 576's policy `spec` array to cover `chart_facts` and
   `chart_dashas`.** A new, surgical, verified migration (per CLAUDE.md §N.4)
   adding both tables to the `DO $policies$` spec list, closing E-002 as
   written.
6. **Set `FORCE ROW LEVEL SECURITY` where it is currently absent everywhere —
   not just on the two new tables.** This is a **necessary addition to
   `g1c_arm_rls.sql` itself**, which today only ever runs bare
   `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` and never sets FORCE (verified
   by reading the script in full during this session). Per E-015, arming
   without FORCE is safe-but-inert for an owner-connection and a false sense
   of security for a fix that assumes it protects that connection. This step
   should be added to the arm script's own detector logic, gated the same way
   the existing ownership check is (measure, then require an explicit
   `accept_risk`-style override) before flipping to require FORCE by default.
7. **Flip the `PARIPRASHNA_LEDGER_OUT_OF_PROCESS`-equivalent readiness gate**
   once steps 1–6 are live and verified, so the wall the migration and arm
   script build is actually enforced for these two tables' live traffic.
8. **Run `g1c_arm_rls.sql`** (updated per step 6) against production, per its
   own runbook (`G1_C_ROLES_RLS_CUTOVER_RUNBOOK_v1_0.md`), only once an
   operator has independently verified steps 1–7 and accepted the ownership
   risk report the script itself produces.

No step above was executed this session. This document and the linked PR are
the complete record of what *was* done: reproduction, not remediation.

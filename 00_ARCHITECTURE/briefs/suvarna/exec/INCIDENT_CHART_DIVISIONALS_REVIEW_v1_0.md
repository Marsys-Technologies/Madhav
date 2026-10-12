---
artifact: INCIDENT_CHART_DIVISIONALS_REVIEW
version: "1.0"
status: SS-APPROVED-ON-HOLD
produced_by: exec-suvarna (analysis lane)
date: 2026-10-01
base_commit: origin/main 066c58587358537d76880712241562e5f6ce722d
related: TRACK_I_FIX_ITEMS.md I-11 (branch TI-i11-divisionals-001, read-only), BUILDER_GRANT_PLAN (branch grant-plan-001, read-only), reader_grants.py (D6 in-process pattern), CF-16 (L1 briefs)
execution: NONE against any real system. Analysis only: no policy, DDL, admin action, DB write, push, PR, workflow or CLAUDE.md change. Every SQL statement and plan below is a draft. The only database access was read-only as `suvarna_reader` (SELECT and catalog reads); what that role cannot see is listed in Part IV.
approval_needed: SS `APPROVED <plan hash>` for the printed plan hash of a dry run, plus the owner's standing authorization in the executing session. Nothing here is available to this lane to run.
hold: "2026-10-01: SS APPROVED count 6d9745dd8005fa2a1845aa2326c101472f3d3db12794478db9f08e6ddf02953f and apply D 531c0940ae6eb654972e3401fd317f95cf2051cca10ae7249ff44e420a741aad, then ordered HOLD after the owner told Pravaha \"don't worry about it, any which way, we will rebuild it\". Do not run unless the owner says otherwise in the executing session. The access fix is the precondition of any ga_vargas rebuild (rebuild plan v1.1, P0b)."
changelog:
  - "1.0.1 (2026-10-01): status set to SS-APPROVED-ON-HOLD (see hold field); no content change."
  - "1.0 (2026-10-01): first draft. Restructured on SS's scope change: Part I is the stand-alone, minimal incident fix (chart_divisionals only, not bundled with the builder grant plan); Parts II-III hold the secondary and follow-up material."
---

# Incident review: `chart_divisionals` reads empty for every role (2026-10-01)

Contents: **Part I** the incident and the minimal fix (stands alone) · **Part II** secondary: the exact count statement, the other fix option · **Part III** follow-ups, not part of the incident fix · **Part IV** unknowns · **Appendix** draft plan texts and hashes.

---

# PART I. INCIDENT REVIEW AND MINIMAL FIX (stands alone)

**What is wrong.** Since migration 1035 (applied 2026-09-18 10:48Z) moved `chart_divisionals` to the NOLOGIN owner `data_plane_l1_owner`, no login role can see a single row of it. The table has row-level security ON (`relrowsecurity` true, `relforcerowsecurity` false) and ZERO policies, so every non-owner gets PostgreSQL's default-deny (`row_security_active` true for `suvarna_reader`; `EXPLAIN` shows `One-Time Filter: false`). Before 09-18 the owner was `amjis_app`, and a table owner bypasses RLS, so everything worked. Product symptom, observed today with the read-only `chart_snapshot` tool: **the D1 and D9 grids are empty (every sign `occupants: []`) for all three charts** (canonical `482012f1-710e-4a25-994a-93821f5871aa`, `1c826d5a-41cb-4450-b4dc-59d440e5f75a`, `cb73cd3d-9eba-4220-9902-0de91566e980`) while `ganita_positions_get` (`chart_facts`, RLS off) works. The app's own runtime role is blind.

**Is the data intact? Very probably yes (fix is ACCESS; a restore or rebuild on this evidence would be harmful), pending one owner-path count.** Evidence: heap 51,175,424 bytes, 6,247 pages, `reltuples` 71,476 (a truncated table would be 0 pages; for scale `chart_dashas` is 130,924 pages); no foreign key points into the table and no delete path ran (Part II.A); columns derived FROM it are populated: `ga_condition_composite.varga_dignity_composite` non-null on 45 of 45 canonical rows (0 of 45 on the other two charts, see Part IV) and `chart_dashas.lord_natal_dignity_d1` non-null on 292,354 of 483,870 canonical rows (`ga_dashas_writer.py:579-587,664` reads `chart_divisionals`); the only policy 002 ever created targeted a `service_role` that does not exist on this instance. The throughput figures that looked inconsistent (24,400 / 38,620 / 38,620 vs 71,476) reconcile once the F-A3 over-count is accounted for (Part II.A). Still a reading: the exact count settles it.

**What the cutover gate pins (read-only, exact).** It pins the SET OF POLICIES and does NOT pin RLS being on:
- `platform/scripts/data-plane-ownership-status.ts:353-417`. `:354-359` `expected_policies` = `l1_data_plane_policy_attestations` UNION ALL `l2_...`; `:360-366` `actual_policies` from `pg_policy` for the 12 L1 + L2 protected tables; `:378-384` a FULL JOIN on table, policy name, command, permissive, role oids, USING and CHECK expressions, `WHERE a.table_name IS NULL OR e.table_name IS NULL` (any one-sided row is "unsafe"); `:417` throws `Protected policies, views, or default privileges drift detected.`
- The attestation is populated once, at `platform/supabase/migrations/1035_data_plane_l1_producer_history.sql:1972-1992` (snapshot of live `pg_policy` rows; none existed for `chart_divisionals`) and is immutable to UPDATE/DELETE (`:1994-1997`). Live: `l1_data_plane_policy_attestations` has 0 rows. So ANY policy added to a protected table fails the gate until a matching attestation row exists.
- Nothing in `platform/scripts`, `platform/src` or `platform-mcp/src` reads `relrowsecurity` for the data-plane tables (grep `relrowsecurity|relforcerowsecurity|row_security|rowsecurity`: only the unrelated Pariprashna g1c scripts and `1039_purna_inquiry_protected_ownership.sql:111`, which pins RLS-on for a different set of tables). `data-plane-ownership-preflight.ts` mentions only `rolbypassrls` of roles (`:180,:197`).

**Choice: Option D, `ALTER TABLE public.chart_divisionals DISABLE ROW LEVEL SECURITY`.** Smallest gate change: NONE (no script change, no attestation row, no test change required). Option P (policies) needs three oid-bearing attestation rows inserted into an immutable table plus a gate-test addition, and still leaves `data_plane_migrator`, `data_plane_l2_owner` and `suvarna_reader` blind unless more policies are added (Part II.B). After D the table matches its 11 L1 siblings (`chart_facts`, `chart_dashas`, ... all `relrowsecurity` false); isolation stays where it always was for these tables (application layer, chart_id scoping, `authorizeChartAccess`).

**The fix: one transaction, D6 in-process owner path** (pattern of `reader_grants.py`: administrator secret fetched inside the process and never printed; local Cloud SQL proxy 127.0.0.1:5433; commit only if the before/after diff equals the plan; `--dry-run` rolls back; `--apply --expect-plan <hash>` refuses on a hash mismatch). Statements, in order:
1. `SET LOCAL search_path = pg_catalog, pg_temp;` `SET LOCAL lock_timeout = '5s';`
2. Transient membership only if missing (as in `reader_grants.py`): `GRANT data_plane_l1_owner TO postgres` (postgres is not currently a member; `data_plane_migrator` is).
3. Before-snapshot: ACL of every `public` relation, `(relname, relrowsecurity, relforcerowsecurity)` of every `public` table, `pg_policy`, role memberships. Pre-state probe as the real runtime roles (in-transaction transient memberships, `SET LOCAL ROLE`, then `RESET ROLE`): `SELECT count(*) FROM public.chart_divisionals` as `amjis_app`, `data_plane_builder`, `data_plane_verifier` (each expected 0 BEFORE: this reproduces the defect under the exact roles).
4. `SET LOCAL ROLE data_plane_l1_owner;` owner-path count per chart (the statements in Part II.A) and abort if any chart reads 0 (that would be the "deleted" branch, not this fix);
   `ALTER TABLE public.chart_divisionals DISABLE ROW LEVEL SECURITY;` `RESET ROLE;`
5. Same probe as step 3 as the three runtime roles: each must now equal the owner count, per chart. Remove the transient memberships. After-snapshot.
6. **Commit only if:** `relrowsecurity` diff over all `public` tables is exactly `[chart_divisionals true -> false]`; `relforcerowsecurity`, `pg_policy`, relation ACL and membership diffs are empty; the three runtime-role counts equal the owner count and are > 0 for each of the three charts; `--expect-plan` equals the plan hash. Otherwise ROLLBACK.

Lock: `ALTER TABLE ... DISABLE ROW LEVEL SECURITY` takes ACCESS EXCLUSIVE on `chart_divisionals` for the instant it runs; `lock_timeout 5s` makes it fail loudly rather than queue (no write path is running: Part I pre-conditions). Draft plan hash (text in the Appendix; the live script's own dry-run prints the one SS must quote): apply `531c0940ae6eb654972e3401fd317f95cf2051cca10ae7249ff44e420a741aad`.

**Pre-conditions.** No `planned/running/paused` build run (read just now: `build_runs` states are only completed 302, failed 419, stopped 14; since the cutover exactly one run has started, `8684032d` on 2026-10-01 15:01Z for `ka_gochara_resonance`, which failed after 1.3 s with no asset started: 0 `build_run_assets` rows since 09-18); no deploy or migration running (D6 standing rule; a catalog change is instantaneous and not gate-pinned, so this is a rule, not a technical need); do NOT refresh `mv_chart_vargas_summary` or `mv_chart_super_vargottama_bodies` (owned by `amjis_app`, so a refresh would read through RLS and could bake in zero rows) until after the fix.

**Verification (all must pass; V1-V3 are read-only checks the analysis lane can run after the commit).**
- **V1** catalog as `suvarna_reader`: `relrowsecurity` false, `row_security_active('chart_divisionals')` false, `pg_policy` 0 rows.
- **V2** `suvarna_reader` exact count per chart and per `(chart, ayanamsha, varga)` (statements C1-C3 of Part II.A run as the reader): equals the owner-path count.
- **V3** gate: `data-plane-ownership-status.ts` under the reader prints `marked` (D6 runbook command).
- **V4** app-role count per chart: a product read as `amjis_app` (`get_divisionals`, handler `SELECT * FROM chart_divisionals WHERE chart_id = $1`, `get_divisionals.ts:90`) returns the same row count per chart; the in-transaction probe of step 5 already proved it before commit.
- **V5** canary: `chart_snapshot` for each of the three charts shows non-empty D1 and D9 grids (every graha present in some sign; canonical: Sun in Capricorn and Lagna in Aries in D1, the FORENSIC anchors).
- **V6** owner-path exact count per chart re-run after the commit equals the pre-commit count (nothing moved).

**Rollback.** `ALTER TABLE public.chart_divisionals ENABLE ROW LEVEL SECURITY;` as `data_plane_l1_owner` through the same executor (draft hash `0743026095a85e9a43135c3b72375f2cf7f4d7e91e398e5f05e26dab1f6853d5`); commit only if the diff is exactly `[chart_divisionals false -> true]`. This restores the blind state (the incident), so use it only for an exposure concern. No data is touched by apply or rollback.

**What this fix does NOT do.** It does not rebuild anything, does not touch the builder grant plan, adds no guard (follow-ups, Part III), and does not add a repo migration (fresh databases built from `002_ganita_divisionals.sql` would re-enable RLS; a guarded parity migration is a Part III follow-up and `002`/`1035` must never be edited).

---

# PART II. SECONDARY

## A. The owner-path exact count (read-only, never commits)

**Method.** Same executor and secret as the fix, same D6 pattern, but the transaction is rolled back, never committed. `postgres` has no table privilege and is not `BYPASSRLS` (`rolbypassrls` false), so it reads the table only as the owner: `SET LOCAL ROLE data_plane_l1_owner` (owner, `relforcerowsecurity` false, so RLS does not apply to it). The transient `GRANT` must come BEFORE `SET TRANSACTION READ ONLY` (a read-only transaction rejects GRANT); the final `ROLLBACK` removes the membership. Alternative that needs no membership change: log in as `data_plane_migrator` (already a member of the owner, NOINHERIT) and `SET LOCAL ROLE data_plane_l1_owner` (the way `attestDataPlaneMigrations` does, `data-plane-migration-attestation.ts:63`); needs that login's secret. PostgreSQL 15.18. Not run by this lane.

```sql
BEGIN;
SET LOCAL search_path = pg_catalog, pg_temp;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';
-- only if pg_has_role('postgres','data_plane_l1_owner','MEMBER') is false:
GRANT data_plane_l1_owner TO postgres;
SET LOCAL ROLE data_plane_l1_owner;
SET TRANSACTION READ ONLY;
-- C0: abort unless current_user = data_plane_l1_owner, transaction_read_only = on, row_security_active = false
SELECT current_user, session_user, current_setting('transaction_read_only'), row_security_active('public.chart_divisionals');
-- C1 per chart
SELECT chart_id, count(*) AS n FROM public.chart_divisionals GROUP BY chart_id ORDER BY chart_id;
-- C2 per chart and ayanamsha
SELECT chart_id, ayanamsha_id, count(*) AS n FROM public.chart_divisionals GROUP BY chart_id, ayanamsha_id ORDER BY chart_id, ayanamsha_id;
-- C3 per chart, ayanamsha, varga
SELECT chart_id, ayanamsha_id, varga, count(*) AS n FROM public.chart_divisionals GROUP BY chart_id, ayanamsha_id, varga ORDER BY chart_id, ayanamsha_id, varga;
-- C4 provenance and timeline
SELECT chart_id, build_id, count(*) AS n, min(created_at) AS first_at, max(created_at) AS last_at FROM public.chart_divisionals GROUP BY chart_id, build_id ORDER BY chart_id, build_id;
-- C5 totals
SELECT count(*) AS total, count(DISTINCT chart_id) AS charts FROM public.chart_divisionals;
ROLLBACK;
```
Draft plan hash `6d9745dd8005fa2a1845aa2326c101472f3d3db12794478db9f08e6ddf02953f` (Appendix). The columns exist (`chart_id, graha, ayanamsha_id, varga, fact_category, fact_key, build_id, created_at`, 31 columns in all).

**Figures to compare, and why they do not reconcile at face value.**

| source | C `482012f1` | A `1c826d5a` | B `cb73cd3d` | total |
|---|---|---|---|---|
| `asset_throughput.rows_written` (ga_vargas, lit) | 24,400 (09-07 11:03Z) | 38,620 (07-26) | 38,620 (07-27) | 101,640 |
| `pg_class.reltuples` (estimate, analyze date unknown) | | | | 71,476 |
| registry `target_floor` (aspirational, not a gate) | 22,092 | | | |

- **The three throughput numbers are not the same kind of number.** `ga_vargas_writer.py:2738-2760` (PR #1766, 2026-09-05, F-A3) changed `_write_rows_batch` to return the driver's affected-row count instead of `len(rows)`. The F-A3 test header (`ga_writers/__tests__/test_ga_vargas_delete_grain.py`) records the defect: "`asset_throughput.rows_written` read 38,620 against 23,542 live, a 39% loss reported as a clean build" on chart 482012f1, because later passes in the same build deleted earlier passes' rows (`replace_prior_chart_divisionals`, `_idempotency.py:106`, delete grain = chart x varga x ayanamsha) and `ON CONFLICT DO NOTHING` skipped collisions. So **38,620 is an attempted count (pre-fix, written July 26-27 for A and B), and the rows actually live for A and B were about 23.5k each, not 38,620.** C's 24,400 (09-07, after the fix) is a landed count.
- **SS's candidate decomposition: is 71,476 = 24,400 + 38,620 + 8,456?** Arithmetically yes (71,476 - 63,020 = 8,456), but it has no meaning: it pairs one chart's attempted count with the others and invents a residual. The reading the evidence supports: 71,476 - 24,400 = 47,076 = A_live + B_live, i.e. about 23,538 per chart, within 4 rows of the 23,542 measured for the canonical chart before the fix. A second reading is equally consistent: `reltuples` taken before C's rebuild with all three charts near 23.8k (71,476 / 3 = 23,825). The two readings cannot be told apart from the reader; both say the table was populated (about 71.4k rows) when it was last analyzed, which can only have been before the 2026-09-10 stats reset (stats since: 0 inserts, 0 deletes, 0 analyze). The owner-path counts decide.
- **No closed-form "vargas x grahas x ayanamsha" expectation exists.** The writer iterates 5 ayanamshas (`CANONICAL_AYANAMSHAS`: lahiri_chitrapaksha, true_chitra, krishnamurti, raman, surya_siddhanta_classical) x up to 30 vargas (`ALL_30_VARGAS`, D81 skipped) x 10 classical bodies, but emits a variable number of fact rows per (ayanamsha, varga) across about 20 builders (position, dignity, vargottama, house/lord, deity, formula variants, D30 lords, vimsopaka, ashtakavarga, saptavargaja, karaka, pushkara, harmonics, `INVARIANT` sentinels...). The F-A3 test cites 147 rows across 10 fact_categories for a typical varga. Compare per-chart totals and the per-ayanamsha split (24,400 / 5 = 4,880 if the five are equal; not verified).

**How to read the result.**
| owner-path result | meaning | action |
|---|---|---|
| C near 24,400; A and B each between 22,092 and 38,620 (about 23.5k expected); total near 71.5k | INTACT | apply Part I only; no rebuild |
| A or B equals 38,620 | intact; the F-A3 loss did not affect that chart | apply Part I only |
| any chart 0, or total far below 71k, or a single ayanamsha/varga missing | deleted or partial | Part I still first (a rebuild cannot write under RLS), then a `ga_vargas` rebuild for the affected chart(s) and the 61-asset closure plus `ga_dashas` = production build = SS REVIEW; find the delete before rebuilding |

**Delete paths checked (from I-11, re-confirmed where cheap).** FK into the table: none (out: `chart_id -> charts ON DELETE CASCADE`, charts for all three exist). Triggers: `l1_data_plane_capture` (AFTER INSERT/UPDATE) and `l1_data_plane_mutation_guard` (BEFORE INSERT/UPDATE/DELETE, requires `session_user = data_plane_builder` plus an active build tuple). Code that deletes: `ga_vargas_writer.py:2896` (INVARIANT sentinel rows only), `_idempotency.py:106`, cockpit Clear (`DELETE ... WHERE chart_id`, none recorded: 0 `dormant` audit transitions for ga_vargas). No migration or script contains DELETE/TRUNCATE on it. No asset build has run since 09-18 (the single failed 10-01 run started no asset). Not excluded from the reader: a delete between 09-07 and the 09-10 stats reset.

## B. Option P (policies): the other fix, with its gate amendment

**Statements** (owner path, same executor, `SET LOCAL ROLE data_plane_l1_owner`, `SET LOCAL lock_timeout = '5s'`; the roles are exactly the runtime logins, since no writer uses `SET ROLE`: L1 and L2 writers connect as `data_plane_builder`, serving as `amjis_app`, verification as `data_plane_verifier`; no code path UPDATEs `chart_divisionals`):
```sql
CREATE POLICY chart_divisionals_select ON public.chart_divisionals AS PERMISSIVE FOR SELECT
  TO amjis_app, data_plane_builder, data_plane_verifier USING (true);
CREATE POLICY chart_divisionals_builder_insert ON public.chart_divisionals AS PERMISSIVE FOR INSERT
  TO data_plane_builder WITH CHECK (true);
CREATE POLICY chart_divisionals_builder_delete ON public.chart_divisionals AS PERMISSIVE FOR DELETE
  TO data_plane_builder USING (true);
```
**Gate amendment (required, or the next `data-plane-ownership-status` run throws at `:417`).** No script diff: the gate is data-driven. It needs three rows in `public.l1_data_plane_policy_attestations` (owner `data_plane_l1_owner`; the table's UPDATE/DELETE trigger does not block INSERT), inserted in the SAME owner-path transaction so no committed state has a policy without an attestation:
```sql
INSERT INTO public.l1_data_plane_policy_attestations
SELECT c.relname, p.polname, p.polcmd, p.polpermissive, p.polroles,
       pg_get_expr(p.polqual, p.polrelid), pg_get_expr(p.polwithcheck, p.polrelid)
FROM pg_policy p JOIN pg_class c ON c.oid = p.polrelid
WHERE c.relname = 'chart_divisionals' AND p.polname IN
  ('chart_divisionals_select','chart_divisionals_builder_insert','chart_divisionals_builder_delete');
```
(the same shape as `1035:1982-1992`). A mistake here is permanent without `ALTER TABLE ... DISABLE TRIGGER USER` on the attestation (the existing test does exactly that at `data_plane_protected_roles.db.test.ts:469-471`). Test change: in `platform/tests/integration/data_plane_protected_roles.db.test.ts` (new case after `:343`, where the view-drift case already asserts `/policies, views, or default privileges drift/`): (1) create an unattested policy on `chart_divisionals` as the owner and expect `readDataPlaneOwnershipStatus` to reject with that message; (2) create it plus the three attestation rows and expect `marked`; (3) `DISABLE ROW LEVEL SECURITY` and expect `marked` (this one case is the only test Option D would add, and is optional).

**Blast radius, both options.**
| | Option D (RLS off) | Option P (3 policies) |
|---|---|---|
| gains visibility | all six roles that already hold SELECT: `amjis_app`, `data_plane_builder`, `data_plane_verifier`, `data_plane_migrator`, `data_plane_l2_owner`, `suvarna_reader` | only `amjis_app`, `data_plane_builder`, `data_plane_verifier` (migrator, L2 owner, reader stay blind) |
| loses | nothing (nobody can read it today) | nothing |
| roles with no privilege today (`nirmana_evidence_ingress_writer`, `retrieval_census_ro`) | still none (the table's relacl grants them nothing; migration 885's grant was superseded by 1035's ACL) | still none |
| gate | no change | attestation rows + test |
| future role added with SELECT | sees data | blind again until its own policy (the same incident class) |
| tenancy | none lost (below) | `USING (true)` gives no tenant isolation either |
| rollback | `ENABLE ROW LEVEL SECURITY` (restores the blind state) | `DROP POLICY` x3 plus attestation cleanup (needs the trigger disabled: harder) |

**Why RLS was on (read from `platform/migrations/002_ganita_divisionals.sql:61-85`).** Comment: "Row-level security placeholder (inherit from charts table policy)", then a single policy `"service role full access" ... TO service_role USING (true) WITH CHECK (true)`, "chart_id scoping done in application". It was a Supabase-era placeholder, not a finished multi-tenant model: the only per-principal RLS is on `charts` (`migrations/_archive/083_charts_rls.sql`, `app.principal_id` GUC) and the later g1c/B002 role design (migration 576, `g1c_arm_rls.sql`) which does not cover this table (its own test records `chart_facts` and `chart_dashas` as RLS-false; I did not find `chart_divisionals` in that spec). `service_role` does not exist on this instance and the live table has no policy; HOW and WHEN the policy disappeared is unknown (no `DROP POLICY` for this table in the migration tree; probably the role's removal). L2 owner: unchanged (it holds SELECT, no runtime path logs in as it). Verifier: gains the read it was granted. Web app (`amjis_app`): regains the read it had until 09-18.

**Recommendation: Option D.** (1) smallest gate change: none; P adds immutable, oid-pinned attestation rows; (2) covers every existing SELECT grantee without enumerating roles, including the read-only campaign login; (3) restores symmetry with the other L1 tables (no RLS) and loses no real isolation (the only policy ever written was role-based with `USING (true)`); (4) one statement, one lock, instant to reverse; (5) P leaves the same latent blindness for any later grantee. The cost to name: a fresh database built from 002 would re-enable RLS (parity migration, Part III).

---

# PART III. FOLLOW-UPS (not part of the incident fix)

## F1. Non-vacuity conjunct in the `ga_vargas` integrity check

Live registry text (`asset_registry.integrity_check_sql`, migrations 883/884 chain; read just now): four conjuncts (a) sign vs sign_number, (b) vargottama flag re-derived, (c) canonical-chart-scoped D1 sign vs `chart_facts` (migration 884), (d) identity-range NOT NULL guard, all `NOT EXISTS`, none with a presence requirement. The runner executes it with NO parameters (`pipeline/orchestrator/asset_runner.py:933-955`, `_probe_asset` runs `cur.execute(integrity_sql)`), as the builder's connection. Under RLS blindness the builder reads 0 rows, every `NOT EXISTS` is true, and the check passes on an empty table (`CLAUDE.md §N.8` defect class). Worse, the writer's per-row fallback (`ga_vargas_writer.py:2762-2776`) swallows a per-row insert error (it only logs) and returns `written` = rows that did land: a rebuild under blindness would likely end `lit` with 0 rows written and a green check. (Inferred from code, not exercised.)

Proposed: an asset_registry-only migration (SS pre-approved precedent: I-8, `1215_suvarna_i8_ka_avadhi_integrity_check_chart_scope.sql`, PR #2827 pattern: `SET LOCAL lock_timeout = '5s'`, `DO $pre$` count check, `UPDATE asset_registry SET integrity_check_sql = $ck$ ...full current text + one conjunct... $ck$`, `DO $post$` that asserts the new text took via `position(...)`), conjunct (e):
```sql
  -- (e) non-vacuity (migration NNNN): the canonical chart must actually HOLD varga rows. Without this, a table the
  -- builder cannot see (RLS without a policy) or an emptied table passes every NOT EXISTS above.
  AND (SELECT count(*) FROM chart_divisionals
        WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
          AND ayanamsha_id = 'lahiri_chitrapaksha' AND varga = 'D1'
          AND fact_category = 'varga_position' AND fact_key = 'sign'
          AND graha = ANY (ARRAY['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'])) = 9
```
Two cautions: the `= 9` is my reading of the writer (unique key gives one `varga_position/sign` row per graha) and must be measured on the live table through the owner path BEFORE adoption (fall back to `>= 1` as in 1215's conjunct (f)); the hard-coded canonical literal repeats the disclosed 882/884/902/1019/1022/1215 tradeoff (non-canonical builds are not measured). The freeze-time `integrity_verified` detector (`src/lib/nirmana-elevation/definitions.ts`) runs this SQL standalone, so it also stops certifying an empty table. Tests, as 1215 had: a text/shape test and a DB-backed behaviour test (empty table -> false, populated -> true), opt-in and guarded as in `test_migration_1215_ka_avadhi_integrity_behaviour_db.py`. The writer-side counterpart (fail the run when rows are produced but 0 land) is a separate writer change, not proposed here.

## F2. RLS-without-policy check in the gate

Why: this incident is a table with RLS on, no policy and a non-bypass owner; nothing detects it. Catalog check (read-only; I ran the equivalent as the reader):
```sql
SELECT c.relname, pg_get_userbyid(c.relowner) AS owner_name, COALESCE(g.rolname,'PUBLIC') AS blind_grantee
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
CROSS JOIN LATERAL aclexplode(COALESCE(c.relacl, acldefault('r', c.relowner))) a
LEFT JOIN pg_roles g ON g.oid = a.grantee
WHERE n.nspname = 'public' AND c.relkind IN ('r','p') AND c.relrowsecurity
  AND NOT EXISTS (SELECT 1 FROM pg_policy p WHERE p.polrelid = c.oid)
  AND a.grantee <> c.relowner AND a.privilege_type IN ('SELECT','INSERT','UPDATE','DELETE')
  AND NOT COALESCE(g.rolbypassrls OR g.rolsuper, false)
  AND NOT (c.relname = ANY ($1::text[]))      -- allowlist
```
Live result: 22 RLS-on `public` tables, 13 with zero policies: 12 `ai_*` tables owned by `amjis_app` plus `chart_divisionals`. The blind-grantee rows are `chart_divisionals` x 6 roles and the ai_* tables x `retrieval_census_ro` / `suvarna_reader` (the owner `amjis_app` itself bypasses). The 12 `ai_*` names are the allowlist (they are deny-all-to-others by design as far as I can tell; the grants to `retrieval_census_ro`/`suvarna_reader` on them are blind, intent UNKNOWN, worth a look: the same pattern).
Wiring: (1) in `platform/scripts/data-plane-ownership-status.ts`, a new query right after the `catalogSurface` block (`:417`) restricted to `[...L1_ACTIVE_TABLES, ...L2_ACTIVE_TABLES]` (no allowlist needed there; protected tables should never be blind) that throws `Protected table has row-level security enabled with no policy for its granted roles (default-deny blindness).`; (2) a repo-wide governance check next to `platform/scripts/governance/check_fact_category_pinning.py` (the §N.7 precedent) running the query above with the ai_* allowlist, wired into the CI governance suite.
Unit-test design: DB-backed cases in `data_plane_protected_roles.db.test.ts`: (a) as the owner `ALTER TABLE public.chart_facts ENABLE ROW LEVEL SECURITY` with no policy -> `readDataPlaneOwnershipStatus` rejects; `DISABLE` -> `marked` (restore in `finally`, as the other cases do); (b) enabled + an attested policy -> `marked` (proves the check keys on policy count, not on RLS itself); (c) a scratch table owned by a scratch role with RLS on, no policy, one grantee -> the governance query returns exactly that pair; with the table name allowlisted -> returns nothing; with a `BYPASSRLS` grantee -> returns nothing. Also assert the live allowlist equals the 12 `ai_*` names so a new RLS-no-policy table has to be consciously added. Note: tests that count RLS tables (`roles_rls.db.test.ts:259` expects 0, `:389` expects 21, on a scratch database) were not checked for whether `chart_divisionals` is in that count; check before an Option D parity migration lands.

## F3. Ripple list

**Assets that read `chart_divisionals`** (grep of writers; the six readers named in CF-16 plus the undeclared one): `ga_condition` (`ga_condition_writer.py`), `ga_sade_sati`, `ga_strength`, `ga_structural`, `ga_yoga` (D9 detectors), `ga_dashas` (reads it WITHOUT declaring `depends_on`; `lord_natal_dignity_d1`; registry edge item), and downstream `bo_laksana`, `bo_pratijna` (+ `bo_pratijna_v4_engine.py`, `brahmagyan/chart_reader_v4.py`), `bo_vargottama_dhana` (per I-11), `mi_kula` (records `{"source": "chart_divisionals"}`). Registry closure of `ga_vargas` = 61 active assets (I-11 section 6) plus `ga_dashas` and its dependents. No asset build has run since 09-18, so no derived table was computed from a blind read; the derived tables stand as built (stale-correct, not corrupted). The next build of any of them while the table is blind WOULD compute from nothing.
**Capabilities and tools that read it** (platform/src/lib/retrieval/registry, grep): `get_chart_snapshot.ts:177` (tool `chart_snapshot`; observed blank), `get_divisionals.ts:90,128`, `get_argala.ts:169`, `register_d9_judgment.ts` (`judgment_query` D9/varga terms), `register_d7_channel.ts:1075,1335` (the `divisional_facts` section and per-varga sign/house), `address_resolver.ts:401,567` ("Atmakaraka in D9" style addresses), `source_query_availability.ts:1434,1959,2120,2126,2276` (availability probes: may report "not built" for a built table), `coverage_matrix.ts`, `reading_checklist.ts`, `L2_bodha/query_mechanisms.ts:230` (per-varga serving text), `platform-mcp/src/tools/registry_bridge.ts:3746` (the "show me the chart" D1 grid). **User-visible symptoms** (only the first is observed; the rest follow from the handlers and are unverified): empty D1/D9 chart grids; divisional-chart answers with no placements; `judgment_query` verdicts missing varga evidence (the verdict layer is supposed to report an honest gap via `judgment_flags`, §N.6 item 3); availability probes reading the table as empty. Materialized views `mv_chart_vargas_summary` (reltuples -1, relpages 0 as read now) and `mv_chart_super_vargottama_bodies` (1,550 rows, 51 pages; I-11 had the two descriptions swapped) are owned by `amjis_app`: contents unseen; do not refresh before the fix.

## F4. New cascading FK for F-3's follow-up: `chart_fact_identity -> chart_facts`

`chart_fact_identity_fact_id_fkey` references `chart_facts(fact_id) ON DELETE CASCADE`; child owned by `amjis_app` (outside the L1 protected owner; no guard on the child). Delete paths that trigger it: every `chart_facts` row delete: the delete-then-insert of the seven `chart_facts` writers (`ga_positions`, `ga_sensitive`, `ga_panchanga`, `ga_nakshatra`, `ga_sade_sati`, `ga_ayurdaya`, `ga_sensitive_degree`; `authorize_l1_chart_facts_delete` receipt required), cockpit Clear on those assets, and a `charts` delete. The child is rebuilt only by `python-sidecar/scripts/build_fact_identity_index.py` (a standalone script: DELETE this chart's rows then INSERT; not an orchestrator asset, so no build triggers it; whether anything schedules it is UNKNOWN). **Observation that may be an instance, unverified:** identity rows per chart are 125,873 (A, computed 2026-08-08), 124,390 (B, 08-08) and only **1,205 for the canonical chart** (computed 2026-09-07 03:43Z, categories graha_position, bhava_cusps, house_chalit, graha_sign_attributes, sandhi_flag), against 143,299 canonical `chart_facts` rows, and the canonical `chart_facts` writers re-ran 09-07 08:37 to 09-08 after that index run. A cascade after the re-write is consistent with this but not proven (the 1,205 may simply be what the single 09-07 run indexed). Treatment to decide with F-3 (the MSR FK drop set): the same two options (drop the FK and delete children explicitly in the owning writers, or keep it and add a delete guard); readers of the index: `bo_pratijna.py`, `chart_reader_v4.py`, `consent/scope.ts`.

## F5. Ordering against the consolidated grant plan, and the contingency

Independent and first. This is a product-visible outage with a one-statement fix; the grant plan (L2 FK drops, mimamsa guard, builder grants; one 19+ statement plan, its own hash and diffs) is a separate transaction and must not be bundled. Both use the same executor (the holder of `cloudsql-postgres-admin-password`), the same D6 pattern and the same gate. Run the incident fix first, verify V1-V6 and the gate prints `marked`, then take the grant plan's own gate baseline and run it under its own approval. Neither plan's snapshot diffs include `relrowsecurity`, and Option D changes no ACL, membership, constraint, trigger or function, so neither can invalidate the other's "diff is exactly the plan" check. If the rows are intact: the rebuild plan's "ga_vargas first" item (I-11) is dropped; nothing is restored; the 61-asset closure is NOT rebuilt for this reason. If the rows are deleted or partial: Part I still goes first (a `ga_vargas` rebuild under RLS would drop 0 rows, insert 0 rows and look green, see F1), then a rebuild of `ga_vargas` for the affected charts and the dependent closure, which is a production build and SS REVIEW.

## F6. Other observations

- I-11's section 1 says RLS was enabled in 002 with "plus a policy ... TO service_role" and also that the table has been "deny-all for every non-owner since creation". The first is right; the second is not established: a policy for a role that existed in the Supabase era may have kept the table usable by that role until the role went away. When the policy was lost is unknown.
- I-11's reading of the sweep ("`nirmana_evidence_ingress_writer` ... SELECT granted by 885 ... non-owner too") is outdated: the live relacl gives it no privilege on this table (1035 reset the ACL).
- The registry `integrity_check_sql` and `count_sql` for `ga_vargas` both ran as ordinary reads; `count_sql` (`SELECT count(*) FROM chart_divisionals WHERE chart_id = $1`) returned 0 for `ga_vargas` under the reader, exactly the stat route's "cockpit truth" path: the cockpit probably shows 0 for this asset to every role now.
- A fresh-DB parity migration for Option D (idempotent, guarded with a `DO` block so it no-ops when the caller is not the owner, never editing 002 or 1035) is a decision for SS, not needed for the incident.

---

# PART IV. UNKNOWNS AND WHAT THE READER COULD NOT SEE

- The actual row counts (RLS; the owner-path count in Part II.A is the one thing that settles intact vs deleted). `reltuples` 71,476 is an estimate of unknown date.
- Whether any pre-09-10 delete occurred (stats reset 2026-09-10 15:46Z; no WAL, backup or log access).
- When and how the 002 policy disappeared; whether any role ever hit the RLS wall in a log (no error-log access); whether the cockpit and any scheduled job (`REFRESH MATERIALIZED VIEW`, `build_runner.py` legacy refresh at `:52-84`) touched the table after 09-18.
- Which role the freeze-time `integrity_verified` evidence ran as; `ga_condition_composite.varga_dignity_composite` is non-null on the canonical chart (45/45) but 0/45 on the other two charts (predates the writer change, or computed from a blind/empty source: not determined).
- Contents of the two materialized views; `charts` (permission denied for the reader); `pg_stats` of the table; other sessions.
- Not run by this lane: any query as `amjis_app`, builder, verifier or owner; any DDL; any EXPLAIN ANALYZE; any build. The in-transaction runtime-role probe, the owner-path count and V4-V6 are all part of the executor's job, not mine.
- Unverified code-reading inferences, flagged in place: the writer's per-row fallback behavior under RLS (F1), the `= 9` conjunct (F1), the symptom list beyond `chart_snapshot` (F3), the chart_fact_identity cascade (F4).

---

# APPENDIX. Draft plan texts and hashes (sha256 of the text plus a newline plus the JSON expected diff, the formula of `reader_grants.py plan_hash`; the executor's dry run prints the real hash)

Files (not in the repo): `/Users/Dev/suvarna-evidence/TrackI/i11_plans/count_ro.txt`, `apply_D.txt`, `rollback_D.txt`.
- count (read-only) `6d9745dd8005fa2a1845aa2326c101472f3d3db12794478db9f08e6ddf02953f`, expected diff `[]`.
- apply D `531c0940ae6eb654972e3401fd317f95cf2051cca10ae7249ff44e420a741aad`, expected diff `["chart_divisionals|relrowsecurity|true->false"]`.
- rollback D `0743026095a85e9a43135c3b72375f2cf7f4d7e91e398e5f05e26dab1f6853d5`, expected diff `["chart_divisionals|relrowsecurity|false->true"]`.
The apply and rollback texts are the Part I steps 1, 2, 4 and the commit conditions of step 6 in one-line form; the in-transaction runtime-role probes of steps 3 and 5 are checks, not plan statements, and are not hashed. If SS wants them hashed, the executor script must be drafted first (not done: this lane produces the review only).

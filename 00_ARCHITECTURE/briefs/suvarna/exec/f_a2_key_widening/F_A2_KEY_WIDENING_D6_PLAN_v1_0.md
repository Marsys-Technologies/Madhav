---
artifact: F_A2_KEY_WIDENING_D6_PLAN
version: "1.1"
status: DRAFT_FOR_REVIEW
date: 2026-10-02
lane: suvarna/land/TI-l1-fa2-key-001
base_commit: origin/main bf6fe712b
produced_by: exec-suvarna (S-L1 mandatory item Q01 writer lane)
decision: L1 decision sheet Q-L1-01 (SS-ruled N-62, accepted as recommended)
execution: NONE against any real system. DB access was SELECT and catalog reads as `suvarna_reader`; the executor script and migration 1222 were exercised only against disposable local PostgreSQL 15 databases built for this lane. Nothing was applied.
approval_needed: SS `APPROVED <plan hash>` for the hash `d6_f_a2_key_widening_DRAFT.py --dry-run` prints (the FROZEN hash is recorded in the hand-off, section 11), plus the owner's standing authorization in the executing session. Migration 1222 is allocated by SS and rides the normal pipeline.
changelog:
  - "1.1 (2026-10-02): SS direction on #2858. (1) approach accepted. (2) integrity: conjunct (e) kept, (f) dropped from integrity_check_sql and turned into S-L1 ACCEPTANCE CRITERIA (section 8) with a read-only check script. (3) the registry migration is now platform/migrations/1222_nirmana_l1_ga_vargas_integrity_nonvacuity.sql (routine, guarded, not applied). (4) the executor gains a readable catalog-diff dry run, an identity probe, owner-role reads (the administrator holds no table privilege), an ANY-chart build guard, a builder-session guard, a pgcrypto precondition and window timestamps; the plan hash now binds the executor's own source. (5) sequencing: the WRITER deploys FIRST (section 6)."
  - "1.0 (2026-10-02): first draft."
---

# F-A2: widen the `chart_divisionals` natural key to include `fact_subject`

## 1. Verdict in four lines

1. The ruled change (widen `chart_divisionals_unique_idx` and both `ON CONFLICT` targets to `fact_subject`) is correct and is implemented in the writer on this branch.
2. It is **not** a one-migration change. The index, the L1 capture trigger and one hunk of the L1 capture function are all owned by `data_plane_l1_owner` and are attested; widening the index alone makes every later `ga_vargas` partition abort at completion (section 4). That is why the database half is a **D6 owner-path plan** (`d6_f_a2_key_widening_DRAFT.py`), not an `amjis_app` migration.
3. The row gain is **~14,200 rows per chart, not +250**: the sheet's "D30 60 to 10" is one of four collapsed families (section 3).
4. Only the integrity clause is a plain registry migration (`platform/migrations/1222_nirmana_l1_ga_vargas_integrity_nonvacuity.sql`, `asset_registry` is `amjis_app`-owned, conjunct (e) only). The key-grain numbers are S-L1 acceptance criteria, not an integrity check (section 8).

## 2. The key: old vs new

| | columns |
|---|---|
| live index and writer target, before | `(chart_id, graha, ayanamsha_id, varga, fact_category, fact_key)` NULLS NOT DISTINCT |
| after | `(chart_id, graha, ayanamsha_id, varga, fact_category, fact_key, fact_subject)` NULLS NOT DISTINCT |

`fact_subject` is the writer's own per-row discriminator and is never NULL in any row the writer builds (checked on all 38,665 rows of an offline 5-ayanamsha build). It is the right column, not a wider net: with it, an offline build of 25 different births (1940-2015, six continents) produced **0** key collisions on every one.

## 3. What the old key silently dropped (and what comes back)

Method: the shipping row builders and the shipping `build_ga_vargas` were run offline against an in-memory model of the unique index and `ON CONFLICT DO NOTHING` (no database), with the real `bg_shashtiamsha_deities` table (60 rows, read as `suvarna_reader`) seeded. **The model reproduces live exactly:** on the old key it lands 4,878 rows per ayanamsha for the canonical chart and matches the live per-category counts of `lahiri_chitrapaksha` category by category (e.g. `varga_ashtakavarga` 240, `varga_house_lord` 210, `varga_d30_lord_per_amsa` 10, `varga_position` 1,800, `varga_deity_attribution` 135). It also reproduces the F-4 investigation's 7,724 attempted rows per ayanamsha (38,620 over five). This agrees with `INVESTIGATION_L1_F4_F8_v1_0.md` (branch `suvarna/land/TI-l1-f4-f8-001`, `682ce1623`).

| fact_category | built / ayanamsha | stored before | stored after | collapse mechanism |
|---|---|---|---|---|
| `varga_ashtakavarga` | 2,880 (96 per varga x 30) | 240 | 2,880 | 12 sign rows per (graha, varga) share `fact_key='bindus'`; only `S1` survived |
| `varga_house_lord` | 360 (12 per varga x 30) | 210 | 360 | graha is the key and `lord` the fact_key: a lord of two houses kept one |
| `varga_d30_lord_per_amsa` | 60 | 10 | 60 | six odd and six even signs share five lord/degree keys each |
| `scope_cap` (INVARIANT) | 6 per call | 2 | 6 | the five floored bodies share one key |

### Expected row counts (for verification after the S-L1 `ga_vargas` rebuild)

| scope | before (live, 2026-10-02) | after | gain |
|---|---|---|---|
| per ayanamsha, excluding INVARIANT | 4,878 (canonical) | **7,718** | +2,840 |
| `varga_ashtakavarga`, per chart | 1,200 | **14,400** | **+13,200** |
| `varga_house_lord`, per chart | 1,050 | **1,800** | **+750** |
| `varga_d30_lord_per_amsa`, per chart | 50 | **300** (60 per ayanamsha) | **+250** |
| `scope_cap` / INVARIANT, per chart | 2 | **6** | **+4** (the 20 in the F-4 investigation are attempted-and-dropped across five per-ayanamsha calls; the sentinels are deleted and re-inserted per call, so the net on the stored table is +4) |
| **`chart_divisionals` rows, chart 482012f1 (canonical)** | **24,392** | **38,596** = 5 x 7,718 + 6 | **+14,204** |
| chart 1c826d5a and chart cb73cd3d | 23,542 each | **38,596** each, after a rebuild with the current writer | +15,054 (the extra 850 are the D30 main-loop rows the F-A3 fix already restores) |

`38,596 = 5 x (7,724 attempted - 6 sentinels) + 6`. The count is structural (houses, signs, D30 regions), independent of birth data (25 charts: 7,724 attempted, 7,724 landed, 0 collided each). One caveat: the model uses the live deity table, so `varga_deity_attribution` (135 per ayanamsha) follows `bg_shashtiamsha_deities` and would move with it. Also `krishnamurti` / `surya_siddhanta_classical` on charts 1c826d5a and cb73cd3d currently hold Lahiri-identical positions (pre-#1053); the rebuild changes their values, not their counts.

Verification after the run (read-only, by chart and ayanamsha): `count(*)` per chart = 38,596; `GROUP BY ayanamsha_id` = 7,718 x 5 + INVARIANT 6; `GROUP BY fact_category` for the four families above; `SELECT count(*) - count(DISTINCT (chart_id, graha, ayanamsha_id, varga, fact_category, fact_key, fact_subject))` = 0; and the new integrity clause returns true.

## 4. Why the index alone is not enough (read from migration 1035 and the live catalog)

- `chart_divisionals` carries `l1_data_plane_capture`, an AFTER INSERT trigger on `l1_data_plane_capture_row('chart_id','graha','ayanamsha_id','varga','fact_category','fact_key')`. The function builds each row's `row_identity` from exactly those arguments (1035 lines ~900-960).
- `complete_l1_data_plane_partition` compares the writer's reported `rows_inserted` with `count(DISTINCT (source_table, row_identity))` over the partition's snapshots and raises `L1 partition % reported % rows but protected capture contains %` on a mismatch (1035 ~1365-1385). `rows_inserted` is the writer's `total_rows_written` (`data_plane_runtime.py`).
- With the index widened and the trigger not, a rebuilt ayanamsha lands ~7.7k rows but only ~4.9k distinct identities; every partition aborts. So the trigger's key arguments must widen in the same transaction.
- The same function contains one hunk that spells the six-column key to build `source_row_identities` for the `ga_condition_composite` dependency graph (1035 ~1005-1025; read from the LIVE function: exactly one occurrence). Without the new element those provenance references stop matching any captured row.
- Both objects are attested: `l1_data_plane_trigger_attestations.definition_digest` = sha256(`pg_get_triggerdef`) and `l1_data_plane_function_attestations.definition_digest` = sha256(`pg_get_functiondef`), compared by `data-plane-ownership-status.ts` (it throws "Protected trigger inventory or definition drift detected" / "Protected function definition digest drift detected"). I checked on the live database that today both digests equal the live objects. Both attestation tables are append-only by trigger and owned by `data_plane_l1_owner`.

## 5. Objects and owners (catalog, `suvarna_reader`, 2026-10-02)

| object | owner | path |
|---|---|---|
| `chart_divisionals`, `chart_divisionals_unique_idx`, its capture trigger | `data_plane_l1_owner` | owner path (D6) |
| `l1_data_plane_capture_row()` (SECURITY DEFINER), both attestation tables | `data_plane_l1_owner` | owner path (D6) |
| `asset_registry` | `amjis_app` | ordinary migration |
| `mv_chart_vargas_summary`, `mv_chart_super_vargottama_bodies` | `amjis_app` | no change: they read only `varga_position / varga_dignity / varga_vargottama_flag / varga_deity_attribution / varga_super_vargottama_flag`, none of the collapsed families |

`data_plane_migrator` is a member of `data_plane_l1_owner` (read live). The executor follows the I-11 / `reader_grants.py` pattern: transient `GRANT data_plane_l1_owner TO <admin>`, `SET LOCAL ROLE`, revoke, commit only if the diff equals the plan.

## 6. The D6 plan (`d6_f_a2_key_widening_DRAFT.py`)

One transaction, `lock_timeout 5s`, `statement_timeout 120s`, `search_path = pg_catalog, pg_temp` (`public.digest` is schema-qualified).

Preconditions (abort and ROLLBACK otherwise; reads only, the plan never writes a run):
- no `build_runs` row in `planned` / `running` / `paused` **on ANY chart**: the query has no chart filter (`FROM public.build_runs WHERE state IN ('planned','running','paused')`), and `build_runs.state` is CHECK-constrained to exactly `planned, running, paused, completed, stopped, failed` (read live), so those three are every non-terminal state. If another workstream's run appears in the gap, the plan prints that run's chart and state, stops, and does not touch it;
- no `l1_data_plane_generations` row in `building`; no `data_plane_builder` session active or idle-in-transaction (a hidden state, if the administrator lacks `pg_read_all_stats`, is printed as a warning and `build_runs` is then the only guard);
- the live index, trigger and function have exactly the pre-state this plan was written against;
- `public.digest(text,text)` resolves (the extension's schema is printed). **Production, read as `suvarna_reader` 2026-10-02: extension `pgcrypto` is in schema `public`; `digest(bytea,text)` and `digest(text,text)` are in `public`.** The executor calls `public.digest` (schema-qualified) because it runs under `SET LOCAL search_path = pg_catalog, pg_temp`, where an unqualified `digest()` would fail. The live capture function calls `digest(` unqualified but carries its own `SET search_path = 'pg_catalog', 'public', 'pg_temp'` (read from `pg_get_functiondef`), which `CREATE OR REPLACE` from the live definition preserves, so it resolves in `public` too. The status gate's own query (`data-plane-ownership-status.ts`) is unqualified under the default path, which also includes `public`.

Role handling: the administrator holds no table privilege (I-11 incident review), so every table read and the whole plan run as `SET LOCAL ROLE data_plane_l1_owner` (owner of the table, index, function and both attestation tables), and the `build_runs` read as `amjis_app` (its owner). Both are transient `GRANT <role> TO CURRENT_USER`; the role-membership snapshot is taken before any grant and must equal the one after the revoke.

Statements, as `data_plane_l1_owner`:

1. `CREATE UNIQUE INDEX chart_divisionals_unique_idx_f_a2 ON public.chart_divisionals (<7 cols>) NULLS NOT DISTINCT; DROP INDEX public.chart_divisionals_unique_idx; ALTER INDEX ... RENAME TO chart_divisionals_unique_idx;` (the name is kept: the writer's preflight and every document read it. A superset of a unique key is trivially satisfiable on existing data.)
2. `DROP TRIGGER l1_data_plane_capture ON public.chart_divisionals; CREATE TRIGGER l1_data_plane_capture AFTER INSERT OR UPDATE ... EXECUTE FUNCTION public.l1_data_plane_capture_row(<7 args>);`
3. `CREATE OR REPLACE FUNCTION` from the function's own live `pg_get_functiondef`, with exactly one hunk replaced (asserted to occur once): `'fact_key=' || cd.fact_key` gains `, 'fact_subject=' || COALESCE(cd.fact_subject,'<null>')` and the `ORDER BY` gains `cd.fact_subject`. Owner, SECURITY DEFINER, `proconfig` and ACL are preserved by `CREATE OR REPLACE` (and checked).
4. Re-attest the two rows: `ALTER TABLE ... DISABLE TRIGGER <append-only>`, `UPDATE` the one `definition_digest` from the live object (expected row count 1 each), `ENABLE TRIGGER`, for both attestation tables.

`--dry-run` applies everything above in one transaction, prints the exact catalog diff in readable form, and ROLLS BACK; it prints the same plan hash and UTC start/end timestamps. The diff has one block per category (index definition, trigger definition, trigger attestation row, function md5/owner/secdef/config/ACL, function attestation row), each headed `exactly N removed / M added (ONE ENTRY CHANGES | UNEXPECTED)`, then a unified diff of `pg_get_functiondef` (the hunk: `'fact_key=' || cd.fact_key` becomes `..., 'fact_subject=' || COALESCE(cd.fact_subject, '<null>')` and the `ORDER BY` gains `cd.fact_subject`), then `IDENTICAL` lines for ACL, membership, RLS, policy and per-chart row data. The attestation UPDATEs execute `public.digest(...)` inside the dry run, so digest resolution is exercised, not assumed.

**The identity probe (what the dry run fires, and what it cannot).** After the swap the dry run INSERTs 84 fixture rows (60 D30 lords, 12 house lords, 12 ashtakavarga bindus: the writer's own shapes) into a session-local copy of the table (`CREATE TEMP TABLE ... (LIKE chart_divisionals)`, unique index built from the LIVE index's columns, `ON CONFLICT` on those columns), then computes the capture identity exactly the way `l1_data_plane_capture_row` builds `v_identity` (the LIVE trigger's own arguments, `col=value` joined with `|`, NULL as `<null>`) and the completion arithmetic: stored rows must equal `count(DISTINCT identity)`. Expected and shown: 84 landed, 84 distinct identities under the widened trigger arguments, **18** under the legacy six (the abort the plan prevents). **What it does not fire:** the capture function itself and `complete_l1_data_plane_partition`. The first statement of the live capture function is `IF session_user <> 'data_plane_builder' THEN RAISE EXCEPTION 'L1 governed capture requires direct data_plane_builder authentication'`; `session_user` cannot be changed by an administrator that is not a superuser (`SET SESSION AUTHORIZATION` needs superuser), and the function further requires an admitted generation (`open_l1_data_plane_generation`, a running `build_runs` row and a `building` `build_run_assets` row, none of which a rollback-only dry run may create without touching run state). So the real capture path can only fire in a builder session, i.e. in the S-L1 run itself; the dry run proves the identity expression and the count equality the completion check depends on, plus the digest path and the diff, not the trigger's full execution.

Commit only if ALL hold: exactly one index, one trigger, one trigger-attestation, one function and one function-attestation entry changed across a before/after snapshot of every public index, trigger, `l1_/l2_data_plane_*` function and both attestation tables; ACL, membership, RLS, policy and per-chart row-data (count + md5 of ids) snapshots are identical; the new index is `indisunique`, `indisvalid`, `indnullsnotdistinct` on the 7 columns in order; both append-only triggers are `enabled` again; the two attestation rows equal the live digests under the gate's own join; the identity probe equality above holds; the transient role grants are revoked and membership equals the pre-state; `--expect-plan` equals the plan hash. Then V1 (after commit, outside the transaction): `data-plane-ownership-status.ts` reports `marked`.

Rollback: before the S-L1 rebuild, the reverse statements restore the old state (the six-column index is trivially satisfiable on the pre-rebuild rows). **After a rebuild that lands the widened rows the six-column index cannot be rebuilt** (the new rows collide on it); a rollback then means deleting the recovered rows first. State this in the approval.

Exercised locally (never against production): the executor's `run()` against a disposable PostgreSQL 15 holding a model of the objects built from the **live** function text (the model's function has the same md5 as production, `1e079261...`, so the printed hunk is the production hunk), run as a NON-superuser administrator with `CREATEROLE` and no table privilege, as production's. Results: `--count` read-only; `--dry-run` printed the diff and probe and rolled back with the state unchanged; an active build on a DIFFERENT chart refused the apply and was not touched; `--apply` committed with all conditions holding and left the index 7-column, the trigger 7-argument, the function hunk present, both append-only triggers enabled and still enforcing, and the administrator no longer a member of the owner role; a second apply was refused by the preconditions. (This run found and fixed a real defect: the first version read owner-only tables as the administrator.) What this does not prove: Cloud SQL's real grants, or the real attestation tables' extra columns/constraints.

### Order and gap (SS direction 2026-10-02): the WRITER deploys first

Together, immediately before S-L1: migration 1219 + this D6 plan + the writer deploy. Order:

1. **Writer deploy FIRST.** The new writer fails closed on a missing seven-column index (`assert_unique_key_grain`, before any DELETE), so deploying it against the six-column index is safe: any `ga_vargas` build simply refuses with a message naming the cause. Nothing is written.
2. **Then the D6 plan** (`--apply --expect-plan <frozen hash>`).
3. Migration 1222 (e) is independent of the index and may apply earlier in the normal pipeline (it is TRUE on production today).
4. S-L1 `ga_vargas` rebuild (one rebuild carries F-A1, F-A2, F-A3 for the charts).

The gap: between the index swap and the writer deploy any `ga_vargas` build fails either way (old writer: six-column target on a seven-column index; new writer: not yet deployed). That is why the writer goes first: the only window in which a build can fail is then the plan's own seconds. The executor prints UTC start/end timestamps and the `index-swap-to-end window`; report them to SS. If another workstream's run appears at any point (planned/running/paused on ANY chart) the plan stops and does not touch it.

## 7. The writer change (this branch)

- `ON CONFLICT (chart_id, graha, ayanamsha_id, varga, fact_category, fact_key, fact_subject) DO NOTHING` in both statements; `UNIQUE_KEY_COLUMNS` is the single named definition.
- `_write_rows_batch` returns rows that LANDED (driver `rowcount`; a per-row `DO NOTHING` conflict is no longer counted) and fills a run-scoped `stats` (`attempted / landed / collided / db_skipped / failed`). `collided` is a deterministic pre-write detector: a row whose seven-column key was already emitted in this run (`find_key_collisions`), sampled and logged at WARNING.
- The per-row fallback no longer swallows rejections: any row the database rejects (not skips) raises with the first error, so a table that refuses every INSERT (RLS with no policy) cannot end `lit` with zero rows. The orchestrator runs each sub-step in a savepoint, so the raise rolls the sub-step back.
- `assert_unique_key_grain(conn)` runs once per call, before any DELETE, and fails closed.
- `build_ga_vargas` summary gains `rows_attempted / rows_landed / rows_collided / rows_db_skipped / rows_failed / collision_samples`; the orchestrator adapter reports `rows_inserted` = stored rows, `rows_skipped` = attempted minus stored, and a `notes` string naming collisions. Idempotency is unchanged: per-chart delete-then-insert, scopes cleared once per run (F-A3), INVARIANT sentinels replaced per ayanamsha and excluded from the run-collision set.
- `WriterBase` contract (CLAUDE.md N.2) is untouched: `plan_substeps` / `run_substep`, no commit, no throughput write. CLAUDE.md N.7 item 2 (total, key-pinned selections) is respected: no selection was added.

## 8. The integrity clause (migration 1222) and the S-L1 acceptance criteria (SS direction)

**Migration 1222** (`platform/migrations/1222_nirmana_l1_ga_vargas_integrity_nonvacuity.sql`; routine, guarded, `asset_registry`-only, no transaction control, **not applied**; re-check that 1222 is free at arm time: at this HEAD the only 12xx files are 1216 and 1222). The live `integrity_check_sql` (4,216 chars, md5 `255af7c5194553e19f7009c1e8774d8a`, read 2026-10-02) is byte-identical to migration 884's body; all four of its conjuncts are `NOT EXISTS`. 1222 keeps them and adds ONE conjunct, scoped to the canonical chart by literal (the disclosed 882/884/902/1019/1022/1215 tradeoff):

- **(e) non-vacuity:** for each of the five declared ayanamshas x the thirty declared vargas, fewer than nine `varga_position / sign` rows for the nine grahas makes the check false. Zero rows (an empty table, or RLS blindness) is the extreme case; too few the partial one. **Measured today** (the (e) text evaluated read-only against production as `suvarna_reader`, READ ONLY transaction, 2026-10-02): (e) is TRUE (the nine rows exist for all 150 pairs), so 1222 may apply before S-L1 and does not depend on the key widening.

SS dropped the key-grain clause (f) from the integrity check entirely (bare count pins, red by design). Tests: a static vitest (`nirmana_l1_ga_vargas_integrity_nonvacuity.test.ts`: routine/guarded/asset_registry-only; the SQL passes the REAL elevation validators `nirmanaReadOnlyDetectorSqlAcceptable` and no-bind-placeholder; (f) and `<> 12/96/60` absent) and behaviour tests on a disposable PostgreSQL (empty / one row short / a whole varga missing / other chart: false; complete data: true; data collapsed by the six-column key still passes (e), i.e. (e) alone does not pin the grain; the migration applies once and refuses a second run).

### S-L1 ACCEPTANCE CRITERIA for `ga_vargas` (checked from the run result, not by integrity_check_sql)

`s_l1_ga_vargas_acceptance_check.sql` in this folder is one read-only SELECT with no parameters, to be run as `suvarna_reader` after the S-L1 rebuild of the canonical chart. It prints one row per criterion (PASS/FAIL) and a final `ACCEPTED` row.

| | criterion (canonical chart 482012f1) | expected |
|---|---|---|
| C1 | total `chart_divisionals` rows | **38,596** |
| C2 | rows per ayanamsha (5 declared; INVARIANT excluded) | **7,718** each |
| C3 | INVARIANT `scope_cap` sentinels | **6** |
| C4 | `varga_house_lord` rows in every ayanamsha x varga (150 pairs) | **12** |
| C5 | `varga_ashtakavarga` rows in every ayanamsha x varga (150 pairs) | **96** |
| C6 | `varga_d30_lord_per_amsa` rows per ayanamsha | **60** |
| C7 | rows sharing the seven-column key | **0** |
| info | family totals | ashtakavarga 14,400 / house_lord 1,800 / d30 300 |

Run against production **now** (read-only, pre-S-L1 state) as a check that the SQL is valid on the real schema: C1 24,392 FAIL; C2 five ayanamshas at 4,878 FAIL; C3 2 FAIL; C4 and C5 150 pairs each FAIL; C6 5 FAIL; C7 0 PASS; info 1,200 / 1,050 / 50; `ACCEPTED` FAIL. Behaviour tests (disposable PostgreSQL, real writer rows): complete data PASSES every row; the six-column-collapsed data FAILS C1-C6 and passes C7; empty FAILS; one D30 row short fails C6 only (among C4-C6). C1/C2 include `varga_deity_attribution`, which follows `bg_shashtiamsha_deities` (production: 60 rows, every `deity_name` NULL, 135 rows per ayanamsha); the writer test pins 7,724 attempted / 7,718 stored using that production reference.

## 9. Track I items (docs/notes, not code; from the coordinator, 2026-10-02)

- **T-1 `ga_dashas` integrity_check_sql is hard-scoped to the canonical chart** (all four conjuncts carry the literal `482012f1-...`, migration 882) and never looks at charts 1c826d5a / cb73cd3d. Fix before S-L1b: a change that can only make PASS harder is a pre-approved class. (F-8 investigation, B.1.)
- **T-2 Lahiri-identical varga positions on charts 1c826d5a and cb73cd3d** (their `krishnamurti` and `surya_siddhanta_classical` rows equal Lahiri: pre-#1053 fallback and the F-A1 birth-instant error): goes into the S-L1b brief; the S-L1 rebuild with the current writer corrects them. (F-4 investigation, A.6.)
- **T-3** the same defect class exists wherever a unique key omits a writer-side discriminator and the INSERT is `ON CONFLICT ... DO NOTHING`: a census of delete-then-insert writers whose conflict key is narrower than their emitted grain was not run in this lane.
- **T-4** `platform/python-sidecar/brahma/l1/ganita/divisionals_writer.py` still carries a four-column `ON CONFLICT (chart_id, graha, ayanamsha_id, varga) DO UPDATE`; it is not a registered writer (nothing imports it outside its own tests) and would be refused by the live index. Left untouched.
- **T-5** `nirmana_analysis_layer_pins.py --check` reports the L1, L2 and L3 `writer_inventory_sha256` stale at origin/main already (`bf6fe712b`, before this change); this change moves the `ga_vargas` digest in `nirmana-writer-digests.json` and so the derived L1 inventory (`cfdac07e...` to `83c6bc69...`). The pin document was not regenerated here (it needs `--convergence-commit <reviewed sha>`); nine tests in `test_nirmana_analysis_layer_pins.py` fail identically on a clean origin/main in this environment (shallow ancestry / "CI must provide the protected pin baseline").

## 10. Not verified

1. The executor was never run against Cloud SQL or any production catalog; its mechanics were proved on a local model only (section 6).
2. Whether any L2/L3 reader parses `row_identity` / `grain_jsonb->natural_key` of `chart_divisionals` snapshots as a six-element key: a repo grep found no such reader (only generic `DISTINCT ON (row_identity)` uses); `l1_data_plane_row_snapshots` is not readable by `suvarna_reader`, so existing snapshot contents were not inspected.
3. Downstream consumers of the recovered families (11 sign bindus per ashtakavarga graha-varga, second house of a double lord, the other 50 D30 rows): not traced. More rows per page may change response density of `get_divisionals.ts` (about +58% rows per chart).
4. The post-rebuild counts are an offline model that matches the live pre-state exactly per category; they are not a measurement of the rebuilt table.
5. (RESOLVED 2026-10-02) `pgcrypto` is in schema `public` on production, `digest(text,text)` and `digest(bytea,text)` in `public` (read-only). The executor's `public.digest` resolves; the precondition re-checks it at run time.
6. Real behaviour of `GRANT data_plane_l1_owner` / `GRANT amjis_app` for the real administrator role (the local model uses a `CREATEROLE` non-superuser, the closest stand-in; a role unable to grant them would abort the dry run harmlessly before any statement).
7. The capture function itself and `complete_l1_data_plane_partition` are not fired by the dry run (section 6: the `session_user = data_plane_builder` check and the admitted-generation requirement). The identity probe covers the arithmetic they depend on. `l1_data_plane_row_snapshots` stays unreadable to the reader; that is acceptable only because the probe uses the live trigger arguments.
8. `pg_read_all_stats` for the administrator (decides whether a hidden builder session is visible; a warning is printed if not).

## 11. Final review package for SS (what accompanies the frozen hash)

1. **The frozen plan hash** (binds `d6_f_a2_key_widening_DRAFT.py`'s own bytes, this document and the expected diff), recorded in the hand-off with the HEAD that produced it (`python d6_f_a2_key_widening_DRAFT.py --print-hash`). Any edit to the script or this document changes it.
2. **A `--dry-run` against production under the owner's standing authorization** (run by the coordinator when SS asks): it must print the same hash, the exact diff of section 6 with `ONE ENTRY CHANGES` on all five categories, the identity probe (84 / 84 / 18), `commit conditions: ALL HOLD`, and `ROLLED BACK (dry run)`.
3. The independent review verdict.
4. The unverified items that matter for safety: section 10 items 1, 6, 7, 8.
5. The S-L1 acceptance script and 1222's static and behaviour tests (section 8).


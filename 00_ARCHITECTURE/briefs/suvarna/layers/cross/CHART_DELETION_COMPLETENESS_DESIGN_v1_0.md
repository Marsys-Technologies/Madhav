---
artifact: CHART_DELETION_COMPLETENESS_DESIGN
canonical_id: SUVARNA_CHART_DELETION_COMPLETENESS_DESIGN
version: "1.0"
status: DRAFT_FOR_REVIEW
date: 2026-10-03
produced_by: "Exec Suvarṇa (worker chart-delete-design)"
lane: suvarna/land/TI-chart-delete-design-001
decision: "SS item 'chart deletion completeness' (NOT S-L1, NOT migration 1275). N-46 reading is a WORKING ASSUMPTION, OPEN-FOR-OWNER (section 6)."
scope: "design only. Read-only catalog and count queries as suvarna_reader through the existing proxy; a disposable PostgreSQL 15 on a unix socket for fixtures (stopped by recorded PID, directory deleted). No migration written, nothing applied, no production write, no credential in this file."
evidence: "/Users/Dev/suvarna-evidence/TrackI/cdd/ (queries, outputs, fixture SQL, inventory.csv) and /Users/Dev/suvarna-evidence/TrackI/CHART_DELETE_DESIGN_REPORT.md"
changelog:
  - "1.0 (2026-10-03): first issue."
---

# Chart deletion completeness: design

Evidence tags used throughout: **[MEASURED]** read from the production catalogue or row counts as `suvarna_reader` on 2026-10-03; **[SOURCE]** derived by reading repo or function source, not executed against production; **[FIXTURE]** reproduced on a synthetic disposable PostgreSQL 15; **[ESTIMATE]** reasoned, to be re-measured. "Canonical chart" is `482012f1-710e-4a25-994a-93821f5871aa`. Counts and names only; no people-entered content was read.

## 0. Findings in one page

1. **Deleting a chart cannot succeed today: three independent blockers, plus an unsound transaction.** (Repo code on `origin/main` read against the production catalogue.)
   a. The route's first statement is `DELETE FROM messages ...`; no relation named `messages` exists in any schema, and `conversation_branches` has no `chart_id` column (it has `conversation_id`) [MEASURED + SOURCE]. The route as written ends in its own `catch` with a 500 for every chart.
   b. (Integrity hazard, not a blocker.) Its `BEGIN`/`COMMIT` run through `query()`, which is `pool.query`, so they are not guaranteed to share a connection with the statements between them. A concurrent request made a ROLLBACK leave 3 of 3 deleted rows deleted [FIXTURE, section 2.1].
   c. NO ACTION / RESTRICT keys block the final `DELETE FROM charts`: `life_events` (63 rows on the canonical chart), `event_chart_state_index` (57), `mimamsa_pool_contributions` (0), `planner_inquiry_lifecycles` (RESTRICT, 25 rows over all charts), four `ka_gochara_*` tables, plus `conversation_summaries` and `message_parts` under the conversation cascade [MEASURED].
   d. **Trigger guards refuse the cascade itself.** `chart_divisionals` (24,392 canonical rows) and `ga_prashna_judgment` already have `ON DELETE CASCADE`, but their BEFORE DELETE trigger raises unless `session_user = 'data_plane_builder'` inside an admitted build generation. A cascade run by the app role is refused [SOURCE + FIXTURE]. So even the part that "works by FK" does not work.
2. **174 live per-chart tables have no cascade path to `charts`** (confirms the 1275 report), plus 35 shadow/archive/staging copies; 235 tables carry a `chart_id` column [MEASURED]. The two data-plane owners hold 56 of the 174 (18 L1, 38 L2); 54 of the 56 also sit behind a DELETE trigger with no chart-delete allowance (only the two `*_generation_heads` tables do not). Adding foreign keys alone therefore changes nothing for them.
3. **FKs are necessary and not sufficient.** Four more classes survive a chart delete even with every FK present: text-typed `chart_id` (12 tables), second-hop keys (`prashna_charts.question_text` and `ga_prashna_lagna` hang off a prashna id space, not `charts.id`), soft-keyed conversation/query content with no FK (`llm_usage_events` prompt/response text, `query_trace_steps`, `tool_execution_log`, `audit_log` and others), and global fits that embed per-chart statistics (`gochara_v3_calibration.per_chart_hit_rates`).
4. **The target is one mechanism**: `DELETE FROM charts WHERE id = $1` inside one real transaction on one dedicated connection, with an `ON DELETE CASCADE` path from every per-chart table, a database-resident registry whose exemptions need a reason, a catalog-driven completeness detector (proved on a fixture, including a mutation), a guard-allowance function reused by every guard, and a post-delete residual count inside the same transaction that rolls everything back if it is not zero (section 5).
5. **Size forces a job, not a request.** The canonical chart has about 11.2 million rows in live per-chart tables, 8.57 million of them in `kala_field` alone [MEASURED]. The pool sets `statement_timeout = 25 s` (`platform/src/lib/db/client.ts`). A 3-million-row, 3-index synthetic cascade took 8 to 14 s warm on a local SSD [FIXTURE]; the production figure must be re-measured on a production-sized mirror before the route's timeout is chosen (section 5.6).
6. **Three decisions above engineering** are open: people-entered data (section 6, OPEN-FOR-OWNER), whether append-only safety and sealed-publication records survive subject deletion (section 7), and whether the "irreplaceable" `kala_gochara_windows_archive_20260805` v1 archive yields to a person's deletion.
7. **Sequence**: app-side route repair and report-only detector first (no data-plane touch), then the ruled chain S-L1, then #3040 + 1259, then 1265, then 1275, then the routine FK batches, then the L1 owner-path package after S-L1, then the L2 owner-path package before S-L2 (section 8). About 12 to 16 routine migrations, up to 3 owner-path packages, 3 to 4 application PRs. No numbers are picked here.

## 1. What was and was not done

Read: `MIG_1275_REPORT.md`, `mig1275_gap_report.txt`, `mig1275_chart_delete_blockers_rows.txt`, `FK_CASCADE_INVENTORY_2026-10-04.md`, the delete route on `origin/main` (`platform/src/app/api/charts/[id]/route.ts`, 169 lines), the consent withdrawal sweep (`platform/src/lib/pariprashna/consent/withdrawal.ts`, `scope.ts`, migration 575), the pool (`platform/src/lib/db/client.ts`), the cockpit clear route, PRs #3033 (1265), #3064 (1275), #3045 (1272/1273), #3061 (1274) and migrations 423, 674, 1033. Queried (reader role, `default_transaction_read_only=on`): relations, columns, constraints, triggers, trigger function bodies, ACLs, row counts of per-chart tables (exact `count(*)` below 300 MB; canonical-chart index counts above it). Not done: any write, any migration file, any change to a proxy, any read of a `*_content*` column.

## 2. How deletion works today

### 2.1 The route (`DELETE /api/charts/[id]`)

Authorization is sound (owner, `client_id`, or `super_admin`). The body then runs `BEGIN`, deletes `messages`, `conversations`, `conversation_branches`, `asset_throughput`, `build_runs`, `pyramid_layers`, `chart_grants`, `charts`, `COMMIT`; any error runs `ROLLBACK` and returns 500 `Delete failed`. Everything else is left to `ON DELETE CASCADE`.

| id | defect | evidence |
|---|---|---|
| R1 | `messages` does not exist (checked `pg_class` in every schema: 0 rows); `conversation_branches.chart_id` does not exist. The first statement throws. | [MEASURED] |
| R2 | `BEGIN`/`COMMIT`/`ROLLBACK` use the pool-level `query()`; the cockpit clear route and the consent sweep both use `pool.connect()` correctly, this route does not. Under an interleaving request the statements run on different connections. Fixture: BEGIN, DELETE of 3 rows, ROLLBACK with one unrelated 200 ms query in flight left `rows_after = 0` (not atomic). | [FIXTURE] `pool_atomicity_demo.js` |
| R3 | No `SET LOCAL statement_timeout`: the pool default of 25 s applies to a delete that will exceed it for any built chart. | [SOURCE] |
| R4 | Deletes `asset_throughput` and `build_runs` explicitly because their keys are NO ACTION; nothing is checked afterwards, so a table that is missed leaves rows with no error. | [SOURCE] |
| R5 | No record of the deletion survives (no receipt, no event). | [SOURCE] |

Two other `DELETE FROM charts` sites exist: `platform/scripts/dedupe_charts.ts:193` (uses the alternate id column `chart_id`, see 2.5) and the two create routes' compensating cleanup (`clients/route.ts:97`, `clients/create/route.ts:387`, run before any child data exists). The cockpit clear route is a per-asset clear, not a chart delete, and is out of scope here except where it meets the 1265 guards.

### 2.2 Foreign keys to `charts` [MEASURED, 33 keys]

* `ON DELETE CASCADE` (21 direct): `asset_freshness`, `asset_provenance_receipts`, `bodha_spine_bundles`, `chart_divisionals`, `chart_grants`, `chart_subject_consent`, `conversations`, `ganita_dashas`, `ganita_graha_sthana`, `ga_prashna_judgment`, `kala_activation`, `kala_bhavishya`, `kala_convergence`, `kala_darshana`, `kala_jivana_parva`, `kala_obstruction`, `layer_approvals`, `phala_rectification`, `phala_rectification_best`, `planner_managed_prashna_jobs`, `pyramid_layers`. Transitive closure: 35 tables (the 21, `phala_anchors` and its four children, the conversation children).
* NO ACTION (9): `asset_throughput`, `build_runs`, `event_chart_state_index`, `ka_gochara_contact`, `ka_gochara_eval_window`, `ka_gochara_generation_seal`, `ka_gochara_relationship_record`, `life_events`, `mimamsa_pool_contributions`.
* RESTRICT (1, explicit in migration 1033): `planner_inquiry_lifecycles`.
* SET NULL (2): `concordance_ayanamsha_flags` (rows survive with `chart_id` NULL), `mcp_sessions.active_chart_id`.
* The NO ACTION on `life_events` and `event_chart_state_index` is the default of `ADD COLUMN ... REFERENCES charts(id)` with no action clause (migration 423); it is not a recorded protective decision. `planner_inquiry_lifecycles` RESTRICT is explicit.
* Further blockers inside the cascade closure: `conversation_summaries` (NO ACTION to `conversations` and `conversation_messages`), `message_parts` (NO ACTION to `conversation_messages`), `pariprashna_retraction_*` and `pariprashna_safety_review_passes` (RESTRICT to their parents). The header of `scope.ts` states that `message_parts` and `conversation_summaries` "cascade"; the production catalogue says NO ACTION. Row counts of these two are not readable by the reader role.

### 2.3 Trigger guards that run on the cascade [SOURCE, bodies read from `pg_proc`]

| guard | tables | what it does on DELETE | chart-delete allowance |
|---|---|---|---|
| `l1_data_plane_guard_active_mutation` (owner `data_plane_l1_owner`, SECURITY DEFINER) | `chart_facts`, `chart_dashas`, `chart_divisionals`, `chart_vichara`, 7 `ga_*` tables, `l1_tajik_varsha_year_lords` (11) | raises unless `session_user = 'data_plane_builder'` and a build generation context is set; `chart_facts` additionally needs a temp-table receipt per fact | **none** |
| `l2_data_plane_guard_active_mutation` (owner `data_plane_l2_owner`) | 28 of the 29 `bodha_*` tables (not `bodha_spine_bundles`, not `bodha_cdlm_evolution_gradients`), `synthesis_quality_scorecard` | same session_user check and context | **none** |
| `l1_/l2_data_plane_reject_immutable_change`, `*_guard_generation_change`, `l2_data_plane_guard_completed_run_rows` | 14 per-chart `l1_/l2_data_plane_*` control tables, `data_plane_l2_producer_generations` | unconditional "append-only" or "completed generation is immutable" (bodies read) | **none** |
| `pariprashna_safety_append_only_guard` | `pariprashna_safety_decisions`, `_retractions`, `_review_events`, `_review_passes`, `_retraction_prediction_notes` | unconditional | **none** |
| `ka_gochara_chart_write_guard` / `_statement_lock` / `generation_seal_guard` | `ka_gochara_*` chart tables | DELETE refused when the (chart, generation) is SEALED (published) | **none** |
| `ai_reject_history_mutation` | `ai_turn_routing_snapshots`, `ai_turn_role_invocations` | refused unless `pg_trigger_depth() > 1` AND the parent row is already gone | **yes** (the working precedent) |
| `mimamsa_predictions_builder_guard` plus 1265 frozen guards (in flight) | `mimamsa_predictions` and three ledgers | consent-withdrawal exception today; 1265 adds the cascade discriminator | **in 1265** |
| `chart_subject_append_only_guard` | `chart_subject_consent_events`, `chart_subject_deletion_tombstones` | refuses DELETE; neither table has a key to `charts`, so they are never cascaded | n/a (they are the audit trail) |

Fixture result [FIXTURE]: a table with the L1-style guard and a CASCADE FK makes `DELETE FROM charts` fail with "protected L1 DELETE requires direct data_plane_builder authentication" and leaves every row in place (the chart, 3 plain rows, 2 guarded rows all still present). The same table with the allowance (`pg_trigger_depth() >= 2 AND NOT EXISTS (SELECT 1 FROM charts WHERE id = chart_id)`) deletes cleanly, while a direct `DELETE` on the same table with the chart still present is refused.

### 2.4 The consent-withdrawal sweep

`withdrawConsentAndDelete` (`consent/withdrawal.ts`) is flag-gated (`SUBJECT_CONSENT_ENFORCEMENT`, default off) and has **no caller outside tests** [SOURCE]. It is a different operation from chart deletion on purpose: it destroys the L2+ interpretive corpus and keeps `charts`, L1 and build bookkeeping (`SUBJECT_SCOPE_DENY_TABLES`). Its discipline is the model for this design: digest, delete, re-count, tombstone, `verified_deletion_at` only when every re-count is zero, and a dispute interlock. Defects relevant to completeness:

* S1 scope is a hand-maintained prefix allowlist plus an extras list. It does not include `life_events`, `event_chart_state_index`, `prashna_charts`, `lel_event_class_resolution`, `planner_*`, `ganita_*`, `ga_*` and similar. Whether that is intended is not stated for each.
* S2 `conversations` is swept, but `conversation_summaries`/`message_parts` block it (2.2), so the sweep would throw and roll back whole for any chart that has such rows.
* S3 `bodha_*` and `pariprashna_*` match the allowlist, and their guards (2.3) refuse the delete, so the sweep would also throw there. The 1265 consent exception exists only for four L5 tables.
* S4 `DELETE ... WHERE chart_id::text = $1` and the digest/re-count queries cast a uuid column to text, which cannot use the `chart_id` leading index that 179 of the 235 tables have. On `kala_field` (10.3M rows, 5.4 GB) that is three full scans plus an md5 of every row.
* S5 the sweep writes tombstones keyed by `withdrawal_event_seq`; a hard delete has no withdrawal event, so the receipt model needs an extension (5.7).

### 2.5 Two identifiers on `charts`

`charts` has `id` (primary key, the target of all 33 FKs) and `chart_id` (unique, default `gen_random_uuid()`); they differ for 5 of the 7 charts and are equal for the canonical chart and the Abhinandan chart [MEASURED]. Nine per-chart tables sampled (including `chart_vichara`, 25,011 rows over 3 charts) key on `id`, none on the alternate. All other tables were not tested for this. `dedupe_charts.ts` deletes by the alternate column. The design keys everything on `charts.id` and the detector (5.8) includes a check that every `chart_id` value resolves to `charts.id`.

## 3. Inventory

Full table lists, one row per table with owner, row counts and notes, are in Appendix A (235 tables with a `chart_id` column) and Appendix B (the other 195 base tables; there are 431 base tables and 38 views in `public`; the views hold no rows). Classes (counts [MEASURED]):

| class | tables | meaning | what it needs |
|---|---:|---|---|
| A cascade-ok-already | 26 (+9 children without `chart_id`) | FK path exists | guard allowance for `chart_divisionals` and `ga_prashna_judgment` (L1 guard); fix the two NO ACTION conversation children (2.2) |
| R-1275 routine, in 1275 | 27 | owner `amjis_app` | nothing new; ships with #3064 behind #3033 |
| R-other routine | 66 | owner `amjis_app`, no FK (the two `brahma_*` ledgers listed here are being added to 1275 per the coordinator and move to R-1275 when #3064's head shows it; #3064's PR text at head `91077ca3d` was seen to mention them, its SQL was not re-read): `kala_*` 33, `chart_*` 9, `pariprashna_*` 7, `l25_*` 6, `brahma_*` ledgers 2, `build_*` 2, `ka_*` 2, `prashna_*` 2, `bodha_cdlm_evolution_gradients`, `gochara_resonance_map`, `lel_event_class_resolution` | `ADD CONSTRAINT ... ON DELETE CASCADE` (routine); other workstreams for kala/pariprashna/ka; exemption decisions for 4 consent tables |
| B blocked | 11 | direct FK that is not CASCADE: 9 NO ACTION (all `amjis_app`), 1 RESTRICT (`planner_inquiry_lifecycles`, `purna_inquiry_owner`), 1 SET NULL | relink to CASCADE per the section 6 and section 7 decisions |
| O1 owner-path | 18 | `data_plane_l1_owner` (`chart_facts` 420k rows 699 MB, `chart_dashas` 1.46M rows 1.9 GB, `chart_vichara`, `ga_*`, `l1_data_plane_*`) | owner-path package: FKs + guard allowance |
| O2 owner-path | 38 | `data_plane_l2_owner` (`bodha_*` 28, `l2_data_plane_*` 8, `data_plane_l2_producer_generations`, scorecard) | owner-path package: FKs + guard allowance |
| T text-typed `chart_id` | 12 | `build_events`, `convergence_scores`, `mcp_predictions_retired_backup`, `orchestrator_event_register`, `pariprashna_stream_capture`, `projects`, `query_plan_log`, `runtime_config`, `school_*` (3), `system_health` | convert to uuid, or exempt with a reason and delete by a typed predicate in the delete function |
| L log/audit | 2 | `audit_events` (unreadable by reader), `asset_throughput_state_audit` (460 canonical rows, 209 NULL-chart) | retain-or-delete policy |
| H shadow/archive/staging | 35 | 30 `__ssv_` rollback copies, 5 archive/staging; 34 have nullable `chart_id` | disposition (5.9) |
| hidden | see 3.2 | no `chart_id`, still per-chart content | see 3.2 |

The 174 live tables without a cascade path are R (93: 27 in 1275 plus 66 others) + B 11 + O1 18 + O2 38 + T 12 + L 2 = 174, reproduced by the `cls` column of `inventory.csv`; the 35 shadows are counted separately, as in the 1275 report. `mimamsa_pool_contributions` is counted in B and ships relinked in 1275.

### 3.1 Row-count facts [MEASURED]

Canonical chart, live per-chart tables scanned: **11,199,753 rows**; `kala_field` 8,570,075; `kala_field_provenance` 959,032; `chart_dashas` 483,870; `kala_field_boundaries` 261,998; `kala_field_primitives` 165,082; `chart_facts` 143,299; `kala_field_kinematics` 120,118; `kala_taranga` 92,412; `mimamsa_fact_adjustment` 61,523; `bodha_msr_signals` 50,678; `bodha_signal_embeddings` 50,678. By owner: `amjis_app` 10.38M, `data_plane_l1_owner` 0.66M, `data_plane_l2_owner` 0.16M. All per-chart tables together are 15.8 GB (15.1 GB live). Thirty tables were unreadable by the reader role (listed in `inventory.csv`, `mode = DENIED`); their rows are not in the totals. Only 7 charts exist; 3 have built data.

179 of the 235 per-chart tables have a valid `chart_id`-leading index, including every large live table. The 56 without it are the 35 shadows (up to 423 MB) and 21 live tables each under 1 MB (`planner_*`, four `pariprashna_*`, `l25_*`, `query_plan_log`, `system_health` and similar): the cascade lookup is an index probe wherever the volume is.

### 3.2 Per-chart content that is not reachable through `chart_id`

* **Second-hop keys.** `prashna_charts` (2 rows, both with `querent_natal_chart_id` pointing at real charts, holding `question_text`, a people-entered question) has its own id space in `chart_id`; `ga_prashna_lagna` (5 rows) keys on that id and none of its 5 values exists in `charts.id`. Neither has a path to `charts`. `kala_field_weight_versions.fitted_from_chart_id` (1 row, NULL) and `pariprashna_samiksha_digest_journal.run_chart_id` (0 rows) are alternate references.
* **Soft-keyed content, no FK.** `query_trace_steps` (uuid `conversation_id`), `llm_call_log`, `llm_usage_events` (text `conversation_id`; carries prompt, response and system-prompt columns), `pending_streams`, `ai_metering_attempts`, and the `query_id`-keyed `tool_execution_log` (response text), `audit_log` (query text, final output), `context_assembly_item_log`, `plan_alternatives_log`, `performance_queries`, `performance_judge_verdict`, `mcp_prediction_outcomes`. The reader role cannot read `conversations`, so the join to the canonical chart's conversations could not be counted. Whether these rows survive a chart delete is therefore certain by structure and unquantified.
* **Embedded per-chart statistics in global tables.** `gochara_v3_calibration` (`per_chart_hit_rates`, `delta_native`, `delta_abhinandan`) and `mcp_sessions.state_json`. These are derived aggregates, not rows of the chart; policy in 5.7.
* **Orphan check** [MEASURED, exact counts]: rows whose `chart_id` is not in `charts.id`: `ga_prashna_lagna` 5, `prashna_charts` 2, nothing else among the 195 scanned tables. So VALIDATE of the new FKs will pass except for those two. NULL `chart_id` rows exist in `asset_freshness` (39), `asset_provenance_receipts` (39), `asset_throughput` (43), `asset_throughput_state_audit` (209), `concordance_ayanamsha_flags` (2): global-scope rows that no delete should touch.

## 4. What must not be deleted

Other charts' rows (every delete is keyed by `charts.id`; the fixture asserts the second chart is untouched); global reference data (`bg_*`, `brahma_*` catalogues, `reference_*`, `classical_*`, `ephemeris_daily`, `panchanga_daily`, `ka_gochara_*` rule tables, `kala_field_weights`, 135 tables in Appendix B by name prefix); user and connection tables; NULL-`chart_id` rows; the audit trail of the deletion itself (5.7); and anything on the exemption registry with a recorded reason.

## 5. Target design

### 5.1 The one mechanism

Chart deletion is `DELETE FROM charts WHERE id = $1`, nothing else mutating, so that the database, not the route, owns completeness:

1. every table that holds per-chart rows has a validated `ON DELETE CASCADE` path to `charts(id)`, directly or through a parent that has one;
2. every table that must keep rows after a deletion is on a registry with a stated reason, and the registry is what the detector, the withdrawal sweep and the route read (replacing the hand lists in `scope.ts`);
3. every trigger that forbids a DELETE grants one narrow, data-driven exception to the cascade of a chart delete (5.4);
4. the delete runs on one dedicated connection and ends with a residual count that must be zero for every registered table, otherwise the transaction rolls back (5.3);
5. new tables cannot be added without a path or an exemption (5.8).

Alternatives considered: a sweep that deletes table by table (as the consent sweep does) needs privileges and guard exceptions on the same tables anyway, depends on a hand-kept order, and cannot stop a later insert from resurrecting rows for a deleted chart (an FK does: the insert fails); a SECURITY DEFINER purge function per owner is kept only as the carrier for the owner-path parts, not as the mechanism. Partitioning `kala_field` by chart so a delete becomes a partition drop is the one real performance alternative; it is a Kāla re-architecture and is listed in section 7 as an ask, not assumed.

### 5.2 Registry and exemptions

A table `chart_data_scope(tbl text primary key, delete_on_withdrawal bool, delete_on_hard_delete bool, exempt_reason text, ...)` with `CHECK (delete_on_hard_delete OR exempt_reason IS NOT NULL)`, populated from Appendix A. Proposed exemptions (each needs its owner's agreement): `chart_subject_consent_events`, `chart_subject_deletion_tombstones` (the audit trail; no FK; append-only), `chart_subject_exclusions` (the register already has a `subject_deleted` reason designed for this moment), `chart_subject_deletion_disputes` (open disputes block the sweep; a closed one is history), and the new receipts table (5.7). Everything else defaults to delete. The withdrawal sweep then reads `delete_on_withdrawal`, which replaces `SUBJECT_SCOPE_*`, and the detector reads the registry plus the catalogue.

### 5.3 Route and function behaviour

`deleteChart(chartId, principal)` in a library module, called by the route (and by the job, 5.6):

1. authorize (existing logic, kept); typed confirmation token for interactive deletes (section 6);
2. `client = pool.connect()`; `BEGIN`; `SET LOCAL statement_timeout` to the measured budget; `SET LOCAL lock_timeout = '5s'`; `pg_advisory_xact_lock(hashtext('chart_delete:' || id))`; `SELECT ... FROM charts WHERE id = $1 FOR UPDATE`;
3. refuse with 409 and a stable code if a build run for the chart is `running`/`queued` or a withdrawal dispute is open;
4. insert the receipt (5.7) with per-table counts taken from the registry;
5. `DELETE FROM charts WHERE id = $1`;
6. residual check: for every registered table with a `chart_id`, `count(*) WHERE chart_id = $1` using the native column type (a `::text` comparison only for the text-typed class), skipping exempt tables; any non-zero row raises;
7. mark the receipt `verified_empty`, `COMMIT`; release the client in a `finally`.

Failure semantics: any error rolls back everything, including the receipt; the chart is complete or untouched. The response carries a stable code (`CHART_DELETE_BLOCKED`, `CHART_DELETE_TIMEOUT`, `CHART_DELETE_RESIDUAL`, `CHART_DELETE_BUILD_RUNNING`), never "Delete failed" alone, and logs table names and counts only. The residual check is the detector behind the claim "deleted" (CLAUDE.md N.8): a fixture mutant that makes it a no-op must be caught (5.8). A committed fence column `charts.deletion_requested_at` (set in its own short transaction before the long one, cleared by a failed run) makes the chart unservable and unbuildable while the job runs; it does not make the data deletion partial.

### 5.4 Guard interplay

Use one authorization function, `SECURITY DEFINER` with a pinned `search_path`, fail-closed. It must be SECURITY DEFINER because `charts` has row-level security: a guard running as an invoker that cannot see the chart row would read "chart absent" and wrongly authorize (or, fail-closed, wrongly refuse). The function's owner must be a role that can read `charts` under its RLS policies. Consequence stated as a constraint: **do not enable FORCE ROW LEVEL SECURITY on `charts`, or arm its RLS policies for more roles, without revisiting 1265's helper and this one**, because that would change what the owner (and `suvarna_reader`, `data_plane_builder`) see in `charts` (#3033 already records that arming RLS hides rows from the builder):

```sql
chart_cascade_delete_authorizes(p_chart uuid) RETURNS boolean
  = pg_trigger_depth() >= 2 AND NOT EXISTS (SELECT 1 FROM public.charts WHERE id = p_chart)
```

This is the discriminator already proved in #3033 section C1b (named `l5_frozen_chart_cascade_authorizes` there) and the same shape as `ai_reject_history_mutation`. Reuse #3033's function by name if it already takes a chart id; do not write a fourth variant. Each guard calls it at the top of its DELETE branch:

* L1 and L2 guards (owner-path, 5.5): add the call before the `session_user` test. Second-level children (for example `chart_fact_identity` via `chart_facts`) run at depth 3 and are covered by `>= 2`.
* The per-chart `l1_/l2_data_plane_*` control tables (append-only history). Decision needed (section 7): either the allowance (they hold per-chart snapshots and row copies, `l1_data_plane_row_snapshots`, `l2_data_plane_row_snapshots`, `l2_data_plane_run_rows`) or an exemption that states why a copy of the rows may outlive the chart. Their row counts are unreadable to the reader role and the estimates are -1 (never analyzed), so whether they hold anything is not determined.
* `pariprashna_*` append-only and `ka_gochara_*` sealed-generation guards: other workstreams (section 7).
* 1265's four guards: already have it. The two `brahma_*` ledgers get their FKs in 1275 itself (coordinator), so 1265 must land first; the full ruled order is S-L1, then #3040 + 1259, then 1265, then 1275. The 1275 report's finding that "1265 as it stands refuses the chart delete" predates the C1b text now in #3033's body; I did not re-run it and the fixture below must be re-run at merge time.

The withdrawal sweep needs a sibling exception (`consent_state = 'withdrawn'` and no open dispute, as 1265 already does for L5) in the L2 guard, or `bodha_*` stays undeletable by it (S3).

Residual risk named in #3033 stays true: a role that can create a trigger can reach depth 2, but the chart row must also be absent, so a chart that exists is never exposed; only orphan rows could be. With an FK on every table there are no orphan rows after this work, which is a reason to finish the FK coverage.

### 5.5 Getting FKs onto tables the routine runner does not own

Pattern from #3045/#3061: SQL lives outside `platform/migrations` (so `migrate.ts` never sees it), applied by a gated executor with a plan hash, a dry run, `--expect-plan`, a rollback script and a mirrored-roles test.

* **L1 package** (`data_plane_l1_owner`, 18 tables): for each, `ALTER TABLE ... ADD CONSTRAINT <t>_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE NOT VALID`, then `VALIDATE CONSTRAINT`; plus the guard patch generated from the live function body at apply time (1265's capture-then-patch method: refuse to overwrite a body that differs from the captured hash); plus `ga_prashna_lagna` keyed to the prashna id space (3.2). `chart_fact_identity` (`amjis_app`, 251k rows, 169 MB) already cascades from `chart_facts` on `fact_id`; it needs no FK of its own, because the detector accepts the transitive path once `chart_facts` has one.
* **L2 package** (`data_plane_l2_owner`, 38 tables): same, 29 `bodha_*` plus 8 `l2_data_plane_*` plus the scorecard. `bodha_msr_signals` (883 MB) and `bodha_signal_embeddings` (1.2 GB) are the two large ones.
* **Planner**: `planner_inquiry_lifecycles` RESTRICT to CASCADE is the owner's call (section 7).
* The owner roles need `REFERENCES` on `charts` (1033 checked this exact privilege for `purna_inquiry_owner`); the administrator identity and `SET LOCAL ROLE` steps are the ones #3033 already tested on the mirrored roles. Whether `data_plane_l1_owner` and `data_plane_l2_owner` already hold `REFERENCES` on `charts` was not checked.

Lock and validation technique for all FK additions: `ADD ... NOT VALID` takes SHARE ROW EXCLUSIVE briefly on the child and on `charts` and scans nothing; `VALIDATE CONSTRAINT` scans the child under SHARE UPDATE EXCLUSIVE, so writes continue. Do the large tables one per statement with `lock_timeout` and retry, never 90 ALTERs inside one transaction holding `charts` (a long hold blocks every write to `charts`). Each new FK adds a primary-key probe on `charts` per inserted row for the builders (cheap and cached for 7 charts; measure on `kala_field`'s 8.5M-row writes).

### 5.6 Ordering, locking, performance

Order is irrelevant for FK cascades (the database orders them), which is the point of using them. Locking: `DELETE FROM charts` takes ROW EXCLUSIVE on each cascaded table and row locks on the chart's rows only; other charts' builds proceed. Cost model [ESTIMATE, anchored on one measurement]:

* Fixture [FIXTURE]: `kala_field`-like table, 6.0M rows, 3 indexes, about 390 bytes per row, 2.3 GB: cascade delete of 3.0M rows 13.8 s (cold-ish) and 8.3 s (second run, rolled back), on a local SSD with no concurrent load. That is 220 to 360 thousand rows per second.
* Applied to the canonical chart's 11.2M rows: roughly 30 to 60 s warm on that hardware for the cascade; production (network storage, WAL sync, concurrent builders, cold cache) is plausibly 3 to 10 times slower, so minutes. A rollback is cheap in PostgreSQL (0.19 ms on the fixture) but the work, the WAL and the dead tuples are wasted, so a late failure is expensive in I/O rather than in time.
* Therefore: the HTTP request cannot hold the transaction (25 s pool timeout; the platform's request limit was not checked). Run the same function in a worker/job with `SET LOCAL statement_timeout` set to the measured p99 plus margin; the HTTP route returns 202 with a status resource. Batching is **not** recommended as the default because it breaks the all-or-nothing guarantee; it becomes the fallback only if the production-sized mirror shows the single transaction exceeding what the platform tolerates. If it does, the fallback is: committed fence, then per-table chunks (child before parent, `DELETE ... WHERE ctid IN (SELECT ctid ... LIMIT n)`), each chunk its own transaction, then the final `DELETE FROM charts` and residual check; the chart is unreadable throughout, and the run is resumable until the residual check passes. That variant is weaker and must be chosen by SS, not assumed.
* Aftermath: about 15 GB of dead tuples for a fully built chart; autovacuum reclaims space for reuse, the files do not shrink, and Cloud SQL backups/PITR retain the deleted rows for the retention window. "Deleted" here is logical deletion; physical erasure from backups is out of scope and must be stated to the person honestly.
* The pool's `max: 10` and `idle` settings are untouched; the job uses one connection.

### 5.7 Audit trail

What remains after a deletion, and nothing else: a row in a new append-only `chart_deletion_receipts` (no FK to `charts`): `chart_id` uuid, `deleted_at`, `requested_by` principal id, `mode` (`hard_delete`), `registry_version`, per-table row counts as jsonb, `residual_total` (must be 0 for a committed row), the registry hash. No name, no birth data, no content. Plus a `deletion_verified` link on the existing hash-chained `chart_subject_consent_events` (the enum already contains `deletion_verified`; the payload carries `mode: hard_delete`, ids and counts only), so the chain a subject can verify records the deletion, and plus tombstones in `chart_subject_deletion_tombstones` for tables below a size threshold (content hash of sorted row md5s). Hashing 8.5M `kala_field` rows costs a full read of 5.4 GB; recommendation: counts for every table, content hashes only for subject-content tables (conversations, predictions, journal, events, prashna), as a threshold in the registry. The tombstone table's `withdrawal_event_seq` is NOT NULL, so either hard delete allocates a sequence in the chain or the table gets a nullable sibling; one migration either way.

Retained by design: the consent chain, exclusion register history, tombstones, receipts. Retained by policy unless decided otherwise: global fits that embed per-chart statistics (`gochara_v3_calibration`) are recomputed at the next fit and noted in the receipt, not edited by the delete; log/audit tables (`audit_events`, `asset_throughput_state_audit`, `system_health`, `query_plan_log`) get an explicit retain-or-delete line in the registry (default delete when `chart_id` is set; rows with NULL `chart_id` are not touched).

### 5.8 Verification

* **D1 detector (static, catalog-driven, CI-blocking):** every `public` base table with a `chart_id` column must have an `ON DELETE CASCADE` path to `charts` or a registry exemption with a reason. **D2:** no non-CASCADE FK may point at `charts` or at any table in the cascade closure (NO ACTION/RESTRICT block, SET NULL orphans). **D3:** every table in the closure that has a DELETE trigger must appear in a `guard_allowance_verified` list that the fixture below writes. **D4:** every `chart_id` value resolves to `charts.id` (catches the alternate-id class). The recursive CTE for D1 and D2 is in Appendix C and ran on a fixture (D3 and D4 are specified here and were not run): it listed exactly the FK-less table, the text-typed table and the NO ACTION table; dropping the cascade FK on a parent made the parent and its child appear; adding an exemption removed one table [FIXTURE].
* **Fixture (dynamic, mirrored PG, CI for DB-affecting PRs):** build a schema-only mirror with the production roles and triggers (the #3033 world helper `platform/python-sidecar/tests/l5_frozen_guard_world.py` is the pattern); insert a throwaway chart row and one synthetic row per per-chart table (catalog-driven seeding by column type, with hand seeds for the tables it cannot seed; the unseedable list is itself reported); run `deleteChart` as the app role; assert `chart_residual(chart) = 0` for every table, a second seeded chart untouched in every table, the receipt present, the guards still refuse a direct DELETE of an existing chart's rows for the owner and a superuser, and a rolled-back failure leaves every row. On the fixture, the residual function found exactly the two leaks (FK-less table 2 rows, text-typed 1 row) before the FKs existed [FIXTURE].
* **Mutants the suite must catch:** drop one FK; change CASCADE to NO ACTION; remove an allowance call from a guard; add a table with `chart_id` and no path; add an exemption without a reason; replace the residual check with a no-op; run `BEGIN` on the pool instead of a client under a concurrent request (the 3-to-0 case); cascade on the alternate id; widen the discriminator to depth alone (decoy trigger) and to chart-absent alone (orphan delete).

### 5.9 Shadows

The 35 copies: 30 `__ssv_*` rollback snapshots taken for the SUDDHA-VACA rebuild plus 5 archive/staging. Migration 674 already dropped the 7 Kāla ones with the reasoning that the rollback window closed; the remaining ones are L2 (6), L4 (13), L5 (10, including `mimamsa_predictions__ssv_20260728b` with 292 prediction rows, 154 canonical), L1 and bookkeeping (`l1_tajik_varsha_year_lords__ssv_`, `asset_throughput__ssv_`, `build_substep_progress__ssv_`, `synthesis_quality_scorecard__ssv_`). Recommendation: **drop**, per layer, each under that layer's own disposition (674 is the precedent and the template), because an FK on 34 nullable-key copies would keep dead snapshots alive for ever and a chart delete should not depend on them. Two caveats: `kala_gochara_windows__ssv_20260728c` is cited by 674 as deliberately retained (a weak repo reader remains), and `kala_gochara_windows_archive_20260805` is described in 674 as the "hard floor's named irreplaceable v1 archive": per-chart rows (35,620) that a governance rule calls irreplaceable and a person's deletion would remove. That conflict is for SS (section 7). Until dropped, the registry lists each copy with `delete_on_hard_delete = true` and the residual check covers them, which means the FK (or the drop) must exist before the residual check can pass. 29 of the 35 exist only because nothing disposed them yet.

## 6. People-entered data (OPEN-FOR-OWNER)

**Working assumption (OPEN-FOR-OWNER until the owner confirms in Exec Suvarṇa's session; stated by the coordinator, not decided):** when a PERSON deletes their own chart, their life events go with it; N-46 governs agents, not the person's own act. N-46 forbids agents from changing or deleting people-entered data. A deletion the person initiates is their own act, so their events go with their chart. SS is confirming this with the owner; nothing below is built on it until that returns.

Tables that hold people-entered or person-derived content and their current state [MEASURED unless marked]:

| table | rows (canonical) | status today |
|---|---:|---|
| `life_events` | 63 (0 with `pool_consent`, 0 contributed to the pool) | NO ACTION: blocks the delete (accident of migration 423) |
| `event_chart_state_index` | 57 | NO ACTION; computed from the events, so derived data |
| `mimamsa_event_provenance` | 63 | in 1275 |
| `conversations` and children (chat text) | not readable | CASCADE, and the route already deletes them explicitly: the product already treats chat as the person's data that goes with the chart |
| `prashna_charts.question_text` | 2 rows linked to natal charts | not reachable (3.2) |
| `planner_inquiry_lifecycles` | 25 over all charts | RESTRICT, explicit (1033) |
| `mimamsa_journal`, `life_events_staging` | 0, 0 | empty |

Options and consequences:

* **A. Cascade everything (matches the working assumption).** Relink `life_events`, `event_chart_state_index` and the others to CASCADE. Consequence: a person's deletion is complete and consistent with what the route already does to chat. Risk: any role with `DELETE` on `charts` can then erase events; today `amjis_app` and `role_orchestrator` hold it. Mitigations that belong with A: `REVOKE DELETE ON charts FROM role_orchestrator` unless a use is shown (not checked), typed confirmation with a count summary in `DeleteChartDialog`, an export offer using the existing export manifest, and a rule that only `deleteChart` with an owner or `super_admin` principal may issue the statement. Agents never receive that privilege.
* **B. A with a mandatory export first.** Same data model; the route refuses until an export has been offered and acknowledged. Adds a step; protects against regret.
* **C. Detach instead of delete for pooled rows.** Events with `pool_consent = true` are kept with the chart link removed. Needs a `SET NULL` relink and a consent text that covers retention after deletion. Today it applies to 0 rows; it matters only once pooling is used. Without that consent it contradicts the person's act.
* **D. Keep today's accidental behaviour: refuse while events exist.** A person cannot delete a chart that has events until the events are removed one by one in a separate act. It preserves N-46 for agents trivially, and makes "delete my chart" unusable for the canonical chart (63 events). It is not a decision anyone recorded.

Recommendation: A with B's export step, C deferred until pooling is real. The answer decides the relink for `life_events` and `event_chart_state_index` and nothing else in this design.

## 7. Other workstreams: what to ask

* **Kāla / Gochara (ṢAḌ-DARŚANA handoff).** (1) Agree to `ON DELETE CASCADE` from the 33 `kala_*` tables, `ka_gochara_eval_window_record`, `ka_gochara_record_prerequisite` and `gochara_resonance_map` to `charts(id)` (tables plus sizes in Appendix A). (2) Relink the four NO ACTION `ka_gochara_*` keys to CASCADE. (3) Add the `chart_cascade_delete_authorizes` call to `ka_gochara_chart_write_guard`, `ka_gochara_contact_guard`, `ka_gochara_generation_seal_guard` (today a SEALED generation refuses even the cascade; confirm that chart deletion outranks publication-immutability). (4) State whether `kala_gochara_windows_archive_20260805` may be deleted with its chart (5.9). (5) Re-measure `kala_field` delete time and say whether partitioning by chart is acceptable. (6) Confirm no Kāla reader depends on the 8.5M rows surviving a delete. I did not touch any Kāla object.
* **Paripraśna.** `pariprashna_*` append-only guards refuse every delete (PPR-26 "append-only"). Ask: are safety decisions, retractions and reviews about a subject erased with the subject, kept with the chart id as an opaque key, or kept with a redacted payload? Either answer needs a guard change by their owner; the registry records the decision.
* **Planner (Pūrṇa, `purna_inquiry_owner`; Pravāha as named by SS).** Change `planner_inquiry_lifecycles.chart_id` from RESTRICT to CASCADE (children `planner_inquiry_action_reservations`, `planner_inquiry_evidence_receipts` already cascade from it); state whether `principal_uid ... RESTRICT` to `profiles` has a similar effect on account deletion (out of scope here). 25 rows over all charts.
* **Data-plane owners (S-L1 / S-L2 lanes of Exec Suvarṇa).** The two owner-path packages (5.5), and a decision on the 14 append-only per-chart control tables and the producer-generations table (5.4).
* **L5 (#3033, #3064).** `brahma_mimamsa_prediction_ledger` (5 canonical rows) and `brahma_prospective_ledger` (18) are per-chart with no link; the 1275 report excluded them, and 1275 now adds them (coordinator). They depend on 1265's allowance, hence the order. Nothing further to ask.
* **SS decisions.** The three owner questions in section 0 item 6; whether the consent sweep and chart delete share the registry (recommended); the timeout and job model after the mirror measurement.

## 8. Sequence and slots

Proposed order; SS decides.

| step | content | route | counts | depends on |
|---|---|---|---|---|
| G0 | this document; owner answers on section 6; asks in section 7 sent | none | | |
| G1 | route repair (dedicated client, correct statements, stable error codes, fence), registry/exemption/receipts tables, detector in report-only mode; no change to any existing table's behaviour. The repaired route still returns a clean 409 with the blocking table names until the FKs exist. | routine + app | 1 migration (new objects), 1 to 2 app PRs | none; can precede S-L1 |
| G2 | #3040 + 1259, then 1265, then 1275 (1275 now includes the two `brahma_*` ledgers) | already planned (#3040, #3033, #3064) | 0 new | after S-L1, in that ruled order |
| G3 | routine FK batches: small/medium `amjis_app` tables; big tables NOT VALID then VALIDATE; relinks (`event_chart_state_index`, `life_events` per section 6, the four `ka_gochara_*` after their owner agrees); text-typed class; prashna second hop and soft-key FKs; amjis-owned guard allowances; `charts` fence column and the `role_orchestrator` revoke | routine | about 8 to 10 migrations | G2; independent of S-L1 except lock windows |
| G4 | **L1 owner-path package**: 18 FKs + guard allowance, generated from the live body | owner-path | 1 package | after S-L1 closes (it patches the guard function S-L1 depends on and adds keys to tables S-L1 rebuilds) |
| G5 | **L2 owner-path package**: 38 FKs + guard allowance + withdrawal exception | owner-path | 1 package | before S-L2 starts (so S-L2's verification runs against the final guard; a guard body is patched once, in a quiet window) |
| G6 | planner owner change | routine with `SET LOCAL ROLE` (1033 pattern) or owner path | 1 | their decision |
| G7 | shadow dispositions (drops) | routine, per layer | 3 to 4 | each layer's disposition; before the residual check is made blocking |
| G8 | production-sized mirror rehearsal, timeout choice, route switched to the registry-driven `deleteChart` behind a flag, consent sweep switched to the registry, detectors blocking in CI | app + CI | 2 to 3 app PRs | G3 to G7 |

Totals: about 12 to 16 routine migrations (G1 1, G3 8 to 10, G6 0 to 1, G7 3 to 4 as drops), up to 3 owner-path packages (L1, L2, and the planner if it goes that route), 3 to 4 application PRs. Migration numbers are not chosen here.

## 9. What could not be determined

1. Row counts and join keys of thirty tables the reader role cannot read: `conversations`, `ka_gochara_contact|eval_window|eval_window_record|generation_seal|record_prerequisite|relationship_record`, `planner_inquiry_lifecycles`, `planner_managed_prashna_jobs`, `audit_events`, `chart_subject_consent`, `chart_subject_consent_events`, `projects`, `conversation_summaries`, `message_parts`, `data_plane_l2_producer_generations`, and the per-chart `l1_/l2_data_plane_*` control tables. Whether the control tables hold row copies of the canonical chart is unknown.
2. How many soft-keyed rows (3.2) belong to the canonical chart; the reader cannot join through `conversations`.
3. The production cascade time. One synthetic measurement only; the production-sized mirror is the missing instrument. Also the platform's request timeout and whether Cloud Run Jobs or an existing worker is the intended carrier.
4. Whether `data_plane_l1_owner`/`data_plane_l2_owner` hold `REFERENCES` on `charts`, and whether the administrator path used for #3033 can reach them.
5. Whether the pattern in `ai_reject_history_mutation` and #3033's C1b behave identically for a third-level cascade through a `SECURITY DEFINER` guard owned by a role without SELECT on `charts` (fail-closed would refuse). The fixture must include a guard owned by a non-owner role.
6. The state of #3033 after its latest edits: the 1275 report said 1265 refused the chart delete; #3033's body now contains the discriminator. I did not re-run that interplay.
7. Whether any row of the 135 reference-looking tables in Appendix B is per-chart: classified by name prefix, not row-inspected.
8. Whether anything uses `charts.chart_id` (the alternate id) as a key outside `dedupe_charts.ts`: nine tables sampled, none; the other tables not tested.
9. Whether `role_orchestrator` needs `DELETE` on `charts`.
10. Physical erasure from backups and logs; the proxy log directories under the evidence folder are not part of this design.
11. The completeness of seeding every table synthetically for the fixture; some `CHECK`s and triggers will need hand seeds.
12. `mcp_sessions.state_json`, `llm_usage_events` text columns and similar may contain chart content by value (not by key); no content was read.
13. The 25-second and 10-connection pool facts are from the code; production's Cloud SQL settings were not queried.

## 10. Evidence index

`/Users/Dev/suvarna-evidence/TrackI/cdd/`: `main.sql`, `main_out.txt` (431-table catalogue query), `reach.sql`/`reach_out.txt` (cascade closure, 36 relations including `charts`), `blockers.sql`/`blockers_out.txt`, `hidden.sql`/`hidden_out.txt`, `guards_out.txt`, `l1_guard_src.txt`, `l2_guard_src.txt`, `scan.sh`/`scan_out.txt` (row counts), `inventory.csv` (235 rows), `detector.sql`, fixture files (`fixture_setup.sql`, `fixture_seed_builder.sql`, `fixture_tests.sql`, `fixture_t2.sql`, `fixture_t3.sql`, `fixture_resid_fn.sql`, `fixture_scale.sql`, `pool_atomicity_demo.js`), generators (`gen_inventory.py`, `gen_appendix.py`, `gen_appendix_b.py`). The disposable PostgreSQL (PID 11956, unix socket only) was stopped by that PID and its directory deleted.

---

## Appendix A. Per-chart tables (235), by class

Columns: rows are exact counts unless marked; "denied" means the reader role cannot read the table; `~` is the planner estimate (tables over 300 MB were counted for the canonical chart through the index only). "trg" lists user DELETE triggers on the table.


### A. cascade-ok-already (FK path to charts) (26)

| table | owner | rows (all charts) | rows (canonical) | size | chart_id | delete-trigger / note |
|---|---|---:|---:|---:|---|---|
| `asset_freshness` | amjis_app | 98 | 57 | 168.0 kB | uuid | chart_id nullable; 39 NULL-chart rows |
| `asset_provenance_receipts` | amjis_app | 98 | 57 | 392.0 kB | uuid | chart_id nullable; 39 NULL-chart rows |
| `bodha_spine_bundles` | amjis_app | 1 | 1 | 208.0 kB | uuid |  |
| `chart_divisionals` | data_plane_l1_owner | 71,476 | 24,392 | 78.6 MB | uuid | trg: l1_data_plane_guard_active_mutation |
| `chart_grants` | amjis_app | 10 | 3 | 80.0 kB | uuid |  |
| `chart_subject_consent` | amjis_app | denied | denied | 40.0 kB | uuid |  |
| `conversations` | amjis_app | denied | denied | 1.4 MB | uuid |  |
| `ga_prashna_judgment` | data_plane_l1_owner | 0 | 0 | 48.0 kB | uuid | trg: l1_data_plane_guard_active_mutation |
| `ganita_dashas` | amjis_app | 819 | 819 | 408.0 kB | uuid |  |
| `ganita_graha_sthana` | amjis_app | 10 | 10 | 96.0 kB | uuid |  |
| `kala_activation` | amjis_app | ~336,357 | 0 | 1.6 GB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_bhavishya` | amjis_app | 100 | 0 | 472.0 kB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_convergence` | amjis_app | 20,497 | 0 | 80.4 MB | uuid | chart_id nullable; KALA (SAD-DARSANA handoff) |
| `kala_darshana` | amjis_app | 750 | 0 | 1.4 MB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_jivana_parva` | amjis_app | 309 | 100 | 4.1 MB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_obstruction` | amjis_app | 747 | 0 | 1.3 MB | uuid | KALA (SAD-DARSANA handoff) |
| `layer_approvals` | amjis_app | 0 | 0 | 32.0 kB | uuid |  |
| `phala_anchors` | amjis_app | 60 | 4 | 1.6 MB | uuid |  |
| `phala_pramana` | amjis_app | 60 | 4 | 824.0 kB | uuid |  |
| `phala_rectification` | amjis_app | 370 | 185 | 376.0 kB | uuid |  |
| `phala_rectification_best` | amjis_app | 2 | 1 | 96.0 kB | uuid |  |
| `phala_sankrama` | amjis_app | 630 | 155 | 9.3 MB | uuid |  |
| `phala_sodhana` | amjis_app | 41 | 0 | 520.0 kB | uuid |  |
| `phala_suddha_sodhana` | amjis_app | 60 | 4 | 664.0 kB | uuid |  |
| `planner_managed_prashna_jobs` | purna_inquiry_owner | denied | denied | 216.0 kB | uuid | PLANNER (purna_inquiry_owner) |
| `pyramid_layers` | amjis_app | 44 | 8 | 96.0 kB | uuid |  |

### B. blocked by a NO ACTION / RESTRICT / SET NULL foreign key directly to charts (11)

| table | owner | rows (all charts) | rows (canonical) | size | chart_id | delete-trigger / note |
|---|---|---:|---:|---:|---|---|
| `asset_throughput` | amjis_app | 268 | 84 | 264.0 kB | uuid | chart_id nullable; 43 NULL-chart rows |
| `build_runs` | amjis_app | 705 | 494 | 1.7 MB | uuid |  |
| `concordance_ayanamsha_flags` | amjis_app | 2 | 0 | 96.0 kB | uuid | chart_id nullable; 2 NULL-chart rows |
| `event_chart_state_index` | amjis_app | 57 | 57 | 168.0 kB | uuid |  |
| `ka_gochara_contact` | amjis_app | denied | denied | 48.0 kB | uuid | trg: ka_gochara_chart_statement_lock,ka_gochara_contact_guard; GOCHARA/KALA (SAD-DARSANA handoff) |
| `ka_gochara_eval_window` | amjis_app | denied | denied | 48.0 kB | uuid | trg: ka_gochara_chart_statement_lock,ka_gochara_chart_write_guard; GOCHARA/KALA (SAD-DARSANA handoff) |
| `ka_gochara_generation_seal` | amjis_app | denied | denied | 16.0 kB | uuid | trg: ka_gochara_generation_seal_guard; GOCHARA/KALA (SAD-DARSANA handoff) |
| `ka_gochara_relationship_record` | amjis_app | denied | denied | 72.0 kB | uuid | trg: ka_gochara_chart_statement_lock,ka_gochara_chart_write_guard; GOCHARA/KALA (SAD-DARSANA handoff) |
| `life_events` | amjis_app | 63 | 63 | 248.0 kB | uuid |  |
| `mimamsa_pool_contributions` | amjis_app | 0 | 0 | 24.0 kB | uuid | in 1275 (#3064) |
| `planner_inquiry_lifecycles` | purna_inquiry_owner | denied | denied | 1016.0 kB | uuid | PLANNER (purna_inquiry_owner) |

### R-1275. routine route, covered by migration 1275 (#3064, HELD) (27)

| table | owner | rows (all charts) | rows (canonical) | size | chart_id | delete-trigger / note |
|---|---|---:|---:|---:|---|---|
| `mimamsa_adjudication_log` | amjis_app | 0 | 0 | 32.0 kB | uuid | in 1275 (#3064) |
| `mimamsa_anchor_adjustment` | amjis_app | 195 | 139 | 392.0 kB | uuid | in 1275 (#3064) |
| `mimamsa_attribution` | amjis_app | 1,425 | 1,425 | 7.1 MB | uuid | in 1275 (#3064) |
| `mimamsa_calibration` | amjis_app | 57 | 57 | 408.0 kB | uuid | in 1275 (#3064) |
| `mimamsa_calibration_snapshot` | amjis_app | 5 | 4 | 48.0 kB | uuid | in 1275 (#3064) |
| `mimamsa_convergence_adjustment` | amjis_app | 1,000 | 500 | 592.0 kB | uuid | in 1275 (#3064) |
| `mimamsa_discoveries` | amjis_app | 71 | 71 | 168.0 kB | uuid | in 1275 (#3064) |
| `mimamsa_event_provenance` | amjis_app | 63 | 63 | 136.0 kB | uuid | in 1275 (#3064) |
| `mimamsa_export_log` | amjis_app | 0 | 0 | 32.0 kB | uuid | in 1275 (#3064) |
| `mimamsa_fact_adjustment` | amjis_app | 123,272 | 61,523 | 60.5 MB | uuid | in 1275 (#3064) |
| `mimamsa_insight_embeddings` | amjis_app | 0 | 0 | 1.2 MB | uuid | in 1275 (#3064) |
| `mimamsa_insight_units` | amjis_app | 150 | 115 | 472.0 kB | uuid | in 1275 (#3064) |
| `mimamsa_intervention_ledger` | amjis_app | 0 | 0 | 56.0 kB | uuid | in 1275 (#3064) |
| `mimamsa_journal` | amjis_app | 0 | 0 | 32.0 kB | uuid | in 1275 (#3064) |
| `mimamsa_load_bearing` | amjis_app | 9 | 4 | 80.0 kB | uuid | in 1275 (#3064) |
| `mimamsa_manifestation_grammar` | amjis_app | 47 | 24 | 112.0 kB | uuid | in 1275 (#3064) |
| `mimamsa_manifestation_sets` | amjis_app | 195 | 139 | 440.0 kB | uuid | in 1275 (#3064) |
| `mimamsa_multipliers` | amjis_app | 18 | 9 | 120.0 kB | uuid | in 1275 (#3064) |
| `mimamsa_predictions` | amjis_app | 195 | 139 | 888.0 kB | uuid | trg: mimamsa_predictions_builder_guard; in 1275 (#3064) |
| `mimamsa_qa_eval` | amjis_app | 174 | 168 | 288.0 kB | uuid | in 1275 (#3064) |
| `mimamsa_reliability` | amjis_app | 6 | 6 | 48.0 kB | uuid | in 1275 (#3064) |
| `mimamsa_resonance_feedback` | amjis_app | 0 | 0 | 32.0 kB | uuid | in 1275 (#3064) |
| `mimamsa_signal_adjustment` | amjis_app | 100,275 | 50,104 | 66.4 MB | uuid | in 1275 (#3064) |
| `mimamsa_snapshot_cosign` | amjis_app | 0 | 0 | 40.0 kB | uuid | in 1275 (#3064) |
| `phala_mitigation` | amjis_app | 1,277 | 536 | 3.5 MB | uuid | in 1275 (#3064) |
| `phala_muhurta` | amjis_app | 183 | 134 | 944.0 kB | uuid | in 1275 (#3064) |
| `phala_phaladesa` | amjis_app | 26 | 13 | 320.0 kB | uuid | in 1275 (#3064) |

### R-other. routine route (owner amjis_app), cascade still to be added (not in 1275) (66)

| table | owner | rows (all charts) | rows (canonical) | size | chart_id | delete-trigger / note |
|---|---|---:|---:|---:|---|---|
| `bodha_cdlm_evolution_gradients` | amjis_app | 0 | 0 | 32.0 kB | uuid |  |
| `brahma_mimamsa_prediction_ledger` | amjis_app | 5 | 5 | 104.0 kB | uuid |  |
| `brahma_prospective_ledger` | amjis_app | 29 | 18 | 160.0 kB | uuid |  |
| `build_protected_assets` | amjis_app | 3 | 1 | 32.0 kB | uuid |  |
| `build_substep_progress` | amjis_app | 2,407 | 1,216 | 872.0 kB | uuid |  |
| `chart_fact_identity` | amjis_app | 251,468 | 1,205 | 169.3 MB | uuid |  |
| `chart_facts_history` | amjis_app | 0 | 0 | 32.0 kB | uuid |  |
| `chart_facts_supersedence` | amjis_app | 0 | 0 | 24.0 kB | uuid |  |
| `chart_panchanga` | amjis_app | 0 | 0 | 64.0 kB | uuid |  |
| `chart_panchanga_cache` | amjis_app | 0 | 0 | 24.0 kB | uuid |  |
| `chart_subject_consent_events` | amjis_app | denied | denied | 32.0 kB | uuid | trg: chart_subject_append_only_guard |
| `chart_subject_deletion_disputes` | amjis_app | 0 | 0 | 24.0 kB | uuid |  |
| `chart_subject_deletion_tombstones` | amjis_app | 0 | 0 | 32.0 kB | uuid | trg: chart_subject_append_only_guard |
| `chart_subject_exclusions` | amjis_app | 0 | 0 | 32.0 kB | uuid |  |
| `gochara_resonance_map` | amjis_app | 1,453 | 623 | 832.0 kB | uuid | GOCHARA/KALA (SAD-DARSANA handoff) |
| `ka_gochara_eval_window_record` | amjis_app | denied | denied | 32.0 kB | uuid | trg: ka_gochara_chart_statement_lock,ka_gochara_chart_write_guard; GOCHARA/KALA (SAD-DARSANA handoff) |
| `ka_gochara_record_prerequisite` | amjis_app | denied | denied | 32.0 kB | uuid | trg: ka_gochara_chart_statement_lock,ka_gochara_chart_write_guard,ka_gochara_record_finalize_check; GOCHARA/KALA (SAD-DARSANA handoff) |
| `kala_activation_predicates` | amjis_app | 150,724 | 50,678 | 222.7 MB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_avadhi` | amjis_app | 3,620 | 1,169 | 4.2 MB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_field` | amjis_app | ~10,280,842 | 8,570,075 | 5.2 GB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_field_boundaries` | amjis_app | ~511,320 | 261,998 | 319.8 MB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_field_clocks` | amjis_app | 16 | 8 | 96.0 kB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_field_gof` | amjis_app | 6 | 6 | 64.0 kB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_field_kinematics` | amjis_app | 239,661 | 120,118 | 148.2 MB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_field_null` | amjis_app | 210 | 150 | 1.7 MB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_field_primitives` | amjis_app | 316,803 | 165,082 | 240.5 MB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_field_promise_edges` | amjis_app | 220 | 114 | 216.0 kB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_field_promise_nodes` | amjis_app | 174 | 88 | 184.0 kB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_field_provenance` | amjis_app | ~1,348,991 | 959,032 | 1.0 GB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_field_routes` | amjis_app | 182 | 91 | 192.0 kB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_field_salience` | amjis_app | 7,650 | 0 | 13.2 MB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_field_skill` | amjis_app | 7 | 7 | 64.0 kB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_field_snapshots` | amjis_app | 1 | 0 | 104.0 kB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_field_windows` | amjis_app | 25,178 | 17,528 | 20.1 MB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_gochara_authority` | amjis_app | 2 | 1 | 32.0 kB | uuid | GOCHARA/KALA (SAD-DARSANA handoff) |
| `kala_gochara_contacts` | amjis_app | ~138,836 | 0 | 351.9 MB | uuid | GOCHARA/KALA (SAD-DARSANA handoff) |
| `kala_gochara_coverage` | amjis_app | 48 | 0 | 104.0 kB | uuid | GOCHARA/KALA (SAD-DARSANA handoff) |
| `kala_gochara_publication` | amjis_app | 2 | 1 | 112.0 kB | uuid | GOCHARA/KALA (SAD-DARSANA handoff) |
| `kala_gochara_v2_build_state` | amjis_app | 594 | 297 | 312.0 kB | uuid | GOCHARA/KALA (SAD-DARSANA handoff) |
| `kala_gochara_windows` | amjis_app | 40,117 | 17,211 | 186.6 MB | uuid | trg: kala_gochara_generation_guard; GOCHARA/KALA (SAD-DARSANA handoff) |
| `kala_gochara_windows_v2` | amjis_app | 1,993 | 1,001 | 6.1 MB | uuid | GOCHARA/KALA (SAD-DARSANA handoff) |
| `kala_insights` | amjis_app | 415 | 0 | 1.7 MB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_kota_chakra` | amjis_app | 1,170 | 585 | 1.5 MB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_moorti_nirnaya` | amjis_app | 148 | 74 | 296.0 kB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_paddhati_profile` | amjis_app | 12 | 6 | 120.0 kB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_sudarshana_varsha` | amjis_app | 120 | 120 | 136.0 kB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_taranga` | amjis_app | 277,236 | 92,412 | 185.9 MB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_timeline_spec` | amjis_app | 6 | 0 | 6.4 MB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_tithi_pravesha` | amjis_app | 240 | 120 | 624.0 kB | uuid | KALA (SAD-DARSANA handoff) |
| `kala_vedha_gochara` | amjis_app | 344 | 171 | 1.9 MB | uuid | KALA (SAD-DARSANA handoff) |
| `l25_cdlm_cells` | amjis_app | 0 | 0 | 16.0 kB | uuid |  |
| `l25_cgm_edges` | amjis_app | 0 | 0 | 16.0 kB | uuid |  |
| `l25_cgm_nodes` | amjis_app | 0 | 0 | 16.0 kB | uuid |  |
| `l25_msr_signals` | amjis_app | 0 | 0 | 16.0 kB | uuid |  |
| `l25_rm_resonances` | amjis_app | 0 | 0 | 16.0 kB | uuid |  |
| `l25_ucn_digests` | amjis_app | 0 | 0 | 16.0 kB | uuid |  |
| `lel_event_class_resolution` | amjis_app | 64 | 64 | 128.0 kB | uuid |  |
| `pariprashna_ledger_outbox` | amjis_app | 18 | 5 | 96.0 kB | uuid | PARIPRASHNA (PPR-26) |
| `pariprashna_persistence_outbox` | amjis_app | 0 | 0 | 80.0 kB | uuid | PARIPRASHNA (PPR-26) |
| `pariprashna_predictive_samples` | amjis_app | 13 | 5 | 64.0 kB | uuid | PARIPRASHNA (PPR-26) |
| `pariprashna_retractions` | amjis_app | 0 | 0 | 24.0 kB | uuid | trg: pariprashna_safety_append_only_guard; PARIPRASHNA (PPR-26) |
| `pariprashna_safety_decisions` | amjis_app | 2,336 | 38 | 1.3 MB | uuid | trg: pariprashna_safety_append_only_guard; PARIPRASHNA (PPR-26) |
| `pariprashna_safety_notifications` | amjis_app | 2 | 0 | 48.0 kB | uuid | PARIPRASHNA (PPR-26) |
| `pariprashna_safety_reviews` | amjis_app | 11 | 2 | 64.0 kB | uuid | PARIPRASHNA (PPR-26) |
| `prashna_charts` | amjis_app | 2 | 0 | 32.0 kB | uuid | 2 orphan rows |
| `prashna_followup_schedule` | amjis_app | 0 | 0 | 40.0 kB | uuid |  |

### O1. owner-path needed: data_plane_l1_owner (18)

| table | owner | rows (all charts) | rows (canonical) | size | chart_id | delete-trigger / note |
|---|---|---:|---:|---:|---|---|
| `chart_dashas` | data_plane_l1_owner | ~1,460,985 | 483,870 | 1.9 GB | uuid | trg: l1_data_plane_guard_active_mutation |
| `chart_facts` | data_plane_l1_owner | ~420,236 | 143,299 | 698.8 MB | uuid | trg: l1_data_plane_guard_active_mutation |
| `chart_vichara` | data_plane_l1_owner | 25,011 | 8,524 | 37.4 MB | uuid | trg: l1_data_plane_guard_active_mutation |
| `ga_condition_composite` | data_plane_l1_owner | 135 | 45 | 504.0 kB | uuid | trg: l1_data_plane_guard_active_mutation |
| `ga_medical` | data_plane_l1_owner | 135 | 45 | 176.0 kB | uuid | trg: l1_data_plane_guard_active_mutation |
| `ga_prashna_lagna` | data_plane_l1_owner | 5 | 0 | 48.0 kB | uuid | trg: l1_data_plane_guard_active_mutation; 5 orphan rows |
| `ga_transit_anchors` | data_plane_l1_owner | 135 | 45 | 152.0 kB | uuid | trg: l1_data_plane_guard_active_mutation |
| `ga_vastu_planet_direction_map` | data_plane_l1_owner | 120 | 40 | 120.0 kB | uuid | trg: l1_data_plane_guard_active_mutation |
| `ga_yoga_firings` | data_plane_l1_owner | 202 | 53 | 504.0 kB | uuid | trg: l1_data_plane_guard_active_mutation |
| `l1_data_plane_configuration_snapshots` | data_plane_l1_owner | denied | denied | 24.0 kB | uuid | trg: l1_data_plane_reject_immutable_change |
| `l1_data_plane_dasha_snapshots` | data_plane_l1_owner | denied | denied | 24.0 kB | uuid | trg: l1_data_plane_reject_immutable_change |
| `l1_data_plane_fact_snapshots` | data_plane_l1_owner | denied | denied | 24.0 kB | uuid | trg: l1_data_plane_reject_immutable_change |
| `l1_data_plane_generation_heads` | data_plane_l1_owner | denied | denied | 16.0 kB | uuid |  |
| `l1_data_plane_generation_partitions` | data_plane_l1_owner | denied | denied | 16.0 kB | uuid | trg: l1_data_plane_reject_immutable_change |
| `l1_data_plane_generations` | data_plane_l1_owner | denied | denied | 16.0 kB | uuid | trg: l1_data_plane_guard_generation_change |
| `l1_data_plane_partition_contexts` | data_plane_l1_owner | denied | denied | 16.0 kB | uuid | trg: l1_data_plane_reject_immutable_change |
| `l1_data_plane_row_snapshots` | data_plane_l1_owner | denied | denied | 32.0 kB | uuid | trg: l1_data_plane_reject_immutable_change |
| `l1_tajik_varsha_year_lords` | data_plane_l1_owner | 780 | 240 | 3.0 MB | uuid | trg: l1_data_plane_guard_active_mutation |

### O2. owner-path needed: data_plane_l2_owner (38)

| table | owner | rows (all charts) | rows (canonical) | size | chart_id | delete-trigger / note |
|---|---|---:|---:|---:|---|---|
| `bodha_anomalies` | data_plane_l2_owner | 10,873 | 3,276 | 7.1 MB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_cdlm_cells` | data_plane_l2_owner | 430 | 280 | 5.8 MB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_cdlm_chart_summary` | data_plane_l2_owner | 15 | 5 | 128.0 kB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_cdlm_domain_rollups` | data_plane_l2_owner | 120 | 60 | 248.0 kB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_cdlm_pattern_clusters` | data_plane_l2_owner | 15 | 5 | 2.6 MB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_cgm_chart_topology_summary` | data_plane_l2_owner | 15 | 5 | 256.0 kB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_cgm_edges` | data_plane_l2_owner | 2,517 | 849 | 5.7 MB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_cgm_motifs` | data_plane_l2_owner | 1,811 | 600 | 2.6 MB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_cgm_nodes` | data_plane_l2_owner | 1,101 | 385 | 1.6 MB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_cgm_paths` | data_plane_l2_owner | 135 | 45 | 352.0 kB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_cgm_sub_graphs` | data_plane_l2_owner | 15 | 5 | 376.0 kB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_chart_gestalt` | data_plane_l2_owner | 15 | 5 | 1.0 MB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_contradictions` | data_plane_l2_owner | 45 | 15 | 3.7 MB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_convergence` | data_plane_l2_owner | 120 | 60 | 360.0 kB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_discoveries` | data_plane_l2_owner | 3,695 | 1,161 | 14.2 MB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_grounding_matches` | data_plane_l2_owner | 50,731 | 50,731 | 43.6 MB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_mechanisms` | data_plane_l2_owner | 1,868 | 615 | 3.9 MB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_msr_signals` | data_plane_l2_owner | ~150,309 | 50,678 | 882.6 MB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_pratijna` | data_plane_l2_owner | 405 | 135 | 12.7 MB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_question_lenses` | data_plane_l2_owner | 180 | 60 | 272.1 MB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_rm_chart_summary` | data_plane_l2_owner | 15 | 5 | 208.0 kB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_rm_dasha_windowed_prescriptions` | data_plane_l2_owner | 20 | 5 | 248.0 kB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_rm_dosha_remedy_bundles` | data_plane_l2_owner | 10 | 5 | 112.0 kB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_rm_pattern_remedies` | data_plane_l2_owner | 135 | 45 | 144.0 kB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_rm_remedy_prescriptions` | data_plane_l2_owner | 405 | 135 | 1.6 MB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_rm_resonances` | data_plane_l2_owner | 135 | 45 | 744.0 kB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_signal_embeddings` | data_plane_l2_owner | ~150,724 | 50,678 | 1.2 GB | uuid | trg: l2_data_plane_guard_active_mutation |
| `bodha_triangulation` | data_plane_l2_owner | 405 | 195 | 7.0 MB | uuid | trg: l2_data_plane_guard_active_mutation |
| `data_plane_l2_producer_generations` | data_plane_l2_owner | denied | denied | 16.0 kB | uuid | trg: l2_data_plane_guard_generation_change |
| `l2_data_plane_generation_heads` | data_plane_l2_owner | denied | denied | 16.0 kB | uuid |  |
| `l2_data_plane_generation_partitions` | data_plane_l2_owner | denied | denied | 16.0 kB | uuid | trg: l2_data_plane_reject_immutable_change |
| `l2_data_plane_generation_runs` | data_plane_l2_owner | denied | denied | 16.0 kB | uuid | trg: l2_data_plane_reject_immutable_change |
| `l2_data_plane_input_bind_receipts` | data_plane_l2_owner | denied | denied | 16.0 kB | uuid | trg: l2_data_plane_reject_immutable_change |
| `l2_data_plane_partition_contexts` | data_plane_l2_owner | denied | denied | 16.0 kB | uuid | trg: l2_data_plane_reject_immutable_change |
| `l2_data_plane_row_snapshots` | data_plane_l2_owner | denied | denied | 24.0 kB | uuid | trg: l2_data_plane_reject_immutable_change |
| `l2_data_plane_run_intents` | data_plane_l2_owner | denied | denied | 16.0 kB | uuid | trg: l2_data_plane_reject_immutable_change |
| `l2_data_plane_run_rows` | data_plane_l2_owner | denied | denied | 16.0 kB | uuid | trg: l2_data_plane_guard_completed_run_rows |
| `synthesis_quality_scorecard` | data_plane_l2_owner | 3 | 1 | 88.0 kB | uuid | trg: l2_data_plane_guard_active_mutation |

### T. text-typed chart_id (an FK to charts(id) uuid is impossible as the column stands) (12)

| table | owner | rows (all charts) | rows (canonical) | size | chart_id | delete-trigger / note |
|---|---|---:|---:|---:|---|---|
| `build_events` | amjis_app | 0 | 0 | 40.0 kB | text |  |
| `convergence_scores` | amjis_app | 0 | 0 | 56.0 kB | text |  |
| `mcp_predictions_retired_backup` | amjis_app | 12 | 10 | 16.0 kB | text | chart_id nullable; MCP |
| `orchestrator_event_register` | amjis_app | 2 | 2 | 80.0 kB | text | chart_id nullable |
| `pariprashna_stream_capture` | amjis_app | 0 | 0 | 32.0 kB | text | chart_id nullable; PARIPRASHNA (PPR-26) |
| `projects` | amjis_app | denied | denied | 16.0 kB | text | chart_id nullable |
| `query_plan_log` | amjis_app | 19 | 3 | 208.0 kB | text | chart_id nullable |
| `runtime_config` | amjis_app | 0 | 0 | 24.0 kB | text | chart_id nullable |
| `school_analysis_runs` | amjis_app | 0 | 0 | 56.0 kB | text |  |
| `school_disagreements` | amjis_app | 0 | 0 | 64.0 kB | text |  |
| `school_signal_coverage` | amjis_app | 0 | 0 | 72.0 kB | text |  |
| `system_health` | amjis_app | 64 | 32 | 96.0 kB | text | chart_id nullable |

### L. log / audit tables (retain-or-delete is a policy call) (2)

| table | owner | rows (all charts) | rows (canonical) | size | chart_id | delete-trigger / note |
|---|---|---:|---:|---:|---|---|
| `asset_throughput_state_audit` | amjis_app | 713 | 460 | 408.0 kB | uuid | chart_id nullable; 209 NULL-chart rows |
| `audit_events` | amjis_app | denied | denied | 48.0 kB | uuid | chart_id nullable |

### H. shadow / archive / staging copies (35)

| table | owner | rows (all charts) | rows (canonical) | size | chart_id | delete-trigger / note |
|---|---|---:|---:|---:|---|---|
| `asset_throughput__ssv_20260728c` | amjis_app | 1 | 0 | 16.0 kB | uuid | chart_id nullable |
| `bodha_cdlm_cells__ssv_20260728a` | amjis_app | 150 | 75 | 1.2 MB | uuid | chart_id nullable |
| `bodha_cgm_edges__ssv_20260728a` | amjis_app | 1,687 | 849 | 1.6 MB | uuid | chart_id nullable |
| `bodha_cgm_nodes__ssv_20260728a` | amjis_app | 711 | 355 | 304.0 kB | uuid | chart_id nullable |
| `bodha_msr_signals__ssv_20260728a` | amjis_app | 99,498 | 49,563 | 147.7 MB | uuid | chart_id nullable |
| `bodha_rm_resonances__ssv_20260728a` | amjis_app | 90 | 45 | 120.0 kB | uuid | chart_id nullable |
| `bodha_signal_embeddings__ssv_20260728a` | amjis_app | ~99,498 | not counted | 423.1 MB | uuid | chart_id nullable |
| `build_substep_progress__ssv_20260728c` | amjis_app | 78 | 0 | 24.0 kB | uuid | chart_id nullable |
| `build_substep_progress_archive_20260805` | amjis_app | 1,212 | 606 | 240.0 kB | uuid | chart_id nullable |
| `builds_staging` | amjis_app | 0 | 0 | 32.0 kB | uuid |  |
| `concordance_ayanamsha_flags_staging` | amjis_app | 0 | 0 | 48.0 kB | uuid | chart_id nullable |
| `kala_convergence_staging` | amjis_app | 0 | 0 | 40.0 kB | uuid | chart_id nullable; KALA (SAD-DARSANA handoff) |
| `kala_gochara_windows__ssv_20260728c` | amjis_app | 1,267 | 0 | 3.6 MB | uuid | chart_id nullable; GOCHARA/KALA (SAD-DARSANA handoff) |
| `kala_gochara_windows_archive_20260805` | amjis_app | 35,620 | 16,297 | 103.1 MB | uuid | chart_id nullable; GOCHARA/KALA (SAD-DARSANA handoff) |
| `l1_tajik_varsha_year_lords__ssv_20260728b` | amjis_app | 475 | 240 | 960.0 kB | uuid | chart_id nullable |
| `mimamsa_calibration__ssv_20260728b` | amjis_app | 67 | 67 | 32.0 kB | uuid | chart_id nullable |
| `mimamsa_insight_units__ssv_20260728a` | amjis_app | 149 | 112 | 112.0 kB | uuid | chart_id nullable |
| `mimamsa_insight_units__ssv_20260728b` | amjis_app | 147 | 111 | 120.0 kB | uuid | chart_id nullable |
| `mimamsa_journal__ssv_20260728b` | amjis_app | 0 | 0 | 8.0 kB | uuid | chart_id nullable |
| `mimamsa_load_bearing__ssv_20260728b` | amjis_app | 9 | 4 | 16.0 kB | uuid | chart_id nullable |
| `mimamsa_manifestation_grammar__ssv_20260728b` | amjis_app | 48 | 24 | 24.0 kB | uuid | chart_id nullable |
| `mimamsa_multipliers__ssv_20260728b` | amjis_app | 18 | 9 | 16.0 kB | uuid | chart_id nullable |
| `mimamsa_predictions__ssv_20260728b` | amjis_app | 292 | 154 | 400.0 kB | uuid | chart_id nullable |
| `mimamsa_qa_eval__ssv_20260728b` | amjis_app | 171 | 165 | 80.0 kB | uuid | chart_id nullable |
| `phala_anchors__ssv_20260728a` | amjis_app | 213 | 106 | 584.0 kB | uuid | chart_id nullable |
| `phala_anchors__ssv_20260728b` | amjis_app | 141 | 3 | 392.0 kB | uuid | chart_id nullable |
| `phala_mitigation__ssv_20260728b` | amjis_app | 1,269 | 553 | 1.5 MB | uuid | chart_id nullable |
| `phala_muhurta__ssv_20260728b` | amjis_app | 270 | 145 | 552.0 kB | uuid | chart_id nullable |
| `phala_phaladesa__ssv_20260728b` | amjis_app | 14 | 7 | 56.0 kB | uuid | chart_id nullable |
| `phala_pramana__ssv_20260728b` | amjis_app | 141 | 3 | 200.0 kB | uuid | chart_id nullable |
| `phala_rectification__ssv_20260728b` | amjis_app | 370 | 185 | 56.0 kB | uuid | chart_id nullable |
| `phala_sankrama__ssv_20260728b` | amjis_app | 1,665 | 55 | 2.6 MB | uuid | chart_id nullable |
| `phala_sodhana__ssv_20260728b` | amjis_app | 17 | 0 | 24.0 kB | uuid | chart_id nullable |
| `phala_suddha_sodhana__ssv_20260728b` | amjis_app | 141 | 3 | 88.0 kB | uuid | chart_id nullable |
| `synthesis_quality_scorecard__ssv_20260728a` | amjis_app | 2 | 1 | 16.0 kB | uuid | chart_id nullable |

## Appendix B. The other 195 base tables (no `chart_id` column)

Classified by foreign keys read from the catalogue where one exists, otherwise by name prefix and by the column lists read from `pg_attribute` (names only). The 135 "global" tables are by prefix, not row-inspected.

- **conversation child, cascades from conversations (already deleted by chart delete)** (9): `ai_conversation_selections`, `ai_turn_role_invocations`, `ai_turn_routing_snapshots`, `conversation_branches`, `conversation_folder_members`, `conversation_message_embeddings`, `conversation_messages`, `conversation_shares`, `project_conversations`
- **conversation child, BLOCKS the delete (NO ACTION) - contradicts scope.ts header** (2): `conversation_summaries`, `message_parts`
- **SOFT-KEYED to a conversation or query id with no FK: content about a chart survives deletion (reader cannot read the join keys)** (16): `ai_metering_attempts`, `ai_metering_receipts`, `audit_log`, `context_assembly_item_log`, `llm_call_log`, `llm_cost_reconciliation`, `llm_provider_cost_reports`, `llm_usage_events`, `mcp_disagreements`, `mcp_prediction_outcomes`, `pending_streams`, `performance_judge_verdict`, `performance_queries`, `plan_alternatives_log`, `query_trace_steps`, `tool_execution_log`
- **child of a per-chart table in another workstream (planner / paripraśna), hangs off RESTRICT** (6): `pariprashna_retraction_notifications`, `pariprashna_retraction_prediction_notes`, `pariprashna_safety_review_events`, `pariprashna_safety_review_passes`, `planner_inquiry_action_reservations`, `planner_inquiry_evidence_receipts`
- **second-hop key (derived id space or alternate chart reference column)** (3): `gochara_v3_calibration`, `kala_field_weight_versions`, `pariprashna_samiksha_digest_journal`
- **people-entered staging (no chart key; 0 rows)** (1): `life_events_staging`
- **build/orchestrator keyed by build or run id, not chart** (6): `build_checkpoints`, `build_dependencies`, `build_engine_versions`, `build_notifications`, `build_run_assets`, `notification_views`
- **user / account / connection keyed** (17): `access_requests`, `admin_audit_log`, `conversation_folders`, `llm_budget_rules`, `llm_pricing_versions`, `llm_stack_config`, `mcp_alerts_config`, `mcp_api_keys`, `mcp_oauth_auth_codes`, `mcp_oauth_clients`, `mcp_oauth_tokens`, `mcp_rate_buckets`, `mcp_sessions`, `mimamsa_preferences`, `personas`, `profiles`, `project_files`
- **global reference / ontology / constants (L0 and registries)** (135): `_migrations_applied`, `ai_cli_grants`, `ai_cli_installations`, `ai_cli_models`, `ai_configuration_audit_log`, `ai_connection_models`, `ai_custom_configuration_roles`, `ai_custom_configurations`, `ai_metering_rate_cards`, `ai_provider_connections`, `ai_user_defaults`, `asset_coefficients`, `asset_output_digest_specs`, `asset_registry`, `bg_avastha_schemes`, `bg_combustion_orbs`, `bg_dignity_reference`, `bg_gochara_arcs`, `bg_gochara_citation_resolution`, `bg_graha_dik`, `bg_graha_naisargika_friendship`, `bg_kota_chakra_rings`, `bg_kp_sublord_division`, `bg_medical_mappings`, `bg_motion_state_thresholds`, `bg_muhurta_activity_rules`, `bg_muhurta_factor_census`, `bg_muhurta_lattice`, `bg_nakshatra_medical`, `bg_parihara_rules`, `bg_phaladeepika_latta`, `bg_prashna_fructification_rules`, `bg_prashna_lagna_methods`, `bg_prashna_significators`, `bg_prashna_special_techniques`, `bg_prashna_tajik_yogas`, `bg_sarvatobhadra_grid`, `bg_shashtiamsha_deities`, `bg_sign_medical`, `bg_sky_calendar`, `bg_synthetic_cohort`, `bg_synthetic_cohort_md`, `bg_transit_av_gates`, `bg_transit_engine`, `bg_transit_moorti`, `bg_transit_rules`, `bg_transit_vedha`, `bg_vastu_direction_remedials`, `bg_vastu_directions`, `bg_vedha_malefic_scale`, `brahma_activity_ontology`, `brahma_class_priors`, `brahma_compendium_index`, `brahma_dasha_systems`, `brahma_dosha_catalog`, `brahma_event_ontology`, `brahma_formula_constants`, `brahma_ontology`, `brahma_remedy_corpus`, `brahma_vichara_constants`, `brahma_yoga_catalog`, `brahma_yoga_source_chunks`, `capability_asset_tool_bindings`, `capability_tool_registry`, `classical_attributions`, `classical_chunks`, `classical_text_chunks`, `classical_texts`, `classical_texts_source`, `concept_ledger`, `engine_versions`, `ephemeris_daily`, `eval_runs`, `fact_category_ownership`, `ka_gochara_av_polarity_declaration`, `ka_gochara_contact_identity`, `ka_gochara_convention_bridge`, `ka_gochara_factor`, `ka_gochara_physical_object`, `ka_gochara_predicate`, `ka_gochara_rule_path`, `ka_gochara_rule_path_prerequisite`, `ka_gochara_rule_path_seal`, `ka_gochara_rule_path_soft_factor`, `ka_gochara_sky_convention`, `ka_gochara_sky_event`, `ka_kshetra_tier_basis`, `kala_field_weights`, `kala_gochara_convention`, `kala_gochara_cutover_step05_snapshot`, `l1_data_plane_function_attestations`, `l1_data_plane_policy_attestations`, `l1_data_plane_sequence_attestations`, `l1_data_plane_trigger_attestations`, `l1_data_plane_view_attestations`, `l2_data_plane_asset_outputs`, `l2_data_plane_function_attestations`, `l2_data_plane_manifest_attestations`, `l2_data_plane_policy_attestations`, `l2_data_plane_sequence_attestations`, `l2_data_plane_trigger_attestations`, `l2_data_plane_view_attestations`, `mimamsa_negative_controls`, `mimamsa_signal_families`, `nirmana_bg_texts_integrity_baselines`, `nirmana_elevation_monitor_observations`, `panchanga_daily`, `reference_aspects`, `reference_constants`, `reference_dasha_systems`, `reference_doshas`, `reference_glossary`, `reference_houses`, `reference_karakas`, `reference_nakshatra`, `reference_nakshatra_matrix`, `reference_nakshatra_pada`, `reference_nakshatras`, `reference_planets`, `reference_signs`, `reference_strength_systems`, `reference_topic_tags`, `reference_upagrahas`, `reference_vargas`, `reference_yogas`, `remedy_review_queue`, `sutravali_review`, `sutravali_rules`, `tool_registry`, `vidhi_floor_items`, `vidhi_intent_floors`, `vidhi_primitives`, `yoga_families`, `yoga_family_members`, `yoga_interaction_rules`

## Appendix C. Proposed SQL (design text, not applied; the detector and residual function were run on a synthetic disposable fixture)

### C.1 Completeness detector (D1 and D2)

```sql
-- D1: every public base table with a chart_id column must have an ON DELETE CASCADE path to charts, or be on the exemption list.
WITH RECURSIVE fk AS (
  SELECT conrelid AS child, confrelid AS parent, confdeltype AS d
    FROM pg_constraint WHERE contype='f' AND connamespace='public'::regnamespace
), reach(rel) AS (
  SELECT 'public.charts'::regclass::oid
  UNION
  SELECT fk.child FROM fk JOIN reach ON fk.parent = reach.rel WHERE fk.d = 'c'
)
SELECT 'D1_no_cascade_path' AS finding, c.relname::text AS tbl
  FROM pg_class c
  JOIN pg_attribute a ON a.attrelid=c.oid AND a.attname='chart_id' AND a.attnum>0 AND NOT a.attisdropped
 WHERE c.relkind IN ('r','p') AND c.relnamespace='public'::regnamespace AND c.relname <> 'charts'
   AND c.oid NOT IN (SELECT rel FROM reach)
   AND c.relname NOT IN (SELECT tbl FROM chart_delete_exemptions)
UNION ALL
-- D2: a non-cascading FK whose parent is charts or any table the cascade deletes from can block (NO ACTION / RESTRICT) or orphan (SET NULL / SET DEFAULT) the delete.
SELECT 'D2_blocker_' || CASE fk.d WHEN 'a' THEN 'no_action' WHEN 'r' THEN 'restrict' WHEN 'n' THEN 'set_null' WHEN 'd' THEN 'set_default' END,
       fk.child::regclass::text || ' -> ' || fk.parent::regclass::text
  FROM fk WHERE fk.parent IN (SELECT rel FROM reach) AND fk.d <> 'c'
   AND fk.child::regclass::text NOT IN (SELECT tbl FROM chart_delete_exemptions)
ORDER BY 1,2;
```

Fixture result with one synthetic table of each kind: D1 listed the FK-less table, the text-typed table and the NO ACTION table; D2 listed the NO ACTION key; after dropping the cascade FK on a parent, the parent and its child both appeared; one exemption row removed one finding.

### C.2 Residual count used inside the delete transaction

```sql
CREATE OR REPLACE FUNCTION chart_residual(p_chart uuid) RETURNS TABLE(tbl text, n bigint)
LANGUAGE plpgsql AS $$
DECLARE r record; k bigint;
BEGIN
  FOR r IN
    SELECT c.relname::text AS relname, format_type(a.atttypid,a.atttypmod) AS typ
      FROM pg_class c JOIN pg_attribute a ON a.attrelid=c.oid AND a.attname='chart_id' AND a.attnum>0 AND NOT a.attisdropped
     WHERE c.relkind='r' AND c.relnamespace='public'::regnamespace AND c.relname <> 'charts'
     ORDER BY 1
  LOOP
    IF r.typ = 'uuid' THEN
      EXECUTE format('SELECT count(*) FROM public.%I WHERE chart_id = $1', r.relname) INTO k USING p_chart;       -- index-friendly
    ELSE
      EXECUTE format('SELECT count(*) FROM public.%I WHERE chart_id = $1', r.relname) INTO k USING p_chart::text; -- text-typed keys
    END IF;
    IF k > 0 THEN tbl := r.relname; n := k; RETURN NEXT; END IF;
  END LOOP;
END $$;
```

Fixture result before FKs existed on two tables: `no_fk_table | 2`, `text_keyed | 1`; nothing from the cascaded, guarded-with-allowance or grandchild tables.

### C.3 Guard allowance (the discriminator of #3033 section C1b and `ai_reject_history_mutation`)

```sql
CREATE FUNCTION chart_cascade_delete_authorizes(p_chart uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, public AS
$$ SELECT pg_trigger_depth() >= 2 AND NOT EXISTS (SELECT 1 FROM public.charts c WHERE c.id = p_chart) $$;
-- at the top of each guard's DELETE branch:
--   IF TG_OP = 'DELETE' AND chart_cascade_delete_authorizes(OLD.chart_id) THEN RETURN OLD; END IF;
```

Fixture results: without the call, `DELETE FROM charts` as the app role fails with "protected L1 DELETE requires direct data_plane_builder authentication" and nothing changes; with the call it succeeds; a direct `DELETE` of one of the same table's rows while the chart exists is refused; a NO ACTION child row blocks the chart delete with a foreign-key error until it is removed.

### C.4 Receipts (sketch)

`chart_deletion_receipts(receipt_id bigserial, chart_id uuid NOT NULL, deleted_at timestamptz NOT NULL DEFAULT now(), requested_by text NOT NULL, mode text NOT NULL CHECK (mode IN ('hard_delete')), registry_hash text NOT NULL, table_counts jsonb NOT NULL, residual_total int NOT NULL CHECK (residual_total = 0))`, no foreign key to `charts`, UPDATE and DELETE refused by the same append-only trigger as the consent tables.

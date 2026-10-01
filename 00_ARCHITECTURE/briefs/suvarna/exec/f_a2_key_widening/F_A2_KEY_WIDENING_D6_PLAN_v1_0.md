---
artifact: F_A2_KEY_WIDENING_D6_PLAN
version: "1.0"
status: DRAFT_FOR_REVIEW
date: 2026-10-02
lane: suvarna/land/TI-l1-fa2-key-001
base_commit: origin/main bf6fe712b
produced_by: exec-suvarna (S-L1 mandatory item Q01 writer lane)
decision: L1 decision sheet Q-L1-01 (SS-ruled N-62, accepted as recommended)
execution: NONE against any real system. DB access was SELECT and catalog reads as `suvarna_reader`; the executor script and the registry migration were exercised only against disposable local PostgreSQL 15 databases built for this lane. Nothing was applied, pushed or numbered.
approval_needed: SS `APPROVED <plan hash>` for the hash `d6_f_a2_key_widening_DRAFT.py --dry-run` prints, plus the owner's standing authorization in the executing session; SS allocates the migration number for the registry migration.
changelog:
  - "1.0 (2026-10-02): first draft."
---

# F-A2: widen the `chart_divisionals` natural key to include `fact_subject`

## 1. Verdict in four lines

1. The ruled change (widen `chart_divisionals_unique_idx` and both `ON CONFLICT` targets to `fact_subject`) is correct and is implemented in the writer on this branch.
2. It is **not** a one-migration change. The index, the L1 capture trigger and one hunk of the L1 capture function are all owned by `data_plane_l1_owner` and are attested; widening the index alone makes every later `ga_vargas` partition abort at completion (section 4). That is why the database half is a **D6 owner-path plan** (`d6_f_a2_key_widening_DRAFT.py`), not an `amjis_app` migration.
3. The row gain is **~14,200 rows per chart, not +250**: the sheet's "D30 60 to 10" is one of four collapsed families (section 3).
4. Only the integrity clause is a plain registry migration (`DRAFT_f_a2_key_widening.sql`, `asset_registry` is `amjis_app`-owned).

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

Preconditions (abort and ROLLBACK otherwise): no `build_runs` in planned/running/paused; no `l1_data_plane_generations` in `building`; the live index, trigger and function have exactly the pre-state this plan was written against.

Statements, as `data_plane_l1_owner`:

1. `CREATE UNIQUE INDEX chart_divisionals_unique_idx_f_a2 ON public.chart_divisionals (<7 cols>) NULLS NOT DISTINCT; DROP INDEX public.chart_divisionals_unique_idx; ALTER INDEX ... RENAME TO chart_divisionals_unique_idx;` (the name is kept: the writer's preflight and every document read it. A superset of a unique key is trivially satisfiable on existing data.)
2. `DROP TRIGGER l1_data_plane_capture ON public.chart_divisionals; CREATE TRIGGER l1_data_plane_capture AFTER INSERT OR UPDATE ... EXECUTE FUNCTION public.l1_data_plane_capture_row(<7 args>);`
3. `CREATE OR REPLACE FUNCTION` from the function's own live `pg_get_functiondef`, with exactly one hunk replaced (asserted to occur once): `'fact_key=' || cd.fact_key` gains `, 'fact_subject=' || COALESCE(cd.fact_subject,'<null>')` and the `ORDER BY` gains `cd.fact_subject`. Owner, SECURITY DEFINER, `proconfig` and ACL are preserved by `CREATE OR REPLACE` (and checked).
4. Re-attest the two rows: `ALTER TABLE ... DISABLE TRIGGER <append-only>`, `UPDATE` the one `definition_digest` from the live object (expected row count 1 each), `ENABLE TRIGGER`, for both attestation tables.

Commit only if ALL hold: exactly one index, one trigger, one trigger-attestation, one function and one function-attestation entry changed across a before/after snapshot of every public index, trigger, `l1_/l2_data_plane_*` function and both attestation tables; ACL, membership, RLS, policy and per-chart row-data (count + md5 of ids) snapshots are identical; the new index is `indisunique`, `indisvalid`, `indnullsnotdistinct` on the 7 columns in order; both append-only triggers are `enabled` again; the two attestation rows equal the live digests under the gate's own join; `--expect-plan` equals the plan hash. Then V1 (after commit, outside the transaction): `data-plane-ownership-status.ts` reports `marked`.

Rollback: before the S-L1 rebuild, the reverse statements restore the old state (the six-column index is trivially satisfiable on the pre-rebuild rows). **After a rebuild that lands the widened rows the six-column index cannot be rebuilt** (the new rows collide on it); a rollback then means deleting the recovered rows first. State this in the approval.

Exercised locally (never against production): the executor's `run()` against a disposable PostgreSQL 15 holding a model of the objects built from the **live** function text. Results: `--count` read-only; `--dry-run` rolled back with the state unchanged; an active build blocked the apply; `--apply` committed with all conditions holding and left the index 7-column, the trigger 7-argument, the function hunk present, both append-only triggers enabled and still enforcing; a second apply was refused by the preconditions. What this does not prove: behaviour of the real role grants, Cloud SQL, or the real attestation tables' extra columns/constraints.

### Order across the four steps

1. D6 plan (above) **in the same window as** the writer deploy: the new writer's explicit seven-column `ON CONFLICT` fails against the six-column index, and the old writer's six-column target fails against the seven-column index. The writer therefore reads the live index at start (`assert_unique_key_grain`) and refuses with a message naming the cause; with no builds running between the two there is no window for a half-state.
2. `DRAFT_f_a2_key_widening.sql` (registry-only). Conjunct (e) is green today; conjunct (f) is red until step 4 by design (migration 654 precedent). SS may split (f) into a second migration to land after the rebuild.
3. (writer deploy, step 1)
4. S-L1 `ga_vargas` rebuild (no extra run; one rebuild carries F-A1, F-A2, F-A3 for the three charts).

## 7. The writer change (this branch)

- `ON CONFLICT (chart_id, graha, ayanamsha_id, varga, fact_category, fact_key, fact_subject) DO NOTHING` in both statements; `UNIQUE_KEY_COLUMNS` is the single named definition.
- `_write_rows_batch` returns rows that LANDED (driver `rowcount`; a per-row `DO NOTHING` conflict is no longer counted) and fills a run-scoped `stats` (`attempted / landed / collided / db_skipped / failed`). `collided` is a deterministic pre-write detector: a row whose seven-column key was already emitted in this run (`find_key_collisions`), sampled and logged at WARNING.
- The per-row fallback no longer swallows rejections: any row the database rejects (not skips) raises with the first error, so a table that refuses every INSERT (RLS with no policy) cannot end `lit` with zero rows. The orchestrator runs each sub-step in a savepoint, so the raise rolls the sub-step back.
- `assert_unique_key_grain(conn)` runs once per call, before any DELETE, and fails closed.
- `build_ga_vargas` summary gains `rows_attempted / rows_landed / rows_collided / rows_db_skipped / rows_failed / collision_samples`; the orchestrator adapter reports `rows_inserted` = stored rows, `rows_skipped` = attempted minus stored, and a `notes` string naming collisions. Idempotency is unchanged: per-chart delete-then-insert, scopes cleared once per run (F-A3), INVARIANT sentinels replaced per ayanamsha and excluded from the run-collision set.
- `WriterBase` contract (CLAUDE.md N.2) is untouched: `plan_substeps` / `run_substep`, no commit, no throughput write. CLAUDE.md N.7 item 2 (total, key-pinned selections) is respected: no selection was added.

## 8. The integrity clause (`DRAFT_f_a2_key_widening.sql`)

The live `integrity_check_sql` (4,216 chars, md5 `255af7c5194553e19f7009c1e8774d8a`, read 2026-10-02) is byte-identical to migration 884's body. All four of its conjuncts are `NOT EXISTS`. The draft keeps them and adds, scoped to the canonical chart by literal (the disclosed 882/884/902/1019/1022/1215 tradeoff):

- **(e) non-vacuity:** for each of the five declared ayanamshas x the thirty declared vargas, `count(varga_position / sign rows for the nine grahas) < 9` makes the check false. Zero rows (an empty table, or RLS blindness) is the extreme case; too few is the partial one. Measured today (conjunct (e) text evaluated read-only against production as `suvarna_reader` inside a READ ONLY transaction, 2026-10-02): (e) is true (the nine rows exist for all 150 pairs), and the whole new check is false, because of (f).
- **(f) key-grain completeness:** 12 `varga_house_lord` and 96 `varga_ashtakavarga` rows per (ayanamsha, varga), 60 `varga_d30_lord_per_amsa` per ayanamsha. These are per-scope structural cardinalities (houses, signs x (7 grahas + SARVA), D30 regions), not a volume pin of the table (the C12 rule in the 884 header); SS can reject that reading and keep only (e). Red on current production data by design.

Behaviour tests against a disposable PostgreSQL: empty table false; complete widened-grain data true; data collapsed by the six-column key false; one position row missing for one (ayanamsha, varga) false; rows for another chart only false; the migration applies once and refuses a second run (pre-check on the base md5). `ga_writers/__tests__/test_ga_vargas_f_a2_integrity_clause.py` (behaviour part opt-in via `F_A2_PG_DSN`, disposable DB only).

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
5. Whether `pgcrypto`'s `digest` is in `public` on production (the status gate and 1035 call it unqualified under a `public` search path; the executor qualifies `public.digest` and would fail loudly and roll back otherwise).
6. Real behaviour of `GRANT data_plane_l1_owner` for the administrator role (the local test superuser is always a member).

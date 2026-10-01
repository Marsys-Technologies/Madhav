---
artifact: F3_MSR_FK_DROP
version: 1.1
status: DRAFT_FOR_REVIEW
date: 2026-10-01
lane: suvarna/land/F3-msr-fk-drop-001
decision: N-32 (F-3); Track E section 4a; SS ruling 2026-10-01
changelog:
  - "1.1 (2026-10-01): independent-review corrections: pre-merge gates, v4-id charts, silent inner-join consumers, per-site vacuity, derived dependents (ka_yojaka), L2-key prerequisite, registry blobs left alone."
  - "1.0 (2026-10-01): migration 1214 (five kala keys), the dangling-reference detector, the rebuild-order guard, the F3.PROOF on a disposable Postgres, and the owner-path plan for the three L2 keys."
---

# F-3: drop the foreign keys from kala_* into bodha_msr_signals

## 1. The keys (measured read-only as `suvarna_reader`, 2026-10-01)

Eight foreign keys reference `bodha_msr_signals(signal_id)`, all `ON DELETE CASCADE` (`confdeltype = 'c'`), none deferrable, all validated.

| Key | Table | Owner | Created by | Handled by |
|---|---|---|---|---|
| kala_convergence_signal_id_fkey | kala_convergence | amjis_app | 244 (SET NULL), made CASCADE by 403 | **migration 1214** |
| kala_activation_signal_id_fkey | kala_activation | amjis_app | 246 (CASCADE), re-stated by 403 | **migration 1214** |
| kala_obstruction_signal_id_fkey | kala_obstruction | amjis_app | 245 (SET NULL), 403 | **migration 1214** |
| kala_darshana_signal_id_fkey | kala_darshana | amjis_app | 247 (SET NULL), 403 | **migration 1214** |
| kala_bhavishya_signal_id_fkey | kala_bhavishya | amjis_app | 249 (SET NULL), 403 | **migration 1214** |
| bodha_contradictions_signal_a_id_fkey | bodha_contradictions | data_plane_l2_owner | 226 (NO ACTION), 404 | owner-path (section 5) |
| bodha_contradictions_signal_b_id_fkey | bodha_contradictions | data_plane_l2_owner | 226, 404 | owner-path |
| bodha_signal_embeddings_signal_id_fkey | bodha_signal_embeddings | data_plane_l2_owner | 226, 404 | owner-path |

Eight keys on seven tables is the count SS named: five kala_* plus the three intra-L2 keys. Owners differ, so the SS rule splits the work: the five `amjis_app` keys are ALTER-only and pre-approved; the three `data_plane_l2_owner` keys are an owner-path review and are NOT in the migration. Evidence: `/Users/Dev/suvarna-evidence/F3/fk_catalog.txt`, `roles_fn.txt`.

## 2. Migration 1214

`platform/supabase/migrations/1214_f3_drop_kala_msr_signal_fks.sql`: `SET LOCAL lock_timeout = '5s'` then five `ALTER TABLE ... DROP CONSTRAINT IF EXISTS`. Nothing else. No data changes; idempotent. The number was checked free on `origin/main` and every open PR branch (1200/1201/1210 main; 1202/1203 main; 1204/1205 pravaha b6-v15; 1212/1213 claimed by TI lanes; 1211 reserved).

Locking, proven on the proof database: the DROP also locks `bodha_msr_signals`. A plain open SELECT on it held for more than 5 s makes the migration fail with `LockNotAvailable` (after exactly 5.0 s, all five drops rolled back), and `migrate.ts` has no retry, so that deploy fails for every workstream until the migration is re-run. As `amjis_app` (owner of the kala tables, not of `bodha_msr_signals`) the drop works; the same role cannot drop the L2-owned keys (`InsufficientPrivilege`), which is why those are owner-path.

**Pre-merge gates (all required):**
1. No `build_runs` in `planned`/`running`/`paused` (any chart): `msr_rebuild_order_guard.py --chart-id C` PF-1 per chart, or `SELECT count(*) FROM build_runs WHERE state IN ('planned','running','paused')` = 0.
2. An idle deploy window: no other deploy, no migration in flight.
3. No long reads on `bodha_msr_signals`: `SELECT pid, now()-query_start FROM pg_stat_activity WHERE query ILIKE '%bodha_msr_signals%' AND state <> 'idle'` returns nothing older than a few seconds (a reader with the delay is the failure mode).
4. After deploy: the five names absent from `pg_constraint`; run the detector post-wave with `--require-nonvacuous`.

## 3. Without the key: ids, detection, and what silently changes

**Stable ids hold ONLY where ids are already deterministic.** `signal_id = uuid_generate_v5(namespace, jsonb_build_array(chart_id, ayanamsha_id, signal_type_id, varga_id, configuration_jsonb)::text)` (`bodha_signal_identity`, migration 661); all six MSR writers assign ids through it and re-grading does not move an id. Measured live (`id_versions_all_charts.txt`): canonical chart 482012f1 has 50,678 signals, all v5. **Charts 1c826d5a (50,171 signals) and cb73cd3d (49,875) are ALL uuid v4**: the first v5 regeneration of either chart changes EVERY id. After 1214, `assert_l2_msr_delete_safe` (1036:726-760) no longer refuses on Kala dependants, so that regeneration would succeed and strand 100% of that chart's Kala rows (1c826d5a: 336,093 `kala_activation` rows and the rest) with no error. Rule (plan_invariant.md): do not regenerate MSR for 1c826d5a or cb73cd3d until their Kala rows are re-keyed or the owner-path decision is made; the order guard and the pre-wave check are MANDATORY for those two charts.

**Rebuild ordering is now the only control.** The guard's second branch (refusal on Kala dependants) was the only rebuild-time protection; it finds no key after 1214. `msr_rebuild_order_guard.py` plus the detector replace it, and they are checks run around a wave, not constraints the database enforces.

**Silent consumers.** These inner-join (or EXISTS-filter) on the signal id, so a dangling Kala row simply disappears from the answer; nothing errors: `register_d8_assess_domain.ts:2062`, `L3_kala/call_service_wrappers.ts:708`, `knowledge/source_query_availability.ts:1452` and `:3425` (all `bodha_msr_signals m JOIN kala_activation`), and the EXISTS filter at `L3_kala/query_temporal_activation.ts:257`. Stale comments claiming the key guarantees existence are in migration 670 (lines 703, 858, 876); 670 is applied and is NOT edited.

**Detector** `platform/scripts/governance/msr_dangling_signal_refs.py` (read-only SELECTs; `--self-test` DB-free):
- per chart and site: rows referencing, `dangling` (signal absent), `cross_chart`, `unattributable` (the row's own `chart_id` is NULL but it references a live signal; the SQL uses `IS DISTINCT FROM` and an explicit NULL branch); NULL references are not references;
- tiers `fk_dropped` (the five kala tables; broken rows FAIL), `l2_internal`, `unconstrained` (`kala_activation_predicates`, `phala_anchors`; advisory, `--strict` fails them); an unknown `--tiers` value exits 2;
- vacuity is judged PER SITE: a scanned site with zero referencing rows proves nothing. Default exit 3 INCONCLUSIVE; `--require-nonvacuous` exits 1 (the post-wave step uses it); `--allow-vacuous` passes. An unreadable site exits 2;
- **limit:** a DELETED referencing row leaves no trace in its table, so this detector cannot see it (that is what the old CASCADE did). That is PF-2: the before-state row counts and digests of the wave plan.
Live baseline (`live_detector_*.txt`, `live_round2.txt`): `fk_dropped` sites on 1c826d5a and cb73cd3d: 0 dangling over 359k rows; the canonical chart has zero Kala rows (every `fk_dropped` site VACUOUS, exit 3). `kala_activation_predicates`, never keyed, shows 79 dangling on the canonical chart and 49,730 of 49,875 on cb73cd3d.

**Order guard dependents are derived, not hand-listed.** `msr_signal_bearing_tables.json` maps every table holding MSR signal ids (live catalog, 21 columns) to the assets that write it; tests re-check the columns against the migrations and the assets against the writers' `INSERT INTO`, and `--verify-map` re-reads the catalog (live: 18 columns, none missing). It adds `ka_yojaka` (`kala_activation_predicates`) and `ph_nimitta` (`phala_anchors`) to the five Kala assets, the L2 consumers (`bo_karanajala`, `bo_bimba`, `bo_samskara`, `bo_sangati`, `bo_cdlm_summary`, `bo_pratijna`) and the Phala assets reached through `kala_convergence`.

**Registry wiring: not done.** The `integrity_check_sql` blobs are not edited (editing them moves the Nirmana-pinned fingerprint); the detector stays a post-wave check. `ka_kalasutra`'s check already covers `kala_activation` (670, clause (e) at line 876).

## 4. F3.PROOF (disposable Postgres 15, local, loopback, throwaway cluster, deleted afterwards)

Run: `F3_DISPOSABLE_DATABASE_URL=postgresql://postgres@127.0.0.1:<port>/f3_msr_fk_test pytest platform/scripts/governance/__tests__/test_f3_msr_fk_drop.py` (skips without the env var; refuses any URL that is not explicit loopback host:port and database exactly `f3_msr_fk_test`). Schema: the real `bodha_signal_identity` (migration 661) and the real `assert_l2_msr_delete_safe` (migration 1036) extracted from the migration files; kala tables owned by `amjis_app`, L2 tables and `bodha_msr_signals` by `data_plane_l2_owner`; the migration is applied as `amjis_app`. Outcome (`proof_outcome.txt`):
- BEFORE: an unguarded MSR replace for the chart takes every kala_* table from 4 rows to 0 (the I-6 bug reproduced); the other chart is untouched. The admitted guard with the keys present refuses ("cross-layer dependent rows").
- AFTER: the admitted guard passes; regenerating with the same logic gives identical ids and all 20 kala rows intact; detector 20 referencing, 0 dangling.
- Changed + removed signals: ids kept 2, disappeared 2, new 1; predicted orphans 10 = detected dangling 10 (exact; pre-delete impact upper bound 20); a downstream re-point restores a clean detector; a reference into another chart's signal is flagged `cross_chart`.
- The three L2 keys still cascade after 1214 (embeddings and contradictions go to 0 on regeneration; the L2 writers rebuild them): this is the owner-path half.
- Guard: refuses an unadmitted delete in 8 situations (no context; full context but not `data_plane_builder`; wrong chart/build/partition/generation/asset; generation not `building`), before and after the migration.

## 5. assert_l2_msr_delete_safe, and the owner path

The function is `SECURITY DEFINER`, owned by `data_plane_l2_owner`, with an attested digest (`l2_data_plane_function_attestations`, immutable trigger), so it is NOT touched by 1214. Its first branch (admitted asset context: `session_user = data_plane_builder`, matching chart/asset/generation/partition/build, generation `building`) is unchanged and tested. Its second branch is catalogue-driven: it refuses when a row depends on the replacement scope through any non-L2 key. After 1214 it finds no kala key, so it stops refusing on Kala dependants; it re-arms (refuses again) if any cross-layer key is ever re-added. Track E 4a asks to also remove that re-arm and record counts: that needs `CREATE OR REPLACE` plus a new attestation, an owner-path change; recommendation: leave it (the re-arm is a safety net, the detector gives the orphan report). Open question Q2.

Owner-path plan for the three L2 keys (D6 in-process pattern, `exec/reader_grants/reader_grants.py`): in one transaction, administrator password from Secret Manager inside the process; `SET LOCAL ROLE data_plane_l2_owner` (add the membership transiently only if missing, remove it before commit); `ALTER TABLE public.bodha_contradictions DROP CONSTRAINT IF EXISTS bodha_contradictions_signal_a_id_fkey, DROP CONSTRAINT IF EXISTS bodha_contradictions_signal_b_id_fkey; ALTER TABLE public.bodha_signal_embeddings DROP CONSTRAINT IF EXISTS bodha_signal_embeddings_signal_id_fkey;` under `SET LOCAL lock_timeout = '5s'`; commit only if the before/after `pg_constraint` diff is exactly those three rows and the plan hash matches (`--dry-run` rolls back). The F3.FK target `no_fk` (zero keys of any kind) is met only after this step.

**PREREQUISITE (reviewer caveat; do NOT run this step until it is met).** The earlier note "the keys are redundant because the L2 writers delete their own children" is NOT established. `_idempotency.py:116,191` scopes the explicit child deletes by `pg_temp.bodha_msr_signals`, which `bind_l2_exact_inputs` (1036) builds as a SNAPSHOT of the rows captured for the L2 generations in the dependency vector, while the MSR delete runs on `public.bodha_msr_signals` (the guard's `l2_data_plane_msr_delete_receipt` holds the live scope). A root writer such as `bo_laksana` binds an L1-only vector (`data_plane_contracts.py:410-411` requires an L1 entry, no L2 entry), so its snapshot is empty and its explicit child deletes remove nothing: today the FK cascade removes the embeddings and contradictions. Proved on the disposable Postgres with the real `replace_prior_msr_signals` (three cases): keys present + empty snapshot -> 0 dangling; keys dropped + empty snapshot -> 5 dangling (4 embeddings, 1 contradiction); keys dropped + snapshot equal to the live scope -> 0. So dropping the three keys is safe only after the child-delete scope is made equal to the live delete scope in admitted context, e.g. by scoping the child deletes with the guard's receipt (a writer change, which moves the writer digests and needs its own review) or by proving the snapshot equal for every MSR writer. Until then the three keys stay.

Not edited: the stale "every FK is ON DELETE CASCADE / closure crosses layers" comments in `bodha_writers/_idempotency.py` (editing a writer file moves its code digest and the Nirmana digest inventory); correct them with the next writer change.

## 6. Open questions for SS
1. Owner-path drop of the three L2 keys: blocked by the section 5 prerequisite; who owns the writer change (child deletes scoped by the guard's receipt) and the administrator step?
2. (Decided, see SS decisions below: keep `assert_l2_msr_delete_safe` unchanged.) With the Kala keys gone it protects nothing for Kala; ordering is the control.
3. Charts 1c826d5a and cb73cd3d (all v4 ids): re-key their Kala rows, or freeze MSR regeneration for them?
4. Placement: the migration is in `supabase/migrations` (active directory); Suvarna 1210 went to `platform/migrations`.

## SS decisions (2026-10-01)

1. **The three L2 keys owned by `data_plane_l2_owner`** (`bodha_contradictions_signal_{a,b}_id_fkey`, `bodha_signal_embeddings_signal_id_fkey`): go in ONE REVIEW together with the phala/mimamsa builder grants (same D6 in-process executor, run after SS's `APPROVED <plan hash>`); the plan includes a read-only check that `data-plane-ownership-status.ts` / the deploy preflights do not pin those constraints (if they do, the gate amendment goes first). Tracked in `BUILDER_GRANT_PLAN` v1.1.
2. **`assert_l2_msr_delete_safe` is kept as is. Track E §4a's "remove the re-arm" is DECLINED**, with the reason: the function's catalogue-driven refusal re-arms only if a cross-layer foreign key into `bodha_msr_signals` is re-added, which is exactly the right fail-safe; removing it would make a re-added key silent again.
3. **The dangling-reference detector** (`msr_dangling_signal_refs.py`) runs as a **post-wave check**; wiring it into the five Kāla `integrity_check_sql` blobs waits until there is a green baseline on the canonical chart.
4. **The plan invariant (MSR writers strictly before the Kāla and Phala assets, none rebuilt later in the same window) stays in force until BOTH migration 1214 AND the L2 owner-path drop are deployed**, because embeddings and contradictions still cascade until the owner-path drop runs.

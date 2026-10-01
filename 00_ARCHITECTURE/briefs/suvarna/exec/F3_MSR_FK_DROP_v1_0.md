---
artifact: F3_MSR_FK_DROP
version: 1.0
status: DRAFT_FOR_REVIEW
date: 2026-10-01
lane: suvarna/land/F3-msr-fk-drop-001
decision: N-32 (F-3); Track E section 4a; SS ruling 2026-10-01
changelog:
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

Locking, proven on the proof database: the DROP also takes a lock on `bodha_msr_signals` (a reader holding a lock on it makes the migration fail with `LockNotAvailable` after exactly 5.0 s, rolling all five drops back). So it fails loudly instead of queueing; run it when no MSR writer or long reader is active. As `amjis_app` (owner of the kala tables, not of `bodha_msr_signals`) the drop works; the same role cannot drop the L2-owned keys (`InsufficientPrivilege`), which is why those are owner-path.

## 3. Without the key: stable ids and detection

**Stable ids (references survive a regeneration).** `signal_id = uuid_generate_v5(namespace, jsonb_build_array(chart_id, ayanamsha_id, signal_type_id, varga_id, configuration_jsonb)::text)` (`bodha_signal_identity`, migration 661). All six MSR writers (`bo_laksana`, `bo_arudha`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`, `bo_nakshatra_semantic`) assign ids through it; no uuid4 remains. Re-grading a signal (salience, tier, scores) does not move its id; an unchanged signal regenerates to the same id (proved: same ids before/after, section 4). All 50,678 live canonical-chart ids are version-5 uuids. Existing writer tests: 48 pass (`test_bo_*_signal_identity.py`, `test_bo_shared_msr_signal_identity.py`, `test_l2_data_plane_contracts.py`).

**Changed or removed signals are detected, not prevented.** A signal whose configuration (including a fact value), varga, type or ayanamsha changed IS a different signal and takes a new id; a removed signal's id disappears. Detector: `platform/scripts/governance/msr_dangling_signal_refs.py` (read-only SELECTs, `--self-test` DB-free, live mode via `DATABASE_URL`):
- per chart, per referencing site: rows referencing, `dangling` (signal absent), `cross_chart` (signal of another chart); NULL references are not references;
- tiers: `fk_dropped` (the five kala tables; broken rows FAIL), `l2_internal` (the three L2 keys), `unconstrained` (`kala_activation_predicates`, `phala_anchors`, never keyed; advisory, `--strict` fails them);
- a clean result over zero referencing rows is reported VACUOUS, and a site the role cannot read makes the run exit 2, never a silent pass (N.8);
- `would_orphan_sql` gives the pre-delete impact for a replacement scope (what `assert_l2_msr_delete_safe` locks), an upper bound on what a regeneration can orphan.

Live baseline (read-only, 2026-10-01; `live_detector_*.txt`): `fk_dropped` sites on charts 1c826d5a and cb73cd3d: 0 dangling over 359k referencing rows; canonical chart 482012f1: zero referencing rows (erased by the 2026-09-08 cascade, so this is vacuous there). The unconstrained table `kala_activation_predicates` shows what the missing key permits: 79 dangling on the canonical chart and 49,730 of 49,875 on cb73cd3d.

**Wiring (open question for SS).** The five Kala assets already carry `integrity_check_sql` (4.4-5.7 KB each, chart-partitioned). Adding a dangling-reference conjunct is a registry UPDATE of those blobs (and moves the registry fingerprint the Nirmana-frozen manifests pin). I did not do it: it is large, and a gate that has never been green on the canonical chart (zero rows) is a proposal, not a gate. The detector is delivered as a helper + tests; the registry wiring is a follow-up.

## 4. F3.PROOF (disposable Postgres 15, local, loopback, throwaway cluster, deleted afterwards)

Run: `F3_DISPOSABLE_DATABASE_URL=postgresql://postgres@127.0.0.1:<port>/f3_msr_fk_test pytest platform/scripts/governance/__tests__/test_f3_msr_fk_drop.py` (skips without the env var; refuses any URL that is not explicit loopback host:port and database exactly `f3_msr_fk_test`). Schema: the real `bodha_signal_identity` (migration 661) and the real `assert_l2_msr_delete_safe` (migration 1036) extracted from the migration files; kala tables owned by `amjis_app`, L2 tables and `bodha_msr_signals` by `data_plane_l2_owner`; the migration is applied as `amjis_app`. Outcome (`proof_outcome.txt`):
- BEFORE: an unguarded MSR replace for the chart takes every kala_* table from 4 rows to 0 (the I-6 bug reproduced); the other chart is untouched. The admitted guard with the keys present refuses ("cross-layer dependent rows").
- AFTER: the admitted guard passes; regenerating with the same logic gives identical ids and all 20 kala rows intact; detector 20 referencing, 0 dangling.
- Changed + removed signals: ids kept 2, disappeared 2, new 1; predicted orphans 10 = detected dangling 10 (exact; pre-delete impact upper bound 20); a downstream re-point restores a clean detector; a reference into another chart's signal is flagged `cross_chart`.
- The three L2 keys still cascade after 1214 (embeddings and contradictions go to 0 on regeneration; the L2 writers rebuild them): this is the owner-path half.
- Guard: refuses an unadmitted delete in 8 situations (no context; full context but not `data_plane_builder`; wrong chart/build/partition/generation/asset; generation not `building`), before and after the migration.

## 5. assert_l2_msr_delete_safe, and the owner path

The function is `SECURITY DEFINER`, owned by `data_plane_l2_owner`, with an attested digest (`l2_data_plane_function_attestations`, immutable trigger), so it is NOT touched by 1214. Its first branch (admitted asset context: `session_user = data_plane_builder`, matching chart/asset/generation/partition/build, generation `building`) is unchanged and tested. Its second branch is catalogue-driven: it refuses when a row depends on the replacement scope through any non-L2 key. After 1214 it finds no kala key, so it stops refusing on Kala dependants; it re-arms (refuses again) if any cross-layer key is ever re-added. Track E 4a asks to also remove that re-arm and record counts: that needs `CREATE OR REPLACE` plus a new attestation, an owner-path change; recommendation: leave it (the re-arm is a safety net, the detector gives the orphan report). Open question Q2.

Owner-path plan for the three L2 keys (D6 in-process pattern, `exec/reader_grants/reader_grants.py`): in one transaction, administrator password from Secret Manager inside the process; `SET LOCAL ROLE data_plane_l2_owner` (add the membership transiently only if missing, remove it before commit); `ALTER TABLE public.bodha_contradictions DROP CONSTRAINT IF EXISTS bodha_contradictions_signal_a_id_fkey, DROP CONSTRAINT IF EXISTS bodha_contradictions_signal_b_id_fkey; ALTER TABLE public.bodha_signal_embeddings DROP CONSTRAINT IF EXISTS bodha_signal_embeddings_signal_id_fkey;` under `SET LOCAL lock_timeout = '5s'`; commit only if the before/after `pg_constraint` diff is exactly those three rows and the plan hash matches (`--dry-run` rolls back). Safe functionally: the L2 writers already delete their own embeddings and contradictions explicitly before the MSR delete (`_idempotency.py`), so the keys are redundant there. The F3.FK detector target `no_fk` (zero keys of any kind) is met only after this step.

Not edited: the stale "every FK is ON DELETE CASCADE / closure crosses layers" comments in `bodha_writers/_idempotency.py` (editing a writer file moves its code digest and the Nirmana digest inventory); correct them with the next writer change.

## 6. Open questions for SS
1. Run the owner-path for the three L2 keys (and who holds the administrator step)?
2. Keep `assert_l2_msr_delete_safe` unchanged (recommended) or replace it without the re-arm (owner-path + re-attestation)?
3. Wire `msr_dangling_signal_refs` into the five Kala assets' `integrity_check_sql` (registry migration), or keep it a post-wave check run by the wave runner?
4. Which migration directory: placed in `supabase/migrations` (active directory per its README); the Suvarna 1210 went to `platform/migrations`.

## SS decisions (2026-10-01)

1. **The three L2 keys owned by `data_plane_l2_owner`** (`bodha_contradictions_signal_{a,b}_id_fkey`, `bodha_signal_embeddings_signal_id_fkey`): go in ONE REVIEW together with the phala/mimamsa builder grants (same D6 in-process executor, run after SS's `APPROVED <plan hash>`); the plan includes a read-only check that `data-plane-ownership-status.ts` / the deploy preflights do not pin those constraints (if they do, the gate amendment goes first). Tracked in `BUILDER_GRANT_PLAN` v1.1.
2. **`assert_l2_msr_delete_safe` is kept as is. Track E §4a's "remove the re-arm" is DECLINED**, with the reason: the function's catalogue-driven refusal re-arms only if a cross-layer foreign key into `bodha_msr_signals` is re-added, which is exactly the right fail-safe; removing it would make a re-added key silent again.
3. **The dangling-reference detector** (`msr_dangling_signal_refs.py`) runs as a **post-wave check**; wiring it into the five Kāla `integrity_check_sql` blobs waits until there is a green baseline on the canonical chart.
4. **The plan invariant (MSR writers strictly before the Kāla and Phala assets, none rebuilt later in the same window) stays in force until BOTH migration 1214 AND the L2 owner-path drop are deployed**, because embeddings and contradictions still cascade until the owner-path drop runs.

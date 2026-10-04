---
artifact: V5_SMALLTEST_TEARDOWN_RUNBOOK
version: "1.0"
status: DRAFT for steward review — nothing in it has been executed against any database
date: 2026-10-04
author: Stream A (Exec A), answering Codex round 2 on PR 3098 (steward TEARDOWN-CODEX-2)
scope: How the small-test teardown (`platform/scripts/teardown_v5_small_test_job.py`) is run, when it refuses and what the steward does then, and which database role it needs.
changelog:
  - "1.0 (2026-10-04): first version."
---

# V5 small test — teardown runbook

## 1. Run it within 90 days of the small test
The cockpit watchdog deletes terminal build runs (completed, failed, stopped) 90 days after their creation (`platform/src/app/api/cockpit/watchdog/route.ts`, "M-4"). `asset_provenance_receipts.build_id` is `ON DELETE SET NULL`, so the small test's receipts then carry no run link. The teardown **refuses a receipt with no run link, for good** (a pruned test run and a pruned real run look the same; the Nirmana monitor's rule N-137 reads such a receipt as non-test evidence too). So the clock is: **creation time of the small-test run + 90 days.** The dry run prints each owned run's creation time and the days remaining; the dispatch prints the same deadline when it stages the run. Tear down well inside it.

## 2. The usual sequence
1. Dry run (the default; it runs every statement an execution runs, then rolls back, zero commits): `DATABASE_URL=... python3 scripts/teardown_v5_small_test_job.py`. Read the counts and the retention lines.
2. Execute only on steward go: add `--execute --i-am-steward`.
3. Afterwards: the registry row is inert (`is_active = false`, migration-1304 shape), the Nirmana monitor's N-137 end state holds (checked again by the script before it claims success), and nothing of the test remains for the pinned chart and generation `5.0`.

## 3. When it refuses because receipts have no run link (recovery)
**The rule is not weakened and the script is not patched around.** The recovery is a steward procedure that restores a link only from evidence that does not depend on the rows being questioned.

1. **Stop.** Delete nothing. Record the receipts' partition keys and `observed_at` from the refusal message and from `SELECT partition_key, observed_at FROM asset_provenance_receipts WHERE asset_id = 'ka_gochara_v5' AND chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND build_id IS NULL`.
2. **Establish the origin from independent evidence**, and record each item in the tracker or a decision file before going on:
   - the dispatch's own output: the run id it printed and the manifest digest, kept in the tracker report for that dispatch;
   - the Cloud Run job executions of `brahma-build-pipeline-job` for that run id (`--args=--run-id,<id>`): there must be exactly the executions the steward started, inside the window;
   - the current manifest's slice stamp (its marker digest) equal to the dispatch's plan, and the stored snapshot and inventory headers carrying the stamped manifest's vector (the dry run checks this for the output);
   - each receipt's `observed_at` inside an execution's window, and no other v5 execution for that chart in the period.
3. **If the run row still exists** (the watchdog has not reached it): restore the link, in one transaction run by the steward: `UPDATE asset_provenance_receipts SET build_id = '<run id>' WHERE asset_id = 'ka_gochara_v5' AND chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND partition_key IN (<the recorded keys>) AND build_id IS NULL`. Then re-run the teardown.
4. **If the run row was pruned** (the usual case after 90 days): a link cannot be restored to a row that no longer exists, and a placeholder run row is never fabricated. If, and only if, step 2 proves the receipts are the small test's, the steward records that proof in `00_ARCHITECTURE/briefs/pravaha/decisions/` and authorises ONE explicit deletion of exactly those receipts by key: first the `SELECT` that shows them, then `DELETE FROM asset_provenance_receipts WHERE asset_id = 'ka_gochara_v5' AND chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND partition_key IN (<the recorded keys>) AND build_id IS NULL`, then check the row count equals the recorded count. Then re-run the teardown. If step 2 cannot prove it, the receipts stay and the asset stays out of the monitor's excluded set until the steward decides otherwise.

## 4. Which role the script runs as
It runs as ONE database role and does not assume the admin role. From the migrations (production ACLs were not read; the Gochara hold stands), the privileges it needs:

| Object (schema `public`) | Privilege |
|---|---|
| `asset_provenance_receipts`, `asset_freshness`, `build_run_assets`, `build_runs`, `asset_throughput` | SELECT, DELETE |
| `ka_gochara_eval_window`, `ka_gochara_relationship_record`, `ka_gochara_contact`, `kala_gochara_coverage`, `ka_gochara_search_interval`, `ka_gochara_search_obligation`, `ka_gochara_search_path_pin`, `ka_gochara_search_inventory`, `ka_gochara_search_input_snapshot`, `kala_gochara_publication` | SELECT, DELETE |
| `ka_gochara_generation_seal`, `kala_gochara_authority`, `kala_gochara_windows`, `kala_gochara_contacts` | SELECT |
| `asset_registry` | SELECT, UPDATE (`is_active`) |
| `ka_gochara_lock_chart(uuid)` | EXECUTE |
| the two verification tables (`ka_gochara_eval_window_verification`, `ka_gochara_search_inventory_verification`) | none: removed by foreign-key cascade (the cascade runs as the child's owner; the 1240 write guard on them refuses only a sealed generation) |

What each candidate holds, by the migrations:
- **`data_plane_builder`** (the builder): lacks DELETE on `asset_provenance_receipts` (1070), `asset_freshness` (1217 states no DELETE and fails on apply if it is granted), `kala_gochara_publication` (1216 grants SELECT, INSERT, UPDATE); holds **no grant at all** in any migration on `build_runs`, `build_run_assets`, `asset_throughput`, `kala_gochara_authority`; lacks UPDATE (`is_active`) on `asset_registry` (column-level UPDATE only on health columns, 1070). It has the chain, inventory and snapshot DELETEs and EXECUTE on the lock.
- **`gochara_verifier`, `gochara_sealer`**: read-mostly; no DELETE on any parent table.
- **`role_orchestrator`**: full DML on the pre-576 orchestrator tables (`asset_registry`, `build_runs`, `build_run_assets`, `asset_throughput`) but nothing on `asset_freshness`, `asset_provenance_receipts`, the `ka_gochara_*` tables, `kala_gochara_publication`, and no EXECUTE on the lock.
- **`amjis_app`** (the application's owner role, not the admin role): owns every object above, so it holds every privilege implicitly, including EXECUTE on the lock; no REVOKE against it was found. It is the only existing role that holds all of them.

**Recommendation:** run as `amjis_app` for the one-off small-test teardown, because no narrower role exists today and creating one is a grant change that belongs in a protected migration window; if the steward prefers least privilege, a dedicated `gochara_teardown` role with exactly the table above is the follow-up (its own migration and review, including the open decision about the builder's `asset_freshness` DELETE that 1217 forbids). Whether production's ACLs match the migrations is **not shown**.

## 5. What the dry run proves, and what it does not
It proves the locks can be taken, every refusal check passes, every DELETE is accepted by the real foreign keys and guards, the registry row restores to its 1304 shape, and the N-137 end state holds afterwards — all in the transaction an execution would commit, then rolled back. It does not prove anything about a COMMIT failing, or about another session writing between the dry run and the execution (run the execution under the same locks, soon after).

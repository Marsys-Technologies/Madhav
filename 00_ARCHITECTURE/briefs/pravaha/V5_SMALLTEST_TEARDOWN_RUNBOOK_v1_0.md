---
artifact: V5_SMALLTEST_TEARDOWN_RUNBOOK
version: "1.1"
status: DRAFT for steward review — nothing in it has been executed against any database
date: 2026-10-04
author: Stream A (Exec A), answering Codex rounds 2 and 3 and Stream B on PR 3098 (steward TEARDOWN-CODEX-2, TEARDOWN-B-ADD)
scope: How the small-test teardown (`platform/scripts/teardown_v5_small_test_job.py`) is run, when it refuses and what the steward does then, and which database role it needs.
changelog:
  - "1.1 (2026-10-04): Stream B additions: direct connection required (B6), what the locks do not do (B7), the recovery conditions for NULL links (B9), the role section with Stream B's production verification and the conditional registry privileges (B1, B2), the catalog-discovered references (B4, B5)."
  - "1.0 (2026-10-04): first version."
---

# V5 small test — teardown runbook

## 1. Run it within 90 days of the small test
The cockpit watchdog deletes terminal build runs (completed, failed, stopped) 90 days after their creation (`platform/src/app/api/cockpit/watchdog/route.ts`, "M-4"). `asset_provenance_receipts.build_id` is `ON DELETE SET NULL`, so the small test's receipts then carry no run link. The teardown **refuses a receipt with no run link, for good** (a pruned test run and a pruned real run look the same; the Nirmana monitor's rule N-137 reads such a receipt as non-test evidence too). So the clock is: **creation time of the small-test run + 90 days.** The dry run prints each owned run's creation time and the days remaining; the dispatch prints the same deadline when it stages the run. Tear down well inside it.

## 2. Connect DIRECTLY, then run the usual sequence
**Use a DIRECT connection to the database's own host and port. Never a pooler** (PgBouncer or any transaction-mode pooler). The orchestrator exclusion lock is a SESSION advisory lock; through a transaction-mode pooler it silently holds nothing, and the script's other protections lean on it. The script reads `pg_backend_pid()` in three separate transactions and refuses if the backend changes, and checks that the lock is held by the backend running the transaction; that catches a busy pooler but cannot prove a quiet one is absent, so the direct connection is a requirement of this runbook, not only of the code.

1. Dry run (the default; it runs every statement an execution runs, then rolls back, zero commits): `DATABASE_URL=... python3 scripts/teardown_v5_small_test_job.py`. Read the counts and the retention lines.
2. Execute only on steward go: add `--execute --i-am-steward`.
3. Afterwards: the registry row is inert (`is_active = false`, migration-1304 shape), the Nirmana monitor's N-137 end state holds (checked again by the script before it claims success), and nothing of the test remains for the pinned chart and generation `5.0`.
4. If a run ends with "COMMIT OUTCOME UNKNOWN": do not retry blindly. Run the dry run: it lists what remains. Nothing remaining and a clean N-137 check means the commit landed.

### What the locks do and do not do
The advisory lock excludes **orchestrator build runs** (`runner.acquire_chart_lock`); the Gochara chart lock excludes **Gochara writers**. Neither excludes the **cockpit watchdog**, which takes no advisory lock and may prune terminal runs at any moment. The script's reads and DELETEs are by id inside one transaction, so a run pruned in between can only make a receipt it had already proven lose its link, and the same transaction deletes it as proven.

## 3. When it refuses because receipts have no run link (recovery) — **NOT FOR USE until reviewed**
**This section is NOT FOR USE until a reviewer has accepted it; it is not needed for a timely teardown (section 1), and nobody should reach for it before the 90 days are up.** It is written down so that the rule is not silently worked around, and so the review has something concrete to review.

**The rule is not weakened and the script is not patched around.** The recovery is a steward-run, logged procedure that restores a link only from evidence that does not depend on the rows being questioned, and only for the exact receipt version whose origin was proved.

1. **Stop.** Delete nothing. Record, for each receipt, its full identity from the refusal message and from `SELECT partition_key, observed_at, code_digest, config_digest, upstream_digest, partition_digest, output_digest, receipt_version FROM asset_provenance_receipts WHERE asset_id = 'ka_gochara_v5' AND chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND build_id IS NULL`. **A receipt can be REPLACED under the same key** (the provenance writer upserts on `(asset_id, scope_key, partition_key)`), so a key alone proves nothing: the recorded identity is `observed_at` plus all five digests plus `receipt_version`.
2. **A link may be restored for a receipt only if ALL THREE hold, each recorded in a decision file under `00_ARCHITECTURE/briefs/pravaha/decisions/` before anything is changed:**
   - **the window:** the receipt's `observed_at` lies inside the recorded dispatch window — the Cloud Run job execution of `brahma-build-pipeline-job` for the run id the dispatch printed (`--args=--run-id,<id>`), whose start and end times and the dispatch output are kept in the tracker;
   - **the digests:** the receipt's `code_digest` and `config_digest` equal the ones the stamped manifest pinned (the manifest's input vector carries the implementation and configuration identities the writer pinned; the dry run already proves the manifest's stamp, snapshot and inventory identities);
   - **nobody else:** no other run touched the asset in that window — no other `build_run_assets` row or Cloud Run execution for `ka_gochara_v5` inside it, on any chart.
3. **The change itself runs in ONE transaction, under the same locks the teardown takes** (the orchestrator's `pg_try_advisory_lock(hashtext(<chart>))` on a direct connection, then `ka_gochara_lock_chart`), and **re-validates the full receipt identity inside that transaction and must roll back on any mismatch**:
   - If the run row still exists: `UPDATE asset_provenance_receipts SET build_id = '<run id>' WHERE asset_id = 'ka_gochara_v5' AND chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND partition_key = '<key>' AND build_id IS NULL AND observed_at = '<recorded>' AND code_digest = '<recorded>' AND config_digest = '<recorded>' AND upstream_digest = '<recorded>' AND partition_digest = '<recorded>' AND output_digest = '<recorded>' AND receipt_version = '<recorded>'`, one statement per receipt, then check the total updated row count equals the number of recorded receipts; **if it does not, ROLLBACK** (a receipt was replaced or already re-linked since the proof) and start again from step 1.
   - If the run row was pruned (the usual case after 90 days): a link cannot be restored to a row that no longer exists, and a placeholder run row is never fabricated. If, and only if, all three conditions hold, the steward authorises ONE deletion of exactly those receipts, in the same shape: `DELETE FROM asset_provenance_receipts WHERE <the same full-identity predicate>` per receipt, row count checked against the record, `ROLLBACK` on any mismatch.
4. Then re-run the dry run, and only then the execution. If any condition cannot be shown, the receipts stay and the asset stays out of the monitor's excluded set until the steward decides otherwise.

## 4. Which role the script runs as
**The role choice is the owner's; this runbook changes no grant.** The script runs as ONE database role and never assumes the admin role. `REQUIRED_PRIVILEGES` in the script is the machine-readable list (a real-database test runs the script as a role holding exactly it, and shows a missing grant fails the dry run). From the migrations, and verified read-only on production by Stream B:

| Object (schema `public`) | Privilege |
|---|---|
| `asset_provenance_receipts`, `asset_freshness`, `build_run_assets`, `build_runs`, `asset_throughput` | SELECT, DELETE |
| `ka_gochara_eval_window`, `ka_gochara_relationship_record`, `ka_gochara_contact`, `kala_gochara_coverage`, `ka_gochara_search_interval`, `ka_gochara_search_obligation`, `ka_gochara_search_path_pin`, `ka_gochara_search_inventory`, `ka_gochara_search_input_snapshot`, `kala_gochara_publication` | SELECT, DELETE |
| `ka_gochara_generation_seal`, `kala_gochara_authority`, `kala_gochara_windows`, `kala_gochara_contacts` | SELECT |
| `asset_registry` | SELECT always; UPDATE(`is_active`) **only if the row is found active** — an already-inert row is not updated (production's is inert) |
| `asset_freshness` (additionally, **only if the registry row is found active**) | SELECT and UPDATE: the registry restore is a real `is_active` change, so migration 596's trigger runs `nirmana_invalidate_registry_receipts`, an **invoker-rights** function (not SECURITY DEFINER) that UPDATEs `asset_freshness` as the caller. With the row already inert (production's is) the script does not issue the UPDATE and none of this applies |
| every table the catalog shows referencing an owned `build_runs` row or the manifest (conversations, the prediction and calibration ledgers, ...) | SELECT, to count the rows that reference them (the script refuses by name if any do) |
| `ka_gochara_lock_chart(uuid)` and `ka_gochara_generation_is_sealed(uuid, text)` (the DELETE guards on the chain tables call it as the invoker; a real-database test with PUBLIC EXECUTE revoked, as production has it, found it missing from the first draft of this table) | EXECUTE |
| the two verification tables (`ka_gochara_eval_window_verification`, `ka_gochara_search_inventory_verification`) | none: removed by foreign-key cascade (the cascade runs as the child's owner; the 1240 write guard on them refuses only a sealed generation) |

What each candidate holds:
- **`amjis_app`** (the application's owner role, not the admin role): owns every object above, so it holds every privilege implicitly, including EXECUTE on the lock. **It is the only existing role that holds all of them** (Stream B, verified on production).
- **`data_plane_builder`** (the builder) is four short: DELETE on `asset_freshness` (migration 1217 states no DELETE and fails on apply if it is granted), DELETE on `asset_provenance_receipts`, DELETE on `kala_gochara_publication`, and UPDATE on `asset_registry` (its column grant excludes `is_active`; needed only when the row is active). By the migrations it also has no grant on `build_runs`, `build_run_assets`, `asset_throughput` or `kala_gochara_authority`.
- **`gochara_verifier`, `gochara_sealer`**: read-mostly; no DELETE on any parent table. **`role_orchestrator`**: the pre-576 orchestrator tables only.

Recommendation, for the owner: `amjis_app` for the one-off teardown, because no narrower role exists today and creating one is a grant change that belongs in a protected migration window; if least privilege is preferred, a dedicated `gochara_teardown` role with exactly the table above is the follow-up (its own migration and review, including the open decision about the builder's `asset_freshness` DELETE that 1217 forbids).

## 5. What the dry run proves, and what it does not
It proves the locks can be taken (on a direct connection), every refusal check passes, every DELETE is accepted by the real foreign keys, guards and **privileges of the role it ran as**, the registry row ends in its 1304 shape, and the N-137 end state holds afterwards — all in the transaction an execution would commit, then rolled back. It does not prove anything about a COMMIT failing, or about another session writing between the dry run and the execution (run the execution soon after, on the same locks).

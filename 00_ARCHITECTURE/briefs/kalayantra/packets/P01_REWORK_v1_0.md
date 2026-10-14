---
artifact: P01_REWORK
version: "1.0"
status: REVIEW_CANDIDATE
produced_on: 2026-10-15
changelog:
  - "1.0: P01-B1 settlement caller regressions; P01-B2 executable bindings, measured teardown absence, paired logical backup/restore, explicit residual scope and CI coverage."
---

# Wave 4 P01 — packet-review correction

This is a code/inheritance disposition for independent review, not child acceptance or operational evidence. The cockpit job explicitly authorises this rework's local script/table/model changes; the older scratch-only J-1a readiness packet is retained as information. No executor request, database connection, real operation, Git write, deployment or runtime model installation is performed.

## P01-B1 — settlement-bound callers

The provided HEAD merges reviewed prerequisite `3da0710880f26918c2f779bf0ee95e993aac4c22` as the second parent of `1550e648f54a2248110843bcddd2ae935b8bc3a1`. The real governed selector loads the receipt at `platform/python-sidecar/services/gochara_kernel/dasha_read.py:96` and rejects any sole build other than its full run at line 104. `load_pinned_vimshottari` (line 131) performs the all-build guard, raw selection and then a read pinned to the named run. The lazy P1 operand invokes it at line 165. The writer imports those readers at `platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:64` and line 85; its snapshot invokes the loader at line 921, before generation deletion.

New regressions in `platform/python-sidecar/tests/l3/gochara/test_j4p_dasha_settlement.py:232` exercise both lazy P1 refusal and the actual writer snapshot branch, including a synthetic full-UUID prefix collision; line 246 checks the settled positive control and one-time pin. They fake only external chart/context/SQL boundaries. The in-memory sole-build selector mutation causes all three negative cases to fail.

The latest local `origin/kalayantra/j-4p` is now `64bcf5068` (a separate cutover-loader all-build guard change), beyond the merged reviewed settlement head. Its kernel reader and settlement bytes equal this worktree's. No claim is made that the latest ref is an ancestor; the cockpit retains ownership of any further stack update.

## P01-B2 — six concrete operation bindings

`00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json:8` through line 13 enable only the six J-1a entries, with existing reviewed dispatch/teardown scripts and the new backup script proposed for independent review. These entries have effect only after the reviewed table lands on main and an independently accepted request passes the unchanged executor. The source-only enabled state does not certify an operation or authorise one.

Dispatch fixed arguments include `--i-am-steward --after-settled-1` and the correct `--dry-run`/`--execute` mode. Teardown preserves the chart-wide ownership guard, binds its actual script and mode, and exposes no request arguments: there is no invented `--run-id` deletion interface. Both parsers refuse abbreviations and unsupported options. The backup entries use `needs=owner`, matching the existing executor's selective URL handover (`fleet/executor.py:305`–306), and accept only a label; operation/mode are fixed.

Teardown's `_prove_absence` (`platform/scripts/teardown_v5_small_test_job.py:486`) checks measured zero counts after all deletes and before commit under the existing locks. It checks original owned run IDs without joining to deleted parents, all deleted asset/chart and chart/generation scopes, and the four cascade children. A survivor refuses success and rolls back. Its JSON carries chart/generation, original run IDs, counts and observation point; dry runs say `rehearsed_then_rolled_back`, and only a confirmed commit can emit `committed`. Independent post-operation readback still belongs to J-2d/A5.5i. The privilege inventory/runbook now require SELECT on cascade children, without changing any database grant.

Backup plans perform zero DB/program/file operations and set both earned flags to null. Real capture, when separately authorised, uses a complete custom-format logical archive and a read-only exported repeatable-read snapshot shared with the per-table measurements. Sorted row JSON is streamed into SHA-256 with length framing, including duplicate/null rows; every user relation's count/content and every sequence's state are measured. Changing sequence state during capture refuses a receipt. Unsupported foreign-table data and large objects refuse rather than silently omit coverage. Roles/grants are explicitly excluded from the logical restore claim. Archive hash, label and script identity bind the subsequent restore.

Restore creates a fresh database on the fixed loopback scratch cluster, rejects an existing target or source database name, restores with `--exit-on-error --single-transaction`, remeasures every relation and sequence, and requires complete equality. Equal counts with changed content fail. It drops only the target created by this invocation; a failed restore/equality/cleanup cannot emit verified evidence. Neither script starts/stops Docker.

## Inheritance and writable scope

The source requirements are `00_ARCHITECTURE/control/pravaha/plan_model.json:735` (A5.5f), line 746 (A5.5g), line 756 (A5.5h), and line 1323 (B5.5b). Source commits `9c1f42970` (#3132), `5d9e71279` (#3110) and `4c34647a3` (#3129) are ancestors of this HEAD. Tooling lineage is #3097 (`8d63c31b0`), #3098 (`eeba33831`) and #3101 (`f50a00091`). These are observed source facts, not substituted review or CI receipts.

The inherited G7 chain replacement source, slice source, N-137 definitions and applied migration 1304 are unchanged against the current local main ref. Non-DB chain order/candidate refusal/row conflict tests, all C46 non-DB slice cases, and dispatch/teardown N-137 refusal controls were rerun. Live replacement, role/privilege, published-head compatibility and populated teardown suites remain required CI evidence. No writer/reader implementation, applied migration, generated aggregate, G8 rule, FROZEN path or serving code changes here. The #3140 SQL draft remains byte-identical to its review pin (`e42ed26f5512e23381045b9617f7cc511ab5313a6dc1f48fcd21b325ced8a694`); its promotion/application is not part of this rework.

`00_ARCHITECTURE/control/kalayantra/plan_model.json:4519` carries the supplied J-1a-a55h child definition, with owns enumerating exactly the fourteen rework paths, explicit test obligations, and its J-1a join dependency. Branch-merge detection, independent review and required CI are preserved; no child completion event is fabricated.

## Interpretations requiring cockpit reconciliation

- **(I) INTERPRETATION P01-I1:** the placeholder's “existing backup mechanism” means the existing custom-format `pg_dump`/`pg_restore` flags (`platform/scripts/backup/export_irreplaceable_tables.sh:89`, `restore_irreplaceable_tables.sh:66`), broadened to the complete logical DB for conservative side-effect/sequence/schema coverage. This is not a Cloud SQL snapshot, role/grant recovery or production restore claim.
- **(I) INTERPRETATION P01-I2:** the scratch restore target is a newly created `ky_restore_<label>` on the fleet's existing loopback test cluster, using its fixed test settings (`fleet/local_db.sh:62`, line 338). A different scratch topology requires its own reviewed binding. No existing database is reset or reused.
- **(I) INTERPRETATION P01-I3:** this checkout's model predates the J-0m residual-child registration. Only the supplied J-1a-a55h definition, concrete owns and J-1a edge are carried; the cockpit must reconcile this delta into the accepted full J-0m model and activate it through its governed path. Other residual children/joins are not reconstructed.

## Verification and remaining evidence

Non-DB tests: **494 passed** across dispatch, teardown, new operations/backup, settlement and C46 suites; **13 passed** for inherited G7 non-DB tests; **26 passed** for the safe executor table/boundary selection. Five C46 and sixteen G7 DB cases are explicitly deselected. Twenty-eight existing executor fixture cases require Git writes and are not run in this no-Git-writes job; new tests execute the real request validator against fake transport boundaries and check that enabling a kind cannot bypass its acceptance/argument/requester/evidence gates. The existing suite's expected table state is updated without relaxing the executor implementation boundary.

Four in-memory mutation runs produce expected pytest failures: sole-build acceptance (3), zeroed absence counts (6), skipped restore comparison (4), missing dispatch execute (1). Logs and commands are retained in JOB_SCRATCH. Syntax, YAML, child/scope, source ancestry, unchanged draft hash and whitespace checks pass.

CI now collects the new operations/backup tests in DB Integration Tests, and the two real snapshot/restore tests in Kāla DB Tests (`platform/python-sidecar/tests/l3/kala_db/test_p01_smalltest_backup.py`). PostgreSQL 16 clients are installed in that job (`.github/workflows/ci.yml:323`). The real DB test covers a sequence, cross-table FK and JSON/null content, complete equality, and a same-count content mutation. Collection succeeds; execution is **deferred to CI**, alongside C37/C38, G7 populated replacement, C46 DB and published-head compatibility. The N-137 Vitest suite is also deferred to CI because this checkout has no installed Vitest; no network installation is attempted.

Remaining cockpit work: exact resulting head independently reviewed; required CI green; source/inheritance and nonempty scope disposition accepted; broader full-model reconciliation/activation; applicable scratch capability/role/source/window/image/migration/lease receipts before any operation. Actual two-run timing, teardown and independent absence/backup/restore evidence remain J-2d/A5.5i. Done for this builder job means code/tests/handoff completed, not earned operational completion.

The provided worktree and JOB_SCRATCH evidence are retained for the cockpit. Finished pytest temporary trees are removed. No test database, worktree copy or background process is created by this job.

---
artifact: J2A_SCOPED_BACKUP
version: "1.0"
status: REVIEW_CANDIDATE
produced_on: 2026-10-17
authority: surrogate ruling SR-J2A-BACKUP-SCOPE (DECISIONS_SURROGATE.jsonl, 2026-10-16T22:08Z); amends P01_REWORK_v1_0.md (paired logical backup) and the step-10 text of the small-test sitting checklist
changelog:
  - "1.0: scoped small-test backup (--scope small_test): reviewed scope file + digest, SQL-aggregate measurement, parallel directory dump, restore proof, validity window, dispatch check."
---

# J-2a step 10 — the SCOPED small-test backup (spec and runbook)

Plan item J-2a step 2 (`backup_restore_verified`; checklist row 10) needs a backup and a restore proof before the first
small-test dispatch. The full-database form failed with SQLSTATE 53400 (a server-side `ORDER BY row_to_json` over
`kala_field`, 10.3 M rows; the database is 21.9 GB / 507 tables). This document is the amendment: a second, **scoped** form.
The full form (`--scope full`, the default) is unchanged and remains available; it is not dead code.

## 1. What the scoped backup claims — and does not

| | Full (`--scope full`) | Scoped (`--scope small_test`) |
|---|---|---|
| Schema (tables, functions, guard triggers, FKs, extensions) | archived and restored | archived and restored (the whole schema) |
| Row data | every table | **the tables the small test can write, plus their foreign-key parents** |
| Restore proof | every table's count + content hash + sequences equal | the same, over exactly that data set |
| Receipt wording | "complete logical database" | "SCOPED logical backup, not a complete database" |
| Recovers a table the test was never meant to write but wrote | yes | **no** (no backup detects an unexpected write either) |

A restore of live shared tables over a running production would roll back other writers; the row-targeted teardown is the
rollback. The backup is insurance plus proof that the pre-test rows (chiefly the `asset_throughput` row the dispatch
overwrites and the teardown deletes, and the insert-only global Gochara tables nothing else can undo) are recoverable.

## 2. The scope — `platform/scripts/backup_v5_small_test_scope.json`

* **Rule (ruling condition 1):** every table the dispatch, the run and the teardown can WRITE, plus `_migrations_applied`
  (context only: written by `scripts/migrate.ts`, kept so the proof can state the scratch schema is at the same migration set).
  Currently 34 written + 1 context = 35 tables; the **digest** (`sha256` of the canonical JSON of `{schema, name, sorted tables}`)
  is `489330948aecf7b6fdaa52d00a8f8fa8735e4ed1dcd27a14ee957bd43c07b528`. Prose and `sites` do not enter the digest.
* **Independently re-derived** at head `4c43d2281` (not copied from the draft). Differences from the draft, all verified:
  `public.asset_throughput_state_audit` is **added** — a trigger (`586_f152_asset_throughput_state_audit.sql:96-117`) writes it on
  every `UPDATE OF state` of `asset_throughput`, which the dispatch upsert and the runner perform. Legacy
  `kala_gochara_contacts` / `kala_gochara_windows` and the sealing tables `ka_gochara_seal_brief` / `_approval` have write
  statements in the scanned code but are **proven unreached** (§2.2), so they are not scope. `kala_gochara_coverage` and
  `kala_gochara_publication` stay (the writer reaches them through `RecordStore` / `publish_candidate`).
* **2.1 Static pin (test `test_backup_v5_small_test_scoped.py`):** an AST scan of the dispatch, teardown, shared policy, the
  orchestrator modules, all of `gochara_kernel` and the writer's first-party import closure finds every
  `INSERT/UPDATE/DELETE/MERGE/TRUNCATE/COPY` string; each target must be in the scope file or be a declared unreached table;
  placeholder targets (`{table}`) must be declared with a resolver that is re-evaluated against the real constants. A new write
  target fails the test. The detector is shown to read false against a planted file.
* **2.2 Unreached claims:** the legacy-ledger tables are written only inside `ledger.py` functions that no scanned module calls
  (`write_contacts`, `rollback`, `clear_generation`, `clear_windows_on_reversal`, `supersede`, and their internals); the sealing
  tables only in `seal_job` / `verification_job` / `seal_flow` / `seal_brief`, which nothing scanned imports. Both are tested.
* **2.3 Changing the scope** is a reviewed change to the JSON, to `SCOPED_BACKUP_SCOPE_SHA256` in `v5_small_test_shared.py`
  (the executor loads that file alone from the reviewed commit, so the pin lives there) and to the test list. Any of the three
  out of step fails a test.
* **2.4 What the static scan cannot see** — checked at **capture time from the catalog**, under the exported snapshot, and
  refused by name: (a) a trigger on a WRITTEN table whose function body writes outside the data set (first level; catches the
  audit table; foreign-key parents and the context table are never written, so their triggers never fire); (b) a `DELETE`/`UPDATE` referential action (`CASCADE`, `SET NULL`, `SET DEFAULT`) from a written table to a table
  that is neither archived nor reviewed (`guarded_children`: the six tables `build_runs` can null, which the teardown refuses to
  touch unless they hold zero references); (c) a scope table that is missing or not an ordinary table.
* **Foreign-key parents** are computed at capture (`pg_constraint`, upward and transitive) and archived as data, because
  `pg_restore` adds foreign keys after loading data. On the migration-derived schema they are `charts`, `profiles`,
  `asset_output_digest_specs`. They are recorded in the receipt (`scope.closure`) and measured.

## 3. How capture and restore work

* **Capture** (`--operation snapshot --scope small_test`): `REPEATABLE READ READ ONLY`, `pg_export_snapshot()`; global
  refusals (foreign tables, large objects — both measured as zero on production, prerequisites receipt) ; catalog refusals (§2.4);
  size refusal; **measurement**; `pg_dump --format=directory --jobs=4 --snapshot=<id> --no-owner --no-privileges` with
  `--exclude-table-data` for every other user table (so the archive carries the full schema and only the data set's rows);
  sequences re-measured after the dump (the only state a snapshot does not freeze); the archive's table-of-contents must list
  data for **exactly** the data set (an exclusion that did not take effect refuses); every archive file is SHA-256'd and the sorted
  manifest is the archive digest.
* **Measurement (ruling condition 2):** no server-side sort and no row transfer. Per table one scan:
  `count(*)` and two sums of the 64-bit halves of `sha256(row_to_json(row))`; the receipt stores
  `sha256("rows:sum1:sum2")` in the existing `{rows, sha256}` shape and names `measurement_method =
  sql_sum_sha256_rowjson/1`. Order is not a claim; a changed, missing, duplicated or swapped row changes it. The same SQL runs on
  the restore target.
* **(I) INTERPRETATION J2A-S1:** the second same-snapshot table pass is dropped (it cannot differ under one `REPEATABLE READ`
  snapshot). Alternative: keep both passes (a third of the source volume, no signal).
* **Restore proof** (`--operation restore-verify --scope small_test`, same label): validates the capture (scope digest equal to
  the reviewed file's, file hashes, window, provenance — the BG-01 checks are shared with the full form), creates
  `ky_restore_<label>` on the loopback cluster, `pg_restore --exit-on-error --single-transaction`, measures the receipt's data set
  and sequences, requires exact equality, drops the target, and only then writes `restore.json`
  (`ky.smalltest_restore/2`: `restore_verified`, `target_removed`, `scope_sha256`, `validity`).
* **Fail-closed (condition 3):** `backup_taken` is written only with the capture receipt, after the archive, the table of contents
  and the measurements are validated; `restore_verified` only after exact equality and target removal. A failed client exit,
  an unmeasured or different table, a changed sequence, a scope or file-hash difference, an existing target or evidence file
  refuses with no receipt. No existing refusal was relaxed. A scoped receipt is refused by a full request and the reverse.

## 4. The 30-minute target (condition 5)

At today's observed 1.2 MB/s the dominant cost is bytes through the proxy. Bounds, enforced in code rather than hoped for:
the data set may not exceed 500 MB on disk (`SCOPED_DATA_BUDGET_BYTES`; a COPY stream is at most about twice that, ~14 minutes
before any `--jobs` gain) — over that the capture refuses **before dumping**, naming the byte count; `pg_dump` is killed at
15 minutes and `pg_restore` at 10; each measurement statement is capped at 5 minutes. Estimate: schema catalog read 1–3 minutes,
data (tens of MB expected) 1–5 minutes, local restore and proof under 2 minutes — **about 5–12 minutes typical, 28 minutes
worst case**. The real byte count of the 35 tables is not known (none is among the ten largest relations; each is below
0.52 GB including indexes): if the budget refusal fires, the step stops with that number and the cockpit decides — nothing is
dumped. Local rehearsal on the full migration-derived schema (475 tables, pgvector, guard triggers): capture 0.4 s, restore 1.1 s.

## 5. Validity window (condition 4)

The capture receipt states `validity` = `[snapshot instant, snapshot instant + 4 h]` (`SCOPED_BACKUP_VALIDITY_S`); the restore
proof repeats it. **(I) INTERPRETATION J2A-S3:** 4 h, so a sitting (dry run, pre-acceptance receipt — itself valid 3 h) fits;
alternative: shorter, at the cost of re-running step 10 inside a long sitting. A dispatch must satisfy
`restore proof time <= now <= not_after`.

Enforcement is the smallest change that works: `scoped_backup_problem` in `v5_small_test_shared.py`, called from
`smalltest_request_problem`, which runs at executor admission **and again inside the dispatch script at `--execute`**. A
`smalltest_dispatch` request that carries `backup_label` and `backup_restore_sha256` (the SHA-256 of that label's `restore.json`,
bound by the request's acceptance digest like the absence evidence) is admitted only for a verified scoped proof of the pinned
scope digest, whose capture matches it, inside its window. **(I) INTERPRETATION J2A-S2:** a request with no `backup_label` is
not checked here (the executor's boolean attestations are unchanged) and a full-form proof (`/1`) carries no window; the scoped
step-10 pack must therefore always name the label. Alternative: make the label mandatory for every dispatch — rejected here
because it changes every existing dispatch request and its pinned suites.

## 6. Runbook — step 10, scoped

1. Prerequisites as before (lease, quiescence/fence, readback prerequisites). The reviewer quotes the **scope digest** above in
   the step detail; neither attestation may be worded "complete database".
2. `backup_snapshot` request, `args: {"label": "<new unique label>", "scope": "small_test"}` (the label is burned on any
   failure: use a new one). Success prints the capture receipt; read `scope.closure`, `scope.data_bytes`, `validity`.
3. `backup_restore_verify` request, the **same label**, `args: {"label": "<same>", "scope": "small_test"}`.
4. The dispatch request names `backup_label` and `backup_restore_sha256` (`sha256sum run/ops/backups/<label>/restore.json`).
5. If the window lapses before dispatch, repeat 2–4 with a new label. Refusal text names what to do: *scope table missing*
   (production lacks a reviewed table: fix the scope by review), *trigger … writes outside the scope* / *action … reaches an
   unreviewed table* (a write path the review missed: extend the scope by review, never bypass), *over the budget* (§4),
   *capture scope differs from the reviewed scope; recapture required* (the scope changed after capture).

## 7. Test map (one oracle per claim)

| Claim | Oracle |
|---|---|
| every write target is in scope; detector reads false | `test_backup_v5_small_test_scoped.py` scope-pin tests |
| digest pinned where the executor reads it | `test_policy_pins_the_reviewed_scope_digest…` |
| trigger targets read from function bodies | `test_trigger_write_targets_come_from_the_function_body` (the migrations' real bodies) |
| archive holds exactly scope + FK parents; restores equal | `test_p01_smalltest_backup_scoped.py::test_scoped_archive_holds_exactly…` (real `pg_dump`/`pg_restore`) |
| measurement order-independent and change-sensitive | `…::test_sql_measurement_is_order_independent…` |
| unhonourable scope refused before any dump | `…::test_scope_the_database_cannot_honour…` |
| sequence drift / leaked data / tampered file / failed client | the four matching tests in the same DB file |
| receipt bound to scope, file hashes, window, provenance | `test_scoped_capture_refuses_anything_not_bound…` |
| window gates the dispatch | `test_dispatch_after_the_window…`, `…_not_the_reviewed_scope…`, `test_request_policy_applies_the_window…` |
| scopes cannot be crossed; executor can request the scope | cross-refusal and executor-table tests |

## 8. Residual risks (stated, not hidden)

* The production byte size of the data set is unmeasured (§4); the budget refusal is the safeguard.
* Trigger detection is first-level (a trigger calling a function that writes is not seen); the three known trigger functions
  are covered by test and the catalog run on the migration-derived schema passed. A `SECURITY DEFINER`/nested writer would need review.
* Production has 507 tables against 475 on the migration-derived schema; a foreign-key parent or trigger among the extra 32 is
  possible and would refuse the capture by name (fail-closed) rather than widen it silently.
* Materialized views are refreshed during restore over mostly empty tables; a view that errors on empty inputs would fail the
  restore (loudly, before any receipt).

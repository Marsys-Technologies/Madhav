---
artifact: J2A_SCOPED_BACKUP
version: "1.2"
status: REVIEW_CANDIDATE
produced_on: 2026-10-17
authority: surrogate rulings SR-J2A-BACKUP-SCOPE (DECISIONS_SURROGATE.jsonl, 2026-10-16T22:08Z), SR-J2A-BACKUP-POSITIVE (2026-10-17T01:50Z) and SR-J2A-RESTORE-BASE (2026-10-17T10:52Z); amends P01_REWORK_v1_0.md (paired logical backup) and the step-10 text of the small-test sitting checklist
changelog:
  - "1.3: W3W4 pack verify E3. `--scope century` and `--scope verification_seal` share this mechanism, each with its own reviewed scope file and pinned digest (SCOPED_BACKUP_SCOPE_SHA256S): century = the final candidate build (same tables as small_test, its own name), verification_seal = the verifier's and the sealer's declared write surface (verification_job.VERIFIER_WRITE_TABLES + seal_flow.SEALER_WRITE_ALLOWED + the migration ledger as context). A proof of one scope never admits a dispatch of another."
  - "1.2: SR-J2A-RESTORE-BASE. The 2026-10-17T09:04Z restore proof failed (`pg_restore failed`): production had since applied migration 1394 (functions `ka_gochara_governed_chart_statement_lock` / `ka_gochara_touched_chart_statement_lock`, triggers on `kala_gochara_publication` / `kala_gochara_authority`, both in scope), and the pinned, empty `SCOPED_RESTORE_BASE_MIGRATIONS` could not supply them. The restore base is now DERIVED, never pinned: the governed bundle schema plus every migration the archive's own `_migrations_applied` ledger records as applied after the bundle whose file mentions a scope table, each file hash-checked against the ledger. New captures record the ledger digest and the base identity in capture.json; the proof refuses if the ledger differs from the one recorded (or, for a capture that recorded none, from the one the base was derived from). `SCOPED_RESTORE_BASE_MIGRATIONS` is removed."
  - "1.1: SR-J2A-BACKUP-POSITIVE. The 01:48Z production capture failed because the full-schema dump locked relations the backup login (amjis_app) cannot read (four planner_* tables owned by purna_inquiry_owner). The scoped dump now names ONLY the scope plus its foreign-key parents, each with its own -t (definitions and data), so nothing else is locked or dumped; the restore target is built from the governed L1 bundle schema instead of from a production schema dump; a guarded --exclude-table fallback is recorded in capture.json with each table's owner. No grant was widened."
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
| Schema (tables, functions, guard triggers, FKs, extensions) | archived and restored | **the definitions of the same tables only** (with their indexes, constraints, triggers, owned sequences); functions, types and extensions are not archived |
| Row data | every table | **the tables the small test can write, plus their foreign-key parents** |
| Restore proof | every table's count + content hash + sequences equal | the same, over exactly that data set, into a target built from the governed L1 bundle schema (§3) |
| Receipt wording | "complete logical database" | "SCOPED logical backup, not a complete database" |
| Recovers a table the test was never meant to write but wrote | yes | **no** (no backup detects an unexpected write either) |

A restore of live shared tables over a running production would roll back other writers; the row-targeted teardown is the
rollback. The backup is insurance plus proof that the pre-test rows (chiefly the `asset_throughput` row the dispatch
overwrites and the teardown deletes, and the insert-only global Gochara tables nothing else can undo) are recoverable.

## 2. The scope — `platform/scripts/backup_v5_small_test_scope.json`

* **Rule (ruling condition 1):** every table the dispatch, the run and the teardown can WRITE, plus `_migrations_applied`
  (context only: written by `scripts/migrate.ts`, kept so the proof can state the scratch schema is at the same migration set).
  Currently 37 written + 1 context = 38 tables (the three migration-1308 near-miss tables were added on top of the 34 + 1 first
  derived at `4c43d2281`, by the p06 near-miss storage PR); the **digest** (`sha256` of the canonical JSON of `{schema, name, sorted tables}`)
  is `1daf69d6e31279592947aa25e2b4f9a5c1c8137d6663ba039c27e7331ac7335a`. Prose and `sites` do not enter the digest.
  The teardown's closed deletion list moves with the scope (owner-surrogate ruling madhav-6d, 2026-10-19): `GENERATION_TABLES` in
  `teardown_v5_small_test_job.py` holds the two generation-scoped near-miss tables (`ka_gochara_near_miss`,
  `ka_gochara_near_miss_search`; `NEAR_MISS_TABLES` in `v5_small_test_shared.py`, so the absence proof and the independent readback count
  them too). The GLOBAL insert-only `ka_gochara_near_miss_object` is backed up but never deleted or counted by the teardown: its trigger
  refuses DELETE and other charts and generations share an object. The table list, hence the digest, did not change.
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

* **2.5 The other two scopes (W3W4 pack verify E3).** `--scope century` and `--scope verification_seal` are this mechanism under two more reviewed files, each pinned by digest in
  `v5_small_test_shared.SCOPED_BACKUP_SCOPE_SHA256S` (the executor loads that file alone). The digest is over `{schema, name, sorted tables}`, so the NAME is part of it: a proof of one scope never admits a
  dispatch of another (`scoped_backup_problem(..., scope=)`; `century_request_problem` demands `century`).
  * `century` (`backup_v5_century_scope.json`): the final, ordinary candidate build is the small-test staged run without the test-slice marker, so it writes the same tables; the file is derived from the small-test one
    and `test_backup_v5_century_verification_scopes.py` (S1) runs the same AST scan over `dispatch_v5_century_job.py` and `century_launch.py` as well and refuses a write target the file does not list.
  * `verification_seal` (`backup_v5_verification_seal_scope.json`): the write surface the verifier job and the sealer each PROVE they hold at run time — `verification_job.VERIFIER_WRITE_TABLES`
    (`ka_gochara_search_inventory_verification`, `ka_gochara_eval_window_verification`, `ka_gochara_seal_brief`) and `seal_flow.SEALER_WRITE_ALLOWED` (`ka_gochara_generation_seal`, `ka_gochara_seal_approval`, four
    columns of `kala_gochara_publication`) — plus `_migrations_applied` as context. The test (V1) re-derives it from those constants; its digest equals the one the J5S pack's `derive_scope.py` computes.
    `guarded_children` is empty by design: an unreviewed referential-action child fails the capture by name (§2.4b), it is never assumed away.

## 3. How capture and restore work

* **Capture** (`--operation snapshot --scope small_test`): `REPEATABLE READ READ ONLY`, `pg_export_snapshot()`; global
  refusals (foreign tables, large objects — both measured as zero on production, prerequisites receipt) ; catalog refusals (§2.4);
  size refusal; **measurement**; `pg_dump --format=directory --jobs=4 --snapshot=<id> --no-owner --no-privileges --strict-names`
  with **one quoted `--table="schema"."name"` per relation of the data set and nothing else** (SR-J2A-BACKUP-POSITIVE: pg_dump
  locks and reads only the named relations, so a relation the backup login cannot read — the `planner_inquiry_*` /
  `planner_managed_prashna_jobs` tables — is never touched, and no exclusion list is needed); sequences re-measured after the dump
  (the only state a snapshot does not freeze); the archive's table-of-contents must list **both the definition and the data of
  exactly** the data set (anything else refuses: `archive data entries differ…` / `archive definitions differ…`); every archive
  file is SHA-256'd and the sorted manifest is the archive digest.
* **Guarded fallback (`--exclude-table`)**: `dump_excludes` in the scope file (absent today, so none is passed) names a relation
  pg_dump must be told to skip. At capture it must lie **outside the scope and the foreign-key closure and have no foreign-key
  edge to or from them**, else the capture refuses (`dump exclusion is inside the scope…` / `…has a foreign-key edge…`); each one
  is written to `scope.dump_excludes` in `capture.json` with its catalog owner.
* **Measurement (ruling condition 2):** no server-side sort and no row transfer. Per table one scan:
  `count(*)` and two sums of the 64-bit halves of `sha256(row_to_json(row))`; the receipt stores
  `sha256("rows:sum1:sum2")` in the existing `{rows, sha256}` shape and names `measurement_method =
  sql_sum_sha256_rowjson/1`. Order is not a claim; a changed, missing, duplicated or swapped row changes it. The same SQL runs on
  the restore target.
* **(I) INTERPRETATION J2A-S1:** the second same-snapshot table pass is dropped (it cannot differ under one `REPEATABLE READ`
  snapshot). Alternative: keep both passes (a third of the source volume, no signal).
* **Restore proof** (`--operation restore-verify --scope small_test`, same label): validates the capture (scope digest equal to
  the reviewed file's, file hashes, window, provenance — the BG-01 checks are shared with the full form), creates
  `ky_restore_<label>` on the loopback cluster, **builds its base schema, drops the data-set tables from it, then**
  `pg_restore --exit-on-error --single-transaction` of the archive, measures the receipt's data set and sequences, requires exact
  equality, drops the target, and only then writes `restore.json` (`ky.smalltest_restore/2`: `restore_verified`, `target_removed`,
  `scope_sha256`, `validity`, `restore_base`).
* **(I) INTERPRETATION J2A-B1 — restore base (SR-J2A-BACKUP-POSITIVE).** Scoped definitions alone cannot be restored: the
  archived guard triggers call functions (and columns use types and extensions) that a `-t` dump does not carry. The base is
  therefore the **governed L1 bundle's `schema.sql`** (`run/canonical_l1/20261016T135745Z/`, 475 tables, sha256
  `7e15492f09d54b3f4c49e05afe4237b70254d59740e6a1222a0aa4277899700e`, checked against the bundle manifest before use; mode-700
  directory, read in place, never copied or printed), **not** a dump of production's catalog. It is applied the way the bundle's own
  strict restore applied it (the two psql-only restrict/unrestrict lines dropped; the empty `public` schema dropped; the dump's
  `CREATE SCHEMA public`; the five extensions `vector, pgcrypto, pg_trgm, uuid-ossp, btree_gist`; the rest). The archive's own
  definitions then replace the base's copy of exactly the data set (`DROP TABLE … CASCADE`, then `pg_restore`), so the proof tests
  the archive's definitions, not the bundle's. `restore.json` records the base's path, sha256 and migration list. Alternative:
  `--data-only` into the base's own tables (does not test the archived definitions).
* **(I) INTERPRETATION J2A-B2 (superseded by SR-J2A-RESTORE-BASE, v1.2) — migrations since the bundle are DERIVED.** The earlier
  pinned, empty list is gone. At proof time, before any scratch database exists, the script reads the `_migrations_applied`
  ledger **from the archive** (`pg_restore --data-only --table=_migrations_applied`; that table is in the scope, so the archive
  holds production's ledger exactly as of the snapshot). The base is the bundle schema **plus**, in ledger (`id`) order, every
  entry that was applied after the bundle was cut (`SCOPED_RESTORE_BASE_CUT`) and whose repository file mentions a scope table.
  Each file must exist and hash to the ledger's own `sha256` (else *ledger migration … is missing from the repository* /
  *differs from the file production applied*): the base is what production ran, or the proof refuses. `restore.json`
  records `restore_base.migrations` (the files carried) and `restore_base.ledger` (`count`, `sha256`, `source`).
* **(I) INTERPRETATION J2A-B3 — what "touches a scope table" and "after the bundle" mean.** *Touches* = a whole-word, case-insensitive
  textual mention of a scope table's name in the migration file (over-inclusion or a dynamic-SQL miss fails the restore loudly,
  before any receipt). *After the bundle* = `applied_at` later than `SCOPED_RESTORE_BASE_CUT = 2026-10-16T17:10:23Z`, the time
  `schema.sql` was written (the bundle manifest's `captured_at`, 13:57:45Z, dates the chart data, not the schema; a first
  attempt with it re-applied migration 1235, already in the schema, and failed its owner guard). The cut is a property of the
  pinned bundle file like its sha256; production's ledger has no migration between 14:49:45Z (1389, in the bundle) and 22:26:25Z
  (1393, not), so any cut in that gap gives the same set. Alternatives: carry every post-bundle migration (larger blast radius);
  derive the cut from the file's mtime (not durable).
* **Ledger identity (condition 3).** New captures record `migrations_ledger` (`count`, `sha256` over the sorted
  `(filename, file hash, applied instant)`) read under the same snapshot as the dump, and `restore_base` (bundle path + sha256).
  The proof refuses (a) *migration ledger in the archive differs from the ledger recorded at capture*, (b) a recorded base that is not
  the base it would use, (c) *migration ledger at restore differs from the ledger the base was derived from* — the ledger read
  back from the restored scratch target, checked before the row measurements. A capture by this script lacking those records is
  refused (*recapture required*).
* **(I) INTERPRETATION J2A-B4 — the existing, seedless archive.** A capture taken by an earlier script carries no ledger digest and
  its `script_sha256` no longer equals the script's. `SCOPED_LEGACY_CAPTURE_SCRIPTS` lists the one earlier capture-script digest
  (`3f967bf9…`, the capture of `w4r1_20261017t090403z`); such a receipt is restored through the same ledger-derived base, with the
  ledger taken from the archive (`restore_base.ledger.source = archive`) and checked against the archive's measured row count and,
  after the restore, against the restored target. Any other script digest is refused as before. Alternative: re-capture (rejected by
  the ruling: re-run the proof against that backup).
* **(I) INTERPRETATION J2A-B5 — the schema seed is not built.** SR-J2A-RESTORE-BASE prefers a schema seed taken at backup time and
  allows the ledger-derived base "only if the seed path cannot deliver referenced functions". Judged not deliverable here:
  `pg_dump` cannot select functions by dependency; a plpgsql body's callees are not recorded in `pg_depend`, so a "referenced
  functions" seed is the same first-level reading that missed 1394's functions; and a whole-schema seed locks every relation,
  including the `planner_*` tables the backup login cannot read (the SR-J2A-BACKUP-POSITIVE failure). The ledger-derived base is
  deterministic, hash-checked file by file, and testable locally. Alternative: a catalogue query of all non-extension functions
  (`pg_get_functiondef`) under the snapshot as the seed, plus types; to be built if a later migration needs more than the files
  provide.
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
worst case**. The real byte count of the 35 tables first derived is not known (none is among the ten largest relations; each is below
0.52 GB including indexes): if the budget refusal fires, the step stops with that number and the cockpit decides — nothing is
dumped. Local rehearsal on the full migration-derived schema (475 tables, pgvector, guard triggers): capture 0.4 s, restore 1.1 s.
With the governed bundle as source stand-in and a login that cannot read an out-of-scope table: capture 0.1 s, restore (base build
included) 1.1 s, counts and digests equal.

## 5. Validity window (condition 4)

The capture receipt states `validity` = `[snapshot instant, snapshot instant + 4 h]` (`SCOPED_BACKUP_VALIDITY_S`); the restore
proof repeats it. **(I) INTERPRETATION J2A-S3:** 4 h, so a sitting (dry run, pre-acceptance receipt — itself valid 3 h) fits;
alternative: shorter, at the cost of re-running step 10 inside a long sitting. A dispatch must satisfy
`restore proof time <= now <= not_after`.

Enforcement is the smallest change that works: `scoped_backup_problem` in `v5_small_test_shared.py`, called from
`smalltest_request_problem`, which runs at executor admission **and again inside the dispatch script at `--execute`**. A
`smalltest_dispatch` request **must** carry `backup_label` and `backup_restore_sha256` (the SHA-256 of that label's
`restore.json`, bound by the request's acceptance digest like the absence evidence); without them it is refused. The named
proof is admitted only inside its window: a scoped proof (`/2`) must also be a verified proof of the pinned scope digest whose
capture matches it. **(I) INTERPRETATION J2A-S2 (revised after review B1; the earlier opt-in reading is withdrawn):** the label
is mandatory for every `smalltest_dispatch` (dry-run kinds are unchanged). **(I) INTERPRETATION J2A-S4:** a full-form proof
(`/1`) is accepted only with the same 4 h window, measured from its capture receipt's `ts` (a `/1` capture has no snapshot
instant, so the window starts after the dump); a `/1` pair without a readable timestamp is refused. Alternative: refuse `/1`
proofs for dispatch altogether.

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
   *capture scope differs from the reviewed scope; recapture required* (the scope changed after capture), *dump exclusion …*
   (§3 fallback declared against the scope or an FK-linked table: remove it), *restore base schema … differs / is not readable*
   (the governed bundle moved: stop and raise it; do not point the script at another file); *ledger migration … is missing from
   the repository / differs from the file production applied* (the reviewed commit the executor runs does not hold the migration
   production applied: run the proof from a commit that does); *migration ledger … differs* (the archive or the restored target is not the
   state the capture or the base was derived from: stop, raise it, recapture). A pg_dump failure still withholds the
   client's text; `permission denied for table …` there means a scope or closure relation is unreadable to the login — never widen
   grants to fix it; report it.

## 7. Test map (one oracle per claim)

| Claim | Oracle |
|---|---|
| every write target is in scope; detector reads false | `test_backup_v5_small_test_scoped.py` scope-pin tests |
| digest pinned where the executor reads it | `test_policy_pins_the_reviewed_scope_digest…` |
| trigger targets read from function bodies | `test_trigger_write_targets_come_from_the_function_body` (the migrations' real bodies) |
| archive holds exactly scope + FK parents (definitions and data); restores equal | `test_p01_smalltest_backup_scoped.py::test_scoped_archive_holds_exactly…` (real `pg_dump`/`pg_restore`) |
| another role's unreadable table outside the scope no longer breaks the dump | `…::test_a_table_outside_the_scope_that_the_login_cannot_read_does_not_break_the_dump` (real second login) |
| the dump names exactly the data set, one quoted `-t` each | `test_backup_v5_small_test_scoped.py::test_dump_names_exactly_the_data_set…` |
| guarded exclusion: outside scope/closure, no FK edge, owner recorded | `…::test_a_dump_exclusion_is_a_guarded_fallback…` |
| restore base is the hash-checked governed bundle, bootstrapped as its own restore ran; carried migrations re-hash-checked | `test_restore_base_is_the_hash_checked…`, `test_restore_base_migrations_are_applied…` |
| migrations after the bundle that touch a scope table are derived from the ledger (not pinned), in ledger order | `test_restore_migrations_are_those_applied_after_the_bundle…` |
| a ledger migration the repository cannot reproduce exactly refuses the base | `test_a_ledger_migration_the_repository_cannot_reproduce_exactly_refuses_the_base` |
| a 1394-style post-bundle migration on a scope table is carried and the restore succeeds | `test_p01_smalltest_backup_scoped.py::test_a_post_bundle_migration_on_a_scope_table_is_derived…` (real `pg_dump`/`pg_restore`) |
| the existing seedless capture restores through the ledger-derived fallback | `…::test_a_capture_taken_before_the_ledger_was_recorded_is_restored…` |
| a current-script capture without its ledger digest is refused | `…::test_a_capture_by_this_script_without_its_ledger_digest_is_refused` |
| ledger differing from capture (archive) / from the base's source (restored target) refuses | `…::test_restore_refuses_when_the_archives_ledger…`, `…::test_restore_refuses_when_the_restored_targets_ledger…` |
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
  possible and would refuse the capture by name (fail-closed) rather than widen it silently. A foreign-key parent the login cannot
  read would now fail the dump on that parent (and only it) with the same withheld text.
* Row-level security: `public.charts` (a closure parent) has it enabled in the bundle. pg_dump errors, and the SQL measurement would
  silently see filtered rows, for a login that is neither the owner nor `BYPASSRLS`; the earlier full-form backups ran under the
  same login. Not changed here; the local rehearsal needed `BYPASSRLS` for the stand-in login.
* The restore base is the bundle plus the ledger-derived migrations (J2A-B1/B2/B3). A dependency that is neither in the bundle nor in a
  migration file that mentions a scope table (e.g. a function created by an unrelated-looking migration and called by a carried
  one) fails the restore loudly before any receipt; it is then fixed by review, not by a pin. Rehearsed 2026-10-17 on the local
  cluster against the real archive `w4r1_20261017t090403z` (read in place, scratch database dropped): restore equal, one migration
  carried (1394).
* Materialized views are refreshed during restore over mostly empty tables; a view that errors on empty inputs would fail the
  restore (loudly, before any receipt).

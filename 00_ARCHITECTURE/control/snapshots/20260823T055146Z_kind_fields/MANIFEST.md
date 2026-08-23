# M0-T21 — I2 snapshot: `asset_registry` kind fields

**Captured:** 2026-08-23T05:51:46Z (UTC), before any write by this task
**Task:** M0-T21 (Nirmāṇa Phase 0.6b), branch `campaign/nirmana-autonomous`
**Authority:** DECISIONS.jsonl D-24 part 2 (G9) — *repair the values first, then make the column authoritative*
**Author:** KĀRAKA. **Not certified by its author** (I16/H7).

## What is captured

`asset_registry`: `asset_id`, `asset_kind`, `asset_type`, `storage_type` — **all 128 rows**,
not only the six this task changed. A snapshot scoped to the change set could not have proved
that nothing *else* moved, which is the assertion the post-check actually needs.

| file | purpose |
|---|---|
| `snapshot.tsv` | 128 rows, tab-separated, header row |
| `snapshot.json` | same 128 rows + capture timestamp and column list |
| `restore.sql` | literal-`VALUES` restore of the three columns, with a rowcount assertion that `RAISE EXCEPTION`s (aborting the transaction) unless exactly 128 rows are restored |
| `SHA256SUMS` | checksums over every file in this directory |
| `derive_independent.py` | the independent re-derivation (below) |
| `independent_derivation.json` | its machine-readable output |
| `snapshot.py` / `verify_snapshot.py` / `apply.py` / `postcheck.py` | capture, verification, apply, post-check |

## Restore status — stated honestly

`restore.sql` is **AUTHORED AND PARSE-VERIFIED, NOT PROVEN-BY-EXECUTION.**

`verify_snapshot.py` re-parses the 128 `VALUES` tuples back out of the SQL text and asserts they
are byte-identical to `snapshot.tsv`/`snapshot.json` and to the live table, and asserts the file
contains no `DROP`/`TRUNCATE`/`DELETE`/`ALTER`. That is as far as verification can go without
executing it. **A restore drill is itself a write and is outside M0-T21's granted scope** — it is
not claimed here, and no green signal is written for it (§N.8 / H4).

## Scope of the write this snapshot protects

`asset_kind`, `asset_type`, `storage_type` on six named `asset_id`s. No other column, no other
table, no DDL, no migration, no build dispatched.

# M0-T26 — I2 snapshot + repair record: `asset_registry` layer position

**Captured:** 2026-08-23T06:41:41Z (UTC), before any write by this task
**Task:** M0-T26 (Nirmāṇa Phase 0.5a) — repair `layer_index` and `layer_name`
**Branch:** `campaign/nirmana-autonomous`
**Authority:** `DECISIONS.jsonl` **D-4** (mechanical, derivable-only, non-derivable left NULL,
pre-flight discriminating detector) and **D-23** (`lel_events` HELD — the SOURCE
reclassification is R5's, so its value is not mechanically derivable and stays NULL).
**Author:** KĀRAKA. **Not certified by its author** (I16 / H7).

## What is captured

`asset_registry`: `asset_id`, `layer`, `layer_index`, `layer_name` — **all 128 rows**, not only
the 21 assets this task touched. A snapshot scoped to the change set could not have proved that
nothing *else* moved, which is the assertion the post-check actually needs. `layer` is captured
because it is the derivation's **input**: P5 asserts the repair did not move its own input.

| file | purpose |
|---|---|
| `snapshot.tsv` / `snapshot.json` | 128 rows, pre-repair, tab-separated and machine-readable |
| `restore.sql` | literal-`VALUES` restore of the two written columns, with a rowcount assertion that `RAISE EXCEPTION`s (aborting the transaction) unless exactly 128 rows restore |
| `SHA256SUMS` | checksums over every file in this directory |
| `snapshot.py` | capture |
| `verify_snapshot.py` | 4 read-back assertions (tsv==json, restore.sql re-parses to the snapshot, snapshot==live, no destructive token) |
| `derive_independent.py` | re-derivation of both repair sets from THREE sources; `independent_derivation.json` (pre-repair, the input `apply.py`/`postcheck.py` consumed) and `independent_derivation_postrepair.json` (re-run after the repair with the parser defect below fixed) |
| `preflight.py` | the discriminating detector; `detector_pre.json` / `detector_post.json` |
| `apply.py` | the write, with rowcount + `lel_events` + codepoint assertions that roll back |
| `postcheck.py` | 7 assertions against the SNAPSHOT, not against the statement's shape; `postcheck.json` |
| `restore_drill.py` | executes `restore.sql` in a transaction, compares to the snapshot, ROLLS BACK; `restore_drill.json` |
| `durability_check.py` | re-projection of a re-seed for these two columns; `durability_after_repair.json` |

## Restore status — stated honestly

`restore.sql` is **PROVEN BY EXECUTION, ROLLED BACK — not committed.**

`verify_snapshot.py` first re-parsed all 128 `VALUES` tuples back out of the SQL text and
asserted they are byte-identical to `snapshot.tsv` / `snapshot.json` and to the live table, and
that the file contains no `DROP`/`TRUNCATE`/`DELETE`/`ALTER`. After the repair,
`restore_drill.py` then **executed** the file's body inside one transaction and compared all 128
rows against `snapshot.json`: **0 cells differed**, i.e. the restore genuinely reproduces the
pre-repair state. The transaction was then rolled back, and `postcheck.py` was re-run afterwards
and still passed — so the repaired state is what is live. The drill writes only the two columns
this task is scoped to, on rows already in the snapshot, and nothing was committed by it.

## Scope of the write this snapshot protects

`layer_index` (20 rows) and `layer_name` (19 rows) on the re-derived asset_ids. No other column,
no other table, no DDL, no migration, no build dispatched. `lel_events` was excluded by an
explicit assertion in `apply.py`, not merely by a `WHERE` clause, and is still `NULL` / `NULL`.

## A defect in this directory's own tooling, disclosed

`derive_independent.py` and `durability_check.py` originally matched seed entries with
`asset_id:\s*'…'`, which **also matches `downstream_asset_id:`** elsewhere in the seed; the later
match then overwrote the real entry for 8 assets (`bg_concordance`, `bg_ephemeris`, `bg_rules`,
`bo_karanajala`, `bo_laksana`, `ka_kalasutra`, `ka_sangam`, `ph_nimitta`), leaving their seed
`layer` unresolved. Both files are now fixed (`(?<![A-Za-z_])`, first occurrence wins) and
`durability_check.py`'s reported figures are from the fixed run.

**It did not affect the repair.** None of the 8 is in either repair set, and
`derive_independent.py` fell back to the live `layer` when the seed entry lacked one, so every
seed value it reported for a repair-set row was correct — independently reconfirmed by
`independent_derivation_postrepair.json` (fixed parser, 0/0 repair set remaining) and by
`postcheck.py` P3, which asserted all 39 written cells landed on the seed's value.
`independent_derivation.json` is retained unmodified as the pre-repair record that `apply.py`
actually consumed.

The sibling register's own extractor (`seed_durability/extract_seed_projection.mjs`) does **not**
share this defect — it bracket-matches and evaluates the `ASSETS` array literal rather than
regexing it. Read read-only for that check; nothing in `seed_durability/` was modified.

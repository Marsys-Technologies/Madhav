---
title: Migrations 588/589 — applied-state verification and proposed ledger registration
version: 1.0
status: SUPERSEDED BY EVENTS — the proposal was subsequently APPLIED (see §0)
task: WORK_QUEUE M0-T4
agent: KARAKA-M0-T4
date: 2026-08-23
gated_on: ADHIKARIN ruling (requested, not returned at time of writing)
status_corrected_by: KARAKA-M0-T24, 2026-08-23T05:57Z — status line only; §A–§F analysis untouched
---

# Migrations 588 / 589 — applied-state verification and proposed registration

---

## 0 — DATED CORRECTION (2026-08-23T05:57Z, KĀRAKA-M0-T24)

**This document's `status` line said `PROPOSAL — NO WRITE EXECUTED`. That was true when it was
written and is now false.** All three migrations were applied roughly two hours later. A control
document asserting a state that production contradicts is this campaign's own defect class, so the
status line is corrected here rather than left to be tripped over.

What actually happened, read live from `_migrations_applied` at 2026-08-23T05:55Z (read-only):

| ledger id | filename | applied_at (UTC) |
|---|---|---|
| 448 | `588_remove_asset_build_protection.sql` | 2026-08-23T05:33:15.527766Z |
| 449 | `589_drop_orphaned_protection_functions.sql` | 2026-08-23T05:34:38.787119Z |
| 450 | `590_nirmana_m0_catalogue_contract_columns.sql` | 2026-08-23T05:36:13.833986Z |

The ledger now holds **450 rows**, up from the **447** this document verified. Row 447 remains
`588_samiksha_digest_journal.sql` (applied 2026-08-22T23:42:20Z) — the *other* 588, which is F-1's
subject and is not evidence of anything about these migrations.

**Nothing below this section has been rewritten.** §A–§F were accurate as analysis and as a record
of what M0-T4 itself did and did not do — including its statement that M0-T4 executed no write,
which remains true of M0-T4. The write was performed later, by a different agent, under the
ADHIKĀRIN ruling this document was waiting on. Read §A–§F as a proposal-plus-evidence document
whose proposal was subsequently accepted and carried out, not as a description of current state.

This correction touched the frontmatter `status` line and added this section. No other edit was
made, and no `.sql` file was touched (H5).

---

**Nothing in this document has been executed.** No INSERT was made into the migration
ledger, neither migration was run, and neither `.sql` file was edited (H5 / CLAUDE.md §N.4).
This is a proposal plus the evidence it rests on.

---

## A — What each migration claims to change

### `platform/migrations/588_remove_asset_build_protection.sql`
sha256 `a626570346237ed7b3cc609f986e333c615c83f89a7de082d3de46f88b39040c`

Claims, in one transaction:

1. `DROP TRIGGER IF EXISTS trg_kala_gochara_windows_protect_row ON kala_gochara_windows`
2. `DROP TRIGGER IF EXISTS trg_kala_gochara_windows_protect_truncate ON kala_gochara_windows`
3. `DROP TRIGGER IF EXISTS trg_kala_gochara_windows_protect_gen3_row ON kala_gochara_windows`
4. `DROP FUNCTION IF EXISTS kala_gochara_windows_protect_row()`
5. `DROP FUNCTION IF EXISTS kala_gochara_windows_protect_truncate()`
6. `DROP FUNCTION IF EXISTS kala_gochara_windows_protect_gen3_row()`
7. `DELETE FROM build_protected_assets` — unscoped, unconditional; the TABLE is deliberately
   retained.

Statements 4–6 name functions that **never existed**. The real function names, read from the
migrations that created them, are:

- `platform/supabase/migrations/540_build_protected_assets.sql:144` →
  `CREATE OR REPLACE FUNCTION build_protected_assets_guard_row()`
- `…540…:184` → `CREATE OR REPLACE FUNCTION build_protected_assets_guard_truncate()`
- `platform/supabase/migrations/566_parishkara_mr06_gen3_protection.sql:96` →
  `CREATE OR REPLACE FUNCTION build_gen3_gochara_guard_row()`

So 588's own file header is correct when it says its `DROP FUNCTION` statements were no-ops.

### `platform/migrations/589_drop_orphaned_protection_functions.sql`
sha256 `80ba7c0e5976411f188ca6b6469fb33e1ad15cf49dda063b6b309195b07f0e43`

Claims, in one transaction, three drops with the correct names:
`DROP FUNCTION IF EXISTS build_protected_assets_guard_row()`,
`… build_protected_assets_guard_truncate()`,
`… build_gen3_gochara_guard_row()`.

It correctly declines to edit 588 (CLAUDE.md §N.4) and corrects it forward.

---

## B — Live verification (objects inspected directly, not the ledger, not the files)

Connection: production `DATABASE_URL` from `platform/.env.local`, read the way
`00_ARCHITECTURE/control/measure_assets.py` reads it. Session set
`default_transaction_read_only = on` before any query. Credential never printed.

### Q1 — triggers on `kala_gochara_windows`
```sql
SELECT t.tgname, p.proname AS func, n.nspname AS func_schema
  FROM pg_trigger t
  JOIN pg_class c ON c.oid = t.tgrelid
  JOIN pg_proc p ON p.oid = t.tgfoid
  JOIN pg_namespace n ON n.oid = p.pronamespace
 WHERE c.relname = 'kala_gochara_windows' AND NOT t.tgisinternal
 ORDER BY t.tgname;
```
```
(0 rows)
```

### Q2 — all six function names mentioned by 588 and 589
```sql
SELECT n.nspname AS schema, p.proname, pg_get_function_identity_arguments(p.oid) AS args
  FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
 WHERE p.proname IN ('kala_gochara_windows_protect_row',
                     'kala_gochara_windows_protect_truncate',
                     'kala_gochara_windows_protect_gen3_row',
                     'build_protected_assets_guard_row',
                     'build_protected_assets_guard_truncate',
                     'build_gen3_gochara_guard_row')
 ORDER BY p.proname;
```
```
(0 rows)
```

### Q2b — every non-system function whose name contains "protect" or "guard"
```sql
SELECT n.nspname AS schema, p.proname
  FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
 WHERE n.nspname NOT IN ('pg_catalog','information_schema')
   AND (p.proname ILIKE '%protect%' OR p.proname ILIKE '%guard%')
 ORDER BY 1,2;
```
```
{"schema": "public", "proname": "chart_subject_append_only_guard"}
{"schema": "public", "proname": "pariprashna_safety_append_only_guard"}
```
(Neither is a gochara build guard; the protection family is entirely absent.)

### Q3 — protection registry
```sql
SELECT to_regclass('public.build_protected_assets') AS tbl,
       (SELECT count(*) FROM build_protected_assets) AS rows;
```
```
{"tbl": "build_protected_assets", "rows": 0}
```
Table retained, zero rows — exactly what 588 statement 7 claims.

### Q7 — any trigger anywhere still bound to a protect/guard function
```sql
SELECT c.relname AS table, t.tgname, p.proname
  FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
  JOIN pg_proc p ON p.oid=t.tgfoid
 WHERE NOT t.tgisinternal AND (p.proname ILIKE '%protect%' OR p.proname ILIKE '%guard%')
 ORDER BY 1,2;
```
```
{"table": "chart_subject_consent_events", "tgname": "trg_chart_subject_consent_events_append_only", "proname": "chart_subject_append_only_guard"}
{"table": "chart_subject_deletion_tombstones", "tgname": "trg_chart_subject_deletion_tombstones_append_only", "proname": "chart_subject_append_only_guard"}
{"table": "pariprashna_retraction_prediction_notes", "tgname": "trg_pariprashna_retraction_prediction_notes_append_only", "proname": "pariprashna_safety_append_only_guard"}
{"table": "pariprashna_retractions", "tgname": "trg_pariprashna_retractions_append_only", "proname": "pariprashna_safety_append_only_guard"}
{"table": "pariprashna_safety_decisions", "tgname": "trg_pariprashna_safety_decisions_append_only", "proname": "pariprashna_safety_append_only_guard"}
{"table": "pariprashna_safety_review_events", "tgname": "trg_pariprashna_safety_review_events_append_only", "proname": "pariprashna_safety_append_only_guard"}
{"table": "pariprashna_safety_review_passes", "tgname": "trg_pariprashna_safety_review_passes_append_only", "proname": "pariprashna_safety_append_only_guard"}
```

### Q9 — were 540 and 566 ever applied? (the question that makes 589's verdict decidable)
```sql
SELECT id, filename, applied_at, sha256 FROM _migrations_applied
 WHERE filename LIKE '540%' OR filename LIKE '566%' ORDER BY filename;
```
```
{"id": 400, "filename": "540_build_protected_assets.sql", "applied_at": "2026-08-06 10:41:51.476086+00:00", "sha256": "4c0a4c5482b4629df6e992b0d155c0336eb5b202d15a4e3f331e73b59364f9d2"}
{"id": 425, "filename": "566_parishkara_mr06_gen3_protection.sql", "applied_at": "2026-08-10 18:18:48.406726+00:00", "sha256": "0650b1716a04426475c48c2d54dd20e7d299b23289d588f3ffd182b77508459e"}
```

### Q8 — the corpus 588 removed protection from is intact
```sql
SELECT generation, count(*) FROM kala_gochara_windows GROUP BY generation ORDER BY 1;
```
```
{"generation": "3.0", "count": 1884}
{"generation": "v1", "count": 38287}
```
Matches the counts 588's header records (38,287 v1 + 1,884 gen-3.0). Nothing was lost.

### Verdicts

| Migration | Verdict | Basis |
|---|---|---|
| `588_remove_asset_build_protection.sql` | **APPLIED** (fully, as written — including its two documented no-op statements) | Q1: all three triggers gone. Q3: `build_protected_assets` exists with 0 rows. Its statements 4–6 were no-ops when it ran and would be no-ops now; "as written" is the honest qualifier. |
| `589_drop_orphaned_protection_functions.sql` | **APPLIED** | Q9 proves 540/566 ran, so the three functions existed. Q2/Q2b prove none of the three exists now. 588's `DROP FUNCTION` statements named different (non-existent) identifiers and cannot have dropped them. 589 is the only statement set in the repo that names them correctly. |

**Honest limit on the 589 verdict.** `DROP … IF EXISTS` leaves no positive trace: absence is
consistent both with "589 ran" and with "something else dropped them." The verdict above is an
inference from four facts (540/566 applied → functions existed; functions now absent; 588's
drops named other identifiers; no other migration in either directory drops them). I did not
find a transaction log or audit record that names 589 as the actor, and I do not claim one
exists. If PARĪKṢAKA wants a stronger basis than inference, none is available from the
database's current state — the evidence is structural, not recorded.

---

## C — The tracked runner and its ledger

**Runner:** `platform/scripts/migrate.ts`. It reads **two** directories that share one numeric
sequence: `platform/migrations/` and `platform/supabase/migrations/`
(`collectMigrationFiles`, migrate.ts:399–410), concatenates and sorts by filename.

**Ledger table:** `_migrations_applied` — runner-owned bookkeeping, created by the runner's own
`TRACKER_DDL`/`TRACKER_IDENTITY_DDL` (migrate.ts:40–64), never by a numbered migration.

Live schema (`information_schema.columns`):
```
{"column_name": "id",           "data_type": "integer",                  "is_nullable": "NO"}
{"column_name": "filename",     "data_type": "text",                     "is_nullable": "NO"}
{"column_name": "applied_at",   "data_type": "timestamp with time zone", "is_nullable": "NO"}
{"column_name": "sha256",       "data_type": "text",                     "is_nullable": "NO"}
{"column_name": "sql_identity", "data_type": "text",                     "is_nullable": "YES"}
```
`filename` is UNIQUE (`_migrations_applied_filename_key`, `0001_brahma_baseline.sql:3594`);
`id` is `SERIAL` PRIMARY KEY.

**Are 588/589 recorded? NO.**
```sql
SELECT id, filename, applied_at FROM _migrations_applied
 WHERE filename ~ '^(588|589)' ORDER BY filename;
```
```
{"id": 447, "filename": "588_samiksha_digest_journal.sql", "applied_at": "2026-08-22 23:42:20.550183+00:00"}
```
The only `588*` row belongs to a **different** migration (see finding F-1 below). Neither
`588_remove_asset_build_protection.sql` nor `589_drop_orphaned_protection_functions.sql` has a
row.

**Full unapplied set** (all `.sql` in both dirs vs. all ledger filenames — 441 files on disk,
447 ledger rows):
```
UNAPPLIED: 588_remove_asset_build_protection.sql
UNAPPLIED: 589_drop_orphaned_protection_functions.sql
```
These two are the **only** files the runner currently considers unapplied.

---

## D — Proposed registration, and whether re-running is harmless

### D.1 Are they genuinely idempotent?

**589 — yes, unconditionally.** Every statement is `DROP FUNCTION IF EXISTS`. All three targets
are already absent (Q2), so a re-run drops nothing and errors on nothing. Re-running it is a
true no-op today and remains one unless 540/566 are re-applied.

**588 — yes today, with one caveat named.**
- Statements 1–3 (`DROP TRIGGER IF EXISTS`): no-ops, the triggers are gone (Q1).
- Statements 4–6 (`DROP FUNCTION IF EXISTS`, misnamed): no-ops now and always were.
- Statement 7 (`DELETE FROM build_protected_assets`): unscoped and unconditional. It affects
  **0 rows today** because the table is empty (Q3), so the re-run is harmless *now*. The caveat
  is real, not theoretical: this statement is idempotent only while the table is empty. If
  protection is ever reinstated (the file itself documents re-applying 540/566 as the reversal
  path) and 588 is re-run afterwards, it would silently wipe the reinstated registry. This is
  not H1 — `build_protected_assets` is a registry table, not the gochara corpus or a snapshot —
  but it is worth stating that "idempotent" here is state-dependent, not structural.

### D.2 Two registration options

**Option 1 — run the tracked runner (recommended, subject to ADHIKĀRIN).**
```bash
cd platform && DATABASE_URL="$(…from platform/.env.local…)" ./node_modules/.bin/tsx scripts/migrate.ts
```
The runner would execute both files (both no-ops per D.1) and then INSERT their ledger rows
itself, computing `sha256` and `sql_identity` with its own code. Verified precondition: these
two files are the *only* unapplied files, so a bare run applies nothing else. `--target
589_drop_orphaned_protection_functions.sql` narrows it further but is not required.
This is the option that makes the record match reality *through the mechanism*, not around it.

**Option 2 — direct ledger INSERT (record-only, no SQL executed).**
Hash values below computed with the runner's own exported `sqlIdentityOf` / `crypto` sha256
against the exact on-disk bytes.
```sql
-- NOT EXECUTED. Gated on ADHIKARIN.
INSERT INTO _migrations_applied (filename, sha256, sql_identity, applied_at) VALUES
  ('588_remove_asset_build_protection.sql',
   'a626570346237ed7b3cc609f986e333c615c83f89a7de082d3de46f88b39040c',
   'a38b9dc04f4720aa123067f2cf668454e55d7713ec003ae5513d6f2ade9ba8bf',
   NOW()),
  ('589_drop_orphaned_protection_functions.sql',
   '80ba7c0e5976411f188ca6b6469fb33e1ad15cf49dda063b6b309195b07f0e43',
   'be6ce14b6149345fc81eb0e2907a226776038fa640c9e4265e37e34c4f9a15ce',
   NOW());
```
Note on `applied_at`: `NOW()` would record the *registration* time, not the (unknown, unrecorded)
hand-apply time. There is no honest value for the real apply moment — I found no record of it —
so `NOW()` plus this document is the truthful option; back-dating it would be fabrication (H6).

**Which is better.** Option 1 is preferable on the §N.4 doctrine the task cites: the hazard is a
migration that silently does nothing while the record says success. Option 1 makes the runner
itself the detector — it executes, and the ledger row is a *consequence* of a real execution
rather than an assertion about one. Option 2 asserts an apply that this agent inferred but did
not witness. Both are proposals; neither was run.

---

## E — What was NOT done

- No INSERT, UPDATE or DELETE of any kind was executed. Session ran with
  `default_transaction_read_only = on`.
- Neither migration was run, by the runner or by hand.
- Neither `.sql` file was edited, reformatted or renamed (H5).
- No credential was printed, logged, copied or committed (P4).
- Findings outside this task were written to `mailbox/to_conductor/`, not fixed (I13/I14).
- This agent does not certify its own work (I16/H7). The verdicts above are observations with
  their queries attached; PARĪKṢAKA decides.

## F — Findings raised elsewhere

- **F-1 · migration number 588 is claimed twice.** Full detail in
  `00_ARCHITECTURE/autonomy/mailbox/to_conductor/20260823T041229Z-m0t4-findings.md`.
- **F-2 · `migrate.ts` executes `main()` on import** unless `NODE_ENV === 'test'`. Same file.

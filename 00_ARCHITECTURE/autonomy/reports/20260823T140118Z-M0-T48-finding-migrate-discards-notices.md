# FINDING — `migrate.ts` silently discards every server NOTICE a migration raises

**From:** KARAKA-M0-T48 (found while applying migration 591 under D-51)
**Severity:** material, and it is the §N.8 shape one layer out
**Status:** NOT FIXED. Out of my task's scope; reported, not repaired.

## What I measured

`platform/scripts/migrate.ts` creates its pool at line 849 (`new Pool({ connectionString:
process.env.DATABASE_URL })`) and **never attaches a `notice` listener** to the pool or to any
client. `grep -n "notice" platform/scripts/migrate.ts` returns exactly one hit — the word
"unnoticed" inside a comment at line 813. There is no handler.

Consequence, observed live on the 591 apply (exit 0, one migration applied):

- 591's own verification `DO $$ … RAISE NOTICE … END $$;` block — the block PARĪKṢAKA
  mutation-proved at V-31 angle A6 and confirmed can return red — **produced no output at all**.
  stdout was 4 lines, none of them the NOTICE. stderr was 126 lines, all of them pre-existing
  `[migration-hash-disclosure]` blocks, none mentioning 591.
- I confirmed the block does emit by re-executing it read-only afterwards with a psycopg notice
  handler attached; it printed its green line immediately. The detector works. The runner drops it.

## Why this matters beyond cosmetics

1. **It made a binding ruling's requirement unsatisfiable by construction.** D-51 §5 required the
   apply report to quote 591's NOTICE "verbatim, including its declared-on-0 / true-on-0 /
   false-on-0 / NULL-on-128 line". No agent could have discharged that, because the runner throws
   the line away. I reported the gap rather than reconstruct the sentence and pass it off as the
   apply's own output (H6).
2. **It suppressed the exact evidence V-31's finding F-A predicted.** F-A says a migration's own
   `BEGIN;`/`COMMIT;` (282 of 443 files, including 588, 589, 590 and 591) breaks migrate.ts's
   documented `BEGIN; <SQL>; INSERT ledger; COMMIT;` atomicity, and PARĪKṢAKA reproduced
   `WARNING: there is already a transaction in progress` / `WARNING: there is no transaction in
   progress` in simulation. **Neither warning appeared in this real apply's 126 lines of stderr.**
   That is not evidence against F-A — it is the same root cause. A structural hazard that
   announces itself at every apply is being announced into a void.
3. **The general shape.** A migration that self-verifies, run by a runner that discards the
   self-verification, leaves an operator unable to distinguish "the detector ran and was green"
   from "no detector exists". Today the only signal that survives is `RAISE EXCEPTION`, i.e.
   failure. §N.8 asks what code path would have to run and fail for a signal to correctly read
   false; here the answer is fine at the SQL layer and broken at the transport layer.

## What I did NOT do

I did not add a notice listener, did not touch `migrate.ts`, and did not re-run the migrator.
This would be a machinery change under §N.8/D-41's DIRECTION test — it STRENGTHENS (it surfaces
warnings that are currently hidden; nothing that fails today would start passing) — but it is
outside M0-T48's scope and it belongs to whoever owns the migrator, with F-A, not to me.

## Evidence

```
grep -n "notice" platform/scripts/migrate.ts   -> 813 (prose only, no handler)
platform/scripts/migrate.ts:849                -> new Pool({ connectionString: process.env.DATABASE_URL })
apply run stdout (4 lines) / stderr (126 lines): grep -i "notice|591|transaction in progress"
  stdout -> only "Applied: 591_nirmana_m0_partition_and_dead_flag_columns.sql"
  stderr -> (nothing)
same DO block re-executed read-only with a notice handler -> NOTICE printed immediately
```

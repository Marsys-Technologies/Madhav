# platform/migrations — Legacy Migration Directory

This directory holds the **original (older) migration sequence** — SQL files applied
before the migration tooling was reorganised under `platform/supabase/migrations/`.

## Two-directory setup

`migrate.ts` reads **both** this directory and `platform/supabase/migrations/`.
It de-duplicates by **filename** (not by number), so each file is applied at most once.

- `platform/supabase/migrations/` is where **new migrations go** (current sequence: 226–236+).
- This directory (`platform/migrations/`) is retained for historical migrations already applied
  to production. Do not add new migrations here.

## Number collisions

Because de-duplication is filename-based, two files with the same leading number but
different names (e.g. `174_ganita_graha_sthana.sql` here vs.
`174_brahmagyan_naming_reconciliation.sql` in supabase/migrations/) are both applied
and tracked independently — this is **functionally safe**.

However, authors should still **pick a fresh number** (i.e. increment beyond the current
highest in both dirs combined) to avoid confusion in audits and the migration log.

## Do not rename or delete applied .sql files

Renaming an already-applied migration changes its filename key, causing it to be
re-applied on the next migrate run — a dangerous double-execution. If a migration needs
to be amended, add a new corrective migration instead.

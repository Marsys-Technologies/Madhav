# platform/supabase/migrations — Current Migration Directory

This is the **active migration directory** for the MARSYS-JIS project.
All new migrations go here. Current sequence: 226–236 (and counting).

## Two-directory setup

`migrate.ts` reads **both** this directory and `platform/migrations/` (the older sequence).
It de-duplicates by **filename** (not by number), so each file is applied at most once.

- **New migrations belong here** — increment beyond the current highest number across both dirs.
- `platform/migrations/` holds the legacy sequence and is kept for historical continuity only.

## Number collisions

Because de-duplication is filename-based, two files with the same leading number but
different names (e.g. `174_brahmagyan_naming_reconciliation.sql` here vs.
`174_ganita_graha_sthana.sql` in platform/migrations/) are both applied and tracked
independently — this is **functionally safe**.

However, authors should still **pick a fresh number** (i.e. increment beyond the current
highest in both dirs combined) to avoid confusion in audits and the migration log.

## Do not rename or delete applied .sql files

Renaming an already-applied migration changes its filename key, causing it to be
re-applied on the next migrate run — a dangerous double-execution. If a migration needs
to be amended, add a new corrective migration instead.

## Governance note

Per `00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md` §N.4, migrations must be
**surgical** — never bulk-auto-applied via deploy.yml. Apply each migration explicitly
and verify before the next one.

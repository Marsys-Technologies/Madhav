# platform/supabase/migrations — Current Migration Directory

This is the **active migration directory** for the MARSYS-JIS project.
All new migrations go here.

> **Governing protocol: `00_ARCHITECTURE/MIGRATION_AND_MERGE_PROTOCOL_v1_0.md`.**
> Read it before allocating a number. It covers the allocation rule, the merge lock, the deploy
> window a merge opens, and the local Cloud SQL Auth Proxy trap.
>
> **Do not compute the next number by hand.** Run:
> ```bash
> cd platform && npm run migration:next
> ```

## Two-directory setup

`migrate.ts` reads **both** this directory and `platform/migrations/` (the older sequence).
It de-duplicates by **filename** (not by number), so each file is applied at most once.

- **New migrations belong here** — increment beyond the current highest number across both dirs.
- `platform/migrations/` holds the legacy sequence and is kept for historical continuity only.

> **This routing rule is not enforced and is being broken.** The single highest number on `main`,
> `platform/migrations/474_asset_throughput_incomplete_state.sql` (2026-07-29), is in the directory
> this README calls legacy. A costed consolidation spec is filed at
> `00_ARCHITECTURE/briefs/samapti/SPEC_MIGRATION_DIRECTORY_CONSOLIDATION_v1_0.md` (PROPOSED — not
> authorized for execution). Until it runs, the MIG-1 guard below is what makes the split safe.

## Number collisions — now a CI failure (MIG-1)

Because de-duplication is filename-based, two files with the same leading number but
different names (e.g. `174_brahmagyan_naming_reconciliation.sql` here vs.
`174_ganita_graha_sthana.sql` in platform/migrations/) are both applied and tracked
independently. That is *functionally* survivable, but it is not safe in practice — it is
how migration **467** came to be claimed by two campaigns at once (`f7160b5c` vs
`455033ed`), untangled only by a manual renumber at merge time.

**A duplicate number across BOTH directories now fails CI.** The guard is
`platform/scripts/ci/migration_number_guard.ts`, run by `.github/workflows/ci.yml` as
the step "MIG-1 — migration number guard". Check locally before opening a PR:

```bash
cd platform && npm run guard:migration-numbers
```

The 35 duplicate groups that predate the guard are frozen in
`migration_number_legacy_duplicates.json`. **Do not add an entry there to silence a new
collision** — renumber your file. Note that a same-*filename* collision across the two
directories is worse than a same-number one: the second copy is silently skipped and its
SQL never runs. The guard fails on that unconditionally.

## Do not rename or delete applied .sql files

Renaming an already-applied migration changes its filename key, causing it to be
re-applied on the next migrate run — a dangerous double-execution. If a migration needs
to be amended, add a new corrective migration instead.

## Governance note

Per `00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md` §N.4, migrations must be
**surgical** — never bulk-auto-applied via deploy.yml. Apply each migration explicitly
and verify before the next one.

> **Live discrepancy, recorded not resolved.** `.github/workflows/deploy.yml` (job
> `deploy-web`, step "Run database migrations") *does* run `npx tsx scripts/migrate.ts`
> in bulk on every deploy to `main`. The doctrine line above and the pipeline disagree.
> Treat every merge to `main` as a production migration run until one of them moves.
> See `MIGRATION_AND_MERGE_PROTOCOL_v1_0.md` §5 and its residual R3.

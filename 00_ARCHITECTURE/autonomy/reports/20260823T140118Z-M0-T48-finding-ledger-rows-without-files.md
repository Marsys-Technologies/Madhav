# FINDING — 8 `_migrations_applied` rows have no file on disk, one of them the D-5 588 collision

**From:** KARAKA-M0-T48 (measured while running M0-T48's disk-vs-ledger diff)
**Severity:** low / record-keeping. Pre-existing, disclosed by the runner itself.
**Status:** NOT FIXED, NOT INVESTIGATED beyond enumeration. Out of scope.

After 591 applied: **451 ledger rows, 443 `.sql` files on disk** across
`platform/migrations` + `platform/supabase/migrations`. `migrate.ts` discloses the gap in its own
summary ("including any whose file is no longer on disk"), so nothing is concealed — but the set
is not written down anywhere I could find, so here it is, read-only:

```
id   1  118_build_events.sql
id   2  124_builds.sql
id   3  125_build_steps.sql
id   4  126_engine_versions.sql
id   5  127_build_notifications.sql
id   6  133_notification_views.sql
id 337  456_lel_schema_v2_event_shapes.sql
id 447  588_samiksha_digest_journal.sql
```

Two are worth naming:

- **id 337 `456_lel_schema_v2_event_shapes.sql`** is the known 456→457 renumber that
  `migrate.ts`'s `assertNotRenumberedReapply()` docstring cites by number.
- **id 447 `588_samiksha_digest_journal.sql`** is a **different 588** from the campaign's
  `588_remove_asset_build_protection.sql`. This is the D-5 number collision, and it is still
  visible in the live ledger as a row whose file is gone. Anyone reasoning about "588" from the
  ledger alone will hit two different migrations under one number.

ids 1–6 are the earliest tracked rows and look like a pre-tracking-era artifact; I did not trace
them and am not claiming a cause.

I did not delete, edit, backfill or reconcile anything. This is an observation.

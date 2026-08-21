---
canonical_id: F188_ACCRETION_EXCEPTION
version: 1.0
status: CURRENT
campaign: PARIŚEṢA-V4
finding: F-188
authored: 2026-08-22
authored_by: PARIŚEṢA-V4 repair lane (GA-2 authority)
execution_status: IMPLEMENTED — count_sql corrected (migration 585, renumbered from 584 pre-merge — see §5 note); accretion behaviour ratified as-is, not changed
---

# F-188 — `mimamsa_calibration_snapshot` is a RATIFIED exception to CLAUDE.md §N.3

## §1 — What this document is

The doctrine record for F-188's ratified exception. This is **not** a bug report against
`mi_gunanaka.py::_publish_snapshot()` — the accretion behaviour it documents is correct and
intentional. The defect this finding actually closes was the **silence**: the exception existed
in code with no doctrine citation, and `asset_registry.count_sql` for `mi_gunanaka` had never been
updated to count the table the exception applies to. Both are fixed by this finding's PR
(`platform/supabase/migrations/585_mi_gunanaka_count_sql_accretion_fix.sql` +
`platform/scripts/seed/asset_registry_seed.ts`'s `mi_gunanaka` entry). Nothing about
`_publish_snapshot()`'s behaviour changes here — see §5.

**CLAUDE.md itself is not edited by this note or this PR.** Amending CLAUDE.md §N.3 requires
native authorization and a version bump (CLAUDE.md §L, §D). This document records a scoped,
per-asset exception to the standard as it already exists; it does not alter the standard's text.

## §2 — The rule this is an exception to

CLAUDE.md §N.3 — Idempotency standard per layer:

> **L1+ (Gaṇita, Bodha, …):** per-chart **delete-then-insert** scoped to `(chart_id × natural
> key)`. Rebuild REPLACES, never accretes.

`mi_gunanaka` is an L5 (Mīmāṃsā) writer and is bound by this standard for the same reason every
L1+ writer is: a rebuild must be safe to re-run without silently growing a table forever.

## §3 — Where the exception lives, and what it looks like

`platform/python-sidecar/pipeline/orchestrator/writers/mi_gunanaka.py::run()` writes to **two**
tables, with two different idempotency disciplines:

| Table | Discipline | Where |
|---|---|---|
| `mimamsa_multipliers` | **Ordinary §N.3** — `DELETE FROM mimamsa_multipliers WHERE chart_id = %s` immediately before the `INSERT`. | `mi_gunanaka.py` (`run()`, delete at the top of the write block) |
| `mimamsa_calibration_snapshot` | **Exception** — no delete. `_publish_snapshot()` inserts a new row every call, keyed on a `snapshot_id` that embeds `int(time.time())` (`f"snap_{str(chart_id)[:8]}_{int(time.time())}"`), with `ON CONFLICT (snapshot_id) DO NOTHING`. | `mi_gunanaka.py::_publish_snapshot()` |

Because the key embeds wall-clock time, **every rebuild inserts a distinct new row** — the table
accretes across rebuilds, chart-scoped but never truncated. Confirmed live in production, chart
`482012f1-710e-4a25-994a-93821f5871aa`: **4** `mimamsa_calibration_snapshot` rows against **9**
`mimamsa_multipliers` rows for the same chart (2026-08-22) — the multipliers table holds a stable
per-rebuild count exactly as §N.3 predicts; the snapshot table does not, by design.

## §4 — Why the exception is correct, not a bug

`mimamsa_calibration_snapshot` is the **append-only historical record** the L5 calibration loop
reads. Its own table comment (`platform/supabase/migrations/400_mimamsa_p6_schema.sql`) states:

> BA-P6 Step 4: Two-key versioned calibration snapshots. key-1 = proposing_executor
> (mi_gunanaka write), key-2 = Ācārya-Pratinidhi (native sign-off). Both keys required for
> publication_status=published. Snapshot flows to exactly three sinks: bg_class_priors overlay,
> anchor lift calibrations, triangulation tradition-weights.

Two-key publication is the load-bearing reason a delete-then-insert cannot apply here: a snapshot
proposed by `mi_gunanaka` (key-1) may still be awaiting native sign-off (key-2,
`two_key_complete = false`) when the next rebuild runs. A delete-then-insert on this table would
destroy that pending proposal — and every prior published snapshot the calibration loop's
downstream sinks (class priors, anchor lift, triangulation weights) already depend on — the exact
opposite of what a versioned historical record exists to guarantee. Replacing history is not a
rebuild of this asset; it is data loss of a different asset's dependency.

This is the same "honest tier over a broadcast/fabricated claim" reasoning CLAUDE.md §N.4 already
applies to `ga_sensitive`'s `single`-tier ruling — an exception earns ratification by being the
behaviour the table's actual contract requires, not by convenience.

## §5 — Disposition: no behaviour change, two documentation fixes + one count_sql fix

1. **`mi_gunanaka.py::_publish_snapshot()` docstring** — appended, citing this ruling by date
   (2026-08-22) and this document by path. No code path changed.
2. **This document** — the doctrine note CLAUDE.md §N.3 itself does not carry (and, per §L,
   cannot without native authorization); this is where the exception is recorded for audit.

   **Migration renumbering note:** the migration carrying this fix was originally authored as
   584, then renumbered to **585** before either it or the colliding PR merged — migration 584
   was independently claimed by PR #1448 (F-187, `584_remedy_review_queue_remedy_id_unique.sql`),
   a different finding's fix authored in parallel. F-187 kept 584; this finding's migration moved
   to the next free slot. This is a pre-merge renumber, not a post-apply edit — CLAUDE.md §N.4's
   "never edit an applied migration" rule was not implicated, since neither file had applied.
3. **`asset_registry.count_sql` for `mi_gunanaka`** — corrected (migration 585 +
   `asset_registry_seed.ts`) from a single-table count that silently missed the accretion table
   to a two-table sum. This is the "Cockpit truth" half of CLAUDE.md §N.4 ("each asset needs a
   correct chart-scoped `count_sql`") — an asset whose data model *includes* a ratified accretion
   table must still report a `count_sql` that reflects everything it owns, accretion included.
   Undercounting the accretion table is a defect independent of whether the accretion itself is
   ratified.

## §6 — Scope of the ratification

This exception is scoped to `mimamsa_calibration_snapshot` written by `mi_gunanaka` specifically.
It is **not** a blanket carve-out for L5, for Mīmāṃsā, or for any other accretion-shaped table
elsewhere in the codebase — each such table needs its own ratification citing its own reason, the
same way this one does. A future session finding an unexplained accreting L2+ table should treat
it as an open §N.3 violation until a doctrine note like this one exists for it, not assume this
precedent covers it by analogy.

## §7 — Verification

- Live query confirming the asymmetry (2026-08-22, chart `482012f1`):
  `mimamsa_multipliers` = 9 rows, `mimamsa_calibration_snapshot` = 4 rows, both `chart_id`-scoped.
- Corrected `count_sql` verified to return **13** (9 + 4) for the same chart — see migration 585's
  header and the F-188 test suite (`platform/python-sidecar/tests/test_f188_mi_gunanaka_count_sql.py`).
- Source-level parity: `asset_registry_seed.ts`'s `mi_gunanaka.count_sql` literal and migration
  585's `UPDATE ... SET count_sql` literal are asserted identical by the same test suite (the
  F-146 defect class — a seed and a migration silently diverging on the same field — applied
  here as a regression guard rather than found as a live defect).

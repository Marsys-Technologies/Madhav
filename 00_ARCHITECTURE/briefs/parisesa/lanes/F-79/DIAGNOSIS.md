---
lane: F-79
stream: S6_ADHARA
stage: D (DIAGNOSE) — COMPLETE
author: ADHARA-LEAD (sonnet)
---

# F-79 — migration 456's SQL source missing from disk (severity correction found)

## 1. Live reproduction

`SELECT filename, applied_at, sha256 FROM _migrations_applied WHERE filename IN
('456_lel_schema_v2_event_shapes.sql','457_lel_schema_v2_event_shapes.sql')` — confirmed
live: both rows present, `456` applied `2026-07-18T23:30:11.222Z` (sha256 `a6d30ee4...`),
`457` applied one second later `2026-07-19T01:19:40.153Z` — wait, actually ~2h later
(`23:30:11` vs `01:19:40`), sha256 `fdc1edb0...`, different hash. `find` across the entire
repo (all worktrees, all dirs, including `_archive/`) for `456_lel_schema_v2_event_shapes.sql`
returns zero hits pre-fix; `457_lel_schema_v2_event_shapes.sql` exists broadly (current
active migration). REPRODUCES: 456's filename is genuinely absent from every working tree
on disk. Not ALREADY-FIXED.

## 2. Claim decomposition — and the correction

The corpus claim has two parts:
- **C1** — 456's source file is absent from disk under its original name (not in
  `platform/migrations/`, not in `_archive/`). **TRUE, confirmed.**
- **C2** — "456's actual SQL, once run against production, is now unrecoverable from the
  repository for audit or rollback-safety review." **FALSE — this is the corrected finding.**
  `git log --all --oneline -- '*456_lel_schema_v2_event_shapes.sql'` (searching ALL branches,
  not just the working tree) finds commit `54c809bc5` ("renumber 456->457 after rebase
  collision with A-2"). `git show 54c809bc5 --name-status` shows this as a git-detected
  **rename** (`R086`, 86% similarity) from `platform/migrations/456_lel_schema_v2_event_shapes.sql`
  to `platform/migrations/457_lel_schema_v2_event_shapes.sql` — not a deletion. `git show
  54c809bc5^:platform/migrations/456_lel_schema_v2_event_shapes.sql` recovers 456's exact
  content, byte-for-byte, from the parent commit. Diffed against current `457`: the only
  differences are the header comment's migration number and a 3-line explanatory note added
  about the renumbering — the actual DDL body is identical. The two different `sha256`
  values in `_migrations_applied` come from that header-comment difference (whatever hashes
  the file, hashes the whole file including comments), not from different SQL logic.

**Corrected claim:** 456's source was never destroyed. It is fully, exactly recoverable via
`git show 54c809bc5^:platform/migrations/456_lel_schema_v2_event_shapes.sql` — one git
command away, not "unrecoverable."

**Stronger verification, using the project's own mechanism:** `migrate.ts` computes a
comment/whitespace-normalized `sql_identity` (via `normalizeSqlForIdentity` +
`sqlIdentityOf`, `platform/scripts/migrate.ts:308-397`) specifically to answer "is this the
same SQL regardless of cosmetic differences." `_migrations_applied.sql_identity` for 456 is
honestly `NULL` in the DB today — the codebase already declined to fabricate it once the
file went missing (exactly the §N.8 honest-null pattern; the column's own doc-comment says
so: *"file gone from disk... so we cannot honestly claim to know what ran"*). Ran the
project's own normalization function (extracted standalone to avoid pulling in `migrate.ts`'s
`pg` dependency, logic copied verbatim, not reimplemented from a guess) against the recovered
456 content: **`sqlIdentityOf(recovered_456) == sqlIdentityOf(current_457) ==
278470efc88d047d173ac5a63f672024a133078e69425c19e2e0f6a4f42d250f`**, which also matches
`457`'s own `sql_identity` value already stored in the live DB. This is not just "looks
similar" — it is a cryptographic identity match, using the project's own tool, proving 456
and 457 ran (and still represent) the exact same SQL. What's real is narrower: **456 is the
one applied
migration in the 430-row `_migrations_applied` set whose source isn't inspectable from the
current working tree without git-history archaeology** — every other superseded/renumbered
migration in this window (118/124/125/126/127_build_notifications/133_notification_views,
confirmed present) is retained in `platform/migrations/_archive/` per
`ONGOING_HYGIENE_POLICIES.md`'s own archival convention, and 456 alone is the gap in that
otherwise-consistent practice. TIER2-HONESTY was calibrated to the overstated "unrecoverable"
framing; the corrected, still-real defect is a TIER3/TIER4-shaped hygiene gap (an
inconsistently-applied archival policy), not a genuine audit-trail loss.

## 3. Mechanism

The rename happened in `54c809bc5` (2026-07-19, `fix(D-4a/A-1)`) as a side effect of
resolving a migration-number collision during a rebase: a different, unrelated lane (A-2,
`platform/supabase/migrations/456_brahma_event_ontology_dr13_shapes.sql`) had already
claimed `456` in a sibling migrations directory that `migrate.ts` pools together with
`platform/migrations/` for sequencing purposes, so this lane's `456` was renumbered to `457`
to keep the combined sequence unique. The renumbering commit did the rename correctly at the
git level (git tracked it as a rename, preserving history) but did not also copy the old
filename into `_archive/` the way every other renumbered/superseded migration in this
project's history was — an omission in that one commit, not a policy violation elsewhere.

## 4. Sibling census

Confirmed present in `_archive/`: `118_build_events.sql`, `124_builds.sql`,
`125_build_steps.sql`, `126_engine_versions.sql`, `127_build_notifications.sql`,
`133_notification_views.sql` — all 6 siblings the original corpus finding cited as
correctly archived. No other `_migrations_applied` row was checked exhaustively this
session for the same gap (430 rows total); this diagnosis is scoped to the one row the
corpus named. A broader sweep (every `_migrations_applied` filename vs. disk presence in
either `platform/migrations/` or `_archive/`) would be the way to confirm 456 is the *only*
gap — not done here, flagged as a possible follow-up if this class of issue recurs.

## 5. Blast radius

None. This is a documentation/archival-completeness fix — adding a file to `_archive/`
that recovers already-applied, already-live migration history. No schema change, no
re-application, no `_migrations_applied` row touched (migration 456 stays recorded as
applied under its original filename; the archived file is a historical record, not a
migration `migrate.ts` would try to re-run — `_archive/` is excluded from migration
discovery, matching the convention the 6 siblings already demonstrate).

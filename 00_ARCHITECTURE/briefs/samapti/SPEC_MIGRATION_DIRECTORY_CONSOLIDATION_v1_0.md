---
artifact: SPEC_MIGRATION_DIRECTORY_CONSOLIDATION_v1_0.md
canonical_id: SPEC_MIGRATION_DIRECTORY_CONSOLIDATION
version: 1.0
status: PROPOSED — NOT AUTHORIZED FOR EXECUTION
authored_by: SAMĀPTI lane B-MIGGUARD (Claude Code, Opus) 2026-07-30
authorization: >
  SAMAPTI_IMPLEMENTATION_BRIEF_v2_0.md §4.4(c) directs this lane to RECORD whether the
  two-directory split is intentional and, if it is not, to FILE A COSTED SPEC rather than perform
  the consolidation — explicitly out of that brief's authorization. This document is that spec.
  No file was moved. Executing it requires a separate, native-authorized session.
governs: platform/migrations/ · platform/supabase/migrations/
depends_on: >
  00_ARCHITECTURE/MIGRATION_AND_MERGE_PROTOCOL_v1_0.md (the guard and the allocation rule this
  spec assumes are already in place)
baseline_commit: 5f5033a5
---

# Costed Spec — Consolidating the Two Migration Directories

## §1 — The finding

`main` carries two migration directories over one number sequence:

| Directory | Numbered `.sql` | Unnumbered `.sql` | `_archive/` | Highest |
|---|---|---|---|---|
| `platform/migrations/` | 127 | 27 (`brahma_*`, `ws2_*`, `v13_*`) | 124 files | **474** |
| `platform/supabase/migrations/` | 201 | 0 | 30 files | **473** |

**Is the split intentional?** *Partly, and it is no longer honored.*

`platform/supabase/migrations/README.md` designs it deliberately — one active directory, one
legacy directory retained for continuity, `migrate.ts` reading both — and even names the number
collision behaviour, calling it "functionally safe."

But the README's own routing rule ("new migrations belong here") is unenforced and is being
broken: the single highest number on `main`,
`platform/migrations/474_asset_throughput_incomplete_state.sql` (2026-07-29), is in the *legacy*
directory. A directory declared closed that keeps receiving files is not a legacy directory; it is
a second active directory that nobody is treating as one.

**Consequences on record:** 35 duplicate-number groups; migration 467 claimed concurrently by two
campaigns (`f7160b5c` PB-2 vs `455033ed` SATYA-DĪPA) and untangled by a manual renumber
(`75a5d9e6`); 15 files whose header comment disagrees with their own filename.

**Disposition: recorded as unintentional-in-effect.** The MIG-1 CI guard makes the split *safe to
live with*. It does not make it correct, and it does not stop the legacy directory from growing.

---

## §2 — Why this is far cheaper than it looks

Three properties of the current runner make consolidation a **rename-free file move**, which is
the difference between a half-day and a multi-day migration project. Each was verified against
`platform/scripts/migrate.ts` at `5f5033a5`:

1. **`_migrations_applied` is keyed on the bare filename, not on a path.**
   `runMigrations` does `applied.has(file.name)`. Moving a file between directories does not
   change `file.name`, so **an already-applied migration stays applied and is not re-executed.**
   This is the single fact that makes the whole operation safe.

2. **Apply order is already a single global filename sort.**
   `collectMigrationFiles` pushes both directories and then runs
   `files.sort((a, b) => a.name.localeCompare(b.name))` across the combined list. Order is
   therefore *already* directory-independent. **A fresh-database bootstrap replays in exactly the
   same order after consolidation as before it.**

3. **There are zero identical filenames across the two directories.**
   Verified by the MIG-1 guard's E1 check (currently 0). So every move is a clean move — no
   overwrite, no merge, no filename disambiguation needed.

**The corollary is a hard constraint:** consolidation must be **move-only**. Renaming any applied
`.sql` file — including "tidying up" a duplicate number — changes its `_migrations_applied` key and
causes a **re-execution on the next deploy**. The supabase README already warns about this in bold.
**The 35 legacy duplicate numbers must be left exactly as they are.** They are ugly; they are not
worth a double-execution.

---

## §3 — Recommended option

Three options were considered.

| Option | Description | Cost | Residual risk | Verdict |
|---|---|---|---|---|
| **A — Do nothing** | Keep both directories; rely on the MIG-1 guard. | 0 | Legacy directory keeps growing; every new session must learn the two-directory rule; audits stay confusing. | Acceptable fallback, not a resolution |
| **B — Move-only consolidation** *(recommended)* | `git mv` every `.sql` from `platform/migrations/` into `platform/supabase/migrations/`. No renames, no renumbering. Retire the source directory. | **~5.5 h** | Low — see §5 | **Recommended** |
| **C — Consolidate + renumber to a clean sequence** | B, plus renumber the 35 duplicate groups into a gapless sequence. | ~5.5 h + 3–4 d + a production replay window | **High** — every rename re-executes on the next deploy unless `_migrations_applied` is hand-patched in production in the same transaction. | **Rejected** — cost and blast radius are not justified by cosmetics |

---

## §4 — Option B, phased

**Total: ~5.5 engineering hours, one merge-lock window, no database write.**

| Phase | Work | Est. |
|---|---|---|
| **P0 — Pre-flight** | On `origin/main`: confirm E1 = 0 (`npm run guard:migration-numbers`); snapshot `SELECT filename FROM _migrations_applied ORDER BY filename` to a file; confirm `npx tsx scripts/migrate.ts --dry-run` against production returns **empty** (nothing pending). A non-empty dry-run means production is behind `main` — **stop and resolve that first**. | 0.5 h |
| **P1 — Move** | `git mv platform/migrations/*.sql platform/supabase/migrations/`. 154 files (127 numbered + 27 unnumbered). Decide `_archive/` (124 files) → recommended: `git mv platform/migrations/_archive platform/supabase/migrations/_archive_legacy` (keeping it distinct from the existing 30-file `_archive/`). Move `platform/migrations/__tests__/` (4 Python files) alongside. Verify with `git status` that every entry is `R` (rename), **zero `A`/`D` pairs** — a delete+add means the content changed. | 1.0 h |
| **P2 — Update referrers** | Only **documentation-comment** references exist — no code resolves the path at runtime. Update: `python-sidecar/services/gochara_grammar/citations.py:85,94`, `sarvatobhadra.py:9,16`, `panchanga_daily_writer.py:5`, plus `platform/supabase/migrations/README.md` (rewrite the "Two-directory setup" section). `migrate.ts` keeps both directory entries — an absent directory is skipped by `if (!fs.existsSync(dir)) continue`, so nothing breaks if the path lingers; remove the stale entry for cleanliness. | 1.0 h |
| **P3 — Update MIG-1** | `MIGRATION_DIRS` in `platform/scripts/ci/migration_number_guard.ts` becomes single-entry (keep the array shape — it is what makes re-splitting detectable). Regenerate `migration_number_legacy_duplicates.json`: **the same 35 groups with rewritten paths, not a fresh capture.** Update `migration_number_guard.test.ts` (the E1/E2 cross-directory cases become within-directory cases; keep them). Update `MIGRATION_AND_MERGE_PROTOCOL_v1_0.md` §1/§2/§7 and bump to v1.1. | 1.5 h |
| **P4 — Prove it** | (a) `migrate.ts --dry-run` against production returns empty *after* the move — **the load-bearing check: it proves nothing was orphaned or resurrected**; (b) fresh-DB replay into a scratch Postgres, then diff the resulting `_migrations_applied` filename list against the P0 snapshot — must be identical, same order; (c) `npm test` + `npm run guard:migration-numbers` green; (d) can-fail the updated guard once. | 1.0 h |
| **P5 — Merge** | Single PR under merge lock per `MIGRATION_AND_MERGE_PROTOCOL` §4. Watch the deploy; confirm the deploy-web `migrate.ts` step applies **zero** migrations. | 0.5 h |

**Explicitly out of scope:** renumbering anything; touching `_archive/` contents; any write to
`_migrations_applied`; any change to `runMigrations` logic.

---

## §5 — Risk register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | A move is recorded as delete+add with modified content, changing a file's SHA | Low | Low — `_migrations_applied` stores a sha256 but the runner never compares it on the skip path (`applied.has(name)` only) | P1 verifies every entry is a git rename |
| R2 | An accidental rename re-executes an applied migration on the next deploy | Low | **High** — arbitrary DDL replays against production | P1 zero-`A`/`D` check + P4(a) empty dry-run, which would list any resurrected file by name |
| R3 | Production is behind `main` when the move lands, so the post-move dry-run is non-empty for an unrelated reason and masks R2 | Medium | High | P0 requires an empty dry-run **before** starting; do not proceed otherwise |
| R4 | Fresh-DB bootstrap order changes | **Very low** — order is already a global filename sort (§2.2) | High | P4(b) full replay + ordered diff |
| R5 | A concurrent campaign adds a file to `platform/migrations/` mid-flight | Medium (multiple active campaigns) | Low | Do it in one merge-lock window; re-run P0 immediately before merge |
| R6 | The stale `platform/migrations` entry is left in `migrate.ts` and someone re-creates the directory later | Medium | Medium | Keep MIG-1's `MIGRATION_DIRS` as an array so a re-split is still scanned, not silently ignored |

---

## §6 — Acceptance criteria

1. `platform/migrations/` contains no `.sql` files; the directory is deleted or holds only
   `_archive`-class content, and the decision is stated in `README.md`.
2. `git log --follow` still resolves the history of a sampled moved migration.
3. `migrate.ts --dry-run` against production returns **empty** both before and after.
4. A fresh-DB replay produces an `_migrations_applied` filename list byte-identical, and in the
   same order, to the pre-move production snapshot.
5. The MIG-1 guard passes, its baseline still describes **35** groups (paths rewritten, membership
   unchanged), and its can-fail proof is re-run and recorded.
6. `MIGRATION_AND_MERGE_PROTOCOL_v1_0.md` bumped to v1.1 with §1/§2/§7 rewritten; residuals R2 and
   R4 in that document's §7 closed.
7. The deploy triggered by the merge applies **zero** migrations.

---

## §7 — Recommendation

**Execute Option B**, as one dedicated session under merge lock, **after** the SAMĀPTI run's other
lanes are terminal — moving 154 files while eight lanes hold worktrees cut from `origin/main`
would force a rebase conflict on every lane that touches a migration.

Until then, **Option A holds and is genuinely safe**: the MIG-1 guard blocks the collision class at
CI, which is the part that was actually costing time.

---

*End of SPEC_MIGRATION_DIRECTORY_CONSOLIDATION v1.0 — PROPOSED, not authorized for execution.*

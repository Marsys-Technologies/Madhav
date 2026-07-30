---
artifact: MIGRATION_AND_MERGE_PROTOCOL_v1_0.md
canonical_id: MIGRATION_AND_MERGE_PROTOCOL
version: 1.3
status: CURRENT
authored_by: SAMĀPTI lane B-MIGGUARD (Claude Code, Opus) 2026-07-30
implements: >
  SAMAPTI_IMPLEMENTATION_BRIEF_v2_0.md §4.3 (codify the merge-lock + deploy-window protocol),
  §4.4 (kill the migration-collision class at the root — MIG-1), §4.5 (the local Postgres proxy
  standing note). Enforcement surface: platform/scripts/ci/migration_number_guard.ts, wired into
  .github/workflows/ci.yml as the "MIG-1 — migration number guard" step.
purpose: >
  The standing protocol for allocating a migration number, taking the merge lock, and reading the
  deploy window that a merge to main opens. Written so future sessions inherit these rules instead
  of rediscovering them — the specific failure this document exists to prevent is a migration
  number being independently claimed by two concurrent campaigns.
supersedes: nothing (first issue)
---

# Migration & Merge Protocol

Binding on every session, campaign, and autonomous lane that merges to `main`.

Three things in this document are load-bearing, and each one is here because it was learned the
expensive way:

1. **§3 — how to pick a migration number.** Reading one directory is wrong. It has been wrong at
   least twice in recorded history.
2. **§4 — the merge lock.** "No open PR" is not the same as "nobody is working."
3. **§5 — the deploy window.** A merge to `main` is a production deploy *and* a production
   migration run. It is not a code checkpoint.

§6 records the local Cloud SQL Auth Proxy trap. §7 records the two-directory question and its
disposition.

---

## §1 — The two migration directories (the ground truth)

`main` carries **two** migration directories that share **one** number sequence:

| Directory | Numbered `.sql` files | Highest number | README's stated role |
|---|---|---|---|
| `platform/migrations/` | 127 | **474** | "legacy sequence … kept for historical continuity only" |
| `platform/supabase/migrations/` | 201 | **473** | "the **active** migration directory … all new migrations go here" |

*(Counts as of `5f5033a5`, 2026-07-30. `npm run guard:migration-numbers` prints them live.)*

`platform/scripts/migrate.ts` reads **both** (`collectMigrationFiles`), concatenates them, sorts by
filename, and applies anything whose **filename** is not already a row in `_migrations_applied`.

Three consequences follow, and all three matter:

- **The number is not a key of anything.** It orders nothing that the runner relies on and
  uniquely identifies nothing. It is a *human coordination token*, and until MIG-1 nothing
  enforced it.
- **Same number, different filenames → both apply.** Functionally survivable (the supabase README
  says so), but it destroys the audit trail and is how two campaigns end up believing they own the
  same slot.
- **Same *filename* in both directories → one is silently skipped.** `_migrations_applied` is keyed
  on the bare filename, so the second copy's SQL never runs and nothing reports a problem. This is
  the genuinely dangerous case. Zero instances exist today; the guard treats it as a hard,
  never-allowlisted failure.

### The incident this protocol exists to prevent

Migration **467** was claimed twice, concurrently, on two branches:

| Commit | File | Campaign |
|---|---|---|
| `f7160b5c` | `platform/supabase/migrations/467_pariprashna_canonical_message_parts.sql` | PB-2 SMṚTI |
| `455033ed` | `platform/migrations/467_asset_throughput_incomplete_state.sql` | SATYA-DĪPA |

Both authors computed "the next free number" correctly *within the directory they were looking at*.
It was untangled by hand at merge time (`75a5d9e6` — "renumber migration 467→474 after rebase onto
main"), and the renumber left the file's own header comment still reading `-- Migration 467:` — a
defect still open on `main` today.

---

## §2 — Where a new migration goes

**`platform/supabase/migrations/`.** Always, per that directory's own README.

`platform/migrations/` is the legacy sequence and should receive no new files. Note that this rule
was violated as recently as `474_asset_throughput_incomplete_state.sql` (2026-07-29) — the
directory choice is not currently enforced by any check (see §7 residuals).

Filename form: `<NNN>_<snake_case_description>.sql`. Do **not** use the letter-suffix form
(`346a_…`) to dodge a taken number — it is a legacy workaround, only two instances exist, and the
guard scores `346a` as a claim on `346` precisely so it cannot be used as a bypass.

---

## §3 — Allocating the number (THE RULE)

> **`next = max(highest in platform/migrations/, highest in platform/supabase/migrations/) + 1`**
>
> read from **`origin/main`**, and **re-checked immediately before merge**.

Run it, don't compute it:

```bash
cd platform && npm run migration:next        # → 475
```

**Two reads, not one.** At authoring time you pick a number so you can write the file. At merge
time the number may have been taken by a lane that merged while you were working. In an autonomous
swarm the merge-time read is the authoritative one — under
`00_ARCHITECTURE/CONDUCTOR/SAMAPTI_CONDUCTOR_PROMPT_v1_0.md` §5 the **Conductor allocates the
number at the moment MERGE-LOCK is taken**, not when the builder writes the file.

**Write the number in two places and keep them in sync through any renumber:**

1. the filename, and
2. the file's internal header comment (`-- Migration 475: <what it does>`).

The 467→474 renumber updated only the filename. **Seventeen** files on `main` currently disagree
with their own header — the full register, and the Dvārapāla ruling that keeps the check
non-blocking, are in §3.1.

### The CI guard

`platform/scripts/ci/migration_number_guard.ts`, run by `.github/workflows/ci.yml` in the
`unit-tests` job as **"MIG-1 — migration number guard"**, before `npm test`. Also exercised by
`platform/tests/unit/migrations/migration_number_guard.test.ts` under `npm test`.

| Class | Behaviour |
|---|---|
| **E1** identical filename in both directories | **fails CI** — never allowlisted (silent-skip hazard) |
| **E2** duplicate number not in the frozen baseline | **fails CI** — this is the 467 class |
| **E3** a new file added to a *baselined legacy* duplicate group | **fails CI** — an old collision is not cover for a new one |
| header/filename number mismatch | **advisory warning, never fatal** (see below) |

The 35 duplicate numbers that already existed when the guard was written are frozen in
`platform/scripts/ci/migration_number_legacy_duplicates.json`, keyed to **exact file lists** rather
than bare numbers. **Do not add entries to that file to silence a new collision** — renumber the
file instead. Widening the baseline is the one way to defeat this guard, and doing so is a
governance violation, not a fix.

The header-mismatch check is deliberately non-fatal and says so in its own docstring. This is a
standing constraint under **Dvārapāla RULING 44**, not an oversight — see §3.1.

Locally, before you open a PR:

```bash
cd platform && npm run guard:migration-numbers
```

### §3.1 — The header/filename mismatch register (17 files) · Dvārapāla RULING 44

**Ruling:** the duplicate-number checks (E1/E2/E3) are **blocking**. The header-consistency check
is **WARN-ONLY** and must stay that way until this backlog is cleared. All 17 predate the MIG-1
campaign; a blocking check would turn `main` red the moment the guard merged, on 17 defects this
campaign did not create, which would read exactly like a regression it introduced.

**Status:** these are **comment-only** defects with **no functional SQL effect** — the applied SQL
is correct and live in production. Fixing them is **authorized but not required**, and not blocking
for any lane. They were left unfixed by B-MIGGUARD under CONDUCTOR_PROMPT §9 ("report residuals
rather than fixing them out of lane") — editing 17 historical migrations mid-run, while eight lanes
hold worktrees cut from `origin/main`, buys a cosmetic gain at the price of avoidable conflicts.

Reproduce this table at any time with `cd platform && npm run guard:migration-numbers`.

| # | File | Filename says | Header says |
|---|---|---|---|
| 1 | `platform/migrations/474_asset_throughput_incomplete_state.sql` | 474 | 467 |
| 2 | `platform/supabase/migrations/182_bg_ephemeris_target_floor_825084.sql` | 182 | 174 |
| 3 | `platform/supabase/migrations/209_ga5_sensitive_points_mv.sql` | 209 | 208 |
| 4 | `platform/supabase/migrations/210_ga6_chart_divisionals_extension.sql` | 210 | 209 |
| 5 | `platform/supabase/migrations/211_ga7_dashas_kp_sublevel.sql` | 211 | 208 |
| 6 | `platform/supabase/migrations/225_fix_asset_throughput_pk.sql` | 225 | 171 |
| 7 | `platform/supabase/migrations/227_ga_structural_floor_update.sql` | 227 | 220 |
| 8 | `platform/supabase/migrations/237_drop_signal_type_registry.sql` | 237 | 226 |
| 9 | `platform/supabase/migrations/335_phala_rectification.sql` | 335 | 333 |
| 10 | `platform/supabase/migrations/336_phala_rectification_best.sql` | 336 | 334 |
| 11 | `platform/supabase/migrations/337_phala_sankrama.sql` | 337 | 335 |
| 12 | `platform/supabase/migrations/338_phala_pramana.sql` | 338 | 336 |
| 13 | `platform/supabase/migrations/339_phala_phaladesa.sql` | 339 | 337 |
| 14 | `platform/supabase/migrations/340_kala_convergence_horizon_tier.sql` | 340 | 338 |
| 15 | `platform/supabase/migrations/341_school_consensus_tables.sql` | 341 | 340 |
| 16 | `platform/supabase/migrations/369_ga_nakshatra_structural_count_fix.sql` | 369 | 368 |
| 17 | `platform/supabase/migrations/433_bodha_cgm_edges_constituent_fact_ids.sql` | 433 | 431 |

**Row 1** is the 467→474 renumber (`75a5d9e6`) that updated the filename and not the header —
the original incident. **Rows 9–15** are a contiguous 335–341 run drifting 1–3 behind, i.e. a
whole block was renumbered once and the headers were not carried along.

**Two detection notes, both load-bearing:**

- **Scan the whole file, not a prefix.** Rows 7 and 8 declare their header at lines 24 and 10.
  A 5-line window — the guard's first implementation — reported **15 of 17**. An advisory that
  silently under-counts is worse than none, because it invites the reader to treat the list as
  complete.
- **`183_bg_texts_and_text_dependent_floors.sql` is NOT a mismatch.** It contains
  *"never set by migration 174 or 179"* in running prose and carries no `-- Migration N`
  declaration. A looser grep scores it as an 18th row; it is a false positive. The guard matches
  only the declaration form anchored at the start of a comment line.

**2026-07-30 re-verification (independent):** re-ran `npm run guard:migration-numbers` against
this branch's tip — reports exactly **17**, identical set. Confirms the register above is still
accurate and the whole-file scan (not the original 5-line-window advisory) is what's live.

### §3.2 — The tracker's own sha256 was recorded but never checked · Dvārapāla RULING 58

**The defect (now fixed):** `migrate.ts`'s `_migrations_applied` table has always recorded a
`sha256` of each migration's SQL at apply time, but until this fix nothing ever read it back.
`getApplied()` returned filenames only; `runMigrations` decided "already applied, skip" on
**filename alone**. Two hazards followed from this, both empirically confirmed on `main`
(migrations 461–466 recorded as applied *twice* under different filenames; 474 avoided a triple
apply only by luck of renumbering order):

1. **Editing an already-applied migration's SQL was silently skipped forever.** The filename was
   already in the tracker, so the edited content never ran again — deploy reports success, the
   new SQL never executes, and the stored `sha256` now disagrees with the file on disk with
   nothing checking. This is the literal mechanism the `[[feedback-deploy-migrations-silent-noop]]`
   doctrine tag names.
2. **Renumbering (this project's own standing practice) can re-apply a migration under its new
   name.** The tracker sees an unfamiliar filename and treats it as new, even when the content is
   byte-identical to something already applied.

**The fix, narrowly scoped to comparison-and-fail-loud (`platform/scripts/migrate.ts`):**
`getApplied()` now returns `filename -> sha256`. Before skipping an already-recorded filename,
`runMigrations` (and the `--dry-run` path) recomputes the on-disk file's sha256 and compares it
to the stored value:

- **Identical → genuinely skip** (the same behaviour as before, now verified rather than assumed).
- **Different → throw `MigrationHashMismatchError`** naming the filename and both hashes, *before*
  any `BEGIN`/write against the file. `main()`'s existing `catch` turns this into a non-zero exit
  with the message on stderr — no new CLI plumbing was needed. The runner never auto-re-applies
  and never silently continues; an already-applied migration's drift is reported as an operator
  decision (revert the file, or ship the change as a NEW migration), not resolved by the runner.

**What this closes and what it does NOT close (be honest about the boundary):**

- **CLOSES hazard 1** (edited-after-applied) completely — proven on a real throwaway Postgres,
  see below.
- **Does NOT close hazard 2** (renumbering / filename-keyed re-apply). The comparison only fires
  when the CANDIDATE FILENAME is already a key in `_migrations_applied`. A renamed file with
  identical content is, from the tracker's point of view, an unseen filename — there is nothing
  in the map to compare its hash against, so it is treated as new and re-applied. This is a
  **separate, still-open concern**, deliberately out of this fix's scope (Ruling 58 asked for the
  comparison-and-fail-loud behavior only, not a tracker redesign). Closing it would require keying
  the tracker on content hash (or a stable migration ID independent of filename) rather than
  filename — a structural change, not a comparison fix, and out of this lane's authorization.
  Filed as **R5** below.

**Can-fail reproduction (both hazards, on a real throwaway local Postgres — never production):**

- *Hazard 1, before the fix:* apply a migration, edit its SQL, re-run → returns an empty "applied"
  list, throws nothing, table schema unchanged from the edit — the silent skip, reproduced.
- *Hazard 1, after the fix:* same steps → `runMigrations` throws `MigrationHashMismatchError`
  before any `BEGIN`, naming the file and both the stored and current sha256; table left exactly
  as the original (unedited) migration left it.
- *Hazard 2, after the fix (unchanged by it):* apply a migration as `001_x.sql`, rename the
  identical file to `002_x_renamed.sql`, re-run → applies again under the new name with **no**
  error; two `_migrations_applied` rows share the same sha256; the migration's `INSERT` ran
  twice. Confirms the fix's own docstring: this hazard remains open by design.

Full driver scripts and console transcripts for all three runs are recorded in this lane's close
report; not reproduced verbatim here to keep this protocol document stable across future edits.

---

## §4 — The merge lock

**One merge to `main` at a time.** The lock is a discipline, not a mechanism — nothing in GitHub
enforces it, so it holds only if every campaign observes it.

Before taking the lock, confirm the other live campaigns are **quiesced**:

- **no open or auto-merging PR** from any other active campaign, **and**
- **no live session editing the tree.**

**"No open PR" alone is insufficient** and is the specific way this check has failed: work that is
uncommitted in a worktree, or committed to an unpushed branch, is invisible to `gh pr list` and
will still collide.

```bash
gh pr list --state open                       # other campaigns' PRs
git worktree list                             # who else has a working surface
git -C <each-worktree> status --porcelain     # uncommitted work is invisible to gh
```

While holding the lock:

1. `git fetch origin` and **rebase onto `origin/main`** immediately before merging — not earlier.
2. **Re-check the migration number** (§3). A rebase does not renumber anything for you.
3. Merge. Then hold the lock through the deploy window (§5) — release only when the new revision
   is verified healthy.
4. If the deploy is unhealthy: **HARD-STOP the merge queue.** Do not stack the next merge on top of
   a broken revision.

---

## §5 — The deploy window (what a merge to `main` actually does)

A merge to `main` is **not** a code checkpoint. It is an automatic production deploy *and* an
automatic production migration run:

```
merge to main
  └─ CI — "Ganga Quality Gate"  (.github/workflows/ci.yml)
        └─ on success → workflow_run → "Deploy to Cloud Run" (.github/workflows/deploy.yml)
              ├─ deploy-web:  starts Cloud SQL Auth Proxy →
              │               `cd platform && npx tsx scripts/migrate.ts`   ← MIGRATIONS APPLY HERE
              │               → build image → deploy amjis-web → shift traffic
              ├─ deploy-sidecar: amjis-sidecar (path-gated)
              └─ deploy-mcp:     amjis-mcp (revision-URL smoke, then promotion)
```

Three things follow:

- **Your migration runs against production the moment CI goes green.** There is no separate apply
  step and no human confirmation. This is why the number must be re-checked *before* the merge and
  not after.
- **A green pipeline is not a served revision.** `amjis-mcp` deploys to a revision URL, smoke-tests
  it, and only then promotes. A pipeline that passes but skips promotion leaves production serving
  the old code — the INF-2 failure mode. Verify the *serving* revision, not the workflow's green
  tick.
- **Verify after every merge**, before releasing the lock: the new revision responds, no error
  spike, and the migration is present in `_migrations_applied`.

```bash
gh run watch                                        # the deploy, not just CI
gcloud run services describe amjis-web --region asia-south1 \
  --format='value(status.latestReadyRevisionName,status.traffic)'
gcloud run services describe amjis-mcp --region asia-south1 \
  --format='value(status.latestReadyRevisionName,status.traffic)'
```

> **Doctrine note, recorded not resolved.** `CLAUDE.md` §N.4 and `ONGOING_HYGIENE_POLICIES` §N.4
> state "surgical migrations only — never `deploy.yml`-auto or bulk `migrate.ts`". The deploy
> pipeline above *does* run `migrate.ts` in bulk on every deploy to `main`. That is the live
> behaviour as of `5f5033a5`; the doctrine line and the pipeline disagree. Reconciling them is out
> of MIG-1's authorization and is filed as a residual (§7).

---

## §6 — The local Cloud SQL Auth Proxy (`ECONNREFUSED 127.0.0.1:5433`)

**The trap:** the local proxy dies or goes stale, a probe returns `ECONNREFUSED 127.0.0.1:5433`,
and the session reports **"no data"** or **"the table is empty."** It then reasons — sometimes at
length — from an absence that was never observed. This has recurred often enough across campaigns
to be worth a standing rule.

**The rule:** a connection error is **never** evidence about data. Restart the proxy and re-run
before drawing any conclusion. If a lane cannot get the proxy up, it reports the probe
**UNPERFORMED** — never "no rows."

**Restart:**

```bash
# 1. Kill whatever is holding the port (a stale proxy will not surrender it)
pkill -f cloud-sql-proxy
lsof -nP -iTCP:5433 -sTCP:LISTEN        # expect empty

# 2. Restart (sources INSTANCE_CONNECTION_NAME from .env.rag)
platform/scripts/start_db_proxy.sh

# 3. Prove it before trusting any query
psql "$DATABASE_URL" -c 'select 1'
```

Port **5433** is the project convention for the *local* proxy (CI's ephemeral proxy in
`deploy.yml` uses 5432 — do not copy CI's port into a local `DATABASE_URL`).

**localhost is production.** The proxy tunnels to `madhav-astrology:asia-south1:amjis-postgres`.
A write to `127.0.0.1:5433` is a write to the production database. There is no local Postgres to
fall back to.

---

## §7 — The two-directory split: disposition and residuals

**Is the split intentional?** **Partly — and it is no longer honored.**

- **Intentional in origin.** `platform/supabase/migrations/README.md` documents the arrangement
  deliberately: one active directory, one legacy directory retained for historical continuity,
  with `migrate.ts` reading both and de-duplicating by filename. It even names the collision
  behaviour and calls it "functionally safe." This is a considered design, not an accident.
- **Not honored in practice.** The README says all new migrations go to
  `platform/supabase/migrations/`. The single highest number on `main`,
  `474_asset_throughput_incomplete_state.sql` (2026-07-29), is in the *legacy* directory. Nothing
  enforces the routing rule, so the "legacy" directory is still growing.

**Disposition:** the split is **recorded as unintentional-in-effect**. A costed consolidation spec
is filed at
`00_ARCHITECTURE/briefs/samapti/SPEC_MIGRATION_DIRECTORY_CONSOLIDATION_v1_0.md`.
Consolidation is **not** performed here — it is outside SAMĀPTI's authorization (brief v2.0 §4.4c).
The CI guard makes the split *safe to live with* in the meantime; it does not make it correct.

**Residuals — recorded, not fixed by MIG-1:**

| # | Residual | Owner |
|---|---|---|
| R1 | **17** files whose header comment disagrees with their filename number — full register in §3.1. Comment-only, no functional SQL effect. Lane B-MIG474-COMMENT scopes only `474_asset_throughput_incomplete_state.sql`; the other 16 are unowned. Fixing them is authorized (RULING 44), not required, not blocking. | unassigned |
| R2 | No check enforces that new migrations land in `platform/supabase/migrations/`. `474_*` violated it. | consolidation spec |
| R3 | `CLAUDE.md`/`ONGOING_HYGIENE_POLICIES` §N.4 "never deploy.yml-auto" contradicts the live `deploy.yml` behaviour (§5). One of the two must move. | governance |
| R4 | The two directories are not consolidated. | consolidation spec |
| R5 | **CLOSED 2026-07-31 (SAMĀPTI integrity-residuals lane) — see §9.4.** `migrate.ts` now refuses to apply an ostensibly-new migration whose content is already recorded under a different filename, matching on exact sha256 AND on `sql_identity` (comment/whitespace-normalised content hash). The second arm is load-bearing: both real instances of this hazard rewrote their header comment during the rename, so a raw-hash-only guard would have missed them. A second, previously-undetected production instance was found while closing this — `456_lel_schema_v2_event_shapes.sql` re-applied as `457_…` 1h49m later (§9.2). | CLOSED |
| R6 | **RESOLVED via Dvārapāla RULING 70** (was: discovered 2026-07-30 rebasing this lane onto `origin/main` `d5c4b359`; independently found twice — once by this lane's own rebase, once by VER via a different path). `platform/supabase/migrations/484_bg_muhurta_lattice.sql` and `484_bg_synthetic_cohort_md.sql` (ṢAḌ-DARŚANA, `#930`/`#932`) both claim migration number 484 — a genuine E2 duplicate-number collision, NOT in the frozen legacy baseline. Ruling 70 rejected both the "hard-fail B-MIGGUARD's own PR on someone else's bug" option and the "silently widen the frozen baseline" option, and directed the SAME itemized-disclosure mechanism this codebase already uses for `schema_validator.py`'s `known_residuals` whitelist: a new `disclosed_additions` block in `migration_number_legacy_duplicates.json`, separate from (never merged into) the immutable `legacy_duplicate_groups` baseline, carrying one itemized/dated/attributed entry — `484_bg_muhurta_lattice.sql` / `484_bg_synthetic_cohort_md.sql`, owner ṢAḌ-DARŚANA, landed 2026-07-30, disclosed via RULING 70, `fixed_by_samapti: false`. `migration_number_guard.ts` now validates this entry structurally (new **E4** class: a `disclosed_additions` entry missing any required field — `owner`/`landed_at`/`disclosed_via`/`fixed_by_samapti`/`files` — is treated as UNDISCLOSED, not a partial pass) and surfaces it as a non-fatal `[disclosed-residual]` warning even while passing — disclosed, not hidden. `npm run guard:migration-numbers` now exits **0**; all 4 previously-red tests in `migration_number_guard.test.ts` pass; 5 new tests added, including a synthetic-second-undisclosed-collision sanity check confirming the mechanism still discriminates (stays red) and does not act as a blanket amnesty. Still not fixed: renumbering the ṢAḌ-DARŚANA file itself remains out of this lane's authorization — this entry records the collision, it does not close it. | DVA (Ruling 70) — actual renumbering still owned by ṢAḌ-DARŚANA |

---

## §9 — The four integrity residuals of RULING 73-CLOSE (SAMĀPTI, 2026-07-30/31)

RULING 73-CLOSE carried six surviving residuals out of the migration-hash incident. Four were
dispatched as a dedicated lane. This section is their standing record. **Read §9.1 before ever
concluding "the tracker's stored hash is the truth about what ran."**

Production DB access for this section was **read-only**, via an already-configured connection in
the environment (no new connection was opened, no mutation was issued). Every claim below is a
query result or a command output, not an inference.

### §9.1 — The 7 applied-but-missing-from-disk rows — **CLOSED, all 7 explained**

Rows in `_migrations_applied` whose filename exists in neither migrations directory. Enumerated by
diffing all 374 tracker filenames against the 367 on-disk `.sql` files. **All seven are explained,
and six of them are byte-exactly reconstructable.** None is a mystery, and none should be restored.

| # | Filename | Disposition |
|---|---|---|
| 1 | `118_build_events.sql` | Legacy Teardown |
| 2 | `124_builds.sql` | Legacy Teardown |
| 3 | `125_build_steps.sql` | Legacy Teardown |
| 4 | `126_engine_versions.sql` | Legacy Teardown |
| 5 | `127_build_notifications.sql` | Legacy Teardown |
| 6 | `133_notification_views.sql` | Legacy Teardown |
| 7 | `456_lel_schema_v2_event_shapes.sql` | **Renumber — see §9.2** |

**Rows 1–6 — deliberate deletion by PR #187 "Legacy Teardown".** Deleted in commit `0b264942`
("feat(legacy-teardown): AC.6 — fresh migration baseline"), merged as `30640c96`. This is the same
teardown `CLAUDE.md §B` already records as having removed the FORENSIC v8.0 markdown. The tables
they created were dropped by that teardown; the migrations are dead legacy.

Their content is recoverable **byte-exactly** — each pre-deletion blob hashes to the sha256 the
tracker recorded at apply time, verified 6/6:

```
$ git show 0b264942^:platform/migrations/<name>.sql | shasum -a 256   # vs stored sha256
118_build_events.sql          stored=91db713557feeea3  blob=91db713557feeea3  MATCH
124_builds.sql                stored=8a5d175718ded375  blob=8a5d175718ded375  MATCH
125_build_steps.sql           stored=616e055d5bdf124a  blob=616e055d5bdf124a  MATCH
126_engine_versions.sql       stored=fa65f67ad523b9c1  blob=fa65f67ad523b9c1  MATCH
127_build_notifications.sql   stored=048d1a051be0f2ed  blob=048d1a051be0f2ed  MATCH
133_notification_views.sql    stored=85b50984c1d1a5e4  blob=85b50984c1d1a5e4  MATCH
```

**Decision: DOCUMENT, do not restore.** The brief allowed reconstruct-and-restore, but restoring
here would be motion without safety. Because their filenames are already in `_migrations_applied`
and the recovered content hashes to the stored value, the runner would compare, match, and skip —
restoring them changes runner behaviour by exactly nothing, while re-introducing SQL a sealed
teardown PR deliberately removed. The absence of a file is not itself a hazard: if anyone later
creates a *new* file under one of these six names, the existing hash guard fires loudly, which is
the correct outcome. The recovery command above is the standing recipe should that judgement ever
be revisited.

**Row 7 is a different animal entirely** and is the subject of §9.2.

### §9.2 — `456_lel_schema_v2_event_shapes.sql`: the renumber hazard, caught in production

The 7th missing row is **not** a deletion. It is the R5 hazard (§7, hazard 2) having actually
happened, undetected, in production:

```
456_lel_schema_v2_event_shapes.sql   sha a6d30ee4…   applied 2026-07-18T23:30:11Z
457_lel_schema_v2_event_shapes.sql   sha fdc1edb0…   applied 2026-07-19T01:19:40Z
```

Commit `54c809bc` ("renumber 456->457 after rebase collision with A-2") renamed the file after it
had already been applied. The tracker is keyed by **filename**, so 457 looked brand-new, and the
same migration executed a second time 1h49m later. It caused no damage only because the SQL was
additive/idempotent. Nothing detected it at the time; it surfaced only because this lane diffed
the tracker against the disk.

This is the second recorded instance of the class (the first: 474, which went 466→467→474 — see
RULING 44). **R5 is now CLOSED** — see §9.4.

Note for the record: the stored sha256 of the 456 row matches the pre-rename git blob exactly
(`git show 15947002:platform/migrations/456_lel_schema_v2_event_shapes.sql | shasum -a 256` →
`a6d30ee4…`), so this row is fully accounted for and needs no reconstruction — 457 carries the
content forward.

### §9.3 — The 4 `UNDER-INVESTIGATION` hash disclosures — **all 4 dispositioned**

RULING 73-CLOSE left four disclosure entries reading *"well-formed sha256, no matching git blob
anywhere in history."* Each now carries a real disposition in
`platform/scripts/ci/migration_hash_disclosed_residuals.json`. **The hash pins themselves were not
touched** — only the `cause` text — so the guard's behaviour is unchanged and each disclosure
still pins exactly the same historical mismatch.

**What was checked, for all four:**

1. **Widened blob search.** RULING 73's search was scoped to blobs appearing *under the same
   filename*. This swept **all 68,303 objects (22,112 blobs) in the object database**, including
   unreachable/dangling ones — i.e. content committed on a deleted branch, amended away, or
   stashed — under *any* filename, plus an LF-normalised comparison. **No match, for any of the
   four.** DVA's finding is independently confirmed and strengthened.
2. **Benign-mechanical drift replay.** Line endings (LF/CRLF/CR), BOM, trailing-newline count,
   per-line trailing whitespace, tab↔space, latin-1 re-encode — **none** reproduces a stored hash.
3. **Alternate digest algorithms** (md5, sha1, sha224, sha384, sha512, sha3-256, blake2s) over the
   committed content — **none** matches. The recorded values really are sha256 of *different
   content*.
4. **Effect verification.** What the migration was *for* was checked directly against production.

**The root-cause CLASS is now established, and it is shared by all four:** in every case
`applied_at` **precedes** the file's only commit — by 11 seconds, 7m42s, 10m32s and 2h57m
respectively. The content applied was *working-tree* content that was then edited before being
committed. Migration 237's own commit message says so outright ("migration 237 applied to prod;
to_regclass → NULL confirmed"), and 314's says "Migrations 311-317 applied to prod
(ledger-reconciled)". This is apply-by-hand-then-write-up, not corruption. **What remains unknown
is only the exact bytes; what each migration did is now verified.**

| Entry | Disposition | Evidence |
|---|---|---|
| `237_drop_signal_type_registry.sql` | **RESOLVED-AS-IMMATERIAL** · replay-equivalent | Its whole executable content is one `DROP TABLE IF EXISTS signal_type_registry CASCADE;`. Live: `to_regclass('public.signal_type_registry')` → `NULL`. Any variant producing that state contained that statement; drift is confined to header commentary. |
| `294_ga_vastu_target_floor.sql` | **RESOLVED-AS-REAL-AND-MATERIAL** · fixed forward | **Not benign.** See below. |
| `314_bo_samskara_count_sql_scope_fix.sql` | **RESOLVED-AS-IMMATERIAL** · replay-equivalent | Deliberately superseded by `344_bo_samskara_scope_per_chart.sql` and `379_bodha_count_sql_chart_parameterize.sql`. Live values match 344/379, not 314 (`scope='per_chart'`, `count_sql='… WHERE chart_id = $1'`) — as intended. A replay runs 314→344→379 and lands identically whatever 314's bytes were. |
| `377_ka_dasha_kala_target_floor.sql` | **RESOLVED-AS-IMMATERIAL** · drift positively characterised | Its commit message documents behaviour the committed SQL does not implement — "Also flips the two existing dormant throughput rows to lit directly" — but the file contains only the `asset_registry` update. The applied version almost certainly carried that second statement, stripped before commit (applied 11s before the commit). Both effects verified live: `target_floor = 0`, throughput rows all `lit`. Immaterial for replay: `asset_throughput` is per-chart build state, regenerated by every build, not schema. |

**`294_ga_vastu_target_floor.sql` — a real defect, found by investigating the drift.**
The committed file reads:

```sql
UPDATE asset_registry SET target_floor = 40 WHERE asset_id = 'ga_vastu_planet_direction_map';
```

`ga_vastu_planet_direction_map` is the **target table**; the `asset_id` is `ga_vastu` (migration
287). **The on-disk file matches zero rows — it is a no-op.** Yet production correctly holds
`target_floor = 40` for `ga_vastu`, which is precisely 294's stated intent (45→40, because Ketu has
no classical Vastu direction so the writer emits 8 grahas × 5 ayanamshas = 40), and **no other
migration in either directory sets that value** (287 inserts 45; 381's floor calibration does not
touch `ga_vastu`).

The applied version carried the correct predicate; the committed version does not. **Consequence:
replaying every migration onto a fresh database would leave `ga_vastu` at 45 — `main` could not
reproduce production.** That is a genuine replayability defect that no amount of hash-pinning would
have surfaced; only asking "what was this migration *for*, and is it true?" did.

**Fixed forward by `498_ga_vastu_target_floor_replay_fix.sql`.** 294 itself is untouched — it is
already applied, editing it is forbidden, and it would break its own pin. 498 is a no-op against
current production and a correction on any fresh replay, exactly as `MigrationHashMismatchError`'s
own message prescribes ("create a NEW migration file to carry the intended change forward").

### §9.4 — R5 CLOSED: the filename-keyed renumber hazard

**`migrate.ts` now refuses to apply an ostensibly-new migration whose content is already recorded
under a different filename.** Two filename-blind arms:

1. **exact sha256** — catches a pure `git mv` with no content edit;
2. **`sql_identity`** — sha256 of the content with SQL comments stripped and whitespace collapsed
   (string literals, dollar-quoted bodies and nested block comments handled properly).

**The second arm is load-bearing, not belt-and-braces.** Both real instances of this hazard
rewrote the `-- Migration NNN:` header in the same commit as the rename, so the two files have
**different** sha256 — a raw-hash-only guard would have missed the very defect it exists to catch
(CLAUDE.md §N.8: a detector must measure the claim it asserts). Verified against the real pair:

```
raw sha256    456=a6d30ee464d7cac1  457=fdc1edb0789ac743  -> DIFFERENT (raw-hash guard MISSES)
sql_identity  456=278470efc88d047d  457=278470efc88d047d  -> SAME      (identity guard CATCHES)
```

**False-positive sweep before implementing**, over all 367 on-disk migrations: 0 raw-sha256
collisions, and exactly **1** `sql_identity` collision —
`361_fix_cgm_asset_throughput_state.sql` / `374_cgm_throughput_state_correction.sql`. Those two are
genuinely the *same* migration written twice and applied twice (identical SQL, different comments).
**A true positive, not a false one** — precisely what the guard exists to flag. Net false positives
across the whole corpus: **zero**. Both are already applied, so the guard is silent on today's
tree.

**Supporting mechanism.** A nullable `sql_identity` column on `_migrations_applied` (runner-owned
DDL via `TRACKER_IDENTITY_DDL`, **not** a numbered migration — the tracker has always been the
runner's own table), plus an opportunistic backfill that stamps an identity **only** for rows whose
on-disk content still hashes to the sha256 recorded at apply time. Rows whose file is gone, or
whose content has drifted (the 25 disclosed residuals), stay **NULL** rather than be stamped with
an identity derived from content we cannot prove ran. An honest NULL, not a fabricated value.

**Escape hatch** — `platform/scripts/ci/migration_renumber_disclosed.json`, mirroring the
`disclosed_additions` / disclosed-hash-residual discipline exactly: empty by design, every field
required (a partial entry is dropped as UNDISCLOSED, never a partial pass), pinning one exact
`(new_filename, applied_filename, sql_identity)` triple. Two dispositions:

- `already-applied-under-old-name` — the SQL genuinely ran under the old name; the runner records
  the new filename as applied **without executing it**. *This is the normal answer for a renumber*,
  and it is what keeps the guard from being deploy-blocking in practice.
- `intentional-reapply` — the SQL is idempotent and re-running it is deliberate; execute normally.

The guard also runs under `--dry-run`, so an operator finds out from a preview.

### §9.5 — The `workflow_dispatch` deploy bypass — CLOSED

RULING 73-CLOSE recorded this as observed **3×** in one night and held it *"unchanged, not
hardened,"* on the stated ground that gating manual dispatch could block a legitimate emergency
deploy. That objection is sound, and it is the design constraint here — not a reason to leave the
hole open. **Confirmed from the YAML, the bypass had two halves, not one:**

| | Old condition | What it bypassed |
|---|---|---|
| CI gate | `github.event_name == 'workflow_dispatch' \|\| github.event.workflow_run.conclusion == 'success'` on every deploy job | A manual dispatch deployed **whether or not CI passed, or ever ran**, on that SHA. |
| Path gate | `github.event_name == 'workflow_dispatch' \|\| needs.changes.outputs.<x> == 'true'` on sidecar / MCP / pipeline-job | A dispatch **force-deployed every service**, discarding the path outputs the `changes` job had just computed. |

**Both are closed; `workflow_dispatch` is retained.**

- Manual dispatch now **defaults** to the same CI-green requirement as an automatic deploy.
- Bypassing it takes **two deliberate acts**: select the `ci_gate` choice whose value literally
  reads `EMERGENCY-OVERRIDE-CI-NOT-GREEN`, **and** type an `emergency_reason` of ≥20 characters.
  Both are recorded in the run log, and the run is annotated with a `::warning::`. A reflex click
  cannot produce either.
- Path gates now honour an explicit `force_all_services` boolean input (default `false`) instead of
  firing implicitly on every dispatch.
- An unrecognised `ci_gate` value is treated as `require-ci-green` — **fail safe, not fail open**.

**Why this mechanism over the alternatives.** A dry-run/plan-by-default mode was considered and
rejected: it creates a second code path that drifts from the real one, and an operator who must
re-dispatch with `force` in an actual emergency is worse off than one who must tick a box. This
design adds **no new job topology, no new credentials, and no second code path**. The gate runs
inside the existing `changes` job — which every deploy job (now including `deploy-web`, the job
that runs migrations and promotes traffic) `needs` — so failing it skips them all. No `always()`
gymnastics, and the failure direction is the safe one.

**Verification.** The decision logic lives in `platform/scripts/ci/dispatch_gate.ts` as a pure
function with unit tests, precisely so the gate is exercisable off GitHub Actions rather than being
a YAML expression nobody can test. `platform/scripts/__tests__/dispatch_gate.test.ts` additionally
parses the **real `deploy.yml`** and asserts the wiring — that `workflow_dispatch` still exists,
that the gate step is present, that every deploy job needs `changes`, and that no job has
re-introduced the `event_name == 'workflow_dispatch' || needs.changes.outputs…` short-circuit. A
correct decision function that `deploy.yml` never consults would be a §N.8 signal with no detector
behind it.

**Not verified by this lane, and deliberately not claimed:** an end-to-end GitHub Actions run. That
requires pushing and triggering a real production deploy, which is the Integrator's step under
merge-lock, not a builder's. The recommended live proof at merge is the three-way check the design
is built for: (a) dispatch mid-CI → blocked with the CI-not-green message; (b) dispatch with the
override token + reason → proceeds, warning annotated; (c) a normal `workflow_run` deploy →
unaffected.

---

## §8 — Checklist (copy into a session close)

- [ ] Migration number = `npm run migration:next` read from `origin/main` **at merge time**
- [ ] Number written in **both** the filename and the header comment
- [ ] New migration is in `platform/supabase/migrations/`
- [ ] `npm run guard:migration-numbers` passes locally
- [ ] Merge lock: no other campaign's open PR **and** no live session editing the tree
- [ ] Rebased onto `origin/main` immediately before merge
- [ ] Deploy watched to completion; `amjis-web` **and** `amjis-mcp` serving revisions verified
- [ ] Migration confirmed present in `_migrations_applied`
- [ ] Any live-DB probe preceded by a proven-up proxy (§6) — otherwise reported UNPERFORMED

---

*End of MIGRATION_AND_MERGE_PROTOCOL v1.3 (2026-07-31, SAMĀPTI integrity-residuals lane — the four
RULING 73-CLOSE integrity residuals, new §9. §9.1: all 7 applied-but-missing-from-disk rows CLOSED —
6 are PR #187 Legacy Teardown deletions, reconstructable byte-exactly (6/6 stored-sha256 match
against the pre-deletion blob) and deliberately NOT restored; the 7th is a renumber. §9.2: that 7th,
`456_lel_schema_v2_event_shapes.sql`, is a previously-undetected PRODUCTION instance of the R5
hazard — the same SQL executed twice under two filenames 1h49m apart, harmless only because it was
idempotent. §9.3: all 4 UNDER-INVESTIGATION disclosures dispositioned; the widened blob sweep
(68,303 objects / 22,112 blobs, dangling included, any filename) confirms DVA's finding, and the
shared root-cause class is established (applied_at precedes the only commit in all four —
apply-by-hand-then-edit-before-commit). Three are replay-immaterial with live effect verified; the
fourth, `294_ga_vastu_target_floor.sql`, is a REAL defect — the committed file filters on the table
name instead of the asset_id and is a no-op, so a fresh replay could not reproduce production —
fixed forward by migration 498, with 294 itself untouched. §9.4: **R5 CLOSED** — `migrate.ts` now
refuses a renumbered re-apply, matching on exact sha256 AND on comment/whitespace-normalised
`sql_identity` (load-bearing: both real instances rewrote their header during the rename, so a
raw-hash guard would have missed them); 0 net false positives across all 367 on-disk migrations.
§9.5: the `workflow_dispatch` bypass CLOSED — both halves of it (CI gate and path gate), with
emergency capability preserved behind an explicit two-act override, which was RULING 73-CLOSE's
stated objection to hardening it. Not claimed: an end-to-end Actions run, which belongs to the
Integrator under merge-lock.)
Prior: v1.2 (2026-07-30, SAMĀPTI lane B-MIGGUARD — Dvārapāla RULING 70:
R6 resolved. The 484 duplicate (ṢAḌ-DARŚANA, not owned by SAMĀPTI) is now an itemized/dated/
attributed `disclosed_additions` entry in `migration_number_legacy_duplicates.json`, kept separate
from the immutable `legacy_duplicate_groups` freeze, validated structurally by a new E4 guard class
(missing field = treated as undisclosed, never a partial pass) and surfaced as a non-fatal warning —
same itemize-or-it-doesn't-count discipline as `schema_validator.py`'s `known_residuals` whitelist.
`guard:migration-numbers` exits 0; all 4 previously-red tests pass; 5 new tests, including a
synthetic-second-undisclosed-collision check that the mechanism still discriminates. Renumbering
the ṢAḌ-DARŚANA file itself remains that campaign's own open item, not SAMĀPTI's.).
Prior: v1.1 (2026-07-30, SAMĀPTI lane B-MIGGUARD — Dvārapāla RULING 58: §3.2 added, the tracker's
sha256 is now compared and fails loudly on drift for an already-applied migration whose filename is
unchanged; R5 records the renumbering hazard this does NOT close; R6 records the newly-discovered
484 collision, flagged for DVA). Prior: v1.0 (2026-07-30, SAMĀPTI lane B-MIGGUARD, first issue).*

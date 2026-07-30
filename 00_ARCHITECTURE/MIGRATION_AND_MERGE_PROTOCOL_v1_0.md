---
artifact: MIGRATION_AND_MERGE_PROTOCOL_v1_0.md
canonical_id: MIGRATION_AND_MERGE_PROTOCOL
version: 1.0
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

*End of MIGRATION_AND_MERGE_PROTOCOL v1.0 (2026-07-30, SAMĀPTI lane B-MIGGUARD).*

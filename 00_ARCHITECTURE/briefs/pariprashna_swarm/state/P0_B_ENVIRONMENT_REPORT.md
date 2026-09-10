---
artifact: P0_B_ENVIRONMENT_REPORT
canonical_id: PARIPRASHNA_P0_B_ENVIRONMENT_REPORT
version: 1.0
status: DRAFT — lane deliverable, not yet reviewed/merged by the conductor
date: 2026-08-19
produced_by: P0-B (environment) lane, Paripraśna implementation swarm
lane_worktree: /private/tmp/pariprashna-p0-b-env
lane_branch: pariprashna/p0-b-env
lane_base: pariprashna/p0 @ 16557dd69
role: >
  Findings + scaffolding for the P0-B environment lane per
  KICKOFF_PROMPT_SWARM_CONDUCTOR_v2_0.md and
  PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md §6 (P0 lane list). Covers
  the four items the prior conductor attempt explicitly left unprobed
  (SWARM_TRACKER.json `prior_attempt.not_yet_probed_owed_by_p0_b`): worktree
  farm conventions, cloud-sql-proxy, template test-DB design, migration
  allocator — plus the flag-registry survey (RF-3).
---

# P0-B Environment Report

## 1. Worktree farm conventions (as observed, not invented)

`git worktree list` against this repo's shared `.git` shows two live, distinct
conventions in concurrent use, plus a third for this harness's own agent
sessions. Documenting all three as observed:

**A. `/private/tmp/<name>` — the general swarm/conductor worktree farm.**
Used by Paripraśna itself (`/private/tmp/pariprashna-p0` on `pariprashna/p0`),
by the EKAVĀKYATĀ/PARIṢKĀRA/other campaigns' scratch and coordination
worktrees (`/private/tmp/coord_wt`, `/private/tmp/ekv-coord-push3`,
`/private/tmp/madhav-main-check`), and by ad-hoc fix worktrees
(`/private/tmp/stage5-fix-worktree`). This is the convention P0-B used for its
own lane worktree (`/private/tmp/pariprashna-p0-b-env`, branch
`pariprashna/p0-b-env`, branched from `pariprashna/p0` @ `16557dd69` — the
conductor's own worktree at `/private/tmp/pariprashna-p0` was deliberately
left untouched since another live session owns it). `CROSS_CAMPAIGN_
COLLISION_FORENSICS_AND_REPAIR_v1_0.md` §E1 documents this same pattern
(`pariprashna/g0-close` → `/private/tmp/pariprashna-g0-close`,
`pariprashna/p0-ignition` → `/private/tmp/pariprashna-p0-ignition`).
Naming: `/private/tmp/<campaign-or-branch-slug>`, one worktree per
branch/lane, pruned when the branch is retired (`git worktree remove` /
`git worktree prune` after deleting the branch).

**B. `/Users/Dev/par-night/codex-wt/<name>` — PARIŚEṢA/Codex's own farm.**
Exclusively `codex/parisesa-*` and `codex/v4-*` branches (`bootstrap-ccd`,
`governance-macro-plan-v21`, `parisesa-lease-kernel`, ~20 `v4-f*` lanes,
etc.). Paripraśna lanes should NOT create worktrees here — it is the other
live campaign's own farm and mixing in it risks exactly the kind of
cross-campaign collision `CROSS_CAMPAIGN_COLLISION_FORENSICS_AND_REPAIR_v1_0.md`
was written to prevent.

**C. `.claude/worktrees/<agent-id>` — this harness's own per-agent-session
isolation** (e.g. this P0-B investigation's own launch worktree,
`.claude/worktrees/agent-ad7647b34e2f23701`, on a synthetic
`worktree-agent-<id>` branch, NOT a `pariprashna/*` branch). This is separate
machinery from A/B above — it is how each Claude Code Task/Agent invocation
gets its own filesystem isolation, not a swarm lane convention. A lane
builder should not treat this as its "worktree branch" for the swarm's own
bookkeeping; it should create a real `/private/tmp/<name>` worktree on a real
`pariprashna/*` branch (as this lane did) so the branch/commits are
inspectable and mergeable through the normal train protocol.

**Recommendation for future P0+ lanes:** `git worktree add /private/tmp/
pariprashna-<lane-id> -b pariprashna/<phase>-<lane-id> <base-ref>`, one
worktree per lane, based on the current phase branch tip (read fresh, not
predicted — X-7). Prune with `git worktree remove` + branch delete once the
lane's commits are merged/parked, never `rm -rf`.

## 2. `cloud-sql-proxy` — capability check (read-only, no connection attempted)

**Available.** `/opt/homebrew/bin/cloud-sql-proxy`, version 2.21.3 (`cloud-sql-proxy
--version`), installed via Homebrew (`brew list` shows `cloud-sql-proxy` as a
formula). Note: `gcloud components list` reports the *gcloud-managed*
"Cloud SQL Proxy v2" component (`cloud-sql-proxy` component ID) as
"Not Installed" — this is a red herring; it is a separate install path from
the Homebrew binary. The Homebrew binary is what's actually on `PATH` and
what `platform/scripts/start_db_proxy.sh` already expects (it explicitly
prepends `/opt/homebrew/bin` to `PATH`).

**Existing usage in-repo:** `platform/scripts/start_db_proxy.sh` is a small,
already-working wrapper — reads `INSTANCE_CONNECTION_NAME` from
`.env.rag`, starts `cloud-sql-proxy "$INSTANCE_CONNECTION_NAME" --port=5433 &`,
prints the local connection string. `cloud-sql-proxy`/`cloudsql` references
also appear in ~25 other scripts under `platform/scripts/` (dispatch/harvest/
bootstrap/audit scripts) and ~15 docs under `00_ARCHITECTURE/` — all use the
same auth-proxy-then-`psql`/`DATABASE_URL` pattern, nothing novel needed.

No connection to the production instance was attempted per the task's hard
constraint — this is a capability check only. The binary + wrapper script are
both confirmed ready for any future session that needs an authenticated
proxy connection.

## 3. Template test-DB design note (RF-5)

**How the existing CI "throwaway Postgres" pattern actually works** (from
`.github/workflows/ci.yml`, job `db-integration-tests` / "DB Integration Tests
(SAMĪKṢĀ, throwaway Postgres)", and the sibling `pratijna-v4-fixture-
property-tests` job):

- A GitHub Actions `services: postgres: image: postgres:16` container, fresh
  per job run, exposed on `localhost:5432`, password `postgres`.
- The job's own first step provisions what it needs directly via `psql`:
  `db-integration-tests` creates two logical databases (`samiksha_test`,
  `samiksha_e2e`), adds `pgcrypto`, stubs a minimal `message_parts(id)` table
  just to satisfy one FK, then applies exactly one real migration file
  (`470_pariprashna_samiksha_prediction_ledger.sql`) to get the real DDL under
  test. `pratijna-v4-fixture-property-tests` instead restores a small
  committed, versioned, gzipped fixture snapshot (~1.8MB,
  `platform/python-sidecar/tests/fixtures/pratijna_v4_snapshot/`) into a
  freshly created database.
- Both patterns are **local/CI-only** — no cloud database, no `cloud-sql-
  proxy` in the loop, matching the task's constraint.

**Design for a template-DB-clone-per-lane pattern (for P1+ local dev, not
CI):** CI's per-job containers already solve isolation for CI itself (each
job gets its own container). The gap RF-5 actually names is **concurrent
local builders sharing one dev Postgres** — several lane worktrees running DB
integration suites against the same instance at once, corrupting each
other's state. Proposed pattern, built directly on Postgres's own
`CREATE DATABASE ... TEMPLATE ...` (no new tooling required, a few lines a
lane's own test setup can run):

1. **One-time (conductor or first lane that needs it):** provision a local
   Postgres (Homebrew `postgresql@16`/`postgresql@17`, already present per
   `brew list`, or a single long-lived `postgres:16` Docker container — either
   is fine, both are local, neither is cloud), build a `pariprashna_template`
   database with the DB-integration schema pre-applied (mirror
   `db-integration-tests`' own provisioning step: `pgcrypto` + the
   `message_parts` stub + migration 470, or whatever the current lane's
   suites need), then `ALTER DATABASE pariprashna_template WITH
   is_template = true;` — the flag Postgres itself needs before another
   session can clone it.
2. **Per lane (each builder's own worktree, at test-setup time):**
   `CREATE DATABASE pariprashna_lane_<lane_id> TEMPLATE pariprashna_template;`
   — sub-second, because Postgres does a filesystem-level copy, not a
   logical restore. The lane's `DATABASE_URL`/`SAMIKSHA_TEST_DATABASE_URL`
   env var points at its own `pariprashna_lane_<lane_id>` database; no other
   lane can see or corrupt it.
3. **Teardown:** `DROP DATABASE pariprashna_lane_<lane_id>;` when the lane's
   worktree is retired (or just leave it — cheap, and useful for post-mortem
   debugging of a failed suite until pruned).
4. **DB-heavy suites still also run once at train level** against a shared
   instance (mirrors CI's `db-integration-tests` job as the ground truth) —
   the per-lane clone is a local speed/isolation convenience for the builder
   loop, not a replacement for the real gate.

This needs zero new infrastructure to stand up — it is a ~10-line
`createdb --template` / `CREATE DATABASE ... TEMPLATE ...` convention a P1+
lane's own test-setup script can follow, matching the docker-based/local
Postgres the existing CI already uses (per the task's constraint against
provisioning any actual cloud database). No script was written for this
item since the pattern is simple enough to document rather than wrap; if a
future lane wants a helper, `platform/scripts/governance/
reserve_migration_number.py` (§4 below) is the sibling-script precedent for
where such a helper would live (`platform/scripts/db/` or similar).

## 4. Migration-number allocator (RF-2/X-6)

**Verified current ceiling (re-checked live, do not trust any older number):**
**573** — `platform/migrations/573_mi_sambandha_scored_count.sql`. Migration
numbering is a **single global sequence spanning both directories**
(`platform/migrations/` AND `platform/supabase/migrations/`) despite
`00_ARCHITECTURE/MIGRATION_DIRECTORY_POLICY_v1_0.md` (2026-05-22) nominally
declaring the supabase directory "FROZEN" at 057–071 — live practice
(confirmed by files up to 571 in `platform/supabase/migrations/` and the
CCD's own claim table treating both directories as one counter) has
superseded that doc's text without a doc update. Highest number per
directory: `platform/migrations/` → 573, `platform/supabase/migrations/` →
571.

**origin/campaign-coordination's own "## 2. MIGRATION NUMBER CLAIMS" table
convention** (read fresh via `git show origin/campaign-coordination:
00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md`): a plain markdown table,
one row per number or contiguous range, columns `number | campaign | file |
status`, a trailing `| N+ | — | next free; claim here before use | —` sentinel
row, "claim-at-PR-open; renumber-on-collision stands" as the header's own
rule. **This existing pattern is followed, not replaced.** One finding worth
flagging to the conductor: **the table's own sentinel row currently reads
`570+`, but the true disk ceiling is already 573** — migrations 571/572/573
were claimed/applied via inline dated log entries elsewhere in the same file
rather than by updating the §2 table itself, so a lane trusting the table's
sentinel row alone would collide. The allocator below defends against this by
taking `max(disk ceiling, table ceiling) + 1`, never the table alone.

**Built:** `platform/scripts/governance/reserve_migration_number.py` (in this
lane's worktree, committed). Pure read/compute tool — reads the local
migration directories for the disk ceiling, `git show`s
`origin/campaign-coordination`'s CCD file for the table ceiling, takes the
max, and prints a ready-to-paste CCD table row. **It never writes to
`origin/campaign-coordination` or any governance file** — per X-6 the actual
append is a conductor action from a scratch worktree, never automated by a
lane tool and never done by this lane (hard constraint: do not touch
`origin/campaign-coordination` directly).

Smoke-tested dry run (not a real claim):
```
$ python3 platform/scripts/governance/reserve_migration_number.py \
    --campaign PARIPRASHNA --file pariprashna_p1_example.sql \
    --description "example dry run, not a real claim" \
    --context "P0-B smoke test"
disk ceiling (platform/migrations + platform/supabase/migrations): 573
CCD claim-table ceiling (origin/campaign-coordination):            570
NEXT FREE (max + 1):                                               574
```

**Recommended coordination-file entry for the conductor to post** (NOT posted
by this lane): update the `## 2. MIGRATION NUMBER CLAIMS` table's sentinel
row from `| 570+ | — | next free; claim here before use | — |` to
`| 574+ | — | next free; claim here before use | — |`, and optionally add
explicit rows for 571 (`571_p3a_shape_only_tier.sql`, `git log` shows PR #1279 "[SM-Δ1] P-B
L-TIER: P3-a/b/e", MERGED per disk evidence), 572
(`572_ekv_c01_ledger_empty_daterange_repair.sql`, EKAVĀKYATĀ — PR #1295,
MERGED — this is the C-01 migration `CROSS_CAMPAIGN_COLLISION_
FORENSICS_AND_REPAIR_v1_0.md`/CCD log entries reference), and 573
(`573_mi_sambandha_scored_count.sql`, PR #1316 "batch-4 (night): F-116
preamble-strip + F-35 scored-count + ...", MERGED — campaign banner unclear
from the commit message alone, doesn't match a `pariprashna/ekv/parisesa/
parishkara` prefix; conductor should confirm the owning campaign before
crediting a row) so the table stops silently trailing the real ceiling.

## 5. Flag registry (RF-3)

**No gap found; existing infrastructure is mature and sufficient.** Two
layered systems, both already live:

1. **`platform/src/lib/config/feature_flags.ts`** — a compile-time
   `FeatureFlag` string-literal union (the legacy/simple flags:
   `PANEL_MODE_ENABLED`, `CHECKPOINT_4_5_ENABLED`, `DISCOVERY_PATTERN_ENABLED`,
   `LEL_CONTEXT_ENABLED`, `NVIDIA_PLANNER_ENABLED`, etc., each with an
   inline comment documenting its owning unit/phase and default), served by
   the `configService` singleton in `platform/src/lib/config/index.ts`.
   Retired flags are left in place as commented-out entries with a retirement
   note rather than deleted — the same "honest history over silent deletion"
   discipline as elsewhere in this repo's governance docs.
2. **`platform/src/lib/gates/gate_registry.ts` + `platform/src/lib/config/
   configService.ts`'s DB-backed "gate" plane** (Stream C / Unit 2d, newer,
   the direction the system is moving) — a static `GATE_REGISTRY` catalog
   where each `GateSpec` declares `class` (`feature_flag` |
   `pipeline_threshold` | `model_routing` | `access_capability` |
   `data_source`), `scope` (`global` | `per_chart`), `value_type`, `default`,
   `hot_reload`, and `danger` (requires confirm + reason). Runtime values
   resolve `cache → runtime_config DB row → env-var override → registry
   default`, writes go through `setGate()` (validates against the registry,
   enforces an `AYANAMSHA_CANONICAL_ENABLED=false` guard, upserts
   `runtime_config`, appends `gate_change_log`, invalidates cache).
3. **`platform/src/lib/models/runtime_config.ts`'s `getEffectiveModel()`** —
   the model-routing-specific reader used by exactly the shared files RF-3
   worries about (`platform/src/app/api/pariprashna/route.ts`,
   `platform/src/app/api/chat/consult/route.ts`,
   `.../consult/continue/route.ts`), confirming the pattern is already the
   one live in the file P0-C is decomposing.

**What RF-3 actually needs from P0-B is a process rule, not new code:**
"`feature_flags.ts` additions go through a conductor-reserved flag registry."
Given the infrastructure above already exists and is shared/barrel-like
(`feature_flags.ts`'s union type, `gate_registry.ts`'s static catalog — both
single files many lanes could plausibly need to touch), the recommendation
is the same ownership rule RF-3 already states for `protocol/events.ts` and
lockfiles: **treat `feature_flags.ts` and `gate_registry.ts` as
integrator-only edit surfaces during P0–P5** — a lane proposes its flag/gate
addition in its lane brief, the conductor (or the designated integrator hat)
batches additions into these two files at train time, same as barrel files.
No new registry, tooling, or scaffolding is needed; this is a lane-brief +
train-protocol convention, not a code gap.

## 6. Summary for the conductor

| Item | Status | Key fact |
|---|---|---|
| Worktree farm | Documented (§1) | `/private/tmp/<name>` = general swarm farm (used here); `/Users/Dev/par-night/codex-wt/<name>` = PARIŚEṢA/Codex's own, do not use; `.claude/worktrees/<agent-id>` = harness session isolation, not a swarm lane branch |
| `cloud-sql-proxy` | CONFIRMED available | `/opt/homebrew/bin/cloud-sql-proxy` v2.21.3 (Homebrew, not the gcloud component); `platform/scripts/start_db_proxy.sh` already wraps it |
| Template test-DB (RF-5) | Design documented (§3) | CI already does per-job throwaway `postgres:16` containers; local per-lane isolation = `CREATE DATABASE ... TEMPLATE ...`, no new tooling |
| Migration allocator (RF-2/X-6) | Built + tested (§4) | `platform/scripts/governance/reserve_migration_number.py`; verified ceiling = **573**; CCD table's own sentinel (570+) is stale — conductor should post an update |
| Flag registry (RF-3) | Surveyed, no gap (§5) | `feature_flags.ts` + `gate_registry.ts`/`configService.ts` DB-backed gates + `runtime_config.ts.getEffectiveModel()` already mature; need is a process rule (integrator-only edits), not new code |

**Recommended `origin/campaign-coordination` entries for the conductor to
post** (this lane touched nothing there, per hard constraint):
1. Update `## 2. MIGRATION NUMBER CLAIMS` sentinel row `570+` → `574+`
   (§4), optionally backfilling rows for 571/572/573.
2. A short P0-B completion note under the PARIPRAŚNA campaign-entry section:
   worktree/proxy/template-DB/allocator/flag-registry items are no longer
   "not yet probed" — all five are closed out, findings in this report, no
   production/DB/migration/deploy action taken.

**Lane worktree / branch for the conductor to pull in:**
`/private/tmp/pariprashna-p0-b-env`, branch `pariprashna/p0-b-env`, based on
`pariprashna/p0` @ `16557dd69`.

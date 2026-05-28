---
artifact: OPERATOR_CLEANUP_PLAN_v1_0.md
status: SUPERSEDED-AS-COMPLETE  # v1.2 fully discharged by OPERATOR_CLEANUP_V1_2_REPORT_v1_0.md (2026-05-28)
version: 1.2
date: 2026-05-28
relates_to:
  - 00_ARCHITECTURE/PLATFORM_MODERNIZATION_CLOSE_v1_0.md       # the seal
  - 00_ARCHITECTURE/CONDUCTOR/modernization/RED_TEAM_PLATFORM_MOD_v1_0.md
  - 00_ARCHITECTURE/CONDUCTOR/modernization/OPERATOR_CLEANUP_V1_2_PATCH_BRIEF.md
changelog:
  - v1.2 (2026-05-28, native): Phase C deferred at cursor 086 — authored against greenfield charts shape vs legacy in prod; remainder of C (086–090 + 118 + 119) + the Phase J l25_msr_signals HASH partition deferred to a v1.2 follow-on patch session that pre-stages a charts-alignment migration. D-M proceed now as structurally independent of C.
  - v1.1 (2026-05-27, native): SQL scale-up + HA + partition moved IN (Phase J — a second tenant now exists, the user's data under the new architecture); the post-cutover wait before mig 090 is REMOVED (defense replaced by a pre-flight grep that no live code references `audience_tier`); naming-lint baseline drawdown stays deferred per native call.
purpose: Close the seal's §Deferred queue (8 items) + SQL scale-up + accumulated hygiene, in one ordered Claude Code session.
expose_to_chat: false
---

# Post-Seal Operator Cleanup — Plan v1.1

## §0 — Scope & posture
Closes all 8 deferred operator items from the seal, **plus** Cloud SQL scale-up + HA + partitioning (a second
tenant is live — the user's chart under the new architecture sits alongside the legacy one), **plus** the
accumulated hygiene I'd add for a clean post-program state. ONE Claude Code session, bypass perms,
**sequential phases with smoke + auto-rollback between**, halt on red. **No deliberate human pauses** — the
post-cutover wait that v1.0 had before migration 090 has been replaced by an automated pre-flight check
(grep for any remaining `audience_tier` references in live code) — defense without a calendar.

Some steps remain **irreversible** (mig 090, AR cleanup, partition table swap, service delete) — those sit
behind explicit gates (pre-flight checks, staging-first, dependency confirmation) so the plan won't blunder
into them.

## §1 — Prerequisites (one-time, in the user's environment)
- `gcloud` CLI authenticated to project `madhav-astrology` (region `asia-south1`).
- Terraform installed; the six terraform modules authored by `4.edge_and_infra_hygiene` are committed under
  `infra/` (or wherever that unit laid them) and `terraform init` is run.
- Cloud SQL Auth Proxy (port 5433) reachable for staging + prod, OR the `@google-cloud/cloud-sql-connector`
  flow works from the host.
- Env vars present for the live-eval / smoke step: `SMOKE_SESSION_COOKIE`, `SMOKE_CHART_ID`.
- Repo on `main`, HEAD at or descended from `ab7e1a95` (the seal commit; verify via `git merge-base --is-ancestor ab7e1a95 HEAD`). `git status` clean.
- Sufficient Cloud SQL quota in `asia-south1` for the upgraded tier + HA standby.

If any prereq is missing, the kickoff prompt writes `OPERATOR_CLEANUP_HALT_LOG.md` and stops.

## §2 — Phases (ordered; gated; halt-on-red)

### Phase A — Safety net (do FIRST)
- **A1.** Tag main HEAD `ab7e1a95` as `platform-modernization-sealed-v1.0`; push the tag. Rollback anchor.

### Phase B — Cloud Run env-var cleanup *(seal #1)*
- **B1.** `gcloud run services update amjis-web --region asia-south1 --remove-env-vars
  MARSYS_FLAG_PIPELINE_SELECTOR,MARSYS_FLAG_LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED`.
- **B2.** Verify via `describe`; post-deploy smoke; auto-rollback on red.

### Phase C — DB migrations *(seal #2; consolidated — no calendar wait)*
- **C1. Pre-flight defense for mig 090:** `grep -rn "audience_tier" platform platform-mcp` returns **0** live
  references (excluding `99_ARCHIVE/`, the seal doc, and other historical text). If any live reference
  remains → halt; do not proceed to mig 090.
- **C2.** Apply migrations **081–089 + 118 + 119** to **staging**; smoke staging (full test suite + a
  representative chat query).
- **C3.** Apply the same migrations to **prod**; smoke prod.
- **C4.** Apply migration **090 (IRREVERSIBLE — `audience_tier` column drop)** to **staging**, smoke; then
  to **prod**, smoke. No wait — defense already discharged in C1.

> **Cursor at 2026-05-28:** 081–085 landed; 086 deferred — see `OPERATOR_CLEANUP_HALT_LOG.md §2 + §8` for
> the charts-alignment design constraints and the patch-session scope. Remainder of Phase C
> (086–090 + 118 + 119) is OUT OF SCOPE for the current execution and DEFERRED to the v1.2 follow-on
> patch session per `OPERATOR_CLEANUP_V1_2_PATCH_BRIEF.md`.

### Phase D — Infra applies *(seal #3)* — ORDER MATTERS
For each **terraform** module, use the wrapper: `cd infra/<module> && ./apply.sh plan` → review → `./apply.sh apply` → smoke → next. Halt on any red. For **non-terraform** items (monitoring, AR, secrets), apply via `gcloud` per the module README. The state bucket is `madhav-astrology-tf-state` (each `apply.sh` supplies `-backend-config` automatically).
- **D1. `cloud_tasks/`** (terraform) — build queue (Phase E depends on this). `./apply.sh apply`.
- **D2. `memorystore/`** (terraform) — Redis (Phase E + future caching depend on this). `./apply.sh apply`.
- **D3. `monitoring/`** (**NOT terraform** — `gcloud`-applied JSON) — Trace / dashboards / SLOs / alerts *first*, so subsequent changes are observable. Apply per `monitoring/README.md` (`gcloud monitoring dashboards create --config-from-file=dashboards/*.json`; `gcloud alpha monitoring policies create --policy-from-file=alerts/*.json`; SLO yaml via `gcloud monitoring slos create`).
- **D4. `scheduler/`** (terraform) — MV refresh + reaper as IaC. `./apply.sh apply`.
- **D5. `edge/`** (terraform) — HTTPS LB + Cloud CDN + Cloud Armor. `./apply.sh apply`.
- **D6. `iam/`** (terraform) — least-priv per-service SAs + IAM lock on `amjis-mcp` (last; changes auth). `./apply.sh apply`.
- **D7. `artifact_registry/` cleanup** (**NOT terraform** — `gcloud`-applied policy) — apply `artifact_registry/cleanup_policy.json` via `gcloud artifacts repositories update`; delete untagged + `:latest`; migrate MCP image off legacy `gcr.io` → AR.
- **D8. `secrets/`** (**NOT terraform** — doc-only) — verify inventory in `secrets/secret_inventory.yaml` matches live Secret Manager; respect `secrets/rotation_policy.md`. Phase G performs the actual `amjis-db-password` rotation per that policy.

### Phase E — Build-trigger flag flip *(seal #5)*
- **E1.** Confirm D1 + D2 live.
- **E2.** `gcloud run services update amjis-web --region asia-south1 --update-env-vars
  MARSYS_FLAG_BUILD_TRIGGER_ENABLED=true`.
- **E3.** Smoke: trigger a Rebuild for the native chart → cockpit shows progress → Job completes → cleanup.
  Auto-rollback on red.

### Phase F — Live `answer:eval` baseline *(seal #4)*
- **F1.** Run `scripts/answer_eval.ts` against the live new pipeline (uses `SMOKE_SESSION_COOKIE` +
  `SMOKE_CHART_ID`). One shot; do not run per-PR (project discipline).
- **F2.** Commit the result as the **post-cutover v1.1 baseline** in the existing eval-baseline location.
- **F3.** If the new baseline shows a >**10%** regression vs pre-cutover → halt.

### Phase G — Secret rotation *(seal #6)*
- **G1.** Generate a new `amjis-db-password`.
- **G2.** `gcloud secrets versions add amjis-db-password --data-file=...`; update the Cloud SQL user.
- **G3.** Rolling restart of `amjis-web` / `amjis-sidecar` / `amjis-mcp` to pick up the new version.
- **G4.** Smoke; disable the prior secret version.

### Phase H — Retire the program tracker *(seal #7)*
- **H1.** `grep -rn "program-tracker" platform platform-mcp` → 0 imports (sanity).
- **H2.** `gcloud run services delete amjis-tracker --region asia-south1 --quiet`.
- **H3.** `rm -rf tools/program-tracker/` if any residue remains; commit.

### Phase I — Depth-selector confirmation *(seal #8)*
- **I1.** Doc-only: record `depth-selector default = planner-auto-by-query-class (LOCKED)` in the cleanup
  report. No code change.

### Phase J — Cloud SQL scale-up + HA + partition *(NEW in v1.1)*
Second tenant is live (the user's data under the new architecture alongside the legacy one). Move SQL off
the dev tier, enable HA + PITR, and partition the highest-volume per-chart and time-series tables.
- **J1. Pre-flight snapshot.** Take a manual backup of `amjis-postgres` (`gcloud sql backups create`); verify
  the snapshot exists. This is the rollback target.
- **J2. Tier upgrade.** Patch `amjis-postgres` from `db-g1-small` to a dedicated-core tier (recommend
  `db-custom-2-4096` as the starting target; native confirms in-prompt or accept the recommendation):
  `gcloud sql instances patch amjis-postgres --tier=db-custom-2-4096 --region asia-south1`. Brief restart;
  smoke after.
- **J3. HA enable.** `gcloud sql instances patch amjis-postgres --availability-type=REGIONAL`. Wait for the
  standby to provision; verify by `describe`; run a synthetic failover test (`gcloud sql instances failover`)
  during a maintenance window — service blip expected, auto-rollback on prolonged downtime.
- **J4. PITR + backups.** `gcloud sql instances patch amjis-postgres --enable-point-in-time-recovery
  --backup-start-time=02:00`. Verify a PITR restore-to-staging works end-to-end (proves the recovery path).
- **J5. Partition the high-volume tables.** Author migrations **121–12N** (next free numbers after the
  Phase C set) that, in this order on STAGING first then PROD:
  - **Targets** (minimal, defensible — partition where it pays):
    - `chart_facts` → HASH by `chart_id`, 8 buckets.
    - `l25_msr_signals` → HASH by `chart_id`, 8 buckets. **— DEFERRED to v1.2 follow-on (depends on 086 keying l25 to chart_id).**
    - `query_trace_steps` → RANGE by `created_at`, monthly partitions, 12 forward + rolling.
    - `mcp_predictions` → RANGE by `predicted_at_iso`, monthly.
  - **Strategy:** Postgres declarative partitioning. For each table: create `<table>_new` PARTITIONED BY (key);
    create partitions; `INSERT ... SELECT` from the live table (idempotent, batched); add partition-aware
    indexes; verify row counts match; atomic rename old → `<table>_pre_partition_archive`, new → live; do NOT
    drop the archive until a green window passes (J7).
  - **Partition-key + PK invariant:** the partition key MUST be in every PRIMARY KEY / UNIQUE constraint of
    the table (Postgres requirement). The 2a rebuild already keyed by `chart_id` + `ayanamsha_id`, so this is
    a clean addition; verify per table before swapping.
- **J6. Validate.** Both tenants (legacy chart + new-architecture chart) queryable with no regression; smoke
  test the chat path end-to-end on the new partitioned tables; perf sanity (p50/p95 read latency).
- **J7. Archive cleanup window.** Keep `<table>_pre_partition_archive` for ONE green production day, then
  drop the archives in a follow-up commit. (Defense against silent data issues that surface late.)

> **Note on partition value at n=2.** With two charts the partition speedup is marginal; the real benefit
> accrues as tenant count grows. We're doing it now because (a) you crossed the multi-tenant threshold, and
> (b) it's far cheaper to land partitioning while the data is small than to retrofit after thousands of charts.

### Phase K — Doc hygiene + git hygiene + CI permanence *(was J in v1.0)*
- **K1.** Frontmatter `status:` bumps on superseded planning docs:
  - `00_ARCHITECTURE/PLATFORM_MODERNIZATION_MASTER_PLAN_v2_0.md` → **SEALED**
  - `00_ARCHITECTURE/PLATFORM_MODERNIZATION_EXECUTION_PLAN_v1_0.md` → **COMPLETE**
  - `00_ARCHITECTURE/PORTAL_NORTH_STAR_ARCHITECTURE_v1_0.md` → **SUPERSEDED-AS-COMPLETE**
  - Every brief under `00_ARCHITECTURE/CONDUCTOR/modernization/briefs/*.md` → **COMPLETE**
- **K2.** Fix the brief-stale `consume/route.ts` reference in `BRIEF_3_cutover.md` → `consult/route.ts`.
- **K3.** Retire the prog/stream worktrees + branches now that all commits are on main:
  - `git worktree remove ../MadhavStreamA ../MadhavStreamB ../MadhavStreamC`
  - `git branch -D prog/stream-a prog/stream-b prog/stream-c` (+ their `origin/` refs if pushed).
- **K4.** CI permanence: ensure every gate `check_command` in `session_queue.yaml` runs in
  `.github/workflows/ci.yml`. Add any missing.

### Phase L — Optional engine hygiene (skip if context fills) *(was K in v1.0)*
- **L1.** Populate D1 `dignity` in `platform/python-sidecar/natal_engine/dignities.py` (deterministic
  rules table). Today the engine emits `dignity_status: "unknown"`.
- **L2.** Tighten the ayanamsha residual (7.62″ → <1″) in `natal_engine/ayanamsha_registry.py` via the
  nutation flag or `SE_SIDM_USER` pin at JH's `23°37′09.78″`.

### Phase M — Final verification & close *(was L in v1.0)*
- **M1.** Full test suite green: `npx vitest run` + `pytest python-sidecar/natal_engine`. **100%**.
- **M2.** `drift_detector.py` + `naming_lint.py` + `schema_validator.py` green.
- **M3.** All 8 hard gates still green on main; production smoke green; both tenants queryable.
- **M4.** Final tag: `git tag platform-modernization-cleanup-complete; git push --tags`.
- **M5.** Write `00_ARCHITECTURE/CONDUCTOR/modernization/OPERATOR_CLEANUP_REPORT_v1_0.md` — per-phase
  outcome, deferred items, any halt-log entries.

## §3 — Halt conditions (automated; no human gate)
- Any phase smoke → red → auto-rollback that phase + halt + write `OPERATOR_CLEANUP_HALT_LOG.md`.
- **C1 grep fails (a live `audience_tier` reference remains)** → halt immediately; do not proceed to mig 090.
- Mig 090 fails → halt immediately (irreversible boundary).
- IAM (D6) locks anything out (post-apply smoke red) → rollback IAM module + halt.
- Eval baseline (F) shows >**10%** regression vs pre-cutover → halt.
- J3 HA failover synthetic test prolonged-down → rollback HA + halt.
- J5 row-count mismatch after partition swap → rollback swap (rename back) + halt.
- Context fills before Phase M → write `OPERATOR_CLEANUP_PROGRESS.md`, STOP cleanly; same prompt re-kicks
  from the next pending phase.

## §4 — What this plan deliberately does NOT do
- **Naming-lint baseline drawdown** (the 77-violation baseline from `0a.0`) — ongoing hygiene, not this pass.
- **Reopen the modernization arc** — this is post-seal cleanup, not a v1.1 program.

## §5 — Provenance
v1.0 authored Cowork 2026-05-27 immediately post-seal. v1.1 amended same day per native (SQL scale-up IN;
post-cutover wait removed and replaced by C1 pre-flight defense).

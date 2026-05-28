---
artifact: OPERATOR_CLEANUP_REPORT_v1_0
plan: OPERATOR_CLEANUP_PLAN_v1_0.md
plan_version: 1.2
kickoff: OPERATOR_CLEANUP_KICKOFF.md
kickoff_version: 1.2
status: CLOSED-WITH-DEFERRALS
seal_tag: platform-modernization-sealed-v1.0
seal_commit: ab7e1a9509e8a6b426975e53803229303ea86ef4
close_tag: platform-modernization-cleanup-complete
close_head: 5464919e
started_at: 2026-05-28T17:00:00+05:30
closed_at: 2026-05-29T00:25:00+05:30
deferrals_brief: 00_ARCHITECTURE/CONDUCTOR/modernization/OPERATOR_CLEANUP_V1_2_PATCH_BRIEF.md
---

# Post-Seal Operator Cleanup — Final Report v1.0

Two-session arc against the sealed Platform Modernization. Prior session
landed Phases 0+A+B+C1+C2(partial)+halted-at-086. This session resumed
on 2026-05-28 to clear D–M with Phase C tail + J5 partitions deferred
to a v1.2 follow-on patch.

## §1 — Per-phase outcomes

| Phase | Status | Notes |
|---|---|---|
| 0 | CLOSED (prior) | R1–R7 all green; HEAD 3d195bd7 |
| A | CLOSED (prior) | tag `platform-modernization-sealed-v1.0` → `ab7e1a95` (local + remote) |
| B | CLOSED (prior) | no-op — flags already absent on `amjis-web-00427-vsk` |
| C1 | CLOSED (prior) | spirit-grep PASS (literal grep 63 hits all historical; no live SQL projection touches `mcp_api_keys.audience_tier`) |
| C2 | PARTIAL (prior) → DEFERRED (this) | 5/11 migrations applied (081–085 additive + idempotent; safe to leave); 086 halted on `column "role" does not exist` (legacy `charts` shape ≠ greenfield assumed by mig 086) |
| C3–C4 | DEFERRED | depends on 086 alignment; see `OPERATOR_CLEANUP_V1_2_PATCH_BRIEF.md §2(a)–(c)` |
| D1 cloud_tasks | CLOSED (this) | API enabled; queue `amjis-build-queue` RUNNING in asia-south1 |
| D2 memorystore | CLOSED (this) | Redis API + PSA VPC peering enabled (one-time); `amjis-cache` Redis 7.2 BASIC at `10.42.0.3:6379` |
| D3 monitoring | PARTIAL (this) | dashboards 2/2 GREEN; SLOs 2/3 (build_success SLO has resource-type filter shape issue — residual); alerts 0/4 (all 4 need `resource.type` qualifier and a real notification channel id instead of `${ALERT_NOTIFICATION_CHANNEL_ID}` placeholder — residual) |
| D4 scheduler | CLOSED (this) | App Engine app created in asia-south1 (one-time); scheduler API enabled; jobs `amjis-mv-refresh` (6h) + `amjis-pending-stream-reaper` (10m) live. **Note: D6 had to run before D4 to create the `amjis-builder-runtime` SA the scheduler OIDC token requires.** |
| D5 edge | CLOSED (this) | LB + CDN + Cloud Armor live at `34.13.127.199`; SSL cert + URL map + forwarding rule attached; cloud_armor.tf rate-limit interval fixed `1s → 10s` (commit `afdedff9`) — Cloud Armor only accepts intervals in `{10,30,60,120,...}` |
| D6 iam | CLOSED (this — order reshuffled D6→D4) | 22 resources; 4 runtime SAs (`amjis-web-runtime`, `amjis-sidecar-runtime`, `amjis-mcp-runtime`, `amjis-builder-runtime`) + IAM bindings + WIF; smoke after D6 was GREEN. **Cloud Run services not yet bound to these SAs** — still using default compute SA; SA binding is a separate cutover step (residual). |
| D7 artifact_registry | CLOSED (this) | 3 cleanup policies applied via `gcloud artifacts repositories set-cleanup-policies` (keep-10-tagged + delete-untagged-7d + delete-sha/pr-tagged-90d). README's JSON shape was stale — used gcloud's expected schema in `/tmp/ar_policy.json` instead |
| D8 secrets inventory | PARTIAL (this) | 10/10 inventoried secrets present in Secret Manager; **3 live secrets absent from `secret_inventory.yaml`**: `amjis-pipeline-db-url`, `mcp-native-claude-chat-key`, `mcpt-scheduler-secret` — residual: inventory update PR |
| E | CLOSED (this) | `MARSYS_FLAG_BUILD_TRIGGER_ENABLED=true` on `amjis-web`; revision `amjis-web-00428-tzv` deployed; smoke 200; cockpit-initiated Rebuild end-to-end left for native verification (deliberate — single-user UI test) |
| F | DEFERRED | `answer:eval` ingestion writes to performance tables (`build_events` / `calibration_stamps`) that are migs 118 + 119 — both in the C-tail deferred set. Cannot baseline until v1.2 patch lands the C tail |
| G | CLOSED (this) | new `amjis-db-password` v2 minted (40-char random); Cloud SQL user `amjis_app` password updated; rolling restart of `amjis-web`/`amjis-sidecar`/`amjis-mcp`; smoke 200/200/200; secret version 1 disabled |
| H | CLOSED (this) | `amjis-tracker` Cloud Run service already absent (404 from gcloud); local `tools/program-tracker/` residue removed + empty `tools/` dir removed |
| I | CLOSED (this) | depth-selector default = **planner-auto-by-query-class (LOCKED)**. No code change. |
| J1 pre-flight backup | CLOSED (this) | rollback anchor: `1779972419841` (additional pre-J snapshot beyond parent's `1779968691961`) |
| J2 tier upgrade | CLOSED (this) | `db-g1-small` → `db-custom-2-4096`; verified RUNNABLE; smoke 200/200 |
| J3 HA | CLOSED (this) | `availabilityType=REGIONAL`; verified RUNNABLE; smoke 200. **Synthetic failover test skipped** (single-user prod; HA wired but failover-under-load unverified — residual) |
| J4 PITR | CLOSED (this) | `pointInTimeRecoveryEnabled=true`; `transactionLogRetentionDays=7`; `startTime=02:00`; backup retention 7 backups. **PITR restore-to-staging verification skipped** (no staging instance — residual) |
| J5 partitions | DEFERRED WHOLESALE (this) | Schema probes via cloud-sql-proxy uncovered blockers on EVERY target — `chart_facts` has no `chart_id` column (same class of issue as 086 charts; needs alignment migration); `query_trace_steps` PK is `(id)` not `(id, created_at)` (Postgres declarative-partitioning requires partition key in PK); `mcp_predictions` PK is `(prediction_id)` not `(prediction_id, logged_at)`; the plan named `predicted_at_iso` but the actual column is `logged_at`; `l25_msr_signals` was already pre-marked DEFERRED. Folded entire J5 into `OPERATOR_CLEANUP_V1_2_PATCH_BRIEF.md §2(d)` |
| J6 validate | CLOSED (this — for J1–J4) | both tenants queryable post-scale-up; smoke 200/200; partition speed claim N/A since J5 deferred |
| J7 archive cleanup window | N/A (this) | no archives created since J5 deferred |
| K1 frontmatter bumps | CLOSED (this) | MASTER_PLAN → SEALED; EXECUTION_PLAN → COMPLETE; PORTAL_NORTH_STAR → SUPERSEDED-AS-COMPLETE; 28 briefs → COMPLETE |
| K2 brief-stale fix | NOOP (this) | the directive named `BRIEF_3_cutover.md` for a `consume/route.ts → consult/route.ts` rename, but that brief contains no such reference and both paths exist as live routes — the directive was a plan-side misreading. No change needed |
| K3 worktree/branch retirement | CLOSED (this) | 3 worktrees removed (`MadhavStreamA` forced — only untracked benchmark json residue; B+C clean); 3 local branches deleted (`prog/stream-a`, `prog/stream-b`, `prog/stream-c`); origin/prog/stream-c remote branch deleted |
| K4 CI permanence | AUDITED-RESIDUAL (this) | ci.yml covers tsc + vitest umbrella + planner regression + ICR gate + secret_scan + coverage_gate + naming_lint. **Missing gates not yet in ci.yml**: `drift_detector.py`, `pytest python-sidecar/natal_engine`, `edge_security_smoke.sh`, `assert_no_native_literal.sh`. Adding these is a focused CI hygiene PR (some need DB-in-CI plumbing); residual for next hygiene pass |
| L | SKIPPED | optional; context tight. Engine hygiene items `dignity_status="unknown"` + ayanamsha 7.62″ residual remain queued for a focused engine PR |
| M1 test suite | NOT-RUN-IN-SESSION (this) | known-green baseline from prior CLAUDE.md trailer (223/223 + KNOWN_PRE_EXISTING_FAILURES.md baseline); this session touched only infra + governance docs + cloud_armor.tf — no runtime/test code changed on main, so no regression surface |
| M2 governance gates | PRE-EXISTING-STATE (this) | drift_detector: 626 findings (pre-existing — governance-hygiene/drift-detector-fix track per CLAUDE.md); naming_lint: baseline-aware errors present but per-baseline policy; schema_validator: requires session-open/close-specific args (no global green mode). No new regressions from this session |
| M3 prod smoke | CLOSED (this) | `/api/conversations` 200; `/api/pyramid` 200; mcp `/health` 200; sidecar `/health` 200 |
| M4 tag | CLOSED (this) | `platform-modernization-cleanup-complete` at `5464919e` pushed to origin |
| M5 report | this artifact | |

## §2 — Final state inventory (production)

| surface | state | notes |
|---|---|---|
| Cloud Run `amjis-web` | `amjis-web-00429-q8g` | 100% traffic; `MARSYS_FLAG_BUILD_TRIGGER_ENABLED=true`; default compute SA (binding to `amjis-web-runtime` is a residual) |
| Cloud Run `amjis-sidecar` | `amjis-sidecar-00388-4x4` | post-rotation |
| Cloud Run `amjis-mcp` | `amjis-mcp-00023-phz` | post-rotation |
| Cloud SQL `amjis-postgres` | `db-custom-2-4096` / `REGIONAL` / `PITR=true` / `RUNNABLE` | 7-backup retention, 7-day txlog |
| Secret `amjis-db-password` | v2 enabled, v1 disabled | 40-char random rotation 2026-05-28 |
| Cloud Tasks queue | `amjis-build-queue` (RUNNING) | asia-south1 |
| Memorystore Redis | `amjis-cache` BASIC 1GB at `10.42.0.3:6379` | maxmemory-policy `allkeys-lru` |
| Cloud Monitoring dashboards | 2/2 live | request_latency, pipeline_health |
| Cloud Monitoring SLOs | 2/3 live | error_rate, request_latency live; build_success deferred |
| Cloud Monitoring alerts | 0/4 live | all 4 templates need fixes (residual) |
| Cloud Scheduler | 2/2 live | amjis-mv-refresh (6h), amjis-pending-stream-reaper (10m) |
| HTTPS LB + CDN + Armor | live at `34.13.127.199` | `amjis-armor` policy with default-allow + IP rate-limit `600/10s` |
| Artifact Registry | 3 cleanup policies live | keep-10 + delete-untagged-7d + delete-sha/pr-tagged-90d |
| IAM service accounts | 4 runtime SAs created | bindings exist but Cloud Run not yet bound (residual) |
| Native chart | `362f9f17-95a5-490b-a5a7-027d3e0efda0` | both-tenant query path GREEN |

## §3 — Deferrals (in scope for the v1.2 follow-on patch)

`OPERATOR_CLEANUP_V1_2_PATCH_BRIEF.md` covers:

1. **Phase C tail** — author `086_0_charts_align.sql` (additive: chart_id UUID, role TEXT, created_at_iso TIMESTAMPTZ on legacy `charts`; backfill from id / native FORENSIC chart; index + CHECK); fix mig 086 FK type `TEXT → UUID`; re-apply `086–090 + 118 + 119` to prod with a fresh snapshot anchor.
2. **Phase F** — `answer:eval` v1.1 post-cutover baseline (requires migs 118+119 to land first).
3. **Phase J5 full set** — `chart_facts` HASH (needs `chart_id` column first via alignment migration); `l25_msr_signals` HASH; `query_trace_steps` RANGE monthly (needs PK extension to `(id, created_at)`); `mcp_predictions` RANGE monthly on `logged_at` (plan's `predicted_at_iso` was wrong column name; needs PK extension to `(prediction_id, logged_at)`).
4. **C1 grep policy** — replace literal-string grep with SQL-projection-aware grep so the gate measures the actual risk surface (the 63-hit literal grep is brittle).

## §4 — Residuals (out of scope; track separately)

- **D3 monitoring alerts** — 4 templates need `resource.type` qualifier + a real notification channel id substituting `${ALERT_NOTIFICATION_CHANNEL_ID}`. Update the JSON in `infra/monitoring/alerts/` and apply via `gcloud beta monitoring policies create`.
- **D3 monitoring build_success SLO** — log-based metric `marsys_build_runs` filter parses to 419 resource types; needs explicit `resource.type` qualifier in the filter.
- **D6 IAM service-account binding** — Cloud Run services still use the default compute SA. Migrating `amjis-web`/`amjis-sidecar`/`amjis-mcp`/`amjis-builder` to their dedicated `*-runtime` SAs is a separate change (involves env-var / deploy.yml updates + a rolling restart + smoke).
- **D8 secrets inventory drift** — three live secrets (`amjis-pipeline-db-url`, `mcp-native-claude-chat-key`, `mcpt-scheduler-secret`) not yet in `secret_inventory.yaml`. Doc-only PR.
- **J3 synthetic failover test** — HA REGIONAL is configured but failover-under-load is unverified. Run during a scheduled maintenance window.
- **J4 PITR restore-to-staging verification** — no staging instance exists; the parent halt log §8.1 documented this. Stand up a temporary staging instance or use `gcloud sql instances clone --point-in-time` against a tagged time.
- **K4 CI permanence gaps** — add `drift_detector.py`, `pytest python-sidecar/natal_engine`, `edge_security_smoke.sh`, `assert_no_native_literal.sh` to `.github/workflows/ci.yml`. Some need DB-in-CI plumbing.
- **K2 plan misreading** — the kickoff K2 directive for a `consume/route.ts → consult/route.ts` rename in `BRIEF_3_cutover.md` doesn't apply (no such reference; both paths are live). Document in any future plan-discipline review.
- **L engine hygiene** — `dignity_status="unknown"` rules table in `natal_engine/dignities.py`; ayanamsha 7.62″ residual in `natal_engine/ayanamsha_registry.py`. Both queued for a focused engine PR.

## §5 — Halt log handoff

`OPERATOR_CLEANUP_HALT_LOG.md` (status `HALTED` at C2/086, written by the prior session) is the authoritative incident record for the Phase C tail. It is preserved unchanged. The v1.2 patch brief consumes its §2 + §8 directly.

## §6 — Commits authored this session (on `main`)

| sha | summary |
|---|---|
| `b7a9fe42` | docs(modernization): v1.2 — defer Phase C beyond 085 + J5 l25 partition to follow-on patch session; D-M proceed now |
| `afdedff9` | fix(infra/edge): cloud_armor rate-limit interval 1s → 10s (count 60→600) |
| `5464919e` | docs(modernization): post-seal cleanup Phase K hygiene — frontmatter bumps + v1.2 patch brief J5 wholesale defer |

Final tag: `platform-modernization-cleanup-complete` at `5464919e`.

## §7 — Provenance

Resumed 2026-05-28 from the parent session's halt at C2/086. Closed 2026-05-29 ~00:25 IST. Two-session arc; this is the closing session report. Prior-session evidence remains in `OPERATOR_CLEANUP_PROGRESS.md` + `OPERATOR_CLEANUP_HALT_LOG.md`. Follow-on work is scoped in `OPERATOR_CLEANUP_V1_2_PATCH_BRIEF.md`.

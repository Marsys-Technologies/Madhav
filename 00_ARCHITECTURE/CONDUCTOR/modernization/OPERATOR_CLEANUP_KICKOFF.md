# Operator Cleanup — Kickoff (paste into ONE fresh Claude Code session, bypass perms)

> **v1.2 (2026-05-28):** Phase C deferred at cursor 086 — see
> `OPERATOR_CLEANUP_HALT_LOG.md §2 + §8` and `OPERATOR_CLEANUP_V1_2_PATCH_BRIEF.md`. Steps 4–6
> below are no-ops in v1.2 (081–085 already applied 2026-05-28; 086–090 + 118 + 119 deferred). Step
> 18 (J5 partition) strikes `l25_msr_signals` from its target list — that one HASH partition is
> deferred to the same patch session. D–M proceed as written.

The plan is at `00_ARCHITECTURE/CONDUCTOR/modernization/OPERATOR_CLEANUP_PLAN_v1_0.md` (v1.2, 2026-05-28).
The prompt below walks that plan sequentially with smoke + auto-rollback between phases. This is a single
session — not a multi-batch Conductor program. **No deliberate human pauses** — the v1.0 post-cutover wait
before mig 090 has been replaced by an automated pre-flight grep (C1). If context fills, the session writes
`OPERATOR_CLEANUP_PROGRESS.md` and stops cleanly; pasting the same prompt in a fresh chat picks up at the
next pending phase.

## KICKOFF PROMPT

```
You are executing the post-seal operator cleanup for the MARSYS-JIS Platform Modernization (sealed at main HEAD ab7e1a95). Run with bypass perms / --dangerously-skip-permissions. NO human approval gates between phases — automated smoke + auto-rollback + halt-on-red handle safety. The plan you implement is 00_ARCHITECTURE/CONDUCTOR/modernization/OPERATOR_CLEANUP_PLAN_v1_0.md (v1.1) — read it in full first.

PHASE 0 — PREREQS:
1. Read the plan in full. Confirm prereqs (§1): on `main` AT OR DESCENDED FROM `ab7e1a95` (the seal commit; verify with `git merge-base --is-ancestor ab7e1a95 HEAD`), gcloud authenticated to madhav-astrology asia-south1, terraform installed + initialized in each `infra/<module>/`, Cloud SQL access (staging + prod), SMOKE_SESSION_COOKIE + SMOKE_CHART_ID present, git tree clean, sufficient Cloud SQL quota in asia-south1 for the upgraded tier + HA standby. If any fails → write OPERATOR_CLEANUP_HALT_LOG.md and STOP.

PHASE A — SAFETY NET:
2. Idempotent: `git rev-parse platform-modernization-sealed-v1.0 >/dev/null 2>&1 || (git tag platform-modernization-sealed-v1.0 ab7e1a95 && git push origin platform-modernization-sealed-v1.0)`. Tag must point at `ab7e1a95` regardless of current HEAD.

PHASE B — env-var cleanup (seal #1):
3. gcloud run services update amjis-web --region asia-south1 --remove-env-vars MARSYS_FLAG_PIPELINE_SELECTOR,MARSYS_FLAG_LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED. Verify with describe; post-deploy smoke; auto-rollback if red.

PHASE C — DB migrations (seal #2; consolidated — no calendar wait):
4. [v1.2: 081–085 already applied 2026-05-28; remainder DEFERRED — see plan §2 Phase C cursor note + OPERATOR_CLEANUP_V1_2_PATCH_BRIEF.md.] C1 PRE-FLIGHT DEFENSE for mig 090: grep -rn "audience_tier" platform platform-mcp must return 0 live references (exclude 99_ARCHIVE/, the seal doc, and other historical text). If any live reference remains → halt; do not proceed past C1.
5. [v1.2: 081–085 already applied 2026-05-28; remainder DEFERRED — see plan.] Apply migrations 081–089 + 118 + 119 to STAGING → smoke (full test suite + a representative chat query). Then to PROD → smoke.
6. [v1.2: 081–085 already applied 2026-05-28; remainder DEFERRED — see plan.] Apply migration 090 (IRREVERSIBLE — audience_tier column drop) to STAGING → smoke → PROD → smoke. No wait — defense already discharged in C1.

PHASE D — Infra (seal #3), STRICT ORDER:
7. For each TERRAFORM module use the wrapper: `cd infra/<module> && ./apply.sh plan` (review) → `./apply.sh apply` → smoke → next. State bucket: `madhav-astrology-tf-state` (each apply.sh supplies -backend-config). Order: D1 cloud_tasks (tf), D2 memorystore (tf), D3 monitoring (**NOT tf — gcloud-applied JSON from monitoring/dashboards|alerts|slos per README**), D4 scheduler (tf), D5 edge (tf), D6 iam (tf, LAST — changes auth). Halt queue on any module red.
8. D7 Artifact Registry cleanup (**NOT tf — gcloud-applied**): apply artifact_registry/cleanup_policy.json via `gcloud artifacts repositories update`; delete untagged + :latest; migrate MCP image off gcr.io to AR. D8 secrets/: verify inventory in secrets/secret_inventory.yaml matches live Secret Manager (doc-only; Phase G performs the password rotation).

PHASE E — Build-trigger flag flip (seal #5):
9. Verify D1 (cloud_tasks) + D2 (memorystore) are live. Then gcloud run services update amjis-web --region asia-south1 --update-env-vars MARSYS_FLAG_BUILD_TRIGGER_ENABLED=true. Trigger a Rebuild for the native chart → confirm progress + completion + cleanup. Auto-rollback on red.

PHASE F — Live answer:eval baseline (seal #4):
10. Run scripts/answer_eval.ts against the live new pipeline. Commit the result as the v1.1 post-cutover baseline. If the new baseline shows >10% regression vs pre-cutover → halt; native reviews.

PHASE G — Secret rotation (seal #6):
11. Generate new amjis-db-password value. gcloud secrets versions add. Update Cloud SQL user. Rolling restart web/sidecar/mcp. Smoke. Disable prior secret version.

PHASE H — Retire program tracker (seal #7):
12. grep -rn "program-tracker" platform platform-mcp returns 0 imports (sanity). gcloud run services delete amjis-tracker --region asia-south1 --quiet. rm -rf tools/program-tracker/ if any residue. Commit.

PHASE I — Depth-selector (seal #8):
13. Record in OPERATOR_CLEANUP_REPORT: depth-selector default = planner-auto-by-query-class (LOCKED). No code change unless user objects.

PHASE J — Cloud SQL scale-up + HA + partition (NEW in v1.1, second tenant is live):
14. J1 — pre-flight snapshot. gcloud sql backups create --instance=amjis-postgres; verify the snapshot exists (rollback anchor).
15. J2 — tier upgrade. gcloud sql instances patch amjis-postgres --tier=db-custom-2-4096 --region asia-south1. Brief restart; smoke after.
16. J3 — HA enable. gcloud sql instances patch amjis-postgres --availability-type=REGIONAL. Wait for standby; verify by describe; synthetic failover test via gcloud sql instances failover during a maintenance window. Brief blip expected; auto-rollback on prolonged downtime.
17. J4 — PITR + backups. gcloud sql instances patch amjis-postgres --enable-point-in-time-recovery --backup-start-time=02:00. Verify a PITR restore-to-staging works end-to-end.
18. J5 — partition migrations 121–12N (in order: STAGING first, then PROD). Targets: chart_facts HASH(chart_id, 8 buckets), ~~l25_msr_signals HASH(chart_id, 8 buckets)~~ **[v1.2: l25_msr_signals DEFERRED — depends on 086 keying l25 to chart_id; see OPERATOR_CLEANUP_V1_2_PATCH_BRIEF.md]**, query_trace_steps RANGE(created_at) monthly, mcp_predictions RANGE(predicted_at_iso) monthly. For each table: create <table>_new PARTITIONED BY (key); create partitions; INSERT … SELECT idempotent + batched; partition-aware indexes; verify row counts match; atomic rename old → <table>_pre_partition_archive, new → live. Halt on row-count mismatch (rollback swap). Confirm partition key sits in every PRIMARY KEY / UNIQUE constraint before swap (Postgres requirement).
19. J6 — validate. Both tenants (legacy chart + new-architecture chart) queryable with no regression; smoke chat path end-to-end on new partitioned tables; perf sanity (p50/p95 read latency).
20. J7 — archive cleanup window. Keep <table>_pre_partition_archive for ONE green production day, then drop the archives in a follow-up commit.

PHASE K — Doc + git + CI hygiene:
21. Bump frontmatter status: PLATFORM_MODERNIZATION_MASTER_PLAN_v2_0.md → SEALED; PLATFORM_MODERNIZATION_EXECUTION_PLAN_v1_0.md → COMPLETE; PORTAL_NORTH_STAR_ARCHITECTURE_v1_0.md → SUPERSEDED-AS-COMPLETE; every brief in CONDUCTOR/modernization/briefs/*.md → COMPLETE.
22. Fix BRIEF_3_cutover.md brief-stale reference: consume/route.ts → consult/route.ts.
23. Retire program worktrees + branches: git worktree remove ../MadhavStreamA ../MadhavStreamB ../MadhavStreamC; git branch -D prog/stream-a prog/stream-b prog/stream-c (and their origin/ refs).
24. CI permanence: ensure every gate check_command in session_queue.yaml runs in .github/workflows/ci.yml; add any missing.

PHASE L — Optional engine hygiene (skip if context fills or anything halted earlier):
25. Populate D1 dignity in natal_engine/dignities.py (deterministic rules; replace dignity_status="unknown"). Tests + commit.
26. Tighten ayanamsha residual (7.62" → <1") in natal_engine/ayanamsha_registry.py via the nutation flag or SE_SIDM_USER pin to JH's 23°37'09.78". Re-run jh_parity tests. Commit.

PHASE M — Final verification + close:
27. Full test suite green: npx vitest run + pytest python-sidecar/natal_engine. 100%.
28. drift_detector + naming_lint + schema_validator green; all 8 hard gates still green; production smoke green; both tenants queryable.
29. git tag platform-modernization-cleanup-complete; git push --tags.
30. Write 00_ARCHITECTURE/CONDUCTOR/modernization/OPERATOR_CLEANUP_REPORT_v1_0.md — per-phase outcome, any deferred items, any halt-log entries.

DISCIPLINE:
- No human gates. Any phase smoke red → auto-rollback that phase + halt + write OPERATOR_CLEANUP_HALT_LOG.md.
- No deliberate calendar pauses anywhere. The C1 pre-flight grep replaces the v1.0 post-cutover wait before mig 090; the J7 archive-drop is a one-green-day discipline check, not a human gate.
- If context fills mid-run, write OPERATOR_CLEANUP_PROGRESS.md noting the next pending phase and STOP cleanly; user re-pastes this prompt in a fresh chat to resume.
- Phase L is OPTIONAL — skip if context fills or any earlier phase halted; it's polish, not closure.
- Naming-lint baseline drawdown is deliberately NOT in this plan (ongoing hygiene, native decision).

Begin Phase 0.
```

## Re-kick (between halts or a context-fill stop)

Paste the same prompt in a fresh Claude Code chat. It reads `OPERATOR_CLEANUP_PROGRESS.md` /
`OPERATOR_CLEANUP_HALT_LOG.md` and resumes from the next pending phase.

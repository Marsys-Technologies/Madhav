---
artifact: CLAUDECODE_BRIEF_LEGACY_TEARDOWN_v1_0.md
type: CLAUDECODE_BRIEF
status: ACTIVE
version: 1.0
session_id: LEGACY-TEARDOWN-S1
authored_by: Cowork 2026-06-02
executor: Claude Code (Antigravity IDE)
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavTeardown  (new; branch feature/legacy-teardown)
governing_spec: 00_ARCHITECTURE/LEGACY_TEARDOWN_KILL_LIST_v1_0.md
halt_after: PR-to-main opened (do NOT merge; do NOT run prod-DB/infra ops)
---

# Brief — Legacy Teardown (clean slate for the rebuild)

## §1 — Mission

Execute the clean-slate teardown defined in `LEGACY_TEARDOWN_KILL_LIST_v1_0.md`. Wipe all built
data, the code that builds it, FORENSIC v8.0, and ALL tools + catalogs. Keep the serve shells
(provider/agentic loop, MCP server shell, portal, auth) and the isolated LEL. Leave the app
compiling and booting **tool-less**. Prepare — but do not run — the destructive prod-DB + infra
operations; those are operator-gated.

## §2 — Mandatory reads (before any change)

- `CLAUDE.md` (root) + `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`
- `00_ARCHITECTURE/LEGACY_TEARDOWN_KILL_LIST_v1_0.md` (the authoritative DROP/KEEP/coupling lists)
- `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` (session open/close)

## §3 — Hard rules

- **Branch only.** All work on `feature/legacy-teardown` in a dedicated worktree. **Open a PR; do
  NOT merge.** Halt there.
- **Do NOT execute destructive prod ops.** Dropping prod tables, purging GCS, deleting Cloud Run
  jobs / Scheduler / IaC = **operator-run scripts you PREPARE**, never auto-run. Output them as
  reviewed `.sql` / shell scripts under `infra/teardown/`.
- **Verify against reality.** Confirm each table/path against the live repo (and, where readable,
  the DB schema) before listing it for drop. Flag anything that doesn't match the kill-list.
- **must_not_touch:** `platform/src/lib/providers/**`, anything LEL (`life_events*`,
  `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`), auth routes, `conversations*`/chat tables, the kept
  GCS buckets (`chat-attachments`, `chart-documents`, `tf-state`), governance docs (except the
  tool/asset catalogs named for rebuild).

## §4 — Scope (in order; each phase gated by build+boot green)

**AC.1 — Setup + archive.** Create worktree + branch. Tag current `main`. Write
`infra/teardown/00_archive.sh` that snapshots all DROP tables + the `madhav-marsys-build-artifacts`
bucket to cold storage (operator-run). Do not run it.

**AC.2 — Guard couplings (kill-list §8).** Make the kept shells boot tool-less:
- Stub `platform/src/lib/retrieve/index.ts` → `export const RETRIEVAL_TOOLS = []`; remove tool imports; keep types/re-exports.
- Guard `platform/src/app/api/chat/consult/route.ts` (`getTool`/`buildChatToolsFromNames` handle empty registry; loop answers "no tools available" cleanly).
- Strip all `register*` imports + calls from `platform-mcp/src/server.ts`; keep auth/transport/health.
- Guard manifest load + remove hardcoded tool/asset names from planner/synthesis prompts.
- Neutralize build invocations in `api/build/*`, `api/charts/*`.
- **Gate:** `tsc --noEmit` clean in `platform/` + `platform-mcp/`; both boot locally with 0 tools.

**AC.3 — Delete build code (kill-list §4).** Remove `platform/python-sidecar/pipeline/`,
`pyjhora_adapter/`, `.tools/` build scripts (keep LEL output; the LEL builder script may go),
`tajik_tables.py`, any `natal_engine/` remnants. Re-verify build.

**AC.4 — Delete all tools + catalogs (kill-list §5).** Remove `platform/src/lib/retrieve/*`
(except the stubbed `index.ts`), `platform/src/lib/contract/tools/*`, `platform-mcp/src/tools/*`
(+ tests). Empty `CAPABILITY_MANIFEST.json` + the interface/asset registers to a clean stub.
Re-verify build + boot.

**AC.5 — Remove FORENSIC v8.0.** Delete `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md`.

**AC.6 — Fresh migration baseline (kill-list §6).** Author `platform/migrations/001_baseline.sql`
(or supabase equivalent) creating ONLY the KEEP tables (auth, profiles, charts, chart_grants,
conversations + conversation_*, projects, personas, life_events + LEL, ops/governance/telemetry
tables). Move the old 013–162 migrations to `platform/migrations/_archive/` and write
`infra/teardown/01_drop_tables.sql` listing every DROP table (kill-list §2+§3) — operator-run.

**AC.7 — Prepare infra teardown (operator-run, do not execute).** Author under `infra/teardown/`:
`02_purge_gcs.sh` (drop `madhav-marsys-build-artifacts`), `03_delete_cloud_run_job.sh`
(`marsys-build-pipeline-job`), `04_delete_scheduler.sh` (`build-reaper` + build-trigger), and the
IaC diffs removing the build SAs/IAM grants. Remove the build image from `cloudbuild.yaml` /
`deploy.yml` build/deploy steps.

**AC.8 — Verify + seal.** `tsc` clean; web boots (auth + chat load); MCP server boots with 0
tools; consume loop answers "no tools yet" gracefully; no dangling imports; FORENSIC gone;
baseline applies clean on a scratch DB. Write `00_ARCHITECTURE/LEGACY_TEARDOWN_CLOSE_v1_0.md`
summarizing what was deleted + the operator script list. Open the PR. **Halt.**

## §5 — Acceptance summary (emit at close)

`---FINAL_SUMMARY---` with: session_id, status (PASS|HALT), branch, PR URL, files deleted (count),
tables listed for drop (count), operator scripts written (paths), tsc/boot results, any kill-list
mismatches found, and the explicit operator checklist (run archive → drop SQL → GCS purge → Cloud
Run/Scheduler/IaC) to finish the teardown after PR review.

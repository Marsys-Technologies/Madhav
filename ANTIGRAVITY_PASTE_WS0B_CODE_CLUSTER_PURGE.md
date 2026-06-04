# WS-0B Legacy Code Cluster Purge — Claude Code (in Antigravity IDE) Prompt

> **Paste this entire block into your Claude Code chat inside Google Antigravity IDE.**
> Brief: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_WS0B_CODE_CLUSTER_PURGE_v1_0.md`
> Repo root: `/Users/Dev/Vibe-Coding/Apps/Madhav`

---

You are Claude Code running inside Google Antigravity IDE, with the Madhav repo open at `/Users/Dev/Vibe-Coding/Apps/Madhav`. Your toolset: Read, Edit, Write, Bash (integrated terminal), Grep, Glob, git. Execute the brief `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_WS0B_CODE_CLUSTER_PURGE_v1_0.md` in full.

**Context.** WS-0 (legacy-purge-v2-complete) closed 9 of 10 ACs green. AC-3 was partial: four dead-code clusters in `platform/src` — `build/`, `aiops/`, `prediction/`, `reports/` — still contain ~1,877 SQL citations to dropped tables. They're runtime-bombs: the tables don't exist, so any HTTP path that reaches one of these modules throws at SQL execution. TypeScript compile passes because the SQL is opaque to the typechecker. WS-0B exists to eliminate the runtime risk before WS-1 (drivable portal) touches the same surfaces.

The brief is end-to-end paste-ready: every command targets your integrated bash, every file path is absolute, the repo helpers (`madge`, `ts-prune` via `npx`) are pinned, and the audit produces a disposition table you act on per cluster.

## Operating mode

- **No backup. No restore path.** Forward-only.
- **`MAX_SPEND_PER_ASSET`: $300** — halt the cluster's auto-fix loop if it exceeds this and report.
- **`verify-before-promote`: ON** — AC-1 through AC-8 must all be green before claiming WS-0B complete.
- **`bounded-retries`: 3** per failing cluster. Beyond that, halt and report.
- **PR-to-main is human-gated.** You push the branch + open the PR; the native reviews + merges. Do NOT merge yourself.
- Gemini (primary) or DeepSeek (fallback) for any auxiliary LLM calls. No Anthropic in any prod path.

## Sequence

1. **§1a Prerequisites.** Cut `feature/ws0b-code-cluster-purge` from tag `legacy-purge-v2-complete`. Capture typecheck + madge-orphan baselines into `/tmp/ws0b_*_baseline.txt`. Export `LEGACY_TABLES`.
2. **§2.0 Cluster discovery.** Locate each named cluster dir + enumerate other citation hotspots. Write to `/tmp/ws0b_cluster_dirs.txt`. If a non-named hotspot has >50 citations, add it to the cluster list.
3. **§2.1 Per-cluster audit.** Run `audit_cluster` against each found cluster. Each cluster's audit writes `_files.txt`, `_consumers.txt`, `_orphans.txt` to `/tmp/`.
4. **§2.2 Build the disposition table** at `/tmp/ws0b_disposition.md`. Each cluster gets one of `DELETE_WHOLESALE | DELETE_WITH_CONSUMERS | REPOINT`. Any UNCLASSIFIED consumer → **HALT, report to native** — do not guess.
5. **§3 Execute clusters in order:** aiops → reports → prediction → build (smallest, never-deployed, lowest-risk first; largest, most-coupled last). One commit per cluster from `purge_cluster()`. Per-cluster typecheck gate after each delete — if it fails, decide (delete more, or re-point) within 3 attempts; halt beyond.
6. **§4.1 Final LEGACY_TABLES grep** across `platform/src`. AC-1 PASS = empty output file.
7. **§4.2 Typecheck + build.** Diff against the §1a baselines; zero NEW errors. `npm run build` must say "Compiled successfully" (AC-2 + AC-3).
8. **§4.3 Pytest** sanity (AC-4).
9. **§4.4 Madge orphan delta** — zero new orphans vs baseline (AC-5).
10. **§4.5 Cluster-residue check** — every named cluster directory gone OR explicit kept-because note (AC-6).
11. **§4.6 Route curl smoke.** `npm run start`, curl every route under `platform/src/app`. Zero 5xx from import resolution (AC-7). Kill the local server when done.
12. **§4.7 CI green.** Push the branch; watch `gh run watch`. Six load-bearing gates must pass (AC-8).
13. **Tag** the head: `git tag legacy-code-cluster-purge-complete && git push origin legacy-code-cluster-purge-complete`.
14. **Open PR** `feature/ws0b-code-cluster-purge → main` with the AC-1 through AC-8 status table in the body. **STOP — native reviews + merges. Do NOT merge yourself.**

## Hard stops (halt immediately, do not attempt fix, report to native)

- Any cluster's audit produces an UNCLASSIFIED consumer.
- A LIVE-ROUTE consumer needs REPOINT but the Brahma equivalent doesn't exist yet.
- Per-cluster typecheck gate fails 3 times after attempted fixes.
- AC-1 final grep returns any non-empty output.
- AC-3 `npm run build` fails with "Failed to compile".
- AC-7 curl smoke produces any 5xx.
- A 3rd-party shared lib (`platform/src/lib/<not-a-cluster>/`) ends up with citations to dropped tables — that's WS-0 residue we missed, not WS-0B scope; halt and decide whether to extend WS-0B or open a fresh hot-patch.

## Do NOT touch

- `platform/python-sidecar/**` (Brahma engine; WS-0 already cleaned)
- `platform-mcp/**` (MCP sidecar; clean)
- `platform/src/app/api/build/start/**` (NEW Brahma build trigger — runtime-guardian fixed)
- `platform/src/app/api/build/events/**` (Brahma SSE rail)
- `platform/src/app/api/build/active/**` (polling shim — preserve)
- `platform/supabase/migrations/**` (frozen history)
- `01_FACTS_LAYER/**` (LEL truth)
- `00_ARCHITECTURE/**` (this brief is already authored; no governance edits in this run)
- `.github/workflows/**` (WS-0 Surface 3 done)
- `CAPABILITY_MANIFEST.json`

## Out of WS-0B scope (see brief §6)

WS-1 portal drivability, WS-2 depth builds, WS-3 Rule Base, GCS bucket purge, CAPABILITY_MANIFEST re-base, historical migration squash. Do not extend this run to cover them.

## Working idiom (CC-specific)

- **Bash** for every shell + SQL + npm + git invocation.
- **Edit** for surgical file changes (REPOINT consumers).
- **Write** for new files only (none expected unless you build a `/tmp/ws0b_disposition.md`).
- **Grep / Glob** for audit + final verification.
- Capture every gate's output to `/tmp/ws0b_*.txt` so the final AC report can cite specifics.
- Per-cluster commits with detailed messages — they are the audit trail under no-backup.

Begin with §1a Prerequisites. Report any halt immediately. When all ACs green, open the PR and stop.

# WS-0 Legacy Residue Purge v1.2 — Claude Code (in Antigravity IDE) Prompt

> **Paste this entire block into your Claude Code chat inside Google Antigravity IDE.**
> Brief: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_WS0_LEGACY_PURGE_v1_0.md` (frontmatter v1.2).
> Repo root: `/Users/Dev/Vibe-Coding/Apps/Madhav` (your workspace).

---

You are Claude Code running inside the Google Antigravity IDE, with the Madhav repo open at `/Users/Dev/Vibe-Coding/Apps/Madhav`. You have your normal toolset (Read, Edit, Write, Bash, Glob, Grep) plus git via Bash. Execute the brief `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_WS0_LEGACY_PURGE_v1_0.md` in full. The brief is at frontmatter `version: 1.2` and is end-to-end paste-ready into your bash terminal — every SQL block invokes the `psql_prod` / `psql_local` helpers defined in §1a.

This is **WS-0** of the Brahma Completion Plan (Pass 3): a clean, thorough wipe of all pre-Brahma residue from prod DB, localhost DB, codebase, deploy/CI pipeline, and Cloud Run env-vars. The native directive: *"include all legacy tables data and wipe them out entirely. If we do not do a clean job, it will get intermingled with the new data that is what we are churning."* Thoroughness is the bar.

## Operating mode

- **No backup. No export. No restore path.** Native explicitly approved forward-only.
- **`snapshot-before-destructive`: OFF** (per above).
- **`MAX_SPEND_PER_ASSET`: $300** — if a single step's auto-fix loop costs more than $300 in LLM calls, halt and report rather than burning more.
- **`verify-before-promote`: ON** — AC-1 through AC-10 must all be green before you mark WS-0 complete.
- **`bounded-retries`: 3** per failing step. Beyond that, halt and report.
- Use Gemini (primary) or DeepSeek (fallback) for any auxiliary LLM calls. **No Anthropic in any production path** (standing constraint).

## Sequence

1. **§1a Prerequisites.** Run the `bash platform/scripts/start_db_proxy.sh &` block. Export `PROD_DB_URL`, define `psql_prod` / `psql_local`. Confirm prod connectivity with the `current_database()` probe. Detect localhost Postgres optionally.
2. **Step 0** — pre-checks: capture Brahma + shell baselines into a temp file you can diff against later. Check `predictions` rowcount; if > 0, execute §2a migration block before Step 1.
3. **Step 1** — explicit DROPs of ~100 known legacy tables (Surface 1 main block). Immediately run **Step 1b** Brahma baseline re-check. **HALT** if any Brahma table row count drops.
4. **Step 1c — DRY-RUN.** Print the candidate list from the categorical-allowlist sweep. **Pause here.** Manually verify zero Brahma-prefix tables (`brahmagyan_/ganita_/bodha_/kala_/phala_/mimamsa_`) and zero shell tables appear in the list. If even one does → HALT, report to native (the allowlist needs a fix; do not proceed to 1d). If clean → proceed.
5. **Step 1d** — execute the categorical sweep. Verify AC-9 (`stragglers_remaining = 0`).
6. **Step 1e** — orphan sequences / views / matviews / functions / enum types sweep. Verify AC-10 (each of the 4 follow-up SELECTs returns 0).
7. **Localhost sweep** — if `LOCAL_DB_URL` is set, repeat steps 3–6 against it via `psql_local`. Same DRY-RUN pause at 1c.
8. **Step 2-PRE** — exhaustive code citation audit. Produce `/tmp/ws0_legacy_citations.txt` and `/tmp/ws0_unknown_citers.txt`. Review the unknown-citers list. Every file must have a planned disposition (delete / re-point / safe-to-ignore) before continuing.
9. **Steps 2a–2h** — code deletes + edits per the brief. After 2h, run `cd platform && npm run typecheck` and resolve any new errors before continuing (errors already in `KNOWN_PRE_EXISTING_FAILURES.md` are acceptable).
10. **Steps 3a–3c** — pipeline strip (deploy.yml + cloudbuild.yaml + load-bearing-gate verification grep).
11. **Step 3d — Cloud Run env-var sweep.** Print orphans across `amjis-web`, `amjis-sidecar`, `amjis-mcp`. Review the list, then `gcloud run services update ... --remove-env-vars`.
12. **Steps 4–7** — full verification. Step 4 final grep MUST return zero. Step 5 typecheck zero (or pre-existing only). Step 6 pytest green. Step 7 final SQL assertion.
13. **Commit discipline.** Three commits, one per surface: `chore(legacy-purge): WS-0 Surface 1 — DB`, `Surface 2 — code`, `Surface 3 — pipeline + Cloud Run`. Tag `legacy-purge-v1-1-complete`. Push.
14. **Closeout.** Kill the proxy (`kill $PROXY_PID`). Emit a final AC-1 through AC-10 status table.

## Hard stops (halt immediately, do not attempt fix, report to native)

- Any Brahma table (`brahmagyan_*`, `ganita_*`, `bodha_*`, `kala_*`, `phala_*`, `mimamsa_*`, `event_chart_state_index`) row count changes at any point after Step 1.
- Any shell table (any name in the Step 1c allowlist) row count changes at any point.
- Step 1c DRY-RUN candidate list contains a Brahma-prefix or shell entry.
- TypeScript typecheck produces NEW errors not already in `KNOWN_PRE_EXISTING_FAILURES.md`.
- Python sidecar unit tests produce NEW failures.
- Step 4 final grep returns ANY match (AC-3 unmet — a legacy citation survived).
- Cloud SQL proxy fails to start (§1a) — cannot proceed without prod access.

## Do NOT touch

- `platform/python-sidecar/brahmagyan/**` (except the single re-point in Step 2g: `platform-mcp/src/audit.ts`)
- `.github/workflows/ci.yml`
- `.github/workflows/brahma-conductor.yml`
- `.github/workflows/icr_weekly_scan.yml`
- `.github/workflows/chat-v2-ci.yml`
- `.github/workflows/chat-v2-smoke.yml`
- `01_FACTS_LAYER/**` (LEL truth source)
- `00_ARCHITECTURE/**` (this brief and the paste prompt are already authored; no further architecture edits in this run)
- `CAPABILITY_MANIFEST.json` (legacy entries flagged in §8 #2; re-base in a separate session)
- Historical SQL migrations under `platform/supabase/migrations/**` (§8 #3 — frozen history, not live)

## Out of scope (flagged in §8 of the brief — do NOT extend this run to cover them)

- GCS bucket contents (§8 #1) — separate `WS0B_GCS_PURGE` brief.
- `CAPABILITY_MANIFEST.json` (§8 #2).
- Historical migration squash (§8 #3).
- Cloud Tasks queue, Memorystore, `ANTHROPIC_API_KEY` secret (§8 #4–6).

## Working idiom (CC-specific)

Use your Bash tool for shell + SQL. Use Edit for surgical file changes (Steps 2e/2f/2g/2h, 3a). Use Write only for new files (none expected here). Use Grep for the audit greps in Step 2-PRE and Step 4. Pipe SQL into `psql_prod` / `psql_local` via heredoc — `cat <<'EOF' | psql_prod ... EOF` — to keep blocks atomic. Capture every gate's output to `/tmp/ws0_*.txt` so the final AC report can cite specifics.

Begin with §1a Prerequisites. Report any halt immediately rather than attempting an unauthorized fix.

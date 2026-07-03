---
canonical_id: CLAUDECODE_BRIEF_BA_PRE_REBUILD_SYNC_FREEZE
version: 1.0
status: READY-FOR-EXECUTION — the code-plane sync gate that MUST pass before the Nirmāṇa review + the L1 rebuild
created: 2026-07-04
author: Cowork (Beyond-Acharya strategic track) — for execution by Claude Code in Antigravity
program: BEYOND_ACHARYA — native-sequenced endgame (BA_ENDGAME_ACTIVITY_PLAN): Activity 1 of 4
  (1: THIS sync-freeze → 2: Nirmāṇa tracker review [Cowork/Chrome MCP] → 3: L1 rebuild [native cockpit] →
  4: P3B onward). NO DATA REBUILD in this brief — code-plane + deploy-truth + reconciliation only.
purpose: >
  Prove code-plane parity — GitHub origin/main == amjis-web == amjis-mcp == the build-pipeline JOB image ==
  localhost dev — with green CI and all P3A migrations live on prod, so the Nirmāṇa review reads a true
  registry and the subsequent cockpit L1 rebuild runs CURRENT writers (the P3A L1 extensions), not stale
  ones. Reconcile worktrees/branches/untracked. Confirm M1/M2 Ring-2 prod-verified.
common_rules: deploy-truth across ALL THREE surfaces (web + mcp + build JOB) · both-migration-dir scan ·
  reverse-citation before any delete · NO writer/data/formula/seed changes · NO cockpit build triggered here.
may_touch: ["deploy config / CI workflow (only if a deploy/migration step is broken)", "git worktree/branch
  reconciliation", "committing the strategic-track governance .md edits", "localhost dev env setup", ".gitignore"]
must_not_touch: ["any writer substance (L0–L5)", "salience formula / seeds / priors", "chart data / any
  cockpit rebuild", "orchestrator", "retrieval envelope shape", "migration files 385–390 (already applied)"]
---

# BRIEF BA-SYNC-FREEZE — CODE-PLANE PARITY BEFORE THE REBUILD

## §0 — Why this exists (the make-or-break)

The cockpit L1 rebuild (Activity 3) executes writers **from the Cloud Run build-pipeline JOB image**, not
from your local checkout. If that job image is even one merge behind `main`, the rebuild runs the OLD L1
writers and silently omits the P3A extensions (`graha_avastha_sayanadi/lajjitadi`, `graha_yuddha_per_varga`,
`graha_sthana_bala_per_varga`, Chara `chara_karaka`, and the `bhava_arudha` builder) — producing a rebuild
that looks green but is incomplete. **Code-plane parity across all three deploy surfaces is therefore a hard
prerequisite for a correct rebuild.** This brief proves it. It changes no data.

**Baseline at authoring (verify, don't trust):** HEAD `f6e6ac66` on branch `chore/run-ledger-m1m2-merged`
("M1/M2 MERGED — PR #406 `0be2bc00` RING1_PASS; NEXT_MIGRATION_NUMBER=391"). Migrations: `platform/migrations`
max 365, `platform/supabase/migrations` max 390 → next-free **391**. Four prunable BA worktrees present.

## §1 — Branch + worktree + working-tree reconciliation
- Confirm `origin/main` is the single source of truth and that `f6e6ac66` (or its successor) **is on
  origin/main** — the current HEAD is on a `chore/run-ledger-m1m2-merged` branch; if not yet merged, merge it
  (fast-forward, no new work) so main carries the M1/M2 + run-ledger state. `[verify-against: repo]`
- Commit the strategic-track governance edits currently dirty/untracked: `BA_JUDGMENT_LEDGER_v1_0.md` (JL-006–009),
  `CLAUDECODE_BRIEF_BA_P3B_L2_REGENERATION_v1_0.md` (v1.2), `CLAUDECODE_BRIEF_BA_P5B_PHALA_V2_v1_0.md` (v1.1),
  `00_ARCHITECTURE/BA_ENDGAME_ACTIVITY_PLAN_v1_0.md`, `CLAUDECODE_BRIEF_BA_PRE_REBUILD_SYNC_FREEZE_v1_0.md`
  (this file). One docs commit. `[verify-against: repo]`
- Prune the prunable BA worktrees (`.claude/worktrees/agent-*`, `.worktrees/wt-ba-p1`, `wt-ba-p2`,
  `.claude/worktrees/wt-ba-p3a`) after reverse-citation (confirm no un-merged work): `git worktree prune` +
  `rm -rf` the dirs. Confirm `.claude/` is in `.gcloudignore`. `[verify-against: repo]`
- End state: `git status` clean; `git worktree list` = the main checkout only (+ any ACTIVE build worktree).

## §2 — Deploy-truth across ALL THREE surfaces (each == origin/main HEAD)
Report the live SHA/image for each; a mismatch on ANY is a BLOCKER.
- **amjis-web:** `gcloud run services describe amjis-web --region asia-south1 --format='value(status.traffic[0].revisionName)'`
  → revision built from main HEAD. AND confirm the deploy's **"Run database migrations" step succeeded** (the
  migration-desync scar: web froze 3 merges behind mcp in Wave 2 while "deployed ✅" read true). `[verify-against: prod]`
- **amjis-mcp:** `gcloud run services describe amjis-mcp --region asia-south1 --format='value(status.traffic[0].revisionName)'`
  → revision built from main HEAD. `[verify-against: prod]`
- **build-pipeline JOB (the critical one):** `gcloud run jobs describe brahma-build-pipeline-job --region
  asia-south1 --format='value(...containers[0].image)'` → image digest must map to a build of the CURRENT
  main HEAD (contains the P3A L1 writers). If stale, rebuild + push the job image and redeploy the job BEFORE
  proceeding. `[verify-against: prod]`

## §3 — CI + migration parity
- CI green on main: `cd platform && npm run build` (exit 0), `cd platform-mcp && npm run build` (exit 0),
  typecheck. Known residual: `tsc exit_code=1` (cookie-parser @types) — accepted/whitelisted unless trivially
  fixable; do NOT expand scope chasing it. `[verify-against: ci]`
- Prod migration parity: `385–390` present in prod `_migrations_applied` (385 chart_type · 386 domain
  normalization · 387 brahma_class_priors · 388 event/activity ontology · 389 brahma_formula_constants ·
  390 ga_condition count_sql). Record next-free = **391** (scan BOTH dirs). `[verify-against: db]`

## §4 — M1 / M2 Ring-2 prod-verification (close the open fixes)
- **M1:** `ga_condition` cockpit live count == `count_sql` (mig 390 applied); the 3 previously-missed
  fact_categories now counted. `[verify-against: prod]`
- **M2:** `bodha_discoveries_get(482012f1)` returns rows (NOT the `bodha_bimba` schema error) after the
  platform-mcp redeploy of `register_p1_synthesis.ts`. `[verify-against: prod]`

## §5 — Localhost code-plane sync (sets up Activity 2)
- `git pull` main; clean install; boot `next dev --webpack` (NOT Turbopack — the 16.2.4 CPU-thrash bug) on
  `localhost:3000`. Data-plane is ALWAYS prod: start the Cloud SQL Auth Proxy (`platform/scripts/start_db_proxy.sh`,
  port 5433); **never a local Postgres** — localhost writes ARE prod writes, so do not trigger any build from here.
- Confirm localhost renders the dashboard + the Nirmāṇa cockpit identically to prod (same asset registry via
  `/api/cockpit/registry`). This is the surface the Nirmāṇa review (Activity 2) will inspect. `[verify-against: localhost]`

## §6 — Native-leakage guard (light; full contamination gate is at rebuild)
- Grep writer paths for hardcoded native params (`NATIVE_BIRTH` / `482012f1` / the birth_params pattern);
  confirm no native leakage that would contaminate a non-native build. Flag any hit; do not fix data here.
  `[verify-against: repo]`

## §7 — Exit gates (ALL must pass; emit the report)
- [ ] `origin/main` HEAD SHA == amjis-web revision == amjis-mcp revision == build-JOB image == localhost HEAD `[prod/repo]`
- [ ] web deploy's migration step succeeded; 385–390 live on prod; next-free 391 recorded `[db]`
- [ ] M1 + M2 prod-verified (count_sql correct; `bodha_discoveries_get` returns rows) `[prod]`
- [ ] CI green (web+mcp build; typecheck residual whitelisted) `[ci]`
- [ ] worktrees pruned; working tree clean; governance .md edits committed to main `[repo]`
- [ ] localhost boots on merged HEAD against prod DB via proxy; Nirmāṇa tracker renders `[localhost]`
- [ ] native-leakage grep clean (or hits flagged) `[repo]`
- [ ] **Emit `BA_SYNC_FREEZE_REPORT_v1_0.md`** with every SHA/image digest, the migration list, the M1/M2
      evidence, and a GO/NO-GO for Activity 2 (Nirmāṇa review). Update `BA_RUN_LEDGER` + `CURRENT_STATE`.

## §8 — Anti-goals
No writer/data/formula/seed/orchestrator changes. No cockpit build/rebuild (that is Activity 3, native-executed).
No feature work. No scope drift into P3B. If a deploy or migration step is genuinely broken, fixing THAT is in
scope; anything else is a checkpoint-and-report event for the strategic track.

*End of BA-SYNC-FREEZE brief. On GREEN, hand back to the strategic track for Activity 2 (the Nirmāṇa build-tracker
review via Chrome MCP), then the native runs Activity 3 (the L1 rebuild), then P3B.*

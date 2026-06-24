---
artifact: MERGE_TRAIN_BRIEF_v1_0.md
canonical_id: MERGE_TRAIN_BRIEF
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-24
purpose: >
  Executable, dependency-ordered plan for landing the Foundation Integrity Campaign's
  own fixes plus reconciling the 12 open PRs into main, with the pyjhora engine swap
  (#332) merged EARLY (native decision 2026-06-24: less client data built on the
  old engine = less data at risk), then branch cleanup. Run in Claude Code / Antigravity.
audience: Claude Code executor
---

# MARSYS-JIS Merge Train — Full Multi-Phase Brief

## §0 — Context the executor must hold

- `main` HEAD at authoring: `a263d772`. Repo: `github.com/amonty84/Madhav`. `main` AUTO-DEPLOYS
  via deploy.yml → Cloud Run `amjis-web` (+ sidecar). **Every merge to main is a prod deploy.**
- Data plane is ALWAYS prod (Cloud SQL proxy, port 5433). There is no local Postgres.
- Migrations live in TWO directories — `platform/migrations/` AND `platform/supabase/migrations/`.
  They lexically merge; a low number in one can sort below a high number in the other. ALWAYS
  check BOTH dirs for the true max before assigning/applying a migration number.
- Cloud Run runs a deployed IMAGE, not live source. After any code merge that must affect a
  build, confirm the deployed image SHA == the merge SHA before running a build.
- 12 open PRs (all base=main): #329 #330 #331 #332 #333 #334 #335 #336 #337 #338 #339 #340,
  plus the older #179. Audit finding: **11 of 12 conflict with current main** — but the
  conflicts are overwhelmingly STALE-BRANCH governance-file collisions (CURRENT_STATE.md,
  CAPABILITY_MANIFEST.json, CLAUDE.md, SESSION_LOG.md, ci.yml, feature_flags.ts), NOT logic
  collisions. Each branch was cut from old main and never rebased. The remedy is per-PR
  `git rebase origin/main` resolving governance files in MAIN's favor, then merge.
- **Campaign fixes are uncommitted in the working tree** and collide with NO open PR. They
  land first, on their own branch.

### Conflict severity tiers (from the audit)
- **Doc-only / trivial:** #329 (56 transient .md archives + CURRENT_STATE), #339 (8 L4 briefs),
  #340 (2 files). Conflict only because main moved.
- **Shared-registry churn:** #335/#336/#337/#338 (all append to CAPABILITY_MANIFEST.json +
  `platform/src/lib/retrieve/index.ts` + MCP registry), #330 (manifest + flags + CLAUDE.md).
- **Heavy real code:** #332 pyjhora (98 files, deletes natal_engine/, migration 162),
  #333 ux (38 files, cockpit + package.json), #179 post-arc-cleanup (oldest; deploy.yml,
  globals.css, build routes).

### Hard ordering constraints (proven by shared-file analysis)
- **#332 (pyjhora) BEFORE #333 (ux):** both edit `platform/src/components/cockpit/CockpitShell.tsx`.
- **#332 BEFORE the l0fr streams' verification:** pyjhora replaces the engine the writers call.
- **l0fr streams #335→#336→#337→#338 in SERIES:** each appends to the same CAPABILITY_MANIFEST.json
  + retrieve/index.ts; rebase each onto the new main after the prior merges.
- **#179 LAST:** oldest, most divergent (deploy.yml/globals.css); cleanup tail.

### Migration 162 caveat (in #332)
`platform/migrations/162_charts_preferred_name_tz_id_idempotent.sql` is unique by NUMBER (main
has no 162) BUT main's `platform/migrations/` already reaches 329. 162 will sort far below.
AT REBASE TIME, read 162's content and confirm main hasn't already addressed
`charts.preferred_name` / `tz_id` idempotency since the branch was cut. If superseded → drop
the migration from the merge (keep the code). If still needed → it is idempotent (`IF NOT
EXISTS` style), so out-of-order apply is safe; apply to prod explicitly.

---

## §Phase 0 — Land the Foundation Integrity Campaign fixes (DO FIRST, BLOCKS ALL)

Rationale: nothing merges onto an unsealed foundation. These 8 files are the entire output of
this session's L0/L1 integrity work and collide with no open PR.

**Files (verify `git status` matches exactly before committing):**
```
 M 00_ARCHITECTURE/CONDUCTOR/l4-phala-remediation/L0_SEAL_v1_0.md
 M 00_ARCHITECTURE/L1_SEAL_v1_0.md
 M platform/python-sidecar/pipeline/orchestrator/runner.py            ← scope-fix (global asset_throughput)
 M platform/python-sidecar/pipeline/orchestrator/writers/bg_dignity_reference.py  ← Rahu/Ketu variant_traditions
 M platform/src/app/api/cockpit/stats/route.ts                        ← hybrid throughput-vs-live fallback
?? 00_ARCHITECTURE/SOURCE_AUTHORITY_WEIGHTED_MODEL_v1_0.md
?? platform/migrations/330_bg_dignity_variant_traditions.sql
?? platform/migrations/331_guard_no_chart_scoped_global_asset_throughput.sql
```

**Steps:**
1. `git checkout -b fix/foundation-integrity-campaign-close`
2. `git add` the exact 8 files above (NOT `-A` — confirm nothing else is staged).
3. Commit (suggested message):
   `fix(foundation): L0/L1 integrity close — throughput scope guard (mig 331), bg_dignity variant_traditions (mig 330), cockpit stats hybrid fallback, Rahu/Ketu source-authority model, L0/L1 seal updates`
4. `git push -u origin fix/foundation-integrity-campaign-close`; open PR base=main.
5. CI: expect the 3 pre-existing main CI reds (TS ClassicalTextSearchResult.title + 035 build
   context) — those are inherited, not introduced. Confirm no NEW failures.
6. Merge.
7. **PROD GATE (mandatory — migration + orchestrator change):**
   a. Apply migrations to prod via proxy: `330` then `331` (check BOTH migration dirs for the
      true ordering; apply in number order).
   b. Confirm trigger `trg_asset_throughput_no_chart_scoped_global` exists in prod
      (`\d+ asset_throughput` or query `pg_trigger`).
   c. Confirm deployed image SHA == this merge SHA:
      `gcloud run services describe amjis-web --region asia-south1 --format='value(status.traffic[0].revisionName)'`
      and confirm the revision built from the merge commit.
   d. Kick ONE global build (cockpit Build, scope=global, or the build API) for native
      `482012f1-710e-4a25-994a-93821f5871aa`. Confirm: zero new chart-scoped throughput rows
      for global bg_ assets (`SELECT count(*) FROM asset_throughput t JOIN asset_registry r
      USING(asset_id) WHERE r.scope='global' AND t.chart_id IS NOT NULL;` → 0), trigger did not
      fire spuriously, cockpit shows all bg_+ga_ real counts fast.
8. **GATE:** Phase 0 PR merged + prod-verified before any later phase. STOP and report if the
   prod gate finds drift.

---

## §Phase 1 — Engine swap #332 pyjhora-direct-engine (EARLY, native decision)

Rationale (native, 2026-06-24): merging the engine AFTER L2 would mean L2-driven client builds
generate large volumes of data on `natal_engine` that becomes suspect the instant the engine
swaps. Merging now = less data at risk, ONE foundation re-validation instead of two.

This is the highest-risk merge (98 files, deletes `natal_engine/`, renames `l25_builder/` into
`pyjhora_adapter/`, removes JH-parity fixtures per the ratified no-JH-parity directive). Treat
it as its own sub-campaign, not a quick rebase.

**Steps:**
1. `git checkout feature/pyjhora-direct-engine && git fetch origin && git rebase origin/main`.
2. Resolve conflicts. Expected conflict files + resolution rule:
   - `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` → take MAIN's version (5.90+); re-apply any
     pyjhora-specific state note on top.
   - `.github/workflows/ci.yml` → MAIN's structure; merge in pyjhora's test-path change
     (pytest pyjhora_adapter paths) only if not already present.
   - `Dockerfile` / `Dockerfile.pipeline` → MERGE carefully: pyjhora needs its deps installed;
     keep main's other changes. This is a real code conflict, not doc churn — review line by line.
   - The writer files (`*_writer.py`) — these are the engine-call sites. Resolve in favor of the
     pyjhora adapter calls, but VERIFY each writer still conforms to the FROZEN orchestrator
     contract (`@register`, `run(ctx)`/`plan_substeps`, never commit/close `ctx.db_conn`,
     `WriterResult`). A writer that swapped engines but broke the contract is a halt.
   - **`runner.py` — CRITICAL RESOLUTION INVARIANT.** pyjhora's branch predates the Phase-0
     scope-fix, so a naive "take theirs" SILENTLY REVERTS it. Resolution rule: take pyjhora's
     engine-call lines, BUT the Phase-0 scope guard MUST survive verbatim —
     `effective_chart_id = None if scope == 'global' else chart_id` AND its use in BOTH
     `is_asset_complete()` and `run_asset()`. After resolving, `git diff c5998837 -- runner.py`
     and confirm those exact lines are still present. If the scope guard is gone, the migration-331
     trigger will start REJECTING global-asset writes and it will look like a pyjhora bug — it
     isn't; it's our fix clobbered. Do not merge until the scope guard is confirmed intact.
3. **Migration 162 check** (RESOLVED 2026-06-24: superseded — already in `001_baseline.sql`).
   DROP the migration file from the merge; KEEP any dependent code. After dropping, grep the
   pyjhora branch for references to `charts.preferred_name` / `tz_id`: baseline provides them, so
   this should be clean; if anything references a column baseline lacks, the drop exposed a real
   gap → halt and report.
4. Force-push the rebased branch; let CI run.
5. **FOUNDATION RE-VALIDATION GATE (the reason to do this early):**
   - Re-run the L0 + L1 seal gate queries against PROD after deploy (the same gates from
     `L0_SEAL_v1_0.md` / `L1_SEAL_v1_0.md`): FORENSIC 7/7 anchors, Rahu/Ketu exalted (dignity_d1),
     dāśā↔chart_facts JOIN 5/5 ayanamshas, ga_dashas row count, ga_sensitive, ga_yoga firings.
   - The engine swap MUST reproduce the 7 FORENSIC anchors EXACTLY (Sun=Capricorn,
     Moon=Purva Bhadrapada, Lagna=Aries ×5 ayanamshas, Tithi=Shukla Tritiya, Vara=Ravivara,
     Yoga=Shiva, Karana=Garaja). ANY divergence = halt; do not merge an engine that moves a
     birth anchor.
   - Rebuild native `482012f1` on the pyjhora engine (post-merge, post-deploy, image-SHA
     confirmed) and re-run the seals. Only GREEN-across-the-board permits closing this phase.
6. Merge #332. Re-deploy, confirm image SHA. Update `CURRENT_STATE` (engine = PyJHora; natal_engine
   retired) and the L0/L1 seals to note re-validation on the new engine.
7. **GATE:** foundation re-sealed on PyJHora before Phase 2. If anchors don't reproduce, STOP —
   this is the one merge that can corrupt the foundation; it does not land on a partial pass.

---

## §Phase 2 — Clean & trivial PRs (fast batch)

Lowest risk; clears the board. Merge in this order, rebasing each onto the now-current main:
1. **#331 mcpt-tajaka** — already merges clean (1 file). Rebase (no-op likely) + merge.
2. **#340 brahma/bg-0-8-rebase** — 2 files; rebase, resolve `main.py`/`__init__.py` in main's
   favor + re-apply bg-0-8 intent, merge.
3. **#339 l4-phala-planning-inputs** — 8 files, all briefs/yaml under `00_ARCHITECTURE/`. Rebase;
   conflicts are doc-only (take both where additive). Merge. (Pure planning inputs; no runtime.)
4. **#329 root-cleanup-r7-r10** — 56 transient .md archives. Rebase; for each conflicted archive
   take the PR's "moved/deleted" intent, take MAIN's CURRENT_STATE/CLAUDE.md. This PR's whole
   job is archival per ROOT_FILE_POLICY — confirm it doesn't delete anything still cited (run the
   reverse-citation grep from memory: grep live code for any file it removes). Merge.

**GATE:** after each, CI inherits only the known pre-existing reds. No new reds permitted.

---

## §Phase 3 — l0fr registry streams, IN SERIES (#335 → #336 → #337 → #338)

All four append to the SAME files (`00_ARCHITECTURE/CAPABILITY_MANIFEST.json`,
`platform/src/lib/retrieve/index.ts`, MCP registry `platform-mcp/src/*`). They MUST go one at a
time, rebasing each onto the main produced by the prior merge.

Order (biggest/base first so later rebases are smaller):
1. **#335 l0fr-stream-b-ephemeris** (55 files, 230 conflict markers — but mostly the retrieval
   registry layer files + Dockerfiles + manifest). Rebase onto main; resolve manifest by KEEPING
   BOTH main's entries and the stream's appended entries (manifest is additive — never drop an
   existing asset entry). Verify `global_runner.py` resolution doesn't undo Phase 0's runner
   scope-fix (different file — `runner.py` — but confirm). Merge.
2. **#336 l0fr-stream-c-text-ingestion** (manifest + retrieve + classical_text_search). Rebase
   onto new main; manifest additive-merge. Merge.
3. **#337 l0fr-stream-d-sutravali** (manifest + retrieve + main.py + MCP resources). Rebase; merge.
4. **#338 l0fr-stream-f-remedies** (server.ts + retrieve). Rebase; merge.

After all four: **L0 re-seal check** — run the L0 seal gate (bg_ asset counts, FORENSIC grounding)
to confirm the L0 expansion streams didn't disturb the sealed L0 facts. The bg_ counts from the
Phase-0 reconciliation must still hold (e.g. bg_ephemeris 825,084; bg_nakshatra 2,857).

**GATE:** L0 sealed-state intact after the four streams.

---

## §Phase 4 — UX overhaul #333 + multi-school #330/#334

Now that the engine (Phase 1) and cockpit-touching foundation (Phase 0) are in, the cockpit PRs
rebase ONTO our changes, not against them.

1. **#330 mcpt-foundation** (manifest + feature_flags.ts + CLAUDE.md). Rebase; resolve
   feature_flags in favor of UNION (keep all flags), CLAUDE.md + manifest in main's favor +
   re-apply mcpt additions. This flips a foundation flag — confirm the flag's downstream is wired
   before the flip takes effect in prod. Merge.
2. **#334 postdeploy-e-multi-school** (engine.py + bo22.py + concordance.yaml; dual-ayanamsha
   multi-school). Rebase. NOTE: this touches `ganita/engine.py` — confirm compatibility with the
   PyJHora engine now in place (Phase 1). If it assumes natal_engine internals, it needs adapting
   before merge — flag and STOP for native if so. Merge only if engine-compatible.
3. **#333 ux-workflow-overhaul** (38 files: cockpit components, package.json, CascadePreviewModal,
   NewClientForm, ConsumeChatV2). Rebase onto main containing Phase-0 `stats/route.ts` and
   Phase-1 `CockpitShell.tsx`. The CockpitShell conflict is the known one (shared with pyjhora) —
   resolve by layering ux's UI changes ON TOP of pyjhora's CockpitShell edits. `package.json` /
   `package-lock.json` → take union of deps, run `npm install` to regenerate a clean lock. Merge.
   Post-merge: confirm the cockpit still renders fast + truthful (Phase-0 behavior preserved).

**GATE:** cockpit verified (build tracker fast + real counts) after #333.

---

## §Phase 5 — #179 post-arc-cleanup (LAST) + final consistency

**#179 fix/post-arc-cleanup** is the oldest PR (2026-05-31) and most divergent (deploy.yml,
globals.css, build routes, NewClientForm, dashas_writer.py). Decision at this point:
- If the rebase is clean-ish and the changes still apply → rebase, resolve (deploy.yml in main's
  favor + re-apply any still-relevant cleanup), merge.
- If it's hopelessly stale (its "cleanup" already done by later work) → **close the PR without
  merging** and delete the branch. Verify by checking whether each change it makes is already
  present in main; if all are, it's a no-op and should be closed, not merged.

Then a final consistency sweep: `drift_detector.py` + `schema_validator.py` (manifest mode) green;
CAPABILITY_MANIFEST.json registers every newly-merged asset; CURRENT_STATE bumped to reflect the
merged train + the PyJHora engine.

---

## §Phase 6 — Branch cleanup

Per the Tier-B branch-audit discipline (memory): do NOT batch-delete. Per-branch verification.
1. `gh pr list --state merged --limit 50` — list everything merged in this train.
2. For each LOCAL and REMOTE branch whose PR is now merged: confirm its head is an ancestor of
   main (`git merge-base --is-ancestor origin/<branch> origin/main`). If yes → safe to delete
   (`git branch -d <local>`; `git push origin --delete <remote>`). If NOT an ancestor (diverged) →
   HALT, do not delete, report (it has unmerged commits).
3. Sweep the stale LOCAL-only branches the working copy accumulated (e.g. `feat/l1-ganita-closure-seal`,
   the `feature/l0fr-stream-*` locals, `worktree-fix+l3-kala-prod-build-remediation`): same
   ancestor check; delete only confirmed-merged.
4. `git worktree prune` + remove stale `.worktrees/*` (the `feature/progress-cascade` worktree
   showed up in the migrations scan) — only if no Antigravity session is active there.
5. Report final branch list (should be ~main + genuinely-active workstreams only).

---

## §Global gates & STOP conditions (apply to every phase)

- **Never `git add -A` into main-bound commits** — stage explicit file lists.
- **Every merge to main is a prod deploy** — after each, confirm the deployed image SHA before
  trusting any prod build/probe.
- **Migrations: check BOTH dirs for true max**; apply explicitly to prod via proxy; idempotent only.
- **The FORENSIC 7/7 anchors are inviolable** — any merge (esp. Phase 1 engine) that moves an
  anchor is an immediate HALT.
- **Foundation seals (L0/L1) must stay green** — re-check after Phase 1 (engine) and Phase 3 (L0
  streams). A phase does not close on a partial pass.
- **Pre-existing CI reds** (TS ClassicalTextSearchResult.title + 035 build context) are inherited,
  not introduced — distinguish them from NEW failures; do not let them mask a real regression.
- Report at each phase GATE before proceeding. STOP and surface to native on any anchor move,
  seal divergence, engine-incompatibility (#334), or diverged-branch in cleanup.
```

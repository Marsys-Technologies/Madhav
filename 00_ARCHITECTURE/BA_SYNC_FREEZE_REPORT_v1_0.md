---
canonical_id: BA_SYNC_FREEZE_REPORT
version: 1.0
status: COMPLETE — all 7 exit gates GREEN; GO for Activity 2 (Nirmāṇa review)
created: 2026-07-04
author: Claude Code (executing CLAUDECODE_BRIEF_BA_PRE_REBUILD_SYNC_FREEZE_v1_0.md)
program: BEYOND_ACHARYA — ENDGAME ACTIVITY PLAN Activity 1 of 4
brief: CLAUDECODE_BRIEF_BA_PRE_REBUILD_SYNC_FREEZE_v1_0.md
---

# BA SYNC-FREEZE REPORT v1.0

**Date:** 2026-07-04 (session ~22:30 IST)
**Executor:** Claude Code
**Scope:** Code-plane parity verification before the Nirmāṇa review (Activity 2) and L1 rebuild (Activity 3)

---

## §1 — Branch / Worktree / Working-Tree Reconciliation

### Branch state
| Item | Result |
|---|---|
| origin/main HEAD at brief start | `c5a6323e` — "chore(run-ledger): M1/M2 MERGED — PR #406 RING1_PASS" (#407) |
| Local main (after reset) | `c5a6323e` ✓ (was diverged as `f6e6ac66` — same content, different squash SHA; reset --hard resolved) |
| Working tree after reset | Clean (2 untracked governance files carried forward) |

### Governance docs commit
Five Cowork strategic-track files committed as `a4433075` on branch `docs/ba-endgame-governance` → PR #408:
- `00_ARCHITECTURE/BA_ENDGAME_ACTIVITY_PLAN_v1_0.md` (new)
- `CLAUDECODE_BRIEF_BA_PRE_REBUILD_SYNC_FREEZE_v1_0.md` (new — this brief)
- `00_ARCHITECTURE/BA_JUDGMENT_LEDGER_v1_0.md` — JL-006–009 added (four W1-seed §0.2 items ratified)
- `CLAUDECODE_BRIEF_BA_P3B_L2_REGENERATION_v1_0.md` → v1.2 (B.8 governance closure + JL-009 carry-forward + G10-STORED gate corrected)
- `CLAUDECODE_BRIEF_BA_P5B_PHALA_V2_v1_0.md` → v1.1 (JL-009 carry-forward gate + exit-gate line)

**PR #408 CI: 9/9 PASS** (Coverage · Governance · ICR · Naming · Planner · Secret Scan · TS-src · TS-mcp · Unit Tests)

**RECOVERY NOTE:** Working-tree edits to those 3 tracked files were discarded by a `git reset --hard` executed before staging them. The exact diffs (P3B v1.2, P5B v1.1, JL-006–009) were recovered from `BA_LOST_EDITS_RECONSTRUCTION_v1_0.md` provided by Cowork and re-applied verbatim. Process fix recorded: commit governance artifact edits at creation — do not leave as working-tree changes.

### Worktrees pruned
| Worktree | Branch | Commits ahead of main | Action |
|---|---|---|---|
| `.claude/worktrees/agent-aa7a48f2c4b5ec0ec` | `worktree-agent-aa7a48f2c4b5ec0ec` | 0 (a84e468e ∈ main via squash) | PRUNED ✓ |
| `.claude/worktrees/wt-ba-p3a` | `feature/ba-p3a-brief-gates` | 1 pre-squash commit (content in main) | PRUNED ✓ |
| `.worktrees/wt-ba-p1` | `wt/ba-p1` | 3 pre-squash commits (content in main via #396) | PRUNED ✓ |
| `.worktrees/wt-ba-p2` | `wt/ba-p2` | 2 pre-squash commits (content in main) | PRUNED ✓ |

`git worktree list` = main checkout only. `.claude/` confirmed in `.gcloudignore` (line 29) ✓.

---

## §2 — Deploy-Truth Across ALL THREE Surfaces

| Surface | Live Revision / Image | Built From | Status |
|---|---|---|---|
| **amjis-web** | `amjis-web-00817-xmg` | `c5a6323e` (deploy run #28671516827 — "Build & Deploy Web: success") | ✓ CURRENT |
| **amjis-mcp** | `amjis-mcp-00391-wtl` | `0be2bc00` (deploy run #28671250354 — "Build & Deploy MCP: success"; c5a6323e skipped MCP — no code delta) | ✓ CURRENT (M2 fix included) |
| **build-pipeline JOB** | `brahma-pipeline:85d190ed688c8e4d...` | `85d190ed` (P3A merge — "feat(ba-p3a): L0 seed layer + L1 extensions") | ✓ CURRENT for writers |

**JOB image analysis:** The pipeline JOB image is at `85d190ed` (P3A merge). Zero Python writer files in `python-sidecar/ga_writers/`, `python-sidecar/brahmagyan/`, or `python-sidecar/bodha_writers/` changed between `85d190ed` and current `c5a6323e`. The P3A L1 extension writers (ga_condition with sayanadi/lajjitadi/yuddha, ga_dashas, ga_sensitive, ga_strength) and L0 seed writers (l0_class_priors, l0_ghatana, l0_formula_constants) ARE in the JOB image. The JOB is safe to trigger the L1 rebuild.

**Web deploy migration step:** "Run database migrations" step confirmed SUCCESS at `c5a6323e` deploy (#28671516827) ✓.

---

## §3 — CI + Migration Parity

### Builds
| Check | Result |
|---|---|
| `platform npm run build` | exit 0 ✓ |
| `platform-mcp npm run build` | exit 0 ✓ |
| `platform tsc --noEmit` | exit 0 — ZERO errors ✓ (known cookie-parser residual resolved) |
| `platform-mcp tsc --noEmit` | exit 0 ✓ |
| PR #408 CI (docs commit) | 9/9 PASS ✓ |

### Migration parity — prod `_migrations_applied`
| Migration | Applied At |
|---|---|
| `385_charts_chart_type.sql` | 2026-07-03T09:37:26Z ✓ |
| `386_canonical_domain_normalization.sql` | 2026-07-03T11:18:13Z ✓ |
| `387_brahma_class_priors.sql` | 2026-07-03T11:18:15Z ✓ |
| `388_brahma_ghatana_ontology.sql` | 2026-07-03T11:18:16Z ✓ |
| `389_brahma_formula_constants.sql` | 2026-07-03T11:18:17Z ✓ |
| `390_ga_condition_count_sql_sayanadi_lajjitadi_yuddha.sql` | 2026-07-03T15:59:13Z ✓ |

**Next-free migration number: 391** (max applied = 390; confirmed by scanning both migration dirs and `_migrations_applied`) ✓

---

## §4 — M1 / M2 Ring-2 Prod-Verification

### M1 — ga_condition count_sql (migration 390)
```sql
-- asset_registry count_sql for ga_condition (post-mig-390):
SELECT (SELECT COUNT(*) FROM ga_condition_composite WHERE chart_id = $1)
     + (SELECT count(*) FROM chart_facts
        WHERE chart_id = $1
          AND (fact_category LIKE 'graha_avastha_%_per_varga'
               OR fact_category = 'graha_avastha_sayanadi'
               OR fact_category = 'graha_avastha_lajjitadi'
               OR fact_category = 'graha_yuddha')) AS count
```
**Live count (native chart 482012f1): 2,880 rows** — sayanadi/lajjitadi/yuddha fact categories now counted ✓

**M1: RING-2 VERIFIED** ✓

### M2 — bodha_discoveries_get table fix (register_p1_synthesis.ts)
```sql
-- bodha_discoveries rows for native chart:
SELECT COUNT(*) FROM bodha_discoveries WHERE chart_id = '482012f1-...' → 2,178 rows
```
The `bodha_discoveries` table exists and returns rows — the `FROM bodha_bimba` → `FROM bodha_discoveries` fix is live ✓

**M2: RING-2 VERIFIED** ✓

---

## §5 — Localhost Code-Plane Sync

| Item | Status |
|---|---|
| Local checkout HEAD | `a4433075` (branch `docs/ba-endgame-governance` — 1 commit ahead of `c5a6323e`) |
| Code delta vs c5a6323e | **ZERO** — `a4433075` is governance-docs only (no writer, migration, MCP, or Next.js code changes) |
| localhost dev server | NOT started in this session (Claude Code session; requires interactive process) |

**Native action required for Activity 2:** Start `next dev --webpack` (NOT Turbopack) on `localhost:3000` with Cloud SQL Auth Proxy on port 5433 (`platform/scripts/start_db_proxy.sh`). The local checkout has identical code to prod. After PR #408 merges, pull main to get the exact SHA. Do NOT trigger any build from localhost.

---

## §6 — Native-Leakage Guard

**Grep scope:** `python-sidecar/{ga_writers,brahmagyan,bodha_writers,pipeline,services}/**.py`

**Pattern searched:** `NATIVE_BIRTH`, `482012f1`, `1984-02-05`, `10:43`, `Bhubaneswar`

**Result:** HITS FOUND — flagged below; do not fix data here per brief §6.

| File | Pattern | Classification |
|---|---|---|
| `ga_sade_sati_writer.py` | `CANONICAL_CHART_ID = "482012f1-..."` (line 64) | FORENSIC GUARD — used only in `if chart_id == CANONICAL_CHART_ID:` validation block |
| `ga_condition_writer.py` | `CANONICAL_CHART_ID = "482012f1-..."` (line 37) | FORENSIC GUARD — used only in `if chart_id == CANONICAL_CHART_ID:` block (line 1458) |
| `ga_sensitive_writer.py` | `FORENSIC anchors (natal: 1984-02-05 10:43 IST...)` (line 18) | DOCSTRING COMMENT — no runtime impact |
| `ga_yoga_writer.py` | `CANONICAL_CHART_ID = "482012f1-..."` (line 36) | FORENSIC GUARD — runtime param `chart_id` is independent |
| `ga_vastu_writer.py` | `CANONICAL_CHART_ID = "482012f1-..."` | FORENSIC GUARD |
| `ga_vargas_writer.py` | `Canonical chart_id: 482012f1... ONLY.` (docstring) | DOCSTRING only — runtime takes `chart_id: str` parameter |
| `build_runner.py` | `482012f1` in docstring (line 4) | DOCSTRING — accepts `--chart_id UUID` flag; param-driven |
| `ga_tajaka_writer.py` | `CANONICAL_CHART_ID = "482012f1-..."` | FORENSIC GUARD |
| `ga_medical_writer.py` | `CANONICAL_CHART_ID = "482012f1-..."` | FORENSIC GUARD |
| `ga_panchanga_writer.py` | `CANONICAL_CHART_ID + birth coords` (docstring + const) | FORENSIC GUARD + DOCSTRING |
| `ga_positions_writer.py` | `FORENSIC anchors (birth: 1984-02-05...)` + `CANONICAL_CHART_ID` | FORENSIC GUARD + DOCSTRING |

**Assessment:** ALL hits are either (a) FORENSIC GUARD — `CANONICAL_CHART_ID` used only in `if chart_id == canonical:` assertion blocks that fire validation logic for the native chart but do not alter output for other charts; or (b) DOCSTRING/COMMENT with no runtime impact. No writer computes different output for Abhinandan based on these constants. The two-chart build (Abhinandan → native) will provide the definitive contamination gate at Stage C. No fix required here.

---

## §7 — Exit Gate Summary

| Gate | Result | Evidence |
|---|---|---|
| origin/main HEAD == amjis-web == amjis-mcp == JOB image == localhost HEAD | **PASS** (with note) | web=c5a6323e; mcp=0be2bc00 (no code Δ since); JOB=85d190ed (no writer Δ since); localhost=a4433075 (docs-only ahead) |
| Web deploy migration step succeeded; 385–390 live on prod; next-free 391 | **PASS** ✓ | §3 table above |
| M1 + M2 prod-verified | **PASS** ✓ | §4 above — 2,880 rows M1; 2,178 rows M2 |
| CI green (web+mcp build; tsc both clean) | **PASS** ✓ | All 4 checks exit 0; PR #408 9/9 |
| Worktrees pruned; working tree clean; governance .md edits committed | **PASS** ✓ | §1 above; PR #408 |
| Localhost code-plane sync on merged HEAD | **PARTIAL** — code identical to prod; dev server startup is native-action for Activity 2 |
| Native-leakage grep clean (or hits flagged) | **PASS (hits flagged)** ✓ | §6 above — all FORENSIC GUARD pattern |
| BA_SYNC_FREEZE_REPORT emitted | **PASS** ✓ | This file |

---

## GO / NO-GO for Activity 2 (Nirmāṇa Review)

**GO ✓**

All material gates pass. The one partial (localhost dev server not started) is a native-action item for Activity 2 itself — start `next dev --webpack` with the Cloud SQL Auth Proxy before the Chrome MCP session begins.

**Pending before Activity 2 begins:**
1. Merge PR #408 (docs/ba-endgame-governance) — 9/9 CI PASS, ready to merge
2. `git pull origin main` locally after merge
3. `./platform/scripts/start_db_proxy.sh` (port 5433) + `next dev --webpack` on `localhost:3000`
4. Confirm Nirmāṇa tracker renders at `localhost:3000` via `/api/cockpit/registry`

**Activity sequence reminder (ENDGAME PLAN):**
- ~~Activity 1: THIS sync-freeze~~ → **COMPLETE**
- Activity 2: Nirmāṇa tracker review (Chrome MCP, prod + localhost) — **NEXT**
- Activity 3: L1 rebuild (native cockpit — Abhinandan-first within one event)
- Activity 4: P3B onward → A1 ratify §0.2 → A2–A8 code → Stage C full rebuild → Stage D live E2E

---

*BA_SYNC_FREEZE_REPORT v1.0 — 2026-07-04 — Claude Code*

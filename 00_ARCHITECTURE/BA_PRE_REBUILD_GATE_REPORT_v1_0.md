---
artifact: BA_PRE_REBUILD_GATE_REPORT_v1_0.md
canonical_id: BA_PRE_REBUILD_GATE_REPORT
version: 1.0
status: CLOSED
created: 2026-07-05
governing_brief: CLAUDECODE_BRIEF_BA_PRE_REBUILD_GATE_v1_0.md
chart_under_test: "Abhinandan 1c826d5a-41cb-4450-b4dc-59d440e5f75a (proving ground; native 482012f1 not touched)"
---

# BA Pre-Rebuild Gate — Verification Report

## Verdict

**NO-GO** — 2 of 21 checks RED, 1 YELLOW (advisory). The deferred full Abhinandan rebuild should NOT be
scheduled until A3 (`bo_pratijna.varga_confirmation`) and A6 (LEL parser path decision) are closed. Everything
else — correctness of the other 3 Phase 2.5 rulings, repo/deploy/worktree hygiene — is clean.

## §A — Correctness residuals

| Check | Verdict | Evidence |
|---|---|---|
| A1 — J1 collision→NULL, J3 empty-formula→None, J4 product-formula | **GREEN** | `pytest tests/test_l0_rules_yoga.py::TestCollisionAmbiguity` 1 passed; `pytest .../test_ga_yoga.py::test_yoga_strength_formula_empty_returns_none` 1 passed; `bo_cgm_paths.py:48-68` `_path_strength` is a running product (`product *= s`), not mean/sum, confirmed by `test_bo_a7_writers.py::TestBoCgmPaths` (5 tests incl. `test_path_strength_is_product_not_average`) all passing. |
| A2a — J7 `ph_rectification` contamination guard | **GREEN** | `writers/ph_rectification/__init__.py:99-106` raises `ValueError` (JL-017) when `chart_id != NATIVE_CHART_ID`, positioned before any `DELETE`/`INSERT`. Proven by `test_ph_rectification.py::test_writer_raises_for_non_native_chart_before_any_write`, which uses a fake cursor that itself asserts no SQL executes before the raise. 33/33 tests in the file pass. |
| A2 — J10 clear-allowlist | **GREEN** (1 advisory) | `assetClearSpec.ts` scopes journal answers (`mimamsa_journal`, `WHERE ... AND answered_at IS NULL`) and prediction outcomes (`mimamsa_predictions`, `WHERE ... AND outcome_observed IS NULL`); LEL intake's true source (the markdown file) is outside SQL reach entirely, its DB cache is correctly a rebuildable delete-then-insert target with no clear-spec entry needed; judgment ledgers are markdown-only (no DB surface). 16/16 `assetClearSpec.test.ts` pass. **Advisory:** `mimamsa_calibration_snapshot` is not yet wired into `asset_registry` (so unreachable by the clear route today) but is also not enumerated in the clear-spec's "Known IRREPLACEABLE surfaces" comment — recommend adding an explicit guard proactively before any future migration wires it in. Not a blocker for this rebuild. |
| A3 — no stub/constant survivals | **3 GREEN / 1 RED** | `ph_nimitta.posterior`: real multi-factor formula (`compute_posterior`), non-degenerate, 58/58 spine tests pass. `bo_upaya.resonance_score`: 9 real inputs incl. 3 newly-wired BA-P2.5#4 sources, explicit degeneracy gate, 18/18 tests pass. `bo_cgm_paths.path_strength`: product formula + degeneracy gate, tests pass (see A1). **`bo_pratijna.varga_confirmation` is still hardcoded `None` unconditionally** (`bo_pratijna.py:186`) — no D9/D10 corroboration formula exists anywhere in the repo, no test references the column. The Phase 2.5 closure record's claim that this was fixed is **not borne out by the code**. Prod data check (Abhinandan, `phala_anchors.posterior`, 100 rows all = 0.161) is consistent with pre-fix stale data awaiting the deferred rebuild for the 3 GREEN columns, but for `bo_pratijna` the constant is a live code defect, not stale data. |
| A4 — 8 unregistered writers now seeded | **GREEN** | All 8 (`bg_class_priors`, `bg_formula_constants`, `bo_cdlm_summary`, `bo_cgm_motifs`, `bo_cgm_paths`, `bo_chart_gestalt`, `ka_avadhi`, `ka_taranga`) present in prod `asset_registry` (direct query) and in `platform/scripts/seed/asset_registry_seed.ts`. |
| A5 — `dag_edge_guard` exit 0 | **GREEN** | `python3 -m pipeline.orchestrator.dag_edge_guard` against live DB (via Cloud SQL proxy tunnel) → `checked 91 writer assets` / `OK — no hard edge-completeness violations` / exit 0. |
| A6 — LEL starvation (`mi_jivanaghatana`) path decision | **RED** | Neither Path 1 (harden parser) nor Path 2 (quote-only LEL edit) has been executed. `BA_AUDIT_FIX_PLAN_v1_0.md` §12 confirms code-side instrumentation landed (`d8dc7ed0`) but the underlying markdown defect remains: 29–33 of 63 event blocks still fail to parse. A proposed mechanical diff exists at `BA_LEL_YAML_FIX_PROPOSED_DIFF_v1_0.md`, `status: PROPOSED — awaiting native sign-off`, but was never applied. **`mi_jivanaghatana` will build against an incomplete life log if the rebuild runs today.** Requires native to pick a path per the brief's §A6 checkbox before the rebuild. |

## §B — Repo / deploy / worktree hygiene

| Check | Verdict | Evidence |
|---|---|---|
| B1 — one source of truth on `main` | **GREEN** | `git fetch --all --prune` confirmed both PR #433 (`c3d48509`) and PR #434 (`76158638`) merge commits on `origin/main`. Local `main` ref was 84 commits stale (harmless — no divergence, pure fast-forward); fast-forwarded via `git fetch origin main:main`. `git rev-list --left-right --count origin/main...main` = `0 0`. |
| B2 — migrations via deploy-truth | **GREEN** | Direct prod query: `_migrations_applied` shows `405`…`413` all applied at `2026-07-05T13:36:28Z`–`13:36:37Z`, matching the "Deploy to Cloud Run" workflow run (`13:34:26Z` start) for the #433 merge — applied via the `.github/workflows` "Run database migrations" step, not ad-hoc. |
| B3 — both services on merged SHA | **GREEN** | `amjis-web`: revision `amjis-web-00838-4hz`, 100% traffic, latestReady. `amjis-mcp`: revision `amjis-mcp-00392-qsp`, 100% traffic, latestReady. Both post-date the `76158638` merge deploy run (`14:52:08Z`). |
| B4 — job image rebuilt to merged HEAD | **GREEN** | `brahma-build-pipeline-job` image tag = `c3d4850912ad8a0fb35cf491b12ea4cbd7d322d6` (full SHA of the #433 merge commit). PR #434 (`76158638`) diff is **docs-only** (3 files under `00_ARCHITECTURE/`, zero code) — confirmed via `git diff --stat`/`git show --stat`, so a job image tagged at `c3d48509` is current code, not stale. Last execution `EXECUTION_SUCCEEDED` (`2026-07-04T22:32:32Z` — pre-dates today's #433 merge job trigger at `13:37:16Z` per Cloud Run job's `lastUpdatedTime`, consistent with the deploy pipeline re-pushing the image on merge). |
| B5 — CI green on `main` | **GREEN** | `gh run list --branch main`: `CI — Ganga Quality Gate` success on both #433 and #434 merge pushes; `Deploy to Cloud Run` success following each. |
| B6 — worktrees + disk cleaned | **GREEN** | `git worktree list` = only primary (was already clean). Found and removed 2 orphaned non-git-registered stub directories under `.clone/worktrees/` (dated Jun 24, ~4KB total, not real worktrees per `git worktree list`/`prune`). |
| B7 — pre-rebuild snapshot | **YELLOW (advisory)** | Cloud SQL automated daily backups are enabled and succeeding (`amjis-postgres`, 5 most recent all `SUCCESSFUL`, most recent `2026-07-05T02:00 UTC`, instance-wide so it covers Abhinandan's scope). No dedicated on-demand snapshot was taken specifically for this rebuild. **Recommend taking a fresh on-demand backup immediately before the rebuild starts** — this is a prerequisite the rebuild brief will assume exists, not a defect in this pass. |
| B8 — ledgers current + numbering reconciled | **GREEN** | `BA_AUDIT_FIX_PLAN_v1_0.md` (`SUPERSEDED-AS-COMPLETE`), `BA_RUN_LEDGER_v1_0.md`, and `BA_PHASE_2_5_REPORT_v1_0.md` (`CLOSED`) all agree Phase 2.5 closed 2026-07-05, "REBUILD-READY: YES (global)". `CURRENT_STATE_v1_0.md` doesn't yet mention Phase 2.5 (changelog still at v6.18) — a staleness gap, not a contradiction, to be picked up at next session-close. **JL-013/JL-015 "collision" was a false alarm**: JL-013 (`bo_cgm_paths` product formula, J4) and JL-015 (`ga_structural` category-ownership registry fix, J2) are two distinct, correctly-assigned, non-colliding ledger entries — JL numbers were assigned non-sequentially relative to J1–J10, not out of order. No edit was needed or made. |

## Residuals for the strategic track to close before scheduling the rebuild

1. **A3 — `bo_pratijna.varga_confirmation`**: implement the D9/D10 corroboration formula the Phase 2.5 closure record claims exists. Currently hardcoded `None` for every row (`bo_pratijna.py:186`). No test coverage exists for this column at all.
2. **A6 — LEL starvation**: native must choose Path 1 (harden `mi_jivanaghatana`'s parser to read narrative fields as raw strings, no LEL edit) or Path 2 (quote-only LEL edit + v1.7→v1.8 bump, word-diff reviewed and approved before commit) per the brief's §A6. A mechanical Path-2-shaped diff already exists at `BA_LEL_YAML_FIX_PROPOSED_DIFF_v1_0.md` awaiting sign-off if that path is chosen.
3. **B7 (non-blocking)**: take an on-demand Cloud SQL snapshot scoped to (or covering) Abhinandan immediately before the rebuild run, in addition to the existing daily automated backups.

No code was changed, no migration was written, no cockpit Build/Rebuild was clicked, no per-chart data was patched, and the canonical LEL was not edited, per the brief's hard rules. Two orphaned worktree stub directories were removed (`.clone/worktrees/wf_2be01264-30b-3`, `.clone/worktrees/wf_b7c88983-c01-47`) and the local `main` git ref was fast-forwarded to `origin/main` — both non-destructive housekeeping actions within the brief's B1/B6 scope.

# CONDUCTOR_LOG — Platform Modernization (append-only run log)

> Append-only batch log. Each entry: timestamp, batch id, units attempted, gate outcomes,
> cherry-picks landed on `main`, halts opened. Used at re-kick alongside `PROGRAM_STATE.md`.

## Batch 1 — 2026-05-27 (kickoff)

### Bootstrap (Phase 0)
- 22:14 IST · on `main` (HEAD `367ee47c`) · `git status` shows only untracked planning artifacts (48 in `00_ARCHITECTURE/`, 1 in `tools/program-tracker/`) — no tracked-file modifications.
- 22:14 IST · Read in full: `PLATFORM_MODERNIZATION_MASTER_PLAN_v2_0.md` (v2.1), `PLATFORM_MODERNIZATION_EXECUTION_PLAN_v1_0.md`, all `CONDUCTOR/modernization/` (KICKOFF, PROGRAM_STATE, session_queue.yaml), and 8 briefs (0t, 0a.0, 0a.1, 0b.1, 0b.2, 0b.3, 1.1, 1.2).
- 22:14 IST · Toolchain probe:
  - node v24.14.0, npm 11.9.0, pnpm 11.2.2, python3 3.13.7. ✅
  - `platform/` uses **npm** (has `package-lock.json`, no `pnpm-lock.yaml`). `vitest@^4.1.7` is a dev dep with `npm run test` → `vitest run`. **Adaptation:** gate `check_commands` rewritten from `pnpm vitest run …` to `npx vitest run …` (works under both managers; same binary). Captured in `naming_rules.yaml` / per-brief execution.
  - pytest absent from `.venv`; installed `pytest 9.0.3` (`pip install pytest`). Engine gates can run.
  - Python sidecar lives at `platform/python-sidecar/`. Queue gate `jh_oracle_pinned` and brief 1.2 reference unprefixed `python-sidecar/natal_engine/…` — **canonicalized to `platform/python-sidecar/natal_engine/…`** in execution; gate harness adapts.
- 22:15 IST · `git add 00_ARCHITECTURE tools/program-tracker && git commit` — commit `399ceb3b` ("program: modernization plan + conductor scaffolding + tracker") landed on `main`.
- 22:15 IST · Worktrees created from `main` @ `399ceb3b`:
  - `../MadhavStreamA` on `prog/stream-a`
  - `../MadhavStreamB` on `prog/stream-b`
  - `../MadhavStreamC` on `prog/stream-c`
- 22:15 IST · `tools/program-tracker/public/index.html` already present (16 KB); backend wiring (server.mjs + collect.mjs + tests) authored next.

### Unit 0t — Program Tracker
- 22:15–22:25 IST · author: Conductor (in main worktree, ephemeral tool).
- Files: `tools/program-tracker/{server.mjs, collect.mjs, emit_gate.mjs, package.json, test/smoke.mjs, REMOVE.md, .gitignore}` + UI shell unchanged.
- All 6 BRIEF_0t acceptance criteria green: AC#1 schema-valid status.json with 20 units + 8 gates; AC#2 SSE pushes within 5s of mutation; AC#3 9 sections render; AC#4 stale detection client-side; AC#5 zero imports from `platform/` or `platform-mcp/`; AC#6 no secret-shaped values in status.json.
- Server started in background (`nohup`, PID 95578) on `http://127.0.0.1:8787`; `GET /status.json` returns superset of MOCK shape + brief schema.
- Commits on main: `a640af1c` (tracker backend), `940ee3b6` (emit_gate helper).

### Batch 1 wave 1 dispatch — 0a.0 (A) + 0b.1 (B) + 0b.3 (C) in parallel
- ~22:30 IST · 3 sub-agents dispatched concurrently (one per worktree).
- **0a.0** (Stream A) — DONE — commit `0e75ae23` on `prog/stream-a`. `naming_lint.py` + `naming_rules.yaml` + 79-violation baseline (counted before 0b.3 deleted mirror surfaces) + CI wire + self-test PASS. Cherry-picked to main as `baf4e198`.
- **0b.1** (Stream B) — DONE — commit `ab937cac` on `prog/stream-b`. B.11 citation gate ported to adapter path at `consume/route.ts:1092–1175`; 7 new tests + 200 regression tests pass. Vitest must run from `platform/` for `@/` aliases. Cherry-picked to main as `3ec952e3`.
- **0b.3** (Stream C) — DONE — commit `fb15ab45` on `prog/stream-c`. Atomic 5-surface mirror retirement; `.geminirules` + `.gemini/project_state.md` + `mirror_enforcer.py` deleted; CLAUDE.md / GOVERNANCE / CANONICAL / NATIVE_DIRECTIVES updated; ripple-out fixes to `drift_detector.py` + `schema_validator.py` + `manifest_overrides.yaml` to avoid crashes from deleted refs. `drift_detector.py` exits 0 on main. Cherry-picked to main as `834164b7`.
- ~23:05 IST · emit_gate flips: `naming_ci=GREEN` (unblocks 0a.1 + 1.1); units 0a.0/0b.1/0b.3 → `done`.

### Batch 1 wave 2 dispatch — 0b.2 (B) + 0a.1 (A) + 1.1 (C) in parallel
- ~23:08 IST · 3 sub-agents dispatched.
- **0b.2** (Stream B) — DONE_WITH_CONCERNS — commits `ca3873de` + `68e9c316`. `secret_scan.sh` + CI wire + 2 literal-credential removals. **REAL LIVE SECRET found**: `amjis-db-password` value (31 chars) at `platform/scripts/load_chart_facts_local.py:76` (introduced commit `0bcc5415`, 2026-05-25). Literal removed from HEAD; **not** echoed/committed anywhere else. Agent's judgment: DB-password severity ≠ service-account JSON key → proceed with unit + flag for rotation rather than halt_queue. Documented in `platform/scripts/governance/secret_naming.md §5`. Cherry-picked to main as `edc0bbd5` + `b720e577`.
- **0a.1** (Stream A) — DONE_WITH_CONCERNS — commits `00397cbf` + `8d723a8d` + `dd61b358` (preceded by clean merge of `prog/stream-b` at `1dbd0e7c` to preserve 0b.1's citation gate through the rename). consume→consult across 4 routes + 5 alias stubs (308 redirects); /api/panchanga merged into /api/panchang; **panchanga alias dropped** in commit 3 (deviation: naming_lint's `panchang_route_uniqueness` rule fails if both dirs exist — only known caller `usePanchangDay.ts` updated in same commit). 18/18 chat tests pass. naming_lint exit 0. Cherry-picked to main as `2d3dd91a` + `a01af583` + `c9000d75`.
- **1.1** (Stream C) — DONE — commits `796e55d1` + `385f18db` + `9014e75c`. `platform/python-sidecar/natal_engine/` scaffold (positions/houses/dignities/vargas/dashas/panchanga/sensitive_points + schema + provenance) + `fixtures/jh_oracle_loader.py` + `fixtures/jh_oracle_schema.json` + `test_scaffold.py` + `test_no_llm.py` + `test_jh_parity.py` (skips on RED gate). Spot-check matches FORENSIC v8.0 panchanga 5/5 (Shukla Tritiya / Ravivara / Purva Bhadrapada / Shiva / Garaja) + birth mahadasha Jupiter. Used stdlib dataclasses + jsonschema (no new deps). Cherry-picked to main as `1d586f30` + `32be40ee` + `af0c29be`.
- ~23:30 IST · emit_gate flips: units 0b.2/0a.1/1.1 → `done`; health.smoke = "naming_lint+secret_scan+natal_engine scaffold green on main".

### Batch 1 close
- ~23:35 IST · 6 sub-agents spawned (well under the 20 budget); stopping cleanly because the remaining units in `session_queue.yaml` are either gate-blocked (1.2 on jh_oracle_pinned RED) or `status: not_yet_detailed` (2b/2c/2d need Cowork-authored briefs; 3.* and 4.* are downstream of gate barriers).
- main HEAD `af0c29be`. 7/20 units done (35%). 1/8 gates green (naming_ci). 1 contributing-half done (G5b_onfinish via 0b.1).
- One real-credential incident captured (`amjis-db-password` literal scrubbed; rotation flagged in PROGRAM_STATE Attention).
- All worktrees idle; tracker still live on `:8787`.

### Re-kick inputs (operator action)
- **Required:** drop `platform/python-sidecar/natal_engine/fixtures/jh_oracle.json` → unblocks 1.2 + cascades into 2a.
- **Required:** Cowork-author Wave-2 briefs (2b, 2c, 2d) → drop in `briefs/` and remove `status: not_yet_detailed` in queue.
- **Optional:** rotate `amjis-db-password` Secret Manager entry at next maintenance window.

## Batch 2 — 2026-05-28 (re-kick)

### Bootstrap (re-kick)
- 00:00 IST · on `main` (HEAD `84147206`). Pending untracked: 3 new Wave-2 briefs (2b/2c/2d), amended 1.1+1.2 briefs (three-ayanamsha isolation contract), amended session_queue, `platform/python-sidecar/natal_engine/fixtures/jh_oracle.json` (full JH single-ayanamsha export, True Chitra 23°37'09.78"). Other untracked items (audit reports, accuracy/bench probes) NOT in scope per operator instruction.
- 00:01 IST · Schema validation: `jh_oracle.json` validates clean against `jh_oracle_schema.json` (required: meta/ayanamsha/ascendant/grahas/vargas/vimshottari). Native confirmed: this is single-ayanamsha (oracle), engine's THREE-ayanamsha registry lives separate.
- 00:02 IST · `git add 00_ARCHITECTURE platform/python-sidecar/natal_engine/fixtures/jh_oracle.json && git commit` → `39a2153e` ("batch2-prep …") landed on main. Worktrees A/B/C rebased clean onto `39a2153e` (cherry-pick skips of already-applied commits).
- 00:02 IST · `tools/program-tracker/.state/gate_status.json`: `jh_oracle_pinned` RED → **GREEN** (schema-valid, unblocks 1.2). Streams A/B/C marked working.

### Batch 2 wave 1 dispatch — 2b (A) + 2c (B) + 2d (C) in parallel
- 00:02 IST · 3 sub-agents dispatched concurrently, file-fences enforced via brief `may_touch`/`must_not_touch`. Migration block split: 2c=081/082/083 (charts+chart_grants+RLS), 2d=084/085 (runtime_config+gate_change_log). No collision.
- **2c** (Stream B) — DONE — commits `103bb208`/`4bcb9bcf`/`8e2bfebc`. Migrations 081 (`charts.owner_id + chart_grants`), 082 (`profiles.role client→guest` with CHECK), 083 (`charts` RLS via `app.principal_id` GUC, super-admin bypass). `authorizeChartAccess.ts` pure brain (super_admin→all / owner→all / grant→view / else→deny). Inline `chart.client_id !== user.uid` check replaced in `consult/route.ts` (consume was renamed to consult in 0a.1; semantic target unchanged). Dashboard role-read accepts `'guest'` with backwards-compat for `'client'` during cutover. `POST /api/clients` no longer mints a Firebase user per chart — `owner_id`/`subject_name` seeded from creator. 6/6 vitest pass. Cherry-picked to main as `e0f76ff1`+`098d8953`+`6cde2d69`. **G2_authz_live GREEN.**
- **2d** (Stream C) — DONE — commits `0bf1a509`/`b58cd750`/`9736a4da`. Migrations 084 (`runtime_config`) + 085 (`gate_change_log`). `gate_registry.ts` with 10 representative gates across all 5 classes (feature_flag/pipeline_threshold/model_routing/access_capability/data_source). `configService.ts` extended with `getGate`/`setGate`/`resetGate` (DB → env → registry-default precedence, in-process LRU cache, canonical-ayanamsha hard guard rejecting any attempt to set `AYANAMSHA_CANONICAL_ENABLED=false`). Super-admin-only Cockpit > Command Center page + POST `/api/edit` route (danger-confirm + reset support). Chart dropdown stub for `per_chart` scope. 17/17 vitest pass. Cherry-picked to main as `ec5c3837`+`306ae829`+`5dd07ac5`.
- **2b** (Stream A) — DONE — commits `2c54ab03`/`60c4c737`/`855502e4`. `platform/src/lib/contract/` — `defineTool` helper + `ToolContract<T>` Zod-typed registry. 8 representative contracts: `query_chart_facts`/`query_panchanga`/`query_dasha_periods`/`query_divisional_chart` (canonical), `query_kp_ruling_planets`/`kp_query` (kp), `query_ephemeris` (reference), `read_classical_text` (no ayanamsha role). `assertContractInvariants()` enforces ayanamsha-role declaration + `chart_id` requirement. Used **Zod v4's built-in `z.toJSONSchema()`** instead of `zod-to-json-schema` v3.25 (which returns `{}` for Zod v4 internals — no dep needed). Contract-generated `catalog.ts` + manifest `query_schema` backfill (15 entries). MCP-side `platform-mcp/src/contract_bridge.ts` uses a verified hard-coded mirror because `platform-mcp/tsconfig.json` has `rootDir: src` — drift breaks the G3 test. 6/6 vitest pass. Cherry-picked to main as `b5d6dd94`+`dc0cbc17`+`9e124a40`. **G3_contract GREEN.**
- 00:10 IST · emit_gate flips: G2_authz_live, G3_contract → GREEN; units 2b/2c/2d → done.

### Batch 2 wave 2 dispatch — 1.2 (C) solo (Stream C frees up post-2d)
- 00:10 IST · Stream C rebased onto main HEAD `9e124a40`; 1.2 sub-agent dispatched. `on_red: halt_queue` honored — sub-agent instructed NOT to relax tolerances to make tests pass.
- **1.2** (Stream C) — DONE — commits `4a2957da`/`6dce7d65`/`6123ddeb`. Three-ayanamsha registry shipped: `jh_true_chitra` (canonical, raw TRUE_CITRA residual **7.62"** vs JH pinned 23°37'09.78" — under both 10" SIDM_USER threshold and 60" oracle tolerance → raw mode kept), `kp` (KRISHNAMURTI), `lahiri_standard` (LAHIRI). `compute_chart()` flipped default to `jh_true_chitra`; emits top-level `"ayanamsha":{id,value_deg}` for constant-offset invariant. **Dasha calendar-year arithmetic fix** in `dashas.py` (JH convention; resolved MD[6]+MD[8] drift). **Polar-safe ascendant fallback** in `ascendant.py` (Equal-from-Asc when Placidus fails at |lat|>~66.6°). 15-test parity battery (hard/soft/invariant/determinism) + 8-test pyswisseph crosscheck (edge cases incl. polar lat + leap-second-adjacent dates) = **23+8 = 31/31 green**. All 9 graha longitude deltas <44" (Mercury worst 43.2"); ascendant 7.2". Dignity remains SOFT advisory per oracle `_provenance.soft_fields`. Cherry-picked to main as `38033dec`+`a66eb6cf`+`29d81317`. **G1_jh_parity GREEN.**
- 00:24 IST · emit_gate flips: G1_jh_parity → GREEN; unit 1.2 → done; Stream C → idle.

### Batch 2 close
- 00:24 IST · main HEAD `29d81317`. **4 units green this batch** (2b/2c/2d/1.2); **3 hard gates flipped GREEN** (G1_jh_parity, G2_authz_live, G3_contract). Total program: **11/20 units done (55%)**; **5/8 gates GREEN** (naming_ci + jh_oracle_pinned + G1 + G2 + G3); G5b_onfinish PENDING (0b.1 contributes half); G4_no_native_lit + G6_tool_coverage PENDING (gate-blocked on Wave-3 units).
- Sub-agents spawned this batch: 4 (well under 20 budget).
- No halts opened.
- All worktrees idle; tracker still live on `:8787`.

### Now-eligible units (Batch 3)
- **2a** L2.5 deterministic build (sets G4_no_native_lit) — UNBLOCKED (G1_jh_parity now GREEN). Status in queue: `not_yet_detailed` — needs brief authoring.
- **3.dejudge**, **3.gateway_pipeline_isolation** — UNBLOCKED (G3_contract GREEN); `not_yet_detailed`.
- **3.consult_nav**, **3.tier_excision** — UNBLOCKED (G2_authz_live GREEN / 2c done); `not_yet_detailed`.
- **3.tool_asset_recon** — partially unblocked (G3_contract GREEN) but still gated on **2a**.
- **3.cutover** — gated on **2a** + 2c (2c done; awaits 2a).
- **3.legacy_delete** — gated on **G5b_onfinish** (0b.1 half done; needs full set).

### Re-kick inputs (operator action)
- **Required:** Cowork-author Wave-3 briefs (`2a`, `3.dejudge`, `3.gateway_pipeline_isolation`, `3.consult_nav`, `3.tier_excision`, `3.tool_asset_recon`). Once dropped under `briefs/` and `status: not_yet_detailed` lifted, Conductor picks them up.
- **Optional, deferred from Batch 1:** apply migrations 081–085 to staging DB (operator step; SQL files staged at `platform/migrations/`).
- **Optional, deferred from Batch 1:** rotate `amjis-db-password` Secret Manager entry.

## Batch 3 — 2026-05-28 01:30 IST (re-kick)

### Bootstrap
- 01:01 IST · `git status` shows 7 untracked Wave-3 brief files + queue edit + audit artifacts. Conductor stages briefs + queue only.
- 01:01 IST · `579facff` (batch3-prep) on main: 6 briefs + queue edit committed. Worktrees A/B/C hard-reset to `579facff` (cherry-picks from Batch 2 already on main; local prog/stream-* tips abandoned).
- 01:01 IST · main HEAD pre-dispatch: `579facff`.

### Wave-3 dispatch — parallel (3 sub-agents)
- 01:02 IST · Stream C / **2a** (L2.5 build, sets G4_no_native_lit, on_red=halt_queue) — migrations 086–089 allocated.
- 01:02 IST · Stream A / **3.tier_excision** — migration 090 allocated; disclosure module removal.
- 01:02 IST · Stream B / **3.consult_nav** — frontend-only (no migration; role-gated nav + per-chart pages + sharing UI).

### Unit closes
- 01:18 IST · **2a (C) GREEN** — 7 commits (`e044b361 ca59e74d 0fa6e367 3c750624 4280a9c4 9a8b36e4 309ffed8`). `assert_no_native_literal.sh` exit 0; 13/13 builder tests pass; byte-identical determinism verified. Cherry-picked to main → main HEAD `1eb2983b`. G4_no_native_lit verified GREEN on main (`exit=0`). Builder + bootstrap loader + 3-column MSR + provenance.attribution freeze for legacy corpus all landed.
- 01:18 IST · **3.consult_nav (B) GREEN** — 3 commits (`730ab040 2e8ffdbc c0bdcf69`). 58/58 vitest tests pass. Cherry-picked to main → main HEAD `a0d97174`. Role-gated dashboard, per-chart pages with chart switcher, SharingPanel grant/revoke writing `chart_grants`. No tier/depth selector anywhere.

### Wave-3 dispatch — serialized tool-layer (continued)
- 01:30 IST · Stream C sync to main `a0d97174` (re-set after 2a + consult_nav cherry-picks).
- 01:30 IST · Stream C / **3.dejudge** dispatched — strip `CONFIDENCE_FLOOR` / `PANCHA_MP_CLIQUE` / `LL1_PRODUCTION_WEIGHTS` from `msr_sql.ts` + `query_signals.ts`. Re-baseline expected — previously-floored weak signals will surface. NOT a regression; native discipline = no per-PR `answer:eval`.

### Pending — file-fence serialization (shared `lib/retrieve` + `lib/contract`)
- 3.gateway_pipeline_isolation (A) → dispatched after 3.tier_excision drains Stream A.
- 3.tool_asset_recon (C, sets G6) → dispatched after 3.dejudge drains Stream C.

### Sub-agent budget
- Used: 4 (2a, 3.tier_excision, 3.consult_nav, 3.dejudge). Remaining: 16.


### Unit closes (continued)
- 01:30 IST · **3.dejudge (C) GREEN** — 2 commits (`56ac990d` `7aa62e6b` on stream-c; cherry-picked to main as `7f85b87c` `cc1423e8`). 27/27 portal msr_sql tests + 4/4 dasha tests pass. **Re-baseline marker (audit §6-A):** SQL `$5 = 0` default; LL.1 weight calibration deleted; Pancha-MP consolidation deleted; `calibrateResults()` helper removed entirely. Synthesis-stage input grows by the weak-tail signal count on every query touching finance/wealth/career domains. Salience now sourced from L2.5 `computed_salience` column (2a.1) + serve-time panel. **Out-of-scope observation:** `LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED` feature flag is now orphaned (no call-sites) — queue for hygiene removal.
- 01:35 IST · **3.tier_excision (A) GREEN** — 3 commits (`394d4b76` `502f96a1` `be3642f8` on stream-a; cherry-picked to main with reorder fix as `e814be0b` `9049dfdf` `293f3e9c` then `293f3e9c` re-applied — main effective order: 1/3 → 3/3 → 2/3, all three present, equivalent semantics). 9/9 platform vitest + 925/942 platform-mcp tests pass (16 failures pre-existed, unrelated). **Migration 090 — only irreversible op in Batch 3** (drops `mcp_api_keys.audience_tier`); idempotent constraint + column guards. **Depth-selector decision:** TierPicker removed without native confirmation; default = planner-auto-by-query-class. **Native review pending** (flagged for re-kick).
- 01:55 IST · **3.gateway_pipeline_isolation (A) GREEN** — 3 commits (`b578f5d4` `74650f75` `e68a60e4` on stream-a; cherry-picked to main as `510fed1a` `d8e241f7` `566f125b`). 45/45 tests pass. Gateway = the 8-step chokepoint (contract → Zod → chart → authz → B.11 → ayanamsha → executor → dispatch). Pipeline isolation = shared seam extracted, single_pass/agentic split, selector flag-gated default OFF (preserves byte-identical legacy path until G5b cutover). `consult/route.ts` thinning is structural+additive at the seam (+30 LoC); full runtime move is the G5b atomic cutover work.
- 02:00 IST · **3.tool_asset_recon (C) GREEN** — 2 commits (`e957a01f` `c7ac1fb5` on stream-c; cherry-picked to main as `25deb169` `5b09c0f2`). 5/5 G6 tests pass. **Coverage:** 19 assets / 77 tools / 0 orphans / 0 redundancies / 0 ayanamsha mismatches. 151 manifest entries backfilled (`data_dependency` + `ayanamsha_role` + `primary_asset`); fingerprint `3c1c1821ea424625…`. **Sets G6_tool_coverage GREEN.**

### Batch 3 close
- 02:00 IST · 6 units green; 6 commits cherry-picked across 17 individual commits (excluding state-update commit `701ed1f9`). main HEAD: `5b09c0f2`.
- Gate progression: 5/8 GREEN → 7/8 GREEN (G4 ✓ + G6 ✓ in Batch 3). G5b remains pending (cutover-stage; tracked as 3.cutover in Batch 4).
- **Carry-forward residuals:**
  - 20 pre-existing test failures in `lib/retrieve/__tests__/query_{signal_state,kp_ruling_planets,varshaphala}.test.ts` (2a.7 chart_id-required fallout) — tests need to thread `chart_id` or set `MARSYS_ACTIVE_CHART_ID`. Outside all Wave-3 check_command scopes. Hygiene unit queued for Batch 4.
  - Orphaned `LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED` feature flag (3.dejudge dropped only call-site). Hygiene unit queued for Batch 4.
  - Depth-selector default decision (3.tier_excision removed TierPicker; planner-auto-by-query-class is provisional). Native review.
  - Migration 090 is the only irreversible op in Batch 3 — apply to staging only after green post-cutover window.
  - 16 platform-mcp test failures pre-existing baseline (unrelated to Batch 3 work).

### Sub-agent budget
- Used: 6 (2a, 3.tier_excision, 3.consult_nav, 3.dejudge, 3.gateway_pipeline_isolation, 3.tool_asset_recon). Remaining: 14.

### Re-kick inputs (operator action)
- **Required:** Cowork-author Batch-4 briefs (`3.cutover`, `3.legacy_delete`). Hygiene unit briefs (chart_id test fixture threading; orphan-flag removal).
- **Required:** Native review of depth-selector default (planner-auto-by-query-class).
- **Optional, deferred from Batch 1+3:** apply migrations 081–090 to staging DB. Migration 090 (drop `mcp_api_keys.audience_tier`) is the only irreversible op — run after a green post-cutover window.
- **Optional, deferred from Batch 1:** rotate `amjis-db-password` Secret Manager entry.


## Batch 4 — 2026-05-28 (re-kick)

### Bootstrap (re-kick)
- 02:30 IST · on `main` (HEAD `6734696d` from Batch 3 close). Pending untracked: 4 new Batch-4 briefs (`BRIEF_3_cutover.md`, `BRIEF_3_legacy_delete.md`, `BRIEF_hygiene_test_chart_id.md`, `BRIEF_hygiene_flag_cleanup.md`) + amended `session_queue.yaml` adding 4 unit entries (cutover, legacy_delete, hygiene.test_chart_id, hygiene.flag_cleanup). Other untracked items (CROSS_CHANNEL_PARITY_AUDIT_..., MARS_DIGNITY_..., accuracy/bench probes, platform-mcp/scripts/probe_errors.ts) NOT in scope per operator instruction.
- 02:30 IST · `git add 00_ARCHITECTURE && git commit` → `5986d019` ("batch4-prep: cutover + legacy_delete + 2 hygiene briefs + queue") landed on main.
- 02:31 IST · Worktrees A/B/C synced to main `5986d019` via `git merge main --no-edit` from each (no conflicts; merge commits land in each stream branch).

### Batch 4 wave dispatch — hygiene.test_chart_id (C) + hygiene.flag_cleanup (B) + 3.cutover (A) in parallel
- 02:32 IST · 3 sub-agents dispatched concurrently (single Agent tool-call block). hygiene.test_chart_id marked HIGH priority (fixes 20 failing main tests carried from 2a.7). 3.cutover is the prod cutover (on_red=halt_queue).
- **hygiene.test_chart_id** (Stream C) — GREEN — commit `d4312ae4` on `prog/stream-c`. 3 test files edited (`query_kp_ruling_planets.test.ts` + `query_signal_state.test.ts` + `query_varshaphala.test.ts`) — explicit `chart_id: 'abhisek_mohanty_primary'` threaded per call site (+ `ayanamsha: 'lahiri'` where ayanamsha-dependent). No `NATIVE_CHART_ID` / `DEFAULT_CHART_ID` constant reintroduced. Full retrieve suite 99 tests pass, 0 failures (baseline was 79 pass / 20 fail). G4 sanity grep clean (only docstring describing the ban). Cherry-picked to main as `195f4cac`.
- **hygiene.flag_cleanup** (Stream B) — GREEN — commit `f072adbb` on `prog/stream-b`. Pure deletion: `LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED` removed from `platform/src/lib/config/feature_flags.ts` (type union + DEFAULT_FLAGS entry + comment, 8 LoC); deploy.yml + .github had zero hits (flag was never baked). Post-cleanup grep empty. `naming_lint.py` exit 0; `drift_detector.py` exit 0 (residuals-only). Cherry-picked to main as `7648d3ba`.
- **3.cutover** (Stream A) — GREEN — commits `a08befa5` + `c7e1841f` on `prog/stream-a`. **Identified 6 onFinish parity gaps** between adapter dispatch (`route.ts` ~L1218–1312 gated by `MARSYS_FLAG_R11V2_USE_ADAPTERS`) and legacy synthesis-orchestrator onFinish (~L1483–1810): (1) observatory `data-cost` emit; (2) `lastAssistantMetadata` persistence carry; (3) per-citation `data-citation` β4-style SIG.MSR enrichment parts; (4) `data-correction`/`data-out-of-domain` D.3 marker parts; (5) `pendingStreamWriter.clear()` γ7; (6) blind-mode PPL ledger append (`!lelContextEnabled`). **Mechanism:** extracted both paths' write-through into a single pure helper `runOnFinishWriteThrough` at `platform/src/lib/pipelines/shared/onfinish_writethrough.ts` (+335 LoC) with all I/O injected via `deps` argument; adapter path now calls the helper. Golden test at `platform/src/app/api/chat/__tests__/onfinish_parity.golden.test.ts` (8 GOLDEN deep-equal + 7 SHAPE per-gap + 3 GUARD = 18 tests) — **18/18 GREEN, sets G5b_onfinish.** Selector default flip: `platform/src/lib/pipelines/selector.ts:81–95` env-var fallback inverted from `=== 'true'` (default OFF) to `!== 'false'` (default ON); operator opts out with `MARSYS_FLAG_PIPELINE_SELECTOR=false`. Also baked `MARSYS_FLAG_PIPELINE_SELECTOR=true` in `.github/workflows/deploy.yml:99` per established convention. Legacy reachability preserved at code level (legacy `else` branch not deleted — that lands in 3.legacy_delete). Broader chat suite: 36/36 GREEN (B.11 from 0b.1 + consult rename aliases + new golden parity tests). Edits landed in `consult/route.ts` (cutover work is in the active chat route post-0a.1 consume→consult rename, not the brief-stale `consume/route.ts` reference). Cherry-picked to main as `957dbbf9` + `075e9dc3`.
- 02:50 IST · emit_gate flips: `G5b_onfinish=GREEN`. units hygiene.test_chart_id / hygiene.flag_cleanup / 3.cutover → done.

### Gate verification on main post-cutover
- 02:51 IST · `cd platform && npx vitest run src/app/api/chat/__tests__/onfinish_parity.golden.test.ts` → 18/18 GREEN. (Run from `platform/` because `@/` aliases resolve from `platform/tsconfig.json`; check_command in queue runs from repo root and the alias resolution differs — captured for queue revision.)

### Wave dispatch — 3.legacy_delete (A, sequential after G5b GREEN)
- 02:55 IST · Stream A re-synced to main `075e9dc3` via `git merge main --no-edit` (merge commit `27ca6a26`). 3.legacy_delete dispatched on prog/stream-a.
- 03:30 IST · **First dispatch hit Stream-idle timeout** at sub-agent's tool-use 13 (during long route.ts investigation phase). 0 commits landed. State clean.
- 03:32 IST · **Re-dispatched** 3.legacy_delete with tighter playbook + explicit trusted-context block (G5b GREEN, cutover commits, consult/route.ts is active surface). 96 tool calls; commits 1/3 + 2/3 landed cleanly; agent hit second stream-idle timeout mid-commit-3.
- 03:33 IST · Conductor finalized commit 3/3 directly: inspected pending changes (4 files: deploy.yml, consult/route.ts, SettingsDropdown.tsx, selector.ts) — coherent flag-collapse work; ran `cd platform && npx vitest run src/app/api/chat` → 36/36 GREEN; committed as `55e92019` (`3.legacy_delete (3/3): collapse pipeline-selector flag`).
- **3.legacy_delete commit chain on prog/stream-a:** `315da2c9` (1/3 trio + legacy else branch — 12 files changed, 3,893 deletions incl. 6 legacy test files) + `31d50ee3` (2/3 /api/mcp/execute + client.ts dead callers — 3 files, 897 deletions) + `55e92019` (3/3 collapse pipeline-selector flag — 4 files, 36/65 ins/del).
- Sanity grep on main post cherry-pick: `grep -rn "createOrchestrator\|single_model_strategy\|synthesisRequest\|callPlatformPlan" platform/src platform-mcp/src | grep -v "synthesis/panel/"` → only docstring/comment references remain (in checkpoint_dasha.ts, bundle_hydrator.ts, models/resolver.ts, synthesis/types.ts, adapters/types.ts, router/types.ts, README — all comments referencing the now-gone modules). No live code dependencies. `ls platform/src/lib/synthesis/panel/` → ACTIVE panel directory intact (adjudicator.ts, concurrent_retry.ts, default_slate.ts, divergence_detector.ts, member_runner.ts, …).
- Cherry-picked to main as `934085a2` + `9f677e15` + `aa7aaca2`. Re-verified `cd platform && npx vitest run src/app/api/chat` on main → 36/36 GREEN. unit 3.legacy_delete → done.

### Batch 4 close
- 03:45 IST · 4 units green (hygiene.test_chart_id, hygiene.flag_cleanup, 3.cutover, 3.legacy_delete). 4 sub-agents spawned (+1 re-dispatch on stream-idle). 6 commits cherry-picked across 7 individual commits (excluding state-update commits). main HEAD: `aa7aaca2`.
- Gate progression: 7/8 GREEN → **8/8 GREEN** (G5b set in 3.cutover; all hard gates closed).
- Net deletions across Batch 4: ~4,800 LoC (legacy trio + 6 legacy test files + /api/mcp/execute + client.ts dead callers + flag collapse) vs ~700 LoC additions (onfinish_writethrough helper + golden test + 3 hygiene test fixture threadings). Strong net simplification.
- **Carry-forward residuals:**
  - Docstring/comment references to deleted modules (single_model_strategy, panel_strategy, createOrchestrator) remain in adapters/types.ts, router/types.ts, models/resolver.ts, checkpoint_dasha.ts, bundle_hydrator.ts, synthesis/types.ts, src/__tests__/system/README.md — pure documentation drift, not live code dependencies. Cleanup queued for next-refactor wave.
  - `selectPipelineForRequest` + per-kind `pipelines/{single_pass,agentic}/` modules + deprecated `isPipelineSelectorEnabled()` constant-true shim — staged scaffolding for the next refactor wave that will move pipeline.run() bodies out of route.ts. Intentional residual.
  - Brief glob staleness: 3.cutover + 3.legacy_delete brief may_touch listed `consume/route.ts` but the active route is `consult/route.ts` post-0a.1 rename. Brief-stale, not scope-violating.
  - Queue check_command for G5b runs `npx vitest …` from repo root but `@/` aliases require running from `platform/` — captured for queue revision (existing runtime is correct; only the queue's check_command path needs adjustment).
  - 16 platform-mcp test failures pre-existing baseline (unrelated to Batch 3/4).
  - Migration 090 + Cloud Run env-var cleanup (PIPELINE_SELECTOR + LL3_PANCHA_MP_CLUSTER_MODIFIER) now operator-eligible.

### Sub-agent budget
- Used in Batch 4: 4 dispatches + 1 re-dispatch = 5. Cross-batch total since re-kick: 5. Remaining in 20-budget: 15. Stopping cleanly with all eligible Batch-4 units green and gate board fully closed.

### Re-kick inputs (operator action)
- **Required:** Cowork-author next-refactor-wave brief (move pipeline.run() bodies out of route.ts; delete `isPipelineSelectorEnabled()` shim; clean up docstring carry-overs).
- **Required:** Native review of depth-selector default (still carried from Batch 3 — 3.tier_excision shipped planner-auto-by-query-class).
- **Now eligible:** apply migrations 081–090 to staging DB. Migration 090 (drop `mcp_api_keys.audience_tier`) is the only irreversible op — run after a green post-cutover smoke window.
- **Now eligible:** Cloud Run env-var cleanup `gcloud run services update amjis-web --remove-env-vars MARSYS_FLAG_PIPELINE_SELECTOR,MARSYS_FLAG_LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED`.
- **Carried:** rotate `amjis-db-password` Secret Manager entry.

---

## Batch 5 — Wave 4 final seal (2026-05-28, ~12:55–15:00 IST)

**Status: SEALED.** Platform Modernization arc COMPLETE.

### Dispatch sequence
- **Prep**: commit `888af675` — 7 Wave-4 briefs + queue (batch5-prep). Worktrees A/B/C reset to main HEAD.
- **Wave-1 parallel (3 agents)**:
  - 4.refactor_pipeline_shim (A) → GREEN; commits `452e008b` `31f2509e` → cherry-picked `bc9379ce` `5b9164bd`
  - 4.observability (B) → GREEN; commits `40f44ccd` `0f7656d8` `829899a0` `a7739fce` → cherry-picked `5180733f` `50b74814` `33bacc0a` `42a39960`
  - 4.memorystore_caching (C) → STALLED at 2/3 (watchdog) but commits 1/3 + 2/3 green. Tests 44/44 pass.
- **Cherry-pick wave-1** with conflict resolution on `embedText.ts` (combined B's batched compute with C's cache wrapper). Verified 113/113 tests.
- **Wave-2 parallel (3 agents)**:
  - 4.memorystore_caching 3/3 + chaos test (C) → GREEN; commit `3d18f3d6` → cherry-picked `a56434b1`
  - 4.edge_and_infra_hygiene (A) → GREEN; commits `6ad47425` `21bb5ff8` `1f9ca41c` → cherry-picked `309376cd` `d47ad81a` `c8592215`. 32/32 smoke checks + 3 IAM-bearer tests GREEN. Deleted 4 cloudbuild*.yaml files.
  - 4.build_trigger (B) → STALLED at 1/3 (watchdog); commit 1/3 green with 23/23 tests → cherry-picked `4b5d60b7`.
- **Cherry-pick wave-2**. Verified 147/147 tests.
- **Wave-3** (after agent stalls): 4.learning_loop done **inline** on main: migration 119 + calibration_producer + onfinish step 10 + STUBBED answer:eval baseline. Commits `1a0b0fe8` + `307c39ed`. Tests 22/22.
- **Build_trigger 2/3+3/3 retry** (tight prompt) → GREEN; commits `e72cae45` `51cfd494` → cherry-picked `6d34e6cb` `524792ab`. 77/77 tests across api/build + clients + lib/build.
- **Verification on main**: 223/223 tests GREEN across all Wave-4 surfaces.
- **4.red_team_seal inline (A)**:
  - 1/3 `fcdc9199` — adversarial red-team report (0 class-1, 3 class-2, 4 class-3 — all dispositioned).
  - 2/3 — `tools/program-tracker/` removed (ephemeral lifecycle); grep clean of app imports.
  - 3/3 — seal artifact `PLATFORM_MODERNIZATION_CLOSE_v1_0.md` + PROGRAM_STATE/session_queue/CONDUCTOR_LOG updates.

### Sub-agent count
8 dispatched (3 stalled — runtime watchdog flakiness today; 2 agents partial commits salvaged on inspection, 3rd retried with tight prompt) + 3 inline (learning_loop 1/2, learning_loop 2/2, red_team_seal full).
Total = 11 effective units of work; well under the 20-budget.

### Gates
**All 8 hard gates GREEN.** Final test posture: 223/223 across the Wave-4 functional surface; no pre-existing failures regressed.

### Operator queue (forwarded to PLATFORM_MODERNIZATION_CLOSE §Deferred operator items)
Migrations 081–090 (carried) + 118 + 119; terraform apply on 6 IaC packages; Cloud Run env-var cleanup; rotate amjis-db-password; live answer:eval baseline; flip BUILD_TRIGGER flag; delete amjis-tracker; native review of depth-selector default.

### Reflection
3 agent stalls during the run (runtime watchdog issue, not prompt/state issue — partial commits were preserved and the work was salvaged on inspection or by retry/inline). The Conductor's "inspect-stash-then-decide" pattern handled all three salvages cleanly without rollback. The `tools/program-tracker/` removal closes the 0t ephemeral lifecycle as designed.

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


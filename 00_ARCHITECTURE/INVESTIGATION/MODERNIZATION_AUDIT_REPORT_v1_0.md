---
artifact: MODERNIZATION_AUDIT_REPORT_v1_0.md
document: Audit of PLATFORM_MODERNIZATION_MASTER_PLAN v2.0 against main HEAD
status: COMPLETE (read-only verification pass — no code/plan edits made)
version: 1.0
date: 2026-05-27
audit_target: 00_ARCHITECTURE/PLATFORM_MODERNIZATION_MASTER_PLAN_v2_0.md
audited_by: Antigravity
mode: read-only forensic; verify-don't-trust; cite path:line
git_state:
  branch: main
  head_sha: 367ee47ccc25eea3d92b32b84296991d5aec2d51
  dirty: false (only untracked governance briefs / new docs)
  recent_commits:
    - "367ee47c fix(chart-snapshot): rebuild planetary table + karakas from FORENSIC v8.0"
    - "faea77cf fix(data): correct PLN.MARS.DIGNITY.D1 debilitated→enemy + cascade fixes"
    - "b7ff36f1 governance(mcp-rem-close): MCP Tool Audit v2 COMPLETE — 40/40 tools 100%"
---

# §0 — Executive Summary

The Platform Modernization Master Plan v2.0 is, on balance, **a sound program** — its high-stakes claims about code state are overwhelmingly correct, often to the exact line. But it under-states severity in five places (tenant-key drift, hidden judgment-time gates beyond floors, dual deploy path scope, "L2 archived" vs. live L2 references, and python-sidecar's actual capability), under-cites in another (peer files for §6-A live in `platform-mcp/`, not `platform/src/lib/retrieve/`), and contains **two path-drift errors in the constituent_plans frontmatter** that will break automated tooling on day one. There is one **must-fix-before-implementation** ambiguity: the plan's "JH parity gate" (hard-gate G1) blocks builds until the engine matches FORENSIC v8.0 — but FORENSIC v8.0 itself depends on JH v8.0 for §12.1, §12.2, §6.6–§6.8, §26 (per its own frontmatter `dual_engine_policy`). The plan does not specify the JH-side parity oracle when JH itself is the standard.

### Top findings (confidence-ranked)

1. **CONFIRMED (high impact, exact)** — De-judgment floors live exactly where claimed: `platform/src/lib/retrieve/msr_sql.ts:20,24,33,44`. The plan's most important load-bearing technical claim is precise.
2. **CONFIRMED (exact line)** — B.11 citation gate is on the legacy path only at `consume/route.ts:1374`. Adapter branch (`:923–:1198`) has zero `validateCitationsForStream` calls. G5 hard gate is justified.
3. **CONFIRMED (exact line)** — Per-chart Firebase user at `api/clients/route.ts:51,57`. §6-H precise.
4. **PARTIALLY-CORRECT (under-stated)** — Tenant-key drift is worse than §3.2 conveys: TWO live `NATIVE_CHART_ID` values (`'abhisek_mohanty_primary'` text in 4 files; `'362f9f17-95a5-490b-a5a7-027d3e0efda0'` UUID in 2 files). Same constant name, two values, two semantics. The data plane has `chart_id uuid` in migration 001 and `chart_id TEXT` in 022/024/025/031/033 — both live.
5. **WRONG (path)** — §6-A cites `query_signals.ts` and `query_varshphal.ts:87` as in `platform/src/lib/retrieve/`. They do **not** exist there; they live in `platform-mcp/src/tools/`. The portal counterpart is spelled `query_varshaphala.ts` (the same name-split §3.3 documents). The judgment logic at the cited line 87 is in fact a **hard-403 tier gate**, not a "redaction" — it returns Forbidden when `audience_tier === 'client'`. Plan language conflates two distinct gate categories.
6. **WRONG (path drift)** — constituent_plans frontmatter cites `00_ARCHITECTURE/BRIEFS/FACT_ENGINE_PYJHORA_BRIEF_v1_0.md`; actual location is `00_ARCHITECTURE/FACT_ENGINE_PYJHORA_BRIEF_v1_0.md` (no `BRIEFS/` prefix). §2.1 corrects the v1.0 TOOL_PORTFOLIO path but **misses this twin error**. v1.0 has the same drift uncorrected.
7. **CONFIRMED (under-stated)** — Dual deploy paths exist: 6 GitHub Actions workflows + 4 separate `cloudbuild.yaml` files at repo-root, `platform/`, `platform/` (sidecar), and `platform-mcp/`. R11 + §4.2-7 are justified.
8. **CONFIRMED** — `amjis-mcp` is deployed with `--allow-unauthenticated` at `platform-mcp/cloudbuild.yaml:56`. §4.1 / R10 precise.
9. **WRONG (deletion-list error)** — §6-F says "L2 already archived — only L1+L1.5 fold + dir renumber remain". But `api/clients/route.ts:82–83` still scaffolds `L2` sublayer rows (`analysis_mode_a`/`analysis_mode_b`) at chart-create time. L2 is archived as canonical *artifacts* (`99_ARCHIVE/02_ANALYTICAL_LAYER/` exists) but L2 is **not** archived as code: `pyramid_layers` rows still get created. §6-F is half-right; live L2 references remain.
10. **PARTIALLY-CORRECT** — §6-D claim "all 79 retrieval_tool manifest entries have query_schema=null" (from REALITY_REPORT) is over-broad. 9 entries DO carry a non-null `query_schema` field in `CAPABILITY_MANIFEST.json` (lines 1253, 2645, 2682, 2747, 2781, 2819, 2852, 2918, 2968); the remaining 70+ have **no `query_schema` field at all** (absent, not null). The corrective action is the same (populate), but the diagnostic phrasing is loose.

### MUST-RESOLVE-BEFORE-IMPLEMENTATION (prioritized)

| # | Item | Why blocking |
|---|---|---|
| 1 | **JH parity gate oracle** (§7, G1): FORENSIC v8.0 explicitly cites JH v8.0 as authoritative for §12.1, §12.2, §6.6–§6.8, §26 (per FORENSIC frontmatter). The gate cannot be "match FORENSIC" alone where FORENSIC defers to JH. Decide: (a) accept JH-as-oracle and pin a JH binary/version; (b) re-author FORENSIC sections to be engine-independent; (c) restrict G1 to the FORENSIC-primary sections only. | Wave 1 cannot close without a deterministic, re-runnable parity test. |
| 2 | **§9 item 14 RESOLVED but §6-G ordering still ambiguous.** B.11 gate must port to adapter path before legacy delete. Plan agrees. But §7 Wave 0 lists "B.11 adapter-path hotfix" while Wave 3 lists "legacy-pipeline delete (after B.11 ported)". The plan doesn't say where the **adapter onFinish parity** (§6-B claim "synthesisRequest 863-907 legacy-only" + the `tokensFor`/`tokensForAdapter` duplicate budget tables at :1418/:1139) lives in the cutover. Without parity tests covering observatory/perf/persistence stages, deleting `synthesisRequest` will silently drop telemetry/persistence rows. | G5 is necessary but insufficient — needs a sibling gate G5b: "adapter `onFinish` reaches parity with legacy `onFinish` (write-through persistence, predictions, observatory) by golden-transcript test." |
| 3 | **§3.2 tenant-key normalization assumes a single rename batch can flip `chart_id TEXT → uuid`.** It cannot: live data uses `'abhisek_mohanty_primary'` literal (text) as the chart key across 6+ tables, and a parallel uuid `362f9f17-95a5-490b-a5a7-027d3e0efda0` lives in muhurta + shashtiamsha test fixtures. The migration path needs a join table (chart_text_key ↔ chart_uuid) and a deterministic mapping migration, not a column-type alter. | Wave 2 schema migration cannot be authored without that mapping. |
| 4 | **§12 class C ("date-parameterized derivations") enumeration is the explicit Track-1 deliverable but is not given anywhere in v2.0.** Without that enumeration, the DAG cannot be specified, and Wave 1 cannot close. | Explicit blocker on §12 sentence "investigation deliverable for Track 1: a complete enumeration of class C." |
| 5 | **§4.2-1 build-trigger wiring** depends on the Cloud Run Job `marsys-build-pipeline-job` existing AND having an in-app trigger. The Job's Dockerfile lives at `platform/python-sidecar/Dockerfile.pipeline` (see §10 below), but no `marsys-build-pipeline-job` resource was grep-able in cloudbuild/deploy.yml — only `amjis-sidecar` and `amjis-mcp` Cloud Run *services* are deployed by CI. The Job either does not exist as configured infrastructure or exists only manually-created. **Decide & document its current state before §4.2-1 enters scope.** | §4.2-1 cannot proceed if its precondition is unverified. |
| 6 | **§11.1 retires Mirror Discipline + `.geminirules` + `project_state.md` + `mirror_enforcer.py`** — but those surfaces are referenced multiple times in CLAUDE.md §K and in the active session-open template. The retirement is sound (Gemini inactive per §9 item 16 RESOLVED), but the actual deletes cascade into CLAUDE.md §C item 11 (and §K), `GOVERNANCE_INTEGRITY_PROTOCOL §K.3`, `CANONICAL_ARTIFACTS §2`, and `NATIVE_DIRECTIVES §1 ND.1`. Without a single PR to fix all five surfaces together, the retirement will land as half-state and `drift_detector.py` will fail on the next pass. | Wave 0 program-wrapper task; size correctly. |
| 7 | **Naming-governance CI (§3.7) names "the unified contract" as the SSOT, but the contract does not exist yet** (gateway tools `search_tools`/`invoke_tool` — confirmed absent by grep). The CI gate cannot enforce "tool name not in unified contract" until the contract ships. Sequencing: §3.7 CI rule (c)+(d) cannot enter Wave 0; must move to Wave 3. | Mis-sequenced gate. |
| 8 | **§6-I "`retrieval_capability_spec.ts` does not exist — drop from delete list"** is correct, but does NOT remove all phantom items in v2.0's elimination list (see §9 below — three other items have residue). | Elimination list needs a second pass before any deletes execute. |

Overall soundness verdict: **APPROVE WITH CONDITIONS.** Address the 8 items above and the plan is implementable. The architectural picture (determinism seam, computed-coefficient salience, strangler/parallel cutover, four-class asset taxonomy, the JH-equivalent engine + serve-time panel split) is internally coherent and matches code state.

---

# §1 — Claim-Verification Matrix

Format: | Plan ref | Claim | Evidence (path:line) | Verdict | Note |

| Plan ref | Claim | Evidence | Verdict | Note |
|---|---|---|---|---|
| §0 thesis | "deterministic, JH-equivalent compute engine builds every per-chart asset narrative-free" | `platform/python-sidecar/routers/` has ephemeris/jaimini/panchang/muhurat/sade_sati/transit_search/v7_additions/dasha_chain/retrogrades/eclipses; no full natal engine | PARTIALLY-CORRECT | Sidecar today is NOT a JH-equivalent natal engine; it computes date-parameterized derivations (class C in §12 terms). Wave 1 must *build* what is described, not refactor what exists. |
| §1 v2 delta | "v1.0 is the reconciliation spine (...kept and referenced, not restated)" | `PLATFORM_MODERNIZATION_MASTER_PLAN_v1_0.md:1–14` exists and contains the five-track spine | CONFIRMED | v1.0 has its own path-drift errors (TOOL_PORTFOLIO_PLAN_v1_4 path) that §2.1 catches; FACT_ENGINE path drift uncaught in both. |
| §2 architecture | "single coherent picture: INPUT → chart_id → engine → JSONL → additively-extended chart-keyed stores → unified de-judged retrieval → serve-time panel+judge" | (architectural) | UNVERIFIABLE-ARCHITECTURAL | Description is a design statement; verifying requires test the design isn't built. |
| §2.1 (v1.4 path) | "TOOL_PORTFOLIO_PLAN_v1_4 lives at 00_ARCHITECTURE/BRIEFS/" | `00_ARCHITECTURE/BRIEFS/TOOL_PORTFOLIO_PLAN_v1_4.md` exists; `00_ARCHITECTURE/TOOL_PORTFOLIO_PLAN_v1_4.md` does NOT | CONFIRMED | v2.0's §2.1 correction is right. |
| §2.1 (L2 archive) | "L2 is already archived (99_ARCHIVE/02_ANALYTICAL_LAYER/, Phase 14F)" | `99_ARCHIVE/02_ANALYTICAL_LAYER/CLAUDE.md` + MATRIX_* exist | CONFIRMED (artifacts) BUT WRONG (code) | See §6-F deeper finding: `api/clients/route.ts:82–83` still creates `L2.analysis_mode_a` + `L2.analysis_mode_b` pyramid_layer rows. L2 is archived as docs, not as live code. |
| §2.1 (TierPicker) | "Deep/Study/Brief depth selector IS the tier picker; maps onto super_admin/acharya_reviewer/client" | `platform/src/components/consume/TierPicker.tsx:7–26` and `:66–71` show exactly that mapping | CONFIRMED (exact) | Both `TIERS` and `TIER_LABELS` consts confirm the mapping. |
| §2.1 (de-judgment) | "DEFAULT_CONFIDENCE_FLOOR (20), FINANCE_WEALTH_CONFIDENCE_FLOOR (24), PANCHA_MP_CLIQUE (33), LL1_PRODUCTION_WEIGHTS (44)" | `platform/src/lib/retrieve/msr_sql.ts:20,24,33,44` — line numbers exact | CONFIRMED (exact) | Most precise claim in the plan. |
| §2.1 (B.11 asymmetry) | "legacy path has validateCitationsForStream at consume/route.ts:1374; adapter path does not" | `consume/route.ts:1374` confirms exact line; only call site in the file; adapter branch (`:923–:1198`) reviewed, no citation gate | CONFIRMED (exact) | G5 hard gate is justified. |
| §3.1 (product names) | "amjis-=infra; Madhav=brand/project; MARSYS-JIS=system" | (terminology choice — no code dependency) | UNVERIFIABLE-DECISION | Note: `marsys-jis-build-state` GCS bucket exists; rename to `amjis-*` is non-trivial. |
| §3.2 (tenant key drift) | "chart_id uuid / chart_id text / native_id / client_id split across migrations" | migration 001:50 chart_id uuid FK→charts.id; migrations 022:22, 024:13, 025:15, 031:24, 033:17 ALL use `chart_id TEXT`; migration 008:23 adds `native_id VARCHAR(64) NOT NULL DEFAULT 'abhisek'` to 6 tables; migration 009:13 msr_signals uses native_id | CONFIRMED (worse than stated) | Same `chart_id` name, two types, live. Add to risk register. |
| §3.2 (client_id overload) | "`client_id`-as-owner overload" | `api/clients/route.ts:57` `client_id = firebaseUser.uid` (Firebase UID stuffed into client_id) + migration 006 changes profiles.id+charts.client_id to text | CONFIRMED | client_id is a Firebase UID, FK to profiles.id (text). |
| §3.2 (per-chart Firebase user) | "deprecate per-chart Firebase user" | `api/clients/route.ts:51` `adminAuth.createUser` + `:57` `client_id = firebaseUser.uid` | CONFIRMED (exact) | §6-H precise. |
| §3.3 (tool name splits) | "chart_facts_query↔query_chart_facts" | `platform/src/lib/mcp/primitives_registry.ts:96`+ `query_chart_facts: 'chart_facts_query'` | CONFIRMED | |
| §3.3 (tool name splits) | "query_varshaphala↔query_varshphal" | `platform/src/lib/retrieve/query_varshaphala.ts` (portal) + `platform-mcp/src/tools/query_varshphal.ts` (MCP); alias bridge `queryVarshphalAlias` in `retrieve/index.ts` | CONFIRMED | |
| §3.3 (tool name splits) | "divisional_query↔query_divisional_chart" | portal: `query_divisional_chart`-named test exists `divisional_query.test.ts`; mapping in primitives_registry | CONFIRMED | |
| §3.3 (tool name splits) | "cgm_graph_walk↔get_cgm_subgraph" | primitives_registry `get_cgm_subgraph: 'cgm_graph_walk'` | CONFIRMED | |
| §3.3 (tool name splits) | "classical_text_search_tool↔read_classical_text" | primitives_registry `read_classical_text: 'classical_text_search'` (note: portal name is `classical_text_search_tool.ts`, engine name is `classical_text_search`) | PARTIALLY-CORRECT | Three-way split — portal file is `classical_text_search_tool`, engine name `classical_text_search`, MCP name `read_classical_text`. Plan flattens it to 2 names. |
| §3.3 (tool name splits) | "multi_school_signal_lookup_tool↔multi_school_bundle_tool" | portal `multi_school_signal_lookup_tool.ts` exists; MCP has both `multi_school_bundle_tool.ts` AND `cross_school_lookup` (different things) | PARTIALLY-CORRECT | Two distinct MCP tools (`multi_school_bundle` is Tier-2 composite; `cross_school_lookup` is Tier-3 primitive); plan implies a one-to-one mapping where there is a 2:1. |
| §3.3 (msr_sql + *_balam dups) | "duplicate surfaces msr_sql+query_signals and *_balam+*_for_native pairs" | `RETRIEVAL_TOOLS` array in `retrieve/index.ts:151–212` includes `taraBalamForNative.tool`, `chandraBalamForNative.tool` AND `queryTaraBalam.tool`, `queryChandraBalam.tool` (R2-S1/S2 canonical-name aliases) | CONFIRMED | Both pairs live in the same array. |
| §3.4 (flag convention) | "Convention: MARSYS_FLAG_<DOMAIN>_<FEATURE>; retire R9_/R10_/R11_ prefixes" | `consume/route.ts:923` reads `R11V2_USE_ADAPTERS`; deploy.yml uses both `R11E_*_LOOP` and `MARSYS_FLAG_R11V2_*` | CONFIRMED | Round-prefixes still live. |
| §3.4 (one flag source) | "configService reads runtime_config + env bootstrap; PANEL_MODE_ENABLED, CITATION_GATE_OVERRIDE, VALIDATOR_FAILURE_HALT have no MARSYS_FLAG_ mirror" | not directly verified in this pass — flag list is plausible but exhaustive grep not performed | UNVERIFIABLE | Should be checked before naming-governance CI lands. |
| §3.5 (env vars) | "GOOGLE_CLOUD_* / GCP_* / GOOGLE_* trio; DATABASE_URL dual; chart-id test-var triple" | deploy.yml shows `WIF_PROVIDER` references `projects/938361928218/locations/global/workloadIdentityPools/github` + `madhav-astrology`; multiple naming conventions observed | PARTIALLY-CONFIRMED | Triple-prefix claim plausible but a full env-var audit was out of scope. |
| §3.6 (layer model) | "L0 / L1 / L2 retired / L2.5 / L3 / L4 / L5 / L6"; canonical set | `CAPABILITY_MANIFEST.json` has entries marked `"layer": "L1"` (FORENSIC, LEL); other layer values exist; manifest doesn't carry an L# enumeration | PARTIALLY-CONFIRMED | The proposal is sensible; no current SSOT for layer labels exists — three different surfaces use different vocabularies. |
| §3.7 (consult rename) | "consume → consult" | `platform/src/app/api/chat/consume/route.ts` is the live route | CONFIRMED-AS-NEEDED | Plan correctly identifies. |
| §3.7 (duplicate panchang dirs) | "Merge /api/panchang + /api/panchanga" | `platform/src/app/api/panchang/{charts,feed,feed.ics,ics}` AND `platform/src/app/api/panchanga/route.ts` both exist | CONFIRMED (exact) | |
| §3.7 (path drift TOOL_PORTFOLIO) | "TOOL_PORTFOLIO_PLAN under BRIEFS/" | confirmed (see §2.1 row) | CONFIRMED | But plan misses the twin error: FACT_ENGINE_PYJHORA_BRIEF is **not** under BRIEFS/ — it's at `00_ARCHITECTURE/FACT_ENGINE_PYJHORA_BRIEF_v1_0.md`. v2.0 frontmatter `constituent_plans.data_engine` cites the wrong path. |
| §3.7 (CI gate) | "naming-governance CI gate (drift_detector/schema_validator-extension)" | `drift_detector.py` and `schema_validator.py` referenced in CLAUDE.md; existence not directly verified in this pass | UNVERIFIABLE-IN-SCOPE | Plan is sound; implementability depends on extending existing tooling. |
| §4.1 (Cloud Run services) | "amjis-web, amjis-sidecar, amjis-mcp" | `.github/workflows/deploy.yml:106` PYTHON_SIDECAR_URL=amjis-sidecar; `:159–167` builds+deploys `amjis-sidecar`; `platform-mcp/cloudbuild.yaml` builds+deploys `amjis-mcp`; deploy.yml builds `amjis-web` | CONFIRMED | All three services confirmed. |
| §4.1 (Cloud Run Job marsys-build-pipeline-job) | "Cloud Run Job marsys-build-pipeline-job (the build DAG — no in-app trigger, run manually)" | `platform/python-sidecar/Dockerfile.pipeline` exists; no grep hit for `marsys-build-pipeline-job` in any cloudbuild/deploy file | PARTIALLY-CORRECT / UNVERIFIABLE | The Dockerfile.pipeline exists, but I could not confirm via CI/IaC that the Job is provisioned. Either the Job exists out-of-band (manually `gcloud` deployed) or it doesn't exist; in either case, §4.2-1 has a precondition gap. |
| §4.1 (CI dual deploy) | "GitHub Actions via WIF + Cloud Build configs (dual path → drift risk)" | `.github/workflows/deploy.yml` (WIF) + 4 cloudbuild.yaml (root, platform/, platform/sidecar, platform-mcp/) — confirmed | CONFIRMED (exact) | R11 justified. |
| §4.1 (Cloud SQL tier) | "db-g1-small (dev tier)" | grep hits only in PLAN, SESSION_LOG, A2_gcp_services.md audit, archive script; not in deploy/cloudbuild | UNVERIFIABLE-from-code | Tier is declared in plan-side audit; needs gcloud verification before §4.2-2 enters scope. |
| §4.1 (MCP unauthenticated) | "amjis-mcp public via --allow-unauthenticated" | `platform-mcp/cloudbuild.yaml:56` `--allow-unauthenticated` | CONFIRMED (exact) | R10 + §4.2-4 justified. |
| §4.1 (Cloud Scheduler comment-only) | "Cloud Scheduler only in comments" | only references found in `.github/workflows/chat-v2-ci.yml:512,515,522` as NOTE comments and node_modules residue | CONFIRMED | §4.2-8 codify-as-IaC is sound. |
| §4.1 (hardcoded DB passwords) | "hardcoded DB passwords in dev scripts" | grep for `password=` / `PGPASSWORD=` in `scripts/` and `platform/scripts/` found no obvious literal passwords (most via `process.env`/`os.environ`); `99_ARCHIVE/scripts/gcp_migrate.sh` referenced | PARTIALLY-CORRECT / UNVERIFIABLE | If the claim is real, evidence path must be supplied in the plan body. My grep returned nothing actionable. Move to OPEN-VERIFICATION list before §4.2-6 lands. |
| §4.2-1 (Cloud Task/Pub-Sub) | "amjis-web enqueues task → Job → cockpit polls" | no Cloud Task / Pub/Sub usage found in `platform/src/`; described as future work | CONFIRMED-AS-FUTURE | Gap-to-build, not present. |
| §4.2-3 (Memorystore) | "no Memorystore today, only process-local 60s caches" | confirmed by absence of redis/memorystore client in `platform/package.json` (not directly inspected this pass but consistent with plan) | UNVERIFIABLE-CONSISTENT | |
| §4.2-9 (observability) | "no Cloud Trace across web→sidecar→mcp" | confirmed by absence in deploy.yml + cloudbuild + main.py | CONFIRMED | |
| §5.1 (QueryContext lib) | "no single QueryContext{principal, chart_id} thread" | The `Principal` type exists in `platform-mcp/src/types.ts` and is passed via `getPrincipal()` closure (server.ts:165); a unified, cross-channel `QueryContext` does not exist | CONFIRMED | Gap-to-build identified correctly. |
| §5.2 (Command Center) | "gate_registry + runtime_config + configService extension; LEL build-exclusion serve-time boundary" | `configService.getFlag(...)` is in use at `consume/route.ts:923,955,971`; gate registry not directly found | CONFIRMED-DESIGN | Half-built: configService is the substrate, but the gate registry pattern is a gap. |
| §5.3 (B.11 on adapter path) | (hotfix) | same as §2.1 row | CONFIRMED | |
| §5.4 (build trigger wiring) | (gap) | same as §4.1 marsys-build-pipeline-job row | CONFIRMED-GAP | |
| §5.5 (intake determinism) | "geocoding + historical-timezone pinned at intake" | `api/clients/route.ts:39–47` accepts `birth_lat/birth_lng/birth_place` as freeform body fields with no geocoder pin or historical TZ derivation; no provenance record on insert | CONFIRMED (gap is real) | High-priority since `dasha_periods.computed_by='pyswisseph'` is the *only* recorded provenance. |
| §6-A | de-judgment | (already verified) | CONFIRMED | |
| §6-B (legacy synthesis trio) | "orchestrator.ts/single_model_strategy.ts/panel_strategy.ts" | `platform/src/lib/synthesis/` lists all three + agentic_loop.ts + b11_guard.ts + citation_check.ts + history_compression.ts + mcp_tool_executor.ts + prompt_assembler.ts + provider_quirks.ts + streaming_citation_validator.ts + thinking_config.ts + token_caps.ts + types.ts | CONFIRMED | Note: panel_strategy.ts is single-file legacy; a separate `panel/` directory also exists (active panel implementation). Distinguishing them in §6-B is missing. |
| §6-B (/api/mcp/execute) | "deletion candidate" | `platform/src/app/api/mcp/execute/route.ts` directory exists | CONFIRMED-AS-EXISTS | The plan should specify whether it's safe to delete given `platform-mcp/src/client.ts:13` claims callPlatform routes ask_madhav/execute_plan through it. |
| §6-B (callPlatform/Plan) | "client.ts:145/165" | `platform-mcp/src/client.ts:145` `callPlatform`, `:165` `callPlatformPlan`, `:189` `callPlatformPrimitive`, `:211` `callPlatformAsset`, `:232` `callPlatformTrace` | CONFIRMED (exact) | Note: only callPlatform + callPlatformPlan are deletion candidates per §6-B; the others (Primitive/Asset/Trace) are load-bearing. |
| §6-C (lib/disclosure/) | "tier/disclosure subsystem to eliminate" | `platform/src/lib/disclosure/{index.ts,types.ts,__tests__/}` exists; index.ts shows that for `client` and `public_redacted` tiers, the filtering is TODO (no actual redaction implemented); `acharya_reviewer` only prepends preamble | CONFIRMED but UNDERSTATED | The "tier subsystem" is mostly stub today — most filtering is "TODO M6/M10". Removing it now is plausible, but the plan should record what's *actually* in disclosure/index.ts so the deletion isn't a surprise. |
| §6-C (X-MCP-Audience-Tier client.ts:109/142/248/326) | line refs | `platform-mcp/src/client.ts` calls referenced; line numbers approximate but not exhaustively verified | PARTIALLY-CORRECT | Header use confirmed across `/api/mcp/health/tools`, `/health/coverage`, `/api/mcp/recent`, `/api/mcp/asset`, `/api/mcp/primitives/[tool]`, `/api/mcp/writes/[action]`, `/api/mcp/trace/[trace_id]`, `/api/mcp/bundles/[name]`. |
| §6-C (mcp_api_keys.audience_tier migrations 070/117) | "mig 070/117" | `platform/supabase/migrations/070_mcp_api_keys.sql` exists; `platform/migrations/117_audience_tier_acharya_enum.sql` exists | CONFIRMED | Note: 070 lives in `supabase/migrations/` (with a *colliding* `070_capability_tool_registry.sql` in the same dir) — not in `platform/migrations/`. Duplicate numbering needs to be called out as a sub-finding. |
| §6-C (tier_catalog.ts) | "to eliminate" | `platform-mcp/src/tools/tier_catalog.ts` exists; used by `server.ts:106,172` for description variation per tier | CONFIRMED | But: server.ts:230 comment says "All ops tools registered unconditionally — native is super_admin of his own instrument." So most tier *gating* is already gone — tier_catalog is now only description variation. |
| §6-C (hard-403 health gates) | "to eliminate" | `platform/src/app/api/mcp/health/tools/route.ts:34` + `health/coverage/route.ts:22` read `X-MCP-Audience-Tier` from headers (gates exist) | CONFIRMED | |
| §6-C (DisclosureTierBadge.tsx) | "to eliminate" | `platform/src/components/disclosure/DisclosureTierBadge.tsx` exists | CONFIRMED | |
| §6-C (public_redacted.md) | "to eliminate" | `platform-mcp/src/resources/house_rules_variants/public_redacted.md` exists | CONFIRMED | |
| §6-D (MCP_TO_RETRIEVAL_TOOL aliases, line 96) | path `primitives_registry.ts:96` | actual file: `platform/src/lib/mcp/primitives_registry.ts`; `MCP_TO_RETRIEVAL_TOOL` defined at line **92** (close enough; line drift ≤4) | PARTIALLY-CORRECT | Plan cites line 96; actual is 92. The path is right; the file is at `platform/src/lib/mcp/`, not `platform-mcp/` (which the plan's brevity might mislead a reader into thinking). |
| §6-D (SURGICAL_TOOLS 32 dups at :46) | line 46 | `primitives_registry.ts:46` is `SURGICAL_TOOLS = [` — exact match | CONFIRMED (exact) | REALITY_REPORT §10 confirms 32 of 42 entries duplicated (msr_sql appears 4×). |
| §6-D (retrieve/index.ts:151-212 inline aliases) | "inline name-bridge objects" | `retrieve/index.ts:151` `export const RETRIEVAL_TOOLS: RetrievalTool[] = [` array body extends to ~212; contains `chartFactsQueryAlias` + `queryVarshphalAlias` at the bottom | CONFIRMED (line range correct; description PARTIALLY-CORRECT) | The 151–212 range is the RETRIEVAL_TOOLS array body; not pure name-bridge objects — most entries are real `.tool` references. Two aliases ride at the tail. |
| §6-D (tokensFor/tokensForAdapter) | "duplicated budget tables in route.ts" | `consume/route.ts:1418` (tokensFor — legacy), `:1139` (tokensForAdapter) | CONFIRMED (exact) | Plan-class evidence. |
| §6-E (TierPicker as Brief/Study/Deep) | "= depth-selector ⇒ goes with tier excision" | (already verified) | CONFIRMED | One of v2.0's better connections: removing tiers and removing the depth selector are the same act. |
| §6-E (CONSUME_UI_V2_ENABLED dead branch consume/page.tsx:123) | "dead" | Not directly inspected in this pass; line 123 of `consume/page.tsx` should be checked before delete | UNVERIFIABLE-IN-SCOPE | Add to verification checklist. |
| §6-F (L2 archived) | "only L1+L1.5 fold + dir renumber remain" | `99_ARCHIVE/02_ANALYTICAL_LAYER/` exists (CONFIRMED); but `api/clients/route.ts:82–83` still creates `L2.analysis_mode_a` + `L2.analysis_mode_b` pyramid_layer rows | PARTIALLY-CORRECT (worse than stated) | Live L2 references remain in code; the "fold" is bigger than docs suggest. |
| §6-G (legacy pipeline) | "consume/route.ts else @ ~1201, synthesisRequest 863-907, import :82" | `:862` `createOrchestrator`, `:863` synthesisRequest, `:1201` orchestrator.synthesize, `:82` `import { createOrchestrator }` (line approx — also see :85 `validateCitationsForStream`) | CONFIRMED (line drift ≤2 across all 3 refs) | Most accurate large-claim cluster in the plan. |
| §6-H (Firebase user per chart api/clients/route.ts:51/57) | exact lines | (already verified) | CONFIRMED (exact) | |
| §6-I (stale tests) | "tool_descriptions.test.ts:91 asserts 22 vs 57" | REALITY_REPORT finding #2 confirms `expect(CATALOG).toHaveLength(22)` at line 91; CATALOG has 57 entries | CONFIRMED | |
| §6-I (PRIMARY_TOOL_NAMES, @deprecated resolver.ts:68, assembleTraceLegacy/fetchTraceLegacy) | symbol grep | Not directly inspected; REALITY_REPORT supports the cluster | UNVERIFIABLE-IN-SCOPE / SUPPORTED-BY-CONSTITUENT | |
| §6 note (retrieval_capability_spec.ts) | "does NOT exist as a source file (only a test)" | grep returned no source file | CONFIRMED | Drop from elimination list — already corrected. |
| §7 G1 (JH parity gate) | "nothing above L1 builds until engine reproduces FORENSIC v8.0" | FORENSIC frontmatter: `dual_engine_policy: "...JH is authoritative for §12.1, §12.2, §6.6–§6.8, §26."` | PARTIALLY-CORRECT (load-bearing risk) | Gate is sound but ambiguous where FORENSIC defers to JH. See MUST-RESOLVE #1. |
| §7 G2 (multi-tenant authz before tier excision) | sequencing | `authorizeChartAccess` not currently a unified function; tier checks scattered (server.ts, query_varshphal.ts, api/clients/route.ts, lib/disclosure/) | CONFIRMED-AS-SEQUENCING | Sound. |
| §7 G3 (contract unification before de-judgment) | sequencing | unified contract does not exist yet; floors are live | CONFIRMED-AS-SEQUENCING | Sound. |
| §7 G4 (chart_id-keyed before NATIVE_CHART_ID fallback removed) | sequencing | NATIVE_CHART_ID literal in 4 production files + 2 test files + UUID variant in 2 more files | CONFIRMED-AS-SEQUENCING (critical) | The plan's gate is necessary; the size of the fallback set is larger than implied. |
| §7 G5 (B.11 ported before legacy delete) | sequencing | (already verified) | CONFIRMED | |
| §7 Wave 0 (parallel-safe) | "Wave 0 — tooling hygiene + B.11 + naming-taxonomy + GCP-consolidation + secrets" | mix of pure renames and behavior-altering work in one wave; B.11 port is behavior-altering (it adds a gate to a path) | PARTIALLY-CORRECT | "B.11 hotfix" is not parallel-safe with "naming-taxonomy refactor" — name renames can mask citation-gate test failures. Recommend B.11 hotfix as a *gating sub-wave* inside Wave 0. |
| §7 Wave 1 (engine gate) | "PyJHora engine + adapter + JH parity gate" | gate is sound; adapter shape is unspecified in v2.0 | CONFIRMED-AS-SCOPE | But the FACT_ENGINE_PYJHORA_BRIEF lives at the wrong path per constituent_plans frontmatter — fix before brief opens. |
| §7 Wave 2 (parallel a/b/c/d) | (a) L1→L2.5 build; (b) contract unification + chart_id in contract; (c) charts registry + owner/subject + authorizeChartAccess; (d) Command Center scaffold | (a) and (c) share a dependency on §3.2 tenant-key normalization completing — they cannot be truly parallel-safe if both are touching `charts` table | PARTIALLY-CORRECT | Hidden dependency: (a) and (c) both write to charts/owner/subject; sequencing or strict file-fence required. |
| §7 Wave 3 (sequenced) | de-judgment → gateway+control-model-B+pipeline isolation → per-chart cutover → portal Consult/nav → tier excision → legacy-pipeline delete | ordering reasonable | CONFIRMED-AS-ORDERING | But "gateway" doesn't exist yet (`search_tools`/`invoke_tool` not present) — this is a build, not a refactor. |
| §7 Wave 4 (GCP + close) | "build-trigger wiring + Cloud SQL upgrade + Memorystore + CDN + observability; eval re-baseline; learning-loop wiring; red-team + macro-phase seal" | (architectural) | CONFIRMED-AS-SCOPE | |
| §8 R1–R8 (carried from v1.0) | (risks) | (architectural) | UNVERIFIABLE-IN-SCOPE | |
| §8 R9 (naming blast radius) | "tenant-key + tool-name renames touch many surfaces" | NATIVE_CHART_ID alone: 4 production + 2 test files = 6 surfaces in TS; plus ~16 literal 'abhisek_mohanty_primary' in code + 100+ in SQL fixtures (migration seed inserts) | CONFIRMED (worse than stated) | |
| §8 R10 (security debt) | "hardcoded DB passwords; amjis-mcp public; live Anthropic vs cost-ban" | amjis-mcp public CONFIRMED; hardcoded passwords UNVERIFIABLE; live Anthropic from deploy.yml env-var presence (not directly inspected) | PARTIALLY-CORRECT | |
| §8 R11 (deploy-path drift) | "GH Actions + Cloud Build both present" | confirmed: 6 GHA workflows + 4 cloudbuild.yaml | CONFIRMED | |
| §11.1 (retire mirror discipline) | "Gemini collaboration no longer active — remove mirror enforcers + .geminirules + project_state.md" | architectural decision; cascades to CLAUDE.md, GOVERNANCE_INTEGRITY_PROTOCOL §K, CANONICAL_ARTIFACTS §2, NATIVE_DIRECTIVES §1 | CONFIRMED-AS-DECISION (needs cascade) | See MUST-RESOLVE #6. |
| §12 (asset taxonomy) | "Class A shared, Class B per-chart natal, Class C per-chart date-parameterized, Class D LEL serve-time only" | sensible architectural classification | CONFIRMED-AS-DESIGN | Class C enumeration is the explicit deliverable — see MUST-RESOLVE #4. |
| §12 (LEL never engine-built) | "class D — never engine-built, never in build/churn, serve-time-only" | grep for `life_event` in build/pipeline/scripts paths returned no consumers; LEL is read at serve time via `lel_query` retrieval tool | CONFIRMED | |
| §13 (MCP client perspective) | "small prompt-cache-stable resident core + gateway; real input schemas; LLM-tuned names; de-judged structured results; bundles+prompts; auto-loaded resources; forced B.11-first; explicit chart_id; determinism/idempotency; operator observability" | design criteria; gateway absent today (CONFIRMED); auto-loaded resources exist (`platform-mcp/src/resources/`); B.11 NOT forced (asymmetric); chart_id NOT required everywhere (NATIVE_CHART_ID default) | CONFIRMED-AS-GAP-LIST | Implementation gap matches the plan. |
| §14 (panchang component) | "carve-out as class-C module; bounded; one UI + one retrieval tool; consolidate /api/panchang + /api/panchanga" | duplicate trees confirmed; carve-out is a build, not refactor | CONFIRMED-AS-SCOPE | |
| §9 item 17 (MCP client expectations) | OPEN | (no code dependency) | CONFIRMED-AS-OPEN | Genuine open question; cannot be code-verified. |

---

# §2 — Conflict Matrix

### §2A — Plan vs. code

| Conflict | Source A | Source B | Evidence | Severity | Resolution |
|---|---|---|---|---|---|
| **L2 archival** | Plan §6-F "L2 archived; only L1+L1.5 fold + dir renumber remain" | `api/clients/route.ts:82–83` still creates `L2.analysis_mode_a` + `L2.analysis_mode_b` pyramid_layer rows on chart-create | code | MEDIUM | Add explicit task to §6-F: "delete L2 sublayer creation in clients POST after the fold." |
| **De-judgment file paths** | Plan §6-A cites `query_signals.ts` and `query_varshphal.ts:87` as in `platform/src/lib/retrieve/` | Actual: those files live in `platform-mcp/src/tools/`. The portal counterpart is `query_varshaphala.ts` | code grep | MEDIUM | Correct paths; clarify the dual-channel implication. |
| **"redaction" at query_varshphal.ts:87** | Plan §6-A: "redaction" | Code is a HARD-403 tier gate (`audience_tier === 'client'` → Forbidden) | code | MEDIUM | Re-label as "hard-403 tier gate". This is the *same* finding §6-C lists under "hard-403 health gates" — i.e., it's a tier-gate, not a redaction. |
| **MCP_TO_RETRIEVAL_TOOL line drift** | Plan §6-D `primitives_registry.ts:96` | Code: `MCP_TO_RETRIEVAL_TOOL` at `primitives_registry.ts:92` | code | LOW | Fix line number. |
| **NATIVE_CHART_ID singular** | Plan §3.2 "deprecate `chart_id text` (`'abhisek_mohanty_primary'`)" implies one default | Code: TWO concurrent defaults — `'abhisek_mohanty_primary'` (text) AND `'362f9f17-95a5-490b-a5a7-027d3e0efda0'` (UUID) | grep across 4+2 files | HIGH | Plan must enumerate the UUID variant too; migration plan must map between the two. |
| **JH parity gate target** | Plan §7 G1 "engine reproduces FORENSIC v8.0" | FORENSIC frontmatter `dual_engine_policy: "JH is authoritative for §12.1, §12.2, §6.6–§6.8, §26."` | `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` frontmatter | HIGH | Decide which engine is the oracle. See MUST-RESOLVE #1. |
| **manifest query_schema** | Plan §6-D + §13 (via REALITY_REPORT): "all 79 entries have query_schema null" | Code: 9 entries DO have query_schema; rest have no field at all | grep `"query_schema"` in CAPABILITY_MANIFEST.json | LOW | Phrase as "no query_schema in 70+ of 79 retrieval_tool entries" — corrective action unchanged. |
| **L2 sub-strategy** | Plan §6-B "panel_strategy.ts" listed as legacy synthesis trio | `platform/src/lib/synthesis/` has both `panel_strategy.ts` (legacy single-pass panel) AND a separate `panel/` directory (active panel-mode implementation) | dir listing | MEDIUM | Disambiguate — what stays, what goes. |
| **classical_text_search 3-way split** | Plan §3.3 names a 2-way split | Code: `classical_text_search_tool.ts` (portal file), `classical_text_search` (engine name), `read_classical_text` (MCP name) | grep | LOW | Update §3.3 to list all 3 names. |
| **multi_school 2:1 mapping** | Plan §3.3 names `multi_school_signal_lookup_tool ↔ multi_school_bundle_tool` (1:1) | Code: portal `multi_school_signal_lookup_tool` maps to BOTH `multi_school_bundle` (Tier 2 composite) and `cross_school_lookup` (Tier 3 primitive) | server.ts inspection | LOW | Clarify the 2:1 split. |

### §2B — Plan vs. constituent

| Conflict | Source A | Source B | Evidence | Severity | Resolution |
|---|---|---|---|---|---|
| **FACT_ENGINE_PYJHORA path** | v2.0 frontmatter cites `00_ARCHITECTURE/BRIEFS/FACT_ENGINE_PYJHORA_BRIEF_v1_0.md` | Actual file: `00_ARCHITECTURE/FACT_ENGINE_PYJHORA_BRIEF_v1_0.md` | ls | MEDIUM | Fix path in both v1.0 and v2.0 frontmatter. v2.0 §2.1 caught TOOL_PORTFOLIO; missed this. |
| **TOOL_PORTFOLIO_PLAN path (v1.0)** | v1.0 constituent_plans cites `00_ARCHITECTURE/TOOL_PORTFOLIO_PLAN_v1_4.md` | Actual: `00_ARCHITECTURE/BRIEFS/TOOL_PORTFOLIO_PLAN_v1_4.md` | ls | MEDIUM | v2.0 §2.1 already addresses; v1.0 still has stale path. |
| **§6-A: peer files location** | v2.0 §6-A says they're under `platform/src/lib/retrieve/` | Constituent REALITY_REPORT correctly cites `platform-mcp/src/tools/` for `query_signals.ts` and `query_varshphal.ts` | grep | MEDIUM | Re-cite. |
| **REALITY_REPORT "all 79" vs evidence** | REALITY_REPORT §3A column "has_query_schema_in_manifest" lists all-no | Actual: 9 entries have `query_schema` field present | manifest grep | LOW | Update REALITY_REPORT — purely cosmetic but undermines the "all" claim. |
| **§11.1 retire mirror discipline** | v2.0 retires Gemini mirror | CLAUDE.md §K still active; CANONICAL_ARTIFACTS §2 still references MP.1–MP.8 | CLAUDE.md inspection | MEDIUM | Cascade. See MUST-RESOLVE #6. |
| **§12 "investigation deliverable: Class C enumeration"** | Plan says deliverable owned by Track 1 | No constituent currently enumerates Class C | constituent files inspection | HIGH | Author Class C enumeration before Wave 1 opens. |

### §2C — Intra-plan

| Conflict | Where | Detail | Severity | Resolution |
|---|---|---|---|---|
| Wave 0 mix | §7 Wave 0 lists "B.11 adapter-path hotfix" alongside "naming-taxonomy refactor pass (pure renames)" | B.11 hotfix is behavior-altering; renames are not. Mixing risks masking gate-test regressions | MEDIUM | Split Wave 0 into 0a (renames) and 0b (B.11 hotfix + secrets). |
| §3.7 CI gate (c)(d) | "tool name not in unified contract" rule | Unified contract does not exist yet (§13 acceptance) → cannot enter Wave 0 | MEDIUM | Move rules (c)+(d) to Wave 3 once contract ships. |
| §9 item 14 RESOLVED | "parallel-build + validated cutover + freeze-old-as-archive" | sound, but plan doesn't specify what *cutover atomicity* looks like for live SQL tables (chart_facts, l25_*, dasha_periods, etc.) | MEDIUM | Add atomicity protocol (staging→live swap pattern from Phase 4C is precedent). |
| §9 item 17 OPEN | "locate MCP client-expectations conversation" | unresolved | LOW | Surface as Wave 0 deliverable. |

---

# §3 — Gap Matrix

| Gap | Where it bites | Owner track | Severity | What's needed |
|---|---|---|---|---|
| Class-C asset enumeration | §12 build DAG cannot be authored | Track 1 (engine) | HIGH | Catalog every per-chart date-parameterized derivation. |
| JH-side parity oracle when FORENSIC defers to JH | §7 G1 | Track 1 | HIGH | Decide oracle policy; pin JH version + ayanamsha or re-author FORENSIC. |
| QueryContext{principal, chart_id} library | §5.1 — every pipeline rederives | Track 3 | MEDIUM | Build once; thread through portal + MCP + sidecar. |
| Command Center gate registry | §5.2 — runtime_config is half-built | Track 3/4 | MEDIUM | gate_registry + admin UI + LEL build-exclusion serve-time boundary. |
| B.11 on adapter path | §5.3 — single citation gate today | Track 2 | HIGH | Port `validateCitationsForStream` into the adapter onFinish; add golden-transcript test. |
| Build trigger wiring (web → Cloud Task → Job) | §5.4 — Job orphaned | Track 3 | HIGH | Cloud Task/Pub-Sub fan-out + Job dispatcher + cockpit progress poll. |
| Intake determinism (geocoding + historical TZ pin) | §5.5 — multi-tenant blocker | Track 3 | HIGH | At intake: pin lat/lon + IANA TZ + chart_id provenance row. |
| Naming-governance CI | §3.7 — taxonomy drifts back | Track 0 | MEDIUM | Extend drift_detector with name-set checks. |
| Observability + SLOs | §4.2-9 — only cost reconciliation today | Track 0 (GCP) | MEDIUM | Cloud Trace, Monitoring dashboards, SLOs, alerts. |
| Learning-loop wiring (prediction logging at n=1) | §5.8 — calibration substrate | Track 5 | MEDIUM | Wire prediction logging into adapter onFinish (already partially via mcp_predictions migration 071). |
| Adapter `onFinish` parity (persistence + observatory) | §6-G — not in current plan | Track 2 | HIGH | Sibling gate G5b to G5; golden-transcript test. |
| L2 live-code cleanup | §6-F — sublayer rows still created | Track 0 | LOW | Delete `'L2'` sublayer creation in api/clients POST. |
| `marsys-build-pipeline-job` infrastructure provisioning | §4.1 — claimed but not in CI | Track 3 | MEDIUM | Confirm/provision via cloudbuild or Terraform. |
| Cloud SQL tier verification | §4.2-2 precondition | Track 0 | LOW | gcloud verification + record current tier explicitly. |
| Real Anthropic-cost decision | §8 R10 — "live ANTHROPIC_* despite cost-ban" | Track 0 | LOW | Explicit native decision, recorded in plan body. |
| Cloud Scheduler IaC | §4.2-8 — comment-only | Track 0 | LOW | Codify or kill. |
| Public_redacted disclosure (M10 deliverable) | §6-C — tier subsystem mostly stub | Track 5 | LOW | Plan can delete; if a future audience needs redaction, build fresh. |

---

# §4 — Complexity & Roadblock Matrix

| Item | Blast radius | Complexity | Roadblock | Mitigation |
|---|---|---|---|---|
| Tenant-key normalization (chart_id TEXT→uuid + NATIVE_CHART_ID retirement) | 18+ SQL tables, 6+ TS files, 100+ migration seed rows | **H** | Live data has `'abhisek_mohanty_primary'` as the chart key in dasha_periods/kp_sublords/varshaphala/shadbala (all `chart_id TEXT`). Cannot column-alter without re-mapping. | Add a `chart_text_alias` column; populate join; cut over reads first, writes second, drop text last. Strangler. |
| B.11 on adapter path | adapter branch in consume/route.ts + tests | M | Adapter `onFinish` ordering differs from legacy (no orchestrator wrapper) | Wrap adapter result stream with `validateCitationsForStream` before `data-citation` parts emit. Mirror the legacy 1374 site. |
| Legacy pipeline delete | route.ts:82,862–907,1201,1374,1418 + synthesis/orchestrator.ts + single_model_strategy.ts + panel_strategy.ts | M | Adapter `onFinish` parity (persistence, observatory, predictions) | Golden-transcript test BEFORE delete; then delete; then re-run. |
| Unified tool contract + gateway | gateway not present today; all portal+MCP tool sites | H | Designs the canonical name set; both channels switch | Spec the contract first (Wave 2b); implement gateway; rename in one atomic batch; flag-gate. |
| De-judgment | msr_sql.ts:20,24,33,44 + query_signals.ts (MCP):72,73 + query_varshphal.ts:87 tier gate + classical_disclosure_filter.ts | M | Removing PANCHA_MP_CLIQUE dedup changes counts in synthesis tests; LL1_PRODUCTION_WEIGHTS change is calibration-sensitive | Move scoring to L2.5 build (computed coefficient column) per §12; retire query-time floors atomically with golden-transcript test. |
| L2.5 deterministic rebuild | MSR (573 signals), CDLM, CGM (9 versions), RM, UCN — all coefficient-bearing | H | Cited grounding gap (V1_3_AUDIT_QUEUE: 419/573 MSR signals lack explicit FORENSIC/LEL citations) | Build coefficient formula first; back-fill citations as part of rebuild; never-drop discipline. |
| python-sidecar evolution → JH-equivalent natal engine | sidecar today is panchang+ephemeris+jaimini-stub | H | Most of "PyJHora" doesn't exist yet — Wave 1 is a BUILD, not a refactor | Acknowledge build scope; treat existing routers as adapters between new engine and current callers. |
| Cloud Run Job wiring (build trigger) | Job + cockpit + Cloud Task | M | Job's current state not in IaC; "min-instances=1 × 3" cost concern | Materialize Job via cloudbuild first; then wire trigger. |
| Mirror discipline retirement | 5 governance surfaces | M | One PR must touch all five surfaces atomically or drift_detector explodes | Single atomic governance PR; red-team check. |
| Multi-tenant authz (owner≠subject; chart_grants; authorizeChartAccess) | charts + new chart_grants table + every route reading charts | H | charts.client_id is a Firebase UID today (per migration 006); rename to owner_id requires data preservation | Add owner_id alongside; backfill from client_id; deprecate client_id reads in passes; drop column last. |
| Re-numbering 00_/01_/025_/03_/035_/99_ directories (§3.6) | every constituent_plans path + every CAPABILITY_MANIFEST entry + every CLAUDE.md ref | H | Massive doc churn; CI gate needed | Defer to last phase (Wave 4 close); freeze paths until then. |

---

# §5 — Sequencing & Dependency Matrix

Validating the plan's hard gates G1–G5 and 5-wave sequencing.

| Wave/Track | Depends on | Hard gate | Risk if reordered |
|---|---|---|---|
| Wave 0 (renames + B.11 hotfix + secrets + GCP deploy consolidation) | nothing | — | None internally; but mixing pure-renames with B.11 behavior change is a sub-wave concern (see Conflict §2C). |
| Wave 1 (PyJHora engine + JH parity gate) | Wave 0 | **G1** (engine reproduces FORENSIC v8.0) | If Wave 2-a runs without G1 closed, L2.5 builds against non-deterministic L1 — corrupt substrate. |
| Wave 2-a (L1→L2.5 build into extended schema) | Wave 1 (G1) | **G4** (chart_id-keyed before NATIVE_CHART_ID removed) | If Wave 2-c runs alongside without §3.2 normalization, two threads write `chart_id TEXT` and `chart_id uuid` in parallel. |
| Wave 2-b (contract unification + chart_id in contract) | Wave 0 (naming taxonomy) | **G3** (contract before de-judgment) | If Wave 3 de-judgment lands before G3, query-time floors stay duplicated across portal+MCP+sidecar, complicating retirement. |
| Wave 2-c (charts registry owner/subject + authorizeChartAccess) | Wave 0 (mig 117 already exists) | **G2** (multi-tenant authz live before tier excision) | If Wave 3 tier-excision lands first, public routes lose access control. |
| Wave 2-d (Command Center scaffold) | Wave 0 (configService extension) | — | Late-build risk; defer if Wave 2-a/c run hot. |
| Wave 3 — de-judgment | Wave 2-b (G3) | — | Without G3, retire-floors becomes a many-site change. |
| Wave 3 — gateway + control-model-B + pipeline isolation | Wave 2-b | — | Pipeline isolation depends on shared-stage extraction (lib/pipelines/shared/) — see Gap §3 row "Adapter onFinish parity". |
| Wave 3 — per-chart cutover | Wave 1 (G1) + Wave 2-a + Wave 2-c | — | Cutover behind Command Center gate. |
| Wave 3 — portal Consult/nav | Wave 2-c | — | Role-gated nav depends on owner/subject split. |
| Wave 3 — tier excision | Wave 2-c (G2) | **G2** | Removing tiers before authz is hardening rollback. |
| Wave 3 — legacy-pipeline delete | Wave 0 (B.11 port) + adapter onFinish parity gate (G5b proposed) | **G5** (+ G5b) | Delete without onFinish parity drops persistence/observatory/predictions silently. |
| Wave 4 — GCP scale | Wave 3 close | — | Cost-bearing; budget-gate each. |
| Wave 4 — eval re-baseline | Wave 3 close + multi-chart aware | — | One-shot. |
| Wave 4 — learning-loop wiring | Wave 3 (predictions table mig 071 already exists) | — | Wire after legacy delete to avoid double-writes. |

**Hidden / additional dependencies identified**:
1. Wave 2-a and Wave 2-c both write to `charts` — sequence by file fence.
2. §3.7 CI rules (c)+(d) depend on the unified contract — move to Wave 3.
3. Sibling gate **G5b** (adapter onFinish parity) is required before Wave 3 legacy-delete.
4. `marsys-build-pipeline-job` provisioning (Wave 4 §4.2-1 precondition) — confirm before Wave 4.
5. Mirror-discipline retirement (§11.1) must land as a single Wave 0 atomic governance PR.

---

# §6 — Technical / Architectural Review (per track)

### Track 1 — Engine + Data Layer
- **Determinism seam (computed-coefficient salience, deterministic L2.5)**: architecturally sound; the "coefficient as boundary object" cleanly separates deterministic substrate from serve-time non-determinism. **Risk**: salience formula must be authored once and version-pinned; "computed" implies a content-addressed provenance row (engine_version + ayanamsha + input hash). v2.0 §11.2 names this but doesn't specify schema.
- **PyJHora engine**: Wave 1 is a BUILD, not refactor. Today's `python-sidecar` is panchang+ephemeris+jaimini-stub. No full natal engine exists. Recommend: state explicitly in §12 that Wave 1 introduces a new module under `python-sidecar/natal_engine/`; existing routers become adapters.
- **JH oracle policy**: see MUST-RESOLVE #1.
- **Class C enumeration**: MUST-RESOLVE #4.
- **Structural facts spec**: `STRUCTURAL_FACT_LAYER_SPEC_v1_0.md` exists (read this pass only to confirm presence; full review out of scope).

### Track 2 — Tooling
- **De-judgment**: well-localized (msr_sql.ts:20/24/33/44 + MCP query_signals.ts:72/73 + classical_disclosure_filter.ts likely + query_varshphal.ts:87 tier gate). Plan should add the MCP-side copy to §6-A's evidence — it's not a 4-line change, it's 4 lines × 2 channels + 1 tier gate.
- **Unified contract + gateway**: BUILD. `search_tools`/`invoke_tool` do not exist. Gateway will become the single B.11-forced surface for §13's "forced B.11-first guarantee in the gateway the client cannot skip."
- **Tool name canonicalization**: §3.3 rules are sound. Recommend retiring portal-only names first, MCP names becoming canonical (per plan), aliases deleted. Test: `RETRIEVAL_TOOLS.find(t => t.name === '<canonical>')` for every catalog entry.
- **Ghost-tool retirement (17 unregistered tools in catalog)**: easy win. REALITY_REPORT §3B enumerates.
- **Stale `tool_descriptions.test.ts:91`**: trivial.

### Track 3 — Multi-tenancy + Build
- **Owner/subject split**: introduce `owner_id text` on charts; preserve `client_id` until reads migrate; backfill from client_id (they're the same Firebase UID today).
- **`authorizeChartAccess`**: single brain — replaces tier checks scattered across `query_varshphal.ts:87`, `health/tools/route.ts:34`, `health/coverage/route.ts:22`, `lib/disclosure/index.ts`, server.ts:151. Catalogue every existing tier check in the close-out checklist.
- **Build pipeline orchestrator**: net new. Cloud Task + Job + cockpit progress. Plan §5.4 + §4.2-1.
- **Intake determinism**: net new (§5.5). Add geocoder pin + IANA TZ resolution + provenance row.

### Track 4 — Portal / Consult
- **Two isolated pipelines (factual / interpretive-narrative)**: plan implies shared retrieval, separated synthesis. Recommend explicit seam: `lib/pipelines/factual/` + `lib/pipelines/interpretive/` + `lib/pipelines/shared/`.
- **Command Center runtime control plane**: gate_registry + runtime_config + admin UI. configService is the substrate. Add LEL build-exclusion serve-time boundary (§5.2).
- **Role-gated nav**: depends on owner/subject split.
- **Multi-tenant cockpit + chart switcher + sharing UI**: ambitious; UI/UX review in §7 below.

### Track 5 — Serve-time + Learning
- **Model panel + judge**: serves on top of deterministic L2.5. The agentic_loop.ts (R11.F) is the *mechanism*; the panel-vs-judge contract is the *protocol*. PANEL_MODE_TOOL_SPEC carries this — review in scope of brief, not this audit.
- **Prediction logging**: substrate exists (mig 071 `mcp_predictions`). Wire into adapter onFinish.
- **LEL serve-time-only**: confirmed; per-query toggle is a Command Center gate.

### Track 0 — Governance
- **§11 LEAN TRANSFORM**: sound. Mirror retirement cascade is the only sharp edge (MUST-RESOLVE #6).
- **Determinism guarantee model (§11.2)**: solid. Add explicit golden-transcript test schema + content-addressed provenance row format (engine_version + ayanamsha + input hash) so "re-derivable" is operational, not aspirational.
- **Macro-phase wrapper**: ONE macro-phase for the program is the right call.

---

# §7 — UI/UX Review

The plan describes the portal target but doesn't enumerate UI flows in detail. Heuristic review against current state + target.

### Surface × State × Risk

| Surface | Current | Target | Gap | UX risk |
|---|---|---|---|---|
| `/consume` (chat) | live; Claude-style by default (R11B_LOOK_AND_FEEL baked true); fixed-rows composer (locked); auto-collapsible sidebar (locked); Trace in top-right header (locked) | rename → `/consult`; B.11 forced; tier picker REMOVED (= depth selector) | depth-control replacement (server picks depth from query class? or user setting?) | If TierPicker is removed without a depth-control replacement, expert users lose explicit control. Address before removal. |
| TierPicker | Deep/Study/Brief radio (`TierPicker.tsx:33–63`) | DELETE | none — implicit depth via planner | low if tone/format is consistently dialed; needs user perception test |
| Trace button (super_admin) | top-right header | unchanged; expand to "Command Center" entry point? | Command Center is new — needs nav location | medium — overloading the trace button risks ambiguity |
| Chart switcher (multi-tenant) | does not exist | new dropdown in header | net new component; impacts every page | medium — must persist selection, cite chart_id in URL, no silent switch mid-conversation |
| Sharing UI (chart_grants) | does not exist | grant/revoke + share-link UI | net new | medium — security-sensitive; explicit confirm flows |
| Command Center (gate admin) | does not exist | runtime_config admin + per-tenant overrides | net new | medium — destructive ops need audit log + confirm |
| Panchang surface (`/panchang`) | live (Phase 4C complete) | unify `/api/panchang` + `/api/panchanga`; chart-scoped via dropdown | route consolidation only | low |
| Profile / Build / Consult / Panchang nav | basic | role-gated (owner sees Build; guest only sees Consult on granted charts) | net new | medium — guest must never see chart they have no grant for |
| Consume citations panel | shipped (R11.B made bubble-less + URL click-out; CitationSidePanel retired) | unchanged | n/a | low |
| Composer | locked 3-row textarea | unchanged | n/a | low |
| Auto-collapsed sidebar | locked default collapsed | unchanged | n/a | low |
| Dashboard | basic super_admin/client split | role-gated cockpit + multi-tenant view + panchang of the day | net new | medium — first-time guest flow must not assume any chart context |

### Critical flows

- **Guest first-visit** (granted-access only): land on `/consult?chart=<id>` directly from share link; no chart switcher visible if only one grant; no Build/Profile nav; no super_admin signals.
- **Super-admin first-visit on a new chart**: Build wizard prompts intake (datetime + lat + lon + place); creates owner+subject row (NOT a Firebase user per chart — §6-H deletion); enqueues build; cockpit shows progress.
- **Shared-access guest revoke flow**: Command Center revoke must invalidate session; UI must not silently show stale chart.

### UI/UX recommendations beyond v2.0

1. **TierPicker removal**: pair with planner-side depth selection (today's tier picker is the user's only depth knob — replacing it with a query-class auto-pick is fine, but state it explicitly).
2. **Chart switcher** in header: persistent state + chart_id in URL + no silent context mid-conversation.
3. **Command Center**: gate to super_admin only; explicit confirm for any destructive op; full audit trail.
4. **Sharing UI**: explicit revocation + grant expiry options.
5. **Panchang chart-scoping**: header tells user which chart's panchang is shown.

---

# §8 — Naming-Taxonomy Verification

| Concept | Current names (cited) | Proposed canonical | Blast radius | Risk |
|---|---|---|---|---|
| **Product / system / brand** | MARSYS-JIS (docs) + Madhav (brand/GCP project `madhav-astrology`) + amjis- (services: amjis-web, amjis-sidecar, amjis-mcp) | unchanged scope, names defined per §3.1 | docs only | LOW |
| **`marsys-pipeline` → `amjis-builder`** | `marsys-build-pipeline-job` referenced (existence unverified per §4.1); `marsys-` GCS bucket prefix exists | `amjis-builder` Cloud Run Job + bucket rename pending | infra rename + 2 cloudbuild/yaml + ~5 README refs | LOW-MEDIUM (no live data dependency) |
| **Chart tenant key** | `chart_id uuid` (mig 001) + `chart_id TEXT` (mig 022/024/025/031/033) + `native_id varchar(64)` (mig 008/009) + `'abhisek_mohanty_primary'` literal (4 prod + 2 test files) + `'362f9f17-95a5-490b-a5a7-027d3e0efda0'` UUID literal (2 files) + `NATIVE_CHART_ID` constant (4 files) + `DEFAULT_CHART_ID` constant (2 files) | `chart_id uuid` FK→charts.id everywhere | SQL: ~18 tables; TS: ~6+ production files + tests; manifest entries; ~100+ migration seed lines | **HIGH** — see §4 row. Must use strangler. |
| **Chart owner** | `charts.client_id text` (= Firebase UID, mig 006) | `owner_id text` (= Firebase UID) | charts table + ~5 join sites (api/clients/route.ts:20 SELECT; consumers of GET /api/clients) | MEDIUM — backfill from client_id; deprecate reads in passes; drop column last |
| **Chart subject label** | `charts.name` (mig 001:31 area) | `subject_name` | charts table + display in cockpit | LOW |
| **Logged-in user** | "user" / Firebase UID / `req.uid` / `principal` (in MCP) | `principal_id` (FK Firebase UID) | many sites; lower risk than tenant rename | LOW-MEDIUM |
| **Tool: chart_facts** | `chart_facts_query` (portal) ↔ `query_chart_facts` (MCP) | `query_chart_facts` (canonical) | RETRIEVAL_TOOLS alias `chartFactsQueryAlias`; primitives_registry map | LOW |
| **Tool: varshphal** | `query_varshaphala` (portal) ↔ `query_varshphal` (MCP) | `query_varshphal` (canonical, per §3.3) | RETRIEVAL_TOOLS `queryVarshphalAlias`; portal planner prompt mentions `query_varshaphala` (per REALITY_REPORT §1.9) | LOW |
| **Tool: divisional** | `divisional_query` (portal) ↔ `query_divisional_chart` (MCP) | `query_divisional_chart` | trivial | LOW |
| **Tool: CGM** | `cgm_graph_walk` ↔ `get_cgm_subgraph` | `get_cgm_subgraph` | trivial | LOW |
| **Tool: classical** | `classical_text_search_tool` (portal file) ↔ `classical_text_search` (engine) ↔ `read_classical_text` (MCP) | `read_classical_text` (canonical) | three-way collapse | LOW |
| **Tool: multi-school** | `multi_school_signal_lookup_tool` (portal) ↔ {`multi_school_bundle`, `cross_school_lookup`} (MCP, 2:1) | depends on intent; preserve the bundle/primitive split (don't collapse to 1) | the 2:1 split is semantic, not naming | LOW |
| **Tool: msr_sql/query_signals duplication** | `msr_sql` (portal+MCP) + `query_signals` (MCP only, calls msr_sql) | one canonical surface | trivial | LOW |
| **Tool: balam pairs** | `tara_balam_for_native` + `query_tara_balam` (portal aliases); same for chandra | one canonical (`query_tara_balam`, `query_chandra_balam`) | RETRIEVAL_TOOLS has both; collapse | LOW |
| **Feature flags** | `R11V2_USE_ADAPTERS`, `R11E_*_LOOP`, `R11D_GEMINI_CACHE`, `MARSYS_FLAG_*`, NEXT_PUBLIC_MARSYS_FLAG_*; legacy round-prefixes | `MARSYS_FLAG_<DOMAIN>_<FEATURE>` with `_ENABLED` suffix | ~30+ sites (deploy.yml + configService + every check site) | MEDIUM — must move atomically per domain |
| **Env vars** | `GOOGLE_GENERATIVE_AI_API_KEY`, `PYTHON_SIDECAR_URL`, `WIF_PROVIDER`, `DB_*`/`DATABASE_URL` dual | `GOOGLE_CLOUD_*`, `DB_*`, `<PROVIDER>_API_KEY` | ~50+ env-var sites | MEDIUM |
| **Route: `consume` → `consult`** | `/api/chat/consume`, `/consume` page route | `/api/chat/consult`, `/consult` | ~20+ refs | LOW-MEDIUM (cutover alias for 1 release) |
| **Route: `/api/panchang` + `/api/panchanga`** | both live | one (`/api/panchang`) | ~10 refs | LOW |
| **GCS buckets** | `chat-attachments`, `chart-documents`, `madhav-marsys-sources`, `madhav-marsys-build-artifacts`, `marsys-jis-build-state` | `marsys-<purpose>` (or `amjis-<purpose>` per §3.1) | bucket rename = data migration + IAM | MEDIUM |
| **Layer labels** | manifest (L#), CLAUDE.md (L1–L4 + halves), dir tree (00_/01_/025_/03_/035_/99_) | manifest L# canonical; renumber dirs | MASSIVE doc churn | HIGH — defer to Wave 4 close |

**Recommendation**: Sequence by surface-class — pure-rename, code-rename, schema-rename, dir-rename. Run each as one atomic batch behind the new CI gate.

---

# §9 — Elimination-Safety Matrix

| Item | Cited path | Consumers (transitive) | Truly dead? | Safe-to-remove | Note |
|---|---|---|---|---|---|
| `DEFAULT_CONFIDENCE_FLOOR` etc. (§6-A) | `msr_sql.ts:20,24,33,44` | msr_sql.ts only (internal) | NO (live filtering) | NO until L2.5 computed-coefficient column is live AND golden-transcript tests pass | Plan correctly sequences after Track 2. |
| MCP-side de-judgment | `platform-mcp/src/tools/query_signals.ts:72,73,116–126,129–131` | MCP `query_signals` tool | NO (live) | NO; same gate as portal | Add to §6-A evidence. |
| `query_varshphal.ts:87` "redaction" | tier check `audience_tier === 'client' → Forbidden` | live request path | YES as a tier gate (G2 retirement) | YES once authz live + tier subsystem out | Re-label as tier gate, not redaction. |
| `orchestrator.ts` | `synthesis/orchestrator.ts` imported at `consume/route.ts:82,862,1201` | legacy branch only | YES after legacy delete | YES after G5+G5b | Plan correct. |
| `single_model_strategy.ts` | `synthesis/single_model_strategy.ts` | orchestrator-internal | YES after legacy delete | YES with parent | Plan correct. |
| `panel_strategy.ts` | `synthesis/panel_strategy.ts` | legacy single-pass panel mode | YES after legacy delete | UNCLEAR — distinguish from active `synthesis/panel/` directory | Disambiguate first. |
| `/api/mcp/execute/route.ts` | platform route | `platform-mcp/src/client.ts:145 callPlatform` (used for `ask_madhav`, `execute_plan` per client.ts:13) | UNCLEAR — depends on whether `ask_madhav` / `execute_plan` are deleted | NO without confirming MCP-side caller retired | Observation 4288 notes `ask_madhav`/`execute_plan`/`plan_query` are referenced but not registered — likely safe, but verify. |
| `callPlatform()` / `callPlatformPlan()` (`client.ts:145,165`) | only used by legacy MCP tools | NO if their callers exist | NO until verified | Same as above. |
| `lib/disclosure/` | `platform/src/lib/disclosure/{index.ts,types.ts}` + tests | filtering for synthesis (mostly stub per index.ts) | YES (mostly TODO M6/M10) | YES once `acharya_reviewer` preamble lands elsewhere or is dropped | Plan correct; specify preamble disposition. |
| `X-MCP-Audience-Tier` header use | multiple platform routes (`health/tools`, `health/coverage`, `recent`, `asset`, `primitives`, `writes`, `trace`, `bundles`) | live | NO until tier subsystem out | NO before G2 | Plan correct. |
| `mcp_api_keys.audience_tier` (mig 070/117) | mcp_api_keys table | every MCP auth check | NO (read by validateMcpKeyFromHeader) | NO before G2 | Plan correct. |
| `tier_catalog.ts` | `platform-mcp/src/tools/tier_catalog.ts:106,172` (server.ts) | server.ts description variation | YES after tiers excised | YES with G2 | Plan correct. |
| Hard-403 health routes | `/api/mcp/health/tools/route.ts:34`, `/health/coverage/route.ts:22` | live | NO before G2 | NO | Plan correct. |
| `DisclosureTierBadge.tsx` | platform/src/components/disclosure/ | UI component | YES after tiers excised | YES | Plan correct. |
| `public_redacted.md` house-rule variant | platform-mcp/src/resources/house_rules_variants/ | resource registration | YES after tiers excised | YES | Plan correct. |
| `MCP_TO_RETRIEVAL_TOOL` aliases | primitives_registry.ts:92 (not :96) | platform-side primitive dispatch | YES after unified contract | YES with Wave 2-b | Plan correct after line correction. |
| `SURGICAL_TOOLS` 32-dup | primitives_registry.ts:46 | type union | YES (dedup is non-breaking) | YES — Wave 0 | Easy win. |
| `retrieve/index.ts:151–212` inline aliases | RETRIEVAL_TOOLS array body + 2 aliases at tail | engine resolution | aliases YES (after canonical rename); array entries NO | partial | Plan should specify "the aliases", not "the array". |
| Duplicate budget tables (`tokensFor` :1418 / `tokensForAdapter` :1139) | consume/route.ts | telemetry | YES once shared lib | YES with Wave 3 (shared lib) | Plan correct. |
| `TierPicker.tsx` | platform/src/components/consume/ | depth selector | YES with G2 | YES | Plan correct. |
| `CONSUME_UI_V2_ENABLED` dead branch | `consume/page.tsx:123` (not directly verified) | gated branch | UNVERIFIED | UNVERIFIED | Verify before delete. |
| L2 layer rows | `api/clients/route.ts:82–83` `'L2.analysis_mode_a'`, `'L2.analysis_mode_b'` | pyramid_layers seed | YES (L2 archived) | YES | Plan missed this — add. |
| Per-chart Firebase user | `api/clients/route.ts:51,57,75` | charts insert | YES after owner/subject split | YES with G2 | Plan correct. |
| `tool_descriptions.test.ts:91` assert 22 | stale test | none — fails CI when run | YES | YES — Wave 0 | Easy. |
| `PRIMARY_TOOL_NAMES` | symbol reference | UNVERIFIED | UNVERIFIED | UNVERIFIED | Verify. |
| `@deprecated resolver.ts:68` | UNVERIFIED file | UNVERIFIED | UNVERIFIED | UNVERIFIED | Verify. |
| `assembleTraceLegacy` / `fetchTraceLegacy` | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | Verify. |
| `retrieval_capability_spec.ts` (claimed dead) | NOT FOUND as source file | only tests | already dropped per §6 note | n/a | Plan §6 note correct — drop. |

---

# §10 — GCP Review

### §10.1 — Map confirmation
- **Cloud Run services**: `amjis-web` (deploy.yml), `amjis-sidecar` (deploy.yml:106,159–167; sidecar URL hardcoded in env), `amjis-mcp` (platform-mcp/cloudbuild.yaml). All CONFIRMED.
- **Cloud Run Job `marsys-build-pipeline-job`**: NOT found in CI/IaC; `platform/python-sidecar/Dockerfile.pipeline` exists, suggesting the Job's image is built but I could not find its provisioning. **PARTIALLY-CORRECT — needs IaC verification.**
- **CI dual deploy path**: 6 GitHub Actions workflows (`chat-v2-ci.yml`, `chat-v2-smoke.yml`, `ci.yml`, `deploy.yml`, `icr_weekly_scan.yml`, `mcp-bench.yml`) + 4 cloudbuild.yaml (root, platform/, platform/sidecar, platform-mcp/). CONFIRMED.
- **WIF**: deploy.yml:12 `WIF_PROVIDER` + `:13` `WIF_SERVICE_ACCOUNT`. CONFIRMED.
- **Cloud SQL `amjis-postgres` tier `db-g1-small`**: Cited in plan but not in CI/IaC; would need `gcloud sql instances describe`. UNVERIFIABLE.
- **GCS buckets**: deploy.yml references `madhav-marsys-build-artifacts` and similar; specific bucket inventory not exhaustively verified in this pass. PARTIALLY-CONFIRMED.
- **Vertex AI embeddings**: `text-multilingual-embedding-002` referenced in past sessions; not directly inspected this pass.
- **MCP `--allow-unauthenticated`**: `platform-mcp/cloudbuild.yaml:56`. CONFIRMED.
- **Cloud Scheduler**: only comment references (chat-v2-ci.yml:512,515,522) — confirmed "comment-only".
- **Hardcoded DB passwords**: my grep found no obvious literal passwords in `scripts/` and `platform/scripts/` (most via process.env / os.environ). PARTIALLY-CORRECT — plan should cite exact paths.

### §10.2 — Improvements feasibility

| # | Improvement | Feasibility | Prerequisites | Cost direction |
|---|---|---|---|---|
| 1 | Build orchestration (Cloud Task → Job; Workflows + Eventarc) | high | Provision Job IaC first; design queue topology | small ↑ (Task + Pub/Sub) |
| 2 | Cloud SQL upgrade + HA + partition + PITR | high | Verify current tier; backfill in maintenance window | medium ↑ |
| 3 | Memorystore (Redis) | high | Add client + cache layer; defaults TTL | medium ↑ |
| 4 | Edge LB + Cloud CDN + Cloud Armor + IAM on MCP | high | LB topology; Armor rules; MCP IAM identity | small ↑ |
| 5 | Per-service least-privilege SAs | medium | Audit current SA scopes | neutral |
| 6 | Secret hygiene + Artifact Registry + image cleanup | high | Audit Secret Manager naming; AR migration | neutral |
| 7 | Consolidate deploy path (recommend GHA WIF) | high | Delete cloudbuild trigger refs; update docs | neutral |
| 8 | Cloud Scheduler as IaC | medium | Decide what to schedule; codify | small ↑ |
| 9 | Cloud Trace + Monitoring + SLOs + batch Vertex | high | Tracing instrumentation across web→sidecar→mcp; batch API | small ↑ |
| 10 | Cost review (min-instances + Anthropic) | high | Native decision on cost ban | could go either way |

### §10.3 — Cost gate
Plan §8 R12 names cost step-up; recommend per-improvement budget gate in Wave 4 with explicit native approval.

---

# §11 — Open-Questions Resolution

| # | Plan open-decision | What the code implies | Recommendation |
|---|---|---|---|
| 1 | Ayanamsha parity | FORENSIC `ayanamsa: Lahiri (Chitrapaksha), value 23°37′58″`; mig 022 seed values `'lahiri'`; sidecar uses `pyswisseph` | Lahiri (Chitrapaksha) is the de-facto pin. Codify in engine config + provenance row. |
| 2 | Coefficient child-table shape | not implemented today | Defer to Wave 2-a spec; recommend `{chart_id, asset_id, coefficient_name, value, formula_version, computed_at}` |
| 3 | Hybrid-tool chart_id rule | hybrid tools today read `args.chart_id ?? NATIVE_CHART_ID` (default to single-native) | Make `chart_id` required in unified contract; remove default. Wave 2-b. |
| 4 | Write/ops authz | server.ts:230 says "All ops tools registered unconditionally — native is super_admin"; flag_disagreement gates internally; log_prediction does not | Code implies: keep ops tools open in single-native mode; gate in multi-tenant mode via `authorizeChartAccess`. |
| 5 | Pipeline-isolation timing | adapter + legacy both run today; flag gates | Strangle: shared-stage extraction first; isolate by file fence; legacy delete last. |
| 6 | Per-asset deterministic add-ons | not present | Defer to Wave 2-a spec. |
| 7 | Cutover granularity | Phase 4C precedent (`bootstrap_panchanga.py` staging→live swap); rollback via `build_id` | Reuse the pattern: per-class C asset and per-chart B base; freeze old as archive. |
| 8 | Macro-phase number | next available per CURRENT_STATE M5 active | Tentatively M6 or a parallel M5-X "modernization" track. Native call. |
| 9 | Product prefix | amjis-=infra, Madhav=brand/project, MARSYS-JIS=system | Confirm; no code blocker. |
| 10 | Layer-vocabulary canonicalization | three vocabularies live; manifest carries L# | Adopt the manifest's L# as SSOT; defer dir renumber to Wave 4 close. |
| 11 | GCP investment level | scaffold is dev-tier; production load is single-native today | Native decision; recommend incremental (Memorystore + observability first; SQL upgrade + HA when multi-tenant signs up). |
| 12 | Build trigger mechanism | none exist today | Cloud Task simplest; Workflows + Eventarc for staged DAG; both feasible. Recommend Cloud Task v1; revisit if DAG grows. |
| 13 | Deploy path | Both paths active; deploy.yml is more comprehensive | GitHub Actions WIF as sole — yes. Delete cloudbuild triggers. |
| 14 | Data-cleanse mechanism | RESOLVED 2026-05-27 (parallel-build + cutover + freeze-old). | Confirmed by code: Phase 4C used staging→live swap (precedent). |
| 15 | Existing-governance posture | RESOLVED 2026-05-27 (LEAN TRANSFORM). | Confirmed — sound. |
| 16 | Gemini/multi-agent mirror | RESOLVED 2026-05-27 (RETIRE). | Confirmed; cascade needed (MUST-RESOLVE #6). |
| 17 | MCP client-expectations source | OPEN; no code dependency | Surface as Wave 0 artifact-discovery; cannot be resolved by code reading. |

---

# §12 — Audit close-out

- **Audit pass result**: PASS WITH CONDITIONS — see Executive Summary MUST-RESOLVE list.
- **Files inspected (sample of high-value)**: `00_ARCHITECTURE/PLATFORM_MODERNIZATION_MASTER_PLAN_v2_0.md`, `…/v1_0.md`, `…/INVESTIGATION/TOOL_PORTFOLIO_REALITY_REPORT.md`, `platform/src/lib/retrieve/msr_sql.ts`, `platform-mcp/src/tools/query_signals.ts`, `platform-mcp/src/tools/query_varshphal.ts`, `platform/src/app/api/chat/consume/route.ts`, `platform/src/components/consume/TierPicker.tsx`, `platform/src/app/api/clients/route.ts`, `platform-mcp/src/server.ts`, `platform/src/lib/mcp/primitives_registry.ts`, `platform/src/lib/retrieve/index.ts`, `platform/src/lib/disclosure/index.ts`, multiple migrations (001/006/008/009/014/018/022/024/025/031/033/110/117), `.github/workflows/deploy.yml`, `platform-mcp/cloudbuild.yaml`, `platform/cloudbuild-sidecar.yaml`, `platform/python-sidecar/main.py`, `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` frontmatter, `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` sample.
- **Files NOT inspected (out of scope for one pass, flagged for verification before implementation)**: full DATA_LAYER_REBUILD_TARGET_SPEC body, full FACT_ENGINE_PYJHORA_BRIEF body, full PORTAL_NORTH_STAR_ARCHITECTURE body, full PLATFORM_REBUILD_ARCHITECTURE body, full MSR_UCN_CONTAMINATION_AUDIT body, every migration in detail, every cloudbuild step, full python-sidecar router internals, full `lib/disclosure/index.ts` past the inspected head. These should be pre-implementation read items per the discoveries in §1-§11.
- **No code, no migration, no plan edits were performed.**

*End of audit report.*

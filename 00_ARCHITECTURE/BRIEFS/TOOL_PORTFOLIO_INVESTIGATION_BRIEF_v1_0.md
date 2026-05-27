# Tool Portfolio — Ground-Truth Investigation Brief (for Claude Code)

> **How to run:** Open this repo in Claude Code (Antigravity) and paste:
> *"Read `00_ARCHITECTURE/BRIEFS/TOOL_PORTFOLIO_INVESTIGATION_BRIEF_v1_0.md` and execute it exactly. Produce the report at the path it specifies. This is a read-only investigation — do not modify any code or governance artifact."*

---

## 0. Role, mission, and HARD CONSTRAINTS

You are performing a **read-only forensic investigation** of the MARSYS-JIS tool/MCP landscape. A
separate planning track (Cowork) is designing a refactor that converges two channels — the **MCP
sidecar** (`platform-mcp/`) and the **portal `/consume` agentic loop** (`platform/`) — onto a single
canonical tool contract. Your job is to establish **complete ground truth** so the plan can be
finalized in one pass. Be exhaustive. Do not produce half-answers.

**HARD CONSTRAINTS — do not violate:**
- **READ-ONLY.** Do NOT edit, create, move, or delete any source, manifest, migration, or governance
  file. The ONLY file you may write is the report (path in §1).
- **No mutations to governance.** Do NOT run the session-open/close handshake, do NOT touch
  `SESSION_LOG.md`, `CAPABILITY_MANIFEST.json`, `CURRENT_STATE`, fingerprints, or mirrors. You may
  *read* `CLAUDE.md` and `00_ARCHITECTURE/*` for orientation.
- **No destructive/side-effecting commands.** No deploys, no migrations, no writes to the DB, no
  `npm run` that mutates state. Read-only DB `SELECT`s are allowed (see §2). `npm run build` /
  `tsc --noEmit` / running the read-only test harnesses is allowed if needed to observe behavior, but
  prefer static reading.
- **No guessing.** Every answer carries `file:line` or command-output evidence. If something cannot be
  determined (e.g., DB unavailable), write **`UNVERIFIED — <reason>`** and explain exactly what's
  needed to verify. Do not paper over gaps.
- **Flag surprises.** If reality contradicts an assumption in this brief, say so loudly — that is the
  most valuable output.

**Verdict vocabulary** (use per question): `CONFIRMED` · `CONTRADICTED` · `PARTIAL` · `UNVERIFIED`.

---

## 1. Required output

Write a single Markdown report to:

```
00_ARCHITECTURE/INVESTIGATION/TOOL_PORTFOLIO_REALITY_REPORT.md
```

(Create the `INVESTIGATION/` folder if needed — that is the one write you may make, plus the report.)

**Report structure (mandatory):**
1. **Executive summary** — top 10 findings, and a bulleted list of every place reality CONTRADICTS or
   exceeds the assumptions in this brief.
2. **The Master Tool Table** (see §3) — the single most important artifact. One row per tool.
3. **Sections 4–14** answering every numbered question below, each with verdict + evidence + nuance.
4. **Appendix: commands run** — the exact shell/grep/SQL you used, so results are reproducible.

For every question: state the **verdict**, give **evidence** (`path:line` or command output excerpt),
and add **nuance** if the truth is more subtle than the question implies.

---

## 2. Capabilities to use (use ALL that apply — this is why Claude Code, not chat)

- **Exhaustive grep/glob** across BOTH `platform/` and `platform-mcp/` (and `00_ARCHITECTURE/`).
- **Database row counts** (ground truth for "empty data" tools). If a local proxy is available
  (look for `platform/scripts/start_db_proxy.sh`, typically port 5433; connection via `DATABASE_URL`
  or `.env`), run **read-only `SELECT count(*)`** queries. If no DB is reachable, mark those items
  `UNVERIFIED` and infer emptiness from seed scripts + graceful-empty code paths, stating which.
- **Inspect `node_modules`** — e.g. `platform-mcp/node_modules/@modelcontextprotocol/sdk/dist/` for the
  real `registerTool`/`sendToolListChanged`/`listChanged` API (a prior chat-based pass could not see the
  compiled dist; you can).
- **Run read-only harnesses** if static reading is ambiguous (`tsc --noEmit`, the accuracy/bench test
  files in dry mode) — but do not mutate state.
- **Count, don't estimate** — e.g. exact number of manifest entries with a non-empty `query_schema`.

---

## 3. The Master Tool Table (build this first — it anchors everything)

Produce one row per **MCP-facing tool AND per underlying retrieval engine** (union of both worlds).
Columns:

| col | meaning |
|---|---|
| `mcp_name` | name registered in `platform-mcp/src/server.ts` (or "—" if not MCP-registered) |
| `engine_name` | underlying `RETRIEVAL_TOOLS` engine it maps to (`platform/src/lib/mcp/primitives_registry.ts` `MCP_TO_RETRIEVAL_TOOL`) |
| `portal_name` | name the portal/planner uses (from `retrieve/index.ts`, may differ — note aliases) |
| `registered_in_server_ts` | yes/no |
| `in_primitives_whitelist` | yes/no |
| `in_manifest` | yes/no (+ canonical_id) |
| `has_query_schema_in_manifest` | yes/no |
| `has_zod_schema` | yes / no-params / raw-literal / transform-refine (from `platform-mcp/src/tools/*.ts`) |
| `channel` | both / mcp / portal (manifest `channel` field) |
| `written_unregistered_mcp_file` | yes/no (a `tools/*.ts` file exists but isn't imported in server.ts) |
| `is_stub` | yes/no (sidecar `not_implemented` etc.) |
| `data_table` | the table/asset it reads |
| `data_rows` | row count if DB reachable, else `UNVERIFIED` |
| `b11_floor_member` | yes/no (appears in the consume/route.ts floor literals) |
| `declared_asymmetry` | yes/no (listed in INTERFACE_NORMALIZATION_REGISTER §2 as deliberately distinct) |
| `handler_complexity` | trivial-dispatch / has-custom-logic (note what) |

Reconcile and **state the authoritative count** of registered MCP tools — the codebase currently
disagrees with itself (a test asserts ~22, `server.ts` ~40, `catalog.ts` header "57"). Resolve it.

---

## 4. Inventory & count reconciliation

4.1 Exact list + count of `RETRIEVAL_TOOLS` (`platform/src/lib/retrieve/index.ts`), including the alias
objects. How many engines vs alias entries?
4.2 Exact list + count of `register*()` calls in `platform-mcp/src/server.ts`. The TRUE registered count.
4.3 `primitives_registry.ts`: list `SURGICAL_TOOLS` + `MCP_TO_RETRIEVAL_TOOL`; flag the **duplicate
`msr_sql`** and every engine-name pass-through alias entry.
4.4 `catalog.ts`: count entries; does `tool_descriptions.test.ts` assert a length (what number)? Reconcile
the 22/40/57 contradiction with evidence.
4.5 `CAPABILITY_MANIFEST.json`: total entries; count of `type:"retrieval_tool"`; count with non-empty
`query_schema`; channel split (both/mcp/portal).

## 5. Manifest & canonical-contract feasibility

5.1 Confirm manifest is generated (`platform/src/scripts/manifest/build.ts`) from frontmatter +
`manifest_overrides.yaml`; confirm hand-edits are overwritten.
5.2 Confirm `platform/src/lib/schemas/asset_entry.schema.json` is `additionalProperties:false` and that
unknown fields are **warn-only** (build proceeds). Quote the warn code path.
5.3 Is there a Zod↔JSON-Schema converter anywhere in deps (`zod-to-json-schema`, `json-schema-to-zod`,
etc.)? Is `zod` a direct dependency of `platform-mcp/package.json` or only transitive? What converter +
dependency would be required to (a) backfill manifest schemas FROM Zod and (b) register MCP tools FROM
manifest JSON Schema?
5.4 Per-tool Zod schema audit: for EVERY MCP tool, classify `has_zod_schema` (yes/no-params/raw-literal/
transform-refine). List the tools whose schemas use `.transform`/`.refine` (won't round-trip JSON Schema
losslessly).
5.5 Handler-complexity audit: sample at least `query_signals.ts`, `chart_summary.ts`,
`holistic_bundle_tool.ts`, `log_prediction.ts`, plus 4 others — which handlers contain logic beyond
schema+dispatch? Conclusion: can a manifest-driven registration loop replace hand-registration while
keeping handlers? State precisely what stays hand-written.
5.6 Are `catalog.ts` and the `capabilities.ts` resource hand-maintained? Confirm `capabilities.ts`
hardcodes a tool list/count and what number (stale?).

## 6. Dual-channel control flow

6.1 Trace a `/consume` request in `platform/src/app/api/chat/consume/route.ts`: confirm `runPlanner()`
runs unconditionally; identify the three synthesis tails and the EXACT flag gates
(`R11V2_USE_ADAPTERS`, per-provider `R11E_*_LOOP`). Quote line numbers.
6.2 Confirm the agentic loop's tool catalog = `buildChatToolsFromNames(queryPlan.tools_authorized)` and
that the loop is therefore constrained to the planner-authorized subset.
6.3 Confirm `executeMCPTool` (`platform/src/lib/synthesis/mcp_tool_executor.ts`) dispatches via
`getTool(name).retrieve()` — i.e. portal calls engines IN-PROCESS while MCP calls them over HTTP
(`/api/mcp/primitives`). Confirm both ultimately hit the same engine layer.
6.4 **Planner-demotion blast radius:** enumerate everything that depends on `tools_authorized` /
`PipelinePlan` being authoritative — parallel pre-fetch, `arbitrateBudgets`/token budgets, trace logging
(`writeQueryPlanLog`, step_seq), caching (`plannerParamsMap`/`executeWithCache`), audit consumer,
context-assembly token accounting, the loop catalog itself, and the `LegacyQueryPlanShape` threaded into
every `retrieve(queryPlan, …)`. Give the concrete couplings with line numbers.

## 7. B.11 enforcement (and the loop gap)

7.1 List ALL B.11 floor literal sites in `route.ts` (the default L2.5 set, the **predictive branch** that
bans `cgm_graph_walk`, and the dasha floor adding `chart_facts_query`). Quote them.
7.2 Confirm the agentic-loop path has **no forced-first tool call** and that B.11 is enforced only by
pre-injected floor context.
7.3 **Critical:** does the adapter/loop tail have ANY final-answer guard (citation gate / B.11 guard), or
does the `onFinish` citation gate (`validateCitationsForStream`) exist ONLY on the orchestrator path?
Determine whether the loop tail is currently un-guarded for B.11.
7.4 Confirm the MCP-side B.11 is advisory prose (`platform-mcp/.../resources/house-rules*`/`house_rules.ts`),
not deterministic. Two mechanisms, unequal strength — confirm.
7.5 List EVERY name-keyed table in `route.ts` (`toolStepType`, `inferLayer`, token-accounting tables
`tokensFor`/`tokensForAdapter`) — exact line ranges. These all need updating on any tool rename.

## 8. Gateway / dynamic loading / providers

8.1 SDK reality: from `platform-mcp/node_modules/@modelcontextprotocol/sdk/dist/`, confirm the
`registerTool` handle methods (`.enable/.disable/.update/.remove`) and `sendToolListChanged`, and the
`tools.listChanged` capability. Does the codebase use `registerTool` or the legacy `server.tool(...)`?
(Confirm whether the dynamic API is wired or merely latent.)
8.2 Confirm the server is stateless (`sessionIdGenerator: undefined`; new `McpServer` per POST; `GET /mcp`
→ 405) and that statelessness — not the SDK — blocks native `listChanged`. What exactly must change to go
stateful (session store, SSE GET endpoint, Cloud Run stickiness)?
8.3 Provider path: how do tool schemas reach each of the 5 providers
(`platform/src/lib/providers/{anthropic,google,openai,deepseek,nvidia}/adapter.ts`)? Where does the
schema transform actually happen (`tools()` vs `chat()`), and what does `normalizeInputSchema` do? Any
provider tool-count caps?
8.4 Gateway feasibility: would a stateless `search_tools` + `invoke_tool` pattern work given the above?
Enumerate concretely what routing through a generic `invoke_tool` would LOSE (per-tool observability /
Observatory tool-loop tiles, model-visible per-tool schemas, B.11 audit granularity, per-tool client UX,
streaming identity). Can `search_tools` source schemas from the manifest TODAY (recall 5.3 — likely no)?

## 9. Tier removal — COMPLETE surface (be exhaustive; this was under-counted before)

Enumerate EVERY occurrence touching `audience_tier` / `tier` / `acharya` / `acharya_reviewer` / `client`
/ `super_admin` / `public_redacted` / `disclosure_tier`, grouped by subsystem, with `file:line`. Must cover:
9.1 `platform-mcp/`: `auth.ts` (the validation gate that rejects keys lacking `audience_tier`), `types.ts`
(Principal / envelope `audience_tier` field), `server.ts` (URL-key→super_admin gate; `getCatalogForTier`/
`tierDesc`), `tier_catalog.ts` (whole module), `bundles/*` (params + cache key), `resources/*`
(house_rules variants + hardcoded `X-MCP-Audience-Tier` headers — **sweep ALL `tools/*.ts` for header
senders**, not just bundles).
9.2 `platform/` API routes: confirm whether `/api/mcp/health/tools` and `/api/mcp/health/coverage`
**hard-403 by tier** (a real surviving tool-access gate). Then sweep ALL `/api/mcp/*` routes
(`execute`, `primitives/[tool]`, `bundles/[name]`, `asset`, `writes/[action]`, `trace/[trace_id]`,
`recent`, `keys`, `keys/validate`) for reading/stamping the tier header.
9.3 **DB / key issuance:** `mcp_api_keys` schema (migration 070) + the migration adding `acharya`
(check ~117); the key-creation route + admin UI (`McpKeysClient.tsx` tier dropdown); `lib/mcp/auth.ts`
SELECT of `audience_tier`.
9.4 `PipelinePlan.audience_tier` zod enum (`pipeline/types.ts`); `epistemics.ts` tier params;
`classical_disclosure_filter.ts` (content redaction by tier); `query_plan.schema.json` + migrations
027/040 (do they carry `audience_tier`?).
9.5 The **`acharya` vs `acharya_reviewer` naming split** — list every spelling in DB vs code.
9.6 All tests/fixtures/bench carrying tier (`tier_catalog.test.ts`, `server_tier_visibility.test.ts`,
`mcp_visibility.integration.test.ts`, red-team tests, bench scenario YAMLs).
9.7 Produce a single consolidated **"tier-removal worklist"** — every file that must change, grouped
into: delete-module / drop-field / drop-DB-column+constraint / remove-route-gate / update-test.

## 10. Per-tool disposition reality

For each item, verify the proposed verdict (CONFIRMED/CONTRADICTED/NUANCE):
10.1 Same-engine merge: `query_signals` + `msr_sql` both → engine `msr_sql`?
10.2 Register quartet (`pattern_register`/`resonance_register`/`cluster_atlas`/`contradiction_register`)
— 4 distinct engines, near-identical shape? Note shape divergences (e.g. fixed conf/sig, signal_id keys).
10.3 Synthesis trio (`query_ucn_walk`/`query_cdlm_lookup`/`query_rm_walk`) — 3 distinct engines/files?
10.4 Remedies: confirm `query_remedies_prescribed` **imports/calls** `remedial_codex_query` (a layering,
not a sibling) — so a naive merge risks recursion.
10.5 PROMOTE set — for EACH of `tara_balam_for_native`, `chandra_balam_for_native`,
`query_transits_over_natal`, `query_yogas_active_now`, `get_shadbala_full`, `get_planet_avastha`,
`query_jaimini_chara_dasha`, `query_planetary_period_predictions`, `query_eclipse_transits`,
`query_planet_war`, `saham_query`, `domain_report_query`, `query_msr_aggregate`: confirm engine exists,
NOT registered in server.ts, and whether a **written-but-unregistered `platform-mcp/src/tools/*.ts`**
file already exists (i.e. "wire it" vs "build it").
10.6 `query_jaimini_drishti` is a stub (sidecar `not_implemented`) — confirm + confirm it IS currently
registered.
10.7 BACKFILL: `get_cgm_subgraph`(`cgm_graph_walk` → `l25_cgm_*`), `timeline_query` (reads
`rag_chunks WHERE doc_type='l5_timeline'`, NOT a dedicated table), `query_signal_state` (`signal_states`).
**Run row counts** to prove emptiness (or `UNVERIFIED`). Note the populate scripts (e.g.
`signal_activator.py`).
10.8 Spot-check ≥3 of the 6 declared asymmetries to confirm they are genuinely distinct, not duplicates.
10.9 FOLD candidates exist as engines: `query_dasamsha_career`, `query_shashtiamsha`,
`query_drekkana_drishti`, `cross_varga_dignity_query`, `classical_attribution_lookup`,
`convergence_score_lookup`, `manifest_query`, `query_v7_additions` — confirm each + give a one-line "what
it does" so fold targets are clear. Resolve the two INVESTIGATE items (`query_v7_additions`,
`domain_report_query`) definitively.

## 11. Rename / migration blast radius (the complete coupling list)

Grep both trees and produce the EXHAUSTIVE list of every string-literal tool/engine-name coupling a
rename/merge must update atomically. Must include and verify each:
11.1 `catalog.ts` names + the length assertion in `tool_descriptions.test.ts`.
11.2 `server.ts` register calls + each tool file's `server.tool('<name>', …)` literal.
11.3 `primitives_registry.ts` (`SURGICAL_TOOLS` array + `MCP_TO_RETRIEVAL_TOOL` keys AND values +
`SurgicalToolName` type).
11.4 `retrieve/index.ts` (`tool.name` literals + the alias objects `chartFactsQueryAlias`/
`queryVarshphalAlias`; `getTool(name)` resolution).
11.5 `retrieval_capability_spec.ts` `tool_name` fields (confirm DEAD — only its own test imports it).
11.6 `route.ts` `toolStepType`/`inferLayer`/floor literals/token tables.
11.7 Bundle fan-out maps: `platform-mcp/src/bundles/holistic_bundle.ts` `getToolRouteFor` +
`multi_school_bundle.ts` peer map (which sub-tool names they call).
11.8 **DB tool registry**: `platform/scripts/governance/seed_tool_registry.ts` reads `tool_name` from
`CAPABILITY_MANIFEST.json` and upserts `capability_tool_registry` (migration 070/077) — a non-code
coupling. Confirm + note it requires a manifest edit + DB re-seed on rename.
11.9 **`00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md`** — count tool-name occurrences (expected ~47) and confirm
it is loaded verbatim at runtime by `pipeline_planner.ts` (find the load line). This is the largest single
literal surface — verify.
11.10 `bench/scenarios/*.yaml` tool names + `cross_scenario.test.ts` literal `chart_summary`/
`query_chart_facts`.
11.11 Any prompt templates / house-rules / docs that name tools and are runtime-loaded (vs pure docs).
Distinguish runtime-loaded from inert.

## 12. Eval harness reality

12.1 `platform-mcp/test/accuracy/*`: confirm the golden is **category-keyed** (how many categories?),
NOT tool-name-keyed; list the exact triggers that DO invalidate it (`CHART_FACTS_CATEGORIES` change,
`query_chart_facts` shape change, rename of `chart_summary`/`query_chart_facts`).
12.2 `platform-mcp/test/bench/*`: confirm it IS tool-name-keyed (which tools, which round-trip-count
assertions).
12.3 `tool_descriptions.test.ts`: list every lint rule it enforces on `catalog.ts`.
12.4 `answer:eval`: where does it live (`platform/scripts/answer_eval.ts`?), what are its scoring
criteria, and how is the chart selected (env `CHART_ID`? default?)? What would re-baselining require?

## 13. Dead code & orphans

13.1 Confirm `retrieval_capability_spec.ts` is dead (only its test imports it).
13.2 Confirm the MCP orphaned planner path: `/api/mcp/execute` route + `callPlatform()`/
`callPlatformPlan()` in `platform-mcp/src/client.ts` have NO callers among registered tools; confirm no
registered MCP tool is `ask_madhav`/`plan_query`/`execute_plan`.
13.3 Confirm the `primitives_registry.ts` alias cruft + duplicate `msr_sql`.
13.4 Any other dead/duplicate tool code you find.

## 14. Governance integration (what a refactor session must do)

14.1 How do `drift_detector.py` / `schema_validator.py` / `mirror_enforcer.py` consume the manifest
("manifest mode"), and what triggers a HIGH finding (e.g. `fingerprint_sha256` vs on-disk file)?
14.2 What must a refactor session do to stay compliant when it edits tool source + the manifest
(fingerprint rotation, `last_verified_*`, MP.5 mirror to `.geminirules`, session close-checklist)?
14.3 Does mirror pair MP.5 trip on tool-only changes, or only on L2.5 asset-path changes? Confirm.

---

## 15. Final deliverable

Write `00_ARCHITECTURE/INVESTIGATION/TOOL_PORTFOLIO_REALITY_REPORT.md` with: the executive summary, the
Master Tool Table (§3), answers to every numbered question in §4–§14 (verdict + evidence + nuance), the
consolidated tier-removal worklist (§9.7), the consolidated rename blast-radius list (§11), and the
appendix of commands run. Then print a short chat summary: the authoritative tool count, the top 5
contradictions found vs this brief, and any blockers (e.g. DB unreachable) that left items `UNVERIFIED`.

**Remember:** read-only; evidence for every claim; no guessing; flag every surprise. Completeness over
brevity — this report must let the planning track finalize without another investigation round.

---
canonical_id: TOOL_PORTFOLIO_PLAN
version: 1.2
status: DRAFT — FOR NATIVE REVIEW
supersedes: TOOL_PORTFOLIO_PLAN_v1_1.md (and v1.0) — archive both on approval of v1.2
date: 2026-05-27
author: Cowork planning session (no implementation; plan only)
scope: Unified tool contract across MCP + portal agentic loop — structure, reconciliation, dynamic loading, B.11, tiers
related:
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  - 00_ARCHITECTURE/manifest_overrides.yaml
  - 00_ARCHITECTURE/INTERFACE_NORMALIZATION_REGISTER_v1_0.md   # at v1.1
  - platform/src/scripts/manifest/build.ts
  - platform/src/lib/schemas/asset_entry.schema.json
  - platform/src/lib/retrieve/index.ts                         # RETRIEVAL_TOOLS (55)
  - platform/src/lib/retrieve/tool_catalogue.ts                # buildChatToolsFromNames — EMPTY schemas today
  - platform/src/lib/mcp/primitives_registry.ts                # MCP_TO_RETRIEVAL_TOOL (to be retired)
  - platform/src/lib/synthesis/mcp_tool_executor.ts            # executeMCPTool → getTool().retrieve()
  - platform/src/lib/providers/agentic_loop.ts                 # R11 bounded loop
  - platform/src/lib/pipeline/pipeline_planner.ts              # server-side planner
  - platform/src/app/api/chat/consume/route.ts                 # planner-first; B.11 floor literals (460-504)
  - platform-mcp/src/{server.ts,auth.ts,types.ts}              # MCP Zod schemas = richest contract seed
  - platform-mcp/src/resources/* , platform-mcp/src/bundles/*
  - platform-mcp/test/accuracy/* , platform-mcp/test/bench/*
note: >
  STRATEGIC PLAN, not an implementation brief. v1.2 reflects the native decision to converge
  the two channels onto ONE canonical tool contract (not a wrapper around the divergence) and
  is grounded in verification of the portal agentic-loop internals. Executor briefs are cut
  per-phase only after this plan is approved.
---

# Tool Portfolio — Unified Contract Plan v1.2

## §0 — Purpose, locked decisions, what changed from v1.1

**Goal.** Stop maintaining two divergent tool worlds. Build **one canonical tool contract** —
one name, one input schema, one Claude-tuned description, one annotation set, one engine handler
per capability — generated from the manifest and consumed identically by **both** the MCP server
and the portal agentic loop. The LLM selects tools the same way on both channels; only the
*synthesis runtime* differs (MCP delegates to an external host; the portal hosts its own LLM).

**Locked with native:** full reconcile · tiers ripped out entirely · dynamic loading both
(gateway now, native `listChanged` later) · **unified tool contract** (converge, don't wrapper) ·
sequencing per best practice (contract spine first) · auth/eval/normalization-register are all in
scope to deconstruct, not work around.

**What changed from v1.1 (driven by portal verification):**
1. The plan's spine is now the **Canonical Tool Contract** consumed by both channels (§2), not an
   MCP-only wrapper. The `MCP_TO_RETRIEVAL_TOOL` map, the alias objects, and
   `INTERFACE_NORMALIZATION_REGISTER` are **retired**, not extended.
2. Verification revealed the portal is **planner-first, loop-second** (loop constrained to
   `tools_authorized`), and its agentic-loop tool **schemas are empty**. So convergence (a) requires
   a **control-model decision** (§3) and (b) **fixes a live portal quality bug** (empty schemas).
3. **B.11 is enforced two ways today** — unify to one shared mechanism (§4).
4. Contract is **seeded from the MCP Zod schemas** (the richest existing source), not authored from scratch.

---

## §1 — Verified system truth

**Shared engine layer (already unified at runtime).** Both channels call `getTool(name).retrieve()`
on `RETRIEVAL_TOOLS` (55 entries = 53 engines + 2 alias objects). Portal calls it in-process
(`mcp_tool_executor.ts:executeMCPTool`); MCP calls it over HTTP via `/api/mcp/primitives/{tool}`
(which itself calls `getTool().retrieve()`). **The engine layer is the existing shared substrate.**

**Divergent tool-contract layer (the problem).**
| | Tool-list source | Input schema | Naming |
|---|---|---|---|
| **MCP server** | 40 hand-registered `register*()` in `server.ts` | rich hand-written **Zod** per `tools/*.ts` | MCP-canonical |
| **Portal loop** | `buildChatToolsFromNames(tools_authorized)` from `RETRIEVAL_TOOLS` (`tool_catalogue.ts`) | **EMPTY `{}` for every tool** | engine names |
| **Manifest** | generated (`manifest:build`) | `query_schema` on rich entries; planner uses a compressed view | mixed |

**Portal control flow (verified).** `/consume` always runs `runPlanner()` → B.11 floor pre-execution
→ parallel pre-fetch of `tools_authorized` → then a synthesis tail: `orchestrator.synthesize` |
single-shot `adapter.chat` | `runAgenticLoop(...)` (gated by `R11V2_USE_ADAPTERS` + per-provider
`R11E_*_LOOP`, all live `=true`). The agentic loop is **gap-recovery over the planner's pre-fetched
subset**, not free tool choice. B.11 floor results are pre-injected into system context; the loop has
**no forced-first-call** mechanism.

**Tier (verified minimal on portal).** Not used for tool-gating; only synthesis prompt/disclosure +
a chart-ownership check (`role === 'super_admin'`). MCP side: `auth.ts` rejects keys lacking
`audience_tier`, and the success envelope carries a top-level `audience_tier` field.

**Dead/decayed.** `retrieval_capability_spec.ts` is dead (only its test imports it); `capabilities.ts`
resource hard-codes a stale "21 tools"; orphaned planner path in MCP (`/api/mcp/execute`,
`callPlatform*`); alias cruft + duplicate `msr_sql` in `primitives_registry.ts`.

---

## §2 — The Canonical Tool Contract (the spine)

**One definition per capability**, stored as the source of truth and consumed by both channels:
`canonical_name` · `input_schema` (JSON Schema) · `description` (Claude-tuned, disambiguator-first) ·
`annotations{readOnly,destructive,idempotent,openWorld}` · `role` (entry-point|primitive|raw-read|write|meta) ·
`family` · `cost` (`cost_weight`/`token_cost_hint`) · `engine` (the `getTool` name it dispatches to) ·
`resident_core` (bool) · `data_dependency` · `deprecated_aliases[]`.

**Where it lives.** The manifest (`CAPABILITY_MANIFEST.json`) is the generated store; the edit surface
is file frontmatter + `manifest_overrides.yaml`. **Extend `asset_entry.schema.json`** (today
`additionalProperties:false`, warn-only) to admit the new fields. **Seed `input_schema` + `description`
from the existing MCP Zod schemas** (`platform-mcp/src/tools/*.ts`) — the richest source — converting
Zod → JSON Schema once.

**Both channels generate from it (no hand-maintained lists):**
- **MCP server** — replace the 40 hand-coded `register*()` calls with a single manifest-driven
  registration loop (name + JSON-Schema → Zod via a shared converter + annotations).
- **Portal loop** — `convertRetrievalToolToChatTool` reads the **real** schema + description from the
  contract instead of `normalizeInputSchema({})`. **This fixes the empty-schema bug.**
- **catalog.ts + capabilities.ts** — generated from the contract (kills the 40/57/21 drift).

**Retire, don't extend:** `MCP_TO_RETRIEVAL_TOOL` (name indirection), the alias objects in
`RETRIEVAL_TOOLS`, and `INTERFACE_NORMALIZATION_REGISTER` — the latter consumed **once** as the
canonicalization input (it already declares "MCP name is canonical" + every mismatch), then archived.

**Governance.** Editing a tool's `.ts` rotates its manifest `fingerprint_sha256` +
`last_verified_session/_on` (or `drift_detector` HIGH). MP.5 mirror only trips on L2.5 asset-path
changes; emit `mirror_updates_propagated` at close regardless. Run drift/schema/mirror at close.

**Provider fan-out caveat.** The canonical JSON Schema still flows through each provider's
`adapter.tools()` transform (anthropic/google/openai/deepseek/nvidia) — `normalizeInputSchema` exists
because root-shape requirements differ. The contract is provider-agnostic; the adapters remain the
per-provider translation layer.

---

## §3 — The control-model decision (central; needs native sign-off)

Contract convergence is unambiguous. **How freely the portal LLM selects tools is a separate choice**,
because today the planner gates `tools_authorized` and the loop only recovers within it — unlike MCP's
free selection. Three target models:

- **(A) Keep planner as gate; share contract only.** Lowest change: fix schemas, unify naming, but the
  portal still pre-plans and constrains the loop. Pro: cost/determinism preserved. Con: portal stays
  structurally unlike MCP; two selection models persist.
- **(B) Planner → advisor; loop selects from the gateway (recommended).** The planner stops being a hard
  gate and becomes a lightweight pre-seed (B.11 floor + suggested starters); the agentic loop then selects
  freely from the **full canonical catalog via the gateway** (§6), exactly like MCP. One selection model
  on both channels. B.11 enforced by the shared mechanism (§4). Cost controlled by the gateway's small
  resident core + bounded iterations.
- **(C) Remove planner; pure-agentic both channels.** Maximal convergence; the gateway + B.11 guard fully
  replace the planner. Highest blast radius; defer unless (B) proves the model.

**Recommendation: (B), reachable in stages** — it makes the two channels behave identically for tool
selection, fixes the empty-schema bug, and keeps a thin B.11/efficiency pre-seed without a hard gate.
(C) becomes a later option once (B) is proven on live traffic.

---

## §4 — B.11 unification (one mechanism, both channels)

Today: portal pre-executes a hardcoded floor (`route.ts` 460-504: L2.5 set + dasha `chart_facts_query`)
and injects results into context; MCP enforces via the house-rules resource. Two mechanisms, one invariant.

**Target:** a single **"holistic-read guarantee"** expressed once in the canonical layer and applied
identically: a **forced-first gateway interaction** (the gateway's entry-point returns the holistic
bundle / B.11 floor before free tool selection is permitted) plus a guard that blocks an interpretive
final answer until the floor has been consulted. Same code path feeds both the MCP host and the portal
loop. Any canonical-name rename must update the floor literals + `inferLayer`/`toolStepType` switch
tables in `route.ts` (call out in migration).

---

## §5 — Portfolio structure (families, roles, contract fields)

Carried from v1.1, now expressed in the canonical contract. **Families** (LLM navigates by these):
Foundation · Holistic Synthesis · Discovery · Time & Prediction · Electional · System Lenses ·
Tradition & Adjudication · Ground-truth & Substrate · Governance/Meta. **Roles:** entry-point ·
primitive · raw-read · write · meta (the register's §4 already enumerates the MCP-only set by role —
reuse). **Governing law:** no two tools share an intent slot, but **respect the 6 declared asymmetries**
(`read_classical_text`≠`classical_text_search`, `cross_school_lookup`≠`multi_school_signal_lookup`,
`get_cgm_subgraph`≠`cgm_graph_walk`, `query_divisional_chart`≠`divisional_query`,
`query_remedial_mantras`≠`remedial_codex_query`, `muhurta_finder`≠`query_muhurat`). **Annotation matrix:**
retrieval/raw-read/observability/health → readOnly+idempotent, openWorld:false; `log_prediction`/
`flag_disagreement` → write, non-idempotent; `record_outcome` → write, idempotent.

---

## §6 — Dynamic loading / gateway (the convergence linchpin)

The gateway is now **shared infrastructure for both channels**, and the bridge to control-model (B):

- **Resident core (~12):** family entry-points (`chart_summary`, `holistic_bundle`, `multi_school_bundle`),
  `vector_search`, `query_chart_facts`, the gateway tools (`search_tools`, `invoke_tool`), observability
  (`get_trace`, `list_recent_queries`), and the three writes.
- **`search_tools(query|family)`** returns matching canonical-contract entries **with full JSON Schema**
  (the manifest now carries it). **`invoke_tool(name, params)`** dispatches and **validates params
  server-side against the contract schema** (recovers per-tool validation a generic dispatcher loses).
- **Now (stateless-safe):** gateway works on MCP (stateless server) and in the portal loop without
  protocol `listChanged`. **Later:** protocol-native `listChanged` (stateful sessions + SSE + Memorystore)
  for MCP hosts that honor it. SDK 1.29.0 already supports it; only the stateless server config blocks it.
- The gateway is also where the **B.11 forced-first guarantee** (§4) lives, so both channels inherit it.

---

## §7 — Tier rip-out (full surface, both channels)

- **MCP `auth.ts`** — relax the `audience_tier`-required gate (and the `/api/mcp/keys/validate` contract)
  or every key fails auth; drop the envelope `audience_tier` field (response-shape change — check consumers/bench).
- **MCP `tier_catalog.ts`** — delete (OPS/SYNTHESIS sets, suffixes, `getCatalogForTier`); remove `server.ts`
  `tierDesc` wiring; bundle `tier` cache-key component; cosmetic `X-MCP-Audience-Tier` headers.
- **URL-key restriction** (`?api_key=` super_admin-only) — re-ground as a pure security control (see §17).
- **Portal** — tier isn't tool-gating; keep the **chart-ownership** check as an identity/authorization
  control (not a tier), and collapse synthesis/disclosure tier-conditioning to a single profile.
- **Tests:** `tier_catalog.test.ts`, `server_tier_visibility.test.ts`, `mcp_visibility.integration.test.ts`,
  `audience_tier` in `bench/scenarios/*.yaml`.

---

## §8 — Resources

Five resources (`resources/index.ts`). **House-rules collapse is near-free** (endpoint already serves
`super_admin`; `getHouseRulesForTier` unused) — keep one `house_rules.md`, delete the 3 variants, drop the
`VARIANTS` map. **`capabilities.ts` becomes generated** from the contract (today hard-codes stale "21").
`chart-overview`/`chart-snapshot` tier comments are cosmetic.

---

## §9 — Per-tool disposition (contract-level; applies to BOTH channels at once)

Verdicts: KEEP · MERGE · PROMOTE · DE-REGISTER · FOLD · DEDUP · BACKFILL. Because the contract is unified,
a merge/rename happens **once** and both channels inherit it (no Layer-A/Layer-B split). Engine-name
changes still ripple to the B.11 floor literals + switch tables (§4/§10).

- **Foundation:** `chart_summary` KEEP(entry); `query_chart_facts` KEEP; `query_divisional_chart` KEEP +
  FOLD `query_dasamsha_career`/`query_shashtiamsha`/`query_drekkana_drishti`/`cross_varga_dignity_query`;
  PROMOTE `get_shadbala_full`, `get_planet_avastha`.
- **Holistic Synthesis:** `holistic_bundle` KEEP(entry); MERGE `query_signals`+`msr_sql` (one engine —
  update bundle fan-out + B.11 floor literal); MERGE `query_ucn_walk`+`query_cdlm_lookup`+`query_rm_walk`
  → `synthesis_walk(layer:)`; `get_cgm_subgraph` KEEP + BACKFILL; PROMOTE/FOLD `query_msr_aggregate`.
- **Discovery:** MERGE `pattern_register`+`resonance_register`+`cluster_atlas`+`contradiction_register`
  → `discovery_register(kind:)` (note: 4 are B.11 floor members — update floor + switch tables).
- **Time & Prediction:** `query_dasha_periods` KEEP; reconcile `query_ephemeris`+`temporal` (merge under
  `mode` or keep distinct — §17); `query_transit_event` KEEP; PROMOTE `query_transits_over_natal`,
  `query_yogas_active_now`, `query_planetary_period_predictions`, `query_eclipse_transits`, `query_planet_war`;
  `timeline_query`+`query_signal_state` KEEP + BACKFILL; `interpret_current_dasha` → prompt template.
- **Electional:** `query_panchanga`, `muhurta_finder` KEEP; PROMOTE `tara_balam_for_native`, `chandra_balam_for_native`.
- **System Lenses:** KEEP `kp_query` + `query_kp_ruling_planets` (sharpen disambiguator; don't merge);
  DE-REGISTER `query_jaimini_drishti` (stub); PROMOTE `query_jaimini_chara_dasha`; DEDUP `jaimini_chara_dasha[_full]`;
  `query_varshphal` KEEP; PROMOTE `saham_query`.
- **Tradition:** `multi_school_bundle` KEEP(entry); `cross_school_lookup`, `read_classical_text` KEEP;
  MERGE `query_remedial_mantras`+`query_remedies_prescribed`; FOLD `classical_attribution_lookup`,
  `convergence_score_lookup`; `classical_disclosure_filter` REMOVE-with-tiers.
- **Ground-truth:** `lel_query`, `vector_search`, `read_asset` KEEP; PROMOTE/FOLD `domain_report_query`;
  `query_v7_additions` INVESTIGATE.
- **Governance/Meta:** observability + health + 3 writes KEEP; FOLD `manifest_query`; catalog/`capabilities`
  generated; `tool_catalogue.ts` becomes the contract→ChatTool builder (schema-aware).

---

## §10 — Migration / deprecation

Use the (now-temporary, dated) name-indirection as a **migration shim**: during transition, old names
resolve to canonical via an alias table with a hard removal date, then deleted — the additive-alias pattern
the register already uses. `search_tools` flags `deprecated:true`. **Engine renames must mirror-update**
the B.11 floor literals + `inferLayer`/`toolStepType` switch tables in `consume/route.ts`, or the floor
breaks silently.

---

## §11 — Eval impact (redo against the unified contract)

Accept re-baselining (native-approved). Accuracy golden is **category-keyed** (survives renames) — breaks
only if `CHART_FACTS_CATEGORIES` or `query_chart_facts` shape changes, or `chart_summary`/`query_chart_facts`
rename. **Bench is tool-name-keyed** — regenerate when named tools/scenarios change. `tool_descriptions.test.ts`
lint stays green. **Fixing the portal empty-schema bug is expected to improve `answer:eval`** (chart
`362f9f17`) — run it once per consolidated batch, not per-PR. Add a tool-selection-accuracy metric.

---

## §12 — Naming & dead-code

Canonicalize names once from the register ("MCP name canonical"), then archive the register. Consistent
verb scheme (`query_` parametric read · `get_` single fetch · `read_` raw doc · `*_bundle` composite ·
bare-noun reserved for gateway/meta). **Delete:** `retrieval_capability_spec.ts` (dead), the MCP orphaned
planner path, `MCP_TO_RETRIEVAL_TOOL` + alias objects (post-migration), `capabilities.ts` hand-coding.

---

## §13 — Sequence (contract spine first)

0. **Canonical contract spine** — extend manifest schema + fields; seed input schemas from MCP Zod →
   JSON Schema; generate `catalog.ts` + `capabilities.ts`; **rip out tiers** (§7); remove dead code;
   wire fingerprint/drift/mirror compliance.
1. **Dual-channel generation** — MCP server registers from the contract; portal `tool_catalogue` reads
   real schemas (fixes empty-schema bug). Both channels now share one contract.
2. **Per-tool contract enrichment** — annotations, description template + lint, `response_format`, errors.
3. **Reconciliation** — merges/promotions/de-registrations/folds (§9) once, inherited by both channels;
   deprecation shim (§10).
4. **Gateway** — `search_tools`+`invoke_tool` + resident core; **B.11 forced-first guarantee** (§4) lives here.
5. **Control-model (B)** — planner → advisor; portal loop selects freely via the gateway (§3).
6. **Parity promotions + data backfills** — expose engine-only capabilities; CGM/timeline/signal_states.
7. **Native `listChanged`** — stateful sessions + SSE + session store.
8. **Prompts + eval gates** — `prompts` for canned workflows; blocking contract tests; re-baseline `answer:eval`.

**Implement first = Phase 0+1 (the contract spine + dual-channel generation).** It establishes the single
source of truth, fixes the live empty-schema bug, and is prerequisite to everything.

---

## §14 — Success metrics

One contract powering both channels (zero `MCP_TO_RETRIEVAL_TOOL`/alias/register entries remaining);
`catalog`/`capabilities` counts = manifest count (zero drift); portal agentic-loop tools carry real
schemas (0 empty schemas); resident core ≤ ~12; bench green post-regeneration; `answer:eval`
tool-selection accuracy ≥ baseline (target: improved by the schema fix); one B.11 mechanism, not two.

---

## §15 — Anthropic-specific notes

Keep the resident-core list **stable/ordered** (R11.D prompt-cache prefix). Reserve `sampling` as the
zero-key path if server-side model help is ever wanted. Declare per-tool `outputSchema` so Claude parses
results deterministically. The gateway pattern is Anthropic's recommended approach for large surfaces and
now serves both channels.

---

## §16 — Open decisions for native

1. **Control model (§3) — the big one:** approve **(B)** planner→advisor + free gateway selection
   (recommended, staged), or **(A)** keep the planner gate, or **(C)** remove the planner now?
2. **B.11 mechanism (§4):** approve a single forced-first gateway guarantee replacing the dual mechanism?
3. **Security (§7):** with tiers gone, every key gains write/ops tools and the `?api_key=` URL form loses
   its super_admin gate — confirm acceptable; how to re-ground the URL-key restriction (e.g. per-key scopes)?
4. **`query_ephemeris`+`temporal`** — merge under `mode`, or keep distinct?
5. **Merge granularity (§9)** — approve the MERGE set as proposed, or review each before commit?
6. **INVESTIGATE** — `query_v7_additions`, `domain_report_query` final disposition (quick engine read).

---

*End of TOOL_PORTFOLIO_PLAN v1.2 (DRAFT — for native review). No implementation performed.
Supersedes v1.1 and v1.0.*

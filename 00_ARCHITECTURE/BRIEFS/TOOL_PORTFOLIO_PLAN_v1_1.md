---
canonical_id: TOOL_PORTFOLIO_PLAN
version: 1.1
status: DRAFT — FOR NATIVE REVIEW
supersedes: TOOL_PORTFOLIO_PLAN_v1_0.md (v1.0 — archive on approval of v1.1)
date: 2026-05-27
author: Cowork planning session (no implementation; plan only)
scope: MCP/LLM tooling portfolio — structure, reconciliation, dynamic loading
related:
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  - 00_ARCHITECTURE/manifest_overrides.yaml
  - 00_ARCHITECTURE/INTERFACE_NORMALIZATION_REGISTER_v1_0.md  # at v1.1
  - platform/src/scripts/manifest/build.ts
  - platform/src/lib/schemas/asset_entry.schema.json
  - platform/scripts/governance/{drift_detector,schema_validator,mirror_enforcer}.py
  - platform/src/lib/retrieve/index.ts                       # RETRIEVAL_TOOLS (55)
  - platform/src/lib/mcp/primitives_registry.ts              # MCP_TO_RETRIEVAL_TOOL
  - platform/src/app/api/chat/consume/route.ts               # B.11 floor literals
  - platform-mcp/src/{server.ts,auth.ts,types.ts}
  - platform-mcp/src/resources/* , platform-mcp/src/bundles/*
  - platform-mcp/test/accuracy/* , platform-mcp/test/bench/*
note: >
  STRATEGIC PLAN, not an implementation brief. v1.1 folds in the self-audit findings
  and three deep-research passes (manifest/governance, dual-channel, plumbing/eval).
  Executor briefs are cut per-phase only after this plan is approved.
---

# Tool Portfolio Reconciliation — Strategic Plan v1.1

## §0 — Purpose, locked decisions, and what changed from v1.0

**Goal.** Turn the accreted tool surface into a coherent **portfolio** an LLM (Anthropic/Claude-
optimized) can navigate without trial-and-error, and keep it coherent over time.

**Locked with native:** full reconcile · tiers ripped out entirely · dynamic loading both
(gateway now, protocol-native `listChanged` later) · sequencing per best practice (manifest spine first).

**What changed in v1.1 (from audit + research):**
1. The manifest already exists and is **generated** — v1.0's "create a manifest" is replaced by
   "extend `CAPABILITY_MANIFEST.json` + its schema, and generate the catalog from it" (§2).
2. **Two-layer reconciliation scope** added (§3) — most work is MCP-**wrapper-only** with zero portal
   impact; only true engine merges/removals touch the shared portal channel. This is the key de-risk.
3. Tier rip-out surface corrected — the `auth.ts` validation gate and envelope field are load-bearing (§6).
4. Resources, migration/deprecation, eval-invalidation, naming, dead-code, and success metrics added
   (§7, §9, §10, §11, §12, §14).
5. Disposition revised to respect `INTERFACE_NORMALIZATION_REGISTER`'s already-decided distinctions (§8).

---

## §1 — Landscape truth (verified)

Four inventories, none agreeing — the root of "tools randomly popping up":

| Inventory | Where | Count (verified) |
|---|---|---|
| Retrieval **engines** | `platform/src/lib/retrieve/index.ts` `RETRIEVAL_TOOLS` | **55** (53 engines + 2 alias objects) |
| Manifest **tool entries** | `CAPABILITY_MANIFEST.json` | 268 entries; **79 `retrieval_tool`**; channel split ~29 both / 28 mcp / 22 portal |
| MCP **registered tools** | `platform-mcp/src/server.ts` | **40** (→ ~30 distinct engines via the map) |
| Catalog **lint list** | `catalog.ts` | "**57**" (⊋ registered 40) |
| `capabilities.ts` resource | hard-coded literal | "**21**" (stale, wrong) |

Confirmed pathologies: true redundancy (`query_signals` + `msr_sql` → same engine `msr_sql`); alias
cruft in the whitelist; stubs/empty-data tools registered as functional (`query_jaimini_drishti` stub;
`get_cgm_subgraph`/`timeline_query`/`query_signal_state` over empty tables); and a ~15-engine parity gap
(engines built but with no MCP tool). Plus **`retrieval_capability_spec.ts` is dead code** (only its own
test imports it) and `capabilities.ts` is hand-coded and stale.

---

## §2 — Vocabulary & the manifest (REVISED — extend, don't invent)

The four confused terms resolve to **one generated source of truth + two derivations + one deletion**:

- **Manifest = `CAPABILITY_MANIFEST.json`, already the governed source of truth.** It is **generated**
  by `npm run manifest:build` (`platform/src/scripts/manifest/build.ts`) from (a) file frontmatter and
  (b) `manifest_overrides.yaml` `additional_entries:`. **Do not hand-edit the JSON** — it is overwritten
  on rebuild. The real edit surface is frontmatter + the overrides YAML.
  - It already carries the rich fields we need indirectly: `tool_name`, `tool_description`,
    `query_schema` (input JSON-schema), `expose_to_planner`, `expose_to_chat`, `cost_weight`,
    `token_cost_hint`, `preferred_for`, `always_required`, `layer`, `fingerprint_sha256`.
  - **Fields to ADD:** `family`, `role` (entry-point | primitive | raw-read | write | meta),
    `annotations{readOnly,destructive,idempotent,openWorld}`, `response_format` (output-shape control).
    Reuse `always_required` (or add `resident_core`) for the always-on core; `expose_to_planner` already
    gates portal visibility.
  - **Schema must be extended too:** `platform/src/lib/schemas/asset_entry.schema.json` is
    `additionalProperties:false` and only whitelists 15 props; today rich tool fields validate-**warn**
    (build proceeds). New fields require adding them to this schema or they stay warn-only.
- **Registry = runtime liveness** (enabled/healthy/version/coverage), keyed to the manifest.
- **Catalog = generated** from the manifest — `catalog.ts` AND the `capabilities.ts` resource both become
  generated artifacts, never hand-maintained (this kills the 40/57/21 drift permanently).
- **Tier = deleted** (§6).

**Governance integration (mandatory for the executor).** Editing a tool's source `.ts` requires rotating
that manifest entry's `fingerprint_sha256` + `last_verified_session`/`_on`, or `drift_detector.py` raises
a HIGH `fingerprint_mismatch` (exit-2). Mirror pair **MP.5** (`CAPABILITY_MANIFEST.json` ↔ `.geminirules`
L2.5 path block) only trips on L2.5 **asset-path** changes — tool-only edits likely don't, but the session
close-checklist must still emit `mirror_updates_propagated`. Run `drift_detector` / `schema_validator` /
`mirror_enforcer` (all default manifest-mode) at close.

---

## §3 — Reconciliation scope: two layers (KEY DE-RISK; resolves audit C2)

The engines are shared by **two channels**: the MCP sidecar and the portal `/consume` LLM planner
(which reads the manifest's `expose_to_planner` tools and executes via `getTool()`). Therefore:

**Layer A — MCP-portfolio (wrapper-only; ZERO portal impact).** MCP names are decoupled from engine
names by `MCP_TO_RETRIEVAL_TOOL` (`primitives_registry.ts`). Everything below is achievable by editing
only that map + the `platform-mcp/` sidecar, leaving engines and the portal untouched:
- rename / regroup MCP-facing tools; assign families/roles; add annotations + descriptions;
- **merge at the wrapper** — collapse two MCP names that hit one engine (signals + msr_sql), or expose a
  parameterized dispatcher MCP tool (`discovery_register(kind:)`, `synthesis_walk(layer:)`) that fans out
  to several engines internally;
- build the gateway (`search_tools` / `invoke_tool`);
- deprecation aliases (old MCP name → same engine) for a migration window.

**Layer B — engine-level (touches the shared portal; minimize + coordinate).** Only these require care:
- changing an engine's `.name`, merging two engines into one, or **removing** an engine;
- blast radius: `retrieve/index.ts`, `CAPABILITY_MANIFEST.json` + `manifest_overrides.yaml`, and the
  **B.11 floor string literals** in `consume/route.ts` (`'msr_sql'`,`'vector_search'`,`'pattern_register'`,
  `'cgm_graph_walk'`,`'chart_facts_query'`), plus `mcp_tool_executor.ts`. A missed literal breaks the floor
  silently.

**Recommendation:** do **Layer A in full first** (it captures ~all of the portfolio value at near-zero
risk), and treat Layer B as a small, explicitly-coordinated follow-on limited to genuine engine dedup
(e.g. retiring stub-engines). Most v1.0 "merges" are Layer A, not Layer B.

---

## §4 — Portfolio structure (framework)

**Axis 1 — Family** (LLM navigates by this; the practitioner's reading order):
Foundation · Holistic Synthesis · Discovery · Time & Prediction · Electional · System Lenses ·
Tradition & Adjudication · Ground-truth & Substrate · Governance/Meta.

**Axis 2 — Role** (fixed 5-value vocabulary): entry-point/composite · primitive · raw-read · write · meta.
*(Note: `INTERFACE_NORMALIZATION_REGISTER §4` already enumerates the MCP-only set by exactly these roles —
reuse it.)* Plus per-tool: **access** (read/write, idempotent), **breadth/cost** (reuse `cost_weight`/
`token_cost_hint`), **data-dependency** (for functional-vs-stub).

**Governing law:** no two tools occupy the same intent slot — but respect the **6 declared asymmetries**
in the register (`read_classical_text`≠`classical_text_search`, `cross_school_lookup`≠`multi_school_signal_lookup`,
`get_cgm_subgraph`≠`cgm_graph_walk`, `query_divisional_chart`≠`divisional_query`,
`query_remedial_mantras`≠`remedial_codex_query`, `muhurta_finder`≠`query_muhurat`); these are settled non-merges.

**Per-tool contract (lint-enforced via `tool_descriptions.test.ts`):** disambiguator-first description
(one-line "right tool when…" → what/returns → when-to-prefer/NOT → input example → output preview → cost);
MCP annotations; `response_format` (concise|detailed) + pagination defaults; structured errors
(class+remediation+retry); uniform envelope; declared data-dependency.

**Annotation matrix:** all retrieval/raw-read/observability/health → `readOnly:true, destructive:false,
idempotent:true, openWorld:false`. `log_prediction`/`flag_disagreement` → `readOnly:false, idempotent:false`.
`record_outcome` → `readOnly:false, idempotent:true`. (Single closed corpus/chart → `openWorld:false` always.)

---

## §5 — Dynamic tool loading (both; Anthropic-optimized)

**Finding (verified):** not available today — SDK **1.29.0** fully supports it (`tools.listChanged:true`;
`registerTool` handles `.enable/.disable/.update/.remove` → `sendToolListChanged()`), but the server is
deliberately **stateless** (`sessionIdGenerator: undefined`; fresh `McpServer`+40 tools per POST;
`GET /mcp` → 405). Cloud Run (min-1, conc-80, horizontal) makes stateful sessions need sticky routing or
externalized session state.

**Gateway baseline (now) — stateless-safe, matches Anthropic "tool search / code execution with MCP":**
resident core + `search_tools(query|family)` (returns matching manifest entries — **`query_schema` is
already in the manifest**, so full input schemas are available to the model) + `invoke_tool(name,params)`
(generic dispatcher). **H5 mitigation:** `search_tools` returns the full JSON-schema and `invoke_tool`
validates `params` server-side against the manifest schema, recovering the per-tool validation that a
generic dispatcher would otherwise lose.

**Protocol-native `listChanged` (later):** stateful sessions (`sessionIdGenerator: randomUUID()`) + SSE
channel on `GET /mcp` + externalized session store (Memorystore) for Cloud Run; register core at attach,
`.enable()` families on demand, push `tools/list_changed`. Layered on the gateway, not a replacement.

---

## §6 — Tier rip-out (full surface; corrected)

Tier no longer gates registration (GISMCP R1 made all tools unconditional). It still touches — all must go:
- **`auth.ts:98` — load-bearing.** Auth returns `null` unless the key-validation response has a truthy
  `audience_tier`. Removing tiers requires relaxing this gate (and/or the platform `/api/mcp/keys/validate`
  contract) **or every key fails auth**. Highest-risk item in the rip-out.
- **Envelope field.** `McpEnvelopeSuccess.audience_tier` is a top-level success field — dropping it is a
  response-shape change; check `get_trace`/consumers and bench fixtures that echo it.
- **`tier_catalog.ts`** — entire module (`OPS_TOOLS`, `SYNTHESIS_TOOLS`, suffixes, `getCatalogForTier`)
  collapses; `server.ts` L167-189 `tierDesc()` wiring removed.
- **URL-key restriction** (`server.ts:134-157`, `?api_key=` → super_admin only) — re-ground as a pure
  security control, decoupled from tier (see §15 / audit M5).
- **Bundles** — remove `tier` from `HolisticBundleParams`/`MultiSchoolBundleParams` and the `cache.ts`
  `computeCacheKey` (changes every bundle cache key; acceptable at 5-min TTL).
- **Resources** — `chart_snapshot.ts`/`capabilities.ts` send a cosmetic hardcoded `X-MCP-Audience-Tier:
  super_admin` header (drop); house-rules collapse in §7.
- **Tests to update:** `tier_catalog.test.ts`, `server_tier_visibility.test.ts`,
  `integration/mcp_visibility.integration.test.ts`, and `audience_tier` in `bench/scenarios/*.yaml`.

---

## §7 — Resources (newly first-class)

Five resources registered (`resources/index.ts`): `chart-snapshot`, `chart-overview`, `house-rules`,
`capabilities`, `school-conventions`.
- **House-rules collapse is nearly free.** Four variant files exist but the endpoint **already always serves
  `super_admin`** (`house_rules.ts:63`); `getHouseRulesForTier()` is exported-but-unused. Action: keep one
  `house_rules.md`, delete `acharya/client/public_redacted`, drop the `VARIANTS` map.
- **`capabilities.ts` must become generated.** It hard-codes the tool list + a stale "21 total"; regenerate
  from the manifest/`CATALOG` (or from `tool_health`). It is the single biggest count-drift hazard.
- `chart-overview`/`chart-snapshot` "tier-conditioned length" is comment-only (no real variant logic).

---

## §8 — Per-tool disposition (revised; Layer A unless tagged Ⓑ)

Verdicts: KEEP · MERGE-A (wrapper merge, no portal impact) · MERGE-Ⓑ (engine merge, portal-coordinated) ·
PROMOTE (engine exists, expose as MCP tool) · DE-REGISTER (stub/dead) · FOLD (param/recipe of a broader tool) ·
DEDUP (alias cruft) · BACKFILL (empty data). Names follow `INTERFACE_NORMALIZATION_REGISTER` (MCP-name-canonical).

**Foundation** — `chart_summary` KEEP(entry); `query_chart_facts` KEEP; `query_divisional_chart` KEEP +
FOLD in `query_dasamsha_career`(D10)/`query_shashtiamsha`(D60)/`query_drekkana_drishti`(D3)/`cross_varga_dignity_query`;
PROMOTE `get_shadbala_full`, `get_planet_avastha`.

**Holistic Synthesis** — `holistic_bundle` KEEP(entry); **MERGE-A** `query_signals`+`msr_sql` (same engine;
**update holistic-bundle fan-out route**, which calls `query_signals` by literal); **MERGE-A**
`query_ucn_walk`+`query_cdlm_lookup`+`query_rm_walk` → `synthesis_walk(layer:)` dispatcher; `get_cgm_subgraph`
KEEP + BACKFILL; PROMOTE/FOLD `query_msr_aggregate`.

**Discovery** — **MERGE-A** `pattern_register`+`resonance_register`+`cluster_atlas`+`contradiction_register`
→ `discovery_register(kind:)` (4 engines, 1 wrapper dispatcher; engines untouched).

**Time & Prediction** — `query_dasha_periods` KEEP; **reconcile** `query_ephemeris`+`temporal` (live-sidecar vs
positional-SQL — keep distinct w/ sharpened disambiguator, or wrapper-merge under `mode`); `query_transit_event`
KEEP; PROMOTE `query_transits_over_natal`, `query_yogas_active_now`, `query_planetary_period_predictions`,
`query_eclipse_transits`, `query_planet_war`; `timeline_query`+`query_signal_state` KEEP + BACKFILL;
`interpret_current_dasha` → **prompt template**, not a tool.

**Electional** — `query_panchanga` KEEP; `muhurta_finder` KEEP; PROMOTE `tara_balam_for_native`,
`chandra_balam_for_native`.

**System Lenses** — KEEP both `kp_query` + `query_kp_ruling_planets` (sharpen FORENSIC-vs-computed
disambiguator; do NOT merge); **DE-REGISTER** `query_jaimini_drishti` (stub) until engine built; PROMOTE
`query_jaimini_chara_dasha`; DEDUP `jaimini_chara_dasha`/`jaimini_chara_dasha_full` aliases; `query_varshphal`
KEEP; PROMOTE `saham_query`.

**Tradition & Adjudication** — `multi_school_bundle` KEEP(entry); `cross_school_lookup` KEEP;
`read_classical_text` KEEP (distinct from `vector_search` — different corpus; declared asymmetry); **MERGE-A**
`query_remedial_mantras`+`query_remedies_prescribed` → one remedies tool; FOLD `classical_attribution_lookup`,
`convergence_score_lookup`; `classical_disclosure_filter` REMOVE-with-tiers (§6).

**Ground-truth & Substrate** — `lel_query` KEEP; `vector_search` KEEP (resident core); `read_asset` KEEP;
PROMOTE/FOLD `domain_report_query`; `query_v7_additions` INVESTIGATE.

**Governance/Meta** — `get_trace`, `list_recent_queries`, `tool_health`, `data_coverage`, `log_prediction`,
`record_outcome`, `flag_disagreement` KEEP; FOLD `manifest_query`; `tool_catalogue`/`capabilities.ts` →
generated catalog (§2/§7).

**Dead code (remove):** orphaned planner path (`/api/mcp/execute`, `/api/mcp/plan`, `callPlatform`,
`callPlatformPlan`); alias dupes + duplicate `msr_sql` in `primitives_registry.ts`;
**`retrieval_capability_spec.ts`** (dead — only its test imports it); `capabilities.ts` hand-coding.

**Resident core (always-on; §15 confirm):** the family entry-points (`chart_summary`, `holistic_bundle`,
`multi_school_bundle`), `vector_search`, `query_chart_facts`, the gateway tools (`search_tools`,
`invoke_tool`), observability (`get_trace`, `list_recent_queries`), and the three writes. ~12 resident;
the rest discovered on demand.

---

## §9 — Migration / deprecation (audit H1)

MCP-name changes never hard-break: the `MCP_TO_RETRIEVAL_TOOL` indirection makes a retired name a
**deprecated alias** (old name → same engine) for a deprecation window, then removal — the exact additive-alias
pattern `INTERFACE_NORMALIZATION_REGISTER` already uses for `query_chart_facts`/`query_varshphal`. Document
each rename in the register; `search_tools` results flag `deprecated:true` to steer the model off old names.

---

## §10 — Eval impact (audit H2; bounded)

- **Accuracy golden is category-keyed, NOT tool-name-keyed** — survives renames/merges. Only breaks if
  `CHART_FACTS_CATEGORIES` changes, `query_chart_facts` response shape changes, or `chart_summary`/
  `query_chart_facts` are renamed (`cross_scenario.test.ts` uses literal names + 27-category asserts).
- **Bench IS tool-name-keyed** — asserts named tools + round-trip counts (`chart_summary`, `query_chart_facts`,
  `holistic_bundle`, + `bench/scenarios/*.yaml`). Any rename/merge of those requires regenerating bench.
- **`tool_descriptions.test.ts`** lints `catalog.ts` (disambiguator + "When to prefer:" + ≤1200 chars) — every
  add/rename must keep this green.
- **`answer:eval`** (chart `362f9f17`) runs **once per consolidated batch** per native discipline — re-baseline
  after the reconciliation batch, not per-PR.

---

## §11 — Naming convention (audit M1/C3)

Adopt `INTERFACE_NORMALIZATION_REGISTER`'s "MCP name is canonical" + a consistent scheme: a small verb set
(`query_` for parametric reads, `get_` for single-object fetch, `read_` for raw documents, `*_bundle` for
composites, bare-noun reserved for the gateway/meta). Thread every rename through the register; do not
introduce a name that conflicts with an existing engine `.name`.

---

## §12 — Sequence (Anthropic-optimized; manifest spine first)

0. **Manifest spine** — extend `asset_entry.schema.json` + manifest fields (`family`/`role`/`annotations`/
   `response_format`); generate `catalog.ts` + `capabilities.ts` from the manifest; **rip out tiers** (§6);
   remove dead code (§8/§12-list); wire fingerprint/drift/mirror compliance (§2).
1. **Per-tool contract** — annotations, description template + lint, `response_format`, structured errors.
2. **Layer-A reconciliation** — wrapper merges/regroups/de-registrations/folds/dedups (§3/§8); deprecation aliases (§9).
3. **Gateway baseline** — `search_tools`+`invoke_tool` over the manifest; resident core (§8).
4. **Parity promotions** — expose engine-only capabilities, highest-value families first (Time, Electional).
5. **Data backfills** — CGM graph, L5 timeline, signal_states (so health/coverage reads true).
6. **Layer-B engine consolidation** — only genuine engine dedup, portal-coordinated (B.11 floor literals).
7. **Protocol-native `listChanged`** — stateful sessions + SSE + session store.
8. **Prompts + eval gates** — `prompts` for canned workflows (incl. `interpret_current_dasha`); per-tool
   contract tests (blocking) + functional/coverage gate; re-baseline `answer:eval`.

**Implement first = Phase 0 (the spine).** Lowest astrological risk, highest leverage, prerequisite to all.

---

## §13 — Success metrics (audit M6)

Target resident-core ≤ ~12 tools; total distinct MCP tools reduced from 40 (with overlaps) toward a
fully-distinct set; `capabilities.ts`/`catalog.ts` count = manifest count (zero drift); every tool passes the
contract lint; bench green post-regeneration; `answer:eval` (chart 362f9f17) tool-selection accuracy ≥ current
baseline (no regression) with the gateway in place.

---

## §14 — Anthropic-specific notes

- **Prompt caching (R11.D live):** the tool-list prefix is in the cached block — keep the resident core
  **stable/ordered**; regenerating the catalog churns the cache, so batch catalog changes.
- **`sampling`** is the MCP-native way to get model help with **zero server-side key** — the correct future
  path if any server-side planning/synthesis is ever wanted (preserves the zero-LLM invariant).
- **`outputSchema`/structured content** — declare per-tool output schema (M7) so Claude parses results
  deterministically; pairs with `response_format`.

---

## §15 — Open decisions for native

1. **Scope confirm (audit C2):** approve "Layer A in full first, Layer B minimal + coordinated" (§3)?
   (Recommended — captures the value at near-zero portal risk.)
2. **Security (audit M5):** with tiers gone, every authenticated key gains the write tools
   (`log_prediction`/`record_outcome`/`flag_disagreement`) + ops tools, and the `?api_key=` URL form is no
   longer super_admin-gated. Confirm acceptable, and how to re-ground the URL-key restriction as a pure
   security control.
3. **`query_ephemeris`+`temporal`** — wrapper-merge under `mode`, or keep distinct with a sharpened disambiguator?
4. **Merge granularity** — approve the §8 MERGE-A set as proposed, or review each before commit?
5. **INVESTIGATE items** — `query_v7_additions`, `domain_report_query` final disposition (need a quick engine read).

---

*End of TOOL_PORTFOLIO_PLAN v1.1 (DRAFT — for native review). No implementation performed. Supersedes v1.0.*

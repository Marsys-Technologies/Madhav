---
canonical_id: TOOL_PORTFOLIO_PLAN
version: 1.3
status: DRAFT — IMPLEMENTATION PLAN, READY FOR PER-PHASE EXECUTOR BRIEFS
supersedes: TOOL_PORTFOLIO_PLAN_v1_2.md (and v1.1, v1.0) — archive on approval
date: 2026-05-27
author: Cowork planning session (no implementation; plan only)
evidence_base: 00_ARCHITECTURE/INVESTIGATION/TOOL_PORTFOLIO_REALITY_REPORT.md (read in full)
scope: Unified tool contract across MCP + portal agentic loop; reconciliation; gateway; B.11; tier excision
note: >
  v1.3 is the implementation plan, grounded entirely in the verified reality report. Every phase
  becomes a separate CLAUDECODE_BRIEF for Claude Code execution. Facts here are cited from the report;
  this doc does not re-derive them.
---

# Tool Portfolio — Implementation Plan v1.3

## §0 — Locked decisions

- **Unified tool contract** across both channels (MCP sidecar + portal agentic loop).
- **Schema home = a shared Zod schema module** both channels import; manifest `query_schema` backfilled
  from it (Zod is the schema source of truth; manifest is the metadata source of truth).
- **Full canonical rename in one atomic batch** (not permanent aliases) — gated by the §14.2 checklist.
- **B.11 adapter-path citation gap = early standalone fix** (it is a live production governance hole).
- **Tiers ripped out entirely** (access + metadata + DB + disclosure subsystem).
- **Dynamic loading: gateway now, native `listChanged` later.**
- **Control model = B-surgical**: planner stays as the B.11 floor + accounting authority; the loop's
  catalog is *widened to the full set via the gateway* on top of the planner floor (full planner removal
  deferred — 15+ subsystems depend on `tools_authorized`, report §6.4).

## §1 — Verified foundation (authoritative; from the reality report)

- **40** tools registered in `server.ts` (authoritative). **57** entries in `catalog.ts` = 40 + **17
  written-but-unregistered ghost tools** (report §3B). **55** engines in `RETRIEVAL_TOOLS`. **79**
  `retrieval_tool` manifest entries (aspirational, not a live registry).
- **All 79 manifest `query_schema` fields are null** — the manifest carries **zero** usable tool input
  schemas today (§4.5). The Zod schemas in `platform-mcp/src/tools/*.ts` are the only real source.
- **The portal agentic loop emits empty tool schemas** (`normalizeInputSchema({})`, §8.3) — a live
  quality bug fixed by Phase 3.
- **The live adapter/agentic path has NO citation gate** (`validateCitationsForStream` is orchestrator-
  only, §7.3) — live B.11 hole, fixed by Phase 1.
- **`tool_descriptions.test.ts` asserts `toHaveLength(22)` and FAILS now** (catalog has 57, §4.4) — the
  catalog has no working CI gate today.
- **`SURGICAL_TOOLS` has 32 duplicates** (`msr_sql` ×4, §4.3); pass-through self-aliases are redundant.
- **Confirmed dead:** `retrieval_capability_spec.ts`; orphaned `/api/mcp/execute` + `callPlatform()/
  callPlatformPlan()` (§13).
- **7 tools use `.transform`/`.refine`** (won't round-trip JSON-Schema losslessly, §5.4) → the shared
  source must be Zod, with JSON-Schema as a generated projection.
- **Rename blast radius = 12 surfaces** incl. runtime-loaded `PLANNER_PROMPT_v2_0.md` (47 `msr_sql`
  hits) + DB `capability_tool_registry` re-seed + 4 name-keyed `route.ts` tables (§11, §14.2).
- **Tier surface** spans DB (migrations 070+117), an entire `platform/src/lib/disclosure/` module + UI,
  all `/api/mcp/*` routes, the `X-MCP-Audience-Tier` header on every outbound MCP call, two hard-403
  health routes, and the **`acharya` vs `acharya_reviewer` spelling split** (§9).

**Flags to confirm during execution (cheap):** (a) `answer:eval` existence (`platform/package.json` →
`scripts/answer_eval.ts` per an earlier pass; this pass didn't find it); (b) `query_remedies_prescribed`
vs `remedial_codex_query` — distinct siblings or layered? **Confirm before any merge** (§10.4); (c)
`capabilities.ts` confirmed dynamic, not stale.

## §2 — Target architecture

One **canonical tool contract**: `canonical_name` + Zod `input_schema` (shared module) + Claude-tuned
`description` + `annotations` + `role` + `family` + `cost` + `engine` + `resident_core` + `data_dependency`.
- **Schema SoT:** a shared Zod module imported by (a) the MCP server registration and (b) the portal
  `tool_catalogue` ChatTool builder. JSON-Schema is generated from it (`zod-to-json-schema`).
- **Metadata SoT:** `CAPABILITY_MANIFEST.json` (generated from frontmatter + `manifest_overrides.yaml`),
  with `query_schema` backfilled from the Zod module and new `family`/`role`/`annotations`/`response_format`
  fields (schema extended in `asset_entry.schema.json`).
- **Catalog + capabilities:** generated from the manifest (no hand maintenance).
- **Gateway** (`search_tools` + `invoke_tool`) over the contract serves both channels and hosts the
  single B.11 forced-first guarantee.
- **Tiers:** removed entirely; auth resolves identity + (optional) per-key scopes, not tiers.

## §3 — Phased implementation

> Each phase = one CLAUDECODE_BRIEF. Every code phase runs the §14.2 governance steps
> (manifest:build → fingerprint rotation → drift/schema/mirror → close-checklist). Dependency notes per phase.

### Phase 0 — Truth baseline + hygiene  *(low risk; do first)*
Work: dedupe `SURGICAL_TOOLS` (kill the 32 dups incl. `msr_sql` ×4) + drop redundant pass-through
aliases in `MCP_TO_RETRIEVAL_TOOL`; delete dead code (`retrieval_capability_spec.ts`, orphaned
`/api/mcp/execute` route + `callPlatform()/callPlatformPlan()` in `client.ts`); fix the stale
`tool_descriptions.test.ts` length assertion and make the catalog a real gate.
AC: full test suite green; `SURGICAL_TOOLS` has no duplicates; dead files removed; catalog count gate live.
Depends on: nothing. Parallel-safe with Phase 1.

### Phase 1 — B.11 live-gap hotfix  *(pulled forward; standalone)*
Work: add the citation/holistic output-guard (equivalent of `validateCitationsForStream`) to the
adapter/agentic-loop tail in `consume/route.ts` (currently un-guarded when `R11V2_USE_ADAPTERS=true`).
AC: adapter-path responses pass through the citation gate; parity with the orchestrator path on B.11
output validation; no regression in the live path.
Depends on: nothing. Ship independently of the convergence.

### Phase 2 — Canonical contract spine
Work: create the **shared Zod schema module**; add `zod-to-json-schema` (build dep); backfill manifest
`query_schema` for all tools from the Zod module; extend `asset_entry.schema.json` with `family`/`role`/
`annotations`/`response_format` (and stop these being warn-only); **generate `catalog.ts` + capabilities
content from the manifest**.
AC: every tool's manifest `query_schema` populated; catalog is generated and matches `server.ts`; schema
validation passes (not warn-only for the new fields); `manifest:build` reproducible.
Depends on: Phase 0.

### Phase 3 — Dual-channel generation + portal schema fix
Work: MCP server registers from the contract (handlers stay hand-written for the 8 custom-logic tools,
report §5.5; the 32 trivial-dispatch tools use a generated registration call); portal
`tool_catalogue.convertRetrievalToolToChatTool` reads the **real** JSON-schema from the shared module
instead of `normalizeInputSchema({})`.
AC: portal agentic-loop tools carry real schemas (0 empty); all 5 provider adapters still pass; both
channels demonstrably build their tool list from the one contract.
Depends on: Phase 2.

### Phase 4 — Wire the 17 ghost tools  *(near-free parity win)*
Work: per the report §3B, wire the ~11 genuine astrology engines (tara/chandra bala, transits-over-natal,
yogas-active-now, shadbala, planet-avastha, jaimini-chara-dasha, planetary-period-predictions, eclipse,
planet-war, drekkana/dasamsha/shashtiamsha) via import + register; convert `interpret_current_dasha` to a
prompt template (Phase 11); decide `list_assets`/`list_canonical_artifact_versions` (meta-utility or drop).
Add each to the shared schema module + manifest.
AC: live surface 40 → ~51; `server.ts` == generated catalog; bench + accuracy green.
Depends on: Phase 3 (so they're born into the contract).

### Phase 5 — Gateway baseline (dynamic loading, now)
Work: `search_tools(query|family)` (returns contract entries incl. generated JSON-schema) +
`invoke_tool(name, params)` (server-side Zod validation — recovers what a generic dispatcher loses,
report §8.4); define the resident core (~12); host the **single B.11 forced-first guarantee** in the
gateway (unifies the portal floor + MCP advisory into one mechanism).
AC: stateless gateway works on both channels; resident core stable/ordered (prompt-cache friendly);
B.11 forced-first enforced via the gateway on both channels.
Depends on: Phase 3 (contract), Phase 1 (B.11 guard logic to reuse).

### Phase 6 — Control-model B (surgical)
Work: widen the agentic loop's catalog from `tools_authorized` to the full contract **via the gateway**,
while keeping the planner producing the authorized floor (so all `tools_authorized` accounting/trace/cache
in report §6.4 stays intact).
AC: loop can discover+call beyond the planner subset via the gateway; budget/trace/cache/audit unchanged;
B.11 floor still pre-seeded.
Depends on: Phase 5.

### Phase 7 — Reconciliation + canonical rename  *(one atomic batch)*
Work: the full canonical rename across all 12 surfaces (report §14.2) — `catalog`, `server.ts`,
`primitives_registry`, `retrieve/index.ts` + alias objects, `route.ts` 4 name-keyed tables, bundle
fan-out maps, **`PLANNER_PROMPT_v2_0.md`**, DB `capability_tool_registry` re-seed, `bench/scenarios/*`,
`cross_scenario.test`. Includes: the parameterized dispatchers `discovery_register(kind:)` +
`synthesis_walk(layer:)`; the trivial `query_signals`/`msr_sql` dedupe (both already → engine `msr_sql`);
de-register the `query_jaimini_drishti` stub; resolve the `acharya`/`acharya_reviewer` split; handle
remedies **only after** confirming the §10.4 relationship.
AC: `drift_detector.py` no HIGH findings; bench regenerated; PLANNER_PROMPT updated; manifest rebuilt;
single atomic PR.
Depends on: Phase 4 (rename the final tool set once).

### Phase 8 — Tier excision  *(subsystem; security sign-off)*
Work: drop `mcp_api_keys.audience_tier` column + 070/117 constraints (new migration); remove the
`platform/src/lib/disclosure/` module + UI components; relax the `auth.ts` validation gate + the
`/api/mcp/keys/validate` contract; strip `X-MCP-Audience-Tier` from all outbound MCP calls; remove the two
hard-403 health routes' gates; delete `tier_catalog.ts`; remove the `flag_disagreement` super_admin gate
and the `query_varshphal` client-redaction branch (**security decision: every key now writes/flags and
sees unredacted output**); collapse house-rules variants to one; re-ground the `?api_key=` URL restriction
as a pure security control.
AC: zero tier references; keys validate without tier; security posture explicitly confirmed; all
tier-coupled tests removed/updated.
Depends on: Phase 7 (avoid colliding on `route.ts`/manifest). Independent of Phases 5–6 otherwise.

### Phase 9 — Data backfills
Work: seed CGM graph (`cgm_nodes`/`cgm_edges`) and L5 timeline (`rag_chunks` `doc_type='l5_timeline'`) so
`get_cgm_subgraph`/`timeline_query` read true; verify `query_signal_state` populated.
AC: `tool_health`/`data_coverage` report these functional; row counts > 0.
Depends on: nothing (operator/data task; can parallel).

### Phase 10 — Native `listChanged`  *(deferred enhancement)*
Work: stateful sessions (`sessionIdGenerator` + SSE on `GET /mcp` + externalized session store for Cloud
Run); enable on-demand family loading via `listChanged`.
AC: hosts that honor `listChanged` get dynamic tool sets; stateless gateway remains the fallback.
Depends on: Phase 5.

### Phase 11 — Prompts + eval gates + re-baseline
Work: `prompts` primitive for canned workflows (incl. `interpret_current_dasha`); per-tool contract test
(blocking); confirm/repair `answer:eval`; regenerate bench; re-baseline `answer:eval` once (per the
"once per consolidated batch" discipline).
AC: contract lint blocking in CI; bench green; `answer:eval` re-baselined with tool-selection accuracy ≥
prior (target: improved by the Phase 3 schema fix).
Depends on: Phases 4, 7.

## §4 — Sequencing summary

Critical path: **0 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 11.**
Parallel-safe: **Phase 1** (B.11 hotfix) immediately; **Phase 9** (backfills) anytime; **Phase 10** after 5.
Heavy/high-risk phases (stage carefully, own PRs): **7** (atomic rename) and **8** (tier excision) — both
touch `route.ts`/manifest, so they are sequenced, never concurrent.

## §5 — Success metrics

One contract → both channels (0 `MCP_TO_RETRIEVAL_TOOL` indirection, 0 alias objects, 0 dup `SURGICAL_TOOLS`
entries remaining post-Phase-7); manifest `query_schema` populated 100%; portal empty-schemas = 0; catalog
== server == manifest count (generated, gated); adapter-path B.11 citation gate live; resident core ≤ ~12;
`drift_detector` clean; bench green; `answer:eval` ≥ baseline; zero tier references.

## §6 — Open confirmations (non-blocking; resolve in Phase 0/execution)

1. `answer:eval` existence + scoring (confirm `scripts/answer_eval.ts`).
2. `query_remedies_prescribed` vs `remedial_codex_query` relationship before any merge (§10.4).
3. Final wire-vs-retire calls for `list_assets` + `list_canonical_artifact_versions` (Phase 4).
4. Security sign-off for Phase 8 (writes/flags/redaction open to all keys once tiers go).

---

*End of TOOL_PORTFOLIO_PLAN v1.3 (DRAFT — implementation plan). Grounded in the verified reality report.
Each phase becomes a CLAUDECODE_BRIEF. No implementation performed in this planning session.*

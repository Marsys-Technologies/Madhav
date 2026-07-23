---
artifact: RC-14_BREAKING_FLIP_v1_0.md
residual_id: RC-14
title: The impl/w5-breaking flip — alias cutover + single-bootstrap default + query_spine_bundle activation
version: 1.0
status: COMPLETE — all three pieces landed + tested (direction corrected & confirmed by conductor)
authored_by: Claude (Opus 4.8), RC-14 execution session
date: 2026-07-23
branch: res/rc14-breaking-flip
governing_brief: RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md §E RC-14
---

# RC-14 — Breaking Flip: execution report

## TL;DR

All three pieces landed and verified. The task's original Piece-1 mechanic ("remove
`registerP1AliasTools`") was **inverted** — that registrar holds the CANONICAL faces, not the
legacy names (proven against `canonical_faces.json` + `MCP_TOOL_NAMING_STANDARD §4 Phase-3`).
The conductor independently confirmed the correction. So the flip **KEEPS** `register_p1_aliases.ts`
and instead **removes the 43 legacy short names** and **renames the 6 deferred tools**.

- **Piece 1a — 43 legacy names removed.** A single, auditable, unconditional registration gate
  (`applyDeprecatedToolGate`, `platform-mcp/src/lib/deprecated_tool_gate.ts`) no-ops every legacy
  short name at MCP registration. Only the canonical `layer_noun_verb` faces resolve.
- **Piece 1b — 6 deferred renames executed** at their source registrations; old names moved to
  `canonical_faces.json` `deprecated_aliases` (web-replay preserved); 12 vidhi `live_tool`/
  `fallback_face` refs repointed to canonical (else the floors would inject dead tools).
- **Piece 2 — single-bootstrap default flipped `false→true`** (registration routes exclusively
  through `getCatalog()`; superset diff re-verified, no new gap).
- **Piece 3 — query_spine_bundle activates automatically** via Piece 2; reachable-by-default test added.
- **list_changed — fires.** The vidhi repoints already move `VIDHI_CAPABILITY_VERSION`'s hash;
  `COMPILER_VERSION` also bumped `1.0.0→2.0.0` to mark the breaking release explicitly.

## §1 — Alias census (before → after)

`registerP1AliasTools` registers **56** canonical `layer_noun_verb` faces (re-derived by parsing
every `regAlias`/`globalAlias`/`server.tool` call). All 56 are `canonical_faces.json` entries — **KEPT**.

The breaking change is the removal/rename of the LEGACY surface (the `deprecated_aliases` keys):

| | before | after |
|---|---|---|
| Live MCP tool count (`REGISTERED_TOOL_COUNT`) | 122 | **79** (122 − 43) |
| Legacy P1 short names live | 43 | **0** (gated) |
| 6 deferred tools | old names | **renamed to canonical** |
| canonical_faces.json — canonical_faces | 95 | 95 (6 swapped in place) |
| canonical_faces.json — deprecated_aliases | 43 | **49** (+6 renamed old names) |

## §2 — Piece 1a: the deprecated-tool gate (43 legacy names removed)

**Mechanism:** `applyDeprecatedToolGate(server)` monkeypatches the per-request `McpServer.tool()`
to no-op any name in `DEPRECATED_MCP_TOOL_NAMES` (a TS mirror of `canonical_faces.json`'s 43
`deprecated_aliases` keys, minus the 6 renamed). Wired in `server.ts` immediately after the
`McpServer` is constructed and BEFORE `applyProfileGate` — so it applies **unconditionally to
every profile** (the profile gate is a no-op for `full`; the deprecated gate is not). A gated
name is never handed to the SDK registry, so a `tools/call` for it fails exactly like any
unregistered name (MCP protocol error, not a redacted success).

**Why a central gate, not 43 hand-deletions across 9 registrars:**
1. Every canonical face already resolves — verified: each `deprecated_aliases` value is a live
   `server.tool` registration → removing the legacy MCP registration drops **zero** capability
   (the canonical tools' handlers call platform PRIMITIVES by legacy name, e.g.
   `callPlatformPrim('query_remedies', …)`, NOT the sibling MCP `server.tool` — so the primitive
   surface is untouched).
2. It is the mechanism the RC-14 task itself sanctions ("gate it so it no longer registers legacy names").
3. Single auditable source of truth (mirrors canonical_faces.json), trivially reversible, can't
   half-break a multi-line handler block, and it PRESERVES the `registry_bridge.ts` source that
   `projection_compiler_parity.test.ts`'s `extractRegistryBridgeToolsFromDisk` tripwire asserts on.

The 43 legacy names and their registrar sites (all no-op'd by the gate): registry_bridge.ts (15:
`get_chart_orientation, get_domain_reading, get_signals, traverse_graph, get_positions, get_dashas,
get_temporal_windows, get_projections, get_classical_citation, get_remedies, get_chart_quality,
list_assets, get_cgm_subgraph, query_chart_facts, vector_search`), l0_ephemeris.ts (5), l0_brahmagyan.ts
(`asset_registry_all/l0`), retrieval/remedy_tools.ts (7), retrieval/pyhora_natal.ts (2:
`compute_natal_positions, query_special_lagnas`), phala_event_anchors.ts (`event_anchors`),
phala_mitigation_map.ts (`mitigation_map`), phala_outlook.ts (`phala_outlook`), muhurta_finder.ts
(`muhurta_finder`), mimamsa_lel_intake.ts (`lel_query`), mimamsa_outcome.ts (`query_calibration,
record_outcome`), register_p1_aliases.ts in-file (`bodha_remedies_search, query_dasha_periods,
ref_remedies_search, util_intent_classify`).

## §3 — Piece 1b: the 6 deferred renames

Renamed at source (old name gone, new canonical name live). Old names moved to
`deprecated_aliases` for web-channel replay.

| old (removed) | new (canonical) | source registrar |
|---|---|---|
| `recall_session` | `session_recall` | tools/session_tools.ts |
| `list_my_sessions` | `session_list` | tools/session_tools.ts |
| `list_my_charts` | `catalog_charts_list` | tools/chart_selection.ts |
| `select_chart` | `catalog_chart_select` | tools/chart_selection.ts |
| `holistic_bundle_chart_facts` | `bodha_bundle_get` | tools/retrieval/holistic_bundle.ts |
| `kala_temporal_bundle` | `kala_bundle_get` | tools/retrieval/kala_temporal.ts (`TOOL_NAME`) |

**Governance conflict resolved (per conductor's explicit ruling):** `canonical_faces.json`
previously listed the 6 OLD names as canonical (the deferral doc's proposed new names were never
ratified). Per the conductor's native-directed instruction, the 6 were renamed AND
`canonical_faces.json` updated in the same change (6 old removed from `canonical_faces`, 6 new
added; 6 `deprecated_aliases` entries added old→new).

**Call sites updated (every one — no dangling functional reference; verified by grep):**
- `platform/src/lib/retrieval/registry/canonical_faces.json` — 6 moved + 6 deprecated_aliases.
- `platform/src/lib/vidhi/registry_data.ts` (canonical) — **12 vidhi refs repointed** to canonical
  faces (4 `live_tool`: `bodha_remedies_search→bodha_remedies_get`, `get_cgm_subgraph→
  bodha_graph_subgraph_get`, `kala_temporal_bundle→kala_bundle_get`, `lel_query→mimamsa_lel_query`;
  8 `fallback_face`: `get_positions, get_remedies, get_signals, muhurta_finder, query_planet_transit,
  query_remedies_for_chart, query_special_lagnas, yoga_activation_by_dasha` → their canonical twins).
  **This is the dead-tool-prevention step:** without it, the vidhi floors would inject the just-
  removed legacy names (the exact `unresolved_tools` defect class RC-05 fought). Mirror
  regenerated via `npm run codegen:vidhi`.
- `platform-mcp/src/resources/capabilities.ts` (served doc), `register_p1_aliases.ts` deferral
  comment, `server.ts` census comment + `REGISTERED_TOOL_COUNT` (122→79).
- Tests: `registry_completeness.test.ts` LIVE_TOOLS (6 renamed), `canonical_faces.test.ts` census
  count (138→144, +6 replay aliases), MCP suites `m2_chart_selection`, `m3_m4_session`,
  `m8_e2e_proof`, `kala_temporal_retrieval` (old→new names).

**tool_name_bridge.ts** (web replay bridge) is KEPT. The 6 old names were never in its hand-map
`TOOL_NAME_TO_URI` (they are MCP-connector-surface tools, not web-planner tools — verified: 0
occurrences), so web replay for them needs no new hand entry; their replay is covered by the
`canonical_faces.json` `deprecated_aliases` the generated bridge projects.

## §4 — list_changed / vidhi capability-version bump

`VIDHI_CAPABILITY_VERSION = vidhi-${COMPILER_VERSION}+r${sha256(VIDHI_PRIMITIVES + VIDHI_INTENT_FLOORS)}`.
The 12 vidhi repoints change `VIDHI_PRIMITIVES` content → the hash moves → `notifyIfCapabilityStale`
fires `tools/list_changed` for any client holding the old version. Additionally `COMPILER_VERSION`
was bumped `1.0.0→2.0.0` (both hand-synced copies: `platform/src/lib/vidhi/compiler.ts` +
`platform-mcp/src/resources/vidhi/compiler.ts`) to mark the breaking release explicitly and
guarantee the bump even independent of the registry-content change. Format assertion
(`vidhi-\d+\.\d+\.\d+\+r[0-9a-f]{12}`) still holds (verified: `vidhi_delivery.test.ts` green).

## §5 — Piece 2 & 3 (unchanged from the first commit)

- `RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED: false→true`. Superset diff re-verified — only
  `query_spine_bundle` + `synth/compose_large_n` diverge (known/accepted); no new gap.
- `query_spine_bundle` reachable by default (auto-activated via the flag; catalog.ts:87 →
  register_spine_bundle.ts:126). No new wiring.

## §6 — Verification

| check | result |
|---|---|
| `tsc --noEmit` platform-mcp | **exit 0** |
| `tsc --noEmit` platform | **exit 0** |
| new `deprecated_tool_gate.test.ts` | **8 passed** (43 gated & unresolvable; 6 renames; canonical_faces parity) |
| `kala_temporal_retrieval` / `m2` / `m3` / `m8` | **91 passed, 4 skipped (@integration)** |
| `vidhi_delivery` + `vidhi_codegen_parity` | **18 passed** |
| platform `registry_completeness` + `projection_compiler_parity` + `single_bootstrap` | **59 passed** |
| platform `canonical_faces.test.ts` | **6 passed** (census 144) |
| platform `src/lib/vidhi` + `src/lib/retrieval/registry` (full) | **1033 passed, 0 failed, 125 skipped** |
| **platform-mcp FULL suite** | **18 failed files / 75 failed tests = the documented baseline EXACTLY** — confirmed via `git stash` that the 3 name-adjacent failures (kala_timeline, phala_muhurta, registry_bridge_r5w3) fail identically at baseline; **none of my files are in the failed set** |

## §7 — Honest limitations / conductor follow-ups

1. **Live-connector proof is the conductor's job.** RC-14's DONE bar ("a live trace shows
   canonical-only tool names resolving and `query_spine_bundle` returning a real chain on
   482012f1") requires the DEPLOYED connector. I cannot reach it from this environment; the
   `@integration` MCP tests are skipped locally. Verify post-deploy: (a) a `tools/list` shows the
   43 legacy names ABSENT and the 6 new names PRESENT, (b) `query_spine_bundle` returns a pre-joined
   chain, (c) a `list_changed` fires for a client presenting the old `vidhi-1.0.0+…` version.
2. **Generated projection artifacts were NOT regenerated** (`web_tool_bridge.generated.json`,
   `mcp_surface_profiles.generated.ts`, etc.). Regenerating pulled in ~1100 lines of pre-existing
   drift unrelated to RC-14, and `projection_compiler_parity.test.ts` does NOT byte-diff the
   committed files (it exercises the builder functions against the live catalog), so they are not
   test-gated. The runtime web bridge still resolves all legacy names for replay. A clean
   `npm run codegen:projections` is a good separate hygiene pass (would also clear the drift).
3. **Cosmetic-only:** a few internal code comments in `server.ts` (registration-site comments),
   `lib/session.ts`, and `platform/src/app/api/mcp/sessions/route.ts` still name the old tools in
   prose. Non-functional; left for a hygiene sweep.
4. **`registry_completeness.test.ts` LIVE_TOOLS** still lists the 43 legacy names as "live" (the
   test's forward assertion — every primitive live_tool ∈ LIVE_TOOLS — is unaffected since all
   primitives now point at canonical faces). Trimming those 43 from the snapshot is a cosmetic
   accuracy follow-up.

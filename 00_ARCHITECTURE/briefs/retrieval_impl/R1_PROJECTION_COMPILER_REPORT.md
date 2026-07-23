---
artifact: R1_PROJECTION_COMPILER_REPORT.md
canonical_id: R1_PROJECTION_COMPILER_REPORT
version: 1.0
status: GENERATED — regenerate via `npx tsx --conditions=react-server scripts/manifest/generate_projections.ts`
generated_at: 2026-07-23T20:20:06.711Z
generator: platform/scripts/manifest/generate_projections.ts
---

# R-1 Projection Compiler Report (plan §3 R-1 item 2)

ADDITIVE ONLY. Nothing below is wired into any live-serving path. This document is
regenerated, not hand-maintained — see the generator's own header comment for scope.

## 0. Live catalog snapshot

`getCatalog()` returned **166** live capabilities at generation time.

By resolved type: **tool**=160, **resource**=5, **prompt**=1.

(6 of these resolve `type` via a `primitive_type` fallback — a real, pre-existing
registry inconsistency this generator tolerates rather than papers over; see
`machine_census.generated.json`'s `summary.type_resolved_via_primitive_type_fallback`.)

## 1. (a) Chat tool-def projection vs. the real served chat contract catalog

Generated chat projection (type=tool + `projection_tags` includes `chat`):
**79** tool defs.

Real served chat contract catalog (`TOOL_CONTRACTS`, `platform/src/lib/contract/registry.ts`):
**5** entries. (The plan's GT-3 citation says 6; this worktree's live
`registry.ts` has 5 — flagged, not silently reconciled; see §4 below.)

- Overlap by name: find_verses_about, list_classical_texts
- Only in `TOOL_CONTRACTS` (not reachable via the generated chat projection today):
  read_chapter, read_classical_text, search_classical_texts
- Only in the generated projection (new capabilities `TOOL_CONTRACTS` never covered):
  77 names — see `comparison_report.generated.json`
  `chat_projection.only_in_generated` for the full list (too long to inline).

**Reading:** `TOOL_CONTRACTS` is a hand-authored 5-classical-text-tool surface that predates
the registry (`lib/retrieve/index.ts`'s own header: "DEPRECATED as of D7... 17+ active
callers... still depend on it"). The generated projection draws from the registry's
79 chat-tagged capabilities instead — a near-complete disjoint set by name,
because they were never the same catalog. This is the exact triplication the plan's R-1
opening line names ("kill the triplication") — the projection compiler does not resolve it
by itself (that is item 3, One Bootstrap, and item 4, Alias cutover — explicitly out of this
additive-only lane's scope); it makes the size and shape of the gap machine-legible for the
first time.

## 2. (b) MCP tool-registration projection vs. the ~25 hand-written `server.tool` blocks

Generated MCP projection (type=tool + `projection_tags` includes `mcp_full`):
**158** tool registrations (+ 6 mcp-tagged
resources/prompts that would need `server.resource()`/`server.prompt()`, not
`server.tool()` — listed separately, not folded in).

Real hand-written `server.tool(...)` blocks extracted from
`platform-mcp/src/tools/registry_bridge.ts` (mechanical text scan, not hand-counted):
**26** blocks.

- Name overlap: 13 → assess_career, assess_health, assess_marriage, assess_wealth, chart_snapshot, get_dashas, get_graha_yuddha, get_positions, graha_portrait, judgment_query, pact_query, tool_search, yoga_activation_by_dasha
- Only in `registry_bridge.ts` (workflow-shaped consolidated names with no 1:1 registry
  capability of the same name): get_cgm_subgraph, get_chart_orientation, get_chart_quality, get_classical_citation, get_domain_reading, get_projections, get_remedies, get_signals, get_temporal_windows, list_assets, query_chart_facts, traverse_graph, vector_search
- Only in the generated projection: 145 names (the granular
  registry capability set the hand-written file does not expose under its own name —
  see `comparison_report.generated.json` for the full list).
- 7 of the 26 hand-written blocks use the
  SDK's 3-arg overload (name, schema, handler) with **no top-level description literal**:
  traverse_graph, get_positions, get_projections, get_classical_citation, get_remedies, get_chart_quality, list_assets.

**Reachability cross-check** (does a registry capability have ANY route through the current
hand-written 25, by literal `marsys://` URI reference in that tool's body — not by name):
**24 / 166** catalog URIs are referenced somewhere in
`registry_bridge.ts`; **142 / 166** are not referenced
by literal URI anywhere in that file (they may still be reachable via a different bridge file,
a resource loader, or not yet individually exposed on MCP at all — this scan is scoped to
`registry_bridge.ts` only, per this lane's (b) sub-item; a full-surface reachability
cross-check across every MCP bridge file is a larger census, not this generator's job).


**Reading:** the plan's own framing ("replacing the ~25 hand-written server.tool blocks...
with a loop over compiled defs — handlers stay hand-written; surfaces are generated") implies
a MUCH larger generated MCP surface (near-1:1 with the registry, 158 tools) than
today's curated 26-tool consolidation. The hand-written file fans multiple
registry capabilities into single workflow-shaped tools (e.g. `get_chart_orientation` wraps
`marsys://tool/L2/query_ucd` plus a `get_chart_header` follow-up call) and adds real business
logic (response-format bounding, v3 envelope population, budget trimming) inside the handler —
none of which a projection compiler should try to synthesize. This report characterizes the
gap; it does not propose collapsing the two (see §4, out of scope this lane).

## 3. (c) Machine census

`machine_census.generated.json` — **166** entries, every field the registry
declares (uri/type/layer/name/scope/archetype/traversal_level/tool_role/data_source/
mutation/emits_references/lel_capable/calibration_context_only/bearing_first/
required_inputs/projection_tags/display/annotations + presence flags for
density_contract/output_schema/family_overrides/register.glossary/drill_children).
Also emitted as the summary block inline in that same file (`summary.by_layer`,
`by_type`, `by_scope`, `by_archetype`, `by_tool_role`, `by_data_source`,
`by_projection_tag`). This is the "machine-generated census" the plan's item 2d calls for
— kills the need to hand-recount (the exact failure mode the plan's §1.1/GT findings name
for `server.ts`'s own comment-based count).

## 4. (d) Docs resource stub — `marsys://resource/catalog` shape

`docs_resource_catalog.generated.json` — a resource-shaped document (`uri:
"marsys://resource/catalog"`, `mime_type: "application/json"`) listing every live
capability's uri/type/layer/name/short_label/one_line/scope/archetype/tool_role/
projection_tags, so any MCP client could self-orient by reading one resource. This is a
STUB in the sense that it is generated as a static JSON artifact here, not wired to
`server.resource("marsys://resource/catalog", ...)` on the live MCP server (that wiring
is a live-serving-path change, explicitly out of this additive-only lane's scope per the
task's own instruction — "new code paths gated behind an explicit flag that defaults OFF").

## 5. (e) Web↔MCP tool-name bridge (W5 L1)

`web_tool_bridge.generated.json` — resolves the Vidhi floor compiler's
`live_tool` namespace (31 distinct names across
`registry_data.ts`) plus the full `canonical_faces.json` list
(95 names) to registry URIs, by chaining
`getCatalog()` capability names + `canonical_faces.json`'s `deprecated_aliases`
+ `tool_name_bridge.ts`'s existing hand-curated maps (not re-authored — chained).

- Vidhi `live_tool` bridge: **12 / 31** resolve to a
  registry URI (before this lane's generated projection, `compiled_floor_adapter.ts`'s
  hand-curated `LIVE_TOOL_TO_RETRIEVAL` mapped only **4 / 31**).
  Unmapped: bodha_chart_digest_get, bodha_remedies_get, bodha_signals_get, ganita_ayurdaya_get, ganita_condition_get, ganita_dasha_lord_capability_get, ganita_kp_cusps_get, ganita_nakshatra_get, ganita_sensitive_degrees_get, ganita_strength_get, ganita_structural_get, gochara_activation_get, gochara_election_avoidance_get, gochara_forecast_get, kala_bundle_get, kala_windows_get, phala_predictive_anchors_get, ref_doshas_get, synth_tail_divergence_get.
- `canonical_faces.json` bridge (broader census): **39 / 95**
  resolve to a registry URI. 56 remain unmapped — see
  `web_tool_bridge.generated.json`'s `canonical_faces_bridge.entries` for the
  full per-name resolution_kind/via chain (not inlined here, too long).

**Wiring status:** `tool_name_bridge.ts`'s `resolveToolUri()` now falls back to
this generated projection (`resolveGeneratedToolUri`) for any name not already
in its hand-curated `TOOL_NAME_TO_URI`, and resolves literal registry URIs
directly (the CR-118 fast-fail fix — see that file's `isCapabilityUri` doc
comment). `compiled_floor_adapter.ts`'s `LIVE_TOOL_TO_RETRIEVAL` now consults
this generated bridge before falling back to its small hand-curated map, raising
Vidhi floor-primitive mappability from 4/31 toward
12/31 without hand-editing that file.

## 6. (f) Per-family tool-def projection (W5 lane L3 — annotations + family_overrides + input_examples/search_result emissions)

`family_tool_defs.generated.json` — the base chat tool-def projection (§1 above),
merged per model family (anthropic/gemini/openai/deepseek) with any declared
`cap.family_overrides[family]` (types.ts `FamilyOverrideSpec`:
`description_override`/`name_override`/`strict_schema`/`input_examples`/
`search_result_content_block`). Every emitted tool def also now carries an
`annotations` block in the REAL MCP `ToolAnnotations` wire shape
(`readOnlyHint`/`destructiveHint`/`idempotentHint`/`openWorldHint`/`title`,
verified against this repo's installed `@modelcontextprotocol/sdk` — not guessed) —
the same `annotations` addition also lands on (a) chat tool defs and (b) MCP tool
registrations above, additively alongside their pre-existing `read_only`/
`destructive` fields.

Overrides declared per family today: **anthropic**=0, **gemini**=0, **openai**=0, **deepseek**=0
(0 across the board — W2's descriptor-migration lane deliberately left
`family_overrides` at 0/118, "requires genuine per-capability editorial judgment
[...] left for a future, explicitly-scoped editorial wave" — that ruling stands;
this lane builds the EMISSION mechanism the override merge needs, not the editorial
content). Every family's projection is therefore mechanically identical to the base
chat projection today — the CORRECT output of a real merge with no overrides
present, not a gap in this lane. Name collisions per family (would only appear once
`name_override` population starts): **anthropic**=0, **gemini**=0, **openai**=0, **deepseek**=0.

**Wiring status:** additive only, same as every other projection here — nothing in
this artifact is consumed by `getCatalog()`, the chat pipeline's MARO adapter, or
any live `server.tool()` call. The day an editorial wave populates a real
`family_overrides` entry on any capability, this generator picks it up on its next
run with zero code changes (verified in `family_projection.test.ts` via test-local
mock overrides exercising every merge path: `description_override`, `name_override`,
`strict_schema`'s additionalProperties:false/all-required transform,
`input_examples` pass-through, `search_result_content_block`).

## 7. (g) W5 Lane L4 — tool-search index (`tool_search_index.generated.json`)

**166** entries — one per live capability, no filtering. Each entry
carries `uri`/`name`/`type`/`layer`/`scope`/`family` (the descriptor's own
`archetype`)/`tool_role`/`short_label`/`one_line`/`description`/`keywords` (a deduped,
sorted, tokenized set derived from name+description+display+layer+archetype+tool_role+
traversal_level+projection_tags — no field invented, everything traces to a real descriptor
property per B.10's "don't fabricate" discipline applied to metadata, not just numbers).

Live-served counterpart: `marsys://tool/L0/tool_search`, bridged onto MCP as the
`tool_search` tool (`registry_bridge.ts`) — same `buildToolSearchIndex`/`searchToolIndex`
functions, called against the LIVE `getCatalog()` on every request (not this static
snapshot), so a stale generated JSON can never diverge from what a caller actually gets back.

**Scope of "search" (explicit, not a silent limitation):** case-insensitive keyword/substring
match over tokenized fields, scored (name match > keyword match > description substring).
NOT fuzzy matching, NOT semantic/embedding search (that would be a `vector_search`-style
corpus build — materially heavier, out of scope for this lane's first cut). A query with zero
token overlap against every entry returns an honest `total_matches: 0`, never a fabricated
best-effort guess.

## 8. (h) MCP surface profiles — full / compact≤20 / consult (W5 L2)

Plan §R-4 item 1/2 + ruling RC-1/RC-3: "Profile selection = entitlement (OT-10 b+c):
OAuth scope / connect URL selects the projection; a plain guest cannot reach raw tools."
`mcp_surface_profiles.generated.json` builds the three named profiles as a 6th output of
this same compiler (not a parallel one), reusing `buildMcpToolRegistration` for per-tool
shape:

- **full**: **150** `mcp_full`-tagged tools, uncapped.
- **compact**: **20 / 20** (capped per RC-1;
  50 eligible `mcp_compact`-tagged tools
  did not make the cap — reachable via `full` or a surfaced sibling's `drill_children`, listed
  in `overflow_tool_names`, never silently dropped).
- **consult**: **8** `mcp_consult`-tagged (L-ORIENT) tools —
  the restricted "safe by default" set (plan §6.5). Verified by construction (not just
  asserted): every consult tool name is also a full tool name
  (`invariant_consult_subset_of_full`: **true**) — consult can never surface
  a name absent from full.

F-R7 (NO-LEAKAGE) enforcement: `calibration_context_only` capabilities are excluded from all
three profiles here. Full: lel_query, mechanism_retrodiction_get, query_predictions
excluded. Compact: lel_query, mechanism_retrodiction_get, query_predictions
excluded.

**Wiring status:** `platform-mcp/src/lib/mcp_profile.ts` (this same lane) reads the generated
TS mirror (`platform-mcp/src/generated/mcp_surface_profiles.generated.ts`) to resolve a
profile from the caller's OAuth scope and gate `server.tool()` registration in
`platform-mcp/src/server.ts` accordingly — see that file's own doc comments for the
scope-to-profile mapping and the safe-default (unscoped/legacy OAuth token → consult).

**Honest residuals, not silently closed:**
- `marsys_drill` (the plan's named compact-profile dispatcher tool) does not exist in the
  catalog — not fabricated here; the existing `drill_children` field already gives overflow
  tools the same reachability guarantee. A literal dispatcher tool is a possible future wave,
  not built this lane.
- The OTHER four projections this compiler already emits (chat/mcp_full/mcp_compact/docs
  census above) do not yet apply the F-R7 calibration_context_only filter this profile builder
  enforces — flagged for a future tightening pass, not fixed here (out of this lane's scope,
  touches files this lane did not open to rewrite).
- `prashna_ask` (plan: "MCP-consult = `prashna_ask` + ~5 orienting tools") is W6 scope, not
  yet built — the consult profile here is the 8 orienting
  tools only; `prashna_ask` joins the consult set when W6 lands it.

## 9. Honesty notes / what's NOT done this lane

- Plan item 2c ("the vidhi primitive rows' tool bindings") is **not** covered by this
  generator — it is the separately-landed `codegen:vidhi`/`codegen:vidhi:check` lane
  (GT-56, `scripts/generate_vidhi_registry_mirror.ts`), found already present in this
  worktree at lane open (concurrent W2 work). Not duplicated.
- The MCP tool-registration projection emits **shape only** (name/description/JSON-Schema
  input_schema) — it does NOT generate zod source code or an actual `server.tool()` call
  loop. Wiring that (replacing the hand-written blocks with "handlers stay hand-written;
  surfaces are generated") is real follow-on codegen work (closer to
  `generate_registry_shims.ts`'s zod-source-emission pattern) not attempted here — the
  task explicitly permits stubbing (b)/(d) if full fidelity isn't reached; this lane
  reached full fidelity on the DATA SHAPE of (b) but not on TS-source emission.
- `TOOL_CONTRACTS` count discrepancy: the plan (GT-3) says 6 entries; this worktree's live
  `registry.ts` has 5. Not investigated further (reading, not
  editing, per this lane's scope) — flagged for whoever owns GT-3's ground truth next.
- The registry-bridge extractor is a text scan (documented method in
  `extract_registry_bridge_tools.ts`'s header), not a TS/AST parse. It is defended by a
  parity-test tripwire (known tool names must round-trip) rather than claimed complete
  against arbitrary future syntax changes to that file.

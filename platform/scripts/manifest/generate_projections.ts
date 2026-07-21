/**
 * generate_projections.ts — R-1 projection compiler (build-time generator)
 * ================================================================================
 * RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md §3 R-1 item 2: "Build the projection
 * compiler. One build-time generator emits: (a) chat tool defs...; (b) MCP tool
 * registrations...; (c) the vidhi primitive rows' tool bindings; (d) a
 * machine-generated census...; (e) a docs resource (marsys://resource/catalog)."
 *
 * SCOPE OF THIS LANE (Wave 2b, ADDITIVE ONLY): sub-items (a) chat tool defs,
 * (b) MCP tool registrations, (d)→here relabeled (c) machine census, (e)→here
 * relabeled (d) docs resource stub. The plan's own (c) — "the vidhi primitive
 * rows' tool bindings" — is a DIFFERENT, already-separately-landed codegen
 * lane (`scripts/generate_vidhi_registry_mirror.ts`, GT-56, CI-wired as
 * `codegen:vidhi`/`codegen:vidhi:check` — confirmed present in this worktree's
 * git status at lane open, a concurrent W2 lane's work) — NOT duplicated here.
 *
 * Every artifact this script writes is a NEW generated file alongside the
 * existing hand-written surfaces (TOOL_CONTRACTS, registry_bridge.ts) — it
 * does not modify, import from, or get imported by either live-serving path.
 * `catalog.ts`'s `getCatalog()` and `chat`/`MCP` bootstrap are UNTOUCHED.
 *
 * Requires NO database and NO network access — `getCatalog()` only enumerates
 * already-registered descriptor objects (handlers are functions, never
 * invoked here); `TOOL_CONTRACTS` is a static in-memory array. Still needs
 * `--conditions=react-server` because the registry import chain pulls in
 * `lib/db/client.ts`, which is gated by the `server-only` package (same flag
 * every other script under `scripts/manifest/` already requires).
 *
 * Usage: npx tsx --conditions=react-server scripts/manifest/generate_projections.ts
 */
import { writeFileSync, mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { getCatalog } from '../../src/lib/retrieval/registry/catalog'
import { CONTRACT_CATALOG } from '../../src/lib/contract/catalog'
import {
  buildMachineCensus,
  buildChatToolDefs,
  buildMcpToolRegistrations,
  buildMcpNonToolRegistrations,
  buildDocsResourceCatalog,
  buildAllFamilyToolDefs,
  findFamilyNameCollisions,
  MODEL_FAMILIES,
  resolveType,
} from './projection_builders'
import { extractRegistryBridgeToolsFromDisk, REGISTRY_BRIDGE_PATH } from './extract_registry_bridge_tools'
import { resolveWebToolBridge, type CanonicalFacesData } from './web_tool_bridge_builder'
import { TOOL_NAME_TO_URI, MCP_TO_RETRIEVAL_TOOL } from '../../src/lib/retrieval/registry/tool_name_bridge'
import canonicalFacesRaw from '../../src/lib/retrieval/registry/canonical_faces.json'
import { VIDHI_PRIMITIVES } from '../../src/lib/vidhi/registry_data'

const OUT_DIR = join(__dirname, '..', '..', 'src', 'generated', 'projections')
const REPORT_PATH = join(
  __dirname, '..', '..', '..', '00_ARCHITECTURE', 'briefs', 'retrieval_impl',
  'R1_PROJECTION_COMPILER_REPORT.md',
)

function writeJson(name: string, data: unknown): void {
  const path = join(OUT_DIR, name)
  mkdirSync(dirname(path), { recursive: true })
  writeFileSync(path, JSON.stringify(data, null, 2) + '\n', 'utf-8')
  console.log(`[generate_projections] wrote ${path}`)
}

function main(): void {
  const caps = getCatalog()
  const generatedAt = new Date().toISOString()

  console.log(`[generate_projections] getCatalog() returned ${caps.length} live capabilities`)

  // (c) machine census — every capability, every declared field
  const census = buildMachineCensus(caps, generatedAt)
  writeJson('machine_census.generated.json', census)

  // (a) chat tool-def projection
  const chatDefs = buildChatToolDefs(caps)
  writeJson('chat_tool_defs.generated.json', {
    generated_at: generatedAt,
    generator: 'generate_projections.ts',
    source: 'getCatalog() capabilities with type=tool AND projection_tags includes "chat"',
    total: chatDefs.length,
    tool_defs: chatDefs,
  })

  // (b) MCP tool-registration projection
  const mcpTools = buildMcpToolRegistrations(caps)
  const mcpNonTools = buildMcpNonToolRegistrations(caps)
  writeJson('mcp_tool_registrations.generated.json', {
    generated_at: generatedAt,
    generator: 'generate_projections.ts',
    source: 'getCatalog() capabilities with type=tool AND projection_tags includes "mcp_full"',
    total: mcpTools.length,
    tool_registrations: mcpTools,
    excluded_non_tool_mcp_tagged: {
      note:
        'Capabilities carrying an mcp_* projection_tag but type != tool (resources/prompts) would ' +
        'register via server.resource()/server.prompt(), not server.tool() — listed here, not folded ' +
        'into tool_registrations above.',
      total: mcpNonTools.length,
      entries: mcpNonTools,
    },
  })

  // (d) docs resource stub — marsys://resource/catalog shape
  const docsCatalog = buildDocsResourceCatalog(caps, generatedAt)
  writeJson('docs_resource_catalog.generated.json', docsCatalog)

  // (e) W5 L1 — web↔MCP tool-name bridge. Resolves every distinct Vidhi floor-
  // compiler `live_tool` name (the MCP-native namespace `compiled_floor_adapter.ts`
  // had to hand-map, 4/23 before this lane) PLUS the full `canonical_faces.json`
  // list (broader coverage census) to a registry URI, by chaining getCatalog()
  // names + canonical_faces.json's deprecated_aliases + tool_name_bridge.ts's
  // existing hand-curated maps. See web_tool_bridge_builder.ts header for the
  // full resolution-order rationale.
  const canonicalFaces = canonicalFacesRaw as unknown as CanonicalFacesData
  const liveToolNames = [...new Set(VIDHI_PRIMITIVES.map((p) => p.live_tool))].sort()
  const liveToolBridge = resolveWebToolBridge(liveToolNames, caps, TOOL_NAME_TO_URI, MCP_TO_RETRIEVAL_TOOL, canonicalFaces)
  const canonicalFaceBridge = resolveWebToolBridge(
    canonicalFaces.canonical_faces,
    caps,
    TOOL_NAME_TO_URI,
    MCP_TO_RETRIEVAL_TOOL,
    canonicalFaces,
  )
  const liveToolMapped = liveToolBridge.filter((e) => e.uri !== null)
  const liveToolUnmapped = liveToolBridge.filter((e) => e.uri === null)
  const canonicalFaceMapped = canonicalFaceBridge.filter((e) => e.uri !== null)
  const canonicalFaceUnmapped = canonicalFaceBridge.filter((e) => e.uri === null)
  writeJson('web_tool_bridge.generated.json', {
    generated_at: generatedAt,
    generator: 'generate_projections.ts',
    source:
      'getCatalog() capability names + canonical_faces.json deprecated_aliases + ' +
      'tool_name_bridge.ts TOOL_NAME_TO_URI/MCP_TO_RETRIEVAL_TOOL (chained, not re-authored)',
    vidhi_live_tool_bridge: {
      total: liveToolBridge.length,
      mapped: liveToolMapped.length,
      unmapped: liveToolUnmapped.length,
      entries: liveToolBridge,
    },
    canonical_faces_bridge: {
      total: canonicalFaceBridge.length,
      mapped: canonicalFaceMapped.length,
      unmapped: canonicalFaceUnmapped.length,
      entries: canonicalFaceBridge,
    },
  })

  // (f) W5 L1 — per-family tool-def projection: MCP annotations already ride
  // inline on (a)/(b) above (`annotations` field, added this lane). This 6th
  // artifact is the `family_overrides` + `input_examples`/`search_result`
  // emission the brief's W5 standing scope line names — merges any declared
  // `cap.family_overrides[family]` onto the base chat-tool-def shape, per
  // model family (anthropic/gemini/openai/deepseek). Currently 0/118 live
  // capabilities declare a real override (W2's deliberate, documented
  // non-population — editorial judgment, not this campaign's job to
  // fabricate) so every family's projection is mechanically IDENTICAL to the
  // base chat projection today. That is the CORRECT, expected output of a
  // real merge-with-no-overrides-present, not a bug — the mechanism is real
  // and tested (see `family_projection.test.ts`); population is a future
  // editorial wave's job, same disposition W2 already recorded.
  const familyToolDefs = buildAllFamilyToolDefs(caps)
  const familyCollisions = Object.fromEntries(
    MODEL_FAMILIES.map((f) => [f, findFamilyNameCollisions(familyToolDefs[f])]),
  )
  const familyOverrideCounts = Object.fromEntries(
    MODEL_FAMILIES.map((f) => [f, familyToolDefs[f].filter((d) => d.has_override).length]),
  )
  writeJson('family_tool_defs.generated.json', {
    generated_at: generatedAt,
    generator: 'generate_projections.ts',
    source:
      'getCatalog() capabilities with type=tool AND projection_tags includes "chat", merged with ' +
      'cap.family_overrides[family] per model family (types.ts FamilyOverrideSpec)',
    families: MODEL_FAMILIES,
    total_per_family: Object.fromEntries(MODEL_FAMILIES.map((f) => [f, familyToolDefs[f].length])),
    overrides_declared_per_family: familyOverrideCounts,
    name_collisions_per_family: familyCollisions,
    tool_defs: familyToolDefs,
  })

  // ── Comparison (a): generated chat defs vs the real served TOOL_CONTRACTS ──
  const contractNames = new Set(CONTRACT_CATALOG.map((c) => c.canonical_name))
  const generatedChatNames = new Set(chatDefs.map((d) => d.name))
  const chatOverlap = [...contractNames].filter((n) => generatedChatNames.has(n)).sort()
  const chatOnlyInContracts = [...contractNames].filter((n) => !generatedChatNames.has(n)).sort()
  const chatOnlyInGenerated = [...generatedChatNames].filter((n) => !contractNames.has(n)).sort()

  // ── Comparison (b): generated MCP tool projection vs the ~25 hand-written blocks ──
  const bridgeBlocks = extractRegistryBridgeToolsFromDisk()
  const bridgeNames = new Set(bridgeBlocks.map((b) => b.tool_name))
  const generatedMcpNames = new Set(mcpTools.map((t) => t.tool_name))
  const mcpNameOverlap = [...bridgeNames].filter((n) => generatedMcpNames.has(n)).sort()
  const bridgeOnlyNames = [...bridgeNames].filter((n) => !generatedMcpNames.has(n)).sort()
  const generatedOnlyNames = [...generatedMcpNames].filter((n) => !bridgeNames.has(n)).sort()

  // Which registry URIs the 25 hand-written tools actually reach (by literal
  // marsys:// reference in their body) vs. the full catalog — the "how many
  // of the 120 are reachable by name today" question the plan's item 3 (One
  // Bootstrap) and item 4 (Alias cutover) care about.
  const bridgeReferencedUris = new Set(bridgeBlocks.flatMap((b) => b.referenced_uris))
  const catalogUris = new Set(caps.map((c) => c.uri))
  const reachableViaBridge = [...catalogUris].filter((u) => bridgeReferencedUris.has(u)).sort()
  const unreachableViaBridge = [...catalogUris].filter((u) => !bridgeReferencedUris.has(u)).sort()
  const bridgeUrisNotInCatalog = [...bridgeReferencedUris].filter((u) => !catalogUris.has(u)).sort()

  const noDescriptionBridgeTools = bridgeBlocks.filter((b) => b.description === null).map((b) => b.tool_name)

  const typeCounts: Record<string, number> = {}
  for (const c of caps) typeCounts[resolveType(c)] = (typeCounts[resolveType(c)] ?? 0) + 1

  // ── Write comparison JSON (machine-readable) alongside the human report ──
  writeJson('comparison_report.generated.json', {
    generated_at: generatedAt,
    catalog_total: caps.length,
    catalog_by_type: typeCounts,
    chat_projection: {
      generated_count: chatDefs.length,
      tool_contracts_count: CONTRACT_CATALOG.length,
      overlap_by_name: chatOverlap,
      only_in_tool_contracts: chatOnlyInContracts,
      only_in_generated: chatOnlyInGenerated,
    },
    mcp_projection: {
      generated_count: mcpTools.length,
      excluded_non_tool_count: mcpNonTools.length,
      registry_bridge_block_count: bridgeBlocks.length,
      registry_bridge_source: REGISTRY_BRIDGE_PATH,
      name_overlap: mcpNameOverlap,
      only_in_registry_bridge: bridgeOnlyNames,
      only_in_generated: generatedOnlyNames,
      registry_bridge_tools_without_top_level_description: noDescriptionBridgeTools,
      catalog_uris_reachable_via_registry_bridge: reachableViaBridge,
      catalog_uris_reachable_via_registry_bridge_count: reachableViaBridge.length,
      catalog_uris_unreachable_via_registry_bridge_count: unreachableViaBridge.length,
      registry_bridge_uris_not_found_in_live_catalog: bridgeUrisNotInCatalog,
    },
  })

  // ── Human-readable report ──
  const report = `---
artifact: R1_PROJECTION_COMPILER_REPORT.md
canonical_id: R1_PROJECTION_COMPILER_REPORT
version: 1.0
status: GENERATED — regenerate via \`npx tsx --conditions=react-server scripts/manifest/generate_projections.ts\`
generated_at: ${generatedAt}
generator: platform/scripts/manifest/generate_projections.ts
---

# R-1 Projection Compiler Report (plan §3 R-1 item 2)

ADDITIVE ONLY. Nothing below is wired into any live-serving path. This document is
regenerated, not hand-maintained — see the generator's own header comment for scope.

## 0. Live catalog snapshot

\`getCatalog()\` returned **${caps.length}** live capabilities at generation time.

By resolved type: ${Object.entries(typeCounts).map(([t, n]) => `**${t}**=${n}`).join(', ')}.

(6 of these resolve \`type\` via a \`primitive_type\` fallback — a real, pre-existing
registry inconsistency this generator tolerates rather than papers over; see
\`machine_census.generated.json\`'s \`summary.type_resolved_via_primitive_type_fallback\`.)

## 1. (a) Chat tool-def projection vs. the real served chat contract catalog

Generated chat projection (type=tool + \`projection_tags\` includes \`chat\`):
**${chatDefs.length}** tool defs.

Real served chat contract catalog (\`TOOL_CONTRACTS\`, \`platform/src/lib/contract/registry.ts\`):
**${CONTRACT_CATALOG.length}** entries. (The plan's GT-3 citation says 6; this worktree's live
\`registry.ts\` has ${CONTRACT_CATALOG.length} — flagged, not silently reconciled; see §4 below.)

- Overlap by name: ${chatOverlap.length ? chatOverlap.join(', ') : '(none)'}
- Only in \`TOOL_CONTRACTS\` (not reachable via the generated chat projection today):
  ${chatOnlyInContracts.length ? chatOnlyInContracts.join(', ') : '(none)'}
- Only in the generated projection (new capabilities \`TOOL_CONTRACTS\` never covered):
  ${chatOnlyInGenerated.length} names — see \`comparison_report.generated.json\`
  \`chat_projection.only_in_generated\` for the full list (too long to inline).

**Reading:** \`TOOL_CONTRACTS\` is a hand-authored 5-classical-text-tool surface that predates
the registry (\`lib/retrieve/index.ts\`'s own header: "DEPRECATED as of D7... 17+ active
callers... still depend on it"). The generated projection draws from the registry's
${chatDefs.length} chat-tagged capabilities instead — a near-complete disjoint set by name,
because they were never the same catalog. This is the exact triplication the plan's R-1
opening line names ("kill the triplication") — the projection compiler does not resolve it
by itself (that is item 3, One Bootstrap, and item 4, Alias cutover — explicitly out of this
additive-only lane's scope); it makes the size and shape of the gap machine-legible for the
first time.

## 2. (b) MCP tool-registration projection vs. the ~25 hand-written \`server.tool\` blocks

Generated MCP projection (type=tool + \`projection_tags\` includes \`mcp_full\`):
**${mcpTools.length}** tool registrations (+ ${mcpNonTools.length} mcp-tagged
resources/prompts that would need \`server.resource()\`/\`server.prompt()\`, not
\`server.tool()\` — listed separately, not folded in).

Real hand-written \`server.tool(...)\` blocks extracted from
\`platform-mcp/src/tools/registry_bridge.ts\` (mechanical text scan, not hand-counted):
**${bridgeBlocks.length}** blocks.

- Name overlap: ${mcpNameOverlap.length} → ${mcpNameOverlap.join(', ') || '(none)'}
- Only in \`registry_bridge.ts\` (workflow-shaped consolidated names with no 1:1 registry
  capability of the same name): ${bridgeOnlyNames.join(', ') || '(none)'}
- Only in the generated projection: ${generatedOnlyNames.length} names (the granular
  registry capability set the hand-written file does not expose under its own name —
  see \`comparison_report.generated.json\` for the full list).
- ${noDescriptionBridgeTools.length} of the ${bridgeBlocks.length} hand-written blocks use the
  SDK's 3-arg overload (name, schema, handler) with **no top-level description literal**:
  ${noDescriptionBridgeTools.join(', ')}.

**Reachability cross-check** (does a registry capability have ANY route through the current
hand-written 25, by literal \`marsys://\` URI reference in that tool's body — not by name):
**${reachableViaBridge.length} / ${caps.length}** catalog URIs are referenced somewhere in
\`registry_bridge.ts\`; **${unreachableViaBridge.length} / ${caps.length}** are not referenced
by literal URI anywhere in that file (they may still be reachable via a different bridge file,
a resource loader, or not yet individually exposed on MCP at all — this scan is scoped to
\`registry_bridge.ts\` only, per this lane's (b) sub-item; a full-surface reachability
cross-check across every MCP bridge file is a larger census, not this generator's job).
${bridgeUrisNotInCatalog.length > 0 ? `\n${bridgeUrisNotInCatalog.length} URI(s) referenced in \`registry_bridge.ts\` do not resolve to any live \`getCatalog()\` capability: ${bridgeUrisNotInCatalog.join(', ')} (stale reference, or a capability registered under a different URI since — not investigated further here, out of this lane's scope).` : ''}

**Reading:** the plan's own framing ("replacing the ~25 hand-written server.tool blocks...
with a loop over compiled defs — handlers stay hand-written; surfaces are generated") implies
a MUCH larger generated MCP surface (near-1:1 with the registry, ${mcpTools.length} tools) than
today's curated ${bridgeBlocks.length}-tool consolidation. The hand-written file fans multiple
registry capabilities into single workflow-shaped tools (e.g. \`get_chart_orientation\` wraps
\`marsys://tool/L2/query_ucd\` plus a \`get_chart_header\` follow-up call) and adds real business
logic (response-format bounding, v3 envelope population, budget trimming) inside the handler —
none of which a projection compiler should try to synthesize. This report characterizes the
gap; it does not propose collapsing the two (see §4, out of scope this lane).

## 3. (c) Machine census

\`machine_census.generated.json\` — **${caps.length}** entries, every field the registry
declares (uri/type/layer/name/scope/archetype/traversal_level/tool_role/data_source/
mutation/emits_references/lel_capable/calibration_context_only/bearing_first/
required_inputs/projection_tags/display/annotations + presence flags for
density_contract/output_schema/family_overrides/register.glossary/drill_children).
Also emitted as the summary block inline in that same file (\`summary.by_layer\`,
\`by_type\`, \`by_scope\`, \`by_archetype\`, \`by_tool_role\`, \`by_data_source\`,
\`by_projection_tag\`). This is the "machine-generated census" the plan's item 2d calls for
— kills the need to hand-recount (the exact failure mode the plan's §1.1/GT findings name
for \`server.ts\`'s own comment-based count).

## 4. (d) Docs resource stub — \`marsys://resource/catalog\` shape

\`docs_resource_catalog.generated.json\` — a resource-shaped document (\`uri:
"marsys://resource/catalog"\`, \`mime_type: "application/json"\`) listing every live
capability's uri/type/layer/name/short_label/one_line/scope/archetype/tool_role/
projection_tags, so any MCP client could self-orient by reading one resource. This is a
STUB in the sense that it is generated as a static JSON artifact here, not wired to
\`server.resource("marsys://resource/catalog", ...)\` on the live MCP server (that wiring
is a live-serving-path change, explicitly out of this additive-only lane's scope per the
task's own instruction — "new code paths gated behind an explicit flag that defaults OFF").

## 5. (e) Web↔MCP tool-name bridge (W5 L1)

\`web_tool_bridge.generated.json\` — resolves the Vidhi floor compiler's
\`live_tool\` namespace (${liveToolNames.length} distinct names across
\`registry_data.ts\`) plus the full \`canonical_faces.json\` list
(${canonicalFaces.canonical_faces.length} names) to registry URIs, by chaining
\`getCatalog()\` capability names + \`canonical_faces.json\`'s \`deprecated_aliases\`
+ \`tool_name_bridge.ts\`'s existing hand-curated maps (not re-authored — chained).

- Vidhi \`live_tool\` bridge: **${liveToolMapped.length} / ${liveToolBridge.length}** resolve to a
  registry URI (before this lane's generated projection, \`compiled_floor_adapter.ts\`'s
  hand-curated \`LIVE_TOOL_TO_RETRIEVAL\` mapped only **4 / ${liveToolNames.length}**).
  Unmapped: ${liveToolUnmapped.length ? liveToolUnmapped.map((e) => e.name).join(', ') : '(none)'}.
- \`canonical_faces.json\` bridge (broader census): **${canonicalFaceMapped.length} / ${canonicalFaceBridge.length}**
  resolve to a registry URI. ${canonicalFaceUnmapped.length} remain unmapped — see
  \`web_tool_bridge.generated.json\`'s \`canonical_faces_bridge.entries\` for the
  full per-name resolution_kind/via chain (not inlined here, too long).

**Wiring status:** \`tool_name_bridge.ts\`'s \`resolveToolUri()\` now falls back to
this generated projection (\`resolveGeneratedToolUri\`) for any name not already
in its hand-curated \`TOOL_NAME_TO_URI\`, and resolves literal registry URIs
directly (the CR-118 fast-fail fix — see that file's \`isCapabilityUri\` doc
comment). \`compiled_floor_adapter.ts\`'s \`LIVE_TOOL_TO_RETRIEVAL\` now consults
this generated bridge before falling back to its small hand-curated map, raising
Vidhi floor-primitive mappability from 4/${liveToolNames.length} toward
${liveToolMapped.length}/${liveToolNames.length} without hand-editing that file.

## 6. (f) Per-family tool-def projection (W5 lane L3 — annotations + family_overrides + input_examples/search_result emissions)

\`family_tool_defs.generated.json\` — the base chat tool-def projection (§1 above),
merged per model family (${MODEL_FAMILIES.join('/')}) with any declared
\`cap.family_overrides[family]\` (types.ts \`FamilyOverrideSpec\`:
\`description_override\`/\`name_override\`/\`strict_schema\`/\`input_examples\`/
\`search_result_content_block\`). Every emitted tool def also now carries an
\`annotations\` block in the REAL MCP \`ToolAnnotations\` wire shape
(\`readOnlyHint\`/\`destructiveHint\`/\`idempotentHint\`/\`openWorldHint\`/\`title\`,
verified against this repo's installed \`@modelcontextprotocol/sdk\` — not guessed) —
the same \`annotations\` addition also lands on (a) chat tool defs and (b) MCP tool
registrations above, additively alongside their pre-existing \`read_only\`/
\`destructive\` fields.

Overrides declared per family today: ${MODEL_FAMILIES.map((f) => `**${f}**=${familyOverrideCounts[f]}`).join(', ')}
(0 across the board — W2's descriptor-migration lane deliberately left
\`family_overrides\` at 0/118, "requires genuine per-capability editorial judgment
[...] left for a future, explicitly-scoped editorial wave" — that ruling stands;
this lane builds the EMISSION mechanism the override merge needs, not the editorial
content). Every family's projection is therefore mechanically identical to the base
chat projection today — the CORRECT output of a real merge with no overrides
present, not a gap in this lane. Name collisions per family (would only appear once
\`name_override\` population starts): ${MODEL_FAMILIES.map((f) => `**${f}**=${familyCollisions[f].length}`).join(', ')}.

**Wiring status:** additive only, same as every other projection here — nothing in
this artifact is consumed by \`getCatalog()\`, the chat pipeline's MARO adapter, or
any live \`server.tool()\` call. The day an editorial wave populates a real
\`family_overrides\` entry on any capability, this generator picks it up on its next
run with zero code changes (verified in \`family_projection.test.ts\` via test-local
mock overrides exercising every merge path: \`description_override\`, \`name_override\`,
\`strict_schema\`'s additionalProperties:false/all-required transform,
\`input_examples\` pass-through, \`search_result_content_block\`).

## 7. Honesty notes / what's NOT done this lane

- Plan item 2c ("the vidhi primitive rows' tool bindings") is **not** covered by this
  generator — it is the separately-landed \`codegen:vidhi\`/\`codegen:vidhi:check\` lane
  (GT-56, \`scripts/generate_vidhi_registry_mirror.ts\`), found already present in this
  worktree at lane open (concurrent W2 work). Not duplicated.
- The MCP tool-registration projection emits **shape only** (name/description/JSON-Schema
  input_schema) — it does NOT generate zod source code or an actual \`server.tool()\` call
  loop. Wiring that (replacing the hand-written blocks with "handlers stay hand-written;
  surfaces are generated") is real follow-on codegen work (closer to
  \`generate_registry_shims.ts\`'s zod-source-emission pattern) not attempted here — the
  task explicitly permits stubbing (b)/(d) if full fidelity isn't reached; this lane
  reached full fidelity on the DATA SHAPE of (b) but not on TS-source emission.
- \`TOOL_CONTRACTS\` count discrepancy: the plan (GT-3) says 6 entries; this worktree's live
  \`registry.ts\` has ${CONTRACT_CATALOG.length}. Not investigated further (reading, not
  editing, per this lane's scope) — flagged for whoever owns GT-3's ground truth next.
- The registry-bridge extractor is a text scan (documented method in
  \`extract_registry_bridge_tools.ts\`'s header), not a TS/AST parse. It is defended by a
  parity-test tripwire (known tool names must round-trip) rather than claimed complete
  against arbitrary future syntax changes to that file.
`
  mkdirSync(dirname(REPORT_PATH), { recursive: true })
  writeFileSync(REPORT_PATH, report, 'utf-8')
  console.log(`[generate_projections] wrote ${REPORT_PATH}`)
}

main()

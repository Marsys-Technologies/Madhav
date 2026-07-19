---
artifact: TOOL_SHAPE_DESIGN.md
canonical_id: NATIVE_REVIEW_PACKET_W1_TOOL_SHAPE_DESIGN
version: 1.0
status: NATIVE REVIEW PACKET — §F human gate deliverable 3/5
governing_brief: RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md §F item 3
source_data:
  - 00_ARCHITECTURE/RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md §3 R-1, R-4
  - platform/src/lib/retrieval/registry/types.ts (D1 amendment_version 2)
  - platform/src/lib/retrieval/registry/layers/register_d7_channel.ts (chart_facts_query descriptor)
  - 00_ARCHITECTURE/briefs/retrieval_impl/DARK_SET_WIRING_PLAN_v1_0.md
  - platform/src/lib/retrieval/registry/service_manifest/DESIGN_KA_GRAHA_SANCARA_WIRING.md
generated_for_native: 2026-07-20
---

# Tool-Shape Design — the proposed umbrella/drill/bundle topology + extended descriptor contract

## 1. The topology (from the plan's own R-1/R-4 design, not a fresh idea)

Per `RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md` §3 R-1 item 2 ("Build the projection compiler") and
R-4 item 1 ("Enforce the surface spec at the edge"): **one registry, many generated projections**
(OT-7, already adopted — `RULINGS_ADOPTED.md`). The registry (`CapabilityDescriptor[]` in
`platform/src/lib/retrieval/registry/`) is the sole author surface; a build-time compiler emits:

- **Chat tool defs** — absorbing the real served chat contract catalog (`TOOL_CONTRACTS`, 6
  entries) and retiring the unused 76-row audit-only `ToolReconciliationEntry` table.
- **MCP-full** (expert) — every registered capability, current shape (~118 today).
- **MCP-compact** (~25–35 umbrellas, RC-1 ruling) + a `marsys_drill` dispatcher reaching leaves via
  `drill_pointers`.
- **MCP-consult** (OT-10: `prashna_ask` + ~5 orienting tools) — the minimal surface a
  consult-scoped OAuth principal can reach; provably cannot obtain raw tools (R-4 gate).
- **A docs resource** (`marsys://resource/catalog`) so any client self-orients without a hand-typed
  census.

**Profile selection = entitlement** (OT-10 b+c, adopted): OAuth scope / connect URL picks the
projection at connect time, not per-call. `family_overrides` (§2 below) drives per-LLM-family
description length and schema strictness within whichever projection is selected (RC-1: Claude
family gets compact 25–35 + tool-search metadata; non-Claude families ≤20 umbrellas; RC-2 ChatGPT
search/fetch connector = deferred; RC-3 DeepSeek = consult-profile only).

**Today's real baseline this topology replaces:** 118 live capabilities, 0/118 with
`projection_tags` populated (census A8 finding), 0/118 implementing the v3 envelope yet (census A3
finding — exactly 1 repo-wide `buildRetrievalEnvelope()` call site). The topology above is the
target state; populating it across the estate is explicitly W2's migration, not W1's (per the
master brief's wave sequencing).

## 2. The extended descriptor contract (9 new fields, D1 `amendment_version` 1→2, type-only this wave)

Landed in `platform/src/lib/retrieval/registry/types.ts` on `CapabilityDescriptorBase`. All 9 are
**optional** — zero of the ~118 existing descriptors were touched this wave; populating them is W2.

| field | shape | purpose |
|---|---|---|
| `display` | `{ short_label?, one_line?, full_description? }` | Reader-facing display strings, length-disciplined per surface — short_label for compact umbrella lists, one_line for the docs index/chat tool-picker, full_description as an optional override of `description`. |
| `annotations` | `{ read_only?, idempotent?, destructive?, open_world? }` | MCP-spec behavioral annotations (closes GT-30 — zero MCP annotations found anywhere at audit time). Lets a foreign LLM client's approval flow relax on the read-only majority without inferring read-vs-write from prose. |
| `register` | `{ glossary?: Record<string,string>, enforce_complete? }` | Reader-facing plain-language glossary for internal tokens the output emits (SIG.MSR.* ids, marsys:// URIs, flag/grade codes) — rides in the v3 envelope so a careless-reading foreign LLM still gets the label next to the token. `enforce_complete` reserves a future CI register-linter hook. |
| `mutation` | `boolean` | A-04 mutation capability class. Absent/false = read-only (the overwhelming majority today). True marks write-capable tools (outcome recording, prediction filing) so the compiler/family-overrides can treat them distinctly from reads. |
| `projection_tags` | `Array<'chat'\|'mcp_full'\|'mcp_compact'\|'mcp_consult'>` | Which generated surfaces serve this capability. Absent = not yet classified (0/118 today — census A8 finding); classification is W2. |
| `family_overrides` | `{ anthropic?, gemini?, openai?, deepseek?: FamilyOverrideSpec }` | Per-family serving overrides — description/name overrides, strict-schema opt-in (OpenAI), few-shot examples only where they help (Claude) / omitted where they hurt (OpenAI reasoning models). Broader than the pre-existing `behavioral_overrides` field, which stays as-is this wave (consolidation is W2). |
| `data_source` | `'stored' \| 'computed' \| 'hybrid'` | Strategy §5.3 native ruling: every descriptor declares whether its output reads sealed build data, real-time sidecar compute, or both — so an LLM never mistakes a live transit for a sealed build fact (B.1 applied to time). |
| `demand_ranking` | `{ bearing_first?, static_salience? }` | Question-conditioned ranking hook — reserves the shape for generalizing `judgment_query`'s bearing-first ordering to every umbrella; `static_salience` is a fallback tiebreaker only, never the primary sort key. |
| `calibration_context_only` | `boolean` | NO-LEAKAGE arms 2 & 4 (ruling F-R7): flags outcome/LEL-read tools whose role is calibration-context supply only — excluded from ALL projections and `prashna_ask`'s tool set. This wave lands the flag; enforcement (compiler filter + CI canary) is R-4's job. |

## 3. Three worked examples (one per §9.6 lifecycle scenario)

### (a) EXISTING asset — `chart_facts_query` (already served, real descriptor)

Real descriptor today (`register_d7_channel.ts`, `uri: 'marsys://tool/L1/chart_facts_query'`,
`layer: 'L1'`, `scope: 'per_chart'`) — the single umbrella reaching all 218 fact_category concepts
(Group 1 of CONCEPT_TOOL_MAPPING.md). Sketch of how the 9 new fields would populate:

```jsonc
{
  "uri": "marsys://tool/L1/chart_facts_query",
  // ...existing fields unchanged (type, layer, name, scope, description, input_schema)...
  "display": {
    "short_label": "Chart facts lookup",
    "one_line": "Parametric lookup over any of 218 chart_facts categories (positions, dignities, strengths, yogas, doshas, divisionals).",
    // full_description omitted — falls back to the existing `description` prose (already comprehensive)
  },
  "annotations": {
    "read_only": true,
    "idempotent": true,
    "destructive": false,
    "open_world": false
  },
  "register": {
    "glossary": {
      "about_resolution": "the resolution chain from an `about` facet address (e.g. house_lord:10) to the concrete graha/subject it resolved to",
      "fact_id": "chart_facts primary key; every pivoted field cites its source fact_id for Bodha back-reference"
    }
  },
  "mutation": false,
  "projection_tags": ["chat", "mcp_full", "mcp_compact"],
  // not "mcp_consult" — this is a full-detail retrieval leaf, not an orienting tool
  "data_source": "stored",
  // reads sealed chart_facts build data exclusively, no real-time compute
  "demand_ranking": { "bearing_first": false, "static_salience": 0.9 },
  // high static salience (near-universal utility) as a fallback tiebreaker only
  "calibration_context_only": false
}
```

### (b) ELEVATED asset — `bodha_triangulation` (real DARK-but-should-be-served concept)

From `DARK_SET_WIRING_PLAN_v1_0.md`: 200 real rows on the live chart (not empty), `NEEDS-OWNER`,
flagged by L1b's own rationale as "the most consequential DARK class: real data with no discovered
TS-registry route." Proposed new leaf tool `bodha_triangulation_get`, sketched under the extended
contract (illustrative — the FK/standalone-vs-facet decision from the wiring plan is not made
here):

```jsonc
{
  "uri": "marsys://tool/L2/bodha_triangulation_get",
  "type": "tool",
  "layer": "L2",
  "name": "bodha_triangulation_get",
  "scope": "per_chart",
  "description": "Reads bodha_triangulation — cross-signal triangulation rows joining MSR/discovery evidence into converging-evidence clusters. Drill leaf off bodha_discoveries_get/bodha_signals_get once triangulation rows' FK shape confirms they reference bodha_discoveries or bodha_msr_signals fact_ids (per the wiring plan's own open question).",
  "input_schema": { "chart_id": { "type": "string", "required": true }, "min_convergence": { "type": "number" } },
  "traversal_level": "L-SOURCE",
  "tool_role": "drill",
  "emits_references": true,
  "display": {
    "short_label": "Triangulation clusters",
    "one_line": "Cross-signal convergence clusters (200 rows on the live chart) — where independent MSR/discovery evidence lines corroborate one another."
  },
  "annotations": { "read_only": true, "idempotent": true, "destructive": false, "open_world": false },
  "register": {
    "glossary": { "triangulation_cluster": "a set of independently-derived signals whose evidence converges on the same claim" }
  },
  "mutation": false,
  "projection_tags": ["mcp_full", "mcp_compact"],
  // not "chat" initially — drill-only depth, elevate to chat once demand is observed
  "data_source": "stored",
  "demand_ranking": { "bearing_first": true, "static_salience": 0.4 },
  "calibration_context_only": false
}
```
Elevation path: (1) confirm FK shape (standalone vs. facet-on-existing per the wiring plan);
(2) commission under W-27's CI commissioning contract (same contract exercised live in worked
example (c) below); (3) land `table_hint`/harvest re-run so the concept_ledger row for
`bodha_triangulation` (currently `dark_table`/`NEEDS-OWNER`) flips to `service_endpoint`/`SERVED`
at the next harvest regeneration — the ledger is the durable record of the lifecycle transition,
not a one-off doc edit.

### (c) NEW asset — `ka_graha_sancara` (`call_ephemeris_at_t`, commissioning a dark service)

From `DESIGN_KA_GRAHA_SANCARA_WIRING.md`: the MCP-facing capability already exists
(`call_ephemeris_at_t`, `L3_kala/call_service_wrappers.ts:155-216`) but its handler
(lines 196-214) unconditionally errors — "not yet wired to a compute sidecar endpoint." The design
note proposes a new sidecar route `POST /api/compute/ephemeris_at_t` (extending
`routers/ephemeris.py`, which already imports `swisseph` and factors out `_position_from_lon`) and
replacing the stub with a real `fetch()` following the `callTransitSearchCapability` pattern in the
same file. Descriptor sketch once wired (today's descriptor already declares the input_schema
correctly — `datetime_utc`, `ayanamsha_id`; commissioning changes the handler body and adds the
9 new fields):

```jsonc
{
  "uri": "marsys://tool/L3/call_ephemeris_at_t",
  "type": "tool",
  "layer": "L3",
  "name": "call_ephemeris_at_t",
  "scope": "global",
  // global — graha longitudes are geocentric, no chart_id/lat/lng needed, per the design note §1
  "description": "Computes sidereal graha longitudes at an arbitrary UTC instant via the sidecar's swisseph integration (extends /ephemeris's existing sign/nakshatra/pada shaping). Distinct from the bounded 1900-2150 daily-grain ephemeris_daily table — this is live sub-day-precision compute, no build_id.",
  "input_schema": {
    "datetime_utc": { "type": "string", "required": true, "description": "ISO 8601 UTC instant, e.g. 2026-07-20T12:00:00Z" },
    "ayanamsha_id": { "type": "string", "description": "default lahiri_chitrapaksha" }
  },
  "display": {
    "short_label": "Graha positions at time T",
    "one_line": "Live sidereal planet longitudes at any UTC instant (not bounded to a stored chart or a 1900-2150 daily table)."
  },
  "annotations": { "read_only": true, "idempotent": true, "destructive": false, "open_world": false },
  "register": {
    "glossary": { "ayanamsha_id": "which sidereal-zodiac correction is applied; unrecognized ids must fail loud, never silently fall back to tropical (design note §3 item 5)" }
  },
  "mutation": false,
  "projection_tags": ["mcp_full", "mcp_compact"],
  "data_source": "computed",
  // real-time sidecar compute, no build_id — carries its own computed_at + swisseph-engine-version provenance instead
  "demand_ranking": { "bearing_first": false, "static_salience": 0.5 },
  "calibration_context_only": false
}
```

**Commissioning gate (W-27, per the master brief's V2 acceptance criteria):** "commissioning
contract CI live and demonstrated on one asset" — `ka_graha_sancara` is the natural first live
test of that contract precisely because its design is already fully specified (this note) and its
descriptor's `input_schema` requires zero breaking change, only a handler-body replacement + the 9
new fields. The design note explicitly leaves two decisions for native sign-off before W2 wires
this: (1) whether `/ephemeris` should be shared-refactored or duplicated for the arbitrary-instant
use case; (2) whether `ka_muhurta_seva` (the sibling dark service, same stub shape) should be
co-wired in the same pass.

---

*End of TOOL_SHAPE_DESIGN v1.0 — NATIVE_REVIEW_PACKET_W1, deliverable 3/5. All three worked
examples are illustrative descriptor sketches under the extended contract — none are landed code;
W2 is where any of this actually ships.*

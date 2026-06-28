---
canonical_id: RETRIEVAL_D7_GAP_REPORT
version: 1.0
status: CURRENT
created: 2026-06-28
author: Claude Code (Gap Analysis + Port Agent — D7 Chat-Channel Migration)
classification: Migration gap report — §2 deliverable of CLAUDECODE_BRIEF_RETRIEVAL_D7_CHAT_MIGRATION_v1_0
parent: CLAUDECODE_BRIEF_RETRIEVAL_D7_CHAT_MIGRATION_v1_0 §2
scope: Read-only analysis + registry additions. No callers repointed (that is §3).
gate_result: chart_agnostic_gate PASS — 7 D7 capabilities checked, 0 violations
---

# RETRIEVAL D7 GAP REPORT v1.0

Gap analysis for the D7 chat-channel migration (§2 deliverable).
Covers all lib/retrieve capabilities the chat path depends on, cross-checked
against the sealed D1–D6 registry, with gap-fill capabilities added to
`register_d7_channel.ts`.

---

## §1 — Methodology

1. Read `RETRIEVAL_D7_CALLER_MAP_v1_0.md` for the authoritative chat-path tool inventory.
2. Enumerated all `RETRIEVAL_TOOLS` in `lib/retrieve/index.ts` (direct + via CLASSICAL_TOOLS,
   SUTRAVALI_RETRIEVAL_TOOLS, REMEDY_TOOLS imports).
3. Grepped `uri:` across all registry layer files (L0–L5 + D5/D6/D7 wave files).
4. For each lib/retrieve tool the chat path calls via `getTool()`: checked whether a
   registry equivalent exists (URI match or functional equivalence).
5. Added D1-contract-conformant capabilities for each real gap.
6. Ran `chart_agnostic_gate` against the 7 new D7 capabilities.

---

## §2 — Coverage map (pre-gap-fill)

### Tools already covered by registry (NO GAP)

| lib/retrieve tool name | Registry URI | Notes |
|---|---|---|
| `msr_sql` | `marsys://tool/L2/query_signals` | Full coverage — domain, salience, lel filters, semantic_query |
| `read_classical_text` | `marsys://tool/L0/query_classical_texts` | L0FR Stream C |
| `search_classical_texts` | `marsys://tool/L0/query_classical_texts` | Alias — same handler |
| `find_verses_about` | `marsys://tool/L0/query_classical_texts` | Same handler; topic param |
| `read_chapter` | `marsys://tool/L0/query_classical_texts` | Same handler; chapter param |
| `list_classical_texts` | `marsys://tool/L0/query_classical_texts` | Same handler; list op |
| `query_remedies` (remedy_tools.ts) | `marsys://tool/L0/query_remedy_corpus` + `marsys://tool/L2/query_remedies` | Planet/domain/category covered |
| `query_remedies_for_chart` | `marsys://tool/L2/query_remedies` | chart_id + affliction path |
| `list_remedies_by_category` | `marsys://tool/L0/query_remedy_corpus` | category filter |
| `read_remedy` | `marsys://tool/L0/query_remedy_corpus` | offset=0 limit=1 + remedy_id |
| `query_tantric_remedies` | `marsys://tool/L0/query_remedy_corpus` | category=tantric_heavy filter |
| `query_remedies_by_planet` | `marsys://tool/L0/query_remedy_corpus` | graha filter |
| `query_mantras` | `marsys://tool/L0/query_remedy_corpus` | category=mantra filter |
| `compute_natal_positions` | `marsys://tool/L1/get_positions` | L1 Gaṇita |
| `query_dasha_periods` | `marsys://tool/L1/get_dashas` | L1 Gaṇita |
| `query_special_lagnas` | `marsys://tool/L1/get_sensitive_points` | L1 Gaṇita |

### Tools NOT in RETRIEVAL_TOOLS (silently skipped by `getTool()` — NO GAP in dispatch)

These tool names appear in B.11 injection arrays and `tools_authorized` lists, but
`getTool(name)` returns `undefined` for all of them. The chat route at line 699 does
`if (!t) return null` — silent skip. They are stub/planned capabilities not yet
implemented in lib/retrieve. No dispatch gap exists to fill.

| Tool name | Notes |
|---|---|
| `msr_sql` | NOTE: `msr_sql` IS dispatched but has no `RetrievalTool` entry — getTool returns undefined. B.11 injection injects it as a PlanStep but the tool fetch silently skips it. The registry has `query_signals` which IS the functional equivalent. See §3 note. |
| `pattern_register` | Not in RETRIEVAL_TOOLS — future L2 tool; stub only |
| `resonance_register` | Not in RETRIEVAL_TOOLS — future L2 tool; stub only |
| `vector_search` | Not in RETRIEVAL_TOOLS — future embedding search tool |
| `cgm_graph_walk` | Not in RETRIEVAL_TOOLS — registry has `traverse_chart_graph` (L2) |
| `classical_attribution_lookup` | NOT imported into RETRIEVAL_TOOLS (only in lib/tools/) |

**Clarification on `msr_sql`:** The contract registry (`tool_metadata.ts`) has a
`canonical_name: 'msr_sql'` entry and the B.11 floor injects `tool_name: 'msr_sql'` into
PlanSteps. However `lib/retrieve/index.ts` does NOT define a `RetrievalTool` with
`name: 'msr_sql'`. `getTool('msr_sql')` returns undefined. The MCP channel uses
`marsys://tool/L2/query_signals` directly. The D7 migration §3 must wire the contract
name `msr_sql` → URI `marsys://tool/L2/query_signals` when repointing callers.

### NOT a gap: `classical_disclosure_filter`

`classical_disclosure_filter.ts` is already RETIRED (its own header says so). The registry
does not need a capability for it — disclosure filtering at serve-time is handled at the
API/MCP boundary per the no-audience-tier principle. No registry capability needed.

### NOT a gap: `chart_facts_query`

`lib/retrieve/chart_facts_query.ts` is a TYPE STUB ONLY — the implementation was removed
in the legacy teardown. `getTool('chart_facts_query')` returns undefined. The registry
covers the functional ground via 19 L1 tools (get_positions, get_dashas, get_divisionals,
etc.). No single `chart_facts_query` URI is required.

---

## §3 — Identified GAPS (tools in RETRIEVAL_TOOLS with no registry equivalent)

Five tools in `RETRIEVAL_TOOLS` had no registry equivalent before this run:

| # | Gap name | lib/retrieve file | lib/retrieve tool name |
|---|---|---|---|
| G1 | Sutravali flexible query | `sutravali_tools.ts` | `query_rules` |
| G2 | Sutravali planet query | `sutravali_tools.ts` | `query_rules_for_planet` |
| G3 | Sutravali single rule fetch | `sutravali_tools.ts` | `read_rule` |
| G4 | Sutravali list by text | `sutravali_tools.ts` | `list_rules_by_text` |
| G5 | Classical attribution lookup | `classical_attribution_lookup_tool.ts` | `classical_attribution_lookup` |

Note: `classical_attribution_lookup_tool.ts` is NOT imported into `RETRIEVAL_TOOLS` in
`lib/retrieve/index.ts` — getTool() would return undefined. However it IS referenced in
the contract registry, router spec (`retrieval_capability_spec.ts`), and trace types. It
has no registry equivalent and IS part of the chat-path surface. Added as G5.

---

## §4 — Gap-fill capabilities added

All 5 gaps are filled by additions to
`platform/src/lib/retrieval/registry/layers/register_d7_channel.ts`.

### G1 — `marsys://tool/L0/query_sutravali_rules`

- **Old lib/retrieve code:** `sutravali_tools.ts::queryRulesTool` (`query_rules`)
- **New registry URI:** `marsys://tool/L0/query_sutravali_rules`
- **Scope:** `global` (sutravali_rules is a reference corpus, not per-chart)
- **Contract changes:** audience_tier stripped; limit capped at 200; sidecar URL from env
- **D1 fields:** archetype=`prose_citation`, traversal_level=`L-SOURCE`, tool_role=`hybrid_retrieval`, emits_references=`false`, lel_capable=`false`
- **Gate:** chart_agnostic_gate PASS

### G2 — `marsys://tool/L0/query_sutravali_rules_for_planet`

- **Old lib/retrieve code:** `sutravali_tools.ts::queryRulesForPlanetTool` (`query_rules_for_planet`)
- **New registry URI:** `marsys://tool/L0/query_sutravali_rules_for_planet`
- **Scope:** `global`
- **Contract changes:** audience_tier stripped; `planet` required; limit capped at 500
- **D1 fields:** archetype=`prose_citation`, traversal_level=`L-SOURCE`, tool_role=`drill`, emits_references=`false`, lel_capable=`false`
- **Gate:** chart_agnostic_gate PASS

### G3 — `marsys://tool/L0/read_sutravali_rule`

- **Old lib/retrieve code:** `sutravali_tools.ts::readRuleTool` (`read_rule`)
- **New registry URI:** `marsys://tool/L0/read_sutravali_rule`
- **Scope:** `global`
- **Contract changes:** audience_tier stripped; `rule_id` required
- **D1 fields:** archetype=`flat_fact`, traversal_level=`L-SOURCE`, tool_role=`leaf`, emits_references=`false`, lel_capable=`false`
- **Gate:** chart_agnostic_gate PASS

### G4 — `marsys://tool/L0/list_sutravali_rules_by_text`

- **Old lib/retrieve code:** `sutravali_tools.ts::listRulesByTextTool` (`list_rules_by_text`)
- **New registry URI:** `marsys://tool/L0/list_sutravali_rules_by_text`
- **Scope:** `global`
- **Contract changes:** audience_tier stripped; `text_id` required; limit/offset pagination
- **D1 fields:** archetype=`prose_citation`, traversal_level=`L-OVERVIEW`, tool_role=`drill`, emits_references=`false`, lel_capable=`false`
- **Gate:** chart_agnostic_gate PASS

### G5 — `marsys://tool/L2/classical_attribution_lookup`

- **Old lib/retrieve code:** `classical_attribution_lookup_tool.ts` (wraps `lib/tools/classical_attribution_lookup.ts`)
- **New registry URI:** `marsys://tool/L2/classical_attribution_lookup`
- **Scope:** `per_chart` — attributions are scoped to MSR signals which are per-chart
- **Contract changes:**
  - audience_tier stripped — `classical_disclosure_filter.ts` (RETIRED) gated on tier; that gating is removed. All content emitted; serve-time gating at API boundary only.
  - `chart_id` added as required input (chart_id was implicit before; now explicit per D1 contract)
  - `signal_ids` required (was already required in old tool)
- **D1 fields:** archetype=`prose_citation`, traversal_level=`L-SOURCE`, tool_role=`leaf`, emits_references=`true`, lel_capable=`false`, grounds_to={l1_fact_ids: true, l0_citation_ids: true}
- **Gate:** chart_agnostic_gate PASS (scope=per_chart, chart_id in required_inputs, no native id in description)

---

## §5 — Gate results

```
D7 capabilities to check: 7
  marsys://tool/channel/mcp_wiring | scope: global
  marsys://tool/channel/chat_dispatch | scope: global
  marsys://tool/L0/query_sutravali_rules | scope: global
  marsys://tool/L0/query_sutravali_rules_for_planet | scope: global
  marsys://tool/L0/read_sutravali_rule | scope: global
  marsys://tool/L0/list_sutravali_rules_by_text | scope: global
  marsys://tool/L2/classical_attribution_lookup | scope: per_chart

[chart_agnostic_gate] PASS — no violations found
```

---

## §6 — D7_CAPABILITY_URIS roster (final)

```typescript
export const D7_CAPABILITY_URIS = [
  'marsys://tool/channel/mcp_wiring',
  'marsys://tool/channel/chat_dispatch',
  'marsys://tool/L0/query_sutravali_rules',
  'marsys://tool/L0/query_sutravali_rules_for_planet',
  'marsys://tool/L0/read_sutravali_rule',
  'marsys://tool/L0/list_sutravali_rules_by_text',
  'marsys://tool/L2/classical_attribution_lookup',
] as const
```

---

## §7 — What this deliverable does NOT cover

This deliverable is §2 only (gap analysis + port). The following are §3–§6 work:

- **§3 (not done here):** Repointing chat-route callers (`getTool` → `getCapability`),
  parity tests (≥2 charts), type migration (`ToolBundle` → `ToolResult`)
- **§4 (not done here):** Legacy retirement (reverse-citation gate, `lib/retrieve/` deletion,
  `primitives_registry.ts` fold)
- **§6 (not done here):** D8 faithfulness eval against prod DB with judge model

The `chat_dispatch` descriptor in D7 documents the migration as PENDING for §3.

---

*End of RETRIEVAL_D7_GAP_REPORT v1.0.*
*Generated 2026-06-28 by Gap Analysis + Port Agent. chart_agnostic_gate: PASS.*

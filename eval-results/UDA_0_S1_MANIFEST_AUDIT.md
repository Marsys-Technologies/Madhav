---
title: "UDA-0-S1 — CAPABILITY_MANIFEST.json Audit Report"
session_id: UDA-0-S1
campaign: universal-parity
authored_on: 2026-05-25
status: COMPLETE
---

# UDA-0-S1: CAPABILITY_MANIFEST.json Audit Report

## 1. Summary Table

| Metric | Pre-session | Post-session |
|---|---|---|
| Total entries | 189 | 189 |
| Duplicate `canonical_id` values (gate-style) | 21 | 0 |
| Entries with missing `canonical_id` (used `id` field instead) | 22 | 0 |
| Entries missing required fields (canonical_id/status/version) | 31 | 18 |
| Stale paths (path declared but file absent) | 0 | 0 |

**Action taken:** 22 entries used `id` as their identifier field instead of `canonical_id`. These were distinct, non-duplicate entries (ingestion scripts and M9C analysis artifacts). Their `id` value was copied to `canonical_id` to satisfy the manifest schema. No entries were removed; the total count remains 189.

---

## 2. Per-Channel Tool Entry Counts

| Channel | Count |
|---|---|
| `portal` (retrieval_tool) | 0 |
| `mcp` (retrieval_tool) | 0 |
| Tool entries missing `channel` field | 31 |

**Note:** All 31 tool entries (26 `RETRIEVAL_TOOL_*` + 5 `*_TOOL`) lack a `channel` field. This is the primary gap to be filled by UDA-0-S2 (portal tool population) and UDA-0-S3 (MCP tool population). The existing tool entries represent the M5-A CAPABILITY_MANIFEST population from the retrieval tool layer; they predate the channel taxonomy.

### Tool entry breakdown (by canonical_id prefix/suffix):

| Pattern | Count | Examples |
|---|---|---|
| `RETRIEVAL_TOOL_*` | 26 | lel_query, cgm_graph_walk, temporal, vector_search, … |
| `*_TOOL` (non-RETRIEVAL_TOOL) | 5 | CLASSICAL_TEXT_SEARCH_TOOL, UCN_WALK_TOOL, CDLM_LOOKUP_TOOL, RM_WALK_TOOL, CLASSICAL_ATTRIBUTION_LOOKUP_TOOL |

---

## 3. Stale Paths

**None.** All 189 entries with a declared `path` resolve to an existing file. 0 stale paths.

---

## 4. Missing-Field Entries (Post-Session)

18 entries still lack one or more of the required fields (`canonical_id`, `status`, `version`). These are **not** within scope to fix in UDA-0-S1 (scope is dedup only); documented here for downstream sessions.

### Missing `status` (9 entries — RETRIEVAL_TOOL entries from M5-A):

| canonical_id | Missing field |
|---|---|
| RETRIEVAL_TOOL_lel_query | status |
| RETRIEVAL_TOOL_multi_school_signal_lookup | status |
| RETRIEVAL_TOOL_convergence_score_lookup | status |
| RETRIEVAL_TOOL_query_signal_state | status |
| RETRIEVAL_TOOL_query_kp_ruling_planets | status |
| RETRIEVAL_TOOL_query_varshaphala | status |
| UCN_WALK_TOOL | status |
| CDLM_LOOKUP_TOOL | status |
| RM_WALK_TOOL | status |

### Missing `version` (9 entries — M9C artifacts):

| canonical_id | Missing field |
|---|---|
| M9C_RUNNER_SCRIPT | version |
| M9C_MULTI_SCHOOL_ANALYSIS | version |
| M9C_PARASHARI_JSON | version |
| M9C_JAIMINI_JSON | version |
| M9C_TAJIKA_JSON | version |
| M9C_KP_JSON | version |
| M9C_NADI_JSON | version |
| M9C_BNN_JSON | version |
| M9C_YOGINI_JSON | version |

---

## 5. Entry Type Breakdown

| type field | Count |
|---|---|
| (none / missing type) | 143 |
| INGESTION_SCRIPT | 10 |
| analysis_data | 7 |
| spec_document | 7 |
| document | 5 |
| ATTRIBUTION_SCRIPT | 2 |
| json | 2 |
| typescript | 2 |
| typescript_module | 3 |
| script | 3 |
| analysis_document | 1 |
| eval | 1 |
| INGESTION_UTILS | 1 |
| test | 1 |
| test_suite | 1 |
| **Total** | **189** |

The 143 entries with no `type` field are primarily governance documents, canonical artifacts, and retrieval tool entries from the M5-A population sweep.

---

## 6. Conclusion

The manifest is **clean** after this session:

- Zero duplicate `canonical_id` values (gate GATE_UDA_0_S1_DUPES: PASS).
- All 189 entries have a `canonical_id` field (22 entries promoted from `id` field).
- Zero stale paths.
- 18 entries with partial missing fields documented above for downstream remediation.
- 31 tool entries exist with no `channel` assignment — ready for UDA-0-S2 (portal) and UDA-0-S3 (MCP) population.

The manifest is ready for UDA-0-S2 population.

---

*End of UDA_0_S1_MANIFEST_AUDIT.md*

---
canonical_id: SAMAPTI_MCP_TOOL_GAP_CHARACTERIZATION
version: 1.0
status: CURRENT
created: 2026-07-30
author: SAMĀPTI lane A2-CI-POINTERS (builder), commissioned by DVA Ruling 17
measured_against: amjis-mcp revision amjis-mcp-00517-b5q (100% traffic), commit b5fe163f
---

# MCP tool-surface gap — characterization

**Commissioned by DVA Ruling 17** after lane A2's reopen cycle 1 surfaced that the pointer
harness's "registered" set over-reported the served surface by 43 names.

## 1 — The headline answer

**There is no regression. The three numbers in circulation count three different things and
were never comparable.**

| Number | What it actually counts | Value |
|---|---|---|
| `tools/list` on the deployed server | the MCP tools a caller can actually invoke | **124** |
| `server.tool()` call sites in source | registration call sites, ignoring runtime gates | **167** |
| `mcp_server_info.tool_count` | `MCP_SURFACE_PROFILES.full.total` from a generated manifest | **152** |

`167 − 43 (RC-14 gate) = 124`, exactly and set-for-set, verified against the live catalog.

## 2 — Live measurement (performed, not reported)

- **Endpoint:** `https://amjis-mcp-938361928218.asia-south1.run.app/mcp`, `tools/list`,
  first-party Bearer key.
- **Measured:** 2026-07-30, **124 tools**.
- **Serving revision:** `amjis-mcp-00517-b5q`, 100% of traffic, created
  `2026-07-29T19:35:38Z`, `commit-sha b5fe163f2370a06450e6ccccc00e3a403b94a428`.
- **Auth caveat that makes this the RIGHT number:** a first-party Bearer key resolves to the
  `full` profile, and `applyProfileGate()` is an explicit **no-op** for `full`
  (`getAllowedToolNames('full')` returns `null`). So 124 is the *unfiltered* surface, not a
  profile-narrowed view. An OAuth token would have returned a smaller, gated catalog and would
  have made this measurement meaningless — this is the confound that had to be excluded first,
  and it is excluded by construction, not by assumption.

## 3 — Was anything served on 2026-07-29 that is not served now?

**No.** Every Cloud Run revision alive during the 2026-07-29 18:40–19:44Z window carries the
RC-14 gate and models to exactly 124 served tools:

| Revision | Created (UTC) | Commit | Call sites | Gated | Modelled served |
|---|---|---|---|---|---|
| `amjis-mcp-00517-b5q` (serving) | 2026-07-29T19:35:38Z | `b5fe163f` | 167 | 43 | **124** |
| `amjis-mcp-00516-46s` | 2026-07-29T18:37:11Z | `f573be8d` | 167 | 43 | **124** |
| `amjis-mcp-00515-z4s` | 2026-07-29T18:26:47Z | `42151b24` | 167 | 43 | **124** |
| `amjis-mcp-00514-2gz` | 2026-07-29T17:50:42Z | `e43f41f9` | 167 | 43 | **124** |
| `amjis-mcp-00513-8d6` | 2026-07-29T16:50:18Z | `139c89c6` | 167 | 43 | **124** |
| `origin/main` tip | — | `cdb6fc3b` | 167 | 43 | **124** |

The RC-14 gate landed `96a4b637` (2026-07-23 12:20 IST), merged via #726 — **six days before**
the window. No tool lost service during or after it. **No escalation is warranted.**

## 4 — Where "152" comes from

`mcp_server_info` reports `tool_count: 152` **right now**, on the same server, same key, same
moment that `tools/list` returns 124. It is therefore not a stale reading and not a regression
signal — it is a different measurement:

```
register_server_info.ts:55   tool_count: MCP_CATALOG_TOOL_COUNT
mcp_catalog_version.ts:39    MCP_CATALOG_TOOL_COUNT = MCP_SURFACE_PROFILES.full.total   // = 152
```

`mcp_surface_profiles.generated.ts` is generated **from the platform retrieval registry**
(`getCatalog()`), `generated_at: 2026-07-24T05:06:15.709Z` — it enumerates *retrieval capability*
faces, not MCP `server.tool()` registrations. The two sets overlap by only **15 of 124** names:
the manifest lists entries like `assess_career` / `assess_wealth` that are not MCP tools at all,
while **109 genuinely-served MCP tools are absent from it**.

So the SHODHANA liveness note ("`tool_count: 152` nominal") and the ṢAḌ-DARŚANA state note
("152 tools total") were both reading this manifest figure. Neither was ever a `tools/list`
count, and neither contradicts today's 124.

**Residual finding (NOT fixed here — out of lane, reported not silently dropped):**
`mcp_server_info.tool_count` advertises a number that does not describe the served catalog and
overlaps it by 12%. Any consumer treating it as "how many tools can I call" is misled, and a
liveness check asserting `tool_count: 152 nominal` is an earned-signal (§N.8) violation: it
passes on a number that would not change if the MCP surface collapsed to zero. Needs its own lane.

## 5 — Per-tool classification of all 43 registered-but-unserved names

Every one is an RC-14-retired legacy alias with a **live** canonical replacement. Zero are
genuinely broken; zero lack a mapping. Source of the mapping: `canonical_faces.json`
→ `deprecated_aliases` (authoritative), cross-checked against the live catalog.

| Gated legacy name | Classification | Canonical replacement | Replacement served? |
|---|---|---|---|
| `asset_registry_all` | RC-14 legacy alias, gated | `catalog_assets_all` | LIVE |
| `asset_registry_l0` | RC-14 legacy alias, gated | `catalog_assets_l0` | LIVE |
| `bodha_remedies_search` | RC-14 legacy alias, gated | `bodha_remedies_get` | LIVE |
| `compute_natal_positions` | RC-14 legacy alias, gated | `ganita_natal_positions_compute` | LIVE |
| `ephemeris_cache_year` | RC-14 legacy alias, gated | `ref_ephemeris_year_get` | LIVE |
| `event_anchors` | RC-14 legacy alias, gated | `phala_anchors_get` | LIVE |
| `get_cgm_subgraph` | RC-14 legacy alias, gated | `bodha_graph_subgraph_get` | LIVE |
| `get_chart_orientation` | RC-14 legacy alias, gated | `bodha_chart_digest_get` | LIVE |
| `get_chart_quality` | RC-14 legacy alias, gated | `bodha_quality_get` | LIVE |
| `get_classical_citation` | RC-14 legacy alias, gated | `ref_classical_citation_get` | LIVE |
| `get_dashas` | RC-14 legacy alias, gated | `ganita_dashas_get` | LIVE |
| `get_domain_reading` | RC-14 legacy alias, gated | `bodha_domain_reading_get` | LIVE |
| `get_positions` | RC-14 legacy alias, gated | `ganita_positions_get` | LIVE |
| `get_projections` | RC-14 legacy alias, gated | `kala_projections_get` | LIVE |
| `get_remedies` | RC-14 legacy alias, gated | `bodha_remedies_get` | LIVE |
| `get_signals` | RC-14 legacy alias, gated | `bodha_signals_get` | LIVE |
| `get_temporal_windows` | RC-14 legacy alias, gated | `kala_windows_get` | LIVE |
| `lel_query` | RC-14 legacy alias, gated | `mimamsa_lel_query` | LIVE |
| `list_assets` | RC-14 legacy alias, gated | `catalog_assets_list` | LIVE |
| `list_remedies_by_category` | RC-14 legacy alias, gated | `ref_remedies_by_category_list` | LIVE |
| `mitigation_map` | RC-14 legacy alias, gated | `phala_mitigation_get` | LIVE |
| `muhurta_finder` | RC-14 legacy alias, gated | `kala_muhurta_get` | LIVE |
| `phala_outlook` | RC-14 legacy alias, gated | `phala_outlook_get` | LIVE |
| `query_aspects_at_time` | RC-14 legacy alias, gated | `ref_aspects_at_time_get` | LIVE |
| `query_calibration` | RC-14 legacy alias, gated | `mimamsa_calibration_get` | LIVE |
| `query_chart_facts` | RC-14 legacy alias, gated | `ganita_chart_facts_get` | LIVE |
| `query_dasha_periods` | RC-14 legacy alias, gated | `ganita_dasha_periods_get` | LIVE |
| `query_mantras` | RC-14 legacy alias, gated | `ref_mantras_get` | LIVE |
| `query_planet_position` | RC-14 legacy alias, gated | `ref_planet_position_get` | LIVE |
| `query_planet_transit` | RC-14 legacy alias, gated | `ref_planet_transit_get` | LIVE |
| `query_remedies` | RC-14 legacy alias, gated | `ref_remedies_get` | LIVE |
| `query_remedies_by_planet` | RC-14 legacy alias, gated | `ref_remedies_by_planet_get` | LIVE |
| `query_remedies_for_chart` | RC-14 legacy alias, gated | `ref_remedies_chart_get` | LIVE |
| `query_retrograde_periods` | RC-14 legacy alias, gated | `ref_retrograde_periods_get` | LIVE |
| `query_special_lagnas` | RC-14 legacy alias, gated | `ganita_special_lagnas_get` | LIVE |
| `query_tantric_remedies` | RC-14 legacy alias, gated | `ref_tantric_remedies_get` | LIVE |
| `read_remedy` | RC-14 legacy alias, gated | `ref_remedy_get` | LIVE |
| `record_outcome` | RC-14 legacy alias, gated | `mimamsa_outcome_record` | LIVE |
| `ref_remedies_search` | RC-14 legacy alias, gated | `ref_remedies_get` | LIVE |
| `traverse_graph` | RC-14 legacy alias, gated | `bodha_graph_traverse_get` | LIVE |
| `util_intent_classify` | RC-14 legacy alias, gated | `intent_classify` | LIVE |
| `vector_search` | RC-14 legacy alias, gated | `ref_vector_search` | LIVE |
| `yoga_activation_by_dasha` | RC-14 legacy alias, gated | `kala_yoga_activation_get` | LIVE |
**Note on `record_outcome` → `mimamsa_outcome_record`:** the replacement name IS served, but its
handler was deliberately retired under CR-128 (raises before any DB access). Served ≠ functional;
that is by design and is not a gap.

## 6 — What this cost, and the fix

The 43-name over-report was not cosmetic. It is what let `sc_pointer_validation.ts` **PASS 32
production drill-pointer / recover sites that dead-end on the live server** — the exact SC-18
harm ("the recovery path fires exactly when data was withheld and points at tool-not-found"),
reintroduced wholesale by RC-14 and invisible to the check built to catch it, for one week.

Fixed in lane A2: `collectRegisteredTools()` now subtracts the gate (offline, live-accurate,
no network dependency in CI), and `runLiveCatalogParity()` measures the model against a real
`tools/list` when an endpoint is configured — so model drift is detectable rather than assumed
away. All 43 pointer sites were repointed at live-served canonical faces and verified by real
`tools/call`.

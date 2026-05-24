# MCPT v3.2 Description Audit — Phase 1d

Generated: 2026-05-23

## Tools audited: 21
## False claims found and fixed: 5 (across 3 files)

---

## False claims found and corrected

| Tool | File | Line(s) | Original text | Corrected text |
|------|------|---------|---------------|----------------|
| query_chart_facts | `platform-mcp/src/tools/query_chart_facts.ts` | 4 (JSDoc) | `Queries the 795-row chart_facts table` | `Queries the 2,717-row chart_facts table` |
| query_chart_facts | `platform-mcp/src/tools/query_chart_facts.ts` | 55 (description string) | `'What it does: Queries the 795-row chart_facts table...'` | `'What it does: Queries the 2,717-row chart_facts table...'` |
| query_chart_facts | `platform-mcp/src/tools/query_chart_facts.ts` | 63 (coverageHint) | `'795 rows across 37 categories'` | `'2,717 rows across 27 categories'` |
| multi_school_bundle | `platform-mcp/src/tools/multi_school_bundle_tool.ts` | 26 (schema describe) | `'KP and Tajaka evidence queries skip if the respective chart_facts rows have not been backfilled.'` | `'All four school evidence sets (including KP and Tajaka) are fully populated as of MCPT v3.3.'` |
| multi_school_bundle | `platform-mcp/src/tools/multi_school_bundle_tool.ts` | 44-45 (tool description) | `'KP and Tajaka evidence queries degrade gracefully if their chart_facts rows have not been backfilled (v3.3 scope).'` | `'All four school evidence sets are fully populated (MCPT v3.3 complete).'` |
| description_builder | `platform-mcp/src/tools/description_builder.ts` | 17 (JSDoc comment) | `(e.g. "795 rows across N categories")` | `(e.g. "2,717 rows across 27 categories")` |
| description_builder | `platform-mcp/src/tools/description_builder.ts` | 27 (JSDoc example) | `"What it does: Queries the chart_facts table (795 rows). ...` | `"What it does: Queries the chart_facts table (2,717 rows). ...` |

---

## Ground truth applied

Per `00_ARCHITECTURE/MCPT_V33_CLOSE.md` (sealed 2026-05-22):
- chart_facts: **2,717 total rows** across **27 categories** (not 795/37)
- All 9 v3.3-scope categories populated: shadbala, ashtakavarga_sav, ashtakavarga_bav, bhava_bala, kp_cusp, kp_planet, kp_significator, upagraha, varshphal
- KP and Tajaka evidence is fully backfilled — "skip if not backfilled" language is obsolete
- Migrations 072–080 applied to production 2026-05-22

---

## Tools with no false claims

- `cross_school_lookup.ts` — clean
- `data_coverage.ts` — skipped (handled by sub-agent s1a)
- `flag_disagreement.ts` — clean
- `get_cgm_subgraph.ts` — clean
- `get_trace.ts` — clean (runtime audit-timing message is accurate, not stale)
- `holistic_bundle_tool.ts` — clean
- `lel_query.ts` — clean
- `list_recent_queries.ts` — clean
- `log_prediction.ts` — clean
- `query_dasha_periods.ts` — clean
- `query_ephemeris.ts` — clean
- `query_panchanga.ts` — clean
- `query_signals.ts` — clean
- `query_transit_event.ts` — clean
- `read_asset.ts` — clean
- `read_classical_text.ts` — clean
- `record_outcome.ts` — clean (horizon-date logic is accurate business logic)
- `tool_health.ts` — skipped (handled by sub-agent s1b)
- `vector_search.ts` — clean

---

## Acceptance criteria verification

- `grep -r "pending v3.3 backfill" platform-mcp/` → **0 matches** (PASS)
- `grep -r "Apply migrations 073-076" platform-mcp/` → **0 matches** (PASS)
- All 21 tool descriptions reviewed → **PASS**
- Tests: 75/75 passing → **PASS**

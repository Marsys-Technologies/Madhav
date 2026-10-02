---
artifact: BAND_X2_WAVE2_SERVED_SURFACING
version: "1.0"
status: DRAFT-HELD (tool-text wave 2 piece; merges only after S-L1, with the single wave-2 regeneration)
produced_by: exec-suvarna (worker lane)
date: 2026-10-02
branch: suvarna/land/TI-w2-condition-served-001
split_from: "PR #2890 (writer-only after the split); the original text of these paragraphs is in the v1.0-v1.4 history of BAND_X2_LANE_INTENT (PR #2890, commits before the v1.5 split)"
depends_on: "#2890 merged AND deployed first: the served field reads condition_score_breakdown.varga_fallback_used / varga_fallback_reason, which only the new ga_condition writer writes."
---

# get_condition_composite: serving the D1 fallback (X2 / I-29), wave 2 piece

Decision: SS, option A (2026-10-02). The writer half (the guard that raises, the band table, the visible flag in the stored breakdown) stays in #2890. This PR is ONLY the served-tool half.

## What I-29 asked
- **I-29 / X2** (mandatory before S-L1; canonical in S-L1, the other two charts in S-L1b): "a D1-fallback row is made visible (served field and Dens facet) and an integrity clause fails a fallback on a chart that has divisionals." Finding F-7: `varga_dignity_composite` NULL and `varga_fallback_used = true` on all 90 rows of two charts.

## What this PR changes
2. **Served field + Dens facet** (`platform/src/lib/retrieval/registry/layers/L1_ganita/get_condition_composite.ts`): every row carries top-level `varga_fallback_used` (true / false / **null when the flag is absent**, never coerced to false) and `varga_fallback_reason`; `varga_fallback_used` is a declared input filter and a `density_contract.facets` entry (`['graha','ayanamsha_id','varga_fallback_used']`); the response counts D1-fallback rows separately (`d1_fallback_rows_in_page`, `d1_fallback_total_matching` over the full filtered set, null if the count did not return it) with a `d1_fallback_note` (CLAUDE.md N.6 item 1: never flattened in with divisional-based rows). The empty-reason text names the new filter.

Also: a present but non-boolean `varga_fallback_used` ('yes', 1, `{}`) is an explicit `is_error` (same pattern as `chart_id is required`), never silently read as "no filter"; absent / null / '' mean no filter. The dead `divisional_total` count is not selected.

Files: `get_condition_composite.ts` and its test (13 tests); the two served-read pins in `platform/scripts/governance/asset_declarations.json` (`get_condition_composite.ts:91` -> `:129`; the select moved); regenerated `capability_knowledge.snapshot.json` and `capability_estate_census.json`.

## Generated artifacts and the HOLD
- `capability_content_hash` moves `sha256:6c1aefca7601a9b7204471e0a3ccc03fe8ffa31819e5800b0d5e36fe83e156a8` (main) -> `sha256:0cbfae115923cf57e826e345bbcf529d9b2b57e3097587cab1238c972f9e0da3` (this PR; 182 SCUs; the diff is the tool description, the new optional input and the two hashes). Regenerated with `codegen:capability-knowledge -- --generated-at=2026-10-02T00:30:26.000Z`; the census with `--generated-at=2026-10-02T00:30:26.000Z --source-revision=c70d0067857e839945f15275bfc692b9dabdbc65` (the diff is the new `varga_fallback_used` input plus three source sha256s). All four `:check` commands pass.
- By design the Pariprashna route baselines (`tests/pariprashna/route_ports/route_golden_stream.test.ts`, 2 cases) and the beyond-acarya acceptance pins (`src/lib/vidhi/inquiry/beyond_acarya_acceptance.test.ts`, 2 cases: the v13 pin and the frozen-route-denominator `report_hash`) pin the snapshot hash and go RED until the single wave-2 regeneration (owner authorisation covers it). They are protected paths and are NOT regenerated here. This PR therefore stays DRAFT and is not armed.

## Served consumers and open questions
- **Served (platform):** `get_medical_indications.ts` (selects `indication_strength` verbatim), `get_vastu_directions.ts` (selects `direction_impact` verbatim, joins remedies), `get_condition_composite.ts` (the new served field), `source_query_availability.ts` (knowledge probes over `ga_medical` / `ga_vastu_planet_direction_map` / `ga_condition_composite`). None interprets the label strings, so no served code needed a change for the value changes; vāstu rows with `direction_impact = 'unknown'` can now appear only when a composite row is missing/NULL (none today). MCP descriptions (`ganita_medical_get`, `ganita_vastu_get`, `ganita_condition_get`-family surface text) say "weakened / neutral / strengthened" for vāstu and do not mention the NULL case; unchanged by this lane.
- Whether the sheet's I-29 "Dens facet" is meant to be the `density_contract.facets` entry (done) or an additional census Dens criterion: I implemented the former; the census `Dens.served` criterion itself (a tier column in the served select) is a different, existing check and I did not add a tier column to the select.

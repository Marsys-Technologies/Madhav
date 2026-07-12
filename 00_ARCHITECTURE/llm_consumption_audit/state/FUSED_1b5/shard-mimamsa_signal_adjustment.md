# FUSED Lane 1b+5 shard — mimamsa_signal_adjustment (14 families)

Channel (path-level): served-only-by-down-pipeline. No surgical MCP tool (0 manifest mappings; 0 route.ts refs; absent from ALIVE + DEAD-19). This is the L5 calibration-overlay table (per-signal multipliers applied to readings); consumed internally by the L5/reading compute path (applies_to_reading, applied_bound), never exposed as a per-chart surgical retrieval.
DB truth: `SELECT count(*) FROM mimamsa_signal_adjustment WHERE chart_id=<A>`=66836 (Abhisek), `<B>`=66747 (Abhinandan). HEAVILY populated — ~66.8k overlay rows/chart. Columns: chart_id, origin_layer, origin_asset_id, origin_id, weight_id, multiplier, raw_multiplier, applied_bound, evidence_n, leakage_status, applies_to_reading, derived_from_pramana_ids, overlay_formula_version, created_at.
Wire probe: NONE possible — no surgical tool. Lane 5 four failure modes un-testable (no wire value to diff). Significance: this is the single largest decisive-data volume in my path set (133k+ rows total) with ZERO public retrieval path — a large body of calibration overlays that shape every reading is unreachable to a consuming LLM via the public MCP surface.
Derivation: path-grade(exemplar=multiplier[VF-2488]) + member-confirmation (all 14 families identical channel; same absent-surgical-tool condition, same populated data-plane state). heterogeneity_escalated=false.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| chart_id (VF-2483) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB heavily populated (66836/66747) | N/A — no wire path; diff un-exercisable | path-grade(exemplar=multiplier) + member-confirmation |
| origin_layer (VF-2484) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade + member-confirmation |
| origin_asset_id (VF-2485) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade + member-confirmation |
| origin_id (VF-2486) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade + member-confirmation |
| weight_id (VF-2487) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade + member-confirmation |
| multiplier (VF-2488) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade(exemplar) + member-confirmation |
| raw_multiplier (VF-2489) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade + member-confirmation |
| applied_bound (VF-2490) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade + member-confirmation |
| evidence_n (VF-2491) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade + member-confirmation |
| leakage_status (VF-2492) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade + member-confirmation |
| applies_to_reading (VF-2493) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade + member-confirmation |
| derived_from_pramana_ids (VF-2494) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade + member-confirmation |
| overlay_formula_version (VF-2495) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade + member-confirmation |
| created_at (VF-2496) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; DB populated | N/A — no wire path | path-grade + member-confirmation |

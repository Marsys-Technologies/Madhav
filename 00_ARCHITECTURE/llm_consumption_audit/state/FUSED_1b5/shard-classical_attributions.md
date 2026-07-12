# FUSED 1b+5 shard — classical_attributions (1 family)

| family_key | channel | retrievability_verdict (1b) | fidelity_verdict (5) | derivation |
|---|---|---|---|---|
| `__table_row_count__=720` | served-only-by-down-pipeline | NOT RETRIEVABLE NOW — surgical front `cross_school_lookup` routes to DEAD tool `multi_school_signal_lookup` (DEAD-19). Data (720 rows) + serving code exist; consult-repair quick-win class. | N/A (cannot reach wire) | path-grade(exemplar=`__table_row_count__=720`) + member-confirmation (single family) |

## Evidence
- DB truth: `SELECT count(*) FROM classical_attributions` = 720 (matches ledger). Topic→school attribution catalog (topic_id, school, source_text_ids[], rule_ids[], match_confidence).
- Wire probe: `POST /api/mcp/primitives/cross_school_lookup {"params":{"chart_id":"482012f1-...","topic":"tenth house"}}` →
  `ok:false … "Retrieval tool not found in registry: multi_school_signal_lookup", remediation:"Platform retrieval tool registry may be misconfigured (TOOL_NAME_TO_URI missing entry)"`.

## Findings
- **[lane 1b][class 1 UNREACHABLE][MEDIUM] classical_attributions served only by a DEAD tool.** 720-row topic→school attribution catalog is fronted by `cross_school_lookup`, which dispatches to the un-registered `multi_school_signal_lookup` (DEAD-19). Data + serving code present; single registry-wiring fix (TOOL_NAME_TO_URI entry) restores it — remediation quick-win. Repro: curl above.

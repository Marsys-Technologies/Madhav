# Shard 1a4-b3 — FUSED Lane 1a (synthesizability-as-received) + Lane 4 (receipt honesty)

Charter: LLM_CONSUMPTION_AUDIT_CHARTER v1.1 §7.2 (synthesizability), §7.1 (usable form), §4 (taxonomy).
Cross-refs (rider 1, cite-not-rederive): LCA-1 (DEAD-19 surgical tools incl. `cgm_graph_walk`), LCA-2 (full-pipeline/ask_madhav consult path broken).
Surgical wire probed once per tool (chart_id 482012f1-710e-4a25-994a-93821f5871aa). 100% probed, no skips.

## Channel census (11/11 tools)

| # | tool | whitelist? | channel | synthesizability | receipt_honesty |
|---|------|-----------|---------|------------------|-----------------|
| 1 | ganita_sade_sati_get | NO | served-only-by-down-pipeline | not-probed | n/a |
| 2 | ganita_special_lagnas_get | NO | served-only-by-down-pipeline | not-probed | n/a |
| 3 | ganita_strength_get | NO | served-only-by-down-pipeline | not-probed | n/a |
| 4 | ganita_structural_get | NO | served-only-by-down-pipeline | not-probed | n/a |
| 5 | ganita_tajaka_get | NO | served-only-by-down-pipeline | not-probed | n/a |
| 6 | ganita_transit_anchors_get | NO | served-only-by-down-pipeline | not-probed | n/a |
| 7 | ganita_yogas_get | NO | served-only-by-down-pipeline | not-probed | n/a |
| 8 | get_cgm_subgraph | YES | dead (fronts DEAD-19 `cgm_graph_walk`) | FAIL | n/a |
| 9 | get_chart_orientation | NO | served-only-by-down-pipeline | not-probed | n/a |
| 10 | get_chart_quality | NO | served-only-by-down-pipeline | not-probed | n/a |
| 11 | get_classical_citation | NO | served-only-by-down-pipeline | not-probed | n/a |

## Verbatim evidence (E-6)

10 tools (all except get_cgm_subgraph) returned identical shape:
`{"ok":false,"trace_id":"","error":{"class":"validation","message":"Tool not in surgical whitelist: <name>","remediation":"Use ask_madhav for full-pipeline queries. Surgical primitives are: query_chart_facts, query_signals, ... get_cgm_subgraph, ... msr_sql, ... query_calibration"}}`
The verbatim whitelist (48 primitives) does NOT contain any `ganita_*` tool, nor get_chart_orientation / get_chart_quality / get_classical_citation. It DOES contain `get_cgm_subgraph`. These 10 tools are therefore reachable only via the full pipeline (`ask_madhav`), whose consult path is broken per LCA-2 → effectively surgically UNREACHABLE.

get_cgm_subgraph (PASSES whitelist, fails at dispatch):
`{"ok":false,"trace_id":"","error":{"class":"internal","message":"Retrieval tool not found in registry: cgm_graph_walk","remediation":"Platform retrieval tool registry may be misconfigured (TOOL_NAME_TO_URI missing entry)"}}`
`cgm_graph_walk` is a confirmed member of LCA-1's DEAD-19 set. The MCP-facing `get_cgm_subgraph` is whitelisted (advertised as an available surgical primitive) but dispatches to a dead retrieval primitive → first-contact FAIL, no payload ever produced.

## Findings

- **F-1a-b3-1 (lane 1a, class 1 UNREACHABLE, HIGH):** get_cgm_subgraph passes the surgical whitelist but every call fails at dispatch with `Retrieval tool not found in registry: cgm_graph_walk` (LCA-1 DEAD-19). Synthesizability-as-received = FAIL (error, no payload). The one CGM-graph surgical entry point I own is dead.
- **F-4-b3-1 (lane 4, class 5 DISHONEST SELF-DESCRIPTION, MEDIUM):** The surgical whitelist advertises `get_cgm_subgraph` as an available primitive (it passes validation), yet it cannot execute — the registry lacks its retrieval URI. The whitelist over-advertises coverage: a consumer trusting the whitelist believes CGM subgraph retrieval is available surgically when it is not. Receipt-level dishonesty at the capability-advertisement layer.
- **F-1a-b3-2 (lane 1a, class 1 UNREACHABLE, HIGH):** 10 of my 11 tools (all `ganita_*` + get_chart_orientation/quality + get_classical_citation) are absent from the surgical whitelist; the only advertised path is `ask_madhav` (full pipeline), whose consult path is broken (LCA-2). These L1 Ganita surfaces (sade sati, special lagnas, six-fold strength, structural, tajaka/varshphal, transit anchors, yogas) plus chart orientation/quality and classical citation are surgically unreachable; synthesizability not-probed because no payload is obtainable on either path.

## Notes
- Rate-limit (60 RPM) forced a paced re-probe (8s spacing) — not a tool defect, an env constraint.
- No live payload with honesty markers/counters was obtainable for any of the 11 tools, so payload-level receipt_honesty grading (the LCA-7 msr_sql `truncated=False` pattern) has no subject here — receipt_honesty = n/a across the shard; the single lane-4 finding is at the whitelist-advertisement layer.

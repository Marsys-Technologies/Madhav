# Shard: reference_topic_tags (FUSED Lane 1b + Lane 5)

channel: truly-UNREACHABLE
families_total: 1 | members_sampled: 1 (sole family) | per_family_rows_written: 1
heterogeneity_escalated: false

## Channel check (E-6)
- DB truth: `SELECT count(*) FROM reference_topic_tags` → 481 (matches ledger family_key `__table_row_count__=481`).
- Serving-tool search (no wire probe possible):
  - `grep CAPABILITY_MANIFEST.json` → no hit.
  - `grep platform/src/lib/retrieval` → only `parity_check.ts:37` (a build-time integrity check that topic_ids resolve in reference_topic_tags) — NOT a serving tool.
  - Consumers found: `bg_concordance.py`, `bg_text_index.py` load it as internal tagging vocabulary. No MCP retrieval path exposes the catalog to a consuming LLM.
- Verdict: global L0 catalog, no chart_id; NO tool serves it over the wire. Class 1 UNREACHABLE.

## Per-family rows
| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| `__table_row_count__=481` | truly-UNREACHABLE | UNREACHABLE (no MCP tool serves reference_topic_tags; internal vocab only; class 1) | N/A — no wire value (unreachable, cannot probe) | path-grade sole-family (exemplar=`__table_row_count__=481`); family_count=1, member==exemplar |

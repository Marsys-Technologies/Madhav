# FUSED Lane1b+Lane5 shard — bodha_signal_embeddings

- families_total: 10
- channel: served-only-by-down-pipeline
- serving_tool: vector_search ALIVE but searches classical-text corpus (citation_ref/verse_text_en), returns 0 signal_id/embedding_id — does NOT serve bodha_signal_embeddings
- retrievability_verdict: UNREACHABLE-via-surgical (data EXISTS: 66836/66747 rows; consumed internally by pipeline; no surgical tool exposes signal embeddings)
- fidelity_verdict: N/A (never arrives over wire)
- derivation: path-grade(exemplar=embedding_input_summary) + member-confirmation (channel is table-level: tool routing is per-table, so all families share it; heterogeneity_escalated=false)
- note: vector_search points at classical text embeddings, not signal embeddings; the signal vectors are an internal similarity store.

| row_id | family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|---|
| VF-2048 | embedding_id | served-only-by-down-pipeline | UNREACHABLE-via-surgical (data EXISTS: 66836/66747 rows; consumed internally by pipeline; no surgical tool exposes signal embeddings) | N/A (never arrives over wire) | path-grade(exemplar=embedding_input_summary) + member-confirm |
| VF-2049 | signal_id | served-only-by-down-pipeline | UNREACHABLE-via-surgical (data EXISTS: 66836/66747 rows; consumed internally by pipeline; no surgical tool exposes signal embeddings) | N/A (never arrives over wire) | path-grade(exemplar=embedding_input_summary) + member-confirm |
| VF-2050 | chart_id | served-only-by-down-pipeline | UNREACHABLE-via-surgical (data EXISTS: 66836/66747 rows; consumed internally by pipeline; no surgical tool exposes signal embeddings) | N/A (never arrives over wire) | path-grade(exemplar=embedding_input_summary) + member-confirm |
| VF-2051 | ayanamsha_id | served-only-by-down-pipeline | UNREACHABLE-via-surgical (data EXISTS: 66836/66747 rows; consumed internally by pipeline; no surgical tool exposes signal embeddings) | N/A (never arrives over wire) | path-grade(exemplar=embedding_input_summary) + member-confirm |
| VF-2052 | build_id | served-only-by-down-pipeline | UNREACHABLE-via-surgical (data EXISTS: 66836/66747 rows; consumed internally by pipeline; no surgical tool exposes signal embeddings) | N/A (never arrives over wire) | path-grade(exemplar=embedding_input_summary) + member-confirm |
| VF-2053 | embedding_vec | served-only-by-down-pipeline | UNREACHABLE-via-surgical (data EXISTS: 66836/66747 rows; consumed internally by pipeline; no surgical tool exposes signal embeddings) | N/A (never arrives over wire) | path-grade(exemplar=embedding_input_summary) + member-confirm |
| VF-2054 | embedding_model | served-only-by-down-pipeline | UNREACHABLE-via-surgical (data EXISTS: 66836/66747 rows; consumed internally by pipeline; no surgical tool exposes signal embeddings) | N/A (never arrives over wire) | path-grade(exemplar=embedding_input_summary) + member-confirm |
| VF-2055 | embedding_model_version | served-only-by-down-pipeline | UNREACHABLE-via-surgical (data EXISTS: 66836/66747 rows; consumed internally by pipeline; no surgical tool exposes signal embeddings) | N/A (never arrives over wire) | path-grade(exemplar=embedding_input_summary) + member-confirm |
| VF-2056 | embedding_input_summary | served-only-by-down-pipeline | UNREACHABLE-via-surgical (data EXISTS: 66836/66747 rows; consumed internally by pipeline; no surgical tool exposes signal embeddings) | N/A (never arrives over wire) | path-grade(exemplar=embedding_input_summary) + member-confirm |
| VF-2057 | computed_at | served-only-by-down-pipeline | UNREACHABLE-via-surgical (data EXISTS: 66836/66747 rows; consumed internally by pipeline; no surgical tool exposes signal embeddings) | N/A (never arrives over wire) | path-grade(exemplar=embedding_input_summary) + member-confirm |

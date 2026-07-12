# FUSED Lane 1b + Lane 5 shard — mimamsa_insight_embeddings

channel: truly-UNREACHABLE
families_total: 5
exemplar_family: embedding
heterogeneity_escalated: false (all families are columns/value-partitions of ONE table sharing ONE retrieval path; path-grade valid)
members_sampled: 5

retrievability_verdict (Lane 1b): UNREACHABLE + DATA-PLANE-EMPTY: 0 rows for ALL charts; no confirmed serving tool (vector_search fronts bodha_signal_embeddings, not this table). Semantic-search index over insights never populated.

fidelity_verdict (Lane 5): NOT-TESTABLE (0 rows + no tool). SELECT count(*)=0 globally.

| family_key | channel | retrievability | fidelity | derivation |
|---|---|---|---|---|
| chart_id (VF-2333) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=embedding) + member-confirmation |
| insight_id (VF-2334) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=embedding) + member-confirmation |
| embedding (VF-2335) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade EXEMPLAR(embedding) |
| embed_model_version (VF-2336) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=embedding) + member-confirmation |
| embedded_at (VF-2337) | truly-UNREACHABLE | UNREACHABLE | NOT-TESTABLE | path-grade(exemplar=embedding) + member-confirmation |

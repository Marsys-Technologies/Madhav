# FUSED Lane 1b+5 shard — mimamsa_snapshot_cosign

- channel: served-only-by-down-pipeline
- families: 8
- db_row_counts: 0/0 (EMPTY both charts)
- serving_path: none dedicated; mimamsa consumption compute/full-pipeline only
- heterogeneity_escalated: false (all families = columns/value-partitions of one table, served identically by the same down-pipeline; no member deviates)
- derivation: path-grade(exemplar=snapshot_id) + member-confirmation across all 8 families

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| id | served-only-by-down-pipeline | UNRETRIEVABLE (data-plane empty: 0 rows, 0 charts in mimamsa_snapshot_cosign) | not-probed (no rows exist to serve; no wire path) | path-grade(exemplar=snapshot_id) + member-confirmation [VF-2517] |
| snapshot_id | served-only-by-down-pipeline | UNRETRIEVABLE (data-plane empty: 0 rows, 0 charts in mimamsa_snapshot_cosign) | not-probed (no rows exist to serve; no wire path) | path-grade(exemplar=snapshot_id) + member-confirmation [VF-2518] |
| chart_id | served-only-by-down-pipeline | UNRETRIEVABLE (data-plane empty: 0 rows, 0 charts in mimamsa_snapshot_cosign) | not-probed (no rows exist to serve; no wire path) | path-grade(exemplar=snapshot_id) + member-confirmation [VF-2519] |
| action | served-only-by-down-pipeline | UNRETRIEVABLE (data-plane empty: 0 rows, 0 charts in mimamsa_snapshot_cosign) | not-probed (no rows exist to serve; no wire path) | path-grade(exemplar=snapshot_id) + member-confirmation [VF-2520] |
| cosigner_uid | served-only-by-down-pipeline | UNRETRIEVABLE (data-plane empty: 0 rows, 0 charts in mimamsa_snapshot_cosign) | not-probed (no rows exist to serve; no wire path) | path-grade(exemplar=snapshot_id) + member-confirmation [VF-2521] |
| cosigned_at | served-only-by-down-pipeline | UNRETRIEVABLE (data-plane empty: 0 rows, 0 charts in mimamsa_snapshot_cosign) | not-probed (no rows exist to serve; no wire path) | path-grade(exemplar=snapshot_id) + member-confirmation [VF-2522] |
| judgment_ledger_ref | served-only-by-down-pipeline | UNRETRIEVABLE (data-plane empty: 0 rows, 0 charts in mimamsa_snapshot_cosign) | not-probed (no rows exist to serve; no wire path) | path-grade(exemplar=snapshot_id) + member-confirmation [VF-2523] |
| notes | served-only-by-down-pipeline | UNRETRIEVABLE (data-plane empty: 0 rows, 0 charts in mimamsa_snapshot_cosign) | not-probed (no rows exist to serve; no wire path) | path-grade(exemplar=snapshot_id) + member-confirmation [VF-2524] |

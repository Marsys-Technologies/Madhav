# shard-mimamsa_calibration_snapshot (FUSED 1b+5)

Path channel: **served-only-by-down-pipeline** (no surgical tool serves `mimamsa_*`; L5 compute / full-pipeline only, consult-gated per LCA-2). No wire probe possible.

DB-truth (E-6 call): `SELECT count(*) FROM mimamsa_calibration_snapshot` → **n=0** (Abhisek=0, Abhinandan=0). Table EMPTY for both charts — two-key-signed calibration snapshots publish only once calibration cells exist; empty is BY DESIGN under the L5 STRUCTURAL seal (CLAUDE.md §E). 10 schema-derived families, zero data instances.

retrievability_verdict: **FAIL(no-data + no-surgical-tool)**.
fidelity_verdict: **N/A** — no wire (unreachable → no diff).
derivation (all rows): served-only-by-down-pipeline; DB-truth count via SELECT; no wire. Path-grade(exemplar=snapshot_id) + member-confirmation (all 10 families share empty-table + no-tool status). heterogeneity_escalated=false.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| snapshot_id | served-only-by-down-pipeline | FAIL(no-data+no-surgical-tool) | N/A | path-grade(exemplar=snapshot_id) + member-confirmation |
| snapshot_at | served-only-by-down-pipeline | FAIL(no-data+no-surgical-tool) | N/A | path-grade(exemplar=snapshot_id) + member-confirmation |
| chart_id | served-only-by-down-pipeline | FAIL(no-data+no-surgical-tool) | N/A | path-grade(exemplar=snapshot_id) + member-confirmation |
| proposing_executor | served-only-by-down-pipeline | FAIL(no-data+no-surgical-tool) | N/A | path-grade(exemplar=snapshot_id) + member-confirmation |
| acharya_pratinidhi_key | served-only-by-down-pipeline | FAIL(no-data+no-surgical-tool) | N/A | path-grade(exemplar=snapshot_id) + member-confirmation |
| two_key_complete | served-only-by-down-pipeline | FAIL(no-data+no-surgical-tool) | N/A | path-grade(exemplar=snapshot_id) + member-confirmation |
| cells_jsonb | served-only-by-down-pipeline | FAIL(no-data+no-surgical-tool) | N/A | path-grade(exemplar=snapshot_id) + member-confirmation |
| delta_from_prior_jsonb | served-only-by-down-pipeline | FAIL(no-data+no-surgical-tool) | N/A | path-grade(exemplar=snapshot_id) + member-confirmation |
| publication_status | served-only-by-down-pipeline | FAIL(no-data+no-surgical-tool) | N/A | path-grade(exemplar=snapshot_id) + member-confirmation |
| formula_version | served-only-by-down-pipeline | FAIL(no-data+no-surgical-tool) | N/A | path-grade(exemplar=snapshot_id) + member-confirmation |

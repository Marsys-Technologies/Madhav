# shard-mimamsa_discoveries (FUSED 1b+5)

Path channel: **served-only-by-down-pipeline** (no surgical tool serves `mimamsa_*`; L5 `mi_pariksha` compute / full-pipeline only, consult-gated per LCA-2). No wire probe possible → no fidelity diff.

DB-truth (E-6 call): `SELECT count(*) FROM mimamsa_discoveries` → **n=45** (Abhisek=45, Abhinandan=0). POPULATED for Abhisek ONLY. Sample row: `discovery_id='retro_0d03e02a-...', discovery_class='retrodiction', strength=0, n_support=0, confidence_band=null, activation_status='candidate', citation_required=false, discovery_formula_ver='mi_pariksha_v2.0', statement='Blind retrodiction for 0d03e02a-...'`. Note: all sampled discoveries are `candidate` / strength=0 / n_support=0 (unvalidated retrodictions — consistent with STRUCTURAL seal; no accrued support yet). Two anchor-value families present: `activation_status=candidate` and `discovery_class=retrodiction` — both CONFIRMED as the dominant/only observed values in DB.

retrievability_verdict: **FAIL(no-surgical-tool)** — data exists (45 rows, Abhisek) but no surgical channel; served only by full pipeline, consult-gated (LCA-2). Remediation quick-win class.
fidelity_verdict: **N/A** — no wire → no diff.
derivation (all rows): served-only-by-down-pipeline; DB-truth count + sample-row via SELECT; no wire. Path-grade(exemplar=discovery_id) + member-confirmation (all 14 families same populated-Abhisek + no-tool status; two value-anchor families confirmed against DB). heterogeneity_escalated=false.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| chart_id | served-only-by-down-pipeline | FAIL(no-surgical-tool; data exists n=45 Abhisek) | N/A | path-grade(exemplar=discovery_id) + member-confirmation |
| discovery_id | served-only-by-down-pipeline | FAIL(no-surgical-tool; data exists n=45 Abhisek) | N/A | path-grade(exemplar=discovery_id) + member-confirmation |
| discovery_class | served-only-by-down-pipeline | FAIL(no-surgical-tool; data exists n=45 Abhisek) | N/A | path-grade(exemplar=discovery_id) + member-confirmation |
| statement | served-only-by-down-pipeline | FAIL(no-surgical-tool; data exists n=45 Abhisek) | N/A | path-grade(exemplar=discovery_id) + member-confirmation |
| evidence_refs | served-only-by-down-pipeline | FAIL(no-surgical-tool; data exists n=45 Abhisek) | N/A | path-grade(exemplar=discovery_id) + member-confirmation |
| strength | served-only-by-down-pipeline | FAIL(no-surgical-tool; data exists n=45 Abhisek) | N/A | path-grade(exemplar=discovery_id) + member-confirmation |
| n_support | served-only-by-down-pipeline | FAIL(no-surgical-tool; data exists n=45 Abhisek) | N/A | path-grade(exemplar=discovery_id) + member-confirmation |
| confidence_band | served-only-by-down-pipeline | FAIL(no-surgical-tool; data exists n=45 Abhisek) | N/A | path-grade(exemplar=discovery_id) + member-confirmation |
| activation_status | served-only-by-down-pipeline | FAIL(no-surgical-tool; data exists n=45 Abhisek) | N/A | path-grade(exemplar=discovery_id) + member-confirmation |
| citation_required | served-only-by-down-pipeline | FAIL(no-surgical-tool; data exists n=45 Abhisek) | N/A | path-grade(exemplar=discovery_id) + member-confirmation |
| citation_ref | served-only-by-down-pipeline | FAIL(no-surgical-tool; data exists n=45 Abhisek) | N/A | path-grade(exemplar=discovery_id) + member-confirmation |
| discovery_formula_ver | served-only-by-down-pipeline | FAIL(no-surgical-tool; data exists n=45 Abhisek) | N/A | path-grade(exemplar=discovery_id) + member-confirmation |
| activation_status=candidate | served-only-by-down-pipeline | FAIL(no-surgical-tool; value confirmed in DB) | N/A | path-grade(exemplar=discovery_id) + member-confirmation |
| discovery_class=retrodiction | served-only-by-down-pipeline | FAIL(no-surgical-tool; value confirmed in DB) | N/A | path-grade(exemplar=discovery_id) + member-confirmation |

"""
services/ka_kshetra — Lane D of the ṢAḌ-DARŚANA W2 "field as science" build
(KALA_W2_FIELD_DESIGN_v1_0.md §0, §6).

Lane D owns Stage 6 (salience vector + submodular selection + rarity axis,
registry items 25/15) and Stage 6.5 (insight synthesis, E2):

    from services.ka_kshetra.cohort_client import cohort_base_rate, CohortRate
    from services.ka_kshetra.stage6_salience import compute_salience_vector
    from services.ka_kshetra.submodular import select_submodular
    from services.ka_kshetra.stage65_insights import synthesize_insights

Lane boundary discipline (§0): this package reads OTHER lanes' tables (or
their one published function) — it never reads another lane's code. The
`ka_kshetra` heavy-writer orchestration shim (`pipeline/orchestrator/writers/
ka_kshetra.py`) and the cross-lane `contracts.py` dataclasses are owned by
Lane C / a cross-lane PR, not this package; they do not exist in this build
yet (no other W2 lane has landed). Every module here therefore accepts
explicit, locally-typed inputs whose SHAPE mirrors the frozen SQL schemas in
KALA_W2_FIELD_DESIGN_v1_0.md §5.2-§5.4 exactly (documented at each dataclass)
rather than importing a not-yet-existent shared contracts module — when
`contracts.py` lands, Lane C/E's wiring passes real `kala_field_windows` /
`kala_field_provenance` rows into these same call signatures.
"""

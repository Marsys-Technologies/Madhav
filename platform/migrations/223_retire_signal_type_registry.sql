-- Migration 223: Retire signal_type_registry (G52)
--
-- The predicate-firing model was dropped per L1_L2_RELATIONSHIP_ARCHITECTURE_DECISION_v1_0.
-- ga_structural enumerates exhaustively and labels from brahma_yoga_catalog,
-- referencing signal_type_registry zero times. Asset bg_signal_type_registry is DORMANT.
--
-- Table may not exist in all environments (was never populated in prod after L2 model change).
-- DROP IF EXISTS is intentionally safe.

DROP TABLE IF EXISTS signal_type_registry;

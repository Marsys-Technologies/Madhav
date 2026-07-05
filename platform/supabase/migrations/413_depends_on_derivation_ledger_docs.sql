-- Migration 413: BA Phase 2.5 fast-follow #9 — consolidated depends_on
-- derivation-ledger documentation edges.
--
-- 6 assets read L0-bedrock tables (brahma_event_ontology / brahma_class_priors /
-- brahma_formula_constants) without declaring the corresponding bg_* asset in
-- depends_on. dag_edge_guard.py exempts all bg_* reads by design (L0 bedrock is
-- always-present, never a real scheduling risk), so these are NOT scheduling
-- bugs — but they violate the derivation-ledger spirit of CLAUDE.md §I B.3
-- (every L2+ claim should cite the specific L1/L0 fact source it consumes).
-- Doc-only, registry-only correction; no writer behavior changes.
--
--   mi_jivanaghatana -> bg_ghatana        (event_class_id resolution)
--   mi_kula          -> bg_class_priors   (family prior-weight seeding)
--   mi_pramana       -> bg_ghatana, bg_formula_constants (base_rate, scoring weights)
--   mi_gunanaka      -> bg_formula_constants (shrinkage_k, divergence_cap)
--   mi_pariksha      -> bg_formula_constants (attribution dimension weights)
--
-- ph_muhurta -> bg_ghatana was in the original audit finding list but could
-- NOT be confirmed against the current ph_muhurta.py source (no
-- brahma_event_ontology read found) — omitted rather than asserting an
-- unverified edge. bo_upaya -> bg_remedies is handled separately in
-- migration 412 (BA Phase 2.5 fast-follow #4, bo_upaya real resonance inputs).
--
-- Idempotent (UPDATE by asset_id; re-running sets the same array). Applied
-- surgically — never via deploy.yml. No rebuild triggered.

BEGIN;

DO $$
BEGIN
    UPDATE asset_registry SET depends_on = ARRAY['bg_ghatana']::text[]
    WHERE asset_id = 'mi_jivanaghatana';
    IF NOT FOUND THEN
        RAISE EXCEPTION 'migration 413: mi_jivanaghatana row not found in asset_registry';
    END IF;

    UPDATE asset_registry SET depends_on = ARRAY['bg_rules','bg_class_priors']::text[]
    WHERE asset_id = 'mi_kula';
    IF NOT FOUND THEN
        RAISE EXCEPTION 'migration 413: mi_kula row not found in asset_registry';
    END IF;

    UPDATE asset_registry
    SET depends_on = ARRAY['mi_bhavisya','mi_jivanaghatana','bg_ghatana','bg_formula_constants']::text[]
    WHERE asset_id = 'mi_pramana';
    IF NOT FOUND THEN
        RAISE EXCEPTION 'migration 413: mi_pramana row not found in asset_registry';
    END IF;

    -- mi_kula retained: migration 365 established this edge (mi_gunanaka.py:70
    -- reads mimamsa_signal_families, owned by mi_kula) — a real hard build-order
    -- dependency, not a doc-only edge. Must not be dropped here.
    UPDATE asset_registry SET depends_on = ARRAY['mi_pramana','mi_kula','bg_formula_constants']::text[]
    WHERE asset_id = 'mi_gunanaka';
    IF NOT FOUND THEN
        RAISE EXCEPTION 'migration 413: mi_gunanaka row not found in asset_registry';
    END IF;

    UPDATE asset_registry SET depends_on = ARRAY['mi_pramana','mi_kula','bg_formula_constants']::text[]
    WHERE asset_id = 'mi_pariksha';
    IF NOT FOUND THEN
        RAISE EXCEPTION 'migration 413: mi_pariksha row not found in asset_registry';
    END IF;
END $$;

COMMIT;

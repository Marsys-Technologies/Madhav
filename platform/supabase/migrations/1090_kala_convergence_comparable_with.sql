-- Migration 1090 — `comparable_with` relation vocabulary (synergy audit #2, #8 interim)
--
-- RENUMBERED 2026-09-24 (was 1087). The L0 repair branch claimed 1087 first
-- (verified first-commit times: theirs 08:54/11:21 IST, mine 11:25/11:42), and neither
-- side had applied. Under the rule the Gochara stream proposed and this stream accepts —
-- an applied migration keeps its number, otherwise first claim holds — they keep 1087.
-- Safe to renumber precisely because this file is UNAPPLIED; a migration is never
-- renumbered after it has been applied.
--
-- Adopts the layer's one comparability vocabulary, pinned at
-- gochara_wp0_7/WP1_CONTRACTS.md §6 and read AT SOURCE from
-- origin/l3/gochara-autonomous-wp0-7 (that branch was unpushed when the synergy
-- audit raised #2, which is why this session declined to implement against a
-- described enum and waited for the values).
--
-- CORRECTION TO THE LAYER BINDING, recorded because it changes what #2 asked for.
-- The binding proposed "one name, `comparable_with`, that enum" as a RENAME of
-- ka_sangam's `comparability_class`. They are different objects:
--   * `comparability_class` (ka_sangam/<signature_class>) is a GROUPING key — a
--     projection may rank only within one class (§4.5);
--   * `comparable_with` is a RELATION to a reference row — may this row be
--     compared against that one, and how (WP1 §6's table).
-- Renaming one into the other would have silently destroyed the grouping. Both
-- columns exist; neither replaces the other.
--
-- VALUE: every ka_sangam row is `different_convention` today, and this is NOT a
-- default — it is derived from the row's own convention frame. The layer ruled
-- MEAN node (M-1 / N-4a / Kṣetra ruling 7); ka_sangam's contacts still come from
-- a scanner hard-coded to TRUE_NODE (pipeline/transit_search.py:10,:64), which is
-- must_not_touch for every stream. Per WP1 §6, a differing convention_id means the
-- comparison is NOT_RUN and no tolerance may be quoted across it. The value flips
-- to a comparable relation automatically when the node convention unifies — the
-- writer derives it from convention_frame.node_convention, so nothing must
-- remember to update it.

ALTER TABLE kala_convergence
    ADD COLUMN IF NOT EXISTS comparable_with TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'kala_convergence_comparable_with_chk'
    ) THEN
        ALTER TABLE kala_convergence
            ADD CONSTRAINT kala_convergence_comparable_with_chk
            CHECK (comparable_with IS NULL OR comparable_with IN
                   ('self', 'same_convention_same_inputs',
                    'same_convention_newer_inputs', 'different_convention'));
    END IF;
END $$;

COMMENT ON COLUMN kala_convergence.comparable_with IS
    'Layer comparability RELATION (WP1_CONTRACTS.md §6, four-value closed enum). Distinct from '
    'comparability_class, which is a grouping key — neither replaces the other. Currently '
    'different_convention on every row: the layer ruled mean node, ka_sangam''s scanner is TRUE_NODE '
    '(transit_search.py, must_not_touch), so cross-convention comparison is NOT_RUN per §6. Derived '
    'from convention_frame.node_convention, not defaulted — it changes when the convention does.';

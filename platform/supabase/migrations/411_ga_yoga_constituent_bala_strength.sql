-- Migration 411: JL-012 (BA Phase 2.5 P3 J3) — ga_yoga.strength constituent_bala_v1
-- derivation + documented-NULL bhanga_active.
--
-- ga_yoga_firings.strength/is_partial/bhanga_active were NULL/false for all
-- solar/positional yogas (only pancha_mahapurusha ever populated strength, via
-- an ad hoc kendra/exaltation bonus formula with no classical citation). Per
-- JL-012: no yoga-specific strength formula exists in the classical corpus, so
-- strength is instead derived as the normalized shadbala (actual/required rupa,
-- graha_shadbala_total) of each yoga's constituent grahas, mean-combined — a
-- single formula applied uniformly across yoga types, not invented per-yoga
-- (B.10). bhanga_active is set NULL-with-a-documented-reason wherever this
-- writer implements no classical cancellation (bhanga) rule for that yoga type;
-- Kemadruma's own bhanga logic (baked into its firing gate) is untouched.

BEGIN;

ALTER TABLE ga_yoga_firings
    ADD COLUMN IF NOT EXISTS derivation TEXT,
    ADD COLUMN IF NOT EXISTS strength_label TEXT,
    ADD COLUMN IF NOT EXISTS citation_ref TEXT,
    ADD COLUMN IF NOT EXISTS citation_human TEXT,
    ADD COLUMN IF NOT EXISTS bhanga_na_reason TEXT;

COMMENT ON COLUMN ga_yoga_firings.derivation IS
  'JL-012: formula identity for a computed (non-classical-formula) strength value. '
  '''constituent_bala_v1'' = mean of normalized (actual/required rupa) shadbala '
  'across the yoga''s constituent_planets, sourced from graha_shadbala_total. '
  'NULL when no constituent has resolvable shadbala (strength also NULL — not fabricated).';

COMMENT ON COLUMN ga_yoga_firings.strength_label IS
  'JL-012: classification of the strength value''s provenance. ''computed_extension'' '
  'marks it explicitly as an extension beyond the classical corpus (B.10), never a '
  'classical citation. NULL when strength is NULL.';

COMMENT ON COLUMN ga_yoga_firings.citation_ref IS
  'JL-012: machine-readable citation for a computed strength value — a bala_gate '
  'reference into graha_shadbala_total (chart_facts), e.g. '
  '''ga_yoga.strength:<yoga_id>:constituent_bala_v1@chart=<id>:ay=<ayanamsha>:bala_gate=graha_shadbala_total''.';

COMMENT ON COLUMN ga_yoga_firings.citation_human IS
  'JL-012: human-readable citation/derivation note paired with citation_ref.';

COMMENT ON COLUMN ga_yoga_firings.bhanga_na_reason IS
  'JL-012: documented reason bhanga_active is NULL for this yoga row. Distinguishes '
  '''classical bhanga rule exists in brahma_yoga_catalog.cancellation_conditions but is '
  'not evaluated by ga_yoga_writer'' from ''no classical bhanga rule exists for this '
  'yoga type''. NULL for kemadruma_aristha, whose cancellation is already gated into '
  'its firing condition upstream (not duplicated here).';

COMMIT;

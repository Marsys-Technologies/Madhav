-- Migration 552: chart_fact_identity — THE FACT IDENTITY INDEX
-- ADHIṢṬHĀNA Campaign A, Lane A5 (2026-08-08)
--
-- `chart_facts` (migration 204) has NO structured varga/house columns —
-- identity is smuggled into free-text `fact_key`/`fact_subject` using at
-- least six house encodings, three varga separators, two planet-naming
-- systems, and (discovered during this lane's live reconnaissance) a sign
-- dimension with its own two encodings. Every downstream consumer that
-- wants "what's in house 7" or "Venus's D9 sign" has been hand-rolling its
-- own fragile substring parsing against this text (SIDDHANTA_STATE.md DB10
-- documents a `house_1`-substring-collides-with-`house_10/11/12` defect
-- from exactly this class of ad-hoc parsing).
--
-- This migration adds ONE new, purely additive, derived table populated by
-- the single deterministic parser at
-- `platform/python-sidecar/brahmagyan/fact_identity_parser.py`. It changes
-- nothing about `chart_facts` (R19: chart_facts stays sealed forever — this
-- table is read-derived from it, never the reverse) and is fully
-- rebuildable from `chart_facts` alone at any time via
-- `platform/python-sidecar/scripts/build_fact_identity_index.py`, which
-- does a per-chart DELETE-then-INSERT (CLAUDE.md §N.3 L1+ idempotency
-- standard: rebuild REPLACES, never accretes).
--
-- Column choices (adjusted from the lane brief's starting shape after live
-- reconnaissance — see A5_COVERAGE_REPORT_v1_0.md §1 for the full shape
-- inventory this schema was derived from, not guessed):
--   - graha_code_secondary / house_num_secondary: chart_facts carries a
--     real population of two-entity relational facts (graha-to-graha
--     aspects/conjunctions/friendships/wars, varga house-to-house argala
--     edges) whose *second* participant is itself identity, not a plain
--     attribute value — dropping it would silently halve what the Index
--     captures for those rows.
--   - sign_num: rashi (1-12) identity is smuggled in fact_subject/fact_key
--     text via the same swamp pattern as houses (`D9_SIGN_4`, hyphen
--     `MOON-SIGN_1`, bare sign names in `aspect_jaimini`) but is NOT the
--     same dimension as a bhava/house number (sign is ascendant-
--     independent, house is not) — a distinct column keeps the two from
--     ever being conflated by a future writer or reader.
--   - parse_rule / parsed_from: per-row provenance so a human or
--     PARĪKṢAKA auditing any row can see exactly which named rule matched
--     and against which original string(s), per the lane brief's
--     provenance requirement.

BEGIN;

CREATE TABLE IF NOT EXISTS chart_fact_identity (
  fact_id               TEXT PRIMARY KEY REFERENCES chart_facts(fact_id) ON DELETE CASCADE,
  chart_id              UUID NOT NULL,
  entity_kind           TEXT NOT NULL,
  graha_code            TEXT NULL,
  graha_code_secondary  TEXT NULL,
  house_num             SMALLINT NULL CHECK (house_num BETWEEN 1 AND 12),
  house_num_secondary   SMALLINT NULL CHECK (house_num_secondary BETWEEN 1 AND 12),
  varga_id              TEXT NULL,
  sign_num              SMALLINT NULL CHECK (sign_num BETWEEN 1 AND 12),
  parse_rule            TEXT NOT NULL,
  parsed_from           TEXT NOT NULL,
  build_id              UUID NULL,
  computed_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Retrieval indexes mirroring chart_facts' own pattern (migration 204):
-- chart-scoped lookups are the dominant query shape ("occupants of house 7
-- in this chart", "this chart's D9 graha placements").
CREATE INDEX IF NOT EXISTS chart_fact_identity_chart_id_idx
  ON chart_fact_identity (chart_id);

CREATE INDEX IF NOT EXISTS chart_fact_identity_chart_entity_kind_idx
  ON chart_fact_identity (chart_id, entity_kind);

CREATE INDEX IF NOT EXISTS chart_fact_identity_chart_graha_idx
  ON chart_fact_identity (chart_id, graha_code)
  WHERE graha_code IS NOT NULL;

CREATE INDEX IF NOT EXISTS chart_fact_identity_chart_house_idx
  ON chart_fact_identity (chart_id, house_num)
  WHERE house_num IS NOT NULL;

CREATE INDEX IF NOT EXISTS chart_fact_identity_chart_varga_idx
  ON chart_fact_identity (chart_id, varga_id)
  WHERE varga_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS chart_fact_identity_chart_sign_idx
  ON chart_fact_identity (chart_id, sign_num)
  WHERE sign_num IS NOT NULL;

COMMIT;

-- DOWN (rollback): purely additive migration; dropping the table removes
-- exactly what this migration added and nothing else. Not expected to be
-- needed — the table is a derived cache with no independent data (it can
-- be rebuilt in full from chart_facts at any time).
--
--   DROP TABLE IF EXISTS chart_fact_identity;

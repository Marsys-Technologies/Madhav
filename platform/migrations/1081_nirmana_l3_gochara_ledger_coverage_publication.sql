-- RENUMBERED 1076->1081 on 2026-09-24: after the 1075 renumbering below, origin/l0/vedha-and-frame-repair
-- (PR #2727, L0 vedha-and-frame repair) claimed 1075-1079 in platform/supabase/migrations and all five
-- (1075-1079) were APPLIED to production on 2026-09-23. Both directories form one runner sequence; two 1075s would
-- order deterministically (l0_ before l3_) but would let "1075/1076 applied" read as this file. 1080/1081
-- were the lowest free numbers across every remote head, local head and worktree at renumbering time.
-- This file had never been applied outside a disposable DB. Record: ESCALATIONS.md E-007 addendum.
-- RENUMBERED 1072->1076 on 2026-09-23: 1072/1072 and 1073/1074 were found claimed on other unmerged
-- branches (sangam/stage3 + l3/kala-elevation-readiness in platform/supabase/migrations;
-- l3/kala-p1-1-b1-clear-guard and l3/kala-p1-2-builder-grants-timeout in platform/migrations).
-- 1075/1076 were the lowest numbers free across every remote branch at renumbering time.
-- Migration 1081 (originally authored as 1072, renumbered twice — see header above):
--   kala_gochara_convention + kala_gochara_contacts +
--                 kala_gochara_coverage + kala_gochara_publication
-- Created: 2026-09-23
-- WP6 (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1 §4.3/§4.4/§4.7/§5.5;
-- WP1_CONTRACTS.md §1.2/§3.1/§4.1/§5.2 lifted verbatim and refined;
-- GOCHARA_RULING_SHEET_v1_0 N-7, N-10 conditions). Author: nirmana l3
-- autonomous gochara run (WP6, ledger/coverage/publication implementation).
--
-- Numbering: 1072 is the next-free block in the shared platform/migrations +
-- platform/supabase/migrations sequence (1070 applied in platform/migrations;
-- 1071 claimed by the concurrent WP3c target_resolution_state migration;
-- platform/supabase/migrations holds only 1035/1036/1038/1041 in the 10xx
-- range). Verified 2026-09-23 by directory listing of both paths + git status.
--
-- DESIGN ARTIFACT for WP6: this file is applied ONLY to the disposable WP6
-- database (docker gochara-wp6-disposable). It must NEVER be applied to a
-- shared or production database; production application is WP10-gated.
--
-- Schema notes (refinements over the WP1 in-document drafts, each deliberate):
--   * contacts.input_generation_vector_id is UUID (NOT TEXT as drafted in
--     WP1 §3.1) with a real FK to kala_gochara_publication(manifest_id) —
--     the draft's TEXT annotation cannot FK to a UUID primary key, and the
--     join-ability argument WP1 made for convention_id applies equally here.
--   * publication UNIQUE (chart_id, generation) is additionally backed by a
--     partial unique index restricting status='published' (N-10: at most ONE
--     published manifest per chart+generation; candidate rebuilds may replace
--     the candidate row in place, but two published manifests never coexist).
--   * kala_gochara_convention is insert-only by trigger (WP1 §1.2:
--     "WP6 enforces: no UPDATE/DELETE; a correction is a new row").
--   * (chart_id, generation) serving scope on all three owned relations is
--     covered by primary-key / unique leading columns (contacts PK, coverage
--     PK, publication UNIQUE); the explicit serving indexes below are the
--     ones the P-4 read shapes and §4.5 latency measurements actually use.
--
-- ROLLBACK (down-migration, dependents first):
--   DROP TRIGGER IF EXISTS kala_gochara_convention_immutable ON kala_gochara_convention;
--   DROP FUNCTION IF EXISTS kala_gochara_convention_no_mutation();
--   DROP TABLE IF EXISTS kala_gochara_contacts;
--   DROP TABLE IF EXISTS kala_gochara_coverage;
--   DROP TABLE IF EXISTS kala_gochara_publication;
--   DROP TABLE IF EXISTS kala_gochara_convention;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ── 1. Convention vector (WP1 §1.2) ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS kala_gochara_convention (
  convention_id     TEXT PRIMARY KEY,          -- "sha256:<hex>" per WP1 §1.1
  -- TEXT, not uuid-typed: the natural id IS the full sha256 hex; coercing to
  -- uuid would truncate it and break independent reimplementation of the id
  -- from the vector alone (WP1 §1.2 type note).
  zodiac            TEXT NOT NULL,
  ayanamsha         TEXT NOT NULL,
  sidereal_method   TEXT NOT NULL,
  node_model        TEXT NOT NULL,
  node_source       TEXT NOT NULL,
  epoch_convention  TEXT NOT NULL,
  time_scale        TEXT NOT NULL,
  house_system      TEXT NOT NULL,
  ephemeris_mode    TEXT NOT NULL,             -- requested backend (method field)
  ephemeris_backend TEXT,                      -- from probe retflag, never requested flag
  probe_retflag     INTEGER,                   -- raw retflag of the registration probe calc
  se1_checksums     JSONB,                     -- {sepl_18, semo_18, seas_18} sha256 at registration
  method_version    TEXT NOT NULL,             -- kernel/projection method version (semver)
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE kala_gochara_convention IS
  'Gochara convention vector, one row per distinct vector; natural id = sha256 of the '
  'canonical vector fields (WP1_CONTRACTS.md §1.1). Two rows with different ids are '
  'never compared; a tolerance/method change inserts a new row, never edits one. '
  'Insert-only: enforced by the kala_gochara_convention_immutable trigger.';

-- WP1 §1.2 immutability, enforced in the database (not just the writer):
-- no UPDATE/DELETE; a correction is a new row.
CREATE OR REPLACE FUNCTION kala_gochara_convention_no_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'kala_gochara_convention is insert-only (WP1_CONTRACTS.md §1.2): % not permitted; register a new convention row instead', TG_OP;
END;
$$;

DROP TRIGGER IF EXISTS kala_gochara_convention_immutable ON kala_gochara_convention;
CREATE TRIGGER kala_gochara_convention_immutable
  BEFORE UPDATE OR DELETE ON kala_gochara_convention
  FOR EACH ROW EXECUTE FUNCTION kala_gochara_convention_no_mutation();

-- ── 2. Publication manifest (WP1 §5.2) — created BEFORE contacts so the
--    contacts FK (input_generation_vector_id -> manifest_id) has a target. ──

CREATE TABLE IF NOT EXISTS kala_gochara_publication (
  manifest_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id          UUID NOT NULL,
  generation        TEXT NOT NULL,              -- '4.0', '4.1', ... (never g4_*)
  writer_asset_id   TEXT NOT NULL,              -- 'ka_gochara'
  convention_id     TEXT NOT NULL REFERENCES kala_gochara_convention(convention_id),
  input_generation_vector JSONB NOT NULL,       -- WP1 §5.3 (content digests for
                                                --   bg_transit_rules / bg_transit_av_gates)
  ephemeris_backend JSONB NOT NULL,             -- {backend, retflag, se1_checksums} from
                                                --   the build's retflag(s), never requested
  horizon           TSTZRANGE NOT NULL,
  row_counts        JSONB NOT NULL,             -- {contacts:n, coverage:n, windows:n}
  content_digest    TEXT NOT NULL,              -- sha256 over the canonical row set
  status            TEXT NOT NULL DEFAULT 'candidate'
                    CHECK (status IN ('candidate','published','superseded','rolled_back')),
  published_at      TIMESTAMPTZ,
  superseded_at     TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE (chart_id, generation)
);

-- N-10: at most ONE published manifest per (chart_id, generation).
CREATE UNIQUE INDEX IF NOT EXISTS kala_gochara_publication_one_published
  ON kala_gochara_publication (chart_id, generation)
  WHERE status = 'published';

-- Serving shape: per-chart manifest listing by status.
CREATE INDEX IF NOT EXISTS idx_kgpub_chart ON kala_gochara_publication
  (chart_id, status, generation);

COMMENT ON TABLE kala_gochara_publication IS
  'Publication manifest (N-10): one row per (chart, generation). A generation is '
  'immutable once published; a rebuild while candidate replaces the candidate; after '
  'publication a rebuild is a NEW generation label. The writer refuses '
  'delete-then-insert against a published generation (WP6 gate, N-7 condition).';

-- ── 3. Contact ledger (WP1 §3.1, N-7) ───────────────────────────────────────

CREATE TABLE IF NOT EXISTS kala_gochara_contacts (
  -- identity
  chart_id          UUID NOT NULL,
  generation        TEXT NOT NULL,              -- '4.0', '4.1', ... (never g4_*)
  contact_id        TEXT NOT NULL,              -- "sha256:<hex>" per WP1 §3.2
  independence_group TEXT NOT NULL,             -- H-6: one physical contact via several
                                                --   targets/rules counts once
  -- geometry
  body              TEXT NOT NULL,              -- Title-case graha agent
  relation          TEXT NOT NULL,              -- conjunction|drishti_contact|
                                                --   sign_ingress|nakshatra_ingress|
                                                --   kakshya_cell_crossing|return
  aspect_deg        NUMERIC,                    -- dṛṣṭi angle for drishti_contact; else 0
  target_type       TEXT NOT NULL,              -- WP1 §5.3 target_type (target_kind)
  target_ref        TEXT NOT NULL,              -- resonance-map ref (graha/house/fact_id/yoga id)
  target_fact_id    TEXT,                       -- L1 chart_facts.fact_id or NULL
  target_resolution_state TEXT NOT NULL
                    CHECK (target_resolution_state IN ('resolved','unavailable','unqualified')),
  target_longitude_deg NUMERIC,                 -- reference copy; L1 is authority
  -- time
  t_in              TIMESTAMPTZ NOT NULL,
  t_exact           TIMESTAMPTZ NOT NULL,
  t_out             TIMESTAMPTZ NOT NULL,
  bracket_seconds   INTEGER NOT NULL,           -- declared per relation class (WP1 §9)
  tolerance_arcsec  NUMERIC NOT NULL,           -- declared per relation class (WP1 §9)
  truncated_at_horizon TEXT CHECK (truncated_at_horizon IN ('start','end') OR truncated_at_horizon IS NULL),
  -- motion
  branch            TEXT NOT NULL CHECK (branch IN ('direct','retrograde','station')),
  station_flag      BOOLEAN NOT NULL DEFAULT FALSE,
  exact_crossing    BOOLEAN NOT NULL DEFAULT TRUE,
  orb_max_deg       NUMERIC NOT NULL,
  orb_source        TEXT NOT NULL,              -- WP1 §7 orb-table row id
  dwell_days        NUMERIC,
  -- qualification (F04/F06/F12)
  epistemic_class   TEXT NOT NULL,
  completeness_state TEXT NOT NULL,             -- six F06 states; unqualified propagated
                                                --   from near_station_unresolved, never a
                                                --   silent boolean
  operator_role     TEXT NOT NULL,
  claim_grain       TEXT NOT NULL,
  time_basis        TEXT NOT NULL,
  comparable_with   TEXT NOT NULL CHECK (comparable_with IN
                    ('self','same_convention_same_inputs',
                     'same_convention_newer_inputs','different_convention')),
  -- provenance
  convention_id     TEXT NOT NULL REFERENCES kala_gochara_convention(convention_id),
  ephemeris_backend JSONB NOT NULL,             -- {backend, retflag, se1_checksums{...}}
  evidence_fact_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  classical_citation TEXT,
  uncited_extension BOOLEAN NOT NULL DEFAULT FALSE,
  corpus_verifiable BOOLEAN,                    -- cited text resolves in served corpus
  input_generation_vector_id UUID NOT NULL
                    REFERENCES kala_gochara_publication(manifest_id),
  build_id          TEXT NOT NULL,
  computed_at       TIMESTAMPTZ NOT NULL,

  PRIMARY KEY (chart_id, generation, contact_id)
);

-- Covering indexes for the serving queries the P-4 read capability and the
-- §4.5 latency measurement actually run (WP6 measures with THESE in place;
-- (chart_id, generation) scope itself is the PK leading prefix on this relation).
-- P-4 read shape: per-chart+generation, per body+relation, t_exact range scan.
CREATE INDEX IF NOT EXISTS idx_kgc_serve_p4 ON kala_gochara_contacts
  (chart_id, generation, body, relation, t_exact) INCLUDE
  (target_type, target_ref, contact_id, independence_group,
   completeness_state, comparable_with, target_resolution_state);
-- H-6 dedup/read: all rows of one physical contribution.
CREATE INDEX IF NOT EXISTS idx_kgc_independence ON kala_gochara_contacts
  (chart_id, generation, independence_group);
-- Target-lookup read shape.
CREATE INDEX IF NOT EXISTS idx_kgc_target ON kala_gochara_contacts
  (chart_id, generation, target_type, target_ref);

COMMENT ON TABLE kala_gochara_contacts IS
  'Gochara contact ledger (N-7): one row per episode per chart per generation. '
  'Natural key (chart_id, generation, contact_id). contact_id = sha256 over the '
  'canonical serialization at WP1_CONTRACTS.md §3.2 — stable under horizon '
  're-partitioning. Overlay state at the contact instant is deliberately NOT stored '
  'here; the projection recomputes it from interval sets (plan §4.3).';

-- ── 4. Search-coverage manifest (WP1 §4.1, plan §4.4) ──────────────────────

CREATE TABLE IF NOT EXISTS kala_gochara_coverage (
  chart_id            UUID NOT NULL,
  generation          TEXT NOT NULL,
  partition_kind      TEXT NOT NULL
                      CHECK (partition_kind IN ('body_target','event_class','moon_on_demand')),
  partition_key       TEXT NOT NULL,   -- e.g. 'saturn:karaka' | 'marriage' |
                                       --   'moon:interval:<start>/<end>'
  convention_id       TEXT NOT NULL REFERENCES kala_gochara_convention(convention_id),
  requested_horizon   TSTZRANGE NOT NULL,
  completed_horizon   TSTZRANGE NOT NULL,   -- H-3: reported exactly, never silently
                                            --   truncated into the requested range
  resolution          NUMERIC NOT NULL,     -- ε (arcsec) used for this partition
  relations_searched  TEXT[] NOT NULL,
  targets_requested   INTEGER NOT NULL,
  targets_resolved    INTEGER NOT NULL,
  targets_unresolved  INTEGER NOT NULL,
  target_resolution_state_counts JSONB NOT NULL,  -- {"resolved":n,"unavailable":n,
                                                  --  "unqualified":n}
  unavailable_inputs  JSONB NOT NULL DEFAULT '{}'::jsonb,
  unsearched_reason   TEXT,          -- NULL when fully searched; else the honest reason
  build_id            TEXT NOT NULL,
  computed_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (chart_id, generation, partition_kind, partition_key)
);

CREATE INDEX IF NOT EXISTS idx_kgcov_chart ON kala_gochara_coverage
  (chart_id, generation, partition_kind);

COMMENT ON TABLE kala_gochara_coverage IS
  'Search-coverage manifest (plan §4.4): requested vs completed horizon, resolution, '
  'relations searched, target resolution states, unavailable inputs, unsearched '
  'reason. Moon on-demand partitions are first-class (partition_kind=moon_on_demand): '
  'a Moon search writes a coverage record for the requested interval even though '
  'Moon contacts are not persisted by default (R7).';

COMMIT;

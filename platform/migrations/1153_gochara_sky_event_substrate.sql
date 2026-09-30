-- Migration 1153: ka_gochara sky-event substrate — convention, physical
--                 object, and contact identity per GOCHARA_DESIGN_SPECS_v1_4
--                 §6.1 (schema, physical-object identity, occurrence-ordinal
--                 contact identity, ordinal-domain pinning, publication
--                 immutability) + §7.1 (solver_method / uncertainty fields).
-- Created: 2026-09-30. Author: pravaha/a5-migrations (Stream A, A5.1).
--
-- Numbering: 1153 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4; 1150/1151/1152 are used). Verified free by a fresh scan of
-- every origin/* ref across BOTH platform/migrations/ and
-- platform/supabase/migrations/ (2026-09-30: max in use anywhere is 1152;
-- no 1153 anywhere). `npm run guard:migration-numbers` green on this branch.
--
-- Spec: 00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_4.md
-- (FROZEN 2026-09-30, D-SPECS_DECISION_v1_0). What is encoded where:
--   * CONSTRAINT: event_kind 5-enum (§6.1); solver_method 3-enum (§7.1);
--     occurrence_ordinal >= 1 (§6.1 NK-2); UNIQUE (physical_object_id,
--     occurrence_ordinal) per convention (§6.1); station ⇒ swiss_refined
--     (§7.1 "stations are always Swiss-refined", O-SM-3); coverage.truncated
--     boolean flag present; t_exact NULL ⟺ coverage.truncated = true
--     (§6.1 truncated contacts carry no exact centre — the same rule 1152
--     enforced on kala_gochara_contacts); domain_start/domain_end NOT NULL
--     (§6.1 "the convention carries its domain start and end").
--   * TRIGGER: ka_gochara_sky_convention and ka_gochara_physical_object are
--     insert-only (a correction is a new row; §7.2 inv 4 — a tolerance or
--     method change implies a new convention_id). ka_gochara_sky_event:
--     DELETE forbidden; UPDATE forbidden on identity fields (event_id,
--     physical_object_id, occurrence_ordinal, convention_id, body,
--     event_kind) and on any published non-NULL t_exact/longitude; filling a
--     NULL t_exact/longitude (truncated → exact enrichment in place, same
--     id, same ordinal — §6.1) is allowed. Publication immutability per §6.1:
--     once published, contact ids are never renumbered or reused; any change
--     to a published non-NULL value is a correction (new id, supersedes edge
--     via supersedes_event_id, old id retired).
--   * COMMENT ONLY (writer behaviour, not SQL-checkable): the hash recipes
--     (physical_object_id = hash(body, relation_kind, canonical_target,
--     convention_id); event/contact id = hash(physical_object_id,
--     occurrence_ordinal)); canonical_target canonicalisation
--     (point:λ full precision / span:sign / star:index); canonical identity
--     bytes `body|relation_kind|canonical_target|convention_id|ordinal`;
--     ordinal assignment over the FULL-domain ordered crossing set (never a
--     clipped partition), forward-time partitions only, append-only
--     partition extension; loud failure on hash collision; Moon events
--     generated on demand (§6.1 contract counts).
--   * DELIBERATELY NOT ENCODED: the "0° seam root exists" / both-boundaries
--     search rules (§6.2) — solver-side invariants, no table shape here.
--
-- asset_registry: deliberately NOT registered. asset_registry.layer CHECK
-- admits only ('brahmagyan','ganita','bodha','kala','phala','mimamsa') —
-- there is no 'L2' layer value, so the shape does not match; and these are
-- contract tables of the already-registered ka_gochara writer family, like
-- kala_gochara_convention/contacts/coverage in 1081, which registered no
-- new asset rows.
--
-- Operational properties:
--   * Pure CREATE TABLE / CREATE FUNCTION / CREATE TRIGGER migration; no
--     existing table, guard, or data is touched. No production data writes.
--   * ONE TRANSACTION via the BEGIN/COMMIT below (1081 style; migrate.ts
--     also wraps the file, and SET LOCAL is scoped to the transaction).
--   * Replay-idempotent by construction: every DDL uses IF NOT EXISTS /
--     CREATE OR REPLACE / DROP TRIGGER IF EXISTS, so a second application is
--     a no-op. migrate.ts still never replays (tracked in
--     _migrations_applied).
--   * New-table creation is cheap; the SET LOCAL bounds below are stated
--     honestly, not because lock pressure is expected.
--
-- ROLLBACK (down-migration, dependents first):
--   DROP TRIGGER IF EXISTS ka_gochara_sky_event_mutation_guard ON ka_gochara_sky_event;
--   DROP TRIGGER IF EXISTS ka_gochara_physical_object_immutable ON ka_gochara_physical_object;
--   DROP TRIGGER IF EXISTS ka_gochara_sky_convention_immutable ON ka_gochara_sky_convention;
--   DROP FUNCTION IF EXISTS ka_gochara_sky_event_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_physical_object_no_mutation();
--   DROP FUNCTION IF EXISTS ka_gochara_sky_convention_no_mutation();
--   DROP TABLE IF EXISTS ka_gochara_sky_event;
--   DROP TABLE IF EXISTS ka_gochara_physical_object;
--   DROP TABLE IF EXISTS ka_gochara_sky_convention;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── 1. Convention (§6.1 substrate dimensions + ordinal-domain pinning) ─────

CREATE TABLE IF NOT EXISTS ka_gochara_sky_convention (
  convention_id       TEXT PRIMARY KEY,          -- "sha256:<hex>" over the canonical
                                                 --   substrate vector (§6.1; TEXT not
                                                 --   uuid — same rationale as
                                                 --   kala_gochara_convention in 1081)
  ephemeris_generation TEXT NOT NULL,            -- ephemeris/convention generation (§6.1)
  ayanamsha           TEXT NOT NULL,             -- ayanāṃśa dimension (§6.1)
  node_convention     TEXT NOT NULL,             -- node convention (mean/true etc., §6.1)
  grid                TEXT NOT NULL,             -- search grid / resolution (§6.1)
  method_version      TEXT NOT NULL,             -- §7.2 inv 4: tolerance/method change ⇒
                                                 --   new convention_id; contact ids hash
                                                 --   method_version
  domain_start        TIMESTAMPTZ NOT NULL,      -- ordinal-domain pinning (§6.1): ordinals
                                                 --   computed over the full domain, never
                                                 --   over a clipped partition
  domain_end          TIMESTAMPTZ NOT NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  CHECK (domain_start < domain_end)
);

COMMENT ON TABLE ka_gochara_sky_convention IS
  'Sky-event substrate convention (GOCHARA_DESIGN_SPECS_v1_4 §6.1): one substrate per '
  '(ephemeris/convention generation, ayanāṃśa, node convention, body, grid) — the '
  'per-body dimension lives on ka_gochara_physical_object; this row carries the shared '
  'vector plus the ordinal domain (domain_start/domain_end) that pins occurrence '
  'ordinals to the FULL-domain ordered crossing set (§6.1, Codex amendment 1). A '
  'backward partition is a new convention_id. Insert-only (trigger).';

CREATE OR REPLACE FUNCTION ka_gochara_sky_convention_no_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'ka_gochara_sky_convention is insert-only (GOCHARA_DESIGN_SPECS_v1_4 §6.1/§7.2 inv 4): % not permitted; a tolerance/method/domain change is a new convention_id', TG_OP;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_sky_convention_immutable ON ka_gochara_sky_convention;
CREATE TRIGGER ka_gochara_sky_convention_immutable
  BEFORE UPDATE OR DELETE ON ka_gochara_sky_convention
  FOR EACH ROW EXECUTE FUNCTION ka_gochara_sky_convention_no_mutation();

-- ── 2. Physical object (§6.1 canonical physical-object identity) ───────────

CREATE TABLE IF NOT EXISTS ka_gochara_physical_object (
  physical_object_id  UUID PRIMARY KEY,          -- hash(body, relation_kind,
                                                 --   canonical_target, convention_id) (§6.1);
                                                 --   computed by the writer — the hash
                                                 --   recipe is NOT re-implemented in SQL
  body                TEXT NOT NULL,             -- transiting body (graha set; §2.1 agent set)
  relation_kind       TEXT NOT NULL,             -- physical relation kind of the crossing
                                                 --   (e.g. sign/nakshatra/kakshya boundary
                                                 --   crossing, station, eclipse contact)
  canonical_target    TEXT NOT NULL,             -- canonicalised BEFORE any role/label:
                                                 --   'point:<λ full precision>' /
                                                 --   'span:<sign>' / 'star:<index>' (§6.1);
                                                 --   hashing a rounded t_exact or a
                                                 --   role-qualified target is FORBIDDEN
  convention_id       TEXT NOT NULL REFERENCES ka_gochara_sky_convention(convention_id),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT ka_gochara_physical_object_natural_uq
    UNIQUE (body, relation_kind, canonical_target, convention_id)
);

COMMENT ON TABLE ka_gochara_physical_object IS
  'Canonical physical object (GOCHARA_DESIGN_SPECS_v1_4 §6.1): label-independent physical '
  'identity (v3.0 #27); one object per (body, relation_kind, canonical_target, '
  'convention_id). A retrograde re-crossing of one target is a second CONTACT of this one '
  'object, never a second object (O-RX-1). Canonical identity bytes (O-RX-1 lineage): '
  'body|relation_kind|canonical_target|convention_id|ordinal. Hash-collision handling: the '
  'build fails loudly, no silent dedup (§6.1) — writer behaviour, stated here as contract. '
  'Insert-only (trigger): a corrected physical reading mints a new id and supersedes.';

CREATE OR REPLACE FUNCTION ka_gochara_physical_object_no_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'ka_gochara_physical_object is insert-only (GOCHARA_DESIGN_SPECS_v1_4 §6.1 publication immutability): % not permitted; a correction is a new object plus a supersedes edge on the event', TG_OP;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_physical_object_immutable ON ka_gochara_physical_object;
CREATE TRIGGER ka_gochara_physical_object_immutable
  BEFORE UPDATE OR DELETE ON ka_gochara_physical_object
  FOR EACH ROW EXECUTE FUNCTION ka_gochara_physical_object_no_mutation();

-- ── 3. Sky event / contact (§6.1 schema + §7.1 solver fields) ──────────────

CREATE TABLE IF NOT EXISTS ka_gochara_sky_event (
  event_id            UUID PRIMARY KEY,          -- the contact id (NK-2):
                                                 --   hash(physical_object_id,
                                                 --   occurrence_ordinal); writer-computed
  physical_object_id  UUID NOT NULL REFERENCES ka_gochara_physical_object(physical_object_id),
  convention_id       TEXT NOT NULL REFERENCES ka_gochara_sky_convention(convention_id),
  body                TEXT NOT NULL,             -- denormalised copy of the object's body;
                                                 --   identity bytes include it (§6.1)
  event_kind          TEXT NOT NULL CHECK (event_kind IN
                        ('sign_ingress','nakshatra_ingress','kakshya_crossing',
                         'station','eclipse_instant')),           -- §6.1 closed enum
  occurrence_ordinal  INTEGER NOT NULL CHECK (occurrence_ordinal >= 1),
                        -- 1-based index inside the ordered set of crossings of the same
                        -- physical tuple, ordered by solved t_exact at full precision,
                        -- over the FULL domain of the convention — never a clipped
                        -- partition (§6.1); a truncated contact takes (ordinals already
                        -- assigned) + 1, ordered by t_in until the centre is solved
  t_exact             TIMESTAMPTZ,               -- NULL iff the exact centre lies beyond the
                                                 -- solved partition (truncated, N3); no
                                                 -- fabricated ingress (§6.2 inv 2)
  longitude           DOUBLE PRECISION,          -- λ at the crossing at FULL solved
                                                 -- precision; never rounded before hashing
                                                 -- or canonicalisation (§6.1)
  solver_method       TEXT NOT NULL CHECK (solver_method IN
                        ('arc_index_bracket','swiss_refined','clipped_truncated')), -- §7.1
  delta_lambda        REAL,                      -- §7.1 uncertainty (degrees)
  delta_t             REAL,                      -- §7.1 uncertainty (seconds); δt ≈ δλ/|λ̇|
                                                 -- is unstable near stations — stations
                                                 -- are always swiss_refined (CHECK below)
  precision_regime    TEXT,                      -- §7.1
  coverage            JSONB NOT NULL,            -- includes the truncated flag (§6.1/N3)
  supersedes_event_id UUID REFERENCES ka_gochara_sky_event(event_id),
                        -- correction lineage (§6.1 publication immutability): a corrected
                        -- reading mints a new id that supersedes; the old id is retired,
                        -- never renumbered or reused
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT ka_gochara_sky_event_ordinal_uq
    UNIQUE (physical_object_id, occurrence_ordinal),
    -- §6.1: one crossing exists once per tuple; occurrence 2 of one object is the
    -- retrograde re-crossing (O-RX-1)
  CONSTRAINT ka_gochara_sky_event_coverage_shape_check
    CHECK (jsonb_typeof(coverage) = 'object'
           AND jsonb_typeof(coverage -> 'truncated') = 'boolean'),
  CONSTRAINT ka_gochara_sky_event_t_exact_iff_truncated
    CHECK ((t_exact IS NULL) = COALESCE((coverage ->> 'truncated')::boolean, false)),
    -- a truncated row carries NO exact centre; an exact row is not flagged truncated
    -- (the anti-fabrication rule 1152 enforced on kala_gochara_contacts, applied here
    -- to the substrate at creation)
  CHECK (event_kind <> 'station' OR solver_method = 'swiss_refined')
    -- §7.1: stations are always Swiss-refined (O-SM-3)
);

COMMENT ON TABLE ka_gochara_sky_event IS
  'Sky-event / contact substrate (GOCHARA_DESIGN_SPECS_v1_4 §6.1, §7.1): one solved '
  'physical relation between a transiting body and a physical object, once per '
  'convention_id. Contact identity = hash(physical_object_id, occurrence_ordinal); '
  'ordinals are pinned to the convention domain (§6.1). Publication immutability '
  '(trigger below): DELETE forbidden; UPDATE may only fill NULL t_exact/longitude '
  '(truncated → exact in-place enrichment, same id/ordinal — §6.1); any other change is '
  'a correction: new event id, supersedes_event_id edge, old id retired. Moon events are '
  'generated on demand and write a moon_on_demand coverage record (§6.1).';

COMMENT ON COLUMN ka_gochara_sky_event.supersedes_event_id IS
  'Correction edge (§6.1): points at the retired contact this row replaces. NULL on '
  'original publications. The retired row is never deleted (trigger).';

-- Publication immutability (§6.1): enrichment may only fill NULL / truncated-
-- flagged fields; a change to any published non-NULL value of t_exact,
-- longitude, ordinal, target or id fields is a correction, never an update.
CREATE OR REPLACE FUNCTION ka_gochara_sky_event_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'ka_gochara_sky_event is publication-immutable (GOCHARA_DESIGN_SPECS_v1_4 §6.1): DELETE forbidden; a correction retires a contact via a superseding event, never by deletion';
  END IF;
  -- identity / target fields: never mutable
  IF NEW.event_id            <> OLD.event_id
     OR NEW.physical_object_id <> OLD.physical_object_id
     OR NEW.occurrence_ordinal <> OLD.occurrence_ordinal
     OR NEW.convention_id      <> OLD.convention_id
     OR NEW.body               <> OLD.body
     OR NEW.event_kind         <> OLD.event_kind THEN
    RAISE EXCEPTION 'ka_gochara_sky_event identity fields are immutable (§6.1): a change to id/ordinal/target/convention is a correction — mint a new event id with a supersedes edge, never UPDATE';
  END IF;
  -- published non-NULL t_exact / longitude: never mutable; filling a NULL
  -- (truncated → exact enrichment, same id, same ordinal) is the only
  -- permitted in-place write (§6.1)
  IF OLD.t_exact IS NOT NULL AND NEW.t_exact IS DISTINCT FROM OLD.t_exact THEN
    RAISE EXCEPTION 'ka_gochara_sky_event.t_exact is published and non-NULL (§6.1): changing it is a correction (new id + supersedes edge), not an UPDATE';
  END IF;
  IF OLD.longitude IS NOT NULL AND NEW.longitude IS DISTINCT FROM OLD.longitude THEN
    RAISE EXCEPTION 'ka_gochara_sky_event.longitude is published and non-NULL (§6.1): changing it is a correction (new id + supersedes edge), not an UPDATE';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_sky_event_mutation_guard ON ka_gochara_sky_event;
CREATE TRIGGER ka_gochara_sky_event_mutation_guard
  BEFORE UPDATE OR DELETE ON ka_gochara_sky_event
  FOR EACH ROW EXECUTE FUNCTION ka_gochara_sky_event_guard();

-- Serving/read shapes the writer and rehearsal actually use.
CREATE INDEX IF NOT EXISTS idx_kgse_object ON ka_gochara_sky_event
  (physical_object_id, occurrence_ordinal);
CREATE INDEX IF NOT EXISTS idx_kgse_convention_time ON ka_gochara_sky_event
  (convention_id, body, event_kind, t_exact);

COMMIT;

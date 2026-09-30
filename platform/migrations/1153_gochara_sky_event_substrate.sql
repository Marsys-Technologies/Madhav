-- Migration 1153: ka_gochara sky-event substrate — convention, physical
--                 object, boundary sky events, and the §6.1 CONTACT identity
--                 (GOCHARA_DESIGN_SPECS_v1_4 §6.1/§7, FROZEN 2026-09-30).
--                 Rewritten at A5.1 round 2 per ASTRA_REVIEW_A5_1_MIGRATIONS
--                 v1_0 (REJECT) amendments 1, 2, 4, 5, 6, 8, 9 and the
--                 steward rulings of 2026-09-30. 1153–1157 were never applied
--                 anywhere, so this is an in-place rewrite of the same number.
-- Created: 2026-09-30. Author: pravaha/a5-migrations (Stream A, A5.1).
--
-- Numbering: 1153 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4; 1150/1151/1152 are used). Verified free by a fresh scan of
-- every origin/* ref across BOTH platform/migrations/ and
-- platform/supabase/migrations/ (2026-09-30: max in use anywhere is 1152;
-- no 1153 anywhere). `npm run guard:migration-numbers` green on this branch.
--
-- ── Amendment 2 (P1 #2, deploy hazard) — TRANSACTION OWNERSHIP ─────────────
-- This file contains NO BEGIN/COMMIT. platform/scripts/migrate.ts owns ONE
-- transaction around (DDL execution + the _migrations_applied ledger insert)
-- — see migrate.ts runMigrations(): `BEGIN; query(sql); INSERT ledger;
-- COMMIT;` with ROLLBACK on any error. A migration-owned COMMIT would end
-- that transaction early and could leave committed DDL with no ledger row.
-- SET LOCAL below is scoped to the runner's transaction, as intended.
-- Atomicity is tested by
-- platform/tests/integration/gochara_a5_1_migrations.db.test.ts, which forces
-- a failure between DDL execution and ledger recording and proves nothing
-- persists.
--
-- ── Amendment 1 (P1 #1) — BOUNDARY EVENTS vs CONTACTS ──────────────────────
-- ka_gochara_sky_event carries ONLY the five boundary kinds (§6.1:
-- sign_ingress, nakshatra_ingress, kakshya_crossing, station,
-- eclipse_instant). The §6.1 contact identity — one solved physical relation
-- between a transiting body and a physical object (S:91/96/621-640), with
-- residence intervals and truncated spans (S:664-668) — lives in the new
-- ka_gochara_contact table: (physical tuple, occurrence ordinal, relation
-- kind, t_in/t_out/t_exact all nullable-but-ruled). Transit relationship
-- records (1155) FK the CONTACT, never the sky event (O-RX-1's conjunction
-- crossing at point:198.52 is a contact, not a boundary event).
--
-- Contact lifecycle (steward ruling; CLAUDE.md §N.3; spec §6.1/§10): the
-- contact ledger carries (chart_id, generation) ownership. The ka_gochara
-- writer family rebuilds a CANDIDATE generation by per-(chart_id ×
-- generation) delete-then-insert (§N.3); a generation covered by a
-- kala_gochara_publication row with status='published' is
-- publication-immutable (§6.1/§10.1): DELETE is refused by trigger, and
-- UPDATE may only ENRICH (fill a NULL / truncated-flagged field; never
-- change a published non-NULL value). The sky-event substrate is global
-- geometry: DELETE is forbidden outright; the same enrichment-only UPDATE
-- rule applies.
--
-- Legacy mapping (steward ruling): legacy kala_gochara_contacts rows
-- (1081; PK (chart_id, generation, contact_id TEXT "sha256:<hex>")) are NOT
-- migrated into ka_gochara_contact. The correspondence is BY GENERATION
-- ONLY: a legacy row's (chart_id, generation) scope equals a new row's
-- (chart_id, generation) scope; the legacy TEXT contact_id has no mapping
-- into the new UUID identity (hash(physical_object_id, occurrence_ordinal[,
-- correction_seq])) and is never reused. Readers needing legacy geometry
-- join kala_gochara_contacts by (chart_id, generation), not by id.
--
-- ── Amendment 6 (P1 #6) — CORRECTION IDENTITY (contract decision, stated) ──
-- A correction to a published reading must mint a new id, but the prescribed
-- hash inputs (physical_object_id, occurrence_ordinal) are unchanged and the
-- predecessor is never deleted or renumbered. Resolution: identity carries a
-- correction_seq (0 = original publication). A correction mints
-- hash(physical_object_id, occurrence_ordinal, correction_seq) with
-- correction_seq = predecessor + 1, and supersedes_*_id points at the
-- predecessor of the SAME tuple with correction_seq one less (insert trigger
-- verifies; self-supersession and supersession-history edits are forbidden).
-- Retirement is derivable — a row is retired iff another row supersedes it —
-- so no mutable retired flag exists. Uniqueness is over (physical_object_id,
-- occurrence_ordinal, correction_seq).
--
-- Encoded as:
--   * CONSTRAINT: event_kind 5-enum (§6.1); solver_method 3-enum (§7.1);
--     occurrence_ordinal >= 1; correction_seq >= 0; UNIQUE (physical_object_id,
--     occurrence_ordinal, correction_seq) on both identity tables; ordered
--     convention domain (domain_start < domain_end); coverage JSONB must CARRY
--     an explicit boolean 'truncated' key (a '{}' row fails — `?`, not
--     jsonb_typeof of a missing key); t_exact NULL ⟺ coverage.truncated=true;
--     every reported t_exact carries longitude + delta_lambda + delta_t +
--     precision_regime NOT NULL (§7.2 inv 1, amendment 5); station ⇒
--     swiss_refined (§7.1, O-SM-3); composite consistency FKs so an event's /
--     contact's (body, convention_id) can never disagree with its physical
--     object (amendment 4); body domain CHECKs (9-graha physical objects;
--     substrate bodies exclude Moon — O-SS-4: the global substrate holds NO
--     materialised Moon rows; Moon-on-demand is per-chart contact plus
--     business); contact relation_kind ∈ {residence, aspect, conjunction}
--     with t_in NOT NULL, t_out required unless truncated, and solved
--     t_exact inside [t_in, t_out]; canonical chart CHECK (D-SCOPE
--     disposition, amendment 9) on the per-chart contact ledger.
--   * TRIGGER: convention/physical_object insert-only (§7.2 inv 4); sky_event
--     DELETE-forbidden + enrichment-only UPDATE; contact publication-aware
--     lifecycle guard above; supersede-edge validation on INSERT (same tuple,
--     predecessor correction_seq, never superseded twice, never self).
--   * COMMENT ONLY (writer behaviour, not SQL-checkable): the hash recipes
--     (physical_object_id = hash(body, relation_kind, canonical_target,
--     convention_id); event/contact id = hash(physical_object_id,
--     occurrence_ordinal[, correction_seq])); canonical_target
--     canonicalisation (point:λ full precision / span:sign / star:index);
--     identity bytes `body|relation_kind|canonical_target|convention_id|
--     ordinal`; ordinal assignment over the FULL-domain ordered crossing set,
--     forward-time partitions only, append-only partition extension; loud
--     failure on hash collision; Moon events generated on demand with a
--     moon_on_demand coverage record (§6.1 contract counts, O-SS-4).
--   * DELIBERATELY NOT ENCODED: the "0° seam root exists" / both-boundaries
--     search rules (§6.2) — solver-side invariants, no table shape here.
--
-- asset_registry: deliberately NOT registered (asset_registry.layer CHECK
-- admits no 'L2' value; contract tables of the already-registered ka_gochara
-- writer family — same disposition as 1081).
--
-- Operational properties:
--   * Pure CREATE TABLE / FUNCTION / TRIGGER / INDEX + post-DDL verification;
--     no existing table, guard, or data is touched; no business-data writes.
--   * Execution outcomes (amendment 8), distinct and tested:
--       - fresh apply: objects created, verification blocks pass;
--       - repeat execution (same definitions): IF NOT EXISTS skips creation,
--         the verification blocks re-prove the definitions — a no-op;
--       - a drifted same-named object (missing column/constraint/trigger):
--         the verification block RAISES and the apply fails loudly. An
--         untracked same-named object is therefore never silently adopted.
--     migrate.ts itself never replays (tracked in _migrations_applied).
--
-- ROLLBACK (down-migration, dependents first):
--   DROP TRIGGER IF EXISTS ka_gochara_contact_supersede_check   ON ka_gochara_contact;
--   DROP TRIGGER IF EXISTS ka_gochara_contact_lifecycle_guard   ON ka_gochara_contact;
--   DROP TRIGGER IF EXISTS ka_gochara_sky_event_supersede_check ON ka_gochara_sky_event;
--   DROP TRIGGER IF EXISTS ka_gochara_sky_event_mutation_guard  ON ka_gochara_sky_event;
--   DROP TRIGGER IF EXISTS ka_gochara_physical_object_immutable ON ka_gochara_physical_object;
--   DROP TRIGGER IF EXISTS ka_gochara_sky_convention_immutable  ON ka_gochara_sky_convention;
--   DROP FUNCTION IF EXISTS ka_gochara_contact_supersede_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_contact_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_sky_event_supersede_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_sky_event_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_physical_object_no_mutation();
--   DROP FUNCTION IF EXISTS ka_gochara_sky_convention_no_mutation();
--   DROP TABLE IF EXISTS ka_gochara_contact;
--   DROP TABLE IF EXISTS ka_gochara_sky_event;
--   DROP TABLE IF EXISTS ka_gochara_physical_object;
--   DROP TABLE IF EXISTS ka_gochara_sky_convention;
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── 1. Convention (§6.1 substrate dimensions + ordinal-domain pinning) ─────

CREATE TABLE IF NOT EXISTS ka_gochara_sky_convention (
  convention_id       TEXT PRIMARY KEY,          -- "sha256:<hex>" over the canonical
                                                 --   substrate vector (§6.1)
  ephemeris_generation TEXT NOT NULL,
  ayanamsha           TEXT NOT NULL,
  node_convention     TEXT NOT NULL,
  grid                TEXT NOT NULL,
  method_version      TEXT NOT NULL,             -- §7.2 inv 4: tolerance/method change ⇒
                                                 --   new convention_id
  domain_start        TIMESTAMPTZ NOT NULL,      -- ordinal-domain pinning (§6.1)
  domain_end          TIMESTAMPTZ NOT NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT kgsc_domain_ordered_ck CHECK (domain_start < domain_end)
);

COMMENT ON TABLE ka_gochara_sky_convention IS
  'Sky-event substrate convention (GOCHARA_DESIGN_SPECS_v1_4 §6.1): one substrate per '
  '(ephemeris/convention generation, ayanāṃśa, node convention, grid, method version) '
  'plus the ordinal domain (domain_start/domain_end) that pins occurrence ordinals to '
  'the FULL-domain ordered crossing set. A backward partition is a new convention_id. '
  'Insert-only (trigger).';

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
                                                 --   canonical_target, convention_id);
                                                 --   writer-computed (§6.1)
  body                TEXT NOT NULL,             -- the body whose position defines the
                                                 --   object (natal Moon objects allowed —
                                                 --   the Moon exclusion binds the TRANSITING
                                                 --   substrate bodies, not natal targets)
  relation_kind       TEXT NOT NULL,             -- physical relation kind of the crossing
  canonical_target    TEXT NOT NULL,             -- canonicalised BEFORE any role/label:
                                                 --   'point:<λ full precision>' /
                                                 --   'span:<sign>' / 'star:<index>' (§6.1)
  convention_id       TEXT NOT NULL REFERENCES ka_gochara_sky_convention(convention_id),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT kgpo_body_domain_ck CHECK (body IN
    ('sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu')),
  CONSTRAINT kgpo_target_form_ck CHECK (canonical_target ~ '^(point:|span:|star:)'),
  CONSTRAINT ka_gochara_physical_object_natural_uq
    UNIQUE (body, relation_kind, canonical_target, convention_id),
  -- FK target for the composite consistency FKs of ka_gochara_sky_event and
  -- ka_gochara_contact (amendment 4): an event/contact can never disagree
  -- with its physical object on body or convention.
  CONSTRAINT kgpo_identity_uq
    UNIQUE (physical_object_id, body, convention_id)
);

COMMENT ON TABLE ka_gochara_physical_object IS
  'Canonical physical object (GOCHARA_DESIGN_SPECS_v1_4 §6.1): label-independent physical '
  'identity (v3.0 #27); one object per (body, relation_kind, canonical_target, '
  'convention_id). A retrograde re-crossing of one target is a second CONTACT of this one '
  'object, never a second object (O-RX-1). Canonical identity bytes: '
  'body|relation_kind|canonical_target|convention_id|ordinal. Hash-collision handling: the '
  'build fails loudly, no silent dedup (§6.1). Insert-only (trigger).';

CREATE OR REPLACE FUNCTION ka_gochara_physical_object_no_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'ka_gochara_physical_object is insert-only (GOCHARA_DESIGN_SPECS_v1_4 §6.1 publication immutability): % not permitted; a correction is a new object plus a supersedes edge', TG_OP;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_physical_object_immutable ON ka_gochara_physical_object;
CREATE TRIGGER ka_gochara_physical_object_immutable
  BEFORE UPDATE OR DELETE ON ka_gochara_physical_object
  FOR EACH ROW EXECUTE FUNCTION ka_gochara_physical_object_no_mutation();

-- ── 3. Sky event — BOUNDARY EVENTS ONLY (§6.1 + §7.1) ─────────────────────

CREATE TABLE IF NOT EXISTS ka_gochara_sky_event (
  event_id            UUID PRIMARY KEY,          -- hash(physical_object_id,
                                                 --   occurrence_ordinal, correction_seq)
  physical_object_id  UUID NOT NULL,
  convention_id       TEXT NOT NULL,
  body                TEXT NOT NULL,             -- transiting body; MUST equal the object's
                                                 --   body (composite FK below, amendment 4)
  event_kind          TEXT NOT NULL,
  occurrence_ordinal  INTEGER NOT NULL,          -- 1-based index inside the ordered
                                                 --   crossing set of the same physical
                                                 --   tuple, over the FULL convention domain
  correction_seq      INTEGER NOT NULL DEFAULT 0,-- amendment 6: 0 = original publication;
                                                 --   a correction is predecessor + 1
  t_exact             TIMESTAMPTZ,               -- NULL iff truncated (coverage.truncated)
  longitude           DOUBLE PRECISION,
  solver_method       TEXT NOT NULL,
  delta_lambda        REAL,
  delta_t             REAL,
  precision_regime    TEXT,
  coverage            JSONB NOT NULL,            -- MUST carry boolean 'truncated'
  supersedes_event_id UUID REFERENCES ka_gochara_sky_event(event_id),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT ka_gochara_sky_event_object_fk
    FOREIGN KEY (physical_object_id, body, convention_id)
    REFERENCES ka_gochara_physical_object (physical_object_id, body, convention_id),
  CONSTRAINT kgse_event_kind_ck CHECK (event_kind IN
    ('sign_ingress','nakshatra_ingress','kakshya_crossing','station','eclipse_instant')),
  CONSTRAINT kgse_body_domain_ck CHECK (body IN
    ('sun','mars','mercury','jupiter','venus','saturn','rahu','ketu')),
    -- O-SS-4: the global substrate holds NO materialised Moon rows; Moon
    -- boundary events are generated on demand (per-chart, with a
    -- moon_on_demand coverage record), never persisted here.
  CONSTRAINT kgse_ordinal_ck CHECK (occurrence_ordinal >= 1),
  CONSTRAINT kgse_correction_seq_ck CHECK (correction_seq >= 0),
  CONSTRAINT ka_gochara_sky_event_ordinal_uq
    UNIQUE (physical_object_id, occurrence_ordinal, correction_seq),
  CONSTRAINT kgse_solver_method_ck CHECK (solver_method IN
    ('arc_index_bracket','swiss_refined','clipped_truncated')),
  CONSTRAINT kgse_coverage_shape_ck
    CHECK (jsonb_typeof(coverage) = 'object'
           AND coverage ? 'truncated'
           AND jsonb_typeof(coverage -> 'truncated') = 'boolean'),
    -- amendment 5: an explicit boolean truncated key is REQUIRED; '{}' fails
    -- (jsonb_typeof of a missing key is NULL, which used to satisfy the CHECK)
  CONSTRAINT kgse_t_exact_iff_truncated_ck
    CHECK ((t_exact IS NULL) = (coverage ->> 'truncated')::boolean),
  CONSTRAINT kgse_exact_precision_ck
    CHECK (t_exact IS NULL
           OR (longitude IS NOT NULL AND delta_lambda IS NOT NULL
               AND delta_t IS NOT NULL AND precision_regime IS NOT NULL)),
    -- §7.2 inv 1: every REPORTED t_exact carries its uncertainties and regime
  CONSTRAINT kgse_station_refined_ck
    CHECK (event_kind <> 'station' OR solver_method = 'swiss_refined'), -- O-SM-3
  CONSTRAINT kgse_no_self_supersede_ck
    CHECK (supersedes_event_id IS NULL OR supersedes_event_id <> event_id),
  CONSTRAINT kgse_correction_edge_ck
    CHECK ((correction_seq = 0) = (supersedes_event_id IS NULL))
);

COMMENT ON TABLE ka_gochara_sky_event IS
  'Boundary-event substrate (GOCHARA_DESIGN_SPECS_v1_4 §6.1, §7.1): the five boundary '
  'kinds ONLY. Transit contacts (residence/aspect/conjunction, truncated spans, '
  't_in/t_out) live in ka_gochara_contact — amendment 1. Correction identity: '
  'correction_seq + supersedes edge (amendment 6); a row is retired iff another row '
  'supersedes it (derivable; no mutable flag). Publication immutability (trigger): '
  'DELETE forbidden; UPDATE may only fill NULL/truncated-flagged fields.';

-- Supersede-edge validation (amendment 6): the edge must point at the
-- predecessor of the SAME tuple (physical_object_id, occurrence_ordinal)
-- with correction_seq one less, and a tuple version is superseded at most
-- once (supersession history is a chain, never a tree, and never mutable).
CREATE OR REPLACE FUNCTION ka_gochara_sky_event_supersede_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.supersedes_event_id IS NULL THEN
    RETURN NEW;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM ka_gochara_sky_event p
    WHERE p.event_id = NEW.supersedes_event_id
      AND p.physical_object_id = NEW.physical_object_id
      AND p.occurrence_ordinal = NEW.occurrence_ordinal
      AND p.correction_seq = NEW.correction_seq - 1
  ) THEN
    RAISE EXCEPTION 'ka_gochara_sky_event supersede edge invalid (amendment 6): % must reference the predecessor of the SAME (physical_object_id, occurrence_ordinal) with correction_seq %',
      NEW.supersedes_event_id, NEW.correction_seq - 1;
  END IF;
  IF EXISTS (
    SELECT 1 FROM ka_gochara_sky_event s
    WHERE s.supersedes_event_id = NEW.supersedes_event_id
  ) THEN
    RAISE EXCEPTION 'ka_gochara_sky_event % is already superseded (amendment 6): supersession history is a chain, never a tree',
      NEW.supersedes_event_id;
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_sky_event_supersede_check ON ka_gochara_sky_event;
CREATE TRIGGER ka_gochara_sky_event_supersede_check
  BEFORE INSERT ON ka_gochara_sky_event
  FOR EACH ROW EXECUTE FUNCTION ka_gochara_sky_event_supersede_guard();

-- Publication immutability + enrichment-only UPDATE (amendments 5/6):
-- identity fields never mutable; any non-NULL published value (t_exact,
-- longitude, solver_method, uncertainties, precision_regime, coverage,
-- supersedes edge) never changes in place; the only permitted writes are
-- NULL → value fills and the truncated → exact coverage flip.
CREATE OR REPLACE FUNCTION ka_gochara_sky_event_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE enrichment_flip boolean;
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'ka_gochara_sky_event is publication-immutable (GOCHARA_DESIGN_SPECS_v1_4 §6.1): DELETE forbidden; a correction retires an event via a superseding row, never by deletion';
  END IF;
  -- the one legitimate multi-field UPDATE: a truncated row's centre is solved
  -- — t_exact filled, the truncated flag flips, and the solver method may
  -- move off 'clipped_truncated' with it (§6.1 enrichment in place).
  enrichment_flip := (OLD.coverage ->> 'truncated')::boolean
    AND OLD.t_exact IS NULL AND NEW.t_exact IS NOT NULL
    AND NOT (NEW.coverage ->> 'truncated')::boolean
    AND (OLD.coverage - 'truncated') = (NEW.coverage - 'truncated');
  IF NEW.event_id            <> OLD.event_id
     OR NEW.physical_object_id <> OLD.physical_object_id
     OR NEW.occurrence_ordinal <> OLD.occurrence_ordinal
     OR NEW.correction_seq     <> OLD.correction_seq
     OR NEW.convention_id      <> OLD.convention_id
     OR NEW.body               <> OLD.body
     OR NEW.event_kind         <> OLD.event_kind THEN
    RAISE EXCEPTION 'ka_gochara_sky_event identity fields are immutable (§6.1): a change to id/ordinal/correction_seq/target/convention is a correction — mint a new id with a supersedes edge, never UPDATE';
  END IF;
  IF (OLD.t_exact           IS NOT NULL AND NEW.t_exact           IS DISTINCT FROM OLD.t_exact)
     OR (OLD.longitude      IS NOT NULL AND NEW.longitude       IS DISTINCT FROM OLD.longitude)
     OR (OLD.solver_method  IS NOT NULL AND NEW.solver_method   IS DISTINCT FROM OLD.solver_method
         AND NOT enrichment_flip)
     OR (OLD.delta_lambda   IS NOT NULL AND NEW.delta_lambda    IS DISTINCT FROM OLD.delta_lambda)
     OR (OLD.delta_t        IS NOT NULL AND NEW.delta_t         IS DISTINCT FROM OLD.delta_t)
     OR (OLD.precision_regime IS NOT NULL AND NEW.precision_regime IS DISTINCT FROM OLD.precision_regime)
     OR (OLD.supersedes_event_id IS NOT NULL AND NEW.supersedes_event_id IS DISTINCT FROM OLD.supersedes_event_id) THEN
    RAISE EXCEPTION 'ka_gochara_sky_event published non-NULL values are immutable (§6.1 enrichment-vs-correction): changing one is a correction (new id + supersedes edge), not an UPDATE';
  END IF;
  -- coverage may change ONLY as the truncated → exact flip that accompanies
  -- filling a NULL t_exact; every other coverage byte is immutable.
  IF NEW.coverage IS DISTINCT FROM OLD.coverage AND NOT enrichment_flip THEN
    RAISE EXCEPTION 'ka_gochara_sky_event.coverage is immutable except the truncated→exact enrichment flip (§6.1)';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_sky_event_mutation_guard ON ka_gochara_sky_event;
CREATE TRIGGER ka_gochara_sky_event_mutation_guard
  BEFORE UPDATE OR DELETE ON ka_gochara_sky_event
  FOR EACH ROW EXECUTE FUNCTION ka_gochara_sky_event_guard();

-- ── 4. Contact — the §6.1 contact identity, per-chart ledger ──────────────

CREATE TABLE IF NOT EXISTS ka_gochara_contact (
  contact_id          UUID PRIMARY KEY,          -- hash(physical_object_id,
                                                 --   occurrence_ordinal, correction_seq)
  chart_id            UUID NOT NULL REFERENCES charts(id),
  generation          TEXT NOT NULL,             -- '4.1'/'5.0'…; lifecycle scope (§N.3)
  physical_object_id  UUID NOT NULL,
  convention_id       TEXT NOT NULL,
  body                TEXT NOT NULL,             -- transiting body = the record's agent;
                                                 --   Moon allowed: Moon-on-demand contacts
                                                 --   persist per-chart inside admitted
                                                 --   windows with moon_on_demand coverage
  relation_kind       TEXT NOT NULL,             -- the transit relations of §1.1
  occurrence_ordinal  INTEGER NOT NULL,
  correction_seq      INTEGER NOT NULL DEFAULT 0,
  t_in                TIMESTAMPTZ NOT NULL,      -- in-orb interval start (truncated
                                                 --   spans included — S:637-640)
  t_out               TIMESTAMPTZ,               -- NULL only while truncated at the
                                                 --   partition end (N3)
  t_exact             TIMESTAMPTZ,               -- NULL iff truncated (coverage.truncated)
  solver_method       TEXT NOT NULL,
  delta_lambda        REAL,
  delta_t             REAL,
  precision_regime    TEXT,
  coverage            JSONB NOT NULL,            -- MUST carry boolean 'truncated'
  supersedes_contact_id UUID REFERENCES ka_gochara_contact(contact_id),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT ka_gochara_contact_object_fk
    FOREIGN KEY (physical_object_id, body, convention_id)
    REFERENCES ka_gochara_physical_object (physical_object_id, body, convention_id),
  CONSTRAINT kgc_canonical_chart_ck
    CHECK (chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid),
    -- D-SCOPE disposition (amendment 9): the frozen contract serves the
    -- canonical chart only; widening requires a migration.
  CONSTRAINT kgc_body_domain_ck CHECK (body IN
    ('sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu')),
  CONSTRAINT kgc_relation_kind_ck CHECK (relation_kind IN
    ('residence','aspect','conjunction')),
  CONSTRAINT kgc_ordinal_ck CHECK (occurrence_ordinal >= 1),
  CONSTRAINT kgc_correction_seq_ck CHECK (correction_seq >= 0),
  CONSTRAINT ka_gochara_contact_ordinal_uq
    UNIQUE (physical_object_id, occurrence_ordinal, correction_seq),
  -- FK target for relationship_record's composite consistency FK
  -- (amendment 4): a transit record's agent/object can never disagree with
  -- its referenced contact.
  CONSTRAINT kgc_identity_uq
    UNIQUE (contact_id, body, physical_object_id),
  CONSTRAINT kgc_solver_method_ck CHECK (solver_method IN
    ('arc_index_bracket','swiss_refined','clipped_truncated')),
  CONSTRAINT kgc_coverage_shape_ck
    CHECK (jsonb_typeof(coverage) = 'object'
           AND coverage ? 'truncated'
           AND jsonb_typeof(coverage -> 'truncated') = 'boolean'),
  CONSTRAINT kgc_t_exact_iff_truncated_ck
    CHECK ((t_exact IS NULL) = (coverage ->> 'truncated')::boolean),
  CONSTRAINT kgc_t_out_unless_truncated_ck
    CHECK (t_out IS NOT NULL OR (coverage ->> 'truncated')::boolean),
  CONSTRAINT kgc_exact_precision_ck
    CHECK (t_exact IS NULL
           OR (delta_lambda IS NOT NULL AND delta_t IS NOT NULL
               AND precision_regime IS NOT NULL)),
  CONSTRAINT kgc_time_order_ck
    CHECK (t_exact IS NULL
           OR (t_in <= t_exact AND (t_out IS NULL OR t_exact <= t_out))),
  CONSTRAINT kgc_span_order_ck
    CHECK (t_out IS NULL OR t_in < t_out),
  CONSTRAINT kgc_no_self_supersede_ck
    CHECK (supersedes_contact_id IS NULL OR supersedes_contact_id <> contact_id),
  CONSTRAINT kgc_correction_edge_ck
    CHECK ((correction_seq = 0) = (supersedes_contact_id IS NULL))
);

COMMENT ON TABLE ka_gochara_contact IS
  'Transit-contact ledger (GOCHARA_DESIGN_SPECS_v1_4 §6.1 contact identity; amendment 1): '
  'one solved physical relation between a transiting body and a physical object — '
  'physical tuple + occurrence ordinal + relation kind, with residence intervals and '
  'truncated spans (t_in/t_out/t_exact ruled nullable, N3). Per-(chart_id × generation) '
  'ownership: the writer rebuilds a CANDIDATE generation by delete-then-insert '
  '(CLAUDE.md §N.3); a published generation is immutable (lifecycle trigger). Legacy '
  'kala_gochara_contacts rows (TEXT contact_id) are NOT migrated — correspondence is by '
  '(chart_id, generation) scope only; legacy ids are never reused. Correction identity: '
  'correction_seq + supersedes edge (amendment 6).';

CREATE OR REPLACE FUNCTION ka_gochara_contact_supersede_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.supersedes_contact_id IS NULL THEN
    RETURN NEW;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM ka_gochara_contact p
    WHERE p.contact_id = NEW.supersedes_contact_id
      AND p.physical_object_id = NEW.physical_object_id
      AND p.occurrence_ordinal = NEW.occurrence_ordinal
      AND p.correction_seq = NEW.correction_seq - 1
  ) THEN
    RAISE EXCEPTION 'ka_gochara_contact supersede edge invalid (amendment 6): % must reference the predecessor of the SAME (physical_object_id, occurrence_ordinal) with correction_seq %',
      NEW.supersedes_contact_id, NEW.correction_seq - 1;
  END IF;
  IF EXISTS (
    SELECT 1 FROM ka_gochara_contact s
    WHERE s.supersedes_contact_id = NEW.supersedes_contact_id
  ) THEN
    RAISE EXCEPTION 'ka_gochara_contact % is already superseded (amendment 6): supersession history is a chain, never a tree',
      NEW.supersedes_contact_id;
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_contact_supersede_check ON ka_gochara_contact;
CREATE TRIGGER ka_gochara_contact_supersede_check
  BEFORE INSERT ON ka_gochara_contact
  FOR EACH ROW EXECUTE FUNCTION ka_gochara_contact_supersede_guard();

-- Lifecycle guard (amendment 1; CLAUDE.md §N.3; spec §6.1/§10.1):
--   DELETE — allowed while the row's (chart_id, generation) is NOT covered by
--     a published kala_gochara_publication manifest (candidate rebuild:
--     per-chart delete-then-insert); REFUSED once published.
--   UPDATE — enrichment-only, always: identity fields immutable; any non-NULL
--     published value immutable; NULL/truncated-flagged fields may be filled
--     (partition extension solving a centre updates the row in place, same
--     id, same ordinal — §6.1).
CREATE OR REPLACE FUNCTION ka_gochara_contact_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE enrichment_flip boolean;
BEGIN
  IF TG_OP = 'DELETE' THEN
    IF EXISTS (
      SELECT 1 FROM kala_gochara_publication pub
      WHERE pub.chart_id = OLD.chart_id
        AND pub.generation = OLD.generation
        AND pub.status = 'published'
    ) THEN
      RAISE EXCEPTION 'ka_gochara_contact is publication-immutable (GOCHARA_DESIGN_SPECS_v1_4 §6.1/§10.1): (chart_id %, generation %) is published — DELETE refused; a correction mints a new id with a supersedes edge',
        OLD.chart_id, OLD.generation;
    END IF;
    RETURN OLD;
  END IF;
  enrichment_flip := (OLD.coverage ->> 'truncated')::boolean
    AND OLD.t_exact IS NULL AND NEW.t_exact IS NOT NULL
    AND NOT (NEW.coverage ->> 'truncated')::boolean
    AND (OLD.coverage - 'truncated') = (NEW.coverage - 'truncated');
  IF NEW.contact_id         <> OLD.contact_id
     OR NEW.chart_id           <> OLD.chart_id
     OR NEW.generation         <> OLD.generation
     OR NEW.physical_object_id <> OLD.physical_object_id
     OR NEW.occurrence_ordinal <> OLD.occurrence_ordinal
     OR NEW.correction_seq     <> OLD.correction_seq
     OR NEW.convention_id      <> OLD.convention_id
     OR NEW.body               <> OLD.body
     OR NEW.relation_kind      <> OLD.relation_kind THEN
    RAISE EXCEPTION 'ka_gochara_contact identity fields are immutable (§6.1): a change to id/chart/generation/ordinal/target/relation is a correction — mint a new id with a supersedes edge, never UPDATE';
  END IF;
  IF (OLD.t_in              IS NOT NULL AND NEW.t_in              IS DISTINCT FROM OLD.t_in)
     OR (OLD.t_out          IS NOT NULL AND NEW.t_out             IS DISTINCT FROM OLD.t_out)
     OR (OLD.t_exact        IS NOT NULL AND NEW.t_exact           IS DISTINCT FROM OLD.t_exact)
     OR (OLD.solver_method  IS NOT NULL AND NEW.solver_method     IS DISTINCT FROM OLD.solver_method
         AND NOT enrichment_flip)
     OR (OLD.delta_lambda   IS NOT NULL AND NEW.delta_lambda      IS DISTINCT FROM OLD.delta_lambda)
     OR (OLD.delta_t        IS NOT NULL AND NEW.delta_t           IS DISTINCT FROM OLD.delta_t)
     OR (OLD.precision_regime IS NOT NULL AND NEW.precision_regime IS DISTINCT FROM OLD.precision_regime)
     OR (OLD.supersedes_contact_id IS NOT NULL AND NEW.supersedes_contact_id IS DISTINCT FROM OLD.supersedes_contact_id) THEN
    RAISE EXCEPTION 'ka_gochara_contact published non-NULL values are immutable (§6.1 enrichment-vs-correction): changing one is a correction (new id + supersedes edge), not an UPDATE';
  END IF;
  IF NEW.coverage IS DISTINCT FROM OLD.coverage AND NOT enrichment_flip THEN
    RAISE EXCEPTION 'ka_gochara_contact.coverage is immutable except the truncated→exact enrichment flip (§6.1)';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_contact_lifecycle_guard ON ka_gochara_contact;
CREATE TRIGGER ka_gochara_contact_lifecycle_guard
  BEFORE UPDATE OR DELETE ON ka_gochara_contact
  FOR EACH ROW EXECUTE FUNCTION ka_gochara_contact_guard();

-- Serving/read shapes the writer and rehearsal actually use. (The old
-- idx_kgse_object is deliberately NOT recreated: ka_gochara_sky_event_ordinal_uq
-- already supplies that index — review minor item.)
CREATE INDEX IF NOT EXISTS idx_kgse_convention_time ON ka_gochara_sky_event
  (convention_id, body, event_kind, t_exact);
CREATE INDEX IF NOT EXISTS idx_kgc_chart_gen ON ka_gochara_contact
  (chart_id, generation, relation_kind, t_exact);
CREATE INDEX IF NOT EXISTS idx_kgc_object ON ka_gochara_contact
  (physical_object_id, occurrence_ordinal);

-- ── 5. Post-DDL definition verification (amendment 8) ─────────────────────
-- A fresh apply creates every object; a repeat execution re-proves the same
-- definitions (no-op); a drifted same-named object fails loudly HERE instead
-- of being silently adopted. Column tuples are (name, format_type, notnull).

DO $$
DECLARE missing text;
BEGIN
  WITH expected(tbl, col, typ, nn) AS (
    VALUES
      ('ka_gochara_sky_convention','convention_id','text',true),
      ('ka_gochara_sky_convention','ephemeris_generation','text',true),
      ('ka_gochara_sky_convention','ayanamsha','text',true),
      ('ka_gochara_sky_convention','node_convention','text',true),
      ('ka_gochara_sky_convention','grid','text',true),
      ('ka_gochara_sky_convention','method_version','text',true),
      ('ka_gochara_sky_convention','domain_start','timestamp with time zone',true),
      ('ka_gochara_sky_convention','domain_end','timestamp with time zone',true),
      ('ka_gochara_physical_object','physical_object_id','uuid',true),
      ('ka_gochara_physical_object','body','text',true),
      ('ka_gochara_physical_object','relation_kind','text',true),
      ('ka_gochara_physical_object','canonical_target','text',true),
      ('ka_gochara_physical_object','convention_id','text',true),
      ('ka_gochara_sky_event','event_id','uuid',true),
      ('ka_gochara_sky_event','physical_object_id','uuid',true),
      ('ka_gochara_sky_event','convention_id','text',true),
      ('ka_gochara_sky_event','body','text',true),
      ('ka_gochara_sky_event','event_kind','text',true),
      ('ka_gochara_sky_event','occurrence_ordinal','integer',true),
      ('ka_gochara_sky_event','correction_seq','integer',true),
      ('ka_gochara_sky_event','t_exact','timestamp with time zone',false),
      ('ka_gochara_sky_event','longitude','double precision',false),
      ('ka_gochara_sky_event','solver_method','text',true),
      ('ka_gochara_sky_event','delta_lambda','real',false),
      ('ka_gochara_sky_event','delta_t','real',false),
      ('ka_gochara_sky_event','precision_regime','text',false),
      ('ka_gochara_sky_event','coverage','jsonb',true),
      ('ka_gochara_sky_event','supersedes_event_id','uuid',false),
      ('ka_gochara_contact','contact_id','uuid',true),
      ('ka_gochara_contact','chart_id','uuid',true),
      ('ka_gochara_contact','generation','text',true),
      ('ka_gochara_contact','physical_object_id','uuid',true),
      ('ka_gochara_contact','convention_id','text',true),
      ('ka_gochara_contact','body','text',true),
      ('ka_gochara_contact','relation_kind','text',true),
      ('ka_gochara_contact','occurrence_ordinal','integer',true),
      ('ka_gochara_contact','correction_seq','integer',true),
      ('ka_gochara_contact','t_in','timestamp with time zone',true),
      ('ka_gochara_contact','t_out','timestamp with time zone',false),
      ('ka_gochara_contact','t_exact','timestamp with time zone',false),
      ('ka_gochara_contact','solver_method','text',true),
      ('ka_gochara_contact','delta_lambda','real',false),
      ('ka_gochara_contact','delta_t','real',false),
      ('ka_gochara_contact','precision_regime','text',false),
      ('ka_gochara_contact','coverage','jsonb',true),
      ('ka_gochara_contact','supersedes_contact_id','uuid',false)
  )
  SELECT string_agg(e.tbl || '.' || e.col, ', ' ORDER BY e.tbl, e.col) INTO missing
  FROM expected e
  LEFT JOIN pg_attribute a
    ON a.attrelid = to_regclass('public.' || e.tbl)
   AND a.attname = e.col AND NOT a.attisdropped
  WHERE a.attname IS NULL
     OR format_type(a.atttypid, a.atttypmod) IS DISTINCT FROM e.typ
     OR a.attnotnull IS DISTINCT FROM e.nn;
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1153 post-DDL verification failed (amendment 8): column drift: %', missing;
  END IF;

  WITH expected(conrelid, conname) AS (
    VALUES
      ('ka_gochara_sky_convention','kgsc_domain_ordered_ck'),
      ('ka_gochara_physical_object','kgpo_body_domain_ck'),
      ('ka_gochara_physical_object','kgpo_target_form_ck'),
      ('ka_gochara_physical_object','ka_gochara_physical_object_natural_uq'),
      ('ka_gochara_physical_object','kgpo_identity_uq'),
      ('ka_gochara_sky_event','ka_gochara_sky_event_object_fk'),
      ('ka_gochara_sky_event','kgse_event_kind_ck'),
      ('ka_gochara_sky_event','kgse_body_domain_ck'),
      ('ka_gochara_sky_event','kgse_ordinal_ck'),
      ('ka_gochara_sky_event','kgse_correction_seq_ck'),
      ('ka_gochara_sky_event','ka_gochara_sky_event_ordinal_uq'),
      ('ka_gochara_sky_event','kgse_solver_method_ck'),
      ('ka_gochara_sky_event','kgse_coverage_shape_ck'),
      ('ka_gochara_sky_event','kgse_t_exact_iff_truncated_ck'),
      ('ka_gochara_sky_event','kgse_exact_precision_ck'),
      ('ka_gochara_sky_event','kgse_station_refined_ck'),
      ('ka_gochara_sky_event','kgse_no_self_supersede_ck'),
      ('ka_gochara_sky_event','kgse_correction_edge_ck'),
      ('ka_gochara_contact','ka_gochara_contact_object_fk'),
      ('ka_gochara_contact','kgc_canonical_chart_ck'),
      ('ka_gochara_contact','kgc_body_domain_ck'),
      ('ka_gochara_contact','kgc_relation_kind_ck'),
      ('ka_gochara_contact','kgc_ordinal_ck'),
      ('ka_gochara_contact','kgc_correction_seq_ck'),
      ('ka_gochara_contact','ka_gochara_contact_ordinal_uq'),
      ('ka_gochara_contact','kgc_identity_uq'),
      ('ka_gochara_contact','kgc_solver_method_ck'),
      ('ka_gochara_contact','kgc_coverage_shape_ck'),
      ('ka_gochara_contact','kgc_t_exact_iff_truncated_ck'),
      ('ka_gochara_contact','kgc_t_out_unless_truncated_ck'),
      ('ka_gochara_contact','kgc_exact_precision_ck'),
      ('ka_gochara_contact','kgc_time_order_ck'),
      ('ka_gochara_contact','kgc_span_order_ck'),
      ('ka_gochara_contact','kgc_no_self_supersede_ck'),
      ('ka_gochara_contact','kgc_correction_edge_ck')
  )
  SELECT string_agg(e.conrelid || '.' || e.conname, ', ' ORDER BY 1) INTO missing
  FROM expected e
  WHERE NOT EXISTS (
    SELECT 1 FROM pg_constraint c
    WHERE c.conrelid = to_regclass('public.' || e.conrelid) AND c.conname = e.conname
  );
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1153 post-DDL verification failed (amendment 8): missing constraint: %', missing;
  END IF;

  WITH expected(tgrelid, tgname) AS (
    VALUES
      ('ka_gochara_sky_convention','ka_gochara_sky_convention_immutable'),
      ('ka_gochara_physical_object','ka_gochara_physical_object_immutable'),
      ('ka_gochara_sky_event','ka_gochara_sky_event_supersede_check'),
      ('ka_gochara_sky_event','ka_gochara_sky_event_mutation_guard'),
      ('ka_gochara_contact','ka_gochara_contact_supersede_check'),
      ('ka_gochara_contact','ka_gochara_contact_lifecycle_guard')
  )
  SELECT string_agg(e.tgrelid || '.' || e.tgname, ', ' ORDER BY 1) INTO missing
  FROM expected e
  WHERE NOT EXISTS (
    SELECT 1 FROM pg_trigger t
    WHERE t.tgrelid = to_regclass('public.' || e.tgrelid)
      AND t.tgname = e.tgname AND NOT t.tgisinternal
  );
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1153 post-DDL verification failed (amendment 8): missing trigger: %', missing;
  END IF;
END;
$$;

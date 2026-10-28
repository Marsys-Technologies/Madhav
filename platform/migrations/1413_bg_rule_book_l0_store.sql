-- 1413_bg_rule_book_l0_store.sql
--
-- Rule Book engine, packet E2 (ENGINE_PLAN_v0_2 §1, §5, §7): the L0 rule-book store, asset bg_rule_book.
-- AUTHORITY: owner approval OWNER-APPROVAL-ENGINE-NATIVE-ITEMS-20261028 ("yes to all three"), item (1): a new L0 asset bg_rule_book and its
-- tables, locked and versioned; the FROZEN orchestrator contract is unchanged (the writer registers through _auto_discover, no
-- orchestrator file is edited). Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here).
--
-- WHAT IT ADDS (additive only; no existing table, row, function or migration is touched other than ONE new asset_registry row and the
-- data_plane_builder grants on the three new tables):
--   public.l0_rule_book_versions      one row per rule-book version: manifest hash, card count, freeze stamp, change-register ids, current pointer
--   public.l0_rule_book_cards         one row per (version, card): the card in canonical REDACTED form + its hashes, compiled IR, extracted columns
--   public.l0_rule_book_card_classes  (version, card, class_group) join table: one card may serve several class groups (F-S10)
--   three trigger functions + their triggers: freeze immutability enforced IN THE DATABASE (F-S1, G-S9)
--   one asset_registry row: bg_rule_book, scope global, has_writer true, is_active FALSE (inert until a ratified card file is committed)
--
-- FREEZE IMMUTABILITY (the trigger contract):
--   * cards and card_classes: any INSERT, UPDATE or DELETE whose OLD or NEW version is frozen RAISES. The version row is read FOR SHARE so a
--     concurrent freeze waits for in-flight card writes, and a card write queued behind a freeze sees the freeze and raises. The freeze itself
--     must run at READ COMMITTED (the trigger refuses any other isolation level): at REPEATABLE READ the freeze-time counts below would use the
--     freezing transaction's older snapshot and could miss a card committed while it waited. Status changes
--     (active / quarantined_not_evaluable / withdrawn) are ordinary UPDATEs, so they are possible only while the version is unfrozen.
--   * versions: a row is INSERTed unfrozen (frozen_at must be NULL; it is frozen by UPDATE so the freeze-time checks below always run).
--     Once frozen_at is set, every column except is_current is immutable (compared as to_jsonb(row) minus is_current, so a column added later
--     is covered automatically), and the row cannot be DELETEd. Moving the current pointer stays possible (is_current is not content).
--   * at the freeze transition (frozen_at NULL -> NOT NULL) the trigger MEASURES what it seals and raises unless: the version holds exactly
--     card_count cards, every card has at least one class row, and every active card carries its IR.
--   * TRUNCATE on any of the three tables RAISES while any frozen version exists (row triggers do not fire on TRUNCATE).
--   WHO IT BINDS, stated so the guard cannot overclaim (§N.8): every role that does not own the tables, which includes the build identity
--   data_plane_builder (granted DML below, never TRUNCATE or TRIGGER). It does NOT bind the table owner (amjis_app, the migration login, per
--   1328): the owner can ALTER TABLE ... DISABLE TRIGGER, DROP TRIGGER, DROP TABLE, or CREATE OR REPLACE the guard functions, and those
--   statements are not caught by the public-schema privilege scan. Nor does it bind a superuser (session_replication_role = replica). Any such
--   change is a reviewed migration, not a writer path.
--
-- EXTRACTED COLUMNS TIED TO card_json BY CHECK (where Postgres can express it): card_id, category, polarity, provenance, passage_ids; the
-- verdict to the provenance (verse_cited <-> scored, commentarial_practice <-> testimony); the IR's card_id/category/polarity/provenance to the
-- row; an active row to an IR whose own status is active; an empty redaction map to ratification_sha256 = card_sha256 (nothing was redacted,
-- so the full card IS the stored card). NOT expressible here and covered by the writer tests instead: card_sha256 / ir_sha256 against the
-- Python canonical JSON (jsonb text output is not that byte form), the class rows against card_json, and the licence rule (needs the allowlist).
--
-- QUOTES (M5, Q7): card_json is the canonical REDACTED form. The writer refuses (raises, writes nothing) any card carrying quote text for an
-- edition outside the compiler's public-domain allowlist. Restricted editions are stored as passage_ids + quote sha256 only.
--
-- ROUTE: public-schema DDL, so this file joins the Kāla protected window automatically (governance/kala_protected_migrations.py).
-- GRANTS (1410 pattern; 1328 records that tables created after the ownership cutover reach the builder only by explicit grant):
--   data_plane_builder   SELECT, INSERT, UPDATE, DELETE on the three tables. The writer upserts (INSERT+UPDATE+SELECT), replaces class rows and
--                        drops removed cards (DELETE+SELECT), and reads the version row FOR UPDATE; the trigger reads it FOR SHARE as the caller
--                        (both need UPDATE). No TRUNCATE, REFERENCES or TRIGGER. An absent role is NAMED in a NOTICE, never a silent pass.
--   amjis_app            none: it is the owner (the applying identity).
-- IDEMPOTENT: CREATE ... IF NOT EXISTS, CREATE OR REPLACE FUNCTION, DROP TRIGGER IF EXISTS + CREATE TRIGGER, INSERT ... ON CONFLICT DO NOTHING, GRANT of a held privilege is a no-op.
-- FAIL-CLOSED: refuses when asset_registry is missing; the post-apply block raises unless every table, constraint, index and trigger is present.
-- ROLLBACK (legal only while no version is frozen; loses only rule-book rows): DELETE FROM asset_registry WHERE asset_id = 'bg_rule_book';
--   DROP TABLE public.l0_rule_book_card_classes, public.l0_rule_book_cards, public.l0_rule_book_versions;
--   DROP FUNCTION public.l0_rule_book_guard_rows(), public.l0_rule_book_guard_version(), public.l0_rule_book_guard_truncate();

SET LOCAL lock_timeout = '5s';

-- ── 0. Prerequisites (fail-closed) ───────────────────────────────────────────
DO $$
BEGIN
  IF to_regclass('public.asset_registry') IS NULL THEN
    RAISE EXCEPTION 'migration 1413: prerequisite table public.asset_registry is missing';
  END IF;
END;
$$;

-- ── 1. Versions ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.l0_rule_book_versions (
  rulebook_version     TEXT        PRIMARY KEY,
  manifest_sha256      TEXT        NOT NULL,
  card_file_sha256     TEXT        NOT NULL,
  card_count           INTEGER     NOT NULL,
  frozen_at            TIMESTAMPTZ,
  change_register_ids  TEXT[]      NOT NULL DEFAULT '{}'::text[],
  is_current           BOOLEAN     NOT NULL DEFAULT false,
  build_id             TEXT,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT l0rbv_version_ck CHECK (rulebook_version ~ '^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$'),
  CONSTRAINT l0rbv_hashes_ck CHECK (manifest_sha256 ~ '^[0-9a-f]{64}$' AND card_file_sha256 ~ '^[0-9a-f]{64}$'),
  CONSTRAINT l0rbv_card_count_ck CHECK (card_count >= 0),
  -- only a frozen version can be current (count_sql and serving read the current frozen version)
  CONSTRAINT l0rbv_current_frozen_ck CHECK (NOT is_current OR frozen_at IS NOT NULL),
  -- a fixture version can never become current
  CONSTRAINT l0rbv_fixture_never_current_ck CHECK (NOT (is_current AND upper(rulebook_version) LIKE 'FIXTURE-%'))
);

-- at most one current version
CREATE UNIQUE INDEX IF NOT EXISTS l0rbv_one_current_uq ON public.l0_rule_book_versions ((true)) WHERE is_current;

COMMENT ON TABLE public.l0_rule_book_versions IS
  'Rule Book engine E2 (OWNER-APPROVAL-ENGINE-NATIVE-ITEMS-20261028): one row per rule-book version. Frozen by setting frozen_at (UPDATE only); '
  'after that every column except is_current is immutable (trigger l0rbv_guard). At most one row is_current, and only a frozen row may be.';
COMMENT ON COLUMN public.l0_rule_book_versions.manifest_sha256 IS
  'sha256 of the version manifest in canonical JSON (sorted keys, compact separators, UTF-8), as the writer read it.';
COMMENT ON COLUMN public.l0_rule_book_versions.card_file_sha256 IS
  'sha256 of the committed card file bytes; the writer refuses a file whose bytes do not match the manifest.';

-- ── 2. Cards ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.l0_rule_book_cards (
  rulebook_version     TEXT        NOT NULL REFERENCES public.l0_rule_book_versions(rulebook_version),
  card_id              TEXT        NOT NULL,
  card_json            JSONB       NOT NULL,
  card_sha256          TEXT        NOT NULL,
  ratification_sha256  TEXT        NOT NULL,
  redaction_map_json   JSONB       NOT NULL DEFAULT '[]'::jsonb,
  ir_json              JSONB,
  ir_sha256            TEXT,
  category             TEXT        NOT NULL,
  polarity             TEXT        NOT NULL,
  provenance           TEXT        NOT NULL,
  verdict              TEXT        NOT NULL,
  passage_ids          TEXT[]      NOT NULL DEFAULT '{}'::text[],
  status               TEXT        NOT NULL,
  quarantine_reason    TEXT,
  build_id             TEXT,
  written_at           TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (rulebook_version, card_id),
  CONSTRAINT l0rbc_enums_ck CHECK (
    category IN ('natal_promise', 'dasha', 'transit')
    AND polarity IN ('promotive', 'obstructive')
    AND provenance IN ('verse_cited', 'commentarial_practice')
    AND verdict IN ('scored', 'testimony')
    AND status IN ('active', 'quarantined_not_evaluable', 'withdrawn')),
  CONSTRAINT l0rbc_verdict_provenance_ck CHECK ((verdict = 'scored') = (provenance = 'verse_cited')),
  CONSTRAINT l0rbc_hashes_ck CHECK (
    card_sha256 ~ '^[0-9a-f]{64}$' AND ratification_sha256 ~ '^[0-9a-f]{64}$'
    AND (ir_sha256 IS NULL OR ir_sha256 ~ '^[0-9a-f]{64}$')),
  -- the IR and its hash travel together
  CONSTRAINT l0rbc_ir_pair_ck CHECK ((ir_json IS NULL) = (ir_sha256 IS NULL)),
  -- the extracted columns are the card's own values
  -- (COALESCE(..., false): a missing key yields NULL, which a CHECK would otherwise accept)
  CONSTRAINT l0rbc_card_json_ck CHECK (COALESCE(
    jsonb_typeof(card_json) = 'object'
    AND card_json ->> 'card_id' = card_id
    AND card_json #>> '{field2_target_scope,category}' = category
    AND card_json ->> 'polarity' = polarity
    AND card_json ->> 'provenance' = provenance
    AND to_jsonb(passage_ids) = COALESCE(card_json #> '{field1_citation,passage_ids}', '[]'::jsonb), false)),
  -- the IR, when present, describes this row's card
  CONSTRAINT l0rbc_ir_json_ck CHECK (
    ir_json IS NULL OR COALESCE(
      jsonb_typeof(ir_json) = 'object'
      AND ir_json ->> 'card_id' = card_id
      AND ir_json ->> 'category' = category
      AND ir_json ->> 'polarity' = polarity
      AND ir_json ->> 'provenance' = provenance, false)),
  -- an active card has a compiled IR whose own status is active; a non-active card always says why
  CONSTRAINT l0rbc_status_ck CHECK (COALESCE(
    CASE status
      WHEN 'active' THEN ir_json IS NOT NULL AND ir_json ->> 'status' = 'active' AND quarantine_reason IS NULL
      ELSE quarantine_reason IS NOT NULL AND length(btrim(quarantine_reason)) > 0
    END, false)),
  -- nothing redacted -> the full (ratified) card is the stored card
  CONSTRAINT l0rbc_redaction_ck CHECK (COALESCE(
    jsonb_typeof(redaction_map_json) = 'array'
    AND (redaction_map_json <> '[]'::jsonb OR ratification_sha256 = card_sha256)
    AND (redaction_map_json = '[]'::jsonb OR ratification_sha256 <> card_sha256), false))
);

CREATE INDEX IF NOT EXISTS l0rbc_version_status_idx ON public.l0_rule_book_cards (rulebook_version, status);

COMMENT ON TABLE public.l0_rule_book_cards IS
  'Rule Book engine E2: one row per (rulebook_version, card_id). card_json is the canonical REDACTED card (no quote text for an edition outside '
  'the public-domain allowlist); card_sha256 is over that form, ratification_sha256 over the full ratified card, redaction_map_json lists what '
  'was removed. quarantined_not_evaluable rows are stored, never counted. Immutable once the version is frozen (trigger l0rbc_guard).';
COMMENT ON COLUMN public.l0_rule_book_cards.quarantine_reason IS
  'Why a non-active card is not active: the compiler findings or panel-return lint codes (quarantined_not_evaluable), or the manifest''s '
  'withdrawal reason (withdrawn). NULL exactly when status = active.';
COMMENT ON COLUMN public.l0_rule_book_cards.ratification_sha256 IS
  'sha256 of the full ratified card in canonical JSON. Equal to card_sha256 when nothing was redacted (CHECK). For a redacted card it is the '
  'value recorded at ratification and carried by the manifest; the writer can re-derive it only where the full text is available (owner session).';

-- ── 3. Card ↔ class-group join ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.l0_rule_book_card_classes (
  rulebook_version  TEXT NOT NULL,
  card_id           TEXT NOT NULL,
  class_group       TEXT NOT NULL,

  PRIMARY KEY (rulebook_version, card_id, class_group),
  CONSTRAINT l0rbcc_card_fk FOREIGN KEY (rulebook_version, card_id)
    REFERENCES public.l0_rule_book_cards (rulebook_version, card_id) ON DELETE CASCADE,
  -- the 20 CLASS_GROUPS of services/rulebook/constants.py (schema v1.2 enum; ledger CR-007-WAVE2-ENABLEMENT-20261028)
  CONSTRAINT l0rbcc_class_group_ck CHECK (class_group IN (
    'illness_chronic_surgery', 'relocation_travel', 'major_gain', 'major_loss', 'career_adv_change_entry',
    'business_launch', 'cross_cutting', 'marriage_relationship_begin', 'separation_relationship_end', 'bereavement_parent',
    'childbirth_progeny', 'education_learning', 'achievement_recognition', 'deception_fraud', 'foreign_residence',
    'parent_affairs_non_death', 'property_acquisition', 'mental_distress', 'spiritual_renunciation', 'career_setback'))
);

CREATE INDEX IF NOT EXISTS l0rbcc_class_idx ON public.l0_rule_book_card_classes (rulebook_version, class_group);

COMMENT ON TABLE public.l0_rule_book_card_classes IS
  'Rule Book engine E2: which class groups each card serves (F-S10). Immutable once the version is frozen (trigger l0rbcc_guard).';

-- ── 4. Freeze-immutability triggers ──────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.l0_rule_book_guard_rows() RETURNS trigger
LANGUAGE plpgsql AS $fn$
DECLARE
  v_frozen TIMESTAMPTZ;
BEGIN
  IF TG_OP IN ('UPDATE', 'DELETE') THEN
    SELECT frozen_at INTO v_frozen FROM public.l0_rule_book_versions
     WHERE rulebook_version = OLD.rulebook_version FOR SHARE;
    IF v_frozen IS NOT NULL THEN
      RAISE EXCEPTION 'l0_rule_book frozen: % on %.% refused; version % was frozen at %',
        TG_OP, TG_TABLE_SCHEMA, TG_TABLE_NAME, OLD.rulebook_version, v_frozen
        USING ERRCODE = 'object_not_in_prerequisite_state';
    END IF;
  END IF;
  IF TG_OP IN ('INSERT', 'UPDATE') THEN
    SELECT frozen_at INTO v_frozen FROM public.l0_rule_book_versions
     WHERE rulebook_version = NEW.rulebook_version FOR SHARE;
    IF v_frozen IS NOT NULL THEN
      RAISE EXCEPTION 'l0_rule_book frozen: % on %.% refused; version % was frozen at %',
        TG_OP, TG_TABLE_SCHEMA, TG_TABLE_NAME, NEW.rulebook_version, v_frozen
        USING ERRCODE = 'object_not_in_prerequisite_state';
    END IF;
    RETURN NEW;
  END IF;
  RETURN OLD;
END;
$fn$;

CREATE OR REPLACE FUNCTION public.l0_rule_book_guard_version() RETURNS trigger
LANGUAGE plpgsql AS $fn$
DECLARE
  v_cards INTEGER;
  v_classless INTEGER;
  v_active_no_ir INTEGER;
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.frozen_at IS NOT NULL THEN
      RAISE EXCEPTION 'l0_rule_book: version % must be inserted unfrozen and frozen by UPDATE (so the freeze-time checks run)',
        NEW.rulebook_version USING ERRCODE = 'object_not_in_prerequisite_state';
    END IF;
    RETURN NEW;
  END IF;
  IF TG_OP = 'DELETE' THEN
    IF OLD.frozen_at IS NOT NULL THEN
      RAISE EXCEPTION 'l0_rule_book frozen: DELETE of version % refused; frozen at %', OLD.rulebook_version, OLD.frozen_at
        USING ERRCODE = 'object_not_in_prerequisite_state';
    END IF;
    RETURN OLD;
  END IF;
  -- UPDATE
  IF OLD.frozen_at IS NOT NULL THEN
    IF (to_jsonb(NEW) - 'is_current') IS DISTINCT FROM (to_jsonb(OLD) - 'is_current') THEN
      RAISE EXCEPTION 'l0_rule_book frozen: version % content is immutable since %; only is_current may change',
        OLD.rulebook_version, OLD.frozen_at USING ERRCODE = 'object_not_in_prerequisite_state';
    END IF;
    RETURN NEW;
  END IF;
  IF NEW.frozen_at IS NOT NULL THEN
    -- the freeze transition: measure what is being sealed
    IF current_setting('transaction_isolation') <> 'read committed' THEN
      RAISE EXCEPTION 'l0_rule_book: freeze of % refused at isolation %; freeze at READ COMMITTED so the counts see every committed card',
        NEW.rulebook_version, current_setting('transaction_isolation') USING ERRCODE = 'object_not_in_prerequisite_state';
    END IF;
    IF NEW.rulebook_version IS DISTINCT FROM OLD.rulebook_version THEN
      RAISE EXCEPTION 'l0_rule_book: a version cannot be renamed while being frozen' USING ERRCODE = 'object_not_in_prerequisite_state';
    END IF;
    SELECT COUNT(*) INTO v_cards FROM public.l0_rule_book_cards WHERE rulebook_version = NEW.rulebook_version;
    IF v_cards <> NEW.card_count THEN
      RAISE EXCEPTION 'l0_rule_book: freeze of % refused: % card rows, card_count says %', NEW.rulebook_version, v_cards, NEW.card_count
        USING ERRCODE = 'object_not_in_prerequisite_state';
    END IF;
    SELECT COUNT(*) INTO v_classless FROM public.l0_rule_book_cards c
     WHERE c.rulebook_version = NEW.rulebook_version
       AND NOT EXISTS (SELECT 1 FROM public.l0_rule_book_card_classes k
                        WHERE k.rulebook_version = c.rulebook_version AND k.card_id = c.card_id);
    IF v_classless > 0 THEN
      RAISE EXCEPTION 'l0_rule_book: freeze of % refused: % card(s) without a class row', NEW.rulebook_version, v_classless
        USING ERRCODE = 'object_not_in_prerequisite_state';
    END IF;
    -- DEFENSIVE, not a measured gate today: l0rbc_status_ck already makes the IR mandatory for an active row; kept so the seal
    -- still holds if that constraint is ever relaxed by a later migration.
    SELECT COUNT(*) INTO v_active_no_ir FROM public.l0_rule_book_cards
     WHERE rulebook_version = NEW.rulebook_version AND status = 'active' AND ir_json IS NULL;
    IF v_active_no_ir > 0 THEN
      RAISE EXCEPTION 'l0_rule_book: freeze of % refused: % active card(s) without IR', NEW.rulebook_version, v_active_no_ir
        USING ERRCODE = 'object_not_in_prerequisite_state';
    END IF;
  END IF;
  RETURN NEW;
END;
$fn$;

CREATE OR REPLACE FUNCTION public.l0_rule_book_guard_truncate() RETURNS trigger
LANGUAGE plpgsql AS $fn$
BEGIN
  IF EXISTS (SELECT 1 FROM public.l0_rule_book_versions WHERE frozen_at IS NOT NULL) THEN
    RAISE EXCEPTION 'l0_rule_book frozen: TRUNCATE of %.% refused while a frozen version exists', TG_TABLE_SCHEMA, TG_TABLE_NAME
      USING ERRCODE = 'object_not_in_prerequisite_state';
  END IF;
  RETURN NULL;
END;
$fn$;

DROP TRIGGER IF EXISTS l0rbv_guard ON public.l0_rule_book_versions;
CREATE TRIGGER l0rbv_guard BEFORE INSERT OR UPDATE OR DELETE ON public.l0_rule_book_versions
  FOR EACH ROW EXECUTE FUNCTION public.l0_rule_book_guard_version();
DROP TRIGGER IF EXISTS l0rbc_guard ON public.l0_rule_book_cards;
CREATE TRIGGER l0rbc_guard BEFORE INSERT OR UPDATE OR DELETE ON public.l0_rule_book_cards
  FOR EACH ROW EXECUTE FUNCTION public.l0_rule_book_guard_rows();
DROP TRIGGER IF EXISTS l0rbcc_guard ON public.l0_rule_book_card_classes;
CREATE TRIGGER l0rbcc_guard BEFORE INSERT OR UPDATE OR DELETE ON public.l0_rule_book_card_classes
  FOR EACH ROW EXECUTE FUNCTION public.l0_rule_book_guard_rows();

DROP TRIGGER IF EXISTS l0rbv_truncate_guard ON public.l0_rule_book_versions;
CREATE TRIGGER l0rbv_truncate_guard BEFORE TRUNCATE ON public.l0_rule_book_versions
  FOR EACH STATEMENT EXECUTE FUNCTION public.l0_rule_book_guard_truncate();
DROP TRIGGER IF EXISTS l0rbc_truncate_guard ON public.l0_rule_book_cards;
CREATE TRIGGER l0rbc_truncate_guard BEFORE TRUNCATE ON public.l0_rule_book_cards
  FOR EACH STATEMENT EXECUTE FUNCTION public.l0_rule_book_guard_truncate();
DROP TRIGGER IF EXISTS l0rbcc_truncate_guard ON public.l0_rule_book_card_classes;
CREATE TRIGGER l0rbcc_truncate_guard BEFORE TRUNCATE ON public.l0_rule_book_card_classes
  FOR EACH STATEMENT EXECUTE FUNCTION public.l0_rule_book_guard_truncate();

-- ── 5. Grants ────────────────────────────────────────────────────────────────
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
    GRANT SELECT, INSERT, UPDATE, DELETE ON public.l0_rule_book_versions, public.l0_rule_book_cards, public.l0_rule_book_card_classes
      TO data_plane_builder;
    RAISE NOTICE 'migration 1413: builder DML grants issued to role data_plane_builder on the three l0_rule_book tables';
  ELSE
    RAISE NOTICE 'migration 1413: role data_plane_builder NOT FOUND — NO builder grant was issued; the bg_rule_book writer cannot run as the build identity until it is provisioned and granted';
  END IF;
END;
$$;

-- ── 6. asset_registry row (seed column order, ASSET_REGISTRY_UPSERT_SQL) ─────
-- INERT (is_active = false): no ratified card file is committed yet (only a FIXTURE), so no planner selects it; has_writer = true so the
-- orchestrator's writer-gap pre-flight finds the @register('bg_rule_book') writer's row. Activation is a later, separate step.
INSERT INTO asset_registry (
  asset_id, layer, sort_order, sanskrit_name, english_name, english_description,
  storage_type, target_table, count_sql, size_sql, target_floor,
  expected_volume_formula, expected_volume_inputs, volume_explanation,
  depends_on, scope, is_active, estimated_seconds,
  asset_type, layer_name, layer_index, provides_apis, health_probe, catalog_status,
  asset_kind, has_writer, has_substeps, writer_timeout_seconds
) VALUES (
  'bg_rule_book',
  'brahmagyan',
  81,
  'Niyama-Grantha',
  'Rule Book (ratified Rule Cards, versioned and frozen)',
  'Rule Book engine E2 (OWNER-APPROVAL-ENGINE-NATIVE-ITEMS-20261028): the ratified, verse-cited Rule Cards as chart-agnostic L0 rows, one set per rulebook_version. Each card is stored in canonical redacted form (no quote text for an edition outside the public-domain allowlist) with card_sha256, ratification_sha256, its compiled closed-AST IR and ir_sha256, its class groups, and a status (active | quarantined_not_evaluable | withdrawn). A version is frozen by its freeze stamp, after which a database trigger refuses every change by the writer and any non-owner role. The writer reads the committed card file and manifest, runs the rulebook compiler and its licence lint, and refuses a frozen version.',
  'postgres_table',
  'l0_rule_book_cards',
  'SELECT COUNT(*) FROM l0_rule_book_cards c JOIN l0_rule_book_versions v ON v.rulebook_version = c.rulebook_version WHERE v.is_current AND v.frozen_at IS NOT NULL AND c.status = ''active''',
  'SELECT pg_total_relation_size(''l0_rule_book_cards'') + pg_total_relation_size(''l0_rule_book_card_classes'') + pg_total_relation_size(''l0_rule_book_versions'')',
  0,
  NULL,
  NULL,
  'Active cards of the current frozen rule-book version. 0 until a ratified version is written and frozen (E8); floors are aspirational and set to the achieved count (§N.4), never estimated.',
  '{}'::text[],
  'global',
  false,
  NULL,
  'data',
  'Brahmagyan',
  'L0',
  NULL,
  NULL,
  'CURRENT',
  'data',
  true,
  false,
  120
) ON CONFLICT (asset_id) DO NOTHING;

-- ── 7. Post-apply presence checks (raise, never a silent skip) ───────────────
DO $$
DECLARE missing text; t text; priv text;
BEGIN
  SELECT string_agg(x.name, ', ') INTO missing
  FROM (VALUES ('public.l0_rule_book_versions'), ('public.l0_rule_book_cards'), ('public.l0_rule_book_card_classes'),
               ('public.l0rbv_one_current_uq'), ('public.l0rbc_version_status_idx'), ('public.l0rbcc_class_idx')) AS x(name)
  WHERE to_regclass(x.name) IS NULL;
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1413 post-apply check failed: missing relation(s): %', missing;
  END IF;
  SELECT string_agg(x.name, ', ') INTO missing
  FROM (VALUES ('l0rbv_version_ck', 'public.l0_rule_book_versions'), ('l0rbv_hashes_ck', 'public.l0_rule_book_versions'),
               ('l0rbv_card_count_ck', 'public.l0_rule_book_versions'), ('l0rbv_current_frozen_ck', 'public.l0_rule_book_versions'),
               ('l0rbv_fixture_never_current_ck', 'public.l0_rule_book_versions'),
               ('l0rbc_enums_ck', 'public.l0_rule_book_cards'), ('l0rbc_verdict_provenance_ck', 'public.l0_rule_book_cards'),
               ('l0rbc_hashes_ck', 'public.l0_rule_book_cards'), ('l0rbc_ir_pair_ck', 'public.l0_rule_book_cards'),
               ('l0rbc_card_json_ck', 'public.l0_rule_book_cards'), ('l0rbc_ir_json_ck', 'public.l0_rule_book_cards'),
               ('l0rbc_status_ck', 'public.l0_rule_book_cards'), ('l0rbc_redaction_ck', 'public.l0_rule_book_cards'),
               ('l0rbcc_card_fk', 'public.l0_rule_book_card_classes'),
               ('l0rbcc_class_group_ck', 'public.l0_rule_book_card_classes')) AS x(name, rel)
  WHERE NOT EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conname = x.name AND c.convalidated AND c.conrelid = x.rel::regclass);
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1413 post-apply check failed: missing or unvalidated constraint(s): %', missing;
  END IF;
  SELECT string_agg(x.name, ', ') INTO missing
  FROM (VALUES ('l0rbv_guard', 'public.l0_rule_book_versions'), ('l0rbc_guard', 'public.l0_rule_book_cards'),
               ('l0rbcc_guard', 'public.l0_rule_book_card_classes'), ('l0rbv_truncate_guard', 'public.l0_rule_book_versions'),
               ('l0rbc_truncate_guard', 'public.l0_rule_book_cards'),
               ('l0rbcc_truncate_guard', 'public.l0_rule_book_card_classes')) AS x(name, rel)
  WHERE NOT EXISTS (SELECT 1 FROM pg_trigger tg WHERE tg.tgname = x.name AND tg.tgrelid = x.rel::regclass
                      AND NOT tg.tgisinternal AND tg.tgenabled = 'O');
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1413 post-apply check failed: missing or disabled trigger(s): %', missing;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM asset_registry WHERE asset_id = 'bg_rule_book' AND has_writer AND scope = 'global') THEN
    RAISE EXCEPTION 'migration 1413 post-apply check failed: asset_registry row bg_rule_book missing or not a global has_writer row';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
    FOREACH t IN ARRAY ARRAY['public.l0_rule_book_versions', 'public.l0_rule_book_cards', 'public.l0_rule_book_card_classes'] LOOP
      FOREACH priv IN ARRAY ARRAY['SELECT', 'INSERT', 'UPDATE', 'DELETE'] LOOP
        IF NOT has_table_privilege('data_plane_builder', t, priv) THEN
          RAISE EXCEPTION 'migration 1413 post-apply check failed: data_plane_builder lacks % on %', priv, t;
        END IF;
      END LOOP;
      FOREACH priv IN ARRAY ARRAY['TRUNCATE', 'TRIGGER', 'REFERENCES'] LOOP
        IF has_table_privilege('data_plane_builder', t, priv) THEN
          RAISE EXCEPTION 'migration 1413 post-apply check failed: data_plane_builder unexpectedly holds % on %', priv, t;
        END IF;
      END LOOP;
    END LOOP;
  END IF;
END;
$$;

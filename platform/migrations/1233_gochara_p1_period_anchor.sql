-- Migration 1233: P1 period ANCHOR on the relationship record — ADDITIVE over 1155.
-- Pravāha B6.0, Codex round 8 (steward M20261002T032818-fea8; AM-21 part 2 in the amendments draft v0.19), 2026-10-02.
-- Author: pravaha stream B. STATUS: HOLD (stacked on #2909 / 1232 only for the shared protected-window wiring).
--
-- WHY
-- ═══
-- A P1 (daśā-lord) transit record is licensed by the running periods of ONE lord at ONE level — its ANCHOR — and that lord is
-- NOT always the transiting agent (Phaladīpikā XX.38, phaladeepika:PG250:C1: "the Sun enters the planet's exaltation sign"
-- delivers the BHUKTI lord's fruit; the Sun's own periods are irrelevant to that reading). Two readings of one physical contact
-- (Sun in Libra = the Sun's own debilitation sign AND Saturn's exaltation sign) are different records with different anchors,
-- period domains and directions, sharing one contact_id as role aliases (S §1.2 inv 3). The natural key (S §1.1) therefore
-- needs the anchor, and the existing columns cannot carry it: 1154's ka_gochara_frame_ok forces frame_arg NULL for
-- `dasha_lord` (and the classical frame is the lagna, AM-20); object_id must be the contacted physical object; prerequisites
-- carry predicate versions; source_text is a citation (a lord encoded in it would be identity by prose).
--
-- WHAT THIS DOES (and deliberately does NOT do)
-- ═════════════════════════════════════════════
--   1. Adds two nullable columns to ka_gochara_relationship_record: period_anchor_lord (nine lowercase graha tokens) and
--      period_anchor_level ('md' | 'ad' | 'pd').
--   2. Three CHECKs, so the failure names its cause: kgrr_period_anchor_pair_ck (both NULL or both set),
--      kgrr_period_anchor_vocab_ck (the token vocabularies), kgrr_period_anchor_path_ck (set EXACTLY for path_id 'P1').
--   3. Refuses to apply while any P1 record exists: such rows carry no anchor and cannot be given one (record_id is the
--      writer-computed hash of the natural key, which now includes the anchor); a P1 record set is rebuilt as a new generation.
--   NOT changed: no trigger, no function, no grant. The anchor columns ride the builder's table-level SELECT/INSERT on the
--   record table (1216 line 97); a SEALED generation stays frozen because ka_gochara_chart_write_guard compares
--   to_jsonb(NEW) - 'precision' with to_jsonb(OLD) - 'precision', which includes the new columns automatically. The writer
--   adds the anchor to the record_id hash and S §1.1's key list (version bump) — writer-side, not SQL.
--   RESIDUAL (stated): the database does not check that the stored anchor is the RIGHT lord for the record's reading; the
--   independent verifier derives it. The CHECKs bound the vocabulary and the path, not the doctrine.
--
-- WINDOW: protected public-schema window, AFTER 1155 (it ALTERs a 1155 table); logical order 1204 → 1206 → 1232 → 1233.
-- Transaction ownership: NO BEGIN/COMMIT — migrate.ts owns one transaction per migration.
-- ROLLBACK (unused installation only): DROP the three constraints, DROP the two columns, delete the _migrations_applied row.
-- Once any P1 record carries an anchor, correct forward instead.
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL search_path = public, pg_catalog;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── GATE ──────────────────────────────────────────────────────────────────────
DO $$
DECLARE failures text;
BEGIN
  WITH f(failure, detail) AS (
    SELECT 'migration_1155_not_applied', 'ka_gochara_relationship_record'
    WHERE to_regclass('public.ka_gochara_relationship_record') IS NULL
    UNION ALL SELECT 'migration_1233_already_applied', 'period_anchor_lord'
    WHERE EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema = 'public' AND table_name = 'ka_gochara_relationship_record'
                    AND column_name IN ('period_anchor_lord', 'period_anchor_level'))
  )
  SELECT string_agg(failure || ' (' || detail || ')', ', ') INTO failures FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1233 BLOCKED: %', failures;
  END IF;
  -- existing P1 rows have no anchor and cannot receive one (the key changes): refuse rather than guess
  IF EXISTS (SELECT 1 FROM public.ka_gochara_relationship_record WHERE path_id = 'P1') THEN
    RAISE EXCEPTION 'preflight 1233 BLOCKED: p1_records_exist_without_anchor (rebuild them as a new generation first)';
  END IF;
END;
$$;

-- ── 1. the anchor columns ─────────────────────────────────────────────────────
ALTER TABLE public.ka_gochara_relationship_record
  ADD COLUMN period_anchor_lord  TEXT,
  ADD COLUMN period_anchor_level TEXT;

-- ── 2. the checks ─────────────────────────────────────────────────────────────
ALTER TABLE public.ka_gochara_relationship_record
  ADD CONSTRAINT kgrr_period_anchor_pair_ck
    CHECK ((period_anchor_lord IS NULL) = (period_anchor_level IS NULL)),
  ADD CONSTRAINT kgrr_period_anchor_vocab_ck
    CHECK (period_anchor_lord IS NULL
           OR (period_anchor_lord IN ('sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu')
               AND period_anchor_level IN ('md','ad','pd'))),
  ADD CONSTRAINT kgrr_period_anchor_path_ck
    CHECK ((path_id = 'P1') = (period_anchor_lord IS NOT NULL));

COMMENT ON COLUMN public.ka_gochara_relationship_record.period_anchor_lord IS
  'AM-21 part 2: the period lord whose running periods license a P1 record and whose sign-quality it judges (not necessarily the agent: Phaladīpikā XX.38). NOT NULL exactly for path_id P1; part of the natural key (S §1.1).';
COMMENT ON COLUMN public.ka_gochara_relationship_record.period_anchor_level IS
  'AM-21 part 2: the level of the anchoring period (md = Dasa, ad = Bhukti, pd = Pratyantara; the PD level has no verse in Phaladīpikā XX.34-39 — flagged). NOT NULL exactly for path_id P1.';

-- ── Presence checks ────────────────────────────────────────────────────────────
DO $$
DECLARE n integer;
BEGIN
  SELECT count(*) INTO n FROM information_schema.columns
   WHERE table_schema = 'public' AND table_name = 'ka_gochara_relationship_record'
     AND column_name IN ('period_anchor_lord', 'period_anchor_level') AND is_nullable = 'YES' AND data_type = 'text';
  IF n <> 2 THEN
    RAISE EXCEPTION 'migration 1233 post-apply check failed: the two anchor columns are not both present as nullable text';
  END IF;
  SELECT count(*) INTO n FROM pg_constraint c
   WHERE c.conrelid = 'public.ka_gochara_relationship_record'::regclass
     AND c.conname IN ('kgrr_period_anchor_pair_ck', 'kgrr_period_anchor_vocab_ck', 'kgrr_period_anchor_path_ck');
  IF n <> 3 THEN
    RAISE EXCEPTION 'migration 1233 post-apply check failed: expected 3 anchor constraints, found %', n;
  END IF;
  RAISE NOTICE 'migration 1233: presence checks passed';
END;
$$;

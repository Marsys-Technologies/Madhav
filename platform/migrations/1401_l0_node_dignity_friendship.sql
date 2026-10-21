-- 1401_l0_node_dignity_friendship.sql
--
-- SR-DOCTRINE-H (owner surrogate, 2026-10-21): additive L0 correction to bg_dignity_reference and bg_graha_naisargika_friendship.
-- Data-only: upsert of 2 rows of bg_dignity_reference and 5 rows of bg_graha_naisargika_friendship; no DDL, no new object. Transaction
-- ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here). L0 idempotency per CLAUDE.md N.3: INSERT ... ON CONFLICT DO UPDATE on
-- the table's natural key; a second run changes nothing. Migrations 250 and 330 are NOT edited.
--
-- (1) Rahu and Ketu moolatrikona and own signs. L0 held none (migration 250: moolatrikona_sign NULL, own_signs empty). The served BPHS chapter 47
-- verse states them (chunks bphs:PG573:C2 to bphs:PG574:C1, verses 34-39 and a half as served): "The Moola trikonas of Rahu and Ketu are Gemini and
-- Sagittarius respectively. The own signs of Rahu and Ketu are Aquarius and Scorpio in that order." So Rahu: moolatrikona Gemini, own Aquarius;
-- Ketu: moolatrikona Sagittarius, own Scorpio. The verse gives signs only, so moolatrikona_from and moolatrikona_to stay NULL (no degree range is
-- invented, B.10). The same passage records a minority view, "Some learneds have expressed the view that Virgo is the own sign of Rahu and Pisces
-- is the own sign of Ketu": it is NOT stored in own_signs (the ruling leaves it an open L0 decision); it is disclosed in the row notes. Exaltation,
-- debilitation and variant_traditions are untouched.
--
-- (2) Five node-friendship pairs. The translator note under BPHS 3.55 (chunk bphs:PG40:C1, commentary tier [C]) states: "Rahu: The Sun, Moon and
-- Mars are his enemies. Jupiter, Venus and Saturn are his friends. Mercury is his neutral. Ketu: The luminaries are his enemies. Mars, Venus and
-- Saturn are his friends, while Mercury and Jupiter are his neutrals." L0 (cited to an unlocated "UK Ch.4" schema) disagreed on exactly five pairs;
-- a served source states each, so each is corrected to the served relation with that citation: Rahu to Mercury friend -> neutral; Rahu to Mars
-- neutral -> enemy; Rahu to Jupiter neutral -> friend; Ketu to Sun neutral -> enemy; Ketu to Moon neutral -> enemy. The other node rows already
-- agree with the note and are left as they are. Rahu to Ketu and Ketu to Rahu (enemy) and every planet-to-node row are not stated by that note and
-- are not touched.
--
-- (3) Saturn combustion: NO change here. L1 stays at 15 degrees (SR-Q6-L1); the BPHS translator table reads 16 only through an OCR-ambiguous scan
-- and is recorded as a discrepancy for the L0 owner in the pull request, not in this migration.
--
-- GUARD (never a silent no-op). Before writing, the migration requires the 250 rows to be present in exactly the shape it corrects: Rahu and Ketu
-- with the 250 exaltation/debilitation signs and no moolatrikona sign and an empty own_signs (or already the 1401 values, for a replay), and each
-- of the five friendship pairs holding either its 250 relation or its 1401 relation. Anything else RAISES by name and changes nothing. After the
-- writes, the rows are re-read and must equal the 1401 values, and the table sizes must be unchanged (9 and 72).
--
-- WRITER COUPLING. brahmagyan/l0_dignity_reference.py and pipeline/orchestrator/writers/bg_dignity_reference.py hold the same values, so a
-- writer rebuild writes the same rows (a migration alone would be undone by the next rebuild). A static test pins the SQL below to those seeds.

DO $guard$
DECLARE
  n_dig INT;
  n_fr INT;
  n_old_dig INT;
  n_fr_ok INT;
BEGIN
  SELECT COUNT(*) INTO n_dig FROM bg_dignity_reference;
  SELECT COUNT(*) INTO n_fr FROM bg_graha_naisargika_friendship;
  IF n_dig <> 9 THEN
    RAISE EXCEPTION 'migration 1401 refuses: bg_dignity_reference has % rows, expected 9', n_dig;
  END IF;
  IF n_fr <> 72 THEN
    RAISE EXCEPTION 'migration 1401 refuses: bg_graha_naisargika_friendship has % rows, expected 72', n_fr;
  END IF;
  SELECT COUNT(*) INTO n_old_dig FROM bg_dignity_reference
   WHERE (graha = 'Rahu' AND exaltation_sign = 'Taurus' AND debilitation_sign = 'Scorpio'
          AND ((moolatrikona_sign IS NULL AND COALESCE(own_signs, ARRAY[]::TEXT[]) = ARRAY[]::TEXT[])
               OR (moolatrikona_sign = 'Gemini' AND own_signs = ARRAY['Aquarius']::TEXT[])))
      OR (graha = 'Ketu' AND exaltation_sign = 'Scorpio' AND debilitation_sign = 'Taurus'
          AND ((moolatrikona_sign IS NULL AND COALESCE(own_signs, ARRAY[]::TEXT[]) = ARRAY[]::TEXT[])
               OR (moolatrikona_sign = 'Sagittarius' AND own_signs = ARRAY['Scorpio']::TEXT[])));
  IF n_old_dig <> 2 THEN
    RAISE EXCEPTION 'migration 1401 refuses: Rahu/Ketu bg_dignity_reference rows are not in the migration-250 or migration-1401 shape (% of 2 matched)', n_old_dig;
  END IF;
  SELECT COUNT(*) INTO n_fr_ok FROM bg_graha_naisargika_friendship
   WHERE ((graha = 'Rahu' AND other_graha = 'Mercury' AND relation = 'friend') OR (graha = 'Rahu' AND other_graha = 'Mars' AND relation = 'neutral') OR (graha = 'Rahu' AND other_graha = 'Jupiter' AND relation = 'neutral') OR (graha = 'Ketu' AND other_graha = 'Sun' AND relation = 'neutral') OR (graha = 'Ketu' AND other_graha = 'Moon' AND relation = 'neutral'))
      OR ((graha = 'Rahu' AND other_graha = 'Mercury' AND relation = 'neutral') OR (graha = 'Rahu' AND other_graha = 'Mars' AND relation = 'enemy') OR (graha = 'Rahu' AND other_graha = 'Jupiter' AND relation = 'friend') OR (graha = 'Ketu' AND other_graha = 'Sun' AND relation = 'enemy') OR (graha = 'Ketu' AND other_graha = 'Moon' AND relation = 'enemy'));
  IF n_fr_ok <> 5 THEN
    RAISE EXCEPTION 'migration 1401 refuses: the five node-friendship pairs are not in the migration-250 or migration-1401 shape (% of 5 matched)', n_fr_ok;
  END IF;
END
$guard$;

INSERT INTO bg_dignity_reference
    (graha, moolatrikona_sign, moolatrikona_from, moolatrikona_to, own_signs, classical_citation, notes)
VALUES
    ('Rahu',
     'Gemini', NULL, NULL,
     ARRAY['Aquarius']::TEXT[],
     'BPHS Ch.3 (Santanam); Phaladeepika Ch.1; Saravali — Parashari consensus: Taurus. Moolatrikona and own signs: BPHS Ch.47 (verses 34-39½ as served), chunks bphs:PG573:C2 to bphs:PG574:C1, verse text: “The Moola trikonas of Rahu and Ketu are Gemini and Sagittarius respectively. The own signs of Rahu and Ketu are Aquarius and Scorpio in that order.” (SR-DOCTRINE-H, migration 1401)',
     'Taurus exaltation per Parashari mainstream (BPHS/Phaladeepika/Saravali/JH/PL); Gemini is a minority Kerala school position. Moolatrikona Gemini and own sign Aquarius per BPHS Ch.47; the verse names signs only, so no degree range is stored (moolatrikona_from and moolatrikona_to are NULL). Minority reading, not stored in own_signs and unresolved: “Some learneds have expressed the view that Virgo is the own sign of Rahu and Pisces is the own sign of Ketu.” (bphs:PG573:C2 to bphs:PG574:C1)'),
    ('Ketu',
     'Sagittarius', NULL, NULL,
     ARRAY['Scorpio']::TEXT[],
     'BPHS Ch.3 (Santanam); Phaladeepika Ch.1; Saravali — reverse of Rahu. Moolatrikona and own signs: BPHS Ch.47 (verses 34-39½ as served), chunks bphs:PG573:C2 to bphs:PG574:C1, verse text: “The Moola trikonas of Rahu and Ketu are Gemini and Sagittarius respectively. The own signs of Rahu and Ketu are Aquarius and Scorpio in that order.” (SR-DOCTRINE-H, migration 1401)',
     'Scorpio exaltation per Parashari mainstream; Sagittarius is a minority Kerala school position. Moolatrikona Sagittarius and own sign Scorpio per BPHS Ch.47; the verse names signs only, so no degree range is stored (moolatrikona_from and moolatrikona_to are NULL). Minority reading, not stored in own_signs and unresolved: “Some learneds have expressed the view that Virgo is the own sign of Rahu and Pisces is the own sign of Ketu.” (bphs:PG573:C2 to bphs:PG574:C1)')
ON CONFLICT (graha) DO UPDATE SET
    moolatrikona_sign  = EXCLUDED.moolatrikona_sign,
    moolatrikona_from  = EXCLUDED.moolatrikona_from,
    moolatrikona_to    = EXCLUDED.moolatrikona_to,
    own_signs          = EXCLUDED.own_signs,
    classical_citation = EXCLUDED.classical_citation,
    notes              = EXCLUDED.notes;

INSERT INTO bg_graha_naisargika_friendship (graha, other_graha, relation, classical_citation)
VALUES
    ('Rahu', 'Mercury', 'neutral',
     'BPHS 3.55 translator note [C], chunk bphs:PG40:C1: “Rahu: The Sun, Moon and Mars are his enemies. Jupiter, Venus and Saturn are his friends. Mercury is his neutral.” (SR-DOCTRINE-H)'),
    ('Rahu', 'Mars', 'enemy',
     'BPHS 3.55 translator note [C], chunk bphs:PG40:C1: “Rahu: The Sun, Moon and Mars are his enemies. Jupiter, Venus and Saturn are his friends. Mercury is his neutral.” (SR-DOCTRINE-H)'),
    ('Rahu', 'Jupiter', 'friend',
     'BPHS 3.55 translator note [C], chunk bphs:PG40:C1: “Rahu: The Sun, Moon and Mars are his enemies. Jupiter, Venus and Saturn are his friends. Mercury is his neutral.” (SR-DOCTRINE-H)'),
    ('Ketu', 'Sun', 'enemy',
     'BPHS 3.55 translator note [C], chunk bphs:PG40:C1: “Ketu: The luminaries are his enemies. Mars, Venus and Saturn are his friends, while Mercury and Jupiter are his neutrals.” (SR-DOCTRINE-H)'),
    ('Ketu', 'Moon', 'enemy',
     'BPHS 3.55 translator note [C], chunk bphs:PG40:C1: “Ketu: The luminaries are his enemies. Mars, Venus and Saturn are his friends, while Mercury and Jupiter are his neutrals.” (SR-DOCTRINE-H)')
ON CONFLICT (graha, other_graha) DO UPDATE SET
    relation           = EXCLUDED.relation,
    classical_citation = EXCLUDED.classical_citation;

DO $verify$
DECLARE
  n_dig INT;
  n_fr INT;
  n_new_dig INT;
  n_new_fr INT;
BEGIN
  SELECT COUNT(*) INTO n_dig FROM bg_dignity_reference;
  SELECT COUNT(*) INTO n_fr FROM bg_graha_naisargika_friendship;
  IF n_dig <> 9 OR n_fr <> 72 THEN
    RAISE EXCEPTION 'migration 1401 post-check: table sizes changed (bg_dignity_reference %, bg_graha_naisargika_friendship %)', n_dig, n_fr;
  END IF;
  SELECT COUNT(*) INTO n_new_dig FROM bg_dignity_reference
   WHERE moolatrikona_from IS NULL AND moolatrikona_to IS NULL
     AND ((graha = 'Rahu' AND moolatrikona_sign = 'Gemini' AND own_signs = ARRAY['Aquarius']::TEXT[])
       OR (graha = 'Ketu' AND moolatrikona_sign = 'Sagittarius' AND own_signs = ARRAY['Scorpio']::TEXT[]));
  IF n_new_dig <> 2 THEN
    RAISE EXCEPTION 'migration 1401 post-check: Rahu/Ketu rows do not read back as written (% of 2)', n_new_dig;
  END IF;
  SELECT COUNT(*) INTO n_new_fr FROM bg_graha_naisargika_friendship
   WHERE (graha = 'Rahu' AND other_graha = 'Mercury' AND relation = 'neutral') OR (graha = 'Rahu' AND other_graha = 'Mars' AND relation = 'enemy') OR (graha = 'Rahu' AND other_graha = 'Jupiter' AND relation = 'friend') OR (graha = 'Ketu' AND other_graha = 'Sun' AND relation = 'enemy') OR (graha = 'Ketu' AND other_graha = 'Moon' AND relation = 'enemy');
  IF n_new_fr <> 5 THEN
    RAISE EXCEPTION 'migration 1401 post-check: the five node-friendship pairs do not read back as written (% of 5)', n_new_fr;
  END IF;
END
$verify$;

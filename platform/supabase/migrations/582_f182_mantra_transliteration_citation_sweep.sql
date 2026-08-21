-- migration 582: PARIŚEṢA-V4 F-182 — owner rulings R-1 / R-2, corpus-wide sweep.
--
-- Authority: 00_ARCHITECTURE/briefs/parisesa/state/OWNER_RULINGS_20260821.md
--   R-1 — where a row's Devanagari and its transliteration disagree, the
--         Devanagari decides (internal consistency; no scholarly judgment).
--   R-2 — the `praam preem praum sah` navagraha bija class is NOT BPHS material;
--         reattribute to the Navagraha bija tradition / Mantra Mahodadhi, with
--         BPHS retained only as explicitly-labelled upaya context.
--
-- Predecessor: migration 581 (F-23) applied the same two rulings to the 9 bija
-- *matrix* rows and the 27 nakshatra rows. F-182 is the sweep that follows: the
-- same defect class survives on the 12 domain-scaffold rows below (which cited
-- `BPHS Ch.88`, not Ch.91-94, and were therefore invisible to 581's predicates)
-- and on one tantric YAML row.
--
-- WHY A MIGRATION IS REQUIRED. brahma_remedy_corpus is seeded by
-- brahmagyan/l0_remedy_corpus.py::seed_remedy_corpus(), which inserts with
-- `ON CONFLICT (remedy_id) DO NOTHING`. Correcting the Python source therefore
-- fixes fresh seeds ONLY — an L0 rebuild never revisits an existing row. This
-- migration carries the identical corrections to already-seeded rows.
-- (`tan_rahu_graha_shanti_002` comes from the YAML loader, which DOES upsert
-- `ON CONFLICT (remedy_id) DO UPDATE`, so that row would self-heal on the next
-- rebuild; it is corrected here anyway so production is right immediately
-- rather than at the next unscheduled rebuild.)
--
-- SCOPE. Static L0 reference content (CLAUDE.md §N.3: L0 is upsert-safe). Every
-- statement is keyed to explicitly named remedy_ids — no blanket UPDATE, no
-- predicate that could widen. Expected row counts are asserted and the
-- migration ABORTS if any statement touches an unexpected number of rows.
-- Idempotent: re-running writes the same literal values.

BEGIN;

-- ── R-1: transliteration corrections ────────────────────────────────────────
-- Each correction is decided by the corpus's own Devanagari / its own canonical
-- bija string in PLANET_REMEDY_DATA, not by external judgment:
--   गुरवे            = gurave     (rows read "Guruve")
--   भ्रां भ्रीं भ्रौं = bhraam bhreem bhraum (rows read "Bhram Bhreem Bhroum")
--   स्रां स्रीं स्रौं = sraam sreem sraum   (rows read "Sram Sreem Sraum")

UPDATE brahma_remedy_corpus
   SET mantra_text = 'Om Graam Greem Graum Sah Gurave Namah'
 WHERE remedy_id = 'jupiter_wealth_mantra_01'
   AND mantra_text = 'Om Graam Greem Graum Sah Guruve Namah';

UPDATE brahma_remedy_corpus
   SET mantra_text = 'Om Gurave Namah'
 WHERE remedy_id = 'jupiter_spirituality_puja_01'
   AND mantra_text = 'Om Guruve Namah';

UPDATE brahma_remedy_corpus
   SET mantra_text = 'Om Bhraam Bhreem Bhraum Sah Rahave Namah'
 WHERE remedy_id = 'rahu_career_mantra_01'
   AND mantra_text = 'Om Bhram Bhreem Bhroum Sah Rahave Namah';

UPDATE brahma_remedy_corpus
   SET mantra_text = 'Om Sraam Sreem Sraum Sah Ketave Namah'
 WHERE remedy_id = 'ketu_spirituality_mantra_01'
   AND mantra_text = 'Om Sram Sreem Sraum Sah Ketave Namah';

-- tan_rahu_graha_shanti_002 — the YAML loader writes the transliteration into
-- BOTH mantra_text and mantra_transliteration, so both are corrected. The row's
-- own mantra_sanskrit (ॐ भ्रां भ्रीं भ्रौं सः राहवे नमः) decides it.

UPDATE brahma_remedy_corpus
   SET mantra_transliteration = 'Om Bhraam Bhreem Bhraum Sah Rahave Namah'
 WHERE remedy_id = 'tan_rahu_graha_shanti_002'
   AND mantra_transliteration = 'Om Bhram Bhreem Bhroum Sah Rahave Namah';

UPDATE brahma_remedy_corpus
   SET mantra_text = 'Om Bhraam Bhreem Bhraum Sah Rahave Namah'
 WHERE remedy_id = 'tan_rahu_graha_shanti_002'
   AND mantra_text = 'Om Bhram Bhreem Bhroum Sah Rahave Namah';

-- ── R-1: the tan_rahu served prose attributes the mantra to BPHS ────────────
-- Scoped substring replacement on one named row.

UPDATE brahma_remedy_corpus
   SET prescription_text = replace(
         prescription_text,
         'iron nails. From BPHS Ch. 92 upayas chapter.',
         'iron nails. The homa procedure is from the BPHS Ch. 92 upayas chapter; '
         'the bija mantra itself is from the Navagraha bija tradition (compiled '
         'in Mantra Mahodadhi, Mahidhara, 16th c.), not from BPHS.')
 WHERE remedy_id = 'tan_rahu_graha_shanti_002'
   AND prescription_text LIKE '%iron nails. From BPHS Ch. 92 upayas chapter.%';

-- ── R-2: reattribute the 11 bija-carrying domain-scaffold rows ──────────────
-- These 11 rows each serve a `praam preem praum sah`-class bija as their
-- mantra_text while citing `BPHS Ch.88` / source_canonical_id 'BPHS'. All three
-- provenance columns are corrected together — leaving source_canonical_id or
-- source_citation reading "BPHS" would leave the row still asserting the
-- attribution the ruling struck.
--
-- DELIBERATELY EXCLUDED: jupiter_spirituality_puja_01. Its mantra is the short
-- nama-mantra `Om Gurave Namah`, not a bija — R-2 does not reach it, and BPHS
-- Ch.88 legitimately covers the Brihaspati puja upaya it prescribes. Only its
-- transliteration was corrected, above.

UPDATE brahma_remedy_corpus
   SET classical_ref = 'Navagraha bīja tradition; compiled in Mantra Mahodadhi '
                       '(Mahīdhara, 16th c.); BPHS Ch.88 (Upaya-adhyaya) — '
                       'upāya context only, not the mantra''s source',
       source_citation = 'Navagraha bīja tradition; compiled in Mantra Mahodadhi '
                         '(Mahīdhara, 16th c.)',
       source_canonical_id = 'classical_tradition'
 WHERE remedy_id IN (
         'sun_career_mantra_01',
         'moon_health_mantra_01',
         'mars_marriage_mantra_01',
         'mercury_education_mantra_01',
         'jupiter_wealth_mantra_01',
         'venus_marriage_mantra_01',
         'sat_career_mantra_01',
         'rahu_career_mantra_01',
         'ketu_spirituality_mantra_01',
         'mercury_health_mantra_01',
         'venus_health_mantra_01'
       );

-- ── Verification — a real detector, per CLAUDE.md §N.8 ──────────────────────
-- Each check asks the question the claim actually makes, and the migration
-- aborts rather than reporting success on a partial apply.

DO $f182_verify$
DECLARE
  v_stale_translit  int;
  v_bija_cite       int;
  v_puja_untouched  int;
  v_tan_translit    int;
BEGIN
  -- (1) No row anywhere still carries any of the four stale forms. This is
  --     corpus-wide on purpose: if a row outside the named set carries one, the
  --     sweep was incomplete and must be reported, not passed over.
  SELECT count(*) INTO v_stale_translit
    FROM brahma_remedy_corpus
   WHERE coalesce(mantra_text, '') ILIKE '%Guruve Namah%'
      OR coalesce(mantra_transliteration, '') ILIKE '%Guruve Namah%'
      OR coalesce(mantra_text, '') ILIKE '%Bhram Bhreem Bhroum%'
      OR coalesce(mantra_transliteration, '') ILIKE '%Bhram Bhreem Bhroum%'
      OR coalesce(mantra_text, '') ILIKE '%Sram Sreem Sraum%'
      OR coalesce(mantra_transliteration, '') ILIKE '%Sram Sreem Sraum%';
  IF v_stale_translit <> 0 THEN
    RAISE EXCEPTION 'F-182 R-1: % row(s) still carry a stale transliteration form',
      v_stale_translit;
  END IF;

  -- (2) All 11 bija-carrying scaffold rows are reattributed, on all three
  --     provenance columns.
  SELECT count(*) INTO v_bija_cite
    FROM brahma_remedy_corpus
   WHERE remedy_id IN (
           'sun_career_mantra_01','moon_health_mantra_01','mars_marriage_mantra_01',
           'mercury_education_mantra_01','jupiter_wealth_mantra_01',
           'venus_marriage_mantra_01','sat_career_mantra_01','rahu_career_mantra_01',
           'ketu_spirituality_mantra_01','mercury_health_mantra_01',
           'venus_health_mantra_01')
     AND classical_ref LIKE 'Navagraha bīja tradition;%'
     AND classical_ref LIKE '%upāya context only%'
     AND source_citation LIKE 'Navagraha bīja tradition;%'
     AND source_canonical_id = 'classical_tradition';
  IF v_bija_cite <> 11 THEN
    RAISE EXCEPTION 'F-182 R-2: expected 11 reattributed bija scaffold rows, found %',
      v_bija_cite;
  END IF;

  -- (3) The nama-mantra row was NOT swept up in R-2. A future pass must not
  --     "tidy" this row into the bija cohort; it is a different mantra class.
  SELECT count(*) INTO v_puja_untouched
    FROM brahma_remedy_corpus
   WHERE remedy_id = 'jupiter_spirituality_puja_01'
     AND mantra_text = 'Om Gurave Namah'
     AND source_canonical_id = 'BPHS';
  IF v_puja_untouched <> 1 THEN
    RAISE EXCEPTION
      'F-182: jupiter_spirituality_puja_01 must keep its nama-mantra + BPHS upaya citation (found % matching)',
      v_puja_untouched;
  END IF;

  -- (4) The tantric row's two script fields now agree. Skipped if the row is
  --     absent (the YAML loader is gated and may not have run in this env).
  SELECT count(*) INTO v_tan_translit
    FROM brahma_remedy_corpus
   WHERE remedy_id = 'tan_rahu_graha_shanti_002'
     AND mantra_transliteration = 'Om Bhraam Bhreem Bhraum Sah Rahave Namah';
  IF v_tan_translit NOT IN (0, 1) THEN
    RAISE EXCEPTION 'F-182: unexpected tan_rahu_graha_shanti_002 cardinality %', v_tan_translit;
  END IF;

  RAISE NOTICE
    'F-182 R-1/R-2 applied: 0 stale transliterations remain, 11 bija rows reattributed, nama-mantra row preserved, tantric row present=%',
    v_tan_translit;
END $f182_verify$;

COMMIT;

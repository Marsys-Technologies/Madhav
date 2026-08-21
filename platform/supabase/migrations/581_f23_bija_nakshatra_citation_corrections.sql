-- migration 581: PARIŚEṢA-V4 F-23 — owner rulings R-1 / R-2 / R-3.
--
-- Authority: 00_ARCHITECTURE/briefs/parisesa/OWNER_RULINGS_20260821.md
-- Investigation: 00_ARCHITECTURE/briefs/parisesa/state/F23_PROVISIONAL_RULING_20260821.md
--
-- WHY A MIGRATION IS REQUIRED. brahma_remedy_corpus is seeded by
-- brahmagyan/l0_remedy_corpus.py::seed_remedy_corpus(), which inserts with
-- `ON CONFLICT (remedy_id) DO NOTHING`. Correcting the Python source therefore
-- fixes fresh seeds ONLY — existing rows are never revisited by a rebuild. This
-- migration carries the same corrections to already-seeded rows. The two must
-- agree; the guards in
-- platform/python-sidecar/tests/l0/test_f23_mantra_script_and_citation.py assert
-- the Python side, and the verification block at the foot of this file asserts
-- the DB side.
--
-- SCOPE. Static L0 reference content (CLAUDE.md §N.3: L0 is upsert-safe). Every
-- statement is keyed to explicitly named remedy_ids — no blanket UPDATE, no
-- predicate that could widen. Expected row counts are asserted, and the
-- migration ABORTS if any statement touches an unexpected number of rows.
-- Idempotent: re-running writes the same literal values.
--
-- R-1 — saturn_matrix_mantra stored Devanagari ॐ प्रां प्रीं प्रौं सः शनैश्चराय नमः
--       (śanaiścarāya) against transliteration "Om Praam Preem Praum Sah Shanaye
--       Namah" (śanaye) — a different, shorter mantra. The Devanagari is correct.
-- R-2 — the 9 bīja-matrix rows attributed the `prāṃ prīṃ prauṃ saḥ` mantra class
--       to BPHS Ch.91-94. Ruled incorrect-as-stated: that class belongs to the
--       tantric/āgamic layer (Mantra Mahodadhi, Navagraha Stotra tradition).
--       BPHS is retained as upāya context, explicitly labelled.
-- R-3 — the 27 nakshatra rows cited BPHS Ch.94 in a way that implied BPHS
--       supplies the mantra text. It supplies the devatā only; the served
--       `Om <devatā> Namah` string is a constructed nāma-mantra. The mantra text
--       itself is NOT changed — only what the citation claims.
--
-- Rollback: see 00_ARCHITECTURE/briefs/parisesa/OWNER_RULINGS_20260821.md; the
-- pre-image values are recorded in the PR body for this migration. Reverting is
-- a matter of restoring the prior literals with the same remedy_id keying.

BEGIN;

-- ── R-1 + R-4 column contract: mantra_transliteration = IAST ────────────────
-- Applies to the 9 bīja mantra rows AND their 18 sibling rows (japa + yantra),
-- which carry the identical romanised bīja from the same source table and
-- therefore carried the identical Saturn defect. The F-23 reproducer counted
-- remedy_type='mantra' only, so the siblings were not visible to it. 27 rows.

WITH iast(remedy_key, translit) AS (
  VALUES
    ('sun',     'oṃ hrāṃ hrīṃ hrauṃ saḥ sūryāya namaḥ'),
    ('moon',    'oṃ śrāṃ śrīṃ śrauṃ saḥ candrāya namaḥ'),
    ('mars',    'oṃ krāṃ krīṃ krauṃ saḥ bhaumāya namaḥ'),
    ('mercury', 'oṃ brāṃ brīṃ brauṃ saḥ budhāya namaḥ'),
    ('jupiter', 'oṃ grāṃ grīṃ grauṃ saḥ gurave namaḥ'),
    ('venus',   'oṃ drāṃ drīṃ drauṃ saḥ śukrāya namaḥ'),
    ('saturn',  'oṃ prāṃ prīṃ prauṃ saḥ śanaiścarāya namaḥ'),
    ('rahu',    'oṃ bhrāṃ bhrīṃ bhrauṃ saḥ rāhave namaḥ'),
    ('ketu',    'oṃ srāṃ srīṃ srauṃ saḥ ketave namaḥ')
)
UPDATE brahma_remedy_corpus c
   SET mantra_transliteration = i.translit
  FROM iast i
 WHERE c.remedy_id IN (
         i.remedy_key || '_matrix_mantra',
         i.remedy_key || '_matrix_japa',
         i.remedy_key || '_matrix_yantra'
       );

-- ── R-1: the same śanaye contamination in served prose ──────────────────────
-- prescription_text on these four rows interpolates the same romanised bīja.
-- Scoped substring replacement on named rows only.

UPDATE brahma_remedy_corpus
   SET prescription_text = replace(
         prescription_text, 'Sah Shanaye Namah', 'Sah Shanaischaraya Namah')
 WHERE remedy_id IN (
         'saturn_matrix_mantra',
         'saturn_matrix_japa',
         'saturn_matrix_yantra',
         'yantra_shani_spec_maharnava'
       )
   AND prescription_text LIKE '%Sah Shanaye Namah%';

-- ── R-2: reattribute the 9 bīja mantra rows ─────────────────────────────────

UPDATE brahma_remedy_corpus
   SET classical_ref = 'Navagraha bīja tradition; compiled in Mantra Mahodadhi '
                       '(Mahīdhara, 16th c.); BPHS Ch.91-94 (Upaya-adhyaya) — '
                       'upāya context only, not the mantra''s source',
       source_citation = 'Navagraha bīja tradition; compiled in Mantra Mahodadhi '
                         '(Mahīdhara, 16th c.)',
       source_canonical_id = 'classical_tradition'
 WHERE remedy_id IN (
         'sun_matrix_mantra', 'moon_matrix_mantra', 'mars_matrix_mantra',
         'mercury_matrix_mantra', 'jupiter_matrix_mantra', 'venus_matrix_mantra',
         'saturn_matrix_mantra', 'rahu_matrix_mantra', 'ketu_matrix_mantra'
       );

-- ── R-3: correct what the 27 nakshatra citations claim ──────────────────────
-- The nāma-mantra text in mantra_transliteration is deliberately UNTOUCHED.

UPDATE brahma_remedy_corpus
   SET classical_ref = 'BPHS Ch.94 (devatā attribution); mantra: nāma-mantra '
                       'form (constructed)'
 WHERE remedy_type = 'mantra'
   AND remedy_id LIKE 'nakshatra\_%\_mantra'
   AND classical_ref = 'BPHS Ch.94 (Nakshatra devata table); Deva Keralam';

-- Matching prose fix: the old sentence read "...is prescribed for nakshatra
-- shanti in BPHS Ch.94", which a reader can take as BPHS prescribing this mantra.
UPDATE brahma_remedy_corpus
   SET prescription_text = replace(
         prescription_text,
         ' and is prescribed for nakshatra shanti in BPHS Ch.94.',
         '. Nakshatra shanti is prescribed in BPHS Ch.94, which supplies the '
         'presiding devata; the ''Om <devata> Namah'' recitation form itself is '
         'a constructed nama-mantra, not BPHS text.')
 WHERE remedy_type = 'mantra'
   AND remedy_id LIKE 'nakshatra\_%\_mantra'
   AND prescription_text LIKE '% and is prescribed for nakshatra shanti in BPHS Ch.94.%';

-- ── Verification: assert the post-state, abort the transaction otherwise ────

DO $f23_verify$
DECLARE
  v_bija_iast      int;
  v_sibling_iast   int;
  v_bija_cite      int;
  v_nak_cite       int;
  v_shanaye_left   int;
  v_nak_mantra_kept int;
BEGIN
  SELECT count(*) INTO v_bija_iast
    FROM brahma_remedy_corpus
   WHERE remedy_id LIKE '%\_matrix\_mantra'
     AND mantra_transliteration LIKE 'oṃ %';
  IF v_bija_iast <> 9 THEN
    RAISE EXCEPTION 'F-23 R-1: expected 9 bija mantra rows in IAST, found %', v_bija_iast;
  END IF;

  SELECT count(*) INTO v_sibling_iast
    FROM brahma_remedy_corpus
   WHERE (remedy_id LIKE '%\_matrix\_japa' OR remedy_id LIKE '%\_matrix\_yantra')
     AND mantra_transliteration LIKE 'oṃ %';
  IF v_sibling_iast <> 18 THEN
    RAISE EXCEPTION 'F-23 R-1: expected 18 bija japa+yantra rows in IAST, found %',
      v_sibling_iast;
  END IF;

  SELECT count(*) INTO v_shanaye_left
    FROM brahma_remedy_corpus
   WHERE coalesce(prescription_text, '') ILIKE '%Sah Shanaye Namah%'
      OR coalesce(mantra_transliteration, '') ILIKE '%Shanaye%'
      OR coalesce(mantra_text, '') ILIKE '%Shanaye%';
  IF v_shanaye_left <> 0 THEN
    RAISE EXCEPTION 'F-23 R-1: % rows still carry the stale sanaye bija form', v_shanaye_left;
  END IF;

  SELECT count(*) INTO v_bija_cite
    FROM brahma_remedy_corpus
   WHERE remedy_id LIKE '%\_matrix\_mantra'
     AND classical_ref LIKE 'Navagraha bīja tradition;%'
     AND classical_ref LIKE '%upāya context only%'
     AND source_canonical_id = 'classical_tradition';
  IF v_bija_cite <> 9 THEN
    RAISE EXCEPTION 'F-23 R-2: expected 9 reattributed bija rows, found %', v_bija_cite;
  END IF;

  SELECT count(*) INTO v_nak_cite
    FROM brahma_remedy_corpus
   WHERE remedy_type = 'mantra'
     AND remedy_id LIKE 'nakshatra\_%\_mantra'
     AND classical_ref = 'BPHS Ch.94 (devatā attribution); mantra: nāma-mantra form (constructed)';
  IF v_nak_cite <> 27 THEN
    RAISE EXCEPTION 'F-23 R-3: expected 27 corrected nakshatra citations, found %', v_nak_cite;
  END IF;

  -- R-3 explicitly PRESERVES the served nama-mantra. Guard against a citation
  -- fix that also emptied the mantra it cites.
  SELECT count(*) INTO v_nak_mantra_kept
    FROM brahma_remedy_corpus
   WHERE remedy_type = 'mantra'
     AND remedy_id LIKE 'nakshatra\_%\_mantra'
     AND mantra_transliteration IS NOT NULL
     AND length(trim(mantra_transliteration)) > 0;
  IF v_nak_mantra_kept <> 27 THEN
    RAISE EXCEPTION 'F-23 R-3: nama-mantra text must be retained on all 27 rows, found %',
      v_nak_mantra_kept;
  END IF;

  RAISE NOTICE 'F-23 R-1/R-2/R-3 applied: 27 IAST rows, 9 reattributed bija, 27 corrected nakshatra citations';
END $f23_verify$;

COMMIT;

-- Migration 386: Canonical 12-domain normalization (BA-P3A Step 1, BA_MASTER C15)
-- Resolves 8 divergent domain lists to the canonical 12 life-domains + 'general'.
-- Source of truth: BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md §1.
--
-- Canonical domains (lowercase):
--   career · wealth · relationship · progeny · health · education ·
--   family · residence · travel · spirituality · character · transition · general
--
-- Normalization map (legacy → canonical):
--   financial / finance     → wealth
--   spiritual / dharma      → spirituality
--   psychological / mind    → character
--   children / creativity   → progeny
--   property / residential  → residence
--   foreign                 → travel
--   intellect               → education
--   relational              → relationship
-- UPPERCASE variants (migration 341) → lowercase canonical
--
-- ORDER: DROP old constraints FIRST so legacy values are writable during
-- data normalization, then ADD canonical constraints after all updates.
--
-- NOTE: DO blocks use to_regclass() (null-safe) instead of ::regclass (throws
-- if table absent). The actual table for asset ka_bhavishya_lekha is kala_bhavishya.

-- ── §1. Schema: drop all legacy CHECK constraints BEFORE data updates ─────────
-- This ensures legacy domain values (e.g. 'financial') can be read and the
-- updated canonical values (e.g. 'wealth') pass validation during the UPDATEs.

-- phala_anchors
DO $$ DECLARE v TEXT; BEGIN
  SELECT conname INTO v FROM pg_constraint
  WHERE conrelid = to_regclass('public.phala_anchors') AND contype = 'c'
    AND pg_get_constraintdef(oid) ILIKE '%domain%';
  IF v IS NOT NULL THEN EXECUTE 'ALTER TABLE phala_anchors DROP CONSTRAINT ' || quote_ident(v); END IF;
END $$;

-- phala_phaladesa
DO $$ DECLARE v TEXT; BEGIN
  SELECT conname INTO v FROM pg_constraint
  WHERE conrelid = to_regclass('public.phala_phaladesa') AND contype = 'c'
    AND pg_get_constraintdef(oid) ILIKE '%domain%';
  IF v IS NOT NULL THEN EXECUTE 'ALTER TABLE phala_phaladesa DROP CONSTRAINT ' || quote_ident(v); END IF;
END $$;

-- kala_bhavishya (asset_id ka_bhavishya_lekha; actual table name is kala_bhavishya)
DO $$ DECLARE v TEXT; BEGIN
  SELECT conname INTO v FROM pg_constraint
  WHERE conrelid = to_regclass('public.kala_bhavishya') AND contype = 'c'
    AND pg_get_constraintdef(oid) ILIKE '%domain%';
  IF v IS NOT NULL THEN EXECUTE 'ALTER TABLE kala_bhavishya DROP CONSTRAINT ' || quote_ident(v); END IF;
END $$;

-- school_analysis_runs
DO $$ DECLARE v TEXT; BEGIN
  FOR v IN SELECT conname FROM pg_constraint
    WHERE conrelid = to_regclass('public.school_analysis_runs') AND contype = 'c'
      AND pg_get_constraintdef(oid) ILIKE '%domain%'
  LOOP EXECUTE 'ALTER TABLE school_analysis_runs DROP CONSTRAINT ' || quote_ident(v); END LOOP;
END $$;

-- convergence_scores
DO $$ DECLARE v TEXT; BEGIN
  FOR v IN SELECT conname FROM pg_constraint
    WHERE conrelid = to_regclass('public.convergence_scores') AND contype = 'c'
      AND pg_get_constraintdef(oid) ILIKE '%domain%'
  LOOP EXECUTE 'ALTER TABLE convergence_scores DROP CONSTRAINT ' || quote_ident(v); END LOOP;
END $$;

-- ── §2. Data normalization: bodha_msr_signals.domains_affected_array ──────────
-- TEXT[] column; chain array_replace() for each legacy value.
UPDATE bodha_msr_signals SET domains_affected_array = (
  array_replace(array_replace(array_replace(array_replace(array_replace(
  array_replace(array_replace(array_replace(array_replace(array_replace(
  array_replace(array_replace(
    domains_affected_array,
    'financial',    'wealth'),
    'finance',      'wealth'),
    'spiritual',    'spirituality'),
    'dharma',       'spirituality'),
    'psychological','character'),
    'mind',         'character'),
    'children',     'progeny'),
    'creativity',   'progeny'),
    'intellect',    'education'),
    'property',     'residence'),
    'residential',  'residence'),
    'foreign',      'travel')
)
WHERE domains_affected_array && ARRAY[
  'financial','finance','spiritual','dharma','psychological','mind',
  'children','creativity','intellect','property','residential','foreign'
];

-- ── §3. Data normalization: phala_anchors.domain ─────────────────────────────
UPDATE phala_anchors SET domain = CASE domain
  WHEN 'financial'    THEN 'wealth'
  WHEN 'spiritual'    THEN 'spirituality'
  WHEN 'psychological'THEN 'character'
  ELSE domain
END
WHERE domain IN ('financial','spiritual','psychological');

-- ── §4. Data normalization: phala_phaladesa.domain ───────────────────────────
UPDATE phala_phaladesa SET domain = CASE domain
  WHEN 'financial'    THEN 'wealth'
  WHEN 'spiritual'    THEN 'spirituality'
  WHEN 'psychological'THEN 'character'
  ELSE domain
END
WHERE domain IN ('financial','spiritual','psychological');

-- ── §5. Data normalization: kala_bhavishya.domain ────────────────────────────
-- (asset_id ka_bhavishya_lekha; the physical table is kala_bhavishya)
UPDATE kala_bhavishya SET domain = CASE domain
  WHEN 'finance'    THEN 'wealth'
  WHEN 'spiritual'  THEN 'spirituality'
  ELSE domain
END
WHERE domain IN ('finance','spiritual');

-- ── §6. Data normalization: phala_sankrama.target_domain ─────────────────────
UPDATE phala_sankrama SET target_domain = CASE target_domain
  WHEN 'financial'    THEN 'wealth'
  WHEN 'spiritual'    THEN 'spirituality'
  WHEN 'psychological'THEN 'character'
  ELSE target_domain
END
WHERE target_domain IN ('financial','spiritual','psychological');

-- ── §7. Data normalization: school_analysis_runs / convergence_scores ────────
UPDATE school_analysis_runs SET domain = LOWER(domain)
WHERE domain ~ '[A-Z]';

UPDATE convergence_scores SET domain = LOWER(domain)
WHERE domain ~ '[A-Z]';

UPDATE school_analysis_runs SET domain = CASE domain
  WHEN 'spiritual'    THEN 'spirituality'
  WHEN 'psychological'THEN 'character'
  ELSE domain
END
WHERE domain IN ('spiritual','psychological');

UPDATE convergence_scores SET domain = CASE domain
  WHEN 'spiritual'    THEN 'spirituality'
  WHEN 'psychological'THEN 'character'
  ELSE domain
END
WHERE domain IN ('spiritual','psychological');

-- ── §8. Schema: add canonical CHECK constraints AFTER data is clean ───────────

ALTER TABLE phala_anchors
  ADD CONSTRAINT phala_anchors_domain_canonical
  CHECK (domain IN ('career','wealth','relationship','progeny','health','education',
                    'family','residence','travel','spirituality','character','transition','general'));

ALTER TABLE phala_phaladesa
  ADD CONSTRAINT phala_phaladesa_domain_canonical
  CHECK (domain IN ('career','wealth','relationship','progeny','health','education',
                    'family','residence','travel','spirituality','character','transition','general'));

ALTER TABLE kala_bhavishya
  ADD CONSTRAINT kala_bhavishya_domain_canonical
  CHECK (domain IN ('career','wealth','relationship','progeny','health','education',
                    'family','residence','travel','spirituality','character','transition','general'));

ALTER TABLE school_analysis_runs
  ADD CONSTRAINT school_analysis_runs_domain_canonical
  CHECK (domain IN ('career','wealth','relationship','progeny','health','education',
                    'family','residence','travel','spirituality','character','transition','general'));

ALTER TABLE convergence_scores
  ADD CONSTRAINT convergence_scores_domain_canonical
  CHECK (domain IN ('career','wealth','relationship','progeny','health','education',
                    'family','residence','travel','spirituality','character','transition','general'));

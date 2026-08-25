-- Migration 609: append-only corrected bg_reference and bg_texts digest specs.
--
-- Migration 600 is already committed evidence and remains byte-identical. Its
-- current specs are retained as retired predecessors so any provenance receipt
-- that references them remains resolvable. Every accepted SHA is coupled to
-- its exact JSONB content; a label alone is never trusted.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

DO $$
DECLARE
  old_reference_sha constant text :=
    '7f29bb1a2a6082096fd365bde66b817ca82c7cf2e56d40ee16e30ebdd4466fb3';
  new_reference_sha constant text :=
    '89e71583339838a72bde5ead48dd0a901b144ff1493d8c825b60ecbf4f39524f';
  old_texts_sha constant text :=
    'c29c5ed004e16cf59f051882c805e458d0070619181829d4e989d6b213c80931';
  new_texts_sha constant text :=
    '10416cda800b6bd6d606f8daee76b06928071d66b09ff733a3b48ebc734c02f6';
  old_reference_spec constant jsonb :=
    '{"components":[{"key_columns":["planet_id"],"name":"reference_planets","relation":"reference_planets","value_columns":["planet_id","canonical_name_en","canonical_name_sa","exaltation_sign","exaltation_degree","debilitation_sign","mooltrikona_sign","own_signs","natural_benefic","karak_domains","dasha_years","source_citation"]},{"key_columns":["nakshatra_id"],"name":"reference_nakshatras","relation":"reference_nakshatras","value_columns":["nakshatra_id","canonical_name_en","canonical_name_sa","lord","deity","nature","guna","start_degree","end_degree","pada_lords","body_part","source_citation"]},{"key_columns":["sign_id"],"name":"reference_signs","relation":"reference_signs","value_columns":["sign_id","canonical_name_en","canonical_name_sa","lord","element","modality","natural_house","is_odd","is_biped","significations","source_citation"]},{"key_columns":["planet_id","aspect_house"],"name":"reference_aspects","relation":"reference_aspects","value_columns":["planet_id","aspect_house","aspect_strength","strength_value","is_special","notes","source_citation"]},{"key_columns":["varga_id"],"name":"reference_vargas","relation":"reference_vargas","value_columns":["varga_id","varga_number","canonical_name_en","canonical_name_sa","division_count","primary_signification","secondary_signification","source_citation"]},{"key_columns":["house_num"],"name":"reference_houses","relation":"reference_houses","value_columns":["house_num","name_sa","name_en","category","natural_significations","karakas","classical_doctrine_jsonb","source_citation"]},{"key_columns":["strength_id"],"name":"reference_strength_systems","relation":"reference_strength_systems","value_columns":["strength_id","name_sa","name_en","category","formula_text","max_value","units","classical_interpretation","source_citation"]},{"key_columns":["karaka_id"],"name":"reference_karakas","relation":"reference_karakas","value_columns":["karaka_id","name_sa","name_en","karaka_type","applies_to","classical_significations","source_citation"]},{"key_columns":["upagraha_id"],"name":"reference_upagrahas","relation":"reference_upagrahas","value_columns":["upagraha_id","name_sa","name_en","parent_planet","computation_method","significations","source_citation"]},{"key_columns":["constant_id"],"name":"reference_constants","relation":"reference_constants","value_columns":["constant_id","name","value_numeric","value_text","unit","category","source_citation","classical_context"]},{"key_columns":["canonical_id"],"name":"reference_topic_tags","relation":"reference_topic_tags","value_columns":["canonical_id","name","category","description","example_chunks"]},{"key_columns":["term_id"],"name":"reference_glossary","relation":"reference_glossary","value_columns":["term_id","term_sa","term_en","definition","category","classical_citation","related_concepts"]}],"version":"nirmana-output-digest-spec-v1"}'::jsonb;
  new_reference_spec constant jsonb :=
    '{"components":[{"key_columns":["planet_id"],"name":"reference_planets","relation":"reference_planets","value_columns":["planet_id","canonical_name_en","canonical_name_sa","exaltation_sign","exaltation_degree","debilitation_sign","mooltrikona_sign","own_signs","natural_benefic","karak_domains","dasha_years","source_citation"]},{"key_columns":["sign_id"],"name":"reference_signs","relation":"reference_signs","value_columns":["sign_id","canonical_name_en","canonical_name_sa","lord","element","modality","natural_house","is_odd","is_biped","significations","source_citation"]},{"key_columns":["planet_id","aspect_house"],"name":"reference_aspects","relation":"reference_aspects","value_columns":["planet_id","aspect_house","aspect_strength","strength_value","is_special","notes","source_citation"]},{"key_columns":["varga_id"],"name":"reference_vargas","relation":"reference_vargas","value_columns":["varga_id","varga_number","canonical_name_en","canonical_name_sa","division_count","primary_signification","secondary_signification","source_citation"]},{"key_columns":["house_num"],"name":"reference_houses","relation":"reference_houses","value_columns":["house_num","name_sa","name_en","category","natural_significations","karakas","classical_doctrine_jsonb","source_citation"]},{"key_columns":["strength_id"],"name":"reference_strength_systems","relation":"reference_strength_systems","value_columns":["strength_id","name_sa","name_en","category","formula_text","max_value","units","classical_interpretation","source_citation"]},{"key_columns":["karaka_id"],"name":"reference_karakas","relation":"reference_karakas","value_columns":["karaka_id","name_sa","name_en","karaka_type","applies_to","classical_significations","source_citation"]},{"key_columns":["upagraha_id"],"name":"reference_upagrahas","relation":"reference_upagrahas","value_columns":["upagraha_id","name_sa","name_en","parent_planet","computation_method","significations","source_citation"]},{"key_columns":["constant_id"],"name":"reference_constants","relation":"reference_constants","value_columns":["constant_id","name","value_numeric","value_text","unit","category","source_citation","classical_context"]},{"key_columns":["canonical_id"],"name":"reference_topic_tags","relation":"reference_topic_tags","value_columns":["canonical_id","name","category","description","example_chunks"]},{"key_columns":["term_id"],"name":"reference_glossary","relation":"reference_glossary","value_columns":["term_id","term_sa","term_en","definition","category","classical_citation","related_concepts"]}],"version":"nirmana-output-digest-spec-v1"}'::jsonb;
  old_texts_spec constant jsonb :=
    '{"components":[{"key_columns":["text_id"],"name":"classical_texts","relation":"classical_texts","value_columns":["text_id","title_en","title_sa","author","school","tradition","tier","license","license_cleared","total_chapters","total_verses","source_edition"]},{"key_columns":["chunk_id"],"name":"classical_text_chunks","relation":"classical_text_chunks","value_columns":["text_id","chunk_id","verse_ref","chapter","verse_start","verse_end","content_sa","content_en","content_summary","topics","source_citation","translator","tradition_school","embedding","content_sha256","topic_tag","ocr_confidence_score","cleaned_translation_text","cleaned_devanagari_text","low_confidence_flag","ocr_review_note","ocr_cleanup_pass_version","translation_status","translation_provenance"]}],"version":"nirmana-output-digest-spec-v1"}'::jsonb;
  new_texts_spec constant jsonb :=
    '{"components":[{"key_columns":["text_id"],"name":"classical_texts","relation":"classical_texts","value_columns":["text_id","title_en","title_sa","author","school","tradition","tier","license","license_cleared","total_chapters","total_verses","source_edition"],"where_in":{"text_id":["bhrigu_nandi_nadi","bphs","bphs_jaimini","brihat_jataka","brihat_samhita","hora_sara","jataka_parijata","muhurta_chintamani","nadi_navamsa_patel","phaladeepika","saravali","sarvartha_chintamani","tajaka_neelakanthi","uttara_kalamrita","yavana_jataka"]}},{"key_columns":["chunk_id"],"name":"classical_text_chunks","relation":"classical_text_chunks","value_columns":["text_id","chunk_id","verse_ref","chapter","verse_start","verse_end","content_sa","content_en","source_citation","translator","tradition_school","embedding","content_sha256"],"where_in":{"text_id":["bhrigu_nandi_nadi","bphs","bphs_jaimini","brihat_jataka","brihat_samhita","hora_sara","jataka_parijata","muhurta_chintamani","nadi_navamsa_patel","phaladeepika","saravali","sarvartha_chintamani","tajaka_neelakanthi","uttara_kalamrita","yavana_jataka"]}}],"version":"nirmana-output-digest-spec-v1"}'::jsonb;
  current_reference_sha text;
  current_reference_spec jsonb;
  current_texts_sha text;
  current_texts_spec jsonb;
BEGIN
  SELECT spec_sha256, spec
  INTO current_reference_sha, current_reference_spec
  FROM asset_output_digest_specs
  WHERE asset_id = 'bg_reference' AND retired_at IS NULL
  FOR UPDATE;

  IF NOT FOUND OR NOT (
    (current_reference_sha = old_reference_sha AND current_reference_spec = old_reference_spec)
    OR (current_reference_sha = new_reference_sha AND current_reference_spec = new_reference_spec)
  ) THEN
    RAISE EXCEPTION 'migration 609 refuses unknown current bg_reference digest spec: %',
      current_reference_sha;
  END IF;

  SELECT spec_sha256, spec
  INTO current_texts_sha, current_texts_spec
  FROM asset_output_digest_specs
  WHERE asset_id = 'bg_texts' AND retired_at IS NULL
  FOR UPDATE;

  IF NOT FOUND OR NOT (
    (current_texts_sha = old_texts_sha AND current_texts_spec = old_texts_spec)
    OR (current_texts_sha = new_texts_sha AND current_texts_spec = new_texts_spec)
  ) THEN
    RAISE EXCEPTION 'migration 609 refuses unknown current bg_texts digest spec: %',
      current_texts_sha;
  END IF;

  IF current_reference_sha = old_reference_sha
     AND EXISTS (
       SELECT 1 FROM asset_output_digest_specs
       WHERE asset_id = 'bg_reference' AND spec_sha256 = new_reference_sha
     ) THEN
    RAISE EXCEPTION 'migration 609 refuses pre-existing non-current bg_reference replacement';
  END IF;

  IF current_texts_sha = old_texts_sha
     AND EXISTS (
       SELECT 1 FROM asset_output_digest_specs
       WHERE asset_id = 'bg_texts' AND spec_sha256 = new_texts_sha
     ) THEN
    RAISE EXCEPTION 'migration 609 refuses pre-existing non-current bg_texts replacement';
  END IF;

  IF current_reference_sha = new_reference_sha AND NOT EXISTS (
    SELECT 1 FROM asset_output_digest_specs
    WHERE asset_id = 'bg_reference'
      AND spec_sha256 = old_reference_sha
      AND spec = old_reference_spec
      AND retired_at IS NOT NULL
  ) THEN
    RAISE EXCEPTION 'migration 609 refuses corrupt bg_reference predecessor evidence';
  END IF;

  IF current_texts_sha = new_texts_sha AND NOT EXISTS (
    SELECT 1 FROM asset_output_digest_specs
    WHERE asset_id = 'bg_texts'
      AND spec_sha256 = old_texts_sha
      AND spec = old_texts_spec
      AND retired_at IS NOT NULL
  ) THEN
    RAISE EXCEPTION 'migration 609 refuses corrupt bg_texts predecessor evidence';
  END IF;

  UPDATE asset_output_digest_specs
  SET retired_at = COALESCE(retired_at, NOW())
  WHERE asset_id = 'bg_reference'
    AND spec_sha256 = old_reference_sha
    AND spec = old_reference_spec
    AND retired_at IS NULL;

  UPDATE asset_output_digest_specs
  SET retired_at = COALESCE(retired_at, NOW())
  WHERE asset_id = 'bg_texts'
    AND spec_sha256 = old_texts_sha
    AND spec = old_texts_spec
    AND retired_at IS NULL;

  INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
  VALUES
    ('bg_reference', new_reference_sha, new_reference_spec),
    ('bg_texts', new_texts_sha, new_texts_spec)
  ON CONFLICT (asset_id, spec_sha256) DO NOTHING;

  IF NOT EXISTS (
    SELECT 1 FROM asset_output_digest_specs
    WHERE asset_id = 'bg_reference'
      AND spec_sha256 = new_reference_sha
      AND spec = new_reference_spec
      AND retired_at IS NULL
  ) OR NOT EXISTS (
    SELECT 1 FROM asset_output_digest_specs
    WHERE asset_id = 'bg_texts'
      AND spec_sha256 = new_texts_sha
      AND spec = new_texts_spec
      AND retired_at IS NULL
  ) THEN
    RAISE EXCEPTION 'migration 609 failed exact replacement postflight';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_output_digest_specs
    WHERE asset_id = 'bg_reference'
      AND spec_sha256 = old_reference_sha
      AND spec = old_reference_spec
      AND retired_at IS NOT NULL
  ) OR NOT EXISTS (
    SELECT 1 FROM asset_output_digest_specs
    WHERE asset_id = 'bg_texts'
      AND spec_sha256 = old_texts_sha
      AND spec = old_texts_spec
      AND retired_at IS NOT NULL
  ) THEN
    RAISE EXCEPTION 'migration 609 failed to retain exact retired predecessor evidence';
  END IF;
END $$;

-- Forward reversal: append a new reviewed spec and retire these rows only after
-- proving any receipts that depend on them remain resolvable. Never delete a
-- digest specification referenced by provenance evidence.

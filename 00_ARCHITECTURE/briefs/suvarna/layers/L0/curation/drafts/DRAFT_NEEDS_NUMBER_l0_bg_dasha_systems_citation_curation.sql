-- =============================================================================
-- DRAFT_NEEDS_NUMBER_l0_bg_dasha_systems_citation_curation.sql      (HELD DRAFT: NOT APPLIED, NOT A MIGRATION)
-- Lane: curation-lane (Exec Suvarna), branch suvarna/land/TI-curation-001, N-101 curation of bg_dasha_systems.
-- SS allocates the migration number (block 1200-1299).  Citation TEXT only: 21 rows across 2 table(s);
-- no value, key or other column changes.  Every proposed citation is chunk-level (corpus chunk id + page + printed
-- sloka) and each row's FACT/INFERENCE class and supporting quote are in the ledger
-- (assets/bg_dasha_systems_ledger.json); rows the held text CONTRADICTS are not touched (acharya batch).
-- GUARDS  per-table md5 fingerprint of every non-timestamp column must equal the pinned pre-state; every UPDATE
--         matches natural key AND exact old citation and must hit the exact expected row count; post-state
--         fingerprints are pinned; the stored integrity_check_sql is pinned by md5 and resealed (each sha256/md5 literal replaced by the value computed on the test replica after the UPDATEs); it must read true afterwards;
--         idempotent: a second apply is a NOTICE + no-op.
-- Seed parity (NOT patched here; follow-up after SS review and PR #2984): platform/python-sidecar/brahmagyan/l0_dasha_systems.py (delete-then-insert; also writes the 20 ontology rows)
--         must carry the same citations or the next L0 rebuild reverts them; editing it also stales
--         nirmana-writer-digests.json (a #2984 file).
-- =============================================================================

DO $curation$
DECLARE
  n integer;
  ic text;
  ok boolean;
  fp_0 text;
  fp_1 text;
  fp_2 text;
BEGIN
  SELECT integrity_check_sql INTO ic FROM asset_registry WHERE asset_id = 'bg_dasha_systems' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'curation refuses: asset_registry row bg_dasha_systems not found'; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t) - ARRAY[$v$created_at$v$]::text[])::text, E'\n' ORDER BY canonical_id::text COLLATE "C"), '')) FROM brahma_dasha_systems t$q$ INTO fp_0;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t) - ARRAY[$v$created_at$v$]::text[])::text, E'\n' ORDER BY entity_class::text COLLATE "C",canonical_id::text COLLATE "C"), '')) FROM brahma_ontology t WHERE entity_class='dasha_system'$q$ INTO fp_1;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY 1), '')) FROM reference_dasha_systems t$q$ INTO fp_2;
  IF fp_0 = 'b3b36b229a63aa0cc08d90b2036518b2' AND fp_1 = 'c07ea3815a0f9f07544ec018131766ca' AND fp_2 = '8bd115683f7c39fb661c08aad6c6f998' THEN
    IF NOT (position('ecec58c2c2ae25afc327be8f5696330ea5241883bf88c875b61d384f4cfd338e' IN ic) > 0 AND position('f910f597da07b7fb63ada55e26f196a897d505aadad14f88917801da3df93430' IN ic) > 0) THEN RAISE EXCEPTION 'curation refuses: tables are at the curated content but the registry contract is not resealed'; END IF;
    RAISE NOTICE 'curation already applied: no-op';
    RETURN;
  END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t) - ARRAY[$v$created_at$v$]::text[])::text, E'\n' ORDER BY canonical_id::text COLLATE "C"), '')) FROM brahma_dasha_systems t$q$ INTO fp_0;
  IF fp_0 IS DISTINCT FROM 'f3d028e1401e74ea409ce48132dd6141' THEN RAISE EXCEPTION 'curation refuses: brahma_dasha_systems is not the pinned pre-state (%)', fp_0; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t) - ARRAY[$v$created_at$v$]::text[])::text, E'\n' ORDER BY entity_class::text COLLATE "C",canonical_id::text COLLATE "C"), '')) FROM brahma_ontology t WHERE entity_class='dasha_system'$q$ INTO fp_1;
  IF fp_1 IS DISTINCT FROM '1faf767f52f0219acfed43ec928c7f8e' THEN RAISE EXCEPTION 'curation refuses: brahma_ontology is not the pinned pre-state (%)', fp_1; END IF;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY 1), '')) FROM reference_dasha_systems t$q$ INTO fp_2;
  IF fp_2 IS DISTINCT FROM '8bd115683f7c39fb661c08aad6c6f998' THEN RAISE EXCEPTION 'curation refuses: reference_dasha_systems is not the pinned pre-state (%)', fp_2; END IF;
  IF md5(ic) IS DISTINCT FROM '6c90488ea53226613e86806fa3529135' THEN RAISE EXCEPTION 'curation refuses: registry integrity_check_sql is not the pinned pre-state text (md5 mismatch)'; END IF;

  UPDATE brahma_dasha_systems t SET classical_citations = v.new_c::jsonb
    FROM (VALUES
      ($c$ashtottari$c$, $c$[{"chapter": 48, "text_id": "bphs"}]$c$, $c$[{"chapter": 506, "chunk_id": "5d8d0f7c-eba1-4074-8d4c-579ba2f10003", "text_id": "bphs", "verse_ref": "PG506:C1"}, {"chapter": 505, "chunk_id": "d9bc2eb2-7fb2-45fd-b0e0-c976de1def0b", "text_id": "bphs", "verse_ref": "PG505:C1"}, {"chapter": 508, "chunk_id": "a902ac3e-12ab-4333-b0d7-d804b8dd3682", "text_id": "bphs", "verse_ref": "PG508:C1"}]$c$),
      ($c$chaturashiti_sama$c$, $c$[{"chapter": 49, "text_id": "bphs"}]$c$, $c$[{"chapter": 515, "chunk_id": "63a1277a-598b-4fa0-a646-c279bf1a0b34", "text_id": "bphs", "verse_ref": "PG515:C1"}]$c$),
      ($c$dwadashottari$c$, $c$[{"chapter": 48, "text_id": "bphs"}]$c$, $c$[{"chapter": 511, "chunk_id": "23f9fa96-40a6-4240-a732-133791e48cdf", "text_id": "bphs", "verse_ref": "PG511:C1"}]$c$),
      ($c$dwisaptati_sama$c$, $c$[{"chapter": 49, "text_id": "bphs"}]$c$, $c$[{"chapter": 515, "chunk_id": "63a1277a-598b-4fa0-a646-c279bf1a0b34", "text_id": "bphs", "verse_ref": "PG515:C1"}]$c$),
      ($c$panchottari$c$, $c$[{"chapter": 48, "text_id": "bphs"}]$c$, $c$[{"chapter": 511, "chunk_id": "23f9fa96-40a6-4240-a732-133791e48cdf", "text_id": "bphs", "verse_ref": "PG511:C1"}, {"chapter": 511, "chunk_id": "1d6274b0-ecaa-4400-ae43-1c6fddcd04bd", "text_id": "bphs", "verse_ref": "PG511:C2"}]$c$),
      ($c$shodashottari$c$, $c$[{"chapter": 48, "text_id": "bphs"}]$c$, $c$[{"chapter": 509, "chunk_id": "3d2a7f50-137e-4829-b203-36ad59640a26", "text_id": "bphs", "verse_ref": "PG509:C1"}]$c$),
      ($c$vimshottari$c$, $c$[{"chapter": 46, "text_id": "bphs"}]$c$, $c$[{"chapter": 499, "chunk_id": "33882f91-cfc0-43b6-997d-4e693993e232", "text_id": "bphs", "verse_ref": "PG499:C1"}, {"chapter": 499, "chunk_id": "63bea733-c49c-4e66-9ec3-58fe4496c6c0", "text_id": "bphs", "verse_ref": "PG499:C2"}, {"chapter": 500, "chunk_id": "865159e7-85a6-4bd8-944e-4bf5b876a2c4", "text_id": "bphs", "verse_ref": "PG500:C1"}, {"chapter": 519, "chunk_id": "2e1bc175-bc82-418a-860c-6184d6ef2a04", "text_id": "bphs", "verse_ref": "PG519:C1"}]$c$),
      ($c$yogini$c$, $c$[{"chapter": 50, "text_id": "bphs"}]$c$, $c$[{"chapter": 564, "chunk_id": "7d467f70-6295-402a-9ef6-60a898176f3e", "text_id": "bphs", "verse_ref": "PG564:C1"}]$c$)
    ) AS v(canonical_id, old_c, new_c)
    WHERE t.canonical_id::text = v.canonical_id AND t.classical_citations::jsonb = v.old_c::jsonb;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 8 THEN RAISE EXCEPTION 'curation expected 8 brahma_dasha_systems rows, updated %', n; END IF;
  UPDATE brahma_ontology t SET source_citation = v.new_c
    FROM (VALUES
      ($c$dasha_system$c$, $c$ashtottari$c$, $c$BPHS Ch.48 (Conditional Nakshatra Dashas)$c$, $c$BPHS Ch. 46 (Dasas (Periods) of planets), Sloka 17-20 as printed — bphs:PG505:C1 (Santhanam trans.); PG506:C1$c$),
      ($c$dasha_system$c$, $c$chaturashiti_sama$c$, $c$BPHS Ch.49 (Kalachakra & Conditional Dashas)$c$, $c$BPHS Ch. 46 (Dasas (Periods) of planets), p.515 — bphs:PG515:C1 (Santhanam trans.)$c$),
      ($c$dasha_system$c$, $c$dwadashottari$c$, $c$BPHS Ch.48 (Conditional Nakshatra Dashas)$c$, $c$BPHS Ch. 46 (Dasas (Periods) of planets), Sloka 27-28 as printed — bphs:PG511:C1 (Santhanam trans.)$c$),
      ($c$dasha_system$c$, $c$dwisaptati_sama$c$, $c$BPHS Ch.49 (Kalachakra & Conditional Dashas)$c$, $c$BPHS Ch. 46 (Dasas (Periods) of planets), Sloka 37-39 as printed — bphs:PG515:C1 (Santhanam trans.)$c$),
      ($c$dasha_system$c$, $c$kalachakra$c$, $c$BPHS Ch.49 (Kalachakra & Conditional Dashas)$c$, $c$BPHS Ch. 46 (Dasas (Periods) of planets), Sloka 89 as printed — bphs:PG529:C1 (Santhanam trans.)$c$),
      ($c$dasha_system$c$, $c$panchottari$c$, $c$BPHS Ch.48 (Conditional Nakshatra Dashas)$c$, $c$BPHS Ch. 46 (Dasas (Periods) of planets), Sloka 29-31 as printed — bphs:PG511:C1 (Santhanam trans.)$c$),
      ($c$dasha_system$c$, $c$shashtihayani$c$, $c$BPHS Ch.49 (Kalachakra & Conditional Dashas)$c$, $c$BPHS Ch. 46 (Dasas (Periods) of planets), Sloka 40-41 as printed — bphs:PG517:C1 (Santhanam trans.); total 60 by arithmetic from example (acharya to confirm 10 vs 13)$c$),
      ($c$dasha_system$c$, $c$shatabdika$c$, $c$BPHS Ch.48 (Conditional Nakshatra Dashas)$c$, $c$BPHS Ch. 46 (Dasas (Periods) of planets), p.513 — bphs:PG513:C1 (Santhanam trans.)$c$),
      ($c$dasha_system$c$, $c$shattrimsha_sama$c$, $c$BPHS Ch.49 (Kalachakra & Conditional Dashas)$c$, $c$BPHS Ch. 46 (Dasas (Periods) of planets), Sloka 42-43 as printed — bphs:PG517:C1 (Santhanam trans.); PG517:C2$c$),
      ($c$dasha_system$c$, $c$shodashottari$c$, $c$BPHS Ch.48 (Conditional Nakshatra Dashas)$c$, $c$BPHS Ch. 46 (Dasas (Periods) of planets), Sloka 24-26 as printed — bphs:PG509:C1 (Santhanam trans.)$c$),
      ($c$dasha_system$c$, $c$tara_dasha$c$, $c$BPHS Ch.47 (Tara Chakra & Nakshatra Dashas)$c$, $c$BPHS Ch. 46 (Dasas (Periods) of planets), Sloka 207-249 [sic] as printed — bphs:PG567:C1 (Santhanam trans.)$c$),
      ($c$dasha_system$c$, $c$vimshottari$c$, $c$BPHS Ch.46 (Vimshottari Dasha)$c$, $c$BPHS Ch. 46 (Dasas (Periods) of planets), Sloka 12-15 as printed — bphs:PG499:C1 (Santhanam trans.)$c$),
      ($c$dasha_system$c$, $c$yogini$c$, $c$BPHS Ch.50 (Yogini Dasha)$c$, $c$BPHS Ch. 46 (Dasas (Periods) of planets), Sloka 195-199 as printed — bphs:PG564:C1 (Santhanam trans.)$c$)
    ) AS v(entity_class, canonical_id, old_c, new_c)
    WHERE t.entity_class::text = v.entity_class AND t.canonical_id::text = v.canonical_id AND t.source_citation = v.old_c;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 13 THEN RAISE EXCEPTION 'curation expected 13 brahma_ontology rows, updated %', n; END IF;

  -- post-flight
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t) - ARRAY[$v$created_at$v$]::text[])::text, E'\n' ORDER BY canonical_id::text COLLATE "C"), '')) FROM brahma_dasha_systems t$q$ INTO fp_0;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t) - ARRAY[$v$created_at$v$]::text[])::text, E'\n' ORDER BY entity_class::text COLLATE "C",canonical_id::text COLLATE "C"), '')) FROM brahma_ontology t WHERE entity_class='dasha_system'$q$ INTO fp_1;
  EXECUTE $q$SELECT md5(COALESCE(string_agg((to_jsonb(t))::text, E'\n' ORDER BY 1), '')) FROM reference_dasha_systems t$q$ INTO fp_2;
  IF fp_0 IS DISTINCT FROM 'b3b36b229a63aa0cc08d90b2036518b2' THEN RAISE EXCEPTION 'curation post-flight: brahma_dasha_systems content fingerprint mismatch (%)', fp_0; END IF;
  IF fp_1 IS DISTINCT FROM 'c07ea3815a0f9f07544ec018131766ca' THEN RAISE EXCEPTION 'curation post-flight: brahma_ontology content fingerprint mismatch (%)', fp_1; END IF;
  IF fp_2 IS DISTINCT FROM '8bd115683f7c39fb661c08aad6c6f998' THEN RAISE EXCEPTION 'curation post-flight: reference_dasha_systems content fingerprint mismatch (%)', fp_2; END IF;

  -- reseal the stored integrity contract (its sha256 covers the changed tables)
  UPDATE asset_registry SET integrity_check_sql = replace(replace(integrity_check_sql, '8e35495ffef68342f7e88e2adee00654701feeee7852634cdada8df3932bf906', 'ecec58c2c2ae25afc327be8f5696330ea5241883bf88c875b61d384f4cfd338e'), '58a2b8b98dddcc6bb5dec73af8de386af3768457d2b3e2aea739bc435c83d4c9', 'f910f597da07b7fb63ada55e26f196a897d505aadad14f88917801da3df93430') WHERE asset_id = 'bg_dasha_systems';
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 1 THEN RAISE EXCEPTION 'curation expected 1 registry row, updated %', n; END IF;
  SELECT integrity_check_sql INTO ic FROM asset_registry WHERE asset_id = 'bg_dasha_systems';
  IF ic IS NOT NULL THEN
    EXECUTE ic INTO ok;
    IF ok IS NOT TRUE THEN RAISE EXCEPTION 'curation post-flight: bg_dasha_systems stored integrity_check_sql reads false'; END IF;
  END IF;
END
$curation$;

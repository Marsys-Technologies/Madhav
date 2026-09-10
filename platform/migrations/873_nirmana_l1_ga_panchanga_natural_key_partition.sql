-- 873_nirmana_l1_ga_panchanga_natural_key_partition.sql
--
-- NIRMANA v2.1 -- L1 (Ganita) W4 EXECUTE. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sixth of seven natural_key_partition backfills authorized by the
-- Conductor's ruling on adjudication #2180 (2026-09-07). Prior five:
-- ga_positions (868, PR #2205, merged), ga_ayurdaya (869, PR #2208,
-- merged), ga_sensitive_degree (870, PR #2209), ga_sade_sati (871,
-- PR #2212), ga_nakshatra (872, PR #2213).
--
-- ga_panchanga writes far more categories than this session's earlier,
-- partial characterisation assumed: 16 literal fact_category constants
-- (panchanga_calendrical, panchanga_tithi, panchanga_vara,
-- panchanga_karana, panchanga_yoga, panchanga_nakshatra_moon,
-- panchanga_hora_birth, panchanga_choghadiya_birth,
-- panchanga_disha_shul, panchanga_agni_vasa,
-- panchanga_tithi_shoonya_rashi, panchanga_nakshatra_shoonya_rashi,
-- panchanga_panchaka_classification, panchanga_solar_context,
-- panchanga_sun_moon_dynamics, panchanga_special_yoga_combinations)
-- PLUS 18 dynamically-constructed window categories -- 9 inauspicious
-- and 9 auspicious muhurta/kalam windows, built as
-- f"panchanga_{window_name}" inside _emit_inauspicious_window/
-- _emit_auspicious_window (ga_panchanga_writer.py:859) from the
-- INAUSPICIOUS_WINDOWS/AUSPICIOUS_WINDOWS tuple lists (lines
-- 1404-1431): rahu_kalam, yamaganda_kalam, gulika_kalam, durmuhurta,
-- varjyam, visha_ghati, sashtighati, yamakantaka, krakaca,
-- abhijit_muhurta, brahma_muhurta, pratah_sandhya, madhyahna_sandhya,
-- sayam_sandhya, amrit_kaal, vijaya_muhurta, godhuli_muhurta,
-- nishita_kala.
--
-- 34 total declared, 33 confirmed live for the canonical chart
-- (amrit_kaal legitimately absent -- _emit_auspicious_window returns
-- nothing when the underlying panchanga library finds no matching
-- timing object for a chart, an honest empty rather than a fabricated
-- row; verified this is the ONLY gap via a live comm diff against
-- chart_facts). All 34 share the exact same "panchanga_" prefix, so
-- this partition is expressed as a prefix match rather than an
-- unwieldy 34-item enumeration -- confirmed no OTHER writer emits
-- anything with this prefix: two incidental hits in ga_sade_sati_
-- writer.py and ga_sensitive_writer.py checked directly and confirmed
-- to be code comments / unrelated dict-key lookups, not fact_category
-- writes.

UPDATE asset_registry
   SET natural_key_partition = 'chart_facts.fact_category LIKE panchanga_%'
 WHERE asset_id = 'ga_panchanga'
   AND natural_key_partition IS NULL;

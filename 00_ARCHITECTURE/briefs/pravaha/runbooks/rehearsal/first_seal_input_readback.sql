-- FIRST-SEAL INPUT-STABILITY readbacks (runbook §5.5; Codex R16-3). READ-ONLY. Run as:
--   psql -X -q -t -A -F "$(printf '\t')" -v ON_ERROR_STOP=1 -v chart=482012f1-710e-4a25-994a-93821f5871aa -v gen=5.0 -f first_seal_input_readback.sql
-- PART A is the AUXILIARY readback: its output is compared BYTE FOR BYTE between R0 (before the brief), R1 (at the approval) and R2 (after the seal) — it is NOT compared to the manifest/brief/receipt
-- (a whole-table md5 is not the manifest's selected-row sha256, and a whole-chart build inventory is not the consumed-row digest). Both `build_id` columns are cast to text: the declared types differ
-- between the archived DDL (chart_facts TEXT) and the live catalog (UUID, read 2026-10-03), and a UNION of the two raw types fails type resolution.
-- PART B compares the snapshot's STORED consumed-row digests with the SAME SQL functions that derived them (the derivation the verifier and the seal use): both must be `true`.
SET default_transaction_read_only = on;
SELECT kind, rel, grain, value, n FROM (
  SELECT 'A1_l1_build' AS kind, 'chart_facts' AS rel, ayanamsha_id AS grain, build_id::text AS value, count(*)::text AS n
    FROM public.chart_facts WHERE chart_id = :'chart'::uuid GROUP BY ayanamsha_id, build_id::text
  UNION ALL
  SELECT 'A1_l1_build', 'chart_dashas', ayanamsha_id || '/' || system_id, build_id::text, count(*)::text
    FROM public.chart_dashas WHERE chart_id = :'chart'::uuid GROUP BY ayanamsha_id, system_id, build_id::text
  UNION ALL SELECT 'A2_registry_md5', 'ka_gochara_predicate', '', md5(coalesce(string_agg(to_jsonb(t)::text, '|' ORDER BY to_jsonb(t)::text), '')), count(*)::text FROM public.ka_gochara_predicate t
  UNION ALL SELECT 'A2_registry_md5', 'ka_gochara_factor', '', md5(coalesce(string_agg(to_jsonb(t)::text, '|' ORDER BY to_jsonb(t)::text), '')), count(*)::text FROM public.ka_gochara_factor t
  UNION ALL SELECT 'A2_registry_md5', 'ka_gochara_rule_path', '', md5(coalesce(string_agg(to_jsonb(t)::text, '|' ORDER BY to_jsonb(t)::text), '')), count(*)::text FROM public.ka_gochara_rule_path t
  UNION ALL SELECT 'A2_registry_md5', 'ka_gochara_rule_path_prerequisite', '', md5(coalesce(string_agg(to_jsonb(t)::text, '|' ORDER BY to_jsonb(t)::text), '')), count(*)::text FROM public.ka_gochara_rule_path_prerequisite t
  UNION ALL SELECT 'A2_registry_md5', 'ka_gochara_rule_path_soft_factor', '', md5(coalesce(string_agg(to_jsonb(t)::text, '|' ORDER BY to_jsonb(t)::text), '')), count(*)::text FROM public.ka_gochara_rule_path_soft_factor t
  UNION ALL SELECT 'A2_registry_md5', 'ka_gochara_rule_path_seal', '', md5(coalesce(string_agg(to_jsonb(t)::text, '|' ORDER BY to_jsonb(t)::text), '')), count(*)::text FROM public.ka_gochara_rule_path_seal t
  UNION ALL SELECT 'A3_corpus_md5', 'classical_texts', '', md5(coalesce(string_agg(to_jsonb(t)::text, '|' ORDER BY to_jsonb(t)::text), '')), count(*)::text FROM public.classical_texts t
  UNION ALL SELECT 'A3_corpus_md5', 'classical_chunks', '', md5(coalesce(string_agg(to_jsonb(t)::text, '|' ORDER BY to_jsonb(t)::text), '')), count(*)::text FROM public.classical_chunks t
  UNION ALL SELECT 'A3_corpus_md5', 'classical_attributions', '', md5(coalesce(string_agg(to_jsonb(t)::text, '|' ORDER BY to_jsonb(t)::text), '')), count(*)::text FROM public.classical_attributions t
) q ORDER BY 1, 2, 3, 4;
-- PART B: stored digests vs the same derivation (expected: every row `true | true`)
SELECT 'B_snapshot_vs_rederived', s.generation,
       (s.l1_facts_digest = public.ka_gochara_search_l1_facts_digest(s.chart_id, s.consumed_fact_ids))::text AS l1_facts_digest_ok,
       (s.dasha_digest = public.ka_gochara_search_dasha_digest(s.chart_id, s.consumed_dasha_row_ids))::text AS dasha_digest_ok
  FROM public.ka_gochara_search_input_snapshot s WHERE s.chart_id = :'chart'::uuid AND s.generation = :'gen' ORDER BY 1, 2;

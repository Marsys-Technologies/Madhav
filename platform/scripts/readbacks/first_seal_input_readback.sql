WITH
-- FIRST-SEAL INPUT-STABILITY readback (runbook section 5.5; Codex R16-3; before-seal list C-09). READ-ONLY. ONE SELECT/WITH statement accepted by the executor
-- readback_sql protocol (fleet/readback_sql.sh): it starts with WITH, contains no backslash and no psql variable, and the executor session is read-only.
-- Brought from origin/campaign/pravaha (00_ARCHITECTURE/briefs/pravaha/runbooks/rehearsal/first_seal_input_readback.sql). Changes from that file, all forced by the
-- executor protocol: the two psql variables (chart, gen) are the literals of the params row below; the SET and the two result sets are ONE statement whose parts
-- are told apart by `kind`; PART B no longer returns an empty set when the snapshot is absent (see below).
-- Staged per request under run/ops/sql (hash-bound). Run it three times: R0 (before the brief), R1 (at the approval) and R2 (after the seal).
--
-- PART A (kind A1_..A3_) is the AUXILIARY readback: its rows are compared BYTE FOR BYTE between R0, R1 and R2 - they are NOT compared to the manifest/brief/receipt
-- (a whole-table md5 is not the manifest's selected-row sha256, and a whole-chart build inventory is not the consumed-row digest). Both build_id columns are cast to
-- text: the declared types differ between the archived DDL (chart_facts TEXT) and the live catalog (UUID, read 2026-10-03), and a UNION of the two raw types fails
-- type resolution. A change in any L1 build, registry row or classical-corpus row between two runs changes at least one A row.
-- PART B (kind B_snapshot_vs_rederived) compares the snapshot's STORED consumed-row digests with the SAME SQL functions that derived them (the derivation the
-- verifier and the seal use): in every run, B must read grain=true value=true and n=1. A missing snapshot, or a NULL stored or re-derived digest, reads false
-- (n=0 for a missing one) - never an empty set that a reader could take for a pass.
-- params: the canonical chart and the generation the first seal covers (century_contract.json: "5.0"). Another generation is another reviewed file.
params AS (SELECT '482012f1-710e-4a25-994a-93821f5871aa'::uuid AS chart, '5.0'::text AS gen),
part_a AS (
  SELECT 'A1_l1_build' AS kind, 'chart_facts' AS rel, f.ayanamsha_id::text AS grain, f.build_id::text AS value, count(*)::text AS n
    FROM public.chart_facts f, params p WHERE f.chart_id = p.chart GROUP BY f.ayanamsha_id, f.build_id::text
  UNION ALL
  SELECT 'A1_l1_build', 'chart_dashas', d.ayanamsha_id || '/' || d.system_id, d.build_id::text, count(*)::text
    FROM public.chart_dashas d, params p WHERE d.chart_id = p.chart GROUP BY d.ayanamsha_id, d.system_id, d.build_id::text
  UNION ALL SELECT 'A2_registry_md5', 'ka_gochara_predicate', '', md5(coalesce(string_agg(to_jsonb(t)::text, '|' ORDER BY to_jsonb(t)::text), '')), count(*)::text FROM public.ka_gochara_predicate t
  UNION ALL SELECT 'A2_registry_md5', 'ka_gochara_factor', '', md5(coalesce(string_agg(to_jsonb(t)::text, '|' ORDER BY to_jsonb(t)::text), '')), count(*)::text FROM public.ka_gochara_factor t
  UNION ALL SELECT 'A2_registry_md5', 'ka_gochara_rule_path', '', md5(coalesce(string_agg(to_jsonb(t)::text, '|' ORDER BY to_jsonb(t)::text), '')), count(*)::text FROM public.ka_gochara_rule_path t
  UNION ALL SELECT 'A2_registry_md5', 'ka_gochara_rule_path_prerequisite', '', md5(coalesce(string_agg(to_jsonb(t)::text, '|' ORDER BY to_jsonb(t)::text), '')), count(*)::text FROM public.ka_gochara_rule_path_prerequisite t
  UNION ALL SELECT 'A2_registry_md5', 'ka_gochara_rule_path_soft_factor', '', md5(coalesce(string_agg(to_jsonb(t)::text, '|' ORDER BY to_jsonb(t)::text), '')), count(*)::text FROM public.ka_gochara_rule_path_soft_factor t
  UNION ALL SELECT 'A2_registry_md5', 'ka_gochara_rule_path_seal', '', md5(coalesce(string_agg(to_jsonb(t)::text, '|' ORDER BY to_jsonb(t)::text), '')), count(*)::text FROM public.ka_gochara_rule_path_seal t
  UNION ALL SELECT 'A3_corpus_md5', 'classical_texts', '', md5(coalesce(string_agg(to_jsonb(t)::text, '|' ORDER BY to_jsonb(t)::text), '')), count(*)::text FROM public.classical_texts t
  UNION ALL SELECT 'A3_corpus_md5', 'classical_chunks', '', md5(coalesce(string_agg(to_jsonb(t)::text, '|' ORDER BY to_jsonb(t)::text), '')), count(*)::text FROM public.classical_chunks t
  UNION ALL SELECT 'A3_corpus_md5', 'classical_attributions', '', md5(coalesce(string_agg(to_jsonb(t)::text, '|' ORDER BY to_jsonb(t)::text), '')), count(*)::text FROM public.classical_attributions t
),
part_b AS (
  SELECT 'B_snapshot_vs_rederived' AS kind, p.gen AS rel,
         coalesce((s.l1_facts_digest = public.ka_gochara_search_l1_facts_digest(s.chart_id, s.consumed_fact_ids))::text, 'false') AS grain,
         coalesce((s.dasha_digest = public.ka_gochara_search_dasha_digest(s.chart_id, s.consumed_dasha_row_ids))::text, 'false') AS value,
         (s.chart_id IS NOT NULL)::int::text AS n
    FROM params p LEFT JOIN public.ka_gochara_search_input_snapshot s ON s.chart_id = p.chart AND s.generation = p.gen
)
SELECT kind, rel, grain, value, n
FROM (SELECT * FROM part_a UNION ALL SELECT * FROM part_b) q
ORDER BY kind COLLATE "C", rel COLLATE "C", grain COLLATE "C", value COLLATE "C", n COLLATE "C";

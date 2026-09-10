-- 728_bo_sangati_volume_formula.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; F-L2-14 -- expected_volume_formula gap).
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- Sixth asset in the F-L2-14 sweep. Third bound-style (not point-estimate)
-- formula after bo_arudha and bo_vargottama_dhana, and the widest bound so
-- far -- this asset's row count is the most data-dependent measured in this
-- campaign.
--
-- bo_sangati.py:227-324 (_build_cdlm_cells) iterates every ordered pair of
-- the 13 canonical domains (brahmagyan/domain_vocabulary.py's
-- CANONICAL_DOMAINS_SORTED -- the same 13-domain vocabulary this asset's
-- own M-14 check already hardcodes), C(13,2) = 78 possible pairs, and emits
-- a bodha_cdlm_cells row ONLY for a pair with at least one shared MSR
-- signal (line 248: "if not shared_ids: continue"). There is no ranking
-- cutoff / top-K limit on this table (top_k_rank_in_snapshot ranks every
-- emitted cell, it does not truncate the set) -- so the real per-ayanamsha
-- range is [0, 78], entirely determined by how many domain pairs happen to
-- share a signal for that chart.
--
-- Measured live across all three production charts before landing (C12:
-- never a formula that has yet to be checked against real data) shows this
-- variance is real, not theoretical: the canonical chart (482012f1) sits at
-- 56/78 pairs (72%) on every ayanamsha, while the other two charts sit at
-- only 15/78 (19%) -- a 3.7x spread between charts, both well inside the
-- [0, 78] bound and consistent within each chart across all 5 ayanamshas.

UPDATE asset_registry
   SET expected_volume_formula = '0 <= ROWS <= AYANAMSHAS * DOMAIN_PAIRS_CEILING',
       expected_volume_inputs = jsonb_build_object(
         'AYANAMSHAS', 5,
         'DOMAIN_PAIRS_CEILING', 78,
         'domain_pairs_ceiling_meaning', 'C(13,2) -- all ordered pairs of the 13 canonical domains (brahmagyan/domain_vocabulary.py CANONICAL_DOMAINS_SORTED)',
         'row_condition', 'a domain pair gets a row only if >=1 MSR signal is shared between both domains that build (bo_sangati.py:248) -- no top-K cutoff, no floor other than 0',
         'bound_per_chart', jsonb_build_object('min', 0, 'max', 390),
         'measured_pairs_per_ayanamsha_by_chart', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', 56,
           '1c826d5a-41cb-4450-b4dc-59d440e5f75a', 15,
           'cb73cd3d-9eba-4220-9902-0de91566e980', 15
         ),
         'contract_ref', 'platform/python-sidecar/pipeline/orchestrator/writers/bo_sangati.py:227-324'
       ),
       volume_explanation = 'A domain-pair cell exists only if the two domains share at least '
         || 'one MSR signal that build -- genuinely chart-data-dependent, not a build defect. No '
         || 'ranking or top-K limit applies to this table (top_k_rank_in_snapshot orders the '
         || 'emitted set, it does not truncate it), so the real ceiling is the full domain-pair '
         || 'combinatorics: C(13,2) = 78 pairs x 5 ayanamshas = 390/chart. The wide observed '
         || 'spread across production charts (56/78 pairs on the canonical chart vs 15/78 on the '
         || 'other two, each stable across all 5 ayanamshas within its own chart) confirms this is '
         || 'real variance to expect, not a hint that one chart''s build is defective.'
 WHERE asset_id = 'bo_sangati';

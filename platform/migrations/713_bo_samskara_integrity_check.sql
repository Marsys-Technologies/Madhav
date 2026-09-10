-- 713_bo_samskara_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; M-14 layer-wide gap). Adds a real
-- integrity_check_sql for bo_samskara. Transaction ownership belongs to
-- platform/scripts/migrate.ts. Fourth migration of L2's 710-729 range.
--
-- bo_samskara's own docstring claims "one bodha_signal_embeddings row per
-- bodha_msr_signals row (1:1)". Live census before writing anything: this
-- is currently FALSE — 150,081 of 150,150 MSR signals have an embedding;
-- 69 are missing, all on chart_id 1c826d5a-41cb-4450-b4dc-59d440e5f75a
-- (Abhinandan Mohanty), spread ~13-14 per ayanamsha across all five, with
-- ZERO gaps on the other two charts. That distribution (small, uniform
-- across ayanamshas, isolated to one non-canonical chart) is consistent
-- with a transient embedding-API batch failure on that chart's build, not
-- a structural writer defect — but C12 forbids asserting "0 missing" when
-- it is honestly false today, so this check does NOT include a
-- completeness/coverage assertion. Recorded as a finding rather than
-- silently worked around (D-L2-031).
--
-- Seven invariants that ARE universally true today, all independently
-- verified live before landing:
--   1. No orphan embeddings — every bodha_signal_embeddings row references
--      a real bodha_msr_signals.signal_id.
--   2. No duplicate embeddings — at most one row per signal_id (the 1:1
--      relationship holds in the "never more than 1" direction even where
--      it doesn't hold in the "never less than 1" direction).
--   3. embedding_model is always 'text-multilingual-embedding-002' (the
--      writer's own EMBEDDING_MODEL constant).
--   4. embedding_model_version is always '002' (EMBEDDING_VER).
--   5. embedding_vec is never NULL and always exactly 768-dimensional
--      (EMBEDDING_DIM), checked via pgvector's vector_dims().
--   6. Denormalized chart_id/ayanamsha_id on the embedding row always
--      match the referenced signal's own chart_id/ayanamsha_id — a
--      cross-table consistency guard, not just a same-table check.
--   7. embedding_input_summary is never NULL or empty (traceability floor
--      — what text was actually embedded must be recoverable).

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  NOT EXISTS (
    SELECT 1 FROM bodha_signal_embeddings e
    LEFT JOIN bodha_msr_signals m ON m.signal_id = e.signal_id
    WHERE m.signal_id IS NULL
  )
  AND NOT EXISTS (
    SELECT signal_id FROM bodha_signal_embeddings
    GROUP BY signal_id
    HAVING count(*) > 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_signal_embeddings
    WHERE embedding_model != 'text-multilingual-embedding-002'
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_signal_embeddings
    WHERE embedding_model_version != '002'
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_signal_embeddings
    WHERE embedding_vec IS NULL OR vector_dims(embedding_vec) != 768
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_signal_embeddings e
    JOIN bodha_msr_signals m ON m.signal_id = e.signal_id
    WHERE e.chart_id != m.chart_id OR e.ayanamsha_id != m.ayanamsha_id
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_signal_embeddings
    WHERE embedding_input_summary IS NULL OR embedding_input_summary = ''
  )
$ic$
 WHERE asset_id = 'bo_samskara';

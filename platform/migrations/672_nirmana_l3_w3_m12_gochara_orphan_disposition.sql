-- 672_nirmana_l3_w3_m12_gochara_orphan_disposition.sql
--
-- NIRMĀṆA L3 Kāla — W3 IMPLEMENT. Discharges finding F-CENT-2 / M12 (54 unrefreshable
-- orphan rows in `kala_gochara_windows`, found in L3_W1_ANALYSIS_BATCH_A.md's audit of
-- `ka_gochara_v3_century_materialize`).
--
-- 54 rows carry generation='3.0' AND era_slice_key IS NULL (29 on the canonical chart
-- 482012f1, 25 on 1c826d5a), all stamped computed_at = 2026-08-11 08:58:12 (a single
-- historical instant, not an ongoing write), all peak_basis='gochara_lambda_e_v1' — a
-- DIFFERENT engine (ka_gochara's, not the century materializer's own) whose output was
-- promoted directly into the production surface at some point, bypassing the staging
-- table (kala_gochara_windows_v2 carries ZERO era_slice_key-NULL rows — verified live).
--
-- The century materializer's own production DELETE is era-scoped
-- (`WHERE chart_id=%s AND event_class=%s AND generation='3.0' AND era_slice_key=%s`,
-- pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py) and the writer's own
-- INSERT always supplies a concrete era_slice_key per decade slice — it has never written,
-- and by construction cannot write, an era_slice_key-NULL row. So these 54 rows are not an
-- ongoing accretion from the writer's normal operation; they are one-time historical debris
-- that the writer's own DELETE can never reach (§N.3: "rebuild REPLACES, never accretes" —
-- violated by construction for exactly these rows, which sit permanently in the served
-- surface and are the only rows in the table carrying attribution, making the corpus
-- internally inconsistent in exactly the field a caller would compare).
--
-- Verified before deletion (live, this session): no FK anywhere in the schema references
-- kala_gochara_windows by id; none of the 54 rows are a parent_window_id target of any other
-- row, nor do any of the 54 carry a parent_window_id themselves (no chain relationships);
-- the table has no outcome/confirmed/actual column, so this is not a P7 falsifiability seam.
-- Disposition: DELETE, per F-CENT-2's second remediation option (explicit disposition,
-- rather than folding a one-time cleanup into the per-slice production DELETE's WHERE
-- clause, which would conflate "this decade slice's own replace" with "clean up unrelated
-- legacy debris" and is not a substep the FROZEN plan_substeps/run_substep contract
-- (ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2) needs touched for a one-time cleanup).
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

DELETE FROM kala_gochara_windows
WHERE generation = '3.0'
  AND era_slice_key IS NULL;

-- 1073_data_plane_builder_l3_reference_read_grants.sql
--
-- Grant `data_plane_builder` the three L0 reference-table SELECTs that L3 Kāla reads on the
-- live build path, and NOTHING else. Deliberately does NOT grant `phala_rectification`.
--
-- WHY
-- ---
-- Migration 1070 restored the orchestrator-core grants `data_plane_builder` needs to START a
-- run. It did not reach the per-asset data reads. `data_plane_builder` holds ZERO role
-- memberships (re-verified live 2026-09-22: `pg_auth_members` returns no row for it), so it
-- inherits nothing from `role_orchestrator` — which DOES hold SELECT/INSERT/UPDATE/DELETE on
-- every table named here. The privileges exist; the builder is simply not in the role that
-- has them.
--
-- Measured live at the authority, 2026-09-22, read-only as `amjis_app`:
--
--   has_table_privilege('data_plane_builder', t, 'SELECT')
--     public.bg_transit_moorti       -> f
--     public.bg_synthetic_cohort     -> f
--     public.bg_synthetic_cohort_md  -> f
--     public.phala_rectification     -> f   (NOT granted here — see HOLD below)
--
--   All four are ordinary tables owned by `amjis_app`, relrowsecurity = false.
--
-- Consequence today, from the L3 environment-readiness audit (KALA_ENVIRONMENT_READINESS_
-- AUDIT_v1_0.md §F4) and re-traced in source for this migration:
--   * `ka_moorti_nirnaya` — CONFIRMED HARD FAIL. `_fetch_moorti_table` is called
--     unconditionally from `run()`; there is no try/except and it is a LIGHT writer, so there
--     is no substep boundary to isolate the failure.
--   * `ka_kshetra` — stage-6 cohort path has a try/except but no SAVEPOINT, so the aborted
--     transaction poisons and the NEXT statement fails with an unrelated-looking error. (That
--     savepoint gap is a real code fix, independent of this grant, and is NOT fixed here.)
--
-- SCOPE — least privilege, derived from actual source reads, not assumption
-- ------------------------------------------------------------------------
-- Verb map, grepped across platform/, platform-mcp/ and pipeline/ at this commit. Every read
-- below is a bare SELECT; there is no DML on these tables anywhere in an L3 path
-- (`grep -c 'INSERT|UPDATE|DELETE' services/ka_kshetra/cohort_client.py` -> 0):
--
--   bg_transit_moorti       SELECT
--       services/ka_moorti_nirnaya/writer.py:82-85  `_FETCH_MOORTI_TABLE_SQL`
--         (SELECT nakshatra_offset, moorti_name, quality_tier, phala_brief, classical_citation)
--       executed at services/ka_moorti_nirnaya/writer.py:169 (`_fetch_moorti_table`, :164),
--         called unconditionally from `KaMoortiNirnayaWriter.run()` at :195
--       27 rows live; the cited Phaladeepika Ch.26 reference partition (migration 401).
--
--   bg_synthetic_cohort     SELECT
--       services/ka_kshetra/cohort_client.py:171   corpus fingerprint (count/digest)
--       services/ka_kshetra/cohort_client.py:317,:322,:346,:365  count(*) base-rate denominator
--         and numerator (the module's own docstring at :32 states it returns only counts,
--         "never the matched rows")
--       services/ka_kshetra/writer.py:2304  SELECT MAX(build_id::text) — the corpus pin that
--         goes into the snapshot hash
--       10,000 rows live.
--
--   bg_synthetic_cohort_md  SELECT
--       services/ka_kshetra/cohort_client.py:179   corpus fingerprint (count/chain_version)
--       services/ka_kshetra/cohort_client.py:338   JOIN ... ON m.synthetic_id = c.synthetic_id
--         feeding the :346/:365 md_lord-conditioned base rates
--       100,000 rows live.
--
--   services/ka_kshetra/stage1_symbolization.py:236 also names `bg_transit_moorti`, but as a
--   `source_table=` provenance literal on a PrimitiveRow — no SQL, no privilege required.
--
-- HOLD — `phala_rectification` is deliberately NOT granted (Strategy §6.2)
-- -----------------------------------------------------------------------
-- `ka_kshetra` does read it today: `services/ka_kshetra/uncertainty.py:185-196`
-- (`fetch_sigma_t_days`, "SELECT offset_minutes, lel_fit_score, lagna_stable FROM
-- phala_rectification WHERE chart_id = %s"), called unconditionally from
-- `services/ka_kshetra/stage3_clocks.py:1012`. Granting SELECT would make that read succeed.
-- It is held anyway, for a reason of record rather than preference:
--
--   * It is L3 reading L4 — a dependency pointing UPWARD through the layer stack.
--   * MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md §6.2 rules: "Rectification and L5 weight
--     inputs require separately admitted, purpose-compatible immutable artifacts. An earlier
--     timestamp does not make an event-derived rectification posterior admissible under the
--     event-free prospective contract." A LIVE TABLE READ of L4 output is not a separately
--     admitted immutable artifact and cannot be made into one by a grant.
--   * A grant would cement the live read as the design. The correct disposition is a design
--     change — replace the live read with an admitted immutable artifact — which belongs in
--     the Kshetra brief, not in a privilege migration.
--   * It costs nothing measured. Verified live 2026-09-22: `phala_rectification` holds 185
--     rows per chart (370 across 2 charts) and ZERO rows with `lel_fit_score > 0`, so
--     `compute_sigma_t_days`'s `usable` filter (uncertainty.py:176-178) is always empty,
--     `len(usable) < 2` always holds, and the function always returns
--     (DEFAULT_SIGMA_T_DAYS, 'default_120s_assumption'). All 511,320 rows of
--     `kala_field_boundaries` carry `sigma_t_source = 'default_120s_assumption'` — 100%, no
--     other value present. The posterior contributes nothing today.
--
--   The undeclared-read half of this is filed separately as
--   00_ARCHITECTURE/briefs/nirmana/l3_autonomous/setup/
--   W0_REGISTER_AMENDMENT_001_KSHETRA_PHALA_RECTIFICATION.md (the read is absent from the W0
--   FIELD_CONTRACT_REGISTER: grep for 'phala_rectification' over that file returns nothing).
--
-- Deliberately NOT granted
-- ------------------------
--   * `phala_rectification` — above.
--   * INSERT / UPDATE / DELETE / TRUNCATE / REFERENCES on any table here. Note honestly that
--     `bg_cohort` (writers/bg_cohort.py:470) and `bg_transit_rules` (writers/bg_transit_rules.py:11)
--     ARE orchestrator-registered writers whose DML (bg_cohort.py:588,:593,:642,:673;
--     brahmagyan/l0_transit.py:1023) would need write privileges if `data_plane_builder` ever
--     dispatches them. That is a REAL, SEPARATE L0 reference-corpus seed gap, recorded for the
--     L0 grants owner rather than silently widened here: L3 reads these corpora, it does not
--     reseed them, and a builder able to rewrite a cited 27-row Phaladeepika reference table
--     or a 10,000-chart synthetic reference population has a far larger blast radius than one
--     able to read them.
--   * `kala_gochara_windows_archive_20260805` (verified: SELECT -> f for the builder). The
--     restore drill reportedly cannot read its own recovery source; that is CONFIRMED. It is
--     held out of this migration on purpose — it has no live caller anywhere in source (grep
--     across platform/, platform-mcp/, pipeline/ returns zero references; only governance
--     markdown and migrations 670/674 mention it), and the open question
--     (KALA_ELEVATION_READINESS_PACKAGE_v1_0.md A-3) is "does the R6 restore drill run as
--     `data_plane_builder` or as a privileged operator?" Landing the grant here would answer
--     that design question silently, as a side effect of an unrelated migration. It is a
--     separate item for the R6 gate owner.
--   * No sequence grants — SELECT needs none, and nothing here writes.
--   * No ownership, RLS, trigger or table-shape change.
--
-- AUTHORITY / SAFETY
-- ------------------
-- L3 Kāla reserved migration range 1070-1119 (DP-SD-021); 1073 is inside it and free in BOTH
-- migration directories (`platform/migrations/` and `platform/supabase/migrations/` are read
-- as ONE numeric sequence by platform/scripts/migrate.ts:832-835). `amjis_app` owns all three
-- tables and is the role the migration runner authenticates as, so this is an ordinary routine
-- migration with no owner bootstrap. GRANT is naturally idempotent; this migration is
-- re-runnable, adds privileges only, and revokes nothing.

BEGIN;

-- L0 reference corpora that L3 reads verbatim (§N.5: L1/L0 is the authority; L3 references,
-- never restates). Read-only: no L3 path writes any of these.
GRANT SELECT ON TABLE public.bg_transit_moorti      TO data_plane_builder;
GRANT SELECT ON TABLE public.bg_synthetic_cohort    TO data_plane_builder;
GRANT SELECT ON TABLE public.bg_synthetic_cohort_md TO data_plane_builder;

-- Fail closed if any grant did not take effect, so a silent no-op cannot pass as applied
-- (CLAUDE.md §N.8 Earned-Signal Principle: this check can genuinely read false — it did read
-- false on production at authoring time, which is why this migration exists).
DO $$
DECLARE
  missing text := '';
BEGIN
  IF NOT has_table_privilege('data_plane_builder','public.bg_transit_moorti','SELECT')
    THEN missing := missing || ' bg_transit_moorti.SELECT'; END IF;
  IF NOT has_table_privilege('data_plane_builder','public.bg_synthetic_cohort','SELECT')
    THEN missing := missing || ' bg_synthetic_cohort.SELECT'; END IF;
  IF NOT has_table_privilege('data_plane_builder','public.bg_synthetic_cohort_md','SELECT')
    THEN missing := missing || ' bg_synthetic_cohort_md.SELECT'; END IF;

  IF missing <> '' THEN
    RAISE EXCEPTION 'migration 1073 did not take effect; still missing:%', missing;
  END IF;

  -- The HOLD is an assertion, not a comment. Strategy §6.2 forbids admitting an
  -- event-derived L4 rectification posterior as a live L3 input; if some other change grants
  -- it, this migration must be re-read and the hold re-argued, not silently overtaken.
  IF has_table_privilege('data_plane_builder','public.phala_rectification','SELECT') THEN
    RAISE EXCEPTION
      'migration 1073: data_plane_builder has SELECT on phala_rectification, which Strategy '
      '§6.2 holds (L3 reading L4 live; rectification inputs require separately admitted, '
      'purpose-compatible immutable artifacts). Resolve the design change in the Kshetra '
      'brief before granting.';
  END IF;
END $$;

COMMIT;

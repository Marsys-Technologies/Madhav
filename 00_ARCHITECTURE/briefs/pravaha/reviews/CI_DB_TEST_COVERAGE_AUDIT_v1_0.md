---
artifact: CI_DB_TEST_COVERAGE_AUDIT
version: "1.2"
status: CURRENT (dated report) — re-run on main de64ff04f after the a53 suites landed; merge hold lifted for reviewed work only
date: 2026-10-04
author: Stream C (C54), pravaha campaign
generator: platform/scripts/governance/ci_db_test_coverage_audit.py (same PR)
scope: platform/python-sidecar test files vs .github/workflows/*.yml on origin/main at de64ff04f (2026-10-04)
changelog:
  - "1.2 (2026-10-04, Stream B; Stream C retired): RE-RUN on main de64ff04f — the a53 suites now exist on main, so the counts change (133 needing a database became 184; with a database 11 became 46; never with a database 122 became 138). The projection with PRs #3134 / #3136 / #3137 merged is in the Reviewer notes. Method and script unchanged; the front sections below were kept, the Summary and tables are regenerated."
  - "1.1 (2026-10-04, Stream B): adds the `integration_marker` column/summary — CI's generic sidecar jobs run `-m \"not integration\"`, so integration-marked DB tests are DESELECTED (visible) rather than silently skipped; reviewer notes on precision below."
---

# CI database-test coverage audit — v1.2

C54: three Gochara tests were found silently NOT_RUN in CI (they need a database
and were in no CI DB step's file list). This audit answers, statically, for every
test file under platform/python-sidecar: does it need a database (and why), and
does any CI step execute it WITH a database (a postgres service, a DSN /
REQUIRE_DB / cloud-sql-proxy in the job), WITHOUT one, or never?

Method (all static; no test was run, no database was touched):
- DB need: direct references (psycopg.connect, a DSN, disposable-Postgres helpers,
  a *_REQUIRE_DB gate), pytest fixtures that transitively reach database machinery
  through the conftest.py chain, imports from a sibling suite that needs one, or a
  NOT_RUN-on-unreachable-database skip. Lines that mention the machinery only to
  disable it (monkeypatched connect, a deliberately unused DSN) are not use.
- CI execution: every pytest invocation in every workflow, with `cd` tracking and
  shell-continuation joins; directory targets cover their subtree. A step is "with
  a database" when its job declares a postgres service or any run/env text in the
  job names a DSN / postgres / DATABASE_URL / cloud-sql-proxy / a REQUIRE_DB gate.
  Dynamic file lists (${FILES[@]}) are noted, not resolved.
- `--check` (not wired into CI yet) exits 1 when a DB-needing file is neither run
  with a database nor in the script's explicit, commented EXCLUSIONS list. This
  first run has NO exclusions, so --check currently fails on all 122 NEVER files —
  the exclusion list is the follow-up decision, file by file.

The C52 guard (tests/l3/gochara/test_a53_ci_db_list_guard.py, re-cut as PR #3134 on main)
covers the test_a53_*.py suites specifically; this audit is the whole sidecar. As of v1.2
the a53 suites ARE on main and appear in the tables below.

## Reviewer notes (Stream B, 2026-10-04)

- **v1.2 re-run (main de64ff04f): 184 needing a database, 46 executed with one, 138 never (126 executed without a database + 12 not executed).** Projection computed with the same function on the tree where PRs #3134, #3136 and #3137 are merged: **187 needing a database, 62 with one, 125 never (113 without a database + 12 not executed)** and **zero a53 / C5x files left in the never list** — what remains (125) is outside Gochara: bodha / ga / orchestrator writer tests, gochara_v3, ka_kshetra, l0 / l2 suites. Deciding which of those must run with a database is the follow-up (the script's EXCLUSIONS list, file by file); `--check` stays unwired until then.

- Counts are internally consistent (133 = 11 with a database + 110 executed without + 12 not executed).
- Precision: spot-checks found true positives (e.g. `bodha_writers/__tests__/test_l2_data_plane_contracts.py` skips when `L2_CONTRACT_DATABASE_URL` is unset) and at least one false positive class — tests that replace the connection with fakes through an attribute chain (`pipeline/orchestrator/tests/test_s7lock_guc_hardening.py` patches `orchestrator_db.psycopg.connect`) are still flagged by their fake-infrastructure text. Treat the NEVER list as a review queue, not as 122 defects.
- Intentionally excluded tests are now visible: the `integration` marker column separates DESELECTED-by-design from silent NOT_RUN risk (e.g. `ga_writers/__tests__/test_vimshottari_independent_verifier.py`'s live-DB smoke carries `@pytest.mark.integration`).
- The audit is static: it does not read CI's actual skip lists. A cross-check against a CI run's "SKIPPED … DATABASE_URL" lines is the natural next step.

## Summary

- test files needing a database: **184**
- executed WITH a database in CI: **46**
- NEVER executed with a database in CI: **138**

Of the 138: **126 ARE executed by CI but without a database** — they skip NOT_RUN silently every run (the C54 failure class) — and **12 are not executed by CI at all**.

Of the 126 executed without a database, **47 carry the `integration` marker** (module-level or on some tests): CI's generic sidecar jobs run `-m "not integration"`, so those tests are DESELECTED (visible in pytest's deselected count) rather than silently skipped — a deliberate, visible exclusion — and **79 carry no marker** (the silent NOT_RUN risk to review first). The marker is a file-level hint; the audit does not verify per step that the `-m` expression is present.

### NEVER run with a database in CI

| file | why it needs a database | executed WITHOUT a database in | integration marker |
|---|---|---|---|
| `platform/python-sidecar/bodha_writers/__tests__/test_l2_data_plane_contracts.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/ga_writers/__tests__/test_ga_vargas_integrity_nonvacuity_and_acceptance.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/ga_writers/__tests__/test_vimshottari_independent_verifier.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/pipeline/orchestrator/tests/test_mr39_idle_timeout_connection_setup.py` | direct reference: psycopg,dsn,disposable-pg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/pipeline/orchestrator/tests/test_s7lock_guc_hardening.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_class_lifetime_counts.py` | direct reference: psycopg | — | — |
| `platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_cohort.py` | direct reference: psycopg | — | — |
| `platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_dignity_reference.py` | direct reference: psycopg | — | — |
| `platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_muhurta_lattice.py` | direct reference: psycopg | — | — |
| `platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_ontology.py` | direct reference: psycopg | — | — |
| `platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_parihara_rules.py` | direct reference: psycopg | — | — |
| `platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_reference.py` | direct reference: psycopg | — | — |
| `platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_sky_calendar.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_texts.py` | direct reference: psycopg | — | — |
| `platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bo_pratijna.py` | direct reference: psycopg | — | — |
| `platform/python-sidecar/pipeline/orchestrator/writers/tests/test_mi_sankalpa.py` | direct reference: psycopg | — | — |
| `platform/python-sidecar/services/gochara_v3/tests/test_context_moorti_wiring.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates-gochara :: pytest — gochara fast dirs + unmarked gochara_v3 tests (required); ci.yml :: governance-gates-gochara :: pytest — non-gating benchmark (continue-on-error; NOT a gate) | some |
| `platform/python-sidecar/services/gochara_v3/tests/test_mr15_av_gate_bhava_num_fix.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates-gochara :: pytest — gochara fast dirs + unmarked gochara_v3 tests (required); ci.yml :: governance-gates-gochara :: pytest — non-gating benchmark (continue-on-error; NOT a gate) | some |
| `platform/python-sidecar/services/ka_kshetra/tests/test_stage0_kinematics.py` | direct reference: psycopg | — | — |
| `platform/python-sidecar/services/ka_kshetra/tests/test_stage2_promise.py` | direct reference: psycopg | — | — |
| `platform/python-sidecar/tests/l0/test_bg_ephemeris_writer_columns.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l0/test_l0_orphan_census.py` | direct reference: dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l2/test_b6_eval_harness.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | module |
| `platform/python-sidecar/tests/l2/test_bo22.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/l2/test_bo_upaya_preamble_strip.py` | uses fixture 'db_conn' from tests/l2/conftest.py (fixture body references psycopg) | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l2/test_l2_node_orphan_census.py` | direct reference: dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l2/test_l2_semantic_corrections.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l2/test_l2_wrapper_real_pg.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/l2/test_l2_wrapper_shadow_real_pg.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/l2/test_n8_earned_signal_detectors.py` | direct reference: psycopg,dsn,disposable-pg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_a25_final_edge_projection.py` | direct reference: disposable-pg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_a25_teardown_keeps_registry_row_pg.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_a25_v41_candidate_writer_pg.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_a53_am5_writer.py` | direct reference: psycopg,disposable-pg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_a53_aspect_span.py` | imports from sibling suite test_a53_record_store (direct reference: psycopg,dsn,disposable-pg,require-db-gate) | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_a53_ephemeral_tier_rule.py` | imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate) | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_a53_inventory.py` | direct reference: psycopg,dsn,disposable-pg,require-db-gate | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_a53_member_geometry.py` | imports from sibling suite test_a53_window_verification_gate (imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)) | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_a53_moon_on_demand.py` | imports from sibling suite test_a53_record_store (direct reference: psycopg,dsn,disposable-pg,require-db-gate) | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_a53_moon_scope_domain.py` | direct reference: psycopg,disposable-pg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_a53_p1_house_descriptor.py` | imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate) | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_a53_record_store.py` | direct reference: psycopg,dsn,disposable-pg,require-db-gate | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_a53_rule_registry_versions.py` | imports from sibling suite test_a53_record_store (direct reference: psycopg,dsn,disposable-pg,require-db-gate) | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_a53_version_selection.py` | imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate) | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_a53_window_sweep_pg.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_a53_writer_native_types.py` | direct reference: psycopg,disposable-pg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_b_binding_conformance.py` | uses fixture 'conn' from tests/l3/gochara/conftest.py (fixture body references psycopg,dsn) | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_g10_digest_spec_1086.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_node_series_pin.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_node_series_pin_w2g.py` | imports from sibling suite test_node_series_pin (direct reference: psycopg,dsn) | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_step06_enumeration.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_step06a_class_context.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_step06b_angular_m1.py` | imports from sibling suite test_step06b_windows_projection (direct reference: psycopg,dsn) | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_step06b_per_instant_permission.py` | imports from sibling suite test_step06b_windows_projection (direct reference: psycopg,dsn) | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_step06b_tara_testimony.py` | imports from sibling suite test_step06b_windows_projection (direct reference: psycopg,dsn) | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_step06b_three_field_valence.py` | imports from sibling suite test_step06b_windows_projection (direct reference: psycopg,dsn) | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_step06b_windows_projection.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_vedha_interval_gate.py` | imports from sibling suite test_step06b_windows_projection (direct reference: psycopg,dsn) | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_wp12_vedha_fingerprint.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_wp12_vedha_unsourced.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_wp4_decomposed.py` | uses fixture 'conn' from tests/l3/gochara/conftest.py (fixture body references psycopg,dsn) | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_wp6_ledger.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_wp7_sentinel.py` | uses fixture 'conn' from tests/l3/gochara/conftest.py (fixture body references psycopg,dsn) | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_wp9_m8_vedha_exceptions.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_wp9_overlays_kernel.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/gochara/test_wp9_stamp_columns.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/ka_kshetra/test_dhara_parity.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/l3/test_bhavishya_p0_safety.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/test_builder_role_ka_gochara_windows_v2.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/test_disposable_db_guard.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/test_i4_i5_output_digest_specs.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l3/test_ka_dasha_kala.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/l3/test_ka_kshetra_cohort_client.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/l3/test_ka_kshetra_migration_487_integration.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/l3/test_ka_kshetra_stage6_salience.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/l3/test_resonance_rebuild_rehearsal.py` | direct reference: dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/l5/test_mi_bhara_circularity_guard_w2.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/l5/test_mimamsa_multiplier.py` | direct reference: dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_a1_telemetry_upsert_guard.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_argala_migration_1219_sql.py` | direct reference: disposable-pg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_b1_forensic_gate.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_b6_disposable_guard.py` | direct reference: dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_bg_sarvatobhadra_grid_throughput.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_cr131_gochara_db_reachability.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_el19_saham_recompute.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_f188_mi_gunanaka_count_sql.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_f_a2_d6_executor.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_ga4_chandra_bala_birth_sign.py` | direct reference: dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_gochara_grammar.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_gochara_intensity.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_gochara_provision_roles_script.py` | direct reference: psycopg,dsn,disposable-pg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_gochara_sealer_stage_secrets_script.py` | direct reference: dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_has_writer_completeness.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_ka_gochara_sweep.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_l5_reference_resolution_ledger_design.py` | direct reference: psycopg,disposable-pg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_mi_bhavisya_append_only.py` | direct reference: psycopg,disposable-pg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_migration_1243_inert_registry_rows.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_migration_1255_builder_reference_grants.py` | direct reference: psycopg,disposable-pg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_migration_1259_integrity_scope_own_output.py` | direct reference: psycopg,disposable-pg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_migration_1275_chart_delete_per_chart_tables.py` | direct reference: psycopg,disposable-pg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_migration_1302_revoke_orchestrator_windows.py` | direct reference: psycopg,disposable-pg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_migration_527_generation_catalog_only.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_675_paddhati_arbitration_role.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_676_muhurta_seva_depends_on.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_677_o10_authority_profile.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_678_parva_volume_explanation.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_679_parva_level_column.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_730_vighnakara_depends_on.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_731_conc7_size_sql.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_848_dasha_kala_proxy_probe.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_849_tulana_health_probe.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_850_muhurta_seva_health_probe.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_852_vedha_gochara_expected_volume.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_853_kota_chakra_expected_volume.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_854_gochara_expected_volume.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_855_moorti_nirnaya_expected_volume.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_856_vighnakara_expected_volume.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_857_bhavishya_lekha_expected_volume.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_858_jivana_parva_expected_volume.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_859_avadhi_expected_volume.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_860_service_assets_expected_volume.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_861_gochara_resonance_expected_volume.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_862_kala_darshana_expected_volume.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_863_kalasutra_expected_volume.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_864_yojaka_expected_volume.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_865_gochara_v3_century_expected_volume.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_866_sangam_expected_volume.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_migration_867_kshetra_expected_volume.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_mimamsa_outcome.py` | direct reference: dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_mimamsa_prediction_ledger.py` | direct reference: dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_permission_curve_route.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_phala_muhurta.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_phala_phaladesa.py` | direct reference: dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_r6a1_neecha_bhanga.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_r6a3_d9_cross_check_redemption.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_sd_eventreg_durable_register.py` | direct reference: psycopg,dsn | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |
| `platform/python-sidecar/tests/test_w2g_validations.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | some |
| `platform/python-sidecar/tests/test_yoga_formation_band_route.py` | direct reference: psycopg | ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline | — |

### Run with a database in CI

| file | workflow :: job :: step |
|---|---|
| `platform/python-sidecar/ga_writers/__tests__/test_l1_min_fixes_builder_role_pg.py` | ci.yml :: db-integration-tests :: TI-l1-min-fixes-001 — L1 MV-refresh ownership skip + aborted-transaction guard against real Postgres |
| `platform/python-sidecar/tests/l3/gochara/test_a25_v41_candidate_writer.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_all_null_policy_db.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_builder_restricted_flow.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_complete_output_verification.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_contact_certification.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_disposable_db_guard.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_input_vector.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_migration_1240_static.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_p1_anchor.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_p1_contact_completeness.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_p1_support.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_r10_boundary_contract.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_r10_complete_records.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_r10_identity.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_r10_locking.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_r10_record_results.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_r10_runner_gate.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_r11_generation_wide.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_r11_p1_independence.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_r11_seal_brief.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_r12_boundary.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_r12_persisted_brief.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_r12_seal_job.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_r13_own_checkout.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_r13_producer.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_r13_sealed_boundary.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_r13_timeouts.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_r14_sealed_contacts.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_r15_amendments.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_r16_amendments.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_scope_completeness.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_stored_scope_real_sky.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_verification_job.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_window_verification_gate.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_a53_window_verification_roles.py` | ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped |
| `platform/python-sidecar/tests/l3/gochara/test_wp10_cutover.py` | ci.yml :: db-integration-tests :: C21 — WP10 cutover rehearsal gate against the CI Postgres service |
| `platform/python-sidecar/tests/l3/test_builder_role_overlay_writers.py` | ci.yml :: db-integration-tests :: C19 — overlay writers' SQL layer AS data_plane_builder against real Postgres |
| `platform/python-sidecar/tests/l3/test_builder_role_resonance_writer.py` | ci.yml :: db-integration-tests :: C7 — ka_gochara_resonance writer row build + insert AS data_plane_builder against real Postgres |
| `platform/python-sidecar/tests/l3/test_builder_role_v4_41_candidate.py` | ci.yml :: db-integration-tests :: C15 — ka_gochara_v4_41_candidate writer SQL layer AS data_plane_builder against real Postgres |
| `platform/python-sidecar/tests/l3/test_ka_jivana_parva_circularity_guard.py` | shad-darshana-circularity-guard.yml :: circularity-guard-live :: Run the Circularity Guard — static census (defense in depth, DB-free); shad-darshana-circularity-guard.yml :: circularity-guard-live :: Run the Circularity Guard — empirical live-DB invariance proof |
| `platform/python-sidecar/tests/test_ga4_chandra_bala_birth_sign_pg.py` | ci.yml :: db-integration-tests :: TI-l1-panchanga-moon-sign-001 — ga_panchanga birth-Moon-sign position-fact read against real Postgres |
| `platform/python-sidecar/tests/test_ga_vichara_identity_and_asof.py` | ci.yml :: db-integration-tests :: TI-l1-vichara-writer-001 — ga_vichara writer identity/as-of tests + migration 920 digest against real Postgres |
| `platform/python-sidecar/tests/test_karaka_readers_pg.py` | ci.yml :: db-integration-tests :: TI-s-l1-integration-001 — karaka-role readers (ga_vargas, ga_dashas, ga_structural karaka web) against real Postgres |
| `platform/python-sidecar/tests/test_l0_ontology.py` | ci.yml :: db-integration-tests :: Nirmāṇa L0 — migration 628 exact digest contracts and ontology co-writer retry |
| `platform/python-sidecar/tests/test_pratijna_v4_snapshot_properties.py` | ci.yml :: pratijna-v4-fixture-property-tests :: pytest — PRATIJÑĀ v4 CI-tier property tests |

### Unresolved dynamic steps

- ci.yml :: governance-tool-tests-shard :: pytest — governance tool tests (shard ${{ matrix.shard }}/3): dynamic file list — not resolved statically
- ci.yml :: governance-gates-gochara :: pytest — slow real-ephemeris shard ${{ matrix.leg }} (required; budget 20 min): dynamic file list — not resolved statically

### Full TSV

```
file	needs_db_why	runs_with_db_in_ci	runs_without_db_in_ci	integration_marker
platform/python-sidecar/bodha_writers/__tests__/test_l2_data_plane_contracts.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/ga_writers/__tests__/test_ga_vargas_integrity_nonvacuity_and_acceptance.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/ga_writers/__tests__/test_l1_min_fixes_builder_role_pg.py	direct reference: psycopg,dsn	ci.yml :: db-integration-tests :: TI-l1-min-fixes-001 — L1 MV-refresh ownership skip + aborted-transaction guard against real Postgres	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	module
platform/python-sidecar/ga_writers/__tests__/test_vimshottari_independent_verifier.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/pipeline/orchestrator/tests/test_mr39_idle_timeout_connection_setup.py	direct reference: psycopg,dsn,disposable-pg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/pipeline/orchestrator/tests/test_s7lock_guc_hardening.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_class_lifetime_counts.py	direct reference: psycopg	NEVER		
platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_cohort.py	direct reference: psycopg	NEVER		
platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_dignity_reference.py	direct reference: psycopg	NEVER		
platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_muhurta_lattice.py	direct reference: psycopg	NEVER		
platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_ontology.py	direct reference: psycopg	NEVER		
platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_parihara_rules.py	direct reference: psycopg	NEVER		
platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_reference.py	direct reference: psycopg	NEVER		
platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_sky_calendar.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_texts.py	direct reference: psycopg	NEVER		
platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bo_pratijna.py	direct reference: psycopg	NEVER		
platform/python-sidecar/pipeline/orchestrator/writers/tests/test_mi_sankalpa.py	direct reference: psycopg	NEVER		
platform/python-sidecar/services/gochara_v3/tests/test_context_moorti_wiring.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates-gochara :: pytest — gochara fast dirs + unmarked gochara_v3 tests (required); ci.yml :: governance-gates-gochara :: pytest — non-gating benchmark (continue-on-error; NOT a gate)	some
platform/python-sidecar/services/gochara_v3/tests/test_mr15_av_gate_bhava_num_fix.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates-gochara :: pytest — gochara fast dirs + unmarked gochara_v3 tests (required); ci.yml :: governance-gates-gochara :: pytest — non-gating benchmark (continue-on-error; NOT a gate)	some
platform/python-sidecar/services/ka_kshetra/tests/test_stage0_kinematics.py	direct reference: psycopg	NEVER		
platform/python-sidecar/services/ka_kshetra/tests/test_stage2_promise.py	direct reference: psycopg	NEVER		
platform/python-sidecar/tests/l0/test_bg_ephemeris_writer_columns.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l0/test_l0_orphan_census.py	direct reference: dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l2/test_b6_eval_harness.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	module
platform/python-sidecar/tests/l2/test_bo22.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/l2/test_bo_upaya_preamble_strip.py	uses fixture 'db_conn' from tests/l2/conftest.py (fixture body references psycopg)	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l2/test_l2_node_orphan_census.py	direct reference: dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l2/test_l2_semantic_corrections.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l2/test_l2_wrapper_real_pg.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/l2/test_l2_wrapper_shadow_real_pg.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/l2/test_n8_earned_signal_detectors.py	direct reference: psycopg,dsn,disposable-pg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a25_final_edge_projection.py	direct reference: disposable-pg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a25_teardown_keeps_registry_row_pg.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a25_v41_candidate_writer.py	direct reference: dsn	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a25_v41_candidate_writer_pg.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_all_null_policy_db.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_am5_writer.py	direct reference: psycopg,disposable-pg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_aspect_span.py	imports from sibling suite test_a53_record_store (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_builder_restricted_flow.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_complete_output_verification.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_contact_certification.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_disposable_db_guard.py	direct reference: psycopg,dsn	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_ephemeral_tier_rule.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_input_vector.py	direct reference: psycopg,disposable-pg	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_inventory.py	direct reference: psycopg,dsn,disposable-pg,require-db-gate	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_member_geometry.py	imports from sibling suite test_a53_window_verification_gate (imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate))	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_migration_1240_static.py	imports from sibling suite test_a53_window_verification_gate (imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate))	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_moon_on_demand.py	imports from sibling suite test_a53_record_store (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_moon_scope_domain.py	direct reference: psycopg,disposable-pg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_p1_anchor.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_p1_contact_completeness.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_p1_house_descriptor.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_p1_support.py	direct reference: psycopg,disposable-pg	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_r10_boundary_contract.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_r10_complete_records.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_r10_identity.py	direct reference: psycopg	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_r10_locking.py	direct reference: psycopg	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_r10_record_results.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_r10_runner_gate.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_r11_generation_wide.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_r11_p1_independence.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_r11_seal_brief.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_r12_boundary.py	direct reference: psycopg	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_r12_persisted_brief.py	direct reference: psycopg	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_r12_seal_job.py	direct reference: psycopg	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_r13_own_checkout.py	imports from sibling suite test_a53_r10_complete_records (imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate))	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_r13_producer.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_r13_sealed_boundary.py	direct reference: psycopg	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_r13_timeouts.py	direct reference: psycopg	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_r14_sealed_contacts.py	direct reference: psycopg,dsn,disposable-pg	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_r15_amendments.py	direct reference: psycopg	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_r16_amendments.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_record_store.py	direct reference: psycopg,dsn,disposable-pg,require-db-gate	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_rule_registry_versions.py	imports from sibling suite test_a53_record_store (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_scope_completeness.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_stored_scope_real_sky.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_verification_job.py	direct reference: psycopg	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_version_selection.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_window_sweep_pg.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_window_verification_gate.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_window_verification_roles.py	imports from sibling suite test_a53_inventory (direct reference: psycopg,dsn,disposable-pg,require-db-gate)	ci.yml :: db-integration-tests :: Pravāha A5.3 — migration 1240 / 1233 live-DB suites (window verification gate, roles, seal flows, P1 anchor) — REQUIRED, never skipped	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_a53_writer_native_types.py	direct reference: psycopg,disposable-pg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_b_binding_conformance.py	uses fixture 'conn' from tests/l3/gochara/conftest.py (fixture body references psycopg,dsn)	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_g10_digest_spec_1086.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_node_series_pin.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_node_series_pin_w2g.py	imports from sibling suite test_node_series_pin (direct reference: psycopg,dsn)	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_step06_enumeration.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_step06a_class_context.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_step06b_angular_m1.py	imports from sibling suite test_step06b_windows_projection (direct reference: psycopg,dsn)	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_step06b_per_instant_permission.py	imports from sibling suite test_step06b_windows_projection (direct reference: psycopg,dsn)	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_step06b_tara_testimony.py	imports from sibling suite test_step06b_windows_projection (direct reference: psycopg,dsn)	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_step06b_three_field_valence.py	imports from sibling suite test_step06b_windows_projection (direct reference: psycopg,dsn)	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_step06b_windows_projection.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_vedha_interval_gate.py	imports from sibling suite test_step06b_windows_projection (direct reference: psycopg,dsn)	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_wp10_cutover.py	direct reference: psycopg,dsn,require-db-gate	ci.yml :: db-integration-tests :: C21 — WP10 cutover rehearsal gate against the CI Postgres service	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_wp12_vedha_fingerprint.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_wp12_vedha_unsourced.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_wp4_decomposed.py	uses fixture 'conn' from tests/l3/gochara/conftest.py (fixture body references psycopg,dsn)	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_wp6_ledger.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_wp7_sentinel.py	uses fixture 'conn' from tests/l3/gochara/conftest.py (fixture body references psycopg,dsn)	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_wp9_m8_vedha_exceptions.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_wp9_overlays_kernel.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/gochara/test_wp9_stamp_columns.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/ka_kshetra/test_dhara_parity.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/l3/test_bhavishya_p0_safety.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/test_builder_role_ka_gochara_windows_v2.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/test_builder_role_overlay_writers.py	direct reference: psycopg,dsn	ci.yml :: db-integration-tests :: C19 — overlay writers' SQL layer AS data_plane_builder against real Postgres	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/test_builder_role_resonance_writer.py	direct reference: psycopg,dsn	ci.yml :: db-integration-tests :: C7 — ka_gochara_resonance writer row build + insert AS data_plane_builder against real Postgres	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/test_builder_role_v4_41_candidate.py	direct reference: psycopg,dsn	ci.yml :: db-integration-tests :: C15 — ka_gochara_v4_41_candidate writer SQL layer AS data_plane_builder against real Postgres	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/test_disposable_db_guard.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/test_i4_i5_output_digest_specs.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l3/test_ka_dasha_kala.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/l3/test_ka_jivana_parva_circularity_guard.py	direct reference: psycopg,dsn	shad-darshana-circularity-guard.yml :: circularity-guard-live :: Run the Circularity Guard — static census (defense in depth, DB-free); shad-darshana-circularity-guard.yml :: circularity-guard-live :: Run the Circularity Guard — empirical live-DB invariance proof	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/l3/test_ka_kshetra_cohort_client.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/l3/test_ka_kshetra_migration_487_integration.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/l3/test_ka_kshetra_stage6_salience.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/l3/test_resonance_rebuild_rehearsal.py	direct reference: dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/l5/test_mi_bhara_circularity_guard_w2.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/l5/test_mimamsa_multiplier.py	direct reference: dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_a1_telemetry_upsert_guard.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_argala_migration_1219_sql.py	direct reference: disposable-pg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_b1_forensic_gate.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_b6_disposable_guard.py	direct reference: dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_bg_sarvatobhadra_grid_throughput.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_cr131_gochara_db_reachability.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_el19_saham_recompute.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_f188_mi_gunanaka_count_sql.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_f_a2_d6_executor.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_ga4_chandra_bala_birth_sign.py	direct reference: dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_ga4_chandra_bala_birth_sign_pg.py	direct reference: psycopg,dsn	ci.yml :: db-integration-tests :: TI-l1-panchanga-moon-sign-001 — ga_panchanga birth-Moon-sign position-fact read against real Postgres	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	module
platform/python-sidecar/tests/test_ga_vichara_identity_and_asof.py	direct reference: psycopg,dsn	ci.yml :: db-integration-tests :: TI-l1-vichara-writer-001 — ga_vichara writer identity/as-of tests + migration 920 digest against real Postgres	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_gochara_grammar.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_gochara_intensity.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_gochara_provision_roles_script.py	direct reference: psycopg,dsn,disposable-pg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_gochara_sealer_stage_secrets_script.py	direct reference: dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_has_writer_completeness.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_ka_gochara_sweep.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_karaka_readers_pg.py	direct reference: psycopg,dsn	ci.yml :: db-integration-tests :: TI-s-l1-integration-001 — karaka-role readers (ga_vargas, ga_dashas, ga_structural karaka web) against real Postgres	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	module
platform/python-sidecar/tests/test_l0_ontology.py	direct reference: psycopg	ci.yml :: db-integration-tests :: Nirmāṇa L0 — migration 628 exact digest contracts and ontology co-writer retry	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_l5_reference_resolution_ledger_design.py	direct reference: psycopg,disposable-pg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_mi_bhavisya_append_only.py	direct reference: psycopg,disposable-pg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_migration_1243_inert_registry_rows.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_migration_1255_builder_reference_grants.py	direct reference: psycopg,disposable-pg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_migration_1259_integrity_scope_own_output.py	direct reference: psycopg,disposable-pg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_migration_1275_chart_delete_per_chart_tables.py	direct reference: psycopg,disposable-pg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_migration_1302_revoke_orchestrator_windows.py	direct reference: psycopg,disposable-pg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_migration_527_generation_catalog_only.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_675_paddhati_arbitration_role.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_676_muhurta_seva_depends_on.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_677_o10_authority_profile.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_678_parva_volume_explanation.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_679_parva_level_column.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_730_vighnakara_depends_on.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_731_conc7_size_sql.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_848_dasha_kala_proxy_probe.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_849_tulana_health_probe.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_850_muhurta_seva_health_probe.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_852_vedha_gochara_expected_volume.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_853_kota_chakra_expected_volume.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_854_gochara_expected_volume.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_855_moorti_nirnaya_expected_volume.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_856_vighnakara_expected_volume.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_857_bhavishya_lekha_expected_volume.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_858_jivana_parva_expected_volume.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_859_avadhi_expected_volume.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_860_service_assets_expected_volume.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_861_gochara_resonance_expected_volume.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_862_kala_darshana_expected_volume.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_863_kalasutra_expected_volume.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_864_yojaka_expected_volume.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_865_gochara_v3_century_expected_volume.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_866_sangam_expected_volume.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_migration_867_kshetra_expected_volume.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_mimamsa_outcome.py	direct reference: dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_mimamsa_prediction_ledger.py	direct reference: dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_permission_curve_route.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_phala_muhurta.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_phala_phaladesa.py	direct reference: dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_pratijna_v4_snapshot_properties.py	direct reference: psycopg,dsn,docker-postgres	ci.yml :: pratijna-v4-fixture-property-tests :: pytest — PRATIJÑĀ v4 CI-tier property tests	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_r6a1_neecha_bhanga.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_r6a3_d9_cross_check_redemption.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_sd_eventreg_durable_register.py	direct reference: psycopg,dsn	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	
platform/python-sidecar/tests/test_w2g_validations.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline	some
platform/python-sidecar/tests/test_yoga_formation_band_route.py	direct reference: psycopg	NEVER	ci.yml :: governance-gates :: pytest — pyjhora_adapter + pipeline
```

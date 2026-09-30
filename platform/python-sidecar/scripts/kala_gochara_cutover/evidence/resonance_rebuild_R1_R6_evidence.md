# Evidence — A5.4 resonance_rebuild_R1_R6 (FABLE v3.0 T0-12, finding #9)

Date: 2026-09-30. Branch: pravaha/a5-tier0s-repairs (worktree pravaha-a5).

**No production write was made at any point.** Production PostgreSQL was not
even readable from this workspace (proxy up on 127.0.0.1:5433 but
password-gated; credentials not available to the agent and `.env` files are
off-limits) — so the disposable evidence below is synthetic-fixture, executed
through the REAL writer code path, per the item brief's fallback clause. What
remains for the governed (native-only) run is listed in §5.

## 1. Test suite (deliverable 1)

Command (worktree `platform/python-sidecar`, system `python3`, pytest 9.1.1):

```
python3 -m pytest tests/l3/gochara/test_wp3c_resonance_corrections.py \
    tests/l3/test_ka_gochara_resonance.py \
    tests/l3/gochara/test_m6_derived_target_rows.py \
    services/ka_gochara_resonance/tests -q
```

Result: **203 passed, 0 failed** (breakdown: 27 + 39 + 41 + 6 + 90).

Coverage audit vs R-rules — every rule already has golden, mutation-sensitive
tests in `tests/l3/gochara/test_wp3c_resonance_corrections.py`; no new tests
were needed:

| Rule | Tests |
|---|---|
| R-1 (positive-only sensitive targets; `not_gandanta` et al. never emitted) | `test_fixture_negative_case_produces_zero_rows`, `test_all_four_negative_spellings_produce_zero_rows`, `test_unknown_value_dropped_and_counted_not_silent`, `test_positive_vocabulary_is_the_pinned_set`, `test_subject_position_absent_honest_unavailable` |
| R-2 (arudha = sign-level interval; cusp placeholder never a degree) | `test_fixture_arudha_row_references_sign_fact_only`, `test_missing_sign_value_is_unavailable_not_cusp_resolved` |
| R-3 (yoga live re-validation; drift surfaced in notes) | `test_firing_row_constituents_carried_in_report`, `test_dangling_yoga_id_produces_no_row_and_surfaces_in_notes`, `test_bhanga_active_carried_as_qualifier_not_weight`, `test_r3_dropped_yoga_id_surfaces_in_next_build_notes` |
| R-4 (lord whole-sign resolution; unqualified on rulership gap) | `test_fixture_lord_whole_sign_resolved`, `test_missing_rulership_row_is_unqualified`, `test_empty_rulership_table_is_unqualified_not_silent_fallback`, `test_missing_lagna_fact_is_unavailable`, `test_lord_graha_position_absent_is_unavailable`, drift guard `test_sign_lords_copy_matches_chart_reader_v4_drift_guard` |
| R-5 (first root retained; qualifier preserved; discards counted) | `test_afflicted_qualifier_preserved_on_clean_ref`, `test_compound_qualifier_applies_to_each_token`, `test_multiple_roots_first_retained_discard_counted`, `test_no_report_no_behavior_change` |
| R-6 (target_resolution_state on every row; closed enum) | `test_every_emitted_row_carries_a_valid_state`, `test_notes_state_counts_sum_to_rows`, `test_migration_1071_exists_with_check_constraint`, `test_r1_r4_end_to_end_states_and_notes` |

Mutation-sensitivity spot checks (temporary in-place mutations, reverted with
`git checkout` immediately after; writer.py byte-identical before and after):

- R-1 mutation: `"gandanta": frozenset({"gandanta", "not_gandanta"})` →
  `test_wp3c_resonance_corrections.py`: **4 failed, 23 passed** (caught by
  `test_positive_vocabulary_is_the_pinned_set`, `test_r1_r4_end_to_end_states_and_notes`, +2).
- R-6 mutation: `target_resolution_state` key dropped from `_base_row` →
  wp3c + `test_ka_gochara_resonance.py`: **14 failed, 52 passed**.

## 2. Disposable-DB rehearsal (deliverable 2)

Script: `scripts/kala_gochara_cutover/resonance_rebuild_disposable_rehearsal.py`
(loopback-only guard; refuses any non-loopback DSN and the production proxy
port 5433, exit 4).

Target: fresh database `resonance_a54` on the disposable PG16 container
`gochara-wp6-disposable` (PostgreSQL 16.14, loopback 55435) — the established
rehearsal instance. Schema = the REAL migrations applied verbatim
(`platform/migrations/459_gochara_resonance_map.sql` +
`1080_..._target_resolution_state.sql`), plus minimal faithful DDL for the
writer's input tables (chart_facts, brahma_event_ontology, bg_transit_rules,
ga_yoga_firings, chart_dashas, reference_signs, asset_registry stub so 459
applies verbatim). Fixture reproduces finding #9's exact shape on the
canonical chart id: 176 sensitive-degree check facts, 154 negative-result
(`not_fired`/`not_gandanta`/`not_pushkara`/`none`), plus a pre-WP3c legacy
map partition whose 176 `sensitive_degree` targets key those facts, and a
prior-build yoga id (`yoga_demo_stopped`, fired=false) to exercise R-3 drift.

The REAL writer ran against the disposable DB:
`KaGocharaResonanceWriter().run(ctx)`; the harness owned and committed the
connection (the writer never commits, per its contract).

### Results (raw JSON preserved in the run output)

| Check | Before | After | Verdict |
|---|---|---|---|
| total rows (this chart) | 177 | 481 | rebuilt across all 11 target types |
| sensitive_degree targets | 176 | 105 | positive-only (R-1) |
| sensitive targets keyed to a negative-result check | **154** | **0** | R-1 satisfied |
| rows with NULL/invalid target_resolution_state | n/a (legacy rows) | **0** | R-6 satisfied |
| arudha rows keyed to fact_key='sign' facts | — | 67 of 67 (true) | R-2 satisfied |
| yoga refs not backed by a live fired=true firing | — | **0** | R-3 satisfied |
| lord rows | — | 51, all 'resolved'; `afflicted` qualifier on 6 rows | R-4/R-5 |
| resolution states | — | resolved 418, unavailable 63, unqualified 0 | honest states stored |

Writer's own build record (`WriterResult.notes` JSON, abridged):

- `sensitive_degree`: positive_kept 105, negative_dropped_zero_rows **735**
  (154 × per-class re-fetches), unknown_value_dropped 0, kept_subjects all 9 grahas.
- `arudha`: sign_level_interval true, cusp_placeholder_longitude_never_read
  true, invalid_sign_value_unavailable 10 (the deliberately invalid ARUDHA_A12
  sign value surfaced as honest 'unavailable' on every class that cites house
  12 — never resolved to the cusp placeholder).
- `yoga_constituent`: validated_ids [yoga_demo_bhanga, yoga_demo_gajakesari];
  **dropped_since_prior_build ["yoga_demo_stopped"]** — R-3 drift surfaced,
  not silent. bhanga qualifier carried on the bhanga firing.
- `lord`: rulership_source reference_signs; all 12 house lords resolved via
  whole-sign from LAGNA (Aries); 10L/11L → Saturn etc.
- `roots`: discarded_duplicates 0, first_root_retained true.

The disposable database was left in place for inspection
(`resonance_a54` on gochara-wp6-disposable) and can be dropped freely.

## 3. Governed production runbook (deliverable 3)

`scripts/kala_gochara_cutover/resonance_rebuild_R1_R6_runbook.md` —
pre-conditions, finding-#9 baseline queries, the governed rebuild path
(asset-scope build_runs rebuild executed by the orchestrator, or the
run_heavy_writer_standalone lifecycle pattern), post-verification queries
(negative-result targets must go to 0), rollback via a pre-rebuild backup
table, and the explicit statement that **only the native executes it**.

## 4. What was NOT done / remains native-only (deliverable honesty)

- **The production rebuild itself was NOT run** — NATIVE-ONLY write. The
  runbook §0–§3 is what the native executes on the governed path.
- **Migration 1080's production application** is a precondition the runbook
  verifies, not something this step did (1080 is a design artifact; applied
  only on the disposable instance here).
- The disposable rehearsal uses synthetic chart_facts (production was
  unreachable read-only from this workspace). The governed run must re-run the
  §1 baseline queries on production first: if the real negative count differs
  from 154, that divergence is evidence to record, not a blocker — the
  post-check threshold (0 negative targets) is absolute either way.
- `enrichment.py`'s read-side arudha resolution remains the documented gap
  named in the writer header (out of scope for T0-12).

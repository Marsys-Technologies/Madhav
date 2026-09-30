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


## 6. Rework run (ASTRA_REVIEW_A5_4 P1-7 / P1-8) — 2026-09-30, FAILING acceptance check

Reworked rehearsal (`resonance_rebuild_disposable_rehearsal.py`, exit 1 on any
violated property) run live against the gochara-wp6-disposable PG16 container.
Disposable identity by construction: the run CREATED database
`rehearsal_a54_20260930151025_89df62` over the loopback maintenance DSN, verified
`current_database()` equality and zero user tables before any DDL/DML, and
DROPPED it afterwards (`database_dropped: True`; server
address diagnostic 172.17.0.5 — a container
address, recorded, not a discriminator).

Acceptance: **passed = True**, failures = [].

| Check | Value | Rule |
|---|---|---|
| fixture control (before) | 154 negative / 176 sensitive targets | must be 154/176 |
| R-1 negative-result sensitive targets (after) | **0** | must be 0 |
| R-1 positive control: sensitive rows kept / keyed to positive facts | 105 / 105 | > 0 and equal |
| refs: NULL / dangling / non-uuid target refs (NOT EXISTS) | 0 | must be 0 |
| R-6 rows with NULL/invalid state; partition total | 0; 481 | 0; > 0 |
| resolution states | {'resolved': 418, 'unavailable': 63} | recorded |
| R-2 arudha rows / all keyed to fact_key='sign' | 67 / True | > 0 and true |
| R-2 control: invalid ARUDHA_A12 surfaced 'unavailable' | 10 rows | > 0 |
| R-3 yoga rows / refs not live-fired | 19 / 0 | > 0 / 0 |
| R-3 drift: dropped_since_prior_build | ['yoga_demo_stopped'] | == ['yoga_demo_stopped'] |
| R-4 lord rows / states | 51 / {'resolved': 51} | > 0 / all resolved |
| R-5 afflicted qualifier rows / expected from signature models | 6 / 6 | equal, > 0 |
| notes.sensitive_degree | {'kept_subjects': ['JUP', 'KET_MEAN', 'MAR', 'MER', 'MOON', 'RAH_MEAN', 'SAT', 'SUN', 'VEN'], 'negative_dropped_zero_rows': 735, 'positive_kept': 105, 'unknown_value_dropped_zero_rows': 0} | negative_dropped_zero_rows is the PER-CLASS exclusion counter (735 for 154 facts), never required to equal 154 |
| idempotent rerun (content digest equal) | True | must be true |
| post-rebuild content digest | {'count': 481, 'digest': '3fdac1f46bcc72a95916fc510b375301'} | recorded |

Snapshot / rollback rehearsal (the runbook's own statements, from
`resonance_rebuild_backup_sql.py`):

| Step | Result |
|---|---|
| snapshot table (unique per chart × stamp; plain CREATE TABLE) | `gochara_resonance_map_snap_482012f1_20260930151025` |
| recorded count / content digest; equals live preimage | 177 / `6d250468f359785360e8f48eba26f696`; True |
| rollback with a WRONG recorded digest | refused before any DELETE: `ROLLBACK REFUSED: snapshot gochara_resonance_map_snap_482012f1_20260930151025 is stale or incomplete (count 177 digest 6…`; partition untouched: True |
| rollback with the recorded pair | restored exact preimage (digest equal): True |
| foreign chart partition (11111111-…) | untouched throughout: True |
| rebuild after rollback reproduces the post-rebuild digest | True |

The production runbook (`resonance_rebuild_R1_R6_runbook.md`) was regenerated
from the same module: uniquely named snapshot (never IF NOT EXISTS), recorded
count/digest verification, refuse-unless-verified rollback with post-restore
verification, postconditions as MUST values with positive controls, NOT EXISTS
reference checks, and the 154-versus-counter confusion corrected.
`tests/l3/test_resonance_rebuild_rehearsal.py` holds the runbook to the
module's statements byte for byte and fails the acceptance function on every
violated property. The §2 result table above (154 → 0) is superseded by this
run's numbers, which are identical for the invariants it measured.


## 7. Rework r2 run (ASTRA_REVIEW_A5_4 v1.1 P1-6 / P1-7) — 2026-09-30

Destination cluster established BEFORE any DDL: `--expect-cluster-id
7690735150699565094` equal to `pg_control_system().system_identifier` on the
maintenance connection (a probe with `--expect-cluster-id 1` was REFUSED before
`CREATE DATABASE`; no `rehearsal_a54_*` database was left behind). Database
`rehearsal_a54_20260930170120_7ede95` created by the run and dropped afterwards
(`True`).

Acceptance: **passed = True**, failures = [].

Preimage certificate (typed full-row digest, ids and computed_at included):
snapshot `gochara_resonance_map_snap_482012f1_20260930170120` count 177, full-row digest
`befde32704af7097c8346a2fa9a2124d`, equal to the live preimage before the
destructive phase: True (content digest
`9a32a9f0c26152bf008482dcf2f9b6c8` recorded separately for the rerun comparison).

Exact identity sets (totals alone can be preserved by a transferred qualifier or
a substituted input — the sets cannot):

| Identity | expected | actual | equal |
|---|---|---|---|
| afflicted_rows | 6 | 6 | True |
| arudha_fact_ids | 12 | 12 | True |
| lord_rows | 51 | 51 | True |
| sensitive_fact_ids | 22 | 22 | True |
| yoga_ids | 2 | 2 | True |

Negative-result fact ids referenced: 0. Runbook R-5
EXCEPT pair executed: {'ontology_not_qualified': 0, 'qualified_not_in_ontology': 0} (both 0).

Rollback: wrong full-row certificate refused before any DELETE
(True; partition untouched True);
recorded certificate restored the exact preimage — full-row digest equal
True, content digest equal True;
foreign partition untouched True; rebuild after rollback reproduces the
post-rebuild content digest True.
R-1: 0 negative / 105 kept; total 481;
rerun content digest equal True.

## 8. Rework r3 run (ASTRA_REVIEW_A5_4 v1.2 P1-3 / P2-b) — 2026-09-30

Destination cluster asserted before any DDL (`--expect-cluster-id 7690735150699565094`
= `pg_control_system().system_identifier`). Database `rehearsal_a54_20260930180328_b456a4`
created by the run and dropped afterwards (True).

Acceptance: **passed = True**, failures = [].

Preimage certificate: snapshot `gochara_resonance_map_snap_482012f1_20260930180328` count 177,
full-row digest `019f69e1f85cf90b102db1ae2d6fcdd1`, equal to the live preimage
before the destructive phase: True.

Class-associated identities (`class:ref`) and the full retained-value tuples
(event_class, type, ref, weight, state, qualifier, uncited, citation) for the
exactly-determined types — expected from the writer's own eligibility rules per
class, never a global DISTINCT set:

| Identity | expected | actual | equal |
|---|---|---|---|
| afflicted_rows | 6 | 6 | True |
| arudha_rows | 67 | 67 | True |
| exact_row_tuples | 419 | 419 | True |
| lord_rows | 51 | 51 | True |
| sensitive_rows | 105 | 105 | True |
| yoga_rows | 19 | 19 | True |

Runbook identity pairs, both EXCEPT directions (actual − eligible, eligible − actual):
R-1 {'actual_not_expected': 0, 'expected_not_actual': 0}, R-2 {'actual_not_expected': 0, 'expected_not_actual': 0}, R-3 {'actual_not_expected': 0, 'expected_not_actual': 0},
R-5 {'ontology_not_qualified': 0, 'qualified_not_in_ontology': 0}. Retained-value invariant violations (weight / provenance /
resolution state / qualifier, each against its own source): 0.
Negative-result fact ids referenced: 0.

Detector positive controls (each mutation applied inside a savepoint and rolled
back; every per-class count and every global target_ref set preserved, so a
totals-only or global-DISTINCT acceptance would still pass):

| Control | counts preserved | global id sets preserved | measured (rows flagged) | detected |
|---|---|---|---|---|
| arudha_class_swap | True | True | r1=(0, 0) r2=(2, 2) r3=(0, 0) r5=(0, 0) values=0 | True |
| provenance_flipped | True | True | r1=(0, 0) r2=(0, 0) r3=(0, 0) r5=(0, 0) values=2 | True |
| qualifier_transferred | True | True | r1=(0, 0) r2=(0, 0) r3=(0, 0) r5=(1, 1) values=2 | True |
| resolution_state_flipped | True | True | r1=(0, 0) r2=(0, 0) r3=(0, 0) r5=(0, 0) values=2 | True |
| sensitive_class_swap | True | True | r1=(2, 2) r2=(0, 0) r3=(0, 0) r5=(0, 0) values=0 | True |
| weight_changed | True | True | r1=(0, 0) r2=(0, 0) r3=(0, 0) r5=(0, 0) values=1 | True |
| yoga_class_swap | True | True | r1=(0, 0) r2=(0, 0) r3=(2, 2) r5=(0, 0) values=2 | True |

Map restored after the controls: True; post-control content digest
equals the rerun digest: True.

Rollback (P2-b): full certificate recorded BEFORE the refusal probe
`429049b70ebe485cf0f6f80ab7cc12ec` (count 481) and AFTER it
`429049b70ebe485cf0f6f80ab7cc12ec` (count 481) — equal:
True; wrong certificate refused before any DELETE:
True; recorded certificate restored the exact preimage — full-row digest
equal True, content digest equal True;
foreign partition untouched (full-row certificate AND content digest): True;
rebuild after rollback reproduces the post-rebuild content digest: True.
After counts by type: {'arudha': 67, 'bhava': 67, 'bhava_arudha': 67, 'dasha_lord_portfolio': 43, 'gulika_mandi_distance': 2, 'karaka': 43, 'lord': 51, 'mechanism_node': 9, 'sensitive_degree': 105, 'yamakantaka_difference': 8, 'yoga_constituent': 19}; rerun content digest equal True.

## 9. Rework r5 run (ASTRA_REVIEW_A5_4 v1.3 amendments 1 / 3 / P2) — 2026-10-01

Destination cluster asserted before any DDL (`--expect-cluster-id 7690735150699565094`).
Database `rehearsal_a54_20260930200746_0be947` created by the run and dropped afterwards (True).

Acceptance: **passed = True**, failures = [].

**Schema derived from the checked-in migrations** (both runner roots, migrate.ts:834-835) —
verbatim: 388_brahma_ghatana_ontology.sql, 456_brahma_event_ontology_dr13_shapes.sql, 459_gochara_resonance_map.sql, 550_gochara_resonance_map_event_class_fk.sql, 1080_nirmana_l3_gochara_resonance_target_resolution_state.sql; extracted DDL (CREATE TABLE / ALTER TABLE / CREATE
INDEX ON / DO-blocks that ALTER, seeds and bookkeeping excluded): `bg_transit_rules` ← 266_bg_transit_tables.sql (3), 397_bg_transit_av_gates.sql (2); `chart_dashas` ← 206_ga3_supporting_tables.sql (4), 211_ga7_dashas_kp_sublevel.sql (26), 414_chart_dashas_kp_sublevel_unique_key.sql (2), 415_chart_dashas_condition_lookup_idx.sql (1), 428_chart_dashas_v11_dead_column_drop.sql (2), 652_nirmana_l1_ga_dashas_scope_cap_sentinel_vocab.sql (2), 882_nirmana_l1_ga_dashas_integrity_check_perf.sql (2); `chart_facts` ← 204_chart_facts.sql (6), 206_ga3_supporting_tables.sql (5), 209_ga5_sensitive_points_mv.sql (6), 215_chart_facts_formula_id.sql (3), 216_chart_facts_partial_indexes.sql (2), 359_fix_build_runs_active_index.sql (1), 429_ga_sade_sati_cycle_uniqueness_gate.sql (2), 539_chart_facts_verification_pass_status_check.sql (1); `ga_yoga_firings` ← 240_ga_yoga.sql (3), 411_ga_yoga_constituent_bala_strength.sql (1), 434_lane3_detector_registry_yogas.sql (1); `reference_signs` ← ws2_l0_reference.sql (2); stub: asset_registry
only. Column types observed: `brahma_event_ontology.citations` = `ARRAY` (TEXT[]),
`chart_facts.fact_id` = `text`.

**Class universe** = the writer's `TARGET_EVENT_CLASSES` (26 classes).
Retained non-eligible ontology rows present: ['birth_anchor'];
`birth_anchor` present in the ontology: True; `birth_anchor`
rows in the map: 0; map classes == eligible set:
True; SIGNATURE_MODELS mirror == migration seed:
True (diff []).

Preimage certificate: snapshot `gochara_resonance_map_snap_482012f1_20260930200748` count 177, full-row digest
`d236b0935d05fea8270ece77ccef9697`, equal to the live preimage: True.

Class-associated identities and full retained-value tuples (expected from the migration-seeded
ontology's own signature models and citations, scoped to the eligible classes):

| Identity | expected | actual | equal |
|---|---|---|---|
| afflicted_rows | 6 | 6 | True |
| arudha_rows | 67 | 67 | True |
| exact_row_tuples | 419 | 419 | True |
| lord_rows | 51 | 51 | True |
| sensitive_rows | 105 | 105 | True |
| yoga_rows | 19 | 19 | True |

Runbook identity pairs, both EXCEPT directions: R-1 {'actual_not_expected': 0, 'expected_not_actual': 0}, R-2 {'actual_not_expected': 0, 'expected_not_actual': 0},
R-3 {'actual_not_expected': 0, 'expected_not_actual': 0}, **R-4 (all lords) {'actual_not_expected': 0, 'expected_not_actual': 0}**, R-5 {'ontology_not_qualified': 0, 'qualified_not_in_ontology': 0}.
Retained-value invariant violations: 0. Negative-result fact ids
referenced: 0.

Detector positive controls (inside a savepoint, rolled back; the ten named records are REQUIRED
by `verify_acceptance` — P2):

| Control | counts | preserved counts / global id sets / applied | measured (rows flagged) | detected |
|---|---|---|---|---|
| arudha_class_swap | preserved (required) | True / True / True | r1=(0, 0) r2=(2, 2) r3=(0, 0) r4=(0, 0) r5=(0, 0) values=0 | True |
| birth_anchor_row_injected | changes by design | False / True / True | r1=(0, 0) r2=(0, 0) r3=(0, 0) r4=(0, 0) r5=(0, 0) values=1 | True |
| lord_token_missing | changes by design | False / True / True | r1=(0, 0) r2=(0, 0) r3=(0, 0) r4=(0, 1) r5=(0, 0) values=0 | True |
| lord_token_wrong | preserved (required) | True / True / True | r1=(0, 0) r2=(0, 0) r3=(0, 0) r4=(1, 1) r5=(0, 0) values=0 | True |
| provenance_flipped | preserved (required) | True / True / True | r1=(0, 0) r2=(0, 0) r3=(0, 0) r4=(0, 0) r5=(0, 0) values=2 | True |
| qualifier_transferred | preserved (required) | True / True / True | r1=(0, 0) r2=(0, 0) r3=(0, 0) r4=(0, 0) r5=(1, 1) values=2 | True |
| resolution_state_flipped | preserved (required) | True / True / True | r1=(0, 0) r2=(0, 0) r3=(0, 0) r4=(0, 0) r5=(0, 0) values=2 | True |
| sensitive_class_swap | preserved (required) | True / True / True | r1=(2, 2) r2=(0, 0) r3=(0, 0) r4=(0, 0) r5=(0, 0) values=0 | True |
| weight_changed | preserved (required) | True / True / True | r1=(0, 0) r2=(0, 0) r3=(0, 0) r4=(0, 0) r5=(0, 0) values=1 | True |
| yoga_class_swap | preserved (required) | True / True / True | r1=(0, 0) r2=(0, 0) r3=(2, 2) r4=(0, 0) r5=(0, 0) values=2 | True |

`lord_token_wrong` is the reviewer's replay (marriage:7L → marriage:2L, weight / state / citation /
qualifier preserved, counts and global id sets unchanged): caught in BOTH R-4 directions;
`lord_token_missing` in the second; `birth_anchor_row_injected` as a `class:not_eligible` value
violation. Map restored after the controls: True; post-control digest equals
the rerun digest: True.

Rollback: pre-refusal certificate `c04bfc33fc08aae9fc5e407fa97203c5` == post-refusal
`c04bfc33fc08aae9fc5e407fa97203c5`: True; wrong certificate
refused before any DELETE: True; exact preimage restored — full-row digest equal
True, content digest equal True; foreign
partition untouched: True; rebuild after rollback reproduces the digest:
True. After counts by type: {'arudha': 67, 'bhava': 67, 'bhava_arudha': 67, 'dasha_lord_portfolio': 43, 'gulika_mandi_distance': 2, 'karaka': 43, 'lord': 51, 'mechanism_node': 9, 'sensitive_degree': 105, 'yamakantaka_difference': 8, 'yoga_constituent': 19}; rerun content
digest equal True.

## 10. Rework r6 run (ASTRA_REVIEW_A5_4 v1.4 amendments 1 / 2 / P2) — 2026-10-01

Destination cluster asserted before any DDL (`--expect-cluster-id 7690735150699565094`).
Database `rehearsal_a54_20260930205009_910d7a` created by the run and dropped afterwards (True).
Schema derived from the checked-in migrations as in §9 (`citations` = `ARRAY`,
`chart_facts.fact_id` = `text`).

Acceptance: **passed = True**, failures = [].

**Fact references (amendment 1).** Every chart_facts row is minted by its producer's own id function
(16-hex semantic ids; 36 (subject, key) sensitive pairs across five ayanāṃśas). Fact-backed refs in the
map: 158; not producer-shaped: 0;
NULL / blank / dangling under the chart-scoped text-identity resolution: 0;
non-canonical-ayanāṃśa fact ids referenced: 0.

**Retained values (amendment 2).** Every emitted target type enumerated; value-invariant violations:
0; mechanism identity pair (both directions): {'actual_not_expected': 0, 'expected_not_actual': 0}.
Exact tuples now include the mechanism_node rows (weight from the cited rule's type through the writer's
contract) and the M-6 rows.

| Identity | expected | actual | equal |
|---|---|---|---|
| afflicted_rows | 6 | 6 | True |
| arudha_rows | 67 | 67 | True |
| exact_row_tuples | 424 | 424 | True |
| lord_rows | 51 | 51 | True |
| sensitive_rows | 91 | 91 | True |
| yoga_rows | 19 | 19 | True |

Runbook pairs: R-1 {'actual_not_expected': 0, 'expected_not_actual': 0}, R-2 {'actual_not_expected': 0, 'expected_not_actual': 0}, R-3 {'actual_not_expected': 0, 'expected_not_actual': 0},
R-4 {'actual_not_expected': 0, 'expected_not_actual': 0}, R-5 {'ontology_not_qualified': 0, 'qualified_not_in_ontology': 0}, mechanism {'actual_not_expected': 0, 'expected_not_actual': 0}.

Detector positive controls (thirteen named records REQUIRED; the clean baseline's contents validated —
P2): clean = {'dangling': 0, 'mech': [0, 0], 'r1': [0, 0], 'r2': [0, 0], 'r3': [0, 0], 'r4': [0, 0], 'r5': [0, 0], 'value_violations': 0}.

| Control | expectation | counts / id sets preserved / applied | measured (rows flagged) | detected |
|---|---|---|---|---|
| arudha_class_swap | counts + id sets preserved (required) | True / True / True | r1=(0, 0) r2=(2, 2) r3=(0, 0) r4=(0, 0) r5=(0, 0) mech=(0, 0) values=0 dangling=0 | True |
| birth_anchor_row_injected | count changes by design | False / True / True | r1=(0, 0) r2=(0, 0) r3=(0, 0) r4=(0, 0) r5=(0, 0) mech=(0, 0) values=1 dangling=0 | True |
| fact_ref_foreign_chart | id set changes by design (re-pointed ref) | True / False / True | r1=(1, 1) r2=(0, 0) r3=(0, 0) r4=(0, 0) r5=(0, 0) mech=(0, 0) values=1 dangling=1 | True |
| fact_ref_missing | id set changes by design (re-pointed ref) | True / False / True | r1=(1, 1) r2=(0, 0) r3=(0, 0) r4=(0, 0) r5=(0, 0) mech=(0, 0) values=1 dangling=1 | True |
| lord_token_missing | count changes by design | False / True / True | r1=(0, 0) r2=(0, 0) r3=(0, 0) r4=(0, 1) r5=(0, 0) mech=(0, 0) values=0 dangling=0 | True |
| lord_token_wrong | counts + id sets preserved (required) | True / True / True | r1=(0, 0) r2=(0, 0) r3=(0, 0) r4=(1, 1) r5=(0, 0) mech=(0, 0) values=0 dangling=0 | True |
| mechanism_weight_sign_flipped | counts + id sets preserved (required) | True / True / True | r1=(0, 0) r2=(0, 0) r3=(0, 0) r4=(0, 0) r5=(0, 0) mech=(0, 0) values=1 dangling=0 | True |
| provenance_flipped | counts + id sets preserved (required) | True / True / True | r1=(0, 0) r2=(0, 0) r3=(0, 0) r4=(0, 0) r5=(0, 0) mech=(0, 0) values=2 dangling=0 | True |
| qualifier_transferred | counts + id sets preserved (required) | True / True / True | r1=(0, 0) r2=(0, 0) r3=(0, 0) r4=(0, 0) r5=(1, 1) mech=(0, 0) values=2 dangling=0 | True |
| resolution_state_flipped | counts + id sets preserved (required) | True / True / True | r1=(0, 0) r2=(0, 0) r3=(0, 0) r4=(0, 0) r5=(0, 0) mech=(0, 0) values=2 dangling=0 | True |
| sensitive_class_swap | counts + id sets preserved (required) | True / True / True | r1=(2, 2) r2=(0, 0) r3=(0, 0) r4=(0, 0) r5=(0, 0) mech=(0, 0) values=0 dangling=0 | True |
| weight_changed | counts + id sets preserved (required) | True / True / True | r1=(0, 0) r2=(0, 0) r3=(0, 0) r4=(0, 0) r5=(0, 0) mech=(0, 0) values=1 dangling=0 | True |
| yoga_class_swap | counts + id sets preserved (required) | True / True / True | r1=(0, 0) r2=(0, 0) r3=(2, 2) r4=(0, 0) r5=(0, 0) mech=(0, 0) values=2 dangling=0 | True |

`fact_ref_missing` (a producer-shaped id no fact carries) and `fact_ref_foreign_chart` (the same id
minted for another chart, present in chart_facts) are each dangling; `mechanism_weight_sign_flipped`
(illness_acute saturn:unfavourable:h8, −1.0 → +1.0, everything else unchanged) is a
`weight:mechanism_rule_type` violation. Map restored after the controls: True;
post-control digest equals the rerun digest: True.

Rollback: pre/post-refusal certificates equal: True; wrong certificate
refused before any DELETE: True; exact preimage restored — full-row digest equal
True, content digest equal True; foreign
partition untouched: True; rebuild after rollback reproduces the digest:
True. Snapshot `gochara_resonance_map_snap_482012f1_20260930205011` count 177, full-row
digest `46d6b07d59e2aefcc83895e2969f0ee1`. After counts by type: {'arudha': 67, 'bhava': 67, 'bhava_arudha': 67, 'dasha_lord_portfolio': 43, 'gulika_mandi_distance': 2, 'karaka': 43, 'lord': 51, 'mechanism_node': 9, 'sensitive_degree': 91, 'yamakantaka_difference': 8, 'yoga_constituent': 19}; rerun content digest
equal True.

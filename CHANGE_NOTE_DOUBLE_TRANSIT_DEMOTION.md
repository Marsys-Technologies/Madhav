---
artifact: CHANGE_NOTE_DOUBLE_TRANSIT_DEMOTION.md
status: PROPOSED (travels with the PR; commit only, not pushed)
branch: kalayantra/demote-double-transit-testimony
worktree: /Users/Dev/worktrees.noindex/madhav/claude/kalayantra-demote-double-transit
base: origin/main a1a6a9e73 (2026-10-27)
rulings: DOUBLE-TRANSIT-PROVENANCE-20261027 (provenance audit) · FOURQ-CLOSURE-20261027 (panel closure: switched OFF)
audit: /Users/Dev/scratch.noindex/claude/madhav/20261027-doctrine-inventory/DOUBLE_TRANSIT_PROVENANCE_v0_1.md
placement: at the worktree root as the brief instructed; ROOT_FILE_POLICY.md §1 lists no change notes at root — the surrogate may move this file to 00_ARCHITECTURE/briefs/ before merge (see §10)
---

# Jupiter–Saturn double transit: switched off (FOURQ-CLOSURE-20261027)

## 1. What was decided, and how the scope evolved

The provenance audit (DOUBLE-TRANSIT-PROVENANCE-20261027) found (a) no classical source in the corpus for the Jupiter–Saturn
"double transit" rule — the "Phaladeepika ch.26 §double-gochara" passage migration 397 cited does not exist (migration 565
CORPUS_GAP; three independent reviews 2026-09-29; the sealed Pravāha v3.0 doctrine already labels P4 modern K.N. Rao practice,
`uncited_extension`) — and (b) one confirmed leakage: PR #651 (2026-07-20) widened the detection logic (the
`double_transit_mixed` occupation+aspect leg, OR-combined into permission generator #10, a bhava-target guard removed) so a
recorded specimen of the native would be detected.

The task started as a demotion to labelled testimony. Three coordinator amendments, then the panel closure
FOURQ-CLOSURE-20261027, changed the disposition to **switched OFF entirely**: generator #10 and its mirrors emit nothing; the
composition operators are deleted; kernel path P4 is disabled; the seven seed rows are `retired_pending_reauthor`; served
consumers return an honest empty/null with a reason. Re-admission only via a panel-verified classical citation and a
forward-only test. Everything below implements that final disposition; where an earlier (testimony) step was superseded the
code was rewritten, not layered.

## 2. Files touched and why

### Live engines (the served effect)
| File | Change |
|---|---|
| `platform/python-sidecar/services/gochara_intensity/permission.py` | Generator #10 `guru_shani_double_transit` stays REGISTERED (12-row table, `systems_considered` unchanged) but is never evaluated: no primitive, no composition, no sentence. It emits `retired_system_row(...)`: `active False`, `weight 0.0`, `state/status retired_pending_reauthor`, `ruling_ref FOURQ-CLOSURE-20261027`, `empty_reason` (§N.7.6). New `RETIRED_SYSTEM_IDS`, `SCORED_SYSTEM_WEIGHTS`, `scored_weight()`, `retired_system_row()`; `detail["retired_systems"]`, `detail["scored_weight_total"]`. The `composition` import is gone. `SYSTEM_WEIGHTS` is unchanged (see §3). Module docstring rewritten; the specimen-narrative comments removed. |
| `platform/python-sidecar/services/gochara_v3/engine.py` | Mirror: row 10 is `retired_system_row(...)`; `_check_guru_shani_from_context` kept as a stub returning the empty result (no ephemeris, no primitives); `detail["retired_systems"]`; the sade-sati N-15 branch unchanged. |
| `platform/python-sidecar/services/gochara_kernel/legacy_semantics.py` | Mirror of the weight semantics: `RETIRED_SYSTEM_IDS`, `SCORED_PERMISSION_SYSTEM_IDS`; `compute_permission` sums live ids only; `SYSTEM_WEIGHTS` and the 12 pinned ids unchanged. |
| `platform/python-sidecar/services/gochara_grammar/composition.py` | `double_transit` and `double_transit_mixed` DELETED (no live invoker remains); docstring item 2 records the deletion and both rulings; `itertools.combinations` import dropped; `__all__` = the five surviving operators. |
| `platform/python-sidecar/services/gochara_grammar/citations.py` | `DOUBLE_GOCHARA_PHALADEEPIKA_26` (the non-existent citation) struck from the module and from `__all__` (14 → 13). Added, outside `__all__`: `DOUBLE_TRANSIT_COMMENTARIAL_ATTRIBUTION` (the honest attribution the seven rows carry — byte-identical to migration 1412), `DOUBLE_TRANSIT_RULING_REF`, `FOURQ_CLOSURE_RULING_REF`, `STATUS_RETIRED_PENDING_REAUTHOR`, `RETIRED_CITATION_PREFIX`, `DOUBLE_TRANSIT_RETIRED_REASON`. |
| `platform/python-sidecar/services/gochara_grammar/primitives.py` | `sign_occupation` docstring: the specimen narrative and the reference to the deleted operator removed; the primitive itself stays (generic, cited). |
| `platform/python-sidecar/services/ka_gochara_resonance/writer.py` | Served consumer of the seven rows: `_build_mechanism_rows` skips a row whose `rule_type` is `double_transit` OR whose citation starts with `RETIRED_PENDING_REAUTHOR` (so a database before/after migration 1412 behaves the same), recording `retired_skipped`, `retired_ids` and the reason in the build report. The `double_transit: 0.75` weight entry is kept (unreachable) so the table is stable. |
| `platform/python-sidecar/routers/permission_curve.py` | Served route: a retired generator's points carry `status` and `empty_reason`; the response carries `retired_systems`. The 12-generator contract (`system_ids`) is unchanged. |
| `platform-mcp/src/tools/retrieval/register_gochara_windows.ts` | Comment only: `dominantGraha` no longer describes a preference for the guru_shani system (it is never active; the function already returns null rather than fabricating). |

### Kernel (ka_gochara_v5 — inert asset; P4 disabled through the kernel's own mechanism)
| File | Change |
|---|---|
| `platform/python-sidecar/services/gochara_rules/registry.py` | `DISABLED_PATHS = {"P4": {status retired_pending_reauthor, ruling FOURQ-CLOSURE-20261027, reason tier_withheld_by_ruling, provenance_ruling_ref}}` + `path_disabled()`; `FOURQ_CLOSURE_RULING(_TEXT)`, `DOUBLE_TRANSIT_PROVENANCE_RULING`, `STATUS_RETIRED_PENDING_REAUTHOR`. A NEW immutable row `P4@1.4.0` (`P4_TESTIMONY_VERSION`): `disabled True`, `status retired_pending_reauthor`, `operator_role testimony` (pending re-authoring — the only non-scoring value of the closed vocabulary), `ruling_ref FOURQ-CLOSURE-20261027`; registered only — not bound, not selected, in no supersession table; `H_TABLE_VERSIONS["1.4.0"]` = 1.3.0's table. The sealed rows P4@1.0.0–1.3.0 are NOT edited (B.8; they are persisted insert-if-absent and bound into the century build's identity). |
| `platform/python-sidecar/services/gochara_kernel/inventory.py` | `standing_exclusions()` now also yields every `DISABLED_PATHS` entry: P4 is pinned `excluded / tier_withheld_by_ruling / ruling:FOURQ-CLOSURE-20261027` for every class and every sealed version BEFORE any enumeration — no P4 obligation, interval, record or window is planned, built, admitted or served. |
| `platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py` | `VERIFIER_PATH_RULINGS["p4"]` — the verifier's independent copy of the ruling (told, never imported). `_applicable_rulings()` therefore carries FOURQ-CLOSURE-20261027 in the build identity (AM-16). |
| `platform/python-sidecar/services/gochara_kernel/evaluator.py` | `enumerate_p4_edges` returns `[]` when the P4 row at `rule_version` is disabled (the 1.4.0 row); the sealed rows' enumeration is byte-identical. |

### Trigger / admit lane
| File | Change |
|---|---|
| `platform/python-sidecar/services/kala_trigger/trigger.py` | One comment at `guru_shani_double_transit` (ledger id; stays UNWIRED); the `compute_trigger_currents` docstring no longer instructs callers to pass the fitted 0.2 for it. No behaviour change. |
| `platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py` | `TRIGGER_ADMITTED_ADDITIVE_WEIGHTS` loses `guru_shani_double_transit: 0.2` (a fitted artefact with no consumer: `compose_with_ka_sangam` applies the suppressive side only). The current is still computed and reported by `compute_trigger_currents`; it carries no weight. |

### Data
| File | Change |
|---|---|
| `platform/migrations/1412_bg_transit_rules_double_transit_testimony_reseal.sql` (NEW) | See §5. |
| `platform/scripts/seed/asset_registry_seed.ts` | `bg_transit_rules.english_description` = migration 1412's text (the seed's upsert writes this column; migration 1320's parity rule). |
| `platform/python-sidecar/brahmagyan/kala/convergence.py` | The two comment lines tying "Guru-Shani activation" / "Jupiter-Saturn opposition" to years of the native's life deleted. Comments only. |
| `00_ARCHITECTURE/CONDUCTOR/ws3/bphs_canon_batch_01.yaml` (BPHS.79.3.1), `bphs_canon_batch_03.yaml` (BPHS.80.2.1, BPHS.80.3.1), `kp_canon_batch_03.yaml` (KP.3.ch19.double_transit.1) | `verified: true` → `verified: null` + `verification_note: "LLM-extracted paraphrase; no page-anchored quote in corpus (audit 2026-10-27)"`. Checked first: no code or test reads `verified` from these files (`brahmagyan/bodha/_grounding_engine.py` loads the YAML but never reads that key; the f178/f182 tests check mantra fields only). The files' `metadata` blocks carry no verified count, so none was changed. |

### Tests (see §7)

## 3. Weight-normalisation effect (before / after)

`SYSTEM_WEIGHTS` is unchanged (12 entries, sum 1.0; the generator's 0.10 stays). The denominator of PERMISSION is still the
full declared table. Before: `permission = Σ_{active} w / 1.0` over 12 generators. After: generator #10 is never active and
weighs 0.0, so `permission = Σ_{active live} w / 1.0`. Consequences: every other generator's absolute contribution is
byte-identical (no silent re-scaling of a declared structural prior); the maximum attainable PERMISSION is 0.90 (it was 1.0);
at an instant where the old generator fired the value is lower by exactly 0.10, everywhere else identical. The alternative —
renormalising the denominator to 0.90 (the engine's N-15 sade-sati pattern) — was rejected: it would scale all eleven live
generators by 1/0.90 (e.g. vimshottari 0.16 → 0.178 effective), altering their declared priors at every instant and breaking
the WP3b legacy pin (`compute_permission({"vimshottari": True}) == 0.16`).

## 4. Kernel: how "P4 disabled" is realised, and its honest boundary

The kernel already owns an OFF switch for a path withheld by ruling — P5's `standing_exclusions()` entry — and that is what P4
now uses. The planner pins P4 `excluded / tier_withheld_by_ruling / ruling:FOURQ-CLOSURE-20261027` for every class and every
sealed version before it enumerates anything; the verifier is told independently; the ruling enters the build identity. The
registered disabled row stamps no edge. **Boundary, stated plainly:** the enumerator for the sealed P4 rows (1.0.0–1.3.0) is
unchanged and remains callable directly (tests and the verifier's re-derivation do call it); no build or serving path reaches it.
A global "P4 enumerates nothing at every version" would rewrite the kernel's DVI tier, final-rule contexts, inventory intervals
and the verifier's independent P4 derivation across ~10 modules and dozens of sealed tests on an inert asset — not done
(cockpit: minimal diff, no rebuild). **Consequence either way:** the sealed century build's P4 inventory pins and records were
produced with P4 included; its next re-verification under the current code will report the P4 grains as disagreeing with the
stored generation. That is the ruling taking effect, not a defect; no rebuild or backfill is triggered by this PR (owner stop
order), and none is required for the served effect (§2 live engines).

## 5. Migration 1412 (the seven seed rows)

* Rows: exactly the 7 `rule_type = 'double_transit'` rows. `classical_citation := 'RETIRED_PENDING_REAUTHOR (FOURQ-CLOSURE-20261027) — ' || attribution`; `rule_notes := 'retired_pending_reauthor: P4 switched off (ruling …; provenance …) — not served, not scored; …' || existing note`. ids, rule_type, graha, houses, phala unchanged; 76 = 43 + 26 + 7 unchanged, so the frozen `count(double_transit) = 7` and `count_sql` hold.
* Status column: **none exists** (`bg_transit_rules` = id, rule_type, graha, primary_house, vedha_house, phala, classical_citation, rule_notes; CHECKs on rule_type and the house ranges only; no enum). Nothing rejects the new text; the status therefore rides as a machine-readable citation prefix (precedent: the node vedha rows start with `UNSOURCED`, migration 1320). The migration's real-SQL test proves the UPDATE under the real DDL of 266/397, inspects `information_schema.columns` and `pg_constraint`, and runs the vedha loader (`vedha_house IS NOT NULL` rows only — unaffected) before and after.
* Integrity pin: guarded `replace()` of migration 1320's pin `dce17ed0…` → `19cf8768…`. Both hashes were computed with migration 613's exact query on a disposable Postgres (seed rows + 397's seven): the PRE hash reproduces 1320's pin exactly, the POST hash is the one pinned; the test re-derives both on every run.
* `english_description`: 1079's text ("…Saravali or Jataka Parijata") becomes false, so it is replaced (§N.7); the TS seed carries the same text (1320's parity rule; the seed's upsert writes the column).
* No DDL (the Kāla protected-window detector sees nothing); idempotent; refuses an unrecognised prior state; no rebuild — if 1320's governed rebuild has not yet run, the stored check stays FALSE for exactly the reason 1320 documents and becomes TRUE when it does.
* Consumers: `ka_gochara_resonance` skips retired rows (§2); the sky-calendar `double_transit` event_type (bg_sky_calendar — chart-independent Jupiter–Saturn conjunction geometry, 10 rows, frozen by migration 605) is a different artefact and is untouched.

## 6. Spec amendment

`00_ARCHITECTURE/GOCHARA_DESIGN_SPECS_v1_4.md` line 314 defines P4 as "scored". That file is FROZEN and is **not edited** by this
PR. Line 314 is amended by the decision record **DECISION_RECORD_P4_DEMOTION** travelling with this PR (placeholder path, supplied
by the surrogate: `00_ARCHITECTURE/decisions/DECISION_RECORD_P4_DEMOTION.md`), which records FOURQ-CLOSURE-20261027: P4 is
disabled (`retired_pending_reauthor`), its `operator_role` left as `testimony` pending re-authoring, nothing admitted or scored.
The registry's P4@1.4.0 row and `DISABLED_PATHS["P4"]` cite the record in their comments.

**Superseded decision (recorded, not edited):** `ND-H-20261005_DECISION_BY_DELEGATE.md` — the "CORE + DVI houses" amendment
whose DVI ("double-transit-only") tier exists for P4 alone — is superseded by this switch-off: with P4 a standing exclusion the
DVI tier admits nothing anywhere. The document is left as is.

## 7. Tests

Removed (they encoded a recorded event of the native as the acceptance criterion — the leakage pattern the ledger now forbids —
or tested deleted code): `test_gochara_grammar.py::test_composition_2_double_transit_marriage_specimen`, `…2b_…end_to_end_rasi_fix`,
`…2c_double_transit_mixed_…`; `test_gochara_intensity.py::test_permission_guru_shani_double_transit_fires_for_real_marriage_house`.
Retained (primitive-level, the primitive stays): the `sign_occupation` and `drishti_contact` rasi-fallback tests.

Adapted (they pinned P4 as planned/included or the composition operator as present): `test_a53_window_evaluator.py`,
`test_nd_h_builder_tiers.py` (three inventory tests; `_assert_p4_switched_off`), `test_p06_final_rule_verification.py` (the
verifier's exclusion copy; the P4-intervals test), `test_n15_sade_sati_testimony.py`, `test_a58_honest_tier_readers.py` (state
vocabulary), `wp8synth.py` (denominator from `declared_prior_weight`), `test_ka_gochara_resonance.py`,
`test_w29_citation_resolution.py` (13 constants), `gochara_v3/tests/test_lambda_v3_bounded.py` and
`test_self_normalizing_thresholds.py` (I2/AC6 sentinels → the five surviving operators + the deletion).

Added: generator #10 emits an empty result with reason and no primitive runs (`test_gochara_intensity.py`); weights split
(`…retired_split…`); operators deleted + no citation names the passage (`test_gochara_grammar.py`); legacy mirror
(`test_wp3b_legacy_semantics.py`); registry row/datum + sealed rows untouched + not bound/selected (`test_rp.py`); planner
excludes P4 for a **synthetic chart** under both profiles, disabled row stamps no edge, ruling in the identity
(`test_a53_window_evaluator.py`); resonance writer skips retired rows with reason; **golden served-route test**
`test_permission_curve_route.py::test_route_serves_the_retired_generator_as_an_empty_series_with_status_and_reason`
(real `compute_permission`, stubbed DB, primitives that fail if called); migration 1412 real-SQL + static tests
(`tests/l0/test_migration_1412_double_transit_testimony.py`).

### Results (worktree, 2026-10-27; Python 3.13.7 / pytest 9.0.3 from the project venv; disposable PostgreSQL 17 for the migration tests)
* Touched modules + `tests/l3/gochara_rules` + the adapted kernel files: `1171 passed, 51 skipped, 8 deselected, 8 xfailed`.
* Broad kernel run (`tests/l3/gochara services/gochara_v3/tests tests/l3/kala_db`, `-m "not integration and not slow_real_ephemeris and not benchmark"`): `53 failed, 4434 passed, 3604 skipped, 58 deselected, 9 xfailed, 24 errors`. The same files run on an untouched checkout of the same commit give `53 failed … 24 errors` in the identical file set (`test_od1_vedha_residence`, `test_a53_gochara_v5_writer`, `test_c46/c47/c49`, `test_d1_near_miss_geometry`, `test_graze_interim`, `test_j4p_dasha_settlement`, `test_member_geometry_seam`, `test_p06b_near_miss_integration`, `test_w2_serving_route`, `test_k9_dispatch_provider`) — environmental (no `SE_EPHE_PATH`, no DSN, real-sky fixtures), pre-existing, not introduced here.
* pyflakes over every touched Python file: no findings (pyright is not installed in this environment and nothing was downloaded).
* TS gate (`platform/`, `node_modules` linked from the installed shared checkout): ESLint on the seed exit 0; vitest `scripts/__tests__/catalog_reconciliation`, `asset_registry_seed_dag_parity`, `l0_dag_contracts.freshness`, `tests/unit/migrations/nirmana_l0_transit_integrity_contract` → 35 passed, 3 skipped (DB-backed); `tsc --noEmit --skipLibCheck` → 1 error, `tests/unit/gochara_seal_workflow_static.test.ts` (NODE_ENV typing), unchanged from origin/main.

## 8. Not verified / left undone (plainly)
* Migration 1412 has NOT been applied to any real database; its behaviour is proven on a disposable cluster against the reconstructed table only. The production rows' pre-state must be 1320's (the migration refuses anything else).
* The sealed century build's next re-verification will report P4 (§4). Not re-run here; no rebuild.
* The kernel's P4 enumerator for sealed versions remains directly callable (§4).
* The citation census (`asset_census` Ldgr detector) may now read the seven rows as unsourced/placeholder-prefixed — that is accurate; not run here.
* `GOCHARA_DESIGN_SPECS_v1_4.md` line 314 stands until DECISION_RECORD_P4_DEMOTION is filed (§6).
* Documents naming the rule (Pravāha sealed set, D-5 briefs, `SHAD_DARSHANA_BRIEF_v2_0.md`, `plan_model.json` D-P4/RQ-8) are not edited.
* This note sits at the worktree root per the brief; ROOT_FILE_POLICY §1 would place it under `00_ARCHITECTURE/briefs/`.

## 9. What was NOT changed
FROZEN paths (asset_runner.py, runner.py, staleness.py, writers/__init__.py); any life-event, LEL, calibration, journal,
rectification or pramana asset; any applied migration; any other generator's weight; `GOCHARA_DESIGN_SPECS_v1_4.md`;
`l0_gochara_citation_resolution.ROWS` (sealed by migration 631; its row for the struck string stays as the historical record).

## 10. Clean-up record
Disposable Postgres clusters: started under `/Users/Dev/scratch.noindex/claude/madhav/20261027-dt/tmp`, stopped and removed by
the tests/scripts that started them. Baseline comparison worktree (`detached-a1a6a9e-dt-baseline`) and the gitignored
`node_modules` symlinks used for the TS gate: removed before commit. The scratch folder is removed at session end.

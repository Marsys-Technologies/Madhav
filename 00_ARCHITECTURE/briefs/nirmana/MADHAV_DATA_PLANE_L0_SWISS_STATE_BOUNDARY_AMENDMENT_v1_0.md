---
artifact: MADHAV_DATA_PLANE_L0_SWISS_STATE_BOUNDARY_AMENDMENT
version: "1.0"
status: APPROVED_FOR_EXECUTION
approved_on: 2026-09-13
strategy_decision: DP-SD-010
approval_record: "DP-SD-010; immutable amendment commit populated before dispatch"
strategic_parent_task: "Strategy — Data Plane / 01a0996e-6ca0-7642-ac31-f968fee214b3"
execution_task: "Execution — Data Plane / 01a0998a-8240-7631-97ce-36c6d4734fde"
parent_layer_contract: "MADHAV_DATA_PLANE_L0_BRAHMAGYAN_EXECUTION_BRIEF v1.0 / approval content cfe16cdac6d550499a2ecc7f762b57e3f3779da9 / dispatch 66a5ce6f8e92bd064b52b84d6eb473bb58ef1c9f"
source_revision: 552fa76d21406fcbb7f534afbd9600330f3a6276
accepted_blocker_evidence:
  - "MADHAV_DATA_PLANE_L0_PRODUCER_READY_ACCEPTANCE/1.0/blob-e9856ad9902e2f3c168b853d951826526e206589@552fa76d21406fcbb7f534afbd9600330f3a6276"
  - "MADHAV_DATA_PLANE_L0_VALIDATION_AND_REVIEW_RECORD/1.0/blob-743de521bbd1f8c360742a880dce582ec578c369@552fa76d21406fcbb7f534afbd9600330f3a6276"
  - "MADHAV_DATA_PLANE_EXECUTION_LEDGER/1.0/blob-dcbc64b8029c9aa6255cdd60f45097f19419f9ac@552fa76d21406fcbb7f534afbd9600330f3a6276"
goal_continuation: "Continue the existing active L0 Brahmagyan goal; do not create a replacement goal. Close only the Swiss Ephemeris process-state blocker, re-challenge L0 and return the terminal L0 verdict."
implementation_owner: "Execution — Data Plane / one writer"
independent_review_owner: "independent read-only reviewer, separate from implementation"
release_authority: "Strategy — Data Plane under native product-owner authority"
may_touch:
  - "platform/python-sidecar/panchang_engine/swiss_state.py"
  - "platform/python-sidecar/panchang_engine/__init__.py"
  - "platform/python-sidecar/panchang_engine/angas.py"
  - "platform/python-sidecar/panchang_engine/ayanamsha.py"
  - "platform/python-sidecar/panchang_engine/lagna.py"
  - "platform/python-sidecar/panchang_engine/planets.py"
  - "platform/python-sidecar/panchang_engine/rich_topics.py"
  - "platform/python-sidecar/panchang_engine/timings.py"
  - "platform/python-sidecar/panchang_engine/upagrahas.py"
  - "platform/python-sidecar/brahmagyan/l0_ephemeris.py"
  - "platform/python-sidecar/brahmagyan/ganita/engine.py"
  - "platform/python-sidecar/brahmagyan/ganita/graha_sthana_writer.py"
  - "platform/python-sidecar/brahmagyan/ganita/l1_dashas.py"
  - "platform/python-sidecar/brahmagyan/ganita/l1_divisionals.py"
  - "platform/python-sidecar/brahmagyan/ganita/l1_engine_check.py"
  - "platform/python-sidecar/brahmagyan/ganita/l1_panchanga_birth.py"
  - "platform/python-sidecar/brahmagyan/ganita/l1_positions.py"
  - "platform/python-sidecar/brahmagyan/ganita/l1_sensitive_points.py"
  - "platform/python-sidecar/brahmagyan/ganita/l1_strength.py"
  - "platform/python-sidecar/brahma/l1/ganita/divisionals_writer.py"
  - "platform/python-sidecar/pipeline/transit_search.py"
  - "platform/python-sidecar/pipeline/orchestrator/service_probes.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/bg_cohort.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/bg_ephemeris.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/bg_muhurta_lattice.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/bg_sky_calendar.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/ka_vighnakara.py"
  - "platform/python-sidecar/ga_writers/ga_dashas_writer.py"
  - "platform/python-sidecar/ga_writers/ga_sade_sati_writer.py"
  - "platform/python-sidecar/ga_writers/ga_sensitive_writer.py"
  - "platform/python-sidecar/ga_writers/ga_vargas_writer.py"
  - "platform/python-sidecar/pyjhora_adapter/_isolation.py"
  - "platform/python-sidecar/pyjhora_adapter/_jhora.py"
  - "platform/python-sidecar/pyjhora_adapter/_ayanamsha.py"
  - "platform/python-sidecar/pyjhora_adapter/compute.py"
  - "platform/python-sidecar/pyjhora_adapter/dashas.py"
  - "platform/python-sidecar/pyjhora_adapter/houses.py"
  - "platform/python-sidecar/pyjhora_adapter/panchanga.py"
  - "platform/python-sidecar/pyjhora_adapter/positions.py"
  - "platform/python-sidecar/pyjhora_adapter/sensitive_points.py"
  - "platform/python-sidecar/pyjhora_adapter/special_lagnas.py"
  - "platform/python-sidecar/pyjhora_adapter/strength.py"
  - "platform/python-sidecar/pyjhora_adapter/transits.py"
  - "platform/python-sidecar/pyjhora_adapter/vargas.py"
  - "platform/python-sidecar/routers/ephemeris.py"
  - "platform/python-sidecar/routers/panchang.py"
  - "platform/python-sidecar/routers/permission_curve.py"
  - "platform/python-sidecar/routers/pyhora.py"
  - "platform/python-sidecar/routers/transit_search.py"
  - "platform/python-sidecar/services/gochara_grammar/__init__.py"
  - "platform/python-sidecar/services/gochara_grammar/primitives.py"
  - "platform/python-sidecar/services/gochara_v3/engine.py"
  - "platform/python-sidecar/services/gochara_v3/mechanisms/w30_nodal_drishti.py"
  - "platform/python-sidecar/services/ka_gochara_sweep/writer.py"
  - "platform/python-sidecar/services/ka_kshetra/stage0_kinematics.py"
  - "platform/python-sidecar/services/ka_kshetra/stage3_clocks.py"
  - "platform/python-sidecar/services/ka_sangam/engine.py"
  - "platform/python-sidecar/services/taranga_service.py"
  - "platform/python-sidecar/services/w2g_validations/v3_spline_accuracy.py"
  - "platform/python-sidecar/tests/test_swiss_state_boundary.py"
  - "platform/python-sidecar/tests/test_ephemeris_ayanamsha.py"
  - "platform/python-sidecar/tests/l3/test_transit_search_cache.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_sky_calendar.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_sky_calendar_accuracy_anchors.py"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_SWISS_STATE_BOUNDARY_INVENTORY_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_SWISS_STATE_BOUNDARY_VALIDATION_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_VALIDATION_AND_REVIEW_RECORD_v1_0.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_PRODUCER_READY_ACCEPTANCE_v1_0.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_EXECUTION_LEDGER_v1_0.md"
must_not_touch:
  - "CLAUDE.md"
  - "CLAUDECODE_BRIEF.md"
  - "00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_v3_0.md"
  - "00_ARCHITECTURE/CROSS_CUTTING_DECISION_REGISTER_v1_0.md"
  - "00_ARCHITECTURE/CAPABILITY_MANIFEST.json"
  - "00_ARCHITECTURE/CURRENT_STATE_v1_0.md"
  - "00_ARCHITECTURE/SESSION_LOG.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v1_0.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_EXECUTION_BRIEF_v1_0.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_SWISS_STATE_BOUNDARY_AMENDMENT_v1_0.md"
  - "platform/src/**"
  - "platform/supabase/migrations/**"
  - "platform/migrations/**"
  - ".github/workflows/**"
  - "**/*credential*"
  - "**/*secret*"
activation_prohibitions:
  - "No output-semantic, doctrine, source-rights, identity, layer-ownership or consumer-integration change."
  - "No process-isolation architecture, deployment, process-manager, worker-count or capacity change under this decision."
  - "No push, PR, merge, deploy, production/database/campaign mutation or L1-L5 elevation."
changelog:
  - "1.0: Selects shared process-wide serialization over process isolation and authorizes the exact blocker-closing boundary for L0 producer readiness."
---

# L0 Swiss Ephemeris process-state boundary amendment

## 1. Decision

`DP-SD-010` selects the shared process-wide serialization path. Execution is
authorized to inventory and serialize every live in-process Swiss Ephemeris
state setter and its complete dependent calculation within the fixed file list
above, including `platform/python-sidecar/pipeline/transit_search.py`.

Process isolation is not selected. It would introduce a new runtime topology,
worker lifecycle and latency/capacity contract without current operational
evidence or deployment authority. Extending the already implemented re-entrant
boundary is the smaller reversible correction and makes the mutable library
state explicit at its source.

This is a scope amendment to the still-active L0 goal, not permission to begin
L1-L5 or change their meanings. The only expected external distinction is that
the same Swiss-dependent input yields the same output regardless of concurrent
requests using another permitted sidereal mode or ephemeris path.

## 2. Accepted failure and non-claim

At `552fa76d2`, permitted ephemeris and Panchanga entry points share one
`RLock`, but `pipeline/transit_search.py` calls `swe.set_sid_mode` and dependent
calculations outside that boundary. Other live modules also call process-global
`set_sid_mode` or `set_ephe_path`. A concurrent non-Lahiri request can therefore
intervene between another operation's state selection and calculation.

This source observation proves a concurrency hazard and prevents process-wide
repeatability acceptance. It does not prove a production incident, wrong stored
row, deployment state, consumer-value loss or empirical error rate.

## 3. Fixed semantic delta

1. Preserve one canonical process-wide re-entrant lock. Do not introduce a
   second independent lock. Moving the lock requires a compatibility re-export
   so every old and new import resolves the same object identity.
2. Hold the lock from the first state selection or state-dependent calculation
   through the final dependent Swiss calculation and copying of its result.
   Locking only the setter is insufficient.
3. Nested calls must remain safe through re-entrancy. Do not hold the lock over
   database/network I/O, sleep or unrelated transformation; narrow the critical
   section without exposing state-dependent work.
4. Inventory every non-test sidecar occurrence of direct Swiss state mutation
   (`swe.set_*`), aliased mutation and wrapper mutation (including PyJHora
   `drik.set_ayanamsa_mode`), plus every direct or wrapper-dependent Swiss
   calculation that can observe sidereal mode or ephemeris path. Follow imports
   and live callers through PyJHora adapters and `brahma/l1/ganita`, rather than
   treating absence of a literal `swe.set_*` as safety. Classify each as
   `SERIALIZED`, `PROCESS_ISOLATED_EXISTING`, `NOT_STATE_DEPENDENT` or
   `UNRESOLVED`; record exact file/function/evidence. `TEST_ONLY` is valid only
   outside shipped source. Any live `UNRESOLVED` occurrence blocks acceptance.
5. The amendment's `may_touch` list is the immutable outer boundary. WP0 may
   narrow it; execution may not add another path. A live affected operation
   outside this list returns one exact residual to strategy.
6. Cached Swiss results must either include every varying state dimension in
   their key or be reachable only under a proved invariant state. Preserve cache
   bounds and output identity; clear/invalidate only when the old key would be
   unsound.
7. Preserve all numerical algorithms, input/output schemas, units, rounding,
   node choice, ayanamsha selection, event ordering, failure states and service
   routes. Serialization may change waiting time, not astrological meaning.

## 4. Required proof

| Proof | Required detector-backed result |
|---|---|
| Complete inventory | A committed inventory generated from the source tree accounts for every direct, aliased and wrapper Swiss-state mutation (including `drik.set_ayanamsa_mode`) and every direct/wrapper-dependent calculation; injected literal and wrapper unclassified fixtures fail. |
| Object identity | All participating modules resolve the same lock object; a deliberately separate lock is detected. |
| Adversarial interleave | A barrier-controlled non-Lahiri ephemeris operation cannot alter an overlapping Lahiri transit search, Panchanga or L0 calculation; reverse ordering also passes. |
| Ephemeris-path interleave | Path selection/reset cannot intervene in another dependent calculation; the prior unsafe interleave fails under a negative fixture. |
| Critical-section span | A test pauses after state selection, attempts a conflicting operation, and proves it cannot calculate until the first operation releases. |
| Re-entrancy/deadlock | Nested permitted entry points complete under timeout with deterministic results. |
| Cache context | Repeated and alternating modes/paths cannot obtain a cached result produced under incompatible state. |
| Semantic invariance | Fixed pre-amendment single-thread fixtures are byte/value equivalent except documented non-semantic metadata. |
| Regression | Focused L0 suite remains green; the broad L0 suite is rerun. The two pre-existing Muhurta isolation failures may remain only if reproduced unchanged at the pinned baseline and excluded from the changed boundary. |
| Independent challenge | No owned HIGH/CRITICAL finding and no unresolved live state-dependent caller. |

The missing `DBURL`/`DATABASE_URL` remains honest `NOT_RUN` live-parity evidence;
it neither becomes a health claim nor blocks computational producer readiness if
all source, fixture and process-state proofs pass.

## 5. Terminal rule

After implementation, rerun the applicable F22/F23, DP03 and DP07 proof and the
original L0 acceptance matrix. Execution may change the prior verdict to
`PRODUCER_READY` only if the complete inventory has no live `UNRESOLVED` caller,
the adversarial concurrency tests pass, semantic invariants remain unchanged and
independent review has no owned HIGH/CRITICAL finding. `INTEGRATED`, deployment,
consumer value and empirical evaluation remain unreached. Update the execution
ledger, commit the terminal packet, complete the existing L0 goal if true, hand
back to `Strategy — Data Plane`, and stop with L1 waiting.

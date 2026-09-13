---
artifact: MADHAV_DATA_PLANE_L0_SWISS_STATE_BOUNDARY_SCOPE_ADDENDUM
version: "1.0"
status: APPROVED_FOR_EXECUTION
approved_on: 2026-09-13
strategy_decision: DP-SD-011
approval_record: "DP-SD-011 at strategy content commit a112b64a61c60ff44369ba64eee73a3445a48461"
strategic_parent_task: "Strategy — Data Plane / 01a0996e-6ca0-7642-ac31-f968fee214b3"
execution_task: "Execution — Data Plane / 01a0998a-8240-7631-97ce-36c6d4734fde"
parent_amendment: "MADHAV_DATA_PLANE_L0_SWISS_STATE_BOUNDARY_AMENDMENT v1.0 / content d61469b6d96b956782548d36fb23f9e813e1ae98 / approval pin b1a0f17eb65494f21a00fd2b22d6264da76c3c38"
source_revision: b8e342049
goal_continuation: "Continue the existing active L0 goal; close only the transitive ga_strength PyJHora Swiss-state span and repeat the terminal challenge."
implementation_owner: "Execution — Data Plane / one writer"
independent_review_owner: "independent read-only reviewer, separate from implementation"
release_authority: "Strategy — Data Plane under native product-owner authority"
may_touch:
  - "platform/python-sidecar/ga_writers/ga_strength_writer.py"
  - "platform/python-sidecar/tests/test_swiss_state_boundary.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/__tests__/test_ga_strength_enrichment.py"
  - "platform/python-sidecar/tests/test_ga3_writers.py"
  - "platform/python-sidecar/tests/test_l1_bhava_bala_av_completion_d1_5b.py"
  - "platform/python-sidecar/tests/test_l1_strength.py"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_SWISS_STATE_BOUNDARY_INVENTORY_v1_0.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_SWISS_STATE_BOUNDARY_VALIDATION_v1_0.md"
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
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_SWISS_STATE_BOUNDARY_SCOPE_ADDENDUM_v1_0.md"
  - "platform/src/**"
  - "platform/supabase/migrations/**"
  - "platform/migrations/**"
  - ".github/workflows/**"
activation_prohibitions:
  - "No strength, Ashtakavarga, Bhava Bala, PyJHora, numerical or output-contract semantic change."
  - "No orchestrator, concurrency level, process architecture, L1-L5 elevation, deploy or production change."
changelog:
  - "1.0: Adds the exact live ga_strength PyJHora setter-to-calculation spans found by the DP-SD-010 transitive audit."
---

# Swiss-state boundary scope addendum — `ga_strength_writer`

## 1. Accepted residual and decision

The DP-SD-010 audit at `b8e342049` found one shipped affected file outside the
immutable amendment scope: `platform/python-sidecar/ga_writers/ga_strength_writer.py`.
It is live through the `ga_strength` orchestrator writer, and the orchestrator
uses an in-process thread pool. It is therefore neither test-only nor
process-isolated.

Two exact unsafe spans are accepted:

- `_derive_ashtakavarga_shodhana_grids` selects PyJHora ayanamsha and releases
  the canonical lock before `charts.rasi_chart` and the dependent shodhana calls;
- `_derive_bhava_bala` selects PyJHora ayanamsha and releases the lock before
  `bhava_bala` and its three dependent component calculations.

`DP-SD-011` adds only this file and its exact proof surfaces. It does not reopen
the 54-file boundary or authorize changes to strength doctrine, algorithms,
values, units, rounding, output schemas or orchestration.

## 2. Required correction

1. Both complete functions must hold the same canonical re-entrant lock from
   before PyJHora state selection through copying the final dependent results.
   Reusing the approved decorator is preferred when it spans the whole function.
2. `pyjhora_adapter.strength._set_ayanamsha` may retain its current nested lock;
   re-entrancy must be proved and all imports must resolve the same lock object.
3. Do not hold the lock across database/network I/O. These functions are
   computation-only and must remain so.
4. Update the committed inventory so both spans are `SERIALIZED`, and keep the
   transitive detector capable of finding wrapper-setter-then-dependent-call
   sequences rather than only literal setters.
5. Any further live affected file outside DP-SD-010 plus this addendum returns
   as one exact residual. Execution may not generalize the addendum into a
   directory glob.

## 3. Proof and terminal rule

- Add a barrier-controlled negative that pauses after the PyJHora setter and
  proves a conflicting non-Lahiri operation cannot calculate until the complete
  Ashtakavarga/Bhava Bala span releases.
- Prove reverse ordering, nested re-entrancy, no deadlock and single-thread
  byte/value equivalence for the affected outputs.
- Run the addendum tests, DP-SD-010 amendment suite, focused L0 suite and exact
  broad baseline. The same two unchanged Muhurta failures remain an inherited
  baseline only if reproduced identically.
- Complete the independent challenge. `PRODUCER_READY` remains prohibited if
  any shipped direct, aliased, wrapper or transitive Swiss-state span remains
  `UNRESOLVED`.

If all original L0 and DP-SD-010 criteria then pass, execution may update the
acceptance/ledger, complete the existing goal, return the terminal packet and
stop with L1 waiting. No later delivery state is granted.

---
artifact: 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/README.md
mechanism_id: LL.1
mechanism_name: Signal weight calibration
version: 1.0
status: STUB
expose_to_chat: false
native_id: "abhisek"
layer: "L6"
produced_during: STEP_11_LEARNING_LAYER_SCAFFOLD (Step 0 → Step 15 governance rebuild)
produced_on: 2026-04-24
activates_at: M4
prerequisite: >
  M3 closed (temporal engine produces per-event signal-firing records); CW.LEL events
  match against MSR signals; CW.PPL prediction outcomes available per MP §LL-Appendix.B LL.1.
authoritative_spec: 00_ARCHITECTURE/MACRO_PLAN_v2_0.md §LL-Appendix.B LL.1
provenance: 00_ARCHITECTURE/LEARNING_LAYER_SCAFFOLD_DECISION_v1_0.md §3.2
---

# LL.1 — Signal Weight Calibration

```
STATUS: STUB — M3 closed 2026-05-01; LEL gate cleared (46 events). Awaiting scoring rubric native-approval (Track T3 output) before first signal_weights/ write. Population begins at M4-B.
```

---

## What this mechanism does

LL.1 calibrates per-signal weights for the 499-signal Master Signal Register
(`025_HOLISTIC_SYNTHESIS/MSR_v3_0.md`) against empirical match records. The output is a
per-signal calibration weight written to a shadow-mode register (`signal_weights/` —
**does not yet exist**; created at M4 first calibration cycle). Weights are promoted to
the production register only after the per-mechanism N-observation threshold is met
(N = 3 per MP §"Learning discipline" rule #3, default; per-mechanism override deferred
to Step 12 or M4 session per `LEARNING_LAYER_SCAFFOLD_DECISION_v1_0.md §5.4`).

LL.1 is the foundation mechanism for the Learning Layer — LL.2 (graph edge weights)
depends on LL.1 weights stabilizing first per MP §LL-Appendix.B LL.2 dependencies.

## I/O contract (from MP §LL-Appendix.B LL.1)

- **Input.** MSR signal rows (499 at v3.0); per-signal LEL event-match records once M4
  produces them; per-signal PPL prediction outcomes once M6 produces them.
- **Output.** Per-signal calibration weights at `06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/`
  (shadow-mode register; does not yet exist). Promoted to production register after N
  observations.
- **Kill-switch.** Suspended if per-signal calibration error rate worsens over a rolling
  window of N updates; suspended globally if any learning-discipline rule (#1
  priors-locked in particular) is flagged as violated.
- **Owner.** Native approves weight-update rubric; Claude scaffolds register + update
  pipeline; Gemini red-teams per MP §IS.8 cadence.
- **Dependency on other LL.M.** None (foundation mechanism).
- **Interaction with workstreams.** Consumes CW.LEL event records; consumes CW.PPL
  prediction outcomes.

## Activation status

Per MP §LL-Appendix.A activation matrix:

| Phase | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M8 | M9 | M10 |
|-------|----|----|----|----|----|----|----|----|----|-----|
| LL.1  | n/a | scaffold | scaffold | **active** | active | active | active | active | active | active |

Currently in M2 (paused for governance rebuild). Scaffold state. No active calibration.

## Guardrails (this mechanism specifically)

- **Population gate.** First write to `signal_weights/` is at the M4 calibration session.
  No earlier session may create the directory or write to it.
- **N threshold.** N = 3 per default; per-mechanism override deferred to Step 12 or M4
  session opening, whichever fires first.
- **Reversal protocol.** Retract the parameter version + log retraction at
  `06_LEARNING_LAYER/OBSERVATIONS/` next to the data that motivated the original update.
- **Two-pass approval.** Every weight update requires both Claude + Gemini approval
  evidence in the SESSION_LOG entry that performs the write.

Full guardrail list: `00_ARCHITECTURE/LEARNING_LAYER_SCAFFOLD_DECISION_v1_0.md §5`.

## Last update

*No updates. Stub state at Step 11 scaffold close (2026-04-24).*

*Updated M4-A-T2-PPL-INFRA (2026-05-01): STUB banner removed. Status: ACTIVE-PENDING. signal_weights/ directory not yet created — first write is M4-B scope per PHASE_M4_PLAN §3.2.*

---

*End of LL.1 stub — Step 11 of the Step 0 → Step 15 governance rebuild — 2026-04-24.*

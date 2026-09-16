---
artifact: MADHAV_DATA_PLANE_DP019_KSHETRA_GATE_ACCEPTANCE
version: "1.0"
status: SOURCE_PACKET_ACCEPTED
accepted_on: 2026-09-16
strategy_decision: DP-SD-019
execution_task: "Execution — Data Plane / 01a0998a-8240-7631-97ce-36c6d4734fde"
execution_branch: codex/madhav-data-plane-execution
---

# DP-SD-019 Kṣetra gate acceptance

## Accepted source

The broad Python release-gate repair removed retired test infrastructure and
aligned inherited tests with accepted producer contracts. During exact-tip
review, the first Kṣetra candidate `ad4f4f27d8d19f3e37290beb64b57c1d6645d3a3`
was rejected with one HIGH correctness finding: the active DHARA null engine
sampled its envelope on midpoint times but interpolated those values with
edge-relative array coordinates. Integer-day circular shifts therefore blended
adjacent log rates and could corrupt null maxima, thresholds and p-values.

Correction `87cc8c9baf894c615e167672c6c7af57a15cf71c` converts shifted source
times to midpoint-relative sample coordinates before interpolation. It also
retains the accepted Kṣetra baseline tuple/shape-only contract and makes the
historical vector entry point delegate to the single active C/E null engine.
The correction changes no database schema, write path, identity denominator,
layer boundary or public call signature.

Independent exact-tip re-review reports no CRITICAL, HIGH, MED or LOW finding
and recommends source acceptance under the existing DP-SD-019 L3 authority.

## Verification

- the reviewer’s independent `H=60`, `R=2`, alternating-rate oracle returns
  `1515.0000000000002`, matching the hand-derived integer-shift maximum `1515`;
- the independent `H=4`, `R=8` oracle returns alternating total hazards
  `40.00000000000001` and `202.00000000000009`, matching the hand-derived
  half-day interpolation and integer-day permutation sequence;
- local regression proof deliberately failed on the predecessor with
  `300.0000000000001` instead of `1515`, then passed after the one-coordinate
  correction;
- focused null-engine verification: 37 passed;
- complete local Kṣetra verification: 259 passed and 3 skipped;
- reviewer focused Kṣetra/null verification: 110 passed;
- writer inventory verification passes with 123 writers; version and probe
  digest are unchanged and exactly `ka_kshetra` changes from
  `979a2500f639f42865ed5be1e26861cb5f97db2535c0309f060e75255a764085`
  to `c735c02bf28340fc33ca3615d89750f4532cdbbbfade1706b71f684e83dc27ce`;
- `git diff --check` passes and no database/runtime mutation was performed.

## Non-claims and next gate

This is source-local acceptance. The L3 analysis-layer pin must remain red until
this immutable source and review artifact are bound through the versioned
successor-admission mechanism. The acceptance does not establish or authorize
database mutation, physical generation, build, deployment, L4/L5 work,
consumer value or empirical predictive performance. The two inherited Muhūrta
contract failures remain a separate authority-bound release-gate issue.

---
artifact: POST_GATE_II_FOLLOWUPS.md
version: 1.0
status: ACTIVE
authored_by: Claude Code Sonnet 4.6 (Gate II post-close fixup) — 2026-05-13
purpose: Tracked follow-ups discovered during Gate II that are
         intentionally deferred to a later gate.
---

# Post-Gate-II Follow-ups

## FU.1 — Panel-mode trace emission validation gate

**Source:** GAP_ANALYSIS.md §J.4
**Status:** DEFERRED — renderer ready, emitter pending production rollout
**Trigger:** When panel-mode synthesis is enabled in production
            (currently single_model only)

### Context
Gate II's SynthesisStepDetail.tsx implements a discriminated
branch on `mode: 'single_model' | 'panel'` per locked design
decision D6. The single_model branch is exercised by current
production traffic and validated by Gate II's fixture tests
(single_model + panel-mode fixtures both pass).
The panel-mode branch is forward-compatible dead code until the
synthesis module begins emitting `mode: 'panel'` step rows.

### When-Then
WHEN any of the following are true:
  - A feature flag enabling panel-mode synthesis is flipped on in
    production
  - The synthesis module is modified to emit `mode: 'panel'`
    step rows
  - A native query is observed routing through panel mode
THEN open a 1-hour follow-up gate to:
  1. Submit a query that triggers panel-mode synthesis
  2. Verify the trace drawer renders the panel branch correctly
     (N panelist rows + aggregator row, each with full LLM-call
     metadata)
  3. Capture a screenshot
  4. If broken, fix SynthesisStepDetail's panel branch and re-test

### Owner
TBD — assign at the time the trigger fires.

### Estimated effort
1 hour (renderer is built; this is verification + minor fixes only).

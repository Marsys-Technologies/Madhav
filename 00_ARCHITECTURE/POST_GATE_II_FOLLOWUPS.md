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

---

## FU.2 — Audit writer follow-up: populate D11 nullable columns

**Source:** Gate II.5 W3/W6 (D11 discovery)
**Status:** DEFERRED — migration 045 applied; renderer ready; writer not yet updated
**Added:** 2026-05-13

### Context
Gate II.5 added three nullable columns to `audit_events`:
  - `disclosure_tier TEXT`
  - `b10_compliant BOOLEAN`
  - `b11_compliant BOOLEAN`

The trace UI renders null values as "—" with tooltip
"Not yet tracked — pending audit writer update (POST_GATE_II_FOLLOWUPS.md FU.2)"
per R10 / AuditDetail.tsx PENDING_TOOLTIP.

The audit writer (route.ts or audit_writer.ts) does not yet populate
these columns — they always land as NULL in production.

### When-Then
WHEN the audit writer is extended to emit disclosure_tier and B.10/B.11
compliance flags, THEN:
  1. Verify the `audit_events` INSERT/UPDATE includes the three columns
  2. Run W11-style live verification: query `/api/admin/trace/<query_id>`
     and confirm AuditDetail renders real values (not "—") for all three
  3. Remove the PENDING_TOOLTIP from AuditDetail.tsx (or replace with
     the actual tooltip text for the populated values)

### Owner
TBD — audit writer author.

### Estimated effort
30 min (writer extension) + 15 min (verification).

---

## FU.3 — compose_bundle / context_assembly terminology correction

**Source:** Gate II.5 DISCOVERY_REPORT.md §F (W1 finding)
**Status:** NOTED — no code change required; documentation correction only
**Added:** 2026-05-13

### Context
The Gate II close report and earlier session notes conflated two distinct
pipeline steps:

- `compose_bundle` (step_seq 2): bundle hydration — fires before tool_fetch,
  assembles the retrieval bundle spec from the planner output. Emitted by
  route.ts at step_seq 2 with step_name='compose_bundle'.

- `context_assembly` (step_seq 7): pre-synthesis assembly — fires after
  tool_fetch, builds the LLM context window from retrieved chunks. Despite
  the `CONTEXT_ASSEMBLY_ENABLED` feature flag being retired (Pipeline-
  Transform-S1 2026-05-11), the step still emits in production under the
  step_name='context_assembly'.

These are NOT the same step. Gate II.5 W1 confirmed this by reading
route.ts directly. Any document that says "compose_bundle was renamed
context_assembly" or vice versa is incorrect.

### Action Required
If any CURRENT_STATE.md, SESSION_LOG.md, or downstream document equates
these two steps, correct it at the next governance pass. The canonical
reference is DISCOVERY_REPORT.md §F (Gate II.5 worktree root, committed
at 5463702).

### Owner
Native / next governance pass.

### Estimated effort
< 15 min (documentation search-and-correct).

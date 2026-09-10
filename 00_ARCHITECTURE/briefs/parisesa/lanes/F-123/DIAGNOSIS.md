---
finding: F-123
stream: S1 DVARA
class: CL-11 dead pointer (missing required-args on a tri_plane/drill pointer)
stage: D COMPLETE
---

## 1. Live reproduction

Step 1: `mcp__marsys-jis-direct__kala_now_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa'})` →
`tri_plane.interpretation_ref = {"instrument":"kala_explain_get","hint":"Why this NOW state reads as
it does — the drivers and classical grounds behind the active windows and confluence"}` — no mention
of any required argument.
Step 2 (following the pointer exactly as advertised):
`mcp__marsys-jis-direct__kala_explain_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa'})` →
`{"ok":false,"error":"either \`domain\` or \`bhava\` is required","tool":"kala_explain_get"}`.
CONFIRMED exactly as claimed — the pointer dead-ends.

## 2. Claim decomposition

1. "kala_explain_get hard-errors on the exact call shape kala_now_get advertises" — CONFIRMED, §1.
2. "the advertised drill is chart-scoped; the target is domain-scoped" — CONFIRMED: `kala_now_get`'s
   pointer takes only `chart_id` in its own envelope's framing; `kala_explain_get` requires
   `domain` or `bhava`, neither of which exists in `kala_now_get`'s NOW-state response at all (NOW
   state has no single privileged domain — it spans all 8 domains named in its windows' `domains[]`
   arrays, confirmed in this session's own `kala_now_get` output).
3. "'Explain my current dasha' is domain-less by nature and has no correct value to supply" — this is
   the finding's own framing/argument, not independently falsifiable by a tool call; accepted as
   correctly characterizing the UX gap.

## 3. Mechanism → file:line

`platform-mcp/src/tools/kala_views/now.ts` — `tri_plane.interpretation_ref` is constructed as a
static object literal (`{instrument:'kala_explain_get', hint:'...'}`) with no args payload, at the
point in the handler that builds the `tri_plane` field (co-located with the `drill_pointers` array
construction, same file — exact line not individually pinned this pass since the fix target is the
STRUCTURE of the pointer object, not a single line; Stage S should grep
`interpretation_ref.*kala_explain_get` in `now.ts` to pin the exact literal).
`platform-mcp/src/tools/kala_explain_get.ts` (or wherever `kala_explain_get`'s handler validates
input) enforces `domain XOR bhava` required — confirmed by the live error message's exact wording.

## 4. Sibling census

Not performed this pass — the finding's own scope note says "PP2 gate reconciliation: evidence_file
reduced to a single canonical JSON pointer; the other evidence file(s) for this finding are
evidence/E2_q1_marriage_timing_trace.json," implying at least one other reproduction path
(E2_q1) already exists in the corpus for the same defect class. Not independently re-verified this
pass. Worth checking at Stage S whether `kala_ahead_get`'s and `kala_elect_get`'s own
`tri_plane`/`drill_pointers` (also present on `kala_now_get`'s envelope, per this session's live
output: `prediction_ref: kala_ahead_get`, `intervention_ref: kala_elect_get`) have the same
missing-required-args gap — NOT reproduced this pass, flagged as a likely sibling census for
Stage S.

## 5. Blast radius

- Two possible fix directions (Stage S should pick one, not both): (a) make the pointer carry the
  args the target needs — e.g. synthesize a reasonable default `domain` from the NOW state's
  strongest-signaled domain, or (b) make `kala_explain_get` degrade gracefully with a
  domain-agnostic "general explain" mode when called bare, rather than hard-erroring. Direction (a)
  keeps `kala_explain_get`'s existing contract stable (lower blast radius, S1's preferred
  recommendation since S1 doesn't own `kala_explain_get`'s validation logic — that's inside S4
  VĀCA's `now.ts`/`explain.ts` lease per §2.1's kala_views file split: **S1 does NOT own
  `now.ts`/`explain.ts`** — this finding's actual fix file is S4's, not S1's own OWNS list. Flagging:
  **PAR-F123-NEEDS-LEASE `platform-mcp/src/tools/kala_views/{now.ts,explain.ts}`** — same situation
  as F-09, a board-assignment vs. lease-domain mismatch not caught by plan §2.1's table.**
- This lane's D-stage work stands; Stage S/B should route to S4 or be re-leased, per the plan's
  "specs travel; leases don't" rule.

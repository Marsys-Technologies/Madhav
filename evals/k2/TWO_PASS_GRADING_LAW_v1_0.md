---
artifact: TWO_PASS_GRADING_LAW
version: 1.0
status: LAW — PERMANENT, applies to every future standing-battery run, not just this campaign
lane: Elevation Campaign v2.1, Stream γ (PŪRṆA), Lane K2 · EL-10
implements: evals/k2/auditor.ts (executable enforcement), evals/k2/consumption_grader.ts
  (the grader half of the pair)
supersedes: single-pass grading as practiced in UAT_DARPANA run 1
---

# Two-pass grading — codified as LAW

## Why this exists (the evidence, not a hypothesis)

`ELEVATION_REGISTER_v1_0.md` EL-10: single-pass grading in UAT_DARPANA run 1 missed the top
failure in the whole exercise — S4-03 (the Gulika "isn't actually in your computed chart data"
false-absence claim) was rated a perfect DELIGHT by the first-pass grader and only caught on
adversarial re-audit. Across the sampled slice, **~22% of scores were overturned on audit**, and
27–28 of 36 scored queries were **never independently verified at all**. A grading process with a
~1-in-5 overturn rate on the slice that WAS checked is not a grading process a battery can be
staked on. This is why the charter (`ELEVATION_CAMPAIGN_CHARTER_v2_1.md` §γ.K2) makes two-pass
grading LAW, not a recommendation.

## The law, stated exactly

1. **No graded answer is final on a single pass.** Every answer that receives a quality grade
   (pass/fail, band, score) MUST also receive an independent second pass by a **different
   method** — not a second look by the same grader, not a re-read by the same code path. The
   second pass verifies the FIRST pass's claims against source evidence (tool results, DB rows,
   raw fact_ids) rather than re-answering the question itself.
2. **The two passes must be methodologically independent.** In `evals/k2/auditor.ts`, the grader
   pass (`evals/k2/consumption_grader.ts`) uses fast substring matching against raw tool-result
   text; the auditor pass uses a structurally stricter method — it parses each result as JSON
   and walks the object graph for an EXACT leaf-value match, catching the specific false-positive
   class substring matching is prone to (a fact_id that is a substring of an unrelated longer
   token). Where `DATABASE_URL` is configured, the auditor pass additionally cross-checks a
   sample of disagreement fact_ids directly against the live `chart_facts` table — genuinely
   "DB-verifying," not just a second heuristic. Independence of METHOD is the requirement, not
   independence of implementation language or code location.
3. **Disagreements are LOGGED, never silently resolved in the grader's favor.** When the grader
   and the auditor disagree on a concept's hit/miss (or an answer's pass/fail), the disagreement
   is written to a `disagreement_ledger` entry carrying both verdicts, both reasons, and an
   explicit `resolution: 'UNRESOLVED_LOGGED'` status. The grader's verdict is NEVER auto-promoted
   to final just because it ran first or because reconciling by hand is more work. A human (or a
   dedicated Opus adversarial auditor, per the Darpana design's own Phase-4 pattern) resolves the
   disagreement explicitly; the ledger records who resolved it and how.
4. **`audit_overturn_rate` is a tracked, reported number**, every run, not just when someone
   remembers to check. `evals/k2/auditor.ts` computes it as
   `disagreements / total_concepts_assessed` and prints it in the run summary. A rate trending
   toward the EL-10 baseline (~22%) or worse on a NEW run is itself a finding, not noise — it
   means the grader's heuristic has drifted from ground truth again.
5. **No ACCEPT disposition may cite a battery run that skipped the auditor pass.** A grader-only
   run is a legitimate quick-look tool (fast iteration during development), but its output must
   be labeled `SINGLE_PASS — NOT AUDIT-CLEARED` wherever it is reported, and it cannot be the
   evidence base for a native disposition ruling (`§9` of `UAT_DARPANA_DESIGN_v1_0.md`'s ACCEPT
   / ITERATE / dispositions). `evals/k2/auditor.ts`'s output JSON carries
   `two_pass_complete: true` only when both passes actually ran over the same transcript.
6. **This is PERMANENT**, per the charter's explicit language ("two-pass grading (grader +
   DB-verifying auditor) codified as LAW in the battery spec"). It binds every future standing-
   battery run this instrument's evaluators execute, not only the Elevation Campaign v2.1 run
   that wrote it down. A future session that wants to relax this back to single-pass grading
   must raise that with the native explicitly (CLAUDE.md §L: "Change architecture without
   native's explicit approval + version bump" applies to grading architecture too) — it does not
   get to happen by a future session simply not calling `auditor.ts`.

## What this does NOT claim

This law governs the MECHANICAL concept-hit / consumption-ratio grading dimension (K2 item 1).
It does not by itself replace the Darpana design's own richer two-source verification for the
investigation/Vidhi/retrieval-plane tracks (§6.0/§6.2/§6.3 of `UAT_DARPANA_DESIGN_v1_0.md`,
already independently sourced from sealed transcript + controlled replay) — those tracks already
satisfy an equivalent independence discipline by a different mechanism and are out of scope for
`auditor.ts`'s rewrite. What K2 adds is: the NEW consumption/completeness/volunteering dimensions
this lane introduces (EL-04/05/23) inherit the same two-pass discipline from day one, rather than
repeating EL-10's mistake of shipping a grading dimension before its own verification exists.

## How to run it

```
npx tsx evals/k2/auditor.ts <transcript.json> <domain> <chart_id> [--ledger-out <dir>]
```

Runs the grader pass internally, then the independent auditor pass, prints the combined
`TwoPassResult` (including `audit_overturn_rate` and the full `disagreement_ledger`), and — unless
`--no-write` is passed — persists the ledger to
`evals/k2/disagreement_ledger/<domain>_<chart8>_<timestamp>.json` for the audit trail
`ORCHESTRATOR_CONVERGENCE_CLOSE`/`GOVERNANCE_INTEGRITY_PROTOCOL` style sessions expect.

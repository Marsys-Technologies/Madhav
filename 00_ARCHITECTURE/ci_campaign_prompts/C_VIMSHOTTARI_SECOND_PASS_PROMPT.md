# Claude Code task C — build the real Vimshottari second pass (Madhav)

Repo `Marsys-Technologies/Madhav`, `main` queue-gated. **State the `origin/main` SHA.** Standing
rules `CI_EFFICIENCY_AUDIT_v1_0.md §6`; the governing one:

> A check earns `two_pass_verified` only if it could have failed for a reason other than a bug in
> itself — it must discriminate over the producer's actual output space. Test: mutate the
> producer's output to a *plausible wrong* value and confirm the check fires.

This is the **constructive** task — the inverse of everything the campaign did so far. The demotions
lowered claims to meet the truth; this raises the truth to meet the claim, honestly re-earning
~1.36M `chart_dashas` rows that Task A/B demoted to `single`. Scoped in §6.19 as ~1 focused day.

**Do not relabel. Earn.** A row goes back to `two_pass_verified` only when an independent
re-derivation actually agreed on it.

## Part 1 — Build the independent verifier

Requirements, each non-negotiable:
1. **Independent implementation.** Re-derive the Vimshottari sequence from the Moon's sidereal
   longitude **without calling `compute_vimshottari`** — a second pass that shares the producer's
   code proves nothing. Different code path, ideally different structure (e.g. derive from the
   nakshatra-lord cycle directly).
2. **Per row, every level.** Compare each row, not one L1 row broadcast — the defect Task A fixed.
   Cover level_n 1–4.
3. **Both fields.** Compare **lord** AND **both period boundaries** (start, end). A lord-only check
   is a membership check and earns nothing (the ruling). Boundaries are the hard part: dates are
   JD-rounded, so define and justify a tolerance — too tight = false `divergent_flagged`, too loose
   = the check stops discriminating. State the tolerance and why.
4. **All charts.** Remove the `if chart_id == CANONICAL_CHART_ID` gate; the verifier derives each
   chart's own expected starting lord rather than comparing to a constant. Every chart earns or
   fails on its own evidence.
5. **Honest verdict per row:** agree → `two_pass_verified`; disagree → `divergent_flagged` (with a
   logged WARNING naming chart/level/field/values); not computable → `single`. Use
   `two_pass_verdict(...)` / the sanctioned constants, never a literal.

## Part 2 — Prove it discriminates (before trusting one green row)

The whole point is that it *can* fail on a plausible wrong value:
- Mutate a lord to a valid-but-wrong graha → must fire `divergent_flagged`. Confirm.
- Mutate a boundary by more than tolerance → must fire. Confirm.
- Mutate a boundary by less than tolerance → must NOT fire (else the tolerance is meaningless).
- Confirm each probe reaches the code under test (rule 4).
Report the real disagreement rate on a full run: if it is exactly zero across ~1.36M rows, be
suspicious — either the engine is genuinely that good (state your confidence) or the comparison is
not biting (find out which). A second verifier that never disagrees is the exact defect this
campaign exists to kill; hold yourself to the standard you enforced on others.

## Part 3 — Re-promote only what genuinely passes

- Run the verifier (its own execution, not a relabel); rows that agree return to
  `two_pass_verified`, disagreements land `divergent_flagged` and are **reported to Abhisek** as
  real engine defects, not silently corrected.
- Backfill via the established pattern (`DATABASE_URL` from env, dry-run default, one chart first,
  production run handed to Abhisek). Publish the split: re-earned / divergent / uncomputable.
- Wire the verifier into the build so future rows are earned at write time, not retro-audited.

## Part 4 — Close the loop

- The standing invariant's detector-liveness check should now see `divergent_flagged` populated if
  any real divergence exists; confirm.
- §6 subsection: the verifier's method, the tolerance decision, the disagreement rate, and the
  re-earned count. If divergences surfaced real engine bugs, that is a **finding**, reported
  separately — it may reopen accuracy questions beyond M-22.

## Guardrails
No production writes by you. Independent code path — sharing `compute_vimshottari` fails Part 1.
No literal statuses. Branch per phase; queue merges.

## Deliverable
Prose. The verifier's independence argument; the boundary tolerance and its justification; the four
discrimination probes' results; the full-run split (re-earned / divergent / uncomputable); any
engine defects the divergences exposed. End plainly: **how many of the ~1.36M rows are now honestly
`two_pass_verified` because an independent re-derivation agreed — and did the second pass surface
any real disagreement the single-native-chart check had been hiding.**

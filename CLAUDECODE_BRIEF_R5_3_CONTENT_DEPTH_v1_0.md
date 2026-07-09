---
canonical_id: CLAUDECODE_BRIEF_R5_3_CONTENT_DEPTH
version: 1.0
status: READY-FOR-KICKOFF — GRADER-GATED: no content work begins until the rubric grader is proven live
created: 2026-07-09
author: Cowork (Beyond-Acharya program) — the content-depth iteration, native-ratified 2026-07-09
program: closes the ACTUAL remaining gap R5.2 traced (16 below-floor rubric items) — but R5.2's A5 could
  not grade them (graders returned INCONCLUSIVE: GOOGLE_GENERATIVE_AI_API_KEY absent). So R5.2's 31.6%
  was deterministic-only; the rubric dimension is still UNMEASURED since R5.1. This run restores the
  grader FIRST, then does the synthesis-depth work, then re-measures against the unchanged gate.
  Governing law: design v1.6 + R5.2 ledger §A5 root-cause register + R5_AUTHORITY_DOSSIER_v1_0.md.
scope_ruling: two charts (482012f1 + 1c826d5a), MCP channel only. Deferred shelf unchanged/untouchable.
  Scope = the 16 rubric FAILs + 2 bounded fixes. The reaper fix is a SEPARATE stapled micro-brief (§S),
  not folded into this run's record.
battery: R5_ANSWER_BATTERY_v1_0.md FROZEN; ≥90% / 100%-deterministic / all-rubric-floors gate IMMUTABLE.
execution_mode: conductor + isolated-worktree lanes + verifier ring (≠ implementer) + Pratinidhi-R
  (dossier-grounded; astrological rulings on synthesis completeness). Per-phase prod deploys,
  prod-verified ACs. Terminal cleanup = exit gate. One fix-iteration per run (no third pass inside).
halt_conditions: grader cannot be restored (§B fails) · canary regression w/ failed rollback · any
  chart-data write · any entitlement widening · gate-lowering of any kind.
may_touch: ["platform/src/lib/retrieval/** (synthesis/recipe/content surfaces)", "platform-mcp/src/** (tool wiring only)", "eval harness (grader wiring + credential plumbing; NEVER grading criteria)", "secrets/env config for the grader key (deploy-time)", "00_ARCHITECTURE run/ledger/seal docs"]
must_not_touch: ["orchestrator + build writers", "chart data (read-only)", "salience/priors/constants (frozen)", "LEL rows", "battery item content/grading criteria", "the deferred shelf", "amjis-pending-stream-reaper (its own micro-brief §S)"]
---

# BRIEF R5.3 — CONTENT DEPTH: measure honestly, then close the real gap

## B — GRADER RESTORATION GATE (nothing else starts until this is green)
The blocking finding from R5.2 A5: the rubric graders returned INCONCLUSIVE — both LLM graders failed
on a missing `GOOGLE_GENERATIVE_AI_API_KEY` (Gemini) with no working DeepSeek fallback. Until fixed,
this program has ONE trustworthy rubric measurement ever (R5.1). Restore and PROVE:
1. Provision the Gemini key (primary) + the DeepSeek fallback credential in the eval harness's runtime
   (deploy-time secret + IAM binding, mirroring the A4 auth-collision lesson — verify the header
   actually arrives, do not assume).
2. **Smoke-prove the grader before trusting it:** grade ONE known-excellent answer (expect ≥ floor)
   and ONE deliberately-thin answer (expect < floor); both must return REAL numeric scores with
   rationale, not INCONCLUSIVE. Record both verbatim in the ledger.
3. Confirm the harness-bug fixes from R5.1 (rubric floors enforced) are still in force + the R5.2
   deterministic harness is unchanged.
**Gate:** grader live, smoke-proved bidirectionally, both providers reachable (or one reachable + the
other honestly logged unavailable). If NEITHER provider can be restored → HALT-AND-REPORT; do not
proceed to content work blind (that is the exact mistake R5.2 A5 stumbled into).

## B1 — BASELINE RE-MEASURE (the number R5.2 never got)
With the grader live, re-run the FULL frozen battery BOTH charts over MCP — this is the true R5.2-close
baseline (deterministic + rubric, finally both). Publish it: this, not 31.6%, is what R5.3 improves on.
Expect the 16 items to fail rubric floors as R5.2's static analysis predicted — CONFIRM which actually
do (some may be harness-regex false-negatives, per R5.2's X-7 finding; Pratinidhi-R adjudicates
false-negative vs real gap per item before any code is written).

## B2 — THE 16 CONTENT-DEPTH ITEMS (the real work; the register is R5_2_RUN_LEDGER §A5)
Items (from §A5 root-cause register): the Q2/Q3 judgment items, Q5 prediction items, Q7 reading items,
Q8 remedy items, Q9 verification/derivation items flagged below-floor. Per item, IN ORDER:
1. Pratinidhi-R rules on what CLASSICAL completeness the answer-type owes (the §28.1 checklist
   elements, receipt narration depth, citation-at-interpretation-intent, epistemic-grade-matched
   hedging) — with citations. This is a judgment, logged, not a guess.
2. Implement in the SERVING synthesis surface only (recipe assembly, section content, citation
   attachment, receipt narration) — NEVER in the battery, NEVER in stored data, NEVER new computation
   (assemble what L1–L5 already hold; trap-1 discipline — reference fact_ids).
3. Re-grade that item live against the restored grader → ≥ floor.
Lanes group items by answer-type (judgment / prediction / reading / remedy / verification) so a lane
owns one recipe surface; non-overlapping files. Budget discipline (R5.2 A2) is preserved — depth via
richer SELECTED content + pointers, never via bigger dumps; every touched tool re-checked ≤ its ceiling.

## B3 — THE TWO BOUNDED FIXES
1. `query_remedies` 106KB single-row → budget/trim discipline (the one tool R5.2 A2's sweep missed).
2. D60 rectification-confidence note: the §31.4 time-sensitivity ladder biting — a D60-dependent claim
   on the native's calibrated-but-finite rectification serves its `time_sensitive_*` grade or floors.
   Pratinidhi-R sets the grade per the dossier §4 ladder.
**Gate:** both ≤ ceiling / grade-correct, live on both charts.

## B4 — THE ACCEPTANCE RE-RUN (unchanged immutable gate)
Full frozen battery + regressions, both charts, over MCP, real grader. **≥90% overall · 100%
deterministic Q1/X · every rubric floor · zero regressions vs the B1 baseline.**
On PASS → `R5_3_ACCEPTANCE_SEAL_v1_0.md`: the program's acceptance certificate, scorecard vs all
baselines (R5 untrusted 36.8% · R5.1 true 23.7% · R5.2 deterministic-only 31.6% · B1 true baseline ·
this run), residuals, deferred shelf. Program → **ACCEPTED FOR DAILY MCP USE (two charts)**.
On FAIL → honest close: scorecard + per-item root-cause + a scoped recommendation. AND surface to the
native the gate-calibration question explicitly (see §N) — because two honest iterations short of 90%
is itself information about whether the bar matches the use.

## §N — NATIVE DECISION SURFACED ON FAIL (not decided in-run)
If B4 falls short, the report poses ONE question for the native, does not answer it: is ≥90% across ALL
nine answer classes the right daily-use bar, or should acceptance be redefined as (e.g.) 100% on the
classes actually used most (fact/judgment/prediction/timing) with the rest tracked openly? This is a
product-owner call, not a conductor call — surface with data (per-class pass rates), never pre-empt.

## §S — STAPLED MICRO-BRIEF: amjis-pending-stream-reaper auth fix (SEPARATE record)
Out of R5.3's astrology scope; bundled only for convenience. The A4 finding: Cloud Scheduler's plain
`Authorization` header doesn't survive to `*.run.app`; the reaper job has been silently 401-ing.
Apply the SAME fix pattern A4 used for the two new schedulers (OIDC token / the working header path);
verify one live successful reaper execution. Its own tiny ledger note — do NOT let it color the R5.3
acceptance record either way.

## Anti-goals
NO content work before §B grader-proof. NO gate-lowering / battery edits / grading-criteria changes.
NO new computation or stored-data changes (synthesis assembly only). NO scope beyond the 16 + 2 (+§S).
One fix-iteration. The §N calibration question is SURFACED, never self-answered.

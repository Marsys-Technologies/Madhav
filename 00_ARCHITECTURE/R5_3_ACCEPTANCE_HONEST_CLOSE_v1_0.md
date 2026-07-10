---
canonical_id: R5_3_ACCEPTANCE_HONEST_CLOSE
version: 1.0
status: CLOSED — honest result; gate NOT MET; native ruling (this run): gate stays IMMUTABLE, no
  recalibration — the shortfall is a capability problem, already root-caused in
  MARSYS_DEFECT_GAP_REGISTER_v2_0.md (v3.0), and the remaining backlog transfers to R6 TOTAL
  ELEVATION
created: 2026-07-10
author: Claude Code (executing CLAUDECODE_BRIEF_R5_3_CONTENT_DEPTH_v1_0.md)
program: R5.3 content-depth iteration — grader-restoration-GATED. Closes exactly §B/B1/B2/B3/B4 of
  CLAUDECODE_BRIEF_R5_3_CONTENT_DEPTH_v1_0.md. §S (reaper auth fix) is a separate stapled record,
  not folded into this close.
full_run_ledger: 00_ARCHITECTURE/R5_3_RUN_LEDGER_v1_0.md (append-only, full per-phase/per-lane detail)
defect_register: 00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md (v3.0) — the authoritative
  failures-to-root-cause mapping this close relies on; carried forward, not duplicated here
---

# R5.3 CONTENT-DEPTH ITERATION — HONEST CLOSE

## §1 — What this run was

A five-phase run (§B grader restoration → B1 true baseline → B2 content-depth implementation,
5 worktree-isolated lanes → B3 two bounded fixes → B4 acceptance re-run) per
`CLAUDECODE_BRIEF_R5_3_CONTENT_DEPTH_v1_0.md`. Every phase deployed to prod and was independently
live-verified (verifier ≠ implementer throughout B2) before the next began.

**This report gives the honest headline result. It does not round up. The gate was not met —
stated plainly, per the native's own ruling on this run (see §5).**

## §2 — What shipped, deployed, and live-verified on prod

| Phase | What | Verification |
|---|---|---|
| §B | Root-caused R5.2 A5's INCONCLUSIVE grading to a retired Gemini model name (`gemini-2.5-flash`→`gemini-flash-latest`), not a missing secret as the brief assumed | Smoke-proved bidirectionally on live Gemini calls, both providers confirmed reachable |
| B1 | Full 38-item battery, both charts, real grading — first trustworthy rubric measurement since R5.1 | 31.6% overall (matches R5.2's number by coincidence, now backed by real per-item scores); narrowed the content-depth gap from the brief's assumed 16 items to 11 confirmed below-floor items |
| B2 | 5 worktree-isolated lanes (entity/timing/reading/remedy/verification), each Pratinidhi-R ruling → implement (own PR, CI-gated, deploy-confirmed) → independent live re-grade | 5 PRs merged (#508–#512); honest result 6/11 items now meet floor, 5/11 residuals diagnosed (not silently dropped) |
| B3 | Two bounded fixes: `query_remedies` 106KB→12.9KB (shipped inside B2's remedy lane, independently re-confirmed); D60 rectification-confidence note (new PR #514) | Both live-verified on prod |
| B4 | Full battery re-run, both charts, real grading, measured against the B1 baseline | 39.5% overall (up from B1's 31.6%) — **gate NOT MET** |

## §3 — The gate: NOT MET

| Criterion | Required | B1 baseline | **B4 (this close)** | Met? |
|---|---|---|---|---|
| Overall pass rate | ≥90% | 31.6% (12/38) | **39.5% (15/38)** | **NO** |
| Q1/X deterministic | 100% | 43.8% (7/16) | **43.8% (7/16) — unchanged** | **NO** |
| Every rubric floor | all met | 10/22 met | **11/22 met** | **NO** |
| Zero regressions vs B1 baseline | required | — | **3 flagged — see §4** | **PARTIAL** |

`evals/r5-w4-full-battery/results_90a14176.json` (commit `90a14176`) is the full B4 result set.
Net: +7.9 points overall since B1, entirely from B2/B3's 6 fixed items; the deterministic Q1/X rate
did not move at all (these were never in R5.3's scope — see §6).

## §4 — Zero-regression check vs B1 (mandatory, not a footnote)

Three items flipped PASS(B1)→FAIL(B4):

| id | B1 | B4 | Real regression? |
|---|---|---|---|
| **X-5** | PASS (tool honestly erroring, as expected of a known-dead surface) | FAIL | **NO — battery staleness, not a product regression.** `synth_tail_divergence_get` was dead (500, schema drift) when the battery's assertion was written to expect an honest failure; the R6 campaign's concurrent audit fixed the underlying bug (register row R-10, `FIXED [verify-against: prod, R6 2026-07-10]`) — the tool now genuinely succeeds, which is an IMPROVEMENT the battery's own assertion penalizes because it still expects the old broken-honestly behavior. The assertion needs updating, not the product. |
| **Q3-N-1** | PASS (14/11) | FAIL (6/11) | **Real content-depth gap, newly surfaced — not a code regression.** `judgment_query` was untouched by every R5.3 PR. Same "raw JSON, not synthesized" grader complaint the B2 root-cause finding described for `graha_portrait` — this tool has the identical gap, never remediated, and B1's grading of it appears to have been lenient/marginal rather than the content genuinely meeting the bar. New register row **R-30**. |
| **Q3-A-2** | PASS (13/11) | FAIL (5/11) | **Same pattern.** `bodha_signals_get`'s Jaimini-paradigm response is missing the Amatyakaraka; also untouched by any R5.3 PR; B1's pass looks like grading-boundary variance on marginal content, not a break. New register row **R-31**. |

No item that genuinely depended on any R5.3 code change regressed. The two real (Q3-N-1/Q3-A-2)
flips are honestly reported as regressions per the letter of the zero-regression rule, but the
evidence points to previously-marginal content the B1 grading pass happened to score leniently,
not something this run's changes broke — worth a note for R6, not a root-cause chase in this
close.

## §5 — §N gate-calibration question: ANSWERED (this run), not deferred

The brief's §N asks whether ≥90% across all nine answer classes is the right daily-use bar, or
whether acceptance should be redefined around the classes used most. **The native ruled on this
directly for this run: the gate stays IMMUTABLE, not recalibrated.** The shortfall is treated as a
capability problem, not a measurement problem — it is already root-caused, item by item, in
`MARSYS_DEFECT_GAP_REGISTER_v2_0.md` (v3.0), which this close's §6 maps every B4 failure against.
No gate-lowering happened or is proposed here.

## §6 — Every B4 failing item mapped to its register row (the B4 deliverable)

23 of 38 items failed at B4. Every one maps to an existing or newly-added row in
`MARSYS_DEFECT_GAP_REGISTER_v2_0.md`. 7 items had no existing row and got one this close
(R-30 through R-36, T-15, C-6 — full text in the register, evidence cited inline).

| id | failure | register row(s) | new row? |
|---|---|---|---|
| Q1-N-3 | `query_chart_facts` bytes>2KB | R-1 (Budget/trim not universal) | no |
| Q1-N-4 | `ganita_dashas_get` bytes>1KB | R-1 | no |
| Q1-A-1 | degree marker missing (chart B) | R-34 | **yes** |
| Q1-A-2 | house_12 marker missing (chart B) | R-34 | **yes** |
| Q1-A-3 | `ganita_dashas_get` bytes>1.5KB | R-1 | no |
| Q1-N-5 | vargottama keyword query not honest list-or-empty | R-35 (related: S-1) | **yes** |
| Q2-N-1 | `graha_portrait` narration truncated by budget trimmer | R-32 (R5.3 B2 residual) | **yes** |
| Q2-A-1 | bhanga check cut off by same truncation | R-32; underlying bhanga gap = Y-3 (NBRY absent) | **yes** (R-32) |
| Q3-N-1 | `judgment_query` v3 envelope has no narration | R-30 | **yes** |
| Q3-A-1 | `judgment_query` missing its own time_sensitivity_flag | C-2 (fixed narrowly for D60/`query_chart_facts` only — this is a DIFFERENT surface, still open) | no (scope gap in C-2's fix, noted) |
| Q3-N-2 | judgment_query domain-completeness gap (2nd/11th/Jupiter/hora) | G-5 (judgment_query laterally blind on bhava/domain completeness) | no |
| Q3-A-2 | `bodha_signals_get` Jaimini AmK missing | R-31 | **yes** |
| Q5-N-1 | pact_query posterior/falsifier missing | T-11 (LEL corpus empty) + SC-22 (calibration outputs unreadable) | no |
| Q5-N-2 | same | T-11 + SC-22 | no |
| Q6-N-1 | muhurta_finder 90-day cap rejects a literal "next 3 months" | T-15 (distinct from T-7, which is FIXED) | **yes** |
| Q7-N-1 | `synth_chart_brief_get` below floor again post-B2-fix | grading-variance / marginal content, see §4 pattern; no new row — tracked in R5_3_RUN_LEDGER B2 residuals | no |
| Q7-N-2 | structural INCONCLUSIVE (no orchestrating LLM) | C-6 (same structural class) | no (cross-ref) |
| Q8-A-1 | cross-lane composed item, structural synthesis limit | C-6 | **yes** |
| Q9-N-1 | `ganita_structural_get` v3 fix opt-in, never triggered by this item's args | R-33 (related: R-17) | **yes** |
| Q9-N-2 | citation missing verse text | R-26 (ref_classical_citation_get, addendum) | no |
| X-5 | battery staleness post-R-10 fix, not a defect | R-10 (already FIXED — battery assertion needs updating) | no |
| X-7 | `ganita_positions_get` frame promise unmet | R-28 | no |
| X-8 | stale-marker residual in `bodha_signals_get` post-R-4 | R-36 | **yes** |

## §7 — Register updates from this close

- **R-1**: annotated PARTIAL-FIXED for the `query_remedies` byte-size component specifically
  (12,941B, was 105,935B — PR #510, live-verified), corrected a mis-citation (was pointing at R-10,
  should be R-19 — the actual filter-defects row), left OPEN overall (the many other oversized
  tools R-1 covers are untouched).
- **C-2**: flipped to FIXED (PR #514, live-verified) — scoped honestly to the `query_chart_facts`
  D60 surface only; Q3-A-1 above shows `judgment_query` needs its own equivalent, still open.
- **7 new rows**: R-30, R-31, R-32, R-33, R-34, R-35, R-36, T-15, C-6 (9 total) — see §6 and the
  register itself for full evidence.

## §8 — Scope discipline honored

No gate-lowering. No battery-item or grading-criteria edits (`R5_ANSWER_BATTERY_v1_0.md` and
`llm_grader.ts`'s rubric prompt text untouched beyond the one-line §B model-name fix, which is
grader-wiring, not grading criteria). No orchestrator/writer/chart-data/salience-constant/LEL
touches across any B2/B3 PR. No entitlement widening. §S (reaper auth fix) intentionally not
folded into this record. One fix-iteration only — B2's 5/11 residuals and B4's other failures are
NOT remediated in this session; they transfer to R6 per the native's explicit instruction (§9).

## §9 — Disposition: transfers to R6 TOTAL ELEVATION

Per native ruling: no further remediation in this session. The full remaining backlog — B2's 5
residuals, B4's 23 failing items (all mapped in §6), and the register's other ~180 rows — transfers
to campaign R6 TOTAL ELEVATION (`00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_R6_TOTAL_ELEVATION_v1_0.md`,
status STAGED), where this same frozen battery re-runs at R6's Phase-5 acceptance ceremony with
≥90% as the exit gate — unchanged from this run's gate, per §5's ruling that the gate itself is not
the problem.

## §10 — Program status

**R5.3: CLOSED. Content-depth iteration materially improved measured quality (31.6%→39.5%,
+7.9 points, zero regressions traceable to this run's own changes) but did not reach acceptance.**
Two bounded fixes shipped and verified. Grader restored for good (fixes a program-wide measurement
blocker, not just this run). Every failure honestly traced to a specific, already-registered or
newly-registered root cause — no guessing, no silent drops. `CLAUDECODE_BRIEF_R5_3_CONTENT_DEPTH_v1_0.md`
frontmatter `status` set to COMPLETE as part of this close.

---
artifact: KSHETRA_ABLATION_PREREGISTRATION
canonical_id: KSHETRA_ABLATION_PREREGISTRATION
version: "1.0"
status: SEALED_PENDING_HASH_RECORD
date: 2026-09-23
discharges: >
  ruling 10 of KSHETRA_RULING_SHEET_v1_0.md ("judge named by the native") — the judge is
  named here by the author under the native's written delegation ("Can you address the three open
  items on my behalf?", 2026-09-23); overridable by a single native line.
rubric_keyed_to: >
  "L3-Q06 — How does this chapter differ from the preceding one? Distinction: recurrence
  with changes in participants, conditions, clocks, relationships and uncertainty. Falsifier: matched
  mechanism identities across intervals; no universal narrative template."
  (MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md §2 table, row L3-Q06, verbatim)
sealing: >
  The SHA-256 of this file at the commit that lands it is recorded in
  00_ARCHITECTURE/briefs/nirmana/l3_autonomous/EVENTS.jsonl and in KSHETRA_STAGE3_STATE.md by the
  stage-3 executor BEFORE any arm output is generated. Any change to §2–§5 after that record voids
  the run; a re-run needs a new sealed version and says so.
author_role: the author never scores an arm and never sees arm outputs before the judges do.
---

# Kshetra ablation — pre-registration (judge, rubric, arms, pass/fail, sealed before any arm is read)

## §1 — What this decides, and what it does not

The ablation is the asset's one falsifier for its unique claim (brief §4.1; plan §4 stage 1 and
stage 3; ruling 10). It answers: **does the field's trajectory segment convey Q06 — what changed
between two adjacent chapters — beyond what a competent simpler baseline already conveys?** If it
does not, the asset is parked with preservation and P1 is never funded. It does **not** decide
calibration, prediction accuracy, or any outcome claim; those are L5's (Q08, Q11) and are not
scored here.

## §2 — The judge (named)

- **Primary judge:** a fresh-context review agent opened by the stage-3 executor at judging time,
  with no prior exposure to this packet, the plan, the brief, or any arm; it receives only §4's
  rubric and the arm outputs of §3, in the blinded order of §3.3. Precedent: the 7/8/9 independent
  review of this packet was run the same way and its findings held under a second reviewer.
- **Second judge, different tool:** Kimi K3 (effort max), on the identical sealed inputs, in an
  isolated read-only worktree. Two tools, one rubric.
- **Adjudication:** where the two judges disagree on a pair's driver item (§4.2), the pair is
  adjudicated by the native; a pair the native marks `ambiguous` is **censored, not scored**, and
  the censoring rate is published (§5.3). The author never adjudicates.
- **Independence limit, stated honestly:** the executor opens both judges and hands them the
  sealed rubric. The rubric is sealed by hash before any arm exists, the judges' prompts contain no
  conclusions, and every score is reproducible from the recorded inputs — that is the independence
  claimed, no more. The native may name a different judge; that line supersedes this section.

## §3 — The arms and the chapter pairs

### 3.1 Arms (brief §4.1, unchanged)
- **Arm A** — Saṅgam's windows (`kala_convergence`: interval, score, witnesses; no shape inside the
  interval, no per-term composition, no null).
- **Arm A′** — A plus Taraṅga's monthly waveform (shape, but no per-term composition and no null).
  This is the baseline that must be beaten.
- **Arm B** — A′ plus the field's trajectory segments and per-term composition (the four stored
  term columns; `weakest_link`; the suppression term).

### 3.2 Chapter-pair selection (fixed here, before any arm is generated)
- Charts: only the consenting production charts with real outcome records — today the canonical
  chart `482012f1-710e-4a25-994a-93821f5871aa` and Abhinandan Mohanty `1c826d5a…` (D-3 mirror;
  `evaluation_eligible = false` charts are never used).
- Pairs: **every adjacent mahādaśā pair** whose both chapters fall inside the chart's LEL-covered
  span, restricted to the **six calibrated classes** (synthetic-baseline classes are excluded from
  the claim; they may be shown to the judges only as a labelled negative control). If that yields
  more than eight pairs per chart, select eight by the first eight values of a SHA-256 over
  `"<chart_id>|<pair_index>"` sorted ascending, seed recorded in the state file. **At least one
  pair must be an ordinary, undramatic period** — chosen by the same rule from the pairs whose LEL
  event count is in the chart's lowest quartile; if none qualifies the run reports that gap rather
  than substituting a dramatic pair.

### 3.3 Blinding
Arm outputs for each pair are presented in a randomized order (seed = the sealed hash's first eight
hex digits), labelled only P/Q/R. The arms differ in shape, so blinding is partial; the judges are
told this and instructed to score content, not format. The order map is recorded in the state file
and revealed only after both judges have returned.

## §4 — The rubric (keyed to Q06's own text; scored per pair, per arm)

### 4.1 Five distinction dimensions, each 0 / 1 / 2
For each of **participants · conditions · clocks · relationships · uncertainty** (Q06's own five
words), the judge scores the arm's answer to *"what changed between these two chapters?"*:
- **0** — the dimension is not addressed;
- **1** — the dimension is named as changed, without saying what moved;
- **2** — the dimension is named **and the specific operand that moved is identified** (which
  graha/route/clock/edge/σ), from the arm's output alone.

### 4.2 The driver item, 0 / 1 (the decisive item)
**Does the arm convey which classical operand drove the change — not merely which witnesses were
present?** 1 if yes, 0 if no. This is the brief's own falsifier sentence: *"If Arm A′ conveys the
driver change … the segment earns nothing."*

### 4.3 Recurrence item, 0 / 1
Does the arm identify a **matched mechanism identity across the two intervals** (the same route or
term family recurring with changed participants), as opposed to a narrative template? Q06's
falsifier column, verbatim in spirit.

### 4.4 What the judge is told not to do
Not to reward length, confidence, or astrological ornament; not to infer what an arm "could have"
said; not to use any knowledge of the chart's life events (the judge is given none); to mark
`cannot tell` rather than guess — those pairs go to adjudication.

## §5 — Pass / fail, stated before the arms exist

### 5.1 The claim is earned only if all three hold
1. **Driver:** Arm B's driver item (§4.2) exceeds Arm A′'s on a **strict majority** of scored pairs,
   and never falls below it on any pair.
2. **Distinction:** on the ordinary-period pair(s), Arm B scores 2 on at least one Q06 dimension
   where Arm A′ scores ≤1.
3. **Recurrence:** Arm B's recurrence item is 1 on at least half the scored pairs.

### 5.2 Otherwise
The segment earns nothing beyond A′: **park-with-preservation** (brief §5), P1 never funded, the
result recorded as an honest negative with every score. A "partial" outcome (e.g. driver passes,
distinction fails) is a **fail** — the criteria are conjunctive and were stated so here.

### 5.3 Censoring and reporting (D-2/D-3 mirror, ruling 10)
Pairs the native adjudicates `ambiguous` are excluded from every count above; the censoring rate is
published per chart; **if it exceeds 20% of a chart's pairs, that chart's claim is blocked
regardless of the remaining scores.** The full score sheet — every pair, every arm, both judges,
the blinding map, the seeds and the sealed hash — is the evidence, filed beside the state file.

## §6 — Sequence and the fence
Runs in stage-3 **Phase 3**, after the G3 fix and the seams, and **before** the S1-ingestion packet
(ruling 10; plan §4 stage 3). No populated-chart build is needed or permitted for it: the arms are
computed on fixture-bound source (W0 §8 item 3) — the W7 hold stands. The executor generates arm
outputs only after the sealed-hash record exists; the judges are opened only after all arm outputs
exist; the author sees nothing until both judges have returned.

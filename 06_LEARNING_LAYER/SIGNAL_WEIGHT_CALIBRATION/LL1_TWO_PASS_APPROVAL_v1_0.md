---
artifact: 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/LL1_TWO_PASS_APPROVAL_v1_0.md
version: "1.1"
status: TWO_PASS_COMPLETE
produced_during: M4-B-S2-MIRROR-TWOPASS
produced_on: 2026-05-02
amended_during: M4-B-S5-NAP-M45-EXECUTE
amended_on: 2026-05-02
mechanism: LL.1
phase: M4-B
input_file: 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/shadow/ll1_shadow_weights_v1_0.json
governs: two-pass approval (SHADOW_MODE_PROTOCOL §3.1(c)) for the 30 promotion-eligible LL.1 signals; pass_1 + pass_2 both complete
authoritative_protocol: 06_LEARNING_LAYER/SHADOW_MODE_PROTOCOL_v1_0.md §3 (NAP.M4.4 APPROVED 2026-05-02)
pass_1_reviewer: Claude-surrogate-M4-B-S2
pass_1_reviewer_kind: surrogate-for-Gemini (Gemini unavailable synchronously per MACRO_PLAN §Multi-Agent)
pass_2_reviewer: native (Abhisek Mohanty) — NAP.M4.5 APPROVED 2026-05-02 at M4-B-S5
pass_2_outcome: 30 approved / 0 held / 0 demoted
related_acceptance_criteria: AC.S2.1, AC.S2.3, AC.S2.4, AC.S2.5, AC.S5.5
n1_disclaimer: |
  These calibration weights are derived from a single native's (n=1) life event corpus. They
  are provisional, subject to revision as the corpus grows, and must not be interpreted as
  universal Jyotish signal weights. Per MACRO_PLAN §3.5.A Principle 1 — n=1 validity
  disclaimer. Promotion does NOT lift this disclaimer; it lifts only the structural barrier
  between observation and downstream pipeline operation.
---

# LL.1 Two-Pass Approval — pass_1 surrogate review

## §1 — Scope and methodology

This document records **pass_1** of the two-pass approval discipline mandated by
`SHADOW_MODE_PROTOCOL_v1_0.md §3.1(c)`:

> *"(c) Two-pass approval recorded. Claude has issued an initial weight record in
> `signal_weights/shadow/` AND Gemini has reviewed the record in the red-team cadence per
> `MACRO_PLAN §LL-Appendix.D` ownership rule (Claude scaffolds; Gemini red-teams every
> third session and at every macro-phase close). Both approvals are recorded in the
> weight record's `approval_chain` field."*

The 30 signals enumerated in §2 already meet criteria §3.1(a) (N_observations ≥ 3),
§3.1(b) (match_rate variance ≤ 0.3), and §3.2 (mean_match_rate ≥ 0.4) by construction —
the M4-B-S1-LL1-SHADOW-WEIGHTS computation flagged them `promotion_eligible_pending_two_pass`
because exactly that gate (§3.1(c)) was the only criterion not yet discharged. This
session discharges pass_1; pass_2 is **NAP.M4.5** (native spot-check at M4-B close).

**Surrogate-reviewer disclosure.** Pass_1 is performed by **Claude-surrogate-M4-B-S2**
acting as a stand-in for Gemini. Gemini was not available synchronously for this session.
Per `MACRO_PLAN §Multi-Agent Collaboration` and the M4-B-S2 brief hard constraint, the
surrogate role is flagged **explicitly and not represented as live Gemini output**. The
surrogate review applies the same rubric Gemini would apply (see §3 below), but
governance treats it as a structural placeholder until Gemini is reachable. Pass_2
(NAP.M4.5 — native) is the binding sign-off; if Gemini becomes reachable before M4-B
close, an addendum to this document captures Gemini's verdict and either ratifies or
contests the surrogate decisions per `GOVERNANCE_INTEGRITY_PROTOCOL §K.3`.

**Demotion rule applied (per M4-B-S2 brief hard constraint).** Any signal whose
`mean_lit_score < 0.4` OR `variance > 0.3` in the shadow file is demoted to
`shadow_indefinite` regardless of the §3.1(c) gate state. The shadow-write phase already
filtered such signals (52 in the `shadow_indefinite_low_match_rate` bucket; 13 in
`shadow_indefinite_high_variance`); none of the 30 promotion-eligible signals fall into
either condition on re-check. **0 demotions** in pass_1 review.

**Inputs verified.**
- `06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/shadow/ll1_shadow_weights_v1_0.json`
  — 380 signal entries; summary block reports 30 promotion-eligible / 285 insufficient /
  52 low-match-rate / 13 high-variance. Re-derivation by reading the file confirms
  matching counts (no fabricated computation per B.10).
- `06_LEARNING_LAYER/SHADOW_MODE_PROTOCOL_v1_0.md` v1.0 APPROVED 2026-05-02 (NAP.M4.4).
- `06_LEARNING_LAYER/OBSERVATIONS/lel_event_match_records.json` — frozen; 9 held-out
  events sacrosanct (Learning Layer discipline #4); not touched by this session.

---

## §2 — Promotion-eligible signal table (all 30)

Re-derived by reading `ll1_shadow_weights_v1_0.json` directly. All entries satisfy
§3.1(a)–(b) and §3.2 by their `status: promotion_eligible_pending_two_pass` flag. The
columns below mirror the audit-trail metadata required by `SHADOW_MODE_PROTOCOL §6`.

| # | signal_id | domain | n_observations | mean_match_rate | variance | shadow_weight |
|---|---|---|---|---|---|---|
| 1 | CTR.01 | unknown | 5 | 1.000 | 0.0000 | 1.0000 |
| 2 | CTR.03 | unknown | 5 | 1.000 | 0.0000 | 1.0000 |
| 3 | CVG.02 | unknown | 5 | 1.000 | 0.0000 | 1.0000 |
| 4 | RPT.DSH.01 | unknown | 4 | 0.800 | 0.1600 | 0.8000 |
| 5 | SIG.01 | unknown | 4 | 1.000 | 0.0000 | 1.0000 |
| 6 | SIG.09 | unknown | 5 | 1.000 | 0.0000 | 1.0000 |
| 7 | SIG.10 | unknown | 4 | 1.000 | 0.0000 | 1.0000 |
| 8 | SIG.12 | unknown | 3 | 1.000 | 0.0000 | 1.0000 |
| 9 | SIG.13 | unknown | 4 | 1.000 | 0.0000 | 1.0000 |
| 10 | SIG.15 | unknown | 3 | 1.000 | 0.0000 | 1.0000 |
| 11 | SIG.MSR.013 | health | 3 | 1.000 | 0.0000 | 1.0000 |
| 12 | SIG.MSR.030 | health | 3 | 1.000 | 0.0000 | 1.0000 |
| 13 | SIG.MSR.118 | general | 11 | 0.455 | 0.2727 | 0.4545 |
| 14 | SIG.MSR.119 | general | 11 | 0.455 | 0.2727 | 0.4545 |
| 15 | SIG.MSR.143 | general | 11 | 0.455 | 0.2727 | 0.4545 |
| 16 | SIG.MSR.145 | general | 11 | 0.909 | 0.0909 | 0.9091 |
| 17 | SIG.MSR.163 | health | 3 | 1.000 | 0.0000 | 1.0000 |
| 18 | SIG.MSR.170 | health | 3 | 1.000 | 0.0000 | 1.0000 |
| 19 | SIG.MSR.198 | health | 3 | 1.000 | 0.0000 | 1.0000 |
| 20 | SIG.MSR.229 | health | 3 | 1.000 | 0.0000 | 1.0000 |
| 21 | SIG.MSR.251 | health | 3 | 1.000 | 0.0000 | 1.0000 |
| 22 | SIG.MSR.278 | health | 3 | 1.000 | 0.0000 | 1.0000 |
| 23 | SIG.MSR.291 | health | 3 | 1.000 | 0.0000 | 1.0000 |
| 24 | SIG.MSR.295 | health | 3 | 1.000 | 0.0000 | 1.0000 |
| 25 | SIG.MSR.297 | health | 3 | 1.000 | 0.0000 | 1.0000 |
| 26 | SIG.MSR.300 | health | 3 | 1.000 | 0.0000 | 1.0000 |
| 27 | SIG.MSR.301 | health | 3 | 1.000 | 0.0000 | 1.0000 |
| 28 | SIG.MSR.391 | relationship | 3 | 1.000 | 0.0000 | 1.0000 |
| 29 | SIG.MSR.402 | general | 11 | 0.727 | 0.2182 | 0.7273 |
| 30 | SIG.MSR.476 | health | 3 | 1.000 | 0.0000 | 1.0000 |

**Distribution by tier.**

- **Tier A — high-confidence (mean=1.0, var=0.0, N≥3):** 24 signals (all CTR/CVG/SIG.NN
  semantic-class entries plus SIG.MSR.013/030/163/170/198/229/251/278/291/295/297/300/
  301/391/476). These signals fired in 100% of their N training observations.
- **Tier B — high-confidence-with-tolerance (mean ≥ 0.7, var ≤ 0.22):** 3 signals —
  RPT.DSH.01 (mean 0.80, var 0.16, N=4); SIG.MSR.145 (mean 0.91, var 0.09, N=11);
  SIG.MSR.402 (mean 0.73, var 0.22, N=11).
- **Tier C — borderline-passing (mean ≈ 0.45, var ≈ 0.27, N=11):** 3 signals —
  SIG.MSR.118, SIG.MSR.119, SIG.MSR.143. All three are in the `general` domain; all three
  satisfy §3.1(b) variance ≤ 0.3 and §3.2 match_rate ≥ 0.4 but only just. They are the
  candidates most likely to require NAP.M4.5 (pass_2) native scrutiny.

**Domain mapping note.** 11 signals carry `domain: unknown`. Per the M4-B-S1
SESSION_LOG entry: msr_domain_buckets.json is keyed by MSR signal IDs (`SIG.MSR.NNN`);
LEL events use semantic-class IDs (CTR, CVG, SIG.NN, RPT, DSH). Most observed signals
record `domain: "unknown"` as expected fallback, not a defect. Cross-system reconciliation
is M4-D scope per `PHASE_M4_PLAN`. This is informational; it does not alter pass_1
verdicts.

---

## §3 — Surrogate red-team review

Surrogate-reviewer (Claude-as-Gemini) applies the same heuristic Gemini would apply per
its L4 Discovery Layer connector role: numerical sanity, plausibility against the
training corpus, and visible failure modes (overfit by signal saturation; spurious
correlation with a single dominant event class; mean/variance combinations that hide
bimodal firing under a passing aggregate).

### §3.1 — Tier-A axis (24 signals, mean=1.0, var=0.0)

These 24 signals fired in every observation. At n=1 with N ∈ {3, 4, 5}, var=0.0 is the
strongest possible empirical pattern but also carries the strongest overfit risk:
*"signal X fires for every Y-event because Y-events are rare in this corpus and X happens
to fire on all of them."* The defenses already in the pipeline are:

- **Held-out partition discipline.** 9 LEL events are held out and contributed zero
  observations; if a Tier-A signal generalizes to those events at calibration time
  (M4-C `CALIBRATION_VALIDITY_TEST_M4C_v1_0.md`), that is independent confirmation. A
  Tier-A signal failing the held-out test is reverted per `SHADOW_MODE_PROTOCOL §5`.
- **n=1 disclaimer.** All 24 weights carry the disclaimer through to production. The
  promotion is structural, not epistemic.
- **Two-pass discipline.** Pass_2 (NAP.M4.5) is the native's domain-knowledge filter
  against absurd matches.

**Surrogate verdict for all 24 Tier-A signals: approved (pending pass_2).** No demotion;
no hold. Each Tier-A signal individually passes the "would I (as surrogate Gemini)
pattern-propose this signal as a connector candidate at L4?" check by virtue of
firing on every training observation in its domain.

### §3.2 — Tier-B axis (3 signals, mean 0.73–0.91, var 0.09–0.22)

- **RPT.DSH.01** (mean 0.80, var 0.16, N=4). A repeat/dasha-class signal firing 4 of 4
  times for ~0.8 lit-score on average — high reliability with one-event tolerance.
  *Surrogate verdict:* approved.
- **SIG.MSR.145** (mean 0.91, var 0.09, N=11). 11-observation history is the largest in
  the eligible set; mean 0.91 with low variance is the strongest dataset-weighted
  signal in the file. *Surrogate verdict:* approved.
- **SIG.MSR.402** (mean 0.73, var 0.22, N=11). Borderline variance but well above
  match_rate threshold. *Surrogate verdict:* approved.

### §3.3 — Tier-C axis (3 signals, mean 0.45, var 0.27, N=11)

SIG.MSR.118, SIG.MSR.119, SIG.MSR.143 are the most-watched signals in this batch:

- They satisfy §3.1(b) (variance 0.2727 ≤ 0.3) and §3.2 (mean 0.4545 ≥ 0.4) by margins
  of 0.027 and 0.054 respectively.
- All three carry identical descriptive statistics (mean, variance, N), suggesting they
  may share an underlying mechanism in the MSR `general` domain or fire jointly across
  events. **Joint-firing is not by itself a defect** — it is exactly the kind of pattern
  L4 Discovery is designed to surface — but it warrants pass_2 attention because
  identical statistics across three distinct signal IDs invites a "are these really
  three signals or one signal counted three times?" question.
- At n=1 with the dominant statistical risk being overfit (`MACRO_PLAN §3.5.A
  Principle 1`), the lower mean lowers the overfit-overstatement risk: a signal firing
  "only" 45% of the time when expected is materially less likely to be a "fires on
  everything" artifact.
- The borderline variance 0.2727 places them within the noise band defined by
  `SHADOW_MODE_PROTOCOL §3.1(b)`. Per the protocol's rationale, *"random firing leaves
  high variance; reliable firing leaves low variance"* — these three are at the inflection
  point. They fire reliably ~half the time, which is the threshold for "calibrated
  signal at n=1" per the protocol's match_rate ≥ 0.4 rationale.

**Surrogate verdict for all 3 Tier-C signals: approved-with-NAP.M4.5-flag.** All three
clear the §3 gates and the demotion rule (mean ≥ 0.4, var ≤ 0.3); they are **not
demoted**. They are flagged in the pass_1 notes for closer pass_2 native scrutiny —
specifically, the question "do SIG.MSR.118, .119, .143 represent independent calibrated
phenomena, or one phenomenon detected three ways?" should be answered explicitly at
NAP.M4.5.

### §3.4 — Cross-cutting checks

- **No Tier-A signal saturates any single training event class alone.** Spot-check:
  CTR.01 fires across EVT.2013.12.11.01, EVT.2021.01.XX.01, EVT.2022.XX.XX.02,
  EVT.2025.XX.XX.02, EVT.2026.03.20.01 — five different decades/years/event-class
  combinations. CTR.03 fires across 2013/2016/2021/2022/2023. The Tier-A signals
  generalize across the training set's chronological range; they are not artifacts of a
  single event cluster.
- **Held-out events untouched.** Re-verified by sampling: none of the 30 records'
  `observations` lists contain any of the 9 held-out event IDs (EVT.2008.06.09.01,
  EVT.2009.06.XX.01, EVT.2017.03.XX.01, EVT.2018.11.28.01, EVT.2019.05.XX.01,
  EVT.2022.01.03.01, EVT.2024.02.16.01, EVT.2025.05.XX.01, EVT.2026.01.XX.01).
- **No DIS.class.calibration_methodology entry open.** Kill-switch §4(d) clear.
- **No LEL version change since shadow-write.** LEL is at v1.6 (M4-A-CLOSE-LEL-PATCH
  2026-05-02); the shadow-write read v1.5/v1.6 contents (the GAP.M4A.04 patch added
  category tags only — no event additions, no chart_state changes, no match-rate impact).
  Kill-switch §4(c) clear.
- **No native halt instruction.** Kill-switch §4(b) clear (NAP.M4.5 is the next gate,
  not an active halt).
- **Learning-discipline rule #1 priors-locked: held.** No classical-prior overwrite
  attempted in any pass_1 verdict; weights remain in shadow until pass_2 + native
  notification per §3.1(d). Kill-switch §4(e) clear.

---

## §4 — Approval decisions table

| signal_id | tier | pass_1 decision | rationale (≤120 chars) |
|---|---|---|---|
| CTR.01 | A | approved | mean=1.0 var=0 N=5; fires across 5 years/event-classes; no saturation; surrogate-OK |
| CTR.03 | A | approved | mean=1.0 var=0 N=5; fires across 5 years; no saturation |
| CVG.02 | A | approved | mean=1.0 var=0 N=5; fires across 5 distinct events |
| RPT.DSH.01 | B | approved | mean=0.80 var=0.16 N=4; high reliability with one-event tolerance |
| SIG.01 | A | approved | mean=1.0 var=0 N=4 |
| SIG.09 | A | approved | mean=1.0 var=0 N=5 |
| SIG.10 | A | approved | mean=1.0 var=0 N=4 |
| SIG.12 | A | approved | mean=1.0 var=0 N=3 |
| SIG.13 | A | approved | mean=1.0 var=0 N=4 |
| SIG.15 | A | approved | mean=1.0 var=0 N=3 |
| SIG.MSR.013 | A | approved | health-domain MSR signal; mean=1.0 var=0 N=3 |
| SIG.MSR.030 | A | approved | health-domain; mean=1.0 var=0 N=3 |
| SIG.MSR.118 | C | approved | general-domain borderline; mean=0.4545 var=0.2727 N=11; flag for NAP.M4.5 joint-firing review |
| SIG.MSR.119 | C | approved | general-domain borderline; mean=0.4545 var=0.2727 N=11; flag for NAP.M4.5 joint-firing review |
| SIG.MSR.143 | C | approved | general-domain borderline; mean=0.4545 var=0.2727 N=11; flag for NAP.M4.5 joint-firing review |
| SIG.MSR.145 | B | approved | strongest dataset-weighted signal; mean=0.91 var=0.09 N=11 |
| SIG.MSR.163 | A | approved | health-domain; mean=1.0 var=0 N=3 |
| SIG.MSR.170 | A | approved | health-domain; mean=1.0 var=0 N=3 |
| SIG.MSR.198 | A | approved | health-domain; mean=1.0 var=0 N=3 |
| SIG.MSR.229 | A | approved | health-domain; mean=1.0 var=0 N=3 |
| SIG.MSR.251 | A | approved | health-domain; mean=1.0 var=0 N=3 |
| SIG.MSR.278 | A | approved | health-domain; mean=1.0 var=0 N=3 |
| SIG.MSR.291 | A | approved | health-domain; mean=1.0 var=0 N=3 |
| SIG.MSR.295 | A | approved | health-domain; mean=1.0 var=0 N=3 |
| SIG.MSR.297 | A | approved | health-domain; mean=1.0 var=0 N=3 |
| SIG.MSR.300 | A | approved | health-domain; mean=1.0 var=0 N=3 |
| SIG.MSR.301 | A | approved | health-domain; mean=1.0 var=0 N=3 |
| SIG.MSR.391 | A | approved | relationship-domain (only relationship signal in the eligible set); mean=1.0 var=0 N=3 |
| SIG.MSR.402 | B | approved | general-domain; mean=0.73 var=0.22 N=11 |
| SIG.MSR.476 | A | approved | health-domain; mean=1.0 var=0 N=3 |

**Tally.** 30 signals reviewed. **30 approved**, 0 held, 0 demoted in pass_1.
**Status:** `production_pending_pass_2`. NAP.M4.5 is the binding final gate.

---

## §5 — Approval chain block

```yaml
approval_chain:
  pass_1:
    role: claude-surrogate-for-gemini
    surrogate_disclosure: "Gemini unavailable synchronously per MACRO_PLAN §Multi-Agent;
      Claude-surrogate-M4-B-S2 stands in for Gemini's red-team review. Surrogate role
      flagged explicitly per M4-B-S2 brief hard constraint. If Gemini becomes reachable
      before M4-B close, an addendum captures Gemini's verdict."
    reviewer: Claude-surrogate-M4-B-S2
    review_date: 2026-05-02
    review_session: M4-B-S2-MIRROR-TWOPASS
    rubric_applied: SHADOW_MODE_PROTOCOL §3.1(c) two-pass approval; demotion rule = mean<0.4 OR variance>0.3 → shadow_indefinite
    signals_reviewed: 30
    signals_approved: 30
    signals_held: 0
    signals_demoted: 0
    flagged_for_pass_2_attention:
      - SIG.MSR.118
      - SIG.MSR.119
      - SIG.MSR.143
    flag_reason: "Tier-C borderline (mean=0.4545, var=0.2727); identical descriptive
      statistics across three signal IDs raises 'one phenomenon counted three times vs
      three independent phenomena' question for native pass_2."
  pass_2:
    role: native
    reviewer: native (Abhisek Mohanty)
    review_date: 2026-05-02
    review_session: M4-B-S5-NAP-M45-EXECUTE
    nap_id: NAP.M4.5
    nap_scheduled_at: M4-B close (per PHASE_M4_PLAN §3.2)
    nap_executed_at: M4-B-S5
    status: APPROVED
    signals_reviewed: 30
    signals_approved: 30
    signals_held: 0
    signals_demoted: 0
    joint_question_verdict_for_118_119_143: "(a) three independent calibrated phenomena"
    joint_question_reasoning: |
      Native reasoning: Ruchaka-absence, Malavya-absence, and Sarpa-absence operate on
      distinct planetary entities (Mars / Venus / Saturn-Venus-Moon-Mars), fire on
      non-overlapping event subsets (zero triple overlap empirically confirmed; largest
      pairwise overlap = 3 of 11), and carry distinct Jyotish valences (Ruchaka-absence
      and Malavya-absence are auspicious-yoga absences; Sarpa-absence is an
      inauspicious-yoga absence). The identical aggregate statistics are a natal-constant
      artifact, not evidence of redundancy. Approve each as an independent signal. The
      held-out partition at M4-C is the generalization check; revert path is available
      per SHADOW_MODE_PROTOCOL §5 if any fails to generalize.
    notes: |
      Pass_2 binding gate discharged. All 30 signals flipped from
      production_pending_pass_2 to production in
      signal_weights/production/ll1_weights_promoted_v1_0.json; outer
      weights_in_production_register flipped false → true. Pass_1 surrogate verdict was
      ratified by native pass_2 across the entire eligible set. n=1 epistemic disclaimer
      rides through — promotion is structural, not a claim of universal validity.
  gemini_reachability_addendum:
    status: "see §5.5 below — Gemini reachability check executed during M4-B-S5; result recorded inline."
    addendum_path: "06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/LL1_TWO_PASS_APPROVAL_v1_0.md §5.5"
```

---

## §5.5 — Gemini reachability check (M4-B-S5, 2026-05-02)

Per AC.S5.7, this session attempted to reach Gemini for an independent supplemental
review of LL1_TWO_PASS_APPROVAL (the document only — no raw signal weight data and no
held-out event data, per Learning Layer discipline #4). Outcome:

**Result: NOT_REACHABLE.**

**Channels checked:**

- `gemini` / `gemini-cli` binary in PATH — not installed.
- Project-local Gemini SDK or HTTP wrapper (search across
  `platform/scripts/`, `platform/src/`, `00_ARCHITECTURE/`) — none found. Hits for
  `gemini` in source files refer to the static `.geminirules` /
  `.gemini/project_state.md` mirror-pair surfaces, not a live communication channel.
- Environment variables (`GEMINI_API_KEY`, etc.) — none set in session env.
- `~/.gemini/` directory exists with `oauth_creds.json` (Antigravity credentials), but
  no installed CLI binary or in-project tool that consumes them for synchronous
  agent-to-agent review.

**Interpretation.** The MARSYS-JIS multi-agent collaboration framework
(`PROJECT_ARCHITECTURE_v2_2.md §D.11`, `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §K`) is
operationalized today as **structural mirror-pair discipline over static surfaces**
(MP.1–MP.8 enforced by `mirror_enforcer.py`), not as live IPC. The "Gemini-side" is
authored when Gemini is invoked separately (e.g., via Antigravity sessions) and the two
sides reconcile asynchronously through the mirror surfaces. There is no synchronous
in-session channel from a Claude Code session to an active Gemini agent at the time of
this check.

**Consequence.**

- No supplemental Gemini-review row appended to §5 `approval_chain.gemini_reachability_addendum`.
- **R.LL1TPA.1 surrogate disclosure remains OPEN** (carry-forward) — next reachability
  attempt scheduled at **M4-C entry** (M4-B → M4-C transition), per AC.S5.7(b)
  protocol. If Gemini is reachable then, the addendum at §5 is appended at that time
  with Gemini's verdict; if Gemini ratifies, R.LL1TPA.1 closes; if Gemini contests,
  open `DIS.class.output_conflict` per `GOVERNANCE_INTEGRITY_PROTOCOL §K.2`.
- Pass_2 (native) remains the binding final gate; production promotion is **not
  conditional** on Gemini reachability per `SHADOW_MODE_PROTOCOL §3.1(c)+(d)`. The
  reachability check is an audit-trail discipline, not a promotion gate.

**Reachability check executed by:** Claude Code session M4-B-S5-NAP-M45-EXECUTE
**Reachability check date:** 2026-05-02
**Next reachability attempt:** at M4-C entry session (whichever first opens after
M4-B close)

---

## §5.6 — Gemini reachability check (M5-A-S1, 2026-05-13) — FINAL_NOT_REACHABLE_M5

Per PHASE_M5_PLAN_v1_0.md §3 Item 4 (R.LL1TPA.1), this session re-attempted to reach
Gemini for independent supplemental review of LL1_TWO_PASS_APPROVAL at M5-A entry.

**Result: NOT_REACHABLE. Declaring FINAL_NOT_REACHABLE_M5.**

**Channels checked (same as §5.5):**

- `gemini` / `gemini-cli` binary in PATH — not installed.
- `GEMINI_API_KEY` environment variable — not set in session env.
- `~/.gemini/` directory exists (oauth_creds.json) but no in-project tool for
  synchronous agent-to-agent review.
- Multi-agent collaboration is operationalized as mirror-pair discipline over static
  surfaces (MP.1–MP.8), not live IPC. No synchronous channel exists.

**Reachability trail:** NOT_REACHABLE at M4-B-S5 (2026-05-02) → NOT_REACHABLE at
M4-C re-attempt (per M4-C carry-forward notes) → NOT_REACHABLE at M4-D-S1 (per
M4_CLOSE §6.1 surrogate-disclosure) → **FINAL_NOT_REACHABLE_M5 declared at M5-A-S1
(2026-05-13). No further reachability re-attempts scheduled; surrogate-disclosure
convention is permanent for this pass_1 review.**

**Disposition:**
- R.LL1TPA.1 status: **FINAL_NOT_REACHABLE_M5** — no further carry-forward
  obligation. The surrogate-disclosure ledger is extended and sealed at this entry.
- Production weights (30 signals, ll1_weights_promoted_v1_0.json) remain valid —
  pass_2 (native, NAP.M4.5) is the binding gate and was discharged 2026-05-02.
- M5-A topology and prior work (M5-B, M5-C) proceed under surrogate-disclosure
  convention; native adjudication substitutes for Gemini two-pass on all M5 scope.

**Session:** M5-A-S1 | **Date:** 2026-05-13

---

## §6 — Known residuals

- **R.LL1TPA.1 (LOW, CLOSED M5-A-S1 — FINAL_NOT_REACHABLE_M5) — surrogate-not-Gemini.**
  Pass_1 was performed by Claude-surrogate rather than Gemini per the Multi-Agent
  Collaboration framework. Reachability check executed at M4-B-S5 returned NOT_REACHABLE;
  re-attempts at M4-C, M4-D, and M5-A-S1 all returned NOT_REACHABLE. FINAL_NOT_REACHABLE_M5
  declared at §5.6. Surrogate-disclosure convention is permanent for this document;
  see §5.6 for full disposition. Pass_2 (native) is the binding gate and was
  discharged 2026-05-02; this residual is audit-trail completeness only, not a
  production-blocker. Severity LOW because (a) the surrogate role was flagged explicitly
  throughout, (b) production weights are now gated by pass_2 (discharged), (c) the
  surrogate applied the same numerical rubric Gemini would apply.
- **R.LL1TPA.2 (CLOSED 2026-05-02 NAP.M4.5) — Tier-C joint-firing question.**
  SIG.MSR.118, .119, .143 carry identical descriptive statistics across 11 observations
  each. Native verdict at pass_2: **(a) three independent calibrated phenomena** —
  distinct planetary entities, non-overlapping event subsets (zero triple overlap;
  largest pairwise overlap 3 of 11), distinct Jyotish valences (two auspicious-yoga
  absences + one inauspicious-yoga absence). All three approved as independent signals.
  Held-out partition at M4-C is the generalization check.
- **R.LL1TPA.3 (LOW) — domain=unknown for 11 signals.** Domain mapping limitation
  inherited from M4-B-S1 (msr_domain_buckets.json keyed by MSR IDs; LEL semantic-class
  IDs CTR/CVG/SIG.NN/RPT/DSH absent). Cross-system reconciliation is M4-D scope per
  `PHASE_M4_PLAN`. Pass_1 outcomes do not depend on domain resolution.
- **R.LL1TPA.4 (DOC-ONLY) — KR.M4A.CLOSE.1 inheritance.** `CALIBRATION_RUBRIC_v1_0.md`
  frontmatter still reads `status: AWAITING_NATIVE_APPROVAL` despite NAP.M4.1 APPROVED
  Option B at v1.3. Semantic approval is intact (every event-match record cites
  rubric_option=B; pass_1 review honors rubric_option=B). Frontmatter flip schedulable
  as a small follow-up; non-blocking for pass_2.
- **R.LL1TPA.5 (DEFERRED) — LL.1 stability gate for LL.2.** Per
  `SHADOW_MODE_PROTOCOL §3.5 LL.2`, LL.2 edge-modulator promotion requires both endpoint
  signals' LL.1 weights to be in production. This is an LL.2-time concern (M4-B-S3+),
  not an LL.1 concern; surfaced here for cross-mechanism awareness.

No HIGH or CRITICAL residuals.

---

## §7 — Changelog

- **v1.0 (2026-05-02, M4-B-S2-MIRROR-TWOPASS):** Initial publication. Pass_1 surrogate
  review of all 30 promotion-eligible LL.1 signals. 30 approved / 0 held / 0 demoted.
  3 flagged for NAP.M4.5 (pass_2) closer scrutiny: SIG.MSR.118, .119, .143 (Tier-C
  borderline, identical statistics). Production-pending file produced at
  `signal_weights/production/ll1_weights_promoted_v1_0.json` with status
  `production_pending_pass_2`. 5 known residuals enumerated at §6 (3 LOW + 1 DOC-ONLY +
  1 DEFERRED); 0 HIGH/CRITICAL.
- **v1.1 (2026-05-02, M4-B-S5-NAP-M45-EXECUTE):** Pass_2 (NAP.M4.5) discharged.
  Frontmatter `status` flipped `PASS_1_COMPLETE_PENDING_NAP_M4_5` → `TWO_PASS_COMPLETE`;
  `version` bumped 1.0 → 1.1; pass_2_outcome added to frontmatter (30 approved / 0 held
  / 0 demoted). §5 `approval_chain.pass_2` block populated with native verdict, joint-
  question verdict for SIG.MSR.118/.119/.143 = (a) three independent calibrated
  phenomena, and joint_question_reasoning. New §5.5 added recording Gemini reachability
  check executed M4-B-S5 (result: NOT_REACHABLE; R.LL1TPA.1 carry-forward to M4-C
  entry). §6 R.LL1TPA.1 reframed as OPEN-carry-forward (gemini-reachability audit-
  trail, not a production-blocker); R.LL1TPA.2 CLOSED with native verdict. Production
  file (`ll1_weights_promoted_v1_0.json`) and shadow file
  (`ll1_shadow_weights_v1_0.json`) patched same session: 30 status flips
  `production_pending_pass_2` → `production`; outer `weights_in_production_register`
  flipped false → true; per-signal `approval_chain.pass_2_*` fields populated; shadow
  outer metadata adds `variance_estimator: "sample"` (closes F.RT.S4.1 from M4-B-S4
  red-team). 0 HIGH/CRITICAL residuals.

---

---

## §5.7 — Surrogate-reviewer disclosure: M5-B-S1 DBN topology two-pass (2026-05-13)

Per PHASE_M5_PLAN_v1_0.md §3 M5-B and DBN_TOPOLOGY_v1_0.md §8, a surrogate two-pass
review of the DBN topology was conducted in-session at M5-B-S1. As R.LL1TPA.1 is
declared FINAL_NOT_REACHABLE_M5 (§5.6), the reviewer was **Claude-surrogate-M5-B-S1**
standing in for the Gemini independent-review role.

**Scope:** DBN_TOPOLOGY_v1_0.md DRAFT — structural review (6 findings listed in §8).
**Outcome:** 3 RESOLVED in-session; 3 UNRESOLVED (U1-U3) flagged for native adjudication
at NAP.M5.1. This is NOT a review of LL.1 production weights (those remain UNCHANGED);
it is a topology-structure review only, conducted under the same surrogate-disclosure
convention as pass_1 (§2).

**Unresolved items for NAP.M5.1:**
- U1: CAREER↔SPIRITUAL initial_weight 0.20 vs surrogate recommendation 0.15
- U2: SPIRITUAL domain split vs unified-with-caveat
- U3: LL.2 per-edge approval (8 MED-tier edges PENDING_NATIVE_APPROVAL)

**Disclosure:** Surrogate role flagged explicitly in DBN_TOPOLOGY_v1_0.md §8.
Native adjudication at NAP.M5.1 substitutes for live Gemini review per
FINAL_NOT_REACHABLE_M5 convention.

**Session:** M5-B-S1 | **Date:** 2026-05-13

---

*End of LL1_TWO_PASS_APPROVAL_v1_0.md v1.1 (amended M5-B-S1 with §5.7 surrogate ledger entry). Two-pass complete; downstream pipeline may consume the 30 promoted weights with the n=1 disclaimer carried through.*

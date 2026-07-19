---
artifact: BIND_D-4_PREWORK_DRAFT
type: D-4 BINDER PRE-WORK — NOT a wave open, NOT a BOUND stamp
status: DRAFT — pre-work only, per native's explicit "allowed; NOT the wave open" instruction
authored_by: D-3 conductor session, pre-D-4 wrap-up pass, 2026-07-18
governing: BRIEF_D4.md + CONDUCTOR_PROTOCOL.md §2 step 1 (OPEN) — this document does the
  "fresh-verify every §B binding live" legwork ahead of time; it does NOT stamp the brief BOUND
  and does NOT authorize lane spawn. That remains D-4's own open, gated on native's go.
---

# BIND_D-4 pre-work — fresh live verification of BRIEF_D4 §B slots

## §B slot 1 — Matcher root-cause hypothesis (C-1)

**Not independently re-derived this pass** (native's directive scoped this session to "no D-4
lane code, no bakeoff scoring runs" — a C-1 diagnosis spike is lane-adjacent work, deferred to
D-4's own Binder). What this pass DOES contribute directly to C-1's future binding: `REPORT_D-3.md`
+ the §G per-event scoring artifact (`score_g.py`/`result_g.json`, retained in this session's
scratchpad, should be copied into the campaign's permanent artifact store before D-4 opens — see
Final Report §D1) — this is real evidence of how the CURRENT event-matching (bare-point,
distance-to-peak) performs, directly relevant to C-1's "shared LEL↔candidate matcher fix"
diagnosis.

## §B slot 2 — Evidence-set taxonomy per event class

**Partially advanced by this pass**: the LEL HEAD's actual event classes were enumerated live
during the §G gate run and the questionnaire-building pass (6 categories observed on real data:
`health`, `psychological`, `spiritual`, `education`, `finance`, `career`, `relationship`, `loss`,
`residential+travel` — 9 distinct top-level categories with more granular `domain` sub-tags per
`life_events.domain`, e.g. `health/chronic_onset` vs `health/chronic_resolution`). This is real,
already-enumerated data D-4's Binder can consume directly rather than re-deriving — not a
substitute for C-1/C-3's actual evidence-set-taxonomy design work.

## §B slot 3 — Curve-shape parameters ← D-3's shipped kernel

**Directly informed by this pass.** D-3's §G run produced real intensity-distribution data: both
named-mechanism curves (8L-Mars→2H loss, Venus+Jupiter windfall) showed genuine non-degenerate
variance (0.163/0.294) and a top-decile-day-fraction of 10.1% on both — these are real,
already-measured curve-shape parameters from the ACTUAL shipped kernel (post-FIX-PSEL,
post-PERF-TRIGGER-CACHE), not the obsolete cycle-1 proxy. D-4's Binder should pull these directly
from `REPORT_D-3.md`/`STATE_D-3.md`'s `cycle2_gate_G_FINAL_RESULT` block rather than re-measuring.

## §B slot 4 — Promotion-gate + kill-switch release thresholds

**NOT advanced this pass** — explicitly flagged in BRIEF_D4 as "Adjudicator-doctrine (DR-n;
epistemics, not engineering)" — this is D-4's own Binder's job at its own open, not pre-work
territory. No action taken, correctly out of scope for this pass.

## §B slot 5 — Rollback pin + all prior batteries green

**Fresh-verified live, this pass** (D4 of this checklist, see Final Report): live deploy SHAs
confirmed (`amjis-web`/`amjis-sidecar`/`brahma-build-pipeline-job` @ `04d5d0ce…` post
PERF-TRIGGER-CACHE, `amjis-mcp` @ `11377530…` unchanged all cycle), worktrees/branches swept
clean (2 stranded remote branches found and deleted this pass — `wave/D-3/FIX-PSEL`,
`wave/D-3/PERF-TRIGGER-CACHE`). **NOT all prior batteries green** — D-3's own §G gate is RED,
which is exactly why D-4 has not opened; DR-12's bakeoff (§ below) inherits this as load-bearing
input rather than requiring it resolved green first.

## DR-12's bakeoff — what D-4's C-1 inherits from this pass

Per `DR-12`/`DIS.025` ("D-4 battery MUST score midpoint-triangle vs pratyantar-lord vs
transit-kernel against LEL corpus; data retires the loser"), D-4's C-1 matcher work inherits, as
of this pass:
1. The §G RED result + full per-event scoring table (transit-kernel's real performance: 7/40 hit
   rate, -16.1pp control gap) as the transit-kernel arm's baseline data point.
2. `DR_13_EVENT_SCORING_SEMANTICS_DRAFT.md` — the event-shape-aware matcher spec C-1 should
   implement AGAINST, pending native ratification at D-4's actual bind.
3. `LEL_SCHEMA_V2_PROPOSAL.md` — the additive schema C-1's matcher needs to read `shape`/
   `date_confidence`/interval bounds from, once DR-13 is ratified and the migration lands.
4. The three competing peak models DR-12 names (midpoint-triangle, pratyantar-lord,
   transit-kernel) — only the transit-kernel arm has real §G data yet; the other two need their
   own retrodiction runs at D-4 open, using the SAME per-event scoring script/methodology for a
   fair bakeoff (reuse `score_g.py`'s scoring primitives, don't reimplement).

## C-2's one-shot backfill discipline — restated, unchanged

"Never run on an unverified matcher" — C-1 must land and be independently verified BEFORE C-2's
one-time backfill (`mimamsa_outcome_record` batch write) runs, per BRIEF_D4's own declared merge
order (`C-1 → C-3/C-4 → C-2 → C-5/C-6`). This pass does not touch or advance C-2's implementation
— it is listed here only to confirm the discipline is understood and unchanged by anything in
this wrap-up pass.

## E2 — C-2 firewall re-scope language, checked against the questionnaire flow

**Confirmed consistent, no contradiction found.** C-2's firewall: "quarantine LEL →
prediction-INPUTS only; LEL → outcome-SCORING flows freely." The date-tightening questionnaire
(`NATIVE_DATE_TIGHTENING_QUESTIONNAIRE.md`) asks the native to supply TIGHTER GROUND-TRUTH DATES
for existing LEL rows — this is LEL **data entry/correction**, not LEL flowing into a prediction
input. A tightened date updates what the LEL record SAYS happened and when; it does not feed a
forward-looking prediction. The firewall's INPUT-side quarantine is about preventing a chart
reading from being biased by "I already know X happened" — tightening a date on an already-past,
already-recorded event doesn't touch that boundary at all. **No firewall violation, no language
change needed.**

**Sealed test-split handling for tightened events — explicitly stated, not previously documented
elsewhere**: tightening a date does NOT change which split an event belongs to. An event dated
`>= 2020-01-01` (post-tightening or as originally recorded) remains in the sealed test split,
subject to the same ESCALATION_POLICY §4 restriction (only the gate runner and anti-gaming
verifier may read it) regardless of whether its date was ever tightened. The questionnaire's own
firewall (native pins dates blind, zero model/curve information shown) means the tightening
PROCESS itself cannot leak sealed-split information back to a build/admission agent — the native
supplies dates directly, no agent brokers that exchange. This is now the explicit, documented
handling D-4's C-1/C-2 should assume.

---
*This is pre-work, not a bind. D-4's actual Binder pass (Fable, at D-4's own open) must still
fresh-verify every slot above against live state at that time — nothing here should be trusted as
a cached substitute for D-4's own BIND_D-4.md when D-4 actually opens.*

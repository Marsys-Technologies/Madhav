---
artifact: PARIKSHAKA_W2_ACCEPTANCE_CHECKLIST (Track T2 gate-chain pre-staging)
canonical_id: PARIKSHAKA_W2_ACCEPTANCE_CHECKLIST
version: 1.0
status: PRE-STAGED — not yet walked; walk this checklist ONLY after real production
  data exists for both charts (post SWEEPS-COMPLETE → field build → hash-replay →
  weights-v0 pin → skill score + GOF publish → gate-close deploy).
created: 2026-08-05
author: Track T2 builder (ṢAḌ-DARŚANA overnight campaign, gate-chain pre-staging lane)
governing: SHAD_DARSHANA_BRIEF_v2_0.md §3 "Gate W2" (verbatim source of every item below)
  + SHAD_DARSHANA_NIGHT_RUN_v1_0.md §A (PARĪKṢAKA role charter, four-disposition vocabulary)
chart_ids:
  - 482012f1-710e-4a25-994a-93821f5871aa   # Abhisek Mohanty (native, primary canonical)
  - 1c826d5a-41cb-4450-b4dc-59d440e5f75a   # Abhinandan Mohanty (secondary canonical)
---

# PARĪKṢAKA — Gate W2 live acceptance checklist

**How to use this file.** PARĪKṢAKA (Opus, never writes code) walks each item below against
LIVE production, on **BOTH** canonical charts, after the gate-close deploy. Per
`SHAD_DARSHANA_NIGHT_RUN_v1_0.md` §A: four dispositions only — `VERIFIED-FIXED` /
`VERIFIED-NO-DEFECT` / `PARKED-HONEST` / `FAILED-REOPENED` — no "passed with caveats", ever.
An item without a PARĪKṢAKA disposition **does not exist**. Fill in the `Evidence` and
`Disposition` cells in place; do not delete or renumber items (append-only correction
discipline per the ledger's own convention).

Every clause below is copied **verbatim** from `SHAD_DARSHANA_BRIEF_v2_0.md` §3 "Gate W2"
(lines 364–373 as of brief v2.0) — this checklist adds structure (item numbering, per-chart
columns, evidence/disposition fields), it does not add, remove, or reinterpret a single
acceptance clause.

---

## Gate W2 preconditions this checklist assumes (do not walk the checklist before these hold)

- [ ] SESSION-A-SWEEP's ledger shows `SWEEPS-COMPLETE` (both charts, 606/606 substeps each).
- [ ] `ka_gochara_resonance` re-run for both charts against the completed sweep.
- [ ] `ka_kshetra` (stages 0–8) built successfully on both canonical charts.
- [ ] `mi_bhara` (stage 9 — weight fit, skill score, GOF, weights version write) run
      successfully on both canonical charts.
- [ ] The gate-close PR (`shad-darshana/integration` → `main`) has merged (merge queue,
      §B.2a — 5–60 min is normal, not stuck) and production traffic tracks the new revision.

---

## W2.1 — Field deterministic (hash-replay)

**Brief text:** *"field deterministic (hash-replay)"*

| # | Check | 482012f1 evidence | 1c826d5a evidence | Disposition |
|---|---|---|---|---|
| W2.1.a | A second `ka_kshetra` build on the SAME inputs (same sweep generation, same weights version) produces a byte-identical `field_snapshot_id` hash to the first build. | | | |
| W2.1.b | The hash-replay comparison is a REAL byte/hash comparison (§N.8 — "the PB-2 byte-equality gate" trap: a claimed byte-identity check with no actual comparison behind it is not evidence), not a self-report from the build log. | | | |

## W2.2 — LEL-invariance test green

**Brief text:** *"LEL-invariance test green"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.2.a | The Circularity Guard LEL-mutation-invariance CI test (seeded at W1 with item 10, per Elev §7) is green on the branch that produced the gate-close deploy. | | |
| W2.2.b | The test's own assertion is inspected directly (not just its green checkmark) — it must assert that `kala_field`'s hash is unchanged when the LEL is mutated, i.e. stages 0–8 genuinely never read the LEL (the Circularity Guard's static half, `services/mi_bhara/db.py` as the ONLY LEL-reading module, is also spot-checked here). | | |

## W2.3 — Skill score + GOF report published, both charts, regression-gated

**Brief text:** *"skill score + GOF report published for both charts and regression-gated (the
first published score becomes the CI baseline; thereafter 'regressed' means below the best
released value without a classified reason)"*

| # | Check | 482012f1 evidence | 1c826d5a evidence | Disposition |
|---|---|---|---|---|
| W2.3.a | A skill score (chart-level, event-weighted per `services/mi_bhara/skill.py::aggregate_chart_skill`) is published for the chart, with its bootstrap CI and honest `skill_state` (`established` / `not_established` / `underpowered`). | | | |
| W2.3.b | A GOF report (`services/mi_bhara/gof.py::compute_gof`, KS + Ljung–Box) is published for the chart, with honest `gof_state` (`pass` / `fail` / `underpowered`) and, if `fail`, a named `failing_statistic`. | | | |
| W2.3.c | This is confirmed to be the FIRST published score for each chart (`kala_field_skill`/`kala_field_gof` tables previously empty) — if so, it is recorded as the CI regression baseline, per the brief's own rule; this does not require a PASS/FAIL judgment on the score's sign, only that it published and was recorded as baseline. | | | |
| W2.3.d | If NOT the first publish (a prior baseline already exists), the new score is checked against `has_regressed()` (`SKILL_REGRESSION_TOLERANCE_NATS = 0.05`) — any regression carries a classified reason, never silently accepted. | | | |

## W2.4 — The LEL-absent scenario, verified (not just designed)

**Brief text:** *"the LEL-absent scenario verified: a chart with no LEL serves structural-prior
weights, `no_lived_history_recorded` STORY flags, and an honest calibration_maturity of zero —
the D6 three-scenario contract gated, not just designed"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.4.a | Identify (or synthesize, read-only) a chart/scope with zero LEL events and confirm it serves `weight_value == prior_value` (i.e. `n_eff = 0` for every weight, per migration 491's `v0_classical` contract) rather than crashing or silently defaulting to something else. | | |
| W2.4.b | The STORY view serves a `no_lived_history_recorded` flag for that scope — not a silently empty or misleadingly "clean" narrative (this is the same failure shape S4-05 exists to prevent, one layer up — see the S4-05 re-test artifact in this directory's sibling files). | | |
| W2.4.c | `calibration_maturity` reads honestly zero for that scope, not omitted or defaulted to a non-zero placeholder. | | |

**Note for the Conductor/Verifier:** as of this pre-staging pass, BOTH canonical charts have
real LEL history (the native's own — 57+ events per `NEXT-ACTION`/ledger references), so W2.4
may need a third, non-canonical scope (or a deliberately LEL-stripped fixture chart) to exercise
honestly — flag this as a scoping question if no zero-LEL chart is available at acceptance time,
rather than silently skipping the check.

## W2.5 — Cohort base rates served

**Brief text:** *"cohort base rates served"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.5.a | The rarity axis (item 15) / salience stage (stage 6) surfaces a real cohort base rate (from `bg_cohort`'s ~10⁴⁺ synthetic reference cohort) for at least one served insight, on each chart. | | |

## W2.6 — Null exceedance on every window

**Brief text:** *"null exceedance on every window"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.6.a | Every served `kala_field_windows` row (or the served window surface it maps to) carries a null-exceedance figure derived from the circular-shift null (item 23) — not a subset, "every window" is a completeness claim and is checked as one (row-count parity, not a sample). | | |

## W2.7 — Salience vector visible in PRIORITIZE

**Brief text:** *"salience vector visible in PRIORITIZE"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.7.a | `kala_priority_get` (PRIORITIZE) serves the stage-6 salience vector (submodular-selected) as a visible field in its response, on both charts, for at least one real query. | | |

## W2.8 — Insight rows lead readings

**Brief text:** *"insight rows lead readings"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.8.a | The stage-6.5 insight-synthesis rows (the 8-type catalog, `kala_insights` table) appear FIRST in at least one composed reading (the "reading-leads-with-insight" rule enforced in `argument_composer.ts`) — checked by inspecting a real composed response's ordering, not by trusting the composer's own claim. | | |

## W2.9 — Timeline spec renders valid

**Brief text:** *"timeline spec renders valid"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.9.a | `kala_timeline_spec v1` (item 27) validates against its own golden-render test on real served data for both charts (the "FULL spec surface" per rail 5, not a subset). | | |

## W2.10 — Specificity gate HARD-green

**Brief text:** *"specificity gate HARD-green"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.10.a | The specificity gate (E3) is confirmed flipped from its W0 skeleton (canonical + 4-chart proxy cohort) to HARD mode (real cohort charts, per D2) in the branch/deploy under acceptance. | | |
| W2.10.b | The specificity gate battery is green against real production prose on both canonical charts — not just the proxy cohort. | | |

## W2.11 — Legacy writers untouched and still serving

**Brief text:** *"legacy writers UNTOUCHED and still serving"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.11.a | `ka_gochara_sweep`'s legacy output (the pre-item-9 three classes: `career_advancement`, `major_gain`, `marriage`) is confirmed byte-unchanged in `kala_gochara_windows` for pre-existing rows (the strangler-fig proof — item 9 EXTENDS, never mutates). | | |
| W2.11.b | Every legacy tool/writer this campaign strangles-beside (not yet retired — retirement is W6's job) is confirmed still live and serving, on both charts. | | |

## W2.12 — Item 44 (authority-basis), reported not gated here

**Brief text (§1 item 44):** *"Reported at W2 (scoreboard in the ledger), gated at W6 — a W2
shortfall is a tracked number, not a wave blocker."*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W2.12.a | The authority-basis census scoreboard is populated with real numbers (paths enumerated / carrying `authority_basis` / computing own windows) in the ledger at gate-close — a shortfall here is recorded, NOT treated as a W2 blocker (only W6 hard-gates it at 100%). | | |

---

## Overall Gate W2 disposition

| Chart | All W2.1–W2.11 items VERIFIED-FIXED or VERIFIED-NO-DEFECT? | Any FAILED-REOPENED? | Gate W2 disposition for this chart |
|---|---|---|---|
| 482012f1 | | | |
| 1c826d5a | | | |

**Gate W2 closes only when BOTH charts show no `FAILED-REOPENED` row above and every item
carries a real disposition (no blanks).** A parked item is legal only as `PARKED-HONEST` with
a named reason and release condition — never a silent omission.

---
artifact: EVALUATION_PROTOCOL
canonical_id: EVALUATION_PROTOCOL
version: "2.3"
status: PRE_DECLARED — amendment implementing D-PROTO_DECISION_v1_0 (ACCEPT_WITH_CONDITIONS); B4.6 marks ACCEPTED only after the steward's condition checks pass
date: 2026-09-30
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
supersedes: "EVALUATION_PROTOCOL_v2_2.md (sha256 1803cfe3…; retained as history — a decided file is never edited)"
registry: "measurement/event_registry_v2_3.json (machine-readable; the scorer's actual input) + measurement/EVENT_REGISTRY_v2_3.md (review copy of the same rows)"
decision: "decisions/D-PROTO_DECISION_v1_0.md (Fable 5.1 as the native's delegate, 2026-09-30): ACCEPT_WITH_CONDITIONS on v2.2 — this v2.3 lands its §6 conditions 1–5 exactly as written, together"
declared_before: "the v2.2 re-run of '3.0' and any '4.1'/'5.0' scoring"
amendment_disclosure: >
  v2.3 is the condition amendment named by D-PROTO_DECISION_v1_0 §6: conditions 1–5 landed
  together, each with its "Verify" line satisfied — the evidence is in §11 of this file and in
  rerun_result_v2_3.json. The v2.3 re-run of '3.0' moved NO figure (T-cover 32/47 with the
  same 15 misses; T-time 182 d with uncapped 686/998/333; T-rank VOID 0/32; adverse T-FP
  figures unchanged; controls 638/940, all 940 draws byte-identical to v1_2). D-PROTO is
  decided at ACCEPT_WITH_CONDITIONS; whether the conditions are satisfied is the steward's
  check (B4.6), not mine. No '4.1'/'5.0' scoring has occurred. D-PROTO gates scoring only,
  not J1 (native, 2026-09-30).
  v2.2's disclosure, retained: written after the round-3 Codex review
  (ASTRA_REVIEW_DESIGN_SPECS_v1_2.md, REWORK / REWORK) was read in full, implementing its
  protocol-side findings (D-PROTO amendments 1–5 and R3-P01; reconciliation:
  design/RECONCILIATION_DESIGN_SPECS_v1_2.md §2/§6).
deviation_history: >
  Retained in full: B4.3 scored '3.0' before the B4.2 protocol review closed (disclosed in
  BASELINE_3_0_v1_0.md and v1.1's header). The '3.0' measurement stands as a measurement taken
  under an unreviewed protocol; v2.3 re-runs it under this protocol from the same pinned
  extract (sha256 70ba6142…, now MEASURED at load — condition 4) used by v2.0/v2.1/v2.2.
---

# Gochara evaluation protocol v2.3 — consolidated (D-PROTO condition amendment)

Changes v2.2 → v2.3 (D-PROTO_DECISION_v1_0 §6 conditions 1–5; everything below is the full
protocol; this list is the delta map): §6.4 enforces the gain-class 0.5–40 % band (C1);
§4.6/§6.3 freeze candidate-set membership to the span-years-clipped set (C2); §6.5 defines
T-honesty's consequences (C3); §9.1 requires the extract hash to be measured, not asserted,
and the class universe to be validated on input (C4); riding corrections: 731/730-day
interval spans, one tie-grouping predicate for plateau and ranking, dev-tier reporting
reworded, §10's held-out-meaning and B5.4-disclosure sentences, three registry
mapping_reason clauses (C5).
v2.1 → v2.2 changes, retained: the registry is machine-readable and the two multi-year
uncertainties are 2-year interval rows (M = 32, floor 17); the vertigo exacerbation is an
unscored annotation; the full 27-class polarity/adverse/eligibility table is here (§2); the
merge representative and ONE tie tolerance are in prose (§4); the sign-convention adapter is
corrected and enforced on RAW inputs with a machine-readable stop (§4.5, R3-P01); a
generation-wide rank void is enforced in code with a machine-readable status (§6.3, §8.1);
the random-control experiment is frozen ONE way with prose matching the code (§7, R2-M05);
the annotation guard is restated to its honest scope (§7); the source-reconciliation
invariant replaces "the table is infallible" (§9.2).

## 1. Event source

The only event source is **event_registry_v2_3.json** (built row-by-row from
LIFE_EVENT_LOG_v1_2.md, read-only; review copy EVENT_REGISTRY_v2_3.md). No event enters
scoring except through the registry; any registry change after a scoring pass is a versioned
amendment naming what was seen. Registry facts this protocol relies on: held-out **47 (32
timing-usable + 15 year-grain)**; dev 3 (calibration only); excluded 7 (EVT.CURRENT.01 inside
the 7, counted once); annotation 1 (unscored); observation mask ends **2026-04-17**; scored
horizon H = 1998-01-01 → 2026-04-17 = **10,334 days**.

Onset vs status vs exacerbation: only `point`/`interval` rows are scored. `status` rows
(EVT.CURRENT.01) and `exacerbation` rows (the vertigo exam-prep peak) are annotations, never
dated events. Date-uncertainty rows carry the grain the LEL supports and no finer — including
**two-year intervals** where the LEL says "2007 or 2008" / "2021 or 2022" (never flattened to
a single year). Class mappings with reasons live in the registry; proxy mappings (a row whose
dated point stands for a different mechanism, e.g. Tepper sponsorship → education_milestone)
carry that qualification explicitly in `mapping_reason`.

## 2. Class universe — full 27-class table (R2-M06)

Polarity, adverse-set membership, and endpoint eligibility are fixed here — part of the class
universe, not of any scorer. "Rank-eligible" means eligible *subject to* the §8 degeneracy
exclusions; birth_anchor is the natal epoch and enters no endpoint.

| class | polarity | adverse (frozen set) | T-cover | T-time/T-rank | T-FP |
|---|---|---|---|---|---|
| achievement_recognition | gain | no | yes | rank-eligible | no |
| bereavement | adverse | **yes** | yes | rank-eligible | yes |
| birth_anchor | anchor | no | **no** | **no** | **no** |
| business_launch | gain | no | yes | rank-eligible | no |
| career_advancement | gain | no | yes | rank-eligible | no |
| career_change | gain | no | yes | rank-eligible | no |
| career_entry | gain | no | yes | rank-eligible | no |
| career_setback | adverse | **yes** | yes | rank-eligible | yes |
| childbirth | gain | no | yes | rank-eligible | no |
| chronic_onset | adverse | **yes** | yes | rank-eligible | yes |
| education_milestone | gain | no | yes | rank-eligible | no |
| exam_outcome | gain | no | yes | rank-eligible | no |
| financial_deception | adverse | **yes** | yes | rank-eligible | yes |
| foreign_settlement | gain | no | yes | rank-eligible | no |
| illness_acute | adverse | **yes** | yes | rank-eligible | yes |
| major_gain | gain | no | yes | rank-eligible | no |
| major_loss | adverse | **yes** | yes | rank-eligible | yes |
| marriage | gain | no | yes | rank-eligible | no |
| parental_event | adverse | **yes** | yes | rank-eligible | yes |
| property_acquisition | gain | no | yes | rank-eligible | no |
| psychological_arc | non-adverse (scored with gain-side conventions) | no | yes | rank-eligible | no |
| relocation | gain | no | yes | rank-eligible | no |
| romantic_start | gain | no | yes | rank-eligible | no |
| separation | adverse | **yes** | yes | rank-eligible | yes |
| spiritual_turn | non-adverse (scored with gain-side conventions) | no | yes | rank-eligible | no |
| surgery | adverse | **yes** | yes | rank-eligible | yes |
| travel_event | gain | no | yes | rank-eligible | no |

The frozen adverse classes (T-FP): bereavement, career_setback, chronic_onset,
financial_deception, illness_acute, parental_event, separation, surgery, major_loss.

## 3. Timezone and calendar conventions

- All event dates are **IST calendar dates** as logged in the LEL.
- Window timestamps stored in UTC follow the platform's 18:30-UTC (= 00:00 IST) day-anchor
  convention; a stored timestamp `T` represents the IST civil date `T + 5:30`. All scoring
  converts to IST dates before any comparison.
- A generation whose coverage ends before 2026-04-17 is scored on the intersection and the
  shortfall is reported as coverage, never as absence of events.
- Interval endpoints are calendar-date inclusive on both ends; spans are counted in days
  inclusive (a [Y-01-01, Y+1-12-31] two-year interval is 730 or 731 days as the calendar
  gives — this registry: 2007–08 = **731 d** (2008 is a leap year), 2021–22 = 730 d).

## 4. Window identity, deduplication, ties

1. **Candidate identity:** a candidate window is the tuple (class, window_start, window_end,
   peak_date, generation) after conversion to IST dates.
2. **Dedup before counting:** overlapping or abutting windows of the same class within a
   generation are merged into one candidate **before** N (candidate count) is computed and
   before any ranking. A plateau of 40 contiguous daily rows is one candidate.
   **Merge representative (in prose, R2-M04):** the merged candidate carries the peak date and
   si of its highest-si member; **ties go to the earliest peak date**.
3. **Ranking:** candidates of class c in event e's year are ranked by **signed intensity,
   descending, for gain and adverse classes alike** (the si sign convention of §4.5).
   **Ties take the average rank** of the tied group. **ONE tie tolerance everywhere
   (R2-M04):** two si values are the same value iff `|si₁ − si₂| < 1e-9` — this tolerance is
   used identically by ranking tie-groups and by the §8.3 peak-diversity check.
4. **Eligible misses stay in the ranking:** if no admitted window of class c overlaps e's
   scored span, e is retained in the T-rank median at the **worst-rank convention —
   percentile 100** (the asymmetry is stated: real ranks land on 100(r−1)/N ≤ 100(N−1)/N,
   so a miss at 100 is strictly worse than any real rank; Kimi NK-9). Misses are also counted
   separately for T-cover; the two reports never silently drop the same event. Saved
   per-event records carry both the percentile and the event's eligibility/void status
   (R2-M03).
5. **Sign-convention adapter — enforced on RAW inputs (R3-P01, corrected claim):** raw
   extract rows carry `valence ∈ {gain, loss, mixed, neutral}` (the pinned extract contains
   all four: 270 gain / 330 loss / 134 mixed / 180 neutral — v2.1's "adverse rows carry
   valence `loss`" was **false** and is corrected: 70 parental_event rows are `mixed`, 10
   surgery rows `neutral`). The convention the scorer actually relies on is: **si is stored
   non-negative for every class**, and "most adverse first" / "most gainful first" are both
   si descending. The adapter runs on **raw rows before merging**: any raw row with si < 0 is
   a machine-readable rejection — the scorer writes `status: INPUT_REJECTED` with the
   offending rows to the result file and stops. A diagnostic print is not an assertion.

## 5. Timing error — single rule

One rule, no parallel formulations:

- **grain exact:** error = |peak IST date of the highest-ranked overlapping window − event
  date| in days; 0 if peak = event date.
- **grain month:** event date = 15th of the month (error proxy only — coverage is the whole
  month, §6.1); error in days on the same scale.
- **grain interval [a,b]:** hit iff an admitted window overlaps [a,b]; error = distance from
  peak to the nearest point of [a,b] (0 if peak ∈ [a,b]).
- **Miss:** no overlapping window → error = **182 days** (capped miss value).
- **All errors are capped at 182 days.** Alongside the capped median, the scorer reports
  separately: (a) the miss count, (b) the uncapped errors of the hits. The capped median is
  the endpoint; the separate reports are mandatory disclosure.

## 6. Endpoints (all co-primary, each necessary, none sufficient)

1. **T-cover:** of the 47 held-out events, the fraction with at least one admitted window of
   the event's class **overlapping the event's scored span** (exact: the day; month: the
   calendar month — any shared day; interval: the interval; year: the year) must be
   **≥ 32/47** — the v2.1/v2.2/v2.3 re-run figure of '3.0' on this registry
   (BASELINE_3_0_v2_3.md; the bar equals the served floor), and every miss must be named.
   The §4.6 candidate set is used identically for hits, for ranking, and for N.
2. **T-time (single rule):** capped-median timing error over the 5 exact-date held-out events
   (registry §2, exact cohort) **≤ 45 days**. Misses enter at 182 d per §5.
3. **T-rank:** over timing-usable held-out events whose class is **not degenerate for the
   event's scored-span years** (§8 exclusions run first), with **N ≥ 3 candidate windows**
   in the §4.6 candidate set (post-dedup; interval events: the span-years-clipped set),
   median rank percentile ≤ **25**. **Validity floor:** at least **floor(32/2)+1 = 17** of
   the 32 timing-usable events must be eligible, else the generation is **rank-unproven**,
   which **blocks the flip** regardless of other endpoints. Worst-rank misses stay in the
   median per §4.4. Aggregation: event-pooled (one median over eligible events), stated.
   **Machine-readable void (R2-M03):** when a §8 degeneracy test voids the rank block, the
   result file carries `t_rank.status: "VOID"` with the tripped test named and **no rank
   median is emitted as a result** (a median computed for diagnostics is labelled
   `diagnostic_only: true` and can never satisfy the endpoint).
4. **T-FP (single estimand, Codex R2-M02):** for each frozen adverse class c, the **admitted
   day-fraction** (union of admitted days of class c inside the horizon) ÷ H must be
   ≤ **min(1, 3·n_c·90/H)**, n_c = held-out in-horizon events of class c, H = 10,334 — the
   same denominator on both sides. Arithmetic (registry §5): n_c = 1 → 270/10,334 =
   **2.61 %**; n_c = 2 → **5.23 %**; n_c = 0 (major_loss) → single-event allowance
   **2.61 %**. **Policy statement:** the ±45-day legitimate footprint, the factor-3 slack,
   the 90-day window, and the n_c = 0 allowance are **declared engineering allowances**
   (evaluation policy chosen so a blanket-claim class fails by construction), not quantities
   derived from event density. **Gain-side enforcement (C1):** T-FP additionally FAILS if any
   non-adverse class other than `birth_anchor` that has scored rows sits outside
   **0.5 % ≤ base rate ≤ 40 %** of scored-horizon days — the band is a pass/fail criterion
   enforced in code (each such class carries `burden_pct` and `pass` in the result file's
   `t_fp_gain` block), not a printed tally; the generation-level T-FP verdict requires every
   adverse AND every gain entry to pass. Classes with no rows remain `absent` (§9.5) and are
   handled by T-honesty, not by this band. Rationale (D-PROTO F1): without enforcement, an
   over-broad gain-side candidate passes every other endpoint — with the band enforced, a
   blanket gain coverage is capped at 40 % and the 32/47 T-cover bar again implies real
   signal.
5. **T-honesty:** every metric carries its coverage; a class with coverage < 50 % of the
   scored horizon is reported `unqualified`, not scored. **Coverage must be verifiable from
   a computation-coverage manifest naming which (class, year) cells the engine computed;
   without that manifest T-honesty is UNVERIFIABLE** (Codex R2-M06) — the manifest is a
   **build requirement** for any future generation scored under this protocol, and '3.0' is
   reported with it absent. **Consequences (C3, D-PROTO F4):** (a) held-out events are never
   removed from any denominator by their class's coverage status — an event in an
   `unqualified` class scores as a T-cover miss and T-rank percentile 100 unless an admitted
   window overlaps it; (b) `t_honesty.status = UNVERIFIABLE` on a candidate generation means
   the candidate is **not flip-eligible**, equivalent to failing a co-primary endpoint (the
   result file carries `t_honesty.pass: false` whenever the status is not PASS); (c) the
   coverage fraction is defined per class as **(class, year) cells computed ÷ (class, year)
   cells in the horizon**.

Failure on any co-primary endpoint is failure of the generation. D-FLIP additionally requires
the A5.7 engineering gates.

## 7. Controls

- **Negative days/years:** per class, every horizon day/year with no registry event of that
  class (LEL completeness disclosed as a limit).
- **Random controls — ONE frozen experiment (R2-M05; prose matches the code exactly):**
  **20 intervals per held-out event**, each a **rolling span of the event's own actual span
  length in days** as the calendar gives it (exact: 1 d; month events: the actual calendar
  month, 28–31 d; year events: the actual calendar year, 365 or 366 d; interval events: the
  interval's own length — grandfather 61 d, 2026.01 59 d, 2007–08 and 2021–22 two-year rows
  730 d). **Units:** days (no calendar-unit matching; the calendar-unit alternative is
  rejected — frozen). **Sampling domain:** start offset drawn as `randrange(0, H − span + 1)`
  — the inclusive integer range [0, H − span], final valid start included. **Overlap
  semantics:** any shared calendar day. **Weighting:** unweighted — every control interval
  counts once. **Seed = 482012**, **materialised**: the draw is committed beside the score
  file (v2.2 materialisation: random_controls_v1_3.json) so the controls are reproducible
  byte-for-byte. (v2.1's prose said "month: 30 d; year: 365 d" while the code drew actual
  month/year lengths — the code is the frozen experiment; the prose error is corrected, not
  the code.)
- **Placebo classes:** classes with zero registry events (e.g. major_loss) — scored against
  the single-event allowance, §6.4.
- **Annotation guard — honest scope (R2-M06, R3-P01):** THIS historical pinned re-run is
  restricted to **annotation-free inputs**: the registry JSON contains no annotation payloads
  beyond LEL-anchored fields, and the scorer accepts no other annotation channel. The broader
  claim (a general machine guard rejecting unverified annotations in arbitrary inputs) is
  **withdrawn** — it is a build-contract item for the future engine, not a property of this
  scorer. Only annotations verified in
  `measurement/LEL_CHART_STATE_RECONCILED_v1_0.md` may annotate a score file at all.

## 8. Degeneracy tests (run on every generation BEFORE any endpoint; exclusions feed T-rank)

1. **Era-boundary fingerprint:** ≥ 50 % of class pairs sharing identical window boundaries →
   generation flagged **class-indiscriminate**; T-rank is **VOID with the machine-readable
   status of §6.3** (not merely printed), flag recorded atop the score file and in the result
   JSON.
2. **Two-horns check:** class base rate > 95 % or < 0.5 % → class degenerate-high/-low; such
   classes count in T-cover and T-FP but never toward T-rank's N or floor. The tally is
   reported over **all 27 classes including birth_anchor**.
3. **Peak-diversity check:** if ≥ 50 % of a class's in-year windows share one si value (a
   plateau), T-rank for that class-year is void. Same-value grouping uses the §4.3
   tolerance: si values are sorted and cut into groups wherever the gap is ≥ 1e-9; the
   largest group's share is the plateau share — one grouping predicate for plateau and
   ranking alike (C5)
   (ties make rank arbitrary) and its events do not count toward the floor.

## 9. Procedure

1. Pin the scored rows to a file (read-only dump, sha256 recorded) before any counting.
   **Measured, not asserted (C4):** the scorer COMPUTES the extract's sha256 at load and
   rejects with `INPUT_REJECTED` on any mismatch with the declared pin; it likewise rejects
   with `INPUT_REJECTED` any extract class outside the §2 27-class table.
2. Compute registry-derived counts first. **Source-reconciliation invariant (R2-M01):** any
   mismatch with the registry's §6 table triggers a documented registry-vs-scorer diff
   reconciliation — each differing count is traced to its registry row and its scorer
   predicate, the side in error is fixed, and the diff is recorded in the baseline. Neither
   side is presumed correct by rule (v2.1's "the table is authoritative, any differing scorer
   has a bug" is replaced).
3. Score each generation once per protocol version, read-only, every figure with its
   predicate and the pinned extract's hash. The run emits a **machine-readable result file**
   (`rerun_result_v2_2.json`): per-endpoint status, the T-rank status field of §6.3, the
   input-adapter verdict of §4.5, and per-event records with eligibility/void status.
4. Dev-tier events are listed in the registry and excluded from every endpoint (they exist
   for calibration outside this protocol's scoring; no dev-tier figures appear in a result
   file).
5. Aggregation: **T-cover, T-time and T-rank are event-pooled; T-FP is per class** (stated
   once, here). Missing values are reported as missing (never silently zero-filled); a class
   with no scored rows is `absent`.
6. A protocol change after a scoring pass is a versioned amendment naming what was seen.

## 10. Honest limits (retained, restated for v2.2)

Single chart; 32 timing-usable held-out events (5 exact-date): medians, not distributions; no
significance claim beyond the pre-declared thresholds. **"Held-out" here means "not used for
calibration", not "unseen"** — the authors of the '5.0' rule paths have read the LEL (D-PROTO
F11a). The LEL is the native's curated recollection; negative years assume log completeness
for the major classes. **Mandatory non-gating B5.4 disclosures (D-PROTO F11b):**
per-mechanism attribution and per-path ablations (the sealed doctrine's Tier 3) are
diagnostics the B5.4 report must carry; they are not gates. '3.0''s windows
are known-collapsed; its re-run baseline is the honest floor, not a straw man. For '3.0'
specifically: every timing-usable event sits in a degenerate class, so T-rank has no eligible
events at all — rank-unproven is a statement about '3.0''s windows, not about the test.

## 11. Condition evidence (D-PROTO_DECISION_v1_0 §6 "Verify" lines)

1. **C1 (gain band enforced):** `rerun_result_v2_3.json.t_fp_gain` carries `burden_pct` and
   `pass` for all **17** non-adverse, non-anchor '3.0' classes — every one `false` (13 at
   99.8742 %, including psychological_arc; 4 at ≤ 0.12 %: business_launch, career_change,
   education_milestone, foreign_settlement); `t_fp_overall.pass = false` requires every
   adverse AND every gain entry; adverse figures unchanged; the band-label logic is fixed
   (no class can be labelled "low" above 40 %).
2. **C2 (candidate set frozen):** the v2.3 re-run reproduces every v2.2 '3.0' figure exactly
   (§0's amendment header). The F2 probe (synthetic lone chronic_onset window
   2008-03-01→2008-05-30 against the [2007-01-01, 2008-12-31] span) now returns hit=True,
   N=1 (v2.2: miss). The F3 probe (one in-mask 2026 window plus two wholly post-mask 2026
   windows for EVT.2026.01.XX.01) now returns N=1 (v2.2: N=3). Both probes run by Stream B;
   the steward reruns them in a scratch copy.
3. **C3 (T-honesty consequences):** §6.5 (a)/(b)/(c) above; `rerun_result_v2_3.json` shows
   `t_honesty.pass: false` for '3.0'.
4. **C4 (inputs measured):** `rerun_result_v2_3.json.extract_sha256` is a computed object
   `{declared_pin, measured, match: true}`. Mutation check: one byte flipped in a scratch
   copy of the extract ⇒ `INPUT_REJECTED: extract hash mismatch`, exit 1 (run by Stream B;
   steward re-runs). The scorer's class list equals §2's 27 rows and unknown-class input is
   `INPUT_REJECTED`.
5. **C5 (riding corrections):** "730 d" appears only for the 2021–22 row in this file, the
   registry and the baseline (2007–08 = 731 d); plateau grouping and ranking share one 1e-9
   predicate (§8.3); §9.4 reworded; §10 carries the held-out-meaning and B5.4-disclosure
   sentences; the three registry mapping_reason clauses are in event_registry_v2_3.json /
   EVENT_REGISTRY_v2_3.md (D-PROTO F10).

*End of protocol v2.3. The '3.0' v2.3 re-run follows in BASELINE_3_0_v2_3.md; B4.6 marks the
protocol ACCEPTED only after the steward's condition checks pass.*

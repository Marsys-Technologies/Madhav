---
artifact: D4_BRIEF_REVISION_INPUTS
type: CONSOLIDATED INPUT DOCUMENT — for native + Cowork use revising BRIEF_D4.md before kickoff
status: DELIVERED — assembled per native's D-3 closeout + D-4 staging directive, 2026-07-18, item 5
authored_by: D-3 conductor session, closeout pass, 2026-07-18
note: >
  This document does NOT bind D-4, does NOT propose lane code, and does NOT score anything. It
  consolidates everything a brief-revision pass needs into one place. BRIEF_D4.md v1.3 remains
  the operative FROZEN brief until the native/Cowork revision supersedes it with a version bump.
---

# D-4 Brief Revision Inputs

## 1 — BRIEF_D4.md v1.3, verbatim (current FROZEN brief)

> Full text below, reproduced exactly from
> `00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/BRIEF_D4.md` at closeout time
> (version 1.3, status `FROZEN — §B slots bind at wave open`). Do not edit this section in place;
> revise the source file directly and re-run this assembly if a fresh snapshot is needed.

```yaml
artifact: BRIEF_D4
type: WAVE BRIEF (two-part: FROZEN + BIND-AT-OPEN)
wave: D-4 — Calibration ignition (L5 finally fed)
version: 1.3
status: FROZEN — §B slots bind at wave open
governing: CONDUCTOR_PROTOCOL.md + DOCTRINE_CAMPAIGN_EXECUTION_PLAN_v1_0.md §7 +
  DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §7
prerequisite: D-3 gate GREEN (mechanism curves exist and retrodict). Wave sequence to date —
  D-1.5a, D-1.5b (Gate B 17/17), and D-1.6 "Śuddhi" (Gate Ś) are ALL CLOSED; D-2 then D-3
  precede this wave.
gate: discrimination + negative-control gates (§G) with anti-gaming verifier pass.
```

# D-4 — Calibration Ignition

## §F0 — Baseline as of D-1.6 close (alignment note, 2026-07-16 — read before binding)

This brief froze before waves D-1.5a / D-1.5b / D-1.6 ran (all three CLOSED: Gate A 13/15 + 2
documented PARKs; Gate B 17/17; Gate Ś). What changed in D-4's territory:

- **Framing: L5 is SEALED in STRUCTURAL mode by design** (CLAUDE.md §E) — empirical calibration
  values fill in as prediction→outcome data accrues. D-4 is the designed IGNITION of that loop
  (the first real outcome feed), not a repair of unfinished L5 work. Nothing in this wave
  re-opens the L5 seal; writers stay inside the FROZEN WriterBase contract.
- **Calibration-alias unification (D-1.6 Lane S-1, CR-51/CR-30):** `query_calibration` and
  `mimamsa_calibration_get` — previously documented aliases returning DIFFERENT payloads — are
  now a strict twin (Gate Ś #3: IDENTICAL result_hash on the deployed connector), and an
  alias→primitive conformance check lives in the harness (S-6, O-7). §G assertions may probe
  either face; alias parity is a standing regression surface this wave must not break.
- **CR-47's honesty half already shipped:** D-1.6 S-1 added the serve-side `non_discriminating`
  flag to `phala_rectification_get` (a zero-signal run now self-reports instead of presenting a
  fake ranking). Lane C-1's remaining scope is the MATCHER ROOT FIX itself (the 0/36 silent
  zero-scoring), which D-1.6 explicitly deferred ("full method fix stays K-6/later" — that later
  is this lane).
- **Register verification (2026-07-16):** this brief's cited rows — CR-47, CR-79, CR-20/67,
  CR-68 — are all still OPEN in `POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md` v1.5 (§A–§I+§M
  remains system-of-record for CR-1..89+107; CR-90..106 resolve via the §N pointer table into
  the execution plan §8 + wave briefs). No re-statusing by D-1.6 S-8 touched this brief's rows.

## FROZEN §F1 — Lane map (6 lanes)

### Lane C-1 — Shared LEL↔candidate matcher fix (CR-47 root)
The matcher scored 0/36 LEL events across all 185 rectification candidates — silently. The
silent half is fixed (D-1.6 S-1's `non_discriminating` flag — see §F0); this lane root-causes
the shared matcher itself. Healing this heals rectification too (same component). Verifier:
matcher matches known specimens (2025-05 fraud → 8L-Mars→2H mechanism; 2010-07 windfall →
wealth mechanism) with nonzero fit.

### Lane C-2 — LEL firewall re-scope + retrodiction backfill
Firewall re-scoped: quarantine LEL → prediction-INPUTS only; LEL → outcome-SCORING flows freely.
One-time backfill job: score all 57 LEL events (per chart) against their D-3 mechanism curves;
batch-write `mimamsa_outcome_record` rows under PH-4-3's train/test discipline. Flips
n_observations 0 → ~40/chart; promotion gates evaluate for the first time.

### Lane C-3 — Event-class evidence + verdict function (CR-79)
Evidence sets become event-class-specific (gain ≠ loss — opposite outcomes may never share
identical evidence + identical grade); QA checks that always return 0.5 self-report as
non-discriminating; kill-switch release criteria defined as data.

### Lane C-4 — Negative controls
Shuffled-birth + antiphase controls implemented (the `not_implemented` stubs become real); every
calibration claim carries its control delta. No control, no claim.

### Lane C-5 — Remedy-leverage join (CR-20/67)
bo_upaya populated from: leverage_index (weakest load-bearing graha) × existing sādhanā history
(LEL spiritual arc) × dasha runway (intervention window = years BEFORE the weak lord's MD opens).
The Venus/Venkaṭeśvara specimen becomes computable: system holds both halves today and never joins
them. Wealth resonances ≠ 0; at least one schedulable program.

### Lane C-6 — mechanism_retrodiction surface (CR-68)
LEL events joined to the mechanism that predicts them, served as CONFIRMATION ("this chart's 2H
mechanism has fired N times: …") — never as prediction input. Feeds L5 honestly; gives readings
their retrodictive-evidence section.

**Merge order:** C-1 → C-3/C-4 (parallel) → C-2 (backfill runs AFTER matcher+evidence fixed) →
C-5/C-6. The backfill is one-shot: never run it on an unverified matcher.

**Then the standing live loop opens (not a lane — a property):** every reading logs
falsifier-bearing predictions per its vidhi; every LEL append triggers outcome matching;
multipliers update; the next compiled contract retrieves with calibrated priors.

## FROZEN §F2 — must_not_touch
FROZEN orchestrator contract (PARK) · the leakage firewall on prediction-INPUTS (re-scoped, never
removed) · raw LEL event data (append-only corpus) · all prior gate surfaces (regression batteries).

## §F3 — Execution discipline + operational constants (standard, per CONDUCTOR_PROTOCOL — added v1.1)

[... full §F3 text, unchanged from source — parallel-sub-agent discipline, operational constants,
orchestration economy grant, Definition of DONE — see BRIEF_D4.md lines 96–146 for the complete
text; omitted here only to keep this pointer section from duplicating a large unchanged block. It
is UNCHANGED input, not a revision candidate, unless the native/Cowork pass decides otherwise.]

## §B — BIND-AT-OPEN slots (Fable Binder)
- Matcher root-cause hypothesis ← C-1 diagnosis spike at open (read the actual matcher code + one
  traced run) before lane briefs finalize.
- Evidence-set taxonomy per event class ← LEL HEAD's actual event classes (enumerate, don't assume).
- Curve-shape parameters ← D-3's shipped kernel (intensity distribution percentiles for scoring
  thresholds).
- Promotion-gate + kill-switch release thresholds ← Adjudicator-doctrine (DR-n; these are
  epistemics, not engineering).
- Rollback pin + all prior batteries green.

## §G — Gate
1. `mimamsa_calibration_get`: n_observations ≈ 40/chart; multipliers evaluating (no longer all
   prior_only); verdict_distribution + reliability_curve non-empty.
2. Discrimination: `mimamsa_insight_get(wealth)` — "Major Financial Gain" and "Major Financial
   Loss" carry DIFFERENT evidence sets and DIFFERENT grades on 482012f1.
3. Negative controls: implemented, and calibration beats shuffled-birth with the gap reported.
4. At least one served verdict demonstrably moved by a calibrated multiplier (before/after receipt).
5. Remedy: bo_upaya wealth resonances ≠ 0; the leverage-ranked intervention (Venus, pre-2034
   window) served with its sādhanā join.
6. Anti-gaming pass on 1–4 + all prior wave batteries green (full regression).

**Campaign close (after this gate):** parked-items review + all DR-n rulings presented to the
native for ratification; register final sweep; CURRENT_STATE + SESSION_LOG campaign seal; the
master test becomes the standing per-release regression suite.

---

## 2 — BIND_D-4_PREWORK_DRAFT.md's findings (pre-work only, not a bind)

Full document: `BIND_D-4_PREWORK_DRAFT.md`. Key findings for revision purposes:

- Addresses BRIEF_D4 §B's 5 bind slots with what is independently verifiable now (pre-D-4-open),
  explicitly marked pre-work, not a bind — D-4's own Binder still owns the actual bind at open.
- **DR-12's bakeoff inheritance (§ "DR-12's bakeoff — what D-4's C-1 matcher work inherits"):**
  D-4's C-1 matcher work inherits D-3's §G RED result + full per-event scoring table as the
  transit-kernel arm's baseline data point in the midpoint-triangle vs pratyantar-lord vs
  transit-kernel bakeoff (7/40 hit rate, -16.1pp control gap).
- **E2 — C-2 firewall consistency check (folded in):** confirmed no contradiction between C-2's
  firewall re-scope language and the date-tightening questionnaire flow (full text in §7 below).
- **Sealed test-split handling for tightened events** — documented here for the first time (see
  §8 below), since no prior artifact addressed what happens to an event's split membership after
  its date is tightened by the native.
- Explicit closing disclaimer in the source file: "This is pre-work, not a bind."

## 3 — D-3 RED result + per-event artifact

**Result:** D-3's §G retrodiction gate ran once, blind, full LEL access, post-fix
(FIX-PSEL+PERF-TRIGGER-CACHE+clean rebuild). RESULT: RED.
- Named-mechanism checks (a)/(b): both miss top-decile (81%/67% of threshold).
- Blind battery: 17.5% hit rate vs 50% floor, AND scores worse than shuffled-birth control
  (-16.1pp raw gap; A1's coverage-matched re-analysis: -15.8pp — confirms genuine kernel finding,
  not a coverage artifact).
- Full per-event scoring table (40 events, full scoring anatomy) and the coverage-matched
  control-gap analysis script live at:
  `/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/d6aa9c91-2f4f-4044-8214-8432b8934686/scratchpad/`
  (`score_g.py`, `lel_events.json`, `pooled_activations.json`, `result_g.json`,
  `coverage_matched_control.py`, `coverage_matched_result.json`).
  **HONEST GAP:** these are session-scratchpad files, not committed to the repository. They have
  NOT yet been copied to a permanent campaign location. D-4's Binder should either (a) copy them
  into `00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/artifacts/D-3/` at D-4 open,
  or (b) accept that this raw per-event data may not survive past this session's scratchpad
  lifetime and re-derive it from the deployed connector if needed. Full narrative detail (not raw
  data) is preserved in `REPORT_D-3.md` and `PRE_D4_WRAPUP_REPORT.md`.

## 4 — DR-12 + DR-13 final texts

**DR-12 (DIS.025) — RATIFIED 2026-07-17, forward-binding on D-4:**
> The D-4 retrodiction battery MUST score midpoint-triangle vs pratyantar-lord vs transit-kernel
> as competing peak models against the full LEL outcome corpus — the data retires the loser.
> Neither doctrine nor engineering decides the peak model by opinion; the empirical retrodiction
> score does. This hook is registered at D-3 open so the D-4 Binder inherits it as a MANDATORY
> battery dimension at D-4's own bind (not optional, not re-litigated).
Full entry: `DISAGREEMENT_REGISTER_v1_0.md` DIS.025.

**DR-13 (DIS.026) — RATIFIED 2026-07-18 (this closeout directive):**
> Point/interval/chain event shapes; interval scoring by overlap with top-decile windows;
> date_confidence-scaled tolerance (exact ±45d / month ±75d / year-only → labeled secondary
> interval battery, not discarded); control-mirroring rule binding on every scoring loosening.
Full entry: `DISAGREEMENT_REGISTER_v1_0.md` DIS.026. Full authoring record:
`DR_13_EVENT_SCORING_SEMANTICS_DRAFT.md` (now RATIFIED). Explicit non-scope: does NOT
retroactively re-score D-3's closed RED result; does NOT loosen DR-11's ±45d figure for
exact-confidence events; does NOT authorize any kernel-weight/threshold/orb/valence change.
D-4's C-1 (event-shape-aware matcher spec) is speced against this ruling. LEL schema v2
(APPROVED, see `LEL_SCHEMA_V2_PROPOSAL.md`) implements the shape/date_confidence fields this DR
requires — additive migration, executes in D-4's own migration lane.

## 5 — C-0 scope entry (transfers to D-4 as infrastructure)

Registered in `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` as three cross-referenced CR pointers, all
labeled Lane C-0:

- **CR-109 — C-0(a), writer-cardinality fix.** `resolve_activation_windows()`
  (`platform/python-sidecar/services/ka_temporal/date_resolver.py` ~L392-551) collapses all
  matched dasha periods to one `primary_selected` window, bracketing served coverage to
  ~2010-2032. Root cause of the majority of D-3's §G RED (confirmed genuine kernel signal via
  A1's coverage-matching, but the coverage gap itself is a separate, real, independent defect).
  FIX-COV (A2) diagnosed this correctly and STOPPED per its own guard — needs a schema/cardinality
  change exceeding its narrow infra-only remit. Fix: surgical migration + writer-cardinality
  change per CLAUDE.md §N.4, serving full-span birth→2054, zero kernel/weight changes.
- **CR-110 — C-0(b), double dasha-spine bug (native-reported, UNVERIFIED by conductor).**
  `kala_temporal_bundle` observed serving two ayanamsha dasha-period variants interleaved
  undisclosed: Mercury MD reported ending BOTH 2027-08-12 and 2027-08-18; phantom Ketu-MD-2025
  rows carrying Venus/Sun antardashas not belonging to that lineage. Suspected root cause
  (unverified): bundle join pulls across >1 ayanamsha computation without a discriminating
  filter. D-4's binder must independently verify before scoping a fix.
- **CR-111 — C-0(c), convergence-windows build-vs-serve gap (native-reported, UNVERIFIED by
  conductor).** `kala_temporal_bundle` returns 0 convergence windows for 2026-2027 on the
  deployed connector, while `kala_convergence` holds 16,767 TRIGGER-refined rows (the same
  FIX-PSEL/PERF-TRIGGER-CACHE-fixed data verified live this wave) peaking 2027-10-20 to
  2027-11-01. Distinct from CR-109 (window selection/collapse) — this looks like a join/filter
  mismatch between what the build produced and what the serve path returns. D-4's binder must
  independently verify (direct DB query against the deployed connector, CR-96 discipline) before
  scoping a fix.

## 6 — Four carried D-2 findings: current status

D-2's REPORT_D-2.md §6 named 4 findings explicitly carried forward as D-3's opening agenda
(restated formally in D-3's own `PRE_D3_READINESS.md` §B.1 as a named opening-agenda table).
**Honest finding: all 4 remain OPEN/UNTOUCHED as of D-3's close.** None were resolved, fixed, or
explicitly re-carried in D-3's own forward-transfer list (`REPORT_D-3.md` §11 names only C-0,
DR-12, DR-13, LEL v2, and the questionnaire — these 4 items are absent). D-3's actual engineering
effort went to 7 different findings discovered within D-3's own lanes (C1-C7 in
`PRE_D4_WRAPUP_REPORT.md` §C), none of which correspond to these 4. `STATE_D-3.md`'s
`carried_item_dispositions` field also does not name any of these 4 — they were silently left
behind rather than actively dispositioned. This is recorded here so D-4's revision doesn't
silently drop them a second time.

1. **`leverage_index` `subject=venus` false-empty** — code is `VEN`; natural-language `subject`
   param gets 0 rows behind an ambiguous `empty_reason`. STILL OPEN. Directly relevant to D-4
   Lane C-5 (remedy-leverage join) — same surface.
2. **C1 nodal-exaltation offset surface asymmetry** — Rahu-H2 net −0.50 lives on
   `judgment_query.affliction_mechanisms` only, not on the raw `valence_pass` Rahu rows. STILL
   OPEN.
3. **`canonical_faces.json` missing 3 cycle-2 tools** — census 138 live vs 135 listed; 3
   `unaccounted_tools` (`plan_retrieval`, `scan_fetch_signals`, `reading_notes_get`). STILL OPEN.
   Low-effort fix candidate — pure registry bookkeeping.
4. **`judgment_query` v3 oversize baseline** — trimmed 73KB→23KB but still self-flags
   `response_still_over_12kb_budget_after_full_trim`. STILL OPEN. §N.6 `response_budget.ts`
   further-trim work (S-5 class), explicitly deferred pending T-6's `timing_hooks` payload
   reshape — T-6 has since landed in D-3, so this is now re-scopable.

## 7 — C-2's firewall language (verbatim)

**Definition (BRIEF_D4.md §F1, Lane C-2):**
> Firewall re-scoped: quarantine LEL → prediction-INPUTS only; LEL → outcome-SCORING flows
> freely. One-time backfill job: score all 57 LEL events (per chart) against their D-3 mechanism
> curves; batch-write `mimamsa_outcome_record` rows under PH-4-3's train/test discipline. Flips
> n_observations 0 → ~40/chart; promotion gates evaluate for the first time.

**must_not_touch guarantee (BRIEF_D4.md §F2):**
> FROZEN orchestrator contract (PARK) · the leakage firewall on prediction-INPUTS (re-scoped,
> never removed) · raw LEL event data (append-only corpus) · all prior gate surfaces (regression
> batteries).

**Consistency check against the questionnaire flow (BIND_D-4_PREWORK_DRAFT.md §E2):**
> Confirmed consistent, no contradiction found. C-2's firewall: "quarantine LEL →
> prediction-INPUTS only; LEL → outcome-SCORING flows freely." The date-tightening questionnaire
> asks the native to supply TIGHTER GROUND-TRUTH DATES for existing LEL rows — this is LEL data
> entry/correction, not LEL flowing into a prediction input. A tightened date updates what the
> LEL record SAYS happened and when; it does not feed a forward-looking prediction. The
> firewall's INPUT-side quarantine is about preventing a chart reading from being biased by "I
> already know X happened" — tightening a date on an already-past, already-recorded event
> doesn't touch that boundary at all. No firewall violation, no language change needed.

## 8 — Sealed-test-split handling note for tightened dates

From `BIND_D-4_PREWORK_DRAFT.md` (documented here for the first time, no prior artifact
addressed this):
> Tightening a date does NOT change which split an event belongs to. An event dated
> `>= 2020-01-01` (post-tightening or as originally recorded) remains in the sealed test split,
> subject to the same ESCALATION_POLICY §4 restriction (only the gate runner and anti-gaming
> verifier may read it) regardless of whether its date was ever tightened. The questionnaire's
> own firewall (native pins dates blind, zero model/curve information shown) means the tightening
> PROCESS itself cannot leak sealed-split information back to a build/admission agent — the
> native supplies dates directly, no agent brokers that exchange. This is now the explicit,
> documented handling D-4's C-1/C-2 should assume.

The `>= 2020-01-01` sealed-split boundary itself traces to `ESCALATION_POLICY_v1_0.md` §4, and
was independently live-verified by D-3's ADMIT lane: all 36 cache event_dates in range
1984-02-05..2019-05-15 (zero ≥2020-01-01), boundary off-by-one correct both directions
(2020-01-01 exact raises, 2019-12-31 accepts) — recorded in `STATE_D-3.md`.

## 9 — Honest list of every known open item touching D-4's lanes

- **CR-109/110/111 (Lane C-0)** — see §5 above; C-0(a) confirmed root-caused, C-0(b)/(c)
  native-reported and NOT YET independently verified.
- **4 carried D-2 findings** — see §6 above; all 4 still open, 2 of them (leverage_index
  false-empty, canonical_faces census) touch Lane C-5 and general hygiene directly.
- **DR-12's bakeoff** — mandatory battery dimension for C-1, not yet executed (forward-binding
  only, per §4 above).
- **DR-13 + LEL schema v2** — ratified/approved but NOT YET implemented; the additive migration
  is D-4's own migration lane's first job, gated on migration-guard receipt.
- **Windfall event `EVT.2010.XX.XX.01` reclassification** — approved (interval-shaped), not yet
  applied; awaits the LEL schema v2 migration before it can be recorded as such.
- **D-3 per-event scoring artifacts in scratchpad, not yet in permanent storage** — see §3 above,
  flagged honestly as a possible data-survival gap.
- **`NATIVE_DATE_TIGHTENING_QUESTIONNAIRE.md`** — delivered to native (root copy + canonical
  copy), answers not yet returned; D-4's LEL schema v2 migration + tightening flow depends on
  when/whether the native returns it. Not a blocker to opening D-4, but relevant to C-1/C-2
  sequencing.
- **§F3's operational constants** — unchanged, still binding (Cloud Run job path only, rate-limit
  throttling discipline, orchestrator FROZEN).

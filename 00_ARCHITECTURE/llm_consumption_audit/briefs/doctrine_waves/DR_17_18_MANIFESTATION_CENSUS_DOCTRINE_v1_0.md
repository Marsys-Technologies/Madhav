---
artifact: DR_17_18_MANIFESTATION_CENSUS_DOCTRINE
type: DOCTRINE RULING TEXTS + FIRST CENSUS ARTIFACT (for registration in DISAGREEMENT_REGISTER at
  D-4b open)
version: 1.0
status: DR-17/DR-18 NATIVE-RATIFIED IN SUBSTANCE (D-5 gate_run_2 native disposition, STATE_D-5.md
  `native_disposition_gate_run_2`, 2026-07-20) — this artifact is the FIRST FORMAL WRITE-UP of the
  harness spec (§1) the native's ruling implies, plus the first DR-18 census (§2), authored during
  the pre-D-4b readiness pass (v3, 2026-07-21). D-4b's Binder ratifies the harness spec verbatim
  or amends it before B-1/B-3 consume it.
authored_by: Claude Code (Sonnet 5), pre-D-4b readiness pass v3
supersedes: none — new doctrine, companion to DR_14_15_16_TEMPORAL_DOCTRINE_v1_0.md
---

# DR-17 — Graded Manifestation Acceptance (harness spec)

## §0 — Provenance

Named by the native's D-5 gate_run_2 disposition (STATE_D-5.md): rejecting a rank-1-argmax
collapse of point-class serving ("the argmax-per-year collapse is the defect... DR-15 rules
multi-modal densities a legitimate served shape") and rejecting a fabricated-precision plateau cap
("the >2-year continuous major_gain elevation... is NOT a defect... sharpening to sub-year
structure is D-4b's fitted-weights job"). DR-17 formalizes the GRADING scale those two rulings
imply, so B-1's bakeoff and B-3's calibration score against one documented scale rather than each
inventing its own notion of "close enough."

## §1 — The grade scale

Every scored specimen (a LEL event scored against a model's served window/peak for its event_class)
receives exactly one grade from this ordered scale:

| Grade | Meaning | Scoring weight |
|---|---|---|
| `peak` | The model's HIGHEST-intensity served point/window for this event_class overlaps (interval) or lands within its DR-13 confidence-scaled tolerance (point) of the true LEL date, AND the mechanism named by the model is a real, live-active system at that date (not a structural-prior placeholder). | 1.0 |
| `sub_peak` | A NON-rank-1 local maximum (DR-15(a) multi-modal density) overlaps/lands per the same rule as `peak`, but is not the model's single strongest point for the event_class. Per this readiness pass's own top-K local-maxima fix (D-5 gate_run_2 finding 2), this is NOT a lesser finding to be discarded — it is the doctrine's explicit acceptance that several peak-logics can coexist. | 0.75 |
| `elevated` | The true date falls within a served PLATEAU/interval whose intensity is above the event_class's own structural-prior baseline, but does not itself carry a distinct local peak at that date (D-5 gate_run_2 finding 1's plateau case — the major_gain 2-year open-edged window). | 0.5 |
| `neutral` | The true date falls within the model's served horizon but the model's own intensity at that date is statistically indistinguishable from its coverage-matched shuffled-birth control (DR-15(b)) — the model neither found nor missed anything, honestly. | 0.0 |
| `contra` | The model serves an ACTIVE peak/window for a DIFFERENT, non-overlapping date within the same specimen's plausible window, while the true date scores `neutral` or below — the model pointed somewhere wrong with confidence. This is the ONLY grade that can be WORSE than a bare miss. | −0.5 |

**Anti-hit double-weight (native-directed, this pass's brief):** an ADVERSE-valence specimen
(loss/setback/bereavement-class events) that the model calls `contra` — i.e., serves a
GAIN-valence peak where the truth was a loss, or vice versa — is scored at DOUBLE the `contra`
penalty (−1.0, not −0.5). Rationale: DR-16's honest-clarity principle makes a confidently-wrong
VALENCE call (not just a wrong date) the single worst class of error this instrument can commit —
worse than an honest miss, because it actively misleads a consenting adult about which DIRECTION
their elevated-risk window points. This is the "anti-hit constant" the native's brief names;
`−1.0` is PROPOSED here for D-4b Binder ratification, not yet binding (see §4 below — DR is
proposed, not self-ratifying).

## §2 — Tie-bands from pre-registered uncertainty

When two candidate served dates/windows are within the model's OWN pre-registered date-uncertainty
band of each other (DR-13's date_confidence-scaled tolerance: exact ±45d / month ±75d / year-only
secondary battery), they are NOT separately graded and summed — the HIGHER of the two grades is
kept, and the tie is recorded in the per-event artifact as `tie_band_applied: true` with both
candidate dates named. This prevents a model from gaming the grade scale by serving many
near-identical points to farm multiple `sub_peak` credits for what is really one signal.

**Harness-refusal guard (binding, no exceptions):** the tie-band width is FIXED at pre-registration
time (§D of the readiness pass; D-4b's Binder confirms it fresh) from the model's OWN declared
`date_confidence` tier — never computed post-hoc from the scoring run's own results. A harness that
widens or narrows a tie-band AFTER seeing which specimens would score better under the new width is
gate-gaming per DR-15(d)/BRIEF_D4 v2.0's pre-registration rule, and the harness itself REFUSES to
run (raises, does not silently proceed) if it detects its own tie-band parameter differs from the
value committed to the ledger before the first scoring call of a run. This guard is implemented as
an assertion in the harness's own entry point, not a code-review convention.

## §3 — Residual-pair schema

When B-1's bakeoff or B-3's calibration finds two named, independently-live mechanisms disagreeing
on activation for the SAME specimen (the marriage-specimen pattern this readiness pass found:
`chara_karaka` active, `guru_shani_double_transit` also active or inactive depending on
materialization completeness — see this pass's own report §A.0-bis), the pair is recorded as a
`residual_pair` row, not silently resolved by whichever mechanism happens to dominate the ensemble
weight:

```
residual_pair: {
  event_class: str,
  chart_id: str,
  true_date: date,
  mechanism_a: {system_id, active: bool, weight, contribution},
  mechanism_b: {system_id, active: bool, weight, contribution},
  agreement: "concordant" | "discordant",
  disposition: "RESOLVED-BY-MATERIALIZATION" | "RESOLVED-BY-CALIBRATION" | "OPEN-RESIDUAL",
  evidence_ref: str,  -- pointer to the report/session that produced the disposition
}
```

A `residual_pair` is never dropped from the served evidence set even after B-3's calibration
learns a weight for it — it remains the auditable record of WHY the learned weight is what it is.

## §4 — Ratification status

DR-17 is proposed here, native-ratified IN SUBSTANCE (the grading philosophy — graded acceptance
over binary hit/miss, multi-modal legitimacy, plateau honesty) via the D-5 gate_run_2 disposition,
but this §1-§3 HARNESS SPEC (the exact weights, the −1.0 anti-hit constant, the tie-band mechanism)
is a PROPOSAL for the D-4b Binder to ratify verbatim or amend before B-1 consumes it — per
CONDUCTOR_PROTOCOL §4.1, a doctrine-class question routes to Fable for the campaign's disagreement
register, and this artifact stages that routing rather than pre-empting it.

---

# DR-18 — Knowledge-Utilization Census (first census)

## §0 — Purpose

Named by the native's D-5 gate_run_2 disposition (STATE_D-5.md `doctrine_registered` line). Answers
a question no prior wave asked directly: of everything this instrument COULD classically compute
(the full L0 reference corpus — citations, rules, primitives) and everything it HAS computed for
482012f1 (L1-L5 tables), how much reaches a served answer versus sitting unused? A census is not a
gate criterion by itself — it is a coverage map that prioritizes future work by classical weight ×
implementation cost, and it retains negative knowledge (TESTED-NO-SIGNAL) rather than silently
dropping a tried-and-empty avenue.

## §1 — The four buckets

Every classical technique/primitive/generator this codebase implements is classified into exactly
one bucket, per chart (482012f1, this first census):

1. **consumed** — computed AND reaches a served MCP surface's response for at least one realistic
   query shape (spot-checked, not assumed from the writer existing).
2. **consumed-elsewhere** — computed and served, but only via a DIFFERENT surface than the one a
   naive query would hit (e.g. a signal that only shows up in `bodha_signals_get`'s corroboration
   list, never in `judgment_query`'s primary verdict) — flagged so a future serving-density pass
   (§N.6) can decide whether that's the right home for it.
3. **computed-never-consumed** — a writer produces real rows (verified by direct table count) but
   NO current MCP tool reads that table/column in ANY response path. Dead weight; a census
   priority-1 candidate for either wiring in or formally retiring.
4. **known-never-computed** — a classically-attested technique this codebase's own citation
   corpus (`citations.py`, `bg_transit_rules`, etc.) names but no writer implements yet. This is
   NOT a defect list — BRIEF_D5 §7 explicitly scoped some of these out (e.g. a standalone Tājaka
   varṣaphala year-lord signal, `permission.py`'s own documented scope gap) — but it is the honest
   backlog, distinct from bucket 3's "we built it and forgot to wire it" class.

## §2 — First census (Gochara subsystem only, this readiness pass's scope; NOT project-wide)

This readiness pass had time to census the D-5 Gochara-Chitra subsystem only (12 PERMISSION
generators + the 11 G-1 contact primitives + the shape-serving layer) — a project-wide DR-18 census
across all six layers is future work, named explicitly rather than implied complete.

| Item | Bucket | Evidence |
|---|---|---|
| 8 dasha-system PERMISSION generators (vimshottari…yogini) | consumed | `gochara_election_avoidance_get`/`gochara_forecast_get`/`gochara_activation_get` all surface `contributing_systems` incl. `systems_active` from `compute_permission`. |
| `sade_sati_phase` PERMISSION generator | consumed | same surfaces; `system_id="sade_sati"` appears in live `contributing_systems` rows (verified this session: chart 482012f1's committed rows). |
| `guru_shani_double_transit` PERMISSION generator | consumed | Same surfaces; directly the subject of this pass's own A.0-bis re-verification. |
| `av_threshold_state` PERMISSION generator | consumed-elsewhere | fires into `contributing_systems` (served) but its `bindu_count_resolved=False` sub-claim (the live SAV bindu count) is NEVER separately surfaced as its own served field anywhere — a caller cannot ask "is the AV threshold gate's bindu count actually resolved for this chart" without reading the raw JSONB. Candidate for a future serving-density pass, not a defect.
| `planetary_return` PERMISSION generator | consumed | same surfaces. |
| Sarvatobhadra vedha-pair grid (`sarvatobhadra.py`) | **known-never-computed** (classical grid) / consumed (algorithmic approximation) | G-2's own honest finding, carried since D-5 open: migrations 140/144 have zero rows — no real classical grid data lives anywhere in the DB. The ALGORITHMIC approximation IS computed and served (`uncited_extension=true`, disclosed), but the classical grid itself is TESTED-NO-SIGNAL in the sense that the data source was checked and found empty, not merely unimplemented. |
| Tājaka varṣaphala year-lord (standalone, distinct from mudda) | known-never-computed | `permission.py`'s own module docstring names this as an explicit, documented scope gap (BRIEF_D5 §7 exclusion) — `ganita_tajaka_get` exposes a related but not identical surface. |
| `kakshya_cell_crossing`'s DB-sourced boundary variant | consumed-elsewhere | Falls back to an equal-eighths fixture approximation when `ashtakavarga_kakshya_boundary` chart_facts rows are unreachable for a target — the FIXTURE path is what actually serves for most targets today (spot-check needed at D-4b open to quantify what fraction); the real-boundary path is `consumed` only when that L1 data happens to be present. |
| `bg_transit_av_gates` gate rows (all `house_from_moon` values) | consumed for {1,2,3,5,6,9,11}, **computed-never-consumed** for houses {4,7,8,10,12} for chart 482012f1 | This census's own live query (`SELECT house_from_moon, COUNT(*) FROM bg_transit_av_gates GROUP BY house_from_moon`) found gate rows ONLY for houses 1,2,3,5,6,9,11 — houses 4/7/8/10/12 have zero live `bg_transit_av_gates` rows to fire in the first place, which is a GLOBAL (L0) reference-table coverage gap, not a per-chart one. Flagged for a future L0 hygiene pass — every chart is affected equally. |

**Coverage %, this subsystem, this pass:** 6/9 classified items land in `consumed` or
`consumed-elsewhere` (67%); 1 item (Sarvatobhadra classical grid) is genuinely TESTED-NO-SIGNAL;
1 item (Tājaka year-lord) is a documented, in-scope-elsewhere gap; 1 item (AV gate house coverage)
is an L0 reference-table gap affecting every chart identically.

**Prioritized backlog (classical weight × cost, this subsystem):**
1. `bg_transit_av_gates` house-coverage gap (houses 4/7/8/10/12) — HIGH classical weight (AV
   threshold gating is core BPHS Ch.66-68 doctrine), LOW cost (an L0 data-authoring task, not new
   code) — top bakeoff-candidate-family adjacent item: fixing this BEFORE B-1 runs would let the
   av_threshold generator's standalone-contender arm (§1 B-1) be evaluated on its full intended
   design rather than a 7/12-houses-covered approximation.
2. Sarvatobhadra classical grid — HIGH classical weight (CR-21's own centerpiece framing), HIGH
   cost (requires sourcing/authoring real vedha-pair data, not a code fix) — already named,
   TESTED-NO-SIGNAL, correctly not chased further without a native data-sourcing decision.
3. Tājaka year-lord standalone — MEDIUM classical weight (a real sub-system DR-14 names but
   doesn't require as its own line item since `mudda` already covers the annual-period concept),
   LOW-MEDIUM cost — candidate for a future bakeoff-contender-family addition, not urgent.

## §3 — Ratification status

DR-18 is proposed here, native-ratified IN SUBSTANCE (the census discipline itself) via the D-5
gate_run_2 disposition; this first census (§2) is a DATA ARTIFACT, not a doctrine ruling — it is
re-run and extended (project-wide) as a standing B-6/campaign-close discipline, per ARC PLAN's own
framing of DR-18 as a coverage practice, not a one-time report.

---
canonical_id: PROMISE_LAYER_SCOREBOARD
version: 1.0
status: CURRENT
campaign: PRATIJÑĀ v4 (Lane B7 — CAMPAIGN A, MASTER_PLAN_v1_0.md §5)
closes: Rung P9 (MASTER_PLAN_v1_0.md §10) — "scoreboard derivation links resolve" half.
        Degenerate-interval half already closed by Lane B6 (SKILL_MEASUREMENT_REGISTER_v1_0.md
        MEASUREMENT #3).
scope: chart 482012f1-710e-4a25-994a-93821f5871aa, ayanamsha lahiri_chitrapaksha — the ONLY one
       of the three canonical charts with a populated life_events table (64 rows; 1c826d5a and
       cb73cd3d both have zero life_events rows, confirmed live before this artifact was written).
r13_compliance: PURE MEASUREMENT. No weight, threshold, band edge, or rubric constant in
                bo_pratijna_karyatva.py / the v4 scoring engine was read, touched, or informed by
                this artifact. All bo_pratijna_karyatva.py grades in this scoreboard were computed
                by Lanes B0–B6 and closed BEFORE this session opened; this session only queried
                already-computed bodha_pratijna rows and already-recorded life_events rows,
                read-only, and wrote zero rows to any database table. Per R13, any future tuning
                the campaign undertakes must run against held-out charts, never against this
                scoreboard's own comparison chart (482012f1).
---

# PROMISE-LAYER SCOREBOARD v0

**Occurrence-verdict vs. lifetime-outcome, chart 482012f1, all 27 `bo_pratijna_karyatva` classes.**

## 0. What this is and isn't

This is the first-ever instance of this measurement class in the repo — MASTER_PLAN_v1_0.md's own
success dashboard (§7) lists "Promise scoreboard: does not exist → v0 published, all charts" as an
open gate; this artifact is that publication (scoped honestly to the one chart with real outcome
data, per the "all charts" phrasing meaning "all charts that qualify," not a claim that three
charts were scored — see `scope` above).

It is **not** a grading of the v4 engine's accuracy. A single native's 64-event life log is not a
calibration sample — MASTER_PLAN_v1_0.md is explicit that this is "the campaign's fast feedback…
within days," not a statistically powered validation. Read every "verdict" row below as a
qualitative divergence/agreement check, not a p-value.

**Timezone note (verify before reading any date):** `life_events.event_date` is stored as UTC with
a `18:30:00` time-of-day convention, which is `00:00:00 IST` the *following* calendar day (IST =
UTC+5:30). So `event_date = 2013-12-10T18:30:00Z` is **2013-12-11 IST** — this matches the native's
own stated marriage date and is used throughout this document. All "occurred" dates below are
given in IST, derived this way from the raw UTC rows.

## 1. Method — how "lifetime-outcome" was determined per class

Two evidence tiers, stated per class in §2/§3, never blended silently:

- **Direct category/keyword match**: the class has an unambiguous `life_events.category` and/or
  description keyword hit (e.g. `marriage` ↔ category `family`, description contains "Married").
- **Domain match**: no single `category` value names the class; a specific dated row's
  description was read and judged to describe that class's domain (e.g. `career_advancement` ↔
  the Tepper-sponsorship row, category `career`, "Selected as one of the top employees").

Every class below cites the exact `event_id`(s) it matched on — reproducible, not vibes. Where no
row could be honestly matched (ambiguous or absent), the class is marked **no-outcome-data**, not
forced into a verdict.

**One data-hygiene finding surfaced during this matching pass, reported per R16 (not silently
dropped):** `life_events` contains one row, `event_id 5278d97c-e769-529a-b0c2-be1e965c2d6b`
(`event_date` 2025-07-31 IST, `category='travel_event'`), whose description is explicitly labeled
`"[TEST FIXTURE - D-4a Lane A-4 append-hook live demonstration, NOT real native data]"`. This row
was **excluded** from `travel_event`'s outcome evidence below — its own description disclaims
being real data, so counting it would fabricate an outcome. `travel_event`'s verdict below rests
solely on the real 2010 Thailand-trip row.

## 2. Non-provisional classes (22) — the primary table

`status` / `occurrence_grade` (band, [0,1]) / `condition_grade` (affliction magnitude, [0,10],
higher = worse) are read verbatim from `bodha_pratijna` for
`chart_id=482012f1-…`/`ayanamsha_id=lahiri_chitrapaksha`. Band labels (`WEAK`/`MODERATE`/…,
`CLEAN`/`MILD`/…) are the engine's own `derivation.occurrence_label`/`derivation.condition_label`
— not recomputed here, per §N.7 (narration restates a cited value, never re-derives it).

| Class | v4 status | occurrence (label) | condition (label) | Lifetime outcome | Match basis | Verdict |
|---|---|---|---|---|---|---|
| **marriage** | conditional | 0.321 (WEAK) | 5.83 (MODERATE) | **Occurred** — married 2013-12-11 | `b72f40f7-…`, category `family`, "Married childhood girlfriend" | **VERDICT — see §4, THE MARRIAGE ANSWER** |
| **separation** | conditional | 0.505 (MODERATE) | 8.75 (CRITICAL) | **Occurred** — separated 2026-04-17 | `1f9c6775-…`, category `relationship`, "Separated from wife" | VERDICT — agreement (moderate promise, severe/critical affliction, and it happened under real affliction) |
| **childbirth** | conditional | 0.593 (MODERATE) | 7.50 (SEVERE) | **Occurred** — twin daughters born 2022-01-03 | `25a0f2ec-…`, category `family`, "Twin daughters born" | VERDICT — agreement |
| **surgery** | conditional | 0.471 (MODERATE) | 6.25 (SEVERE) | **Occurred** — right knee arthroscopy 2007-06-15 | `4e09e1e1-…`, category `health`, "(minor surgery)" | VERDICT — agreement |
| **relocation** | conditional | 0.486 (MODERATE) | 8.75 (CRITICAL) | **Occurred** (×2) — moved to US 2019-05-15; returned to India 2023-05-15 | `928a1f56-…`, `7f29458f-…`, category `residential+travel` (domain match — no `relocation`-named category exists) | VERDICT — agreement |
| **foreign_settlement** | promised | 0.707 (STRONG) | 7.50 (SEVERE) | **Occurred** — 4-year US residence 2019–2023 | `928a1f56-…-fs`, explicit "R15 ruling: … counts as genuine foreign settlement. Shadow row for scoring" — a row purpose-built for this exact check | VERDICT — agreement |
| **romantic_start** | conditional | 0.286 (WEAK) | 7.50 (SEVERE) | **Occurred** (×3) — R#1 1998-02-15, R#2 2004-01-15, R#3 2012-10-15 | `3a37fa76-…`, `45ba996d-…`, `aa591eb5-…`, category `relationship`, "started" | VERDICT — divergence (WEAK occurrence promise vs. three real relationship starts — see §5) |
| **career_entry** | promised | 0.786 (STRONG) | 3.75 (MILD) | **Occurred** — joined Cognizant 2007-06-10 ("first corporate IT job") | `fd04fecc-…`, category `career` | VERDICT — agreement |
| **career_change** | promised | 0.774 (STRONG) | 6.25 (SEVERE) | **Occurred** (×2+) — exited Cognizant 2008-06-09; switched Mahindra Retail→Tech Mahindra 2017-03-15 | `aed78f94-…`, `e3b2f1d5-…`, category `career` | VERDICT — agreement |
| **career_advancement** | promised | 0.771 (STRONG) | 7.50 (SEVERE) | **Occurred** — selected top Mahindra Group employee, Tepper/CMU Executive-MBA sponsorship 2021-07-01 | `b8884cbe-…`, category `career`, "Selected as one of the top employees" | VERDICT — agreement |
| **career_setback** | promised | 0.870 (VERY_STRONG) | 7.50 (SEVERE) | **Occurred** — Mahindra Retail "crashed," career stress 2016-07-01; 2nd quarry unable to operationalize ~2021–2026 | `b5ea6a4d-…`, `74e527bb-…`, category `career` | VERDICT — agreement |
| **business_launch** | promised | 0.698 (STRONG) | 8.75 (CRITICAL) | **Occurred** — founded Marsys Group 2023-07-15; launched Kotadwara mining 2024-02-16 | `661c8535-…`, `836bb274-…`, category `career`, "Founded" / "Launched" | VERDICT — agreement |
| **education_milestone** | conditional | 0.583 (MODERATE) | 6.25 (SEVERE) | **Occurred** (many) — B.Tech completed 2007-06-15; XIMB MBA graduated 2013-03-15; Tepper/CMU EMBA completed 2023-06-15 | `71af4f61-…`, `c143ce2a-…`, `d506f3e6-…`, category `education` | VERDICT — agreement |
| **exam_outcome** | conditional | 0.500 (MODERATE) | 6.25 (SEVERE) | **Ambiguous** — no `life_events` row records a discrete exam pass/fail result distinct from the admission/graduation milestones already counted under `education_milestone`; the one exam-adjacent row (`39f8395f-…`, Aptech, "could not sit certification exam") records a non-attempt, not an outcome | none confident | **NO-OUTCOME-DATA** |
| **illness_acute** | conditional | 0.471 (MODERATE) | 6.25 (SEVERE) | **Occurred** — panic/anxiety episode Jan 2021 | `974651b2-…`, category `health`, "Health episode with jitters and sweating — panic/anxiety episode" | VERDICT — agreement |
| **chronic_onset** | conditional | 0.586 (MODERATE) | 3.75 (MILD) | **Occurred** — sleep disorder onset 2007-08-31, explicitly "Persisted ~18 years" | `8573c0ca-…`, category `health` (corroborated by `3e96c6da-…`, congenital stammering, also chronic) | VERDICT — agreement |
| **major_gain** | promised | 0.639 (STRONG) | 10.00 (CRITICAL) | **Occurred** — first major Marsys contract 2025-07-15 ("Windfall-class revenue"); Marsys Technology "enormous profits" 2026-03-20 | `4018cc05-…`, `153d920e-…`, category `finance`/`career` | VERDICT — agreement |
| **major_loss** | promised | 0.625 (STRONG) | 10.00 (CRITICAL) | **Occurred** — major deception/scam event May 2025 | `d81fae4e-…`, category `loss`, "deceived / defrauded" (same row cross-cited under `financial_deception`, §3) | VERDICT — agreement |
| **property_acquisition** | conditional | 0.350 (WEAK) | 6.25 (SEVERE) | **Ambiguous** — no `life_events` row records the native acquiring property; the only property-adjacent row (`bd7f5711-…`) is the *father* selling real estate, opposite direction and different person | none confident | **NO-OUTCOME-DATA** |
| **bereavement** | promised | 0.686 (STRONG) | 10.00 (CRITICAL) | **Occurred** (×2) — paternal grandfather passed 2009-06-15; father passed 2018-11-28 | `1dc207bc-…`, `b75c63f4-…`, category `loss` | VERDICT — agreement |
| **parental_event** | conditional | 0.500 (MODERATE) | 6.25 (SEVERE) | **Occurred** — twin daughters born 2022-01-03 (native becoming a parent) | `25a0f2ec-…` — **note: same row as `childbirth`'s evidence**, not an independent corroboration; flagged rather than presented as a second confirming data point | VERDICT — agreement, weak-independence caveat |
| **spiritual_turn** | promised | 0.740 (STRONG) | 7.50 (SEVERE) | **Occurred** (7+ rows) — Ugratara devotion from 2010; Mahadev/Shiva turn; daily abhisheka from 2024; Vishnu/Balaji turn 2025; Mahalakshmi/Kamlatmika practice 2025 | `132b61e0-…`, `56a1222d-…`(+corr), `63e90113-…`, `acb209c7-…`, `3ea3a2fc-…`, category `spiritual` | VERDICT — agreement |

**22/22 non-provisional classes accounted for. 20 verdict, 2 no-outcome-data** (`exam_outcome`,
`property_acquisition`) — reported honestly rather than forced.

## 3. Provisional classes (5) — reported separately, per DR-13 (R16: not silently omitted)

These 5 use `bo_pratijna_karyatva.KARYATVA_REGISTRY`'s domain-fallback derivation
(`provisional=True`), not the full factor-band rubric §2–§6 of `V4_RUBRIC_SPEC_v1_0.md` uses for
the 22 above. Their `condition_grade=0.000`/`CLEAN` is **not** a computed "no affliction" finding —
every one of the 5 has an **empty `condition_ledger: []`** in its `derivation`, i.e. the
condition-side slot is structurally unpopulated for provisional classes, not evaluated-and-clean.
Reported as `CLEAN` (the engine's own literal label) with this caveat attached, not silently
re-labeled.

| Class | v4 status | occurrence (label) | condition (label, caveat above) | Lifetime outcome | Match basis | Verdict |
|---|---|---|---|---|---|---|
| **achievement_recognition** | promised | 0.891 (VERY_STRONG) | 0.00 (CLEAN†) | **Occurred** — top-Mahindra-employee/Tepper sponsorship 2021-07-01; elected IRC President at XIMB 2012-08-31 | `b8884cbe-…`, `cf0c918d-…` | VERDICT — agreement |
| **financial_deception** | promised | 0.841 (VERY_STRONG) | 0.00 (CLEAN†) | **Occurred** — major deception/scam event May 2025 | `d81fae4e-…` (same row as `major_loss`, §2 — cross-class, not independent) | VERDICT — agreement, weak-independence caveat |
| **psychological_arc** | promised | 0.661 (STRONG) | 0.00 (CLEAN†) | **Occurred** — stammering 3-phase arc (congenital onset, per 2026-07-19 native correction); vertigo/head-reeling arc ~2001–2004 | `3e96c6da-…` (+ congenital correction row), `123eee97-…` | VERDICT — agreement |
| **birth_anchor** | conditional | 0.564 (MODERATE) | 0.00 (CLEAN†) | **Occurred, trivially** — this class's own subject is the native's birth itself | `5d039007-…`, "Born in Bhubaneswar…" | VERDICT — **degenerate match, near-zero informativeness** (the class is definitionally satisfied by chart existing at all; do not read this row as evidence the v4 engine "predicted" anything) |
| **travel_event** | promised | 0.745 (STRONG) | 0.00 (CLEAN†) | **Occurred** — first international travel, Thailand, Dec 2010 | `a1ef10c2-…`. **Test-fixture row `5278d97c-…` explicitly excluded** — see §1 hygiene finding | VERDICT — agreement |

† = structurally-unpopulated condition slot for provisional classes, not a computed clean reading. See preamble above the table.

**No class, provisional or non-provisional, was reported `no_evidence` by the v4 engine itself** —
all 27 `bo_pratijna_karyatva` classes returned a real `bodha_pratijna` row with a real
`occurrence_grade`/`condition_grade` for this chart (27 rows queried = 27 classes in the registry;
none missing). The `no_evidence` state defined in this scoreboard's own three-state schema
(engine-side "no karyatva-derivable evidence") therefore has zero occurrences in this run — an
honest finding, not an omission.

## 4. THE MARRIAGE ANSWER

v4's real, unmodified verdict for chart `482012f1` marriage:

> **`status = conditional`, `occurrence_grade = 0.321` (WEAK), `condition_grade = 5.830`
> (MODERATE), composite `grade = 3.210`.**

The real lifetime outcome: **marriage did occur** — 2013-12-11, to the native's long-term
girlfriend (relationship #1, dating since 1998), per `life_events.event_id b72f40f7-687e-51dd-a21d-06b184fc24c1`.

**This is served at its earned tier, unmodified in either direction.** A WEAK occurrence score
(0.321, the second-lowest of all 27 classes — only `romantic_start` at 0.286 is lower) coexisting
with a real marriage having happened is not corrected, softened, or reconciled here. Per R13 this
is a measurement artifact, not a target: nothing about this divergence fed back into
`bo_pratijna_karyatva.py`'s weights, bands, or denial rules, and nothing will, except on held-out
charts in a future lane.

**What the divergence plausibly means, stated as interpretation, clearly separated from the
measurement above:** `occurrence_grade` measures how strongly the *classical factor set*
(house-lord/karaka/divisional/yoga-keyword bands, §2 of `V4_RUBRIC_SPEC_v1_0.md`) supports the
class occurring, before any denial deductions. A WEAK reading paired with a real occurrence is
consistent with — but does not by itself prove — a marriage that happened against a
structurally-unsupportive configuration (the `condition_grade=5.83`/MODERATE affliction is a
separate axis and is *not* low; the chart does show real affliction to the domain, just not enough
of it alone to explain a WEAK *occurrence* score, which is about promise strength, not affliction).
The v3 predecessor engine had marriage sitting at `DENIED` for this same native
(`V4_RUBRIC_SPEC_v1_0.md` §6.1's own stated motivation for building five bands instead of three) —
v4's WEAK is a real, measured improvement in calibration direction even though it still under-reads
a chart that did produce a marriage. This is exactly the kind of informative miss Lane B7 exists to
surface, not paper over.

## 5. Derivation-link resolution check (Rung P9 closing condition)

For every one of the 27 classes above (all classes checked, not only the 20 "verdict" ones, for
full coverage), the class's `bodha_pratijna.derivation->'provenance'` array was queried and its
first `fact_id`-kind entry was independently resolved against `chart_facts.fact_id` (scoped to
`chart_id=482012f1-…`) via a live join — not a JSONB-non-null check.

**Result: 27/27 resolve. Zero failures.**

| Class | Provenance id checked | id_kind | Resolves in `chart_facts`? |
|---|---|---|---|
| achievement_recognition | `cbcb638efb19aa49` | fact_id | ✅ |
| bereavement | `945a71ef7fb384eb` | fact_id | ✅ |
| birth_anchor | `7c00df1c58b81ca4` | fact_id | ✅ |
| business_launch | `fd0a642e4b7dac57` | fact_id | ✅ |
| career_advancement | `cbcb638efb19aa49` | fact_id | ✅ |
| career_change | `cbcb638efb19aa49` | fact_id | ✅ |
| career_entry | `cbcb638efb19aa49` | fact_id | ✅ |
| career_setback | `cbcb638efb19aa49` | fact_id | ✅ |
| childbirth | `668b206715869f4f` | fact_id | ✅ |
| chronic_onset | `5a00f21d615413c0` | fact_id | ✅ |
| education_milestone | `98496ea4bb167fb5` | fact_id | ✅ |
| exam_outcome | `98496ea4bb167fb5` | fact_id | ✅ |
| financial_deception | `945a71ef7fb384eb` | fact_id | ✅ |
| foreign_settlement | `f511ae350ec6b456` | fact_id | ✅ |
| illness_acute | `5a00f21d615413c0` | fact_id | ✅ |
| major_gain | `25a1202387872c9c` | fact_id | ✅ |
| major_loss | `25a1202387872c9c` | fact_id | ✅ |
| marriage | `fd0a642e4b7dac57` | fact_id | ✅ |
| parental_event | `98496ea4bb167fb5` | fact_id | ✅ |
| property_acquisition | `98496ea4bb167fb5` | fact_id | ✅ |
| psychological_arc | `668b206715869f4f` | fact_id | ✅ |
| relocation | `98496ea4bb167fb5` | fact_id | ✅ |
| romantic_start | `668b206715869f4f` | fact_id | ✅ |
| separation | `fd0a642e4b7dac57` | fact_id | ✅ |
| spiritual_turn | `c9d59accee6b4e89` | fact_id | ✅ |
| surgery | `5a00f21d615413c0` | fact_id | ✅ |
| travel_event | `acdd5ed7183512e2` | fact_id | ✅ |

**Spot-check on a second link kind:** `marriage`'s `derivation.provenance` also carries 11
`chart_divisionals_id` entries (varga placements). One (`e12c0163-61f4-4242-bd12-a0f154359445`) was
independently resolved against `chart_divisionals.id` scoped to the same `chart_id` — resolves
(confirmed live, not re-tabulated above for brevity).

**Rung P9 verdict: GREEN.** Both halves of the measurement tripwire are now closed: the
degenerate-interval stop (Lane B6, prior) and this scoreboard's derivation-link resolution (this
lane). No fabricated, dangling, or self-referential provenance id was found anywhere in the 27-row
scan.

## 6. Summary

| Metric | Count |
|---|---|
| Non-provisional classes scored | 22 / 22 |
| Provisional classes scored (reported separately) | 5 / 5 |
| `no_evidence` (engine-side) | 0 |
| `verdict` (real occurrence-verdict + real lifetime outcome, compared) | 25 (20 non-provisional + 5 provisional) |
| `no-outcome-data` (real verdict, no confident outcome match) | 2 (`exam_outcome`, `property_acquisition`) |
| Derivation links checked | 27 / 27 |
| Derivation links resolved | 27 / 27 (100%) |
| Derivation links failed | 0 |
| THE MARRIAGE ANSWER | WEAK occurrence (0.321) / MODERATE condition (5.83) vs. real marriage — served unmodified |

**SCOREBOARD PUBLISHED. Rung P9 GREEN.**

---
*v1.0 (2026-08-09, Lane B7, PRATIJÑĀ v4 campaign). First publication of this measurement class.
Pure measurement — see `r13_compliance` frontmatter field. Scope: chart `482012f1` only (the sole
canonical chart with populated `life_events`); `1c826d5a`/`cb73cd3d` carry zero `life_events` rows
as of this writing and are out of scope, not silently dropped — recorded in `scope` above.*

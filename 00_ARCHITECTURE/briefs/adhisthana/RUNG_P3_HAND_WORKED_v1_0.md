---
canonical_id: RUNG_P3_HAND_WORKED
version: 1.0
status: DRAFT — for CHECKPOINT review (native + Fable)
date: 2026-08-08
campaign: ADHIṢṬHĀNA, Rung P3 (MASTER_PLAN_v1_0.md §10) — the checkpoint's numeric input
author: Conductor (Sonnet 5)
chart: 482012f1-710e-4a25-994a-93821f5871aa (Abhisek Mohanty), ayanamsha lahiri_chitrapaksha
inputs: A8_FACTOR_FACT_COVERAGE_MATRIX_v1_0.md (fact locations) + V4_RUBRIC_SPEC_v0_9.md
  (bands/weights/formulas) + Rung P2's established retrieval pattern (chart_divisionals for
  base position/occupancy/lordship, chart_fact_identity+chart_facts for derived signals)
r13_statement: >
  All facts below were retrieved from the live chart AFTER the rubric spec (bands, weights,
  denial rules, thresholds) was already fixed in V4_RUBRIC_SPEC_v0_9.md. No band, weight, or
  threshold was adjusted after seeing these numbers. Where a computed score happens to align or
  misalign with the native's known life events, that correspondence is reported factually (the
  checkpoint's own explicit purpose per MASTER_PLAN_v1_0.md §4 is to ask "do the numbers read
  like astrology?") — it played no role in producing the spec or these calculations.
---

# RUNG P3 — Hand-Worked Marriage, Separation, Childbirth (chart 482012f1)

**Per MASTER_PLAN_v1_0.md §10, Rung P3: "Hand-worked rubric on live facts: marriage/separation/
childbirth scored BY HAND from P2-retrieved facts — the numbers the checkpoint reviews ARE this
probe's output." Green means: "The future engine's logic produces astrology-shaped numbers before
any engine exists."** No code was written to produce these numbers — every value below is a
manual computation, shown in full, from live query results.

---

## §0 — Shared base data (retrieved once, live, both used by multiple classes below)

### §0.1 — Planetary dignity anchors (`reference_planets`, live, 2026-08-08)

| Planet | Exalt sign | Debil sign | Mūlatrikoṇa sign | Own signs |
|---|---|---|---|---|
| Sun | 1 (Aries) | 7 (Libra) | 5 (Leo) | {5} |
| Venus | 12 (Pisces) | 6 (Virgo) | 7 (Libra) | {2,7} |
| Jupiter | 4 (Cancer) | 10 (Capricorn) | 9 (Sagittarius) | {9,12} |
| Saturn | 7 (Libra) | 1 (Aries) | 11 (Aquarius) | {10,11} |
| Mars | 10 (Capricorn) | 4 (Cancer) | 1 (Aries) | {1,8} |
| Mercury | 6 (Virgo) | 12 (Pisces) | 6 (Virgo) | {3,6} |
| Moon | 2 (Taurus) | 8 (Scorpio) | 2 (Taurus) | {4} |
| Rahu | 2 (Taurus) | 8 (Scorpio) | — | {} |
| Ketu | 8 (Scorpio) | 2 (Taurus) | — | {} |

Naisargika (natural) friend/enemy table (BPHS ch.3, standard, cited by `V4_RUBRIC_SPEC_v0_9.md
§2.1`'s reference to `ga_condition_writer.py`'s `_NAISARGIKA` dict):

| Planet | Friends | Enemies | Neutral |
|---|---|---|---|
| Sun | Moon, Mars, Jupiter | Venus, Saturn | Mercury |
| Venus | Mercury, Saturn | Sun, Moon | Mars, Jupiter |
| Jupiter | Sun, Moon, Mars | Mercury, Venus | Saturn |
| Saturn | Mercury, Venus | Sun, Moon, Mars | Jupiter |
| Mars | Sun, Moon, Jupiter | Mercury | Venus, Saturn |

Tatkalika (temporal, house-distance) doctrine, standard: planet B is a temporal friend of planet A
if B occupies the 2nd/3rd/4th/10th/11th/12th house counted from A's own sign; temporal enemy if
1st/5th/6th/7th/8th/9th. Compounded with naisargika per the standard five-fold (pañcadhā maitri)
table: friend+friend→great friend(0.70); friend+enemy→neutral(0.50); neutral+friend→friend(0.60);
neutral+enemy→enemy(0.30); enemy+friend→neutral(0.50); enemy+enemy→great enemy(0.20). **Citation
note (§8-style honesty, matching the rubric spec's own convention): this is doctrine cited by
name, not independently verified against a specific chapter/verse by this document's author.**
Rāhu/Ketu are excluded from this table per the rubric spec's own ruling (nodes test only
exalted/debilitated/neutral-default, §2.1).

### §0.2 — D1 (rāśi) positions, live (`chart_divisionals`, `varga='D1'`, `fact_category=
'varga_position'`, ayanamsha `lahiri_chitrapaksha`)

Whole-sign house system confirmed (Lagna = Aries = sign 1 = house 1, so house N = sign N
throughout this chart — verified against the FORENSIC 7/7 anchor: Sun=Capricorn, Lagna=Aries):

| Graha | Sign (=House) |
|---|---|
| Lagna | 1 Aries |
| Rahu | 2 Taurus |
| Mars | 7 Libra |
| Saturn | 7 Libra |
| Ketu | 8 Scorpio |
| Venus | 9 Sagittarius |
| Jupiter | 9 Sagittarius |
| Sun | 10 Capricorn |
| Mercury | 10 Capricorn |
| Moon | 11 Aquarius |

**Houses 3, 4, 5, 6, 12 are EMPTY** — verified live, zero occupant rows for any of the five
(`chart_divisionals` `fact_category='varga_house_occupant'` grouped by house, full 12-house scan,
2026-08-08). This is decision-critical for the denial-configuration checks below.

House lords (`kp_house_significators` `fact_key='cusp_owner'`, live, all 12 confirmed — this table
was already spot-checked in `A8_FACTOR_FACT_COVERAGE_MATRIX_v1_0.md §0.3` and is internally
consistent with Rung P2's independent cusp-longitude derivation of the 7th lord):

1L=Mars · 2L=Venus · 3L=Mercury · 4L=Moon · 5L=Sun · 6L=Mercury · 7L=Venus · 8L=Mars · 9L=Jupiter
· 10L=Saturn · 11L=Saturn · 12L=Jupiter

### §0.3 — Dignity-band lookups used below (worked once per planet+sign, reused across classes)

| Planet @ Sign | Test | Result | Band |
|---|---|---|---|
| Venus @ 9 (Sagittarius) | not exalt(12)/debil(6)/mūla(7)/own({2,7}). Lord=Jupiter. Natural: Venus↔Jupiter=**neutral**. Tatkalika: Venus(9)→Jupiter(9), distance=((9−9)mod12)+1=**1** → enemy-set. Compound: neutral+enemy=**enemy** | Enemy (śatru) | **0.30** |
| Jupiter @ 9 (Sagittarius) | mūlatrikoṇa_sign=9 — direct match (own_signs also contains 9, but mūlatrikoṇa is checked first per the band's ordering) | Mūlatrikoṇa | **0.90** |
| Saturn @ 7 (Libra) | exaltation_sign=7 — direct match | Exalted | **1.00** |
| Ketu @ 8 (Scorpio) | exaltation_sign=8 — direct match (nodes: exalt/debil/neutral-default only, §2.1) | Exalted | **1.00** |
| Sun @ 10 (Capricorn) | not exalt(1)/debil(7)/mūla(5)/own({5}). Lord=Saturn. Natural: Sun↔Saturn=**enemy**. Tatkalika: Sun(10)→Saturn(7), distance=((7−10)mod12)+1=**10** → friend-set. Compound: enemy+friend=**neutral** | Neutral (sama) | **0.50** |
| Venus @ 6 (Virgo, D9) | debilitation_sign=6 — direct match | Debilitated | **0.00** (matches Rung P2's independent cross-check: `chart_fact_identity` D9_VEN `dignity_state`='debilitated', internally consistent) |
| Saturn @ 1 (Aries, D9) | debilitation_sign=1 — direct match | Debilitated | **0.00** |
| Jupiter @ 11 (Aquarius, D7) | not exalt(4)/debil(10)/mūla(9)/own({9,12}). Lord=Saturn. Natural: Jupiter↔Saturn=**neutral**. Tatkalika (using D1 positions, per this document's stated convention — dignity is read against the varga sign, but graha-to-graha friendship is computed from the natal/D1 snapshot, the standard software convention): Jupiter(D1 sign 9)→Saturn(D1 sign 7), distance=((7−9)mod12)+1=**11** → friend-set. Compound: neutral+friend=**friend** | Friend (mitra) | **0.60** |

D1 sign-9 (Sagittarius): both Venus AND Jupiter are conjunct there — this single conjunction
produces the "enemy" reading for Venus (tatkalika distance-1 = same-sign = enemy-set by the
standard rule) even though Venus's natural relationship to Jupiter is neutral. Flagged because
it is the single most consequential dignity reading below (Venus is 7L, marriage's own primary
karaka, AND separation's core-house-lord).

---

## §1 — MARRIAGE

**KaryatvaMap** (`bo_pratijna_karyatva.py`): `primary_bhava=[7]`, `karaka_grahas=[Venus,Jupiter]`,
`divisional=D9`, `yoga_keywords=[darakaraka,upapada,kalatra]`, `condition_malefic_grahas=
[Saturn,Rahu,Ketu]`. Citations: BPHS ch.19, ch.28, ch.6; Jaimini Sutram 1.3.1.

**Weights** (`V4_RUBRIC_SPEC_v0_9.md §3.2`, 4-slot renormalized): 7L=0.500000, Venus(karaka)=
0.142857, Jupiter(karaka)=0.142857, divisional=0.142857, yoga=0.071429.

### §1.1 — Occurrence

| Slot | Weight | Band (from §0.3) | Contribution |
|---|---|---|---|
| 7L = Venus @ D1 | 0.500000 | 0.30 (enemy) | 0.150000 |
| Karaka: Venus @ D1 | 0.142857 | 0.30 (enemy — same planet/position as 7L, a real coincidence of this chart, not double-computed differently) | 0.042857 |
| Karaka: Jupiter @ D1 | 0.142857 | 0.90 (mūlatrikoṇa) | 0.128571 |
| Divisional: Venus @ D9 | 0.142857 | 0.00 (debilitated) | 0.000000 |
| Yoga | 0.071429 | 0.00 — see §1.3 | 0.000000 |
| **Sum (pre-denial)** | | | **0.321429** |

**Denial configurations checked (§4 of the spec):**
- **CFG-1** (7L + primary karaka both debilitated): 7L=Venus(0.30), primary karaka=Venus(0.30) —
  neither is 0.00/debilitated. **Does not fire.**
- **CFG-3** (pāpakartarī on house 7 — malefics in both house 6 and house 8): house 6 is **empty**
  (§0.2, live-verified) — the 12th-from-7 side has no occupant at all, let alone a malefic.
  **Does not fire** (fails at the first condition).
- CFG-2 is N/A (marriage is not `dusthana_required`).

**No deductions.** Occurrence(marriage) = clamp₀¹(0.321429) = **0.321**

### §1.2 — Threshold reading (§6.1)

0.321 falls in **[0.20, 0.40) = WEAK**: "A minority of the class's classical evidence set is
present. Occurrence is not supported as more-likely-than-not by this rubric."

### §1.3 — Yoga slot: an honest gap, not an improvisation

Per `A8_FACTOR_FACT_COVERAGE_MATRIX_v1_0.md §1.4`: `darakaraka` (Jaimini chara-karaka, 70 live
rows) and `upapada` (10 live rows, including an `'afflicted_marriage_indication'` verdict row on
this exact chart) both have real, on-topic, non-empty live facts. `kalatra` has none (dispositioned
as redundant, not a gap). **However**, none of the three is a `ganita_yoga_firings_get`
firings-authoritative match or even a `ganita_yogas_get` catalog-only match — a direct live check
against `ga_yoga_firings` for this chart found no marriage-relevant yoga firing (one substring hit,
`kedara`, was checked and is a false positive — Kedara Yoga is an unrelated planetary-distribution
yoga, not a spouse-signification yoga; excluded per the same false-positive discipline the Coverage
Matrix used for `kshetra`).

**This is a real design tension for the checkpoint, not resolved here**: the rubric's yoga-tier
band (§2.5) is scoped narrowly to the yoga catalog/firings system, but marriage's own most
citable classical evidence (darakaraka, upapada) lives in a *different* fact system (Jaimini
special points), which the current band definition cannot see. Applying §2.5 strictly gives
**0.00** (no match) — which is what is used above — even though real, relevant, non-empty evidence
exists elsewhere in the chart. Recommendation for Campaign B: either broaden the yoga-tier band to
accept special-point/karaka evidence as a distinct sub-tier, or accept that these three classes'
yoga slots will structurally read low under the current band definition regardless of what the
chart shows.

### §1.4 — Condition

`condition_malefic_grahas=[Saturn,Rahu,Ketu]`, target = house 7 / its lord Venus.

| Malefic | Position | Relationship to house 7 / Venus (house 9) | Contribution (§2.7) |
|---|---|---|---|
| Saturn | House 7 | **Conjunct the core house itself** (occupies house 7) | **1.00** |
| Rahu | House 2 | To house 7: 7th-from-2=house 8, no match. To Venus (house 9): 8th-from-2=house 9 — general 4th/8th aspect | **0.75** |
| Ketu | House 8 | To house 7: 7th-from-8=house 2, no match. To Venus (house 9): tested all four general-aspect distances (4th/8th/5th/9th/3rd/10th from house 8 = 11/3/12/4/10/5) — house 9 matches none | **0.00** |

condition(marriage) = clamp₀,₁₀( 10 × (1.00+0.75+0.00)/3 ) = 10 × 1.75/3 = 10 × 0.5833 = **5.83**

**Threshold reading (§6.2):** 5.83 falls in **[4,6) = MODERATE**: "Meaningful affliction; visible
friction should be expected in this domain's manifestation."

### §1.5 — Marriage summary

**Occurrence = 0.321 (WEAK) · Condition = 5.83 (MODERATE affliction)**

---

## §2 — SEPARATION

**KaryatvaMap**: `primary_bhava=[7,6,8,12]` (7=core, 6/8/12=dusthana), `karaka_grahas=
[Saturn,Ketu]`, `dusthana_required=True`, `divisional=D9`, `yoga_keywords=[kuja_dosha,manglik,
6L-7L]`, `condition_malefic_grahas=[Mars,Rahu]`. Citations: BPHS ch.19, ch.12, ch.28.

**Weights** (5-slot, no renormalization needed — base subtotal already 1.00): 7L=0.35, dusthana
(6th/8th/12th, 0.10 each)=0.30 total, Saturn(karaka)=0.10, Ketu(karaka)=0.10, divisional=0.10,
yoga=0.05.

### §2.1 — Dusthana-involvement band, worked in full (§2.6)

Core house-lord = Venus (7L), D1 house = 9 (§0.2).

| Dusthana house | House lord | Structural connection test | Result |
|---|---|---|---|
| 6 | Mercury (D1 house 10) | (a) Venus not in house 6. (b) Mercury's 7th-aspect from house 10 = house 4; no aspect/conjunction reaches house 7 or Venus (house 9). (c) No parivartana (Mercury not in Venus's sign 2/7; Venus not in Mercury's sign 3/6). | **NOT connected** |
| 8 | Mars (D1 house 7) | (a) Venus not in house 8. **(b) Mars physically occupies house 7 — direct conjunction with the core house itself.** | **CONNECTED** |
| 12 | Jupiter (D1 house 9) | (a) Venus not in house 12. **(b) Jupiter occupies house 9 — the SAME house as Venus (7L) — direct conjunction with the core house's lord.** | **CONNECTED** |

Band = 2 connected / 3 cited = **0.6667**. Contribution to occurrence = 0.30 × 0.6667 =
**0.200000** (identical to summing three per-house terms 0.10×0 + 0.10×1 + 0.10×1 = 0.20 — the
two equivalent formulations in the spec's §2.6/§3.1 converge exactly, as they must).

### §2.2 — Occurrence

| Slot | Weight | Band | Contribution |
|---|---|---|---|
| 7L = Venus @ D1 | 0.35 | 0.30 (enemy, §0.3) | 0.105000 |
| Dusthana involvement (§2.1 above) | 0.30 | 0.6667 | 0.200000 |
| Karaka: Saturn @ D1 | 0.10 | 1.00 (exalted, §0.3) | 0.100000 |
| Karaka: Ketu @ D1 | 0.10 | 1.00 (exalted, §0.3) | 0.100000 |
| Divisional: Saturn @ D9 | 0.10 | 0.00 (debilitated, §0.3) | 0.000000 |
| Yoga | 0.05 | 0.00 (see §1.3's finding — same gap applies; `manglik` `dosha_label` exists live but is not a yoga-firing match under the spec's strict §2.5 test) | 0.000000 |
| **Sum (pre-denial)** | | | **0.505000** |

**Denial configurations checked:**
- **CFG-1** (7L + primary karaka both debilitated): 7L=Venus(0.30), primary karaka=Saturn(1.00,
  exalted) — neither debilitated. **Does not fire.**
- **CFG-2** (core house-lord occupies a cited dusthana house, debilitated/combust there): Venus's
  D1 house is 9 — not one of separation's own dusthana houses (6/8/12). **Does not fire** (fails
  at the placement test before dignity is even checked).
- **CFG-3** (pāpakartarī on house 7): identical test to marriage's §1.1 — house 6 is empty.
  **Does not fire.**

**No deductions.** Occurrence(separation) = clamp₀¹(0.505000) = **0.505**

### §2.3 — Threshold reading

0.505 falls in **[0.40, 0.60) = MODERATE**: "Roughly half of the class's classical evidence set
is present and aligned. A plausible but not confidently established promise."

**Note for the checkpoint (the exact comparison the master plan names, §4 CFG-1 worked contrast):
separation (0.505, MODERATE) scores HIGHER than marriage (0.321, WEAK) on this chart, computed
from genuinely distinct evidence sets** — the current v2/v3 defect this whole campaign traces back
to was marriage and separation returning the SAME grade from IDENTICAL evidence (`PRATIJNA_ENGINE_
V3_SPEC_v1_0.md` §1). Here the two scores differ by construction (different karakas — Venus vs.
Saturn/Ketu — different divisional dignity, and separation carries a real, non-trivial dusthana
term marriage structurally cannot have at all), not by a special-cased rule forcing them apart.

### §2.4 — Condition

`condition_malefic_grahas=[Mars,Rahu]`, target = house 7 / its lord Venus (house 9).

| Malefic | Position | Relationship | Contribution |
|---|---|---|---|
| Mars | House 7 | **Conjunct the core house itself** | **1.00** |
| Rahu | House 2 | Same computation as §1.4: 8th-from-2 = house 9 = Venus's house — general 4th/8th aspect | **0.75** |

condition(separation) = clamp₀,₁₀( 10 × (1.00+0.75)/2 ) = 10 × 0.875 = **8.75**

**Threshold reading:** 8.75 falls in **[8,10] = CRITICAL**: "Maximal affliction from this rubric's
cited malefic set; this domain is likely to manifest with serious difficulty independent of
whether it occurs at all."

### §2.5 — Separation summary

**Occurrence = 0.505 (MODERATE) · Condition = 8.75 (CRITICAL affliction)**

---

## §3 — CHILDBIRTH

**KaryatvaMap**: `primary_bhava=[5]`, `karaka_grahas=[Jupiter]`, `divisional=D7`, `yoga_keywords=
[putra,santana]`, `condition_malefic_grahas=[Saturn,Rahu]`. Citations: BPHS ch.16, ch.28, ch.6.

**Weights** (4-slot renormalized): 5L=0.500000, Jupiter(karaka)=0.285714, divisional=0.142857,
yoga=0.071429.

### §3.1 — Occurrence

| Slot | Weight | Band | Contribution |
|---|---|---|---|
| 5L = Sun @ D1 | 0.500000 | 0.50 (neutral, §0.3) | 0.250000 |
| Karaka: Jupiter @ D1 | 0.285714 | 0.90 (mūlatrikoṇa, §0.3) | 0.257143 |
| Divisional: Jupiter @ D7 | 0.142857 | 0.60 (friend, §0.3) | 0.085714 |
| Yoga | 0.071429 | 0.00 — `putra` has a real live counterpart (`karaka_chara_position` `PUTRAKARAKA`, 70 rows + `saham_position`, 40 rows) but, per the same §1.3 finding, neither is a `ganita_yoga_firings_get` match; `santana` has no live counterpart at all (dispositioned as redundant by the Coverage Matrix). Same honest gap as marriage/separation — applied consistently, not re-litigated per class. | 0.000000 |
| **Sum (pre-denial)** | | | **0.592857** |

**Denial configurations checked:**
- **CFG-1** (5L + karaka both debilitated): 5L=Sun(0.50), karaka=Jupiter(0.90) — neither
  debilitated. **Does not fire.**
- **CFG-3** (pāpakartarī on house 5 — malefics in house 4 AND house 6): **both house 4 and house 6
  are empty** (§0.2, live-verified) — neither side has a malefic, or anything at all. **Does not
  fire.**
- CFG-2 is N/A (childbirth is not `dusthana_required`).

**No deductions.** Occurrence(childbirth) = clamp₀¹(0.592857) = **0.593**

### §3.2 — Threshold reading

0.593 falls in **[0.40, 0.60) = MODERATE** — 0.007 below the STRONG threshold (0.60). "Roughly
half of the class's classical evidence set is present and aligned. A plausible but not confidently
established promise" is the letter of the band, though the margin to STRONG is narrow enough to be
worth the checkpoint's attention (a single stronger divisional reading, e.g. if Jupiter's D7
dignity had been "great friend" 0.70 instead of "friend" 0.60, would have crossed it: 0.500+0.257+
0.100+0=0.857... actually let's not speculate further — this is exactly the kind of counterfactual
R13 forbids reasoning from toward a conclusion; noted only as a literal margin observation).

### §3.3 — Condition

`condition_malefic_grahas=[Saturn,Rahu]`, target = house 5 / its lord Sun (house 10).

| Malefic | Position | Relationship | Contribution |
|---|---|---|---|
| Saturn | House 7 | To house 5: tested special (3rd/10th-from-7 = house 9/house 4) and general aspects — no match to house 5. To Sun (house 10): 4th-from-7 = house 10 — general 4th/8th aspect (Saturn's SPECIAL aspects are 3rd/10th, not 4th, so this is the general-table entry) | **0.75** |
| Rahu | House 2 | To house 5: 4th-from-2 = house 5 — general 4th/8th aspect. To Sun (house 10): 9th-from-2 = house 10 — general 5th/9th aspect (weaker, 0.50) | **0.75** (stronger of the two) |

condition(childbirth) = clamp₀,₁₀( 10 × (0.75+0.75)/2 ) = 10 × 0.75 = **7.50**

**Threshold reading:** 7.50 falls in **[6,8) = SEVERE**: "Heavy affliction; substantial obstacles
or hardship color this domain."

### §3.4 — Childbirth summary

**Occurrence = 0.593 (MODERATE, near STRONG) · Condition = 7.50 (SEVERE affliction)**

---

## §4 — Cross-class summary table

| Class | Occurrence | Band | Condition | Band | Denials fired |
|---|---|---|---|---|---|
| Marriage | 0.321 | WEAK | 5.83 | MODERATE | none |
| Separation | 0.505 | MODERATE | 8.75 | CRITICAL | none |
| Childbirth | 0.593 | MODERATE (near STRONG) | 7.50 | SEVERE | none |

**R12 property directly demonstrated**: every occurrence/condition pair is independently nonzero
and the two axes clearly diverge in relative ordering (marriage has the lowest occurrence but a
*higher* condition than nothing; separation has both the highest occurrence among these three AND
the highest condition) — occurrence and condition are not collapsing to a single scalar or moving
in lockstep, which is exactly the structural independence R12/R18 require and the old v3 engine's
`condition_grade≡0` defect could never produce.

**Context for the checkpoint (R13: reported, not used to derive anything above) — the native's
recorded life events** (`SIDDHANTA_STATE.md`'s R15 scoring event set): married 2013-12-11;
separated 2026-04-17; twin daughters born 2022-01-03. All three events occurred. This rubric scores
marriage WEAK, separation MODERATE, and childbirth MODERATE-near-STRONG — none DENIED, all three
in the "plausible-to-moderate" range rather than "very strong," which is itself a fair question for
the checkpoint to weigh against the old v3 defect (marriage/separation identically DENIED at grade
1.169) this campaign exists to fix. Whether MODERATE/WEAK readings for three events that did happen
represent "the rubric is appropriately conservative" or "the rubric under-credits confirmed
classical evidence" is precisely the kind of question this checkpoint is for — not resolved here.

---

## §5 — What this probe could NOT hand-work from live facts (honest, not improvised)

Per the task's own instruction: "If any factor cannot be hand-worked from live facts, that is a
matrix gap to record, not a reason to improvise." One real gap surfaced, applied consistently
across all three classes rather than special-cased per class:

- **The yoga-presence slot** (§2.5 of the rubric) is defined against the `ganita_yogas_get`/
  `ganita_yoga_firings_get` system specifically. None of the six `yoga_keywords` across these three
  classes (`darakaraka`, `upapada`, `kalatra`, `kuja_dosha`, `manglik`, `6L-7L`, `putra`, `santana`
  — nine listed, some overlapping in disposition) resolved to an actual yoga catalog/firing match
  on this chart, even though several have real, on-topic, non-empty evidence in OTHER fact systems
  (Jaimini karakas, upapada lagna, dosha labels). Scored 0.00 (the strict, defensible reading) for
  all three classes rather than inventing a broader match rule not in the spec — see §1.3 for the
  full reasoning and the Campaign B recommendation.

No other factor across the three classes lacked a live, retrievable answer — every dignity band,
every house-occupancy check, every dusthana-connection test, and every aspect-contribution
computation above was answered from a real query result, cited inline.

---

*End of RUNG_P3_HAND_WORKED_v1_0.md. This document, alongside `A8_FACTOR_FACT_COVERAGE_MATRIX_
v1_0.md` and `V4_RUBRIC_SPEC_v0_9.md`, is the complete Lane A8 / Rung P3 deliverable for the
human+Fable checkpoint (MASTER_PLAN_v1_0.md §4). No engine code was written to produce any number
in this document.*

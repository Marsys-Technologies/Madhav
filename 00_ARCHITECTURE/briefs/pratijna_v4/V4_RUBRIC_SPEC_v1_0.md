---
title: "PRATIJÑĀ v4 — Bounded Rubric Scoring Specification"
canonical_id: V4_RUBRIC_SPEC
version: 1.0
status: RATIFIED
date: 2026-08-08
ratified_at: 2026-08-08 human+Fable checkpoint (ratified AS-IS from v0.9; content byte-identical
  except this frontmatter)
campaign: ADHIṢṬHĀNA, Lane A8 item 2 (checkpoint artifact 2 of 2); ratified under PRATIJÑĀ v4
  Campaign B, CHECKPOINT_RECORD_v1_0.md Decision 1
author: Conductor (Sonnet 5), dispatched research/writing agent, document-only
rulings_governed: R11, R12, R13, R18, R20, R21
supersedes: V4_RUBRIC_SPEC_v0_9.md (00_ARCHITECTURE/briefs/adhisthana/), unchanged content
implements_nothing: this document specifies; it contains no engine code and authorizes none.
  Campaign B (PRATIJÑĀ v4 engine) implements it starting Lane B0.
---

# PRATIJÑĀ v4 — Bounded Rubric Scoring Specification (DRAFT v0.9)

## 0. Purpose, scope, and how to read this document

This is the rubric Campaign B's engine (Lane B2) implements. It is **not** the engine, the
Chart Reader (Lane B1), or the signal-matching algorithm — those are Campaign B's job, and nothing
in this document authorizes writing them. This document answers exactly four questions, in this
order, per the ADHIṢṬHĀNA Master Plan §3 Lane A8 item 2:

1. What [0,1] score does each factor TYPE receive, for a given classical state, and why
   (§2 — bands)?
2. How much does each factor type count toward each of the 27 event classes' occurrence score,
   and why do the weights sum to exactly 1.0 (§3 — weights)?
3. Under what named classical configurations is occurrence DENIED outright, and by how much,
   regardless of the positive score (§4 — denials)?
4. What do the two output numbers (occurrence, condition) actually mean in plain language, stated
   BEFORE any chart is scored against them (§5 — formulas; §6 — thresholds)?

**Hard constraints this document satisfies (non-negotiable, MASTER_PLAN_v1_0.md §1):**

- **R18 — Bounded rubric scoring.** Every grade in this spec is `Σ(weight × band)` with weights
  summing to exactly 1.0 per class and every band in [0,1] from a cited classical source. No sum
  accumulates without a ceiling; no threshold is derived from looking at a score distribution —
  every threshold in §6 is stated as a plain-language a-priori claim about what fraction of
  classical evidence is present, decided before this spec has been run against any chart's facts.
- **R13 — no fitting, absolute.** This document was written **without querying any of
  chart `482012f1`'s facts, signals, or outcomes** — no `chart_facts`, `bodha_msr_signals`, or LEL
  data for the native was read while writing §2–§6. Every number here is either (a) a direct
  citation from `reference_planets`, `brahma_event_ontology.signature_model`, or the existing
  `bo_pratijna_karyatva.py` `KaryatvaMap` registry, (b) a well-established classical doctrine
  named without a chart-specific application, or (c) a mechanically-derived consequence of (a)/(b)
  applied by ONE general rule to all 27 classes uniformly — never a per-class discretionary pick.
  §8 flags the specific places this document's author had to exercise judgment rather than pure
  extraction, honestly, for the checkpoint to weigh.

**Grounding sources actually used (live-verified 2026-08-08):**

| Source | What it supplied |
|---|---|
| `platform/python-sidecar/pipeline/orchestrator/writers/bo_pratijna_karyatva.py` | The 26-class `KaryatvaMap` registry (primary_bhava, karaka_grahas, dusthana_required, divisional, yoga_keywords, condition_malefic_grahas, citations) — the factor list this rubric scores. **26, not 27** — see §7. |
| `reference_planets` (live DB, 11 rows) | `exaltation_sign`, `debilitation_sign`, `mooltrikona_sign`, `own_signs[]`, `natural_benefic`, `source_citation` per planet — the dignity-band source (§2.1). |
| `brahma_event_ontology.signature_model` (live DB, 27 rows) | Cross-reference for weight justification and the one class (`parental_event`) missing from the karyatva registry (§7). |
| `00_ARCHITECTURE/briefs/pratijna_satya/PRATIJNA_ENGINE_V3_SPEC_v1_0.md` | The prior spec draft the Master Plan's grounding table (§2) says is "carried into B1 spec v2." Found and read in full (it exists at that exact path — earlier repo-wide greps that missed it were searching the wrong scope). Its classical citations, factor typology, and two-judgment (occurrence/condition) architecture are reused and tightened here; its **uniform, unbounded weights (karaka=1.0, divisional=0.8, no ceiling)** are the exact R18 violation this v0.9 spec corrects — see §8. |
| `platform/python-sidecar/ga_writers/ga_condition_writer.py` (`DIGNITY_SCORES`, lines 52–63) and `ga_vargas_writer.py` (`dignity_factor`/`dignity_scores`, lines ~1544/~1895) | The dignity-to-[0,1] band this spec adopts (§2.1) is **not invented for this document** — it is the pre-existing, already-live, generically-applied L1 `condition_score`/`vimsopaka` dignity scale, promoted here rather than re-derived, per the "adoption over addition" spirit of R17. |
| `ADHISTHANA_STATE.md` Rung P2 output (2026-08-08, live) | Confirms `chart_divisionals` (not `chart_facts`) is where base graha/varga/house positional data lives, and confirms the "dignity of a graha in a given varga" cross-check (VEN/D9 dignity) is a live-computable quantity — precedent this spec's divisional-band design (§2.4) relies on. |

---

## 1. Design overview (read this before the tables)

The rubric scores each of the 27 event classes on **two independent axes** (R12):

- **Occurrence** — will the chart's classical evidence support this event happening at all?
  `occurrence = clamp₀¹( Σᵢ (weightᵢ × bandᵢ) − denial_deductions )`, weights summing to 1.0
  per class (§3), bands from §2, denials from §4.
- **Condition** — independent of whether it happens, how afflicted is the configuration?
  `condition ∈ [0,10]`, driven only by `condition_malefic_grahas` aspect/conjunction magnitude
  (§5.2) — a **disjoint** input set from occurrence's dignity-based factors, so an afflicted-but-
  present house structurally CANNOT collapse both axes to the same reading.

Every event class's occurrence rubric is built from up to **five factor SLOTS**, each with one
fixed base weight used identically across all 27 classes (§3.1), applied mechanically to
whichever slots that class's own `KaryatvaMap` populates. No class's slot weights were chosen by
looking at that class individually — the slot base-weight table is decided once, in §3.1, and
every class's final numbers are a pure arithmetic consequence of which slots its own registry
entry happens to have.

---

## 2. Factor bands (§ per factor TYPE)

All bands are [0,1] except where noted (condition-side bands feed the separate [0,10] scale,
§5.2). Every band below is either a direct classical dignity ladder or a documented,
well-established classical doctrine.

### 2.1 Dignity band (the shared primitive)

Four of the five occurrence slots (`bhava_lord`, `karaka`, `divisional`, and — indirectly, via
its own graha's placement — the affliction test inside `dusthana`) are scored through the SAME
underlying dignity ladder, evaluated against a different graha/chart depending on the slot. This
is deliberate: BPHS's dignity hierarchy (uccha/mūlatrikoṇa/svakṣetra → adhi-mitra/mitra/sama →
śatru/adhi-śatru → nīca) is a single ordered classical scale; reusing one band for every
"how strong is this planet here" question, rather than inventing a new scale per question, is
itself an R13 discipline — one number system, cited once, applied everywhere.

**Band table** (adopted verbatim from the live, already-in-production `DIGNITY_SCORES` constant
in `ga_condition_writer.py:52-63`, itself citing BPHS ch.3 grahasvarūpa + the pañcadhā maitri
five-fold relationship doctrine):

| Dignity state | Band | Classical test (against `reference_planets`) |
|---|---|---|
| Exalted (uccha) | **1.00** | sign = `reference_planets.exaltation_sign` |
| Mūlatrikoṇa | **0.90** | sign = `reference_planets.mooltrikona_sign` (and, where a degree range is tracked elsewhere in L1, within that range) |
| Own sign (svakṣetra) | **0.80** | sign ∈ `reference_planets.own_signs[]` |
| Great friend (adhi-mitra) | **0.70** | sign lord is in the "great friend" tier of the classical pañcadhā maitri (naisargika + tātkālika compounding) relative to the graha being scored |
| Friend (mitra) | **0.60** | sign lord is a naisargika friend (BPHS ch.3's fixed friend/enemy table, e.g. Sun↔Moon/Mars/Jupiter = friend) |
| Neutral (sama) | **0.50** | sign lord is neither a cited friend nor enemy, or the graha rules its own sign's lord (self) |
| Enemy (śatru) | **0.30** | sign lord is a naisargika enemy |
| Great enemy (adhi-śatru) | **0.20** | sign lord is in the "great enemy" compounded tier |
| Debilitated (nīca) | **0.00** | sign = `reference_planets.debilitation_sign` |

**Spacing justification (why these numbers, not others):** the nine states are a strictly ordered
classical scale (this ordering itself is the citation — no BPHS-based text disputes that exalted
> mūlatrikoṇa > own > friend-tiers > neutral > enemy-tiers > debilitated). Two design choices were
made to turn an ORDER into a SPACING, both already made once, in the codebase, for an unrelated L1
purpose (vimsopaka bala), and adopted here rather than re-derived: (a) exalted/debilitated anchor
the [0,1] extremes since they are definitionally a graha's strongest and weakest classical states;
(b) the seven intermediate states are spaced at 0.10 intervals with mūlatrikoṇa (0.90) placed
just below exalted per its classical treatment as "exaltation-adjacent" (a mūlatrikoṇa placement is
frequently described in BPHS as functionally close to exaltation strength) and neutral anchored at
the exact midpoint (0.50) as the state with no directional pull either way. This spacing is a
judgment call about STEP SIZE within an undisputed ORDER — flagged honestly in §8, not hidden;
what is not a judgment call is the order itself or the extremes.

**Note on `reference_planets`'s friend/enemy gap:** the live table carries exaltation/
debilitation/mūlatrikoṇa/own-sign columns but no friendship matrix. The naisargika (natural)
friend/enemy table is a second, equally fixed classical constant (BPHS ch.3) — already present
verbatim in `ga_condition_writer.py`'s `_NAISARGIKA` dict (lines ~220–239) for all 7 classical
grahas. This spec cites that table by reference rather than re-transcribing it; Campaign B's
Reader (B1) should read it from there, not re-type it a fourth time (the codebase's own count of
independent graha-relationship maps is exactly the kind of proliferation ADHIṢṬHĀNA Lane A2 spent
effort collapsing — a new copy here would be a fresh instance of the defect this campaign is
fixing elsewhere).

**Rāhu/Ketu:** `reference_planets` carries exaltation/debilitation for both nodes (Rāhu: exalt
Taurus/debil Scorpio; Ketu: exalt Scorpio/debil Taurus — the table's own `source_citation` flags
this as the debated-but-mainstream Parashari convention, "L0 sealed 2026-06-24" per
`ga_vargas_writer.py`). Neither node has an own sign, mūlatrikoṇa, or a friend/enemy entry in the
classical naisargika table (nodes are shadow points, not physical planets, in most BPHS-derived
friendship doctrine) — for `karaka_grahas` entries that are Rāhu or Ketu (separation, relocation,
foreign_settlement, spiritual_turn, financial_deception, travel_event), the band collapses to
three reachable states only: exalted (1.00) / debilitated (0.00) / neutral (0.50, the default for
every other sign). This is an honest scale restriction, not a new number.

### 2.2 House-lord strength band

= the dignity band (§2.1) of the sign-lord of the class's cited house, evaluated in **D1**
(rāśi). "Sign-lord of house N" is resolved by classical whole-sign lordship (the ruling planet of
house N's occupied sign) — the same resolution method Rung P2 already validated live against
`chart_divisionals`+cusp-longitude for chart `482012f1`/`1c826d5a` (ADHISTHANA_STATE.md, Rung P2
output). This band answers "does the house have a structurally capable steward," independent of
that steward's placement (placement quality is captured separately, if at all, by the denial
configurations in §4 — this rubric does not double-count a lord's own house-placement as a second
occurrence factor).

### 2.3 Karaka strength band

= the dignity band (§2.1) of the class's cited `karaka_grahas` entry, evaluated in **D1**. Where a
class lists more than one karaka (e.g. marriage: Venus, Jupiter), each karaka is scored
independently and the karaka SLOT weight (§3) is split evenly across them — no classical citation
in the existing registry ranks one listed karaka above another for the same class, so equal
division is the only claim this document can defend (see §8 on this choice).

### 2.4 Divisional-chart placement band

= the dignity band (§2.1) of the class's **primary** (first-listed) karaka, evaluated against
its sign placement **within the class's cited `divisional` varga** (e.g. for marriage, Venus's D9
sign; for childbirth, Jupiter's D7 sign). Reading dignity against a varga sign rather than the D1
sign is the standard classical use of vargas as confirmatory instruments (BPHS ch.6) — and is
exactly the computation Rung P2 already proved live-feasible and internally consistent (Venus/D9
dignity cross-checked between the Fact Identity Index and `chart_divisionals` on `482012f1`,
matching case-for-case; ADHISTHANA_STATE.md Rung P2). Classes with `divisional = None`
(the 5 DR-13 provisional classes) do not carry this slot at all (§3.2) — no band is invented for a
varga the registry itself does not cite.

### 2.5 Yoga/keyword presence band (3-tier)

| State | Band | Basis |
|---|---|---|
| No match | **0.00** | none of the class's `yoga_keywords` correspond to any yoga touching this chart |
| Catalog-only match | **0.50** | a yoga matching one of the class's keywords exists in `ganita_yogas_get`'s catalog but has not cleared cross-verification (the `fire_reason: 'requires_pass'` tier already defined by the platform's own Serving Density Principle, `CLAUDE.md` §N.6 item 1) |
| Confirmed firing | **1.00** | a yoga matching one of the class's keywords appears in `ganita_yoga_firings_get`'s firings-authoritative surface |

This is not an invented three-way split: it is the codebase's own already-ratified distinction
between catalog-label matches and cross-verified firings (§N.6), applied here as the classical
"is this yoga actually formed, or only nominally present" test — a yoga's classical definition
requires its full stated combination to be present, so an unconfirmed catalog match earns partial,
not full, credit. A class's several `yoga_keywords` are evaluated as ONE test (best match wins,
not summed) — a class with three keyword synonyms should not out-score a class with one just for
having more names for the same classical concept.

### 2.6 Dusthana involvement band (dusthana-required classes only)

Applies only to the three classes with `dusthana_required = True` (separation, career_setback,
major_loss — §3.2). Band = (count of the class's own cited dusthana houses, from its
`primary_bhava` list beyond the first/core house, showing a structural connection to the core
house or its lord) ÷ (total dusthana houses cited for that class). "Structural connection," tested
per dusthana house, counted once regardless of how many connection types apply to that house:

- the core house's lord is placed IN that dusthana house, OR
- that dusthana house's lord aspects (classical drishti, §2.7) or conjoins the core house or its
  lord, OR
- a classical exchange (parivartana) exists between the core house's lord and that dusthana
  house's lord — the exact "6L-7L exchange" the separation class's own `yoga_keywords` already
  names.

This is the classical dusthana doctrine (BPHS ch.12) each of the three classes already cites in
its own `KaryatvaMap.citations` — it is not a new rule, only a formalization of what "dusthana
involvement" (the flag these three classes already carry) computationally means.

### 2.7 Aspect-from-malefic/benefic band (condition-side; feeds §5.2, not occurrence)

Classical graha-dṛṣṭi (planetary aspect) fractional strength — every planet aspects the 7th house
from itself at full strength; all planets carry additional partial aspects at fixed fractions; Mars,
Jupiter, and Saturn carry additional named FULL-strength special aspects. This fractional-aspect
doctrine (often called "rāśi dṛṣṭi with pada strength") is stated identically across BPHS-lineage
texts; this document cites it by the doctrine's name rather than a specific chapter/verse number it
cannot independently verify against a primary text (flagged in §8, not asserted with false
precision).

| Relationship to the target house | Contribution |
|---|---|
| Conjunction (occupies the house) | **1.00** |
| 7th-house aspect (every graha) | **1.00** |
| Special full aspect — Mars→4th/8th, Jupiter→5th/9th, Saturn→3rd/10th | **1.00** |
| General 4th/8th aspect (non-special-planet) | **0.75** |
| General 5th/9th aspect (non-special-planet) | **0.50** |
| General 3rd/10th aspect (non-special-planet) | **0.25** |
| No aspect, no conjunction | **0.00** |

---

## 3. Per-class weights (all 27 classes, weights summing to exactly 1.0)

### 3.1 The universal base-weight table (decided once, applied to all 27 classes)

| Slot | Base weight | A-priori justification (stated before any class is scored) |
|---|---|---|
| `bhava_lord` | **0.35** | BPHS's house-lord-primacy principle: a house's promise cannot manifest without functional force in its own lord — the single most decisive factor, ranked first across every class, positive or negative. |
| `dusthana_involvement` | **0.30** | Applies only where the class's own registry entry already flags `dusthana_required = True`. For exactly those three classes, dusthana connection IS the registry's own stated reason the class is structurally distinct from its positive counterpart (e.g. separation from marriage) — ranked second, just below the lord's own dignity, because dusthana involvement describes a RELATIONSHIP to the primary house that presupposes the house/lord already exist as the anchor being afflicted. |
| `karaka` | **0.20** | BPHS ch.28 karakatva doctrine: the natural significator is independent corroborating evidence — classically secondary to the house-and-lord system itself, which BPHS treats as primary (houses signify, karakas corroborate). |
| `divisional` | **0.10** | BPHS ch.6: varga charts REFINE an already-indicated D1 promise — confirmatory, not establishing. |
| `yoga_keyword` | **0.05** | Named yogas/combinations are classically treated as amplifiers of an existing promise, not primary establishers — the lightest corroborating signal in this rubric. |

Sum of all five (the hypothetical class using every slot) = 0.35+0.30+0.20+0.10+0.05 = **1.00
exactly** — this is why the three dusthana-required classes (§3.2, 5-slot) need no renormalization
at all. Every other class uses a strict SUBSET of these five slots (whichever its own
`KaryatvaMap` populates); that subset's base weights are renormalized to sum to 1.0 by dividing
each by the subset's own total. This is the ONE mechanical rule applied to all 27 classes —
no class's weights were picked by looking at that class in isolation.

**Within-slot splitting rule:** when a class's `primary_bhava` (for the `bhava_lord` slot) or
`karaka_grahas` (for the `karaka` slot) lists more than one item, that slot's weight is divided
EQUALLY across the listed items. No citation in the existing registry ranks one listed house or
karaka above another for the same class — equal division is the only defensible default absent
such a citation (flagged in §8). For the three dusthana-required classes, the FIRST-listed house
in `primary_bhava` is the class's core house (`bhava_lord` slot, single item, matches that class's
primary citation ordering — e.g. separation's citations list "BPHS ch.19 (vivaha-vicara)" before
"BPHS ch.12 (dusthana)"); the REMAINING listed houses are that class's own cited dusthana houses
(`dusthana_involvement` slot, split equally across however many the class cites — 3 for
separation, 2 for career_setback, 1 for major_loss, matching each class's own citation scope).

### 3.2 Full 27-class weight table (verified by exact rational arithmetic, not float rounding)

Computed by the script in §3.3; every row's rightmost column was independently re-summed by the
script as `Fraction` objects (exact rational arithmetic, no floating-point drift) and every one of
the 27 rows returned `exact == 1`.

**4-slot classes (bhava_lord + karaka + divisional + yoga; base subtotal 0.70 → ×10/7 renormalization) — 19 classes:**

| Class | House-lord weight(s) | Karaka weight(s) | Divisional | Yoga | Sum |
|---|---|---|---|---|---|
| marriage | 7L = 0.500000 | Venus 0.142857, Jupiter 0.142857 | 0.142857 | 0.071429 | 1.000000 |
| childbirth | 5L = 0.500000 | Jupiter 0.285714 | 0.142857 | 0.071429 | 1.000000 |
| surgery | 6L 0.250000, 8L 0.250000 | Mars 0.285714 | 0.142857 | 0.071429 | 1.000000 |
| relocation | 4L 0.250000, 12L 0.250000 | Moon 0.142857, Rahu 0.142857 | 0.142857 | 0.071429 | 1.000000 |
| foreign_settlement | 12L 0.166667, 9L 0.166667, 7L 0.166667 | Rahu 0.285714 | 0.142857 | 0.071429 | 1.000000 |
| romantic_start | 5L 0.250000, 7L 0.250000 | Venus 0.285714 | 0.142857 | 0.071429 | 1.000000 |
| career_entry | 10L = 0.500000 | Sun 0.142857, Saturn 0.142857 | 0.142857 | 0.071429 | 1.000000 |
| career_change | 10L = 0.500000 | Sun 0.142857, Saturn 0.142857 | 0.142857 | 0.071429 | 1.000000 |
| career_advancement | 10L 0.250000, 11L 0.250000 | Sun 0.142857, Jupiter 0.142857 | 0.142857 | 0.071429 | 1.000000 |
| business_launch | 7L 0.166667, 10L 0.166667, 11L 0.166667 | Mercury 0.142857, Jupiter 0.142857 | 0.142857 | 0.071429 | 1.000000 |
| education_milestone | 4L 0.166667, 5L 0.166667, 9L 0.166667 | Mercury 0.142857, Jupiter 0.142857 | 0.142857 | 0.071429 | 1.000000 |
| exam_outcome | 4L 0.250000, 5L 0.250000 | Mercury 0.142857, Jupiter 0.142857 | 0.142857 | 0.071429 | 1.000000 |
| illness_acute | 6L = 0.500000 | Mars 0.285714 | 0.142857 | 0.071429 | 1.000000 |
| chronic_onset | 6L 0.250000, 8L 0.250000 | Saturn 0.285714 | 0.142857 | 0.071429 | 1.000000 |
| major_gain | 2L 0.250000, 11L 0.250000 | Jupiter 0.142857, Mercury 0.142857 | 0.142857 | 0.071429 | 1.000000 |
| property_acquisition | 4L = 0.500000 | Mars 0.142857, Venus 0.142857 | 0.142857 | 0.071429 | 1.000000 |
| bereavement | 4L 0.166667, 9L 0.166667, 8L 0.166667 | Moon 0.095238, Sun 0.095238, Saturn 0.095238 | 0.142857 | 0.071429 | 1.000000 |
| spiritual_turn | 9L 0.166667, 12L 0.166667, 5L 0.166667 | Jupiter 0.142857, Ketu 0.142857 | 0.142857 | 0.071429 | 1.000000 |
| parental_event† | 4L 0.250000, 9L 0.250000 | Moon 0.142857, Sun 0.142857 | 0.142857 | 0.071429 | 1.000000 |

† authored for this spec — see §7, not extracted from `KaryatvaMap` (which is missing this class).

**5-slot classes (bhava_lord + dusthana + karaka + divisional + yoga; base subtotal already 1.00, no renormalization) — 3 classes:**

| Class | House-lord | Dusthana houses | Karaka(s) | Divisional | Yoga | Sum |
|---|---|---|---|---|---|---|
| separation | 7L = 0.35 | 6th 0.10, 8th 0.10, 12th 0.10 | Saturn 0.10, Ketu 0.10 | 0.10 | 0.05 | 1.00 |
| career_setback | 10L = 0.35 | 6th 0.15, 8th 0.15 | Saturn = 0.20 | 0.10 | 0.05 | 1.00 |
| major_loss | 2L = 0.35 | 12th = 0.30 | Saturn = 0.20 | 0.10 | 0.05 | 1.00 |

**2-slot classes — DR-13 provisional (bhava_lord + karaka only; base subtotal 0.55 → ×20/11 renormalization) — 5 classes:**

| Class | House-lord weight(s) | Karaka weight(s) | Sum |
|---|---|---|---|
| achievement_recognition | 10L 0.318182, 11L 0.318182 | Sun 0.181818, Jupiter 0.181818 | 1.000000 |
| financial_deception | 8L 0.318182, 12L 0.318182 | Rahu = 0.363636 | 1.000000 |
| psychological_arc | 5L 0.212121, 8L 0.212121, 12L 0.212121 | Moon 0.181818, Ketu 0.181818 | 1.000000 |
| birth_anchor | 1L = 0.636364 | Sun = 0.363636 | 1.000000 |
| travel_event | 3L 0.212121, 9L 0.212121, 12L 0.212121 | Moon 0.181818, Rahu 0.181818 | 1.000000 |

**No divisional or yoga slot exists for the provisional 5** — their `KaryatvaMap.divisional` is
`None` and `yoga_keywords` is empty (§7's `provisional: true` marker), so per §3.1's own rule
those slots are absent from the renormalization base, not zero-weighted placeholders.

### 3.3 Verification method

The table above was generated and checked by a standalone script using Python's `fractions.Fraction`
(exact rational arithmetic — no floating-point rounding could hide a sum ≠ 1), asserting `sum(weights)
== Fraction(1)` per class. **Result: 27/27 classes exact.** The script (base-weight table, slot
population per class, splitting rule, and the assertion) is reproduced here in full so Campaign B
can re-run it as a regression check before wiring these numbers into the writer:

```python
from fractions import Fraction as F

BASE = {"bhava_lord": F(35,100), "dusthana": F(30,100), "karaka": F(20,100),
        "divisional": F(10,100), "yoga": F(5,100)}

# name: (primary_bhava houses, karaka_grahas, has_divisional, has_yoga, dusthana_houses|None)
# dusthana_houses is the tail of primary_bhava (all but the first element) for the 3
# dusthana_required=True classes; None otherwise, matching KARYATVA_REGISTRY exactly (+parental_event, §7).
CLASSES = { ... }  # 27 entries, see §3.2 tables for the full enumeration

def compute(houses, karakas, has_div, has_yoga, dusthana):
    slots = {"bhava_lord": BASE["bhava_lord"], "karaka": BASE["karaka"]}
    if has_div: slots["divisional"] = BASE["divisional"]
    if has_yoga: slots["yoga"] = BASE["yoga"]
    if dusthana is not None: slots["dusthana"] = BASE["dusthana"]
    norm = {k: v / sum(slots.values()) for k, v in slots.items()}
    out = {}
    for h in houses: out[f"house_lord_{h}"] = norm["bhava_lord"] / len(houses)
    for k in karakas: out[f"karaka_{k}"] = norm["karaka"] / len(karakas)
    if has_div: out["divisional"] = norm["divisional"]
    if has_yoga: out["yoga"] = norm["yoga"]
    if dusthana is not None:
        for d in dusthana: out[f"dusthana_{d}"] = norm["dusthana"] / len(dusthana)
    return out

for name, args in CLASSES.items():
    out = compute(*args)
    assert sum(out.values()) == F(1), f"{name} FAILED: {sum(out.values())}"
print("27/27 classes exact.")
```

---

## 4. Denial configurations (occurrence-side; independent of the positive weighted sum)

Per R18/the master plan, denial must be earned by NAMED classical configurations, never by raw
affliction volume. Three configurations, each defined once and applied identically to every class
its structure fits — no per-class discretionary denial rule was written.

**Deduction-sizing rule (mechanical, not picked per class):** each configuration's deduction
equals the sum of the exact slot weight(s) (from §3.2, that class's own computed table) that the
configuration classically falsifies. This keeps deductions non-arbitrary and auditable: a
configuration that breaks two structural pillars removes exactly those two pillars' weight, no
more, no less — never a flat, unexplained penalty constant.

### DENIAL-CFG-1 — Compound uncancelled double debilitation (applies to all 27 classes)

**Fires when:** the class's PRIMARY (first-listed) house-lord AND its PRIMARY (first-listed)
karaka are BOTH in classical debilitation (§2.1's 0.00 band — sign = `debilitation_sign`) with no
neecha-bhaṅga (cancellation) present. Neecha-bhaṅga test (classical, standard): the debilitated
graha's dispositor (the lord of the sign it occupies) is itself angular (kendra, houses 1/4/7/10)
from the lagna or from the Moon.

**Deduction:** `weight(primary house-lord item) + weight(primary karaka item)` for that class —
read directly from §3.2's tables. E.g. marriage: 0.500000 + 0.142857 = **0.642857**; birth_anchor
(2-slot): 0.636364 + 0.363636 = **1.000000** (the entire score, since a 2-slot class's only two
factors ARE its lord and karaka).

**Citation:** BPHS ch.3 (nīca as the graha's weakest capacity to signify) + the standard
neecha-bhaṅga dispositor-in-kendra cancellation test, stated identically across BPHS-lineage
commentary.

**Worked contrast (marriage vs separation, the exact case the master plan names as the checkpoint
question):** marriage's DENIAL-CFG-1 tests 7L + Venus; separation's tests 7L + Saturn (its primary
karaka is Saturn, listed first in `karaka_grahas=["Saturn","Ketu"]`). The two classes can and will
disagree on whether this configuration fires for the same chart, because they test different
karakas — this is the structural distinctness the domain-matching v2/v3 defect (that produced
IDENTICAL grades for marriage/separation/romantic_start, PRATIJNA_ENGINE_V3_SPEC_v1_0.md §1) is
designed to prevent by construction, not by a special-cased rule.

### DENIAL-CFG-2 — Lord in dusthana, uncancelled (dusthana-required classes only: separation, career_setback, major_loss)

**Fires when:** the class's core house-lord OCCUPIES one of that class's own cited dusthana houses
AND is itself debilitated OR combust there, with no neecha-bhaṅga/no benefic (Jupiter, Mercury as
benefic, or Venus) conjunction or aspect reaching it.

**Deduction:** `weight(primary house-lord item) + weight(all dusthana items combined)`. Separation:
0.35 + 0.30 = **0.65**; career_setback: 0.35 + 0.30 = **0.65**; major_loss: 0.35 + 0.30 = **0.65**
(all three land at the same figure because §3.1's base weights are identical across the 5-slot
archetype — a mechanical consequence, not a re-picked number).

**Citation:** BPHS ch.12 (dusthana doctrine — already cited by all three classes' own
`KaryatvaMap.citations`) + the standard combustion doctrine (a combust graha, "burnt" within its
classical orb of the Sun, loses the capacity to deliver its significations).

**Why this is a SEPARATE configuration from CFG-1, not a duplicate:** CFG-1 tests the lord's OWN
sign dignity in isolation; CFG-2 tests the lord's HOUSE PLACEMENT (is it sitting in the very
houses that structurally define this class as a denial-prone class). A lord can fail one without
failing the other — e.g. a dignified-by-sign lord physically sitting in the 8th house still fires
CFG-2 without firing CFG-1.

### DENIAL-CFG-3 — Pāpakartarī yoga on the core house (applies to all 27 classes)

**Fires when:** the class's core (first-listed) house is hemmed by malefics on both adjoining
houses (the 12th-from and 2nd-from the core house both malefic-occupied) with no benefic aspect
reaching the core house or its lord.

**Deduction:** `weight(primary house-lord item)` only — pāpakartarī afflicts the HOUSE's structural
environment specifically, which most directly compromises the reliability of the lord-strength
evidence pillar (a hemmed house's lord, however dignified by sign, sits in a besieged house), so
only that pillar's weight is removed. E.g. marriage: **0.500000**; separation: **0.35**.

**Citation:** classical pāpakartarī yoga (malefic-hemming doctrine), stated by name — not by a
specific chapter/verse this document can independently verify — across BPHS-lineage and
Phaladeepika-lineage texts alike (flagged in §8 alongside §2.7's aspect-fraction citation for the
same reason: doctrine-name citation, not chapter-and-verse citation, where this author cannot
verify the latter against a primary source).

---

## 5. The two formulas (R12, R18)

### 5.1 Occurrence

```
occurrence(class, chart) = clamp[0,1]( Σᵢ weightᵢ · bandᵢ  −  Σ_fired_denials deductionⱼ )
```

- `weightᵢ` — from §3.2 (that class's own table row), summing to 1.0 before any denial.
- `bandᵢ` — from §2.1–§2.6, one band per populated slot/item.
- `deductionⱼ` — from §4, summed over however many of the three configurations actually fire
  (a chart can trigger more than one; deductions accumulate, then the whole expression clamps to
  [0,1] — it never goes negative, and a chart that fires CFG-1 alone on a class where CFG-1's
  deduction already equals or exceeds the max positive sum floors cleanly at 0 without needing a
  special-cased override).
- Maximum un-denied occurrence is exactly 1.0 by construction (§3's weights sum to 1.0, every band
  is ≤1.0) — no class can exceed 1.0 even before considering denials, satisfying R18's "no
  accumulating unbounded sums" clause directly.

### 5.2 Condition

```
condition(class, chart) = clamp[0,10]( 10 × ( Σ_{m ∈ condition_malefic_grahas} contribution(m) ) / |condition_malefic_grahas| )
```

- `contribution(m)` — from §2.7's aspect-fraction table, the STRONGEST single relationship found
  between malefic `m` and the class's core house/lord (conjunction beats aspect; among aspects,
  the strongest fraction found wins — contributions are not summed across multiple aspect types
  from the same malefic, only across DIFFERENT listed malefics).
- **Scale semantics, stated explicitly because the prior v3 spec used the opposite convention and
  this is exactly the kind of silent-flip defect §N.7/§N.8 exist to catch:** 0 = no detectable
  affliction from any of the class's cited malefics (clean); 10 = every cited malefic found in
  full (1.00) contact with the house/lord (maximally afflicted). Condition is an AFFLICTION-
  MAGNITUDE scale, not a favorability scale — higher number = worse, not better. This is the
  deliberate fix the master plan names ("condition = affliction magnitude on its own positive
  [0,10] scale... fixes the structurally-zero defect by design," MASTER_PLAN_v1_0.md §5 Lane B2):
  the old v3 `condition_grade` used a 0–10 FAVORABILITY scale that a genuinely afflicted house
  could only ever push toward zero from a fixed ceiling, structurally biasing it toward the
  low end regardless of real signal; the new scale has no such directional bias because it
  measures the affliction directly, starting from a true zero.
- Condition's only inputs (`condition_malefic_grahas`, aspect fractions) are DISJOINT from
  occurrence's inputs (dignity states of lords/karakas, dusthana connection counts, yoga firing
  tier) for every one of the 27 classes — an afflicted-but-present house therefore yields
  `occurrence > 0 AND condition > 0` by construction, not by a special-cased test (the exact
  property the master plan's B3 property test list requires, MASTER_PLAN_v1_0.md §5 Lane B3).

---

## 6. Threshold semantics — stated a priori, before any chart is scored

**These bands are written blind.** No chart's occurrence score for any class has been computed
against this spec at the time of writing (see the R13 statement in §0). Per the master plan's
own sequencing (§10, Rung P3 comes AFTER this document, and explicitly reviews numbers computed
"from" it, never the reverse), the numeric example computation belongs to Rung P3 and the parallel
Coverage Matrix artifact — not here.

### 6.1 Occurrence bands (equal-width, five bands of 0.20 — no distribution-derived cutoff)

| Range | Label | Plain-language meaning |
|---|---|---|
| [0.00, 0.20) | **DENIED** | Classical evidence for this event's occurrence is largely absent, or has been actively negated by a named denial configuration (§4). At most fragmentary, isolated signals present. |
| [0.20, 0.40) | **WEAK** | A minority of the class's classical evidence set is present. Occurrence is not supported as more-likely-than-not by this rubric. |
| [0.40, 0.60) | **MODERATE** | Roughly half of the class's classical evidence set is present and aligned. A plausible but not confidently established promise. |
| [0.60, 0.80) | **STRONG** | A clear majority of the class's classical evidence set is present and aligned. Occurrence is well-supported. |
| [0.80, 1.00] | **VERY STRONG** | Nearly the complete classical evidence set is present. Occurrence is maximally supported within this rubric's terms. |

Equal 0.20-wide bands were chosen, rather than any narrower or skewed banding, specifically
because R18 forbids deriving band edges from how scores happen to distribute once real charts are
run — five equal bands is the simplest a-priori partition of [0,1] that still distinguishes
"denied" from "weak" (a distinction the master plan's checkpoint questions require: the current
v2/v3 defect is that marriage sits at "denied" for a native who married — this rubric needs at
least a DENIED/not-DENIED boundary that isn't the same as WEAK/MODERATE, hence five bands rather
than three).

### 6.2 Condition bands ([0,10], affliction magnitude — five bands of 2.0)

| Range | Label | Plain-language meaning |
|---|---|---|
| [0, 2) | **CLEAN** | Negligible affliction detected from the class's cited malefics. |
| [2, 4) | **MILD** | Minor affliction present; background-level friction, not a defining feature of this domain. |
| [4, 6) | **MODERATE** | Meaningful affliction; visible friction should be expected in this domain's manifestation. |
| [6, 8) | **SEVERE** | Heavy affliction; substantial obstacles or hardship color this domain. |
| [8, 10] | **CRITICAL** | Maximal affliction from this rubric's cited malefic set; this domain is likely to manifest with serious difficulty independent of whether it occurs at all. |

Same equal-width, stated-in-advance rationale as §6.1 — no chart's condition distribution
influenced these cut points.

---

## 7. The 27th class: `parental_event` is missing from `KaryatvaMap` — authored here, flagged

`brahma_event_ontology` carries **27** `event_class_id` rows (live-verified,
`SELECT count(*) FROM brahma_event_ontology` = 27). `bo_pratijna_karyatva.py`'s
`KARYATVA_REGISTRY` carries **26** (live-verified, `grep -c "event_class_id=" ... .py` = 26). The
missing class is **`parental_event`** (signature_model: lords `["4L","9L"]`, houses `["4","9"]`,
vargas `["D12"]`, karakas `["Moon","Sun"]`, `lel_category: "family"`).

This is not a fresh invention: `PRATIJNA_ENGINE_V3_SPEC_v1_0.md` §2.2 already discusses this class
under a combined heading, **"Bereavement / Parental Event"** (line 139), citing the identical
house/lord/karaka/divisional set this document uses (4/9/8 for bereavement's death-context, 4/9
alone for parental_event's non-death context) — the prior spec simply never split it into its own
`KaryatvaMap` entry. This document does that split, using:

```python
"parental_event": KaryatvaMap(
    event_class_id="parental_event",
    primary_bhava=[4, 9],
    karaka_grahas=["Moon", "Sun"],
    dusthana_required=False,   # non-death parental events; bereavement (death) stays the separate, dusthana-eligible class
    divisional="D12",
    yoga_keywords=["matru", "pitru"],
    condition_malefic_grahas=["Saturn", "Rahu"],
    citations=["BPHS ch.4 (mother)", "BPHS ch.9 (father)", "BPHS ch.6 (dwadashamsha)"],
)
```

`dusthana_required=False` is a judgment call, not a citation: bereavement (death) is the dusthana-
eligible sibling class; a living parent's non-death event (illness, achievement, remarriage, etc.
— the class is deliberately broad per `lel_category: "family"` with no narrower LEL mapping yet)
has no single classical affliction pattern this document can cite as its defining denial-adjacent
structure the way separation/career_setback/major_loss have theirs. Flagged in §8. This makes
`parental_event` a 4-slot class, weighted identically to the other 18 four-slot classes (§3.2
table, row `parental_event`, marked with a dagger).

**Campaign B implication:** whoever wires this rubric into the writer must actually ADD this
`KaryatvaMap` entry to the registry file (a code change, out of scope for this document) before
`parental_event` can be scored at all — until then it has no karyatva map, only this spec's
proposal for one.

---

## 8. Honest R13/judgment-call flags (for the checkpoint, not hidden in §0's summary)

Per instruction, every place this document's author exercised judgment rather than pure citation
extraction is listed here explicitly, so the human+Fable checkpoint can weigh it rather than
discover it later:

1. **Dignity band spacing (§2.1).** The nine-state ORDER is undisputed classical doctrine; the
   specific 0.10-step SPACING and the exact 0.70/0.60/0.50/0.30/0.20 midpoint numbers are adopted
   from `ga_condition_writer.py`'s existing `DIGNITY_SCORES` rather than freshly invented — but
   that constant was itself, at some point, a judgment call by whoever wrote it, and this document
   inherits that call rather than independently re-deriving it from a primary classical source.
   This is the single highest-leverage number in the whole spec (every occurrence factor except
   yoga and dusthana routes through it) and the one most worth the checkpoint's scrutiny.
2. **The five-slot base-weight table (§3.1): 0.35/0.30/0.20/0.10/0.05.** The ORDERING
   (bhava_lord > dusthana > karaka > divisional > yoga) is defended by named classical doctrine
   for each pairwise comparison. The exact NUMBERS are this document's own construction — chosen
   to (a) sum cleanly to 1.00 in the 5-slot case with no renormalization, and (b) preserve the
   stated ordering with meaningful gaps. A different, still-defensible author could have chosen
   0.40/0.25/0.20/0.10/0.05 or similar without violating any cited doctrine. This is the second
   highest-leverage judgment call in the document.
3. **Equal splitting of multi-item slots (§3.1, §3.2).** When a class lists two or three houses or
   karakas, this document splits that slot's weight evenly. No classical citation in the existing
   registry ranks, e.g., marriage's Venus above its Jupiter, or business_launch's 7th house above
   its 10th — equal division is the STATED DEFAULT for "no citation says otherwise," which is a
   real and disclosed assumption, not a hidden one.
4. **`parental_event`'s `dusthana_required=False` (§7).** A judgment call with no denial-adjacent
   citation behind it, as stated in §7 itself.
5. **Denial-configuration deduction SIZE (§4).** The deduction-sizing RULE (deduction = weight of
   the falsified slot(s)) is mechanical and non-arbitrary once chosen; the CHOICE to size
   deductions that way, rather than e.g. a flat 1.0/0.6/0.4 severity ladder independent of
   per-class weights, is this document's own design decision — defensible (it ties the penalty
   directly to the specific evidence the configuration falsifies) but not itself a classical
   citation.
6. **Citation precision on two doctrines (§2.7 aspect fractions, §4 CFG-3 pāpakartarī).** Both
   doctrines are real, well-established, and named correctly; neither is pinned to a specific
   chapter/verse this document's author could independently verify against a primary text, unlike
   the registry's own citations (which follow a `BPHS ch.N (topic)` convention this document
   could not always match with equal confidence). Stated honestly in-line at both points rather
   than fabricating a plausible-looking chapter number, per §N.7 item 6 (an honest gap beats an
   invented precision).
7. **The yoga-presence 3-tier band's 0.50 midpoint (§2.5).** The 0.00/1.00 endpoints are
   unambiguous (no match / confirmed firing); the 0.50 value for a catalog-only match is a
   reasonable midpoint given the two-tier confidence distinction the codebase already draws
   (§N.6), but "reasonable midpoint" is this document's word choice, not a classical number.

None of the above trace to chart `482012f1`'s facts, signals, or the native's known outcomes —
they were not consulted while writing this document (§0). They are documented uncertainty about
WHERE this document's judgment substituted for a citation it did not have, which is a different
and much narrower risk than R13's, but worth the checkpoint's attention regardless.

---

*End of V4_RUBRIC_SPEC_v0_9.md. Status: DRAFT. Ratifies to v1.0 only at the human+Fable
checkpoint (MASTER_PLAN_v1_0.md §4), alongside the sibling Factor→Fact Coverage Matrix artifact
and the Rung P3 hand-worked examples this spec's thresholds must NOT be adjusted to match.*

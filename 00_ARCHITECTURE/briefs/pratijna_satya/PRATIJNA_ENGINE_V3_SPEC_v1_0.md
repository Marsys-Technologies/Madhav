# Promise Engine v3.0 Specification

**Campaign:** PRATIJÑA-SATYA Phase B
**Status:** DRAFT
**Version:** 1.0
**Author:** Conductor (Opus 4.6)
**Rulings:** R11 (per-class significators), R12 (occurrence ≠ condition), R13 (no fitting)

---

## 1. Problem Statement

bo_pratijna v2.0 matches signals to event classes by **ontology domain only**:
```python
if domain not in ec_domains: continue
```

This means every `relationship`-domain event class (marriage, separation, romantic_start)
receives the **same grade** from the **same signals** — confirmed live on 482012f1/lahiri:
all three carry grade EXACTLY 1.1690 with identical evidence (2,710 supporting / 1,078
contradicting). Marriage remains `denied` for a native who married in 2013.

**Root cause:** Domain is a coarse bucket, not a classical significator set. An afflicted
7th house is evidence about the marriage's CHARACTER (R12), not about whether marriage
occurs. And the dusthana involvement that signals separation is invisible to a domain
matcher that only sees "relationship."

## 2. Design — Classical Karyatva Routing

v3 replaces domain matching with **per-class karyatva (significator) factor sets** drawn
from classical texts. Each factor set defines WHICH chart facts constitute evidence for
or against a specific event class.

### 2.1 Factor Types

Each event class's karyatva map contains these factor types, each with a classical citation:

| Factor Type | Source (L1) | How matched against bodha_msr_signals |
|---|---|---|
| `primary_bhava` | Houses [1-12] | Signal's `constituent_facts_array` references facts with `fact_key` matching house-related keys |
| `bhava_lord` | Lord of house N | Signal references the lord planet's dignity/placement facts |
| `karaka` | Natural significator | Signal's primary graha matches the karaka planet |
| `divisional` | Varga chart | Signal type references the relevant divisional |
| `yoga_dosha` | Relevant yogas | Signal references yoga firings relevant to the class |
| `arudha` | Relevant arudha pada | Signal references arudha pada facts |

### 2.2 Karyatva Map — Per Event Class

Each row below carries one or more BPHS/Phaladeepika citations. R13 mandate: these are
drawn from classical rules ONLY, never adjusted for the native's known outcomes.

#### Marriage
- **Primary bhava:** 7 (kalatra-bhava) — BPHS ch.19 (vivaha-vicara)
- **Bhava lord:** 7L — BPHS ch.19
- **Karaka:** Venus (kalatra karaka) — BPHS ch.28 (karaka-adhyaya)
- **Divisional:** D9 (navamsha — the marriage chart) — BPHS ch.6
- **Arudha:** Upapada Lagna (A7/UL) — Jaimini Sutram 1.3.1
- **Yoga/Dosha:** Darakaraka activation — Jaimini Sutram 1.2
- **Occurrence factors:** 7L dignity, Venus strength, D9 lagna condition, Jupiter aspect to 7H
- **DISTINGUISHING from separation:** Marriage routes through BENEFIC aspects and strengths
  of 7L/Venus. An afflicted 7L is a CONDITION signal for marriage quality, but 7L's
  existence and connection to lagna is OCCURRENCE evidence.

#### Separation
- **Primary bhava:** 7 PLUS 6, 8, 12 (dusthana involvement) — BPHS ch.19/ch.12
- **Bhava lord:** 7L in 6/8/12 or afflicted by dusthana lords — BPHS ch.19
- **Karaka:** Saturn (karaka for separation/delay), Ketu (karaka for severance) — BPHS ch.28
- **Divisional:** D9 affliction — BPHS ch.6
- **Yoga/Dosha:** Kuja dosha (Mars in 1/4/7/8/12 of D9) — BPHS ch.19; 6L-7L exchange
- **Occurrence factors:** 7L in dusthana, Saturn/Rahu aspecting 7H, 6L/8L/12L conjunct 7L
- **DISTINGUISHING from marriage:** Separation REQUIRES dusthana involvement (6/8/12) in
  the 7th-house system. A strong 7L without dusthana is evidence FOR marriage, AGAINST
  separation. This is the structural difference the domain matcher misses entirely.

#### Childbirth
- **Primary bhava:** 5 (putra-bhava) — BPHS ch.16 (santana-vicara)
- **Bhava lord:** 5L — BPHS ch.16
- **Karaka:** Jupiter (putra karaka) — BPHS ch.28
- **Divisional:** D7 (saptamsha — progeny chart) — BPHS ch.6
- **Arudha:** A5 — Jaimini Sutram
- **Occurrence factors:** 5L dignity, Jupiter strength, D7 lagna, 5th-from-Jupiter
- **INDEPENDENT of relationship:** Childbirth routes through 5H/Jupiter/D7 — entirely
  independent of 7H affliction. An afflicted 7th house says NOTHING about progeny.

#### Surgery
- **Primary bhava:** 6, 8 (roga/randhra) — BPHS ch.12 (shastra-vrana)
- **Bhava lord:** 6L, 8L — BPHS ch.12
- **Karaka:** Mars (karaka for cutting/sharp instruments) — Phaladeepika ch.6
- **Divisional:** D30 (trimsamsha — affliction) — BPHS ch.6
- **Occurrence factors:** Mars in 6/8, malefic aspects to lagna, 8L-Mars connection

#### Relocation
- **Primary bhava:** 4 (sukha-bhava — homeland), 12 (vyaya — foreign) — BPHS ch.11/ch.12
- **Bhava lord:** 4L, 12L — BPHS ch.11/ch.12
- **Karaka:** Moon (karaka for mind/comfort), Rahu (foreign influence) — BPHS ch.28
- **Divisional:** D4 (chaturthamsha) — BPHS ch.6
- **Occurrence factors:** 4L-12L exchange, Rahu in 4/9/12, Moon affliction

#### Foreign Settlement
- **Primary bhava:** 12 (videsh), 9 (long journeys), 7 (foreign residence) — BPHS ch.12
- **Bhava lord:** 12L, 9L — BPHS ch.12
- **Karaka:** Rahu (foreign influence) — classical consensus
- **Divisional:** D9, D12 — BPHS ch.6
- **Occurrence factors:** 12L-lagna connection, Rahu in kendra, 9L in 12

#### Career Entry / Career Change / Career Advancement / Career Setback
- **Primary bhava:** 10 (karma-bhava) — BPHS ch.10
- **Bhava lord:** 10L — BPHS ch.10
- **Karaka:** Sun (authority), Saturn (karma) — BPHS ch.28
- **Divisional:** D10 (dashamsha) — BPHS ch.6
- **Career entry/advancement vs setback:** Benefic involvement = entry/advancement;
  malefic/dusthana involvement = setback. The SAME house system, different valence.

#### Business Launch
- **Primary bhava:** 7 (partnerships), 10 (karma), 11 (gains) — BPHS ch.10/ch.11
- **Bhava lord:** 7L, 10L, 11L — BPHS ch.10
- **Karaka:** Mercury (commerce), Jupiter (expansion) — BPHS ch.28
- **Divisional:** D10 — BPHS ch.6

#### Education Milestone / Exam Outcome
- **Primary bhava:** 4 (vidya), 5 (buddhi), 9 (higher learning) — BPHS ch.4/ch.5/ch.24
- **Bhava lord:** 4L, 5L, 9L — BPHS ch.4/ch.5
- **Karaka:** Mercury (intellect), Jupiter (wisdom) — BPHS ch.28
- **Divisional:** D24 (chaturvimsamsha — education) — BPHS ch.6

#### Health events (illness_acute, chronic_onset)
- **Primary bhava:** 6 (roga), 8 (chronic) — BPHS ch.12
- **Bhava lord:** 6L, 8L — BPHS ch.12
- **Karaka:** Saturn (chronic), Mars (acute) — Phaladeepika ch.6
- **Divisional:** D30 — BPHS ch.6

#### Financial events (major_gain, major_loss, property_acquisition)
- **Primary bhava:** 2 (dhana), 11 (labha) — BPHS ch.2/ch.11
- **Bhava lord:** 2L, 11L — BPHS ch.2/ch.11
- **Karaka:** Jupiter (wealth), Mercury (commerce) — BPHS ch.28
- **Divisional:** D2 (hora) — BPHS ch.6
- **Gain vs loss:** Benefic connection = gain; 12L/dusthana = loss

#### Bereavement / Parental Event
- **Primary bhava:** 4 (mother), 9 (father), 8 (death/transformation) — BPHS ch.4/ch.9
- **Bhava lord:** 4L, 9L, 8L — BPHS ch.4/ch.9
- **Karaka:** Moon (mother), Sun (father), Saturn (longevity) — BPHS ch.28
- **Divisional:** D12 (dwadashamsha — parents) — BPHS ch.6

#### Spiritual Turn
- **Primary bhava:** 9 (dharma), 12 (moksha), 5 (purva-punya) — BPHS ch.24/ch.12
- **Bhava lord:** 9L, 12L — BPHS ch.24
- **Karaka:** Jupiter (guru), Ketu (moksha) — BPHS ch.28
- **Divisional:** D20 (vimshamsha — spiritual) — BPHS ch.6

### 2.3 Provisional Classes (DR-13)

The 5 DR-13 classes (achievement_recognition, financial_deception, psychological_arc,
birth_anchor, travel_event) keep their `provisional: true` signature_models. They use
domain-matching as a labelled lower-confidence fallback until dedicated classical factor
sets are authored — never silently defaulting.

## 3. Two-Judgment Architecture (R12)

The current v2.0 produces ONE grade per event class. v3 produces TWO:

### 3.1 Occurrence Judgment
**Question:** Does the chart promise this event at all?

- Computed from the OCCURRENCE factors listed in §2.2
- Reads: house condition, lord dignity, karaka strength, relevant varga lagna
- **An afflicted 7th house is still occurrence-positive for marriage** (the house
  exists and is activated) — the affliction speaks to condition, not existence

### 3.2 Condition Reading
**Question:** How afflicted or supported is the configuration?

- Computed from the SAME house system but reads DIFFERENT signals: aspects by
  malefics/benefics, dusthana lord involvement, combust/retrograde status
- An afflicted-but-present 7th house yields: occurrence=positive, condition=afflicted

### 3.3 Schema Impact

`bodha_pratijna` gains two new columns:
```sql
ALTER TABLE bodha_pratijna
  ADD COLUMN IF NOT EXISTS occurrence_grade NUMERIC(5,3),
  ADD COLUMN IF NOT EXISTS condition_grade NUMERIC(5,3);
```

The existing `grade` column becomes the combined grade (weighted: `0.7 * occurrence + 0.3 * condition`). The `status` derivation reads from `occurrence_grade`:
- `no_evidence` when no occurrence factors matched
- `promised` when `occurrence_grade >= 6.0`
- `denied` when `occurrence_grade < 2.0`
- `conditional` otherwise

The `condition_grade` is served separately (R12) and never collapses into the
occurrence judgment.

## 4. Signal Matching Algorithm

v3 replaces the domain-matching inner loop with a karyatva-routing algorithm:

```python
def _match_signal_to_class(signal, karyatva_map) -> (occurrence_weight, condition_weight):
    """
    For each signal, check if its constituent_facts reference any of the
    karyatva_map's factors (houses, lords, karakas, divisionals, yogas).

    Returns (occurrence_weight, condition_weight) where:
      occurrence_weight > 0 means the signal is evidence about whether the event occurs
      condition_weight > 0 means the signal is evidence about the event's quality
    """
    occ_w = 0.0
    cond_w = 0.0

    for fact_id in signal.constituent_facts_array:
        fact = lookup_fact(fact_id)

        # Check primary bhava match
        if fact.fact_key matches any karyatva_map.primary_bhava:
            if signal.valence in ('benefic', 'neutral'):
                occ_w += signal.salience
            else:
                cond_w += signal.salience

        # Check karaka match
        if fact references karyatva_map.karaka planet:
            occ_w += signal.salience * 0.8  # karaka is occurrence evidence

        # Check dusthana involvement (separation-type classes only)
        if karyatva_map.requires_dusthana:
            if fact.fact_key references dusthana houses (6/8/12):
                occ_w += signal.salience  # dusthana IS the occurrence signal

    return (occ_w, cond_w)
```

**Domain fallback:** For classes where no karyatva map exists (provisional DR-13 classes),
fall back to v2.0 domain matching with a labelled `confidence_tier: 'domain_fallback'`.

## 5. R13 Compliance — No Fitting

Every weight and threshold in v3 is derived from classical rules:
- House lordship strengths: from BPHS ṣaḍbala, already in L1 chart_facts
- Karaka weights: uniform (1.0) — no empirical tuning
- Divisional weights: uniform (0.8) — no empirical tuning
- Occurrence threshold (6.0): carried from v2.0, a structural constant

**PARĪKṢAKA audit points:**
1. No weight or threshold traceable to the native's known outcomes
2. Every citation resolves against the classical corpus
3. The mapping table is the same for ALL charts — no per-chart adjustment

## 6. Required Property Tests (B3)

1. **Marriage ≠ separation:** Same chart, both "relationship" domain, but different
   karyatva routes produce DIFFERENT grades. Test: marriage occurrence_grade >
   separation occurrence_grade when 7L is strong without dusthana involvement.

2. **Childbirth independent of relationship:** An afflicted 7th house does NOT affect
   childbirth grade. Test: modification to 7H facts changes marriage/separation grades
   but NOT childbirth grade.

3. **Afflicted-but-present (R12):** An afflicted 7th house yields
   occurrence_grade > 2.0 (the house is present) AND condition_grade < 5.0
   (it is afflicted). Test: the status is NOT 'denied'.

4. **R13 audit:** No weight or threshold derived from the native's outcomes.
   Test: inspect all constants and verify none reference chart_id or LEL data.

## 7. Implementation Plan

### B1: This spec (done)
### B2: Build bo_pratijna v3.0
- New file: `platform/python-sidecar/pipeline/orchestrator/writers/bo_pratijna_karyatva.py`
  (the karyatva map data structure, separate from the writer for auditability)
- Modify: `bo_pratijna.py` — ENGINE_VERSION → "bo_pratijna_v3.0", FORMULA_VERSION → "v3.0"
- Migration: add `occurrence_grade` and `condition_grade` columns
- Keep no_evidence status, keep R6 modifier contract intact

### B3: Tests (per §6 above)
### B4: PARĪKṢAKA verdict (citation + R13 + mutation standard)

## 8. Downstream Compatibility

The R6 modifier contract is preserved:
- `_promise_lift(grade, status)` in ph_nimitta continues to read `grade` (the combined)
- `stage2_promise` reads `supporting_signal_ids` (unchanged)
- `ka_avadhi` reads `grade` (unchanged, now the combined value)
- `mi_darshana` reads `status` + `grade` (unchanged semantics)

New consumers CAN read `occurrence_grade` and `condition_grade` separately, but
existing consumers are unaffected.

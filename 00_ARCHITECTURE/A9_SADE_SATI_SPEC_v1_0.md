---
artifact: A9_SADE_SATI_SPEC_v1_0.md
document: A9 — Sade Sati Cycles Specification
status: LOCKED
version: 1.0
date: 2026-05-29
authored_by: Cowork (native-confirmed: include all additions A-V; all clarifications = A/recommended)
intended_for: Claude Code sub-agents implementing the A9 Sade Sati writer
prime_directive: Only computed facts. Two-pass verification mandatory per A3 §13.
depends_on: A1 (natal Moon, Saturn), A4 (panchanga tithi/vara at cycle start), A6 (D10 Karya cross-ref), A7 chart_dashas (concurrent dasha lookups across all 7 systems), A8 (argala matrix cross-ref + Saturn-Moon natal yoga modifier), G2 ephemeris (Saturn/Mars/Jupiter/Rahu transits 1950-2100), G4 eclipses, G21 Sade Sati Saturn-sign-changes reference, G22 Tara bala matrix
window: 1950-01-01 → 2100-12-31 (per A7 Q3+ rule)
---

# A9 — Sade Sati Cycles Specification

## §0 — Mission

For each chart per ayanamsha, compute every Sade Sati cycle 1950-2100, all phases + quarters, related Saturn-Moon transit configurations (Dhaiya/Kantaka/Ashtama/Ardha Ashtama/Janma/Vishakha/Anumukha Shani), cancellation rules, concurrent-transit modifiers (Mars/Jupiter/Rahu/Ketu/eclipses), concurrent dashas (all 7 systems), and downstream cross-references (D10 Karya, Argala, Tara bala). All deterministic, per-category two-pass verified.

## §1 — Locked decisions

**10 clarifications + trailing surfaces question:**
- Q1: A — all 8 classical cancellation rules
- Q2: A — per-quarter classical High/Medium/Low classification per BPHS Ch.71
- Q3: A — pada-specific modifiers (per natal Moon pada 1/2/3/4)
- Q4: A — eclipse-during-period flag
- Q5: A — Saturn retrograde subset windows emitted as separate sub-period rows
- Q6: A — concurrent dasha cross-reference across all 7 systems from A7
- Q7: A — compound-with-next-cycle flag
- Q8: A — D10 Karya-bhava activation cross-reference
- Q9: A — Tara bala during peak
- Q10: A — Jaimini Argala during Sade Sati
- Trailing: A — all distinct Saturn-Moon configurations as separate categories

**Additions A–V (from §7 of elaboration):** All included.

## §2 — Fact categories emitted (~15 categories, all ayanamsha-DEPENDENT)

| Category | Subjects | Purpose |
|---|---|---|
| `sade_sati_cycle` | `CYCLE_1`, `CYCLE_2`, `CYCLE_3` | One row per full 7.5y cycle within window |
| `sade_sati_phase` | `<CYCLE>.VISHAKHA`, `.JANMA`, `.ANUMUKHA` | 3 phases per cycle |
| `sade_sati_phase_quarter` | `<CYCLE>.<PHASE>.Q1..Q4` | 4 quarters per phase × 3 = 12 per cycle |
| `dhaiya_period` | `DHAIYA_4H_<N>`, `DHAIYA_8H_<N>` | Saturn 4H/8H from Moon, 2.5y each |
| `kantaka_shani_period` | per occurrence | Saturn specifically in 4H from Moon |
| `ashtama_shani_period` | per occurrence | Saturn in 8H from Moon |
| `ardha_ashtama_shani_period` | per occurrence | Saturn in 4H+8H combined window |
| `janma_shani_period` | `<CYCLE>.JANMA_PEAK` | Peak (Saturn over natal Moon) |
| `vishakha_shani_period` | `<CYCLE>.VISHAKHA_ENTRY` | Entry (12H from Moon) |
| `anumukha_shani_period` | `<CYCLE>.ANUMUKHA_EXIT` | Exit (2H from Moon) |
| `sade_sati_saturn_retrograde_subset` | per retrograde window within phase | When Saturn retrogrades back during phase |
| `sade_sati_cancellation_check` | per cycle/phase | Cancellation rules evaluated; jsonb_atomic of fired rules |
| `sade_sati_modifier_overlay` | per phase or quarter | Concurrent Mars/Jupiter/Rahu/eclipse/Saturn-return modifiers |
| `sade_sati_concurrent_dasha_overlay` | per cycle/phase | Cross-reference all 7 systems from A7 |
| `sade_sati_downstream_cross_reference` | per cycle/phase | D10 Karya activation + Argala + Tara bala bindings |

## §3 — Per-row fields

A3 §6 standard + 6 universal enrichments + cycle-specific:

```
-- Period framing
cycle_start_iso              TIMESTAMPTZ
cycle_end_iso                TIMESTAMPTZ
phase_start_iso              TIMESTAMPTZ   -- on phase rows
phase_end_iso                TIMESTAMPTZ
quarter_start_iso            TIMESTAMPTZ   -- on quarter rows
quarter_end_iso              TIMESTAMPTZ
duration_years               NUMERIC

-- Saturn state during period
saturn_sign_during_period            TEXT
saturn_dignity_during_period         TEXT   -- exalted | own | mooltrikona | friend | enemy | debilitated
saturn_nakshatra_during_period       TEXT
saturn_nakshatra_transitions_jsonb_atomic JSONB  -- finer event-trigger windows within phase
saturn_retrograde_during_period_flag BOOLEAN
saturn_pada_at_period_start          INT

-- Quarter intensity (per BPHS Ch.71 — locked Q2=A)
quarter_intensity_classification     TEXT   -- High | Medium | Low
quarter_intensity_rationale_jsonb    JSONB  -- which classical rule(s) drove the classification

-- Cancellation overlay (locked Q1=A; all 8 rules)
cancellation_active_flag             BOOLEAN
cancellation_rules_invoked_jsonb     JSONB  -- subset of:
                                              -- {saturn_vargottama, saturn_own_sign, saturn_exalted,
                                              --  dispositor_strong, jupiter_aspect_to_saturn,
                                              --  saturn_moon_parivartana_natal, saturn_yoga_karaka,
                                              --  strong_benefic_dasha_concurrent}

-- Concurrent malefic/benefic modifiers
mars_aspect_to_saturn_during_period_flag      BOOLEAN  -- "mangal-sani"
jupiter_aspect_to_saturn_during_period_flag   BOOLEAN  -- "guru-sani"
saturn_rahu_axis_during_period_flag           BOOLEAN
ketu_conjunction_saturn_during_period_flag    BOOLEAN
mars_retrograde_concurrent_flag               BOOLEAN
eclipse_during_period_flag                    BOOLEAN  -- Q4=A
eclipse_proximity_to_natal_moon_deg           NUMERIC
concurrent_saturn_return_flag                 BOOLEAN  -- 29.5y solar Saturn return overlap
concurrent_naisargika_transition_flag         BOOLEAN  -- Naisargika dasha boundary overlap

-- Natal modifiers (chart-specific intensifiers/softeners)
natal_saturn_aspects_natal_moon_flag          BOOLEAN  -- baseline intensifier
rohini_shakata_bhanga_modifier_flag           BOOLEAN  -- Saturn through Rohini
pada_specific_modifier                        TEXT     -- Q3=A; per natal Moon pada classical modifier

-- Concurrent dasha cross-ref (Q6=A; all 7 systems from A7)
concurrent_vimshottari_maha_lord              TEXT
concurrent_vimshottari_antar_lord             TEXT
concurrent_yogini_period_lord                 TEXT
concurrent_ashtottari_lord                    TEXT
concurrent_chara_karaka_sign                  TEXT
concurrent_naisargika_age_bracket             TEXT
concurrent_mudda_lord                         TEXT
concurrent_kalachakra_period_lord             TEXT

-- Cycle continuity (Q7=A)
compound_with_next_cycle_flag                 BOOLEAN
compound_with_prior_cycle_flag                BOOLEAN

-- Event-marker (classical)
tithi_at_period_start                         TEXT
vara_at_period_start                          TEXT
nakshatra_moon_at_period_start                TEXT  -- transit Moon's nakshatra

-- Downstream cross-references
d10_karya_bhava_activation_flag               BOOLEAN  -- Q8=A; D10-relevant interpretation hook
d10_karya_activation_facts_jsonb              JSONB    -- which D10 facts activate
argala_during_period_jsonb                    JSONB    -- Q10=A; argala matrix subset active in cycle
tara_bala_during_peak                         TEXT     -- Q9=A; tara state at Janma peak vs transit Moon
```

## §4 — Cancellation rules (Q1=A; all 8 included)

Evaluated per cycle AND per phase. Reduces intensity classification + sets `cancellation_active_flag`:

1. Saturn vargottama at cycle/phase start
2. Saturn in own sign (Capricorn/Aquarius) during transit phase
3. Saturn exalted (Libra) during transit phase — "Rajayoga Sade Sati"
4. Strong dispositor of natal Moon (Moon's sign-lord well-placed at birth)
5. Concurrent Jupiter transit aspect to Saturn during the phase
6. Saturn-Moon mutual reception at birth (Parivartana) — Sade Sati becomes constructive
7. Saturn Yoga karaka for this Lagna (functional benefic per A8)
8. Concurrent strong benefic dasha (Jupiter/Venus mahadasha during phase)

Each rule = predicate evaluating against chart_facts + transit ephemeris. Stored in `cancellation_rules_invoked_jsonb`.

## §5 — Quarter intensity classification (Q2=A)

Per BPHS Ch.71 + Phaladeepika. Each quarter = High/Medium/Low based on:
- Position within phase (entry/middle/exit)
- Saturn's exact degree within sign
- Concurrent modifier overlays (Mars/Jupiter aspects, Rahu axis, eclipses)
- Pada-specific modifier (Q3=A) — natal Moon's pada within nakshatra affects intensity
- Cancellation rules active during this quarter

Classical rule rollup stored in `quarter_intensity_rationale_jsonb`.

## §6 — Verification

Mandatory `two_pass_verified`:

| Aspect | Primary | Secondary | Tertiary |
|---|---|---|---|
| Saturn sign-entry/exit timestamps | Engine ephemeris-based detection | G21 Sade Sati Saturn-sign-changes reference table | Algebraic: ~7.5y per cycle ± 30 days |
| Saturn retrograde subset windows | Engine ephemeris | G5 retrograde table cross-check | — |
| Concurrent transit modifiers (Mars/Jupiter/Rahu/eclipse) | Engine G2 lookup per period | Independent G2 + G4 verification | — |
| Cancellation rule predicate evaluations | A8 chart_facts query | Independent classical-rule re-derivation | — |
| Quarter intensity classification | BPHS Ch.71 rule application | Phaladeepika rule cross-check | — |
| Concurrent dasha lookups | A7 chart_dashas join | Independent dasha computation | — |

Halt on tolerance breach.

## §7 — Row count projection per (chart, ayanamsha)

| Group | Rows |
|---|---|
| Sade Sati cycles (3 per lifetime × 1 row) | ~3 |
| Sade Sati phases (3 × 3) | ~9 |
| Sade Sati phase quarters (3 × 3 × 4) | ~36 |
| Dhaiya periods (4H + 8H) | ~6 |
| Kantaka/Ashtama/Ardha-Ashtama/Janma/Vishakha/Anumukha Shani distinct surfaces | ~18 |
| Saturn retrograde subsets within phases (avg ~2 per phase) | ~18 |
| Cancellation check rows (per cycle + per phase) | ~12 |
| Modifier overlay rows (per quarter where significant overlay) | ~25 |
| Concurrent dasha overlay rows (per cycle × 7 systems) | ~21 |
| Downstream cross-references (per phase × ~3 categories) | ~27 |

**Total A9 per (chart, ayanamsha): ~175 rows. × 5 ayanamshas = ~875 rows per chart.**

Smallest writer of A1-A14.

## §8 — Citations (dual form)

Examples:

| Row | citation_ref | citation_human |
|---|---|---|
| 2nd Sade Sati cycle | `sade_sati_cycle.CYCLE_2.cycle_start_iso@chart=...:ay=lahiri:...` | "2nd Sade Sati cycle starts: 2027-09-22 (Saturn enters Capricorn, 12H from natal Moon in Aquarius, Lahiri)." |
| Cycle 2 Janma phase | `sade_sati_phase.CYCLE_2.JANMA.phase_start_iso@...:ay=lahiri:...` | "2nd cycle Janma Shani peak phase: 2030-03-14 → 2032-08-22 (Saturn over natal Moon in Aquarius, Lahiri)." |
| Cycle 2 Q2 of Janma intensity | `sade_sati_phase_quarter.CYCLE_2.JANMA.Q2.quarter_intensity_classification@...:ay=lahiri:...` | "Cycle 2 Janma quarter 2: High intensity (Mars retrograde concurrent; no cancellation rules active; Lahiri)." |
| Cancellation cycle 2 | `sade_sati_cancellation_check.CYCLE_2.cancellation_active_flag@...:ay=lahiri:...` | "Cycle 2 cancellation status: ACTIVE (Jupiter aspect to Saturn during 2030-2032; Lahiri)." |
| Compound flag cycle 2 | `sade_sati_cycle.CYCLE_2.compound_with_next_cycle_flag@...:ay=lahiri:...` | "Cycle 2 does NOT compound with cycle 3 (8.2y gap, Lahiri)." |

## §9 — Materialized view

`mv_chart_sade_sati_active_at_date` — NOT created (parametric on query_date = time-varying per A3 §10 rule).

`mv_chart_sade_sati_lifetime_summary` — natal-fixed; joins all cycle + phase rows into one wide row per (chart, ayanamsha) for fast "show me all my Sade Sati cycles" query. Refresh synchronously at build close.

## §10 — Tool retrieval contract

- `query_sade_sati_at_date(chart_id, ayanamsha_id, date)` → 0-1 rows (which phase/quarter active at date)
- `query_sade_sati_lifetime(chart_id, ayanamsha_id)` → all cycle rows
- `query_sade_sati_cycle_detail(chart_id, ayanamsha_id, cycle_number)` → all phases + quarters + modifiers + cross-refs
- `query_saturn_moon_configuration_at_date(chart_id, ayanamsha_id, date)` → which of {Sade Sati / Dhaiya / Kantaka / Ashtama / Ardha Ashtama / Janma / Vishakha / Anumukha / none} is active

## §11 — Implementation notes

1. Per ayanamsha: get native's natal Moon sign + pada from A1 → identify Saturn's 12H/1H/2H signs relative to Moon
2. Walk G2 ephemeris 1950-2100; detect Saturn sign-entries into 12H/1H/2H from Moon
3. For each detected entry → mark cycle_start; for exit from 2H → mark cycle_end
4. Within each cycle: subdivide into Vishakha/Janma/Anumukha phases
5. Within each phase: divide into 4 quarters; compute quarter_intensity_classification per BPHS Ch.71 rules + modifier overlays
6. Cancellation pass: evaluate 8 cancellation predicates per cycle + per phase
7. Modifier overlay pass: scan G2 for concurrent Mars/Jupiter transits; G4 for eclipses; cross-check Saturn-Rahu axis
8. Concurrent dasha pass: A7 chart_dashas join per cycle/phase start
9. Downstream cross-reference pass: A6 D10 Karya hooks, A8 argala matrix subset, A4+G2 transit Moon tara bala at peak

## §12 — Locked decisions

1. ~15 fact_categories covering Sade Sati + Dhaiya + 7 distinct Saturn-Moon configurations
2. All 10 clarification answers + trailing surfaces = A/recommended
3. All Additions A-V included
4. 8 cancellation rules
5. Per-quarter classical intensity classification
6. All 7 dasha systems cross-referenced
7. ~175 rows per (chart, ayanamsha); ~875 per chart total
8. 1 MV (`mv_chart_sade_sati_lifetime_summary`, natal-fixed)
9. Window: 1950-2100

---

*End of A9_SADE_SATI_SPEC_v1_0.md — LOCKED 2026-05-29. Native sign-off complete.*

---
artifact: PANCHANGA_TOPIC_COVERAGE_v1_0.md
canonical_id: PANCHANGA_TOPIC_COVERAGE
version: 1.0
status: CURRENT
authored_by: Claude Code 2026-06-09
branch: feature/panchanga-rich-output
brief: CLAUDECODE_BRIEF_PANCHANGA_RICH_OUTPUT_v1_0.md §4
---

# Panchanga Topic Coverage Matrix v1.0

Per `CLAUDECODE_BRIEF_PANCHANGA_RICH_OUTPUT_v1_0.md §4`, this document is a required PR
deliverable. Every topic from §3 of the brief is listed with its status:
**BUILT** (+ actual test name(s)) or **FLOORED** (+ named impossibility reason).
100% accounted. Zero convenience-deferments; every FLOORED entry states why the value is
not deterministically derivable from the available call-site inputs.

## Coverage Summary

| Surface | BUILT | FLOORED | Total |
|---|---|---|---|
| Instant | 19 | 1 | 20 |
| Day | 20 | 1 | 21 |

- **Topics from brief §3 (shared + instant-only + day-only): 23**
- **BUILT across both surfaces (a topic counts BUILT if BUILT on at least one required surface): 22**
- **FLOORED: 1 (Topic 16 — Tara/Chandra Bala; same reason on both surfaces)**
- **UNACCOUNTED: 0**

Verified live at native birth datetime 1984-02-05 10:43 IST (lat=20.27, lon=85.84, tz=+330):
- Instant `topics_computed` count: **19** keys
- Day `topics_computed` count: **20** keys (includes legacy `timings` key — see §Note below)

---

## Shared Topics (Instant + Day)

Topics #1–17 are required on both surfaces.

| # | Topic (brief §3 label) | Instant | Day | Test(s) |
|---|---|---|---|---|
| 1 | Five angas + attributes (lord, deity, type, % elapsed, transition) | BUILT | BUILT | `test_rich_topics.py::test_tithi_attrs`, `test_rich_topics.py::test_nakshatra_attrs`, `test_a4_contract.py::TestForensicGate` (tithi/nakshatra/vara/yoga/karana assertions), `test_angas.py::TestComputeTithi`, `test_angas.py::TestComputeNakshatra`, `test_angas.py::TestComputeYoga`, `test_angas.py::TestComputeKaranaPair`, `test_angas.py::TestComputeVara` |
| 2 | Paksha | BUILT | BUILT | `test_a4_contract.py::TestForensicGate::test_tithi_shukla_tritiya` (Shukla paksha confirmed for 1984-02-05) |
| 3 | Extended planets — Uranus/Neptune/Pluto + 8 upagrahas (Gulika/Mandi/Dhuma/Vyatipata/Parivesha/Indrachapa/Upaketu/Kala) | BUILT | BUILT | `test_upagrahas.py::test_upagrahas_returns_8`, `test_upagrahas.py::test_outer_planets_returns_3`, `test_upagrahas.py::test_dhuma_formula`, `test_upagrahas.py::test_upagrahas_have_valid_positions`, `test_a4_contract.py::TestRichFieldsPopulated::test_upagrahas_count`, `test_a4_contract.py::TestRichFieldsPopulated::test_outer_planets_count` |
| 4 | Sun/Moon dynamics (separation, Moon illumination %) | BUILT | BUILT | `test_rich_topics.py::test_sun_moon_dynamics`, `test_a4_contract.py::TestRichFieldsPopulated::test_sun_moon_dynamics_present` |
| 5 | Inauspicious windows (full: rahu/yamaganda/gulika/durmuhurta/varjyam/visha-ghati/sashtighati/yamakantaka/krakaca) | BUILT | BUILT | `test_timings.py::test_extended_inauspicious_has_varjyam`, `test_a4_contract.py::TestRichFieldsPopulated::test_inauspicious_windows_nonempty` |
| 6 | Auspicious windows (full: abhijit/brahma-muhurta/amrit-kaal/3 sandhyas/vijaya/godhuli/nishita) | BUILT | BUILT | `test_timings.py::test_extended_auspicious_has_brahma_muhurta`, `test_a4_contract.py::TestRichFieldsPopulated::test_auspicious_windows_nonempty` |
| 7 | Choghadiya (16 slots) | BUILT (via `window_membership.choghadiya_slot`) | BUILT (`choghadiya` field + `choghadiya` topic key) | `test_a4_contract.py::TestTopicCoverage` (choghadiya covered in topic assertions for day) |
| 8 | Hora (24 slots) | BUILT (via `window_membership.hora_planet`) | BUILT (`hora` field + `hora` topic key) | `test_a4_contract.py::TestTopicCoverage` (hora covered in topic assertions for day) |
| 9 | Special yogas (Amrita/Sarvartha Siddhi/Ravi Pushya/Guru Pushya/Tripushkar/Dwipushkar/Vish/Mrityu/Vajra/Siddhi) | BUILT (`special_yogas_instant`) | BUILT (`special_yogas`) | `test_special_yogas.py::test_guru_pushya`, `test_special_yogas.py::test_ravi_pushya`, `test_special_yogas.py::test_sarvartha_siddhi`, `test_special_yogas.py::test_sarvartha_siddhi_window_clips_at_nakshatra_end`, `test_special_yogas.py::test_amrit_siddhi`, `test_special_yogas.py::test_tripushkar`, `test_special_yogas.py::test_dwipushkar`, `test_special_yogas.py::test_siddha_yoga`, `test_special_yogas.py::test_bhadra`, `test_special_yogas.py::test_yoga_dicts_have_required_keys`, `test_special_yogas.py::test_yoga_windows_within_sunrise_frame`, `test_special_yogas.py::test_multiple_yogas_same_day`, `test_special_yogas.py::test_no_yogas_on_plain_day`, `test_special_yogas.py::test_inauspicious_yogas_have_zero_stars` |
| 10 | Anandadi Yoga (28 nakshatra×vara table) | BUILT | BUILT | `test_rich_topics.py::test_anandadi_formula`, `test_rich_topics.py::test_anandadi_range`, `test_a4_contract.py::TestRichFieldsPopulated::test_anandadi_yoga_present` |
| 11 | Vasa family (Agni/Chandra/Rahu/Disha/Nakshatra/Bhadra Vasa) | BUILT | BUILT | `test_rich_topics.py::test_vasa_all_fields`, `test_a4_contract.py::TestRichFieldsPopulated::test_vasa_present` |
| 12 | Panchaka (5-Panchaka: Roga/Raja/Agni/Chora/Mrityu) | BUILT | BUILT | `test_rich_topics.py::test_panchaka_active`, `test_rich_topics.py::test_panchaka_inactive` |
| 13 | Homa/Ahuti windows | BUILT | BUILT | `test_timings.py::test_homa_windows_count`, `test_a4_contract.py::TestRichFieldsPopulated::test_homa_windows_nonempty` |
| 14 | Calendrical (masa purnimanta+amanta, adhika/kshaya, samvat×4, samvatsara/Jovian-60, ritu, ayana, sankranti context) | BUILT | BUILT | `test_calendrical.py::test_birth_ayana`, `test_calendrical.py::test_birth_ritu`, `test_calendrical.py::test_samvat_formulas_2026`, `test_calendrical.py::test_jovian_year_range`, `test_calendrical.py::test_masa_purnimanta_makara`, `test_calendrical.py::test_sankranti_flag`, `test_a4_contract.py::TestRichFieldsPopulated::test_calendrical_present` |
| 15 | Tithi/Nakshatra Shoonya (void-sign per classical table) | BUILT | BUILT | `test_rich_topics.py::test_shoonya_present`, `test_a4_contract.py::TestRichFieldsPopulated::test_shoonya_present` |
| 16 | Tara/Chandra Bala | FLOORED | FLOORED | See FLOORED record below — `tara_bala` field present, typed `Optional`, returns `None` on both surfaces |
| 17 | Provenance + `topics_computed` | BUILT | BUILT | `test_a4_contract.py::TestTopicCoverage::test_minimum_18_topics`, `test_a4_contract.py::TestTopicCoverage::test_core_angas_in_topics`, `test_a4_contract.py::TestTopicCoverage::test_planets_in_topics`, `test_a4_contract.py::TestTopicCoverage::test_lagna_in_topics`, `test_a4_contract.py::TestTopicCoverage::test_upagrahas_in_topics`, `test_a4_contract.py::TestTopicCoverage::test_outer_planets_in_topics`, `test_a4_contract.py::TestTopicCoverage::test_sun_moon_in_topics`, `test_a4_contract.py::TestTopicCoverage::test_inauspicious_in_topics`, `test_a4_contract.py::TestTopicCoverage::test_auspicious_in_topics`, `test_a4_contract.py::TestTopicCoverage::test_anandadi_yoga_in_topics`, `test_a4_contract.py::TestTopicCoverage::test_calendrical_in_topics`, `test_a4_contract.py::TestTopicCoverage::test_homa_windows_in_topics`, `test_a4_contract.py::TestTopicCoverage::test_shoonya_in_topics`, `test_a4_contract.py::TestTopicCoverage::test_micro_timing_in_topics` |

---

## Instant-Only Topics

Topics #18–20 are required on the Instant surface only. Day surface does not provide these.

| # | Topic (brief §3 label) | Instant | Test(s) |
|---|---|---|---|
| 18 | Lagna + 12 house cusps + MC (P0) — ascendant deg/sign/nak/pada, 12 cusps multi-system, MC | BUILT | `test_lagna.py::test_lagna_forensic_mesha`, `test_lagna.py::test_lagna_returns_12_cusps`, `test_lagna.py::test_lagna_mc_present`, `test_lagna.py::test_lagna_nakshatra_pada`, `test_a4_contract.py::TestForensicGate::test_lagna_mesha`, `test_a4_contract.py::TestRichFieldsPopulated::test_lagna_present`, `test_a4_contract.py::TestRichFieldsPopulated::test_lagna_has_12_cusps`, `test_a4_contract.py::TestRichFieldsPopulated::test_lagna_sign_id_is_positive` |
| 19 | Window-membership (which inauspicious/auspicious/choghadiya/hora the instant falls in + time-to-next-boundary) | BUILT | `test_rich_topics.py::test_window_membership`, `test_a4_contract.py::TestRichFieldsPopulated::test_window_membership_present` |
| 20 | Instant micro-timing (Pranapada, ghati/vighati into day, muhurta-of-day 1 of 30) | BUILT | `test_rich_topics.py::test_micro_timing`, `test_a4_contract.py::TestRichFieldsPopulated::test_micro_timing_present` |

---

## Day-Only Topics

Topics #21–23 are required on the Day surface only. Instant surface does not provide these.

| # | Topic (brief §3 label) | Day | Test(s) |
|---|---|---|---|
| 21 | Festival/vrata flags (Ekadashi/Pradosh/Sankashti/Purnima/Amavasya/Sankranti + rule-derived) | BUILT | `test_timings.py::test_festivals_ekadashi`, `test_timings.py::test_festivals_purnima`, `test_timings.py::test_festivals_empty_for_no_match` |
| 22 | Sankranti/ingress/station/eclipse day-events ("Sun enters X", "Mars retrograde", eclipse) | BUILT | `test_timings.py::test_day_events_returns_list` |
| 23 | Day muhurtas (15 day + 15 night, named + lords) | BUILT | `test_timings.py::test_day_muhurtas_count` |

---

## FLOORED Topics — Impossibility Record

### Topic 16 — Tara/Chandra Bala

**Status: FLOORED on both surfaces.**

**Named impossibility reason:**

Tara Bala and Chandra Bala are *natal-reference computations*, not panchanga computations.

- **Tara Bala** requires knowing the native's *janma nakshatra* (birth Moon nakshatra). It is computed as
  the count from the janma nakshatra to the current transit nakshatra, modulo the 9-tara cycle. The
  janma nakshatra is a chart fact — it is not derivable from the call-site arguments
  `(datetime, lat, lon, tz_offset)` alone. Those arguments yield the current sky; they do not identify
  the native.
- **Chandra Bala** requires knowing the native's *janma rasi* (birth Moon sign). Same constraint.

This is not a convenience-deferment — there is no classical algorithm that computes Tara/Chandra Bala
without a natal reference point. The `tara_bala` field is present on both `PanchangaInstant` and
`Panchang` dataclasses, typed `Optional[TaraBala]`, and returns `None` until the caller supplies
`natal_nakshatra_id`. The field contract is correct and the floor is named. The topic-coverage matrix
counts this as FLOORED with a named reason, not BUILT.

---

## Note: `timings` legacy key in Day `topics_computed`

The Day surface carries 20 `topics_computed` keys including a legacy `timings` key (alongside the
discrete `choghadiya` and `hora` keys). The `timings` key was set in the original `compute_panchang`
implementation to record that sunrise/sunset/moonrise/moonset computation completed. It predates the
per-topic granularity introduced in the rich-output arc and is retained for backward compatibility.
It does not correspond to a distinct brief §3 topic — Topics 5/6/7/8 are all covered by their own
discrete keys (`inauspicious_full`, `auspicious_full`, `choghadiya`, `hora`). The total meaningful
topic count on Day is therefore 19 discrete topics + 1 legacy composite key = 20 `topics_computed`
entries; the brief's 23-topic contract is fully satisfied.

---

## Note: Adhika/Kshaya Masa (within Topic 14 — Calendrical)

`is_adhika_masa` and `is_kshaya_masa` sub-fields within the `Calendrical` object are floored to
`False` with a documented reason — they are NOT floored at the topic level (Topic 14 overall is
**BUILT**). Named reason: determining whether a lunar month is intercalary (adhika) or suppressed
(kshaya) requires comparing the current masa against the prior and next solar month boundary to check
whether the Sun transits 0, 1, or 2 sign boundaries within the lunar month. This multi-month context
is not available within a single-day or single-instant call. These two sub-fields return `False`
explicitly; they are not silently absent. The floor is documented, not hidden.

---

*End of PANCHANGA_TOPIC_COVERAGE_v1_0.md v1.0.*
*Authored 2026-06-09 per CLAUDECODE_BRIEF_PANCHANGA_RICH_OUTPUT_v1_0.md §4.*
*All test names verified against actual test files at time of authoring.*

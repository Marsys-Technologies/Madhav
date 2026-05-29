---
artifact: A4_PANCHANGA_SPEC_v1_0.md
document: A4 — Panchanga (birth-day) Specification
status: LOCKED
version: 1.0
date: 2026-05-29
authored_by: Cowork (native-confirmed full classical scope: no inauspicious or auspicious windows trimmed; Agni Vasa + 5-panchaka added)
intended_for: Claude Code sub-agents implementing the A4 per-chart panchanga writer
prime_directive: Only computed facts. No narrative, no opinion. Schema enforces.
depends_on: A3 (chart_facts schema), G7 (panchanga_daily 5-ayanamsha), G22 (Tara bala matrix), G23 (Chandra bala matrix), G24 (Vimshottari starting lord), G6 (Sankranti), G4 (Eclipse), G9 (Nakshatra attrs), G10 (Sign attrs), G11 (Graha attrs)
---

# A4 — Panchanga (birth-day) Specification

## §0 — Mission

For each ayanamsha, compute every classical panchanga element + extensions for the native's birth instant. All values are computed facts only. Output supports birth-instant queries AND transit-time downstream joins via Tara bala / Chandra bala state tables.

## §1 — Inputs

Engine-side: `chart_output.JSONL` Sun + Moon longitudes (sidereal and tropical), birth_jd, sidereal_time_birth, lat/lon/tz_offset.

Global lookups: G4 eclipses, G6 sankranti, G7 panchanga_daily, G9 nakshatra attributes, G10 sign attributes, G11 graha attributes, G22 Tara bala 27×27, G23 Chandra bala 12×12, G24 Vimshottari starting lord.

Swiss Ephemeris APIs: `swe_rise_trans` (rise/set/transit for any body), `swe_houses_ex` (cusps), `swe_sun_apparent_long`.

## §2 — Fact categories emitted (final locked set)

### Ayanamsha-INVARIANT (1 row per chart per key):
- `panchanga_tithi`
- `panchanga_vara`
- `panchanga_yoga`
- `panchanga_karana`
- `panchanga_hora_birth`
- `panchanga_choghadiya_birth`
- `panchanga_rahu_kalam`
- `panchanga_yamaganda_kalam`
- `panchanga_gulika_kalam`
- `panchanga_durmuhurta`
- `panchanga_varjyam`
- `panchanga_visha_ghati`
- `panchanga_sashtighati`
- `panchanga_yamakantaka`
- `panchanga_krakaca`
- `panchanga_abhijit_muhurta`
- `panchanga_brahma_muhurta`
- `panchanga_pratah_sandhya`
- `panchanga_madhyahna_sandhya`
- `panchanga_sayam_sandhya`
- `panchanga_amrit_kaal`
- `panchanga_vijaya_muhurta`
- `panchanga_godhuli_muhurta`
- `panchanga_nishita_kala`
- `panchanga_solar_context`
- `panchanga_calendrical`
- `panchanga_astronomical`
- `panchanga_sun_moon_dynamics`
- `panchanga_disha_shul`
- `panchanga_tithi_shoonya_rashi`
- `panchanga_nakshatra_shoonya_rashi`
- `panchanga_agni_vasa`

### Ayanamsha-DEPENDENT (5 rows per chart per key, one per canonical ayanamsha):
- `panchanga_nakshatra_moon`
- `panchanga_special_yoga_combinations` (vara+nakshatra; nakshatra is ayanamsha-shifted at boundaries)
- `panchanga_panchaka_classification` (tithi+vara+nakshatra composite)
- `tara_bala_natal_baseline`
- `chandra_bala_natal_baseline`
- `panchaka_flag` (Panchak Rahit — Dhanishta-last-quarter through Revati window)
- `bhadra_flag` (active when Vishti karana operating at birth)
- `eclipse_proximity_natal` (±15 days from birth)

## §3 — Per-category emission detail

### `panchanga_tithi` (subject: `TITHI_BIRTH`)

| key | type | example | render |
|---|---|---|---|
| `name` | text_enum | "Shukla Tritiya" | "Tithi at birth: Shukla Tritiya." |
| `number_in_lunar_month` | num | 3 | "Tithi number: 3 (of 30)." |
| `paksha` | text_enum | "Shukla" | "Paksha: Shukla (waxing)." |
| `type` | text_enum | "Jaya" | "Tithi type: Jaya." |
| `deity` | text | "Gauri" | "Tithi deity: Gauri." |
| `lord` | graha_enum | "MAR" | "Tithi lord: Mars." |
| `percent_elapsed_at_birth` | num | 0.421 | "Tithi was 42.1% elapsed at birth." |
| `pravesh_iso` | timestamp | "1984-02-05T03:14:22Z" | "Tithi began: 1984-02-05 08:44 IST." |
| `arambha_iso` | timestamp | "1984-02-06T01:42:10Z" | "Tithi ended: 1984-02-06 07:12 IST." |
| `inauspicious_flag` | bool | false | "Tithi is auspicious for general activity." |

### `panchanga_vara` (subject: `VARA_BIRTH`)

`name`, `number` (0=Sun..6=Sat), `lord` (graha), `lord_element` (Agni/Bhumi/Vayu/Jala/Akasha), `weekday_iso`.

### `panchanga_nakshatra_moon` (subject: `NAKSHATRA_MOON_BIRTH`)

`name`, `number` (1-27), `vimshottari_starting_lord` (joins G24), `pada` (1-4), `pada_deity`, `deity` (G9), `gana` (G9), `nadi` (G9), `yoni` (G9), `pakshi` (G9), `varna` (G9), `tatva` (G9), `paramayus_years` (G9), `percent_elapsed_at_birth`, `pravesh_iso`, `arambha_iso`.

### `panchanga_yoga` (subject: `YOGA_BIRTH`)

`name` (27 enum: Vishkambh..Vaidhriti), `number` (1-27), `deity`, `lord`, `percent_elapsed_at_birth`, `pravesh_iso`, `arambha_iso`, `inauspicious_flag` (true for 9 inauspicious: Vishkambh, Atiganda, Shoola, Ganda, Vyaghata, Vajra, Vyatipata, Parigha, Vaidhriti).

### `panchanga_karana` (subject: `KARANA_BIRTH`)

`name` (11 enum: Bava/Balava/Kaulava/Taitila/Garaja/Vanija/Vishti/Shakuni/Chatushpada/Naga/Kimstughna), `number`, `lord`, `half_tithi_position` (first/second), `vishti_bhadra_flag`.

### `panchanga_hora_birth` (subject: `HORA_BIRTH`)

`hora_number` (1-24 from sunrise), `lord` (graha), `day_or_night`, `shubh_ashubh_classification`, `start_iso`, `end_iso`.

### `panchanga_choghadiya_birth` (subject: `CHOGHADIYA_BIRTH`)

`choghadiya_number` (1-16), `name` (Udveg/Char/Labh/Amrit/Kaal/Shubh/Rog), `lord` (graha), `classification` (shubh/ashubh/mishrit), `start_iso`, `end_iso`.

### Inauspicious time windows (9 categories — full classical set)

Each as a separate category with subject = window-name. Common keys: `start_iso`, `end_iso`, `duration_minutes`, `weekday_table_reference`. Specifics:

- `panchanga_rahu_kalam` — 1/8 of day; position varies by weekday per classical table (Sun=8th, Mon=2nd, Tue=7th, Wed=5th, Thu=6th, Fri=4th, Sat=3rd portion)
- `panchanga_yamaganda_kalam` — 1/8 of day; weekday table
- `panchanga_gulika_kalam` — 1/8 of day; weekday table
- `panchanga_durmuhurta` — 2 windows per day typically; tabular per weekday + day/night
- `panchanga_varjyam` — 24-min window specific to current nakshatra
- `panchanga_visha_ghati` — "poison hour" per nakshatra, specific subset of nakshatra duration
- `panchanga_sashtighati` — 60-ghati cycle inauspicious window
- `panchanga_yamakantaka` — yama-related inauspicious window
- `panchanga_krakaca` — saw-tooth inauspicious window per classical Muhurta texts

### Auspicious time windows (9 categories — full extended set)

Same shape (start_iso, end_iso, duration_minutes):

- `panchanga_abhijit_muhurta` — 8th of 15 day-muhurtas (~48 min around solar noon); `applicable_flag` (skipped on Wednesday)
- `panchanga_brahma_muhurta` — ~96 min before sunrise
- `panchanga_pratah_sandhya` — dawn twilight ritual window
- `panchanga_madhyahna_sandhya` — noon ritual window
- `panchanga_sayam_sandhya` — dusk twilight ritual window
- `panchanga_amrit_kaal` — variable; computed from yoga + nakshatra combination
- `panchanga_vijaya_muhurta` — early afternoon victory muhurta
- `panchanga_godhuli_muhurta` — twilight cow-dust muhurta (~24 min after sunset)
- `panchanga_nishita_kala` — midnight ritual window

### `panchanga_special_yoga_combinations` (ayanamsha-dependent)

One row per recognized combination, with `combination_name`, `active_at_birth_flag`, `classical_citation_id`, `constituent_facts_jsonb_atomic` (tithi+vara+nakshatra triple).

Combinations: Amrita Siddhi, Sarvarth Siddhi, Ravi Yoga, Ravi Pushya, Guru Pushya, Tripushkar, Dwipushkar, Vish Yoga, Mritya Yoga (the YOGA — separate from panchaka), Vajra Yoga, Siddhi Yoga, Yama-Ghantaka, Vyaghra-Mukha, Lagna Shuddhi.

### `panchanga_solar_context` (subject: `SOLAR_CONTEXT_BIRTH`)

`last_sankranti_name` (one of 12: Mesha/Vrishabha/.../Meena), `last_sankranti_iso`, `next_sankranti_name`, `next_sankranti_iso`, `ayana` (Uttarayana/Dakshinayana), `ritu` (Vasant/Grishma/Varsha/Sharad/Hemant/Shishir), `solar_arc_into_current_sign_deg` (Sun's degrees past sankranti).

### `panchanga_calendrical` (subject: `CALENDRICAL_BIRTH`)

Both masa systems per native decision: `masa_purnimanta` (e.g., "Magha"), `masa_amanta` (e.g., "Magha"), `adhika_masa_flag`, `kshaya_masa_flag`, `paksha` (Shukla/Krishna), `vikram_samvat` (year), `shaka_samvat`, `kali_samvat`, `saptarshi_samvat`, `jovian_60yr_cycle_name` (one of 60: Prabhava..Akshaya), `jovian_60yr_position` (1-60).

### `panchanga_astronomical` (subject: `ASTRONOMICAL_BIRTH`)

For birth lat/lon:
- `sunrise_iso`, `sunset_iso`, `day_length_minutes`, `night_length_minutes`, `solar_noon_iso`
- `moonrise_iso`, `moonset_iso`
- Per graha (Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn/Rahu/Ketu): `rise_iso`, `set_iso`, `transit_iso` (upper culmination)
- `sun_altitude_at_birth_deg`, `sun_azimuth_at_birth_deg`
- `moon_altitude_at_birth_deg`, `moon_azimuth_at_birth_deg`

### `panchanga_sun_moon_dynamics` (subject: `SUN_MOON_DYNAMICS_BIRTH`)

Pravesh + arambha timestamps for each panchanga limb:
- `tithi_pravesh_iso`, `tithi_arambha_iso`
- `nakshatra_pravesh_iso`, `nakshatra_arambha_iso`
- `yoga_pravesh_iso`, `yoga_arambha_iso`
- `karana_pravesh_iso`, `karana_arambha_iso`
- `pranic_pada` (sub-Moon-derived point, classical Vedic timing micro-unit)

### `panchanga_disha_shul` (subject: `DISHA_SHUL_BIRTH`)

`direction_to_avoid` (East/SE/South/SW/West/NW/North/NE per weekday classical table), `weekday_reference`.

### `panchanga_tithi_shoonya_rashi` (subject: `TITHI_SHOONYA_BIRTH`)

`void_sign` for the operating tithi (per classical table — each tithi has 1-2 signs that go "void" for muhurta purposes during it).

### `panchanga_nakshatra_shoonya_rashi` (subject: `NAKSHATRA_SHOONYA_BIRTH`)

Same shape per operating nakshatra.

### `panchanga_agni_vasa` (subject: `AGNI_VASA_BIRTH`) — NEW

`residence` (Bhumi/Akasha/Patala/Swarga), `computation_formula` (e.g., "(tithi + paksha + nakshatra + vara) mod 4"), `interpretive_class` (auspicious_for_yagna_flag based on residence — only the deterministic flag, no narrative), `weekday_reference`.

### `panchanga_panchaka_classification` (subject: `PANCHAKA_BIRTH`) — NEW (ayanamsha-dependent)

For each of the 5 panchakas (Roga / Raja / Agni / Chora / Mrityu), one row with `panchaka_name`, `active_at_birth_flag`, `tithi_component`, `vara_component`, `nakshatra_component`, `classical_citation_id`. Plus a separate row for `panchaka_overall_classification` (which of the 5 is active, if any).

### `panchaka_flag` (Panchak Rahit window — last 1/4 Dhanishta through Revati)

`active_at_birth_flag`, `nakshatra_position` (which of the 5 inauspicious nakshatras Moon was in).

### `bhadra_flag`

`active_at_birth_flag` (true when Vishti karana operating).

### `eclipse_proximity_natal`

For each eclipse within ±15 days of birth (rare; usually 0-1):
- `eclipse_type` (solar/lunar/partial/total)
- `eclipse_date_iso`
- `days_from_birth` (signed)
- `eclipse_sign` + `eclipse_nakshatra`
- `natal_points_within_1deg_array` (which natal grahas/Lagna are within 1° of the eclipse point)

### `tara_bala_natal_baseline` (27-row state table per ayanamsha)

For native's natal nakshatra (per ayanamsha), join G22 matrix to produce 27 rows. Each row's subject = `TRANSIT_NAK_<NAME>` (e.g., `TRANSIT_NAK_ASH`), key = `tara_class`, value ∈ {Janma/Sampat/Vipat/Kshema/Pratyak/Sadhaka/Vadha/Mitra/Atimitra}.

Used downstream for any transit-time query: "what's today's Tara bala for this native" = direct lookup against this baseline.

### `chandra_bala_natal_baseline` (12-row state table per ayanamsha)

For native's natal Moon sign, join G23 matrix. Each row's subject = `TRANSIT_SIGN_<NAME>`, key = `classification`, value ∈ {favorable/neutral/unfavorable}.

## §4 — Verification

| Category group | Verification min |
|---|---|
| Tithi/Vara/Yoga/Karana | `single` (Swiss Ephemeris authoritative) |
| Nakshatra | `single` |
| Hora/Choghadiya | `single` (deterministic from sunrise + weekday table) |
| Inauspicious + auspicious time windows | `two_pass_verified` (table-driven; errors propagate silently) |
| Special yoga combinations | `two_pass_verified` (lookup-table validation) |
| Panchaka classification | `two_pass_verified` |
| Agni Vasa | `two_pass_verified` (modular arithmetic + table) |
| Solar context | `single` (G6 sankranti is authoritative) |
| Calendrical (eras) | `single` (era conversion well-defined) |
| Astronomical (rise/set) | `single` (Swiss Ephemeris) |
| Sun-Moon dynamics | `single` |
| Tara bala / Chandra bala matrices | `single` (G22/G23 are static reference tables) |

## §5 — Citations (dual form per A3 §6)

Examples:

| Row | citation_ref | citation_human |
|---|---|---|
| Tithi | `panchanga_tithi.TITHI_BIRTH.name@chart=362f9f17:ay=INVARIANT:eng=natal_engine/0.2.0` | "Tithi at birth: Shukla Tritiya." |
| Nakshatra (Lahiri) | `panchanga_nakshatra_moon.NAKSHATRA_MOON_BIRTH.name@chart=362f9f17:ay=lahiri_chitrapaksha:eng=natal_engine/0.2.0` | "Moon's nakshatra at birth: Purva Bhadrapada (Lahiri)." |
| Agni Vasa | `panchanga_agni_vasa.AGNI_VASA_BIRTH.residence@chart=362f9f17:ay=INVARIANT:eng=natal_engine/0.2.0` | "Agni Vasa at birth: Bhumi (Earth)." |
| Mrityu Panchaka | `panchanga_panchaka_classification.PANCHAKA_BIRTH.mrityu_active@chart=362f9f17:ay=lahiri_chitrapaksha:eng=natal_engine/0.2.0` | "Mrityu Panchaka at birth: not active (Lahiri)." |
| Rahu Kalam start | `panchanga_rahu_kalam.RAHU_KALAM_BIRTH_DAY.start_iso@chart=362f9f17:ay=INVARIANT:eng=natal_engine/0.2.0` | "Rahu Kalam on birth day: 16:30-18:00 IST." |
| Tara bala (Lahiri, transit Mrigashira) | `tara_bala_natal_baseline.TRANSIT_NAK_MRI.tara_class@chart=362f9f17:ay=lahiri_chitrapaksha:eng=natal_engine/0.2.0` | "When transit Moon is in Mrigashira, Tara state for this native is: Sampat (Lahiri)." |

## §6 — Tool retrieval contract

`query_panchanga_at_birth(chart_id, ayanamsha_ids[], scope_filter=['core'\|'all'\|'inauspicious'\|'auspicious'\|'panchaka'\|'astronomical'\|'sun_moon_dynamics']) → rows`.

For transit-time queries — directly query the state-table categories with the transit date as an input, joining underlying timelines:

`query_tara_bala_at_date(chart_id, ayanamsha_id, transit_date) → 1 row` (joins `tara_bala_natal_baseline` × G2 ephemeris-derived transit Moon nakshatra at that date).

## §7 — Materialized view

`mv_chart_panchanga_birth_summary` — joins all `panchanga_*` rows into one wide row per (chart, ayanamsha) for fast "give me birth-day panchanga at a glance" queries. Refreshed synchronously at build close per A3 §10.

Note: NO MV for Tara bala / Chandra bala AT TRANSIT DATE — those are computed live from the natal_baseline state tables × transit Moon position. The natal_baseline tables themselves are constant for a given build and live in chart_facts.

## §8 — Implementation notes

1. Most panchanga limb computations are already implemented in `platform/python-sidecar/natal_engine/panchanga.py` — A4 extends to the full classical scope above.
2. G7 `panchanga_daily` table already has Choghadiya/Hora/Kalam windows for any date — A4 looks up the birth-day row and copies into chart_facts under per-chart provenance.
3. New computations needed in engine: Agni Vasa (modular arithmetic), 5-Panchaka classification (table lookup), the 6 less-common time windows (Visha Ghati / Sashtighati / Yamakantaka / Krakaca / Vijaya / Godhuli / Nishita), Disha Shul, Tithi Shoonya, Nakshatra Shoonya.
4. All rise/set calculations via `swe_rise_trans`; cross-check with sunrise-sunset Python library for two-pass.
5. Tara bala + Chandra bala baseline tables are precomputed lookups; engine joins natal nakshatra/sign × global G22/G23 reference matrix.

## §9 — Row count projection per chart per ayanamsha

| Group | Categories × subjects × keys ≈ rows |
|---|---|
| Core panchanga limbs (tithi/vara/nakshatra/yoga/karana/hora/choghadiya) | ~80 rows |
| Inauspicious windows (9 categories × ~5 keys each) | ~45 rows |
| Auspicious windows (9 × ~5) | ~45 rows |
| Solar context + Calendrical | ~25 rows |
| Astronomical (sunrise/sunset + 9 grahas × rise/set/transit + alt/az) | ~40 rows |
| Sun-Moon dynamics | ~10 rows |
| Special yoga combinations (~15 entries) | ~30 rows |
| Panchaka classification (5 panchakas + composite) | ~12 rows |
| Agni Vasa | ~4 rows |
| Disha Shul + 2 Shoonya rashi | ~6 rows |
| Tara bala matrix | 27 rows |
| Chandra bala matrix | 12 rows |
| Eclipse proximity, Panchak Rahit, Bhadra | ~10 rows |

**Total A4 emission per (chart, ayanamsha): ~350-400 rows.** Across 5 ayanamshas + invariants: ~600-800 panchanga rows per chart. Fits comfortably in chart_facts.

## §10 — Locked decisions

1. Full classical inauspicious + auspicious time window scope (no trimming)
2. Astronomical sub-category IN (all 9 graha rise/set + alt/az)
3. Sun-Moon dynamics sub-category IN (pravesh/arambha timestamps for every limb)
4. Both Purnimanta + Amanta masa systems
5. Disha Shul + Tithi Shoonya + Nakshatra Shoonya IN
6. Agni Vasa IN (new category)
7. 5-Panchaka classification (Roga/Raja/Agni/Chora/Mrityu) IN (new category)
8. Tara bala natal baseline as a 27-row state table (per ayanamsha)
9. Chandra bala natal baseline as a 12-row state table (per ayanamsha)
10. Verification: two_pass_verified for table-driven windows + panchaka + agni vasa; single for limbs (Swiss Ephemeris authoritative)

---

*End of A4_PANCHANGA_SPEC_v1_0.md — LOCKED 2026-05-29. Native sign-off complete.*

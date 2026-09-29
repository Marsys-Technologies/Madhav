---
artifact: LEL_CHART_STATE_RECONCILED
version: "1.0"
status: CURRENT
date: 2026-09-29
author: "Stream B (Śāstra)"
---

# LEL Chart-State Reconciliation v1.0

Derived artifact. Regenerates the chart-state annotations carried inside the Life Event
Log (LEL) from the authoritative layers (L0 ephemeris positions, L1 `chart_facts`),
per Pravāha measurement task B4.1. **No LEL file was edited.** The LEL
(`01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`) was read-only throughout; this file is the
only file written. CLAUDE.md §B.10 honoured: every position below comes from the L0
evidence appendix E8 (sealed doctrine v3.0) or from L1 `chart_facts` queried
read-only; nothing is from memory.

## §1 Method and sources

**Sources.**

- **L0 (transits):** sealed doctrine v3.0 evidence appendix **E8** — Lahiri sidereal
  longitudes for 2013-12-11, 2018-11-28, 2022-01-03 (all 9 grahas), cited as
  "E8 <date>".
- **L1 (natal):** `chart_facts`, `chart_id='482012f1-710e-4a25-994a-93821f5871aa'`,
  `build_id='1c092ffb-72eb-4614-8422-552ca6eae985'`. Cross-checked live via the
  read-only postgres MCP tool on 2026-09-29 (READ-ONLY `select` only). Query used
  (schema-adapted — `build_id` is a uuid column, not text):

  ```sql
  select fact_key, fact_value_text, fact_value_num from chart_facts
  where chart_id='482012f1-710e-4a25-994a-93821f5871aa'
    and build_id='1c092ffb-72eb-4614-8422-552ca6eae985'
    and fact_key='longitude_sidereal';
  ```

  Lahiri values returned match the L1 natal table exactly: Lagna 12.4311, Sun
  291.9626, Moon 327.0552, Mars 198.5192, Mercury 270.8388, Jupiter 249.7875,
  Venus 259.1882, Saturn 202.4320, Rahu 49.0330, Ketu 229.0330. Natal facts are
  therefore DB-confirmed, not just table-asserted.

- **LEL under audit:** `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (2289 lines). The
  companion `01_FACTS_LAYER/LIFE_EVENT_LOG_FACTS_ONLY_v1_0.md` (962 lines) carries
  no chart-state annotation blocks and was out of scope for annotation audit.

**Conventions.** Sign of longitude λ: `floor(λ/30)` → 0 Aries, 1 Taurus, 2 Gemini,
3 Cancer, 4 Leo, 5 Virgo, 6 Libra, 7 Scorpio, 8 Sagittarius, 9 Capricorn,
10 Aquarius, 11 Pisces. House from Lagna: count inclusively from the lagna sign
(Lagna 12.43° → Aries). House from Moon: count inclusively from the natal Moon sign
(Moon 327.06° → Aquarius). "E8 <date>" cites the E8 table; "L1" cites the natal
table above.

**Verdicts.** CONFIRMED / CORRECTED (old → new, with arithmetic) / UNSUPPORTED
(assertion L0/L1 cannot ground) / [U] = needs an L0 query to settle; the exact
query is stated.

## §2 The three worked events — annotation-by-annotation reconciliation

### §2.1 Marriage — EVT.2013.12.11.01 (LEL lines 886–913)

E8 2013-12-11: Sun 235.56, Moon 348.50, Mars 157.81, Mercury 225.78,
Jupiter 84.57 R, Venus 272.87, Saturn 204.25, Rahu 192.99, Ketu 12.99.

| # | LEL file:line | Verbatim old text | Recomputed value | Arithmetic | Verdict |
|---|---|---|---|---|---|
| M1 | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md:904` | `"Saturn transit 9H from Moon (Libra)"` | Saturn Libra; Libra = 9H from natal Moon | E8: Saturn 204.25 → floor(204.25/30)=6 → Libra. From Aquarius (10): Libra (6) is (6−10 mod 12)+1 = 9th | CONFIRMED (sign from E8, house arithmetic correct) |
| M2 | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md:904` | `"Saturn transit Libra = 7H from Lagna"` | Libra = 7H from Aries | (6−0)+1 = 7 | CONFIRMED |
| M3 | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md:904` | `"Jupiter transit Gemini = 3H from Lagna"` | Gemini = 3H from Aries | E8: Jupiter 84.57 → floor=2 → Gemini. (2−0)+1 = 3 | CONFIRMED |
| M4 | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md:906` | `"Jupiter retro in Gemini"` | Jupiter retrograde in Gemini | E8 flags Jupiter 84.57 **R**; 84.57 → Gemini | CONFIRMED |
| M5 | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md:905,907` | eclipse list and `ashtakavarga_SAV_transit_sign: "Sat=23, Jup=28, Sun=29, Moon=27"` | not checkable from E8/L1 | eclipse longitudes and SAV matrices are not in the supplied data | [U] query: `ref_planet_position_get` for the four eclipse dates; SAV from L1 ashtakavarga table (if materialised) |

No sign/house error exists in the marriage block. Note transit Moon on 2013-12-11
was Pisces (E8: 348.50 → floor=11); the block makes no transit-Moon claim, so
nothing to correct.

### §2.2 Father's passing — EVT.2018.11.28.01 (LEL lines 983–1010)

E8 2018-11-28: Sun 222.07, Moon 112.22, Mars 313.75, Mercury 219.43 R,
Jupiter 220.31, Venus 183.83, Saturn 253.43, Rahu 93.92, Ketu 273.92.

| # | LEL file:line | Verbatim old text | Recomputed value | Arithmetic | Verdict |
|---|---|---|---|---|---|
| F1 | `:1000` | `sade_sati_phase: null (Sade Sati Cycle 2 starts Jan 2020, ~2 months after event)` | SS C2 Rising starts 2020-01-24 (per LEL `:1062`), which is **≈ 14 months** after 2018-11-28 | 2018-11-28 → 2020-01-24 = 13 months 27 days ≈ 14 months | **CORRECTED**: "~2 months" → "≈14 months". The null phase verdict itself stands (Saturn 253.43 → floor=8 → Sagittarius = 11th from natal Moon Aquarius: (8−10 mod 12)+1 = 11, i.e. not 12/1/2, so Sade Sati indeed not active) |
| F2 | `:1001` | `"Saturn transit Sagittarius = 9H from Lagna — CLASSICAL FATHER-DEATH TRIGGER"` | Saturn Sagittarius = 9H from Aries | E8: 253.43 → floor=8 → Sagittarius. (8−0)+1 = 9 | CONFIRMED |
| F3 | `:1001` | `"Jupiter transit Scorpio 10°16' conjunct Sun 11°50' + Mercury retro 09°44' — heavy stellium in 8H from Lagna (death house)"` | Sun, Mercury(R), Jupiter all Scorpio = 8H from Aries; quoted arc-minutes are approximate | E8: Sun 222.07 → 222.07−210 = 12.07° = 12°04' Sco (annotated 11°50', −14'); Jupiter 220.31 → 10.31° = 10°19' Sco (annotated 10°16', −3'); Mercury 219.43 R → 9.43° = 9°26' Sco (annotated 09°44', +18'). All floor=7 → Scorpio; (7−0)+1 = 8 | CONFIRMED for sign/house/retrograde; **CORRECTED** (minor) for the quoted degrees-minutes — E8 values are 12°04', 10°19', 9°26' respectively |
| F4 | `:1001` | `"Ketu transit Capricorn 05°14' — on 10H natal Sun+Mercury stellium"` | Ketu Capricorn, on natal 10H Sun+Mercury | E8: Ketu 273.92 → floor=9 → Capricorn; 273.92−270 = 3.92° = 3°55' (annotated 05°14', ~1.3° off). L1: natal Sun 291.96 → Capricorn, natal Mercury 270.84 → Capricorn; Capricorn = (9−0)+1 = 10H from Aries | CONFIRMED for sign/house/conjunction-by-sign; **CORRECTED** (minor) degree 5°14' → 3°55' |
| F5 | `:1001` | `"Saturn transit 11H from Moon (Sagittarius)"` | Sagittarius = 11H from Aquarius | (8−10 mod 12)+1 = 11 | CONFIRMED |
| F6 | `:1003` | `"Mercury retrograde in Scorpio (conjunct Sun + Jupiter)"` | Mercury R Scorpio, same sign as Sun+Jupiter | E8: Mercury 219.43 **R**, Scorpio (F3) | CONFIRMED |
| F7 | `:1002,1004` | eclipse list; SAV string | not checkable | as M5 | [U] same queries as M5 |

Transit Moon on 2018-11-28: E8 Moon 112.22 → floor=3 → Cancer (4H from Lagna,
6th from natal Moon). The block makes no transit-Moon claim — nothing to correct.

### §2.3 Twin daughters — EVT.2022.01.03.01 (LEL lines 1134–1161)

E8 2022-01-03: Sun 258.91, Moon 269.14, Mars 230.71, Mercury 277.45,
Jupiter 306.87, Venus 267.83 R, Saturn 288.01, Rahu 36.87, Ketu 216.87.

| # | LEL file:line | Verbatim old text | Recomputed value | Arithmetic | Verdict |
|---|---|---|---|---|---|
| T1 | `:1152` | `"Rahu transit Aries = 1H Lagna (identity-amplification at parenthood)"` | Rahu transit **Taurus = 2H from Lagna**, conjunct natal Rahu by sign (Rahu return) | E8: Rahu 36.87 → floor(36.87/30)=1 → Taurus, not Aries. (1−0)+1 = 2H. L1: natal Rahu 49.03 → Taurus — same sign | **CORRECTED**: "Aries = 1H" → "Taurus = 2H (on natal Rahu)" |
| T2 | `:1152` | `"Ketu transit Libra = 7H (partnership-house axis active)"` | Ketu transit **Scorpio = 8H from Lagna** | E8: Ketu 216.87 → floor=7 → Scorpio, not Libra. (7−0)+1 = 8H | **CORRECTED**: "Libra = 7H" → "Scorpio = 8H" |
| T3 | `:1152` | `"Jupiter transit Aquarius = 11H AND ON NATAL MOON (gajakesari-class children transit)"` | Jupiter Aquarius = 11H, on natal Moon | E8: Jupiter 306.87 → floor=10 → Aquarius. (10−0)+1 = 11. L1: natal Moon 327.06 → Aquarius | CONFIRMED |
| T4 | `:1152` | `"Saturn transit Capricorn = 10H from Lagna, 12H from Moon (Sade Sati Rising)"` | Saturn Capricorn = 10H / 12H-from-Moon | E8: Saturn 288.01 → floor=9 → Capricorn. (9−0)+1 = 10; (9−10 mod 12)+1 = 12 | CONFIRMED (also `:1151` sade_sati_phase C2.P1 consistent) |
| T5 | `:1154` | `"None of the 5 classical retrograders retrograde at event"` | **Venus is retrograde** at event | E8 flags Venus 267.83 **R** (Sagittarius, 9H) | **CORRECTED**: statement is false per E8 → "Venus retrograde in Sagittarius (9H); Mars, Jupiter, Saturn, Mercury direct" |
| T6 | `:1155` | `ashtakavarga_SAV_transit_sign: "Sat=32(Cap), Jup=24(Aqu on Moon), Sun=31(Sag), Moon=27(Pis); ..."` | transit Moon is **Sagittarius**, not Pisces; SAV integers not checkable | E8: Moon 269.14 → floor=8 → Sagittarius (9H from Lagna), not Pisces. Sun 258.91 → Sagittarius ✓ (Sun annotation correct). SAV integers need L1 SAV table | **CORRECTED** for Moon sign (Pis → Sag); SAV numbers [U]: L1 ashtakavarga SAV query for Cap/Aqu/Sag/Sag |
| T7 | `:1153` | `"Lunar Partial Taurus 2021-11-19 (-45d) — ON natal Rahu 2H"` and `"Solar Partial Taurus 2022-04-30 (+117d) — ON natal Rahu 2H again"` | natal Rahu is Taurus, 2H | L1: Rahu 49.03 → floor=1 → Taurus; (1−0)+1 = 2H | CONFIRMED (eclipse longitude itself [U]: `ref_planet_position_get` 2021-11-19 / 2022-04-30 Sun+Moon) |
| T8 | `:1153` | `"Solar Total Sagittarius 2021-12-04 (-30d) — ON natal 9H Jupiter+Venus"` | natal Jupiter+Venus in Sagittarius = 9H | L1: Jupiter 249.79 → floor=8 Sag; Venus 259.17 → floor=8 Sag; (8−0)+1 = 9H | CONFIRMED (eclipse position [U] as T7) |
| T9 | `:1153` | `"Lunar Total Scorpio 2022-05-16 (+133d) — ON natal 8H Ketu"` | natal Ketu in Scorpio = 8H | L1: Ketu 229.03 → floor=7 → Scorpio; (7−0)+1 = 8H | CONFIRMED — note this line *internally contradicts* T10 below |
| T10 | `:1159` | `"Ketu in 5H Leo natally (children's house) is typically a delayed/unusual-child signal..."` | natal Ketu is **Scorpio, 8H** — not 5H Leo | L1: Ketu 229.03 → floor=7 → Scorpio; (7−0)+1 = 8H from Aries. 5H from Aries is Leo — Ketu is not there | **CORRECTED**: "Ketu in 5H Leo" → "Ketu in Scorpio 8H". The "delayed/unusual-child" retrodiction resting on 5H-Ketu loses its stated basis and must be re-grounded or dropped (also `:1161` "Ketu-5H delayed-child signature" same correction) |
| T11 | `:1158` | `"SIG.10 (Rahu 2H — Rahu AD classically multiplies/doubles/produces-unusual — TWINS fit Rahu's 'multiplication' signature exactly)"` | positional core: natal Rahu Taurus = 2H ✓ (L1, as T1). The "Rahu multiplies → twins" retrodiction is annotation/doctrine interpretation | L1 confirms Rahu 2H. No L0/L1 table grounds "multiplies → twins" | positional claim CONFIRMED; interpretive claim **UNSUPPORTED** (annotation, not L0/L1-groundable) |
| T12 | `:1160` | `"Jupiter transit aspecting 11H/5H"` | Jupiter occupies Aquarius = 11H ✓ (T3); "aspecting 5H" is an unstated aspect rule | E8 confirms the occupancy; the aspect claim invokes a doctrine rule not in L0/L1 data supplied | occupancy CONFIRMED; aspect clause **UNSUPPORTED** |

## §3 The known-wrong four, explicitly resolved

1. **"Rahu transit in Aries" (twins event).** WRONG. E8 2022-01-03 Rahu 36.87° →
   floor(36.87/30) = 1 → **Taurus** (2H from Lagna, on natal Rahu 49.03° Taurus).
   LEL `:1152` corrected per T1.
2. **"Moon in Pisces" (twins event).** WRONG. E8 2022-01-03 Moon 269.14° →
   floor(269.14/30) = 8 → **Sagittarius** (9H from Lagna). LEL `:1155` corrected
   per T6.
3. **"Natal Ketu in Leo (5H)."** WRONG. L1 natal Ketu 229.03° → floor(229.03/30) =
   7 → **Scorpio**, (7−0)+1 = **8H** from Aries Lagna. LEL `:1159` and `:1161`
   corrected per T10. (DB-confirmed against `chart_facts`, §1.)
4. **"Jan 2020 ≈ 2 months after Nov 2018."** WRONG date arithmetic. 2018-11-28 →
   2020-01-24 = 13 months 27 days ≈ **14 months**. LEL `:1000` corrected per F1.

## §4 Inventory of remaining chart-state annotations

All other `chart_state_at_event` blocks in `LIFE_EVENT_LOG_v1_2.md`. House
arithmetic is checked against Lagna Aries / Moon Aquarius; the transit *signs*
themselves need L0 for dates outside the E8 table and are marked [U] with the
query. Verdict "arith ✓" = the house claim is correct *given* the stated sign.

| LEL lines | Event | Annotation content | Verdict |
|---|---|---|---|
| `:164` | birth 1984-02-05 | "Saturn transit 9H from Moon (Libra)", "Libra = 7H", "Jupiter Sagittarius = 9H" | arith ✓ (Libra=9th from Aq ✓, 7th from Ar ✓, Sag=9th ✓); signs [U]: `ref_planet_position_get('1984-02-05', saturn, jupiter)` |
| `:151` | birth | "Aries Lagna, Moon in Aquarius, Sun in Capricorn" | CONFIRMED via L1 (Lagna 12.43 Ar; Moon 327.06 Aq; Sun 291.96 Cap) |
| `:197` | 1995 headaches | "Saturn Pisces = 12H", "Jupiter Scorpio = 8H" | arith ✓; signs [U]: `ref_planet_position_get('1995-06-01', saturn, jupiter)` |
| `:196,229,1639,1668` | 1995–1998 | "Cycle1_approx_peak_Saturn_Aquarius (~1995-1998)" | [U]: Saturn Aquarius ingress/egress dates c. 1993–2000 via `ref_planet_position_get` sweep; not groundable from supplied data |
| `:230` | 1998-02-16 | "Jupiter/Ketu transit on natal Moon (Aquarius)", "Saturn Pisces = 12H", "Jupiter Aquarius = 11H" | arith ✓; conjunction claims [U]: `ref_planet_position_get('1998-02-16', jupiter, ketu, saturn)` |
| `:288-289` | 2001-03 | "Saturn Taurus = 2H", "Jupiter Taurus = 2H", post-Sade-Sati | arith ✓ and internally consistent (Taurus = past Pisces); signs [U] |
| `:319,352` | 2003/2004 | "Saturn Gemini = 3H", "Jupiter Cancer = 4H / Leo = 5H" | arith ✓; signs [U] |
| `:414,474,505` | 2007 | "Rahu transit on natal Moon (Aquarius)", "Saturn Cancer = 4H", "Jupiter Scorpio = 8H" | arith ✓; Rahu-conjunction [U]: `ref_planet_position_get('2007-06-10', rahu, saturn, jupiter)` |
| `:535,566` | 2008/2009 | "Saturn 7H from Moon (Leo)", "Leo = 5H", "Jupiter Aquarius = 11H on natal Moon" | arith ✓ (Leo = 7th from Aq ✓); signs [U] |
| `:599,630,661,692` | 2010–2011 | "Saturn Virgo = 6H", "Jupiter Pisces = 12H / Aries = 1H" | arith ✓; signs [U] |
| `:723,781,811,842,873` | 2012–2013 | "Saturn 9H from Moon (Libra)", "Libra = 7H", "Jupiter Taurus = 2H / Gemini = 3H" | arith ✓; signs [U] |
| `:937` | 2016 | "Ketu transit on natal Moon (Aquarius)", "Saturn Scorpio = 8H", "Jupiter Leo = 5H" | arith ✓; Ketu claim [U]: `ref_planet_position_get('2016-06-01', ketu)` |
| `:968` | 2017-03 | "Saturn Sagittarius = 9H", "Ketu on natal Moon", "Jupiter Virgo = 6H" | arith ✓; signs [U]: `ref_planet_position_get('2017-03-01', saturn, ketu, jupiter)` |
| `:1031-1032` | 2019-05 | "Sade Sati Cycle 2 starts Jan 2020" (no interval claim), "Saturn Sag = 9H", "Jupiter Scorpio = 8H" | arith ✓; no faulty arithmetic present; signs [U]: `ref_planet_position_get('2019-05-15', saturn, jupiter)` |
| `:1062-1063` | 2021-01 | C2.P1 "Saturn in Capricorn = 12th from Moon; 2020-01-24 to 2022-04-28"; "Saturn/Jupiter Capricorn = 10H" | arith ✓ ((9−10 mod 12)+1=12 ✓, 10H ✓); ingress dates [U] |
| `:1085-1130` | 2021 proxies | key_transits `saturn_sign: Capricorn`, `jupiter_sign: Capricorn/Aquarius`, `rahu_sign: Taurus` | [U]: `ref_planet_position_get('2021-04-01'/'2021-09-01', saturn, jupiter, rahu)` — note rahu_sign Taurus is *consistent* with E8 2022-01-03 Rahu Taurus (node moves ~19°/yr retrograde) but must be settled by query |
| `:1174-1190` | 2022-06 proxy | key_transits `rahu_sign: Aries` | [U]: `ref_planet_position_get('2022-06-01', rahu)` — check against the T1 finding (Rahu entered Aries only later in 2022) |
| `:1211-1212` | 2022-10 | C2.P2→P3; "Saturn Capricorn = 10H", "Jupiter Pisces = 12H" | arith ✓; signs [U] |
| `:1243-1337` | 2023–2024 | C2.P4 "Saturn Aquarius = 11H", "Jupiter Aries = 1H" | arith ✓; signs [U]: `ref_planet_position_get` per event date |
| `:1367-1459,1575-1576,1843-1844,1873-1874` | 2025–2026 | C2.P5 "Saturn Pisces = 12H", "Jupiter Gemini = 3H / Cancer = 4H", "Rahu transit on natal Moon (Aquarius)" | arith ✓; Rahu-on-Moon [U]: `ref_planet_position_get('2025-06-01', rahu)` etc. |
| `:1433-1436,1493-1496,1521-1524,1550-1553` | 2025–2026 proxies | key_transits `rahu_sign: Aquarius` | [U]: `ref_planet_position_get` per proxy date |
| `:1843` vs `:1367` | 2025 | "Saturn in Pisces 12H from Moon, began ~Jan 2025" vs "2025-03-30 to 2027-06-02" | internal inconsistency flagged (Jan 2025 vs 2025-03-30); settle via [U]: Saturn Pisces ingress date `ref_planet_position_get` sweep Mar 2025. Note ":1843" also says "12H from Moon" for Pisces — from Aquarius Moon, Pisces is 2nd, not 12th; "12H from Lagna" is the correct frame (Pisces = 12th from Aries ✓). **CORRECTED (frame label)**: Pisces = 12H from Lagna, 2H from Moon |
| all `:eclipses_within_6mo` and `:ashtakavarga_SAV_transit_sign` rows | all events | eclipse sign lists; SAV integers | [U]: eclipse longitudes via `ref_planet_position_get` per listed date; SAV values need the L1 ashtakavarga table (not in supplied data) |

## §5 Honest limits

- **Dasha, Yogini, Chara, and Sade-Sati phase boundaries** (`vimshottari_*`,
  `yogini_*`, `chara_*`, `TRS.SS.*` ingress dates) were not recomputed: they need
  the dasha engines / full L0 time series, not three E8 snapshots. None were
  verdicted except the F1 date arithmetic and frame checks explicitly shown.
- **SAV integers and eclipse lists** are unchecked everywhere ([U] with queries
  stated); no SAV table was available in the supplied L1 extract, and the DB
  session was used only to verify natal longitudes.
- **Only three event dates have E8 ground truth.** Every other event's transit
  *signs* are marked [U]; their house arithmetic is verified conditional on the
  stated sign, which is why so many rows read "arith ✓; signs [U]".
- **Degree-minute quotes** in `:1001` (F3/F4) deviate from E8 by up to ~1.3°;
  corrected values shown, but a future pass should decide whether the LEL's
  minutes came from a different ephemeris/ayanamsha snapshot and normalise the
  citation.
- **Interpretive claims** (e.g. "Rahu multiplies → twins", T11; Jupiter-aspect
  clause, T12) are marked UNSUPPORTED rather than false: they are doctrine-layer
  annotations and belong in a doctrine register, not in computed chart state.
- **A future pass needs:** (a) `ref_planet_position_get` for every [U] date in §4;
  (b) the L1 SAV/ashtakavarga table; (c) dasha-engine outputs to verify the
  `vimshottari_id`/`yogini_id`/`chara_id` references; (d) a doctrine citation for
  any interpretive claim retained in the LEL. The LEL itself remains untouched;
  corrections live only in this derived file.

---
artifact: BOUNDARY_FLIP_REPORT
version: 1.2
status: DRAFT-FOR-REVIEW
produced_by: exec-suvarna
date: 2026-10-02
lane: suvarna/land/TI-ephemeris-flip-report-001
base: origin/main 57bcef8c9
mode: OFFLINE, READ-ONLY. DB reads only (suvarna_reader, through a wrapper that only sources ~/.config/suvarna/pgenv.sh and runs psql). No DB write, no repo code change, no push.
precondition_for: any L1 / panchanga_daily rebuild after the ephemeris-backend fix (INVESTIGATION_EPHEMERIS_BACKEND_v1_0.md, branch suvarna/land/TI-ephemeris-backend-001)
gate: G-FLIP CLEARED for the canonical chart (SS decision N-64, recorded in section 0A)
evidence_dir: /Users/Dev/suvarna-evidence/TrackI/ephemeris_flip/ (not in the repo; README.md there lists every script and output)
changelog:
  - "1.2 (2026-10-02): detector, per-lane attribution hooks, schema README and self-test committed in the repo (s_l1_attribution_hooks/); SS standing rule: every S-L1 fix PR adds its own hook; guessed Daridra regex removed, no placeholder hooks."
  - "1.1 (2026-10-02): SS N-64 rulings recorded (section 0A): dasha shift = accuracy refinement; Mahadasha day-crossing verified; S-L1 acceptance criterion; detector packaged (--snapshot / --compare); pre-rebuild snapshot of 482012f1 taken (path and sha256 below); G-EPH Linux check recorded; S-L1b hand-offs."
  - "1.0 (2026-10-02): first full comparison of production-state Moshier vs pinned Swiss .se1 for the three charts and the stored panchanga_daily window."
---

**ANCHOR STATUS: ALL SEVEN FORENSIC ANCHORS ARE UNCHANGED UNDER THE .se1 FILES. NO ALERT.** Sun = Capricorn, Moon = Purva Bhadrapada, Lagna = Aries (all 5 ayanamshas), Tithi = Shukla Tritiya, Vara = Ravivara, Yoga = Shiva, Karana = Garaja. The repo's own FORENSIC gates (ga_positions x5, ga_panchanga, ga_sensitive x5) all PASS on the .se1 run. Smallest anchor margin: 3,267 arcsec (Tithi / Karana); largest backend movement of any input: 0.665 arcsec (Moon).

# Boundary-flip report: Moshier (production state) vs Swiss .se1

## 0. Bottom line

1. **Zero classification-level flips.** Not one sign, nakshatra, pada, tithi, yoga, karana, vara, house, special-lagna, upagraha, KP star/sub/sub-sub/prana lord or varga sign (30 vargas, 10 bodies, 5 ayanamshas) changes between Moshier and .se1, in any of the three charts (about 10,940 class facts each), nor in the 544 stored `panchanga_daily` days (3,808 class facts). A negative control (birth time +180 min, same detector) reports 3,769 flips, so the detector can read true.
2. **What does change is time.** Every Vimshottari start moves by one uniform amount (native +6,993 s = +1 h 56 m 33 s; chart 2 -1,795 s; chart 3 +5,910 s), Kalachakra by about 0.4 to 1.7 days, Mudda by up to 43 s; Yogini, Ashtottari, Chara, Naisargika and Narayana do not move. So **every Vimshottari/KP/Kalachakra start changes "to the minute"** and some cross a calendar-day boundary: about 2-8% of Vimshottari starts (IST day), nearly all Kalachakra starts (section 3.2).
3. **Continuous values move by at most 0.665 arcsec for a graha** (Moon, native), at most 17.9 arcsec for an amplified derived point (Sree Lagna = 27 x Moon fraction).
4. **Fragility is real but thin:** 10 / 13 / 18 facts (native / chart 2 / chart 3) sit within 2 arcsec of a class boundary (several are clusters hanging on one longitude, most are deep vargas or KP prana lords). One is a genuine razor edge: chart 3, Saturn under Raman is 0.52 arcsec from a pada / navamsa boundary, and chart 3's Moon under Lahiri is 0.03 arcsec from a KP prana-lord boundary under .se1 (section 5).
5. **The Moshier run reproduces production** for every family that is current code (facts bit-exact to 1e-9 deg, all but one of 1.46 million dasha starts exact to the second, 544/544 daily rows). Two stored families do not reproduce for charts 2 and 3: their `chart_divisionals` rows predate two later fixes (section 6.2). That is independent of the backend question, and a rebuild will change them either way.

## 0A. Rulings (SS N-64)

SS decision N-64: **G-FLIP is CLEARED for the canonical chart `482012f1`.** The rulings below are recorded as given; verification I ran for them is stated next to each.

### (1) The dasha shift is an accuracy refinement, not a flip

Ruling: every dasha-start change is the arithmetic consequence of the Moon moving 0.665 arcsec (0.665 / 48,000 of a 16-year Vimshottari period = 1.385e-5 x 504,921,600 s = about 6,994 s; observed +6,993 s), far inside birth-time uncertainty. Recorded per-system shifts (Swiss minus Moshier, details in 3.2):

| system | native | chart 2 | chart 3 |
|---|---|---|---|
| Vimshottari (uniform) | +6,993 s | -1,795 s | +5,910 s |
| Kalachakra | mode +1.68 d | mode -0.38 d | mode +1.14 d (0.4 to 1.7 days across charts) |
| Mudda | <= 43 s | <= 43 s | <= 43 s |
| Yogini, Ashtottari, Chara, Naisargika, Narayana | none | none | none |

**Mahadasha day-crossing check (native, Vimshottari; paired Moshier / .se1 rows, `out/md_daycross_native.json`):**
- **Lahiri (canonical ayanamsha): no Mahadasha start crosses a UTC or an IST calendar day.** All nine lords' starts of one 120-year cycle are covered: Jupiter 1975-08-18, Saturn 1991, Mercury 2010, Ketu 2027, Venus 2034, Sun 2054, Moon 2060, Mars 2070, Rahu 2077 (each +6,993 s, all within the same UTC and IST day; the table in 3.2 lists the times); the window holds 12 shifted MD starts in all (Jupiter 2095 closes the cycle), all clear. The clipped window-start row (1950-01-01) does not move.
- True Chitra and Surya Siddhanta: also none (13 and 12 MD rows, 0 UTC / 0 IST crossings).
- **The statement does not hold for two non-canonical ayanamshas, and the ruling should know it:** Krishnamurti, 1 of 13 MD starts crosses an IST day (Moon 2060-07-06 17:01:51 -> 18:58:23 UTC) and 2 cross a UTC day (Rahu 1957 and 2077, 23:01:51 -> 00:58:23 UTC); Raman, 4 of 12 cross an IST day (Mercury 2008, Venus 2032, Sun 2052, Mars 2068: 17:54:25 -> 19:50:57 UTC on a 22 Nov) and 4 cross a UTC day (Jupiter 1973 and 2093, Saturn 1989, Ketu 2025: 23:54:25 -> 01:50:57 UTC).
- **Antardasha day-crossing rate (native, IST day):** Lahiri 3 of 104 (2.9%; UTC 0), True Chitra 10 of 104 (9.6%; UTC 7), Krishnamurti 12 of 104 (11.5%; UTC 14), Raman 9 of 102 (8.8%; UTC 9), Surya Siddhanta 1 of 101 (1.0%; UTC 12). Lahiri Pratyantardasha 79 of 923 (8.6%), Sukshma 661 of 8,148 (8.1%).

**Consumers of dasha start timestamps (grep survey over `platform/` and `platform-mcp/`, not a line-by-line audit; I ran none of them):**
- Day-resolution consumers read the DATE columns (`start_date`/`end_date`, a UTC date) and change only when a start crosses a UTC day, i.e. at the rates above (Lahiri MD: never): TS `kala_dasha_sandhi_get` (`platform-mcp/src/tools/kala_views/dasha_sandhi.ts`, serves period start/end dates "verbatim" from `get_dashas`), and the Python `ka_dasha_kala` (service, tree_walk), `ka_avadhi`, `ka_jivana_parva`, `ka_taranga`, `ka_temporal/date_resolver`, `ph_rectification`.
- Timestamp-resolution consumers read `start_iso`: `now.ts` sandhi bands (band width = max(1 day, 3% of the period), so a 2 h shift sits inside the band), `kala_uncertainty.ts` (Sukshma boundary served as +/- half the period's own duration), `gochara_grammar/dasha_data`, `ka_kshetra/stage3_clocks`, `ka_sangam`.
- Conclusion, matching the ruling with one qualification: a ~2 h shift is visible by itself only to sandhi-hour questions (a question that asks whether an instant lies within hours of a boundary). Everything else sees it only on a day crossing, and the writers that persist date-derived rows (the day-resolution list above) will change those rows when a boundary crosses a day, which is exactly what the post-run compare in (2) catches and attributes. The `kala_dasha_sandhi_get` test anchors (Jupiter MD 2019-02-07 etc.) are served-verbatim fixtures; none of the three charts has a Jupiter MD start on that date.

### (2) S-L1 acceptance criterion (added)

After the S-L1 run, re-run the same class-flip detector on the ACTUAL rebuilt canonical output versus the pre-rebuild snapshot. Expected: **zero class flips from the backend**; every other difference attributed to a named ruled change (argala, tiers, Gandanta, F-A2, Daridra, band table). **Any unattributed class change: stop the wave and go to SS. A changed FORENSIC anchor = ALERT.**

Detector, hooks and self-test are committed in the repo: **`00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks/`** (`flip_detector.py`, `README.md` with the exact hook schema, `test_flip_detector.py`, one `<lane>.json` per lane). Standing rule (SS): **every S-L1 mandatory fix PR adds its own hook file in that folder in the same PR**; a lane with no hook file is a blocker the S-L1 REVIEW must flag (`--require-lanes` fails the run). The detector is read-only (SELECT only) with the same entry points:
- `--snapshot native|<chart uuid>` captures the current production class-level state (every `chart_facts` row with its verification tier, every `chart_divisionals` row, every `chart_dashas` row, `panchanga_daily`) into a gzip JSON plus a `.sha256`.
- `--compare <snapshot>` reads production again, attributes every class / tier / dasha-row-set difference to a lane via ALL `*.json` hooks in the folder (exact table, category, fact key, ayanamsha, change type; optional `expected_count`; `dasha_shift` entries declare the ruled start shifts), and reports continuous values and timestamps separately. Exit **0** clean; **2** unattributed change, unattributed dasha shift, expectation mismatch, invalid hook, or missing required lane (stop, go to SS); **3** FORENSIC anchor changed (ALERT, wins over 2).
- `--validate-hooks [--require-lanes ...]` lints the hook files without database access.
- Seeded with the two lanes whose categories are grounded in the stored data: `argala.json` (argala_natal_matrix, virodha_argala_natal_matrix, net_argala_per_varga) and `gandanta.json` (graha_gandanta / is_gandanta). The earlier guessed Daridra pattern is removed; F-A2, Daridra, band table, tiers, ephemeris and formula-pin hooks are **absent on purpose** and are written by their own fix PRs. The ephemeris lane declares the ruled backend dasha shift through a `dasha_shift` entry (e.g. Lahiri Vimshottari 6,990 to 6,996 s); without it the shift is UNATTRIBUTED.
- Self-tests: `test_flip_detector.py` (12 offline tests: identical -> clean; attributed change names its lane; unattributed class change, tier change, dasha shift and dasha row-set change stop the wave; continuous / timestamp changes are separated; expectation mismatch stops; anchor change is an ALERT that wins over unattributed and is native-only; chart-scoped hooks; strict hook validation rejecting empty placeholders, patterns, wrong stems and unknown fields; read-only guard refusing non-SELECT) passes; a live `--compare` of the repo detector against the fresh snapshot reports 0 changes, 0 unattributed, anchors 7 of 7 OK, exit 0 (production unchanged between snapshot and compare).

**Pre-rebuild snapshot of the canonical chart `482012f1` (taken now, read-only):**
- path: `/Users/Dev/suvarna-evidence/TrackI/ephemeris_flip/snapshots/pre_rebuild_482012f1_2026-10-01.json.gz`
- sha256: `0a92f79249f53103afbb1edac6986e417aaa2368d58336b96aa93451128dc455`
- taken 2026-10-01T19:50:18Z (2026-10-02 01:20 IST) as `suvarna_reader`; contents: 143,299 `chart_facts` rows, 24,392 `chart_divisionals` rows, 483,869 `chart_dashas` rows (scope-cap sentinel excluded), 544 `panchanga_daily` rows. These are the Moshier-state values that section 6 shows the offline Moshier run reproduces.

### (3) Families not compared

Strength, structural, tajaka, sade sati, yoga, condition and the other vargas families (section 8) are covered by the post-run compare, not by more offline work now: `--compare` diffs all 219 stored `chart_facts` categories of the canonical chart, plus divisionals, dashas and the daily table.

### (4) G-EPH is still open

The report ran on macOS arm64 (section 7.1). **G-EPH must still be verified on the deployed Linux image**: that the Linux image really resolves `.se1` after the backend fix (probe flag = `SWIEPH` for Sun..Saturn, all planetary calls `SWIEPH`), using the same flag probe and call recorder as `backend_ctl.py`. This report does not establish it.

### (5) Charts 2 and 3: hand-offs to the S-L1b brief

- Stale varga rows of charts 2 and 3 (5.5 h planet offset and the Krishnamurti / Surya Siddhanta -> Lahiri ayanamsha fallback, section 6.2): S-L1b brief.
- Razor-edge facts (section 5): chart 3 Saturn under Raman 0.52 arcsec from a pada / navamsa boundary; chart 3 Moon KP prana lord under Lahiri 0.03 arcsec (Mars 0.02, Ketu under Raman 0.03): S-L1b brief.
- **S-L1b gets its own flip report from actual output, and SS informs the owner before it runs.** The same detector applies: take `--snapshot 1c826d5a` and `--snapshot cb73cd3d` immediately before S-L1b (not taken now). Note that the chart 2 and 3 varga rows will change for the 6.2 reasons regardless of the backend, so their hooks need a "6.2 stale rows" entry.

## 1. Summary table

Compared = present in both the Moshier and the .se1 run. Class facts = text or integer-valued classification facts (sign, nakshatra, nakshatra lord, pada, house, tithi/yoga/karana/vara ids and names, special-lagna and upagraha signs and padas, varga signs, KP lords). Continuous facts = longitudes, degrees, distances. Dasha "rows" = `chart_dashas` rows paired between the two runs by (ayanamsha, system, level, lord path, nearest start).

| | native `482012f1` | chart 2 `1c826d5a` | chart 3 `cb73cd3d` | `panchanga_daily` (544 days) |
|---|---|---|---|---|
| Birth parameters | stated (1984-02-05 10:43 IST Bhubaneswar; 20.27 N 85.84 E) | recovered by inversion from stored L1 facts (section 7.2) | recovered by inversion (section 7.2) | stored observer 20.27 N 85.84 E, +330 min |
| Class facts compared | 10,960 | 10,939 | 10,938 | 3,808 (7 per day) |
| **Class facts FLIPPED** | **0** | **0** | **0** | **0** |
| FORENSIC anchors (7) OK under .se1? | **7 of 7 OK** | n/a (native-only anchors) | n/a | n/a |
| Continuous facts compared / changed | 1,951 / 1,409 (max 17.95 arcsec, Sree Lagna) | 1,952 / 1,408 (max 4.10 arcsec) | 1,951 / 1,408 (max 12.14 arcsec) | Moon at sunrise up to 1.76 arcsec |
| Time-valued facts (anga end times at birth) compared / changed | 46 / 12 (max 2 s) | 46 / 0 | 46 / 10 (max 1 s) | tithi/nakshatra/yoga/karana end: 343 to 382 days changed, max 4 s; sunrise 2 days, 1 s |
| Dasha rows paired | 482,605 | 470,044 | 504,432 | n/a |
| Dasha start changed at minute resolution | 85,831 | 88,028 | 86,519 | n/a |
| Dasha start crosses UTC day / IST day | 36,982 / 37,095 | 12,881 / 13,351 | 35,424 / 35,413 | n/a |
| Dasha rows existing in only one backend (Moshier-only / .se1-only) | 1,264 / 1,249 | 1,723 / 1,689 | 916 / 924 | n/a |
| Facts within 2 arcsec of a class boundary (ephemeris-sensitive) | 10 | 13 | 18 | 0 (closest 8.96 arcsec) |
| Moshier run reproduces stored production? | yes, all families | yes, except `chart_divisionals` (explained) | yes, except `chart_divisionals` (explained) | yes, 544/544 |

Dasha systems that do not move at all (every chart): Yogini, Ashtottari, Chara-karaka, Naisargika, Narayana. Systems that move: Vimshottari (and its KP sub-periods), Kalachakra, Mudda (seconds only). Detail in 3.2.

## 2. How far the ephemeris actually moves

Swiss .se1 minus Moshier, arcsec, Lahiri (the other ayanamshas are identical to within 0.0002 arcsec for every body):

| body | native | chart 2 | chart 3 |
|---|---|---|---|
| Sun | +0.0003 | -0.0099 | -0.0587 |
| Moon | **-0.6647** | +0.1517 | -0.4495 |
| Mars | -0.1183 | +0.0031 | -0.0466 |
| Mercury | +0.0156 | -0.0157 | -0.0483 |
| Jupiter | -0.2022 | -0.2944 | -0.0404 |
| Venus | -0.0358 | +0.0520 | -0.0365 |
| Saturn | +0.1515 | +0.0237 | +0.0058 |
| Rahu / Ketu (mean node, analytic) | 0 | 0 | 0 |
| Lagna | 0.0000 | 0.0000 | 0.0000 |

Ayanamsha value: unchanged for Lahiri, Krishnamurti, Raman; True Chitra moves by -0.0055 / -0.0006 / -0.0039 arcsec; Surya Siddhanta by -0.00004 arcsec. Native Moon -0.6647 arcsec reproduces the investigation's -0.665 arcsec figure.

Derived points amplify the Moon: Sree Lagna moves 27 x the Moon fraction (native -17.95, chart 2 +4.10, chart 3 -12.14 arcsec), Vighati Lagna 3.6 arcsec (chart 3), Mrityu sphuta up to 5.3 arcsec (native), sahams up to 1.3 arcsec. No special lagna, upagraha or saham changes class (Section 3.1).

Placidus/Sripati cusps and MC move by at most 0.0055 arcsec (house computation does not need planetary files).

## 3. The flip list

### 3.1 Class-level facts: none

Coverage compared (native; charts 2 and 3 are within 25 facts of these counts): ga_positions 815 (graha_position sign, nakshatra, nakshatra_lord, pada, house_d1, sign_lord, sign_num for 9 grahas + Lagna x 5 ayanamshas; Sripati chalit houses), PyJHora birth panchanga ids 30, ga_panchanga 380 (tithi, vara, yoga, karana, nakshatra_moon, panchaka, tara/chandra bala baselines, shoonya, agni_vasa, hora, choghadiya, bhadra), ga_sensitive 7,485 (all 30 categories: special lagnas, upagrahas, Gulika/Mandi, sahams, arudhas, KP cuspal rows, Yogi/Avayogi, karakas, midpoints, ...; includes the second occurrence of keys the production writers emit twice), ga_vargas 1,850 (sign of 10 bodies in 30 vargas D1..D2700, D2/D3 formula variants, D30 lord, D60 amsa number, x 5 ayanamshas), KP star/sub/sub-sub/prana lords 400.

Result: **no row**. The table the brief asked for (chart, ayanamsha, fact key, Moshier value, Swiss value, delta, distance to boundary) is therefore empty; the closest approaches in the same schema are in section 5.

Negative control (`control_check.json`): the same detector fed the Moshier run against a Moshier run with the birth time moved +180 min reports 3,769 class flips (Lagna Aries -> Taurus, Tithi Shukla Tritiya -> Shukla Chaturthi, house numbers, ...). A zero is therefore not a blind detector.

### 3.2 Dasha starts (changes to the minute)

Moshier-to-.se1 shift (Swiss minus Moshier) per system; "min changed" = start differs at minute resolution; "IST day" = local calendar date of the start changes. All rows in 1950..2100 as stored.

Native:

| system | rows paired | min changed | IST day changed | rows only in one backend (M / S) | shift |
|---|---|---|---|---|---|
| vimshottari (L1-L4) | 45,518 | 45,498 | 3,744 | 146 / 146 | **+6,992 / +6,993 s (+116.55 min)** for every row except the 20 rows clipped at the window start (0 s) |
| vimshottari_kp (sub / sub-sub) | 5,670 | 5,658 | 412 | 0 / 0 | within [0, +6,993] s; 84% of rows at +6,993 s, the rest spread inside that range (window-clipped rows and ambiguous pairing of repeated sub-sub paths; not further resolved) |
| kalachakra | 33,935 | 33,915 | 32,938 | 1,118 / 1,103 | mode +145,089 s (+1.68 d) for 54% of rows; range -4.3 d to +8.1 d (see note) |
| mudda | 102,375 | 760 | 1 | 0 / 0 | -43 s to +1 s |
| yogini, ashtottari, chara_karaka, naisargika, narayana | 83,740; 32,960; 155,135; 21,945; 1,327 | 0 | 0 | 0 / 0 | 0 |

Chart 2: vimshottari 49,697 rows, 49,679 min changed, 991 IST day, shift **-1,795 s (-29.9 min)** (99.96%); vimshottari_kp 6,210 / 6,184 / 129; kalachakra 31,798 / 31,779 / 12,231, mode -33,113 s (37%); mudda 100,230 / 386 / 0 (0 to +1 s); the other five systems 0.
Chart 3: vimshottari 46,127 rows, 46,107 min changed, 3,158 IST day, shift **+5,910 s (+98.5 min)**; vimshottari_kp 5,760 / 5,750 / 357; kalachakra 33,012 / 32,994 / 31,898, mode +98,109 s (56%); mudda 130,108 / 1,668 / 0 (-43 to +1 s); the other five systems 0.

Mechanism (verified against the code): Vimshottari starts are `birth - elapsed fraction of the Moon's nakshatra` plus whole periods, so the whole timeline translates by `(Moon delta / 13 deg 20') x lord_years x 365.25 d`: native 0.6647" / 48,000" x 16 y = 6,993 s, exactly the observed shift. Kalachakra scales the same fraction over its 100-year pada cycle. Yogini, Ashtottari, Naisargika and Chara/Narayana starts carry no Moon-fraction term (the stored Yogini starts all fall on the birth time-of-day, 05:13:00 UTC for the native), which is why they do not move. Mudda follows the Sun's solar-return search (seconds).

Rows that exist in only one backend are sub-day Sukshma rows and window-edge rows: `compute_vimshottari` drops a period when its start date is not before its end date, so a ~2 h shift adds or removes such rows (native Vimshottari 146 each way). For Kalachakra the lord path repeats inside one parent, so some one-to-one pairings are ambiguous; the unpaired count and the spread of shifts there should be read as "structure near the birth-spanning periods shifts non-uniformly", not as 33,915 independent facts.

**Native Vimshottari Mahadasha starts, Lahiri (UTC; none crosses a UTC or IST day):**

| MD | Moshier start | .se1 start | shift |
|---|---|---|---|
| Mars | 1950-08-18 15:50:23 | 1950-08-18 17:46:56 | +6,993 s |
| Rahu | 1957-08-18 09:50:23 | 1957-08-18 11:46:56 | +6,993 s |
| Jupiter | 1975-08-18 21:50:23 | 1975-08-18 23:46:56 | +6,993 s |
| Saturn | 1991-08-18 21:50:23 | 1991-08-18 23:46:56 | +6,993 s |
| Mercury | 2010-08-18 15:50:23 | 2010-08-18 17:46:56 | +6,993 s |
| Ketu | 2027-08-18 21:50:23 | 2027-08-18 23:46:56 | +6,993 s |
| Venus | 2034-08-18 15:50:23 | 2034-08-18 17:46:56 | +6,993 s |
| Sun | 2054-08-18 15:50:23 | 2054-08-18 17:46:56 | +6,993 s |
| Moon | 2060-08-18 03:50:23 | 2060-08-18 05:46:56 | +6,993 s |
| Mars | 2070-08-18 15:50:23 | 2070-08-18 17:46:56 | +6,993 s |
| Rahu | 2077-08-18 09:50:23 | 2077-08-18 11:46:56 | +6,993 s |
| Jupiter | 2095-08-18 21:50:23 | 2095-08-18 23:46:56 | +6,993 s |

(The first stored row, Moon MD at 1950-01-01 00:00:00, is clipped to the window start and does not move.)

**Native Vimshottari Antardasha starts whose IST calendar day changes, Lahiri:** Saturn-Mercury 1994-08-21 16:53:23 -> 18:49:56 UTC; Ketu-Jupiter 2031-08-06 17:38:23 -> 19:34:56 UTC; Sun-Rahu 2055-10-12 16:44:23 -> 18:40:56 UTC (each crosses 18:30 UTC, i.e. IST midnight).

Vimshottari MD + AD starts whose IST day changes, by ayanamsha (native / chart 2 / chart 3): Lahiri 3 / 4 / 11; True Chitra 10 / 8 / 5; Krishnamurti 13 / 0 / 0; Raman 13 / 2 / 9; Surya Siddhanta 1 / 3 / 5. Pratyantardasha (L3) rows with an IST day change, Lahiri: 79 / 20 / 74 of 923 / 1,005 / 918; Sukshma (L4): 661 / 194 / 563.

**Complete per-row lists** (every paired row with both start timestamps, shift in seconds, minute / UTC-day / IST-day flags): `out/dasha_shifts_<chart>.json.gz` (480 k rows each); the rows whose day changes: `out/dasha_date_flips_<chart>.json`. The MD/AD/PD/Sukshma start of every system for every chart and both backends is in `out/<chart>_<backend>_dashas.json`. The report does not reprint 260 k rows. For chart 2 and chart 3 only counts are given here; exact birth-derived dates stay in the evidence directory.

### 3.3 Time-valued birth-panchanga facts

Anga end times at the birth instant (tithi, nakshatra, yoga, karana `end_iso`) move by 0 to 2 s (native: 12 of 46 time-valued facts changed). Stored `panchanga_daily` end times move by up to 4 s (343 to 382 of 544 days per field) and sunrise/moonrise/moonset by up to 1 s (2 / 12 / 28 days). None crosses the class boundary that defines it.

## 4. The seven FORENSIC anchors (native)

| anchor | Moshier | .se1 | margin to the class boundary (.se1, arcsec) |
|---|---|---|---|
| Sun = Capricorn (all 5 ayanamshas) | Capricorn x5 | Capricorn x5 | 18,271 (5.07 deg, smallest of the 5) |
| Moon = Purva Bhadrapada (all 5) | Purva Bhadrapada x5 | Purva Bhadrapada x5 | 11,939 (3.32 deg, smallest of the 5) |
| Lagna = Aries (all 5) | Aries x5 | Aries x5 | 44,752 (12.43 deg) |
| Tithi = Shukla Tritiya | Shukla Tritiya | Shukla Tritiya | 3,267 (0.91 deg; the tithi ends 07:12:47 UTC, birth is 05:13 UTC) |
| Vara = Ravivara | Ravivara | Ravivara | birth is 4 h 21 m after sunrise (sunrise moves at most 1 s) |
| Yoga = Shiva | Shiva | Shiva | 20,464 (5.68 deg) |
| Karana = Garaja | Garaja | Garaja | 3,267 |

The smallest anchor margin (3,267 arcsec) is about 4,900 times the largest backend movement (0.665 arcsec). The PyJHora birth-instant panchanga ids (tithi 3, vara 0, nakshatra 25, yoga 20, karana 6) are also identical.

## 5. Sensitivity: how many facts are one rounding away

"Within X arcsec of a class boundary" is evaluated on the underlying longitude (sign 30 deg, nakshatra 13 deg 20', pada 3 deg 20', varga amsa 30/n deg, tithi 12 deg, yoga 13 deg 20', karana 6 deg, KP lord boundaries from `compute_kp_lords`), taking the nearer of the two backends. Facts that sit exactly on a boundary by construction (Arudha / bhava-arudha / ruling-planet points with degree 0; same longitude in both backends; 375 / 355 / 370 per chart) are excluded and listed separately: they cannot move with the ephemeris, but their classification depends on floating-point handling of 30.0 and is worth a golden test.

Ephemeris-sensitive facts within X arcsec (native / chart 2 / chart 3; one longitude often carries several facts):

| group | <= 2" | <= 10" | <= 60" |
|---|---|---|---|
| core pada (graha, Lagna, special points) | 0 / 0 / 5 | 1 / 0 / 6 | 4 / 9 / 11 |
| core nakshatra | 0 / 0 / 0 | 0 / 0 / 1 | 0 / 1 / 3 |
| KP lords (star / sub / sub-sub / prana, graha) | 2 / 7 / 4 | 16 / 20 / 17 | 55 / 56 / 57 |
| varga D1..D60 family | 1 / 0 / 4 | 5 / 4 / 13 | 27 / 37 / 29 |
| varga D108, D150, D2700 | 7 / 6 / 5 | 24 / 30 / 32 | 65 / 67 / 58 |
| **total <= 2"** | **10** | **13** | **18** |
| `panchanga_daily` (544 days x tithi, yoga, karana, nakshatra, pada, Moon/Sun sign) | 0 | | |

The D2700 and KP-prana counts are geometric, not alarming: a D2700 amsa is 40 arcsec wide and a KP prana-lord bin averages ~66 arcsec, so 2 arcsec is ~5-10% of a bin. Nothing flipped, the backend moves a graha by at most 0.665 arcsec.

The ones to know about (chart, ayanamsha, fact, distance to boundary Moshier / .se1, backend delta):

| chart | ayanamsha | fact | Moshier / .se1 (arcsec) | delta (arcsec) |
|---|---|---|---|---|
| **3** | **Raman** | **Saturn pada (and the navamsa D9, D27, D45, D54, D108 signs, Putrakaraka, Yamaganda sphuta, which all hang on this one longitude)** | **0.524 / 0.530** | +0.0058 |
| **3** | **Lahiri** | **Moon KP prana lord** | **0.48 / 0.03** | -0.4495 |
| 3 | Lahiri | Mars KP prana lord | 0.02 / 0.07 | -0.0466 |
| 3 | Raman | Ketu KP prana lord | 0.03 / 0.03 | 0.0 |
| 3 | Lahiri | Mercury KP prana lord | 1.49 / 1.54 | -0.0483 |
| 3 | Raman | Saham Stri pada | 1.01 / 1.42 | -0.413 |
| native | Lahiri | Mercury KP sub-sub and prana lord | 0.49 / 0.48 | +0.0156 |
| native | Surya Siddhanta | Jupiter D40 sign | 1.69 / 1.89 | -0.2021 |
| 2 | Lahiri | Saturn KP prana lord | 0.33 / 0.31 | +0.0237 |
| 2 | Krishnamurti | Mars KP prana lord | 0.34 / 0.34 | +0.0031 |
| 2 | Surya Siddhanta | Saturn / Ketu KP prana lord | 0.33 / 0.35 and 0.68 / 0.68 | +0.0238 / 0 |
| 2 | Raman | Sun KP prana lord | 0.67 / 0.66 | -0.0099 |
| 2 | Lahiri | Venus KP prana lord | 1.24 / 1.18 | +0.0520 |
| 2 | True Chitra | Lagna KP prana lord | 1.13 / 1.13 | -0.0001 |

D2700 within 2": native 7 (Lahiri Moon, Rahu, Ketu; True Chitra Sun; Raman Lagna, Jupiter, Saturn); chart 2: 6 (Lahiri Mars, Saturn; Raman Venus; Surya Siddhanta Lagna, Rahu, Ketu); chart 3: 4 (Raman Saturn; Surya Siddhanta Sun, Moon, Mars). Full rows: `out/near_le2_rows.json`.

Reading the table: chart 3's Saturn under Raman is 0.53 arcsec from a pada boundary and the backend moves it only 0.0058 arcsec, so the .se1 switch is safe by a factor of ~90; a different Raman constant (not a different ephemeris) would flip nine facts at once. The Moon / Mars / Ketu KP prana rows of chart 3 are closer to the line than any plausible library revision moves them, but the Moon moved 0.45 arcsec toward its boundary on this very switch and stopped 0.03 arcsec short, which is the single most fragile classification in the data set. Core (non-KP, non-deep-varga) closest approaches per chart (arcsec): native 61.5 (Surya Siddhanta Moon sign Aquarius/Pisces and its pada), 124.2 (Raman Mars nakshatra); chart 2 31.0 (Krishnamurti Moon pada), 323.7; chart 3 0.52 (above), 206.9 (Lahiri Ketu/Rahu nakshatra/pada).

`panchanga_daily` closest approaches over 544 days (arcsec, min of the two backends): yoga 8.96 (2027-03-27), nakshatra / Moon pada 13.2 (2026-12-13), karana 18.1 (2026-07-28), tithi 18.9 (2026-07-22), Sun sign 78.9, Moon sign 87.0. The largest Moon movement at sunrise over the window is 1.76 arcsec, so every daily margin exceeds it by at least 5x.

## 6. Does the Moshier run reproduce production?

Yes for every family the current code writes; the exceptions are named and explained. "Bit-exact" below = equal to the stored `numeric` within 1e-9 relative.

### 6.1 Reproduction table (Moshier run vs `suvarna_reader` values)

| family | native | chart 2 | chart 3 |
|---|---|---|---|
| ga_positions + chalit + lagna (graha_position, graha_sign_attributes, house_chalit, bhava_cusps) | 1,205 / 1,205 (max numeric diff 9e-13) | 1,205 / 1,205 | 1,205 / 1,205 |
| ga_panchanga (all stored birth-panchanga facts) | 437 / 437 | 405 / 405 (12 stored rows use the old key name `arambha_iso`; same values as today's `end_iso`) | 403 / 403 (same 12) |
| ga_sensitive (all 30 categories, duplicates included) | 8,775 / 8,775 (35 YAMAKANTAKA rows emitted by current code are absent from the DB) | 8,775 / 8,775 | 8,775 / 8,775 |
| KP lords (graha star/sub/sub-sub/prana) | 200 / 200 | 200 / 200 | 200 / 200 |
| `chart_divisionals` varga signs | **1,750 / 1,750** | **1,222 / 1,700 (478 differ)** | **1,238 / 1,700 (462 differ)**; see 6.2 |
| `chart_dashas`, 9 systems, start_iso to the second | 483,869 / 483,869 (stored has 1 extra scope-cap sentinel row) | 471,767 / 471,767 | 505,348 / 505,348 (one Kalachakra row differs by under a minute, same minute) |
| `panchanga_daily` (544 days) | 544 / 544 class fields; all 8 timestamps to the second; Moon/Sun longitude within 1.8e-5 arcsec (8-decimal storage) | | |

Every Moshier-run value equals the stored production value, and the investigation's bit-exact criterion (stored native Moon `327.055230133129`) is met: the run gives `327.055230133129`.

Backend proof for the runs themselves: before and after every run, a probe on Sun..Saturn returns `MOSEPH` (Moshier run) or `SWIEPH` (.se1 run); in addition every `swe.calc_ut`/`swe.calc` call issued by the repo code (millions per run, dominated by Mudda's solar-return search) was recorded with its return flag, and **all** planetary calls for bodies 0..9 carried `SWIEPH` in the .se1 run and `MOSEPH` in the Moshier run (zero offenders; mean node, body 10, reports `SWIEPH` under both because it is analytic, as the investigation noted). The two Moshier set-ups are equivalent: path = PyJHora's wheel directory (what production's import leaves) and `swe.set_ephe_path(None)` with `SE_EPHE_PATH` unset give bit-identical full `compute_chart` payloads for all three charts and all five ayanamshas (`check_none_vs_wheel.json`).

### 6.2 What does not reproduce, and why (stored chart_divisionals, charts 2 and 3)

Their `chart_divisionals` rows were built 2026-07-26/27; the native's on 2026-09-07. A Moshier run of today's code differs from them on 478 / 462 of 1,700 sign rows. The cause is two defects fixed later, not the ephemeris: (a) before the Nirmana L1-W1 F-A1 fix (documented in the comment above `_compute_varga_positions`) planets were evaluated at the local clock time treated as UT, i.e. 5 h 30 m after birth (stored D1 Moon degree for chart 2 is 16.2260, the same chart's `graha_sign_attributes` Moon is 13.2278); (b) before the 2026-08-04 A1 fix the adapter silently mapped `krishnamurti` and `surya_siddhanta_classical` to Lahiri. Emulating exactly those two behaviours on Moshier reproduces the stored rows of chart 2 and chart 3 with **0 mismatches in 1,450 / 1,450**, while the native (negative control) matches current code 1,500 / 1,500 and not the emulation (490 mismatches) (`repro_varga_oldbug.json`). Consequence for SS: a rebuild changes charts 2 and 3 varga rows regardless of the ephemeris backend, so the backend flip must not be given credit or blame for those diffs.

## 7. Method

### 7.1 Computation (the repo's own code, backend toggled explicitly)

Environment: macOS arm64, Python 3.13.7, pyswisseph 2.10.3.2 (swe 2.10.03, the production pin), PyJHora 4.8.6, repo at the worktree of `origin/main 57bcef8c9`. The three `.se1` files (`sepl_18`, `semo_18`, `seas_18`) were fetched from the production Dockerfile's bucket (`https://storage.googleapis.com/madhav-ephemeris/se1/`) and their SHA-256 equals the digests pinned in `platform/python-sidecar/Dockerfile.pipeline` (`ca1393ce...`, `1ca07bd6...`, `a2cd8fc3...`); the check is repeated at the start of every Swiss run. `.se1` covers 1800 to 2400 CE, which includes all birth years, the dasha window (1950..2100) and the 544 daily dates.

Backend toggle (`backend_ctl.py`): Moshier = `SE_EPHE_PATH` unset and path = PyJHora wheel directory; Swiss = `SE_EPHE_PATH=<pinned .se1 dir>` in the environment (so the `set_ephe_path(None)` calls inside `panchang_engine` also resolve to the files) plus an explicit `swe.set_ephe_path(<.se1 dir>)` after all imports. The probe and the per-call flag recorder are described in 6.1.

Families, each through the production function with only the database write seam patched out (rows captured instead of inserted; FORENSIC gate calls wrapped to record PASS/FAIL instead of raising):
- `ga_positions_writer.build_ga_positions` (5 ayanamshas) -> `compute_chart`; plus a direct `compute_chart` pass for the PyJHora panchanga block, MC, ayanamsha value, retrograde/combust flags.
- `ga_panchanga_writer.build_ga_panchanga` -> `panchang_engine.panchanga_instant`.
- `ga_sensitive_writer.build_ga_sensitive` (all categories, 5 ayanamshas; special lagnas, upagrahas, sahams, arudhas, KP cuspal rows, ...).
- `ga_vargas_writer._compute_varga_positions` (30 vargas x 10 bodies x 5 ayanamshas) with the writer's own `_compute_d2_hora`, `_compute_d3_drekkana`, `_compute_d30_lord`, `_get_d60_amsa_number`.
- `ga_nakshatra_compute.compute_kp_lords` on this run's own longitudes.
- `ga_dashas_writer.build_system(skip_db=True)` for all 8 systems x 5 ayanamshas (plus the KP sub-periods inside `vimshottari`); rows captured at `stabilize_hierarchical_uuids`, i.e. exactly as persisted. Chara and Narayana issue two SELECTs against `chart_facts` for graha signs/degrees and the Lagna sign; an in-memory stand-in serves them from this run's own `ga_positions` facts (equal to the stored ones by 6.1).
- `scripts/panchanga_daily_writer._row_from_panchang` over `compute_panchang` for the 544 stored dates and the stored observer (20.27, 85.84, +330).

Comparison (`compare.py`, `daily_compare.py`): per natural key (domain, ayanamsha, category, subject, key); text compared exactly; integer-valued and listed numeric keys treated as class facts; ISO-timestamp values treated as time facts; everything else continuous. Production writers emit some natural keys more than once with different values (7.3), so every occurrence is kept (suffix `~i`) and compared in emission order. Dasha rows are paired by (ayanamsha, system, level, lord path) then by nearest start within 10 days (ordinal-free, because a 2 h shift adds or removes sub-day rows).

### 7.2 Birth parameters of charts 2 and 3

`suvarna_reader` cannot SELECT `public.charts` (permission denied; the repo's birth-param code reads it), so the parameters were recovered from stored L1 facts and then validated by reproduction (6.1), not read from `public.charts`: (1) the stored Lahiri Moon longitude (double precision, produced on Moshier) was inverted by bisection on `drik.sidereal_longitude` to the UT instant, which lands on a whole second to within 4e-5 s for both charts; (2) the stored Placidus 10th cusp (MC) fixes longitude and the stored Lagna fixes latitude at that instant; both come out as round values (to 1e-9 deg); (3) +5.5 h IST is assumed (consistent with the stored sunrise-dependent facts). Validation: with these parameters, 100% of stored position, panchanga, sensitive-point and KP facts and every one of the 471,767 / 505,348 dasha starts reproduce to the second. The exact recovered values are in `charts.json` in the evidence directory and are deliberately not reproduced in this committed file (third-party birth data); say if you want them inline. Chart 2: 1985, India, same observer coordinates as the native's default; chart 3: 1971, India, a different city.

### 7.3 Production data-integrity observation (outside the brief)

Each chart's stored `chart_facts` holds 460 natural keys with more than one row; for 159 / 127 / 160 of them (native / chart 2 / chart 3) the two rows carry different values (`karaka_chara_position`, `esoteric_point_mrityu`, `esoteric_point_avayogi`, `esoteric_point_yogi`: two builders in `ga_sensitive_writer` emit the same (category, subject, key) with different longitudes; both rows were written inside the same second). The Moshier run emits the same duplicates in the same order and matches both stored rows. A serving read that picks "one row per key" returns one of two contradictory values. This is independent of the backend, but a rebuild is the moment to fix it.

## 8. Unverified

- **Not compared:** `ga_strength`, `ga_structural`, `ga_tajaka`, `ga_sade_sati`, `ga_yoga`, `ga_condition`, `ga_medical`, `ga_prashna`, `ga_vichara`, `ga_ayurdaya`, `ga_vastu`, `ga_transit_anchors`, the other `ga_vargas` row families (dignity, vimsopaka, ashtakavarga, saptavargaja, karakas), and every Bodha/Kala/Phala/Mimamsa asset. Facts purely derived from compared class facts cannot flip when no upstream class flips; facts that embed a transit or return TIME (Tajaka varsha pravesha, Sade Sati phase dates, Kala gochara, Saturn/Sun ingress dates) were not recomputed. Expected size: Saturn ingress times move by minutes (Saturn delta 0.006 to 0.15 arcsec at ~120 arcsec/day), Sun return times by seconds; a date flips only if it lands within that distance of midnight. Not quantified.
- **Cusp KP lords** (`cusp_kp_lords`, from Placidus cusps) were not recomputed; cusps move at most 0.0055 arcsec but their distance to KP boundaries was not measured.
- **Platform:** macOS arm64, not the Linux job image (G-EPH open, section 0A (4)). Bit-exact agreement with production-stored Moshier values supports platform-independence of the Moshier side; the .se1 side was not run on Linux.
- **Dasha pairing for Kalachakra** is imperfect (see 3.2); its counts are upper-bound style, not 33,915 independent facts. Rows "existing in only one backend" mix real sub-day-row removals with Kalachakra pairing ambiguity.
- **Only Lahiri** panchanga_daily at the one stored observer; other observers and dates outside the stored 544-day window were not examined (the daily closest approaches suggest per-day flip odds of roughly 1e-4 or less, but that is an extrapolation).
- **TRUE_NODE** is not used on the L1 paths examined (mean node everywhere); the investigation's ~25 arcsec TRUE_NODE difference was not re-measured here.
- **Birth parameters of charts 2 and 3** are inverted, not read (7.2); +5.5 h is assumed. A wrong time zone with a compensating wall-clock would give the same UT and same positions, and would show only in the sunrise-based facts, which do reproduce.
- **"As stored" assumption:** the stored production values are assumed to be what serving returns; for the 460 duplicate keys per chart (7.3) the run matches both rows, so which one serving picks was not determined.
- **Why Yogini/Ashtottari/Chara/Naisargika/Narayana ignore the Moon fraction** was observed (no shift) and tied to the code only for Yogini (birth time-of-day anchoring); whether that is intended is not assessed here.
- **Sree-Lagna-type amplification** was explained from arithmetic (27 x Moon), not isolated by an ablation.

## 9. Reproduce

```
E=/Users/Dev/suvarna-evidence/TrackI/ephemeris_flip ; PY=/Users/Dev/Vibe-Coding/Apps/Madhav/.venv/bin/python3
$PY $E/collect_chart.py moshier native   # also: swiss | abhinandan | kiran   (~15 min for Moshier: Mudda dominates)
$PY $E/collect_daily.py moshier          # also: swiss
$PY $E/export_db.py native               # reader-only exports; also abhinandan, kiran, daily
$PY $E/compare.py native                 # also abhinandan, kiran;  $PY $E/daily_compare.py
$PY $E/report_numbers.py
```

Key outputs in `$E/out/`: `summary_<chart>.json`, `repro_<chart>.json`, `flips_<chart>.json` (empty lists), `nearflips_<chart>.json`, `near_le2_rows.json`, `dasha_shifts_<chart>.json.gz`, `dasha_date_flips_<chart>.json`, `daily_summary.json`, `control_check.json`, `repro_varga_oldbug.json`, `check_none_vs_wheel.json`, `graha_deltas.json`, `report_numbers.json`.

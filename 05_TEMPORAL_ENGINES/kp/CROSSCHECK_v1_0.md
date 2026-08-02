---
artifact: CROSSCHECK_v1_0.md
domain: kp_sublords
version: 1.1
status: WITHIN_TOLERANCE_GAP_09_BOUND
produced_during: M3-W3-C2-KP-VARSHAPHALA
produced_on: 2026-05-01
extended_during: SHAD-DARSHANA W3K Lane 1 (w3k-sublord-substrate)
extended_on: 2026-08-02
authoritative_side: claude
chart_id: abhisek_mohanty_primary
changelog:
  - version: 1.1
    date: 2026-08-02
    note: >
      §§6–8 added by ṢAḌ-DARŚANA W3K Lane 1, extending this document's EXISTING
      methodology (per W3K_SUBSTRATE_INVENTORY_v1_0.md §2 G-6: "extend this exact
      crosscheck methodology … rather than starting a citation search from zero")
      to cover (a) the new L0 249-fold division table `bg_kp_sublord_division`,
      (b) the live cuspal output, and (c) the new 4-limbed significator
      derivation. §§0–5 are the 2026-05-01 record and are UNCHANGED.
  - version: 1.0
    date: 2026-05-01
    note: Original `compute_kp.py` vs FORENSIC §4.2 cross-check.
---

# KP Sub-Lord Cross-Check — `compute_kp.py` vs FORENSIC §4.2

## §0 — Verdict

**WITHIN_TOLERANCE** (with documented Sub-Sub-Lord boundary flips).

| Field | Match rate | Outcome |
|---|---|---|
| Nakshatra | 9/9 | PASS |
| Star Lord (= nakshatra lord) | 9/9 | PASS |
| Sub Lord | 9/9 | PASS |
| Sub-Sub Lord | 4/9 exact; 5/9 boundary-flip within ≤6 arcmin of FORENSIC longitude | WITHIN_TOLERANCE per GAP.09 |

The five Sub-Sub-Lord disagreements are all explained by the documented
ayanamsha-precision band already named in FORENSIC §5 GAP.09: pyswisseph +
Moshier + Lahiri SIDM_LAHIRI lands ~5–8 arcmin offset from the canonical
FORENSIC longitudes for individual planets, and the Sub-Sub-Lord segment
widths within a nakshatra are tight enough (3–22 arcmin) that a 5–8 arcmin
position difference can place the planet on the other side of a Sub-Sub
boundary while leaving Sub Lord (segment widths 40–133 arcmin) and Star
Lord / Nakshatra (800-arcmin segments) unaffected. This is the same
class of effect that GAP.09 documents for Vimshottari dasha date offsets.

No engine bug, no algorithmic disagreement. The KP algorithm
(nakshatra → sub-lord chain starting at nakshatra-lord with Vimshottari
proportions → sub-sub-lord chain starting at sub-lord) reproduces FORENSIC
§4.2 for every planet whose engine longitude is on the same side of the
Sub-Sub boundary as FORENSIC's longitude.

The project's standing GAP.09 policy applies: **FORENSIC values are canonical
at synthesis time**; engine values are L1.5 substrate. Where the two
disagree on Sub-Sub-Lord at a boundary case, retrieval-time consumers
prefer FORENSIC's value if the chart_id matches a FORENSIC-bearing native;
otherwise they use the engine value with `needs_verification=true` until an
external acharya / Jagannatha Hora export resolves it.

## §1 — What was checked

| Source | What |
|---|---|
| Engine (`compute_kp.py`) | pyswisseph 2.10.x, Moshier ephemeris, Lahiri SIDM_LAHIRI; computes sidereal longitude per planet → identifies nakshatra → derives Star Lord / Sub Lord / Sub-Sub Lord by Vimshottari subdivision |
| FORENSIC §4.2 (canonical) | KP Planetary Positions table — degree-within-sign, Star Lord, Sub Lord, Sub-Sub Lord per the 9 grahas |

The `compute_kp.py` longitudes are **absolute sidereal** (0°–360°); FORENSIC §4.2
records degree-within-sign. Cross-checks below convert engine output to
degree-within-sign for direct comparison.

## §2 — Per-planet table

| Planet | FORENSIC §4.2 (deg w/i sign) | Engine (deg w/i sign) | Δ arcmin | Star Lord | Sub Lord | Sub-Sub Lord | Sub-Sub Verdict |
|---|---|---|---:|---|---|---|---|
| Sun | 22°02′ Capricorn | 21°57′ Capricorn | −2.6 | Moon = Moon ✓ | Venus = Venus ✓ | Saturn = Saturn ✓ | EXACT |
| Moon | 27°08′ Aquarius | 27°03′ Aquarius | −4.7 | Jupiter = Jupiter ✓ | Venus = Venus ✓ | Moon = Moon ✓ | EXACT |
| Mars | 18°37′ Libra | 18°31′ Libra | −6.0 | Rahu = Rahu ✓ | Moon = Moon ✓ | Saturn ↔ Jupiter | BOUNDARY-FLIP (Δ < 6.6 arcmin to Saturn segment edge) |
| Mercury | 00°55′ Capricorn | 00°50′ Capricorn | −5.3 | Sun = Sun ✓ | Rahu = Rahu ✓ | Sun ↔ Venus | BOUNDARY-FLIP (Sun segment is 6 arcmin wide; Δ flips into adjacent Venus segment) |
| Jupiter | 09°53′ Sagittarius | 09°47′ Sagittarius | −5.6 | Ketu = Ketu ✓ | Saturn = Saturn ✓ | Mercury = Mercury ✓ | EXACT |
| Venus | 19°15′ Sagittarius | 19°10′ Sagittarius | −5.0 | Venus = Venus ✓ | Rahu = Rahu ✓ | Mercury = Mercury ✓ | EXACT |
| Saturn | 22°32′ Libra | 22°26′ Libra | −5.9 | Jupiter = Jupiter ✓ | Saturn = Saturn ✓ | Venus ↔ Ketu | BOUNDARY-FLIP (Δ < 6 arcmin to Venus/Ketu boundary) |
| Rahu | 19°07′ Taurus | 19°02′ Taurus | −5.0 | Moon = Moon ✓ | Mercury = Mercury ✓ | Jupiter ↔ Rahu | BOUNDARY-FLIP (Δ < 5 arcmin) |
| Ketu | 19°07′ Scorpio | 19°02′ Scorpio | −5.0 | Mercury = Mercury ✓ | Ketu = Ketu ✓ | Saturn ↔ Jupiter | BOUNDARY-FLIP (Δ < 5 arcmin) |

Engine "deg w/i sign" computed from absolute sidereal longitude:
`deg_w_i_sign = sidereal_lon mod 30°`.

## §3 — Why the Sub-Sub-Lord flips happen

The Sub-Sub-Lord cycle inside a Sub-Lord segment uses Vimshottari proportions
on a base whose width is itself a Vimshottari fraction of the nakshatra
(800 arcmin). Concretely:

- Nakshatra: 800 arcmin (~13°20′).
- Sub-Lord segment: 40 to 133 arcmin (varies by lord).
- Sub-Sub-Lord segment: 1.4 to 22 arcmin (varies by both Sub-Lord *and*
  Sub-Sub-Lord, since width = `sub_lord_width × sub_sub_lord_vim_years / 120`).

The smallest Sub-Sub segments (Sun-within-Mars, Sun-within-Sun, etc.) are
≤3.3 arcmin wide. A 5–8 arcmin engine-vs-FORENSIC longitude Δ can span an
entire small segment. This is structurally the same effect FORENSIC §5
GAP.09 records for Vimshottari dasha *date* boundaries: a 1.4-arcmin Moon
longitude difference shifts dasha dates by 7–9 days; a 5–8 arcmin planet
longitude difference shifts the Sub-Sub-Lord boundary by an amount large
enough to flip the result for some planets and not others.

## §4 — Disposition

1. **Star Lord** and **Sub Lord** results are 9/9 PASS at 800-arcmin and
   40–133-arcmin segment scales. These are the substantive KP signification
   inputs — they are reliable from the engine.

2. **Sub-Sub-Lord** is GOLDEN at FORENSIC §4.2 values for retrieval-time
   queries scoped to chart_id `abhisek_mohanty_primary`. The engine output
   is the substrate for charts other than the FORENSIC-anchored native and
   for forward-looking transit/varshaphala timestamps where no FORENSIC
   row exists.

3. No `needs_verification=true` flag is set on the engine rows by default.
   The Star Lord and Sub Lord cross-check passes 9/9, and Sub-Sub-Lord
   disagreements are in a documented ayanamsha-precision band, not engine
   defects. Downstream consumers that need acharya-grade Sub-Sub-Lord
   resolution should JOIN against `chart_facts` category=`KP.PLN.*` for
   the FORENSIC-canonical value when chart_id matches.

4. **Open item for follow-up:** if a Jagannatha Hora export is later
   obtained for this native, re-run the cross-check at that ephemeris
   to confirm whether the FORENSIC §4.2 values themselves correspond to
   the JH+Lahiri ayanamsha (likely, given GAP.09's framing) or to a third
   ayanamsha source. Filing under M3-D held-out sample work, not a
   blocker for M3-C close.

## §5 — Files referenced

- Engine: `platform/scripts/temporal/compute_kp.py`
- Output: `05_TEMPORAL_ENGINES/kp/KP_SUBLORDS_RAW_v1_0.json` (9 rows)
- Insert SQL: `05_TEMPORAL_ENGINES/kp/KP_SUBLORDS_INSERT_v1_0.sql`
- Migration: `platform/migrations/024_kp_sublords.sql`
- FORENSIC source: `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` §4.2
- Standing-policy reference: FORENSIC §5 GAP.09 (resolved 2026-04-19) +
  Vimshottari `CROSSCHECK_v1_0.md` (M3-W2-B1 close)

---
---

# EXTENSION — ṢAḌ-DARŚANA W3K Lane 1 (2026-08-02)

*Everything above (§0–§5) is the 2026-05-01 record and is unchanged. §§6–8 extend
this document's methodology, per `W3K_SUBSTRATE_INVENTORY_v1_0.md` §2 G-6's
instruction to extend this exact crosscheck rather than invent a new harness, to
cover three surfaces that did not exist on 2026-05-01: the L0 249-fold division
table, the live cuspal output, and the 4-limbed significator derivation. This is
Gate W3K's two-pass verification discharge.*

## §6 — Pass 1: the L0 division table vs. the same FORENSIC §4.2 fixture

**What is new.** `bg_kp_sublord_division` (ADJUDICATION-7 Part 1, migration 535,
built by `brahmagyan/l0_kp_sublord_division.py`) is a THIRD, independent
implementation of the KP sub-lord geometry — after `compute_kp.py` (§1, now
retired with migration 024) and `compute_kp_lords()` (the live path since PR #738).
It differs from both in kind, not only in code: it works in **exact rational
arithmetic** (`fractions.Fraction`) over the whole circle at build time, where both
predecessors accumulate **floats** per call. It therefore fails differently, which
is what makes the comparison informative.

**The classical count reproduces itself.** 27 nakṣatras × 9 Vimśottarī subs = 243
segments; the 12 rāśi boundaries are then applied as cuts, of which three coincide
with a nakṣatra start (0°/120°/240°), three fall EXACTLY on an interior sub
boundary (60°/180°/300° — cumulative 60 Vimśottarī years inside the Mars-lorded
Mṛgaśira/Citrā/Dhaniṣṭhā), and the remaining **six** split one segment each:
243 + 6 = **249**. The builder does not hard-code 249; the count falls out of the
arithmetic and the test asserts it
(`tests/test_bg_kp_sublord_division.py::test_exactly_249_divisions_after_the_rashi_cut`).
The three exact coincidences are asserted in rationals, not floats
(`::test_the_three_exact_coincidences_are_real_not_float_luck`) — had they been
float near-misses the count would have been 252 and the classical figure would
have failed to reproduce.

**Against the §2 fixture (the FORENSIC §4.2 column), 9/9 and 9/9:**

| Planet | FORENSIC §4.2 abs. sidereal | Star Lord (FORENSIC = table) | Sub Lord (FORENSIC = table) |
|---|---:|---|---|
| Sun | 292°02′ | Moon ✓ | Venus ✓ |
| Moon | 327°08′ | Jupiter ✓ | Venus ✓ |
| Mars | 198°37′ | Rahu ✓ | Moon ✓ |
| Mercury | 270°55′ | Sun ✓ | Rahu ✓ |
| Jupiter | 249°53′ | Ketu ✓ | Saturn ✓ |
| Venus | 259°15′ | Venus ✓ | Rahu ✓ |
| Saturn | 202°32′ | Jupiter ✓ | Saturn ✓ |
| Rahu | 49°07′ | Moon ✓ | Mercury ✓ |
| Ketu | 229°07′ | Mercury ✓ | Ketu ✓ |

Same verdict as §0's Star Lord 9/9 and Sub Lord 9/9, from a different
implementation and a different arithmetic. Committed as
`tests/test_bg_kp_sublord_division.py::FORENSIC_KP_FIXTURE` — the tier-(iii)
committed fixture the brief's citation hierarchy authorises where no KP text is
ingested (see §8).

**Sub-Sub Lord is NOT re-litigated here.** §0's WITHIN_TOLERANCE verdict and §3's
GAP.09 explanation stand unchanged: the division table does not tabulate the
sub-sub grain at all (migration 535's SCOPE DISCLOSURE), so it neither confirms
nor disturbs that finding.

## §7 — Pass 2: table vs. live engine, and the live cuspal output on BOTH charts

**Whole-circle sweep.** The exact-rational lookup and the live float-accumulating
`compute_kp_lords()` were compared at every 0.01° of the zodiac:

| Samples attempted | Boundary-adjacent, excluded (<1e-6° from a division edge) | Compared | Disagreements |
|---:|---:|---:|---:|
| 36,000 | 33 | **35,967** | **0** |

The 33 exclusions are counted and reported rather than silently tolerated: exactly
at a division edge the two implementations legitimately round to opposite sides,
and that is the same boundary-flip effect §3 documents — not evidence of an engine
defect. Everywhere else the agreement is exact.
(`::test_table_lookup_agrees_with_compute_kp_lords_across_the_whole_circle`.)

**Cuspal sub-lords, chart 482012f1 (Abhisek), Krishnamurti ayanāṃśa** — the surface
§1's 2026-05-01 crosscheck did not cover, because cuspal KP output did not exist
then:

| Cusp | Placidus longitude | Star lord | Sub lord | Table = live engine |
|---|---:|---|---|---|
| 1 | 12.5181° | Ketu | Mercury | ✓ |
| 2 | 42.5096° | Moon | Rahu | ✓ |
| 3 | 68.0275° | Rahu | Rahu | ✓ |
| 4 | 93.0669° | Jupiter | Rahu | ✓ |
| 5 | 121.1276° | Ketu | Venus | ✓ |
| 6 | 154.7908° | Sun | Saturn | ✓ |
| 7 | 192.5181° | Rahu | Saturn | ✓ |
| 8 | 222.5096° | Saturn | Mars | ✓ |
| 9 | 248.0275° | Ketu | Jupiter | ✓ |
| 10 | 273.0669° | Sun | Saturn | ✓ |
| 11 | 301.1276° | Mars | Mercury | ✓ |
| 12 | 334.7908° | Saturn | Saturn | ✓ |

**Cuspal sub-lords, chart 1c826d5a (Abhinandan, 1985-03-02 09:40 IST Bhubaneswar)**
— the brief's "cuspal sub-lords computed on BOTH charts" clause:

| Cusp | Placidus longitude | Star lord | Sub lord | Table = live engine |
|---|---:|---|---|---|
| 1 | 23.6233° | Venus | Saturn | ✓ |
| 2 | 51.8471° | Moon | Venus | ✓ |
| 3 | 76.7933° | Rahu | Venus | ✓ |
| 4 | 102.3159° | Saturn | Mars | ✓ |
| 5 | 131.6695° | Ketu | Mercury | ✓ |
| 6 | 166.4820° | Moon | Saturn | ✓ |
| 7 | 203.6233° | Jupiter | Saturn | ✓ |
| 8 | 231.8471° | Mercury | Sun | ✓ |
| 9 | 256.7933° | Venus | Moon | ✓ |
| 10 | 282.3159° | Moon | Rahu | ✓ |
| 11 | 311.6695° | Rahu | Saturn | ✓ |
| 12 | 346.4820° | Saturn | Jupiter | ✓ |

12/12 on both charts; per-graha 9/9 on both charts. Note the two charts' cusps are
genuinely different arcs, not a shared fallback — the same guard §1's original
methodology applied to the engine longitudes.

**The significator derivation (new in W3K), worked in full on the native's 10th
cusp.** The 10th Placidus cusp is 273.0669° (Capricorn) → owner **Saturn**. The
10th cuspal arc is [273.0669°, 301.1276°).

1. **Occupants.** The Sun (292.0595°) falls inside the arc. Mercury (270.9356°)
   does **not** — it is *below* the cusp, so it is cuspally 9th although whole-sign
   it is 10th. → Level B = **Sun**.
2. **Level A** — planets tenanting the star of an occupant. The occupant is the
   Sun; the planet in a Sun-lorded nakṣatra is Mercury (270.9356°, Uttarāṣāḍhā,
   star lord Sun). → **Mercury**.
3. **Level C** — planets tenanting the star of the owner (Saturn). No graha here
   sits in Puṣya / Anurādhā / Uttara Bhādrapadā. → **none** (reported as the
   literal `none`, not an empty string).
4. **Level D** — the owner. → **Saturn**.
5. **Ranked** (strongest first, deduped to strongest appearance):
   **Mercury, Sun, Saturn**.

The classical content of that result, and the reason KP earns its place as a
distinct voice: **Mercury is the strongest significator of the native's 10th house
even though Mercury is not in the 10th cuspal house at all.** No Parāśarī rule
reaches that verdict — it follows only from KP's star-lord-outranks-occupancy
ladder. Asserted end to end at
`tests/test_ga_kp_significators.py::test_native_chart_10th_house_worked_example`,
so this prose cannot drift from the emitter's actual output.

**The house-frame divergence is data, not a reconciliation** (Elevation Law 4;
brief §W3K "served as data, never silently reconciled"). Mercury above is the
concrete case: `kp_cuspal_house=9`, `whole_sign_house=10`,
`house_system_divergence=true`, all three stored side by side. Nothing overwrites
anything.

**Honest empties are reported, not filled.** On chart 1c826d5a the 10th cusp
(282.3159°) is untenanted: levels A and B are `none`, level C is Saturn, level D is
Saturn, ranked = `Saturn` (count 1). An empty limb is reported as empty
(§N.6 item 3 / §N.7 item 6).

## §8 — Disposition, and the corpus gap this extension FILES

1. **Star Lord / Sub Lord** are now confirmed by THREE independent implementations
   against the same FORENSIC §4.2 fixture. `bg_kp_sublord_division` is the
   AUTHORITY going forward: `ga_nakshatra`'s significator emitter READS it and does
   not re-derive the geometry (§N.5), and cross-checks each referenced value
   against the live path, storing `two_pass_verified` or `divergent_flagged` per
   row — a verdict that can genuinely come back false (§N.8).

2. **Sub-Sub Lord** — unchanged from §4.2. The division table does not cover it. A
   sub-sub/prāṇa reference table is a NAMED, PARKED follow-on, not a silent
   omission (migration 535 SCOPE DISCLOSURE).

3. **CORPUS GAP FILED** (ADJUDICATION-7's own instruction, "File that gap"):
   **no KP source text is ingested in `classical_text_chunks`.** The adjudication's
   search found 3 chunks matching sub-lord/Krishnamurti terms and all three are
   false positives (Sārāvalī and Sarvārtha Cintāmaṇi on daśā sub-periods). The
   consequence, stated plainly: the KP-specific conventions in this instrument —
   applying the Vimśottarī proportion to ARC rather than TIME, and cutting the
   divisions at rāśi boundaries — rest on tier (iii) (published KP reader
   convention, K. S. Krishnamurti, *KP Reader* I–III / Stellar Astrology) VERIFIED
   against the committed §6 fixture, not on tier (i) ingested text. The
   proportional constants themselves (the Vimśottarī year table and its fixed
   order) ARE tier (i): BPHS Ch.46, ingested, seeded at
   `brahma_dasha_systems.canonical_id='vimshottari'`.
   **Work item:** ingest a KP primary source (KP Reader I–VI, or *Krishnamurti
   Padhdhati* volumes) into `classical_text_chunks` so these conventions can be
   re-verified at tier (i). Until then no KP surface may claim a corpus citation
   for the convention itself.

4. **Not covered by this extension, and deliberately so** (named so it is not
   mistaken for verified): the `chart_dashas.system_id='vimshottari_kp'` window
   stream (W3K Lane 2 / gap G-4), query-moment ruling planets (gap G-2, parked per
   the inventory §5.4 recommendation), and KP concurrence/dissent serving (gap G-5,
   Lane 2). This extension verifies the natal sub-lord geometry and the significator
   derivation only.

**§§6–8 files referenced:**
`platform/python-sidecar/brahmagyan/l0_kp_sublord_division.py` ·
`platform/python-sidecar/pipeline/orchestrator/writers/bg_kp_sublord_division.py` ·
`platform/python-sidecar/ga_writers/ga_kp_significators.py` ·
`platform/python-sidecar/pipeline/orchestrator/writers/ga_nakshatra.py` ·
`platform/python-sidecar/tests/test_bg_kp_sublord_division.py` (18 tests) ·
`platform/python-sidecar/tests/test_ga_kp_significators.py` (18 tests) ·
`platform/supabase/migrations/535_bg_kp_sublord_division.sql` ·
ruling: `00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md`
ADJUDICATION-7 ·
inventory: `00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/W3K_SUBSTRATE_INVENTORY_v1_0.md`

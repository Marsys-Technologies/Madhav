---
artifact: JYOTISH_ENGINE_SCOPE_CATALOGUE_v1_0
document: Jyotish Compute Engine — Full Data-Point Scope Catalogue
project_codename: Jaganathura-equivalent
status: DRAFT (scoping — feeds the build brief)
date: 2026-05-27
authority: "Jagannatha Hora (JH) is the SOLE authority for assumptions and formulas. Validate-once against 01_FACTS_LAYER/SOURCES/JHORA_TRANSCRIPTION_v8_0_SOURCE.md. No LLM in the compute path. GCP-only."
output_contract: "Engine emits canonical JSON; renderer produces L1.md in FORENSIC schema."
inputs: "{ date, time (IST, exact), latitude, longitude }"
layer: "L1 (generation spec)"
expose_to_chat: false
---

# Jyotish Compute Engine — Full Data-Point Scope Catalogue

## Purpose

Defines the complete set of data points the JH-parity engine will compute. Three bands:

- **Band 0 — L1 parity:** everything already in `FORENSIC_ASTROLOGICAL_DATA_v8_0.md` (27 sections). The engine must reproduce all of it. Not re-listed exhaustively here; see that file.
- **Band 1 — Additional JH-computable:** data points JH itself produces (or that follow directly from JH's documented Parashara/Jaimini/Tajaka formulas) that are NOT in the current L1. **This is the focus of this document.**
- **Band 2 — Beyond-JH, ephemeris-computable:** points the Swiss Ephemeris can produce but that fall outside JH's classical scope (outer planets as Western bodies, Chiron, tropical overlay, midpoints). Included only if explicitly wanted; **clearly flagged as non-JH** so they never contaminate JH-parity claims.

Per-item annotation: **[inputs]** = what beyond birth data is needed (e.g., target date, partner chart, sunrise); **[parity]** = confidence we can hit JH exactly (HIGH = deterministic/well-documented; MED = scheme-variant-sensitive; LOW = under-specified, reverse-engineer from JH outputs).

---

## A — Additional Divisional Charts (Vargas)

L1 has D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D30, D40, D45, D60. JH computes the full Shodasavarga and an extended set. Add:

- **D5 Panchamsa** — fame, authority, power. [parity HIGH]
- **D6 Shashthamsa / Kauluka** — health, disease. [parity HIGH]
- **D8 Ashtamsa** — sudden events, longevity, legacies. [parity MED — odd/even reckoning variants]
- **D11 Rudramsa / Ekadasamsa** — death, destruction, gains (JH supports both the Rudramsa and the Labhamsa conventions). [parity MED]
- **D27 Bhamsa / Saptavimsamsa** — strengths and weaknesses, stamina. [parity HIGH]
- **D81 Nava-Navamsa** — fine spiritual/karmic granularity. [parity MED]
- **D108 (Ashtottaramsa)** and **D144 (Dwadas-Dwadasamsa)** — JH computes these. [parity MED]
- **D150 Nadiamsa** — JH offers multiple Nadiamsa schemes (Chandra Kala, etc.); pin the scheme to JH's default. [parity LOW — scheme-sensitive]

**For each varga (Band 0 + new), emit the full record, not just sign occupancy:**
- Varga-Lagna; each planet's varga sign, degree-in-varga, house-from-varga-Lagna, dispositor.
- Vargottama flag, Pushkara-navamsa / Pushkara-bhaga flags.
- Per-varga dignity (own/exalted/debilitated/friend/enemy/neutral).

**Varga-summary strength tables (very JH, absent from L1):**
- **Shadvarga / Saptavarga / Dasavarga / Shodasavarga dignity counts** per planet.
- **Varga-visesha named states** per planet across the varga set: Parijata, Uttama, Gopura, Simhasana, Paravata, Devaloka, Brahmaloka (and the higher Iravata, Sridhama, Devloka chains). [parity HIGH once varga set is locked]

---

## B — Deeper & Additional Dasha Systems

L1 has Vimshottari (to Antardasha), Yogini, Jaimini Chara. Add:

**Vimshottari deeper levels:**
- **Pratyantardasha (PD), Sookshma (SD), Prana (PrD)** — full 5-level breakdown to the day/hour, for any date window. [parity HIGH]

**Other Nakshatra (conditional) dashas JH computes:**
- **Ashtottari** (108-yr), **Shodashottari** (116), **Dwadashottari** (112), **Panchottari** (105), **Shatabdika** (100), **Chaturashiti-sama** (84), **Dwisaptati-sama** (72), **Shashtihayani / Shashti-sama** (60), **Shattrimsha-sama** (36). [parity HIGH — applicability conditions per BPHS; JH auto-selects]

**Rashi (Jaimini & Parashari) dashas JH computes:**
- **Kalachakra Dasha** (nakshatra-pada based; paramayus; the savya/apasavya gati). [parity LOW — notoriously variant; pin to JH]
- **Narayana (Padakrama) Dasha**, **Sthira Dasha**, **Shoola Dasha**, **Brahma Dasha**, **Mandooka (Manduka) Dasha**, **Sudasa / Lakshmi Dasha**, **Drig Dasha**, **Trikona Dasha**, **Navamsa Dasha**, **Yogardha Dasha**, **Tara Lagna Dasha**. [parity MED]
- **Karaka Kendradi Graha Dasha (KCGD)**, **Moola Dasha**, **Lagna Kendradi Rasi Dasha**. [parity MED]
- **Sudarshana Chakra Dasha** (the 3-wheel Sun/Moon/Lagna annual-progression). [parity MED]

**Annual-chart dashas (Tajaka — see §C):** Mudda Dasha, Patyayini Dasha, Varsha-Yogini.

Each dasha: full nested period table with start/end to the day, lord, and (for rashi dashas) sign + antardasha sequence.

---

## C — Annual / Progression Charts (Tajaka / Varshphal)

L1 §22 has a single 2026–27 Varshphal. Generalise to **any year, plus monthly/daily:**

- **Varshphal (solar return) for any year:** Varsha-Lagna, **Muntha** + Muntha lord, **Year Lord (Varshesh)** via the 5-office adhikari method (Muntha-pati, Janma-Lagna-pati, Tri-rashi-pati, Dina-ratri-pati, Varsha-pravesh-Lagna-pati), Tri-rashi lords. [parity MED]
- **Tajaka strengths:** Pancha-vargeeya bala and **Harsha bala** in the annual chart. [parity MED]
- **16 Tajaka yogas:** Ithasala, Ishrafa, Nakta, Yamaya, Manau, Kamboola, Gairi-kamboola, Khallasara, Radda, Duruph, Dutthotha-davira, Tambira, Kuttha, Durpha, and the Muthasila/Ithasala variants. [parity MED]
- **Sahams recomputed for the annual chart** (the day/night-variant lots). [parity HIGH]
- **Mudda Dasha & Patyayini Dasha** for the year. [parity MED]
- **Maasa-pravesh (monthly)** and **Dina-pravesh (daily)** charts. [parity MED]
- **Tri-pataki chakra** for the year. [parity MED]

---

## D — Additional Sensitive Points & Sphutas

L1 §11 has 9 upagrahas + Bhrigu Bindu + Yogi/Avayogi. Add the classical sphuta set JH computes:

- **Beeja Sphuta** (male fertility/virility index) and **Kshetra Sphuta** (female fertility index). [parity HIGH]
- **Tithi Sphuta, Yoga Sphuta, Avayogi Sphuta, Prana Sphuta, Deha Sphuta, Mrityu Sphuta.** [parity HIGH]
- **Trisphuta, Chatusphuta, Panchasphuta** (composite longevity/event points). [parity HIGH]
- **Bhava arambha / madhya / anta** (cusp-start, mid, end) for all 12 houses, in the Sripati scheme. [parity HIGH]
- **Alternate house systems as parallel outputs:** Equal, Whole-sign, Porphyry, Placidus (for KP) — so cross-system questions are answerable. [parity HIGH]
- **Pranapada** (already a lagna) and the remaining upagraha completeness check (Kala, Mrityu, Ardhaprahara — verify all eight Kaala-velas present). [parity MED — sunrise-dependent; **[inputs] accurate sunrise/sunset**]

---

## E — Strength & Ashtakavarga Extensions

**Ashtakavarga (L1 §7 has BAV/SAV + Shuddha Pinda):**
- **Prastara Ashtakavarga** — the full per-planet contributor grid (the raw 8×12 matrices behind each BAV). [parity HIGH]
- **Kakshya tables for ALL planets** (L1 §8 has Saturn only) — for transit timing of every graha. [parity HIGH]
- **Trikona Sodhana** and **Ekadhipatya Sodhana** intermediate reductions (the audit trail from BAV to Sodhya Pinda). [parity MED]
- **Samudaya (aggregate) Ashtakavarga** transit interpretation scaffolds. [parity HIGH]

**Shadbala extensions:**
- Full **Saptavargaja Bala** per-varga breakdown; expanded **Sthana Bala** sub-components beyond the L1 totals. [parity LOW — match JH formula exactly]
- **Bhava Bala** full sub-component ledger (Bhavadhipati, Bhava-digbala, Bhava-drishti) per house. [parity LOW]

---

## F — Transit (Gochara) Framework — for ANY target date

**[inputs] target date.** None of this is in L1 except natal Sade Sati (§21).

- Sidereal transit positions for any date; transit sign + **house-from-Lagna and house-from-Moon**. [parity HIGH]
- **Saturn cycles:** Sade Sati (extend §21 to past+future cycles), Dhaiya (Ashtama/Kantaka Shani). [parity HIGH]
- **Jupiter transit cycle** (12-yr), **nodal cycle** (Rahu-Ketu 18.6-yr return), **Saturn return** (~29.5-yr). [parity HIGH]
- **Ashtakavarga-gated transits** — Saturn/Jupiter strong-bindu transit windows (using §E Kakshya + BAV). [parity HIGH]
- **Vedha & Argala on transits**; transit-to-natal aspect hits with exact dates. [parity MED]
- **Daily predictive panchang:** Tara-bala and Chandra-bala for any day relative to natal Moon. [parity HIGH]
- **Ingress / retrograde / stationary / combustion windows**, eclipse proximity (natal and transiting). [parity HIGH]
- **Transit chakras for timing:** Sarvatobhadra, Sapta-shalaka, Kota (extend §19), Surya/Chandra Kalanala, Kurma chakra. [parity MED]

---

## G — Panchang & Calendrical Extensions

L1 §15 has the core five limbs + Avakahada. Add (natal + any-date):

- **Birth-time time-lords:** Hora lord (have Saturn), Vara-hora sequence, Choghadiya, Rahu Kalam / Yama Ganda / Gulika Kalam windows, Abhijit muhurta. [parity HIGH — **[inputs] sunrise**]
- **Full nakshatra profile:** pada lord, Nadi, Yoni + Yoni animal/sex, Tara, Gana, Varna, Vashya, nakshatra deity & guna, ruling planet, Janma ghatis (have 10.7380). [parity HIGH]
- **Calendrical frame:** lunar month + Paksha, Ritu (season), Ayana, Samvatsara (have Rudhirodgaari), Shaka/Vikram year, sunrise/sunset/day-length. [parity HIGH]
- **Muhurta engine** for any future date (auspicious-window finder) — you already have a Panchang module to extend. [parity HIGH]

---

## H — Compatibility / Relational (when a second chart is supplied)

**[inputs] partner chart.** Entirely new capability.

- **Ashtakuta Milan (36-point Guna Milap):** Varna, Vashya, Tara, Yoni, Graha-Maitri, Gana, Bhakoot, Nadi — each sub-score + total. [parity HIGH]
- **Dosha checks:** Mangal/Kuja Dosha (both charts), Nadi Dosha, Bhakoot Dosha, Rajju, Vedha, Mahendra, Stree-Deergha kutas. [parity HIGH]
- **Synastry / composite:** inter-chart house overlays, Dasha-sandhi alignment, Navamsa compatibility. [parity MED]

---

## I — Longevity (Ayurdaya) — extend §24

- **Pindayu, Nisargayu, Amsayu** with all Haranas (Chakrapata, Krurodaya, Astangata, Bhandya, Saturn/Mars drishti reductions). [parity LOW — match JH's harana order exactly]
- **Kalachakra ayus**; Lagna/Moon/Sun-based ayus selection rule. [parity MED]
- **Jaimini longevity:** Sthira/Chara/Ubhaya dvara pairs → short/middle/long band. [parity MED]
- **Maraka framework:** marakesh planets, maraka dashas/transits, Brahma/Maheshwara/Rudra longevity-planets. [parity MED]

---

## J — Yogas — extend §26 to a full BPHS/Jaimini scan

For each detected yoga: participating planets, active/cancelled flag, governing house-lords, and the dasha window that activates it.

- **Pancha Mahapurusha:** Ruchaka, Bhadra, Hamsa, Malavya, Sasa. [parity HIGH]
- **32 Nabhasa yogas** (Ashraya, Dala, Akriti, Sankhya families). [parity MED]
- **Raja yogas** (all kendra-trikona lord associations), **Dhana yogas**, **Daridra yogas**. [parity MED]
- **Vipareeta Raja yoga** (Harsha, Sarala, Vimala) and **Neecha-bhanga Raja yoga** (extend the D9 NBR logic in L1 §3.5.1). [parity MED]
- **Parivartana yogas** (Maha, Khala, Dainya). [parity HIGH]
- **Moon yogas:** Sunapha, Anapha, Durudhara, Kemadruma; Gajakesari, Chandra-Mangala, Adhi. [parity HIGH]
- **Solar:** Budha-Aditya; **Lakshmi, Saraswati, Kalanidhi, Amala, Chamara** etc. [parity MED]

---

## K — Jaimini & Karaka Deep Layer

- **Karakamsa chart** (AK in navamsa) + **Swamsa** analysis. [parity HIGH]
- **All 12 Arudha padas (A1–A12)** + **Graha-arudhas** (L1 §13 has a subset). [parity HIGH]
- **Argala** (primary, secondary, virodha-argala) for all houses; **Jaimini rashi-drishti** matrix. [parity MED]
- **Chara-karaka-based yogas**; AK-in-navamsa-sign and 12th-from-AK (Ishta/Kashta devata — extend §20). [parity MED]

---

## L — Nakshatra Matrices (extend §14 Navatara)

- **Full 27/28-position Tara chakra** from Janma (all nine taras × three cycles; optional Abhijit). [parity HIGH]
- **Nadi nakshatra**, **Sapta-shalaka chakra**, **Sarvatobhadra chakra** (transit vedha timing). [parity MED]

---

## M — Band 2: Beyond-JH, Ephemeris-Computable (FLAGGED non-JH)

Computable from Swiss Ephemeris but **outside JH's classical scope** — include only on explicit request, never folded into JH-parity outputs. (Note: FORENSIC §16.2 already carries a Western overlay with Uranus/Neptune/Pluto, so precedent exists.)

- Outer planets as Western bodies (Uranus, Neptune, Pluto) — tropical and sidereal. [ephemeris HIGH]
- Chiron, mean/true Lilith (Black Moon), the Vertex, Part of Fortune (Western). [ephemeris HIGH]
- Full **tropical-zodiac chart** + Western house systems + aspect/orb grid + midpoint tree. [ephemeris HIGH]
- True-node variant of the whole chart (JH/L1 use Mean node) as a parallel diagnostic. [ephemeris HIGH]

---

## N — Cross-Cutting Engine Requirements (apply to every band)

- **Convention stack pinned per-section to JH:** ayanamsa (Lahiri value matching JH's 23°37′09.78″ at native epoch; **KP section uses KP/Krishnamurti ayanamsa + Placidus** — open resolution item), Mean node, Sripati houses (Placidus for KP). [parity HIGH once pinned]
- **Determinism:** identical input + `engine_version` → byte-identical output. Stamp ephemeris-data version + ayanamsa model + engine_version into every artifact.
- **Golden-fixture validation:** reproduce Abhisek's JH report (and the additional JH exports you supply) to declared per-section tolerances; CI gate blocks parity regressions.
- **Tolerance policy:** positional points to arcsecond; Tier-3 (Shadbala/Ayurdaya/Nadiamsa) to JH's exact value where formula is documented, else reverse-engineered from JH outputs and the residual recorded.

---

## Open Items Carried From Scoping

1. **JH-vs-FORENSIC input divergence** — JH header: 85°50′E/20°14′N, ayanamsa 23°37′09.78″; FORENSIC: 20.2960N/85.8246E, 23°37′58″. Decide canonical coordinate policy (exact geocode for new clients; JH's rounded coords to reproduce Abhisek).
2. **KP-ayanamsa per-section** — confirm FORENSIC §4 KP runs Krishnamurti ayanamsa + Placidus (the 12°29′19″ vs 12°25′21.62″ gap strongly indicates it).
3. **PyJHora evaluation** — vet library state, licence, and parity against the JH report before adopt/hybrid decision.
4. **Swiss Ephemeris licensing** — AGPL vs Astrodienst commercial for a closed-source multi-client SaaS.

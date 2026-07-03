---
artifact: L0_L1_DATA_INVESTIGATION
canonical_id: L0_L1_DATA_INVESTIGATION
version: 1.0
status: CURRENT
created: 2026-06-17
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
---

# L0/L1 Data Investigation v1.0

**Purpose:** Empirically baseline what the L1 tables hold today — D1-only or already partial-varga — to size the L1 enrichment expansions against reality.

**Date:** 2026-06-17  
**Database:** Production via Cloud SQL Proxy (port 5433)  
**Native chart:** `482012f1-710e-4a25-994a-93821f5871aa`  

---

## Q1 — Graha-sthāna (positions)

### Part A: fact categories with 'graha' prefix

**Query:**
```sql
SELECT DISTINCT fact_category FROM chart_facts 
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category LIKE 'graha%'
ORDER BY fact_category;
```

**Result:**
```
                fact_category                
---------------------------------------------
 graha_avastha_baladi
 graha_avastha_deepta
 graha_avastha_jagrad
 graha_avastha_lajjitadi
 graha_avastha_lifetime_exposure_summary
 graha_avastha_sayanadi
 graha_composite_state_classification
 graha_dignity_per_varga
 graha_dispositor_chain
 graha_effective_dignity_modified_by_aspects
 graha_functional_class_per_ascendant
 graha_gandanta
 graha_in_house_composite_strength
 graha_ishta_phala
 graha_kashta_phala
 graha_kp_lords
 graha_nakshatra_join
 graha_pada_join
 graha_position
 graha_saptavargaja_bala_component
 graha_shadbala_cheshta
 graha_shadbala_dig
 graha_shadbala_drik
 graha_shadbala_kala
 graha_shadbala_naisargika
 graha_shadbala_sthana
 graha_shadbala_total
 graha_sign_attributes
 graha_special_state_rollup
 graha_tara_bala
 graha_tri_deva_role_strength
 graha_vargottama_amplification_factor
 graha_vimsopaka_dasavarga
 graha_vimsopaka_saptavarga
 graha_vimsopaka_shadvarga
 graha_vimsopaka_shodasavarga
 graha_yoga_karaka_flag
(37 rows)
```

### Part B: ganita_positions table

**Query:**
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema='public' AND table_name LIKE '%position%';
```

**Result:**
```
 table_name 
------------
(0 rows)
```

No `ganita_positions` table exists — positions live in `chart_facts` (category `graha_position`) and `chart_divisionals` (category `varga_position`).

### Part C: chart_divisionals varga positions

**Query:**
```sql
SELECT DISTINCT varga, count(*) as cnt FROM chart_divisionals 
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'
GROUP BY varga ORDER BY varga;
```

**Result:**
```
 varga | cnt 
-------+-----
 CROSS | 150
 D1    | 715
 D10   | 680
 D108  | 735
 D11   | 645
 D12   | 750
 D14   | 645
 D15   | 645
 D150  | 735
 D16   | 725
 D2    | 860
 D20   | 725
 D21   | 645
 D24   | 725
 D27   | 730
 D2700 | 735
 D3    | 910
 D30   | 810
 D32   | 645
 D33   | 645
 D4    | 680
 D40   | 725
 D45   | 725
 D5    | 645
 D50   | 690
 D54   | 690
 D6    | 645
 D60   | 805
 D7    | 680
 D8    | 645
 D9    | 850
(31 rows)
```

### Additional: graha_position ayanamshas and bodies

```
 total | distinct_subjects 
-------+-------------------
   430 |                10

       ayanamsha_id        
---------------------------
 krishnamurti
 lahiri_chitrapaksha
 raman
 surya_siddhanta_classical
 true_chitra
(5 rows)
```

**Answer:** `graha_position` in `chart_facts` holds D1-only positions (10 bodies × 5 ayanamshas = ~430 rows per set of fact_keys). Varga positions for all 30+ charts live in `chart_divisionals` under `varga_position` category (31 distinct vargas including CROSS).

---

## Q2 — Varga (chart_divisionals): all 30?

**Query:**
```sql
SELECT DISTINCT varga FROM chart_divisionals 
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' 
ORDER BY varga;
```

**Result:**
```
 varga 
-------
 CROSS
 D1
 D10
 D108
 D11
 D12
 D14
 D15
 D150
 D16
 D2
 D20
 D21
 D24
 D27
 D2700
 D3
 D30
 D32
 D33
 D4
 D40
 D45
 D5
 D50
 D54
 D6
 D60
 D7
 D8
 D9
(31 rows — 30 named vargas + CROSS)
```

**Inventory vs. classical 20-varga standard set:**

| Present | Missing from classical 20 |
|---------|--------------------------|
| D1, D2, D3, D4, D5, D6, D7, D8, D9, D10, D11, D12, D16, D20, D24, D27, D30, D40, D45, D60 | None — all 20 present |
| Supplementary: D14, D15, D21, D32, D33, D50, D54, D108, D150, D2700 | All extras present |
| CROSS (cross-varga analysis rows) | — |

**Answer:** All 20 standard Parashari vargas are present; an additional 10 supplementary vargas (D14, D15, D21, D32, D33, D50, D54, D108, D150, D2700) plus CROSS rows are also stored — 31 total distinct varga values.

---

## ⭐ Q3 — Strength: Shadbala / Vimsopaka / Ashtakavarga

### Strength-related fact categories

**Query:**
```sql
SELECT DISTINCT fact_category, count(*) as cnt 
FROM chart_facts 
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' 
  AND (fact_category LIKE '%shadbala%' OR fact_category LIKE '%vimsopaka%' 
    OR fact_category LIKE '%bala%' OR fact_category LIKE 'ashtakavarga%')
GROUP BY fact_category ORDER BY fact_category;
```

**Result:**
```
         fact_category           | cnt 
-----------------------------------+-----
 ashtakavarga_anubindu             | 420
 ashtakavarga_bindu                | 480
 ashtakavarga_pinda_bhinna         |  40
 ashtakavarga_pinda_sarva          |  40
 ashtakavarga_pinda_sodhita        |  40
 bhava_bala_aspectual              |  60
 bhava_bala_directional            |  60
 bhava_bala_lord                   |  60
 bhava_bala_occupant               |  60
 bhava_bala_positional             |  60
 bhava_bala_temporal               |  60
 bhava_bala_total_extended         |  60
 chandra_bala_natal_baseline       |  60
 graha_avastha_baladi              |  45
 graha_saptavargaja_bala_component |  35
 graha_shadbala_cheshta            |  35
 graha_shadbala_dig                |  35
 graha_shadbala_drik               |  35
 graha_shadbala_kala               |  35
 graha_shadbala_naisargika         |   7
 graha_shadbala_sthana             |  35
 graha_shadbala_total              |  42
 graha_tara_bala                   | 150
 graha_vimsopaka_dasavarga         |  35
 graha_vimsopaka_saptavarga        |  35
 graha_vimsopaka_shadvarga         |  35
 graha_vimsopaka_shodasavarga      |  35
 house_bhava_bala_subscore         | 180
 house_bhava_bala_total            |  60
 tara_bala_natal_baseline          | 135
 vimsopaka_bala_per_graha          |  35
(31 rows)
```

### Shadbala

**Query:**
```sql
SELECT DISTINCT fact_category, fact_key FROM chart_facts 
WHERE chart_id='...' AND fact_category LIKE '%shadbala%'
ORDER BY fact_category, fact_key;
```

**Result:**
```
       fact_category       |   fact_key    
---------------------------+---------------
 graha_shadbala_cheshta    | rupa
 graha_shadbala_dig        | rupa
 graha_shadbala_drik       | rupa
 graha_shadbala_kala       | rupa
 graha_shadbala_naisargika | rupa
 graha_shadbala_sthana     | rupa
 graha_shadbala_total      | required_rupa
 graha_shadbala_total      | rupa
```

**Varga dimension?** NO. All shadbala categories carry a single `rupa` value per graha per ayanamsha (7 grahas × 5 ayanamshas = 35 rows per component). The `graha_shadbala_sthana` component — which classically includes saptavargaja bala — does NOT break out per-varga in `chart_facts`; it stores only the rolled-up score. The per-varga breakdown lives in `chart_divisionals.varga_saptavargaja_bala_component` (7 vargas: D1, D2, D3, D9, D12, D30, D60 — the classical Saptavarga set).

### Vimsopaka

**Query:**
```sql
SELECT DISTINCT fact_category, fact_key FROM chart_facts 
WHERE chart_id='...' AND fact_category LIKE '%vimsopaka%';
```

**Result:**
```
        fact_category         |    fact_key     
------------------------------+-----------------
 graha_vimsopaka_dasavarga    | score
 graha_vimsopaka_saptavarga   | score
 graha_vimsopaka_shadvarga    | score
 graha_vimsopaka_shodasavarga | score
 vimsopaka_bala_per_graha     | vimsopaka_total
```

**Per-varga contribution (chart_divisionals):**
```sql
SELECT DISTINCT varga FROM chart_divisionals 
WHERE chart_id='...' AND fact_category='varga_vimsopaka_contribution'
ORDER BY varga;
```
Result: D1, D10, D12, D16, D2, D20, D24, D27, D3, D30, D4, D40, D45, D60, D7, D9 (16 vargas — the Shodasavarga set).

**Varga dimension?** YES — partially. `chart_facts` stores aggregate scores for four standard groups (Shadvarga/Saptavarga/Dasavarga/Shodasavarga). `chart_divisionals.varga_vimsopaka_contribution` holds the per-varga contribution for all 16 Shodasavarga charts. There is NO per-varga vimsopaka score stored for non-Shodasavarga charts (D5, D6, D8, D11, D14, D15, D21, etc.).

### Ashtakavarga

**Result:**
```
     fact_category     |    fact_key     | fact_subject (sample)
-----------------------+-----------------+----------------------
 ashtakavarga_anubindu | anubindu_bindus | JUP-HOUSE_1 ... JUP-HOUSE_12
 ashtakavarga_bindu    | bindu_count     | JUP-SIGN_1 ... etc.
 ashtakavarga_pinda_*  | (totals)        | SARVA / per-graha
```

**Varga dimension?** NO. Ashtakavarga data in `chart_facts` is D1-only (house/sign scores for the natal D1 chart). No per-varga BAV is stored.

**Answer (Q3 summary):** Shadbala is D1-only (rolled-up per graha). Vimsopaka has per-varga contribution data in `chart_divisionals` for the Shodasavarga set (16 vargas), with aggregate group-scores in `chart_facts`. Ashtakavarga is D1-only. The `graha_dignity_per_varga` category (1,350 rows) already covers ALL 30 vargas per graha per ayanamsha — that is the most varga-complete strength-related dataset in L1.

---

## ⭐ Q4 — Sensitive Points: Inventory + Diff

### Categories found

**Query:**
```sql
SELECT DISTINCT fact_category, count(*) as cnt 
FROM chart_facts 
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' 
  AND (fact_category LIKE '%upagraha%' OR fact_category LIKE '%saham%' OR ...)
GROUP BY fact_category ORDER BY fact_category;
```

**Result:**
```
            fact_category            | cnt  
-------------------------------------+------
 aprakasha_position                  |  175
 arudha_pada                         |  285
 aspect_tajik                        |   25
 bhrigu_nadi_point                   |  280
 cusp_kp_lords                       |  240
 esoteric_point_avayogi              |   70
 esoteric_point_bhrigu_bindu         |   35
 esoteric_point_brahma               | (via distinct)
 esoteric_point_chatushphuta         | (via distinct)
 esoteric_point_mrityu               | (via distinct)
 esoteric_point_panchasphuta         |   70
 esoteric_point_pranapada_sphuta     |   35
 esoteric_point_shiva                | (via distinct)
 esoteric_point_sri_yantra_position  | (via distinct)
 esoteric_point_trikona_dasha_sphuta |   35
 esoteric_point_trisphuta            |   35
 esoteric_point_vishnu               | (via distinct)
 esoteric_point_yogi                 |   70
 graha_kp_lords                      |  200
 graha_special_state_rollup          |  225
 graha_yoga_karaka_flag              |   35
 karaka_chara_position               |  525
 karaka_house_lord_overlap_flag      |   60
 karakamsa_position                  |   15
 karakatva_strength_per_significance |  300
 kp_cuspal_significators             |  240
 kp_ruling_planets_natal             |   50
 lal_kitab_special_point             |  100
 midpoint                            | 1080
 nakshatra_pada_sensitive            |   80
 panchanga_gulika_kalam              |    3
 panchanga_special_yoga_combinations |   15
 saham_position                      | 2800
 tajik_hadda_lord                    | 1200
 tajik_triraashipathi                |   10
 tajik_vargottama_specific           |   15
 upagraha_position                   |  210
(31 rows)
```

### (a) Varga dimension on sensitive points?

Arudha_pada keys: `longitude_sidereal`, `sign`, `house_d1` — NO varga dimension.  
Upagraha_position sample: tied to `ayanamsha_id` only — D1 positions only, NO varga dimension.  
All sensitive-point categories in `chart_facts` are D1-only (no varga column or fact_key encoding a varga).

### (b) Inventory vs. classical universe

**Gulika/Mandi:**
- `panchanga_gulika_kalam` stores the Gulika Kalam time window (start/end/duration) for the birth day — 3 rows only.
- **PRESENT as time-window**; positional longitude/house placement of Gulika as a sensitive point **NOT separately stored** in a dedicated point category. The `aprakasha_position` table holds: DHWAJA, KANDANGA, PATALA, PIDAA, VIGHNI (5 Sun-derived minor points) — Gulika/Mandi longitude is absent here.
- **GAP:** Gulika/Mandi as a positional sensitive point (longitude + house) is missing from `chart_facts`.

**Rahu-derived Upagrahas (5 sub-Rahu):**
- `upagraha_position` holds: DHUMA, INDRACHAPA, PARIVESHA, UPAKETU, VYATIPATA.
- **PRESENT: all 5 Rahu-derived upagrahas.**

**Sun-derived upagrahas (Kala/Mrityu/Artha-Prahara/Yamaghantaka):**
- `aprakasha_position` holds: DHWAJA, KANDANGA, PATALA, PIDAA, VIGHNI (these are the 5 aprakasha grahas, not identical to Kala/Mrityu/Artha-Prahara/Yamaghantaka).
- **GAP:** Classical Sun-derived upagrahas Kala, Mrityu, Artha-Prahara, Yamaghantaka are NOT found in either `upagraha_position` or `aprakasha_position`.

**Bhrigu Bindu:**
- `esoteric_point_bhrigu_bindu` → subject `BHRIGU_BINDU`.
- **PRESENT.**

**Bhrigu Nadi Points:**
- `bhrigu_nadi_point` → subjects BHRIGU_CHAKRA_1 through BHRIGU_CHAKRA_8 (8 points).
- **PRESENT** (extended Bhrigu system).

**Arudha Padas:**
- `arudha_pada` → A1–A12 (12 bhava arudhas) + graha arudhas (ARUDHA_JU, ARUDHA_MA, ARUDHA_ME, ARUDHA_MO, ARUDHA_SA, ARUDHA_SU, ARUDHA_VE) = 19 subjects.
- **PRESENT: A1–A12 (all 12 bhava arudhas). MISSING: UL (Upapada Lagna / A12 is present as ARUDHA_A12, but explicit UL label absent).** A7, A10 present. Graha arudhas present.

**Karakamsa/Swamsa:**
- `karakamsa_position` (15 rows) + `karaka_chara_position` (525 rows covering 8 chara karakas per ayanamsha).
- **PRESENT.**

**Pranapada:**
- `esoteric_point_pranapada_sphuta` → subject `PRANAPADA_SPHUTA`.
- **PRESENT.**

**Special Lagnas (Hora/Ghati/Bhava/Vighati):**
- No dedicated `special_lagna` category found. The query returned 0 rows for `fact_category LIKE '%lagna%'` in chart_facts beyond `graha_nakshatra_join`. The D9 Lagna special appears in `chart_divisionals.varga_d9_lagna_special`.
- **GAP:** Hora Lagna, Ghati Lagna, Vighati Lagna, Bhava Lagna as positional sensitive points in `chart_facts` are absent.

**Sphuta family:**
- `esoteric_point_trisphuta` → TRISPHUTA
- `esoteric_point_chatushphuta` → CHATUSHPHUTA (from distinct query result)
- `esoteric_point_panchasphuta` → PANCHASPHUTA
- `esoteric_point_pranapada_sphuta` → PRANAPADA_SPHUTA
- `esoteric_point_mrityu` → MRITYU_SPHUTA
- `esoteric_point_trikona_dasha_sphuta` → TRIKONA_DASHA_SPHUTA
- **PRESENT: Tri/Chatu/Pancha/Pranapada/Mrityu sphuta. MISSING: Beeja Sphuta, Kshetra Sphuta** (reproductive capacity sphuta pair — not found).

**Yogi/Avayogi:**
- `esoteric_point_yogi` → YOGI_POINT
- `esoteric_point_avayogi` → AVAYOGI_POINT
- **PRESENT. Nakshatra of Yogi Point is stored** (confirmed Chitra/Swati values). **GAP: Yogi Graha (the graha lord of Yogi nakshatra) and Dagdha Rashi** not found as separate records.

**Sahams:**
- `saham_position` → 70 distinct Saham subjects confirmed across two query batches: SAHAM_AASTHA through SAHAM_YATRA (70 named sahams).
- **Classical Parashari core (Punya/Yasha/Vidya/Karma/Bhagya etc.) PRESENT.**
- `tajik_hadda_lord` (1200 rows), `aspect_tajik`, `tajik_triraashipathi` — Tajik system data present.
- **Answer:** 70 Sahams stored. Classical Tajik 36-saham set: partially present (Tajik-specific data in `tajik_*` categories; cross-check between Saham list and the 36 standard Tajik Sahams requires per-saham audit — not blocking).

**Answer (Q4 summary):**  
(a) NO sensitive-point row in `chart_facts` carries a varga dimension — all are D1 with ayanamsha only.  
(b) **Present:** 5 Rahu-upagrahas, Bhrigu Bindu, 8 Bhrigu Chakra points, all 12 Bhava Arudhas + A7/A10 + graha arudhas, Karakamsa, Pranapada, Tri/Chatu/Pancha/Mrityu/Trikona sphuta, Yogi/Avayogi points, 70 Sahams, Tajik data, KP lords, Midpoints, Chara karakas.  
**Missing/Gap:** Gulika/Mandi positional longitude absent; Sun-derived upagrahas Kala/Mrityu/Artha-Prahara/Yamaghantaka absent; Hora/Ghati/Vighati/Bhava Lagna absent from `chart_facts`; Beeja Sphuta and Kshetra Sphuta absent; Yogi Graha and Dagdha Rashi absent as separate records.

---

## Q5 — Nakshatra Strength

**Query:**
```sql
SELECT DISTINCT fact_category, count(*) as cnt 
FROM chart_facts 
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category LIKE '%nakshatra%'
GROUP BY fact_category ORDER BY fact_category;
```

**Result:**
```
           fact_category           | cnt 
-----------------------------------+-----
 graha_nakshatra_join              | 700
 nakshatra_cogravity               |  10
 nakshatra_conjunction             |   1
 nakshatra_cross_ayanamsha         |  17
 nakshatra_dispositor              | 200
 nakshatra_pada_sensitive          |  80
 nakshatra_statistics              |  34
 panchanga_nakshatra_moon          |  25
 panchanga_nakshatra_shoonya_rashi |   2
(9 rows)
```

**Nakshatra dispositor sample:**
```
 fact_category      | fact_subject | fact_key     | fact_value_text
--------------------+--------------+--------------+----------------
 nakshatra_dispositor | SUN        | lord_chain   | ["Sun"]
 nakshatra_dispositor | SUN        | terminus_body| Sun
 nakshatra_dispositor | SUN        | chain_depth  | 1
```

**Nakshatra statistics sample keys include:** `dominant_gana`, `gana_deva_count`, `gana_manushya_count`, `gana_rakshasa_count`, `nadi_adi_count` — aggregate counts of nakshatra qualities across all chart bodies.

**Tara Bala:**
```
 graha_tara_bala | SUN  | tara_count | 25
 graha_tara_bala | SUN  | tara_position | 7
 graha_tara_bala | SUN  | tara_name  | Vadha
 graha_tara_bala | MOON | tara_name  | Janma
```
`graha_tara_bala` (150 rows) stores the Tara position of each graha from the natal Moon nakshatra — this IS a nakshatra-strength concept (Tara Bala = quality of each graha's nakshatra relationship to the natal Moon).

**Answer:** Tara Bala (graha_tara_bala, 150 rows) is present and constitutes a nakshatra-strength metric (each graha's tara count, tara position, and tara name relative to natal Moon). Nakshatra dispositor chains are stored. There is NO stored "nakshatra-dispositor strength score" (a numeric strength value derived from dispositor quality). Nakshatra statistics are aggregate counts (dominant gana etc.), not per-nakshatra strength rankings. **Tara Bala is the only nakshatra-strength metric present.**

---

## ⭐ Q6 — Planetary Condition Composite

**Query:**
```sql
SELECT DISTINCT fact_category, count(*) as cnt 
FROM chart_facts 
WHERE chart_id='...' 
  AND (fact_category LIKE '%condition%' OR fact_category LIKE '%avastha%'
    OR fact_category LIKE '%dignity%' OR fact_category LIKE '%combustion%'
    OR fact_category LIKE '%graha_sthiti%')
GROUP BY fact_category ORDER BY fact_category;
```

**Result:**
```
                fact_category                | cnt  
---------------------------------------------+------
 graha_avastha_baladi                        |   45
 graha_avastha_deepta                        |   45
 graha_avastha_jagrad                        |   45
 graha_avastha_lajjitadi                     |   45
 graha_avastha_lifetime_exposure_summary     |   45
 graha_avastha_sayanadi                      |   45
 graha_dignity_per_varga                     | 1350
 graha_effective_dignity_modified_by_aspects |   45
(8 rows)
```

### graha_dignity_per_varga — varga coverage

**Query:**
```sql
SELECT DISTINCT substring(fact_subject FROM '^[^_]+') as varga, count(*) as cnt
FROM chart_facts 
WHERE chart_id='...' AND fact_category='graha_dignity_per_varga'
GROUP BY 1 ORDER BY 1;
```

**Result:**
```
 varga | cnt 
-------+-----
 D1    |  45
 D10   |  45
 D108  |  45
 D11   |  45
 D12   |  45
 D14   |  45
 D15   |  45
 D150  |  45
 D16   |  45
 D2    |  45
 D20   |  45
 D21   |  45
 D24   |  45
 D27   |  45
 D2700 |  45
 D3    |  45
 D30   |  45
 D32   |  45
 D33   |  45
 D4    |  45
 D40   |  45
 D45   |  45
 D5    |  45
 D50   |  45
 D54   |  45
 D6    |  45
 D60   |  45
 D7    |  45
 D8    |  45
 D9    |  45
(30 rows — all vargas, 45 rows each = 9 grahas × 5 ayanamshas)
```

### graha_composite_state_classification sample

```
            fact_category             | fact_subject |    fact_key    |    fact_value_text     
--------------------------------------+--------------+----------------+------------------------
 graha_composite_state_classification | JUP          | classification | debilitation_cancelled
 graha_composite_state_classification | MAR          | classification | well_placed
 graha_composite_state_classification | KET_MEAN     | classification | neutral
```

### ga_condition_composite table

```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema='public' AND table_name LIKE '%condition%';
```
Result: 0 rows — no `ga_condition_composite` table exists. Condition data lives entirely in `chart_facts`.

**Components of the composite:**
1. `graha_composite_state_classification` — single composite label per graha per ayanamsha.
2. `graha_avastha_sayanadi` — Sayana/Upavesa/Netrapanya/Prakasha/Gamana avasthas.
3. `graha_avastha_jagrad` — Jagrad/Swapna/Sushupti.
4. `graha_avastha_deepta` — Deepta/Svastha/Mudita/Shanta/Deena/Dukhita/Vikala/Khala/Kopa.
5. `graha_avastha_baladi` — Bala/Kumara/Yuva/Vriddha/Mrita.
6. `graha_avastha_lajjitadi` — Lajjita/Garvita/Kshudhita/Trushita/Mudita/Kshobhita.
7. `graha_avastha_lifetime_exposure_summary` — aggregate avastha exposure counts.
8. `graha_effective_dignity_modified_by_aspects` — dignity modified by aspect influence.
9. `graha_dignity_per_varga` — dignity state (own/exalted/debilitated/friendly/neutral/enemy) per varga.

**Does DIGNITY span vargas?** YES — `graha_dignity_per_varga` covers all 30 vargas × 9 grahas × 5 ayanamshas = 1,350 rows. This is the most complete per-varga coverage of any single metric in L1.

**Answer:** No `ga_condition_composite` table exists; the composite is assembled from 9 `chart_facts` categories. The dignity dimension spans ALL 30 vargas already. Avastha dimensions (sayanadi, jagrad, deepta, baladi, lajjitadi) are D1-only (45 rows = 9 grahas × 5 ayanamshas). No combustion-specific category was found — combustion_state is encoded within `graha_position` fact_key `combustion_state`.

---

## Q7 — Transit Natal Anchors

**Query:**
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema='public' AND table_name LIKE '%transit%';
```

**Result:**
```
     table_name     
--------------------
 bg_transit_engine
 bg_transit_rules
 ga_transit_anchors
(3 rows)
```

**Schema of ga_transit_anchors:**
```
      column_name      |        data_type         
-----------------------+--------------------------
 id                    | integer
 chart_id              | uuid
 build_id              | text
 ayanamsha_id          | text
 graha                 | text
 natal_sign            | text
 natal_house_from_moon | integer
 natal_degree_absolute | double precision
 computed_at           | timestamp with time zone
(9 columns)
```

**Sample rows:**
```
 id | ayanamsha_id        | graha   | natal_sign  | natal_house_from_moon | natal_degree_absolute
----+---------------------+---------+-------------+-----------------------+----------------------
 46 | lahiri_chitrapaksha | jupiter | sagittarius |                    11 |  249.787497023181
 47 | lahiri_chitrapaksha | ketu    | scorpio     |                    10 |  229.033044100281
 48 | lahiri_chitrapaksha | mars    | libra       |                     9 |  198.519187554622
 50 | lahiri_chitrapaksha | moon    | aquarius    |                     1 |  327.055230133129
 53 | lahiri_chitrapaksha | sun     | capricorn   |                    12 |  291.962617284992
```

**Counts:**
```
 total | distinct_grahas | distinct_ayanamshas 
-------+-----------------+---------------------
    45 |               9 |                   5
(9 grahas × 5 ayanamshas = 45 rows)
```

**Transit categories in chart_facts:** 0 rows (no transit-time data in chart_facts).

**Answer:** `ga_transit_anchors` stores ONLY the natal positions of 9 grahas (Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn/Rahu/Ketu) across 5 ayanamshas — 45 rows total. Each row = natal sign + house-from-Moon + absolute longitude. This is exclusively the static natal anchor table (time-invariant per build). No transit positions over time are stored here. `bg_transit_engine` and `bg_transit_rules` hold the rule engine/configuration, not per-chart data.

---

## Q8 — Medical/Ayurvedic

### bg_medical_mappings schema and content

**Schema:**
```
    column_name     | data_type 
--------------------+-----------
 id                 | integer
 graha              | text
 dosha              | ARRAY
 dhatu              | ARRAY
 organ_systems      | ARRAY
 body_part          | ARRAY
 disease_tendency   | ARRAY
 classical_citation | text
```

**Sample rows:**
```
 id | graha   | dosha        | dhatu                 | organ_systems            | body_part                 | disease_tendency                                | classical_citation
----+---------+--------------+-----------------------+--------------------------+---------------------------+-------------------------------------------------+--------------------
  1 | Sun     | {pitta}      | {asthi}               | {heart,eyes}             | {right_eye,spine,heart}   | {heart_disease,eye_problems,bone_disorders}     | BPHS Ch.18 / Ashtanga Hridayam
  2 | Moon    | {kapha,vata} | {rasa}                | {mind,lungs,stomach}     | {left_eye,breast,uterus}  | {mental_disorders,respiratory,digestive}        | BPHS Ch.18 / Charaka Samhita
  3 | Mars    | {pitta}      | {rakta,mamsa}         | {marrow,red_blood_cells} | {right_ear,bile,genitals} | {blood_disorders,inflammation,accidents}        | BPHS Ch.18 / Ashtanga Hridayam
  4 | Mercury | {tridosha}   | {skin,nervous_tissue} | {nervous_system,skin}    | {tongue,hands,arms}       | {nervous_disorders,skin_diseases,speech_disorders} | BPHS Ch.18 / Charaka Samhita
  5 | Jupiter | {kapha}      | {meda,majja}          | {liver,pancreas}         | {thighs,liver,ears}       | {obesity,liver_disorders,diabetes}              | BPHS Ch.18 / Ashtanga Hridayam
  6 | Venus   | {kapha,vata} | {shukra,rasa}         | {reproductive,kidneys}   | {face,neck,genitals}      | {reproductive_disorders,venereal,kidney_stones} | BPHS Ch.18 / Charaka Samhita
  7 | Saturn  | {vata}       | {asthi,nervous}       | {large_intestine,spleen} | {teeth,bones,joints,legs} | {chronic_diseases,arthritis,paralysis}          | BPHS Ch.18 / Ashtanga Hridayam
  8 | Rahu    | {vata}       | {skin}                | {nervous_system}         | {skin,limbs}              | {mysterious_diseases,cancer_indications,poisons}| BPHS Ch.18 (Rahu)
  9 | Ketu    | {pitta,vata} | {marrow}              | {intestines}             | {abdomen,anus}            | {intestinal_worms,abdominal_disorders}          | BPHS Ch.18 (Ketu)
(9 rows)
```

### bg_nakshatra_medical schema and content

**Schema:** nakshatra_name, nakshatra_number, body_part, classical_citation (5 cols, 27 rows covering all 27 nakshatras).

**Sample:**
```
 nakshatra_name | nakshatra_number | body_part     | classical_citation
----------------+------------------+---------------+--------------------------
 Ashwini        |                1 | feet/knees    | Ashtanga Hridayam / BPHS
 Bharani        |                2 | head          | Ashtanga Hridayam / BPHS
 Krittika       |                3 | eyes/face     | Ashtanga Hridayam / BPHS
 Rohini         |                4 | forehead/neck | Ashtanga Hridayam / BPHS
```

### ga_medical schema and content

**Schema:** chart_id, ayanamsha_id, graha, natal_sign, natal_nakshatra, indication_strength, dosha_aggravated (ARRAY), organ_watch (ARRAY), body_part_watch (ARRAY), nakshatra_body_part, indication_tier, not_diagnosis (boolean), classical_citation.

**Per-chart content:**
```
  graha  | cnt 
---------+-----
 Jupiter |   5
 Ketu    |   5
 Mars    |   5
 Mercury |   5
 Moon    |   5
 Rahu    |   5
 Saturn  |   5
 Sun     |   5
 Venus   |   5
(9 rows — 9 grahas × 5 ayanamshas = 45 rows total)
```

**Sample:**
```
 graha   | natal_sign  | natal_nakshatra | indication_strength | indication_tier    | dosha_aggravated | organ_watch
---------+-------------+-----------------+---------------------+--------------------+------------------+------------------
 Jupiter | Sagittarius | Mula            | mild                | jyotish_indication | {kapha}          | {liver,pancreas}
 Ketu    | Scorpio     | Jyeshtha        | moderate            | jyotish_indication | {pitta,vata}     | {intestines}
 Mars    | Libra       | Swati           | moderate            | jyotish_indication | {pitta}          | {marrow,red_blood_cells}
```

**Answer:**  
- `bg_medical_mappings` (L0, 9 rows) = static lookup: graha → dosha/dhatu/organ_systems/body_part/disease_tendency, sourced from BPHS Ch.18.  
- `bg_nakshatra_medical` (L0, 27 rows) = static lookup: nakshatra → body_part per Ashtanga Hridayam/BPHS.  
- `ga_medical` (L1, 45 rows for native) = per-chart derivation: for each graha in its natal sign/nakshatra, combines graha dosha with nakshatra body_part to produce an indication_strength (mild/moderate/strong), dosha_aggravated, organ_watch, body_part_watch, with `not_diagnosis=true` flag on every row.  
The `ga_medical` computation is graha×sign×nakshatra → indication only; no house-health mapping or sign-body-part mapping layer is present in the per-chart output.

---

## Summary: Sizing Answers for L1 Enrichment Amendments

| Expansion | Current Coverage | Gap |
|-----------|-----------------|-----|
| Shadbala per-varga | D1-only rolled-up score in `chart_facts`; per-varga saptavargaja breakdown exists in `chart_divisionals` for 7 classical vargas (D1/D2/D3/D9/D12/D30/D60) | Shadbala components per each of 30+ vargas not stored |
| Vimsopaka varga-groups | 4 group scores in `chart_facts` (Shad/Sapta/Dasa/Shodasa); per-varga contribution stored in `chart_divisionals` for Shodasavarga 16 charts | Non-Shodasavarga vargas (D5, D6, D8, D11, D14, D15, D21 etc.) have no vimsopaka contribution row |
| Ashtakavarga per-varga | D1-only BAV in `chart_facts` | No BAV for D9 or any other varga |
| Sensitive points: missing | Rahu-5 upagrahas PRESENT; Bhrigu Bindu PRESENT; A1–A12 + A7/A10 PRESENT; Karakamsa PRESENT; Pranapada PRESENT; 70 Sahams PRESENT | Gulika/Mandi positional; Sun-derived upagrahas (Kala/Mrityu/Artha-Prahara/Yamaghantaka); Hora/Ghati/Vighati/Bhava Lagna; Beeja/Kshetra Sphuta; Yogi Graha + Dagdha Rashi |
| Dignity per-varga | FULLY PRESENT — all 30 vargas × 9 grahas × 5 ayanamshas = 1,350 rows | No gap |
| Avastha per-varga | D1-only (45 rows per avastha category) | Avasthas for D9 and other vargas not computed |
| Nakshatra strength (Tara Bala) | PRESENT — graha_tara_bala (150 rows) | No numeric nakshatra-dispositor strength score stored |
| Transit anchors | PRESENT — 45 rows (9 grahas × 5 ayanamshas), natal positions only | No transit-over-time data (by design) |
| Medical/Ayurvedic | PRESENT — 45 per-chart rows (graha×sign×nakshatra indication) + static L0 lookups | House-health and sign-body-part mappings not in ga_medical per-chart output |

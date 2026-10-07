# Row diff — bg_remedies (brahma_remedy_corpus), citation pass 2

Decision OS-2026-10-05-CITATIONS (ACHARYA/CITATION_PASS2/PASS2_DECISIONS.tsv, 101 brahma_remedy_corpus rows): 25 removed, 30 CONTENT_FIX+K1, 5 CONTENT_FIX+K2, 40 LABEL_K2_MODERN, 1 KEEP_UNVERIFIED_LABELLED.
The 54 corpus-sweep rows and the 4 tantric rows are untouched by this decision and are identical before and after.

Table `brahma_remedy_corpus`, natural key `remedy_id`. Before = the writer replayed from origin/main; after = the writer replayed from this branch (both on a disposable local PostgreSQL, no production access).

| | rows |
|---|---|
| before | 341 |
| after | 316 |
| removed | 26 |
| added | 1 |
| changed (same key) | 75 |
| unchanged | 240 |

The one rename (`dosha_kemadruma_compat_kuja_mars` -> `dosha_kuja_from_venus_mars`) changes a natural key, so it is listed once under Removed and once under Added; its content is the same except the K2 label, source id and confidence (see Added).

Mars japa count: left at 10,000 by SS directive and flagged 'count under verification: corpus scan reads "I 1000" (10,000 or 11,000); row keeps 10,000 until the page image is checked'; the K1 excerpt quotes the scan literally ('Mars I 1000') in all nine japa rows.

All 45 K2 rows: classical_ref is the K2 label wording 'modern practice / project judgment — OS-2026-10-05-CITATIONS' (42 rows; the three rows the TSV words individually keep theirs). SS ruling 2026-10-05, N-151.

PROPOSED ADDITION for the owner (NOT authored; remedies stay 316): one K1 row dosha_koota_parihara_dana_mc34 (record 6 item 1, MC Vivaha v.34 tika, muhurta_chintamani:PG97:C1) replacing the 11 removed kuta-puja rows.

## Removed (26)

- `dosha_bhakoot_vishnu_puja` — REMOVE
- `dosha_gana_shiva_puja` — REMOVE
- `dosha_graha_maitri_puja` — REMOVE
- `dosha_kala_sarpa_anant_shanti` — REMOVE
- `dosha_kala_sarpa_ghatak_shanti` — REMOVE
- `dosha_kala_sarpa_karkotak_shanti` — REMOVE
- `dosha_kala_sarpa_kulik_shanti` — REMOVE
- `dosha_kala_sarpa_mahapadma_shanti` — REMOVE
- `dosha_kala_sarpa_padma_shanti` — REMOVE
- `dosha_kala_sarpa_shankhachud_shanti` — REMOVE
- `dosha_kala_sarpa_shankhpal_shanti` — REMOVE
- `dosha_kala_sarpa_sheshnag_shanti` — REMOVE
- `dosha_kala_sarpa_takshak_shanti` — REMOVE
- `dosha_kala_sarpa_vasuki_shanti` — REMOVE
- `dosha_kala_sarpa_vishdhar_shanti` — REMOVE
- `dosha_kemadruma_compat_kuja_mars` — LABEL_K2_MODERN + RENAME to dosha_kuja_from_venus_mars (appears as removed + added: the natural key changes)
- `dosha_mahendra_vishnu_puja` — REMOVE
- `dosha_rajju_shiva_puja` — REMOVE
- `dosha_stree_deergha_puja` — REMOVE
- `dosha_tara_nakshatra_puja` — REMOVE
- `dosha_varna_surya_mantra` — REMOVE
- `dosha_vashya_venus_mantra` — REMOVE
- `dosha_vedha_nakshatra_puja` — REMOVE
- `dosha_vish_dosha_shani_chandra` — REMOVE
- `dosha_vish_kanya_puja` — REMOVE
- `dosha_yoni_puja` — REMOVE

## Added (1)

- `dosha_kuja_from_venus_mars` — RENAME of dosha_kemadruma_compat_kuja_mars (TSV: follows the dosha rename)

## Changed (75)

### `dosha_abhukta_mula_shanti` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `deity`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: religious remedial rites should be performed after the 12th day after the birth ; Instal a kalasha and put in it Panchagavya ... idol of the Rakshasa ... facing west ... worship of its Adhideva Indra and Pratyadhideva Jala
- `classical_ref`
  - before: classical tradition (Abhukta Mula shanti)
  - after: BPHS Ch.93 §1-4, §10-20 — bphs:PG1021:C1, bphs:PG1023:C1
- `deity`
  - before: Ketu/Nirriti
  - after: Rākṣasa (Mūla); adhideva Indra; pratyadhideva Jala
- `prescription_text`
  - before: For Abhukta Mula Dosha: perform the prescribed Abhukta Mula Shanti immediately after birth — the traditional shanti for this junction is more urgent than the general Mool Shanti. Propitiate Ketu and the presiding deity of Mula nakshatra.
  - after: Abhukta-Mūla śānti per BPHS Ch.93: rites after the 12th day from birth (§3-4); kalaśa with pañcagavya, śatauṣadhi and holy-river water; idol of the Rākṣasa (Mūla's deity) facing west on a hundred-holed earthen pot, worshipped with white flowers, sandal and cloth; worship of adhideva Indra and pratyadhideva Jala (§10-20). Until then the father does not see the child (§1-2).
- `source_canonical_id`
  - before: classical_tradition
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.93 §3-4 — bphs:PG1021:C1 — "religious remedial rites should be performed after the 12th day after the birth" ; K1 — BPHS Ch.93 §10-20 — bphs:PG1023:C1 — "Instal a kalasha and put in it Panchagavya ... idol of the Rakshasa ... facing west ... worship of its Adhideva Indra and Pratyadhideva Jala"

### `dosha_angarak_mars_rahu` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (Angarak dosha upaya)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `prescription_text`
  - before: For Angarak Dosha (Mars-Rahu): perform Hanuman puja on Tuesdays and Rahu shanti on Saturdays. Recite Hanuman Chalisa daily. Donate blood (blood donation) on Tuesdays. Wear red coral (if Mars is functional benefic).
  - after: For Angarak Dosha (Mars-Rahu): perform Hanuman puja on Tuesdays and Rahu shanti on Saturdays. Recite Hanuman Chalisa daily. Donate blood (blood donation; modern practice) on Tuesdays. Wear red coral (if Mars is functional benefic).
- `source_canonical_id`
  - before: classical_tradition
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha_dhaiya_shani_puja` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (Dhaiya upaya)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: classical_tradition
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha_grahan_surya_chandra_mantra` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (Grahan dosha upaya)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: classical_tradition
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — BPHS Ch.91 (Birth in Eclipses) §1-14 — bphs:PG1016:C1 — "a person whose birth takes place at the time of solar or lunar eclipse suffers from ailments, distress and poverty and faces danger of death" — classical doṣa is birth DURING an eclipse; luminary-conjunct-node is a modern generalisation

### `dosha_guru_chandal_jupiter_puja` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (Guru Chandal upaya)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: classical_tradition
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha_kala_amrita_shanti` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (Kala Amrita upaya)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.75
  - after: 0.6
- `source_canonical_id`
  - before: classical_tradition
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha_kala_sarpa_mantra` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (Kala Sarpa shanti)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: classical_tradition
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha_kala_sarpa_nag_puja` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (Kala Sarpa upaya)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: classical_tradition
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha_kuja_from_moon_hanuman` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (Moon-referenced Manglik upaya)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: classical_tradition
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha_mool_shanti` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: father should see the child born only on the morning next to the end of the days of Sutaka ... Giving a cow with calf in charity in the case of Nakshatra Gandanta ; rites should be performed after the 12th day after the birth ; 3 cows ... Jyestha Moola and Ashlesha Makha ... 2 cows in Revati-Ashwini … [350 chars]
- `classical_ref`
  - before: classical tradition (Mool Shanti — 27th-day puja)
  - after: BPHS Ch.92 §6-8 (bphs:PG1019:C1); Ch.93 §3-4 (bphs:PG1021:C1); Ch.94 §6-9 (bphs:PG1026:C1)
- `prescription_text`
  - before: For Mool (Gandmool) Dosha: perform Mool Shanti puja on the 27th day after birth (or at the next occurrence of the birth nakshatra). Propitiate the birth nakshatra's deity. This is the classical prescriptive timing in tradition.
  - after: Gaṇḍānta / gaṇḍamūla śānti: performed after the sūtaka days / after the 12th day, the father seeing the child only then (BPHS Ch.92 §6-8; Ch.93 §3-4). Gifts: a cow with calf for nakṣatra-gaṇḍānta (Ch.92 §6-8); by junction 3 cows (Jyeṣṭhā–Mūla, Āśleṣā–Maghā), 2 (Revatī–Aśvinī), 1 (others) or their value (Ch.94 §8-9); Mṛtyuñjaya japa and abhiṣeka (Ch.94 §6).
- `source_canonical_id`
  - before: classical_tradition
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.92 §6-8 — bphs:PG1019:C1 — "father should see the child born only on the morning next to the end of the days of Sutaka ... Giving a cow with calf in charity in the case of Nakshatra Gandanta" ; K1 — BPHS Ch.93 §3-4 — bphs:PG1021:C1 — "rites should be performed after the 12th day after the birth" ; K1 — BPHS Ch.94 §6-9 — bphs:PG1026:C1 — "3 cows ... Jyestha Moola and Ashlesha Makha ... 2 cows in Revati-Ashwini ... 1 cow in other gandantas ... Mrityunjaya japa"

### `dosha_mrityu_bhaga_mantra` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (Mrityu Bhaga upaya)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.75
  - after: 0.6
- `prescription_text`
  - before: For Mrityu Bhaga Dosha: propitiate the afflicted planet with its beej mantra 108 times daily. Perform Mahamrityunjaya japa (11,000 minimum). The 'death-degree' position is pacified by strengthening the planet's digbala, dasha timing awareness, and puja on its day.
  - after: For Mrityu Bhaga Dosha: propitiate the afflicted planet with its beej mantra 108 times daily. Perform Mahamrityunjaya japa (11,000 minimum — a project parameter, not a classical count). The 'death-degree' position is pacified by strengthening the planet's digbala, dasha timing awareness, and puja on its day.
- `source_canonical_id`
  - before: classical_tradition
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha_nadi_mahamrityunjaya` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: a śānti for the nāḍī, namely: japa of the Mṛtyuñjaya and other mantras, the gift of a golden nāḍī, and — in the varṇa and the other kūṭas — the giving of a cow, grain, cloth and gold
- `classical_ref`
  - before: classical tradition (Nadi Dosha niraakarana)
  - after: MC Vivāha-prakaraṇa v.34 ṭīkā — muhurta_chintamani:PG97:C1
- `prescription_text`
  - before: For Nadi Dosha (compatibility): perform a Mahamrityunjaya mantra japa of 1,25,000 (1.25 lakh) before marriage. Perform Nadi Niraakarana puja prescribed by a learned astrologer. This dosha is among the most serious in Ashtakoota.
  - after: Nāḍī-doṣa śānti per MC Vivāha v.34 ṭīkā: japa of the Mṛtyuñjaya and other mantras, and the gift of a golden nāḍī (for the other kūṭas: a cow, grain, cloth and gold); applied when the parihāras of vv.32-37 obtain. [Modern elaboration, labelled: the 1,25,000 count; "Nadi Nirākaraṇa pūjā prescribed by a learned astrologer".]
- `source_canonical_id`
  - before: classical_tradition
  - after: muhurta_chintamani
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — Muhurta Chintamani Vivāha-prakaraṇa v.34 ṭīkā — muhurta_chintamani:PG97:C1 — "a śānti for the nāḍī, namely: japa of the Mṛtyuñjaya and other mantras, the gift of a golden nāḍī, and — in the varṇa and the other kūṭas — the giving of a cow, grain, cloth and gold"

### `dosha_pitru_surya_mantra` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (Pitru Dosha — Sun upaya)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: classical_tradition
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha_pitru_tarpan` — KEEP_UNVERIFIED_LABELLED
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (Pitru Dosha upaya — Gaya Shraddha, Tarpan)
  - after: dharmaśāstra śrāddha prescription — text not in library
- `confidence`
  - before: 0.85
  - after: 0.6
- `source_canonical_id`
  - before: classical_tradition
  - after: k1_unverified
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1_UNVERIFIED — classical (dharmaśāstra) source claimed (pitṛ-tarpaṇa on amāvāsyā; Gayā-śrāddha), not verified in our library; needs Garuḍa Purāṇa Preta-kalpa or a smṛti śrāddha-prakaraṇa — none in corpus ; K2 — the attachment to "Pitru Dosha" is modern usage; ratified OS-2026-10-05-CITATIONS

### `dosha_punarphoo_shani_mantra` — CONTENT_FIX+K2
fields changed: `classical_ref`, `confidence`, `contraindications`, `domain`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (Punarphoo upaya)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `contraindications`
  - before: null
  - after: No blanket gem advice: a Pearl for the Moon only after functional-benefic assessment
- `domain`
  - before: marriage
  - after: general
- `prescription_text`
  - before: For Punarphoo Dosha (Saturn-Moon): recite Shani Chalisa on Saturdays and Chandra Ashtottara on Mondays. The Saturn-Moon combination delays but does not deny; patience and consistent practice are the core remedy.
  - after: For the Moon–Saturn conjunction/aspect (Punarphoo; popularly "Vish dosha"): Śani Chalisa on Saturdays and Candra Aṣṭottara on Mondays; Mahāmṛtyuñjaya japa; Śiva pūjā on Mondays (merged from the removed vish-dosha row). The combination delays but does not deny.
- `source_canonical_id`
  - before: classical_tradition
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; NAME COLLISION — the classical Viṣa-yoga is a tithi×vāra muhūrta yoga (muhurta_chintamani:PG17:C2 v.8); never cite it for Moon–Saturn

### `dosha_sade_sati_shani_charity` — CONTENT_FIX+K2
fields changed: `classical_ref`, `confidence`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (Sade Sati dana)
  - after: BPHS Ch.84 §25 — bphs:PG999:C1 (black cow); remainder modern
- `confidence`
  - before: 0.85
  - after: 0.6
- `prescription_text`
  - before: For Sade Sati: donate black sesame, mustard oil, iron, and black cloth to laborers or the poor on Saturdays throughout the 7.5-year period. Service to the elderly and underprivileged is the most direct Saturn remedy.
  - after: Classical Saturn dāna per BPHS Ch.84 §25: a black cow (bphs:PG999:C1). Modern practice, labelled (not from BPHS Ch.84 §25): for Sade Sati, donate black sesame, mustard oil, iron, and black cloth to laborers or the poor on Saturdays throughout the 7.5-year period. Service to the elderly and underprivileged is the most direct Saturn remedy. Note: in BPHS Ch.84 §25 iron is Rahu's dāna item, not Saturn's.
- `source_canonical_id`
  - before: classical_tradition
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1 — BPHS Ch.84 §25 — bphs:PG999:C1 — "things to be given in charity are (1) cow with calf, (2) conch, (3) bullock, (4) gold, (5) robes, (6) horse, (7) black cow, (8) weapons made of iron and (9) goat, respectively" (Saturn = black cow; iron = Rahu)

### `dosha_sade_sati_shani_mantra` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (Sade Sati upaya)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.85
  - after: 0.6
- `source_canonical_id`
  - before: classical_tradition
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha_shakata_guru_puja` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (Shakata yoga upaya)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.75
  - after: 0.6
- `source_canonical_id`
  - before: classical_tradition
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha_shrapit_shani_rahu` — CONTENT_FIX+K2
fields changed: `classical_ref`, `confidence`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (Shrapit Dosha upaya)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `prescription_text`
  - before: For Shrapit Dosha (Saturn-Rahu): perform a Shrapit Dosha Nivaran homa with prescribed samidha on Saturdays. Recite the Shrapit Dosha mantra 1,08,000 times. Donate black sesame and iron. Visit a Shani Shingnapur (or equivalent Shani temple) on Saturdays.
  - after: For Shrapit Dosha (Saturn-Rahu): perform a Shrapit Dosha Nivaran homa with prescribed samidha on Saturdays. Recite the Śani and Rāhu mantras (count a project parameter). Donate black sesame and iron. Visit a Shani Shingnapur (or equivalent Shani temple) on Saturdays (modern pilgrimage practice).
- `source_canonical_id`
  - before: classical_tradition
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `jupiter_matrix_behavioral` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (karaka conduct)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.85
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS (project doctrine: behavioural alignment as the deepest remedy)

### `jupiter_matrix_homa` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28
- `classical_ref`
  - before: classical tradition (graha-shanti homa)
  - after: BPHS Ch.84 §21-22 — bphs:PG999:C1
- `prescription_text`
  - before: Perform a Brihaspati/Vishnu / Jupiter graha-shanti homa (fire ritual) with the prescribed samidha (fire-wood) on Thursday. 1008 ahutis is the standard count for a full dasha-shanti.
  - after: Graha-śānti homa for Jupiter with its samidhā pippala (aśvattha) (BPHS Ch.84 §21-22), offered with honey, ghee, curd or milk; 108 (or 28) āhutis per the text. [Modern practice, labelled: larger counts such as 1008; weekday Thursday.]
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 §21-22 — bphs:PG999:C1 — "Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28"

### `jupiter_matrix_japa` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000
- `classical_ref`
  - before: classical tradition (dasha-japa counts)
  - after: BPHS Ch.84 §17-20 (Santhanam) — bphs:PG998:C1
- `prescription_text`
  - before: Complete the Jupiter mantra japa to its mahadasha count over the dasha period: recite 'Om Graam Greem Graum Sah Gurave Namah' on Thursdays and daily. Standard counts: Sun 7,000; Moon 11,000; Mars 10,000; Mercury 9,000; Jupiter 19,000; Venus 16,000; Saturn 23,000; Rahu 18,000; Ketu 17,000.
  - after: Japa of the Jupiter mantra to the BPHS count of 19,000 (BPHS Ch.84 §17-20, which pairs the counts with the Vedic graha-mantras). The bīja mantra carried here is the tantric navagraha bīja (Mantra Mahodadhi — not in our library; labelled K1_UNVERIFIED). Weekday is modern convention.
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 (Remedial measures) §17-20 — bphs:PG998:C1 — "mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000" ; K1_UNVERIFIED — the bīja mantra string (Oṃ … Saḥ … Namaḥ) is the tantric navagraha bīja: Mantra Mahodadhi claimed, not in our library (BPHS pairs the counts with the Vedic graha-mantras)

### `jupiter_matrix_puja` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `deity`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins
- `classical_ref`
  - before: classical tradition (graha-shanti puja)
  - after: BPHS Ch.84 §15-16 — bphs:PG998:C1
- `deity`
  - before: Brihaspati/Vishnu
  - after: Jupiter (BPHS Ch.84 §6-13 dhyāna form)
- `prescription_text`
  - before: Worship Brihaspati/Vishnu on Thursday with prescribed flowers, incense and lamp (graha-shanti puja for Jupiter). Chant the Jupiter Ashtottara (108 names) during the puja.
  - after: Graha-śānti pūjā of Jupiter per BPHS Ch.84 §15-16: offer flowers and garments of the planet's colour, sandal, lamp (dīpa), guggula incense, its metal and its grain, then give these to Brahmins; feed Brahmins the planet's food (§23-24). [Modern additions, labelled: weekday Thursday; Aṣṭottara-śata-nāma; popular deity association as currently in the deity field.]
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 §15-16 — bphs:PG998:C1 — "Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins" ; K1 — BPHS Ch.84 §3-13 — bphs:PG995:C1–PG997:C1 — idols/metals and dhyāna forms of the nine grahas ; K2 — weekday, Aṣṭottara-śata-nāma and the popular deity mapping (Rahu→Durga, Ketu→Ganesha, Saturn→Hanuman, Mercury→Vishnu) are modern convention; ratified OS-2026-10-05-CITATIONS

### `jupiter_matrix_vrata` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (navagraha vrata)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `jupiter_matrix_yantra` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (navagraha yantra)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — BPHS Ch.84 §5 — bphs:PG996:C1 — "sketches of all the above planets should be drawn in the colours belonging to them on a piece of cloth ... placed in their own directions" — classical analogue, not this bīja-yantra's source; Yantra Maharnava (sibling citation) not in library

### `ketu_matrix_behavioral` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (karaka conduct)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.85
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS (project doctrine: behavioural alignment as the deepest remedy)

### `ketu_matrix_homa` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28
- `classical_ref`
  - before: classical tradition (graha-shanti homa)
  - after: BPHS Ch.84 §21-22 — bphs:PG999:C1
- `prescription_text`
  - before: Perform a Ganesha / Ketu graha-shanti homa (fire ritual) with the prescribed samidha (fire-wood) on Saturday/Tuesday. 1008 ahutis is the standard count for a full dasha-shanti.
  - after: Graha-śānti homa for Ketu with its samidhā kuśa (BPHS Ch.84 §21-22), offered with honey, ghee, curd or milk; 108 (or 28) āhutis per the text. [Modern practice, labelled: larger counts such as 1008; weekday Saturday/Tuesday.]
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 §21-22 — bphs:PG999:C1 — "Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28"

### `ketu_matrix_japa` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000
- `classical_ref`
  - before: classical tradition (dasha-japa counts)
  - after: BPHS Ch.84 §17-20 (Santhanam) — bphs:PG998:C1
- `prescription_text`
  - before: Complete the Ketu mantra japa to its mahadasha count over the dasha period: recite 'Om Sraam Sreem Sraum Sah Ketave Namah' on Saturday/Tuesdays and daily. Standard counts: Sun 7,000; Moon 11,000; Mars 10,000; Mercury 9,000; Jupiter 19,000; Venus 16,000; Saturn 23,000; Rahu 18,000; Ketu 17,000.
  - after: Japa of the Ketu mantra to the BPHS count of 17,000 (BPHS Ch.84 §17-20, which pairs the counts with the Vedic graha-mantras). The bīja mantra carried here is the tantric navagraha bīja (Mantra Mahodadhi — not in our library; labelled K1_UNVERIFIED). Weekday is modern convention.
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 (Remedial measures) §17-20 — bphs:PG998:C1 — "mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000" ; K1_UNVERIFIED — the bīja mantra string (Oṃ … Saḥ … Namaḥ) is the tantric navagraha bīja: Mantra Mahodadhi claimed, not in our library (BPHS pairs the counts with the Vedic graha-mantras)

### `ketu_matrix_puja` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `deity`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins
- `classical_ref`
  - before: classical tradition (graha-shanti puja)
  - after: BPHS Ch.84 §15-16 — bphs:PG998:C1
- `deity`
  - before: Ganesha
  - after: Ketu (BPHS Ch.84 §6-13 dhyāna form)
- `prescription_text`
  - before: Worship Ganesha on Saturday/Tuesday with prescribed flowers, incense and lamp (graha-shanti puja for Ketu). Chant the Ketu Ashtottara (108 names) during the puja.
  - after: Graha-śānti pūjā of Ketu per BPHS Ch.84 §15-16: offer flowers and garments of the planet's colour, sandal, lamp (dīpa), guggula incense, its metal and its grain, then give these to Brahmins; feed Brahmins the planet's food (§23-24). [Modern additions, labelled: weekday Saturday/Tuesday; Aṣṭottara-śata-nāma; popular deity association as currently in the deity field.]
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 §15-16 — bphs:PG998:C1 — "Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins" ; K1 — BPHS Ch.84 §3-13 — bphs:PG995:C1–PG997:C1 — idols/metals and dhyāna forms of the nine grahas ; K2 — weekday, Aṣṭottara-śata-nāma and the popular deity mapping (Rahu→Durga, Ketu→Ganesha, Saturn→Hanuman, Mercury→Vishnu) are modern convention; ratified OS-2026-10-05-CITATIONS

### `ketu_matrix_vrata` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (navagraha vrata)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `ketu_matrix_yantra` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (navagraha yantra)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — BPHS Ch.84 §5 — bphs:PG996:C1 — "sketches of all the above planets should be drawn in the colours belonging to them on a piece of cloth ... placed in their own directions" — classical analogue, not this bīja-yantra's source; Yantra Maharnava (sibling citation) not in library

### `mars_matrix_behavioral` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (karaka conduct)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.85
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS (project doctrine: behavioural alignment as the deepest remedy)

### `mars_matrix_homa` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28
- `classical_ref`
  - before: classical tradition (graha-shanti homa)
  - after: BPHS Ch.84 §21-22 — bphs:PG999:C1
- `prescription_text`
  - before: Perform a Hanuman/Kartikeya / Mars graha-shanti homa (fire ritual) with the prescribed samidha (fire-wood) on Tuesday. 1008 ahutis is the standard count for a full dasha-shanti.
  - after: Graha-śānti homa for Mars with its samidhā khadira (Khair) (BPHS Ch.84 §21-22), offered with honey, ghee, curd or milk; 108 (or 28) āhutis per the text. [Modern practice, labelled: larger counts such as 1008; weekday Tuesday.]
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 §21-22 — bphs:PG999:C1 — "Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28"

### `mars_matrix_japa` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000
- `classical_ref`
  - before: classical tradition (dasha-japa counts)
  - after: BPHS Ch.84 §17-20 (Santhanam) — bphs:PG998:C1
- `prescription_text`
  - before: Complete the Mars mantra japa to its mahadasha count over the dasha period: recite 'Om Kraam Kreem Kraum Sah Bhaumaya Namah' on Tuesdays and daily. Standard counts: Sun 7,000; Moon 11,000; Mars 10,000; Mercury 9,000; Jupiter 19,000; Venus 16,000; Saturn 23,000; Rahu 18,000; Ketu 17,000.
  - after: Japa of the Mars mantra to the count of 10,000 (BPHS Ch.84 §17-20, which pairs the counts with the Vedic graha-mantras; count under verification: corpus scan reads "I 1000" (10,000 or 11,000); row keeps 10,000 until the page image is checked). The bīja mantra carried here is the tantric navagraha bīja (Mantra Mahodadhi — not in our library; labelled K1_UNVERIFIED). Weekday is modern convention.
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 (Remedial measures) §17-20 — bphs:PG998:C1 — "mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000" ; K1_UNVERIFIED — the bīja mantra string (Oṃ … Saḥ … Namaḥ) is the tantric navagraha bīja: Mantra Mahodadhi claimed, not in our library (BPHS pairs the counts with the Vedic graha-mantras)

### `mars_matrix_puja` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `deity`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins
- `classical_ref`
  - before: classical tradition (graha-shanti puja)
  - after: BPHS Ch.84 §15-16 — bphs:PG998:C1
- `deity`
  - before: Hanuman/Kartikeya
  - after: Mars (BPHS Ch.84 §6-13 dhyāna form)
- `prescription_text`
  - before: Worship Hanuman/Kartikeya on Tuesday with prescribed flowers, incense and lamp (graha-shanti puja for Mars). Chant the Mars Ashtottara (108 names) during the puja.
  - after: Graha-śānti pūjā of Mars per BPHS Ch.84 §15-16: offer flowers and garments of the planet's colour, sandal, lamp (dīpa), guggula incense, its metal and its grain, then give these to Brahmins; feed Brahmins the planet's food (§23-24). [Modern additions, labelled: weekday Tuesday; Aṣṭottara-śata-nāma; popular deity association as currently in the deity field.]
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 §15-16 — bphs:PG998:C1 — "Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins" ; K1 — BPHS Ch.84 §3-13 — bphs:PG995:C1–PG997:C1 — idols/metals and dhyāna forms of the nine grahas ; K2 — weekday, Aṣṭottara-śata-nāma and the popular deity mapping (Rahu→Durga, Ketu→Ganesha, Saturn→Hanuman, Mercury→Vishnu) are modern convention; ratified OS-2026-10-05-CITATIONS

### `mars_matrix_vrata` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (navagraha vrata)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `mars_matrix_yantra` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (navagraha yantra)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — BPHS Ch.84 §5 — bphs:PG996:C1 — "sketches of all the above planets should be drawn in the colours belonging to them on a piece of cloth ... placed in their own directions" — classical analogue, not this bīja-yantra's source; Yantra Maharnava (sibling citation) not in library

### `mercury_matrix_behavioral` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (karaka conduct)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.85
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS (project doctrine: behavioural alignment as the deepest remedy)

### `mercury_matrix_homa` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28
- `classical_ref`
  - before: classical tradition (graha-shanti homa)
  - after: BPHS Ch.84 §21-22 — bphs:PG999:C1
- `prescription_text`
  - before: Perform a Vishnu/Budha / Mercury graha-shanti homa (fire ritual) with the prescribed samidha (fire-wood) on Wednesday. 1008 ahutis is the standard count for a full dasha-shanti.
  - after: Graha-śānti homa for Mercury with its samidhā apāmārga (Chirchiri) (BPHS Ch.84 §21-22), offered with honey, ghee, curd or milk; 108 (or 28) āhutis per the text. [Modern practice, labelled: larger counts such as 1008; weekday Wednesday.]
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 §21-22 — bphs:PG999:C1 — "Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28"

### `mercury_matrix_japa` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000
- `classical_ref`
  - before: classical tradition (dasha-japa counts)
  - after: BPHS Ch.84 §17-20 (Santhanam) — bphs:PG998:C1
- `prescription_text`
  - before: Complete the Mercury mantra japa to its mahadasha count over the dasha period: recite 'Om Braam Breem Braum Sah Budhaya Namah' on Wednesdays and daily. Standard counts: Sun 7,000; Moon 11,000; Mars 10,000; Mercury 9,000; Jupiter 19,000; Venus 16,000; Saturn 23,000; Rahu 18,000; Ketu 17,000.
  - after: Japa of the Mercury mantra to the BPHS count of 9,000 (BPHS Ch.84 §17-20, which pairs the counts with the Vedic graha-mantras). The bīja mantra carried here is the tantric navagraha bīja (Mantra Mahodadhi — not in our library; labelled K1_UNVERIFIED). Weekday is modern convention.
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 (Remedial measures) §17-20 — bphs:PG998:C1 — "mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000" ; K1_UNVERIFIED — the bīja mantra string (Oṃ … Saḥ … Namaḥ) is the tantric navagraha bīja: Mantra Mahodadhi claimed, not in our library (BPHS pairs the counts with the Vedic graha-mantras)

### `mercury_matrix_puja` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `deity`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins
- `classical_ref`
  - before: classical tradition (graha-shanti puja)
  - after: BPHS Ch.84 §15-16 — bphs:PG998:C1
- `deity`
  - before: Vishnu/Budha
  - after: Mercury (BPHS Ch.84 §6-13 dhyāna form)
- `prescription_text`
  - before: Worship Vishnu/Budha on Wednesday with prescribed flowers, incense and lamp (graha-shanti puja for Mercury). Chant the Mercury Ashtottara (108 names) during the puja.
  - after: Graha-śānti pūjā of Mercury per BPHS Ch.84 §15-16: offer flowers and garments of the planet's colour, sandal, lamp (dīpa), guggula incense, its metal and its grain, then give these to Brahmins; feed Brahmins the planet's food (§23-24). [Modern additions, labelled: weekday Wednesday; Aṣṭottara-śata-nāma; popular deity association as currently in the deity field.]
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 §15-16 — bphs:PG998:C1 — "Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins" ; K1 — BPHS Ch.84 §3-13 — bphs:PG995:C1–PG997:C1 — idols/metals and dhyāna forms of the nine grahas ; K2 — weekday, Aṣṭottara-śata-nāma and the popular deity mapping (Rahu→Durga, Ketu→Ganesha, Saturn→Hanuman, Mercury→Vishnu) are modern convention; ratified OS-2026-10-05-CITATIONS

### `mercury_matrix_vrata` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (navagraha vrata)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `mercury_matrix_yantra` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (navagraha yantra)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — BPHS Ch.84 §5 — bphs:PG996:C1 — "sketches of all the above planets should be drawn in the colours belonging to them on a piece of cloth ... placed in their own directions" — classical analogue, not this bīja-yantra's source; Yantra Maharnava (sibling citation) not in library

### `moon_matrix_behavioral` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (karaka conduct)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.85
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS (project doctrine: behavioural alignment as the deepest remedy)

### `moon_matrix_homa` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28
- `classical_ref`
  - before: classical tradition (graha-shanti homa)
  - after: BPHS Ch.84 §21-22 — bphs:PG999:C1
- `prescription_text`
  - before: Perform a Chandra / Moon graha-shanti homa (fire ritual) with the prescribed samidha (fire-wood) on Monday. 1008 ahutis is the standard count for a full dasha-shanti.
  - after: Graha-śānti homa for Moon with its samidhā palāśa (BPHS Ch.84 §21-22), offered with honey, ghee, curd or milk; 108 (or 28) āhutis per the text. [Modern practice, labelled: larger counts such as 1008; weekday Monday.]
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 §21-22 — bphs:PG999:C1 — "Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28"

### `moon_matrix_japa` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000
- `classical_ref`
  - before: classical tradition (dasha-japa counts)
  - after: BPHS Ch.84 §17-20 (Santhanam) — bphs:PG998:C1
- `prescription_text`
  - before: Complete the Moon mantra japa to its mahadasha count over the dasha period: recite 'Om Shraam Shreem Shraum Sah Chandraya Namah' on Mondays and daily. Standard counts: Sun 7,000; Moon 11,000; Mars 10,000; Mercury 9,000; Jupiter 19,000; Venus 16,000; Saturn 23,000; Rahu 18,000; Ketu 17,000.
  - after: Japa of the Moon mantra to the BPHS count of 11,000 (BPHS Ch.84 §17-20, which pairs the counts with the Vedic graha-mantras). The bīja mantra carried here is the tantric navagraha bīja (Mantra Mahodadhi — not in our library; labelled K1_UNVERIFIED). Weekday is modern convention.
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 (Remedial measures) §17-20 — bphs:PG998:C1 — "mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000" ; K1_UNVERIFIED — the bīja mantra string (Oṃ … Saḥ … Namaḥ) is the tantric navagraha bīja: Mantra Mahodadhi claimed, not in our library (BPHS pairs the counts with the Vedic graha-mantras)

### `moon_matrix_puja` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `deity`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins
- `classical_ref`
  - before: classical tradition (graha-shanti puja)
  - after: BPHS Ch.84 §15-16 — bphs:PG998:C1
- `deity`
  - before: Chandra
  - after: Moon (BPHS Ch.84 §6-13 dhyāna form)
- `prescription_text`
  - before: Worship Chandra on Monday with prescribed flowers, incense and lamp (graha-shanti puja for Moon). Chant the Moon Ashtottara (108 names) during the puja.
  - after: Graha-śānti pūjā of Moon per BPHS Ch.84 §15-16: offer flowers and garments of the planet's colour, sandal, lamp (dīpa), guggula incense, its metal and its grain, then give these to Brahmins; feed Brahmins the planet's food (§23-24). [Modern additions, labelled: weekday Monday; Aṣṭottara-śata-nāma; popular deity association as currently in the deity field.]
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 §15-16 — bphs:PG998:C1 — "Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins" ; K1 — BPHS Ch.84 §3-13 — bphs:PG995:C1–PG997:C1 — idols/metals and dhyāna forms of the nine grahas ; K2 — weekday, Aṣṭottara-śata-nāma and the popular deity mapping (Rahu→Durga, Ketu→Ganesha, Saturn→Hanuman, Mercury→Vishnu) are modern convention; ratified OS-2026-10-05-CITATIONS

### `moon_matrix_vrata` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (navagraha vrata)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `moon_matrix_yantra` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (navagraha yantra)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — BPHS Ch.84 §5 — bphs:PG996:C1 — "sketches of all the above planets should be drawn in the colours belonging to them on a piece of cloth ... placed in their own directions" — classical analogue, not this bīja-yantra's source; Yantra Maharnava (sibling citation) not in library

### `rahu_matrix_behavioral` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (karaka conduct)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.85
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS (project doctrine: behavioural alignment as the deepest remedy)

### `rahu_matrix_homa` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28
- `classical_ref`
  - before: classical tradition (graha-shanti homa)
  - after: BPHS Ch.84 §21-22 — bphs:PG999:C1
- `prescription_text`
  - before: Perform a Durga / Rahu graha-shanti homa (fire ritual) with the prescribed samidha (fire-wood) on Saturday. 1008 ahutis is the standard count for a full dasha-shanti.
  - after: Graha-śānti homa for Rahu with its samidhā dūrvā (Doob) (BPHS Ch.84 §21-22), offered with honey, ghee, curd or milk; 108 (or 28) āhutis per the text. [Modern practice, labelled: larger counts such as 1008; weekday Saturday.]
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 §21-22 — bphs:PG999:C1 — "Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28"

### `rahu_matrix_japa` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000
- `classical_ref`
  - before: classical tradition (dasha-japa counts)
  - after: BPHS Ch.84 §17-20 (Santhanam) — bphs:PG998:C1
- `prescription_text`
  - before: Complete the Rahu mantra japa to its mahadasha count over the dasha period: recite 'Om Bhraam Bhreem Bhraum Sah Rahave Namah' on Saturdays and daily. Standard counts: Sun 7,000; Moon 11,000; Mars 10,000; Mercury 9,000; Jupiter 19,000; Venus 16,000; Saturn 23,000; Rahu 18,000; Ketu 17,000.
  - after: Japa of the Rahu mantra to the BPHS count of 18,000 (BPHS Ch.84 §17-20, which pairs the counts with the Vedic graha-mantras). The bīja mantra carried here is the tantric navagraha bīja (Mantra Mahodadhi — not in our library; labelled K1_UNVERIFIED). Weekday is modern convention.
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 (Remedial measures) §17-20 — bphs:PG998:C1 — "mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000" ; K1_UNVERIFIED — the bīja mantra string (Oṃ … Saḥ … Namaḥ) is the tantric navagraha bīja: Mantra Mahodadhi claimed, not in our library (BPHS pairs the counts with the Vedic graha-mantras)

### `rahu_matrix_puja` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `deity`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins
- `classical_ref`
  - before: classical tradition (graha-shanti puja)
  - after: BPHS Ch.84 §15-16 — bphs:PG998:C1
- `deity`
  - before: Durga
  - after: Rahu (BPHS Ch.84 §6-13 dhyāna form)
- `prescription_text`
  - before: Worship Durga on Saturday with prescribed flowers, incense and lamp (graha-shanti puja for Rahu). Chant the Rahu Ashtottara (108 names) during the puja.
  - after: Graha-śānti pūjā of Rahu per BPHS Ch.84 §15-16: offer flowers and garments of the planet's colour, sandal, lamp (dīpa), guggula incense, its metal and its grain, then give these to Brahmins; feed Brahmins the planet's food (§23-24). [Modern additions, labelled: weekday Saturday; Aṣṭottara-śata-nāma; popular deity association as currently in the deity field.]
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 §15-16 — bphs:PG998:C1 — "Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins" ; K1 — BPHS Ch.84 §3-13 — bphs:PG995:C1–PG997:C1 — idols/metals and dhyāna forms of the nine grahas ; K2 — weekday, Aṣṭottara-śata-nāma and the popular deity mapping (Rahu→Durga, Ketu→Ganesha, Saturn→Hanuman, Mercury→Vishnu) are modern convention; ratified OS-2026-10-05-CITATIONS

### `rahu_matrix_vrata` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (navagraha vrata)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `rahu_matrix_yantra` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (navagraha yantra)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — BPHS Ch.84 §5 — bphs:PG996:C1 — "sketches of all the above planets should be drawn in the colours belonging to them on a piece of cloth ... placed in their own directions" — classical analogue, not this bīja-yantra's source; Yantra Maharnava (sibling citation) not in library

### `saturn_matrix_behavioral` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (karaka conduct)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.85
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS (project doctrine: behavioural alignment as the deepest remedy)

### `saturn_matrix_homa` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28
- `classical_ref`
  - before: classical tradition (graha-shanti homa)
  - after: BPHS Ch.84 §21-22 — bphs:PG999:C1
- `prescription_text`
  - before: Perform a Shani/Hanuman / Saturn graha-shanti homa (fire ritual) with the prescribed samidha (fire-wood) on Saturday. 1008 ahutis is the standard count for a full dasha-shanti.
  - after: Graha-śānti homa for Saturn with its samidhā śamī (BPHS Ch.84 §21-22), offered with honey, ghee, curd or milk; 108 (or 28) āhutis per the text. [Modern practice, labelled: larger counts such as 1008; weekday Saturday.]
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 §21-22 — bphs:PG999:C1 — "Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28"

### `saturn_matrix_japa` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000
- `classical_ref`
  - before: classical tradition (dasha-japa counts)
  - after: BPHS Ch.84 §17-20 (Santhanam) — bphs:PG998:C1
- `prescription_text`
  - before: Complete the Saturn mantra japa to its mahadasha count over the dasha period: recite 'Om Praam Preem Praum Sah Shanaischaraya Namah' on Saturdays and daily. Standard counts: Sun 7,000; Moon 11,000; Mars 10,000; Mercury 9,000; Jupiter 19,000; Venus 16,000; Saturn 23,000; Rahu 18,000; Ketu 17,000.
  - after: Japa of the Saturn mantra to the BPHS count of 23,000 (BPHS Ch.84 §17-20, which pairs the counts with the Vedic graha-mantras). The bīja mantra carried here is the tantric navagraha bīja (Mantra Mahodadhi — not in our library; labelled K1_UNVERIFIED). Weekday is modern convention.
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 (Remedial measures) §17-20 — bphs:PG998:C1 — "mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000" ; K1_UNVERIFIED — the bīja mantra string (Oṃ … Saḥ … Namaḥ) is the tantric navagraha bīja: Mantra Mahodadhi claimed, not in our library (BPHS pairs the counts with the Vedic graha-mantras)

### `saturn_matrix_puja` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `deity`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins
- `classical_ref`
  - before: classical tradition (graha-shanti puja)
  - after: BPHS Ch.84 §15-16 — bphs:PG998:C1
- `deity`
  - before: Shani/Hanuman
  - after: Saturn (BPHS Ch.84 §6-13 dhyāna form)
- `prescription_text`
  - before: Worship Shani/Hanuman on Saturday with prescribed flowers, incense and lamp (graha-shanti puja for Saturn). Chant the Saturn Ashtottara (108 names) during the puja.
  - after: Graha-śānti pūjā of Saturn per BPHS Ch.84 §15-16: offer flowers and garments of the planet's colour, sandal, lamp (dīpa), guggula incense, its metal and its grain, then give these to Brahmins; feed Brahmins the planet's food (§23-24). [Modern additions, labelled: weekday Saturday; Aṣṭottara-śata-nāma; popular deity association as currently in the deity field.]
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 §15-16 — bphs:PG998:C1 — "Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins" ; K1 — BPHS Ch.84 §3-13 — bphs:PG995:C1–PG997:C1 — idols/metals and dhyāna forms of the nine grahas ; K2 — weekday, Aṣṭottara-śata-nāma and the popular deity mapping (Rahu→Durga, Ketu→Ganesha, Saturn→Hanuman, Mercury→Vishnu) are modern convention; ratified OS-2026-10-05-CITATIONS

### `saturn_matrix_vrata` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (navagraha vrata)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `saturn_matrix_yantra` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (navagraha yantra)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — BPHS Ch.84 §5 — bphs:PG996:C1 — "sketches of all the above planets should be drawn in the colours belonging to them on a piece of cloth ... placed in their own directions" — classical analogue, not this bīja-yantra's source; Yantra Maharnava (sibling citation) not in library

### `stotra_saraswati_mercury_education` — CONTENT_FIX+K2
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (Mercury-Saraswati upaya); Deva Keralam
  - after: modern devotional practice (Sarasvatī for Budha)
- `confidence`
  - before: 0.83
  - after: 0.6
- `source_canonical_id`
  - before: classical_tradition
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `sun_matrix_behavioral` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (karaka conduct)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.85
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS (project doctrine: behavioural alignment as the deepest remedy)

### `sun_matrix_homa` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28
- `classical_ref`
  - before: classical tradition (graha-shanti homa)
  - after: BPHS Ch.84 §21-22 — bphs:PG999:C1
- `prescription_text`
  - before: Perform a Surya / Sun graha-shanti homa (fire ritual) with the prescribed samidha (fire-wood) on Sunday. 1008 ahutis is the standard count for a full dasha-shanti.
  - after: Graha-śānti homa for Sun with its samidhā arka (Aak) (BPHS Ch.84 §21-22), offered with honey, ghee, curd or milk; 108 (or 28) āhutis per the text. [Modern practice, labelled: larger counts such as 1008; weekday Sunday.]
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 §21-22 — bphs:PG999:C1 — "Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28"

### `sun_matrix_japa` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000
- `classical_ref`
  - before: classical tradition (dasha-japa counts)
  - after: BPHS Ch.84 §17-20 (Santhanam) — bphs:PG998:C1
- `prescription_text`
  - before: Complete the Sun mantra japa to its mahadasha count over the dasha period: recite 'Om Hraam Hreem Hraum Sah Suryaya Namah' on Sundays and daily. Standard counts: Sun 7,000; Moon 11,000; Mars 10,000; Mercury 9,000; Jupiter 19,000; Venus 16,000; Saturn 23,000; Rahu 18,000; Ketu 17,000.
  - after: Japa of the Sun mantra to the BPHS count of 7,000 (BPHS Ch.84 §17-20, which pairs the counts with the Vedic graha-mantras). The bīja mantra carried here is the tantric navagraha bīja (Mantra Mahodadhi — not in our library; labelled K1_UNVERIFIED). Weekday is modern convention.
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 (Remedial measures) §17-20 — bphs:PG998:C1 — "mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000" ; K1_UNVERIFIED — the bīja mantra string (Oṃ … Saḥ … Namaḥ) is the tantric navagraha bīja: Mantra Mahodadhi claimed, not in our library (BPHS pairs the counts with the Vedic graha-mantras)

### `sun_matrix_puja` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `deity`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins
- `classical_ref`
  - before: classical tradition (graha-shanti puja)
  - after: BPHS Ch.84 §15-16 — bphs:PG998:C1
- `deity`
  - before: Surya
  - after: Sun (BPHS Ch.84 §6-13 dhyāna form)
- `prescription_text`
  - before: Worship Surya on Sunday with prescribed flowers, incense and lamp (graha-shanti puja for Sun). Chant the Sun Ashtottara (108 names) during the puja.
  - after: Graha-śānti pūjā of Sun per BPHS Ch.84 §15-16: offer flowers and garments of the planet's colour, sandal, lamp (dīpa), guggula incense, its metal and its grain, then give these to Brahmins; feed Brahmins the planet's food (§23-24). [Modern additions, labelled: weekday Sunday; Aṣṭottara-śata-nāma; popular deity association as currently in the deity field.]
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 §15-16 — bphs:PG998:C1 — "Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins" ; K1 — BPHS Ch.84 §3-13 — bphs:PG995:C1–PG997:C1 — idols/metals and dhyāna forms of the nine grahas ; K2 — weekday, Aṣṭottara-śata-nāma and the popular deity mapping (Rahu→Durga, Ketu→Ganesha, Saturn→Hanuman, Mercury→Vishnu) are modern convention; ratified OS-2026-10-05-CITATIONS

### `sun_matrix_vrata` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (navagraha vrata)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `sun_matrix_yantra` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (navagraha yantra)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — BPHS Ch.84 §5 — bphs:PG996:C1 — "sketches of all the above planets should be drawn in the colours belonging to them on a piece of cloth ... placed in their own directions" — classical analogue, not this bīja-yantra's source; Yantra Maharnava (sibling citation) not in library

### `venus_matrix_behavioral` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (karaka conduct)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.85
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS (project doctrine: behavioural alignment as the deepest remedy)

### `venus_matrix_homa` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28
- `classical_ref`
  - before: classical tradition (graha-shanti homa)
  - after: BPHS Ch.84 §21-22 — bphs:PG999:C1
- `prescription_text`
  - before: Perform a Lakshmi/Shukra / Venus graha-shanti homa (fire ritual) with the prescribed samidha (fire-wood) on Friday. 1008 ahutis is the standard count for a full dasha-shanti.
  - after: Graha-śānti homa for Venus with its samidhā udumbara (Goolar) (BPHS Ch.84 §21-22), offered with honey, ghee, curd or milk; 108 (or 28) āhutis per the text. [Modern practice, labelled: larger counts such as 1008; weekday Friday.]
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 §21-22 — bphs:PG999:C1 — "Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28"

### `venus_matrix_japa` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000
- `classical_ref`
  - before: classical tradition (dasha-japa counts)
  - after: BPHS Ch.84 §17-20 (Santhanam) — bphs:PG998:C1
- `prescription_text`
  - before: Complete the Venus mantra japa to its mahadasha count over the dasha period: recite 'Om Draam Dreem Draum Sah Shukraya Namah' on Fridays and daily. Standard counts: Sun 7,000; Moon 11,000; Mars 10,000; Mercury 9,000; Jupiter 19,000; Venus 16,000; Saturn 23,000; Rahu 18,000; Ketu 17,000.
  - after: Japa of the Venus mantra to the BPHS count of 16,000 (BPHS Ch.84 §17-20, which pairs the counts with the Vedic graha-mantras). The bīja mantra carried here is the tantric navagraha bīja (Mantra Mahodadhi — not in our library; labelled K1_UNVERIFIED). Weekday is modern convention.
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 (Remedial measures) §17-20 — bphs:PG998:C1 — "mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000" ; K1_UNVERIFIED — the bīja mantra string (Oṃ … Saḥ … Namaḥ) is the tantric navagraha bīja: Mantra Mahodadhi claimed, not in our library (BPHS pairs the counts with the Vedic graha-mantras)

### `venus_matrix_puja` — CONTENT_FIX+K1
fields changed: `classical_attestation_text`, `classical_ref`, `deity`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_attestation_text`
  - before: null
  - after: Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins
- `classical_ref`
  - before: classical tradition (graha-shanti puja)
  - after: BPHS Ch.84 §15-16 — bphs:PG998:C1
- `deity`
  - before: Lakshmi/Shukra
  - after: Venus (BPHS Ch.84 §6-13 dhyāna form)
- `prescription_text`
  - before: Worship Lakshmi/Shukra on Friday with prescribed flowers, incense and lamp (graha-shanti puja for Venus). Chant the Venus Ashtottara (108 names) during the puja.
  - after: Graha-śānti pūjā of Venus per BPHS Ch.84 §15-16: offer flowers and garments of the planet's colour, sandal, lamp (dīpa), guggula incense, its metal and its grain, then give these to Brahmins; feed Brahmins the planet's food (§23-24). [Modern additions, labelled: weekday Friday; Aṣṭottara-śata-nāma; popular deity association as currently in the deity field.]
- `source_canonical_id`
  - before: BPHS
  - after: bphs
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.84 §15-16 — bphs:PG998:C1 — "Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins" ; K1 — BPHS Ch.84 §3-13 — bphs:PG995:C1–PG997:C1 — idols/metals and dhyāna forms of the nine grahas ; K2 — weekday, Aṣṭottara-śata-nāma and the popular deity mapping (Rahu→Durga, Ketu→Ganesha, Saturn→Hanuman, Mercury→Vishnu) are modern convention; ratified OS-2026-10-05-CITATIONS

### `venus_matrix_vrata` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (navagraha vrata)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `venus_matrix_yantra` — LABEL_K2_MODERN
fields changed: `classical_ref`, `confidence`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (navagraha yantra)
  - after: modern practice / project judgment — OS-2026-10-05-CITATIONS
- `confidence`
  - before: 0.8
  - after: 0.6
- `source_canonical_id`
  - before: BPHS
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — BPHS Ch.84 §5 — bphs:PG996:C1 — "sketches of all the above planets should be drawn in the colours belonging to them on a piece of cloth ... placed in their own directions" — classical analogue, not this bīja-yantra's source; Yantra Maharnava (sibling citation) not in library

### `yantra_kala_sarpa_shanti` — CONTENT_FIX+K2
fields changed: `classical_ref`, `confidence`, `prescription_text`, `source_canonical_id`, `source_citation`

- `classical_ref`
  - before: classical tradition (Kala Sarpa Shanti yantra; Trimbakeshwar)
  - after: modern Kala Sarpa Shanti yantra practice
- `confidence`
  - before: 0.75
  - after: 0.6
- `prescription_text`
  - before: Kala Sarpa Dosha Yantra: a specific yantra prescribed for Kala Sarpa Dosha remediation, combining Rahu and Ketu yantras with a serpent (Naga) motif encircling all the planets. Classically installed at a Shiva temple (Trimbakeshwar is the canonical site per tradition) during a special Kala Sarpa Shanti puja. The yantra is then worn or installed at home. Source: classical tradition for Kala Sarpa Shanti puja.
  - after: Kala Sarpa Dosha Yantra: a specific yantra prescribed for Kala Sarpa Dosha remediation, combining Rahu and Ketu yantras with a serpent (Naga) motif encircling all the planets. Customarily installed at a Shiva temple (Trimbakeshwar is the popular site — modern practice) during a special Kala Sarpa Shanti puja. The yantra is then worn or installed at home.
- `source_canonical_id`
  - before: classical_tradition
  - after: k2:OS-2026-10-05-CITATIONS
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS


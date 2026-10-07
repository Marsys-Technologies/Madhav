# Row diff — bg_doshas catalog projection (brahma_dosha_catalog), citation pass 2

> **APPLY ORDER (SS 2026-10-05).** (1) rebuild bg_doshas (accept bg_yogas, bg_dasha_systems and bg_ontology showing stale: the shared grp_brahma_ontology fingerprint moves); (2) bg_ontology in the DEFAULT mode (no expected-change file);
> (3) ga_structural in the L1 refresh pass BEFORE the L2 refresh, so no dosha_label fact points at a removed catalog id when L2 reads it.
>
> **bg_parihara_rules (SS decision 2026-10-05, no reseal).** Its `_DOSHA_QUERY` keeps doshas whose `classical_citations` hold a real `text_id`. The K1 source verified for 14 doshas covers the dosha's DEFINITION, not its cancellation
> conditions, so those 14 are DECLARED out of the graph (`PARIHARA_K1_SOURCE_CHECK_PENDING`: abhukta_mula_dosha, bhakoot_dosha, daridra, dhaiya, gana_dosha, graha_maitri_dosha, mool_dosha, mrityu_bhaga_dosha, nadi_dosha, sade_sati,
> tara_dosha_compat, varna_dosha, vashya_dosha, yoni_dosha) and K1_ANALOGUE objects never qualify: the parihara row set stays the identical 60 rows (migration 703's pin untouched). The 27 would-be rows are in ACHARYA/PARIHARA_27_PENDING.tsv.
>
> **Dropped in the merge:** vish_dosha's two bhanga conditions ('benefic aspect', 'Moon strong in own/exalt') are not carried into punarphoo (the TSV is silent): listed in CITATION_AMBIGUOUS.md.


Decision OS-2026-10-05-CITATIONS (PASS2_DECISIONS.tsv, 53 brahma_dosha_catalog rows): 13 REMOVE, 7 APPLY_K1, 7 CONTENT_FIX+K1, 3 CONTENT_FIX+K2, 8 KEEP_UNVERIFIED_LABELLED, 15 LABEL_K2_MODERN. The 26 other dosha rows are identical before and after.

Table `brahma_dosha_catalog`, natural key `canonical_id`. Before = the writer replayed from origin/main; after = the writer replayed from this branch (both on a disposable local PostgreSQL, no production access).

| | rows |
|---|---|
| before | 79 |
| after | 66 |
| removed | 14 |
| added | 1 |
| changed (same key) | 39 |
| unchanged | 26 |

The one rename (kemadruma_compat_kuja -> kuja_dosha_from_venus) changes the natural key, so it is listed under Removed and under Added.

## Removed (14)

- `kala_sarpa_anant` — REMOVE
- `kala_sarpa_ghatak` — REMOVE
- `kala_sarpa_karkotak` — REMOVE
- `kala_sarpa_kulik` — REMOVE
- `kala_sarpa_mahapadma` — REMOVE
- `kala_sarpa_padma` — REMOVE
- `kala_sarpa_shankhachud` — REMOVE
- `kala_sarpa_shankhpal` — REMOVE
- `kala_sarpa_sheshnag` — REMOVE
- `kala_sarpa_takshak` — REMOVE
- `kala_sarpa_vasuki` — REMOVE
- `kala_sarpa_vishdhar` — REMOVE
- `kemadruma_compat_kuja` — KEEP_UNVERIFIED_LABELLED + RENAME to kuja_dosha_from_venus (removed + added: the natural key changes)
- `vish_dosha` — REMOVE

## Added (1)

- `kuja_dosha_from_venus` — RENAME of kemadruma_compat_kuja (K1_UNVERIFIED; name_sa Śukrāt Kuja-doṣa)

## Changed (39)

### `abhukta_mula_dosha` — CONTENT_FIX+K1
fields changed: `cancellation_conditions`, `classical_citations`, `effects_text`, `formation_rule_jsonb`, `formation_text`

- `cancellation_conditions`
  - before: {"mitigation": ["prescribed shanti"]}
  - after: {"mitigation": ["śānti after the 12th day (BPHS Ch.93 §3-4)"]}
- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1", "locus": "PG1021:C1", "excerpt": "ruling deity of Jyestha is Indra and ... of Moola is Rakshasa ... this gandanta is considered as the most evil ... father should not see the face of the child for 8 years", "text_id": "bphs", "human_locus": "Ch.93 (Abhukta Moola) §1-2"}, {"kind": "K1", "locus": "PG1019:C1", "excerpt": "the last 6 ghatikas of Jyestha and first 8 ghatikas of Moola are known as Abhukta Moola", "text_id": "bphs", "human_locus": "Ch.92 §5"}, {"kind": "K1", "locus": "PG53:C1", "excerpt": "first eight ghaṭīs of Mūla and the last five nāḍīs of Jyeṣṭhā ... abandon the child; or else the father should not look upon its face for eight years", "text_id": "muhurta_chintamani", "human_locus": "Nakṣatra-prakaraṇa v.54"}, {"kind": "K2", "note": "name is modern", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]
- `effects_text`
  - before: Considered especially inauspicious for the child/family per tradition; specific shanti prescribed.
  - after: Most evil of the gaṇḍāntas (Indra/Rākṣasa enmity): the child to be given away, or the father not to see its face for 8 years until śānti (BPHS Ch.93 §1-2; MC v.54)
- `formation_rule_jsonb`
  - before: {"requires": "birth in the specific junction ghatis of Jyeshtha-end / Mula-start"}
  - after: {"note": "two classical values for the Jyeṣṭhā side; MC ṭīkā records other opinions", "window": {"mula_first_ghatis": 8, "jyeshtha_last_ghatis": {"bphs_ch92_s5": 6, "mc_v54_narada": 5}}}
- `formation_text`
  - before: Birth in the abhukta-mula window — the last ghatis of Jyeshtha into the first of Mula.
  - after: Birth in the abhukta-mūla window: the last 6 (BPHS Ch.92 §5) or 5 (MC v.54, Nārada) ghaṭīs of Jyeṣṭhā and the first 8 ghaṭīs of Mūla

### `angarak` — LABEL_K2_MODERN
fields changed: `classical_citations`, `school`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K2", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]
- `school`
  - before: parashari
  - after: modern

### `bhakoot_dosha` — CONTENT_FIX+K1
fields changed: `cancellation_conditions`, `classical_citations`, `formation_rule_jsonb`, `severity_grades`

- `cancellation_conditions`
  - before: {"bhanga": ["same rashi lord", "lords are friends", "Nadi-koota satisfied"]}
  - after: {"note": "any one suffices; nāḍī-śuddhi must hold in every case (MC v.32 ṭīkā)", "bhanga": ["ekādhipatya (one lord for both signs)", "rāśi-lords mutually friendly, with nāḍī- and nakṣatra-śuddhi", "aṃśa-lords friendly and strong, with nāḍī- and tārā-śuddhi", "rāśi-vaśyatā", "tārā-śuddhi"]}
- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1", "locus": "PG95:C1–PG96:C1", "excerpt": "sixth from an odd sign ... eighth from an even sign ... śatru-ṣaḍaṣṭaka ... brings death ... 5–9 ... loss of sons; if 2–12, poverty ... mitra-ṣaḍaṣṭaka ... auspicious", "text_id": "muhurta_chintamani", "human_locus": "Vivāha-prakaraṇa vv.31-32"}, {"kind": "K1", "locus": "PG96:C1", "excerpt": "five parihāras: ekādhipatya, friendly rāśi-lords, friendly strong aṃśa-lords, rāśi-vaśyatā, tārā-śuddhi; \"nāḍī-śuddhi must be present in every case\"", "text_id": "muhurta_chintamani", "human_locus": "v.32 ṭīkā"}, {"kind": "K2", "note": "name is modern", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]
- `formation_rule_jsonb`
  - before: {"rashi_distance": ["6-8", "2-12", "5-9"]}
  - after: {"rashi_distance": {"5-9": "loss of sons", "6-8": {"mitra": "6th from an even sign or 8th from an odd sign — auspicious, no dosha", "shatru": "6th from the bride's ODD sign or 8th from her EVEN sign — inauspicious (death)"}, "2-12": "poverty"}}
- `severity_grades`
  - before: {"severe": "6/8", "moderate": "2/12 or 5/9"}
  - after: {"none": "mitra-ṣaḍaṣṭaka and all other distances", "severe": "śatru-ṣaḍaṣṭaka", "moderate": "5-9 (progeny) or 2-12 (poverty)"}

### `chandal_yoga_dosha` — LABEL_K2_MODERN
fields changed: `classical_citations`, `school`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K2", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]
- `school`
  - before: parashari
  - after: modern

### `chandra_grahan_dosha` — CONTENT_FIX+K2
fields changed: `classical_citations`, `formation_rule_jsonb`, `school`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K2", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}, {"kind": "K1_ANALOGUE", "note": "classical doṣa is birth DURING an eclipse; luminary-conjunct-node is a modern generalisation", "locus": "PG1016:C1", "excerpt": "a person whose birth takes place at the time of solar or lunar eclipse suffers from ailments, distress and poverty and faces danger of death", "text_id": "bphs", "relation": "classical analogue, not the source of this rule", "human_locus": "Ch.91 (Birth in Eclipses) §1-14"}]
- `formation_rule_jsonb`
  - before: {"or": {"conjunction": ["moon", "ketu"]}, "conjunction": ["moon", "rahu"]}
  - after: {"conjunction": [["moon", "rahu"], ["moon", "ketu"]]}
- `school`
  - before: parashari
  - after: modern

### `daridra` — CONTENT_FIX+K1
fields changed: `cancellation_conditions`, `classical_citations`, `formation_rule_jsonb`, `formation_text`, `severity_grades`

- `cancellation_conditions`
  - before: {"bhanga": ["dhana/raja yoga present", "11th lord retrograde-strong"]}
  - after: {"bhanga": ["dhana/raja yoga present (K2 project judgment; BPHS Ch.42 gives no cancellation on bphs:PG412)"]}
- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1", "locus": "PG412:C1", "excerpt": "penniless if the ascendant lord is in the 12th as the 12th lord is in the ascendant along with a Maraka lord ... ascendant lord in the 6th while the 6th lord is in the ascendant", "text_id": "bphs", "human_locus": "Ch.42 (Combinations for Poverty) §2-5"}, {"kind": "K2", "note": "name is modern", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]
- `formation_rule_jsonb`
  - before: {"requires": "11th lord in dusthana (6/8/12) or 2nd/11th lords afflicted"}
  - after: {"any_of": [{"lagna_lord_in_house": 12, "with_or_aspected_by": "maraka_lord", "house12_lord_in_house": 1}, {"lagna_lord_in_house": 6, "with_or_aspected_by": "maraka_lord", "house6_lord_in_house": 1}, {"lagna_or_moon_with": "ketu", "lagna_lord_in_house": 8}, {"house2_lord": "debilitated_or_in_enemy_sign", "lagna_lord_with_malefic_in_house": [6, 8, 12]}]}
- `formation_text`
  - before: Lord of gains (11th) in a dusthana, or wealth-house lords debilitated/combust.
  - after: BPHS Ch.42 poverty yogas (all lagna-lord-centred): L1 in 12 with L12 in lagna joined/aspected by a māraka lord; L1 in 6 with L6 in lagna joined/aspected by a māraka; lagna or Moon with Ketu while L1 is in 8; L1 with a malefic in 6/8/12 while L2 is debilitated or in an enemy sign
- `severity_grades`
  - before: {"severe": "multiple", "moderate": "one condition"}
  - after: {"severe": "any BPHS Ch.42 combination present (the text gives no gradation)"}

### `dhaiya` — APPLY_K1
fields changed: `classical_citations`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1", "locus": "PG330:C1", "excerpt": "in the 4th house, there will be loss of wife, relation and wealth ... In the 8th house, there will be loss in children, cattle, friends and wealth ... disease", "text_id": "phaladeepika", "human_locus": "Adh. XXVI śl.22"}, {"kind": "K2", "note": "the names \"Dhaiya / Panoti / Kantaka / Ashtama Shani\" and the 2.5-year framing are later usage", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]

### `gana_dosha` — CONTENT_FIX+K1
fields changed: `cancellation_conditions`, `classical_citations`, `formation_rule_jsonb`, `formation_text`, `severity_grades`

- `cancellation_conditions`
  - before: {"bhanga": ["same rashi/nakshatra lord", "Bhakoot satisfied"]}
  - after: {"bhanga": ["rāśi-lords mutually friendly (MC v.33)", "aṃśa-lords friendly (v.33)", "same nakṣatra, different pāda (v.37)"]}
- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1", "locus": "PG95:C1", "excerpt": "rākṣasa-gaṇa = Maghā, Āśleṣā, Dhaniṣṭhā, Jyeṣṭhā, Mūla, Śatabhiṣā, Kṛttikā, Citrā, Viśākhā; \"same gaṇa great love; deva–manuṣya middling; rākṣasa–manuṣya death; deva–rākṣasa quarrel\"", "text_id": "muhurta_chintamani", "human_locus": "Vivāha-prakaraṇa vv.29-30 (Hindi ṭīkā)"}, {"kind": "K1", "locus": "PG93:C1", "excerpt": "eight kūṭas carry guṇa 1,2,3,4,5,6,7,8 = 36 (gaṇa = 6)", "text_id": "muhurta_chintamani", "human_locus": "v.21 ṭīkā"}, {"kind": "K2", "note": "name is modern", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]
- `formation_rule_jsonb`
  - before: {"mismatch": "Deva vs Rakshasa gana of the two Moon-nakshatras"}
  - after: {"points": {"same_gana": 6, "deva_manushya": 5, "deva_or_manushya_with_rakshasa": 0}, "mismatch": "Deva vs Rakshasa gana of the two Moon-nakshatras"}
- `formation_text`
  - before: Nakshatra-gana mismatch (Deva/Manushya/Rakshasa) — worst when Deva-bride & Rakshasa-groom.
  - after: Gaṇa mismatch between the partners' janma-nakṣatra gaṇas (deva / manuṣya / rākṣasa). Same gaṇa best; deva–manuṣya middling; deva–rākṣasa quarrel; rākṣasa–manuṣya gravest ("death"), with the ṭīkā's asymmetry: groom manuṣya + bride rākṣasa → groom's death; groom rākṣasa + bride manuṣya → enmity
- `severity_grades`
  - before: {"mild": "Manushya-Deva", "severe": "Deva-Rakshasa"}
  - after: {"mild": "deva–manushya (middling affection)", "none": "same gana", "severe": "rakshasa–manushya (either direction; groom manushya + bride rakshasa gravest)", "moderate": "deva–rakshasa (quarrel)"}

### `graha_maitri_dosha` — APPLY_K1
fields changed: `classical_citations`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1", "locus": "PG94:C1", "excerpt": "friend/enemy/neutral table of the rāśi-lords; 5 guṇa for friends or one lord, down to 0 for mutual enemies (\"mṛtyu-ṣaḍaṣṭaka\")", "text_id": "muhurta_chintamani", "human_locus": "Vivāha-prakaraṇa vv.27-28 (ṭīkā)"}, {"kind": "K1", "locus": "PG96:C1", "excerpt": "friendship of the rāśi-lords destroys the ṣaḍaṣṭaka and the other doṣas", "text_id": "muhurta_chintamani", "human_locus": "vv.32-33"}, {"kind": "K2", "note": "name is modern", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]

### `grahan` — LABEL_K2_MODERN
fields changed: `classical_citations`, `school`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K2", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}, {"kind": "K1_ANALOGUE", "note": "classical doṣa is birth DURING an eclipse; luminary-conjunct-node is a modern generalisation", "locus": "PG1016:C1", "excerpt": "a person whose birth takes place at the time of solar or lunar eclipse suffers from ailments, distress and poverty and faces danger of death", "text_id": "bphs", "relation": "classical analogue, not the source of this rule", "human_locus": "Ch.91 (Birth in Eclipses) §1-14"}]
- `school`
  - before: parashari
  - after: modern

### `guru_chandal` — LABEL_K2_MODERN
fields changed: `classical_citations`, `school`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K2", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]
- `school`
  - before: parashari
  - after: modern

### `kala_amrita_dosha` — LABEL_K2_MODERN
fields changed: `classical_citations`, `school`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K2", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]
- `school`
  - before: parashari
  - after: modern

### `kala_sarpa` — CONTENT_FIX+K2
fields changed: `classical_citations`, `formation_rule_jsonb`, `school`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K2", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]
- `formation_rule_jsonb`
  - before: {"requires": "all 7 planets hemmed between Rahu and Ketu (one side of the nodal axis)"}
  - after: {"requires": "all 7 planets hemmed between Rahu and Ketu (one side of the nodal axis)", "variant_names_by_rahu_house": {"1": "Anant", "2": "Kulik", "3": "Vasuki", "4": "Shankhpal", "5": "Padma", "6": "Mahapadma", "7": "Takshak", "8": "Karkotak", "9": "Shankhachud", "10": "Ghatak", "11": "Vishdhar", "12": "Sheshnag"}}
- `school`
  - before: parashari
  - after: modern

### `kuja_dosha_from_moon` — KEEP_UNVERIFIED_LABELLED
fields changed: `classical_citations`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1_UNVERIFIED", "needs": "Vivāha-paṭala / Jātaka-tattva / Praśna-mārga — none in corpus; not in hora_sara, jataka_parijata or muhurta_chintamani (pass-1 search)", "claimed_text": "classical source claimed (Kuja-doṣa reckoned from Moon / Venus)"}, {"kind": "K2", "note": "name is modern", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]

### `lagna_lord_grahan_dosha` — LABEL_K2_MODERN
fields changed: `classical_citations`, `school`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K2", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]
- `school`
  - before: parashari
  - after: modern

### `mahendra_dosha` — KEEP_UNVERIFIED_LABELLED
fields changed: `classical_citations`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1_UNVERIFIED", "note": "MC Vivāha-prakaraṇa vv.21-38 (muhurta_chintamani:PG93–PG100) read in full in pass 2 and does not contain it", "needs": "a daśa-kūṭa text (Vivāha-paṭala / Kālaprakāśikā / Jyotirnibandha) — none in corpus", "claimed_text": "classical source claimed (daśa-kūṭa item)"}, {"kind": "K2", "note": "name is modern", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]

### `mool_dosha` — CONTENT_FIX+K1
fields changed: `cancellation_conditions`, `classical_citations`, `effects_text`, `formation_text`, `severity_grades`

- `cancellation_conditions`
  - before: {"mitigation": ["gandmool shanti performed", "benefic aspect on the Moon"]}
  - after: {"mitigation": ["śānti performed (go-dāna 3/2/1 cows by junction, cow with calf, Mṛtyuñjaya japa)", "benefic aspect on the Moon (K2)"]}
- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1", "locus": "PG632:C1", "excerpt": "Ganda at the conclusion of ... Revati, Aslesha or Jyeshta ... and at the commencement of ... Aswini, Magha or Moola", "text_id": "jataka_parijata", "human_locus": "śl.59"}, {"kind": "K1", "note": "remedy: cow with calf; father sees child after sūtaka", "locus": "PG1018:C1, bphs:PG1019:C1", "excerpt": "last two ghatikas of Revti and first two ghatikas of Aswini ... Ashlesha ... Makha ... Jyestha ... Moola ... Nakshatra Gandanta", "text_id": "bphs", "human_locus": "Ch.92 §3, §6-8"}, {"kind": "K1", "locus": "PG1026:C1", "excerpt": "3 cows ... in the case of Jyestha Moola and Ashlesha Makha gandantas, 2 cows in Revati-Ashwini gandantas and 1 cow in other gandantas", "text_id": "bphs", "human_locus": "Ch.94 §8-9"}, {"kind": "K1", "locus": "PG53:C1", "excerpt": "first pāda of Mūla the father ... second, the mother; third, wealth ... fourth auspicious ... In Āśleṣā the order is reversed", "text_id": "muhurta_chintamani", "human_locus": "Nakṣatra-prakaraṇa v.55"}, {"kind": "K2", "note": "name is modern", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]
- `effects_text`
  - before: Early-childhood vulnerability; tradition prescribes a 27th-day shanti.
  - after: Early-childhood vulnerability (gaṇḍānta birth); śānti after the sūtaka days / after the 12th day (BPHS Ch.92 §6-8, Ch.93 §3-4) — the "27th-day" timing is not in the texts
- `formation_text`
  - before: The natal Moon falls in one of the six gandmool nakshatras (ruled by Ketu/Mercury).
  - after: Natal Moon in a gaṇḍamūla nakṣatra (Aśvinī, Āśleṣā, Maghā, Jyeṣṭhā, Mūla, Revatī); the strict gaṇḍānta is the last/first 2 ghaṭikās at the Revatī–Aśvinī, Āśleṣā–Maghā, Jyeṣṭhā–Mūla junctions (BPHS Ch.92 §3; JP śl.59)
- `severity_grades`
  - before: {"mild": "middle padas", "severe": "junction padas (Jyeshtha-4 / Mula-1, Revati-4 / Ashwini-1, Ashlesha-4 / Magha-1)"}
  - after: {"mild": "middle padas (K2 project grading)", "severe": "junction padas (Jyeshtha-4 / Mula-1, Revati-4 / Ashwini-1, Ashlesha-4 / Magha-1) (K2 project grading)", "ashlesha": "reversed order", "mula_pada": {"1": "father", "2": "mother", "3": "wealth", "4": "auspicious after śānti"}}

### `mrityu_bhaga_dosha` — CONTENT_FIX+K1
fields changed: `classical_citations`, `formation_text`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1", "note": "(śl.11 gives an alternative set)", "locus": "PG169:C1", "excerpt": "degrees attained by the Moon in Mesha and the other signs be respectively 26, 12, 13, 25, 24, 11, 26, 14, 13, 25, 5 and 12, they indicate death", "text_id": "phaladeepika", "human_locus": "Adh. XIII śl.10"}, {"kind": "K1_UNVERIFIED", "claimed_text": "the per-planet/lagna mṛtyu-bhāga table used by L1: classical source claimed (Jātaka Pārijāta, which Phaladeepika cross-refers as \"जा.पा. p.38\")"}, {"kind": "K2", "note": "name is modern", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]
- `formation_text`
  - before: A planet or the lagna occupies its specific 'death-degree' (mrityu-bhaga) per the classical per-sign degree table.
  - after: The Moon at its mṛtyu-bhāga per Phaladeepika XIII.10 (26,12,13,25,24,11,26,14,13,25,5,12 from Meṣa; XIII.11 gives an alternative set). The per-planet and lagna degrees that L1 computes are carried under a separate label: classical source claimed (Jātaka Pārijāta), not verified in our library.

### `nadi_dosha` — CONTENT_FIX+K1
fields changed: `cancellation_conditions`, `classical_citations`, `formation_rule_jsonb`, `severity_grades`

- `cancellation_conditions`
  - before: {"bhanga": ["same nakshatra but different pada", "same rashi different nakshatra", "specific Nadi-bhanga rules"]}
  - after: {"bhanga": ["same nakṣatra, different pāda (MC v.37)", "same rāśi, different nakṣatra (v.37 ṭīkā)", "regional (optional flag): ādya/antya doṣa not applied south of the Godāvarī or to Kṣatriyas (v.34 ṭīkā)"]}
- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1", "note": "(three nāḍī lists in the verse)", "locus": "PG96:C1–PG97:C1", "excerpt": "Marriage of a couple falling within one and the same nāḍī is not good; falling in the middle nāḍī, it means the death of both", "text_id": "muhurta_chintamani", "human_locus": "Vivāha-prakaraṇa v.34"}, {"kind": "K1", "locus": "PG100:C1", "excerpt": "no doṣa of nāḍī or of the gaṇas when the nakṣatra is the same but the pādas differ", "text_id": "muhurta_chintamani", "human_locus": "v.37"}, {"kind": "K1", "locus": "PG93:C1", "excerpt": "nāḍī = 8 guṇa of 36", "text_id": "muhurta_chintamani", "human_locus": "v.21 ṭīkā"}, {"kind": "K2", "note": "name is modern", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]
- `formation_rule_jsonb`
  - before: {"requires": "same Nadi (Aadi/Madhya/Antya) for both partners' Moon nakshatras"}
  - after: {"same_nadi": true, "nadi_lists_mc_v34": {"adya": ["Ashvini", "Ardra", "Punarvasu", "Uttaraphalguni", "Hasta", "Jyeshtha", "Mula", "Shatabhisha", "Purvabhadrapada"], "antya": ["Krittika", "Rohini", "Ashlesha", "Magha", "Svati", "Vishakha", "Uttarashadha", "Shravana", "Revati"], "madhya": ["Bharani", "Mrigashira", "Pushya", "Purvaphalguni", "Chitra", "Anuradha", "Purvashadha", "Dhanishtha", "Uttarabhadrapada"]}}
- `severity_grades`
  - before: {"severe": "same Nadi and same nakshatra-pada"}
  - after: {"severe": "same madhya nāḍī (\"death of both\")", "moderate": "same ādya or antya nāḍī"}

### `naga_dosha_nodes_kendra` — LABEL_K2_MODERN
fields changed: `classical_citations`, `school`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K2", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]
- `school`
  - before: parashari
  - after: modern

### `naga_dosha_rahu_lagna` — LABEL_K2_MODERN
fields changed: `classical_citations`, `school`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K2", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]
- `school`
  - before: parashari
  - after: modern

### `pitra_dosha_9th_lord_afflicted` — LABEL_K2_MODERN
fields changed: `classical_citations`, `school`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K2", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}, {"kind": "K1_ANALOGUE", "note": "classical Pitṛ-śāpa is a progeny-loss doctrine; this row's fortune / ancestral-debt scope is modern", "locus": "PG980:C1–PG981:C1", "excerpt": "no male issue as a result of the curse of the father in the previous birth, if ... the Sun as lord of the 5th posited in a trikona with a malefic is hemmed in between malefics", "text_id": "bphs", "relation": "classical analogue, not the source of this rule", "human_locus": "Ch.83 (Curses of the previous birth) §20-30"}]
- `school`
  - before: parashari
  - after: modern

### `pitra_dosha_sun_12th_malefic` — LABEL_K2_MODERN
fields changed: `classical_citations`, `school`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K2", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}, {"kind": "K1_ANALOGUE", "locus": "PG47:C1", "excerpt": "Predict similar results regarding the father of the native, if the Sun joins malefics at birth", "text_id": "saravali", "relation": "classical analogue, not the source of this rule", "human_locus": "Ch.16 §36"}, {"kind": "K1_ANALOGUE", "note": "classical father-affliction; the name \"Pitra dosha\" and the ancestral-debt reading are modern", "locus": "PG115:C1", "excerpt": "Early loss of father will take place if the Sun is with a malefic or is hemmed between malefics", "text_id": "bphs", "relation": "classical analogue, not the source of this rule", "human_locus": "(Evils to father) §36"}]
- `school`
  - before: parashari
  - after: modern

### `pitra_dosha_sun_rahu` — LABEL_K2_MODERN
fields changed: `classical_citations`, `school`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K2", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}, {"kind": "K1_ANALOGUE", "locus": "PG47:C1", "excerpt": "Predict similar results regarding the father of the native, if the Sun joins malefics at birth", "text_id": "saravali", "relation": "classical analogue, not the source of this rule", "human_locus": "Ch.16 §36"}, {"kind": "K1_ANALOGUE", "note": "classical father-affliction; the name \"Pitra dosha\" and the ancestral-debt reading are modern", "locus": "PG115:C1", "excerpt": "Early loss of father will take place if the Sun is with a malefic or is hemmed between malefics", "text_id": "bphs", "relation": "classical analogue, not the source of this rule", "human_locus": "(Evils to father) §36"}]
- `school`
  - before: parashari
  - after: modern

### `pitra_dosha_sun_saturn_conjunction` — LABEL_K2_MODERN
fields changed: `classical_citations`, `school`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K2", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}, {"kind": "K1_ANALOGUE", "locus": "PG47:C1", "excerpt": "Predict similar results regarding the father of the native, if the Sun joins malefics at birth", "text_id": "saravali", "relation": "classical analogue, not the source of this rule", "human_locus": "Ch.16 §36"}, {"kind": "K1_ANALOGUE", "note": "classical father-affliction; the name \"Pitra dosha\" and the ancestral-debt reading are modern", "locus": "PG115:C1", "excerpt": "Early loss of father will take place if the Sun is with a malefic or is hemmed between malefics", "text_id": "bphs", "relation": "classical analogue, not the source of this rule", "human_locus": "(Evils to father) §36"}]
- `school`
  - before: parashari
  - after: modern

### `pitru_dosha` — LABEL_K2_MODERN
fields changed: `classical_citations`, `school`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K2", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}, {"kind": "K1_ANALOGUE", "note": "classical Pitṛ-śāpa is a progeny-loss doctrine; this row's fortune / ancestral-debt scope is modern", "locus": "PG980:C1–PG981:C1", "excerpt": "no male issue as a result of the curse of the father in the previous birth, if ... the Sun as lord of the 5th posited in a trikona with a malefic is hemmed in between malefics", "text_id": "bphs", "relation": "classical analogue, not the source of this rule", "human_locus": "Ch.83 (Curses of the previous birth) §20-30"}]
- `school`
  - before: parashari
  - after: modern

### `punarphoo` — CONTENT_FIX+K2
fields changed: `classical_citations`, `name_en`, `name_sa`, `school`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K2", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}, {"kind": "K1_UNVERIFIED", "claimed_text": "classical dvi-graha effect of Moon–Saturn claimed (Brihat Jataka Adh.14 / Saravali Ch.15 two-planet yogas, corpus ≈ saravali PG42–43 unread)", "name_collision": "the classical Viṣa-yoga is a tithi×vāra muhūrta yoga (muhurta_chintamani:PG17:C2 v.8); never cite it for Moon–Saturn"}]
- `name_en`
  - before: Punarphoo Dosha
  - after: Moon–Saturn conjunction/aspect (Punarphoo; popularly "Vish dosha")
- `name_sa`
  - before: Punarphū Doṣa
  - after: Candra-Śani-yuti (Punarphū)
- `school`
  - before: parashari
  - after: modern

### `rajju_dosha` — KEEP_UNVERIFIED_LABELLED
fields changed: `classical_citations`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1_UNVERIFIED", "note": "MC Vivāha-prakaraṇa vv.21-38 (muhurta_chintamani:PG93–PG100) read in full in pass 2 and does not contain it", "needs": "a daśa-kūṭa text (Vivāha-paṭala / Kālaprakāśikā / Jyotirnibandha) — none in corpus", "claimed_text": "classical source claimed (daśa-kūṭa item)"}, {"kind": "K2", "note": "name is modern", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]

### `sade_sati` — APPLY_K1
fields changed: `classical_citations`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1", "locus": "PG330:C1", "excerpt": "Saturn's transit through the Janmarasi ... disease ... funeral rites; in the 2nd ... trouble to wealth and children; ... 12th ... worthless and fruitless business ... robbed", "text_id": "phaladeepika", "human_locus": "Adh. XXVI śl.22-23"}, {"kind": "K2", "note": "the name \"Sade Sati\", the 7.5-year total and the rising/peak/setting phases are modern usage (duration is arithmetic on Saturn's ~2.5 years per sign)", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]

### `shakata` — KEEP_UNVERIFIED_LABELLED
fields changed: `classical_citations`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1_UNVERIFIED", "note": "candidates in corpus: Jataka Parijata Adh. VII yoga chapter (PG462–464 read, not there), Phaladeepika Adh. VI; do NOT cite saravali:PG59:C2 (Nābhasa Śakaṭa, a different yoga)", "claimed_text": "classical source claimed (Candra–Guru Śakaṭa: Moon in 6/8/12 from Jupiter, cancelled by Jupiter in a kendra)"}, {"kind": "K2", "note": "name is modern", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]

### `shrapit_dosha` — LABEL_K2_MODERN
fields changed: `classical_citations`, `school`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K2", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]
- `school`
  - before: parashari
  - after: modern

### `stree_deergha_dosha` — KEEP_UNVERIFIED_LABELLED
fields changed: `classical_citations`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1_UNVERIFIED", "note": "MC Vivāha-prakaraṇa vv.21-38 (muhurta_chintamani:PG93–PG100) read in full in pass 2 and does not contain it", "needs": "a daśa-kūṭa text (Vivāha-paṭala / Kālaprakāśikā / Jyotirnibandha) — none in corpus", "claimed_text": "classical source claimed (daśa-kūṭa item)"}, {"kind": "K2", "note": "name is modern", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]

### `surya_grahan_dosha` — LABEL_K2_MODERN
fields changed: `classical_citations`, `school`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K2", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}, {"kind": "K1_ANALOGUE", "note": "classical doṣa is birth DURING an eclipse; luminary-conjunct-node is a modern generalisation", "locus": "PG1016:C1", "excerpt": "a person whose birth takes place at the time of solar or lunar eclipse suffers from ailments, distress and poverty and faces danger of death", "text_id": "bphs", "relation": "classical analogue, not the source of this rule", "human_locus": "Ch.91 (Birth in Eclipses) §1-14"}]
- `school`
  - before: parashari
  - after: modern

### `tara_dosha_compat` — APPLY_K1
fields changed: `classical_citations`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1", "locus": "PG93:C1", "excerpt": "count from the bride's nakṣatra to the groom's and back, divide by 9; remainders 3, 5, 7 inauspicious ... 3 guṇa", "text_id": "muhurta_chintamani", "human_locus": "Vivāha-prakaraṇa v.24 (ṭīkā)"}, {"kind": "K2", "note": "name is modern", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]

### `varna_dosha` — APPLY_K1
fields changed: `classical_citations`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1", "locus": "PG93:C1", "excerpt": "Pisces, Scorpio, Cancer Brāhmaṇa; 1,5,9 Kṣatriya; 2,6,10 Vaiśya; 3,7,11 Śūdra; a groom of lower varṇa than the bride is not good; 1 guṇa", "text_id": "muhurta_chintamani", "human_locus": "Vivāha-prakaraṇa v.22 (ṭīkā)"}, {"kind": "K2", "note": "name is modern", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]

### `vashya_dosha` — APPLY_K1
fields changed: `classical_citations`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1", "locus": "PG93:C1", "excerpt": "all signs except Leo are vaśya to the human signs ... water signs, being food of humans, are their vaśya ... 2 guṇa when the bride's sign is vaśya to the groom's", "text_id": "muhurta_chintamani", "human_locus": "Vivāha-prakaraṇa v.23 (ṭīkā)"}, {"kind": "K2", "note": "name is modern", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]

### `vedha_dosha` — KEEP_UNVERIFIED_LABELLED
fields changed: `classical_citations`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1_UNVERIFIED", "note": "MC Vivāha-prakaraṇa vv.21-38 (muhurta_chintamani:PG93–PG100) read in full in pass 2 and does not contain it", "needs": "a daśa-kūṭa text (Vivāha-paṭala / Kālaprakāśikā / Jyotirnibandha) — none in corpus", "claimed_text": "classical source claimed (daśa-kūṭa item)"}, {"kind": "K2", "note": "name is modern", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]

### `vish_kanya_dosha` — KEEP_UNVERIFIED_LABELLED
fields changed: `classical_citations`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1_UNVERIFIED", "note": "BPHS Ch.80 Strī-jātaka lists Viṣa-kanyā in its TOC (bphs:PG492:C1), body ≈ corpus PG927–957 unread; also Jataka Parijata strī-jātaka; do NOT cite muhurta_chintamani:PG17:C2 (Viṣa-yoga, different)", "claimed_text": "classical source claimed (Viṣa-kanyā: tithi+vāra+nakṣatra)"}, {"kind": "K2", "note": "name is modern", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]

### `yoni_dosha` — APPLY_K1
fields changed: `classical_citations`

- `classical_citations`
  - before: [{"text_id": "classical_tradition"}]
  - after: [{"kind": "K1", "locus": "PG94:C1", "excerpt": "fourteen yonis by nakṣatra pair; \"enmities: cow–tiger, elephant–lion, horse–buffalo, dog–deer, mongoose–serpent, monkey–sheep, cat–rat ... 4 guṇa\"", "text_id": "muhurta_chintamani", "human_locus": "Vivāha-prakaraṇa vv.25-26 (ṭīkā)"}, {"kind": "K2", "note": "name is modern", "label": "modern practice / project judgment", "decision_id": "OS-2026-10-05-CITATIONS"}]



# Row diff — bg_doshas reference projection (reference_doshas), citation pass 2

Decision OS-2026-10-05-CITATIONS (PASS2_DECISIONS.tsv, 53 brahma_dosha_catalog rows): 13 REMOVE, 7 APPLY_K1, 7 CONTENT_FIX+K1, 3 CONTENT_FIX+K2, 8 KEEP_UNVERIFIED_LABELLED, 15 LABEL_K2_MODERN. The 26 other dosha rows are identical before and after.

Table `reference_doshas`, natural key `canonical_id`. Before = the writer replayed from origin/main; after = the writer replayed from this branch (both on a disposable local PostgreSQL, no production access).

| | rows |
|---|---|
| before | 79 |
| after | 66 |
| removed | 14 |
| added | 1 |
| changed (same key) | 1 |
| unchanged | 64 |

The one rename (kemadruma_compat_kuja -> kuja_dosha_from_venus) changes the natural key, so it is listed under Removed and under Added.

## Removed (14)

- `kala_sarpa_anant`
- `kala_sarpa_ghatak`
- `kala_sarpa_karkotak`
- `kala_sarpa_kulik`
- `kala_sarpa_mahapadma`
- `kala_sarpa_padma`
- `kala_sarpa_shankhachud`
- `kala_sarpa_shankhpal`
- `kala_sarpa_sheshnag`
- `kala_sarpa_takshak`
- `kala_sarpa_vasuki`
- `kala_sarpa_vishdhar`
- `kemadruma_compat_kuja`
- `vish_dosha`

## Added (1)

- `kuja_dosha_from_venus`

## Changed (1)

### `punarphoo`
fields changed: `name_en`

- `name_en`
  - before: Punarphoo Dosha
  - after: Moon–Saturn conjunction/aspect (Punarphoo; popularly "Vish dosha")


# Ontology partition (entity_class='dosha') — summary

The same writer owns the dosha partition of the shared `brahma_ontology` table: 79 rows before, 66 after (the shared table moves 741 -> 728 rows). Its row-by-row diff is in ROW_DIFF_bg_ontology_v1_0.md (bg_ontology branch).

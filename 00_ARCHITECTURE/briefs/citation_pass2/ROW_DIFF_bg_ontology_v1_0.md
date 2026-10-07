# Row diff — bg_ontology dosha partition (brahma_ontology, entity_class='dosha'), citation pass 2

> **APPLY ORDER (SS 2026-10-05).** (1) rebuild **bg_doshas** (it writes this partition; accept bg_yogas, bg_dasha_systems and bg_ontology showing stale: the shared grp_brahma_ontology fingerprint moves); (2) rebuild **bg_ontology in the DEFAULT mode**
> (there is NO expected-change file for it: its rows already moved in step 1, so an expected-change dispatch could never be MET); (3) rebuild **ga_structural** in the L1 refresh pass BEFORE the L2 refresh.
>
> The `entity_class='dosha'` partition is written by the bg_doshas writer, not by bg_ontology's (`l0_ontology.seed_ontology` leaves `dosha`, `yoga` and `dasha_system` to their co-writers). The 13 removals and 40 edits below land when bg_doshas is rebuilt.
> bg_ontology's floor is the achieved count: 741 (R4 census total, not re-read live) less the 13 removed dosha nodes = 728 (migration 1325).


Decision OS-2026-10-05-CITATIONS (PASS2_DECISIONS.tsv, 53 brahma_ontology dosha rows, identical decisions to the catalog rows): 13 REMOVE, 7 APPLY_K1, 7 CONTENT_FIX+K1, 3 CONTENT_FIX+K2, 8 KEEP_UNVERIFIED_LABELLED, 15 LABEL_K2_MODERN.
The dosha partition of brahma_ontology is written by the bg_doshas writer (l0_doshas.py seed_doshas), not by bg_ontology's own writer (which leaves entity_class='dosha' to its co-writer). The other ontology classes (662 rows of the 741) are untouched.

Table `brahma_ontology`, natural key `entity_class+canonical_id`. Before = the writer replayed from origin/main; after = the writer replayed from this branch (both on a disposable local PostgreSQL, no production access).

| | rows |
|---|---|
| before | 79 |
| after | 66 |
| removed | 14 |
| added | 1 |
| changed (same key) | 39 |
| unchanged | 26 |

Keys are (entity_class, canonical_id); the 26 dosha rows not in the decision and every non-dosha class are identical before and after. Table total 741 -> 728.

## Removed (14)

- `dosha/kala_sarpa_anant` — REMOVE
- `dosha/kala_sarpa_ghatak` — REMOVE
- `dosha/kala_sarpa_karkotak` — REMOVE
- `dosha/kala_sarpa_kulik` — REMOVE
- `dosha/kala_sarpa_mahapadma` — REMOVE
- `dosha/kala_sarpa_padma` — REMOVE
- `dosha/kala_sarpa_shankhachud` — REMOVE
- `dosha/kala_sarpa_shankhpal` — REMOVE
- `dosha/kala_sarpa_sheshnag` — REMOVE
- `dosha/kala_sarpa_takshak` — REMOVE
- `dosha/kala_sarpa_vasuki` — REMOVE
- `dosha/kala_sarpa_vishdhar` — REMOVE
- `dosha/kemadruma_compat_kuja` — KEEP_UNVERIFIED_LABELLED + RENAME to kuja_dosha_from_venus (removed + added: the natural key changes)
- `dosha/vish_dosha` — REMOVE

## Added (1)

- `dosha/kuja_dosha_from_venus` — RENAME of kemadruma_compat_kuja (K1_UNVERIFIED; name_sa Śukrāt Kuja-doṣa)

## Changed (39)

### `dosha/abhukta_mula_dosha` — CONTENT_FIX+K1
fields changed: `description`, `source_citation`

- `description`
  - before: Considered especially inauspicious for the child/family per tradition; specific shanti prescribed.
  - after: Most evil of the gaṇḍāntas (Indra/Rākṣasa enmity): the child to be given away, or the father not to see its face for 8 years until śānti (BPHS Ch.93 §1-2; MC v.54)
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.93 (Abhukta Moola) §1-2 — bphs:PG1021:C1 — "ruling deity of Jyestha is Indra and ... of Moola is Rakshasa ... this gandanta is considered as the most evil ... father should not see the face of the child for 8 years" ; K1 — BPHS Ch.92 §5 — bphs:PG1019:C1 — "the last 6 ghatikas of Jyestha and first 8 ghatikas of Moola are known as Abhukta Moola" ; K1 — Muhurta Chintamani Nakṣatra-prakaraṇa v.54 — muhurta_chintamani:PG53:C1 — "first eight ghaṭīs of Mūla and the last five nāḍīs of Jyeṣṭhā ... abandon the child; or else the father should not look upon its face for eight years" ; name is modern (OS-2026-10-05-CITATIONS)

### `dosha/angarak` — LABEL_K2_MODERN
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha/bhakoot_dosha` — CONTENT_FIX+K1
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — Muhurta Chintamani Vivāha-prakaraṇa vv.31-32 — muhurta_chintamani:PG95:C1–PG96:C1 — "sixth from an odd sign ... eighth from an even sign ... śatru-ṣaḍaṣṭaka ... brings death ... 5–9 ... loss of sons; if 2–12, poverty ... mitra-ṣaḍaṣṭaka ... auspicious" ; K1 — MC v.32 ṭīkā — muhurta_chintamani:PG96:C1 — five parihāras: ekādhipatya, friendly rāśi-lords, friendly strong aṃśa-lords, rāśi-vaśyatā, tārā-śuddhi; "nāḍī-śuddhi must be present in every case" ; name is modern (OS-2026-10-05-CITATIONS)

### `dosha/chandal_yoga_dosha` — LABEL_K2_MODERN
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha/chandra_grahan_dosha` — CONTENT_FIX+K2
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — BPHS Ch.91 (Birth in Eclipses) §1-14 — bphs:PG1016:C1 — "a person whose birth takes place at the time of solar or lunar eclipse suffers from ailments, distress and poverty and faces danger of death" — classical doṣa is birth DURING an eclipse; luminary-conjunct-node is a modern generalisation

### `dosha/daridra` — CONTENT_FIX+K1
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — BPHS Ch.42 (Combinations for Poverty) §2-5 — bphs:PG412:C1 — "penniless if the ascendant lord is in the 12th as the 12th lord is in the ascendant along with a Maraka lord ... ascendant lord in the 6th while the 6th lord is in the ascendant" ; name is modern (OS-2026-10-05-CITATIONS)

### `dosha/dhaiya` — APPLY_K1
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — Phaladeepika Adh. XXVI śl.22 — phaladeepika:PG330:C1 — "in the 4th house, there will be loss of wife, relation and wealth ... In the 8th house, there will be loss in children, cattle, friends and wealth ... disease" ; K2 — the names "Dhaiya / Panoti / Kantaka / Ashtama Shani" and the 2.5-year framing are later usage; ratified OS-2026-10-05-CITATIONS

### `dosha/gana_dosha` — CONTENT_FIX+K1
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — Muhurta Chintamani Vivāha-prakaraṇa vv.29-30 (Hindi ṭīkā) — muhurta_chintamani:PG95:C1 — rākṣasa-gaṇa = Maghā, Āśleṣā, Dhaniṣṭhā, Jyeṣṭhā, Mūla, Śatabhiṣā, Kṛttikā, Citrā, Viśākhā; "same gaṇa great love; deva–manuṣya middling; rākṣasa–manuṣya death; deva–rākṣasa quarrel" ; K1 — MC v.21 ṭīkā — muhurta_chintamani:PG93:C1 — eight kūṭas carry guṇa 1,2,3,4,5,6,7,8 = 36 (gaṇa = 6) ; name is modern (OS-2026-10-05-CITATIONS)

### `dosha/graha_maitri_dosha` — APPLY_K1
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — Muhurta Chintamani Vivāha-prakaraṇa vv.27-28 (ṭīkā) — muhurta_chintamani:PG94:C1 — friend/enemy/neutral table of the rāśi-lords; 5 guṇa for friends or one lord, down to 0 for mutual enemies ("mṛtyu-ṣaḍaṣṭaka") ; K1 — MC vv.32-33 — muhurta_chintamani:PG96:C1 — "friendship of the rāśi-lords destroys the ṣaḍaṣṭaka and the other doṣas" ; name is modern (OS-2026-10-05-CITATIONS)

### `dosha/grahan` — LABEL_K2_MODERN
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — BPHS Ch.91 (Birth in Eclipses) §1-14 — bphs:PG1016:C1 — "a person whose birth takes place at the time of solar or lunar eclipse suffers from ailments, distress and poverty and faces danger of death" — classical doṣa is birth DURING an eclipse; luminary-conjunct-node is a modern generalisation

### `dosha/guru_chandal` — LABEL_K2_MODERN
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha/kala_amrita_dosha` — LABEL_K2_MODERN
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha/kala_sarpa` — CONTENT_FIX+K2
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha/kuja_dosha_from_moon` — KEEP_UNVERIFIED_LABELLED
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1_UNVERIFIED — classical source claimed (Kuja-doṣa reckoned from Moon / Venus), not verified in our library; needs Vivāha-paṭala / Jātaka-tattva / Praśna-mārga — none in corpus; not in hora_sara, jataka_parijata or muhurta_chintamani (pass-1 search) ; name is modern (OS-2026-10-05-CITATIONS)

### `dosha/lagna_lord_grahan_dosha` — LABEL_K2_MODERN
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha/mahendra_dosha` — KEEP_UNVERIFIED_LABELLED
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1_UNVERIFIED — classical source claimed (daśa-kūṭa item), not verified in our library; MC Vivāha-prakaraṇa vv.21-38 (muhurta_chintamani:PG93–PG100) read in full in pass 2 and does not contain it; needs a daśa-kūṭa text (Vivāha-paṭala / Kālaprakāśikā / Jyotirnibandha) — none in corpus ; name is modern (OS-2026-10-05-CITATIONS)

### `dosha/mool_dosha` — CONTENT_FIX+K1
fields changed: `description`, `source_citation`

- `description`
  - before: Early-childhood vulnerability; tradition prescribes a 27th-day shanti.
  - after: Early-childhood vulnerability (gaṇḍānta birth); śānti after the sūtaka days / after the 12th day (BPHS Ch.92 §6-8, Ch.93 §3-4) — the "27th-day" timing is not in the texts
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — Jataka Parijata śl.59 — jataka_parijata:PG632:C1 — "Ganda at the conclusion of ... Revati, Aslesha or Jyeshta ... and at the commencement of ... Aswini, Magha or Moola" ; K1 — BPHS Ch.92 §3, §6-8 — bphs:PG1018:C1, bphs:PG1019:C1 — "last two ghatikas of Revti and first two ghatikas of Aswini ... Ashlesha ... Makha ... Jyestha ... Moola ... Nakshatra Gandanta"; remedy: cow with calf; father sees child after sūtaka ; K1 — BPHS Ch.94 §8-9 — bphs:PG1026:C1 — "3 cows ... in the case of Jyestha Moola and Ashlesha Makha gandantas, 2 cows in Revati-Ashwini gandantas and 1 cow in other gandantas" ; K1 — MC Nakṣatra-prakaraṇa v.55 — muhurta_chintamani:PG53:C1 — "first pāda of Mūla the father ... second, the mother; third, wealth ... fourth auspicious ... In Āśleṣā the order is reversed" ; name is modern (OS-2026-10-05-CITATIONS)

### `dosha/mrityu_bhaga_dosha` — CONTENT_FIX+K1
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — Phaladeepika Adh. XIII śl.10 — phaladeepika:PG169:C1 — "degrees attained by the Moon in Mesha and the other signs be respectively 26, 12, 13, 25, 24, 11, 26, 14, 13, 25, 5 and 12, they indicate death" (śl.11 gives an alternative set) ; K1_UNVERIFIED — the per-planet/lagna mṛtyu-bhāga table used by L1: classical source claimed (Jātaka Pārijāta, which Phaladeepika cross-refers as "जा.पा. p.38"), not verified in our library ; name is modern (OS-2026-10-05-CITATIONS)

### `dosha/nadi_dosha` — CONTENT_FIX+K1
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — Muhurta Chintamani Vivāha-prakaraṇa v.34 — muhurta_chintamani:PG96:C1–PG97:C1 — "Marriage of a couple falling within one and the same nāḍī is not good; falling in the middle nāḍī, it means the death of both" (three nāḍī lists in the verse) ; K1 — MC v.37 — muhurta_chintamani:PG100:C1 — "no doṣa of nāḍī or of the gaṇas when the nakṣatra is the same but the pādas differ" ; K1 — MC v.21 ṭīkā — muhurta_chintamani:PG93:C1 — nāḍī = 8 guṇa of 36 ; name is modern (OS-2026-10-05-CITATIONS)

### `dosha/naga_dosha_nodes_kendra` — LABEL_K2_MODERN
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha/naga_dosha_rahu_lagna` — LABEL_K2_MODERN
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha/pitra_dosha_9th_lord_afflicted` — LABEL_K2_MODERN
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — BPHS Ch.83 (Curses of the previous birth) §20-30 — bphs:PG980:C1–PG981:C1 — "no male issue as a result of the curse of the father in the previous birth, if ... the Sun as lord of the 5th posited in a trikona with a malefic is hemmed in between malefics" — classical Pitṛ-śāpa is a progeny-loss doctrine; this row's fortune / ancestral-debt scope is modern

### `dosha/pitra_dosha_sun_12th_malefic` — LABEL_K2_MODERN
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — Saravali Ch.16 §36 — saravali:PG47:C1 — "Predict similar results regarding the father of the native, if the Sun joins malefics at birth" ; K1_ANALOGUE — BPHS (Evils to father) §36 — bphs:PG115:C1 — "Early loss of father will take place if the Sun is with a malefic or is hemmed between malefics" — classical father-affliction; the name "Pitra dosha" and the ancestral-debt reading are modern

### `dosha/pitra_dosha_sun_rahu` — LABEL_K2_MODERN
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — Saravali Ch.16 §36 — saravali:PG47:C1 — "Predict similar results regarding the father of the native, if the Sun joins malefics at birth" ; K1_ANALOGUE — BPHS (Evils to father) §36 — bphs:PG115:C1 — "Early loss of father will take place if the Sun is with a malefic or is hemmed between malefics" — classical father-affliction; the name "Pitra dosha" and the ancestral-debt reading are modern

### `dosha/pitra_dosha_sun_saturn_conjunction` — LABEL_K2_MODERN
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — Saravali Ch.16 §36 — saravali:PG47:C1 — "Predict similar results regarding the father of the native, if the Sun joins malefics at birth" ; K1_ANALOGUE — BPHS (Evils to father) §36 — bphs:PG115:C1 — "Early loss of father will take place if the Sun is with a malefic or is hemmed between malefics" — classical father-affliction; the name "Pitra dosha" and the ancestral-debt reading are modern

### `dosha/pitru_dosha` — LABEL_K2_MODERN
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — BPHS Ch.83 (Curses of the previous birth) §20-30 — bphs:PG980:C1–PG981:C1 — "no male issue as a result of the curse of the father in the previous birth, if ... the Sun as lord of the 5th posited in a trikona with a malefic is hemmed in between malefics" — classical Pitṛ-śāpa is a progeny-loss doctrine; this row's fortune / ancestral-debt scope is modern

### `dosha/punarphoo` — CONTENT_FIX+K2
fields changed: `canonical_name_en`, `canonical_name_sa`, `source_citation`, `synonyms`

- `canonical_name_en`
  - before: Punarphoo Dosha
  - after: Moon–Saturn conjunction/aspect (Punarphoo; popularly "Vish dosha")
- `canonical_name_sa`
  - before: Punarphū Doṣa
  - after: Candra-Śani-yuti (Punarphū)
- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_UNVERIFIED — classical dvi-graha effect of Moon–Saturn claimed (Brihat Jataka Adh.14 / Saravali Ch.15 two-planet yogas, corpus ≈ saravali PG42–43 unread), not verified in our library ; NAME COLLISION — the classical Viṣa-yoga is a tithi×vāra muhūrta yoga (muhurta_chintamani:PG17:C2 v.8); never cite it for Moon–Saturn
- `synonyms`
  - before: []
  - after: ["vish_dosha", "Vish Dosha", "Punarphoo", "Chandra-Shani yuti"]

### `dosha/rajju_dosha` — KEEP_UNVERIFIED_LABELLED
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1_UNVERIFIED — classical source claimed (daśa-kūṭa item), not verified in our library; MC Vivāha-prakaraṇa vv.21-38 (muhurta_chintamani:PG93–PG100) read in full in pass 2 and does not contain it; needs a daśa-kūṭa text (Vivāha-paṭala / Kālaprakāśikā / Jyotirnibandha) — none in corpus ; name is modern (OS-2026-10-05-CITATIONS)

### `dosha/sade_sati` — APPLY_K1
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — Phaladeepika Adh. XXVI śl.22-23 — phaladeepika:PG330:C1 — "Saturn's transit through the Janmarasi ... disease ... funeral rites; in the 2nd ... trouble to wealth and children; ... 12th ... worthless and fruitless business ... robbed" ; K2 — the name "Sade Sati", the 7.5-year total and the rising/peak/setting phases are modern usage (duration is arithmetic on Saturn's ~2.5 years per sign); ratified OS-2026-10-05-CITATIONS

### `dosha/shakata` — KEEP_UNVERIFIED_LABELLED
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1_UNVERIFIED — classical source claimed (Candra–Guru Śakaṭa: Moon in 6/8/12 from Jupiter, cancelled by Jupiter in a kendra), not verified in our library; candidates in corpus: Jataka Parijata Adh. VII yoga chapter (PG462–464 read, not there), Phaladeepika Adh. VI; do NOT cite saravali:PG59:C2 (Nābhasa Śakaṭa, a different yoga) ; name is modern (OS-2026-10-05-CITATIONS)

### `dosha/shrapit_dosha` — LABEL_K2_MODERN
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS

### `dosha/stree_deergha_dosha` — KEEP_UNVERIFIED_LABELLED
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1_UNVERIFIED — classical source claimed (daśa-kūṭa item), not verified in our library; MC Vivāha-prakaraṇa vv.21-38 (muhurta_chintamani:PG93–PG100) read in full in pass 2 and does not contain it; needs a daśa-kūṭa text (Vivāha-paṭala / Kālaprakāśikā / Jyotirnibandha) — none in corpus ; name is modern (OS-2026-10-05-CITATIONS)

### `dosha/surya_grahan_dosha` — LABEL_K2_MODERN
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — BPHS Ch.91 (Birth in Eclipses) §1-14 — bphs:PG1016:C1 — "a person whose birth takes place at the time of solar or lunar eclipse suffers from ailments, distress and poverty and faces danger of death" — classical doṣa is birth DURING an eclipse; luminary-conjunct-node is a modern generalisation

### `dosha/tara_dosha_compat` — APPLY_K1
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — Muhurta Chintamani Vivāha-prakaraṇa v.24 (ṭīkā) — muhurta_chintamani:PG93:C1 — "count from the bride's nakṣatra to the groom's and back, divide by 9; remainders 3, 5, 7 inauspicious ... 3 guṇa" ; name is modern (OS-2026-10-05-CITATIONS)

### `dosha/varna_dosha` — APPLY_K1
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — Muhurta Chintamani Vivāha-prakaraṇa v.22 (ṭīkā) — muhurta_chintamani:PG93:C1 — "Pisces, Scorpio, Cancer Brāhmaṇa; 1,5,9 Kṣatriya; 2,6,10 Vaiśya; 3,7,11 Śūdra; a groom of lower varṇa than the bride is not good; 1 guṇa" ; name is modern (OS-2026-10-05-CITATIONS)

### `dosha/vashya_dosha` — APPLY_K1
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — Muhurta Chintamani Vivāha-prakaraṇa v.23 (ṭīkā) — muhurta_chintamani:PG93:C1 — "all signs except Leo are vaśya to the human signs ... water signs, being food of humans, are their vaśya ... 2 guṇa when the bride's sign is vaśya to the groom's" ; name is modern (OS-2026-10-05-CITATIONS)

### `dosha/vedha_dosha` — KEEP_UNVERIFIED_LABELLED
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1_UNVERIFIED — classical source claimed (daśa-kūṭa item), not verified in our library; MC Vivāha-prakaraṇa vv.21-38 (muhurta_chintamani:PG93–PG100) read in full in pass 2 and does not contain it; needs a daśa-kūṭa text (Vivāha-paṭala / Kālaprakāśikā / Jyotirnibandha) — none in corpus ; name is modern (OS-2026-10-05-CITATIONS)

### `dosha/vish_kanya_dosha` — KEEP_UNVERIFIED_LABELLED
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1_UNVERIFIED — classical source claimed (Viṣa-kanyā: tithi+vāra+nakṣatra), not verified in our library; BPHS Ch.80 Strī-jātaka lists Viṣa-kanyā in its TOC (bphs:PG492:C1), body ≈ corpus PG927–957 unread; also Jataka Parijata strī-jātaka; do NOT cite muhurta_chintamani:PG17:C2 (Viṣa-yoga, different) ; name is modern (OS-2026-10-05-CITATIONS)

### `dosha/yoni_dosha` — APPLY_K1
fields changed: `source_citation`

- `source_citation`
  - before: classical tradition (Jyotish)
  - after: K1 — Muhurta Chintamani Vivāha-prakaraṇa vv.25-26 (ṭīkā) — muhurta_chintamani:PG94:C1 — fourteen yonis by nakṣatra pair; "enmities: cow–tiger, elephant–lion, horse–buffalo, dog–deer, mongoose–serpent, monkey–sheep, cat–rat ... 4 guṇa" ; name is modern (OS-2026-10-05-CITATIONS)


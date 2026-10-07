"""CITATION-PASS2 overlay for bg_remedies (brahma_remedy_corpus): decision OS-2026-10-05-CITATIONS.
Implements the 101 brahma_remedy_corpus rows of ACHARYA/CITATION_PASS2/PASS2_DECISIONS.tsv, exactly, as a deterministic overlay on the rows produced by
`l0_remedy_corpus.build_all_remedies()` (no DB access, no generation, no LLM): 25 rows removed, 76 rows edited by remedy_id, one renamed.
Storage format (PASS2_DECISION_RECORD §5): `source_citation` is a text column of segments separated by " ; ", each beginning with a kind tag
(K1 with machine locus <text_id>:PGnnn:Cn + human locus + excerpt, K2 citing the decision id, K1_UNVERIFIED, K1_ANALOGUE); `source_canonical_id` is the corpus
text_id for K1, "k2:OS-2026-10-05-CITATIONS" for K2, "k1_unverified" for an unverified claim; `confidence` is capped at 0.60 on K2 / unverified rows.

SS RULINGS (2026-10-05, applied): (1) mars_matrix_japa: count LEFT UNCHANGED at 10,000 by SS directive; the K1 excerpt quotes the corpus text LITERALLY as scanned ("Mars I 1000", never normalised to 11000) in all nine japa rows and the row text carries the flag "count under verification";
(2) the replacement kuta-parihara remedy row is NOT authored (proposed addition for the owner); (3) every K2 row's classical_ref is the K2 label wording (a K2 row is never dressed as classical, N-151), except the three rows the TSV words individually.
"""
from __future__ import annotations

from typing import Any

DECISION_ID = 'OS-2026-10-05-CITATIONS'
K2_SOURCE_CANONICAL_ID = 'k2:OS-2026-10-05-CITATIONS'
K2_CONFIDENCE_CAP = 0.60

CIT_K2 = (
    'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS'
)
CIT_K2_BEHAVIORAL = (
    'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS (project doctrine: behavioural alignment as the deepest remedy)'
)
CIT_K2_YANTRA_ANALOGUE = (
    'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — BPHS Ch.84 §5 — bphs:PG996:C1 — "sketches of all the above planets should be drawn in the colours belonging to them on a piece of cloth ... placed in their own directions" — classical analogue, not this bīja-yantra\'s source; Yantra Maharnava (sibling citation) not in library'
)
CIT_K1_JAPA = (
    'K1 — BPHS Ch.84 (Remedial measures) §17-20 — bphs:PG998:C1 — "mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000" ; K1_UNVERIFIED — the bīja mantra string (Oṃ … Saḥ … Namaḥ) is the tantric navagraha bīja: Mantra Mahodadhi claimed, not in our library (BPHS pairs the counts with the Vedic graha-mantras)'
)
CIT_K1_HOMA = (
    'K1 — BPHS Ch.84 §21-22 — bphs:PG999:C1 — "Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28"'
)
CIT_K1_PUJA = (
    'K1 — BPHS Ch.84 §15-16 — bphs:PG998:C1 — "Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins" ; K1 — BPHS Ch.84 §3-13 — bphs:PG995:C1–PG997:C1 — idols/metals and dhyāna forms of the nine grahas ; K2 — weekday, Aṣṭottara-śata-nāma and the popular deity mapping (Rahu→Durga, Ketu→Ganesha, Saturn→Hanuman, Mercury→Vishnu) are modern convention; ratified OS-2026-10-05-CITATIONS'
)
REF_K2 = (
    'modern practice / project judgment — OS-2026-10-05-CITATIONS'
)
REF_JAPA = (
    'BPHS Ch.84 §17-20 (Santhanam) — bphs:PG998:C1'
)
REF_HOMA = (
    'BPHS Ch.84 §21-22 — bphs:PG999:C1'
)
REF_PUJA = (
    'BPHS Ch.84 §15-16 — bphs:PG998:C1'
)
EXC_JAPA = (
    'mantras of all the planets and the prescribed number of their recitation ... Sun 7000, Moon 11000, Mars I 1000, Mercury 9000, Jupiter 19000, Venus 16000, Saturn 23000, Rahu 18000, Ketu 17000'
)
EXC_HOMA = (
    'Havan should be performed with Aak, Palash, Khair, Chirchiri, Pipal, Goolar, Shami, Doob and Kush for the Sun ... Ketu respectively ... The number of offerings to the sacred fire is 108 or 28'
)
EXC_PUJA = (
    'Dedicate with devotion to the planet concerned the flowers and garments of the colour belonging to him, sandal, deep, guggul, his metal and the grain dear to him and distribute all these things to Brahmins'
)

REMOVED_REMEDY_IDS: frozenset[str] = frozenset({
    'dosha_bhakoot_vishnu_puja',
    'dosha_gana_shiva_puja',
    'dosha_graha_maitri_puja',
    'dosha_kala_sarpa_anant_shanti',
    'dosha_kala_sarpa_ghatak_shanti',
    'dosha_kala_sarpa_karkotak_shanti',
    'dosha_kala_sarpa_kulik_shanti',
    'dosha_kala_sarpa_mahapadma_shanti',
    'dosha_kala_sarpa_padma_shanti',
    'dosha_kala_sarpa_shankhachud_shanti',
    'dosha_kala_sarpa_shankhpal_shanti',
    'dosha_kala_sarpa_sheshnag_shanti',
    'dosha_kala_sarpa_takshak_shanti',
    'dosha_kala_sarpa_vasuki_shanti',
    'dosha_kala_sarpa_vishdhar_shanti',
    'dosha_mahendra_vishnu_puja',
    'dosha_rajju_shiva_puja',
    'dosha_stree_deergha_puja',
    'dosha_tara_nakshatra_puja',
    'dosha_varna_surya_mantra',
    'dosha_vashya_venus_mantra',
    'dosha_vedha_nakshatra_puja',
    'dosha_vish_dosha_shani_chandra',
    'dosha_vish_kanya_puja',
    'dosha_yoni_puja',
})

RENAMED_REMEDY_IDS: dict[str, str] = {'dosha_kemadruma_compat_kuja_mars': 'dosha_kuja_from_venus_mars'}

# remedy_id -> field overrides. `confidence_cap` is applied as min(existing, cap), never raises a confidence.
PASS2_EDITS: dict[str, dict[str, Any]] = {
    'dosha_abhukta_mula_shanti': {
        'source_canonical_id': 'bphs',
        'source_citation': (
            'K1 — BPHS Ch.93 §3-4 — bphs:PG1021:C1 — "religious remedial rites should be performed after the 12th day after the birth" ; K1 — BPHS Ch.93 §10-20 — bphs:PG1023:C1 — "Instal a kalasha and put in it Panchagavya ... idol of the Rakshasa ... facing west ... worship of its Adhideva Indra and Pratyadhideva Jala"'
        ),
        'classical_ref': 'BPHS Ch.93 §1-4, §10-20 — bphs:PG1021:C1, bphs:PG1023:C1',
        'classical_attestation_text': (
            'religious remedial rites should be performed after the 12th day after the birth ; Instal a kalasha and put in it Panchagavya ... idol of the Rakshasa ... facing west ... worship of its Adhideva Indra and Pratyadhideva Jala'
        ),
        'prescription_text': (
            "Abhukta-Mūla śānti per BPHS Ch.93: rites after the 12th day from birth (§3-4); kalaśa with pañcagavya, śatauṣadhi and holy-river water; idol of the Rākṣasa (Mūla's deity) facing west on a hundred-holed earthen pot, worshipped with white flowers, sandal and cloth; worship of adhideva Indra and pratyadhideva Jala (§10-20). Until then the father does not see the child (§1-2)."
        ),
        'deity': 'Rākṣasa (Mūla); adhideva Indra; pratyadhideva Jala',
    },
    'dosha_angarak_mars_rahu': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'prescription_text': (
            'For Angarak Dosha (Mars-Rahu): perform Hanuman puja on Tuesdays and Rahu shanti on Saturdays. Recite Hanuman Chalisa daily. Donate blood (blood donation; modern practice) on Tuesdays. Wear red coral (if Mars is functional benefic).'
        ),
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'dosha_dhaiya_shani_puja': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'dosha_grahan_surya_chandra_mantra': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': (
            'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — BPHS Ch.91 (Birth in Eclipses) §1-14 — bphs:PG1016:C1 — "a person whose birth takes place at the time of solar or lunar eclipse suffers from ailments, distress and poverty and faces danger of death" — classical doṣa is birth DURING an eclipse; luminary-conjunct-node is a modern generalisation'
        ),
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'dosha_guru_chandal_jupiter_puja': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'dosha_kala_amrita_shanti': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'dosha_kala_sarpa_mantra': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'dosha_kala_sarpa_nag_puja': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'dosha_kemadruma_compat_kuja_mars': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'dosha_kuja_from_moon_hanuman': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'dosha_mool_shanti': {
        'source_canonical_id': 'bphs',
        'source_citation': (
            'K1 — BPHS Ch.92 §6-8 — bphs:PG1019:C1 — "father should see the child born only on the morning next to the end of the days of Sutaka ... Giving a cow with calf in charity in the case of Nakshatra Gandanta" ; K1 — BPHS Ch.93 §3-4 — bphs:PG1021:C1 — "rites should be performed after the 12th day after the birth" ; K1 — BPHS Ch.94 §6-9 — bphs:PG1026:C1 — "3 cows ... Jyestha Moola and Ashlesha Makha ... 2 cows in Revati-Ashwini ... 1 cow in other gandantas ... Mrityunjaya japa"'
        ),
        'classical_ref': (
            'BPHS Ch.92 §6-8 (bphs:PG1019:C1); Ch.93 §3-4 (bphs:PG1021:C1); Ch.94 §6-9 (bphs:PG1026:C1)'
        ),
        'classical_attestation_text': (
            'father should see the child born only on the morning next to the end of the days of Sutaka ... Giving a cow with calf in charity in the case of Nakshatra Gandanta ; rites should be performed after the 12th day after the birth ; 3 cows ... Jyestha Moola and Ashlesha Makha ... 2 cows in Revati-Ashwini ... 1 cow in other gandantas ... Mrityunjaya japa'
        ),
        'prescription_text': (
            'Gaṇḍānta / gaṇḍamūla śānti: performed after the sūtaka days / after the 12th day, the father seeing the child only then (BPHS Ch.92 §6-8; Ch.93 §3-4). Gifts: a cow with calf for nakṣatra-gaṇḍānta (Ch.92 §6-8); by junction 3 cows (Jyeṣṭhā–Mūla, Āśleṣā–Maghā), 2 (Revatī–Aśvinī), 1 (others) or their value (Ch.94 §8-9); Mṛtyuñjaya japa and abhiṣeka (Ch.94 §6).'
        ),
    },
    'dosha_mrityu_bhaga_mantra': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'prescription_text': (
            "For Mrityu Bhaga Dosha: propitiate the afflicted planet with its beej mantra 108 times daily. Perform Mahamrityunjaya japa (11,000 minimum — a project parameter, not a classical count). The 'death-degree' position is pacified by strengthening the planet's digbala, dasha timing awareness, and puja on its day."
        ),
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'dosha_nadi_mahamrityunjaya': {
        'source_canonical_id': 'muhurta_chintamani',
        'source_citation': (
            'K1 — Muhurta Chintamani Vivāha-prakaraṇa v.34 ṭīkā — muhurta_chintamani:PG97:C1 — "a śānti for the nāḍī, namely: japa of the Mṛtyuñjaya and other mantras, the gift of a golden nāḍī, and — in the varṇa and the other kūṭas — the giving of a cow, grain, cloth and gold"'
        ),
        'classical_ref': 'MC Vivāha-prakaraṇa v.34 ṭīkā — muhurta_chintamani:PG97:C1',
        'classical_attestation_text': (
            'a śānti for the nāḍī, namely: japa of the Mṛtyuñjaya and other mantras, the gift of a golden nāḍī, and — in the varṇa and the other kūṭas — the giving of a cow, grain, cloth and gold'
        ),
        'prescription_text': (
            'Nāḍī-doṣa śānti per MC Vivāha v.34 ṭīkā: japa of the Mṛtyuñjaya and other mantras, and the gift of a golden nāḍī (for the other kūṭas: a cow, grain, cloth and gold); applied when the parihāras of vv.32-37 obtain. [Modern elaboration, labelled: the 1,25,000 count; "Nadi Nirākaraṇa pūjā prescribed by a learned astrologer".]'
        ),
    },
    'dosha_pitru_surya_mantra': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'dosha_pitru_tarpan': {
        'source_canonical_id': 'k1_unverified',
        'source_citation': (
            'K1_UNVERIFIED — classical (dharmaśāstra) source claimed (pitṛ-tarpaṇa on amāvāsyā; Gayā-śrāddha), not verified in our library; needs Garuḍa Purāṇa Preta-kalpa or a smṛti śrāddha-prakaraṇa — none in corpus ; K2 — the attachment to "Pitru Dosha" is modern usage; ratified OS-2026-10-05-CITATIONS'
        ),
        'classical_ref': 'dharmaśāstra śrāddha prescription — text not in library',
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'dosha_punarphoo_shani_mantra': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': (
            'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; NAME COLLISION — the classical Viṣa-yoga is a tithi×vāra muhūrta yoga (muhurta_chintamani:PG17:C2 v.8); never cite it for Moon–Saturn'
        ),
        'classical_ref': REF_K2,
        'prescription_text': (
            'For the Moon–Saturn conjunction/aspect (Punarphoo; popularly "Vish dosha"): Śani Chalisa on Saturdays and Candra Aṣṭottara on Mondays; Mahāmṛtyuñjaya japa; Śiva pūjā on Mondays (merged from the removed vish-dosha row). The combination delays but does not deny.'
        ),
        'domain': 'general',
        'contraindications': 'No blanket gem advice: a Pearl for the Moon only after functional-benefic assessment',
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'dosha_sade_sati_shani_charity': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': (
            'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1 — BPHS Ch.84 §25 — bphs:PG999:C1 — "things to be given in charity are (1) cow with calf, (2) conch, (3) bullock, (4) gold, (5) robes, (6) horse, (7) black cow, (8) weapons made of iron and (9) goat, respectively" (Saturn = black cow; iron = Rahu)'
        ),
        'classical_ref': 'BPHS Ch.84 §25 — bphs:PG999:C1 (black cow); remainder modern',
        'prescription_text': (
            "Classical Saturn dāna per BPHS Ch.84 §25: a black cow (bphs:PG999:C1). Modern practice, labelled (not from BPHS Ch.84 §25): for Sade Sati, donate black sesame, mustard oil, iron, and black cloth to laborers or the poor on Saturdays throughout the 7.5-year period. Service to the elderly and underprivileged is the most direct Saturn remedy. Note: in BPHS Ch.84 §25 iron is Rahu's dāna item, not Saturn's."
        ),
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'dosha_sade_sati_shani_mantra': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'dosha_shakata_guru_puja': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'dosha_shrapit_shani_rahu': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'prescription_text': (
            'For Shrapit Dosha (Saturn-Rahu): perform a Shrapit Dosha Nivaran homa with prescribed samidha on Saturdays. Recite the Śani and Rāhu mantras (count a project parameter). Donate black sesame and iron. Visit a Shani Shingnapur (or equivalent Shani temple) on Saturdays (modern pilgrimage practice).'
        ),
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'jupiter_matrix_behavioral': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2_BEHAVIORAL,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'jupiter_matrix_homa': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_HOMA,
        'classical_ref': REF_HOMA,
        'classical_attestation_text': EXC_HOMA,
        'prescription_text': (
            'Graha-śānti homa for Jupiter with its samidhā pippala (aśvattha) (BPHS Ch.84 §21-22), offered with honey, ghee, curd or milk; 108 (or 28) āhutis per the text. [Modern practice, labelled: larger counts such as 1008; weekday Thursday.]'
        ),
    },
    'jupiter_matrix_japa': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_JAPA,
        'classical_ref': REF_JAPA,
        'classical_attestation_text': EXC_JAPA,
        'prescription_text': (
            'Japa of the Jupiter mantra to the BPHS count of 19,000 (BPHS Ch.84 §17-20, which pairs the counts with the Vedic graha-mantras). The bīja mantra carried here is the tantric navagraha bīja (Mantra Mahodadhi — not in our library; labelled K1_UNVERIFIED). Weekday is modern convention.'
        ),
    },
    'jupiter_matrix_puja': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_PUJA,
        'classical_ref': REF_PUJA,
        'classical_attestation_text': EXC_PUJA,
        'prescription_text': (
            "Graha-śānti pūjā of Jupiter per BPHS Ch.84 §15-16: offer flowers and garments of the planet's colour, sandal, lamp (dīpa), guggula incense, its metal and its grain, then give these to Brahmins; feed Brahmins the planet's food (§23-24). [Modern additions, labelled: weekday Thursday; Aṣṭottara-śata-nāma; popular deity association as currently in the deity field.]"
        ),
        'deity': 'Jupiter (BPHS Ch.84 §6-13 dhyāna form)',
    },
    'jupiter_matrix_vrata': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'jupiter_matrix_yantra': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2_YANTRA_ANALOGUE,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'ketu_matrix_behavioral': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2_BEHAVIORAL,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'ketu_matrix_homa': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_HOMA,
        'classical_ref': REF_HOMA,
        'classical_attestation_text': EXC_HOMA,
        'prescription_text': (
            'Graha-śānti homa for Ketu with its samidhā kuśa (BPHS Ch.84 §21-22), offered with honey, ghee, curd or milk; 108 (or 28) āhutis per the text. [Modern practice, labelled: larger counts such as 1008; weekday Saturday/Tuesday.]'
        ),
    },
    'ketu_matrix_japa': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_JAPA,
        'classical_ref': REF_JAPA,
        'classical_attestation_text': EXC_JAPA,
        'prescription_text': (
            'Japa of the Ketu mantra to the BPHS count of 17,000 (BPHS Ch.84 §17-20, which pairs the counts with the Vedic graha-mantras). The bīja mantra carried here is the tantric navagraha bīja (Mantra Mahodadhi — not in our library; labelled K1_UNVERIFIED). Weekday is modern convention.'
        ),
    },
    'ketu_matrix_puja': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_PUJA,
        'classical_ref': REF_PUJA,
        'classical_attestation_text': EXC_PUJA,
        'prescription_text': (
            "Graha-śānti pūjā of Ketu per BPHS Ch.84 §15-16: offer flowers and garments of the planet's colour, sandal, lamp (dīpa), guggula incense, its metal and its grain, then give these to Brahmins; feed Brahmins the planet's food (§23-24). [Modern additions, labelled: weekday Saturday/Tuesday; Aṣṭottara-śata-nāma; popular deity association as currently in the deity field.]"
        ),
        'deity': 'Ketu (BPHS Ch.84 §6-13 dhyāna form)',
    },
    'ketu_matrix_vrata': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'ketu_matrix_yantra': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2_YANTRA_ANALOGUE,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'mars_matrix_behavioral': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2_BEHAVIORAL,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'mars_matrix_homa': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_HOMA,
        'classical_ref': REF_HOMA,
        'classical_attestation_text': EXC_HOMA,
        'prescription_text': (
            'Graha-śānti homa for Mars with its samidhā khadira (Khair) (BPHS Ch.84 §21-22), offered with honey, ghee, curd or milk; 108 (or 28) āhutis per the text. [Modern practice, labelled: larger counts such as 1008; weekday Tuesday.]'
        ),
    },
    'mars_matrix_japa': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_JAPA,
        'classical_ref': REF_JAPA,
        'classical_attestation_text': EXC_JAPA,
        'prescription_text': (
            'Japa of the Mars mantra to the count of 10,000 (BPHS Ch.84 §17-20, which pairs the counts with the Vedic graha-mantras; count under verification: corpus scan reads "I 1000" (10,000 or 11,000); row keeps 10,000 until the page image is checked). The bīja mantra carried here is the tantric navagraha bīja (Mantra Mahodadhi — not in our library; labelled K1_UNVERIFIED). Weekday is modern convention.'
        ),
    },
    'mars_matrix_puja': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_PUJA,
        'classical_ref': REF_PUJA,
        'classical_attestation_text': EXC_PUJA,
        'prescription_text': (
            "Graha-śānti pūjā of Mars per BPHS Ch.84 §15-16: offer flowers and garments of the planet's colour, sandal, lamp (dīpa), guggula incense, its metal and its grain, then give these to Brahmins; feed Brahmins the planet's food (§23-24). [Modern additions, labelled: weekday Tuesday; Aṣṭottara-śata-nāma; popular deity association as currently in the deity field.]"
        ),
        'deity': 'Mars (BPHS Ch.84 §6-13 dhyāna form)',
    },
    'mars_matrix_vrata': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'mars_matrix_yantra': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2_YANTRA_ANALOGUE,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'mercury_matrix_behavioral': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2_BEHAVIORAL,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'mercury_matrix_homa': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_HOMA,
        'classical_ref': REF_HOMA,
        'classical_attestation_text': EXC_HOMA,
        'prescription_text': (
            'Graha-śānti homa for Mercury with its samidhā apāmārga (Chirchiri) (BPHS Ch.84 §21-22), offered with honey, ghee, curd or milk; 108 (or 28) āhutis per the text. [Modern practice, labelled: larger counts such as 1008; weekday Wednesday.]'
        ),
    },
    'mercury_matrix_japa': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_JAPA,
        'classical_ref': REF_JAPA,
        'classical_attestation_text': EXC_JAPA,
        'prescription_text': (
            'Japa of the Mercury mantra to the BPHS count of 9,000 (BPHS Ch.84 §17-20, which pairs the counts with the Vedic graha-mantras). The bīja mantra carried here is the tantric navagraha bīja (Mantra Mahodadhi — not in our library; labelled K1_UNVERIFIED). Weekday is modern convention.'
        ),
    },
    'mercury_matrix_puja': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_PUJA,
        'classical_ref': REF_PUJA,
        'classical_attestation_text': EXC_PUJA,
        'prescription_text': (
            "Graha-śānti pūjā of Mercury per BPHS Ch.84 §15-16: offer flowers and garments of the planet's colour, sandal, lamp (dīpa), guggula incense, its metal and its grain, then give these to Brahmins; feed Brahmins the planet's food (§23-24). [Modern additions, labelled: weekday Wednesday; Aṣṭottara-śata-nāma; popular deity association as currently in the deity field.]"
        ),
        'deity': 'Mercury (BPHS Ch.84 §6-13 dhyāna form)',
    },
    'mercury_matrix_vrata': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'mercury_matrix_yantra': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2_YANTRA_ANALOGUE,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'moon_matrix_behavioral': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2_BEHAVIORAL,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'moon_matrix_homa': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_HOMA,
        'classical_ref': REF_HOMA,
        'classical_attestation_text': EXC_HOMA,
        'prescription_text': (
            'Graha-śānti homa for Moon with its samidhā palāśa (BPHS Ch.84 §21-22), offered with honey, ghee, curd or milk; 108 (or 28) āhutis per the text. [Modern practice, labelled: larger counts such as 1008; weekday Monday.]'
        ),
    },
    'moon_matrix_japa': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_JAPA,
        'classical_ref': REF_JAPA,
        'classical_attestation_text': EXC_JAPA,
        'prescription_text': (
            'Japa of the Moon mantra to the BPHS count of 11,000 (BPHS Ch.84 §17-20, which pairs the counts with the Vedic graha-mantras). The bīja mantra carried here is the tantric navagraha bīja (Mantra Mahodadhi — not in our library; labelled K1_UNVERIFIED). Weekday is modern convention.'
        ),
    },
    'moon_matrix_puja': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_PUJA,
        'classical_ref': REF_PUJA,
        'classical_attestation_text': EXC_PUJA,
        'prescription_text': (
            "Graha-śānti pūjā of Moon per BPHS Ch.84 §15-16: offer flowers and garments of the planet's colour, sandal, lamp (dīpa), guggula incense, its metal and its grain, then give these to Brahmins; feed Brahmins the planet's food (§23-24). [Modern additions, labelled: weekday Monday; Aṣṭottara-śata-nāma; popular deity association as currently in the deity field.]"
        ),
        'deity': 'Moon (BPHS Ch.84 §6-13 dhyāna form)',
    },
    'moon_matrix_vrata': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'moon_matrix_yantra': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2_YANTRA_ANALOGUE,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'rahu_matrix_behavioral': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2_BEHAVIORAL,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'rahu_matrix_homa': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_HOMA,
        'classical_ref': REF_HOMA,
        'classical_attestation_text': EXC_HOMA,
        'prescription_text': (
            'Graha-śānti homa for Rahu with its samidhā dūrvā (Doob) (BPHS Ch.84 §21-22), offered with honey, ghee, curd or milk; 108 (or 28) āhutis per the text. [Modern practice, labelled: larger counts such as 1008; weekday Saturday.]'
        ),
    },
    'rahu_matrix_japa': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_JAPA,
        'classical_ref': REF_JAPA,
        'classical_attestation_text': EXC_JAPA,
        'prescription_text': (
            'Japa of the Rahu mantra to the BPHS count of 18,000 (BPHS Ch.84 §17-20, which pairs the counts with the Vedic graha-mantras). The bīja mantra carried here is the tantric navagraha bīja (Mantra Mahodadhi — not in our library; labelled K1_UNVERIFIED). Weekday is modern convention.'
        ),
    },
    'rahu_matrix_puja': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_PUJA,
        'classical_ref': REF_PUJA,
        'classical_attestation_text': EXC_PUJA,
        'prescription_text': (
            "Graha-śānti pūjā of Rahu per BPHS Ch.84 §15-16: offer flowers and garments of the planet's colour, sandal, lamp (dīpa), guggula incense, its metal and its grain, then give these to Brahmins; feed Brahmins the planet's food (§23-24). [Modern additions, labelled: weekday Saturday; Aṣṭottara-śata-nāma; popular deity association as currently in the deity field.]"
        ),
        'deity': 'Rahu (BPHS Ch.84 §6-13 dhyāna form)',
    },
    'rahu_matrix_vrata': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'rahu_matrix_yantra': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2_YANTRA_ANALOGUE,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'saturn_matrix_behavioral': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2_BEHAVIORAL,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'saturn_matrix_homa': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_HOMA,
        'classical_ref': REF_HOMA,
        'classical_attestation_text': EXC_HOMA,
        'prescription_text': (
            'Graha-śānti homa for Saturn with its samidhā śamī (BPHS Ch.84 §21-22), offered with honey, ghee, curd or milk; 108 (or 28) āhutis per the text. [Modern practice, labelled: larger counts such as 1008; weekday Saturday.]'
        ),
    },
    'saturn_matrix_japa': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_JAPA,
        'classical_ref': REF_JAPA,
        'classical_attestation_text': EXC_JAPA,
        'prescription_text': (
            'Japa of the Saturn mantra to the BPHS count of 23,000 (BPHS Ch.84 §17-20, which pairs the counts with the Vedic graha-mantras). The bīja mantra carried here is the tantric navagraha bīja (Mantra Mahodadhi — not in our library; labelled K1_UNVERIFIED). Weekday is modern convention.'
        ),
    },
    'saturn_matrix_puja': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_PUJA,
        'classical_ref': REF_PUJA,
        'classical_attestation_text': EXC_PUJA,
        'prescription_text': (
            "Graha-śānti pūjā of Saturn per BPHS Ch.84 §15-16: offer flowers and garments of the planet's colour, sandal, lamp (dīpa), guggula incense, its metal and its grain, then give these to Brahmins; feed Brahmins the planet's food (§23-24). [Modern additions, labelled: weekday Saturday; Aṣṭottara-śata-nāma; popular deity association as currently in the deity field.]"
        ),
        'deity': 'Saturn (BPHS Ch.84 §6-13 dhyāna form)',
    },
    'saturn_matrix_vrata': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'saturn_matrix_yantra': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2_YANTRA_ANALOGUE,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'stotra_saraswati_mercury_education': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': 'modern devotional practice (Sarasvatī for Budha)',
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'sun_matrix_behavioral': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2_BEHAVIORAL,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'sun_matrix_homa': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_HOMA,
        'classical_ref': REF_HOMA,
        'classical_attestation_text': EXC_HOMA,
        'prescription_text': (
            'Graha-śānti homa for Sun with its samidhā arka (Aak) (BPHS Ch.84 §21-22), offered with honey, ghee, curd or milk; 108 (or 28) āhutis per the text. [Modern practice, labelled: larger counts such as 1008; weekday Sunday.]'
        ),
    },
    'sun_matrix_japa': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_JAPA,
        'classical_ref': REF_JAPA,
        'classical_attestation_text': EXC_JAPA,
        'prescription_text': (
            'Japa of the Sun mantra to the BPHS count of 7,000 (BPHS Ch.84 §17-20, which pairs the counts with the Vedic graha-mantras). The bīja mantra carried here is the tantric navagraha bīja (Mantra Mahodadhi — not in our library; labelled K1_UNVERIFIED). Weekday is modern convention.'
        ),
    },
    'sun_matrix_puja': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_PUJA,
        'classical_ref': REF_PUJA,
        'classical_attestation_text': EXC_PUJA,
        'prescription_text': (
            "Graha-śānti pūjā of Sun per BPHS Ch.84 §15-16: offer flowers and garments of the planet's colour, sandal, lamp (dīpa), guggula incense, its metal and its grain, then give these to Brahmins; feed Brahmins the planet's food (§23-24). [Modern additions, labelled: weekday Sunday; Aṣṭottara-śata-nāma; popular deity association as currently in the deity field.]"
        ),
        'deity': 'Sun (BPHS Ch.84 §6-13 dhyāna form)',
    },
    'sun_matrix_vrata': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'sun_matrix_yantra': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2_YANTRA_ANALOGUE,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'venus_matrix_behavioral': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2_BEHAVIORAL,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'venus_matrix_homa': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_HOMA,
        'classical_ref': REF_HOMA,
        'classical_attestation_text': EXC_HOMA,
        'prescription_text': (
            'Graha-śānti homa for Venus with its samidhā udumbara (Goolar) (BPHS Ch.84 §21-22), offered with honey, ghee, curd or milk; 108 (or 28) āhutis per the text. [Modern practice, labelled: larger counts such as 1008; weekday Friday.]'
        ),
    },
    'venus_matrix_japa': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_JAPA,
        'classical_ref': REF_JAPA,
        'classical_attestation_text': EXC_JAPA,
        'prescription_text': (
            'Japa of the Venus mantra to the BPHS count of 16,000 (BPHS Ch.84 §17-20, which pairs the counts with the Vedic graha-mantras). The bīja mantra carried here is the tantric navagraha bīja (Mantra Mahodadhi — not in our library; labelled K1_UNVERIFIED). Weekday is modern convention.'
        ),
    },
    'venus_matrix_puja': {
        'source_canonical_id': 'bphs',
        'source_citation': CIT_K1_PUJA,
        'classical_ref': REF_PUJA,
        'classical_attestation_text': EXC_PUJA,
        'prescription_text': (
            "Graha-śānti pūjā of Venus per BPHS Ch.84 §15-16: offer flowers and garments of the planet's colour, sandal, lamp (dīpa), guggula incense, its metal and its grain, then give these to Brahmins; feed Brahmins the planet's food (§23-24). [Modern additions, labelled: weekday Friday; Aṣṭottara-śata-nāma; popular deity association as currently in the deity field.]"
        ),
        'deity': 'Venus (BPHS Ch.84 §6-13 dhyāna form)',
    },
    'venus_matrix_vrata': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'venus_matrix_yantra': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2_YANTRA_ANALOGUE,
        'classical_ref': REF_K2,
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
    'yantra_kala_sarpa_shanti': {
        'source_canonical_id': K2_SOURCE_CANONICAL_ID,
        'source_citation': CIT_K2,
        'classical_ref': 'modern Kala Sarpa Shanti yantra practice',
        'prescription_text': (
            'Kala Sarpa Dosha Yantra: a specific yantra prescribed for Kala Sarpa Dosha remediation, combining Rahu and Ketu yantras with a serpent (Naga) motif encircling all the planets. Customarily installed at a Shiva temple (Trimbakeshwar is the popular site — modern practice) during a special Kala Sarpa Shanti puja. The yantra is then worn or installed at home.'
        ),
        'confidence_cap': K2_CONFIDENCE_CAP,
    },
}



def apply_pass2(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a NEW list of NEW row dicts: removed ids dropped, edits applied, renames applied.

    Fails loudly (no silent no-op: CLAUDE.md N.8) when a decision key does not match a produced row, so a seed change that drops a
    decided row cannot quietly void the decision.
    """
    produced = {r["remedy_id"] for r in rows}
    missing = (set(PASS2_EDITS) | set(REMOVED_REMEDY_IDS) | set(RENAMED_REMEDY_IDS)) - produced
    if missing:
        raise RuntimeError(f"citation pass 2: decision keys not produced by the remedy seed: {sorted(missing)}")
    out: list[dict[str, Any]] = []
    for r in rows:
        rid = r["remedy_id"]
        if rid in REMOVED_REMEDY_IDS:
            continue
        new = dict(r)
        edit = PASS2_EDITS.get(rid)
        if edit:
            for field, value in edit.items():
                if field == "confidence_cap":
                    new["confidence"] = min(float(new.get("confidence", 0.85)), float(value))
                else:
                    new[field] = value
        if rid in RENAMED_REMEDY_IDS:
            new["remedy_id"] = RENAMED_REMEDY_IDS[rid]
            if new.get("dosha_target") == "kemadruma_compat_kuja":
                new["dosha_target"] = "kuja_dosha_from_venus"
        out.append(new)
    return out

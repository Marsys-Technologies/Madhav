"""CITATION-PASS2 overlay for bg_doshas / bg_ontology (dosha projections): decision OS-2026-10-05-CITATIONS.

Implements the 53 brahma_dosha_catalog rows (and the identical 53 brahma_ontology entity_class=dosha rows) of ACHARYA/CITATION_PASS2/PASS2_DECISIONS.tsv exactly, as a
deterministic overlay on the `DOSHAS` list of l0_doshas.py: 13 rows removed (12 Kala Sarpa named variants, vish_dosha merged into punarphoo), 40 rows edited by canonical_id,
one renamed (kemadruma_compat_kuja -> kuja_dosha_from_venus). The three projections written by bg_doshas (brahma_dosha_catalog, brahma_ontology[dosha], reference_doshas)
all derive from the one list, so they change together; the ontology row takes `source_citation` (text column) and `ontology_synonyms` from here.

Storage format (PASS2_DECISION_RECORD section 5): `classical_citations` (JSONB) is an array with one object per citation segment: K1 {kind,text_id,locus,human_locus,excerpt[,note]},
K2 {kind,decision_id,label[,note]}, K1_UNVERIFIED {kind,claimed_text,needs[,note]}, K1_ANALOGUE {... ,relation}; the ontology text column carries the same segments joined with " ; ".
`school` becomes the new value "modern" only where the decision says the doctrine itself is modern; the machine locus (<text_id>:PGnnn:Cn) resolves in the classical corpus.
"""
from __future__ import annotations

import copy
from typing import Any

DECISION_ID = 'OS-2026-10-05-CITATIONS'

REMOVED_DOSHA_IDS: frozenset[str] = frozenset({
    'kala_sarpa_anant',
    'kala_sarpa_ghatak',
    'kala_sarpa_karkotak',
    'kala_sarpa_kulik',
    'kala_sarpa_mahapadma',
    'kala_sarpa_padma',
    'kala_sarpa_shankhachud',
    'kala_sarpa_shankhpal',
    'kala_sarpa_sheshnag',
    'kala_sarpa_takshak',
    'kala_sarpa_vasuki',
    'kala_sarpa_vishdhar',
    'vish_dosha',
})

RENAMED_DOSHA_IDS: dict[str, str] = {'kemadruma_compat_kuja': 'kuja_dosha_from_venus'}

# ontology synonyms for the FINAL (post-rename) canonical_id; the merge target absorbs the removed vish_dosha id and name.
ONTOLOGY_SYNONYMS: dict[str, list[str]] = {'punarphoo': ['vish_dosha', 'Vish Dosha', 'Punarphoo', 'Chandra-Shani yuti']}

# canonical_id (as in the seed list, before any rename) -> field overrides. `source_citation` is the ontology text column.
PASS2_DOSHA_EDITS: dict[str, dict[str, Any]] = {'angarak': {'classical_citations': [{'kind': 'K2', 'decision_id': 'OS-2026-10-05-CITATIONS', 'label': 'modern practice / project judgment'}],
             'source_citation': 'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS',
             'school': 'modern'},
 'chandal_yoga_dosha': {'classical_citations': [{'kind': 'K2',
                                                 'decision_id': 'OS-2026-10-05-CITATIONS',
                                                 'label': 'modern practice / project judgment'}],
                        'source_citation': 'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS',
                        'school': 'modern'},
 'chandra_grahan_dosha': {'classical_citations': [{'kind': 'K2',
                                                   'decision_id': 'OS-2026-10-05-CITATIONS',
                                                   'label': 'modern practice / project judgment'},
                                                  {'kind': 'K1_ANALOGUE',
                                                   'text_id': 'bphs',
                                                   'locus': 'PG1016:C1',
                                                   'human_locus': 'Ch.91 (Birth in Eclipses) §1-14',
                                                   'excerpt': 'a person whose birth takes place at the time of solar or lunar eclipse suffers from '
                                                              'ailments, distress and poverty and faces danger of death',
                                                   'note': 'classical doṣa is birth DURING an eclipse; luminary-conjunct-node is a modern '
                                                           'generalisation',
                                                   'relation': 'classical analogue, not the source of this rule'}],
                          'source_citation': 'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; '
                                             'K1_ANALOGUE — BPHS Ch.91 (Birth in Eclipses) §1-14 — bphs:PG1016:C1 — "a person whose birth takes '
                                             'place at the time of solar or lunar eclipse suffers from ailments, distress and poverty and faces '
                                             'danger of death" — classical doṣa is birth DURING an eclipse; luminary-conjunct-node is a modern '
                                             'generalisation',
                          'school': 'modern',
                          'formation_rule_jsonb': {'conjunction': [['moon', 'rahu'], ['moon', 'ketu']]}},
 'daridra': {'classical_citations': [{'kind': 'K1',
                                      'text_id': 'bphs',
                                      'locus': 'PG412:C1',
                                      'human_locus': 'Ch.42 (Combinations for Poverty) §2-5',
                                      'excerpt': 'penniless if the ascendant lord is in the 12th as the 12th lord is in the ascendant along with a '
                                                 'Maraka lord ... ascendant lord in the 6th while the 6th lord is in the ascendant'},
                                     {'kind': 'K2',
                                      'decision_id': 'OS-2026-10-05-CITATIONS',
                                      'label': 'modern practice / project judgment',
                                      'note': 'name is modern'}],
             'source_citation': 'K1 — BPHS Ch.42 (Combinations for Poverty) §2-5 — bphs:PG412:C1 — "penniless if the ascendant lord is in the 12th '
                                'as the 12th lord is in the ascendant along with a Maraka lord ... ascendant lord in the 6th while the 6th lord is '
                                'in the ascendant" ; name is modern (OS-2026-10-05-CITATIONS)',
             'formation_rule_jsonb': {'any_of': [{'lagna_lord_in_house': 12, 'house12_lord_in_house': 1, 'with_or_aspected_by': 'maraka_lord'},
                                                 {'lagna_lord_in_house': 6, 'house6_lord_in_house': 1, 'with_or_aspected_by': 'maraka_lord'},
                                                 {'lagna_or_moon_with': 'ketu', 'lagna_lord_in_house': 8},
                                                 {'lagna_lord_with_malefic_in_house': [6, 8, 12], 'house2_lord': 'debilitated_or_in_enemy_sign'}]},
             'formation_text': 'BPHS Ch.42 poverty yogas (all lagna-lord-centred): L1 in 12 with L12 in lagna joined/aspected by a māraka lord; L1 '
                               'in 6 with L6 in lagna joined/aspected by a māraka; lagna or Moon with Ketu while L1 is in 8; L1 with a malefic in '
                               '6/8/12 while L2 is debilitated or in an enemy sign',
             'severity_grades': {'severe': 'any BPHS Ch.42 combination present (the text gives no gradation)'},
             'cancellation_conditions': {'bhanga': ['dhana/raja yoga present (K2 project judgment; BPHS Ch.42 gives no cancellation on '
                                                    'bphs:PG412)']}},
 'dhaiya': {'classical_citations': [{'kind': 'K1',
                                     'text_id': 'phaladeepika',
                                     'locus': 'PG330:C1',
                                     'human_locus': 'Adh. XXVI śl.22',
                                     'excerpt': 'in the 4th house, there will be loss of wife, relation and wealth ... In the 8th house, there will '
                                                'be loss in children, cattle, friends and wealth ... disease'},
                                    {'kind': 'K2',
                                     'decision_id': 'OS-2026-10-05-CITATIONS',
                                     'label': 'modern practice / project judgment',
                                     'note': 'the names "Dhaiya / Panoti / Kantaka / Ashtama Shani" and the 2.5-year framing are later usage'}],
            'source_citation': 'K1 — Phaladeepika Adh. XXVI śl.22 — phaladeepika:PG330:C1 — "in the 4th house, there will be loss of wife, relation '
                               'and wealth ... In the 8th house, there will be loss in children, cattle, friends and wealth ... disease" ; K2 — the '
                               'names "Dhaiya / Panoti / Kantaka / Ashtama Shani" and the 2.5-year framing are later usage; ratified '
                               'OS-2026-10-05-CITATIONS'},
 'guru_chandal': {'classical_citations': [{'kind': 'K2', 'decision_id': 'OS-2026-10-05-CITATIONS', 'label': 'modern practice / project judgment'}],
                  'source_citation': 'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS',
                  'school': 'modern'},
 'kala_amrita_dosha': {'classical_citations': [{'kind': 'K2',
                                                'decision_id': 'OS-2026-10-05-CITATIONS',
                                                'label': 'modern practice / project judgment'}],
                       'source_citation': 'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS',
                       'school': 'modern'},
 'kala_sarpa': {'classical_citations': [{'kind': 'K2', 'decision_id': 'OS-2026-10-05-CITATIONS', 'label': 'modern practice / project judgment'}],
                'source_citation': 'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS',
                'school': 'modern',
                'formation_rule_jsonb': {'requires': 'all 7 planets hemmed between Rahu and Ketu (one side of the nodal axis)',
                                         'variant_names_by_rahu_house': {'1': 'Anant',
                                                                         '2': 'Kulik',
                                                                         '3': 'Vasuki',
                                                                         '4': 'Shankhpal',
                                                                         '5': 'Padma',
                                                                         '6': 'Mahapadma',
                                                                         '7': 'Takshak',
                                                                         '8': 'Karkotak',
                                                                         '9': 'Shankhachud',
                                                                         '10': 'Ghatak',
                                                                         '11': 'Vishdhar',
                                                                         '12': 'Sheshnag'}}},
 'kemadruma_compat_kuja': {'classical_citations': [{'kind': 'K1_UNVERIFIED',
                                                    'claimed_text': 'classical source claimed (Kuja-doṣa reckoned from Moon / Venus)',
                                                    'needs': 'Vivāha-paṭala / Jātaka-tattva / Praśna-mārga — none in corpus; not in hora_sara, '
                                                             'jataka_parijata or muhurta_chintamani (pass-1 search)'},
                                                   {'kind': 'K2',
                                                    'decision_id': 'OS-2026-10-05-CITATIONS',
                                                    'label': 'modern practice / project judgment',
                                                    'note': 'name is modern'}],
                           'source_citation': 'K1_UNVERIFIED — classical source claimed (Kuja-doṣa reckoned from Moon / Venus), not verified in our '
                                              'library; needs Vivāha-paṭala / Jātaka-tattva / Praśna-mārga — none in corpus; not in hora_sara, '
                                              'jataka_parijata or muhurta_chintamani (pass-1 search) ; name is modern (OS-2026-10-05-CITATIONS)',
                           'name_sa': 'Śukrāt Kuja-doṣa'},
 'kuja_dosha_from_moon': {'classical_citations': [{'kind': 'K1_UNVERIFIED',
                                                   'claimed_text': 'classical source claimed (Kuja-doṣa reckoned from Moon / Venus)',
                                                   'needs': 'Vivāha-paṭala / Jātaka-tattva / Praśna-mārga — none in corpus; not in hora_sara, '
                                                            'jataka_parijata or muhurta_chintamani (pass-1 search)'},
                                                  {'kind': 'K2',
                                                   'decision_id': 'OS-2026-10-05-CITATIONS',
                                                   'label': 'modern practice / project judgment',
                                                   'note': 'name is modern'}],
                          'source_citation': 'K1_UNVERIFIED — classical source claimed (Kuja-doṣa reckoned from Moon / Venus), not verified in our '
                                             'library; needs Vivāha-paṭala / Jātaka-tattva / Praśna-mārga — none in corpus; not in hora_sara, '
                                             'jataka_parijata or muhurta_chintamani (pass-1 search) ; name is modern (OS-2026-10-05-CITATIONS)'},
 'lagna_lord_grahan_dosha': {'classical_citations': [{'kind': 'K2',
                                                      'decision_id': 'OS-2026-10-05-CITATIONS',
                                                      'label': 'modern practice / project judgment'}],
                             'source_citation': 'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS',
                             'school': 'modern'},
 'mrityu_bhaga_dosha': {'classical_citations': [{'kind': 'K1',
                                                 'text_id': 'phaladeepika',
                                                 'locus': 'PG169:C1',
                                                 'human_locus': 'Adh. XIII śl.10',
                                                 'excerpt': 'degrees attained by the Moon in Mesha and the other signs be respectively 26, 12, 13, '
                                                            '25, 24, 11, 26, 14, 13, 25, 5 and 12, they indicate death',
                                                 'note': '(śl.11 gives an alternative set)'},
                                                {'kind': 'K1_UNVERIFIED',
                                                 'claimed_text': 'the per-planet/lagna mṛtyu-bhāga table used by L1: classical source claimed '
                                                                 '(Jātaka Pārijāta, which Phaladeepika cross-refers as "जा.पा. p.38")'},
                                                {'kind': 'K2',
                                                 'decision_id': 'OS-2026-10-05-CITATIONS',
                                                 'label': 'modern practice / project judgment',
                                                 'note': 'name is modern'}],
                        'source_citation': 'K1 — Phaladeepika Adh. XIII śl.10 — phaladeepika:PG169:C1 — "degrees attained by the Moon in Mesha and '
                                           'the other signs be respectively 26, 12, 13, 25, 24, 11, 26, 14, 13, 25, 5 and 12, they indicate death" '
                                           '(śl.11 gives an alternative set) ; K1_UNVERIFIED — the per-planet/lagna mṛtyu-bhāga table used by L1: '
                                           'classical source claimed (Jātaka Pārijāta, which Phaladeepika cross-refers as "जा.पा. p.38"), not '
                                           'verified in our library ; name is modern (OS-2026-10-05-CITATIONS)',
                        'formation_text': 'The Moon at its mṛtyu-bhāga per Phaladeepika XIII.10 (26,12,13,25,24,11,26,14,13,25,5,12 from Meṣa; '
                                          'XIII.11 gives an alternative set). The per-planet and lagna degrees that L1 computes are carried under a '
                                          'separate label: classical source claimed (Jātaka Pārijāta), not verified in our library.'},
 'naga_dosha_nodes_kendra': {'classical_citations': [{'kind': 'K2',
                                                      'decision_id': 'OS-2026-10-05-CITATIONS',
                                                      'label': 'modern practice / project judgment'}],
                             'source_citation': 'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS',
                             'school': 'modern'},
 'naga_dosha_rahu_lagna': {'classical_citations': [{'kind': 'K2',
                                                    'decision_id': 'OS-2026-10-05-CITATIONS',
                                                    'label': 'modern practice / project judgment'}],
                           'source_citation': 'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS',
                           'school': 'modern'},
 'pitra_dosha_9th_lord_afflicted': {'classical_citations': [{'kind': 'K2',
                                                             'decision_id': 'OS-2026-10-05-CITATIONS',
                                                             'label': 'modern practice / project judgment'},
                                                            {'kind': 'K1_ANALOGUE',
                                                             'text_id': 'bphs',
                                                             'locus': 'PG980:C1–PG981:C1',
                                                             'human_locus': 'Ch.83 (Curses of the previous birth) §20-30',
                                                             'excerpt': 'no male issue as a result of the curse of the father in the previous birth, '
                                                                        'if ... the Sun as lord of the 5th posited in a trikona with a malefic is '
                                                                        'hemmed in between malefics',
                                                             'note': "classical Pitṛ-śāpa is a progeny-loss doctrine; this row's fortune / "
                                                                     'ancestral-debt scope is modern',
                                                             'relation': 'classical analogue, not the source of this rule'}],
                                    'source_citation': 'K2 — modern practice / project judgment, not a classical source; ratified '
                                                       'OS-2026-10-05-CITATIONS ; K1_ANALOGUE — BPHS Ch.83 (Curses of the previous birth) §20-30 — '
                                                       'bphs:PG980:C1–PG981:C1 — "no male issue as a result of the curse of the father in the '
                                                       'previous birth, if ... the Sun as lord of the 5th posited in a trikona with a malefic is '
                                                       'hemmed in between malefics" — classical Pitṛ-śāpa is a progeny-loss doctrine; this row\'s '
                                                       'fortune / ancestral-debt scope is modern',
                                    'school': 'modern'},
 'pitra_dosha_sun_12th_malefic': {'classical_citations': [{'kind': 'K2',
                                                           'decision_id': 'OS-2026-10-05-CITATIONS',
                                                           'label': 'modern practice / project judgment'},
                                                          {'kind': 'K1_ANALOGUE',
                                                           'text_id': 'saravali',
                                                           'locus': 'PG47:C1',
                                                           'human_locus': 'Ch.16 §36',
                                                           'excerpt': 'Predict similar results regarding the father of the native, if the Sun joins '
                                                                      'malefics at birth',
                                                           'relation': 'classical analogue, not the source of this rule'},
                                                          {'kind': 'K1_ANALOGUE',
                                                           'text_id': 'bphs',
                                                           'locus': 'PG115:C1',
                                                           'human_locus': '(Evils to father) §36',
                                                           'excerpt': 'Early loss of father will take place if the Sun is with a malefic or is '
                                                                      'hemmed between malefics',
                                                           'note': 'classical father-affliction; the name "Pitra dosha" and the ancestral-debt '
                                                                   'reading are modern',
                                                           'relation': 'classical analogue, not the source of this rule'}],
                                  'source_citation': 'K2 — modern practice / project judgment, not a classical source; ratified '
                                                     'OS-2026-10-05-CITATIONS ; K1_ANALOGUE — Saravali Ch.16 §36 — saravali:PG47:C1 — "Predict '
                                                     'similar results regarding the father of the native, if the Sun joins malefics at birth" ; '
                                                     'K1_ANALOGUE — BPHS (Evils to father) §36 — bphs:PG115:C1 — "Early loss of father will take '
                                                     'place if the Sun is with a malefic or is hemmed between malefics" — classical '
                                                     'father-affliction; the name "Pitra dosha" and the ancestral-debt reading are modern',
                                  'school': 'modern'},
 'pitra_dosha_sun_rahu': {'classical_citations': [{'kind': 'K2',
                                                   'decision_id': 'OS-2026-10-05-CITATIONS',
                                                   'label': 'modern practice / project judgment'},
                                                  {'kind': 'K1_ANALOGUE',
                                                   'text_id': 'saravali',
                                                   'locus': 'PG47:C1',
                                                   'human_locus': 'Ch.16 §36',
                                                   'excerpt': 'Predict similar results regarding the father of the native, if the Sun joins malefics '
                                                              'at birth',
                                                   'relation': 'classical analogue, not the source of this rule'},
                                                  {'kind': 'K1_ANALOGUE',
                                                   'text_id': 'bphs',
                                                   'locus': 'PG115:C1',
                                                   'human_locus': '(Evils to father) §36',
                                                   'excerpt': 'Early loss of father will take place if the Sun is with a malefic or is hemmed '
                                                              'between malefics',
                                                   'note': 'classical father-affliction; the name "Pitra dosha" and the ancestral-debt reading are '
                                                           'modern',
                                                   'relation': 'classical analogue, not the source of this rule'}],
                          'source_citation': 'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; '
                                             'K1_ANALOGUE — Saravali Ch.16 §36 — saravali:PG47:C1 — "Predict similar results regarding the father of '
                                             'the native, if the Sun joins malefics at birth" ; K1_ANALOGUE — BPHS (Evils to father) §36 — '
                                             'bphs:PG115:C1 — "Early loss of father will take place if the Sun is with a malefic or is hemmed '
                                             'between malefics" — classical father-affliction; the name "Pitra dosha" and the ancestral-debt reading '
                                             'are modern',
                          'school': 'modern'},
 'pitra_dosha_sun_saturn_conjunction': {'classical_citations': [{'kind': 'K2',
                                                                 'decision_id': 'OS-2026-10-05-CITATIONS',
                                                                 'label': 'modern practice / project judgment'},
                                                                {'kind': 'K1_ANALOGUE',
                                                                 'text_id': 'saravali',
                                                                 'locus': 'PG47:C1',
                                                                 'human_locus': 'Ch.16 §36',
                                                                 'excerpt': 'Predict similar results regarding the father of the native, if the Sun '
                                                                            'joins malefics at birth',
                                                                 'relation': 'classical analogue, not the source of this rule'},
                                                                {'kind': 'K1_ANALOGUE',
                                                                 'text_id': 'bphs',
                                                                 'locus': 'PG115:C1',
                                                                 'human_locus': '(Evils to father) §36',
                                                                 'excerpt': 'Early loss of father will take place if the Sun is with a malefic or is '
                                                                            'hemmed between malefics',
                                                                 'note': 'classical father-affliction; the name "Pitra dosha" and the ancestral-debt '
                                                                         'reading are modern',
                                                                 'relation': 'classical analogue, not the source of this rule'}],
                                        'source_citation': 'K2 — modern practice / project judgment, not a classical source; ratified '
                                                           'OS-2026-10-05-CITATIONS ; K1_ANALOGUE — Saravali Ch.16 §36 — saravali:PG47:C1 — "Predict '
                                                           'similar results regarding the father of the native, if the Sun joins malefics at birth" '
                                                           '; K1_ANALOGUE — BPHS (Evils to father) §36 — bphs:PG115:C1 — "Early loss of father will '
                                                           'take place if the Sun is with a malefic or is hemmed between malefics" — classical '
                                                           'father-affliction; the name "Pitra dosha" and the ancestral-debt reading are modern',
                                        'school': 'modern'},
 'pitru_dosha': {'classical_citations': [{'kind': 'K2', 'decision_id': 'OS-2026-10-05-CITATIONS', 'label': 'modern practice / project judgment'},
                                         {'kind': 'K1_ANALOGUE',
                                          'text_id': 'bphs',
                                          'locus': 'PG980:C1–PG981:C1',
                                          'human_locus': 'Ch.83 (Curses of the previous birth) §20-30',
                                          'excerpt': 'no male issue as a result of the curse of the father in the previous birth, if ... the Sun as '
                                                     'lord of the 5th posited in a trikona with a malefic is hemmed in between malefics',
                                          'note': "classical Pitṛ-śāpa is a progeny-loss doctrine; this row's fortune / ancestral-debt scope is "
                                                  'modern',
                                          'relation': 'classical analogue, not the source of this rule'}],
                 'source_citation': 'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE '
                                    '— BPHS Ch.83 (Curses of the previous birth) §20-30 — bphs:PG980:C1–PG981:C1 — "no male issue as a result of the '
                                    'curse of the father in the previous birth, if ... the Sun as lord of the 5th posited in a trikona with a '
                                    'malefic is hemmed in between malefics" — classical Pitṛ-śāpa is a progeny-loss doctrine; this row\'s fortune / '
                                    'ancestral-debt scope is modern',
                 'school': 'modern'},
 'punarphoo': {'classical_citations': [{'kind': 'K2', 'decision_id': 'OS-2026-10-05-CITATIONS', 'label': 'modern practice / project judgment'},
                                       {'kind': 'K1_UNVERIFIED',
                                        'claimed_text': 'classical dvi-graha effect of Moon–Saturn claimed (Brihat Jataka Adh.14 / Saravali Ch.15 '
                                                        'two-planet yogas, corpus ≈ saravali PG42–43 unread)',
                                        'name_collision': 'the classical Viṣa-yoga is a tithi×vāra muhūrta yoga (muhurta_chintamani:PG17:C2 v.8); '
                                                          'never cite it for Moon–Saturn'}],
               'source_citation': 'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_UNVERIFIED '
                                  '— classical dvi-graha effect of Moon–Saturn claimed (Brihat Jataka Adh.14 / Saravali Ch.15 two-planet yogas, '
                                  'corpus ≈ saravali PG42–43 unread), not verified in our library ; NAME COLLISION — the classical Viṣa-yoga is a '
                                  'tithi×vāra muhūrta yoga (muhurta_chintamani:PG17:C2 v.8); never cite it for Moon–Saturn',
               'school': 'modern',
               'name_en': 'Moon–Saturn conjunction/aspect (Punarphoo; popularly "Vish dosha")',
               'name_sa': 'Candra-Śani-yuti (Punarphū)'},
 'sade_sati': {'classical_citations': [{'kind': 'K1',
                                        'text_id': 'phaladeepika',
                                        'locus': 'PG330:C1',
                                        'human_locus': 'Adh. XXVI śl.22-23',
                                        'excerpt': "Saturn's transit through the Janmarasi ... disease ... funeral rites; in the 2nd ... trouble to "
                                                   'wealth and children; ... 12th ... worthless and fruitless business ... robbed'},
                                       {'kind': 'K2',
                                        'decision_id': 'OS-2026-10-05-CITATIONS',
                                        'label': 'modern practice / project judgment',
                                        'note': 'the name "Sade Sati", the 7.5-year total and the rising/peak/setting phases are modern usage '
                                                "(duration is arithmetic on Saturn's ~2.5 years per sign)"}],
               'source_citation': 'K1 — Phaladeepika Adh. XXVI śl.22-23 — phaladeepika:PG330:C1 — "Saturn\'s transit through the Janmarasi ... '
                                  'disease ... funeral rites; in the 2nd ... trouble to wealth and children; ... 12th ... worthless and fruitless '
                                  'business ... robbed" ; K2 — the name "Sade Sati", the 7.5-year total and the rising/peak/setting phases are '
                                  "modern usage (duration is arithmetic on Saturn's ~2.5 years per sign); ratified OS-2026-10-05-CITATIONS"},
 'shakata': {'classical_citations': [{'kind': 'K1_UNVERIFIED',
                                      'claimed_text': 'classical source claimed (Candra–Guru Śakaṭa: Moon in 6/8/12 from Jupiter, cancelled by '
                                                      'Jupiter in a kendra)',
                                      'note': 'candidates in corpus: Jataka Parijata Adh. VII yoga chapter (PG462–464 read, not there), Phaladeepika '
                                              'Adh. VI; do NOT cite saravali:PG59:C2 (Nābhasa Śakaṭa, a different yoga)'},
                                     {'kind': 'K2',
                                      'decision_id': 'OS-2026-10-05-CITATIONS',
                                      'label': 'modern practice / project judgment',
                                      'note': 'name is modern'}],
             'source_citation': 'K1_UNVERIFIED — classical source claimed (Candra–Guru Śakaṭa: Moon in 6/8/12 from Jupiter, cancelled by Jupiter in '
                                'a kendra), not verified in our library; candidates in corpus: Jataka Parijata Adh. VII yoga chapter (PG462–464 '
                                'read, not there), Phaladeepika Adh. VI; do NOT cite saravali:PG59:C2 (Nābhasa Śakaṭa, a different yoga) ; name is '
                                'modern (OS-2026-10-05-CITATIONS)'},
 'shrapit_dosha': {'classical_citations': [{'kind': 'K2', 'decision_id': 'OS-2026-10-05-CITATIONS', 'label': 'modern practice / project judgment'}],
                   'source_citation': 'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS',
                   'school': 'modern'},
 'surya_grahan_dosha': {'classical_citations': [{'kind': 'K2',
                                                 'decision_id': 'OS-2026-10-05-CITATIONS',
                                                 'label': 'modern practice / project judgment'},
                                                {'kind': 'K1_ANALOGUE',
                                                 'text_id': 'bphs',
                                                 'locus': 'PG1016:C1',
                                                 'human_locus': 'Ch.91 (Birth in Eclipses) §1-14',
                                                 'excerpt': 'a person whose birth takes place at the time of solar or lunar eclipse suffers from '
                                                            'ailments, distress and poverty and faces danger of death',
                                                 'note': 'classical doṣa is birth DURING an eclipse; luminary-conjunct-node is a modern '
                                                         'generalisation',
                                                 'relation': 'classical analogue, not the source of this rule'}],
                        'source_citation': 'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; '
                                           'K1_ANALOGUE — BPHS Ch.91 (Birth in Eclipses) §1-14 — bphs:PG1016:C1 — "a person whose birth takes place '
                                           'at the time of solar or lunar eclipse suffers from ailments, distress and poverty and faces danger of '
                                           'death" — classical doṣa is birth DURING an eclipse; luminary-conjunct-node is a modern generalisation',
                        'school': 'modern'},
 'abhukta_mula_dosha': {'classical_citations': [{'kind': 'K1',
                                                 'text_id': 'bphs',
                                                 'locus': 'PG1021:C1',
                                                 'human_locus': 'Ch.93 (Abhukta Moola) §1-2',
                                                 'excerpt': 'ruling deity of Jyestha is Indra and ... of Moola is Rakshasa ... this gandanta is '
                                                            'considered as the most evil ... father should not see the face of the child for 8 '
                                                            'years'},
                                                {'kind': 'K1',
                                                 'text_id': 'bphs',
                                                 'locus': 'PG1019:C1',
                                                 'human_locus': 'Ch.92 §5',
                                                 'excerpt': 'the last 6 ghatikas of Jyestha and first 8 ghatikas of Moola are known as Abhukta '
                                                            'Moola'},
                                                {'kind': 'K1',
                                                 'text_id': 'muhurta_chintamani',
                                                 'locus': 'PG53:C1',
                                                 'human_locus': 'Nakṣatra-prakaraṇa v.54',
                                                 'excerpt': 'first eight ghaṭīs of Mūla and the last five nāḍīs of Jyeṣṭhā ... abandon the child; or '
                                                            'else the father should not look upon its face for eight years'},
                                                {'kind': 'K2',
                                                 'decision_id': 'OS-2026-10-05-CITATIONS',
                                                 'label': 'modern practice / project judgment',
                                                 'note': 'name is modern'}],
                        'source_citation': 'K1 — BPHS Ch.93 (Abhukta Moola) §1-2 — bphs:PG1021:C1 — "ruling deity of Jyestha is Indra and ... of '
                                           'Moola is Rakshasa ... this gandanta is considered as the most evil ... father should not see the face of '
                                           'the child for 8 years" ; K1 — BPHS Ch.92 §5 — bphs:PG1019:C1 — "the last 6 ghatikas of Jyestha and first '
                                           '8 ghatikas of Moola are known as Abhukta Moola" ; K1 — Muhurta Chintamani Nakṣatra-prakaraṇa v.54 — '
                                           'muhurta_chintamani:PG53:C1 — "first eight ghaṭīs of Mūla and the last five nāḍīs of Jyeṣṭhā ... abandon '
                                           'the child; or else the father should not look upon its face for eight years" ; name is modern '
                                           '(OS-2026-10-05-CITATIONS)',
                        'formation_rule_jsonb': {'window': {'jyeshtha_last_ghatis': {'bphs_ch92_s5': 6, 'mc_v54_narada': 5}, 'mula_first_ghatis': 8},
                                                 'note': 'two classical values for the Jyeṣṭhā side; MC ṭīkā records other opinions'},
                        'formation_text': 'Birth in the abhukta-mūla window: the last 6 (BPHS Ch.92 §5) or 5 (MC v.54, Nārada) ghaṭīs of Jyeṣṭhā and '
                                          'the first 8 ghaṭīs of Mūla',
                        'effects_text': 'Most evil of the gaṇḍāntas (Indra/Rākṣasa enmity): the child to be given away, or the father not to see its '
                                        'face for 8 years until śānti (BPHS Ch.93 §1-2; MC v.54)',
                        'cancellation_conditions': {'mitigation': ['śānti after the 12th day (BPHS Ch.93 §3-4)']}},
 'gana_dosha': {'classical_citations': [{'kind': 'K1',
                                         'text_id': 'muhurta_chintamani',
                                         'locus': 'PG95:C1',
                                         'human_locus': 'Vivāha-prakaraṇa vv.29-30 (Hindi ṭīkā)',
                                         'excerpt': 'rākṣasa-gaṇa = Maghā, Āśleṣā, Dhaniṣṭhā, Jyeṣṭhā, Mūla, Śatabhiṣā, Kṛttikā, Citrā, Viśākhā; '
                                                    '"same gaṇa great love; deva–manuṣya middling; rākṣasa–manuṣya death; deva–rākṣasa quarrel"'},
                                        {'kind': 'K1',
                                         'text_id': 'muhurta_chintamani',
                                         'locus': 'PG93:C1',
                                         'human_locus': 'v.21 ṭīkā',
                                         'excerpt': 'eight kūṭas carry guṇa 1,2,3,4,5,6,7,8 = 36 (gaṇa = 6)'},
                                        {'kind': 'K2',
                                         'decision_id': 'OS-2026-10-05-CITATIONS',
                                         'label': 'modern practice / project judgment',
                                         'note': 'name is modern'}],
                'source_citation': 'K1 — Muhurta Chintamani Vivāha-prakaraṇa vv.29-30 (Hindi ṭīkā) — muhurta_chintamani:PG95:C1 — rākṣasa-gaṇa = '
                                   'Maghā, Āśleṣā, Dhaniṣṭhā, Jyeṣṭhā, Mūla, Śatabhiṣā, Kṛttikā, Citrā, Viśākhā; "same gaṇa great love; deva–manuṣya '
                                   'middling; rākṣasa–manuṣya death; deva–rākṣasa quarrel" ; K1 — MC v.21 ṭīkā — muhurta_chintamani:PG93:C1 — eight '
                                   'kūṭas carry guṇa 1,2,3,4,5,6,7,8 = 36 (gaṇa = 6) ; name is modern (OS-2026-10-05-CITATIONS)',
                'formation_text': "Gaṇa mismatch between the partners' janma-nakṣatra gaṇas (deva / manuṣya / rākṣasa). Same gaṇa best; deva–manuṣya "
                                  'middling; deva–rākṣasa quarrel; rākṣasa–manuṣya gravest ("death"), with the ṭīkā\'s asymmetry: groom manuṣya + '
                                  "bride rākṣasa → groom's death; groom rākṣasa + bride manuṣya → enmity",
                'severity_grades': {'severe': 'rakshasa–manushya (either direction; groom manushya + bride rakshasa gravest)',
                                    'moderate': 'deva–rakshasa (quarrel)',
                                    'mild': 'deva–manushya (middling affection)',
                                    'none': 'same gana'},
                'formation_rule_jsonb': {'mismatch': 'Deva vs Rakshasa gana of the two Moon-nakshatras',
                                         'points': {'same_gana': 6, 'deva_manushya': 5, 'deva_or_manushya_with_rakshasa': 0}},
                'cancellation_conditions': {'bhanga': ['rāśi-lords mutually friendly (MC v.33)',
                                                       'aṃśa-lords friendly (v.33)',
                                                       'same nakṣatra, different pāda (v.37)']}},
 'mahendra_dosha': {'classical_citations': [{'kind': 'K1_UNVERIFIED',
                                             'claimed_text': 'classical source claimed (daśa-kūṭa item)',
                                             'needs': 'a daśa-kūṭa text (Vivāha-paṭala / Kālaprakāśikā / Jyotirnibandha) — none in corpus',
                                             'note': 'MC Vivāha-prakaraṇa vv.21-38 (muhurta_chintamani:PG93–PG100) read in full in pass 2 and does '
                                                     'not contain it'},
                                            {'kind': 'K2',
                                             'decision_id': 'OS-2026-10-05-CITATIONS',
                                             'label': 'modern practice / project judgment',
                                             'note': 'name is modern'}],
                    'source_citation': 'K1_UNVERIFIED — classical source claimed (daśa-kūṭa item), not verified in our library; MC Vivāha-prakaraṇa '
                                       'vv.21-38 (muhurta_chintamani:PG93–PG100) read in full in pass 2 and does not contain it; needs a daśa-kūṭa '
                                       'text (Vivāha-paṭala / Kālaprakāśikā / Jyotirnibandha) — none in corpus ; name is modern '
                                       '(OS-2026-10-05-CITATIONS)'},
 'mool_dosha': {'classical_citations': [{'kind': 'K1',
                                         'text_id': 'jataka_parijata',
                                         'locus': 'PG632:C1',
                                         'human_locus': 'śl.59',
                                         'excerpt': 'Ganda at the conclusion of ... Revati, Aslesha or Jyeshta ... and at the commencement of ... '
                                                    'Aswini, Magha or Moola'},
                                        {'kind': 'K1',
                                         'text_id': 'bphs',
                                         'locus': 'PG1018:C1, bphs:PG1019:C1',
                                         'human_locus': 'Ch.92 §3, §6-8',
                                         'excerpt': 'last two ghatikas of Revti and first two ghatikas of Aswini ... Ashlesha ... Makha ... Jyestha '
                                                    '... Moola ... Nakshatra Gandanta',
                                         'note': 'remedy: cow with calf; father sees child after sūtaka'},
                                        {'kind': 'K1',
                                         'text_id': 'bphs',
                                         'locus': 'PG1026:C1',
                                         'human_locus': 'Ch.94 §8-9',
                                         'excerpt': '3 cows ... in the case of Jyestha Moola and Ashlesha Makha gandantas, 2 cows in Revati-Ashwini '
                                                    'gandantas and 1 cow in other gandantas'},
                                        {'kind': 'K1',
                                         'text_id': 'muhurta_chintamani',
                                         'locus': 'PG53:C1',
                                         'human_locus': 'Nakṣatra-prakaraṇa v.55',
                                         'excerpt': 'first pāda of Mūla the father ... second, the mother; third, wealth ... fourth auspicious ... '
                                                    'In Āśleṣā the order is reversed'},
                                        {'kind': 'K2',
                                         'decision_id': 'OS-2026-10-05-CITATIONS',
                                         'label': 'modern practice / project judgment',
                                         'note': 'name is modern'}],
                'source_citation': 'K1 — Jataka Parijata śl.59 — jataka_parijata:PG632:C1 — "Ganda at the conclusion of ... Revati, Aslesha or '
                                   'Jyeshta ... and at the commencement of ... Aswini, Magha or Moola" ; K1 — BPHS Ch.92 §3, §6-8 — bphs:PG1018:C1, '
                                   'bphs:PG1019:C1 — "last two ghatikas of Revti and first two ghatikas of Aswini ... Ashlesha ... Makha ... Jyestha '
                                   '... Moola ... Nakshatra Gandanta"; remedy: cow with calf; father sees child after sūtaka ; K1 — BPHS Ch.94 §8-9 '
                                   '— bphs:PG1026:C1 — "3 cows ... in the case of Jyestha Moola and Ashlesha Makha gandantas, 2 cows in '
                                   'Revati-Ashwini gandantas and 1 cow in other gandantas" ; K1 — MC Nakṣatra-prakaraṇa v.55 — '
                                   'muhurta_chintamani:PG53:C1 — "first pāda of Mūla the father ... second, the mother; third, wealth ... fourth '
                                   'auspicious ... In Āśleṣā the order is reversed" ; name is modern (OS-2026-10-05-CITATIONS)',
                'effects_text': 'Early-childhood vulnerability (gaṇḍānta birth); śānti after the sūtaka days / after the 12th day (BPHS Ch.92 §6-8, '
                                'Ch.93 §3-4) — the "27th-day" timing is not in the texts',
                'formation_text': 'Natal Moon in a gaṇḍamūla nakṣatra (Aśvinī, Āśleṣā, Maghā, Jyeṣṭhā, Mūla, Revatī); the strict gaṇḍānta is the '
                                  'last/first 2 ghaṭikās at the Revatī–Aśvinī, Āśleṣā–Maghā, Jyeṣṭhā–Mūla junctions (BPHS Ch.92 §3; JP śl.59)',
                'severity_grades': {'mild': 'middle padas (K2 project grading)',
                                    'severe': 'junction padas (Jyeshtha-4 / Mula-1, Revati-4 / Ashwini-1, Ashlesha-4 / Magha-1) (K2 project grading)',
                                    'mula_pada': {'1': 'father', '2': 'mother', '3': 'wealth', '4': 'auspicious after śānti'},
                                    'ashlesha': 'reversed order'},
                'cancellation_conditions': {'mitigation': ['śānti performed (go-dāna 3/2/1 cows by junction, cow with calf, Mṛtyuñjaya japa)',
                                                           'benefic aspect on the Moon (K2)']}},
 'nadi_dosha': {'classical_citations': [{'kind': 'K1',
                                         'text_id': 'muhurta_chintamani',
                                         'locus': 'PG96:C1–PG97:C1',
                                         'human_locus': 'Vivāha-prakaraṇa v.34',
                                         'excerpt': 'Marriage of a couple falling within one and the same nāḍī is not good; falling in the middle '
                                                    'nāḍī, it means the death of both',
                                         'note': '(three nāḍī lists in the verse)'},
                                        {'kind': 'K1',
                                         'text_id': 'muhurta_chintamani',
                                         'locus': 'PG100:C1',
                                         'human_locus': 'v.37',
                                         'excerpt': 'no doṣa of nāḍī or of the gaṇas when the nakṣatra is the same but the pādas differ'},
                                        {'kind': 'K1',
                                         'text_id': 'muhurta_chintamani',
                                         'locus': 'PG93:C1',
                                         'human_locus': 'v.21 ṭīkā',
                                         'excerpt': 'nāḍī = 8 guṇa of 36'},
                                        {'kind': 'K2',
                                         'decision_id': 'OS-2026-10-05-CITATIONS',
                                         'label': 'modern practice / project judgment',
                                         'note': 'name is modern'}],
                'source_citation': 'K1 — Muhurta Chintamani Vivāha-prakaraṇa v.34 — muhurta_chintamani:PG96:C1–PG97:C1 — "Marriage of a couple '
                                   'falling within one and the same nāḍī is not good; falling in the middle nāḍī, it means the death of both" (three '
                                   'nāḍī lists in the verse) ; K1 — MC v.37 — muhurta_chintamani:PG100:C1 — "no doṣa of nāḍī or of the gaṇas when '
                                   'the nakṣatra is the same but the pādas differ" ; K1 — MC v.21 ṭīkā — muhurta_chintamani:PG93:C1 — nāḍī = 8 guṇa '
                                   'of 36 ; name is modern (OS-2026-10-05-CITATIONS)',
                'formation_rule_jsonb': {'same_nadi': True,
                                         'nadi_lists_mc_v34': {'adya': ['Ashvini',
                                                                        'Ardra',
                                                                        'Punarvasu',
                                                                        'Uttaraphalguni',
                                                                        'Hasta',
                                                                        'Jyeshtha',
                                                                        'Mula',
                                                                        'Shatabhisha',
                                                                        'Purvabhadrapada'],
                                                               'madhya': ['Bharani',
                                                                          'Mrigashira',
                                                                          'Pushya',
                                                                          'Purvaphalguni',
                                                                          'Chitra',
                                                                          'Anuradha',
                                                                          'Purvashadha',
                                                                          'Dhanishtha',
                                                                          'Uttarabhadrapada'],
                                                               'antya': ['Krittika',
                                                                         'Rohini',
                                                                         'Ashlesha',
                                                                         'Magha',
                                                                         'Svati',
                                                                         'Vishakha',
                                                                         'Uttarashadha',
                                                                         'Shravana',
                                                                         'Revati']}},
                'severity_grades': {'severe': 'same madhya nāḍī ("death of both")', 'moderate': 'same ādya or antya nāḍī'},
                'cancellation_conditions': {'bhanga': ['same nakṣatra, different pāda (MC v.37)',
                                                       'same rāśi, different nakṣatra (v.37 ṭīkā)',
                                                       'regional (optional flag): ādya/antya doṣa not applied south of the Godāvarī or to Kṣatriyas '
                                                       '(v.34 ṭīkā)']}},
 'rajju_dosha': {'classical_citations': [{'kind': 'K1_UNVERIFIED',
                                          'claimed_text': 'classical source claimed (daśa-kūṭa item)',
                                          'needs': 'a daśa-kūṭa text (Vivāha-paṭala / Kālaprakāśikā / Jyotirnibandha) — none in corpus',
                                          'note': 'MC Vivāha-prakaraṇa vv.21-38 (muhurta_chintamani:PG93–PG100) read in full in pass 2 and does not '
                                                  'contain it'},
                                         {'kind': 'K2',
                                          'decision_id': 'OS-2026-10-05-CITATIONS',
                                          'label': 'modern practice / project judgment',
                                          'note': 'name is modern'}],
                 'source_citation': 'K1_UNVERIFIED — classical source claimed (daśa-kūṭa item), not verified in our library; MC Vivāha-prakaraṇa '
                                    'vv.21-38 (muhurta_chintamani:PG93–PG100) read in full in pass 2 and does not contain it; needs a daśa-kūṭa text '
                                    '(Vivāha-paṭala / Kālaprakāśikā / Jyotirnibandha) — none in corpus ; name is modern (OS-2026-10-05-CITATIONS)'},
 'stree_deergha_dosha': {'classical_citations': [{'kind': 'K1_UNVERIFIED',
                                                  'claimed_text': 'classical source claimed (daśa-kūṭa item)',
                                                  'needs': 'a daśa-kūṭa text (Vivāha-paṭala / Kālaprakāśikā / Jyotirnibandha) — none in corpus',
                                                  'note': 'MC Vivāha-prakaraṇa vv.21-38 (muhurta_chintamani:PG93–PG100) read in full in pass 2 and '
                                                          'does not contain it'},
                                                 {'kind': 'K2',
                                                  'decision_id': 'OS-2026-10-05-CITATIONS',
                                                  'label': 'modern practice / project judgment',
                                                  'note': 'name is modern'}],
                         'source_citation': 'K1_UNVERIFIED — classical source claimed (daśa-kūṭa item), not verified in our library; MC '
                                            'Vivāha-prakaraṇa vv.21-38 (muhurta_chintamani:PG93–PG100) read in full in pass 2 and does not contain '
                                            'it; needs a daśa-kūṭa text (Vivāha-paṭala / Kālaprakāśikā / Jyotirnibandha) — none in corpus ; name is '
                                            'modern (OS-2026-10-05-CITATIONS)'},
 'tara_dosha_compat': {'classical_citations': [{'kind': 'K1',
                                                'text_id': 'muhurta_chintamani',
                                                'locus': 'PG93:C1',
                                                'human_locus': 'Vivāha-prakaraṇa v.24 (ṭīkā)',
                                                'excerpt': "count from the bride's nakṣatra to the groom's and back, divide by 9; remainders 3, 5, 7 "
                                                           'inauspicious ... 3 guṇa'},
                                               {'kind': 'K2',
                                                'decision_id': 'OS-2026-10-05-CITATIONS',
                                                'label': 'modern practice / project judgment',
                                                'note': 'name is modern'}],
                       'source_citation': 'K1 — Muhurta Chintamani Vivāha-prakaraṇa v.24 (ṭīkā) — muhurta_chintamani:PG93:C1 — "count from the '
                                          'bride\'s nakṣatra to the groom\'s and back, divide by 9; remainders 3, 5, 7 inauspicious ... 3 guṇa" ; '
                                          'name is modern (OS-2026-10-05-CITATIONS)'},
 'vedha_dosha': {'classical_citations': [{'kind': 'K1_UNVERIFIED',
                                          'claimed_text': 'classical source claimed (daśa-kūṭa item)',
                                          'needs': 'a daśa-kūṭa text (Vivāha-paṭala / Kālaprakāśikā / Jyotirnibandha) — none in corpus',
                                          'note': 'MC Vivāha-prakaraṇa vv.21-38 (muhurta_chintamani:PG93–PG100) read in full in pass 2 and does not '
                                                  'contain it'},
                                         {'kind': 'K2',
                                          'decision_id': 'OS-2026-10-05-CITATIONS',
                                          'label': 'modern practice / project judgment',
                                          'note': 'name is modern'}],
                 'source_citation': 'K1_UNVERIFIED — classical source claimed (daśa-kūṭa item), not verified in our library; MC Vivāha-prakaraṇa '
                                    'vv.21-38 (muhurta_chintamani:PG93–PG100) read in full in pass 2 and does not contain it; needs a daśa-kūṭa text '
                                    '(Vivāha-paṭala / Kālaprakāśikā / Jyotirnibandha) — none in corpus ; name is modern (OS-2026-10-05-CITATIONS)'},
 'yoni_dosha': {'classical_citations': [{'kind': 'K1',
                                         'text_id': 'muhurta_chintamani',
                                         'locus': 'PG94:C1',
                                         'human_locus': 'Vivāha-prakaraṇa vv.25-26 (ṭīkā)',
                                         'excerpt': 'fourteen yonis by nakṣatra pair; "enmities: cow–tiger, elephant–lion, horse–buffalo, dog–deer, '
                                                    'mongoose–serpent, monkey–sheep, cat–rat ... 4 guṇa"'},
                                        {'kind': 'K2',
                                         'decision_id': 'OS-2026-10-05-CITATIONS',
                                         'label': 'modern practice / project judgment',
                                         'note': 'name is modern'}],
                'source_citation': 'K1 — Muhurta Chintamani Vivāha-prakaraṇa vv.25-26 (ṭīkā) — muhurta_chintamani:PG94:C1 — fourteen yonis by '
                                   'nakṣatra pair; "enmities: cow–tiger, elephant–lion, horse–buffalo, dog–deer, mongoose–serpent, monkey–sheep, '
                                   'cat–rat ... 4 guṇa" ; name is modern (OS-2026-10-05-CITATIONS)'},
 'bhakoot_dosha': {'classical_citations': [{'kind': 'K1',
                                            'text_id': 'muhurta_chintamani',
                                            'locus': 'PG95:C1–PG96:C1',
                                            'human_locus': 'Vivāha-prakaraṇa vv.31-32',
                                            'excerpt': 'sixth from an odd sign ... eighth from an even sign ... śatru-ṣaḍaṣṭaka ... brings death ... '
                                                       '5–9 ... loss of sons; if 2–12, poverty ... mitra-ṣaḍaṣṭaka ... auspicious'},
                                           {'kind': 'K1',
                                            'text_id': 'muhurta_chintamani',
                                            'locus': 'PG96:C1',
                                            'human_locus': 'v.32 ṭīkā',
                                            'excerpt': 'five parihāras: ekādhipatya, friendly rāśi-lords, friendly strong aṃśa-lords, rāśi-vaśyatā, '
                                                       'tārā-śuddhi; "nāḍī-śuddhi must be present in every case"'},
                                           {'kind': 'K2',
                                            'decision_id': 'OS-2026-10-05-CITATIONS',
                                            'label': 'modern practice / project judgment',
                                            'note': 'name is modern'}],
                   'source_citation': 'K1 — Muhurta Chintamani Vivāha-prakaraṇa vv.31-32 — muhurta_chintamani:PG95:C1–PG96:C1 — "sixth from an odd '
                                      'sign ... eighth from an even sign ... śatru-ṣaḍaṣṭaka ... brings death ... 5–9 ... loss of sons; if 2–12, '
                                      'poverty ... mitra-ṣaḍaṣṭaka ... auspicious" ; K1 — MC v.32 ṭīkā — muhurta_chintamani:PG96:C1 — five '
                                      'parihāras: ekādhipatya, friendly rāśi-lords, friendly strong aṃśa-lords, rāśi-vaśyatā, tārā-śuddhi; '
                                      '"nāḍī-śuddhi must be present in every case" ; name is modern (OS-2026-10-05-CITATIONS)',
                   'formation_rule_jsonb': {'rashi_distance': {'6-8': {'shatru': "6th from the bride's ODD sign or 8th from her EVEN sign — "
                                                                                 'inauspicious (death)',
                                                                       'mitra': '6th from an even sign or 8th from an odd sign — auspicious, no '
                                                                                'dosha'},
                                                               '5-9': 'loss of sons',
                                                               '2-12': 'poverty'}},
                   'severity_grades': {'severe': 'śatru-ṣaḍaṣṭaka',
                                       'moderate': '5-9 (progeny) or 2-12 (poverty)',
                                       'none': 'mitra-ṣaḍaṣṭaka and all other distances'},
                   'cancellation_conditions': {'bhanga': ['ekādhipatya (one lord for both signs)',
                                                          'rāśi-lords mutually friendly, with nāḍī- and nakṣatra-śuddhi',
                                                          'aṃśa-lords friendly and strong, with nāḍī- and tārā-śuddhi',
                                                          'rāśi-vaśyatā',
                                                          'tārā-śuddhi'],
                                               'note': 'any one suffices; nāḍī-śuddhi must hold in every case (MC v.32 ṭīkā)'}},
 'graha_maitri_dosha': {'classical_citations': [{'kind': 'K1',
                                                 'text_id': 'muhurta_chintamani',
                                                 'locus': 'PG94:C1',
                                                 'human_locus': 'Vivāha-prakaraṇa vv.27-28 (ṭīkā)',
                                                 'excerpt': 'friend/enemy/neutral table of the rāśi-lords; 5 guṇa for friends or one lord, down to 0 '
                                                            'for mutual enemies ("mṛtyu-ṣaḍaṣṭaka")'},
                                                {'kind': 'K1',
                                                 'text_id': 'muhurta_chintamani',
                                                 'locus': 'PG96:C1',
                                                 'human_locus': 'vv.32-33',
                                                 'excerpt': 'friendship of the rāśi-lords destroys the ṣaḍaṣṭaka and the other doṣas'},
                                                {'kind': 'K2',
                                                 'decision_id': 'OS-2026-10-05-CITATIONS',
                                                 'label': 'modern practice / project judgment',
                                                 'note': 'name is modern'}],
                        'source_citation': 'K1 — Muhurta Chintamani Vivāha-prakaraṇa vv.27-28 (ṭīkā) — muhurta_chintamani:PG94:C1 — '
                                           'friend/enemy/neutral table of the rāśi-lords; 5 guṇa for friends or one lord, down to 0 for mutual '
                                           'enemies ("mṛtyu-ṣaḍaṣṭaka") ; K1 — MC vv.32-33 — muhurta_chintamani:PG96:C1 — "friendship of the '
                                           'rāśi-lords destroys the ṣaḍaṣṭaka and the other doṣas" ; name is modern (OS-2026-10-05-CITATIONS)'},
 'varna_dosha': {'classical_citations': [{'kind': 'K1',
                                          'text_id': 'muhurta_chintamani',
                                          'locus': 'PG93:C1',
                                          'human_locus': 'Vivāha-prakaraṇa v.22 (ṭīkā)',
                                          'excerpt': 'Pisces, Scorpio, Cancer Brāhmaṇa; 1,5,9 Kṣatriya; 2,6,10 Vaiśya; 3,7,11 Śūdra; a groom of '
                                                     'lower varṇa than the bride is not good; 1 guṇa'},
                                         {'kind': 'K2',
                                          'decision_id': 'OS-2026-10-05-CITATIONS',
                                          'label': 'modern practice / project judgment',
                                          'note': 'name is modern'}],
                 'source_citation': 'K1 — Muhurta Chintamani Vivāha-prakaraṇa v.22 (ṭīkā) — muhurta_chintamani:PG93:C1 — "Pisces, Scorpio, Cancer '
                                    'Brāhmaṇa; 1,5,9 Kṣatriya; 2,6,10 Vaiśya; 3,7,11 Śūdra; a groom of lower varṇa than the bride is not good; 1 '
                                    'guṇa" ; name is modern (OS-2026-10-05-CITATIONS)'},
 'vashya_dosha': {'classical_citations': [{'kind': 'K1',
                                           'text_id': 'muhurta_chintamani',
                                           'locus': 'PG93:C1',
                                           'human_locus': 'Vivāha-prakaraṇa v.23 (ṭīkā)',
                                           'excerpt': 'all signs except Leo are vaśya to the human signs ... water signs, being food of humans, are '
                                                      "their vaśya ... 2 guṇa when the bride's sign is vaśya to the groom's"},
                                          {'kind': 'K2',
                                           'decision_id': 'OS-2026-10-05-CITATIONS',
                                           'label': 'modern practice / project judgment',
                                           'note': 'name is modern'}],
                  'source_citation': 'K1 — Muhurta Chintamani Vivāha-prakaraṇa v.23 (ṭīkā) — muhurta_chintamani:PG93:C1 — "all signs except Leo are '
                                     "vaśya to the human signs ... water signs, being food of humans, are their vaśya ... 2 guṇa when the bride's "
                                     'sign is vaśya to the groom\'s" ; name is modern (OS-2026-10-05-CITATIONS)'},
 'vish_kanya_dosha': {'classical_citations': [{'kind': 'K1_UNVERIFIED',
                                               'claimed_text': 'classical source claimed (Viṣa-kanyā: tithi+vāra+nakṣatra)',
                                               'note': 'BPHS Ch.80 Strī-jātaka lists Viṣa-kanyā in its TOC (bphs:PG492:C1), body ≈ corpus PG927–957 '
                                                       'unread; also Jataka Parijata strī-jātaka; do NOT cite muhurta_chintamani:PG17:C2 (Viṣa-yoga, '
                                                       'different)'},
                                              {'kind': 'K2',
                                               'decision_id': 'OS-2026-10-05-CITATIONS',
                                               'label': 'modern practice / project judgment',
                                               'note': 'name is modern'}],
                      'source_citation': 'K1_UNVERIFIED — classical source claimed (Viṣa-kanyā: tithi+vāra+nakṣatra), not verified in our library; '
                                         'BPHS Ch.80 Strī-jātaka lists Viṣa-kanyā in its TOC (bphs:PG492:C1), body ≈ corpus PG927–957 unread; also '
                                         'Jataka Parijata strī-jātaka; do NOT cite muhurta_chintamani:PG17:C2 (Viṣa-yoga, different) ; name is '
                                         'modern (OS-2026-10-05-CITATIONS)'},
 'grahan': {'classical_citations': [{'kind': 'K2', 'decision_id': 'OS-2026-10-05-CITATIONS', 'label': 'modern practice / project judgment'},
                                    {'kind': 'K1_ANALOGUE',
                                     'text_id': 'bphs',
                                     'locus': 'PG1016:C1',
                                     'human_locus': 'Ch.91 (Birth in Eclipses) §1-14',
                                     'excerpt': 'a person whose birth takes place at the time of solar or lunar eclipse suffers from ailments, '
                                                'distress and poverty and faces danger of death',
                                     'note': 'classical doṣa is birth DURING an eclipse; luminary-conjunct-node is a modern generalisation',
                                     'relation': 'classical analogue, not the source of this rule'}],
            'source_citation': 'K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS ; K1_ANALOGUE — '
                               'BPHS Ch.91 (Birth in Eclipses) §1-14 — bphs:PG1016:C1 — "a person whose birth takes place at the time of solar or '
                               'lunar eclipse suffers from ailments, distress and poverty and faces danger of death" — classical doṣa is birth '
                               'DURING an eclipse; luminary-conjunct-node is a modern generalisation',
            'school': 'modern'}}


def apply_pass2_doshas(doshas: list[dict]) -> list[dict]:
    """Return a NEW list of NEW dosha dicts (the module-level seed list is never mutated).

    Fails loudly (no silent no-op) when a decided key is not in the seed, so a seed change that drops a decided row cannot quietly void the decision.
    """
    present = {d["canonical_id"] for d in doshas}
    missing = (set(PASS2_DOSHA_EDITS) | set(REMOVED_DOSHA_IDS) | set(RENAMED_DOSHA_IDS)) - present
    if missing:
        raise RuntimeError(f"citation pass 2: decision keys not in the dosha seed: {sorted(missing)}")
    out: list[dict] = []
    for d in doshas:
        cid = d["canonical_id"]
        if cid in REMOVED_DOSHA_IDS:
            continue
        new = copy.deepcopy(d)
        for field, value in PASS2_DOSHA_EDITS.get(cid, {}).items():
            new[field] = copy.deepcopy(value)
        if cid in RENAMED_DOSHA_IDS:
            new["canonical_id"] = RENAMED_DOSHA_IDS[cid]
        syn = ONTOLOGY_SYNONYMS.get(new["canonical_id"])
        if syn is not None:
            new["ontology_synonyms"] = list(syn)
        out.append(new)
    return out

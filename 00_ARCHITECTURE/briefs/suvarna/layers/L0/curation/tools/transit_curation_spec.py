#!/usr/bin/env python3
"""Curation SPEC for bg_transit_rules (23 re-sourced rows + classification of all 76) and
bg_transit_engine (9 citations).  Pure data + small helpers; no I/O.  Consumed by
build_transit_curation.py.  Every corpus pointer below was read in the chunk text on
2026-10-03 (reader-only SELECT); quotes are the minimum phrase needed to verify.

Corpus facts relied on (see ledger README section):
  * classical_text_chunks.verse_ref / .chapter are PAGE locators (PG324 = scanned page 324).
  * Sloka numbers are those PRINTED in the Sastri English translation inside the chunk
    ("Sloka 9 .-", running head "Sl. 18-19").  Where the printed numeral is OCR-garbled
    (sl. 10, 16, 18, 19) the number is fixed by the running head + sequence; flagged
    `numeral_basis`.
"""

PD_ED = "Sastri trans. 1950"
PD = "phaladeepika"


def pd_chunk(page):
    return f"phaladeepika_pg{page:04d}_c01"


# ---------------------------------------------------------------------------------------
# A. rules re-sourced to Phaladeepika Adh. XXVI slokas 9-24
#    key = (graha, rule_type, primary_house); id = live bg_transit_rules.id (2026-10-03)
# ---------------------------------------------------------------------------------------
# fields: id, old ('bphs29' | 'pdch26'), sloka, numeral_basis, page, continued_from (page|None),
#         supports (what the chunk states), not_stated (phala words NOT in the sloka),
#         quote, weak (bool)
FACT_ROWS = [
    dict(id=5,   key=("sun", "unfavourable", 1),     old="bphs29", sloka=9,  numeral="printed", page=324, cont=None,
         supports="unfavourable valence; ill-health (diseases)",
         not_stated="loss of position; eye trouble",
         quote="fatigue and loss of wealth ... suffer from diseases"),
    dict(id=6,   key=("sun", "unfavourable", 5),     old="bphs29", sloka=10, numeral="running-head+sequence (OCR 'iO')", page=324, cont=None,
         supports="unfavourable valence; ill-health, mental agitation",
         not_stated="trouble with children; loss of intelligence",
         quote="Mental agitation, ill-health and embarrassment"),
    dict(id=7,   key=("sun", "unfavourable", 8),     old="bphs29", sloka=10, numeral="running-head+sequence (OCR 'iO')", page=325, cont=324,
         supports="unfavourable valence; diseases; royal displeasure (conflict with authority)",
         not_stated="obstacle",
         quote="suffer from fear, and diseases ... incur royal displeasure"),
    dict(id=14,  key=("moon", "unfavourable", 8),    old="bphs29", sloka=12, numeral="printed", page=325, cont=None,
         supports="unfavourable valence only (wording 'untoward events' is weak)",
         not_stated="fear; sorrow; ill health", weak=True,
         quote="(8) untoward events"),
    dict(id=18,  key=("mars", "unfavourable", 1),    old="bphs29", sloka=13, numeral="printed", page=326, cont=None,
         supports="unfavourable valence; diseases from blood, bile or heat",
         not_stated="accidents; injury; quarrels",
         quote="diseases caused by (impurity of) blood, bile or heat"),
    dict(id=19,  key=("mars", "unfavourable", 4),    old="bphs29", sloka=13, numeral="printed", page=326, cont=None,
         supports="unfavourable valence; loss of position; sorrow through relations",
         not_stated="trouble to mother; property loss",
         quote="loss of position ... sorrow through relations"),
    dict(id=20,  key=("mars", "unfavourable", 8),    old="bphs29", sloka=15, numeral="running-head+sequence (OCR 'Shka JG' opens sl. 16)", page=327, cont=326,
         supports="unfavourable valence; fever; loss of wealth and honour",
         not_stated="danger; accidents; surgical risk",
         quote="In the 8th house, the native will suffer from fever"),
    dict(id=31,  key=("jupiter", "unfavourable", 4), old="bphs29", sloka=18, numeral="running-head+sequence (OCR 'Shka in')", page=328, cont=None,
         supports="unfavourable valence; sorrow through relations; humiliation",
         not_stated="loss of comforts; mother's illness",
         quote="sorrow through relations; the person will suffer humiliation"),
    dict(id=32,  key=("jupiter", "unfavourable", 8), old="bphs29", sloka=19, numeral="running-head+sequence (OCR 'SJoka 79')", page=328, cont=None,
         supports="unfavourable valence; loss of money; unlucky, miserable",
         not_stated="obstacles; loss of position; health issues",
         quote="will be unlucky, suffer loss of money and will be miserable"),
    dict(id=39,  key=("saturn", "unfavourable", 1),  old="pdch26", sloka=22, numeral="printed", page=330, cont=None,
         supports="unfavourable valence; disease",
         not_stated="'Sade Sati peak' framing; delays",
         quote="the native will suffer from disease"),
    dict(id=40,  key=("saturn", "unfavourable", 4),  old="bphs29", sloka=22, numeral="printed", page=330, cont=None,
         supports="unfavourable valence; loss of wife, relation and wealth",
         not_stated="mother's illness; property loss as such",
         quote="loss of wife, relation and wealth"),
    dict(id=41,  key=("saturn", "unfavourable", 8),  old="bphs29", sloka=22, numeral="printed", page=330, cont=None,
         supports="unfavourable valence; disease; loss of children, cattle, friends, wealth",
         not_stated="accidents; prolonged suffering",
         quote="loss in children, cattle, friends and wealth"),
    dict(id=190, key=("rahu", "unfavourable", 1),    old="bphs29", sloka=24, numeral="printed", page=331, cont=None,
         supports="unfavourable valence; sickness or death",
         not_stated="confusion; loss of clarity; fear and anxiety",
         quote="(1) sickness or death"),
    dict(id=191, key=("rahu", "unfavourable", 2),    old="bphs29", sloka=24, numeral="printed", page=331, cont=None,
         supports="unfavourable valence; loss of wealth",
         not_stated="speech affliction; family disputes",
         quote="(2) loss oi wealth", ocr="oi = of"),
    dict(id=192, key=("rahu", "unfavourable", 4),    old="bphs29", sloka=24, numeral="printed", page=331, cont=None,
         supports="unfavourable valence; sorrow",
         not_stated="domestic troubles; property loss; mother's health",
         quote="(4) sorrow"),
    dict(id=193, key=("rahu", "unfavourable", 7),    old="pdch26", sloka=24, numeral="printed", page=331, cont=None,
         supports="unfavourable valence; loss",
         not_stated="partnership conflicts; danger in travel; hidden adversaries",
         quote="(7) loss"),
    dict(id=194, key=("rahu", "unfavourable", 8),    old="bphs29", sloka=24, numeral="printed", page=331, cont=None,
         supports="unfavourable valence; danger to life",
         not_stated="accidents; sudden illness; hidden dangers",
         quote="8) danger to life", ocr="opening parenthesis lost in OCR"),
    dict(id=195, key=("rahu", "unfavourable", 12),   old="pdch26", sloka=24, numeral="printed", page=331, cont=None,
         supports="unfavourable valence; expenditure",
         not_stated="foreign travel under duress; separation",
         quote="(12) expenditure"),
]

# Ketu rows: stated equivalence (sloka 2: "Rahu and Ketu are similar to the Sun") + the Sun's
# result for that house + Rahu's sloka 24.  Valence = INFERENCE (no Ketu-specific verse).
# sun_sloka/sun_page = where the Sun's result for that house is printed.
INFERENCE_ROWS = [
    dict(id=200, key=("ketu", "unfavourable", 1), old="bphs29", sun_sloka=9,  sun_page=324,
         sun_quote="suffer from diseases", rahu_quote="(1) sickness or death"),
    dict(id=201, key=("ketu", "unfavourable", 2), old="pdch26", sun_sloka=9,  sun_page=324,
         sun_quote="there will be loss of wealth", rahu_quote="(2) loss oi wealth", ocr="oi = of"),
    dict(id=202, key=("ketu", "unfavourable", 4), old="bphs29", sun_sloka=9,  sun_page=324,
         sun_quote="the Sun will cause diseases", rahu_quote="(4) sorrow"),
    dict(id=203, key=("ketu", "unfavourable", 7), old="pdch26", sun_sloka=10, sun_page=324,
         sun_quote="wearisome travelling, diseases of the stomach", rahu_quote="(7) loss"),
    dict(id=204, key=("ketu", "unfavourable", 8), old="bphs29", sun_sloka=10, sun_page=325,
         sun_quote="the native will suffer from fear, and diseases", rahu_quote="8) danger to life", ocr="opening parenthesis lost in OCR"),
]

KETU_12 = dict(id=199, key=("ketu", "favourable", 12))

OLD_BPHS29 = "BPHS Ch.29 (Gochara Phala — Transit Results)"
OLD_PDCH26 = "Phaladeepika Ch.26 (Gochara Vedha and Transit Phala)"


def new_citation_fact(r):
    if r["cont"]:
        loc = f"Sloka {r['sloka']} (continued from PG{r['cont']}) — {PD}:PG{r['page']}:C1"
    else:
        loc = f"Sloka {r['sloka']} — {PD}:PG{r['page']}:C1"
    return (f"Phaladipika Adh. XXVI, {loc} ({PD_ED}) "
            f"[supports: {r['supports']}; remaining phala wording is not in the sloka]")


def new_citation_inference(r):
    h = r["key"][2]
    return (f"Phaladipika Adh. XXVI, Sloka 2 (Rahu and Ketu are similar to the Sun) read with Sloka {r['sun_sloka']} "
            f"(Sun, house {h}) and Sloka 24 (Rahu, house {h}) — {PD}:PG321:C1, {PD}:PG{r['sun_page']}:C1, "
            f"{PD}:PG331:C1 ({PD_ED}) [INFERENCE: no Ketu-specific verse; unfavourable valence only; "
            f"remaining phala wording is not in the text]")


# ---------------------------------------------------------------------------------------
# B. verification table for the 39 already page/sloka-anchored rows.
#    Pairs transcribed from the chunk text (sloka 3-8) and the sloka-2 favourable sets.
#    Used ONLY to re-check the live rows programmatically (the verification is a diff
#    between this transcription and the live table).
# ---------------------------------------------------------------------------------------
PD_VEDHA = {   # sloka: (page, [grahas], [(primary_house, vedha_house), ...])
    3: (322, ["sun"], [(11, 5), (3, 9), (10, 4), (6, 12)]),
    4: (322, ["moon"], [(7, 2), (1, 5), (6, 12), (11, 8), (10, 4), (3, 9)]),
    5: (322, ["mars", "saturn"], [(3, 12), (11, 5), (6, 9)]),
    6: (323, ["mercury"], [(2, 5), (4, 3), (6, 9), (8, 1), (10, 8), (11, 12)]),
    7: (323, ["jupiter"], [(2, 12), (11, 8), (9, 10), (5, 4), (7, 3)]),
    8: (323, ["venus"], [(1, 8), (2, 7), (3, 1), (4, 10), (5, 9), (8, 5), (9, 11), (12, 6), (11, 3)]),
}
# sloka 2 (PG321): good-result houses counted from the Moon; "all planets in the 11th";
# Venus: all places except 10, 7, 6.  Rahu/Ketu "similar to the Sun".
PD_SL2_GOOD = {
    "sun": {6, 3, 10, 11}, "moon": {3, 10, 6, 7, 1, 11}, "jupiter": {7, 9, 2, 5, 11},
    "mars": {6, 3, 11}, "saturn": {6, 3, 11}, "mercury": {6, 2, 4, 10, 8, 11},
    "venus": set(range(1, 13)) - {10, 7, 6},
}
# sloka 21 (PG329) Venus: "mishap in the 6th; trouble to wife in the 7th; quarrel in the 10th"
PD_VEDHA_PHRASE = {
    3: "the 5th, 9th, 4th and 12th respectively",
    4: "2nd, 5th, 12th, 8th, 4th and the 9th",
    5: "if the 12th, 5th and 9th places respectively are free",
    6: "3rd, 9th, 1st, 8th and 12th",
    7: "12th, 8th, 10th, 4th and 3rd are void of planets",
    8: "8th, 7th, 1st, 10th, 9th, 5th, 11th, 6th and 3rd respectively",
}
PD_VENUS_UNFAV = {6: "mishap in the 6th", 7: "trouble to wife in the 7th", 10: "quarrel in the 10th"}

# ---------------------------------------------------------------------------------------
# C. bg_transit_engine citations (9).  Values untouched.
# ---------------------------------------------------------------------------------------
ENGINE_TAIL = ('Former citation "BPHS Ch.22 (Graha Gati)" withdrawn as refuted: served bphs:PG22:C1 is Chapter 2 '
               '(incarnations) and the held corpus has no BPHS Graha Gati text.')

ENGINE = {
    "sun": dict(state="sourced_inference_partial", cells={"sign_residence_days": "INFERENCE"},
                pointers=[("brihat_jataka", "brihat_jataka_pg0096_c01", "PG96", "30 days and 30 months respectively"),
                          ("jataka_parijata", "jataka_parijata_pg0144_c01", "PG144", "30 days and 30 months respectively")],
                text=("PARTIALLY SOURCED — only sign_residence_days is stated in the held corpus, as the round figure "
                      "'30 days' per sign (brihat_jataka:PG96:C1; jataka_parijata:PG144:C1, translator notes; stored 30.44 is "
                      "read from it: INFERENCE). Motion and period values are not stated in the held corpus (the period coincides with the modern mean sidereal period). ")),
    "moon": dict(state="unsourced_marked", cells={},
                 pointers=[("sarvartha_chintamani", "sarvartha_chintamani_pg0001_c301", "PG1:C301",
                            "Moon who moves one sign in 2 J days (numeral illegible in OCR; not relied on)")],
                 text=("UNSOURCED — no value of this row is stated in the held corpus (sarvartha_chintamani:PG1:C301 "
                       "has a translator note giving the Moon's time per sign, but the numeral is OCR-illegible and is not relied on). "
                       "The period coincides with the modern mean sidereal period. ")),
    "mars": dict(state="unsourced_marked", cells={}, pointers=[],
                 text="UNSOURCED — no value of this row is stated in the held classical corpus (the period coincides with the modern mean sidereal period). "),
    "mercury": dict(state="unsourced_marked", cells={}, pointers=[],
                    text="UNSOURCED — no value of this row is stated in the held classical corpus (the period coincides with the modern mean sidereal period). "),
    "venus": dict(state="unsourced_marked", cells={}, pointers=[],
                  text="UNSOURCED — no value of this row is stated in the held classical corpus (the period coincides with the modern mean sidereal period). "),
    "jupiter": dict(state="sourced_inference_partial", cells={"sign_residence_days": "INFERENCE"},
                    pointers=[("yavana_jataka", "yavana_jataka_pg0662_c01", "PG662", "at the rate of one sign a year"),
                              ("yavana_jataka", "yavana_jataka_pg0900_c01", "PG900", "Jupiter spends approximately one year in each sign"),
                              ("bphs", "bphs_pg0933_c01", "PG933", "Jupiter stays in one sign for one year")],
                    text=("PARTIALLY SOURCED — only sign_residence_days (about one year per sign) is stated in the held corpus: "
                          "yavana_jataka:PG662:C1 ('at the rate of one sign a year'), yavana_jataka:PG900:C1, bphs:PG933:C1 "
                          "(worked example); stored 361.05 is read from the round figure: INFERENCE. Motion and period values are not stated "
                          "(the period coincides with the modern mean sidereal period). ")),
    "saturn": dict(state="sourced_inference_partial", cells={"sign_residence_days": "INFERENCE"},
                   pointers=[("brihat_jataka", "brihat_jataka_pg0096_c01", "PG96", "30 days and 30 months respectively"),
                             ("jataka_parijata", "jataka_parijata_pg0144_c01", "PG144", "30 days and 30 months respectively"),
                             ("sarvartha_chintamani", "sarvartha_chintamani_pg0001_c301", "PG1:C301", "Saturn who takes 900 days to move in a sign")],
                   text=("PARTIALLY SOURCED — only sign_residence_days is stated in the held corpus, as round figures: '30 months' per sign "
                         "(brihat_jataka:PG96:C1; jataka_parijata:PG144:C1, translator notes) and 'takes 900 days to move in a sign' "
                         "(sarvartha_chintamani:PG1:C301, translator note); stored 913.37 is read as 30 months: INFERENCE. Motion and period "
                         "values are not stated (the period coincides with the modern mean sidereal period). ")),
    "rahu": dict(state="unsourced_marked", cells={}, pointers=[],
                 text="UNSOURCED — no value of this row is stated in the held classical corpus (the period coincides with the modern mean sidereal period). "),
    "ketu": dict(state="unsourced_marked", cells={}, pointers=[],
                 text="UNSOURCED — no value of this row is stated in the held classical corpus (the period coincides with the modern mean sidereal period). "),
}


def engine_citation(graha):
    return ENGINE[graha]["text"] + ENGINE_TAIL


OLD_ENGINE_CITATION = "BPHS Ch.22 (Graha Gati — Planetary Motion)"
